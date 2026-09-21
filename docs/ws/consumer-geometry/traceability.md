---
workstream: consumer-geometry
last_updated: 2026-09-22
---

# Traceability — consumer-geometry

Rows owned by the `consumer-geometry` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd:specs`, `sdd:implement` and `sdd:verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited, and never by a leaf: regeneration is the
orchestrator's post-gate bookkeeping.

`Verified` takes the values of `docs/spec/ws-traceability.md` §Legal `Verified`
Cell Values. Rows were created by the orchestrator at the requirements stage
gate on 2026-09-21; `Spec` is `sdd:specs`' cell, `Test` and `Implementation`
are `sdd:implement`'s, and `Verified` is `sdd:verify`'s — all four are
intentionally blank here.

The amended `REQ-PKG-MARKETPLACE-006` and `-007` are **not** given rows here.
Their rows belong to the `marketplace` workstream, which owns them; this cycle
amends their text in the shared corpus and records the amendments in
`docs/requirements/index.md`'s delta note. Adding duplicate rows would make the
regenerated aggregate carry two assertions per id.

**Requirement → plan task.** The matrix shape is fixed at the six columns of
`docs/spec/ws-traceability.md` §The Per-Workstream File, so the plan stage adds
no `Task` column — a seventh cell makes every row unparseable and the drift
sweep drops it from the regenerated aggregate (`[traceability-rowdrop]`).

Spec cells cite the `## Consumer-Geometry Amendment` section of each file. `two-root-linter.md`'s subsections are numbered `§CG-1`…`§CG-11` (plus `§CG-5a`);
`drift-sweep.md`'s are numbered `§1`…`§4` — `§1` the `--suite-root` surface, `§2`
`lint_command()`'s pass-through, `§3` `sweep_lint()`'s `GEOMETRY:` forwarding,
`§4` `AGG_FIX` — exactly as its `### 1.`…`### 4.` headings spell them. In
`marketplace-packaging.md`, `skill-lint-v5.md` and `pre-commit.md` the
subsections are **named**, so those citations quote the name rather than a
number and a renumbering cannot silently misroute them.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-PKG-CONSUMERGEOMETRY-001 | `two-root-linter.md` §CG-7 + criteria; `marketplace-packaging.md` §CG "The three checklist items…" (freeze repin); `drift-sweep.md` §2, §4; `pre-commit.md` §CG | consumer-geometry | `skill-lint.py --self-test` / `gc.py --self-test`: `cg_reconcile()` asserts constant-vs-registered both ways; falsifiability demonstrated by two mutation runs (Chunk 0 task 2 — token-without-case and case-without-token each print their own `cg-row-` line). **Row 4** registered in Chunk 2 in **`gc.py`'s** self-test (not the linter's), covering `lint_path()`'s sibling-first precedence and both `lint_command()` branches; its two plan-named mutations run — revert branch (i) to `[executable, str(lint), str(self.root)]`, and reorder the `lint_path()` candidate tuple — each putting a line beginning `cg-row-4:` in the printed failure list, which is the comparand, never the process exit code. **Row 3** registered in Chunk 1 as case `zero_sweep_summary_is_distinguishable`, its mutation run (drop the `— NOTHING SWEPT` suffix → the printed list carries `cg-row-3:` lines; control → none) | `plugins/sdd/tools/skill-lint.py`: `CG_ROW_TOKENS` (rows 1-3, 5-8), `cg_check()` registration, `cg_reconcile()`; `plugins/sdd/tools/gc.py`: the same surface for row 4 alone. Both constants empty at Chunk 0 close (plan D1, incremental population); `skill-lint.py`'s `CG_ROW_TOKENS` holds `("cg-row-3:",)` at Chunk 1 close; `gc.py`'s holds `("cg-row-4:",)` at Chunk 2 close — complete at one member, never eight | |
| REQ-PKG-CONSUMERGEOMETRY-002 | `two-root-linter.md` §CG-4 (citation correction), §CG-5, §CG-5a | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-003 | `two-root-linter.md` §CG-2, §CG-9 (the `:89` and `:522-523` rows); `drift-sweep.md` §1, §2; `skill-lint-v5.md` §CG criteria | consumer-geometry | `skill-lint.py --help` names `--suite-root` (the deliberate inversion of REQ-PKG-PACKAGING-003's negative-surface grep) and, in a scratch fixture, an explicit suite root under the corpus root yields `suite_contained() == True` with a non-empty `skill_files()` while the same corpus without it falls through to `default_suite_root()`; `gc.py --help` names `--suite-root` and `Gc(...)` accepts and stores the keyword. `gc.py --self-test` case `cg-row-4:` covers both `lint_command()` branches — branch (i) asserted **on the constructed vector**, branch (ii) by running the `-c` shim and reading `suite_contained()` back off the `GEOMETRY:` token. Six mutation runs recorded in the plan's Chunk 2 Notes (branch (i) reverted; the shim's ctor reverted; the linter's flag removed; the argument accepted-and-discarded; `gc.py`'s flag removed; the `Gc` keyword removed) — the branch pair reds in opposite directions. Omission half: with `suite_root is None` both branches are byte-identical to the entry sha `3bac4af`. Leg (i) greps run: `no-suite-rules` still absent, no production `suite_rules=False` construction site | `plugins/sdd/tools/skill-lint.py`: the `--suite-root PATH` argument on `main()`'s parser, resolved to an absolute path and adopted as tier 1 **with no existence test**, passed to `Linter(root, suite_root)` (and to `print_population()`); omitted it stays `None` so the constructor's lower tiers answer. `plugins/sdd/tools/gc.py`: the matching `--suite-root` flag, the `Gc(..., suite_root=None)` constructor parameter, and `lint_command()`'s pass-through on **both** branches — the argv branch appends `--suite-root <path>`, the `-c` shim threads the root through its program string as `sys.argv[3]` with a second ctor spelling, so "pass nothing" stays byte-identical by construction | |
| REQ-PKG-CONSUMERGEOMETRY-004 | `two-root-linter.md` §CG-6; `drift-sweep.md` §3; `skill-lint-v5.md` §CG "The summary-line pins", "The GEOMETRY: token is not a finding" | consumer-geometry | `skill-lint.py --self-test` case `zero_sweep_summary_is_distinguishable` (row 3) — the presence-iff suffix, asserted over a one-file and an empty corpus with the swept-file count normalised away; the three acceptance mutations run on `disjoint_scratch_suite()` copies (drop the suffix, make it unconditional, remove the `GEOMETRY:` emission) with the results in the plan's Chunk 1 Notes. Enum rendering (`disjoint`/`nested`/`equal`), tier-1 `suite-rows-root=`, emission on the failing path and none from `--self-test` recorded there as four separate assertions; tier-2 `suite-rows-root=` owed to Chunk 3 task 4 | `plugins/sdd/tools/skill-lint.py`: `Linter.geometry()` and `Linter.geometry_line()` (the three-member enum, `swept-roots=`, the **effective** `suite-rows-root=`), emitted by `run()` alone on its own line immediately before the summary, and the `— NOTHING SWEPT` suffix on **all three** print sites (`FAIL:`, the warn `OK:` variant and the clean `OK:` variant). `gc.py`'s forwarding is Chunk 5 | |
| REQ-PKG-CONSUMERGEOMETRY-005 | `marketplace-packaging.md` §CG "The removal", "The three disposition classes", "The shape every string criterion…", "The three checklist items…", "Consumer-unreachable strings…"; `two-root-linter.md` §CG-9 (the `:366` row); `drift-sweep.md` §4; `pre-commit.md` §CG | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-006 | `two-root-linter.md` §CG-1, §CG-3, §CG-4, §CG-8, §CG-10; `pre-commit.md` §CG | consumer-geometry | `disjoint_scratch_suite()` is callable from either tool's self-test fixture layer; the §CG-8 construction was run and its four pre-change observations pinned in the plan's Chunk 0 Notes | `plugins/sdd/tools/skill-lint.py` and `plugins/sdd/tools/gc.py`: `disjoint_scratch_suite(dest)` copies this tool's own plugin dir into `$TMPDIR`, disjoint by construction, never the installed cache | |
