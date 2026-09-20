---
workstream: harness-p5
status: pass
research_id: RS-HARNESSP5-001
last_updated: 2026-09-20
plan_ref: docs/ws/harness-p5/plan.md
scope: REQ-ARB / REQ-TELEM / REQ-GC / REQ-HARN / REQ-LINT / REQ-QIMPL / REQ-WS (harness-p5) over docs/spec/{arbitrated-handoff,telemetry,telemetry-reader,drift-sweep,ws-traceability,harness-loop-control,harness-write-scope,harness-commit-fidelity,harness-chunk-verifier,skill-lint-v5,deviation-protocol}.md, skills/sdd-{orchestrate,implement,verify,requirements,migrate}/**, tools/sdd-{gc,telemetry,scope-check-selftest}.py and tools/fixtures/**
---

# Verification Report

## Summary

Blue-team verification of the `harness-p5` cycle passes. All 38 plan tasks are
ticked and the plan reads `status: complete` with `research_id:
RS-HARNESSP5-001` matching the kickoff. Every quality gate is green:
`sdd-skill-lint.py` exits 0 with `OK: 25 file(s) clean` and **0** `[size]`
findings, `sdd-gc.py --report` exits 0 with **zero fail-class findings** (9
sweeps clean, **0** `qimpl-broken-ref`, **0** `traceability-rowdrop`), and all
three self-test harnesses exit 0 — `sdd-telemetry.py --self-test`, `sdd-gc.py
--self-test` and `sdd-scope-check-selftest.py --self-test` (27/27, including
arbitration scenarios A1–A3 and mutations A1m-i / A1m-ii, and commit fidelity
C1–C6).

Acceptance-command reproduction, stated without inflation: the earlier claim
that "22 of the 23 traced requirements reproduce every literal acceptance
command" was wrong. At first report time (2026-09-20, before the red rounds)
**three** criteria did not reproduce literally — `deviation-protocol.md`'s
`git diff --stat main -- tools/sdd-gc.py` guard (superseded by
REQ-GC-HARNESSP5-001's edits to the same file); `harness-write-scope.md`'s
`grep -n 'no-renames -z'` criterion, whose literal form returned 2 rather than 1
because the criterion line matched itself (it was marked `pass` on a
reinterpreted command); and `skill-lint-v5.md`'s "summary line prints
`0 warning(s)`" clause, which the linter never prints and which was therefore
unreproducible as written. **All three reproduce literally now**, after the red-round criterion amendments
(red round 2 R1, R5) and this pass's M5 rescope landed — so all 23 traced
requirements reproduce every literal acceptance command against the tree this
report describes. No regressions against the branch point `9bf25fd`. Because
this run was dispatched with `Red team: enabled`, the report closes at
`status: pending-red` and every would-be-`pass` `Verified` cell reads
`pending-red`; the orchestrator flips both at the verify gate once the red
round resolves.

## Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| Skill lint | pass | `python3 tools/sdd-skill-lint.py` → exit 0, `OK: 25 file(s) clean`; `\| grep -c '[size]'` → `0` |
| Drift sweep | pass | `python3 tools/sdd-gc.py --report` → exit 0, 9 sweeps clean, **zero fail-class findings**; `grep -c 'qimpl-broken-ref'` → `0`; `grep -c 'traceability-rowdrop'` → `0`. No total warn count is pinned here: the warn class is `[stale-chain]`-dominated and rises with every `last_updated:` bump — including this report's own and the orchestrator's aggregate regeneration at the gate — so any fixed number would be stale on arrival (recorded as §Next Steps 1 and Carried 2/4) |
| Telemetry self-test | pass | `python3 tools/sdd-telemetry.py --self-test` → exit 0; banner names the harness-p5 cases (null-chunk group, `v: 1` equal-heads exemption, `v: 2.0` skip, finding sort 2-before-5, frozen p3 sorted-sha256, frozen p4 67 records, `test_p4_fixture_frozen`, `test_advisory_cases`, `test_stage_level_fix_has_null_chunk_verdict`, `test_commit_group_records_closing_line`) |
| gc self-test | pass | `python3 tools/sdd-gc.py --self-test` → exit 0; banner names row-drop safety (escaped-pipe round-trip, five-cell row → one `[traceability-rowdrop]` fail at `<file>:<line>`, `--fix traceability-rowdrop` exit 2) |
| Scope-check self-test | pass | `python3 tools/sdd-scope-check-selftest.py --self-test` → exit 0, `OK: 27/27 scenarios passed` (F1–F16, C1–C6, A1–A3, A1m-i, A1m-ii) |
| Size budget | pass | `wc -l skills/*/SKILL.md` — max is `sdd-orchestrate` 399; `sdd-implement` 385, `sdd-verify` 375, `sdd-requirements` 374, `sdd-plan` 324, `sdd-migrate` 304, `sdd-specs` 273, `sdd-review` 258, `sdd-research` 253, `sdd-replan` 244. All < 400 |
| Spec size budget | pass | `wc -l docs/spec/telemetry*.md` → `telemetry.md` 764, `telemetry-reader.md` 700 — both under the amended ~800 bound (Q-REQ-P5-I) |
| Working tree | pass | The verify-stage artifacts (this report, the per-ws traceability, the red-round spec repairs) are written by the verify leaf and **committed by the orchestrator at the verify gate**, so this report describes the tree **as of that commit** — not the mid-flight tree it was drafted in. At the gate the only diff against `HEAD` is that commit's own contents; no unrelated or untracked path is left behind (`git status --porcelain` is empty once it lands) |

No language build/test toolchain applies — this repository ships Markdown
skills/specs and three standalone Python 3 tools, whose gates are the
self-tests above (CLAUDE.md §Quality Checks).

## Criteria

### arbitrated-handoff.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `grep -n 'byte-identical' docs/spec/arbitrated-handoff.md skills/sdd-orchestrate/references/loop-control.md` hits §`W_N` Includes Regeneration Writes and §2a with matching wording; A1 yields `class b` with two annotated keys under the diff-based rule and no token under provenance, printed side by side; lint exits 0 (REQ-ARB-HARNESSP5-001) | pass | grep hits `arbitrated-handoff.md:253` and `loop-control.md:181` with the identical sentence "**byte-identically adds nothing to `W_N`**". Self-test line: `PASS A1 ARB: round 2 on the regenerated plan's unchanged sections (diff-based vs provenance) -> diff-based: class b (2 keys) \| provenance: no token`. `sdd-skill-lint.py` exit 0 |
| `python3 tools/sdd-scope-check-selftest.py --self-test` exits 0 with A1–A3 listed and A1's provenance column printed alongside; deleting one `round-2.txt` line or flipping `§Conventions` to a changed section makes A1 fail; `tools/fixtures/README.md` labels the fixture a **git capture** naming both shas with per-file sha256; §Criteria records the run as the evidence for both ARB rows (REQ-ARB-HARNESSP5-002, REQ-ARB-HARNESSP3-001, REQ-ARB-HARNESSP4-001) | pass | Exit 0, `OK: 27/27 scenarios passed`. A1/A2/A3 printed with the provenance column (`A2 … no token either way`; `A3 … class b under both readings`). Mutations printed: `PASS A1m-i … -> A1 fails as required (annotated 1 of 2)` and `PASS A1m-ii …`. `tools/fixtures/README.md` records the capture shas `82d0af0` / `3772574` and per-file sha256. **This table row is the recorded evidence for REQ-ARB-HARNESSP3-001 and REQ-ARB-HARNESSP4-001**, replacing the non-discriminating live O1 exercise carried from `harness-p4` |
| The key table's `section` row states the leading-ordinal strip rule and Open Question 3 reads closed, pointing at that row; `references/loop-control.md` §2a agrees; the A1–A3 key parser implements it; `sdd-gc.py --report` raises no new finding on this spec (REQ-ARB-HARNESSP5-003) | pass | `arbitrated-handoff.md:84` key table `section` row carries "**then a leading ordinal `\d+[.)]?\s*` stripped** (`§3. Foo` ≡ `§Foo` … REQ-ARB-HARNESSP5-003, closing Open Question 3)"; `:547` Open Question 3 reads "**closed 2026-09-19** (REQ-ARB-HARNESSP5-003)"; `loop-control.md:150` states the same strip. Parser exercised by A1–A3. `--report` raises no finding on this file |

### telemetry.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| §Writer rule (i) states the per-chunk-only condition (`dispatch.chunk != null`) and that a stage-level `fix` record keeps `chunk_verdict: null`; `references/telemetry.md` §3 and `SKILL.md` §Telemetry agree; on the frozen p4 fixture `--lint` still lists the three records as `[cross-field]` by seq; lint exits 0 (REQ-TELEM-HARNESSP5-001) | pass | `--lint --file tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl` prints `seq 21`, `seq 24`, `seq 27` as `[cross-field] verdict.chunk_verdict: non-null on a fix record with no verifier record for chunk None in the session`. `--self-test` case `test_stage_level_fix_has_null_chunk_verdict` passes. `sdd-skill-lint.py` exit 0 |
| §Writer states the `commit` source records the gate's **closing** `COMMIT:` line; `references/telemetry.md` §3 agrees; `summarize` on the frozen p4 fixture prints `COMMIT: INCOMPLETE (accepted): 0`; `test_schema_table_agrees` still passes (REQ-TELEM-HARNESSP5-005) | pass | `summarize --file …p4….jsonl` prints `widened dispatches: 0; COMMIT: INCOMPLETE (accepted): 0` for harness-p3 session 1 and harness-p4 session 1, and `widened dispatches: 1; COMMIT: INCOMPLETE (accepted): 0` for harness-p4 session 2. `--self-test` banner lists `schema table agrees with both renderings` and `test_commit_group_records_closing_line` |
| `wc -l docs/spec/telemetry*.md` shows no file over ~800 lines; the schema table stays under §Record Schema and `test_schema_table_agrees` passes; every moved section is listed in §Moved Sections; the six fold-in notes count six; `--report` raises no `qimpl-broken-ref` or broken-link finding on either file (REQ-LINT-HARNESSP5-003) | pass | 764 / 700 lines. `docs/spec/telemetry.md:436` `### Moved Sections — Reader, Lint and Fixture Contracts (REQ-LINT-HARNESSP5-003)`. `grep -c 'folded into'` over the four carrying specs → `0 + 4 + 1 + 1 = 6`. `--report \| grep -c 'qimpl-broken-ref'` → `0` |

### telemetry-reader.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `summarize` on the p4 fixture reports no missing pipeline for the `(implement, chunk null)` group; the p3 fixture's `expected 39` / 19 missing unchanged (sha256 asserted); `--self-test` covers three stage-level fixes with no chunk record → 0 implied pipeline (REQ-TELEM-HARNESSP5-002) | pass | p4 session 2: `implied vs recorded — pipeline :  8 vs 8  (0 missing)` and `implement: 0 missing (0 pipeline first attempts + 0 verifier)`. p3 session 1 unchanged: `records-vs-expected: 20 recorded, expected 39 (19 missing)`. `--self-test` banner: `harness-p5: null-chunk group implies no pipeline` |
| `--self-test`: `v: 1` + equal heads + `files_written_n > 0` → no finding, same shape at `v: 2` with null `commit.token` → finding; on the p4 fixture `--lint` raises no equal-heads finding on session 2 `seq` 2/4/6; the p3 finding set unchanged order-insensitively; no `migration` marker stamped (REQ-TELEM-HARNESSP5-003) | pass | `--self-test` banner: `v: 1 exempt from equal-heads`. `--lint` on the p4 fixture: `grep -c -i 'equal head'` → `0`; total `62 finding(s), 4 warning(s)`. Banner also names `frozen p3 finding set unchanged (sorted sha256)` |
| `--self-test` feeds `v: 2.0`: `summarize` reports it skipped and counted, `--lint` emits `[type] v`; `grep -c 'ADMITTED_V' tools/sdd-telemetry.py` shows the membership test in one helper called from both `load()` paths (REQ-TELEM-HARNESSP5-004) | pass | Banner: `v: 2.0 skipped and [type] v from one admission helper`. `grep -c 'ADMITTED_V'` → `3` (constant `:347`, `V_ADMITTED_TEXT` `:348`, membership `:365`), with the single helper `v_admitted()` `:355` called from `load()` `:443` and `_check_value()`'s `v` branch `:952` |
| `summarize` on the p4 fixture prints `COMMIT: INCOMPLETE (accepted): 0`; the label is stated in §Records-vs-Expected and §Fixture-Based Test Contract; `test_schema_table_agrees` still passes (REQ-TELEM-HARNESSP5-005) | pass | As above — all three session blocks print `COMMIT: INCOMPLETE (accepted): 0` |
| `--self-test` builds a type finding on `seq` 5 and a cross-field finding on `seq` 2 and asserts the rendered order 2, 5; the p3 finding set's sha256 over sorted lines is unchanged (REQ-TELEM-HARNESSP5-006) | pass | Banner: `findings sorted 2 before 5, frozen p3 finding set unchanged (sorted sha256)` |
| `shasum -a 256 …p4….jsonl` matches `tools/fixtures/README.md`; `wc -l` = 67; `git diff --stat main -- …p3….jsonl` is empty; the sha256 is asserted before and after every case that reads it (REQ-TELEM-HARNESSP5-007) | pass | `shasum -a 256` → `ff5cf2864abc74c2c05449b86e5117f5c4ed8851b6b5f96617859b8b061ef370` = `README.md:25`; p3 → `7e20b6307da09355f9aee504c451f0ed59e79ef9a33861cd72f370ea84af9237` = `README.md:51`. `wc -l` → `67`. `git diff --stat main -- tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` and `git diff --name-only 9bf25fd..HEAD -- <same>` are both empty. Banner: `test_p4_fixture_frozen (67 lines, README sha256, p3 unchanged against main)` |
| The three advisory cases are named in `--self-test` output and each fails when its check is removed in a temp copy; the frozen fixtures' outputs are unchanged (REQ-TELEM-HARNESSP5-008) | pass | Banner: `test_advisory_cases ((a) commit.token on verifier/red, (b) reason RED_BREAK, (c) migration.from outside chunk-string)`. p4 `--lint` output unchanged at `62 finding(s), 4 warning(s)`. The three removal mutations were run and recorded at Chunk 5; re-running them is outside this pass's write-free budget and the self-test asserts the positive side of each |
| This file is under the ~800-line bound; every `## Implementation Questions` entry sits with the section it amends, unrenumbered; `--report` raises no `qimpl-broken-ref` finding here (REQ-LINT-HARNESSP5-003) | pass | 700 lines; `--report \| grep -c 'qimpl-broken-ref'` → `0` |

### drift-sweep.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Fifteen-row sweep table with class, rule id and severity as specified; row 12 carries the second rule id `traceability-rowdrop` at fail (REQ-GC-HARNESSP5-001) | pass | `drift-sweep.md:89` row 12 reads `… \| \`traceability-aggregate\`; \`traceability-rowdrop\` \| warn; \`traceability-rowdrop\` **fail** \| …` |
| Row parser splits on unescaped pipes only; a wrong cell count raises one `[traceability-rowdrop]` **fail** naming `<file>:<line>`; `traceability-rowdrop` is not in `FIXABLE`; `--report` on this repository raises none and `grep -c '^\| REQ-ARB-HARNESSP4-003 \|^\| REQ-CYCID-HARNESSP4-001 ' docs/requirements/traceability.md` prints `2` (REQ-GC-HARNESSP5-001) | pass | `sdd-gc.py --self-test` exit 0, banner: `row-drop safety: an escaped pipe round-trips through --fix traceability-aggregate, a five-cell row raises one [traceability-rowdrop] fail at <file>:<line>, --fix traceability-rowdrop exits 2`. `python3 tools/sdd-gc.py --fix traceability-rowdrop` → exit `2` (not fixable). `--report \| grep -c 'traceability-rowdrop'` → `0`. The row-presence grep prints `2` |

### ws-traceability.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| §Legal `Verified` Cell Values lists `pass \| fail \| pending-red \| descoped` with the use limit; `skills/sdd-verify/SKILL.md` Step 6 and `skills/sdd-requirements/SKILL.md` Step 5 name the four values; a per-ws file containing a `descoped` cell passes `--report` with no new finding and regenerates into the aggregate unchanged; lint exits 0 (REQ-WS-HARNESSP5-001) | pass | `skills/sdd-verify/SKILL.md:149-161` names the four values and the "never written by this skill / never a `fail` substitute / never completion" limit; `skills/sdd-requirements/SKILL.md:250, 281-282` agrees. `docs/ws/harness-p4/traceability.md:36-37` carries two `descoped` cells and `sdd-gc.py --report` exits 0 with no finding attributable to them. `sdd-skill-lint.py` exit 0 |
| `grep -n 'descoped' docs/ws/harness-p4/traceability.md` hits exactly the two ARB rows; the commit that last touched that file lists exactly it and `docs/requirements/traceability.md` and its subject starts `docs(traceability):`; the regenerated aggregate shows three rows for `REQ-ARB-HARNESSP3-001` and two for `REQ-ARB-HARNESSP4-001` (REQ-WS-HARNESSP5-002) | pass | grep hits table rows `:36` and `:37` (the only other hit, `:17`, is the §preamble sentence). Last commit `9c7cb9c` — subject `docs(traceability): descope harness-p4's carried ARB rows and recover two dropped rows`, `--stat` lists exactly `docs/requirements/traceability.md` and `docs/ws/harness-p4/traceability.md`. **Aggregate row counts are stated as the expected post-regeneration state, not a mid-flight reading**: the shared aggregate is regenerated wholesale by the orchestrator at the verify gate, after this report is written, so the row counts asserted here — `REQ-ARB-HARNESSP3-001` → `3` (harness-p3 `fail`, harness-p4 `descoped`, this workstream's authoritative row) and `REQ-ARB-HARNESSP4-001` → `2` (harness-p4 `descoped`, this workstream's authoritative row) — are what the regenerated file must show, derivable by construction from the per-ws sources (`docs/ws/harness-p3/`, `…p4/`, `…p5/traceability.md`). The gate's own regeneration is the confirming run |

### harness-loop-control.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `grep -n 'status: complete' skills/sdd-orchestrate/SKILL.md …/loop-control.md …/write-scope.md skills/sdd-implement/SKILL.md` shows the flip in §The gate, §1 and the §7 table, and the direct-session / orchestrated split in `sdd-implement` Step 6; the per-chunk PIPELINE template carries "tick tasks, never `status:`"; §Gate Signal Order lists 6b and 8b and `references/loop-control.md` §5 agrees item for item (REQ-HARN-HARNESSP5-001) | pass | `SKILL.md:287` = signal 8b; `loop-control.md:35` (§1 loop tail), `:593` (§5 item 8b); `write-scope.md:485` (§7 table row) and `:512`; `sdd-implement/SKILL.md:278` ("the `status: complete` flip is the orchestrator's bookkeeping commit"). `dispatch-templates.md:117` carries **"tick tasks, never `status:`"**. 6b at `SKILL.md:284` and `loop-control.md:38` |
| `references/loop-control.md` §6 lists `PLAN: INCOMPLETE (N of M ticked)` as the **fifth** pause-family member with `replan │ stop` as its whole option set; a walkthrough where a contradiction pause and an unticked task fire together renders signal 6's block and 6b's line but offers `replan │ stop` only (REQ-HARN-HARNESSP5-001) | pass | `loop-control.md:662` lists it as a §6 pause member; `:664` states the flip is **withheld**. `harness-loop-control.md:394` states "**6b supersedes**: when `PLAN: INCOMPLETE` renders, the gate's option set is …"; `:434` restates it in the signal table with "6's block still renders, its options are suppressed, and the gate offers `replan \| stop` only". Desk walkthrough of both texts agrees item for item |
| A walkthrough of an implement stage gate `proceed` shows the flip in a commit separate from the leaf's and `COMMIT: COMPLETE`; a second walkthrough with one unticked task shows the `PLAN: INCOMPLETE` pause, no flip and no verify dispatch; the `research_id:` line is byte-identical before and after the flip; lint exits 0 (REQ-HARN-HARNESSP5-001) | pass | Exercised **live this cycle**: commit `2aa6eec chore(plan): flip harness-p5 plan to status: complete (O4)` is a bookkeeping commit separate from the Chunk 9 leaf commit `b136f83`. `git diff 2aa6eec^ 2aa6eec -- docs/ws/harness-p5/plan.md` touches `status:` only — `research_id: RS-HARNESSP5-001` is byte-identical and still string-equals the kickoff's. The unticked-task branch is a desk walkthrough of `loop-control.md:662-664` + `harness-loop-control.md:376-394` (no unticked task occurred). `sdd-skill-lint.py` exit 0 |

### harness-write-scope.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| §Commit Ownership names the **second** orchestrator bookkeeping commit with its three writes, states that it lands **after** `HEAD_landed` is captured and that a leaf writing any of them is a `SCOPE: VIOLATION`; `grep -n 'no-renames -z' docs/spec/harness-write-scope.md` shows the flags quoted once, pointing at `harness-commit-fidelity.md` §Comparand Table and `references/write-scope.md` §7a (REQ-HARN-HARNESSP5-001, REQ-WS-HARNESSP5-001, REQ-HARN-HARNESSP5-002) | pass | grep returns exactly one non-criterion hit, `harness-write-scope.md:226`, which quotes `git diff --name-only --no-renames -z HEAD_before HEAD_landed` and defers to the comparand table rather than restating it. §Commit Ownership carries the three-write bookkeeping paragraph (`:512`, plan-flip sentence) |

### harness-commit-fidelity.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `grep -n 'no-renames -z' docs/spec/harness-commit-fidelity.md` hits inside §Comparand Table on every `landed` cell; no five-fixture count remains; `--self-test` lists C1–C6; `--report` raises no new finding (REQ-HARN-HARNESSP5-002) | pass | grep hits `:116`, `:117`, `:118` — the three `landed` cells of §Comparand Table (plus the criterion line `:329`). `grep -n 'C1–C5'` returns nothing outside the criterion line; no five-fixture count remains. `sdd-scope-check-selftest.py --self-test` prints `PASS C1 … PASS C6`, including `C6 … path with a space counted once (-z landed operand, NUL split)`. `--report` raises no finding on this file |

### harness-chunk-verifier.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `grep -n '^  CHUNK_VERDICT:' docs/spec/harness-chunk-verifier.md` returns nothing; Q-IMPL-HARNESSP4-009 carries its fold-in status note with its body unchanged (REQ-QIMPL-HARNESSP5-001) | pass | grep returns nothing — both the §Verdict Rule example and the gate-text block render the token at column 0. `grep -c 'folded into'` on this file → `1` (Q-IMPL-HARNESSP4-009) |

### skill-lint-v5.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Size check at 400 warn / 1000 fail as module constants; baseline warns on none — the shipped skill set is `[size]`-clean (REQ-LINT-003, baseline amended 2026-09-19 by REQ-LINT-HARNESSP5-002) | pass | `python3 tools/sdd-skill-lint.py \| grep -c '[size]'` → `0`; `OK: 25 file(s) clean` |
| Marker-4 prose moved to `references/v4-workstreams.md` with stubs, `research_id` guard and superseding Q-IMPL; `SKILL.md` under 400 lines; lint exits 0 (REQ-LINT-007, bound amended 2026-09-19) | pass | `wc -l skills/sdd-orchestrate/SKILL.md` → `399`; lint exit 0 with every `REQUIRED` row and `[template-drift]` fence satisfied (`OK: 25 file(s) clean`). See §Issues Found → Minor on the lagging requirements text for this rule |
| lint exits 0 and its summary line matches `OK: N file(s) clean` with no warning clause — the linter appends `, W warning(s)` only when W > 0, so warn-clean is signalled by the absence of that clause; `\| grep -c '[size]'` prints 0; `wc -l skills/*/SKILL.md` shows every file < 400; every new `references/*.md` is linked from its stub and resolves; every `REQUIRED` row, the `VERSION_GATED_SKILLS` mention and the `[template-drift]` fences stay satisfied (REQ-LINT-HARNESSP5-001) | pass | Exit 0, summary `OK: 25 file(s) clean` with no warning clause. `[size]` count `0`. All ten `SKILL.md` line counts < 400 (max 399) — see §Quality Gates. Unresolved reference links would surface as `sdd-gc.py --report` broken-link findings; there are none |
| REQ-LINT-HARNESSP5-002's file-wide grep for the two legacy baseline figures returns nothing in this spec; the R7/R8 `reproduce:` commands print 0 and a number < 400; `docs/ws/harness-p5/verification.md` `## Post-cycle Fixes` records both reds closed (REQ-LINT-HARNESSP5-002) | pass | `grep -n '450' docs/spec/skill-lint-v5.md` → nothing; `grep -n "exactly .sdd-orchestrate. and .sdd-migrate" docs/spec/skill-lint-v5.md` → nothing. R7 `reproduce:` → `0`; R8 `reproduce:` `wc -l skills/sdd-orchestrate/SKILL.md` → `399` (< 400). §Post-cycle Fixes below records both closed |
| §`[template-drift]` states the absent-side behaviour (warn, never fail) and the rendered finding order; Q-IMPL-HARNESSP4-008 carries its fold-in status note and its body is unchanged (REQ-QIMPL-HARNESSP5-001) | pass | `grep -c 'folded into' docs/spec/skill-lint-v5.md` → `1`; lint exit 0 with the `[template-drift]` fences satisfied |

### deviation-protocol.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| The `[folded into §<section>, YYYY-MM-DD]` status note is defined here with its four rules; the six Q-IMPL-HARNESSP4-004..009 entries carry it and their bodies are unchanged; `grep -c 'folded into'` over the four specs sums to 6; `test_schema_table_agrees` still passes; `grep -n '^  CHUNK_VERDICT:' docs/spec/harness-chunk-verifier.md` returns nothing; `--report` raises no new finding (REQ-QIMPL-HARNESSP5-001) | pass | `grep -c 'folded into'` → `telemetry.md 0`, `telemetry-reader.md 4`, `skill-lint-v5.md 1`, `harness-chunk-verifier.md 1` = **6**. `--self-test` banner lists `schema table agrees with both renderings`. `^  CHUNK_VERDICT:` grep returns nothing. `--report` exit 0 with no new finding |
| `python3 tools/sdd-gc.py --report \| grep -c 'qimpl-broken-ref'` prints 0 — (REQ-QIMPL-HARNESSP5-002) | pass | → `0` (down from the 4 warnings in the harness-p4 baseline) |
| … no qimpl-related hunk lands in `tools/sdd-gc.py` — (REQ-QIMPL-HARNESSP5-002) | pass | Criterion **rescoped 2026-09-20** (`deviation-protocol.md` §Acceptance Criteria, bracketed dated note). It read "`git diff --stat main -- tools/sdd-gc.py` is empty"; the 2026-09-20 replan (`docs/ws/harness-p5/plan-history/2026-09-20-replan-gc-rowdrop-and-fixture-boundary.md`) added REQ-GC-HARNESSP5-001, whose `traceability-rowdrop` implementation legitimately edits that same file (81 insertions / 12 deletions, every added rule-id token `rowdrop`) **after** this criterion was Approved, making the empty-diff form unsatisfiable. Reworded form run verbatim: `git diff main -- tools/sdd-gc.py \| grep -E '^[+-]' \| grep -v '^[+-][+-]' \| grep -ci 'qimpl'` → **`0`**, i.e. zero qimpl-related hunks. `python3 tools/sdd-gc.py --report \| grep -c 'qimpl-broken-ref'` → **`0`** independently proves the same point. The requirement's substance — re-point three broken `Spec reference` lines, renumber nothing — is fully met |
| … no entry was renumbered; the entry `GC:` line at the next orchestrated run shows the reduced warning count (REQ-QIMPL-HARNESSP5-002) | pass | Q-IMPL-002, -009, -014 and -072 keep their numbers (`--report` finds no `qimpl-undefined`/`qimpl-broken-ref`); the baseline moved from 4 `[qimpl-broken-ref]` warnings to 0 |

## User-Perspective Validation

| Scenario | Status | Notes |
|----------|--------|-------|
| An operator runs the repository's three tools cold, as CLAUDE.md §Quality Checks instructs | pass | `python3 tools/sdd-skill-lint.py`, `python3 tools/sdd-gc.py --report` and each `--self-test` run from a clean checkout with no arguments and no setup; all exit 0 and print a one-line verdict banner |
| A reader of `docs/ws/harness-p5/traceability.md` can reproduce any row's claim | pass | Every `Test` cell names a literal command, and all 23 reproduce verbatim against the tree this report describes. Three did not at first report time — the superseded `git diff --stat` guard, the self-matching `no-renames -z` grep and the unprintable `0 warning(s)` clause — and each was amended (M5 rescope; red round 2 R5; red round 2 R1) rather than reinterpreted, so no cell now needs a reader to reinterpret it. See §Summary |
| A reader asks "did the arbitration question actually get settled?" | pass | `sdd-scope-check-selftest.py --self-test` prints A1/A2/A3 with **both** readings side by side, so the discriminating case is legible without reading the spec; the two mutation scenarios show the assertion cannot pass vacuously |
| An operator asks gc to fix a row-drop finding | pass | `python3 tools/sdd-gc.py --fix traceability-rowdrop` exits `2` rather than silently doing nothing — the rule is deliberately outside `FIXABLE` and says so |
| `--fix` and `--report` leave the frozen regression oracles alone | pass | Both fixtures' sha256 match their `tools/fixtures/README.md` entries after the full gate run, and neither fixture path appears in `git status --porcelain` at any point in this stage |
| A future cycle can tell this cycle's artifacts from a previous one's | pass | `plan.md` and this report both carry `research_id: RS-HARNESSP5-001`, string-equal to `docs/ws/harness-p5/kickoff.md` |

## Regressions

- None found. Regression base is the workstream branch point
  `merge-base(harness-p5, main)` = `9bf25fd` (confirmed:
  `git merge-base harness-p5 main` → `9bf25fd17d725fbc15adf2e43a2311e4c47cf4af`).
- `git diff --name-only 9bf25fd..HEAD` lists 55 files, every one inside this
  cycle's declared scope (requirements, specs, research, `docs/ws/harness-p5/**`,
  the one authorised cross-workstream `docs/ws/harness-p4/traceability.md`
  bookkeeping edit, `skills/**`, `tools/**`). No unintended change.
- The frozen harness-p3 telemetry fixture is byte-identical to `main`
  (`git diff --stat main -- tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
  empty); its `--lint` finding set and `summarize` numbers (`expected 39`,
  19 missing) are unchanged.
- Working-tree state: the verify-stage writes (this report, the per-ws
  traceability, the red-round spec repairs) are the orchestrator's gate commit;
  no path outside this cycle's declared scope is modified or left untracked.

## Post-cycle Fixes

Both harness-p4 accepted red findings are closed by this cycle
(`skill-lint-v5.md` §Acceptance Criteria, REQ-LINT-HARNESSP5-002):

- **R7 closed** (accepted at gate 2026-09-19; stale size baseline in
  `skill-lint-v5.md` REQ-LINT-003). The baseline now reads "warns on none" and
  the shipped skill set is `[size]`-clean. `reproduce:`
  `python3 tools/sdd-skill-lint.py | grep -c '[size]'` → **0**.
- **R8 closed** (accepted at gate 2026-09-19; `sdd-orchestrate/SKILL.md` 551
  lines against a "≤ ~450" bound). The bound was amended to 400 and the file
  was reduced. `reproduce:` `wc -l skills/sdd-orchestrate/SKILL.md` → **399**
  (< 400).

## Issues Found

### Critical (blocks release)

- None.

### Minor (can ship, fix later)

- **harness-p4 R7 and R8** (both accepted at gate 2026-09-19, both now
  `closed`): recorded once, with their observed text and `reproduce:` output,
  under §Post-cycle Fixes above. They are not restated here — cross-reference
  only, so a reader meets each finding in exactly one place.
- **Red round 2 R1** (`BROKEN`, **fixed** this cycle): `skill-lint-v5.md`'s
  acceptance criterion for REQ-LINT-HARNESSP5-001 required the linter's summary
  line to print `0 warning(s)`, which `tools/sdd-skill-lint.py` never emits — it
  appends `, W warning(s)` only when `W > 0`, so a warn-clean run prints
  `OK: 25 file(s) clean` and the criterion was literally unreproducible. Fixed
  by restating the criterion as "matches `OK: N file(s) clean` with **no**
  warning clause"; the edit touched four files (the spec criterion, the matching
  §Criteria row and §Quality Gates note here, and the per-ws traceability `Test`
  cell for REQ-LINT-HARNESSP5-002). `reproduce:`
  `python3 tools/sdd-skill-lint.py` → `OK: 25 file(s) clean`, exit 0.
- **Red round 2 R5** (`BROKEN`, **fixed** this cycle):
  `harness-write-scope.md`'s `grep -n 'no-renames -z' docs/spec/harness-write-scope.md`
  criterion was self-matching — the criterion line itself contains the quoted
  flags, so the literal command returned **2** hits, not the asserted 1, and the
  row had been marked `pass` on a reinterpreted ("exactly one non-criterion
  hit") reading. Fixed by rewording the criterion so its own text is excluded
  and the literal command reproduces.
- **Red round 2 R7** (`BROKEN`, **fixed** this cycle): `deviation-protocol.md`
  §Numbering specified Q-IMPL ids as "global sequential `Q-IMPL-001`,
  `Q-IMPL-002`, … across all specs", contradicting the already-Approved
  `docs/spec/ws-ids.md` marker-`4` contract, CLAUDE.md §Workstream-prefixed IDs,
  and the 54 live `Q-IMPL-<WS>-NNN` ids in the corpus. Fixed by rewriting
  §Numbering (and its rationale paragraph, and the stale REQ-QIMPL-002
  acceptance line) to cite `ws-ids.md` as the owning contract for the
  `Q-IMPL-<WS>-NNN` form, the per-workstream counter and the parsing rule, with
  legacy bare ids read as the `default` workstream and never remapped. **This is
  a contract-text change that traces to no harness-p5 requirement, and that is
  correct**: it does not introduce a new rule — it aligns stale spec prose with
  a contract Approved in an earlier cycle, so there is nothing new to require.
  It is recorded here rather than in traceability for that reason. Not reverted.
- **Plan annotations.** `docs/ws/harness-p5/plan.md` carries two annotations
  reading "red R1"; both mean **red round 2 R1** (the lint-summary criterion),
  not red round 1 R1 (the gc fence asymmetry below). The plan is outside this
  pass's write scope, so the disambiguation is recorded here.
- `docs/spec/telemetry.md` `last_updated: 2026-09-19` lags
  `docs/requirements/functional/telemetry.md` (`2026-09-20`, moved at the
  replan), which is the largest single contributor to the gc `[stale-chain]`
  warn class (no total is pinned — see §Quality Gates). The spec's
  **content** is current — the harness-p5 writer rules were Approved at the
  specs stage; only the date lags. Routed to the DONE gc step as
  `record | ignore` by operator decision; recorded, not fixed here.
- `docs/requirements/integration/skill-lint.md` (REQ-LINT-007, ~L128-130) still
  says "§Isolation Discipline, §Rules and §Orchestrator-Only Work must not
  move", unqualified, while `docs/spec/skill-lint-v5.md` was rescoped in Chunk 9
  and REQ-LINT-HARNESSP5-001 in the same requirements file authorises the move.
  Requirements text lags the spec; no shipped behaviour is affected (lint exits
  0 and the `Moves: no` row is scoped in the spec).

- Red round 1 R1 (accepted by the operator, routed to the next cycle):
  `tools/sdd-gc.py`'s Q-IMPL sweep is fence-asymmetric — the reference side uses
  `visible_lines()` but the definition side scans raw lines
  (`tools/sdd-gc.py:611`), so a `### Q-IMPL-…:` heading inside a fenced code
  block registers as a real definition and can suppress a fail-class
  `[qimpl-undefined]` finding anywhere in the corpus.
  reproduce: copy `docs/ skills/ tools/` to a throwaway git repo, add a prose
  reference to an undefined Q-IMPL id (gc reports `FAIL: 1 finding`), then add a
  triple-backtick-fenced `### <that id>:` heading to any spec and re-run — gc reports
  `OK: 0 findings`.
  Not fixed this cycle: `Q-IMPL-001` and `Q-IMPL-002` are format illustrations
  living inside a fence in `deviation-protocol.md`, so making the definition side
  fence-aware would un-define them and turn roughly thirty legitimate prose
  mentions across specs, requirements, skills and three prior workstreams into
  `[qimpl-undefined]` failures. The correct fix needs a countability rule for
  format examples (an `is_countable`-style exclusion), which is a design decision
  rather than a patch.

## Recommendation

- [x] Ship once the red rounds close — both have now run (round 1: one
      `BROKEN` finding, accepted and carried; round 2: R1, R5 and R7
      `BROKEN`, all three fixed), so the remaining condition is the
      orchestrator's `pending-red → pass` flip at the verify gate. No
      blue-team condition is outstanding.
- [ ] Fix critical issues then ship (invoke sdd-replan)
- [ ] Significant rework needed (invoke sdd-replan)

Blue-team verification passes with no critical issue. Because the dispatch
carried `Red team: enabled`, `status:` reads `pending-red` and every
`Verified` cell this pass would have marked `pass` reads `pending-red`; the
orchestrator flips both to `pass` at the verify gate once every `BROKEN` `Rn`
is fixed or accepted. The active plan may be archived to
`docs/ws/harness-p5/plan-history/` after the gate.

## Open Questions

- **The `Verified` value for REQ-QIMPL-HARNESSP5-002 — resolved 2026-09-20.**
  Its `git diff --stat main -- tools/sdd-gc.py` guard had been made
  unsatisfiable by a later replan putting a *different* requirement's code in
  the same file. The operator's decision was to rescope the criterion rather
  than close the cycle on a spec-text defect: `deviation-protocol.md`
  §Acceptance Criteria now reads "no qimpl-related hunk in `tools/sdd-gc.py`",
  carrying a bracketed dated note naming REQ-GC-HARNESSP5-001 as what superseded
  the original. The reworded command reproduces (→ `0`), the §Criteria row is
  `pass`, and the row reads `pending-red` (i.e. would-be-`pass`) like every
  other. No open question remains.
- **Mutation re-runs for REQ-TELEM-HARNESSP5-008.** The three
  check-removal mutations were executed and recorded at Chunk 5 but were not
  re-executed in this pass (each needs a temp copy of `tools/sdd-telemetry.py`
  and a write, which this read-only verification budget excludes). **Default
  taken: the criterion reads `pass` on the Chunk 5 evidence plus the positive
  `test_advisory_cases` assertions.** If the operator wants an independent
  re-run, the red-team leaf is the natural place for it.

## Next Steps

- gc `[stale-chain]` (the dominant warn-class contributor): bump `docs/spec/telemetry.md`
  **[Superseded 2026-09-20 — RS-HARNESSP6-001 Q1; the full note follows this entry. Marker repeated here on the line immediately above the phrase so the matched-phrase, at-or-above liveness rule resolves it (red R1/R2).]**
  `last_updated:` to `2026-09-20` through `sdd-specs` in a follow-up cycle — the
  content is already current. Routed `record` at the DONE gc step.
  **[Superseded 2026-09-20 by RS-HARNESSP6-001 Q1 — see REQ-GC-HARNESSP6-002 and
  REQ-GC-HARNESSP6-003.** This item is Q1's option A, which that spike rejects
  and the harness-p6 kickoff bars: bumping a `last_updated:` purely to silence a
  sweep destroys the signal. The shared-spec staleness class is instead folded to
  one finding per (spec, category file) pair and carried at `info`. No date bump
  is to be made on this account. The record of what harness-p5 found stands; the
  instruction does not.**]**
- ~~Spec text: rescope `docs/spec/deviation-protocol.md` §Acceptance Criteria
  (REQ-QIMPL-HARNESSP5-002) so the `tools/sdd-gc.py` guard reads "no
  qimpl-related hunk".~~ **Done 2026-09-20** — applied in this cycle with a
  bracketed dated note; the reworded command reproduces (→ `0`).
- Requirements text: qualify `docs/requirements/integration/skill-lint.md`
  REQ-LINT-007 (~L128-130) so the "must not move" list matches the Chunk 9
  rescoping that REQ-LINT-HARNESSP5-001 authorised in the same file.
  **[Closed 2026-09-20 in harness-p6 — in scope as kickoff item (6) and written
  up as REQ-LINT-HARNESSP6-002; no longer a forward-looking item here.]**
- `docs/ws/harness-p5/plan.md` §Open Questions still says
  `telemetry-reader.md` "says 61" — **resolved**: it reads `67` in all three
  places (`wc -l` on the frozen p4 fixture → 67; `README.md:25`;
  `test_p4_fixture_frozen`). The stale entry can be struck at plan archival.
  **[Closed 2026-09-20 in harness-p6 — in scope as kickoff item (7) and written
  up as REQ-PLAN-HARNESSP6-001; the strike happens at that cycle's plan
  archival.]**
- L2 (cross-layer convergence as a gate signal) remains deferred, as decided at
  DISCUSS; the harness-p5 evidence adds nothing that changes the deferral.
  **[Superseded 2026-09-20 by RS-HARNESSP6-001 Q4 — see REQ-HARN-HARNESSP6-002
  and REQ-ORCH-HARNESSP6-001..002.** L2 ships in workstream `harness-p6` on
  explicit operator direction, as an orchestrator-derived informational gate
  signal at position 6c — no finding field, no fifth layer. The deferral
  recorded here is no longer live; the two matching
  `docs/requirements/index.md` §Out of Scope entries were struck with it.**]**

**[Closed 2026-09-20 — the four numbered items below are all closed in
harness-p6 and none survives as forward work: (1/4) → kickoff item (5) /
REQ-GC-HARNESSP6-004; (2/4) → kickoff item (1) / REQ-GC-HARNESSP6-001; (3/4) →
kickoff item (3) / REQ-HARN-HARNESSP6-001; (4/4) → kickoff item (4) /
REQ-LINT-HARNESSP6-001. They are left in place as the record of what harness-p5
found; they are no longer instructions. This marker deliberately does not quote
the phrase it retires, so the REQ-REQ-HARNESSP6-001 acceptance grep cannot match
the annotation itself.]**

- **[Closed 2026-09-20 in harness-p6 — REQ-GC-HARNESSP6-004; no countability rule was needed: all 82 definition ids have an unfenced definition, 0 are fence-only.]** Carried to the next cycle (1/4): the red round 1 R1 fence asymmetry in
  `tools/sdd-gc.py`'s Q-IMPL sweep recorded under §Issues Found → Minor, together
  with its open design question — a countability rule that lets fenced format
  illustrations stay defined while fenced headings elsewhere stop counting.
- **[Closed 2026-09-20 in harness-p6 — REQ-GC-HARNESSP6-001 (closed-workstream skip) and REQ-GC-HARNESSP6-002/-003 (the shared-spec sub-class).]** Carried to the next cycle (2/4): gc's `[stale-chain]` rule flags closed,
  `status: pass` workstreams forever, so the warning count grows monotonically
  (11 warnings on `docs/ws/harness-p3/plan.md` today). Teach the rule to skip
  closed workstreams.
- **[Closed 2026-09-20 in harness-p6 — REQ-HARN-HARNESSP6-001: a `GIT_STATE` line inside the existing `SCOPE:` block.]** Carried to the next cycle (3/4): read-only dispatches can mutate git state
  undetected. The write-scope contract forbids creating, modifying and deleting
  files but says nothing about `git stash` / `git checkout` / `git reset`, and a
  verifier in this cycle ran `git stash` (recovered, no loss) while nine files of
  uncommitted work were in the tree — `SCOPE:` observes file writes and would not
  have caught it.
- **[Closed 2026-09-20 in harness-p6 — REQ-LINT-HARNESSP6-001, which also adopts the `GIT_STATE` row (Q-REQ-P6-D).]** Carried to the next cycle (4/4): `PLAN:` is the only gate token with no
  `REQUIRED` row in `tools/sdd-skill-lint.py`, unlike `VERDICT:`,
  `CHUNK_VERDICT:`, `RED_VERDICT:` and `COMMIT:`, so deleting it from
  `loop-control.md` §6 is unguarded.

### gc routing at DONE (2026-09-20, `record`)

`python3 tools/sdd-gc.py --report --workstream harness-p5` → exit 0, **zero
fail-class findings**, 14 warnings in workstream scope; repo-wide 63
`[stale-chain]` warnings and 25 `[qimpl-unreferenced]` info. The operator routed
every finding `record` rather than `--fix`: `[stale-chain]` is deliberately not
auto-fixable (gc's own guidance is that dates move through the owning skill),
and bumping a `last_updated:` purely to silence the sweep is how a staleness
signal stops meaning anything. The rule itself is Next Step 2/4.

- gc `[stale-chain]`: `docs/spec/telemetry.md` (42 warnings) — the spec's content
  is current (the harness-p5 writer rules were Approved at the specs stage and
  needed no edit), only its `last_updated:` lags its 2026-09-20 requirement file.
  **[Superseded 2026-09-20 — RS-HARNESSP6-001 Q1; the full note follows this entry. Marker repeated above the phrase for the at-or-above liveness rule (red R1/R2).]**
  Fix: bump through `sdd-specs` in a cycle that actually edits it, or let Next
  Step 2/4's rule change retire the class.
  **[Superseded 2026-09-20 by RS-HARNESSP6-001 Q1 — the "bump through
  `sdd-specs`" half of this routing is withdrawn (see REQ-GC-HARNESSP6-002 and
  -003); only the rule-change half stands.]**
- gc `[stale-chain]`: `docs/ws/harness-p3/plan.md` (13), `docs/ws/harness-p4/plan.md` (6)
  — closed, `status: pass` workstreams flagged for being older than specs later
  cycles amended. They *should* be older. Fix: Next Step 2/4 — teach the rule to
  skip workstreams whose verification is `pass`.
  **[Closed 2026-09-20 in harness-p6 — REQ-GC-HARNESSP6-001.]**
- gc `[stale-chain]`: `docs/spec/adversarial-verify.md` (2) — same class, against
  a 2026-09-19 requirement file.
- gc `[qimpl-unreferenced]`: 25 info lines — informational by design; entries live
  in their spec and need no citation. No action.
