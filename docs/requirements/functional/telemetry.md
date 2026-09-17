---
domain: TELEM
last_updated: 2026-09-17
status: Approved
research_refs: [RS-HARNESSP2-001, RS-008]
workstream: harness-p2
---

# Requirements: Per-Dispatch Telemetry

## Overview

Per-dispatch telemetry for the orchestrated loop (idea catalogue
`docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md` item D11,
de-risked by RS-HARNESSP2-001 Q1). One append-only JSON-Lines file at the
repository root, `.sdd/telemetry.jsonl`, written **only by the orchestrator**,
once per dispatch, after that dispatch's gate decision, holding a transcript of
the gate signals the v5 harness already renders (RS-008: `RETURN:`, `SCOPE:`,
`CHUNK_VERDICT:`, `VERDICT:`, caps) plus wall-clock timestamps. It is read by
**nothing inside the SDD loop** — its only reader is an out-of-loop tool — so it
can never act as a loop-position marker (REQ-ORCH-014) and never becomes a
project artifact under `docs/` (REQ-HARN-027 as amended on 2026-09-17).

Standing constraints: REQ-ORCH-004 (kickoff is the only new git-tracked artifact
type — telemetry is gitignored, not tracked), REQ-ORCH-012/013 (records carry
counts of findings, never finding text or reviewer reasoning), REQ-ORCH-014 (no
dedicated marker; no resume field), REQ-HARN-027 (`docs/` invariant unchanged).
Telemetry is the measurement instrument for the two RS-008 dogfooding probes and
the prerequisite for any multi-run evaluation (EVAL domain); the plan must land
it first (RS-HARNESSP2-001 Implications for Design).

Terminology follows `harness-loop-control.md`: a **dispatch** is one subagent
invocation; dispatch kinds are `pipeline`, `fix`, `fanout_leaf`, `verifier`,
`review`, and — new in this cycle — `red` (REDB domain).

## Requirements

### Record

### REQ-TELEM-HARNESSP2-001: One record per dispatch, gate-signal transcript only
Each telemetry record must be one JSON object on one line containing exactly
these top-level keys: `v` (schema version, integer, `1`), `ts_dispatch`,
`ts_return`, `ts_gate` (ISO-8601 UTC timestamps stamped by the orchestrator's
own clock), `cycle` (`workstream`, `research_id`, `kickoff_date`, `marker`),
`dispatch` (`seq`, `kind` ∈ {pipeline, fix, fanout_leaf, verifier, review, red},
`stage`, `chunk`, `iteration`, `redo`, `reason` — mirroring the repair packet's
`reason` — `budget` per REQ-TELEM-HARNESSP2-002, `write_scope_n`), `return`
(`status`, `budget_consumed`, `files_written_n`, `commits_n`, `tasks_completed_n`,
`failures_n`, `ledger_n`, `open_questions_n`, `blocked_writes_n`, `warnings`),
`scope` (`token` ∈ {CLEAN, VIOLATION}, `in`, `advisory`, `out`,
`history_rewrite`), `verdict` (`chunk_verdict`, `review_verdict`, `red_verdict`,
`findings` as `{C, M, m}` counts, `malformed`, `contradiction_class` ∈ {null, b,
c}), `gate` (`decision`, `decision_by` ∈ {operator, policy}, `fix_iteration`,
`fix_cap`, `cap_raised`, `redo_count`, `replan_count`, `replan_cap`),
`replan_trigger`, and `git` (`head_before`, `head_after`). Every value must be a
count, enum, sha, boolean, null or timestamp — a record must never contain a
finding line, a file's content, a path list, reviewer reasoning or any other
prose (REQ-ORCH-012/013 hold: counts of findings, never the lines). Field naming
may be refined by `sdd-specs`; the key set and the counts-not-text rule are
fixed. (see RS-HARNESSP2-001 Q1 record shape)
**Acceptance**: a record produced for a review dispatch with two Material
findings has `verdict.findings.M == 2` and no string value longer than a sha or
an enum; `grep -c '"C1' .sdd/telemetry.jsonl` is 0 after a full cycle; the
schema in `skills/sdd-orchestrate/references/telemetry.md` lists the key set
above.
[Priority: must]

### REQ-TELEM-HARNESSP2-002: Budget is recorded as enumerated units, never free text
The `dispatch.budget` field must be an object of enumerated units with numeric
or boolean values — `{"tool_calls": <int|null>, "test_runs": <int|null>,
"prototypes": <bool>, "read_only": <bool>}` — parsed by the orchestrator from
the dispatched `Budget:` line, never the line's text. `return.budget_consumed`
must use the same unit keys, so consumed-versus-budget is computable per record,
and must carry `"self_reported": true` because the harness exposes no tool-call
counter (REQ-HARN-005's recorded v1 limitation — telemetry labels the
self-report rather than pretending precision). A `Budget:` line that cannot be
parsed into units must be recorded as `{"unparsed": true}` with no text copied.
(see RS-HARNESSP2-001 Q1)
**Acceptance**: the dispatch line `Budget: ~70 tool calls, no prototypes`
yields `{"tool_calls": 70, "test_runs": null, "prototypes": false, "read_only":
false}`; no record contains the substring `tool calls`.
[Priority: must]

### REQ-TELEM-HARNESSP2-003: No resume or next-stage field
A telemetry record must not carry any field that answers "where does the loop
resume" — no `next_stage`, `resume`, `current_phase`, `pending` or equivalent —
and the orchestrator must not consult the file to derive position on re-entry
(REQ-ORCH-014). Position is derived solely from the SDD artifacts via the stage
skills' phase detection; the record's `dispatch.stage` is the stage that **was**
dispatched, a historical fact, and the file may be deleted at any time without
changing loop behavior. (see RS-HARNESSP2-001 Q1 "provably not a marker")
**Acceptance**: the key set of REQ-TELEM-HARNESSP2-001 contains no resume-class
key; `sdd-orchestrate/SKILL.md` §Phase Detection and its position table cite
`.sdd/` nowhere (REQ-TELEM-HARNESSP2-006 enforces this mechanically).
[Priority: must]

### Writer

### REQ-TELEM-HARNESSP2-004: Orchestrator-only writer, one append after each gate
Only the orchestrator (`sdd-orchestrate`) may write `.sdd/telemetry.jsonl`. It
must append exactly one record per dispatch, **after** the operator's gate
decision for that dispatch (so `gate.decision` is filled), using an append-only
write; it must never rewrite or truncate the file — with a **single
exception**: the leaf-write revert of REQ-TELEM-HARNESSP2-005, which truncates
the file back to the pre-dispatch record count. A write failure must not
stop the loop: the orchestrator notes `TELEMETRY: WRITE FAILED` as one line of
the next gate's text and continues — telemetry is never load-bearing. No stage
skill, review, verifier, fan-out leaf or red dispatch is instructed to write it,
and no dispatch template mentions the path. Under `docs/.sdd-version` == `4`
there is one file per repository; records are attributed by `cycle.workstream`
and no per-workstream file or `docs/ws/<id>/` entry is created (the directory
would otherwise become an owned execution artifact). Telemetry is **default on**
under orchestrate; the operator may disable it for a cycle at KICKOFF, in which
case no record is written and the gate shows `TELEMETRY: OFF` once. (see
RS-HARNESSP2-001 Q1 writer rule; decisions deferred to requirements)
**Acceptance**: after a cycle of N gated dispatches the file has exactly N lines
(or N + records of prior cycles), each with a non-null `gate.decision`; a
simulated unwritable `.sdd/` produces `TELEMETRY: WRITE FAILED` at the next gate
and the same `proceed | loop-back-to-fix | stop` options as before; no
`docs/ws/*/telemetry*` path exists.
[Priority: must]

### REQ-TELEM-HARNESSP2-005: Leaf writes to `.sdd/` surface as `OUT`
Any write to `.sdd/**` by a dispatched subagent must be a boundary finding
tagged `OUT` in the write-scope block (REQ-HARN-022), even though `.sdd/` is
gitignored and therefore invisible to the porcelain snapshot (REQ-HARN-026
limitation (b)). The orchestrator must therefore take a third, telemetry-specific
observation alongside the snapshot pair of REQ-HARN-021: the record count
(line count) of `.sdd/telemetry.jsonl` and the entry list of `.sdd/` before the
dispatch and on return, **before** its own append (REQ-HARN-025 ordering). Any
delta inside the window is a leaf write and is rendered as
`OUT .sdd/telemetry.jsonl (+k records, leaf write — reverted)`; the orchestrator
must truncate the file back to the before-count (the single exception to
REQ-TELEM-HARNESSP2-004's never-truncate rule) and never treat leaf-written
records as telemetry. The finding string above is defined **once**, in
`skills/sdd-orchestrate/references/telemetry.md`; `references/write-scope.md`
§3 specifies the third observation and §5 limitation (b)'s `.sdd/` exception
by **referencing** that definition — those two sections are the third
allowlisted `\.sdd/` location of REQ-LINT-HARNESSP2-002. `.sdd/**` may never
appear in any default or operator-widened write scope (REQ-HARN-020). (see
RS-HARNESSP2-001 Q1 writer rule)
**Acceptance**: a scope-check fixture in which the leaf appends one line to
`.sdd/telemetry.jsonl` yields `SCOPE: VIOLATION (1 paths)` with the `OUT` line
above and a file whose line count equals the before-count; `tools/sdd-scope-
check-selftest.py` gains this scenario.
[Priority: must]

### Non-interference

### REQ-TELEM-HARNESSP2-006: Never a phase-detection or staleness input
No skill's phase detection or staleness computation may read `.sdd/` or any
telemetry record. The complete set of phase-detection and staleness inputs is,
and must remain: `docs/.sdd-version` (all skills); `docs/research/RS-*/findings.md`
`status` and `docs/research/index.md` (research, requirements);
`docs/requirements/index.md` and category files (`status`, `last_updated`) and
`docs/spec/*.md` (`status`, `last_updated`, `requires:`) (requirements, specs,
plan, implement, verify, replan); `docs/ws/<id>/plan.md` (task marks,
`last_updated`, `traces to`) and `docs/ws/<id>/plan-history/` (`-replan-`
archives) (plan, implement, verify, replan, orchestrate); `docs/ws/<id>/
verification.md` `status` (verify, replan, orchestrate); `docs/ws/<id>/kickoff.md`
`research_id` / `date` (orchestrate); and `docs/requirements/traceability.md` /
`docs/ws/<id>/traceability.md` for coverage only, never position (sdd-verify
Step 3b, sdd-review Step 2) — flat `docs/` equivalents under marker `3`. Every
input is under `docs/`; `.sdd/` is not. Deleting `.sdd/` must leave every
skill's detected phase, every staleness verdict and the orchestrator's position
table byte-identical. (see RS-HARNESSP2-001 Q1 detection-input table;
REQ-ORCH-014)
**Acceptance**: with a populated `.sdd/telemetry.jsonl`, `rm -rf .sdd/` followed
by re-running the orchestrator's position table and each stage skill's phase
detection on the same repo yields identical output; `grep -rn '\.sdd/'
skills/*/SKILL.md` hits only the `sdd-orchestrate` telemetry stub
(REQ-TELEM-HARNESSP2-007).
[Priority: must]

### REQ-TELEM-HARNESSP2-007: Lint guard on the telemetry path
`tools/sdd-skill-lint.py` must carry a `FORBIDDEN` row (fail severity) for the
pattern `\.sdd/` across every `skills/*/SKILL.md` and `skills/*/references/*.md`,
with an allowlist of exactly three locations: the telemetry stub in
`skills/sdd-orchestrate/SKILL.md`, `skills/sdd-orchestrate/references/
telemetry.md`, and `skills/sdd-orchestrate/references/write-scope.md` (§3 and
§5 only, REQ-TELEM-HARNESSP2-005). Operator docs (`USAGE.md`, `CLAUDE.md`) are
outside the row's scan. The row's `fix:` text must say that telemetry is orchestrator-
written and never a detection input. This guard, together with the absence of a
resume field (REQ-TELEM-HARNESSP2-003), is what satisfies REQ-ORCH-014 — by
mechanism, not by promise. (see RS-HARNESSP2-001 Q1 guards (i)+(iii);
REQ-LINT-HARNESSP2-002)
**Acceptance**: adding the text `.sdd/telemetry.jsonl` to
`skills/sdd-verify/SKILL.md` makes the lint exit 1 with the row's fix string;
the shipped skill set exits 0.
[Priority: must]

### Consumer

### REQ-TELEM-HARNESSP2-008: Placement — gitignored, root-level, outside `docs/`
The telemetry file must live at `<repo root>/.sdd/telemetry.jsonl`; `.sdd/` must
be added to the repository's `.gitignore` (precedent: `.superpowers/`) so
`git check-ignore .sdd/telemetry.jsonl` exits 0 and `git ls-files docs/` is
unchanged after a full orchestrated cycle (REQ-HARN-027's acceptance, verbatim).
The orchestrator must create `.sdd/` on first append and must add the ignore
line itself if missing, reporting `TELEMETRY: .gitignore updated` once at the
next gate (that edit is the orchestrator's own bookkeeping commit, outside any
observed window per REQ-HARN-025). (see RS-HARNESSP2-001 Q1 "Where `.sdd/`
sits")
**Acceptance**: `git check-ignore .sdd/telemetry.jsonl` exits 0; `git status
--porcelain` shows no `.sdd/` entry after a cycle; `git ls-files docs/` before
and after the cycle differ only by the artifacts the stage skills already
produce.
[Priority: must]

### REQ-TELEM-HARNESSP2-009: Out-of-loop reader
A stdlib-only tool `tools/sdd-telemetry.py` should provide `summarize`, reading
`.sdd/telemetry.jsonl` and printing, per workstream and per stage: dispatch
count, mean and max `budget_consumed.tool_calls` versus budget, `SCOPE:
VIOLATION` count, `MALFORMED` count, fix iterations per stage, redo count per
chunk, contradiction pauses, red verdicts, and wall time per dispatch
(`ts_return − ts_dispatch`) and per gate (`ts_gate − ts_return`) — the per-chunk
dispatch-cost table RS-008 probe 1 asks for, as a query instead of a hand count.
It must tolerate records of unknown `v` (skip with a count) and must have
`--help` and `--self-test`. No skill may invoke it inside the loop. (see
RS-HARNESSP2-001 Q1; Q5 scorer)
**Acceptance**: `python3 tools/sdd-telemetry.py summarize` on a fixture of six
records prints one row per stage with the columns above; `--self-test` exits 0;
`grep -rn sdd-telemetry skills/` hits only the `sdd-orchestrate` telemetry stub
as a pointer to a post-cycle step.
[Priority: should]
