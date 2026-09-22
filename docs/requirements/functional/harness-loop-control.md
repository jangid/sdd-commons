---
domain: HARN
last_updated: 2026-09-22
status: Approved
research_refs: [RS-008, RS-005, RS-006, RS-HARNESSP5-001]
---

# Requirements: Harness Hardening — Loop Control

## Overview

Hardens the SDD harness (`sdd-orchestrate` driving `sdd-implement`, `sdd-review`,
`sdd-replan`) with the deterministic loop-control, decoupled-verification and
boundary patterns from the harness-engineering literature, as scoped in the
idea catalogue (`docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md`,
ideas A1–A4, B5–B7, C8–C10, E13) and de-risked by RS-008. The `HARN` domain
spans three files sharing one ID sequence:

- **This file — loop control** (REQ-HARN-001..008, 027): a max-iteration guard on
  the review fix loop and on replan re-entries, a budget slot on every dispatch,
  an attempt ledger with an oscillation rule in stuck detection, a bounded
  checkpoint on circuit-break, and the no-new-artifact constraint (RS-008 Q1, Q3).
- **`harness-verification.md`** (REQ-HARN-009..019): the structured `RETURN:`
  block, repair packet, `VERDICT:` token, fresh chunk-close verifier, pruned
  re-dispatch state and orchestrator-owned routing (RS-008 Q2–Q4). The SKILL.md
  size audit (C10) is specified in the LINT domain (`integration/skill-lint.md`).
- **`harness-boundaries.md`** (REQ-HARN-020..026): a declared write scope per
  dispatch, checked mechanically on return, commit ownership and snapshot
  ordering (RS-008 Q5).

Standing constraints every requirement in the domain respects: no new on-disk
artifact type (REQ-ORCH-004), reviews stay ephemeral (REQ-ORCH-013), no
loop-position marker or authoritative loop log (REQ-ORCH-014), fix re-dispatches
carry findings and paths only (REQ-ORCH-012), and `sdd-review` is never the chunk
verifier (REQ-REV-005, REQ-REV-006). `sdd-implement` standalone (no orchestrator)
keeps its current behavior; every orchestrate-only mechanism is a second pass
layered on top, not a replacement (REQ-ORCH-001).

**Marker-4 resolution rule (applies to every HARN requirement).** Under
`docs/.sdd-version` == `4` the same artifacts are rooted at `docs/ws/<id>/`
(`plan.md`, `plan-history/`, `verification.md`, per-workstream `traceability.md`)
and the revert/merge target is the workstream branch, not `main`; marker `3` is
unchanged.

**Procedure placement.** Orchestrator procedure text introduced by this domain
(scope default table, three-command scope check, finding format, commit
ownership, snapshot ordering, `RETURN:` field-source mapping, verdict branching)
lands in **new** `skills/sdd-orchestrate/references/` files —
`references/write-scope.md` and `references/return-contract.md` — with short
stubs/pointers in `SKILL.md`, so the entry point keeps reading as a table of
contents (REQ-LINT-003, REQ-LINT-007).

Terminology: a **dispatch** is one subagent invocation by the orchestrator. The
five dispatch types are *pipeline* (one stage, sequential mode), *fix
re-dispatch* (loop-back-to-fix of a stage), *fan-out leaf* (one chunk-group in a
worktree), *review* (`sdd-review`), and *chunk verifier* (REQ-HARN-014). A
**leaf** is any non-review dispatch — the chunk verifier is a leaf with an empty
write scope. **Observable units** are counts the subagent can report about itself
without harness support — tasks, chunks, tool calls, test runs, approaches.

## Requirements

### Loop control

### REQ-HARN-001: Fix-loop max-iteration guard
The orchestrator must cap the number of loop-back-to-fix re-dispatches per stage
within one orchestrator session at a configurable maximum (default **3**). Each
fix re-dispatch must state its position as `iteration N of MAX`. When a stage's
review still does not pass after the MAX-th fix iteration, the orchestrator must
**not** dispatch another fix; it must exit to the operator at the gate with a
compiled findings log (the review's Critical/Material findings across the
iterations, by iteration) and offer only stop, manual intervention, or an
explicit operator-authorized extra iteration. The count is per-session — it is
not persisted to any artifact (REQ-ORCH-014) and restarts at 0 in a new session,
which is itself a human intervention. (see RS-008 Q1)
**Acceptance**: a session that reaches REJECT three times on one stage shows a
fourth gate with the compiled log and no automatic fourth dispatch; the
`iteration N of 3` line appears in each fix dispatch prompt; no file under
`docs/` records the counter.
[Priority: must]
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> RS-PIPELINEOBSERVABILITY-001 R6, R8; Q-REQ-PO-C) `[Updated: 2026-09-22]`:
> the **counted quantity** is narrowed to what the acceptance criterion already
> read — fix re-dispatches that follow a consumed **`REJECT`**, counted as a
> run of **consecutive** consumed `REJECT`s per stage per session
> (`reject_run`); a consumed `APPROVE` or `APPROVE_WITH_FIXES` resets the run to
> 0, and under REQ-HARN-PIPELINEOBSERVABILITY-001 an `APPROVE_WITH_FIXES` fix
> is applied and the stage proceeds, so an `APPROVE_WITH_FIXES` can never be
> "at cap" and never renders the exhausted gate. A verdict **voided** under
> REQ-HARN-PIPELINEOBSERVABILITY-004, a `post-manual` review
> (REQ-HARN-PIPELINEOBSERVABILITY-003) and a third opinion
> (REQ-ARB-HARNESSP2-007) are re-dispatches and count nothing. `iteration N of
> MAX` now reports `reject_run`. The exhausted gate's `manual intervention`
> option gains the mandatory `post-manual` review before `proceed`
> (REQ-HARN-PIPELINEOBSERVABILITY-003); the `explicit operator-authorized extra
> iteration` option is not removed (kickoff constraint 4 is this cycle's
> operator policy, not a corpus rule). No fourth cap is added: `ROUND_MAX` is
> **not adopted** (Q-REQ-PO-A) and the three-cap inventories stay at three.
> Observed defect: the cap fired at all four consumer-geometry document stages
> on an `APPROVE_WITH_FIXES` with zero blocking findings, forcing four manual
> interventions. **Acceptance, added**: a session whose consumed verdicts on
> one stage run `APPROVE_WITH_FIXES, REJECT, REJECT, APPROVE_WITH_FIXES` (the
> recorded requirements stage) never renders the exhausted gate, while
> `REJECT, REJECT, REJECT` does; `references/loop-control.md` §2 states the
> consecutive-`REJECT` rule and is pinned by a skill-lint `REQUIRED` row on the
> word `consecutive` in that section; the cross-field assertion (b) of
> REQ-TELEM-PIPELINEOBSERVABILITY-003 fails on a `fix_iteration` that
> increments across an `APPROVE_WITH_FIXES`. Leaves REQ-HARN-002/-008
> (`REPLAN_MAX`, `REDO_MAX`), REQ-HARN-011 (the field), REQ-ORCH-018 and
> REQ-ORCH-034 consistent.

### REQ-HARN-002: Replan re-entry cap, derived from plan-history
The orchestrator must cap replan re-entries per cycle at a configurable maximum
(default **3**). The count must be **derived**, not stored: it is the number of
`docs/plan-history/*-replan-*.md` archives whose filename date is on or after the
kickoff's `date:` frontmatter (falling back to the kickoff's commit date when the
field is absent, the same fallback `sdd-orchestrate` §KICKOFF uses for
`research_id`). On the MAX-th re-entry the orchestrator must surface the cap as a
gate event (REQ-ORCH-017) and must not route back into `sdd-replan` again without
an explicit operator decision. Minor in-place replans leave no archive and are
deliberately not counted. Under `docs/.sdd-version` == `4` the archives and the
kickoff are the active workstream's (`docs/ws/<id>/plan-history/`,
`docs/ws/<id>/kickoff.md`), so the count is per workstream; marker `3` is
unchanged. (see RS-008 Q1)
**Acceptance**: with three `-replan-` archives dated ≥ kickoff date, a fourth
replan trigger produces a gate pause naming the cap; archives dated before the
kickoff date or lacking the `-replan-` segment do not count.
[Priority: must]

### REQ-HARN-003: `-replan-` archive filename convention is a stated contract
Every plan archive written by `sdd-replan` must carry the `-replan-` segment in
its filename (`{date}-replan-{reason}.md`, or `{date}-m{N}-replan-{reason}.md`
per milestone), and no other skill (`sdd-plan` rewrite archives, milestone-
complete archives) may use that segment. `sdd-replan/SKILL.md` must state this
as an explicit contract, not an implicit convention, because REQ-HARN-002's
derivation depends on it. (see RS-008 Q1; lint row: REQ-LINT-005)
**Acceptance**: `sdd-replan/SKILL.md` contains the stated rule; `sdd-plan/SKILL.md`
archive names contain no `-replan-`; `tools/sdd-skill-lint.py` carries a
`REQUIRED` row for the pattern in `sdd-replan/SKILL.md`.
[Priority: must]

### REQ-HARN-004: Budget slot on every dispatch
Every dispatch template — pipeline, fix re-dispatch, fan-out leaf, review, and
chunk verifier — must carry an explicit `Budget:` slot stated in observable
units (e.g. "1 chunk, ≤ 25 tool calls, ≤ 3 test runs"; for a review "≤ 15 tool
calls, read-only"). The orchestrator must fill the slot on every dispatch; a
dispatch with an empty budget is a template violation. The read-only review
dispatch **does** get a budget slot (operator decision, Q-REQ-C in
`index.md`). (see RS-008 Q4 contract table, catalogue A2)
**Acceptance**: each fenced dispatch template in
`skills/sdd-orchestrate/references/dispatch-templates.md` and
`references/fan-out.md` contains `Budget:`; `tools/sdd-skill-lint.py` has a
`REQUIRED` row per template file (REQ-LINT-005).
[Priority: must]

### REQ-HARN-005: Budget exhaustion is a checkpointed return, never a silent overrun
A leaf that reaches its stated budget must stop, **write or return** the
circuit-break checkpoint (per REQ-HARN-008 — the sequential implementer writes
it into the plan; a fan-out leaf, barred from the plan, returns it) when the
exhaustion occurs mid-task, and return with `status: BUDGET_EXHAUSTED` and a
`budget_consumed` field in the same observable units the dispatch's `Budget:`
slot was stated in. The orchestrator must use `budget_consumed` to size the next
repair packet's budget (REQ-HARN-011). `budget_consumed` is **self-reported** by
the leaf — the harness exposes no tool-call counter to the orchestrator — so
adherence is only as trustworthy as the leaf; this is a recorded v1 limitation,
not a defect to be fixed in this cycle. (see RS-008 Q3)
**Acceptance**: the pipeline and fan-out templates instruct the leaf to
self-count in the stated units and to return `budget_consumed`; a `RETURN:`
block with `status: BUDGET_EXHAUSTED` and no `budget_consumed` is treated by the
orchestrator as malformed (REQ-HARN-009) and surfaced at the gate.
[Priority: must]

### REQ-HARN-006: Attempt ledger in implement
`sdd-implement` must keep, per task in its working context, an attempt ledger
with one entry per attempted fix: `attempt` (ordinal), `hypothesis` (one line),
`change` (files/lines touched, one line), `result` (which tests now pass/fail,
one line). The ledger must also carry a `verified_do_not_touch` list of paths
whose tests pass and that later attempts must not modify. The ledger lives in
the leaf's context only; its sole durable trace is the checkpoint
(REQ-HARN-008). It is **not** a Q-IMPL entry — Q-IMPL records deviation
decisions, the ledger records attempts; when an attempt reveals a spec ambiguity
the implementer files a Q-IMPL entry as today and cites its id in the ledger /
`open_questions`. (see RS-008 Q1, Q3; catalogue A3)
**Acceptance**: `sdd-implement/SKILL.md` Step 3 defines the four ledger fields and
`verified_do_not_touch`; no ledger text is written to `docs/spec/*.md` or
`docs/handoff/kickoff.md`.
[Priority: must]

### REQ-HARN-007: Oscillation rule in stuck detection
`sdd-implement` stuck detection must fire, in addition to its existing triggers
(same test failing 3+ times with different fixes, 2× expected effort, spec
contradiction), when the ledger shows oscillation: (a) an attempt's `result`
reports a test failing that an earlier attempt's `result` reported passing (a fix
re-introduced a fixed failure), or (b) an attempt's `change` matches an earlier
attempt's `change` (a repeated rejected patch). Both are string comparisons over
the ledger and need no new tooling. Firing follows the existing stuck path:
checkpoint (REQ-HARN-008) then replan trigger. (see RS-008 Q3; catalogue A3)
**Acceptance**: `sdd-implement/SKILL.md` Step 3 lists both oscillation conditions
with the word "oscillation"; a ledger fixture with `attempt 2: test_drift
REGRESSED` after `attempt 1: test_drift passes` is described as stuck.
[Priority: must]

### REQ-HARN-008: Circuit-break checkpoint in the plan's blocked-task note
When stuck detection (including oscillation), budget exhaustion, or the
fix-loop cap fires on an implement task, a structured checkpoint must be written
as the blocked-task note under that task in `docs/plan.md` (`docs/ws/<id>/plan.md`
under `docs/.sdd-version` == `4`; marker `3` unchanged) — the slot `sdd-replan`
already defines ("mark blocked tasks — note why they're blocked and what unblocks
them"). The checkpoint must be bounded (≤ ~15 lines) and contain: failing test
names with one-line reasons, the last hypothesis, a one-line-per-attempt ledger
summary, and the open question (citing a Q-IMPL id where one was filed, never
duplicating it). Full tracebacks must not be stored — they are regenerated by
re-running the named tests. The checkpoint is composed from the `RETURN:` block
(REQ-HARN-009) with **no dedicated checkpoint field**: failing tests + reasons ←
`failures[].test` / `failures[].message`; last hypothesis ← last
`ledger[].hypothesis`; ledger summary ← `ledger[].change` + `ledger[].result`
one-liners; open question ← `open_questions[]`. In sequential mode the
implementer writes it; under fan-out the leaf returns it and the orchestrator
applies it in its post-merge bookkeeping (leaves are barred from writing the
plan). A blocked note does not change phase detection (the plan still has
incomplete tasks) and cannot make the plan stale. (see RS-008 Q1; catalogue A4)
**Acceptance**: `sdd-implement/SKILL.md` and `sdd-replan/SKILL.md` state the
checkpoint format and the RETURN-field mapping; a checkpoint fixture is ≤ 15
lines and contains no traceback frames; `sdd-replan` Step 1 reads the checkpoint
as its "stuck state" input instead of "recent conversation context".
[Priority: must]

### Constraints

### REQ-HARN-027: No new on-disk artifact type
Every mechanism in this domain must fit inside existing artifacts and dispatch
templates: fix counts are session-scoped, replan counts are derived from
`plan-history`, the ledger lives in leaf context, the checkpoint reuses the plan's
blocked-task note, the `RETURN:` block, repair packet, `VERDICT:`,
`CHUNK_VERDICT:` and `SCOPE:` tokens are return/gate text, and the write scope is
a template slot. New `skills/sdd-orchestrate/references/*.md` files are skill
text, not project artifacts, and are permitted. REQ-ORCH-004 (kickoff is the
only new artifact), REQ-ORCH-013 (reviews ephemeral) and REQ-ORCH-014 (no loop
marker / loop log) must remain satisfied verbatim; no `docs/reviews/`, `.sdd/` or
telemetry file is created (telemetry is deferred to the next cycle, catalogue
D11). (see RS-008 Implications for Design)
**Acceptance**: `git ls-files docs/` after a full orchestrated cycle shows no file
type that did not exist before this feature, other than the `docs/plan-history/`
archives `sdd-replan` already produces.
[Priority: must]
[Updated 2026-09-17, RS-HARNESSP2-001] The sentence "no `docs/reviews/`, `.sdd/`
or telemetry file is created (telemetry is deferred to the next cycle, catalogue
D11)" is amended: a **gitignored, root-level** `.sdd/telemetry.jsonl` (TELEM
domain, `functional/telemetry.md`) is permitted under these non-interference
conditions, all of which must hold: (a) it lives outside `docs/` and is matched
by `.gitignore`, so it is not a project artifact and `git ls-files docs/` is
unchanged (this requirement's acceptance stands verbatim); (b) it is written
only by the orchestrator, after each gate (REQ-TELEM-HARNESSP2-004); (c) it is
never a phase-detection or staleness input and carries no resume field
(REQ-TELEM-HARNESSP2-003, -006), with a lint guard (REQ-TELEM-HARNESSP2-007) —
so REQ-ORCH-014 remains satisfied by mechanism; (d) records are counts, enums,
shas and timestamps, never finding text (REQ-ORCH-012/013 hold). The `docs/`
invariant, the `docs/reviews/` prohibition and REQ-ORCH-004 are unchanged; the
mirroring sentence at `docs/spec/harness-loop-control.md` §Constraints needs
the same amendment at the specs stage. Same device as REQ-ORCH-034's note.

<!-- REQ-HARN-HARNESSP5-NNN: workstream-prefixed additions for the harness-p5
     cycle (RS-HARNESSP5-001; marker 4). One HARN counter across the three HARN
     files: -001 here, -002 in harness-boundaries.md. -->

### REQ-HARN-HARNESSP5-001: the orchestrator flips `plan.md` `status: complete` at the implement stage gate `proceed`
Under orchestrated per-chunk dispatch the **orchestrator** must flip
`docs/ws/<id>/plan.md` `status:` to `complete` at the implement **stage gate**
`proceed` (after the stage review's verdict, never at the last per-chunk gate),
in its own bookkeeping commit — the same post-gate slot as aggregate
regeneration and the `pending-red → pass` flip (`write-scope.md` §7 gains a
second bookkeeping entry) — after its completion parse shows every numbered
chunk task `[x]`. The flip edits `status:` only; the `research_id:` stamp is
`sdd-plan`'s and is untouched. A chunk leaf ticks tasks and **never** writes
`status:` (`dispatch-templates.md` §PIPELINE per-chunk says so);
`sdd-verify` never writes the plan. `sdd-implement` Step 6.4 keeps the flip for
a **direct** session, with one sentence stating the orchestrated exception.
Because `HEAD_landed` is captured before any bookkeeping commit, the flip is
outside the `COMMIT:` range and never renders `landed, not observed`.
**Else-branch.** When the completion parse at `proceed` does **not** show every
numbered chunk task `[x]` (for example a task the stage review accepted as
deferred), the flip is **withheld** and the stage gate **pauses** — rendered as
one line `PLAN: INCOMPLETE (N of M ticked)` in the gate's signal order (exact
placement at specs' discretion, `loop-control.md` §5) — offering `replan │ stop`
only: `proceed` is not offered, so verify is never dispatched while `plan.md`
reads `implementing`, and phase detection (REQ-CYCID-HARNESSP3-001) keeps
reading the plan as incomplete until a replan closes the unticked tasks
(descoped or removed, archived per plan archival) and the gate is re-rendered.
Ratified as Q-REQ-P5-C. (workstream `harness-p5`; see RS-HARNESSP5-001 §Q3 — the
last-chunk leaf would assert a completion the stage review has not decided (p4
implement round 1 review C1); verify-on-entry would widen the verify leaf's
scope and leave a resumed session reading "implementing" on a fully ticked plan)
**Acceptance**: `grep -n 'status: complete' skills/sdd-orchestrate/SKILL.md skills/sdd-orchestrate/references/loop-control.md skills/sdd-orchestrate/references/write-scope.md skills/sdd-implement/SKILL.md`
shows the flip in §The gate, §1 and the §7 table, and the direct-session /
orchestrated split in `sdd-implement` Step 6; the per-chunk PIPELINE template
carries "tick tasks, never `status:`"; a walkthrough of an implement stage gate
`proceed` shows the flip in a commit separate from the leaf's and `COMMIT:
COMPLETE`, and a second walkthrough with one unticked task shows the
`PLAN: INCOMPLETE` pause, no flip and no verify dispatch; `python3 tools/sdd-skill-lint.py` exits 0 (a `REQUIRED` row for the
flip sentence is optional, `may`).
[Priority: must]

### REQ-HARN-PIPELINEOBSERVABILITY-001: the review verdict is the routing — `REJECT` → fix → re-review; `APPROVE_WITH_FIXES` → fix → proceed without re-review
The orchestrator's `loop-back-to-fix` must route by the consumed verdict as
`skills/review/SKILL.md` §Verdict definitions already defines it: after a
**`REJECT`**, re-dispatch the pipeline leaf with a repair packet and then
re-run the review for this stage, the iteration counted by `FIX_LOOP_MAX`
(REQ-HARN-001 as amended); after an **`APPROVE_WITH_FIXES`**, re-dispatch with
the packet and then **proceed without re-review** — the next stage's review
reads the fixed artifact as its upstream — unless the operator opts in to a
re-review at that gate; after an `APPROVE`, proceed. The repair packet carries
**Critical/Material findings only**, never minor ones. An `APPROVE_WITH_FIXES`
returned after the cap is reached is **not** an exhaustion: its fix is applied
and the stage proceeds. This is the resolution of gaps 3 and 4 together: the
four forced manual interventions were caused by re-reviewing every
`APPROVE_WITH_FIXES` fix under a cap that counted every re-dispatch — a fresh
reviewer over a growing artifact is a generator no cap converges. **Landed
before this stage** on branch `pipeline-observability`
(RS-PIPELINEOBSERVABILITY-001 §Gate observation 2026-09-22, V3) with its
skill-lint pins — the `REQUIRED` row `proceeds **without re-review**` on
`skills/orchestrate/SKILL.md` and the `FORBIDDEN` phrase `then re-run the
review for this stage` — which are the comparands; no commit is cited, because
a sha is a snapshot comparand of the class REQ-GC-PIPELINEOBSERVABILITY-001
warns on (Q-REQ-PO-A). This requirement records the rule as in force, not as a
proposal. V2's `ROUND_MAX` backstop and its
two-consecutive-`APPROVE_WITH_FIXES` terminator are not requirements — they are
moot under this routing (Q-REQ-PO-A). (see RS-PIPELINEOBSERVABILITY-001 §Q3,
§Gate observation 2026-09-22, R6.) Touches REQ-HARN-001 and REQ-HARN-013
(amended); leaves REQ-HARN-011, REQ-ORCH-018 (`REJECT` with no actionable
findings pauses), REQ-ORCH-034 (gate order) and the REQ-ARB-* keys (per round,
unchanged) consistent.
**Acceptance**: `python3 plugins/sdd/tools/skill-lint.py` exits 0 on the
branch with the two landed pins present — the `REQUIRED` row on
`skills/orchestrate/SKILL.md` for the phrase `proceeds **without re-review**`
and the `FORBIDDEN` phrase `then re-run the review for this stage` (files:
all) — and `python3 plugins/sdd/tools/skill-lint.py --self-test` exits 0 with
its pinned `REQUIRED` and `FORBIDDEN` counts including these rows; in a temp
copy, deleting the `without re-review` sentence from §The gate
makes the linter exit non-zero with the `REQUIRED` finding, and restoring the
unconditional phrase makes it exit non-zero with the `FORBIDDEN` finding;
`references/return-contract.md` §6's `APPROVE_WITH_FIXES` row and
`docs/spec/harness-return-contract.md`'s branching table read fix-then-proceed
with re-review on opt-in only; `references/loop-control.md` §5a's default is
proceed and §2a states that an `APPROVE_WITH_FIXES` at or after the cap is not
an exhaustion; this cycle's `verification.md` names the gates that ran under
this rule (kickoff decision 3).
[Priority: must]

### REQ-HARN-PIPELINEOBSERVABILITY-002: an informational `GROWTH:` line renders the deliverable's size delta at review round N ≥ 2
On a review round N ≥ 2 the stage gate must render one informational own-line
`GROWTH: <deliverable> +A/−D lines (N₁ → N₂) since round N−1` — the
deliverable's visible-line delta since the previous round — at position 6d of
the gate order, after `CONVERGENCE:` and before `TELEMETRY:`. It carries no
option set, never pauses and never withholds `proceed`; it exists so the
fix-grows-artifact generator behind gap 3 is visible at the gate where it
acts. **Landed before this stage** with its skill-lint pin — the `REQUIRED`
row `GROWTH: ` on `skills/orchestrate/references/loop-control.md`, which is the
comparand (no commit is cited, Q-REQ-PO-A); recorded here as in force. (see RS-PIPELINEOBSERVABILITY-001
§Gate observation 2026-09-22.) Leaves REQ-ORCH-034 (`TELEMETRY:` still last)
and REQ-HARN-027 (no new artifact — the line is text) consistent.
**Acceptance**: `python3 plugins/sdd/tools/skill-lint.py` exits 0 with the
landed `REQUIRED` row on `references/loop-control.md` for `GROWTH: `; in a
temp copy with item 6d removed it exits non-zero; `skills/orchestrate/SKILL.md`
§The gate's row for positions 6c, 6d, 7 names `GROWTH:` before `TELEMETRY:`;
`python3 plugins/sdd/tools/skill-lint.py --self-test` exits 0 with the pinned
`REQUIRED` count including this row; and, **at every stage of this cycle that
ran a review round N ≥ 2 — if any** (under REQ-HARN-PIPELINEOBSERVABILITY-001 a
round 2 arises only after a `REJECT` or an operator opt-in, so a correct cycle
may run none), this cycle's `verification.md` quotes the rendered `GROWTH:`
line from that gate; when no stage ran a round N ≥ 2, `verification.md` states
so and the temp-copy and self-test checks alone decide the criterion.
[Priority: must]

### REQ-HARN-PIPELINEOBSERVABILITY-003: a manual intervention is followed by a `post-manual` review before `proceed`
When the operator chooses `manual intervention` at an exhausted gate — or
otherwise edits the stage deliverable at a gate — the orchestrator must observe
its own edits as it observes a leaf's writes (the `COMMIT:` comparand of
REQ-HARN-HARNESSP4-001), then dispatch an ordinary review of this stage
labelled `post-manual` and withhold `proceed` until that review's verdict is
consumed; the verdict routes per REQ-HARN-PIPELINEOBSERVABILITY-001. The
`post-manual` review does not increment `reject_run` (REQ-HARN-001 as amended;
precedent: a third opinion is not a fix iteration, REQ-ARB-HARNESSP2-007) and
writes one `review` telemetry record carrying the label. Observed defect: four
interventions in the consumer-geometry cycle each went straight to the next
stage's dispatch with no review between, and the three orchestrator errors
attributable in telemetry were caught one stage and 3–4 rounds downstream.
This rule applies from the first gate of this cycle (kickoff constraint 3).
(see RS-PIPELINEOBSERVABILITY-001 §Q4, R8, §Mechanical pin R8.) Touches
REQ-HARN-001 (amended); leaves REQ-HARN-019 (routing orchestrator-only),
REQ-REV-003 (review inputs — an ordinary review dispatch) and
REQ-TELEM-HARNESSP4-001 (one record per dispatch) consistent.
**Acceptance**: `references/loop-control.md` §2b's `manual intervention` option
names the `post-manual` review and states that `proceed` is withheld until its
record exists, pinned by a skill-lint `REQUIRED` row on `post-manual` whose
removal in a temp copy makes the linter exit non-zero; the cross-field
assertion (c) of REQ-TELEM-PIPELINEOBSERVABILITY-003 fails on a
`manual_intervention` gate record not followed by a `post-manual` review
record; this cycle's `verification.md` lists every manual intervention with
the review round that followed it, and none without.
[Priority: must]
