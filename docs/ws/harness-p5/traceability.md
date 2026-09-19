---
workstream: harness-p5
last_updated: 2026-09-20
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
| REQ-ARB-HARNESSP3-001 | arbitrated-handoff.md §Offline Arbitration Fixture | harness-p5 | Chunk 2 task 4: `python3 tools/sdd-scope-check-selftest.py --self-test` exits 0 (27/27 scenarios). Scenario A1 replays the harness-p4 regeneration case offline and discriminates the two readings: the diff-based reading yields `class b` with two annotated keys (`§Conventions`, `§Verification Hand-off`), the provenance reading `(file, *)` yields no token; mutations A1m-i / A1m-ii both fail A1, so the assertion cannot pass vacuously | tools/fixtures/arbitration-harness-p4-regen-2026-09-19/ (git capture: `before.md` = 82d0af0:docs/ws/harness-p4/plan.md, `after.md` = 3772574:docs/ws/harness-p4/plan.md, sha256 of all five files recorded in tools/fixtures/README.md); tools/sdd-scope-check-selftest.py scenario A1 with `arbitrate()` / `parse_round()`; docs/spec/arbitrated-handoff.md §Offline Arbitration Fixture, §Acceptance Criteria | |
| REQ-ARB-HARNESSP4-001 | arbitrated-handoff.md §Offline Arbitration Fixture | harness-p5 | Chunk 2 task 4: `python3 tools/sdd-scope-check-selftest.py --self-test` exits 0 (27/27 scenarios), covering the acceptance re-stated under Q-REQ-P5-A on the same offline capture — A1 (`class b`, two annotated keys; no token under the provenance reading), A2 (no token either way) and A3 (`class b`, one key) — replacing the non-discriminating live O1 exercise this row carried from harness-p4 | tools/fixtures/arbitration-harness-p4-regen-2026-09-19/ (git capture of 82d0af0 → 3772574 of docs/ws/harness-p4/plan.md; per-file sha256 in tools/fixtures/README.md); tools/sdd-scope-check-selftest.py scenarios A1–A3 (plus mutations A1m-i / A1m-ii); docs/spec/arbitrated-handoff.md §Offline Arbitration Fixture, §Acceptance Criteria | |
| REQ-ARB-HARNESSP5-001 | arbitrated-handoff.md §W_N Includes Regeneration Writes | harness-p5 | Chunk 1 task 4: `grep -n 'byte-identical' docs/spec/arbitrated-handoff.md skills/sdd-orchestrate/references/loop-control.md` hits both with matching wording | docs/spec/arbitrated-handoff.md §`W_N` Includes Regeneration Writes; skills/sdd-orchestrate/references/loop-control.md §2a | |
| REQ-ARB-HARNESSP5-002 | arbitrated-handoff.md §Offline Arbitration Fixture | harness-p5 | Chunk 2 task 4: `python3 tools/sdd-scope-check-selftest.py --self-test` exits 0 with scenarios A1 (class b, two annotated keys; provenance column no token), A2 (no token either way), A3 (class b, one key) and mutations A1m-i / A1m-ii both failing A1 | tools/fixtures/arbitration-harness-p4-regen-2026-09-19/ (git capture, shas 82d0af0 and 3772574; sha256 per file in tools/fixtures/README.md); tools/sdd-scope-check-selftest.py `arbitrate()`, `parse_round()`, scenarios A1–A3, A1m-i, A1m-ii; docs/spec/arbitrated-handoff.md §Offline Arbitration Fixture, §Acceptance Criteria | |
| REQ-ARB-HARNESSP5-003 | arbitrated-handoff.md §Retained Per-Round State | harness-p5 | Chunk 1 task 4 desk check: the key table's `section` row and `references/loop-control.md` §2a state the same leading-ordinal strip; Open Question 3 reads closed (Chunk 2 task 4 exercises it on A1–A3) | docs/spec/arbitrated-handoff.md §Retained Per-Round State key table (`section` row), §Open Questions item 3 | |
| REQ-GC-HARNESSP5-001 | drift-sweep.md §Row-Drop Safety | harness-p5 | Chunk 4 task 6: `python3 tools/sdd-gc.py --self-test` exits 0 with the three row-drop assertions (an escaped-pipe `Test` cell round-trips through `--fix traceability-aggregate` byte-for-byte and raises no finding; a five-cell row raises exactly one `[traceability-rowdrop]` fail naming `<file>:<line>`; `--fix traceability-rowdrop` exits 2); `python3 tools/sdd-gc.py --report` exits 0 with no `traceability-rowdrop` finding and `grep -c '&#124;' docs/requirements/traceability.md` prints 2 | tools/sdd-gc.py: `CELL_SPLIT_RE` / `table_cells()` (unescaped-pipe split), `trace_rows(text, bad)` (expected cell count from the table header), `Gc.checked_rows()` + `ROWDROP_FIX`, rule id `traceability-rowdrop` in `GC_RULES` (absent from `FIXABLE`), docstring sweep 12 row and `HELP_EPILOG` |  |
| REQ-HARN-HARNESSP5-001 | harness-loop-control.md §Plan Completion Ownership Under Orchestration | harness-p5 | | | |
| REQ-HARN-HARNESSP5-002 | harness-commit-fidelity.md §Comparand Table | harness-p5 | | | |
| REQ-LINT-HARNESSP5-001 | skill-lint-v5.md §Size Warn-Clean Baseline | harness-p5 | | | |
| REQ-LINT-HARNESSP5-002 | skill-lint-v5.md §Size Warn-Clean Baseline | harness-p5 | | | |
| REQ-LINT-HARNESSP5-003 | telemetry.md §Moved Sections; telemetry-reader.md | harness-p5 | | | |
| REQ-QIMPL-HARNESSP5-001 | deviation-protocol.md §Fold-In Status Note | harness-p5 | | | |
| REQ-QIMPL-HARNESSP5-002 | deviation-protocol.md §Spec-Reference Integrity | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-001 | telemetry.md §Writer | harness-p5 | Chunk 3 task 4: `python3 tools/sdd-telemetry.py --self-test` exits 0 (`test_schema_table_agrees` included, no key added); `--lint --file tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl` still lists `seq` 21, 24, 27 as `[cross-field]`; `python3 tools/sdd-skill-lint.py` exits 0 | docs/spec/telemetry.md §Writer rule (i); skills/sdd-orchestrate/references/telemetry.md §3 rule (i); skills/sdd-orchestrate/SKILL.md §Telemetry | |
| REQ-TELEM-HARNESSP5-002 | telemetry-reader.md §Implication-Derived `expected` | harness-p5 | Chunk 4 task 6: `--self-test` case (1) — three stage-level `fix` records with no chunk record yield `implied.pipeline` 0; on the frozen p4 fixture `summarize` reports pipeline 8 vs 8 (0 missing) for the `(implement, chunk null)` session and the p3 fixture's `expected 39` / 19 missing are unchanged (both fixture sha256 asserted before and after) | tools/sdd-telemetry.py `session_rows()` — the implement group loop keyed on `chunk_key != "null"` |  |
| REQ-TELEM-HARNESSP5-003 | telemetry-reader.md §Schema Lint | harness-p5 | Chunk 4 task 6: `--self-test` case (2) — `v: 1` + equal heads + `files_written_n: 3` raises no finding, the same shape at `v: 2` with a null `commit.token` raises one, and no `migration` marker is stamped; on the p4 fixture `--lint` raises no equal-heads finding (65 to 62 findings, `seq` 2/4/6 clean) | tools/sdd-telemetry.py `lint_records()` — the equal-heads cross-field rule guarded by `r.get("v") == 2` |  |
| REQ-TELEM-HARNESSP5-004 | telemetry-reader.md §Out-of-Loop Reader | harness-p5 | Chunk 4 task 6: `--self-test` case (3) — `v_admitted()` accepts 2 and rejects `2.0` / `True` / `"2"`; a `v: 2.0` record is skipped and counted by `summarize` (`skipped: 1 unknown-schema record(s)`) and raises `[type] v` under `--lint`; `grep -c 'ADMITTED_V' tools/sdd-telemetry.py` shows the membership test in the one helper | tools/sdd-telemetry.py `v_admitted()` (with `V_ADMITTED_TEXT`), called from `load()` and `_check_value()`'s `v` branch |  |
| REQ-TELEM-HARNESSP5-005 | telemetry.md §Writer | harness-p5 | Chunk 3 task 4: `summarize --file tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl` prints `COMMIT: INCOMPLETE (accepted): 0`; `--self-test` exits 0 with the updated `COMMIT: INCOMPLETE (accepted): 1` assertion and `test_schema_table_agrees` still passing (no `commit.amended` key) | docs/spec/telemetry.md §Writer `commit` source + §`commit` Group; docs/spec/telemetry-reader.md §Records-vs-Expected + §Fixture-Based Test Contract; skills/sdd-orchestrate/references/telemetry.md §3 `commit` source; tools/sdd-telemetry.py `summarize` COMMIT line | |
| REQ-TELEM-HARNESSP5-006 | telemetry-reader.md §Schema Lint | harness-p5 | Chunk 4 task 6: `--self-test` case (4) — a type finding on `seq` 5 and a cross-field finding on `seq` 2 render in the order 2, 5; case (5) — the frozen p3 fixture's finding set is unchanged, compared order-insensitively as sha256 over the sorted finding lines (`FIXTURE_LINT_SORTED_SHA256`) | tools/sdd-telemetry.py `sort_findings()`, applied at the end of `lint_records()` across all three passes |  |
| REQ-TELEM-HARNESSP5-007 | telemetry-reader.md §Fixture-Based Test Contract | harness-p5 | | | |
| REQ-TELEM-HARNESSP5-008 | telemetry-reader.md §Schema Lint | harness-p5 | | | |
| REQ-WS-HARNESSP5-001 | ws-traceability.md §Legal `Verified` Cell Values | harness-p5 | Chunk 1 task 4: `python3 tools/sdd-skill-lint.py` exits 0; `python3 tools/sdd-gc.py --report` raises no new finding attributable to a `descoped` cell (`trace-empty` checks empty cells only, no value vocabulary) | docs/spec/ws-traceability.md §Legal `Verified` Cell Values; skills/sdd-verify/SKILL.md Step 3b/6 traceability block; skills/sdd-requirements/SKILL.md Step 5 | |
| REQ-WS-HARNESSP5-002 | ws-traceability.md §Legal `Verified` Cell Values | harness-p5 | | | |
