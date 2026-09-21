---
workstream: packaging
description: Packaging follow-up, cycle 2 (narrow) — prove the git-subdir install mechanism for real, then settle the one root/rule-file interface that cycle 1 could not close
cycle: packaging-followup-2
research_id: RS-PACKAGING-002
entry_stage: research
date: 2026-09-21
branch: packaging
supersedes: RS-PACKAGING-001
---

# Kickoff: RS-PACKAGING-002 — Packaging follow-up, cycle 2 (narrow)

Run `/sdd:research` for workstream `packaging`. This is a **narrow** spike. It
does not revisit cycle 1's answers; it proves the one mechanism they rest on and
settles the one interface they contradicted.

## Why there is a cycle 2

Cycle 1 (`RS-PACKAGING-001`, findings at
`docs/research/RS-PACKAGING-001-packaging-followup/findings.md`, commit
`6a84ec5`) answered its three questions and was **rejected at the stage gate
after four review rounds**, with the fix-loop cap exhausted. The operator chose
`stop` over a fourth patch, applying the rule the marketplace cycle recorded:
when round N+1 finds defects in round N's repairs twice running on the same
component, revert and redesign rather than spend another iteration. The
artifact had grown 433 → 1029 lines across three repairs, and what remained was
not a local error but a contradiction between two of its own answers.

**Note for phase detection.** That artifact carries `status: Complete` because
its three questions were answered. It does **not** mean the stage was approved.
Reviews are ephemeral, so nothing on disk distinguishes a stage that passed from
one that stopped — the only durable trace is the message on commit `6a84ec5`.
This kickoff's `research_id` is `RS-PACKAGING-002`, so phase detection keys on
**that** spike's findings and will not read cycle 1's as this cycle's.

## Carried forward as EVIDENCE — do not re-derive

Each item below was independently re-derived by at least two cold reviewers
across cycle 1's four rounds. A finding here is an input to this spike, not a
question for it. Cite `RS-PACKAGING-001` rather than re-running the measurement.

- **No path-exclusion declaration exists.** The install file list is identical
  to `git ls-tree` at the pinned sha; the CLI binary contains zero
  `claudeignore` / `pluginignore` strings; the installer's `github` branch takes
  `(repo, ref, sha)` only, and `declaredComponentPaths` is threaded to the
  `archive` branch alone.
- **The `archive` source is dismissed** — its schema is an HTTPS URL of a zip
  archive, so it cannot source a repository at a ref at all.
- **`git-subdir` is the candidate mechanism** — clone `--depth 1
  --filter=tree:0 --no-checkout`, `sparse-checkout set --cone`, checkout, then
  move `<scratch>/<path>` alone into the install dir. **Read, not executed —
  this is Q1 below.**
- **Costing at `0f5ec26`:** 45 files move (`plugin.json` 1 + `skills/` 27 +
  `agents/` 3 + `tools/` 14), 154 stay, 45 + 154 = 199 = `git ls-files`. The
  driver's ten skill-directory-relative `references/*.md` cost **zero** edits.
- **The linter needs two roots after the move.** `RETIRED_SCOPE_FILES` (six root
  files), `RETIRED_SCOPE_DIRS` (including `docs/spec`, `docs/requirements`) and
  the spec side of `TEMPLATE_PAIRS` all key on paths that stay.
- **Every suite-specific row is flat data; none needs code.** `tools/gc.py`
  carries none of them — it emits 15 rule ids over 26 `self.flag(` sites (13
  `GC_RULES` + `kickoff-fields` + the `lint` passthrough). All suite rows live in
  `tools/skill-lint.py`.
- **`tools/gc.py:1855`** — a `no docs/ directory` bail sits in `main()` *before*
  `Gc(...)` and before `lint_path()`. A third gating condition neither proposed
  change touches.
- **`git archive <sha> | tar -x` is a non-circular fixture** — its file list
  diffs empty against the live GitHub-sourced install.

## Research questions

**Q1 — Does a `git-subdir` entry actually install as modelled?**
Everything above rests on installer internals read from one CLI build
(`2.1.278`), rated Medium confidence and never executed. Cycle 1's own
§Implications made proving this a **blocking, sequenced gate before the 45-file
move**. Build a throwaway repository under `$TMPDIR` containing a plugin in a
subdirectory and a marketplace entry sourcing that subdirectory, then perform
one real install and inspect the materialised tree. Establish: does the install
contain the subdirectory's contents and **nothing from the repository root**;
does a marketplace entry hosted in the **same repository** as the plugin resolve
(cycle 1 flagged this as unconditional in code but unexecuted); and — settling
cycle 1's unmeasured S1 — does a component path written **relative to the plugin
root** resolve in the installed tree, which decides whether `marketplace.json`
costs 1 line or 14.

If `git-subdir` does **not** behave as modelled, say so plainly and stop: the
root move loses its mechanism and Q2 becomes moot. That is a valid and valuable
outcome for this spike.

**Q2 — After the move, which root is the sweep pointed at, and how is the rule
file found from it without a tool-directory fallback?**
This is the contradiction that stopped cycle 1. The rule data was specified at
`<swept root>/tools/skill-lint.rules.json`, resolved from the swept root with no
fallback. After the move neither root works: pointed at the **repository root**
(the default, and what the pre-commit entries do) the rule file is gone, so this
repository's own 40 contract rows **silently turn off** — verbatim the
already-rejected round-2 `R1` failure; pointed at the **plugin root** there is no
`docs/`, so the sweep exits 2 and the corpus sweep stops working entirely.
Dropping the no-fallback rule reinstates the fabrication bug the work exists to
remove, so that is not an available answer.

Two candidate resolutions are on record. Cost both, recommend one, and state
what each does to the numbers above:

- **(A) The rule file stays at `<repo>/tools/skill-lint.rules.json`.** Forces
  `tools/` to split into a shipped subset and a dev-only subset, re-derives the
  45/154 costing, and contradicts cycle 1's fixture placement.
- **(B) The sweep gains an explicit corpus-root / suite-root pair**, unified
  with the two-root concept the move already forces.

Whichever is recommended must come with the **acceptance vector that would catch
the silent-disable failure**: this repository's own post-move sweep, run exactly
as the pre-commit gate runs it, must still report the full 40-row population —
an assertion on the policed count, not on exit 0. A criterion that only checks
for silence cannot distinguish "correctly quiet" from "switched off", and that
distinction is the whole point.

## Success criteria

Q1 closes with a real install performed and its tree inspected — three
answers (subdirectory-only contents, same-repo entry resolution, plugin-root-
relative component paths) each backed by a command and its output, or an
explicit negative that stops the cycle. Q2 closes with one recommended design,
both options costed against the carried numbers, and the policed-count
acceptance vector stated in run-time-decidable form.

## Budget

**25 tool calls**, 0 test runs. Deliberately tight: this spike answers two
questions over a corpus it has already been handed. If a question exhausts its
share, record what was learned and what remains rather than overrunning.

## Authorized for this cycle — install commands

The operator has authorized `claude plugin install` and
`claude plugin marketplace add/remove` **for this spike**, under three
conditions: the test marketplace is registered under a **distinct name** (never
`sdd-commons`), the repository under test lives under `$TMPDIR`, and the test
marketplace is **removed afterwards**. The live `sdd-commons` marketplace entry
and the installed `sdd` plugin are never modified — this session runs from them.

Cycle 1's blanket no-install constraint was this spike's predecessor's, and it
is precisely why Q1 is unproven.

## Out of scope

- Re-deriving anything under §Carried forward.
- The three original questions of cycle 1 as questions — they are answered.
- Rewriting the sweep's generic rules.
- Executing the root move itself. This cycle decides the design; the move is
  implementation work for the plan stage.
- Any new SDD phase, skill or agent.

## Carried repairs — still queued, entering at requirements

Unchanged from cycle 1; known work with known fixes, not research questions.

- **Deferral-backlog screen marker leakage** — the L-1 adjacency check reads the
  preceding bullet's `[closed …]` marker as satisfying the following entry.
  Evidence: `docs/ws/marketplace/verification.md` §Deferral-Backlog Screen.
- **`skills/verify/SKILL.md:169`** — the last cwd-relative drift-sweep
  invocation in a shipped skill body. Sequence after Q2, which decides where a
  non-driver skill's bundled tool copy lives.
- **`docs/spec/orchestration.md:574`** — name the project README by its current
  filename.
- **`tools/skill-lint.py:381` and `:1252`** — drop the deleted front door's
  filename from `RETIRED_SCOPE_FILES` and from the self-test's `policed_files`
  tuple **together** (`Q-IMPL-MARKETPLACE-017`).
- **`CLAUDE.md:251` vs `:215`** — reconcile which marker the repository uses.

## Also live from cycle 1's final review, for the requirements stage

- The restated acceptance target **amends** the kickoff §Success criteria of
  cycle 1 (`exit 0` "in their own repository" — overwhelmingly the no-`docs/`
  shape, which is deliberately kept at exit 2). Requirements must carry the
  amended wording or it will encode an unachievable criterion.
- Whether `plugins/sdd/` carries its own `README`/`LICENSE` (45 vs 47 installed
  files) is recorded, not decided.
