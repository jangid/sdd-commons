---
name: sdd-requirements
description: >
  Guides requirements gathering for a new project or feature using Spec-Driven
  Development (SDD). Produces structured requirements in docs/requirements/
  (split by domain) through iterative Q&A with the user. Use at the start of
  any new project or when adding significant new functionality. Can reference
  prior research from docs/research/. Skip for bug fixes and small tweaks that
  don't change what the system should do.
---

# SDD: Requirements Gathering

You are guiding the user through requirements gathering for a Spec-Driven Development workflow. Your output is a structured set of requirement files under `docs/requirements/`.

## Phase Detection

Requirements gathering is always valid — the user may be starting a new cycle or updating existing requirements. Before starting, check project state:

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
  `plan-history/`) under `base` — never at flat `docs/`. Requirements are part of
  the **shared corpus**: the requirements index, category files, and the
  aggregated `traceability.md` stay at their top-level `docs/requirements/` paths
  and are ADDED to (never forked per workstream); `docs/research/` and `docs/spec/`
  are likewise shared.

Ownership, sharing, solo-`default`, and approval semantics under marker `4`
follow the common v4 contract — see `docs/spec/ws-layout.md`. In short: a
workstream owns only its `docs/ws/<ws>/` execution artifacts and per-ws
`traceability.md`; requirements/specs/research and the aggregated traceability
are shared (ADD, never fork); omitting the argument resolves `default`.

1. **Version check**: Read `docs/.sdd-version`. If missing, suggest running `sdd-migrate` before proceeding — it migrates pre-versioning layouts and initializes greenfield projects. If present but below the latest supported version, note that `sdd-migrate` can upgrade (advisory, not blocking).
2. **Format detection**: Check which format exists:
   - If `docs/requirements/index.md` exists → v2 format, proceed normally
   - If `docs/requirements.md` exists (v1 monolithic format) → suggest running `sdd-migrate` to convert to v2 structure before proceeding. Do not attempt to read/write the v1 format
   - If neither exists → start fresh with the current format
3. If `docs/requirements/index.md` exists with `status: Draft` → resume requirements gathering
4. If `docs/requirements/index.md` exists with `status: Approved` → inform the user. They can either:
   - Update the existing requirements (proceed here, downstream artifacts will become stale)
   - Move to the next phase (`sdd-specs` if specs are missing/stale, `sdd-plan` if specs are done)
5. If downstream artifacts exist (`docs/spec/`, `docs/plan.md`, `docs/verification.md`) → note them. If requirements are being rewritten or significantly updated, these will become stale and need updating in subsequent phases — that's the intended workflow
6. **Research staleness check** (REQ-STALE-002): Read `docs/research/index.md` if it exists. Find the newest research date (latest `Date` column entry with `status: Complete`). Compare against `docs/requirements/index.md`'s `last_updated`. If research is newer, inform the user: "Research RS-NNN completed on {date} — requirements may need updating to reflect new findings." This is advisory, not blocking.
   - **Workstream-independent (marker `4`)**: `docs/.sdd-version` is the sole gate, but this check is deliberately **the same under marker `3` and marker `4`**: requirements are a product-wide shared corpus, so research→requirements staleness stays on the **shared corpus** and is **NOT** scoped by any workstream key — a shared requirement can be stale relative to shared research regardless of which workstream is active (REQ-WS-028). The **only** thing that changes under marker `4` is that research IDs may be workstream-prefixed (`RS-<WS>-NNN`, per `docs/spec/ws-ids.md`); the "newest `status: Complete` research date vs `requirements/index.md` `last_updated`" comparison is otherwise unchanged and applies no workstream key. See `docs/spec/ws-staleness.md`.

Tell the user what artifacts exist and confirm how to proceed.

## Your Role

- Ask questions to clarify scope, constraints, and expected behavior
- Identify gaps and ambiguities in what the user describes
- Organize requirements into domain-specific files with unique IDs
- Reference research findings when available (by RS-NNN ID)
- Do NOT design solutions — requirements describe WHAT, not HOW

## Process

### Step 1: Understand Context

Before asking questions, understand what exists:

1. Read `docs/requirements/index.md` — check the Files table for existing category files and their status
2. Read existing category files under `docs/requirements/` — you may be adding to them, not starting fresh
3. Read `docs/research/index.md` and relevant `docs/research/RS-*/findings.md` — prior spikes inform what's feasible and what constraints exist
4. Read `CLAUDE.md` or `README` for project context
5. Ask the user: "What are we building and why?" if not already clear

### Step 2: Elicit Requirements

Ask questions in these categories (skip what's already clear):

- **Functional**: What must the system do? What are the inputs/outputs?
- **Non-functional**: Performance, security, reliability, scalability constraints?
- **Integration**: What does this connect to? What protocols/APIs?
- **Configuration**: What must be configurable? What are sensible defaults?
- **Scope boundaries**: What is explicitly out of scope?

Don't ask all questions at once. Go category by category. Listen for implicit requirements in the user's answers — things they assume but don't state.

When a requirement depends on an unresolved uncertainty, mark it with `[needs-spike]` and note what research is needed.

### Step 3: Capture External Input

The user may bring in requirements from other parties (stakeholders, docs, tickets). When they paste or describe external requirements:

1. Restate them in your own words to confirm understanding
2. Assign requirement IDs (using the domain-based scheme)
3. Flag any conflicts with existing requirements
4. Ask clarifying questions about ambiguities

### Step 4: Write Requirements

Write requirements to the appropriate category files based on domain. The directory structure is:

```
docs/requirements/
  index.md                      # Versioned index (auto-maintained)
  traceability.md               # RTM: requirement -> spec -> test -> status
  functional/
    {domain}.md                 # One file per feature domain
  non-functional/
    {concern}.md                # One file per quality concern
  integration/
    {system}.md                 # One file per external system
  configuration/
    {area}.md                   # One file per config area
```

#### Category File Format

Each category file follows this structure:

```markdown
---
domain: AUTH
last_updated: YYYY-MM-DD
status: Draft
---

# Requirements: Authentication

## Overview
Brief context for this domain — what it covers and why.

## Requirements

### REQ-AUTH-001: User login via OAuth2
The system must authenticate users through OAuth2 providers.

### REQ-AUTH-002: Session expiry
User sessions should expire after 30 minutes of inactivity.

### REQ-AUTH-003: Remember me option
The system may offer a "remember me" checkbox extending sessions to 30 days.
```

**Conventions**:
- `domain` in frontmatter is the uppercase prefix used in IDs for this file (2-8 chars)
- Each requirement is an h3 heading: `### REQ-{DOMAIN}-{NNN}: {title}`
- Priority is expressed solely by the requirement's modal verb — must (mandatory), should (preferred), may (optional); no separate `[Priority:]` tag
- One requirement per heading — no bundling multiple behaviors
- Requirements are testable statements — if you can't write a verification, rewrite

#### ID Assignment

Use `REQ-{DOMAIN}-{NNN}` format:
- `{DOMAIN}` is an uppercase short name matching the file's `domain` frontmatter
- `{NNN}` is a zero-padded 3-digit number, sequential within the domain
- Scan **all category files sharing the domain prefix** (a prefix can span multiple files after a split — check the Domain Prefixes table) for the highest existing NNN and increment
- New files start at 001
- IDs are globally unique — the domain prefix prevents collisions
- When creating a new category file, choose a domain prefix that doesn't collide with existing prefixes (check `index.md` Domain Prefixes table)
- Never reuse IDs, even for removed requirements

**Workstream-prefixed IDs (marker `4` only).** `docs/.sdd-version` is the sole
gate. When the marker is **not** `4` (v3 or earlier), allocate exactly as above —
bare `REQ-{DOMAIN}-{NNN}`, highest-NNN scan within the domain, behavior UNCHANGED.
When the marker is `4`, resolve `ws` (the workstream argument, default `default`)
and allocate `REQ-{DOMAIN}-<WS>-{NNN}` with a **per-`domain+workstream` counter**:
- `{NNN}` is parsed **after** the `<WS>` token and scanned for its max per
  `domain+workstream` — not globally within the domain — so each workstream
  advances an independent sequence under a shared domain (REQ-WS-009, REQ-WS-011)
- `REQ-AUTH-ISSUE42-001` and `REQ-AUTH-ISSUE57-001` are both valid and collision-free
- Legacy bare `REQ-{DOMAIN}-{NNN}` ids from a v3 corpus are treated as the `default`
  workstream and are NOT remapped. See `docs/spec/ws-ids.md`.

**Do NOT touch (RS-007 Q4 — provably unaffected):** requirements/traceability row
parsing matches `REQ-*` by prefix-glob / opaque string and tolerates the inserted
`<WS>` segment unchanged — do not add or "fix" any numeric-suffix parser.

#### Index File Format

`docs/requirements/index.md` is auto-maintained:

```markdown
---
version: 1.0
status: Draft
last_updated: YYYY-MM-DD
---

# Requirements Index

## Summary
One paragraph: what the project is and what this requirements set covers.

## Stakeholders
Who provided requirements and their role/perspective.

## Files

| Category | File | Domain | Status | Count | Last Updated |
|----------|------|--------|--------|-------|--------------|
| Functional | functional/auth.md | AUTH | Approved | 12 | 2026-04-28 |

## Domain Prefixes

Reserved prefixes to prevent collisions:

| Prefix | File | Description |
|--------|------|-------------|
| AUTH | functional/auth.md | Authentication and authorization |

## Out of Scope
- Explicit list of what this project does NOT do

## Open Questions
- Unresolved items that need answers before specs can be written
- Items marked [needs-spike] that require research

## Glossary
Domain-specific terms used in these requirements.

## See Also
- [Traceability Matrix](traceability.md)
```

#### Traceability File Format

`docs/requirements/traceability.md` maps requirements through the lifecycle:

```markdown
---
last_updated: YYYY-MM-DD
---

# Traceability Matrix

| Requirement | Spec | Test | Implementation | Verified |
|-------------|------|------|----------------|----------|
| REQ-AUTH-001 | | | | |
| REQ-AUTH-002 | | | | |
```

When adding new requirements, add rows with the Spec/Test/Implementation/Verified columns blank. Other SDD skills fill those columns later:
- `sdd-specs` fills the Spec column
- `sdd-implement` fills Test and Implementation columns
- `sdd-verify` fills the Verified column — its three legal values are `pass`,
  `fail` and `pending-red` (written while a red round is outstanding, flipped to
  `pass` by the orchestrator at DONE; `docs/spec/ws-traceability.md` §Legal
  `Verified` Cell Values)

### Requirement Rules

- Every requirement gets a unique ID: `REQ-{DOMAIN}-{NNN}` where DOMAIN matches the file's frontmatter
- Requirements must be **testable** — if you can't write a verification for it, rewrite it
- Requirements describe behavior, not implementation ("the system must support multiple exchanges" not "use a factory pattern for exchanges")
- One requirement per ID — don't bundle multiple behaviors
- Use "must" for mandatory, "should" for preferred, "may" for optional
- Mark uncertain requirements with `[needs-spike]` — these may bounce back to `sdd-research`

### Step 5: Auto-Maintain Index and Traceability

After every write to a category file, perform these maintenance steps:

1. **Update category file frontmatter**: Bump `last_updated` to today
2. **Update index.md**:
   - Bump `version`: major bump for requirements added/removed/fundamentally changed; minor bump for clarifications, rewording, priority changes
   - Bump `last_updated` to today
   - Update the Files table row for the changed file (count, status, last_updated)
   - Add new rows to Files table and Domain Prefixes table if a new category file was created
3. **Update traceability.md**:
   - Add rows for new requirements (all columns except Requirement are blank)
   - For removed requirements: delete from category file, mark `[Deprecated]` in the traceability Requirement column. Never reuse the ID
   - Bump `last_updated` to today

   **Per-workstream traceability (marker `4` only).** `docs/.sdd-version` is the sole
   gate. Under marker `3` or earlier, add rows to the single shared
   `docs/requirements/traceability.md` directly, as above (unchanged). Under marker `4`,
   traceability rows are per-workstream-owned (REQ-WS-008): the requirement text stays in
   the **shared** category file (added merge-safe per the "Merge-safe shared writes" note
   in this Step 5, below), but the new **row** — recording that this workstream delivers the REQ — is written into the
   active workstream's OWN file `docs/ws/<ws>/traceability.md` (frontmatter
   `workstream: <ws>` / `last_updated:`; 6-column matrix with the `Workstream`
   column as the 3rd column), never another ws's file and never the shared aggregate in place. Then
   **regenerate** the shared `docs/requirements/traceability.md` wholesale (shipped legacy
   rows — rows predating the v4 migration, attributed to the blank/default workstream — + concat of every `docs/ws/<id>/traceability.md`,
   stable-sorted by requirement id; never appended/hand-merged). See
   `docs/spec/ws-traceability.md`.

**Unless the dispatched write scope omits the aggregate (REQ-WS-HARNESSP3-001).**
Regenerate the aggregate after the per-ws write **unless this run was dispatched
with a write scope that omits `docs/requirements/traceability.md`** — under
`sdd-orchestrate` that path is absent from every leaf scope by construction, and
its absence *is* the signal that regeneration is the orchestrator's post-gate
bookkeeping (`sdd-orchestrate/references/write-scope.md` §2, §7). Its presence in
the dispatched scope, or no dispatched write scope at all (a standalone run),
means regenerate here. No flag or field beyond the scope slot is involved.

**Merge-safe shared writes (marker `4` only).** `docs/.sdd-version` is the sole
gate; under marker `3` or earlier this is unchanged. Under marker `4`,
`requirements/`, `spec/`, `research/`, and the aggregated traceability are a single
**shared** corpus that concurrent workstreams write, so every write must 3-way-merge
cleanly (REQ-WS-010, REQ-WS-013, REQ-WS-015):

- **New requirements append under a claimed domain prefix.** A workstream adds new
  `REQ-{DOMAIN}-<WS>-{NNN}` ids under a domain prefix it has claimed in the Domain
  Prefixes registry — it never rewrites an existing shared requirement body.
  Modifying an existing shared requirement stays a **human PR conflict**, not
  automated.
- **ID-sorted, one-row-per-line insertion — never raw EOF append.** Additions to
  `docs/requirements/index.md` (Files table, Domain Prefixes table) and new
  requirement rows within a category file are inserted at their correct **sorted
  position** by id/prefix key, one row per line — NOT appended at end-of-file
  (append-to-EOF and insert-before-a-trailing-sentinel are the same git location for
  both branches and always conflict; RS-007 Q1). Sorted insertion places concurrent
  additions in distinct, non-adjacent regions.
- **Distinct-domain-prefix precondition.** The clean-merge guarantee holds only when
  each concurrent workstream owns a **distinct** claimed domain prefix, so its new
  ids sort into a distinct region. **Same-domain** concurrent additions are an
  accepted degradation to an ordinary human PR conflict — the tooling must **NOT**
  auto-union them (a `merge=union` `.gitattributes` driver is deliberately **not
  adopted**: it interleaves rows out of sort order, breaking REQ-WS-015's
  deterministic sort). Default recorded, per the sdd-plan Open Question.

See `docs/spec/ws-ids.md` for the full merge-safe write contract.

### Step 6: File Size Monitoring

After writing to any category file, check its line count. If the file exceeds 300 lines:
- Inform the user: "{file} is at {N} lines — recommend splitting"
- Propose a split (e.g., `auth.md` -> `auth-login.md` + `auth-permissions.md`)
- If approved: create the new files and move requirements **verbatim — IDs are permanent** (`REQ-AUTH-007` stays `REQ-AUTH-007`; never renumber or assign a new domain prefix on a split)
- The split files **share the original domain prefix**: each keeps `domain: AUTH` in frontmatter, the Domain Prefixes table lists all files carrying the prefix, and the next-ID scan covers every file sharing the domain (see ID Assignment)
- Update index.md: one Files-table row per new file; update the Domain Prefixes table row to list all the prefix's files

### Step 7: Review

Present the requirements to the user. Ask:
- "Are any requirements missing?"
- "Are any requirements wrong or unclear?"
- "Are the priorities right?" (must vs should vs may)
- "Are there open questions we need to resolve before proceeding to design?"
- "Do any [needs-spike] items need research before we proceed?"

Iterate until the user approves. Set `status: Approved` in both the category file frontmatter and `index.md` when approved.

If `[needs-spike]` items remain, recommend invoking `sdd-research` before proceeding to specs. The user may choose to proceed anyway and resolve them during implementation.

## Updating Existing Requirements

When category files already exist under `docs/requirements/`:

1. Read the current files via `index.md`'s Files table
2. Identify where new requirements fit in the existing structure
3. Use the next available ID number in each domain (don't reuse deleted IDs)
4. If a requirement changes, update in place and add a `[Updated: YYYY-MM-DD]` tag
5. If a requirement is removed: delete it from the category file and mark `[Deprecated]` in `traceability.md` — never reuse the ID
6. Present a diff summary to the user for approval
7. Run the auto-maintenance steps (Step 5) after every change

## Transition

When approved, recommend the next step:
- If `[needs-spike]` items remain unresolved → suggest `sdd-research`
- Otherwise → suggest `sdd-specs`
