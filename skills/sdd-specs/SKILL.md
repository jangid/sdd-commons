---
name: sdd-specs
description: >
  Reads approved requirements from docs/requirements/index.md and category
  files in docs/requirements/{category}/*.md, then produces feature design
  specs in docs/spec/. Each spec defines contracts, interfaces, and
  verification criteria — not implementation code. Use after requirements are
  approved and before implementation begins. Skip while requirements are still
  Draft, or for changes too small to need a design spec.
---

# SDD: Design Specs

You are writing design specs for a Spec-Driven Development workflow. Your input is approved requirements from `docs/requirements/index.md` (overview) and `docs/requirements/{category}/*.md` (detail). Your output is feature specs in `docs/spec/`.

## Phase Detection

Before starting, check project state:

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

0. **Version check**: If `docs/.sdd-version` is missing, suggest running `sdd-migrate` before proceeding
1. If no `docs/requirements/index.md` or status is `Draft` → use `sdd-requirements` first
2. **Staleness check**: compare `last_updated` in `docs/requirements/index.md` against `last_updated` in each `docs/spec/*.md` and `docs/plan.md` (if they exist). If requirements are newer than existing specs or plan, those downstream artifacts are **stale** — they were written against older requirements and need updating. Proceed to write/update specs regardless of their current status
   - **Workstream-scoped (marker `4` only)**: `docs/.sdd-version` is the sole gate. Under marker `3` (or earlier) run the compare above — requirements vs each spec **and** the flat `docs/plan.md` — **unchanged**. Under marker `4` specs are **shared** and plans are **per-workstream** (there are N `docs/ws/<id>/plan.md`, no flat monolith), so `sdd-specs` **stops treating the flat plan as a monolith**: check **only** requirements→spec staleness (the shared corpus — compare `docs/requirements/index.md` against each `docs/spec/*.md`) and **defer plan staleness** to `sdd-plan`'s per-workstream branch. Do **not** compare against a global `docs/plan.md` under marker `4` (REQ-WS-027). See `docs/spec/ws-staleness.md`
3. If `docs/spec/*.md` all have `status: Approved` **and are not stale** (per check 2) → use `sdd-plan`
4. If `docs/plan.md` exists with incomplete tasks **and is not stale** (per check 2) → use `sdd-implement`
5. If `docs/verification.md` exists with failures → use `sdd-replan`
6. If `docs/requirements/index.md` has `status: Approved` and specs are missing, `Draft`, or stale → you're in the right place

Tell the user which phase you detected, including any stale artifacts found, and confirm before proceeding.

## Your Role

- Translate requirements into concrete design decisions
- Define contracts, interfaces, data shapes, and behavior
- Document rationale for design choices (why X not Y)
- Include verification criteria so reviewers can assess testability
- Mark sections with high uncertainty that may need spikes during implementation
- Do NOT write implementation code — specs define WHAT the system looks like, not the code

## Process

### Step 1: Read Requirements

1. Read `docs/requirements/index.md` — this is your overview and entry point
2. Read `docs/requirements/{category}/*.md` — detailed requirements organized by category. Use `index.md` to discover which category directories and files exist
3. Read `docs/research/RS-*/findings.md` — prior research informs design decisions
4. Read `CLAUDE.md` or `README` for project context and technical constraints
5. Read any existing specs in `docs/spec/` — you may be adding or updating
6. Flag any requirements that are ambiguous or conflicting — ask the user before proceeding

### Step 2: Plan Spec Structure

Propose a list of spec files to the user. Each spec should cover a cohesive feature area. Example:

```
docs/spec/
  overview.md          # Architecture, principles, package structure
  feature-a.md         # One feature area
  feature-b.md         # Another feature area
  testing.md           # Testing strategy
```

Get approval on the structure before writing. The user may merge or split areas.

**Merge-safe shared writes (marker `4` only).** `docs/.sdd-version` is the sole gate;
under marker `3` or earlier this is unchanged. Under marker `4`, `docs/spec/` is a
single **shared** corpus that concurrent workstreams extend, so writes must
3-way-merge cleanly (REQ-WS-010, REQ-WS-013): each new design lands as a **new file**
in `docs/spec/` — never an in-place edit to an existing shared spec body. Modifying
an existing shared spec remains a **human PR conflict** to resolve and is not
automated. New files by distinct workstreams never share a git location, so they
merge without conflict. See `docs/spec/ws-ids.md`.

### Step 3: Write Specs

Start with `overview.md` — get it approved before writing other specs. The overview establishes architecture and principles that other specs depend on.

Each spec follows this format:

```markdown
---
status: Draft
last_updated: YYYY-MM-DD
requires: [REQ-{DOMAIN}-{NNN}, ...]  # e.g. REQ-AUTH-001, REQ-PERF-002
---

# Feature Name

## Context
Why this feature exists and what problem it solves.
Reference the requirements it fulfills.

## Design

### [Sub-section as needed]
Contracts, interfaces, data shapes, behavior.
Decisions with rationale (why X not Y).

### [Sub-section] [high-uncertainty]
Mark sections where the design depends on unverified assumptions.
Note what spike would resolve it and what the fallback is.

Keep this section focused on:
- Public interfaces and their contracts
- Data models and their invariants
- Behavior under normal and error conditions
- Interaction with other features/specs

Do NOT include:
- Line-by-line implementation instructions
- File paths or directory structures (except in overview.md)
- Code snippets longer than 10 lines (use pseudocode for contracts)

## Verification

### Automated
- Key test scenarios with descriptive names
- Cover: happy path, edge cases, failure modes, boundary conditions

### Manual (if any)
- Steps to verify interactively (only when automated testing isn't sufficient)

### Acceptance Criteria
- [ ] Checkable conditions that define "done"
- [ ] Each must be independently verifiable
- [ ] Must include: type checking passes, linting clean
- [ ] Must trace to at least one requirement
```

### Step 3b: Update Traceability

After writing or updating each spec, update traceability:

1. For each requirement ID listed in the spec's `requires` frontmatter, fill in the **Spec** column with the spec filename
2. This keeps a single source of truth for requirement-to-artifact mapping

**Per-workstream traceability (marker `4` only).** `docs/.sdd-version` is the sole gate.
Under marker `3` or earlier, write the **Spec** column into the single shared
`docs/requirements/traceability.md` directly, as above (unchanged). Under marker `4`,
traceability rows are per-workstream-owned (REQ-WS-008): fill the **Spec** column in the
active workstream's OWN file `docs/ws/<ws>/traceability.md` (6-column matrix with the
`Workstream` column as the 3rd column) — never another ws's file and never the shared aggregate
in place — then **regenerate** the shared `docs/requirements/traceability.md` wholesale
(shipped legacy rows — rows predating the v4 migration, attributed to the blank/default workstream — + concat of every `docs/ws/<id>/traceability.md`, stable-sorted by
requirement id; never appended/hand-merged). See `docs/spec/ws-traceability.md`.

**Unless the dispatched write scope omits the aggregate (REQ-WS-HARNESSP3-001).**
Regenerate the aggregate after the per-ws write **unless this run was dispatched
with a write scope that omits `docs/requirements/traceability.md`** — under
`sdd-orchestrate` that path is absent from every leaf scope by construction, and
its absence *is* the signal that regeneration is the orchestrator's post-gate
bookkeeping (`sdd-orchestrate/references/write-scope.md` §2, §7). Its presence in
the dispatched scope, or no dispatched write scope at all (a standalone run),
means regenerate here. No flag or field beyond the scope slot is involved.

### Spec Rules

- **Trace everything**: every spec must list which requirements it addresses in the `requires` frontmatter. If you're writing something no requirement covers, flag it to the user — don't invent requirements.
- **One cohesive area per spec**: a spec should be readable in isolation. Cross-references to other specs are fine but shouldn't be required to understand the core design.
- **Keep specs cohesive**: ~1000 lines is a soft review trigger, not a hard cap. When a spec grows past it, prefer splitting by cohesive feature area, or moving bulky detail out — don't split just to hit a number. Line count is a proxy for cohesion and readability, not the goal.
- **Decisions need rationale**: every non-obvious design choice should have a "why" — a sentence or two explaining the tradeoff. Future readers need to know if the context has changed enough to revisit the decision.
- **Verification is design**: the verification section is reviewed alongside the design, not added as an afterthought. If you can't write verification criteria, the design isn't concrete enough.
- **Mark uncertainty**: sections marked `[high-uncertainty]` become spike tasks in the plan. They must include: what assumption is unverified, what spike would resolve it, and what the fallback design is if the assumption is wrong.

### Step 4: Review Cycle

Present each spec to the user for review. The lifecycle is:

```
Draft → Under Review → Approved
```

- **Draft**: you've written it, not yet presented
- **Under Review**: presented to user, awaiting feedback
- **Approved**: user has signed off, ready for implementation

When the user requests changes:
1. Update the spec in place
2. Update `last_updated`
3. Keep status as `Under Review` until the user approves

### Step 4b: Cross-Spec Consistency Pass

After all specs are individually reviewed and approved (Step 4) and before the coverage check (Step 5), run a cross-spec consistency pass to catch type reference mismatches between specs.

This validates that when one spec references a type defined in another spec, the type exists with the expected fields. Catches the failure mode where spec A says "match by `contract_id`" but spec B's type doesn't include that field.

**Process:**

1. **Extract type definitions** from each spec's code blocks, using the pattern set matching each block's language:
   - Python: `class Foo` / `class Foo(Base)`; enums `class Foo(Enum)` / `class Foo(StrEnum)`; aliases `Foo: TypeAlias = Bar` / `Foo = NewType("Foo", Bar)` only — bare `Foo = ...` is excluded to avoid noise on TypeVar/generic declarations
   - TypeScript: `interface Foo`, `class Foo`, `enum Foo`, `type Foo = ...`
   - Rust: `struct Foo`, `enum Foo`, `trait Foo`, `type Foo = ...;`
   - Move: `struct Foo` (incl. `public struct Foo`)
   - If a spec's code blocks match **no** pattern for their language, report "no extractable type definitions in {spec}" as an explicit result — a silent no-op reads as a clean pass and hides the gap

2. **Build a type-to-spec map**: `{TypeName: spec-file.md}` across all specs. Flag duplicates (same type defined in multiple specs) as findings.

3. **Scan for cross-spec references**: For each spec, search prose and code blocks for type names defined in other specs. A reference is any mention outside the defining spec.

4. **Validate each reference**:
   - Type exists in target spec? If not → finding
   - Expected fields present? If the referencing spec mentions specific fields of the type, verify those fields exist in the target spec's definition → finding if missing
   - Field name consistency? Same conceptual field with different names across specs → finding

**Findings policy:** Flag-only, no auto-fix. Cross-spec mismatches typically have multiple valid resolutions (the referencing spec might be wrong, the defining spec might be incomplete, the types might need restructuring). Present findings to the operator with the referencing spec, target spec, and what's missing or inconsistent. The operator resolves each finding by editing the relevant spec(s) and re-running the pass until clean.

**Scope limits:**
- Type names only — semantic meaning isn't validated
- Code blocks only — types described in prose without a code definition aren't picked up
- No transitive checking — A→B is validated; if B references C, that's checked when processing B

See `docs/spec/cross-spec-consistency.md` for full design rationale and edge cases.

### Step 5: Coverage Check

After all specs are written, read `docs/requirements/traceability.md` and verify:

1. **Every requirement is covered** — each REQ-* ID has a non-empty Spec column in traceability.md
2. **No orphan specs** — every spec traces to at least one requirement
3. **No contradictions** — specs don't make conflicting design decisions
4. **Uncertainty inventory** — list all `[high-uncertainty]` sections and confirm the user is aware

Present a summary based on `traceability.md`:

```
REQ-AUTH-001 → auth.md (covered)
REQ-AUTH-002 → auth.md (covered)
REQ-PERF-001 → testing.md (covered)
...
[Uncovered]: REQ-DATA-015 (Spec column empty in traceability.md)
[High-uncertainty]: auth.md §OAuth2 flow, testing.md §TA-Lib fallback
```

## Updating Existing Specs

When updating specs after code exists:

1. Read the current spec and the current code
2. Update the spec to reflect the proposed change
3. Bump `last_updated`, set status back to `Under Review`
4. In the design section, note what changed and why: `[Changed YYYY-MM-DD: switched from X to Y because Z]`
5. Update verification/acceptance criteria to cover the change
6. Present the diff to the user for approval

## Transition

When all specs are approved, recommend `sdd-plan` as the next step.
