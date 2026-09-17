#!/usr/bin/env python3
"""sdd-eval — score orchestrated SDD runs from `.sdd/telemetry.jsonl`.

Out-of-loop reader for the evaluation fields fixed by `docs/spec/evaluation.md`
§Scorer Fields (REQ-EVAL-HARNESSP2-002). It reads the telemetry file the
orchestrator appends after each gate (gitignored, orchestrator-only, never read
by phase detection) plus a `verification.md` `status:` line, groups records
into runs by (`cycle.workstream`, `cycle.kickoff_date`, `cycle.research_id`)
and prints one row per run plus one aggregate row. Every field is derived using
only the derivation table of `skills/sdd-orchestrate/references/telemetry.md`
§6 — no prose, no artifact other than `verification.md`'s `status`.

Usage:
  tools/sdd-eval.py [--file .sdd/telemetry.jsonl] [--verification docs/ws/<id>/verification.md]
                    [--status pass|fail|pending-red] [--run-status RESEARCH_ID=STATUS ...]
                    [--workstream ID] [--csv]
  tools/sdd-eval.py --self-test        # six-record fixture in a temp dir

The `verification.md` status applies to every run unless a `--run-status`
override names the run's `research_id`; a run whose status is unknown reports
field 1 as `unknown` and is excluded from the aggregate pass rate. An empty or
missing telemetry file prints zero rows and `N = 0` — no error.

Exit codes: 0 = ok, 1 = self-test failure, 2 = usage error / unreadable file.
No skill invokes this tool; it is never a phase-detection input.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone

SCHEMA_V = 1
DEFAULT_FILE = ".sdd/telemetry.jsonl"
STAGES = ("research", "requirements", "specs", "plan", "implement", "verify")
CHUNK_KINDS = {"pipeline", "fanout_leaf", "verifier", "fix"}
COLUMNS = [
    ("run", "run"),
    ("status", "status"),
    ("first_attempt_pass", "1 first-attempt pass"),
    ("fix_iterations", "2 fix iterations (per stage)"),
    ("scope_violation_rate", "3 SCOPE: VIOLATION"),
    ("malformed_rate", "4 MALFORMED"),
    ("dispatches_per_chunk", "5 dispatches/chunk"),
    ("contradiction_pauses", "6 CONTRADICTION"),
    ("red_broken", "7 red BROKEN"),
    ("tool_calls", "8 tool calls (used / budget)"),
    ("wall_dispatch_mean", "9 wall/dispatch (mean)"),
    ("wall_run", "9 wall/run"),
]


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------

def load(path: str) -> tuple[list[dict], int]:
    """Return (v1 records, skipped count). A missing file is an empty run set."""
    records: list[dict] = []
    skipped = 0
    if not os.path.exists(path):
        return records, skipped
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(rec, dict) or rec.get("v") != SCHEMA_V:
                skipped += 1
                continue
            records.append(rec)
    return records, skipped


def read_status(path: str | None) -> str | None:
    """The `status:` frontmatter value of a verification.md, or None."""
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^status:\s*(\S+)", line)
            if m:
                return m.group(1)
    return None


def _get(rec: dict, *keys, default=None):
    cur = rec
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return default if cur is None else cur


def _ts(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# scoring — one dict per run, one aggregate; keys are the derivation rows
# ---------------------------------------------------------------------------

def run_key(rec: dict) -> tuple[str, str, str]:
    return (
        str(_get(rec, "cycle", "workstream", default="default")),
        str(_get(rec, "cycle", "kickoff_date", default="?")),
        str(_get(rec, "cycle", "research_id", default="?")),
    )


def score_run(recs: list[dict], status: str | None) -> dict:
    """The nine scorer fields for one run, as raw numbers (formatting is separate)."""
    n = len(recs)
    # 2: max gate.fix_iteration per stage
    fix_iter: dict[str, int] = {}
    for r in recs:
        stage = _get(r, "dispatch", "stage")
        if stage is None:
            continue
        fix_iter[stage] = max(fix_iter.get(stage, 0), int(_get(r, "gate", "fix_iteration", default=0) or 0))
    # 1: status pass and zero verify-stage fix iterations
    if status is None:
        first = None
    else:
        first = status == "pass" and fix_iter.get("verify", 0) == 0
    # 3: scope
    scoped = [r for r in recs if _get(r, "scope", "token") is not None]
    violations = sum(1 for r in scoped if _get(r, "scope", "token") == "VIOLATION")
    # 4: malformed
    malformed = sum(1 for r in recs if _get(r, "verdict", "malformed") is True)
    # 5: dispatches per chunk
    per_chunk: dict = defaultdict(int)
    for r in recs:
        chunk = _get(r, "dispatch", "chunk")
        if chunk is not None and _get(r, "dispatch", "kind") in CHUNK_KINDS:
            per_chunk[chunk] += 1
    # 6: contradiction pauses
    contradictions = sum(1 for r in recs if _get(r, "verdict", "contradiction_class") is not None)
    # 7: red BROKEN findings
    red_broken = sum(int(_get(r, "return", "failures_n", default=0) or 0)
                     for r in recs if _get(r, "dispatch", "kind") == "red")
    # 8: tool calls consumed vs budget
    used = sum(int(_get(r, "return", "budget_consumed", "tool_calls", default=0) or 0) for r in recs)
    budget = sum(int(_get(r, "dispatch", "budget", "tool_calls", default=0) or 0) for r in recs)
    # 9: wall time
    per_dispatch = []
    dispatches, gates = [], []
    for r in recs:
        td, tr, tg = _ts(r.get("ts_dispatch")), _ts(r.get("ts_return")), _ts(r.get("ts_gate"))
        if td and tr:
            per_dispatch.append((tr - td).total_seconds())
        if td:
            dispatches.append(td)
        if tg:
            gates.append(tg)
    wall_run = (max(gates) - min(dispatches)).total_seconds() if dispatches and gates else None
    return {
        "records": n,
        "status": status,
        "first_attempt_pass": first,
        "fix_iterations": fix_iter,
        "scope_violations": violations,
        "scope_checked": len(scoped),
        "malformed": malformed,
        "chunk_dispatches": sum(per_chunk.values()),
        "chunks": len(per_chunk),
        "contradiction_pauses": contradictions,
        "red_broken": red_broken,
        "tool_calls_used": used,
        "tool_calls_budget": budget,
        "wall_dispatch_mean": (sum(per_dispatch) / len(per_dispatch)) if per_dispatch else None,
        "wall_run": wall_run,
    }


def aggregate(runs: list[dict]) -> dict:
    """One aggregate over N runs — rates are sum/sum, per-run counts are means."""
    n = len(runs)
    known = [r for r in runs if r["first_attempt_pass"] is not None]
    passes = sum(1 for r in known if r["first_attempt_pass"])
    fix_mean: dict[str, float] = {}
    for stage in STAGES:
        vals = [r["fix_iterations"].get(stage) for r in runs if stage in r["fix_iterations"]]
        if vals:
            fix_mean[stage] = sum(vals) / len(vals)
    dm = [r["wall_dispatch_mean"] for r in runs if r["wall_dispatch_mean"] is not None]
    wr = [r["wall_run"] for r in runs if r["wall_run"] is not None]
    return {
        "n": n,
        "known": len(known),
        "first_attempt_passes": passes,
        "fix_iterations": fix_mean,
        "scope_violations": sum(r["scope_violations"] for r in runs),
        "scope_checked": sum(r["scope_checked"] for r in runs),
        "malformed": sum(r["malformed"] for r in runs),
        "records": sum(r["records"] for r in runs),
        "chunk_dispatches": sum(r["chunk_dispatches"] for r in runs),
        "chunks": sum(r["chunks"] for r in runs),
        "contradiction_pauses": (sum(r["contradiction_pauses"] for r in runs) / n) if n else 0.0,
        "red_broken": (sum(r["red_broken"] for r in runs) / n) if n else 0.0,
        "tool_calls_used": sum(r["tool_calls_used"] for r in runs),
        "tool_calls_budget": sum(r["tool_calls_budget"] for r in runs),
        "wall_dispatch_mean": (sum(dm) / len(dm)) if dm else None,
        "wall_run": (sum(wr) / len(wr)) if wr else None,
    }


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def _secs(v: float | None) -> str:
    if v is None:
        return "n/a"
    v = int(round(v))
    h, rem = divmod(v, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m" if h else (f"{m}m {s:02d}s" if m else f"{s}s")


def _ratio(a: int, b: int) -> str:
    return f"{a}/{b}" + (f" ({a / b:.2f})" if b else "")


def _fix_str(fi: dict, fmt: str = "{:d}") -> str:
    return ", ".join(f"{st} {fmt.format(fi[st])}" for st in STAGES if st in fi) or "-"


def run_row(key: tuple[str, str, str], s: dict) -> dict:
    first = {True: "yes", False: "no", None: "unknown"}[s["first_attempt_pass"]]
    return {
        "run": "/".join(key),
        "status": s["status"] or "unknown",
        "first_attempt_pass": first,
        "fix_iterations": _fix_str(s["fix_iterations"]),
        "scope_violation_rate": _ratio(s["scope_violations"], s["scope_checked"]),
        "malformed_rate": _ratio(s["malformed"], s["records"]),
        "dispatches_per_chunk": _ratio(s["chunk_dispatches"], s["chunks"]),
        "contradiction_pauses": str(s["contradiction_pauses"]),
        "red_broken": str(s["red_broken"]),
        "tool_calls": f"{s['tool_calls_used']} / {s['tool_calls_budget']}",
        "wall_dispatch_mean": _secs(s["wall_dispatch_mean"]),
        "wall_run": _secs(s["wall_run"]),
    }


def agg_row(a: dict) -> dict:
    rate = f"{a['first_attempt_passes']}/{a['known']}" + (f" ({a['first_attempt_passes'] / a['known']:.2f})" if a["known"] else "")
    return {
        "run": f"aggregate (N = {a['n']})",
        "status": "-",
        "first_attempt_pass": rate,
        "fix_iterations": _fix_str(a["fix_iterations"], "{:.2f}"),
        "scope_violation_rate": _ratio(a["scope_violations"], a["scope_checked"]),
        "malformed_rate": _ratio(a["malformed"], a["records"]),
        "dispatches_per_chunk": _ratio(a["chunk_dispatches"], a["chunks"]),
        "contradiction_pauses": f"{a['contradiction_pauses']:.2f}/run",
        "red_broken": f"{a['red_broken']:.2f}/run",
        "tool_calls": f"{a['tool_calls_used']} / {a['tool_calls_budget']}",
        "wall_dispatch_mean": _secs(a["wall_dispatch_mean"]),
        "wall_run": _secs(a["wall_run"]),
    }


def render(rows: list[dict], skipped: int, as_csv: bool) -> str:
    keys = [k for k, _ in COLUMNS]
    heads = [h for _, h in COLUMNS]
    if as_csv:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(heads)
        for r in rows:
            w.writerow([r[k] for k in keys])
        return buf.getvalue().rstrip("\n")
    widths = [max(len(h), *(len(r[k]) for r in rows)) if rows else len(h) for k, h in COLUMNS]
    out = ["  ".join(h.ljust(w) for h, w in zip(heads, widths)).rstrip()]
    out.append("  ".join("-" * w for w in widths))
    for r in rows:
        out.append("  ".join(r[k].ljust(w) for k, w in zip(keys, widths)).rstrip())
    if skipped:
        out.append(f"skipped: {skipped} line(s) (unknown schema version or not JSON)")
    return "\n".join(out)


def evaluate(records: list[dict], status: str | None, run_status: dict[str, str],
             workstream: str | None) -> tuple[list[dict], dict]:
    """Group → score → rows. Returns (rows incl. aggregate, aggregate dict)."""
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in records:
        k = run_key(r)
        if workstream and k[0] != workstream:
            continue
        groups[k].append(r)
    scored = []
    rows = []
    for k in sorted(groups):
        st = run_status.get(k[2], status)
        s = score_run(groups[k], st)
        scored.append(s)
        rows.append(run_row(k, s))
    a = aggregate(scored)
    rows.append(agg_row(a))
    return rows, a


# ---------------------------------------------------------------------------
# self-test — six-record fixture yielding every field
# ---------------------------------------------------------------------------

def _record(**over) -> dict:
    rec = {
        "v": 1, "ts_dispatch": "2026-09-17T10:00:00Z", "ts_return": "2026-09-17T10:10:00Z", "ts_gate": "2026-09-17T10:12:00Z",
        "cycle": {"workstream": "default", "research_id": "RS-001", "kickoff_date": "2026-09-17", "marker": "4"},
        "dispatch": {"seq": 1, "kind": "pipeline", "stage": "research", "chunk": None, "iteration": None, "redo": None,
                     "reason": None, "budget": {"tool_calls": 70, "test_runs": None, "prototypes": False, "read_only": False},
                     "write_scope_n": 2},
        "return": {"status": "COMPLETE", "budget_consumed": {"tool_calls": 40, "test_runs": None, "self_reported": True},
                   "files_written_n": 1, "commits_n": 0, "tasks_completed_n": 0, "failures_n": 0, "ledger_n": 0,
                   "open_questions_n": 0, "blocked_writes_n": 0, "warnings": []},
        "scope": {"token": "CLEAN", "in": 1, "advisory": 0, "out": 0, "history_rewrite": False},
        "verdict": {"chunk_verdict": None, "review_verdict": None, "red_verdict": None,
                    "findings": {"C": 0, "M": 0, "m": 0}, "malformed": False, "contradiction_class": None},
        "gate": {"decision": "proceed", "decision_by": "operator", "fix_iteration": 0, "fix_cap": 3, "cap_raised": 0,
                 "redo_count": None, "replan_count": 0, "replan_cap": 3},
        "replan_trigger": None, "git": {"head_before": "aaaaaaa", "head_after": "aaaaaaa"},
    }
    for group, vals in over.items():
        if isinstance(vals, dict) and isinstance(rec.get(group), dict):
            rec[group].update(vals)
        else:
            rec[group] = vals
    return rec


def _fixture_lines() -> list[str]:
    """Six v1 records of one run + one unknown-v line + one torn line."""
    recs = [
        _record(dispatch={"seq": 1, "kind": "pipeline", "stage": "research"}),
        # review: no scope check, contradiction class b recorded at its gate
        _record(dispatch={"seq": 2, "kind": "review", "stage": "research", "budget": {"tool_calls": 15}},
                **{"return": {"budget_consumed": {"tool_calls": 10}}},
                scope={"token": None}, verdict={"review_verdict": "APPROVE_WITH_FIXES", "contradiction_class": "b"},
                ts_dispatch="2026-09-17T10:15:00Z", ts_return="2026-09-17T10:20:00Z", ts_gate="2026-09-17T10:25:00Z"),
        _record(dispatch={"seq": 3, "kind": "pipeline", "stage": "implement", "chunk": 1, "budget": {"tool_calls": 25}},
                **{"return": {"budget_consumed": {"tool_calls": 22}}}, verdict={"chunk_verdict": "PASS"},
                ts_dispatch="2026-09-17T10:30:00Z", ts_return="2026-09-17T10:50:00Z", ts_gate="2026-09-17T10:55:00Z"),
        # verifier: malformed return
        _record(dispatch={"seq": 4, "kind": "verifier", "stage": "implement", "chunk": 1, "budget": {"tool_calls": 15}},
                **{"return": {"budget_consumed": {"tool_calls": 8}}}, verdict={"malformed": True},
                ts_dispatch="2026-09-17T10:56:00Z", ts_return="2026-09-17T11:00:00Z", ts_gate="2026-09-17T11:02:00Z"),
        # fix on chunk 2: scope violation
        _record(dispatch={"seq": 5, "kind": "fix", "stage": "implement", "chunk": 2, "iteration": 1, "budget": {"tool_calls": 25}},
                **{"return": {"budget_consumed": {"tool_calls": 20}}}, scope={"token": "VIOLATION", "out": 1},
                gate={"decision": "redo", "fix_iteration": 1},
                ts_dispatch="2026-09-17T11:05:00Z", ts_return="2026-09-17T11:15:00Z", ts_gate="2026-09-17T11:20:00Z"),
        # red at verify: two BROKEN findings, verify-stage fix iteration 1
        _record(dispatch={"seq": 6, "kind": "red", "stage": "verify", "budget": {"tool_calls": 25}},
                **{"return": {"budget_consumed": {"tool_calls": 19}, "failures_n": 2}},
                verdict={"red_verdict": "BROKEN"}, gate={"decision": "fix", "fix_iteration": 1},
                ts_dispatch="2026-09-17T11:30:00Z", ts_return="2026-09-17T11:40:00Z", ts_gate="2026-09-17T12:00:00Z"),
    ]
    lines = [json.dumps(r, separators=(",", ":")) for r in recs]
    lines.append(json.dumps({"v": 2, "ts_dispatch": "2026-09-17T12:00:00Z"}))
    lines.append("{this is not json")
    return lines


def self_test() -> int:
    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    with tempfile.TemporaryDirectory() as tmp:
        tpath = os.path.join(tmp, "telemetry.jsonl")
        vpath = os.path.join(tmp, "verification.md")
        with open(tpath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(_fixture_lines()) + "\n")
        with open(vpath, "w", encoding="utf-8") as fh:
            fh.write("---\nstatus: pass\nlast_updated: 2026-09-17\n---\n# V\n")

        records, skipped = load(tpath)
        check(len(records) == 6 and skipped == 2, f"load: {len(records)} records, {skipped} skipped")
        status = read_status(vpath)
        check(status == "pass", f"status: {status}")
        rows, a = evaluate(records, status, {}, None)
        check(len(rows) == 2, f"rows: {len(rows)} (one run + aggregate)")
        r = rows[0]
        # field 1: pass but verify fix_iteration 1 → not first attempt
        check(r["first_attempt_pass"] == "no", f"field 1: {r['first_attempt_pass']}")
        # field 2
        check(r["fix_iterations"] == "research 0, implement 1, verify 1", f"field 2: {r['fix_iterations']}")
        # field 3: 1 violation / 5 scope-checked (review has no scope token)
        check(r["scope_violation_rate"].startswith("1/5"), f"field 3: {r['scope_violation_rate']}")
        # field 4: 1 malformed / 6 records
        check(r["malformed_rate"].startswith("1/6"), f"field 4: {r['malformed_rate']}")
        # field 5: chunk 1 → pipeline + verifier, chunk 2 → fix = 3 dispatches / 2 chunks
        check(r["dispatches_per_chunk"].startswith("3/2"), f"field 5: {r['dispatches_per_chunk']}")
        # field 6, 7
        check(r["contradiction_pauses"] == "1", f"field 6: {r['contradiction_pauses']}")
        check(r["red_broken"] == "2", f"field 7: {r['red_broken']}")
        # field 8: 40+10+22+8+20+19 = 119 used / 70+15+25+15+25+25 = 175 budget
        check(r["tool_calls"] == "119 / 175", f"field 8: {r['tool_calls']}")
        # field 9: per-dispatch (10+5+20+4+10+10)/6 = 9m50s; run = 12:00 − 10:00 = 2h
        check(r["wall_dispatch_mean"] == "9m 50s", f"field 9a: {r['wall_dispatch_mean']}")
        check(r["wall_run"] == "2h 00m", f"field 9b: {r['wall_run']}")
        # aggregate
        check(rows[1]["run"] == "aggregate (N = 1)", f"aggregate label: {rows[1]['run']}")
        check(rows[1]["first_attempt_pass"].startswith("0/1"), f"aggregate field 1: {rows[1]['first_attempt_pass']}")
        # run-status override and unknown status
        rows2, a2 = evaluate(records, None, {"RS-001": "pass"}, None)
        check(rows2[0]["status"] == "pass", "run-status override applied")
        rows3, a3 = evaluate(records, None, {}, None)
        check(rows3[0]["first_attempt_pass"] == "unknown" and a3["known"] == 0, "unknown status excluded from rate")
        # workstream filter that matches nothing → N = 0
        rows4, a4 = evaluate(records, status, {}, "other")
        check(a4["n"] == 0 and rows4[-1]["run"] == "aggregate (N = 0)", "workstream filter → N = 0")
        # csv and text render carry the twelve columns
        text = render(rows, skipped, False)
        check("skipped: 2 line(s)" in text and text.count("\n") >= 3, "text render")
        csv_out = render(rows, skipped, True)
        check(csv_out.splitlines()[0].count(",") == len(COLUMNS) - 1, "csv header width")
        # empty file → zero rows, N = 0, no error
        empty = os.path.join(tmp, "empty.jsonl")
        open(empty, "w").close()
        recs0, sk0 = load(empty)
        rows0, a0 = evaluate(recs0, None, {}, None)
        check(recs0 == [] and sk0 == 0 and a0["n"] == 0 and len(rows0) == 1, "empty file → N = 0")
        # missing file behaves like empty
        recs1, _ = load(os.path.join(tmp, "absent.jsonl"))
        check(recs1 == [], "missing file → empty")

    if failures:
        print("sdd-eval self-test FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("sdd-eval self-test OK (6 records, 9 fields, aggregate, empty/missing file, csv)")
    return 0


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="sdd-eval",
        description="Score orchestrated SDD runs from .sdd/telemetry.jsonl: one row per run, one aggregate row "
                    "(docs/spec/evaluation.md §Scorer Fields). Out-of-loop reader — no skill runs it.",
        epilog="Fields: 1 first-attempt pass rate, 2 mean fix iterations per stage, 3 SCOPE: VIOLATION rate, "
               "4 MALFORMED rate, 5 dispatches per chunk, 6 CONTRADICTION pauses per run, 7 red BROKEN findings "
               "per run, 8 self-reported tool calls vs budget, 9 wall time per dispatch and per run.")
    ap.add_argument("--file", default=DEFAULT_FILE, help=f"telemetry file (default: {DEFAULT_FILE}); missing → N = 0")
    ap.add_argument("--verification", default=None, help="verification.md whose `status:` line applies to every run")
    ap.add_argument("--status", default=None, choices=["pass", "fail", "pending-red"],
                    help="status to use instead of reading --verification")
    ap.add_argument("--run-status", action="append", default=[], metavar="RESEARCH_ID=STATUS",
                    help="per-run status override, keyed by cycle.research_id (repeatable)")
    ap.add_argument("--workstream", default=None, help="only runs of this cycle.workstream")
    ap.add_argument("--csv", action="store_true", help="CSV instead of aligned text")
    ap.add_argument("--self-test", action="store_true", help="run the built-in six-record fixture test")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    run_status: dict[str, str] = {}
    for item in args.run_status:
        if "=" not in item:
            print(f"sdd-eval: --run-status expects RESEARCH_ID=STATUS, got {item!r}", file=sys.stderr)
            return 2
        rid, st = item.split("=", 1)
        run_status[rid] = st
    try:
        records, skipped = load(args.file)
    except OSError as exc:
        print(f"sdd-eval: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2
    status = args.status or read_status(args.verification)
    rows, _ = evaluate(records, status, run_status, args.workstream)
    print(render(rows, skipped, args.csv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
