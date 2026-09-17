# Loop Control — sdd-orchestrate reference

Loop-control **procedure** text moved out of `SKILL.md` (REQ-LINT-007 size
target; REQ-HARN-001, REQ-HARN-002 procedure placement). Each section below is
referenced from a stub in `SKILL.md` that keeps the contract line and the lint
marker literals (`fix-loop cap`, `iteration N of 3`, `replan re-entry cap`,
`CHUNK_VERDICT:`); the canonical per-chunk gate block itself stays in
`SKILL.md` §Per-chunk implement dispatch and per-chunk gate. Every counter here is orchestrator
session state (`docs/spec/harness-loop-control.md` §State Placement) — nothing
is persisted, and no template tells a subagent to count anything
(`SKILL.md` §Orchestrator-Only Work). Contracts:
`docs/spec/harness-loop-control.md`, `docs/spec/harness-chunk-verifier.md`,
`docs/spec/harness-return-contract.md`.

## 1. Per-chunk implement loop — from §Per-chunk implement dispatch and per-chunk gate

The sequential implement stage runs this loop; the PER-CHUNK GATE block it
renders is the canonical copy in `SKILL.md`:

```
for each `### Chunk N:` in plan order:
  1. snapshot(before) → dispatch PIPELINE implement, Chunk N
  2. on return: snapshot(after) → parse RETURN → write-scope check → `SCOPE:` token
  3. branch on RETURN.status (references/return-contract.md §7):
       COMPLETE / PARTIAL → dispatch CHUNK VERIFIER for Chunk N (repo root) → `CHUNK_VERDICT:`
       BLOCKED / BUDGET_EXHAUSTED → no verifier; the leaf's checkpoint is already in the plan
  4. render the PER-CHUNK GATE (SKILL.md block); wait for the operator:
       proceed → orchestrator commits the chunk (commit ownership) → next chunk
       fix     → repair packet (reason: VERIFIER_FAIL, failures ← verifier RETURN.failures,
                 findings: [], iteration ← chunk_redo_count[<chunk header>] + 1) → redo Chunk N → back to 2
       stop    → halt; the chunk's writes stay uncommitted in the working tree
after the last chunk: dispatch the implement-stage sdd-review ONCE on the merged state
                      → the single implement-stage review gate (proceed │ loop-back-to-fix │ stop)
```

### 1a. Gate defaults and per-chunk redo counter

- **Defaults.** `proceed` on `CHUNK_VERDICT: PASS` + `SCOPE: CLEAN`; `fix` on
  `FAIL` or `SCOPE: VIOLATION`. `proceed` on a FAIL is an explicit operator
  override recorded as gate text (`CHUNK_VERDICT: FAIL — proceeded by
  operator`); nothing is persisted. An unresolved `OUT` path is resolved by the
  scope options (`revert path | accept & widen scope`) before any choice.
- **Per-chunk redo counter.** `chunk_redo_count[<chunk header>]`, shown as
  `Redo: N of 3` against `REDO_MAX` (default 3, `harness-loop-control.md` §Redo
  Cap per Chunk), increments **only on `fix`** (a `PARTIAL_CONTINUE` or
  fresh-budget `fix` counts; a verifier re-dispatch does not). On exhaustion
  the gate behaves exactly like the fix-loop cap (§2) — `stop │ manual
  intervention │ authorized extra redo` — with the summary compiled from the
  verifier's findings; the operator may choose a replan from there. The redo
  counter is independent of the stage fix-iteration counter: the
  implement-stage review runs once after all chunks, so review-driven and
  verifier-driven loops are distinct.
- **Checkpoint on redo exhaustion (REQ-HARN-008).** When `REDO_MAX` fires at
  an implement chunk the implementer is not running, so the **orchestrator**
  composes the circuit-break checkpoint from the last `RETURN` (`failures`,
  `ledger`, `open_questions`) per the mapping table in
  `sdd-implement/SKILL.md` §Step 3, with trigger label `fix-cap`, and applies
  it as the blocked-task note under the chunk's open task (sequential: in the
  working tree before the gate renders; fan-out: after merge per
  `fan-out.md` §3e.4). `sdd-replan` Step 1 reads it as the stuck state.
- **FAIL routing.** A FAIL routes **only** to a repair packet for a redo of the
  same chunk (`fix`); never directly to a merge, to the implement-stage review,
  or to `sdd-replan`. The per-chunk gate never shows a review `VERDICT:`.
- **Review runs ONCE.** The implement-stage `sdd-review` and its stage gate run
  once, after all chunks, on the merged state: a three-chunk plan yields 3
  implement + 3 verifier dispatches (plus redos), 3 per-chunk gates, **1**
  review with **1** stage gate.
- **Post-review loop-back re-entry.** After a stage-level `loop-back-to-fix`,
  findings are mapped to chunks (`references/return-contract.md` §5 — REQ →
  spec → chunk; unmappable or multi-chunk → one `target.chunk: all` fix
  dispatch). Each fix dispatch is followed by the scope check, **one verifier
  per touched chunk**, and that chunk's per-chunk gate **before** the re-review.

### 1b. Verifier edge cases

- No `### Chunk N:` headers (v2 vocabulary) → one implement dispatch, no
  verifier, stated at the gate.
- A verifier returning `status: BUDGET_EXHAUSTED` is consumed as
  `CHUNK_VERDICT: FAIL`; you may re-dispatch it with a larger budget before
  rendering the gate — a **verifier re-dispatch is not a redo** and does not
  increment `chunk_redo_count`.
- A gate command that exits non-zero on the verifier's run but zero on your
  re-run (or on a redo with no code change) renders as `possible flake` — never
  auto-PASS.
- A verifier that writes anyway gets every path tagged `OUT`, `SCOPE:
  VIOLATION`, and its writes reverted before any redo.

## 2. Fix-loop cap (REQ-HARN-001) — from §The gate

`FIX_LOOP_MAX` is an orchestrator constant, default **3**, keyed by **stage**
and **session-only** — a new session restarts it at 0 (the restart is itself a
human intervention; nothing is persisted, REQ-ORCH-014). It increments once per
fix re-dispatch of that stage's pipeline subagent — never on `proceed`, `stop`
or a replan route. Every fix re-dispatch prompt carries the literal line
`iteration N of 3` (`iteration N of MAX` in general) inside the repair packet
(`references/return-contract.md` §3); `N of N` is the last attempt before
circuit-break. The operator may **raise the cap by one** for the current stage
at the gate by an explicit decision (not itself a fix iteration); each
authorization adds one and the gate renders the raise count — e.g.
`iteration 5 of 5 (cap raised ×2)` — so the history is visible without
persisting it.

### 2a. Exhaustion and the compiled findings log

When the stage's review returns `VERDICT: REJECT` (or `APPROVE_WITH_FIXES` and
the operator would fix again) after iteration `MAX`, do **not** dispatch another
fix. Render the gate with the **compiled findings log** and offer only
`stop | manual intervention | authorize extra iteration`:

```
Fix loop exhausted — stage: specs, 3 of 3 iterations
  iteration 1: C1 <finding text> — <file:section>; M1 <...>
  iteration 2: C1 (persisting) <finding text>; M2 <...>
  iteration 3: C1 (persisting) <finding text>
  Options: stop | manual intervention | authorize extra iteration (cap → 4)
```

Each line is the review's Critical/Material finding line lifted verbatim, one
group per iteration; no reviewer reasoning, no prose summary (REQ-ORCH-012).
The per-chunk redo cap (§1a) renders the same shape with the verifier's
findings in place of the review's.

- **Checkpoint on fix-loop exhaustion at an implement chunk (REQ-HARN-008).**
  When `FIX_LOOP_MAX` fires while the stage is implement, the implementer is
  not running; the **orchestrator** composes the circuit-break checkpoint from
  the last `RETURN` (`failures`, `ledger`, `open_questions`) per the mapping
  table in `sdd-implement/SKILL.md` §Step 3, trigger label `fix-cap`, and
  applies it as the blocked-task note under the affected task (sequential:
  working tree; fan-out: after merge per `fan-out.md` §3e.4) before rendering
  the exhausted gate. Non-implement stages have no task to annotate — the
  compiled findings log above is their only record.

#### Red round (verify stage, opt-in — REQ-REDB-HARNESSP2-007, -009)

A **red round** is one RED TEAM dispatch (`dispatch-templates.md` §RED TEAM)
after a verify-pipeline return, its gate, and — when the operator routes a
`BROKEN` `Rn` to `fix` — the `RED_BREAK` repair packet
(`return-contract.md` §3) and the re-verify that follows. Counting rules:

- **One red round = at most one fix iteration of the verify stage's counter**
  (`iteration N of 3`), however many chunk-grouped `RED_BREAK` fix dispatches
  it fans into (`return-contract.md` §5) — the same rule as one review round.
- **Red rounds and review rounds share the verify stage's single counter**: a
  cycle cannot spend 3 red rounds *and* 3 review rounds; findings from both in
  the same round count as **one** iteration and may be merged into one
  implement fix dispatch per chunk by the mapping.
- **One default re-run, not an iteration.** After the fix dispatch → scope
  check → chunk verifier → per-chunk gate, the verify pipeline is re-dispatched
  (it regenerates `verification.md` from evidence and writes `pending-red`
  again) and red is re-run **once** by default — the verifier re-dispatch
  rule, not a counted iteration. A second red re-run after the same fix needs
  an explicit operator choice and is likewise not an iteration.
- `FIX_LOOP_MAX` (3) is the backstop: its exhaustion renders the compiled
  findings log above (red's `Rn` lines in place of review findings) with no
  fourth automatic dispatch.
- Red is dispatched only after `RETURN.status: COMPLETE` from blue; a blue
  `verification.md` `status: fail` or a non-`COMPLETE` return renders the
  non-token line `Red team: not run (blue status fail)` and proceeds to the
  normal fix/replan routing.

Sequence per red round:

```
fix dispatch (implement chunk) → scope check → chunk verifier → per-chunk gate
  → re-dispatch verify pipeline (regenerates verification.md from evidence; writes pending-red again)
  → red re-run ONCE by default (not an iteration — the verifier re-dispatch rule)
  → verify stage gate with a fresh RED_VERDICT:
```

Gate fixture — pasted verbatim from `docs/spec/adversarial-verify.md`
§Verify-Stage Gate and Exit Rule (signal order `RETURN.status` → `SCOPE:` →
`RED_VERDICT:` → `VERDICT:` → counters; `proceed` withheld until every
`BROKEN` `Rn` is fixed or accepted):

```
Verify stage gate — pipeline #9 (sdd-verify), red #10, review #11
  RETURN.status  : COMPLETE   budget_consumed: {tool_calls: 41, test_runs: 6}  vs  Budget: ~70 tool calls
  SCOPE: CLEAN
  RED_VERDICT: BROKEN
    - R1: <criterion> — attack: … — observed: … — reproduce: `python -m app --window 0` — BROKEN
    - R2: <criterion> — attack: … — observed: held — reproduce: `pytest -q tests/test_recon.py::test_window` — HELD
  VERDICT: APPROVE
  iteration 0 of 3
  Options per BROKEN finding: R1 → fix (RED_BREAK packet) | accept (record) | stop
  proceed: unavailable until every BROKEN Rn is fixed or accepted
```

`accept (record)` appends `- Rn accepted at gate <YYYY-MM-DD>: <observed> —
reproduce: \`<cmd>\`` under `verification.md` §Issues Found → Minor (marker
`4`: `docs/ws/<id>/verification.md`) — bookkeeping in an existing section of
an existing artifact, outside the observed window; no review store is created.
On `proceed` the orchestrator flips `status: pending-red → pass` immediately
before its commit (`../SKILL.md` §The gate).

## 3. Replan re-entry cap derivation (REQ-HARN-002, REQ-HARN-003) — from §The gate

`REPLAN_MAX` is an orchestrator constant, default **3**. The count is never
stored; recompute it on every replan trigger, before routing into `sdd-replan`:

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

- `<kickoff>` / `<plan-history>` are `docs/handoff/kickoff.md` /
  `docs/plan-history/` under marker `3` and `docs/ws/<id>/kickoff.md` /
  `docs/ws/<id>/plan-history/` under marker `4` — the count is per workstream.
- Only `sdd-replan` writes archives carrying the `-replan-` segment
  (`{date}-replan-{reason}.md`; per milestone `{date}-m{N}-replan-{reason}.md`).
  `sdd-plan` rewrite archives (`{date}-{reason}.md`) and milestone-complete
  archives (`{date}-m{N}-complete.md`) never count; archives dated before the
  kickoff date never count (previous cycle); minor in-place replans leave no
  archive and are deliberately not counted.
- The legacy fallback is deliberately **not** `git log --diff-filter=A
  --follow` (that yields first creation — wrong once the kickoff is overwritten
  per cycle); the `-S` pickaxe finds the commit that started the current cycle.
- **Neither determinable** (no `date:`, kickoff uncommitted, or `research_id:`
  unmatched): the cap is **treated as reached** — the gate shows
  `replan re-entry cap: kickoff date undeterminable — treated as reached` with
  every `-replan-` archive listed, and routes into `sdd-replan` only on an
  explicit operator decision. The cap is never silently unreachable.
- When `count >= REPLAN_MAX`, surface the cap as a gate event (REQ-ORCH-017
  shape) naming the count, the cap and the counted archive filenames; do not
  route into `sdd-replan` without an explicit operator decision.

## 4. Fan-out lifecycle summary — from §Execution Model

The full command sequence is `references/fan-out.md` §3; this is the contract
summary that used to sit in `SKILL.md`. Under marker `3` everything below
applies against `main` UNCHANGED; under marker `4` the provision base,
merge-back target and redo re-branch are the workstream branch and the
boundary-error inference is removed — `references/fan-out.md` §0/§3c,
`references/v4-workstreams.md` §Marker-4 anchor.

### 4a. Lifecycle (provision → dispatch → merge → teardown)

When the operator opts in and the graph has ≥2 independent branches:

1. **Provision** one worktree/branch per group yourself; worktree ownership is
   the orchestrator's (Q-REQ-G) so provisioning and teardown stay symmetric.
2. **Dispatch** one **leaf** implement subagent per group, pinned to its
   worktree/branch, carrying that group's chunks; a leaf runs `sdd-implement`
   and cannot sub-dispatch (REQ-ORCH-022). Non-interactivity and central ID
   assignment apply. Issue all dispatches **in one batch**, then **await all
   returns** before merging. Each leaf commits with an inline
   `git -c user.email=… -c user.name=…` identity — never by writing
   `.git/config`, which the sandbox blocks (RS-006 Q2).
3. **Sequential merge:** one branch at a time, **all** merges **before** the
   implement-stage review; one-at-a-time merging rules out partial-merge
   corruption. Each leaf's per-leaf gate (the §1 block, rendered before merge
   with no orchestrator commit — `references/fan-out.md` §3a.v) precedes its
   merge.
4. **Teardown** each worktree and branch after its clean merge, leaving only
   `main` for the review.

### 4b. Conflict handling (redo by re-derivation)

On a merge conflict: abort the single failing merge (merged work is never
corrupted), then **redo the chunk-group by re-derivation** — a fresh worktree
re-branched from the updated `main`, a fresh leaf re-running `sdd-implement`.
**Never replay the stale returned patch.** A group that **still** conflicts
after re-derivation was not truly independent (a boundary error) → **run the
affected groups sequentially**, which cannot conflict and guarantees
termination. A merge-abort redo counts toward that group's chunks'
`chunk_redo_count` like any other `fix`. Full command sequence:
`references/fan-out.md` §3c (Q-IMPL-1).

## 5. Gate signal order (REQ-ORCH-034) — from §The gate

Signals surface in the order they are produced; everything is ephemeral
(REQ-ORCH-013). `SKILL.md` §The gate keeps the one-line summary; this is the
per-signal detail:

1. the leaf's `RETURN.status` and `budget_consumed` against the dispatched
   `Budget:` (`references/return-contract.md` §1, §7);
2. the write-scope block ending in the own-line `SCOPE: CLEAN | VIOLATION (N
   paths)` token (`references/write-scope.md` §5) — branch on the token, never
   prose: `VIOLATION` offers, per `OUT` path, `revert path | accept & widen
   scope | stop`, resolved before the chunk's commit (sequential) or the leaf's
   merge (fan-out), with `proceed` unavailable while any `OUT` path is
   unresolved; a `HISTORY_REWRITE` finding counts as a violation and offers only
   `stop` (`SKILL.md` §Isolation Discipline);
3. implement stage only, per chunk: the chunk's `CHUNK_VERDICT:` (parsed from
   the verifier's `RETURN:` block, last line; missing or unrecognized →
   `RETURN: MALFORMED`) with `Redo: N of 3` against `REDO_MAX` — signals 1–3
   render at the **per-chunk gate** (§1);
4. the parsed review `VERDICT:`;
5. when a loop is active, the loop counters — `iteration N of MAX` for the
   fix-loop cap (§2) and the derived count against the replan re-entry cap
   (§3) — signals 4–5 (and, for a non-implement stage, 1–2 with them) render
   at the **stage gate**.

## 6. Edge cases routed through the gate — from §The gate

- **Replan trigger**: if a pipeline subagent triggers a replan (stuck detection,
  spike invalidation, or a verification failure), surface it to the operator as a
  gate event — after recomputing the replan re-entry cap (§3). The loop may then
  route back to an earlier stage via `sdd-replan`, consistent with the cyclic
  SDD model. Do not silently absorb or auto-resolve a replan trigger.
- **Reject with no actionable findings**: if a review returns a reject/fail
  verdict carrying no actionable findings, **pause** and let the operator decide
  (re-dispatch, override, or stop). Do not auto-loop the pipeline.
- **`REVIEW: MALFORMED`**: if the review's `VERDICT:` token is missing,
  unrecognized, or disagrees with its prose verdict, **pause** with
  `re-dispatch review | accept prose manually | stop`. Never guess the verdict
  from prose (`references/return-contract.md` §6).
- **`RETURN: MALFORMED (<reason>)`**: if a leaf's `RETURN:` block is absent,
  `status:` is not its first key or not one of the four values, a value spans
  multiple lines, or the block is self-contradictory, **pause** with the raw
  tail of the return and `re-dispatch | accept manually | stop`. Never treat a
  malformed return as `COMPLETE` (`references/return-contract.md` §1).
