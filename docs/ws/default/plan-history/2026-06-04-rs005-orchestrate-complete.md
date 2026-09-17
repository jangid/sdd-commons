# Implementation Plan: sdd-orchestrate Driver (RS-005)

## Overview

Create `skills/sdd-orchestrate/SKILL.md` per `docs/spec/orchestration.md`: a
**driver** skill that runs the existing nine `sdd-*` skills as a single-operator
loop (DISCUSS → KICKOFF → LOOP → DONE) with per-stage external review by isolated
subagents and a human gate after every stage. The bulky dispatch prompt templates
live in `skills/sdd-orchestrate/references/dispatch-templates.md` to keep the body
under the ~500-line guideline. v1 is research-entry and sequential — no
mid-pipeline entry, no parallel fan-out. Deliverable is Markdown skill
definitions plus a one-line documentation update to the project's SDD section.

## Conventions

- **Task types**: [implement] produces SKILL.md / references changes,
  [verify] validates against spec acceptance criteria. No [spike] tasks — the
  one `[high-uncertainty]` section (subagent nesting) is v1-deferred (see Risks).
- **Chunk headers**: `### Chunk N: <name>` per v3 conventions.
- **Traceability**: each task's `(REQ-…)` reference identifies the requirement;
  the spec section is named inline. After each task, update
  `docs/requirements/traceability.md` Implementation column.
- **Chunk close**: 4-check review per chunk-close-review.md at each chunk
  boundary.

## Chunks

### Chunk 0: Driver skill body — phases and dispatch contracts

**Goal**: `skills/sdd-orchestrate/SKILL.md` exists and implements the full driver
flow and both dispatch contracts in prose, modifying no other `sdd-*` skill.

**Tasks**:
1. [implement] Skill scaffolding — frontmatter (`name: sdd-orchestrate`,
   `description` stating when to use vs skip), opening context establishing the
   driver role (composes the nine, never reimplements; relays stage phase
   detection). Traces to orchestration.md §Driver Positioning. (REQ-ORCH-001)
2. [implement] Phase overview — DISCUSS → KICKOFF → LOOP → DONE in order, with the
   LOOP stage list [research, requirements, specs, plan, implement, verify].
   Traces to §Driver Phases. (REQ-ORCH-002)
3. [implement] DISCUSS phase — reuse the brainstorming process to converge on
   scope and open questions before any kickoff. Traces to §Driver Phases/DISCUSS.
   (REQ-ORCH-003)
4. [implement] KICKOFF phase — write `docs/handoff/kickoff.md`; v1 emits a
   research kickoff and starts the loop at research; state the only-new-artifact
   and git-tracked rules; non-research entry explicitly out of scope.
   Traces to §Kickoff Artifact. (REQ-ORCH-004, REQ-ORCH-005)
5. [implement] Per-stage dispatch model — two separate subagent dispatches
   (pipeline, then review) per stage; pipeline runs to disk before the review
   dispatch is built. Traces to §Per-Stage Dispatch Model. (REQ-ORCH-006)
6. [implement] Pipeline subagent contract (body) — non-interactivity clause,
   front-loaded decisions, central ID assignment, absolute cwd, labeled-content
   fallback. Traces to §Pipeline Subagent Contract. (REQ-ORCH-007, REQ-ORCH-008)
7. [implement] Review subagent contract (body) — MUST-carry (paths only) /
   MUST-NOT-carry lists; research-stage upstream-omission exception; later stages
   supply upstream. Traces to §Review Subagent Contract.
   (REQ-ORCH-009, REQ-ORCH-010)
8. [implement] Gate protocol + ephemeral reviews — proceed │ loop-back-to-fix │
   stop with no auto-advance; fix loop re-dispatches pipeline with findings +
   paths only; replan surfaces as a gate event; reject-with-no-findings pauses;
   verdicts never written to disk / no `docs/reviews/`. Traces to §Gate Protocol,
   §Ephemeral Reviews. (REQ-ORCH-011, 012, 013, 017, 018)
9. [implement] Resume + execution model — resume via existing phase detection,
   no marker file, no authoritative loop log; v1 sequential in main workspace;
   document the deferred fan-out boundary rule (independent plan chunks, one
   worktree per group, sequential merge to main). Traces to §Resume, §Sequential
   Execution and Deferred Fan-out. (REQ-ORCH-014, 015, 016)

**Entry criteria**: None (first chunk).
**Exit criteria**: SKILL.md covers REQ-ORCH-001..018 and documents 016; no other
`sdd-*` skill modified; chunk-close 4-check passes.

### Chunk 1: Templates, packaging, and verification

**Goal**: Dispatch templates extracted to `references/`, skill within size
budget, documentation consistent, and all acceptance criteria verified.

**Tasks**:
10. [implement] Create `skills/sdd-orchestrate/references/dispatch-templates.md`
    with the pipeline and review prompt templates (adapt the RS-005 prototype
    templates at `docs/research/RS-005-sdd-orchestrate-feasibility/prototype/dispatch-templates.md`);
    the SKILL.md body references this file rather than inlining full templates.
    Traces to §Packaging. (REQ-ORCH-019, supports REQ-ORCH-007, REQ-ORCH-009)
11. [implement] Update the project SDD documentation (`CLAUDE.md` §SDD) to
    introduce `sdd-orchestrate` as the cross-cutting driver over the nine phase
    skills. (Project doc only — not an `sdd-*` skill edit.) (REQ-ORCH-001)
12. [verify] Packaging check — `SKILL.md` is a single file under ~500 lines and
    the two dispatch templates live in `references/`. Traces to §Verification.
    (REQ-ORCH-019)
13. [verify] Isolation inspection — from the templates, construct (a) a
    non-research review dispatch and confirm only permitted paths-only inputs are
    present and all prohibited inputs are absent; (b) a research-stage review
    dispatch and confirm the upstream path is omitted; (c) a pipeline dispatch and
    confirm the non-interactivity clause, front-loaded decisions, pinned IDs, and
    absolute cwd are present. Traces to §Verification Manual.
    (REQ-ORCH-007, 009, 010)
14. [verify] Acceptance-criteria walkthrough — walk all 20 acceptance criteria in
    orchestration.md with evidence; fill the Implementation column in
    `traceability.md` for REQ-ORCH-001..019. Traces to §Verification Acceptance
    Criteria. (all REQ-ORCH)

**Entry criteria**: Chunk 0 complete.
**Exit criteria**: All 20 acceptance criteria pass; traceability Implementation
column filled; `pre-commit run --all-files` clean; chunk-close 4-check passes.

### Chunk 2: Validation pass and operator documentation

**Goal**: Close the "never run live" gap, apply review findings, and ship
extensive operator documentation + README.

**Tasks**:
15. [verify] Live smoke test — dispatch a real pipeline subagent using the
    actual `references/` PIPELINE template; confirm the skill loads, the
    non-interactivity clause works, and the labeled-content fallback handles a
    blocked write. (REQ-ORCH-007)
16. [verify] D7 dogfood — dispatch a fresh-session review subagent (the REVIEW
    template) over the implementation; record the verdict. (REQ-ORCH-009)
17. [implement] Apply review finding M1 — add success-criterion, budget, and
    deliverable-contract slots to the PIPELINE template; add a precedence note
    and the validated blocked-write/fallback guidance. (REQ-ORCH-007)
18. [implement] Install the skill link `~/.claude/skills/sdd-orchestrate` and
    write the operator guide `skills/sdd-orchestrate/USAGE.md`. (REQ-ORCH-020)
19. [implement] Update `README.org` — introduce the driver/suite, the
    `~/.claude/skills/` symlink convention, and link the operator guide.
    (REQ-ORCH-021)
20. [verify] Re-verify — 23 acceptance criteria, traceability complete for
    REQ-ORCH-001..021, structural gates green. (all REQ-ORCH)

**Entry criteria**: Chunk 1 complete.
**Exit criteria**: Smoke + dogfood recorded; M1 applied; USAGE.md + README
shipped; REQ-ORCH-020/021 traced and verified.

## Replan Triggers

- `skills/sdd-orchestrate/SKILL.md` exceeds ~500 lines even after moving the
  templates to `references/` → revisit REQ-ORCH-019: compress, or split the
  kickoff-writer into a sub-skill (Tier 3 — would reopen the packaging decision).
- During implementation, some stage's `sdd-*` skill proves it cannot run under the
  non-interactivity contract (requires an interactive decision that cannot be
  front-loaded) → surface to the operator and revisit §Pipeline Subagent Contract
  (REQ-ORCH-007).
- The paths-only review dispatch proves insufficient for a stage's `sdd-review`
  checklist (reviewer needs an input not derivable from disk) → revisit
  REQ-ORCH-009/010 isolation contract.

## Completed

- v2 artifact structure: 8 skills updated for v2 paths (2026-04-28, 11 tasks)
- RS-002 workflow improvements: chunk-close, Q-IMPL, per-milestone, cross-spec
  consistency, staleness enhancements (2026-05-25, 5 chunks)
- RS-003 v3 migration: sdd-migrate v2→v3, v1→v3 composition, version bump
  (2026-05-25, 9 tasks)
- RS-004 sdd-review skill: external review skill + sdd-verify fourth-layer update
  (2026-06-04, 1 chunk / 8 tasks)

## Risks

- **Deferred subagent nesting** (orchestration.md §Subagent nesting,
  high-uncertainty): the future fan-out implies a subagent spawning subagents,
  unverified by RS-005. **Not in v1 scope** (v1 is sequential, REQ-ORCH-015), so
  no mitigation is required now; a nested-dispatch spike precedes any future
  fan-out feature (REQ-ORCH-016). Fallback: orchestrator owns fan-out, keeping
  nesting one level deep.
- **End-to-end testability**: a full DISCUSS→DONE run exercises six real stages
  and is expensive to execute as a test. Mitigation: verify by dispatch-prompt
  inspection (task 13) plus at most a single live stage smoke test, rather than a
  full pipeline run.
- **Skill size creep**: 19 requirements in one body risk breaching the size
  budget. Mitigation: templates to `references/` (task 10); reference the spec for
  rationale rather than duplicating it.

## Archive

Full plan history:
- [2026-04-28-pre-v2-migration.md](plan-history/2026-04-28-pre-v2-migration.md)
- [2026-05-25-pre-rs002-rewrite.md](plan-history/2026-05-25-pre-rs002-rewrite.md)
- [2026-05-25-rs002-complete.md](plan-history/2026-05-25-rs002-complete.md)
- [2026-05-25-rs003-complete.md](plan-history/2026-05-25-rs003-complete.md)
- [2026-06-04-rs004-complete.md](plan-history/2026-06-04-rs004-complete.md)
