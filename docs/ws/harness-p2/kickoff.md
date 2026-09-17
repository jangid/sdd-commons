---
workstream: harness-p2
description: Harness hardening, part 2 — telemetry, adversarial verify, arbitrated handoff, drift sweep, multi-run evaluation
cycle: harness-hardening-p2
research_id: RS-HARNESSP2-001
entry_stage: research
date: 2026-09-17
---

# Kickoff: RS-HARNESSP2-001 — Harness hardening, part 2

Run `/sdd-research` for workstream `harness-p2`. This spike de-risks the five
harness-engineering ideas deferred from the v5 cycle (idea catalogue
`docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md`, items D11, D12,
F14, F15, G17) plus the follow-ups queued by the v5 verification
(`docs/ws/default/verification.md` §Next Steps). Findings must land before
requirements/specs. Reuse `docs/research/RS-008-harness-hardening/findings.md`; do
not repeat it.

Driven by `sdd-orchestrate` under marker `4`: this is the **first orchestrated run
under the v5 harness**, so it doubles as the live measurement of the two RS-008
dogfooding probes (per-chunk dispatch cost; write-scope false-positive rate).

## Scope in one paragraph

(1) **Per-dispatch telemetry** in a gitignored `.sdd/telemetry.jsonl` — stage, wall
time, `budget_consumed`, verdict, fix iterations, scope findings, replan triggers —
designed so it can never act as a loop-position marker (REQ-ORCH-014) and never
becomes a new artifact under `docs/` (REQ-HARN-027). (2) An **opt-in Red/Blue
adversarial pass at the verify stage**: an adversarial subagent tries to break the
acceptance criteria before `verification.md` may read `pass`. (3) **Arbitrated
handoff**: when two consecutive review rounds contradict each other, the loop
stops ping-ponging and hands both verdicts to the operator. (4) An **`sdd-gc`
drift-sweep tool** running lint + staleness + orphan Q-IMPL + stale cross-links
across `docs/` on a cadence, opening targeted fix tasks. (5) **Multi-run
evaluation** of the sdd skills on a toy project (ADK-style N runs, pass-rate
telemetry). Plus the queued follow-up: split `sdd-implement/SKILL.md` Step 3 detail
and the leaf return contract into `references/` (Q-IMPL-083).

## Research questions

- **Q1 — Telemetry without a marker.** What record shape and writer (orchestrator
  only) let `.sdd/telemetry.jsonl` capture per-dispatch facts while phase detection
  provably never reads it? Where does `.sdd/` sit relative to the no-new-artifact
  invariant and `.gitignore`? What does the v5 gate already expose for free
  (`RETURN.budget_consumed`, `SCOPE:`, `CHUNK_VERDICT:`, `VERDICT:`)?
- **Q2 — Red/Blue at verify.** How does an adversarial subagent compose with
  `sdd-verify` (holistic) and `sdd-review` (REQ-REV-005/006 — never the verifier)?
  What is its input contract (acceptance criteria + repo, read-only), its return
  (`RETURN:` + findings), and its exit rule (verification `pass` only when both
  gates hold and the red findings are resolved or accepted)?
- **Q3 — Arbitrated handoff.** How does the orchestrator detect that review round
  N+1 contradicts round N (same finding id flipped, or a new Critical that round N
  approved)? What gate text and options result, and how does it interact with
  `FIX_LOOP_MAX`?
- **Q4 — `sdd-gc` mechanics.** Which sweeps are mechanically checkable today with
  `tools/sdd-skill-lint.py` and the staleness rules (spec/requirement dates, orphan
  Q-IMPL ids, dead `references/` and `docs/spec` pointers, empty traceability
  cells), what cadence mechanism fits (a tool invoked at cycle DONE vs. a scheduled
  routine), and what does "open targeted fix tasks" mean without a new artifact type?
- **Q5 — Multi-run evaluation feasibility.** What is the smallest toy project and
  harness that can run N orchestrated cycles non-interactively (gates need an
  operator — can a canned policy stand in?), what does one run cost, and is this an
  orchestrator-only task (dispatch-requiring) or a tool?
- **Q6 — Probe measurements (this cycle).** Record, for every dispatch in this
  cycle, the dispatch count per chunk and every `SCOPE:` finding; report the two
  probe values against the plan's replan triggers from the v5 cycle.

## Success criteria

- Q1–Q5 each end in a recommendation with evidence; Q1 names the record fields and
  proves non-interference with phase detection by citing the detection inputs.
- Q4 delivers a table: sweep → checkable now / needs code / not mechanical.
- Q5 gives a go/no-go with a cost estimate; a no-go is an acceptable finding.
- Q6 is filled from this cycle's own dispatches, never simulated.
- Findings say which of the five ideas need **no** further research.

## Budget

Analysis-only: ~70 tool calls, ~12 per question; no live subagent dispatch (record
dispatch-requiring probes for the orchestrator). Early-exit is allowed per question
when RS-008 or the shared corpus already answers it.

## Out of scope

Any marker bump (the layout stays at `4`); changes to the shared corpus beyond
adding new IDs; re-doing RS-008.
