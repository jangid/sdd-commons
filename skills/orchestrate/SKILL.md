---
name: orchestrate
description: >
  Driver skill that runs the nine SDD phase skills as a single-operator
  orchestration loop with per-stage external review. Drives DISCUSS → KICKOFF →
  LOOP → DONE: brainstorm an idea to shared understanding, write a research
  kickoff, then for each stage dispatch an isolated pipeline subagent and an
  isolated review subagent, gating with the operator after every stage. Use when
  you want to run a whole SDD cycle end-to-end with built-in external review. Do
  NOT use to run a single phase (invoke that sdd:* skill directly) or to review
  an artifact in isolation (use review).
---

# SDD: Orchestration Driver

You are the **orchestrator**: you drive the full SDD cycle from a single human
session, dispatching each stage and each review as separate subagents and
gating with the operator after every stage.

## What This Is

`orchestrate` is a **driver**, not a tenth phase skill. It composes the
nine existing `sdd:*` skills and **never reimplements their logic**: stage
work — including each skill's own phase detection and staleness handling — is
done by dispatching that skill, and you relay its output. You own only
orchestration: sequencing stages, constructing isolated dispatches, and
mediating operator gates. Isolation is **by construction** — each stage and
each review runs as a **separate subagent** with a fresh context window, so
your reasoning cannot leak (repo-level context such as `CLAUDE.md` is still
inherited).

## Phase Detection

The driver introduces **no loop-position marker**: on entry — including
re-entry in a fresh session mid-loop — derive the loop position from the
existing SDD artifacts, reusing the stage skills' own phase detection.

**Upgrade offer, then drift sweep (REQ-WS-030, REQ-GC-HARNESSP2-005).** Read
`docs/.sdd-version`; if it is behind marker `4`, offer `/migrate` once
(informational, never forcing —
[`references/v4-workstreams.md`](references/v4-workstreams.md) §Upgrade offer).
Then run `python3 <skill-dir>/tools/gc.py --report --root .` (`<skill-dir>` = this skill's own directory, so the bundled copy runs; `--root .` keeps the operator's repository the subject),
render one line (`GC: clean` or
`GC: F fail, W warn — run tools/gc.py --report`) and continue regardless:
[`references/drift-sweep.md`](references/drift-sweep.md) §1.

**Workstream & version gate (v4).** Under `docs/.sdd-version` ≠ `4` behavior is
UNCHANGED — ignore the `workstream` argument and never read `docs/ws/`; under
marker `4` execution artifacts are rooted at `docs/ws/<ws>/`:
[`references/v4-workstreams.md`](references/v4-workstreams.md) §Workstream & version gate.

**Cycle identity (REQ-CYCID-HARNESSP3-001, -002).** Before reading a
**completion signal** as "this cycle is done", compare that artifact's
frontmatter `research_id:` against the kickoff's by **exact string equality**:
a mismatch, or an absent field where the kickoff has one, reads as a previous
cycle's artifact; with no usable discriminator the comparison is skipped and
the `status:`-only rule applies unchanged. The three exhaustive cases:
[`references/phase-detection.md`](references/phase-detection.md) §1.

**Loop position and new-cycle-vs-resume.** Derive position from the artifact
table in [`references/phase-detection.md`](references/phase-detection.md) §2 —
kickoff → research → requirements → specs → plan → implement → verify → DONE
(`status: pending-red` resumes at verify, before the red dispatch); for an
**entry kickoff** (§Entry Points) start from its recorded entry stage. Tell the
operator the detected position and confirm; a review leaves no on-disk trace
and is **reproduced** by re-dispatching the review subagent. A complete prior
cycle is both DONE and the next feature's starting point, and only **operator
intent** separates *done* from *new cycle* — one global intent under marker
≠ `4` (UNCHANGED), per workstream under marker `4` (REQ-ORCH-014; §3 there).

## Workstream Picker

`docs/.sdd-version` is the **sole** gate. **Marker is not `4`: NO picker —
behavior UNCHANGED**; drive the single flat cycle. **Marker is `4`:** open with
a workstream picker (REQ-WS-029) — enumerate `docs/ws/<id>/`, show id +
description + detected phase, and let the operator select or create one; every
new workstream enters at research and its kickoff's `research_id` spike decides
when that research is complete (REQ-WS-024):
[`references/v4-workstreams.md`](references/v4-workstreams.md) §Workstream Picker.

## Entry Points

Research is the **default** entry; when approved upstream artifacts already
exist the operator may start **mid-pipeline** (REQ-ORCH-031) at requirements,
specs, plan or implement — **never verify**. *Resume* continues a cycle **this
driver** started; *non-research entry* begins a fresh loop over artifacts
produced **outside** it. Mid-pipeline entry is a marker-`3` single-cycle
concept (UNCHANGED there); under marker `4` a new workstream always begins at
research and selecting an existing one is resume, not entry
([`references/v4-workstreams.md`](references/v4-workstreams.md) §Marker-4 scope).

**Detect → confirm → validate (REQ-ORCH-032).** Auto-detect the entry stage,
**present and confirm** it (override to an earlier stage only), then
**validate** that stage's upstream is approved — else route to the earliest
incomplete upstream and say why; never guess silently. An **entry kickoff**
(REQ-ORCH-033) records scope, entry stage and assumed-approved upstream, not
research questions; DISCUSS still runs first:
[`references/loop-control.md`](references/loop-control.md) §7.

## The Four Phases

```
DISCUSS  — converge with the operator on the idea (scope + open questions)
KICKOFF  — write the kickoff file (a research kickoff by default)
LOOP     — per stage [research … verify]: PIPELINE subagent → REVIEW subagent
           → operator GATE (proceed │ loop-back-to-fix │ stop); on fix,
           re-dispatch PIPELINE with findings + paths only and re-review
DONE     — the verify stage passes review AND the operator approves
```

## DISCUSS

Before writing any kickoff, reach a shared understanding of the idea with the
operator. **Reuse the brainstorming process** — a brainstorming skill if one is
available, else the equivalent inline: explore intent, challenge assumptions,
surface scope boundaries, capture the open questions research should answer.
Exit DISCUSS when you both agree on scope and those questions.

## KICKOFF

Write the converged discussion into the cycle's kickoff file — the **only** new
on-disk artifact type the driver introduces, git-tracked like any SDD artifact.
**Path — version gate:** marker ≠ `4`, the flat `docs/handoff/kickoff.md`
(UNCHANGED); marker `4`, the per-workstream `docs/ws/<id>/kickoff.md`
([`references/v4-workstreams.md`](references/v4-workstreams.md) §Kickoff path).

**By default** the kickoff is a **research kickoff** (questions, success
criteria, budget, out-of-scope) and the LOOP begins at research. Assign the
cycle's research ID centrally at KICKOFF — the next `RS-NNN` (marker `4`:
`RS-<WS>-NNN`) — and record it in the frontmatter as `research_id:`; phase
detection checks **that spike's** findings, never "any `RS-*`". A
**non-research entry** writes an **entry kickoff** instead (§Entry Points). The
kickoff carries **no loop log** — the SDD artifacts are the source of truth for
resume.

**Frontmatter — `date:` is mandatory (REQ-HARN-002)**, beside `research_id:`:
it is the primary source for the replan re-entry cap (§The gate).
**Pre-pipeline self-checks** (not lint — you check yourself): both fields
present before the first pipeline dispatch, and every dispatch's `Budget:` slot
non-empty in observable units
([`references/return-contract.md`](references/return-contract.md) §Budget grammar).

**Telemetry opt-out (one prompt, REQ-TELEM-HARNESSP2-004).** Ask once at
KICKOFF — `telemetry: on (default) │ off` — and hold the answer as session
state for the cycle; it is never written to the kickoff
([`references/telemetry.md`](references/telemetry.md) §3).

## LOOP

For each stage in order — research, requirements, specs, plan, implement,
verify — run pipeline → review → gate.

**Return contract.** Every leaf dispatch ends with a structured `RETURN:` block
(`status:` first) and `review` emits an own-line `VERDICT:` token. Parse
both — never prose; malformed returns and reviews pause at the gate. Keys,
packet shape, branching, finding → chunk mapping, pruned-state check:
[`references/return-contract.md`](references/return-contract.md).

**Write scope.** Every leaf template declares `Write scope:` (review and
verifier: `(empty — read-only)`). Around every dispatch take
`snapshot(before)` / `snapshot(after)`, tag each written path `IN` /
`ADVISORY` / `OUT`, and surface an own-line `SCOPE: CLEAN | VIOLATION (N
paths)` before the verifier, the gate and any commit; commit ownership is fixed
per dispatch type: [`references/write-scope.md`](references/write-scope.md).

**Telemetry.** Default **on** (opt-out at KICKOFF only). After **each gate**
append **one record per dispatch, for every kind** — counts, enums, shas,
timestamps, never finding text — to the gitignored `.sdd/telemetry.jsonl`; no
leaf writes it and no skill reads it (**never read by phase detection**), and
readers are post-cycle only. Schema, per-kind clauses, the `commit` group, the
`.gitignore` bookkeeping, readers and the `TELEMETRY:` lines:
[`references/telemetry.md`](references/telemetry.md) §2–§3.

### Per-stage dispatch model

Issue **two separate subagent dispatches** per stage — never one combined —
and run the **pipeline** dispatch to completion (artifacts on disk) **before**
constructing the **review** dispatch, whose only inputs are the produced paths.

### Pipeline subagent dispatch

The pipeline subagent invokes `<stage>` and writes the stage's
artifact(s). A subagent is **non-interactive**, so the dispatch prompt MUST
**front-load every decision** (scope, success criterion, explicit budget, exact
deliverable contract), **assign IDs centrally**, **pin the absolute working
directory**, and carry the **non-interactivity clause** and the
**labeled-content fallback**
([`references/dispatch-templates.md`](references/dispatch-templates.md)).
**Provision at the tip the leaf is told to reach** — every worktree is
provisioned at the workstream branch tip (marker `4`; `main`/HEAD under marker
`3`), so the prompt names no catch-up commit; the named-base `CATCH-UP`
fallback: [`references/write-scope.md`](references/write-scope.md) §3.

### Per-chunk implement dispatch and per-chunk gate

In **sequential mode** the implement stage is dispatched **per chunk, in plan
order** — one PIPELINE dispatch per `### Chunk N:` header — and every chunk
closes at a lightweight **per-chunk gate** before the next is dispatched. After
each return the read-only **chunk verifier**, a second independent executor of
the chunk-close layer, returns `CHUNK_VERDICT: PASS | FAIL`; `implement`
itself is unchanged (REQ-ORCH-001; `docs/spec/harness-chunk-verifier.md`). The
loop, gate defaults, the per-chunk redo counter (`Redo: N of 3` against
`REDO_MAX`), FAIL routing, the once-only implement-stage review and verifier
edge cases: [`references/loop-control.md`](references/loop-control.md) §1.
The gate block —
the **one canonical copy** in this skill, identical in content to the copies in
`harness-chunk-verifier.md` §Sequencing — Sequential Mode,
`harness-write-scope.md` §Commit Ownership and `orchestration.md` §v5, and
byte-identical to the latter two: it keeps the gate's two-space indentation on
the `CHUNK_VERDICT:` line, where the chunk-verifier spec alone renders that
token at column 0 to satisfy its file-wide no-indented-token criterion
(REQ-QIMPL-HARNESSP5-001). Under fan-out it is the per-leaf gate,
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

The review subagent invokes `review` against the pipeline's output and
enforces `review`'s prohibited-inputs list **at dispatch time** — isolation
does not depend on operator vigilance. **The dispatch MUST carry ONLY:** the
repository root; the deliverable artifact path(s); the upstream artifact path
(**omitted for the research stage**, whose kickoff is a prohibited input); the
`Budget:` and read-only `Write scope:` lines; and the instruction to invoke
`review`. Everything else — your reasoning, the pipeline subagent's
framing, kickoff prose, drafts — is prohibited; the reviewer reads the rest
from the repository. Template, per-slot rules and prohibited inputs:
[`references/dispatch-templates.md`](references/dispatch-templates.md) §REVIEW.

### The gate

After review, parse the own-line token — `VERDICT: APPROVE`,
`VERDICT: APPROVE_WITH_FIXES` or `VERDICT: REJECT` (last occurrence wins; never
classify from prose) — surface it with the review's return text and **wait**
for an explicit decision; never auto-advance. Choices per token and per
`RETURN.status`: `references/return-contract.md` §6, §7.

**Chunk verifier token (REQ-HARN-HARNESSP4-007).** At the per-chunk gate parse
`CHUNK_VERDICT: PASS | FAIL` on the **last non-blank line**, at column 0 as
`^VERDICT:` and `^RED_VERDICT:` are; otherwise it is a malformed return
([`references/return-contract.md`](references/return-contract.md) §1).

| Decision | Action |
|----------|--------|
| **proceed** | Advance to the next stage. |
| **loop-back-to-fix** | Re-dispatch the pipeline subagent with a repair packet (findings + paths by construction — `references/return-contract.md` §3; never a re-litigation of the reviewer's reasoning), then re-run the review for this stage. |
| **stop** | Halt the loop; leave artifacts as-is. |

**Post-gate aggregate regeneration (marker `4` — REQ-WS-HARNESSP3-001).**
After the decision is collected, on **every** outcome, regenerate
`docs/requirements/traceability.md` wholesale from the per-ws files in the
orchestrator's **own** bookkeeping commit — dirty-flag driven, run after the
snapshot window closes, never written by a leaf:
[`references/write-scope.md`](references/write-scope.md) §7.

**Rendering and collecting.** Render the gate block **verbatim as text** — a
fixture whose signal order is the contract — then collect the decision through
the host's option picker when one exists. **Rendering is not asking**: a turn
ending on a rendered block without a picker call leaves the loop ungated.
Picker rules, fallback, shortcut: [`references/loop-control.md`](references/loop-control.md) §5a.

**Gate signals — REQ-ORCH-034 order (pointers only).** The **canonical** order
and every per-signal rule live in
[`references/loop-control.md`](references/loop-control.md) §5; the summary
below never restates it in a form that can diverge. In production order, all
ephemeral (REQ-ORCH-013):

| # | Signal | Where |
|---|--------|-------|
| 1 | `RETURN.status` + `budget_consumed` vs the dispatched `Budget:` | per-chunk gate |
| 2 | the own-line `SCOPE:` token; a `VIOLATION` block renders each finding by name — `HISTORY_REWRITE`, and `GIT_STATE` for git-state mutation by a read-only leaf | per-chunk gate |
| 3 | per chunk, `CHUNK_VERDICT:` with `Redo: N of 3` | per-chunk gate |
| 3b | verify only: `RED_VERDICT:` with its `Rn` lines verbatim, then — on a red round N >= 2 — the derived `RED: Rn new-ground \| regression` lines, before the exit rule and before (4) | stage gate |
| 4 | the review `VERDICT:` | stage gate |
| 5 | the loop counters | stage gate |
| 6 | the `REVIEW: CONTRADICTION` pause block when it fires, after the counters | stage gate |
| 6b | implement only: the plan completion parse `PLAN: INCOMPLETE (N of M ticked)`, pausing with `replan │ stop` **only** and suppressing (6)'s options — signal 6's block still renders, only its options are suppressed | stage gate |
| 6c, 7 | the informational own-line `CONVERGENCE:` token — one line per cluster whose second member arrived here, naming its key (shared id, sectionless file, or file and section), the layers and the layer count; no option set, never pauses, never withholds `proceed` — then the `TELEMETRY:` line, last, before the options | every gate |
| 8 | **post-decision**: the own-line `COMMIT: COMPLETE \| INCOMPLETE` closing line right after the orchestrator's own commit (or the fan-out merge; pre-decision at 2b for a fan-out per-leaf gate), pausing on `INCOMPLETE` with `amend \| accept (note) \| stop` before any next dispatch ([`references/write-scope.md`](references/write-scope.md) §7a) | after the decision |
| 8b | implement `proceed` only, after (8): the orchestrator — the sole writer of the plan's `status:` under orchestration — flips `docs/ws/<id>/plan.md` to `status: complete` in its own bookkeeping commit, editing `status:` only and leaving `research_id:` untouched | after the decision |

**Red team (verify stage only, opt-in — REQ-REDB-HARNESSP2-001, -007, -008).**
Ask `red team: off | on` (default `off`) before dispatching the verify
pipeline. With `on` the pipeline carries `Red team: enabled` (`verify`
writes `status: pending-red`, never `pass`) and ONE read-only RED TEAM leaf
follows each `COMPLETE` blue return, before the review; parse
`RED_VERDICT: BROKEN | HELD` on the last non-blank line. `proceed` iff
`VERDICT ≠ REJECT` ∧ (red not run ∨ `HELD` ∨ every `BROKEN` `Rn`
fixed/accepted), and on `proceed` flip `pending-red → pass` — the same flip
turns every `Verified` cell reading `pending-red` to `pass` in the
workstream's own traceability file (REQ-REDB-HARNESSP3-003). Rounds, the
`BROKEN` options, the round-N>=2 `RED:` derivation, the blue-fail case, the
fixture and token parsing:
[`references/loop-control.md`](references/loop-control.md) §2a "Red round" and
[`references/return-contract.md`](references/return-contract.md) §6a.

**`TELEMETRY:` lines** — the four-member family `rec <n>` │ `WRITE FAILED` │
`OFF` │ `.gitignore updated` (`rec <n>` the positive member, `<n>` = successful
appends this session) — render at most once each, after the `iteration`/cap
line (or the `REVIEW: CONTRADICTION` token line when that pause fired) and
before the options: [`references/telemetry.md`](references/telemetry.md) §3.

**Fix-loop cap (REQ-HARN-001).** `FIX_LOOP_MAX` (default **3**) is per stage,
session-only, incremented once per fix re-dispatch, which carries the literal
`iteration N of 3`; the operator may raise the cap by one per explicit gate
decision; on exhaustion the gate renders the **compiled findings log** with
`stop | manual intervention | authorize extra iteration` only:
[`references/loop-control.md`](references/loop-control.md) §2.

**Replan re-entry cap (REQ-HARN-002, REQ-HARN-003).** `REPLAN_MAX` (default
**3**) is never stored: recount the `-replan-` archives in `plan-history/`
dated ≥ the kickoff's `date:` on every replan trigger (legacy fallback
`git log -S'research_id: <id>'`; neither determinable → **treated as
reached**); at or past the cap route into `replan` only on an explicit
operator decision at a gate event naming count, cap and archive filenames:
[`references/loop-control.md`](references/loop-control.md) §3.

**Edge cases routed through the gate** — a replan trigger; a reject with no
actionable findings; `REVIEW: MALFORMED`; `RETURN: MALFORMED (<reason>)`; and
`REVIEW: CONTRADICTION (round N vs round N+1, class b|c)` — each with its own
option set in [`references/loop-control.md`](references/loop-control.md) §6.

## Reviews Are Ephemeral

A review verdict is the review subagent's return text, surfaced inline. Never
write verdicts to disk or create a `docs/reviews/` directory; decisions land in
the artifacts themselves — commits, spec edits, Q-IMPL entries, replans.

## Execution Model

**Sequential is the default**; only the implement stage may fan out, on
explicit operator opt-in at its gate, where the **chunk verifier** is also
recorded as running this cycle (on by default, disableable there only, never
persisted). **Implement-stage fan-out (Design B — active, opt-in)** is
**orchestrator-owned and one level deep**: fan out along the independent
branches of the plan's **chunk dependency graph** (read each chunk's
`**Depends on**: Chunk N` field — never modify `implement`), one
worktree/branch and one **leaf** implement subagent per group dispatched in one
batch (a leaf cannot sub-dispatch, REQ-ORCH-022), per-leaf gate, then
sequential merges — all before the implement-stage review — and teardown.
Design A (a pipeline subagent owning nested fan-out) is **ruled out
infeasible**: a dispatched subagent has no subagent-dispatch tool (RS-006 Q1).
**Degrade to sequential** (never guess a boundary) when dependencies are
unparseable or the
graph is a single chain; on a merge conflict abort that merge and **redo the
chunk-group by re-derivation**, never replay the stale patch.

**Integration anchor — version gate.** `docs/.sdd-version` is the **sole**
gate. Marker ≠ `4`: behavior UNCHANGED — fan-out branches from and merges into
`main`. Marker `4`: the workstream branch is the anchor (REQ-WS-016..018;
[`references/v4-workstreams.md`](references/v4-workstreams.md) §Integration
anchor). Boundary derivation, the opt-in gate, the command sequence, conflict
handling and teardown: [`references/fan-out.md`](references/fan-out.md) §0–§3
(summary: [`references/loop-control.md`](references/loop-control.md) §4).

## Orchestrator-Only Work and Isolation Discipline (normative)

A dispatched subagent's toolset contains **no dispatch tool** (RS-006 Q1), so
work that requires dispatching a subagent is yours — implement-stage fan-out
execution, and any spike that measures or uses dispatch; ordinary stage work
stays delegable. **Routing is orchestrator-only (REQ-HARN-019)**: verdict and
`SCOPE:` interpretation, cap arithmetic, repair-packet composition and the
decision to merge, re-dispatch, replan or stop never appear in any template —
templates say what to *produce*, never what to *decide next*.

The driver MUST (1) dispatch the pipeline and the review as **two separate
subagents** per stage; (2) construct the review dispatch from **artifact paths
only**; (3) on a fix loop pass the pipeline subagent **only** the findings plus
paths; and (4) on a failed write-scope ancestry check surface
`HISTORY_REWRITE`, count it as a `SCOPE: VIOLATION` and offer **only `stop`** —
never reset, force-move or merge a rewritten branch on your own initiative.

Full text of all four rules, the two orchestrator-only cases and the routing
list: [`references/isolation.md`](references/isolation.md).

## Rules

Five invariants govern every cycle: **compose, never reimplement**; **two
dispatches per stage** with **paths only to the reviewer**; a **human gate at
every stage**; **reviews ephemeral**, artifacts the source of truth for resume;
**sequential by default** (fan-out at the implement gate on opt-in only,
mid-pipeline entry per §Entry Points). In full: [`references/loop-control.md`](references/loop-control.md) §8.

## Transition

When the verify stage passes review and the operator approves, the cycle is
DONE. Recommend committing the cycle's artifacts (including the kickoff). Then
run `python3 <skill-dir>/tools/gc.py --report --root . [--workstream <id>]`, render its findings
at the DONE gate and route each — mechanical → `--fix <rule>`;
needs-a-decision → `record | ignore`; out-of-scope → note — per
[`references/drift-sweep.md`](references/drift-sweep.md) §2. gc never runs
between stages, never blocks a gate and never touches a plan task.
