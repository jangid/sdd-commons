---
status: Approved
last_updated: 2026-05-25
requires:
  - REQ-MIG-001
  - REQ-MIG-002
  - REQ-MIG-003
  - REQ-MIG-004
  - REQ-MIG-005
  - REQ-MIG-006
  - REQ-MIG-007
  - REQ-MIG-008
  - REQ-MIG-009
  - REQ-MIG-010
  - REQ-MIG-011
  - REQ-MIG-012
  - REQ-MIG-013
  - REQ-MIG-014
  - REQ-MIG-015
  - REQ-CFG-001
  - REQ-SKILL-017
  - REQ-COMPAT-002
---

# Migration (migrate)

## Context

The SDD artifact structure is changing from v1 (flat files, monolithic
requirements, accumulating plans) to v2 (ID-prefixed research directories,
split requirements with versioned index, lean plans with archival). Existing
projects using SDD skills need a migration path that handles mid-cycle
projects safely.

This spec covers two migration procedures: v1→v2 (REQ-MIG-001..008, RS-001)
and v2→v3 (REQ-MIG-009..015, RS-003). They share the same `sdd-migrate` skill
and are co-located in one file so operators reading "how do I migrate" see all
paths in one place.

## Design

### Skill Identity

- **Skill name**: `sdd-migrate`
- **Location**: `skills/sdd-migrate/SKILL.md`
- **Purpose**: One-time migration between SDD artifact structure versions
- **Invocation**: User runs `/sdd-migrate` or the skill is suggested by other
  skills when they detect an old format

### Version Detection

On entry, the skill reads `docs/.sdd-version`:

| File state | Detected version | Action |
|------------|-----------------|--------|
| Missing | v1 | Offer migration to v3 (v1→v2 then v2→v3) |
| Contains `2` | v2 | Offer migration to v3 |
| Contains `3` | v3 | Inform user: already current, exit |
| Contains unknown value | Unknown | Warn and exit |

If no `docs/` directory exists at all, there's nothing to migrate — inform
the user and exit.

### Migration Pipeline

The migration runs in three independent steps. Each step is idempotent — it
can be re-run safely if interrupted.

```
Step 1: Research    (docs/research/*.md → docs/research/RS-NNN-{topic}/)
Step 2: Requirements (docs/requirements.md → docs/requirements/{category}/)
Step 3: Plan        (docs/plan.md → docs/plan-history/ + lean plan.md)
```

**Independence**: Each step checks its own preconditions. If research is
already migrated but requirements aren't, Step 2 runs without Step 1. This
supports partial migrations and resumption after interruption.

### Step 1: Research Migration

**Precondition**: `docs/research/*.md` files exist at the root level (not
inside `RS-NNN-*` directories).

**Process**:
1. Collect all `docs/research/*.md` files (excluding `index.md` if it exists).
2. Sort by file modification date (oldest first).
3. For each file, assign the next `RS-NNN` number starting from 001.
4. Create `docs/research/RS-NNN-{topic}/` directory where `{topic}` is derived
   from the original filename (kebab-case).
5. Move the file to `docs/research/RS-NNN-{topic}/findings.md`.
6. Add `id: RS-NNN` to the file's frontmatter if not already present.
7. After all files are moved, generate `docs/research/index.md`.

**Idempotency**: If `RS-NNN-*` directories already exist alongside flat files,
only migrate the flat files. Existing directories are not touched.

### Step 2: Requirements Migration

**Precondition**: `docs/requirements.md` exists (monolithic v1 format).

**Process**:
1. Read `docs/requirements.md` fully.
2. Parse all requirement IDs and their sections.
3. Group requirements by category:
   - `REQ-F-*` → `functional/` (further grouped by domain if detectable from
     section headings)
   - `REQ-NF-*` → `non-functional/`
   - `REQ-I-*` → `integration/`
   - `REQ-C-*` → `configuration/`
4. For each group, determine the domain prefix:
   - Use the section heading as a hint (e.g., "### Authentication" → `AUTH`).
   - If ambiguous, prompt the user to choose a prefix.
5. Create category files with proper frontmatter.
6. Remap IDs: `REQ-F-001` → `REQ-{DOMAIN}-001` (renumber within each domain
   starting from 001).
7. Perform in-place replacement of old IDs across all files in `docs/`:
   - `docs/spec/*.md` (frontmatter `requires` lists and prose references)
   - `docs/plan.md` (task traces)
   - `docs/verification.md` (acceptance criteria tables)
8. Create `docs/requirements/index.md` with `version: 2.0`.
9. Create `docs/requirements/traceability.md` seeded from spec `requires`
   fields (if specs exist).
10. Verify all replacements succeeded (grep for any remaining `REQ-F-*`,
    `REQ-NF-*`, `REQ-I-*`, `REQ-C-*` patterns in `docs/`).
11. Delete `docs/requirements.md`.

**ID Remapping Safety**:
- Before deleting the old file, verify every old ID has a corresponding new ID.
- Log the full mapping (old → new) to stdout so the user can review.
- Old IDs are unique strings (e.g., `REQ-F-001`) that won't match non-ID text,
  making in-place replacement safe.

**Domain prefix inference**: The skill inspects category headings in the v1
file (e.g., `### Authentication`, `### Data Pipeline`). It proposes a short
uppercase prefix for each (e.g., `AUTH`, `DATAPIPE`). The user confirms or
overrides before the remap happens.

### Step 3: Plan Migration

**Precondition**: `docs/plan.md` exists.

**Process**:
1. Read `docs/plan.md`.
2. Create `docs/plan-history/` directory.
3. Copy the full plan to `docs/plan-history/{date}-pre-v2-migration.md`.
4. Parse the plan to identify:
   - Completed milestones (tasks all marked done)
   - Active/future milestones (tasks pending or in-progress)
   - Changelog sections
   - `[removed: ...]` markers
5. Rewrite `docs/plan.md`:
   - Keep: Overview, Conventions, active/future milestones, Replan Triggers,
     Risks.
   - Summarize: completed milestones → one line each in `## Completed`.
   - Remove: `## Plan Changelog`, `[removed: ...]` markers.
6. Verify the archived file is identical to the original before modifying.

### Finalization

After all steps complete:
1. Write `docs/.sdd-version` containing `2`.
2. Present a summary to the user:
   - Research: N files migrated to RS-NNN directories
   - Requirements: N requirements remapped across M files
   - Plan: archived to `plan-history/`, N completed milestones summarized
   - ID mapping: list of old → new ID changes

### Mid-Cycle Handling

The migration must preserve the current SDD phase state:

| Current phase | What to preserve |
|--------------|-----------------|
| Research in progress | Don't migrate the in-progress spike; let it finish first or migrate it with `status: In-Progress` |
| Requirements draft | Migrate the draft; split into category files with `status: Approved` |
| Specs in progress | Update ID references in spec `requires` lists |
| Plan in progress | Remap IDs in task traces; preserve task completion status |
| Implementation | Remap IDs; code references (comments, test names) are NOT migrated — only docs/ files |
| Verification | Remap IDs in verification tables |

**Why not migrate code references**: Code files may use requirement IDs in
comments or test names, but these are implementation details. Migrating them
risks breaking code. The traceability matrix provides the mapping; developers
update code references as they encounter them.

### Version Routing

The skill routes based on current version:

```
if version == missing:
    migrate_v1_to_v2()    # Steps 1-3 above
    migrate_v2_to_v3()    # See "v2 to v3 Migration" below
elif version == 2:
    migrate_v2_to_v3()
elif version == 3:
    inform("already at v3, nothing to do")
```

For v1 projects, both migrations run in a single invocation. The intermediate
v2 state exists only briefly during execution — finalization writes `3`, not
`2`. See § v1 to v3 Composition for details.

Each migration is a self-contained section. The skill version and migration
logic are defined in `SKILL.md`, not in external scripts.

## v2 to v3 Migration

### Overview

v3 adds behavioral conventions on top of the v2 artifact layout: chunk-close
review, Q-IMPL deviation protocol, per-milestone plan support, and cross-spec
consistency. The only artifact change is plan vocabulary — work-unit headers
shift from `### M N:` to `### Chunk N:`, reserving "milestone" for delivery
groupings. The migration is lightweight: one required rename step, two optional
advisory steps, and a version bump.

### Detection

Primary signal: `docs/.sdd-version` contains `2`.

When `.sdd-version` contains `3`, the skill informs the operator and exits.
When `.sdd-version` is missing (v1), the skill runs v1→v2 first, then
proceeds to v2→v3 (see § v1 to v3 Composition).

No secondary heuristics are needed. The version marker is authoritative.

### Step 1: Plan Vocabulary Rename

**Precondition**: `docs/plan.md` exists and contains work-unit headers
matching the `### M\d+:` pattern (M followed by one or more digits, then a
colon). Section headers like `### Migration` or `### Models` do not match
this pattern.

**Skip conditions** — the skill skips this step entirely if:
- `docs/plan.md` does not exist
- The plan already uses `### Chunk N:` headers (no `### M\d+:` matches)
- The plan is complete with no active work

**Process**:
1. Read `docs/plan.md`.
2. Scan for lines matching `### M\d+:` at the work-unit level.
3. Present proposed renames to the operator, preserving original numbering:
   ```
   ### M1: Foundation    →  ### Chunk 1: Foundation
   ### M2: Core Models   →  ### Chunk 2: Core Models
   ```
   Numbering is preserved (M1 → Chunk 1, not Chunk 0) because chunk-close
   triggers on `### Chunk N:` regardless of N's value, and renumbering would
   break external references (commit messages, conversations, documentation)
   for no functional benefit.
4. Wait for operator confirmation before applying.
5. Apply renames in `docs/plan.md` only. Archive files in `docs/plan-history/`
   are historical snapshots and are not modified.

**Edge cases**:
- **Mixed headers** (`### M1:` as delivery milestone + `### Chunk N:` as work
  units): Already partially v3-compatible. Present the mixed state to the
  operator for confirmation; don't auto-rename delivery milestone headers.
- **Completed sections in `## Completed`**: Leave as-is. Completed entries
  are one-line summaries without `###` headers in the active plan.

### Step 2: Multi-Milestone Split (Optional)

**Precondition**: `docs/plan.md` contains multiple delivery milestone
groupings with distinct chunks under each.

**Process**:
1. Detect multi-milestone structure in `docs/plan.md`.
2. Offer to split into per-milestone plan files (`docs/plan-{id}.md`) with
   `docs/plan.md` converted to an index. Per milestone-plans.md spec, each
   per-milestone file gets `milestone:`, `last_updated:`, and `status:`
   frontmatter.
3. Operator confirms or declines. Declining is the default — single-file
   plans are valid in v3.
4. If accepted, archive the pre-split plan to `docs/plan-history/`.

**Why optional**: Single-milestone plans satisfy all v3 conventions. Splitting
is valuable only for multi-milestone projects that want milestone-scoped
staleness detection and independent milestone lifecycle management.

### Step 3: Capability Report

After completing required steps, the skill reports new v3 capabilities:

- **Chunk-close review**: Structured 4-check checklist at each `### Chunk N:`
  boundary during `sdd-implement`
- **Q-IMPL deviation protocol**: Three-tier classification for implementation
  decisions that diverge from spec
- **Per-milestone plan support**: Optional structure for multi-milestone
  projects with milestone-scoped staleness
- **Cross-spec consistency pass**: Type reference validation between specs
  during `sdd-specs`

The report is informational. No operator action required — these mechanisms
activate automatically during their respective skill phases.

### Step 4: Finalization

1. Write `3` to `docs/.sdd-version`.
2. Present a migration summary:
   - Plan vocabulary: N headers renamed (or "skipped — already using Chunk
     format")
   - Multi-milestone split: applied / declined / not applicable
   - New capabilities: listed above

**Why version marker is written last**: If any prior step fails or is
interrupted, `.sdd-version` still contains `2`. Re-running `sdd-migrate`
detects v2 and resumes the v2→v3 migration. Writing the marker last
guarantees that a `3` on disk means all migration steps completed.

### v2→v3 Acceptance Criteria

- [ ] `sdd-migrate` detects `.sdd-version == 3` and exits (REQ-MIG-009)
- [ ] `sdd-migrate` detects `.sdd-version == 2` and offers v3 migration
      (REQ-MIG-009)
- [ ] Plan vocabulary rename matches `### M\d+:` precisely — does not
      match `### Migration`, `### Models`, etc. (REQ-MIG-010)
- [ ] Rename preserves original numbering: M1 → Chunk 1 (REQ-MIG-010)
- [ ] Operator confirmation required before vocabulary rename (REQ-MIG-010)
- [ ] Rename skipped when plan already uses `### Chunk N:` (REQ-MIG-010)
- [ ] Multi-milestone split is operator-confirmed, not automatic (REQ-MIG-011)
- [ ] Single-file plans remain valid in v3 (REQ-MIG-011, REQ-COMPAT-002)
- [ ] Capability report describes v3 mechanisms (REQ-MIG-012)
- [ ] Version marker written last for resumability (REQ-MIG-014)

## v1 to v3 Composition

For v1 projects (`.sdd-version` missing), `sdd-migrate` runs v1→v2
(Steps 1-3 from the existing migration pipeline, unchanged) then v2→v3
(Steps 1-4 from the section above) in a single invocation.

The intermediate v2 state exists only briefly during execution — finalization
writes `3` to `.sdd-version`, not `2`. The operator sees one migration
flow, not two separate runs.

**Resumability**: If v1→v2 fails mid-way, `.sdd-version` is still missing.
Re-running `sdd-migrate` resumes v1→v2 from where it stopped (each step
is idempotent), then continues to v2→v3. If v1→v2 completes but v2→v3 is
interrupted, `.sdd-version` is still missing (v1→v2 doesn't write it in
the composition path — only the final v2→v3 finalization writes `3`).

**Existing logic preservation**: The v1→v2 migration (research, requirements,
and plan steps) is not modified. v2→v3 is added as a new section. The
composition is routing logic only — no changes to either migration's
internals.

### v1→v3 Acceptance Criteria

- [ ] v1→v3 composition runs sequentially in one invocation (REQ-MIG-013)
- [ ] v1→v2 logic is unchanged (REQ-MIG-013)
- [ ] Intermediate v2 state is not visible to the operator (REQ-MIG-013)
- [ ] Final `.sdd-version` contains `3`, not `2` (REQ-MIG-013, REQ-MIG-014)
- [ ] Interrupted v1→v3 migration is resumable (REQ-MIG-007, REQ-MIG-014)

## Verification

### Manual
- Run migration on a v1 project and verify:
  - All research files moved to RS-NNN directories
  - All requirement IDs remapped consistently
  - Plan archived and active plan is lean
  - Plan vocabulary uses `### Chunk N:` headers
  - `docs/.sdd-version` contains `3`
  - No orphaned old-format files remain
- Run migration on a v2 project and verify:
  - Plan vocabulary renamed (or skipped if already `### Chunk N:`)
  - Capability report displayed
  - `docs/.sdd-version` updated to `3`
- Run migration on a v3 project and verify it exits cleanly
- Run migration on a mid-cycle project and verify phase can resume

### Acceptance Criteria
- [ ] `sdd-migrate` skill exists at `skills/sdd-migrate/SKILL.md` (REQ-MIG-001)
- [ ] Detects v1 (no version file), v2 (version file = 2), and v3 (version file = 3) (REQ-MIG-002)
- [ ] Research files moved to `RS-NNN-{topic}/findings.md` (REQ-MIG-003)
- [ ] RS numbers assigned by file date (REQ-MIG-003)
- [ ] `docs/research/index.md` created (REQ-MIG-003)
- [ ] Requirements split into category files (REQ-MIG-004)
- [ ] IDs remapped from `REQ-{TYPE}-{NNN}` to `REQ-{DOMAIN}-{NNN}` (REQ-MIG-004)
- [ ] Old IDs replaced in all docs/ files (REQ-MIG-004)
- [ ] `requirements/index.md` created with version 2.0 (REQ-MIG-004)
- [ ] `traceability.md` seeded from existing specs (REQ-MIG-004)
- [ ] Plan archived to `plan-history/` (REQ-MIG-005)
- [ ] Active plan contains only current/future work (REQ-MIG-005)
- [ ] `docs/.sdd-version` written after all steps complete (REQ-MIG-006, REQ-MIG-014)
- [ ] No files deleted until replacements verified (REQ-MIG-007)
- [ ] Each step independently runnable and idempotent (REQ-MIG-007)
- [ ] Mid-cycle projects: IDs remapped, phase state preserved (REQ-MIG-008)
- [ ] Version marker at `docs/.sdd-version` (REQ-CFG-001)
