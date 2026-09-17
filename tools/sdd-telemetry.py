#!/usr/bin/env python3
"""sdd-telemetry — out-of-loop reader for the orchestrator's telemetry transcript.

Reads ``.sdd/telemetry.jsonl`` (one JSON record per dispatch, schema ``v: 1``,
defined in ``skills/sdd-orchestrate/references/telemetry.md`` §2) and prints,
per workstream, one row per ``dispatch.stage`` followed by a per-chunk block
(RS-008 probe 1 as a query). Contract: ``docs/spec/telemetry.md``
§Out-of-Loop Reader (REQ-TELEM-HARNESSP2-009).

This tool is **never invoked inside the orchestration loop** and no skill
reads the file it summarises; the file is gitignored, orchestrator-written and
never a phase-detection or staleness input.

Usage:
  tools/sdd-telemetry.py summarize [--file .sdd/telemetry.jsonl] [--workstream ID] [--since ISO]
  tools/sdd-telemetry.py --self-test      # six-record fixture in a temp dir
  tools/sdd-telemetry.py --help

Records with an unknown ``v`` and lines that are not JSON are skipped and
counted on a trailing ``skipped: N unknown-schema record(s)`` line.

Exit codes: 0 = ok, 1 = self-test failure, 2 = usage error / unreadable file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone

SCHEMA_V = 1
DEFAULT_FILE = ".sdd/telemetry.jsonl"
STAGES = ["research", "requirements", "specs", "plan", "implement", "verify", "replan"]

# ---------------------------------------------------------------------------
# Budget: line grammar (telemetry.md §2 — budget object)
# ---------------------------------------------------------------------------

_TOOL_CALLS_RE = re.compile(r"[~≤<=]?\s*(\d+)\s*tool calls?", re.IGNORECASE)
_TEST_RUNS_RE = re.compile(r"[~≤<=]?\s*(\d+)\s*test runs?", re.IGNORECASE)
_NO_PROTOTYPES_RE = re.compile(r"\bno\s+prototypes\b", re.IGNORECASE)
_PROTOTYPES_RE = re.compile(r"\bprototypes\b", re.IGNORECASE)
_READ_ONLY_RE = re.compile(r"\bread[- ]only\b", re.IGNORECASE)


def parse_budget_line(text: str) -> dict:
    """Parse a dispatched ``Budget:`` line into the budget object.

    ``{"tool_calls": int|None, "test_runs": int|None, "prototypes": bool,
    "read_only": bool}``; when no fragment matches at all the whole object is
    ``{"unparsed": True}`` — no text is ever copied into a record.
    """
    body = text.split(":", 1)[1] if text.lower().lstrip().startswith("budget:") else text
    matched = False
    out: dict = {"tool_calls": None, "test_runs": None, "prototypes": False, "read_only": False}
    m = _TOOL_CALLS_RE.search(body)
    if m:
        out["tool_calls"] = int(m.group(1))
        matched = True
    m = _TEST_RUNS_RE.search(body)
    if m:
        out["test_runs"] = int(m.group(1))
        matched = True
    if _NO_PROTOTYPES_RE.search(body):
        out["prototypes"] = False
        matched = True
    elif _PROTOTYPES_RE.search(body):
        out["prototypes"] = True
        matched = True
    if _READ_ONLY_RE.search(body):
        out["read_only"] = True
        matched = True
    return out if matched else {"unparsed": True}


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------


def load(path: str) -> tuple[list[dict], int]:
    """Return ``(records, skipped)``: parsed ``v == 1`` objects and the skipped count."""
    records: list[dict] = []
    skipped = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1  # torn or non-JSON line
                continue
            if not isinstance(rec, dict) or rec.get("v") != SCHEMA_V:
                skipped += 1  # unknown schema version
                continue
            records.append(rec)
    return records, skipped


def _ts(value) -> datetime | None:
    """Parse an ISO-8601 UTC timestamp (``...Z`` or offset form); None when absent/invalid."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _get(rec: dict, *keys, default=None):
    """Nested lookup tolerant of missing groups (``_get(rec, "gate", "decision")``)."""
    cur = rec
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def filter_records(records: list[dict], workstream: str | None, since: str | None) -> list[dict]:
    out = records
    if workstream:
        out = [r for r in out if _get(r, "cycle", "workstream") == workstream]
    if since:
        since_dt = _ts(since)
        if since_dt is None:
            raise ValueError(f"--since is not an ISO-8601 timestamp: {since!r}")
        out = [r for r in out if (_ts(r.get("ts_dispatch")) or datetime.min.replace(tzinfo=timezone.utc)) >= since_dt]
    return out


# ---------------------------------------------------------------------------
# summarize
# ---------------------------------------------------------------------------


def _fmt_secs(values: list[float]) -> str:
    """``mean/max`` of durations in seconds rendered as ``MmSSs``; ``-`` when empty."""
    if not values:
        return "-"

    def one(v: float) -> str:
        v = int(round(v))
        return f"{v // 60}m{v % 60:02d}s"

    return f"{one(statistics.fmean(values))}/{one(max(values))}"


def _mean_max(values: list[int]) -> str:
    if not values:
        return "-/-"
    return f"{statistics.fmean(values):.1f}/{max(values)}"


def stage_rows(records: list[dict]) -> list[dict]:
    """One row per ``dispatch.stage`` with every §Out-of-Loop Reader column."""
    by_stage: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_stage[str(_get(r, "dispatch", "stage"))].append(r)
    order = [s for s in STAGES if s in by_stage] + sorted(k for k in by_stage if k not in STAGES)
    rows = []
    for stage in order:
        recs = by_stage[stage]
        used, budget, na = [], [], 0
        for r in recs:
            u = _get(r, "return", "budget_consumed", "tool_calls")
            b = _get(r, "dispatch", "budget", "tool_calls")
            if isinstance(u, int) and isinstance(b, int):
                used.append(u)
                budget.append(b)
            else:
                na += 1  # unparsed budget or null count
        redo_by_chunk: dict = defaultdict(int)
        for r in recs:
            rc = _get(r, "gate", "redo_count")
            if isinstance(rc, int):
                ch = _get(r, "dispatch", "chunk")
                redo_by_chunk[ch] = max(redo_by_chunk[ch], rc)
        wall_dispatch, wall_gate = [], []
        for r in recs:
            td, tr, tg = _ts(r.get("ts_dispatch")), _ts(r.get("ts_return")), _ts(r.get("ts_gate"))
            if td and tr:
                wall_dispatch.append((tr - td).total_seconds())
            if tr and tg:
                wall_gate.append((tg - tr).total_seconds())
        red = [_get(r, "verdict", "red_verdict") for r in recs]
        rows.append({
            "stage": stage,
            "dispatches": len(recs),
            "tool_calls": _mean_max(used),
            "budget": _mean_max(budget),
            "n/a": na,
            "scope_violations": sum(1 for r in recs if _get(r, "scope", "token") == "VIOLATION"),
            "malformed": sum(1 for r in recs if _get(r, "verdict", "malformed") is True),
            "fix_iterations": max((_get(r, "gate", "fix_iteration") or 0) for r in recs),
            "redos_per_chunk": " ".join(f"c{c}:{n}" for c, n in sorted(redo_by_chunk.items(), key=lambda kv: str(kv[0]))) or "-",
            "contradiction_pauses": sum(1 for r in recs if _get(r, "verdict", "contradiction_class") is not None),
            "red_broken": red.count("BROKEN"),
            "red_held": red.count("HELD"),
            "wall_dispatch": _fmt_secs(wall_dispatch),
            "wall_gate": _fmt_secs(wall_gate),
        })
    return rows


PER_CHUNK_KINDS = ("pipeline", "fanout_leaf", "verifier", "fix")


def chunk_rows(records: list[dict]) -> list[dict]:
    """Per-chunk block: implement + verifier + fix dispatches and the max redo per chunk."""
    by_chunk: dict[int, dict] = {}
    for r in records:
        ch = _get(r, "dispatch", "chunk")
        if not isinstance(ch, int):
            continue
        kind = _get(r, "dispatch", "kind")
        row = by_chunk.setdefault(ch, {"chunk": ch, "implement": 0, "verifier": 0, "fix": 0, "other": 0, "redo": 0, "total": 0})
        if kind in ("pipeline", "fanout_leaf"):
            row["implement"] += 1
        elif kind == "verifier":
            row["verifier"] += 1
        elif kind == "fix":
            row["fix"] += 1
        else:
            row["other"] += 1
        row["total"] += 1
        rc = _get(r, "gate", "redo_count")
        if isinstance(rc, int):
            row["redo"] = max(row["redo"], rc)
    return [by_chunk[k] for k in sorted(by_chunk)]


STAGE_COLUMNS = [
    ("stage", "stage"), ("dispatches", "dispatches"), ("tool_calls", "tool calls mean/max"),
    ("budget", "budget mean/max"), ("n/a", "n/a"), ("scope_violations", "SCOPE violations"),
    ("malformed", "MALFORMED"), ("fix_iterations", "fix iterations"), ("redos_per_chunk", "redos per chunk"),
    ("contradiction_pauses", "contradiction pauses"), ("red_broken", "red BROKEN"), ("red_held", "red HELD"),
    ("wall_dispatch", "wall dispatch mean/max"), ("wall_gate", "wall gate mean/max"),
]
CHUNK_COLUMNS = [
    ("chunk", "chunk"), ("implement", "implement"), ("verifier", "verifier"), ("fix", "fix"),
    ("other", "other"), ("total", "dispatches"), ("redo", "max redo"),
]


def _table(rows: list[dict], columns: list[tuple[str, str]]) -> list[str]:
    """Render rows as an aligned plain-text table (no third-party deps)."""
    headers = [h for _, h in columns]
    cells = [[str(r[k]) for k, _ in columns] for r in rows]
    widths = [max(len(h), *(len(c[i]) for c in cells)) if cells else len(h) for i, h in enumerate(headers)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    out = [fmt.format(*headers), fmt.format(*("-" * w for w in widths))]
    out += [fmt.format(*c) for c in cells]
    return out


def summarize(records: list[dict], skipped: int) -> str:
    """Full report text: one stage table + per-chunk block per workstream, then the skipped line."""
    lines: list[str] = []
    by_ws: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_ws[str(_get(r, "cycle", "workstream", default="?"))].append(r)
    if not by_ws:
        lines.append("no records")
    for ws in sorted(by_ws):
        recs = by_ws[ws]
        runs = sorted({str(_get(r, "cycle", "research_id")) for r in recs})
        lines.append(f"workstream: {ws}   records: {len(recs)}   runs (cycle.research_id): {', '.join(runs)}")
        lines += _table(stage_rows(recs), STAGE_COLUMNS)
        lines.append("")
        lines.append(f"per-chunk block (workstream {ws}) — implement + verifier + fix dispatches, max redo:")
        chunks = chunk_rows(recs)
        lines += _table(chunks, CHUNK_COLUMNS) if chunks else ["  (no per-chunk dispatches)"]
        lines.append("")
    lines.append(f"skipped: {skipped} unknown-schema record(s)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------


def _record(**over) -> dict:
    """A complete v1 record (every key present, nulls explicit) with overrides applied per group."""
    rec = {
        "v": 1, "ts_dispatch": "2026-09-17T10:00:00Z", "ts_return": "2026-09-17T10:10:00Z", "ts_gate": "2026-09-17T10:12:00Z",
        "cycle": {"workstream": "harness-p2", "research_id": "RS-HARNESSP2-001", "kickoff_date": "2026-09-17", "marker": "4"},
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
        "replan_trigger": None, "git": {"head_before": "c38922d", "head_after": "c38922d"},
    }
    for group, vals in over.items():
        if isinstance(vals, dict) and isinstance(rec.get(group), dict):
            rec[group].update(vals)
        else:
            rec[group] = vals
    return rec


def _fixture_lines() -> list[str]:
    """Six v1 records across four stages + one unknown-v record + one non-JSON line."""
    recs = [
        _record(dispatch={"seq": 1, "kind": "pipeline", "stage": "research"}),
        _record(dispatch={"seq": 2, "kind": "review", "stage": "research", "budget": {"tool_calls": 15, "test_runs": None, "prototypes": False, "read_only": True}},
                verdict={"review_verdict": "APPROVE_WITH_FIXES", "findings": {"C": 0, "M": 2, "m": 3}},
                ts_return="2026-09-17T10:20:00Z", ts_gate="2026-09-17T10:25:00Z"),
        _record(dispatch={"seq": 3, "kind": "pipeline", "stage": "specs", "budget": {"unparsed": True}},
                scope={"token": "VIOLATION", "out": 1}, gate={"decision": "widen"}),
        _record(dispatch={"seq": 4, "kind": "pipeline", "stage": "implement", "chunk": 1,
                          "budget": {"tool_calls": 25, "test_runs": 3, "prototypes": False, "read_only": False}},
                **{"return": {"budget_consumed": {"tool_calls": 22, "test_runs": 3, "self_reported": True}}},
                verdict={"chunk_verdict": "PASS"}, gate={"redo_count": 0}),
        _record(dispatch={"seq": 5, "kind": "fix", "stage": "implement", "chunk": 2, "iteration": 1, "redo": 1,
                          "reason": "verdict_fail",
                          "budget": {"tool_calls": 25, "test_runs": 3, "prototypes": False, "read_only": False}},
                verdict={"chunk_verdict": "FAIL", "malformed": True, "contradiction_class": "b"},
                gate={"decision": "redo", "redo_count": 1, "fix_iteration": 1}),
        _record(dispatch={"seq": 6, "kind": "red", "stage": "verify", "budget": {"tool_calls": 15, "test_runs": 2, "prototypes": False, "read_only": True}},
                verdict={"red_verdict": "BROKEN"}, **{"return": {"failures_n": 2}}),
    ]
    lines = [json.dumps(r, separators=(",", ":")) for r in recs]
    lines.append(json.dumps({"v": 2, "ts_dispatch": "2026-09-17T11:00:00Z"}))  # unknown schema → skipped
    lines.append("{this is not json")                                             # torn line → skipped
    return lines


def self_test() -> int:
    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    # Budget grammar (telemetry.md §2 / spec test_budget_line_parses_to_units).
    check(parse_budget_line("Budget: ~70 tool calls, no prototypes")
          == {"tool_calls": 70, "test_runs": None, "prototypes": False, "read_only": False}, "budget line 1")
    check(parse_budget_line("Budget: ≤ 25 tool calls, ≤ 3 test runs, read-only")
          == {"tool_calls": 25, "test_runs": 3, "prototypes": False, "read_only": True}, "budget line 2")
    check(parse_budget_line("Budget: whatever fits") == {"unparsed": True}, "budget line 3")
    check(parse_budget_line("Budget: 2 approaches, prototypes")["prototypes"] is True, "prototypes without no")

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, ".sdd", "telemetry.jsonl")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(_fixture_lines()) + "\n")
        records, skipped = load(path)
        check(len(records) == 6, f"expected 6 records, got {len(records)}")
        check(skipped == 2, f"expected skipped == 2, got {skipped}")
        # No record copies budget text.
        check(not any("tool calls" in json.dumps(r) for r in records), "record contains budget text")

        rows = stage_rows(records)
        check([r["stage"] for r in rows] == ["research", "specs", "implement", "verify"],
              f"one row per stage expected, got {[r['stage'] for r in rows]}")
        by = {r["stage"]: r for r in rows}
        check(by["research"]["dispatches"] == 2, "research dispatches")
        check(by["specs"]["n/a"] == 1 and by["specs"]["scope_violations"] == 1, "specs n/a + violation")
        check(by["implement"]["malformed"] == 1 and by["implement"]["contradiction_pauses"] == 1, "implement malformed/contradiction")
        check(by["implement"]["fix_iterations"] == 1 and by["implement"]["redos_per_chunk"] == "c1:0 c2:1", "implement fix/redo")
        check(by["verify"]["red_broken"] == 1 and by["verify"]["red_held"] == 0, "verify red counts")
        check(by["research"]["wall_dispatch"] == "15m00s/20m00s", f"wall dispatch {by['research']['wall_dispatch']}")
        check(by["research"]["wall_gate"] == "3m30s/5m00s", f"wall gate {by['research']['wall_gate']}")

        chunks = chunk_rows(records)
        check([c["chunk"] for c in chunks] == [1, 2], f"per-chunk block chunks {[c['chunk'] for c in chunks]}")
        check(chunks[0]["implement"] == 1 and chunks[1]["fix"] == 1 and chunks[1]["redo"] == 1, "per-chunk counts")

        report = summarize(records, skipped)
        check("workstream: harness-p2" in report, "report header")
        check("skipped: 2 unknown-schema record(s)" in report, "skipped line")
        check("per-chunk block" in report, "per-chunk block present")
        for _, header in STAGE_COLUMNS:
            check(header in report, f"column missing: {header}")

        # Filters.
        check(len(filter_records(records, "nope", None)) == 0, "workstream filter")
        check(len(filter_records(records, None, "2026-09-18T00:00:00Z")) == 0, "since filter")

    if failures:
        print("SELF-TEST FAIL:\n- " + "\n- ".join(failures))
        return 1
    print("SELF-TEST OK: budget grammar, six-record fixture (one row per stage, per-chunk block, skipped: 2)")
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="sdd-telemetry",
        description="Out-of-loop reader for .sdd/telemetry.jsonl (orchestrator-written, gitignored, "
                    "never read by phase detection). One table per workstream, one row per stage.",
    )
    ap.add_argument("--self-test", action="store_true", help="run the built-in six-record fixture test")
    sub = ap.add_subparsers(dest="command")
    sp = sub.add_parser("summarize", help="print per-workstream stage tables and the per-chunk block")
    sp.add_argument("--file", default=DEFAULT_FILE, help=f"telemetry file (default: {DEFAULT_FILE})")
    sp.add_argument("--workstream", default=None, help="only records of this cycle.workstream")
    sp.add_argument("--since", default=None, help="only records with ts_dispatch >= this ISO-8601 timestamp")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.command != "summarize":
        ap.print_help()
        return 2
    if not os.path.isfile(args.file):
        print(f"error: {args.file} not found (telemetry is written by sdd-orchestrate after each gate)", file=sys.stderr)
        return 2
    records, skipped = load(args.file)
    try:
        records = filter_records(records, args.workstream, args.since)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(summarize(records, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
