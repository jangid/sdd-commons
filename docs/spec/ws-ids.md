---
status: Approved
last_updated: 2026-09-19
requires:
  - REQ-WS-009
  - REQ-WS-010
  - REQ-WS-011
  - REQ-WS-012
  - REQ-WS-013
  - REQ-WS-014
  - REQ-WS-015
---

# Workstream-Prefixed IDs & Merge-Safe Shared Writes

## Context

Two failure modes appear when concurrent workstreams share one repo:

1. **ID allocation races** — the current "scan the whole tree, take the highest
   `NNN`, +1" generators are not concurrency-safe: two workstreams both allocate the
   same next number.
2. **Shared-table merge conflicts** — RS-007 Q1 proved that appending a row at EOF is
   the same git location for both branches and **always** conflicts, regardless of row
   content.

This spec pins the workstream-prefixed ID format, the exact generators and convention
string it touches (and, critically, the parsers it must NOT touch — RS-007 Q4 bounded
the blast radius), and the merge-safe write model for shared-corpus tables. It covers
REQ-WS-009..015. The traceability restructuring that removes the highest-risk shared
write point is in `ws-traceability.md`.

## Design

### Workstream-Prefixed ID Format (REQ-WS-009)

Downstream artifact IDs carry a workstream segment inserted **before** the numeric
counter:

| Namespace | v3 format | v4 format | Example |
|-----------|-----------|-----------|---------|
| Research | `RS-NNN` | `RS-<WS>-NNN` | `RS-ISSUE42-001` |
| Implement deviation | `Q-IMPL-NNN` | `Q-IMPL-<WS>-NNN` | `Q-IMPL-ISSUE42-003` |
| Requirement | `REQ-<DOMAIN>-NNN` | `REQ-<DOMAIN>-<WS>-NNN` | `REQ-AUTH-ISSUE42-001` |

The `NNN` counter is always parsed **after** the workstream token (and, for
requirements, after the domain token). `NNN` stays zero-padded to 3 digits.

**Why insert a middle segment rather than suffix the workstream**: parsing `NNN` after
the `<WS>` token makes each workstream's counter an independent sequence, which is what
eliminates the allocation race at its root (REQ-WS-011), not just its symptom.

### Per-Workstream ID Counters (REQ-WS-011)

Each generator scopes its max-scan **per workstream** (and, for requirements, per
`domain+workstream`), replacing the global "scan whole tree, take max, +1":

```
next_id(namespace, ws[, domain]):
    existing = scan artifacts whose id matches namespace + ws (+ domain)
    n = max( parse_NNN_after_ws_token(id) for id in existing ; default 0 )
    return format(namespace, [domain,] ws, n + 1)
```

Two workstreams concurrently allocate `RS-ISSUE42-001` and `RS-ISSUE57-001` with no
coordination and no collision, because each scans only its own workstream's ids.

### Exactly Four Generators + One Convention String (REQ-WS-012)

The format change touches **exactly** these five sites (RS-007 Q4, exhaustive):

| Site | Current logic | Replacement |
|------|---------------|-------------|
| `sdd-research` (`SKILL.md` id-alloc) | scan `RS-NNN-*` dirs, extract highest `NNN`, zero-pad | scan `RS-<WS>-NNN-*`; parse `NNN` after `<WS>`; max per-workstream |
| `sdd-requirements` (`SKILL.md` id-alloc) | `REQ-<DOMAIN>-NNN` template, highest-`NNN` scan | `REQ-<DOMAIN>-<WS>-NNN`; scan max per `domain+workstream` |
| `sdd-implement` (`SKILL.md` Q-IMPL alloc) | `Q-IMPL-NNN` global sequential, increment from highest | `Q-IMPL-<WS>-NNN`; scan per-workstream |
| `sdd-migrate` (`SKILL.md` RS/REQ remap) | RS/REQ allocation/remap templates, "start after highest" | update the general RS/REQ allocation/remap template to carry a `<WS>` slot for NEW allocations; the v3→v4 migration itself does NOT remap legacy corpus IDs — they remain bare and are treated as the `default` workstream (see ws-migration.md, ws-traceability.md) |
| `sdd-review` (`SKILL.md` convention check) | asserts `REQ-<DOMAIN>-NNN` literally | assert `REQ-<DOMAIN>-<WS>-NNN` / optional `<WS>` segment |

**Parsers that MUST NOT change** (RS-007 Q4 proved them unaffected — over-touching them
risks regressions):

- **Fan-out `Depends on: Chunk N`** derivation — parses chunk **ordinals** from
  `### Chunk N:` headers, a separate namespace from RS/Q/REQ artifact ids. Artifact ids
  appear only as inert prose there.
- **Traceability / requirements row parsing** — opaque-string / `REQ-*` prefix-glob
  matching; tolerates the inserted `<WS>` segment.
- **`sdd-review` Q-REQ / Q-SPEC / Q-IMPL content checks** — no numeric-suffix
  assumption; Q-REQ/Q-SPEC already use letter suffixes (`Q-REQ-G`).
- **`### M\d+:` milestone regex** in `sdd-migrate` — matches milestone headers, not
  artifact ids.

**Why enumerate the non-touched set**: RS-007 Q4 found there is no compiled `RS-\d+` /
`Q-IMPL-\d+` regex anywhere — the breakage is in the described *algorithms*, not grep
patterns. Naming what stays unchanged prevents a well-meaning implementer from
"fixing" a parser that is provably fine and thereby breaking fan-out or review.

### Append Under a Claimed Prefix; New Specs Are New Files (REQ-WS-010)

- **New requirements** are appended under a **claimed domain prefix** recorded in the
  requirements index prefix registry (the Domain Prefixes table), yielding new
  `REQ-<DOMAIN>-<WS>-NNN` ids.
- **New specs** are **new files** in `docs/spec/` — never edits to existing spec file
  bodies.
- **Modifying** an existing shared requirement or spec remains a **human PR conflict**
  to resolve and is explicitly not automated.

**Why append-only new-file/new-row**: these writes 3-way-merge cleanly (REQ-WS-013);
in-place edits to shared artifacts are the genuinely conflicting case and are left to
human resolution.

### Merge-Safe Shared Writes, Never Tail-Append (REQ-WS-013)

All writes to shared-corpus **table** artifacts must be merge-safe — either:

- **sorted insertion into distinct, non-adjacent regions**, or
- **per-workstream-owned rows/files** (as `ws-traceability.md` does).

Naive **append-to-EOF** (and the equivalent insert-before-a-trailing-sentinel) MUST
NOT be used for any shared table.

**Why**: RS-007 Q1 empirically proved append-to-EOF is the same git location for both
branches and always conflicts regardless of row content; a trailing sentinel does not
rescue it (both target the same pre-sentinel point); only distinct-region or
owned-region writes merge cleanly.

### ID-Sorted, One-Row-Per-Line Insertion for `requirements/index.md` (REQ-WS-015)

Additions to `docs/requirements/index.md` — the **Files table**, the **Domain
Prefixes table**, and new requirement rows within a category file — are inserted at
their correct **sorted position**, **one row per line**, never appended at EOF.

```
insert_row(table, new_row):
    find sorted position by id/prefix key
    insert new_row on its own line at that position   # not EOF
```

This keeps the sort deterministic and places concurrent additions in distinct regions.

### Distinct-Domain-Prefix Precondition (REQ-WS-014)

The clean-merge guarantee for `docs/requirements/index.md` new rows is **conditional**
on each concurrent workstream owning a **DISTINCT claimed domain prefix**, so their new
ids sort into distinct, non-adjacent regions (RS-007 S3 clean; S4 same-region
conflicts).

- Distinct-prefix concurrent additions → clean 3-way merge.
- **Same-domain** concurrent additions are an **accepted degradation** to an ordinary
  human PR conflict — the tooling must NOT attempt to silently union them.

**Why accept same-domain conflicts**: RS-007 proved sorted insertion merges cleanly
only when new ids sort to non-adjacent regions. The design already treats modifying
shared artifacts as a human PR conflict; two workstreams extending the same domain
concurrently is the same class of event and is surfaced, not auto-merged. A
`merge=union` `.gitattributes` driver was considered as a belt-and-suspenders
mitigation but is **not adopted** — it can interleave rows unsorted, defeating the
deterministic sort (see Open Questions).

## Open Questions / Assumptions

- **`merge=union` driver (RS-007 Q1, Assumption).** A `merge=union` `.gitattributes`
  driver on the shared table files would auto-union concurrent appends without
  conflict. Default: **do NOT adopt** — it interleaves rows out of sort order,
  breaking the deterministic-sort invariant REQ-WS-015 relies on. The structural fix
  (sorted insertion + per-ws-owned rows) is preferred. Flagged for the operator to
  optionally reconsider at approval.

## Verification

### Automated
- Verify each of the four generators parses `NNN` after the `<WS>` token and scopes its
  max-scan per workstream (per `domain+workstream` for requirements).
- Verify `sdd-review`'s convention check accepts a `<WS>` segment and does not flag
  ws-prefixed ids.
- Verify `### Chunk N:` parsing, traceability/requirements row matching, and the
  Q-REQ/Q-SPEC/Q-IMPL content checks operate unchanged against ws-prefixed ids.
- Verify no skill write path performs a raw EOF append to a shared table; index
  additions insert at sorted position, one row per line.

### Manual
- Two workstreams concurrently allocate `RS-ISSUE42-001` and `RS-ISSUE57-001`; confirm
  no collision without coordination.
- Two workstreams add requirements under **distinct** prefixes; confirm clean 3-way
  merge. Under the **same** domain concurrently; confirm a human-resolvable conflict is
  surfaced and the tooling does not auto-union.

### Acceptance Criteria
- [ ] IDs carry a workstream segment: `RS-<WS>-NNN`, `Q-IMPL-<WS>-NNN`,
      `REQ-<DOMAIN>-<WS>-NNN`; `NNN` parsed after `<WS>` (REQ-WS-009)
- [ ] New requirements append under a claimed prefix; new specs are new files; existing
      shared artifact bodies are not rewritten by tooling (REQ-WS-010)
- [ ] Generators scope max-scan per workstream (per domain+workstream for requirements),
      replacing the global scan-and-increment (REQ-WS-011)
- [ ] Exactly the four generators + the review convention string change; fan-out,
      traceability/requirements parsing, and Q-REQ/Q-SPEC/Q-IMPL checks are untouched
      (REQ-WS-012)
- [ ] Shared-table writes are sorted-insertion or per-ws-owned; no raw EOF append
      (REQ-WS-013)
- [ ] Clean index merges are conditional on distinct claimed domain prefixes;
      same-domain concurrency is an accepted human PR conflict, not auto-unioned
      (REQ-WS-014)
- [ ] `requirements/index.md` additions use ID-sorted, one-row-per-line insertion
      (REQ-WS-015)
- [ ] Markdown well-formed; frontmatter valid

## Implementation Questions

### Q-IMPL-009: Merge-safe write model is marker-`4`-gated (v3 append behavior retained)
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Merge-Safe Shared Writes, §ID-Sorted, One-Row-Per-Line Insertion for `requirements/index.md`, §Append Under a
Claimed Prefix (REQ-WS-010/013/015) — stated as the v4 contract without an explicit
`.sdd-version` gate.
**Decision**: The merge-safe shared-write rules (append-under-claimed-prefix,
ID-sorted one-row-per-line insertion into `requirements/index.md`, new-specs-are-new-
files, no-raw-EOF-append, distinct-prefix precondition) are encoded as a **marker-`4`
branch** in `sdd-requirements` Step 5 and `sdd-specs` Step 2. Under marker `3` or
earlier, the existing write behavior is left byte-unchanged (this repo is live at
marker `3`).
**Rationale**: The plan's v3-solo-safety invariant (constraint #1) requires every
behavior change to be marker-`4`-gated with marker-`3` behavior retained. The spec's
§Design is framed entirely for the v4 concurrent-workstream corpus; gating it on
marker `4` preserves solo v3 behavior while making the merge-safe model active
exactly where concurrency exists. Default carried: gate on `marker == "4"`.

### Q-IMPL-010: Merge-safe write rules placed in requirements + specs
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Exactly Four Generators + One Convention String enumerates the
five ID-format sites but does not pin which skill hosts the REQ-WS-010/013/015
merge-safe *write* rules.
**Decision**: The requirements-side rules (claimed-prefix append, ID-sorted index
insertion, distinct-prefix precondition, no-EOF-append) are encoded in
`sdd-requirements` Step 5 (the skill that maintains `requirements/index.md` and
category files); the new-specs-are-new-files rule is encoded in `sdd-specs` Step 2
(the skill that writes `docs/spec/`). No new skill and no generator beyond the four
was altered for these write rules.
**Rationale**: The write rules must live in the skills that perform the shared writes;
`sdd-requirements` and `sdd-specs` are those skills. This keeps the ID-format change
bounded to the four generators + review string (REQ-WS-012) while placing the
merge-safe write policy at its natural point of enforcement.
