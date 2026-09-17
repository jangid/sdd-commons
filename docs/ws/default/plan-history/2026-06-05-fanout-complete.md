# Implementation Plan: sdd-orchestrate Implement-Stage Fan-out (Design B)

## Overview

Promote the implement-stage fan-out feature in `skills/sdd-orchestrate/` from
"v1 sequential, fan-out deferred" to the **active Design B** behavior specified by
`docs/spec/orchestration.md` (the "Sequential Execution and Implement-Stage
Fan-out" section, REQ-ORCH-016 and REQ-ORCH-022..028). Design B is
**orchestrator-owned fan-out, one level deep**: the orchestrator derives
independent chunk-groups from the plan's chunk dependency graph, provisions one
git worktree per group, dispatches one **leaf** implement subagent per group,
then merges the branches sequentially into `main` (with an abort-and-redo-by-
re-derivation conflict fallback and a sequential convergence fallback) **before**
the implement-stage review runs. The work is Markdown skill authoring — edits to
`SKILL.md` and `references/` plus operator-doc reconciliation — so verification is
inspection / acceptance-criteria-based, not unit tests. One open uncertainty
(dispatch concurrency, REQ-ORCH-028) is carried as a budgeted [spike]; it affects
only wall-clock speedup, never correctness. Out of scope: modifying any other
`sdd-*` skill (REQ-ORCH-001) — in particular `sdd-implement` is untouched.

## Conventions

- **Task types**: [implement] produces SKILL.md / references / doc changes;
  [spike] produces a time-boxed finding that may trigger replan; [verify]
  validates against spec acceptance criteria (inspection-based — no unit tests
  for Markdown skills).
- **Chunk headers**: `### Chunk N: <name>` per v3 conventions.
- **Traceability**: each task's `(REQ-…)` reference identifies the requirement;
  the spec section is named inline. After each chunk, update
  `docs/requirements/traceability.md` Implementation / Verified columns for the
  REQ-ORCH IDs that chunk closes.
- **Chunk close**: 4-check review per `chunk-close-review.md` at each chunk
  boundary.
- **No-modify constraint**: do NOT edit any other `sdd-*` skill; the orchestrator
  derives fan-out boundaries by *reading* the plan, never by changing
  `sdd-implement` (REQ-ORCH-001, REQ-ORCH-016).

## Chunks

### Chunk 0: Extract the fan-out procedure to references/, then promote the SKILL.md body

**Goal**: The bulky fan-out dispatch/merge procedure lives in
`skills/sdd-orchestrate/references/` **from the outset**, and
`skills/sdd-orchestrate/SKILL.md` describes the active Design B fan-out behavior
in concise prose that **points to** that reference — boundary derivation, opt-in
gate, the fan-out lifecycle (provision → dispatch → merge → teardown), and
conflict handling — replacing the "sequential / fan-out deferred" framing, while
modifying no other `sdd-*` skill and keeping SKILL.md under the ~500-line ceiling.

**Tasks**:
1. [implement] Create the fan-out reference **first** — add the fan-out dispatch +
   worktree-merge procedure to `skills/sdd-orchestrate/references/` (extend
   `dispatch-templates.md` or add a `fan-out.md`): the per-group implement dispatch
   prompt (worktree path/branch pinned, leaf clause, inline `git -c` identity,
   chunk-group tasks) and the orchestrator merge/teardown/conflict-redo command
   sequence. This is the bulky procedure; landing it in `references/` before the
   SKILL.md prose keeps SKILL.md lean from the start (the ~500-line ceiling is a
   replan trigger). Traces to §Packaging, §Worktree Provisioning, §Merge-Conflict
   Handling. (REQ-ORCH-019, supports 022..027)
2. [implement] Rewrite the Execution Model / sequential section so sequential is
   the default but fan-out is an **active opt-in** at the implement gate (not
   deferred); fan-out is available **only** at the implement stage; concise prose
   that points to the fan-out reference from task 1 rather than inlining the
   procedure. Traces to §Sequential Execution and Implement-Stage Fan-out, §Fan-out
   Design Resolution (Design B selected, Design A ruled out infeasible).
   (REQ-ORCH-015, REQ-ORCH-022)
3. [implement] Boundary-derivation rule — orchestrator computes independent
   chunk-groups by parsing the plan's chunk-level `**Depends on**: Chunk N` field
   (or its `Entry criteria: Chunk N complete` prose equivalent), **not**
   milestone-level Entry/Exit; fan-out applies only when ≥2 independent branches
   exist; if the plan has no parseable chunk-level dependencies, **degrade to
   sequential** and never guess a boundary. Traces to §Fan-out Boundary Rule.
   (REQ-ORCH-016)
4. [implement] Opt-in gate behavior — fan-out is never automatic; at the implement
   gate the orchestrator offers it as an explicit choice, may surface the
   independent-group count, and when the graph is a **single chain** (or has no
   parseable chunk deps) tells the operator **at the gate** that fan-out will
   degrade to sequential. Traces to §Fan-out Opt-in Gate. (REQ-ORCH-024)
5. [implement] Worktree provisioning + dispatch (orchestrator-owned) — for each
   group, the orchestrator runs `git worktree add -b <branch> <path> <base>`,
   dispatches one implement subagent pinned to its worktree/branch carrying that
   group's chunks; each subagent is a **leaf** (runs `sdd-implement`, must not
   sub-dispatch); non-interactivity contract + central ID assignment apply;
   orchestrator awaits all returns before merging; the SKILL.md prose points to the
   task-1 reference for the full dispatch template. Traces to §Worktree
   Provisioning and Dispatch. (REQ-ORCH-022, REQ-ORCH-023)
6. [implement] Subagent git identity — fan-out subagents commit with inline
   `git -c user.email=<id> -c user.name=<name> commit ...`; orchestrator must
   **not** instruct subagents to write a shared `.git/config` (sandbox blocks it).
   Traces to §Worktree Provisioning and Dispatch step 4. (REQ-ORCH-027)
7. [implement] Sequential merge to main + teardown — after returns, merge each
   branch into `main` one at a time (`git merge --no-edit <branch>`), completing
   **all** merges before the implement-stage review; on each clean merge remove the
   worktree (`git worktree remove <path>`) and delete its branch (`git branch -d`),
   leaving only `main` for the review. Traces to §Sequential Merge to Main.
   (REQ-ORCH-025, REQ-ORCH-023/Q-REQ-G)
8. [implement] Merge-conflict handling — on non-zero `git merge` exit: optional
   best-effort auto-resolve (a clean auto-resolve = PASS, no abort); otherwise
   `git merge --abort` then **redo by re-derivation** in a fresh worktree
   re-branched from the updated `main` (`git worktree add -b <branch>-redo <path>
   main`, re-dispatch a leaf implement subagent, re-attempt merge) — never replay
   the stale patch; if it **still** conflicts after re-derivation, treat as a
   boundary-selection error and **fall back to sequential** for the affected
   groups (guaranteed termination); never corrupt already-merged work. Traces to
   §Merge-Conflict Handling and Q-IMPL-1. (REQ-ORCH-026)
9. [implement] Note the dispatch-concurrency uncertainty in the body — fan-out is
   correct whether dispatches run concurrently or serialized; only wall-clock
   speedup is at stake; do not claim a speedup guarantee (defer to the spike in
   Chunk 1). Traces to §Dispatch Concurrency [high-uncertainty]. (REQ-ORCH-028)

**Entry criteria**: None (first chunk).
**Exit criteria**: Fan-out procedure lives in `references/`; SKILL.md describes
active Design B fan-out covering REQ-ORCH-015/016/022..027 (pointing to the
reference for the bulky procedure) and notes REQ-ORCH-028; no other `sdd-*` skill
modified; SKILL.md under ~500 lines; chunk-close 4-check passes.

### Chunk 1: Concurrency spike, doc + requirements reconciliation, verification

**Goal**: The one open uncertainty is measured, the operator docs **and** the
governing requirement text no longer say "no fan-out", and all fan-out acceptance
criteria are walked with traceability filled.

**Tasks**:
10. [spike] Dispatch concurrency (budget: ~30 min) — measure whether a batch of
    ≥2 orchestrator-issued implement dispatches runs **truly concurrently** vs.
    issued-together-but-serialized (e.g. dispatch two trivial timestamped
    subagents and compare overlap). Record the finding in the spec's §Dispatch
    Concurrency / RS-006 Open Questions. **Correctness is unaffected either way** —
    this only decides whether a wall-clock speedup may be claimed. If serialized:
    ship Design B as-is and document "isolation + ordered integration, not
    necessarily parallel speedup on this harness." Traces to §Dispatch Concurrency
    [high-uncertainty]. (REQ-ORCH-028)
11. [implement] Reconcile OPERATOR DOCS **and the governing requirement text**
    (carried-forward finding m3 + review finding M1) — remove the "no fan-out" /
    "sequential only" language now that fan-out is active:
    - `skills/sdd-orchestrate/USAGE.md` §v1 limitations / deferred features — fan-out
      is now an opt-in implement-stage mode; describe it and its single-chain
      degrade-to-sequential behavior.
    - `README.org` — update the driver description so it no longer claims no fan-out.
    - `skills/sdd-orchestrate/SKILL.md` scope notes — any residual "fan-out
      deferred" wording.
    - `docs/requirements/functional/orchestration.md` — REQ-ORCH-020 and
      REQ-ORCH-021 still literally mandate that the operator docs cover "v1
      limitations (research-entry, sequential, no fan-out)", which now contradicts
      the active fan-out feature. Reword both so they no longer say "no fan-out":
      fan-out is active/opt-in at the implement stage only (sequential remains the
      default), and the remaining genuine v1 limitation is **research-entry-only /
      no non-research entry**. Keep REQ-ORCH-020/021 otherwise intact.
    Reflect the spike outcome (speedup claim or its absence). Traces to §User
    Documentation, §Sequential Execution and Implement-Stage Fan-out.
    (REQ-ORCH-020, REQ-ORCH-021, REQ-ORCH-015)
12. [verify] Fan-out acceptance-criteria walkthrough — walk the spec's fan-out
    criteria (the REQ-ORCH-015/016/022..028 acceptance checkboxes and the
    fan-out Manual verification bullets): construct/inspect a fan-out implement
    dispatch (leaf clause, worktree pin, inline `git -c` identity present); confirm
    the boundary rule parses `**Depends on**`/chunk prose and not milestone
    Entry/Exit; confirm opt-in + single-chain degrade notice; confirm
    sequential-merge-before-review, teardown, abort-and-redo-by-re-derivation, and
    sequential convergence fallback are all described; confirm no `sdd-implement`
    edit. Fill `docs/requirements/traceability.md` Implementation **and** Verified
    columns for REQ-ORCH-015/016/022..028. Traces to §Verification (Manual +
    Acceptance Criteria). (all fan-out REQ-ORCH)

**Entry criteria**: Chunk 0 complete (fan-out procedure already in `references/`,
SKILL.md body promoted).
**Exit criteria**: Concurrency spike finding recorded; operator docs (USAGE.md,
README.org, SKILL.md scope notes) **and** the governing requirement text
(REQ-ORCH-020/021 in `docs/requirements/functional/orchestration.md`) no longer say
"no fan-out"; all fan-out acceptance criteria pass with traceability
Implementation + Verified filled; `pre-commit run --all-files` clean; chunk-close
4-check passes.

## Replan Triggers

- **Spike shows serialized dispatch AND speedup is later required** — if task 10
  finds dispatches serialize and the operator subsequently deems wall-clock
  speedup a hard requirement, the isolation-only framing is insufficient → replan
  the fan-out dispatch mechanism (REQ-ORCH-028). (Default per spec: ship Design B
  as-is, correctness unaffected — no replan unless speedup becomes required.)
- **Redo-by-re-derivation fails to converge in practice** — if a re-derived
  chunk-group keeps conflicting even after re-branching from updated `main` and the
  sequential convergence fallback does not terminate cleanly in a real run →
  revisit §Merge-Conflict Handling / Q-IMPL-1 and the boundary rule (REQ-ORCH-026,
  REQ-ORCH-016).
- **Boundary rule unparseable in real plans** — if live plans cannot reliably
  express chunk-level `**Depends on**` / `Entry criteria: Chunk N` such that the
  orchestrator can derive groups, fan-out always degrades to sequential and the
  feature is inert → revisit REQ-ORCH-016 boundary derivation (may require a
  cross-spec change to plan-management.md, a Tier-3 escalation).
- **SKILL.md exceeds ~500 lines** after adding fan-out prose even with the
  procedure moved to `references/` → revisit REQ-ORCH-019 packaging (compress or
  split further).

## Assumptions

- **Reference file placement** (no explicit spec mandate): the fan-out procedure
  is added under `skills/sdd-orchestrate/references/` (extending
  `dispatch-templates.md` or a new `fan-out.md`), consistent with REQ-ORCH-019's
  intent to keep SKILL.md lean. Default chosen: extend `dispatch-templates.md`
  unless that pushes it past readability, in which case add `fan-out.md`.
- **Spike default outcome**: absent a measured speedup, the docs state fan-out
  provides isolation + ordered integration, not a guaranteed parallel speedup
  (the spec's stated fallback). No replan unless speedup is later required.

## Completed

- v2 artifact structure + RS-002 workflow + RS-003 v3 migration + RS-004 sdd-review
  (2026-04-28..2026-06-04; archived in plan-history).
- RS-005 sdd-orchestrate driver: SKILL.md (DISCUSS→KICKOFF→LOOP→DONE, dispatch
  contracts, gate protocol), `references/dispatch-templates.md`, USAGE.md, README —
  v1 research-entry/sequential driver, all chunks closed (2026-06-04, 3 chunks /
  20 tasks; archived 2026-06-04-rs005-orchestrate-complete.md).

## Risks

- **End-to-end fan-out testability**: a real fan-out run dispatches multiple
  implement subagents, provisions worktrees, and forces merge conflicts — expensive
  and stateful to execute fully. Mitigation: verify primarily by dispatch-prompt /
  procedure inspection (task 12) against the spec's Manual bullets; reserve live
  execution for the budgeted spike (task 10) only.
- **Boundary parsing fragility**: deriving independent chunk-groups from prose
  `Entry criteria: Chunk N complete` (vs. the canonical `**Depends on**` field) is
  heuristic. Mitigation: spec already mandates degrade-to-sequential when deps are
  unparseable — the orchestrator never guesses; documented as a replan trigger.
- **Conflict-redo correctness is partly spec-design, not RS-006-proven**: RS-006
  verified only `git merge --abort`, not the full redo-by-re-derivation (Q-IMPL-1).
  Mitigation: the sequential convergence fallback bounds it and guarantees
  termination; flagged as a replan trigger if it fails in practice.

## Archive

Full plan history:
- [2026-04-28-pre-v2-migration.md](plan-history/2026-04-28-pre-v2-migration.md)
- [2026-05-25-pre-rs002-rewrite.md](plan-history/2026-05-25-pre-rs002-rewrite.md)
- [2026-05-25-rs002-complete.md](plan-history/2026-05-25-rs002-complete.md)
- [2026-05-25-rs003-complete.md](plan-history/2026-05-25-rs003-complete.md)
- [2026-06-04-rs004-complete.md](plan-history/2026-06-04-rs004-complete.md)
- [2026-06-04-rs005-orchestrate-complete.md](plan-history/2026-06-04-rs005-orchestrate-complete.md)
- [2026-06-04-pre-fanout-reseq.md](plan-history/2026-06-04-pre-fanout-reseq.md)
