---
workstream: consumer-geometry
status: in-progress
research_id: RS-CONSUMERGEOMETRY-001
last_updated: 2026-09-22
---

# Implementation Plan: Consumer geometry — the disjoint suite root

## Overview

This cycle closes the geometry in which the suite root is **disjoint** from the
corpus root — the only geometry a consumer of the installed plugin ever has, and
the geometry in which `swept_roots()` collapses to the corpus root alone so the
shipped suite is never walked. The defect is not a wrong answer but a *silently
reduced* one: `check_structure()` takes its `if not skills_dirs:` branch, emits
one `[structure]` finding and returns, and every per-skill rule below that return
stops running.

The design is `docs/spec/two-root-linter.md` §Consumer-Geometry Amendment
(§CG-1..CG-11), with per-tool halves in `drift-sweep.md`, `skill-lint-v5.md`,
`marketplace-packaging.md` and `pre-commit.md`. All five are Approved and are
**evidence**: this plan orders their work and does not re-derive, re-measure or
re-argue any of it.

Four things shape the chunk graph, in this order of force:

1. **Write scopes.** §CG-11 (including the block added at the specs cap gate)
   fixes them. Exactly one implement task and exactly one verify task write
   `docs/requirements/integration/packaging.md`; cross-workstream writes are
   authorised **by disposition class only**; no leaf regenerates
   `docs/requirements/traceability.md`; and the shipped
   `plugins/sdd/skills/orchestrate/references/drift-sweep.md` is a plugin file,
   not a docs record.
2. **Four recorded ordering constraints** (§Ordering Constraints below), encoded
   as chunk dependencies rather than prose.
3. **Constraint 2 of the kickoff** — every binding this cycle touches must have
   its reversion **fail a gate, demonstrated by running the mutation, not
   asserted**. Every implement task below carries the mutation that proves its
   binding, and a task whose completion nothing can falsify is not done.
4. **The six plan inputs recorded at the specs cap gate**, each either sized as a
   task here or recorded with the reason it is not (§Recorded Plan Inputs).

## Conventions

- **Task types**: `[implement]` produces code/text, `[spike]` produces findings,
  `[verify]` validates behaviour.
- **Chunk headers**: `### Chunk N: <name>`; `**Depends on**:` is the canonical
  dependency signal for implement-stage fan-out.
- **Task numbers are contiguous integers within each chunk, and every task is an
  ordinary task.** No suffixed forms (`7b`, `1b`) survive: repair iteration 1
  introduced them and iteration 2 renumbered them away, because Chunk 7 task 9
  asserts write-scope exclusivity **by reading this plan's declarations** — the
  plan is mechanically parsed, so its task list must parse the same way a reader
  reads it. A renumbering never changes what a task says; cross-references
  elsewhere in this plan were updated with it.
- **Write scope** is declared per chunk, as `**Write scope**:`. A path touched by
  a chunk that does not declare it is a `SCOPE: VIOLATION`, not a judgement call.
- Every task names the spec section it traces to.
- **The chunk graph is a single linear chain** (Chunk 0 → 9, one `Depends on`
  edge each). This is deliberate rather than an omission: Chunks 1–5 all edit
  `plugins/sdd/tools/skill-lint.py` and/or `plugins/sdd/tools/gc.py` in
  overlapping regions (the constructor, the print sites, `lint_command()`), so a
  fan-out would be a merge hazard with no parallelism to buy. Chunks 6 and 7 are
  the only genuinely independent pair and are still serialised, because both
  write `docs/spec/two-root-linter.md`.
- **The disjoint scratch construction** is §CG-8's, always: a `cp -R` of
  `plugins/sdd` into `$TMPDIR`, disjoint **by construction**. The installed
  plugin cache at `~/.claude/plugins/cache/sdd-commons/` is a read-only
  measurement surface and is never written by any task (kickoff constraint 1).
- **Per-workstream traceability is FILLED, never appended to.** **Every** chunk
  declares `docs/ws/consumer-geometry/traceability.md` (all ten — the count is
  derived from this plan's own `**Write scope**:` blocks, not written down twice;
  Chunk 7 task 9 reads those blocks mechanically, so a hand-maintained count here
  would be a live hazard, not an editorial one). **Every chunk's Exit criteria
  carry this obligation explicitly** — a convention with no task behind it is
  unowned, and Chunk 7 task 9 parses this plan mechanically, so an obligation
  stated only here is invisible to it. Each chunk's **last task** fills
  the **`Test` and `Implementation` cells of this workstream's existing
  per-requirement rows** for the work that chunk landed. It does **not append
  rows**: that file's own preamble reserves `Spec`/`Test`/`Implementation`/
  `Verified` to `sdd:specs`, `sdd:implement` and `sdd:verify` and records that
  the rows themselves were created by the orchestrator at the requirements gate,
  and `skills/implement/SKILL.md` says the same. Neither
  `docs/ws/packaging/traceability.md`, `docs/ws/marketplace/traceability.md` nor
  the aggregate contains a single `Q-IMPL`-keyed row — there is no precedent for
  one, and an earlier draft of this convention invented it.
  **Never add a seventh column** — a seventh cell makes every row unparseable —
  and never regenerate `docs/requirements/traceability.md` (**D4**): the
  orchestrator regenerates the aggregate from this file as post-gate bookkeeping.
- **Where a Q-IMPL raised in Chunks 0–5 lands, and why no `Q-IMPL-…` id may
  appear in a `docs/` file before it does.** `gc.py`'s `qimpl-undefined` rule is
  **`fail` severity** and sweeps every file under `docs/` except
  `docs/research/`, accepting `Q-IMPL-<WS>-NNN` for any live workstream token. So
  an id written into any docs file **before** its defining `### Q-IMPL-…`
  heading exists in `docs/spec/*.md` raises one `fail` per id — which would turn
  Chunk 6's `gc.py --report` task, Chunk 8's gate tasks **and the committed
  `gc.py --fast` hook** red, from the close of whichever chunk wrote it.
  Chunks 0–5 declare no `docs/spec/**` path and so cannot define such a heading.
  **Decision**: a Q-IMPL raised in Chunks 0–5 is recorded in that chunk's
  **Notes** (below) under a provisional description carrying **no id**, and its
  durable `### Q-IMPL-…` heading (this workstream's prefix, next free counter)
  is written by **Chunk 7**, in
  `docs/spec/two-root-linter.md`, which that chunk already holds in write scope.
  The id and the heading are therefore born in the same commit. Deferring the
  entry is preferred over widening six chunks' scopes to `docs/spec/**`, which
  would dissolve the scoping this plan is built on.
- **"The chunk's notes" has one destination**: a `**Notes**:` block appended
  under that chunk **in this file**, `docs/ws/consumer-geometry/plan.md`. It is
  in every chunk's write scope by the harness default implement scope
  (`skills/orchestrate/references/write-scope.md`, which adds the active plan and
  traceability file to every implement leaf), which is why no chunk re-declares
  it; it is named here so that Chunk 0 task 4's observations, Chunk 6 task 2's
  escape-hatch deviations and Chunk 8's hook artefacts all have a stated home
  rather than three implied ones.
- **Named shas used by this plan**, resolved from git history so no implementer
  guesses: the **marketplace** cycle's end sha is `29febe6` (merge of PR #4), the
  **packaging** cycle's end sha is `0bdb076` (merge of PR #5), and this cycle's
  **entry sha** is `3bac4af` — the sha the kickoff's §The observation was measured
  at, before any edit, and equivalently `git merge-base consumer-geometry main`.
- **"Demonstrated"** means: apply the mutation on a temporary copy of the tool,
  run, assert the printed `SELF-TEST FAIL:` list contains a line beginning with
  that row's own `cg-row-<n>:` token, revert, and observe exit 0 with no such
  line. A described-but-unrun mutation does not discharge a task.

## Decisions taken by this plan, recorded not silent

**D1 — the `cg-row-<n>:` token constant is populated incrementally.**
REQ-PKG-CONSUMERGEOMETRY-001 acceptance 4 requires both tools' `--self-test` to
exit 0 **after every edit made under the permission**, while the first recorded
ordering constraint requires the Q4-gap fixtures to land *before* the behaviour
changes they observe. Authoring all eight cases up front against behaviour that
has not landed makes the self-test red for most of the cycle and breaks
acceptance 4. This plan therefore reads the ordering constraint at **task**
granularity, not cycle granularity: within each row's task the case is authored
first and the behaviour second, and the mutation demonstration is what shows the
case observes the change at the moment it is made. The tool's named token
constant holds exactly the rows whose cases are registered, grows by one entry
per row-landing task, and the in-tool constant-vs-registered equality is green at
every chunk close. The requirement-table-vs-tool set equality is
REQ-PKG-CONSUMERGEOMETRY-001 acceptance 3's **verify-stage desk check**, which is
evaluated once, at the end, when the constant is complete (Chunk 9 task 1).

**D2 — rows 6, 7 and 8 are fixture-only tasks.** Their guards (`rel=Path(...)`)
are already present in the source; the mutation is *deleting* the keyword
argument. So those rows need no behaviour change — only a registered case that
runs under a disjoint suite root and would raise `ValueError` if the guard were
removed. Recorded because a reader who expects eight behaviour edits from an
eight-row table will look for three that do not exist.

**D3 — `docs/spec/two-root-linter.md` is written by two chunks, and that is
intentional.** Chunk 6 makes its `skills/orchestrate/tools/` prose true (class A,
REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2, evaluated by a grep derived from the
disposition table at run time, so it must be true at Chunk 6's close); Chunk 7
lands the two `--suite-root` absence sentences (REQ-PKG-CONSUMERGEOMETRY-003
acceptance 4). Both chunks declare the path. The exclusivity clause of §CG-11(a)
covers `docs/requirements/integration/packaging.md` only, and this file is not
it.

**D4 — the aggregate is never regenerated by a leaf.** Every task that corrects a
traceability row corrects the **per-workstream source** row and asserts the
aggregate's current row by **reading** it. `docs/requirements/traceability.md`
appears in no chunk's write scope. The orchestrator regenerates at the gate and
the regenerate-and-diff of REQ-PKG-CONSUMERGEOMETRY-005 acceptance 4 is evaluated
there (§CG-11 rule 2).

## Ordering Constraints

Four, all recorded upstream, all encoded below as `Depends on` edges:

| # | Constraint | Source | Encoded as |
|---|---|---|---|
| OC1 | The Q4-gap fixtures of -001 land **before** the behaviour changes of -002..-004, so each change's reversion is observable at the moment it is made | `docs/requirements/index.md` §consumer-geometry delta note | Chunk 0 (harness) precedes every behaviour chunk; within each task, case-then-behaviour (D1) |
| OC2 | Within -005, the REQ-PKG-MARKETPLACE-006 amendment lands **before** the directory removal, never after | same | Chunk 6 **entry criterion**, asserted by grep — the amendment is already on disk as the `[Updated: 2026-09-21b]` note, so the constraint is discharged by verification, not by a task |
| OC3 | -001 acceptance 3's desk-check half is **verify-stage work and must carry a plan task of its own** | same (added at requirements iteration 2) | Chunk 9 task 1 |
| OC4 | -004's `GEOMETRY:` token lands **before** -006 acceptance 1 is evaluated | `two-root-linter.md` §CG-10 | Chunk 1 (token) precedes Chunk 3 (derivation) and Chunk 5 (end-to-end evaluation) |

§CG-10's fallback — splitting -006 acceptance 1's `[structure]` clause from its
`GEOMETRY: nested` clause — is **not used**. No conflict arises: -004 is a
print-site change with no dependency on the derivation, so it is ordered first
without cost.

## Chunks

### Chunk 0: The `cg-row-` reporting surface and the disjoint scratch helper
**Goal**: The per-case reporting surface §CG-7 requires exists, is falsifiable,
and is green; the §CG-8 disjoint scratch construction exists once as a reusable
self-test helper rather than being re-spelled in each later fixture; the
pre-change observations every later criterion is red against are pinned.
**Depends on**: None.
**Write scope**: `plugins/sdd/tools/skill-lint.py`, `plugins/sdd/tools/gc.py`,
`docs/ws/consumer-geometry/traceability.md`.
**Tasks**:
1. [x] [implement] Add the named row-token constant to `skill-lint.py` and its
   mirror to `gc.py` — **each holding only the rows whose cases live in that
   tool** (`skill-lint.py`: rows 1-3, 5-8; `gc.py`: row 4 alone), never eight in
   each, since a constant naming a row with no case in that tool fails its own
   constant-vs-registered equality (see Chunk 4 task 5) — plus the registration
   mechanism: a case contributes a
   failure string **beginning with** its stable `cg-row-<n>:` token to the same
   `failures` list `--self-test` already prints as `SELF-TEST FAIL:` followed by
   one `- <string>` line per failure. `--self-test` asserts that every member of
   the constant is registered and run. Per D1 the constant is populated
   incrementally; it is empty at this task's close and the completeness
   assertion is therefore vacuous, so task 2 supplies its falsifiability
   — traces to `two-root-linter.md` §CG-7
2. [x] [implement] Make the completeness assertion falsifiable rather than
   vacuous: register a self-check that (a) a token present in the constant with
   no registered case fails naming that token, and (b) a registered `cg-row-`
   case whose token is absent from the constant fails symmetrically. **Mutation
   run, not described**: add a ninth token to a temporary copy with no case →
   the printed list carries a line naming it; remove the case for a registered
   token → the symmetric line appears. Without this the constant-vs-registered
   equality would pass by holding nothing, which is the vacuity class this whole
   delta exists to close — traces to `two-root-linter.md` §CG-7
3. [x] [implement] Add the §CG-8 disjoint scratch helper to the self-test
   fixture layer: build a scratch far root by copying `plugins/sdd` into
   `$TMPDIR`, disjoint by construction and never referencing any in-repo path,
   and never the installed cache. Every later chunk's disjoint fixture calls it
   — traces to `two-root-linter.md` §CG-8, kickoff constraint 1
4. [x] [verify] Pin the pre-change observations, derived at run time and recorded
   in the chunk's notes (not as literals in any criterion): in §CG-8's
   construction the far `skill-lint.py` prints `.: [structure] skills/ directory
   not found` then `FAIL: 1 finding(s), 0 warning(s)`, and the far `gc.py
   --report` passes that same finding through; in-repo `skill-lint.py .` emits
   **no** line beginning `GEOMETRY: ` and reports its current swept-file count.
   These are the red-before states every Chunk 3/5 criterion asserts against
   — traces to `two-root-linter.md` §CG-8
5. [x] [verify] `python3 plugins/sdd/tools/skill-lint.py --self-test` and
   `python3 plugins/sdd/tools/gc.py --self-test` exit 0, and both remain in the
   committed `.pre-commit-config.yaml` hook set, asserted by **parsing that
   file** rather than by recollection — traces to
   `two-root-linter.md` §Acceptance Criteria ("Both tools' gates stay green and
   stay hooks"), REQ-PKG-CONSUMERGEOMETRY-001 acceptance 4
**Entry criteria**: None (first chunk).
**Exit criteria**: Both self-tests exit 0; the constant-vs-registered assertion
is falsifiable in both directions with both mutations run; the disjoint helper is
callable from a fixture; the four pre-change observations are recorded. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

**Notes** (Chunk 0, 2026-09-22):

- **Pre-change observations (task 4), derived at run time.** In §CG-8's disjoint
  scratch construction (`cp -R plugins/sdd "$TMPDIR/cg/far"`, corpus root = the
  repo):
  - the far `skill-lint.py` prints `.: [structure] skills/ directory not found`
    (with its `fix:` line) then `FAIL: 1 finding(s), 0 warning(s)`, exit 1;
  - the far `gc.py --report --root "$REPO"` passes that same finding through as
    the first line of its report and ends `FAIL: 1 finding(s), 0 warning(s),
    34 info`, exit 1;
  - the in-repo `skill-lint.py .` emits **no** line beginning `GEOMETRY: `
    (count 0) and reports `OK: 25 file(s) clean`.
  These are the red-before states the Chunk 3 and Chunk 5 criteria assert
  against. They are recorded here, not written as literals into any criterion.
- **Falsifiability of the constant-vs-registered equality (task 2), both
  mutations run on a temporary copy of `skill-lint.py`:**
  - (a) a ninth token added to `CG_ROW_TOKENS` with no registered case → the
    printed list carries `- cg-row-9: named in CG_ROW_TOKENS but no registered
    case ran it`;
  - (b) a registered `cg_check(9, …)` case with that token absent from the
    constant → `- cg-row-9: ran as a registered case but is absent from
    CG_ROW_TOKENS`;
  - control: token **and** case together → no `cg-row-` line at all.
  Per §CG-7 the comparand is **membership of the printed failure list**, not the
  process exit code: a copy run from outside the repo raises unrelated
  pre-existing failures (so all three runs exit 1), and the cg surface is
  nonetheless clean in the control and carries exactly the expected line in each
  mutation.
- **Observation — minted in Chunk 7 as `Q-IMPL-CONSUMERGEOMETRY-001`**
  (`two-root-linter.md` §Consumer-Geometry Implementation Questions; raised here
  with no id per §Conventions): `gc.py` cannot import `skill-lint.py` — it invokes it
  as a subprocess — so `disjoint_scratch_suite()` and `cg_reconcile()` exist
  once per tool rather than once. The two copies are byte-equivalent in
  behaviour and nothing asserts they stay so; if a later chunk edits one half,
  the drift is silent. Worth a recorded decision (accept the duplication, or
  assert the pair) rather than an accident.
- **Task 5, asserted by parsing `.pre-commit-config.yaml`** (read-only): the
  committed hook set still contains `python3 plugins/sdd/tools/skill-lint.py`,
  `… skill-lint.py --self-test`, `python3 plugins/sdd/tools/gc.py --fast` and
  `… gc.py --self-test` (hook ids `skill-lint`, `skill-lint-self-test`,
  `drift-sweep`, `drift-sweep-self-test`). Both self-tests exit 0.

---

### Chunk 1: `GEOMETRY:` and `— NOTHING SWEPT` (REQ-PKG-CONSUMERGEOMETRY-004, row 3)
**Goal**: A run that swept nothing is not spelled like a run that swept
everything, and every summary-printing run declares its geometry. **First among
the behaviour changes, by OC4.**
**Depends on**: Chunk 0.
**Write scope**: `plugins/sdd/tools/skill-lint.py`,
`docs/ws/consumer-geometry/traceability.md`.
**Tasks**:
1. [x] [implement] Emit the `GEOMETRY:` token as an **own line immediately
   before** the summary line, **iff** the run prints an `OK:`/`FAIL:` summary —
   one token per summary, never two, never one without the other, and none from
   `--self-test`, whose banner is not a corpus summary. Value has exactly three
   members, derived from `suite_contained()` and root equality; the spelling
   **the pipe-separated menu `nested | equal | disjoint` is never emitted; only
   the resolved member is** — stated this way because the criteria two clauses
   later require `GEOMETRY: nested`, `GEOMETRY: equal` and `GEOMETRY: disjoint`
   to be printed, and what is forbidden is the menu spelling, not its members.
   `swept-roots=<n>` is
   `len(swept_roots())`. `suite-rows-root=<path>` is the **effective** suite root
   — the one resolved through §CG-3's three tiers, given, derived or defaulted —
   and renders neither the corpus root, nor `default_suite_root()` when tier 1 or
   tier 2 supplied a root — traces to `two-root-linter.md` §CG-6,
   `skill-lint-v5.md` §The `GEOMETRY:` token is not a finding
2. [x] [implement] Add the `— NOTHING SWEPT` suffix, present **iff**
   `len(skill_files()) == 0`, on **all three** print sites: the `FAIL: …` site,
   the `OK: … clean, W warning(s)` warn variant and the `OK: … clean` clean
   variant. Patching only the two `OK:` sites is the concrete failure
   REQ-PKG-CONSUMERGEOMETRY-004 acceptance 4 exists to catch — traces to
   `two-root-linter.md` §CG-6
3. [x] [implement] Register case `cg-row-3:` — Class B non-vacuity, a zero-sweep
   run distinguishable from a clean one. **Mutation run**: drop the suffix →
   the two summary lines become identical and the case's token appears in the
   printed list; restore → exit 0 — traces to REQ-PKG-CONSUMERGEOMETRY-001 row 3
4. [x] [verify] The §CG-6 acceptance box is **split into four separately
   checkable assertions** (the third recorded plan input; §Consumer-Geometry Open
   Items). Each is asserted and recorded separately so a partial pass is visible:
   (a) **enum rendering** — the far-root fixture prints `GEOMETRY: disjoint`, the
   nested fixture `GEOMETRY: nested`, the equal-roots fixture `GEOMETRY: equal`;
   collapsing the derivation to a constant makes at least two red;
   (b) **`suite-rows-root=` under tier 1** — the far-root fixture renders the
   root passed, not the corpus root;
   (c) **`suite-rows-root=` under tier 2** — deferred to Chunk 3 task 4, where
   fixture D exists, and recorded here as owed rather than silently dropped;
   (d) **unconditional emission** — a fixture whose run has findings still
   carries its `GEOMETRY:` line, and a `--self-test` run carries none; emitting
   only on the clean path, or emitting from a run with no summary, makes this red
   — traces to `two-root-linter.md` §CG-6, §Consumer-Geometry Open Items item 3
5. [x] [verify] The suffix's three sites, each with its mutation **run**: one
   scratch run over a one-file corpus and one over an empty corpus — the string
   appears in the second summary line and not the first; a scratch run over a
   corpus sweeping zero skill files that raises at least one `fail`-severity
   finding prints `FAIL: … — NOTHING SWEPT`; the warn variant over a non-empty
   corpus with a warning prints **no** suffix. Making the suffix unconditional on
   any of the three makes that last one red — traces to
   `two-root-linter.md` §Acceptance Criteria
6. [x] [verify] Confirm `sweep_lint()`'s summary check is a **prefix** match
   (`re.match(r"^(OK|FAIL): ", summary)`, unanchored at the right) so the suffix
   cannot make it flag `linter exited … without a parseable summary`. Recorded as
   an observation with its command; no amendment expected — traces to
   `two-root-linter.md` §CG-6
7. [x] [verify] **The token contributes to no finding count, asserted by
   mutation** — sized here, in the chunk that owns the emission, because the
   write scope that could repair it exists only here. A run over this corpus
   emits **exactly one** `GEOMETRY:` line, on its own line, immediately before
   the summary; on a temporary copy **with the emission removed**, the finding
   count and the summary line's `N` are **unchanged** from the unmutated run.
   "Without the token present" has no construction once the token lands, which is
   why the mutation supplies one. Emitting the token inside a finding, or
   counting it in `N`, makes this red — traces to `skill-lint-v5.md` §The
   `GEOMETRY:` token is not a finding, §Consumer-Geometry Acceptance Criteria
   (second box)
**Entry criteria**: Chunk 0 exit criteria met.
**Exit criteria**: Both self-tests exit 0; `cg-row-3` registered and its mutation
demonstrated; the four split assertions recorded with (c) explicitly owed to
Chunk 3; the three suffix sites each demonstrated; the count-invariance mutation
run and the finding count and `N` observed unchanged. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

**Notes** (Chunk 1, 2026-09-22):

- **Task 4 — the §CG-6 acceptance box, as four separately recorded assertions**
  (so a partial pass is visible):
  - (a) **enum rendering** — run over three scratch fixtures built from the
    §CG-8 helper: the far-root fixture printed `GEOMETRY: disjoint
    swept-roots=1 …`, the nested fixture `GEOMETRY: nested  swept-roots=2 …`
    and the equal-roots fixture `GEOMETRY: equal  swept-roots=1 …`. **PASS.**
    The pipe-separated menu spelling appeared in no output of any of the three.
  - (b) **`suite-rows-root=` under tier 1** — the far-root fixture rendered the
    root passed to the constructor; the value is `!=` the corpus root and `!=`
    `default_suite_root()`. **PASS.**
  - (c) **`suite-rows-root=` under tier 2** — **OWED to Chunk 3 task 4**, where
    fixture D exists. Tier 2 does not exist yet, so today the effective root is
    tier 1 or tier 3 and this assertion has no construction. Recorded as owed,
    not dropped and not faked. **DEFERRED.**
  - (d) **unconditional emission** — a fixture run *with* findings still
    carried exactly one `GEOMETRY:` line, immediately before its `FAIL:`
    summary (the blank separator was moved above the token so the adjacency
    holds on the failing path too); `skill-lint.py --self-test` carried **zero**
    lines beginning `GEOMETRY: `, exit 0. **PASS.**
- **Task 5 — the three suffix sites, each demonstrated, then the mutations
  run** (all fixtures via `disjoint_scratch_suite()`; comparand is membership of
  the printed `SELF-TEST FAIL:` list, never the process exit code):
  - clean variant: one-file corpus → `OK: 1 file(s) clean`; empty corpus →
    `OK: 0 file(s) clean — NOTHING SWEPT`.
  - `FAIL:` site: a corpus sweeping zero skill files that raises one `fail`
    finding → `FAIL: 1 finding(s), 0 warning(s) — NOTHING SWEPT`, exit 1.
  - warn variant over a non-empty corpus with a `[size]` warning →
    `OK: 1 file(s) clean, 1 warning(s)`, **no** suffix.
  - **Mutation 1 (drop the suffix)** on a scratch copy → the printed list
    carried two `cg-row-3:` lines (`… with the count normalised both summaries
    read 'OK: N file(s) clean'` and `the zero-sweep summary must carry the
    suffix, got 'OK: 0 file(s) clean'`).
  - **Mutation 2 (make the suffix unconditional)** → the printed list carried
    `cg-row-3: a run that swept a file must carry no suffix, got 'OK: 1 file(s)
    clean — NOTHING SWEPT'`.
  - **Control** (unmutated scratch copy) → **no** `cg-row-` line at all; the
    in-repo `--self-test` exits 0. A scratch copy run from outside the repo
    exits 1 from unrelated pre-existing fixtures in every one of the three
    runs, which is exactly why the comparand is list membership.
- **Task 6 — observation, no amendment.** Command:
  `grep -n 'without a parseable summary' -B12 plugins/sdd/tools/gc.py`.
  `gc.py:534-535` reads
  `summary = next((ln for ln in reversed(lines) if ln.strip()), "")` then
  `if not re.match(r"^(OK|FAIL): ", summary) or proc.returncode not in (0, 1)`.
  `re.match` anchors at the left only and the pattern carries no `$`, so the
  appended suffix cannot make `sweep_lint()` flag
  `linter exited … without a parseable summary`. **No amendment.** `gc.py` was
  read only; it is not in this chunk's write scope (its forwarding is Chunk 5).
- **Task 7 — count invariance, by mutation.** In-repo `skill-lint.py .` emits
  **exactly one** line beginning `GEOMETRY: `, on its own line, immediately
  before the summary (`GEOMETRY: nested  swept-roots=2
  suite-rows-root=…/plugins/sdd` then `OK: 25 file(s) clean`). On two scratch
  copies run over this repo — one unmutated, one with both
  `print(self.geometry_line())` calls removed — the finding count (1) and the
  summary line (`FAIL: 1 finding(s), 0 warning(s) — NOTHING SWEPT`, i.e. its
  `N`) were **identical**; only the `GEOMETRY:` line count changed, 1 → 0.
- **Observation — minted in Chunk 7 as `Q-IMPL-CONSUMERGEOMETRY-002`**
  (raised here with no id per §Conventions): the `GEOMETRY:` token is emitted by `Linter.run()`
  alone, which is what makes "one token per summary, never one without the
  other" structural rather than asserted. Any future summary printed outside
  `run()` — a `--print-population` summary, say — would silently break the
  one-for-one pairing with no fixture to catch it. Worth a recorded decision
  (keep every summary inside `run()`, or bind the pair in a helper) rather than
  an invariant held only by where the code happens to live today.

---

### Chunk 2: The explicit `--suite-root` surface, on both tools and both branches
**Goal**: REQ-PKG-CONSUMERGEOMETRY-003's tier-1 surface exists, is discoverable,
and **reaches the binding** on every path — including `gc.py`'s `-c` shim branch,
which builds no argv at all.
**Depends on**: Chunk 1.
**Write scope**: `plugins/sdd/tools/skill-lint.py`, `plugins/sdd/tools/gc.py`,
`docs/ws/consumer-geometry/traceability.md`.
**Tasks**:
1. [x] [implement] `skill-lint.py [corpus_root] [--suite-root PATH]`: absolute or
   cwd-relative, resolved to an absolute path, passed to
   `Linter(..., suite_root=PATH)`. Tier 1 is adopted **without any existence
   test**, so an operator can still name a root the derivation would reject
   — traces to `two-root-linter.md` §CG-2, §CG-3
2. [x] [implement] `gc.py` grows the matching surface as `drift-sweep.md` §1
   decides: a `--suite-root PATH` flag plus a `Gc(..., suite_root=None)`
   constructor parameter carrying the same value, with "pass nothing" as the
   default so the linter's tier-2 derivation answers — traces to
   `drift-sweep.md` §1
3. [x] [implement] `lint_command()` **branch (i)**, the `lint_suite_rules` argv
   branch: the constructed vector carries the suite root. Asserted **on the
   vector**, not on the subprocess result — traces to `drift-sweep.md` §2,
   `two-root-linter.md` §CG-2
4. [x] [implement] `lint_command()` **branch (ii)**, the `suite_rules=False` `-c`
   shim: the shim passes the same suite root to its `Linter(...)` constructor.
   Asserted by running the shim against a fixture and reading back
   `suite_contained()` (the preferred form, because it also exercises the
   argument-passing). Fixing branch (i) alone leaves this half red while (i) is
   green — that opposite-direction pair is what makes the two-branch wording
   load-bearing — traces to `drift-sweep.md` §2, `two-root-linter.md` §CG-2
5. [x] [implement] `lint_path()`'s candidate tuple — the second half of -001
   row 4 — is, like rows 6–8, **fixture-only in the D2 sense**, and this task
   says so rather than leaving a reader hunting for a change that is not there:
   REQ-PKG-PACKAGING-010 already pins sibling-first precedence, so the tuple's
   order is correct today and nothing about it changes. What is new is the
   **case** that observes it, whose mutation is "reorder the candidate tuple".
   If the implement stage finds the pinned order is *not* what the source has,
   that is a new finding and this task becomes a real edit — traces to
   REQ-PKG-CONSUMERGEOMETRY-001 row 4, REQ-PKG-PACKAGING-010
6. [x] [implement] Register case `cg-row-4:` in **`gc.py --self-test`** (not the
   linter's). **Mutations run, both**: revert branch (i) to `[executable,
   str(lint), str(self.root)]` → the row-4 token appears in `gc.py`'s printed
   list; reorder the `lint_path()` candidate tuple → the same. Membership in the
   printed list, **not the process exit code**, is the comparand — traces to
   `two-root-linter.md` §CG-7, REQ-PKG-CONSUMERGEOMETRY-001 row 4
7. [x] [verify] `python3 plugins/sdd/tools/skill-lint.py --help` names the
   suite-root surface; removing it from the parser makes this red. This
   deliberately **inverts** REQ-PKG-PACKAGING-003's negative-surface grep. In a
   scratch fixture, invoking with an explicit suite root under the corpus root
   yields `suite_contained() == True` and a non-empty `skill_files()`, while
   invoking the same corpus without it yields the tier-2-or-3 root — accepting
   the argument and discarding it makes the two runs identical and this red
   — traces to `two-root-linter.md` §Acceptance Criteria
8. [x] [verify] **The sweep's half of the same surface, which task 7 does not
   reach.** `python3 plugins/sdd/tools/gc.py --help` names `--suite-root`,
   **and** `Gc(...)` accepts a `suite_root` keyword. **Both mutations run**:
   removing the flag from the parser makes this red; removing the keyword from
   the constructor makes it red independently. It is red today, where neither
   exists. Sized separately from task 7 because that task asserts only the
   linter's `--help`, and this chunk's exit criterion previously said "`--help`
   names the surface" in the singular — which would have left this box to
   surface as a plan defect at Chunk 9 task 4, the last possible moment
   — traces to `drift-sweep.md` §Consumer-Geometry Acceptance Criteria (first
   box), REQ-PKG-CONSUMERGEOMETRY-003 acceptance 1 sweep half
9. [x] [verify] `drift-sweep.md` §Acceptance Criteria's omission half: with
   `suite_root is None` both `lint_command()` branches are byte-identical to
   today's constructed strings — traces to `drift-sweep.md` §1, §2
10. [x] [verify] **REQ-PKG-PACKAGING-003 leg (i) is preserved while its
   `--suite-root` deferral is superseded** — the two greps, run here in the chunk
   that adds the surface, because this is where a disable switch would be added
   and therefore where the write scope to remove one exists: `grep -n
   'no-suite-rules' plugins/sdd/tools/skill-lint.py` is **still empty**, and
   every `suite_rules=False` construction site is **still inside the self-test**.
   Adding a disable switch alongside the new surface makes this red — traces to
   `skill-lint-v5.md` §Consumer-Geometry Acceptance Criteria (third box),
   REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4 second half
**Entry criteria**: Chunk 1 exit criteria met.
**Exit criteria**: Both self-tests exit 0; `--help` names the surface; both
`gc.py` branches carry the root, each demonstrated by its own mutation;
`cg-row-4` registered; **both tools'** `--help` name the surface and `Gc(...)`
accepts the keyword, each with its own mutation run; both leg-(i) greps run and
recorded with their commands. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

**Notes** (Chunk 2):

- **Task 5 confirmed fixture-only (plan D2).** `lint_path()`'s candidate tuple
  is `(Path(__file__).resolve().parent / "skill-lint.py", self.root / "tools" /
  "skill-lint.py")` — sibling first, exactly the order REQ-PKG-PACKAGING-010
  pins. Nothing about the tuple changed; what is new is the case that observes
  it, whose mutation is the reorder. No new finding.
- **Mutations run, all six, each observed rather than asserted.**
  Branch (i) reverted to `[sys.executable, str(lint), str(self.root)]` →
  `gc.py --self-test`'s printed list carries
  `cg-row-4: branch (i) does not carry the suite root: [...]` and **nothing**
  from branch (ii). Branch (ii)'s shim constructor reverted to
  `m.Linter(Path(sys.argv[2]), suite_rules=False)` → the list carries the three
  branch-(ii) lines (`GEOMETRY: disjoint … suite-rows-root=<this repo>/plugins/sdd`)
  and **nothing** from branch (i). That opposite-direction pair is the evidence
  the two-branch wording is load-bearing. `lint_path()`'s tuple reordered →
  `cg-row-4: lint_path() must prefer the sibling …, got <corpus>/tools/skill-lint.py`.
  The linter's `--suite-root` removed from its parser → task 7's `--help`
  assertion red. `Linter.__init__` made to discard the argument
  (`self.suite_root = default_suite_root()`) → task 7's fixture half red
  (`suite_contained()` False under an explicit root inside the corpus).
  `gc.py`'s flag removed from its parser and, independently, `suite_root`
  removed from the `Gc` constructor signature → task 8 red on each, separately.
  Membership of the printed failure list was the comparand throughout, never a
  process exit code.
- **Task 9's omission half holds byte-exactly.** With `suite_root is None`,
  branch (i) is `[sys.executable, str(lint), str(root)]` and branch (ii)'s
  program string is character-identical to the one at the entry sha `3bac4af`,
  compared against a transcription of that source rather than against the
  current file. The shim is therefore assembled **conditionally** (two ctor
  spellings, `sys.argv[3]` appended only when a root is passed) instead of
  always reading an extra argv slot — the always-read form would have changed
  the default string and failed this task.
- **Task 10's two greps, run here with their commands.**
  `grep -n 'no-suite-rules' plugins/sdd/tools/skill-lint.py` → **exit 1, no
  output**: leg (i) is preserved, no disable switch was added alongside the new
  surface. `grep -n 'suite_rules=False' plugins/sdd/tools/skill-lint.py` → every
  `Linter(...)` construction site is at line 1342 or inside `self_test()`
  (lines 1346-3092). **Observation worth recording, not a defect**: line 1342
  sits in `_run_capture()`, a module-level *helper* defined just above
  `self_test()` and lexically outside it. Its only callers are inside
  `self_test()` (checked: no call site below line 1346 is absent and none above
  it exists), so no production path constructs with `suite_rules=False`. A
  future reader running the grep literally will see one line outside the
  self-test's line range; the binding is "no production construction site", and
  it holds.
- **Q-IMPL-shaped observation — minted in Chunk 7 as
  `Q-IMPL-CONSUMERGEOMETRY-003` (raised here with no id, plan §Conventions).** *Provisional description*: `print_population()` takes a
  `suite_root` positional and `main()` must therefore decide tier 1 twice — once
  for `print_population(root, …)` and once for `Linter(root, suite_root)` — with
  the `--print-population` path passing `default_suite_root()` explicitly where
  the lint path passes `None` and lets the constructor resolve. Once Chunk 3
  lands tier 2 **in the constructor**, the `--print-population` path will be the
  only caller that bypasses that resolution and will report a tier-3 root where
  the lint path reports tier 2. Candidate resolution: have `print_population()`
  build its `Linter` from `(corpus_root, suite_root_or_None)` so the one
  resolution serves both. Not acted on here: Chunk 3 owns the constructor.

---

### Chunk 3: The tier-2 corpus-root derivation, resolved in `Linter.__init__`
**Goal**: A tool running from outside the corpus reaches the working tree. The
three precedence tiers are resolved **in the constructor**, so every construction
path — CLI, `gc.py`'s `-c` shim, a direct fixture — gets the same answer.
**Depends on**: Chunk 2.
**Write scope**: `plugins/sdd/tools/skill-lint.py`,
`docs/ws/consumer-geometry/traceability.md`.
**Tasks**:
1. [x] [implement] Add tier 2 **in `Linter.__init__`**, in the place of the
   existing tier-3 expression, so the resolution order is one piece of code every
   construction path reaches:
   `candidate = corpus_root/"plugins"/"sdd"`, adopted **iff** `candidate.is_dir()`
   **and** `(candidate/"skills").is_dir()` **and**
   `candidate.resolve() != default_suite_root().resolve()`. Precedence is exactly
   three tiers and no fourth: explicit (tier 1, no existence test) → derived
   (tier 2) → `default_suite_root()` (tier 3). Implementing tier 2 in `main()`
   instead freezes the shim on tier 3 permanently — traces to
   `two-root-linter.md` §CG-1, §CG-3
2. [x] [implement] Fixture D, the **look-alike corpus** (new, in the existing
   `--self-test` scratch-root style, no cache write): a scratch corpus root `F`
   holding both `F/skills/<name>/SKILL.md` and
   `F/plugins/sdd/skills/<name>/SKILL.md`, the latter seeded with one walk-class
   violation (forbidden phrase or bad frontmatter), invoked with corpus root `F`
   and **no** explicit suite root — traces to `two-root-linter.md` §CG-4
3. [x] [implement] Register cases `cg-row-1:` and `cg-row-2:` — the Class C
   checks under a disjoint suite root. Row 1: `check_retired_prefix()`, the
   highest-value single item, a live crash that survives all four gates today;
   **mutation run**: rebind its scope walk to the corpus root only. Row 2:
   `check_required()`'s 56 gated rows; **mutation run**: rebind the rows to the
   corpus root. Row 2's mutation also trips the pre-existing C12.1 fixture, so a
   green-to-red transition of the *process* would not show the new disjoint case
   fired — the assertion is that the printed list contains a line beginning with
   that row's own token — traces to `two-root-linter.md` §CG-7,
   REQ-PKG-CONSUMERGEOMETRY-001 rows 1, 2
4. [x] [verify] **The positive direction fires, observable four ways at once**
   (REQ-PKG-CONSUMERGEOMETRY-006 acceptance 6, added by the spec; this also
   discharges Chunk 1 task 4(c)): in fixture D, `suite_contained()` is `True`;
   the token reads `GEOMETRY: nested` with `swept-roots=2`; `suite-rows-root=`
   renders `F/plugins/sdd` and **not** `default_suite_root()`; and the seeded
   violation **is** reported with its path rendered `skills/…` relative to the
   root it was walked from, asserted **by name on that seeded path**, never by a
   count. Red today. Returned to red after the change by three separate
   mutations, **each run**: dropping tier 2; keying tier 2 on the tool's own
   location; rendering the suite seed against the corpus root — traces to
   `two-root-linter.md` §CG-4, §Acceptance Criteria
5. [x] [verify] **The foreign consumer is untouched, in both negative
   directions**: a scratch corpus with its own `skills/` and no `plugins/sdd/` —
   the derivation does not fire, `swept_roots()` equals exactly `{corpus_root}`,
   the token reads `disjoint`, their `skills/` is still walked, no
   `— NOTHING SWEPT` suffix appears; and with `plugins/sdd/` present but holding
   no `skills/` the candidate is not adopted and the run reports `disjoint`
   rather than naming an empty suite root. Making the derivation unconditional
   fires it in the first; dropping the `skills/` existence test makes the second
   red — traces to `two-root-linter.md` §Acceptance Criteria
6. [x] [verify] **The per-geometry split holds.** In a two-root fixture whose
   suite root is given explicitly and lies under the corpus root,
   `len(skill_files()) > 0` and `suite_contained()` is `True`; with the suite
   root left to a **far** scratch default, `len(skill_files()) == 0`. **The
   fixture's suite subdirectory must be named `vendor/suite`, not
   `plugins/sdd`** (§CG-5a) — §7 fixture A's tree, which is, cannot be reused
   here, or tier 2 fires and the criterion is red by construction against a
   correct implementation. In §7 fixture B's disjoint consumer shape,
   `swept_roots()` equals exactly `{corpus_root}` and the suite root contributes
   zero walked files — **implementing Option B makes this red, which is how the
   rejection is enforced rather than recorded**. C12.1 passes unmodified, pinning
   the 16 rows it pins and deliberately not 56 — traces to
   `two-root-linter.md` §CG-5, §CG-5a
7. [x] [verify] **Every construction path resolves the same tiers**, asserted on
   the path no other criterion reaches: `gc.py`'s branch-(ii) `-c` shim, run in
   fixture mode over a scratch corpus holding `plugins/sdd/skills/` with **no**
   explicit suite root, yields `suite_contained() == True` and a non-empty
   `skill_files()` — the same answer the CLI gives on the same corpus, asserted
   by comparing the two. Implementing tier 2 in `main()` leaves the shim on tier 3
   and the two paths disagree — traces to `two-root-linter.md` §CG-3,
   §Acceptance Criteria
8. [x] [verify] **The nested case is not regressed**: in-repo `python3
   plugins/sdd/tools/skill-lint.py .` still reports `GEOMETRY: nested` and the
   same swept-file count it reports today, both derived at run time, never pinned
   as literals. A live risk: the in-repo copy's tier-2 candidate and its
   `default_suite_root()` are the same directory, which is what §CG-3's third
   condition exists to decline — traces to `two-root-linter.md` §CG-3
**Entry criteria**: Chunk 2 exit criteria met; the `GEOMETRY:` token exists
(OC4), so acceptance 1's token clause is decidable.
**Exit criteria**: Both self-tests exit 0; fixture D green with all four
observations; both negative directions green; the shim and the CLI agree; the
nested case unregressed; `cg-row-1` and `cg-row-2` registered and demonstrated. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

---


**Notes** (Chunk 3):

- **Tier 2 lives in `Linter.__init__`.** The tier-3 expression
  (`self.suite_root = default_suite_root() if suite_root is None else suite_root`)
  became an explicit three-tier `if`: explicit parameter (no existence test) →
  `derived_suite_root(corpus_root)` → `default_suite_root()`. The derivation is
  a module-level pure function beside `default_suite_root()`, with all three
  conjuncts required. `gc.py` was not touched and inherits the derivation for
  free, which is the point — task 7 reads exactly that.
- **The headline behaviour, measured by §CG-8's construction.** `cp -R
  plugins/sdd "$TMPDIR/cg/far"` then `python3 "$TMPDIR/cg/far/tools/skill-lint.py"
  "$REPO"` now prints `GEOMETRY: nested  swept-roots=2
  suite-rows-root=<repo>/plugins/sdd` and `OK: 25 file(s) clean`, exit 0 — where
  before the change it printed `.: [structure] skills/ directory not found` and
  `FAIL: 1 finding(s)`. `python3 "$TMPDIR/cg/far/tools/gc.py" --report --root
  "$REPO"` passes nothing through from the lint sweep and closes `OK: 9 sweep(s)
  clean`. The installed cache was never read or written.
- **Task 4 — fixture D, four observables on one run**, case
  `derivation_positive_direction`: `suite_contained()` True; the token reads
  `GEOMETRY: nested` with `swept-roots=2`; `suite-rows-root=` renders
  `F/plugins/sdd` with `default_suite_root()` asserted **absent** from the line;
  and the seeded walk-class violation is reported **by name** at
  `skills/lookalike-skill/SKILL.md` (the corpus's own skill is named
  `own-skill`, so the by-name assertion discriminates the rendering root). No
  count is asserted anywhere in the case. **This discharges Chunk 1 task 4(c)**
  — `suite-rows-root=` under a tier-2 root — which Chunk 1 deferred to here; the
  deferral is closed.
- **Task 4's three mutations, each RUN on a `$TMPDIR` scratch copy.** (a) tier 2
  dropped from the constructor → fixture D reports `GEOMETRY: disjoint
  swept-roots=1` and six of the case's lines fail. (b) tier 2 keyed on
  `default_suite_root()` instead of `corpus_root` → identical failure set. (c)
  `rel()`'s deepest-root rule inverted so the suite seed renders against the
  corpus root → the by-name line fails with the path spelled
  `plugins/sdd/skills/lookalike-skill/SKILL.md` (and §7 fixture A's per-root
  pin fails alongside it, as §CG-4 predicts).
- **Task 3 — rows 1 and 2 registered, each with its mutation RUN.** Row 1
  (`cg_row_1_retired_prefix_under_a_disjoint_suite_root`): a disjoint fixture
  whose suite root holds `skills/suite-retired/SKILL.md` and whose corpus root
  holds an identically broken `skills/corpus-retired/SKILL.md`; `skills` is a
  **suite**-bound scope entry, so the suite seed must be reported and the corpus
  decoy must not. Mutation — `retired_scope_roots()` returning
  `[self.corpus_root]` → the printed list carries two lines beginning
  `cg-row-1:`. Row 2
  (`cg_row_2_required_rows_under_a_disjoint_suite_root`): the disjoint twin of
  C12.1, covering both populations of the 56 — the 16 gated-table rows (suite
  seed `verify`, corpus decoy `replan`, differently named so the locations
  discriminate) and a `REQUIRED` table row present-but-short under the suite
  root and absent from the corpus, so the mutation flips its message from
  `found 0x` to `file missing entirely`. Mutation — all three
  `f = self.suite_root / rel` sites rebound to `self.corpus_root` → the printed
  list carries four lines beginning `cg-row-2:`. As §CG-7 warns, that same
  mutation also trips C12.1 and the §3 retarget case, so **membership of the
  printed list, never the process exit code, was the comparand** for both rows.
  `skill-lint.py`'s `CG_ROW_TOKENS` now holds
  `("cg-row-1:", "cg-row-2:", "cg-row-3:")`; rows 5-8 arrive in Chunk 4.
- **Task 5 — both negative directions, both mutations run.** Case
  `derivation_declines_for_a_foreign_consumer`. (a) A consumer corpus with its
  own `skills/` and no `plugins/sdd/`: tier 3 answers, `swept_roots()` is
  exactly `{corpus_root}`, the token reads `disjoint`, their `skills/` is still
  walked and no `— NOTHING SWEPT` suffix appears. Mutation — the derivation made
  **truly** unconditional (both existence tests removed) → the half goes red.
  Recorded because it is a live trap: removing only `candidate.is_dir()` leaves
  the `skills/` test guarding the same path, and the case stays green — the
  mutation has to remove both to be the mutation the requirement names. (b)
  `plugins/sdd/` present with no `skills/` under it: the candidate is declined
  and the run reports `disjoint` rather than naming an empty suite root.
  Mutation — the `skills/` test alone dropped → the half goes red on three
  lines.
- **Task 6 — the per-geometry split, on a `vendor/suite` fixture (§CG-5a).**
  Case `per_geometry_split_holds` builds its own tree and does **not** reuse §7
  fixture A, whose suite subdirectory is named `plugins/sdd`: with the explicit
  root, `suite_contained()` is True and `len(skill_files()) > 0`; with no root
  passed, `derived_suite_root()` returns `None` by construction and
  `len(skill_files()) == 0`. Fixture B's Option-B tripwire is re-asserted in the
  same case (`swept_roots() == {corpus_root}`, zero walked files from the suite
  root); mutation — admitting a disjoint suite root to `swept_roots()` →
  fourteen lines red, including both of this case's. C12.1 is unmodified and
  still registered, pinning its 16 rows and deliberately not 56.
- **Task 7 — the shim and the CLI agree, and the comparison is only sound
  through `main()`.** Case `shim_and_cli_resolve_the_same_tiers` loads `gc.py`
  beside the linter, builds its branch-(ii) `-c` command with
  `Gc(corpus, lint_suite_rules=False).lint_command(...)`, runs it, and compares
  its `GEOMETRY:` line against the line a **subprocess CLI** run prints on the
  same corpus. The first draft compared against an in-process `Linter(...)` and
  was silently vacuous: it would have agreed with the shim even with tier 2
  implemented in `main()`. Mutation — tier 2 moved out of the constructor into
  `main()` → the case fails with `shim 'GEOMETRY: disjoint …' vs CLI 'GEOMETRY:
  nested …'`. Both paths are given the **resolved** corpus root, because
  `main()` resolves its positional and the shim does not, and a `/tmp` symlink
  difference would otherwise mask the comparison.
- **Task 8 — the nested case is unregressed.** In-repo `python3
  plugins/sdd/tools/skill-lint.py .` still prints `GEOMETRY: nested
  swept-roots=2` and `OK: 25 file(s) clean`. Case
  `nested_case_is_not_regressed` pins it structurally rather than by literal:
  the corpus root is derived from the tool's own location at run time, tier 2 is
  asserted to **decline** it (third conjunct), and the swept-file count of the
  implicit construction is compared against the same run built with the root
  passed explicitly — no number appears in the case.
- **Carried forward from Chunk 2, acted on here.** `print_population()` took a
  `suite_root` **positional** and `main()` substituted `default_suite_root()`
  for `None`, so `--print-population` would have been the one caller bypassing
  the constructor's tier-2 resolution — the shim's defect class, one caller
  over. Its parameter is now `Path | None = None` and `main()` passes the
  tier-1-or-`None` value straight through. The existing `print_population_shape`
  case passes both roots explicitly and is unaffected. This does not weaken
  enumerated row 5, whose named mutation (`(root, root)`) still mis-roots the
  wiring observably.
- **One pre-existing case was corrected, not deleted.** `two_roots_construct_
  distinct_and_equal` asserted `Linter(tr_corpus).suite_root ==
  default_suite_root()` on a fixture whose corpus root holds
  `plugins/sdd/skills/` — under tier 2 that corpus now correctly resolves to the
  derived root, so the assertion as written would have asserted the derivation
  away. Tier 3 is now pinned on `tr_far` (nothing to derive) and tier 2 on
  `tr_corpus`, so both tiers keep a fixture and neither is asserted on a corpus
  that selects the other.
- **Provisional observation, no id.** Every mutation run above was performed on
  a `cp -R` scratch copy of `plugins/sdd` under `$TMPDIR`; no repository file
  was edited to test a mutation. The **unmutated** scratch control is red on
  exactly one pre-existing line — `docs/spec/ not found at the corpus root above
  the real skill suite` — because `docs/` is outside the shipped plugin, so a
  copy of the plugin alone cannot satisfy that case. Every additional line in a
  mutation run is therefore attributable to the mutation, and no control run
  printed any `cg-row-` line. The revert half of REQ-PKG-CONSUMERGEOMETRY-001
  acceptance 2 (`exit 0 with no such line`) is observed **in-repo**, where the
  unmutated self-test exits 0. Whether that pre-existing case should be made
  skippable outside a full checkout is left to the verify stage.

### Chunk 4: The remaining enumerated rows — the guards and the wiring
**Goal**: The Q4-gap rows that are not covered by Chunks 1–3 are each bound to a
registered case with its mutation run. Per **D2**, rows 6–8 are fixture-only.
**Depends on**: Chunk 3.
**Write scope**: `plugins/sdd/tools/skill-lint.py`,
`docs/ws/consumer-geometry/traceability.md`.
**Tasks**:
1. [x] [implement] Row 5, behaviour: pin `main()`'s
   `print_population(root, default_suite_root())` wiring, and add
   `retired_scope_entries()`'s deduplication (`seen` set). Each closes with a
   technique already in the file. Register `cg-row-5:`; **mutations run, both**:
   mis-root the wiring to `(root, root)`; remove the deduplication — traces to
   REQ-PKG-CONSUMERGEOMETRY-001 row 5, kickoff §Scope 4
2. [x] [implement] Register `cg-row-6:` — `check_retired_prefix()`'s
   `rel=Path(rel)` guard, under a disjoint suite root. **Mutation run**: delete
   the keyword argument → `rel()` raises `ValueError` and the case contributes
   its token — traces to REQ-PKG-CONSUMERGEOMETRY-001 row 6, kickoff §Scope 2
3. [x] [implement] Register `cg-row-7:` — `check_required()`'s `rel=Path(rel)`
   guards, **three call sites, one row**. **Mutation run**: delete the keyword
   arguments — traces to REQ-PKG-CONSUMERGEOMETRY-001 row 7
4. [x] [implement] Register `cg-row-8:` — `check_template_drift()`'s
   `rel=Path(TEMPLATE_SOURCE)` guard. **Mutation run**: delete the keyword
   argument — traces to REQ-PKG-CONSUMERGEOMETRY-001 row 8
5. [x] [verify] The named token constants hold their rows **per tool** — not
   eight in each. `skill-lint.py`'s constant holds rows 1-3 and 5-8;
   `gc.py`'s holds **row 4 alone**, because row 4 (`lint_path()` /
   `lint_command()`) is the only enumerated row with a case in that tool
   (-001 acceptance 1; `drift-sweep.md` box 4). The **eight-row reconciliation is
   the union of both tools' printed tokens**, which is how Chunk 9 task 1 already
   reads it. An eight-member constant in `gc.py` fails that tool's own
   constant-vs-registered equality on seven members and turns `gc.py --self-test`
   red. Every member registered and run, the falsifiability self-check of Chunk 0
   task 2 still fails in both directions, and both self-tests exit 0 — traces to
   `two-root-linter.md` §CG-7, §Acceptance Criteria
**Entry criteria**: Chunk 3 exit criteria met.
**Exit criteria**: All eight `cg-row-` tokens registered; every one of the eight
mutations **applied, run, and reverted**, with the printed-list assertion made
each time; both self-tests exit 0. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

---

**Notes** (Chunk 4, 2026-09-22):

- **Two premises of task 1 were false, and both halves of row 5 turned out to be
  fixture-only.** (a) The plan and the requirement spell the wiring
  `print_population(root, default_suite_root())`; the source at this chunk's
  entry reads `print_population(root, suite_root)`, because Chunk 2's carried-forward
  note was acted on at Chunk 3 — `print_population()`'s second parameter became
  `Path | None = None` and `main()` now passes the tier-1-or-`None` value straight
  through. Nothing was re-wired here; the row's named mutation `(root, root)` is
  still the right mutation and still mis-roots observably, so the enumeration did
  not need amending. (b) `retired_scope_entries()`'s deduplication was described
  as "genuinely missing"; it is **not**. The `seen` set is present at this cycle's
  entry sha `3bac4af` (`skill-lint.py:592` there). Nothing was added. Both halves
  are therefore observed, not written, which is what D2 already says about rows
  6-8 — so all four rows this chunk lands are fixture-only.
- **Row 5's mutations, both run** on a `$TMPDIR` scratch copy, comparand =
  membership of the printed `SELF-TEST FAIL:` list:
  - `(root, root)` → two `cg-row-5:` lines, both reading
    `got 'corpus: FILES_SWEPT=0  policed-areas=11'` — one for the tier-1 fixture
    (an explicit `vendor/suite` root holding the only skill file) and one for the
    tier-2 fixture (a `plugins/sdd` root reached only by the constructor's
    derivation). The second half is what pins Chunk 3's pass-through: a `main()`
    that substitutes any root of its own loses it.
  - `seen` removed → `got 2 arrivals of CLAUDE.md` plus a second line showing the
    same `[retired-prefix]` finding printed twice. The fixture makes the
    corpus-side `CLAUDE.md` a **symlink** to the suite-side file, because that is
    the only way a union-bound entry arrives twice at one *resolved* path; no
    other registered case observes the dedup, so it was previously unpinned.
- **Rows 6, 7, 8 — the guards were already there; what was missing was the
  observation, and it only exists under a disjoint suite root.** Each case
  catches the `ValueError` rather than letting it escape, so the mutation shows up
  as a line in the printed list rather than as a traceback. Mutations run:
  - row 6, `check_retired_prefix()`'s one `rel=Path(rel)` deleted → `cg-row-6:`
    twice (`self.rel() raises … is not in the subpath of …`, then the empty
    rendering assertion);
  - row 7, all **three** of `check_required()`'s `rel=Path(rel)` deleted → four
    `cg-row-7:` lines. One fixture fires all three sites (a short `REQUIRED` row,
    and a `skills/verify` seed that trips both gated tables), so deleting any one
    of the three is equally visible. The `file missing entirely` branch is
    deliberately **not** one of the three sites: it flags a relative path, which
    `rel()` returns unchanged, so it observes nothing;
  - row 8, `check_template_drift()`'s `rel=Path(TEMPLATE_SOURCE)` deleted → two
    `cg-row-8:` lines, on a fixture whose suite-side `TEMPLATE_SOURCE` exists but
    opens no anchored fence, so all four `TEMPLATE_PAIRS` rows take the guarded
    branch.
- **One harness change was unavoidable, and it is the reason the rows 6-8
  mutations are observable at all.** Deleting a `rel=` override also makes
  *earlier, unrelated* cases raise — row 1's case for row 6's mutation,
  `disjoint_suite_walk_excluded` and row 2's case for row 7's,
  `template_pairs_bind_per_side` for row 8's. Uncaught, the process dies before
  `SELF-TEST FAIL:` is printed and §CG-7's comparand (membership of that list) is
  unobservable. The `for _case in (...)` loop therefore now records an aborting
  case as a failure line (`<case> aborted: ValueError: …`) and continues. It is a
  strict improvement — an aborting case was previously silent about every case
  after it — and it changes no case's own assertions. Each of the three mutation
  runs shows both the aborted earlier case and the intended `cg-row-<n>:` line.
- **Task 5, the per-tool split, re-confirmed by reading both constants**:
  `skill-lint.py`'s `CG_ROW_TOKENS` is now the seven members
  `("cg-row-1:", "cg-row-2:", "cg-row-3:", "cg-row-5:", "cg-row-6:", "cg-row-7:",
  "cg-row-8:")` and `gc.py`'s is still `("cg-row-4:",)`. Neither holds eight; the
  eight-row reconciliation is the union of the two tools' printed tokens. Chunk 0
  task 2's falsifiability self-check still fails in **both** directions on a
  scratch copy: a ninth token with no case → `- cg-row-9: named in CG_ROW_TOKENS
  but no registered case ran it`; a registered `cg_check(9, …)` with the token
  absent → `- cg-row-9: ran as a registered case but is absent from
  CG_ROW_TOKENS`. Both self-tests exit 0 in the repo; the in-repo
  `skill-lint.py .` still prints `GEOMETRY: nested  swept-roots=2` and
  `OK: 25 file(s) clean`, and `gc.py --report --root .` is clean.
- **Observation — minted in Chunk 7 as `Q-IMPL-CONSUMERGEOMETRY-004`**
  (raised here with no id per §Conventions): the enumeration in REQ-PKG-CONSUMERGEOMETRY-001's table
  names row 5's site by a source expression, `print_population(root,
  default_suite_root())`, which this cycle's own Chunk 3 made stale. The row's
  *mutation* survived the drift, but a comparand table that quotes source text is
  a standing hazard — worth either a recorded decision to name sites by function
  rather than by expression, or a dated note on that row. It is recorded here
  rather than edited into the requirement, because exactly one implement task
  owns `docs/requirements/integration/packaging.md` (§CG-11) and it is not in
  this chunk.

### Chunk 5: The sweep forwards the token, and the disjoint invocation is repaired end to end
**Goal**: The token survives `gc.py`'s sweep, `gc.py` derives no geometry of its
own **against a decidable comparand**, and §CG-8's construction is green on both
tools.
**Depends on**: Chunk 4.
**Write scope**: `plugins/sdd/tools/gc.py`, `docs/spec/drift-sweep.md`,
`docs/ws/consumer-geometry/traceability.md`.
**Tasks**:
1. [x] [implement] `sweep_lint()` forwards the `GEOMETRY:` token **verbatim, on
   its own line**. Today it passes through only two-line finding pairs matching
   its finding regex plus the last non-empty line when it matches
   `^(OK|FAIL): `, discarding every other line, so an own-line token reaches
   nobody. It must **not** compute the token: the linter is the only process that
   knows its own roots, and a second derivation is a second thing to get wrong
   — traces to `drift-sweep.md` §3, `two-root-linter.md` §CG-6
2. [x] [implement] **The first recorded plan input: supply a decidable comparand
   for "`gc.py` derives no geometry of its own".** "Geometry-deriving expression"
   has no grep spelling — the same objection this delta raises against "the
   working tree" in the freeze item. **Cite the target by its text, not by a
   section number**: the criterion is `drift-sweep.md`'s acceptance bullet
   *"`gc.py` derives no geometry of its own"*, whose mechanism is that file's
   §3 (*`sweep_lint()` forwards the `GEOMETRY:` token verbatim*) — **not** §4,
   which is *`AGG_FIX` names a path that resolves*. The spec's own Open Item
   mis-cites §4, and an implementer sent there edits the wrong section. Restate
   that bullet, and its twin in `two-root-linter.md`'s acceptance box, as
   **both** halves, because either alone is weak: (a) a grep of `gc.py` for the
   enum literals `nested`/`equal`/`disjoint` and for `suite_contained` returning
   zero matches **outside the forwarding pass-through**, and (b) a **mutation**:
   compute the token inside `gc.py` and assert the sweep output carries a
   duplicate `GEOMETRY:` line. The mutation is run, not described. The
   `two-root-linter.md` half of this edit is deferred to Chunk 7 task 1, which
   already holds that file open — traces to `two-root-linter.md`
   §Consumer-Geometry Open Items item 1, `drift-sweep.md` §3 and its acceptance
   bullet *"`gc.py` derives no geometry of its own"*
3. [x] [implement] **Re-date `docs/spec/drift-sweep.md`'s `last_updated` in the
   same commit as task 2's edit — which is why it sits IMMEDIATELY AFTER it,
   before the two verify tasks that consume that edit.** Ordered this way because
   an implementer working in task order would otherwise commit task 2 first and
   could comply only by amending; Chunk 7 keeps its own pairing adjacent (t1 → t2)
   for the same reason. §CG-11(b)'s pairing discipline is not specific
   to the requirements corpus: this chunk edits an Approved spec, so the same
   rule applies — the date bump rides the content commit, never a later one, and
   is a date bump rather than a content change. Chunk 7 task 2 does the same for
   the specs it touches; naming it in both places is what keeps the discipline
   from being read as Chunk 7's alone — traces to `two-root-linter.md` §CG-11(b)
4. [x] [verify] **The token survives the sweep.** In §CG-8's disjoint scratch
   construction, `gc.py --report` output contains a line beginning `GEOMETRY: `,
   forwarded verbatim on its own line; it contains none today, and **removing the
   forwarding returns it to none** — mutation run — traces to
   `two-root-linter.md` §Acceptance Criteria
5. [x] [verify] **The disjoint invocation is repaired end to end.** In §CG-8's
   construction the far `skill-lint.py` prints `GEOMETRY: nested`, raises no
   `[structure] skills/ directory not found` finding, and reports a non-zero
   swept-file count — it prints that finding and `FAIL: 1 finding(s)` today
   (Chunk 0 task 4), so the assertion is red before and green after, and
   **reverting the derivation returns it to red**. In the same construction the
   far `gc.py --report --root "$REPO"` raises **no** `[structure]` finding where
   it raises exactly one today, asserted **on the finding set** (decidable under
   both landing orders) rather than on the token; reverting `lint_command()`
   makes the finding reappear — traces to `two-root-linter.md` §CG-8,
   §Acceptance Criteria
6. [x] [verify] Re-run the §CG-8 construction's nested control: the in-repo
   `skill-lint.py` is unchanged at `GEOMETRY: nested` and its run-time-derived
   file count. **No assertion is made about the committed hook set's
   *geometry***, deliberately — every `.pre-commit-config.yaml` entry runs an
   in-repo copy, so every one is already nested and none can be left on the
   degraded default, and an assertion over them would describe a state that
   cannot occur. **This declines a geometry assertion only**: the hook set's
   byte-**identity** across the cycle is a different claim with a different
   comparand and is asserted at Chunk 8 task 2. The two must not be conflated,
   and declining the first is not declining the second — traces to
   `two-root-linter.md` §CG-8, `pre-commit.md` §Consumer-Geometry Amendment
**Entry criteria**: Chunk 4 exit criteria met.
**Exit criteria**: Both self-tests exit 0; §CG-8's construction green on both
tools with the reverting mutations run; the geometry-derivation criterion has a
decidable comparand in `drift-sweep.md` with its mutation demonstrated;
`drift-sweep.md`'s `last_updated` re-dated in the same commit as that edit. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

**Notes** (Chunk 5, 2026-09-22):

- **Task 1 — the forwarding, and where it prints.** `sweep_lint()` gained one
  branch in its line loop: a literal `lines[i].startswith("GEOMETRY: ")` test
  that stores the line **as an opaque string** in `self.forwarded_geometry`
  (last one wins, so one sweep forwards one token). `run()` prints it on its own
  line immediately before the summary — the position the linter emits it in. It
  is not a finding: it never enters `self.findings`, carries no severity and is
  not counted in the summary's `N`, which is §Finding Shape and Summary's
  contract left intact. Nothing in `gc.py` parses, rebuilds or reasons about the
  token's contents.
- **Tasks 2 and 3 pair.** The restated acceptance bullet in
  `docs/spec/drift-sweep.md` and that file's `last_updated` bump to 2026-09-22
  are a single edit pair, made together and (by §CG-11(b)'s pairing discipline,
  which is not specific to the requirements corpus) belonging in one commit.
  This leaf does not commit; the pairing is recorded here so the orchestrator's
  commit carries both.
- **Task 2 — what was cited, and what was not.** The target was cited **by its
  text** — the acceptance bullet *"`gc.py` derives no geometry of its own"* —
  and its mechanism named as `drift-sweep.md` §3 (`sweep_lint()` forwards the
  token). The spec's own Open Item mis-cites §4 (`AGG_FIX` names a path that
  resolves), which is a different criterion; §4 was not touched. The
  `two-root-linter.md` twin of this restatement is **owed to Chunk 7 task 1**,
  which already holds that file open.
- **Task 2 — both halves, the mutation run.** Half (a), the grep
  `grep -nE '\bsuite_contained\b|\b(nested|equal|disjoint)\b'
  plugins/sdd/tools/gc.py` ignoring comment lines, returns exactly two matches,
  both inside the forwarding pass-through: the row-4 self-test assertions that
  compare `cg4_geometry(...)`'s return — a string lifted verbatim off a linter
  run — against `"GEOMETRY: nested"` / `"GEOMETRY: disjoint"`. Zero matches
  compute a member from path comparison, containment or root equality. Half (b),
  the mutation, was **run** on a `$TMPDIR` scratch copy: deriving the member in
  `gc.py` from the corpus/suite roots and emitting a second token made the far
  `gc.py --report --root "$REPO"` output carry a **duplicate** `GEOMETRY:` line
  (count 1 → 2); the unmutated control gives exactly 1.
- **Task 4 — the token survives the sweep, both directions.** Before the change
  the far `gc.py --report --root "$REPO"` carried **zero** `GEOMETRY: ` lines;
  after it, exactly one, verbatim and on its own line. Deleting the pass-through
  branch on a scratch copy returned the count to zero.
- **Task 5 — end to end, and one provisional observation with no id.** Far
  `skill-lint.py "$REPO"`: `GEOMETRY: nested  swept-roots=2`, no `[structure]`
  finding, `OK: 25 file(s) clean` (non-zero swept count). Reverting the tier-2
  derivation in `Linter.__init__` on a scratch copy returns it to red —
  `GEOMETRY: disjoint  swept-roots=1`, the `[structure] skills/ directory not
  found` finding, and `FAIL: 1 finding(s), 0 warning(s) — NOTHING SWEPT`. Far
  `gc.py --report --root "$REPO"`: **zero** `[structure]` findings, asserted on
  the finding set. **Observation — minted in Chunk 7 as
  `Q-IMPL-CONSUMERGEOMETRY-005` (raised here with no id, per §Conventions):** under the landing
  order actually taken, reverting `lint_command()`'s suite-root pass-through
  **alone** leaves the finding set empty — the pass-through is inert when no
  `--suite-root` is supplied, so §CG-8's construction is repaired by the
  linter's tier-2 derivation, not by the pass-through. Reverting the derivation
  (with the pass-through already reverted) makes exactly one `[structure]`
  finding reappear. The plan's clause is decidable **on the finding set** under
  both landing orders, as written; only the attribution of the repair differs,
  and it is recorded here rather than left implied. Note also that the forwarded
  `GEOMETRY:` line is still present in the mutated run (reading `disjoint`) —
  forwarding is independent of geometry, which is the "forwards, never computes"
  property observed directly.
- **Task 6 — the nested control.** In-repo `python3
  plugins/sdd/tools/skill-lint.py .` is unchanged at `GEOMETRY: nested
  swept-roots=2` with `OK: 25 file(s) clean`, the count derived at run time and
  not pinned as a literal. **No assertion is made about the committed hook set's
  geometry**, deliberately — every `.pre-commit-config.yaml` entry runs an
  in-repo copy, so every one is already nested. The hook set's byte-identity is
  a different claim with a different comparand and is Chunk 8 task 2's; the two
  are not conflated.
- **Chunk close.** `python3 plugins/sdd/tools/skill-lint.py --self-test` and
  `python3 plugins/sdd/tools/gc.py --self-test` both exit 0. `python3
  plugins/sdd/tools/gc.py --report --root .` is `OK: 9 sweep(s) clean, 1
  warning(s), 34 info` — the one warning is `[traceability-aggregate]`, expected
  and **not** this leaf's to clear: per plan D4 the aggregate is regenerated by
  the orchestrator as post-gate bookkeeping and appears in no chunk's write
  scope. No `[traceability-rowdrop]` finding, so the filled rows still parse at
  six cells.

---

### Chunk 6: The bundled `orchestrate/tools/` removal and every record it falsifies
**Goal**: `plugins/sdd/skills/orchestrate/tools/` is gone, the consumer-unreachable
strings resolve, and every falsified record is corrected **in its own disposition
class**. This is the chunk the write-scope rules of §CG-11 were written for.
**Depends on**: Chunk 5.
**Write scope** — declared exhaustively, because half of it is a departure from
the v4 ownership rule:
- *Shipped plugin surface*: `plugins/sdd/skills/orchestrate/tools/` (removal),
  `plugins/sdd/skills/orchestrate/references/drift-sweep.md` (class A — **a
  shipped plugin file, not a docs record**),
  `plugins/sdd/skills/orchestrate/USAGE.md`,
  `plugins/sdd/skills/orchestrate/references/telemetry.md`,
  `plugins/sdd/tools/gc.py` (the `AGG_FIX` string).
- *This repo's shared specs* (class A): `docs/spec/two-root-linter.md` (the
  `skills/orchestrate/tools/` prose only — see **D3**), `docs/spec/pre-commit.md`,
  `docs/spec/marketplace-packaging.md`.
- *Cross-workstream, class (C) — corrected in place, as data*:
  `docs/ws/marketplace/traceability.md`.
- *Cross-workstream, class (B) — appended dated note only, never a rewrite*:
  `docs/ws/marketplace/verification.md`, `docs/ws/packaging/verification.md`,
  `docs/ws/packaging/baseline.md`, `docs/ws/packaging/plan.md`.
- *Own*: `docs/ws/consumer-geometry/traceability.md`.
- **Excluded, and not a defect**: `docs/ws/consumer-geometry/kickoff.md` and the
  two `docs/research/` records — stated exemptions, not falsified records.
- **Not in scope**: `docs/requirements/traceability.md` (**D4** — the
  orchestrator regenerates it), `docs/requirements/integration/packaging.md`
  (Chunk 7 owns it, exclusively).
**Tasks**:
1. [x] [implement] Remove `plugins/sdd/skills/orchestrate/tools/` — both files,
   each byte-identical to its `plugins/sdd/tools/` counterpart, reached by no
   invocation that works — traces to REQ-PKG-CONSUMERGEOMETRY-005,
   `marketplace-packaging.md` §The removal
2. [x] [implement] **Class A — make each live artifact true in place.** The file
   set is **read from the disposition table at run time**, not from a literal
   list here, so a row added without correcting its file is red. Covers the
   shipped `references/drift-sweep.md:36` citation of the directory's existence
   and `docs/spec/two-root-linter.md` §8's prose restated in the past tense
   against the removal (§CG-9 row 3).
   **Newly sized at repair iteration 2 — `marketplace-packaging.md:181`, §Tools
   live prose.** *"the bundled population is whatever `skills/*/tools/*.py`
   derives to at run time, and every check over it derives the same way"* is a
   **live assertion that a bundled population is derived**, which task 1's
   removal falsifies. It is unfenced and lies **before** the `:611` amendment
   heading, so neither residual-grep exemption reaches it. It is ordinary class
   (A) live prose — not a Q-IMPL record — so it is made true in place the
   ordinary way. Neither the spec nor this plan's first draft sized it; it is
   named here rather than left to the derived set alone.
   **Both of the spec's named Q-IMPL class-(A) sites, each with its specified
   shape.** These two are named because for them "make true in place" is
   under-specified, and the rule is narrower: **a Q-IMPL Decision or Context
   sentence is made true by re-tensing it and appending an inline dated clause,
   never by changing what was decided or what it was decided against.**
   - `docs/spec/marketplace-packaging.md:567` — Q-IMPL-MARKETPLACE-029's
     **Decision** text, today *"delete the bundled
     `skills/orchestrate/tools/skill-lint.py`, restore `tools/gc.py` to its
     rename-chunk-close content"*. The decision text is **untouched**; it gains
     the inline dated clause the spec spells out, saying only that its object is
     gone — *"(that directory was itself removed on 2026-09-21 under
     REQ-PKG-CONSUMERGEOMETRY-005; the instruction stands as the record of what
     this Q-IMPL decided)"*. The first draft carried this site only as
     "marketplace-packaging.md's restoration instruction", with no id, no line
     and no shape; the reason it gave for naming the `pre-commit.md` site applies
     to this one verbatim.
   - `docs/spec/pre-commit.md:277` — Q-IMPL-MARKETPLACE-019's **Context**
     sentence (*"`skills/orchestrate/tools/gc.py` and
     `skills/orchestrate/tools/telemetry.py` do not exist at the
     rename-chunk-close sha"*), re-tensed with the same inline dated clause. The
     recorded context is **not** rewritten and the Q-IMPL's **decision** is
     unaffected — only its context sentence is — and the match is made
     **whitespace-normalised**, because the sentence spans a line break.
   **The escape hatch, carried from the spec rather than left implicit.** If the
   implementer finds a site where re-tensing plus a dated clause cannot be done
   **without altering what was decided**, that site is handled as **class (B)** —
   original preserved, dated note appended beneath — and the departure is
   **recorded as a deviation** in this chunk's notes. Silently rewriting a
   decision is not an option in either direction. Without this route an
   implementer who hits the case has only two bad choices.
   **The derived set carries one stated carve-out (B2/D4).** The disposition
   table marks `docs/requirements/traceability.md` class **(C)**, and this chunk
   is forbidden to touch it. That is not an omission and it does not leave the
   assertion red under a correct implementation: the aggregate's class-(C) row is
   discharged by the **orchestrator's post-gate regeneration** from the
   per-workstream source row task 4 corrects, per §CG-11 rule 2 — regenerating it
   here would be a violation even if the output were right. So this task derives
   its set as **the table minus the aggregate**, and records that subtraction with
   its reason, so a reader sees a carve-out rather than a missed row. The
   aggregate's correctness is evaluated at the gate, by the diff of
   REQ-PKG-CONSUMERGEOMETRY-005 acceptance 4 — traces to
   REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2, `two-root-linter.md` §CG-9,
   §CG-11 rule 2, `pre-commit.md` §Consumer-Geometry Acceptance Criteria (first
   box)
3. [x] [implement] **Class B — appended dated notes, cross-workstream.** For each
   file the table marks **B**, append a
   `[Superseded 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-005: the bundled copy was
   removed; this observation was true at <that cycle's sha>]` note **within three
   lines of each falsified sentence**, where `<that cycle's sha>` is **`29febe6`**
   for `docs/ws/marketplace/verification.md` and **`0bdb076`** for the two
   `docs/ws/packaging/` records (§Conventions §Named shas — resolved from git
   history so no implementer guesses), and leave every original sentence exactly
   as that cycle wrote it. `docs/ws/packaging/plan.md` is named in no earlier
   draft of the requirement and is easy to miss — it is a falsified record with
   two occurrences. **Asserted by `git diff` over the correction commit alone** —
   never an open-ended diff against a later `HEAD` — showing insertions only and
   zero deletions; a `trailing-whitespace`/`end-of-file-fixer` deletion is a hook
   artefact, re-assert with those staged separately — traces to
   REQ-PKG-CONSUMERGEOMETRY-005 acceptance 3, `marketplace-packaging.md` §The
   three disposition classes
4. [x] [implement] **Class C — the per-workstream source row, corrected in place
   as data.** `docs/ws/marketplace/traceability.md:56` (the REQ-PKG-MARKETPLACE-006
   row naming both bundled paths). Per **D4** the leaf does **not** regenerate
   `docs/requirements/traceability.md`; it asserts that file's current row
   row — **identified by requirement id, never by line number: the aggregate is
   orchestrator-regenerated and its numbering moves** (the wrong literals `:317`
   and `:318` stood here until repair iteration 3; the rows are in fact at `:323`
   and `:324` today, which is exactly why the id is the identifier and the line is
   not) — by **reading** the row whose first cell is `REQ-PKG-MARKETPLACE-006`,
   and records the reading. **The comparand is explicit: the corrected per-ws
   Evidence cell and the aggregate's Evidence cell for that id must be
   character-for-character identical**, asserted by comparing the two cell strings
   directly, not left to follow from the regeneration — -005 acceptance 4 states
   that identity as a requirement, and a reading that merely records the
   aggregate's text cannot detect the two drifting apart. A leaf that regenerates is
   a violation even when its output is correct — traces to
   `two-root-linter.md` §CG-11 rule 2, REQ-PKG-CONSUMERGEOMETRY-005 acceptance 4
5. [x] [implement] **The dead REQ-PKG-MARKETPLACE-007 comparand**, the *other*
   row in the same file: `docs/ws/marketplace/traceability.md:57` carries the
   pinned blob-sha form and no `3ddfdb3 HEAD` spelling; its aggregate twin — the
   row whose first cell is `REQ-PKG-MARKETPLACE-007`, **found by id, not by
   line** — is likewise asserted by reading, not by regenerating. Two different rows,
   two different corrections — traces to REQ-PKG-CONSUMERGEOMETRY-005
   acceptance 4, `marketplace-packaging.md` §The dead … comparand
6. [x] [implement] **The spec-side freeze repin.**
   `docs/spec/marketplace-packaging.md`'s freeze item asserts
   REQ-PKG-MARKETPLACE-007's source freeze against "the working tree", with an
   accepted alternative naming `HEAD`; both leave the right endpoint unpinned, so
   the item turns red at the next gate **not because the freeze was violated but
   because it is evaluated outside its own window**. Repin to the packaging
   cycle's end sha `0bdb076`, asserted **on that named item** and never as a
   file-wide grep (`HEAD` occurs there in unrelated contexts, and "the working
   tree" has no grep spelling at all) — traces to `two-root-linter.md` §CG-7,
   `marketplace-packaging.md` §The dead … comparand
7. [x] [implement] **The consumer-unreachable strings, the same family.**
   `gc.py`'s `AGG_FIX` (`run tools/gc.py --fix …`, a path that resolves for
   nobody but a pre-move in-repo operator) and the six bare `python3
   tools/telemetry.py` sites in `orchestrate` (`USAGE.md` ×3,
   `references/telemetry.md` ×3) name a path that exists after the correction,
   asserted by **resolving each named path at run time, from the repository
   root** — traces to REQ-PKG-CONSUMERGEOMETRY-005 acceptance 7,
   `marketplace-packaging.md` §Consumer-unreachable strings
8. [x] [verify] **The second half of that box, which the resolve half does not
   reach: REQ-PKG-MARKETPLACE-007's binding is untouched.** Re-run the -007
   acceptance the correction could break — **no telemetry invocation under
   `plugins/sdd/skills/` passes a file path beginning with a skill or plugin
   directory, asserted by grep**. Any repair that moves the script path by *also*
   giving the tool a plugin-relative `--file` argument makes this half red, and
   that is precisely the construction that distinguishes the decided spelling
   from the one -007 forbids. Sized as its own task because it fails in a
   different direction from the resolve half and a single task would hide which
   one broke — traces to `marketplace-packaging.md` §Consumer-Geometry Acceptance
   Criteria ("The corrected strings resolve, and -007's binding is untouched"),
   REQ-PKG-MARKETPLACE-007 unchanged
9. [x] [implement] **The consumer residue is recorded, not closed.** The
   `OPEN:` in `docs/spec/marketplace-packaging.md` — *no spelling of a skill-body
   tool invocation resolves for a consumer of the installed plugin* — **survives
   this chunk with its blocking constraint named** (an attested skill-body
   expansion for the plugin root, or a requirement authorising another
   mechanism; neither owned by any artifact in this cycle). The corrected
   telemetry sites resolve **in this repository, from the repository root**,
   which is all acceptance 7 asks, and they resolve for **no consumer of the
   installed plugin**. Deleting the `OPEN:` while the six sites still resolve
   only here would make the record claim a closure that did not happen — in the
   one cycle about consumers. This is a reviewer check, not a tool one, and it is
   a task rather than a note so that task 7's correction cannot silently take the
   `OPEN:` with it — traces to `marketplace-packaging.md` §Consumer-Geometry
   Acceptance Criteria ("The consumer residue is recorded, not closed")
10. [x] [implement] **Neither spec-checklist assertion survives — one by
   *excision*, one by *retirement*. These are different operations on two
   different items and neither substitutes for the other.** Stated in the
   two-part shape §The shape every string criterion in this delta takes fixes,
   because the amendment writes the glob into this very file, so a file-wide grep
   would be decided by this cycle's own prose.
   **Primary, by named site.**
   **(i) — excision; the item survives.** (Two upstreams — `docs/requirements/index.md`
   and the disposition table — still call this item `:364`; the measured location
   is `:366`. The plan uses `:366` and asserts on the **named item**, not the
   line, so the stale upstream costs nothing; noted so the next reader does not
   re-measure it. The same staleness affects the REQ-PKG-MARKETPLACE-007 freeze
   item, now `:368`.) The item at `:366` no longer derives a
   bundled population: its **first clause only** — *"every file matching
   `skills/*/tools/*.py` paired with the suite-root file of the same basename …
   and for each derived pair `cmp` exits 0 and `test ! -L` succeeds"* — is
   excised. **The item stays.** Its remaining clauses are
   REQ-PKG-MARKETPLACE-006's **surviving half** and its only live pin, so this
   task asserts **positively that both are still present after the edit**: the
   `git log --follow` clause resolving every post-change
   `plugins/sdd/tools/*.py` to its pre-change history, and the two-sided loss
   check whose sides are spelled separately across the move commit. This is the
   same clause-level excision §CG-9 specifies for
   `two-root-linter.md:522-523`. **Retiring this item whole destroys the
   surviving loss check** and fails the criterion just as surely as leaving the
   clause in place does.
   **(ii) — retirement; the item goes.** The item at `:367`, asserting that a
   drift-sweep invocation resolves to the bundled copy, is **retired whole**: it
   rests entirely on the superseded duplication clause. Leaving (i)'s clause in
   place instead makes it pass **vacuously** after the removal — a checklist item
   reading green while checking an empty set. Doing either one alone fails this.
   **Secondary, residual — and it is not "returns zero". The bound is DERIVED,
   never enumerated.** A run-time grep of `docs/spec/marketplace-packaging.md`
   for the glob returns matches **only** where an exemption covers them, with the
   stated bound that every occurrence inside the amendment is a **citation of a
   site to be corrected**, never an assertion that a bundled population is
   derived. The exemptions: (a) a fenced code block; (b) any line **at or after**
   that file's own `## Consumer-Geometry Amendment` heading, whose line number is
   **read at run time**, never written down; (c) the Q-IMPL-MARKETPLACE-028
   reverted-record line, per this task's disposition below. There is **no
   exemption for the item-(i) line**: after the excision that line contains no
   glob match, so asserting it positively — *the item-(i) line matches the glob
   zero times after the edit* — is the check, and an exemption there would let
   the grep pass with the deriving clause still in place, which is the vacuity
   the two-part shape exists to prevent. **Every remaining match is a
   site this chunk must have corrected.** Both partitions are computed from the
   heading's line number at run time — a literal enumeration is wrong the moment
   anything moves, which is exactly how the first two drafts of this criterion
   went wrong, once with a zero target and once with an incomplete list.
   **Zero is unreachable against a correct implementation**, because the
   amendment carries the glob after its own heading (a table cell, which cannot
   be fenced, among others); a zero target is discharged only by deleting the
   amendment's own citations, the outcome the exemption exists to prevent.
   **`marketplace-packaging.md:546` — the one match no exemption covers and no
   correction reaches, dispositioned here rather than left silent.** It sits
   inside **Q-IMPL-MARKETPLACE-028's Decision** text, in an entry whose
   **Status** is `REVERTED 2026-09-21` and which is kept *"as the record of a
   decision that was made and then withdrawn"*. Note it is a **different site
   from the `:567` Q-IMPL-MARKETPLACE-029 Decision** task 2 names — the spec names `:567` and
   measures `:546`, and conflating them loses one of the two. **Disposition: a
   reverted record is narrative, not an assertion about the present tree**, so it
   takes the Q-IMPL rule in its class-(B)-shaped form — the Decision text is
   preserved verbatim and a dated clause is appended recording that the
   directory the glob would have derived over was removed on 2026-09-21. It is
   therefore a **stated third exemption** to the residual grep, on the same
   footing as this cycle's own kickoff and the research records in the
   disposition table: listed so the grep has a stated exemption rather than an
   unexplained failure.

   **The exemption is written into the Approved spec by this task, not held in
   the plan alone (added at the plan cap gate, 2026-09-22).** The Approved
   criterion at `marketplace-packaging.md` §Consumer-Geometry Acceptance Criteria
   ("Neither spec-checklist assertion survives", *Secondary, residual*) grants
   **two** exemptions; REQ-PKG-CONSUMERGEOMETRY-005 acceptance 5's own literal
   still reads "returns zero matches". Leaving the third exemption in the plan
   alone makes requirement, spec and plan say three different things, and only
   the plan's version is satisfiable. This task therefore **also amends that
   residual bullet** to name the third exemption — `docs/spec/marketplace-packaging.md`
   is already in this chunk's write scope — and the matching
   `[Updated: 2026-09-21c]` clause beneath REQ-PKG-CONSUMERGEOMETRY-005 is landed
   by **Chunk 7 task 1(c)**, which owns the requirements-corpus write. That is
   §CG-4's own rule for reinterpreting an Approved literal, applied to the
   literal this cycle is reinterpreting. Amending the spec without the
   requirements note, or the note without the spec, leaves the three-way split in
   place and fails this task — traces to REQ-PKG-CONSUMERGEOMETRY-005 acceptance 5,
   `marketplace-packaging.md` §Consumer-Geometry Acceptance Criteria ("Neither
   spec-checklist assertion survives — one by excision, one by retirement")
11. [x] [verify] **The two per-file residual greps, run in the chunk that owns
   the corrections** — they operate on `docs/spec/*.md` and are therefore in the
   one region task 9's `excluding docs/` sweep cannot see, so neither has an
   owner otherwise. (a) `docs/spec/marketplace-packaging.md`: the secondary half
   of task 8, above. (b) `docs/spec/pre-commit.md`, in its **derived** form, with
   no baseline count written down — a written count there has already been wrong
   twice: *exactly one* line matching `skills/orchestrate/tools` lies **before**
   that file's `## Consumer-Geometry Amendment` heading (the
   Q-IMPL-MARKETPLACE-019 sentence), every other match lies after it, and the
   correction of task 2 is what takes that one to **zero**; both halves computed
   from the heading's line number at run time, both exempting fenced blocks and
   the amendment's own citations — traces to `pre-commit.md` §Consumer-Geometry
   Acceptance Criteria (second box), `marketplace-packaging.md` §The shape every
   string criterion in this delta takes
12. [x] [verify] **Gone**, and the residual grep: `test ! -d
   plugins/sdd/skills/orchestrate/tools` succeeds, and a run-time grep for
   `orchestrate/tools` over the repository **excluding `docs/`** returns zero,
   where it returns one today at the shipped `drift-sweep.md:36`. Removing the
   directory but leaving that citation makes this red. The class (B) files are
   **deliberately outside this grep's scope** — they keep their originals by
   policy and hold 21 unfenced occurrences between them — traces to
   REQ-PKG-CONSUMERGEOMETRY-005 acceptance 1, 2
13. [x] [verify] **No invocation regressed *by the removal*.** `python3
   plugins/sdd/tools/gc.py --report --root .` and the commit gate's hooks raise
   no new finding and exit with the same status as before the removal. Evaluated
   **across the removal commit alone**, never across the cycle. Note this command
   is already **nested** — the in-repo copy's `default_suite_root()` is
   `<repo>/plugins/sdd` — so there is no degraded default here to pin
   — traces to REQ-PKG-CONSUMERGEOMETRY-005 acceptance 6
**Entry criteria**: Chunk 5 exit criteria met. **OC2, asserted not assumed**: the
REQ-PKG-MARKETPLACE-006 amendment is already on disk — grep
`docs/requirements/integration/packaging.md` for the `[Updated: 2026-09-21b —`
note beneath that id and confirm it carries the duplication-clause supersession
**before** task 1 runs. If it is absent, this chunk does not start.
**Exit criteria**: Directory gone; the excluding-`docs/` grep returns zero; the
two per-file `docs/spec/` residual greps green **in their exempted form**, never
against a zero target; item (i) excised **with both surviving clauses asserted
present** and item (ii) retired whole; every class A/C file in the derived set
(table minus the aggregate, carve-out recorded) made true, and every class B file
carrying its note with an insertion-only diff over the correction commit; freeze
item repinned on its named item; every corrected string resolves from the
repository root **and** -007's no-plugin-relative-`--file` grep re-run green; the
`OPEN:` consumer residue still present with its blocking constraint named;
`gc.py --report` unregressed; the aggregate **read and recorded, not
regenerated**. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.



**Notes** (Chunk 6):
- **Class taken by each cross-workstream write.** `docs/ws/marketplace/traceability.md`
  — **class (C)**, corrected in place as data, both rows (`:56` -006 Evidence,
  `:57` -007 comparand). `docs/ws/marketplace/verification.md`,
  `docs/ws/packaging/verification.md`, `docs/ws/packaging/baseline.md` and
  `docs/ws/packaging/plan.md` — **class (B)**, appended dated notes only, 20
  notes, `git diff --numstat` insertion-only with zero deletions in all four.
  No original sentence was rewritten in any of them.
- **The escape hatch was not needed** (task 2). Both spec-named Q-IMPL class (A)
  sites took the prescribed re-tense-plus-inline-dated-clause form without
  altering what was decided, so no site was demoted to class (B) and there is no
  deviation to record on that route.
- **Observation — minted in Chunk 7 as `Q-IMPL-CONSUMERGEOMETRY-006`**
  (raised here with no id per §Conventions). The spec
  prescribes the Q-IMPL-MARKETPLACE-029 Decision's corrected text **verbatim**
  and that text **keeps** the literal `skills/orchestrate/tools/skill-lint.py`,
  at `marketplace-packaging.md:578`, which lies before that file's amendment
  heading and is not fenced. REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2's
  *secondary* half, read as a bare per-file `skills/orchestrate/tools` grep over
  every class (A) file, is therefore unsatisfiable for this one file **against
  the spec's own prescription**. The plan assigns no such grep to this file
  (task 11 assigns the glob grep here and the `skills/orchestrate/tools` grep to
  `pre-commit.md`), so nothing in this chunk is red; but requirement, spec and
  plan do not say the same thing about that file, which is the same three-way
  split task 10's second half closes for the *glob* exemption. The same applies
  to the -006 Evidence cell in `docs/ws/marketplace/traceability.md`, whose
  replacement text the spec also specifies verbatim including the string. Raised
  here with no id per §Conventions; a durable entry belongs in Chunk 7.
- **Two note placements could not be made within three lines beneath their
  sentence, and are recorded rather than silently stretched.** (i)
  `docs/ws/packaging/baseline.md:63-64` sit inside a **fenced** inventory
  listing, where no note can be inserted without editing the fence; the note is
  placed at the first position outside it and names the two lines explicitly.
  (ii) `docs/ws/packaging/plan.md:1185` has no sentence boundary at a line end
  within three lines beneath it, so its note is placed as a **banner one line
  above** the paragraph — the shape `docs/ws/marketplace/verification.md`
  already uses for its own supersession banners. Both are within three lines of
  the falsified sentence in the sense the criterion measures; neither touches an
  original. (iii) `docs/ws/marketplace/verification.md:710` is the one note
  placed four lines beneath, for the same reason — lines 711-713 all end
  mid-sentence and splicing there would cut a sentence in half.
- **Pre-removal byte identity is a statement about the entry sha, not HEAD.**
  `telemetry.py` was byte-identical to `plugins/sdd/tools/telemetry.py` at
  removal; `gc.py` was **not**, because Chunks 1-5 of this cycle edited the
  suite-root copy and nothing propagated to the bundled one. That divergence is
  itself evidence for the removal — an unreachable copy that nothing keeps in
  sync — and it is why REQ-PKG-MARKETPLACE-006's duplication evidence is dated
  as historical in the corrected traceability cell rather than re-asserted.
- **The derived class (A)/(C) set is the disposition table minus the aggregate.**
  `docs/requirements/traceability.md` is marked (C) in the table and is
  deliberately **not** in this chunk's write scope (plan **D4**): its row is
  discharged by the orchestrator's post-gate regeneration from the per-ws source
  this chunk corrected. The subtraction is recorded here so a reader sees a
  carve-out rather than a missed row. This leaf **read** both aggregate rows by
  requirement id and compared the cell strings directly; it regenerated nothing.
- **Task 13, attributed rather than asserted.** `gc.py --report --root .` was
  `exit 0 / OK: 9 sweep(s) clean, 0 warning(s), 34 info` before any edit and is
  `exit 0 / … 1 warning(s), 34 info` after the whole chunk. The one new line is
  `WARN docs/requirements/traceability.md: [traceability-aggregate] aggregate
  differs from regenerate(docs/ws/*/traceability.md)`, and it is **not caused by
  the removal**. Demonstrated, not argued: a `cp -R` scratch corpus under
  `$TMPDIR` carrying the removal **and every other edit of this chunk**, with
  only the three traceability files restored to their `HEAD` content, sweeps
  `exit 0 / OK: 9 sweep(s) clean, 0 warning(s), 34 info` — identical to the
  pre-removal baseline. The warning is therefore wholly attributable to the
  class (C) source-row corrections of tasks 4 and 5, which plan **D4** routes to
  the orchestrator's post-gate regeneration. Across the removal alone,
  acceptance 6 holds. The committed hook is unaffected either way: `gc.py
  --fast` does not run the aggregate rule and is `exit 0 / 0 warning(s)` in the
  live tree.


---

### Chunk 7: The requirements notes, the spec corrections, and the summary-line pins
**Goal**: The single implement-stage write of the shared requirements corpus
lands, with all three notes; the two `--suite-root` absence sentences are
corrected without deleting the clauses that survive; and every summary-line pin
is read rather than assumed.
**Depends on**: Chunk 6.
**Write scope**: `docs/requirements/integration/packaging.md` — **this is the
only implement-stage task in the whole plan that declares this path; an
unexpected touch of it from any other chunk is a `SCOPE: VIOLATION`** —
`docs/spec/two-root-linter.md`, `docs/spec/skill-lint-v5.md`,
`docs/requirements/integration/skill-lint.md` — **see the note below**, this is a
second requirements-corpus file and its status is stated rather than inferred —
`docs/ws/consumer-geometry/traceability.md`.
**`docs/requirements/integration/skill-lint.md`: conditional, authorised, and
outside §CG-11's machinery — said plainly, because the plan's own loud
"exactly one implement-stage task declares the requirements corpus" would
otherwise read as contradicted by this line.** Three statements:
(i) **§CG-11's exclusivity clause names `docs/requirements/integration/packaging.md`
and no other file.** It is an exclusivity over *that path*, not over the
requirements corpus as a whole, so this declaration does not breach it and the
"exactly one" claim is unchanged — it was always a claim about one file.
(ii) **The write is conditional and is expected not to occur.** Task 7 reads
`:276` and amends it **only if** it is end-anchored; `N` is non-zero on this
corpus and the suffix is additive and conditional, so the expectation is that no
edit is needed. The authorisation is REQ-PKG-CONSUMERGEOMETRY-004 via
`skill-lint-v5.md`'s first acceptance box ("any that is end-anchored is
amended"), not §CG-11.
(iii) **If the write does occur it takes the corpus rules anyway**: an appended
dated note, never a rewrite of an approved sentence, and the §CG-11(b)
same-commit pairing applies to it exactly as to `packaging.md` — the pairing
rule keys on *bumping the requirements corpus's `last_updated`*, which this
would do, not on which file did it. Task 2 already lands that pairing for this
chunk, so a conditional edit here rides the same commit.
**Tasks**:
1. [x] [implement] **The one requirements-corpus write. Appended dated
   `[Updated:]` notes only — never a rewrite of an approved sentence**, because
   rewriting makes the record disagree with the commit that approved it. Three
   notes, all under `[Updated: 2026-09-21c — …]`:
   (a) beneath **REQ-PKG-CONSUMERGEOMETRY-002** — its consumer bullet cites -006
   acceptances 3 and 5 as asserting "both directions"; they assert the
   **negative** direction only, and the positive is §CG-4's new acceptance 6;
   (b) beneath **REQ-PKG-CONSUMERGEOMETRY-004** — §CG-6 re-reads two of its
   literals: `suite-rows-root=<path>` from "the suite root **as given**" to the
   **effective** root of §CG-3's three tiers, and "emitted by **every** run" as
   "iff the run prints an `OK:`/`FAIL:` summary", which excludes `--self-test`.
   **This note is not optional**: §CG-4 establishes this cycle's own rule for a
   spec that reinterprets an Approved literal, and applying it to -002 while
   exempting -004 reproduces, one requirement away, the defect this delta
   diagnoses;
   (c) the requirement-side halves paired with §CG-2's and §CG-9's corrections,
   beneath **REQ-PKG-CONSUMERGEOMETRY-003** and **-005**.
   Asserted by grepping the file for a `[Updated: 2026-09-21c` note under each of
   the named ids, so a note omitted is red rather than silently absent
   — traces to `two-root-linter.md` §CG-11, §CG-4, §CG-6
2. [x] [implement] **The staleness pairing, decided in §CG-11(b) and executed
   here**: the commit carrying task 1's notes also carries the spec and plan
   touches it pairs with, so no intermediate commit exists in which the corpus is
   newer than the artifacts that trace it. Where the note must land alone, this
   task re-dates the affected specs' `last_updated` in that same commit — a date
   bump, not a content change. Asserted by `git show --name-only` over the
   note-bearing commit. A `[stale-chain]` finding raised between the two events is
   an artefact of the split and is informational, not routed at DONE — traces to
   `two-root-linter.md` §CG-11(b)
3. [x] [implement] **Both absence sentences in `two-root-linter.md`, and they are
   not the same edit** (§CG-9 rows 1–2):
   `:83`→`:89` (§2's *"`--suite-root` is **deferred**, not adopted — it mitigates
   the one unclosed vendored-cache case"*) is **re-scoped in place** — the
   deferral held for the `packaging` cycle and is superseded here, in the shape
   §2's other superseded claims carry; `:516-517`→`:522-523` is an **excision of
   the middle clause only** — *"the argparse surface exposes no `--suite-root`"*
   dies, while the `no-suite-rules` grep clause and the `suite_rules=False`
   containment clause **stand** (REQ-PKG-PACKAGING-003 leg (i)). **The two halves
   fail in opposite directions**: leaving either sentence standing makes the
   first half red, deleting the checklist item wholesale makes the second half
   red — which is what stops an implementer resolving this with a delete
   — traces to `two-root-linter.md` §CG-2, §CG-9,
   REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4
4. [x] [implement] Land the `two-root-linter.md` half of Chunk 5 task 2's
   decidable comparand for "`gc.py` derives no geometry of its own", so the spec
   and its `drift-sweep.md` twin say the same thing — traces to
   `two-root-linter.md` §Consumer-Geometry Open Items item 1
5. [x] [implement] **The second recorded plan input: all three
   `skill-lint-v5.md` summary-line pins name the dead `python3
   tools/sdd-skill-lint.py` path, not one.** Measured at `:128`, `:428`,
   `:453-454`. The spec repairs only the `:454` pin, and the stated reason — that
   the implementer is already reading that line for the end-anchoring check —
   applies identically to the other two, which the same criterion also requires
   them to read. **Decision: repair all three in that read**, which is the
   cheaper of the two options the open item offers and leaves no recorded
   inaccuracy behind — traces to `two-root-linter.md` §Consumer-Geometry Open
   Items item 2
6. [x] [implement] **The two remaining count/aggregation inconsistencies**, sized
   here rather than recorded as debt, because this chunk already holds
   `two-root-linter.md` open: §CG-9 opens "**Two** edits … are owed" above a
   three-row table (its closing criterion already says three), and the
   summary-line pins are counted three ways across two files (three in
   `skill-lint-v5.md`, four including the requirements-side twin). Correct both
   counts to agree with their tables. The third item of that triple — the §CG-6
   four-assertion checkbox — is discharged by Chunk 1 task 4 and Chunk 3 task 4
   — traces to `two-root-linter.md` §Consumer-Geometry Open Items item 3
7. [x] [verify] **The summary-line pins are confirmed unanchored — no count
   written**; the set is the `OK: N file(s) clean` pins **derived by grep**, not
   listed. The three in `docs/spec/skill-lint-v5.md` (`:127`,`:427`,`:452`
   pre-amendment; `:129`,`:429`,`:454` after — **the content, not the number,
   identifies them**) and `docs/requirements/integration/skill-lint.md:276` are
   each read and confirmed to state a prefix or substring match rather than an
   end-anchored one. `N` is non-zero on this corpus and the suffix is additive
   and conditional, so none is **expected** to need amendment — the check is that
   the expectation is **verified rather than assumed**. Any that is end-anchored
   is amended under REQ-PKG-CONSUMERGEOMETRY-004.
   **In the same read, the corrected paths must RESOLVE — the falsifier for task
   5's own repair, which nothing else in the plan supplies.** Each dead
   `python3 tools/sdd-skill-lint.py` invocation task 5 corrects to `python3
   plugins/sdd/tools/skill-lint.py` is asserted **by resolving the named path at
   run time**. This is red before the change and green after: the dead spelling
   resolves under **neither** the pre- nor the post-move layout today, which is
   what makes that half falsifiable; a still-unresolvable path fails it. Without
   this, task 5 is a repair whose completion nothing can falsify — kickoff
   constraint 2 — and Chunk 6 task 7's run-time resolution covers only `AGG_FIX`
   and the six telemetry sites, not these. Recorded as an observation with its
   command — traces to `skill-lint-v5.md` §Consumer-Geometry Acceptance Criteria
   (first box, both halves), `two-root-linter.md` §CG-6, §Acceptance Criteria
8. [x] [verify] **The SECONDARY half of REQ-PKG-CONSUMERGEOMETRY-003 acceptance
   4 — the residual absence grep — which task 3 does not reach.** Task 3 lands
   the two *named* sentences; this is the file-wide claim behind them, and it is
   the third two-part criterion in this delta (Chunk 6 tasks 10 and 11 hold the
   other two; this chunk holds the only write scope for
   `docs/spec/two-root-linter.md`, so it has to be here or nowhere). Run it in
   the **same exempted, run-time-derived shape** as Chunk 6 task 11, never as a
   bare "returns zero": `docs/spec/two-root-linter.md` contains **no other
   sentence asserting the absence of a `--suite-root` surface**, outside (a) a
   fenced code block and (b) that file's own `## Consumer-Geometry Amendment`
   section — whose heading line number is **read at run time**, never written
   down — with the stated bound that every occurrence inside the amendment is a
   **citation made in order to retire the sentence** (it quotes both, in prose
   and in §CG-9's table, and a table cell cannot be fenced), never a fresh
   assertion of absence. Landing the surface and leaving either sentence standing
   makes the primary half red; this half catches a third sentence neither
   requirement names — traces to REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4
   secondary half, `two-root-linter.md` §Acceptance Criteria ("Both absence
   sentences … Secondary, residual grep")
9. [x] [verify] **The requirements-corpus writes are scoped, enumerated and
   dated**: exactly one implement-stage task declares
   `docs/requirements/integration/packaging.md` (this chunk's task 1) and exactly
   one verify-stage task declares it (Chunk 9 task 2); **no other task in either
   stage does**, asserted by reading this plan's write-scope declarations. All
   three notes present under their named ids. The note-bearing commit carries
   either its paired spec/plan touches or the `last_updated` re-dating, asserted
   by `git show --name-only`. A third task touching that path, a missing -004
   note, or a commit with neither pairing nor re-dating, makes this red — traces
   to `two-root-linter.md` §Acceptance Criteria (first box), §CG-11
**Entry criteria**: Chunk 6 exit criteria met.
**Exit criteria**: Three dated notes present under their named ids with no
approved sentence rewritten; both absence sentences corrected, both surviving
clauses present, **and the residual absence grep green in its exempted
run-time-derived form**; all three `skill-lint-v5.md` dead-path pins repaired; the
end-anchoring check recorded with its command; the two count inconsistencies
corrected; exactly one implement task in the plan declares the packaging
requirements file. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

**Notes**:
- **Task 1 — the one requirements-corpus write, four appended dated notes, zero
  rewrites.** `docs/requirements/integration/packaging.md` gained four
  `[Updated: 2026-09-21c — …]` notes, each placed immediately above its
  requirement's closing `[Priority: must]` line, which is the placement every
  existing note in that file uses. **Four, not three**: task 1(c) names two ids
  (-003 and -005), so the three lettered notes are four blocks. Under
  **-002**, the cited direction corrected — -006 acceptances 3 and 5 assert the
  **negative** direction only, and §CG-4's acceptance 6 (confirmed present,
  `two-root-linter.md:964`) is the positive one. Under **-003**, the `:516-517`
  → `:522-523` and `:83` → `:89` citations reconciled and the *re-scope in
  place, do not delete* shape of the §2 edit stated. Under **-004**, §CG-6's
  re-reading of `suite-rows-root=<path>` (as given → **effective**) and of
  "every run" (→ iff an `OK:`/`FAIL:` summary is printed, excluding
  `--self-test`), plus the superseded two-site pin measurement.
  **The -004 note was treated as non-optional**, on the plan's own ground:
  applying §CG-4's rule to -002 and exempting -004 would reproduce the diagnosed
  defect one requirement away. Under **-005**, the requirement-side half of
  Chunk 6 task 10's third grep exemption. Asserted by
  `grep -c 'Updated: 2026-09-21c' → 4`, one under each named id. No approved
  sentence was altered; every note is an insertion.
- **Task 2 — the pairing, and what it could not reach.** The note-bearing edit
  bumps `docs/requirements/integration/packaging.md` `last_updated` to
  `2026-09-22`, so the two specs this chunk edits —
  `docs/spec/two-root-linter.md` and `docs/spec/skill-lint-v5.md` — were
  re-dated to `2026-09-22` in the **same** working tree, a date bump and not a
  content change. This leaf does not commit; the pairing is recorded here so
  the orchestrator's single commit carries both. **One spec could not be
  paired**: `docs/spec/marketplace-packaging.md` (`2026-09-21`) traces PKG
  requirements and is **not in this chunk's write scope**, so any
  `[stale-chain]` finding naming it is the split artefact task 2 declares
  informational, not routed at DONE. `drift-sweep.md` was already `2026-09-22`
  and needed nothing. `docs/requirements/index.md` was **not** touched — it is
  outside this chunk's write scope and no criterion here reads it.
- **Task 3 — both halves, in opposite directions, and neither by deletion.**
  `:89` (§2's deferral bullet) was **re-scoped in place**: the `--suite-root`
  half is marked superseded by REQ-PKG-CONSUMERGEOMETRY-003 (§CG-2) with the
  reason re-measured (the vendored-cache case is not one residual case but the
  geometry every consumer runs in), while the `--no-suite-rules` half is stated
  **untouched** as REQ-PKG-PACKAGING-003 leg (i). `:522-523` lost its **middle
  clause only**. Both surviving clauses asserted **positively present**, not
  inferred from the absence of a diff: `no-suite-rules` occurs 7 times in the
  file and `suite_rules=False` 11 times, and the surviving item now reads
  *"…is empty and every `suite_rules=False` site is inside the self-test"*.
- **Task 4 — the twin, said the same way rather than a second way.**
  `two-root-linter.md`'s §Consumer-Geometry Acceptance Criteria bullet now
  carries both halves of `drift-sweep.md` §4's comparand — the enumerated-permit
  grep and the run duplicate-token mutation — including the explicit note that
  either half alone is weak. The two files no longer state one criterion two
  ways.
- **Task 5 / task 7 — three pins repaired, four pins read, none end-anchored,
  and one file deliberately not written.** The pin set was **derived by grep**
  (`grep -n 'OK: N file(s) clean'`), never listed: `skill-lint-v5.md:129, :429,
  :454` and `docs/requirements/integration/skill-lint.md:276`. Each states a
  *matches* / *prints* relation against the substring with **no** anchor,
  terminator or "exactly" — all four confirmed **not** end-anchored, so **none**
  needed amendment and `docs/requirements/integration/skill-lint.md` was **not
  edited**. That is the outcome the write-scope note predicted (`N` is non-zero
  here and the `— NOTHING SWEPT` suffix is additive and conditional), verified
  rather than assumed. **All three** `skill-lint-v5.md` pin invocations were
  corrected from `python3 tools/sdd-skill-lint.py` to `python3
  plugins/sdd/tools/skill-lint.py` — the plan's recorded input, confirmed: the
  spec repaired only the `:454` pin while its stated reason applies to all
  three. **The falsifier was run**: `test -f plugins/sdd/tools/skill-lint.py`
  succeeds; the pre-change spelling resolves under neither the pre-move
  (`tools/skill-lint.py`) nor the post-move layout, which is what made that
  half red before the change. The remaining `tools/sdd-skill-lint.py`
  occurrences in that file (`:28, :145, :426, :435, :436, :453, :489, :692,
  :701, :742`) are **not** pin invocations and are explicitly out of scope by
  `skill-lint-v5.md:701`; `:453` in particular carries no `python3` and so is
  not one of the three invocations the criterion names — recorded so the
  omission reads as a decision.
- **Task 6 — both counts now agree with their tables.** §CG-9's opening
  sentence reads **three** edits above its three-row table (its closing
  criterion already did). The summary-line pin count is settled once — three in
  `skill-lint-v5.md`, four including the requirements-side twin — and stated
  that way in `two-root-linter.md`'s Open Items resolution note and in
  REQ-PKG-CONSUMERGEOMETRY-004's dated note; the requirement's own "two named
  sites" literal is **re-read, never rewritten**, as a measurement superseded by
  a run-time grep. All three Open Items are closed by an appended
  `[Updated: 2026-09-21c]` block that leaves the raised text standing.
- **Task 8 — the residual absence grep, in its exempted run-time-derived
  shape.** The `## Consumer-Geometry Amendment` heading line number was **read
  at run time** (`:750` in the post-edit file) and never written into the check;
  fence spans were computed from the file. Outside a fence and **before** that
  heading, `docs/spec/two-root-linter.md` carries **zero** sentences asserting
  the absence of a `--suite-root` surface. Six occurrences sit at or after the
  heading, every one a **citation made in order to retire the sentence** —
  §CG-2's prose, §CG-9's table (a table cell cannot be fenced), and this
  chunk's own excision record. The check was red before task 3 (the `:89` and
  `:522-523` sentences) and is green after it.
- **Task 9 — write-scope exclusivity, read off this plan's declarations.**
  Parsing every `**Write scope**:` block in this file: exactly **one**
  implement-stage task declares `docs/requirements/integration/packaging.md`
  (this chunk's task 1) and exactly **one** verify-stage task declares it
  (Chunk 9 task 2). No third task in either stage does. All four notes are
  present under their named ids. The pairing half is task 2's, recorded above;
  `git show --name-only` is the orchestrator's to run over the commit this leaf
  does not make.
- **The six Q-IMPL entries this chunk owed are minted**, in
  `docs/spec/two-root-linter.md` under a new `## Consumer-Geometry
  Implementation Questions` section, each id and its `### Q-IMPL-…` heading
  written in the same edit so no `qimpl-undefined` finding can exist between
  them: **-001** the mirrored `cg` helpers (accept the duplication, recorded —
  `gc.py` invokes the linter as a subprocess and cannot import it), **-002** the
  `GEOMETRY:` token's one-per-summary property being structural only because
  `run()` is the sole emitter (keep every corpus summary inside `run()`),
  **-003** `print_population()`'s second tier-1 resolution (one resolution
  serves both paths; landed by Chunk 3), **-004** the comparand table that
  quotes a source expression (name sites by function, never rewrite the
  approved row), **-005** §CG-8's repair being attributable to tier 2 rather
  than to the inert `lint_command()` pass-through (the criterion is decidable
  under either landing order and is left as written), and **-006** Chunk 6's
  three-way split over Q-IMPL-MARKETPLACE-029's prescribed text (a stated
  exemption in all three places). Each carries `**Tier**`, a `**Spec
  reference**` naming a live heading of that file, `**Decision**` and
  `**Rationale**`. The corresponding Notes entries in Chunks 0, 1, 2, 4, 5 and 6
  were updated to name the id they were minted as, which also makes each entry
  *referenced* rather than defined-only. The Chunk 3 note about mutation runs on
  `$TMPDIR` scratch copies was **not** minted — it is a methodology record, not
  a Q-IMPL-shaped open decision, and §Conventions warns against inventing ids
  for observations that are not there.
- **Traceability.** The `Test` and `Implementation` **cells** of this
  workstream's existing rows for REQ-PKG-CONSUMERGEOMETRY-001 through -005 were
  filled. No row was appended, no seventh column added, and
  `docs/requirements/traceability.md` was not touched (plan **D4** — the
  orchestrator regenerates the aggregate).

---

### Chunk 8: Full-suite regression and gate integrity
**Goal**: Nothing in Chunks 0–7 regressed the nested case, the corpus sweep or
the commit gate.
**Depends on**: Chunk 7.
**Write scope**: `docs/ws/consumer-geometry/traceability.md` only. No production
file is edited in this chunk **by a task**; a finding here routes to a fix in its
owning chunk.
**The hook-write carve-out, stated because this is the chunk most exposed to
it.** Task 3 runs `pre-commit run --all-files`, and the committed hook set
includes `trailing-whitespace` and `end-of-file-fixer`, which **write**. A file
those hooks rewrite here is a **hook artefact, not a task edit**, and is not a
`SCOPE: VIOLATION` — the same class Chunk 6 task 3 already anticipates for its
insertion-only diff. Two handling rules, in order: (i) prefer the read-only form,
`pre-commit run --all-files --show-diff-on-failure`, so a hook's rewrite surfaces
as a diff rather than as a write; (ii) if a rewrite does land, stage it
separately, record it in the chunk's notes as a hook artefact naming the hook and
the path, and re-assert. A rewrite that a hook did **not** produce is a real
violation and is treated as one.
**Tasks**:
1. [x] [verify] `python3 plugins/sdd/tools/skill-lint.py --self-test` and
   `python3 plugins/sdd/tools/gc.py --self-test` exit 0; both are still in the
   committed `.pre-commit-config.yaml` hook set, asserted **by parsing that
   file** — traces to REQ-PKG-CONSUMERGEOMETRY-001 acceptance 4
2. [x] [verify] **The committed hook set is byte-identical across the cycle** —
   a *different* assertion from task 1's presence check and from Chunk 5 task 6's
   deliberate declining, which is about **geometry**, not identity; the three
   must not be conflated. Asserted by `git diff` over
   `.pre-commit-config.yaml`'s hook entries **from this cycle's entry sha
   `3bac4af`** (§Conventions §Named shas), **except** for any change this delta
   explicitly authorises — of which there are **none**: no entry is added,
   removed or re-rooted by the consumer-geometry delta. Adding or re-rooting a
   hook under this delta makes this red — traces to `pre-commit.md`
   §Consumer-Geometry Acceptance Criteria (third box), REQ-PC-PACKAGING-001
   unchanged
3. [x] [verify] `pre-commit run --all-files` is green over the whole corpus,
   including both tools' self-tests, **green on the post-Chunk-7 tree** — the
   per-edit half of this claim is already carried by each chunk's own exit
   criteria and is not decidable by a single run here — traces to
   `pre-commit.md` §Consumer-Geometry Acceptance Criteria
4. [x] [verify] In-repo `python3 plugins/sdd/tools/skill-lint.py .` reports
   `GEOMETRY: nested` and its run-time-derived swept-file count; `python3
   plugins/sdd/tools/gc.py --report --root .` raises no new finding class
   — traces to `two-root-linter.md` §CG-8
5. [x] [verify] Re-run the §CG-8 disjoint construction end to end one final time
   on the post-Chunk-7 tree, so the repair is confirmed against the tree that
   ships and not only against the tree Chunk 5 closed on — traces to
   `two-root-linter.md` §CG-8
**Entry criteria**: Chunk 7 exit criteria met; all implement chunks closed.
**Exit criteria**: Both self-tests green and still hook entries rather than moved
to the run-explicitly set; the hook set byte-identical from `3bac4af`;
`pre-commit run --all-files` green; the nested case and the disjoint construction
both green on the shipping tree. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

**Notes** (Chunk 8, 2026-09-22):
- **Task 1 — presence, not identity.** `python3 plugins/sdd/tools/skill-lint.py
  --self-test` → `SELF-TEST OK: …`, exit 0; `python3 plugins/sdd/tools/gc.py
  --self-test` → `SELF-TEST OK: …`, exit 0. Both are still **hook entries**,
  asserted by parsing `.pre-commit-config.yaml`: under `repo: local`, ids
  `skill-lint-self-test` (entry `python3 plugins/sdd/tools/skill-lint.py
  --self-test`) and `drift-sweep-self-test` (entry `python3
  plugins/sdd/tools/gc.py --self-test`), alongside `drift-sweep` and
  `skill-lint`, plus the four upstream hygiene hooks — eight entries. Parsed
  textually rather than with PyYAML, which is not importable in this
  environment; the parse reads the `- id:` / `entry:` / `- repo:` / `rev:` lines,
  which is the whole hook set's identity surface.
- **Task 2 — byte-identity from the entry sha, a different comparand from task
  1's and from Chunk 5 task 6's.** `git diff 3bac4af HEAD --
  .pre-commit-config.yaml` is **empty**, and the blob is the same object at all
  three points: `3bac4af:.pre-commit-config.yaml`, `HEAD:.pre-commit-config.yaml`
  and `git hash-object .pre-commit-config.yaml` all give
  `689d689eef7c759dc538d0b4cf5b9e9fb19f744a`. The extracted entry lists at the
  two shas diff clean. No entry added, removed or re-rooted — which is what this
  delta authorises, none. Chunk 5 task 6's declining is about **geometry** and is
  not cited here.
- **Task 3 — the gate, and the one thing this sandbox cannot assert.** `pre-commit
  run --all-files --show-diff-on-failure`: `drift sweep (fast profile)` Passed,
  `skill linter` Passed, `skill linter self-test` Passed, `drift sweep self-test`
  Passed, `trim trailing whitespace` Passed, **`fix end of files` Failed**,
  `check yaml` Passed, `check json` Passed. The failure is not a finding: it is
  the known sandbox write-denial, verbatim —
  `PermissionError: [Errno 1] Operation not permitted: '.claude/settings.json'`
  raised from `end_of_file_fixer.py:61` at `open(filename, 'rb+')` — on a file
  wholly outside this cycle's write scope, which must not be touched; precedent
  in `docs/ws/marketplace/verification.md`. **Coverage recovered with `--files`**:
  `pre-commit run end-of-file-fixer --files <every tracked file but that one>`
  (208 paths) → **Passed**; `end-of-file-fixer` and `trailing-whitespace` over
  the **23** files this cycle changed (`git diff --name-only --diff-filter=d
  3bac4af HEAD`) → both **Passed**. `.claude/settings.json` already ends in byte
  `0a`, so even the un-assertable file would pass on content; what is refused is
  the hook's read-write open, not the check. **What can be asserted**: seven of
  eight hooks green over the whole corpus, and the eighth green over every
  tracked file except one whose content independently satisfies it. **What
  cannot**: a single green `pre-commit run --all-files` process in this
  environment.
- **No hook artefact landed.** The read-only form was preferred per handling rule
  (i), and `git status --short` was empty after every hook run, so rule (ii)
  never fired. The only modified path in this chunk is
  `docs/ws/consumer-geometry/traceability.md`, this chunk's declared write scope,
  plus this section of the plan.
- **Task 4 — the nested case and the sweep, both unregressed.** In-repo
  `python3 plugins/sdd/tools/skill-lint.py .` → `GEOMETRY: nested
  swept-roots=2  suite-rows-root=<repo>/plugins/sdd` then `OK: 25 file(s) clean`,
  exit 0 — the count read off the run, never pinned as a literal. `python3
  plugins/sdd/tools/gc.py --report --root .` → exit 0, `OK: 9 sweep(s) clean, 0
  warning(s), 39 info`; `--fast --root .` → exit 0, `OK: 3 sweep(s) clean, 0
  warning(s), 29 info`. **No new finding class**: the only classes present are
  `[qimpl-unreferenced]` and `[stale-chain]`, both pre-existing, and the set of
  rule-class literals in `gc.py` is unchanged from `3bac4af`. Two `[stale-chain]`
  *instances* are new — `marketplace-packaging.md` and `pre-commit.md` now older
  than `docs/requirements/integration/packaging.md` (2026-09-22), which Chunk 7
  wrote — but they are new instances of an old class, informational, and not
  routed at DONE; recorded here so the verify stage sees them rather than
  discovers them.
- **Task 5 — §CG-8 re-run end to end on the shipping tree.** `cp -R
  plugins/sdd "$TMPDIR/cg/far"` (the installed cache never touched), then the far
  `skill-lint.py "$REPO"` → `GEOMETRY: nested  swept-roots=2
  suite-rows-root=<repo>/plugins/sdd`, `OK: 25 file(s) clean`, exit 0, **no
  `[structure] skills/ directory not found` finding**, non-zero swept count; the
  far `gc.py --report --root "$REPO"` → exit 0, **zero** `[structure]` findings
  passed through, same forwarded `GEOMETRY:` line, `OK: 9 sweep(s) clean, 0
  warning(s), 39 info` — byte-equal to the in-repo run. The repair is therefore
  confirmed against the tree that ships, not only against the tree Chunk 5 closed
  on.
- **No regression found**, so nothing is routed back to an owning chunk. No
  production file was edited by any task in this chunk.


---

### Chunk 9: Verify stage — the desk check, the sha back-fill, and the observation
**Goal**: The two verify-stage obligations that no implement task can discharge,
each with its own task, and the machine-dependent observation recorded as an
observation.
**Depends on**: Chunk 8.
**Write scope** — **two disjoint writers, deliberately not merged**:
- task 1, 3, 4: `docs/ws/consumer-geometry/verification.md`,
  `docs/ws/consumer-geometry/traceability.md`.
- **task 2 alone**: `docs/requirements/integration/packaging.md` — the **one**
  verify-stage write of that path, in that file and no other. It is a separately
  scoped writer from Chunk 7 task 1 and must not be folded into it.
**Tasks**:
1. [ ] [verify] **OC3 — the desk-check half of the count equality.** Parse the
   `cg-row-<n>:` tokens from REQ-PKG-CONSUMERGEOMETRY-001's enumeration **table**
   and compare them **as a set** against the tokens `skill-lint.py --self-test`
   and `gc.py --self-test` print; record **both sets and their difference** in
   `docs/ws/consumer-geometry/verification.md`. Adding a row to the table without
   adding its token makes the difference non-empty; adding a token without a row
   fails it symmetrically. The reconciler is the verify stage rather than a gate
   because `docs/` is outside the shipped plugin, so no shipped tool may read
   that table. **This is the half the in-tool assertion cannot reach** — the
   tool's constant-vs-registered check proves the constant and the cases agree
   with *each other*, not that either agrees with the requirement. The count
   "eight" is informational prose and is **never** a literal this comparison is
   evaluated against — traces to `two-root-linter.md` §CG-7, §Acceptance
   Criteria, REQ-PKG-CONSUMERGEOMETRY-001 acceptance 3
2. [ ] [verify] **The REQ-PKG-PACKAGING-003 sha back-fill — its own task, its own
   write scope.** That requirement's Approved `[Updated: 2026-09-21]` note says
   its clause (ii) "is retired from the close of the `consumer-geometry` implement
   stage — whose sha the verify stage back-fills into this note". Write that close
   sha into the note in place of the future-event phrasing, in
   `docs/requirements/integration/packaging.md` and no other file. Nothing else in
   the delta names, sizes or schedules this, and an exclusivity clause that did
   not know about it would read the back-fill as a `SCOPE: VIOLATION` — traces to
   `two-root-linter.md` §CG-11 (Verify stage)
3. [ ] [verify] **Machine-dependent observation, not gating.** On a machine with
   the plugin installed, run the cache's own `skill-lint.py` against this
   repository: it reports `GEOMETRY: nested` after the change where it reports
   the `[structure]` finding today. Recorded in `verification.md` **as an
   observation with its command, never as a gate assertion** — it depends on an
   installed cache whose presence and version no gate can guarantee, and the
   cache is a read-only measurement surface — traces to
   `two-root-linter.md` §Acceptance Criteria (last box), kickoff constraint 1
4. [ ] [verify] **The box-walk is a final completeness check, not the owner of
   any box.** Every box of the five specs' §Consumer-Geometry Acceptance Criteria
   is recorded here as pass/fail with the command that decided it, including the
   four separately-checkable §CG-6 assertions (Chunk 1 task 4 (a), (b), (d) and
   Chunk 3 task 4 (c)) recorded as **four** results, not one. **Each box is
   discharged by a named task in the chunk that holds the write scope to repair
   it** — Chunks 1, 2, 6, 7 and 8 — and this task asserts that every box has such
   a task and that each returned a result, rather than evaluating any box for the
   first time. The distinction is load-bearing: this task runs *after* every
   implement chunk has closed, and the scopes that could repair a red box
   (`docs/spec/marketplace-packaging.md`, `docs/spec/pre-commit.md`,
   `plugins/sdd/tools/skill-lint.py`) exist only in those earlier chunks, so a
   box first evaluated here is a **loop-back, not a fix** — the same
   uncollectable-debt rule OC3 rests on. A box with no owning task found here is
   a plan defect and routes to `sdd:replan`, not to an ad-hoc repair — traces to
   all five specs' §Consumer-Geometry Acceptance Criteria
**Entry criteria**: Chunk 8 exit criteria met; the implement stage's close sha
exists (task 2 needs it).
**Exit criteria**: `verification.md` carries both token sets and their
difference, the four split §CG-6 results, and the machine-dependent observation;
the sha back-fill landed by a single, separately scoped task. The `Test` and `Implementation` cells of this workstream's rows for the requirements this chunk advanced are filled in `docs/ws/consumer-geometry/traceability.md` (§Conventions), never as new rows and never a seventh column.

## Requirement → Chunk Coverage

Re-derived per **acceptance** rather than per requirement, because a
requirement's acceptances land in different chunks and the one-row-per-
requirement form hid three unsized halves. Re-checked at repair iteration 2,
which added four more owners.

| Requirement / acceptance | Chunks · tasks |
|---|---|
| -001 acc. 1–2 (eight rows, each mutation run) | 0 (reporting surface), 1 t3 (row 3), 2 t5–6 (row 4), 3 t3 (rows 1–2), 4 t1–4 (rows 5–8) |
| -001 acc. 3 (desk check, verify-owned — OC3) | 9 t1 |
| -001 acc. 4 (self-tests green, still hooks) | 0 t5, 4 t5, 8 t1 |
| -001 acc. 5 (freeze repin, spec side) | 6 t6 |
| `two-root-linter.md` box: this file's **three §CG-9 correction sites** are landed (`:89`, `:522-523`, `:366`) | 6 t2 (`:366`), 7 t3 (`:89`, `:522-523`) |
| -002 acc. 1–3 (per-geometry split, Option B enforced, C12.1 unmodified) | 3 t5–6; citation note in 7 t1(a) |
| -003 acc. 1–2 (surface exists, discoverable, reaches the binding) — linter half | 2 t1, t7 |
| -003 acc. 1 **sweep half** (`gc.py --help` + `Gc(...)` keyword, both mutations) | 2 t8 |
| -003 acc. 3 (both `gc.py` branches) | 2 t3–4, t6 |
| -003 acc. 4 **primary** (both absence sentences; surviving clauses survive) | 7 t3; **leg (i) greps** 2 t10 |
| -003 acc. 4 **secondary** (residual absence grep, exempted + run-time-derived) | 7 t8 |
| -004 acc. 1, 4, 5 (`— NOTHING SWEPT`, three sites) | 1 t2, t5 |
| -004 acc. 2–3 + negative (enum, `suite-rows-root=`, unconditional) | 1 t1, t4(a)(b)(d), 3 t4(c) |
| -004 (token is not a finding; count invariance **by mutation**) | 1 t7 |
| -004 forwarding clause + decidable comparand | 5 t1–3, 7 t4 |
| -004 interaction note (four summary-line pins, end-anchoring read) | 7 t5, t7 |
| `skill-lint-v5.md` box 1 **resolve half** (corrected paths resolve at run time) | 7 t7 |
| -005 acc. 1 (gone) | 6 t1, t12 |
| -005 acc. 2 class A — live prose, incl. `marketplace-packaging.md:181` | 6 t2 |
| -005 acc. 2 class A — the two named Q-IMPL sites (`:567`, `pre-commit.md:277`) + escape hatch | 6 t2 |
| -005 acc. 2 class C (derived set **minus the aggregate**, carve-out recorded) | 6 t4; aggregate at the gate (D4) |
| -005 acc. 2 secondary residual greps (derived bounds; `:546` exemption) | 6 t11, 6 t12 |
| -005 acc. 3 class B (notes, insertion-only diff) | 6 t3 |
| -005 acc. 4 (dead -007 comparand, both sides) | 6 t5; aggregate diff at the **gate** (D4) |
| -005 acc. 5 (excision **and** retirement, two-part) | 6 t10, t11 |
| -005 acc. 6 (no invocation regressed by the removal) | 6 t13 |
| -005 acc. 7 resolve half | 6 t7 |
| -005 acc. 7 **-007-untouched half** | 6 t8 |
| -005 acc. 7 **residue recorded, not closed** | 6 t9; §Recorded Plan Inputs |
| -006 acc. 1–2 (end-to-end disjoint repair) | 3 t1, 5 t4 |
| -006 acc. 3, 5 (both negative directions) | 3 t5 |
| -006 acc. 4 (nested not regressed) | 3 t8, 8 t3 |
| -006 acc. 6 (positive direction, four ways — added by the spec) | 3 t2, t4 |
| -006 (constructor-resolution pin; all paths agree) | 3 t7 |
| -006 closing note (machine-dependent observation) | 9 t3 |
| §CG-11 box 1 (requirements-corpus writes scoped, enumerated, dated; pairing) | 7 t1, t2, t9 |
| REQ-PKG-PACKAGING-003 (sha back-fill) | 9 t2 |
| REQ-PKG-PACKAGING-003 leg (i) preserved | 2 t10 |
| REQ-PKG-MARKETPLACE-006 (amendment precedes removal, OC2; surviving clauses) | 6 entry criterion; 6 t10(i) |
| REQ-PKG-MARKETPLACE-007 (binding untouched) | 6 t8 |
| REQ-PC-PACKAGING-001 (hook set byte-identical from `3bac4af`) | 8 t2 |
| Completeness check over all five specs' boxes | 9 t4 (**checker, not owner** — see that task) |

## Recorded Plan Inputs (specs cap gate, 2026-09-21)

Six were recorded as named plan inputs. Each is sized as a task or carries the
reason it is not:

| Input | Disposition |
|---|---|
| A decidable comparand for "`gc.py` derives no geometry of its own" | **Sized**: Chunk 5 task 2 (`drift-sweep.md` half, cited by bullet text — the spec's Open Item mis-cites §4; the bullet's mechanism is §3 — with the mutation run) + Chunk 7 task 4 (`two-root-linter.md` twin). Both halves adopted — grep alone is weak, mutation alone leaves the prose undecidable |
| All three `skill-lint-v5.md` summary-line pins name the dead `tools/sdd-skill-lint.py` path | **Sized**: Chunk 7 task 5. Decision: repair all three in the one read, not restate the sentence |
| The §CG-6 acceptance box bundles four assertions into one checkbox | **Sized**: split into four, Chunk 1 task 4 (a)(b)(d) and Chunk 3 task 4 (c); recorded as four results at Chunk 9 task 4 |
| §CG-9 opens "**Two** edits … are owed" above a three-row table | **Sized**: Chunk 7 task 6 |
| The summary-line pins are counted three ways across two files | **Sized**: Chunk 7 task 6 |
| `OPEN:` the 40 `REQUIRED` rows have no binding fixture in any geometry | **Not sized, and this is the recorded reason**: §CG-5 declines the rebinding on scope, because it would land a behaviour change with **no fixture able to falsify it** — the defect class this delta exists to close. The closure is a fixture, and the requirement authorising one is owned by no artifact in this cycle. Carried forward, not silently dropped |
| `OPEN:` whether `--suite-root` should be honoured from an environment variable | **Not sized**: not adopted and not proposed; §2's "no other root-resolution mechanism is introduced" stands and §CG-3's three tiers are exhaustive. Recorded so its absence reads as a decision |
| `OPEN:` **no spelling of a skill-body tool invocation resolves for a consumer of the installed plugin** (`marketplace-packaging.md`) | **Not sized — and it carries a task anyway**: the closure is blocked on either an attested skill-body expansion for the plugin root, or a requirement authorising another mechanism, and neither is owned by any artifact in this cycle. What *is* sized is that the `OPEN:` **survives** with its blocking constraint named (Chunk 6 task 9), because the corrected telemetry sites satisfy acceptance 7 by resolving in this repository while resolving for no consumer — and in the one cycle about consumers, deleting the `OPEN:` would claim a closure that did not happen |

## Replan Triggers

Each names the condition, the observation that detects it, and where it routes.

1. **Tiers 2/3 cannot be resolved inside `Linter.__init__` without breaking an
   existing self-test.** *Detected at*: Chunk 3 task 1 — the constructor change
   turns a pre-existing case red that is not one of the eight enumerated rows.
   *Why it is terminal rather than a fix*: §CG-1's "`gc.py` inherits the
   derivation for free" is true **only** under constructor resolution, and §CG-3
   pins it explicitly; moving it to `main()` freezes `gc.py`'s `-c` shim on
   tier 3 permanently. So the workaround falsifies two Approved spec statements
   at once. *Routes to*: `sdd:replan`, re-entering at **specs** — §CG-1 and §CG-3
   must be re-decided together, not patched.
2. **The `GEOMETRY:` token's forwarding through `sweep_lint()` proves infeasible
   without restructuring `gc.py`'s passthrough parser.** *Detected at*: Chunk 5
   task 1 — the token cannot be forwarded on its own line without changing which
   lines the finding regex admits, i.e. without changing the sweep's finding
   output. *Why it is terminal*: -004's forwarding clause and -006 acceptance 2's
   "asserted on the finding set" both assume the sweep's finding behaviour is
   untouched; a restructure invalidates the comparand every Chunk 5 verify task
   uses. *Routes to*: `sdd:replan`, re-entering at **specs** (`drift-sweep.md` §3).
3. **The `orchestrate/tools/` removal falsifies more records than the six the
   disposition table enumerates.** *Detected at*: Chunk 6 task 12 — the
   excluding-`docs/` grep returns a match in a file the table does not name, or
   the class-A run-time grep finds a file outside the table. *Why it is
   terminal*: the table **is** the comparand (`REQ-PKG-CONSUMERGEOMETRY-005`
   states no count and derives every file set from it at run time), so an
   unlisted falsified record is a requirement-side gap, not an implementation
   one — and two earlier drafts of that requirement already got the set wrong.
   *Routes to*: `sdd:replan`, re-entering at **requirements** to amend the
   enumeration.
4. **Any enumerated mutation cannot be made to turn its own case red.** *Detected
   at*: any `cg-row-` task in Chunks 1–4 — the mutation is applied and run, the
   process turns red, but **no line beginning with that row's token appears**.
   *Why it is terminal*: this is exactly kickoff constraint 2 failing, and this
   cycle has had blocking findings at three stages that were criteria which could
   not fail. A task whose completion nothing can falsify is not done and is not
   closed by weakening the criterion. *Routes to*: `sdd:replan` if the row's
   binding is genuinely unobservable; otherwise a fix inside the chunk.
5. **The tier-2 derivation regresses the nested case.** *Detected at*: Chunk 3
   task 8 — in-repo `skill-lint.py .` reports a different geometry or a different
   swept-file count than Chunk 0 task 4 pinned. *Why it matters*: a live risk,
   since the in-repo copy's tier-2 candidate and its `default_suite_root()` are
   the same directory. *Routes to*: fix inside Chunk 3 (§CG-3's third condition
   exists to decline exactly this); replan only if the third condition cannot
   distinguish them.
6. **`FIX_LOOP_MAX` = 3, no extra-iteration authorisations** (kickoff constraint
   3). A stage that cannot close in three rounds routes to `sdd:replan`. Scope is
   open to what the work finds; rounds are not.

## Risks

- **One conjunct of tier 2's adoption test is individually unpinned (observed at
  Chunk 3's gate, 2026-09-22, by both the implementer and the verifier
  independently).** `derived_suite_root()` requires three conjuncts; removing
  `candidate.is_dir()` **alone** leaves the `(candidate/"skills").is_dir()` test
  guarding the same non-existent path, so no case goes red. Removing both
  together reds eight lines. So the conjunction is pinned and that single
  conjunct is not. This is a gap in the mutation set, not a defect in the
  implementation — but REQ-PKG-CONSUMERGEOMETRY-001's premise is that each named
  site has a mutation that turns it red, so it is recorded here rather than left
  to be rediscovered. Closing it needs a fixture whose corpus holds a
  `plugins/sdd` **file** (not a directory) with a `skills/` path that would
  otherwise resolve — the only shape where the two conjuncts disagree. Carried to
  the verify stage's box-walk as a known, argued gap.

- **Cold-reader load (raised at the plan cap gate, 2026-09-22; noted, not
  actioned).** §Conventions and several Chunk 6/7 task bodies are multi-paragraph
  prose carrying decisions. The decisions are findable and every one is traced,
  but extracting *the work* from them is harder than it should be, and the
  D-numbered decisions would read better lifted into a short table. Not a
  correctness finding and not restructured here: reshaping the plan's own
  presentation on the final iteration would churn the task numbering that Chunk 7
  task 9 parses mechanically, for no change to what any task asserts. Worth doing
  in the next plan this workstream writes.

- **Write-scope violation at the requirements corpus.** The single highest
  mechanical risk in the cycle: two tasks in two different stages write one file,
  and a third touch from anywhere is a `SCOPE: VIOLATION`. Mitigated by declaring
  both scopes explicitly (Chunk 7, Chunk 9 task 2) and by Chunk 7 task 9
  asserting the exclusivity against this plan's own declarations.
- **A leaf regenerating `docs/requirements/traceability.md`.** Correct output,
  still a violation — the aggregate's numbering moves and every other stage reads
  it. Mitigated by **D4** and by that path appearing in no chunk's write scope.
- **Mid-cycle staleness.** Chunk 7's requirements note bumps the corpus
  `last_updated` and can make these specs and this plan read as stale. Handled by
  §CG-11(b)'s same-commit pairing (Chunk 7 task 2); `[stale-chain]` is
  informational and not routed at DONE, so it blocks no gate either way.
- **Class (B) rewrites.** Four cross-workstream prose records are one careless
  edit away from a policy violation. The insertion-only `git diff` over the
  correction commit alone (Chunk 6 task 3) is what catches it, and the two halves
  of that acceptance fail in opposite directions by design.
- **A residual grep restated as "returns zero", or dropped for want of an
  owner.** **Four** criteria in this delta are two-part *because* the amendment
  writes the very string it retires into the file it retires it from; flattening
  any of them to a zero target makes it unreachable against a correct
  implementation and discharged only by deleting the amendment's own citations —
  the outcome the exemptions exist to prevent. This plan hit that trap twice, and
  each time in a different way: it reverted one criterion to a zero target
  (repaired at iteration 1), and it left the fourth — the `--suite-root` absence
  grep over `two-root-linter.md` — with **no owning task at all** while a count
  here claimed all of them were covered (repaired at iteration 3). The four are
  now owned: Chunk 6 tasks 10 and 11 (`marketplace-packaging.md`,
  `pre-commit.md`) and Chunk 7 task 8 (`two-root-linter.md`), all in the same
  exempted, run-time-derived shape. **The count in this bullet is itself the
  hazard it describes** — it was three when it should have been four — so a
  reader who changes the set changes this number with it.
- **Chunk 6 is not split, and that is a decision on the record — not an
  omission.** It is the largest chunk in the plan: thirteen tasks, about twelve
  declared paths, three disposition classes and two cross-workstream policies.
  The review proposed splitting it into a removal-plus-class-A chunk and a
  cross-workstream chunk joined by a dependency edge, and the reasoning was
  sound: **§Conventions' single-chain justification does not reach Chunk 6.**
  That argument is about overlapping edits to `skill-lint.py` and `gc.py`, and
  Chunk 6's writes are almost all docs; a split would have bought real isolation
  between the shipped-surface removal and the cross-workstream corrections.
  **Declined for this cycle** on timing rather than merit: restructuring the
  largest chunk on the final fix iteration risks more than it buys, and the
  per-chunk gate's write-scope check is the mechanism that would catch what the
  split was meant to prevent. **If Chunk 6 throws a `SCOPE: VIOLATION` at its
  gate, this is the first thing to reconsider** — the split is the prepared
  remedy, not a new idea to have under pressure.
- **Fixture A reuse for the -002 criterion.** §7 fixture A is defined as
  `suite_root = corpus_root/plugins/sdd`, so reusing its tree fires tier 2 and
  makes the criterion red against a correct implementation. Mitigated by the
  pinned `vendor/suite` spelling (Chunk 3 task 6).

## Open Questions

- ~~**Does the incremental population of the token constant (D1) satisfy the
  first recorded ordering constraint as its author intended?**~~ **RESOLVED at
  repair iteration 2, on the constraint's own text — D1 stands and no
  requirements amendment is needed.** `docs/requirements/index.md` states the
  constraint with its rationale attached: the fixtures land before the behaviour
  changes *"**so each change's reversion is observable at the moment it is
  made**"*. That rationale clause is **task-granular by construction** — "the
  moment it is made" is a per-change moment, not a cycle boundary — so the
  task-granular reading is the one the constraint's own wording carries. The
  cycle-granular reading, which would have put it in direct conflict with
  REQ-PKG-CONSUMERGEOMETRY-001 acceptance 4, is not what it says. Struck rather
  than deleted so the reasoning survives for a later reader.
- **Do rows 6–8 need any behaviour edit at all (D2)?** The guards are already
  present; only their *cases* are new. If the implement stage finds a geometry in
  which a guard is absent rather than present, that is a new finding, not a
  fixture task, and it widens Chunk 4.
- ~~**Which sha is "that cycle's sha" in the class (B) note text?**~~
  **RESOLVED at repair iteration 1, from git history rather than left to the
  implementer**: `docs/ws/packaging/*` takes the packaging cycle's end sha
  `0bdb076` (merge of PR #5); `docs/ws/marketplace/verification.md` takes the
  marketplace cycle's end sha **`29febe6`** (merge of PR #4). Both literals are in
  §Conventions §Named shas and Chunk 6 task 3 uses them directly.
