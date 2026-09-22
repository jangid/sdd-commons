---
status: pending-red
research_id: RS-PIPELINEOBSERVABILITY-001
last_updated: 2026-09-22
plan_ref: docs/ws/pipeline-observability/plan.md
---

# Verification Report — pipeline-observability

## Summary

Blue verification of the pipeline-observability cycle (RS-PIPELINEOBSERVABILITY-001,
plan `status: complete` at `33738c8`, branch point `git merge-base HEAD main` =
`fb4635f`). All eight whole-cycle quality gates exit 0 on the tree; the four
delta-map criteria hold (`37 rows, 0 mismatches`; `16 specs, 0 failures`; added-line
anchor grep 0; both sha scans 0); the twelve verify-stage inputs V1–V12 were executed
in order with the evidence below; the three gate-rendering walkthroughs are transcribed
under `## Gate-rendering walkthroughs`. **Zero Critical issues.** Thirteen Minor issues,
two of them failed acceptance criteria of `requirements-artifacts.md` §Amendment
Landing ((a) one amended body lacks its `**Amended` marker; (e) the sweep-block
re-runs list files the blocks do not name — the aggregate traceability in 29 blocks,
and `USAGE.md` / `reviewer.md` in 5 blocks, both written after the blocks by the
implement-stage fix `e891ea2`). Two V-items are partial for lack of the orchestrator's
own rendered text (V4: `GROWTH:` lines were handed over for the specs stage only; V5:
the chunk verifier's Check 3 text was not among this stage's inputs). The red team is
enabled for this stage, so `status: pending-red` is written and every would-be-`pass`
`Verified` cell reads `pending-red`; the one `fail` row is
REQ-REQ-PIPELINEOBSERVABILITY-001 (criteria (a) and (e) do not hold on the tree).

**Severity rule used throughout** — a verify-stage decision of this report, stated by no
upstream artifact (plan, kickoff, `docs/spec/**`, `skills/verify/SKILL.md`) and put to the
operator for ratification at the verify gate (review M5). *Critical* = a shipped binding under
`plugins/sdd/` or a gate rule renders a false claim, a self-test or gate exits
non-zero on the tree, or a dogfooding claim of the kickoff fails for a gate.
*Minor* = a corpus-documentation criterion fails, or a standing `warn` floor moves,
with no binding and no gate rendering wrong. A `fail` cell in the traceability matrix
is the per-requirement reading of that rule: REQ-REQ-PIPELINEOBSERVABILITY-001's row
reads `fail` because two of its clauses do not hold on the tree, and that row does not
make the report's own result `fail`, because the failed clauses bind corpus prose, not
a shipped binding or a gate — the phase-detection reading `status: fail → needs replan`
is reserved for the report-level result (review M4).

## Quality Gates

All run from the repository root on the working tree at `33738c8` (clean at entry).

| Gate | Status | Notes |
|------|--------|-------|
| `python3 plugins/sdd/tools/skill-lint.py .` | pass | exit 0 — `GEOMETRY: nested swept-roots=2 suite-rows-root=…/plugins/sdd`, `OK: 25 file(s) clean` |
| `python3 plugins/sdd/tools/skill-lint.py --self-test` | pass | exit 0 — `SELF-TEST OK: all rule classes fire; fix/warn/size/backtick/allow_files/retired-prefix fixtures pass` |
| `python3 plugins/sdd/tools/gc.py --report --root . --workstream pipeline-observability` | pass | exit 0 — `OK: 10 sweep(s) clean, 68 warning(s), 36 info` (the pre-write reading; `33 info` after this report was written — §Regressions); 0 `FAIL` lines; warnings by rule: `dead-path-citation` 59, `literal-anchor` 7, `qimpl-broken-ref` 2; info: `qimpl-unreferenced` 34, `stale-chain` 2 |
| `python3 plugins/sdd/tools/gc.py --self-test` | pass | exit 0 — `SELF-TEST OK: … snapshot comparands: literal-anchor (fence filter only, spans read, sha-pinned exempt, folded count), self-matching-grep (one fixture line per grammar form), dead-path-citation (one span per token form), qimpl-malformed (bare reference with no bare definition), traced-stale-chain (traced pair warn, untraced info under --workstream), aggregate-last-updated` |
| `python3 plugins/sdd/tools/telemetry.py --self-test` | pass | exit 0 — the OK line names `test_append_cases`, `test_flat_cg_migration`, `test_migration_lost_shape`, `test_post_manual_reason_review`, `test_cross_field_gate_rules ((a)–(d) each a finding pair and a control pair)`, `test_frozen_finding_sets_unchanged (p3 and p4 sorted-lines sha256)` |
| `python3 plugins/sdd/tools/telemetry.py --lint` (live file, read-only) | informational | exit 1 — `lint: 123 finding(s), 4 warning(s) — .sdd/telemetry.jsonl`; by class: `[cross-field]` 69, `[type]` 35, `[enum]` 7, `[mistyped-fix]` 6, `[key-undeclared]` 6, `[reason-review]` 4; **0 assertion (a), 0 assertion (c)** findings; (b) fires 27× and (d) 40× on historical records (see §Issues Found → Minor 5) |
| `python3 plugins/sdd/tools/scope-check-selftest.py` | pass | exit 0 — `OK: 45/45 scenarios passed` (44/44 at the branch point; A4 is the added scenario) |
| `pre-commit run --all-files` | pass | exit 0 — drift sweep (fast profile), skill linter, skill linter self-test, drift sweep self-test, trim trailing whitespace, fix end of files, check yaml, check json: all `Passed` |
| `python3 plugins/sdd/tools/skill-lint.py --print-population` | pass | `REQUIRED=57 VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=15 TEMPLATE_PAIRS=4` — equals `two-root-linter.md` §6's dated line (`Current at 2026-09-22: REQUIRED=57 VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=15`); branch point read `40 / 9 / 7 / 13` |

Build / install: the plugin is a file tree, no build step. Install evidence is V6
(the installed cache at 0.2.0 differs from `plugins/sdd` in zero files).

## Verify stage inputs (plan §Verify stage inputs, executed in order)

| Item | Status | Evidence |
|---|---|---|
| **V1** live migrated record count | pass (with one recorded unsatisfiable clause) | `python3 plugins/sdd/tools/telemetry.py summarize --workstream consumer-geometry` → `workstream: consumer-geometry   records: 36   runs (cycle.research_id): None`; per-chunk block: `0   1  1  0  0  2  0  partial — migrated from "Chunk 0"; verifier, fix and redo records were never written and cannot be reconstructed`. 36 equals the fixture-derived reference and is no longer 0. `--workstream packaging` reads `records: 36`, chunks 0 and 1 `partial`. OP-2's own report (carried notes): 72 migrated of 328 lines; consumer-geometry 36 / 17 lost (commit 2, gate 14, pr 1); packaging 36 / 41 lost; unknown-schema skipped 0; lint 245 → 123; a second run wrote nothing. The `telemetry-reader.md` clause "per-chunk blocks for chunks 1–8 stamped `partial`" is unsatisfiable on the live file — chunks 1–8 of consumer-geometry exist only on lost gate records (Q-IMPL-PIPELINEOBSERVABILITY-005); the block is chunk 0 only, as V1 expected. |
| **V2** gates under the fix-then-proceed routing | pass, qualified | See §Dogfooding map as observed. Exactly **one** gate of this cycle closed on `APPROVE_WITH_FIXES` and proceeded without re-review: the implement-stage review r3 (the post-manual round) → fix `e891ea2` → chunk verifier `PASS` → plan complete `33738c8`. Every document stage exited on a closing `APPROVE` because kickoff constraint 4 (amended at the specs gate: "a stage exits only on `VERDICT: APPROVE`") and constraint 5 (route every non-`APPROVE` to requirements) are operator rules layered over the routing: the `APPROVE_WITH_FIXES` rounds of research (r2–r4, before the routing landed at that gate) and requirements (r7, r8) were consumed and followed by fixes and further rounds by those constraints, **not** by a default re-review — so the replan trigger "an `APPROVE_WITH_FIXES` re-reviewed by default" does not fire. Recorded as an observation for the operator: while constraint 4 stands, the routing's `proceed` branch is taken only at a stage whose closing review is the last round (the implement stage here). |
| **V3** manual interventions and their `post-manual` rounds | pass | Manual interventions this cycle: (1) research gate — a manual fix beside the landing of the V3 routing, **before** Chunk 1 landed the `post-manual` rule (`c15e2f5`), so outside the rule's dogfooding window; no post-manual round was owed. (2) Implement stage, `2266511` — M1/M3/M4 of the voided review r2 applied by the orchestrator; followed by r3, the `post-manual` review (`APPROVE_WITH_FIXES`). One `manual intervention` option was offered at requirements and **not** used. Post-rule interventions with a `post-manual` round: 1 of 1; none without. `telemetry.py --lint` over the live file: **0 assertion (c) findings** (`grep -E '\((c)\) '` over the 128-line output is empty; likewise (a)). |
| **V4** the conditional `GROWTH:` quotation | partial | Stages with a review round N ≥ 2: research (4), requirements (8 + 1), specs (5 + 3), plan (1 + 3), implement (r1–r3). The orchestrator handed this stage the rendered lines for the **specs** stage only, as reported: rounds 2, 3, 4, 5 → `+112`, `+69`, `+108`, `+730` added lines (format per `loop-control.md` §5 item 6d: `GROWTH: <deliverable> +A/−D lines (N₁ → N₂) since round N−1`; the orchestrator reported the `+A` term only). For requirements, plan and implement rounds N ≥ 2 no rendered line was handed over, so it cannot be quoted here — **unable to verify** for those stages; the temp-copy and self-test halves of the criterion hold (`REQUIRED` row `GROWTH: ` present: `grep -c 'GROWTH: ' …/loop-control.md` = 1; `skill-lint.py --self-test` exit 0). |
| **V5** real-chunk Check 3 under the declared convention | partial | Derivation command on the tree lists exactly `plugins/sdd/tools/gc.py`, `plugins/sdd/tools/skill-lint.py`, `plugins/sdd/tools/telemetry.py` (neither `scope-check-selftest.py` nor `eval.py`). Fixture: `sh …/check3.sh chunk-gc.md` → `Check 3 (plugins/sdd/tools/gc.py): pass — named by the declared convention, no advisory`, exit 0; `check3.sh chunk-scope-check.md` → `advisory — outside the derived set and no test file imports from it`, exit 2. Real-chunk consequence: Chunks 2 (`telemetry.py`) and 3 (`gc.py`) closed `CHUNK_VERDICT: PASS` after one redo each (telemetry `summarize --workstream pipeline-observability` per-chunk block: chunk 2 verifier 2, chunk 3 verifier 1) — the verifier's Check 3 text itself was not among this stage's inputs, so the "no advisory" line cannot be quoted; **unable to quote**, recorded from the gate outcome only. |
| **V6** installed cache version | pass | `~/.claude/plugins/cache/sdd-commons/sdd/` holds `0.1.0` and `0.2.0`; `0.2.0/.claude-plugin/plugin.json` reads `"version": "0.2.0"` = the working tree's; `diff -rq plugins/sdd …/0.2.0` prints nothing. `grep -c 'at least one Material finding' …/0.1.0/agents/reviewer.md` = 0, `…/0.2.0/agents/reviewer.md` = 1 — the 0.1.0 body that every review leaf of this cycle ran under carries none of the landed grammar (Minor 7). The 0.2.0 marketplace update itself cannot be exercised before the PR merges (marketplace source is GitHub `main`). |
| **V7** walkthrough `reject_run` | pass | Transcribed under §Gate-rendering walkthroughs → W1. |
| **V8** walkthrough chunk-0 void + per-chunk manual intervention | pass | Transcribed → W2; `scope-check-selftest.py` exit 0 (45/45). |
| **V9** walkthrough tier fixtures F1–F9 | pass | Transcribed → W3; every non-`legal` cell of the 4×3 case table exercised. |
| **V10** amendment-landing corpus checks | **fail (Minor)** | (d) `(amended)`-row file set vs index Files-table annotations: 10 = 10, `diff` prints nothing. (a) `[Updated:` / `**Amended` per amended body: 15 of 16 hold; **REQ-LINT-PACKAGING-007** (`docs/requirements/integration/skill-lint.md`) holds `[Updated: 2026-09-22]` and **0** `**Amended`. (b) Spec-cell amendment-section grep = 0 over 37 rows; every `(amended)`-row Spec file holds `Updated: 2026-09-22` ≥ 1 (11 files, counts 2–6). (e) Requirement-column id set (37) equals the sweep-block/`no binding statement` id set (37), `diff` prints nothing; **re-running every block's command with `-l` (35 blocks)**: 6 blocks list exactly the files they name; **29 list `docs/requirements/traceability.md`** (the regenerated aggregate, whose Test cells quote the patterns) which no block names; **5 list a file written after the blocks**: `plugins/sdd/skills/orchestrate/USAGE.md` (REQ-HARN-PIPELINEOBSERVABILITY-002, -003, REQ-HARN-HARNESSP6-001) and `plugins/sdd/agents/reviewer.md` (REQ-HARN-PIPELINEOBSERVABILITY-001, REQ-HARN-013) — the operator guide and reviewer body of the implement-stage fix `e891ea2`. This is the class the criterion exists to catch ("adding one sentence matching a block's pattern to any swept file makes that block's re-run list a file it does not name"). Minor 1 and 2. |
| **V11** whole-cycle gates, anchor and sha scans, hook runs, regression base | pass | Gates: the table above. Added-line anchor grep over the branch diff of `docs/spec` (20 files, +2497/−50): **0**. Per-section sha scan, amendment sections: **0**; marked paragraphs: **0**. Hook runs (Q-PLAN-PO-F): tree — `pre-commit run end-of-file-fixer --files .claude/settings.json` → `fix end of files…(no files to check)Skipped`, exit 0; scratch copy under `$TMPDIR` with the `\.claude/` alternative deleted from the config (`grep -c 'claude/'` = 0 there) → `fix end of files…Passed`, exit 0 — the file was processed. Both runs succeeded **inside** the sandbox once the scratch copy sat under `$TMPDIR`; the chunk's `PermissionError` came from a scratch path the sandbox denied, not from the hook. Regression base `fb4635f`: §Regressions. |
| **V12** the sixteen-spec set under delta-map criterion 2 | pass | Derived set 16 files (`arbitrated-handoff, chunk-close-review, drift-sweep, harness-agents, harness-loop-control, harness-return-contract, harness-write-scope, marketplace-packaging, pre-commit, project-docs, requirements-artifacts, review, skill-lint-v5, telemetry-reader, telemetry, two-root-linter`); the fenced loop prints `16 specs, 0 failures`. Dated observations: `grep -l '^## Pipeline-Observability Amendment' docs/spec/*.md \| wc -l` = 16; the `find … ! -path docs/spec/pipeline-observability.md … 'Updated: 2026-09-22'` count = 16. Run after Chunks 1, 3 and 4 edited members, so the §Conventions bump rule is observed. |

## Acceptance Criteria

### pipeline-observability.md (delta map)

| Criterion | Status | Evidence |
|---|---|---|
| 1. Every row's Spec cell names a section of record of a spec ≠ the map whose `requires:` lists the id | pass | amendment-section cell grep = 0; row population `grep -c '^\| REQ-'` = 37; parse prints `37 rows, 0 mismatches` |
| 2. The derived spec set: Approved, amendment heading, dated marker, `last_updated` ≥ latest marker | pass | `16 specs, 0 failures` (V12) |
| 3. No added line cites a `.md:N` anchor | pass | branch-diff added-line grep = 0 over 20 changed spec files |
| 4. No 7–40-hex token in the amendment sections or marked paragraphs | pass | both loops read 0 |
| §Verification → Automated: coverage sweep | pass | `37 ids 75 refs {'REQ-LINT-PIPELINEOBSERVABILITY-001': 3}` — the stated derivation (2 × 37 + 1) |
| `skill-lint.py` exit 0; `gc.py --report` exits `OK` | pass | Quality Gates |

### arbitrated-handoff.md

| Criterion | Status | Evidence |
|---|---|---|
| `scope-check-selftest.py` exit 0 with scenario A4; A1–A3 unchanged; heading-existence clause removal flips A4 (temp copy) | pass | 45/45 scenarios (44/44 at the branch point); the reversion witness is the row's own Chunk 4 evidence (traceability Test cell) and was not re-run here (test-run budget) |
| `W_N` line carries `new[N]` in both the spec and `loop-control.md` §2a | pass | `sed -n '/^### Retained Per-Round State/,/^### Contradiction/p' … \| grep -c 'new\[N\]'` = 2; `grep -c 'new\[N\]' …/loop-control.md` = 4 |
| A4 fixture includes a moved heading, both names in `W_N` | pass | fixture `plugins/sdd/tools/fixtures/arbitration-moved-heading-2026-09-22/` (`after.md before.md round-1.txt round-2.txt`); `scope-check-selftest.py` A4 source names the moved `§Scope and Constraints` |

### chunk-close-review.md

| Criterion | Status | Evidence |
|---|---|---|
| `script path in a command` in both executors; rows p11/p12 | pass | `grep -c` = 1 over `agents/chunk-verifier.md` and 1 over `skills/implement/SKILL.md`; linter exit 0 |
| Derivation command lists exactly the three modules | pass | V5 |
| Fixture: gc.py chunk no advisory, scope-check chunk advisory; real chunk recorded | pass / partial | `check3.sh` exit 0 / exit 2 as stated; the real-chunk quotation is V5's partial |

### drift-sweep.md

| Criterion | Status | Evidence |
|---|---|---|
| `literal-anchor` self-test case (three anchors, folded count 1; red without the rule; red with span-blanking) | pass | `gc.py --self-test` OK line names `literal-anchor (fence filter only, spans read, sha-pinned exempt, folded count)` |
| `--help` severities; none of the four in `FIXABLE` | pass | `--help`: `[literal-anchor] warn`, `[self-matching-grep] fail`, `[dead-path-citation] warn`, `[qimpl-malformed] fail`; `FIXABLE = ["xlink-dead", "index-requirements", "traceability-aggregate", "plan-history-name"]` |
| `--report` exits `OK`, folded lines counted at run time, exit unaffected | pass | `OK`, `[literal-anchor]` **7** files (`marketplace-packaging.md` 20, `skill-lint-v5.md` 2, `two-root-linter.md` 11, `requirements/index.md` 6, `integration/packaging.md` 21, `integration/skill-lint.md` 1, `requirements/traceability.md` 8), `[dead-path-citation]` 59 files |
| `self-matching-grep` self-test case, one line per grammar form | pass | OK line: `self-matching-grep (one fixture line per grammar form)` |
| `--report` 0 `self-matching-grep` at the landing commit; parent reports 4; pre-commit exit 0 | pass / not re-run | 0 on the tree; `pre-commit run --all-files` exit 0; the parent-commit scratch reading (4) is Chunk 3's recorded evidence, not re-run here |
| `qimpl-malformed` self-test case; `--report` 0 findings | pass | OK line names the case; `grep -c qimpl-malformed` over the report = 0 |
| `dead-path-citation` self-test case; 0 findings on the three repaired spec lines | pass | OK line names the case; the 59 folded warns are the standing floor (Minor 4), none on the repaired lines (`adversarial-verify.md`, `arbitrated-handoff.md`, `harness-commit-fidelity.md` carry no `[dead-path-citation]` line naming those repairs — 1 warn each on other lines) |
| traced-stale-chain case; §Routing at DONE row names the traced sub-kind | pass | OK line: `traced-stale-chain (traced pair warn, untraced info under --workstream)`; `drift-sweep.md:443` `needs a decision (added) \| literal-anchor, dead-path-citation, stale-chain traced shared-spec sub-kind`. Live: `skill-namespace-rename.md` and `harness-chunk-verifier.md` stale-chain lines are `INFO` (untraced class) |

### harness-agents.md

| Criterion | Status | Evidence |
|---|---|---|
| presence screen 3; full-surface per-body 3 | pass | `grep -lE 'git stash\|git state' plugins/sdd/agents/*.md \| wc -l` = 3; the ordered-alternation loop = 3 |
| rows p1–p3; temp-copy deletion names the file | pass | linter exit 0; `--self-test` runs the p1–p15 mutation loop (OK line) — not re-run per body here |
| `tools` excludes Write/Edit/NotebookEdit, declares Bash | pass | all three frontmatters: `tools: Read, Grep, Glob, Bash` |
| `reviewer.md` satisfies the per-producer witnesses | pass | 6 / 3 / 1,1,1 / 1 / 0 (table under review.md) |

### harness-loop-control.md

| Criterion | Status | Evidence |
|---|---|---|
| two landed pins; temp-copy red both ways | pass | `grep -c 'proceeds \*\*without re-review\*\*' SKILL.md` = 1; `grep -c 'then re-run the review for this stage'` = 0; linter and self-test exit 0 |
| routing text in force in the four files; `verification.md` names the gates | pass | `without re-review`: return-contract.md 1, spec 5; `default[^.]*proceed` 1; `not an exhaustion` 2; gates: V2 |
| `reject_run` walkthrough; row p4 | pass | W1; `grep -c 'consecutive consumed'` = 1 |
| `GROWTH: ` row; 6c/6d/7 order in SKILL.md and the spec | pass | `grep -c 'GROWTH: '` loop-control.md = 1; SKILL.md §The gate row `6c, 6d, 7 … CONVERGENCE: … GROWTH: …`; CLAUDE.md line names both `CONVERGENCE:` and `TELEMETRY:` |
| conditional `GROWTH:` quotation | partial | V4 |
| §2b `post-manual`, `proceed` withheld; interventions listed | pass | `grep -c 'post-manual' loop-control.md` = 6; V3 |
| `POST_MANUAL` footprint, `schema_diff`, two-record `[reason-review]` fixture, per-chunk walkthrough | pass | `grep -c POST_MANUAL telemetry.py` = 20; self-test names `schema table agrees with both renderings` and `test_post_manual_reason_review`; W2b |
| `mutations` formula, row p10, worked example, SKILL.md cites the derivation | pass | `grep -c mutations dispatch-templates.md` = 3; line 154 `budget: "1 chunk, ≤ 25 tool calls, ≤ 6 test runs" # 2 × 2 mutations + 2 gates`; SKILL.md line 197 `derived as 2 × mutations + gates` |
| telemetry witnesses (b), (c) | pass | self-test `test_cross_field_gate_rules` (b) and (c) pairs |

### harness-return-contract.md

| Criterion | Status | Evidence |
|---|---|---|
| §6b states both counts, placeholder rule, six pause texts; rows p9/p14 | pass | greps over return-contract.md: `tier/verdict conflict` 4, `missing section` 2, `counts as zero` 1, `material under APPROVE` 4, `0 material under APPROVE_WITH_FIXES` 2, `0 blocking under REJECT` 3; self-test exit 0 |
| fixtures F1–F9 walkthrough | pass | W3 |
| assertion (d) on the four non-`legal` classes and controls | pass | self-test `(d) the four non-legal cells — each a finding pair and a control pair`; live lint shows (d) firing on historical records with `C ≥ 1 under APPROVE_WITH_FIXES` and `M ≥ 1 under APPROVE` (Minor 5) |
| branching table fix-then-proceed; d1/d2 pair holds | pass | `without re-review` 1; linter exit 0 |

### harness-write-scope.md

| Criterion | Status | Evidence |
|---|---|---|
| void sentence in §1b and §8; rows p6/p7 | pass | `voids its verdict` 1 (loop-control.md); `voided` 2 (write-scope.md) |
| §1b bound line with `voided re-dispatch` and `REDO_MAX`; row p8 | pass | one visible line matches both (`grep -c` = 1); self-test exit 0 |
| `missing-token rule` cross-reference | pass | `grep -c` = 1 |
| assertion (a) on the chunk-0 shape | pass | self-test `(a) voided verdict consumed`; live lint 0 (a) findings |
| chunk-0 walkthrough; four git-state scenarios | pass | W2; 45/45 |

### marketplace-packaging.md

| Criterion | Status | Evidence |
|---|---|---|
| both `plugin.json` parse; strictly greater | pass | `tree 0.2.0 base 0.1.0 strictly greater: True` |
| `"version"` 1 in plugin.json, 0 in marketplace.json | pass | 1 / 0 |
| installed cache version recorded | pass | V6: 0.2.0 |

### pre-commit.md

| Criterion | Status | Evidence |
|---|---|---|
| `re` parse: settings.json matches, gc.py does not; scratch without `\.claude/` fails | pass | `matches .claude/settings.json: True \| plugins/sdd/tools/gc.py: False`; without the line: `False` |
| hook: tree skipped exit 0; scratch processed | pass | V11 |
| `#` reason comment; `--all-files` exit 0 | pass | `grep -c '#.*\.claude/'` = 1; pre-commit exit 0 |

### project-docs.md

| Criterion | Status | Evidence |
|---|---|---|
| `without re-review` 1, `consecutive consumed` 1, `iteration N of FIX_LOOP_MAX` 0 | pass | 1 / 1 / 0 |
| `GROWTH:` ≥ 1 on a line naming `CONVERGENCE:` or `TELEMETRY:` | pass | 1 / 1 |
| manifest path forms; files exist | pass | 2 / 0 / `ok` |
| diff touches only §Repository Structure and §Driver | not re-run | the row's Chunk 4 `awk` extraction against `fb4635f` is the recorded evidence; not re-run here (budget) |
| CHANGELOG exists under `plugins/sdd` and is named in `CLAUDE.md` (review r3 M2) | pass | `plugins/sdd/CHANGELOG.md` exists; `CLAUDE.md:13 plugins/sdd/CHANGELOG.md — Consumer-facing changelog, shipped with the plugin` |

### requirements-artifacts.md

| Criterion | Status | Evidence |
|---|---|---|
| (c)/(d) file-set equality | pass | 10 = 10, `diff` empty |
| (a) every amended body holds `[Updated:` and `**Amended` | **fail** | REQ-LINT-PACKAGING-007: `[Updated:` 1, `**Amended` 0 (Minor 1) |
| (b) Spec-cell grep 0; markers in Spec files; no contract only in an amendment section | pass | 0 over 37 rows; 11 files ≥ 1; the last clause was decided by the specs closing review (APPROVE) |
| (e) id-set equality; each block's `-l` re-run lists exactly the named files | pass / **fail** | sets equal (37 = 37); re-runs: 6 of 35 exact, 29 add the aggregate, 5 add `USAGE.md`/`reviewer.md` (Minor 2) |

### review.md

| Criterion | Status | Evidence |
|---|---|---|
| template carries the `VERDICT:` line and label lines; d1 row | pass | `grep -c 'VERDICT: APPROVE \| APPROVE_WITH_FIXES \| REJECT'` = 1; linter exit 0 |
| six labels / three prefixes / three predicates / empty-tier rule per producer | pass | SKILL.md 6 / 3 / 1,1,1 / 1; reviewer.md 6 / 3 / 1,1,1 / 1 |
| retired-wording grep 0 per file; live consumer sentence kept | pass | 0 / 0; `its position is not part of the contract` 1 |
| row p13 names both producers | pass | `skill-lint.py:381` fix string `restore the Approve with fixes predicate — No blocking finding; at least one Material finding`; files list carries both (self-test row-count pin moved to 57) |
| no fenced template shows a tier label followed by a placeholder item | pass | fence-scoped grep = 0 |
| F2 pause N = 1, F1 none, F8/F9 conflict pauses | pass | W3 |

### skill-lint-v5.md

| Criterion | Status | Evidence |
|---|---|---|
| `literal-anchor` `FORBIDDEN` row: visible anchor red, backticked red, fenced clean, `.py` exempt | pass (self-test) | `--self-test` `literal_anchor_visible_only` four cases (OK line); `visible_only` 9 occurrences in the tool; not re-run in a temp copy here |
| `--self-test` exit 0; pinned counts equal the row counts; fifteen markers red one by one | pass | exit 0; `--print-population` 57 / 15 = §6 |

### telemetry-reader.md

| Criterion | Status | Evidence |
|---|---|---|
| `flat-cg` self-test case over the frozen fixture | pass (with the unsatisfiable clause noted) | `test_flat_cg_migration (frozen flat fixture: migrated = mappable kinds, lost = gate + commit + pr per workstream on the first migrated record, zero typed findings, per-chunk block stamped partial, fixture refused and sha256 unchanged)`; "chunks 1–8 stamped partial" is unsatisfiable on the live file (V1, Q-IMPL-PIPELINEOBSERVABILITY-005) |
| `migrate --file <fixture>` exits 2; sha256 recorded; branch diff of fixtures adds only | pass | fixture `ff5cf286…ef370` present in `fixtures/README.md` (1 hit); 130 lines; `git diff fb4635f HEAD --stat -- plugins/sdd/tools/fixtures/` = `10 files changed, 302 insertions(+)`, 0 deletions |
| `[enum] migration.from` on `flat-xx`, none on `flat-cg`; case (c) re-pointed | pass | self-test `test_advisory_cases (c) migration.from flat-xx outside {chunk-string, flat-cg}` |
| `migration.lost` beside `chunk-string` → `[type] migration` | pass | `test_migration_lost_shape` |
| four cross-field cases with controls | pass | `test_cross_field_gate_rules` |
| p3/p4 fixture finding counts unchanged; `schema_diff` clean | pass | `--lint --file …p3…` → `70 finding(s), 3 warning(s)`; `…p4…` → `77 finding(s), 4 warning(s)`; `test_frozen_finding_sets_unchanged (p3 and p4 sorted-lines sha256)`; `schema table agrees with both renderings` |
| live `summarize --workstream consumer-geometry` count recorded | pass | V1: 36 |
| `POST_MANUAL` / `manual_intervention` / `malformed` ≥ 1; `post-manual` 0; two-record fixture | pass | 20 / 13 / 20 / 0; `test_post_manual_reason_review` |
| (c) and (d) pair shapes | pass | self-test OK line |

### telemetry.md

| Criterion | Status | Evidence |
|---|---|---|
| `--help` names `append` | pass | 4 occurrences |
| three `append` self-test cases; M1 reversion | pass | `test_append_cases (v-less object refused with the line count unchanged, [] refused writing nothing, the §2 example record appended and counted 1 by summarize, --help names append)` |
| four `TELEMETRY:` members; `append` in §3; SKILL.md names `rec <n>` and `.gitignore updated` | pass | 4 / 28 / 2 / 1 |
| gate path reads nothing from the file | pass | 0 over §3; 0 over §The gate |
| no dispatch template mentions `telemetry.py append` | pass | 0 |

### two-root-linter.md

| Criterion | Status | Evidence |
|---|---|---|
| three-way equality; self-test asserts it | pass | `--print-population` `REQUIRED=57 VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=15` = §6 dated line (`two-root-linter.md:207`); `grep -o 'grows by exactly [a-z]*' docs/spec/skill-lint-v5.md` → two lines, `1 grows by exactly fifteen` (`:470`) and `1 grows by exactly fourteen` (`:500`) — the stale half was red R1 / review M1, fixed at its origin (Minor 11); after the fix both read `fifteen` |
| `--self-test` passes; `pre-commit run --all-files` exit 0 | pass | Quality Gates |

## Gate-rendering walkthroughs

Transcribed by this stage from the landed rules (`loop-control.md` §2, §1b, §2b;
`return-contract.md` §6b); the orchestrator renders these gates, no shipped tool executes
them (Q-SPEC-PO-L).

### W1 — `reject_run` (V7; `loop-control.md` §2: `FIX_LOOP_MAX` = 3 compares against the run of consecutive consumed `REJECT`s; a consumed `APPROVE`/`APPROVE_WITH_FIXES` resets it to 0)

Sequence A, one stage, consumed in order `APPROVE_WITH_FIXES, REJECT, REJECT, APPROVE_WITH_FIXES`:

```
round 1  VERDICT: APPROVE_WITH_FIXES   reject_run = 0   → fix applied, gate offers proceed | manual intervention | stop
                                                          (fix-then-proceed, no re-review; operator chose a further round)
round 2  VERDICT: REJECT               reject_run = 1   → fix dispatch, packet line `iteration 1 of 3`
round 3  VERDICT: REJECT               reject_run = 2   → fix dispatch, packet line `iteration 2 of 3`
round 4  VERDICT: APPROVE_WITH_FIXES   reject_run = 0   → "not an exhaustion": fix applied, proceed offered
```

The exhausted gate (`Fix loop exhausted — stage: …, 3 of 3 iterations`, options
`stop | manual intervention | authorize extra iteration`) is **never rendered**:
`reject_run` peaks at 2.

Sequence B, `REJECT, REJECT, REJECT`:

```
round 1  VERDICT: REJECT   reject_run = 1   → fix, `iteration 1 of 3`
round 2  VERDICT: REJECT   reject_run = 2   → fix, `iteration 2 of 3`
round 3  VERDICT: REJECT   reject_run = 3   = MAX → no fourth fix dispatch:

Fix loop exhausted — stage: <stage>, 3 of 3 iterations
  iteration 1: C1 … ; iteration 2: … ; iteration 3: …
  stop | manual intervention | authorize extra iteration
```

The exhausted gate **is rendered** on the third consecutive consumed `REJECT`.
Under the pre-delta rule (every fix iteration counted) sequence A would have
exhausted at round 4 — the consumer-geometry observation (gap 3).

### W2 — the chunk-0 void sequence and the per-chunk manual intervention (V8; `loop-control.md` §1b, §2b; `write-scope.md` §8)

W2a — a `GIT_STATE` finding on the chunk verifier (the observed `git stash` at chunk 0):

```
Chunk 0 gate
  RETURN.status: COMPLETE
  SCOPE: VIOLATION — GIT_STATE (stash list grew by 1 during the verifier's run)
  CHUNK_VERDICT: FAIL (voided: GIT_STATE)        ← the leaf's PASS is consumed as FAIL, unverified is not verified
  resolve the finding:  restore │ accept (note) │ stop
    → restore:        tree restored — the verdict stays voided; offered: redo │ stop
    → accept (note):  finding noted — the verdict stays voided; offered: redo │ stop
  `proceed` is withheld after both options.
  redo = a fresh re-dispatch of the same verifier; chunk_redo_count unchanged (Redo: 0 of REDO_MAX)
         voided_redispatch_count[chunk 0 gate] = 1 (never shown in the Redo line)
  at voided_redispatch_count = REDO_MAX (3): the exhausted form `stop │ manual intervention` (§2a) → §2b
```

W2b — a manual intervention at a per-chunk gate (the observed `2266511` shape, chunk N):

```
Chunk N gate — operator edits the chunk deliverable (manual intervention)
  orchestrator observes its own edits (COMMIT: comparand over the manual commit range)
  dispatches the post-manual review: REVIEW template, chunk N's plan tasks + traced specs,
      dispatch.reason = POST_MANUAL, dispatch.chunk = N, dispatch.iteration = current reject_run
  chunk verifier NOT re-dispatched (it is a review, not a verifier)
  Redo: N of REDO_MAX — unchanged
  `proceed` withheld until the post-manual review's record exists and its verdict is consumed:
      REJECT → new reject_run = 1 ; APPROVE_WITH_FIXES → fix, then proceed ; APPROVE → proceed
  reject_run and gate.fix_iteration unchanged by the review itself
```

Observed instance this cycle: implement-stage manual intervention `2266511` → post-manual
review r3 (`APPROVE_WITH_FIXES`) → fix `e891ea2` → verifier `PASS` → proceed.
`scope-check-selftest.py`: `OK: 45/45 scenarios passed`.

### W3 — tier fixtures F1–F9 (V9; `return-contract.md` §6b; grammar of `review.md` §Report Format)

Each fixture is a whole report — the six label lines in producer order, the `VERDICT:`
token on its own line; only the Critical/Material sections and the token vary. Base
report (F1):

```
## Review: specs — fixture

**Verdict:** Approve with fixes
VERDICT: APPROVE_WITH_FIXES

**Strengths:**
- reads the whole artifact

**Critical findings:** [must fix before next phase]

**Material findings:** [should fix; can proceed with note]
- M1: heading X lacks its requires list — [docs/spec/x.md:§X] — affects [REQ-X-001]
- M2: table Y omits column Z — [docs/spec/y.md:§Y] — affects —

**Minor findings:** [polish; defer without documentation]
- m1: typo

**Recommendation:** apply M1, M2 and proceed
```

| Fixture | Critical section | Material section | Token | `blocking_items` / `material_items` | Rendered |
|---|---|---|---|---|---|
| F1 | empty | `M1`, `M2` | `APPROVE_WITH_FIXES` | 0 / 2 | **no pause** (cell C=0, M≥1 × AWF = legal) |
| F2 | `- C1: …` | `M1`, `M2` | `APPROVE_WITH_FIXES` | 1 / 2 | `REVIEW: MALFORMED (tier/verdict conflict: 1 blocking under APPROVE_WITH_FIXES)`, `N = 1` |
| F3 | label line **deleted** | `M1`, `M2` | `APPROVE_WITH_FIXES` | — | `REVIEW: MALFORMED (missing section: Critical findings)` (first pause in order) |
| F4 | `- None` | empty | `APPROVE` | 0 / 0 | **no pause**; likewise `- n/a` and `- —` (placeholders count as zero) |
| F4′ | `- None` then `- C1: …` | empty | `APPROVE` | 1 / 0 | `REVIEW: MALFORMED (tier/verdict conflict: 1 blocking under APPROVE)`, `N = 1` — the placeholder adds nothing beside a real item |
| F5 | `- C1: …` | `M1`, `M2` | `REJECT` | 1 / 2 | **no pause** (C≥1 × REJECT = legal) |
| F6 | F1–F5 re-emitted in `agents/reviewer.md`'s shape (`## Review: [phase] — [artifact]`, no Reviewer Context block, the same six labels) | | | same counts | **same results** — the consumer reads label lines and list markers only, and both producers carry the one label list |
| F7 | empty | `M1`, `M2` | `APPROVE` | 0 / 2 | `REVIEW: MALFORMED (tier/verdict conflict: 2 material under APPROVE)`, `N = 2` |
| F7′ | empty | `- None` | `APPROVE` | 0 / 0 | **no pause** |
| F7″ | empty | label line **deleted** | `APPROVE` | — | `REVIEW: MALFORMED (missing section: Material findings)` |
| F7‴ | empty | `M1`, `M2` | `APPROVE_WITH_FIXES` | 0 / 2 | **no pause** (= F1) |
| F8 | empty | empty | `APPROVE_WITH_FIXES` | 0 / 0 | `REVIEW: MALFORMED (tier/verdict conflict: 0 material under APPROVE_WITH_FIXES)` |
| F8′ | empty | `- M1: …` | `APPROVE_WITH_FIXES` | 0 / 1 | **no pause** |
| F9 | empty | empty | `REJECT` | 0 / 0 | `REVIEW: MALFORMED (tier/verdict conflict: 0 blocking under REJECT)` |
| F9′ | `- C1: …` | empty | `REJECT` | 1 / 0 | **no pause** (F5's shape) |

Every pause renders the existing option set `re-dispatch review │ accept prose
manually │ stop`. Case-table coverage: the eight non-`legal` cells are exercised by F2
(C≥1/M≥1 × AWF), F4′ (C≥1/M=0 × APPROVE), F7 (C=0/M≥1 × APPROVE), F8 (C=0/M=0 × AWF),
F9 (C=0/M=0 × REJECT), and — by the same conditions — F2 with M=0 (C≥1/M=0 × AWF),
F4′ with a Material item (C≥1/M≥1 × APPROVE), F7 with a Critical item under REJECT is
legal; the C=0/M≥1 × REJECT cell renders `0 blocking under REJECT` exactly as F9. The
four `legal` cells are F4/F7′ (APPROVE), F1/F8′ (AWF), F5/F9′ (REJECT, both C≥1 rows).

## Dogfooding map as observed (kickoff decision 3, constraint 3)

| Landed in | Gates that ran under it (observed) |
|---|---|
| Research gate (`25a4b56`, `754915c`): V3 routing, `GROWTH:` | every gate from the requirements stage on; the one `APPROVE_WITH_FIXES` that proceeded without re-review is implement r3 (V2); `GROWTH:` lines rendered at specs rounds 2–5 (`+112`, `+69`, `+108`, `+730`) as reported by the orchestrator (V4) |
| Chunk 1 (`c15e2f5`): tier-count rule, `reject_run`, `post-manual`, void rule, derived budget, grammar, git-state sentence, Check 3 convention | chunk gates 2–4 and the verify gate on the orchestrator's half; review rounds in them: implement r1 (REJECT → requirements 27.7), r2 (**VOIDED** — the read-only reviewer wrote `docs/spec/two-root-linter.md`; reverted; the void rule rendered), r3 (post-manual, AWF). **Half-claim (Minor 7):** every review leaf's body came from the installed cache's 0.1.0 `agents/reviewer.md` until OP-3, which carries none of the landed grammar (V6) |
| Chunk 2 (`f9b0a19`): validated `append`, `rec <n>` on exit 0, `POST_MANUAL`/`manual_intervention`/`malformed` | chunk gates 3–4, the verify gate; `summarize --workstream pipeline-observability` reads 72 records, `runs: RS-PIPELINEOBSERVABILITY-001`, implement redos `c1:0 c2:1 c3:1 c4:0`, `records-vs-expected: 72 recorded, expected 85 (13 missing; 3 mis-typed — see --lint)` |
| Chunk 3 (`63a893b`): gc rules 16–19, traced stale-chain `warn`, pre-commit sweep | Chunk 4's commit gate, this stage's gates (pre-commit `drift sweep (fast profile) Passed`); `GC:` at DONE pending |
| Chunk 4 (`b91566f`): `.claude/` exclusion, `CLAUDE.md` vocabulary, A4 | the verify gate and its commit gate (this stage: pre-commit exit 0 with `.claude/` excluded) |

Chunk gate history as handed over: Chunk 1 PASS; Chunk 2 FAIL → redo 1 → PASS; Chunk 3
BLOCKED (replan trigger → requirements 27.6) → redo 1 → PASS; Chunk 4 PASS.

## Traceability Verification (Step 3b)

Per-workstream file `docs/ws/pipeline-observability/traceability.md`, 37 rows: every row
has a non-empty Spec cell (criterion 1 parse), a non-empty Test cell and a non-empty
Implementation cell (REQ-REQ-PIPELINEOBSERVABILITY-001's Implementation cell records the
requirements-stage landing, index 27.x). No coverage gap. `Verified` written by this
stage: **36 × `pending-red`** (blue passed; red pending) and **1 × `fail`**
(REQ-REQ-PIPELINEOBSERVABILITY-001 — criteria (a) and (e) above). The shared aggregate
`docs/requirements/traceability.md` is **not** regenerated here: the dispatched write scope
omits it, which is the orchestrator's post-gate bookkeeping signal (REQ-WS-HARNESSP3-001);
the `[traceability-aggregate]` warning that may appear before that regeneration is the
designed handshake, not a finding on any cell. gc criterion for the `pending-red` cells:
see the post-write sweep line under §Regressions.

## User-Perspective Validation

| Scenario | Status | Notes |
|---|---|---|
| Operator reads the migrated past: `telemetry.py summarize --workstream consumer-geometry` | pass | 36 records, per-stage table populated, per-chunk block honest about what was lost (`partial — migrated from "Chunk 0"; … cannot be reconstructed`) |
| Operator reads the live cycle: `summarize --workstream pipeline-observability` | pass | 72 records with the cycle id; the `13 missing` fix records and `3 mis-typed` point the operator to `--lint` |
| `telemetry.py --help` | pass | names `append` as `ORCHESTRATOR-ONLY: read one JSON record from stdin, validate…` |
| `gc.py --help` | pass | the four new rules listed with severities and one-line meanings |
| `gc.py --report` on the tree | pass | `OK` with folded, counted warns — a reader sees 7 `literal-anchor` files and 59 `dead-path-citation` files without the exit status moving |
| Reviewer reads `agents/reviewer.md` | pass | the report shape, the empty-tier rule and the three disjoint predicates are stated in one place |
| Consumer installs the plugin | pass | cache 0.2.0 = repo tree (V6) |
| Contributor commits with `.claude/settings.json` present | pass | hook skips the path (V11) |

## Regressions

- Regression base: `git merge-base HEAD main` = `fb4635f`, extracted with `git archive`
  into `$TMPDIR/po-base` (git-initialised for the tools' root probe). At the base:
  `skill-lint.py --self-test` exit 0; `gc.py --self-test` exit 0;
  `scope-check-selftest.py` exit 0 (`44/44`); **`telemetry.py --self-test` exit 1**
  (`schema rendering missing: …/plugins/sdd/docs/spec/telemetry.md` — the pre-existing
  defect consumer-geometry's report recorded as its Minor 1; Q-IMPL-PIPELINEOBSERVABILITY-003)
  → at HEAD exit 0: a fix, not a regression. `skill-lint.py .` at the base:
  `OK: 25 file(s) clean` (same at HEAD).
- Drift sweep at the base: `OK: 9 sweep(s) clean, 0 warning(s), 29 info`, 0 `FAIL`. At
  HEAD: `OK: 10 sweep(s) clean, 68 warning(s), 36 info`, 0 `FAIL`. **No `fail`-severity
  finding was added.** The 68 warnings are 66 from the two new `warn` rules
  (`literal-anchor` 7, `dead-path-citation` 59 — the standing floor the kickoff and
  index §Out of Scope route `record | ignore` at DONE) plus **2 `[qimpl-broken-ref]`
  warns new on the branch outside the four rules** (Minor 3).
- `git diff --stat fb4635f -- docs/spec`: 20 files, +2497/−50; fixtures: 10 files,
  +302/−0 (added only). No unintended path observed in the branch log (26 commits, all
  `pipeline-observability`-scoped).
- Post-write drift sweep over the tree carrying this report and the `pending-red` cells:
  `gc.py --report --root . --workstream pipeline-observability` → `OK: 10 sweep(s) clean,
  68 warning(s), 33 info`, 0 `FAIL`; the only line touching a traceability file is the
  designed handshake `WARN docs/requirements/traceability.md: [traceability-aggregate]
  aggregate differs from regenerate(docs/ws/*/traceability.md)` — no finding on a
  `pending-red` cell.

## Deferral-Backlog Screen (Step 5b, REQ-REQ-HARNESSP6-001)

Phrase table read from `requirements-artifacts.md` §`## Out of Scope` Discipline (22
rows); marker = a bracketed dated token on the line or the line above (the item-scoped
rule of 2026-09-21 widens attachment to a preceding standalone marker line; no such line
changed a result below). One row per path the glob `docs/ws/*/verification.md` returned:

| Path | Section lines | Phrase hits | Live |
|---|---|---|---|
| `docs/requirements/index.md` §Out of Scope | 333 | 2 | **2** — `index.md:2273` "the repair is **a later cycle**'s task bounded to those files (Q-REQ-PO-R)"; `index.md:2274` flagged by the screen on the bullet "The six carried tool-debt items from `consumer-geometry`, …" (no table row could be attributed on re-reading — a possible over-match of this run's extractor) |
| `docs/ws/consumer-geometry/verification.md` §Next Steps | 13 | 0 | 0 |
| `docs/ws/default/verification.md` | 43 | 3 | 0 |
| `docs/ws/harness-p2/verification.md` | 15 | 0 | 0 |
| `docs/ws/harness-p3/verification.md` | 92 | 12 | 0 |
| `docs/ws/harness-p4/verification.md` | 14 | 5 | 0 |
| `docs/ws/harness-p5/verification.md` | 93 | 6 | 0 |
| `docs/ws/harness-p6/verification.md` | 13 | 0 | 0 |
| `docs/ws/marketplace/verification.md` | 9 | 0 | 0 |
| `docs/ws/packaging/verification.md` | 30 | 2 | **2** — `:435` "carry it to a later cycle (REQ-PKG-PACKAGING-009)", `:445` "is a later cycle's decision" (pre-existing; consumer-geometry's Minor 2 listed them; owned by the packaging workstream) |

Paths returned 9, rows walked 9 (this workstream's own report did not exist when the
glob ran). Phrase coverage is a screen over observed vocabulary, not a proof of absence;
a zero above is not an absence of latent work. Live findings: Minor 6 and Minor 9.

## Issues Found

### Critical (blocks release)

- None.

### Minor (can ship, fix later)

1. **REQ-LINT-PACKAGING-007's amended body lacks the `**Amended` marker**
   (`docs/requirements/integration/skill-lint.md`: `[Updated: 2026-09-22]` 1,
   `**Amended` 0) — `requirements-artifacts.md` §Amendment Landing (a) fails for one of
   sixteen bodies. Origin: the requirements stage (27.4 joined the row from the specs
   closing review). Not fixed here (write scope; kickoff constraint 5 places the fix at
   the origin).
2. **Sweep-block re-runs (clause (e)) list files the blocks do not name.** 29 of 35
   blocks list `docs/requirements/traceability.md` — the orchestrator-regenerated
   aggregate whose Test cells quote every pattern — which no block names and the clause
   does not exempt; 5 blocks list a file the implement-stage fix `e891ea2` wrote after
   the blocks: `plugins/sdd/skills/orchestrate/USAGE.md` (REQ-HARN-PIPELINEOBSERVABILITY-002,
   -003, REQ-HARN-HARNESSP6-001) and `plugins/sdd/agents/reviewer.md`
   (REQ-HARN-PIPELINEOBSERVABILITY-001, REQ-HARN-013). The first is a clause-design
   question (exempt the derived aggregate, or name it); the second is the drift class the
   clause exists to detect, and it detected it. Origin: requirements.
3. **Two `[qimpl-broken-ref]` warns new on the branch, outside the four new rules:**
   `docs/spec/skill-lint-v5.md:902` Q-IMPL-PIPELINEOBSERVABILITY-011 names `§Report
   Format` (no such heading in that spec); `docs/spec/marketplace-packaging.md:638`
   Q-IMPL-PIPELINEOBSERVABILITY-012 names `§Repository Structure` (no such heading there).
   Warn severity; fix = rename each reference to an existing heading.
4. **Standing `warn` floor** routed `record | ignore` at DONE: `literal-anchor` 7 files
   (69 anchors on 2026-09-22: `marketplace-packaging.md` 20, `two-root-linter.md` 11,
   `skill-lint-v5.md` 2, `requirements/index.md` 6, `integration/packaging.md` 21,
   `integration/skill-lint.md` 1, `requirements/traceability.md` 8) and
   `dead-path-citation` 59 files (the aggregate and `integration/skill-lint.md` carry
   the bulk; pre-rename citations in history prose). A specs-layer question stands:
   whether dated/history blocks should be exempt from the two rules.
5. **Telemetry assertions on the orchestrator's own records.** The live `--lint` shows
   (b) firing 27× (`fix_iteration N exceeds the run of consecutive REJECTs` — every
   stage's fix counter incremented across non-`REJECT` verdicts, this cycle's routed
   origin fixes and the voided round r2 included) and (d) 40× on historical
   `C ≥ 1 under APPROVE_WITH_FIXES` / `M ≥ 1 under APPROVE` rounds; four
   `[reason-review]` warnings (research, requirements, specs, plan). How a voided round
   and a routed origin fix are counted is an open schema question; (a) and (c) are
   clean.
6. **Live deferral phrase in `docs/requirements/index.md` §Out of Scope** (`:2273`,
   "a later cycle's task", Q-REQ-PO-R) with no adjacent dated marker — the settled
   exclusion should state its reasoning without naming a successor. Origin:
   requirements.
7. **Dogfooding half-claim (review r2 M5).** Every review leaf of this cycle was
   dispatched with the installed cache's 0.1.0 `agents/reviewer.md` (0 occurrences of
   the landed grammar) until OP-3 installed 0.2.0; the orchestrator's half (gate
   rendering, counting, void rule) ran under the landed rules from `c15e2f5`. The
   producer-side grammar (rows p13, the disjoint predicates) is therefore pinned but
   was not exercised by a live review this cycle. A 0.1.0 directory remains in the
   cache beside 0.2.0.
8. **Row p15's pin is weak** (verifier): `skills/orchestrate/USAGE.md` carries the
   pinned phrase four times; deleting only the §7b occurrence leaves the row green.
9. **Pre-existing live deferrals in `docs/ws/packaging/verification.md` §Next Steps**
   (`:435`, `:445`) — consumer-geometry's Minor 2 (carried forward from
   RS-CONSUMERGEOMETRY-001's report by observation; that report is not the one this
   file replaces). Owned by the packaging workstream; outside this write scope.
10. **Reconciliations recorded, not fixed:** the plan's OP-2 text omits the required
    `--file` argument; the Chunk 2 fixture run reported packaging 42 lost where the live
    migrate reports 41 (fixture 77 packaging lines = 36 + 41); the `telemetry-reader.md`
    clause "chunks 1–8 stamped `partial`" is unsatisfiable on the live file
    (Q-IMPL-PIPELINEOBSERVABILITY-005); the p3/p4 frozen fixtures do hold shapes (b)/(d),
    so the spec's "unchanged" claim was false and the self-test compares pre-delta sets
    with (a)–(d) excluded (Q-IMPL-PIPELINEOBSERVABILITY-006).

**Carry-or-close.** No previous `docs/ws/pipeline-observability/verification.md` existed
(the workstream's first cycle), so there is no Minor to carry or close under
REQ-SKILL-HARNESSP3-001; Minor 9 is noted from the superseded workstream's report as
context only.

11. **The population `56 → 57` drift was stated stale in five corpus surfaces** (red round
    1, R1 and R2; review M1): `docs/requirements/integration/skill-lint.md` (REQ-LINT-
    PACKAGING-007 as amended, nine statements), `docs/requirements/index.md`,
    `docs/requirements/functional/review.md`, `docs/spec/skill-lint-v5.md` §Self-Test
    Extension and §Acceptance, and the delta map's Q-SPEC-PO-U all carried the Chunk 1
    arithmetic (fourteen rows, `REQUIRED=56`) after row p15 moved the live population to
    57 at the implement-stage fix `e891ea2`; the Implementation cell of -007 in both
    traceability files quoted `56 / 9 / 7 / 15`. The three-way equality held at 57
    throughout, so no self-test or gate failed — exactly the stated-number failure this
    cycle exists to close, found only by re-running the requirement's own `grep -c` claim.
    Origin: the requirements stage (27.4 stated the post-delta totals as arithmetic).
    Fixed at the origin by the orchestrator's manual intervention (index 27.8) and flowed
    to the spec, the delta map, the plan (note only) and the traceability cell.
12. **V4 partial — the `GROWTH:` lines for the requirements, plan and implement rounds
    were not preserved** (review M3): the orchestrator handed this stage the rendered
    lines for the specs stage only, so the conditional-quotation criterion is decided for
    one stage of five. Not fixable here: the lines are ephemeral gate text. Next cycle the
    orchestrator hands the verify dispatch every rendered `GROWTH:` line, or telemetry
    records the delta (see §Next Steps).
13. **V5 partial — the real chunk's verifier Check 3 text was not among this stage's
    inputs** (review M3): the criterion is recorded from the per-chunk gate outcome
    (`CHUNK_VERDICT: PASS`) and the derivation command plus the `check3.sh` fixture, not
    from the verifier's own Check 3 sentence. Next cycle the verify dispatch carries the
    verifier returns for one real chunk (see §Next Steps).

## Recommendation

- [x] Ship as-is (blue: zero Critical; red verdict pending — the orchestrator dispatches
      the red team and flips `pending-red → pass` at DONE)
- [ ] Fix critical issues then ship (invoke replan)
- [ ] Significant rework needed (invoke replan)

The thirteen Minors are documentation and floor items; Minors 1, 2, 6 and 11 are requirements-
origin corrections (kickoff constraint 5) and should be routed to a requirements
dispatch, not fixed in place by a later stage.

## Next Steps

- Requirements-origin corrections: add the `**Amended` note to REQ-LINT-PACKAGING-007's
  body (Minor 1); decide clause (e)'s treatment of the regenerated aggregate and re-run
  the five drifted sweep blocks against `USAGE.md` / `reviewer.md` (Minor 2); restate
  index §Out of Scope `:2273` as a settled exclusion or close it with a dated marker
  (Minor 6).
- gc qimpl-broken-ref: `docs/spec/skill-lint-v5.md:902` — rename Q-IMPL-PIPELINEOBSERVABILITY-011's spec reference to an existing heading; `docs/spec/marketplace-packaging.md:638` — the same for Q-IMPL-PIPELINEOBSERVABILITY-012 (Minor 3).
- gc literal-anchor: 7 files / 69 anchors and gc dead-path-citation: 59 files — the standing `warn` floor for the DONE `record | ignore` decision (Minor 4; index §Out of Scope binds the repair to those files); the specs-layer question whether dated/history blocks are exempt from both rules is open.
- gc stale-chain: `docs/spec/skill-namespace-rename.md` — `INFO … [stale-chain] spec older than requirements it requires: docs/requirements/integration/skill-lint.md (2026-09-22) is newer than skill-namespace-rename.md (2026-09-21) (ids: REQ-LINT-PACKAGING-008)` — untraced shared-spec class, stays `info`, routed `record | ignore` at DONE (Chunk 4 task 6 (iii)); the sibling `harness-chunk-verifier.md` line is the same class by design.
- Hook-enforcement spike (Chunk 4 task 1, performed by the orchestrator from documentation, **unmeasured**): `PreToolUse` stdin carries `agent_id` and `agent_type` inside a subagent; an agent's frontmatter may declare hooks that run only while it is active; `SubagentStart`/`SubagentStop` carry `agent_type`. A positive answer makes enforcement of read-only leaves feasible; no contract changed this cycle; a live measurement is the precondition before any binding, no requirement exists for it and none is created here.
- Telemetry schema question (Minor 5): how a voided review round and a routed origin fix are counted so that assertion (b) and `[reason-review]` do not fire on the orchestrator's own compliant records.
- Row p15 tightening (Minor 8): pin the §7b occurrence in `USAGE.md` by section, not by file-level count.
- Dogfooding half-claim (Minor 7): the producer-side review grammar has no live review round under 0.2.0 yet; the red round of this stage and the DONE `GC:` line are the first gates whose leaves run the 0.2.0 bodies; the stale 0.1.0 cache directory is the operator's to remove.
- OP-2 record: 72 migrated of 328 lines; consumer-geometry 36 / 17 lost (commit 2, gate 14, pr 1), per-chunk block chunk 0 only, stamped `partial`; packaging 36 / 41 lost; unknown-schema skipped 0; lint 245 → 123; second run wrote nothing; the plan's OP-2 text omits `--file`; fixture-vs-live packaging lost count 42 vs 41 to reconcile (Minor 10).
- OP-3 record: cache `…/sdd/0.2.0/` reads 0.2.0 with zero files differing from `plugins/sdd`; `0.1.0` remains beside it; the 0.2.0 marketplace update is exercisable only after the PR merges.
- V11 sandbox note: the scratch-copy hook run decides inside the sandbox when the copy is under `$TMPDIR`; the chunk's `PermissionError: [Errno 1] Operation not permitted: '.claude/settings.json'` was a path denial, recorded as the reason task 7 wrote `not decided here:`.
- CHANGELOG discipline (review r3 M2, Q-IMPL-012): `plugins/sdd/CHANGELOG.md` exists and `CLAUDE.md:13` names it; the components-as-sets check covers skills and agents only — no tool enforces the changelog's presence; this stage's line above is the verify-time check.
- Hypothesis for the operator to judge at DONE (not a verify finding): "fix a downstream finding at its origin and come back" — requirements origin fixes 27.3, 27.4 (specs stage), 27.6, 27.7 (implement stage) each removed the class at the origin; two were caused by forms the orchestrator's packets recommended; the closing-review exit closed requirements (8 + 1), specs (5 + 3), plan (1 + 3).
- Observation for the operator (V2): while kickoff constraint 4 ("exit only on `APPROVE`") stands, the V3 routing's `proceed` on `APPROVE_WITH_FIXES` is taken only at a stage whose closing round is the last (implement r3 here); the two rules are consistent but the routing's fix-then-proceed branch is exercised once per cycle at most.
- V4 / V5 evidence not preserved (Minors 12, 13): the next cycle's verify dispatch must carry every rendered `GROWTH:` line (or telemetry must record the visible-line delta per review round) and the chunk verifier's return for at least one real chunk; until then the two criteria stay `partial`, decided for one stage and from the gate outcome respectively.
- Stated-number drift (Minor 11): the corpus still states post-delta populations as prose in three requirements and two specs; a next-cycle piece may replace every such statement with the `--print-population` command plus a dated observation, the form Q-SPEC-PO-V already prescribes for the delta map.
- Once the red round closes and the status flips to `pass`, the active plan may be archived to `docs/ws/pipeline-observability/plan-history/`.
