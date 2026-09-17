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
replan, migrate, review) and **never reimplements their logic**: stage work —
including each skill's own phase detection and staleness handling — is done by
dispatching that skill, and you relay its output. You own only orchestration:
sequencing stages, constructing isolated dispatches, and mediating operator
gates. Isolation is **by construction**: each pipeline stage and each review
runs as a **separate subagent** with a fresh context window, so your reasoning
cannot leak (a fresh subagent still inherits repo-level context — `CLAUDE.md`,
project memory; the guarantee covers the working session's reasoning and
drafts, not repo documentation).

**Scope**: research-entry by default, sequential by default. When approved
upstream artifacts already exist the operator may start **mid-pipeline** (§Entry
Points). Implement-stage **fan-out** is an opt-in mode at the implement gate
(§Execution Model); every other stage is always sequential.

## Phase Detection

The driver introduces **no loop-position marker**. On entry — including re-entry
in a fresh session mid-loop — derive the current loop position from the existing
SDD artifacts, reusing the stage skills' own phase detection:

**Upgrade offer (entry, all markers).** First read `docs/.sdd-version`; if it
is **behind** the latest version the installed skills support (currently `4`),
**offer to run `/sdd-migrate` first** — informational, non-forcing, and the
single place a behind-version project is nudged (REQ-WS-030). On accept, hand
off to `sdd-migrate` and re-derive phase from the migrated layout; on decline
(or non-interactive) proceed on the current marker with behavior **unchanged**;
at the latest marker, say nothing.

**Workstream & version gate (v4).** Under `docs/.sdd-version` ≠ `4` (v3 or
earlier) behavior is UNCHANGED — ignore the `workstream` argument, derive loop
position from the flat artifacts in the table below and never read `docs/ws/`.
Under marker `4` the execution artifacts are rooted at `docs/ws/<ws>/`:
[`references/v4-workstreams.md`](references/v4-workstreams.md) §Workstream & version gate.

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

For an **entry kickoff** (§Entry Points) the stages before its recorded entry
stage are *intentionally absent*: derive loop position from the entry stage
onward only, never "at the research stage" from missing research artifacts.
Tell the operator the detected position and confirm before proceeding. A pending
or prior review leaves no on-disk trace by design — it is **reproduced** by
re-dispatching the review subagent (reviews are read-only and idempotent).

**New cycle vs. resume.** A **complete** prior cycle (`status: pass`) is both
"DONE" and the next feature's starting point. Classify entry as **resume** (a
cycle is mid-loop → continue it), **done** (no new idea → report DONE) or **new
cycle** (the operator brings a new idea → run DISCUSS and **overwrite**
`docs/handoff/kickoff.md` at KICKOFF). Only **operator intent** separates *done*
from *new cycle*: surface your interpretation and confirm, never silently report
the prior DONE. No new marker is added (REQ-ORCH-014 stands).

**Marker-`4` gate for done-vs-new-cycle.** Under marker ≠ `4` behavior is
UNCHANGED — the single global operator intent above resolves it. Under marker
`4` it is resolved per workstream via the picker: [`references/v4-workstreams.md`](references/v4-workstreams.md)
§Marker-4 gate for done-vs-new-cycle.

## Workstream Picker

`docs/.sdd-version` is the **sole** gate. **Marker is not `4` (v3 or earlier):
NO picker — behavior UNCHANGED**; skip this section and drive the single flat
cycle. **Marker is `4`:** open with a workstream picker (REQ-WS-029) — enumerate
`docs/ws/<id>/`, show id + kickoff description + detected phase, and let the
operator select an existing workstream or create one; every new workstream
enters at research and its kickoff's `research_id` spike decides when that
research is complete (REQ-WS-024). Full procedure: [`references/v4-workstreams.md`](references/v4-workstreams.md)
§Workstream Picker.

## Entry Points

Research is the **default** entry. But when approved upstream SDD artifacts
already exist, the operator may start the loop **mid-pipeline** (REQ-ORCH-031) at
**requirements, specs, plan, or implement**. **Verify is not an entry point**
(verifying an existing project is just invoking `sdd-verify` directly — no loop).
*Resume* continues a cycle **this driver** started (its kickoff + partial
artifacts are on disk); *non-research entry* begins a fresh loop over artifacts
produced **outside** this driver (e.g. hand-written requirements).

**Marker-`4` scope.** Mid-pipeline entry is a marker-`3` single-cycle concept
(behavior UNCHANGED there); under marker `4` a new workstream always begins at
research and selecting an existing one is resume, not entry — [`references/v4-workstreams.md`](references/v4-workstreams.md)
§Marker-4 scope.

**Detect → confirm → validate (REQ-ORCH-032).** **Auto-detect** the proposed
entry stage with the same phase detection (furthest-complete *approved*
upstream → the next stage); **present and confirm** it with the operator (who
may override to an *earlier* stage, never a later one whose upstream is unmet);
**validate** the chosen stage's upstream is approved/complete — otherwise route
to the earliest incomplete upstream stage and say why. Never guess an entry
stage silently — confirmation is mandatory.

**Entry kickoff (REQ-ORCH-033).** KICKOFF still writes `docs/handoff/kickoff.md`
(the only new artifact), but as an **entry kickoff** recording the *scope of
the change*, the *entry stage*, and *which upstream is assumed approved* — not
research questions. DISCUSS still runs first; from the entry stage on the LOOP
is identical to a research-entry cycle.

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
operator. **Reuse the brainstorming process** — a brainstorming skill if one is
available, else the equivalent inline: explore intent, challenge assumptions,
surface scope boundaries, capture the open questions research should answer.
Never jump straight to a kickoff or to implementation. Exit DISCUSS when you
both agree on what the idea is, what is in and out of scope, and the concrete
questions worth researching.

## KICKOFF

Write the converged discussion into the cycle's kickoff file — the **only** new
on-disk artifact type the driver introduces, git-tracked like any SDD artifact.

**Kickoff path — version gate.** Marker ≠ `4`: the single flat
`docs/handoff/kickoff.md` (UNCHANGED). Marker `4`: the per-workstream
`docs/ws/<id>/kickoff.md` — [`references/v4-workstreams.md`](references/v4-workstreams.md) §Kickoff path.

**By default** the kickoff is a **research kickoff** (questions, success
criteria, budget, out-of-scope) and the LOOP begins at research. Assign the
cycle's research ID at KICKOFF — the next `RS-NNN` (marker `4`: `RS-<WS>-NNN`),
allocated centrally — and record it in the frontmatter as `research_id:`; phase
detection checks **that spike's** findings, never "any `RS-*`", so a prior
cycle's research can never mask the new one's (kickoffs predating the field:
compare findings dates against the kickoff's write date). A **non-research
entry** writes an **entry kickoff** instead (§Entry Points). The kickoff carries
**no loop log** — the SDD artifacts are the source of truth for resume.

**Kickoff frontmatter — `date:` is mandatory (REQ-HARN-002).** Every kickoff
this skill writes carries `date: YYYY-MM-DD` beside `research_id:`; it is the
primary source for the replan re-entry cap derivation (§The gate). Omitting it
is a template violation; only kickoffs predating this rule fall back to the
`git log -S'research_id: <id>'` derivation.

**Pre-pipeline self-checks (not lint — the orchestrator checks itself).** Before
the first pipeline dispatch, the kickoff carries `date:` and `research_id:` (fix
it first if not). Before **every** dispatch (pipeline, fix, fan-out leaf,
review, chunk verifier) the prompt's `Budget:` slot holds a non-empty value in
observable units (`references/return-contract.md` §Budget grammar) — never
dispatch around an empty one.

**Telemetry opt-out (one prompt, REQ-TELEM-HARNESSP2-004).** Ask once at KICKOFF — `telemetry: on (default) │ off` — and hold the answer as session state for the whole cycle; it is never written to the kickoff ([`references/telemetry.md`](references/telemetry.md) §3).

## LOOP

For each stage in order — research, requirements, specs, plan, implement, verify
— run pipeline → review → gate.

**Return contract.** Every leaf dispatch ends with a structured `RETURN:`
block (`status:` first) and `sdd-review` emits an own-line `VERDICT:` token.
You parse both — never prose — branch on them, and compose any fix
re-dispatch's fixed-shape repair packet from the previous `RETURN`, the
review's Critical/Material lines and disk paths only. Malformed returns and
reviews pause at the gate. Key table, malformed rules, packet shape, branching
tables, finding → chunk mapping, pruned-state check:
[`references/return-contract.md`](references/return-contract.md).

**Write scope.** Every leaf template declares `Write scope:` (review and
verifier: `(empty — read-only)`). Around every dispatch take `snapshot(before)`
/ `snapshot(after)` (immediately on return, before the verifier, the gate and
your own commit or merge), tag each written path `IN` / `ADVISORY` / `OUT`, and
surface an own-line `SCOPE: CLEAN | VIOLATION (N paths)` before the verifier,
the gate and any commit. `blocked_writes` are scope-matched before persistence;
commit ownership is fixed per dispatch type (pipeline: orchestrator on
`proceed`; fan-out leaf: the leaf; review/verifier: nobody). Full procedure:
[`references/write-scope.md`](references/write-scope.md).

**Telemetry.** Default **on**; the operator may opt out at KICKOFF (session
state, never written to `kickoff.md`). After **each gate** you append one
record — counts, enums, shas, timestamps, never finding text — to the
gitignored `.sdd/telemetry.jsonl`; no leaf ever writes it and no skill reads
it: **never read by phase detection** — `rm -rf .sdd/` is behaviour-neutral.
Bootstrap: if `git check-ignore -q .sdd/telemetry.jsonl` fails, append `.sdd/`
to `.gitignore` as a bookkeeping commit outside any observed window. Post-cycle
reader: `python3 tools/sdd-telemetry.py summarize`. Record schema, writer
rules, `TELEMETRY:` lines, third observation:
[`references/telemetry.md`](references/telemetry.md).

### Per-stage dispatch model

Issue **two separate subagent dispatches** per stage — never one combined — and
run the **pipeline** dispatch to completion (artifacts on disk) **before**
constructing the **review** dispatch, whose only inputs are the produced paths.

### Pipeline subagent dispatch

The pipeline subagent invokes `sdd-<stage>` and writes the stage's SDD
artifact(s). A subagent is **non-interactive** — no operator answers the
questions an `sdd-*` skill would ask — so the dispatch prompt
([`references/dispatch-templates.md`](references/dispatch-templates.md)) MUST:
**front-load every decision** (scope, success criterion, explicit budget, exact
deliverable contract — files + frontmatter); **assign IDs centrally** (you pick
e.g. the next `RS-NNN`; subagents never scan and choose IDs — that collides
under parallel dispatch); **pin the absolute working directory** (phase
detection reads `docs/.sdd-version` relative to cwd; a wrong cwd silently
misdetects); **include a non-interactivity clause** (no questions, no
fabricated consent; missing information goes under Open Questions /
Assumptions with a stated default); and **include the labeled-content
fallback** (an unwritable file is returned in full, target path labeled).

### Per-chunk implement dispatch and per-chunk gate

In **sequential mode** the implement stage is dispatched **per chunk, in plan
order** — one PIPELINE dispatch per `### Chunk N:` header (`Chunk {N}` slot,
`references/dispatch-templates.md` §PIPELINE) — and every chunk closes at a
lightweight **per-chunk gate** before the next chunk is dispatched. After each
return the orchestrator dispatches the read-only **chunk verifier**
(`references/dispatch-templates.md` §CHUNK VERIFIER), a second independent
executor of the chunk-close layer that returns `CHUNK_VERDICT: PASS | FAIL`.
`sdd-implement` itself is unchanged (REQ-ORCH-001); contract:
`docs/spec/harness-chunk-verifier.md`. The loop, gate defaults, the per-chunk
redo counter (`Redo: N of 3` against `REDO_MAX`, incremented only on `fix`),
FAIL routing, the once-only implement-stage review and verifier edge cases:
[`references/loop-control.md`](references/loop-control.md) §1. The gate block —
the **one canonical copy** in this skill, byte-identical to
`harness-chunk-verifier.md` §Sequencing; under fan-out it is the per-leaf gate,
rendered before merge with no orchestrator commit (`references/fan-out.md` §3a.v):

```
Per-chunk gate — implement dispatch #2 (Chunk 2: Reconciliation)   [fan-out: leaf wt-g1 / branch fanout-g1]
  RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 22, test_runs: 3}  vs  Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs
  SCOPE: CLEAN                                    # full write-scope block above when VIOLATION
  CHUNK_VERDICT: PASS                             # verifier findings (Check 1 / Check 3 / Gates) listed above when FAIL
  Files changed  : src/recon/engine.py M, tests/test_recon.py M, docs/plan.md M
  Redo           : 0 of 3 (per-chunk redo counter)
  Options: proceed (orchestrator commits the chunk) │ fix (re-dispatch Chunk 2 with a repair packet; counts toward the per-chunk redo cap) │ stop
```

### Review subagent dispatch

The review subagent invokes `sdd-review` against the pipeline's output. This
dispatch enforces `sdd-review`'s prohibited-inputs list **at dispatch time** —
isolation does not depend on operator vigilance. Template:
[`references/dispatch-templates.md`](references/dispatch-templates.md).

**The review dispatch MUST carry ONLY:** the repository root; the deliverable
artifact path(s) — for the **implement stage** the plan path plus the
source/test files changed during the stage (`git diff --name-only` against the
stage-start commit); the upstream artifact path — **omitted for the research
stage**, where `sdd-review` prohibits kickoff prompts as a contaminating input
and reads the questions from the findings frontmatter instead; the `Budget:`
line and the read-only `Write scope:` line; and the instruction to invoke
`sdd-review`. **It MUST NOT carry** your conversation or reasoning, the
pipeline subagent's reasoning or framing, kickoff prose beyond the artifact, or
any draft or intermediate state (§Isolation Discipline). The reviewer obtains
all other context (frontmatter, commit history, traceability) by reading
repository files itself.

### The gate

After review, parse the own-line token — `VERDICT: APPROVE`,
`VERDICT: APPROVE_WITH_FIXES` or `VERDICT: REJECT` (match `^VERDICT:`; last
occurrence wins; never classify from prose) — surface it with the review's
return text and **wait** for an explicit decision. Never auto-advance. Choices
per token and per `RETURN.status`: `references/return-contract.md` §6, §7.

| Decision | Action |
|----------|--------|
| **proceed** | Advance to the next stage. |
| **loop-back-to-fix** | Re-dispatch the pipeline subagent with a repair packet (findings + paths by construction — `references/return-contract.md` §3; never a re-litigation of the reviewer's reasoning), then re-run the review for this stage. |
| **stop** | Halt the loop; leave artifacts as-is. |

**Approve-with-fixes shortcut.** `sdd-review` defines *Approve with fixes* as
"fix the named findings, then proceed without re-review": on
**loop-back-to-fix** for that verdict offer both readings — re-dispatch then
re-review (default) or skip the re-review; *Reject* never skips it.

**Gate signals — REQ-ORCH-034 order (pointers only).** In production order,
all ephemeral (REQ-ORCH-013): (1) `RETURN.status` + `budget_consumed` vs the
dispatched `Budget:` (`references/return-contract.md` §1, §7); (2) the
own-line `SCOPE:` token (`references/write-scope.md` §5; `HISTORY_REWRITE`
offers only `stop`); (3) per chunk, `CHUNK_VERDICT:` with `Redo: N of 3` —
1–3 render at the **per-chunk gate**; (4) the review `VERDICT:`; (5) the loop
counters — `iteration N of MAX` for the fix-loop cap and the replan re-entry
count — 4–5 render at the **stage gate**. Detail:
[`references/loop-control.md`](references/loop-control.md) §5.

**`TELEMETRY:` lines** (`WRITE FAILED` │ `OFF` │ `.gitignore updated`) render at most once each, immediately after the `iteration`/cap line and before the options — [`references/telemetry.md`](references/telemetry.md) §3.

**Fix-loop cap (REQ-HARN-001).** `FIX_LOOP_MAX` (default **3**) is per stage,
session-only, incremented once per fix re-dispatch (never on `proceed`, `stop`
or a replan route); every fix re-dispatch carries the literal `iteration N of 3`
(`N of MAX`) in its repair packet, the operator may raise the cap by one per
explicit gate decision, and on exhaustion no further fix is dispatched — the
gate renders the **compiled findings log** and offers only `stop | manual
intervention | authorize extra iteration`. Procedure:
[`references/loop-control.md`](references/loop-control.md) §2.

**Replan re-entry cap (REQ-HARN-002, REQ-HARN-003).** `REPLAN_MAX` (default
**3**) is never stored: on every replan trigger recompute the count of
`-replan-` archives in `plan-history/` dated ≥ the kickoff's `date:` (legacy
fallback `git log -S'research_id: <id>'`; neither determinable → **treated as
reached**). At or past the cap, surface a gate event (REQ-ORCH-017 shape)
naming count, cap and archive filenames and route into `sdd-replan` only on an
explicit operator decision — the cap is never silently unreachable. Derivation:
[`references/loop-control.md`](references/loop-control.md) §3. Cap arithmetic
is orchestrator-only (§Orchestrator-Only Work).

**Edge cases routed through the gate** — a replan trigger (a gate event, never
silently absorbed); a reject with no actionable findings (pause, operator
decides); `REVIEW: MALFORMED` (pause: `re-dispatch review | accept prose
manually | stop`); `RETURN: MALFORMED (<reason>)` (pause with the raw tail;
never treat as `COMPLETE`): [`references/loop-control.md`](references/loop-control.md) §6.

## Reviews Are Ephemeral

A review verdict is the review subagent's return text, surfaced inline. Do
**not** write verdicts to disk as a project artifact, and do **not** create a
`docs/reviews/` directory. Decisions land in the artifacts themselves — commits,
spec edits, Q-IMPL entries, replan triggers.

## Execution Model

**Sequential is the default**; only the implement stage may fan out, and only
on explicit operator opt-in at its gate. **Implement-stage fan-out (Design B —
active, opt-in)** is **orchestrator-owned and one level deep**: derive
independent chunk-groups from the plan, provision a worktree per group,
dispatch one **leaf** implement subagent per group, then merge the branches
sequentially into `main` before the implement-stage review. Design A (a
pipeline subagent owning nested fan-out) is **ruled out infeasible** — a
dispatched subagent has no subagent-dispatch tool (RS-006 Q1). Full procedure:
[`references/fan-out.md`](references/fan-out.md).

### Integration anchor (version gate)

`docs/.sdd-version` is the **sole** gate. Marker ≠ `4`: behavior UNCHANGED —
fan-out branches from and merges into `main`. Marker `4`: the workstream branch
is the anchor (REQ-WS-016..018) — [`references/fan-out.md`](references/fan-out.md)
§0 and [`references/v4-workstreams.md`](references/v4-workstreams.md) §Integration anchor.

### Boundary derivation and opt-in gate

Fan out along the **independent branches of the plan's chunk dependency graph**
(not per-milestone, not per-task), derived by **reading `docs/plan.md`** — never
by modifying `sdd-implement`: parse each chunk's `**Depends on**: Chunk N`
field (canonical) or its prose equivalent `Entry criteria: Chunk N complete`,
never milestone-level criteria. Chunks are independent when neither
(transitively) depends on the other. **Degrade to sequential** (never guess a
boundary) when dependencies are unparseable or the graph is a **single chain**.

Fan-out is **opt-in at the implement gate** and never automatic: present it as an
explicit operator choice, surfacing how many independent chunk-groups the plan
yields (a single chain → say at the gate that it degrades to sequential). The
same gate records whether the **chunk verifier** runs this cycle: **on** by
default — per chunk sequentially, per leaf before merge under fan-out — and
disableable at this gate only, as gate text, never persisted.

### Lifecycle and conflict handling

Provision one worktree/branch per group yourself (Q-REQ-G); dispatch one leaf
per group in one batch and await all returns (a leaf cannot sub-dispatch,
REQ-ORCH-022, and commits with an inline `git -c` identity, RS-006 Q2); merge
sequentially, all merges before the implement-stage review; tear down after
each clean merge. On a merge conflict abort that single merge and **redo the
chunk-group by re-derivation** — never replay the stale patch; a group that
still conflicts is a boundary error → run the affected groups sequentially.
Under marker `3` all of this runs against `main` UNCHANGED; under marker `4`
the workstream branch is the base and merge target (§Integration anchor).
Summary: [`references/loop-control.md`](references/loop-control.md) §4;
commands: [`references/fan-out.md`](references/fan-out.md) §3. Batched leaves
were **observed to run concurrently** (RS-006, medium confidence) — a speedup
(REQ-ORCH-028) correctness does not depend on.

## Orchestrator-Only Work

Some work needs a capability a **leaf pipeline subagent does not have**: subagent
**dispatch**. A dispatched subagent's toolset contains no dispatch tool at all
(RS-006 Q1), so it cannot spawn its own subagents. You (the orchestrator) MUST
perform dispatch-requiring work yourself — never hand it to a delegated pipeline
dispatch, which would stall or silently under-deliver. The two cases that arise:

1. **Implement-stage fan-out execution** — provisioning worktrees and dispatching
   one implement subagent per chunk-group is itself dispatch; that is exactly why
   fan-out is orchestrator-owned (Design B, not the nested Design A).
2. **A spike or task that measures or uses dispatch** — e.g. a concurrency probe
   that dispatches parallel subagents. Run it directly; do not delegate it. (The
   RS-006 dispatch-concurrency spike was run this way.)

Ordinary stage work — invoking an `sdd-*` skill, reading/writing files — remains
delegable to a pipeline subagent as normal. The test is simply: *does executing
this task require dispatching a subagent?* If yes, the orchestrator does it.

**Routing is orchestrator-only (REQ-HARN-019).** A second class of work never
appears as an instruction in any pipeline, fix, fan-out, verifier or review
template: phase-detection relay; `VERDICT:` classification; `CHUNK_VERDICT:`
and `SCOPE:` interpretation; fix / redo / replan cap arithmetic; repair-packet
composition; and the decision to merge, re-dispatch, replan or stop. Templates
tell a subagent what to *produce* (the `RETURN:` block, the `VERDICT:` token,
findings) — never what to *decide next*; `Write scope:` is a bound the
orchestrator checks, not something the subagent judges. Branching and packets:
`references/return-contract.md`; `SCOPE:` branching: `references/write-scope.md`;
loop counters and exhaustion shapes: `references/loop-control.md`.

## Isolation Discipline (normative)

The driver MUST:

1. Dispatch the pipeline and the review as **two separate subagents** per stage.
2. Construct the review dispatch from **artifact paths only** (plus the repo root
   and, for non-research stages, the upstream path). Never include your
   conversation, the pipeline subagent's reasoning, kickoff prose beyond the
   artifact, or draft/intermediate states.
3. On a fix loop, pass the pipeline subagent **only** the review findings plus
   artifact paths — not a re-litigation of the reviewer's reasoning.
4. **`HISTORY_REWRITE` — no automatic reset.** When the write-scope ancestry
   check fails (`HEAD_after` — or a leaf's branch tip — does not descend from
   `HEAD_before` / `<base>`: an amend, rebase or reset inside the dispatch),
   surface `HISTORY_REWRITE` above the path list, count it as a
   `SCOPE: VIOLATION`, and offer **only `stop`** plus a manual recovery hint
   (`git reflog` in the affected tree). Never `git reset` the working tree or
   a branch, never force-move a ref, never merge a rewritten leaf branch, on
   the orchestrator's own initiative (`references/write-scope.md` §3, §5).

Rules 1–3 mirror `sdd-review` Step 2's "Do NOT accept as inputs" list, enforced
at dispatch time; rule 4 is the write-scope analogue — observe and report, the
operator decides.

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
  operator opts in and the plan has ≥2 independent chunk branches; mid-pipeline
  entry only per §Entry Points (detect → confirm → validate), never by guess.

## Transition

When the verify stage passes review and the operator approves, the cycle is
DONE. Recommend committing the cycle's artifacts (including `docs/handoff/kickoff.md`).
