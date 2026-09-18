---
workstream: harness-p4
last_updated: 2026-09-18
---

# Traceability — harness-p4

Rows owned by the `harness-p4` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd-specs`, `sdd-implement` and `sdd-verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited.

`Verified` takes exactly three values (`docs/spec/ws-traceability.md` §Legal
`Verified` Cell Values). The DONE rule for this cycle (kickoff §Decided at
DISCUSS): every row reads `pass`; nothing closes as a deliberate `fail`, and an
item that cannot be exercised live is descoped at replan.

**Carried row.** REQ-ARB-HARNESSP3-001 is carried from `harness-p3`, where it
closed `fail` meaning *not exercised* (no fix loop regenerated its deliverable
between review rounds — `docs/ws/harness-p3/verification.md` §V3). It is listed
here under Workstream `harness-p4` for **live verification** in this cycle,
directed by REQ-ARB-HARNESSP4-001; its `harness-p3` row is left as history.
The regenerated aggregate therefore carries **both** rows for this id; the
`harness-p4` row is **authoritative** for the requirement and the `harness-p3`
row reads as history — a reader, `sdd-gc.py` and `sdd-verify` consult the
`harness-p4` row (REQ-ARB-HARNESSP4-001 §Acceptance).

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-ARB-HARNESSP3-001 | | harness-p4 | | | |
| REQ-ARB-HARNESSP4-001 | | harness-p4 | | | |
| REQ-ARB-HARNESSP4-002 | | harness-p4 | | | |
| REQ-ARB-HARNESSP4-003 | | harness-p4 | | | |
| REQ-CYCID-HARNESSP4-001 | | harness-p4 | | | |
| REQ-CYCID-HARNESSP4-002 | | harness-p4 | | | |
| REQ-HARN-HARNESSP4-001 | | harness-p4 | | | |
| REQ-HARN-HARNESSP4-002 | | harness-p4 | | | |
| REQ-HARN-HARNESSP4-003 | | harness-p4 | | | |
| REQ-HARN-HARNESSP4-004 | | harness-p4 | | | |
| REQ-HARN-HARNESSP4-005 | | harness-p4 | | | |
| REQ-HARN-HARNESSP4-006 | | harness-p4 | | | |
| REQ-HARN-HARNESSP4-007 | | harness-p4 | | | |
| REQ-LINT-HARNESSP4-001 | | harness-p4 | | | |
| REQ-LINT-HARNESSP4-002 | | harness-p4 | | | |
| REQ-REDB-HARNESSP4-001 | | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-001 | | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-002 | | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-003 | | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-004 | | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-005 | | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-006 | | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-007 | | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-008 | | harness-p4 | | | |
