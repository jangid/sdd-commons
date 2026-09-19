---
workstream: harness-p4
description: Harness hardening, part 4 — orchestrator commit fidelity, telemetry completeness and validation, live arbitration exercise, tooling and spec housekeeping
cycle: harness-hardening-p4
research_id: RS-HARNESSP4-001
entry_stage: research
date: 2026-09-18
branch: harness-p4
---

# Kickoff: RS-HARNESSP4-001 — Harness hardening, part 4

Run `/sdd-research` for workstream `harness-p4`. This spike settles the two
design questions left open by the harness-p3 cycle; everything else in scope
was decided at DISCUSS on 2026-09-18 and goes straight to requirements.
Findings must land before requirements.

Reuse `docs/research/RS-008-harness-hardening/findings.md`,
`docs/research/RS-HARNESSP2-001-*/findings.md` and
`docs/research/RS-HARNESSP3-001-*/findings.md`; do not repeat them. The
evidence for this cycle lives in `docs/ws/harness-p3/verification.md`
§Next Steps, §Post-DONE Findings (P1–P3) and §Session Learnings (L1–L6).

**Evidence discipline (operator direction, carried from p3).** Pick the option
the evidence supports and say what the evidence was. Where a question has no
evidence, say so and either run the cheap probe or hand the choice to
requirements — never split the difference silently.

**Git integration (operator decision).** This workstream runs on its own
branch `harness-p4` and merges to `main` by PR at DONE. It is the first cycle
to exercise the marker-4 `merge-base(<ws>, main)` regression rule for real.

## Scope in one paragraph

(1) **Orchestrator commit fidelity (V14, lead).** The write-scope check
verifies what a leaf wrote; nothing verifies that the orchestrator committed
what it observed. Three independent findings in p3 (blue: Chunk 7's dropped
`git add`; review C1; red R4) share this root cause. Remedy: at commit time
compare the observed-writes set against the commit's own diff and surface
`COMMIT: COMPLETE | INCOMPLETE (…)` as its own gate signal. (2) **Telemetry
completeness and validation (P2 → P3 → P1, in that order).** Record `verifier`
and `fix` dispatches at all; derive `records-vs-expected`'s `expected` from a
source independent of the record set's own `seq`; validate every field against
its declared domain (`--lint`); only then migrate the 8 mis-typed `chunk`
records in place, stamped partial. The L6 operator-widening record rides with
this item. Tests run against `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`,
never the live file. (3) **Live arbitration exercise.** `REQ-ARB-HARNESSP3-001`
closed p3 as `fail` (not exercised). This cycle exercises it on purpose: the
first `APPROVE_WITH_FIXES` fix loop is directed to regenerate its deliverable
wholesale, and the gate must then not raise a class (b) `REVIEW: CONTRADICTION`
for findings in the regenerated file. (4) **One housekeeping chunk.** Tooling:
V6 (`R`/`C` scope-check fixtures), V7 (observed-writes set semantics), V8
(`[template-drift]` lint rule). Text: R4 (`research_id:` stamp order in
`sdd-plan`/`sdd-verify` vs Q-IMPL-HARNESSP3-014), R6 (V5 wording "on a
`pending-red` cell"), V9 (terminal-token column 0), V10 and V11 (arbitration
fixture and `regen[N]` line), V13 (`CLAUDE.md` completion-row qualifier).

## Research questions

- **Q1 — `COMMIT:` signal under fan-out (evidence: V14, sequential only).**
  In sequential mode the orchestrator commits on `proceed`, so `COMMIT:`
  compares the observed-writes set plus `files_written` against
  `git show --name-only --format= HEAD`. Under fan-out the leaf commits on its
  own branch and the orchestrator merges. What does `COMMIT:` compare against
  at the per-leaf gate (the leaf's `commits` list vs its observed writes?) and
  at the merge step (the merge commit's diff vs the union?). Does the signal
  need a third member for a merge that silently dropped a path, or does
  `INCOMPLETE` cover it? Where in the `loop-control.md` §5 signal order does
  it render — after `SCOPE:` seems right, confirm. Cost in files touched.

- **Q2 — Independent `expected` source (evidence: P2, strong, negative).**
  `records-vs-expected` derives `expected` from the highest `dispatch.seq`, so
  a writer that never appends and never increments reports no gap; zero
  `verifier` and zero `fix` records exist across a cycle that ran 8 verifiers
  and 3 redos. What durable, orchestrator-independent count of dispatches can
  `expected` be derived from without adding a loop log or any new artifact
  under `docs/` (no-new-artifact invariant)? Candidates: the plan's chunk
  count times the per-chunk dispatch shape (pipeline + verifier, plus redos
  from `Redo: N`); git commits between `head_before` and `head_after`; the
  gate blocks the operator saw (not durable). Say which is checkable
  post-cycle by `sdd-telemetry.py summarize` and what it can and cannot detect.

## Decided at DISCUSS (not research — requirements inherit these)

- Migration of the 8 records is in place on the live `.sdd/telemetry.jsonl`,
  stamped partial, after P2 and P3 land; the frozen fixture is never touched.
- REQ-ARB is exercised by directing the first `APPROVE_WITH_FIXES` fix loop of
  this cycle to regenerate its deliverable wholesale.
- DONE rule: every traced requirement `pass`; nothing closes as a deliberate
  `fail`. An item that cannot be exercised live is descoped at replan.
- Scope priority for the plan is the order in §Scope, so a `stop` partway
  leaves V14 and telemetry landed first.

## Success criteria

- Q1 and Q2 each answered with a recommendation, its evidence, and the cost
  in files touched; each classified mechanical (spec/template text), code
  (`tools/*.py`), or design-decision-for-requirements.
- Q2 states explicitly which failure modes the recommended `expected` source
  detects and which it still cannot.
- The findings restate the §Decided list unchanged so requirements sees one
  bounded scope.

## Budget

One spike, ≤ 30 tool calls. Desk research over the existing specs, references
and tools. A probe for Q1, if needed, runs in a scratch git repository under
`$TMPDIR`, never against this repository's working tree.

## Out of scope

- L2 (cross-layer convergence as a gate signal) and its research question —
  deferred to harness-p5; no evidence yet on what the signal should look like.
- Re-opening anything settled by RS-008, RS-HARNESSP2-001 or RS-HARNESSP3-001.
- Touching `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`.
- Any change that adds a durable artifact type under `docs/`, or that lets
  telemetry, reviews or red findings influence phase detection.
- Marker-3 behaviour: unchanged this cycle.
