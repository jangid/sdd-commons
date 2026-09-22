---
name: implement
description: >
  Executes implementation from an approved plan and design specs. Works through
  tasks in order, uses TDD inner loop, detects stuck states, and executes spike
  tasks. Triggers replan when assumptions break. Use after the implementation
  plan is approved. Do not use without an approved plan — run plan first.
---

# SDD: Implementation

You are implementing from an approved plan and design specs. Follow the plan, use TDD, detect when you're stuck, and trigger replanning when needed.

## Phase Detection

Before starting, check project state. **Compare `last_updated` dates** to detect stale upstream artifacts:

**Workstream & version gate (v4).** This skill accepts an optional `workstream`
argument that defaults to `default`. Read `docs/.sdd-version` first — it is the
**sole** layout gate:

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Ignore the workstream
  argument and run exactly the numbered detection below against flat
  `docs/plan.md` / `docs/verification.md`; never read or write `docs/ws/`. The v3
  path is unaffected.
- **Marker is `4` (workstream-aware layout).** Resolve `ws` = the workstream
  argument (default `default`), set `base = docs/ws/<ws>/`, and run the same
  detection below but root every **execution artifact** (`plan.md`,
  `verification.md`, `kickoff.md`, `plan-history/`) at `base` — never at flat
  `docs/`. The **shared corpus** stays at its top-level paths and is used as-is:
  `docs/research/`, `docs/requirements/` (index, category files, aggregated
  `traceability.md`), `docs/spec/`.

Ownership, sharing, solo-`default`, and approval semantics under marker `4`
follow the common v4 contract — see `docs/spec/ws-layout.md`. In short: a
workstream owns only its `docs/ws/<ws>/` execution artifacts and per-ws
`traceability.md`; requirements/specs/research and the aggregated traceability
are shared (ADD, never fork); omitting the argument resolves `default`.

**Cycle identity (REQ-CYCID-HARNESSP3-001, -002).** Before reading a
**completion signal** as "this cycle is done" — `verification.md` `status: pass`,
or `plan.md` `status: complete` with every task `[x]` — compare that artifact's
frontmatter `research_id:` against the kickoff's by **exact string equality**.
Mismatch, or absence while the kickoff has one, reads as a previous cycle's
artifact; with no usable discriminator the comparison is skipped and the
`status:`-only rule applies unchanged. The three exhaustive cases:
[`references/workstream-layout.md`](references/workstream-layout.md) §1.
0. **Version check**: If `docs/.sdd-version` is missing, suggest running `migrate` before proceeding
1. If no `docs/requirements/index.md` or status is `Draft` → use `requirements`
2. If `docs/spec/*.md` are missing or have `status: Draft` → use `specs`
3. If no `docs/plan.md` → use `plan`
4. **Staleness check**: compare `last_updated` dates to detect upstream changes:
   - **Single-milestone plan**: compare `docs/requirements/index.md`'s `last_updated` against specs, and specs against `docs/plan.md`'s `last_updated`. If anything upstream is newer → use `plan`
   - **Multi-milestone plan** (index + per-milestone files): apply milestone-scoped staleness — compare the active milestone plan's `last_updated` only against specs and requirement category files traced by that milestone's tasks (task → spec → `requires:` → requirement IDs → category file dates). Unrelated requirement changes don't trigger staleness. The index-level `docs/plan.md` is not subject to this check
   - **Workstream-scoped (marker `4` only)**: `docs/.sdd-version` is the sole gate. Under marker `3` (or earlier) compute staleness exactly as the single-/multi-milestone bullets above — flat `docs/plan.md`, milestone key — **unchanged**. Under marker `4` the milestone-scoped traversal **generalizes verbatim** by swapping two inputs and keeping the chain identical: plan path `docs/plan.md` → `docs/ws/<ws>/plan.md`, and the **milestone key → workstream key**. Compute the scoped set **live** from the workstream's plan — walk its tasks' `traces to` specs, collect each spec's `requires:` requirement IDs, and compare the plan's `last_updated` against those specs' `last_updated` and the requirement category files those IDs belong to (task → spec `requires:` → requirement IDs → category-file dates). The v3 caveat generalizes rather than drops: when the workstream uses per-milestone files, the index-level `docs/ws/<ws>/plan.md` is not subject to this check. (Workstream *selection* happens via the `orchestrate` picker — `docs/spec/ws-orchestration.md` — never via a repo-global plan index.) This reads **no traceability file** and adds **no** traceability schema column — the scope is derived live (REQ-WS-026). A shared spec/requirement no task in `<ws>`'s plan traces does not trigger staleness. See `docs/spec/ws-staleness.md`
5. If `docs/verification.md` exists with failures → use `replan`
6. If `docs/plan.md` exists with incomplete tasks **and is not stale** (per check 4) → you're in the right place, resume

Tell the user which phase you detected. If resuming, identify the next incomplete task and confirm before proceeding.

## Your Role

- Implement tasks from the plan in order
- Use TDD: write test → see it fail → implement → see it pass → refactor
- Execute spike tasks as time-boxed research
- Detect when you're stuck and trigger replanning
- Verify each task against the spec's acceptance criteria
- Keep the user informed of progress at milestone boundaries

## Process

### Step 1: Load Context

0. **Read `CLAUDE.md` first (if present).** Project conventions in `CLAUDE.md` take precedence over generic patterns when choosing libraries, coding patterns, or project structure. The file may not exist — that's normal — but when it does, its conventions override defaults you might otherwise apply.
1. Read `docs/plan.md` — identify the current chunk and next task
2. If the plan's frontmatter `status:` is `planned`, set it to `active` now (applies to single-milestone plans and the active milestone plan alike)
2a. **`## Post-cycle Fixes` is not a task list (REQ-REDB-HARNESSP3-004).** If the
   plan carries an optional `## Post-cycle Fixes` section at its end, it is
   **orchestrator-owned and outside the task list** — one line per verify-stage
   `RED_BREAK` fix that belonged to no open chunk. Never read its lines as
   tasks, never mark them done, never edit the section
   (`docs/spec/adversarial-verify.md` §`## Post-cycle Fixes` in the Active Plan)
3. Read the relevant spec sections for the current task
4. Read `docs/requirements/{category}/*.md` for requirement context when needed
5. Identify which chunk you're starting from (ask if unclear)

### Step 2: Work Through Tasks

For each task, follow the process based on its type:

#### [implement] tasks — TDD Inner Loop

1. **Read the relevant spec section** before writing any code. Check the spec's `## Implementation Questions` section for existing Q-IMPL entries — these show how prior ambiguities were resolved and prevent contradictory choices
2. **Write a failing test** that captures what the spec requires
3. **Run the test** — confirm it fails (red)
4. **Write minimal code** to make the test pass
5. **Run the test** — confirm it passes (green)
6. **Refactor** if needed — tests must still pass
7. **Run full verification**: build + lint + type-check + tests
8. **Mark the task done**

#### [spike] tasks — Time-Boxed Research

1. **Note the budget** from the plan (e.g., "2 approaches, ~15 tool calls")
2. **Explore** the unknown: read docs, try APIs, prototype in a scratch branch
3. **Read prior research** from `docs/research/RS-*/findings.md` to avoid duplicating work
4. **Document findings** — write to `docs/research/RS-NNN-{topic}/findings.md` and update `docs/research/index.md`
5. **Check replan triggers** — did findings invalidate any plan assumptions?
6. If replan triggered → stop implementation, invoke `replan`
7. If no replan needed → mark done, proceed to next task

**Spike code separation:**

- Spike findings (decisions, learnings, recommendations) go to `docs/research/RS-NNN-{topic}/findings.md` — the same destination as step 4 above and as `research` spikes. Do not create a separate `docs/spikes/` tree.
- Throwaway spike code (proofs of concept, exploratory scripts) goes to `docs/research/RS-NNN-{topic}/prototype/` with a docstring noting it is throwaway (per `research` §Step 5 supporting files).
- Production code for the same functionality must be written fresh against the spec, not adapted from spike code. Spike code is optimized for speed of learning; adapting it imports shortcuts and assumptions the spec's design may have deliberately avoided.

#### [verify] tasks — Beyond Unit Tests

1. **Read the acceptance criteria** from the spec
2. **Run the specified verification** (integration test, manual check, benchmark)
3. **Document results** — what passed, what failed
4. If failures → assess severity. Minor: fix inline. Major: trigger replan

### Task Completion Checklist

Before marking any task done:

- [ ] Code builds without errors
- [ ] Type checker passes (mypy strict or equivalent)
- [ ] Linter passes (ruff, eslint, clippy, or equivalent)
- [ ] Tests pass (including the new test written for this task)
- [ ] The task's spec acceptance criteria are met
- [ ] Update `docs/requirements/traceability.md`: fill **Test** column after writing tests, fill **Implementation** column after writing code

**Per-workstream traceability (marker `4` only).** `docs/.sdd-version` is the
sole gate: under marker `3` or earlier the shared `docs/requirements/traceability.md`
is written **directly** as above. Under marker `4`, fill **Test** /
**Implementation** in the active workstream's OWN `docs/ws/<ws>/traceability.md`
(never another ws's file, never the shared aggregate in place), never fill
**Verified** (that is `verify`'s cell), and regenerate the derived aggregate
— unless the dispatched write scope omits it, which is itself the signal that
regeneration is the orchestrator's post-gate bookkeeping. File shape,
regeneration rule and the compute-live staleness caveat:
[`references/workstream-layout.md`](references/workstream-layout.md) §2.

### Step 3: Stuck Detection

You are **stuck** if any of these are true:

- Same test has failed 3+ times with different attempted fixes
- You've spent more than 2x the expected effort on a single task
- You've discovered something that contradicts the spec or plan
- A dependency you expected to exist doesn't work as documented
- **Oscillation** — either condition of the oscillation rule fires on the
  attempt ledger

Keep a per-task **attempt ledger** (one entry per attempted fix plus a
`verified_do_not_touch` list; context-only, never written to a spec or a new
file) and after every attempt evaluate the **oscillation** rule: (a) a
`result` reporting a test failing that an earlier attempt reported passing, or
(b) a `change` equal to an earlier attempt's. When stuck: **stop**, document
what you tried, assess (spec gap / plan ordering / research question), and
recommend `replan` (standalone) or return `status: BLOCKED` (dispatched).
A stuck trigger, budget exhaustion mid-task, the stage fix-loop cap or the
per-chunk redo cap composes a bounded **circuit-break checkpoint** (≤ ~15
lines, no tracebacks) in the blocked-task note under that task in the plan —
written by you in sequential mode, by the orchestrator under fan-out. When
dispatched with a `Budget:` line and any term is reached, stop starting new
work, leave the tree consistent and return `status: BUDGET_EXHAUSTED` with
`budget_consumed` in the budget's own units.

Full detail — ledger format (REQ-HARN-006), oscillation rule (REQ-HARN-007),
checkpoint format and its `RETURN:`-field composition (REQ-HARN-008), budget
exhaustion (REQ-HARN-005): [`references/stuck-detection.md`](references/stuck-detection.md).

### Step 4: Chunk Close Review

A **chunk** is a contiguous group of tasks in the plan marked by an explicit `### Chunk N: <name>` header. Chunks are implementation work units (~5-15 hours each), distinct from **delivery milestones** (M1, M2, etc. — see Step 5).

At each `### Chunk N:` boundary, run the chunk close checklist:

1. Complete all tasks in the chunk
2. Run per-task verification (build + lint + type-check + tests)
3. Run the four checks below
4. Present the chunk close report to the operator
5. Resolve all blocking findings
6. Record advisory overrides with rationale
7. Mark the chunk closed; proceed to the next

#### Check 1: Spec-Implementation Type Alignment (BLOCKING)

For each spec referenced by the chunk's tasks, extract from code blocks:
- (a) Class names — `class Foo` or `class Foo(Base)` declarations
- (b) Field names — `field_name: Type` lines within class bodies
- (c) Enum value lists — `VALUE = "literal"` lines in enum classes

(a)–(c) show the Python forms; for TypeScript, Rust, or Move use the equivalent declarations (`interface`/`struct`/`trait`/`enum`, their field declarations, and enum variants). If a spec's code blocks match no pattern for their language, report "no extractable types" as a finding-free but explicit result — never silently pass.

Grep the implementation tree for matching definitions. Report as findings:
- Class in spec but not impl
- Field name mismatch (present in spec, absent or renamed in impl)
- Enum value differences between spec and impl

Findings BLOCK chunk close. Fix by editing implementation, updating the spec, or documenting via Q-IMPL.

#### Check 2: Traceability Matrix Update (BLOCKING)

For each requirement covered by this chunk (identified via task → spec `requires:` → requirement IDs), verify traceability has:
- Test column populated (tests written during TDD)
- Implementation column populated (code module path)

Under marker `3` this checks the single shared `docs/requirements/traceability.md`.
Under marker `4` it checks the active workstream's OWN `docs/ws/<ws>/traceability.md`
(the file the workstream is allowed to edit); after filling, regenerate the shared
aggregate per the marker-`4` note in § Task Completion Checklist.

Empty columns BLOCK chunk close. Fill them before proceeding.

#### Check 3: Test Coverage Per Spec (ADVISORY)

For each spec referenced by the chunk's tasks, identify the expected implementation module. A **test convention declared in `CLAUDE.md` satisfies this check for the modules it names**, and a module is named only when it is the **script path in a command** the convention quotes — the command word of a fenced or inline-code command in `CLAUDE.md` (a `--self-test` invocation, for instance) or the `entry:` value of a hook in the `.pre-commit-config.yaml` that `CLAUDE.md` names as the commit gate — with any leading interpreter word (`python3`) dropped; a module named only in prose is not named. The derived set is decided by one command over the two declaring files (`chunk-close-review.md` §Checklist):

```
{ grep -ohE '(^|`|python3 )plugins/sdd/tools/[a-z-]+\.py' CLAUDE.md;
  grep -ohE '^\s*entry: (python3 )?[^ ]+\.py' .pre-commit-config.yaml; } \
  | grep -oE '[^ `]+\.py' | sort -u
```

A module in the derived set is covered — no finding. For every other module search the test directory for test files that import from it; none → advisory finding.

Advisory — the operator may override with rationale (e.g., "tested via integration test in `test_e2e.py`" or "verification task in next chunk").

#### Check 4: Q-IMPL Audit (ADVISORY)

Review the chunk's implementation for decisions that deviated from spec (different parameter, additional field, renamed type, different algorithm). For each, check the relevant spec's `## Implementation Questions` section for a corresponding Q-IMPL entry.

Undocumented deviations are flagged. The operator may override if the deviation is trivially obvious. Otherwise, add the missing Q-IMPL entry per the protocol (see § Q-IMPL Deviation Protocol).

#### Tiered Enforcement

| Check | Severity | On failure |
|-------|----------|------------|
| 1: Type alignment | Blocking | Fix before closing chunk |
| 2: Traceability | Blocking | Fill before closing chunk |
| 3: Test coverage | Advisory | Override with written rationale |
| 4: Q-IMPL audit | Advisory | Override with written rationale |

#### Chunk Close Report

After running all four checks, present a structured report:

```
Chunk N Close Report
- Check 1 (Type Alignment): pass | block — [findings]
- Check 2 (Traceability): pass | block — [findings]
- Check 3 (Test Coverage): pass | advisory — [findings + override rationale]
- Check 4 (Q-IMPL Audit): pass | advisory — [findings + override rationale]
- Blocking: N remaining
- Advisory: N overridden
- Chunk N: CLOSED | BLOCKED
```

The report is presented inline — not persisted as a separate file. The traceability matrix updates and Q-IMPL entries are the durable artifacts.

### Step 5: Milestone Checkpoints

At each delivery milestone boundary (M1, M2, etc.):

1. **Run full verification**: build + lint + type-check + test suite
2. **Check acceptance criteria** from all specs covered by this milestone
3. **Report to the user**: what's done, what passed, what failed
4. **Get approval** before proceeding to the next milestone

### Step 6: Completion

When the plan is complete:

1. Run the full verification suite one final time
2. Walk through every spec's acceptance criteria — confirm each one passes
3. List any spec gaps that were discovered and how they were resolved (Q-IMPL entries)
4. Set the plan's frontmatter `status:` to `complete` — **direct sessions only**.
   Under `orchestrate` this flip belongs to the orchestrator, at the implement
   stage gate on `proceed` after the stage review's `VERDICT:`, so a dispatched
   chunk leaf ticks its tasks `[x]` and never writes `status:` — the
   `status: complete` flip is the orchestrator's bookkeeping commit
   (`docs/spec/harness-loop-control.md` §Plan Completion Ownership Under Orchestration)
5. Recommend invoking `verify` for holistic validation

## Rules

- **Specs are law**: if the spec says X, implement X. If X is wrong, flag it — don't fix it silently
- **Plan is the order**: follow the task order unless you have a concrete reason to deviate (dependency issue, blocker). If you reorder, tell the user why
- **TDD is not optional**: write the test first. If you catch yourself writing implementation before a test, stop and write the test
- **Tests are not optional**: if the spec has acceptance criteria, there must be tests that verify them
- **Small commits**: commit at logical boundaries (per-task or per-subtask), not per-chunk
- **No gold-plating**: implement what the spec says. Don't add features, abstractions, or "nice to haves" that aren't in the spec
- **No silent spec interpretation**: don't silently add behavior the spec doesn't describe, don't assume the spec "probably meant" something, don't skip verification because "it's obvious" — use the Q-IMPL protocol instead
- **Stuck means stop**: if you're stuck, replan. Don't burn cycles on a broken approach
- **Spike budget is real**: when a spike task exceeds its budget, stop and report findings so far

## Q-IMPL Deviation Protocol

When implementation deviates from spec — including spec gaps discovered during implementation — classify the deviation and respond accordingly. See `docs/spec/deviation-protocol.md` for full design rationale.

### Tier 1: Implementation choice

Internal decisions that don't affect the spec's public contract — helper naming, internal data structure selection, import organization, private method decomposition.

**Response:** No documentation required. Commit normally.

### Tier 2: Spec ambiguity

The spec didn't anticipate the situation. The implementation must make a decision, but the decision doesn't change the spec's public interface.

**Response:**
1. Add a Q-IMPL entry to the relevant spec's `## Implementation Questions` section (format below).
2. Continue implementing with the chosen approach.

### Tier 3: Contract change

The spec's public interface must change — a type needs renaming, a field needs adding, an API contract needs revision.

**Response:**
1. Stop the current task.
2. Escalate to the operator.
3. The operator decides: edit the spec via `specs` and get re-approved, or trigger `replan` at Level 2 (spec gap). Q-IMPL classifies the deviation; replan handles the response.

### Q-IMPL Entry Format

Entries live in an `## Implementation Questions` section at the bottom of the relevant spec file:

```markdown
### Q-IMPL-NNN: <short topic>
**Tier**: 2 (spec ambiguity)
**Spec reference**: §<section name or quote>
**Decision**: <what you chose>
**Rationale**: <why; or **Impact** for changes affecting other components>
```

Required fields: question ID, tier, decision, and rationale (or impact for tier 2+ entries).

### Numbering Rules

- Global sequential across all specs in the project: `Q-IMPL-001`, `Q-IMPL-002`, ...
- To find the next number, scan all spec files' `## Implementation Questions` sections and increment from the highest existing.
- **Parallel-dispatch exception**: when running as a fan-out leaf with an assigned Q-IMPL number block in your dispatch, allocate from that block instead of scanning — parallel leaves scanning globally would mint colliding numbers. Gaps left by unused block numbers are permanent and acceptable.
- Append-only: retired entries stay in their spec with a `[superseded by Q-IMPL-NNN]` status note, not deleted or renumbered.

**Workstream-prefixed IDs (marker `4` only).** `docs/.sdd-version` is the sole
gate: under marker `3` or earlier, number exactly as above (bare `Q-IMPL-NNN`,
global sequential scan — behavior UNCHANGED); under marker `4`, allocate
`Q-IMPL-<WS>-NNN` from a **per-workstream** counter. Rules and the legacy-id
reading: [`references/workstream-layout.md`](references/workstream-layout.md) §3.

### Leaf Return Contract (dispatched by `orchestrate`)

When this skill runs as a dispatched leaf of `orchestrate` — a pipeline
implement dispatch, a per-chunk or fix re-dispatch, or a fan-out leaf — **end
the return text with the `RETURN:` block** (REQ-HARN-009). The orchestrator
parses the block and never infers success from prose; a return without it, with
`status:` not first, or with any multi-line value pauses at the gate as
malformed. Standalone (interactive) use is unchanged — no block is required.

```
RETURN:
  status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED   # own line, first key
  budget_consumed: {tool_calls: N, test_runs: N}            # same units as the dispatched Budget:
  files_written: []
  commits: []                                                # fan-out leaves only; else []
  tasks_completed: []                                        # task labels, e.g. "Chunk 2 task 1"
  traceability_fills: []                                     # [{req, test, impl}]
  chunk_close: {}                                            # {chunk, check1..check4, overrides}
  failures: []                                               # empty when COMPLETE
  ledger: []                                                 # [{attempt, hypothesis, change, result}]
  verified_do_not_touch: []
  open_questions: []
  blocked_writes: []                                         # [{path, content}] labeled fallback
```

Keys, types and consumers are defined in
`orchestrate/references/return-contract.md` §1; every key is present
(empty where not applicable), values are path references and one-line strings
only, and `failures` never carry a traceback. `status` is `COMPLETE` when the
dispatch's deliverable contract (the assigned chunk or stage — not the whole
plan) is met; `PARTIAL` when some tasks are done and none is blocked;
`BLOCKED` when stuck detection (§Step 3) fired; `BUDGET_EXHAUSTED` when the
dispatched budget ran out (`budget_consumed` then mandatory). Key-by-key
semantics: [`references/leaf-return.md`](references/leaf-return.md).

## Transition

When all tasks complete, recommend `verify` as the next step.
