# Implementation Plan: v3 Migration (RS-003)

## Overview

Add v2→v3 migration support to `sdd-migrate`, including plan vocabulary
rename, optional multi-milestone split, capability reporting, and v1→v3
sequential composition. Then bump the skills repo's own `.sdd-version` to
`3` as dogfooding. Single skill modified (`skills/sdd-migrate/SKILL.md`),
no test suite — deliverable is a Markdown skill definition.

## Conventions

- **Task types**: [implement] produces SKILL.md changes, [verify] validates
  behavior against spec acceptance criteria.
- **Chunk headers**: `### Chunk N: <name>` per v3 conventions.
- **Traceability**: each task's `traces to` reference identifies the spec
  section. After completing each task, update `docs/requirements/traceability.md`
  Implementation column.
- **Chunk close**: 4-check review per chunk-close-review.md at chunk boundary.

## Chunks

### Chunk 0: sdd-migrate v2→v3 implementation

**Goal**: `sdd-migrate` handles v2→v3 migration (vocabulary rename, optional
split, capability report, finalization) and v1→v3 composition. Skills repo
runs as a v3 project.

**Tasks**:
1. [implement] Update version detection and routing logic — add v3 detection
   (`.sdd-version == 3` → exit), v2→v3 offer, and v1→v3 composition entry
   point. Traces to migration.md §Version Detection, §Version Routing.
   (REQ-MIG-002, REQ-MIG-009)
2. [implement] Add v2→v3 Step 1: plan vocabulary rename — `### M\d+:` pattern
   matching, operator confirmation flow, numbering preservation (M1 → Chunk 1),
   skip conditions (no plan, already chunk format, plan complete), edge cases
   (mixed headers, completed sections). Traces to migration.md §Step 1.
   (REQ-MIG-010)
3. [implement] Add v2→v3 Step 2: multi-milestone split offer — detect
   multi-milestone structure, offer operator-confirmed split into per-milestone
   files, preserve single-file as valid default. Traces to migration.md §Step 2.
   (REQ-MIG-011)
4. [implement] Add v2→v3 Step 3: capability report — informational listing of
   chunk-close, Q-IMPL, per-milestone, and cross-spec mechanisms. Traces to
   migration.md §Step 3. (REQ-MIG-012)
5. [implement] Add v2→v3 Step 4: finalization — write `3` to `.sdd-version`
   last, present migration summary. Traces to migration.md §Step 4.
   (REQ-MIG-014)
6. [implement] Wire v1→v3 composition routing — after v1→v2 completes,
   continue to v2→v3 in same invocation. Intermediate v2 state brief;
   finalization writes `3`. Existing v1→v2 logic unchanged. Traces to
   migration.md §v1 to v3 Composition. (REQ-MIG-013)
7. [implement] Add backward compatibility notes — v2 projects work without
   migration, chunk-close inactive without `### Chunk N:` headers, per-milestone
   activates only with per-milestone files. Traces to overview.md §Version
   Marker, migration.md §v2→v3 Overview. (REQ-COMPAT-002)
8. [verify] Walk migration.md and overview.md acceptance criteria against the
   updated SKILL.md — confirm every checkbox item has a corresponding
   instruction. Traces to migration.md §v2→v3 Acceptance Criteria, §v1→v3
   Acceptance Criteria, overview.md §Acceptance Criteria.
9. [implement] Bump skills repo's own `docs/.sdd-version` from `2` to `3`.
   Final step — the skills repo becomes a v3 project. (REQ-MIG-014, REQ-SKILL-017)

**Entry criteria**: Approved specs (migration.md, overview.md).
**Exit criteria**: Chunk close clean. `sdd-migrate` SKILL.md handles v2→v3
and v1→v3 paths. All acceptance criteria verified. Skills repo `.sdd-version`
is `3`.

## Replan Triggers

- `sdd-migrate` SKILL.md exceeds 350 lines after additions → compress existing
  content or extract shared utilities into a referenced section
- Edge cases surface that aren't covered by migration.md §Step 1 (e.g.,
  archived plans with unexpected header formats needing modification)
- v1→v2 logic needs unexpected modification to support composition (would
  violate REQ-MIG-013 "v1→v2 logic must remain unchanged")

## Completed

- v2 artifact structure: 8 skills updated for v2 paths (2026-04-28, 11 tasks)
- RS-002 workflow improvements: chunk-close, Q-IMPL, milestone plans,
  cross-spec consistency, staleness enhancements (2026-05-25, 5 chunks)

## Risks

- **External adopter migration paths**: First migration designed for external
  operators. If the operator-confirmation flow is unclear or the rename pattern
  over-matches, external adopters hit it before we do. Mitigation: precise
  `### M\d+:` regex, clear acceptance criteria, operator-readable messages.
- **Skills repo self-migration**: Bumping `.sdd-version` to `3` means future
  skill work runs under v3 expectations (chunk-close, Q-IMPL). No mitigation
  needed — intentional dogfooding — but flagging as a notable side-effect.
- **SKILL.md size**: sdd-migrate may grow close to the 500-line budget. Current
  size unknown. Mitigation: keep v2→v3 instructions concise, reference spec
  sections for rationale instead of duplicating.

## Archive

Full plan history:
- [2026-04-28-pre-v2-migration.md](plan-history/2026-04-28-pre-v2-migration.md)
- [2026-05-25-pre-rs002-rewrite.md](plan-history/2026-05-25-pre-rs002-rewrite.md)
- [2026-05-25-rs002-complete.md](plan-history/2026-05-25-rs002-complete.md)
