---
status: Approved
last_updated: 2026-09-18
requires:
  - REQ-HARN-HARNESSP4-001
  - REQ-HARN-HARNESSP4-002
  - REQ-HARN-HARNESSP4-003
  - REQ-HARN-HARNESSP4-006
---

# Harness Commit Fidelity — the `COMMIT:` Gate Signal

## Overview

[Added 2026-09-18, harness-p4 — REQ-HARN-HARNESSP4-001..003, -006]

This spec defines the orchestrator's **commit-fidelity check**: after the
`proceed` decision the orchestrator compares the paths a dispatch was observed
to write against the paths that actually **landed** on the integration line and
renders the result as its own gate signal, `COMMIT: COMPLETE | INCOMPLETE`.

**Why a new spec file and not a section of `harness-write-scope.md`.** The
write-scope spec answers *"did the leaf write only where it was allowed to?"* —
a **pre-decision** question about the leaf, observed before the gate and
resolved inside it. Commit fidelity answers *"did the orchestrator land
everything the leaf wrote?"* — a **post-decision** question about the
orchestrator's own commit, computable only after `proceed`. The two share the
observed-writes set as an input but differ in subject (leaf vs orchestrator),
position (before vs after the decision), token family, pause options, self-test
helper and telemetry group. `harness-write-scope.md` already runs to ~500 lines
across two hardening cycles; folding a second signal with its own lifecycle into
it would bury both. `harness-loop-control.md` owns the *order* of gate signals
and is amended (its §Gate Signal Order) to place `COMMIT:`, but it does not own
any signal's semantics — none of the existing signals is defined there. Hence a
sibling spec, with `harness-write-scope.md` §Commit Ownership pointing here.

## Context

`docs/ws/harness-p3/verification.md` §V14 recorded the defect: Chunk 7's leaf
edited `CLAUDE.md`, the write-scope check correctly tagged the path `IN` and
rendered `SCOPE: CLEAN`, the operator chose `proceed`, and the orchestrator's
commit omitted the path. Nothing in the harness observed the omission; it was
repaired at `16e240b` after a human read, and review finding C1 and red finding
R4 of that cycle share the root cause. The write-scope check is blind here by
design: its snapshot window closes on return, *before* the orchestrator's commit
(`harness-write-scope.md` §Snapshot Ordering), so the commit can never be flagged
by it — which is right for scope and wrong for fidelity.

RS-HARNESSP4-001 §Q1 probed five cases in a scratch repository and fixed the
comparand: a **two-sha `git diff --name-only`** range, never `git show
--name-only --format= HEAD`, because `git show HEAD` names only the last commit
(the aggregate-regeneration commit at every marker-4 implement chunk) and is
empty on a merge commit. Requirements ratified the comparand, the post-decision
placement, the observed-writes-only `expected` term and the two-member token
(Q-REQ-P4-A, -B, -C). Fulfils REQ-HARN-HARNESSP4-001 (signal, comparand,
placement, pause), REQ-HARN-HARNESSP4-002 (sequential `expected`),
REQ-HARN-HARNESSP4-003 (fan-out comparands) and REQ-HARN-HARNESSP4-006
(self-test helper). The lint row is owned by `skill-lint-v5.md`
(REQ-LINT-HARNESSP4-002) and the telemetry trace by `telemetry.md`
(REQ-TELEM-HARNESSP4-007).

**Standing constraints this spec must not contradict**: no auto-advance and no
new artifact (REQ-ORCH-011/014, REQ-HARN-027); telemetry is never load-bearing
(`telemetry.md` §Writer) — `COMMIT:` is rendered from git, never from a record;
the marker-3 path is unchanged apart from where the integration line is rooted.

## Design

### Signal and Token Family (REQ-HARN-HARNESSP4-001)

```
landed   := git diff --name-only <HEAD_before> <HEAD_landed> # two-sha range, captured BEFORE any bookkeeping commit; unconditional
expected := <mode-specific set — §Comparand Table>            # sequential: observed writes only (REQ-HARN-HARNESSP4-002)
COMMIT: COMPLETE (N paths)                                     # expected == landed; N = |landed|
COMMIT: INCOMPLETE (k observed, not landed: <paths>[; j landed, not observed: <paths>])
```

- `HEAD_before` is the integration-line HEAD captured by `snapshot(before)`
  immediately before dispatch — the same sha the write-scope check's
  `committed_delta` starts from (`dispatch-snapshot-base.md`,
  `harness-write-scope.md` §Observation). It is the range start
  **unconditionally** [Amended 2026-09-18, harness-p4 specs review r1 — M2]:
  it equals `HEAD_gate` (the HEAD when the gate decision is taken) whenever the
  leaf did not commit, and precedes the leaf's commits when it did, so a
  compliant-but-eager leaf's commits count as landed with no special case.
  `HEAD_landed` is the integration-line HEAD immediately after the orchestrator's own commit
  (sequential) or merge (fan-out merge step), **before** the
  aggregate-regeneration commit (`ws-traceability.md` §Aggregate Regeneration
  Ownership) or any other bookkeeping commit. The pair is captured as two shas
  and diffed as a range; `HEAD` is never used as a literal comparand.
- The family has **exactly two members**. `INCOMPLETE` carries both directions
  of the set difference as clauses of **one line**: `observed, not landed`
  (the V14 omission) and `landed, not observed` (the inverse error — the
  orchestrator committing a path no leaf wrote). The second clause is omitted
  when `j = 0`. No third token exists for any case (§Fan-out explains why a
  merge drop needs none).
- Paths are rendered repo-relative, sorted, comma-separated; the line is an
  **own-line token** parsed as `^COMMIT:`, like `SCOPE:`.
- The `N` in `COMPLETE (N paths)` counts **distinct** paths (the strict-set rule
  of `harness-write-scope.md` §Observed Writes Are a Strict Set applies to both
  operands).

**Why the range and not `git show HEAD`** (probe-evidenced, RS-HARNESSP4-001 §Q1
cases 3–4): under fan-out a fast-forward of a two-commit leaf makes `git show
HEAD` name only the last commit's paths (a false `INCOMPLETE`), and a true merge
commit shows an empty combined diff; in sequential marker-4 mode the same defect
appears whenever the orchestrator makes more than one commit at a gate, which it
does at every implement chunk. `git diff --name-only PRE HEAD` equalled the
leaf's delta in every probed case.

### Comparand Table (REQ-HARN-HARNESSP4-001, -002, -003)

| Gate | `expected` | `landed` | When computable | Position in the gate |
|---|---|---|---|---|
| sequential per-chunk gate and stage gate, on `proceed` | **observed writes only** — `porcelain_delta ∪ committed_delta ∪ content_delta` (`harness-write-scope.md` §Observation, §Content-Hash Observation) | `git diff --name-only HEAD_before HEAD_landed` (unconditional; `HEAD_before == HEAD_gate` whenever the leaf did not commit), captured right after the orchestrator's commit and before any bookkeeping commit | post-decision | closing line of the same gate — item 8 of `harness-loop-control.md` §Gate Signal Order |
| fan-out **per-leaf** gate | the leaf's observed writes in its worktree | the leaf's committed delta `git diff --name-only <base> <tip>` — the write-scope check's own term (b) | pre-decision | position **2b** — after `SCOPE:`, before `CHUNK_VERDICT:` |
| fan-out **merge step**, per branch | that leaf's committed delta `base..tip` | `git diff --name-only PRE_MERGE HEAD` on the integration branch | post-`proceed`, at merge | closing line after the merge — item 8 |

`base`, `tip` and `PRE_MERGE` are the shas `references/fan-out.md` §3a.v / §3b
already compute; no new git state is introduced. Every operand is a path set
the harness already holds, so the check adds no leaf, no counter and no
artifact.

### Sequential `expected` Is Observed Writes Only (REQ-HARN-HARNESSP4-002)

`RETURN.files_written` is **never a term** of `expected`. A path the leaf claims
but never wrote — or wrote and reverted, so no delta observes it — cannot land;
unioning the claim in would render `COMMIT: INCOMPLETE (observed, not landed)`
for a defect of the leaf's *return*, not of the orchestrator's commit: a false
pause on a load-bearing signal. Instead:

```
return_drift := RETURN.files_written − observed_writes
→ rendered as a warning line  "RETURN drift: <k> path(s) claimed, not observed: <paths>"
  beside the other return-side warnings (KEYS MISSING, …) — never a pause, never a COMMIT: term
```

The warning is **owned by the return contract**
(`harness-return-contract.md` §Return-Drift Warning; skill side
`references/return-contract.md` §1/§3), which already owns return-side defects.
This is the sequential analogue of the fan-out clause `RETURN.commits ⊆ git
rev-list <base>..<tip>` below: both keep a leaf's return error out of the
landed-vs-observed comparison. It departs deliberately from V14's proposed
"`files_written` plus the observed set".

### Placement and the `amend | accept | stop` Pause (REQ-HARN-HARNESSP4-001)

The commit is the *consequence* of the `proceed` decision, so in sequential mode
the line cannot sit between `SCOPE:` and `CHUNK_VERDICT:` without asserting a
commit that has not happened. It renders as a **post-decision closing line of
the same gate**, immediately after the commit and **before the next dispatch**.
The canonical statement of where every signal sits — including item 8
"post-decision: `COMMIT:`" and the per-leaf position 2b — is
`harness-loop-control.md` §Gate Signal Order (the counterpart of
`references/loop-control.md` §5); this spec and every other restating surface
point there and do not restate the order.

**Not adopted**: deferring the line to the *next* gate the way
`TELEMETRY: rec <n>` asserts the previous append. V14's omission survived two
gates and a commit; under deferral the next dispatch would already have run
against the un-landed tree, and the last chunk of a stage has no next gate
until the review. The `TELEMETRY:` precedent is not binding because telemetry
is by contract never load-bearing, while `COMMIT:` exists to be.

On `INCOMPLETE` the gate **pauses** with three options:

| Option | Effect |
|---|---|
| `amend (add the missing paths to the commit)` | the orchestrator stages every `observed, not landed` path and amends its own commit (never a leaf's, never a merge commit — see fan-out below); the line is re-rendered and must now read `COMPLETE`. The write-scope check is **not** re-run: every amended path came from the observed set and was already classified there (`IN` / `ADVISORY` by construction — an `OUT` path could not have reached `proceed`). A `landed, not observed` clause is not amendable; it resolves by `accept (note)` or `stop` |
| `accept (note)` | the note is **recorded in the gate text**, and — if the path is never landed in a later commit of the cycle — in the plan's existing blocked-task note (`harness-loop-control.md` §Circuit-Break Checkpoint): the only durable traces REQ-HARN-027 / REQ-ORCH-014 allow. No new artifact |
| `stop` | as everywhere: the session ends at this gate; the partial commit stands and the pause text names it |

**No next dispatch is issued until the pause is resolved** — including the
implement-stage review after the last chunk (Q-REQ-P4-B): a review dispatched
against an un-landed tree reviews the wrong artifact. `COMPLETE` needs no
acknowledgement and does not alter the options.

The pause is a **fifth pause-family member** beside `RETURN: MALFORMED`,
`SCOPE: VIOLATION`, `REVIEW: CONTRADICTION` and the budget-exhaustion pause;
telemetry normalises `amend` to `gate.decision: other` unless `telemetry.md`
§Record Schema adds a member (it does not this cycle — the `commit` group
carries the token and counts instead).

### Fan-out: Per-Leaf and Merge-Step Clauses, No Third Member (REQ-HARN-HARNESSP4-003)

**Per-leaf gate (position 2b).** `expected` is the leaf's observed writes in its
worktree, `landed` its committed delta `base..tip`, so the comparison reduces to
**the leaf's uncommitted writes** — exactly what worktree teardown
(`references/fan-out.md` §3d) would discard. The data exists before the
decision, so the line renders pre-decision, after `SCOPE:` and before
`CHUNK_VERDICT:`. A second clause on the same line checks the return side:

```
RETURN.commits ⊆ git rev-list <base>..<tip>
→ violation appended to the per-leaf line: "; RETURN.commits not on branch: <sha>[, <sha>]"
```

On per-leaf `INCOMPLETE` the options are the same three; `amend` here means the
orchestrator commits the uncommitted paths **on the leaf branch** (the fan-out
revert precedent — `harness-write-scope.md` §Finding Format: fan-out fixes land
on the leaf branch, never on the integration branch) before the branch may enter
the merge step.

**Merge step (post-`proceed`, item 8).** Per branch, `expected` is the leaf's
committed delta `base..tip` and `landed` is `git diff --name-only PRE_MERGE HEAD`
on the integration branch, rendered as a closing line after the merge. `amend`
is **unavailable** at the merge step: a merge commit is not amended; a drop here
resolves by `accept (note)` or `stop`.

**Why no third member.** A clean `git merge` — fast-forward or true merge
commit — cannot lose a path (`diff PRE HEAD` equalled the leaf delta in both
probe cases). The only way a path vanishes between leaf and integration line is
conflict → abort → redo (`references/fan-out.md` §3c): the redo is a **new
dispatch** with its own snapshot, committed delta and per-leaf gate, so its own
sets are compared and the first attempt's set is discarded **by design**. If
preserving the aborted attempt's path list is ever wanted it is a repair-packet
concern (`harness-return-contract.md` §Repair Packet), not a gate token. The
token family in every file stays exactly `COMPLETE | INCOMPLETE`.

### Self-Test Helper and Fixtures (REQ-HARN-HARNESSP4-006)

`tools/sdd-scope-check-selftest.py` gains a **pure** helper and five fixtures:

```
commit_check(expected: set[str], landed: set[str]) -> str
    # returns the rendered COMMIT: line; no git, no I/O; N counts distinct paths
```

| Fixture | Builds | Asserts |
|---|---|---|
| C1 sequential omission | leaf writes `a.txt b.txt docs/plan.md`; orchestrator stages two | `COMMIT: INCOMPLETE (1 observed, not landed: docs/plan.md)`; same repo fully staged → `COMMIT: COMPLETE (3 paths)` |
| C2 sequential inverse | orchestrator also commits `stray.txt` | the `landed, not observed: stray.txt` clause on the **same** line |
| C3 fan-out fast-forward | leaf makes two commits (`a.txt`, then `b.txt`); merge fast-forwards | `COMMIT: COMPLETE (2 paths)` from the range; the same fixture computed with `git show --name-only --format= HEAD` renders a false `INCOMPLETE` — asserted as the negative control |
| C4 fan-out true merge | integration branch takes a bookkeeping commit before the leaf merges | `COMPLETE` with the leaf's full delta; a regeneration commit *after* the range is captured leaves it `COMPLETE` |
| C5 conflict → abort → redo | first leaf commits `a.txt b.txt`, conflicts on `a.txt`, merge aborted; redo leaf commits `b.txt` | the redo's own sets are compared → `COMPLETE (1 path)`; no third member is ever rendered; the first attempt's set does not enter |

Fixtures build throwaway repositories under a temporary directory exactly as
the existing F-series does; nothing touches this repository's working tree.
Fixture ids continue the tool's existing numbering scheme (a `C` prefix keeps
them distinguishable from the scope fixtures `F1…`; the implementer may renumber
if the tool's convention differs — the five scenarios are the contract).

### Restatement Surfaces

One sentence each, never the order or the comparand table (those live in
`harness-loop-control.md` §Gate Signal Order and here):

| Surface | States |
|---|---|
| `references/write-scope.md` §7 | the check, the comparand table, the token, the pause options — the skill-side defining section (the lint row's `fix:` points here) |
| `references/loop-control.md` §5 | item 8 and position 2b |
| `references/fan-out.md` §3a.v, §3b | the per-leaf clause + 2b; the merge-step comparand `PRE_MERGE..HEAD` |
| `skills/sdd-orchestrate/SKILL.md` §The gate | one line |
| `skills/sdd-orchestrate/USAGE.md` §7b | gate fixtures gain the closing line |
| `CLAUDE.md` §Gate vocabulary | one sentence |
| `docs/spec/harness-write-scope.md` §Commit Ownership | one pointer sentence to this spec |
| `docs/spec/telemetry.md` §Record Schema | the `commit` group (REQ-TELEM-HARNESSP4-007) |
| `docs/spec/skill-lint-v5.md` | the `REQUIRED` row (REQ-LINT-HARNESSP4-002) |

### Marker-4 Rooting

Under `docs/.sdd-version` == `4` the integration line is the **workstream
branch** (`ws-integration.md`); `HEAD_before` / `HEAD_landed` / `PRE_MERGE` are
its shas and the bookkeeping commit excluded from the range is the per-chunk
aggregate regeneration. Under marker `3` the integration line is `main` and no
regeneration commit follows the feature commit; the check is otherwise
identical.

### Live Exercise Required [needs-exercise]

The comparand is probe-evidenced; the post-decision pause, `amend`, and an
`INCOMPLETE` at the last chunk before the implement review are **constructed**
and have never rendered in a live orchestrated run. Default: adopt as specified.
This cycle's implement stage is the live exercise — `verification.md` must
record at least one live gate rendering the `COMMIT:` line (§Acceptance
Criteria). Fallback if the line never renders live: the requirement is descoped
at replan under the cycle's DONE rule, not closed `fail`.

## Verification

### Automated
- `python3 tools/sdd-scope-check-selftest.py --self-test` exits 0 and lists the
  five `COMMIT:` fixtures C1–C5 in its output.
- Mutation: replacing the two-sha range in C3 with `git show --name-only
  --format= HEAD` fails C3 with a false `INCOMPLETE`.
- `commit_check({"a","b","c"}, {"a","b"})` → `COMMIT: INCOMPLETE (1 observed,
  not landed: c)`; `commit_check({"a"}, {"a","stray"})` → `COMMIT: INCOMPLETE
  (0 observed, not landed: ; 1 landed, not observed: stray)` — the implementer
  may elide an empty first clause, but the second clause must be present;
  `commit_check(S, S)` → `COMMIT: COMPLETE (|S| paths)`.
- Walkthrough (fixture return): a leaf listing `docs/extra.md` in
  `files_written` without writing it renders `COMMIT: COMPLETE` plus a
  return-drift warning naming `docs/extra.md`, never `COMMIT: INCOMPLETE`.
- Walkthrough: a leaf whose `RETURN.commits` names a sha absent from
  `git rev-list base..tip` renders the `RETURN.commits not on branch` clause on
  the per-leaf `COMMIT:` line.
- `tools/sdd-skill-lint.py` `REQUIRED` row for `COMMIT: COMPLETE | INCOMPLETE`
  in `loop-control.md` and `SKILL.md` (`skill-lint-v5.md`).
- `grep -rn 'COMMIT: ' skills docs/spec CLAUDE.md` shows only the two members;
  no `DROPPED`, `PARTIAL` or other third token.

### Manual
- Run one sequential implement chunk to `proceed`: the gate text ends with a
  `COMMIT:` line after the commit and before the next dispatch; `git diff
  --name-only HEAD~1 HEAD` (before regeneration) equals the observed set.
- Force an omission (unstage one observed path before the orchestrator commits):
  `COMMIT: INCOMPLETE` pauses; `amend` re-renders `COMPLETE` and no scope
  block is re-rendered.

### Acceptance Criteria
- [ ] `references/write-scope.md` §7 defines the check, the comparand table (sequential / fan-out per-leaf / fan-out merge step), the two-member token and the `amend | accept | stop` options; `skills/sdd-orchestrate/SKILL.md` §The gate, `USAGE.md` §7b, `CLAUDE.md` §Gate vocabulary and `docs/spec/harness-write-scope.md` state it in one sentence each (REQ-HARN-HARNESSP4-001)
- [ ] `harness-loop-control.md` §Gate Signal Order and `references/loop-control.md` §5 list item 8 "post-decision: `COMMIT:`" and position 2b for the fan-out per-leaf gate; no other spec restates the order (REQ-HARN-HARNESSP4-001, -003)
- [ ] Walkthrough: a sequential chunk whose leaf wrote `a.txt`, `b.txt`, `docs/plan.md` and whose orchestrator staged two renders `COMMIT: INCOMPLETE (1 observed, not landed: docs/plan.md)` and pauses before the next dispatch; fully staged it renders `COMMIT: COMPLETE (3 paths)`; also committing `stray.txt` renders the `landed, not observed: stray.txt` clause on the same line; a regeneration commit following the feature commit still renders `COMPLETE` (REQ-HARN-HARNESSP4-001)
- [ ] An `INCOMPLETE` at the last chunk blocks the implement-stage review dispatch until resolved; `amend` does not re-run the write-scope check (REQ-HARN-HARNESSP4-001)
- [ ] This cycle's `docs/ws/harness-p4/verification.md` records at least one live gate rendering the `COMMIT:` line (REQ-HARN-HARNESSP4-001)
- [ ] The comparand table names observed writes as the sole sequential `expected` term and cross-references the return-drift warning; `references/return-contract.md` §1 or §3 and `harness-return-contract.md` §Return-Drift Warning define `RETURN.files_written − observed` as a warning, not a pause; the `docs/extra.md` walkthrough renders `COMPLETE` plus the warning (REQ-HARN-HARNESSP4-002)
- [ ] `references/fan-out.md` §3a.v carries the per-leaf clause (incl. `RETURN.commits ⊆ rev-list`) and its 2b placement; §3b carries the merge-step comparand `PRE_MERGE..HEAD`; the two-commit fast-forward walkthrough renders `COMMIT: COMPLETE (2 paths)`; the true-merge-after-bookkeeping walkthrough renders `COMPLETE` with the leaf's full delta; a claimed sha absent from `rev-list` is reported on the per-leaf line; the token family everywhere is exactly `COMPLETE | INCOMPLETE` (REQ-HARN-HARNESSP4-003)
- [ ] `tools/sdd-scope-check-selftest.py --self-test` exits 0 with the five fixtures C1–C5 listed; the `git show` mutation of C3 fails with a false `INCOMPLETE`; `commit_check(expected, landed)` is pure (REQ-HARN-HARNESSP4-006)
- [ ] `python3 tools/sdd-skill-lint.py` exits 0; `python3 tools/sdd-gc.py --report` raises no new finding on this spec; Markdown well-formed

## Edge Cases

- **Leaf committed anyway in sequential mode** (`harness-write-scope.md`
  §Commit Ownership tolerates it): its paths are inside `committed_delta`, so
  they are in `expected`; because the range starts at `HEAD_before`
  **unconditionally** (§Signal and Token Family), they are inside
  `HEAD_before..HEAD_landed` too, so they count as landed and a
  compliant-but-eager leaf never renders a false `INCOMPLETE`. No conditional
  on the committed delta exists — `HEAD_gate` would have started the range
  after the leaf's commit (the gate is taken after the return), which is why
  it is not the comparand.
- **Nothing observed, nothing landed** (a read-only or no-op dispatch that
  reached `proceed`): `COMMIT: COMPLETE (0 paths)`. Review, verifier and red
  dispatches never commit and render no `COMMIT:` line at all (`telemetry.md`:
  `commit.token: null`).
- **Deleted path**: appears in `observed` (status `D`) and in `git diff
  --name-only` output; compared as a path like any other.
- **Rename**: both old and new paths are observed (`harness-write-scope.md`
  §Content-Hash Observation) and both appear in `--name-only` output (the
  deletion and the addition); compared as two paths. `--name-only` is used
  without rename detection (`--no-renames`) so the two sides agree.
- **Operator chose `stop` after `INCOMPLETE`**: the partial commit stands; the
  gate text names the un-landed paths; resumption's phase detection is
  unaffected (no artifact is involved).
- **`amend` on a shared branch that was already pushed**: out of scope — the
  orchestrator commits locally at gates and the PR happens at workstream end
  (`ws-integration.md`); if the operator has pushed mid-cycle, `amend` is still
  offered and the operator owns the force-push decision.

## Cross-Spec Consistency (XSPEC)

Run per `sdd-specs` Step 4b against `harness-write-scope.md`,
`harness-loop-control.md`, `harness-return-contract.md`, `telemetry.md`,
`skill-lint-v5.md`, `ws-integration.md`, `dispatch-snapshot-base.md`.

- No extractable Python/TS/Rust/Move type definitions in this spec — the
  contracts are shell/pseudocode fixtures. XSPEC operates on named fields and
  tokens.
- `observed writes` = `porcelain_delta ∪ committed_delta ∪ content_delta` is
  defined in `harness-write-scope.md` §Observation / §Content-Hash Observation
  with those names — consistent; the strict-set rule is stated there
  (REQ-HARN-HARNESSP4-004) and relied on here.
- `HEAD_before` / `HEAD_after` are the snapshot pair of
  `dispatch-snapshot-base.md` and `harness-write-scope.md` §Observation;
  `HEAD_before` is **reused** here as the range start with that meaning;
  `HEAD_gate` (prose name for the gate-time HEAD), `HEAD_landed` and
  `PRE_MERGE` are new names for shas taken *after* the pair — no collision.
- `RETURN.files_written`, `RETURN.commits` are fields of
  `harness-return-contract.md` §RETURN Block — consistent; the return-drift
  warning joins that spec's warning set (`KEYS MISSING`, `MULTIPLE_STATUS`,
  `FOREIGN_TOKEN`) as a fourth member and telemetry's `return.warnings` enum
  gains `RETURN_DRIFT` (`telemetry.md` §Record Schema).
- `telemetry.md` §Record Schema `commit.token` domain `COMPLETE | INCOMPLETE |
  null` equals the token family here — consistent.
- `skill-lint-v5.md` `REQUIRED` row pattern `COMMIT: (COMPLETE|INCOMPLETE)` —
  consistent with the two members.
- The gate order is stated **once** in `harness-loop-control.md` §Gate Signal
  Order; `orchestration.md` §v5 points there — no second statement.
- **No unresolved contradictions.**

## Open Questions

1. **`amend` and `gate.decision`** — **closed at the specs gate 2026-09-18**:
   `amend` maps to `other` and `telemetry.md`'s normalisation table now carries
   that row explicitly; the `commit` group records the outcome, so no enum
   member is added. Revisit only if `summarize` ever needs to count amends.
2. **Range start when the leaf committed in sequential mode** — **closed
   (specs review round 1, M2)**: the range is
   `git diff --name-only HEAD_before HEAD_landed` unconditionally (§Signal and
   Token Family, §Comparand Table); the earlier conditional (`HEAD_gate`
   normally, `HEAD_before` when the committed delta is non-empty) is withdrawn.
   The self-test fixture family (§Self-Test Helper) covers the eager-leaf case
   as the sequential mode's leaf-committed fixture.

## Implementation Questions

### Q-IMPL-HARNESSP4-003: `--self-test` flag accepted by the scope self-test tool
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Verification / Automated — `python3 tools/sdd-scope-check-selftest.py --self-test`
**Decision**: `tools/sdd-scope-check-selftest.py` gains an accepted `--self-test` flag; it is a no-op selector because running the fixtures is the script's only mode (its argparse previously knew only `-v` / `--keep`, so the spec's command would have exited 2).
**Rationale**: keeps the spec's and the plan's Close-out command literal and gives the tool the same invocation shape as `tools/sdd-skill-lint.py --self-test`, without adding a second mode. Bare invocation is unchanged.
**Date**: 2026-09-19 (harness-p4 Chunk 1)
