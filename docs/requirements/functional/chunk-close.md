---
domain: CHKC
last_updated: 2026-09-22
status: Approved
---

# Requirements: Chunk-Close Review

## Overview

Structured review checklist at chunk boundaries during implementation.
Catches spec-implementation drift, missing traceability updates, and
undocumented deviations before they ripple into downstream chunks.
"Chunk" is the implementation work unit (~5-15 hours); "milestone" is
the delivery-level grouping (M1, M2, etc.) — see REQ-MPLAN-*.
Derived from RS-002 finding P1 (chunk-close review), P4 (drift detection),
and P5 (traceability enforcement). (see RS-002)

## Requirements

### REQ-CHKC-001: Chunk close checkpoint
After completing all tasks in a chunk, `sdd-implement` must execute a
structured review checklist before reporting the chunk as complete. The
checklist runs at chunk boundaries defined in the plan.
[Priority: must]

### REQ-CHKC-002: Spec-implementation type alignment check
The chunk close checklist must extract from spec code blocks referenced by
the chunk's tasks: (a) class names, (b) field names within each class, and
(c) enum value lists for each enum. The implementation must be grepped for
matching definitions. Mismatches in any of the three (missing class,
missing/renamed field, enum value differences) must be reported as findings.
[Priority: must]

### REQ-CHKC-003: Traceability matrix update check
The chunk close checklist must verify that the Test and Implementation
columns in `docs/requirements/traceability.md` are populated for all
requirements covered by the chunk's tasks. Requirements are identified by
reading each task's prose spec references and extracting the corresponding
`requires:` frontmatter from those specs. If any column is empty, the
implementer must fill it before the chunk is marked complete.
[Priority: must]

### REQ-CHKC-004: Test coverage per spec check
The chunk close checklist must verify that each spec referenced by the
chunk's tasks has at least one corresponding test file that imports from
the implementation module. Specs with zero test coverage must be flagged
as findings.
[Priority: must]
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> RS-PIPELINEOBSERVABILITY-001 R14; Q-REQ-PO-G) `[Updated: 2026-09-22]`: a
> **test convention declared in `CLAUDE.md`** — an embedded `--self-test` entry
> point, a pre-commit hook entry that runs it — **satisfies this check for the
> modules it names**; "a test file that imports from the implementation
> module" remains the default for every module no declared convention covers.
> Observed: the identical coverage advisory fired on 9 of 9 consumer-geometry
> chunks against modules whose self-tests the repository's `CLAUDE.md` names
> and whose commit gate runs. Both executors of the check — `implement/SKILL.md`
> Check 3 and `agents/chunk-verifier.md` — state the convention clause, pinned
> by a skill-lint `REQUIRED` row in each file. **Acceptance, added**:
> `grep -c convention plugins/sdd/agents/chunk-verifier.md` and the same over
> `plugins/sdd/skills/implement/SKILL.md` each read ≥ 1 (today 0);
> `python3 plugins/sdd/tools/skill-lint.py` exits 0 with the two rows and exits
> non-zero in a temp copy with either sentence removed. Leaves REQ-CHKC-006
> (gaps stay advisory), REQ-CHKC-007 (report shape) and REQ-HARN-014 (the
> verifier re-runs Check 3 by reference to this requirement) consistent.

### REQ-CHKC-005: Q-IMPL audit
The chunk close checklist must identify any implementation decisions that
deviated from spec but are not documented as Q-IMPL entries (see
REQ-QIMPL-001). Undocumented deviations must be flagged as findings.
[Priority: must]

### REQ-CHKC-006: Tiered enforcement
Checklist findings must be classified by severity:
- **Blocking**: Type-name mismatches (REQ-CHKC-002) and missing
  traceability entries (REQ-CHKC-003) hard-block the chunk close.
  The implementer must fix them before proceeding.
- **Advisory**: Q-IMPL audit findings (REQ-CHKC-005) and test coverage
  gaps (REQ-CHKC-004) are advisory. The operator may override each with
  a written rationale that gets documented in the chunk close report.
[Priority: must]

### REQ-CHKC-007: Chunk close report
The chunk close checklist must produce a structured findings report listing
each check, its status (pass/block/advisory), and any remediation needed or
override rationale provided. The report is presented to the operator before
the chunk is closed.
[Priority: must]

### REQ-CHKC-008: Chunk identification
A chunk is a contiguous group of tasks in `docs/plan.md` (or
`docs/plan-{milestone-id}.md` per REQ-MPLAN-001) marked by an explicit
`### Chunk N: <name>` header. Chunk boundaries are the trigger for
REQ-CHKC-001 through REQ-CHKC-007.
[Priority: must]
