---
workstream: harness-p4
last_updated: 2026-09-19
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
| REQ-ARB-HARNESSP3-001 | arbitrated-handoff.md | harness-p4 | | | |
| REQ-ARB-HARNESSP4-001 | arbitrated-handoff.md | harness-p4 | | | |
| REQ-ARB-HARNESSP4-002 | arbitrated-handoff.md | harness-p4 | | | |
| REQ-ARB-HARNESSP4-003 | arbitrated-handoff.md | harness-p4 | | | |
| REQ-CYCID-HARNESSP4-001 | cycle-identity.md | harness-p4 | | | |
| REQ-CYCID-HARNESSP4-002 | cycle-identity.md | harness-p4 | | | |
| REQ-HARN-HARNESSP4-001 | harness-commit-fidelity.md | harness-p4 | tools/sdd-skill-lint.py --self-test (COMMIT: row mutation); plan Chunk 0 task 8 walkthroughs (a),(c),(d) | skills/sdd-orchestrate/references/write-scope.md §7a; references/loop-control.md §5 items 2b/8; SKILL.md §The gate; USAGE.md §7b; CLAUDE.md §Gate vocabulary | |
| REQ-HARN-HARNESSP4-002 | harness-commit-fidelity.md | harness-p4 | plan Chunk 0 task 8 walkthrough (b) — drift warning, no COMMIT: term | skills/sdd-orchestrate/references/write-scope.md §7a (observed-writes-only expected); references/return-contract.md §1 return-drift warning | |
| REQ-HARN-HARNESSP4-003 | harness-commit-fidelity.md | harness-p4 | plan Chunk 0 task 8 walkthrough (d) — grep shows two members only; fixtures C3–C5 land in Chunk 1 | skills/sdd-orchestrate/references/fan-out.md §3a.v step a2, §3b merge-step clause | |
| REQ-HARN-HARNESSP4-004 | harness-write-scope.md | harness-p4 | | | |
| REQ-HARN-HARNESSP4-005 | harness-write-scope.md | harness-p4 | | | |
| REQ-HARN-HARNESSP4-006 | harness-commit-fidelity.md | harness-p4 | | | |
| REQ-HARN-HARNESSP4-007 | harness-chunk-verifier.md | harness-p4 | | | |
| REQ-LINT-HARNESSP4-001 | skill-lint-v5.md | harness-p4 | | | |
| REQ-LINT-HARNESSP4-002 | skill-lint-v5.md | harness-p4 | tools/sdd-skill-lint.py --self-test (COMMIT: rows stripped → exit 1 with fix; SCOPE:-only negative control) | tools/sdd-skill-lint.py REQUIRED rows for loop-control.md and SKILL.md | |
| REQ-REDB-HARNESSP4-001 | adversarial-verify.md | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-001 | telemetry.md | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-002 | telemetry.md | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-003 | telemetry.md | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-004 | telemetry.md | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-005 | telemetry.md | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-006 | telemetry.md | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-007 | telemetry.md | harness-p4 | | | |
| REQ-TELEM-HARNESSP4-008 | telemetry.md | harness-p4 | | | |
