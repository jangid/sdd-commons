---
workstream: harness-p5
last_updated: 2026-09-19
---

# Traceability — harness-p5

Rows owned by the `harness-p5` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd-specs`, `sdd-implement` and `sdd-verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited.

`Verified` takes the values of `docs/spec/ws-traceability.md` §Legal `Verified`
Cell Values — `pass | fail | pending-red`, plus `descoped` once
REQ-WS-HARNESSP5-001 lands (limited to rows carried from a previous workstream).
The DONE rule for this cycle (kickoff §Decided at DISCUSS): every row reads
`pass`; nothing closes as a deliberate `fail`, and an item that cannot be
exercised is descoped at replan.

**Carried rows.** REQ-ARB-HARNESSP3-001 and REQ-ARB-HARNESSP4-001 are carried
from `harness-p4`, where their `Verified` cells were left **empty**: the live O1
exercise was non-discriminating (`docs/ws/harness-p4/verification.md` §Open
Questions, §Next Steps), and no legal value fit. They are listed here under
Workstream `harness-p5` for closure on the **deterministic offline fixture** of
REQ-ARB-HARNESSP5-002 (scenarios A1–A3), with REQ-ARB-HARNESSP4-001's acceptance
re-stated under Q-REQ-P5-A; their `harness-p3` (`fail`) and `harness-p4`
(`descoped`, once REQ-WS-HARNESSP5-002's bookkeeping commit lands) rows are left
as history. The regenerated aggregate therefore carries three rows for
REQ-ARB-HARNESSP3-001 and two for REQ-ARB-HARNESSP4-001; the `harness-p5` rows
are **authoritative** for both requirements — a reader, `sdd-gc.py` and
`sdd-verify` consult them for the DONE rule.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-ARB-HARNESSP3-001 | arbitrated-handoff.md §Offline Arbitration Fixture | harness-p5 | | | |
| REQ-ARB-HARNESSP4-001 | arbitrated-handoff.md §Offline Arbitration Fixture | harness-p5 | | | |
| REQ-ARB-HARNESSP5-001 | arbitrated-handoff.md §W_N Includes Regeneration Writes | harness-p5 | | | |
| REQ-ARB-HARNESSP5-002 | arbitrated-handoff.md §Offline Arbitration Fixture | harness-p5 | | | |
| REQ-ARB-HARNESSP5-003 | arbitrated-handoff.md §Retained Per-Round State | harness-p5 | | | |
| REQ-HARN-HARNESSP5-001 | harness-loop-control.md §Plan Completion Ownership Under Orchestration | harness-p5 | | | |
| REQ-HARN-HARNESSP5-002 | harness-commit-fidelity.md §Comparand Table | harness-p5 | | | |
| REQ-LINT-HARNESSP5-001 | skill-lint-v5.md §Size Warn-Clean Baseline | harness-p5 | | | |
| REQ-LINT-HARNESSP5-002 | skill-lint-v5.md §Size Warn-Clean Baseline | harness-p5 | | | |
| REQ-LINT-HARNESSP5-003 | telemetry.md §Moved Sections; telemetry-reader.md | harness-p5 | | | |
| REQ-QIMPL-HARNESSP5-001 | deviation-protocol.md §Fold-In Status Note | harness-p5 | | | |
| REQ-QIMPL-HARNESSP5-002 | deviation-protocol.md §Spec-Reference Integrity | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-001 | telemetry.md §Writer | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-002 | telemetry-reader.md §Implication-Derived `expected` | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-003 | telemetry-reader.md §Schema Lint | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-004 | telemetry-reader.md §Out-of-Loop Reader | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-005 | telemetry.md §Writer | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-006 | telemetry-reader.md §Schema Lint | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-007 | telemetry-reader.md §Fixture-Based Test Contract | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-008 | telemetry-reader.md §Schema Lint | harness-p5 | | | |
| REQ-WS-HARNESSP5-001 | ws-traceability.md §Legal `Verified` Cell Values | harness-p5 | | | |
| REQ-WS-HARNESSP5-002 | ws-traceability.md §Legal `Verified` Cell Values | harness-p5 | | | |
