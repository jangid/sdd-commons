---
name: research
description: >
  Time-boxed exploration to reduce uncertainty before committing to requirements
  or design. Produces structured findings in docs/research/RS-NNN-{topic}/.
  Use when facing unfamiliar APIs, unknown libraries, architectural unknowns,
  or feasibility questions. Skip when the domain is well-understood.
---

# SDD: Research

You are conducting a time-boxed research spike to reduce uncertainty. Your output is structured findings — not code, not requirements, not design.

## Phase Detection

Research is always a valid entry point — new exploration doesn't require a clean slate. Before starting, check what exists so you can inform the user:

**Workstream & version gate (v4).** This skill accepts an optional `workstream`
argument that defaults to `default`. Read `docs/.sdd-version` first — it is the
**sole** layout gate:

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Ignore the workstream
  argument and run exactly the numbered detection below against flat
  `docs/plan.md` / `docs/verification.md`; never read or write `docs/ws/`. The v3
  path is unaffected.
- **Marker is `4` (workstream-aware layout).** Resolve `ws` = the workstream
  argument (default `default`), set `base = docs/ws/<ws>/`, and note any
  **execution artifacts** (`plan.md`, `verification.md`, `kickoff.md`,
  `plan-history/`) under `base` — never at flat `docs/`. The **shared corpus**
  stays at its top-level paths and is used as-is: `docs/research/`,
  `docs/requirements/` (index, category files, aggregated `traceability.md`),
  `docs/spec/`. Research findings are shared-corpus artifacts written under
  `docs/research/`.

Ownership, sharing, solo-`default`, and approval semantics under marker `4`
follow the common v4 contract — see `docs/spec/ws-layout.md`. In short: a
workstream owns only its `docs/ws/<ws>/` execution artifacts and per-ws
`traceability.md`; requirements/specs/research and the aggregated traceability
are shared (ADD, never fork); omitting the argument resolves `default`.

1. **Version check**: Read `docs/.sdd-version`. If missing, suggest running `migrate` before proceeding — it migrates pre-versioning layouts and initializes greenfield projects. If present but below the latest supported version, note that `migrate` can upgrade (advisory, not blocking).
2. If `docs/verification.md` exists with failures → mention it; user may want `replan` instead, but research is valid if they're exploring a new direction
3. If downstream artifacts exist (`docs/requirements/index.md`, `docs/spec/`, `docs/plan.md`) → note them. These may become stale after new research — that's expected. Downstream phases will detect staleness and update them
4. If existing `docs/research/RS-*` directories cover this topic → you may be extending prior research. Read their `findings.md` files first to avoid duplicating work. Check the `docs/research/index.md` table for a quick scan of existing spikes and their statuses
5. Proceed with research

Tell the user what artifacts exist and confirm the research direction before proceeding.

## Your Role

- Explore unknowns through reading docs, trying APIs, and prototyping
- Prove or disprove feasibility of approaches
- Produce findings that inform requirements and design decisions
- Stay within a time/scope budget — research expands to fill available time if unconstrained

## Process

### Step 1: Define the Research Question

Ask the user:
- "What are we trying to learn?" — the specific question(s) this spike should answer
- "What would success look like?" — how will we know when we have enough information
- "What's the budget?" — suggest a scope limit in **observable units** an agent can actually track — N approaches, N documents/APIs tried, N prototype iterations (e.g., "explore 3 approaches, ~20 tool calls"); wall-clock time is a secondary hint at best

If the user doesn't specify a budget, propose one based on the question complexity.

### Step 2: Assign Research ID

Before starting exploration, assign an ID for this spike:

1. Scan `docs/research/` for directories matching `RS-NNN-*`
2. Extract the highest `NNN` value from existing directories
3. Increment by 1 and zero-pad to 3 digits (e.g., `RS-002` if `RS-001` exists)
4. If no `RS-*` directories exist, start at `RS-001`
5. Choose a kebab-case topic slug (e.g., `oauth2-feasibility`, `plan-bloat-analysis`)

The new spike directory will be: `docs/research/RS-NNN-{topic}/`

**Workstream-prefixed IDs (marker `4` only).** `docs/.sdd-version` is the sole
gate. When the marker is **not** `4` (v3 or earlier), allocate exactly as in
steps 1–4 above — bare `RS-NNN`, global scan, behavior UNCHANGED. When the marker
is `4`, resolve `ws` (the workstream argument, default `default`) and allocate a
workstream-prefixed id `RS-<WS>-NNN` with a **per-workstream counter**:

1. Scan `docs/research/` for directories matching `RS-<ws>-NNN-*` (this workstream's
   ids only — a different `<ws>` is a different, independent sequence)
2. Extract the highest `NNN`, parsing the number **after** the `<ws>` token
3. Increment by 1 and zero-pad to 3 digits (e.g., `RS-ISSUE42-002` if
   `RS-ISSUE42-001` exists); if no `RS-<ws>-*` directories exist, start at
   `RS-<ws>-001`
4. The directory is `docs/research/RS-<WS>-NNN-{topic}/`; the frontmatter `id:` is
   `RS-<WS>-NNN`

Scoping the scan per workstream is what makes two workstreams concurrently allocate
`RS-ISSUE42-001` and `RS-ISSUE57-001` with no coordination and no collision
(REQ-WS-009, REQ-WS-011). Legacy bare `RS-NNN` ids from a v3 corpus are treated as
the `default` workstream and are NOT remapped. See `docs/spec/ws-ids.md`.

**Do NOT touch (RS-007 Q4 — provably unaffected):** cross-references that match
`RS-*` by prefix-glob or as opaque strings (index rows, `research_refs:`, inline
`(see RS-...)`) tolerate the inserted `<WS>` segment unchanged — do not "fix" them.

**Edge case**: If a directory exists but its `findings.md` is missing or has `status: Abandoned`, the number is still consumed — IDs are never reused (per workstream under marker `4`).

### Research Early-Exit When the Shared Corpus Already Covers the Work (marker `4`)

`docs/.sdd-version` is the sole gate. Under marker `3` or earlier this subsection does
**not** apply — run the full spike (Steps 3–7) as always. Under marker `4`, because
every new workstream begins at research for uniformity (REQ-WS-024,
`orchestrate` §Workstream Picker), the research stage **should** early-exit fast
(REQ-WS-025) when the shared corpus already covers this workstream's needs, so uniform
research-entry imposes minimal overhead:

1. **Judge coverage.** On entry at research for a workstream `ws`, check whether the
   existing **shared** corpus — `docs/requirements/`, `docs/spec/`, prior
   `docs/research/RS-*/findings.md` — already answers what this workstream needs. This
   is a recorded judgment, not a staleness check (ongoing staleness of traced shared
   inputs is handled separately and live — see `docs/spec/ws-staleness.md`).
2. **If already covered → record a fast, explicit early-exit** instead of a full
   spike. Assign the RS id per Step 2, then write
   `docs/research/RS-<WS>-NNN-{topic}/findings.md` with frontmatter
   `status: Complete` **and** `early_exit: true`, and a single finding
   **"Covered by shared corpus — no new spike"** naming the shared REQ/SPEC/RS ids
   that cover the work. **Skip Steps 3–4** (no Explore, no Prototype, no budget burn).
   Update the research index (Step 6) with the early-exit summary, then advance the
   loop (Step 7 → proceed to requirements/next stage). The early-exit is **recorded**
   so the workstream's research state is auditable, and it is **distinct** from a full
   spike (`early_exit: true` marks it).
3. **If NOT covered → run the full spike** (Steps 3–7). The early-exit is a `should`,
   not a `must`: a workstream is always free to run a real spike; the early-exit is
   only the optimization that keeps the common "already covered" case near-zero-cost.

### Step 3: Explore

For each research question:

1. **Survey** — read docs, search for prior art, check existing libraries
2. **Prototype** (if needed) — minimal throwaway code in a scratch branch to prove feasibility
3. **Document as you go** — capture findings immediately, don't rely on memory

Exploration approaches by uncertainty type:
- **API unknown**: make real calls, inspect responses, document shapes
- **Library unknown**: read docs, try the happy path, check edge cases
- **Architecture unknown**: sketch 2-3 approaches, identify trade-offs
- **Feasibility unknown**: build the riskiest part first in isolation

### Step 4: Budget Enforcement

Track your progress against the budget. When you've consumed ~80% of the budget:
- Summarize what you've learned so far
- Ask the user: "extend budget, narrow scope, or stop here?"

Do NOT continue open-ended exploration past the budget.

### Step 5: Write Findings

Save to `docs/research/RS-NNN-{topic}/findings.md`:

```markdown
---
id: RS-NNN
status: Complete
date: YYYY-MM-DD
questions:
  - "The specific question we were answering"
budget: "What was allocated"
---

# Research: [Topic]

## Questions
What we set out to learn.

## Findings

### [Question 1]
**Answer**: [Clear, actionable answer]
**Evidence**: [What we observed/tested]
**Confidence**: [High/Medium/Low — and why]

### [Question 2]
...

## Implications for Design
- What this means for requirements/specs
- Approaches that are viable vs ruled out
- Constraints discovered

## Prototype (if any)
- Branch: `research/{topic}` (throwaway — do not merge)
- What it demonstrates
- What it doesn't prove

## Open Questions
- Things we still don't know (may need another spike)
```

The `id` field in frontmatter must match the directory prefix (e.g., `RS-001` for directory `RS-001-oauth2`). This allows validation and makes the ID visible when reading the file without inspecting the path.

Supporting files (prototype code, API response samples, screenshots) go in subdirectories within the spike directory:
- `docs/research/RS-NNN-{topic}/prototype/` — throwaway code
- `docs/research/RS-NNN-{topic}/responses/` — API response samples, screenshots
- `docs/research/RS-NNN-{topic}/notes.md` — raw notes, scratchpad

### Step 6: Update Research Index

After writing findings, update `docs/research/index.md`. If the index doesn't exist yet, create it.

**Index format**:

```markdown
---
last_updated: YYYY-MM-DD
---

# Research Index

| ID | Topic | Date | Status | Summary |
|----|-------|------|--------|---------|
| RS-001 | OAuth2 feasibility | 2026-03-15 | Complete | OAuth2 refresh tokens supported; proceed with auth design |
| RS-002 | Plan bloat analysis | 2026-04-27 | Complete | Three bloat sources identified; archive pattern proposed |
```

- Add a new row for a new spike, or update the existing row if revising a spike
- One row per research spike, sorted by ID (chronological by creation)
- Bump `last_updated` in frontmatter to today's date
- Summary should be a single sentence capturing the key finding or outcome

### Step 7: Recommend Next Step

Based on findings, recommend one of:
- **Proceed to requirements** — "We know enough to define what to build"
- **Another spike** — "Question X needs more exploration"
- **Pivot** — "This approach won't work because Y. Consider Z instead"
- **Stop** — "This isn't worth building because..."

## Cross-Referencing

Other artifacts reference research spikes by their RS-NNN ID:
- **Requirements**: `research_refs: [RS-001, RS-002]` in frontmatter, or inline `(see RS-001)` in prose
- **Specs**: `(see RS-001 §Findings)` in design rationale sections
- **Plan**: spike tasks reference `RS-NNN` when extending prior research

Always use the RS-NNN ID for cross-references, not file paths — IDs are stable even if directory structure changes.

## Rules

- **Budget is real**: don't exceed it. Partial findings are better than exhaustive ones delivered late
- **Findings over code**: prototypes are evidence, not deliverables. They live on throwaway branches
- **Concrete over abstract**: "the API returns X in Y format" beats "the API seems flexible"
- **Negative results are valuable**: "this won't work because X" saves weeks of implementation
- **One spike per uncertainty**: don't bundle unrelated questions into one research session
- **IDs are permanent**: never reuse an RS-NNN number, even if the spike was abandoned
