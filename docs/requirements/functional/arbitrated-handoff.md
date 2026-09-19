---
domain: ARB
last_updated: 2026-09-19
status: Approved
research_refs: [RS-HARNESSP2-001, RS-008, RS-HARNESSP3-001, RS-HARNESSP4-001, RS-HARNESSP5-001]
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

### REQ-ARB-HARNESSP3-001: `W_N` includes regeneration writes — a regenerated deliverable is not new ground
`references/loop-control.md` §2a must redefine the retained per-round write set
as the union of the fix dispatch's written pairs **and** the written pairs of
every orchestrator-dispatched **regeneration of the stage deliverable** between
review round N and round N+1:

```
W_N := sections(fix[N] writes) UNION sections(regeneration writes since round N)
       # falling back to (file, *) only where section resolution is unavailable,
       # which is the existing rule and already labels the pause "(file-level)"
```

State it as a general **regenerated-not-patched** rule at the §2a level, not
inside the red section, because it applies to any stage whose pipeline leaf
rewrites its artifact wholesale between rounds (specs, plan, verification).
`fix[N]` generalises from "the fix dispatch" to "the loop dispatches between
round N and round N+1"; whether that is a rename or a sibling `regen[N]` whose
pairs union in is an implementation choice — the **union** is the contract.
Section resolution (REQ-ARB-HARNESSP2-005) is a function of a diff and applies
to a regeneration diff exactly as it applies to a fix's, so granularity is
**not** lost. The arbitration guarantee is not weakened: the pause exists to
catch a reviewer raising new Critical/Material on ground the previous round
approved **and the loop did not touch**, and a wholesale-regenerated file *was*
touched by the loop — so admitting it removes false positives only and cannot
mask a contradiction about a file the loop left alone. (see RS-HARNESSP3-001 Q3
— defect spec-read and run-corroborated (§B8: class (b) fires by construction on
every finding in a regenerated deliverable); remedy **constructed**, reusing the
already-specified section-resolution mechanism but not yet exercised by any run)
**Acceptance**: `references/loop-control.md` §2a's state schema and `W_N`
definition contain the union and the regenerated-not-patched rule;
`docs/spec/arbitrated-handoff.md` §Retained Per-Round State and §Contradiction
Classes match, and `docs/spec/adversarial-verify.md` §Fix-Loop Interaction
carries the cross-reference; a fixture in which round 1 `APPROVE`s, a pipeline
re-dispatch regenerates the deliverable, and round 2 raises Material findings in
regenerated sections yields **no** `REVIEW: CONTRADICTION` pause, while the same
fixture with the findings in a file the loop never touched still pauses as class
(b).
[Priority: must]
> **Carried to workstream `harness-p4` for live verification** (2026-09-18):
> the harness-p3 cycle closed this requirement `fail` meaning *not exercised*
> — every fix iteration patched rather than regenerated
> (`docs/ws/harness-p3/verification.md` §V3). REQ-ARB-HARNESSP4-001 directs the
> live exercise; the requirement text above is unchanged.

### REQ-ARB-HARNESSP4-001: REQ-ARB-HARNESSP3-001 is exercised live in this cycle and its non-pause is recorded
This cycle must exercise the unioned `W_N` of REQ-ARB-HARNESSP3-001 on a live
fix loop: the **first** `APPROVE_WITH_FIXES` stage review of the cycle is
answered by a fix dispatch instructed to **regenerate its deliverable
wholesale** (not patch it), and the next review round's Material or Critical
findings in the regenerated sections must **not** raise a class (b)
`REVIEW: CONTRADICTION` pause, while the arbitration rule stays armed for any
file the loop left alone. `docs/ws/harness-p4/verification.md` must record the
stage, the round numbers, the regenerated paths, the `regen[N]` entry the gate
retained (including the orchestrator-regenerated
`docs/requirements/traceability.md` where the stage produced one) and the
observed absence of the pause, so the carried `REQ-ARB-HARNESSP3-001` row in
`docs/ws/harness-p4/traceability.md` can read `pass` on run evidence rather than
fixture evidence. Decided at DISCUSS; the DONE rule of this cycle is that every
traced requirement reads `pass` and nothing closes as a deliberate `fail` — an
item that cannot be exercised live is descoped at replan, not failed. (workstream
`harness-p4`; see `docs/ws/harness-p3/verification.md` §V3 and §Next Steps
"V3 (not exercised)"; `docs/ws/harness-p4/kickoff.md` §Decided at DISCUSS)
**Acceptance**: the first `APPROVE_WITH_FIXES` fix dispatch of this cycle carries
the regenerate-wholesale instruction in its `{deliverable_contract}`; the
following review round's gate renders `VERDICT:` with no `REVIEW: CONTRADICTION`
line although it raised findings in the regenerated file; `verification.md`
§Criteria has an item recording the above with the round numbers and paths; the
`REQ-ARB-HARNESSP3-001` row in `docs/ws/harness-p4/traceability.md` reads `pass`
at DONE, and the aggregate regenerated from the per-ws files shows the same. The
aggregate carries **both** rows for `REQ-ARB-HARNESSP3-001` (the `harness-p3`
row `fail`, the `harness-p4` row `pass`); the **`harness-p4` row is
authoritative** for this requirement and the `harness-p3` row reads as history —
a reader, `sdd-gc.py` and `sdd-verify` consult the `harness-p4` row for the DONE
rule, and the duplicate id is legal under `ws-traceability.md`'s re-use rows.
[Priority: must]
> **Re-stated for workstream `harness-p5`** (Q-REQ-P5-A, 2026-09-19): the p4
> live exercise was **non-discriminating** — round 2 also raised a finding on a
> file the loop never touched, so class (b) fired under both readings and the
> two ARB cells were left empty (`docs/ws/harness-p4/verification.md` §Open
> Questions; they read `descoped` once REQ-WS-HARNESSP5-001 lands). The
> acceptance clause "no `REVIEW: CONTRADICTION` line although it raised findings
> in the regenerated file" is re-stated as: **no pause on findings in changed
> sections of the regenerated file; a pause on findings in unchanged sections**
> — the contract the offline fixture of REQ-ARB-HARNESSP5-002 asserts (A1/A2/A3).
> The requirement closes in `docs/ws/harness-p5/traceability.md` on that fixture,
> never on a second live loop; the text above is otherwise unchanged.

### REQ-ARB-HARNESSP4-002: the §2a replay fixture demonstrates the derived-artifact case explicitly
`references/loop-control.md` §2a's replay fixture must exercise the
Q-IMPL-HARNESSP3-017 clause it sits beneath: its `regen[1]` entry lists
`docs/requirements/traceability.md §(matrix)` labelled as an **orchestrator
regeneration** (distinct from the leaf-written `docs/ws/<id>/traceability.md`),
and finding `M3` writes its path in full so a reader can tell which of the two
files it is on. Today `regen[1]` names only the per-workstream file and `M3`
names `traceability.md` bare, so the derived-artifact case the prose states is
demonstrated only by an ambiguity. Skill-side text only. (workstream
`harness-p4`; see `docs/ws/harness-p3/verification.md` §V10 — recorded: no,
only implicitly)
**Acceptance**: `grep -n 'docs/requirements/traceability.md' skills/sdd-orchestrate/references/loop-control.md`
hits inside the §2a fixture's `regen[1]` block with an orchestrator-regeneration
label, no bare `traceability.md` remains in the fixture's finding lines, and
`python3 tools/sdd-skill-lint.py` exits 0.
[Priority: should]

### REQ-ARB-HARNESSP4-003: `docs/spec/arbitrated-handoff.md` §Retained Per-Round State carries `regen[N]`
The schema block of `docs/spec/arbitrated-handoff.md` §Retained Per-Round State
must carry the `regen[N]` line and the `W_N` union prose that §Contradiction
Classes of the same spec and `references/loop-control.md` §2a already carry, so
a reader taking that section as the schema of record builds the amended state
rather than the pre-REQ-ARB-HARNESSP3-001 one. The spec was Approved and frozen
in p3, so the gap was recorded rather than edited; this cycle amends it.
(workstream `harness-p4`; see `docs/ws/harness-p3/verification.md` §V11 — the
gap is real, confined to the spec's internal consistency)
**Acceptance**: §Retained Per-Round State's fenced schema shows `round[N]`,
`fix[N]` and `regen[N]` with the union; the section's text and `loop-control.md`
§2a agree on the definition (a side-by-side read at specs); `python3 tools/sdd-gc.py --report`
raises no new finding on the amended spec.
[Priority: should]

<!-- REQ-ARB-HARNESSP5-NNN: workstream-prefixed additions for the harness-p5
     cycle (RS-HARNESSP5-001; marker 4, per docs/spec/ws-ids.md). -->

### REQ-ARB-HARNESSP5-001: `W_N` stays diff-based — a byte-identical re-emission is not a regeneration write
The retained write set `W_N` of `docs/spec/arbitrated-handoff.md` §`W_N` and
`references/loop-control.md` §2a must keep **diff-based section resolution** for
a regenerated artifact: a regeneration that re-emits a section byte-identically
adds **nothing** to `W_N`, and a round-N+1 Critical/Material line keyed on such a
section is on ground round N saw **unchanged** — the class (b) signal, not the
false positive REQ-ARB-HARNESSP3-001 removed. The provenance reading
`regen[N] = (file, *)` for a wholesale dispatch whose diff exists is **not**
adopted; `(file, *)` remains reserved for a *missing* diff (untracked or
non-Markdown path, §Section Resolution / self-test F8). Both texts gain one
clarifying sentence stating this — the Approved sentence is the required record.
`arbitrated-handoff.md` **may** additionally gain one Q-IMPL entry recording the
reading against Q-IMPL-HARNESSP3-010 (which decides which dispatches feed
`regen[N]`, not granularity); left at specs' discretion so the reading is not
stated in three places alongside REQ-QIMPL-HARNESSP5-001's fold-ins. Ratified as Q-REQ-P5-A in
`index.md`. (workstream `harness-p5`; see RS-HARNESSP5-001 §Q1 — three Approved
sources agree; under provenance a `regenerate-wholesale` contract would become
blanket immunity for the whole file and the §`W_N` guarantee "cannot mask a
contradiction" would break; the p4 O1 pause was a true positive)
**Acceptance**: `grep -n 'byte-identical' docs/spec/arbitrated-handoff.md skills/sdd-orchestrate/references/loop-control.md`
hits inside §`W_N` and §2a respectively with matching wording; if a
`Q-IMPL-HARNESSP5-*` entry is added to `arbitrated-handoff.md`, it cites
Q-IMPL-HARNESSP3-010 and names the fixture of REQ-ARB-HARNESSP5-002 as its
evidence; scenario A1 of
that fixture yields `class b` with two annotated keys under this rule and no
token under the provenance rule, printed side by side; `python3 tools/sdd-skill-lint.py`
exits 0.
[Priority: must]

### REQ-ARB-HARNESSP5-002: a deterministic offline fixture closes both ARB rows — no second live loop
The arbitration rule must be verified by a frozen fixture under
`tools/fixtures/arbitration-harness-p4-regen-2026-09-19/` — `before.md`,
`after.md` (byte-identical outside `§(preamble)`, `§Operator Tasks`,
`§Completed`), `round-1.txt` (`APPROVE_WITH_FIXES`, keys on the two changed
sections), `round-2.txt` (two Material lines keyed on the plan's **unchanged**
`§Conventions` and `§Verification Hand-off`, confined to the regenerated file)
and `dispatch.txt` (observed writes `{docs/ws/harness-p4/plan.md}`,
`regenerate: true`, `by: leaf`) — run as three scenarios of
`tools/sdd-scope-check-selftest.py --self-test`: **A1** (p4 case: `class b`, two
annotated keys diff-based; no token provenance — the discriminating case),
**A2** (B8 case, findings in changed sections only: no token either way — the
REQ-ARB-HARNESSP3-001 false positive stays removed), **A3** (control: one key
on an untouched second file: `class b`, one key either way). The runner parses
rounds with the §2a key rule, computes `W_1` via `resolve_sections()`, and
applies the class (b)/(c) table through a pure
`arbitrate(round_n, round_n1, w_n) -> (class | None, annotated_keys)` helper.
`tools/fixtures/README.md` states per fixture that this one is a
**reconstruction** of the p4 implement-stage gate from
`docs/ws/harness-p4/verification.md` §1 and plan O1, not a byte capture.
`arbitrated-handoff.md` §Automated names A1–A3 (its `test_class_b_*` names stop
being prose-only). This closes the carried `REQ-ARB-HARNESSP3-001` and
`REQ-ARB-HARNESSP4-001` rows in `docs/ws/harness-p5/traceability.md` on fixture
evidence — the DONE rule of this cycle is every traced row `pass`, nothing a
deliberate `fail`, and an item that cannot be exercised is descoped at replan
(kickoff §Decided at DISCUSS). Cost sized at **nine** files (selftest, five
fixture files, README, `arbitrated-handoff.md`, `loop-control.md`) plus this
workstream's `traceability.md`. (workstream `harness-p5`; see RS-HARNESSP5-001
§Q1 fixture table; runner placement is a plan-level Open Question — a separate
`tools/sdd-arbitrate-selftest.py` is acceptable with the same assertions)
**Acceptance**: `python3 tools/sdd-scope-check-selftest.py --self-test` exits 0
with A1–A3 listed and A1's provenance column printed alongside; deleting one
`round-2.txt` line or flipping `§Conventions` to a changed section in `after.md`
in a temp copy makes A1 fail; `verification.md` §Criteria records the run as the
evidence for both ARB rows, which read `pass` at DONE in
`docs/ws/harness-p5/traceability.md` and in the regenerated aggregate (the
`harness-p5` rows are authoritative; the `harness-p3` `fail` and `harness-p4`
`descoped` rows read as history, per REQ-WS-HARNESSP5-001).
[Priority: must]

### REQ-ARB-HARNESSP5-003: the §2a leading-ordinal strip rule is stated in the spec's key table
`docs/spec/arbitrated-handoff.md`'s finding-key table should carry the
leading-ordinal strip rule that `references/loop-control.md` §2a applies when
computing `K_N` (a `C1`/`M2` ordinal prefix is stripped before the
`[file:section]` key is read), so the spec and the reference agree on the key
function the fixture of REQ-ARB-HARNESSP5-002 exercises. The spec's §Open
Questions item 3 already carries the strip rule as a Default; that open question
is **closed** in the same edit that adds the rule to the key table (marked
resolved, pointing at the table row). (workstream `harness-p5`; see
`docs/ws/harness-p4/verification.md` verifier advisory — absent from the spec
table, present in §2a)
**Acceptance**: a side-by-side read at specs shows the strip rule in both texts
and §Open Questions item 3 reads closed;
the A1–A3 key parser implements it and a round line with and without the
ordinal resolves to the same key in `--self-test`; `python3 tools/sdd-gc.py --report`
raises no new finding on the amended spec.
[Priority: should]
