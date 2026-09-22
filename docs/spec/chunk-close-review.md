---
status: Approved
last_updated: 2026-09-22
requires:
  - REQ-CHKC-001
  - REQ-CHKC-002
  - REQ-CHKC-003
  - REQ-CHKC-004
  - REQ-CHKC-005
  - REQ-CHKC-006
  - REQ-CHKC-007
  - REQ-CHKC-008
---

# Chunk-Close Review

## Context

`sdd-implement`'s TDD inner loop catches what tests test for, but misses
spec-implementation drift, forgotten traceability updates, and undocumented
deviations. In the rubric M1 cycle, 5 of 7 chunks needed rework after
external review caught issues the implementation session missed: model-name
drift, silent stubbing, wrong matching fields, missing logic, dead code.

This spec defines a structured review checklist that runs at each chunk
boundary, catching the most common failure modes before they ripple into
downstream chunks.

## Design

### Chunk Definition

A chunk is a contiguous group of tasks in the plan file marked by an
explicit `### Chunk N: <name>` header. Chunks are implementation work units
(~5-15 hours each), distinct from delivery milestones (M1, M2, etc. — see
milestone-plans.md).

```markdown
### Chunk 3: Reconciliation

**Goal**: Drift detection, gap reporting, bootstrap flow.

**Tasks**:
1. [implement] SPEC-RECON: reconciliation engine — traces to recon.md
2. [implement] Bootstrap interactive flow — traces to recon.md

**Entry criteria**: Chunk 2 complete.
**Exit criteria**: All 3 drift types detected in unit tests.
```

`sdd-plan` produces chunk headers; `sdd-implement` detects them via the
`### Chunk N:` pattern. The chunk number N is a sequential integer within
the plan file, starting at 0 or 1. Chunk names are descriptive prose.

**Why explicit headers rather than inferred grouping**: Implicit chunk
boundaries (e.g., every 3 tasks) are fragile — they change when tasks are
added or removed. Explicit headers make chunk boundaries a planning
decision, not an accident of ordering.

### Checklist

After completing all tasks in a chunk, `sdd-implement` executes these four
checks in order before reporting the chunk complete. Each check produces
findings classified as blocking or advisory per the tiered enforcement
rules.

#### Check 1: Spec-Implementation Type Alignment

**Input**: Spec files referenced by the chunk's tasks (identified via each
task's prose `traces to` reference).

**Process**:
1. For each referenced spec, extract data type definitions from markdown
   code blocks (fenced with `` ``` ``). Specifically:
   - **(a) Class names**: any `class Foo` or `class Foo(Base)` declaration
   - **(b) Field names**: lines matching `field_name: Type` within class
     bodies
   - **(c) Enum values**: lines matching `VALUE = "literal"` or bare
     `VALUE` entries within enum class bodies
2. Grep the implementation source tree for matching class definitions
3. Compare:
   - Class exists in spec but not impl → finding
   - Class exists in impl but not spec → finding (may be legitimate helper;
     document as Q-IMPL if so)
   - Field name mismatch (present in spec, absent or renamed in impl) →
     finding
   - Enum value mismatch (values differ between spec and impl) → finding

**Severity**: Blocking. All findings must be resolved before the chunk
closes (fix the implementation, update the spec, or document as Q-IMPL).

**What this check doesn't catch**: Semantic drift (field exists but has
wrong meaning), logic drift (algorithm differs but types match), silent
stubbing (function exists but returns dummy data). These require test
execution and reading-comprehension review, which are outside the scope of
an automated grep-level check.

#### Check 2: Traceability Matrix Update

**Input**: `docs/requirements/traceability.md`, the chunk's task list.

**Process**:
1. Identify requirements covered by this chunk: read each task's prose spec
   references → read those spec files' `requires:` frontmatter → collect
   requirement IDs
2. For each requirement ID, check the traceability matrix:
   - **Test** column empty → finding (tests should have been written during
     TDD)
   - **Implementation** column empty → finding (code should exist if the
     task is done)
3. If any column is empty, fill it before proceeding

**Severity**: Blocking. Missing traceability entries must be filled before
the chunk closes. The fill is mechanical — the implementer knows which test
file and source file correspond to each requirement.

#### Check 3: Test Coverage Per Spec

**Input**: Spec files referenced by the chunk's tasks.

**Process**:
1. For each referenced spec, identify the expected implementation module
   (from the spec's design section or by convention: `spec/recon.md` →
   `src/.../recon/`)
2. Search the test directory for test files that import from that module
3. If no test file imports from the module → finding

**Severity**: Advisory. The operator may override with rationale (e.g.,
"tested via integration test in `test_e2e.py`" or "verification task in
next chunk covers this").

**A declared test convention satisfies Check 3 for the modules it names** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-CHKC-004 as amended; Q-REQ-PO-G; the record of why is §Pipeline-Observability Amendment).

A **test convention declared in `CLAUDE.md`** **satisfies this check for the
modules it names**, and the named module set is derived to the character
(round 8 M4 of the requirements review): a module is *named* by a convention
only when it is the **script path in a command the convention quotes** — the
command word of a fenced or inline-code command in `CLAUDE.md` (a `--self-test`
invocation, for instance), or the `entry:` value of a hook in the
`.pre-commit-config.yaml` that `CLAUDE.md` names as the commit gate — with any
leading interpreter word (`python3`) dropped; a module named only in prose is
**not** named by that mention. "A test file that imports from the
implementation module" remains the default for every module the derived set
omits. Check 3's process therefore reads, for each expected implementation
module: (1) if the module is in the derived set, it is covered → no finding;
(2) otherwise search the test directory for a test file importing from the
module; none → advisory finding. The derived set is decided by one command over
the two declaring files:

```
{ grep -ohE '(^|`|python3 )plugins/sdd/tools/[a-z-]+\.py' CLAUDE.md;
  grep -ohE '^\s*entry: (python3 )?[^ ]+\.py' .pre-commit-config.yaml; } \
  | grep -oE '[^ `]+\.py' | sort -u
```

— on this tree exactly `plugins/sdd/tools/gc.py`, `plugins/sdd/tools/skill-lint.py`,
`plugins/sdd/tools/telemetry.py` (a reference value, never a pin), with
`plugins/sdd/tools/scope-check-selftest.py` and `plugins/sdd/tools/eval.py`
absent from it although `CLAUDE.md` names them in prose. Both executors state
the derivation — `skills/implement/SKILL.md` Check 3 and
`agents/chunk-verifier.md` (which re-runs Check 3 by reference to this spec,
`harness-chunk-verifier.md` §Positioning, REQ-HARN-014) — each pinned by a
skill-lint `REQUIRED` row on the phrase `script path in a command` (rows p11
and p12 of `skill-lint-v5.md` §`REQUIRED` Rows — Pipeline-Observability). The
earlier `grep -c convention … ≥ 1` criterion is **withdrawn**: it decided no
module set, and `skills/implement/SKILL.md` already satisfied it by an
unrelated sentence. Why in place rather than a new requirement: the check's
intent (every module has a test that runs at the gate) is unchanged; only the
evidence it accepts widens.

#### Check 4: Q-IMPL Audit

**Input**: Implementation code written during this chunk, spec files
referenced by the chunk's tasks.

**Process**:
1. Review implementation decisions made during the chunk
2. For each decision that deviates from spec (different parameter,
   additional field, renamed type, different algorithm step):
   - Check if a Q-IMPL entry exists in the relevant spec's
     `## Implementation Questions` section
   - If no entry exists → finding
3. Undocumented deviations should be added as Q-IMPL entries per the
   deviation protocol (see deviation-protocol.md)

**Severity**: Advisory. The operator may override if the deviation is
trivially obvious (e.g., fixing a typo in a spec identifier). The
override rationale is recorded in the chunk close report.

### Tiered Enforcement

| Check | Severity | On failure |
|-------|----------|------------|
| Type alignment (Check 1) | Blocking | Must fix before closing chunk |
| Traceability update (Check 2) | Blocking | Must fill before closing chunk |
| Test coverage (Check 3) | Advisory | May override with written rationale |
| Q-IMPL audit (Check 4) | Advisory | May override with written rationale |

**Why this split**: Type-name mismatches and missing traceability are
mechanical errors with clear fixes — there's no good reason to carry them
forward. Test coverage gaps and undocumented Q-IMPL entries may have
legitimate reasons (deferred to next chunk, covered by integration tests,
trivially obvious) that warrant operator judgment.

### Chunk Close Report

After running all four checks, `sdd-implement` presents a structured
findings report to the operator:

```markdown
## Chunk N Close Report

### Check 1: Type Alignment
- Status: pass | block
- Findings:
  - [spec.md] Class `Foo` field `bar_id` not found in impl (BLOCK)
  - ...

### Check 2: Traceability
- Status: pass | block
- Findings:
  - REQ-RECON-003: Test column empty (BLOCK)
  - ...

### Check 3: Test Coverage
- Status: pass | advisory
- Findings:
  - recon.md: no test imports from recon/engine.py (ADVISORY)
  - Override rationale: "covered by test_e2e.py integration test"

### Check 4: Q-IMPL Audit
- Status: pass | advisory
- Findings:
  - phase1.md: classify_regime takes config param not in spec (ADVISORY)
  - Override rationale: "added as Q-IMPL-003"

### Summary
- Blocking: 0 remaining (all fixed)
- Advisory: 1 overridden with rationale
- Chunk N: CLOSED
```

The report is presented inline (not persisted as a separate file). Its
purpose is operator confirmation, not archival. The traceability matrix
and Q-IMPL entries themselves are the durable artifacts.

**Why not persist the report**: Chunk close reports are session-specific
confirmation. The findings they check become traceability entries, Q-IMPL
entries, or code fixes — all of which are durable artifacts. Persisting the
report adds files nobody reads after the first session (validated by rubric
M1 rework prompt experience — see RS-002).

### Integration with implement

The chunk close checklist integrates into `sdd-implement`'s existing
process at the boundary between chunks:

1. Complete all tasks in chunk N
2. Run existing per-task verification (build + lint + type-check + tests)
3. **NEW**: Run chunk close checklist (checks 1-4)
4. Present chunk close report to operator
5. Resolve all blocking findings
6. Record advisory overrides with rationale
7. Report chunk N as closed
8. Proceed to chunk N+1

The existing "Step 4: Milestone Checkpoints" in `sdd-implement` remains
for delivery milestones (M1, M2, etc.) — those are broader checkpoints
where the operator approves proceeding to the next milestone. Chunk close
is more granular and runs more frequently.

## Verification

### Automated
- Verify `sdd-implement` SKILL.md contains chunk close checklist steps
- Verify the checklist references all four checks by name
- Verify tiered enforcement rules are documented (blocking vs advisory)
- Verify chunk identification pattern (`### Chunk N:`) is documented

### Manual
- Run `sdd-implement` against a plan with explicit chunk headers
- Complete a chunk; verify checklist runs before chunk close
- Introduce a deliberate type-name mismatch; verify it blocks
- Introduce a missing traceability entry; verify it blocks
- Introduce a test coverage gap; verify advisory with override option

### Acceptance Criteria
- [ ] Chunk close checkpoint runs after all tasks in a chunk (REQ-CHKC-001)
- [ ] Type alignment check extracts class names and field names from spec code blocks (REQ-CHKC-002 a, b)
- [ ] Type alignment check extracts enum value lists from spec code blocks (REQ-CHKC-002 c)
- [ ] Traceability check verifies Test and Implementation columns (REQ-CHKC-003)
- [ ] Test coverage check verifies at least one test file per spec (REQ-CHKC-004)
- [ ] Q-IMPL audit flags undocumented deviations (REQ-CHKC-005)
- [ ] Type alignment and traceability are blocking; test coverage and Q-IMPL are advisory (REQ-CHKC-006)
- [ ] Chunk close report lists each check with status and findings (REQ-CHKC-007)
- [ ] Chunks are identified by `### Chunk N: <name>` headers in the plan (REQ-CHKC-008)

**Pipeline-observability (2026-09-22, chunk close)**

- [ ] `grep -c 'script path in a command' plugins/sdd/agents/chunk-verifier.md`
  and the same over `plugins/sdd/skills/implement/SKILL.md` each read ≥ 1 (0
  before this delta), pinned by skill-lint rows p11 and p12;
  `python3 plugins/sdd/tools/skill-lint.py` exits 0 with the two rows and
  exits non-zero in a temp copy with either sentence removed (REQ-CHKC-004 as
  amended).
- [ ] The derivation command of §Checklist › Check 3, run on this tree, lists
  exactly `plugins/sdd/tools/gc.py`, `plugins/sdd/tools/skill-lint.py` and
  `plugins/sdd/tools/telemetry.py`, and neither `scope-check-selftest.py` nor
  `eval.py` (reference values, never pins) (REQ-CHKC-004 as amended).
- [ ] One chunk-verifier fixture: a chunk whose spec's implementation module is
  `plugins/sdd/tools/gc.py` (in the derived set) and which has no importing
  test file reports **no** Check 3 advisory, while the same chunk with the
  module `plugins/sdd/tools/scope-check-selftest.py` (prose-only, outside the
  set) still reports it; the real-chunk consequence is recorded in this
  cycle's `verification.md` from a chunk gate (REQ-CHKC-004 as amended).

## Implementation Questions

### Q-IMPL-001: Step 5 (Handle Spec Gaps) folded into Q-IMPL Protocol
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Integration with implement, step 8 ("Proceed to chunk N+1")
**Decision**: Removed the former Step 5 (Handle Spec Gaps) entirely. Q-IMPL Tier 3 covers spec gaps with more structure (stop, escalate, classify). The "Do NOT" rules (no silent additions, no assumptions, no verification skipping) were folded into implement's Rules section.
**Impact**: Step numbering cascade adjusted — Step 5 is now Milestone Checkpoints, Step 6 is Completion.


## Pipeline-Observability Amendment (2026-09-22, REQ-CHKC-004 amended)

[Added 2026-09-22, workstream `pipeline-observability` —
RS-PIPELINEOBSERVABILITY-001 §Q6 gap 10, R14; Q-REQ-PO-G. Observed defect: the
identical coverage advisory fired on 9 of 9 consumer-geometry chunks against
modules whose self-tests the repository's `CLAUDE.md` names and whose commit
gate runs.]

**Where the contract lives** (REQ-REQ-PIPELINEOBSERVABILITY-001 (b), 2026-09-22): this section is the record of *why* and states no contract of its own; the contract is in the sections of record named here, each edited in place under a `[Updated: 2026-09-22]` marker, and its acceptance criteria sit in this spec's own Acceptance Criteria section under the same date. §Checklist › Check 3: Test Coverage Per Spec carries the declared-convention clause and the derivation of the named module set (REQ-CHKC-004 as amended); `harness-chunk-verifier.md` §Positioning inherits it by reference and is not re-dated. Left consistent and not reopened: Checks 1, 2 and 4; §Tiered Enforcement (Check 3 stays advisory); §Chunk Close Report (a convention-covered module reports `pass`).

**Why the set is derived from commands and not prose** (round 8 M4): a prose mention decides no module set — `CLAUDE.md` names three contributor-tool self-tests in a sentence while its commit gate runs a different three — and the `grep -c convention` criterion it replaced was already satisfied by an unrelated sentence.
