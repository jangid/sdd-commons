---
id: RS-HARNESSP3-001
workstream: harness-p3
topic: harness-hardening-p3
status: Complete
date: 2026-09-18
last_updated: 2026-09-18
questions:
  - "Q1 — Write-scope fidelity: the cheapest snapshot that makes IN/ADVISORY/OUT a content decision, its cost here and on a large repo, and whether it changes the SCOPE: token, the HISTORY_REWRITE rule, or only the snapshot step"
  - "Q2 — Leaf return conformance: should the literal RETURN: block move into every leaf template body, and should a malformed budget_consumed shape or a missing gate-arithmetic key become a pause rather than a warning"
  - "Q3 — Arbitration over regenerated artifacts: should W_N be the union of the fix's writes and any pipeline re-dispatch's writes since round N, is there a general regenerated-not-patched rule, and does it weaken the arbitration guarantee"
  - "Q4 — Telemetry assurance: the smallest assurance that the append actually happened, without a new artifact and without letting telemetry influence control flow"
  - "Q5 — Red-team follow-ups: (a) chunk mapping for red breaks and the target.chunk: all fallback, (b) vocabulary for a second break behind the first, (c) what the traceability Verified column should read while a red round is outstanding and who writes it"
  - "Q6 — Cycle identity in phase detection: does comparing verification.md's research_id to the kickoff's settle it for both markers, and does any other detection input have the same ambiguity"
  - "Q7 — Two carried pilot corrections: (a) the marker-4 specs write scope must name docs/ws/<id>/traceability.md, (b) aggregate traceability regeneration belongs in its own orchestrator commit — confirm both and say whether either has a consequence beyond the table row"
  - "Q8 — What NOT to do: which remaining smaller items are fixed here, deferred with a reason, or declined"
budget: "One spike, <= 60 tool calls, <= 3 prototypes/probes. Consumed: 23 tool calls, 2 probe runs (both in $TMPDIR against a throwaway clone of the toy bundle at fbebd05; nothing written into this repository's working tree by a probe)."
research_refs: [RS-008, RS-HARNESSP2-001]
# Note: `last_updated`, `workstream`, `topic` and `research_refs` are extensions
# beyond the sdd-research findings template (staleness detection, marker-4
# workstream attribution, prior-research linkage) — same convention as RS-008
# and RS-HARNESSP2-001.
---

# Research: Harness Hardening, Part 3 — write-scope fidelity, return conformance, arbitration over regenerated artifacts, telemetry assurance, red-team follow-ups

## Questions

The eight questions of `docs/ws/harness-p3/kickoff.md`, reproduced verbatim in
the frontmatter above. They come from two live exercises of the v5 harness: the
N = 3 pilot recorded in `docs/ws/harness-p2/verification.md` §Pilot, and the
manual red-team run of 2026-09-18 recorded in the same file's §Next Steps
(the `adversarial-verify.md` §Manual bullet).

**Evidence base.** Run observations are cited as §A / §B1–B12 / §C of
[`evidence-appendix.md`](evidence-appendix.md) in this spike directory — a
verbatim carry-over, committed for citability, of the gitignored working file
`.pilot-toy/harness-p3-input.md` as of 2026-09-18. Every `§Bn` citation below
resolves against that committed appendix, so a requirements or review reader
can check each claim without the working file. The appendix is working
material, not an SDD artifact: its *observations* are evidence, its *proposals*
are not contracts. Spec citations are to the files as they stand today. Two
probes were run for this spike (§Probes below).

**Confidence vocabulary.** Every finding below carries an explicit confidence
clause in one of three classes: **probe-evidenced** (reproduced mechanically in
this spike's probes), **spec-read** (established by reading committed spec /
reference / tool text, which is checkable but is not a run), and
**constructed** (proposed during this spike and never exercised). Run
observations from the 2026-09-18 session (§Bn) are uncontrolled single-run
evidence and are labelled as such wherever they carry a conclusion alone.

**Classification legend**, per the kickoff's success criteria:

- **mechanical** — spec / reference / template text only.
- **code** — a change to `tools/*.py` (including a new self-test fixture).
- **design-decision-for-requirements** — changes a defined gate signal,
  detection rule or artifact field, so requirements should ratify it rather
  than inherit it as an edit.

---

## Findings

### Q1 — Write-scope fidelity

**Answer**: extend `snapshot(before)` / `snapshot(after)` with a **content-hash
observation** — `(path, sha)` pairs — but compute it **only over the ambiguous
set**, i.e. the paths already listed in `snapshot(before)` as dirty or
untracked. A path that was *clean* before the dispatch is already decided
unambiguously by the porcelain and committed deltas; the blindness of the
three-command check exists exactly and only for paths that were already dirty.
Bounding the hash to that set makes the fix O(dirty files), not O(repo).

Shape (an addition to `write-scope.md` §3, beside the existing observation
commands). Name it the **content-hash observation**, not "the fourth
observation": §3 already calls the named-base observation a four-part one, so
an ordinal label would collide with text that is already there.

```
before : paths(scope.before) -> shasum -> sha.before
after  : paths(scope.before) INTERSECT paths(scope.after) -> shasum -> sha.after
content delta : pairs whose sha changed, plus paths in sha.before now absent
observed writes := porcelain delta UNION committed delta UNION content delta
```

**Evidence**: probe 1 (§Probes), a throwaway clone of the toy bundle at
`fbebd05` in `$TMPDIR`.

- Case A (leaf touches a path that was clean): porcelain delta and content
  delta agree — `src/recon/engine.py` in both. No behaviour change.
- Case B, the §B1 case (leaf re-touches a path that was already dirty from the
  previous dispatch): the porcelain delta is **empty**; the content delta names
  `docs/ws/default/verification.md`. This is the live 2026-09-18 observation
  reproduced mechanically, twice over (§B1 and the C-log R1 fix round both
  record hash-verifying the same file by hand).

**Cost measured**: hashing every tracked file of this repository (134 files)
takes 0.064 s; hashing an 8-path set takes 0.017 s; the porcelain baseline is
0.008 s. Hash throughput measured at ~700 MB/s (200 MB in 0.28 s). On a large
repository the unbounded whole-worktree variant is what would hurt — the
bounded variant scales with the dirty set, which is by construction the
handful of paths a stage has in flight, so it stays in the tens of
milliseconds at any repository size.

**Alternatives, both rejected on probe evidence**:

- `git stash create` — probe 2 measured it writing **7 loose objects into
  `.git/objects` per snapshot**. That makes the orchestrator mutate the
  repository it is observing, against the observe-and-report posture that
  `write-scope.md` §5 states for `HISTORY_REWRITE` ("never an automatic
  reset"), and it returns empty on a clean tree, so the snapshot step would
  need a branch anyway.
- `git diff --stat` against a pre-dispatch index — probe 2: a temporary index
  seeded with `read-tree HEAD` diffs the worktree against **HEAD**, not
  against the pre-dispatch worktree state, so it reported *both* the
  already-dirty file and the leaf's write. Identical blindness. Recording the
  pre-dispatch worktree content in the index requires staging it, which writes
  blobs — the first alternative's problem.

**Does it change the `SCOPE:` token or `HISTORY_REWRITE`?** No to both; only
the snapshot step and one rule. The `IN` / `ADVISORY` / `OUT` tags, the
`N` count, the finding block and the operator options are untouched, because
this changes *what counts as an observed write*, not how an observed write is
matched or rendered. The ancestry check (c) is untouched, so
`HISTORY_REWRITE` is untouched. The one rule that must change is §3's bullet
"Paths present in both snapshots ... cancel — only the *delta* is a write":
it becomes "cancel **only when their content hash is also unchanged**". That
bullet is precisely the false negative.

**Parsing caveats for implementation** (cheap, but must be stated or the
fourth command is wrong): parse porcelain with `-z`; rename/copy records
(`R`, `C`) carry two paths and both must enter the set; a path deleted during
the dispatch cannot be hashed and is recorded as a sentinel "absent" pair,
which is itself a content change. A file modified and reverted within one
dispatch remains invisible (its hash returns) — that accepted limitation of
§5 is unchanged.

**Files touched**: `skills/sdd-orchestrate/references/write-scope.md` §3
(snapshot block + one rules bullet) and §5 (limitation wording);
`docs/spec/harness-write-scope.md` (the contract this reference pastes from);
`tools/sdd-scope-check-selftest.py` (one new fixture — the Case B scenario, an
**F10** beside F8/F9; `F9` is already taken by the catch-up-base scenario, so
the next free id is F10).

**Classification**: mechanical (spec text) + **code** (one new self-test
fixture). Cost: 3 files.

**Confidence: high — probe-evidenced.** Both the blindness and the bounded
remedy were reproduced mechanically in probe 1, the costs are measured numbers
from probe 2, and both rejected alternatives were rejected on measurement
rather than on argument. The one unprobed part is the parsing-caveat list
(rename/copy and delete handling), which is spec-read from `git status`
semantics.

---

### Q2 — Leaf return conformance

**Answer (i) — yes, pin the literal block in every leaf template body**, and
the asymmetry that produced the drift is visible in the reference text, not
just in the run.

Read today:

| Template | Where its `RETURN:` shape lives | Drifted on 2026-09-18? |
|---|---|---|
| PIPELINE (`dispatch-templates.md` §PIPELINE) | **inside** the fenced prompt, literal key block | no |
| fan-out leaf (`fan-out.md` §2) | **inside** the fenced prompt, literal key block | no (not exercised this run) |
| chunk verifier (`dispatch-templates.md` §CHUNK VERIFIER) | fenced prompt says only "then the RETURN: block, whose last line is CHUNK_VERDICT:"; the shape sits in a **later prose subsection** | **yes, twice** (§B2, §B10) |
| red team (§RED TEAM) | fenced prompt says "Return in the shape below"; the shape sits in the **adjacent** subsection | no (the adjacent block was pasted) |
| review (§REVIEW) | no `RETURN:` block by contract — a review emits `VERDICT:` only (`return-contract.md` §6) | n/a |

So the split the evidence found (§B10: two prose-instructed verifier dispatches
drifted, the one whose dispatch text pinned the literal key list conformed) maps
exactly onto "is the block inside the fenced template body or outside it".
Recommendation: move the literal key block **inside** the fenced bodies of the
**chunk verifier** and the **red team** templates (red keeps its `Rn` line shape
above the block and `RED_VERDICT:` on its own last line). The pipeline and
fan-out bodies already comply and need no change; the fix re-dispatch is the
pipeline template with `{on_fix_only}`, so it is covered. The review template
needs no `RETURN:` block — but its own-line `VERDICT: APPROVE |
APPROVE_WITH_FIXES | REJECT` token should be pinned in the body on the same
principle.

**Answer (ii) — elevate exactly one condition, not the whole key set.** The
keys the **gate arithmetic** consumes are two: `status` (already a malformed
condition) and `budget_consumed` (rendered at every gate against the dispatched
`Budget:`, and it sizes the next repair packet's `budget`). `status:
BUDGET_EXHAUSTED` already requires `budget_consumed` to be present, but nothing
requires it to be a *map*, which is why the prose value of §B2 sailed through.
Add one row to `return-contract.md` §Parsing:

```
RETURN: MALFORMED (budget_consumed shape)   # present but not a map of unit -> integer
```

Do **not** elevate the other nine. `files_written` is independently
cross-checked by the write-scope observation, so an omitted list cannot hide a
write. `tasks_completed`, `traceability_fills`, `chunk_close`, `failures`,
`ledger`, `verified_do_not_touch`, `open_questions` and `commits` feed
bookkeeping that either degrades to "nothing to do" or that the orchestrator can
see for itself. `blocked_writes` is the one borderline case — an omitted list
silently loses content — but only when the leaf also failed to write, which
surfaces as the deliverable being absent from the observed window. Keep it a
warning; note the reasoning so requirements can overrule it deliberately.

**Evidence**: §B2 and §B10 (n = 3, uncontrolled, but one-directional and the
mechanism is legible); plus the reference read above, which is the stronger
evidence because it identifies *why* the two classes differ.

**Confidence: (i) high — spec-read** (the template table above is a direct read
of committed template text, and it explains the run rather than merely
agreeing with it); the run corroboration behind it is n = 3 and uncontrolled.
**(ii) medium — spec-read plus judgement**: that `status` and
`budget_consumed` are the two keys the gate arithmetic consumes is a read of
`return-contract.md` and the gate blocks, but the "elevate exactly these, keep
the other nine a warning" boundary is a judgement with no run evidence either
way — which is why it is routed to requirements to ratify rather than adopted
as an edit.

**Files touched**: `dispatch-templates.md` (two fenced bodies, one token pin),
`return-contract.md` §Parsing (one row) and §1 (one note),
`docs/spec/harness-return-contract.md`, `docs/spec/harness-chunk-verifier.md`
and `docs/spec/adversarial-verify.md` §Red Dispatch Template (the two specs the
templates are pasted from). Cost: 5–6 files, all text.

**Classification**: (i) mechanical. (ii) design-decision-for-requirements — it
adds a gate pause condition, and the "which keys" boundary is a judgement
requirements should ratify.

---

### Q3 — Arbitration over regenerated artifacts

**Answer**: yes — `W_N` becomes the union of the fix dispatch's written pairs
**and** the written pairs of every orchestrator-dispatched **regeneration of the
stage deliverable** between round N and round N+1. State it as a general
regenerated-not-patched rule at the `loop-control.md` §2a level, not inside the
red section, because it applies to any stage whose pipeline leaf rewrites its
artifact wholesale between review rounds (specs, plan, verification).

**Evidence**: §B8. Review round 1 `APPROVE`; round 2 `APPROVE_WITH_FIXES` with
three material findings on ground round 1 never named. `W_1` is computed from
the fix dispatch only, and the fix touched code, so it did not contain
`docs/ws/default/verification.md` — the file both rounds reviewed and the file
the blue re-dispatch had regenerated wholesale in between. Class (b)
(`k not in K_N and k not in W_N`) therefore fires **by construction** on every
finding in a regenerated deliverable. That is not a contradiction; it is a
fresh review of a fresh artifact.

**Does it weaken the guarantee?** The pause exists to catch a reviewer raising
new Critical/Material on ground the previous round approved *and the loop did
not touch*. A wholesale-regenerated file **was** touched by the loop, so
admitting it to `W_N` removes false positives only — it cannot mask a
contradiction about a file the loop left alone. The one real degradation is
granularity: if the regeneration enters `W_N` as a blanket `(file, *)` pair,
a genuinely contradictory finding in a section the regeneration did not
materially change is no longer distinguishable.

**That degradation is avoidable at zero extra cost.** Section resolution
already exists (`write-scope.md` §3, "Section resolution of fix hunks",
REQ-ARB-HARNESSP2-005) and is a function of a diff — it applies to a
regeneration dispatch's diff exactly as it applies to a fix's. So:

```
W_N := sections(fix[N] writes) UNION sections(regeneration writes since round N)
       # falling back to (file, *) only where section resolution is unavailable,
       # which is the existing rule and already labels the pause "(file-level)"
```

With that, nothing is weakened: the arbitration guarantee holds at the same
granularity as today, and the §B8 false positive disappears.

The retained per-round state schema in `loop-control.md` §2a follows: `fix[N]`
generalises from "the fix dispatch" to "the loop dispatches between round N and
round N+1" (rename it or add a sibling `regen[N]` whose pairs union in — either
shape is fine; the union is the contract).

**Files touched**: `loop-control.md` §2a (state schema + the `W_N`
definition), `docs/spec/arbitrated-handoff.md` §Retained Per-Round State and
§Contradiction Classes, `docs/spec/adversarial-verify.md` §Fix-Loop Interaction
(one cross-reference, since the red round is where it was observed). Cost: 3
files.

**Classification**: design-decision-for-requirements (it redefines a detection
rule), mechanical to implement.

**Confidence: high for the defect, medium for the remedy.** The defect is
**spec-read and run-corroborated**: class (b)'s definition in
`loop-control.md` §2a and the §B8 observation together show the false positive
fires by construction, not by chance. The remedy — unioning regeneration
writes into `W_N` at section granularity — is **constructed**: it reuses an
existing, already-specified mechanism (section resolution,
REQ-ARB-HARNESSP2-005) rather than inventing one, but no run has exercised the
unioned form.

---

### Q4 — Telemetry assurance

**Answer**: add a **positive member to the `TELEMETRY:` gate-line family** —
the smallest change that converts "silently not written" into "visibly absent",
with no new artifact, no read of the telemetry file, and no control-flow
influence.

```
TELEMETRY: rec <n>     # rendered on the gate AFTER an append; <n> is the session append counter
```

The orchestrator already holds a session-state counter (`dispatch.seq`,
`telemetry.md` §3, "a session-state counter starting at 1"), and the writer
sequence already appends *after* the gate decision — so the next gate is the
natural place to assert the previous append. Crucially `n` is the **session
counter, not a file read**, so the write-only rule
(REQ-TELEM-HARNESSP2-004, "the orchestrator performs zero reads of the file")
is preserved intact, and the line is text, so the non-interference proof of
§5 is untouched. An operator who sees a gate with no `rec` line and no
`OFF` / `WRITE FAILED` line knows the append did not happen.

**Evidence** (§B11, negative): the gate rendered telemetry as on and no record
was ever appended — the toy clone has no `.sdd/telemetry.jsonl` and nothing
failed, warned or noticed. A second, sharper piece of evidence from the same
observation: the text actually rendered was `TELEMETRY: on (record written
after your decision)`, which is **not a member of the family `telemetry.md` §3
defines** (`WRITE FAILED | OFF | .gitignore updated`). The run's own gate text
had drifted into inventing a positive line because none existed — which is the
argument for adding one.

**Second, optional backstop**: have `tools/sdd-telemetry.py summarize` report
records-vs-expected per session (it already skips and counts unparsable lines
on a trailing `skipped:` line, so the reporting slot exists). This makes the
gap visible post-cycle even if the operator missed the missing gate line.
Classification **code**, optional, 1 file. **It is counted inside the Q4 item,
not as a twelfth item** — it is an optional sub-part of the same
recommendation, and the item list in §Implications for Design counts Q4 once
(while counting its code as one of the two code-carrying items).

**On the standing goal**: "first live telemetry cycle in this repo" (open since
harness-p2) remains open — the 2026-09-18 run did not deliver it. Telemetry is
already default-on at KICKOFF, so this is a run-time choice for the harness-p3
cycle, not a spec change, and the `rec <n>` line above is what would make its
success observable.

**Files touched**: `skills/sdd-orchestrate/references/telemetry.md` §3
(gate-line table + one line in the writer sequence), `docs/spec/telemetry.md`
(contract), `skills/sdd-orchestrate/SKILL.md` §The gate (one line). Cost: 3
files (+1 if the `summarize` backstop is taken).

**Classification**: mechanical for the gate line; code for the optional
`summarize` backstop.

**Confidence: high for the gap, medium-high for the remedy — spec-read.** The
gap is directly observed (§B11: telemetry rendered as on, no file written,
nothing noticed) and the sharper half of it — that the rendered line was not a
member of the family `telemetry.md` §3 defines — is a read of committed text.
The remedy's key property, that `n` is the existing session counter and not a
file read, is likewise established by reading `telemetry.md` §3; what is
unexercised is whether an operator actually notices the absent line, which no
spec read can establish.

---

### Q5 — Red-team follow-ups

#### (a) Chunk mapping for red breaks

**Answer**: keep the whole-plan fallback as the *rule*, and narrow the *input*
instead — map from evidence red already returns rather than asking red to make
an ownership judgement.

`return-contract.md` §5 maps a red `Rn` starting at step 2 (spec from the
`## Red team — <spec.md>` heading) because red lines carry no `affects`. But
red's return already carries `failures[].location`, and the red template is
given the plan **for exactly that purpose** ("Plan: {plan_path} ... supplies
the `### Chunk N:` vocabulary red uses in `failures[].location`"). So add a
step 1' to §5's red entry: if the routed `Rn`'s `failures[].location` names a
file or chunk, resolve it to the chunk whose tasks' implementation modules
include it; otherwise fall back to the heading spec and step 2 as today.

**Evidence**: §B4 — both breaks landed as `target.chunk: all` because
`recon.md` is traced by both plan chunks, and §B4's own observation that on a
small plan nearly every spec is traced by more than one chunk. The mechanism is
step 4 of §5 working as specified, so the fallback is not a defect; it is a
default that discards information red already produced.

**Declined**: asking red to "name the narrowest owning symbol" as a new field
on `Rn`. That asks the read-only adversarial leaf to judge code ownership,
which REQ-HARN-019 / REQ-ORCH-012 keep out of leaves, and it widens red's
return shape for a mapping the orchestrator can do from `location`.

**Files touched**: `return-contract.md` §5 (one bullet),
`docs/spec/harness-return-contract.md`, `docs/spec/adversarial-verify.md`
§Fix-Loop Interaction (one table cell). Cost: 3 files.
**Classification**: mechanical.
**Confidence: high — spec-read.** That `failures[].location` already carries
chunk vocabulary, and that §5 step 4 produces `all` when a spec is traced by
more than one chunk, are both direct reads of committed contract text; §B4 is
the run instance of exactly that path. The narrowing step itself is
**constructed** and unexercised, but it cannot regress anything: it only
inserts a more specific resolution ahead of the existing fallback, which stays
in place.

#### (b) A second break behind the first

**Answer**: yes, the gate needs the distinction — but derive it in the
orchestrator from evidence, do **not** add a `supersedes:` / `new-ground:`
marker red must fill.

Rule: on a red round N >= 2, for each `BROKEN` `Rn`, the orchestrator re-runs
the **previous round's** routed `reproduce:` command (it holds those lines
verbatim) and renders one derived line under the token:

```
RED: R1 new-ground (prior R6 reproduce now passes)
RED: R1 regression  (prior R6 reproduce still fails)
```

**Evidence**: §B7 — round 2 returned `BROKEN` on the same criterion by a
different mechanism, and the operator could only tell it apart from "the fix
failed" by doing this by hand (the C-log records verifying `R1 -> [1]`, the R6
overflow case, and the pre-tolerance engine independently). The gate had no
vocabulary for it. The derived line costs one command per prior break and
changes neither red's return shape nor its isolation.

**Declined**: the marker on `Rn` lines. It would require handing red the
previous round's findings, contradicting the withholding default — and §B3 is
direct evidence that withholding works (red found the weakest criterion without
blue's report). §B7 also notes that re-attacking the same criterion is what
found the second bug, so red should *not* be steered away from it.

**Confidence: medium — observed gap, constructed remedy.** The observation is
strong (§B7 is a direct record of the operator having to do this distinction by
hand, and of the gate having no vocabulary for it). The proposed rule itself
has **no run evidence** — it was constructed during this spike and not probed —
which is the weakest evidential footing of any recommendation here, and is why
it also appears under §Open Questions with a named place to exercise it.

**Files touched**: `docs/spec/adversarial-verify.md` §Verify-Stage Gate (gate
block + one rule), `skills/sdd-orchestrate/SKILL.md` §The gate (signal order
note). Cost: 2 files.
**Classification**: design-decision-for-requirements (a new derived gate
signal).

#### (c) The `Verified` column under `pending-red`

**Answer**: the column tracks the report's status. When `sdd-verify` writes
`status: pending-red` it writes `pending-red` into the `Verified` cell of every
row it would otherwise have marked `pass` (a `fail` row stays `fail`); the
orchestrator's **existing** `pending-red -> pass` flip at DONE flips those
cells in the same bookkeeping step and regenerates the aggregate. One writer
per state, no new artifact, and a cycle the operator stops leaves the durable
matrix reading `pending-red` rather than asserting a falsehood.

**Evidence**: §B9 — both the per-ws and the aggregate matrix carried
`Verified: pass` inherited from the superseded `4aced03` report while
`verification.md` read `pending-red`. Confirmed against the specs: `sdd-verify`
Step 3b says only "update the Verified column with pass/fail"; the
`adversarial-verify.md` §`status: pending-red` lifecycle flips **frontmatter
only**; and the flip is already orchestrator-owned bookkeeping, so the cell
flip has a home and needs no new mechanism.

**Checked for a code consequence — there is none.** `tools/sdd-gc.py`'s
`trace-empty` sweep flags only *empty* Spec cells and Implementation-filled /
Test-empty rows; it does not constrain the `Verified` cell's vocabulary, so a
third value is safe today. This was verified by reading the sweep, not assumed.

**Files touched**: `docs/spec/adversarial-verify.md` §`status: pending-red`
(table + lifecycle), `skills/sdd-verify/SKILL.md` Step 3b and Step 6,
`docs/spec/ws-traceability.md` (one sentence naming the legal cell values).
Cost: 3 files, no code.
**Classification**: mechanical, with one small design call for requirements to
ratify — the `Verified` vocabulary gains a third value.
**Confidence: high — spec-read and observed.** The gap is a direct observation
(§B9: both matrices read `pass` while `verification.md` read `pending-red`),
and each of the three load-bearing claims behind the remedy was checked by
reading committed text rather than assumed: `sdd-verify` Step 3b's
`pass`/`fail`-only instruction, `adversarial-verify.md`'s frontmatter-only
flip, and `tools/sdd-gc.py`'s `trace-empty` sweep not constraining the
`Verified` cell's vocabulary.

---

### Q6 — Cycle identity in phase detection

**Answer**: yes, the `research_id` comparison settles it — and it must be
**added**, because `verification.md` does not carry the field today.

**Evidence** (read, not inferred): `docs/ws/harness-p2/verification.md`
frontmatter is `date`, `last_updated`, `status`, `plan_ref`, `workstream`,
`scope` — **no `research_id`**. `docs/ws/harness-p2/plan-history/*.md`
frontmatter is `workstream`, `last_updated`, `status` — also none. A repository
grep shows `research_id` is written **only** into `kickoff.md`, and consumed by
`sdd-orchestrate` §Position, `loop-control.md` (the
`git log -S'research_id: <id>'` cycle-start-date derivation) and
`telemetry.md` (`cycle.research_id`). So the ambiguity the pilot found is
exactly "the kickoff knows which cycle it is and the execution artifacts do
not".

Recommendation: `sdd-verify` Step 6 stamps `research_id:` (copied from the
workstream's `kickoff.md`) into `verification.md`'s frontmatter, and every
reader that treats `status: pass` as "this cycle is done" first checks
`verification.research_id == kickoff.research_id`. A mismatch — or absence, for
legacy reports — reads as "a previous cycle's report", i.e. the verify stage
has not been reached in this cycle. This works identically under both markers
(under marker `3` the kickoff is `docs/handoff/kickoff.md`).

**Does any other detection input have the same ambiguity?**

- **`plan.md` — yes.** `status: complete` with every task `[x]` is equally
  indistinguishable between cycles; the harness-p2 plan reads exactly that
  today. `sdd-orchestrate` already carries a workaround for it (the
  `git log -S` date derivation in `loop-control.md`). Recommend the same stamp:
  `sdd-plan` writes `research_id:` from the kickoff, after which the git
  derivation becomes a fallback rather than the primary signal.
- **Requirements / specs status — no, and it should stay that way.** They are
  the *shared* corpus and are deliberately cumulative; `status: Approved` is a
  product-wide flag (`ws-layout.md` §Approval: "shared `requirements/*` /
  `spec/*` carry one product-wide status"), not a per-cycle one. A cycle
  boundary is not expressible there and stamping one would break sharing.
- **Research findings status** — already per-spike and per-cycle by
  construction (the kickoff names its `research_id`); no change.

**Scope check**: this adds a frontmatter *field* to two existing artifacts, not
a new artifact type, and the field is neither telemetry-, review- nor
red-derived — so it stays inside the kickoff's out-of-scope fence.

**Files touched**: `skills/sdd-verify/SKILL.md` (frontmatter template + Step 6),
`skills/sdd-plan/SKILL.md` (same), the §Phase Detection blocks of `sdd-verify`,
`sdd-replan`, `sdd-plan`, `sdd-implement` and `sdd-orchestrate`, the detection
table in `CLAUDE.md`, and `loop-control.md` (demote the git derivation to a
fallback). Cost: ~7–8 files, all text, but spread across skills.

**Classification**: design-decision-for-requirements (a new phase-detection
input).

**Confidence: high — spec-read, explicitly read rather than inferred.** The
load-bearing negative claim (neither `verification.md` nor `plan.md` carries
`research_id` today) comes from reading the harness-p2 artifacts' frontmatter
and from a repository-wide grep for `research_id`, both reproducible from
committed material. The remedy — stamp and compare — is **constructed** and
unexercised; its one known cost (a one-time re-entry into verify for
workstreams with legacy reports) is carried to §Open Questions rather than
decided here.

---

### Q7 — Two carried pilot corrections

#### (a) marker-4 specs write scope must name `docs/ws/<id>/traceability.md`

**Confirmed, with a correction to the framing.** The path is **not missing from
the reference**: `write-scope.md` §2's marker-4 note already says the
traceability write "resolve[s] to their `docs/ws/<id>/` equivalents
(`docs/ws/<id>/traceability.md` plus the regenerated aggregate
`docs/requirements/traceability.md`)", and §9 enumerates it. What is missing is
the **row itself** — the specs row reads `docs/spec/**,
docs/requirements/traceability.md`, so a reader who stops at the table (which
is how the table is used when filling `{write_scope}`) does not see it.

**Consequence beyond the row**: yes, one, and it is the same class the
reference already records. `ws-traceability.md` Q-IMPL-011 makes `sdd-specs`
fill the **Spec** column of `docs/ws/<id>/traceability.md` under marker `4`.
A specs leaf doing exactly what its skill mandates would therefore be tagged
`OUT` — a false `VIOLATION` — which is precisely the failure the 2026-09-17
re-walk note in §2 was written to prevent for `sdd-verify`'s Verified-column
write. Recommendation: name it in the row.

**Files touched**: `write-scope.md` §2 (one row), and
`docs/spec/harness-write-scope.md` if it carries the same table. Cost: 1–2
files. **Classification**: mechanical.
**Confidence: high — spec-read.** Both halves are direct reads of committed
text: `write-scope.md` §2's marker-4 note and §9 already name the per-ws
traceability path, the specs row in the same §2 table does not, and
`ws-traceability.md` Q-IMPL-011 mandates the write that the row would tag
`OUT`. No run evidence is needed — the false `VIOLATION` follows from the two
texts as they stand.

#### (b) aggregate regeneration belongs in its own orchestrator commit

**Confirmed, and it does have a consequence beyond the table row** — larger
than the kickoff's "expected small".

Today `ws-traceability.md` **Q-IMPL-011** makes *every writing skill* regenerate
`docs/requirements/traceability.md` immediately after its per-ws write —
`sdd-requirements`, `sdd-specs`, `sdd-implement` (including chunk-close Check
2) and `sdd-verify`. For an orchestrated sequential dispatch that means the
**leaf** regenerates, so the aggregate lands inside the observed window and
inside the orchestrator's single stage commit. Meanwhile `fan-out.md` §3e
already has the orchestrator regenerating at merge. The two are inconsistent,
and the pilot's correction resolves it in the orchestrator's favour.

Adopting it means: (i) dropping `docs/requirements/traceability.md` from the
leaf default write scopes for orchestrated dispatches, (ii) adding a post-gate
orchestrator bookkeeping step and a separate commit beside fan-out §3e's, and
(iii) **keeping Q-IMPL-011's behaviour for standalone, non-orchestrated skill
runs** — otherwise the aggregate goes stale whenever someone invokes a single
`sdd-*` skill outside the harness. Recommendation: adopt with that split stated
explicitly ("the orchestrator regenerates for orchestrated dispatches; a
standalone skill run still regenerates itself").

**The discriminator — how a skill knows which mode it is in.** The split above
is only implementable if a skill can tell an orchestrated dispatch from a
standalone invocation, and the finding must name that signal rather than
assume it. It does not need a new mechanism: **the dispatched `{write_scope}`
slot is the discriminator**. An orchestrated leaf is always dispatched with an
explicit write scope (`dispatch-templates.md` §PIPELINE `{write_scope}`;
`write-scope.md` §2 is the table that fills it) and is bound to it by the
`SCOPE:` check; a standalone `sdd-*` run has no dispatched write scope at all.
So the rule is stated in terms of the slot, not in terms of a new flag:

> A writing skill regenerates `docs/requirements/traceability.md` after its
> per-ws write **unless it was dispatched with a write scope that omits that
> path**, in which case the regeneration is the orchestrator's (the post-gate
> bookkeeping commit). Under this cycle's change the orchestrated leaf scopes
> omit it by construction — item (i) above is what removes it — so the absence
> of the path from `{write_scope}` *is* the "orchestrated" signal, and its
> presence (or the absence of any dispatched scope) *is* the standalone signal.

This keeps one behaviour per skill expressed against one input it already
receives, and it keeps the two rules from contradicting: a skill never has to
know *who* invoked it, only what it was scoped to write. Whether requirements
prefer this implicit signal or an explicit instruction line added to the
PIPELINE template body is carried to §Open Questions — but the mechanism above
is grounded in an existing slot and needs no schema change.

**Files touched**: `write-scope.md` §2 and §7 (commit-ownership table),
`ws-traceability.md` Q-IMPL-011 (amendment), `fan-out.md` §3e (cross-reference),
and the marker-4 traceability notes in the four writing skills. Cost: ~7 files.

**Classification**: design-decision-for-requirements. Flagged as **larger than
the pilot expected** — this is the one carried correction that is not a
one-line table edit.

**Confidence: high for the inconsistency, medium for the resolution —
spec-read.** The inconsistency is a read of two committed texts that disagree
(`ws-traceability.md` Q-IMPL-011 has every writing skill regenerate the
aggregate; `fan-out.md` §3e has the orchestrator do it at merge), so it does
not depend on any run. Which side wins, and the discriminator above, are
**constructed** judgements: no run has exercised the split, and the
orchestrated/standalone asymmetry is exactly what requirements should ratify
rather than inherit.

---

### Q8 — What NOT to do: the explicit in/out list

**IN — carry into requirements (4 items, all small):**

| # | Item | Recommendation | Class | Files |
|---|---|---|---|---|
| 1 | Where a verify-stage `RED_BREAK` fix is recorded when no open chunk owns it (§B5) | **Fix here** — specify the section the leaf invented: `## Post-cycle Fixes` in the active plan, one line per fix, orchestrator-owned bookkeeping like fan-out §3e plan marks, and name the section in the implement / `RED_BREAK` default write scope so the write is `IN` rather than unscoped. The ad-hoc behaviour worked; specifying it costs less than leaving it to be re-invented. | mechanical | 3 |
| 2 | Prose about another repository's artifacts must not quote its `Q-IMPL` id tokens (§B12) | **Fix here as a convention; decline the code change.** gc's `qimpl-undefined` behaved correctly — the ids genuinely are undefined in this corpus. Scoping the rule to "ids that look local" is not decidable from text and would weaken a `fail`-class rule. One sentence in `CLAUDE.md` / `drift-sweep.md`. | mechanical | 1 |
| 3 | Carry-forward of un-carried minors between cycles (run log, review round 1 M1) — *provenance: raised by the 2026-09-18 run itself, not carried in from the kickoff's Q8 seed list, so requirements should treat it as new scope rather than as an already-agreed item* | **Fix here** — one rule in `sdd-verify` Step 6: unresolved Minor entries from the previous cycle's report are carried into §Issues Found → Minor or explicitly marked closed. `verification.md` is overwritten per cycle, so a minor not carried is lost to git history (observed: the RS-001 `KeyError('id')` minor). Depends on Q6's `research_id` stamp to identify "the previous cycle's report". | mechanical | 1 |
| 4 | A repair packet has no slot for findings that belong to the **next pipeline dispatch** rather than to a fix (C-log, R1 fix round) — *provenance: raised by the 2026-09-18 run itself, not carried in from the kickoff's Q8 seed list* | **Fix here, the cheap way** — no schema change: state in `return-contract.md` §3 that review findings against an artifact the fix leaf must not touch go into the next pipeline dispatch's `{deliverable_contract}` slot, which is what the operator did by hand. A `carry_to_next_dispatch:` field was considered and is not worth the schema. | mechanical | 1–2 |

**OUT — declined or deferred (3 items):**

| # | Item | Disposition | Reason |
|---|---|---|---|
| 5 | One-shot upstream review before a non-research entry (§A.6) | **Defer** | Mid-pipeline entry is explicitly out of scope this cycle (kickoff §Out of scope; orchestrate v1 is research-entry and sequential). The item only pays off once mid-pipeline entry exists — re-raise in that cycle. |
| 6 | The four pre-existing `qimpl-broken-ref` gc warnings | **Defer** | Housekeeping, not harness behaviour. They are the stable entry baseline (`GC: 0 fail, 6 warn`) that the last two runs measured drift against; clearing them mid-cycle moves the baseline without changing the harness. Route through the `sdd-gc.py --report` sweep at a DONE gate as a `record` item. |
| 7 | gc `table_cells()` pipe escape | **Decline** | The function is `line.strip().strip("|").split("|")`; it mis-splits only a cell containing a literal escaped `\|`. No such row has been observed in any run, and the failure mode is a cosmetic mis-parse of one row in a `warn`-class sweep. Re-open if a real row ever needs an escaped pipe. |

**Not on either list, deliberately**: red's write-revert rule
(REQ-REDB-HARNESSP2-003) remains **unexercised** — §B6 and the C-log both
record red leaving a clean worktree, so the rule has never been tested in
anger. It is not a finding and needs no change; it is recorded here so a future
cycle does not mistake "never fired" for "verified".

**Confidence: high for the boundary, medium per row.** That the list is
*bounded* — 4 in, 3 out, nothing else raised by the run left unrouted — is
high-confidence, because it is a closed enumeration over §A and §B1–B12 in the
appendix. The individual dispositions are mixed: rows 2 and 7 are
**spec-read** (each rests on reading the gc sweep code that produced the
finding), rows 5 and 6 are scope/housekeeping judgements with no evidential
content, and rows 1, 3 and 4 are **observed gaps with constructed remedies**,
each cheap enough that being wrong costs one edit.

---

## Implications for Design

- **Requirements scope for harness-p3 is bounded at 15 items — 11
  question-level plus 4 Q8-IN**. The eleven question-level items are Q1, Q2(i),
  Q2(ii), Q3, Q4, Q5(a), Q5(b), Q5(c), Q6, Q7(a), Q7(b); the four Q8-IN items
  are rows 1–4 of the Q8 table. By class, the eleven question-level items are
  **six mechanical** (Q1, Q2(i), Q4, Q5(a), Q5(c), Q7(a)) and **five
  design-decisions-for-requirements** (Q2(ii), Q3, Q5(b), Q6, Q7(b)); **two of
  them also carry code** (Q1's self-test fixture and Q4's optional `summarize`
  backstop — code inside those items, not extra items). All four Q8-IN items
  are mechanical.
- **The two largest items are Q6 and Q7(b)** — both touch multiple stage
  skills rather than only the orchestrate reference set. Plan them as their own
  chunks; everything else in Q1–Q5 is confined to
  `skills/sdd-orchestrate/references/` + `docs/spec/`.
- **Nothing here requires a marker bump.** No new artifact type under `docs/`;
  the only durable additions are two frontmatter fields on existing artifacts
  (Q6) and a third legal value in an existing table cell (Q5(c)).
- **The no-new-artifact and non-interference invariants hold**: Q4's assurance
  reads no file and influences no branch; Q3's and Q5(b)'s state is
  session-scoped; Q5(c)'s value is written by the same writers that already own
  those cells.
- **Two findings came from reading the specs rather than the run**, and both
  strengthen the run's conclusion: the template-body-vs-prose split that
  explains Q2's drift, and the Q-IMPL-011 / fan-out §3e inconsistency that
  makes Q7(b) bigger than expected. Requirements should treat them as part of
  the evidence, not as new scope.

## Probes

Probe measurements are recorded inline below rather than as retained files:
both probes ran in `$TMPDIR` against a throwaway clone of
`.pilot-toy/sdd-eval-toy.bundle` (HEAD `fbebd05`). Nothing was written into this
repository's working tree by a probe; no probe artifacts are kept (the clone is
disposable and is not part of this spike directory).

- **Probe 1 — content-hash snapshot (Q1).** Reproduced §B1 mechanically: with
  `docs/ws/default/verification.md` already dirty at snapshot time, a simulated
  leaf that re-touched it produced an **empty** porcelain delta and a
  **non-empty** `(path, sha)` delta naming the file; a simulated leaf that
  touched only a clean path produced identical answers from both. Proves the
  blindness and proves the bounded remedy closes it.
- **Probe 2 — alternatives and cost (Q1).** `git stash create` writes 7 loose
  objects per snapshot (measured by counting `.git/objects`); a temp-index
  `read-tree HEAD` + `diff --stat` diffs against HEAD and reproduces the same
  blindness; hashing 134 tracked files = 0.064 s, an 8-path set = 0.017 s,
  porcelain baseline = 0.008 s, hash throughput ~700 MB/s.

Not probed (and labelled as such in the findings): Q5(b)'s
re-run-the-prior-`reproduce:` rule, which is constructed rather than observed.

## Open Questions

- **Q2(ii) boundary**: `blocked_writes` missing is kept a *warning* on the
  reasoning above. If requirements disagrees, it is a one-row change — but it
  should be an explicit decision, not a drift.
- **Q3 granularity**: the recommendation applies section resolution to the
  regeneration diff. If a regeneration is a true wholesale rewrite (every line
  changed), section resolution degenerates to `(file, *)` anyway and the
  file-level caveat applies — acceptable, but worth stating in the spec so the
  `(file-level)` pause label is not surprising.
- **Q5(b) evidence gap**: no run has exercised the proposed derived gate line.
  The first harness-p3 verify stage with `red team: on` and a second round is
  the natural place to exercise it.
- **Q7(b) discriminator shape**: the recommendation grounds the
  orchestrated-vs-standalone split in the dispatched `{write_scope}` slot (a
  signal that already exists), so no schema change is needed. Requirements may
  instead prefer an explicit instruction line in the PIPELINE template body,
  which is more legible but adds text to every dispatch. Either is acceptable;
  what is **not** acceptable is adopting the split without naming one of them,
  because the two regeneration rules then contradict each other silently.
- **Q6 legacy reports**: existing `verification.md` files carry no
  `research_id`. The recommendation reads absence as "a previous cycle's
  report", which is the safe direction (re-enter verify) — but it means the
  first cycle after the change re-enters verify once in every workstream that
  already has a passing report. Requirements should confirm that is acceptable
  rather than back-filling the field.

## Assumptions

- The working file `.pilot-toy/harness-p3-input.md` is treated as an evidence
  record, not a contract: its observations are cited, its proposals are
  re-derived here against the specs and either adopted, narrowed or declined on
  the record. Because `.pilot-toy/` is gitignored and disposable, it is
  reproduced verbatim as `evidence-appendix.md` in this spike directory, and
  every §A / §Bn / §C citation in this document resolves against that committed
  copy. The probe clones are disposable and keep no artifacts, so probe claims
  rest on the measurements recorded in §Probes rather than on retained files.
- Where the kickoff says "the cost of the change in files touched", counts are
  of files that must be *edited*, not of the lines within them, and include the
  `docs/spec/` contract alongside the `skills/.../references/` procedure text
  wherever the reference pastes from the spec.
- No requirement IDs are minted here; all classifications are advisory to the
  requirements stage.

## Recommended Next Step

**Proceed to requirements.** All eight questions are answered with a
recommendation, evidence, an explicit confidence claim and a file-count cost;
Q8 returns a bounded in/out list (4 in, 3 out), so the requirements stage
inherits **15 items — 11 question-level plus 4 Q8-IN** rather than eighteen
open ones. The recommendations resting on constructed rather than run evidence
(Q5(b) most of all) are labelled as such in their confidence clauses and are
cheap enough to specify and exercise in the same cycle.
