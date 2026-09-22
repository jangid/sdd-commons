---
domain: REQ
last_updated: 2026-09-22
status: Approved
research_refs: [RS-HARNESSP6-001, RS-PIPELINEOBSERVABILITY-001]
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

The search covers twenty-two phrasings: `deferred to`, `carried to`,
`queued for`, `re-raise in that cycle`, `next cycle`, `a later cycle`,
`successor`, `candidate`, `revisit`, `follow-up`/`follow-ups`,
`in a cycle that`,
`(?:needs|wants) a\b[^.\n]{0,60}\b(?:cycle|workstream)\b`, `owner:`,
three narrow cycle-name-as-destination forms —
`^\s*[-*]\s+(?:harness-)?p[0-9]+\b`, `\.\s+(?:harness-)?p[0-9]+\s*\.` and
`(?:harness-)?p[0-9]+\s+(?:candidate|lead|owner)` — and six ordinary backlog
markers `\btodo\b`, `\bbacklog:`, `\bopen item\b`, `\bparked\b`,
`\bremains? open\b`, `\bunfinished\b`. Two rows are deliberately narrowed
because their bare forms are citation vocabulary in this corpus: a bare
`harness-p<N>` token fires 11 times in scope (i), every one a citation, and a
bare `backlog` token fires 3 times there, likewise every one a citation — so
the cycle-name rows match only destination/owner positions and the backlog row
requires the label colon.

[Updated: 2026-09-20, harness-p6 — verify-stage review M2. Rows 17–22 were
added after the sixteen-row screen was shown to return zero on ordinary backlog
lines (`TODO:`, `Backlog:`, `Open item:`, `Parked until …`, `Remains open`,
`Unfinished:`). Each row was measured over all seven scopes before adding: the
six together add zero live occurrences and zero marker-satisfied hits to the
corpus as it stands, so their value is prospective. The spec's
§`## Out of Scope` Discipline carries the normative table.]

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
neither of which is a checked scope — re-confirmed 2026-09-20 after rows 17–22
landed: the checked scopes remain `docs/requirements/index.md` §Out of Scope and
the §Next Steps section of every path `docs/ws/*/verification.md` returns, and
this file is neither. The three new settled exclusions named by
RS-HARNESSP6-001 are each present with their reasoning.
[Priority: must]

### REQ-REQ-PIPELINEOBSERVABILITY-001: how an amendment lands — in place, dated, and marked once in each of the three places that record it
When a workstream changes a requirement, or a spec section, that an earlier
cycle approved, the change must land in exactly this way:
(a) **Requirement** — the body is edited **in place** under its existing id,
carrying `[Updated: YYYY-MM-DD]` and a `> **Amended YYYY-MM-DD**` note that
names the workstream, the trigger (research item or review finding) and the
Q-REQ that decided it; when another requirement is the authority for a wording,
the note points at that requirement and states **no verbatim sentence of its
own** — one authority per wording.
(b) **Spec** — the spec's **section of record** is edited in place with a
dated marker (`[Updated: YYYY-MM-DD]` or `**Amended YYYY-MM-DD**`), so a cold
reader of that section sees the current contract; the spec **may** add a
`§<Workstream> Amendment` section as the record of *why* — rationale pointing
at the section it changed — and **never the reverse**: an amendment section
that is the sole carrier of a contract while the section of record still reads
the old text is a defect. Consequently the **Spec cell of an `(amended)`
traceability row (c) must name the section of record** — `<file> §<section of
record>` — and may name the `§<Workstream> Amendment` section only as a
**second** reference after it; a Spec cell naming the amendment section alone
is the same defect seen from the matrix (requirements review round 5 M4).
(c) **Per-workstream traceability** — `docs/ws/<id>/traceability.md` carries
one row per amended id whose Requirement cell reads `<id> (amended)`; the
marker means "**this workstream changed the id and does not own it**" — the
owning workstream's row remains the id's row in the regenerated aggregate, the
marked row asserts only that the amendment is delivered by this workstream,
and no cell of a marked row is read as the id's completion state.
(d) **Index** — the Files table of `docs/requirements/index.md` annotates
**every** category file holding at least one amended id with those ids and the
date, and no other file: the annotated set is derived from the `(amended)` rows
of (c) and must equal them. A workstream's rewrite of an id it minted in the
current cycle is not an amendment and is not annotated.
(e) **Corpus sweep for binding statements** (Q-REQ-PO-AG) — any requirement or
amendment that introduces or changes a **binding statement** (a must / never /
only / exactly, a grammar rule, a parser rule, a token contract) lists, **in
its own text**, every existing sentence on the same subject in
`docs/requirements/**`, `docs/spec/**`, `plugins/sdd/skills/**` and
`plugins/sdd/agents/**`, found by a **stated, re-runnable grep**, and marks
each hit as **reconciled** (consistent as-is, with the reason) or **retired**
(added to a zero-count witness). Where a hit is in `plugins/**` or
`docs/spec/**` that the delta does not amend, the reconciliation names the
requirement that will amend it or states why it is consistent. Why: the
pipeline-observability requirements ran six review rounds because each round
bound a rule whose contrary the shipped corpus already stated somewhere the
delta never looked (round 6 C1: the `VERDICT:` line's position, contradicted
by four shipped texts) — the sweep makes "nowhere else says otherwise" a
listed claim rather than an assumption.
Observed defect: the pipeline-observability cycle annotated five of the nine
files holding its fifteen amended ids, carried three amendment notes on one
requirement each stating a different verbatim sentence, and had no rule for
which side of a spec the amendment lives on (requirements review iteration 3,
M1 and M2). (see RS-PIPELINEOBSERVABILITY-001 §Q3; Q-REQ-PO-AA.) Leaves
REQ-REQ-002 (index versioning), REQ-REQ-006 (auto-maintained index),
REQ-REQ-007 (traceability matrix) and REQ-WS-008 (per-ws row ownership)
consistent.
**Acceptance**: for the active workstream `<id>`, the command
`grep -o '^| REQ-[A-Z0-9-]* (amended)' docs/ws/<id>/traceability.md | sed 's/| //; s/ (amended)//' | while read r; do grep -l "^### $r:" docs/requirements/*/*.md; done | sort -u`
lists the same files, one per line, as
`grep -E '^\| (functional|integration|non-functional|configuration) \|.*amended' docs/requirements/index.md | grep -oE '\]\([a-z-]+/[a-z-]+\.md\)' | tr -d '()]' | sed 's|^|docs/requirements/|' | sort -u`
(for `pipeline-observability`: 9 files by the first and 5 by the second as
observed at requirements review round 4, before this requirement landed; the
current measured value is 9 and 9); every amended requirement
body holds both `[Updated:` and `**Amended` (`grep -c` over each ≥ 1); at the
specs gate, the Spec cell of every `(amended)` row names a section of record
first (`grep -c '(amended) | [a-z0-9-]*\.md §Pipeline-Observability Amendment |' docs/ws/pipeline-observability/traceability.md`
reads 0; today 15 — the cells the specs re-derivation rewrites), and each spec
file named in the Spec cell of an `(amended)` row holds a
dated marker in its section of record — `grep -c 'Updated: YYYY-MM-DD'` over
that file ≥ 1 — and no amendment section states a contract the section of
record lacks (decided by the specs review against this clause). For (e), a
derived set equality like (d)'s: the set of ids this workstream mints or
amends,
`grep -oE '^\| REQ-[A-Z0-9-]+' docs/ws/<id>/traceability.md | sed 's/^| //' | sort -u`
(the Requirement column, `(amended)` rows included — 36 today for
`pipeline-observability`: 21 new ids and 15 amended), equals the set of ids
whose body carries a sweep block or the exemption marker,
`awk '/^### REQ-/{id=$2; sub(/:$/,"",id)} /Corpus sweep \(REQ-REQ-PIPELINEOBSERVABILITY-001 \(e\)|^> no binding statement/{print id}' docs/requirements/*/*.md | sort -u`
(36 today), decided by writing both listings to files and `diff` printing
nothing — an amended id carries its block or marker inside its
`> **Amended` note, so the `awk` attributes it to the amended id's heading;
the exemption marker is the literal line prefix `> no binding statement`
followed by the reason, and it is legal only where the requirement or note
states no must / never / only / exactly, grammar, parser or token rule of its
own (Q-REQ-PO-AH). Each block's stated command, re-run with `-l` in place of
`-n`, lists exactly the files the block names (plus the requirement's own
file and the index). Two temp-copy witnesses: (1) delete one sweep block
from any body — the second listing loses that id and `diff` prints it, so
the obligation is decided by the equality, not by which blocks happen to
exist; (2) add one sentence matching a block's pattern to any swept file —
the block's re-run lists a file the block does not name, the listed
reconciliation is then false and the block must be re-derived.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG, 2026-09-22)** over the `(amended)` marker's meaning —
a listing grep over `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
Command: `grep -rnE '\(amended\)|does not own it' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
`docs/requirements/traceability.md` (the fifteen aggregate rows) — reconciled,
regenerated from `docs/ws/pipeline-observability/traceability.md` whose header
restates (c) by citation; `docs/requirements/index.md` Files table
annotations — reconciled, they are (d)'s derived set; the seven category files
whose amendment notes say `(amended)` in prose — reconciled, each note points
at its authority and states no marker meaning; `docs/spec/pipeline-observability.md`
(the amendment table naming the amended ids) — reconciled, it lists ids and
defines no marker; `plugins/sdd/skills/**` and `plugins/sdd/agents/**` — no
hit (the `requirements` skill's Step 5 describes the per-ws row and never the
marker; a future skill sentence on the marker must cite (c)).
[Priority: must]
`[Updated: 2026-09-22]` — requirements review round 5 M4(b): the Spec cell of
an `(amended)` row names the section of record, the amendment section at most
second. Requirements review round 6 M2 and the operator's new clause
(Q-REQ-PO-AG): the 9/5 baseline is dated to round 4 and the current 9/9
measured; clause (e), the corpus sweep for binding statements, is added with
its acceptance and applied to every binding statement of this delta.
Requirements review round 7 M1/M2 (Q-REQ-PO-AH): (e)'s obligation is decided
by the derived set equality above, and the sweep block or the
`> no binding statement` marker now sits on all 36 ids the workstream mints
or amends.
