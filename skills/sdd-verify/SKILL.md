---
name: sdd-verify
description: >
  Holistic validation after implementation — goes beyond "tests pass" to verify
  quality gates, acceptance criteria, user-perspective behavior, and regressions.
  Produces docs/verification.md. Use after all plan tasks are complete. Skip while
  tasks remain incomplete; not a substitute for per-task testing. Triggers
  sdd-replan if critical failures are found.
---

# SDD: Verification

You are performing holistic verification of a completed implementation. Your job is to confirm that the system works correctly from every angle — not just that tests pass.

## Verification Layers

`sdd-verify` is one of four verification layers in the SDD workflow. The others are: chunk-close (mechanical, in-session, per-chunk), XSPEC (structural, in-session, during sdd-specs), and sdd-review (semantic, out-of-session, at phase boundaries). sdd-verify is the holistic in-session pass at end of project. If you find this skill's scope crossing into another layer's territory, refer to that layer's skill or spec.

**Red team (adversarial second executor — `docs/spec/adversarial-verify.md`).** At the verify stage `sdd-orchestrate` may dispatch, opt-in and default off, a read-only RED TEAM leaf that re-executes **this layer's Steps 3–4** adversarially — picking the weakest acceptance criteria and constructing inputs that violate them. It is a second *executor* of this layer, exactly as the chunk verifier is of chunk-close: not a fifth layer, not `sdd-review`, and the four-layer list above is unchanged. Standalone `sdd-verify` is unaffected except for the `pending-red` rule in Step 6.

## Phase Detection

Before starting, check project state. **Compare dates** to detect stale artifacts:

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
  `traceability.md`), `docs/spec/`.

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
1. If no `docs/plan.md` → use `sdd-plan`
2. **Staleness check**: compare `last_updated` in `docs/requirements/index.md` and specs against `docs/plan.md`'s `last_updated` frontmatter (legacy plans without frontmatter: file modification date as fallback). If upstream artifacts are newer than the plan, the plan is stale → use `sdd-plan` to update before verifying
   - **Workstream-scoped (marker `4` only)**: `docs/.sdd-version` is the sole gate. Under marker `3` (or earlier) run the whole-plan compare above — flat `docs/plan.md` vs all specs/requirements — **unchanged**. Under marker `4` `sdd-verify` gains a **new** workstream-scoped branch (it had no scoped branch before): compare the active workstream's `docs/ws/<ws>/plan.md` / `docs/ws/<ws>/verification.md` **only** against the shared specs/requirements that workstream traces, using the **same live plan-walk** as `sdd-plan`/`sdd-implement` (walk `<ws>`'s tasks' `traces to` specs → each spec's `requires:` requirement IDs → those specs' and requirement category files' `last_updated`; task → spec `requires:` → requirement IDs → category-file dates). It must **not** report staleness from shared-input changes outside `<ws>`'s traced set. This reads **no traceability file** and adds no traceability schema column — the scope is derived live (REQ-WS-027). See `docs/spec/ws-staleness.md`
3. If `docs/plan.md` has incomplete tasks → use `sdd-implement`
4. If all plan tasks are done (or user explicitly requests verification) → you're in the right place
5. If `docs/verification.md` already exists → you're re-verifying (after fixes or replan). A report with `status: pending-red` is this same re-verification state — verification incomplete, red-team verdict pending — and is **never** DONE and **never** a replan trigger (`docs/spec/adversarial-verify.md` §`status: pending-red`)

Tell the user which phase you detected and confirm before proceeding.

## Your Role

- Run all quality gates and report results
- Walk through every acceptance criterion in every spec
- Verify user-perspective behavior (not just unit test pass/fail)
- Check for regressions
- Produce a structured verification report
- Trigger replan if critical failures are found

## Process

### Step 1: Load Context

1. Read `docs/plan.md` — confirm all tasks marked done
2. Read all `docs/spec/*.md` — collect every acceptance criterion
3. Read `CLAUDE.md` — identify the project's quality gates
4. Read `docs/requirements/index.md` and `docs/requirements/{category}/*.md` — understand the original intent
5. Read `docs/requirements/traceability.md` — understand current coverage state

### Step 2: Quality Gates

Run all automated quality checks. Report each as pass/fail:

**Language-specific gates** (paths below are examples — substitute the project's actual source layout, e.g. `ruff check .` or the package directory):

Python:
- `ruff check src/` — zero violations
- `ruff format --check src/` — zero reformats needed
- `mypy src/ --strict` — zero errors
- `pytest` — all pass, note duration

Rust:
- `cargo fmt --check` — clean
- `cargo clippy -- -D warnings` — zero warnings
- `cargo test` — all pass

TypeScript:
- `eslint .` — zero violations
- `prettier --check .` — formatted
- `tsc --noEmit` — zero errors
- `npm test` — all pass

Sui Move:
- `sui move build` — zero warnings
- `sui move test` — all pass

Also check:
- Build succeeds (`uv build`, `cargo build --release`, `npm run build`)
- Package is installable/publishable (if applicable)

### Step 3: Acceptance Criteria Walkthrough

For each spec in `docs/spec/`:

1. Read its acceptance criteria section
2. For each criterion:
   - Determine how to verify it (test exists? manual check needed?)
   - Execute the verification
   - Record: pass, fail, or unable-to-verify
3. If a criterion fails: note what's wrong and severity (critical/minor)

### Step 3b: Traceability Verification

Read `docs/requirements/traceability.md` and verify:

1. **Every requirement has a spec** — Spec column is non-empty for all rows
2. **Every implemented requirement has tests** — Test column is non-empty for requirements with Implementation filled
3. **Flag gaps** — list any requirements missing spec, test, or implementation coverage

After verification, update the **Verified** column for each requirement with one
of its **four** legal values — `pass`, `fail`, `pending-red` or `descoped` (the
block below says which applies). `descoped` is **never** written by this skill:
it is the orchestrator's bookkeeping value for a row **carried from a previous
workstream** that the carrying cycle's DONE rule could not close, it is never a
substitute for `fail`, and it is never read as completion
(`docs/spec/ws-traceability.md` §Legal `Verified` Cell Values,
REQ-WS-HARNESSP5-001).

**`pending-red` cells (REQ-REDB-HARNESSP3-003).** The `Verified` column tracks
the **report's** status, so whenever Step 6 writes `status: pending-red` write
`pending-red` — not `pass` — into the `Verified` cell of **every row you would
otherwise have marked `pass`**; a `fail` row stays `fail`. `pending-red`,
`pass`, `fail` and `descoped` are the four legal cell values
(`docs/spec/ws-traceability.md` §Legal `Verified` Cell Values) — of which this
skill writes the first three. The
orchestrator's existing `pending-red → pass` flip at DONE turns exactly those
cells back to `pass` and regenerates the aggregate in the same bookkeeping step
— this skill never performs that flip.

**gc criterion for these cells (REQ-REDB-HARNESSP4-001).** The check is that
`python3 tools/sdd-gc.py --report` raises no new finding **on a `pending-red`
cell**. The one `[traceability-aggregate]` warning that appears between this
per-workstream write and the orchestrator's post-gate regeneration of the
aggregate (`docs/spec/ws-traceability.md` §Aggregate Regeneration Ownership,
REQ-WS-HARNESSP3-001) is the **designed handshake** — expected, and not a
finding against any cell (`docs/spec/adversarial-verify.md` §`Verified` Reads
`pending-red` While a Red Round Is Outstanding).

**Per-workstream traceability (marker `4` only).** `docs/.sdd-version` is the sole gate.
Under marker `3` or earlier, read and write the single shared
`docs/requirements/traceability.md` directly, as above (unchanged). Under marker `4`,
the aggregate `docs/requirements/traceability.md` remains a convenient read-only
**coverage view** for the checks above, but write the **Verified** column into the
active workstream's OWN file `docs/ws/<ws>/traceability.md` (per-workstream-owned rows,
6-column matrix with the `Workstream` column as the 3rd column) — never another ws's file and
never the shared aggregate in place — then **regenerate** the shared aggregate wholesale
(shipped legacy rows — rows predating the v4 migration, attributed to the blank/default workstream — + concat of every `docs/ws/<id>/traceability.md`, stable-sorted by
requirement id; never hand-merged). See `docs/spec/ws-traceability.md` (REQ-WS-007,
REQ-WS-008).

**Unless the dispatched write scope omits the aggregate (REQ-WS-HARNESSP3-001).**
Regenerate the aggregate after the per-ws write **unless this run was dispatched
with a write scope that omits `docs/requirements/traceability.md`** — under
`sdd-orchestrate` that path is absent from every leaf scope by construction, and
its absence *is* the signal that regeneration is the orchestrator's post-gate
bookkeeping (`sdd-orchestrate/references/write-scope.md` §2, §7). Its presence in
the dispatched scope, or no dispatched write scope at all (a standalone run),
means regenerate here. No flag or field beyond the scope slot is involved.

### Step 4: User-Perspective Validation

Go beyond unit tests. Ask:

- **Does the feature actually work end-to-end?** Start the system, use it as a user would
- **Are error messages helpful?** Trigger common error paths, check the output
- **Is configuration intuitive?** Try setting up from scratch with only the docs
- **Are edge cases handled?** Try unusual inputs, boundary values, empty states

For CLI tools: run them. For servers: start them and make requests. For libraries: write a minimal usage example.

### Step 5: Regression Check

- Run the full test suite (not just new tests)
- If there's a pre-existing test suite, confirm nothing regressed
- Check git diff against the base branch — are there unintended changes?
- **Regression base (version gate — REQ-WS-018)**: `docs/.sdd-version` is the sole gate.
  - **Marker is not `4` (v3 or earlier): UNCHANGED.** Diff against the base branch (`main` HEAD) exactly as the bullets above, and check `git diff` against it for unintended changes. The v3 path is untouched.
  - **Marker is `4`:** the regression base is the **workstream branch point** — `regression_base(<ws>) = merge-base(<ws>, main)`, the commit where the workstream branched. Compute the regression diff as **`<ws>` HEAD vs `regression_base(<ws>)`**, **not** `main` HEAD. Diffing against current `main` would fold in unrelated concurrent workstreams' changes that merged to `main` after `<ws>` branched, producing **false regressions**; the branch point isolates this workstream's own delta regardless of what else landed on `main` meanwhile. So a workstream's verification is **independent of other workstreams merged to `main`** in the interim (e.g. merging an unrelated `ISSUE-57` to `main` does not affect `sdd-verify` for `ISSUE-42`). This is the integration model's branch-per-workstream → PR-to-`main` boundary (REQ-WS-016/017): `main` is a shared trunk that moves under the workstream, so the branch point — not `main` HEAD — is the stable regression anchor. Full contract: `docs/spec/ws-integration.md` §Verification Regression Base Is the Workstream Branch Point.

### Step 6: Write Verification Report

**Workstream scoping (marker `4`)**: under `docs/.sdd-version` == `4`, write the
report to the active workstream's `docs/ws/<ws>/verification.md` (default
`default`) — **never** the flat `docs/verification.md` and never another
workstream's file. Under marker `3` (or earlier) save to `docs/verification.md`
exactly as below, unchanged.

Save to `docs/verification.md` (or `docs/ws/<ws>/verification.md` under marker `4`):

```markdown
---
status: pass | fail
research_id: RS-<WS>-NNN   # copied verbatim from the workstream's kickoff.md; always the line after status:
last_updated: YYYY-MM-DD
plan_ref: docs/plan.md   # marker 4: docs/ws/<ws>/plan.md
---

# Verification Report

## Summary
[One paragraph: overall status — pass or fail with how many issues]

## Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| Lint | pass/fail | details |
| Format | pass/fail | details |
| Type check | pass/fail | details |
| Unit tests | pass/fail | X pass, Y fail, Zs duration |
| Build | pass/fail | details |

## Acceptance Criteria

### [spec-name.md]

| Criterion | Status | Evidence |
|-----------|--------|----------|
| [criterion text] | pass/fail/unable | [how verified] |
| ... | ... | ... |

### [another-spec.md]
...

## User-Perspective Validation

| Scenario | Status | Notes |
|----------|--------|-------|
| [end-to-end usage] | pass/fail | what happened |
| [error handling] | pass/fail | what happened |
| ... | ... | ... |

## Regressions
- [None found / List of regressions]

## Issues Found

### Critical (blocks release)
- [issue description — what's wrong, where]

### Minor (can ship, fix later)
- [issue description]

## Recommendation
- [ ] Ship as-is
- [ ] Fix critical issues then ship (invoke sdd-replan)
- [ ] Significant rework needed (invoke sdd-replan)

## Next Steps
- [follow-up or deferral — one line each; empty section allowed]
```

(`last_updated:` matches every other SDD artifact's staleness field; older reports may carry `date:` instead — treat the two as equivalent when reading.)

**The `research_id:` stamp (REQ-CYCID-HARNESSP3-001).** Emit it on the line
immediately after `status:`, before `last_updated:` (Q-IMPL-HARNESSP3-014;
`docs/spec/cycle-identity.md` §The Stamp), copied **verbatim** from the
active workstream's `kickoff.md` (`docs/ws/<ws>/kickoff.md` under marker `4`,
`docs/handoff/kickoff.md` under marker `3`) — never derived or invented. It is
what lets a later reader tell **this** cycle's `status: pass` report from a
previous cycle's (§Phase Detection). Omit the field when there is no kickoff or
the kickoff carries no `research_id` (case 3). Existing reports are **not**
back-filled, and no file under `docs/requirements/**` or `docs/spec/**` is ever
stamped. See `docs/spec/cycle-identity.md`.

**Carry-or-close for unresolved Minors (REQ-SKILL-HARNESSP3-001).**
`verification.md` is **overwritten** per cycle, so a Minor that is neither
carried nor closed is lost to git history. Before writing the new report, read
the report this write is about to replace — **the previous cycle's report**,
identified via the `research_id` comparison of §Phase Detection — and for every
unresolved entry under its `### Minor (can ship, fix later)` do exactly one of:

- **carry** it into this cycle's §Issues Found → Minor, reproducing its
  **original wording** plus a trailing `(carried from <research_id>)` marker, so
  a reader tells an inherited finding from a fresh one without reading git
  history (Q-IMPL-HARNESSP3-013) — under case 3 the previous report has no
  `research_id` to name, so the marker degrades to `(carried forward)`
  (Q-IMPL-HARNESSP3-019); or
- **close** it, listing it once as `closed: <one-line reason>`; a closed Minor is
  not carried again in the next cycle.

No Minor silently disappears across the overwrite. The rule applies **including
under case 3** (no kickoff, or a kickoff without `research_id`): with no
discriminator the previous report is whatever sits at the report's path on disk,
and **absence of a kickoff must not suppress the rule**.

**Section slots.** `## Next Steps` (after `## Recommendation`) is the **single
definition** of the report's follow-up slot: `- gc <rule>: <file:line> — <fix>`
lines from the drift sweep (`docs/spec/drift-sweep.md`) and deferral lines
(`docs/spec/evaluation.md`) land here and nowhere else. `### Minor (can ship,
fix later)` is additionally the slot for the orchestrator's
`- Rn accepted at gate <YYYY-MM-DD>: <observed> — reproduce: \`<cmd>\`` lines
when a red-team `BROKEN` finding is accepted at the verify gate — appended by
`sdd-orchestrate`, never by this skill.

**`status: pending-red` (REQ-REDB-HARNESSP2-008).** The frontmatter `status:`
you write depends on whether the dispatch prompt carries the literal slot
`Red team: enabled` (`sdd-orchestrate` sets it only when the operator chose
`red team: on`):

| Your own result | Slot absent (standalone, or red off) | Slot `Red team: enabled` present |
|---|---|---|
| pass | `status: pass` | **`status: pending-red`** |
| fail | `status: fail` | `status: fail` |

With the slot absent the output is byte-identical to v5. `pending-red` means
"blue passed, red verdict pending": the **orchestrator** dispatches the red
team, gates, and flips `pending-red → pass` in the frontmatter immediately
before its own commit — this skill **never** writes `pass` while red is
pending and never performs the flip. Writing `pending-red` here also means
writing `pending-red` into every would-be-`pass` `Verified` cell (Step 3b,
REQ-REDB-HARNESSP3-003) — the durable matrix never asserts `pass` while a red
round is outstanding. The gc criterion for those cells is Step 3b's qualified
one — no new finding **on a `pending-red` cell**, with the
`[traceability-aggregate]` handshake warning raised before the orchestrator's
regeneration expected, not a finding. Every reader maps `pending-red` to
"verification incomplete — re-enter the verify stage" (Phase Detection item 5;
`sdd-replan` routes it back here; `sdd-orchestrate` resumes before the red
dispatch).

### Step 7: Decide Next Step

Based on the report:

- **All pass, no issues** → tell the user "verification complete, ready to ship". Note that the active plan can now be archived to `docs/plan-history/` if desired
- **Minor issues only** → ask user: "fix now or ship and track as follow-up?"
- **Critical issues** → recommend `sdd-replan` with the failure context. Under
  marker `4`, route **only** the active workstream `<ws>` into replan — never
  another workstream's plan/verification

## Rules

- **Evidence over assertion**: never write "pass" without running the actual check
- **Run, don't read**: execute commands, don't just read test files and assume they pass
- **User perspective matters**: a passing test suite with a broken UX is a fail
- **Be specific about failures**: "test_foo failed" is useless. Include the error, the expected vs actual, and which spec criterion it maps to
- **Don't fix during verify**: your job is to report, not fix. If you find issues, document them and recommend replan. Fixing during verification muddies the report
