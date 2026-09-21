---
domain: REDB
last_updated: 2026-09-18
status: Approved
research_refs: [RS-HARNESSP2-001, RS-008, RS-HARNESSP3-001, RS-HARNESSP4-001]
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
dispatch **per verify-pipeline return** precedes the verify-stage review — a
re-verify after a `BROKEN` fix is a new return and gets its own single red
re-run (REQ-REDB-HARNESSP2-009).
[Priority: must]

### REQ-REDB-HARNESSP2-002: Red is a second executor of `sdd-verify`, never `sdd-review`
Red must be specified as an adversarial second executor of `sdd-verify` Steps
3–4 (acceptance-criteria walkthrough and user-perspective behavior): its
checklist is the specs' `## Acceptance Criteria`, its method is to attempt to
violate them. It must not be implemented by, or as a mode of, `sdd-review`
(REQ-REV-005, REQ-REV-006 (c)), and the four-verification-layer table
(`sdd-verify` §Verification Layers, `CLAUDE.md`) must remain unchanged — red is
an executor of the verify layer as the chunk verifier is an executor of the
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

### REQ-REDB-HARNESSP3-001: Red breaks map to a chunk from `failures[].location` before the whole-plan fallback
`references/return-contract.md` §5 must gain a step 1' to its red entry: if the
routed `Rn`'s `failures[].location` names a file or chunk, resolve it to the
chunk whose tasks' implementation modules include it; **otherwise** fall back to
the spec named in the `## Red team — <spec.md>` heading and continue at step 2
as today. The whole-plan fallback stays the rule — this only narrows the input,
using evidence red already returns: the red template is given the plan for
exactly that purpose ("supplies the `### Chunk N:` vocabulary red uses in
`failures[].location`"). Asking red to name the narrowest owning symbol as a new
field on `Rn` is **declined**: that makes the read-only adversarial leaf judge
code ownership, which REQ-HARN-019 / REQ-ORCH-012 keep out of leaves, and it
widens red's return shape for a mapping the orchestrator can do from `location`.
(see RS-HARNESSP3-001 Q5(a) — spec-read: §5 step 4 produces `all` whenever a
spec is traced by more than one chunk, and §B4 observed both breaks landing as
`target.chunk: all` on a small plan; the narrowing step itself is constructed
and unexercised, but it cannot regress anything — it inserts a more specific
resolution ahead of an unchanged fallback)
**Acceptance**: `references/return-contract.md` §5's red entry lists step 1'
ahead of the heading-spec step, and `docs/spec/harness-return-contract.md` plus
`docs/spec/adversarial-verify.md` §Fix-Loop Interaction carry the same rule; a
fixture `Rn` whose `failures[].location` names a file owned by one chunk routes
a `RED_BREAK` packet with `target.chunk: <that chunk>`, and a fixture with no
usable `location` still routes `target.chunk: all`.
[Priority: must]

### REQ-REDB-HARNESSP3-002: The verify gate distinguishes a new-ground red break from a regression
On a red round N >= 2, for each `BROKEN` `Rn` the orchestrator must re-run the
**previous round's** routed `reproduce:` command (it holds those lines verbatim)
and render one derived line under the `RED_VERDICT:` token:

```
RED: R1 new-ground (prior R6 reproduce now passes)
RED: R1 regression  (prior R6 reproduce still fails)
```

The line is **derived in the orchestrator from evidence**; no
`supersedes:` / `new-ground:` marker is added to red's return shape. That
alternative is **declined** because it would require handing red the previous
round's findings, contradicting the withholding default
(REQ-REDB-HARNESSP2-004) which §B3 shows works — red found the weakest criterion
without blue's report — and because re-attacking the same criterion is what
found the second bug, so red must not be steered away from it. The rule costs
one command per prior break and changes neither red's return shape nor its
isolation. (see RS-HARNESSP3-001 Q5(b) — **medium confidence: observed gap,
constructed remedy**. §B7 directly records the operator making this distinction
by hand with no gate vocabulary for it; the proposed derived line has **no run
evidence** and is the weakest-evidenced recommendation of this cycle. Carried as
an open question with a named place to exercise it: the first harness-p3 verify
stage with `red team: on` and a second round)
**Acceptance**: `docs/spec/adversarial-verify.md` §Verify-Stage Gate shows the
derived `RED:` line in its gate block with the re-run rule stated, and
`skills/sdd-orchestrate/SKILL.md` §The gate names its position in the signal
order; a two-round walkthrough in which the prior `reproduce:` now passes
renders `new-ground`, and one in which it still fails renders `regression`;
red's `RETURN:` key set is unchanged between the two rounds.
[Priority: must]

### REQ-REDB-HARNESSP3-003: The traceability `Verified` column reads `pending-red` while a red round is outstanding
The `Verified` column tracks the **report's** status. When `sdd-verify` writes
`status: pending-red` it must write `pending-red` into the `Verified` cell of
every row it would otherwise have marked `pass` (a `fail` row stays `fail`), and
the orchestrator's **existing** `pending-red -> pass` flip at DONE must flip
those cells in the same bookkeeping step and regenerate the aggregate. One
writer per state, no new artifact, and a cycle the operator stops leaves the
durable matrix reading `pending-red` rather than asserting a falsehood.
`docs/spec/ws-traceability.md` must name `pending-red` as a legal `Verified`
value beside `pass` and `fail`. No code consequence: `tools/sdd-gc.py`'s
`trace-empty` sweep flags only empty `Spec` cells and Implementation-filled /
Test-empty rows and does not constrain the `Verified` cell's vocabulary
(verified by reading the sweep). (see RS-HARNESSP3-001 Q5(c) — spec-read and
observed: §B9 recorded both the per-ws and the aggregate matrix carrying
`Verified: pass` inherited from a superseded report while `verification.md` read
`pending-red`; `sdd-verify` Step 3b says only "pass/fail" and
`adversarial-verify.md`'s `pending-red` lifecycle flips frontmatter only)
**Acceptance**: `docs/spec/adversarial-verify.md` §`status: pending-red` and
`skills/sdd-verify/SKILL.md` Step 3b / Step 6 instruct the `pending-red` cell
write, and `docs/spec/ws-traceability.md` lists the three legal cell values; a
walkthrough where red returns `BROKEN` leaves every would-be-`pass` row reading
`pending-red` in both the per-ws file and the regenerated aggregate, and the
DONE flip turns exactly those cells to `pass` while `fail` rows are untouched;
`python3 tools/sdd-gc.py --report` raises no new finding on a `pending-red`
cell.
[Priority: must]
> **Amended by REQ-REDB-HARNESSP4-001** (2026-09-18, workstream `harness-p4`):
> the gc criterion reads "no new finding **on a `pending-red` cell**"; the
> `[traceability-aggregate]` warning between a per-ws write and the
> orchestrator's regeneration is the designed handshake, not a finding.

### REQ-REDB-HARNESSP3-004: A post-cycle fix with no open chunk is recorded in the plan's `## Post-cycle Fixes` section
When a verify-stage `RED_BREAK` fix belongs to no open chunk, it must be
recorded as one line per fix under a `## Post-cycle Fixes` section of the
**active plan** — orchestrator-owned bookkeeping in the same class as the
`fan-out.md` §3e plan marks — and that section must be named in the implement /
`RED_BREAK` default write scope so the write is tagged `IN` rather than
unscoped. Because `## Post-cycle Fixes` is a **new plan section**, the
plan-structure contract that defines a plan's sections must record it:
`skills/sdd-plan/SKILL.md`'s plan template (and `docs/spec/harness-*`'s plan
structure where it restates that template) must list the section as optional,
orchestrator-owned, and outside the task list, so `sdd-plan` / `sdd-replan` do
not strip it on rewrite and `sdd-implement` does not read it as tasks. This specifies the section a leaf invented ad hoc on 2026-09-18; the
behaviour worked, and specifying it costs less than leaving it to be
re-invented. It is not a plan task and does not re-open the plan's task list.
(see RS-HARNESSP3-001 Q8-IN row 1, §B5 — observed gap with a constructed remedy)
**Acceptance**: `docs/spec/adversarial-verify.md` names `## Post-cycle Fixes`
with its one-line-per-fix format and its orchestrator ownership, and the
implement / `RED_BREAK` row of `references/write-scope.md` §2 names the plan
path so the write is `IN`; `skills/sdd-plan/SKILL.md`'s plan template lists
`## Post-cycle Fixes` as an optional orchestrator-owned non-task section and a
plan rewrite preserves it; a `RED_BREAK` fix dispatched with no open chunk
yields `SCOPE: CLEAN` and one new line under that section.
[Priority: should]

### REQ-REDB-HARNESSP4-001: the gc criterion for `pending-red` cells names the aggregate handshake as expected
The acceptance criterion inherited from REQ-REDB-HARNESSP3-003 — that
`tools/sdd-gc.py --report` raises no new finding when `Verified` cells hold
`pending-red` — must read "no new finding **on a `pending-red` cell**" wherever
it is stated (`docs/spec/adversarial-verify.md`, `docs/spec/ws-traceability.md`
§Legal `Verified` Cell Values and `skills/sdd-verify/SKILL.md` Step 3b/6), and
must name the `[traceability-aggregate]` warning that legitimately appears
between a per-workstream traceability write and the orchestrator's post-gate
regeneration (REQ-WS-HARNESSP3-001) as the **designed handshake**, not a
finding. In p3 the criterion's bare "no new finding" made an honest verify
record read as a near-failure: gc raised zero findings on the 17 live
`pending-red` cells but one expected aggregate warning, which the criterion's
wording did not admit. Needs a spec-amending cycle. (workstream `harness-p4`; see
`docs/ws/harness-p3/verification.md` §V5 and §Next Steps R6 — accepted at the
verify gate)
**Acceptance**: `grep -rn 'pending-red' docs/spec/adversarial-verify.md docs/spec/ws-traceability.md skills/sdd-verify/SKILL.md`
shows the qualified wording and the named handshake warning in each place the
criterion is stated; this cycle's `verification.md` gc item, run after a per-ws
write and before regeneration, records the aggregate warning as expected and
`pass`es on the qualified criterion.
[Priority: should]
