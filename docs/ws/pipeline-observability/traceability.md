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
| REQ-AGENT-MARKETPLACE-002 (amended) | harness-agents.md §The frontmatter contract | pipeline-observability | | | |
| REQ-AGENT-PIPELINEOBSERVABILITY-001 | harness-agents.md §The frontmatter contract | pipeline-observability | | | |
| REQ-ARB-HARNESSP2-002 (amended) | arbitrated-handoff.md §Contradiction Classes | pipeline-observability | | | |
| REQ-ARB-HARNESSP3-001 (amended) | arbitrated-handoff.md §`W_N` Includes Regeneration Writes | pipeline-observability | | | |
| REQ-ARB-PIPELINEOBSERVABILITY-001 | arbitrated-handoff.md §Contradiction Classes | pipeline-observability | | | |
| REQ-CHKC-004 (amended) | chunk-close-review.md §Checklist | pipeline-observability | | | |
| REQ-DOCS-PIPELINEOBSERVABILITY-001 | project-docs.md §`CLAUDE.md` | pipeline-observability | | | |
| REQ-GC-HARNESSP2-002 (amended) | drift-sweep.md §Sweep Table | pipeline-observability | | | |
| REQ-GC-HARNESSP2-003 (amended) | drift-sweep.md §Q-IMPL Counting Rule | pipeline-observability | | | |
| REQ-GC-HARNESSP6-003 (amended) | drift-sweep.md §Shared-Spec Staleness | pipeline-observability | | | |
| REQ-GC-PIPELINEOBSERVABILITY-001 | drift-sweep.md §Sweep Table | pipeline-observability | | | |
| REQ-GC-PIPELINEOBSERVABILITY-002 | drift-sweep.md §Sweep Table | pipeline-observability | | | |
| REQ-GC-PIPELINEOBSERVABILITY-003 | drift-sweep.md §Q-IMPL Counting Rule | pipeline-observability | | | |
| REQ-GC-PIPELINEOBSERVABILITY-004 | drift-sweep.md §Sweep Table | pipeline-observability | | | |
| REQ-HARN-001 (amended) | harness-loop-control.md §Fix-Loop Cap | pipeline-observability | | | |
| REQ-HARN-013 (amended) | harness-return-contract.md §VERDICT Token | pipeline-observability | | | |
| REQ-HARN-HARNESSP6-001 (amended) | harness-write-scope.md §Git-State Observation | pipeline-observability | | | |
| REQ-HARN-PIPELINEOBSERVABILITY-001 | harness-loop-control.md §Fix-Loop Cap | pipeline-observability | | | |
| REQ-HARN-PIPELINEOBSERVABILITY-002 | harness-loop-control.md §Gate Signal Order | pipeline-observability | | | |
| REQ-HARN-PIPELINEOBSERVABILITY-003 | harness-loop-control.md §Fix-Loop Cap | pipeline-observability | | | |
| REQ-HARN-PIPELINEOBSERVABILITY-004 | harness-write-scope.md §Git-State Observation | pipeline-observability | | | |
| REQ-HARN-PIPELINEOBSERVABILITY-005 | harness-return-contract.md §VERDICT Token | pipeline-observability | | | |
| REQ-HARN-PIPELINEOBSERVABILITY-006 | harness-loop-control.md §Budget Slot | pipeline-observability | | | |
| REQ-LINT-PACKAGING-007 (amended) | two-root-linter.md §6. Counts: asserted, or only printed | pipeline-observability | | | |
| REQ-LINT-PIPELINEOBSERVABILITY-001 | skill-lint-v5.md §`FORBIDDEN` Row — `literal-anchor` | pipeline-observability | | | |
| REQ-PC-PIPELINEOBSERVABILITY-001 | pre-commit.md §Design | pipeline-observability | | | |
| REQ-PKG-PIPELINEOBSERVABILITY-001 | marketplace-packaging.md §The manifest pair | pipeline-observability | | | |
| REQ-REQ-PIPELINEOBSERVABILITY-001 | requirements-artifacts.md §Amendment Landing | pipeline-observability | | | |
| REQ-REV-002 (amended) | review.md §Report Format | pipeline-observability | | | |
| REQ-REV-PIPELINEOBSERVABILITY-001 | review.md §Report Format | pipeline-observability | | | |
| REQ-TELEM-HARNESSP2-004 (amended) | telemetry.md §Writer | pipeline-observability | | | |
| REQ-TELEM-HARNESSP3-001 (amended) | telemetry.md §Positive Gate Line `TELEMETRY: rec <n>` | pipeline-observability | | | |
| REQ-TELEM-HARNESSP4-005 (amended) | telemetry-reader.md §In-Place Migration of the 8 p3 Records | pipeline-observability | | | |
| REQ-TELEM-HARNESSP5-008 (amended) | telemetry-reader.md §Schema Lint | pipeline-observability | | | |
| REQ-TELEM-PIPELINEOBSERVABILITY-001 | telemetry.md §Writer | pipeline-observability | | | |
| REQ-TELEM-PIPELINEOBSERVABILITY-002 | telemetry-reader.md §In-Place Migration of the 8 p3 Records | pipeline-observability | | | |
| REQ-TELEM-PIPELINEOBSERVABILITY-003 | telemetry-reader.md §Schema Lint | pipeline-observability | | | |
