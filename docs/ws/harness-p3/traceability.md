---
workstream: harness-p3
last_updated: 2026-09-18
---

# Traceability — harness-p3

Rows owned by the `harness-p3` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd-specs`, `sdd-implement` and `sdd-verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-ARB-HARNESSP3-001 | arbitrated-handoff.md | harness-p3 |  |  |  |
| REQ-CYCID-HARNESSP3-001 | cycle-identity.md | harness-p3 |  |  |  |
| REQ-CYCID-HARNESSP3-002 | cycle-identity.md | harness-p3 |  |  |  |
| REQ-GC-HARNESSP3-001 | drift-sweep.md | harness-p3 |  |  |  |
| REQ-HARN-HARNESSP3-001 | harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F10 | `tools/sdd-scope-check-selftest.py` (`observe`, `content_hashes`, `ambiguous_set`, `snapshot`), `skills/sdd-orchestrate/references/write-scope.md` §3, §5 |  |
| REQ-HARN-HARNESSP3-002 | harness-return-contract.md, harness-chunk-verifier.md, adversarial-verify.md | harness-p3 | Chunk 2 task 4 template-conformance walkthrough (inline; no executable fixture — skill text) | `skills/sdd-orchestrate/references/dispatch-templates.md` §CHUNK VERIFIER, §RED TEAM, §REVIEW (fenced bodies) |  |
| REQ-HARN-HARNESSP3-003 | harness-return-contract.md | harness-p3 | Chunk 2 task 8 replay: prose `budget_consumed` fixtures pause; missing-only-`ledger` fixture warns | `skills/sdd-orchestrate/references/return-contract.md` §1 Parsing and malformed returns |  |
| REQ-HARN-HARNESSP3-004 | harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F11 | `skills/sdd-orchestrate/references/write-scope.md` §2 (specs row) |  |
| REQ-HARN-HARNESSP3-005 | harness-return-contract.md | harness-p3 | Chunk 2 task 6 contract read (no executable fixture — packet-shape rule) | `skills/sdd-orchestrate/references/return-contract.md` §3 (Rules, out-of-fix-scope bullet) |  |
| REQ-REDB-HARNESSP3-001 | harness-return-contract.md, adversarial-verify.md | harness-p3 | Chunk 2 task 8 replay: both observed red breaks narrow past `all`; negative control still routes `all` | `skills/sdd-orchestrate/references/return-contract.md` §5 (step 1'), §3 (`RED_BREAK` table row) |  |
| REQ-REDB-HARNESSP3-002 | adversarial-verify.md | harness-p3 |  |  |  |
| REQ-REDB-HARNESSP3-003 | adversarial-verify.md, ws-traceability.md | harness-p3 |  |  |  |
| REQ-REDB-HARNESSP3-004 | adversarial-verify.md, harness-write-scope.md, milestone-plans.md | harness-p3 |  |  |  |
| REQ-SKILL-HARNESSP3-001 | skill-updates.md | harness-p3 |  |  |  |
| REQ-TELEM-HARNESSP3-001 | telemetry.md | harness-p3 |  |  |  |
| REQ-TELEM-HARNESSP3-002 | telemetry.md | harness-p3 |  |  |  |
| REQ-WS-HARNESSP3-001 | ws-traceability.md, harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F12 | `skills/sdd-orchestrate/references/write-scope.md` §2, §7, §9, `skills/sdd-orchestrate/SKILL.md` §The gate, `skills/sdd-orchestrate/references/fan-out.md` §3e, `skills/sdd-{requirements,specs,implement,verify}/SKILL.md` |  |
