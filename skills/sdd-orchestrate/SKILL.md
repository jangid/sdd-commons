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
cannot leak (repo-level context — `CLAUDE.md`, project memory — is still
inherited; the guarantee covers the session's reasoning and drafts, not repo docs).

**Scope**: research-entry by default, sequential by default. When approved
upstream artifacts already exist the operator may start **mid-pipeline** (§Entry
Points). Implement-stage **fan-out** is an opt-in mode at the implement gate
(§Execution Model); every other stage is always sequential.

## Phase Detection

The driver introduces **no loop-position marker**. On entry — including re-entry
in a fresh session mid-loop — derive the current loop position from the existing
SDD artifacts, reusing the stage skills' own phase detection:

**Upgrade offer (entry, all markers, REQ-WS-030).** First read `docs/.sdd-version`;
if it is behind the latest supported marker (`4`), offer `/sdd-migrate` once —
informational, never forcing: [`references/v4-workstreams.md`](references/v4-workstreams.md) §Upgrade offer.

**Drift sweep at entry (REQ-GC-HARNESSP2-005).** Before the workstream picker
(marker `4`) / before phase detection (marker `3`) run `python3 tools/sdd-gc.py --report`
and render one line — `GC: clean` or `GC: F fail, W warn — run tools/sdd-gc.py --report` —
then open the picker regardless (informational, never a gate): [`references/drift-sweep.md`](references/drift-sweep.md) §1.

**Workstream & version gate (v4).** Under `docs/.sdd-version` ≠ `4` behavior is
UNCHANGED — ignore the `workstream` argument, derive loop position from the flat
artifacts below and never read `docs/ws/`. Under marker `4` execution artifacts
are rooted at `docs/ws/<ws>/`: [`references/v4-workstreams.md`](references/v4-workstreams.md) §Workstream & version gate.

**Cycle identity (REQ-CYCID-HARNESSP3-001, -002).** Before reading a
**completion signal** as "this cycle is done" — `verification.md` `status: pass`,
or `plan.md` `status: complete` with every task `[x]` — compare that artifact's
frontmatter `research_id:` against the kickoff's (`docs/ws/<ws>/kickoff.md` under
marker `4`, `docs/handoff/kickoff.md` under marker `3`) by **exact string
equality** on the trimmed value — no normalisation, case folding or prefix
matching (Q-IMPL-HARNESSP3-015). The three cases are exhaustive:

1. **Mismatch** — the artifact's `research_id` differs from the kickoff's → **a
   previous cycle's artifact**; this stage has not been reached in this cycle.
2. **Field absent** — a kickoff with a `research_id` exists but the artifact
   carries none (legacy; existing files are **never back-filled**) → the same
   reading as a mismatch. Absence is the safe direction: it costs one re-entry,
   it never asserts a completion that did not happen.
3. **No usable discriminator** — no `kickoff.md` for this `(repo, workstream)`,
   **or** a kickoff that carries no `research_id` (Q-IMPL-HARNESSP3-016) → the
   comparison is **skipped entirely** and the existing `status:`-only rule
   applies unchanged. Cycle identity is an orchestrated-cycle discriminator,
   never a precondition for detection.

See `docs/spec/cycle-identity.md`. The last two rows of the table below
(`plan complete`, `verification.md` status pass) carry a completion signal and
are subject to it. **Nothing is demoted**: `references/loop-control.md` §3's
`git log -S'research_id: <id>'` runs against the **kickoff** and derives a
cycle-start *date* for the replan re-entry cap — a different thing from this
identity comparison, and its cap arithmetic is **unmodified**.

| On disk | Loop position |
|---------|---------------|
| no `docs/handoff/kickoff.md` | before KICKOFF — run DISCUSS |
| kickoff exists, its `research_id` spike has no Complete findings | at the research stage |
| research done, requirements `Draft`/missing | at the requirements stage |
| requirements `Approved`, specs missing/stale | at the specs stage |
| specs `Approved`, no `docs/plan.md` (or stale) | at the plan stage |
| plan has incomplete tasks | at the implement stage |
| plan complete, no/failing `docs/verification.md` | at the verify stage |
| `docs/verification.md` status `pending-red` | at the verify stage — resume before the red dispatch (never DONE, never replan) |
| `docs/verification.md` status pass | at DONE (pending operator approval) |

For an **entry kickoff** (§Entry Points) the stages before its recorded entry
stage are *intentionally absent*: derive loop position from the entry stage on,
never "at the research stage" from missing research artifacts. Tell the operator
the detected position and confirm before proceeding. A review leaves no on-disk
trace by design — it is **reproduced** by re-dispatching the review subagent.

**New cycle vs. resume.** A **complete** prior cycle (`status: pass`) is both
"DONE" and the next feature's starting point. Classify entry as **resume** (a
cycle is mid-loop → continue it), **done** (no new idea → report DONE) or **new
cycle** (a new idea → run DISCUSS and **overwrite** `docs/handoff/kickoff.md` at
KICKOFF). Only **operator intent** separates *done* from *new cycle*: surface your
interpretation and confirm, never silently report the prior DONE (no new marker; REQ-ORCH-014).

**Marker-`4` gate for done-vs-new-cycle.** Under marker ≠ `4` behavior is
UNCHANGED — the single global operator intent above resolves it; under marker `4`
it is per workstream via the picker: [`references/v4-workstreams.md`](references/v4-workstreams.md) §Marker-4 gate for done-vs-new-cycle.

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

Research is the **default** entry; when approved upstream artifacts already
exist the operator may start **mid-pipeline** (REQ-ORCH-031) at **requirements,
specs, plan, or implement** — **never verify** (verifying an existing project is
just `sdd-verify` directly, no loop). *Resume* continues a cycle **this driver**
started (kickoff + partial artifacts on disk); *non-research entry* begins a
fresh loop over artifacts produced **outside** this driver.

**Marker-`4` scope.** Mid-pipeline entry is a marker-`3` single-cycle concept
(behavior UNCHANGED there); under marker `4` a new workstream always begins at
research and selecting an existing one is resume, not entry — [`references/v4-workstreams.md`](references/v4-workstreams.md)
§Marker-4 scope.

**Detect → confirm → validate (REQ-ORCH-032).** Auto-detect the entry stage
(furthest-complete *approved* upstream → the next stage), **present and confirm**
it (the operator may override to an earlier stage, never a later one), then
**validate** that stage's upstream is approved — else route to the earliest
incomplete upstream and say why. Never guess an entry stage silently. An **entry
kickoff** (REQ-ORCH-033) records scope, entry stage and assumed-approved upstream —
not research questions; DISCUSS still runs first and the LOOP is identical from
the entry stage on: [`references/loop-control.md`](references/loop-control.md) §7.

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
Never jump straight to a kickoff or to implementation; exit DISCUSS when you both
agree on the idea, what is in and out of scope, and the questions worth researching.

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
cycle's research never masks the new one's (kickoffs predating the field: compare
findings dates against the kickoff's write date). A **non-research entry** writes
an **entry kickoff** instead (§Entry Points). The kickoff carries **no loop
log** — the SDD artifacts are the source of truth for resume.

**Kickoff frontmatter — `date:` is mandatory (REQ-HARN-002).** Every kickoff
this skill writes carries `date: YYYY-MM-DD` beside `research_id:` — the primary
source for the replan re-entry cap (§The gate); omitting it is a template
violation (only kickoffs predating this rule fall back to the
`git log -S'research_id: <id>'` derivation). **Pre-pipeline self-checks** (not
lint — you check yourself): the kickoff carries `date:` + `research_id:` before
the first pipeline dispatch, and every dispatch's `Budget:` slot holds a non-empty
value in observable units — never dispatch around an empty one:
[`references/return-contract.md`](references/return-contract.md) §Budget grammar.

**Telemetry opt-out (one prompt, REQ-TELEM-HARNESSP2-004).** Ask once at KICKOFF — `telemetry: on (default) │ off` — and hold the answer as session state for the whole cycle; it is never written to the kickoff ([`references/telemetry.md`](references/telemetry.md) §3).

## LOOP

For each stage in order — research, requirements, specs, plan, implement, verify
— run pipeline → review → gate.

**Return contract.** Every leaf dispatch ends with a structured `RETURN:` block
(`status:` first) and `sdd-review` emits an own-line `VERDICT:` token. Parse both
— never prose — branch on them, and compose any fix re-dispatch's repair packet
from the previous `RETURN`, the review's Critical/Material lines and disk paths
only; malformed returns and reviews pause at the gate. Keys, malformed rules,
packet shape, branching, finding → chunk mapping, pruned-state check:
[`references/return-contract.md`](references/return-contract.md).

**Write scope.** Every leaf template declares `Write scope:` (review and
verifier: `(empty — read-only)`). Around every dispatch take `snapshot(before)`
/ `snapshot(after)` (on return, before the verifier, the gate and your own commit
or merge), tag each written path `IN` / `ADVISORY` / `OUT`, and surface an
own-line `SCOPE: CLEAN | VIOLATION (N paths)` before the verifier, the gate and
any commit. `blocked_writes` are scope-matched before persistence; commit
ownership is fixed per dispatch type (pipeline: orchestrator on `proceed`;
fan-out leaf: the leaf; review/verifier: nobody): [`references/write-scope.md`](references/write-scope.md).

**Telemetry.** Default **on** (opt-out at KICKOFF only, §KICKOFF). After **each
gate** you append one record — counts, enums, shas, timestamps, never finding
text — to the gitignored `.sdd/telemetry.jsonl`; no leaf ever writes it and no
skill reads it: **never read by phase detection** — `rm -rf .sdd/` is
behaviour-neutral. Bootstrap: if `git check-ignore -q .sdd/telemetry.jsonl`
fails, append `.sdd/` to `.gitignore` as a bookkeeping commit outside any
observed window. Post-cycle reader: `python3 tools/sdd-telemetry.py summarize`.
Schema, writer rules, `TELEMETRY:` lines, third observation: [`references/telemetry.md`](references/telemetry.md).

### Per-stage dispatch model

Issue **two separate subagent dispatches** per stage — never one combined — and
run the **pipeline** dispatch to completion (artifacts on disk) **before**
constructing the **review** dispatch, whose only inputs are the produced paths.

### Pipeline subagent dispatch

The pipeline subagent invokes `sdd-<stage>` and writes the stage's artifact(s).
A subagent is **non-interactive** — nobody answers an `sdd-*` skill's questions —
so the dispatch prompt ([`references/dispatch-templates.md`](references/dispatch-templates.md))
MUST **front-load every decision** (scope, success criterion, explicit budget,
exact deliverable contract — files + frontmatter); **assign IDs centrally** (you
pick the next `RS-NNN`; subagents never scan and choose — that collides under
parallel dispatch); **pin the absolute working directory** (phase detection reads
`docs/.sdd-version` relative to cwd; a wrong cwd silently misdetects); carry the
**non-interactivity clause** (no questions, no fabricated consent; gaps go under
Open Questions / Assumptions with a stated default) and the **labeled-content
fallback** (an unwritable file is returned in full, target path labeled).
**Provision at the tip the leaf is told to reach**: a sequential-pipeline or fix
dispatch's worktree is provisioned at the workstream branch tip (marker `4`;
`main`/HEAD under marker `3`) so the prompt names no catch-up commit and
`snapshot(before)` is taken there — verifier, review and red worktrees the same
way; the named-base `CATCH-UP` fallback: [`references/write-scope.md`](references/write-scope.md) §3.

### Per-chunk implement dispatch and per-chunk gate

In **sequential mode** the implement stage is dispatched **per chunk, in plan
order** — one PIPELINE dispatch per `### Chunk N:` header (`Chunk {N}` slot,
`references/dispatch-templates.md` §PIPELINE) — and every chunk closes at a
lightweight **per-chunk gate** before the next chunk is dispatched. After each
return dispatch the read-only **chunk verifier** (`references/dispatch-templates.md`
§CHUNK VERIFIER), a second independent executor of the chunk-close layer that
returns `CHUNK_VERDICT: PASS | FAIL`. `sdd-implement` itself is unchanged
(REQ-ORCH-001; contract `docs/spec/harness-chunk-verifier.md`). The loop, gate
defaults, the per-chunk redo counter (`Redo: N of 3` against `REDO_MAX`,
incremented only on `fix`), FAIL routing, the once-only implement-stage review
and verifier edge cases: [`references/loop-control.md`](references/loop-control.md) §1.
The gate block — the **one canonical copy** in this skill, byte-identical to
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

The review subagent invokes `sdd-review` against the pipeline's output and
enforces `sdd-review`'s prohibited-inputs list **at dispatch time** — isolation
does not depend on operator vigilance. Template:
[`references/dispatch-templates.md`](references/dispatch-templates.md) §REVIEW.

**The review dispatch MUST carry ONLY:** the repository root; the deliverable
artifact path(s) — for the **implement stage** the plan path plus the source/test
files changed during the stage (`git diff --name-only` against the stage-start
commit); the upstream artifact path — **omitted for the research stage** (the
kickoff prompt is a prohibited input; `sdd-review` reads the questions from the
findings frontmatter); the `Budget:` and read-only `Write scope:` lines; and the
instruction to invoke `sdd-review`. **It MUST NOT carry** your conversation or
reasoning, the pipeline subagent's reasoning or framing, kickoff prose beyond the
artifact, or any draft or intermediate state (§Isolation Discipline); the
reviewer reads all other context from the repository itself.

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

**Post-gate aggregate regeneration (marker `4` — REQ-WS-HARNESSP3-001).** After
the decision is collected, on **every** outcome — `proceed`, `loop-back-to-fix`
and `stop` alike — and before the session ends, regenerate
`docs/requirements/traceability.md` wholesale from the per-ws
`docs/ws/<id>/traceability.md` files and commit it in the orchestrator's **own**
bookkeeping commit, separate from the stage/chunk commit
(`references/write-scope.md` §7; `references/fan-out.md` §3e is the fan-out path
of the same step). Trigger: a **session dirty flag**
(`docs/spec/ws-traceability.md` Q-IMPL-HARNESSP3-011) set whenever a leaf's
`RETURN.traceability_fills` is non-empty and cleared after a successful
regeneration commit — so a gate whose flag is clear regenerates nothing, and a
stopped or looped-back stage never leaves the aggregate stale. The flag is
session state, not an artifact; on a resumed session it starts set, costing at
most one redundant regeneration (the operation is wholesale and idempotent) and
never a missed one. The regeneration runs **after** the snapshot window closes,
so it is never observed by the write-scope check. Leaves never write this path:
it is absent from every orchestrated `{write_scope}` by construction
(`references/write-scope.md` §2), and that absence is the signal the leaf reads.

**How the decision is collected (presentation only).** Render the gate block
verbatim as text — it is a fixture, and its signal order is the contract — then
collect the decision through the host's option picker when the session has one,
listing the gate's options as the choices, and fall back to plain text when it
does not. The picker never replaces, summarizes or reorders the block above it,
and never adds an option the gate does not offer. This binds nothing about the
loop: the options, their meaning and the caps are unchanged.

**Approve-with-fixes shortcut.** For `APPROVE_WITH_FIXES` (`sdd-review`: "fix
the named findings, then proceed without re-review") **loop-back-to-fix** offers
re-dispatch then re-review (default) or skip the re-review; *Reject* never skips it.

**Gate signals — REQ-ORCH-034 order (pointers only).** The **canonical** order
and every per-signal rule live in
[`references/loop-control.md`](references/loop-control.md) §5; this is the
one-line summary and never restates the order in a form that can diverge from
it. In production order, all ephemeral (REQ-ORCH-013): (1) `RETURN.status` +
`budget_consumed` vs the dispatched `Budget:`; (2) the own-line `SCOPE:` token;
(3) per chunk, `CHUNK_VERDICT:` with `Redo: N of 3` — 1–3 render at the
**per-chunk gate**; (3b) verify stage only, `RED_VERDICT:` with its `Rn` lines
verbatim, then — on a red round N >= 2 — the derived `RED: Rn new-ground |
regression` lines after them, before the exit rule and before (4); (4) the
review `VERDICT:`; (5) the loop counters; (6) the `REVIEW: CONTRADICTION` pause
block when it fires, after the counters; (7) the `TELEMETRY:` line, last, before
the options — 3b–7 render at the **stage gate**; (8) **post-decision**, the
own-line `COMMIT: COMPLETE | INCOMPLETE` closing line rendered right after the
orchestrator's own commit (or the fan-out merge; pre-decision at 2b for a
fan-out per-leaf gate), pausing on `INCOMPLETE` with `amend | accept (note) |
stop` before any next dispatch — comparands and pause in
[`references/write-scope.md`](references/write-scope.md) §7a, position in
`loop-control.md` §5.

**Red team (verify stage only, opt-in — REQ-REDB-HARNESSP2-001, -007, -008).**
Ask `red team: off | on` (default `off`; optional `red input: +verification.md`)
before dispatching the verify pipeline. With `on` the pipeline carries
`Red team: enabled` (`sdd-verify` writes `status: pending-red`, never `pass`)
and ONE read-only RED TEAM leaf (`references/dispatch-templates.md` §RED TEAM)
follows each `COMPLETE` blue return, before the review; parse
`^RED_VERDICT: BROKEN | HELD` on the last non-blank line
(`references/return-contract.md` §6a — malformed table, `FOREIGN_TOKEN`).
`proceed` iff `VERDICT ≠ REJECT` ∧ (red not run ∨ `HELD` ∨ every `BROKEN` `Rn`
fixed/accepted); per `BROKEN` line `fix (RED_BREAK packet) | accept (record) |
stop` (`accept` records the `Rn` under `verification.md` §Issues Found → Minor).
Blue `status: fail` or a non-`COMPLETE` return → `Red team: not run`, no red
dispatch. On a red round **N >= 2**, before applying the exit rule, re-run the
**previous round's** routed `reproduce:` command for each `BROKEN` `Rn` (held
verbatim) and render the derived `RED:` lines at the position given in the
signal order above — `new-ground` when that command now passes, `regression`
when it still fails (REQ-REDB-HARNESSP3-002); red's return shape is unchanged.
On `proceed` flip `pending-red → pass` immediately before the
orchestrator's commit (its only writer). **The same flip turns every
`Verified` cell reading `pending-red` to `pass`** — in the workstream's own
`docs/ws/<id>/traceability.md`, leaving `fail` cells untouched — and
regenerates the shared aggregate in the same post-gate bookkeeping step above
(REQ-REDB-HARNESSP3-003). Rounds, the `accept` line format and
the gate fixture: [`references/loop-control.md`](references/loop-control.md) §2a "Red round".

**`TELEMETRY:` lines** — the four-member family `rec <n>` │ `WRITE FAILED` │ `OFF` │ `.gitignore updated` (`rec <n>` is the positive member, `<n>` = successful appends this session) — render at most once each, immediately after the `iteration`/cap line (or after the `REVIEW: CONTRADICTION` token line when that pause fired) and before the options — [`references/telemetry.md`](references/telemetry.md) §3, signal (7) of [`references/loop-control.md`](references/loop-control.md) §5.

**Fix-loop cap (REQ-HARN-001).** `FIX_LOOP_MAX` (default **3**) is per stage,
session-only, incremented once per fix re-dispatch (never on `proceed`, `stop`
or a replan route); every fix re-dispatch carries the literal `iteration N of 3`
in its repair packet; the operator may raise the cap by one per explicit gate
decision; on exhaustion no further fix is dispatched — the gate renders the
**compiled findings log** and offers only `stop | manual intervention |
authorize extra iteration`: [`references/loop-control.md`](references/loop-control.md) §2.

**Replan re-entry cap (REQ-HARN-002, REQ-HARN-003).** `REPLAN_MAX` (default
**3**) is never stored: on every replan trigger recount the `-replan-` archives
in `plan-history/` dated ≥ the kickoff's `date:` (legacy fallback
`git log -S'research_id: <id>'`; neither determinable → **treated as reached**).
At or past the cap, surface a gate event (REQ-ORCH-017 shape) naming count, cap
and archive filenames and route into `sdd-replan` only on an explicit operator
decision — never silently unreachable: [`references/loop-control.md`](references/loop-control.md) §3.

**Edge cases routed through the gate** — a replan trigger (a gate event, never
silently absorbed); a reject with no actionable findings (pause, operator
decides); `REVIEW: MALFORMED` (pause: `re-dispatch review | accept prose
manually | stop`); `RETURN: MALFORMED (<reason>)` (pause with the raw tail;
never treat as `COMPLETE`); `REVIEW: CONTRADICTION (round N vs round N+1, class b|c)`
(stage-gate pause when a later review round raises new ground or regresses without it: `accept round N+1 (fix) | accept round N (proceed, note) | third opinion (re-dispatch review) | stop`): [`references/loop-control.md`](references/loop-control.md) §6.

## Reviews Are Ephemeral

A review verdict is the review subagent's return text, surfaced inline. Never
write verdicts to disk or create a `docs/reviews/` directory; decisions land in
the artifacts themselves — commits, spec edits, Q-IMPL entries, replan triggers.

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
Fan-out is **opt-in at the implement gate**, never automatic: surface how many
independent chunk-groups the plan yields (a single chain → say it degrades to
sequential); the same gate records whether the **chunk verifier** runs this cycle
(on by default; disableable at this gate only, as gate text, never persisted):
[`references/fan-out.md`](references/fan-out.md) §1.

### Lifecycle and conflict handling

Provision one worktree/branch per group yourself; dispatch one leaf per group in
one batch and await all returns (a leaf cannot sub-dispatch, REQ-ORCH-022); run
the per-leaf gate; merge sequentially, all merges before the implement-stage
review; tear down after each clean merge. On a merge conflict abort that single
merge and **redo the chunk-group by re-derivation** — never replay the stale
patch; a group that still conflicts is a boundary error → run the affected
groups sequentially. Marker `3` runs against `main` UNCHANGED; marker `4` uses
the workstream branch (§Integration anchor). Summary: [`references/loop-control.md`](references/loop-control.md) §4;
commands: [`references/fan-out.md`](references/fan-out.md) §3.

## Orchestrator-Only Work

A dispatched subagent's toolset contains **no dispatch tool** (RS-006 Q1), so
work that requires dispatching a subagent is yours — never hand it to a pipeline
dispatch, which would stall or silently under-deliver. The two cases: (1)
**implement-stage fan-out execution** — provisioning worktrees and dispatching
one leaf per chunk-group is itself dispatch (why fan-out is Design B, not nested
Design A); (2) **a spike or task that measures or uses dispatch** — e.g. a
concurrency probe (the RS-006 spike was run this way). Ordinary stage work —
invoking an `sdd-*` skill, reading/writing files — stays delegable. The test:
*does executing this task require dispatching a subagent?* If yes, you do it.

**Routing is orchestrator-only (REQ-HARN-019).** Phase-detection relay;
`VERDICT:` classification; `CHUNK_VERDICT:`, `RED_VERDICT:` and `SCOPE:`
interpretation; fix / redo / replan cap arithmetic; repair-packet composition;
and the decision to merge, re-dispatch, replan or stop never appear as
instructions in any pipeline, fix, fan-out, verifier or review template.
Templates say what to *produce* (the `RETURN:` block, the `VERDICT:` token,
findings) — never what to *decide next*; `Write scope:` is a bound you check,
not something the subagent judges: [`references/return-contract.md`](references/return-contract.md) §9;
`SCOPE:` branching `references/write-scope.md`; counters `references/loop-control.md`.

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
   `HEAD_before` / `<base>`), surface `HISTORY_REWRITE` above the path list,
   count it as a `SCOPE: VIOLATION`, and offer **only `stop`** plus a `git reflog`
   hint; never reset, force-move or merge a rewritten branch on your own
   initiative (`references/write-scope.md` §3, §5).

Rules 1–3 mirror `sdd-review` Step 2's "Do NOT accept as inputs" list, enforced
at dispatch time; rule 4 is the write-scope analogue — observe and report.

## Rules

- **Compose, never reimplement**: stage logic lives in the nine `sdd-*` skills —
  dispatch them; never duplicate or modify them.
- **Two dispatches per stage, always**, and **paths only to the reviewer** —
  "helpful context" for the reviewer is exactly the leak the design prevents.
- **Human gate at every stage**: never auto-advance past a gate.
- **Reviews are ephemeral** (no `docs/reviews/`, no verdicts on disk) and
  **artifacts are the source of truth for resume** (no loop-position marker, no
  authoritative loop log).
- **Sequential by default**: fan-out only at the implement gate on operator
  opt-in with ≥2 independent chunk branches; mid-pipeline entry only per §Entry
  Points (detect → confirm → validate), never by guess.

## Transition

When the verify stage passes review and the operator approves, the cycle is
DONE. Recommend committing the cycle's artifacts (including `docs/handoff/kickoff.md`).
Then run `python3 tools/sdd-gc.py --report [--workstream <id>]` (marker `4`: the
completed workstream), render its findings at the DONE gate and route each per
[`references/drift-sweep.md`](references/drift-sweep.md) §2: mechanical → `--fix <rule>`
(operator reviews and commits); needs-a-decision → `record | ignore`, `record` appending
`- gc <rule>: <file:line> — <fix>` under that cycle's `verification.md` `## Next Steps`
outside any observed window; out-of-scope → note. gc never runs between stages, never
blocks a gate, is never scheduled or looped, and never creates or modifies a plan task.
