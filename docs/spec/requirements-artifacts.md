---
status: Approved
last_updated: 2026-09-20
requires:
  - REQ-REQ-001
  - REQ-REQ-002
  - REQ-REQ-003
  - REQ-REQ-004
  - REQ-REQ-005
  - REQ-REQ-006
  - REQ-REQ-007
  - REQ-STALE-001
  - REQ-STALE-002
  - REQ-SKILL-003
  - REQ-REQ-HARNESSP6-001
---

# Requirements Artifacts

## Context

In v1, all requirements live in a single `docs/requirements.md`. This file
grows unboundedly as projects evolve — requirements accumulate, removed ones
get `[Removed: ...]` markers, and the file consumes excessive AI context even
when only one domain is relevant.

v2 splits requirements by domain into category directories, adds a versioned
index for staleness detection, and introduces a separate traceability matrix.

## Design

### Directory Layout

```
docs/requirements/
  index.md                      # Versioned index (auto-maintained)
  traceability.md               # RTM: requirement → spec → test → status
  functional/
    {domain}.md                 # One file per feature domain
  non-functional/
    {concern}.md                # One file per quality concern
  integration/
    {system}.md                 # One file per external system
  configuration/
    {area}.md                   # One file per config area
```

**Why four subdirectories instead of flat**: The subdirectory names act as type
tags. When the `sdd-specs` skill needs to find performance constraints, it
knows to look in `non-functional/`. When `sdd-implement` needs API integration
details, it looks in `integration/`. This avoids scanning all files.

**Why not deeper nesting** (e.g., `functional/auth/login.md`): One level of
nesting is enough. If a domain file approaches 300 lines, split it into
sibling files (`auth-login.md`, `auth-permissions.md`), not deeper directories.
Flat within each category keeps paths short and predictable.

### Category File Format

Each category file follows this structure:

```markdown
---
domain: AUTH
last_updated: YYYY-MM-DD
status: Draft | Under Review | Approved
---

# Requirements: Authentication

## Overview
Brief context for this domain — what it covers and why.

## Requirements

### REQ-AUTH-001: User login via OAuth2
The system must authenticate users through OAuth2 providers.
[Priority: must]

### REQ-AUTH-002: Session expiry
User sessions should expire after 30 minutes of inactivity.
[Priority: should]

### REQ-AUTH-003: Remember me option
The system may offer a "remember me" checkbox extending sessions to 30 days.
[Priority: may]
```

**Conventions**:
- `domain` in frontmatter is the uppercase prefix used in IDs for this file.
- Each requirement is an h3 heading with format `### REQ-{DOMAIN}-{NNN}: {title}`.
- Priority (must/should/may) is stated in the requirement text, not the ID.
- One requirement per heading — no bundling multiple behaviors.
- Requirements are testable statements — if you can't write a verification, rewrite.

### Requirement ID Scheme

Format: `REQ-{DOMAIN}-{NNN}`

- `{DOMAIN}` is an uppercase short name (2-8 chars) matching the file's topic.
  Examples: `AUTH`, `PERF`, `STRIPE`, `ENVCFG`.
- `{NNN}` is a zero-padded 3-digit number, sequential within the domain.
- IDs must be globally unique — no two domains may produce the same full ID.
  The domain prefix naturally prevents collisions.

**Domain prefix selection**: When creating a new category file, the skill
chooses the domain prefix based on the topic and checks that it doesn't collide
with existing prefixes. The prefix must be listed in `index.md`.

**ID assignment**: The skill scans the target file for the highest existing
`NNN` and increments. New files start at `001`.

### Requirements Index

`docs/requirements/index.md` is the single source of truth for requirements
metadata and staleness detection:

```markdown
---
version: 1.0
status: Draft | Under Review | Approved
last_updated: YYYY-MM-DD
---

# Requirements Index

## Summary
One paragraph: what the project is and what this requirements set covers.

## Files

| Category | File | Domain | Status | Count | Last Updated |
|----------|------|--------|--------|-------|--------------|
| Functional | functional/auth.md | AUTH | Approved | 12 | 2026-04-28 |
| Functional | functional/billing.md | BILL | Draft | 5 | 2026-04-28 |
| Non-functional | non-functional/performance.md | PERF | Approved | 3 | 2026-04-25 |
| Integration | integration/stripe-api.md | STRIPE | Approved | 8 | 2026-04-20 |

## Domain Prefixes

Reserved prefixes to prevent collisions:

| Prefix | File | Description |
|--------|------|-------------|
| AUTH | functional/auth.md | Authentication and authorization |
| BILL | functional/billing.md | Billing and payments |
| PERF | non-functional/performance.md | Performance constraints |
| STRIPE | integration/stripe-api.md | Stripe API integration |

## See Also
- [Traceability Matrix](traceability.md)
```

**Versioning rules**:
- `version` uses semver `major.minor`.
- Major bump: requirements added, removed, or fundamentally changed.
- Minor bump: clarifications, rewording, priority changes.
- The skill bumps the version and `last_updated` on every change.

**Why a Files table**: It gives any skill a quick scan of all requirement
files without traversing the directory tree. The Count column helps detect
files approaching the 300-line limit.

### Traceability Matrix

`docs/requirements/traceability.md` maps requirements through the full
lifecycle:

```markdown
---
last_updated: YYYY-MM-DD
---

# Traceability Matrix

| Requirement | Spec | Test | Implementation | Verified |
|-------------|------|------|----------------|----------|
| REQ-AUTH-001 | spec/auth-flow.md | tests/test_auth.py | src/auth.py | pass |
| REQ-AUTH-002 | spec/auth-flow.md | tests/test_session.py | src/session.py | pass |
| REQ-PERF-001 | spec/overview.md | tests/test_perf.py | — | fail |
| REQ-STRIPE-001 | spec/payments.md | — | — | — |
```

**Update responsibilities**:
- `sdd-specs` fills the Spec column when writing specs.
- `sdd-implement` fills Test and Implementation columns when writing code.
- `sdd-verify` fills the Verified column during verification.
- `sdd-requirements` creates the initial rows (Requirement column only, rest
  blank).

**Why a separate file instead of embedding in index.md**: The traceability
matrix grows with every requirement and gets updated by four different skills.
Keeping it separate prevents index.md churn and keeps concerns separated.

### Auto-Maintenance Behavior

When the `sdd-requirements` skill creates, updates, or removes requirements:

1. Write the change to the appropriate category file.
2. Update the category file's `last_updated` in frontmatter.
3. Update `index.md`: bump version, bump `last_updated`, update the Files
   table (count, status, date).
4. Update `traceability.md`: add rows for new requirements, mark removed
   requirements as `[Deprecated]`.

**Removed requirements**: In v2, removed requirements get `status: Deprecated`
in the traceability matrix and are removed from the category file. The ID is
never reused. This replaces v1's `[Removed: date — reason]` inline markers
that caused bloat.

**Why not just delete**: The traceability matrix preserves the record that the
requirement once existed and was deprecated. This is important when specs or
tests reference it — the reference becomes traceable to a deliberate removal
rather than a mysterious broken link.

### Staleness Detection

#### Index-based (REQ-STALE-001)

All downstream skills compare against `index.md`'s `last_updated`:
- If `index.md` is newer than `docs/spec/*.md` → specs are stale.
- If `index.md` is newer than `docs/plan.md` → plan is stale.

This replaces comparing against a single `requirements.md`.

#### Research-to-requirements (REQ-STALE-002)

When `sdd-requirements` starts, it checks:
1. Scan `docs/research/index.md` for entries with `status: Complete`.
2. Compare the newest research date against `requirements/index.md`'s
   `last_updated`.
3. If research is newer → inform the user: "Research RS-NNN completed on
   {date} — requirements may need updating."

This is advisory, not blocking. The user decides whether the new research
affects requirements.

### `## Out of Scope` Discipline (REQ-REQ-HARNESSP6-001)

[Added 2026-09-20, harness-p6 — REQ-REQ-HARNESSP6-001]

`docs/requirements/index.md` §Out of Scope records every won't-do as a **settled
exclusion with its reasoning**. It must not hold an entry phrased as deferred,
carried, or queued to a next or later cycle. A section that accumulates
deferrals is a backlog wearing a scope section's name: it makes each cycle's
boundary unfalsifiable and structurally guarantees a successor cycle.

**The four dispositions.** Every entry is exactly one of:

| Disposition | Shape |
|---|---|
| settled exclusion | the entry states the won't-do **and its reasoning** — why it is not worth doing, not when it might be |
| closed | its work has since been done or has become moot: marked closed **with its date and evidence**, not deleted, so the closure stays auditable |
| superseded | replaced by a pointer to the requirement that shipped it |
| in scope | removed from the section because a requirement now carries it |

**The same rule binds `verification.md` §Next Steps.** A cycle's §Next Steps must
contain no item phrased as carried to a later cycle. A finding too large to fix
inside the cycle triggers a **replan**, not a successor workstream.

**The scope is an enumeration, not a hand-list (REQ-REQ-HARNESSP6-001, red R2).**
The §Next Steps half binds the §Next Steps section of **every**
`docs/ws/*/verification.md` the glob returns — the glob is the scope, evaluated
at run time, and a run that walks a hand-picked subset of workstreams has not
run the check. (Marker `3`: the flat `docs/verification.md`, which is the same
enumeration over a one-element set.) Each section is delimited by its heading
and the next heading at the same or higher level — the same delimitation
§Out of Scope uses, so one extractor serves both scopes. A conforming run
reports **one row per path the glob returned**, including the rows that return
zero; the count of rows walked must equal the count of paths the glob returned,
and both sides of that equality are derived from the same run.

**Marker adjacency is decided exactly; phrase coverage is a screen
(red R1).** The mechanism has two halves and they carry different weight, so
the spec states them separately rather than claiming one guarantee for both.

*Half one — exact.* Given an occurrence at line `L`, whether a bracketed dated
marker sits **at or above** it is decided mechanically and completely: only `L`
itself and the line `L-1` immediately preceding it are examined, and nothing
else. There is no judgement in this half and no case it cannot decide.

*Half two — best effort.* Whether a line *is* a deferral is decided by a
case-insensitive search for the phrasings below. That list is a **screen over
observed backlog vocabulary**, not an oracle: it was widened to the shapes real
§Next Steps backlogs in this repo actually use, measured against the corpus, and
a deferral written in vocabulary no cycle has used yet will pass it. A reviewer
still reads the section; the screen is what makes a *regression* cheap to catch,
not what makes the section provably clean.

| # | Phrase (case-insensitive) | Shape it catches |
|---|---|---|
| 1 | `deferred to` | explicit deferral |
| 2 | `carried to` | explicit carry |
| 3 | `queued for` | explicit queue |
| 4 | `re-raise in that cycle` | re-raise instruction |
| 5 | `next cycle` | named successor, generic |
| 6 | `a later cycle` | named successor, generic |
| 7 | `successor` (covers `successor workstream`, `successor cycle`) | the spec's own forbidden-outcome vocabulary |
| 8 | `candidate` | "is the harness-p4 candidate" |
| 9 | `revisit` | "revisit … on cohesion grounds" |
| 10 | `follow-up` / `follow-ups` | "two follow-ups remain" |
| 11 | `in a cycle that` | "in a cycle that can edit both" |
| 12 | `(needs\|wants) a …(cycle\|workstream)` — `(?:needs\|wants) a\b[^.\n]{0,60}\b(?:cycle\|workstream)\b` | "needs a cycle that can amend Approved specs" |
| 13 | `owner:` | an item assigned to a later owner |
| 14 | a §Next Steps bullet **opening** with a cycle name — `^\s*[-*]\s+(?:harness-)?p[0-9]+\b` | "- p5 telemetry (reader): …" |
| 15 | a sentence whose whole content is a cycle name — `\.\s+(?:harness-)?p[0-9]+\s*\.` | "…nothing keeps them so. harness-p4." |
| 16 | a cycle name used as an assignment — `(?:harness-)?p[0-9]+\s+(?:candidate\|lead\|owner)` | "**V14 (harness-p4 lead)**" |
| 17 | `todo` — `\btodo\b` | "- TODO: bump the spec's `last_updated` when a later pass touches it." |
| 18 | `backlog:` — `\bbacklog:` | "- Backlog: fold the liveness screen into `sdd-gc.py`." |
| 19 | `open item` — `\bopen item\b` | "- Open item: the hunk-level check is not built." |
| 20 | `parked` — `\bparked\b` | "- Parked until someone reworks the reader." |
| 21 | `remain(s) open` — `\bremains? open\b` | "- Remains open; handle when the corpus is next touched." |
| 22 | `unfinished` — `\bunfinished\b` | "- Unfinished: L2 recall was never measured." |

**Rows 17–22 are ordinary backlog vocabulary (added 2026-09-20, harness-p6 —
verify-stage review M2).** The sixteen-row screen was tuned to the deferral
shapes this corpus had already written and therefore missed the vocabulary any
repository uses for a backlog. Each row was measured against the seven scopes
before it was added, and together they cost **zero** new live occurrences and
zero new marker-satisfied hits: rows 17 and 19–22 match nothing anywhere in
scope today, so their entire value is prospective. **Row 18 is narrowed to
`backlog:`** for the same reason rows 14–16 are narrowed: a bare `backlog`
token fires three times in `docs/requirements/index.md` §Out of Scope, every one
of them a citation of a research section whose name contains the word, not a
deferral. The colon restricts the match to the label position a backlog item is
actually written in.

**Rows 14–16 are deliberately narrow.** A bare `harness-p<N>` token is *not* a
phrase: measured over the two scopes it fires 11 times in
`docs/requirements/index.md` §Out of Scope alone, every one of them a citation —
a file path, a workstream name, an evidence reference. Rows 14–16 therefore
match a cycle name only where it is used as a **destination or an owner**, which
is the shape a deferral takes. That narrowing is the reason the screen can be
widened this far without the section's own prose reading as live.

Every occurrence the screen finds is reported **live** unless a bracketed dated
marker of the form below sits **at or above** it — on the occurrence's own line
`L`, or on the line `L-1` immediately preceding it, and nowhere else
[**superseded, 2026-09-21, packaging** — the `L`/`L-1` window is replaced by
REQ-DOCS-PACKAGING-003's **item-scoped** rule stated in §Item-Scoped Liveness
(2026-09-21, packaging) below; `project-docs.md` §Carried Documentation Repairs
is the contract. The paragraphs from here to §Item-Scoped Liveness are retained
as the superseded text they are, not rewritten in place, so the two rules stay
comparable]:

```
(\*\*\[|_\()(?i:superseded|closed|struck)[^\]\)]*20[0-9]{2}-[0-9]{2}-[0-9]{2}
```

**The anchor is the matched phrase, not the entry block.** Liveness is
evaluated per *occurrence*: the checker finds a phrase at line `L` and looks
only at `L` and `L-1`. A marker anywhere below the occurrence, or further above
it than `L-1`, does not count, however plainly a human reader would attach it to
the same entry. The cost is that an entry wrapping over several lines must carry
its marker on or above the wrapped line that holds the phrase; the benefit is
that attribution needs no block parser and no judgement about where an entry
begins and ends.

**Not the plan-archival strike rule.** `docs/spec/plan-management.md`
§Resolved `## Open Questions` Entries Are Struck at Archival defines a superficially
similar marker rule with a deliberately **different** anchor: it is anchored on
the **entry block** and accepts a marker *below* the entry. The two govern
disjoint scopes — this rule reads `docs/requirements/index.md` §Out of Scope and
`verification.md` §Next Steps for deferral phrasings; that one reads archived
`plan-history/` §Open Questions for answered entries — and neither regex is ever
applied to the other's scope. An implementer must not borrow that rule's
below-the-entry placement here, nor this rule's `L` / `L-1` semantics there.

Two consequences follow, and both are deliberate. First, **every** annotated
item carries its **own adjacent** marker — a block-level marker introducing
several items does not satisfy the rule, because a reader scanning one line
cannot see it and a mechanical check cannot attribute it. Second, prose in
§Q-REQ Resolutions that records what a **closed** cycle decided is outside the
two scopes and is not examined: recording that a past cycle deferred something
is history, not a live deferral.

**Why a mechanical rule and not a review instruction.** A "don't write
deferrals" instruction is unfalsifiable at a gate; an adjacent-marker rule is a
grep an operator can run and a reviewer can reproduce, which is the property that
makes a terminal cycle's closing condition checkable at all.

#### Item-Scoped Liveness (2026-09-21, packaging)

**The liveness rule is item-scoped** (REQ-DOCS-PACKAGING-003;
`project-docs.md` §Carried Documentation Repairs). A marker suppresses **only
the item it belongs to**. An *item* is

1. the bullet's own line — `-`, `*`, or `N.`, at any indentation; plus
2. its continuation lines — every following line that is neither a new bullet
   nor blank; plus
3. the standalone marker lines **immediately preceding** the bullet, if any: a
   non-bullet, non-blank line that matches the marker regex and abuts the
   bullet (directly, or through a run of such lines) introduces or closes
   *that* item, which is the convention this corpus already writes
   (`docs/ws/harness-p4/verification.md` §Next Steps). **Downward attachment
   wins**: such a line joins the item below it, never continuing the item
   above — otherwise a marker written between two bullets would be read as
   closing the wrong one, which is the very confusion this rule removes.

An occurrence at line `L` is **not live** exactly when a marker matching the
regex above sits inside `L`'s own item, on a line at or above `L`.
Everything else is unchanged: the phrase table above and the marker regex above
stay where they are and are **read from this spec** rather than retyped
anywhere else, and the screen's standing qualification — it is a screen over
observed backlog vocabulary, not a proof of absence — still holds.

What changes, and only this: the old window reached across an item boundary, so
a marker on the **last line of the preceding item** suppressed an occurrence on
the **first line of the next one**. A marker introducing or closing one item can
no longer satisfy the rule for its neighbour. The block-level consequence above
survives intact and is strengthened: a marker introducing several items still
satisfies none of them, because it belongs to no item's own lines.

**The distinguishing fixture.** Two adjacent items, the first carrying a
bracketed dated marker and the second a backlog phrase with no marker of its
own:

```
- The reader's recall target **[Closed 2026-09-20]**
- Backlog: fold the liveness screen into a tool
```

The phrase `backlog:` (row 18) sits on the second item's own line, `L`. The
marker sits on `L-1` — but that line is the **first** item's own bullet line,
not a standalone marker line abutting the second, so clause 3 does not pull it
into the second item. Under the superseded
`L`/`L-1` rule the occurrence is scored **not live**; under the item-scoped
rule it is scored **live**, because the marker lies outside its item. The
fixture therefore distinguishes the two rules rather than merely passing under
the new one.

### File Size Management

When a category file approaches 300 lines, the skill should:
1. Inform the user: "{file} is at {N} lines — recommend splitting."
2. Propose a split (e.g., `auth.md` → `auth-login.md` + `auth-permissions.md`).
3. If approved: create the new files, move requirements, assign new domain
   prefixes if needed, update `index.md`.

## Verification

### Automated

*These bullets state mechanically checkable obligations, as §Automated does
throughout this corpus; they do not assert that a `tools/` implementation
exists. Several bullets below have backing gc rules and several do not. The
durable artifact for a bullet without one is this spec, which pins both sides
of the check verbatim so an independent reader can reproduce it.*
- Validate that no entry in `index.md` §Out of Scope, and no item in a
  `verification.md` §Next Steps, matches a deferral phrasing without a bracketed
  dated `Superseded | Closed | Struck` marker **inside its own item**, at or
  above the matched line (REQ-REQ-HARNESSP6-001, as superseded by
  REQ-DOCS-PACKAGING-003 — §Item-Scoped Liveness).
- Validate that a block-level marker introducing several items does **not**
  satisfy the rule for those items (REQ-REQ-HARNESSP6-001).
- Validate that §Q-REQ Resolutions prose is outside the checked scopes
  (REQ-REQ-HARNESSP6-001).
- The validator derives **both sides** of every assertion from the run it is
  reporting on — it pins no corpus-measured count as a literal — and proves its
  own non-vacuity on a fixture, so it cannot pass by matching nothing
  (REQ-REQ-HARNESSP6-001).
- Validate that `index.md` lists every category file that exists on disk
- Validate that every requirement ID matches its file's `domain` frontmatter
- Validate no duplicate requirement IDs across all files
- Validate no category file exceeds 300 lines
- Validate `traceability.md` has a row for every requirement ID

### Acceptance Criteria
- [ ] Requirements organized into `docs/requirements/` with subdirectories (REQ-REQ-001)
- [ ] `index.md` has version, status, last_updated, and file listing (REQ-REQ-002)
- [ ] Version bumps follow major/minor rules (REQ-REQ-002)
- [ ] IDs use `REQ-{DOMAIN}-{NNN}` format (REQ-REQ-003)
- [ ] Category files have domain, last_updated, status frontmatter (REQ-REQ-004)
- [ ] No category file exceeds 300 lines (REQ-REQ-005)
- [ ] Index is auto-maintained on every change (REQ-REQ-006)
- [ ] `traceability.md` maps requirements to specs/tests/status (REQ-REQ-007)
- [ ] Staleness compares against `index.md` last_updated (REQ-STALE-001)
- [ ] Research-to-requirements staleness is detected and reported (REQ-STALE-002)
- [ ] `sdd-requirements` reads/writes the new structure (REQ-SKILL-003)
- [ ] Old monolithic format is detected with migration offer (REQ-SKILL-003)
- [ ] §Out of Scope holds only settled exclusions with reasoning, closed entries with date and evidence, and pointers to superseding requirements — no entry phrased as deferred, carried or queued to a later cycle (REQ-REQ-HARNESSP6-001)
- [ ] The same rule binds `verification.md` §Next Steps; a finding too large to fix in-cycle triggers a replan, never a successor workstream (REQ-REQ-HARNESSP6-001)
- [ ] Liveness is decided by the adjacent-marker rule: own line or immediately preceding line, per item, block-level markers excluded; §Q-REQ Resolutions prose is outside the checked scopes (REQ-REQ-HARNESSP6-001)
- [ ] The three settled exclusions named by RS-HARNESSP6-001 are each present in §Out of Scope with their reasoning (REQ-REQ-HARNESSP6-001)
- [ ] Liveness is anchored on the **matched phrase** (lines `L` and `L-1`), not on the entry block, and is stated as distinct from the entry-anchored, marker-below plan-archival strike rule in `plan-management.md` (REQ-REQ-HARNESSP6-001)


**[Updated: 2026-09-20 — the rule originally accepted only the bold-bracket
shape `**[Closed …]**`. Measured against the corpus it governs, that shape
matched 11 annotations in `docs/ws/harness-p5/verification.md` §Next Steps and
**0** in `docs/requirements/index.md` §Out of Scope, which uses a multi-line
italic-paren shape `_(superseded 2026-09-20 — …)_`. A liveness rule that cannot
read half its own governed corpus is vacuous until the first annotation lands
there and then misfires, so both shapes are accepted and the match is anchored
at the marker's opening rather than requiring its close (the italic form wraps
across lines). Requirements-review M1.]**
