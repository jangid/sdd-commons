---
name: sdd-orchestrate
description: >
  Driver skill that runs the nine SDD phase skills as a single-operator
  orchestration loop with per-stage external review. Drives DISCUSS → KICKOFF →
  LOOP → DONE: brainstorm an idea to shared understanding, write a research
  kickoff, then for each stage dispatch an isolated pipeline subagent and an
  isolated review subagent, gating with the operator after every stage. Use when
  you want to run a whole SDD cycle end-to-end with built-in external review. Do
  NOT use to run a single phase (invoke that sdd-* skill directly) or to review
  an artifact in isolation (use sdd-review).
---

# SDD: Orchestration Driver

You are the **orchestrator**. You drive the full SDD cycle from a single human
session, dispatching each pipeline stage and each review as separate subagents,
and gating with the operator after every stage.

## What This Is

`sdd-orchestrate` is a **driver**, not a tenth phase skill. It composes the nine
existing `sdd-*` skills (research, requirements, specs, plan, implement, verify,
replan, migrate, review) and **never reimplements their logic**. Stage work —
including each skill's own phase detection and staleness handling — is performed
by dispatching the corresponding `sdd-*` skill; you relay that output rather than
duplicating it. You own only orchestration: sequencing stages, constructing
isolated dispatches, and mediating operator gates.

Isolation is **by construction**. Each pipeline stage and each review run as a
**separate subagent** with a fresh context window. A freshly dispatched subagent
has no shared window through which your reasoning could leak — a stronger
guarantee than two human terminal sessions. (Honest caveat: a fresh subagent
still inherits repo-level context — `CLAUDE.md`, project memory. The guarantee
covers the working session's reasoning and drafts, not repo documentation.)

**Scope**: research-entry **by default**, sequential by default. With no upstream
artifacts the kickoff is a research kickoff and the loop starts at research; when
approved upstream artifacts already exist, the operator may start **mid-pipeline**
(see §Entry Points). Implement-stage **fan-out is active** as an opt-in mode at
the implement gate (see §Execution Model); every other stage is always sequential.

## Phase Detection

The driver introduces **no loop-position marker**. On entry — including re-entry
in a fresh session mid-loop — derive the current loop position from the existing
SDD artifacts, reusing the stage skills' own phase detection:

**Upgrade offer (entry, all markers).** Before deriving loop position, read
`docs/.sdd-version` and compare it to the **latest version the installed skills
support** (currently `4` — the highest version `sdd-migrate` can migrate to). If the
project's marker is **behind** the latest (missing/pre-versioning, `2`, or `3`), tell
the operator an upgrade is available and **offer to run `/sdd-migrate` first** — e.g.
a marker-`3` project can adopt the v4 multi-workstream layout. This offer is
**informational and non-forcing** and is the single place a behind-version project is
nudged toward migration:

- If the operator **accepts**, hand off to `sdd-migrate` (which migrates up through
  the latest version), then re-derive phase from the migrated layout and continue.
- If the operator **declines** — or the session is non-interactive — proceed on the
  current marker with downstream behavior **unchanged**; the offer alters no cycle
  mechanics, so the "behavior UNCHANGED" guarantees below still hold for anyone who
  does not migrate.
- If the marker **already equals** the latest, say nothing and continue.

This generalizes beyond v3→v4: the driver offers migration **whenever the detected
marker is behind the latest supported version**. (REQ-WS-030.)

**Workstream & version gate (v4).** The driver accepts an optional `workstream`
argument that defaults to `default`, threaded through to every dispatched stage
skill. `docs/.sdd-version` is the **sole** layout gate:

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Ignore the workstream
  argument and derive loop position from the flat artifacts exactly as the table
  below states — `docs/handoff/kickoff.md`, `docs/plan.md`, `docs/verification.md`.
  Never read `docs/ws/`.
- **Marker is `4` (workstream-aware layout).** Resolve `ws` = the workstream
  argument (default `default`), set `base = docs/ws/<ws>/`, and read that
  workstream's **execution artifacts** — `kickoff.md`, `plan.md`,
  `verification.md`, `plan-history/` — from `base` (so the table below maps
  `docs/handoff/kickoff.md` → `docs/ws/<ws>/kickoff.md`, `docs/plan.md` →
  `docs/ws/<ws>/plan.md`, `docs/verification.md` → `docs/ws/<ws>/verification.md`),
  never from flat `docs/`. The **shared corpus** stays at its top-level paths:
  `docs/research/`, `docs/requirements/` (incl. aggregated `traceability.md`),
  `docs/spec/`. Omitting the argument resolves the implicit `default` workstream,
  so solo use needs no naming. Enumerating `docs/ws/<id>/` to present a workstream
  picker is specified separately in `docs/spec/ws-orchestration.md`; this step-0
  gate only establishes the workstream argument and marker-`4` execution-artifact
  rooting. Full layout contract: `docs/spec/ws-layout.md`.


| On disk | Loop position |
|---------|---------------|
| no `docs/handoff/kickoff.md` | before KICKOFF — run DISCUSS |
| kickoff exists, its `research_id` spike has no Complete findings | at the research stage |
| research done, requirements `Draft`/missing | at the requirements stage |
| requirements `Approved`, specs missing/stale | at the specs stage |
| specs `Approved`, no `docs/plan.md` (or stale) | at the plan stage |
| plan has incomplete tasks | at the implement stage |
| plan complete, no/failing `docs/verification.md` | at the verify stage |
| `docs/verification.md` status pass | at DONE (pending operator approval) |

**Entry kickoffs shift the table's origin.** If the kickoff on disk is an
**entry kickoff** (§Entry Points — it records an entry stage and which upstream
is assumed approved), the stages before its entry stage are *intentionally
absent*: do not derive "at the research stage" from missing research artifacts.
Read the kickoff's recorded entry stage and derive loop position from that stage
onward only.

Tell the operator the detected position and confirm before proceeding. A pending
or prior review leaves no on-disk trace by design — it is **reproduced** by
re-dispatching the review subagent against the current artifacts (reviews are
read-only and idempotent).

**New cycle vs. resume.** One state is ambiguous: when the prior cycle is
**complete** (`docs/verification.md` with `status: pass`), the same on-disk state
that means "DONE — nothing to resume" is also the starting point for the *next*
feature. Classify entry as one of:

- **resume** — the latest cycle is mid-loop (a stage incomplete/stale) → continue it;
- **done** — the latest cycle is `status: pass` and the operator has no new idea → report DONE;
- **new cycle** — the latest cycle is `status: pass` **and** the operator brings a new idea in DISCUSS → run DISCUSS and **overwrite** `docs/handoff/kickoff.md` at KICKOFF.

The disk cannot distinguish *done* from *new cycle* — **operator intent** does.
Do not silently report the prior DONE and stop when the operator is opening new
work; surface your new-vs-resume interpretation and confirm. This adds no new
marker (REQ-ORCH-014 stands) — it is just explicit reasoning about the
completed-cycle case.

**Marker-`4` gate for done-vs-new-cycle.** `docs/.sdd-version` is the sole gate for
how this ambiguity is resolved:

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** The repo holds a single
  flat cycle (`docs/handoff/kickoff.md`, `docs/plan.md`, `docs/verification.md`) and
  the *done* vs *new cycle* choice is resolved by the **single global operator
  intent** described just above — verbatim, unchanged.
- **Marker is `4`: resolved PER WORKSTREAM via the picker (REQ-WS-029), not by a
  global intent.** Phase is now a function of `(repo, workstream)`, so there is no
  single repo-wide "done" state to appeal to — several workstreams may sit at
  different phases at once. The **Workstream Picker** (§Workstream Picker) surfaces
  each workstream with its detected phase and resolves *done vs new cycle* **within
  the selected workstream's context**: selecting a workstream whose phase is DONE
  (its `docs/ws/<id>/verification.md` is `status: pass`) offers "start a new cycle in
  **this** workstream", while a genuinely new idea creates a **new** workstream id —
  never by appealing to one global operator intent.

## Workstream Picker

`docs/.sdd-version` is the **sole** gate for whether the driver opens with a
workstream picker:

- **Marker is not `4` (v3 or earlier): NO picker — behavior UNCHANGED.** There is no
  `docs/ws/` under marker `3`; the driver drives the single flat cycle exactly as
  today: derive loop position from the flat artifacts (§Phase Detection table),
  resolve done-vs-new-cycle by the single global operator intent (§New cycle vs.
  resume), and use the one `docs/handoff/kickoff.md`. Skip this whole section.
- **Marker is `4`: present a workstream picker at entry (REQ-WS-029).** Because phase
  is a function of `(repo, workstream)`, the driver cannot infer a single active
  cycle from the repo — several workstreams may be live at once — so it must ask which
  workstream the operator is driving before entering the LOOP.

### Present existing workstreams (marker `4`, REQ-WS-029)

Enumerate the `docs/ws/<id>/` directories (each directory is one workstream) and, for
**each**, show a row:

| Field | Source |
|-------|--------|
| id | the `docs/ws/<id>/` directory name |
| description | the description recorded in `docs/ws/<id>/kickoff.md` (kickoff is per-workstream, per `ws-migration.md`) |
| detected phase | that workstream's phase, computed by the §Phase Detection gate with `ws = <id>` (`base = docs/ws/<id>/`) |

Then let the operator **select an existing workstream or create a new one**. Two
workstreams sitting at different phases (e.g. `ISSUE-42` at implement, `ISSUE-57` at
plan) are **both** listed with their own phase, so the operator names the one they are
driving rather than the driver guessing.

**Solo degenerates to a picker of one (REQ-WS-020).** In a repo whose only workstream
is `default` (the migrated/solo case), the picker collapses to that single workstream
with **no naming ceremony** — it is a picker of one, not a prompt the solo operator
must answer. Resolve `default` and proceed exactly as a solo v3 cycle would feel.

### Resolve done-vs-new-cycle per workstream (REQ-WS-029)

Disambiguation is **per workstream**, never by a single global operator intent
(§New cycle vs. resume, marker-`4` gate):

- **Select an existing workstream** → drive it from its detected phase. If that phase
  is **DONE** (`docs/ws/<id>/verification.md` is `status: pass`), offer **"start a new
  cycle in this workstream"** — resolved inside that workstream's context (a new cycle
  overwrites `docs/ws/<id>/kickoff.md` at KICKOFF, as §KICKOFF describes), or report
  DONE if the operator has no new idea for it.
- **Create a new workstream** for a genuinely new idea → mint a **new workstream id**
  (conventionally the branch/issue key, per `ws-integration.md`) and enter the uniform
  research-entry lifecycle below. A new idea is a new id, not a "new cycle" appended to
  someone else's workstream.

### Uniform research-entry lifecycle for a new workstream (REQ-WS-024)

Every **new** workstream begins at the **research stage**, regardless of how much
shared corpus already exists — there is **no per-workstream mid-pipeline entry variant
to select at creation** (mid-pipeline entry, §Entry Points, is a marker-`3`
single-cycle concept; a marker-`4` new workstream always starts at research). Creating
a new workstream:

1. mints the workstream id and creates/uses its branch (`ws-integration.md`);
2. **positions its loop at research** (§Phase Detection: `docs/ws/<id>/kickoff.md`
   exists and research is **not yet complete for `<id>`** → the research stage).
   Research is complete for this cycle when the kickoff's recorded `research_id`
   spike (`docs/research/RS-<id>-NNN-*/findings.md`) exists with
   `status: Complete` (an explicit early-exit finding counts as Complete) —
   scoped to the kickoff's spike, not "any `RS-<id>-*`", so a prior cycle in the
   same workstream never masks a new cycle's research stage. Research findings are **shared**
   — they live in the common `docs/research/` tree, ws-keyed **only** by the
   `RS-<WS>-` id prefix (there is **no** `docs/ws/<id>/research/` dir); the
   workstream owns `docs/ws/<id>/` kickoff, plan, and verification;
3. seeds `docs/ws/<id>/kickoff.md` as a research kickoff (§KICKOFF).

Uniformity keeps the lifecycle one predictable shape for every workstream. It stays
cheap because the research stage **early-exits fast** when the shared corpus already
covers the new workstream's needs: the research pipeline subagent records a fast,
explicit early-exit ("covered by shared corpus — no new spike") rather than running a
full spike, then the loop advances (REQ-WS-025 — see `sdd-research` §Research
Early-Exit and `docs/spec/ws-orchestration.md`).

## Entry Points

Research is the **default** entry. But when approved upstream SDD artifacts
already exist, the operator may start the loop **mid-pipeline** (REQ-ORCH-031) at
**requirements, specs, plan, or implement**. Research is the default; **verify is
not an entry point** (verifying an existing project is just invoking `sdd-verify`
directly — no loop). 

**Marker-`4` scope.** Non-research mid-pipeline entry described in this section is a
**marker-`3` single-cycle** concept. Under marker `4` a **new** workstream always
begins at research (uniform research-entry, §Workstream Picker → REQ-WS-024) — there
is no per-workstream mid-pipeline entry variant to select at its creation; selecting
an **existing** marker-`4` workstream simply resumes it from its detected phase via
the picker, which is resume, not entry.

**Entry ≠ resume.** *Resume* continues a cycle **this driver** started (its
kickoff + partial artifacts are on disk — see §Phase Detection). *Non-research
entry* begins a fresh loop over artifacts produced **outside** this driver — e.g.
the operator hand-wrote requirements or ran `sdd-requirements` directly and now
wants the gated loop for the rest.

**Detect → confirm → validate (REQ-ORCH-032).** On a mid-pipeline entry:
1. **Auto-detect** the proposed entry stage with the same phase detection above —
   the furthest-complete *approved* upstream artifact → the next stage.
2. **Present and confirm** it with the operator before proceeding. The operator
   may override to an *earlier* stage (never a later one whose upstream is unmet).
3. **Validate** the chosen stage's upstream exists and is approved/complete. If
   not, do **not** start there — route to the earliest incomplete upstream stage
   and tell the operator why.

Never silently guess an entry stage — confirmation is mandatory.

**Entry kickoff (REQ-ORCH-033).** KICKOFF still writes `docs/handoff/kickoff.md`
(it stays the only new artifact, git-tracked), but as an **entry kickoff**: it
records the *scope of the change*, the *entry stage*, and *which upstream is
assumed approved* — not research questions. DISCUSS still runs first. From the
entry stage on, the LOOP is identical to a research-entry cycle.

## The Four Phases

```
DISCUSS  — converge with the operator on the idea (scope + open questions)
   ↓
KICKOFF  — write docs/handoff/kickoff.md (a research kickoff for v1)
   ↓
LOOP     — for each stage in [research, requirements, specs, plan, implement, verify]:
             1. PIPELINE subagent → invokes sdd-<stage>, writes artifact(s) to disk
             2. REVIEW subagent   → fed artifact paths only; invokes sdd-review;
                                     returns a tiered verdict
             3. GATE (operator)   → surface the verdict; wait:
                                     proceed │ loop-back-to-fix │ stop
             4. if fix → re-dispatch PIPELINE with findings + paths only; goto 2
   ↓
DONE     — the verify stage passes review AND the operator approves
```

## DISCUSS

Before writing any kickoff, reach a shared understanding of the idea with the
operator. **Reuse the brainstorming process** — invoke a brainstorming skill if
one is available in the session; otherwise run the equivalent inline:
explore intent, challenge assumptions, surface scope boundaries, and capture the
open questions the research stage should answer. Do not jump straight to a kickoff or to
implementation — converge first.

Exit DISCUSS when the operator and you agree on: what the idea is, what is in and
out of scope, and the concrete questions worth researching.

## KICKOFF

Write the converged discussion into the cycle's kickoff file. This is the
**only** new on-disk artifact type the driver introduces; every other stage
output is a normal SDD artifact. It must be git-trackable (a real committed file).

**Kickoff path — version gate.** `docs/.sdd-version` selects where the kickoff lives:
- **Marker is not `4`:** the single flat `docs/handoff/kickoff.md` (unchanged).
- **Marker is `4`:** the per-workstream `docs/ws/<id>/kickoff.md` for the workstream
  selected/created at the picker (kickoff is absorbed per-workstream, `ws-migration.md`;
  no flat `docs/handoff/` in v4). Its `description` is what the §Workstream Picker
  reads back when listing workstreams. A **new cycle in a DONE workstream** overwrites
  that workstream's `docs/ws/<id>/kickoff.md`; a **new workstream** seeds a fresh one.

**By default** the kickoff is a **research kickoff**: it states the research
questions, success criteria, a budget, and what is out of scope, and the LOOP
begins at the research stage. Assign the cycle's research ID at KICKOFF — the
next `RS-NNN` (marker `4`: `RS-<WS>-NNN`), allocated centrally per §Pipeline
subagent dispatch — and record it in the kickoff frontmatter as `research_id:`.
Phase detection checks **that spike's** findings, never "any `RS-*`", so a prior
cycle's completed research can never mask the new cycle's research stage.
(Kickoffs predating this field: fall back to comparing findings dates against
the kickoff's write date.) For a **non-research entry** (§Entry Points) write
an **entry kickoff** instead — scope of the change, the entry stage, and which
upstream is assumed approved — and begin the LOOP at that stage.

The kickoff carries **no loop log**. It is written once at KICKOFF and is not the
source of truth for resume — the SDD artifacts are (see Phase Detection).

## LOOP

For each stage in order — research, requirements, specs, plan, implement, verify
— run pipeline → review → gate.

**Return contract (stub).** Every leaf dispatch ends its return with a
structured `RETURN:` block (`status:` first, then budget, files, commits, task
and traceability fills, one-line `failures`, ledger, open questions, blocked
writes) and `sdd-review` emits an own-line `VERDICT:` token; the orchestrator
parses both — never prose — branches on them, and composes any fix re-dispatch's
fixed-shape repair packet from three sources only (the previous `RETURN`, the
review's Critical/Material lines, disk paths). Malformed returns and reviews
pause at the gate. The full procedure — key table, malformed rules, packet
shape and field sources, `VERDICT:` and `RETURN.status` branching tables,
finding → chunk mapping, pruned-state check — is
`references/return-contract.md`.

### Per-stage dispatch model

Issue **two separate subagent dispatches** per stage — never a single combined
one. Run the **pipeline** dispatch to completion (artifacts on disk) **before**
constructing the **review** dispatch, because the review's only inputs are the
paths the pipeline produced.

### Pipeline subagent dispatch

The pipeline subagent invokes `sdd-<stage>` and writes the stage's SDD
artifact(s). A subagent is **non-interactive** — it has no operator to answer the
questions an `sdd-*` skill would normally ask. You MUST neutralize this in the
dispatch prompt. The full template is in
[`references/dispatch-templates.md`](references/dispatch-templates.md); its slots
MUST satisfy this contract:

- **Front-load every decision** the stage skill would ask a human for: the
  stage's question/scope, the success criterion, an explicit budget, and the
  exact deliverable contract (files to write + their frontmatter).
- **Assign IDs centrally.** You (the orchestrator) pick the artifact IDs (e.g.
  the next `RS-NNN`) and pass them verbatim. Subagents must not scan existing
  artifacts and choose IDs themselves — that collides under any future parallel
  dispatch.
- **Pin the absolute working directory** (phase detection reads
  `docs/.sdd-version` and artifacts relative to cwd; a wrong cwd silently
  misdetects).
- **Include a non-interactivity clause**: do not ask questions; do not fabricate
  operator consent; record genuinely missing information under an
  Open Questions / Assumptions section with a stated default, and proceed.
- **Include the labeled-content fallback**: if a file cannot be written, return
  its full content with the target path labeled.

### Per-chunk implement dispatch and per-chunk gate

In **sequential mode** the implement stage is dispatched **per chunk, in plan
order** — one PIPELINE dispatch per `### Chunk N:` header (`Chunk {N}` slot,
`references/dispatch-templates.md` §PIPELINE) — and every chunk closes at a
lightweight **per-chunk gate** before the next chunk is dispatched. After each
return the orchestrator dispatches the read-only **chunk verifier**
(`references/dispatch-templates.md` §CHUNK VERIFIER), a second independent
executor of the chunk-close layer that returns `CHUNK_VERDICT: PASS | FAIL`.
`sdd-implement` itself is unchanged (REQ-ORCH-001). Contract:
`docs/spec/harness-chunk-verifier.md`.

```
for each `### Chunk N:` in plan order:
  1. snapshot(before) → dispatch PIPELINE implement, Chunk N
  2. on return: snapshot(after) → parse RETURN → write-scope check → `SCOPE:` token
  3. branch on RETURN.status (references/return-contract.md §7):
       COMPLETE / PARTIAL → dispatch CHUNK VERIFIER for Chunk N (repo root) → `CHUNK_VERDICT:`
       BLOCKED / BUDGET_EXHAUSTED → no verifier; the leaf's checkpoint is already in the plan
  4. render the PER-CHUNK GATE (block below); wait for the operator:
       proceed → orchestrator commits the chunk (commit ownership) → next chunk
       fix     → repair packet (reason: VERIFIER_FAIL, failures ← verifier RETURN.failures,
                 findings: [], iteration ← chunk_redo_count[<chunk header>] + 1) → redo Chunk N → back to 2
       stop    → halt; the chunk's writes stay uncommitted in the working tree
after the last chunk: dispatch the implement-stage sdd-review ONCE on the merged state
                      → the single implement-stage review gate (proceed │ loop-back-to-fix │ stop)
```

The gate block (byte-identical to `harness-chunk-verifier.md`,
`harness-write-scope.md` §Commit Ownership and `orchestration.md` §v5):

```
Per-chunk gate — implement dispatch #2 (Chunk 2: Reconciliation)   [fan-out: leaf wt-g1 / branch fanout-g1]
  RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 22, test_runs: 3}  vs  Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs
  SCOPE: CLEAN                                    # full write-scope block above when VIOLATION
  CHUNK_VERDICT: PASS                             # verifier findings (Check 1 / Check 3 / Gates) listed above when FAIL
  Files changed  : src/recon/engine.py M, tests/test_recon.py M, docs/plan.md M
  Redo           : 0 of 3 (per-chunk redo counter)
  Options: proceed (orchestrator commits the chunk) │ fix (re-dispatch Chunk 2 with a repair packet; counts toward the per-chunk redo cap) │ stop
```

**Defaults.** `proceed` on `CHUNK_VERDICT: PASS` + `SCOPE: CLEAN`; `fix` on
`FAIL` or `SCOPE: VIOLATION`. `proceed` on a FAIL is an explicit operator
override, recorded as gate text (`CHUNK_VERDICT: FAIL — proceeded by
operator`); nothing is persisted. An unresolved `OUT` path is resolved by the
scope options (`revert path | accept & widen scope`) before any choice.

**Per-chunk redo counter.** Keep `chunk_redo_count[<chunk header>]` per chunk,
shown as `Redo: N of 3` against `REDO_MAX` (default 3,
`harness-loop-control.md` §Redo Cap per Chunk). It increments **only on
`fix`** (a `PARTIAL_CONTINUE` or fresh-budget `fix` counts; a verifier
re-dispatch does not). On exhaustion the gate behaves exactly like the fix-loop
cap — `stop │ manual intervention │ authorized extra redo` — with the exhaustion
summary compiled from the verifier's findings; the operator may choose a replan
from there.

**FAIL routing.** A FAIL routes **only** to a repair packet for a redo of the
same chunk (`fix`); never directly to a merge, to the implement-stage review,
or to `sdd-replan`. Signal order at this gate is `RETURN.status` → `SCOPE:` →
`CHUNK_VERDICT:` (REQ-ORCH-034); the per-chunk gate never shows a review
`VERDICT:`.

**Review runs ONCE.** The implement-stage `sdd-review` and its stage gate run
once, after all chunks, on the merged state. A three-chunk plan yields 3
implement + 3 verifier dispatches (plus redos), 3 per-chunk gates, and **1**
review with **1** stage gate.

**Post-review loop-back re-entry.** After a stage-level `loop-back-to-fix`,
findings are mapped to chunks (`references/return-contract.md` §5 — REQ → spec
→ chunk; unmappable or multi-chunk → one `target.chunk: all` fix dispatch).
Each fix dispatch is followed by the scope check, **one verifier per touched
chunk**, and that chunk's per-chunk gate **before** the re-review.

**Verifier edge cases.** No `### Chunk N:` headers (v2 vocabulary) → one
implement dispatch, no verifier, stated at the gate. A verifier returning
`status: BUDGET_EXHAUSTED` is consumed as `CHUNK_VERDICT: FAIL`; the
orchestrator may re-dispatch it with a larger budget before rendering the gate
— a **verifier re-dispatch is not a redo** and does not increment
`chunk_redo_count`. A gate command that exits non-zero on the verifier's run
but zero on the orchestrator's re-run (or on a redo with no code change)
renders the gate line as `possible flake` — never auto-PASS. A verifier that
writes anyway gets every path tagged `OUT`, `SCOPE: VIOLATION`, and its writes
reverted before any redo. Under **fan-out** the same block is the per-leaf
gate, rendered before merge with no orchestrator commit
(`references/fan-out.md` §3a.v).

### Review subagent dispatch

The review subagent invokes `sdd-review` against the pipeline's output. This
dispatch enforces `sdd-review`'s prohibited-inputs list **at dispatch time** —
isolation does not depend on operator vigilance. The template is in
[`references/dispatch-templates.md`](references/dispatch-templates.md).

**The review dispatch MUST carry ONLY:**
- the repository root,
- the deliverable artifact path(s) — for the **implement stage**, where there is
  no single artifact file, this means the plan path plus the source/test files
  changed during the stage (e.g. `git diff --name-only` against the
  stage-start commit),
- the upstream artifact path — **except for the research stage** (see below),
- the instruction to invoke `sdd-review`.

**It MUST NOT carry:**
- your conversation or reasoning,
- the pipeline subagent's reasoning or "here's what I was thinking" framing,
- kickoff prose beyond the artifact itself,
- any draft or intermediate states.

The reviewer obtains all other context (frontmatter, commit history, the
traceability matrix) by reading repository files itself.

**Research-stage exception**: for the research stage, **omit the upstream
(kickoff) path** — `sdd-review` prohibits kickoff prompts as a contaminating
input, so the reviewer reads the research questions from the deliverable's own
frontmatter instead. For every later stage, supply the upstream SDD artifact
(requirements when reviewing specs, specs when reviewing the plan, …) — it is a
permitted, non-leaking input.

### The gate

After review, parse the review's own-line token — one of `VERDICT: APPROVE`,
`VERDICT: APPROVE_WITH_FIXES`, `VERDICT: REJECT` (match `^VERDICT:` at line
start; last occurrence wins; never classify the verdict from prose) — surface
it with the review's return text to the operator and **wait** for an explicit
decision. Never auto-advance. Which choices the gate offers per token, and what
runs between a leaf's return and its gate per `RETURN.status`, are the
`VERDICT:` and `RETURN.status` branching tables in
`references/return-contract.md` §6 and §7.

| Decision | Action |
|----------|--------|
| **proceed** | Advance to the next stage. |
| **loop-back-to-fix** | Re-dispatch the pipeline subagent with a repair packet (findings + paths by construction — `references/return-contract.md` §3; never a re-litigation of the reviewer's reasoning), then re-run the review for this stage. |
| **stop** | Halt the loop; leave artifacts as-is. |

**Approve-with-fixes shortcut.** `sdd-review` defines *Approve with fixes* as
"fix the named findings, then proceed without re-review". When that is the
verdict and the operator chooses **loop-back-to-fix**, offer both readings at
the gate: re-dispatch the pipeline with the findings and then either re-review
(the default loop) or skip the re-review per the verdict's own definition — the
operator picks. For *Reject* verdicts the re-review is never skipped.

**`CHUNK_VERDICT:` consumer.** For the implement stage this stage gate is the
*second* gate kind: each chunk has already closed at a per-chunk gate whose
signals, in order, are `RETURN.status` → `SCOPE:` → `CHUNK_VERDICT:` (parsed
from the verifier's `RETURN:` block, last line; missing or unrecognized →
`RETURN: MALFORMED`). The stage gate shows the review `VERDICT:` plus the loop
counters (REQ-ORCH-034) — see §Per-chunk implement dispatch and per-chunk gate.

### Edge cases routed through the gate

- **Replan trigger**: if a pipeline subagent triggers a replan (stuck detection,
  spike invalidation, or a verification failure), surface it to the operator as a
  gate event. The loop may then route back to an earlier stage via `sdd-replan`,
  consistent with the cyclic SDD model. Do not silently absorb or auto-resolve a
  replan trigger.
- **Reject with no actionable findings**: if a review returns a reject/fail
  verdict carrying no actionable findings, **pause** and let the operator decide
  (re-dispatch, override, or stop). Do not auto-loop the pipeline.
- **`REVIEW: MALFORMED`**: if the review's `VERDICT:` token is missing,
  unrecognized, or disagrees with its prose verdict, **pause** with
  `re-dispatch review | accept prose manually | stop`. Never guess the verdict
  from prose (`references/return-contract.md` §6).
- **`RETURN: MALFORMED (<reason>)`**: if a leaf's `RETURN:` block is absent,
  `status:` is not its first key or not one of the four values, a value spans
  multiple lines, or the block is self-contradictory, **pause** with the raw
  tail of the return and `re-dispatch | accept manually | stop`. Never treat a
  malformed return as `COMPLETE` (`references/return-contract.md` §1).

## Reviews Are Ephemeral

A review verdict is the review subagent's return text, surfaced inline. Do
**not** write verdicts to disk as a project artifact, and do **not** create a
`docs/reviews/` directory. Decisions land in the artifacts themselves — commits,
spec edits, Q-IMPL entries, replan triggers.

## Execution Model

**Sequential is the default.** Every stage runs single-threaded in the main
workspace unless the operator explicitly opts into fan-out at the implement gate.
Fan-out is **only** ever available at the implement stage; no other stage fans out.

**Implement-stage fan-out (Design B — active, opt-in).** Fan-out is
**orchestrator-owned and one level deep**: you derive independent chunk-groups from
the plan, provision a worktree per group, dispatch one **leaf** implement subagent
per group, then merge the branches sequentially into `main` before the
implement-stage review. The full procedure (dispatch template + command sequence)
lives in [`references/fan-out.md`](references/fan-out.md); the contract below is its
summary.

Design A (a pipeline subagent owning nested fan-out) is **ruled out infeasible** — a
dispatched subagent has no subagent-dispatch tool (RS-006 Q1) — so Design B is the
only viable design and the spec.

### Integration anchor (version gate — marker-3 `main` vs marker-4 workstream branch)

`docs/.sdd-version` is the **sole** gate for the fan-out integration anchor
(`docs/spec/ws-integration.md`):

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Fan-out branches from
  and merges into `main`; `sdd-verify` diffs against `main`; the §Conflict-handling
  `main`-ownership boundary-error inference applies. The v3 path is untouched.
- **Marker is `4`: integration is branch-per-workstream → PR to `main` (REQ-WS-016).**
  The **workstream branch — not `main`** — is the integration unit for that
  workstream's whole cycle: a completed workstream merges to `main` via **PR**, two
  workstreams can hold **open PRs simultaneously**, and `main` is a shared trunk, not
  a working surface. Consequently, implement-stage fan-out branches its worktrees from
  the **workstream branch** (HEAD) and merges them **back into it**, leaving `main`
  untouched until the workstream PR (REQ-WS-017); the `main`-ownership boundary-error
  inference is **removed**; and `sdd-verify`'s regression base is the **workstream
  branch point** `merge-base(<ws>, main)`, not `main` HEAD (REQ-WS-018). Full contract
  and the exact command substitutions: [`references/fan-out.md`](references/fan-out.md)
  §0.

### Boundary derivation

Fan out along the **independent branches of the plan's chunk dependency graph** —
not per-milestone (too coarse; milestones are sequential) and not per-task (too
fine). Derive the groups by **reading `docs/plan.md`**, never by modifying
`sdd-implement`: parse each chunk's `**Depends on**: Chunk N` field (canonical, per
plan-management.md) or its chunk-level prose equivalent `Entry criteria: Chunk N
complete`. Do **not** use milestone-level Entry/Exit criteria for this. Two chunks
are independent when neither (transitively) depends on the other.

**Degrade to sequential** (never guess a boundary) when the plan has no parseable
chunk-level dependencies, or when the graph is a **single chain** (no ≥2 independent
branches).

### Opt-in gate

Fan-out is **opt-in at the implement gate** and never automatic. At that gate,
present fan-out as an explicit operator choice; you may surface how many independent
chunk-groups the plan yields so the operator can judge whether it is worthwhile.
Absent an opt-in, the implement stage runs sequentially.

When the plan yields only a **single chain** (or has no parseable chunk-level
dependencies), tell the operator **at the gate** that fan-out will degrade to
sequential for this plan — so an opt-in that then runs sequentially is expected, not
surprising.

**Chunk verifier: default on, opt-out here.** The same gate records whether the
chunk-close verifier runs this cycle (`harness-chunk-verifier.md` Open Question
1). It is **on** by default — per chunk in sequential mode, per leaf before merge
under fan-out (`references/fan-out.md` §3a.v). The operator may disable it for
the cycle at this gate only; the choice is gate text, never persisted.

### Lifecycle (provision → dispatch → merge → teardown)

When the operator opts in and the graph has ≥2 independent branches:

1. **Provision** one worktree/branch per group yourself:
   `git worktree add -b <branch> <path> <base>`. Worktree ownership is the
   orchestrator's (Q-REQ-G) — a single owner keeps provisioning and teardown
   symmetric and avoids orphaned worktrees.
2. **Dispatch** one implement subagent per group, pinned to its worktree/branch,
   carrying that group's chunks. Each is a **leaf** — it runs `sdd-implement` and
   must not (and cannot) sub-dispatch (REQ-ORCH-022). The non-interactivity contract
   and central ID assignment apply. **Issue all per-group dispatches in one batch**
   so they run concurrently (see Concurrency note), then **await all returns** before
   merging.
3. **Subagent git identity:** instruct each subagent to commit with inline
   `git -c user.email=<id> -c user.name=<name> commit ...` — never by writing
   `.git/config`, which the subagent sandbox blocks (RS-006 Q2). Do not instruct a
   subagent to write `.git/config`.
4. **Sequential merge to main:** after all returns, merge branches one at a time
   (`git merge --no-edit <branch>`), completing **all** merges **before** the
   implement-stage review (the review sees the merged state, never an unmerged
   branch). One-at-a-time merging means partial-merge corruption cannot occur.
5. **Teardown:** after each clean merge, remove the worktree
   (`git worktree remove <path>`) and delete its branch (`git branch -d <branch>`),
   leaving only `main` for the review.

### Conflict handling (redo by re-derivation)

On a non-zero `git merge` exit: an **optional** best-effort auto-resolve may be tried
first (a clean auto-resolve = PASS, no abort). Otherwise run `git merge --abort`,
then **redo the chunk-group by re-derivation** — provision a fresh worktree
re-branched from the updated `main` (`git worktree add -b <branch>-redo <path>
main`) and re-dispatch a leaf implement subagent to re-run `sdd-implement` there.
**Never replay the stale returned patch** (it would reproduce the same conflict);
re-derivation integrates the already-merged changes. If the group **still** conflicts
after re-derivation, that proves the groups were not truly independent (a boundary
error) → **fall back to running the affected groups sequentially**, which cannot
conflict by construction and guarantees termination. `git merge --abort` unwinds only
the single failing merge — already-merged work is never corrupted. Full command
sequence: [`references/fan-out.md`](references/fan-out.md) §3c (Q-IMPL-1).

**Marker-4 anchor (§Integration anchor):** under `docs/.sdd-version` == `4` the
provision base, merge-back target, and redo re-branch are the **workstream branch**
(not `main`), and the "**still conflicts → boundary error**" inference is **removed**
(REQ-WS-017) — `main` may have moved under the workstream meanwhile, so a repeat
conflict is not diagnostic of non-independence. The guaranteed-termination sequential
fallback is retained (re-run affected groups one at a time off the updated workstream
branch). Under marker `3` this paragraph applies against `main` exactly as written,
unchanged. See [`references/fan-out.md`](references/fan-out.md) §0/§3c.

### Concurrency note

Fan-out implement subagents dispatched in a single batch were **observed to run
concurrently** on this harness — medium confidence, per the RS-006
dispatch-concurrency spike (`docs/spikes/dispatch-concurrency.md`), whose ~4s probe
workload inside a ~426s agent lifetime is latency-dominated. Where it holds, fan-out
delivers wall-clock speedup, not merely worktree isolation (REQ-ORCH-028).
**Correctness does not depend on it:** the design (per-worktree isolation +
sequential conflict-aborting merge) is correct whether dispatches run concurrently or
serialized; only the speedup depends on concurrency.

## Orchestrator-Only Work

Some work needs a capability a **leaf pipeline subagent does not have**: subagent
**dispatch**. A dispatched subagent's toolset contains no dispatch tool at all
(RS-006 Q1), so it cannot spawn its own subagents. You (the orchestrator) MUST
perform dispatch-requiring work yourself — never hand it to a delegated pipeline
dispatch, which would stall (the leaf subagent cannot proceed) or silently
under-deliver. The two cases that arise:

1. **Implement-stage fan-out execution** — provisioning worktrees and dispatching
   one implement subagent per chunk-group is itself dispatch; that is exactly why
   fan-out is orchestrator-owned (Design B, not the nested Design A).
2. **A spike or task that measures or uses dispatch** — e.g. a concurrency probe
   that dispatches parallel subagents. Run it directly; do not delegate it. (The
   RS-006 dispatch-concurrency spike was run this way.)

Ordinary stage work — invoking an `sdd-*` skill, reading/writing files — remains
delegable to a pipeline subagent as normal. The test is simply: *does executing
this task require dispatching a subagent?* If yes, the orchestrator does it.

**Routing is orchestrator-only (REQ-HARN-019).** Beside the dispatch rule above,
a second class of work never appears as an instruction in any pipeline, fix,
fan-out, verifier or review template: phase-detection relay; `VERDICT:`
classification; `CHUNK_VERDICT:` and `SCOPE:` interpretation; fix / redo /
replan cap arithmetic; repair-packet composition; and the decision to merge,
re-dispatch, replan or stop. Templates tell a subagent what to *produce* (the
`RETURN:` block, the `VERDICT:` token, findings) — never what to *decide next*.
The verdict / status branching tables and packet composition live in
`references/return-contract.md`.

## Isolation Discipline (normative)

The driver MUST:

1. Dispatch the pipeline and the review as **two separate subagents** per stage.
2. Construct the review dispatch from **artifact paths only** (plus the repo root
   and, for non-research stages, the upstream path). Never include your
   conversation, the pipeline subagent's reasoning, kickoff prose beyond the
   artifact, or draft/intermediate states.
3. On a fix loop, pass the pipeline subagent **only** the review findings plus
   artifact paths — not a re-litigation of the reviewer's reasoning.

These mirror `sdd-review` Step 2's "Do NOT accept as inputs" list, enforced at
dispatch time rather than relying on operator vigilance.

## Rules

- **Compose, never reimplement**: stage logic lives in the nine `sdd-*` skills.
  Dispatch them; do not duplicate or modify them.
- **Two dispatches per stage, always**: pipeline and review are never combined.
- **Paths only to the reviewer**: if you are tempted to "give the reviewer some
  helpful context," stop — that is the leak the design exists to prevent.
- **Human gate at every stage**: never auto-advance past a gate.
- **Reviews are ephemeral**: no `docs/reviews/`, no verdicts on disk.
- **Artifacts are the source of truth for resume**: no loop-position marker, no
  authoritative loop log.
- **Sequential by default**: only the implement stage may fan out, only when the
  operator opts in and the plan has ≥2 independent chunk branches; no non-research
  entry.

## Transition

When the verify stage passes review and the operator approves, the cycle is
DONE. Recommend committing the cycle's artifacts (including
`docs/handoff/kickoff.md`).
