---
name: sdd-plan
description: >
  Reads approved design specs from docs/spec/ and creates a concrete
  implementation plan with ordered tasks, dependencies, and milestones.
  Tasks are typed (implement, spike, verify). Plan includes replan triggers.
  Use after specs are approved and before writing code. Skip while specs are
  unapproved, or for single-task changes that need no ordered plan.
---

# SDD: Implementation Planning

You are creating an implementation plan from approved design specs. Your input is `docs/spec/*.md` (status: Approved). Your output is an ordered, actionable plan with typed tasks.

## Phase Detection

Before starting, check project state. **Compare `last_updated` dates** to detect stale downstream artifacts:

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
frontmatter `research_id:` against the kickoff's (`docs/ws/<ws>/kickoff.md` under
marker `4`, `docs/handoff/kickoff.md` under marker `3`) by **exact string
equality** on the trimmed value — no normalisation, case folding or prefix
matching (Q-IMPL-HARNESSP3-015). The three cases are exhaustive:

1. **Mismatch** — the artifact's `research_id` differs from the kickoff's → **a
   previous cycle's artifact**; this stage has not been reached in this cycle.
2. **Field absent** — a kickoff with a `research_id` exists but the artifact
   carries none (legacy; existing files are **never back-filled**) → the same
   reading as a mismatch. Absence is the safe direction: it costs one re-entry,
   it never asserts a completion that did not happen.
3. **No usable discriminator** — no `kickoff.md` for this `(repo, workstream)`,
   **or** a kickoff that carries no `research_id` (Q-IMPL-HARNESSP3-016) → the
   comparison is **skipped entirely** and the existing `status:`-only rule
   applies unchanged. Cycle identity is an orchestrated-cycle discriminator,
   never a precondition for detection.

See `docs/spec/cycle-identity.md`.

0. **Version check**: If `docs/.sdd-version` is missing, suggest running `sdd-migrate` before proceeding
1. If no `docs/requirements/index.md` or status is `Draft` → use `sdd-requirements`
2. If `docs/spec/*.md` are missing or any has `status: Draft` → use `sdd-specs`
3. **Staleness check**: if `docs/plan.md` exists, check for upstream changes:
   - **Single-milestone plan**: compare `docs/plan.md`'s `last_updated` frontmatter against `last_updated` in each `docs/spec/*.md` and `docs/requirements/index.md`. If any upstream artifact is newer, the plan is **stale**. (Legacy plans without frontmatter: fall back to file modification date — unreliable after a fresh clone — and add the frontmatter while updating)
   - **Multi-milestone plan** (index + per-milestone files): apply milestone-scoped staleness — for each milestone plan file, compare its `last_updated` only against specs and requirement category files traced by that milestone's tasks (task → spec → `requires:` → requirement IDs → category file dates). A change to unrelated requirements does not make the milestone plan stale
   - **Workstream-scoped (marker `4` only)**: `docs/.sdd-version` is the sole gate. Under marker `3` (or earlier) compute staleness exactly as the single-/multi-milestone bullets above — flat `docs/plan.md`, milestone key — **unchanged**. Under marker `4` the milestone-scoped traversal **generalizes verbatim** by swapping two inputs and keeping the chain identical: plan path `docs/plan.md` → `docs/ws/<ws>/plan.md`, and the **milestone key → workstream key**. Compute the scoped set **live** from the workstream's plan — walk its tasks' `traces to` specs, collect each spec's `requires:` requirement IDs, and compare the plan's `last_updated` against those specs' `last_updated` and against the requirement category files those IDs belong to (task → spec `requires:` → requirement IDs → category-file dates). The multi-milestone branch generalizes verbatim; the single-plan branch becomes the `default` workstream case. This reads **no traceability file** and adds **no** traceability schema column — the scope is derived live (REQ-WS-026). A shared spec/requirement no task in `<ws>`'s plan traces does not make that plan stale. See `docs/spec/ws-staleness.md`.
   - Stale plans need updating. Proceed to rewrite/update regardless of task completion status
4. If `docs/plan.md` exists with incomplete tasks **and is not stale** (per check 3) → use `sdd-implement`
5. If `docs/verification.md` exists with failures → use `sdd-replan`
6. If all specs are `Approved` and plan is missing or stale → you're in the right place

Tell the user which phase you detected, including any stale artifacts found, and confirm before proceeding.

## Your Role

- Break approved specs into implementable tasks
- Order tasks by dependencies (what must exist before what)
- Type each task: `implement`, `spike`, or `verify`
- Identify milestones where the system is testable end-to-end
- Define replan triggers — conditions that mean the plan is no longer valid
- Flag risks and unknowns that could block implementation
- Do NOT start implementing — this skill produces a plan only

## Process

### Step 1: Read Approved Specs

1. Read all files in `docs/spec/` — only plan from specs with `status: Approved`
2. If any spec is still `Draft` or `Under Review`, tell the user and ask whether to proceed without it or wait
3. Read `docs/requirements/index.md` for overview and priorities, then read `docs/requirements/{category}/*.md` for detail (use `index.md` to discover files)
4. Read `docs/research/RS-*/findings.md` for context on what's been explored
5. Read `CLAUDE.md` for project conventions and technical constraints

### Step 2: Identify Implementation Units

Break each spec into implementation units. An implementation unit is:

- Small enough to implement and test in one session
- Large enough to be meaningful (not "add an import")
- Has clear inputs (what it depends on) and outputs (what it produces)
- Has a definition of done from the spec's acceptance criteria

### Step 3: Type Each Task

Every task gets one of three types:

- **`implement`** — produce working code + tests for a spec section
- **`spike`** — time-boxed research to resolve a `[high-uncertainty]` section from specs. Produces findings, may cause replan. Budget: state explicitly, in observable units (e.g., "2 approaches, ~15 tool calls")
- **`verify`** — dedicated verification task (integration test, manual check, performance benchmark). Goes beyond "run pytest" — validates behavior from user perspective

### Step 4: Order by Dependencies

Build a dependency graph:

1. **Foundation first**: models, configuration, utilities
2. **Core interfaces next**: the contracts other code depends on
3. **Implementations**: concrete classes/functions that fulfill contracts
4. **Integration**: wiring components together
5. **Verification**: holistic checks

Place `spike` tasks early — their findings may invalidate later tasks.

### Step 5: Group into Chunks and Milestones

Group tasks into **chunks** — contiguous work units of ~5-15 hours each, marked by `### Chunk N: <name>` headers. Each chunk should have clear entry/exit criteria.

Decide whether to use per-milestone plan files:

- **Default: single-milestone.** Write all chunks directly to `docs/plan.md` with `### Chunk N:` headers. No `milestone:` frontmatter needed. Use this for projects with one delivery scope.

- **Per-milestone activation.** Use per-milestone files when:
  - The plan or specs explicitly define multiple delivery milestones (M1, M2, M3...), OR
  - The total chunk count exceeds ~10, or the plan would exceed ~300 lines, or work spans multiple distinct delivery scopes

When activating per-milestone structure:
1. Create `docs/plan.md` as the index (milestone table format — see Step 7)
2. Create `docs/plan-{milestone-id}.md` for each active milestone
3. Add `milestone:`, `last_updated:`, `status: planned`, and `research_id:` (immediately after `status:`) frontmatter to each milestone plan

**Marker `4`**: the same structure lives inside the workstream — `docs/ws/<ws>/plan.md` is the index and `docs/ws/<ws>/plan-{milestone-id}.md` the milestone plans, archiving to `docs/ws/<ws>/plan-history/`. Per-milestone activation is per-workstream; it never creates flat `docs/plan-*.md` files.

Each delivery milestone should produce a **testable system** — not just a pile of code. Good milestones:

- M1: Project skeleton — builds, lints, type-checks with zero functionality
- M2: Core models + first working feature end-to-end
- M3..N: Feature groups that build on each other
- Final: Full feature set, all acceptance criteria pass

**Milestone lifecycle** (per-milestone plans only):

Each milestone plan file's `status:` frontmatter transitions through:

1. **planned**: `sdd-plan` creates the file. Tasks defined but not started.
2. **active**: `sdd-implement` sets when work begins on the milestone's first task.
3. **complete**: `sdd-implement` (or `sdd-verify`) sets when all tasks are done and verified.
4. **archived**: The completed plan moves to `docs/plan-history/{date}-{milestone-id}-complete.md` and the index table is updated with the archive link.

### Step 6: Define Replan Triggers

For each spike task and any high-risk implement task, define the condition that would invalidate the current plan:

```markdown
## Replan Triggers
- If spike "OAuth2 feasibility" finds the API doesn't support refresh tokens → redesign auth section
- If performance benchmark exceeds 500ms p99 → reconsider caching strategy
- If TA-Lib C library is unavailable on target → switch to pure-Python fallback approach
```

### Step 7: Archive and Write the Plan

**Workstream scoping (marker `4`)**: under `docs/.sdd-version` == `4`, every path
in this step is rooted at the active workstream's `base = docs/ws/<ws>/` (default
`default`): the plan is `docs/ws/<ws>/plan.md` and archives go to
`docs/ws/<ws>/plan-history/`. The rewrite/archive operates **only** within this
workstream's own dir — it must never archive, overwrite, or route the plan or
plan-history of any other workstream. Under marker `3` (or earlier) the paths are
the flat `docs/plan.md` / `docs/plan-history/` exactly as written below, unchanged.

**Archival**: If the plan (`docs/plan.md`, or `docs/ws/<ws>/plan.md` under marker
`4`) already exists, archive it before writing the new plan:

1. Create the `plan-history/` directory (`docs/plan-history/`, or
   `docs/ws/<ws>/plan-history/` under marker `4`) if it doesn't exist
2. Copy the current plan to `{plan-history}/{date}-{reason}.md` (e.g., `2026-04-27-rewrite-after-spec-update.md`)
3. Then write the new plan

Save the plan to `docs/plan.md` (single-milestone; `docs/ws/<ws>/plan.md` under
marker `4`) or create the index + per-milestone files (multi-milestone).

**Single-milestone plan format (default):**

```markdown
---
last_updated: YYYY-MM-DD
status: planned   # planned → active (first task starts) → complete
research_id: RS-<WS>-NNN   # copied verbatim from the workstream's kickoff.md
---

# Implementation Plan: [Project Name]

## Overview
One paragraph: what we're implementing and the approach.

## Conventions
- **Task types**: [implement] produces code, [spike] produces findings, [verify] validates behavior.
- **Chunk headers**: `### Chunk N: <name>` per work unit.

## Chunks

### Chunk 0: [Name]
**Goal**: What's testable after this chunk.
**Depends on**: None.
**Tasks**:
1. [implement] [Task description] — traces to [spec.md]
2. [spike] [Research question, budget: 2 approaches / ~15 tool calls] — traces to [spec.md §section]
3. [verify] [What to validate] — traces to [spec.md acceptance criteria]
**Entry criteria**: None (first chunk).
**Exit criteria**: [conditions].

### Chunk 1: [Name]
**Depends on**: Chunk 0.
**Tasks**: ...
**Entry criteria**: Chunk 0 complete.
**Exit criteria**: ...

## Replan Triggers
- [Condition] → [what changes in the plan]

## Completed
- [chunk/milestone name]: [description] (YYYY-MM-DD, N tasks)

## Risks
- [Risk]: [Impact and mitigation]

## Post-cycle Fixes
<!-- OPTIONAL, orchestrator-owned, outside the task list. Omit until written. -->
- R3 — [what was broken, what was changed, path] ([sha])
```

(`## Post-cycle Fixes` is **optional, orchestrator-owned and outside the task
list** (REQ-REDB-HARNESSP3-004, `docs/spec/adversarial-verify.md` §`## Post-cycle
Fixes` in the Active Plan; the plan-structure contract is
`docs/spec/milestone-plans.md` §Milestone Plan File Format). It holds one line
per verify-stage `RED_BREAK` fix that belonged to **no open chunk**, appended at
the **end** of the plan (Q-IMPL-HARNESSP3-008). Never create it yourself, never
strip it on a rewrite — carry it across verbatim — and never turn its lines into
tasks: `sdd-implement` does not read them as tasks and they do not re-open the
task list.)

(The `last_updated:` field is what every staleness check compares; bump it on every rewrite/update. `status:` follows the same lifecycle vocabulary as per-milestone plans.)

(The `research_id:` field is the **cycle identity** stamp (REQ-CYCID-HARNESSP3-002):
copy it **verbatim** from the active workstream's `kickoff.md` (`docs/ws/<ws>/kickoff.md`
under marker `4`, `docs/handoff/kickoff.md` under marker `3`) — never derive, shorten or
invent one — and emit it on the line immediately after `status:`
(Q-IMPL-HARNESSP3-014). It is what lets a reader tell **this** cycle's
`status: complete` plan from a previous cycle's (§Phase Detection). Omit the field when
there is no kickoff or the kickoff carries no `research_id` — case 3, the comparison is
skipped. Existing plans are **not** back-filled, and nothing under
`docs/requirements/**` or `docs/spec/**` is ever stamped: the shared corpus is cumulative
and its `status: Approved` is product-wide, not per-cycle. See `docs/spec/cycle-identity.md`.)

**Multi-milestone index format** (`docs/plan.md` when per-milestone files exist):

```markdown
# Implementation Plan: [Project Name]

## Overview
One paragraph: project scope and approach.

## Milestones

| ID | Name | Plan File | Status |
|----|------|-----------|--------|
| M1 | [name] | [archived](plan-history/2026-04-20-m1-complete.md) | Complete |
| M2 | [name] | plan-m2.md | Active |
| M3 | [name] | plan-m3.md | Planned |
```

Each `docs/plan-{id}.md` follows the single-milestone format above (with `### Chunk N:` headers) plus `milestone:`, `last_updated:`, and `status:` frontmatter.

**Active plan format rules**:
- Only include current and future chunks in the active plan
- Completed chunks/milestones are summarized as one line each in the `## Completed` section
- Do NOT include a `## Plan Changelog` section in the active plan — changelog entries belong in archive files

### Planning Rules

- **Every task traces to a spec**: if you can't point to which spec a task implements, it's unplanned work — flag it
- **No task should take more than ~2 hours**: if it feels bigger, break it down
- **Tests are tasks, not afterthoughts**: "write tests for X" is a task with its own place in the order
- **Spikes go early**: place spike tasks before the implement tasks that depend on their findings
- **Don't over-plan**: if the order between two independent tasks doesn't matter, say so — let the implementor parallelize
- **Flag unknowns**: if a task depends on something you're not sure about, mark it as a risk
- **Verify tasks are explicit**: don't rely on "tests pass" — include specific verification tasks for complex features
- **Chunks not milestones for work units**: use `### Chunk N: <name>` headers for implementation work units (~5-15 hours each). Reserve "milestone" for delivery groupings (M1, M2, etc.) in multi-milestone projects
- **Declare chunk dependencies**: every chunk carries a `**Depends on**: Chunk N` field (`None` for roots; comma-separate multiple). This is the canonical machine-readable signal implement-stage fan-out parses to find independent chunk-groups — `Entry criteria:` prose is a tolerated fallback, not the canonical form

### Step 8: Review

Present the plan to the user. Ask:

- "Does the chunk ordering make sense?"
- "Are any tasks missing?"
- "Are the replan triggers right?"
- "Do you want to adjust scope for any chunk or milestone?"

Iterate until approved.

## Re-planning

When invoked for an existing plan (e.g., after `sdd-replan` triggers):

1. Note which tasks are done, in-progress, or blocked
2. Identify what changed (spike findings, spec update, discovered blocker)
3. Adjust remaining tasks, chunks, and milestones
4. Present the updated plan — don't silently change it

## Transition

When approved, recommend `sdd-implement` as the next step.
