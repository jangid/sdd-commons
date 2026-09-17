---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-ORCH-001
  - REQ-ORCH-002
  - REQ-ORCH-003
  - REQ-ORCH-004
  - REQ-ORCH-005
  - REQ-ORCH-006
  - REQ-ORCH-007
  - REQ-ORCH-008
  - REQ-ORCH-009
  - REQ-ORCH-010
  - REQ-ORCH-011
  - REQ-ORCH-012
  - REQ-ORCH-013
  - REQ-ORCH-014
  - REQ-ORCH-015
  - REQ-ORCH-016
  - REQ-ORCH-017
  - REQ-ORCH-018
  - REQ-ORCH-019
  - REQ-ORCH-020
  - REQ-ORCH-021
  - REQ-ORCH-022
  - REQ-ORCH-023
  - REQ-ORCH-024
  - REQ-ORCH-025
  - REQ-ORCH-026
  - REQ-ORCH-027
  - REQ-ORCH-028
  - REQ-ORCH-029
  - REQ-ORCH-030
  - REQ-ORCH-031
  - REQ-ORCH-032
  - REQ-ORCH-033
  - REQ-ORCH-034
---

# SDD Orchestration Driver

## Context

SDD's nine skills are run today as an ad-hoc manual flow: the operator invokes
each `sdd-*` skill in turn and occasionally invokes `sdd-review` separately for
an external read. There is no defined workflow for the loop the operator wants:
evolve an idea to shared understanding, emit a kickoff, run the pipeline, and
after **each** stage have a fresh, context-isolated reviewer check the output
with back-and-forth until the stage is sound.

`sdd-orchestrate` is the **driver** that ties the existing skills into that loop.
It adds the isolation discipline and handoff conventions that make per-stage
external review trustworthy. RS-005 proved the two load-bearing mechanisms with
live subagent dispatches: a subagent can reliably invoke an `sdd-*` skill and
write artifacts (Q1), and a review subagent fed only artifact paths produces a
correct verdict with audited zero leakage (Q2). This spec defines the driver's
phases, its dispatch contracts, its gate protocol, and what it explicitly does
not do. Design decisions D1–D7 from the dual-session design are settled inputs.

[Updated 2026-06-04: the implement-stage fan-out feature is now an ACTIVE design,
not deferred. RS-006 ran a live spike that ruled out nested fan-out (Design A) as
infeasible and selected orchestrator-owned fan-out (Design B). The "Sequential
Execution and Implement-Stage Fan-out" section below now specifies Design B —
boundary rule, opt-in gate, worktree provisioning, sequential merge, and conflict
handling — with dispatch-concurrency as the single remaining uncertainty
(REQ-ORCH-016, REQ-ORCH-022..028; see RS-006).]

## Design

### Driver Positioning

`sdd-orchestrate` is a **driver**, not a tenth phase skill. It composes the nine
existing skills and never reimplements their logic (REQ-ORCH-001). Stage work —
including each skill's own phase detection and staleness handling — is performed
by dispatching the corresponding `sdd-*` skill; the driver relays that output
rather than duplicating it. The driver owns only orchestration concerns:
sequencing stages, constructing isolated dispatches, and mediating operator
gates.

A single human session (the **orchestrator**) drives. Each pipeline stage and
each review run as **separate subagents** with fresh context windows (D1). This
gives isolation by construction — a freshly dispatched subagent has no shared
context window through which the orchestrator's reasoning could leak (D2),
a stronger guarantee than two human terminal sessions.

### Driver Phases

The driver runs four phases in order (REQ-ORCH-002):

```
DISCUSS  — orchestrator + operator brainstorm the idea to shared understanding
           (scope + open questions); reuses the brainstorming process
   ↓
KICKOFF  — orchestrator writes docs/handoff/kickoff.md (research kickoff by
           default; an entry kickoff for non-research mid-pipeline entry)
   ↓
LOOP     — for each stage in [research, requirements, specs, plan, implement, verify]:
             1. PIPELINE subagent → invokes sdd-<stage>, writes the SDD artifact(s)
             2. REVIEW subagent   → fed artifact paths only; invokes sdd-review;
                                     returns a tiered verdict (return text)
             3. GATE (operator)   → orchestrator surfaces the verdict and waits:
                                     proceed │ loop-back-to-fix │ stop
             4. if fix → re-dispatch PIPELINE with review findings + paths only;
                         back to step 2
   ↓
DONE     — the verify stage passes review AND the operator approves
```

DISCUSS must reach a shared understanding before KICKOFF, reusing the
brainstorming process rather than jumping straight to a kickoff or to
implementation (REQ-ORCH-003).

### Kickoff Artifact

KICKOFF writes `docs/handoff/kickoff.md`, the **only** new on-disk artifact type
the driver introduces (REQ-ORCH-004). It is git-trackable. Every other stage
output is a normal SDD artifact; those artifacts are the message bus between
pipeline and review subagents (D5).

By **default** (no upstream SDD artifacts exist) the kickoff writer emits a
**research kickoff** and the LOOP begins at the research stage (REQ-ORCH-005).
When upstream artifacts already exist and are approved, the operator may instead
start mid-pipeline — see §Entry Points.

### Entry Points

The driver supports **non-research (mid-pipeline) entry** (REQ-ORCH-031): starting
the LOOP at **requirements, specs, plan, or implement** when the relevant upstream
artifacts already exist and are approved. Research is the default; **verify is not
an entry point** (verifying an existing project is just invoking `sdd-verify`
directly — no loop needed).

This is **distinct from resume** (REQ-ORCH-029): resume *continues a cycle this
driver started* (its kickoff + partial artifacts are on disk); non-research entry
*begins a fresh loop over upstream artifacts produced outside this driver* (e.g.
the operator hand-wrote requirements, or ran `sdd-requirements` directly, and now
wants the gated loop for the rest).

**Detection, confirmation, validation (REQ-ORCH-032).** On entry the driver:
1. **auto-detects** the proposed entry stage via the existing phase detection —
   the furthest-complete *approved* upstream artifact → the next stage;
2. **presents** that proposal to the operator and **confirms** before proceeding;
   the operator may override to an *earlier* stage (never a later one whose
   upstream is unmet);
3. **validates** the chosen entry stage's upstream artifacts exist and are
   approved/complete. If they are not, it must **not** start there — it routes to
   the earliest incomplete upstream stage and tells the operator why.

The driver never silently guesses an entry stage; confirmation is mandatory.

**Entry kickoff (REQ-ORCH-033).** KICKOFF still writes `docs/handoff/kickoff.md`
(REQ-ORCH-004 holds — it remains the only new artifact and is git-tracked), but as
an **entry kickoff**: it records the *scope of the change*, the *entry stage*, and
*which upstream artifacts are assumed approved* — not research questions. DISCUSS
still runs first to converge on the change scope. From the entry stage onward the
LOOP is identical to a research-entry cycle (pipeline → review → gate per stage).

### Per-Stage Dispatch Model

For each stage the driver issues **two separate subagent dispatches** — never a
single combined one (REQ-ORCH-006):

| Dispatch | Fresh ctx | Purpose | Carries |
|----------|-----------|---------|---------|
| Pipeline | yes | Execute one SDD stage | Stage skill name, front-loaded decisions, IDs, cwd, (on fix) review findings |
| Review | yes | Externally review the stage output | Repo root + deliverable path(s) + (non-research) upstream path + "invoke sdd-review" |

The pipeline dispatch always runs to completion (artifacts on disk) before the
review dispatch is constructed, because the review's only inputs are the paths
the pipeline produced.

### Pipeline Subagent Contract

A subagent is non-interactive — it has no operator to answer questions. RS-005 Q1
found this is the single real hazard of subagent skill execution: an interactive
`sdd-*` skill that says "ask the user" will otherwise stall or fabricate consent.
The contract neutralizes this (REQ-ORCH-007):

**The pipeline dispatch prompt MUST:**
- Front-load every decision the stage skill would ask a human for: the stage's
  question/scope, the success criterion, an explicit budget, and the exact
  deliverable contract (files to write + their frontmatter).
- Pin all artifact IDs and the absolute working directory. IDs are assigned
  **centrally by the orchestrator** and passed verbatim — subagents must not scan
  existing artifacts and pick the next ID themselves, which would collide under
  any future parallel dispatch (REQ-ORCH-008).
- Include a **non-interactivity clause**: do not ask questions; do not fabricate
  operator consent; record genuinely missing information under an
  Open Questions / Assumptions section with a stated default and proceed.
- Include the labeled-content fallback (if a file cannot be written, return its
  full content with the target path labeled).

The full prompt template lives in the skill's `references/` file (REQ-ORCH-019);
this spec defines the contract its slots must satisfy. Illustrative shape:

```
You are a non-interactive pipeline subagent executing ONE SDD stage.
Working directory (absolute): {repo_root}
Stage skill: sdd-{stage}    Assigned IDs (verbatim): {ids}
Inputs (paths): {input_paths}    [on fix] Review findings: {findings}
Do NOT ask questions; do NOT fabricate consent. Missing info → record under
Open Questions with a default and proceed. Write {deliverable_contract}.
```

### Review Subagent Contract

The review dispatch enforces `sdd-review` Step 2's prohibited-inputs list **at
dispatch time**, rather than relying on operator vigilance (REQ-ORCH-009). RS-005
Q2 verified a paths-only dispatch yields a correct verdict with an audited
zero-leakage input set.

**The review dispatch prompt MUST carry ONLY:**
- the repository root,
- the deliverable artifact path(s),
- the upstream artifact path — **except for the research stage** (see below),
- the instruction to invoke `sdd-review`.

**It MUST NOT carry:**
- the orchestrator's conversation or reasoning,
- the pipeline subagent's reasoning or "here's what I was thinking" framing,
- kickoff prose beyond the artifact itself,
- any draft or intermediate states.

The reviewer obtains all other context (frontmatter, commit history, the
traceability matrix) by reading repository files itself.

**Research-stage exception** (REQ-ORCH-010): for the research stage the dispatch
**omits the upstream path**, because the upstream is the kickoff and `sdd-review`
prohibits kickoff prompts as a contaminating input. The reviewer reads the
research questions from the deliverable's own frontmatter. For all later stages
the upstream SDD artifact (requirements, specs, plan, …) is a permitted,
non-leaking input and MUST be supplied.

### Gate Protocol

After pipeline → review, the orchestrator surfaces the verdict and waits for an
explicit operator decision — it never auto-advances (REQ-ORCH-011):

| Decision | Driver action |
|----------|---------------|
| **proceed** | Advance to the next stage. |
| **loop-back-to-fix** | Re-dispatch the pipeline subagent with **only** the review findings + relevant artifact paths (not a re-litigation of the reviewer's reasoning), then re-run the review for that stage (REQ-ORCH-012). _(v5)_ The re-dispatch carries the fixed-shape repair packet — `harness-return-contract.md` §Repair Packet; for the implement stage, findings are first mapped to chunks (§Finding → Chunk Mapping) and each touched chunk passes its per-chunk gate before the re-review. |
| **stop** | Halt the loop; leave artifacts as-is. |

_(v5)_ For the implement stage a lightweight **per-chunk gate** (`proceed │ fix
│ stop`) precedes this stage gate — once per chunk, after the write-scope check
and the chunk verifier, before the orchestrator commits the chunk; see §v5
Harness Hardening and `harness-chunk-verifier.md` §Sequencing — Sequential Mode.

Two non-standard events route through the gate as well:

- **Replan trigger** (REQ-ORCH-017): when a pipeline subagent triggers a replan
  (stuck detection, spike invalidation, or a verification failure), the driver
  surfaces it to the operator as a gate event. The loop may then route back to an
  earlier stage via `sdd-replan`, consistent with the cyclic SDD model. The
  driver must not silently absorb or auto-resolve a replan trigger.
- **Reject with no actionable findings** (REQ-ORCH-018): if a review returns a
  reject/fail verdict carrying no actionable findings, the driver pauses and lets
  the operator decide (re-dispatch, override, or stop). It must not auto-loop the
  pipeline in this case.

### Ephemeral Reviews

A review verdict is the review subagent's return text, surfaced inline to the
operator. The driver must not write verdicts to disk as a project artifact and
must not create a `docs/reviews/` directory (REQ-ORCH-013, preserving the
project's prior Q-REQ-B decision). Decisions land in the artifacts themselves —
commits, spec edits, Q-IMPL entries, replan triggers.

### Resume and Phase Detection

On re-entry in a new orchestrator session, the driver derives loop position from
the existing SDD artifacts (existence, status, staleness), reusing the stage
skills' own phase detection (REQ-ORCH-014). RS-005 Q3 established this is
sufficient: loop position is already fully encoded on disk, and the only
non-persisted state — the per-stage review verdict — is **reproducible** by
re-dispatching the (read-only, idempotent) review subagent against the current
artifacts.

Therefore the driver introduces **no** dedicated loop-position marker file, and
`docs/handoff/kickoff.md` carries **no** authoritative loop log. The artifacts
are the single source of truth for resume.

#### New cycle vs. resume (REQ-ORCH-029)

Artifact-only phase detection has one ambiguity, observed while dogfooding the
RS-006 cycle: when the prior cycle is **complete** (`docs/verification.md` with
`status: pass`), the same on-disk state that means "DONE — nothing to resume"
also describes the starting point for the *next* feature. The driver must not
silently report the prior DONE and stop when the operator is in fact opening a new
cycle.

Resolution: on entry the driver classifies the state as one of
- **resume** — the latest cycle is mid-loop (some stage incomplete/stale) → continue it; or
- **done** — the latest cycle is `status: pass` and the operator has no new idea → report DONE; or
- **new cycle** — the latest cycle is `status: pass` **and** the operator brings a new idea in DISCUSS → run DISCUSS and overwrite `docs/handoff/kickoff.md` at KICKOFF.

Operator intent is the disambiguator between *done* and *new cycle* (the disk
cannot distinguish them). The driver MUST surface the detected state and its
new-vs-resume interpretation and confirm before proceeding — it must not assume.
This keeps the no-marker design (REQ-ORCH-014) intact: nothing new is persisted;
the driver simply reasons explicitly about the completed-cycle case.

### Orchestrator-Only Work (REQ-ORCH-030)

Some work requires a capability a **leaf pipeline subagent does not have**:
subagent **dispatch**. RS-006 Q1 established that a dispatched subagent's toolset
contains no dispatch tool at all, so it cannot spawn its own subagents. Two kinds
of work therefore MUST run at the orchestrator level, never inside a delegated
pipeline dispatch:

1. **Implement-stage fan-out execution** — provisioning worktrees and dispatching
   one implement subagent per chunk-group is itself dispatch; the orchestrator
   owns it (this is exactly why Design B, not the nested Design A, is the design —
   see §Fan-out Design Resolution).
2. **Spikes or tasks that measure or use dispatch** — e.g. a concurrency spike
   that dispatches parallel probes. RS-006's dispatch-concurrency spike could not
   be delegated to a leaf subagent; the orchestrator ran it directly.

The driver MUST recognize such tasks (those whose execution requires dispatch) and
perform them itself, rather than constructing a pipeline dispatch that would stall
(a leaf subagent cannot proceed) or silently under-deliver. Ordinary stage work
(invoking an `sdd-*` skill, editing files) remains delegable as normal.

_(v5)_ 3. **Routing on the harness signals** (REQ-HARN-019) — `VERDICT:` /
`CHUNK_VERDICT:` / `SCOPE:` interpretation, `RETURN.status` branching, fix /
redo / replan cap arithmetic, repair-packet composition and every gate decision
(stage gate and per-chunk gate) are orchestrator-only; templates tell a subagent
what to *produce*, never what to *decide next* — `harness-return-contract.md`
§Orchestrator Owns Routing, `harness-write-scope.md` §Finding Format.

### Sequential Execution and Implement-Stage Fan-out

Sequential execution is the **default**: every stage runs single-threaded in the
main workspace unless the operator explicitly opts into fan-out at the implement
gate (REQ-ORCH-015). When fan-out is not selected, the implement stage runs
single-threaded in the main workspace exactly like every other stage. Fan-out is
**only** ever available at the implement stage; no other stage fans out.

[Changed 2026-06-04: fan-out promoted from deferred to an ACTIVE design. RS-006
settled the design selection — see "Fan-out Design Resolution" below — so this
section now specifies the orchestrator-owned fan-out (Design B) as a buildable
feature rather than a forward-pointer.]

#### Fan-out Design Resolution

RS-006 ran a live spike to choose between two fan-out designs and settled it
decisively:

- **Design A (nested) — RULED OUT.** A pipeline implement subagent would own the
  fan-out, spawning one sub-subagent per chunk-group (nesting two levels deep).
  RS-006 Q1 proved this is **infeasible in this harness**: a dispatched subagent
  has **no subagent-dispatch tool in its toolset** (only the todo-list `Task*`
  tools exist), so a nested dispatch call is not even constructible. Nesting is
  blocked by tool provisioning, not a runtime depth limit.
- **Design B (orchestrator-owned, one level deep) — SELECTED.** The orchestrator
  owns the fan-out directly: it dispatches the parallel implement subagents itself
  and performs the merges itself. Each fan-out subagent is a **leaf** — it must
  not (and cannot) dispatch sub-subagents (REQ-ORCH-022). RS-006 Q2/Q3 proved the
  pieces Design B needs (worktree creation and sequential conflict-aborting merge)
  all work and can be orchestrator-driven.

This resolves the prior `[high-uncertainty]` subagent-nesting question: nesting is
infeasible, Design B is the only viable design, and it is now the spec.

#### Fan-out Boundary Rule

Fan-out occurs along the **independent branches of the plan's chunk dependency
graph** — not per-milestone (too coarse; milestones are sequential) and not
per-task (too fine) (REQ-ORCH-016). The orchestrator derives the parallel groups
by reading the plan's dependency graph itself, **without modifying
`sdd-implement`** (REQ-ORCH-001, REQ-ORCH-016). Fan-out applies only when the
graph actually contains ≥2 independent chunk branches; if the graph is a single
chain, execution stays sequential even when the operator selected fan-out.

**Precondition (cross-layer).** The orchestrator derives chunk independence from
the plan's **chunk dependency declarations** in `docs/plan.md` — that is where
chunk-level dependencies are expressed. The canonical form is the
`**Depends on**: Chunk N` field defined in plan-management.md; in practice the
live plan also expresses the same relation as chunk-level prose
("Entry criteria: Chunk N complete"), which the orchestrator treats as the
equivalent of that field. These are **chunk-level** declarations, distinct from
the coarser milestone-level Entry/Exit criteria in milestone-plans.md, which must
**not** be used to derive chunk fan-out. The orchestrator parses independence from
the `**Depends on**` field (or its chunk-level prose equivalent). If the plan does
**not** express parseable chunk-level dependencies in either form, fan-out
**degrades to sequential** — the orchestrator never guesses an independence
boundary. This couples the implement stage to the plan's structure: see
`docs/spec/plan-management.md` for the `**Depends on**: Chunk N` field. (uses the
existing `**Depends on**: Chunk N` field; reconfirm at the specs→plan boundary.)

#### Fan-out Opt-in Gate

Fan-out is **opt-in at the implement gate** (REQ-ORCH-024). The orchestrator must
not enable it automatically. At the implement-stage gate the orchestrator presents
fan-out as an explicit operator choice; absent an opt-in, the implement stage runs
sequentially per REQ-ORCH-015. The orchestrator may surface how many independent
chunk-groups the plan's graph yields so the operator can judge whether fan-out is
worthwhile.

When the plan's graph yields only a **single chain** (no independent branches),
the orchestrator tells the operator **at the gate** that fan-out will degrade to
sequential for this plan, so an opt-in that then runs sequentially is expected
rather than surprising. The same notice applies when the plan does not express
parseable chunk-level dependencies (see the Boundary Rule precondition above).

#### Worktree Provisioning and Dispatch (Design B)

When the operator opts in and the graph has independent branches, the orchestrator
runs this sequence (REQ-ORCH-022, REQ-ORCH-023):

1. **Derive groups.** Read the plan's chunk dependency graph; compute the set of
   concurrently-runnable chunk-groups (the independent branches).
2. **Provision worktrees.** For each group, the **orchestrator** (not the subagent)
   provisions one git worktree on its own branch via `git worktree add -b
   <branch> <path> <base>`. Worktree ownership is the orchestrator's, per the
   deliberate narrowing in Q-REQ-G: a single owner keeps provisioning and teardown
   symmetric and avoids orphaned subagent-created worktrees. (RS-006 Q2 showed both
   orchestrator- and subagent-created worktrees work; this spec requires
   orchestrator-provisioned.)
3. **Dispatch one implement subagent per group.** Each dispatch is pinned to its
   assigned worktree path/branch and carries the chunk-group's tasks. Each fan-out
   subagent operates **only** within its assigned worktree/branch and is a leaf —
   it runs `sdd-implement` on its chunk-group and must not fan out further
   (REQ-ORCH-022, REQ-ORCH-023). The non-interactivity contract (REQ-ORCH-007) and
   central ID assignment (REQ-ORCH-008) apply to these dispatches as to any
   pipeline dispatch.
4. **Subagent git identity.** Each fan-out subagent commits using inline
   `git -c user.email=<id> -c user.name=<name> commit ...` identity flags rather
   than writing a shared `.git/config` (REQ-ORCH-027). RS-006 Q2 observed that a
   dispatched subagent's command sandbox blocks writes to the main repo's
   `.git/config` ("Operation not permitted"); inline `-c` flags sidestep this and
   let commits, merges, and branch operations succeed. The orchestrator must not
   instruct subagents to write `.git/config`.
5. **Await returns.** The orchestrator waits for all fan-out subagents to return
   before beginning the merge sequence.

#### Sequential Merge to Main

After the fan-out subagents return, the orchestrator merges the worktree branches
**sequentially** into `main`, completing all merges **before** the implement-stage
review runs (REQ-ORCH-025). The review therefore operates on the **merged state**,
never on individual unmerged branches. The merge loop, for each branch in turn:

```
git merge --no-edit <branch>
  exit 0  → merged cleanly (fast-forward or auto-merge); continue to next branch
  exit ≠0 → conflict; enter conflict handling (below)
```

Because merges are one-at-a-time, each branch's merge is either fully applied or
fully unwound; partial-merge corruption across branches cannot occur.

**Worktree teardown.** Once a worktree branch is successfully merged into `main`,
the orchestrator **removes that worktree** (`git worktree remove <path>`) and
**deletes its branch** (`git branch -d <branch>`), completing the lifecycle
ownership that Q-REQ-G's rationale ("a single owner ... avoids orphaned
worktrees") promised: the same owner that provisioned the worktree tears it down.
Redo worktrees (`<branch>-redo`, per Merge-Conflict Handling) are torn down the
same way after their merge. Teardown happens before the implement-stage review so
the review sees a clean repository with only `main`.

#### Merge-Conflict Handling

On a non-zero `git merge` exit (REQ-ORCH-026):

1. **(Optional, best-effort) auto-resolve.** The orchestrator MAY first attempt
   automatic resolution of the conflict. This is explicitly best-effort and **not
   guaranteed** — it must never be the only path. A conflict that auto-resolves
   cleanly (no abort) is a normal success: the merge completes and the loop
   continues to the next branch, exactly as for a clean `exit 0` merge.
2. **Guaranteed fallback — abort and redo by re-derivation.** If auto-resolution
   is not attempted or does not cleanly succeed, the orchestrator runs `git merge
   --abort` (which cleanly restores the working tree to the last good merged
   state) and then **redoes the offending chunk-group by re-derivation**, not by
   replaying a stale patch. Concretely:
   - Provision a **fresh worktree re-branched from the now-updated `main`** (which
     already contains the earlier branches merged so far) via `git worktree add
     -b <branch>-redo <path> main`.
   - Re-dispatch an implement subagent (a leaf, per REQ-ORCH-022) to re-run
     `sdd-implement` for that chunk-group **in the fresh worktree**. Because the
     work is re-derived against updated `main`, the already-merged changes are
     integrated by re-derivation rather than by replaying the original patch —
     replaying the stale patch would reproduce the very same conflict.
   - Re-attempt `git merge --no-edit <branch>-redo` for that chunk-group.

   RS-006 proved only the `abort` mechanism end-to-end, not the redo; the
   re-derivation contract above is the spec's design choice for how the redo is
   performed (see Q-IMPL-1).
3. **Convergence / guaranteed termination.** If a chunk-group **still** conflicts
   after re-derivation against the updated `main`, that is proof the chunk-groups
   were **not truly independent** — i.e. a fan-out boundary-selection error, since
   genuinely independent branches cannot conflict after re-derivation against a
   `main` that already contains the other branch. The orchestrator then **falls
   back to running the remaining/affected chunk-groups sequentially** (one
   implement run re-branched from `main`, merged, then the next), which cannot
   conflict by construction. This guarantees termination: each round either merges
   cleanly or proves non-independence and collapses to the sequential path, which
   always terminates.
4. **No corruption invariant.** The abort-and-redo path must **never corrupt or
   unwind already-merged work.** Because merges are sequential and earlier merges
   are already committed, a `git merge --abort` unwinds only the single failing
   merge (RS-006 Q3 proved this end-to-end: clean tree restoration, no loss of
   prior merges). The redo worktree is re-branched from that intact `main`, so the
   already-merged branches are preserved and inherited, never replayed or undone.

Conflict detection relies on the `git merge` exit code as the contract signal
(RS-006 Q3 also confirmed `git status --porcelain` `AA` markers and `<<<<<<<`
file markers as corroborating signals).

**Q-IMPL-1 (redo mechanism — design decision):** The redo after `git merge
--abort` is performed by **re-deriving** the chunk-group in a worktree re-branched
from the updated `main`, not by replaying the failing subagent's original returned
patch. Rationale: replaying the stale patch would reproduce the identical conflict
(the patch was generated against the old base), whereas re-derivation lets the
implement subagent integrate the already-merged changes. RS-006 only verified the
`abort` step, so this redo contract is a spec-level design choice flagged here for
implementation; the convergence rule (fall back to sequential on a repeat
conflict) bounds it and guarantees termination. REQ-ORCH-026 was reconciled to
match this contract — it no longer says the redo may "re-use the subagent's
returned output"; it now mandates re-derivation in a re-branched worktree.

#### Dispatch Concurrency

**Resolved by spike (REQ-ORCH-028).** Whether the harness runs a batch of fan-out
implement dispatches **truly concurrently** rather than serializing them was the
fan-out design's last open question. RS-006 ran the dispatch-concurrency spike on
2026-06-05 (`docs/spikes/dispatch-concurrency.md`) and resolved it **favorably at
medium confidence**: two orchestrator-dispatched probe subagents issued in a single
message were **observed running concurrently** — alive across the same overlapping
wall-clock window and ending within 0.1 s of each other, a pattern inconsistent with
serialization. Confidence is **medium**, not high, because the spike's ~4s probe
workload sits inside a ~426s agent lifetime, so the absolute timings are
latency-dominated; the simultaneous end and shared lifetime remain strong evidence.

- **Why it never threatened correctness:** the fan-out design (per-worktree
  isolation + sequential conflict-aborting merge) is correct **either way**. Only
  the **wall-clock speedup** was ever at stake — serialized dispatch would still
  yield correct output, just with no time savings.
- **When it matters:** only when ≥2 chunk-groups are concurrently runnable; with a
  single runnable group the question is moot.
- **Outcome:** concurrency was observed, so fan-out delivers wall-clock speedup
  where it holds; no speedup-guarantee caveat needs to block the feature. Because
  confidence is medium, downstream prose attributes the speedup to the spike's
  observed result rather than asserting it as established fact.

This was the **one remaining uncertainty** in the fan-out design (RS-006 Open
Questions; RS-005 Q4), now resolved (see `docs/spikes/dispatch-concurrency.md`).

### Packaging

The driver is a single skill at `skills/sdd-orchestrate/SKILL.md`, kept under the
project's ~1000-line guideline (REQ-ORCH-019). The kickoff-writer is not a separate
skill — it is a contained, non-reusable sub-task of the driver. The two dispatch
prompt templates (pipeline and review) live in
`skills/sdd-orchestrate/references/dispatch-templates.md` to keep the body lean;
moving the bulkiest component out is what makes the ~1000-line target comfortable
(RS-005 Q5; existing skills run 162–291 lines).

### User Documentation

`SKILL.md` is Claude-facing operational instruction. Operators also need a
human-facing guide (REQ-ORCH-020), shipped at
`skills/sdd-orchestrate/USAGE.md`. It must cover: what the driver is and when to
use vs. skip; each phase explained for an operator; a complete worked example
(one idea → DISCUSS → KICKOFF → per-stage pipeline→review→gate → DONE); the
isolation guarantees and why they matter; **installation** via the
`~/.claude/skills/<name>` → repo `skills/<name>` symlink convention this project
uses for every SDD skill; troubleshooting, including the blocked-subagent-write
labeled-content fallback observed live in RS-005; and the v1 limitations
(research-entry, sequential, no fan-out).

The project README (`README.org`) introduces the driver and the SDD suite, links
the operator guide, and documents the `~/.claude/skills/` symlink install
convention so a new adopter can install the skills (REQ-ORCH-021).

### v5 Harness Hardening (REQ-ORCH-034)

_(added 2026-09-17, RS-008)_ The harness-hardening cycle layers deterministic
loop control and decoupled verification onto the driver without changing its
phases, artifacts or gate vocabulary. The designs live in four sibling specs:

- `harness-loop-control.md` — fix-loop cap (`iteration N of MAX`, default 3),
  replan re-entry cap derived from `-replan-` archives, `Budget:` slot and
  `budget_consumed`, attempt ledger + oscillation rule, circuit-break checkpoint
  in the plan's blocked-task note, no-new-artifact invariant.
- `harness-return-contract.md` — structured `RETURN:` block from every leaf,
  one-line `failures[]`, `{repair_packet}` slot replacing free-form
  `{review_findings}` on fix re-dispatches, `VERDICT:` token and branching,
  pruned re-dispatch state, orchestrator-owned routing.
- `harness-chunk-verifier.md` — fresh read-only chunk-close verifier
  (`CHUNK_VERDICT:`), per-chunk sequential implement dispatch, verifier before
  merge under fan-out.
- `harness-write-scope.md` — declared `Write scope:` per dispatch, three-command
  observation, `SCOPE: CLEAN | VIOLATION` gate text, commit ownership, snapshot
  ordering.

**Gate text order (REQ-ORCH-034).** The signals surface in the order they are
produced: (1) the leaf's `RETURN.status` and `budget_consumed` against the
dispatched `Budget:`; (2) the write-scope block ending in `SCOPE:`; (3) for the
implement stage, the chunk's `CHUNK_VERDICT:`; **[per-chunk gate]** — for the
implement stage signals (1)–(3) are shown per chunk at a lightweight per-chunk
gate, with `Redo: N of REDO_MAX`; then, after all chunks, (4) the parsed review
`VERDICT:` and (5) when a loop is active, `iteration N of MAX` or the replan
re-entry count against its cap — at the **stage gate**. For a non-implement
stage (1), (2), (4), (5) appear together at the stage gate. The stage-gate
decision vocabulary stays `proceed │ loop-back-to-fix │ stop`, extended only by
the scope options `revert path | accept & widen scope`; the per-chunk gate
offers `proceed │ fix │ stop`. All of it is ephemeral (REQ-ORCH-013).

**Per-chunk gate (implement stage, sequential).** After each chunk's implement
dispatch returns: the orchestrator runs the write-scope check, dispatches the
chunk verifier, then shows the operator a compact block — the `SCOPE:` line,
the `CHUNK_VERDICT:` line, `RETURN.status`, files changed — with the choices
**proceed** (the orchestrator commits the chunk) │ **fix** (re-dispatch the
chunk with a repair packet; counts toward the per-chunk redo cap) │ **stop**.
The single implement-stage review gate remains once, after all chunks. Under
fan-out the equivalent happens per leaf before its merge, with no commit by the
orchestrator (the leaf already committed on its branch). Stated identically in
`harness-chunk-verifier.md` §Sequencing — Sequential Mode and
`harness-write-scope.md` §Commit Ownership / §Snapshot Ordering:

```
Per-chunk gate — implement dispatch #2 (Chunk 2: Reconciliation)   [fan-out: leaf wt-g1 / branch fanout-g1]
  RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 22, test_runs: 3}  vs  Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs
  SCOPE: CLEAN                                    # full write-scope block above when VIOLATION
  CHUNK_VERDICT: PASS                             # verifier findings (Check 1 / Check 3 / Gates) listed above when FAIL
  Files changed  : src/recon/engine.py M, tests/test_recon.py M, docs/plan.md M
  Redo           : 0 of 3 (per-chunk redo counter)
  Options: proceed (orchestrator commits the chunk) │ fix (re-dispatch Chunk 2 with a repair packet; counts toward the per-chunk redo cap) │ stop
```

Rendering procedures live in `skills/sdd-orchestrate/references/return-contract.md`
and `references/write-scope.md`; `SKILL.md` §The gate carries the ordered list
and pointers only. §Gate Protocol's `loop-back-to-fix` row is extended by the
repair packet (findings + paths by construction) in place of a free-form
findings slot; §Orchestrator-Only Work is extended by the routing principle
(REQ-HARN-019) — both marked `(v5)` in place above. The ordering clarification
against REQ-ORCH-034's single-gate wording is recorded in
`harness-chunk-verifier.md` Open Questions #3.

## Verification

### Manual
- Confirm the skill body implements DISCUSS → KICKOFF → LOOP → DONE in order.
- Inspect a constructed review dispatch prompt and confirm it contains only the
  permitted inputs (repo root, deliverable path, non-research upstream path,
  "invoke sdd-review") and none of the prohibited inputs.
- Inspect a constructed research-stage review dispatch and confirm the upstream
  path is omitted.
- Inspect a constructed pipeline dispatch and confirm the non-interactivity
  clause, front-loaded decisions, pinned IDs, and absolute cwd are present.
- Run the driver end-to-end on a small idea and confirm a gate appears after each
  stage with proceed │ loop-back-to-fix │ stop options.
- Confirm no `docs/reviews/` directory is created and `docs/handoff/kickoff.md`
  is git-tracked.
- Opt into fan-out at the implement gate on a plan whose chunk graph has ≥2
  independent branches; confirm the orchestrator provisions one worktree/branch
  per group, dispatches one leaf implement subagent per group, and that no fan-out
  subagent attempts a sub-dispatch.
- Decline fan-out (or run a single-chain plan); confirm the implement stage runs
  single-threaded in the main workspace.
- Inspect a fan-out subagent's commits; confirm they used inline
  `git -c user.email=... -c user.name=...` and that no shared `.git/config` was
  written by a subagent.
- After fan-out subagents return, confirm all branches are merged sequentially into
  `main` and the implement-stage review runs on the merged state (not on an
  unmerged branch).
- After each branch merges, confirm the orchestrator removes the worktree
  (`git worktree remove`) and deletes its branch, leaving no orphaned worktrees or
  branches before the implement-stage review.
- Force a merge conflict (overlapping files across two groups). Confirm that on a
  clean best-effort auto-resolve the merge simply completes (no abort, PASS); and
  that on a non-clean conflict the orchestrator runs `git merge --abort`, then
  redoes the offending chunk-group **by re-running `sdd-implement` in a worktree
  re-branched from the updated `main`** (not by replaying the old patch), and that
  previously-merged branches remain intact.
- Force a chunk-group to conflict **again** after re-derivation (genuinely
  overlapping work mis-classified as independent); confirm the orchestrator falls
  back to running the affected chunk-groups sequentially and that the run
  terminates.
- On a single-chain plan (or a plan without parseable chunk-level dependencies),
  confirm the orchestrator tells the operator at the gate that fan-out will degrade
  to sequential.

### Acceptance Criteria
- [ ] Skill is a driver that dispatches `sdd-*` skills and modifies none of them (REQ-ORCH-001)
- [ ] Skill body implements four ordered phases DISCUSS/KICKOFF/LOOP/DONE (REQ-ORCH-002)
- [ ] DISCUSS reuses the brainstorming process before KICKOFF (REQ-ORCH-003)
- [ ] KICKOFF writes `docs/handoff/kickoff.md` as the only new on-disk artifact type, git-trackable (REQ-ORCH-004)
- [ ] v1 emits a research kickoff and starts the loop at research; non-research entry is excluded (REQ-ORCH-005)
- [ ] Each stage issues two separate subagent dispatches (pipeline, review) (REQ-ORCH-006)
- [ ] Pipeline dispatch front-loads decisions and includes a non-interactivity clause forbidding questions and fabricated consent (REQ-ORCH-007)
- [ ] Orchestrator assigns IDs centrally and passes them verbatim to pipeline subagents (REQ-ORCH-008)
- [ ] Review dispatch carries only the permitted paths-only input set and excludes all prohibited inputs (REQ-ORCH-009)
- [ ] Research-stage review dispatch omits the upstream/kickoff path; later stages supply it (REQ-ORCH-010)
- [ ] A human gate follows every stage with proceed │ loop-back-to-fix │ stop; no auto-advance (REQ-ORCH-011)
- [ ] Fix loop re-dispatches the pipeline with only findings + artifact paths, then re-reviews (REQ-ORCH-012)
- [ ] Review verdicts are never written to disk; no `docs/reviews/` directory (REQ-ORCH-013)
- [ ] Resume derives loop position from existing phase detection; no marker file, no authoritative loop log (REQ-ORCH-014)
- [ ] Sequential execution is the default; non-opted-in implement runs single-threaded in the main workspace (REQ-ORCH-015)
- [ ] Fan-out boundary is the plan's independent chunk-dependency branches (not per-milestone, not per-task); orchestrator derives groups by reading the graph without modifying `sdd-implement`; applies only when ≥2 independent branches exist (REQ-ORCH-016)
- [ ] Orchestrator derives chunk independence from the plan's chunk dependency declarations in `docs/plan.md` — the `**Depends on**: Chunk N` field (or its chunk-level "Entry criteria: Chunk N complete" prose equivalent), not milestone-level Entry/Exit criteria; if the plan lacks parseable chunk-level dependencies, fan-out degrades to sequential and never guesses a boundary (REQ-ORCH-016; see `docs/spec/plan-management.md`)
- [ ] Fan-out is orchestrator-owned, one level deep: orchestrator dispatches the parallel implement subagents itself and each fan-out subagent is a leaf that does not dispatch sub-subagents; Design A (nested) is ruled out infeasible (REQ-ORCH-022)
- [ ] Orchestrator provisions one git worktree on its own branch per concurrently-runnable chunk-group and pins each implement subagent to its worktree/branch (REQ-ORCH-023)
- [ ] Fan-out is opt-in at the implement gate and never enabled automatically; declining runs the stage sequentially (REQ-ORCH-024)
- [ ] When the plan yields a single chain (or no parseable chunk dependencies), the orchestrator tells the operator at the gate that fan-out will degrade to sequential (REQ-ORCH-024)
- [ ] After a worktree branch is merged to `main`, the orchestrator removes the worktree (`git worktree remove`) and deletes its branch, leaving no orphaned worktrees/branches (REQ-ORCH-023, Q-REQ-G)
- [ ] After fan-out subagents return, worktree branches are merged sequentially into `main` and all merges complete before the implement-stage review runs on the merged state (REQ-ORCH-025)
- [ ] On a conflict that is NOT cleanly auto-resolved, the orchestrator runs `git merge --abort` and redoes the offending chunk-group; best-effort auto-resolution is optional and may precede the fallback; a clean auto-resolve (no abort) counts as PASS; already-merged work is never corrupted (REQ-ORCH-026)
- [ ] The redo after `git merge --abort` is performed by re-deriving the chunk-group in a worktree re-branched from the updated `main` (re-running `sdd-implement`), not by replaying the stale patch (REQ-ORCH-026, Q-IMPL-1)
- [ ] If a chunk-group still conflicts after re-derivation against updated `main`, the orchestrator treats it as a fan-out boundary error and falls back to running the affected chunk-groups sequentially, guaranteeing termination (REQ-ORCH-026)
- [ ] Fan-out subagents commit with inline `git -c user.email=... -c user.name=...` identity flags; no subagent writes a shared `.git/config` (REQ-ORCH-027)
- [ ] Dispatch-concurrency is resolved by the RS-006 spike (`docs/spikes/dispatch-concurrency.md`, 2026-06-05): orchestrator-dispatched subagents were observed concurrent at medium confidence; design holds whether dispatches run concurrently or serialized and correctness is unaffected; only wall-clock speedup depends on it, and downstream prose attributes the speedup to the spike's observed (medium-confidence) result rather than asserting it as fact (REQ-ORCH-028)
- [ ] Replan triggers surface to the operator as gate events, not silently absorbed (REQ-ORCH-017)
- [ ] A reject verdict with no actionable findings pauses for an operator decision (REQ-ORCH-018)
- [ ] Skill is a single `SKILL.md` under ~1000 lines with templates in `references/` (REQ-ORCH-019)
- [ ] Operator guide `skills/sdd-orchestrate/USAGE.md` exists covering when-to-use, the four phases, a complete worked example, isolation, installation via `~/.claude/skills/` symlink, troubleshooting (write fallback), and v1 limitations (REQ-ORCH-020)
- [ ] README introduces `sdd-orchestrate`, links the operator guide, and documents the `~/.claude/skills/` symlink install convention (REQ-ORCH-021)
- [ ] On entry the driver classifies state as resume / done / new-cycle; when the prior cycle is `verification.md` status pass and the operator brings a new idea, it runs DISCUSS and overwrites `docs/handoff/kickoff.md` rather than reporting DONE; it surfaces the interpretation and confirms before proceeding (REQ-ORCH-029)
- [ ] The driver performs dispatch-requiring work (implement-stage fan-out execution, parallel-dispatch spikes) at the orchestrator level and does not delegate it to a leaf pipeline subagent (which has no dispatch tool) (REQ-ORCH-030)
- [ ] Research is the default entry (no upstream artifacts → research kickoff, loop starts at research) (REQ-ORCH-005)
- [ ] Non-research entry is supported at requirements/specs/plan/implement when upstream is approved; verify is not an entry point; distinct from resume (REQ-ORCH-031)
- [ ] On entry the driver auto-detects the proposed entry stage via phase detection, presents and confirms it (operator may override earlier), and validates the upstream is approved — routing to the earliest incomplete upstream if not; never guesses without confirmation (REQ-ORCH-032)
- [ ] A non-research entry writes an entry kickoff to `docs/handoff/kickoff.md` (scope + entry stage + assumed-approved upstream, not research questions); DISCUSS still runs first; kickoff remains the only new artifact (REQ-ORCH-033, REQ-ORCH-004)
- [ ] Markdown well-formed; frontmatter valid; kebab-case skill name (project quality checks)

## Implementation Questions

### Q-IMPL-HARNESSP2-008: verify-gate signal order, pause family, entry/DONE gc steps and provisioning base
**Tier**: 2 (spec ambiguity)
**Spec reference**: §v5 Harness Hardening (gate text order), §Gate Protocol, §Driver Phases, §Sequential Execution and Implement-Stage Fan-out
**Decision**: Extended by the harness-p2 specs (amendments 2026-09-17): the verify stage gate order becomes `RETURN.status` → `SCOPE:` → `RED_VERDICT:` → `VERDICT:` → counters, with options `fix (RED_BREAK packet) | accept (record) | stop` per BROKEN finding and the opt-in `red team: off | on` (`adversarial-verify.md`); the stage-gate pause family gains `REVIEW: CONTRADICTION` with `accept round N+1 (fix) | accept round N (proceed, note) | third opinion | stop` (`arbitrated-handoff.md`); entry runs `tools/sdd-gc.py --report` before the workstream picker and DONE renders its findings with `record | ignore` (`drift-sweep.md`); sequential and fix worktrees are provisioned at the branch tip the leaf is told to reach (`dispatch-snapshot-base.md`); `TELEMETRY:` lines appear once per gate when relevant (`telemetry.md`). REQ-ORCH-011/-013/-014 and the never-auto-advance rule are unchanged (`evaluation.md`).
**Rationale**: The driver spec keeps its phases and vocabulary; each extension is owned by the spec that defines its token.
**Date**: 2026-09-17 (harness-p2 specs stage)
