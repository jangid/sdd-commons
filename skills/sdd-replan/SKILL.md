---
name: sdd-replan
description: >
  Structured replanning when assumptions break during implementation. Triggered
  by stuck detection, spike findings that invalidate the plan, verification
  failures, or user-requested scope changes. Reads current state, identifies
  what changed, and produces a revised plan. Use when the current plan is no
  longer valid. Skip for routine progress — invoke only when a replan trigger
  actually fires.
---

# SDD: Replan

You are adjusting an existing implementation plan because something changed. The current plan is no longer valid — your job is to understand why, decide what to adjust, and produce a revised plan.

## Phase Detection

Before starting, check what triggered the replan:

**Workstream & version gate (v4).** This skill accepts an optional `workstream`
argument that defaults to `default`. Read `docs/.sdd-version` first — it is the
**sole** layout gate:

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Ignore the workstream
  argument and run exactly the numbered detection below against flat
  `docs/plan.md` / `docs/verification.md`; never read or write `docs/ws/`. The v3
  path is unaffected.
- **Marker is `4` (workstream-aware layout).** Resolve `ws` = the workstream
  argument (default `default`), set `base = docs/ws/<ws>/`, and run the same
  detection below but root every **execution artifact** (`plan.md`,
  `verification.md`, `kickoff.md`, `plan-history/`) at `base` — never at flat
  `docs/`. The **shared corpus** stays at its top-level paths and is used as-is:
  `docs/research/`, `docs/requirements/` (index, category files, aggregated
  `traceability.md`), `docs/spec/`. A replan re-plans and routes only the active
  workstream `<ws>` — never another workstream's plan/verification.

Ownership, sharing, solo-`default`, and approval semantics under marker `4`
follow the common v4 contract — see `docs/spec/ws-layout.md`. In short: a
workstream owns only its `docs/ws/<ws>/` execution artifacts and per-ws
`traceability.md`; requirements/specs/research and the aggregated traceability
are shared (ADD, never fork); omitting the argument resolves `default`.

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

See `docs/spec/cycle-identity.md`.

0. **Version check**: If `docs/.sdd-version` is missing, suggest running `sdd-migrate` before proceeding
1. If `docs/verification.md` exists with `status: fail` → replan from verification failures
   - A `verification.md` with `status: pending-red` is **not** a verification failure — blue passed and the red-team verdict is pending (`docs/spec/adversarial-verify.md` §`status: pending-red`). Do not replan from it: route to `sdd-verify` (re-enter the verify stage)
2. If a spike task produced findings that contradict the plan → replan from new knowledge
3. If the user explicitly requested changes → replan from scope change
4. If implementation is stuck (documented in conversation) → replan from blocked state
5. **Staleness check**: if upstream artifacts are newer than the plan, the plan is stale → replan to align:
   - **Single-milestone plan**: compare `docs/requirements/index.md` and specs against `docs/plan.md`'s `last_updated` frontmatter (mtime fallback for legacy plans)
   - **Multi-milestone plan**: apply milestone-scoped staleness — compare only against requirements and specs traced by the affected milestone's tasks
   - **Workstream-scoped (marker `4` only)**: `docs/.sdd-version` is the sole gate. Under marker `3` (or earlier) compute staleness exactly as the single-/multi-milestone bullets above — flat `docs/plan.md`, milestone key — **unchanged**. `sdd-replan` references milestone-scoped staleness **by name only**, so under marker `4` re-pointing that reference at the workstream-scoped definition suffices — **no new traversal**: the same chain runs with the plan path `docs/plan.md` → `docs/ws/<ws>/plan.md` and the **milestone key → workstream key**. Compare the affected workstream `<ws>`'s plan `last_updated` only against the specs its tasks trace and the requirement category files those specs `requires:` (task → spec `requires:` → requirement IDs → category-file dates), computed **live** from `<ws>`'s plan — **no traceability-file read**, no new traceability schema column (REQ-WS-026). See `docs/spec/ws-staleness.md`

Tell the user what triggered the replan and confirm before proceeding.

## Your Role

- Understand what changed and why the current plan is invalid
- Assess impact: is this a minor task reordering or a fundamental redesign?
- Produce a revised plan that accounts for the new information
- Route to the appropriate phase if the issue is deeper than task ordering

## Process

### Step 1: Assess the Situation

Read the current state:

1. `docs/plan.md` — which tasks are done, in-progress, blocked?
2. `docs/verification.md` (if exists) — what failed?
3. `docs/research/RS-*/findings.md` — any new findings that changed assumptions?
4. `docs/spec/*.md` — are specs still valid given new information?
5. `docs/requirements/{category}/*.md` — current requirements for context
6. The **checkpoint** — the blocked-task note under the stuck task in
   `docs/plan.md` (`**Blocked** (<date>, <trigger>): checkpoint`, followed by
   `failing:` / `last hypothesis:` / `attempt N:` / `open question:` /
   `unblocks:` lines, ≤ ~15 lines; written by `sdd-implement` Step 3, or
   applied by the orchestrator under fan-out). Read it as the stuck state **in
   place of** recent conversation context, which does not exist across a
   dispatch boundary. Tracebacks are never stored there — regenerate them by
   re-running the named `failing:` tests. Under marker `4` the plan is
   `docs/ws/<id>/plan.md`. A note carrying a `task not found in plan` prefix
   (applied under the nearest chunk header) means the leaf drifted — classify
   the named work as unplanned; never treat it as a plan task.

### Step 2: Classify the Issue

Determine the depth of the problem:

**Level 1: Task adjustment** — plan ordering or task breakdown is wrong, but specs are fine
- Example: "Task 5 depends on something from Task 8, need to reorder"
- Action: revise `docs/plan.md`

**Level 2: Spec gap** — the design doesn't cover something we discovered during implementation
- Example: "The spec assumes the API returns JSON but it returns XML"
- Action: update the affected spec, then revise the plan

**Level 3: Requirements change** — what we're building needs to change
- Example: "Verification showed the approach won't meet performance requirements"
- Action: update requirements, then cascade through specs and plan

**Level 4: Pivot needed** — fundamental assumptions are wrong, need research
- Example: "The library we planned to use doesn't support our use case at all"
- Action: invoke `sdd-research` for a spike, then cascade

### Step 3: Route Based on Level

- **Level 1** → revise plan directly (Step 4 below)
- **Level 2** → tell user "this needs a spec update" and either:
  - Make the spec change inline (if small and obvious)
  - Recommend invoking `sdd-specs` for the affected spec
  - Then revise the plan
- **Level 3** → recommend invoking `sdd-requirements` to capture the change, then cascade
- **Level 4** → recommend invoking `sdd-research` for the unknown, then cascade

### Step 4: Revise the Plan (Level 1 and 2)

First, determine if this is a **significant** or **minor** replan:

- **Significant** = adds/removes milestones or changes the overall approach
- **Minor** = task reordering within a chunk, small task edits

**For significant replans**: archive the current plan before modifying it:

1. Create `docs/plan-history/` directory if it doesn't exist
2. Copy `docs/plan.md` to `docs/plan-history/{date}-replan-{reason}.md`
3. Write the changelog and removed tasks to the **archive file**, not the active plan

**Strike resolved `## Open Questions` entries in the archived copy
(REQ-PLAN-HARNESSP6-001).** Before the archive is written, review its
`## Open Questions` section: an entry is **answered** when the spec, tool or
plan text it asks about now states the answer. Every answered entry is
**struck** — left visible, and marked with a bracketed dated resolution marker
on a line of its own directly abutting the entry — immediately after its
heading line, or after its last line when the entry wraps — naming the date and what
resolved it:

```markdown
### 3. Does the reader still read the old default?
**[Struck 2026-09-20 — resolved: the value reads 67 in all three places that
carry it; REQ-PLAN-HARNESSP6-001]**
```

Never delete the entry and never reword it in place: deleting erases the record
that the question was ever open, rewording leaves no evidence it was resolved
rather than silently dropped. An entry you cannot resolve from the artifacts in
front of you stays **unmarked** and is carried into the archive as-is — this
rule strikes settled entries, it does not force a verdict. It applies to the
archived copy under `plan-history/` only (marker `4`:
`docs/ws/<ws>/plan-history/`); active-plan behaviour, files, sections and
marker types are unchanged. See `docs/spec/plan-management.md` §Resolved
`## Open Questions` Entries Are Struck at Archival.

**`-replan-` filename contract (REQ-HARN-003).** Every archive this skill
writes carries the `-replan-` segment (`{date}-replan-{reason}.md`; per
milestone `{date}-m{N}-replan-{reason}.md`); no other skill may use that
segment. `sdd-orchestrate` derives the replan re-entry count (`REPLAN_MAX`,
default 3) by counting archives matching
`^(\d{4}-\d{2}-\d{2})-(m\d+-)?replan-.*\.md$` dated ≥ the kickoff `date:`;
`sdd-plan`'s rewrite archives (`{date}-{reason}.md`) and milestone-complete
archives (`{date}-m{N}-complete.md`) must never contain the segment.

**For minor replans**: edit `docs/plan.md` in place. No archive needed. A minor
replan leaves no archive and is deliberately not counted against the cap.

When revising `docs/plan.md`:

1. **Preserve done tasks** — never undo completed work unless explicitly reverting
2. **Mark blocked tasks** — note why they're blocked and what unblocks them.
   This blocked-task note is the **checkpoint slot**: `sdd-implement` Step 3
   writes the circuit-break checkpoint here (`**Blocked** (<date>, <trigger>):
   checkpoint` + `failing:` / `last hypothesis:` / `attempt N:` /
   `open question:` / `unblocks:` lines, ≤ ~15 lines, no traceback frames) and
   Step 1 item 6 reads it back. Keep an existing checkpoint intact when
   revising; when the replan resolves the blocker, update its `unblocks:` line
   (or drop the note once the task is unblocked). No new section, no new file
3. **Add new tasks** if the replan introduces new work
4. **Remove invalidated tasks** — move them to the archive file (for significant replans). Do NOT write `[removed: reason]` in the active plan
5. **Reorder** remaining tasks based on new dependencies
6. **Update replan triggers** — the old ones may no longer apply
7. **Carry `## Post-cycle Fixes` across verbatim** — the optional,
   orchestrator-owned section at the end of the plan (REQ-REDB-HARNESSP3-004,
   `docs/spec/adversarial-verify.md` §`## Post-cycle Fixes` in the Active Plan;
   contract in `docs/spec/milestone-plans.md` §Milestone Plan File Format). Its
   lines are **not tasks**: never strip it on a rewrite, never archive-and-drop
   it, never convert its lines into tasks or mark them done. `sdd-plan` does not
   create it and `sdd-implement` does not read it as tasks

**Archive file format** (for significant replans — written to `docs/plan-history/{date}-replan-{reason}.md`):

```markdown
# Plan Archive: Replan — [reason]

## Changelog
- **Date**: YYYY-MM-DD
- **Trigger**: [what caused the replan]
- **Impact**: [what changed]
- **Added**: [new tasks]
- **Removed**: [invalidated tasks and why]
- **Reordered**: [what moved and why]

## Previous Plan Snapshot
[Full content of plan.md at time of archive]
```

#### Per-Milestone Replans

When the project uses per-milestone plan files (`docs/plan-{id}.md`):

**Single-milestone replan** (most common):
1. Identify which milestone's plan file is affected by the replan trigger
2. Archive only that milestone's plan file to `docs/plan-history/{date}-m{N}-replan-{reason}.md`
3. Revise the affected milestone plan
4. Update `docs/plan.md` index table if milestone status changes

**Cross-milestone replan** (tasks moving between milestones):
1. Archive both affected milestone plans before changes
2. Update both milestone plan files with the task movement
3. Update the index table to reflect current status

Single-file plans continue to use the existing archival pattern above. Per-milestone logic activates only when per-milestone files exist. Under marker `4` the same logic runs within the workstream: index and milestone files at `docs/ws/<ws>/plan.md` / `docs/ws/<ws>/plan-{id}.md`, archives to `docs/ws/<ws>/plan-history/`.

### Step 5: Present and Confirm

Present the revised plan to the user:

1. Summarize what triggered the replan
2. Show what changed (added/removed/reordered tasks)
3. Highlight any cascading impacts (spec changes, new risks)
4. Ask for approval before resuming implementation

### Step 6: Transition

After the revised plan is approved:
- If implementation should resume → recommend `sdd-implement`
- If a spec needs updating first → recommend `sdd-specs`
- If research is needed → recommend `sdd-research`
- If re-verification is needed → recommend `sdd-verify`

## Rules

- **Don't panic**: a replan is normal, not a failure. The goal is to adjust efficiently, not to blame or justify
- **Minimize disruption**: change only what's necessary. If 3 tasks out of 20 need adjustment, don't rewrite the whole plan
- **Preserve history**: never silently delete tasks or change what's already done. Use the archive file for significant changes
- **Cascade awareness**: a spec change may invalidate multiple tasks. Check downstream effects
- **User decides scope**: if the replan could go multiple directions (cut scope vs extend timeline vs change approach), present options and let the user choose
- **Don't implement during replan**: produce the revised plan, not code. Implementation happens in `sdd-implement`
