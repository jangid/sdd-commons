---
domain: SKILL
last_updated: 2026-09-17
status: Approved
research_refs: [RS-003, RS-004, RS-008]
---

# Requirements: Skill Updates

## Overview

Changes required across all existing SDD skills to support the v2 artifact
structure.

## Requirements

### REQ-SKILL-001: Skill update scope
All seven existing SDD skills must be updated to read/write the v2 artifact
structure. Path references, phase detection logic, and staleness checks must
reflect the new layout.
[Priority: must]

### REQ-SKILL-002: sdd-research updates
`sdd-research` must write to `docs/research/RS-NNN-{topic}/findings.md` and
auto-maintain `docs/research/index.md`.
[Priority: must]

### REQ-SKILL-003: sdd-requirements updates
`sdd-requirements` must read/write per-domain files in
`docs/requirements/{category}/`, auto-maintain `index.md` with versioning, and
detect the old monolithic format (offering migration via `sdd-migrate`).
[Priority: must]

### REQ-SKILL-004: sdd-specs updates
`sdd-specs` must read requirements from `docs/requirements/{category}/*.md`,
use the new `REQ-{DOMAIN}-{NNN}` IDs in `requires` frontmatter, and update
`docs/requirements/traceability.md` when mapping specs to requirements.
[Priority: must]

### REQ-SKILL-005: sdd-plan updates
`sdd-plan` must implement the archive pattern (REQ-PLAN-002), keep the active
plan lean (REQ-PLAN-001), and read staleness from
`docs/requirements/index.md` (REQ-STALE-001).
[Priority: must]

### REQ-SKILL-006: sdd-implement updates
`sdd-implement` must read requirements from the new paths, reference RS-* IDs
for spike tasks, and update `docs/requirements/traceability.md` when
tests/implementation are created.
[Priority: must]

### REQ-SKILL-007: sdd-verify updates
`sdd-verify` must read requirements from the new paths, verify traceability
across split files using `traceability.md`, and update the traceability matrix
with verification results.
[Priority: must]

### REQ-SKILL-008: sdd-replan updates
`sdd-replan` must write changelogs to the archive file (REQ-PLAN-003) and move
removed tasks to the archive (REQ-PLAN-004) instead of marking them in the
active plan.
[Priority: must]

### REQ-SKILL-009: sdd-implement chunk-close checklist
`sdd-implement` must add the structured chunk close review checklist
(REQ-CHKC-001 through REQ-CHKC-008) to its implementation process. The
current "Step 4: Milestone Checkpoints" must be renamed to distinguish
chunk-level checkpoints (chunk close review) from milestone-level
checkpoints (delivery approval). Chunk close runs at each `### Chunk N`
boundary; milestone checkpoints run at delivery milestone boundaries.
[Priority: must]

### REQ-SKILL-010: sdd-implement Q-IMPL protocol
`sdd-implement` must document the three-tier deviation protocol
(REQ-QIMPL-001 through REQ-QIMPL-003) in its implementation process,
including tier classification guidance and Q-IMPL entry format.
[Priority: must]

### REQ-SKILL-011: sdd-implement spike code separation
`sdd-implement` must add a rule for `[spike]` tasks: spike code is throwaway
and must be written in a scratch location. Spike findings go to
`docs/spikes/{topic}.md`, throwaway code goes to `scripts/spike_*`. Production
code for the same functionality must be written fresh against the spec, not
adapted from spike code.
[Priority: should]

### REQ-SKILL-012: sdd-implement CLAUDE.md convention reading
`sdd-implement` must instruct the implementer to read `CLAUDE.md` as the
first item in its context loading step. Project conventions from `CLAUDE.md`
take precedence over generic patterns when choosing libraries, coding
patterns, and project structure.
[Priority: must]

### REQ-SKILL-013: sdd-specs cross-spec consistency
`sdd-specs` must add the cross-spec consistency reading pass (REQ-XSPEC-001,
REQ-XSPEC-002) after writing all specs and before the final coverage check.
[Priority: must]

### REQ-SKILL-014: sdd-plan milestone support
`sdd-plan` must support per-milestone plan files (REQ-MPLAN-001 through
REQ-MPLAN-004) when the project defines multiple milestones. For single-
milestone projects, the existing single-file behavior must be preserved.
[Priority: must]

### REQ-SKILL-015: sdd-replan milestone support
`sdd-replan` must work with per-milestone plan files, archiving and revising
the correct milestone's plan file based on which milestone's tasks are
affected.
[Priority: must]

### REQ-SKILL-016: Milestone-scoped staleness in plan skills
`sdd-plan` and `sdd-implement` must implement milestone-scoped staleness
detection (REQ-STALE-003) when reading per-milestone plan files, comparing
only against requirements and specs traced by that milestone's tasks.
[Priority: must]

### REQ-SKILL-017: sdd-migrate v2→v3 support
`sdd-migrate` must implement v2→v3 migration steps (REQ-MIG-009 through
REQ-MIG-014): version detection for v3, plan vocabulary rename, optional
multi-milestone split, capability report, v1→v3 sequential composition, and
finalization. The existing v1→v2 logic must remain unchanged.
(see RS-003)
[Priority: must]

### REQ-SKILL-018: sdd-review skill
A new `sdd-review` skill must be created at `skills/sdd-review/SKILL.md`
implementing the external review requirements (REQ-REV-001 through
REQ-REV-008): phase detection with phase-specific checklists, structured
report format, required inputs specification, bias disclosure, trigger
classification, scope boundaries against chunk-close/XSPEC/sdd-verify,
session-isolation confirmation, and scope-completeness checking.
(see RS-004)
[Priority: must]

<!-- REQ-SKILL-019..024: per-skill updates for the harness-hardening cycle
     (HARN and LINT domains). (see RS-008) -->

### REQ-SKILL-019: sdd-orchestrate hardening updates
`sdd-orchestrate` must implement the driver-side HARN requirements: the fix-loop
and replan re-entry caps (REQ-HARN-001, REQ-HARN-002), budget and write-scope
slots on every dispatch (REQ-HARN-004, REQ-HARN-020), `RETURN:` block parsing and
repair-packet composition (REQ-HARN-009, REQ-HARN-011, REQ-HARN-012), `VERDICT:`
branching (REQ-HARN-013), the chunk-verifier dispatch and per-chunk sequential
implement dispatch (REQ-HARN-014 through REQ-HARN-017), pruned re-dispatch state
and the orchestrator-owns-routing principle (REQ-HARN-018, REQ-HARN-019), the
three-command write-scope check with its gate format, commit ownership and
snapshot ordering (REQ-HARN-021 through REQ-HARN-026), and the gate text
additions (REQ-ORCH-034). Template changes land in
`skills/sdd-orchestrate/references/dispatch-templates.md` (pipeline, review, new
verifier template, `{repair_packet}` slot) and `references/fan-out.md` (leaf
template, verifier-before-merge sequencing, checkpoint application in §3e).
New procedure text lands in **new** references files — `references/write-scope.md`
(scope default table, three-command check, finding format, commit ownership,
snapshot ordering, v1 limitations) and `references/return-contract.md` (`RETURN:`
field-source mapping, repair-packet field sources, `VERDICT:` / `CHUNK_VERDICT:`
/ `SCOPE:` branching) — with short stubs/pointers in `SKILL.md`, so `SKILL.md`
stays within the REQ-LINT-007 size target. (see RS-008)
[Priority: must]

### REQ-SKILL-020: sdd-implement ledger, oscillation and checkpoint
`sdd-implement` must add the attempt ledger and `verified_do_not_touch` list
(REQ-HARN-006), the oscillation conditions in Step 3 stuck detection
(REQ-HARN-007), the circuit-break checkpoint format and its RETURN-field mapping
(REQ-HARN-008), and — when running as a dispatched leaf — the `RETURN:` block
(REQ-HARN-009, REQ-HARN-010) and budget self-count with `BUDGET_EXHAUSTED`
(REQ-HARN-005). Step 4 chunk close remains unchanged for the implementer
(REQ-HARN-014); standalone behavior is otherwise untouched. (see RS-008 Q1–Q3)
[Priority: must]

### REQ-SKILL-021: sdd-review verdict token
`sdd-review` must add the own-line `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT`
token to its report format (REQ-HARN-013) without changing the rest of the
report or its scope boundaries (REQ-REV-005, REQ-REV-006 — review is not the
chunk verifier). (see RS-008 Q4)
[Priority: must]

### REQ-SKILL-022: sdd-replan archive convention and checkpoint intake
`sdd-replan` must state the `-replan-` archive filename convention as a contract
(REQ-HARN-003), define the blocked-task note as the checkpoint slot with the
bounded format (REQ-HARN-008), and read that checkpoint in Step 1 as the stuck
state under orchestrate instead of relying on conversation context. (see RS-008
Q1)
[Priority: must]

### REQ-SKILL-023: sdd-skill-lint hardening checks
`tools/sdd-skill-lint.py` must implement the LINT domain (REQ-LINT-001 through
REQ-LINT-006): remediation text, warn tier, SKILL.md size check, backtick
`references/` path resolution, and the `REQUIRED` rows for the new contracts;
its self-test must cover each new check. (see RS-008 Q4)
[Priority: must]

### REQ-SKILL-024: sdd-orchestrate marker-4 prose to references/
`skills/sdd-orchestrate/SKILL.md` must move its marker-4-only prose to
`references/v4-workstreams.md` per REQ-LINT-007, with the `research_id` lint
guard and the superseding Q-IMPL entry in `docs/spec/ws-orchestration.md`. The
operator documentation (REQ-ORCH-020) should be updated to describe the new gate
signals (caps, budgets, `SCOPE:`, chunk verifier). `CLAUDE.md`'s SDD section
must gain **one short paragraph** introducing the new gate vocabulary — chunk
verifier, `RETURN:`, `SCOPE:`, `VERDICT:` / `CHUNK_VERDICT:` — and its
four-verification-layer bullet stays **unchanged** (the verifier is a second
executor of the chunk-close layer, REQ-HARN-014). (see RS-008 Q4)
[Priority: must]
