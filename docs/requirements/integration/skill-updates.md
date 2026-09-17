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

<!-- REQ-SKILL-HARNESSP2-NNN: per-skill updates for the harness-p2 cycle
     (TELEM, REDB, ARB, GC, EVAL domains + HARN/LINT additions). Workstream-
     prefixed ids per docs/spec/ws-ids.md (marker 4). (see RS-HARNESSP2-001) -->

### REQ-SKILL-HARNESSP2-001: sdd-orchestrate telemetry
`sdd-orchestrate` must implement the TELEM domain's driver side: the
per-dispatch record, enumerated budget parsing, orchestrator-only append after
each gate, `TELEMETRY: WRITE FAILED | OFF | .gitignore updated` gate lines, the
`.sdd/` third observation of the scope check, and the KICKOFF on/off choice
(REQ-TELEM-HARNESSP2-001 through -008). The record schema, field-source mapping
from the gate signals, the scorer-derivation table (REQ-EVAL-HARNESSP2-002) and
the timestamp procedure land in a **new** `references/telemetry.md`; `SKILL.md`
carries a short telemetry stub. Those two places plus `references/write-scope.md`
§3/§5 — which **reference** the `OUT .sdd/telemetry.jsonl (+k records …)`
finding string defined once in `references/telemetry.md` — are the only three
places under `skills/` allowed to name the path (REQ-LINT-HARNESSP2-002).
Operator documentation (`USAGE.md`, `CLAUDE.md`) may name it; the lint does not
scan those files (REQ-SKILL-HARNESSP2-008). No dispatch template may mention
`.sdd/`.
**Acceptance**: `references/telemetry.md` exists and resolves (REQ-LINT-004);
the stub is ≤ 10 lines; `tools/sdd-skill-lint.py` exits 0.
[Priority: must]

### REQ-SKILL-HARNESSP2-002: sdd-orchestrate red dispatch
`sdd-orchestrate` must add the `red` dispatch kind: the opt-in at the verify
gate (default off), a RED TEAM template in `references/dispatch-templates.md`
with the input contract, empty write scope, commit-ownership and budget slots
and the `RED_VERDICT:` return shape, the `Red team: enabled` slot on the verify
pipeline template, `^RED_VERDICT:` parsing and malformed rules in
`references/return-contract.md`, the exit rule and `accept (record)`
bookkeeping in `SKILL.md` §The gate, the `RED_BREAK` repair packet, the
`pending-red` → `pass` flip and its position-table row, and the one default red
re-run (REQ-REDB-HARNESSP2-001 through -009). Signal order at the verify gate
extends REQ-ORCH-034: `RETURN.status`, `SCOPE:`, `RED_VERDICT:`, `VERDICT:`.
**Acceptance**: the RED TEAM template carries `Budget:`, `Write scope:`,
`RETURN:` and `RED_VERDICT:`; the position table maps `pending-red` to verify;
lint exits 0 with the new `REQUIRED` rows (REQ-LINT-HARNESSP2-001).
[Priority: must]

### REQ-SKILL-HARNESSP2-003: sdd-orchestrate arbitration
`sdd-orchestrate` must implement the ARB domain in `references/loop-control.md`
(retained per-round tuple, class (b)/(c) rules, the reversal limitation, the
`REVIEW: CONTRADICTION` pause text and options, third-opinion resolution) with a
pointer in `SKILL.md` §The gate next to the `MALFORMED` family, and must extend
`references/write-scope.md` §3 and `tools/sdd-scope-check-selftest.py` with
section resolution of fix hunks (REQ-ARB-HARNESSP2-001 through -007).
Arbitration is default on.
**Acceptance**: `loop-control.md` §6 lists `REVIEW: CONTRADICTION` as the fourth
pause; the pause consumes no iteration in the fixture walkthrough; the scope
self-test gains the section-resolution and `.sdd/` scenarios and passes.
[Priority: must]

### REQ-SKILL-HARNESSP2-004: sdd-orchestrate gc cadence and snapshot base
`sdd-orchestrate` must run `tools/sdd-gc.py --report` at entry (one-line
summary before the workstream picker) and at DONE (full findings, `record |
ignore` routing into `verification.md` §Next Steps) per REQ-GC-HARNESSP2-005/006,
and must adopt the snapshot-base rule and limitation (c) of
REQ-HARN-HARNESSP2-001 in `references/write-scope.md` §3/§5 and in its worktree
provisioning step (provision at the branch tip the leaf is told to reach).
`write-scope.md` §3 must also specify the third, telemetry-specific observation
and §5 limitation (b)'s `.sdd/` exception (REQ-TELEM-HARNESSP2-005), each by
referencing the finding string defined in `references/telemetry.md` — §3 and
§5 are the only `write-scope.md` sections allowlisted for `\.sdd/` by
REQ-LINT-HARNESSP2-002. §6 gains the expected blocked-write path of
REQ-HARN-HARNESSP2-002.
**Acceptance**: `SKILL.md` §Transition and the entry step name the gc command;
`write-scope.md` §5 lists limitations (a), (b), (c); `.sdd/` appears in
`write-scope.md` only inside §3 and §5.
[Priority: must]

### REQ-SKILL-HARNESSP2-005: sdd-verify pending-red, accepted breaks and gc slot
`sdd-verify` must: read the `Red team: enabled` dispatch slot and write
`status: pending-red` in place of `pass` when set (REQ-REDB-HARNESSP2-008),
listing `pending-red` in its Phase Detection as a re-verification state;
document §Issues Found → Minor as the slot for `- Rn accepted at gate …` lines
and §Next Steps as the slot for `- gc <rule>: …` lines written by the
orchestrator (REQ-REDB-HARNESSP2-007, REQ-GC-HARNESSP2-006); and state in
§Verification Layers that red is a second executor of this layer (REQ-REDB-
HARNESSP2-002). Standalone behavior with red off is unchanged.
**Acceptance**: `sdd-verify/SKILL.md` Step 6 contains the `pending-red` rule
guarded by the slot; the four-layer table is unchanged; lint exits 0.
[Priority: must]

### REQ-SKILL-HARNESSP2-006: sdd-review Material `affects` key
`sdd-review` must add `affects REQ-…` (or `affects —`) to its Material finding
template line so every Critical and Material line carries the arbitration key
(REQ-ARB-HARNESSP2-008), changing nothing else in the report format
(REQ-REV-002) or scope boundaries (REQ-REV-005/006); `sdd-review` gains no red
or telemetry text.
**Acceptance**: the Material template line contains `affects`; a diff of
`sdd-review/SKILL.md` against v5 touches only that line and its example.
[Priority: should]

### REQ-SKILL-HARNESSP2-007: sdd-implement references split (Q-IMPL-083)
`skills/sdd-implement/SKILL.md` (525 lines, lint size warn accepted for v5 by
Q-IMPL-083) must move its Step 3 detail (attempt ledger, oscillation rule,
budget exhaustion, checkpoint composition) and the leaf return contract to
`skills/sdd-implement/references/` files, leaving stubs with resolving links —
the same operation the v5 cycle performed on `sdd-orchestrate` (REQ-LINT-007).
Guard: the `oscillation` and `BUDGET_EXHAUSTED` / `RETURN:` `REQUIRED` literals
(REQ-LINT-006) must remain in the stub, or their rows must be re-pointed, so the
lint stays green; standalone `sdd-implement` behavior is unchanged. (see
`docs/ws/default/verification.md` §Next Steps item 5; RS-HARNESSP2-001
Implications for Design)
**Acceptance**: `sdd-implement/SKILL.md` is ≤ 400 lines (no size warn); the
moved sections' stubs each contain a resolving `references/` link; `tools/
sdd-skill-lint.py` exits 0 and `--self-test` §7 still covers the re-pointed rows.
[Priority: must]

### REQ-SKILL-HARNESSP2-008: Operator documentation and CLAUDE.md
The operator documentation (`skills/sdd-orchestrate/USAGE.md`, REQ-ORCH-020)
must describe the new gate signals and choices — telemetry on/off and the
`TELEMETRY:` lines, the red opt-in, `RED_VERDICT:` and `pending-red`, the
`REVIEW: CONTRADICTION` pause and its four options, the gc summary at entry and
DONE — and `CLAUDE.md`'s SDD section must gain **one short paragraph** naming
them; its four-verification-layer bullet stays **unchanged** (red is a second
executor of the sdd-verify layer, REQ-REDB-HARNESSP2-002). Operator docs are outside
the `\.sdd/` lint row (REQ-LINT-HARNESSP2-002 scans `skills/*/SKILL.md` and
`skills/*/references/*.md` only), so `USAGE.md` and `CLAUDE.md` **may** name the
telemetry path; wherever they do, the non-read guarantee must be stated beside
it as "gitignored, orchestrator-only, never read by phase detection".
**Acceptance**: `USAGE.md` has a section per signal; `CLAUDE.md` diff is one
paragraph plus zero changes to the four-layer bullet.
[Priority: must]
