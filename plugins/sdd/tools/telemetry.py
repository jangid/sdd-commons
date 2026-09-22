#!/usr/bin/env python3
"""telemetry — out-of-loop reader for the orchestrator's telemetry transcript.

Reads ``.sdd/telemetry.jsonl`` (one JSON record per dispatch, schema ``v`` in
the admitted set ``{1, 2}`` — Q-IMPL-HARNESSP4-002 — rendered in
``skills/orchestrate/references/telemetry.md`` §2 and ``docs/spec/telemetry.md``
§Record Schema from the ``DOMAIN_TABLE`` below, the schema's single source of
truth) and prints, per workstream, one row per ``dispatch.stage`` followed by a
per-chunk block (RS-008 probe 1 as a query). Contract: ``docs/spec/telemetry-reader.md``
§Out-of-Loop Reader (REQ-TELEM-HARNESSP2-009), §Schema Lint (REQ-TELEM-HARNESSP4-004).

This tool is **never invoked inside the orchestration loop** and no skill
reads the file it summarises; the file is gitignored, orchestrator-written and
never a phase-detection or staleness input.

Usage:
  tools/telemetry.py summarize [--file .sdd/telemetry.jsonl] [--workstream ID] [--since ISO] [--plan docs/ws/<id>/plan.md]
  tools/telemetry.py --lint [--file .sdd/telemetry.jsonl]   # every field against the domain table; exit 1 on a finding
  tools/telemetry.py migrate --file PATH [--out PATH]        # OPERATOR-RUN, between sessions: "Chunk N" chunk strings → int N; v-less flat records → v: 2 (flat-cg)
  tools/telemetry.py append [--file PATH] < record.json      # ORCHESTRATOR-ONLY: validate one record against the domain table, then append one line
  tools/telemetry.py --self-test      # synthetic fixtures in a temp dir + the frozen p3 fixture (read-only)
  tools/telemetry.py --help

``append`` (REQ-TELEM-PIPELINEOBSERVABILITY-001, ``docs/spec/telemetry.md`` §Writer)
is the writer's "append one record" step: it reads exactly one JSON value from
stdin, refuses anything that is not an object, a ``v`` outside the admitted set,
or a record with an ``enum`` / ``type`` / ``key-undeclared`` / ``key-missing``
finding (nothing written, exit non-zero), warns on stderr for ``cross-field`` and
``mistyped-fix``, and on exit 0 has written exactly one line. It prints nothing
that reads the file, so the gate's ``TELEMETRY: rec <n>`` stays the orchestrator's
session counter, advanced only on exit 0.

``--lint`` reports ``seq <n>: [<class>] <group.key>: <message>`` per violation
(classes enum / type / key-undeclared / key-missing / cross-field /
mistyped-fix) and ``WARN … [reason-review]`` warnings that never affect the
exit code. ``summarize`` adds per session ``widened dispatches: N; COMMIT:
INCOMPLETE (accepted): M`` and, with ``--plan``, the implement-stage floor derived from
the plan's ``### Chunk N:`` headers (REQ-TELEM-HARNESSP4-006, -007, -008).

Records with an unknown ``v`` and lines that are not JSON are skipped and
counted on a trailing ``skipped: N unknown-schema record(s)`` line. A sibling
``records-vs-expected:`` headline reports, per session, how many appends the
records imply versus how many are present — a post-cycle backstop for a missing
gate append (REQ-TELEM-HARNESSP3-002). ``expected`` starts from the highest
``dispatch.seq`` and adds every append **implied by a cross-field value the
writer did fill** (REQ-TELEM-HARNESSP4-002, -003; ``docs/spec/telemetry-reader.md``
§Implication-Derived ``expected`` and the Headline): a ``chunk_verdict`` implies
a ``verifier`` record, ``redo`` implies the first attempt, a carried review/red
verdict implies its ``review``/``red`` record, and a fix-dispatching gate
decision or a fix-only ``reason`` implies a ``fix`` record. An implied fix that
exists as a record of another kind is *mis-typed* (a ``--lint`` finding once
that subcommand lands), never a missing append.

``migrate`` (REQ-TELEM-HARNESSP4-005, ``docs/spec/telemetry-reader.md``
§In-Place Migration) rewrites every ``dispatch.chunk`` header string ``"Chunk N"`` to the
int ``N`` and stamps the record ``"migration": {"from": "chunk-string", "at":
<date>}``; ``summarize`` then renders those chunks **partial**, naming the
verifier / fix / redo records that were never written and cannot be
reconstructed. It is the **second exception** to the writer's append-only rule
(the first is the leaf-write revert): the operator runs it with **no
orchestrator session open** — never a leaf, never during a session, never from
a dispatch template — and only after ``--lint`` reports the records clean on
their typed fields. Without ``--out`` it rewrites in place via a sibling temp
file, a line-count check and a rename; it is idempotent; and any ``--file`` or
``--out`` under ``tools/fixtures/`` is refused with exit 2 and no write (the
frozen fixture is read-only evidence — ``tools/fixtures/README.md``).

Exit codes: 0 = ok (a missing/empty file is an empty run set), 1 = self-test failure or a
failed in-place rewrite (original left intact), 2 = usage error / fixture guard.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone

DEFAULT_FILE = ".sdd/telemetry.jsonl"
STAGES = ["research", "requirements", "specs", "plan", "implement", "verify", "replan"]
KINDS = ["pipeline", "fix", "fanout_leaf", "verifier", "review", "red"]

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)                    # the plugin root: plugins/sdd
# The repository root: `docs/` stays outside the plugin (CLAUDE.md §Repository
# Structure), so the two spec-side paths below resolve two levels above the
# plugin root — Q-IMPL-PIPELINEOBSERVABILITY-003 (the self-test was red at the
# Chunk 2 entry because they were resolved under `plugins/sdd/docs/`).
_ROOT = os.path.dirname(os.path.dirname(_REPO))
# The two human-readable renderings of the domain table that `--lint`
# (telemetry-reader.md §Schema Lint) checks itself against: the spec's
# §Record Schema table stayed in telemetry.md across the split, so SPEC_DOC
# is unchanged (telemetry.md §Moved Sections).
SPEC_DOC = os.path.join(_ROOT, "docs", "spec", "telemetry.md")
REF_DOC = os.path.join(_REPO, "skills", "orchestrate", "references", "telemetry.md")
# The p3 plan the `--plan` floor is exercised against (telemetry-reader.md §Fixture-Based Test Contract).
P3_PLAN = os.path.join(_ROOT, "docs", "ws", "harness-p3", "plan.md")

# Frozen live-run evidence (tools/fixtures/README.md): every reader-side test reads
# it read-only and asserts this sha256 before and after (telemetry-reader.md
# §Fixture-Based Test Contract).
FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures",
                            "telemetry-harness-p3-2026-09-18.jsonl")
FIXTURE_SHA256 = "7e20b6307da09355f9aee504c451f0ed59e79ef9a33861cd72f370ea84af9237"
P4_FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures",
                               "telemetry-harness-p4-2026-09-19.jsonl")
P4_FIXTURE_SHA256 = "ff5cf2864abc74c2c05449b86e5117f5c4ed8851b6b5f96617859b8b061ef370"
# The p3 fixture's `--lint` finding SET, order-insensitive: sha256 over the sorted
# finding lines (the summary line excluded) with each `[enum]` message's rendered
# member list stripped (`finding_set_sha`).  REQ-TELEM-HARNESSP5-006's sort may
# reorder the rendering, so the set — never the sequence — is the invariant; and a
# member added to the schema (2026-09-22: `POST_MANUAL`, `manual_intervention`,
# `malformed`) re-renders the `not in […]` list of an out-of-domain value without
# changing which findings exist, so the identity `seq: [class] field: value` — never
# the list — is what the pin holds (Q-IMPL-PIPELINEOBSERVABILITY-006).  Measured
# 2026-09-22 on the pre-delta tool: 66 findings, 3 warnings.
FIXTURE_LINT_SORTED_SHA256 = "73e6f8a44b9f334ca6aec0225c44dff7b71a5a179fe9d4ccfbcd98276af15987"
# The p4 fixture's pre-delta `--lint` finding SET under the same normalisation,
# measured 2026-09-22 before the four cross-field assertions (a)–(d) landed:
# 62 findings, 4 warnings. The (a)–(d) lines the fixtures DO raise are pinned
# separately by `(seq, rule)` (`P3_/P4_FIXTURE_GATE_RULE_FINDINGS`).
P4_FIXTURE_LINT_SORTED_SHA256 = "c4588cbf93c6450c4e9de7b8647d8e3d3cd69b8dab6117e4c2bd098b643076ae"
_MEMBER_LIST_TAIL_RE = re.compile(r"( not in \[.*)$")


def finding_set_sha(lines: list[str]) -> str:
    """sha256 over the sorted finding lines with each rendered member list stripped
    — the order- and member-list-insensitive identity of a `--lint` finding set."""
    return hashlib.sha256("\n".join(sorted(_MEMBER_LIST_TAIL_RE.sub("", ln) for ln in lines)).encode()).hexdigest()
# The frozen flat-record fixture (OP-1 of the pipeline-observability plan): every
# `v`-less line of the live file on 2026-09-22, read-only input of the `flat-cg`
# migration case; its sha256 is recorded in fixtures/README.md and asserted
# before and after (telemetry-reader.md §In-Place Migration, "Frozen fixture").
FLAT_FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures",
                                 "telemetry-flat-2026-09-22.jsonl")
FLAT_FIXTURE_SHA256 = "de57b9608ba3a78fbcdbc2525b8e91870481fe2bc3ecfbfa10eef4a4f7afd358"

# ---------------------------------------------------------------------------
# Domain table (telemetry.md §Record Schema — the code table is the schema's
# single source of truth; §Record Schema and references/telemetry.md §2 are its
# renderings). Every ``group.key`` of the record is a row: ``domain`` is the
# **exact text** of the rendered ``Type / domain`` cell up to its first ` — `
# (with markdown's ``\|`` unescaped), so `test_schema_table_agrees` can parse the
# code cell and the document cell through one function and diff the results;
# ``p4`` marks the rows added for harness-p4 (rendered as a trailing `[p4]`
# token) and is the ONLY source of the per-``v`` key set — ``v: 1`` records are
# validated against the unmarked rows, ``v: 2`` against all (Q-IMPL-HARNESSP4-002);
# ``check`` names the validator ``--lint`` runs on the value; ``members`` overrides
# the enum member set for a cell that only *names* an enum (``dispatch.reason``,
# ``replan_trigger``) rather than listing it.
#
# ``group`` is ``None`` for a top-level key, and the literal ``const`` declares a
# **schema constant**, not a record key: its members are the backticked tokens
# after the colon of its domain cell, and it is parsed into ``schema_constants()``
# — never into the key set (a record carrying its name is ``key-undeclared``).
# ---------------------------------------------------------------------------

# Repair-packet `reason` enum (harness-return-contract.md §Repair Packet, plus
# `red_break` — the RED_BREAK packet as the telemetry record spells it, the `const`
# row's member — and `THIRD_OPINION`, arbitrated-handoff.md). Q-IMPL-HARNESSP4-005.
# `POST_MANUAL` is the reason of the review dispatched after a manual intervention
# (harness-loop-control.md §Fix-Loop Cap §Footprint; loop-control.md §2b) — upper
# case, beside `REVIEW`, outside the fix-only subset (REQ-TELEM-PIPELINEOBSERVABILITY-003).
REASON_MEMBERS = {"REVIEW", "VERIFIER_FAIL", "PARTIAL_CONTINUE", "MERGE_CONFLICT", "red_break", "THIRD_OPINION",
                  "POST_MANUAL"}
REPLAN_TRIGGER_MEMBERS = {"stuck", "spike", "verification", "operator"}


def _row(group, key, domain, check, p4=False, members=None) -> dict:
    return {"group": group, "key": key, "domain": domain, "check": check, "p4": p4, "members": members}


DOMAIN_TABLE: list[dict] = [
    # the cell reads as scalar `int` to the parser; the admitted set is explicit
    _row(None, "v", "int, `1` | `2`", "v", members={"1", "2"}),
    _row(None, "ts_dispatch", "timestamp", "timestamp"),
    _row(None, "ts_return", "timestamp", "timestamp"),
    _row(None, "ts_gate", "timestamp", "timestamp"),
    _row("cycle", "workstream", "string id (`default` under marker `3`)", "string"),
    _row("cycle", "research_id", "`RS-…` id or null", "string_or_null"),
    _row("cycle", "kickoff_date", "date or null", "date_or_null"),
    _row("cycle", "marker", '`"3"` | `"4"`', "enum"),
    _row("dispatch", "seq", "int, **1-based per session**", "int"),
    _row("dispatch", "kind", "`pipeline` | `fix` | `fanout_leaf` | `verifier` | `review` | `red`", "enum"),
    _row("dispatch", "stage", "`research` | `requirements` | `specs` | `plan` | `implement` | `verify` | `replan`", "enum"),
    _row("dispatch", "chunk", "int or null", "int_or_null"),
    _row("dispatch", "iteration", "int or null", "int_or_null"),
    _row("dispatch", "redo", "int or null", "int_or_null"),
    _row("dispatch", "reason", "repair-packet `reason` enum or null; its fix-only subset is the `const` row `FIX_ONLY_REASONS` below",
         "enum_or_null", members=REASON_MEMBERS),
    _row("const", "FIX_ONLY_REASONS", "subset of `dispatch.reason`: `red_break` `[p4]`", "const", p4=True),
    _row("dispatch", "budget", "budget object (below)", "budget"),
    _row("dispatch", "write_scope_n", "int", "int"),
    _row("return", "status", "`COMPLETE` | `PARTIAL` | `BLOCKED` | `BUDGET_EXHAUSTED` | `MALFORMED`", "enum"),
    _row("return", "budget_consumed", "budget object + `self_reported: true`", "budget_consumed"),
    _row("return", "files_written_n", "int", "int"),
    _row("return", "commits_n", "int", "int"),
    _row("return", "tasks_completed_n", "int", "int"),
    _row("return", "failures_n", "int", "int"),
    _row("return", "ledger_n", "int", "int"),
    _row("return", "open_questions_n", "int", "int"),
    _row("return", "blocked_writes_n", "int", "int"),
    _row("return", "warnings", "list of enums ⊆ {`KEYS_MISSING`, `MULTIPLE_STATUS`, `FOREIGN_TOKEN`, `RETURN_DRIFT` `[p4]`}", "list_enum"),
    _row("scope", "token", "`CLEAN` | `VIOLATION` | null", "enum_or_null"),
    _row("scope", "in", "int", "int"),
    _row("scope", "advisory", "int", "int"),
    _row("scope", "out", "int", "int"),
    _row("scope", "history_rewrite", "bool", "bool"),
    _row("scope", "widened", "int, default 0 `[p4]`", "int_nonneg", p4=True),
    _row("verdict", "chunk_verdict", "`PASS` | `FAIL` | null", "enum_or_null"),
    _row("verdict", "review_verdict", "`APPROVE` | `APPROVE_WITH_FIXES` | `REJECT` | null", "enum_or_null"),
    _row("verdict", "red_verdict", "`BROKEN` | `HELD` | null", "enum_or_null"),
    _row("verdict", "findings", '`{"C": int, "M": int, "m": int}`', "findings"),
    _row("verdict", "malformed", "bool", "bool"),
    _row("verdict", "contradiction_class", "null | `b` | `c`", "enum_or_null"),
    # `manual_intervention` (the exhausted gate's option, followed by a `POST_MANUAL`
    # review — cross-field assertion (c)) and `malformed` (whichever option the
    # operator chose at a `REVIEW: MALFORMED` / `RETURN: MALFORMED` pause — the
    # decision assertion (d) exempts) were added 2026-09-22 (REQ-TELEM-PIPELINEOBSERVABILITY-003).
    _row("gate", "decision", "`proceed` | `fix` | `loop-back-to-fix` | `stop` | `redo` | `replan` | `revert` | `widen` | `accept` | `third-opinion` | `re-dispatch` | `override` | `manual_intervention` | `malformed` | `other`", "enum"),
    _row("gate", "decision_by", "`operator` | `policy`", "enum"),
    _row("gate", "fix_iteration", "int", "int"),
    _row("gate", "fix_cap", "int", "int"),
    _row("gate", "cap_raised", "int", "int"),
    _row("gate", "redo_count", "int or null", "int_or_null"),
    _row("gate", "replan_count", "int", "int"),
    _row("gate", "replan_cap", "int", "int"),
    _row(None, "replan_trigger", "enum or null", "enum_or_null", members=REPLAN_TRIGGER_MEMBERS),
    _row("git", "head_before", "short sha (`^[0-9a-f]{7,12}$`)", "sha"),
    _row("git", "head_after", "short sha (`^[0-9a-f]{7,12}$`)", "sha"),
    _row("commit", "token", "`COMPLETE` | `INCOMPLETE` | null `[p4]`", "enum_or_null", p4=True),
    _row("commit", "missing_n", "int `[p4]`", "int", p4=True),
    _row("commit", "extra_n", "int `[p4]`", "int", p4=True),
    # `from` is a two-member enum (`chunk-string`, `flat-cg`); `lost` is admitted
    # only beside `flat-cg` (telemetry-reader.md §In-Place Migration, "Lost, not reconstructed").
    _row(None, "migration", "optional `{from: chunk-string | flat-cg, at: date, lost?: {<kind>: int}}` `[p4]`", "migration", p4=True),
]

# Keys a record may omit: the `migration` marker is present only on migrated records.
OPTIONAL_KEYS = {(None, "migration")}
# Kinds whose gate commits nothing — a non-null `commit.token` on them is a
# cross-field finding (telemetry.md §`commit` Group).
NON_COMMITTING_KINDS = {"review", "verifier", "red"}
SHA_RE = re.compile(r"^[0-9a-f]{7,12}$")
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_P4_MARK = "`[p4]`"

# `migrate` (telemetry-reader.md §In-Place Migration, REQ-TELEM-HARNESSP4-005): the
# marker's first `from` member, the header-string shape it rewrites, and the
# read-only fixture directory the guard refuses to read from or write to.
MIGRATION_FROM = "chunk-string"
# The second shape (REQ-TELEM-PIPELINEOBSERVABILITY-002): every `v`-less record of
# the live file is a flat consumer-geometry / packaging record; the four kinds
# with a `v: 2` counterpart are migrated, every other kind is dropped and counted
# in `migration.lost` on the first migrated record of its workstream.
MIGRATION_FROM_FLAT = "flat-cg"
MIGRATION_FROM_MEMBERS = frozenset({MIGRATION_FROM, MIGRATION_FROM_FLAT})
FLAT_MAPPABLE_KINDS = ("pipeline", "review", "verifier", "red")
FLAT_LOST_KINDS = ("gate", "commit", "pr")   # the kinds the spec names; any other unmapped kind is counted under its own name
FLAT_SHA_PLACEHOLDER = "0000000"             # a flat record without `sha` (Q-IMPL-PIPELINEOBSERVABILITY-004)
_CHUNK_STRING_RE = re.compile(r"^Chunk (\d+)$")
FIXTURES_DIR = os.path.join(_HERE, "fixtures")


def parse_domain(cell: str) -> tuple[str, object]:
    """Classify one ``Type / domain`` cell — the same function reads the code
    table's string and a document's cell.

    Returns ``("enum", frozenset(members))`` when the cell is two or more
    backticked / ``null`` alternatives separated by ``|`` (``null`` is dropped
    from the members and admits ``None``), ``("list", frozenset(members))`` for a
    ``list of enums ⊆ {…}`` cell, and ``("scalar", <leading word>)`` otherwise
    (``int``, ``bool``, ``timestamp``, ``short``, ``date``, ``string``, …). Markdown
    ``\\|`` is unescaped, the trailing ``[p4]`` token is dropped and only the text
    before the first ` — ` is read; the prose after it is not compared.
    """
    text = cell.replace("\\|", "|").split(" — ", 1)[0].strip()
    text = text.replace(_P4_MARK, "").strip()
    if text.startswith("list of enums"):
        return "list", frozenset(t for t in _BACKTICK_RE.findall(text) if not t.startswith("["))
    parts = [p.strip() for p in text.split("|")]
    if len(parts) >= 2 and all(p == "null" or re.fullmatch(r"`[^`]+`", p) for p in parts):
        return "enum", frozenset(p.strip("`").strip('"') for p in parts if p != "null")
    return "scalar", text.split()[0].strip("`,") if text else ""


def _is_p4(cell: str) -> bool:
    """A row is ``[p4]`` when its cell (before any ` — ` prose) ends with the mark."""
    return cell.replace("\\|", "|").split(" — ", 1)[0].strip().endswith(_P4_MARK)


def parse_code_table(table: list[dict] | None = None) -> dict:
    """The code table in the shape :func:`schema_diff` compares:
    ``{"keys": {(group, key): (kind, members_or_type, p4)}, "constants": {name: members}}``."""
    table = DOMAIN_TABLE if table is None else table
    keys: dict[tuple, tuple] = {}
    constants: dict[str, set[str]] = {}
    for row in table:
        if row["group"] == "const":
            constants[row["key"]] = _const_members(row["domain"])
            continue
        kind, dom = parse_domain(row["domain"])
        keys[(row["group"], row["key"])] = (kind, dom, bool(row["p4"]))
    return {"keys": keys, "constants": constants}


def _const_members(cell: str) -> set[str]:
    """Members of a ``const`` cell: the backticked tokens **after the colon** (the
    part before it names the superset, e.g. ``dispatch.reason``); ``[p4]`` is not a member."""
    body = cell.split(" — ", 1)[0]  # the prose after the em-dash is not compared, as in parse_domain
    body = body.split(":", 1)[1] if ":" in body else body
    return {tok for tok in _BACKTICK_RE.findall(body) if not tok.startswith("[")}


_ROW_SPLIT_RE = re.compile(r"(?<!\\)\|")


def parse_doc_table(text: str, heading: str) -> dict:
    """Parse the ``| Group | Key | Type / domain |`` table that follows ``heading``
    in a rendering (docs/spec/telemetry.md §Record Schema, references/telemetry.md §2)
    into the same shape as :func:`parse_code_table`.

    Group cell ``—`` = top level, blank = the previous group continues, ``const`` = a
    schema constant; a ``Key`` cell may list several backticked keys sharing one cell.
    """
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.strip().startswith(heading)), None)
    if start is None:
        raise ValueError(f"heading not found: {heading}")
    hdr = next((i for i in range(start, len(lines)) if lines[i].startswith("| Group | Key | Type / domain |")), None)
    if hdr is None:
        raise ValueError(f"no `| Group | Key | Type / domain |` table under {heading}")
    keys: dict[tuple, tuple] = {}
    constants: dict[str, set[str]] = {}
    group: str | None = None
    for ln in lines[hdr + 2:]:
        if not ln.startswith("|"):
            break
        cells = [c.strip() for c in _ROW_SPLIT_RE.split(ln.strip().strip("|"))]
        if len(cells) < 3:
            continue
        gcell, kcell, dcell = cells[0], cells[1], cells[2]
        # `const` is a row-level marker, not a group: it never changes the running
        # group, so the blank-group rows after it still continue the previous group.
        is_const = gcell.strip("`") == "const"
        if gcell == "—":
            group = None
        elif gcell and not is_const:
            group = gcell.strip("`")
        for key in _BACKTICK_RE.findall(kcell):
            if is_const:
                constants[key] = _const_members(dcell.replace("\\|", "|"))
            else:
                kind, dom = parse_domain(dcell)
                keys[(group, key)] = (kind, dom, _is_p4(dcell))
    return {"keys": keys, "constants": constants}


def schema_diff(a: dict, b: dict) -> list[str]:
    """Differences between two parsed tables (empty when they agree): key set,
    enum/list member sets, scalar type word, ``[p4]`` mark and the constant set."""
    out: list[str] = []
    for k in sorted(set(a["keys"]) | set(b["keys"]), key=str):
        if k not in a["keys"] or k not in b["keys"]:
            out.append(f"{k[0] or '—'}.{k[1]}: present on one side only")
        elif a["keys"][k] != b["keys"][k]:
            out.append(f"{k[0] or '—'}.{k[1]}: {a['keys'][k]} != {b['keys'][k]}")
    if a["constants"] != b["constants"]:
        out.append(f"constants: {a['constants']} != {b['constants']}")
    return out


def schema_constants() -> dict[str, set[str]]:
    """Every ``const`` row of the domain table as ``{name: member set}`` — kept apart
    from the ``group.key`` set so a constant is never mistaken for a record key."""
    return parse_code_table()["constants"]


def enum_members(group: str | None, key: str) -> frozenset:
    """The admitted member set of an enum-typed row (explicit ``members`` override first)."""
    row = next(r for r in DOMAIN_TABLE if r["group"] == group and r["key"] == key)
    if row["members"] is not None:
        return frozenset(row["members"])
    kind, dom = parse_domain(row["domain"])
    return dom if kind in ("enum", "list") else frozenset()


def v_key_set(v: int) -> set[tuple]:
    """The fixed key set a ``v`` record is validated against, derived from the
    ``[p4]`` marks alone: ``v: 1`` → unmarked rows, ``v: 2`` → every row."""
    return {(r["group"], r["key"]) for r in DOMAIN_TABLE
            if r["group"] != "const" and (v >= 2 or not r["p4"])}


SCHEMA_V_ADMITTED: frozenset = enum_members(None, "v")  # {"1", "2"} as rendered → ints below
ADMITTED_V = {int(x) for x in SCHEMA_V_ADMITTED}
V_ADMITTED_TEXT = f"the admitted set {sorted(ADMITTED_V)}"


def _is_int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def v_admitted(v) -> bool:
    """The ONE admission test for a record's schema version (REQ-TELEM-HARNESSP5-004).

    Called from **both** ``load()`` paths — ``load()`` (what ``summarize`` reads)
    and ``_check_value``'s ``v`` branch (what ``--lint`` reads) — so the two agree
    by construction: an inadmissible ``v`` is skipped-and-counted by ``summarize``
    exactly as ``--lint`` rejects it with ``[type] v``.  The test is int-typed
    because ``2.0 in {1, 2}`` is ``True`` in Python, so the bare membership test
    admitted a float (telemetry-reader.md §Out-of-Loop Reader).
    """
    return _is_int(v) and v in ADMITTED_V

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
    """Return ``(records, skipped)``: parsed objects whose ``v`` is in the admitted
    set ``{1, 2}`` (the domain table's ``v`` row, Q-IMPL-HARNESSP4-002) and the
    skipped count — a ``v`` outside the set (``3``) is skipped and counted exactly
    as a torn line is (REQ-TELEM-HARNESSP2-009's unknown-``v`` tolerance).

    A missing file is an empty run set (``([], 0)``) — the same
    ``n_before := 0 if absent`` rule the writer follows — so ``summarize``
    never errors on a repo that has not run a cycle yet.
    """
    records: list[dict] = []
    skipped = 0
    for rec in load_raw(path):
        if not isinstance(rec, dict) or not v_admitted(rec.get("v")):
            skipped += 1  # torn line, or unknown schema version
            continue
        records.append(rec)
    return records, skipped


def load_raw(path: str) -> list:
    """Every non-blank line of ``path`` as a parsed JSON value, or ``None`` for a
    torn / non-JSON line (``--lint`` reports those; ``load`` counts them as skipped)."""
    out: list = []
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                out.append(None)
    return out


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
            if isinstance(r.get("migration"), dict):
                # A migrated record's three timestamps may be one value (the flat
                # writer took one): its 0 is not a measurement, so duration checks
                # skip it (telemetry-reader.md §In-Place Migration, `ts` row).
                continue
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


def partial_stamp(chunk: int) -> str:
    """The `partial` stamp of a migrated chunk, verbatim from telemetry-reader.md
    §In-Place Migration "Stamped-partial block shape": the block cannot be read as
    a full per-chunk history because the kinds it names were never appended."""
    return (f'partial — migrated from "Chunk {chunk}"; verifier, fix and redo records '
            "were never written and cannot be reconstructed")


def chunk_rows(records: list[dict]) -> list[dict]:
    """Per-chunk block: implement + verifier + fix dispatches and the max redo per chunk."""
    by_chunk: dict[int, dict] = {}
    for r in records:
        ch = _get(r, "dispatch", "chunk")
        if isinstance(ch, bool) or not isinstance(ch, int):
            continue  # null, or an out-of-domain value counted by out_of_domain_chunks()
        kind = _get(r, "dispatch", "kind")
        row = by_chunk.setdefault(ch, {"chunk": ch, "implement": 0, "verifier": 0, "fix": 0, "other": 0, "redo": 0, "total": 0, "note": ""})
        if isinstance(r.get("migration"), dict):
            row["note"] = partial_stamp(ch)  # any migrated record makes the whole chunk partial
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
    ("other", "other"), ("total", "dispatches"), ("redo", "max redo"), ("note", "note"),
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

    Mis-typed-fix rule (telemetry-reader.md §Implication-Derived ``expected``): a non-``fix``
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
    telemetry-reader.md §Implication-Derived ``expected``, mis-typed-fix rule).
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

    ``expected := highest dispatch.seq + Σ missing.<kind>`` (telemetry-reader.md
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
        for (stage, chunk_key), grecs in groups.items():
            attempts = 1 + max(_int0(_get(r, "dispatch", "redo")) for r in grecs)
            if any(_get(r, "verdict", "chunk_verdict") is not None and _get(r, "dispatch", "kind") != "verifier"
                   for r in grecs):
                implied[(stage, "verifier")] += attempts
            if stage == "implement" and chunk_key != "null":
                # Chunk groups ONLY (REQ-TELEM-HARNESSP5-002): a `(implement, null)`
                # group — the stage-level fix records of a `loop-back-to-fix` after the
                # stage review — implies no pipeline dispatch, because its first attempt
                # was the per-chunk pipeline records, not a null-chunk one.
                # The first attempt is always a pipeline dispatch; a redo recorded as
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
    as telemetry-reader.md §Implication-Derived ``expected`` and the Headline shows them."""
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


def summarize(records: list[dict], skipped: int, plan_path: str | None = None) -> str:
    """Full report text: one stage table + per-chunk block per workstream, then the
    skipped line, the records-vs-expected block and (with ``--plan``) the floor line."""
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
    # (telemetry-reader.md §Implication-Derived `expected` and the Headline, Q-REQ-P4-D).
    sessions = session_rows(records)
    if not sessions:
        lines.append("records-vs-expected: 0 recorded, expected 0 (0 missing)")
    for s in sessions:
        label = f"   [{s['workstream']}/{s['run']} session {s['session']}]" if len(sessions) > 1 else ""
        lines += _implication_lines(s, label)
        # scope.widened / commit group, per session (telemetry.md §scope.widened,
        # §commit Group): counts only — a v: 1 record has neither key and counts 0.
        widened = sum(1 for r in s["records"] if _int0(_get(r, "scope", "widened")) > 0)
        incomplete = sum(1 for r in s["records"] if _get(r, "commit", "token") == "INCOMPLETE")
        lines.append(f"  widened dispatches: {widened}; COMMIT: INCOMPLETE (accepted): {incomplete}")
    if plan_path:
        lines.append(plan_floor_line(plan_floor(records, plan_path)))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# --lint: every field of every record against the domain table
# (telemetry-reader.md §Schema Lint — `--lint` From One Domain Table, REQ-TELEM-HARNESSP4-004)
# ---------------------------------------------------------------------------


def _check_value(check: str, value, members: frozenset) -> str | None:
    """Return a one-line message when ``value`` violates ``check``; None when in domain."""
    if check == "v":
        return None if v_admitted(value) else f"{value!r} is not an int in {V_ADMITTED_TEXT}"
    if check == "timestamp":
        ok = isinstance(value, str) and _ts(value) is not None and (value.endswith("Z") or "+00:00" in value)
        return None if ok else f"{value!r} is not an ISO-8601 UTC timestamp"
    if check == "string":
        return None if isinstance(value, str) and value else f"{value!r} is not a non-empty string"
    if check == "string_or_null":
        return None if value is None or isinstance(value, str) else f"{value!r} is not a string or null"
    if check == "date_or_null":
        ok = value is None or (isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
        return None if ok else f"{value!r} is not a YYYY-MM-DD date or null"
    if check == "enum":
        return None if isinstance(value, str) and value in members else f"{value!r} not in {sorted(members)}"
    if check == "enum_or_null":
        return None if value is None or (isinstance(value, str) and value in members) else f"{value!r} not in {sorted(members)} or null"
    if check == "list_enum":
        if not isinstance(value, list) or any(v not in members for v in value):
            return f"{value!r} is not a list of {sorted(members)}"
        return None
    if check == "int":
        return None if _is_int(value) else f"{value!r} is not an int"
    if check == "int_nonneg":
        return None if _is_int(value) and value >= 0 else f"{value!r} is not an int ≥ 0"
    if check == "int_or_null":
        return None if value is None or _is_int(value) else f"{value!r} is not an int or null (a `### Chunk N:` header string is out of domain)"
    if check == "bool":
        return None if isinstance(value, bool) else f"{value!r} is not a bool"
    if check == "sha":
        if value == "HEAD":
            return '"HEAD" literal is not a sha'
        if isinstance(value, str) and len(value) == 40 and re.fullmatch(r"[0-9a-f]{40}", value):
            return "40-character sha; the schema fixes a short sha ^[0-9a-f]{7,12}$"
        return None if isinstance(value, str) and SHA_RE.fullmatch(value) else f"{value!r} does not match ^[0-9a-f]{{7,12}}$"
    if check == "budget":
        ok = isinstance(value, dict) and (value == {"unparsed": True} or
                                          all(k in value for k in ("tool_calls", "test_runs", "prototypes", "read_only")))
        return None if ok else f"{value!r} is not a budget object"
    if check == "budget_consumed":
        return None if isinstance(value, dict) and value.get("self_reported") is True else f"{value!r} lacks self_reported: true"
    if check == "findings":
        ok = isinstance(value, dict) and set(value) == {"C", "M", "m"} and all(_is_int(x) for x in value.values())
        return None if ok else f'{value!r} is not {{"C": int, "M": int, "m": int}}'
    if check == "migration":
        # Shape: `{from, at}` plus an optional `lost` — admitted ONLY beside
        # `from: flat-cg` as `{<kind>: int}` (a `lost` beside `chunk-string` is this
        # [type] finding); `from` outside its enum is `[enum] migration.from`, raised
        # by lint_records, not here.
        ok = isinstance(value, dict) and {"from", "at"} <= set(value) <= {"from", "at", "lost"} \
            and isinstance(value["from"], str) \
            and isinstance(value["at"], str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value["at"])
        if ok and "lost" in value:
            lost = value["lost"]
            ok = value["from"] == MIGRATION_FROM_FLAT and isinstance(lost, dict) \
                and all(isinstance(k, str) and _is_int(n) for k, n in lost.items())
        return None if ok else (f"{value!r} is not the declared {{from: chunk-string | flat-cg, at: date, "
                                "lost?: {<kind>: int}} shape (lost is admitted only beside flat-cg)")
    return None


def _fname(group, key) -> str:
    return f"{group}.{key}" if group else key


def lint_records(records: list, seqs: list | None = None) -> list[dict]:
    """Lint findings for in-memory records (already-parsed JSON values; ``None`` = a
    torn line). Each finding is ``{seq, class, field, message, warn}``; ``warn`` marks
    the ``[reason-review]`` warning, which never counts toward the exit code.

    Classes: ``enum``, ``type``, ``key-undeclared``, ``key-missing``, ``cross-field``,
    ``mistyped-fix`` (telemetry-reader.md §Schema Lint).
    """
    findings: list[dict] = []
    valid: list[dict] = []

    def add(seq, cls, field, msg, warn=False):
        findings.append({"seq": seq, "class": cls, "field": field, "message": msg, "warn": warn})

    for idx, rec in enumerate(records, start=1):
        if not isinstance(rec, dict):
            add(f"line {idx}", "type", "record", "not a JSON object")
            continue
        seq = _get(rec, "dispatch", "seq")
        seq = seq if _is_int(seq) else f"line {idx}"
        v = rec.get("v")
        vmsg = _check_value("v", v, frozenset())
        if vmsg:
            add(seq, "type", "v", vmsg)
            continue  # no key set to validate an unknown v against
        declared = v_key_set(v)
        groups = {g for (g, _k) in declared if g}
        # fixed key set per v: undeclared / missing keys (nested one level, per group)
        for k, val in rec.items():
            if k in groups:
                if not isinstance(val, dict):
                    add(seq, "type", k, f"{val!r} is not an object")
                    continue
                for sub in val:
                    if (k, sub) not in declared:
                        add(seq, "key-undeclared", f"{k}.{sub}", f"not a declared key of a v: {v} record")
            elif (None, k) not in declared and (None, k) not in OPTIONAL_KEYS:
                # an OPTIONAL key (the `migration` marker) is admitted on every v —
                # it only ever appears on the migrated v: 1 records (Q-IMPL-HARNESSP4-006)
                add(seq, "key-undeclared", k, f"not a declared key of a v: {v} record"
                    + (" (a schema constant, not a record key)" if k in schema_constants() else ""))
        for (g, k) in sorted(declared, key=str):
            if (g, k) in OPTIONAL_KEYS:
                continue
            holder = rec if g is None else rec.get(g)
            if isinstance(holder, dict) and k not in holder:
                add(seq, "key-missing", _fname(g, k), f"declared for v: {v} but absent")
        # per-field domains
        for row in DOMAIN_TABLE:
            g, k = row["group"], row["key"]
            if g == "const" or ((g, k) not in declared and (g, k) not in OPTIONAL_KEYS):
                continue
            holder = rec if g is None else rec.get(g)
            if not isinstance(holder, dict) or k not in holder:
                continue
            msg = _check_value(row["check"], holder[k], enum_members(g, k))
            if msg:
                cls = "enum" if row["check"] in ("enum", "enum_or_null", "list_enum") else "type"
                add(seq, cls, _fname(g, k), msg)
        # `migration.from` is a TWO-MEMBER enum (`chunk-string`, `flat-cg`), and the
        # shape check above admits any string: a malformed marker is `[type] migration`,
        # a `from` outside the member set is `[enum] migration.from` (telemetry-reader.md
        # §Schema Lint, fixed key set row; REQ-TELEM-HARNESSP5-008 case (c) as amended).
        mig = rec.get("migration")
        if isinstance(mig, dict) and isinstance(mig.get("from"), str) and mig["from"] not in MIGRATION_FROM_MEMBERS:
            add(seq, "enum", "migration.from", f"{mig['from']!r} not in {sorted(MIGRATION_FROM_MEMBERS)}")
        valid.append(rec)

    # cross-field (session-scoped)
    for _ws, _run, _i, sess in _sessions(valid):
        verifier_chunks = {(str(_get(r, "dispatch", "stage")), _get(r, "dispatch", "chunk"))
                           for r in sess if _get(r, "dispatch", "kind") == "verifier"}
        for s in mistyped_fix_seqs(sess):
            add(s, "mistyped-fix", "dispatch.kind",
                f"an implied fix recorded as kind {next((_get(r, 'dispatch', 'kind') for r in sess if _get(r, 'dispatch', 'seq') == s), None)!r}, not `fix`")
        for r in sess:
            d = r.get("dispatch") or {}
            seq = d.get("seq") if _is_int(d.get("seq")) else "?"
            kind, stage = d.get("kind"), str(d.get("stage"))
            if kind != "verifier" and _get(r, "verdict", "chunk_verdict") is not None \
                    and (stage, d.get("chunk")) not in verifier_chunks:
                add(seq, "cross-field", "verdict.chunk_verdict",
                    f"non-null on a {kind} record with no verifier record for chunk {d.get('chunk')!r} in the session")
            # git.head_before / head_after are the write-scope snapshot pair (write-scope.md §3):
            # HEAD_after is taken on the leaf's return, BEFORE the orchestrator commits, so a
            # compliant sequential leaf always shows equal heads at `proceed`. Equal heads are a
            # finding only when the record shows nothing landed: no landed commit group
            # (`commit.token` null, or a v1 record with no `commit` group at all) while the leaf
            # reports files written (Q-IMPL-HARNESSP4-005 item 2, Q-IMPL-HARNESSP4-007).
            # A `v: 1` record is EXEMPT (REQ-TELEM-HARNESSP5-003): it carries no field
            # that can prove landing (no `commit` group at all), so equal heads on it are
            # unprovable, not a finding — and no `migration` marker is stamped to say so.
            hb, ha = _get(r, "git", "head_before"), _get(r, "git", "head_after")
            if r.get("v") == 2 and stage == "implement" and kind in ("pipeline", "fix") and _get(r, "gate", "decision") == "proceed" \
                    and isinstance(hb, str) and SHA_RE.fullmatch(hb) and hb == ha \
                    and _get(r, "return", "files_written_n", default=1) != 0 \
                    and _get(r, "commit", "token") is None:
                add(seq, "cross-field", "git.head_after",
                    "proceed at implement with head_before == head_after and no landed commit group (nothing landed)")
            if kind in NON_COMMITTING_KINDS and _get(r, "commit", "token") is not None:
                add(seq, "cross-field", "commit.token", f"non-null on a {kind} record, whose gate commits nothing")
        for f in gate_rule_findings(sess):
            add(f["seq"], "cross-field", f["field"], f["message"])
    for s in reason_review_warnings(valid):
        stage = next((_get(r, "dispatch", "stage") for r in valid if _get(r, "dispatch", "seq") == s), "?")
        add(s, "reason-review", "dispatch.reason",
            f"REVIEW at iteration ≥ 1 with no preceding loop-back-to-fix at {stage}", warn=True)
    return sort_findings(findings)


# The positive verdict token of each read-only kind — the token assertion (a)
# reads (harness-write-scope.md §Git-State Observation: a verdict rendered beside
# `SCOPE: VIOLATION` is void and must not be consumed by a `proceed`).
POSITIVE_VERDICT_FIELD = {"verifier": "chunk_verdict", "review": "review_verdict", "red": "red_verdict"}
POSITIVE_VERDICT_TOKENS = frozenset({"PASS", "APPROVE", "APPROVE_WITH_FIXES", "HELD"})


def gate_rule_findings(sess: list[dict]) -> list[dict]:
    """The four cross-field assertions (a)–(d) of telemetry-reader.md §Schema Lint
    over one session, in ``seq`` order — each the mechanical witness of a gate
    rule bound in another spec (REQ-TELEM-PIPELINEOBSERVABILITY-003):

    (a) voided verdict consumed — a ``verifier``/``review``/``red`` record with
        ``scope.token = VIOLATION``, a positive verdict token and ``gate.decision =
        proceed`` (harness-write-scope.md §Git-State Observation);
    (b) ``fix_iteration`` counts a non-``REJECT`` — a ``review`` record whose
        ``gate.fix_iteration`` exceeds the run of consecutive ``REJECT`` tokens over
        the immediately preceding same-stage ``review`` records of the session
        (harness-loop-control.md §Fix-Loop Cap, ``reject_run``);
    (c) un-reviewed manual intervention — a ``gate.decision = manual_intervention``
        record whose next same-stage record is not a ``review`` with
        ``dispatch.reason = POST_MANUAL``, or whose ``gate.fix_iteration`` differs
        from the intervention record's (§Fix-Loop Cap §Footprint);
    (d) tier items under the wrong token — a ``review`` record in one of the four
        non-``legal`` cells of harness-return-contract.md §VERDICT Token's case
        table (``C ≥ 1`` under a non-``REJECT`` token; ``C = 0, M ≥ 1`` under
        ``APPROVE``; ``C = 0, M = 0`` under ``APPROVE_WITH_FIXES``; ``C = 0`` under
        ``REJECT``) whose ``gate.decision`` is not the ``malformed`` pause.

    Returns ``[{seq, field, message}]``; the caller classes them ``cross-field``.
    """
    out: list[dict] = []
    ordered = sorted(sess, key=lambda r: _int0(_get(r, "dispatch", "seq")))
    prior_reviews: dict[str, list] = defaultdict(list)   # stage → review verdict tokens, in order
    for i, r in enumerate(ordered):
        d = r.get("dispatch") or {}
        seq = d.get("seq") if _is_int(d.get("seq")) else "?"
        kind, stage = d.get("kind"), str(d.get("stage"))
        decision = _get(r, "gate", "decision")
        # (a)
        if kind in POSITIVE_VERDICT_FIELD and _get(r, "scope", "token") == "VIOLATION" and decision == "proceed":
            tok = _get(r, "verdict", POSITIVE_VERDICT_FIELD[kind])
            if tok in POSITIVE_VERDICT_TOKENS:
                out.append({"seq": seq, "field": "gate.decision",
                            "message": f"(a) voided verdict consumed: {kind} {tok} rendered beside SCOPE: VIOLATION and the gate proceeded"})
        if kind == "review":
            tok = _get(r, "verdict", "review_verdict")
            # (b): the run of consecutive REJECTs ending the preceding same-stage reviews
            run = 0
            for prev in reversed(prior_reviews[stage]):
                if prev != "REJECT":
                    break
                run += 1
            fi = _get(r, "gate", "fix_iteration")
            if _is_int(fi) and fi > run:
                out.append({"seq": seq, "field": "gate.fix_iteration",
                            "message": f"(b) {fi} exceeds the run of consecutive REJECTs ({run}) over the preceding {stage} reviews — an increment across a non-REJECT"})
            prior_reviews[stage].append(tok)
            # (d): the four non-legal cells of the 4×3 case table
            C, M = _get(r, "verdict", "findings", "C"), _get(r, "verdict", "findings", "M")
            if tok is not None and decision != "malformed" and _is_int(C) and _is_int(M):
                cell = None
                if C >= 1 and tok != "REJECT":
                    cell = f"C = {C} under {tok}"
                elif C == 0 and M >= 1 and tok == "APPROVE":
                    cell = f"M = {M} under APPROVE"
                elif C == 0 and M == 0 and tok == "APPROVE_WITH_FIXES":
                    cell = "0 material under APPROVE_WITH_FIXES"
                elif C == 0 and tok == "REJECT":
                    cell = "0 blocking under REJECT"
                if cell:
                    out.append({"seq": seq, "field": "verdict.review_verdict",
                                "message": f"(d) tier items under the wrong token: {cell}, gate decision {decision!r} is not the malformed pause"})
        # (c)
        if decision == "manual_intervention":
            nxt = next((n for n in ordered[i + 1:] if str(_get(n, "dispatch", "stage")) == stage), None)
            fi = _get(r, "gate", "fix_iteration")
            if nxt is None or _get(nxt, "dispatch", "kind") != "review" or _get(nxt, "dispatch", "reason") != "POST_MANUAL":
                out.append({"seq": seq, "field": "gate.decision",
                            "message": f"(c) manual_intervention at {stage} not followed by a POST_MANUAL review record"})
            elif _get(nxt, "gate", "fix_iteration") != fi:
                out.append({"seq": seq, "field": "gate.decision",
                            "message": f"(c) the POST_MANUAL review's fix_iteration {_get(nxt, 'gate', 'fix_iteration')!r} differs from the manual_intervention record's {fi!r}"})
    return out


def sort_findings(findings: list[dict]) -> list[dict]:
    """Stable-sort by ``(int seq ascending, then non-int seqs in insertion order)``
    across all three passes, so a cross-field finding on ``seq`` 2 renders before a
    type finding on ``seq`` 5 (REQ-TELEM-HARNESSP5-006).  ``sorted`` is stable, so
    non-int seqs (``line 3``, ``?``) keep their insertion order after the ints.
    """
    return sorted(findings, key=lambda f: (0, f["seq"]) if _is_int(f["seq"]) else (1, 0))


def lint(path: str) -> tuple[int, list[str]]:
    """Run the lint on a file: ``(exit code, output lines)`` — exit 1 on any finding,
    0 when clean (warnings alone stay 0)."""
    findings = lint_records(load_raw(path))
    lines: list[str] = []
    for f in findings:
        if f["warn"]:
            lines.append(f"WARN seq {f['seq']}: [{f['class']}] {f['field']} {f['message']}")
        else:
            lines.append(f"seq {f['seq']}: [{f['class']}] {f['field']}: {f['message']}")
    n_find = sum(1 for f in findings if not f["warn"])
    n_warn = len(findings) - n_find
    lines.append(f"lint: {n_find} finding(s), {n_warn} warning(s) — {path}")
    return (1 if n_find else 0), lines


# ---------------------------------------------------------------------------
# --plan floor (telemetry-reader.md §`--plan` Floor for Implement-Stage Expectations,
# REQ-TELEM-HARNESSP4-008 [may]) — Q-IMPL-HARNESSP4-005 fixes the shortfall's operands.
# ---------------------------------------------------------------------------

_CHUNK_HDR_RE = re.compile(r"^### Chunk (\d+):", re.MULTILINE)


def plan_floor(records: list[dict], plan_path: str) -> dict:
    """Implement-stage floor from the plan's ``### Chunk N:`` headers.

    ``chunks`` = header count = the pipeline floor; ``verifier_on`` when any
    implement chunk record carries a non-null ``chunk_verdict`` (the floor doubles
    with the verifier records); ``recorded`` = implement-stage ``pipeline``
    records; ``shortfall`` = ``max(0, chunks − recorded)`` — the verifier half is
    already reported by the implication line, so it is not counted twice.
    """
    with open(plan_path, encoding="utf-8") as fh:
        chunks = len(set(_CHUNK_HDR_RE.findall(fh.read())))
    impl = [r for r in records if _get(r, "dispatch", "stage") == "implement"]
    verifier_on = any(_get(r, "verdict", "chunk_verdict") is not None and _get(r, "dispatch", "chunk") is not None
                      for r in impl)
    recorded = sum(1 for r in impl if _get(r, "dispatch", "kind") == "pipeline")
    return {"chunks": chunks, "verifier_on": verifier_on, "recorded": recorded, "shortfall": max(0, chunks - recorded)}


def plan_floor_line(floor: dict) -> str:
    return (f"implement floor: {floor['chunks']} pipeline ({2 * floor['chunks']} with verifier); "
            f"recorded implement records: {floor['recorded']}; shortfall: {floor['shortfall']}"
            + ("" if floor["verifier_on"] else "   (no chunk_verdict recorded — verifier off or unrecorded)"))


# ---------------------------------------------------------------------------
# migrate (telemetry-reader.md §In-Place Migration of the 8 p3 Records, Stamped Partial,
# REQ-TELEM-HARNESSP4-005). Operator-run between sessions; never invoked by a
# skill, a leaf or a dispatch template.
# ---------------------------------------------------------------------------


def under_fixtures(path: str) -> bool:
    """True when ``path`` resolves inside ``tools/fixtures/`` — the guard's test."""
    root = os.path.realpath(FIXTURES_DIR)
    p = os.path.realpath(os.path.abspath(path))
    return p == root or p.startswith(root + os.sep)


def migrate_line(line: str, at: str) -> tuple[str, bool]:
    """Rewrite one JSONL line: ``(new_line, changed)``. Only a record whose
    ``dispatch.chunk`` is a ``"Chunk N"`` header string **and** that carries no
    ``migration`` marker yet is rewritten; every other line — an int chunk, an
    already-migrated record, a non-JSON or blank line — is returned byte-identical
    (idempotency)."""
    body = line.rstrip("\r\n")
    if not body.strip():
        return line, False
    try:
        rec = json.loads(body)
    except ValueError:
        return line, False
    if not isinstance(rec, dict) or "migration" in rec:
        return line, False
    ch = _get(rec, "dispatch", "chunk")
    m = _CHUNK_STRING_RE.fullmatch(ch.strip()) if isinstance(ch, str) else None
    if m is None:
        return line, False
    rec["dispatch"]["chunk"] = int(m.group(1))
    rec["migration"] = {"from": MIGRATION_FROM, "at": at}
    # keep the file's own separator style (compact vs spaced) so rewritten lines match their neighbours
    seps = (", ", ": ") if '": ' in body else (",", ":")
    return json.dumps(rec, ensure_ascii=False, separators=seps) + line[len(body):], True


def flat_kind(rec: dict) -> str | None:
    """The kind of a ``v``-less flat record: its ``kind`` key, else ``dispatch`` when
    that is the kind string (the packaging writer's spelling — ``dispatch`` is an
    int ordinal on the consumer-geometry records), else ``event`` (``gate``)
    (Q-IMPL-PIPELINEOBSERVABILITY-004)."""
    for key in ("kind", "dispatch", "event"):
        val = rec.get(key)
        if isinstance(val, str) and val:
            return val
    return None


def _flat_chunk(value):
    """``dispatch.chunk`` of a flat record: an int stays, a ``"Chunk N"`` header string
    is rewritten as in the first shape, anything else is null."""
    if _is_int(value):
        return value
    if isinstance(value, str) and _CHUNK_STRING_RE.fullmatch(value.strip()):
        return int(_CHUNK_STRING_RE.fullmatch(value.strip()).group(1))
    return None


def flat_to_v2(rec: dict, at: str) -> dict:
    """Map one mappable flat record to a complete ``v: 2`` record — the key mapping of
    telemetry-reader.md §In-Place Migration ("Second migration shape — `flat-cg`"):
    ``ts`` to all three timestamps, ``sha`` to the git heads, ``budget``/``consumed``,
    ``findings.{blocking,substantive,minor}`` to ``{C,M,m}``, ``fix_iteration``, and
    ``kind``/``ws``/``stage``/``chunk``; every other key takes its schema null / zero.
    Where the schema admits no null (``cycle.marker``, ``gate.decision``,
    ``gate.decision_by``, ``return.status``, the shas) the defaults are those of
    Q-IMPL-PIPELINEOBSERVABILITY-004. Nothing is back-filled and no gate decision is invented."""
    kind = flat_kind(rec)
    ts = rec.get("ts")
    # budget object: the flat writer recorded counts only
    fb = rec.get("budget")
    if isinstance(fb, dict) and any(k in fb for k in ("tool_calls", "test_runs")):
        budget = {"tool_calls": fb.get("tool_calls") if _is_int(fb.get("tool_calls")) else None,
                  "test_runs": fb.get("test_runs") if _is_int(fb.get("test_runs")) else None,
                  "prototypes": False, "read_only": False}
    else:
        budget = {"unparsed": True}
    fc = rec.get("consumed", rec.get("budget_consumed"))
    consumed: dict = {"self_reported": True}
    if isinstance(fc, dict):
        consumed = {"tool_calls": fc.get("tool_calls") if _is_int(fc.get("tool_calls")) else None,
                    "test_runs": fc.get("test_runs") if _is_int(fc.get("test_runs")) else None,
                    "self_reported": True}
    ff = rec.get("findings") if isinstance(rec.get("findings"), dict) else {}

    def count(*names) -> int:
        for n in names:
            if _is_int(ff.get(n)):
                return ff[n]
        return 0
    findings = {"C": count("blocking", "critical"), "M": count("substantive", "material"), "m": count("minor")}
    status = rec.get("status")
    if status is None:
        status = "COMPLETE"          # the flat writer recorded a dispatch that returned
    elif status not in enum_members("return", "status"):
        status = "MALFORMED"         # e.g. `FAILED` — no parseable return
    sha = rec.get("sha") if isinstance(rec.get("sha"), str) and SHA_RE.fullmatch(rec["sha"]) else FLAT_SHA_PLACEHOLDER
    scope_tok = rec.get("scope") if rec.get("scope") in ("CLEAN", "VIOLATION") else None
    rv = rec.get("verdict") if kind == "review" and rec.get("verdict") in enum_members("verdict", "review_verdict") else None
    red = rec.get("red_verdict") if kind == "red" and rec.get("red_verdict") in enum_members("verdict", "red_verdict") else None
    cv = rec.get("chunk_verdict") if rec.get("chunk_verdict") in enum_members("verdict", "chunk_verdict") else None
    fw = next((rec[k] for k in ("files_written", "paths_written") if _is_int(rec.get(k))), 0)
    fi = rec.get("fix_iteration") if _is_int(rec.get("fix_iteration")) else 0
    return {
        "v": 2, "ts_dispatch": ts, "ts_return": ts, "ts_gate": ts,
        "cycle": {"workstream": str(rec.get("ws") or "?"), "research_id": None, "kickoff_date": None, "marker": "4"},
        "dispatch": {"seq": 0, "kind": kind, "stage": rec.get("stage"), "chunk": _flat_chunk(rec.get("chunk")),
                     "iteration": rec.get("iteration") if _is_int(rec.get("iteration")) else None,
                     "redo": None, "reason": None, "budget": budget, "write_scope_n": 0},
        "return": {"status": status, "budget_consumed": consumed, "files_written_n": fw, "commits_n": 0,
                   "tasks_completed_n": 0, "failures_n": 0, "ledger_n": 0, "open_questions_n": 0,
                   "blocked_writes_n": 0, "warnings": []},
        "scope": {"token": scope_tok, "in": 0, "advisory": 0, "out": 0, "history_rewrite": False, "widened": 0},
        "verdict": {"chunk_verdict": cv, "review_verdict": rv, "red_verdict": red, "findings": findings,
                    "malformed": False, "contradiction_class": None},
        "gate": {"decision": "other", "decision_by": "operator", "fix_iteration": fi, "fix_cap": 0, "cap_raised": 0,
                 "redo_count": None, "replan_count": 0, "replan_cap": 0},
        "replan_trigger": None, "git": {"head_before": sha, "head_after": sha},
        "commit": {"token": None, "missing_n": 0, "extra_n": 0},
        "migration": {"from": MIGRATION_FROM_FLAT, "at": at},
    }


def migrate_flat(lines: list[str], at: str) -> tuple[list[str], int, dict]:
    """The ``flat-cg`` pass over already chunk-string-migrated lines: every ``v``-less
    JSON object is a flat record — a mappable kind is rewritten by :func:`flat_to_v2`,
    every other kind is dropped and counted per workstream, and the counts are
    stamped as ``migration.lost`` on the first migrated record of that workstream.
    Returns ``(new_lines, n_migrated, lost_by_ws)``; a workstream whose every
    record was lost has no record to carry its count, which the caller reports."""
    entries: list[tuple[str, dict | None]] = []   # (original line, migrated record or None)
    lost: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    first_migrated: dict[str, dict] = {}
    n_migrated = 0
    for line in lines:
        body = line.rstrip("\r\n")
        try:
            rec = json.loads(body) if body.strip() else None
        except ValueError:
            rec = None
        if not isinstance(rec, dict) or "v" in rec:
            entries.append((line, None))     # a typed record, a torn line, or blank: untouched
            continue
        ws = str(rec.get("ws") or "?")
        kind = flat_kind(rec)
        if kind not in FLAT_MAPPABLE_KINDS:
            lost[ws][str(kind)] += 1         # gate / commit / pr, or any other unmapped kind
            continue                         # dropped from the output
        new = flat_to_v2(rec, at)
        n_migrated += 1
        first_migrated.setdefault(ws, new)   # the record that will carry the workstream's `lost`
        entries.append((line, new))
    # stamp the counts on the shared record objects before serialising
    for ws, counts in lost.items():
        if ws in first_migrated:
            first_migrated[ws]["migration"]["lost"] = dict(sorted(counts.items()))
    out_lines = [line if new is None
                 else json.dumps(new, ensure_ascii=False, separators=(",", ":")) + line[len(line.rstrip("\r\n")):]
                 for line, new in entries]
    return out_lines, n_migrated, {ws: dict(c) for ws, c in lost.items()}


def migrate(path: str, out: str | None = None, at: str | None = None) -> tuple[int, str]:
    """Run the migration: ``(exit code, message)``.

    - fixture guard first: a ``path`` or ``out`` under ``tools/fixtures/`` → exit 2, no write;
    - ``out`` given → write there, input untouched;
    - in place → sibling temp file, line-count check, ``os.replace`` over the original
      (a failed check leaves the original intact and exits 1); nothing to rewrite → no write.

    Two shapes run in order: ``chunk-string`` (per line) and then ``flat-cg`` over
    every remaining ``v``-less record (telemetry-reader.md §In-Place Migration); the
    line-count check allows exactly the lost records the second shape dropped.
    """
    for p in (path, out):
        if p and under_fixtures(p):
            return 2, f"refused: {p} is under tools/fixtures/ — read-only evidence, no write performed"
    if not os.path.isfile(path):
        return 2, f"error: --file not found: {path}"
    at = at or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines(keepends=True)
    new_lines: list[str] = []
    n_changed = 0
    for line in lines:
        new, changed = migrate_line(line, at)
        new_lines.append(new)
        n_changed += changed
    new_lines, n_flat, lost = migrate_flat(new_lines, at)
    n_lost = sum(sum(c.values()) for c in lost.values())
    n_changed += n_flat
    summary = f"migrated {n_changed} record(s) of {len(lines)} line(s)"
    if n_flat or n_lost:
        per_ws = "; ".join(f"{ws}: {sum(c.values())} lost ({', '.join(f'{k} {n}' for k, n in sorted(c.items()))})"
                           for ws, c in sorted(lost.items()))
        summary += f" — flat-cg: {n_flat} migrated, {n_lost} lost, not reconstructed" + (f" [{per_ws}]" if per_ws else "")
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.writelines(new_lines)
        return 0, f"{summary} → {out} ({path} untouched)"
    if n_changed == 0:
        return 0, f"{summary} — {path} unchanged, nothing written"
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(prefix=os.path.basename(path) + ".", suffix=".migrate", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.writelines(new_lines)
        with open(tmp_path, encoding="utf-8") as fh:
            written = fh.read().splitlines(keepends=True)
        if len(written) != len(lines) - n_lost:
            os.unlink(tmp_path)
            return 1, f"error: line count changed ({len(lines)} → {len(written)}, {n_lost} lost expected); {path} left intact"
        os.replace(tmp_path, path)
    except OSError as exc:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return 1, f"error: in-place rewrite failed ({exc}); {path} left intact"
    return 0, f"{summary} — {path} rewritten in place (marker at: {at})"


# ---------------------------------------------------------------------------
# append (telemetry.md §Writer, "The append is `telemetry.py append`, and it
# validates before it writes" — REQ-TELEM-PIPELINEOBSERVABILITY-001). The
# orchestrator is the only caller; no dispatch template names it.
# ---------------------------------------------------------------------------

# Finding classes that refuse the write; `cross-field` and `mistyped-fix` (and the
# `reason-review` warning) need a sibling record the single-record call cannot see,
# so they are stderr warnings only.
APPEND_FATAL_CLASSES = frozenset({"enum", "type", "key-undeclared", "key-missing"})


def append(path: str, text: str) -> tuple[int, list[str]]:
    """Validate one JSON value and append it as one line: ``(exit code, stderr lines)``.

    Checks, in order (telemetry.md §Writer table): (1) the text is exactly one JSON
    **object**; (2) ``v`` is admitted through the shared helper :func:`v_admitted`;
    (3) ``lint_records([record])`` returns zero findings of the fatal classes.  Any
    failure exits non-zero with nothing written.  Exit 0 follows one append-only
    write of exactly one line.  Nothing here reads the file — no line number, no
    count — so the writer's zero-reads rule holds by construction and ``<n>`` stays
    the orchestrator's session counter.
    """
    try:
        value = json.loads(text)
    except ValueError as exc:
        return 1, [f"append: stdin is not exactly one JSON value ({exc.msg} at char {exc.pos}); nothing written"]
    if not isinstance(value, dict):
        return 1, ["append: the JSON value is not an object; nothing written"]
    if not v_admitted(value.get("v")):
        return 1, [f"append: v {value.get('v')!r} is not an int in {V_ADMITTED_TEXT}; nothing written"]
    findings = lint_records([value])
    fatal = [f for f in findings if f["class"] in APPEND_FATAL_CLASSES]
    lines = [f"append: WARN [{f['class']}] {f['field']} {f['message']}"
             for f in findings if f["class"] not in APPEND_FATAL_CLASSES]
    if fatal:
        lines += [f"append: [{f['class']}] {f['field']}: {f['message']}" for f in fatal]
        lines.append(f"append: {len(fatal)} finding(s) against the domain table; nothing written")
        return 1, lines
    directory = os.path.dirname(os.path.abspath(path))
    try:
        os.makedirs(directory, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
    except OSError as exc:
        return 1, lines + [f"append: write failed ({exc.strerror or exc}); nothing written"]
    return 0, lines


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------


def _record2(**over) -> dict:
    """A complete ``v: 2`` record: the v1 record plus the ``[p4]`` groups
    (``scope.widened`` 0, ``commit`` ``{null, 0, 0}``) and distinct git heads."""
    base = _record(git={"head_before": "c38922d", "head_after": "d49a33e"})
    base["v"] = 2
    base["scope"]["widened"] = 0
    base["commit"] = {"token": None, "missing_n": 0, "extra_n": 0}
    for group, vals in over.items():
        if isinstance(vals, dict) and isinstance(base.get(group), dict):
            base[group].update(vals)
        else:
            base[group] = vals
    return base


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
    lines.append(json.dumps({"v": 3, "ts_dispatch": "2026-09-17T11:00:00Z"}))  # unknown schema (v outside {1, 2}) → skipped
    lines.append("{this is not json")                                             # torn line → skipped
    return lines


# --- spec-named self-test cases -------------------------------------------
# The specs name these four cases by identifier (`telemetry-reader.md` §Automated,
# §Fixture-Based Test Contract and `telemetry.md` §Automated), so a reader grepping
# a spec-named test finds it here. Each takes the `self_test()` `check(cond, msg)`
# collector and adds no output of its own.


def _lint_classes(recs) -> dict:
    """``{class: [<group.key> …]}`` of the lint findings on in-memory ``recs``."""
    out: dict = defaultdict(list)
    for f in lint_records(recs):
        out[f["class"]].append(f["field"])
    return out


def test_advisory_cases(check) -> None:
    """The three verifier-advisory cases of REQ-TELEM-HARNESSP5-008
    (`telemetry-reader.md` §Schema Lint — Verifier-advisory self-test cases):
    (a) `commit.token` non-null on a non-committing kind other than `review`;
    (b) `dispatch.reason: RED_BREAK` (uppercase) — the canonical spelling is
    `red_break`; (c) `migration.from` outside the one-member `chunk-string` enum.
    """
    # (a) verifier and red gates commit nothing, so a non-null commit.token is a
    #     [cross-field] finding; a pipeline record with the same group is clean.
    verifier = _record2(dispatch={"seq": 1, "kind": "verifier", "stage": "implement", "chunk": 1},
                        verdict={"chunk_verdict": "PASS"},
                        commit={"token": "COMPLETE", "missing_n": 0, "extra_n": 0})
    red = _record2(dispatch={"seq": 1, "kind": "red", "stage": "verify"},
                   verdict={"red_verdict": "HELD"},
                   commit={"token": "INCOMPLETE", "missing_n": 1, "extra_n": 0})
    for label, rec in (("verifier", verifier), ("red", red)):
        check(_lint_classes([rec]).get("cross-field") == ["commit.token"],
              f"advisory (a): commit.token on a {label} record is not a [cross-field] finding: {_lint_classes([rec])}")
    committing = _record2(dispatch={"seq": 1, "kind": "pipeline", "stage": "implement", "chunk": 1},
                          commit={"token": "COMPLETE", "missing_n": 0, "extra_n": 0})
    check("commit.token" not in _lint_classes([committing]).get("cross-field", []),
          f"advisory (a): a committing kind was flagged: {_lint_classes([committing])}")

    # (b) the canonical spelling is `red_break`; the uppercase packet name is out of domain.
    upper = _record2(dispatch={"seq": 1, "kind": "fix", "stage": "verify", "iteration": 1, "reason": "RED_BREAK"})
    check(_lint_classes([upper]).get("enum") == ["dispatch.reason"],
          f"advisory (b): reason RED_BREAK is not an [enum] finding: {_lint_classes([upper])}")
    canonical = _record2(dispatch={"seq": 1, "kind": "fix", "stage": "verify", "iteration": 1, "reason": "red_break"})
    check("dispatch.reason" not in _lint_classes([canonical]).get("enum", []),
          f"advisory (b): the canonical red_break spelling was flagged: {_lint_classes([canonical])}")

    # (c) migration.from is a two-member enum {chunk-string, flat-cg}; the shape check
    #     admits any string. Re-pointed 2026-09-22 at `flat-xx` — outside BOTH members
    #     (REQ-TELEM-HARNESSP5-008 as amended).
    other = {**_record(dispatch={"chunk": 3}), "migration": {"from": "flat-xx", "at": "2026-09-19"}}
    check(_lint_classes([other]).get("enum") == ["migration.from"],
          f"advisory (c): migration.from flat-xx outside the enum is not an [enum] finding: {_lint_classes([other])}")
    for member in (MIGRATION_FROM, MIGRATION_FROM_FLAT):
        declared = {**_record(dispatch={"chunk": 3}), "migration": {"from": member, "at": "2026-09-19"}}
        check("migration.from" not in _lint_classes([declared]).get("enum", []),
              f"advisory (c): the declared {member} value was flagged: {_lint_classes([declared])}")


def test_p4_fixture_frozen(check) -> None:
    """The frozen-fixture contract of REQ-TELEM-HARNESSP5-007
    (`telemetry-reader.md` §Fixture-Based Test Contract): the p4 fixture's sha256
    matches `tools/fixtures/README.md`, it is 67 lines, and the p3 fixture is
    byte-identical to `main`. Read-only — nothing here opens a fixture for writing.
    """
    check(os.path.exists(P4_FIXTURE_PATH), f"frozen p4 fixture missing: {P4_FIXTURE_PATH}")
    if not os.path.exists(P4_FIXTURE_PATH):
        return
    check(_sha256(P4_FIXTURE_PATH) == P4_FIXTURE_SHA256, "p4 fixture sha256 (contract) before")
    with open(P4_FIXTURE_PATH, encoding="utf-8") as fh:
        n_lines = sum(1 for _ in fh)
    check(n_lines == 67, f"p4 fixture is {n_lines} lines, the contract fixes 67")
    readme = os.path.join(FIXTURES_DIR, "README.md")
    check(os.path.exists(readme), f"fixtures README missing: {readme}")
    if os.path.exists(readme):
        text = open(readme, encoding="utf-8").read()
        check(P4_FIXTURE_SHA256 in text, "the p4 fixture sha256 is not recorded in tools/fixtures/README.md")
        check(FIXTURE_SHA256 in text, "the p3 fixture sha256 is not recorded in tools/fixtures/README.md")
    if os.path.exists(FIXTURE_PATH):
        check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "p3 fixture sha256 (contract)")
        # `git diff --stat main -- <p3 fixture>` is empty: the frozen p3 fixture is
        # never touched by this branch. Skipped when `main` is unreachable (a shallow
        # clone or a checkout without the branch), never failed on that account.
        try:
            have_main = subprocess.run(["git", "rev-parse", "--verify", "main"], cwd=_REPO,
                                       capture_output=True, text=True).returncode == 0
            if have_main:
                diff = subprocess.run(["git", "diff", "--stat", "main", "--", FIXTURE_PATH], cwd=_REPO,
                                      capture_output=True, text=True)
                check(diff.returncode == 0 and diff.stdout.strip() == "",
                      f"git diff --stat main -- <p3 fixture> is not empty: {diff.stdout.strip()!r}")
        except OSError:
            pass  # no git binary: the sha256 assertions above still hold the contract
    check(_sha256(P4_FIXTURE_PATH) == P4_FIXTURE_SHA256, "p4 fixture sha256 (contract) after")


def test_stage_level_fix_has_null_chunk_verdict(check) -> None:
    """REQ-TELEM-HARNESSP5-001 (`telemetry.md` §Automated): an implement-stage
    `loop-back-to-fix` (`chunk: null`, `iteration: 1`) whose two chunk verifiers both
    returned PASS appends a `fix` record with `verdict.chunk_verdict: null` beside two
    `verifier` records carrying PASS; a per-chunk redo still copies the verdict onto
    its own record. Both shapes lint clean.
    """
    def rec(seq, kind, stage, chunk=None, iteration=None, redo=None, reason=None, cv=None, decision="proceed"):
        return _record2(dispatch={"seq": seq, "kind": kind, "stage": stage, "chunk": chunk,
                                  "iteration": iteration, "redo": redo, "reason": reason},
                        verdict={"chunk_verdict": cv},
                        gate={"decision": decision, "fix_iteration": iteration or 0, "redo_count": redo},
                        ts_dispatch=f"2026-09-19T10:{seq:02d}:00Z", ts_gate=f"2026-09-19T10:{seq:02d}:30Z")
    sess = [rec(1, "pipeline", "implement", chunk=1, redo=0, cv="PASS"),
            rec(2, "verifier", "implement", chunk=1, cv="PASS"),
            rec(3, "pipeline", "implement", chunk=2, redo=0, cv="PASS"),
            rec(4, "verifier", "implement", chunk=2, cv="PASS"),
            rec(5, "fix", "implement", chunk=None, iteration=1, reason="REVIEW", cv=None,
                decision="loop-back-to-fix")]
    stage_fix = sess[-1]
    check(_get(stage_fix, "dispatch", "chunk") is None and _get(stage_fix, "verdict", "chunk_verdict") is None,
          "the stage-level fix record must carry chunk null and chunk_verdict null")
    check([_get(r, "verdict", "chunk_verdict") for r in sess if _get(r, "dispatch", "kind") == "verifier"] == ["PASS", "PASS"],
          "both chunk verifiers must keep their PASS verdict")
    check(_lint_classes(sess).get("cross-field") is None,
          f"the stage-level fix shape raised a cross-field finding: {_lint_classes(sess)}")
    # a per-chunk redo copies the verdict onto its own record and stays clean
    redo = sess[:4] + [rec(5, "fix", "implement", chunk=2, iteration=1, redo=1, reason="VERIFIER_FAIL", cv="FAIL",
                           decision="redo")]
    check(_get(redo[-1], "verdict", "chunk_verdict") == "FAIL" and _get(redo[-1], "dispatch", "chunk") == 2,
          "a per-chunk redo must copy its chunk verdict onto its own record")
    check(_lint_classes(redo).get("cross-field") is None,
          f"the per-chunk redo shape raised a cross-field finding: {_lint_classes(redo)}")


def test_commit_group_records_closing_line(check) -> None:
    """REQ-TELEM-HARNESSP5-005 (`telemetry.md` §Automated): a gate that renders
    `COMMIT: INCOMPLETE`, is amended and re-renders `COMPLETE` appends
    `commit.token: COMPLETE`; the same gate resolved `accept (note)` appends
    `INCOMPLETE`, which `summarize` counts on its `COMMIT: INCOMPLETE (accepted)` line.
    """
    def rec(token, missing_n=0):
        return _record2(dispatch={"seq": 1, "kind": "pipeline", "stage": "implement", "chunk": 1},
                        commit={"token": token, "missing_n": missing_n, "extra_n": 0},
                        git={"head_before": "c38922d", "head_after": "d49a33e"})
    amended = rec("COMPLETE")
    accepted = rec("INCOMPLETE", missing_n=1)
    check(_get(amended, "commit", "token") == "COMPLETE", "an amended gate appends commit.token COMPLETE")
    check(_get(accepted, "commit", "token") == "INCOMPLETE" and _get(accepted, "commit", "missing_n") == 1,
          "an accepted (note) gate appends commit.token INCOMPLETE with the missing count")
    for label, rec_ in (("amended", amended), ("accepted", accepted)):
        check(_lint_classes([rec_]).get("cross-field") is None and _lint_classes([rec_]).get("enum") is None,
              f"the {label} commit group does not lint clean: {_lint_classes([rec_])}")
    check("COMMIT: INCOMPLETE (accepted): 1" in summarize([accepted], 0),
          "summarize does not count the accepted INCOMPLETE gate")
    check("COMMIT: INCOMPLETE (accepted): 0" in summarize([amended], 0),
          "an amended (COMPLETE) gate must not be counted as accepted")


def _run_tool(argv: list[str], stdin: str | None = None) -> subprocess.CompletedProcess:
    """Run THIS file as a subprocess (so a temp copy under mutation tests itself)."""
    return subprocess.run([sys.executable, os.path.abspath(__file__)] + argv, input=stdin,
                          capture_output=True, text=True)


def _ref_example_record() -> dict:
    """The `references/telemetry.md` §2 example record: the first fenced ```json block
    after the `## 2.` heading, parsed."""
    text = open(REF_DOC, encoding="utf-8").read()
    start = text.index("\n## 2.")
    fence = text.index("```json", start) + len("```json")
    return json.loads(text[fence:text.index("```", fence)])


def _line_count(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def test_append_cases(check, tmp: str) -> None:
    """The three `append` cases of telemetry.md §Writer (REQ-TELEM-PIPELINEOBSERVABILITY-001):
    a `v`-less object exits non-zero with the line count unchanged; `[]` exits
    non-zero writing nothing; the §2 example record exits 0, adds exactly one line
    and `summarize --file` counts 1 record. Only temp files are ever appended to.
    """
    path = os.path.join(tmp, ".sdd", "append.jsonl")
    # (1) the §2 example record → exit 0, one line, summarize counts 1
    ok = _run_tool(["append", "--file", path], json.dumps(_ref_example_record()))
    check(ok.returncode == 0 and ok.stdout == "", f"append example: rc {ok.returncode}, stdout {ok.stdout!r}, stderr {ok.stderr!r}")
    check(_line_count(path) == 1, f"append example: {_line_count(path)} line(s), expected 1")
    summ = _run_tool(["summarize", "--file", path])
    check(summ.returncode == 0 and "records: 1" in summ.stdout, f"summarize after append does not count 1: {summ.stdout[:200]!r}")
    # (2) a v-less object → non-zero, line count unchanged
    before = _line_count(path)
    vless = _run_tool(["append", "--file", path], '{"ts":"x","ws":"x"}')
    check(vless.returncode != 0, "append v-less object: exit 0 — the validation step is missing")
    check(_line_count(path) == before, f"append v-less object wrote a line ({before} → {_line_count(path)})")
    # (3) a non-object → non-zero, nothing written (a fresh path stays absent)
    fresh = os.path.join(tmp, "append-fresh.jsonl")
    arr = _run_tool(["append", "--file", fresh], "[]")
    check(arr.returncode != 0 and not os.path.exists(fresh), f"append []: rc {arr.returncode}, file exists {os.path.exists(fresh)}")
    # a record with an enum finding is refused; a cross-field-only finding is a warning and written
    bad = _record2(dispatch={"kind": "gate"})
    ref = _run_tool(["append", "--file", fresh], json.dumps(bad))
    check(ref.returncode != 0 and "[enum] dispatch.kind" in ref.stderr and not os.path.exists(fresh),
          f"append enum finding not refused: rc {ref.returncode}, {ref.stderr!r}")
    warn_only = _record2(dispatch={"kind": "review"}, commit={"token": "COMPLETE", "missing_n": 0, "extra_n": 0})
    wr = _run_tool(["append", "--file", fresh], json.dumps(warn_only))
    check(wr.returncode == 0 and "WARN [cross-field]" in wr.stderr and _line_count(fresh) == 1,
          f"append cross-field warning: rc {wr.returncode}, {wr.stderr!r}, lines {_line_count(fresh)}")
    # --help names append
    helptext = _run_tool(["--help"]).stdout
    check("append" in helptext, "--help does not name append")


def test_flat_cg_migration(check, tmp: str) -> None:
    """The `flat-cg` case over the frozen flat fixture (REQ-TELEM-PIPELINEOBSERVABILITY-002):
    every count is derived from the fixture at run time — migrated = records of the
    four mappable kinds; lost per workstream = its `gate` + `commit` + `pr` records
    (and every other unmapped kind under its own name, so migrated + lost = total);
    the fixture's sha256 equals the README value before and after.
    """
    check(os.path.exists(FLAT_FIXTURE_PATH), f"frozen flat fixture missing: {FLAT_FIXTURE_PATH}")
    if not os.path.exists(FLAT_FIXTURE_PATH):
        return
    readme = open(os.path.join(FIXTURES_DIR, "README.md"), encoding="utf-8").read()
    check(FLAT_FIXTURE_SHA256 in readme, "the flat fixture sha256 is not recorded in fixtures/README.md")
    check(_sha256(FLAT_FIXTURE_PATH) == FLAT_FIXTURE_SHA256, "flat fixture sha256 before")
    # derive the expected numbers from the fixture itself
    by_ws_kind: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    chunk_set: set[int] = set()
    total = 0
    for rec in load_raw(FLAT_FIXTURE_PATH):
        if not isinstance(rec, dict):
            continue
        total += 1
        k = str(flat_kind(rec))
        by_ws_kind[str(rec.get("ws"))][k] += 1
        if k in FLAT_MAPPABLE_KINDS and rec.get("ws") == "consumer-geometry" and _is_int(_flat_chunk(rec.get("chunk"))):
            chunk_set.add(_flat_chunk(rec.get("chunk")))   # the chunks consumer-geometry's mappable records name
    exp_migrated = sum(n for c in by_ws_kind.values() for k, n in c.items() if k in FLAT_MAPPABLE_KINDS)
    copy = os.path.join(tmp, "flat-copy.jsonl")
    shutil.copyfile(FLAT_FIXTURE_PATH, copy)
    out = os.path.join(tmp, "flat-migrated.jsonl")
    res = _run_tool(["migrate", "--file", copy, "--out", out])
    check(res.returncode == 0 and "flat-cg" in res.stdout, f"flat-cg migrate: rc {res.returncode}: {res.stdout!r} {res.stderr!r}")
    check(_sha256(copy) == FLAT_FIXTURE_SHA256, "migrate --out left the flat copy untouched")
    lint_res = _run_tool(["--lint", "--file", out])
    typed = [ln for ln in lint_res.stdout.splitlines() if re.search(r"\[(enum|type|key-undeclared|key-missing)\]", ln)]
    check(typed == [], f"flat-cg output has typed findings: {typed[:5]}")
    migrated, skipped = load(out)
    check(skipped == 0 and len(migrated) == exp_migrated,
          f"flat-cg migrated {len(migrated)} (skipped {skipped}), fixture has {exp_migrated} records of the mappable kinds")
    check(all(_get(r, "migration", "from") == MIGRATION_FROM_FLAT and r.get("v") == 2 for r in migrated),
          "every migrated record carries migration.from flat-cg at v: 2")
    lost_total = 0
    for ws, counts in by_ws_kind.items():
        exp_lost = {k: n for k, n in counts.items() if k not in FLAT_MAPPABLE_KINDS}
        carriers = [r for r in migrated if _get(r, "cycle", "workstream") == ws and "lost" in (r.get("migration") or {})]
        if not exp_lost:
            check(carriers == [], f"{ws}: lost stamped with nothing lost")
            continue
        check(len(carriers) == 1, f"{ws}: {len(carriers)} records carry migration.lost, expected exactly one")
        if carriers:
            check(carriers[0] is next(r for r in migrated if _get(r, "cycle", "workstream") == ws),
                  f"{ws}: migration.lost is not on the first migrated record")
            got = carriers[0]["migration"]["lost"]
            named = {k: got.get(k, 0) for k in FLAT_LOST_KINDS}
            check(named == {k: counts.get(k, 0) for k in FLAT_LOST_KINDS},
                  f"{ws}: lost gate/commit/pr {named} != fixture {dict((k, counts.get(k, 0)) for k in FLAT_LOST_KINDS)}")
            check(got == exp_lost, f"{ws}: lost {got} != every unmapped kind {exp_lost}")
            lost_total += sum(got.values())
    check(lost_total + len(migrated) == total, f"lost {lost_total} + migrated {len(migrated)} != fixture records {total}")
    # summarize --workstream consumer-geometry: the per-chunk block carries exactly the
    # chunks the mappable records name, each stamped partial (the chunks that live only
    # on lost gate records are missing, not lost — Q-IMPL-PIPELINEOBSERVABILITY-005).
    summ = _run_tool(["summarize", "--file", out, "--workstream", "consumer-geometry"])
    cg = [r for r in migrated if _get(r, "cycle", "workstream") == "consumer-geometry"]
    cg_chunks = {c for c in (_get(r, "dispatch", "chunk") for r in cg) if _is_int(c)}
    rows = chunk_rows(cg)
    check(summ.returncode == 0 and f"records: {len(cg)}" in summ.stdout, f"summarize --workstream consumer-geometry: {summ.stdout[:120]!r}")
    check({r["chunk"] for r in rows} == cg_chunks == chunk_set,
          f"per-chunk block chunks {[r['chunk'] for r in rows]} != migrated chunks {sorted(cg_chunks)} != fixture chunks {sorted(chunk_set)}")
    check(rows and all(r["note"] == partial_stamp(r["chunk"]) and partial_stamp(r["chunk"]) in summ.stdout for r in rows),
          "every migrated chunk is stamped partial in the per-chunk block")
    # idempotent: a second run over the output changes nothing and loses nothing
    out2 = os.path.join(tmp, "flat-migrated-2.jsonl")
    res2 = _run_tool(["migrate", "--file", out, "--out", out2])
    check(res2.returncode == 0 and _sha256(out2) == _sha256(out), "second flat-cg run is a no-op")
    # the fixture itself is refused as --file and as --out
    ref = _run_tool(["migrate", "--file", FLAT_FIXTURE_PATH])
    check(ref.returncode == 2, f"flat fixture as --file: rc {ref.returncode}")
    check(_sha256(FLAT_FIXTURE_PATH) == FLAT_FIXTURE_SHA256, "flat fixture sha256 after")


def test_migration_lost_shape(check) -> None:
    """`lost` is admitted only beside `from: flat-cg`: beside `chunk-string` it is
    `[type] migration`; a `flat-cg` marker with `lost` lints clean (REQ-TELEM-PIPELINEOBSERVABILITY-002)."""
    flat = {**_record2(), "migration": {"from": MIGRATION_FROM_FLAT, "at": "2026-09-22", "lost": {"gate": 14, "commit": 2, "pr": 1}}}
    check(_lint_classes([flat]) == {}, f"flat-cg marker with lost is not clean: {_lint_classes([flat])}")
    cs = {**_record(dispatch={"chunk": 3}), "migration": {"from": MIGRATION_FROM, "at": "2026-09-22", "lost": {"gate": 1}}}
    check(_lint_classes([cs]).get("type") == ["migration"], f"lost beside chunk-string is not [type] migration: {_lint_classes([cs])}")
    bad_lost = {**_record2(), "migration": {"from": MIGRATION_FROM_FLAT, "at": "2026-09-22", "lost": {"gate": "14"}}}
    check(_lint_classes([bad_lost]).get("type") == ["migration"], "a non-int lost count is [type] migration")


def test_post_manual_reason_review(check) -> None:
    """`[reason-review]` fires for a `REVIEW` record at `iteration: 1` with no
    loop-back and not for the `POST_MANUAL` record that follows it; the three
    domain-table members are present (REQ-TELEM-PIPELINEOBSERVABILITY-003)."""
    check("POST_MANUAL" in enum_members("dispatch", "reason") and "POST_MANUAL" not in FIX_ONLY_REASONS,
          "POST_MANUAL is not a dispatch.reason member outside the fix-only subset")
    check({"manual_intervention", "malformed"} <= enum_members("gate", "decision"),
          "gate.decision lacks manual_intervention / malformed")
    first = _record2(dispatch={"seq": 1, "kind": "pipeline", "stage": "specs", "iteration": 1, "reason": "REVIEW"},
                     ts_dispatch="2026-09-22T10:01:00Z")
    second = _record2(dispatch={"seq": 2, "kind": "review", "stage": "specs", "iteration": 1, "reason": "POST_MANUAL"},
                      verdict={"review_verdict": "APPROVE"}, ts_dispatch="2026-09-22T10:02:00Z")
    warns = [f for f in lint_records([first, second]) if f["class"] == "reason-review"]
    check([f["seq"] for f in warns] == [1], f"[reason-review] seqs {[f['seq'] for f in warns]}, expected [1] — never the POST_MANUAL record")
    check(_lint_classes([second]).get("enum") is None, f"a POST_MANUAL record raised an enum finding: {_lint_classes([second])}")


def test_cross_field_gate_rules(check) -> None:
    """The four cross-field assertions (a)–(d), each a finding pair and a control
    pair; (d) over all four non-`legal` cells (REQ-TELEM-PIPELINEOBSERVABILITY-003)."""
    def rec(seq, kind, stage, decision="proceed", scope="CLEAN", cv=None, rv=None, red=None, C=0, M=0, fi=0, reason=None, iteration=None):
        return _record2(dispatch={"seq": seq, "kind": kind, "stage": stage, "reason": reason, "iteration": iteration,
                                  "chunk": 1 if kind == "verifier" else None},
                        scope={"token": scope}, verdict={"chunk_verdict": cv, "review_verdict": rv, "red_verdict": red,
                                                         "findings": {"C": C, "M": M, "m": 0}},
                        gate={"decision": decision, "fix_iteration": fi},
                        ts_dispatch=f"2026-09-22T10:{seq:02d}:00Z", ts_gate=f"2026-09-22T10:{seq:02d}:30Z")

    def cf(recs, field):
        return [f["message"] for f in lint_records(recs) if f["class"] == "cross-field" and f["field"] == field and f["message"][:3] in ("(a)", "(b)", "(c)", "(d)")]

    # (a) voided verdict consumed: VIOLATION + positive token + proceed → finding; CLEAN, or `stop`, → none
    for kind, tokf, tok in (("verifier", "cv", "PASS"), ("review", "rv", "APPROVE_WITH_FIXES"), ("red", "red", "HELD")):
        pair = [rec(1, "pipeline", "implement" if kind == "verifier" else "verify"),
                rec(2, kind, "implement" if kind == "verifier" else "verify", scope="VIOLATION", **{tokf: tok})]
        check(len(cf(pair, "gate.decision")) == 1 and cf(pair, "gate.decision")[0].startswith("(a)"), f"(a) {kind} {tok} under VIOLATION + proceed not flagged: {cf(pair, 'gate.decision')}")
        ctrl = [pair[0], rec(2, kind, pair[1]["dispatch"]["stage"], scope="VIOLATION", decision="stop", **{tokf: tok})]
        ctrl2 = [pair[0], rec(2, kind, pair[1]["dispatch"]["stage"], scope="CLEAN", **{tokf: tok})]
        check(cf(ctrl, "gate.decision") == [] and cf(ctrl2, "gate.decision") == [], f"(a) control pair flagged for {kind}")
    # (b) fix_iteration incrementing across an APPROVE_WITH_FIXES at a document stage → finding;
    #     incrementing across a REJECT → none
    awf = [rec(1, "review", "requirements", rv="APPROVE_WITH_FIXES", M=2, decision="loop-back-to-fix"),
           rec(2, "review", "requirements", rv="APPROVE_WITH_FIXES", M=1, fi=1)]
    check(cf(awf, "gate.fix_iteration") and cf(awf, "gate.fix_iteration")[0].startswith("(b)"), f"(b) not flagged: {cf(awf, 'gate.fix_iteration')}")
    rej = [rec(1, "review", "requirements", rv="REJECT", C=1, decision="loop-back-to-fix"),
           rec(2, "review", "requirements", rv="REJECT", C=1, fi=1, decision="loop-back-to-fix"),
           rec(3, "review", "requirements", rv="APPROVE_WITH_FIXES", M=1, fi=2)]
    check(cf(rej, "gate.fix_iteration") == [], f"(b) control (consecutive REJECTs) flagged: {cf(rej, 'gate.fix_iteration')}")
    # (c) manual_intervention followed by a POST_MANUAL review with the SAME fix_iteration → none;
    #     followed by a non-review record, by nothing, or by a review with a different fix_iteration → finding
    mi = rec(1, "review", "specs", rv="REJECT", C=1, decision="manual_intervention", fi=3)
    good = [mi, rec(2, "review", "specs", rv="APPROVE_WITH_FIXES", M=1, reason="POST_MANUAL", iteration=3, fi=3)]
    check(cf(good, "gate.decision") == [], f"(c) control pair flagged: {cf(good, 'gate.decision')}")
    diff_fi = [mi, rec(2, "review", "specs", rv="APPROVE_WITH_FIXES", M=1, reason="POST_MANUAL", iteration=3, fi=4)]
    no_review = [mi, rec(2, "pipeline", "specs", fi=3)]
    check(cf(diff_fi, "gate.decision") and "fix_iteration" in cf(diff_fi, "gate.decision")[0], f"(c) differing fix_iteration not flagged: {cf(diff_fi, 'gate.decision')}")
    check(cf(no_review, "gate.decision") and cf([mi], "gate.decision"), "(c) missing POST_MANUAL review not flagged")
    # (d) the four non-legal cells at a non-pause decision → finding; the three legal cells → none;
    #     any cell at the `malformed` pause → none
    cells = [("C ≥ 1 under APPROVE", dict(rv="APPROVE", C=1)), ("C ≥ 1 under APPROVE_WITH_FIXES", dict(rv="APPROVE_WITH_FIXES", C=2, M=1)),
             ("C = 0 / M ≥ 1 / APPROVE", dict(rv="APPROVE", M=1)), ("C = 0 / M = 0 / APPROVE_WITH_FIXES", dict(rv="APPROVE_WITH_FIXES")),
             ("C = 0 / REJECT", dict(rv="REJECT", M=3))]
    for label, kw in cells:
        pair = [rec(1, "pipeline", "plan"), rec(2, "review", "plan", **kw)]
        check(len(cf(pair, "verdict.review_verdict")) == 1, f"(d) {label} not flagged: {cf(pair, 'verdict.review_verdict')}")
        paused = [rec(1, "pipeline", "plan"), rec(2, "review", "plan", decision="malformed", **kw)]
        check(cf(paused, "verdict.review_verdict") == [], f"(d) {label} flagged at the malformed pause")
    for label, kw in (("legal APPROVE", dict(rv="APPROVE")), ("legal AWF", dict(rv="APPROVE_WITH_FIXES", M=2)), ("legal REJECT", dict(rv="REJECT", C=1, M=1))):
        pair = [rec(1, "pipeline", "plan"), rec(2, "review", "plan", **kw)]
        check(cf(pair, "verdict.review_verdict") == [], f"(d) control {label} flagged: {cf(pair, 'verdict.review_verdict')}")


_GATE_RULE_TAG_RE = re.compile(r": \(([abcd])\) ")
# The (a)–(d) findings the two frozen fixtures raise, measured 2026-09-22
# (Q-IMPL-PIPELINEOBSERVABILITY-006): both cycles ran under the pre-Chunk-1
# grammar — `APPROVE_WITH_FIXES` carrying blocking items (d) and `fix_iteration`
# counting every loop-back (b) — so the shapes are historical facts on record,
# like the p3 `seq` 20 `kind: gate`; nothing here rewrites a fixture.
P3_FIXTURE_GATE_RULE_FINDINGS = [(14, "b"), (14, "d"), (17, "b"), (17, "d")]
P4_FIXTURE_GATE_RULE_FINDINGS = [(2, "d"), (4, "b"), (7, "d"), (10, "d"), (14, "b"), (14, "d"), (17, "b"), (17, "d"),
                                 (20, "d"), (23, "b"), (23, "d"), (26, "b"), (26, "d"), (34, "b"), (34, "d")]


def test_frozen_finding_sets_unchanged(check) -> None:
    """The p3 and p4 frozen fixtures' pre-delta `--lint` finding sets (sorted-lines
    sha256, the (a)–(d) lines excluded) are unchanged by the schema members and the
    four assertions, and the (a)–(d) lines each fixture raises are exactly the
    measured, pinned `(seq, rule)` list (REQ-TELEM-PIPELINEOBSERVABILITY-003;
    Q-IMPL-PIPELINEOBSERVABILITY-006)."""
    for path, sha, want, rules in ((FIXTURE_PATH, FIXTURE_SHA256, FIXTURE_LINT_SORTED_SHA256, P3_FIXTURE_GATE_RULE_FINDINGS),
                                   (P4_FIXTURE_PATH, P4_FIXTURE_SHA256, P4_FIXTURE_LINT_SORTED_SHA256, P4_FIXTURE_GATE_RULE_FINDINGS)):
        if not os.path.exists(path):
            continue
        check(_sha256(path) == sha, f"{os.path.basename(path)} sha256 before lint")
        _rc, lines = lint(path)
        gate_rule = [ln for ln in lines[:-1] if _GATE_RULE_TAG_RE.search(ln)]
        rest = [ln for ln in lines[:-1] if not _GATE_RULE_TAG_RE.search(ln)]
        got = finding_set_sha(rest)
        check(got == want, f"{os.path.basename(path)} pre-delta finding set changed: {got} != {want} ({lines[-1]})")
        seen = sorted((int(re.match(r"seq (\d+):", ln).group(1)), _GATE_RULE_TAG_RE.search(ln).group(1)) for ln in gate_rule)
        check(seen == sorted(rules), f"{os.path.basename(path)} (a)–(d) findings {seen} != pinned {sorted(rules)}")
        check(_sha256(path) == sha, f"{os.path.basename(path)} sha256 after lint")


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

        # Implication-derived expected (REQ-TELEM-HARNESSP4-002, -003; telemetry-reader.md
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

        # The frozen p3 fixture (telemetry-reader.md §Fixture-Based Test Contract): read-only,
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

        # --- harness-p5 reader/lint findings (REQ-TELEM-HARNESSP5-002..004, -006) ---

        # (1) Three stage-level fixes and NO chunk record: the `(implement, null)`
        #     group implies no pipeline dispatch (REQ-TELEM-HARNESSP5-002, finding 1).
        nullfix = [_record2(dispatch={"seq": i, "kind": "fix", "stage": "implement", "chunk": None,
                                      "iteration": i, "redo": None},
                            gate={"decision": "proceed", "fix_iteration": i})
                   for i in (1, 2, 3)]
        nrow = session_rows(nullfix)[0]
        check(nrow["kinds"]["pipeline"] == {"implied": 0, "recorded": 0, "missing": 0, "mistyped": 0},
              f"null-chunk group implied a pipeline dispatch: {nrow['kinds']['pipeline']}")
        check(nrow["implement_missing"]["pipeline"] == 0,
              f"null-chunk group reported a missing pipeline: {nrow['implement_missing']}")

        # (2) equal heads: a v: 1 record is exempt, the same shape at v: 2 with a null
        #     commit.token is a finding (REQ-TELEM-HARNESSP5-003, finding 3).
        eq_dispatch = {"seq": 1, "kind": "pipeline", "stage": "implement", "chunk": 1}
        eq_heads = {"head_before": "c38922d", "head_after": "c38922d"}
        eq_v1 = _record(dispatch=dict(eq_dispatch), git=dict(eq_heads),
                        **{"return": {"files_written_n": 3}})
        eq_v2 = _record2(dispatch=dict(eq_dispatch), git=dict(eq_heads),
                         commit={"token": None, "missing_n": 0, "extra_n": 0},
                         **{"return": {"files_written_n": 3}})
        def _equal_heads(recs):
            return [f for f in lint_records(recs)
                    if f["class"] == "cross-field" and f["field"] == "git.head_after"]
        check(_equal_heads([eq_v1]) == [], f"v: 1 record not exempt from equal-heads: {_equal_heads([eq_v1])}")
        check(len(_equal_heads([eq_v2])) == 1, f"v: 2 equal-heads finding lost: {_equal_heads([eq_v2])}")
        check(not any("migration" in r for r in (eq_v1, eq_v2)), "a migration marker was stamped by the lint")

        # (3) `v: 2.0` — an int-typed admission test, one helper, both load() paths
        #     (REQ-TELEM-HARNESSP5-004, finding 4).
        check(v_admitted(2) and not v_admitted(2.0) and not v_admitted(True) and not v_admitted("2"),
              "v_admitted() is not the int-typed membership test")
        float_v = _record2()
        float_v["v"] = 2.0
        fpath = os.path.join(tmp, "float-v.jsonl")
        with open(fpath, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(float_v, separators=(",", ":")) + "\n")
        frecs2, fskip2 = load(fpath)
        check(frecs2 == [] and fskip2 == 1, f"v: 2.0 not skipped-and-counted by summarize: {len(frecs2)}, {fskip2}")
        check("skipped: 1 unknown-schema record(s)" in summarize(frecs2, fskip2), "v: 2.0 missing from the skipped line")
        vfind = [f for f in lint_records([float_v]) if f["class"] == "type" and f["field"] == "v"]
        check(len(vfind) == 1, f"v: 2.0 raised no [type] v finding: {lint_records([float_v])}")

        # (4) finding order: a type finding on seq 5 and a cross-field on seq 2 render
        #     2, 5 although the passes emit 5 first (REQ-TELEM-HARNESSP5-006, finding 6).
        type5 = _record2(dispatch={"seq": 5, "kind": "pipeline", "stage": "research"},
                         scope={"widened": "two"})
        cross2 = _record2(dispatch={"seq": 2, "kind": "pipeline", "stage": "implement", "chunk": 1},
                          git=dict(eq_heads), commit={"token": None, "missing_n": 0, "extra_n": 0},
                          **{"return": {"files_written_n": 3}})
        ordered = lint_records([type5, cross2])
        check([f["seq"] for f in ordered] == [2, 5],
              f"findings not stable-sorted by seq: {[(f['seq'], f['class']) for f in ordered]}")
        check(ordered[0]["class"] == "cross-field" and ordered[1]["class"] == "type",
              f"sorted findings lost their classes: {[(f['seq'], f['class']) for f in ordered]}")

        # (5) The frozen p3 fixture's `--lint` finding SET is unchanged under the sort
        #     (order-insensitive: sha256 over the sorted lines) — REQ-TELEM-HARNESSP5-006.
        if os.path.exists(FIXTURE_PATH):
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 before sorted-lint")
            _rc3, _lines3 = lint(FIXTURE_PATH)
            # the (a)–(d) lines are pinned by test_frozen_finding_sets_unchanged; this
            # pin is the pre-delta set (Q-IMPL-PIPELINEOBSERVABILITY-006)
            sorted_sha = finding_set_sha([ln for ln in _lines3[:-1] if not _GATE_RULE_TAG_RE.search(ln)])
            check(sorted_sha == FIXTURE_LINT_SORTED_SHA256,
                  f"p3 fixture finding set changed: {sorted_sha} != {FIXTURE_LINT_SORTED_SHA256}")
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 after sorted-lint")

        # (6) The frozen p4 fixture (telemetry-reader.md §Fixture-Based Test Contract):
        #     no missing pipeline for the `(implement, chunk null)` group and no
        #     equal-heads finding on session 2 `seq` 2/4/6 (v: 1).
        check(os.path.exists(P4_FIXTURE_PATH), f"frozen p4 fixture missing: {P4_FIXTURE_PATH}")
        if os.path.exists(P4_FIXTURE_PATH):
            check(_sha256(P4_FIXTURE_PATH) == P4_FIXTURE_SHA256, "p4 fixture sha256 before")
            p4recs, p4skipped = load(P4_FIXTURE_PATH)
            check(len(p4recs) == 67 and p4skipped == 0, f"p4 fixture load: {len(p4recs)} records, {p4skipped} skipped")
            p4rows = [r for r in session_rows(p4recs) if r["workstream"] == "harness-p4"]
            check(p4rows and all(r["kinds"]["pipeline"]["missing"] == 0 for r in p4rows),
                  f"p4 fixture reports a missing pipeline: {[r['kinds']['pipeline'] for r in p4rows]}")
            check(all(r["gap"] == 0 for r in p4rows), f"p4 fixture session gap: {[r['gap'] for r in p4rows]}")
            check(_equal_heads(load_raw(P4_FIXTURE_PATH)) == [],
                  f"p4 fixture raised an equal-heads finding: {_equal_heads(load_raw(P4_FIXTURE_PATH))}")
            check(_sha256(P4_FIXTURE_PATH) == P4_FIXTURE_SHA256, "p4 fixture sha256 after")

        # (7) The spec-named cases: the frozen-fixture contract (REQ-TELEM-HARNESSP5-007),
        #     the three verifier-advisory lint cases (REQ-TELEM-HARNESSP5-008) and the two
        #     writer shapes the specs name (REQ-TELEM-HARNESSP5-001, -005).
        test_p4_fixture_frozen(check)
        test_advisory_cases(check)
        test_stage_level_fix_has_null_chunk_verdict(check)
        test_commit_group_records_closing_line(check)

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

    # ------------------------------------------------------------------
    # Chunk 3 (harness-p4): whole-schema --lint, v ∈ {1, 2}, scope.widened,
    # the commit group and the schema-agreement diff (telemetry-reader.md §Schema Lint,
    # §scope.widened, §commit Group, §Fixture-Based Test Contract).
    # ------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        def classes(recs) -> dict[str, list[str]]:
            """``{class: [<group.key> …]}`` of the lint findings on ``recs`` (in-memory)."""
            out: dict[str, list[str]] = defaultdict(list)
            for f in lint_records(recs):
                out[f["class"]].append(f["field"])
            return out

        def lint_file(recs) -> tuple[int, str]:
            p = os.path.join(tmp, f"lint-{len(os.listdir(tmp))}.jsonl")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("\n".join(json.dumps(r, separators=(",", ":")) for r in recs) + "\n")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(["--lint", "--file", p])
            return rc, buf.getvalue()

        # test_schema_table_agrees: both renderings parse to the code table [M3].
        code = parse_code_table()
        for doc_path, heading in ((SPEC_DOC, "### Record Schema"), (REF_DOC, "## 2. Record schema")):
            check(os.path.exists(doc_path), f"schema rendering missing: {doc_path}")
            if os.path.exists(doc_path):
                doc = parse_doc_table(open(doc_path, encoding="utf-8").read(), heading)
                diff = schema_diff(code, doc)
                check(not diff, f"test_schema_table_agrees {os.path.relpath(doc_path)}: {diff}")
                check(doc["constants"] == {"FIX_ONLY_REASONS": {"red_break"}}, f"const set parsed from {doc_path}: {doc['constants']}")
                check(("const", "FIX_ONLY_REASONS") not in doc["keys"], "const row leaked into group.key")
        check(FIX_ONLY_REASONS <= enum_members("dispatch", "reason"), "FIX_ONLY_REASONS ⊆ dispatch.reason")
        # a row added on one side only fails the diff (both directions)
        extra = dict(code)
        extra["keys"] = dict(code["keys"])
        extra["keys"][("git", "commit_n")] = ("scalar", "int", False)
        check(schema_diff(extra, code) and schema_diff(code, extra), "row added on one side only must fail")
        # a `v: 1` record admitted, a `v: 2` record admitted, `v: 3` skipped and counted [M1]
        mixed = [_record(dispatch={"seq": 1}), _record2(dispatch={"seq": 2}), {"v": 3, "dispatch": {"seq": 3}}]
        mpath = os.path.join(tmp, "mixed.jsonl")
        with open(mpath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(json.dumps(r) for r in mixed) + "\n")
        mrecs, mskipped = load(mpath)
        check(len(mrecs) == 2 and mskipped == 1, f"mixed v fixture: {len(mrecs)} records, {mskipped} skipped")
        check("skipped: 0 unknown-schema record(s)" in summarize(mixed[:2], 0), "mixed v1/v2 summarised with skipped: 0")
        check(v_key_set(1) < v_key_set(2) and ("commit", "token") in v_key_set(2) and ("commit", "token") not in v_key_set(1),
              "per-v key sets derive from the [p4] marks")
        # a v: 1 record lints clean against the v: 1 key set; a v: 2 one against the full set
        check(classes([_record(git={"head_before": "c38922d", "head_after": "d49a33e"})]) == {}, f"v1 record clean: {classes([_record()])}")
        check(classes([_record2()]) == {}, f"v2 record clean: {classes([_record2()])}")
        # one mutation per domain class
        check(classes([_record(dispatch={"kind": "gate"})]).get("enum") == ["dispatch.kind"], "enum: kind gate")
        check(classes([_record(dispatch={"chunk": "Chunk 0"})]).get("type") == ["dispatch.chunk"], "type: header string chunk")
        check("git.head_after" in classes([_record(git={"head_before": "c38922d", "head_after": "HEAD"})]).get("type", []), "type: HEAD literal")
        check("git.head_after" in classes([_record(git={"head_before": "c38922d", "head_after": "b0b69be0c5be814b9d138acdcabec45dbba6359a"})]).get("type", []), "type: 40-char sha")
        check(classes([_record(ts_gate="yesterday")]).get("type") == ["ts_gate"], "type: timestamp")
        check(classes([_record(git={"head_before": "c38922d", "head_after": "d49a33e", "commit_n": 0})]).get("key-undeclared") == ["git.commit_n"], "key-undeclared: git.commit_n")
        no_token = _record()
        del no_token["scope"]["token"]
        check(classes([no_token]).get("key-missing") == ["scope.token"], "key-missing: scope.token")
        check(classes([_record(FIX_ONLY_REASONS=["red_break"])]).get("key-undeclared") == ["FIX_ONLY_REASONS"], "const name as a key is key-undeclared [M3]")
        # scope.widened in-domain vs string
        check(classes([_record2(scope={"widened": 2})]) == {}, "scope.widened: 2 is in-domain")
        check(classes([_record2(scope={"widened": "2"})]).get("type") == ["scope.widened"], "scope.widened string is a type finding")
        check(classes([_record(scope={"widened": 0})]).get("key-undeclared") == ["scope.widened"], "a v1 record carrying a [p4] key is key-undeclared")
        # commit group in-domain vs DROPPED; non-null token on a non-committing kind
        check(classes([_record2(commit={"token": "INCOMPLETE", "missing_n": 1, "extra_n": 0})]) == {}, "commit INCOMPLETE,1,0 passes")
        check(classes([_record2(commit={"token": "DROPPED", "missing_n": 1, "extra_n": 0})]).get("enum") == ["commit.token"], "commit token DROPPED fails")
        check(classes([_record2(dispatch={"kind": "review"}, commit={"token": "COMPLETE"})]).get("cross-field") == ["commit.token"], "commit.token on a review record")
        # cross-field: chunk_verdict with no verifier record; proceed implement with equal heads
        cv_only = _record2(dispatch={"seq": 1, "stage": "implement", "chunk": 1}, verdict={"chunk_verdict": "PASS"},
                           git={"head_before": "c38922d", "head_after": "d49a33e"})
        check(classes([cv_only]).get("cross-field") == ["verdict.chunk_verdict"], f"chunk_verdict without verifier: {classes([cv_only])}")
        same_heads = _record2(dispatch={"seq": 1, "stage": "implement", "chunk": 1}, git={"head_before": "c38922d", "head_after": "c38922d"})
        check(classes([same_heads]).get("cross-field") == ["git.head_after"], f"proceed implement with equal heads: {classes([same_heads])}")
        # Q-IMPL-HARNESSP4-007: the heads are the snapshot pair (HEAD_after is taken before the
        # orchestrator commits), so equal heads alone mean nothing; the rule fires only when the
        # record shows nothing landed — a null `commit.token` (or a v1 record, which has no commit
        # group) with files_written_n > 0. A COMPLETE / INCOMPLETE commit group exempts the record.
        landed_same = _record2(dispatch={"seq": 1, "stage": "implement", "chunk": 1},
                               git={"head_before": "c38922d", "head_after": "c38922d"},
                               commit={"token": "COMPLETE", "missing_n": 0, "extra_n": 0})
        check(classes([landed_same]) == {}, f"equal heads with commit.token COMPLETE is exempt: {classes([landed_same])}")
        landed_partial = _record2(dispatch={"seq": 1, "stage": "implement", "chunk": 1},
                                  git={"head_before": "c38922d", "head_after": "c38922d"},
                                  commit={"token": "INCOMPLETE", "missing_n": 1, "extra_n": 0})
        check(classes([landed_partial]) == {}, f"equal heads with commit.token INCOMPLETE is exempt: {classes([landed_partial])}")
        # A v: 1 record is EXEMPT (REQ-TELEM-HARNESSP5-003): it carries no field that can
        # prove landing, so the rule is evaluated on v: 2 records only.
        v1_same = _record(dispatch={"seq": 1, "stage": "implement", "chunk": 1})
        check(classes([v1_same]) == {}, f"v1 proceed implement with equal heads is exempt: {classes([v1_same])}")
        v2_same = _record2(dispatch={"seq": 1, "stage": "implement", "chunk": 1},
                           git={"head_before": "c38922d", "head_after": "c38922d"})
        check(classes([v2_same]).get("cross-field") == ["git.head_after"],
              f"v2 proceed implement with equal heads and a null commit.token: {classes([v2_same])}")
        nothing_written = _record2(dispatch={"seq": 1, "stage": "implement", "chunk": 1},
                                   git={"head_before": "c38922d", "head_after": "c38922d"}, **{"return": {"files_written_n": 0}})
        check(classes([nothing_written]) == {}, f"equal heads, null token, files_written_n 0 is exempt: {classes([nothing_written])}")
        # gapless in-domain v2 fixture (the compliant redone chunk of C1 with real heads) exits 0
        def rec2(seq, kind, stage, chunk=None, redo=None, reason=None, cv=None, rv=None, red=None,
                 decision="proceed", gate_of=None, before="c38922d", after="c38922d", commit=None):
            return _record2(dispatch={"seq": seq, "kind": kind, "stage": stage, "chunk": chunk, "redo": redo, "reason": reason},
                            verdict={"chunk_verdict": cv, "review_verdict": rv, "red_verdict": red},
                            gate={"decision": decision, "redo_count": redo},
                            git={"head_before": before, "head_after": after},
                            commit=commit or {"token": None, "missing_n": 0, "extra_n": 0},
                            ts_dispatch=f"2026-09-19T10:{seq:02d}:00Z", ts_gate=f"2026-09-19T10:{(gate_of or seq):02d}:30Z")
        clean2 = [rec2(1, "pipeline", "research", rv="APPROVE", after="d49a33e", commit={"token": "COMPLETE", "missing_n": 0, "extra_n": 0}),
                  rec2(2, "review", "research", rv="APPROVE", gate_of=1),
                  rec2(3, "pipeline", "implement", chunk=1, redo=0, cv="FAIL", decision="redo"),
                  rec2(4, "verifier", "implement", chunk=1, cv="FAIL", decision="redo", gate_of=3),
                  rec2(5, "fix", "implement", chunk=1, redo=1, reason="VERIFIER_FAIL", cv="PASS", after="e4f5a6b",
                       commit={"token": "COMPLETE", "missing_n": 0, "extra_n": 0}),
                  rec2(6, "verifier", "implement", chunk=1, cv="PASS", gate_of=5),
                  rec2(7, "pipeline", "verify", red="HELD", after="f7a8b9c", commit={"token": "INCOMPLETE", "missing_n": 1, "extra_n": 0}),
                  rec2(8, "red", "verify", red="HELD", gate_of=7)]
        clean2[4]["scope"]["widened"] = 1
        crc, cout = lint_file(clean2)
        check(crc == 0 and "0 finding(s)" in cout, f"gapless in-domain fixture lints clean, got rc {crc}:\n{cout}")
        creport = summarize(clean2, 0)
        check("widened dispatches: 1" in creport and "COMMIT: INCOMPLETE (accepted): 1" in creport, f"summarize widened / COMMIT lines:\n{creport}")
        check("records-vs-expected: 8 recorded, expected 8 (0 missing)" in creport, "v2 fixture gapless")
        # the frozen fixture: exit 1 with at minimum the findings of §Fixture-Based Test Contract
        if os.path.exists(FIXTURE_PATH):
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 before lint")
            lbuf = io.StringIO()
            with contextlib.redirect_stdout(lbuf):
                lrc = main(["--lint", "--file", FIXTURE_PATH])
            lout = lbuf.getvalue()
            check(lrc == 1, f"fixture --lint exit {lrc}")
            check("seq 20: [enum] dispatch.kind:" in lout, "fixture: kind gate on seq 20")
            for s in range(6, 14):
                check(f"seq {s}: [type] dispatch.chunk:" in lout, f"fixture: header string chunk on seq {s}")
            check("seq 5: [type] git.head_after:" in lout and '"HEAD"' in lout, "fixture: head_after HEAD on seq 5")
            for s in range(6, 15):
                check(f"seq {s}: [type] git.head_before:" in lout and f"seq {s}: [type] git.head_after:" in lout, f"fixture: null git heads on seq {s}")
            for s in range(15, 21):
                check(f"seq {s}: [type] git.head_after:" in lout, f"fixture: 40-char sha on seq {s}")
                check(f"seq {s}: [key-undeclared] git.commit_n:" in lout, f"fixture: undeclared git.commit_n on seq {s}")
            for s in (2, 18):
                check(f"seq {s}: [mistyped-fix] dispatch.kind:" in lout, f"fixture: [mistyped-fix] on seq {s}")
            for s in (3, 4, 5):
                check(f"WARN seq {s}: [reason-review] dispatch.reason" in lout, f"fixture: [reason-review] on seq {s}")
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 after lint")
        # migrate (REQ-TELEM-HARNESSP4-005 — telemetry-reader.md §In-Place Migration, §Fixture-Based
        # Test Contract): the frozen fixture is copied to the temp dir first; the fixture
        # itself is only ever the *refused* input of the guard test.
        if os.path.exists(FIXTURE_PATH):
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 before migrate")
            copy = os.path.join(tmp, "p3-copy.jsonl")
            shutil.copyfile(FIXTURE_PATH, copy)
            mig = os.path.join(tmp, "p3-migrated.jsonl")
            obuf = io.StringIO()
            with contextlib.redirect_stdout(obuf), contextlib.redirect_stderr(obuf):
                mrc = main(["migrate", "--file", copy, "--out", mig])
            check(mrc == 0 and "migrated 8 record(s)" in obuf.getvalue(), f"migrate --out: rc {mrc}: {obuf.getvalue()!r}")
            check(_sha256(copy) == FIXTURE_SHA256, "migrate --out leaves the input untouched")
            g_recs, g_skipped = load(mig)
            check(len(g_recs) == 20 and g_skipped == 0, f"migrated file: {len(g_recs)} records, {g_skipped} skipped")
            check(out_of_domain_chunks(g_recs) == 0, "migrated file has no out-of-domain chunk")
            marked = [r for r in g_recs if "migration" in r]
            check(len(marked) == 8 and all(r["migration"]["from"] == MIGRATION_FROM
                                           and re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["migration"]["at"]) for r in marked),
                  f"migration marker on exactly the 8 rewritten records, got {len(marked)}")
            check(sorted(_get(r, "dispatch", "chunk") for r in marked) == list(range(8)), "chunks 0-7 are ints after migrate")
            check(all("migration" not in r for r in g_recs if _get(r, "dispatch", "chunk") is None), "unrewritten records carry no marker")
            greport = summarize(g_recs, g_skipped)
            for c in range(8):
                check(partial_stamp(c) in greport, f"migrated per-chunk block lacks the partial stamp for chunk {c}")
            check(partial_stamp(0) == 'partial — migrated from "Chunk 0"; verifier, fix and redo records were never written and cannot be reconstructed',
                  "stamp text as §In-Place Migration renders it")
            check("out-of-domain dispatch.chunk: 0 record(s)" in greport, "migrated report counts 0 out-of-domain chunks")
            lrc2, llines = lint(mig)
            lout2 = "\n".join(llines)
            check("[type] dispatch.chunk:" not in lout2, "migrated records: no type finding for dispatch.chunk")
            check("migration" not in lout2, f"the optional migration marker is admitted on the migrated v: 1 records:\n{lout2}")
            check(lrc2 == 1 and "seq 20: [enum] dispatch.kind:" in lout2, "the fixture's other findings survive migration")
            # idempotent: a second run over the migrated output changes nothing
            mig2 = os.path.join(tmp, "p3-migrated-2.jsonl")
            with contextlib.redirect_stdout(io.StringIO()):
                mrc2 = main(["migrate", "--file", mig, "--out", mig2])
            check(mrc2 == 0 and _sha256(mig2) == _sha256(mig), "second migrate run is a no-op")
            # in place: sibling temp file → line-count check → rename; bytes equal the --out output
            with contextlib.redirect_stdout(io.StringIO()):
                mrc3 = main(["migrate", "--file", copy])
            check(mrc3 == 0 and _sha256(copy) == _sha256(mig), "in-place migrate yields the --out bytes")
            check(not [f for f in os.listdir(tmp) if f.endswith(".migrate")], "no sibling temp file left behind")
            with contextlib.redirect_stdout(io.StringIO()):
                mrc4 = main(["migrate", "--file", copy])
            check(mrc4 == 0 and _sha256(copy) == _sha256(mig), "in-place second run changes nothing")
            # fixture guard: --file or --out under tools/fixtures/ → exit 2, no write
            gbuf = io.StringIO()
            with contextlib.redirect_stdout(gbuf), contextlib.redirect_stderr(gbuf):
                grc = main(["migrate", "--file", FIXTURE_PATH])
            check(grc == 2 and "tools/fixtures/" in gbuf.getvalue(), f"fixture guard on --file: rc {grc}")
            never = os.path.join(FIXTURES_DIR, "never-written.jsonl")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                grc2 = main(["migrate", "--file", copy, "--out", never])
            check(grc2 == 2 and not os.path.exists(never), "fixture guard on --out: exit 2, no write")
            check(under_fixtures(os.path.join(_REPO, "tools", "fixtures", "..", "fixtures", "x.jsonl"))
                  and not under_fixtures(os.path.join(_REPO, "tools", "fixtures-not", "x.jsonl")), "under_fixtures normalises the path")
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 after migrate")
        # lint: the optional marker is admitted on every v in its declared shape only (Q-IMPL-HARNESSP4-006)
        check(not classes([{**_record(dispatch={"chunk": 3}), "migration": {"from": MIGRATION_FROM, "at": "2026-09-19"}}]),
              "migration marker on a v: 1 record lints clean")
        check(classes([{**_record(dispatch={"chunk": 3}), "migration": {"from": MIGRATION_FROM}}]).get("type") == ["migration"],
              "migration marker missing `at` is a type finding")
        # --plan floor (REQ-TELEM-HARNESSP4-008): a plan with a chunk that has no record.
        plan_path = os.path.join(tmp, "plan.md")
        with open(plan_path, "w", encoding="utf-8") as fh:
            fh.write("# Plan\n\n### Chunk 0: a\n\n### Chunk 1: b\n\n### Chunk 2: c\n")
        floor = plan_floor(clean2, plan_path)
        check(floor == {"chunks": 3, "verifier_on": True, "recorded": 1, "shortfall": 2}, f"plan floor: {floor}")
        check("implement floor: 3 pipeline (6 with verifier); recorded implement records: 1; shortfall: 2" in plan_floor_line(floor),
              f"plan floor line: {plan_floor_line(floor)}")
        pbuf = io.StringIO()
        with contextlib.redirect_stdout(pbuf):
            prc = main(["summarize", "--plan", plan_path, "--file", mpath])
        check(prc == 0 and "implement floor: 3 pipeline" in pbuf.getvalue(), f"summarize --plan → exit {prc}")
        if os.path.exists(FIXTURE_PATH) and os.path.exists(P3_PLAN):
            pf = plan_floor(load(FIXTURE_PATH)[0], P3_PLAN)
            check(pf == {"chunks": 8, "verifier_on": True, "recorded": 8, "shortfall": 0}, f"p3 plan floor on the fixture: {pf}")
            check(_sha256(FIXTURE_PATH) == FIXTURE_SHA256, "fixture sha256 after --plan")

        # ------------------------------------------------------------------
        # pipeline-observability (2026-09-22): the validated `append`, the `flat-cg`
        # migration over the frozen flat fixture, the `lost` marker shape, the
        # POST_MANUAL / manual_intervention / malformed members and the four
        # cross-field assertions (a)–(d) — telemetry.md §Writer,
        # telemetry-reader.md §Schema Lint, §In-Place Migration.
        # ------------------------------------------------------------------
        test_append_cases(check, tmp)
        test_flat_cg_migration(check, tmp)
        test_migration_lost_shape(check)
        test_post_manual_reason_review(check)
        test_cross_field_gate_rules(check)
        test_frozen_finding_sets_unchanged(check)

    if failures:
        print("SELF-TEST FAIL:\n- " + "\n- ".join(failures))
        return 1
    print("SELF-TEST OK: budget grammar, six-record fixture (one row per stage, per-chunk block, skipped: 2), "
          "records-vs-expected (gapless + a seq gap), implication-derived expected (verifier, redo first attempt, "
          "review, red, clause (b), loop-back with no record, [reason-review] not counted, gapless compliant-redo "
          "fixture 2/1/0, frozen p3 fixture expected 39 with sha256 unchanged), out-of-domain dispatch.chunk "
          "counted and folded to c?, missing file → records: 0, schema table agrees with both renderings, "
          "v ∈ {1, 2} admitted (v: 3 skipped), --lint one mutation per class + frozen fixture findings + gapless "
          "v2 fixture clean, scope.widened / commit group, --plan floor, migrate (--out, in place, idempotent, "
          "partial stamp, fixture guard, fixture sha256 unchanged); harness-p5: null-chunk group "
          "implies no pipeline, v: 1 exempt from equal-heads, v: 2.0 skipped and [type] v from one "
          "admission helper, findings sorted 2 before 5, frozen p3 finding set unchanged (sorted sha256) "
          "and frozen p4 fixture clean (67 records, 0 missing pipeline, no equal-heads), "
          "test_p4_fixture_frozen (67 lines, README sha256, p3 unchanged against main), "
          "test_advisory_cases ((a) commit.token on verifier/red, (b) reason RED_BREAK, "
          "(c) migration.from flat-xx outside {chunk-string, flat-cg}), test_stage_level_fix_has_null_chunk_verdict, "
          "test_commit_group_records_closing_line; pipeline-observability: test_append_cases (v-less object "
          "refused with the line count unchanged, [] refused writing nothing, the §2 example record appended "
          "and counted 1 by summarize, --help names append), test_flat_cg_migration (frozen flat fixture: "
          "migrated = mappable kinds, lost = gate + commit + pr per workstream on the first migrated record, "
          "zero typed findings, per-chunk block stamped partial, fixture refused and sha256 unchanged), "
          "test_migration_lost_shape (lost beside chunk-string is [type] migration), "
          "test_post_manual_reason_review ([reason-review] on the REVIEW record only, never POST_MANUAL), "
          "test_cross_field_gate_rules ((a) voided verdict consumed, (b) fix_iteration across a non-REJECT, "
          "(c) un-reviewed manual_intervention, (d) the four non-legal cells — each a finding pair and a control pair), "
          "test_frozen_finding_sets_unchanged (p3 and p4 sorted-lines sha256)")
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="telemetry",
        description="Out-of-loop reader for .sdd/telemetry.jsonl (orchestrator-written, gitignored, "
                    "never read by phase detection). One table per workstream, one row per stage.",
    )
    ap.add_argument("--self-test", action="store_true", help="run the built-in fixture tests")
    ap.add_argument("--lint", action="store_true",
                    help="validate every field of every record against the domain table; exit 1 on any finding")
    ap.add_argument("--file", default=DEFAULT_FILE, help=f"telemetry file for --lint (default: {DEFAULT_FILE})")
    sub = ap.add_subparsers(dest="command")
    sp = sub.add_parser("summarize", help="print per-workstream stage tables and the per-chunk block")
    sp.add_argument("--file", default=DEFAULT_FILE, help=f"telemetry file (default: {DEFAULT_FILE})")
    sp.add_argument("--workstream", default=None, help="only records of this cycle.workstream")
    sp.add_argument("--since", default=None, help="only records with ts_dispatch >= this ISO-8601 timestamp")
    sp.add_argument("--plan", default=None, metavar="PATH",
                    help="also print the implement-stage floor derived from this plan's `### Chunk N:` headers")
    mp = sub.add_parser(
        "migrate",
        help='OPERATOR-RUN, between sessions: rewrite "Chunk N" dispatch.chunk strings to int N and stamp a migration marker',
        description=(
            'Rewrite every dispatch.chunk header string "Chunk N" to the int N and add '
            '"migration": {"from": "chunk-string", "at": <today>} to each rewritten record '
            "(REQ-TELEM-HARNESSP4-005). This is the SECOND exception to the writer's append-only rule "
            "(the first is the leaf-write revert): run it as the OPERATOR with NO orchestrator session open — "
            "never from a leaf, never while a session is appending, never from a dispatch template — and only "
            "after --lint reports the records clean on their typed fields. Without --out it rewrites in place "
            "(sibling temp file → line-count check → rename); it is idempotent. FIXTURE GUARD: a --file or --out "
            "under tools/fixtures/ exits 2 with no write — the frozen fixture is read-only evidence."),
    )
    mp.add_argument("--file", required=True, help="telemetry file to migrate (never the frozen fixture)")
    mp.add_argument("--out", default=None, help="write the migrated file here and leave --file untouched")
    apnd = sub.add_parser(
        "append",
        help="ORCHESTRATOR-ONLY: read one JSON record from stdin, validate it against the domain table, "
             "append it as one line; exit non-zero with nothing written on any finding",
        description=(
            "Read exactly one JSON value from stdin and, BEFORE writing, check in order: it is a JSON object; "
            "`v` is in the admitted set; `--lint`'s enum / type / key-undeclared / key-missing checks pass "
            "(cross-field and mistyped-fix are stderr warnings only). Exit 0 follows one append-only write of "
            "exactly one line; nothing is printed that reads the file (the gate's `TELEMETRY: rec <n>` is the "
            "orchestrator's session counter, advanced only on exit 0 — telemetry.md §Writer). No leaf and no "
            "dispatch template calls this."),
    )
    apnd.add_argument("--file", default=DEFAULT_FILE, help=f"telemetry file to append to (default: {DEFAULT_FILE})")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.lint:
        rc, lines = lint(args.file)
        print("\n".join(lines))
        return rc
    if args.command == "migrate":
        rc, msg = migrate(args.file, args.out)
        print(msg, file=sys.stderr if rc else sys.stdout)
        return rc
    if args.command == "append":
        rc, lines = append(args.file, sys.stdin.read())
        for line in lines:
            print(line, file=sys.stderr)
        return rc
    if args.command != "summarize":
        ap.print_help()
        return 2
    if args.plan and not os.path.isfile(args.plan):
        print(f"error: --plan not found: {args.plan}", file=sys.stderr)
        return 2
    # A missing file is an empty run set: load() returns ([], 0) and summarize()
    # prints an empty table with ``records: 0`` (exit 0), matching eval.py.
    records, skipped = load(args.file)
    try:
        records = filter_records(records, args.workstream, args.since)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(summarize(records, skipped, args.plan))
    return 0


if __name__ == "__main__":
    sys.exit(main())
