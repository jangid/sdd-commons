---
status: Approved
last_updated: 2026-09-20
requires:
  - REQ-QIMPL-001
  - REQ-QIMPL-002
  - REQ-QIMPL-003
  - REQ-QIMPL-HARNESSP5-001
  - REQ-QIMPL-HARNESSP5-002
---

# Q-IMPL Deviation Protocol

## Context

During implementation, developers encounter situations the spec didn't
anticipate. In the rubric M1 cycle, ~9 Q-IMPL entries were created across
specs — each capturing a real decision the spec hadn't addressed. Without a
protocol, these become silent interpretations that downstream chunks inherit
without awareness.

The current `sdd-implement` skill says "trigger replan when assumptions
break" — that's the heavy-weight escape valve. In practice, most deviations
are lighter than a replan: a spec ambiguity that needs documenting, or an
internal implementation choice that needs no documentation at all.

This spec defines a three-tier classification that matches deviation severity
to response effort.

## Design

### Tier Classification

#### Tier 1: Implementation Choice

Internal decisions that don't affect the spec's public contract.

**Examples**: helper function naming, internal data structure selection,
import organization, private method decomposition.

**Protocol**: No documentation required. Commit normally.

**Why no protocol**: These decisions are routine engineering judgment.
Documenting them would create noise that obscures real deviations.

#### Tier 2: Spec Ambiguity

The spec didn't anticipate the situation. The implementation must make a
decision, but the decision doesn't change the spec's public interface.

**Examples**: spec says "match positions" but doesn't specify the matching
key; spec defines a type but doesn't cover an edge case in its behavior;
spec is silent on error handling for a specific scenario.

**Protocol**:
1. Add a Q-IMPL entry to the relevant spec's `## Implementation Questions`
   section (format below)
2. Continue implementing with the chosen approach
3. The Q-IMPL entry captures the decision for future reference and chunk
   close review

**Why continue rather than stop**: Tier 2 deviations are ambiguities, not
contradictions. The implementer has enough context to make a reasonable
choice. Stopping for every ambiguity would make implementation sessions
unworkably slow.

#### Tier 3: Contract Change

The spec's public interface must change — a type needs renaming, a field
needs adding, an API contract needs revision.

**Examples**: spec defines `BreadthAssessment` but `BreadthAnalysis` is
more accurate; spec omits a field that downstream consumers require; spec's
algorithm produces incorrect results for a discovered edge case.

**Protocol**:
1. Stop implementation of the current task
2. Escalate to the operator
3. The operator decides: edit the spec via `sdd-specs` and get re-approved,
   or trigger `sdd-replan` at Level 2 (spec gap)

**Relationship to replan**: Q-IMPL Tier 3 is a structured trigger for
`sdd-replan` Level 2 ("spec gap"). The Q-IMPL protocol classifies the
deviation; replan handles the response. They are complementary vocabularies,
not duplicates.

**Why stop**: Contract changes ripple across chunks. A renamed type affects
every file that references it. Continuing with a contract change and
documenting it after the fact creates exactly the drift that chunk-close
review (see chunk-close-review.md) is designed to catch — but catching it
earlier is cheaper.

### Q-IMPL Entry Format

Entries live in an `## Implementation Questions` section at the bottom of
the relevant spec file:

```markdown
## Implementation Questions

### Q-IMPL-001: Position matching key
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Reconciliation Engine, "match positions"
**Decision**: Match by `contract_id` rather than `symbol` because
contract_id is unique per instrument while symbol can be shared across
exchanges.
**Impact**: Downstream consumers must include contract_id in position
snapshots.

### Q-IMPL-002: VIX data source fallback
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Q-IMPL Entry Format, "optional indicators" (illustrative — this example lives in the format fence)
**Decision**: Return None when VIX data is unavailable rather than raising.
**Rationale**: Callers already handle None for optional indicators.
```

**Required fields**: question ID, tier, decision, and rationale (or impact
for tier 2+ entries).

### Numbering

- Under `docs/.sdd-version` marker `4` a Q-IMPL id carries a workstream
  segment and a **per-workstream** counter: `Q-IMPL-<WS>-NNN` (for example
  `Q-IMPL-HARNESSP5-001`). `docs/spec/ws-ids.md` is the owning contract for the
  form, the counter scope and the parsing rule — this spec cites it rather than
  restating it.
- Legacy bare `Q-IMPL-NNN` ids remain valid and are read as the `default`
  workstream. They are never remapped and never renumbered.
- The implementer scans all spec files' `## Implementation Questions`
  sections to find the highest existing number **for the active workstream**
  and increments
- Numbering is append-only: retired entries remain in their spec with a
  `[superseded by Q-IMPL-NNN]` status note rather than being deleted or
  renumbered
- No separate index file — entries live in the specs they relate to

**Why a workstream-scoped sequence**: qualifying the counter by workstream
keeps a Q-IMPL id unambiguous in conversation (one id, one entry) while letting
two concurrent workstreams allocate their next number with no coordination and
no collision — the same reasoning `docs/spec/ws-ids.md` applies to `RS-` and
`REQ-` ids. Per-spec numbering would instead require qualifying with the spec
name.

**Why no index file**: The rubric M1 cycle produced ~9 entries across 4
specs. At this volume, an index adds maintenance overhead without
discoverability benefit. The chunk close Q-IMPL audit (Check 4 in
chunk-close-review.md) already scans all specs.

### Discovery on Task Start

When starting an implementation task, `sdd-implement` should instruct the
implementer to read the relevant spec's existing Q-IMPL entries. This
provides context on how prior ambiguities were resolved and prevents
contradictory decisions.

This is advisory — it informs implementation decisions but does not block
task start. A task may reference a spec with no Q-IMPL entries, and that's
normal.

### Interaction with Chunk Close Review

The Q-IMPL audit (Check 4 in chunk-close-review.md) runs at chunk
boundaries. It verifies that implementation decisions deviating from spec
have corresponding Q-IMPL entries. Undocumented deviations are flagged as
advisory findings — the operator may override if the deviation is trivially
obvious.

This creates a safety net: even if the implementer forgets to add a Q-IMPL
entry during implementation, the chunk close catches it.

### Fold-In Status Note (REQ-QIMPL-HARNESSP5-001)

[Added 2026-09-19, harness-p5 — kickoff §Scope item 3.]

A Tier-2 entry records a reading the implementer took where Approved text was
ambiguous. While the spec stays frozen the entry *is* the record; once a specs
pass amends the section, the reading belongs in the **Approved text** so a
reader of the section builds the shipped behaviour without reading the entry.
The device is a third status note beside `[superseded by Q-IMPL-NNN]` and
`[resolved by REQ-…]`:

```
**Status**: `[folded into §<section>, YYYY-MM-DD]` (REQ-…)   # appended after **Date**
```

Rules: (1) the entry's body is **never** edited, deleted or renumbered —
append-only holds (§Numbering); (2) the amended section carries the decision
as its own prose, marked `folded from Q-IMPL-NNN, YYYY-MM-DD` at the point of
insertion, so the two directions of the pointer are both greppable; (3) a
folded entry stops being a deviation — a later reader who finds the section
and the entry disagreeing treats the **section** as the contract; (4) the
`[qimpl-unreferenced]` / `[qimpl-broken-ref]` gc sweeps are unchanged — a
folded entry still needs a resolving **Spec reference**. Why fold rather than
supersede: supersession is for a *changed* decision; folding is the same
decision promoted to contract, and pretending it changed would mislead.

The six harness-p4 entries folded on 2026-09-19 and the sections that now
carry them:

| Entry | Now Approved text in |
|---|---|
| Q-IMPL-HARNESSP4-004 (clause (a) of `implied.fix` counts deciding gates) | `telemetry-reader.md` §Implication-Derived `expected` and the Headline |
| Q-IMPL-HARNESSP4-005 (`dispatch.reason` members, `red_break` canonical; equal-heads operands; `--plan` shortfall operands) | `telemetry.md` §Record Schema; `telemetry-reader.md` §Schema Lint, §`--plan` Floor |
| Q-IMPL-HARNESSP4-006 (OPTIONAL `migration` marker on every `v`) | `telemetry-reader.md` §Schema Lint |
| Q-IMPL-HARNESSP4-007 (equal-heads fires only when nothing landed; with the REQ-TELEM-HARNESSP5-003 `v: 1` exemption) | `telemetry-reader.md` §Schema Lint |
| Q-IMPL-HARNESSP4-008 (`[template-drift]` absent side, finding order) | `skill-lint-v5.md` §`[template-drift]` |
| Q-IMPL-HARNESSP4-009 (§Verdict Rule example token at column 0) | `harness-chunk-verifier.md` §Verdict Rule |

The status notes count six across `telemetry-reader.md`, `skill-lint-v5.md`
and `harness-chunk-verifier.md` (the telemetry entries moved with their
sections under REQ-LINT-HARNESSP5-003).

### Spec-Reference Integrity (REQ-QIMPL-HARNESSP5-002)

[Added 2026-09-19, harness-p5 — housekeeping deferred twice (RS-HARNESSP3-001
Q8-OUT row 6; `docs/ws/harness-p4/verification.md` §Next Steps).]

`**Spec reference**` is a required line on **every** entry, Tier 1 included,
and it must name at least one `§Heading` that exists in the spec carrying the
entry — `tools/sdd-gc.py`'s `[qimpl-broken-ref]` sweep matches each `§…` token
by heading prefix within that file. A pointer into **another** file (a sibling
spec, a `skills/**/references/*.md` section) is written without the `§` sigil —
`` `file.md` section Name `` — so the sweep does not read it as a local heading;
an example entry inside a fenced block — such as the entries in §Q-IMPL Entry
Format — is **excluded from the sweep**: `tools/sdd-gc.py` blanks every line
inside a fence before scanning (its Q4 fenced/quoted-examples exclusion), so a
fenced illustration can never raise `[qimpl-broken-ref]` and the
`**Spec reference**` line it carries is documentation, not a scanned pointer.
That is why the format fence's `Q-IMPL-001` may keep pointing at the
illustrative `§Reconciliation Engine`, a heading no spec in this corpus
defines. Repairs are **text edits only**: add the
missing line, or re-point at a heading that exists (or restore the heading);
entries are never renumbered, the gc rule is unchanged and there is no
allowlist. The three real legacy warnings closed on 2026-09-19 — the
`Q-IMPL-002` example in the fence above also gained a **Spec reference** line,
and that edit is **kept** for consistency of the illustration, but it closed no
warning and is not one of the three:

| Entry | Was | Repair |
|---|---|---|
| Q-IMPL-009 (`ws-ids.md`) | `§ID-Sorted Insertion` | re-pointed at §ID-Sorted, One-Row-Per-Line Insertion for `requirements/index.md` |
| Q-IMPL-014 (`ws-integration.md`) | `` `fan-out.md` §3c step 3 `` read as a local heading | skill pointer rewritten without `§` |
| Q-IMPL-072 (`ws-orchestration.md`) | `` `skill-lint-v5.md` §Marker-4 Prose Move guard 2 `` read as a local heading | sibling-spec pointer rewritten without `§` |

## Verification

### Automated
- Verify `sdd-implement` SKILL.md documents the three-tier protocol
- Verify tier descriptions match: Tier 1 (no protocol), Tier 2 (Q-IMPL
  entry, continue), Tier 3 (stop, escalate)
- Verify Q-IMPL entry format includes ID, tier, decision, rationale fields
- Verify global sequential numbering is documented

### Manual
- Run `sdd-implement` against a spec with ambiguities
- Create a Tier 2 Q-IMPL entry; verify format compliance
- Trigger a Tier 3 deviation; verify implementation stops and escalates
- At chunk close, verify Q-IMPL audit detects undocumented deviations

### Acceptance Criteria
- [ ] Three-tier protocol documented in implement (REQ-QIMPL-001)
- [ ] Tier 1 requires no documentation (REQ-QIMPL-001)
- [ ] Tier 2 adds Q-IMPL entry and continues (REQ-QIMPL-001)
- [ ] Tier 3 stops and escalates; references replan Level 2 (REQ-QIMPL-001)
- [ ] Q-IMPL entries use the numbering scheme of §Numbering — under marker `4` the workstream-scoped `Q-IMPL-<WS>-NNN` form of `docs/spec/ws-ids.md`, with legacy bare `Q-IMPL-NNN` ids read as the `default` workstream (REQ-QIMPL-002) — [rescoped 2026-09-20] this clause read "global sequential numbering", stale text predating the marker-`4` id contract; see §Numbering
- [ ] Entries placed in spec's Implementation Questions section (REQ-QIMPL-002)
- [ ] Each entry includes ID, tier, decision, rationale (REQ-QIMPL-002)
- [ ] Numbering is append-only with superseded notes (REQ-QIMPL-002)
- [ ] Task start includes advisory read of existing Q-IMPL entries (REQ-QIMPL-003)
- [ ] The `[folded into §<section>, YYYY-MM-DD]` status note is defined here with its four rules; the six Q-IMPL-HARNESSP4-004..009 entries carry it and their bodies are unchanged; `grep -c 'folded into' docs/spec/telemetry.md docs/spec/telemetry-reader.md docs/spec/skill-lint-v5.md docs/spec/harness-chunk-verifier.md` sums to 6; `tools/sdd-telemetry.py --self-test`'s `test_schema_table_agrees` still passes; `grep -n '^  CHUNK_VERDICT:' docs/spec/harness-chunk-verifier.md` returns nothing; `python3 tools/sdd-gc.py --report` raises no new finding (REQ-QIMPL-HARNESSP5-001)
- [ ] `python3 tools/sdd-gc.py --report | grep -c 'qimpl-broken-ref'` prints 0; no qimpl-related hunk lands in `tools/sdd-gc.py` — `git diff main -- tools/sdd-gc.py | grep -E '^[+-]' | grep -v '^[+-][+-]' | grep -ci 'qimpl'` prints 0; no entry was renumbered; the entry `GC:` line at the next orchestrated run shows the reduced warning count (REQ-QIMPL-HARNESSP5-002)
  - [rescoped 2026-09-20] This clause read "`git diff --stat main -- tools/sdd-gc.py` is empty" when it was Approved. The 2026-09-20 replan added REQ-GC-HARNESSP5-001 (`traceability-rowdrop`), whose implementation legitimately edits the same file, superseding the empty-diff form. The rescoped clause keeps the original intent — REQ-QIMPL-HARNESSP5-002 is a spec-text repair that touches no gc code — and is in any case implied by the `qimpl-broken-ref` count above.

## Cross-Spec Consistency (XSPEC)

**harness-p5 pass (2026-09-19).** No extractable type definitions (the entry
format is a Markdown fence). The fold-in device is defined once here and used
by name in `telemetry-reader.md`, `skill-lint-v5.md` and
`harness-chunk-verifier.md`; the "section Name without `§`" pointer form is the
one `telemetry-reader.md`'s moved entries already use for `telemetry.md`
sections. No unresolved contradictions.
