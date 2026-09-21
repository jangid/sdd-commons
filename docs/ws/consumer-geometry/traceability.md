---
workstream: consumer-geometry
last_updated: 2026-09-21
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
| REQ-PKG-CONSUMERGEOMETRY-001 | `two-root-linter.md` §CG-7 + criteria; `marketplace-packaging.md` §CG "The three checklist items…" (freeze repin); `drift-sweep.md` §2, §4; `pre-commit.md` §CG | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-002 | `two-root-linter.md` §CG-4 (citation correction), §CG-5, §CG-5a | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-003 | `two-root-linter.md` §CG-2, §CG-9 (the `:89` and `:522-523` rows); `drift-sweep.md` §1, §2; `skill-lint-v5.md` §CG criteria | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-004 | `two-root-linter.md` §CG-6; `drift-sweep.md` §3; `skill-lint-v5.md` §CG "The summary-line pins", "The GEOMETRY: token is not a finding" | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-005 | `marketplace-packaging.md` §CG "The removal", "The three disposition classes", "The shape every string criterion…", "The three checklist items…", "Consumer-unreachable strings…"; `two-root-linter.md` §CG-9 (the `:366` row); `drift-sweep.md` §4; `pre-commit.md` §CG | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-006 | `two-root-linter.md` §CG-1, §CG-3, §CG-4, §CG-8, §CG-10; `pre-commit.md` §CG | consumer-geometry | | | |
