---
status: Approved
last_updated: 2026-09-18
requires:
  - REQ-WS-007
  - REQ-WS-008
  - REQ-WS-HARNESSP3-001
  - REQ-REDB-HARNESSP3-003
---

# Multi-Workstream Traceability Join

## Context

With requirements and specs shared (`ws-layout.md`) and execution artifacts
per-workstream, traceability is the only structure that records **which workstream
cares about which shared input** — the coverage/derivation join across
`REQ → SPEC → workstream → verification`. RS-007 Q1 empirically proved that a single
hand-appended shared traceability table conflicts on **every** concurrent append
(every workstream appends rows, all at the EOF boundary). So traceability must be
restructured so each workstream owns its own rows.

This spec resolves the requirements-stage carried-forward decision on the concrete
traceability shape (REQ-WS-008 offered two options) and pins how the join relates to
staleness. It covers REQ-WS-007 and REQ-WS-008.

## Design

### Decision: Separate Per-Workstream Files, Aggregated (REQ-WS-008)

**Adopted shape**: option (a) — each workstream owns a **separate file**
`docs/ws/<id>/traceability.md`; a shared `docs/requirements/traceability.md` is a
**derived aggregate** regenerated deterministically from all per-workstream files
(plus the pre-existing shipped rows). A workstream only ever edits its own
`docs/ws/<id>/traceability.md`.

**Rejected**: option (b) — delimited per-ws sections
(`<!-- ws:<id> -->…<!-- /ws:<id> -->`) inside the shared file. Within-section edits
merge cleanly (RS-007 S6), but **creating a brand-new section for a new workstream is
still an EOF-boundary edit** and two concurrent new-workstream creations conflict
(RS-007 S7). Separate files never conflict on creation (S8). Since opening a
workstream is exactly when a new section/file appears, the separate-file shape is the
one that survives concurrent workstream creation.

**Why aggregate at all**: the shared matrix stays useful as a single product-wide
view (the shipped `REQ-*` rows and every workstream's coverage in one place). Because
it is **derived**, it is never hand-merged — regeneration replaces it wholesale, so it
cannot merge-conflict (RS-007 S8).

### Per-Workstream File Shape

`docs/ws/<id>/traceability.md` — owned by workstream `<id>`, holds only that
workstream's rows:

```markdown
---
workstream: <id>
last_updated: YYYY-MM-DD
---

# Traceability — <id>

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-AUTH-ISSUE42-001 | auth-login.md | ISSUE-42 | | | |
| REQ-AUTH-001         | auth-login.md | ISSUE-42 | | | |
```

- Rows record, for each shared REQ/SPEC the workstream delivers, the coverage through
  to that workstream's verification. Both **new ws-prefixed requirements** and
  **pre-existing shared requirements the workstream re-uses** may appear as rows owned
  by this workstream.
- The `Workstream` column is redundant with the file location but is retained so a row
  is self-describing once aggregated into the shared matrix.
- A workstream MUST NOT write rows into any other workstream's file or into the shared
  aggregate directly.

**Why a `Workstream` column added to the historical 5-column matrix**: the shipped
matrix is `| Requirement | Spec | Test | Implementation | Verified |`. Aggregating
per-ws rows into one view needs a workstream axis so rows from different files stay
attributable. The shipped rows (no workstream) aggregate under a `default` / blank
workstream value, preserving them unchanged.

**The `Workstream` column (the 3rd column) does not disturb the REQ-WS-012
unchanged-parsers guarantee**: traceability/requirements row parsing keys off the first
`Requirement` column (opaque-string / `REQ-*` prefix-glob, per `ws-ids.md`), so column
position is irrelevant — the parser is unaffected regardless of where the `Workstream`
column sits.

### Aggregation Contract

The shared `docs/requirements/traceability.md` is **regenerated**, not appended:

```
regenerate_shared_traceability():
    rows  = shipped legacy rows (workstream = blank/default)
    rows += concat( parse(docs/ws/<id>/traceability.md) for each <id> )
    sort rows by (Requirement id)          # deterministic order
    write docs/requirements/traceability.md   # wholesale replacement
```

- Regeneration is deterministic (stable sort by requirement id) so the output is
  reproducible and diffs are minimal.
- Because the shared file is replaced wholesale from owned inputs, two workstreams
  regenerating on their own branches never produce a git merge conflict on the
  per-ws inputs; if the derived aggregate itself is committed on both branches, it is
  re-derived on merge rather than hand-reconciled.
- The aggregate is a convenience view. It is **not** read by staleness (see below).

### Traceability Is the Recorded Join; Staleness Computes Live (REQ-WS-007)

Traceability is the **load-bearing recorded** join: for each workstream it records
which shared REQ and SPEC it depends on, through to its verification. This is the
coverage/derivation join that logically defines a workstream's shared-input set.

The staleness **computation**, however, MUST NOT read any traceability file. It
derives the same scoped set **live** by walking the workstream's plan
`task → spec requires: → requirement` chain (specified in `ws-staleness.md`,
REQ-WS-026). The two must coincide: the live plan-walk set equals the coverage set the
traceability join records for that workstream.

**Why compute live rather than read the join**: RS-007 Q2 chose Option A (compute-live,
no new traceability schema column) as lowest-cost — the existing milestone traversal
generalizes verbatim. Making staleness read traceability would couple it to the
aggregate file (a merge-risk artifact) and add a schema dependency for no benefit. The
recorded join documents coverage for humans and review; the live walk drives staleness.
Consequently no traceability **column** is added for staleness scope — the `Workstream`
column above exists only to attribute aggregated rows, not to feed staleness.

### Aggregate Regeneration Ownership: Orchestrated vs Standalone (REQ-WS-HARNESSP3-001)

[Changed 2026-09-18. The defect is **spec-read** — two committed texts disagreed:
Q-IMPL-011 below made every writing skill regenerate the aggregate immediately
after its per-ws write, while `references/fan-out.md` §3e made the orchestrator
regenerate at merge. Which side wins, and the discriminator, are **constructed**
judgements ratified here.]

**Rule.** Regeneration of the shared `docs/requirements/traceability.md` belongs
to the **orchestrator**, in its own post-gate bookkeeping commit, for every
**orchestrated** dispatch. Concretely:

1. `docs/requirements/traceability.md` is **dropped from the leaf default write
   scopes** for orchestrated dispatches
   (`docs/spec/harness-write-scope.md` §2).
2. A **post-gate orchestrator bookkeeping step** and a separate commit are added,
   beside `fan-out.md` §3e's.
3. Q-IMPL-011's behaviour is **kept for standalone, non-orchestrated skill
   runs**, so the aggregate does not go stale when someone invokes a single
   `sdd-*` skill outside the harness.

**Regeneration trigger — every gate outcome, before the session ends.** Moving
the regeneration behind the gate must not let a non-`proceed` outcome leave the
shared aggregate stale: today the leaf regenerates inline, so a stopped or
looped-back stage still leaves the aggregate consistent. The orchestrator
therefore regenerates on **every** gate outcome — `proceed`,
`loop-back-to-fix` and `stop` alike — and before the session ends. Concretely:
after any gate at which a leaf wrote per-ws traceability rows since the last
regeneration, the orchestrator regenerates and commits, so the aggregate is
consistent with the per-ws files at every point an operator could walk away.
Within a fix loop this means one regeneration per gate, each superseding the
last — regeneration is wholesale and idempotent, so repeating it costs nothing
and never compounds.

**Discriminator — decided, not left open.** The dispatched `{write_scope}` slot
**is** the signal; no new flag, field or schema is added. A writing skill
regenerates the aggregate after its per-ws write **unless it was dispatched with
a write scope that omits that path**, in which case the regeneration is the
orchestrator's. Under item (1) the orchestrated leaf scopes omit the path by
construction, so its absence from `{write_scope}` *is* the orchestrated signal,
and its presence — or the absence of any dispatched scope at all — *is* the
standalone signal. A skill therefore never has to know **who** invoked it, only
what it was scoped to write.

**Not adopted**: an explicit instruction line in the PIPELINE template body.
More legible, but it adds text to every dispatch, and the slot-based signal
already exists.

Affected surfaces: `references/write-scope.md` §2 (leaf rows) and §7
(commit-ownership table), `references/fan-out.md` §3e (cross-reference), and the
marker-4 traceability notes in `sdd-requirements`, `sdd-specs`, `sdd-implement`
and `sdd-verify` (each states the unless-clause).

### Legal `Verified` Cell Values (REQ-REDB-HARNESSP3-003)

The `Verified` column tracks the **report's** status, so its vocabulary is
exactly three values:

| Value | Meaning |
|-------|---------|
| `pass` | the report covering this row is `status: pass` |
| `fail` | the report covering this row is `status: fail` |
| `pending-red` | the report is `status: pending-red` — a red round is outstanding |

`pending-red` is written by `sdd-verify` into every cell it would otherwise have
marked `pass` (a `fail` row stays `fail`), and the orchestrator's existing
`pending-red -> pass` flip at DONE flips exactly those cells and regenerates the
aggregate in the same bookkeeping step. One writer per state; no new artifact.
`tools/sdd-gc.py`'s `trace-empty` sweep does not constrain this cell's
vocabulary, so no code change follows. See `docs/spec/adversarial-verify.md`.

[Amended 2026-09-18, harness-p4 — REQ-REDB-HARNESSP4-001, owned by
`adversarial-verify.md`] The gc criterion for these cells reads "`python3
tools/sdd-gc.py --report` raises no new finding **on a `pending-red` cell**"; the
`[traceability-aggregate]` warning raised between a per-workstream traceability
write and the orchestrator's post-gate regeneration (§Aggregate Regeneration
Ownership) is the **designed handshake** and is expected, not a finding.

**Duplicate requirement id across per-workstream files** — see
Q-IMPL-HARNESSP4-001 below: legal, aggregated as-is, newest-workstream row
authoritative.

## Verification

### Automated
- Verify workstream tooling writes only `docs/ws/<id>/traceability.md` and never edits
  another workstream's file or the shared aggregate in place.
- Verify the aggregate regeneration is deterministic (same inputs → byte-identical
  output) and sorted by requirement id.
- Verify the staleness code path performs no read of any `traceability.md`.

### Manual
- Two concurrent workstreams each append their traceability rows to their own files;
  confirm the branches 3-way-merge with no conflict.
- Regenerate the shared matrix on each branch; confirm it is derived (no hand-merge)
  and merging re-derives rather than conflicts.
- For a workstream, confirm the shared REQ/SPEC set derived live by the plan-walk
  (per ws-staleness.md) coincides with the coverage set its traceability file records.

### Acceptance Criteria
- [ ] Traceability records, per workstream, the REQ→SPEC→workstream→verification
      coverage join (REQ-WS-007)
- [ ] Staleness scope is derived live by the plan-walk with NO traceability-file read,
      and coincides with the recorded coverage set (REQ-WS-007)
- [ ] Each workstream owns its rows via a separate `docs/ws/<id>/traceability.md`
      (REQ-WS-008)
- [ ] The shared matrix is a deterministically regenerated aggregate, never hand-merged
      (REQ-WS-008)
- [ ] A workstream only ever edits its own traceability rows (REQ-WS-008)
- [ ] Two concurrent workstreams' traceability additions 3-way-merge with no conflict
      (REQ-WS-008)
- [ ] Markdown well-formed; frontmatter valid
- [ ] Q-IMPL-011 carries the orchestrated/standalone split stated against `{write_scope}` (REQ-WS-HARNESSP3-001)
- [ ] `references/write-scope.md` §2 leaf rows omit `docs/requirements/traceability.md` and §7's commit-ownership table assigns the regeneration to the orchestrator; `references/fan-out.md` §3e cross-references the same rule (REQ-WS-HARNESSP3-001)
- [ ] The marker-4 traceability notes in `sdd-requirements`, `sdd-specs`, `sdd-implement` and `sdd-verify` state the unless-clause (REQ-WS-HARNESSP3-001)
- [ ] A walkthrough of an orchestrated dispatch shows the aggregate regenerated in a separate orchestrator commit and the leaf's `files_written` containing no aggregate path; a standalone run of the same skill regenerates the aggregate itself (REQ-WS-HARNESSP3-001)
- [ ] A walkthrough of a gate resolved `stop`, and one resolved `loop-back-to-fix`, each shows the aggregate regenerated and committed before the session ends (REQ-WS-HARNESSP3-001)
- [ ] This spec lists `pass`, `fail` and `pending-red` as the legal `Verified` cell values (REQ-REDB-HARNESSP3-003)
- [ ] §Legal `Verified` Cell Values states the qualified gc criterion ("no new finding on a `pending-red` cell") and names the `[traceability-aggregate]` handshake warning as expected (REQ-REDB-HARNESSP4-001, owned by `adversarial-verify.md`)
- [ ] A requirement id present in two per-workstream files yields two adjacent aggregate rows; the newest-kickoff workstream's row is authoritative; `trace-empty` runs per file unchanged (Q-IMPL-HARNESSP4-001; REQ-ARB-HARNESSP4-001 cross-reference)

## Cross-Spec Consistency (XSPEC)

**harness-p3 pass (2026-09-18).** No extractable type definitions in
ws-traceability.md — the matrix is a Markdown table contract, reported
explicitly rather than passing silently. Checks:

- The 6-column matrix shape (`Requirement | Spec | Workstream | Test |
  Implementation | Verified`) is unchanged by this amendment.
- `pending-red` is defined as a report status in
  `docs/spec/adversarial-verify.md` and admitted here as a cell value — both
  amended in this pass, vocabulary matches.
- The `{write_scope}` discriminator is stated here and its table effect lives in
  `docs/spec/harness-write-scope.md` §2 / §7 — one rule, two surfaces, no
  divergence.
- `docs/spec/ws-layout.md`'s ownership model (per-ws file owned, aggregate
  regenerated wholesale) is untouched: only *who runs the regeneration* changed,
  never *how* it is produced.

## Implementation Questions

### Q-IMPL-011: Which skills regenerate the shared aggregate, and when
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Aggregation Contract ("regenerated … wholesale replacement")
**Decision**: Every skill that writes a per-ws traceability row under marker `4`
(`sdd-requirements` adding a new row, `sdd-specs` filling **Spec**, `sdd-implement`
filling **Test**/**Implementation** and at chunk-close Check 2, `sdd-verify` filling
**Verified**) regenerates `docs/requirements/traceability.md` **immediately after** its
per-ws write, using the `regenerate_shared_traceability()` contract (shipped legacy rows
+ concat of every `docs/ws/<id>/traceability.md`, stable-sorted by requirement id,
wholesale replacement). The spec pins the aggregate as derived/deterministic but does not
name a single regenerator; making each writer regenerate keeps the aggregate live after
every owned-row change while remaining conflict-free (each branch only edits its own per-ws
file; the aggregate re-derives on merge).
**Rationale**: A per-ws write leaves the aggregate stale until regenerated; co-locating
regeneration with each write is the least-surprising place and needs no separate trigger
skill. Marker `3` behavior is untouched — the single shared file is still written directly.

[Amended 2026-09-18, REQ-WS-HARNESSP3-001] The rule above now holds **only for
standalone, non-orchestrated runs**. Under an orchestrated dispatch the
aggregate regeneration belongs to the orchestrator's post-gate bookkeeping
commit, and the discriminator is the dispatched `{write_scope}` slot: a writing
skill regenerates the aggregate after its per-ws write **unless it was
dispatched with a write scope that omits `docs/requirements/traceability.md`**.
See §Aggregate Regeneration Ownership above.

### Q-IMPL-012: sdd-requirements (a shared-corpus skill) writes into a per-ws file
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Per-Workstream File Shape ("both new ws-prefixed requirements and
pre-existing shared requirements the workstream re-uses may appear as rows owned by this
workstream")
**Decision**: Under marker `4`, when `sdd-requirements` adds a new
`REQ-<DOMAIN>-<WS>-NNN`, the requirement **text** is added to the shared category file
(merge-safe, per `ws-ids.md`), but the traceability **row** is written into the active
workstream's OWN `docs/ws/<ws>/traceability.md` — not the shared aggregate — then the
aggregate is regenerated. This keeps the "a workstream only ever edits its own rows"
invariant even though requirements themselves are shared.
**Rationale**: The row records *which workstream delivers* the REQ, which is
workstream-owned state; only the requirement definition is shared. Splitting text (shared,
merge-safe append) from row (per-ws owned) satisfies both REQ-WS-004 (shared corpus) and
REQ-WS-008 (per-ws-owned rows) without a shared write point.

### Q-IMPL-HARNESSP3-011: "Since the last regeneration" is tracked as a session-state dirty flag
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Aggregate Regeneration Ownership
**Decision**:

The orchestrator sets a session-scoped flag when a leaf's `traceability_fills`
is non-empty, and clears it after a successful regeneration commit. The flag is
session state, not an artifact, so the no-new-artifact invariant holds; on a
resumed session the flag starts set, which costs at most one redundant
regeneration (idempotent) and never a missed one.
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP4-001: A requirement id carried into a second workstream yields two aggregate rows; the newest workstream's row is authoritative
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Aggregation Contract
**Decision**:

`REQ-ARB-HARNESSP3-001` has a row in `docs/ws/harness-p3/traceability.md`
(`fail` = not exercised, history) and in `docs/ws/harness-p4/traceability.md`
(carried for live exercise — REQ-ARB-HARNESSP4-001). `regenerate_aggregate()`
concatenates and stable-sorts **without de-duplication**, so the aggregate
carries **two rows for one id** with divergent `Verified` values once p4 writes
`pass`. This is legal under §Per-Workstream File Shape (re-use rows) and is
**documented as-is — no de-duplication is added**: the aggregate is a
convenience view whose job is to show every workstream's join, and collapsing
rows would hide the history the carried row exists to preserve.

**Authority rule** (for a reader, `tools/sdd-gc.py` and `sdd-verify`): when one
requirement id appears in more than one per-workstream file, the row of the
workstream whose `kickoff.md` `date:` is **latest** is authoritative for the
requirement's current state; ties (no kickoff, equal dates) fall back to the
lexically greatest workstream id. Consequences: (i) `sdd-gc.py`'s `trace-empty`
sweep already runs per file and needs **no tolerance change** — each row is
judged in its own file; (ii) `sdd-verify` writes only its own workstream's file
and applies the cycle's DONE rule to that file's rows, so it never reads the
other row; (iii) any future aggregate-level reader (a completeness report, the
scorer) applies the authority rule rather than counting the id twice. The stable
sort by requirement id places the two rows adjacent, so the history is visible
at a glance. No code change this cycle; the rule is the contract a future reader
implements.
**Date**: 2026-09-18 (specs stage, harness-p4)
