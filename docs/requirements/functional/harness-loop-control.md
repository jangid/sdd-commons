---
domain: HARN
last_updated: 2026-09-17
status: Approved
research_refs: [RS-008, RS-005, RS-006]
---

# Requirements: Harness Hardening — Loop Control

## Overview

Hardens the SDD harness (`sdd-orchestrate` driving `sdd-implement`, `sdd-review`,
`sdd-replan`) with the deterministic loop-control, decoupled-verification and
boundary patterns from the harness-engineering literature, as scoped in the
idea catalogue (`docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md`,
ideas A1–A4, B5–B7, C8–C10, E13) and de-risked by RS-008. The `HARN` domain
spans three files sharing one ID sequence:

- **This file — loop control** (REQ-HARN-001..008, 027): a max-iteration guard on
  the review fix loop and on replan re-entries, a budget slot on every dispatch,
  an attempt ledger with an oscillation rule in stuck detection, a bounded
  checkpoint on circuit-break, and the no-new-artifact constraint (RS-008 Q1, Q3).
- **`harness-verification.md`** (REQ-HARN-009..019): the structured `RETURN:`
  block, repair packet, `VERDICT:` token, fresh chunk-close verifier, pruned
  re-dispatch state and orchestrator-owned routing (RS-008 Q2–Q4). The SKILL.md
  size audit (C10) is specified in the LINT domain (`integration/skill-lint.md`).
- **`harness-boundaries.md`** (REQ-HARN-020..026): a declared write scope per
  dispatch, checked mechanically on return, commit ownership and snapshot
  ordering (RS-008 Q5).

Standing constraints every requirement in the domain respects: no new on-disk
artifact type (REQ-ORCH-004), reviews stay ephemeral (REQ-ORCH-013), no
loop-position marker or authoritative loop log (REQ-ORCH-014), fix re-dispatches
carry findings and paths only (REQ-ORCH-012), and `sdd-review` is never the chunk
verifier (REQ-REV-005, REQ-REV-006). `sdd-implement` standalone (no orchestrator)
keeps its current behavior; every orchestrate-only mechanism is a second pass
layered on top, not a replacement (REQ-ORCH-001).

**Marker-4 resolution rule (applies to every HARN requirement).** Under
`docs/.sdd-version` == `4` the same artifacts are rooted at `docs/ws/<id>/`
(`plan.md`, `plan-history/`, `verification.md`, per-workstream `traceability.md`)
and the revert/merge target is the workstream branch, not `main`; marker `3` is
unchanged.

**Procedure placement.** Orchestrator procedure text introduced by this domain
(scope default table, three-command scope check, finding format, commit
ownership, snapshot ordering, `RETURN:` field-source mapping, verdict branching)
lands in **new** `skills/sdd-orchestrate/references/` files —
`references/write-scope.md` and `references/return-contract.md` — with short
stubs/pointers in `SKILL.md`, so the entry point keeps reading as a table of
contents (REQ-LINT-003, REQ-LINT-007).

Terminology: a **dispatch** is one subagent invocation by the orchestrator. The
five dispatch types are *pipeline* (one stage, sequential mode), *fix
re-dispatch* (loop-back-to-fix of a stage), *fan-out leaf* (one chunk-group in a
worktree), *review* (`sdd-review`), and *chunk verifier* (REQ-HARN-014). A
**leaf** is any non-review dispatch — the chunk verifier is a leaf with an empty
write scope. **Observable units** are counts the subagent can report about itself
without harness support — tasks, chunks, tool calls, test runs, approaches.

## Requirements

### Loop control

### REQ-HARN-001: Fix-loop max-iteration guard
The orchestrator must cap the number of loop-back-to-fix re-dispatches per stage
within one orchestrator session at a configurable maximum (default **3**). Each
fix re-dispatch must state its position as `iteration N of MAX`. When a stage's
review still does not pass after the MAX-th fix iteration, the orchestrator must
**not** dispatch another fix; it must exit to the operator at the gate with a
compiled findings log (the review's Critical/Material findings across the
iterations, by iteration) and offer only stop, manual intervention, or an
explicit operator-authorized extra iteration. The count is per-session — it is
not persisted to any artifact (REQ-ORCH-014) and restarts at 0 in a new session,
which is itself a human intervention. (see RS-008 Q1)
**Acceptance**: a session that reaches REJECT three times on one stage shows a
fourth gate with the compiled log and no automatic fourth dispatch; the
`iteration N of 3` line appears in each fix dispatch prompt; no file under
`docs/` records the counter.
[Priority: must]

### REQ-HARN-002: Replan re-entry cap, derived from plan-history
The orchestrator must cap replan re-entries per cycle at a configurable maximum
(default **3**). The count must be **derived**, not stored: it is the number of
`docs/plan-history/*-replan-*.md` archives whose filename date is on or after the
kickoff's `date:` frontmatter (falling back to the kickoff's commit date when the
field is absent, the same fallback `sdd-orchestrate` §KICKOFF uses for
`research_id`). On the MAX-th re-entry the orchestrator must surface the cap as a
gate event (REQ-ORCH-017) and must not route back into `sdd-replan` again without
an explicit operator decision. Minor in-place replans leave no archive and are
deliberately not counted. Under `docs/.sdd-version` == `4` the archives and the
kickoff are the active workstream's (`docs/ws/<id>/plan-history/`,
`docs/ws/<id>/kickoff.md`), so the count is per workstream; marker `3` is
unchanged. (see RS-008 Q1)
**Acceptance**: with three `-replan-` archives dated ≥ kickoff date, a fourth
replan trigger produces a gate pause naming the cap; archives dated before the
kickoff date or lacking the `-replan-` segment do not count.
[Priority: must]

### REQ-HARN-003: `-replan-` archive filename convention is a stated contract
Every plan archive written by `sdd-replan` must carry the `-replan-` segment in
its filename (`{date}-replan-{reason}.md`, or `{date}-m{N}-replan-{reason}.md`
per milestone), and no other skill (`sdd-plan` rewrite archives, milestone-
complete archives) may use that segment. `sdd-replan/SKILL.md` must state this
as an explicit contract, not an implicit convention, because REQ-HARN-002's
derivation depends on it. (see RS-008 Q1; lint row: REQ-LINT-005)
**Acceptance**: `sdd-replan/SKILL.md` contains the stated rule; `sdd-plan/SKILL.md`
archive names contain no `-replan-`; `tools/sdd-skill-lint.py` carries a
`REQUIRED` row for the pattern in `sdd-replan/SKILL.md`.
[Priority: must]

### REQ-HARN-004: Budget slot on every dispatch
Every dispatch template — pipeline, fix re-dispatch, fan-out leaf, review, and
chunk verifier — must carry an explicit `Budget:` slot stated in observable
units (e.g. "1 chunk, ≤ 25 tool calls, ≤ 3 test runs"; for a review "≤ 15 tool
calls, read-only"). The orchestrator must fill the slot on every dispatch; a
dispatch with an empty budget is a template violation. The read-only review
dispatch **does** get a budget slot (operator decision, Q-REQ-C in
`index.md`). (see RS-008 Q4 contract table, catalogue A2)
**Acceptance**: each fenced dispatch template in
`skills/sdd-orchestrate/references/dispatch-templates.md` and
`references/fan-out.md` contains `Budget:`; `tools/sdd-skill-lint.py` has a
`REQUIRED` row per template file (REQ-LINT-005).
[Priority: must]

### REQ-HARN-005: Budget exhaustion is a checkpointed return, never a silent overrun
A leaf that reaches its stated budget must stop, **write or return** the
circuit-break checkpoint (per REQ-HARN-008 — the sequential implementer writes
it into the plan; a fan-out leaf, barred from the plan, returns it) when the
exhaustion occurs mid-task, and return with `status: BUDGET_EXHAUSTED` and a
`budget_consumed` field in the same observable units the dispatch's `Budget:`
slot was stated in. The orchestrator must use `budget_consumed` to size the next
repair packet's budget (REQ-HARN-011). `budget_consumed` is **self-reported** by
the leaf — the harness exposes no tool-call counter to the orchestrator — so
adherence is only as trustworthy as the leaf; this is a recorded v1 limitation,
not a defect to be fixed in this cycle. (see RS-008 Q3)
**Acceptance**: the pipeline and fan-out templates instruct the leaf to
self-count in the stated units and to return `budget_consumed`; a `RETURN:`
block with `status: BUDGET_EXHAUSTED` and no `budget_consumed` is treated by the
orchestrator as malformed (REQ-HARN-009) and surfaced at the gate.
[Priority: must]

### REQ-HARN-006: Attempt ledger in sdd-implement
`sdd-implement` must keep, per task in its working context, an attempt ledger
with one entry per attempted fix: `attempt` (ordinal), `hypothesis` (one line),
`change` (files/lines touched, one line), `result` (which tests now pass/fail,
one line). The ledger must also carry a `verified_do_not_touch` list of paths
whose tests pass and that later attempts must not modify. The ledger lives in
the leaf's context only; its sole durable trace is the checkpoint
(REQ-HARN-008). It is **not** a Q-IMPL entry — Q-IMPL records deviation
decisions, the ledger records attempts; when an attempt reveals a spec ambiguity
the implementer files a Q-IMPL entry as today and cites its id in the ledger /
`open_questions`. (see RS-008 Q1, Q3; catalogue A3)
**Acceptance**: `sdd-implement/SKILL.md` Step 3 defines the four ledger fields and
`verified_do_not_touch`; no ledger text is written to `docs/spec/*.md` or
`docs/handoff/kickoff.md`.
[Priority: must]

### REQ-HARN-007: Oscillation rule in stuck detection
`sdd-implement` stuck detection must fire, in addition to its existing triggers
(same test failing 3+ times with different fixes, 2× expected effort, spec
contradiction), when the ledger shows oscillation: (a) an attempt's `result`
reports a test failing that an earlier attempt's `result` reported passing (a fix
re-introduced a fixed failure), or (b) an attempt's `change` matches an earlier
attempt's `change` (a repeated rejected patch). Both are string comparisons over
the ledger and need no new tooling. Firing follows the existing stuck path:
checkpoint (REQ-HARN-008) then replan trigger. (see RS-008 Q3; catalogue A3)
**Acceptance**: `sdd-implement/SKILL.md` Step 3 lists both oscillation conditions
with the word "oscillation"; a ledger fixture with `attempt 2: test_drift
REGRESSED` after `attempt 1: test_drift passes` is described as stuck.
[Priority: must]

### REQ-HARN-008: Circuit-break checkpoint in the plan's blocked-task note
When stuck detection (including oscillation), budget exhaustion, or the
fix-loop cap fires on an implement task, a structured checkpoint must be written
as the blocked-task note under that task in `docs/plan.md` (`docs/ws/<id>/plan.md`
under `docs/.sdd-version` == `4`; marker `3` unchanged) — the slot `sdd-replan`
already defines ("mark blocked tasks — note why they're blocked and what unblocks
them"). The checkpoint must be bounded (≤ ~15 lines) and contain: failing test
names with one-line reasons, the last hypothesis, a one-line-per-attempt ledger
summary, and the open question (citing a Q-IMPL id where one was filed, never
duplicating it). Full tracebacks must not be stored — they are regenerated by
re-running the named tests. The checkpoint is composed from the `RETURN:` block
(REQ-HARN-009) with **no dedicated checkpoint field**: failing tests + reasons ←
`failures[].test` / `failures[].message`; last hypothesis ← last
`ledger[].hypothesis`; ledger summary ← `ledger[].change` + `ledger[].result`
one-liners; open question ← `open_questions[]`. In sequential mode the
implementer writes it; under fan-out the leaf returns it and the orchestrator
applies it in its post-merge bookkeeping (leaves are barred from writing the
plan). A blocked note does not change phase detection (the plan still has
incomplete tasks) and cannot make the plan stale. (see RS-008 Q1; catalogue A4)
**Acceptance**: `sdd-implement/SKILL.md` and `sdd-replan/SKILL.md` state the
checkpoint format and the RETURN-field mapping; a checkpoint fixture is ≤ 15
lines and contains no traceback frames; `sdd-replan` Step 1 reads the checkpoint
as its "stuck state" input instead of "recent conversation context".
[Priority: must]

### Constraints

### REQ-HARN-027: No new on-disk artifact type
Every mechanism in this domain must fit inside existing artifacts and dispatch
templates: fix counts are session-scoped, replan counts are derived from
`plan-history`, the ledger lives in leaf context, the checkpoint reuses the plan's
blocked-task note, the `RETURN:` block, repair packet, `VERDICT:`,
`CHUNK_VERDICT:` and `SCOPE:` tokens are return/gate text, and the write scope is
a template slot. New `skills/sdd-orchestrate/references/*.md` files are skill
text, not project artifacts, and are permitted. REQ-ORCH-004 (kickoff is the
only new artifact), REQ-ORCH-013 (reviews ephemeral) and REQ-ORCH-014 (no loop
marker / loop log) must remain satisfied verbatim; no `docs/reviews/`, `.sdd/` or
telemetry file is created (telemetry is deferred to the next cycle, catalogue
D11). (see RS-008 Implications for Design)
**Acceptance**: `git ls-files docs/` after a full orchestrated cycle shows no file
type that did not exist before this feature, other than the `docs/plan-history/`
archives `sdd-replan` already produces.
[Priority: must]
