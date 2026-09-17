---
domain: ARB
last_updated: 2026-09-17
status: Approved
research_refs: [RS-HARNESSP2-001, RS-008]
workstream: harness-p2
---

# Requirements: Arbitrated Handoff Between Contradicting Review Rounds

## Overview

When review round N+1 contradicts review round N inside a fix loop, the
orchestrated loop must stop ping-ponging and hand both verdicts to the operator
(idea catalogue item F15, de-risked by RS-HARNESSP2-001 Q3). Every review round
is a fresh, isolated reader (REQ-REV-007, `sdd-review` §Bias Disclosure), so
disagreement between rounds is expected noise; the correct response is
arbitration, not treating the latest round as authoritative. Detection is
**mechanical and session-local**: the orchestrator already keeps each round's
Critical/Material lines verbatim (the compiled findings log of REQ-HARN-001 and
the repair packet's `findings`) and each fix dispatch's written delta (the
write-scope snapshot pair, REQ-HARN-021). Finding ids (`C1/M1`) are **not**
stable across rounds, so the comparison key is `(file:section, affects REQ
ids)`, never the id.

Standing constraints: REQ-ORCH-011 (the operator decides), REQ-ORCH-012 (the
pause shows verbatim lines and paths, never reviewer reasoning), REQ-ORCH-013
(the pause is ephemeral gate text), REQ-ORCH-014/REQ-HARN-027 (no new artifact —
the per-round lines are session state that already exists), REQ-HARN-001
(`FIX_LOOP_MAX` remains the terminal backstop). Arbitration is **default on**:
it only pauses (RS-HARNESSP2-001 decisions deferred to requirements).

## Requirements

### Detection

### REQ-ARB-HARNESSP2-001: Per-round finding keys are retained in session state
For every review round of a stage's fix loop the orchestrator must retain, in
session state only (no artifact, REQ-HARN-027), the round's `VERDICT:` and, for
each Critical and Material line, the verbatim line plus its key `(file:section,
affects)` parsed from the line's `[file:section]` reference and `affects
REQ-…` ids; and for every fix dispatch the set of `file:section` pairs it wrote
(REQ-ARB-HARNESSP2-005, falling back to file-level paths from REQ-HARN-021). A
line whose key cannot be parsed is retained with `section = ?` and
`affects = ∅` and participates only in file-level comparison. (see
RS-HARNESSP2-001 Q3 evidence)
**Acceptance**: `skills/sdd-orchestrate/references/loop-control.md` defines the
retained tuple next to the compiled findings log; no `docs/` file records it.
[Priority: must]

### REQ-ARB-HARNESSP2-002: Class (b) — new Critical/Material on approved ground
The orchestrator must flag a contradiction of class **(b)** when round N+1
raises a Critical or Material finding whose `file:section` was **not** among
round N's Critical/Material keys **and** is **not** among the `file:section`
pairs written by the intervening fix dispatch — the reviewer changed its mind
about content nobody changed. The comparison is a set operation over strings;
no semantic judgement is involved. Until section resolution exists
(REQ-ARB-HARNESSP2-005) the rule degrades to file level ("file not written by
the fix"), which over-fires when the fix touched the same file elsewhere; the
degradation must be labelled `(file-level)` in the pause. (see RS-HARNESSP2-001
Q3 class table)
**Acceptance**: a two-round fixture where round 2 raises `C1 … docs/spec/x.md
§C` after a fix that wrote only `docs/spec/x.md §A` and round 1 named only §A
renders `REVIEW: CONTRADICTION (… class b)`; the same fixture with round 2's
finding at §A renders no contradiction.
[Priority: must]

### REQ-ARB-HARNESSP2-003: Class (c) — verdict regression without new ground
The orchestrator must flag a contradiction of class **(c)** when round N's
verdict was `APPROVE_WITH_FIXES` and round N+1's is `REJECT` while (i) the fix
dispatch wrote only `file:section` pairs (or files, at file level) named by
round N's Critical/Material references, and (ii) every round-N+1
Critical/Material key is a subset of round N's keys ∪ the fix's written pairs.
This is the weaker signal and must be labelled `class c` in the pause. (see
RS-HARNESSP2-001 Q3 class table)
**Acceptance**: a fixture `APPROVE_WITH_FIXES → fix touching only round-1 refs
→ REJECT with the same refs` renders `class c`; changing round 2 to
`APPROVE_WITH_FIXES` renders no contradiction.
[Priority: must]

### REQ-ARB-HARNESSP2-004: Class (a) reversal is not detected — rendered as persisting only
A round-N+1 finding whose key equals a round-N key but asks for the opposite
change (a **reversal**) must **not** be treated as a contradiction: "opposite"
is semantic and not decidable by string comparison. Such a finding is rendered
as `(persisting)` in the compiled findings log exactly as today and, when the
cap is reached, surfaces through REQ-HARN-001's exhausted-log gate. This
limitation must be stated next to the two detected classes. (see
RS-HARNESSP2-001 Q3 class (a))
**Acceptance**: `loop-control.md` states that reversals are approximated as
`persisting`; a fixture with identical keys across rounds renders no
`CONTRADICTION` token.
[Priority: must]

### REQ-ARB-HARNESSP2-005: Section resolution of fix hunks [needs-code]
The orchestrator's write-scope snapshot must be extended to emit, for each path
written by a fix dispatch, the `file:section` pairs of its hunks: run `git diff
-U0 <HEAD_before> <HEAD_after> -- <path>` (plus the porcelain-only working-tree
diff for uncommitted writes), map each hunk's start line to its enclosing
`#`-heading in the after-image, and normalise the heading to the `§Name` form
`sdd-review` uses in `[file:section]` references. This is a small extension of
`references/write-scope.md` §3 and of the `tools/sdd-scope-check-selftest.py`
harness, not a new artifact; it also closes RS-008 Q5's recorded v1 limitation
(a) for Markdown paths. Non-Markdown paths resolve to `file:?` and fall back to
file-level comparison. This item needs code, not research; it is not a spike.
(see RS-HARNESSP2-001 Q3 Confidence — "needs code")
**Acceptance**: a fixture diff touching lines 40–58 under `## A` and line 120
under `## C` of `docs/spec/x.md` yields `{x.md:§A, x.md:§C}`; the pause of
REQ-ARB-HARNESSP2-006 shows `fix #1 wrote: docs/spec/x.md §A (hunks L40-58)`;
`tools/sdd-scope-check-selftest.py` gains a section-resolution scenario.
[Priority: must]

### Pause

### REQ-ARB-HARNESSP2-006: `REVIEW: CONTRADICTION` pause consumes no fix iteration
On class (b) or (c) the orchestrator must pause the stage gate with an own-line
token `REVIEW: CONTRADICTION (round N vs round N+1, class b|c) — stage:
<stage>, iteration N of MAX`, followed by, verbatim and side by side: round N's
verdict and Critical/Material lines with their keys; `fix #N wrote:
<file:section (hunks)>`; round N+1's verdict and lines, each new-ground line
annotated `<- section untouched by fix #N, not raised in round N`. Options:
`accept round N+1 (fix)` │ `accept round N (proceed, note)` │ `third opinion
(re-dispatch review)` │ `stop`. The pause is not a dispatch and not an
iteration: it must not increment the fix-loop counter (REQ-HARN-001), can only
occur at iteration ≥ 2 (two rounds are needed) and therefore always sits inside
the `FIX_LOOP_MAX` window; `accept round N+1 (fix)` is a normal fix re-dispatch
and **does** increment the iteration; `accept round N (proceed, note)` proceeds
and records the note where a gate decision already lands (the artifact's own
Open Questions, or a Q-IMPL entry for a spec) — never a review store
(REQ-ORCH-013); `stop` halts. The token is a fourth entry in the
`REVIEW: MALFORMED` / `RETURN: MALFORMED` pause family (`loop-control.md` §6)
and, like REQ-ORCH-018, is a stage-gate event only — the per-chunk gate shows
no review verdict and cannot raise it. The pause's class is recorded in
telemetry as `verdict.contradiction_class` (REQ-TELEM-HARNESSP2-001). Lint
carries the consumer row (REQ-LINT-HARNESSP2-001). (see RS-HARNESSP2-001 Q3
gate text)
**Acceptance**: the gate text fixture in `loop-control.md` matches the shape
above; after the pause and `accept round N (proceed, note)` the fix counter is
unchanged; removing the token from `sdd-orchestrate` text makes
`tools/sdd-skill-lint.py` exit 1.
[Priority: must]

### REQ-ARB-HARNESSP2-007: Third opinion — independent re-dispatch, two-of-three resolution
`third opinion` must dispatch a fresh review of the same stage artifacts
(reviews are idempotent and isolated by construction, REQ-ORCH-014), which is
**not** a fix iteration (the verifier re-dispatch rule). Its verdict and keys
must be compared against **both** prior rounds: if the third round's
Critical/Material keys agree with one prior round (set equality on keys, or
same verdict with keys ⊆ that round's keys ∪ fix pairs), the pause resolves in
that round's favour and the gate re-renders with the normal options; otherwise
the pause re-renders with three columns and only `fix | proceed | stop`. At
most one third opinion per contradiction. (see RS-HARNESSP2-001 Q3 options)
**Acceptance**: a fixture where round 3 matches round 1 re-renders the normal
gate with `iteration N of MAX` unchanged; a fixture where round 3 matches
neither renders three columns and no `third opinion` option.
[Priority: must]

### REQ-ARB-HARNESSP2-008: Every Critical and Material line carries a computable key
`sdd-review`'s report template must require `[file:section]` on every Critical
and Material line (already true) and must add `affects REQ-…` to Material
lines (today only Critical lines carry it) so the class (b)/(c) key is
computable on both tiers; a Material line with no affected requirement writes
`affects —`. The rest of the report format (REQ-REV-002) and review's scope
boundaries (REQ-REV-005/006) are unchanged. Lint carries a `REQUIRED` row on
the Material template line (REQ-LINT-HARNESSP2-001). (see RS-HARNESSP2-001 Q3
evidence)
**Acceptance**: `skills/sdd-review/SKILL.md`'s Material template line contains
`affects`; the linter's `REQUIRED` row fires when it is removed.
[Priority: should]
