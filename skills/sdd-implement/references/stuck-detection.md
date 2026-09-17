# Stuck Detection — Attempt Ledger, Oscillation, Checkpoint, Budget

Detail behind `../SKILL.md` §Step 3 (the stub keeps the trigger list and a
summary). Read on demand, the way `sdd-orchestrate`'s references are.
Contracts: REQ-HARN-005..008, `docs/spec/harness-loop-control.md`;
`RETURN:` field semantics in `leaf-return.md`.

---

## Attempt ledger (REQ-HARN-006)

Keep, per task, an in-context ledger with one entry per attempted fix and a
`verified_do_not_touch` list:

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

- `attempt` is a 1-based ordinal; `hypothesis`, `change`, `result` are each
  one line. `change` names files (and lines where useful); `result` names
  which tests now pass / fail.
- `verified_do_not_touch` lists paths whose tests pass and that later attempts
  must not modify; an attempt whose `change` touches a listed path is a rule
  violation — **revert it before continuing**.
- The ledger is **context-only**. Its durable traces are `RETURN.ledger` /
  `RETURN.verified_do_not_touch` (when dispatched) and the checkpoint below.
  It is **never** written to `docs/spec/*.md`, `docs/handoff/kickoff.md`, or
  any new file.
- The ledger is **not a Q-IMPL entry**: Q-IMPL records a spec-deviation
  *decision*; the ledger records *attempts*. When an attempt reveals a spec
  ambiguity, file a Q-IMPL entry as usual and cite its id in `open_questions`
  and in the checkpoint — never duplicate the entry's text.

## Oscillation rule (REQ-HARN-007)

After **every** attempt, evaluate both conditions as string comparisons over
the ledger; either one is a stuck trigger (**oscillation**):

- **(a) Regression oscillation** — an attempt's `result` reports a test failing
  that an earlier attempt's `result` reported passing (a fix re-introduced a
  fixed failure). Fixture: `attempt 1: test_drift passes` then `attempt 2:
  test_drift REGRESSED` → stuck.
- **(b) Repeated patch** — an attempt's `change` equals (after whitespace
  normalization) an earlier attempt's `change`.

## When stuck

1. **Stop** — don't keep trying the same approach
2. **Document** what you tried and why it failed — the ledger already holds
   it; compose the **circuit-break checkpoint** below
3. **Assess**: is this a spec gap, a plan ordering issue, or a research question?
4. **Recommend**: invoke `sdd-replan` with the stuck context (standalone), or
   return `status: BLOCKED` and let the orchestrator route (dispatched —
   `leaf-return.md`)

## Circuit-break checkpoint (REQ-HARN-008)

**Trigger**: stuck detection (including oscillation); budget exhaustion
mid-task (below); the stage fix-loop cap (`FIX_LOOP_MAX`) firing on an
implement task; or the per-chunk redo cap (`chunk_redo_count[<chunk>]`
reaching `REDO_MAX`) firing at that chunk's per-chunk gate.

**Slot**: the blocked-task note under that task in the plan — the slot
`sdd-replan` Step 4 already defines ("mark blocked tasks — note why they're
blocked and what unblocks them"). No new section, no new file.

**Format** (bounded, ≤ ~15 lines, no traceback frames):

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

**Composition from the `RETURN:` block** (there is **no dedicated checkpoint
field**):

| Checkpoint line | Source |
|---|---|
| `failing:` lines (test + one-line reason) | `failures[].test` + `failures[].message` |
| `last hypothesis:` | last `ledger[].hypothesis` |
| `attempt N:` one-liners | `ledger[].change` + ` -> ` + `ledger[].result` |
| `open question:` | `open_questions[]` (cites a Q-IMPL id where filed) |
| trigger label `(oscillation \| budget \| fix-cap)` | orchestrator / implementer state |

**Who writes it**: in sequential mode (standalone use, or a dispatch whose
write scope includes the plan) **you** write it directly under the task. Under
fan-out you are barred from the plan — return the `RETURN:` fields and the
orchestrator composes and applies the note in
`sdd-orchestrate/references/fan-out.md` §3e post-merge bookkeeping. Full
tracebacks are never stored; `sdd-replan` Step 1 reads this note as its stuck
state and regenerates them by re-running the named tests. One checkpoint per
task; the ≤ 15-line bound is per checkpoint. A blocked note does not change
phase detection (the plan still has incomplete tasks) and cannot make the plan
stale.

## Budget exhaustion (REQ-HARN-005)

When dispatched with a `Budget:` line and you reach **any** term of it:

1. Stop starting new work — finish or revert the in-flight edit so the tree is
   consistent.
2. If exhaustion occurred mid-task, compose the circuit-break checkpoint
   (trigger label `budget`). Sequential implementer: write it into the plan.
   Fan-out leaf: return it through the `RETURN:` fields (you are barred from
   the plan).
3. Return a `RETURN:` block with `status: BUDGET_EXHAUSTED` and
   `budget_consumed` in **the same units** the `Budget:` slot was stated in,
   e.g. `budget_consumed: {tool_calls: 25, test_runs: 3, chunks: 0}`. A
   `BUDGET_EXHAUSTED` return without `budget_consumed` is malformed and pauses
   at the gate. If the budget named a unit you cannot count, report the units
   you can and note the mismatch in `open_questions`.
