---
workstream: harness-p2
last_updated: 2026-09-17
---

# Traceability — harness-p2

Rows owned by the `harness-p2` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd-specs`, `sdd-implement` and `sdd-verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-ARB-HARNESSP2-001 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-ARB-HARNESSP2-002 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-ARB-HARNESSP2-003 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-ARB-HARNESSP2-004 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-ARB-HARNESSP2-005 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-ARB-HARNESSP2-006 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-ARB-HARNESSP2-007 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-ARB-HARNESSP2-008 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-EVAL-HARNESSP2-001 | evaluation.md | harness-p2 |  |  |  |
| REQ-EVAL-HARNESSP2-002 | evaluation.md | harness-p2 |  |  |  |
| REQ-EVAL-HARNESSP2-003 | evaluation.md | harness-p2 |  |  |  |
| REQ-EVAL-HARNESSP2-004 | evaluation.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-001 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-002 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-003 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-004 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-005 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-006 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-007 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-HARN-027 | telemetry.md | harness-p2 | git check-ignore exit 0 + git ls-files docs/ unchanged (amendment row; Verified inherits legacy pass) | .gitignore + SKILL.md §LOOP stub | |
| REQ-HARN-HARNESSP2-001 | dispatch-snapshot-base.md | harness-p2 | tools/sdd-scope-check-selftest.py F9 (3 assertions); replays test_catch_up_by_merge / test_ancestry_still_enforced / test_provision_at_branch_tip | write-scope.md §3 snapshot base rule + named-base observation, §5 (c); selftest observe()/render() | |
| REQ-HARN-HARNESSP2-002 | dispatch-snapshot-base.md | harness-p2 | write-scope.md §6 grep (i)–(iv) + expected; staged-write walkthrough = plain IN, blocked_writes [] | write-scope.md §6 scratchpad staging path | |
| REQ-LINT-HARNESSP2-001 | adversarial-verify.md, arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-LINT-HARNESSP2-002 | telemetry.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-001 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-002 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-003 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-004 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-005 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-006 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-007 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-008 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-009 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-SKILL-HARNESSP2-001 | telemetry.md | harness-p2 | lint exit 0 (stub link); §LOOP stub = 10 lines; .sdd/ only in SKILL.md/telemetry.md/write-scope.md | SKILL.md §LOOP stub; references/telemetry.md | |
| REQ-SKILL-HARNESSP2-002 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-SKILL-HARNESSP2-003 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-SKILL-HARNESSP2-004 | drift-sweep.md, dispatch-snapshot-base.md | harness-p2 | test_provision_at_branch_tip — snapshot half (gc half closes in Chunk 5) | SKILL.md §Pipeline subagent dispatch; dispatch-templates.md slot contract; write-scope.md §3/§5/§6 | |
| REQ-SKILL-HARNESSP2-005 | adversarial-verify.md | harness-p2 |  |  |  |
| REQ-SKILL-HARNESSP2-006 | arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-SKILL-HARNESSP2-007 | dispatch-snapshot-base.md | harness-p2 | lint exit 0 (warn set sdd-orchestrate, sdd-migrate; 20 files); --self-test §7; wc -l SKILL.md = 400; diff vs c38922d clean outside moved regions | sdd-implement/SKILL.md stubs; references/stuck-detection.md; references/leaf-return.md; Q-IMPL-083/-084 resolved notes | |
| REQ-SKILL-HARNESSP2-008 | telemetry.md | harness-p2 |  |  |  |
| REQ-TELEM-HARNESSP2-001 | telemetry.md | harness-p2 | verify walkthrough test_record_key_set_matches_schema | references/telemetry.md §2 | |
| REQ-TELEM-HARNESSP2-002 | telemetry.md | harness-p2 | tools/sdd-telemetry.py --self-test (budget grammar) | references/telemetry.md §2; tools/sdd-telemetry.py parse_budget_line | |
| REQ-TELEM-HARNESSP2-003 | telemetry.md | harness-p2 | no resume-class key in example record; zero .sdd/ hits in §Phase Detection blocks | references/telemetry.md §2 forbidden keys, §5 | |
| REQ-TELEM-HARNESSP2-004 | telemetry.md | harness-p2 | walkthroughs test_one_record_per_gated_dispatch, test_write_failure_is_one_gate_line, TELEMETRY: OFF once | references/telemetry.md §3; SKILL.md §LOOP stub, §KICKOFF, §The gate | |
| REQ-TELEM-HARNESSP2-005 | telemetry.md | harness-p2 | tools/sdd-scope-check-selftest.py F7 | references/telemetry.md §4; write-scope.md §3 third observation, §5 (b); selftest telemetry_snapshot/delta/revert | |
| REQ-TELEM-HARNESSP2-006 | telemetry.md | harness-p2 | grep every §Phase Detection block for .sdd/ = zero hits | references/telemetry.md §5 non-interference table | |
| REQ-TELEM-HARNESSP2-007 | telemetry.md | harness-p2 |  |  |  |
| REQ-TELEM-HARNESSP2-008 | telemetry.md | harness-p2 | git check-ignore -q .sdd/telemetry.jsonl exit 0; no docs/ws/*/telemetry*; git ls-files docs/ unchanged | .gitignore; references/telemetry.md §1 | |
| REQ-TELEM-HARNESSP2-009 | telemetry.md | harness-p2 | tools/sdd-telemetry.py --self-test | tools/sdd-telemetry.py | |
