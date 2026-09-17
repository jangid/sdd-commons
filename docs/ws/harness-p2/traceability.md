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
| REQ-ARB-HARNESSP2-001 | arbitrated-handoff.md | harness-p2 | by-hand fixture test_key_parse | loop-control.md §2a Retained per-round state | |
| REQ-ARB-HARNESSP2-002 | arbitrated-handoff.md | harness-p2 | by-hand fixtures class_b untouched section; file-level degradation | loop-control.md §2a Contradiction classes | |
| REQ-ARB-HARNESSP2-003 | arbitrated-handoff.md | harness-p2 | by-hand fixture test_class_c_regression | loop-control.md §2a Contradiction classes | |
| REQ-ARB-HARNESSP2-004 | arbitrated-handoff.md | harness-p2 | by-hand fixture test_reversal_not_detected | loop-control.md §2a Contradiction classes (a) | |
| REQ-ARB-HARNESSP2-005 | arbitrated-handoff.md | harness-p2 | tools/sdd-scope-check-selftest.py F8 | write-scope.md §3 Section resolution; selftest resolve_sections | |
| REQ-ARB-HARNESSP2-006 | arbitrated-handoff.md | harness-p2 | pause fixture byte-identical to spec; consumes no iteration; stage-gate only, iteration ≥ 2 | loop-control.md §2a REVIEW: CONTRADICTION pause, §6 | |
| REQ-ARB-HARNESSP2-007 | arbitrated-handoff.md | harness-p2 | by-hand fixture test_third_opinion_two_of_three | loop-control.md §2a Third opinion | |
| REQ-ARB-HARNESSP2-008 | arbitrated-handoff.md | harness-p2 | git diff c38922d -- sdd-review/SKILL.md: one line (Material template) | sdd-review/SKILL.md §Step 5 Material line | |
| REQ-EVAL-HARNESSP2-001 | evaluation.md | harness-p2 |  |  |  |
| REQ-EVAL-HARNESSP2-002 | evaluation.md | harness-p2 |  |  |  |
| REQ-EVAL-HARNESSP2-003 | evaluation.md | harness-p2 |  |  |  |
| REQ-EVAL-HARNESSP2-004 | evaluation.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-001 | drift-sweep.md | harness-p2 | tools/sdd-gc.py --self-test (exit codes, --help, clean fixture) | tools/sdd-gc.py (main, Gc, sweep_lint) | |
| REQ-GC-HARNESSP2-002 | drift-sweep.md | harness-p2 | tools/sdd-gc.py --self-test (sweeps 6/8/9/10/13/14; 7/11/12 in Chunk 5) | tools/sdd-gc.py (sweep_xlink, sweep_qimpl, sweep_index, sweep_plan_history; partial) | |
| REQ-GC-HARNESSP2-003 | drift-sweep.md | harness-p2 | tools/sdd-gc.py --self-test (counting rule D/B/D-B/0, exclusion cases, Q-IMPL-999 mutation; partial) | tools/sdd-gc.py (module docstring, Gc.is_countable, Gc.sweep_qimpl; partial) | |
| REQ-GC-HARNESSP2-004 | drift-sweep.md | harness-p2 | tools/sdd-gc.py --self-test (finding shape, WARN/INFO, summary last, empty-fix refusal) | tools/sdd-gc.py (Gc.flag, Gc.passthrough, Gc.run) | |
| REQ-GC-HARNESSP2-005 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-006 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-GC-HARNESSP2-007 | drift-sweep.md | harness-p2 |  |  |  |
| REQ-HARN-027 | telemetry.md | harness-p2 | git check-ignore exit 0 + git ls-files docs/ unchanged (amendment row; Verified inherits legacy pass) | .gitignore + SKILL.md §LOOP stub | |
| REQ-HARN-HARNESSP2-001 | dispatch-snapshot-base.md | harness-p2 | tools/sdd-scope-check-selftest.py F9 (3 assertions); replays test_catch_up_by_merge / test_ancestry_still_enforced / test_provision_at_branch_tip | write-scope.md §3 snapshot base rule + named-base observation, §5 (c); selftest observe()/render() | |
| REQ-HARN-HARNESSP2-002 | dispatch-snapshot-base.md | harness-p2 | write-scope.md §6 grep (i)–(iv) + expected; staged-write walkthrough = plain IN, blocked_writes [] | write-scope.md §6 scratchpad staging path | |
| REQ-LINT-HARNESSP2-001 | adversarial-verify.md, arbitrated-handoff.md | harness-p2 |  |  |  |
| REQ-LINT-HARNESSP2-002 | telemetry.md | harness-p2 |  |  |  |
| REQ-REDB-HARNESSP2-001 | adversarial-verify.md | harness-p2 | lint exit 0; fixture walkthrough test_opt_in_default_off / test_one_red_per_verify_return | sdd-orchestrate/SKILL.md §The gate (Red team); dispatch-templates.md §RED TEAM | |
| REQ-REDB-HARNESSP2-002 | adversarial-verify.md | harness-p2 | git diff c38922d -- sdd-review/SKILL.md empty; four-layer text unchanged | sdd-verify/SKILL.md §Verification Layers; dispatch-templates.md §RED TEAM | |
| REQ-REDB-HARNESSP2-003 | adversarial-verify.md | harness-p2 | fixture walkthrough test_template_slots_verbatim / test_red_write_is_out_and_reverted | dispatch-templates.md §RED TEAM (template, write-revert rule) | |
| REQ-REDB-HARNESSP2-004 | adversarial-verify.md | harness-p2 | grep: verification.md only in withheld/override rows | dispatch-templates.md §Slot contract (red team) | |
| REQ-REDB-HARNESSP2-005 | adversarial-verify.md | harness-p2 | fixture walkthrough test_parse_broken_two_findings / test_malformed_matrix / FOREIGN_TOKEN | return-contract.md §1, §Parsing (red table), §6a; dispatch-templates.md §Return contract (red team) | |
| REQ-REDB-HARNESSP2-006 | adversarial-verify.md | harness-p2 | fixture: reproduce n/a — BROKEN → BROKEN without reproduce | dispatch-templates.md §RED TEAM Rules; return-contract.md §6a | |
| REQ-REDB-HARNESSP2-007 | adversarial-verify.md | harness-p2 | fixture walkthrough test_gate_blocks_proceed_until_resolved | SKILL.md §The gate (signal 3b, Red team); loop-control.md §2a Red round | |
| REQ-REDB-HARNESSP2-008 | adversarial-verify.md | harness-p2 | Step 6 block md5 minus Next Steps == c38922d; pending-red grep in sdd-verify/sdd-replan/sdd-orchestrate | sdd-verify/SKILL.md Step 6 pending-red table; sdd-replan Phase Detection; SKILL.md position table; dispatch-templates.md {verify_red_only} | |
| REQ-REDB-HARNESSP2-009 | adversarial-verify.md | harness-p2 | fixture walkthrough test_red_break_packet | return-contract.md §3 RED_BREAK, §5; loop-control.md §2a Red round | |
| REQ-SKILL-HARNESSP2-001 | telemetry.md | harness-p2 | lint exit 0 (stub link); §LOOP stub = 10 lines; .sdd/ only in SKILL.md/telemetry.md/write-scope.md | SKILL.md §LOOP stub; references/telemetry.md | |
| REQ-SKILL-HARNESSP2-002 | adversarial-verify.md | harness-p2 | lint exit 0; --self-test exit 0 | SKILL.md; dispatch-templates.md; return-contract.md; loop-control.md; sdd-replan/SKILL.md | |
| REQ-SKILL-HARNESSP2-003 | arbitrated-handoff.md | harness-p2 | lint exit 0; grep REVIEW: CONTRADICTION in loop-control.md = 5 | SKILL.md §The gate pointer; loop-control.md §2a, §6 | |
| REQ-SKILL-HARNESSP2-004 | drift-sweep.md, dispatch-snapshot-base.md | harness-p2 | test_provision_at_branch_tip — snapshot half (gc half closes in Chunk 5) | SKILL.md §Pipeline subagent dispatch; dispatch-templates.md slot contract; write-scope.md §3/§5/§6 | |
| REQ-SKILL-HARNESSP2-005 | adversarial-verify.md | harness-p2 | Step 6 template diff vs c38922d: only ## Next Steps added after ## Recommendation | sdd-verify/SKILL.md Step 6 template + Section slots prose | |
| REQ-SKILL-HARNESSP2-006 | arbitrated-handoff.md | harness-p2 | grep -E M1:.*affects sdd-review/SKILL.md; one-line diff | sdd-review/SKILL.md Material line | |
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
