# Implementation Plan: sdd-orchestrate Non-Research Entry (REQ-ORCH-031..033)

## Overview

Add **non-research (mid-pipeline) entry** to the `sdd-orchestrate` driver — the
last deferred feature (design Q4). When upstream SDD artifacts already exist and
are approved, the operator may start the loop at requirements/specs/plan/implement
instead of always starting at research. Deliverable is edits to
`skills/sdd-orchestrate/SKILL.md` plus operator-doc reconciliation
(`USAGE.md` / `README.org`); no other `sdd-*` skill is modified. Markdown
authoring — verify tasks are acceptance-criteria inspection, not unit tests.

## Conventions

- **Task types**: [implement] produces SKILL.md / doc prose, [verify] validates
  against spec acceptance criteria. No [spike] — the design reuses existing phase
  detection (RS-005 Q3) and adds no unverified mechanism.
- **Chunk headers**: `### Chunk N: <name>`.
- **Traceability**: each task names its REQ; after, update
  `docs/requirements/traceability.md`.

## Chunks

### Chunk 0: Entry-point behavior + doc reconciliation

**Goal**: SKILL.md specifies non-research entry (detection/confirm/validate +
entry kickoff), research stays the default, and the operator docs no longer call
research-entry-only a limitation. No other skill touched.

**Tasks**:
1. [implement] Add an **§Entry Points** section to SKILL.md: non-research entry at
   requirements/specs/plan/implement; valid only when upstream is approved; verify
   is not an entry point; **distinct from resume** (REQ-ORCH-029 continues *this
   driver's* cycle; entry begins a loop over externally-produced artifacts).
   Traces to spec §Entry Points. (REQ-ORCH-031)
2. [implement] Specify **detection → confirm → validate** in SKILL.md: auto-detect
   the proposed entry stage via existing phase detection, present + confirm
   (operator may override earlier), validate upstream approved (else route to the
   earliest incomplete upstream and explain); never guess without confirmation.
   (REQ-ORCH-032)
3. [implement] Specify the **entry kickoff** in SKILL.md §KICKOFF: for non-research
   entry, `kickoff.md` records scope + entry stage + assumed-approved upstream (not
   research questions); DISCUSS still runs first; kickoff stays the only new
   artifact. Reframe §KICKOFF / §What This Is / Scope so research is the *default*
   entry, not the only one (REQ-ORCH-005). (REQ-ORCH-033, REQ-ORCH-005)
4. [implement] Reconcile operator docs: update `skills/sdd-orchestrate/USAGE.md`
   (§v1 limitations — drop research-entry-only as a limit; document non-research
   entry, detection/confirm/validate, entry kickoff) and `README.org` if it states
   research-entry. (REQ-ORCH-031, REQ-ORCH-020/021)
5. [verify] Walk the 4 new acceptance criteria (REQ-ORCH-005/031/032/033) against
   SKILL.md; fill traceability Implementation + Verified for REQ-ORCH-031/032/033;
   confirm REQ-ORCH-005's row stays accurate; confirm no other `sdd-*` skill
   modified (REQ-ORCH-001); SKILL.md well-formed and within the ~1000-line
   guideline.

**Entry criteria**: Specs approved.
**Exit criteria**: 4 criteria pass; traceability filled; SKILL.md kebab/
frontmatter/fences valid; only `sdd-orchestrate` touched; docs reconciled.

## Replan Triggers

- If validating "upstream is approved" needs the driver to reimplement a stage
  skill's status/staleness check (rather than relay it) → revisit; the design
  assumes the driver reads artifact frontmatter/phase detection, not new logic.
- If distinguishing non-research *entry* from *resume* on disk proves impossible
  without a new marker (contradicting REQ-ORCH-014) → escalate; the design relies
  on operator intent + artifact provenance, not a marker.

## Completed

- RS-005 sdd-orchestrate driver: research → verify (2026-06-04)
- RS-006 implement-stage fan-out (Design B), dogfooded end-to-end (2026-06-05)
- Driver fixes REQ-ORCH-029/030 + ~1000 soft-limit convention (2026-06-05)

## Risks

- **Doc-only change, low risk**: adds prose to an existing skill; the mechanism
  (phase detection) is already proven (RS-005 Q3). Main risk is clearly
  distinguishing entry from resume for the reader — caught by task 1 wording and
  the verify task.

## Archive

Full plan history:
- [2026-06-04-rs005-orchestrate-complete.md](plan-history/2026-06-04-rs005-orchestrate-complete.md)
- [2026-06-05-fanout-complete.md](plan-history/2026-06-05-fanout-complete.md)
- [2026-06-06-driver-fixes-complete.md](plan-history/2026-06-06-driver-fixes-complete.md)
