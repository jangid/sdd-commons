# Implementation Plan: sdd-review Skill (RS-004)

## Overview

Create `skills/sdd-review/SKILL.md` per `docs/spec/review.md`. The
skill provides structured external review at SDD phase boundaries,
running in a separate session with phase-specific checklists and a
tiered findings report. Also update `sdd-verify` to acknowledge
sdd-review as the fourth verification layer. Single skill created,
one skill updated — deliverable is Markdown skill definitions.

## Conventions

- **Task types**: [implement] produces SKILL.md changes, [verify]
  validates against spec acceptance criteria.
- **Chunk headers**: `### Chunk N: <name>` per v3 conventions.
- **Traceability**: each task's `traces to` reference identifies the
  spec section. After completing each task, update
  `docs/requirements/traceability.md` Implementation column.
- **Chunk close**: 4-check review per chunk-close-review.md at chunk
  boundary.

## Chunks

### Chunk 0: sdd-review skill implementation

**Goal**: `skills/sdd-review/SKILL.md` exists, implements all 8
REQ-REV requirements, and is comparable in size to sdd-verify
(~200-250 lines). `sdd-verify` acknowledges sdd-review.

**Tasks**:
1. [implement] Create skill scaffolding — frontmatter (`name`,
   `description`), opening section establishing context and the
   reviewer's role, phase detection logic for six reviewable phases.
   Traces to review.md §Phase Detection. (REQ-REV-001, REQ-SKILL-018)
2. [implement] Add session-isolation confirmation prompt as the
   skill's opening step — concrete wording per spec, confirm/stop
   options, note on operator responsibility. Traces to review.md
   §Session Isolation. (REQ-REV-007)
3. [implement] Add required inputs section — deliverable, prior phase
   output, traceability matrix as the three inputs; explicit exclusion
   of working-session deliberations. Traces to review.md §Required
   Inputs. (REQ-REV-003)
4. [implement] Add six per-phase checklists — research, requirements,
   specs, plan, implement, verify. Each with content-correctness and
   scope-completeness items. Include RS-004 F2 evidence citation for
   the scope-completeness rationale. Traces to review.md §Per-Phase
   Checklists. (REQ-REV-001, REQ-REV-008)
5. [implement] Add report format section — verdict (Approve / Approve
   with fixes / Reject), strengths (required, substantive), tiered
   findings (critical/material/minor), recommendation. Inline-only,
   not persisted. Traces to review.md §Report Format. (REQ-REV-002)
6. [implement] Add bias disclosure pattern — section template, prior
   involvement description, omission rule when no prior involvement.
   Traces to review.md §Bias Disclosure. (REQ-REV-004)
7. [implement] Add trigger classification — mandatory (requirements→
   specs, specs→plan), recommended (plan→implement, post-verification),
   ad-hoc (any time), skip (chunk-close boundaries). Traces to
   review.md §Trigger Classification. (REQ-REV-005)
8. [implement] Add scope boundaries — explicit delineation against
   chunk-close (mechanical), XSPEC (structural), sdd-verify (holistic).
   Verification stack positioning table. Traces to review.md
   §Verification Stack Positioning. (REQ-REV-006)
9. [verify] Walk all 13 spec acceptance criteria against the completed
   SKILL.md — confirm every checkbox item has a corresponding
   instruction in the skill. Traces to review.md §Acceptance Criteria.
10. [implement] Update `skills/sdd-verify/SKILL.md` — add one paragraph
    acknowledging sdd-review as the fourth verification layer
    (out-of-session semantic review complementing sdd-verify's
    in-session holistic check). Traces to skill-updates.md
    §REQ-SKILL-018.

**Entry criteria**: Approved specs (review.md, skill-updates.md).
**Exit criteria**: Chunk close clean. `sdd-review` SKILL.md handles
all 6 phases with content + scope checklists. All 13 acceptance
criteria verified. `sdd-verify` references sdd-review.

## Replan Triggers

- `skills/sdd-review/SKILL.md` exceeds 350 lines → compress existing
  content or restructure checklists into a more compact format
- Session-isolation prompt wording from the spec proves ambiguous when
  read by an external operator → would require spec edit (Tier 3)
- Six per-phase checklists resist compression below ~8 items each →
  would suggest the spec needs structural rethink

## Completed

- v2 artifact structure: 8 skills updated for v2 paths (2026-04-28, 11 tasks)
- RS-002 workflow improvements: chunk-close, Q-IMPL, per-milestone,
  cross-spec consistency, staleness enhancements (2026-05-25, 5 chunks)
- RS-003 v3 migration: sdd-migrate v2→v3, v1→v3 composition, version
  bump to v3 (2026-05-25, 9 tasks)

## Risks

- **External-adopter ergonomics**: sdd-review is the second
  external-adopter-facing skill (after sdd-migrate). The
  session-isolation prompt is the operator's first interaction. If
  confusing, adopters bounce. Mitigation: spec specifies concrete
  prompt wording; verify task confirms readability.
- **Bias disclosure adoption**: Whether reviewers consistently follow
  the disclosure rule is unenforceable. If silently skipped, the
  protection is theoretical. No mitigation beyond making the prompt
  clear and the rationale visible.
- **Skill size**: sdd-review has more structural sections than
  sdd-verify (6 checklists vs none). Risk of exceeding the 350-line
  replan trigger. Mitigation: compress checklists to ~4-6 items each;
  reference spec for rationale rather than duplicating.

## Archive

Full plan history:
- [2026-04-28-pre-v2-migration.md](plan-history/2026-04-28-pre-v2-migration.md)
- [2026-05-25-pre-rs002-rewrite.md](plan-history/2026-05-25-pre-rs002-rewrite.md)
- [2026-05-25-rs002-complete.md](plan-history/2026-05-25-rs002-complete.md)
- [2026-05-25-rs003-complete.md](plan-history/2026-05-25-rs003-complete.md)
