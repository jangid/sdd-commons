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
> **test convention declared in `CLAUDE.md`** **satisfies this check for the
> modules it names**, and the named module set is derived to the character
> (round 8 M4): a module is *named* by a convention only when it is the
> **script path in a command the convention quotes** — the command word of a
> fenced or inline-code command in `CLAUDE.md` (a `--self-test` invocation,
> for instance), or the `entry:` value of a hook in the `.pre-commit-config.yaml`
> that `CLAUDE.md` names as the commit gate — with any leading interpreter word
> (`python3`) dropped; a module named only in prose (`CLAUDE.md`'s "the three
> contributor-tool self-tests (scope-check, telemetry, evaluation)") is **not**
> named by that mention. "A test file that imports from the implementation
> module" remains the default for every module the derived set omits.
> Observed: the identical coverage advisory fired on 9 of 9 consumer-geometry
> chunks against modules whose self-tests the repository's `CLAUDE.md` names
> and whose commit gate runs. Both executors of the check — `implement/SKILL.md`
> Check 3 and `agents/chunk-verifier.md` — state the convention clause, pinned
> by a skill-lint `REQUIRED` row in each file. **Acceptance, added** (the
> earlier `grep -c convention … ≥ 1` criterion is withdrawn: it decided no
> module set, and `plugins/sdd/skills/implement/SKILL.md` already satisfies it
> by an unrelated sentence — reads 1 today): the module set is decided by one
> command over the two declaring files — on this tree
> `{ grep -ohE '(^|\`|python3 )plugins/sdd/tools/[a-z-]+\.py' CLAUDE.md; grep -ohE '^\s*entry: (python3 )?[^ ]+\.py' .pre-commit-config.yaml; } | grep -oE '[^ \`]+\.py' | sort -u`
> reads exactly `plugins/sdd/tools/gc.py`, `plugins/sdd/tools/skill-lint.py`,
> `plugins/sdd/tools/telemetry.py` (today; a reference value, never a pin),
> and `plugins/sdd/tools/scope-check-selftest.py` and
> `plugins/sdd/tools/eval.py` are absent from it although `CLAUDE.md` names
> them in prose; both executors state the derivation —
> `grep -c 'script path in a command'` over
> `plugins/sdd/agents/chunk-verifier.md` and over
> `plugins/sdd/skills/implement/SKILL.md` each read ≥ 1 (today 0, 0), pinned
> by the two skill-lint `REQUIRED` rows; one chunk-verifier fixture: a chunk
> whose spec's implementation module is `plugins/sdd/tools/gc.py` (in the
> derived set) and which has no importing test file reports **no** Check 3
> advisory, while the same chunk with the module
> `plugins/sdd/tools/scope-check-selftest.py` (prose-only, outside the set)
> still reports it; `python3 plugins/sdd/tools/skill-lint.py` exits 0 with the
> two rows and exits non-zero in a temp copy with either sentence removed. Leaves REQ-CHKC-006
> (gaps stay advisory), REQ-CHKC-007 (report shape) and REQ-HARN-014 (the
> verifier re-runs Check 3 by reference to this requirement) consistent.
> **Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
> 2026-09-22)** over the declared-convention clause — a listing grep over
> `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in
> this requirement's own text and in the index rows citing it are the statement
> itself and are excluded.
> Command: `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/functional/chunk-close.md -exec grep -nHE 'imports from the implementation|declared convention|test convention' {} +`.
> `plugins/sdd/skills/implement/SKILL.md` Check 3 and
> `plugins/sdd/agents/chunk-verifier.md` — no hit (today 0; the acceptance
> above adds the clause, pinned by rows p11/p12);
> `docs/spec/chunk-close-review.md` §A declared test convention satisfies Check
> 3 and `docs/spec/skill-lint-v5.md` rows p11–p12 (pattern `self-test
> convention`) — reconciled, they carry this clause, and the pinned phrase
> satisfies the `grep -c convention` check above;
> `docs/spec/pipeline-observability.md` — reconciled, lists.
> Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
> files the `-l` listing names: `plugins/sdd/skills/implement/SKILL.md` Check
> 3 — now a hit: the declared-convention clause the acceptance above adds,
> landed by the implement stage, so the "no hit" baseline above is history;
> `plugins/sdd/agents/chunk-verifier.md` — still no hit under this pattern
> today.

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
