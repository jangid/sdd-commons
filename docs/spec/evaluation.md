---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-EVAL-HARNESSP2-001
  - REQ-EVAL-HARNESSP2-002
  - REQ-EVAL-HARNESSP2-003
  - REQ-EVAL-HARNESSP2-004
---

# Multi-Run Evaluation

## Context

Idea catalogue item D12 asks for ADK-style N-run evaluation of the SDD skills
on a toy project with pass-rate telemetry. RS-HARNESSP2-001 Q5 returned a
**no-go** for building an N = 30 harness this cycle — nothing can be measured
until telemetry exists, a canned gate policy is the auto-advance REQ-ORCH-011
prohibits, and an N-run outer loop must dispatch the orchestrator N times,
which a subagent cannot do (RS-006 Q1) — and a **go** for three smaller
things: telemetry fields chosen with the scorer in mind (`telemetry.md`), a
definition of what an evaluation mode would be, and a manual N = 3 pilot after
telemetry lands.

This spec records the evaluation-mode definition (defined, not built), fixes
the scorer field list and its derivation contract, designs the pilot as a
verify task with a §Next Steps deferral, and states the out-of-scope harness
with its three blocking conditions. It fulfils REQ-EVAL-HARNESSP2-001..004.

## Design

### Evaluation Mode — Defined, Not Built (REQ-EVAL-HARNESSP2-001)

| Property | Definition |
|---|---|
| Activation | opt-in per run |
| Permitted only on | a toy repository whose `CLAUDE.md` declares `sdd-eval-toy: true` |
| Gate decisions | a canned **policy** — a pure function over the v5/v6 tokens (below) |
| Telemetry | every policy decision recorded as `gate.decision_by: policy` (`telemetry.md`) |
| Status this cycle | **definition only** — no skill implements the policy; REQ-ORCH-011 and `sdd-orchestrate` §Rules ("never auto-advance") stay unamended; every gate in every run, including the pilot, is operator-decided (`decision_by: operator`) |
| Adoption | a future requirements decision that amends REQ-ORCH-011 explicitly |

Policy function (recorded for that future decision; inputs are tokens only):

| Gate state | Policy decision |
|---|---|
| `VERDICT: APPROVE` ∧ `SCOPE: CLEAN` ∧ `CHUNK_VERDICT: PASS` (∧ `RED_VERDICT: HELD` when red is on) | `proceed` |
| `APPROVE_WITH_FIXES`, or `REJECT` with actionable findings, while `iteration < FIX_LOOP_MAX` | `fix` (`loop-back-to-fix`) |
| any pause: `RETURN: MALFORMED`, `REVIEW: MALFORMED`, `SCOPE: VIOLATION`, `REVIEW: CONTRADICTION`, reject with no actionable findings, cap exhausted, replan trigger, `RED_VERDICT: BROKEN` | `stop` |

**Why define without building**: writing the function down now costs nothing
and pins the token vocabulary the scorer and any future headless driver would
consume; building it would silently amend an approved requirement.

Guard: `grep -rn 'decision_by' skills/` matches only the telemetry schema in
`sdd-orchestrate/references/telemetry.md`.

### Scorer Fields (REQ-EVAL-HARNESSP2-002)

The future stdlib-only `tools/sdd-eval.py` reads `.sdd/telemetry.jsonl` plus
the toy's `verification.md` `status` line and computes, per run and aggregated
over N runs:

| # | Field | Definition |
|---|---|---|
| 1 | first-attempt pass rate | runs with `verification.md status: pass` and zero verify-stage fix iterations / N |
| 2 | mean fix iterations per stage | per stage, the max `fix_iteration` reached, averaged over runs |
| 3 | `SCOPE: VIOLATION` rate | violations / scope-checked dispatches |
| 4 | `MALFORMED` rate | malformed returns or reviews / dispatches |
| 5 | dispatches per chunk | implement + verifier + redo + fix dispatches per chunk (RS-008 probe 1) |
| 6 | `CONTRADICTION` pauses per run | count |
| 7 | red `BROKEN` findings per run | count |
| 8 | self-reported tool calls per run vs budget | sums |
| 9 | wall time per dispatch and per run | from the three timestamps |

**Derivation contract**: every field is derivable from the TELEM record key
set alone plus `verification.md`'s `status`; the mapping field → record keys is
the "scorer derivation" table in `telemetry.md` §Scorer Derivation, checked at
the specs stage (this cycle: all nine derive). A scorer field that is not
derivable is a **telemetry schema defect**, not a scorer limitation. The
scorer's implementation may ship this cycle if the plan has room; otherwise it
is queued in `verification.md` §Next Steps naming this requirement. Output
shape when built: one row per run + one aggregate row, CSV or aligned text;
`--help`, `--self-test` on a six-record fixture.

### Manual N = 3 Pilot (REQ-EVAL-HARNESSP2-003)

A **verify task** in the plan (not implement), ordered after telemetry lands.

| Element | Design |
|---|---|
| Toy | `tools/sdd-scope-check-selftest.py` `make_repo()` shape (`src/recon/engine.py`, `tests/test_recon.py`) + one requirement, one spec with two acceptance criteria, a two-chunk plan, `CLAUDE.md` naming `pytest -q` as the gate and `sdd-eval-toy: true`; `docs/.sdd-version` = `4`, workstream `default` |
| Runs | three orchestrated cycles; at least one entering at research, the others at plan (REQ-ORCH-031..033); every gate operator-decided |
| Telemetry | in the **toy's own** `.sdd/telemetry.jsonl` (one file per repository); this repository's file gains no pilot record |
| Scoring | `tools/sdd-telemetry.py summarize` on the toy, or by hand from the records; fields 1–9 above |
| Recording | a "Pilot (N = 3)" section in `docs/ws/harness-p2/verification.md`, in the same form as RS-008 probes 1 and 2 in `docs/ws/default/verification.md`, with the table below; observed wall time per run stated |
| Size rationale | ~1k tool calls fits one operator session (RS-HARNESSP2-001 Q5: ~250–520 per run) |
| Deferral | if the plan has no room, `verification.md` §Next Steps — the `## Next Steps` section the `sdd-verify` Step 6 template gains per `adversarial-verify.md` §Skill and Lint Changes (sdd-verify row), which is the single definition of that slot — carries `- REQ-EVAL-HARNESSP2-003: run the N = 3 pilot on the toy` |

Recording table shape:

```
| Run | Entry | Pass on first attempt | Fix iterations (per stage) | Dispatches | Tool calls (self-reported) | Wall time |
|-----|-------|-----------------------|----------------------------|------------|----------------------------|-----------|
| 1   | research | yes/no | research 0, …, verify 1 | 17 | 312 / 520 | 1h 42m |
| 2   | plan  | … | … | … | … | … |
| 3   | plan  | … | … | … | … | … |
```

### Out of Scope: N ≥ 30 Headless Harness (REQ-EVAL-HARNESSP2-004)

Not built this cycle. Blocking conditions, each to be resolved by a later
cycle before the harness enters scope:

| Condition | What resolves it |
|---|---|
| (a) telemetry first | TELEM shipped and the N = 3 pilot recorded — a baseline exists |
| (b) evaluation-mode carve-out | an explicit requirements decision amending REQ-ORCH-011 (not adopted now) |
| (c) orchestrator-only outer loop | a human running N sessions, or a verified headless driver that runs `/sdd-orchestrate` non-interactively with the policy gate — unverified in this repository and not probeable by a subagent (RS-006 Q1; `index.md` Open Questions) |

Until then the pilot is manual-N-only. No `tools/sdd-eval-run*` or
headless-driver script exists after this cycle; the plan contains no task
that dispatches the orchestrator.

## Verification

### Automated

- `test_decision_by_only_in_telemetry_schema`: `grep -rn 'decision_by'
  skills/` matches only `sdd-orchestrate/references/telemetry.md`.
- `test_never_auto_advance_sentence_present`: `sdd-orchestrate/SKILL.md`
  §Rules still contains the never-auto-advance sentence.
- `test_no_policy_records_this_cycle`: no record in this repository's
  telemetry has `decision_by: policy`.
- `test_scorer_fields_derivable`: for each of the nine fields, the derivation
  row in `telemetry.md` names only record keys and `verification.md status`; a
  six-record fixture yields every field.
- `test_pilot_recorded_or_deferred`: `docs/ws/harness-p2/verification.md`
  contains a "Pilot (N = 3)" section with three run rows and the toy's
  telemetry holds the three runs, **or** §Next Steps names
  REQ-EVAL-HARNESSP2-003.
- `test_no_harness_script`: no `tools/sdd-eval-run*` or headless-driver file;
  no plan task dispatches the orchestrator; `index.md` Out of Scope names the
  harness with conditions (a)–(c).

### Manual

- The pilot itself (§Manual N = 3 Pilot) — operator-run.

### Acceptance Criteria

- [ ] Evaluation mode defined (opt-in, toy-only, policy function table, `decision_by: policy`), not implemented; REQ-ORCH-011 and §Rules unamended; all gates operator-decided (REQ-EVAL-HARNESSP2-001)
- [ ] Nine scorer fields fixed; derivation table in `telemetry.md` covers each; non-derivable field = schema defect; scorer ships or is queued in §Next Steps (REQ-EVAL-HARNESSP2-002)
- [ ] Pilot designed as a verify task after TELEM: toy shape, three runs, toy-local telemetry, recording table, wall time, deferral line (REQ-EVAL-HARNESSP2-003)
- [ ] N ≥ 30 harness out of scope with conditions (a), (b), (c); no driver script; no orchestrator-dispatching task (REQ-EVAL-HARNESSP2-004)
- [ ] `python3 tools/sdd-skill-lint.py` exits 0

## Edge Cases

- **A pilot run hits a pause** (`MALFORMED`, `VIOLATION`, `CONTRADICTION`):
  the operator decides as usual; the run is recorded with the pause counted —
  pauses are data, not failures of the pilot.
- **Pilot run entering at research on a toy with no research to do**:
  research early-exits with a "covered" finding (`ws-orchestration.md`); the
  run still counts as a research-entry run.
- **Scorer built before the pilot**: it runs on an empty file and prints zero
  rows with `N = 0`; no error.
- **Toy repository reused across runs**: each run is a new cycle in the
  `default` workstream (prior `verification.md` `status: pass` → "new cycle");
  `cycle.kickoff_date` distinguishes runs on the same day only if the kickoff
  is rewritten — Open Question 1.

## Cross-Spec Consistency (XSPEC)

- `telemetry.md` §Record Schema ↔ §Scorer Fields: `gate.decision_by`,
  `verdict.contradiction_class`, `return.failures_n` for red,
  `dispatch.budget` / `return.budget_consumed`, the three timestamps — all
  present; §Scorer Derivation covers fields 1–9.
- `orchestration.md` §Gate Protocol / REQ-ORCH-011: unamended; the policy is
  text in this spec only.
- `adversarial-verify.md`: `RED_VERDICT: HELD` conjunct and `BROKEN` → `stop`
  use the token as defined there.
- `arbitrated-handoff.md`: `REVIEW: CONTRADICTION` → `stop` in the policy;
  counted as field 6.
- `harness-loop-control.md` §Fix-Loop Cap: `iteration < FIX_LOOP_MAX` is the
  policy's fix guard — same counter.
- `ws-orchestration.md` new-cycle-per-workstream rule is what lets three runs
  share one toy.
- **No unresolved contradictions.**

## Open Questions

1. **Run identity when two pilot runs share a kickoff date**: Default: the
   operator rewrites `kickoff.md` per run (DISCUSS → KICKOFF each time) so that
   each run's kickoff names a **distinct `research_id`** (the research-entry run
   mints one; a plan-entry run cites its own — two plan-entry runs must not
   share an id). A run boundary is a change of `cycle.research_id`, stamped on
   every record (`telemetry.md` §Record Schema); readers order records by
   `ts_dispatch` within a run and never rely on `dispatch.seq` monotonicity
   across sessions (`seq` restarts at 1 in every session). Runs on one date are
   told apart by `research_id`, not by `kickoff_date`.
2. **Should the scorer ship this cycle?** Default: only if the plan has room
   after TELEM, REDB, ARB, GC and the sdd-implement split; otherwise §Next
   Steps.
3. **Headless driver verification** (`index.md` Open Questions): Default:
   not probed this cycle; manual N only.
