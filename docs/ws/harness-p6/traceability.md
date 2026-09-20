---
workstream: harness-p6
last_updated: 2026-09-20
---

# Traceability — harness-p6

Rows owned by the `harness-p6` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd-specs`, `sdd-implement` and `sdd-verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited.

`Verified` takes the values of `docs/spec/ws-traceability.md` §Legal `Verified`
Cell Values — `pass | fail | pending-red | descoped`. The DONE rule for this
cycle (kickoff §Decided at DISCUSS): every row reads `pass`; nothing closes as a
deliberate `fail`, and an item that cannot be exercised is descoped at replan.

**Terminal cycle.** `harness-p6` is the terminal cycle of the harness-hardening
series (kickoff §Decided at DISCUSS). No row may be closed by carrying it to a
successor workstream; an item too large to fix triggers a replan inside this
cycle. There are no carried rows from a previous workstream.

**Confidence carried from RS-HARNESSP6-001.** The three L2 rows
(REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-001, REQ-ORCH-HARNESSP6-002) rest on
the findings' **Medium**-confidence Q4: the cluster rule reuses an exercised
parser but has never been replayed against a real finding set, and L2's firing
rate is unmeasured. Their verification should not be treated as routine.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-GC-HARNESSP6-001 | drift-sweep.md | harness-p6 | | | |
| REQ-GC-HARNESSP6-002 | drift-sweep.md | harness-p6 | | | |
| REQ-GC-HARNESSP6-003 | drift-sweep.md | harness-p6 | | | |
| REQ-GC-HARNESSP6-004 | drift-sweep.md | harness-p6 | | | |
| REQ-HARN-HARNESSP6-001 | harness-write-scope.md | harness-p6 | | | |
| REQ-HARN-HARNESSP6-002 | harness-loop-control.md | harness-p6 | | | |
| REQ-LINT-HARNESSP6-001 | skill-lint-v5.md | harness-p6 | | | |
| REQ-LINT-HARNESSP6-002 | skill-lint-v5.md | harness-p6 | | | |
| REQ-LINT-HARNESSP6-003 | skill-lint-v5.md | harness-p6 | | | |
| REQ-ORCH-HARNESSP6-001 | harness-loop-control.md | harness-p6 | | | |
| REQ-ORCH-HARNESSP6-002 | harness-loop-control.md | harness-p6 | | | |
| REQ-PLAN-HARNESSP6-001 | plan-management.md | harness-p6 | | | |
| REQ-REQ-HARNESSP6-001 | requirements-artifacts.md | harness-p6 | | | |
