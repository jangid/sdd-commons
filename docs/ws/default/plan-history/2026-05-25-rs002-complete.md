# Implementation Plan: SDD Workflow Improvements (RS-002)

## Overview

Update 4 existing SDD skills (sdd-implement, sdd-specs, sdd-plan, sdd-replan)
and touch 1 more (sdd-requirements) to implement the RS-002 workflow
improvements: chunk-close review, Q-IMPL deviation protocol, milestone plan
support, cross-spec consistency, and related staleness enhancements.
Deliverables are SKILL.md files. Single-milestone scope — no per-milestone
plan structure for this project's own plan (REQ-MPLAN-004 fallback).

## Conventions

- **Tests alongside implementation**: skill changes are verified by reading
  the updated SKILL.md against the spec's acceptance criteria. No code tests
  — deliverables are Markdown skill definitions.
- **Task types**: [implement] produces SKILL.md changes, [verify] validates
  behavior by invoking the skill against a test scenario.
- **Chunk headers**: `### Chunk N: <name>` per REQ-CHKC-008.
- **Traceability**: each task's `traces to` reference identifies the spec.
  After completing each task, update `docs/requirements/traceability.md`
  Implementation column.

## Chunks

### Chunk 0: sdd-implement foundational additions

**Goal**: Add three self-contained sections to `sdd-implement` SKILL.md
that don't restructure existing content.

**Tasks**:
1. [implement] Add CLAUDE.md convention reading as first context loading
   step — traces to skill-updates.md §CLAUDE.md Convention Reading
   (REQ-SKILL-012)
2. [implement] Add spike code separation rule for [spike] tasks — traces to
   skill-updates.md §Spike Code Separation (REQ-SKILL-011)
3. [implement] Add Q-IMPL three-tier deviation protocol section with tier
   classification, entry format, global numbering, and Tier 3 escalation —
   traces to deviation-protocol.md (REQ-QIMPL-001, REQ-QIMPL-002,
   REQ-QIMPL-003), skill-updates.md §Q-IMPL Deviation Protocol
   (REQ-SKILL-010)

**Entry criteria**: None (first chunk).
**Exit criteria**: sdd-implement SKILL.md contains all three additions.
Tier descriptions match spec. Q-IMPL entry format includes all required
fields.

### Chunk 1: sdd-implement chunk close review

**Goal**: Integrate the 4-check structured chunk close checklist into
`sdd-implement`, distinguishing chunk-level from milestone-level
checkpoints.

**Tasks**:
1. [implement] Rename existing "Step 4: Milestone Checkpoints" to
   distinguish chunk close review (per-chunk, 4 checks) from milestone
   checkpoints (delivery approval). Add chunk definition and
   `### Chunk N:` detection pattern — traces to chunk-close-review.md
   §Chunk Definition, §Integration with sdd-implement (REQ-CHKC-001,
   REQ-CHKC-008), skill-updates.md §Chunk Close Checklist (REQ-SKILL-009)
2. [implement] Add Check 1 (spec-implementation type alignment) and Check 2
   (traceability matrix update) as blocking checks — traces to
   chunk-close-review.md §Check 1, §Check 2 (REQ-CHKC-002, REQ-CHKC-003)
3. [implement] Add Check 3 (test coverage per spec) and Check 4 (Q-IMPL
   audit) as advisory checks — traces to chunk-close-review.md §Check 3,
   §Check 4 (REQ-CHKC-004, REQ-CHKC-005)
4. [implement] Add tiered enforcement rules and chunk close report format —
   traces to chunk-close-review.md §Tiered Enforcement, §Chunk Close Report
   (REQ-CHKC-006, REQ-CHKC-007)
5. [implement] Add Q-IMPL discovery on task start (advisory read of existing
   entries) — traces to deviation-protocol.md §Discovery on Task Start
   (REQ-QIMPL-003)

**Entry criteria**: Chunk 0 complete (Q-IMPL protocol exists for Check 4
cross-reference).
**Exit criteria**: sdd-implement SKILL.md contains chunk close checklist
with all 4 checks, tiered enforcement, report format, and chunk detection.
Check 4 references Q-IMPL protocol from Chunk 0.

### Chunk 2: sdd-specs cross-spec consistency

**Goal**: Add the cross-spec consistency reading pass to `sdd-specs`.

**Tasks**:
1. [implement] Add cross-spec reading pass as new sub-step between Step 4
   (review cycle) and Step 5 (coverage check). Include: type extraction from
   code blocks, type-to-spec map building, reference scanning, validation
   checks, flag-only findings — traces to cross-spec-consistency.md
   (REQ-XSPEC-001, REQ-XSPEC-002), skill-updates.md §Cross-Spec Consistency
   (REQ-SKILL-013)

**Entry criteria**: None (independent of sdd-implement changes).
**Exit criteria**: sdd-specs SKILL.md contains cross-spec pass positioned
after individual review, before coverage check. Findings described as
flag-only.

### Chunk 3: Milestone plan and staleness support

**Goal**: Add per-milestone plan support to sdd-plan, sdd-replan, and
sdd-implement. Add research-to-requirements staleness to sdd-requirements.
Align chunk vocabulary in sdd-plan's plan format instructions.

**Tasks**:
1. [implement] Update sdd-plan: add per-milestone file creation
   (`docs/plan-{id}.md`), index format for `docs/plan.md` when multiple
   milestones exist, `milestone:` frontmatter, single-milestone fallback.
   Update plan format to use `### Chunk N:` headers instead of milestone
   headers for work units — traces to milestone-plans.md §Per-Milestone
   File Layout, §Single-Milestone Fallback (REQ-MPLAN-001, REQ-MPLAN-002,
   REQ-MPLAN-004), plan-management.md §Active Plan Structure,
   skill-updates.md §Milestone Plan Support in sdd-plan (REQ-SKILL-014)
2. [implement] Update sdd-plan and sdd-implement: add milestone-scoped
   staleness detection (compare only against requirements/specs traced by
   the milestone's tasks) — traces to milestone-plans.md
   §Milestone-Scoped Staleness (REQ-STALE-003), skill-updates.md
   §Milestone-Scoped Staleness (REQ-SKILL-016)
3. [implement] Update sdd-replan: add per-milestone archival (archive
   correct milestone's plan file), cross-milestone replan handling, index
   table updates — traces to milestone-plans.md §Interaction with
   sdd-replan, skill-updates.md §Milestone Plan Support in sdd-replan
   (REQ-SKILL-015)
4. [implement] Update sdd-plan: add milestone lifecycle management
   (planned → active → complete → archived) and archive naming
   `{date}-{milestone-id}-complete.md` — traces to milestone-plans.md
   §Milestone Lifecycle (REQ-MPLAN-003)
5. [implement] Update sdd-requirements: add research-to-requirements
   staleness check on entry (compare newest research date against
   `index.md` last_updated, advisory) — traces to
   requirements-artifacts.md §Research-to-requirements staleness,
   skill-updates.md §Research-to-Requirements Staleness (REQ-STALE-002)

**Entry criteria**: None (independent of Chunks 0-2, but sequential within
this chunk).
**Exit criteria**: sdd-plan creates per-milestone files when appropriate
and falls back to single-file. sdd-replan handles per-milestone archival.
sdd-implement uses milestone-scoped staleness. sdd-requirements detects
research staleness. Plan format uses `### Chunk N:` headers.

### Chunk 4: Verification

**Goal**: End-to-end verification of all acceptance criteria across all
10 specs.

**Tasks**:
1. [verify] Read each updated SKILL.md against its spec's acceptance
   criteria. Verify every checkbox item is addressed in the skill
   instructions — traces to chunk-close-review.md, deviation-protocol.md,
   milestone-plans.md, cross-spec-consistency.md, skill-updates.md,
   plan-management.md, overview.md
2. [verify] Cross-skill consistency check: verify chunk vocabulary is
   consistent across sdd-plan, sdd-implement, sdd-replan (all use
   `### Chunk N:` for work units, "milestone" only for delivery groupings)
3. [verify] Fill traceability matrix: update Test and Implementation
   columns for all REQ-CHKC-*, REQ-QIMPL-*, REQ-MPLAN-*, REQ-XSPEC-*,
   REQ-STALE-003, REQ-SKILL-009..016, REQ-STALE-002 — traces to
   requirements-artifacts.md §Traceability Matrix

**Entry criteria**: Chunks 0-3 complete.
**Exit criteria**: All acceptance criteria verified. Traceability matrix
Implementation column filled for all new requirements. No cross-skill
vocabulary inconsistencies.

## Replan Triggers

- If sdd-implement SKILL.md exceeds ~500 lines after Chunk 0+1 additions →
  split skill into base + chunk-close appendix or compress existing content
- If milestone plan support in Chunk 3 conflicts with existing plan archival
  logic → revisit plan-management.md and milestone-plans.md composition
- If cross-spec consistency pass in Chunk 2 requires changes to the spec
  format (e.g., standardized type block markers) → revisit specs before
  proceeding

## Completed

- v2 artifact structure: All 8 skills updated for v2 paths (2026-04-28,
  11 tasks)

## Risks

- **sdd-implement size**: After adding chunk-close (4 checks + report +
  tiered enforcement), Q-IMPL (3 tiers + format + numbering), spike
  separation, and CLAUDE.md reading, the skill may exceed 500 lines.
  Mitigation: reference spec files for format details rather than
  duplicating, keep instructions concise.
- **Milestone plan complexity**: Per-milestone support touches 3 skills
  (sdd-plan, sdd-replan, sdd-implement). Changes must be consistent.
  Mitigation: do all three in one chunk, verify vocabulary consistency in
  Chunk 4.

## Archive

Full plan history:
- [2026-04-28-pre-v2-migration.md](plan-history/2026-04-28-pre-v2-migration.md)
- [2026-05-25-pre-rs002-rewrite.md](plan-history/2026-05-25-pre-rs002-rewrite.md)
