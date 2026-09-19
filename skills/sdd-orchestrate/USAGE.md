# `sdd-orchestrate` — Operator Guide

This is the **human-facing** guide to the `sdd-orchestrate` driver. The companion
[`SKILL.md`](SKILL.md) is the Claude-facing operational instruction; this file
explains how *you*, the operator, drive a cycle and what to expect at each step.

---

## 1. What it is

`sdd-orchestrate` runs the nine SDD phase skills (research → requirements →
specs → plan → implement → verify, plus replan/migrate/review) as a **single
operator-driven loop with built-in external review**. You stay in one session.
For each stage the driver dispatches two *separate, context-isolated* subagents —
one that does the work, one that reviews it — and then stops at a **gate** so you
can decide whether to proceed.

It is a **driver**, not a tenth phase skill: it composes the existing skills and
never reimplements them.

### When to use it
- You want to take an idea through a whole SDD cycle end-to-end.
- You want each stage independently reviewed by a reviewer that has **not** seen
  the working session's reasoning (catches scope/coherence gaps in-session checks
  miss).

### When **not** to use it
- You only need one phase → invoke that `sdd-*` skill directly.
- You only want to review one finished artifact → use `sdd-review`.

---

## 2. Installation

Claude Code discovers skills from `~/.claude/skills/`. This project keeps the
source of truth in the repo and **symlinks** each skill into that directory, so
edits to the repo are immediately live.

Install (or re-install) every SDD skill, including this one:

```bash
REPO="$HOME/work/github/jangid/tools-skills-agents"   # adjust to your checkout
for d in "$REPO"/skills/*/; do
  name="$(basename "$d")"
  ln -sfn "$d" "$HOME/.claude/skills/$name"
done
ls -l ~/.claude/skills/        # each entry should point back into the repo
```

To install just this skill:

```bash
ln -sfn "$HOME/work/github/jangid/tools-skills-agents/skills/sdd-orchestrate" \
        "$HOME/.claude/skills/sdd-orchestrate"
```

Notes:
- `ln -sfn` is idempotent — safe to re-run when you add a new skill or move the
  checkout. Re-run it whenever a **new skill** is added to `skills/` so its link
  appears in `~/.claude/skills/`.
- Skills are loaded at **session start**. After adding a link, start a new
  Claude Code session for the skill to become invocable.
- Verify with `ls -l ~/.claude/skills/` — every `sdd-*` entry should be a symlink
  back into `…/tools-skills-agents/skills/<name>`.

---

## 3. Invoking and driving the loop

You invoke the driver **once** and then mostly just talk to it. You do **not**
invoke each `sdd-*` skill yourself — the orchestrator does that for you.

### Start it

In a Claude Code session, either run the slash command:

```
/sdd-orchestrate
```

or ask in plain language:

> Use sdd-orchestrate to take "<your idea>" through a full SDD cycle.

Either way, Claude loads the driver and becomes the **orchestrator** for the rest
of the session.

### Then: discuss (DISCUSS)

The orchestrator opens by brainstorming the idea with you. Just talk — answer its
clarifying questions, push back, refine scope. Nothing is written to disk yet.
When you and it share an understanding of the scope and the open questions, DISCUSS
is done.

### Then: it picks up the loop on its own

Once you've converged, the orchestrator runs the rest **autonomously**, pausing
only at the gates:

1. It writes the kickoff (KICKOFF): `docs/handoff/kickoff.md` under marker `3`,
   or `docs/ws/<id>/kickoff.md` for the selected workstream under marker `4`.
2. For each stage (research → requirements → specs → plan → implement → verify) it
   dispatches the **pipeline** subagent, then the **review** subagent, handling
   skill invocation, ID assignment, paths, and isolation for you.
3. It **stops at each gate**, shows you the review verdict, and waits for your
   one-word decision: **proceed**, **loop-back-to-fix**, or **stop**.

So after DISCUSS your job shrinks to making gate decisions. You are not copy-
pasting between sessions or remembering which skill comes next — the orchestrator
sequences the whole loop and only ever hands control back at a gate.

### A typical exchange (abridged)

```
you  > /sdd-orchestrate
      Idea: add a --dry-run flag to the deploy tool.
orch > GC: clean                                  # drift sweep at entry — one line, never a gate
       A few questions before I write a kickoff:
       - dry-run prints the plan only, or a diff?  - exit-code contract? ...
you  > plan + diff; non-zero exit if drift. partial applies are out of scope.
orch > Good — we're aligned. Telemetry: on (default — say `telemetry: off` now to opt
       out for this cycle; records go to .sdd/telemetry.jsonl — gitignored,
       orchestrator-only, never read by phase detection).
       Writing docs/handoff/kickoff.md and starting research.
       [dispatches research pipeline → research review]
orch > GATE (research): reviewer says Approve. proceed / loop-back / stop?
you  > proceed
orch > [requirements pipeline → review]
       GATE (requirements): Approve with fixes — REQ-DRY-003 not testable. ...?
you  > loop-back-to-fix
orch > [re-dispatch with that finding → re-review] Approve now. proceed?
you  > proceed
       ... specs and plan, each with a gate ...
orch > [implement: Chunk 1 pipeline → scope check → chunk verifier]
       Per-chunk gate — implement dispatch #1 (Chunk 1: Dry-run flag)
         RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 18, test_runs: 2}  vs  Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs
         SCOPE: CLEAN
         CHUNK_VERDICT: PASS
         Files changed  : src/deploy/cli.py M, tests/test_dry_run.py A, docs/plan.md M
         Redo           : 0 of 3 (per-chunk redo counter)
         Options: proceed (orchestrator commits the chunk) │ fix (re-dispatch Chunk 1 with a repair packet; counts toward the per-chunk redo cap) │ stop
you  > proceed
       ... one per-chunk gate per remaining chunk, then ONE implement review ...
orch > GATE (implement): VERDICT: APPROVE. proceed / loop-back-to-fix / stop?
you  > proceed
       ... verify: red team: off | on? (default off)
you  > on
orch > [verify pipeline (Red team: enabled) → scope check → RED TEAM leaf → review]
       Verify stage gate — pipeline #9 (sdd-verify), red #10, review #11
         RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 41, test_runs: 6}  vs  Budget: ~70 tool calls
         SCOPE: CLEAN
         RED_VERDICT: HELD
         VERDICT: APPROVE
         iteration 0 of 3
         Options: proceed │ loop-back-to-fix │ stop
you  > proceed                       # orchestrator flips verification.md pending-red → pass, then commits
orch > DONE — verify passed review. Recommend committing the cycle.
       GC: clean                                  # drift sweep at DONE — findings would be routed here
       Post-cycle: python3 tools/sdd-telemetry.py summarize
```

### Coming back later (resume)

If you stop partway and return in a **new** session, just invoke
`/sdd-orchestrate` again. It reads the existing artifacts on disk, detects which
stage you're at (no hidden marker file), and continues the loop from there — re-
running the current stage's review if needed.

---

## 4. The four phases

```
DISCUSS ──▶ KICKOFF ──▶ LOOP ──▶ DONE
                          │
            ┌─────────────┴───────────────────────────┐
            │ per stage: pipeline ▶ review ▶ GATE      │
            └──────────────────────────────────────────┘
```

### DISCUSS
You and the orchestrator brainstorm the idea until you share an understanding of
scope and the open questions worth researching. It reuses the brainstorming
process — expect to be asked clarifying questions. Nothing is written yet.

### KICKOFF
The orchestrator writes the kickoff (`docs/handoff/kickoff.md`; marker `4`:
`docs/ws/<id>/kickoff.md`) — a **research kickoff** stating
the questions, success criteria, a budget, and what's out of scope. This is the
only new artifact type the driver introduces, and it's committed with the cycle.

### LOOP
For each stage in order, three things happen:
1. **Pipeline subagent** — a fresh subagent invokes the stage skill
   (`sdd-research`, `sdd-requirements`, …) and writes the normal SDD artifact(s).
2. **Review subagent** — a *separate* fresh subagent is given **only** the
   artifact paths and told to invoke `sdd-review`. It returns a tiered verdict.
3. **Gate** — the orchestrator shows you the verdict and waits. You choose:
   - **proceed** → next stage,
   - **loop-back-to-fix** → re-run the pipeline with just the review findings,
     then re-review,
   - **stop** → halt.

### DONE
Reached when the verify stage passes review **and** you approve. Commit the
cycle's artifacts (including the kickoff — `docs/handoff/kickoff.md`, or
`docs/ws/<id>/kickoff.md` under marker `4`).

---

## 4b. Workstreams (marker `4`)

If `docs/.sdd-version` reads `4`, the driver opens with a **workstream picker**:
it lists every `docs/ws/<id>/` workstream with its description and detected
phase, and you select one or create a new one. Several workstreams can be live
at once, each at its own phase, each on its own git branch, integrating via a
PR to `main` when complete.

- **Solo use stays ceremony-free** — a repo whose only workstream is `default`
  collapses to a picker of one; you never name anything.
- **New workstreams always start at research** — cheap when the shared corpus
  already covers the need, because research records a fast "covered by shared
  corpus" early-exit and moves on.
- **Execution artifacts move; the corpus doesn't** — kickoff/plan/verification
  live under `docs/ws/<id>/`; requirements, specs, and research stay shared at
  top level.
- **Fan-out and verification re-anchor** — implement-stage fan-out branches from
  and merges back into the *workstream branch* (`main` is untouched until the
  PR), and `sdd-verify` diffs against the workstream's branch point, not `main`
  HEAD.

Under marker `3` none of this appears — the driver runs the single flat cycle
exactly as described above.

---

## 5. A complete worked example

Idea: *"Add a `--dry-run` flag to our deploy tool."*

1. **DISCUSS.** Orchestrator: "What should `--dry-run` print — the plan only, or a
   diff? Any exit-code contract?" You converge: print the plan + non-zero exit if
   drift detected; out of scope: partial applies.
2. **KICKOFF.** Orchestrator writes `docs/handoff/kickoff.md` with the research
   questions ("does the deploy SDK expose a plan-only mode?"), a 1-hour budget,
   and scope boundaries.
3. **LOOP — research.** Pipeline subagent runs `sdd-research`, writes
   `docs/research/RS-007-dry-run/findings.md`. Review subagent (paths only) returns
   *Approve*. Gate → you say **proceed**.
4. **LOOP — requirements.** Pipeline writes the requirements; review returns
   *Approve with fixes* ("REQ-DRY-003 isn't testable"). Gate → you say
   **loop-back-to-fix**. Orchestrator re-dispatches the pipeline with just that
   finding; re-review returns *Approve*. Gate → **proceed**.
5. **LOOP — specs / plan / implement / verify.** Same rhythm. At implement, the
   pipeline runs `sdd-implement`; at verify, `sdd-verify` writes
   `docs/verification.md`. Each stage is reviewed and gated.
6. **DONE.** Verify passes review, you approve, the orchestrator recommends
   committing the cycle.

You made a decision at six gates; the reviewer never saw your reasoning, only the
artifacts on disk.

---

## 6. Isolation — why two subagents

The review subagent is dispatched with **only**: the repo root, the deliverable
path(s), and (for non-research stages) the upstream artifact path. It never
receives your conversation, the pipeline subagent's reasoning, kickoff prose, or
drafts. Because a freshly dispatched subagent starts with an empty context
window, there is *nothing to leak through* — a stronger guarantee than two human
terminals. (Caveat: the subagent still reads repo-level context like `CLAUDE.md`;
what's excluded is the working session's reasoning, not repo docs.) This is what
lets the review catch framing/scope problems an in-session check would
rationalize away.

(The research stage is special: the review dispatch omits the kickoff path,
because `sdd-review` forbids kickoff prompts as input. The reviewer reads the
research questions from the findings file's own frontmatter.)

---

## 7. Troubleshooting

| Symptom | Cause | What to do |
|---------|-------|------------|
| A pipeline subagent reports "could not write file — returning content inline" | The harness can block a subagent's disk write (especially report-style files or non-conventional paths). Observed live in RS-005. | This is expected and handled: the dispatch template's **labeled-content fallback** returns the file body; the **orchestrator persists it**. No action needed beyond confirming the artifact landed. |
| Pipeline subagent asks a question / stalls | A stage skill's "ask the user" step wasn't front-loaded. | The orchestrator must front-load the stage's question, success criterion, budget, and deliverable contract, plus a non-interactivity clause. Re-dispatch with those filled in. |
| Two artifacts collide on the same ID | A subagent picked its own ID. | The orchestrator assigns IDs centrally and passes them verbatim — never let the subagent scan-and-guess. |
| Review verdict seems to know your reasoning | Isolation leak — prohibited input slipped into the review dispatch. | Reconstruct the review dispatch from paths only (see `references/dispatch-templates.md`). |
| Review returns *Reject* with no actionable findings | Genuine reviewer uncertainty. | The driver pauses; you decide: re-dispatch, override, or stop. |
| A stage triggers a replan | Stuck detection / spike invalidation / verify failure. | It surfaces at the gate as a replan event; you may route back via `sdd-replan`. |

---

## 7b. Gate signals and caps (v5)

The harness-hardening cycle (v5) made the gates machine-checkable without
changing the phases, the artifacts or the one-word decisions you already make.
This section is what the new lines mean when you see them.

### Two kinds of gate

| Gate | When | Options | What it shows |
|------|------|---------|---------------|
| **Per-chunk gate** | implement stage only — after each `### Chunk N:` dispatch returns | `proceed │ fix │ stop` | `RETURN.status`, `SCOPE:`, `CHUNK_VERDICT:`, files changed, `Redo: N of 3`; after `proceed`, the `COMMIT:` closing line |
| **Stage gate** | after every stage's review (implement: once, after all chunks) | `proceed │ loop-back-to-fix │ stop` | review `VERDICT:`, plus `iteration N of 3` or the replan re-entry count when a loop is active; verify stage with red on: `RED_VERDICT:` and its `Rn` lines (position per `references/loop-control.md` §5); after `proceed`, the `COMMIT:` closing line |

Signals appear in the order they are produced, which is stated **once** in the
repo — `references/loop-control.md` §5 "Gate signal order (REQ-ORCH-034)".
Read it there; this section deliberately carries no second ordering of its own,
so it cannot silently drift out of step with §5. In prose: the leaf's own
signals come first, then the mechanical scope and verifier checks, then the
review's judgement and the loop counters, with any pause block and the
`TELEMETRY:` line last, each at most once, before the options. Which of those a
given gate renders at all depends on the stage — a non-implement stage has no
per-chunk signals, and the red-team signals appear only at the verify stage with
red on.

### Reading the per-chunk gate block

```
Per-chunk gate — implement dispatch #2 (Chunk 2: Reconciliation)   [fan-out: leaf wt-g1 / branch fanout-g1]
  RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 22, test_runs: 3}  vs  Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs
  SCOPE: CLEAN                                    # full write-scope block above when VIOLATION
  CHUNK_VERDICT: PASS                             # verifier findings (Check 1 / Check 3 / Gates) listed above when FAIL
  Files changed  : src/recon/engine.py M, tests/test_recon.py M, docs/plan.md M
  Redo           : 0 of 3 (per-chunk redo counter)
  Options: proceed (orchestrator commits the chunk) │ fix (re-dispatch Chunk 2 with a repair packet; counts toward the per-chunk redo cap) │ stop
  > proceed
  COMMIT: COMPLETE (3 paths)                      # post-decision closing line; INCOMPLETE pauses: amend │ accept (note) │ stop
```

- **`RETURN.status`** — the leaf's own one-word verdict on its deliverable:
  `COMPLETE`, `PARTIAL` (some tasks done, none blocked), `BLOCKED` (stuck
  detection fired — the checkpoint is in the plan), or `BUDGET_EXHAUSTED`.
  `budget_consumed` is in the same units as the `Budget:` line you approved.
- **`SCOPE: CLEAN`** — every file the leaf wrote is inside its declared
  `Write scope:`. On **`SCOPE: VIOLATION`** the full write-scope block is shown
  above the gate, one line per `OUT` path, and you must resolve each one before
  `proceed` is available: **`revert path`** (the orchestrator runs the listed
  `git checkout --` / `rm` command) or **`accept & widen scope`** (session-only —
  nothing is persisted). Spec-file writes outside scope are `ADVISORY`, not a
  violation.
- **`CHUNK_VERDICT: PASS`** — a fresh, read-only verifier re-ran the chunk-close
  checks (type alignment, test coverage, build/lint/tests) and found nothing.
  On **`CHUNK_VERDICT: FAIL`** its findings are listed above the block and the
  default choice becomes **`fix`**: the orchestrator composes a repair packet
  from the verifier's `failures` and re-dispatches the same chunk. Choosing
  `proceed` on a FAIL is an explicit override, recorded in the gate text only.
- **`Redo: N of 3`** — the per-chunk redo counter (`REDO_MAX`, default 3). It
  counts only your `fix` choices for this chunk; verifier re-dispatches do not
  count. It is independent of the stage's fix-loop counter.
- **Files changed** — the observed delta (sequential: the working tree;
  fan-out: the branch's committed delta). On `proceed` in sequential mode the
  orchestrator commits the chunk; under fan-out the leaf already committed.
- **`COMMIT: COMPLETE (N paths)`** — the closing line after your `proceed`: the
  orchestrator compared what the leaf was observed to write against what its
  own commit landed (a two-sha `git diff --name-only` range). On
  **`COMMIT: INCOMPLETE (k observed, not landed: …)`** the gate pauses —
  **`amend`** stages the missing paths into the orchestrator's own commit,
  **`accept (note)`** records the gap in the gate text, **`stop`** halts — and
  nothing is dispatched next (not even the implement-stage review) until you
  choose. Under fan-out the same line appears pre-decision at the per-leaf gate
  (the leaf's uncommitted writes) and again after each merge. Defined in
  `references/write-scope.md` §7a.

### Reading the stage gate

- **`VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT`** — the review's own-line
  token, parsed by the orchestrator; it never guesses a verdict from prose.
- **`iteration N of 3`** — the fix-loop counter (`FIX_LOOP_MAX`, default 3, per
  stage). Each `loop-back-to-fix` re-dispatches the pipeline with a **repair
  packet** (the review's findings plus the paths they point at, never the
  reviewer's reasoning) and then re-reviews. At the implement stage a fix
  dispatch is followed by the scope check, one verifier per touched chunk and
  that chunk's per-chunk gate **before** the re-review runs.
- **Fix loop exhausted** — after iteration 3 still rejects, no further fix is
  dispatched. The gate shows the **compiled findings log** (each iteration's
  Critical/Material finding lines, verbatim, with `(persisting)` marks) and
  offers only `stop | manual intervention | authorize extra iteration (cap → 4)`.
  A chunk that hits `Redo: 3 of 3` renders the same shape with the verifier's
  findings.
- **Replan re-entry cap** — when a stage triggers a replan, the orchestrator
  counts the `-replan-` archives in `docs/plan-history/` dated on or after the
  kickoff's `date:` and shows the count against `REPLAN_MAX` (default 3) with
  the counted filenames. At the cap, or when the message reads
  `replan re-entry cap: kickoff date undeterminable — treated as reached`, it
  routes into `sdd-replan` only on your explicit decision.

### Pauses you may see

| Message | Meaning | Options |
|---------|---------|---------|
| `RETURN: MALFORMED (<reason>)` | The leaf's `RETURN:` block is missing, has `status:` out of place or invalid, spans multiple lines, or contradicts itself. Shown with the raw tail of the return. | `re-dispatch │ accept manually │ stop` — never treated as `COMPLETE` |
| `REVIEW: MALFORMED` | The review's `VERDICT:` token is missing, unrecognized, or disagrees with its prose. | `re-dispatch review │ accept prose manually │ stop` |
| `REVIEW: CONTRADICTION (round N vs round N+1, class b\|c[, file-level])` | Inside a fix loop (stage gate, iteration ≥ 2) the later review round raised a Critical/Material on ground the earlier round did not name and the fix did not write (class b), or regressed `APPROVE_WITH_FIXES → REJECT` without new ground (class c). Both rounds' lines and `fix #N wrote:` are shown side by side. | `accept round N+1 (fix) │ accept round N (proceed, note) │ third opinion (re-dispatch review) │ stop` — see §7c |
| `RETURN.status: BUDGET_EXHAUSTED` | The leaf hit a term of its `Budget:` line and stopped cleanly; `budget_consumed` is mandatory. | treat like `fix` with a fresh budget, or `stop` |
| `RETURN.status: BLOCKED` | Stuck detection (3 failed fixes, oscillation, spec contradiction) fired; no verifier runs; the checkpoint is written (sequential) or applied (fan-out). | per-chunk gate with a replan option — default `route to sdd-replan`; not a redo (`references/return-contract.md` §7) |

**Where the checkpoint lives.** On `BLOCKED` or `BUDGET_EXHAUSTED` the leaf's
attempt ledger is condensed into a bounded (≤ 15 line) **circuit-break
checkpoint** under the affected task in `docs/plan.md` — the blocked-task note
`sdd-replan` already reads (`**Blocked** (<date>, <trigger>): checkpoint`, with
`failing:` / `attempt N:` / `open question:` / `unblocks:` lines, no
tracebacks). A sequential leaf writes it itself; under fan-out the orchestrator
applies it after the merge. Nothing else is persisted: no counter file, no loop
log, no review file — the caps are session-scoped or derived from artifacts that
already exist.

## 7c. Cycle signals added in v5 part 2 (harness-p2)

Five more lines can appear in gate text. None changes the one-word decisions;
each is defined once in the reference file named beside it.

### `TELEMETRY:` lines and the KICKOFF choice

Telemetry is **on by default**. After every gate the orchestrator appends one
record — counts, enums, shas and timestamps, never finding text — to
`.sdd/telemetry.jsonl` (gitignored, orchestrator-only, never read by phase
detection). The only place to turn it off is KICKOFF: say `telemetry: off`
when the kickoff is written and the first gate shows `TELEMETRY: OFF` once;
the choice is session state (not written to `kickoff.md`) and holds for the
cycle. Nothing in the loop reads the file (`.sdd/` is gitignored,
orchestrator-only, never read by phase detection — `rm -rf .sdd/` is
behaviour-neutral) and no leaf may write it: a leaf append renders `OUT
.sdd/telemetry.jsonl (+k records, leaf write — reverted)` — gitignored,
orchestrator-only, never read by phase detection — in the write-scope block
and is reverted before the gate. Lines you may see, at most once each, after the
`iteration`/cap line and before the options:

| Line | Meaning |
|------|---------|
| `TELEMETRY: rec <n>` | the previous dispatch's append **succeeded**; `<n>` counts successful appends this session (not the dispatch number), so a gate with telemetry on but no append shows no `rec` line |
| `TELEMETRY: WRITE FAILED` | the previous append raised an error; the gate continues unchanged — never a pause |
| `TELEMETRY: OFF` | first gate of a cycle you opted out of |
| `TELEMETRY: .gitignore updated` | the orchestrator added the `.sdd/` ignore line (gitignored, orchestrator-only, never read by phase detection; a bookkeeping commit outside any observed window) |

**After the cycle** run `python3 tools/sdd-telemetry.py summarize [--workstream
<id>]` yourself — one table per workstream, one row per stage, then a per-chunk
block (RS-008 probe 1 as a query). It is an out-of-loop reader: no skill runs
it. Schema and writer rules: `references/telemetry.md`.

### Red team at the verify gate (opt-in)

Before the verify pipeline is dispatched the orchestrator asks `red team: off |
on` (default `off`; optionally `red input: +verification.md` to hand red the
blue report — withheld by default so red is not anchored on what blue checked).
With `on`, the verify pipeline carries `Red team: enabled` — `sdd-verify` then
writes `status: pending-red`, never `pass` — and ONE read-only RED TEAM leaf
follows each `COMPLETE` blue return, before the review. It picks the weakest
acceptance criteria and tries to break them; a break counts only with a
reproducible `reproduce:` command. Its last line is `RED_VERDICT: BROKEN |
HELD`, rendered at the stage gate between `SCOPE:` and `VERDICT:`:

```
  RED_VERDICT: BROKEN
    - R1: <criterion> — attack: … — observed: … — reproduce: `python -m app --window 0` — BROKEN
    - R2: <criterion> — attack: … — observed: held — reproduce: `pytest -q tests/test_recon.py::test_window` — HELD
  VERDICT: APPROVE
  iteration 0 of 3
  Options per BROKEN finding: R1 → fix (RED_BREAK packet) | accept (record) | stop
  proceed: unavailable until every BROKEN Rn is fixed or accepted
```

- **`fix (RED_BREAK packet)`** — an implement-stage repair packet built from the
  `Rn` line, routed to the chunk whose spec red was attacking; one red round is
  at most one fix iteration of the verify stage's counter (shared with review
  rounds). After the fix the verify pipeline is re-dispatched and red re-runs
  once by default.
- **`accept (record)`** — appends `- Rn accepted at gate <date>: <observed> —
  reproduce: \`<cmd>\`` under `verification.md` §Issues Found → Minor. Nothing
  else is persisted.
- **`proceed`** becomes available when `VERDICT ≠ REJECT` and red either
  `HELD` or every `BROKEN` line is fixed/accepted; on `proceed` the
  orchestrator flips `pending-red → pass` immediately before its commit. A
  blue `status: fail` or non-`COMPLETE` return shows `Red team: not run` and no
  red is dispatched.
- **`pending-red` on resume** — a `verification.md` left at `pending-red` puts
  phase detection at the verify stage, before the red dispatch (never DONE).

Templates and counting: `references/dispatch-templates.md` §RED TEAM,
`references/loop-control.md` §2a "Red round".

### `REVIEW: CONTRADICTION` — when two review rounds disagree

Only inside a fix loop, at a stage gate (iteration ≥ 2). The orchestrator keys
each round's Critical/Material lines by `(file, section)` and compares round
N+1 with round N plus what fix #N actually wrote (section-resolved hunks). Two
classes fire: **class b** — a new C/M on ground round N never named and the fix
never touched; **class c** — `APPROVE_WITH_FIXES → REJECT` with no new ground.
A `(file-level)` tag means a key could not be resolved to a section and the
comparison may over-fire. The pause shows both rounds verbatim with `fix #N
wrote:` between them, consumes no iteration, and offers:

| Option | What it does | Counter |
|--------|--------------|---------|
| `accept round N+1 (fix)` | treat the later round as right — normal fix re-dispatch | +1 |
| `accept round N (proceed, note)` | treat the earlier round as right and proceed; "note" means the round-N+1 line is carried into the gate text only — nothing is written to any artifact and no review is stored | 0 |
| `third opinion (re-dispatch review)` | one more independent review; two-of-three decides (at most one per contradiction) | 0 |
| `stop` | end the session | 0 |

Reversals (a later round asking the opposite of an earlier one) are **not**
detected — that is a semantic judgement the orchestrator never makes; the fix
loop cap remains the backstop. Rule and fixture:
`references/loop-control.md` §2a, §6.

### `GC:` — the drift sweep at entry and at DONE

`tools/sdd-gc.py` is a sweep, not a stage. It runs at exactly two moments:

- **Entry** (before the workstream picker / phase detection): one line —
  `GC: clean`, or `GC: F fail, W warn — run tools/sdd-gc.py --report`, or `GC:
  unavailable (<reason>)` — then the picker opens regardless. Informational;
  never a gate.
- **DONE** (after verify passes review and you approve): the tool's findings
  are shown verbatim with the summary line, and each finding class is routed
  once: **mechanical** (`xlink-dead`, `index-requirements`,
  `traceability-aggregate`, `plan-history-name`) → `python3 tools/sdd-gc.py
  --fix <rule>` — you review the printed paths and commit; **needs a
  decision** (`stale-chain`, `qimpl-broken-ref`, `trace-empty`, …) → `record |
  ignore`, where `record` appends `- gc <rule>: <file:line> — <fix>` under that
  cycle's `verification.md` `## Next Steps` (the one slot `sdd-verify` Step 6
  defines) and `ignore` writes nothing; **out of scope** → note only.

gc never runs between stages, never blocks a gate, is never scheduled, and
never creates or modifies a plan task. It never reads `.sdd/telemetry.jsonl`
(gitignored, orchestrator-only, never read by phase detection). Cadence and
routing: `references/drift-sweep.md`; the tool: `python3 tools/sdd-gc.py --help`.

### `CATCH-UP` in the write-scope block

Sequential and fix dispatches are provisioned **at the workstream branch tip**,
so the prompt names no catch-up commit and the observed window starts there.
When a hand-written prompt, entry kickoff or resumed session still tells the
leaf to "reach commit `<sha>`", the orchestrator takes the window from that
named base and excludes the commits the leaf merely caught up on, rendering
on the "Observed writes" header line:

```
CATCH-UP <HEAD_prov>..<base> (N commits, excluded — base <sha>)
```

Absent when there was nothing to catch up on. Those commits are not `OUT`
paths; the ancestry check still fires (`HISTORY_REWRITE`) if the leaf rewrites
history. Variants: `CATCH-UP base <sha> unresolved — window from <HEAD_prov>`
(named base not reachable — no exclusion) and `CATCH-UP not performed (base
<sha>)` (leaf ignored the instruction — a warning, not a violation). Detail:
`references/write-scope.md` §3.

## 7d. What changed in harness hardening, part 3 (harness-p3)

Nothing here changes the one-word decisions either gate offers; each line is
defined once in the reference named beside it.

- **Write-scope is a content check.** A file that was already dirty when the
  snapshot was taken and that the leaf then re-touched is now observed: paths
  present in both snapshots cancel only when their content hash is unchanged
  too. You will see such a path in the `SCOPE:` block where earlier versions
  stayed silent — `references/write-scope.md` §3.
- **`RETURN:` blocks are pinned.** Every dispatch template carries the leaf's
  return block verbatim, so a `BUDGET_EXHAUSTED` return pauses with its
  `budget_consumed` against the `Budget:` you approved instead of reading as
  partial progress — `references/return-contract.md`.
- **Regeneration is not a contradiction.** When a fix loop regenerates its
  deliverable wholesale, findings the next review round raises inside the
  regenerated file no longer pause as `REVIEW: CONTRADICTION (… class b)`; a
  file the loop left alone still does — `references/loop-control.md` §2a.
- **`TELEMETRY: rec <n>`.** The positive member of the `TELEMETRY:` family:
  `<n>` is the count of successful appends this session, so a gate that says
  telemetry is on now also shows that the append happened. After the cycle,
  `python3 tools/sdd-telemetry.py summarize` reports any records-vs-expected
  gap — `references/telemetry.md` §3.
- **A previous cycle's report no longer counts as this one's.** Before a
  `status: pass` verification or a fully-checked plan is read as "this stage is
  done", its frontmatter `research_id:` is compared by exact string equality
  with the kickoff's; a mismatch, or a missing field, reads as a previous
  cycle's artifact and the stage runs. With no kickoff or no `research_id:` the
  comparison is skipped and the old `status:`-only rule applies —
  `docs/spec/cycle-identity.md`.
- **`RED:` lines on a second red round.** From red round 2 on, the orchestrator
  re-runs each previous `BROKEN` `Rn`'s `reproduce:` command and renders one
  derived line — `RED: Rn new-ground` (the old command now passes: a second bug
  behind the first, not a failed fix) or `RED: Rn regression` (it still fails)
  — inside the `RED_VERDICT:` block, after red's own `Rn` lines and before the
  exit rule. Meanwhile the traceability `Verified` column reads `pending-red`,
  flipping to `pass` in the same DONE bookkeeping step that regenerates the
  aggregate — `references/loop-control.md` §2a.

---

---

## 8. Sequential default and fan-out

### Sequential by default; implement-stage fan-out is opt-in
Every stage runs **single-threaded in the main workspace by default**. The
**implement stage** is the one exception: you can **opt into fan-out** at the
implement gate to run independent chunk-groups in parallel.

When you opt in, the orchestrator:
- derives the independent chunk-groups from the plan's chunk dependency graph
  (the `**Depends on**: Chunk N` field, or its `Entry criteria: Chunk N complete`
  prose equivalent — not milestone-level Entry/Exit),
- provisions one git worktree/branch per group and dispatches one **leaf**
  implement subagent per group (each runs `sdd-implement` and cannot fan out
  further),
- on each leaf's return, runs the write-scope check on its worktree and
  dispatches the **chunk verifier** against that branch (one verifier per chunk
  the leaf owns), then shows you the per-leaf gate (§7b) **before** any merge —
  a `CHUNK_VERDICT: FAIL` never reaches the integration branch; `fix` redoes the
  leaf on the same branch, `proceed` makes it eligible for the merge,
- then merges the `proceed`-ed branches **sequentially** back into the
  integration anchor — `main` under marker `3`, the **workstream branch** under
  marker `4` (`main` stays untouched until the workstream PR) — completing all
  merges **before** the single implement-stage review runs on the merged state,
  tearing down each worktree as it merges.

The verifier is on by default. You can **opt out** at the same implement gate
where you opt into fan-out; the per-leaf gate then shows the constant-shape line
`CHUNK_VERDICT: (verifier disabled)` and relies on the leaf's own chunk-close checks plus the
implement-stage review. The per-chunk sequence in §7b (scope check → verifier →
per-chunk gate) is what runs per leaf; the only difference is that the
orchestrator does not commit — the leaf already committed on its branch.

Dispatched as a single batch, the per-group subagents run concurrently (measured in
the RS-006 spike), so fan-out delivers a genuine wall-clock speedup on top of
worktree isolation.

**Single-chain degrade-to-sequential.** If the plan's chunk graph is a single
chain (or has no parseable chunk-level dependencies), there is nothing to
parallelize. The orchestrator tells you this **at the gate** and runs the implement
stage sequentially even if you opted in — an expected outcome, not a failure.

On a merge conflict, the orchestrator runs `git merge --abort` and **redoes** the
offending group by re-running `sdd-implement` in a worktree re-branched from the
updated integration anchor (`main`, or the workstream branch under marker `4`;
best-effort auto-resolve may be tried first). If a group conflicts
*again*, that proves the groups weren't truly independent, and the orchestrator
falls back to running them sequentially — so the run always terminates and
already-merged work is never corrupted.

### Starting mid-pipeline (non-research entry)

Research is the **default** entry, but you don't have to start there. When approved
upstream artifacts already exist, you can start the loop at **requirements, specs,
plan, or implement** — e.g. you already have approved requirements and want the
gated loop for specs onward. (Verify is not an entry point — to just verify an
existing project, run `sdd-verify` directly.)

How it works: the driver **auto-detects** the furthest-complete approved artifact,
**proposes** the entry stage, and **confirms** with you (you can override to an
earlier stage); it **validates** the upstream is actually approved and otherwise
routes you to the earliest incomplete stage. KICKOFF then writes an **entry
kickoff** (scope + entry stage + assumed-approved upstream) instead of a research
kickoff. This is different from *resume* (§3): resume continues a cycle this driver
started; non-research entry begins a loop over artifacts you produced elsewhere.

### By design (not limitations)
- **Reviews are ephemeral** — verdicts are shown inline and never written to disk;
  there is no `docs/reviews/`. Decisions live in the artifacts (commits, spec
  edits, Q-IMPL entries, replan triggers). Permanent by design.

All originally-deferred features — parallel implement-stage fan-out and
non-research entry — are now built.

---

## 9. See also

- [`SKILL.md`](SKILL.md) — the driver's operational instructions
- [`references/dispatch-templates.md`](references/dispatch-templates.md) — the
  copy-ready pipeline and review dispatch prompts
- [`references/fan-out.md`](references/fan-out.md) — the implement-stage fan-out
  procedure (boundary derivation, per-group dispatch, sequential merge, teardown,
  conflict redo-by-re-derivation)
- [`references/loop-control.md`](references/loop-control.md) — caps, per-chunk
  loop, gate signal order and the pauses listed in §7b
- [`references/return-contract.md`](references/return-contract.md) — the leaf
  `RETURN:` block, repair packet and `VERDICT:` parsing
- [`references/write-scope.md`](references/write-scope.md) — declared write
  scope, the three-command check, `CATCH-UP` and `SCOPE:` findings
- [`references/telemetry.md`](references/telemetry.md) — the per-dispatch
  record schema, `TELEMETRY:` lines and the post-cycle reader
  (`.sdd/telemetry.jsonl` — gitignored, orchestrator-only, never read by phase
  detection)
- [`references/drift-sweep.md`](references/drift-sweep.md) — when
  `tools/sdd-gc.py` runs, how `GC:` renders and where each finding goes
- `tools/sdd-telemetry.py`, `tools/sdd-gc.py`, `tools/sdd-eval.py` — the
  out-of-loop readers and the sweep (`--help`, `--self-test` on each)
- `docs/spec/orchestration.md` — the design spec
- `docs/research/RS-005-sdd-orchestrate-feasibility/findings.md` — the feasibility
  evidence behind the isolation and non-interactivity guarantees
