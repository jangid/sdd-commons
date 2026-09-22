---
workstream: pipeline-observability
last_updated: 2026-09-22
---

# Traceability — pipeline-observability

Rows owned by the `pipeline-observability` workstream (per
`docs/spec/ws-traceability.md`). One row per requirement this workstream
delivers — the twenty-one new `*-PIPELINEOBSERVABILITY-*` ids and the sixteen
existing requirements it amends in place (each amendment row is marked
`(amended)` in the Requirement cell; per REQ-REQ-PIPELINEOBSERVABILITY-001 (c)
the marker means this workstream changed the id and does not own it, so the
regenerated aggregate keeps the owner's row as the id's row). The Spec column is filled by `sdd:specs`
(re-derived on 2026-09-22 against requirements 27.2: every cell names the
owning spec's **section of record**, never its `§Pipeline-Observability
Amendment` section, per REQ-REQ-PIPELINEOBSERVABILITY-001 (b)); Test / Implementation / Verified
are filled by `sdd:implement` and `sdd:verify` at later stages and are blank
until then. The shared aggregate `docs/requirements/traceability.md` is
regenerated from this file and its siblings by the orchestrator at the stage
gate — never hand-edited, and never by a leaf. The spec comparands cited by
the corpus-sweep blocks (`docs/spec/pipeline-observability.md` and the
amended specs) are the re-derived specs-stage output of 2026-09-22.

`Verified` takes the values of `docs/spec/ws-traceability.md` §Legal `Verified`
Cell Values. Rows created by the requirements stage on 2026-09-22.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-AGENT-MARKETPLACE-002 (amended) | harness-agents.md §The frontmatter contract | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (rows p1–p3 mutation loop); the ordered-alternation grep per body reads 3 | `plugins/sdd/agents/reviewer.md`, `chunk-verifier.md`, `red-team.md` — git-state sentence in each read-only paragraph | |
| REQ-AGENT-PIPELINEOBSERVABILITY-001 | harness-agents.md §The frontmatter contract | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (rows p1–p3, p13 on `agents/reviewer.md`); `grep -lE 'git stash'` over `plugins/sdd/agents/*.md` reads 3 | `plugins/sdd/agents/reviewer.md` §The report you write, §What your token means; the three bodies' git-state sentence | |
| REQ-ARB-HARNESSP2-002 (amended) | arbitrated-handoff.md §Contradiction Classes | pipeline-observability | `grep -c 'new\[N\]'` over `loop-control.md` ≥ 1 (Chunk 1 task 11); scenario A4 lands in Chunk 4 task 2 | `plugins/sdd/skills/orchestrate/references/loop-control.md` §2a — `new[N]` third term of `W_N` | |
| REQ-ARB-HARNESSP3-001 (amended) | arbitrated-handoff.md §`W_N` Includes Regeneration Writes | pipeline-observability | `grep -c 'new\[N\]'` over `loop-control.md` ≥ 1; scenario A4 in Chunk 4 task 2 | `plugins/sdd/skills/orchestrate/references/loop-control.md` §2a — `W_N` union gains `new[N]` | |
| REQ-ARB-PIPELINEOBSERVABILITY-001 | arbitrated-handoff.md §Contradiction Classes | pipeline-observability | `grep -c 'new\[N\]'` over `loop-control.md` ≥ 1; scenario A4 in Chunk 4 task 2 | `plugins/sdd/skills/orchestrate/references/loop-control.md` §2a — `new[N]` definition and decision procedure | |
| REQ-CHKC-004 (amended) | chunk-close-review.md §Checklist | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (rows p11, p12); `plugins/sdd/tools/fixtures/check3-declared-convention-2026-09-22/check3.sh` — `chunk-gc.md` exit 0, `chunk-scope-check.md` exit 2 | `plugins/sdd/skills/implement/SKILL.md` Check 3; `plugins/sdd/agents/chunk-verifier.md` Check 3 bullet; the two-sided fixture | |
| REQ-DOCS-PIPELINEOBSERVABILITY-001 | project-docs.md §`CLAUDE.md` | pipeline-observability | | | |
| REQ-GC-HARNESSP2-002 (amended) | drift-sweep.md §Sweep Table | pipeline-observability | | | |
| REQ-GC-HARNESSP2-003 (amended) | drift-sweep.md §Q-IMPL Counting Rule | pipeline-observability | | | |
| REQ-GC-HARNESSP6-003 (amended) | drift-sweep.md §Shared-Spec Staleness | pipeline-observability | | | |
| REQ-GC-PIPELINEOBSERVABILITY-001 | drift-sweep.md §Sweep Table | pipeline-observability | | | |
| REQ-GC-PIPELINEOBSERVABILITY-002 | drift-sweep.md §Sweep Table | pipeline-observability | | | |
| REQ-GC-PIPELINEOBSERVABILITY-003 | drift-sweep.md §Q-IMPL Counting Rule | pipeline-observability | | | |
| REQ-GC-PIPELINEOBSERVABILITY-004 | drift-sweep.md §Sweep Table | pipeline-observability | | | |
| REQ-HARN-001 (amended) | harness-loop-control.md §Fix-Loop Cap | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (row p4) | `plugins/sdd/skills/orchestrate/references/loop-control.md` §2 — `reject_run`, consecutive consumed `REJECT`s | |
| REQ-HARN-013 (amended) | harness-return-contract.md §VERDICT Token | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (rows p9, p14) | `plugins/sdd/skills/orchestrate/references/return-contract.md` §6b Tier-heading parsing | |
| REQ-HARN-HARNESSP6-001 (amended) | harness-write-scope.md §Git-State Observation | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (rows p6, p7, p8) | `plugins/sdd/skills/orchestrate/references/loop-control.md` §1b; `write-scope.md` §8 voided-verdict row | |
| REQ-HARN-PIPELINEOBSERVABILITY-001 | harness-loop-control.md §Fix-Loop Cap | pipeline-observability | `REQUIRED` row `proceeds **without re-review**` and `FORBIDDEN` `then re-run the review for this stage` — each red in a temp copy (Chunk 1 task 12) | `plugins/sdd/skills/orchestrate/SKILL.md` §The gate; `references/loop-control.md` §5a, §2 (landed at the research gate, confirmed) | |
| REQ-HARN-PIPELINEOBSERVABILITY-002 | harness-loop-control.md §Gate Signal Order | pipeline-observability | `REQUIRED` row `GROWTH: ` — red in a temp copy with item 6d deleted (Chunk 1 task 12) | `plugins/sdd/skills/orchestrate/references/loop-control.md` §5 item 6d; `SKILL.md` §The gate (landed at the research gate, confirmed) | |
| REQ-HARN-PIPELINEOBSERVABILITY-003 | harness-loop-control.md §Fix-Loop Cap | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (row p5) | `plugins/sdd/skills/orchestrate/references/loop-control.md` §2b — `post-manual` review | |
| REQ-HARN-PIPELINEOBSERVABILITY-004 | harness-write-scope.md §Git-State Observation | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (rows p6, p7, p8); p6 red with the bound line kept | `plugins/sdd/skills/orchestrate/references/loop-control.md` §1b void sentence and bound; `write-scope.md` §8; `dispatch-templates.md` missing-token rule | |
| REQ-HARN-PIPELINEOBSERVABILITY-005 | harness-return-contract.md §VERDICT Token | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (rows p9, p14) | `plugins/sdd/skills/orchestrate/references/return-contract.md` §6b — both counts, placeholder rule, six pauses, case table | |
| REQ-HARN-PIPELINEOBSERVABILITY-006 | harness-loop-control.md §Budget Slot | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (row p10) | `plugins/sdd/skills/orchestrate/references/dispatch-templates.md` §Slot contract (pipeline) `{budget}`; `return-contract.md` §Budget grammar; `SKILL.md` §Per-chunk implement dispatch | |
| REQ-LINT-PACKAGING-007 (amended) | two-root-linter.md §6. Counts: asserted, or only printed | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (`print_population_shape` — three-way equality read from §6; the three single-side mutations red in temp copies, Chunk 1 task 11) | `plugins/sdd/tools/skill-lint.py` `spec_population()`, `print_population_shape`; `docs/spec/two-root-linter.md` §6 (`56 / 9 / 7 / 15`) | |
| REQ-LINT-PIPELINEOBSERVABILITY-001 | skill-lint-v5.md §`FORBIDDEN` Row — `literal-anchor` | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (`literal_anchor_visible_only` four cases; the p1–p14 mutation loop) | `plugins/sdd/tools/skill-lint.py` — `FORBIDDEN` row `literal-anchor` with `visible_only`; `REQUIRED` rows p1–p14; `required_targets()` | |
| REQ-PC-PIPELINEOBSERVABILITY-001 | pre-commit.md §Design | pipeline-observability | | | |
| REQ-PKG-PIPELINEOBSERVABILITY-001 | marketplace-packaging.md §The manifest pair | pipeline-observability | | | |
| REQ-REQ-PIPELINEOBSERVABILITY-001 | requirements-artifacts.md §Amendment Landing | pipeline-observability | | | |
| REQ-REV-002 (amended) | review.md §Report Format | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (row p13, both producers); the six-label, prefix, predicate and retired-wording greps of `review.md` §Report Format read 6 / 3 / 1 / 0 per producer | `plugins/sdd/skills/review/SKILL.md` §Step 5 (grammar, verdict predicates); `plugins/sdd/agents/reviewer.md` §The report you write | |
| REQ-REV-PIPELINEOBSERVABILITY-001 | review.md §Report Format | pipeline-observability | `plugins/sdd/tools/skill-lint.py --self-test` (row p13, both producers); the same greps | `plugins/sdd/skills/review/SKILL.md` §Step 5; `plugins/sdd/agents/reviewer.md` §The report you write, §What your token means | |
| REQ-TELEM-HARNESSP2-004 (amended) | telemetry.md §Writer | pipeline-observability | `plugins/sdd/tools/telemetry.py --self-test` (`test_append_cases`); mutation M1 (validation step removed) red in a temp copy (Chunk 2 task 7) | `plugins/sdd/tools/telemetry.py` `append()`, `APPEND_FATAL_CLASSES`; `plugins/sdd/skills/orchestrate/references/telemetry.md` §3 writer sequence (validation failure = `WRITE FAILED`) | |
| REQ-TELEM-HARNESSP3-001 (amended) | telemetry.md §Positive Gate Line `TELEMETRY: rec <n>` | pipeline-observability | the `telemetry.md` §Acceptance greps run at the Chunk 2 close: the `TELEMETRY: ` gate-line grep reads 4 rows, `append` in §3 ≥ 1, the zero-reads grep reads 0 over §3 and §The gate, `telemetry.py append` absent from both dispatch references | `plugins/sdd/skills/orchestrate/references/telemetry.md` §3 (`rec <n>` only on `append` exit 0); `plugins/sdd/skills/orchestrate/SKILL.md` §The gate | |
| REQ-TELEM-HARNESSP4-005 (amended) | telemetry-reader.md §In-Place Migration of the 8 p3 Records | pipeline-observability | `plugins/sdd/tools/telemetry.py --self-test` (`test_flat_cg_migration`: the fixture refused as `--file`, sha256 before and after, second run a no-op) | `plugins/sdd/tools/telemetry.py` `migrate()` (both shapes in order, line-count check allowing the lost records), `migrate_flat()`, `flat_to_v2()` | |
| REQ-TELEM-HARNESSP5-008 (amended) | telemetry-reader.md §Schema Lint | pipeline-observability | `plugins/sdd/tools/telemetry.py --self-test` (`test_advisory_cases` (c) re-pointed at `flat-xx`); mutation M2 (enum check removed) red in a temp copy | `plugins/sdd/tools/telemetry.py` `lint_records` `[enum] migration.from` over `MIGRATION_FROM_MEMBERS` | |
| REQ-TELEM-PIPELINEOBSERVABILITY-001 | telemetry.md §Writer | pipeline-observability | `plugins/sdd/tools/telemetry.py --self-test` (`test_append_cases` — `v`-less refused with the line count unchanged, `[]` refused, §2 example appended and counted 1, `--help` names `append`); mutation M1 red | `plugins/sdd/tools/telemetry.py` `append` subcommand; `plugins/sdd/skills/orchestrate/references/telemetry.md` §3; `plugins/sdd/skills/orchestrate/SKILL.md` §The gate | |
| REQ-TELEM-PIPELINEOBSERVABILITY-002 | telemetry-reader.md §In-Place Migration of the 8 p3 Records | pipeline-observability | `plugins/sdd/tools/telemetry.py --self-test` (`test_flat_cg_migration` over the frozen flat fixture, counts derived at run time; `test_migration_lost_shape`) | `plugins/sdd/tools/telemetry.py` `flat_kind()`, `flat_to_v2()`, `migrate_flat()`, `_check_value("migration")`; the `migration` row of `docs/spec/telemetry.md` §Record Schema and `references/telemetry.md` §2 | |
| REQ-TELEM-PIPELINEOBSERVABILITY-003 | telemetry-reader.md §Schema Lint | pipeline-observability | `plugins/sdd/tools/telemetry.py --self-test` (`test_cross_field_gate_rules` (a)–(d) finding + control pairs, `test_post_manual_reason_review`, `test_frozen_finding_sets_unchanged`); mutations M3–M6 red in temp copies | `plugins/sdd/tools/telemetry.py` `gate_rule_findings()`, `REASON_MEMBERS` (`POST_MANUAL`), `gate.decision` members; the `reason` / `decision` rows and normalisation tables of both renderings | |
