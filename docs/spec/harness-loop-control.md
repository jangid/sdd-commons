---
status: Approved
last_updated: 2026-09-17
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
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed

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
  the `m{N}-replan` variant from `skill-updates.md` §sdd-replan — consistent.
- `orchestration.md` §Gate Protocol vocabulary `proceed │ loop-back-to-fix │
  stop` is preserved; the exhaustion options are additive and appear only at a
  cap event — no contradiction (REQ-ORCH-034 amends orchestration.md).
- `deviation-protocol.md` Q-IMPL entry format is untouched; the ledger cites
  Q-IMPL ids and never restates them — consistent.
- `ws-integration.md` merge target = workstream branch under marker `4` —
  restated here identically.
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
