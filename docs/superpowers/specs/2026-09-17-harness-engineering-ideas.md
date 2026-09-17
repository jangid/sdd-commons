# Harness-engineering ideas for the SDD harness (DISCUSS input)

Date: 2026-09-17. Sources walked:

- Google Cloud Tech, "What is harness engineering and why should I care?" (Shir Meir Lador) —
  https://dev.to/googleai/what-is-harness-engineering-and-why-should-i-care-8n0 (mirror of the X article)
- Balaji Subramaniam, "Harness Engineering for Multi-Agent Systems using Google ADK 2.0" —
  https://medium.com/google-cloud/harness-engineering-for-multi-agent-systems-using-google-adk-2-0-e248b885cb95
- Balaji Subramaniam, "Loop Engineering for Coding Agents" — https://medium.com/@BalajiBuilds/61c30c9e36ca
- OpenAI, "Harness engineering" — https://openai.com/index/harness-engineering/
- GitHub: balajismaniam/adk-harness-engineering (6 case studies, README best practices)
- GitHub: google/adk-python contributing/samples/workflows/loop (conditional back-edge loop sample)

## Core thesis of the sources

The LLM is a stateless reasoning engine; reliability comes from the deterministic wrapper:
**orchestration, execution sandboxing, state persistence, verification loops**. Three headline
principles: **strict boundaries**, **repair loops** (trap errors, feed clean logs back),
**progressive context discovery** (small stable entry point, taught where to look next).

## What our SDD harness already does well (no action)

| Source principle | Existing SDD mechanism |
|---|---|
| Orchestration layer with human exception routing | `sdd-orchestrate` gates after every stage |
| Sandboxed execution, per-branch isolation | worktree fan-out (`fan-out.md`), abort-redo merge |
| Decoupled verifier (creator ≠ evaluator) | separate review subagent with paths-only inputs |
| State persistence, resumability | on-disk artifacts are the sole source of truth |
| Stop conditions | `sdd-implement` stuck detection (3 fails / 2× effort / spec contradiction) |
| Budgets in observable units | `sdd-research` budget (approaches, tool calls) |
| Progressive disclosure | `references/` files loaded on demand |
| Mechanical enforcement | `tools/sdd-skill-lint.py` |

## Gaps → improvement ideas

### A. Loop control and stop conditions
1. **Max-iteration guard on the fix loop.** `loop-back-to-fix` has no cap; a reject → fix → reject
   cycle can ping-pong indefinitely. Add a hard cap (default 3) per stage; on breach, exit to the
   operator with a compiled findings log (ADK "ROUTE_TO_HUMAN_EXCEPT"). Same cap for replan re-entries per cycle.
2. **Budgets for every dispatch, not just research.** Every pipeline/fix dispatch carries an explicit
   budget in observable units (tasks, tool calls, test runs). Exhaustion = checkpoint + return, never silent overrun.
3. **Attempt ledger / oscillation detection in stuck detection.** Keep a per-task ledger of
   (hypothesis, change, result). Stuck also fires when a fix re-introduces a previously fixed failure
   (ping-pong) or repeats a rejected patch. Ledger carries "verified segments — do not touch".
4. **Checkpoint on circuit-break.** When stuck/budget/iteration guard fires, write a structured
   checkpoint (failing tests, last traceback, ledger, open question) into the Q-IMPL/handoff so a
   human or fresh session resumes without re-deriving.

### B. Decoupled verification
5. **Fresh verifier at chunk close.** Chunk-close checks are currently run by the implementer itself
   (self-validation bias). Under orchestrate, dispatch a fresh, cheap verifier subagent per chunk
   that only runs gates + spec-type alignment and returns pass/fail.
6. **Repair packet template.** Fix-loop dispatches carry a fixed-shape packet: failing test names,
   clean traceback/lint output, spec excerpt, ledger summary — no prose reasoning.
7. **Machine-parseable verdict tokens.** Reviewer must emit `VERDICT: APPROVE | APPROVE_WITH_FIXES |
   REJECT` on its own line so the orchestrator branches deterministically instead of parsing prose.

### C. Context hygiene (state pruning)
8. **Pruned state on re-dispatch.** Codify that a fix re-dispatch passes only the latest artifact
   paths + latest findings (never accumulated history); cap dispatch prompt size, reference big
   content by path.
9. **Orchestrator owns routing decisions.** Phase detection / verdict classification never delegated
   to a pipeline subagent (keeps the subagents' contexts clean). Document as a principle.
10. **Progressive-disclosure audit of SKILL.md sizes.** `sdd-orchestrate/SKILL.md` has absorbed all
    v4 gating prose. Move marker-4 branches into `references/v4-workstreams.md`; add a soft size
    check to the lint ("entry point ≈ table of contents").

### D. Observability
11. **Per-dispatch telemetry.** Record stage, wall time, fix iterations, verdict, replan triggers
    in a gitignored `.sdd/telemetry.jsonl`. Design question: must not become the forbidden loop log.
12. **Multi-run evaluation of the skills themselves.** Run a toy cycle N times, measure pass rate
    (ADK ran 30 runs/case study). Large; likely a later cycle.

### E. Boundaries
13. **Declared write-scope per dispatch.** Each dispatch names the paths it may write; orchestrator
    diffs `git status` on return and flags out-of-scope writes as a boundary finding.

### F. Adversarial / multi-persona
14. **Red/Blue at verify (opt-in).** An adversarial subagent tries to break acceptance criteria
    before `verification.md` may read pass.
15. **Arbitrated handoff.** If two review rounds contradict each other, stop the ping-pong and hand
    both to the operator.

### G. Linters as teachers, garbage collection
16. **Lint messages carry remediation.** Every `sdd-skill-lint` finding says how to fix it; add
    checks for: fix-loop cap present, budget slot in dispatch templates, verdict-token contract,
    SKILL.md size soft limit, `references/` cross-links resolve.
17. **Drift sweep cadence.** A `sdd-gc` tool/skill that runs lint + staleness + orphan Q-IMPL scan
    across docs/ on a cadence and opens targeted fix tasks.

## Recommended scope for this cycle (v5: "harness hardening")

In: A1–A4, B5–B7, C8–C10, E13, G16.  Defer: D11 (design question first), D12, F14, F15, G17.

## Next cycle — starting prompt (saved for later)

Run after the v5 "harness hardening" cycle is DONE, as a **new SDD cycle** (or a new
workstream if the repo has moved to marker 4 by then). Paste into `/sdd-orchestrate`:

> Start a new SDD cycle: "harness hardening, part 2". Upstream context: the idea
> catalogue at `docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md`
> (deferred items D11, D12, F14, F15, G17) and the completed v5 cycle's specs. Scope:
> (1) per-dispatch telemetry in a gitignored `.sdd/telemetry.jsonl`, designed so it is
> not a loop-position marker; (2) opt-in Red/Blue adversarial pass at the verify stage;
> (3) arbitrated handoff when two review rounds contradict; (4) `sdd-gc` drift-sweep
> tool (lint + staleness + orphan Q-IMPL) with a cadence; (5) multi-run evaluation of
> the sdd skills on a toy project (pass-rate telemetry, ADK-style 30 runs). Research
> first: reuse `docs/research/RS-008-*` findings; do not repeat them.
