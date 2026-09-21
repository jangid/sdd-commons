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
Cell Values — `pass | fail | pending-red | descoped`. All rows below were added
at the requirements stage on 2026-09-21 and are not yet specced or implemented,
and the `Spec` column was filled by `sdd:specs` on 2026-09-21; `Test`,
`Implementation` and `Verified` are intentionally blank.

**Requirement → plan task.** The matrix shape is fixed at the six columns of
`docs/spec/ws-traceability.md` §The Per-Workstream File, so the plan stage adds
no `Task` column — a seventh cell makes every row unparseable and the drift
sweep drops it from the regenerated aggregate (`[traceability-rowdrop]`). The
per-requirement task mapping `sdd:plan` produced on 2026-09-21 therefore lives
in `docs/ws/packaging/plan.md` §Requirement → Task Coverage, which carries one
row per requirement in this table, keyed by the same ids.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-DOCS-PACKAGING-001 | project-docs.md | packaging | | | |
| REQ-DOCS-PACKAGING-002 | project-docs.md | packaging | marker string-equality vs `docs/.sdd-version` (C0.4) | `CLAUDE.md` §Multi-Workstream Layout (C0.3) |  |
| REQ-DOCS-PACKAGING-003 | project-docs.md | packaging | | | |
| REQ-LINT-PACKAGING-001 | two-root-linter.md | packaging | `retired_scope_binds_per_entry` (C2.4) | `RETIRED_SCOPE_BINDING`, `retired_scope_entries()`, `check_retired_prefix()` (C2.1) |  |
| REQ-LINT-PACKAGING-002 | two-root-linter.md | packaging | `template_pairs_bind_per_side`, 3 geometries + negative control (C3.9) | `check_template_drift()` per-side; spec-side-only disjoint skip (C2.2, C3.9) |  |
| REQ-LINT-PACKAGING-003 | two-root-linter.md | packaging | `manifest_pair_membership` (C3.3) | union binding for `.claude-plugin` (C2.1) |  |
| REQ-LINT-PACKAGING-004 | two-root-linter.md | packaging | | | |
| REQ-LINT-PACKAGING-005 | two-root-linter.md | packaging | `sweep_is_duplicate_free` (C1.7) | `duplicate_free_findings()` + `_guard_duplicate_free()` in `walk()` (C1.4) |  |
| REQ-LINT-PACKAGING-006 | two-root-linter.md | packaging | `fixture_counts_exact` (C3.6) | per-fixture literal counts (C3.6) |  |
| REQ-LINT-PACKAGING-007 | two-root-linter.md | packaging | | | |
| REQ-LINT-PACKAGING-008 | skill-namespace-rename.md | packaging | `skill-lint.py --self-test` retired-prefix scope drift | `tools/skill-lint.py`:381,:1252; `skill-namespace-rename.md`:76 (C0.2) |  |
| REQ-PC-PACKAGING-001 | pre-commit.md | packaging | | | |
| REQ-PKG-PACKAGING-001 | two-root-linter.md | packaging | | | |
| REQ-PKG-PACKAGING-002 | two-root-linter.md | packaging | `two_roots_construct_distinct_and_equal`; `--help` grep (C1.7) | `skill-lint.py` `__init__`/`main()` cwd default; `skill-lint-v5.md` REPO_ROOT sentences (C1.1, C1.6) |  |
| REQ-PKG-PACKAGING-003 | two-root-linter.md | packaging | negative-surface grep: no `--no-suite-rules`/`--suite-root` (C1.5) | `skill-lint.py` argparse unchanged (C1.5) |  |
| REQ-PKG-PACKAGING-004 | two-root-linter.md | packaging | `retarget_seeds_an_ungated_finding`; equal-roots vs baseline (C2.5, C2.6) | `check_required()` retarget to suite root (C2.3) |  |
| REQ-PKG-PACKAGING-005 | skill-lint-v5.md | packaging | | | |
| REQ-PKG-PACKAGING-006 | two-root-linter.md | packaging | `nested_roots_render_per_root`, `fixture_counts_exact` (C3.1, C3.6) | fixture A, nested (C3.1) |  |
| REQ-PKG-PACKAGING-007 | two-root-linter.md | packaging | `disjoint_suite_walk_excluded` (C3.2) | fixture B, disjoint (C3.2) |  |
| REQ-PKG-PACKAGING-008 | two-root-linter.md | packaging | `case_c_counts_once`, `case_c_negative_double_count` (C3.4, C3.5a) | `forbidden_findings()` pure counting fn (C3.4) |  |
| REQ-PKG-PACKAGING-009 | two-root-linter.md | packaging | | | |
| REQ-PKG-PACKAGING-010 | marketplace-packaging.md | packaging | | | |
