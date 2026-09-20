---
domain: ORCH
last_updated: 2026-09-20
status: Approved
research_refs: [RS-005, RS-006, RS-008, RS-HARNESSP6-001]
---

# Requirements: SDD Orchestration Driver

## Overview

A driver skill (`sdd-orchestrate`) that runs the existing nine `sdd-*` skills as
a single-operator orchestration loop with per-stage external review. One human
session (the orchestrator) drives; each pipeline stage and each review run as
**separate subagents** with fresh context windows, giving isolation by
construction. After every stage the operator gates on the review verdict
(proceed │ loop-back-to-fix │ stop). Derived from the settled dual-session design
(D1–D7) and RS-005 feasibility findings, which proved subagent skill-invocation
and dispatch-time review isolation with live dispatches. (see RS-005)

Scope note: the loop is **research-entry by default**, with **sequential
execution as the default**. **Non-research (mid-pipeline) entry is supported**
(REQ-ORCH-031..033): when upstream artifacts already exist and are approved, the
operator may start the loop at requirements/specs/plan/implement. Parallel
implement-stage fan-out is **supported** as an opt-in mode (REQ-ORCH-016,
REQ-ORCH-022..028, where 028 is the [needs-spike] dispatch-concurrency item),
built as **Design B (orchestrator-owned fan-out, one level deep)** per the RS-006
spike, which proved subagent dispatch cannot nest and that orchestrator-owned
worktree creation + sequential merge with conflict-abort fallback all work.
(see RS-006)

## Requirements

### REQ-ORCH-001: Driver composes, never reimplements
The skill must act as a driver that composes the nine existing `sdd-*` skills.
It must not modify, rewrite, or reimplement the logic of any `sdd-*` skill;
stage work is performed by dispatching the corresponding skill. Staleness and
phase detection remain the stage skills' responsibility — the driver relays
their output, it does not duplicate that logic.
[Priority: must]

### REQ-ORCH-002: Four driver phases
The driver must implement four phases in order: (a) DISCUSS — converge operator
and orchestrator on scope and questions; (b) KICKOFF — write the kickoff prompt;
(c) LOOP — per-stage pipeline → review → gate; (d) DONE — reached when the verify
stage passes review and the operator approves.
[Priority: must]

### REQ-ORCH-003: DISCUSS borrows brainstorming
The DISCUSS phase must reach a shared understanding of the idea (scope and open
questions) before writing the kickoff, reusing the brainstorming process rather
than jumping directly to a kickoff or to implementation.
[Priority: must]

### REQ-ORCH-004: Kickoff is the only new on-disk artifact
The KICKOFF phase must write `docs/handoff/kickoff.md`, and this must be the only
new on-disk artifact type the driver introduces. It must be git-trackable. All
other stage outputs are the normal SDD artifacts, which serve as the message bus
between pipeline and review subagents.
[Priority: must]

### REQ-ORCH-005: Research is the default entry
Research is the **default** entry: when no upstream SDD artifacts exist, the
kickoff writer must emit a research kickoff and the LOOP must begin at the
research stage. Non-research (mid-pipeline) entry is also supported when upstream
artifacts already exist — see REQ-ORCH-031..033.
[Priority: must] [Updated: 2026-06-06]

### REQ-ORCH-006: Two separate subagents per stage
For each stage in [research, requirements, specs, plan, implement, verify], the
driver must dispatch the pipeline work and the review as two separate subagents,
each with a fresh context. The pipeline and review must never share a single
dispatch.
[Priority: must]

### REQ-ORCH-007: Pipeline non-interactivity contract
Each pipeline dispatch prompt must front-load every decision the stage skill
would otherwise ask a human for: the stage's question/scope, the success
criterion, an explicit budget, and the exact deliverable contract (files to
write and their frontmatter). The prompt must include a non-interactivity clause
instructing the subagent not to ask questions and not to fabricate operator
consent; genuinely missing information must be recorded under an Open
Questions / Assumptions section with a stated default. Evidence: RS-005 Q1 found
the only real hazard of subagent skill execution is the interactive-skill /
non-interactive-dispatch gap, fully solved by front-loading.
[Priority: must]

### REQ-ORCH-008: Central ID assignment
The orchestrator must assign artifact IDs (e.g. `RS-NNN`) centrally and pass them
verbatim to pipeline subagents, rather than letting subagents scan existing
artifacts and pick the next ID themselves. This prevents ID collisions,
especially under any future parallel dispatch.
[Priority: must]

### REQ-ORCH-009: Review dispatch carries paths only
Each review dispatch prompt must carry only: the repository root, the
deliverable artifact path(s), the upstream artifact path (where applicable —
see REQ-ORCH-010), and the instruction to invoke `sdd-review`. It must not
include the orchestrator's conversation or reasoning, the pipeline subagent's
reasoning or "here's what I was thinking" framing, kickoff prose beyond the
artifact itself, or any draft/intermediate states. This enforces `sdd-review`
Step 2's prohibited-inputs list at dispatch time rather than relying on operator
vigilance. Verified by RS-005 Q2: a paths-only review dispatch produced a correct
verdict with an audited zero-leakage input set.
[Priority: must]

### REQ-ORCH-010: Research-stage review omits the upstream path
For the research stage specifically, the review dispatch must omit the upstream
(kickoff) path, because `sdd-review` prohibits kickoff prompts as a contaminating
input. The reviewer instead reads the research questions from the deliverable's
own frontmatter. For all later stages, the upstream SDD artifact (requirements,
specs, plan, …) is a permitted, non-leaking input and must be supplied.
[Priority: must]

### REQ-ORCH-011: Human gate at every stage
After the pipeline → review sequence for a stage, the driver must surface the
review verdict to the operator and wait for an explicit decision: proceed,
loop-back-to-fix, or stop. The driver must not auto-advance to the next stage
without an operator decision.
[Priority: must]

### REQ-ORCH-012: Fix loop passes findings and paths only
On a loop-back-to-fix decision, the driver must re-dispatch the pipeline subagent
with only the review findings plus the relevant artifact paths — not a
re-litigation of the reviewer's reasoning or chain-of-thought — and must then
re-run the review for that stage.
[Priority: must]

### REQ-ORCH-013: Reviews are ephemeral
A review verdict is the review subagent's return text, surfaced to the operator
inline. The driver must not write review verdicts to disk as a project artifact
and must not create a `docs/reviews/` directory. Decisions land in the artifacts
themselves (commits, Q-IMPL entries, replan triggers).
[Priority: must]

### REQ-ORCH-014: Resume via existing phase detection
On re-entry in a new orchestrator session, the driver must derive loop position
from the existing SDD artifacts (existence, status, and staleness), reusing the
stage skills' phase detection. The driver must not introduce a dedicated
loop-position marker file, and `docs/handoff/kickoff.md` must not carry an
authoritative loop log. A pending or prior review is reproduced by re-dispatching
the review subagent against the current artifacts. Evidence: RS-005 Q3.
[Priority: must]

### REQ-ORCH-015: Sequential execution is the default
By default, all stages must run single-threaded in the main workspace. Sequential
execution is the baseline behavior; parallel implement-stage fan-out
(REQ-ORCH-016, REQ-ORCH-022..028, where 028 is the [needs-spike]
concurrency item) is an opt-in mode selected at the implement
gate. When fan-out is not selected, the implement stage runs single-threaded in
the main workspace exactly as every other stage does.
[Priority: must] [Updated: 2026-06-04]

### REQ-ORCH-016: Implement fan-out boundary rule
The orchestrator must support parallel implement-stage fan-out. Fan-out must occur
along the independent branches of the plan's **chunk** dependency graph — not
per-milestone (too coarse, milestones are sequential) and not per-task (too
fine). The orchestrator must derive the parallel groups by reading the plan's
dependency graph, without modifying `sdd-implement`. Fan-out applies only when the
dependency graph actually contains independent chunk branches; otherwise execution
stays sequential even when fan-out is selected. (chunk-boundary rule: RS-005;
orchestrator-owned design selection: RS-006 Q4)
[Priority: must] [Updated: 2026-06-04]

> Note: REQ-ORCH-022..028 extend the implement-fan-out cluster begun at
> REQ-ORCH-015/016 (IDs are non-monotonic in this file).

### REQ-ORCH-022: Orchestrator-owned fan-out, one level deep (Design B)
_(added 2026-06-04, RS-006)_
The orchestrator must own the fan-out directly, dispatching the parallel implement
subagents itself, nesting exactly one level deep. A dispatched implement subagent
must not itself dispatch sub-subagents — each fan-out subagent is a leaf. This is
required because a dispatched subagent has no subagent-dispatch tool in its
toolset, making a nested implement-owns-fan-out design (Design A) infeasible in
this harness. (see RS-006 Q1, Q4)
[Priority: must]

### REQ-ORCH-023: One worktree per concurrently-runnable chunk-group
For each concurrently-runnable chunk-group, the orchestrator must provision one
git worktree on its own branch and pin the corresponding implement subagent to
it, so that parallel work is isolated per worktree. The orchestrator (not the
subagent) must provision these worktrees, giving it cleaner lifecycle and
cleanup ownership (per RS-006 Q2; decision: see Q-REQ-G). Each fan-out subagent
must operate only within its assigned worktree/branch.
[Priority: must]

### REQ-ORCH-024: Fan-out is opt-in at the implement gate
The operator must explicitly choose fan-out at the implement gate; the orchestrator
must not enable fan-out automatically. When the operator does not opt in, the
implement stage runs sequentially per REQ-ORCH-015.
[Priority: must]

### REQ-ORCH-025: Sequential merge to main before the implement-stage review
After the fan-out subagents return, the orchestrator must merge the worktree
branches **sequentially** into `main` and complete all merges **before** the
implement-stage review runs. The review must therefore operate on the merged
state, not on individual unmerged branches.
[Priority: must]

### REQ-ORCH-026: Merge-conflict abort-and-redo (with optional best-effort resolution)
On detecting a merge conflict — a non-zero exit from `git merge` — the orchestrator
must `git merge --abort` and redo the offending chunk-group by **re-deriving** its
implement work in a worktree re-branched from the updated `main` (not by replaying
the prior subagent output), then re-attempt the merge.
This abort-and-redo fallback is the guaranteed contract and must never corrupt or
unwind already-merged work; because merges are sequential, an abort only unwinds
the single failing merge. As an explicit BEST-EFFORT optional step, the orchestrator
may first attempt automatic resolution of the conflict before falling back to
abort-and-redo; auto-resolution is not guaranteed and the abort-and-redo path is
always available as the verifiable fallback. (see RS-006 Q3)
[Priority: must] [Updated: 2026-06-04]

### REQ-ORCH-027: Subagents commit with inline git identity flags
Each fan-out implement subagent must commit using inline
`git -c user.email=... -c user.name=...` identity flags rather than writing a
shared `.git/config`, because a dispatched subagent's command sandbox blocks
writes to the main repo's `.git/config`. Commits, merges, and branch operations
must still succeed under this constraint. (see RS-006 Q2)
[Priority: must]

### REQ-ORCH-028: Concurrent dispatch of fan-out subagents [needs-spike]
The orchestrator should dispatch the fan-out implement subagents so they execute
truly concurrently rather than serialized, to obtain wall-clock speedup. Whether
the harness runs a batch of dispatches concurrently or serializes them is
**unverified** and must be resolved at spec/implementation time. This question
only matters when ≥2 chunk-groups are concurrently runnable; with a single
runnable group it is moot. The fan-out design (worktree isolation + sequential
merge) holds correctly either way; only the wall-clock speedup is at stake if
dispatch is serialized. [needs-spike]
(see RS-006 Open Questions, RS-005 Q4)
[Priority: should]

### REQ-ORCH-017: Replan surfaces as a gate event
When a pipeline subagent triggers a replan (stuck detection, spike invalidation,
or a verification failure), the driver must surface it to the operator as a gate
event. The loop may then route back to an earlier stage via `sdd-replan`,
consistent with the cyclic SDD model. The driver must not silently absorb or
auto-resolve a replan trigger.
[Priority: must]

### REQ-ORCH-018: Reject verdict with no actionable findings pauses
If a review returns a reject/fail verdict with no actionable findings, the driver
must pause and let the operator decide whether to re-dispatch, override, or stop.
It must not auto-loop the pipeline in this case.
[Priority: must]

### REQ-ORCH-019: Single-skill packaging
The driver must be a single skill at `skills/sdd-orchestrate/SKILL.md`, kept under
the project's ~1000-line guideline. The kickoff-writer must not be a separate
skill. The dispatch prompt templates (pipeline and review) may live in a
`skills/sdd-orchestrate/references/` file to keep the body lean.
[Priority: should] [Updated: 2026-06-05]

### REQ-ORCH-020: Extensive operator user documentation
The skill must ship with extensive end-user (operator) documentation, distinct
from the `SKILL.md` (which is Claude-facing instructions). The documentation must
cover, at minimum: what the driver is and when to use vs. skip it; each of the
four phases (DISCUSS, KICKOFF, LOOP, DONE) explained for a human operator; a
complete worked example walking one idea from DISCUSS through a per-stage
pipeline→review→gate to DONE; the isolation guarantees and why they matter;
**installation** instructions, including linking the skill into the Claude skills
directory (`~/.claude/skills/<name>` → repo `skills/<name>`) as the project does
for every SDD skill; troubleshooting (including the blocked-subagent-write
labeled-content fallback); the execution model (sequential by default, with
implement-stage fan-out available as an opt-in mode — including its single-chain
degrade-to-sequential behavior); and the remaining v1 limitation
(**research-entry-only**: no non-research / mid-pipeline entry). It must live at a
discoverable path under `skills/sdd-orchestrate/`.
[Priority: must] [Updated: 2026-06-05]

### REQ-ORCH-021: Project README introduces the driver and links the docs
The project README must be updated to introduce `sdd-orchestrate` (and the SDD
skill suite it drives) and link to the operator documentation (REQ-ORCH-020) and
the skills directory. Installation guidance in the README must describe the
`~/.claude/skills/` symlink convention so a new adopter can install the skills.
[Priority: must]

<!-- REQ-ORCH-029..030 capture driver-behavior gaps observed while dogfooding the
     RS-006 fan-out cycle through orchestrate itself. (see RS-006) -->

### REQ-ORCH-029: Distinguish a new cycle from a mid-loop resume
On entry the driver must distinguish **resuming an in-progress cycle** from
**starting a new cycle after a completed one**. When the on-disk artifacts of the
prior cycle indicate DONE (e.g. `docs/verification.md` with `status: pass`) and
the operator brings a new idea/feature in DISCUSS, the driver must treat this as a
**new cycle** — run DISCUSS and overwrite `docs/handoff/kickoff.md` at KICKOFF —
rather than reporting the prior cycle's DONE state and stopping. Operator intent
disambiguates the two cases; the driver must surface the detected state and the
new-vs-resume interpretation before proceeding. Derived from RS-006 dogfooding
finding #1. [Priority: must]

### REQ-ORCH-030: Orchestrator-only work is not delegated to a leaf subagent
Work that requires orchestrator-level capabilities — specifically subagent
**dispatch** — must be performed by the orchestrator itself, not handed to a leaf
pipeline subagent. A dispatched subagent has no dispatch tool (RS-006 Q1), so it
cannot execute implement-stage fan-out (which dispatches one subagent per
chunk-group) or a spike that measures parallel dispatch. The driver must recognize
such tasks and run them directly rather than delegating them into a pipeline
dispatch that would stall or be unable to proceed. Derived from RS-006 dogfooding
finding #4. [Priority: must]

<!-- REQ-ORCH-031..033 add non-research (mid-pipeline) entry — design Q4 from the
     dual-session design, previously deferred. -->

### REQ-ORCH-031: Non-research (mid-pipeline) entry is supported
The driver must support starting the loop at a stage other than research when the
relevant upstream artifacts already exist and are approved. The valid entry
stages are **requirements, specs, plan, and implement** (research is the default;
verify is not an entry point — verifying an existing project is just invoking
`sdd-verify` directly, no loop needed). From the chosen entry stage, the LOOP
proceeds normally (pipeline → review → gate per stage) to DONE. This is distinct
from resume (REQ-ORCH-029): resume continues a cycle this driver started, whereas
non-research entry begins a loop over upstream artifacts produced outside it.
[Priority: must]

### REQ-ORCH-032: Entry-stage detection, confirmation, and validation
On a non-research entry the driver must **auto-detect** the proposed entry stage
using the existing phase detection (the furthest-complete approved upstream
artifact → the next stage), **present it to the operator, and confirm** before
proceeding; the operator may override to an earlier stage. The driver must
**validate** that the chosen entry stage's upstream artifacts exist and are
approved/complete; if they are not, it must not start there — it must route to the
earliest incomplete upstream stage and tell the operator. The driver must not
guess an entry stage without operator confirmation.
[Priority: must]

### REQ-ORCH-033: Entry kickoff for non-research entry
For a non-research entry, KICKOFF must still write `docs/handoff/kickoff.md`, but
as an **entry kickoff** rather than a research kickoff: it states the scope of the
change, the entry stage, and which upstream artifacts are assumed approved — not
research questions. It remains git-tracked and the only new on-disk artifact type
(REQ-ORCH-004 holds). DISCUSS still runs first to converge on the change scope.
[Priority: must]

<!-- REQ-ORCH-034 adds the gate-text additions required by the harness-hardening
     cycle. The hardening mechanisms themselves live in the HARN domain
     (functional/harness-loop-control.md, harness-verification.md,
     harness-boundaries.md). (see RS-008) -->

### REQ-ORCH-034: Gate text carries the hardening signals
_(added 2026-09-17, RS-008)_
At every gate the driver must surface, next to the review verdict and in this
order: the machine-parsed `VERDICT:` value (REQ-HARN-013); for the implement
stage, each chunk's `CHUNK_VERDICT:` (REQ-HARN-014); the write-scope block ending
in `SCOPE: CLEAN | VIOLATION` (REQ-HARN-022); the leaf's `RETURN.status` and
`budget_consumed` against the dispatched `Budget:` (REQ-HARN-005); and, when a
fix loop is active, `iteration N of MAX` (REQ-HARN-001) or the replan re-entry
count against its cap (REQ-HARN-002). The operator's decision vocabulary stays
proceed │ loop-back-to-fix │ stop, extended only by the scope options `revert
path | accept & widen scope`. All of this is ephemeral gate text (REQ-ORCH-013).
The gate rendering procedure (token branching, scope finding format) lives in
`skills/sdd-orchestrate/references/return-contract.md` and
`references/write-scope.md`; `SKILL.md` §The gate carries the ordered signal list
and a pointer only.
_[Updated 2026-09-17, specs review C1]_ In sequential implement mode these signals
are rendered at a lightweight **per-chunk gate** after each chunk dispatch returns
(order: `RETURN.status` → `SCOPE:` → `CHUNK_VERDICT:`; options proceed │ fix │ stop,
where proceed commits the chunk); under fan-out the same block renders per leaf
before its merge. The stage review `VERDICT:` and loop counters render once at the
stage gate after all chunks. See `docs/spec/harness-chunk-verifier.md` §Sequencing.
**Acceptance**: `sdd-orchestrate/SKILL.md` §The gate lists the five signals and
links the two references files (REQ-LINT-004 resolves the links); a gate
rendering fixture shows them in the stated order.
[Priority: must]

### REQ-ORCH-HARNESSP6-001: `CONVERGENCE:` renders as item 6c of the gate signal order, informational
The L2 convergence signal must render as its own **own-line token** at the gate,
`CONVERGENCE:`, placed at position **6c** of the REQ-ORCH-034 signal order —
after 6b (`PLAN:`) and immediately before 7 (`TELEMETRY:`) — naming the cluster's
key (the shared id, the file alone for a sectionless file, or file and section),
the contributing layers, and the layer count, for example
`CONVERGENCE: docs/spec/telemetry.md §Writer rule (review, red) — 2 layers`. It
renders after every finding-bearing signal and after both derived pauses because
it is derived from them; the "renders last" clause governing `TELEMETRY:` gains
6c in the same enumeration. The signal is **informational**: it never pauses the
gate, has no option set, and never withholds `proceed`. That is the decisive
choice — with no root-cause field the cluster is a heuristic, and a pausing
heuristic turns every false positive into an operator interruption, while an
informational line costs one line when wrong and delivers its whole value when
right, because the value is the operator noticing. (workstream `harness-p6`;
RS-HARNESSP6-001 Q4(c), Confidence Medium; position chosen over a derived line
under one producer because a convergence line spans producers)

**[Updated: 2026-09-20 — amended at replan, caused by the Chunk 8 resolving
spike. The token, its position 6c and its informational status are unchanged;
only what a cluster can be keyed on changed, so the rendered line now names the
cluster's key in the three shapes the amended cluster rule admits
(REQ-HARN-HARNESSP6-002). Requirement id and number unchanged.]**

**Acceptance**: `skills/sdd-orchestrate/references/loop-control.md` §5 lists 6c
between 6b and 7 and its §7 "renders last" clause names 6c;
`skills/sdd-orchestrate/SKILL.md` §The gate names the token in its non-divergent
summary; a gate rendering fixture shows the token in the stated position and
shows `proceed` available while it is displayed; `python3
tools/skill-lint.py` exits 0.
[Priority: must]

### REQ-ORCH-HARNESSP6-002: L2 ships as co-located convergence and is not a fifth verification layer
The shipped scope of L2 must be stated explicitly as **co-located** convergence
— clustering findings that already carry a location — and must not be described
or verified as conceptual convergence. Conceptual convergence (findings sharing
a root cause but no file and no section, as in the three-layer origin case the
signal was named for) cannot be derived from what layers already return: it
needs either a root-cause field on a leaf's `RETURN:` or a fifth layer whose job
is correlation, and both are standing exclusions. Against that origin case the
shipped form clusters **none** of the three layers: replayed over the record,
the two members whose locations survive differ at file level and cite different
ids, and the third was never durably recorded. That measured result — and not a
recall figure the record does not reproduce — is what must be stated. Three invariants bind: L2 adds **no durable artifact**
under `docs/` (its ledger is session-scoped and its output is ephemeral gate
text); it must **not influence phase detection** — no skill's entry check reads
it and it is never written to a file a detector reads; and the **four-layer
verification table stays byte-unchanged**, because L2 is an orchestrator-derived
gate signal, not a layer. No telemetry record key is added for it. (workstream
`harness-p6`; RS-HARNESSP6-001 Q4(d) and §Implications for Design — "requirements
must state the co-located scope explicitly, or verification will be asked to
prove a property the design does not deliver")

**[Updated: 2026-09-20 — amended at replan, caused by the Chunk 8 resolving
spike: the co-located `(file, section)` key formed zero clusters over three
replayed cycles and zero of three on the origin case, so the previously stated
2-of-3 recall is refuted and withdrawn here. The shipped scope is now the
shared-id key as primary plus the sectionless-file rule; the three invariants
(no durable artifact, no influence on phase detection, four-layer table
byte-unchanged) and the no-telemetry-key rule are unchanged. Requirement id and
number unchanged.]**
**Acceptance**: `git diff` over the cycle shows the four-layer verification
table byte-unchanged in `CLAUDE.md` and in every spec that restates it;
`docs/spec/harness-loop-control.md` §Convergence Signal states the shipped scope
(shared id primary, sectionless file, retained `(file, section)`) and states the
origin-case recall as the Chunk 8 replay measured it, with no recall figure the
replay does not reproduce; no file under `docs/` is created by L2 and no phase-detection rule in any `sdd-*` skill references
`CONVERGENCE:`; `python3 tools/sdd-gc.py --report` reports no new artifact class.
[Priority: must]
