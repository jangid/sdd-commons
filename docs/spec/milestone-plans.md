---
status: Approved
last_updated: 2026-09-18
requires:
  - REQ-MPLAN-001
  - REQ-REDB-HARNESSP3-004
  - REQ-MPLAN-002
  - REQ-MPLAN-003
  - REQ-MPLAN-004
  - REQ-STALE-003
  - REQ-SKILL-014
  - REQ-SKILL-015
  - REQ-SKILL-016
---

# Milestone Plans

## Context

SDD skills assume a single `docs/plan.md`. Projects with multiple milestones
(e.g., the rubric project's M1-M4) see this file grow unboundedly as
milestones accumulate. The `## Completed` section dwarfs active work, and
staleness detection fires on requirement changes that are irrelevant to the
current milestone.

This spec extends the plan management model (see plan-management.md) with
per-milestone plan files and milestone-scoped staleness.

## Design

### Per-Milestone File Layout

```
docs/
  plan.md                # Lightweight index — lists milestones, status
  plan-m1.md             # Per-milestone plan file
  plan-m2.md             # Per-milestone plan file
  plan-history/
    {date}-m1-complete.md  # Archived milestone plan
```

`docs/plan.md` becomes an index when multiple milestones exist:

```markdown
---
last_updated: YYYY-MM-DD
---

# Implementation Plan: [Project Name]

## Overview
One paragraph: project scope and approach.

## Milestones

| ID | Name | Plan File | Status |
|----|------|-----------|--------|
| M1 | Project skeleton | [archived](plan-history/2026-04-20-m1-complete.md) | Complete |
| M2 | Core models | plan-m2.md | Active |
| M3 | Integration | plan-m3.md | Planned |
```

**Why an index rather than a master plan**: The index is ~20 lines regardless
of milestone count. Each milestone plan is self-contained and can be loaded
independently, keeping AI context focused.

### Milestone Plan File Format

Each per-milestone file follows the existing plan format with added
`milestone:` frontmatter:

```markdown
---
milestone: M2
last_updated: YYYY-MM-DD
status: active
---

# Plan: M2 — Core Models

## Goal
What this milestone delivers.

## Chunks

### Chunk 0: Data layer
**Goal**: ...
**Tasks**:
1. [implement] ... — traces to spec.md
2. [verify] ... — traces to spec.md
**Entry criteria**: M1 complete.
**Exit criteria**: ...

### Chunk 1: Business logic
...

## Replan Triggers
- [Condition] → [response]

## Risks
- [Risk]: [impact and mitigation]

## Post-cycle Fixes          # optional, orchestrator-owned, outside the task list
- R3 — <what was broken, what was changed, path> (<sha>)
```

[Amended 2026-09-18, REQ-REDB-HARNESSP3-004] `## Post-cycle Fixes` is part of
the plan-structure contract: **optional**, **orchestrator-owned**, and
**outside the task list**. `sdd-plan` / `sdd-replan` must carry it across a plan
rewrite rather than stripping it, and `sdd-implement` must not read its lines as
tasks. It records a verify-stage `RED_BREAK` fix that belongs to no open chunk,
one line per fix; the owning contract is
`docs/spec/adversarial-verify.md` §`## Post-cycle Fixes` in the Active Plan.

**Required frontmatter**:
- `milestone:` — the milestone ID (e.g., `M2`), matching the index table
- `last_updated:` — ISO date, used for staleness detection
- `status:` — one of `planned`, `active`, `complete`, `archived`

### Milestone Lifecycle

```
planned → active → complete → archived
```

1. **Planned**: `sdd-plan` creates the file with `status: planned`. Tasks
   are defined but work hasn't started.
2. **Active**: `sdd-implement` sets `status: active` when work begins on
   the milestone's first task.
3. **Complete**: `sdd-implement` (or `sdd-verify`) sets `status: complete`
   when all tasks are done and verified.
4. **Archived**: The completed plan is moved to
   `docs/plan-history/{date}-{milestone-id}-complete.md`. The index table
   is updated with the archive path.

**Archival follows the same pattern as plan-management.md**: the archive
file is a complete snapshot. The naming convention extends the existing
`{date}-{reason}.md` pattern with the milestone ID as part of the reason
(e.g., `2026-04-20-m1-complete.md`).

### Single-Milestone Fallback

For projects with one milestone or no explicit milestone structure,
`docs/plan.md` remains the single plan file. No `milestone:` frontmatter
is required. The per-milestone convention activates only when:

- The plan or specs explicitly define multiple milestones, OR
- `sdd-plan` detects that the project scope warrants splitting

**Why an explicit activation threshold**: Forcing milestone structure on
small projects adds overhead without benefit. A single-file plan is
perfectly adequate for projects with one delivery scope.

### Milestone-Scoped Staleness (REQ-STALE-003)

When a project uses per-milestone plan files, staleness detection for each
plan file must compare only against requirements and specs relevant to that
milestone.

**Process**:
1. Read the milestone plan's tasks
2. For each task, follow its prose `traces to` reference to identify the
   spec file
3. Read each spec file's `requires:` frontmatter to collect requirement IDs
4. Compare the milestone plan's `last_updated` against:
   - The `last_updated` of each referenced spec
   - The `last_updated` of `docs/requirements/index.md` — but only if any
     of the collected requirement IDs belong to a category file that was
     updated more recently than the plan

**Result**: A requirement change in `functional/auth.md` does not trigger
staleness for `plan-m2.md` if M2's tasks don't trace to any spec that
requires `REQ-AUTH-*` IDs.

**Why not just compare against `index.md`'s `last_updated`**: The index
date bumps whenever any category file changes. In a multi-milestone project,
M1 requirements might be updated during M2 planning. Without scoping,
every milestone plan becomes "stale" on every requirement touch — defeating
the purpose of per-milestone files.

**Fallback**: When using the single-file plan (no `milestone:` frontmatter),
staleness detection continues to compare against `index.md`'s `last_updated`
directly, as in the current model.

### Interaction with sdd-plan

`sdd-plan` must:
1. Detect whether the project uses single-file or per-milestone plans
2. If per-milestone: create/update the relevant milestone's plan file and
   the index
3. When creating a new milestone plan, assign the next milestone ID and
   add it to the index table

### Interaction with sdd-replan

`sdd-replan` must:
1. Identify which milestone's plan is affected by the replan trigger
2. Archive and revise only that milestone's plan file
3. Update the index table if milestone status changes
4. Cross-milestone replans (e.g., moving tasks from M2 to M3) must update
   both milestone files and the index

### Interaction with sdd-implement

`sdd-implement` must:
1. Read the active milestone's plan file (identified via the index or by
   `status: active` frontmatter)
2. Apply milestone-scoped staleness when checking for stale plans
3. Update the milestone plan's `last_updated` when completing tasks

## Verification

### Automated
- Verify `sdd-plan` SKILL.md supports per-milestone file creation
- Verify `sdd-replan` SKILL.md handles per-milestone archival
- Verify milestone plan files include `milestone:` frontmatter
- Verify `docs/plan.md` index format is documented

### Manual
- Create a multi-milestone project; verify per-milestone files are created
- Complete a milestone; verify archival to plan-history with milestone ID
- Change a requirement unrelated to active milestone; verify no staleness
- Change a requirement traced by active milestone; verify staleness detected
- Use a single-milestone project; verify single-file behavior preserved

### Acceptance Criteria
- [ ] Per-milestone plan files at `docs/plan-{id}.md` (REQ-MPLAN-001)
- [ ] `docs/plan.md` serves as lightweight index (REQ-MPLAN-001)
- [ ] Milestone plan files include `milestone:` frontmatter (REQ-MPLAN-002)
- [ ] The plan file format lists `## Post-cycle Fixes` as optional, orchestrator-owned and outside the task list; a plan rewrite by `sdd-plan` / `sdd-replan` preserves it and `sdd-implement` does not read it as tasks (REQ-REDB-HARNESSP3-004)
- [ ] Index lists milestones with status and plan file path (REQ-MPLAN-002)
- [ ] Completed milestones archived to plan-history (REQ-MPLAN-003)
- [ ] Archive naming uses `{date}-{milestone-id}-complete.md` (REQ-MPLAN-003)
- [ ] Index updated on milestone completion (REQ-MPLAN-003)
- [ ] Single-milestone projects use `docs/plan.md` directly (REQ-MPLAN-004)
- [ ] No `milestone:` frontmatter required for single-milestone (REQ-MPLAN-004)
- [ ] Staleness scoped to milestone's traced requirements (REQ-STALE-003)
- [ ] Unrelated requirement changes don't trigger staleness (REQ-STALE-003)
- [ ] `sdd-plan` creates per-milestone files and index (REQ-SKILL-014)
- [ ] `sdd-replan` archives/revises correct milestone plan (REQ-SKILL-015)
- [ ] `sdd-implement` uses milestone-scoped staleness (REQ-SKILL-016)

## Implementation Questions

### Q-IMPL-002: Per-milestone activation threshold heuristics
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Single-Milestone Fallback — "sdd-plan detects that the project scope warrants splitting"
**Decision**: Added concrete heuristics in the skill instruction: activate per-milestone structure when chunk count exceeds ~10, plan would exceed ~300 lines, or work spans multiple distinct delivery scopes.
**Rationale**: The spec intentionally leaves the threshold to judgment. Concrete heuristics give the operator a starting point without being rigid (the "~" prefix signals approximation). Without numbers, different sessions would apply inconsistent thresholds.
