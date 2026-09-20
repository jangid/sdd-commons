---
domain: REQ
last_updated: 2026-09-20
status: Approved
research_refs: [RS-HARNESSP6-001]
---

# Requirements: Requirements Structure

## Overview

How requirements are organized, versioned, and traced across the SDD lifecycle.

## Requirements

### REQ-REQ-001: Requirements directory layout
Requirements must be organized into `docs/requirements/` with the following
subdirectories:
- `functional/` — one file per feature domain (e.g., `auth.md`, `billing.md`)
- `non-functional/` — one file per concern (e.g., `performance.md`, `security.md`)
- `integration/` — one file per external system (e.g., `stripe-api.md`)
- `configuration/` — one file per configuration area (e.g., `env-config.md`)
[Priority: must]

### REQ-REQ-002: Requirements index with versioning
`docs/requirements/index.md` must contain:
- YAML frontmatter with `version` (semver `major.minor`), `status`
  (Draft/Approved), and `last_updated` fields
- A listing of all requirement files with their status and requirement count
- A reference to `docs/requirements/traceability.md`

The version must be bumped on every change:
- Major bump when requirements are added, removed, or fundamentally changed
- Minor bump for clarifications, rewording, or priority changes
[Priority: must]

### REQ-REQ-003: Requirement ID scheme
Requirements must use the ID format `REQ-{DOMAIN}-{NNN}` where `{DOMAIN}` is an
uppercase short name matching the file's topic (e.g., `AUTH`, `PERF`, `STRIPE`)
and `{NNN}` is a zero-padded sequential number within that domain. IDs must be
unique across the entire requirements set.
[Priority: must]

### REQ-REQ-004: Per-file metadata
Each requirements category file must have YAML frontmatter containing:
- `domain` — the domain prefix used in IDs (e.g., `AUTH`)
- `last_updated` — date of last modification
- `status` — Draft or Approved
[Priority: must]

### REQ-REQ-005: File size limit
Each requirements category file should stay under 300 lines. When a file
approaches this limit, the skill should recommend splitting it into more
specific domain files.
[Priority: should]

### REQ-REQ-006: Auto-maintained index
The `sdd-requirements` skill must update `docs/requirements/index.md`
automatically whenever requirements are created, updated, or removed. The user
should not need to manually edit the index.
[Priority: must]

### REQ-REQ-007: Traceability matrix
A separate `docs/requirements/traceability.md` file must maintain a matrix
mapping requirement IDs to spec files, test files, and implementation status.
The format must be a markdown table. This file must be referenced from
`index.md` and updated by `sdd-specs` (when specs are written), `sdd-implement`
(when tests/code are written), and `sdd-verify` (when verification completes).
[Priority: must]

### REQ-REQ-HARNESSP6-001: §Out of Scope holds settled exclusions with reasoning, never deferrals
`docs/requirements/index.md` §Out of Scope must record every won't-do as a
**settled exclusion with its reasoning**, and must not hold an entry phrased as
deferred, carried, or queued to a next or later cycle. An entry whose work has
since been done or has become moot is marked closed with its date and evidence
rather than deleted, so the closure stays auditable; an entry superseded by a
shipped requirement is replaced by a pointer to that requirement. The same rule
binds a cycle's `verification.md` §Next Steps, which must contain no item
phrased as carried to a later cycle. A finding too large to fix inside the cycle
triggers a **replan**, not a successor workstream. (workstream `harness-p6`;
kickoff §Scope item 9 and §Decided at DISCUSS — "§Out of Scope is swept, not
grown"; RS-HARNESSP6-001 §Deferral-Backlog Sweep)
**Acceptance** (widened at the red round, R1/R2; the spec's
§`## Out of Scope` Discipline carries the normative table): a case-insensitive
search over (i) `docs/requirements/index.md` §Out of Scope and (ii) the
§Next Steps section of **every** path the glob `docs/ws/*/verification.md`
returns — the glob is the scope, enumerated at run time; a run that walks a
hand-picked subset has not run the check, and a conforming run reports one row
per returned path, rows-walked equal to paths-returned, both derived from the
same run.

The search covers sixteen phrasings: `deferred to`, `carried to`, `queued for`,
`re-raise in that cycle`, `next cycle`, `a later cycle`, `successor`,
`candidate`, `revisit`, `follow-up`/`follow-ups`, `in a cycle that`,
`(?:needs|wants) a\b[^.\n]{0,60}\b(?:cycle|workstream)\b`, `owner:`, and
three narrow cycle-name-as-destination forms —
`^\s*[-*]\s+(?:harness-)?p[0-9]+\b`, `\.\s+(?:harness-)?p[0-9]+\s*\.` and
`(?:harness-)?p[0-9]+\s+(?:candidate|lead|owner)`. A bare `harness-p<N>` token
is deliberately **not** a phrase: measured, it fires 11 times in scope (i) alone,
every one a citation rather than a deferral.

The two halves of the check carry different weight and the acceptance states
both honestly. **Marker adjacency is exact**: a match does not count as live
when its own line `L`, or the line `L-1` immediately preceding it, carries a
bracketed dated marker matching
`(\*\*\[|_\()(?i:superseded|closed|struck)[^\]\)]*20[0-9]{2}-[0-9]{2}-[0-9]{2}`;
only `L` and `L-1` are examined and nothing else. Every annotated item therefore
carries its own adjacent marker; a block-level marker covering several items
does not satisfy this clause. **Phrase coverage is a best-effort screen** over
the backlog vocabulary observed in this corpus, not an oracle — a deferral
written in vocabulary no cycle has used yet passes it, and a reviewer still
reads the section.

Prose in §Q-REQ Resolutions recording what a **closed** cycle decided is outside
the scopes and is not examined; so is this requirement's own text and the spec's,
neither of which is a checked scope. The three new settled exclusions named by
RS-HARNESSP6-001 are each present with their reasoning.
[Priority: must]
