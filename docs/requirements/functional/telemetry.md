---
domain: TELEM
last_updated: 2026-09-20
status: Approved
research_refs: [RS-HARNESSP2-001, RS-008, RS-HARNESSP3-001, RS-HARNESSP4-001, RS-HARNESSP5-001]
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
> **Amended by REQ-TELEM-HARNESSP4-005** (2026-09-18, workstream `harness-p4`):
> the never-rewrite rule gains a **second exception** — the operator-invoked
> `migrate` subcommand of `tools/sdd-telemetry.py`, run by the operator
> **between sessions**, never by a leaf and never while a session is
> appending. The orchestrator-only-writer rule is otherwise unchanged: no
> dispatch template names `migrate`, and the orchestrator itself never runs it.

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
`docs/ws/<id>/traceability.md` for coverage only, never position (verify
Step 3b, review Step 2) — flat `docs/` equivalents under marker `3`. Every
input is under `docs/`; `.sdd/` is not. Deleting `.sdd/` must leave every
skill's detected phase, every staleness verdict and the orchestrator's position
table byte-identical. (see RS-HARNESSP2-001 Q1 detection-input table;
REQ-ORCH-014)
**Acceptance**: with a populated `.sdd/telemetry.jsonl`, `rm -rf .sdd/` followed
by re-running the orchestrator's position table and each stage skill's phase
detection on the same repo yields identical output; `grep -rn '\.sdd/'
skills/*/SKILL.md` hits only the `orchestrate` telemetry stub
(REQ-TELEM-HARNESSP2-007).
[Priority: must]

### REQ-TELEM-HARNESSP2-007: Lint guard on the telemetry path
`tools/sdd-skill-lint.py` must carry a `FORBIDDEN` row (fail severity) for the
pattern `\.sdd/` across every `skills/*/SKILL.md` and `skills/*/references/*.md`,
with an allowlist of exactly three locations: the telemetry stub in
`skills/sdd-orchestrate/SKILL.md`, `skills/orchestrate/references/
telemetry.md`, and `skills/orchestrate/references/write-scope.md` (§3 and
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

### REQ-TELEM-HARNESSP3-001: A positive `TELEMETRY: rec <n>` gate line asserts the append happened
`references/telemetry.md` §3 must add a **positive member to the `TELEMETRY:`
gate-line family** — today the family is `WRITE FAILED | OFF | .gitignore
updated`, with no line for "on, and the append happened":

```
TELEMETRY: rec <n>     # rendered on the gate AFTER an append; <n> counts SUCCESSFUL appends this session
```

`<n>` **counts successful appends in this session** — it is not `dispatch.seq`.
The two diverge whenever a dispatch produces no append (a `WRITE FAILED`, or a
mid-cycle opt-out), and where they diverge the **append count wins**: the line
exists to assert that the append happened, so binding `<n>` to the dispatch
sequence would have a later gate assert an append count that never occurred —
weakening exactly the assurance the requirement provides. Concretely, `<n>` is a
new session-scoped counter incremented **only** on a successful append,
maintained beside `dispatch.seq` in the orchestrator's existing session state
(§3) — no new artifact, and still **never a read of the telemetry file**, so the
write-only rule
(REQ-TELEM-HARNESSP2-004 — "the orchestrator performs zero reads of the file")
is preserved intact, and the line is text, so the non-interference proof of §5
is untouched. The writer sequence already appends *after* the gate decision, so
the next gate is the natural place to assert the previous append. An operator
who sees a gate carrying no `rec` line, no `OFF` line and no `WRITE FAILED` line
knows the append did not happen. (see RS-HARNESSP3-001 Q4 — spec-read, with a
direct negative observation: on 2026-09-18 the gate rendered telemetry as on,
nothing was ever appended, and the text actually rendered — `TELEMETRY: on
(record written after your decision)` — was not a member of the family §3
defines. What no spec read establishes is whether an operator actually notices
an absent line)
**Acceptance**: `references/telemetry.md` §3's gate-line table lists `rec <n>`
and its writer sequence names the gate that renders it; `docs/spec/telemetry.md`
carries the same family, and `skills/sdd-orchestrate/SKILL.md` §The gate states
it in one line; a walkthrough of two gated dispatches with telemetry on renders
`TELEMETRY: rec 1` then `TELEMETRY: rec 2`, and a walkthrough with telemetry on
but the file unwritable renders `TELEMETRY: WRITE FAILED` and no `rec` line;
a **resumption** walkthrough of three gated dispatches whose second append fails
renders `TELEMETRY: rec 1`, then `TELEMETRY: WRITE FAILED`, then
`TELEMETRY: rec 2` — not `rec 3` — and the same holds after a mid-cycle opt-out
(the `OFF` gates append nothing and do not advance `<n>`);
`grep` for a telemetry-file read in the orchestrator's gate path returns
nothing.
[Priority: must]

### REQ-TELEM-HARNESSP3-002: `summarize` reports records-vs-expected per session as a post-cycle backstop
`tools/sdd-telemetry.py summarize` may report a records-vs-expected count per
session, so a missing-append gap is visible post-cycle even if the operator
missed the absent gate line. The reporting slot already exists — `summarize`
skips and counts unparsable lines on a trailing `skipped:` line. This is an
optional backstop to REQ-TELEM-HARNESSP3-001, not a substitute for it, and it
is a post-cycle reader: it must not influence control flow and the orchestrator
must still perform zero reads of the file during a cycle
(REQ-TELEM-HARNESSP2-004). If the plan has no room it is queued in
`verification.md` §Next Steps rather than dropped. (see RS-HARNESSP3-001 Q4 —
counted inside the Q4 item as an optional sub-part, not as a separate item)
**Acceptance** (conditioned on the `may` — if the backstop is **not** built this
cycle, acceptance is that it is queued under `verification.md` §Next Steps and
nothing else changed): **if built**, `python3 tools/sdd-telemetry.py summarize`
on a fixture whose session records fewer appends than gates prints a
records-vs-expected line for that session and `--self-test` exits 0. Either way,
no orchestrator reference instructs a read of the telemetry file during a cycle.
[Priority: may]

### REQ-TELEM-HARNESSP4-001: every dispatch kind gets its own record — verifier, fix and redo first attempts included
The orchestrator's writer (`references/telemetry.md` §2 writer sequence) must
append **one record per dispatch it issues**, for every kind the schema admits
— `pipeline`, `fix`, `fanout_leaf`, `verifier`, `review`, `red` — with
`dispatch.kind` set to the kind actually dispatched. In particular a chunk
verifier dispatch gets a `verifier` record of its own rather than having its
`CHUNK_VERDICT:` written onto the chunk's `pipeline` record alone; a fix
dispatch (a `loop-back-to-fix`, a per-chunk `fix`, or a `RED_BREAK` packet) gets
a `fix` record, never a `pipeline` one; and the first attempt of a redone chunk
keeps its record when the redo is dispatched (the redo is a further record with
`dispatch.redo` incremented). The p3 file holds zero `verifier` and zero `fix`
records across a cycle that ran eight verifiers and three redos, and its one fix
dispatch at `seq` 18 is typed `pipeline`; `records-vs-expected` saw no gap
because nothing was appended and nothing incremented. (workstream `harness-p4`;
see `docs/ws/harness-p3/verification.md` §P2 and §P3, and RS-HARNESSP4-001 §Q2
fixture cross-check — every count recomputed from
`tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`)
**Acceptance**: `references/telemetry.md` §2 names every kind and states the
one-record-per-dispatch rule with a worked example record for a `verifier` and a
`fix` dispatch (non-null `chunk`), and `docs/spec/telemetry.md` carries the same
rule; this cycle's live `.sdd/telemetry.jsonl`, summarised at DONE by
`python3 tools/sdd-telemetry.py summarize`, shows a `verifier` count equal to the
number of chunk verifiers dispatched and a `fix` count equal to the fix dispatches
the gates rendered, with `implied vs recorded` (REQ-TELEM-HARNESSP4-002) reporting
0 missing for both kinds in this cycle's session.
[Priority: must]

### REQ-TELEM-HARNESSP4-002: `expected` is implication-derived, and the headline is the total shortfall
`tools/sdd-telemetry.py summarize` must derive the `expected` of its
`records-vs-expected:` line from **cross-field implications already present in
the records**, not from the highest `dispatch.seq` alone. Per session, for each
kind, `implied.<kind>` is computed as RS-HARNESSP4-001 §Q2 defines it — a
non-null `chunk_verdict` on a non-verifier record implies `1 + dispatch.redo`
verifier dispatches; a `pipeline` record with `dispatch.redo ≥ 1` implies its
first attempts; a non-null `review_verdict` / `red_verdict` on a record of
another kind implies one review / red dispatch per carrying record; fix
dispatches follow REQ-TELEM-HARNESSP4-003 — with `missing.<kind> := max(0,
implied − recorded)` matched **per stage**, never cross-stage and never negative,
and `expected := highest seq + Σ missing`. **Headline definition (ratified
here):** the reported gap is the **total shortfall of every implied append**,
per session — on the p3 fixture 19 missing, `expected 39` against `20` records —
and the implement-stage line reports the **full** implication count (14 for p3:
3 first-attempt pipeline + 11 verifier), because `expected` is a count of
appends that should exist, and any narrower reading would understate the file's
incompleteness. The 8 + 3 "dispatches with no record of their own kind"
reading may be printed as a secondary figure but is not the headline. One
`implied vs recorded` line per kind is printed beside the headline. The
implications are independent of `seq` and of the writer's append discipline
because each is triggered by a field the writer *did* fill for its own gate
rendering; the original class (`seq` incremented, record lost) is retained since
`expected` starts from the highest `seq`. (workstream `harness-p4`; see
RS-HARNESSP4-001 §Q2 — high confidence that the counts reproduce P2 and P3 on
the frozen fixture; the headline choice was routed to requirements by the
spike's third Open Question and is decided here)
**Acceptance**: `python3 tools/sdd-telemetry.py summarize --file tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
prints `expected 39` against 20 records (or the equivalent "19 missing"
headline), an implement line naming 14 missing, and per-kind `implied vs
recorded` lines reading verifier 11 vs 0, pipeline 11 vs 8 at implement,
review 6 vs 2 with 5 missing, red 1 vs 2 with 0 missing; `--self-test` gains one
fixture per implication (verifier, redo first attempt, review, red) and a
negative fixture in which every implied dispatch has its record and the headline
reads 0 missing; `docs/spec/telemetry.md` §Records-vs-Expected and
`references/telemetry.md` §7 state the definition and the headline;
Q-IMPL-HARNESSP3-006 is amended to name the fields used; the tool still reads
nothing but the telemetry file and the orchestrator still performs zero reads of
it during a cycle (REQ-TELEM-HARNESSP2-004).
[Priority: must]

### REQ-TELEM-HARNESSP4-003: the fix implication has two clauses and a mis-typed-fix rule; the fix-only reason set lives in the domain table
The fix implication of REQ-TELEM-HARNESSP4-002 must have **two clauses**:
(a) a record whose `gate.decision` is `loop-back-to-fix` or `fix` implies one
fix dispatch, and (b) a record of a kind other than `fix` whose
`dispatch.reason` is in the **fix-only reason set** — `{red_break}` today —
implies one fix dispatch. Both are needed: on the p3 fixture `seq` 18 is
reachable only through (b), because its predecessor's `gate.decision` is null.
The **mis-typed-fix rule**: when an implied fix is present as a record of
another kind (a `pipeline` record with `dispatch.iteration ≥ 1` whose
predecessor at the same stage decided `loop-back-to-fix`, or whose
`dispatch.reason` is fix-only), `missing.fix` counts **0** for it and `--lint`
(REQ-TELEM-HARNESSP4-004) reports it as a mis-typed record instead — it is a
wrong `kind`, not a missing append, and must not inflate `expected`. The
fix-only reason set is a row of the domain table, so adding a reason later is a
schema change, not a code constant; `reason: REVIEW` at `iteration ≥ 1` with no
preceding `loop-back-to-fix` at the stage (p3 `seq` 3–5) is a `--lint`
**warning**, not a count, because the fixture cannot say whether those were fix
dispatches or mis-labelled first dispatches and a legitimate chunk redo (`seq`
13) carries the same reason. (workstream `harness-p4`; see RS-HARNESSP4-001 §Q2
"Fix dispatches" and its fourth Open Question — decided here as a warning)
**Acceptance**: on the frozen fixture the tool reports `implied.fix 2, recorded
0, missing 0` with `seq` 2 and `seq` 18 listed as mis-typed fixes by `--lint`
and `seq` 3–5 as `reason: REVIEW without preceding loop-back-to-fix` warnings;
a self-test fixture with a `red_break` pipeline record and a null-decision
predecessor is flagged (clause (b)); a fixture with a `loop-back-to-fix`
decision followed by no record at all counts 1 missing fix; the fix-only reason
set is declared in the domain table and echoed in `docs/spec/telemetry.md`
§Record Schema.
[Priority: must]

### REQ-TELEM-HARNESSP4-004: `--lint` validates every field from one domain table, and that table is the schema's single source of truth
`tools/sdd-telemetry.py` must gain a `--lint` subcommand that validates
**every** field of every record against its declared domain — enum membership
(`dispatch.kind`, `gate.decision`, verdict tokens, `dispatch.reason`), type
(`dispatch.chunk` int-or-null, counters int, shas as short hex, no `"HEAD"`
literal), the **fixed key set** (an undeclared key such as `git.commit_n` is a
finding; a missing declared key is a finding), and the cross-field rules of
REQ-TELEM-HARNESSP4-003 plus "non-null `chunk_verdict` on a non-verifier record
with no verifier record for that chunk" and "`proceed` implement record with
`head_before == head_after`" — not only the one field that happened to break.
**The domain table in the tool is the single source of truth for the record
schema**: `docs/spec/telemetry.md` §Record Schema and `references/telemetry.md`
§2 are renderings of it, and a self-test asserts the rendered table and the code
table agree (whether by generating the spec block from the code or by parsing
the spec block and diffing is a specs decision; the invariant is one table, two
readers). Both documents must also carry at least one worked example whose
`chunk` is non-null and one each for a `verifier` and a `fix` record, since the
p3 mis-typing traces to a sole `"chunk":null` example. (workstream `harness-p4`;
see `docs/ws/harness-p3/verification.md` §P1 and §P3 — the R1 fix validated one
field, and the same session wrote `kind: "gate"`; RS-HARNESSP4-001 §Q2 lists
five violation classes already present in the fixture)
**Acceptance**: `python3 tools/sdd-telemetry.py --lint --file tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
exits non-zero and reports, at minimum, `kind: gate` on `seq` 20, the header
strings on `seq` 6–13, `head_after: "HEAD"` on `seq` 5, null `git` heads on
`seq` 6–14, 40-character shas on `seq` 15–20, and the undeclared key
`git.commit_n` on `seq` 15–20; a gapless in-domain fixture exits 0;
`--self-test` covers each domain class with one mutation; the schema-agreement
self-test fails when a row is added to the code table but not the spec table or
vice versa; `python3 tools/sdd-skill-lint.py` exits 0.
[Priority: must]

### REQ-TELEM-HARNESSP4-005: the 8 mis-typed live records are migrated in place, stamped partial, only after the writer, `expected` and `--lint` land — the fixture is never touched
`tools/sdd-telemetry.py` must gain a `migrate` subcommand that rewrites the 8
`"Chunk N"` `dispatch.chunk` strings of the live `.sdd/telemetry.jsonl` (the
p3 session's `seq` 6–13) to the integer `N` **in place**, and marks the migrated
records so that the per-chunk block `summarize` renders from them is **stamped
partial** — it must say that verifier, fix and redo records for those chunks
were never written and cannot be reconstructed, so the block cannot be read as
a full per-chunk history. `migrate` is the second, **operator-invoked**
exception to REQ-TELEM-HARNESSP2-004's never-rewrite rule (see the amendment
note there): the migration is run by the **operator between sessions** — never
by a leaf (which would breach the orchestrator-only-writer rule) and never
while a session is appending (which would race the orchestrator's appends); no
dispatch template mentions it. The migration is **ordered**: the plan may schedule it
only after REQ-TELEM-HARNESSP4-001, -002, -003 and -004 have landed and `--lint`
reports the migrated records clean on their typed fields; otherwise the
migrated block asserts more than the evidence supports (the P-section trap).
`tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` is read-only evidence and
is **never** modified, reformatted or migrated — `migrate` refuses a path under
`tools/fixtures/`, and every test runs against the fixture as input with the
output written elsewhere. Decided at DISCUSS; requirements inherit it unchanged.
(workstream `harness-p4`; see `docs/ws/harness-p3/verification.md` §"Can the 8
records be repaired in p4?", `docs/ws/harness-p4/kickoff.md` §Decided at
DISCUSS, and `tools/fixtures/README.md`)
**Acceptance**: `sha256sum tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
still reads `7e20b630…af9237` at DONE and `git diff --stat main -- tools/fixtures/`
is empty; `python3 tools/telemetry.py migrate --file <copy of the fixture>
--out <tmp>` produces a file on which `summarize` renders a per-chunk block for
chunks 0–7 carrying the word `partial` and the unreconstructable kinds named;
`migrate --file tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` exits
non-zero without writing; the plan lists the migration task after the four
prerequisite tasks; the operator ran `migrate` on the live file **before the
verify stage** (between sessions, with no orchestrator session open) and this
cycle's `verification.md` records the resulting `--lint` result on the migrated
live records (expected: no typed-field finding).
[Priority: must]

### REQ-TELEM-HARNESSP4-006: `scope.widened` records an operator widening of the write scope
The record schema must gain `scope.widened` (int — the count of globs the
operator added to the dispatched write scope beyond the template's default for
that stage; 0 when none), a sibling of `dispatch.write_scope_n`, written by the
orchestrator from session state it already holds (the dispatched scope and the
template default). It is a count, never the glob text, so the counts-not-text
rule of REQ-TELEM-HARNESSP2-002 holds. Fixing R1 in p3 required widening the
verify scope to `tools/` and `skills/`; the scope check then correctly read those
paths `IN`, but `SCOPE: CLEAN` looks identical either way and nothing durable
records that a widening happened — a post-cycle reader cannot tell a clean stage
from a widened one. (workstream `harness-p4`; see `docs/ws/harness-p3/verification.md`
§L6 and RS-HARNESSP4-001 §Implications — record-field addition, hence a
requirements decision)
**Acceptance**: the domain table (REQ-TELEM-HARNESSP4-004) declares
`scope.widened` as int with default 0, and `docs/spec/telemetry.md` §Record
Schema and `references/telemetry.md` §2 render it; `summarize` prints the number
of widened dispatches per session; a self-test fixture with `scope.widened: 2`
is in-domain and one with a string value is a `--lint` finding; the writer
sequence in `references/telemetry.md` §2 names where the value comes from without
any read of the telemetry file.
[Priority: should]

### REQ-TELEM-HARNESSP4-007: a `commit` record group carries the `COMMIT:` outcome as counts and an enum
The record schema should gain a `commit` group — `{token: COMPLETE | INCOMPLETE
| null, missing_n: int, extra_n: int}` — written from the `COMMIT:` result of
REQ-HARN-HARNESSP4-001 for the dispatch the record describes (`null` / 0 / 0 for
dispatches whose gate does not commit: review, verifier, red). Only the token and
the two counts are recorded, never the path names, per the counts-not-text
rule; telemetry remains non-load-bearing — the group is a post-cycle trace of
the signal, and `COMMIT:` itself is rendered from git, never from the record.
(workstream `harness-p4`; see RS-HARNESSP4-001 §Q1 cost table and
§Recommendation — the spike recommends the group; adopting it costs the two
telemetry texts and one writer/summariser change)
**Acceptance**: the domain table declares the group, both telemetry documents
render it, `summarize` prints per-session `COMMIT: INCOMPLETE` counts, an
in-domain fixture with `token: INCOMPLETE, missing_n: 1, extra_n: 0` passes
`--lint` and one with `token: DROPPED` fails it; `grep -n 'commit' skills/sdd-orchestrate/references/loop-control.md`
shows the gate reading git, not telemetry, for the signal.
[Priority: should]

### REQ-TELEM-HARNESSP4-008: an opt-in `--plan` floor for implement-stage expectations
`summarize` may accept `--plan <path>` and, when given, compute a **floor** for
the implement stage — `chunk_count(plan)` pipeline dispatches, doubled when any
chunk record carries a non-null `chunk_verdict` (the verifier was on) — and
report when recorded implement records fall below it. The floor is the only
reader-side check that sees a chunk whose pipeline **and** verifier records are
both missing and whose verdicts were written nowhere; it can never see redos,
because `Redo: N` and the verifier opt-in are session state that the plan does
not hold. It is opt-in and reads an artifact that already exists; no new
artifact under `docs/` and no phase-detection input. (workstream `harness-p4`;
see RS-HARNESSP4-001 §Q2 candidates table — accepted as a floor, not as
`expected`; medium confidence)
**Acceptance** (conditioned on the `may` — if not built, it is queued under
`verification.md` §Next Steps): **if built**, `summarize --plan
docs/ws/harness-p3/plan.md --file <fixture>` prints an implement floor of 8 (16
with verifier) and flags no shortfall against the 8 recorded pipeline records
while REQ-TELEM-HARNESSP4-002's implication line still reports the 14 missing;
`--self-test` covers a plan with a chunk that has no record at all.
[Priority: may]

<!-- REQ-TELEM-HARNESSP5-NNN: workstream-prefixed additions for the harness-p5
     cycle (RS-HARNESSP5-001; marker 4, per docs/spec/ws-ids.md). Findings 1–6
     are the p4 live-run findings of docs/ws/harness-p4/verification.md
     §Next Steps; the seq numbers cited (21/24/27, 2/4/6) come from that report
     and plan O2 until the p4 fixture of -007 is cut. -->

### REQ-TELEM-HARNESSP5-001: a stage-level `fix` record carries no `chunk_verdict` (writer rule)
`docs/spec/telemetry.md` §Writer rule (i), mirrored in
`references/telemetry.md` §3, must copy a verifier's `CHUNK_VERDICT:` onto the
dispatched record **only when that record is a per-chunk dispatch**
(`dispatch.chunk != null`). A stage-level `fix` record (`iteration ≥ 1`,
`redo: null`, `chunk: null` — the implement-stage `loop-back-to-fix` dispatch
after the stage review) keeps `verdict.chunk_verdict: null`; its verifiers'
verdicts live on their own `verifier` records. `dispatch.chunk` keeps its one
meaning ("the `### Chunk N:` number for per-chunk dispatches") — the writer
never stamps a chunk on a stage-level fix, which may touch several chunks and
whose verifiers may run under several. The `--lint` cross-field rule is
unchanged and becomes true by construction: a `chunk_verdict` on a record whose
`(stage, chunk)` has no verifier is now always a writer defect. Ratified as
Q-REQ-P5-B. (workstream `harness-p5`; see RS-HARNESSP5-001 §Q2 finding 2 — seq
21, 24, 27 of p4 session 2 per `docs/ws/harness-p4/verification.md` §Next Steps)
**Acceptance**: §Writer rule (i) and `references/telemetry.md` §3 state the
per-chunk-only condition; `skills/sdd-orchestrate/SKILL.md` §Telemetry agrees;
on the frozen p4 fixture (REQ-TELEM-HARNESSP5-007) `--lint` still lists the
three records as `[cross-field]` findings by seq in §Fixture-Based Test
Contract (historical fact, like the p3 `seq 20`); `python3 tools/sdd-skill-lint.py`
exits 0.
[Priority: must]

### REQ-TELEM-HARNESSP5-002: `summarize` implies a first-attempt pipeline only for chunk groups (reader)
`tools/sdd-telemetry.py`'s `expected_rows()` must sum `implied.pipeline` over
implement groups with `chunk != null` **only**; a `(implement, null)` group of
stage-level `fix` records implies no pipeline dispatch. `attempts()` and
`implied.verifier` are unchanged (a null group with null `chunk_verdict`
implies nothing). (workstream `harness-p5`; see RS-HARNESSP5-001 §Q2 finding 1
— the false "1 missing pipeline" on the p4 live file)
**Acceptance**: `python3 tools/sdd-telemetry.py summarize --file tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl`
reports no missing pipeline for the `(implement, chunk null)` group; the p3
fixture's `expected 39` / 19 missing and every REQ-TELEM-HARNESSP4-002 number
are unchanged (sha256 asserted before and after); `--self-test` covers a
session with three stage-level fixes and no chunk record → 0 implied pipeline.
[Priority: must]

### REQ-TELEM-HARNESSP5-003: `v: 1` records are exempt from the equal-heads rule — no migration marker
The `--lint` cross-field equal-heads rule (Q-IMPL-HARNESSP4-007: a `proceed`
implement record with `head_before == head_after`, `files_written_n > 0` and no
landed commit group) must evaluate `v: 2` records **only**; a `v: 1` record is
exempt because it carries no field that can prove landing. The `migration`
marker is **not** stamped on such records — `migration.from` is the enum
`chunk-string` for a rewrite `migrate` performed, and the p4 records carry no
defect to rewrite. Documented in §Schema Lint's cross-field row — the fold-in
of Q-IMPL-HARNESSP4-007 under REQ-QIMPL-HARNESSP5-001 carries the exemption into
Approved text, so a separate Q-IMPL entry amending -007's v1 branch is optional
(`may`, at specs' discretion) rather than a third statement of the same rule.
Ratified as Q-REQ-P5-B.
(workstream `harness-p5`; see RS-HARNESSP5-001 §Q2 finding 3 — seq 2, 4, 6 of
p4 session 2; the branch has no true positive on record and one live false
positive)
**Acceptance**: `--self-test`: `v: 1` + equal heads + `files_written_n > 0` →
no finding; the same shape as `v: 2` with null `commit.token` → finding; on the
frozen p4 fixture `--lint` raises no equal-heads finding on seq 2/4/6; the
frozen p3 fixture's `--lint` finding **set** is unchanged (order-insensitive,
compared as REQ-TELEM-HARNESSP5-006 specifies — its `seq` sort may reorder the
p3 findings).
[Priority: must]

### REQ-TELEM-HARNESSP5-004: `summarize` and `--lint` admit the same `v` — integer-typed
Both entry points must admit a record's `v` through one shared helper that
tests `_is_int(v) and v in ADMITTED_V`, so `v: 2.0` (a float, `2.0 in {1, 2}`
is `True` today) is skipped and counted by `summarize` exactly as `--lint`
rejects it with a `[type] v` finding. (workstream `harness-p5`; see
RS-HARNESSP5-001 §Q2 finding 4 — `load()` membership test)
**Acceptance**: `--self-test` feeds a synthetic record with `v: 2.0` — `summarize`
reports it skipped and counted, `--lint` emits `[type] v`; `grep -c 'ADMITTED_V' tools/sdd-telemetry.py`
shows the membership test in one helper called from both `load()` paths.
[Priority: must]

### REQ-TELEM-HARNESSP5-005: the `commit` group records the gate's closing line; `summarize` labels it as accepted
`docs/spec/telemetry.md` §Writer must state that the `commit` source records
the **closing** `COMMIT:` line of the gate — an `amend` re-renders `COMPLETE`
before the append, so an amended omission is recorded as `COMPLETE`, and only an
`accept (note)` leaves `INCOMPLETE` on record. `summarize`'s label becomes
`COMMIT: INCOMPLETE (accepted): N` (§Records-vs-Expected, §Fixture-Based Test
Contract) so the count is not read as the number of omissions rendered. A
`commit.amended` field is **deferred** (Q-REQ-P5-E): it would change the
`v: 2` key set with no evidence anyone needs the count. (workstream
`harness-p5`; see RS-HARNESSP5-001 §Q2 finding 5 — `COMMIT: INCOMPLETE: 0`
although one `INCOMPLETE` was forced live; the O3 record carries `COMPLETE`)
**Acceptance**: `summarize` on the frozen p4 fixture prints
`COMMIT: INCOMPLETE (accepted): 0`; the §Writer sentence and
`references/telemetry.md` §3 agree; `test_schema_table_agrees` still passes (no
key added).
[Priority: must]

### REQ-TELEM-HARNESSP5-006: `--lint` findings are emitted in `seq` order
`lint()` must stable-sort its findings by `(int seq ascending, then non-int seqs
in insertion order)` before rendering, across its three passes (per-record
type/enum/key, per-session mis-typed-fix + cross-field, reason-review).
(workstream `harness-p5`; see RS-HARNESSP5-001 §Q2 finding 6)
**Acceptance**: `--self-test` builds a type finding on seq 5 and a cross-field
finding on seq 2 and asserts the rendered order 2, 5; the frozen p3 fixture's
finding **set** is unchanged (sha256 asserted over the **sorted** finding
lines, so the hash is order-insensitive — the same comparison
REQ-TELEM-HARNESSP5-003's acceptance uses).
[Priority: should]

### REQ-TELEM-HARNESSP5-007: a frozen p4 fixture is cut by the operator; the p3 fixture and the live file are untouched
`tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl` — a copy of
`.sdd/telemetry.jsonl` as it stood at harness-p4 DONE (**67 lines**, i.e.
`head -67` of the live file: harness-p3 migrated at lines 1–20, harness-p4 at
lines 21–67 — 47 records, session 1 = 20 records at `v: 1`, session 2 = 27
records starting `v: 2` at seq 8; harness-p5 begins at line 68. [Corrected
2026-09-20: the earlier figure — 61 lines, "p4 session 1 seq 1–13, p4 session 2
seq 1–28" — was measured wrong. The correction is consequence-free: `--lint` on
a 61-line and on a 67-line cut produce byte-identical output — 65 findings, 4
warnings, the same three `[cross-field]` records at seq 21, 24, 27 — so no
acceptance number below moves. [Re-measured 2026-09-20 after Chunk 4's reader fixes: **62 findings, 4 warnings** — the `v: 2`-only equal-heads guard correctly removed the three findings at `seq` 2, 4 and 6. 65/4 is the figure as measured before those fixes; the equivalence claim is unchanged — both cuts still produce byte-identical output, with the same three `[cross-field]` records at `seq` 21, 24 and 27.]]) — must be cut by the **operator** as a plan
operator task (leaves never read `.sdd/`), scheduled before the telemetry
chunk, with its sha256 recorded in `tools/fixtures/README.md`; the `migrate`
fixture guard covers it automatically (path under `tools/fixtures/`). Findings
1, 2, 3 and 5 are reproduced on it; 4 and 6 are synthetic self-test cases.
`tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` and the live file are
never modified. (workstream `harness-p5`; see RS-HARNESSP5-001 §Q2 "Fixture")
**Acceptance**: `shasum -a 256 tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl`
matches the README; `wc -l` = 67; `git diff --stat main -- tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
is empty; the p4 fixture's sha256 is asserted before and after every
`--self-test` case that reads it.
[Priority: must]

### REQ-TELEM-HARNESSP5-008: verifier advisories — three `--lint` self-test cases
`tools/sdd-telemetry.py --self-test` should gain: (a) a positive
`commit.token`-on-non-committing-kind case for a kind **other than** `review`
(`verifier` or `red`) → `[cross-field]`; (b) a record with `dispatch.reason:
RED_BREAK` (uppercase) → `[enum]` finding, so the canonical `red_break`
spelling of Q-IMPL-HARNESSP4-005 is tested, not only stated; (c) a
`migration.from` value outside the `chunk-string` enum → `[enum]` finding (the
validator accepts any string today). (workstream `harness-p5`; see
`docs/ws/harness-p4/verification.md` verifier advisories)
**Acceptance**: the three cases are named in `--self-test` output and each
fails when its check is removed in a temp copy; the frozen fixtures' outputs
are unchanged.
[Priority: should]
