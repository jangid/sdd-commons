# Implementation Plan: SDD Artifact Structure v2

## Overview

We're updating all 7 existing SDD skills and creating 1 new skill (sdd-migrate)
to support the v2 artifact structure. All deliverables are SKILL.md files —
Markdown skill definitions, not runtime code. The approach is: create the new
migration skill first, then update artifact-producing skills (research,
requirements), then artifact-consuming skills (specs, plan, implement, verify,
replan), then verify everything works together.

## Conventions

- **Tests alongside implementation**: each skill update is verified by checking
  that its SKILL.md references the correct v2 paths and conventions.
- **Task types**: [implement] rewrites a SKILL.md, [verify] validates consistency.
- **Parallelization**: M2 tasks are independent. M3 tasks are independent.
  M2 and M3 can run in parallel since they edit different files.

## Milestones

### M1: Migration skill — new sdd-migrate SKILL.md
**Goal**: A complete `skills/sdd-migrate/SKILL.md` that can guide v1→v2 migration.
**Tasks**:
1. [implement] Create `skills/sdd-migrate/SKILL.md` with version detection,
   3-step migration pipeline (research, requirements, plan), mid-cycle handling,
   and future migration scaffolding — traces to migration.md
**Verify**: SKILL.md exists, covers all REQ-MIG-* acceptance criteria, follows
skill conventions from CLAUDE.md (frontmatter, <500 lines, kebab-case name).

### M2: Artifact-producing skills — sdd-research and sdd-requirements
**Goal**: The two skills that create primary artifacts are updated to write v2 format.
**Depends on**: None (independent of M1)
**Tasks**:
1. [implement] Update `skills/sdd-research/SKILL.md` — change output path to
   `RS-NNN-{topic}/findings.md`, add ID assignment logic, add index maintenance,
   update phase detection to scan RS-* directories — traces to research-artifacts.md,
   skill-updates.md §sdd-research
2. [implement] Update `skills/sdd-requirements/SKILL.md` — change to per-domain
   files, add versioned index maintenance, add traceability row creation, add
   format detection (v1 → suggest migrate), add research staleness check, add
   file size monitoring, update ID scheme to REQ-{DOMAIN}-{NNN} — traces to
   requirements-artifacts.md, skill-updates.md §sdd-requirements
**Verify**: Both skills reference v2 paths exclusively. No references to flat
`docs/research/{topic}.md` or monolithic `docs/requirements.md` as write targets.

### M3: Artifact-consuming skills — specs, plan, implement, verify, replan
**Goal**: All five skills that read/consume artifacts are updated for v2 paths and conventions.
**Depends on**: None (independent of M1, M2 — edits different files)
**Tasks**:
1. [implement] Update `skills/sdd-specs/SKILL.md` — read from split requirements,
   use REQ-{DOMAIN}-{NNN} IDs, add traceability.md update step, update staleness
   to use index.md — traces to skill-updates.md §sdd-specs
2. [implement] Update `skills/sdd-plan/SKILL.md` — add archive pattern (archive
   before rewrite), active plan format (completed summaries only), no changelog
   section, staleness from index.md, read research from RS-* paths — traces to
   plan-management.md, skill-updates.md §sdd-plan
3. [implement] Update `skills/sdd-replan/SKILL.md` — changelogs to archive file,
   removed tasks to archive, significant vs minor distinction, read from v2
   paths — traces to plan-management.md, skill-updates.md §sdd-replan
4. [implement] Update `skills/sdd-implement/SKILL.md` — read requirements from
   split paths, spike tasks write to RS-NNN format, traceability.md updates for
   Test/Implementation columns, staleness from index.md — traces to
   skill-updates.md §sdd-implement
5. [implement] Update `skills/sdd-verify/SKILL.md` — read from split requirements,
   verify traceability matrix completeness, update Verified column, staleness from
   index.md — traces to skill-updates.md §sdd-verify

**Verify**: No skill references `docs/requirements.md` as a single file.
All skills reference `docs/requirements/index.md` for staleness. No skill
appends changelogs to active plan.

### M4: Cross-skill consistency verification
**Goal**: All 8 skills work together coherently with no contradictory path references.
**Depends on**: M1, M2, M3
**Tasks**:
1. [verify] Check all skills for v2 path consistency — grep for v1 patterns
   (`docs/research/{topic}.md` flat refs, `docs/requirements.md` as target,
   `## Plan Changelog` in active plan) — traces to overview.md acceptance criteria
2. [verify] Check shared conventions — all skills suggest `sdd-migrate` when
   version marker is missing, all use `index.md` for staleness, version marker
   handling is consistent — traces to overview.md, skill-updates.md §shared
3. [verify] Check traceability update responsibilities — confirm sdd-requirements
   creates rows, sdd-specs fills Spec column, sdd-implement fills Test/Impl
   columns, sdd-verify fills Verified column — traces to requirements-artifacts.md
   §traceability

**Verify**: Zero v1 patterns found. All traceability responsibilities accounted for.
No contradictions between skills.

## Replan Triggers

- If any single SKILL.md exceeds 500 lines after updates → split into sub-skills
  or simplify the instructions
- If the shared "version detection + suggest migration" logic is too repetitive
  across 7 skills → consider extracting a shared preamble pattern

## Risks

- **Skill file size**: sdd-requirements may grow significantly with all the new
  index maintenance, traceability, and format detection logic. Mitigation: focus
  on concise instructions, reference specs for format details rather than
  inlining them.
- **Circular references**: sdd-migrate references how other skills work (to know
  what to migrate to), while other skills reference sdd-migrate (to suggest it).
  Mitigation: keep references one-directional — skills suggest "run sdd-migrate",
  sdd-migrate doesn't describe how other skills work internally.

## Open Questions

- None — all uncertainties were resolved in research and requirements phases.
