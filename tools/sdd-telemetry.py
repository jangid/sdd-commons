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
counted on a trailing ``skipped: N unknown-schema record(s)`` line. A sibling
``records-vs-expected:`` headline reports, per session, how many appends the
records imply versus how many are present — a post-cycle backstop for a missing
gate append (REQ-TELEM-HARNESSP3-002). ``expected`` starts from the highest
``dispatch.seq`` and adds every append **implied by a cross-field value the
writer did fill** (REQ-TELEM-HARNESSP4-002, -003; ``docs/spec/telemetry.md``
§Implication-Derived ``expected`` and the Headline): a ``chunk_verdict`` implies
a ``verifier`` record, ``redo`` implies the first attempt, a carried review/red
verdict implies its ``review``/``red`` record, and a fix-dispatching gate
decision or a fix-only ``reason`` implies a ``fix`` record. An implied fix that
exists as a record of another kind is *mis-typed* (a ``--lint`` finding once
that subcommand lands), never a missing append.

Exit codes: 0 = ok (a missing/empty file is an empty run set), 1 = self-test failure, 2 = usage error.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
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
KINDS = ["pipeline", "fix", "fanout_leaf", "verifier", "review", "red"]

# Frozen live-run evidence (tools/fixtures/README.md): every reader-side test reads
# it read-only and asserts this sha256 before and after (telemetry.md
# §Fixture-Based Test Contract).
FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures",
                            "telemetry-harness-p3-2026-09-18.jsonl")
FIXTURE_SHA256 = "7e20b6307da09355f9aee504c451f0ed59e79ef9a33861cd72f370ea84af9237"

# ---------------------------------------------------------------------------
# Domain table (telemetry.md §Record Schema — the code table is the schema's
# single source of truth; §Record Schema and references/telemetry.md §2 are its
# renderings). Chunk 2 (harness-p4) lands the rows the implication formula reads
# plus the `const` row; Chunk 3 completes the table and adds `--lint`, which
# validates every record field against it and diffs it with the spec's table.
#
# A row whose group is the literal ``const`` declares a **schema constant**, not a
# record key: its members are the backticked tokens after the colon of its domain
# cell, and it is parsed into ``schema_constants()`` — never into the key set.
# ---------------------------------------------------------------------------

DOMAIN_TABLE: list[dict] = [
    {"group": "dispatch", "key": "kind", "domain": "`pipeline` | `fix` | `fanout_leaf` | `verifier` | `review` | `red`", "p4": False},
    {"group": "dispatch", "key": "stage", "domain": "`research` | `requirements` | `specs` | `plan` | `implement` | `verify` | `replan`", "p4": False},
    {"group": "dispatch", "key": "chunk", "domain": "int or null", "p4": False},
    {"group": "dispatch", "key": "iteration", "domain": "int or null", "p4": False},
    {"group": "dispatch", "key": "redo", "domain": "int or null", "p4": False},
    {"group": "dispatch", "key": "reason", "domain": "repair-packet `reason` enum or null", "p4": False},
    {"group": "const", "key": "FIX_ONLY_REASONS", "domain": "subset of `dispatch.reason`: `red_break`", "p4": True},
    {"group": "verdict", "key": "chunk_verdict", "domain": "`PASS` | `FAIL` | null", "p4": False},
    {"group": "verdict", "key": "review_verdict", "domain": "`APPROVE` | `APPROVE_WITH_FIXES` | `REJECT` | null", "p4": False},
    {"group": "verdict", "key": "red_verdict", "domain": "`BROKEN` | `HELD` | null", "p4": False},
    {"group": "gate", "key": "decision", "domain": "`proceed` | `fix` | `loop-back-to-fix` | `stop` | `redo` | `replan` | `revert` | `widen` | `accept` | `third-opinion` | `re-dispatch` | `override` | `other`", "p4": False},
]

_BACKTICK_RE = re.compile(r"`([^`]+)`")


def schema_constants() -> dict[str, set[str]]:
    """Parse every ``const`` row of the domain table into ``{name: member set}``.

    Members are the backticked tokens **after the colon** of the domain cell (the
    part before it names the superset, e.g. ``dispatch.reason``); a ``[p4]``-style
    marker token is not a member. Kept separate from the ``group.key`` set so a
    constant can never be mistaken for a record key (telemetry.md §Record Schema,
    ``const`` rows).
    """
    out: dict[str, set[str]] = {}
    for row in DOMAIN_TABLE:
        if row["group"] != "const":
            continue
        members = row["domain"].split(":", 1)[1] if ":" in row["domain"] else row["domain"]
        out[row["key"]] = {tok for tok in _BACKTICK_RE.findall(members) if not tok.startswith("[")}
    return out


# The fix-only reason subset — derived from the `const` row, never a bare code
# constant, so adding a reason later is a schema (table) change.
FIX_ONLY_REASONS: set[str] = schema_constants()["FIX_ONLY_REASONS"]

# Gate decisions that each dispatch exactly one fix (clause (a) of the implied-fix
# formula; a per-chunk `fix` normalises to `redo`, telemetry.md §Writer rule (ii)).
FIX_DECISIONS = {"loop-back-to-fix", "fix", "redo"}


def _sha256(path: str) -> str:
    """Hex sha256 of a file — used to assert the frozen fixture is untouched."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()

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
    """Return ``(records, skipped)``: parsed ``v == 1`` objects and the skipped count.

    A missing file is an empty run set (``([], 0)``) — the same
    ``n_before := 0 if absent`` rule the writer follows — so ``summarize``
    never errors on a repo that has not run a cycle yet.
    """
    records: list[dict] = []
    skipped = 0
    if not os.path.isfile(path):
        return records, skipped
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
                # Key by the rendered label, not the raw value: an out-of-domain
                # ``dispatch.chunk`` (telemetry.md §Record Schema: int or null) would
                # otherwise be interpolated verbatim into the ``c{c}:{n}`` cell and
                # render a doubled prefix such as ``cChunk 0:0``.
                label = _chunk_label(_get(r, "dispatch", "chunk"))
                redo_by_chunk[label] = max(redo_by_chunk[label], rc)
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
            "redos_per_chunk": " ".join(f"{c}:{n}" for c, n in sorted(redo_by_chunk.items(), key=lambda kv: str(kv[0]))) or "-",
            "contradiction_pauses": sum(1 for r in recs if _get(r, "verdict", "contradiction_class") is not None),
            "red_broken": red.count("BROKEN"),
            "red_held": red.count("HELD"),
            "wall_dispatch": _fmt_secs(wall_dispatch),
            "wall_gate": _fmt_secs(wall_gate),
        })
    return rows


def _chunk_label(chunk) -> str:
    """Render ``dispatch.chunk`` for the ``redos per chunk`` cell.

    The schema (``telemetry.md`` §Record Schema) fixes the field to ``int or null``.
    An int renders ``cN``, null renders ``c-``, and anything else — a writer that
    stored the ``### Chunk N:`` header string instead of the parsed integer — is
    folded into a single ``c?`` bucket rather than interpolated verbatim. The
    records behind ``c?`` are counted by :func:`out_of_domain_chunks` and reported
    on their own line, so the violation is visible instead of silent.
    """
    if isinstance(chunk, bool):  # bool is an int subclass; not a chunk number
        return "c?"
    if isinstance(chunk, int):
        return f"c{chunk}"
    if chunk is None:
        return "c-"
    return "c?"


def out_of_domain_chunks(records: list[dict]) -> int:
    """Count records whose ``dispatch.chunk`` violates the ``int or null`` domain.

    These records are dropped from the per-chunk block (:func:`chunk_rows` needs an
    int key) and are *not* counted by ``load``'s ``skipped`` tally, which only sees
    torn lines and unknown ``v``. Without this counter the violation would be
    invisible — the block would simply print ``(no per-chunk dispatches)``.
    """
    n = 0
    for r in records:
        ch = _get(r, "dispatch", "chunk")
        if ch is None:
            continue
        if isinstance(ch, bool) or not isinstance(ch, int):
            n += 1
    return n


PER_CHUNK_KINDS = ("pipeline", "fanout_leaf", "verifier", "fix")


def chunk_rows(records: list[dict]) -> list[dict]:
    """Per-chunk block: implement + verifier + fix dispatches and the max redo per chunk."""
    by_chunk: dict[int, dict] = {}
    for r in records:
        ch = _get(r, "dispatch", "chunk")
        if isinstance(ch, bool) or not isinstance(ch, int):
            continue  # null, or an out-of-domain value counted by out_of_domain_chunks()
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


def _sessions(records: list[dict]) -> list[tuple[str, str, int, list[dict]]]:
    """Split records into sessions: ``(workstream, run, session_no, records)``.

    ``dispatch.seq`` is 1-based **per orchestrator session** (telemetry.md §2), so a
    session is a maximal run of records — ordered by ``ts_dispatch`` within one
    (``cycle.workstream``, ``cycle.research_id``) group — whose ``seq`` strictly
    increases; a ``seq`` that does not exceed its predecessor opens a new session
    (Q-IMPL-HARNESSP3-018).
    """
    by_run: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in records:
        key = (str(_get(r, "cycle", "workstream", default="?")), str(_get(r, "cycle", "research_id")))
        by_run[key].append(r)
    out: list[tuple[str, str, int, list[dict]]] = []
    for (ws, run) in sorted(by_run):
        recs = sorted(by_run[(ws, run)],
                      key=lambda r: (_ts(r.get("ts_dispatch")) or datetime.min.replace(tzinfo=timezone.utc)))
        sessions: list[list[dict]] = []
        prev_seq = None
        for r in recs:
            seq = _get(r, "dispatch", "seq")
            seq = seq if isinstance(seq, int) else 0
            if prev_seq is None or seq <= prev_seq:
                sessions.append([])          # first record, or seq restarted → new session
            sessions[-1].append(r)
            prev_seq = seq
        for i, sess in enumerate(sessions, start=1):
            out.append((ws, run, i, sess))
    return out


def _int0(value) -> int:
    """``dispatch.redo`` / ``dispatch.iteration`` read as 0 when null or non-int."""
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _group_key(r: dict) -> tuple[str, str]:
    """The ``(stage, chunk)`` group of a record; the raw chunk value is kept (an
    out-of-domain header string still groups its own records, never a neighbour's)."""
    return (str(_get(r, "dispatch", "stage")), json.dumps(_get(r, "dispatch", "chunk")))


def mistyped_fix_seqs(sess: list[dict]) -> list[int]:
    """``seq`` of every implied fix that exists as a record of another kind.

    Mis-typed-fix rule (telemetry.md §Implication-Derived ``expected``): a non-``fix``
    record whose ``dispatch.reason`` is fix-only (clause (b)), or one carrying
    ``iteration >= 1`` / ``redo >= 1`` whose predecessor **at the same stage** decided
    a fix-dispatching option (clause (a)). It counts 0 toward ``missing.fix`` and is
    a ``--lint`` ``[mistyped-fix]`` finding — a wrong ``kind``, not a missing append.
    """
    out: list[int] = []
    last_decision_by_stage: dict[str, object] = {}
    for r in sess:
        d = r.get("dispatch") or {}
        stage = str(d.get("stage"))
        if d.get("kind") != "fix":
            fix_only = d.get("reason") in FIX_ONLY_REASONS
            after_fix_decision = (_int0(d.get("iteration")) >= 1 or _int0(d.get("redo")) >= 1) \
                and last_decision_by_stage.get(stage) in FIX_DECISIONS
            if fix_only or after_fix_decision:
                out.append(_int0(d.get("seq")))
        last_decision_by_stage[stage] = _get(r, "gate", "decision")
    return out


def reason_review_warnings(records: list[dict]) -> list[int]:
    """``seq`` of every ``reason: REVIEW`` record at ``iteration >= 1`` with **no**
    preceding ``loop-back-to-fix`` decision at its stage in the session.

    A ``--lint`` **warning** ``[reason-review]``, never a count: the shape cannot
    distinguish a mis-recorded fix from a mis-labelled first dispatch (p3 ``seq`` 3–5;
    telemetry.md §Implication-Derived ``expected``, mis-typed-fix rule).
    """
    out: list[int] = []
    for _ws, _run, _i, sess in _sessions(records):
        loop_back_seen: set[str] = set()
        for r in sess:
            d = r.get("dispatch") or {}
            stage = str(d.get("stage"))
            if d.get("reason") == "REVIEW" and _int0(d.get("iteration")) >= 1 and stage not in loop_back_seen:
                out.append(_int0(d.get("seq")))
            if _get(r, "gate", "decision") == "loop-back-to-fix":
                loop_back_seen.add(stage)
    return sorted(out)


def session_rows(records: list[dict]) -> list[dict]:
    """Per session: recorded vs implication-derived ``expected`` appends.

    ``expected := highest dispatch.seq + Σ missing.<kind>`` (telemetry.md
    §Implication-Derived ``expected`` and the Headline; REQ-TELEM-HARNESSP4-002, -003).
    The chunk-shaped implications are computed **per ``(stage, chunk)`` group** —
    the ``pipeline``/``fix`` records sharing one stage and chunk — never by summing
    ``1 + redo`` over records, because a compliant redo keeps the first attempt's
    record *and* adds a ``fix`` record (§Writer rule (iii)):

        attempts(group)  = 1 + max(redo) over the group's pipeline/fix records
        implied.verifier = Σ attempts over groups with a non-verifier chunk_verdict
        implied.pipeline = Σ over implement groups of (1 + #pipeline records with redo >= 1)
        implied.review   = #non-review records with review_verdict     (per stage)
        implied.red      = #non-red records with red_verdict            (per stage)
        implied.fix      = #records with gate.decision in FIX_DECISIONS  (clause (a))
                         + #non-fix records with reason in FIX_ONLY_REASONS (clause (b))
        missing.<kind>   = Σ_stage max(0, implied − recorded [− mistyped, fix only])

    Strictly post-cycle: a reader-side derivation from the file alone
    (REQ-TELEM-HARNESSP3-002, Q-IMPL-HARNESSP3-006) that never influences control flow.
    Row keys: ``workstream, run, session, recorded, highest_seq, expected, gap,
    kinds{kind: {implied, recorded, missing, mistyped}}, implement_missing,
    mistyped_fix_seqs, records``.
    """
    rows: list[dict] = []
    for ws, run, i, sess in _sessions(records):
        highest = max((_int0(_get(r, "dispatch", "seq")) for r in sess), default=0)
        recorded = len(sess)
        # implied / recorded per (stage, kind)
        implied: dict[tuple[str, str], int] = defaultdict(int)
        rec_by: dict[tuple[str, str], int] = defaultdict(int)
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        fix_gates: dict[tuple[str, str], int] = defaultdict(int)
        for r in sess:
            d = r.get("dispatch") or {}
            stage, kind = str(d.get("stage")), str(d.get("kind"))
            rec_by[(stage, kind)] += 1
            if kind in ("pipeline", "fix"):
                groups[_group_key(r)].append(r)
            v = r.get("verdict") or {}
            if kind != "review" and v.get("review_verdict") is not None:
                implied[(stage, "review")] += 1
            if kind != "red" and v.get("red_verdict") is not None:
                implied[(stage, "red")] += 1
            if _get(r, "gate", "decision") in FIX_DECISIONS:
                # clause (a) counts gate DECISIONS, not records: a chunk record and its
                # verifier (or a stage record and its review) share one gate and so one
                # ts_gate; a compliant file would otherwise imply two fixes per redo
                # (Q-IMPL-HARNESSP4-004). Falls back to seq when ts_gate is null.
                fix_gates[(stage, str(r.get("ts_gate") or f"seq:{_int0(d.get('seq'))}"))] += 1
            if kind != "fix" and d.get("reason") in FIX_ONLY_REASONS:
                implied[(stage, "fix")] += 1                       # clause (b)
        for (stage, _gate) in fix_gates:
            implied[(stage, "fix")] += 1                           # clause (a): one fix per deciding gate
        for (stage, _chunk), grecs in groups.items():
            attempts = 1 + max(_int0(_get(r, "dispatch", "redo")) for r in grecs)
            if any(_get(r, "verdict", "chunk_verdict") is not None and _get(r, "dispatch", "kind") != "verifier"
                   for r in grecs):
                implied[(stage, "verifier")] += attempts
            if stage == "implement":
                # the first attempt is always a pipeline dispatch; a redo recorded as
                # pipeline (the p3 collapsed shape) stands in for its own first attempt
                implied[(stage, "pipeline")] += 1 + sum(
                    1 for r in grecs
                    if _get(r, "dispatch", "kind") == "pipeline" and _int0(_get(r, "dispatch", "redo")) >= 1)
        mistyped = mistyped_fix_seqs(sess)
        mistyped_by_stage: dict[str, int] = defaultdict(int)
        for r in sess:
            if _int0(_get(r, "dispatch", "seq")) in mistyped:
                mistyped_by_stage[str(_get(r, "dispatch", "stage"))] += 1
        kinds: dict[str, dict] = {}
        implement_missing: dict[str, int] = {"pipeline": 0, "verifier": 0, "fix": 0}
        for kind in KINDS:
            stages = {st for (st, k) in list(implied) + list(rec_by) if k == kind}
            imp_total = sum(implied[(st, kind)] for st in stages)
            # pipeline is an implement-scoped implication, so its recorded count is too
            rec_stages = {"implement"} if kind == "pipeline" else stages
            rec_total = sum(rec_by[(st, kind)] for st in rec_stages)
            missing = 0
            for st in (rec_stages if kind == "pipeline" else stages):
                mt = mistyped_by_stage[st] if kind == "fix" else 0
                m = max(0, implied[(st, kind)] - rec_by[(st, kind)] - mt)
                missing += m
                if st == "implement" and kind in implement_missing:
                    implement_missing[kind] += m
            kinds[kind] = {"implied": imp_total, "recorded": rec_total, "missing": missing,
                           "mistyped": len(mistyped) if kind == "fix" else 0}
        expected = highest + sum(k["missing"] for k in kinds.values())
        rows.append({"workstream": ws, "run": run, "session": i,
                     "recorded": recorded, "highest_seq": highest, "expected": expected,
                     "gap": max(expected - recorded, 0), "kinds": kinds,
                     "implement_missing": implement_missing,
                     "mistyped_fix_seqs": mistyped, "records": sess})
    return rows


def _implication_lines(row: dict, label: str) -> list[str]:
    """Render one session's headline and per-kind ``implied vs recorded`` lines exactly
    as telemetry.md §Implication-Derived ``expected`` and the Headline shows them."""
    lines = [f"records-vs-expected: {row['recorded']} recorded, expected {row['expected']} ({row['gap']} missing){label}"]
    for kind in ["verifier", "pipeline", "review", "red", "fix"]:
        k = row["kinds"][kind]
        suffix = ""
        if kind == "fix" and k["mistyped"]:
            suffix = f"; {k['mistyped']} mis-typed — see --lint"
        tag = "        [implement]" if kind == "pipeline" else ""
        lines.append(f"  implied vs recorded — {kind:<8} : {k['implied']:>2} vs {k['recorded']:<2} "
                     f"({k['missing']} missing{suffix}){tag}")
    im = row["implement_missing"]
    parts = [f"{im['pipeline']} pipeline first attempts", f"{im['verifier']} verifier"]
    if im["fix"]:
        parts.append(f"{im['fix']} fix")
    lines.append(f"  implement: {sum(im.values())} missing ({' + '.join(parts)})")
    return lines


def summarize(records: list[dict], skipped: int) -> str:
    """Full report text: one stage table + per-chunk block per workstream, then the skipped line."""
    lines: list[str] = []
    by_ws: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_ws[str(_get(r, "cycle", "workstream", default="?"))].append(r)
    if not by_ws:
        # Missing/empty file or a filter that matches nothing: an empty table, not an error.
        lines.append("records: 0")
        lines += _table([], STAGE_COLUMNS)
        lines.append("")
    for ws in sorted(by_ws):
        recs = by_ws[ws]
        runs = sorted({str(_get(r, "cycle", "research_id")) for r in recs})
        lines.append(f"workstream: {ws}   records: {len(recs)}   runs (cycle.research_id): {', '.join(runs)}")
        lines += _table(stage_rows(recs), STAGE_COLUMNS)
        lines.append("")
        lines.append(f"per-chunk block (workstream {ws}) — implement + verifier + fix dispatches, max redo:")
        chunks = chunk_rows(recs)
        ws_bad = out_of_domain_chunks(recs)
        if chunks:
            lines += _table(chunks, CHUNK_COLUMNS)
            if ws_bad:
                lines.append(f"  ({ws_bad} record(s) excluded: dispatch.chunk out of domain — see the counter below)")
        elif ws_bad:
            # Never print a bare "no dispatches" when records exist but carry a chunk
            # value the schema does not allow: say why the block is empty.
            lines.append(f"  (per-chunk block empty: {ws_bad} record(s) excluded — dispatch.chunk out of domain; see the counter below)")
        else:
            lines.append("  (no per-chunk dispatches)")
        lines.append("")
    lines.append(f"skipped: {skipped} unknown-schema record(s)")
    # Sibling of the skipped line: records that parsed as v1 but carry a
    # ``dispatch.chunk`` outside the schema's ``int or null`` domain. They are not
    # in ``skipped`` (they are well-formed JSON with a known ``v``), so without
    # this line a writer-side schema violation would leave no trace in the report.
    lines.append(f"out-of-domain dispatch.chunk: {out_of_domain_chunks(records)} record(s) "
                 f"(schema: int or null — telemetry.md §Record Schema)")
    # Records-vs-expected: a sibling of the skipped line, so a cycle that lost an
    # append is visible post-cycle even if the absent gate line went unnoticed.
    # The headline is the TOTAL shortfall of every implied append, per session
    # (telemetry.md §Implication-Derived `expected` and the Headline, Q-REQ-P4-D).
    sessions = session_rows(records)
    if not sessions:
        lines.append("records-vs-expected: 0 recorded, expected 0 (0 missing)")
    for s in sessions:
        label = f"   [{s['workstream']}/{s['run']} session {s['session']}]" if len(sessions) > 1 else ""
        lines += _implication_lines(s, label)
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

        # Records-vs-expected (REQ-TELEM-HARNESSP3-002 / -HARNESSP4-002): the six-record
        # fixture is one session with no seq gap, but it is p3-shaped — chunk 1 carries a
        # chunk_verdict with no verifier record (1 implied verifier), and chunk 2 is a
        # fix at redo 1 whose first attempt was never recorded (2 verifiers + 1 pipeline)
        # — so the implication formula reads 4 missing appends.
        sessions = session_rows(records)
        check(len(sessions) == 1 and sessions[0]["highest_seq"] == 6 and sessions[0]["gap"] == 4,
              f"six-record fixture: one session, seq 6, 4 implied missing; got {[(x['highest_seq'], x['gap']) for x in sessions]}")
        check("records-vs-expected: 6 recorded, expected 10 (4 missing)" in report, "records-vs-expected headline")
        check("verifier :  3 vs 0  (3 missing)" in report and "pipeline :  2 vs 1  (1 missing)" in report, "six-record per-kind lines")

        gappy = [_record(dispatch={"seq": s, "kind": "pipeline", "stage": "implement"},
                         ts_dispatch=f"2026-09-17T1{i}:00:00Z")
                 for i, s in enumerate([1, 2, 5, 1])]
        grows = session_rows(gappy)
        check(len(grows) == 2, f"seq reset starts a new session, got {len(grows)}")
        check(grows[0]["expected"] == 5 and grows[0]["recorded"] == 3 and grows[0]["gap"] == 2,
              f"gap session counts: {grows[0] if grows else None}")
        check(grows[1]["gap"] == 0, "second session is gapless")
        greport = summarize(gappy, 0)
        check("records-vs-expected: 3 recorded, expected 5 (2 missing)" in greport, f"gap headline:\n{greport}")
        check("records-vs-expected: 1 recorded, expected 1 (0 missing)" in greport, "second-session headline")
        gpath = os.path.join(tmp, "gappy.jsonl")
        with open(gpath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(json.dumps(r, separators=(",", ":")) for r in gappy) + "\n")
        gbuf = io.StringIO()
        with contextlib.redirect_stdout(gbuf):
            grc = main(["summarize", "--file", gpath])
        check(grc == 0 and "(2 missing)" in gbuf.getvalue(), f"summarize on a gap fixture → exit {grc}, unchanged")

        # Implication-derived expected (REQ-TELEM-HARNESSP4-002, -003; telemetry.md
        # §Implication-Derived `expected` and the Headline). Synthetic fixtures, one per
        # implication, built from the same complete-record helper.
        def imp(seq, kind, stage, chunk=None, iteration=None, redo=None, reason=None,
                cv=None, rv=None, red=None, decision="proceed", gate_of=None):
            # gate_of=<seq>: this record fed the same gate as that record (shared ts_gate),
            # as a verifier does with its chunk record and a review with its stage record.
            return _record(dispatch={"seq": seq, "kind": kind, "stage": stage, "chunk": chunk,
                                     "iteration": iteration, "redo": redo, "reason": reason},
                           verdict={"chunk_verdict": cv, "review_verdict": rv, "red_verdict": red},
                           gate={"decision": decision},
                           ts_dispatch=f"2026-09-19T10:{seq:02d}:00Z",
                           ts_gate=f"2026-09-19T10:{(gate_of or seq):02d}:30Z")

        def one(recs):
            rows = session_rows(recs)
            check(len(rows) == 1, f"implication fixture: one session expected, got {len(rows)}")
            return rows[0]

        # FIX_ONLY_REASONS is parsed from the `const` row of the domain table, never a bare constant.
        const_rows = [r for r in DOMAIN_TABLE if r["group"] == "const"]
        check([r["key"] for r in const_rows] == ["FIX_ONLY_REASONS"], f"const rows: {const_rows}")
        check(schema_constants() == {"FIX_ONLY_REASONS": {"red_break"}}, f"schema constants: {schema_constants()}")
        check(FIX_ONLY_REASONS == {"red_break"}, f"FIX_ONLY_REASONS: {FIX_ONLY_REASONS}")

        # (1) verifier: a chunk record carrying chunk_verdict implies one verifier record.
        v = one([imp(1, "pipeline", "implement", chunk=1, cv="PASS")])
        check(v["kinds"]["verifier"] == {"implied": 1, "recorded": 0, "missing": 1, "mistyped": 0}, f"verifier implication: {v['kinds']['verifier']}")
        check(v["expected"] == 2 and v["gap"] == 1, f"verifier expected/gap: {v}")
        # (2) redo first attempt (p3 collapsed shape): attempts = 1 + max(redo) = 2.
        r2 = one([imp(1, "pipeline", "implement", chunk=1, redo=1, reason="VERIFIER_FAIL", cv="PASS")])
        check(r2["kinds"]["verifier"]["implied"] == 2, f"collapsed redo verifier: {r2['kinds']['verifier']}")
        check(r2["kinds"]["pipeline"] == {"implied": 2, "recorded": 1, "missing": 1, "mistyped": 0}, f"collapsed redo pipeline: {r2['kinds']['pipeline']}")
        check(r2["expected"] == 4 and r2["gap"] == 3, f"collapsed redo expected: {r2}")
        check(r2["implement_missing"] == {"pipeline": 1, "verifier": 2, "fix": 0}, f"implement missing: {r2['implement_missing']}")
        # (3) review and (4) red: a verdict carried by a record of another kind implies its own record.
        rv = one([imp(1, "pipeline", "research", rv="APPROVE")])
        check(rv["kinds"]["review"] == {"implied": 1, "recorded": 0, "missing": 1, "mistyped": 0}, f"review implication: {rv['kinds']['review']}")
        rd = one([imp(1, "pipeline", "verify", red="BROKEN")])
        check(rd["kinds"]["red"] == {"implied": 1, "recorded": 0, "missing": 1, "mistyped": 0}, f"red implication: {rd['kinds']['red']}")
        # (5) clause (b): a red_break pipeline record whose predecessor decided nothing is an
        # implied fix, present as a record of another kind → mis-typed, 0 missing.
        cb = one([imp(1, "pipeline", "verify", decision=None),
                  imp(2, "pipeline", "verify", iteration=1, reason="red_break", decision=None)])
        check(cb["kinds"]["fix"] == {"implied": 1, "recorded": 0, "missing": 0, "mistyped": 1}, f"clause (b): {cb['kinds']['fix']}")
        check(cb["mistyped_fix_seqs"] == [2], f"clause (b) mistyped seqs: {cb['mistyped_fix_seqs']}")
        # (6) a loop-back-to-fix followed by no record at all: 1 missing fix.
        lb = one([imp(1, "pipeline", "research", decision="loop-back-to-fix")])
        check(lb["kinds"]["fix"] == {"implied": 1, "recorded": 0, "missing": 1, "mistyped": 0}, f"loop-back no record: {lb['kinds']['fix']}")
        # (6b) the same decision followed by a pipeline record at iteration 1 is a mis-typed fix, not a gap.
        mt = one([imp(1, "pipeline", "research", rv="APPROVE_WITH_FIXES", decision="loop-back-to-fix"),
                  imp(2, "pipeline", "research", iteration=1, reason="REVIEW", rv="APPROVE_WITH_FIXES")])
        check(mt["kinds"]["fix"] == {"implied": 1, "recorded": 0, "missing": 0, "mistyped": 1}, f"mis-typed fix: {mt['kinds']['fix']}")
        check(reason_review_warnings(mt["records"]) == [], "a preceding loop-back-to-fix is not a [reason-review] warning")
        # reason: REVIEW at iteration >= 1 with no preceding loop-back-to-fix at the stage → warning, never a count.
        rr = one([imp(1, "pipeline", "requirements", iteration=1, reason="REVIEW", rv="APPROVE_WITH_FIXES")])
        check(rr["kinds"]["fix"] == {"implied": 0, "recorded": 0, "missing": 0, "mistyped": 0}, f"[reason-review] must not count: {rr['kinds']['fix']}")
        check(reason_review_warnings(rr["records"]) == [1], f"[reason-review] seqs: {reason_review_warnings(rr['records'])}")
        # (7) gapless negative fixture with one compliant redone chunk [C1]:
        # pipeline redo 0 + fix redo 1 (both with chunk_verdict) + two verifier records
        # → 2 implied verifiers / 1 implied pipeline / 0 missing anywhere.
        neg = [imp(1, "pipeline", "research", rv="APPROVE_WITH_FIXES"),
               imp(2, "review", "research", rv="APPROVE_WITH_FIXES"),
               imp(3, "pipeline", "implement", chunk=1, redo=0, cv="FAIL", decision="redo"),
               imp(4, "verifier", "implement", chunk=1, cv="FAIL", decision="redo", gate_of=3),
               imp(5, "fix", "implement", chunk=1, redo=1, reason="VERIFIER_FAIL", cv="PASS"),
               imp(6, "verifier", "implement", chunk=1, cv="PASS", gate_of=5),
               imp(7, "pipeline", "verify", red="HELD"),
               imp(8, "red", "verify", red="HELD", gate_of=7)]
        ng = one(neg)
        check(ng["kinds"]["verifier"] == {"implied": 2, "recorded": 2, "missing": 0, "mistyped": 0}, f"C1 verifier: {ng['kinds']['verifier']}")
        check(ng["kinds"]["pipeline"] == {"implied": 1, "recorded": 1, "missing": 0, "mistyped": 0}, f"C1 pipeline: {ng['kinds']['pipeline']}")
        check(ng["kinds"]["fix"] == {"implied": 1, "recorded": 1, "missing": 0, "mistyped": 0}, f"C1 fix: {ng['kinds']['fix']}")
        check(ng["expected"] == 8 and ng["gap"] == 0, f"C1 gapless: {ng}")
        # clause (a) is per deciding gate: the verifier sharing the chunk record's `redo`
        # gate (same ts_gate) must not imply a second fix (Q-IMPL-HARNESSP4-004).
        shared = one([imp(1, "pipeline", "implement", chunk=2, redo=0, cv="FAIL", decision="redo"),
                      imp(2, "verifier", "implement", chunk=2, cv="FAIL", decision="redo", gate_of=1)])
        check(shared["kinds"]["fix"]["implied"] == 1, f"shared gate implies one fix: {shared['kinds']['fix']}")
        nreport = summarize(neg, 0)
        check("records-vs-expected: 8 recorded, expected 8 (0 missing)" in nreport, f"C1 headline:\n{nreport}")
        check("verifier :  2 vs 2  (0 missing)" in nreport, "C1 verifier line")

        # The frozen p3 fixture (telemetry.md §Fixture-Based Test Contract): read-only,
        # sha256 asserted before and after, exact headline and per-kind numbers.
        check(os.path.exists(FIXTURE_PATH), f"frozen fixture missing: {FIXTURE_PATH}")
        if os.path.exists(FIXTURE_PATH):
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 before")
            frecs, fskipped = load(FIXTURE_PATH)
            fbuf = io.StringIO()
            with contextlib.redirect_stdout(fbuf):
                frc = main(["summarize", "--file", FIXTURE_PATH])
            freport = fbuf.getvalue()
            check(frc == 0 and fskipped == 0 and len(frecs) == 20, f"fixture load: rc {frc}, {len(frecs)} records, {fskipped} skipped")
            for needle in ["records-vs-expected: 20 recorded, expected 39 (19 missing)",
                           "verifier : 11 vs 0  (11 missing)",
                           "pipeline : 11 vs 8  (3 missing)",
                           "review   :  6 vs 2  (5 missing)",
                           "red      :  1 vs 2  (0 missing)",
                           "fix      :  2 vs 0  (0 missing; 2 mis-typed — see --lint)",
                           "implement: 14 missing (3 pipeline first attempts + 11 verifier)"]:
                check(needle in freport, f"fixture report lacks {needle!r}")
            frow = session_rows(frecs)[0]
            check(frow["mistyped_fix_seqs"] == [2, 18], f"fixture mis-typed fix seqs: {frow['mistyped_fix_seqs']}")
            check(reason_review_warnings(frecs) == [3, 4, 5], f"fixture [reason-review] seqs: {reason_review_warnings(frecs)}")
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 after")

        # Out-of-domain dispatch.chunk (the 2026-09-18 live break): a record whose
        # chunk is the "### Chunk N:" header STRING rather than the parsed int must
        # be visible, not silently dropped, and must not render a doubled prefix.
        bad = [_record(dispatch={"seq": 1, "kind": "pipeline", "stage": "implement", "chunk": "Chunk 0"},
                       gate={"redo_count": 0}),
               _record(dispatch={"seq": 2, "kind": "fix", "stage": "implement", "chunk": "Chunk 1"},
                       gate={"redo_count": 1})]
        check(out_of_domain_chunks(bad) == 2, f"out-of-domain count, got {out_of_domain_chunks(bad)}")
        check(out_of_domain_chunks(records) == 0, "clean fixture has no out-of-domain chunk")
        breport = summarize(bad, 0)
        check("out-of-domain dispatch.chunk: 2 record(s)" in breport, "out-of-domain counter line")
        check("cChunk" not in breport, "doubled 'c' prefix must not render")
        check("c?:1" in breport, f"out-of-domain chunks fold into c? , got:\n{breport}")
        check("per-chunk block empty: 2 record(s) excluded" in breport, "empty block states the exclusion")
        check("(no per-chunk dispatches)" not in breport, "no bare no-dispatches line when records were excluded")
        check(chunk_rows(bad) == [], "out-of-domain chunks stay out of the per-chunk block")
        check("out-of-domain dispatch.chunk: 0 record(s)" in report, "counter line present on a clean report")

        # Filters.
        check(len(filter_records(records, "nope", None)) == 0, "workstream filter")
        check(len(filter_records(records, None, "2026-09-18T00:00:00Z")) == 0, "since filter")

        # Missing file → empty run set: ([], 0), ``records: 0`` + empty table, exit 0.
        absent = os.path.join(tmp, "absent.jsonl")
        check(load(absent) == ([], 0), "missing file → ([], 0)")
        empty_report = summarize([], 0)
        check("records: 0" in empty_report, "missing file → records: 0")
        check(all(h in empty_report for _, h in STAGE_COLUMNS), "missing file → empty table header")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["summarize", "--file", absent])
        check(rc == 0 and "records: 0" in buf.getvalue(), f"summarize on missing file → exit {rc}")

    if failures:
        print("SELF-TEST FAIL:\n- " + "\n- ".join(failures))
        return 1
    print("SELF-TEST OK: budget grammar, six-record fixture (one row per stage, per-chunk block, skipped: 2), "
          "records-vs-expected (gapless + a seq gap), implication-derived expected (verifier, redo first attempt, "
          "review, red, clause (b), loop-back with no record, [reason-review] not counted, gapless compliant-redo "
          "fixture 2/1/0, frozen p3 fixture expected 39 with sha256 unchanged), out-of-domain dispatch.chunk "
          "counted and folded to c?, missing file → records: 0")
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
    # A missing file is an empty run set: load() returns ([], 0) and summarize()
    # prints an empty table with ``records: 0`` (exit 0), matching sdd-eval.py.
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
