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

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-PKG-CONSUMERGEOMETRY-001 | | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-002 | | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-003 | | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-004 | | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-005 | | consumer-geometry | | | |
| REQ-PKG-CONSUMERGEOMETRY-006 | | consumer-geometry | | | |
