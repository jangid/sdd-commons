---
domain: QIMPL
last_updated: 2026-09-19
status: Approved
research_refs: [RS-HARNESSP5-001]
---

# Requirements: Q-IMPL Deviation Protocol

## Overview

Protocol for handling implementation deviations from spec during
`sdd-implement`. Provides a three-tier classification: silent implementation
choices, documented spec ambiguities (Q-IMPL entries), and escalated
contract changes. Derived from RS-002 finding P2. (see RS-002)

## Requirements

### REQ-QIMPL-001: Three-tier deviation classification
`sdd-implement` must document a three-tier protocol for implementation
deviations from spec:
- **Tier 1** (implementation choice): Internal decisions (helper naming,
  data structure selection) that don't affect the spec's public contract.
  No documentation required.
- **Tier 2** (spec ambiguity): The spec didn't anticipate the situation.
  Add a Q-IMPL entry to the relevant spec's "Implementation Questions"
  section. Continue implementing.
- **Tier 3** (contract change): The spec's public interface must change.
  Stop implementation, escalate to the operator. This typically triggers
  `sdd-replan` at Level 2 (spec gap), but the Q-IMPL protocol and replan
  vocabulary are complementary — Q-IMPL classifies the deviation, replan
  handles the response.
[Priority: must]

### REQ-QIMPL-002: Q-IMPL entry format
Q-IMPL entries must use global sequential numbering (`Q-IMPL-001`,
`Q-IMPL-002`, ... across all specs in the project) and be placed in an
`## Implementation Questions` section at the bottom of the relevant spec
file. Each entry must include: the question ID, a description of the
deviation, and the rationale for the implementation choice. Numbering is
append-only; retired entries remain in their spec with a
`[superseded by Q-IMPL-NNN]` status note.
[Priority: must]

### REQ-QIMPL-003: Q-IMPL discovery on task start
When starting an implementation task, the implementer should read the
relevant spec's existing Q-IMPL entries to understand how prior ambiguities
were resolved. This is advisory — it informs implementation decisions but
does not block.
[Priority: should]

<!-- REQ-QIMPL-HARNESSP5-NNN: workstream-prefixed additions for the harness-p5
     cycle (RS-HARNESSP5-001; marker 4, per docs/spec/ws-ids.md). -->

### REQ-QIMPL-HARNESSP5-001: Q-IMPL-HARNESSP4-004..009 are folded into Approved spec text
The six harness-p4 Tier-2 entries must be folded into the Approved text of the
spec each amends, so a reader of the section builds the shipped behaviour
without reading the entry: Q-IMPL-HARNESSP4-004 (clause (a) of `implied.fix`
counts deciding gates) and -005 (`dispatch.reason` members with `red_break` as
the canonical spelling and uppercase `RED_BREAK` not admitted; the
equal-heads exemption keyed on `commit.token` and `files_written_n`; `--plan`
shortfall operands) into `docs/spec/telemetry.md` §Implication-Derived
`expected`, §Record Schema and §`--plan` Floor; -006 (the OPTIONAL `migration`
marker admitted on every `v`) and -007 (the equal-heads rule fires only when
nothing landed, keyed on `commit.token`; plus the REQ-TELEM-HARNESSP5-003 `v: 1`
exemption) into §Schema Lint; -008 (`[template-drift]` absent-side behaviour and
finding order) into `docs/spec/skill-lint-v5.md` §`[template-drift]`; -009 (the
§Verdict Rule yaml example) into `docs/spec/harness-chunk-verifier.md` by
un-indenting the example's token so the illustrative prose matches the fenced
contract. Entries are append-only: each keeps its text and gains a
`[folded into §<section>, 2026-09-19]` status note (REQ-QIMPL-002's superseded
device); nothing is deleted or renumbered. (workstream `harness-p5`; kickoff
§Scope item 3)
**Acceptance**: `grep -c 'folded into' docs/spec/telemetry.md docs/spec/skill-lint-v5.md docs/spec/harness-chunk-verifier.md`
sums to 6 across the three files (or the split files of REQ-LINT-HARNESSP5-003);
`tools/sdd-telemetry.py --self-test`'s `test_schema_table_agrees` still passes;
`grep -n '^  CHUNK_VERDICT:' docs/spec/harness-chunk-verifier.md` returns
nothing; `python3 tools/sdd-gc.py --report` raises no new finding.
[Priority: must]

### REQ-QIMPL-HARNESSP5-002: the three `[qimpl-broken-ref]` gc warnings are routed to zero
The three pre-existing `tools/sdd-gc.py` `[qimpl-broken-ref]` warnings must be
resolved at source so the sweep's entry baseline reads `0 warn` for that rule:
Q-IMPL-009 (`ws-ids.md`), Q-IMPL-014 (`ws-integration.md`) and Q-IMPL-072
(`ws-orchestration.md`) have their **Spec reference** re-pointed at a heading
that exists in the named spec (or the named heading restored) — text edits only,
entries never renumbered, no gc rule change and no allowlist. (workstream `harness-p5`; deferred twice —
`index.md` §Out of Scope RS-HARNESSP3-001 Q8-OUT row 6 and
`docs/ws/harness-p4/verification.md` §Next Steps — and now in scope as
housekeeping)
**Acceptance**: `python3 tools/sdd-gc.py --report | grep -c 'qimpl-broken-ref'`
prints 0; `git diff --stat main -- tools/sdd-gc.py` is empty; the entry `GC:`
line at the next orchestrated run shows the reduced warning count.
[Priority: should]
[Updated: 2026-09-19, specs-stage review] This requirement was Approved reading
**four** warnings and counting Q-IMPL-002 (`docs/spec/deviation-protocol.md`)
among them. That premise was false and is corrected to **three**:
`tools/sdd-gc.py` blanks fenced lines before scanning, and the Q-IMPL-002 entry
is an illustration inside a fenced block, so it was never a `[qimpl-broken-ref]`
warning. The **Spec reference** line the fenced Q-IMPL-002 example gained is
kept for illustration consistency with the three real entries — it closes no
warning and is not one of the three. The acceptance grep (gc
`[qimpl-broken-ref]` count → 0) is unaffected and still passes. Decision
recorded as Q-REQ-P5-J; the spec-side statement is
`docs/spec/deviation-protocol.md` §Spec-Reference Integrity.
