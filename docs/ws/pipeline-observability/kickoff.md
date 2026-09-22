---
workstream: pipeline-observability
description: Pipeline observability — the harness makes claims about itself that nothing verifies; close the eleven gaps consumer-geometry's own run exposed, dogfooding each fix at the next gate
cycle: pipeline-observability-1
research_id: RS-PIPELINEOBSERVABILITY-001
entry_stage: research
date: 2026-09-22
branch: pipeline-observability
supersedes: RS-CONSUMERGEOMETRY-001
---

# Kickoff: RS-PIPELINEOBSERVABILITY-001 — the harness verifying itself

Run `/sdd:research` for workstream `pipeline-observability`. This spike is
grounded in defects already observed live during the `consumer-geometry` cycle
(§The observation); it does not have to rediscover them, and re-deriving them
is out of scope.

## The observation — carried as EVIDENCE, do not re-derive

Measured over the `consumer-geometry` cycle (2026-09-21 → 2026-09-22, branch
`consumer-geometry`, merged as PR #6 at `fb4635f`): one research spike, four
document stages, nine implement chunks, one verify stage with a red round;
17 review rounds, 9 chunk gates, 2 read-only-leaf write-scope violations and
5 orchestrator errors. Every gate rendered green. The gates were not lying
about the artifacts; they were silent about the harness.

The eleven gaps, each with the observation that exposes it, in the operator's
priority order:

1. **Telemetry is written but not readable.** The gate rendered `TELEMETRY:
   rec 39` and the file gained 53 records; `python3 plugins/sdd/tools/telemetry.py
   summarize` reads zero of them. The schema example exists
   (`orchestrate/references/telemetry.md`, §2); `append` validates nothing and
   the tool has only `summarize | migrate`, no `append` subcommand.
2. **Read-only leaves are not read-only.** All three shipped harness agents
   (`reviewer`, `chunk-verifier`, `red-team`) declare `Bash` and carry zero
   prohibitions on git-state or file mutation. Observed: a `git stash` by the
   verifier at chunk 0; an in-place edit of `gc.py` by a leaf at chunk 2. The
   write-scope snapshot does not name a `GIT_STATE` check for either.
3. **The fix-loop cap counts the wrong thing.** `FIX_LOOP_MAX` fired at every
   one of the four document stages on `APPROVE_WITH_FIXES` with zero blocking
   findings — 16 rounds of a cap designed for repeated `REJECT`. The class-(b)
   `REVIEW: CONTRADICTION` pause fired twice on staleness that the fix loop's
   own edits created (a cross-reference to a section the fix had just moved).
4. **Manual orchestrator fixes skip review.** Four manual interventions; they
   introduced 2 defects and 3 stale claims. All 5 orchestrator errors were
   caught by subagents, none by a gate.
5. **No lint for the comparand class behind 12 of 17 blocking findings.** A
   criterion whose comparand is a snapshot the artifact invalidates: live line
   citations (58 `\.md:\d+` today, outside fences, in specs and requirements),
   and greps that match their own file (5 times this cycle).
6. **Tier headings are not parsed.** Specs review round 4 listed entries under
   `### Blocking` and closed `VERDICT: APPROVE_WITH_FIXES`; `agents/reviewer.md`
   forbids exactly that and nothing caught it.
7. **`QIMPL_RE` is too loose.** A bare `Q-IMPL-029` (no workstream segment)
   raised a live fail at the plan gate instead of being rejected as malformed.
8. **The implement dispatch budget under-counts test runs.** Observed overruns
   of 8 against 6 and 18 against 12; the honest formula is
   `test_runs = 2 × mutations + gates`.
9. `.claude/` is inside the hygiene hooks' scope; `end-of-file-fixer` cannot
   open `.claude/settings.json` (recurring since the `marketplace` cycle).
10. Check 3 does not honour a declared test convention; the identical advisory
    fired 9 of 9 chunks.
11. A same-cycle stale-chain finding is `info`; the §CG-11(b) gap closed only
    by argument, not by a gate.

**Why it outranks its size.** This is consumer-geometry's defect one level up:
there, a tool silently reduced its checks; here, the harness silently reduces
its own claims. `TELEMETRY: rec 39` with no readable record is the same shape
as `FAIL: 1 finding` with twenty checks not run.

## The three decisions already made at DISCUSS

1. **Harness first, over tool debt.** Gaps 1, 3, 4 and 5 tax every future cycle.
2. **A new series, not `harness-p7`.** `harness-p6`'s terminality bound p6's
   backlog; it guarantees no carried work, not that no future defect can be
   found. This workstream inherits nothing from `harness-p2..p6` and cites only
   consumer-geometry's evidence.
3. **Dogfood at the next gate.** Each fix governs every later gate in this cycle
   from the commit it lands in; `verification.md` records which gates ran under
   which rules. Gap 4 is a process rule and applies **from the first gate**,
   before any code lands.

## Scope

Gaps 1–8 as work; gaps 9–11 as one-line fixes, each with a falsifier.

## Out of scope

- The six carried tool-debt items from `consumer-geometry` (its
  `verification.md` §Next Steps).
- The `docs/spec/packaging.md` split.
- Any new SDD phase, skill or agent.
- Any change to the nine phase skills' own workflow semantics.

## Constraints — these bind every stage, not just this spike

1. **Writes land in `plugins/sdd/` and `docs/` in this repository.** The
   installed plugin cache at `~/.claude/plugins/cache/sdd-commons/` is
   read-only. At KICKOFF the cache (0.1.0) was nine files behind the repo,
   including the `gc.py` fix from PR #6; the operator updates it outside the
   session before the first dispatch. Any stage that observes a cache-vs-repo
   divergence records it as a finding, never edits the cache.
2. **Every binding this cycle touches must have its reversion fail a gate,
   demonstrated by running the mutation — not asserted.** From the first
   dispatch.
3. **Dogfooding as decided above.** A gate that runs under a rule this cycle
   introduced says so on the gate block.
4. **`FIX_LOOP_MAX` = 3, no extra-iteration authorisations.** Gap 3's
   rejection-counting semantics apply from the commit that lands them, not
   retroactively.

## Open questions

**Q1 — Telemetry.** What does the reader enforce versus what `telemetry.md`
specifies? What must `append` validate so that `rec n` is rendered only on a
validated write? Can the 53 orphan records be migrated, or must they be
declared lost?

**Q2 — Read-only leaves.** Can read-only be *enforced* (tooling: tool list,
sandbox, hook) or only *detected* (a `GIT_STATE` check in the write-scope
snapshot), given the leaves need `Bash` to run quality gates? Name the
observable that catches the `git stash` and the in-place edit.

**Q3 — Replay the 17 review rounds.** With a cap that counts consecutive
`REJECT`s and treats `APPROVE_WITH_FIXES` at cap as apply-and-proceed, which
routings change? Would tier-heading parsing have caught specs round 4? Is a
stale cross-reference to a just-fixed section class (a), and what rule
decides it?

**Q4 — Replay the 4 manual interventions.** Would a default re-review have
caught the 2 defects and 3 stale claims, and at what cost in rounds?

**Q5 — The two lint rules.** For `literal-anchor` (`\.md:\d+` outside fences
in specs/requirements → warn) and `self-matching-grep` (a criterion's pattern
matching its own file outside fences → fail): the false-positive rate on
today's corpus, and a decidable definition of "self-matching" derived at read
time, never from a literal list.

**Q6 — Gaps 7–11.** Confirm each is a one-line fix and name its falsifier.

## Success criteria

Every gap has a falsifying construction reachable today — a command or input
that makes the current harness render a wrong claim, and that the fix turns
red. Q1–Q5 return a recommendation with evidence, or an explicit OPEN with the
blocking constraint named. Q6 returns five falsifiers or says which gap is not
a one-liner.

## Budget

**30 tool calls, 0 test runs.** Reading `telemetry.py`, the three agent
bodies, `write-scope.md`, `loop-control.md` and the consumer-geometry
telemetry is most of the work.

## Deliverable

`docs/research/RS-PIPELINEOBSERVABILITY-001-harness-self-verification/findings.md`,
with `status: Complete` when the six questions are answered or explicitly OPEN.
