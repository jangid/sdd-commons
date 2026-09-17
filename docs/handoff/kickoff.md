---
cycle: harness-hardening-v5
research_id: RS-008
entry_stage: research
date: 2026-09-17
---

# Kickoff: RS-008 — Harness hardening (loop control, decoupled verification, boundaries)

Run `/sdd-research`. This spike de-risks hardening the SDD harness with the
deterministic loop-control and verification patterns from the harness-engineering
literature (Google Cloud / ADK 2.0 case studies, OpenAI harness engineering). Its
findings must land before requirements/specs for the "harness hardening" feature.

Driven by `sdd-orchestrate` (dogfooding). Cycle: this research spike → requirements
→ specs → plan → implement → verify. Repo stays at SDD marker `3` for this cycle.

Converged idea catalogue (approved in DISCUSS):
`docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md`. That doc holds the
source walk-through, the "already covered" table, all 17 ideas, and the agreed scope.
The questions below de-risk only the parts still uncertain.

## Scope in one paragraph (context for the spike)

Add to `sdd-implement` and `sdd-orchestrate` **hard stop conditions**: a max-iteration
guard on the review fix loop (default 3) and on replan re-entries; an explicit budget
slot on every dispatch (observable units); an **attempt ledger** so stuck detection
also fires on oscillation (a fix re-introducing a previously fixed failure, or a
repeated rejected patch); and a structured **checkpoint** written on circuit-break so
a human or fresh session resumes. Decouple verification: a **fresh verifier subagent
at chunk close** under orchestrate, a fixed-shape **repair packet** for fix
re-dispatches (failing tests, clean traceback, spec excerpt, ledger summary), and a
**machine-parseable verdict token** from `sdd-review`. Context hygiene: pruned state
on re-dispatch, orchestrator-owned routing, and moving `sdd-orchestrate/SKILL.md`'s
marker-4 prose into `references/`. Boundaries: a declared **write-scope per dispatch**
checked mechanically on return. Lint: findings carry remediation; new checks for the
above contracts and a soft SKILL.md size limit.

## Research questions

- **Q1 — Where does loop-control state live?** REQ-ORCH-014 forbids a loop-position
  marker; artifacts are the sole resume source. Must the fix-iteration count,
  replan-re-entry count, and attempt ledger persist across sessions (and if so in
  which existing artifact — plan task notes, Q-IMPL entries, kickoff frontmatter), or
  is per-session counting acceptable? Recommend one placement with its resume
  semantics and check it against existing requirements (`docs/requirements/`).
- **Q2 — Fresh verifier at chunk close vs. existing layers.** How does a dispatched
  chunk-close verifier compose with `sdd-implement` Step 4's blocking checklist, the
  implement-stage `sdd-review`, and fan-out leaves (who runs it per worktree)? Is it a
  new layer or a re-homing of Step 4? Identify duplication and the minimal contract.
- **Q3 — Repair packet + ledger shape.** What exact fields must a fix re-dispatch
  carry (test names, traceback, spec excerpt, ledger summary) and how does the
  orchestrator obtain them from a leaf subagent's return today? Propose a schema that
  fits the existing Q-IMPL protocol (`docs/spec/deviation-protocol.md`) and the
  dispatch template (`skills/sdd-orchestrate/references/dispatch-templates.md`).
- **Q4 — Mechanical checks.** Which of the new contracts (fix-loop cap present,
  budget slot in every dispatch template, verdict-token line, `references/`
  cross-links resolve, SKILL.md soft size limit) can `tools/sdd-skill-lint.py`
  check with its current architecture, and what is the SKILL.md size baseline today?
  Which `sdd-orchestrate/SKILL.md` sections are safe to move into
  `references/v4-workstreams.md` without breaking the lint's cross-skill contract
  markers or the marker-4 requirements' wording?
- **Q5 — Write-scope check feasibility.** Is a `git status --porcelain` snapshot
  before/after a dispatch sufficient to detect out-of-scope writes in the main
  workspace and in fan-out worktrees? How are untracked scratch files, index
  updates the skill legitimately makes, and returned-content fallbacks handled?
  Propose the finding format and where it surfaces (gate text only — reviews stay
  ephemeral).

## Success criteria

- Each Q has an answer with a **recommendation** and the evidence/analysis behind it.
- Q1 names one placement and shows it satisfies REQ-ORCH-014 (no new marker).
- Q3 delivers a concrete schema (fields + example) usable verbatim by `sdd-specs`.
- Q4 delivers a table: contract → checkable now / needs lint change / not mechanical,
  plus the current line counts of every `skills/*/SKILL.md`.
- Findings say explicitly which of the 12 in-scope ideas need **no** further research.

## Budget

Analysis-only spike: ~60 tool calls total, roughly 12 per question; no prototypes
beyond reading `tools/sdd-skill-lint.py` and running it. **No live subagent
dispatch** — the research subagent cannot dispatch (RS-006 Q1); if a question turns
out to need a dispatch probe, record it as an open question for the orchestrator to
run, do not attempt it.

## Out of scope (for the spike)

Telemetry file design (D11), multi-run skill evaluation (D12), Red/Blue adversarial
verify (F14), arbitrated handoff (F15), `sdd-gc` drift sweep (G17) — deferred to the
next cycle (prompt saved in the idea catalogue). The v3→v4 migration of this repo.
