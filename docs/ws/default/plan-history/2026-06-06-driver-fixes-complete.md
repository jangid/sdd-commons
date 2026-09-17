# Implementation Plan: sdd-orchestrate Driver Fixes (RS-006 dogfooding findings)

## Overview

Two small, doc-level behavior clarifications to the `sdd-orchestrate` driver,
surfaced while dogfooding the RS-006 fan-out cycle through the driver itself:
new-cycle-vs-resume detection (REQ-ORCH-029) and orchestrator-only work
(REQ-ORCH-030). Deliverable is edits to `skills/sdd-orchestrate/SKILL.md`; no
other `sdd-*` skill is modified. A side convention change (the ~500→~1000 line
SKILL.md/spec guideline) was applied directly at the operator's request and is
verified here, not re-implemented.

## Conventions

- **Task types**: [implement] produces SKILL.md prose, [verify] validates against
  spec acceptance criteria. No [spike] — the findings are already evidenced by the
  RS-006 dogfood run.
- **Chunk headers**: `### Chunk N: <name>`.
- **Traceability**: each task names its REQ; after each, update
  `docs/requirements/traceability.md`.

## Chunks

### Chunk 0: Driver behavior clarifications

**Goal**: `SKILL.md` states the new-cycle-vs-resume rule and the orchestrator-only
work rule, matching the spec; no other skill touched.

**Tasks**:
1. [implement] Add the **new-cycle vs. resume** rule to SKILL.md §Phase Detection:
   classify entry state as resume / done / new-cycle; when the prior cycle is
   `verification.md` status pass and the operator brings a new idea, run DISCUSS
   and overwrite `docs/handoff/kickoff.md` rather than reporting DONE; surface the
   interpretation and confirm. Traces to spec §New cycle vs. resume.
   (REQ-ORCH-029)
2. [implement] Add an **Orchestrator-Only Work** note to SKILL.md: dispatch-
   requiring work (implement-stage fan-out execution; parallel-dispatch spikes)
   runs at the orchestrator level, never delegated to a leaf pipeline subagent
   (no dispatch tool, RS-006 Q1). Traces to spec §Orchestrator-Only Work.
   (REQ-ORCH-030)
3. [verify] Walk the two new acceptance criteria (REQ-ORCH-029, REQ-ORCH-030)
   against SKILL.md; confirm the ~1000-line convention change landed in CLAUDE.md,
   the sdd-specs guideline, and REQ-ORCH-019; fill traceability
   Implementation + Verified for REQ-ORCH-029/030. Confirm no other `sdd-*` skill
   modified (REQ-ORCH-001) and SKILL.md is still well-formed.

**Entry criteria**: Specs approved.
**Exit criteria**: Both criteria pass; traceability filled; SKILL.md kebab/
frontmatter/fences valid; only `sdd-orchestrate` touched.

## Replan Triggers

- If stating REQ-ORCH-029 requires a new on-disk marker to disambiguate
  new-vs-resume (contradicting REQ-ORCH-014's no-marker rule) → escalate; the
  spec's "operator intent disambiguates" approach assumes no marker is needed.
- If REQ-ORCH-030's "recognize dispatch-requiring work" proves to need a concrete
  detection mechanism beyond a prose rule → revisit the spec.

## Completed

- RS-005 sdd-orchestrate driver: research → verify (2026-06-04)
- RS-006 implement-stage fan-out (Design B): research → verify, dogfooded
  end-to-end through the driver (2026-06-05)

## Risks

- **Doc-only change, low risk**: both tasks add prose to an existing skill; the
  behaviors were observed working in the RS-006 run, so this codifies rather than
  invents. Main risk is wording clarity, caught by the verify task.

## Archive

Full plan history:
- [2026-06-04-rs004-complete.md](plan-history/2026-06-04-rs004-complete.md)
- [2026-06-04-rs005-orchestrate-complete.md](plan-history/2026-06-04-rs005-orchestrate-complete.md)
- [2026-06-04-pre-fanout-reseq.md](plan-history/2026-06-04-pre-fanout-reseq.md)
- [2026-06-05-fanout-complete.md](plan-history/2026-06-05-fanout-complete.md)
