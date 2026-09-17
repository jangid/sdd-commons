---
domain: EVAL
last_updated: 2026-09-17
status: Approved
research_refs: [RS-HARNESSP2-001, RS-006]
workstream: harness-p2
---

# Requirements: Multi-Run Evaluation

## Overview

Multi-run evaluation of the SDD skills on a toy project (idea catalogue item
D12 — ADK-style N runs with pass-rate telemetry). RS-HARNESSP2-001 Q5 returned
a **no-go** for building an N = 30 evaluation harness this cycle and a **go**
for three smaller things: telemetry fields chosen with the scorer in mind
(TELEM domain), a requirement that defines what an evaluation mode would be,
and a **manual N = 3 pilot** run by the orchestrator after telemetry lands.
The blockers are structural, not effort: there is nothing to measure until
telemetry exists; a canned gate policy is exactly the auto-advance REQ-ORCH-011
prohibits, and an evaluation-mode carve-out to REQ-ORCH-011 is **not adopted**
this cycle; and an N-run outer loop must dispatch the orchestrator N times,
which only a human (or a headless driver this repo has never verified) can do —
a dispatched subagent has no dispatch tool (RS-006 Q1).

## Requirements

### REQ-EVAL-HARNESSP2-001: Evaluation mode is defined, not built — REQ-ORCH-011 unamended
An **evaluation mode** for the orchestrator is defined as: opt-in per run;
permitted only on a toy repository (one whose `CLAUDE.md` declares
`sdd-eval-toy: true`); gates decided by a canned policy that is a pure function
over the v5 tokens — `proceed` on `VERDICT: APPROVE ∧ SCOPE: CLEAN ∧
CHUNK_VERDICT: PASS` (∧ `RED_VERDICT: HELD` when red is on); `fix` on
`APPROVE_WITH_FIXES` or `REJECT`-with-findings while `iteration < FIX_LOOP_MAX`;
`stop` on any pause (`MALFORMED`, `VIOLATION`, `CONTRADICTION`, no actionable
findings, cap exhausted, replan trigger) — with every policy decision recorded
as `gate.decision_by: policy` in telemetry (REQ-TELEM-HARNESSP2-001). This
cycle records the definition only: **no skill may implement the policy**,
REQ-ORCH-011 ("must not auto-advance without an operator decision") and the
`sdd-orchestrate` Rules ("never auto-advance") stay unamended, and every gate in
every run — including the pilot of REQ-EVAL-HARNESSP2-003 — is decided by the
operator (`gate.decision_by: operator`). Adopting the mode is a future
requirements decision that must amend REQ-ORCH-011 explicitly. (see
RS-HARNESSP2-001 Q5 canned gate policy; Implications for Design)
**Acceptance**: `grep -rn 'decision_by' skills/` matches only the telemetry
schema in `sdd-orchestrate/references/telemetry.md`; `sdd-orchestrate/SKILL.md`
§Rules still contains the never-auto-advance sentence; no telemetry record
written this cycle has `decision_by: policy`.
[Priority: must]

### REQ-EVAL-HARNESSP2-002: Scorer fields are fixed so telemetry can feed them
The evaluation scorer — a future stdlib-only `tools/sdd-eval.py` reading
`.sdd/telemetry.jsonl` plus the toy's final artifacts — must compute, per run
and aggregated over N runs: first-attempt pass rate (`verification.md`
`status: pass` with zero verify-stage fix iterations); mean fix iterations per
stage; `SCOPE: VIOLATION` rate per dispatch; `MALFORMED` rate per dispatch;
dispatches per chunk (implement + verifier + redo + fix, RS-008 probe 1);
`CONTRADICTION` pauses per run; red `BROKEN` findings per run; self-reported
tool calls per run against budget; and wall time per dispatch and per run.
Every one of these must be derivable from the TELEM record key set alone plus
the `status` line of `verification.md`; `sdd-specs` must check the TELEM schema
against this list, and any scorer field that is not derivable is a TELEM schema
defect, not a scorer limitation. The scorer's field list is in scope this cycle;
the scorer's implementation may ship this cycle if the plan has room and must
otherwise be queued in `verification.md` §Next Steps. (see RS-HARNESSP2-001 Q5
scorer; Q1 "fields chosen with the scorer in mind")
**Acceptance**: the telemetry spec contains a "scorer derivation" table mapping
each field above to record keys; a six-record fixture yields every field
without reading any artifact other than `verification.md`'s `status`.
[Priority: must]

### REQ-EVAL-HARNESSP2-003: Manual N = 3 pilot on the toy, after telemetry lands
After telemetry is implemented (plan ordering: TELEM first), the operator should
run **three manual orchestrated cycles** on the toy project — the
`tools/sdd-scope-check-selftest.py` `make_repo()` shape (`src/recon/engine.py`,
`tests/test_recon.py`) plus one requirement, one spec with two acceptance
criteria, a two-chunk plan and a `CLAUDE.md` naming `pytest -q` as the gate —
entering at plan (REQ-ORCH-031..033) or at research for at least one run, with
every gate operator-decided. The pilot's results (the scorer fields of
REQ-EVAL-HARNESSP2-002, computed by `tools/sdd-telemetry.py summarize` or by
hand from the records) must be recorded as a dogfooding probe in this cycle's
`verification.md`, alongside RS-008 probes 1 and 2, and must state observed
wall time per run (the first timing data the harness has ever had). N = 3 is
the pilot's size because ~1k tool calls fits one operator session; the pilot
is a **verify task**, not an implement task. The pilot's telemetry records
live in the **toy repository's own** `.sdd/telemetry.jsonl` (one file per
repository, REQ-TELEM-HARNESSP2-004) — this repository's telemetry file gains
no pilot record — and are summarized **by hand** into harness-p2's
`verification.md`. The pilot may run this cycle if the plan has room and must
otherwise be queued in `verification.md` §Next Steps — the same deferral
REQ-EVAL-HARNESSP2-002 grants the scorer implementation (Q-REQ-F in
`index.md`). (see RS-HARNESSP2-001 Q5 go/no-go; cost estimate)
**Acceptance**: either `docs/ws/harness-p2/verification.md` contains a "Pilot
(N = 3)" section with three run rows, each with pass-on-first-attempt, fix
iterations, dispatch count, tool calls and wall time, and the toy repository's
`.sdd/telemetry.jsonl` holds the three runs' records; or `verification.md`
§Next Steps carries the pilot as a queued item naming this requirement.
[Priority: should]

### REQ-EVAL-HARNESSP2-004: N = 30 headless evaluation harness is out of scope this cycle
An automated N ≥ 30 evaluation harness must **not** be built this cycle. The
blocking conditions, each of which must be resolved by a later cycle before the
harness is in scope, are: (a) **telemetry first** — the TELEM domain must be
shipped and the N = 3 pilot recorded so there is a baseline to measure against;
(b) the **evaluation-mode carve-out to REQ-ORCH-011** must be explicitly
adopted by a requirements decision (it is not adopted now,
REQ-EVAL-HARNESSP2-001); (c) the outer N-run loop is **orchestrator-only** —
it requires either a human running N sessions or a verified headless driver
that can run `/sdd-orchestrate` non-interactively with the policy gate, which
this repo has not verified and a subagent cannot probe (RS-006 Q1; `index.md`
Open Questions). Until then the pilot is manual-N-only. (see RS-HARNESSP2-001
Q5 go/no-go; Open Question 2)
**Acceptance**: no `tools/sdd-eval-run*` or headless-driver script exists after
this cycle; `index.md` Out of Scope names the harness with the three
conditions; the plan contains no task that dispatches the orchestrator.
[Priority: must]
