---
status: Approved
last_updated: 2026-09-22
requires:
  - REQ-HARN-001
  - REQ-HARN-002
  - REQ-HARN-003
  - REQ-HARN-004
  - REQ-HARN-005
  - REQ-HARN-006
  - REQ-HARN-007
  - REQ-HARN-008
  - REQ-HARN-027
  - REQ-HARN-HARNESSP5-001
  - REQ-HARN-HARNESSP6-002
  - REQ-ORCH-HARNESSP6-001
  - REQ-ORCH-HARNESSP6-002
  - REQ-HARN-PIPELINEOBSERVABILITY-001
  - REQ-HARN-PIPELINEOBSERVABILITY-002
  - REQ-HARN-PIPELINEOBSERVABILITY-003
  - REQ-HARN-PIPELINEOBSERVABILITY-006
---

# Harness Loop Control

## Context

The orchestrated SDD loop (`sdd-orchestrate` driving `sdd-implement`,
`sdd-review`, `sdd-replan`) has no upper bound on how many times it can
loop-back-to-fix a stage, no bound on how many times a cycle can re-enter
`sdd-replan`, and no durable trace of what an implementer tried before it got
stuck. RS-008 Q1 established that every counter this needs can live in an
existing place: the fix-iteration count is per-session, the replan re-entry
count is *derived* from `plan-history/` archives, and the attempt ledger's only
durable trace is a bounded checkpoint written into the plan's existing
blocked-task note. RS-008 Q3 supplied the ledger and `budget_consumed` shapes.

This spec defines the loop-control contracts: the two caps, the budget slot and
its exhaustion path, the attempt ledger with the oscillation rule, the
circuit-break checkpoint and its composition from the `RETURN:` block (see
`harness-return-contract.md`), the marker-4 rooting rule and the
no-new-artifact invariant. It fulfils REQ-HARN-001..008 and REQ-HARN-027.

Standing constraints inherited from `orchestration.md`: no new on-disk
artifact type (REQ-ORCH-004), reviews ephemeral (REQ-ORCH-013), no loop-position
marker or loop log (REQ-ORCH-014), fix re-dispatch carries findings + paths
only (REQ-ORCH-012). Standalone `sdd-implement` (no orchestrator) keeps its
current behavior; everything orchestrate-only here is a layer on top
(REQ-ORCH-001).

## Design

### State Placement

Every piece of loop-control state has exactly one home. Nothing is written to a
new file; nothing is written to `kickoff.md` frontmatter.

| State | Home | Lifetime | Resume in a new session |
|---|---|---|---|
| Fix-iteration count, per stage | orchestrator session memory | session | restarts at 0 — a new session is itself a human intervention |
| Redo count, per chunk — `chunk_redo_count[<chunk header>]` against `REDO_MAX` (verifier-FAIL / merge-abort / `PARTIAL` continue redos, i.e. every `fix` at the per-chunk gate) | orchestrator session memory | session | restarts at 0 |
| Replan re-entry count, per cycle | **derived** from `plan-history/*-replan-*.md` archives | derived | recomputed on every replan trigger |
| Attempt ledger, per task | leaf (implementer) context | session | not resumed — the checkpoint is what a fresh session reads |
| Circuit-break checkpoint | plan's blocked-task note under the task | durable | read by `sdd-replan` Step 1 as the stuck state |

**Why per-session, not persisted, for the fix count**: every loop-back-to-fix is
already an explicit operator decision at the gate (REQ-ORCH-011). The cap
exists to stop unattended ping-pong *inside one session*. Persisting the count
would guard only against an operator deliberately restarting sessions to evade
it — not a threat model worth a new artifact, and REQ-ORCH-014 forbids the
obvious homes (marker file, kickoff loop log).

### Fix-Loop Cap (REQ-HARN-001)

- `FIX_LOOP_MAX` is an orchestrator constant, default **3**, stated in
  `sdd-orchestrate/SKILL.md` §The gate. The operator may raise it for one stage
  at the gate by an explicit decision (that decision is *not* a fix iteration).
- The counter is keyed by **stage** and increments once per fix re-dispatch of
  that stage's pipeline subagent. It does not increment on `proceed`, `stop`,
  or a replan route.
- Every fix re-dispatch prompt carries the literal line
  `iteration N of MAX` (e.g. `iteration 2 of 3`) inside the repair packet
  (`harness-return-contract.md` §Repair Packet). `N of N` is the last attempt
  before circuit-break.
- **Exhaustion**: when the stage's review returns `VERDICT: REJECT` (or
  `APPROVE_WITH_FIXES` and the operator would fix again) after iteration `MAX`,
  the orchestrator does **not** dispatch another fix. It renders the gate with a
  **compiled findings log** and offers only `stop | manual intervention |
  authorize extra iteration`. An authorized extra iteration raises the cap for
  that stage by one and is logged at the gate as such.

Compiled findings log (gate text, ephemeral):

```
Fix loop exhausted — stage: specs, 3 of 3 iterations
  iteration 1: C1 <finding text> — <file:section>; M1 <...>
  iteration 2: C1 (persisting) <finding text>; M2 <...>
  iteration 3: C1 (persisting) <finding text>
  Options: stop | manual intervention | authorize extra iteration (cap → 4)
```

Each line is the review's Critical/Material finding line lifted verbatim, one
group per iteration; no reviewer reasoning, no prose summary (REQ-ORCH-012).

**The verdict is the routing — recorded as in force** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-HARN-PIPELINEOBSERVABILITY-001; REQ-HARN-013 as amended; the record of why is §Pipeline-Observability Amendment).

`loop-back-to-fix` routes by the consumed verdict exactly as
`skills/review/SKILL.md` §Verdict definitions defines it:

| Consumed verdict | Route | Counted by |
|---|---|---|
| `REJECT` | re-dispatch the pipeline leaf with a repair packet, then re-run this stage's review | `reject_run` (below) |
| `APPROVE_WITH_FIXES` | re-dispatch with the packet, then **proceed without re-review** — the next stage's review reads the fixed artifact as its upstream; a re-review is an explicit operator opt-in at this gate, never the default | nothing |
| `APPROVE` | proceed | nothing |

The repair packet carries **Critical/Material findings only** — an
`APPROVE_WITH_FIXES` packet carries Material findings (its report holds no
Critical finding, by the disjoint definitions of `review.md`
§Report Format), a `REJECT` packet carries Critical and
Material. An
`APPROVE_WITH_FIXES` returned at or after the cap is **not** an exhaustion: its
fix is applied and the stage proceeds. Why: a fresh reviewer over a growing
artifact is a generator no cap converges — eight zero-blocking
`APPROVE_WITH_FIXES` rounds were each fixed and re-reviewed, and every re-review
raised new Material ground. V2's `ROUND_MAX` and its two-consecutive-`APPROVE_WITH_FIXES`
terminator are **not adopted**: under this routing an `APPROVE_WITH_FIXES` ends
the stage's review chain, so nothing they bound can arise (Q-REQ-PO-A). The
three caps stay three.

This routing **landed on the branch before the specs stage**; its comparands
are the skill-lint pins, never a commit: the `REQUIRED` row `proceeds
**without re-review**` on `skills/orchestrate/SKILL.md`, the `REQUIRED` row
`GROWTH: ` on `skills/orchestrate/references/loop-control.md`, and the
`FORBIDDEN` phrase `then re-run the review for this stage`. The skill side is
`skills/orchestrate/references/loop-control.md` §5a (default proceed) and §2a (an
`APPROVE_WITH_FIXES` at or after the cap is not an exhaustion);
`skills/orchestrate/references/return-contract.md` §6's branching table and
`harness-return-contract.md` §VERDICT Token already read fix-then-proceed with
re-review on opt-in only, and `orchestration.md` §Gate Protocol / §v5 Harness
Hardening point here rather than restating the routing.

**The counted quantity is `reject_run`** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-HARN-001 as amended; the record of why is §Pipeline-Observability Amendment).

§Fix-Loop Cap's "increments once per fix re-dispatch" is **narrowed** to what
its acceptance criterion always read: the counter is the run of
**consecutive consumed `REJECT`s** per stage per session, `reject_run`.

- A consumed `APPROVE` or `APPROVE_WITH_FIXES` resets `reject_run` to 0; under
  the routing above an `APPROVE_WITH_FIXES` can never be "at cap" and never
  renders the exhausted gate. §Fix-Loop Cap's parenthesis "(or
  `APPROVE_WITH_FIXES` and the operator would fix again)" in its exhaustion
  bullet is **superseded** by this section: exhaustion is `REJECT` consumed
  with `reject_run = MAX`.
- Re-dispatches that count **nothing**: a verdict **voided** under
  `harness-write-scope.md` §Git-State Observation, a `post-manual`
  review (below), and a third opinion (`arbitrated-handoff.md` §Third Opinion —
  the existing precedent that a re-dispatch is not a fix iteration).
- `iteration N of MAX` now reports `reject_run`; the compiled findings log's
  header `N of MAX iterations` reports the same number. The `explicit
  operator-authorized extra iteration` option is unchanged — kickoff constraint
  4 of this cycle is operator policy, not a corpus rule.
- The skill side states the consecutive-`REJECT` rule in
  `skills/orchestrate/references/loop-control.md` §2, pinned by skill-lint `REQUIRED` row p4 on the
  phrase `consecutive consumed` in that file; the telemetry witness is cross-field
  assertion (b) of `telemetry-reader.md` §Schema Lint.
- `CLAUDE.md` §Gate vocabulary names the counted quantity and no longer says
  `iteration N of FIX_LOOP_MAX` (`project-docs.md` §`CLAUDE.md`).

Consistency: REQ-HARN-002 (`REPLAN_MAX`) is untouched, and so is the per-chunk redo cap — `REDO_MAX` is defined only in §Redo Cap per Chunk of this spec (no requirement establishes it; REQ-HARN-008 governs the circuit-break checkpoint written when a cap fires, not the cap — Q-REQ-PO-AI);
REQ-HARN-011's `iteration` field carries `reject_run`; REQ-ORCH-018's
no-actionable-findings pause and REQ-ORCH-034's order are unchanged.

**A manual intervention is followed by a `post-manual` review** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-HARN-PIPELINEOBSERVABILITY-003; REQ-HARN-001 as amended; the record of why is §Pipeline-Observability Amendment).

When the operator chooses `manual intervention` at an exhausted gate — or
otherwise edits the stage deliverable at a gate — the orchestrator:

1. observes its own edits as it observes a leaf's writes: the `COMMIT:`
   comparand of `harness-commit-fidelity.md` (REQ-HARN-HARNESSP4-001) runs over
   the manual edit's commit range;
2. dispatches an **ordinary review** of this stage (the REVIEW template,
   unchanged inputs per REQ-REV-003) labelled `post-manual`;
3. withholds `proceed` until that review's verdict is consumed; the verdict
   routes per the routing table above (a `REJECT` starts a new `reject_run` at
   1; an `APPROVE_WITH_FIXES` fixes and proceeds).

**Footprint** (Q-REQ-PO-AC) — the review is an ordinary `review` dispatch and
leaves exactly this trace: `dispatch.kind = review`, `dispatch.reason =
POST_MANUAL` (a member of the repair-packet `reason` enum, **not** in the
fix-only subset), `dispatch.stage` = the stage whose gate the intervention
happened at, `dispatch.iteration` = that stage's current `reject_run`. Its gate
record carries `gate.fix_iteration` **equal to** the preceding same-stage gate
record's value — the review counts nothing — and its `gate.decision` routes like
any review's. The existing `[reason-review]` lint warning is keyed on `reason =
REVIEW` at `iteration ≥ 1` with no loop-back; `POST_MANUAL` is a distinct
member, so it does not fire and needs no exception clause. The `post-manual`
review does **not** increment `reject_run` (precedent: a third opinion is not a
fix iteration, `arbitrated-handoff.md` §Third Opinion).

**At a per-chunk gate** (implement stage): a manual intervention or an operator
edit of the chunk's deliverable — including after the void rule's exhaustion
(`harness-write-scope.md` §Git-State Observation, `voided_redispatch_count` at
the `REDO_MAX` value) or §Redo Cap per Chunk renders `stop │ manual
intervention` — dispatches the `post-manual` review with that chunk's
implement-stage inputs (its plan tasks and the specs they trace to,
`dispatch.chunk = N`) and withholds that chunk's `proceed` until the verdict is
consumed; the chunk's `gate.redo_count` (`Redo: N of REDO_MAX`) is untouched,
and the chunk verifier is **not** re-run by it — it is a review, not a verifier.

This rule applies from the first gate of this cycle (kickoff decision 3),
before any code lands, because it is a process rule. The skill side is
`skills/orchestrate/references/loop-control.md` **§2b**, whose `manual
intervention` option names the `post-manual` review and states that `proceed`
is withheld until its record exists, pinned by skill-lint `REQUIRED` row p5
(`post-manual`); the telemetry witness is cross-field assertion (c) of
`telemetry-reader.md` §Schema Lint. REQ-HARN-019 holds: the routing is
orchestrator-only.

### Redo Cap per Chunk (extension, see Open Questions)

Under the implement stage a second loop exists below the review loop: a chunk
verifier `CHUNK_VERDICT: FAIL`, a fan-out merge abort or a `PARTIAL` return
leads to the operator choosing `fix` at the **per-chunk gate**
(`harness-chunk-verifier.md` §Sequencing — Sequential Mode), which triggers a
redo dispatch carrying a repair packet. Redos are counted **per chunk** in the
named counter `chunk_redo_count[<chunk header>]` — incremented on every `fix`
chosen at that chunk's per-chunk gate, never on `proceed` / `stop` / a replan
route — against the orchestrator constant `REDO_MAX`, default **3** (the gate
shows `Redo: N of REDO_MAX`), with the same exhaustion behavior (gate with
compiled findings — here the verifier's findings — and no automatic fourth
redo). The redo counter is independent of the stage's
fix-iteration counter because the implement-stage review runs once after all
chunks (REQ-HARN-016), so review-driven and verifier-driven loops are distinct.

### Replan Re-entry Cap, Derived (REQ-HARN-002, REQ-HARN-003)

`REPLAN_MAX` is an orchestrator constant, default **3**. The count is never
stored; on every replan trigger the orchestrator recomputes it:

```
kickoff_date = frontmatter `date:` of <kickoff>            # PRIMARY — mandatory on every orchestrate-written kickoff
             | legacy fallback (kickoff predates the date: rule):
               git log -1 --format=%cs -S'research_id: <id>' -- <kickoff>
               # = the most recent commit whose diff of <kickoff> changed the `research_id:` line,
               #   i.e. the commit that started the CURRENT cycle (<id> = the kickoff's research_id)
             | neither determinable → cap treated as REACHED (see below)
count = number of files f in <plan-history>/ such that
          basename(f) matches ^(\d{4}-\d{2}-\d{2})-(m\d+-)?replan-.*\.md$
          and group(1) >= kickoff_date
```

- **`date:` is mandatory** in the frontmatter of every kickoff `sdd-orchestrate`
  §KICKOFF writes (`docs/handoff/kickoff.md`; under marker `4`
  `docs/ws/<id>/kickoff.md`); a kickoff written without it is a template
  violation the orchestrator's self-check catches before the pipeline starts.
- The legacy fallback is deliberately **not** `git log --diff-filter=A --follow
  --format=%cs -- <kickoff> | tail -1`: that yields the file's first creation,
  which is wrong once the kickoff is overwritten per cycle. The `-S'research_id:
  <id>'` pickaxe finds the commit that introduced the current cycle's
  `research_id:` line, which is the cycle start.
- If **neither** source is determinable (no `date:`, kickoff uncommitted or
  `research_id:` unmatched), the cap is **treated as reached**: the gate shows
  `replan re-entry cap: kickoff date undeterminable — treated as reached` with
  every `-replan-` archive listed, and routes into `sdd-replan` only on an
  explicit operator decision. The cap is never silently unreachable.

- `<plan-history>` is `docs/plan-history/` under marker `3` and
  `docs/ws/<id>/plan-history/` under marker `4` (see §Marker-4 Rooting).
- Archives whose filename lacks the `-replan-` segment (`sdd-plan` rewrite
  archives `{date}-{reason}.md`, milestone-complete archives
  `{date}-m{N}-complete.md`) never count. Archives dated before the kickoff date
  never count (they belong to a previous cycle).
- Minor in-place replans leave no archive and are deliberately not counted —
  they are task reorders, not the approach oscillation the cap targets.
- When `count >= REPLAN_MAX` the orchestrator surfaces the cap as a gate event
  (REQ-ORCH-017 shape) naming the count, the cap and the counted archive
  filenames, and does not route into `sdd-replan` without an explicit operator
  decision.

**`-replan-` is a stated contract.** `sdd-replan/SKILL.md` Step 4 must state:
"every archive this skill writes carries the `-replan-` segment
(`{date}-replan-{reason}.md`; per milestone `{date}-m{N}-replan-{reason}.md`);
no other skill may use that segment." `sdd-plan`'s rewrite archives and
milestone-complete archives must not contain `-replan-`. The linter carries a
`REQUIRED` row for the pattern in `sdd-replan/SKILL.md` (`skill-lint-v5.md`
§REQUIRED Rows). This turns the implicit convention `plan-management.md`
§Plan History already documents into a load-bearing one.

**Why derived, not stored**: the archives are already written by `sdd-replan`
for exactly the significant replans that matter; deriving from them adds no
artifact (REQ-HARN-027) and is correct across sessions and workstreams for free.

### Budget Slot (REQ-HARN-004)

Every dispatch template — pipeline, fix re-dispatch, fan-out leaf, review,
chunk verifier — carries `Budget: {budget}`. The orchestrator fills it on every
dispatch; an empty slot is a template violation the orchestrator must catch
before dispatching (self-check, not lint).

Budget grammar — a comma-separated list of `<count> <unit>` or `≤ <count>
<unit>` terms in **observable units** the subagent can count about itself:

```
Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs          # implement, per chunk
Budget: ≤ 15 tool calls, read-only                          # review
Budget: 1 chunk, ≤ 15 tool calls, ≤ 2 test runs, read-only  # chunk verifier
Budget: ~70 tool calls, no prototypes                       # pipeline (specs stage)
```

Recognized units: `chunk(s)`, `task(s)`, `tool call(s)`, `test run(s)`,
`approach(es)`; `read-only` and `no prototypes` are qualifiers. Wall-clock
units are forbidden (the existing lint `FORBIDDEN` rows `30 min max` /
`budget: 30min` already enforce this). Default budgets per dispatch type live in
`references/return-contract.md` next to the `RETURN:` field table so the
`budget` ↔ `budget_consumed` pairing is documented in one place.

**The implement test-run budget is derived** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-HARN-PIPELINEOBSERVABILITY-006; the record of why is §Pipeline-Observability Amendment).

§Budget Slot's implement row is sized by the formula

```
test_runs = 2 × mutations + gates
```

where `mutations` is the number of mutation/reversion demonstrations the
chunk's tasks name (each is one red run and one green run — kickoff constraint
2 makes every binding demonstrate its reversion) and `gates` is the number of
quality-gate commands the chunk runs. The implement template of
`skills/orchestrate/references/dispatch-templates.md` states the derivation and its worked example
dispatches a chunk naming 2 mutations and 2 gates with `≤ 6 test runs`; the
orchestrate skill's implement dispatch step cites it. The fixed `≤ 3 test runs`
example is retired: the consumer-geometry chunks overran 8 against 6 and 18
against 12 under it, so a budget overrun was the honest outcome of an honest
chunk. REQ-HARN-005 (exhaustion) and REQ-TELEM-HARNESSP2-002 (the parsed
integer form, which the formula yields) are unchanged; the verifier's own `≤ 2
test runs` example is separate.

### Budget Exhaustion (REQ-HARN-005)

A leaf that reaches any term of its stated budget must:

1. Stop starting new work (finish or revert the in-flight edit so the tree is
   consistent).
2. If exhaustion occurred mid-task, compose the circuit-break checkpoint
   (§Circuit-Break Checkpoint). Sequential implementer: write it into the plan.
   Fan-out leaf: return it (leaves are barred from the plan).
3. Return a `RETURN:` block with `status: BUDGET_EXHAUSTED` and
   `budget_consumed` in **the same units** the `Budget:` slot was stated in,
   e.g. `budget_consumed: {tool_calls: 25, test_runs: 3, chunks: 0}`.

The orchestrator uses `budget_consumed` to size the next repair packet's
`budget` (typically the remaining or a fresh per-chunk allowance) and surfaces
`RETURN.status` + `budget_consumed` against the dispatched `Budget:` at the gate
(REQ-ORCH-034). A `status: BUDGET_EXHAUSTED` without `budget_consumed` is
**malformed** (`harness-return-contract.md` §Malformed Returns) and pauses at the
gate.

**Recorded v1 limitation**: `budget_consumed` is self-reported. The harness
exposes no tool-call counter to the orchestrator, so adherence is as
trustworthy as the leaf. This is documented in `references/return-contract.md`
and is not fixed in this cycle (telemetry is deferred, catalogue D11).

### Attempt Ledger (REQ-HARN-006)

`sdd-implement` Step 3 keeps, per task, an in-context ledger with one entry per
attempted fix and a `verified_do_not_touch` list:

```yaml
ledger:                       # newest last; one line per value, no prose
  - attempt: 1
    hypothesis: "gaps keyed by symbol"
    change: "engine.py: key by contract_id"
    result: "test_drift passes; test_gap_report still fails"
  - attempt: 2
    hypothesis: "off-by-one in window"
    change: "engine.py:140 range(n+1)"
    result: "test_gap_report passes; test_drift REGRESSED"
verified_do_not_touch: [tests/test_bootstrap.py, src/recon/bootstrap.py]
```

Invariants:

- `attempt` is a 1-based ordinal; `hypothesis`, `change`, `result` are each one
  line. `change` names files (and lines where useful); `result` names which
  tests now pass / fail.
- `verified_do_not_touch` lists paths whose tests pass and that later attempts
  must not modify; an attempt whose `change` touches a listed path is a rule
  violation the implementer must revert before continuing.
- The ledger lives in the leaf's context only. Its durable traces are the
  `RETURN.ledger` field (when dispatched) and the checkpoint. It is **never**
  written to `docs/spec/*.md`, `docs/handoff/kickoff.md`, or any new file.
- The ledger is not a Q-IMPL entry. Q-IMPL records a spec-deviation *decision*
  (`deviation-protocol.md`); the ledger records *attempts*. When an attempt
  reveals a spec ambiguity the implementer files a Q-IMPL entry as today and
  cites its id in `open_questions` and in the checkpoint — never duplicating
  the entry's text.

### Oscillation Rule (REQ-HARN-007)

Step 3 stuck detection fires on its existing triggers **and** on either
oscillation condition, evaluated as string comparisons over the ledger after
every attempt:

- **(a) Regression oscillation** — an attempt's `result` reports a test failing
  that an earlier attempt's `result` reported passing (a fix re-introduced a
  fixed failure). Fixture: `attempt 1: test_drift passes` then `attempt 2:
  test_drift REGRESSED` → stuck.
- **(b) Repeated patch** — an attempt's `change` equals (after whitespace
  normalization) an earlier attempt's `change`.

`sdd-implement/SKILL.md` Step 3 must list both under the word **"oscillation"**
(lint marker, `skill-lint-v5.md`). Firing follows the existing stuck path:
compose the checkpoint, then recommend / trigger `sdd-replan`.

### Circuit-Break Checkpoint (REQ-HARN-008)

Trigger: stuck detection (including oscillation), budget exhaustion mid-task,
the stage fix-loop cap (`FIX_LOOP_MAX`) firing on an implement task, or the
per-chunk redo cap (`chunk_redo_count[<chunk>]` reaching `REDO_MAX`) firing at
that chunk's per-chunk gate.

Slot: the blocked-task note under that task in the plan — the slot `sdd-replan`
Step 4 already defines ("mark blocked tasks — note why they're blocked and what
unblocks them"). No new section, no new file.

Format (bounded, ≤ ~15 lines, no traceback frames):

```markdown
3. [implement] SPEC-RECON: reconciliation engine — traces to recon.md
   **Blocked** (2026-09-17, oscillation): checkpoint
   - failing: tests/test_recon.py::test_gap_report — AssertionError: expected 3 gaps, got 2
   - failing: tests/test_recon.py::test_drift — REGRESSED after attempt 2
   - last hypothesis: off-by-one in window
   - attempt 1: engine.py key by contract_id -> test_drift passes; test_gap_report still fails
   - attempt 2: engine.py:140 range(n+1) -> test_gap_report passes; test_drift REGRESSED
   - open question: spec §Gap report silent on overlapping windows — see Q-IMPL-021
   - unblocks: resolve Q-IMPL-021, then retry with windows treated as one gap
```

Composition from the `RETURN:` block (there is **no dedicated checkpoint
field**):

| Checkpoint line | Source |
|---|---|
| `failing:` lines (test + one-line reason) | `failures[].test` + `failures[].message` |
| `last hypothesis:` | last `ledger[].hypothesis` |
| `attempt N:` one-liners | `ledger[].change` + ` -> ` + `ledger[].result` |
| `open question:` | `open_questions[]` (cites a Q-IMPL id where filed) |
| trigger label `(oscillation | budget | fix-cap)` | orchestrator / implementer state |

Who writes it: in sequential mode the implementer writes it directly (it owns
the plan in that dispatch's write scope). Under fan-out the leaf returns the
`RETURN:` fields and the orchestrator composes and applies the note in
`fan-out.md` §3e post-merge bookkeeping, since leaves are barred from the plan.

`sdd-replan` Step 1 reads this note as its "stuck state" input in place of
"recent conversation context" (which does not exist across a dispatch
boundary). Full tracebacks are never stored; they are regenerated by re-running
the named tests.

Phase-detection neutrality: a blocked note does not change phase detection
(the plan still has incomplete tasks → implement stage) and cannot make the plan
stale (staleness compares the plan against *upstream* dates only).

### Marker-4 Rooting Rule

Under `docs/.sdd-version` == `4` every path above resolves to the active
workstream: the plan is `docs/ws/<id>/plan.md`, archives are
`docs/ws/<id>/plan-history/`, the kickoff is `docs/ws/<id>/kickoff.md`, so the
replan re-entry count and the checkpoint are per workstream; the revert/merge
target is the workstream branch, not `main` (`ws-integration.md`). Under marker
`3` the flat paths apply unchanged. `docs/.sdd-version` remains the sole gate.

### No-New-Artifact Invariant (REQ-HARN-027)

Everything in this spec and its siblings fits inside existing artifacts and
dispatch templates:

| Mechanism | Where it lives | New file? |
|---|---|---|
| fix / redo counts | session memory | no |
| replan count | derived from `plan-history/` | no |
| ledger | leaf context; `RETURN.ledger` | no |
| checkpoint | plan blocked-task note | no |
| `RETURN:`, repair packet, `VERDICT:`, `CHUNK_VERDICT:`, `SCOPE:` | return / gate text | no |
| write scope, budget | template slots | no |
| procedure text | `skills/sdd-orchestrate/references/*.md` | skill text, not a project artifact — permitted |

REQ-ORCH-004, -013, -014 hold verbatim; no `docs/reviews/`, `.sdd/` or
telemetry file is created.

### Plan Completion Ownership Under Orchestration (REQ-HARN-HARNESSP5-001)

[Added 2026-09-19, harness-p5 — REQ-HARN-HARNESSP5-001, ratified as Q-REQ-P5-C.
Owner decided at specs: this spec, because the gate order lives here
(`ws-orchestration.md` was the alternative). Evidence: RS-HARNESSP5-001 §Q3 —
the p4 implement round-1 review C1 showed the last-chunk leaf asserting a
completion the stage review had not yet decided.]

Under orchestrated per-chunk dispatch, `sdd-implement` Step 6.4's flip of
`plan.md` `status:` to `complete` has one owner and one moment:

| Actor | Writes `status:`? | Rule |
|---|---|---|
| chunk leaf (per-chunk PIPELINE dispatch) | **never** | ticks its tasks `[x]`; `dispatch-templates.md` §PIPELINE per-chunk says "tick tasks, never `status:`" — a leaf cannot know the stage review's verdict |
| `sdd-verify` | **never** | never writes the plan; a verify-on-entry flip would widen its scope onto an upstream artifact and leave a resumed session reading `implementing` on a fully ticked plan |
| **orchestrator** | **yes** — at the implement **stage gate** `proceed`, after the stage review's `VERDICT:`, never at the last per-chunk gate | edits `status:` only, in its own bookkeeping commit (`references/write-scope.md` §7 gains a second bookkeeping entry beside aggregate regeneration); the `research_id:` stamp is `sdd-plan`'s and is untouched (`cycle-identity.md`) |
| `sdd-implement`, direct session (no orchestrator) | yes — Step 6.4 unchanged | one sentence there states the orchestrated exception |

**Precondition — the completion parse.** At `proceed` the orchestrator parses
the plan: every numbered chunk task must be `[x]`. Then the flip is signal 8b of
§Gate Signal Order — after the `COMMIT:` closing line, because `HEAD_landed` is
captured before any bookkeeping commit, so the flip is outside the `COMMIT:`
range and never renders `landed, not observed`.

**Else-branch.** When the parse shows an unticked task (for example one the
stage review accepted as deferred), the flip is **withheld** and the gate
**pauses** on the own-line `PLAN: INCOMPLETE (N of M ticked)` — signal 6b,
rendered pre-decision after `REVIEW: CONTRADICTION` and before `TELEMETRY:`,
because the tick state exists on the leaf's return — offering **`replan │ stop`
only**. `proceed` is not offered, so verify is never dispatched while `plan.md`
reads `implementing`, and phase detection (`cycle-identity.md`,
REQ-CYCID-HARNESSP3-001) keeps reading the plan as incomplete until a replan
closes the unticked tasks (descoped or removed, archived per plan archival) and
the gate is re-rendered. `PLAN:` joins the **pause family** of
`skills/sdd-orchestrate/references/loop-control.md` §6 as its **fifth** member
(after the three originals and `REVIEW: CONTRADICTION`, which
`arbitrated-handoff.md` registers there as the fourth) — and the only
two-option one; it carries no finding text, only the two counts. REQUIRED:
`references/loop-control.md` §6 lists `PLAN: INCOMPLETE (N of M ticked)` as
member five with its `replan │ stop` option set and the precedence rule below.

**Precedence when signals 6 and 6b fire at the same gate.** Both are
pre-decision pauses and their option sets are disjoint — signal 6 offers
`accept round N (proceed, note)`, signal 6b withholds `proceed` outright.
**6b supersedes**: when `PLAN: INCOMPLETE` renders, the gate's option set is
6b's `replan │ stop` and no option resolving to `proceed` is offered, whichever
options signal 6 printed. Rationale: the withheld `proceed` is the stricter
constraint, and a contradiction accepted "proceed, note" would otherwise
dispatch verify against a plan that still reads `implementing` — exactly the
state 6b exists to prevent. Signal 6's block still renders (its finding is real
and the operator needs it when choosing `replan`); only its options are
suppressed, and one `replan` closes both. No new
artifact: the parse reads the plan the leaf already wrote, and the counts are
gate text (REQ-HARN-027).

**Why not the last-chunk leaf, why not verify.** The leaf would assert a
completion the stage review has not decided (premature; p4 C1); verify would
read the phase wrong on resumption and widen its write scope onto the plan. The
orchestrator at `proceed` is the one actor that has seen the review verdict and
already owns a post-gate bookkeeping commit.

### Convergence Signal — L2 (REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-001, REQ-ORCH-HARNESSP6-002) [high-uncertainty]

[Added 2026-09-20, harness-p6 — L2, deferred through harness-p3, -p4 and -p5 and
shipped here on explicit operator direction recorded in
`docs/ws/harness-p6/kickoff.md`]

**What it is.** When two or more verification layers in one cycle produce
findings that share a root cause, the harness surfaces that convergence as its
own gate line instead of leaving the correlation to the operator's eye. L2 is an
**orchestrator-derived gate signal**. It adds **no field to any leaf's `RETURN:`
shape**, introduces no root-cause field, and is **not a fifth verification
layer** — the four-layer verification table stays byte-unchanged wherever it
appears. Everything L2 needs is already returned by the layers.

**Shipped scope: shared-id convergence plus a sectionless-file rule, stated
explicitly.**

**[Updated: 2026-09-20 — descoped at replan, caused by the Chunk 8 resolving
spike (`docs/ws/harness-p6/plan.md` §Chunk 8 → Spike Findings). The co-located
`(file, section)` key is **no longer the primary cluster key**: replayed over the
recorded findings of the harness-p3, -p4 and -p5 cycles it formed **zero**
clusters — in every one of the three cycles, and zero in total — and against the
harness-p3 §L2 origin case it clusters **none** of the three layers, not two of
the three as this section previously asserted. That 2-of-3 figure was never
measured against the record; it is refuted by the replay and is withdrawn here
and wherever else it was copied. The floor this section now states is what the
spike's own data supports.]**

L2 clusters findings that already carry a **shared identifier or a shared
location**. Conceptual convergence — findings sharing a root cause but naming no
common id, no common file and no common section, as in the three-layer origin
case the signal was named for — **cannot** be derived from what layers already
return: it needs either a root-cause field on a leaf's `RETURN:` or a fifth
layer whose job is correlation, and both are standing exclusions. This is stated
here rather than left implicit so that verification is never asked to prove a
property the design does not deliver. Against the origin case
(`docs/ws/harness-p3/verification.md` §L2 — blue's dropped `git add` in Chunk 7,
review's C1 on an unexercised requirement, red's R4 on aggregate drift) the
shipped form clusters **nothing**: the two members whose locations the record
preserves differ at **file** level and cite different ids, and the third was
never durably recorded at all. That is the measured, recorded cost of shipping
without a new field or a new layer, and the design does not claim more.

**The cluster rule.** Two or more findings form a **cluster** when all three
conditions hold:

| # | Condition |
|---|---|
| (i) | they come from **different** layers or second-executors — blue pipeline, chunk verifier, review, red |
| (ii) | they belong to the **same cycle**, by the `research_id` stamp cycle identity already uses (`cycle-identity.md`) |
| (iii) | their **arbitration finding keys match under one of the three key rules below** — shared id (primary), sectionless file, or equal `(file, section)` |

**Key rule 1 — shared id (primary).** Two findings citing the same `REQ-*` id or
the same deviation-entry id cluster, whatever their files and sections: a shared
id is as strong a co-location claim as a shared heading, and in the spike's
replay it was the **only** key that formed a cluster at all. The spike rated that single cluster **marginal** — in its own words, "0 that an operator would confidently call one root cause, 1 marginal … a topical adjacency rather than a demonstrated common cause". That is precisely why the signal is **informational** and never pauses a gate: its primary key rests on one cluster the spike itself would not confidently call a convergence. Key rule 2's justification is the stronger of the two — the cluster it recovers (red and blue on the same malformed records in a sectionless file) is the one the spike did rate genuine. It is the primary
key of the shipped signal.

**Key rule 2 — structureless file.** The **file-level** key is itself a cluster
key when the file is genuinely **structureless**: it has no addressable
structure of any kind, so "the whole file" is the only key that exists for it.
Two findings from different layers naming such a file cluster on the file alone.
This rule is what recovers the one real convergence the spike found and that a
section-granular rule structurally cannot catch: red R1 and blue both hitting
the same 8 malformed records in `.sdd/telemetry.jsonl`, missed because a JSONL
file has no sections for a `(file, section)` key to be equal on.

**"Structureless" is not "not Markdown" (red R3).** A file qualifies when it is
a **record/data file** — `.jsonl`, `.ndjson`, `.csv`, `.tsv`, `.log`, `.txt` —
or a Markdown file in which the key parser finds no heading. A **source** file
does **not** qualify, however few `#`-headings a Markdown parser finds in it: a
`.py` module has functions and classes, so the parser finding no section there
is a limitation of the parser, not a property of the file. Keying on the file
alone would make two unrelated findings anywhere in a 1000-line module read as
one root cause — the very noise the false-positive control below exists to
suppress, and it would be suppressed correctly in a sectioned spec and
incorrectly here. The rule is narrowed, not deleted: the `.jsonl` case it was
introduced for is preserved and is asserted alongside the source-file case in
the same scenario.

**[Stated limitation, 2026-09-20 — verify-stage review M4. Key rule 2's
motivating case is not reachable in the default configuration.** The case named
above and in REQ-HARN-HARNESSP6-002 is red and blue both hitting
`.sdd/telemetry.jsonl`. That path is **gitignored**, and telemetry is an
operator opt-out at KICKOFF, so in a cycle with telemetry off — and in any
cycle before its first append — the file does not exist. Combined with the
absent-path rule below, a finding naming it then yields **no key**, and the
origin case key rule 2 exists for renders nothing. The scenario that asserts
rule 2 uses a fixture-created data file, so what is demonstrated is the rule's
behaviour on a structureless path that exists, not the real `.jsonl` case; no
claim is made that the motivating case has been exercised end to end.
**The suffix discriminator's edges are arbitrary and are disclosed as such:**
`DATA_SUFFIXES` admits `.jsonl`, `.ndjson`, `.csv`, `.tsv`, `.log` and `.txt`,
while `.json`, `.yaml` and `.toml` read as STRUCTURED even though a heading
parser finds no section in them either — a defensible line drawn at
record-per-line files, not a derived one. No code change follows from this
note; it is a disclosure, not a redesign.**]

**A path absent from the checkout yields no key at all (red R4).** A finding may
name a typo, a renamed path, or a file that exists only in a fan-out worktree.
Absence is **not** evidence of structurelessness, so it must not collapse to the
file-level key: two findings naming *different sections* of a path the
orchestrator cannot see would then cluster, which is exactly the case the
false-positive control forbids. Such a finding contributes nothing to the
ledger's clustering and is silently dropped from convergence — the signal is
informational, so dropping it costs a line, never a decision.

**Section parsing is fence-aware (red R5).** A `#` inside a fenced code block is
a shell comment or a Markdown example, never a heading. Counting it made a
genuinely structureless Markdown file read as sectioned and silently dropped a
convergence key rule 2 would have rendered. This is the same fence-blindness
class REQ-GC-HARNESSP6-004 closed in `tools/sdd-gc.py`; it is now closed in the
sibling parser key rule 2 depends on. _(Added 2026-09-20, red round.)_

**Key rule 3 — equal `(file, section)` (retained, not relied on).** Two findings
whose arbitration finding keys are equal at section granularity — same `file`
**and** same `section`, reusing the existing `(file, section)` key of
`arbitrated-handoff.md` with its ratified leading-ordinal strip
(REQ-ARB-HARNESSP5-003) and its existing parser — still cluster when they occur.
The rule is kept because its precision is not in question; what the spike
refuted is its **recall**, so no recall claim rests on it.

**A file-level-only match in a file that has sections renders nothing.** Two
findings in two different sections of one large prose file are not one root
cause, and a rule that says they are makes the signal noise. This is the
decisive false-positive control and it is **retained unchanged** for sectioned
files: key rule 2 opens file-level matching only where there is no section to
match on, which is exactly the case the guard was never protecting against. In
the spike's replay the suppressed file-level matches scored 1-1 — one genuine
convergence missed (the sectionless `.sdd/telemetry.jsonl` case, now caught by
key rule 2) and one unrelated pair correctly suppressed (`tools/sdd-telemetry.py`,
a sectioned Python file — key rule 2 does not apply where the parser does find
sections).

**The ledger.** Convergence is computed over a **session-scoped, in-memory
finding ledger** of the same class as the loop counters (§State Placement). Per
finding it holds exactly three fields:

```
ledger entry = { key: id | (file,) [sectionless file] | (file, section), layer: blue|chunk-verifier|review|red, gate: <gate label> }
```

No finding text, nothing on disk, no durable artifact. It is never read by any
skill's phase detection and is discarded when the session ends. Losing it on a
session boundary is acceptable: L2 is informational, so a missed cluster costs a
line, not a decision.

**The window.** The signal is evaluated at **every** gate, over everything
recorded so far — not only at DONE. Each cluster renders **once**, at the gate
where its **second member** arrives, so it can and usually will fire mid-cycle,
while there is still a cheap opportunity to act on it. A cluster that completes
only at DONE routes into `verification.md` §Issues Found, to be fixed or
explicitly closed **in this cycle**, and **never** into §Next Steps — which
REQ-REQ-HARNESSP6-001 forbids from holding a carried item.

**Rendering and position (REQ-ORCH-HARNESSP6-001, Q-REQ-P6-B).** The line is the
own-line token `CONVERGENCE:` at position **6c** of the gate signal order
(§Gate Signal Order) — after 6b (`PLAN:`) and immediately before 7
(`TELEMETRY:`):

```
CONVERGENCE: docs/spec/telemetry.md §Writer rule (review, red) — 2 layers
```

It names the cluster's key — the shared id, or the file alone for a sectionless
file, or file and section — the contributing layers, and the layer count. It is
**informational**: no option set, it never pauses the gate, and it
never withholds `proceed`. That is the decisive choice. With no root-cause field
the cluster is a **heuristic** of Medium confidence and unmeasured firing rate; a
pausing heuristic converts every false positive into an operator interruption,
while an informational line costs one line when it is wrong and delivers its
whole value when it is right — because the value is the operator noticing.
Informational is also the reversible direction: promoting the signal later is a
one-line change, demoting it after operators have learned to trust a pause is
not.

**Three invariants (REQ-ORCH-HARNESSP6-002).**

1. **No durable artifact.** The ledger is session-scoped and in memory; the
   output is ephemeral gate text. No file under `docs/` is created by L2 and no
   new artifact class appears in the drift sweep.
2. **No influence on phase detection.** No `sdd-*` skill's entry check reads
   `CONVERGENCE:`, and it is never written to any file a detector reads.
3. **The four-layer verification table stays byte-unchanged**, in `CLAUDE.md`
   and in every spec that restates it, because L2 is a gate signal, not a layer.

No telemetry record key is added for it (REQ-TELEM-HARNESSP2-002 — a
`convergence_n` field is a settled exclusion).

**Uncertainty, spike and fallback — stated plainly.** This section is marked
`[high-uncertainty]`, which under SDD makes it a **spike task inside this
cycle**, not a deferral.

- **Unverified assumption**: that `(file, section)` equality at section
  granularity clusters real convergences at a useful rate without clustering
  unrelated findings. The key parser is exercised (REQ-ARB-HARNESSP5-003), but
  the cluster rule has never been replayed against a real finding set and its
  firing rate is unmeasured (RS-HARNESSP6-001 Q4, Confidence **Medium**).
- **Resolving spike**: replay the rule over the recorded findings of the
  harness-p3, -p4 and -p5 cycles and count clusters, splitting them into ones an
  operator would call the same root cause and ones they would not.
- **Fallback if the assumption is wrong**: a **replan inside this cycle** that
  descopes L2 to its honest floor — the secondary-id key alone (highest
  precision, lowest recall), or the co-located key evaluated only at DONE — with
  the descope recorded as a settled exclusion with its reasoning.

**Spike result and resolution (recorded 2026-09-20).** The resolving spike ran
and the assumption did **not** hold: over the recorded findings of the
harness-p3, -p4 and -p5 cycles the `(file, section)` key formed zero clusters in
each cycle and zero in total, and it clusters none of the three layers of the
harness-p3 §L2 origin case. The rule is not noisy — it is silent, and its
precision was never the problem. The fallback below was therefore taken as a
replan **inside this cycle**: the shipped floor is the shared-id key as primary
plus the sectionless-file rule stated above, and the co-located
`(file, section)` key as the *primary* cluster key is recorded as a settled
exclusion with its measured evidence in `docs/requirements/index.md`
§Out of Scope. The full replay, its input set and the caveats on that input set
are in `docs/ws/harness-p6/plan.md` §Chunk 8 → Spike Findings.

**[Resolved 2026-09-20 — this trigger FIRED and is no longer armed.** The
paragraph below is retained as written before the spike, because it records what
the cycle committed to do in advance of the measurement; read it in the past
tense. The spike measured zero clusters, the replan ran **inside this cycle**,
and L2 shipped at the floor described above — the **shared id** key primary (the
term "secondary-id key" below is the pre-replan name for it), the sectionless-
file rule, and `(file, section)` retained but demoted. The descope is recorded
as a settled exclusion in `docs/requirements/index.md` §Out of Scope, and the
replan is archived at `docs/ws/harness-p6/plan-history/2026-09-20-replan-l2-descope.md`.
Nothing was carried to a successor workstream.**]

It is this cycle's credible replan trigger. If it proves harder than the spike
predicts, the handling is a **replan inside this cycle** that descopes L2 to its
honest floor — the secondary-id key alone, or the co-located key evaluated only
at DONE — with the descope recorded as a settled exclusion. It is **not** carried
to a successor workstream; this cycle is terminal.

### Gate Signal Order (REQ-ORCH-034 counterpart)

[Added 2026-09-18, harness-p4 — REQ-HARN-HARNESSP4-001, REQ-HARN-HARNESSP4-003;
canonical spec-side statement, counterpart of `references/loop-control.md` §5]

Signals surface in the order they are produced; everything is ephemeral
(REQ-ORCH-013). **This section is the one spec-side statement of the full
order.** `orchestration.md` §v5 Harness Hardening, `adversarial-verify.md`
§Verify-Stage Gate, `harness-chunk-verifier.md`, `harness-commit-fidelity.md`
and `telemetry.md` point here and state only their own signal's position; none
restates the list in a form that can diverge from it. The skill side mirrors it
in `references/loop-control.md` §5 — the two must agree item for item.

| # | Signal | Renders at | Owner spec |
|---|---|---|---|
| 1 | `RETURN.status` and `budget_consumed` against the dispatched `Budget:` | per-chunk gate / per-leaf gate / stage gate | `harness-return-contract.md`, this spec §Budget Exhaustion |
| 2 | write-scope block ending in the own-line `SCOPE: CLEAN \| VIOLATION (N paths)` | same | `harness-write-scope.md` |
| 2b | **fan-out per-leaf gate only**: `COMMIT: COMPLETE \| INCOMPLETE` computed pre-decision from the leaf's observed writes vs its committed delta | per-leaf gate, after `SCOPE:`, before `CHUNK_VERDICT:` | `harness-commit-fidelity.md` |
| 3 | implement stage, per chunk: `CHUNK_VERDICT: PASS \| FAIL` with `Redo: N of REDO_MAX` — signals 1–3 (and 2b) render at the **per-chunk / per-leaf gate** | per-chunk gate | `harness-chunk-verifier.md` |
| 3b | verify stage, red opted in: `RED_VERDICT: BROKEN \| HELD`, red's `Rn` lines, then on round N >= 2 the derived `RED: Rn new-ground \| regression` lines | stage gate, after `SCOPE:`, before `VERDICT:` | `adversarial-verify.md` |
| 4 | the parsed review `VERDICT:` | stage gate | `harness-return-contract.md` |
| 5 | loop counters — `iteration N of MAX`, derived replan re-entry count against `REPLAN_MAX` | stage gate | this spec |
| 6 | `REVIEW: CONTRADICTION (round N vs round N+1, class b\|c[, file-level])` pause block | stage gate, after the counters | `arbitrated-handoff.md` |
| 6b | **implement stage gate only**: the completion parse of `docs/ws/<id>/plan.md` — when any numbered chunk task is unticked, the own-line `PLAN: INCOMPLETE (N of M ticked)` pause offering `replan │ stop` **only** (`proceed` withheld, so verify is never dispatched while the plan reads `implementing`); when every task is `[x]` no line renders. **Supersedes signal 6's option set when both fire** — 6's block still renders, its options are suppressed, and the gate offers `replan \| stop` only | implement stage gate, after signal 6, before `TELEMETRY:` | this spec §Plan Completion Ownership |
| 6c | the own-line `CONVERGENCE:` token — one line per cluster whose second member arrived at this gate, naming the cluster's key (shared id, sectionless file, or file and section), the contributing layers and the layer count. **Informational**: no option set, never pauses, never withholds `proceed` | every gate, after 6b, before `TELEMETRY:` | this spec §Convergence Signal |
| 6d | **stage gate, review round N ≥ 2 only**: the own-line informational `GROWTH: <deliverable> +A/−D lines (N₁ → N₂) since round N−1` — the deliverable's size delta since the previous round. **Informational**: no option set, never pauses, never withholds `proceed` (added 2026-09-22, REQ-HARN-PIPELINEOBSERVABILITY-002) | stage gate, after 6c, before `TELEMETRY:` | this spec §Gate Signal Order, the `GROWTH:` paragraph below |
| 7 | the `TELEMETRY:` line — `rec <n> │ WRITE FAILED │ OFF │ .gitignore updated`, at most once each, immediately after the last counter-bearing line and **before the options** | every gate | `telemetry.md` |
| — | the options (`proceed │ fix │ stop` per chunk; `proceed │ loop-back-to-fix │ stop` per stage; pause-family options where a pause fired) | every gate | `orchestration.md` §Gate Protocol |
| 8 | **post-decision**: `COMMIT: COMPLETE \| INCOMPLETE` — rendered immediately after the orchestrator's own commit (sequential per-chunk and stage gates) or after the merge (fan-out merge step), as the **closing line of the same gate**, before the next dispatch; on `INCOMPLETE` it pauses with `amend \| accept (note) \| stop` and no next dispatch — including the implement-stage review after the last chunk — is issued until resolved | closing line of the gate that decided `proceed` | `harness-commit-fidelity.md` |
| 8b | **implement stage gate `proceed` only, after item 8**: the orchestrator flips `docs/ws/<id>/plan.md` `status:` to `complete` in its **own bookkeeping commit** — the same post-gate slot as aggregate regeneration and the `pending-red → pass` flip; outside the `COMMIT:` range because `HEAD_landed` is captured before any bookkeeping commit, so it never renders `landed, not observed` | after the `COMMIT:` closing line, before the verify dispatch | this spec §Plan Completion Ownership |

Two rules follow from "produced order": a signal whose data exists before the
decision renders before the options (items 1–7, 2b, 6b, 6c and 6d — the plan's tick
state exists on the leaf's return, and the convergence ledger holds every
finding this gate surfaced); a signal that is the
*consequence* of the decision renders after them (items 8 and 8b) and is **not**
deferred to the next gate — `TELEMETRY: rec <n>` is the one deferred signal,
and it may be because telemetry is never load-bearing (`telemetry.md` §Writer).
`COMMIT:` is load-bearing and therefore closes the gate it belongs to. No
`TELEMETRY:` line and no `CONVERGENCE:` line ever pauses the gate or changes an
option: 6c renders **after** every finding-bearing signal and after both derived
pauses (6, 6b) because it is derived from them, and the "renders last before the
options" clause that governs item 7 covers 6c in the same enumeration.

**`GROWTH:` — the size delta is visible at the gate where it acts** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-HARN-PIPELINEOBSERVABILITY-002; the record of why is §Pipeline-Observability Amendment).

On a review round N ≥ 2 the stage gate renders one informational own-line

```
GROWTH: <deliverable> +A/−D lines (N₁ → N₂) since round N−1
```

at position **6d** of §Gate Signal Order — after `CONVERGENCE:` (6c), before
`TELEMETRY:` (7). `A`/`D` are the deliverable's visible-line additions and
deletions since the previous round's sha (`git diff --numstat` over the
deliverable path, fenced lines included — the count is a size, not a
comparand), `N₁ → N₂` its line count then and now. Like 6c it carries no option
set, never pauses and never withholds `proceed`. It landed with the routing
above; its comparand is the `REQUIRED` row `GROWTH: ` on
`skills/orchestrate/references/loop-control.md` (item 6d). Under the routing above a round N ≥ 2
arises only after a `REJECT` or an operator opt-in, so a correct cycle may
render it never — which is why the line is informational and why its
verification is conditional (below).

## Verification

### Automated
- `tools/sdd-skill-lint.py` `REQUIRED` rows: fix-loop cap phrase and replan
  re-entry cap phrase in `sdd-orchestrate/SKILL.md`; `Budget:` in both template
  files; `-replan-` in `sdd-replan/SKILL.md`; `oscillation` in
  `sdd-implement/SKILL.md`; checkpoint format marker in `sdd-implement` and
  `sdd-replan` (`skill-lint-v5.md`).
- Grep: no `-replan-` in `skills/sdd-plan/SKILL.md` archive names.
- Fixture: a `plan-history/` directory with `2026-09-01-replan-a.md`,
  `2026-09-18-replan-b.md`, `2026-09-19-m1-replan-c.md`, `2026-09-19-rewrite.md`,
  `2026-09-20-m1-complete.md` and kickoff `date: 2026-09-17` derives count = 2.
- Fixture: a kickoff without `date:` whose `research_id: RS-008` line was last
  changed by a commit dated 2026-09-17 (an earlier commit created the file with
  `research_id: RS-007`) derives the same count = 2; a kickoff with neither
  yields `treated as reached`.
- Fixture: the ledger above is classified stuck by rule (a); a ledger with two
  identical `change` lines is classified stuck by rule (b).
- Fixture: a checkpoint composed from the RS-008 Schema 1 example is ≤ 15 lines
  and contains no line matching `^\s+File ".*", line \d+` or `Traceback`.
- Convergence key-parser scenario group (REQ-HARN-HARNESSP6-002),
  `tools/sdd-scope-check-selftest.py` scenarios **L1-L5**, five cases:
  two findings from **different** layers citing the same `REQ-*` id with
  different sections **cluster** (key rule 1, the primary key); two from
  different layers naming the same file in which the key parser finds **no
  section** (e.g. a `.jsonl` or `.py` path) **cluster** on the file alone (key
  rule 2); two from different layers in the **same sectioned file** with
  **different** sections do **not** (the retained noise guard); two from the
  **same** layer do **not**; two from different layers with equal
  `(file, section)` **cluster** (key rule 3, retained).
- Fixture (**L6**): two findings from different layers stamped with **different**
  `research_id` values do not cluster (condition (ii)).
- Gate rendering fixture (**L7**): a gate with one complete cluster shows the
  `CONVERGENCE:` line between the `PLAN:` position (6b) and the `TELEMETRY:`
  line (7), and shows `proceed` available while it is displayed
  (REQ-ORCH-HARNESSP6-001).
- Fixture (**L8**), demonstrated rather than asserted: `git ls-files docs/` is
  captured before and after a run of the ledger/gate-render fixture **in which a
  cluster actually fires**, and the two listings are identical. The fixture run
  is the comparand because nothing inside this cycle makes a real cluster fire
  during a real orchestrated cycle; the grep that no `sdd-*` skill's
  phase-detection branch reads the convergence ledger is the second half of the
  same invariant (REQ-ORCH-HARNESSP6-002).
- Fixture (**L9**, Q-IMPL-HARNESSP6-001): a **third** layer joining an
  already-rendered cluster does **not** re-render it — the ledger keeps all
  three entries and emits no second line (REQ-HARN-HARNESSP6-002).

### Manual
- Run one orchestrated stage to three `REJECT`s: a fourth gate shows the
  compiled log and no fourth dispatch; each fix prompt contained
  `iteration N of 3`; `git ls-files docs/` shows no counter file.
- Dispatch an implement chunk with `Budget: ≤ 5 tool calls`: the return is
  `status: BUDGET_EXHAUSTED` with `budget_consumed` in tool calls, and a
  checkpoint appears under the task.

### Acceptance Criteria
- [ ] Fix re-dispatches are capped per stage at a default of 3, each prompt states `iteration N of MAX`, exhaustion exits to the gate with a compiled findings log and no automatic dispatch; the counter is session-only (REQ-HARN-001)
- [ ] Replan re-entries are capped per cycle at a default of 3, derived from `-replan-` archives dated ≥ kickoff `date:` (mandatory on orchestrate-written kickoffs; legacy fallback = the last commit that changed the kickoff's `research_id:` line; undeterminable → cap treated as reached and surfaced), per workstream under marker `4` (REQ-HARN-002)
- [ ] `sdd-replan` states the `-replan-` filename contract; no other skill uses the segment; lint enforces it (REQ-HARN-003)
- [ ] Every dispatch template carries a `Budget:` slot in observable units, including review (REQ-HARN-004)
- [ ] Budget exhaustion returns `status: BUDGET_EXHAUSTED` + `budget_consumed` in the dispatched units, with a checkpoint when mid-task; missing `budget_consumed` is malformed (REQ-HARN-005)
- [ ] `sdd-implement` Step 3 defines the four ledger fields and `verified_do_not_touch`; no ledger text in specs or kickoff (REQ-HARN-006)
- [ ] Stuck detection lists both oscillation conditions under the word "oscillation" (REQ-HARN-007)
- [ ] Checkpoint format and RETURN-field mapping are stated in `sdd-implement` and `sdd-replan`; `sdd-replan` Step 1 reads the checkpoint; fixture ≤ 15 lines, traceback-free (REQ-HARN-008)
- [ ] After a full orchestrated cycle `git ls-files docs/` shows no new file type beyond `plan-history/` archives (REQ-HARN-027)
- [ ] §Gate Signal Order is the only spec-side statement of the full order, lists item 8 "post-decision: `COMMIT:`" and position 2b, and agrees item for item with `references/loop-control.md` §5; `orchestration.md` §v5 points here rather than restating the list (REQ-ORCH-034; placement per REQ-HARN-HARNESSP4-001/-003, owned by `harness-commit-fidelity.md`)
- [ ] `grep -n 'status: complete' skills/sdd-orchestrate/SKILL.md skills/sdd-orchestrate/references/loop-control.md skills/sdd-orchestrate/references/write-scope.md skills/sdd-implement/SKILL.md` shows the flip in §The gate, §1 and the §7 table, and the direct-session / orchestrated split in `sdd-implement` Step 6; the per-chunk PIPELINE template carries "tick tasks, never `status:`"; §Gate Signal Order lists 6b (`PLAN: INCOMPLETE (N of M ticked)`, `replan │ stop` only) and 8b (the flip after `COMMIT:`) and `references/loop-control.md` §5 agrees item for item (REQ-HARN-HARNESSP5-001)
- [ ] `skills/sdd-orchestrate/references/loop-control.md` §6 lists `PLAN: INCOMPLETE (N of M ticked)` as the **fifth** pause-family member with `replan │ stop` as its whole option set; a walkthrough of an implement stage gate where a contradiction pause and an unticked task fire together renders signal 6's block and signal 6b's line but offers `replan │ stop` only — no `accept round N (proceed, note)` (REQ-HARN-HARNESSP5-001)
- [ ] A walkthrough of an implement stage gate `proceed` shows the flip in a commit separate from the leaf's and `COMMIT: COMPLETE`; a second walkthrough with one unticked task shows the `PLAN: INCOMPLETE` pause, no flip and no verify dispatch; the `research_id:` line is byte-identical before and after the flip; `python3 tools/sdd-skill-lint.py` exits 0 (a `REQUIRED` row for the flip sentence is optional) (REQ-HARN-HARNESSP5-001)
- [ ] §Convergence Signal states the three cluster conditions, the three key rules (shared id primary, sectionless file, retained `(file, section)`), the file-level-only non-render for files that have sections, and the ledger's three fields; the ledger is session-scoped and in memory (REQ-HARN-HARNESSP6-002)
- [ ] The signal is evaluated at every gate over everything recorded so far, each cluster renders once at the gate where its second member arrives, and a cluster completing only at DONE routes into `verification.md` §Issues Found and never §Next Steps (REQ-HARN-HARNESSP6-002)
- [ ] The key-parser scenario group passes: different layers + same `REQ-*` id cluster (primary key); different layers naming the same sectionless file (no section found by the parser) cluster; different layers + same sectioned file + different sections do **not**; same layer does not; different layers + equal `(file, section)` cluster (retained key) (REQ-HARN-HARNESSP6-002)
- [ ] §Gate Signal Order carries 6c between 6b and 7; the "renders last before the options" clause names 6c; `skills/sdd-orchestrate/references/loop-control.md` §5 agrees item for item and `SKILL.md` §The gate names the token in its non-divergent summary (REQ-ORCH-HARNESSP6-001)
- [ ] `CONVERGENCE:` is informational — no option set, never pauses, never withholds `proceed`; a gate rendering fixture shows `proceed` available while the line is displayed (REQ-ORCH-HARNESSP6-001)
- [ ] §Convergence Signal states the shipped scope explicitly — shared id primary, sectionless file, retained `(file, section)` — and states the origin-case recall as the Chunk 8 replay measured it, with no recall figure that the replay does not reproduce; re-running that replay over the same recorded finding sets reproduces the stated result (REQ-ORCH-HARNESSP6-002)
- [ ] The three invariants hold: no file under `docs/` is created by L2; no phase-detection rule in any `sdd-*` skill references the signal; the four-layer verification table is byte-unchanged in `CLAUDE.md` and in every spec that restates it; no telemetry record key is added (REQ-ORCH-HARNESSP6-002)
- [ ] No leaf `RETURN:` shape in `harness-return-contract.md` or any dispatch template gains a field for L2 (REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-002)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed

**Pipeline-observability (2026-09-22, loop control)**

- [ ] `python3 plugins/sdd/tools/skill-lint.py` exits 0 on the branch with
  the two landed pins present — the `REQUIRED` row on
  `skills/orchestrate/SKILL.md` for `proceeds **without re-review**` and the
  `FORBIDDEN` phrase `then re-run the review for this stage` — and `python3
  plugins/sdd/tools/skill-lint.py --self-test` exits 0 with its pinned
  `REQUIRED` and `FORBIDDEN` totals including them; in a temp copy, deleting
  the `without re-review` sentence from §The gate makes the linter exit
  non-zero with the `REQUIRED` finding, and restoring the unconditional phrase
  makes it exit non-zero with the `FORBIDDEN` finding
  (REQ-HARN-PIPELINEOBSERVABILITY-001).
- [ ] `skills/orchestrate/references/return-contract.md` §6's `APPROVE_WITH_FIXES` row and
  `harness-return-contract.md` §VERDICT Token's branching table read
  fix-then-proceed with re-review on opt-in only; `skills/orchestrate/references/loop-control.md`
  §5a's default is proceed and §2a states that an `APPROVE_WITH_FIXES` at or
  after the cap is not an exhaustion —
  `grep -c 'without re-review' plugins/sdd/skills/orchestrate/references/return-contract.md`
  ≥ 1, `grep -c 'without re-review' docs/spec/harness-return-contract.md` ≥ 1,
  `grep -Ec 'default[^.]*proceed' plugins/sdd/skills/orchestrate/references/loop-control.md`
  ≥ 1 and `grep -c 'not an exhaustion' plugins/sdd/skills/orchestrate/references/loop-control.md`
  ≥ 1; this cycle's `verification.md` names the gates that ran under this rule
  (REQ-HARN-PIPELINEOBSERVABILITY-001).
- [ ] A gate-rendering walkthrough whose consumed verdicts on one stage run
  `APPROVE_WITH_FIXES, REJECT, REJECT, APPROVE_WITH_FIXES` never renders the
  exhausted gate, while `REJECT, REJECT, REJECT` does — its transcript
  recorded in this cycle's `docs/ws/pipeline-observability/verification.md`
  under `Gate-rendering walkthroughs` (Q-SPEC-PO-L,
  `pipeline-observability.md`); `skills/orchestrate/references/loop-control.md`
  §2 states the consecutive-`REJECT` rule, pinned by skill-lint `REQUIRED`
  row p4 on `consecutive consumed` in that file whose removal in a temp copy
  makes the linter exit non-zero (REQ-HARN-001 as amended).
- [ ] `python3 plugins/sdd/tools/skill-lint.py` exits 0 with the landed
  `REQUIRED` row on `skills/orchestrate/references/loop-control.md` for `GROWTH: `; in a temp copy
  with item 6d removed it exits non-zero; `skills/orchestrate/SKILL.md` §The
  gate's row for positions 6c, 6d, 7 names `GROWTH:` before `TELEMETRY:`;
  §Gate Signal Order of this spec carries row 6d between 6c and 7 and agrees
  item for item with `skills/orchestrate/references/loop-control.md` §5
  (REQ-HARN-PIPELINEOBSERVABILITY-002).
- [ ] **Conditional**: at every stage of this cycle that ran a review round
  N ≥ 2 — if any — this cycle's `verification.md` quotes the rendered
  `GROWTH:` line from that gate; when no stage ran a round N ≥ 2,
  `verification.md` states so and the temp-copy and self-test checks alone
  decide the criterion (REQ-HARN-PIPELINEOBSERVABILITY-002).
- [ ] `skills/orchestrate/references/loop-control.md` §2b's `manual intervention` option names the
  `post-manual` review and states that `proceed` is withheld until its record
  exists, pinned by a skill-lint `REQUIRED` row on `post-manual` whose removal
  in a temp copy makes the linter exit non-zero; this cycle's `verification.md`
  lists every manual intervention with the review round that followed it, and
  none without (REQ-HARN-PIPELINEOBSERVABILITY-003).
- [ ] The `post-manual` footprint: `grep -c 'POST_MANUAL' plugins/sdd/tools/telemetry.py`
  reads ≥ 1 (0 before this delta) and `schema_diff` reports no divergence with the
  member added; `--lint` over a two-record fixture — a `reason: REVIEW` record at
  `iteration: 1` with no loop-back followed by a `reason: POST_MANUAL` record —
  emits one `[reason-review]` warning, for the first record only; a gate-rendering
  walkthrough of a per-chunk manual intervention shows `dispatch.chunk = N`, the
  chunk's `Redo: N of REDO_MAX` unchanged and no verifier re-dispatch, recorded
  in this cycle's `docs/ws/pipeline-observability/verification.md` under
  `Gate-rendering walkthroughs` (Q-SPEC-PO-L) (REQ-HARN-PIPELINEOBSERVABILITY-003).
- [ ] `grep -c mutations plugins/sdd/skills/orchestrate/references/dispatch-templates.md`
  reads ≥ 1 (0 before this delta), pinned by skill-lint `REQUIRED` row p10
  (pattern `mutations \+ gates`) on the formula sentence whose removal in a
  temp copy makes the linter exit non-zero;
  the template's worked example dispatches a chunk naming 2 mutations and 2
  gates with `≤ 6 test runs`; `skills/orchestrate/SKILL.md`'s implement
  dispatch step cites the derivation (REQ-HARN-PIPELINEOBSERVABILITY-006).
- [ ] The telemetry witnesses hold: cross-field assertions (b) and (c) of
  `telemetry-reader.md` §Schema Lint fail on their
  recorded shapes and pass on their controls (REQ-HARN-001 as amended,
  REQ-HARN-PIPELINEOBSERVABILITY-003).

## Edge Cases

- **Kickoff without `date:` and never committed** (or committed but its
  `research_id:` line matches no commit): no date is determinable → the cap is
  treated as reached and surfaced at the gate with every `-replan-` archive
  listed (§Replan Re-entry Cap); the operator authorizes the replan explicitly.
  Never silently treat the cap as unreachable.
- **Operator raises the fix cap twice**: each authorization adds one; the gate
  shows `iteration 5 of 5 (cap raised ×2)` so the history is visible without
  persisting it.
- **Replan that is reclassified as minor mid-run**: no archive → not counted;
  this is by design (REQ-HARN-002).
- **Budget stated in a unit the leaf cannot count** (e.g. `≤ 10 minutes`): the
  lint forbids wall-clock terms; if one slips through, the leaf reports
  `budget_consumed` in the units it *can* count and notes the mismatch in
  `open_questions`.
- **Checkpoint for a task the plan does not list** (leaf drifted): the
  orchestrator applies the note under the nearest chunk header with a
  `task not found in plan` prefix and raises it at the gate — it never invents
  a task.
- **Two stuck tasks in one chunk**: one checkpoint per task; the ≤ 15-line
  bound is per checkpoint.

## Cross-Spec Consistency (XSPEC)

- [Added 2026-09-19, harness-p5] §Plan Completion Ownership: `cycle-identity.md`'s
  `research_id:` stamp is untouched by the flip; `harness-commit-fidelity.md`
  §Placement captures `HEAD_landed` before bookkeeping, which is what keeps 8b
  outside the `COMMIT:` range; `ws-traceability.md` §Aggregate Regeneration
  Ownership names the same post-gate bookkeeping slot; `orchestration.md`
  §Resume and Phase Detection reads `status:` as before — the `PLAN:` pause
  changes when the flip happens, not what phase detection reads.

Run per `sdd-specs` Step 4b against `orchestration.md`, `review.md`,
`chunk-close-review.md`, `deviation-protocol.md`, `plan-management.md`,
`ws-*.md` and the sibling harness specs.

- No extractable Python/TS/Rust/Move type definitions in this spec — schemas are
  YAML/Markdown fixtures. XSPEC therefore operates on named fields.
- `ledger[]`, `failures[]`, `open_questions[]`, `budget_consumed`, `status`
  referenced here are defined in `harness-return-contract.md` §RETURN Block with
  the same names and field sets (`attempt/hypothesis/change/result`;
  `test/kind/message/location`) — consistent.
- `plan-management.md` §Plan History names `{date}-replan-{reason}.md` and
  `{date}-m{N}-complete.md`; this spec's regex accepts exactly those shapes and
  the `m{N}-replan` variant from `skill-updates.md` §replan — consistent.
- `orchestration.md` §Gate Protocol vocabulary `proceed │ loop-back-to-fix │
  stop` is preserved; the exhaustion options are additive and appear only at a
  cap event — no contradiction (REQ-ORCH-034 amends orchestration.md).
- `deviation-protocol.md` Q-IMPL entry format is untouched; the ledger cites
  Q-IMPL ids and never restates them — consistent.
- `ws-integration.md` merge target = workstream branch under marker `4` —
  restated here identically.
- §Gate Signal Order names each signal's owner spec; every token it lists
  (`SCOPE:`, `CHUNK_VERDICT:`, `RED_VERDICT:`, `VERDICT:`, `REVIEW:
  CONTRADICTION`, `TELEMETRY:`, `COMMIT:`) is defined with the same members in
  that owner — consistent [Added 2026-09-18, harness-p4].
- **No unresolved contradictions.**

## Open Questions

1. **Redo counter granularity.** REQ-HARN-001 keys the fix count "per stage";
   verifier-FAIL redos are per chunk and are not review-driven. **Default
   adopted**: a separate per-chunk redo counter with the same `MAX = 3` and the
   same exhaustion behavior (§Redo Cap per Chunk). If the operator prefers one
   shared counter per stage, the redo counter collapses into it with no other
   change.
2. **Per-stage cap override persistence.** A cap raised at the gate is
   session-only (consistent with REQ-HARN-001). Default: no persistence.

## Implementation Questions


### Q-IMPL-042: default-budget table rows beyond the spec's four examples
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Budget Slot
**Decision**: the default table in `references/return-contract.md` has one row per dispatch type; two rows generalize spec prose: "pipeline stage (non-implement) = ~70 tool calls, no prototypes" (from the specs-stage example) and "fix re-dispatch = remaining or fresh per-chunk allowance sized from previous `budget_consumed`" (from §Budget Exhaustion).
**Rationale**: the orchestrator needs a default for every dispatch type it issues; the spec gives examples, not a complete table.
**Date**: 2026-09-17 (Chunk 2)

### Q-IMPL-083: implement/SKILL.md size warning accepted for v5
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Circuit-Break Checkpoint, §Budget Slot; `skill-lint-v5.md` size warn tier
**Decision**: the 525-line `sdd-implement/SKILL.md` (attempt ledger, checkpoint and budget detail plus the leaf return contract) trips the new 400-line warn; the warning is accepted **permanently**, and the `references/` split is **declined** rather than queued. **[Updated: 2026-09-20 — harness-p6 is the terminal cycle of the series (kickoff §Decided at DISCUSS), so an action queued to a successor cycle cannot stand. The earlier operator decision to defer the split is superseded by an operator decision at the harness-p6 specs gate to retire it as a settled exclusion: the 525-line `sdd-implement/SKILL.md` warn is accepted, its detail (attempt ledger, checkpoint, budget, leaf return contract) is cohesive with the skill it governs, and splitting it to satisfy a line-count proxy would divide a contract. Re-open only if the file grows past the point where the contract itself stops being readable.]**
**Rationale**: the warn tier is advisory by design (REQ-LINT-002); the ledger/checkpoint/budget prose is what the harness-hardening cycle added and splitting it mid-cycle would move text the implement-stage review has just approved.
**Date**: 2026-09-17 (Chunk 6, implement-stage review fix loop)

**Status**: `[resolved by REQ-SKILL-HARNESSP2-007]` — `skills/sdd-implement/SKILL.md` split into `references/stuck-detection.md` and `references/leaf-return.md` (harness-p2 Chunk 1).

### Q-IMPL-HARNESSP2-001: `.sdd/` prohibition sentence superseded by telemetry.md
**Tier**: 2 (spec ambiguity)
**Spec reference**: §No-New-Artifact Invariant (REQ-HARN-027)
**Decision**: The sentence "no `docs/reviews/`, `.sdd/` or telemetry file is created" is superseded by `telemetry.md` §Placement (REQ-HARN-027 amendment 2026-09-17): a gitignored, root-level `.sdd/telemetry.jsonl` written only by the orchestrator after each gate, never a phase-detection input, is permitted. The `docs/` invariant, the `docs/reviews/` prohibition and the mechanism table are unchanged; `telemetry.md` §Non-Interference Proof is the contract.
**Rationale**: Marker-4 shared specs are extended by new files, never edited in place (`ws-ids.md`); the requirement text carries the same `[Updated 2026-09-17]` clause.
**Date**: 2026-09-17 (harness-p2 specs stage)

### Q-IMPL-HARNESSP6-001: a third layer joining an already-rendered cluster does not re-render it
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Convergence Signal — L2 (REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-001, REQ-ORCH-HARNESSP6-002) [high-uncertainty]
**Decision**: "each cluster renders once, at the gate where its second member arrives" is read literally. A third (or later) finding joining a cluster whose line has already rendered adds a ledger entry but emits **no** further `CONVERGENCE:` line, so the layer count a cluster ever displays is the count at its second member — normally `2`.
**Rationale**: the requirement's wording is "renders once" and its worked example shows `— 2 layers`; re-rendering on each new member would make a Medium-confidence heuristic repeat itself at successive gates, which is precisely the noise the informational-and-quiet choice was made to avoid. The alternative (re-render with a higher count) is a one-line change if operators later report that the higher count would have been worth seeing. Resolved by choice during a non-interactive specs stage; no operator was available to ask.
**Date**: 2026-09-20 (harness-p6 specs stage)


## Pipeline-Observability Amendment (2026-09-22, REQ-HARN-PIPELINEOBSERVABILITY-001, -002, -003, -006; REQ-HARN-001 amended)

[Added 2026-09-22, workstream `pipeline-observability` —
RS-PIPELINEOBSERVABILITY-001 §Q3, §Q4, §Gate observation 2026-09-22, R6, R8,
R12; Q-REQ-PO-A, -C. Observed defect: `FIX_LOOP_MAX` fired at all four
consumer-geometry document stages on an `APPROVE_WITH_FIXES` with zero blocking
findings, forcing four manual interventions, none of which was reviewed.]

**Where the contract lives** (REQ-REQ-PIPELINEOBSERVABILITY-001 (b), 2026-09-22): this section is the record of *why* and states no contract of its own; the contract is in the sections of record named here, each edited in place under a `[Updated: 2026-09-22]` marker, and its acceptance criteria sit in this spec's own Acceptance Criteria section under the same date. §Fix-Loop Cap carries the verdict routing recorded as in force (REQ-HARN-PIPELINEOBSERVABILITY-001), the counted quantity `reject_run` (REQ-HARN-001 as amended — its exhaustion parenthesis is superseded there) and the `post-manual` review with its footprint (REQ-HARN-PIPELINEOBSERVABILITY-003); §Gate Signal Order carries row 6d and the `GROWTH:` line (REQ-HARN-PIPELINEOBSERVABILITY-002); §Budget Slot carries the derived implement test-run budget (REQ-HARN-PIPELINEOBSERVABILITY-006). Left consistent and not reopened: §Redo Cap per Chunk (`REDO_MAX` keeps its meaning and is that section's constant — the voided-re-dispatch bound of `harness-write-scope.md` §Git-State Observation reuses its *value*, not its counter), §Replan Re-entry Cap, §Budget Exhaustion, §Attempt Ledger, §Circuit-Break Checkpoint, §No-New-Artifact Invariant (every counter is session state; the `GROWTH:` line is text), §Plan Completion Ownership, §Convergence Signal.

**Why the verdict is the routing**: a fresh reviewer over a growing artifact is a generator no cap converges — eight zero-blocking `APPROVE_WITH_FIXES` rounds were each fixed and re-reviewed, and every re-review raised new Material ground; under fix-then-proceed an `APPROVE_WITH_FIXES` ends the stage's review chain, so V2's `ROUND_MAX` and its two-consecutive-`APPROVE_WITH_FIXES` terminator have nothing to bound and are not adopted (Q-REQ-PO-A). The routing landed on the branch before the specs stage; its comparands are the skill-lint pins, never a commit. **Why `reject_run`**: the acceptance criterion of REQ-HARN-001 always read "reaches REJECT three times"; the body's "once per fix re-dispatch" was wider than its own test. **Why a `post-manual` review**: four interventions in the consumer-geometry cycle each went straight to the next stage's dispatch, and the three orchestrator errors attributable in telemetry were caught one stage and 3–4 rounds downstream. **Why the budget is derived**: the consumer-geometry chunks overran 8 against 6 and 18 against 12 under a fixed `≤ 3 test runs` example, so a budget overrun was the honest outcome of an honest chunk. **Miscitation corrected** (requirements closing review, round 8 M2): the earlier text of this amendment cited the circuit-break checkpoint requirement (REQ-HARN-008) as the redo cap's; `REDO_MAX` is established by no requirement and is defined only in §Redo Cap per Chunk, which the moved text now cites.
