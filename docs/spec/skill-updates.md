---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-SKILL-001
  - REQ-SKILL-002
  - REQ-SKILL-003
  - REQ-SKILL-004
  - REQ-SKILL-005
  - REQ-SKILL-006
  - REQ-SKILL-007
  - REQ-SKILL-008
  - REQ-SKILL-009
  - REQ-SKILL-010
  - REQ-SKILL-011
  - REQ-SKILL-012
  - REQ-SKILL-013
  - REQ-SKILL-014
  - REQ-SKILL-015
  - REQ-SKILL-016
  - REQ-STALE-001
  - REQ-STALE-002
  - REQ-SKILL-017
  - REQ-SKILL-018
  - REQ-SKILL-019
  - REQ-SKILL-020
  - REQ-SKILL-021
  - REQ-SKILL-022
  - REQ-SKILL-023
  - REQ-SKILL-024
---

# Skill Updates

## Context

All seven existing SDD skills reference v1 artifact paths and conventions.
Each skill needs targeted updates to its phase detection logic, read/write
paths, and staleness checks. The changes are mechanical — the skill workflows
themselves don't change, only the paths and formats they operate on.

This spec documents the changes needed in each skill, organized by skill.

## Design

### Shared Changes (All Skills)

Every SDD skill's phase detection section must be updated:

1. **Read version**: Check `docs/.sdd-version` on entry. If missing, suggest
   `sdd-migrate`.
2. **Requirements path**: Replace `docs/requirements.md` with
   `docs/requirements/index.md` for existence/staleness checks.
3. **Staleness comparison**: Compare against `docs/requirements/index.md`'s
   `last_updated` instead of `docs/requirements.md`'s `last_updated`.

**Why suggest migration instead of silently handling both formats**: Dual-format
support in every skill creates complexity and bugs. A clean migration followed
by single-format skills is simpler and more maintainable.

### sdd-research

**Current behavior**: Writes to `docs/research/{topic}.md`.

**Changes**:
1. **ID assignment**: Scan `docs/research/RS-*` directories to find the next
   sequential number. Start at RS-001 if none exist.
2. **Output path**: Write to `docs/research/RS-NNN-{topic}/findings.md`
   instead of `docs/research/{topic}.md`.
3. **Frontmatter**: Add `id: RS-NNN` field to findings frontmatter.
4. **Index maintenance**: After writing findings, update
   `docs/research/index.md` — add or update the row for this RS ID.
5. **Phase detection**: When checking for existing research on a topic, scan
   `RS-*` directories and read their `findings.md` files (not flat files).

**Unchanged**: The findings document format, research process, budget
enforcement, and recommendation logic remain the same.

### sdd-requirements

**Current behavior**: Reads/writes a single `docs/requirements.md`.

**Changes**:
1. **Format detection**: On entry, check whether `docs/requirements.md` (v1)
   or `docs/requirements/index.md` (v2) exists. If v1 is found, suggest
   running `sdd-migrate` before proceeding.
2. **Read path**: Read all category files under `docs/requirements/` by
   scanning subdirectories. Use `index.md` for the overview and file listing.
3. **Write path**: Write requirements to the appropriate category file based
   on domain. Create new category files and directories as needed.
4. **ID generation**: Use `REQ-{DOMAIN}-{NNN}` scheme. Determine domain from
   target file's frontmatter. Assign next sequential number within that domain.
5. **Index maintenance**: After any change, update `docs/requirements/index.md`:
   bump version (major or minor per rules), bump `last_updated`, update the
   Files table.
6. **Traceability**: After adding a new requirement, add a row to
   `docs/requirements/traceability.md` with the Spec/Test/Implementation/
   Verified columns blank.
7. **Removed requirements**: Instead of `[Removed: date — reason]` inline
   markers, remove the requirement from the category file and mark it
   `[Deprecated]` in `traceability.md`. Never reuse the ID.
8. **Research staleness**: On entry, compare newest research date (from
   `docs/research/index.md`) against `docs/requirements/index.md`'s
   `last_updated`. If research is newer, inform the user.
9. **File size monitoring**: After writing, check if the target file exceeds
   300 lines. If approaching, recommend splitting.

**Unchanged**: The elicitation process, question categories, requirement rules
(testable, one-per-ID, must/should/may), and review cycle.

### sdd-specs

**Current behavior**: Reads `docs/requirements.md`, writes `docs/spec/`.

**Changes**:
1. **Read path**: Read requirements from `docs/requirements/index.md` (for
   overview) and `docs/requirements/{category}/*.md` (for detail). The index
   tells the skill which files exist.
2. **Requires field**: Use `REQ-{DOMAIN}-{NNN}` IDs in spec frontmatter
   `requires` lists.
3. **Traceability update**: After writing or updating a spec, update
   `docs/requirements/traceability.md` — fill the Spec column for each
   requirement the spec addresses.
4. **Staleness check**: Compare `docs/requirements/index.md`'s `last_updated`
   against each spec's `last_updated`.
5. **Coverage check**: During the traceability summary (Step 5), read
   `traceability.md` to verify all requirements have spec coverage. Report
   uncovered requirements from the matrix rather than scanning requirement
   files directly.

**Unchanged**: The spec format, review cycle, and spec rules.

### sdd-plan

**Current behavior**: Reads specs, writes `docs/plan.md`. Appends changelogs
on rewrite.

**Changes**:
1. **Archival on rewrite**: Before writing a new plan (due to staleness or
   fresh creation when a plan exists), archive the current `docs/plan.md` to
   `docs/plan-history/{date}-{reason}.md`.
2. **Active plan format**: Write only current/future milestones. Completed
   milestones go in a `## Completed` section as one-line summaries.
3. **No changelog section**: Do not write a `## Plan Changelog` section in
   the active plan.
4. **Staleness check**: Compare against `docs/requirements/index.md`'s
   `last_updated` (not `docs/requirements.md`).
5. **Requirements reading**: Read from `docs/requirements/{category}/*.md`
   for priority context. Use `index.md` to discover which files exist.
6. **Research reading**: Read from `docs/research/RS-*/findings.md` instead
   of `docs/research/*.md`.

**Unchanged**: The planning process, task typing (implement/spike/verify),
milestone structure, dependency ordering, and replan trigger definition.

### sdd-implement

**Current behavior**: Reads plan and specs, implements tasks.

**Changes**:
1. **Requirements path**: Read from `docs/requirements/{category}/*.md` when
   needing requirement context (e.g., to understand priority or scope).
2. **Staleness check**: Compare `docs/requirements/index.md`'s `last_updated`
   against specs and plan.
3. **Spike tasks**: When a spike task produces findings, ensure they go to
   `docs/research/RS-NNN-{topic}/findings.md` (following the research
   artifact convention) and update `docs/research/index.md`.
4. **Traceability update**: When implementing a task:
   - After writing tests: update `traceability.md`'s Test column for the
     relevant requirements.
   - After writing code: update `traceability.md`'s Implementation column.
5. **Research reading**: Read from `docs/research/RS-*/findings.md`.

**Unchanged**: The TDD inner loop, stuck detection, spec gap handling, and
task completion checklist.

#### Chunk Close Checklist (REQ-SKILL-009)

`sdd-implement`'s current "Step 4: Milestone Checkpoints" must be renamed
to distinguish two levels of checkpoint:

- **Chunk close review**: Runs at each `### Chunk N:` boundary within a
  milestone. Four structured checks (type alignment, traceability, test
  coverage, Q-IMPL audit) with tiered enforcement. See
  chunk-close-review.md for the full checklist design.
- **Milestone checkpoints**: Run at delivery milestone boundaries (M1, M2,
  etc.). The operator approves proceeding to the next milestone.

The chunk close checklist runs more frequently and catches mechanical
errors (type-name drift, missing traceability) before they ripple into
downstream chunks.

#### Q-IMPL Deviation Protocol (REQ-SKILL-010)

`sdd-implement` must document the three-tier deviation protocol inline in
its implementation process. See deviation-protocol.md for the full protocol
design. The skill must include:

- Tier classification guidance (when to use each tier)
- Q-IMPL entry format (ID, tier, decision, rationale)
- Global sequential numbering instructions
- Tier 3 escalation procedure (stop, escalate, reference sdd-replan
  Level 2)

#### Spike Code Separation (REQ-SKILL-011)

For `[spike]` tasks, `sdd-implement` should add a rule:

- Spike findings go to `docs/spikes/{topic}.md`
- Throwaway spike code goes to `scripts/spike_*`
- Production code for the same functionality must be written fresh against
  the spec, not adapted from spike code

**Why fresh code**: Spike code is written for speed of learning, not
production quality. Adapting it silently imports shortcuts and assumptions
that the spec's design may have deliberately avoided.

#### CLAUDE.md Convention Reading (REQ-SKILL-012)

`sdd-implement` must instruct the implementer to read `CLAUDE.md` (if
present) as the first item in its context loading step. Project conventions
from `CLAUDE.md` take precedence over generic patterns when choosing
libraries, coding patterns, and project structure.

**Why must, not should**: The skill *must* instruct the implementer to read
`CLAUDE.md` when present. If absent, the skill proceeds normally. The "must"
is about the skill's behavior, not about requiring `CLAUDE.md` to exist.
Project-specific conventions override generic skill behavior (e.g., preferred
test framework, import style, error handling approach). Missing these
conventions leads to rework when the operator corrects the style.

#### Cross-Spec Consistency in sdd-specs (REQ-SKILL-013)

`sdd-specs` must add the cross-spec consistency reading pass after writing
all specs and before the final coverage check. See
cross-spec-consistency.md for the full design.

#### Milestone Plan Support in sdd-plan (REQ-SKILL-014)

`sdd-plan` must support per-milestone plan files when the project defines
multiple milestones. See milestone-plans.md for the full design. For single-
milestone projects, the existing single-file behavior is preserved.

#### Milestone Plan Support in sdd-replan (REQ-SKILL-015)

`sdd-replan` must work with per-milestone plan files, archiving and revising
the correct milestone's plan file based on which milestone's tasks are
affected.

#### Milestone-Scoped Staleness (REQ-SKILL-016)

`sdd-plan` and `sdd-implement` must implement milestone-scoped staleness
detection when reading per-milestone plan files, comparing only against
requirements and specs traced by that milestone's tasks. See
milestone-plans.md §Milestone-Scoped Staleness.

#### Research-to-Requirements Staleness (REQ-STALE-002)

`sdd-requirements` must detect when new research (a `findings.md` with
`status: Complete`) is newer than `docs/requirements/index.md`'s
`last_updated` and inform the user. This is advisory, not blocking — the
user decides whether the new research affects requirements. This check is
already specified in requirements-artifacts.md §Staleness Detection but is
traced here for completeness.

#### sdd-review Skill (REQ-SKILL-018)

A new skill `skills/sdd-review/SKILL.md` implements the external review
mechanism described in review.md. The skill is phase-agnostic (per
REQ-REV-001) and must include the session-isolation prompt as its opening
step (per REQ-REV-007). The skill operates out-of-session — it provides
checklists and report structure for a reviewer in a separate Claude
session, not in the working session. Target size: ~200-250 lines,
comparable to sdd-verify.

### sdd-verify

**Current behavior**: Reads all artifacts, writes `docs/verification.md`.

**Changes**:
1. **Requirements path**: Read from `docs/requirements/{category}/*.md` to
   collect acceptance criteria.
2. **Traceability verification**: Read `docs/requirements/traceability.md`
   and verify:
   - Every requirement has a spec (Spec column filled)
   - Every implemented requirement has tests (Test column filled)
   - Flag gaps in the verification report.
3. **Traceability update**: After verification, update `traceability.md`'s
   Verified column with pass/fail for each requirement.
4. **Staleness check**: Compare `docs/requirements/index.md`'s `last_updated`
   against plan date.
5. **Plan archival on cycle complete**: After successful verification, the
   plan may be archived. Note this in the recommendation: "Cycle complete —
   plan can be archived with `sdd-plan` on next invocation."

**Unchanged**: The verification process, quality gates, acceptance criteria
walkthrough, user-perspective validation, regression check, and report format.

### sdd-replan

**Current behavior**: Revises plan, appends changelog, marks removed tasks.

**Changes**:
1. **Archival on significant replan**: Before making significant changes
   (adding/removing milestones), archive the current plan to
   `docs/plan-history/{date}-replan-{reason}.md`.
2. **Changelog destination**: Write the changelog entry to the archived plan
   file, not to the active plan.
3. **Removed tasks**: Move invalidated tasks to the archive file. Do not
   write `[removed: reason]` markers in the active plan.
4. **Requirements path**: Read from `docs/requirements/{category}/*.md`.
5. **Staleness check**: Check `docs/requirements/index.md` and spec dates
   as part of situation assessment.

**Unchanged**: The replan process, issue classification (Level 1-4), routing
logic, and rules (minimize disruption, preserve history, cascade awareness).

### v5 Harness Hardening (REQ-SKILL-019..024)

_(added 2026-09-17, RS-008)_ Per-skill changes for the HARN and LINT domains;
designs in `harness-loop-control.md`, `harness-return-contract.md`,
`harness-chunk-verifier.md`, `harness-write-scope.md`, `skill-lint-v5.md`.

- **sdd-orchestrate (REQ-SKILL-019)**: caps (`FIX_LOOP_MAX` per stage,
  `REPLAN_MAX` derived, `REDO_MAX` with the per-chunk session counter
  `chunk_redo_count[<chunk header>]`), `Budget:` / `Write scope:` slots on
  every template, `RETURN:` parsing and `RETURN.status` branching, repair-packet
  composition and finding → chunk mapping, `VERDICT:` / `CHUNK_VERDICT:` /
  `SCOPE:` branching, verifier dispatch, per-chunk sequential implement with
  its per-chunk gate (`proceed │ fix │ stop`), three-command scope check, commit
  ownership, snapshot ordering, gate text order (REQ-ORCH-034). Templates change in `references/dispatch-templates.md`
  (pipeline, review, new verifier, `{repair_packet}`) and `references/fan-out.md`
  (leaf template, verifier-before-merge, checkpoint application in §3e).
  Procedure text lands in **new** `references/write-scope.md` and
  `references/return-contract.md` with stubs in `SKILL.md`.
- **sdd-implement (REQ-SKILL-020)**: attempt ledger + `verified_do_not_touch`,
  oscillation conditions in Step 3, checkpoint format + RETURN mapping, and — as a
  dispatched leaf — the `RETURN:` block and budget self-count. Step 4 unchanged.
- **sdd-review (REQ-SKILL-021)**: own-line `VERDICT:` token; report and scope
  boundaries otherwise unchanged (review is never the chunk verifier).
- **sdd-replan (REQ-SKILL-022)**: `-replan-` filename contract stated; blocked-task
  note defined as the checkpoint slot; Step 1 reads the checkpoint as stuck state.
- **sdd-skill-lint (REQ-SKILL-023)**: `fix` remediation, warn tier, size check,
  backtick `references/` resolution, new `REQUIRED` rows, self-test coverage.
- **sdd-orchestrate marker-4 move (REQ-SKILL-024)**: marker-4 prose to
  `references/v4-workstreams.md` with the `research_id` guard and a superseding
  Q-IMPL in `ws-orchestration.md`; `USAGE.md` describes the new gate signals;
  `CLAUDE.md` gains one short paragraph on the gate vocabulary while its
  four-layer bullet stays unchanged.

## Verification

### Automated
- For each skill SKILL.md file, verify it references v2 paths:
  - `docs/research/RS-*/findings.md` (not `docs/research/*.md`)
  - `docs/requirements/index.md` (not `docs/requirements.md`)
  - `docs/requirements/{category}/*.md` for reading requirements
  - `docs/plan-history/` for archival
- Verify no skill references the v1 monolithic `docs/requirements.md` as a
  write target
- Verify `sdd-replan` does not mention appending changelogs to the active plan
- Verify `sdd-requirements` includes format detection logic

### Manual
- Run each skill against a v2 project structure and confirm correct path usage
- Run `sdd-requirements` against a v1 project and confirm migration suggestion
- Run `sdd-replan` and confirm changelog goes to archive, not active plan

### Acceptance Criteria
- [ ] All 7 skills updated for v2 paths (REQ-SKILL-001)
- [ ] `sdd-research` writes to `RS-NNN-{topic}/findings.md` and maintains index (REQ-SKILL-002)
- [ ] `sdd-requirements` reads/writes split files, maintains index with versioning (REQ-SKILL-003)
- [ ] `sdd-requirements` detects v1 format and suggests migration (REQ-SKILL-003)
- [ ] `sdd-specs` reads from split requirements, updates traceability (REQ-SKILL-004)
- [ ] `sdd-plan` archives before rewrite, keeps active plan lean (REQ-SKILL-005)
- [ ] `sdd-implement` updates traceability when writing tests/code (REQ-SKILL-006)
- [ ] `sdd-verify` verifies traceability matrix, updates Verified column (REQ-SKILL-007)
- [ ] `sdd-replan` writes changelogs/removed tasks to archive only (REQ-SKILL-008)
- [ ] `sdd-implement` includes chunk close checklist at chunk boundaries (REQ-SKILL-009)
- [ ] Step 4 renamed to distinguish chunk vs milestone checkpoints (REQ-SKILL-009)
- [ ] `sdd-implement` documents three-tier Q-IMPL protocol (REQ-SKILL-010)
- [ ] `sdd-implement` separates spike code from production code (REQ-SKILL-011)
- [ ] `sdd-implement` reads CLAUDE.md as first context loading step (REQ-SKILL-012)
- [ ] `sdd-specs` includes cross-spec consistency pass (REQ-SKILL-013)
- [ ] `sdd-plan` supports per-milestone plan files (REQ-SKILL-014)
- [ ] `sdd-replan` handles per-milestone archival and revision (REQ-SKILL-015)
- [ ] Plan skills implement milestone-scoped staleness (REQ-SKILL-016)
- [ ] All skills use `index.md` for staleness detection (REQ-STALE-001)
- [ ] `sdd-requirements` detects research-to-requirements staleness (REQ-STALE-002)
- [ ] `sdd-migrate` implements v2→v3 migration steps (REQ-SKILL-017)
- [ ] `sdd-review` skill exists with session isolation, phase checklists, report format (REQ-SKILL-018)

## Implementation Questions

### Q-IMPL-HARNESSP2-005: per-skill changes for the harness-p2 cycle live in the new specs
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Design (per-skill update tables)
**Decision**: REQ-SKILL-HARNESSP2-001..008 are carried by the new harness-p2 specs, each in a "Skill and Lint Changes" / "Skill Changes" section: `telemetry.md` (-001 orchestrate telemetry, -008 operator docs and CLAUDE.md), `adversarial-verify.md` (-002 red dispatch, -005 sdd-verify pending-red / accepted breaks / gc slot), `arbitrated-handoff.md` (-003 arbitration, -006 sdd-review Material `affects`), `drift-sweep.md` (-004 gc cadence), `dispatch-snapshot-base.md` (-004 snapshot base, -007 sdd-implement references split closing Q-IMPL-083). This spec's tables are unchanged.
**Rationale**: Marker-4 rule: new work adds new spec files; the per-skill table for a workstream stays with the designs it serves.
**Date**: 2026-09-17 (harness-p2 specs stage)
