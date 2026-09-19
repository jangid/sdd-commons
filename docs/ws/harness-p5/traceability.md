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
| REQ-ARB-HARNESSP3-001 | | harness-p5 | | | |
| REQ-ARB-HARNESSP4-001 | | harness-p5 | | | |
| REQ-ARB-HARNESSP5-001 | | harness-p5 | | | |
| REQ-ARB-HARNESSP5-002 | | harness-p5 | | | |
| REQ-ARB-HARNESSP5-003 | | harness-p5 | | | |
| REQ-HARN-HARNESSP5-001 | | harness-p5 | | | |
| REQ-HARN-HARNESSP5-002 | | harness-p5 | | | |
| REQ-LINT-HARNESSP5-001 | | harness-p5 | | | |
| REQ-LINT-HARNESSP5-002 | | harness-p5 | | | |
| REQ-LINT-HARNESSP5-003 | | harness-p5 | | | |
| REQ-QIMPL-HARNESSP5-001 | | harness-p5 | | | |
| REQ-QIMPL-HARNESSP5-002 | | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-001 | | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-002 | | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-003 | | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-004 | | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-005 | | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-006 | | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-007 | | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-008 | | harness-p5 | | | |
| REQ-WS-HARNESSP5-001 | | harness-p5 | | | |
| REQ-WS-HARNESSP5-002 | | harness-p5 | | | |
