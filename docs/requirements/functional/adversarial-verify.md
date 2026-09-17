---
domain: REDB
last_updated: 2026-09-17
status: Approved
research_refs: [RS-HARNESSP2-001, RS-008]
workstream: harness-p2
---

# Requirements: Adversarial (Red/Blue) Verify

## Overview

An opt-in **Red/Blue** pass at the verify stage of the orchestrated loop (idea
catalogue item F14, de-risked by RS-HARNESSP2-001 Q2). **Blue** is `sdd-verify`
itself — confirmatory, "walk every acceptance criterion". **Red** is a third
dispatch kind at the verify stage (`red`), orchestrator-dispatched, read-only,
told to pick the weakest acceptance criteria and construct inputs or commands
that violate them. Red is positioned exactly as the chunk verifier was in RS-008
(REQ-HARN-014): a **second executor of `sdd-verify` Steps 3–4 in adversarial
mode**, not a fifth verification layer and **never `sdd-review`** — an
adversarial break attempt is behavioral work in verify's territory (REQ-REV-006
(c)), and `sdd-review`'s post-verification trigger stays a semantic read of the
report (REQ-REV-005 (b)).

Standing constraints: REQ-REV-005/006 (review is never the verifier), REQ-ORCH-011
(the gate decision stays with the operator), REQ-ORCH-013 (red's report is
ephemeral gate text), REQ-HARN-024 (red never commits), REQ-HARN-027 (no new
artifact — accepted breaks land in `verification.md`'s existing §Issues Found).
`sdd-verify`'s own rules — "don't fix during verify", "run, don't read" — apply
to red unchanged.

## Requirements

### Positioning

### REQ-REDB-HARNESSP2-001: Red is an opt-in third dispatch kind at the verify stage
The orchestrator must offer a red dispatch as an **opt-in at the verify gate**
(the same opt-in device as implement-stage fan-out, REQ-ORCH-024), **default
off**. When selected, red is dispatched after the verify pipeline returns and
before the stage's review, as a context-isolated subagent of kind `red`
(REQ-TELEM-HARNESSP2-001 `dispatch.kind`). Red must never run at chunk close
(it needs the whole system) and must never be dispatched at any stage other
than verify. (see RS-HARNESSP2-001 Q2; decisions deferred to requirements: red
default off)
**Acceptance**: the verify gate shows `red team: off | on` before the verify
pipeline is dispatched, defaulting to `off`; with `off` no `red` record appears
in telemetry and the gate is unchanged from v5; with `on` exactly one `red`
dispatch precedes the verify-stage review.
[Priority: must]

### REQ-REDB-HARNESSP2-002: Red is a second executor of `sdd-verify`, never `sdd-review`
Red must be specified as an adversarial second executor of `sdd-verify` Steps
3–4 (acceptance-criteria walkthrough and user-perspective behavior): its
checklist is the specs' `## Acceptance Criteria`, its method is to attempt to
violate them. It must not be implemented by, or as a mode of, `sdd-review`
(REQ-REV-005, REQ-REV-006 (c)), and the four-verification-layer table
(`sdd-verify` §Verification Layers, `CLAUDE.md`) must remain unchanged — red is
an executor of the sdd-verify layer as the chunk verifier is an executor of the
chunk-close layer (REQ-HARN-014). Standalone `sdd-verify` (no orchestrator) is
unchanged except for the `pending-red` input of REQ-REDB-HARNESSP2-008. (see
RS-HARNESSP2-001 Q2 layering evidence)
**Acceptance**: the red template lives in
`skills/sdd-orchestrate/references/dispatch-templates.md` and names
`sdd-verify` Steps 3–4 as the checklist source; `skills/sdd-review/SKILL.md` is
not modified for red; `CLAUDE.md`'s four-layer bullet diff is empty.
[Priority: must]

### Contract

### REQ-REDB-HARNESSP2-003: Red is read-only and never commits
The red dispatch must carry `Write scope: (empty — read-only)` and `Commit
ownership: you never commit` (REQ-HARN-020, REQ-HARN-024). A reproducible break
is a command line or test id in the return text, never a committed test or a
written file; any observed write by red is `OUT` and is reverted by the
orchestrator before the gate (the chunk verifier's rule). (see RS-HARNESSP2-001
Q2 return contract)
**Acceptance**: the red template contains both slots verbatim; a fixture in
which red writes `tests/test_break.py` yields `SCOPE: VIOLATION (1 paths)` and
the file is absent at the gate.
[Priority: must]

### REQ-REDB-HARNESSP2-004: Red input contract — acceptance criteria plus repository, paths only
The red dispatch prompt must contain, as paths and slots only (mirroring the
REVIEW and CHUNK VERIFIER templates): the repository root (under
`docs/.sdd-version` == `4`, the workstream branch checkout); the spec paths (red
reads `## Acceptance Criteria` itself); the plan path; the quality-gate commands
from `CLAUDE.md`; `Budget:` (default `≤ 25 tool calls, ≤ 3 test runs,
read-only`, REQ-HARN-004); the empty write scope and commit-ownership slots;
and the non-interactive clause. `verification.md` (blue's evidence) must be
**withheld by default** — reading blue's evidence anchors red on what was
already checked (the reviewer-isolation argument) — with an operator override
`red input: +verification.md` at the gate; whether the override finds more
breaks is the live A/B logged in `index.md` Open Questions. (see
RS-HARNESSP2-001 Q2 input contract; Open Question 1)
**Acceptance**: the red template lists exactly the inputs above and no
`verification.md` path unless the override is set; a fixture prompt is
inspected to contain no finding text and no blue evidence.
[Priority: must]

### REQ-REDB-HARNESSP2-005: Red return contract with own-line `RED_VERDICT:`
Red's return text must consist of, in order: a heading `## Red team — <spec.md>
acceptance criteria` per spec examined; one line per attempted criterion in
the fixed shape `- Rn: <criterion text> — attack: <what was tried> — observed:
<one line> — reproduce: \`<command or test id>\` — BROKEN | HELD`; the standard
leaf `RETURN:` block (REQ-HARN-009) whose `failures[]` holds exactly one entry
per `BROKEN` line with `test` = the reproduce command, `kind` ∈ {assertion,
error, lint, type, build}, `message` and `location`; and, last, the own-line
token `RED_VERDICT: BROKEN | HELD`, where `BROKEN` iff `failures[]` is
non-empty. The orchestrator must branch on `^RED_VERDICT:` (the `CHUNK_VERDICT`
precedent, REQ-HARN-014) and must treat `HELD` with non-empty `failures[]`,
`BROKEN` with empty `failures[]`, a missing token, or a token not on the last
line as `RETURN: MALFORMED` (REQ-HARN-009 handling). The token is red-only: its
presence in any other dispatch's return is a warning at the gate. Lint carries
the producer/consumer pair (REQ-LINT-HARNESSP2-001). (see RS-HARNESSP2-001 Q2
return contract)
**Acceptance**: a red return with two `BROKEN` lines and two `failures[]`
entries ending in `RED_VERDICT: BROKEN` is parsed as BROKEN with two findings;
the same return with `RED_VERDICT: HELD` is surfaced as `RETURN: MALFORMED`;
removing the token from the template makes `tools/sdd-skill-lint.py` exit 1.
[Priority: must]

### REQ-REDB-HARNESSP2-006: A break counts only when it is reproducible
A red finding may be `BROKEN` only when its `reproduce:` field is a command or
test id that the orchestrator or operator can run in the repository and that
demonstrates the violated criterion; a claim without a reproducible command is
**advisory** and must be reported as `HELD` with `observed:` describing the
suspicion — it must not enter `failures[]`, must not affect `RED_VERDICT`, and
must not gate the pass commit. (see RS-HARNESSP2-001 Q2 "must be reproducible")
**Acceptance**: the red template states the rule in its Rules section; a return
line with `reproduce: n/a` and `BROKEN` is treated as malformed.
[Priority: must]

### Exit rule

### REQ-REDB-HARNESSP2-007: Red gates the `pass` commit at the verify stage gate
At the verify stage gate the orchestrator must render `RED_VERDICT:` after the
`SCOPE:` block and before the review `VERDICT:` (extending the REQ-ORCH-034
signal order), followed by red's `Rn` lines verbatim. `proceed` (→ DONE, which
commits `verification.md`) may be offered **only if** `VERDICT ≠ REJECT` **and**
(red was not run, or `RED_VERDICT: HELD`, or every `BROKEN` `Rn` has been
resolved). Per `BROKEN` finding the options are `fix (RED_BREAK packet)` │
`accept (record)` │ `stop`. `accept` makes the orchestrator append one line
under `verification.md` §Issues Found → Minor in the shape `- Rn accepted at
gate <date>: <observed> — reproduce: \`<cmd>\`` — orchestrator bookkeeping in an
existing section of an existing artifact (REQ-HARN-027), the same device as
fan-out §3e plan marks — and no `docs/reviews/`-like store is created
(REQ-ORCH-013). The decision remains the operator's (REQ-ORCH-011). (see
RS-HARNESSP2-001 Q2 exit rule)
**Acceptance**: a gate fixture with `RED_VERDICT: BROKEN` (R1) and `VERDICT:
APPROVE` offers no `proceed` until R1 is fixed or accepted; after `accept`,
`verification.md` §Issues Found → Minor contains the R1 line and `proceed` is
offered; no file under `docs/` other than `verification.md` changes.
[Priority: must]

### REQ-REDB-HARNESSP2-008: `status: pending-red` — `pass` never sits on disk while red is pending
When red is enabled for the cycle, the verify pipeline dispatch must tell
`sdd-verify` so (a `Red team: enabled` slot in the pipeline template), and
`sdd-verify` Step 6 must then write `status: pending-red` instead of `pass`
whenever its own result would have been `pass` (a `fail` is written as `fail`
unchanged). The orchestrator flips `pending-red` to `pass` — and only then
commits `verification.md` — when the exit rule of REQ-REDB-HARNESSP2-007 is
satisfied; if red is not run after all, it flips it likewise at the gate. Phase
detection in `sdd-verify`, `sdd-replan` and `sdd-orchestrate` must treat
`pending-red` as "verification incomplete — re-enter the verify stage" (never
as DONE, never as needs-replan), so a session re-entering with an uncommitted
or committed `pending-red` on disk cannot detect DONE. **Decision recorded**:
RS-HARNESSP2-001 Q2 stated commit ownership alone as its default and named
`pending-red` "the safer choice"; this cycle adopts `pending-red` because the
operator's success criterion is that `verification.md` must not read `pass` on
disk while red is pending, which commit ownership alone cannot guarantee across
sessions. Commit ownership (REQ-HARN-024) still holds as the second guard. Under
marker `3` and with red off, `sdd-verify` behavior is unchanged. (see
RS-HARNESSP2-001 Q2 Confidence; decisions deferred to requirements)
**Acceptance**: with red enabled, `docs/ws/<id>/verification.md` never contains
`status: pass` between the verify pipeline's return and the gate's `proceed`;
`sdd-orchestrate`'s position table maps `pending-red` to the verify stage;
`sdd-verify` Phase Detection lists `pending-red` as a re-verification state;
with red off, a diff of `sdd-verify` Step 6 output against v5 is empty.
[Priority: must]

### REQ-REDB-HARNESSP2-009: Fix-loop interaction of a `BROKEN` red result
A `BROKEN` finding routed to `fix` must produce an **implement**-stage repair
packet with `reason: RED_BREAK`, `failures` ← red's `RETURN.failures`, and the
chunk resolved via the finding → chunk mapping of `return-contract.md` §5
(REQ-HARN-011), followed by the scope check, the chunk verifier and a
re-dispatch of the verify pipeline, which regenerates `verification.md` from
evidence (`sdd-verify` re-verification). One red round consumes at most **one**
fix iteration of the **verify** stage's counter (REQ-HARN-001; `FIX_LOOP_MAX`
is the backstop). After the re-verify the orchestrator re-runs red **once** by
default; that re-dispatch is not an iteration (the verifier re-dispatch rule),
and a second red re-run requires an explicit operator choice. (see
RS-HARNESSP2-001 Q2 fix-loop interaction)
**Acceptance**: a `RED_BREAK` packet fixture names the implement chunk and
carries `failures[]` verbatim; the verify gate after the fix shows `iteration 1
of 3` and a fresh `RED_VERDICT:`; three `BROKEN` rounds exhaust the cap and
render the compiled log (REQ-HARN-001) with no fourth automatic dispatch.
[Priority: must]
