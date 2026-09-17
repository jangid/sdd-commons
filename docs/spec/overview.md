---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-CTX-001
  - REQ-CTX-002
  - REQ-COMPAT-001
  - REQ-COMPAT-002
  - REQ-CFG-001
  - REQ-MIG-015
  - REQ-STALE-001
---

# Overview: SDD Artifact Structure

## Context

The SDD workflow produces artifacts across seven phases. In v1, these artifacts
live in flat structures that grow unboundedly: a single `requirements.md`, flat
research files, and plan files that accumulate changelogs and removed-task
markers. v2 restructures all artifacts for bounded file sizes, traceable
cross-references, and AI-context-friendly document sizes. v3 adds behavioral
conventions — chunk-close review, Q-IMPL deviation protocol, per-milestone plan
support, and cross-spec consistency — without changing the artifact layout.

This spec establishes the shared principles, directory layout, and version
conventions that all other specs build on.

## Design

### Directory Layout

```
docs/
  .sdd-version                    # Plain text: "2", "3", or "4" (sole layout gate)
  research/
    index.md                      # Auto-maintained research index
    RS-001-{topic}/
      findings.md                 # Main research document
      prototype/                  # Optional supporting files
    RS-002-{topic}/
      findings.md
  requirements/
    index.md                      # Versioned requirements index
    traceability.md               # RTM: requirements → specs → tests → status
    functional/
      {domain}.md                 # e.g., auth.md, billing.md
    non-functional/
      {concern}.md                # e.g., performance.md, security.md
    integration/
      {system}.md                 # e.g., stripe-api.md
    configuration/
      {area}.md                   # e.g., env-config.md
  spec/
    overview.md                   # This file (unchanged from v1)
    {feature}.md                  # Feature specs (unchanged from v1)
  plan.md                         # Active plan — lean, no history
  plan-history/
    {YYYY-MM-DD}-{reason}.md      # Archived plans with changelogs
  verification.md                 # Verification report (unchanged from v1)
```

### Version Marker

`docs/.sdd-version` is a plain text file containing a single integer
indicating the SDD process version. Current valid values:

- `2` — v2 artifact layout (split requirements, RS-NNN research, archive
  pattern, traceability matrix)
- `3` — v2 layout plus v3 process conventions (chunk-close review, Q-IMPL
  deviation protocol, per-milestone plan support, cross-spec consistency
  pass, plan vocabulary using `### Chunk N:` headers for work units)
- `4` — v4 multi-workstream layout: execution artifacts (`plan.md`,
  `verification.md`, `kickoff.md`, `plan-history/`, per-ws `traceability.md`)
  move under `docs/ws/<id>/`, while the shared corpus (`research/`,
  `requirements/`, `spec/`, aggregated `traceability.md`) stays at top level;
  workstream-prefixed IDs; phase detection becomes a function of
  `(repo, workstream)`; branch-per-workstream → PR-to-`main` integration. The
  marker is the **sole** layout gate — see `ws-layout.md`, `ws-migration.md`,
  `ws-ids.md`.

If the file is missing, assume v1 (backward compatible). All SDD skills read
this file on phase detection to determine which conventions apply. `docs/.sdd-version`
is the **sole** layout gate: marker `3` (or earlier) selects the flat layout
described here, marker `4` selects the per-workstream `docs/ws/<id>/` layout
(`sdd-migrate` performs the one-time v3→v4 flip). A skill under marker `3` never
reads `docs/ws/`; a skill under marker `4` never reads flat `docs/plan.md` /
`docs/verification.md`.

The marker tracks SDD process version — not just artifact layout — because v3
introduces behavioral conventions (not layout changes) that operators need to
know about. Skills read this file to determine which mechanisms are active.

v3 is backward compatible with v2: projects on v2 continue to work without
migration. v3 mechanisms gracefully degrade when v3 conventions aren't present
(chunk-close is inactive without `### Chunk N:` headers; per-milestone logic
activates only when per-milestone files exist; Q-IMPL entries accumulate on
demand).

**Why a separate file instead of frontmatter in an existing artifact**: The
version marker must be detectable before reading any specific artifact. A
standalone file avoids chicken-and-egg problems (which file do you read to find
the version?).

### Shared Conventions

#### File Size Budget

No single artifact file should exceed 300 lines. This ensures any file can be
loaded into an AI session alongside specs and code without consuming excessive
context. Exceptions:
- Index files and `traceability.md` are exempt but should be kept concise.
- `docs/plan.md` is naturally bounded by the archive pattern (completed
  milestones are summarized, not preserved in full).

**Why 300 lines**: Research found that LLMs produce better output with focused,
detailed documents rather than large dumps. 300 lines is ~10KB of markdown —
comfortably fits within a single context window alongside implementation code.

#### Self-Contained Files

Each artifact file must be understandable in isolation. Cross-references use
explicit IDs (`REQ-AUTH-001`, `RS-003`) rather than prose like "see the auth
section in requirements." This allows skills to load only the files relevant to
the current task.

#### Format

All artifacts are plain Markdown with YAML frontmatter. No binary files, no
tool-specific formats. This ensures:
- Git diffs are human-readable
- Any text editor can open them
- AI assistants can read/write them without special tooling

#### Frontmatter Fields

Every artifact file must include at minimum:
- `status` — lifecycle state (Draft, Approved, Complete, etc.)
- `last_updated` — ISO date (YYYY-MM-DD), used for staleness detection

Additional fields are spec-specific (e.g., `version` in requirements index,
`requires` in spec files).

### Staleness Detection Model

v2 changes staleness detection from comparing individual files to comparing
against index files:

```
research/index.md → requirements/index.md → spec/*.md → plan.md → verification.md
         (last_updated)    (last_updated)
```

The key change: `requirements/index.md`'s `last_updated` is bumped whenever any
category file changes. Downstream skills compare against this single date rather
than scanning all category files.

**Why index-based**: In v1, staleness compares one file against one file. With
split requirements, comparing against N files adds complexity. The index acts as
a single source of truth for "when did requirements last change?"

### Plan Vocabulary

v3 distinguishes **chunks** (implementation work units, ~5-15 hours) from
**delivery milestones** (M1, M2, etc., delivery groupings). Single-milestone
plans use `### Chunk N:` headers under a `## Chunks` section. Multi-milestone
projects use per-milestone plan files (see milestone-plans.md) where each
per-milestone file contains chunks.

v2 plans using `### M N:` as work-unit headers are still readable but won't
activate chunk-close review (which triggers on `### Chunk N:` boundaries). The
v2→v3 migration renames these to chunk format, preserving original numbering
(M1 → Chunk 1, M2 → Chunk 2).

### v3 Behavioral Additions

Beyond the v2 artifact layout, v3 adds:

- **Chunk-close review** — structured 4-check checklist at chunk boundaries
  during implementation (see chunk-close-review.md)
- **Q-IMPL deviation protocol** — three-tier classification for implementation
  decisions diverging from spec (see deviation-protocol.md)
- **Per-milestone plan support** — optional structure for multi-milestone
  projects (see milestone-plans.md)
- **Cross-spec consistency pass** — type reference validation between specs
  (see cross-spec-consistency.md)

These are documented in their own specs. The overview lists them as the answer
to "what does v3 add" without restating their designs.

### v5 Harness Hardening

The harness-hardening cycle (RS-008) adds no artifact type and no layout
change. It hardens the orchestrated loop with session-scoped and derived caps,
a structured `RETURN:` block and repair packet on dispatches, machine-parseable
gate tokens — `VERDICT:` (review), `CHUNK_VERDICT:` (chunk verifier), `SCOPE:`
(write-scope check) — a fresh read-only chunk-close verifier that is a second
executor of the existing chunk-close layer (the four verification layers are
unchanged), and a declared write scope per dispatch. Architecturally the new
procedure text lives in `skills/sdd-orchestrate/references/` as skill text —
`return-contract.md`, `write-scope.md`, `v4-workstreams.md` (the LINT
deliverable, REQ-LINT-007) and `loop-control.md` (added by the Chunk 5 minor
replan to land `SKILL.md` under the size target, Q-IMPL-073) — with stubs in
`SKILL.md`, so the entry point keeps reading as a table of contents; the only
durable project-side trace is the bounded circuit-break checkpoint in the plan's
existing blocked-task note. Designs: `harness-loop-control.md`,
`harness-return-contract.md`, `harness-chunk-verifier.md`,
`harness-write-scope.md`, `skill-lint-v5.md`.

### ID Namespaces

v2/v3 use three ID namespaces; the numeric counter is global across the project
(or per domain for requirements):

| Namespace | Format (v2/v3) | Example | Scope |
|-----------|--------|---------|-------|
| Research | `RS-NNN` | `RS-001` | Global across project |
| Requirements | `REQ-{DOMAIN}-{NNN}` | `REQ-AUTH-001` | Unique per domain, globally unique |
| Implement deviation | `Q-IMPL-NNN` | `Q-IMPL-001` | Global sequential across specs |
| Specs | filename-based | `auth-flow.md` | `docs/spec/` directory |

**Why domain-based requirement IDs instead of type-based**: `REQ-AUTH-001` tells
you both what it's about and where to find it (`functional/auth.md` or similar).
`REQ-F-001` tells you only the type, requiring a search to locate it.

#### v4: Workstream-Prefixed IDs

Under marker `4`, downstream artifact IDs carry a `<WS>` **workstream segment**
inserted **before** the numeric counter, and the counter becomes a **per-workstream**
sequence (per `domain+workstream` for requirements). This eliminates the ID-allocation
race between concurrent workstreams — each scans only its own workstream's ids:

| Namespace | Format (marker `4`) | Example |
|-----------|---------------------|---------|
| Research | `RS-<WS>-NNN` | `RS-ISSUE42-001` |
| Requirements | `REQ-<DOMAIN>-<WS>-NNN` | `REQ-AUTH-ISSUE42-001` |
| Implement deviation | `Q-IMPL-<WS>-NNN` | `Q-IMPL-ISSUE42-003` |

`NNN` is always parsed **after** the `<WS>` token (and, for requirements, after the
`<DOMAIN>` token) and stays zero-padded to 3 digits. Specs remain filename-based (no
`<WS>` segment — specs are a shared corpus). The `<WS>` segment applies **only under
marker `4`**; legacy bare ids from a v2/v3 corpus remain valid and are treated as the
reserved `default` workstream — they are **not** remapped by the v3→v4 migration. Full
contract: `ws-ids.md` (REQ-WS-009, REQ-WS-011, REQ-WS-012).

## Verification

### Manual
- Inspect the directory layout after migration or fresh project setup
- Confirm `docs/.sdd-version` contains the current version (`2`, `3`, or `4`)
- Confirm each artifact file has the required frontmatter fields
- Confirm v3 projects use `### Chunk N:` plan vocabulary

### Acceptance Criteria
- [ ] All artifact files use plain Markdown with YAML frontmatter (REQ-COMPAT-001)
- [ ] No artifact file exceeds 300 lines except index/traceability (REQ-CTX-001)
- [ ] Each file is self-contained with ID-based cross-references (REQ-CTX-002)
- [ ] `docs/.sdd-version` exists and contains the version number (REQ-CFG-001)
- [ ] Version marker valid values are `2`, `3`, and `4` (REQ-CFG-001, REQ-WS-023)
- [ ] Staleness detection uses `index.md` dates, not individual file scans (REQ-STALE-001)
- [ ] v2 projects work without migration; v3 mechanisms degrade gracefully (REQ-COMPAT-002)
- [ ] Overview documents plan vocabulary convention (REQ-MIG-015)
- [ ] Overview documents version marker semantics as process version (REQ-MIG-015)
- [ ] Overview lists v3 behavioral additions (REQ-MIG-015)
