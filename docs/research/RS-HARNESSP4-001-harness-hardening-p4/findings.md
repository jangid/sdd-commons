---
id: RS-HARNESSP4-001
workstream: harness-p4
topic: harness-hardening-p4
status: Complete
date: 2026-09-18
last_updated: 2026-09-18
questions:
  - "Q1 — COMMIT: signal under fan-out: what COMMIT: compares against at the per-leaf gate and at the merge step, whether a silently dropped path at merge needs a third token member or INCOMPLETE covers it, where it renders in the loop-control.md §5 order, and the cost in files touched"
  - "Q2 — Independent expected source for records-vs-expected: what durable, orchestrator-independent count of dispatches expected can be derived from without a loop log or any new artifact under docs/, which candidate is checkable post-cycle by sdd-telemetry.py summarize, and which failure modes it detects and still cannot"
budget: "One spike, <= 30 tool calls, 0 test runs, desk research plus one optional scratch-repo probe for Q1. Consumed: 22 tool calls, 1 probe run (in a throwaway repository under $TMPDIR; nothing committed or checked out in this repository), 0 test runs."
research_refs: [RS-008, RS-HARNESSP2-001, RS-HARNESSP3-001]
# Note: `last_updated`, `workstream`, `topic` and `research_refs` are extensions
# beyond the sdd-research findings template (staleness detection, marker-4
# workstream attribution, prior-research linkage) — same convention as RS-008,
# RS-HARNESSP2-001 and RS-HARNESSP3-001.
---

# Research: Harness Hardening, Part 4 — the `COMMIT:` signal under fan-out and an independent `expected` source for telemetry

## Questions

The two questions of `docs/ws/harness-p4/kickoff.md`, condensed in the
frontmatter above. Both originate in the harness-p3 verify session of
2026-09-18: Q1 in `docs/ws/harness-p3/verification.md` §V14 (three independent
findings — blue Chunk 7's dropped `git add`, review C1, red R4 — with one root
cause), Q2 in §Post-DONE Findings P2 (zero `verifier` and zero `fix` records
across a cycle that ran eight verifiers and three redos, while
`records-vs-expected` reported no gap).

Everything else in the p4 scope was settled at DISCUSS and is restated without
change under §Decided at DISCUSS; this spike does not re-open RS-008,
RS-HARNESSP2-001 or RS-HARNESSP3-001.

**Evidence base.** Spec citations refer to the files as they stand at
`92b4d67`. Run evidence is the frozen fixture
`tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` (20 records, read-only)
and the p3 commit range `77e84fe..b0b69be` in this repository's history. One
probe ran for Q1 in a scratch repository under `$TMPDIR`; its transcript is
[`evidence-appendix.md`](evidence-appendix.md) §A. The fixture cross-check that
carries Q2 is §B of the same file; every fixture number quoted below was
recomputed from the fixture for this revision (review round 1 found the review
formula did not reproduce its own prose — see §Q2).

**Confidence vocabulary** (carried from RS-HARNESSP3-001): **probe-evidenced**
(reproduced mechanically in this spike), **spec-read** (established by reading
committed spec / reference / tool text), **constructed** (proposed here, never
exercised).

**Classification legend**, per the kickoff's success criteria:

- **mechanical** — spec / reference / template text only.
- **code** — a change to `tools/*.py` (including a new self-test fixture).
- **design-decision-for-requirements** — defines or changes a gate signal,
  detection rule or record field; requirements should ratify it rather than
  inherit it as an edit.

---

## Findings

### Q1 — `COMMIT:` signal under fan-out

**Answer**: one signal, two members, one comparand rule that holds in every
mode —

```
landed   := git diff --name-only <HEAD_gate> <HEAD_landed>      # what actually reached the integration line
expected := observed_writes                                      # sequential and fix dispatches; RETURN.files_written is NOT a term (see below)
          | leaf committed delta (base..tip)                     # fan-out, at the merge step
COMMIT: COMPLETE (N paths)
COMMIT: INCOMPLETE (k observed, not landed: <paths>[; j landed, not observed: <paths>])
```

`HEAD_gate` is the integration-line HEAD when the gate decision is taken;
`HEAD_landed` is its HEAD immediately after the orchestrator's commit
(sequential) or merge (fan-out), *before* any separate bookkeeping commit.
**No third member is needed**: `INCOMPLETE` covers every drop the probe could
produce, and the single way a path vanishes between leaf and integration line
is not a merge at all (case 5 below). The signal renders **after `SCOPE:`**
where it is computable before the decision (fan-out per-leaf gate) and as a
**post-decision closing line of the same gate** where the commit it observes
is the *consequence* of the decision (sequential per-chunk and stage gates,
fan-out merge step). That second placement is what the kickoff's "after
`SCOPE:` seems right" did not anticipate, and it is the design decision for
requirements.

**Evidence** (probe §A, five cases in a scratch repository):

1. *Sequential, the V14 case.* The leaf writes `a.txt b.txt docs/plan.md`; the
   orchestrator `git add`s two of them. `observed − git show --name-only
   --format= HEAD` = `docs/plan.md`, and the porcelain leftover reads
   ` M docs/plan.md`. The set difference reproduces Chunk 7's omission
   mechanically. **Probe-evidenced.**
2. *Sequential, inverse error.* The orchestrator commits `stray.txt`, which no
   leaf wrote: `committed − observed` = `stray.txt`. V14's aside ("would also
   have caught the inverse") holds; it is the second clause of `INCOMPLETE`,
   not a third member — one set comparison rendered in both directions.
   **Probe-evidenced.**
3. *Fan-out, fast-forward merge.* The leaf makes two commits on its branch
   (`a.txt`, then `b.txt`); the orchestrator merges and git fast-forwards.
   `git show --name-only --format= HEAD` reports **only `b.txt`** — the last
   leaf commit — whereas `git diff --name-only PRE HEAD` reports `a.txt b.txt`.
   **V14's proposed command is wrong for fan-out**: it would render a false
   `COMMIT: INCOMPLETE` on every multi-commit leaf. **Probe-evidenced.**
4. *Fan-out, true merge commit.* The integration branch advanced (a
   bookkeeping commit) before the leaf's branch merges. `git show --name-only
   --format= HEAD` on the merge commit is **empty** (a clean merge has no
   combined diff to show); `git diff --name-only PRE HEAD` reports `a.txt
   c.txt`, identical to the leaf's committed delta `base..tip`.
   **Probe-evidenced.** The same defect reaches the sequential path whenever
   the orchestrator makes more than one commit at a gate — which marker `4`
   does at every implement chunk (`feat(...)`, then `docs(traceability):
   regenerate aggregate after Chunk N`; `write-scope.md` §7
   aggregate-regeneration row; 8 of the 20 commits in `77e84fe..b0b69be` are
   such regenerations). A `git show HEAD` taken after the regeneration commit
   would name only `docs/requirements/traceability.md`. Hence the two-sha
   range, captured before bookkeeping, is the comparand in every mode.
5. *Fan-out, conflict → abort → redo-by-re-derivation.* The first leaf commits
   `a.txt b.txt`, conflicts on `a.txt`, and the merge is aborted per
   `fan-out.md` §3c; the redo leaf commits only `b.txt`. `diff PRE HEAD` after
   the redo merge = `b.txt`. This is the **only** way the probe could make a
   path vanish between leaf and integration line — and it is not a silent
   merge drop: the redo leaf is a **new dispatch with its own snapshot,
   committed delta and per-leaf gate** (§3a.v), so its `expected` set is the
   redo's and the first attempt's set is discarded by design. A clean `git
   merge` (cases 3–4) cannot lose a path: `diff PRE HEAD` equalled the leaf
   delta both times. **Probe-evidenced for the merge; spec-read for the redo
   semantics.** So **no third token member** — if a drop at re-derivation
   matters, it is a *repair-packet* concern (the redo prompt could carry the
   aborted attempt's path list as advisory), not a `COMMIT:` concern.

**What `COMMIT:` compares, per gate** (spec-read against `write-scope.md` §3,
§7 and `fan-out.md` §3a.v, §3b, §3e):

| Gate | `expected` | `landed` | When computable |
|---|---|---|---|
| sequential per-chunk / stage gate, on `proceed` | observed writes (porcelain ∪ committed ∪ content deltas) **only** — `RETURN.files_written − observed` is a return-drift warning owned by `return-contract.md`, never a `COMMIT:` term | `git diff --name-only HEAD_gate HEAD_landed`, taken right after the orchestrator's commit and **before** the aggregate-regeneration commit | post-decision |
| fan-out **per-leaf** gate | observed writes in the worktree | committed delta `git diff --name-only <base> <tip>` — the write-scope check's own term (b) | pre-decision — renders after `SCOPE:` |
| fan-out **merge step** (§3b), per branch | that leaf's committed delta `base..tip` | `git diff --name-only PRE_MERGE HEAD` on the integration branch | post-`proceed`, at merge |

At the per-leaf gate the comparison reduces to **`observed − committed delta`
= the leaf's uncommitted writes**, which worktree teardown (§3d) would discard
— a path the leaf wrote but never committed on its branch is exactly a
`COMMIT: INCOMPLETE` for a leaf. A second per-leaf clause checks
`RETURN.commits` ⊆ `git rev-list <base>..<tip>` (a leaf claiming a sha not on
its branch); it costs one `rev-list` and closes the return side of the same
gap. Both use sets the harness already computes, so V14's "no new leaf, no new
counter" holds.

**Why `RETURN.files_written` is not a term of `expected` (sequential).** A
path the leaf *claims* in `RETURN.files_written` but never wrote — or wrote
and then reverted, so no porcelain, committed or content delta observes it
— cannot land, and a comparand that unioned the claim into `expected` would
render `COMMIT: INCOMPLETE (observed, not landed)` for a defect of the
leaf's *return*, not of the orchestrator's commit: a false pause. So
`expected` in sequential mode is **observed writes only**, and
`RETURN.files_written − observed` is surfaced as a **return-drift warning**
(the field already belongs to `return-contract.md`, which owns
return-side defects) and is excluded from `COMMIT:`. This is the sequential
analogue of the fan-out `RETURN.commits ⊆ rev-list` clause — both keep a
leaf's return error out of the landed-vs-observed comparison. Recorded as a
requirements decision under §Implications for Design. **Constructed.**

**Position in the `loop-control.md` §5 order.** The order is "signals surface
in the order they are produced", with the options rendering last. `COMMIT:`
for a sequential dispatch is *produced by* the `proceed` option, so it cannot
sit between `SCOPE:` and `CHUNK_VERDICT:` there without asserting a commit that
has not happened. Two placements were weighed:

- **(i) post-decision closing line of the same gate** — rendered immediately
  after the commit/merge, before the next dispatch. On `INCOMPLETE` it pauses
  with `amend (add the missing paths to the commit) | accept (note) | stop`.
- **(ii) deferred to the next gate**, the way `TELEMETRY: rec <n>` asserts the
  *previous* append.

Evidence selects **(i)**: V14's omission survived *two* gates and a commit and
was caught only by a later human read; under (ii) the next dispatch would
already have run against the un-landed tree, and the last gate of a stage has
no "next gate" until the review. The `TELEMETRY:` precedent is not binding —
telemetry is "never load-bearing" by contract (`telemetry.md` §3), while
`COMMIT:` exists precisely to be load-bearing. So §5 gains an item **8**,
"post-decision: `COMMIT:`", stated once there and summarised in `SKILL.md`
§The gate; at the fan-out per-leaf gate the same line renders in position 2b
(after `SCOPE:`, before `CHUNK_VERDICT:`), because the data exists before the
decision. The kickoff's "after `SCOPE:`" is therefore right for the per-leaf
gate only. **Constructed** — never exercised.

**Cost in files touched.** The checkable set is the output of

```
grep -rlE 'SCOPE: (CLEAN|VIOLATION)' skills docs/spec tools CLAUDE.md | sort
```

run at `92b4d67`: **17 files** (a looser `grep -rl 'SCOPE:'` over the same
roots finds 22, the extra five being files that cite the token inside a table
or a return-contract field list — `docs/spec/harness-loop-control.md`,
`harness-return-contract.md`, `overview.md`, `skill-updates.md`,
`references/return-contract.md` — none of which states the gate line). The 17
are partitioned below by one rule: a file that **states or renders the gate
line** (defines the check, lists the §5 order, or shows a gate block fixture)
needs a sibling `COMMIT:` statement; a file that only **cites** the token as
an example of an existing signal does not. The partition is spec-read for the
files this spike opened (`write-scope.md`, `loop-control.md`, `fan-out.md`,
`SKILL.md`, `USAGE.md`, `telemetry.md` ×2, `CLAUDE.md`) and by role for the
rest; the plan should confirm the by-role rows before sizing.

| File | Disposition | Change | Class |
|---|---|---|---|
| `skills/sdd-orchestrate/references/write-scope.md` §7 | touch | define the check, the comparand table above, the token, the `amend \| accept \| stop` options — the commit-ownership section is its natural home | mechanical |
| `skills/sdd-orchestrate/references/loop-control.md` §5 | touch | item 8 (post-decision) and the per-leaf 2b placement | mechanical |
| `skills/sdd-orchestrate/references/fan-out.md` §3a.v, §3b | touch | per-leaf clause; merge-step comparand `PRE_MERGE..HEAD` | mechanical |
| `skills/sdd-orchestrate/references/dispatch-templates.md` | touch (by role) | the templates pin `RETURN:` verbatim; the per-leaf gate block fixture, if one is shown, gains the 2b line | mechanical |
| `skills/sdd-orchestrate/SKILL.md` §The gate | touch | one-line summary | mechanical |
| `skills/sdd-orchestrate/USAGE.md` §7b | touch | gate block fixtures gain the closing line | mechanical |
| `CLAUDE.md` §Gate vocabulary | touch | one sentence | mechanical |
| `docs/spec/harness-write-scope.md` | touch, after requirements ratify | the contract (`§COMMIT:`); no new spec file is required | mechanical |
| `docs/spec/orchestration.md` §v5 | touch (by role), after requirements ratify | gate-vocabulary summary, mirroring `CLAUDE.md` | mechanical |
| `docs/spec/harness-chunk-verifier.md`, `dispatch-snapshot-base.md`, `adversarial-verify.md`, `evaluation.md` | cite-only (by role) | none — each names `SCOPE:` as a neighbouring signal | — |
| `skills/sdd-orchestrate/references/telemetry.md`, `docs/spec/telemetry.md` | cite-only **unless** requirements add a `commit: {token, missing_n, extra_n}` record group | counts and enums within the schema rule | design-decision-for-requirements |
| `tools/sdd-scope-check-selftest.py` | touch | a `commit_check(expected, landed)` helper and one fixture per probe case (5 scenarios) | code |
| `tools/sdd-eval.py` | cite-only (by role) | none — the token appears in eval fixture text | — |
| `tools/sdd-skill-lint.py` (not in the grep set — its REQUIRED rows use their own patterns) | touch | one REQUIRED row: `COMMIT: COMPLETE \| INCOMPLETE` present in `loop-control.md` and `SKILL.md` (pattern must not match `SCOPE:`-only files, as the `CHUNK_VERDICT:` row already guards) | code |
| `tools/sdd-telemetry.py` | touch **only if** the `commit` record group is adopted | write and summarise the group | design-decision-for-requirements |

Tally: **9 files mechanical + 2 code**, plus 3 more (`tools/sdd-telemetry.py`
and the two telemetry texts) if the record group is adopted. **Overall
classification**: design-decision-for-requirements for the signal's existence,
its post-decision placement and the two-sha comparand rule; mechanical for
every restatement; code for the fixture and the lint row.

**Confidence**: High on the comparand (probe-evidenced in all five cases, and
the `git show` failure modes are deterministic git behaviour); Medium on the
placement (constructed — the pause options and the interaction with an
`INCOMPLETE` at the *last* chunk before the implement review are untested);
Medium on the file count (the set is reproducible by the command above; the
touch/cite partition of the by-role rows is not yet read-verified).

---

### Q2 — Independent `expected` source for `records-vs-expected`

**Answer**: derive `expected` from **cross-field implications already present
in the records** — a record that carries a sibling dispatch's *verdict*, a
*redo* count, a *fix-producing gate decision* or a *fix-only dispatch reason*
proves that sibling dispatch happened — and, optionally, from the **plan's
chunk count** as a durable floor. Per session:

```
implied.verifier := Σ over records with verdict.chunk_verdict != null and kind != verifier of (1 + dispatch.redo)
                                                                       # the redo's first attempt was verified too
implied.pipeline := Σ over implement kind == pipeline records of (1 + dispatch.redo)   # a redo is a re-dispatch
implied.review   := #records with kind != review and verdict.review_verdict != null    # one per carrying record
implied.red      := #records with kind != red and verdict.red_verdict != null
implied.fix      := #records with gate.decision ∈ {loop-back-to-fix, fix}              # each such decision dispatches one fix
                  + #records with kind != fix and dispatch.reason ∈ {red_break}        # a reason only a fix dispatch carries
missing.<kind>   := max(0, implied.<kind> − recorded.<kind>), matched per stage        # never negative, never cross-stage
missing.fix      := 0 when the implied fix is present as a record of another kind      # a mis-typed fix (reported by --lint), not a missing append;
                                                                                       # only an implied fix with NO carrying record counts as missing
expected         := highest dispatch.seq + Σ missing.<kind>
floor (--plan)   := chunk_count(plan) pipeline dispatches at implement, × 2 when any chunk record has a non-null chunk_verdict
```

`dispatch.redo` is read as 0 when null. `summarize` prints, beside the
existing `records-vs-expected:` line, one `implied vs recorded` line per kind,
and `--lint` validates every field against its declared domain (P3) plus the
cross-field rules: a `kind: pipeline` record with `dispatch.iteration >= 1`
whose predecessor at the same stage decided `loop-back-to-fix`, **or** whose
`dispatch.reason` is `red_break`, is a mis-typed fix; a non-null
`chunk_verdict` on a non-verifier record with no verifier record for that chunk
is a missing append.

**Why this is independent of `seq` and of the writer's discipline.** The
failure P2 describes is a writer that *does not append and does not
increment*. Every implication above is triggered by a field the writer **did**
fill — it wrote `chunk_verdict: PASS` onto the pipeline record because that is
where the verifier's verdict was visible at the gate. The writer cannot
under-report the sibling dispatch without also blanking a field it had no
reason to blank. It is not a loop log, not a new artifact, and reads nothing
but the file `summarize` already reads.

**Evidence** (fixture cross-check, §B; the fixture is the entire p3 record set,
20 records; each number below is the formula's output on that file):

- **Verifiers.** 9 implement records; **8** carry `chunk_verdict: PASS` (every
  chunk record; the 9th is the implement review, seq 14). Three of the eight
  carry `dispatch.redo: 1` (seq 7, 10, 13), so `Σ (1 + redo)` = 8 + 3 =
  **11** implied verifiers; **0** `verifier` records exist; `missing.verifier`
  = 11. The P2 defect, now *computable*.
- **Redos.** `dispatch.redo == 1` with `reason: VERIFIER_FAIL` on seq 7 and
  10 and `reason: REVIEW` on seq 13 — the **3 redos** of P2. Each chunk record
  is the *redo* dispatch; the first attempt's record (whose gate decision was
  `fix`) is absent. `implied.pipeline` at implement = 8 + 3 = **11**, recorded
  8, `missing.pipeline` = 3. P2's "~11 never recorded" is the 8 + 3 reading
  (eight verifiers with no record of their own kind plus three first attempts);
  the full implication count is **14 missing at implement** (3 first-attempt
  pipeline + 11 verifier). Both readings are reported so requirements can pick
  the definition.
- **Reviews.** Six non-review records carry `review_verdict:
  APPROVE_WITH_FIXES`: seq 1–5 (`pipeline` at research, research, requirements,
  specs, plan) and seq 20 (the `kind: gate` record at verify). So
  `implied.review` = **6** per carrying record. Round 1 of this spike's review
  found the earlier formula, keyed on distinct `(stage, fix_iteration)`,
  yields 4 for seq 1–5 — seq 1 and seq 2 both read as research at fix
  iteration 1 in the §B listing (`gate.fix_iteration`; `dispatch.iteration` is
  null on seq 1 and 1 on seq 2) — while the prose claimed ≥ 5; counting per
  carrying record (equivalently, distinct `(stage, dispatch.seq)`) is the fix. Recorded `review` records: **2** (seq
  14 implement, seq 17 verify). Matched per stage, seq 20's verdict sits at
  verify where seq 17 exists, so it is covered; the five at research ×2,
  requirements, specs and plan have no review record at all —
  `missing.review` = **5**. The incompleteness P2 measured at implement is
  present at every earlier stage.
- **Red.** `red_verdict: BROKEN` on the non-red seq 20 → `implied.red` =
  **1**; two `red` records exist (seq 16, 19, both verify), so
  `missing.red` = 0 — the verdict on seq 20 duplicates seq 19's, at the same
  stage.
- **Fix dispatches.** Seq 1 has `gate.decision: loop-back-to-fix`
  (→ 1); seq 18 is `kind: pipeline`, `reason: red_break` (→ 1); no other
  record satisfies either clause, so `implied.fix` = **2**, recorded `fix` =
  0. The two carrying records are seq 2 (`pipeline`, research, iteration 1,
  after seq 1's `loop-back-to-fix`) and seq 18 (`pipeline`, verify, iteration
  1, `reason: red_break`) — both fix dispatches recorded under the wrong kind,
  as P3 observed for seq 18. Seq 18 is reachable **only** through the
  `dispatch.reason` clause: its predecessor seq 17 has `gate.decision: null`,
  not `loop-back-to-fix`, so a rule keyed on the gate decision alone misses
  it. The seq-based check cannot see either. Because each implied fix *is*
  present as a record (under the wrong kind), `missing.fix` = **0** by the
  mis-typed rule in the formula block — the two are `--lint` findings, not
  missing appends, and do not enter `expected`.
- **`expected` on the fixture.** highest `seq` = 20; Σ missing = 11
  (verifier) + 3 (pipeline) + 5 (review) + 0 (red) + 0 (fix — both implied
  fixes exist as mis-typed `pipeline` records, so by the `missing.fix` rule
  they are `--lint` findings, not missing appends) = 19; `expected` = **39**
  dispatches against **20** records. Today's
  `summarize` reports 20 vs 20 and no gap.
- **`--lint` findings the fixture already yields**, beyond P3's `kind: gate`
  (seq 20): `git.head_after: "HEAD"` (seq 5, a literal, not a sha);
  `git.head_before/after` **null on all nine implement records** (seq 6–14);
  40-character shas on seq 15–20 against the schema's "short sha"; and an
  **undeclared key `git.commit_n`** on seq 15–20 — key-set drift the "fixed
  key set" rule (`telemetry.md` §Record Schema) forbids. Five distinct domain
  classes in one 20-record file; the R1 fix covered one field.
- **Not counted, flagged for `--lint`.** Seq 3, 4 and 5 carry `reason: REVIEW`
  and `iteration: 1` although their predecessors decided `proceed`. They are
  either fix dispatches whose gate decision was recorded as `proceed` or
  first dispatches with a mis-labelled reason; the fixture cannot say which,
  so the fix implication deliberately does not claim them (a `REVIEW` reason
  also appears on the legitimate chunk redo seq 13). `--lint` should warn on
  "`reason: REVIEW` with no preceding `loop-back-to-fix` at the stage".

**The other candidates, and why they are rejected as the source of `expected`:**

| Candidate | Durable? | Orchestrator-independent? | Verdict |
|---|---|---|---|
| plan chunk count × dispatch shape | yes (`docs/ws/<id>/plan.md`) | yes | **accepted as a floor**, not as `expected`: the redo count and the verifier opt-in are session state (`Redo: N` and the implement-gate opt-in are never written to the plan — `loop-control.md` §1a; only a cap hit reaches the blocked-task note), so the plan yields `chunk_count` pipeline dispatches and `chunk_count` verifiers *if enabled*, never the redos. Reader-side, opt-in via `--plan`, no new artifact |
| git commits between `head_before` and `head_after` | yes (history) | yes | **rejected**: (1) the fixture's `git` heads are **null on every implement record**, so there is no range to count for exactly the stage that lost records; (2) commits are not dispatches — `77e84fe..b0b69be` holds **20 commits for 8 chunks** (8 features, 8 aggregate regenerations, 1 plan, 1 fix-up, 1 docs), and verifier / review / red dispatches produce zero commits, so the count is blind to the kinds that went missing. Usable only as a `--lint` consistency check: a `proceed` implement record whose `head_before == head_after` is suspicious |
| gate blocks the operator saw | no | — | **rejected** (not durable), as the kickoff anticipated |
| cross-field implications (above) | yes (in the file) | yes — the writer filled the verdict, redo, decision and reason fields for its own gate rendering, not for the count | **accepted** |

**What the recommended source detects** (stated explicitly, per the kickoff):

1. A **verifier** dispatch that got no record while its verdict sits on the
   chunk record — 11 in p3 (8 chunks + 3 redone first attempts).
2. A **redo's first attempt** that got no record — via `dispatch.redo ≥ 1`
   (3 in p3).
3. A **stage review** that got no record while its verdict sits on the
   pipeline record — 5 in p3 (research ×2, requirements, specs, plan),
   previously invisible; the sixth carrying record (seq 20) is covered by the
   recorded verify review.
4. A **fix** dispatch mis-typed as `pipeline` — 2 in p3, by two different
   clauses: seq 2 through the preceding `loop-back-to-fix` on seq 1, and seq
   18 **only** through `dispatch.reason == red_break` (its predecessor's gate
   decision is null, so the decision clause alone does not reach it).
5. A **red** dispatch that got no record while `red_verdict` sits elsewhere —
   0 missing in p3 (seq 20's verdict is covered by the recorded seq 19).
6. Every **domain and key-set violation** in the file (`--lint`, P3): five
   classes found in the fixture today.
7. The original class — `seq` incremented, record lost — is retained because
   `expected` starts from the highest `seq` and only adds the implied
   shortfall.

**What it still cannot detect:**

1. A dispatch **and** its gate that left no trace on any record — a chunk
   whose pipeline *and* verifier records are both missing and whose verdicts
   were written nowhere. Only the `--plan` floor sees it (chunk count vs
   implement pipeline records), and only when the plan is passed.
2. A **verifier that was disabled** vs a verifier that ran unrecorded when the
   chunk record's `chunk_verdict` is *also* null — both read as null. The
   opt-in state is session-only; a `--lint` warning "implement chunk record
   with null `chunk_verdict`" is the most the reader can say.
3. A **session that wrote nothing** — `summarize` prints `records: 0` for a
   missing file but has no way to know a cycle ran (the kickoff is not read).
4. A **red round** beyond the ones whose verdict reached a record; a
   `pending-red → pass` flip at DONE with no record.
5. A **fix recorded correctly as `fix` but at the wrong iteration**, or a
   review round mis-numbered — the implication counts *kinds*, not
   *sequence*, so it cannot detect a swapped or duplicated round. Likewise a
   fix dispatch whose gate decision was recorded as `proceed` and whose reason
   is not in the fix-only set (the seq 3–5 ambiguity above) is a warning, not
   a count.
6. Anything the writer **fabricates consistently** — a record whose kind,
   verdict and gate fields agree with each other but describe a dispatch that
   never ran. No reader-side check reaches that; it is the L1 "adversarial
   layers found everything" observation, not a telemetry problem.

**Cost in files touched**:

| File | Change | Class |
|---|---|---|
| `tools/sdd-telemetry.py` | `session_rows` gains the implication counts, the per-stage `missing`, and the `expected` sum; new `--lint` subcommand with a per-field domain table (derived from the schema table, including the fixed key set) and the cross-field rules; optional `--plan <path>` floor; self-test fixtures for each implication and each domain class; tests run against `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` read-only | code |
| `docs/spec/telemetry.md` §Records-vs-Expected, Q-IMPL-HARNESSP3-006 (amend: "derived from gate records" stays true — the *fields* used change) | contract text | mechanical, after requirements ratify |
| `skills/sdd-orchestrate/references/telemetry.md` §7 (post-cycle reader), §2 (the L6 `scope.widened` sibling of `write_scope_n`, if adopted) | reference text | mechanical |
| `docs/spec/telemetry.md` §Record Schema | **only if** `--lint`'s domain table is to be the schema's source of truth (one table, two readers) or the L6 widening field is added | design-decision-for-requirements |

**3–4 files**; the definition of `expected` (implication-derived, with or
without the plan floor) and whether the 14-missing or 11-missing reading is
the reported implement number are **design decisions for requirements**; the
`--lint` domain table, the cross-field rules and the fixture tests are
**code**; the spec/reference restatements are **mechanical**.

**Confidence**: High that the implication counts reproduce P2 and P3 on the
frozen fixture (every number above is the formula's output on the file, §B,
not an estimate); Medium on the `--plan` floor (constructed; the plan format's
chunk headers are stable but the floor's value depends on the verifier
opt-in, which is not durable).

---

## Decided at DISCUSS (restated unchanged from the kickoff — requirements inherit these)

- Migration of the 8 records is in place on the live `.sdd/telemetry.jsonl`,
  stamped partial, after P2 and P3 land; the frozen fixture is never touched.
- REQ-ARB is exercised by directing the first `APPROVE_WITH_FIXES` fix loop of
  this cycle to regenerate its deliverable wholesale.
- DONE rule: every traced requirement `pass`; nothing closes as a deliberate
  `fail`. An item that cannot be exercised live is descoped at replan.
- Scope priority for the plan is the order in §Scope, so a `stop` partway
  leaves V14 and telemetry landed first.

---

## Implications for Design

- **`COMMIT:` is a post-decision signal in sequential mode.** Requirements
  should state the signal as rendering *after* the commit it observes, with a
  pause on `INCOMPLETE` offering `amend | accept | stop`; the §5 order gains an
  item 8, and the fan-out per-leaf gate renders it in position 2b. Do not adopt
  V14's `git show --name-only --format= HEAD` literally — the comparand is a
  two-sha `git diff --name-only`, captured before any bookkeeping commit.
- **Sequential `expected` is observed writes only — decision for
  requirements.** `RETURN.files_written` is not unioned into `expected`; a
  claimed-but-unobserved (or reverted) path is a RETURN defect, surfaced as
  a return-drift warning under `return-contract.md` and excluded from
  `COMMIT:`, so a leaf's return cannot force a false `INCOMPLETE` pause. This
  mirrors the fan-out per-leaf `RETURN.commits ⊆ rev-list` clause.
- **No third `COMMIT:` member.** A clean merge cannot drop a path; the
  abort-and-redo path re-derives from a new dispatch whose own sets are
  compared. If requirements want the aborted attempt's path list preserved,
  that is a repair-packet field, not a gate token.
- **`expected` becomes implication-derived**: the highest `seq` plus the
  per-stage shortfall of every implied kind (39 vs 20 on the p3 fixture); the
  plan floor is an opt-in reader flag. Requirements must choose the reported
  implement definition (11 or 14 missing for p3) — the tool can print both.
- **The fix implication has two clauses** — the preceding gate decision and
  the fix-only dispatch reason — because the fixture shows a mis-typed fix
  (seq 18) that only the reason clause reaches. Requirements should ratify the
  reason set (`red_break` today) as part of the record schema's domain table.
- **`--lint` validates every field from one domain table**, and the fixture
  already exhibits five violation classes (kind enum, sha literal, null heads,
  long shas, undeclared key). The migration decided at DISCUSS should run only
  after `--lint` is clean on the fixture's *typed* fields — otherwise the
  migrated block asserts more than the evidence supports (the P-section trap).
- **L6 rides on the schema**: `scope.widened` (int, count of widened globs) as
  a sibling of `dispatch.write_scope_n` fits the counts-not-text rule; it is a
  record-field addition and therefore a requirements decision.
- **Telemetry stays non-load-bearing; `COMMIT:` is load-bearing.** Keep the
  two apart in requirements text so the `TELEMETRY:` precedent (assert on the
  next gate) is not copied for `COMMIT:`.
- **No new artifact under `docs/`** is needed by either answer; both read
  artifacts and history that already exist. Phase detection is untouched.

## Probes

- **Probe 1 (Q1)** — `$TMPDIR/rs-p4-probe.sh`, a five-case scratch repository
  (sequential omission, sequential inverse, fan-out fast-forward, fan-out true
  merge, conflict → abort → redo). Transcript in `evidence-appendix.md` §A.
  Throwaway; nothing in this repository was committed, checked out or written
  by it. It demonstrates the comparand behaviour of `git show` vs `git diff`
  and the set differences; it does **not** exercise the gate rendering, the
  `amend` option or the interaction with the aggregate-regeneration commit in
  a live orchestrated run.
- **Fixture cross-check (Q2)** — a read-only pass over
  `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` computing the
  implication counts, the per-stage shortfall and the domain violations
  (`evidence-appendix.md` §B); repeated for this revision to confirm every
  restated number. Not a test run; no tool was modified.
- **File-set enumeration (Q1 cost)** — the `grep -rlE` command quoted in §Q1,
  run read-only at `92b4d67`; 17 files, listed in the cost table.

## Open Questions

- Should `COMMIT: INCOMPLETE` at the **last chunk before the implement-stage
  review** block the review dispatch, or let the review see the partial tree
  and rely on `amend`? The probe does not reach this; requirements decide.
- Does the `amend` option re-run the write-scope check on the amended commit,
  or is the amended path already `IN` by construction (it came from the
  observed set)? Constructed answer: already `IN`; confirm at specs.
- Is the reported `records-vs-expected` gap the 8 + 3 reading (dispatches with
  no record of their own kind) or the full 14 (every implied append) at
  implement, and is the cycle headline the total shortfall (19 for p3)? The
  tool can print all three; requirements pick the headline number.
- Are seq 3–5's `reason: REVIEW` records fix dispatches whose gate decision was
  mis-recorded as `proceed`? If so the fix-only reason set should include a
  `REVIEW`-at-`iteration ≥ 1` clause; the fixture alone cannot settle it.
- Whether `--lint`'s domain table becomes the schema's single source (spec
  generated from code, or code checked against spec by `sdd-skill-lint`) is a
  tooling decision requirements may defer to specs.

## Recommendation

**Proceed to requirements.** Both questions have an evidence-backed answer; no
second spike is needed. Requirements should ratify four design decisions —
the post-decision placement and two-sha comparand of `COMMIT:`, the
implication-derived `expected` with its headline definition, the two-clause fix
implication with its fix-only reason set, and the two record-field additions
(`commit` group, `scope.widened`) — and inherit the §Decided list unchanged.
