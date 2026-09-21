---
workstream: packaging
last_updated: 2026-09-21
---

# Traceability — packaging

Rows owned by the `packaging` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd:specs`, `sdd:implement` and `sdd:verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited, and never by a leaf: regeneration is the
orchestrator's post-gate bookkeeping.

`Verified` takes the values of `docs/spec/ws-traceability.md` §Legal `Verified`
Cell Values — `pass | fail | pending-red | descoped`. Rows were added at the
requirements stage on 2026-09-21, the `Spec` column filled by `sdd:specs` the
same day, and `Test` / `Implementation` filled by `sdd:implement` as each chunk
landed — `Verified` is `sdd:verify`'s cell and is intentionally blank. The two
`REQ-PC-MARKETPLACE-*` rows are here because this workstream delivered their
evidence: the gate's hook set was amended and re-checked inside this cycle
(C9.4, C10.7). Their requirement text lives in the shared corpus, as every
row's does.

**Requirement → plan task.** The matrix shape is fixed at the six columns of
`docs/spec/ws-traceability.md` §The Per-Workstream File, so the plan stage adds
no `Task` column — a seventh cell makes every row unparseable and the drift
sweep drops it from the regenerated aggregate (`[traceability-rowdrop]`). The
per-requirement task mapping `sdd:plan` produced on 2026-09-21 therefore lives
in `docs/ws/packaging/plan.md` §Requirement → Task Coverage, which carries one
row per requirement in this table, keyed by the same ids.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-DOCS-PACKAGING-001 | project-docs.md | packaging | retired filename 0 matches; positive `README.md` match (C6.6) | `orchestration.md:574` (C6.2) |  |
| REQ-DOCS-PACKAGING-002 | project-docs.md | packaging | marker string-equality vs `docs/.sdd-version` (C0.4) | `CLAUDE.md` §Multi-Workstream Layout (C0.3) |  |
| REQ-DOCS-PACKAGING-003 | project-docs.md | packaging | screen re-run, occurrences=24 live=0; fixture distinguishes both rules (C6.7) | item-scoped rule + supersession pointer in `requirements-artifacts.md` (C6.4, C6.5) |  |
| REQ-LINT-PACKAGING-001 | two-root-linter.md | packaging | `retired_scope_binds_per_entry` (C2.4) | `RETIRED_SCOPE_BINDING`, `retired_scope_entries()`, `check_retired_prefix()` (C2.1) |  |
| REQ-LINT-PACKAGING-002 | two-root-linter.md | packaging | `template_pairs_bind_per_side`, 3 geometries + negative control (C3.9) | `check_template_drift()` per-side; spec-side-only disjoint skip (C2.2, C3.9) |  |
| REQ-LINT-PACKAGING-003 | two-root-linter.md | packaging | `manifest_pair_membership` (C3.3) | union binding for `.claude-plugin` (C2.1) |  |
| REQ-LINT-PACKAGING-004 | two-root-linter.md | packaging | three no-pinned-count greps, pre-move (C4.2); re-run post-move at C7.8 | `print_population()` emission half (C4.1) |  |
| REQ-LINT-PACKAGING-005 | two-root-linter.md | packaging | `sweep_is_duplicate_free` (C1.7); `duplicate_guard_negative_case` (C3.5a); `walk_dedupes_repeated_roots` (C9.4); `check_structure_dedupes_repeated_roots`, `check_size_dedupes_repeated_roots` (C10.1, C10.2) | `duplicate_free_findings()` + `_guard_duplicate_free()` in `walk()` (C1.4); the `seen_dirs` / `seen_size` guards pinned, not added (C10.1, C10.2) |  |
| REQ-LINT-PACKAGING-006 | two-root-linter.md | packaging | `fixture_counts_exact` (C3.6) | per-fixture literal counts (C3.6) |  |
| REQ-LINT-PACKAGING-007 | two-root-linter.md | packaging | `print_population_shape` (C4.3) | `--print-population`, `population_tables()` (C4.1) |  |
| REQ-LINT-PACKAGING-008 | skill-namespace-rename.md | packaging | `skill-lint.py --self-test` retired-prefix scope drift | `tools/skill-lint.py`:381,:1252; `skill-namespace-rename.md`:76 (C0.2) |  |
| REQ-PC-MARKETPLACE-001 | pre-commit.md | packaging | parsed-hook-id set == derived union, 8 == 8; `pre-commit validate-config` exit 0 (C10.7) | `.pre-commit-config.yaml` two `--self-test` local hooks (C9.4); closed set amended to eight in requirement + `pre-commit.md` §Hook-Set Amendment (C10.7) |  |
| REQ-PC-MARKETPLACE-004 | pre-commit.md | packaging | three-script-filename grep re-run, 0/0/0 (C9.4, re-run C10.7) | acceptance's grep strings pinned to the three script filenames; `CONTRIBUTING.md` reversal recorded in place (C9.4, C10.7) |  |
| REQ-PC-PACKAGING-001 | pre-commit.md | packaging | revert-either-prefix failure; swept-set membership >=1 `docs/spec/` path (C5.7, C5.8) | both `.pre-commit-config.yaml` hook entries prefixed (C5.4) |  |
| REQ-PKG-PACKAGING-001 | two-root-linter.md | packaging | C5.5 per-name membership vs pre-move sha 95c28b7; `git log --follow` 45/45 (C5.2, C5.5) | the move commit e26f81f — 45 renames, 0 add, 0 delete (C5.2) |  |
| REQ-PKG-PACKAGING-002 | two-root-linter.md | packaging | `two_roots_construct_distinct_and_equal`; `--help` grep (C1.7); `zero_arg_run_sweeps_the_corpus` — the acceptance's own case, corpus half (C9.2) and suite-default half (C10.6); `rel_raises_outside_the_swept_roots` (C10.4); `equal_roots_count_as_contained` (C10.5) | `skill-lint.py` `__init__`/`main()` cwd default; `default_suite_root()`; `rel()` / `skill_dir_of()` fallbacks; `skill-lint-v5.md` REPO_ROOT sentences (C1.1, C1.6) |  |
| REQ-PKG-PACKAGING-003 | two-root-linter.md | packaging | negative-surface grep: no `--no-suite-rules`/`--suite-root` (C1.5) | `skill-lint.py` argparse unchanged (C1.5) |  |
| REQ-PKG-PACKAGING-004 | two-root-linter.md | packaging | `retarget_seeds_an_ungated_finding`; equal-roots vs baseline (C2.5, C2.6) | `check_required()` retarget to suite root (C2.3) |  |
| REQ-PKG-PACKAGING-005 | skill-lint-v5.md | packaging | F11 scan: 18 blocks examined, 0 failing (C6.6); `check_size_binds_to_the_swept_roots` (C8.2); `check_structure_binds_to_the_swept_roots` (C9.1); `backtick_bases_bind_to_the_swept_roots` (C9.3); `swept_base_order_and_fallback` (C10.3) | re-scoped in `skill-lint-v5.md` + 3 linter-source sites (C6.3); `swept_roots()` union binding for `check_structure()`, `check_size()`, `skill_dir_of()` and `swept_base()` (C8.1, C9.1, C9.3) |  |
| REQ-PKG-PACKAGING-006 | two-root-linter.md | packaging | `nested_roots_render_per_root`, `fixture_counts_exact` (C3.1, C3.6) | fixture A, nested (C3.1) |  |
| REQ-PKG-PACKAGING-007 | two-root-linter.md | packaging | `disjoint_suite_walk_excluded` (C3.2) | fixture B, disjoint (C3.2) |  |
| REQ-PKG-PACKAGING-008 | two-root-linter.md | packaging | `case_c_counts_once`, `case_c_negative_double_count` (C3.4, C3.5a) | `forbidden_findings()` pure counting fn (C3.4) |  |
| REQ-PKG-PACKAGING-009 | two-root-linter.md | packaging | scratch-consumer run: resolved root = scratch repo, 0 swept paths under suite (C6.8) | `verify/SKILL.md:169` `<plugin-dir>` + `--root .` (C6.1) |  |
| REQ-PKG-PACKAGING-010 | marketplace-packaging.md | packaging | sibling-first: precedence / fallback / neither, each with its failing construction (C5.6) | frozen behaviour at `gc.py` `lint_path()` (C5.6) |  |
