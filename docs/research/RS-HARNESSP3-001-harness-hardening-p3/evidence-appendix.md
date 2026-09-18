<!--
Evidence appendix for RS-HARNESSP3-001.

This file is a VERBATIM carry-over of the spike's working file
`.pilot-toy/harness-p3-input.md` as of 2026-09-18, reproduced here for
citability: `.pilot-toy/` is gitignored and disposable, so the §A / §B1-B12 /
§C citations in `findings.md` would otherwise be uncheckable by any reader but
the author. Nothing below has been edited.

Status: evidence record, NOT an SDD contract. Its *observations* are evidence;
its *proposals* are not decisions — `findings.md` re-derives each one against
the specs and adopts, narrows or declines it on the record.
-->

# harness-p3 — accumulated input

Running work file for the next `sdd-orchestrate` cycle (suggested workstream id
`harness-p3`, research entry). Gitignored, lives beside the pilot evidence.
Append; do not rewrite. Last updated 2026-09-18.

## A. Seed findings (from the N = 3 pilot, harness-p2 verification §Next Steps)

Committed source of truth: `docs/ws/harness-p2/verification.md` §Next Steps
(the "Pilot (N = 3)" section is the evidence).

1. **write-scope observation (a) is blind to a fix re-dispatch re-touching a path
   already dirty from the pipeline return** (`IN` read 0 for all four pilot fixes).
   → now MEASURED, see §B1.
2. **Phase detection cannot tell a prior cycle's `verification.md`** (`status: pass`,
   same date) from the new cycle's — compare `verification.research_id` to the
   kickoff's `research_id`.
3. Marker-4 specs write scope must name `docs/ws/<id>/traceability.md`.
4. Aggregate traceability regeneration belongs in its own orchestrator commit.
5. Pin the review `RETURN:` block verbatim. → widen, see §B2.
6. One-shot upstream review before a non-research entry.

Also still open from harness-p2: four pre-existing `qimpl-broken-ref` gc warnings;
gc `table_cells()` pipe escape; first live telemetry cycle in this repo.

## B. New findings from the red-team run (2026-09-18, toy clone)

Run shape: toy restored from `.pilot-toy/sdd-eval-toy.bundle` at `4aced03`
(RS-003, `status: pass`, 26 tests green) into the session scratchpad; verify stage
re-run with `red team: on`, `red input:` default (blue's report withheld).

### B1. Seed finding 1 is real, and a content hash closes it — MEASURED

At the R6 fix dispatch the tree already carried blue's uncommitted
`docs/ws/default/verification.md`. After the fix return, `git status --porcelain`
still showed it ` M` — the three-command check cannot distinguish "blue wrote it"
from "the fix leaf re-touched it". A per-path `shasum` snapshot taken before the
fix dispatch and diffed after proved it untouched (identical sha), and the leaf's
own return said the same. Proposal for p3: extend the write-scope snapshot from
path sets to `(path, sha)` pairs, so `IN` is decided by content change, not by
dirty-flag presence. Cheap: one `find | xargs shasum` per snapshot.

### B2. The **chunk verifier** `RETURN:` block drifts too — widen seed finding 5

The verifier returned its own key set — `scope:`, `checks_run:`,
`checks_skipped:`, `gates:`, `blocking_findings:`, `advisory_findings:`,
`notes:`, and a prose `budget_consumed: "6 of ≤15 tool calls; 1 of ≤2 test runs"`
instead of `{tool_calls: N, test_runs: N}`. Nine contract keys absent. Per
`return-contract.md` §Parsing that is only a `RETURN: KEYS MISSING` *warning*,
so it sailed through the per-chunk gate with `CHUNK_VERDICT: PASS` — correct per
spec, but it means no leaf template except the red one actually holds its block
shape under pressure. Seed finding 5 should be widened from "the review block" to
"every leaf template: pin the block verbatim in the template text". Consider also
whether a prose `budget_consumed` should be a malformed condition rather than a
silent pass-through — today §Parsing lists neither missing keys nor a malformed
`budget_consumed` shape as a pause.

### B3. Red earns its keep — evidence for REQ-REDB-HARNESSP2-001

Blue walked all nine acceptance criteria, ran the gate, probed out-of-suite with
8 scenarios, and reported 0 critical / 0 material / 1 minor. The review
(`VERDICT: APPROVE`) independently spot-checked and agreed. Red then broke
criterion 6 in 6 tool calls and 1 test run:

> R6 — spec §Tolerance "with `tolerance=0` the output is identical to the
> pre-tolerance engine **for every input**". `_is_finite_number` calls
> `math.isfinite(10**400)` → `OverflowError`. Fires even when both amounts are
> identical; the pre-tolerance engine returned a result for the same input.
> reproduce: `PYTHONPATH=src .venv/bin/python -c "from recon.engine import reconcile; reconcile([{'id':1,'amount':10**400}],[{'id':1,'amount':10**400}])"`

Reproduced independently by the orchestrator before routing. Withholding blue's
report from red (the default) did not stop red from finding the weak criterion —
it went at the newest, most-conditional clause, which is what the isolation
argument predicts.

Calibration held in both directions: R2 (heterogeneous `id` types raise
`TypeError` from `sorted()`) and R7 (`tolerance=NaN` silently mismatches every
finite pair; `tolerance="1"` raises `TypeError` not `ValueError`) were scored
**HELD/advisory** with the suspicion under `observed:` because the spec does not
constrain those inputs — they did not inflate `failures[]`. That is the
`BROKEN`-needs-a-repro rule working as designed.

### B4. `target.chunk: all` is the common case for a red break

R6's mapping: red lines carry no `affects`, so §5 starts at step 2 with the spec
from the `## Red team — <spec.md>` heading. `recon.md` is traced by BOTH plan
chunks → step 4 → `target.chunk: all`. On a small plan nearly every spec is
traced by more than one chunk, so `RED_BREAK` packets will almost always land as
whole-plan fixes. Worth asking in p3 whether that is intended (it is mechanical
and honest, but it widens the write scope and skips per-chunk budgeting), or
whether red should be asked to name the narrowest owning symbol.

### B5. Post-cycle fix has no home in the plan vocabulary

The R6 fix belongs to code written in the RS-002 cycle, whose plan is archived;
the active RS-003 plan's tasks are all `[x]`. The fix leaf invented a
`## Post-cycle Fixes` section in `plan.md` to record it (reasonable, unprompted),
and the chunk verifier separately flagged that the spec edit sat outside any
chunk write scope while correctly declining to judge it. Neither behaviour is
specified. p3 should decide where a verify-stage `RED_BREAK` fix is recorded when
no open chunk owns it.

### B6. Red left its worktree clean

The write-revert rule (REQ-REDB-HARNESSP2-003) was never exercised: red wrote its
adversarial test to `$TMPDIR` and `git status --porcelain` in the red worktree was
empty at return. Still untested in anger.

## C. Run log (this session)

- entry gc sweep on the skills repo: `GC: 0 fail, 6 warn` (4 known
  `qimpl-broken-ref` + 2 more).
- blue #1 → `COMPLETE`, `status: pending-red`, SCOPE CLEAN.
- review #1 → `VERDICT: APPROVE`; M1 = the RS-001 minor (`KeyError('id')`) had
  been dropped from §Next Steps by the RS-002 report and never restored. Real
  finding: an overwritten-per-cycle `verification.md` loses un-carried minors to
  git history. p3 candidate: does sdd-verify need a carry-forward rule?
- red #1 → `RED_VERDICT: BROKEN` (R6), 6 tool calls / 1 test run of ≤25 / ≤3.
- fix (RED_BREAK, iteration 1 of 3, `target.chunk: all`) → `COMPLETE`, 28 tests
  green; `_is_finite_number` gates `math.isfinite` on `float` only, new
  `_abs_difference` with an exact `Fraction` fallback on `OverflowError`
  (also covers `10**400` vs `1e308`); Q-IMPL-005 records the deviation.
- chunk verifier → `CHUNK_VERDICT: PASS` (block drift, §B2).
- per-chunk gate `proceed` → committed `7d42156` in the toy.
- blue #2 dispatched at `7d42156`; red re-run (once, by default, not an
  iteration) to follow.

## D. Carry to the next session

- Record the red-run outcome under `docs/ws/harness-p2/verification.md`
  §Next Steps by editing the `adversarial-verify.md` §Manual bullet (the run is
  the live half of REQ-REDB-HARNESSP2-001).
- Then open the workstream picker and create `harness-p3` at research entry,
  feeding it §A + §B of this file.

## B (continued) — findings from red round 2 / review round 2

### B7. The red re-run found a SECOND break of the same criterion — and it predates the fix

Red round 2 (after the R6 fix, blue #2, at `7d42156`) returned `BROKEN` again, on
criterion 6 again, by a different mechanism:

> R1 — `abs(l - r)` coerces an out-of-float-precision `int` to `float`. With
> `amount = 2**53+1` on one side and `9007199254740992.0` on the other, the
> difference is `0.0`, so `mismatched` is `[]` while plain `!=` is `True`. No
> `OverflowError`, so Q-IMPL-005's `Fraction` fallback never fires.
> reproduce: `PYTHONPATH=src .venv/bin/python -c "from recon.engine import reconcile; assert reconcile([{'id':1,'amount':2**53+1}],[{'id':1,'amount':9007199254740992.0}])['mismatched']==[1]"`

Orchestrator-verified, including against the pre-tolerance engine
(`git show 6387970~1:src/recon/engine.py`): it returned `[1]`. So the break is
real, is a criterion-6 violation, and **predates the R6 fix** — the fix neither
caused nor masked it. Two harness lessons:

- The default single red re-run is **not** a formality. It found new ground the
  first red round missed, on a criterion the first round had already attacked.
  Arguably red should be told which `Rn` was fixed so it does not re-derive the
  same criterion — or arguably not, since re-attacking it is what worked here.
- A red round that returns `BROKEN` on a *different* mechanism of the *same*
  criterion is not a regression of the fix, but the gate has no vocabulary to
  say so. The operator sees `RED_VERDICT: BROKEN` twice in a row with nothing
  distinguishing "the fix failed" from "there was a second bug behind it".
  p3 should consider a `supersedes:`/`new-ground:` marker on red `Rn` lines.

### B8. `REVIEW: CONTRADICTION` over-fires after a red-round pipeline re-dispatch

Review round 1 = `APPROVE`. Review round 2 (same stage, after the fix +
regenerated report) = `APPROVE_WITH_FIXES` with three material findings on
ground round 1 never named. By `loop-control.md` §6 that is class **b** — a
regression on new ground inside a fix loop at iteration ≥ 2 — so the stage gate
pauses with the contradiction fixture.

But the "new ground" is an artifact that was **wholly regenerated between the two
rounds** by the blue re-dispatch, not by fix #1. `W_N` ("fix #N wrote") is
computed from the fix dispatch only, so it does not contain
`docs/ws/default/verification.md` — the very file both reviews reviewed. Class b
therefore fires on what is really just a fresh review of a fresh artifact.

Proposal for p3: in the red-round sequence, `W_N` should be the union of the fix
dispatch's writes **and** the verify pipeline re-dispatch's writes. More generally:
whenever a stage's deliverable is regenerated rather than patched between review
rounds, arbitration's new-ground test needs to know that.

### B9. Review round 2's M3 is a real gap in the `pending-red` design

M3: `traceability.md` (per-ws and aggregate) carries `Verified: pass` for all four
requirements, inherited from the superseded `4aced03` report, while the current
`verification.md` is `status: pending-red`. If red came back `BROKEN` and the
operator stopped, the durable matrix would assert `pass` with nothing marking it
stale. The spec flips `pending-red → pass` on `verification.md` only. p3 should
decide whether the Verified column flips with it (and what it should read while
a red round is outstanding).

### C (continued) — run log

- blue #2 at `7d42156` → `COMPLETE`, SCOPE CLEAN, 28 green, R6 re-verified,
  RS-001 carry-forward restored (review round 1's M1 closed).
- red #2 → `RED_VERDICT: BROKEN` (new R1, precision loss; 6 tool calls / 1 test
  run). Red worktree clean again — write-revert rule still unexercised.
- review #2 → `VERDICT: APPROVE_WITH_FIXES` (M1 criterion-9 cell overstates what
  is unchanged inside `reconcile()`; M2 report does not record the R6 red round's
  disposition; M3 see B9). Round 1 vs round 2 → `REVIEW: CONTRADICTION (class b)`
  pause at the stage gate, see B8.
- Verify stage counter stands at `iteration 1 of 3` (the R6 fix). Awaiting
  operator: route red R1, and resolve the contradiction pause.

### B10. B2's remedy is confirmed by experiment — pin the block in every leaf template

Three chunk-verifier dispatches, same template, same model tier. The first two
(R6 fix round) used the template's prose "Return: findings … then the RETURN:
block" and both drifted: own key names, prose `budget_consumed`, nine contract
keys absent — each only a `RETURN: KEYS MISSING` warning, so both sailed through
their gates. For the third (R1 fix round) the dispatch text pinned the exact key
list, order, and the `{tool_calls: N, test_runs: N}` shape, with "Do not add,
rename or omit keys". That return was exactly conforming.

n = 3 and not controlled, but the direction is clear and the change is one
paragraph of template text. p3 action: move the literal `RETURN:` key block into
every leaf template body (pipeline, fix, fan-out leaf, chunk verifier, review,
red), not just red's — red was the only one that already carried it verbatim and
the only one that never drifted.

### C (continued) — run log, R1 fix round

- Operator decision: fix R1 rather than run a new cycle. Evaluated and rejected a
  full cycle — criterion 6 already states the violated contract, no replan
  trigger fired, the defect is one private helper. `accept round 2 (fix)` on the
  contradiction pause + `R1 -> fix`, merged as one iteration (2 of 3).
- Review M1/M2 deliberately NOT put in the fix packet: they are report-text
  findings against `verification.md`, which the blue re-dispatch regenerates
  wholesale — pointing a code leaf at a file it must not touch. They go into blue
  #3's deliverable contract instead. (p3 note: the packet shape has no slot for
  "findings that belong to the next pipeline dispatch rather than to a fix".)
- fix #2 (RED_BREAK R1, iteration 2 of 3) -> `COMPLETE`, 29 green. Root cause was
  narrower than R6's: `_abs_difference` used `OverflowError` to detect unsafe
  coercion, which catches ints outside float *range* but not outside float
  *precision*. Now subtracts a mixed int/float pair as exact `Fraction`s
  unconditionally; subsumes Q-IMPL-005. Recorded as Q-IMPL-006.
- Orchestrator-verified all branches independently: R1 -> [1], R6 overflow -> [],
  10**400 vs 1e308 -> [1], 1.5 vs 1.5 -> [], mixed pair at tolerance=1 -> [],
  nan -> [1], inf -> []. verification.md hash-verified untouched a SECOND time
  while reading ` M` in git status (B1 again).
- chunk verifier #3 -> `CHUNK_VERDICT: PASS`, RETURN conforming (see B10). Its
  Check 1 traced the return-type widening int|float -> int|float|Fraction out to
  its single consumer and argued totality/exactness — a real type-alignment
  check, worth citing in p3 as what Check 1 looks like when it works.
- Awaiting operator at the per-chunk gate.

### B11. The orchestrator rendered `TELEMETRY: on` and then wrote nothing — no forcing function

At the first verify gate the gate block carried `TELEMETRY: on (record written
after your decision)`. No record was ever appended: the toy clone's
`.sdd/telemetry.jsonl` does not exist, and nothing in the loop failed or warned
about it. `telemetry.md` makes the orchestrator the sole writer and specifies
`TELEMETRY: WRITE FAILED | OFF | .gitignore updated` as the only gate lines —
there is no line, and no check anywhere, for "on, and the append actually
happened". A silent omission therefore looks identical to a healthy cycle.

p3 candidates: (i) make the post-gate append a step the gate block asserts (e.g.
render the record's sequence number back on the next gate), or (ii) have
`tools/sdd-telemetry.py summarize` report gate-count-vs-record-count mismatch so
the gap is at least visible post-cycle. Note this also means the harness-p2 goal
"first live telemetry cycle in this repo" is still open — this run did not
deliver it.

### B12. Cross-repo Q-IMPL references trip gc

Recording the toy's `Q-IMPL-005`/`-006` ids verbatim in this repo's
`docs/ws/harness-p2/verification.md` turned the entry-baseline `GC: 0 fail, 6 warn`
into `FAIL: 2 findings` — `qimpl-undefined`, because those ids are defined in the
*toy's* spec corpus, not this one. Correct behaviour by gc's own rule, and worth
knowing: prose about another repo's artifacts must not quote its ID tokens.
Resolved by describing them instead ("a deviation entry in the toy's own spec").
p3 could consider whether gc should scope `qimpl-undefined` to ids that look
local, but the cheap answer is a convention, not a code change.

### C (continued) — run log, close-out

- fix #2 committed as toy `96c1546`.
- blue #3 at `96c1546` → `COMPLETE`, three review corrections applied, 29 green,
  plus its own 15×15 amount sweep of the `tolerance=0` identity clause (0
  violations). Re-review SKIPPED under the `APPROVE_WITH_FIXES` shortcut (round
  2's verdict carried to the stage gate) — which also avoided handing the B8
  arbitration bug another regenerated artifact to call "new ground".
- red #3 → `RED_VERDICT: HELD` (8 criteria; 26×26 pathological product + 20k
  fuzz; 2 advisory spec gaps, 0 `failures[]`). RETURN conforming — the pinned
  key block again (B10).
- Verify stage gate: `RETURN.status COMPLETE`, `SCOPE: CLEAN`, `RED_VERDICT: HELD`,
  `VERDICT: APPROVE_WITH_FIXES` (fixes applied), `iteration 2 of 3` → operator
  `proceed`. Orchestrator flipped `pending-red → pass` and reconciled the report's
  four narrative references to the flip, then committed toy `fbebd05`.
- Toy re-bundled to `.pilot-toy/sdd-eval-toy.bundle` at `fbebd05` (was `4aced03`).
- Outcome recorded in this repo's `docs/ws/harness-p2/verification.md` §Next Steps
  (the adversarial-verify.md §Manual bullet). `GC: 0 fail, 6 warn` — back to the
  entry baseline. `tools/sdd-skill-lint.py` exit 0.
