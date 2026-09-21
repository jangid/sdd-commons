---
workstream: packaging
status: planned
research_id: RS-PACKAGING-003
last_updated: 2026-09-21
---

# Implementation Plan: Packaging — the suite root move and the two-root linter

## Overview

This cycle moves the shipped suite (`skills/**`, `agents/**`, `tools/**`,
`.claude-plugin/plugin.json`) into `plugins/sdd/` and teaches `skill-lint.py` to
hold two roots — a **corpus root** (the operator's repository) and a **suite
root** (the shipped plugin). The move is the pivot: almost every acceptance
criterion in the 22 requirements is written as "evaluated after the move", or
spells a pre-move and a post-move side, and several cite a **pre-move sha**. The
plan therefore builds the whole two-root interface *before* the move, while the
two roots are still equal (case C geometry — the pre-change behaviour is the
regression comparand), lands the move as a **single identifiable commit**
(Chunk 5), and then repairs the spellings the move breaks and evaluates every
after-the-move criterion.

## Conventions

- **Task types**: `[implement]` produces code/text, `[spike]` produces findings,
  `[verify]` validates behaviour.
- **Chunk headers**: `### Chunk N: <name>`; `**Depends on**:` is the canonical
  dependency signal for implement-stage fan-out.
- **Pre-move / post-move**: tasks in Chunks 0–4 run against the repository root;
  tasks in Chunks 5–7 run against the moved tree. Chunk 5 is the boundary.
- Every task names the spec it traces to.
- **The two baselines are different objects — never conflate them.**
  - **pre-change baseline** — the repository at Chunk 0's HEAD, *before any task
    in this plan edits anything*. Chunk 0 task 1 pins its sha and captures the
    **finding set** of a pre-change single-root `skill-lint.py` run. It is the
    comparand for every *behavioural* comparison: REQ-PKG-PACKAGING-004's
    equal-roots finding-set comparison (C2.6) and REQ-LINT-PACKAGING-001's
    equal-roots set comparison (C1.7, C2.4).
  - **pre-move sha** — the **parent commit of the Chunk 5 move commit**. Chunks
    0–4 commit between the pre-change baseline and this sha, so the two are
    *not* the same commit. It is the comparand for every *tree-enumeration*
    criterion: REQ-PKG-PACKAGING-001's `git ls-tree` per-name membership (C5.5)
    and the `.py` loss check (C7.4).
  - Where a requirement's own text says "pre-move sha" but means the
    pre-change finding set, this plan uses the name above and says which.
- **Carried notes.** References of the form "carried note m1/M3/…" throughout
  are findings from **this cycle's specs-stage external review** (`sdd:review`
  over `docs/spec/` for workstream `packaging`, 2026-09-21), carried into the
  plan so they are discharged by a task rather than re-litigated. The review is
  ephemeral and is not an artifact on disk.
- **Length deviation (accepted).** This plan runs past `skills/plan/SKILL.md`
  §Step 5's ~300-line threshold for splitting into per-milestone files. The
  deviation is accepted deliberately: the chunk graph is a **single linear
  chain** (Chunk 0 → 7, one `Depends on` edge each), so splitting it into
  milestone files would add navigation cost and an index table without changing
  the sequence or enabling any parallelism. Single-milestone format is retained.

## Chunks

### Chunk 0: Baseline capture and the paired retired-filename removal
**Goal**: A pinned **pre-change baseline** exists to compare against, the one
change that must land before the `RETIRED_SCOPE_FILES` table is re-rooted is in,
and `CLAUDE.md`'s self-contradictory marker statement is reconciled — that
reconciliation belongs in this chunk because it must not ride on the move
commit, so the Goal names it rather than leaving task 3 unaccounted for.
**Depends on**: None.
**Tasks**:
1. [x] [implement] Capture the **pre-change baseline** as a scratch artifact the
   later verify tasks read: the current HEAD sha (recorded under the name
   `pre-change baseline`), `git ls-tree -r --name-only HEAD` restricted to
   `skills/`, `agents/`, `tools/`, `.claude-plugin/plugin.json`, and the full
   finding set of a pre-change single-root `skill-lint.py` run over the
   repository. This artifact is the comparand for the two **behavioural**
   comparisons only — REQ-PKG-PACKAGING-004's equal-roots finding-set
   comparison (C2.6) and REQ-LINT-PACKAGING-001's equal-roots set comparison
   (C1.7, C2.4). It is **not** the comparand for REQ-PKG-PACKAGING-001's
   per-name membership assertion: that cites the **pre-move sha**, the parent of
   the Chunk 5 move commit, derived at C5.5 as `git rev-parse <move commit>^`
   (§Conventions).
   **Explicit decision, recorded not silent:** REQ-PKG-PACKAGING-004 pins the
   comparand at `a1ab5ba`. This plan **substitutes** the Chunk 0 HEAD sha for
   it, and records the substitution here rather than silently: `a1ab5ba` was the
   requirements-stage HEAD, and the specs-stage commits that followed it changed
   `docs/spec/` — files the linter sweeps — so a finding-set comparison against
   `a1ab5ba` would report specs-stage drift as a two-root regression. The task
   writes both shas into the baseline artifact and names the one it used
   — traces to `two-root-linter.md` §1, §Acceptance Criteria
2. [x] [implement] **The paired edit — one change, three files.** Drop the retired
   front door's filename from `RETIRED_SCOPE_FILES` (`tools/skill-lint.py:381`),
   from the self-test's independent `policed_files` tuple (`:1252`) and from the
   documented tuple at `docs/spec/skill-namespace-rename.md:76`, leaving five
   names in each. Editing any one alone trips the scope-drift check or leaves
   the spec contradicting the code — do not split this across tasks or chunks
   — traces to `skill-namespace-rename.md` §Two-Root Amendment
   (REQ-LINT-PACKAGING-008)
3. [x] [implement] Reconcile `CLAUDE.md`'s two contradictory marker statements
   (§Phase Detection says marker `4`; §Multi-Workstream Layout says marker `3`
   "is what this repo uses today") to the marker `docs/.sdd-version` actually
   carries, keeping "marker `3` remains supported" and removing the false
   this-repository claim. No other substance changes — traces to
   `project-docs.md` §`CLAUDE.md` (REQ-DOCS-PACKAGING-002)
4. [x] [verify] `python3 tools/skill-lint.py --self-test` passes after task 2;
   removing the name from only one tuple makes it fail naming the scope drift
   (invertibility). The marker named as this repository's own in `CLAUDE.md`
   string-equals the trimmed contents of `docs/.sdd-version`, read at run time,
   and exactly one marker is so named — traces to `skill-namespace-rename.md`,
   `project-docs.md` §Acceptance Criteria
**Entry criteria**: None (first chunk).
**Exit criteria**: Pre-change baseline artifact written (both shas recorded,
the one used named); both tuples and the spec carry
five names and agree; `CLAUDE.md` names one marker; self-test green.

### Chunk 1: The two-root constructor interface
**Goal**: `Linter(corpus_root, suite_root=None, suite_rules=True)` exists and,
with the two roots equal, reproduces the pre-change sweep exactly.
**Depends on**: Chunk 0.
**Tasks**:
1. [x] [implement] Add the two roots as **constructor parameters**. `corpus_root`
   keeps the CLI positional's value and **defaults to the invocation cwd, never
   to the script's location** — the current `parent-of-parent` default
   (`:1308`) names `plugins/sdd` after the move and would silently stop sweeping
   `docs/`. `suite_root` defaults to the script's own plugin root. No
   environment variable, no new CLI option — traces to `two-root-linter.md` §2
   (REQ-PKG-PACKAGING-002)
2. [x] [implement] `swept_roots()` — the set union over **resolved absolute paths**,
   admitting the suite term only when `suite_root` is contained in
   `corpus_root`, equality counting as containment and degenerating to today's
   single walk. `walk()` returns the deduplicated union of
   `<root>/skills/**/*.md` over that set — traces to `two-root-linter.md` §2
3. [x] [implement] `rel(f)` — per-root rendering: each swept file's relative path is
   computed against the root it was walked from, not a single fixed root —
   traces to `two-root-linter.md` §2
4. [x] [implement] The **duplicate-freeness construction guard** as a *pure function
   over a list of paths returning findings*, called on every invocation and
   skippable by no mode (`--self-test`, `--print-population`, plain run). On
   failure the observable is a `fail`-severity finding in the run's own findings
   list naming the duplicated path — the `flag()` default, never a warning, an
   exception or a bare exit code — traces to `two-root-linter.md` §6
   (REQ-LINT-PACKAGING-005)
5. [x] [implement] Confirm the negative surface: no `--no-suite-rules` option is
   added, argparse grows no `--suite-root` this cycle, and every
   `suite_rules=False` construction site stays inside the self-test — traces to
   `two-root-linter.md` §2 (REQ-PKG-PACKAGING-003)
6. [x] [implement] **The documented default changes with the code.** Restate the
   positional argument's help string (`:1301-1302`, "repository root to lint
   (default: repo containing this script)") and the `REPO_ROOT` sentences of
   `docs/spec/skill-lint-v5.md` (:322, :469, :566) for the cwd default and the
   two roots. The old wording survives **only** inside `skill-lint-v5.md`
   §Two-Root Amendment, quoted in order to be retired — traces to
   `skill-lint-v5.md` §Two-Root Amendment (REQ-PKG-PACKAGING-002)
7. [x] [verify] **Lands three named checked-in self-test cases** of
   `two-root-linter.md` §Verification — `two_roots_construct_distinct_and_equal`
   (construct the class with distinct roots and with equal roots without
   touching argparse), `equal_roots_sweep_set_unchanged` (with equal roots the
   swept set is identical to the **pre-change baseline**, compared as sets
   derived at run time) and `sweep_is_duplicate_free` (the positive half of
   task 4's guard: on a fixture whose union would otherwise repeat a path, the
   swept list holds it once and the guard emits no finding). These are
   checked-in cases in the self-test, not one-off checks — traces to
   `two-root-linter.md` §Verification, §Acceptance Criteria
**Entry criteria**: Chunk 0 complete.
**Exit criteria**: Equal-roots behaviour is byte-for-byte the pre-change
behaviour; the guard runs on every invocation; help text and `skill-lint-v5.md`
carry no surviving script-location-default claim outside the amendment section.

### Chunk 2: Per-entry bindings and the suite-gated retarget
**Goal**: Every check that names a path knows which root that path follows.
**Depends on**: Chunk 1.
**Tasks**:
1. [x] [implement] `retired_scope_files()` binds **per entry**, not per root:
   `skills` / `tools` / `agents` → suite root; `docs/spec` / `docs/requirements`
   → corpus root; `.claude-plugin` and the five root files (`CLAUDE.md`,
   `README.md`, `CONTRIBUTING.md`, `LICENSE`, `.pre-commit-config.yaml`) → the
   **deduplicated union of both**. Replace the `f.relative_to(self.root)` calls
   at `:756`, `:760` and `:772` with per-entry rendering — relative to the root
   that entry is bound to, a union-bound entry relative to whichever root
   supplied the file — or two distinct roots raise `ValueError` and the
   requirement is unimplementable literally. The existing self-test block
   pinning the two constants against literal name tuples is **retained
   unchanged** — traces to `two-root-linter.md` §4 (REQ-LINT-PACKAGING-001)
2. [x] [implement] `TEMPLATE_PAIRS` binds **per side**: the `TEMPLATE_SOURCE` side
   (`skills/orchestrate/references/dispatch-templates.md`) to the suite root,
   every row's `spec` key (`docs/spec/…`) to the corpus root. Under **disjoint**
   roots the spec side is **skipped, not warned** — warning there names this
   suite's spec files inside a consumer's tree. Under containment the spec side
   is checked and an absent spec keeps warning, unchanged — traces to
   `two-root-linter.md` §5 (REQ-LINT-PACKAGING-002)
3. [x] [implement] Retarget the 56 suite-gated rows (`REQUIRED` 40,
   `VERSION_GATED_SKILLS` 9, `V4_CONTRACT_SKILLS` 7) to resolve their path keys
   against the **suite root**. `FORBIDDEN`'s 13 ungated rows, frontmatter, links,
   size and drift phrases keep resolving against the corpus root. Preserve every
   row — the population comparison in Chunk 4 is the regression check on exactly
   this edit — traces to `two-root-linter.md` §3 (REQ-PKG-PACKAGING-004)
4. [x] [verify] **Lands the named checked-in self-test case
   `retired_scope_binds_per_entry`** (`two-root-linter.md` §Verification):
   per-entry binding and rendering hold on a seeded file under each root; no
   construction with two distinct roots raises `ValueError`; on a fixture tree
   carrying both `skills/` and `docs/` with the roots set equal, the returned
   set is identical to the pre-change single-root result — traces to
   `two-root-linter.md` §Verification, §Acceptance Criteria
5. [x] [verify] **Lands the named checked-in self-test case
   `retarget_seeds_an_ungated_finding`** (`two-root-linter.md` §Verification) —
   the retarget check, with a seeded ungated violation. On a scratch
   tree whose corpus root has no `skills/` and whose suite root does, seed
   `<corpus_root>/docs/spec/seeded-retired.md` with one unfenced retired-prefix
   tool name: **no** finding carries a tag from the three gated tables, **and**
   the findings list holds a finding whose path is `docs/spec/seeded-retired.md`
   and whose tag is `[retired-prefix]`, asserted by name. The seeded finding is
   what distinguishes a correct retarget from a linter whose checks are all off
   — traces to `two-root-linter.md` §Acceptance Criteria
6. [x] [verify] **REQ-PKG-PACKAGING-004's equal-roots comparison, run here and not
   after the move (carried note M1).** With the live pre-change tree still on
   disk and the two roots set **equal**, the finding set of the retargeted
   linter is identical — compared as a set derived at run time — to the
   **pre-change baseline** finding set captured at C0.1. This is the regression
   check on task 3's retarget of the 56 gated rows, and its comparand is a live
   tree, not a git object. Scheduling it after the move would need a worktree
   checked out at the pre-move sha *plus* an explicit equal-roots construction
   (post-move, `suite_root` defaults to the plugin root, so the two roots are
   not equal by default) — mechanism this plan deliberately does not build
   — traces to `two-root-linter.md` §3, §Acceptance Criteria
   (REQ-PKG-PACKAGING-004)
**Entry criteria**: Chunk 1 complete.
**Exit criteria**: All four dual-rooted checks bind and render per entry/side;
the retarget is proven by a seeded ungated finding, not by silence; the
equal-roots finding set matches the pre-change baseline.

### Chunk 3: The three fixture geometries and their negative cases
**Goal**: The self-test pins per-root rendering, the consumer shape, and
single-sweep — each geometry proving only what it can prove.
**Depends on**: Chunk 2.
**Tasks**:
1. [x] [implement] **Fixture A — nested** (`suite_root = corpus_root/plugins/sdd`).
   Seeds a walk-class violation under **each** root and asserts **both** are
   reported, each rendered relative to the root it was walked from — both as
   `skills/…` with **no** `plugins/sdd/` segment. Two seeds are required: one
   cannot discriminate per-root rendering from suite-rooted rendering. Fixture A
   does **not** pin single-sweep and must not be written as though it did —
   traces to `two-root-linter.md` §7 (REQ-PKG-PACKAGING-006)
2. [x] [implement] **Fixture B — disjoint** (suite root outside the corpus root, the
   consumer shape). Asserts (i) a **table-row** violation seeded under the suite
   root **is** reported; (ii) a walk-class violation seeded under
   `suite_root/skills/**` is **not** reported, asserted as a **named absent
   finding for a specific seeded path** while other findings are present. No
   assertion may rest on exit-code silence — traces to `two-root-linter.md` §7
   (REQ-PKG-PACKAGING-007)
3. [x] [implement] Add to fixture B the **manifest-pair membership assertion**: the
   set returned by `retired_scope_files()` contains **both**
   `<suite_root>/.claude-plugin/plugin.json` and
   `<corpus_root>/.claude-plugin/marketplace.json`. Each one-root binding drops
   exactly one and fails naming the missing path. No count-based assertion may
   replace it — traces to `two-root-linter.md` §7 (REQ-LINT-PACKAGING-003)
4. [x] [implement] **Case C — equal roots**, reusing fixture A's corpus tree with
   both roots equal. Seeds one walk-class violation under `skills/**` and
   asserts it is counted **exactly once** — the only geometry distinguishing a
   set union from a concatenation. Extract the counting path as a **pure
   function from swept list to findings** (one finding per violation in that
   list), with deduplication staying inside §2's union builder — traces to
   `two-root-linter.md` §7 (REQ-PKG-PACKAGING-008)
5. [x] [implement] **The two checked-in negative cases** — carried note m1: the
   spec's §Verification names twelve self-test cases and these two are not among
   them, so the list becomes **fourteen**. (a) Case C's own negative case calls
   the counting function of task 4 directly with a hand-built swept list holding
   the seeded path **twice** and asserts the count-once assertion **fails**,
   naming the seeded path. (b) The duplicate-freeness negative case calls
   Chunk 1's guard with a hand-built list holding one path twice and asserts a
   `fail` finding naming the duplicated path. Neither may be cited as
   discharging the other, and neither uses source mutation or a manual step —
   traces to `two-root-linter.md` §6, §7 (REQ-PKG-PACKAGING-008,
   REQ-LINT-PACKAGING-005)
6. [x] [implement] Each of the three fixtures seeds a known number of `.md` files and
   asserts the sweep returns **exactly** that number. A literal is sound here and
   only here — traces to `two-root-linter.md` §7 (REQ-LINT-PACKAGING-006)
7. [x] [verify] Invertibility sweep over **every self-test case that exists at the
   close of this chunk** (C1.7's three, C2.4's, C2.5's, and this chunk's own —
   thirteen of the fourteen; `print_population_shape` lands at C4.3 and is
   swept there): swapping each case's expectations fails the self-test. Adding a
   file to a fixture tree without updating its count fails. Binding the corpus
   walk to a root holding no corpus fails the count assertion. The fourteen-case
   total is asserted once, at C7.6 — traces to `two-root-linter.md`
   §Verification
8. [x] [verify] **Carried note M4 — the reviewer-checkable residue, stated as a
   task.** §6 and §7 name it in design prose but not in the acceptance bullets,
   so a task written from the bullet alone loses the obligation: assert by
   inspection that §2's union builder is the **only production call site** of
   the counting function and of the duplicate-freeness guard, and record that
   finding in the chunk's close note — traces to `two-root-linter.md` §6, §7
9. [x] [implement] **Lands the named checked-in self-test case
   `template_pairs_bind_per_side`** — the assertions REQ-LINT-PACKAGING-002
   needs and that C2.2 (an implement task) does not carry. One case per
   geometry, plus its negative control:
   (a) **nested** — with `suite_root = corpus_root/plugins/sdd`, a
   `TEMPLATE_SOURCE`-side drift seeded under the suite root **is** reported and
   a `spec`-side absent spec under the corpus root **still warns**, unchanged
   from today;
   (b) **disjoint** — the `spec` side is **skipped, not warned**: assert that
   **no `template-drift` finding of any severity appears**, asserted as a named
   absent finding per row, never by exit-code silence, while the
   `TEMPLATE_SOURCE`-side finding is still present;
   (c) **equal roots** — both sides bind to the one root and behaviour is the
   pre-change behaviour;
   (d) **the negative control** (`two-root-linter.md` §Acceptance Criteria
   bullet 6): binding **both** sides to the suite root makes all four rows emit
   the absent-spec warning — the self-test asserts this does **not** happen, so
   a wholesale one-root binding fails loudly rather than passing quietly
   — traces to `two-root-linter.md` §5, §7, §Verification
   (REQ-LINT-PACKAGING-002)
10. [x] [implement] **Bind `skill_dir_of()` to the root its files were walked
    from** — added post-plan from the Chunk 2 verification, which found the
    defect no chunk task covers. `skill_dir_of()` computed
    `f.relative_to(self.root / "skills")`, i.e. corpus_root/skills, so after the
    Chunk 5 move every suite-root file carrying a `` `references/….md` `` span
    (seven production files route through `resolve_backtick_path`/`check_links`)
    would raise `ValueError`. §4 binds `skills` to the suite root and §3's
    "links keep resolving against the corpus root" governs link *targets*, not
    the location of a swept file's skill directory — neither section assigns
    `skill_dir_of` a root, and that gap is the defect. Bind it to the root the
    file was walked from, the same rule `rel()` uses, so it holds under nested,
    disjoint and equal geometries; landed with the named self-test case
    `skill_dir_of_binds_per_root`, **in addition** to the fourteen — traces to
    `two-root-linter.md` §2, §4
11. [x] [implement] **Make `FORBIDDEN`'s `allow_files` matching root-correct** —
    added post-plan from the same Chunk 2 verification. `check_forbidden()`
    computed a corpus-rooted local path and matched `allow_files` entries such
    as `skills/orchestrate/SKILL.md` against it; under nested roots a suite-root
    file's corpus-rooted path is `plugins/sdd/skills/orchestrate/SKILL.md`, so
    the entry silently stops matching and that allowlist row is disabled with no
    diagnostic. Only the `rule["files"]` substring filter and the `allow_files`
    exact match are affected — the finding's rendering is already correct
    through `flag()`'s `self.rel()` default; fix the matching path, not the
    rendering. Landed with the named self-test case
    `forbidden_allow_files_root_correct`, **in addition** to the fourteen —
    traces to `two-root-linter.md` §2, §3
**Entry criteria**: Chunk 2 complete.
**Exit criteria**: The thirteen self-test cases landed by Chunks 1–3 are green
and each is invertible (task 7's sweep is the evidence); the fourteenth,
`print_population_shape`, lands at C4.3 and the fourteen-case total is asserted
at C7.6 — this chunk does **not** claim it. The residue of M4 is recorded rather
than implied.

### Chunk 4: `--print-population` and the no-pinned-count discipline
**Goal**: The counts that may be printed are printed; the counts that may not be
asserted are provably not asserted.
**Depends on**: Chunk 3.
**Tasks**:
1. [ ] [implement] Add the `--print-population` flag. It prints one line per rule
   table with its row count — **derived from the table at run time, never
   written into the flag** — plus the informational
   `corpus: FILES_SWEPT=<n>  policed-areas=<n>` line, which is **introduced**
   here, not retained. This task **must precede** any task evaluating the
   population criterion (the ordering constraint is part of
   REQ-LINT-PACKAGING-007, not a scheduling preference) — traces to
   `two-root-linter.md` §6 (REQ-LINT-PACKAGING-007, REQ-LINT-PACKAGING-004
   emission half)
2. [ ] [verify] **The no-pinned-count check, as three runnable greps** over
   **`tools/skill-lint.py`** — the pre-move path, because this chunk runs
   before the Chunk 5 move and `plugins/sdd/tools/skill-lint.py` does not exist
   yet (a grep over a missing file exits 2 and this criterion would close on a
   result it never measured). The same three greps are **re-run at the post-move
   path** `plugins/sdd/tools/skill-lint.py` at **C7.8**, which is where
   REQ-LINT-PACKAGING-004's acceptance is written. Scope: that one file **only**
   — the linter source and the
   self-test it carries — excluding the fixture bodies of A, B and case C
   (identified by §7's fixture function names), whose seeded counts are sound
   literals. Each returns zero matches:
   `grep -nE '(FILES_SWEPT|files_swept|len\( *swept *\))[^\n]*(==|!=|>=|<=|<|>) *[0-9]+'`;
   `grep -nE '[0-9]+ *(==|!=) *(FILES_SWEPT|files_swept|len\( *swept *\))'`;
   `grep -n 'git ls-files'`. Prose is deliberately out of scope. Record as
   **reviewer-checkable** that no spec *asserts* a pinned count and that an
   assertion in a spelling none of the three greps matches would not be caught
   — traces to `two-root-linter.md` §6 (REQ-LINT-PACKAGING-004)
3. [ ] [implement] **Lands the named checked-in self-test case
   `print_population_shape`** — the fourteenth case, and the one Chunk 3 could
   not land because the flag does not exist until task 1: the case asserts the
   `--print-population` output **by shape**, one line per rule table carrying a
   run-time-derived integer and the `corpus: FILES_SWEPT=<n>
   policed-areas=<n>` line, with **no number pinned in the assertion**.
   Inverting it (asserting a shape the flag does not print) fails the self-test
   — traces to `two-root-linter.md` §6, §Verification (REQ-LINT-PACKAGING-007)
**Entry criteria**: Chunk 3 complete.
**Exit criteria**: The flag exists and is exercised by task 3's checked-in
shape assertion, bringing the self-test to fourteen cases; the three greps over
the **pre-move** `tools/skill-lint.py` are empty (the post-move re-run is C7.8);
the emission half awaits Chunk 7's post-move evaluation.

### Chunk 5: The move — one identifiable commit
**Goal**: `plugins/sdd/` exists, the commit gate still works, and a pre-move sha
exists for every criterion that cites one.
**Depends on**: Chunk 4.
**Tasks**:
1. [ ] [implement] **The `README`/`LICENSE` decision point** (the one standing
   `OPEN:`). Decide whether `plugins/sdd/` carries its own `README`/`LICENSE`
   — 45 versus 47 installed files. Non-blocking by the requirements' own
   reasoning: either answer changes which root supplies those names, not whether
   they are policed, since REQ-LINT-PACKAGING-001 binds both to the union.
   Blocking constraint: it is a packaging-surface decision about what an
   installed plugin shows a reader, owned by no artifact in this cycle.
   `OPEN:` if it cannot be settled at the move, default to **not** duplicating
   them (45 files) and record the default as the decision taken, with carried
   note m3 discharged by task 5's wording — traces to `two-root-linter.md`
   §Open Items (REQ-PKG-PACKAGING-001)
2. [ ] [implement] **Perform the move**, recorded by git as a move and not as a
   delete plus an add (`git log --follow` must resolve each moved file).
   Membership rule: `skills/**`, `agents/**`, `tools/**` and
   `.claude-plugin/plugin.json` move to `plugins/sdd/`; **everything else stays**
   at the corpus root, including `.claude-plugin/marketplace.json`, `docs/**`,
   `CLAUDE.md`, `.pre-commit-config.yaml`, `README.md`, `LICENSE` and
   `CONTRIBUTING.md`. The "45 move, 154 stay" figure is carried costing, not the
   rule — traces to `two-root-linter.md` §1 (REQ-PKG-PACKAGING-001)
3. [ ] [implement] In the **same change**: set the plugin entry's `source` in
   `.claude-plugin/marketplace.json` to name the `plugins/sdd` subdirectory
   rather than `./`, and resolve the marketplace-cycle placement amendments the
   move makes due — traces to `marketplace-packaging.md` §Placement
   (REQ-PKG-PACKAGING-001, REQ-PKG-PACKAGING-010)
4. [ ] [implement] In the **same change**: prefix **both** `repo: local` hook entries
   in `.pre-commit-config.yaml` with `plugins/sdd/` — the drift sweep (~`:27-32`)
   and the skill linter (~`:33-38`). Editing one leaves the gate invoking a dead
   path. The linter hook's entry stays **zero-argument**
   (`python3 plugins/sdd/tools/skill-lint.py`), correct only because Chunk 1
   task 1 made the corpus root default to cwd. **Why the drift-sweep entry
   likewise takes no `--root`** — for a different reason than the linter's: it is not
   relying on a default this cycle changed, but on `tools/gc.py`'s own, which
   resolves the root from `git rev-parse --show-toplevel` and therefore keeps
   naming the operator's repository wherever the script itself lives; so only
   the **script path** is prefixed on that entry. `pass_filenames: false` and
   `always_run: true` are unchanged on both — traces to `pre-commit.md` §Two-Root
   Amendment (REQ-PC-PACKAGING-001)
5. [ ] [verify] The move criteria, all derived at run time: `test -d plugins/sdd`,
   `test -f plugins/sdd/.claude-plugin/plugin.json`,
   `test -f .claude-plugin/marketplace.json`,
   `test ! -e plugins/sdd/.claude-plugin/marketplace.json`; the parsed `source`
   resolves to `plugins/sdd`; every component-list path passes `test -e` under
   the suite root; **per-name membership** against
   `git ls-tree -r --name-only $(git rev-parse <move commit>^)` — the
   **pre-move sha**, derived here as the move commit's parent and **not** the
   pre-change baseline sha of C0.1, which by this point is several commits
   older (§Conventions) — never a walk of the post-move tree, where the clause
   passes vacuously; **the move is recorded by git as a move** — carried note
   M5: `git log --follow <path>` resolves each moved file to its pre-move
   history, asserted here per moved path and not only claimed by task 2, since
   it is both an acceptance clause of REQ-PKG-PACKAGING-001 and a replan
   trigger; and
   **the stay-list is policed by name** with a paired `test ! -e` under
   `plugins/sdd/`. Carried note m3: state the criterion so it holds **under
   either answer** to task 1 — `README.md` and `LICENSE` are the only two names
   exempt from the paired `test ! -e` — traces to `two-root-linter.md`
   §Acceptance Criteria (REQ-PKG-PACKAGING-001)
6. [ ] [verify] **The drift sweep resolves its linter sibling-first** — three
   assertions, each with the construction that makes it fail. (1) Precedence:
   with a distinguishable stub at **both** candidate locations, the sweep invokes
   the sibling one; reordering the candidate tuple in `lint_path()` makes the
   root marker appear. (2) Fallback: with the sibling absent and only
   `<root>/tools/skill-lint.py` present, `lint_path()` resolves to the root
   candidate. (3) Neither present: exit 2 with `error: linter missing`. This
   freezes existing behaviour (`gc.py:501-502`) that becomes load-bearing here,
   since `<root>/tools/skill-lint.py` ceases to exist in this repository. Record
   the three residues (a)(b)(c) named in the requirement — traces to
   `marketplace-packaging.md` §Tools (REQ-PKG-PACKAGING-010)
7. [ ] [verify] Reverting the `plugins/sdd/` prefix on either pre-commit hook alone
   makes that hook fail with a missing-file error; every `entry` value parsed
   from the two local hook entries names a path that exists, checked by `test -f`
   per parsed path; the linter hook's parsed `entry` carries no positional root
   argument — traces to `pre-commit.md` §Two-Root Amendment
   (REQ-PC-PACKAGING-001)
8. [ ] [verify] **The membership criterion of `pre-commit.md` §Two-Root Amendment,
   given an owner (carried note M6).** Running the linter hook's parsed `entry`
   **verbatim, from the repository root**, sweeps a set containing **at least
   one `docs/spec/` path** — asserted as **membership on the swept set derived
   at run time, never on the exit code**, because a zero exit proves only that
   nothing was found, not that anything was looked at. This is the criterion
   that catches a corpus root that silently resolved to the suite. C5.7 checks
   the entries' *shape* and C7.1 runs an equivalent command under
   REQ-PKG-PACKAGING-002; neither discharges this one — traces to
   `pre-commit.md` §Two-Root Amendment (REQ-PC-PACKAGING-001)
**Entry criteria**: Chunk 4 complete; the **pre-change baseline** of Chunk 0 is
on disk with its sha recorded.
**Exit criteria**: One commit contains the move, the `source` edit and both hook
prefixes. That commit's **parent** is the **pre-move sha** cited by C5.5 and
C7.4 — a distinct, later object from C0.1's pre-change baseline sha, which the
behavioural comparisons (C1.7, C2.4, C2.6) cite instead.

### Chunk 6: Post-move repairs — the spellings the move changes
**Goal**: Every text the move invalidates is corrected, and the three
documentation repairs land.
**Depends on**: Chunk 5.
**Tasks**:
1. [ ] [implement] Repair the last cwd-relative drift-sweep invocation in a skill
   body — `python3 tools/gc.py --report --root .` in the verify skill's gc
   criterion (`skills/verify/SKILL.md:169`, now under `plugins/sdd/`) — so
   **both** halves come out correct: the script path resolves to the tool inside
   the suite, and the root argument still names the operator's own working
   directory, never the suite. **Sequenced after** Chunk 1 and Chunk 2 — done
   first it would pin a spelling those bindings then change — traces to
   `two-root-linter.md` §8 (REQ-PKG-PACKAGING-009)
2. [ ] [implement] Correct `docs/spec/orchestration.md` (~`:574`) to name the project
   README by its live filename; nothing else in the paragraph changes, and the
   symlink-install convention is untouched. **Carried note m2**: the criterion's
   drift-sweep leg has a pre-move/post-move binary the requirement's own wording
   drops — evaluate it as `python3 plugins/sdd/tools/gc.py --report` here,
   because this task runs after the move, and say so in the task close — traces
   to `project-docs.md` §Carried Documentation Repairs (REQ-DOCS-PACKAGING-001)
3. [ ] [implement] **The amended F11 target.** Re-scope the pre-split F11 sentence
   wherever it is stated — the linter's own docstring or rule-table comment, and
   `docs/spec/skill-lint-v5.md` lines 322, 469-470, 494 and 566 — to name the
   **ungated** set as the consumer-facing one, with **both** exceptions stated
   alongside it every time: (i) *ungated but suite-bound* —
   `check_retired_prefix()`; (ii) *gated but corpus-bound* — `TEMPLATE_PAIRS`'s
   `spec` side. The sentence is re-scoped, never deleted — traces to
   `skill-lint-v5.md` §Two-Root Amendment (REQ-PKG-PACKAGING-005)
4. [ ] [implement] Make the deferral-backlog screen's liveness rule **item-scoped**:
   a marker suppresses only the item it belongs to, so a marker introducing or
   closing one item never satisfies the rule for its neighbour. The phrase table
   and the marker regex stay where they are and keep being read from the spec
   rather than retyped; the screen's standing qualification is unchanged. Add the
   distinguishing fixture: two adjacent items, the first carrying a bracketed
   dated marker and the second a backlog phrase with no marker of its own —
   scored **live** under the new rule and **not-live** under `L`/`L-1` — traces
   to `project-docs.md` §Carried Documentation Repairs (REQ-DOCS-PACKAGING-003)
5. [ ] [implement] **Carried note M5.** `docs/spec/requirements-artifacts.md`
   §`## Out of Scope` Discipline still carries the `L`/`L-1` rule as Approved
   text with no pointer to its superseding contract. Land the wording there:
   the rule is superseded by REQ-DOCS-PACKAGING-003's item-scoped contract, with
   a pointer rather than a silent rewrite — traces to `project-docs.md`
   §Carried Documentation Repairs (REQ-DOCS-PACKAGING-003)
6. [ ] [verify] A run-time grep of `docs/spec/orchestration.md` for the retired front
   door's filename returns zero matches inside backticks or out; a run-time grep
   across `docs/spec/` at the corpus root and `plugins/sdd/skills/` and
   `plugins/sdd/tools/` at the suite root for the F11 sentence **unaccompanied
   by** a scoping clause naming the ungated set returns zero matches; a grep over
   `plugins/sdd/skills/` for a drift-sweep invocation whose script path is bare
   `tools/gc.py` is empty and every such invocation carries an explicit root
   argument; and — carried note m4 — REQ-DOCS-PACKAGING-001's **positive**
   clause, unasserted until now: the corrected paragraph in
   `docs/spec/orchestration.md` **names `README.md`**, asserted as a present
   match on that filename, not merely as the absence of the retired one
   — traces to `two-root-linter.md`, `skill-lint-v5.md`,
   `project-docs.md` §Acceptance Criteria
7. [ ] [verify] Re-run the deferral-backlog screen over `docs/ws/*/verification.md`
   with the item-scoped rule and report its counts; **assert no count that this
   run did not measure** — traces to `project-docs.md` §Acceptance Criteria
8. [ ] [verify] **The scratch-consumer-repository run** — REQ-PKG-PACKAGING-009's
   third acceptance clause (`two-root-linter.md` §Acceptance Criteria bullet 5),
   which neither task 1's edit nor task 6's greps can reach: a grep proves the
   spelling, not what the spelling resolves to at run time. In a **scratch git
   repository that is not this one** (`git init` in a temp dir, seeded with a
   `docs/` tree and no `skills/`), run the verify skill's gc criterion command
   **verbatim as task 1 leaves it**, with this repository's `plugins/sdd/`
   available as the suite. Assert the resolved root **is the scratch
   repository** — the sweep's reported root, derived at run time, equals the
   scratch repo path and **no swept path lies under this suite's tree**. The
   inversion that makes it fail: hard-coding the root to the suite makes the
   assertion name a suite path — traces to `two-root-linter.md` §8,
   §Acceptance Criteria (REQ-PKG-PACKAGING-009)
9. [ ] [implement] **The root documents the move invalidates (carried note M4).**
   `CLAUDE.md` and `CONTRIBUTING.md` spell suite paths that no other task
   touches and that the move makes wrong: `CLAUDE.md:101,103,185`
   (`tools/gc.py`, `tools/skill-lint.py`) and `:30,45,76,82`
   (`skills/<name>/SKILL.md`, `agents/<name>.md`, the repository-structure
   block); `CONTRIBUTING.md:67-68,81-83,93,105`. Re-spell each to its
   `plugins/sdd/` path. **Constraint, and why this is not folded into C0.3**:
   REQ-DOCS-PACKAGING-002 requires `CLAUDE.md`'s two marker sections
   (§Phase Detection, §Multi-Workstream Layout) be "otherwise unchanged", so
   this task must (a) land **after** the move, not in Chunk 0, and (b) touch no
   line inside those two sections — the listed line numbers are all outside
   them, and the task re-checks that before editing. Any spelling that *is*
   inside a marker section is recorded as an accepted residue with its line
   named, not edited — traces to `project-docs.md` §`CLAUDE.md`,
   `two-root-linter.md` §1 (REQ-PKG-PACKAGING-001, REQ-DOCS-PACKAGING-002)
**Entry criteria**: Chunk 5 complete (the move commit exists).
**Exit criteria**: Scoped to what this chunk's tasks actually check (carried
note M7 — the earlier "no skill body **or spec** carries a pre-move spelling"
was broader than any check here): task 6's three named greps return zero
matches over the files they name and its `README.md` clause matches; the F11
target is stated with both exceptions in each of the locations task 3
enumerates; the screen is item-scoped and its fixture distinguishes the two
rules; task 8's resolved root is the scratch repository; and every root-document
line listed in task 9 is re-spelled or recorded as a named residue. A
corpus-wide "no pre-move spelling anywhere" claim is **not** made by this chunk
and is not required by any requirement.

### Chunk 7: Post-move acceptance evaluation
**Goal**: Every criterion written as "evaluated after the move" is evaluated,
against the moved tree.
**Depends on**: Chunk 6.
**Tasks**:
1. [ ] [verify] The zero-argument post-move run: `python3
   plugins/sdd/tools/skill-lint.py` from the repository root sweeps a set that
   **includes at least one `docs/spec/` path**, asserted by membership on the
   swept set derived at run time, never on the exit code. On the pinned pattern
   `grep -nE 'repo containing this script|defaults? to the (script|tool)'`, the
   shipped `--help` output returns zero matches and `skill-lint-v5.md` returns
   matches **only** inside its §Two-Root Amendment. `grep -n 'no-suite-rules'
   plugins/sdd/tools/skill-lint.py` is empty; the argparse surface exposes no
   `--suite-root`; every `suite_rules=False` site is inside the self-test —
   traces to `two-root-linter.md` §Acceptance Criteria (REQ-PKG-PACKAGING-002,
   REQ-PKG-PACKAGING-003)
2. [ ] [verify] The retarget's **post-move** confirmation. The equal-roots
   finding-set comparison itself is **not** run here — it ran at **C2.6**,
   against the live pre-change tree, because after the move that tree exists
   only in git history and the post-move `suite_root` default is the plugin
   root, so the two roots are no longer equal by default (carried note M1;
   §Conventions). What this task does instead is confirm the retarget survived
   the move: re-run **C2.5's seeded-ungated-violation check** against the moved
   tree — no finding carries a tag from the three gated tables when the corpus
   root has no `skills/`, and the seeded `docs/spec/` finding is still present
   by name — and **record C2.6's result** alongside it as the pre-move half of
   REQ-PKG-PACKAGING-004's acceptance. If C2.6 was not run, this task fails
   rather than substituting a post-move measurement for it — traces to
   `two-root-linter.md` §3 (REQ-PKG-PACKAGING-004)
3. [ ] [verify] `python3 plugins/sdd/tools/skill-lint.py --print-population` exits 0,
   prints the `corpus: FILES_SWEPT=<n>  policed-areas=<n>` line (asserted by
   **shape**, not number), and prints the four run-time-derived populations
   `REQUIRED=40 VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=13`. This is the one
   place in the corpus where a row population is compared against a number, and
   it is the regression check on Chunk 2 task 3's retarget — traces to
   `two-root-linter.md` §6 (REQ-LINT-PACKAGING-007, REQ-LINT-PACKAGING-004)
4. [ ] [verify] **Carried note M3 — the vacuous-glob hole.** The `test -d` guard in
   `marketplace-packaging.md`'s blanket clause does not cover glob-derived empty
   populations: a criterion quantifying over `skills/*/tools/*.py` still passes
   vacuously when the glob derives nothing. Before running the per-pair `cmp` /
   `test ! -L` assertions, **assert the derived population is non-empty**, and
   assert the loss check's two sides separately as the spec spells them
   (`ls plugins/sdd/tools/*.py | wc -l` not less than
   `git ls-tree --name-only <pre-move sha> tools/ | grep -c '\.py$'`) — traces to
   `marketplace-packaging.md` §Acceptance Criteria
5. [ ] [verify] The paired retired-filename removal, evaluated post-move: a run-time
   grep of `plugins/sdd/tools/skill-lint.py` for the retired filename returns
   zero matches; the same grep over `docs/spec/skill-namespace-rename.md`
   returns zero matches and that file's tuple lists five names; both tuples have
   five entries and are equal — traces to `skill-namespace-rename.md`
   §Two-Root Amendment (REQ-LINT-PACKAGING-008)
6. [ ] [verify] `python3 plugins/sdd/tools/skill-lint.py --self-test` passes (all
   fourteen cases) and `pre-commit run --all-files` exits 0 and leaves the
   working tree clean on an immediate second run — traces to
   `two-root-linter.md` §Acceptance Criteria, `pre-commit.md`
7. [ ] [verify] Manual: re-run REQ-PKG-MARKETPLACE-010's real-install observation
   against the moved tree, recorded as an observation with its command — traces
   to `two-root-linter.md` §Verification → Manual
8. [ ] [verify] **The no-pinned-count greps, re-run at the post-move path.** The
   three greps of C4.2, verbatim, over `plugins/sdd/tools/skill-lint.py` — the
   path at which REQ-LINT-PACKAGING-004's acceptance is written, and the first
   point in the plan at which that file exists. Each returns zero matches. The
   file must be confirmed present (`test -f`) **before** the greps run, so a
   missing-file exit 2 cannot be read as "empty" — traces to
   `two-root-linter.md` §6 (REQ-LINT-PACKAGING-004)
**Entry criteria**: Chunk 6 complete.
**Exit criteria**: Every after-the-move criterion across the 22 requirements has
been evaluated against the moved tree, with its result recorded.

## Requirement → Task Coverage

All 22 approved requirements, each mapped to the tasks that reach it. This table
lives here rather than in `docs/ws/packaging/traceability.md` because that
matrix's shape is pinned at six columns by `docs/spec/ws-traceability.md` — a
seventh `Task` cell makes every row unparseable and the drift sweep drops it
from the regenerated aggregate (`[traceability-rowdrop]`, observed at the plan
stage). Task refs read `C<chunk>.<task>`. Where a requirement's acceptance names a
self-test case, the owning task is the one that **lands the checked-in case**,
not merely the one that exercises the behaviour.

| Requirement | Spec | Tasks |
|---|---|---|
| REQ-PKG-PACKAGING-001 | two-root-linter.md | C5.1, C5.2, C5.3, C5.5 (`git ls-tree` + `git log --follow` at the **pre-move sha**), C6.9 |
| REQ-PKG-PACKAGING-002 | two-root-linter.md | C1.1, C1.2, C1.3, C1.6, C1.7 (`two_roots_construct_distinct_and_equal`, `equal_roots_sweep_set_unchanged`, `sweep_is_duplicate_free`), C7.1 |
| REQ-PKG-PACKAGING-003 | two-root-linter.md | C1.5, C7.1 |
| REQ-PKG-PACKAGING-004 | two-root-linter.md | C2.3, C2.5, **C2.6** (equal-roots comparison vs the **pre-change baseline** of C0.1), C7.2 (post-move confirmation) |
| REQ-PKG-PACKAGING-005 | skill-lint-v5.md | C6.3, C6.6 |
| REQ-PKG-PACKAGING-006 | two-root-linter.md | C3.1, C3.7 |
| REQ-PKG-PACKAGING-007 | two-root-linter.md | C3.2, C3.7 |
| REQ-PKG-PACKAGING-008 | two-root-linter.md | C3.4, C3.5, C3.8 |
| REQ-PKG-PACKAGING-009 | two-root-linter.md | C6.1, C6.6, **C6.8** (scratch consumer repository) |
| REQ-PKG-PACKAGING-010 | marketplace-packaging.md | C5.3, C5.6 |
| REQ-LINT-PACKAGING-001 | two-root-linter.md | C2.1, C2.4 (`retired_scope_binds_per_entry`), C1.7 |
| REQ-LINT-PACKAGING-002 | two-root-linter.md | C2.2, **C3.9** (`template_pairs_bind_per_side`, three geometries + the both-sides-to-suite negative control) |
| REQ-LINT-PACKAGING-003 | two-root-linter.md | C3.3 |
| REQ-LINT-PACKAGING-004 | two-root-linter.md | C4.1, C4.2 (three greps, **pre-move** `tools/skill-lint.py`), C7.3, **C7.8** (same three greps, **post-move** `plugins/sdd/tools/skill-lint.py`) |
| REQ-LINT-PACKAGING-005 | two-root-linter.md | C1.4, C1.7 (`sweep_is_duplicate_free`), C3.5, C3.8 |
| REQ-LINT-PACKAGING-006 | two-root-linter.md | C3.6, C3.7 |
| REQ-LINT-PACKAGING-007 | two-root-linter.md | C4.1, **C4.3** (`print_population_shape`), C7.3 |
| REQ-LINT-PACKAGING-008 | skill-namespace-rename.md | C0.2, C0.4, C7.5 |
| REQ-PC-PACKAGING-001 | pre-commit.md | C5.4, C5.7, **C5.8** (membership: the entry run verbatim sweeps a `docs/spec/` path), C7.6 |
| REQ-DOCS-PACKAGING-001 | project-docs.md | C6.2, C6.6 (incl. the positive `README.md` clause) |
| REQ-DOCS-PACKAGING-002 | project-docs.md | C0.3, C0.4, C6.9 (root-doc path spellings, marker sections untouched) |
| REQ-DOCS-PACKAGING-003 | project-docs.md | C6.4, C6.5, C6.7 |

## Replan Triggers

- **The move cannot be recorded as a move.** If `git log --follow` does not
  resolve moved files to their pre-move history — a rename-detection failure
  across 45 files — REQ-PKG-PACKAGING-001's history criterion is unsatisfiable
  as written → replan the criterion, not the move.
- **The containment rule makes a required assertion unbuildable.** If fixture B
  (disjoint) cannot produce a *table-row* violation that bypasses the walk while
  the walk-class seed stays absent, D4's fixture shape is refuted → replan
  REQ-PKG-PACKAGING-007 back to the specs stage.
- **The counting function cannot be separated from the deduplicator.** Case C's
  invertibility rests on the counting path being a pure function whose only
  production caller is §2's union builder. If the existing code cannot be split
  that way without a rewrite larger than this cycle → replan Chunk 3 task 4–5.
- **The population counts do not come out at 40/9/7/13** after the retarget.
  That is either a dropped/duplicated row (fix in place) or the carried
  population is wrong (RS-PACKAGING-002 evidence refuted) → replan to research.
- **The cwd default breaks an existing caller.** If any skill body, hook or tool
  depends on the old script-location default in a way Chunk 6 cannot repair →
  replan REQ-PKG-PACKAGING-002's default.
- **`pre-commit run --all-files` cannot reach green** after the move for a reason
  outside the two prefixed hooks → replan Chunk 5 task 4 with the gate's actual
  failure named.
- **A pre-move-sha criterion turns out to be unevaluable after Chunk 5 has
  landed.** Judgement threshold, stated so it is not left to taste: if at Chunk
  5, 6 or 7 a criterion citing the **pre-move sha** or the **pre-change
  baseline** cannot be evaluated from the artifacts then on disk — the baseline
  was not captured, the move commit's parent is not identifiable (a squash, an
  amend, a rebase), or the criterion needs the pre-change *tree* live rather
  than as a git object — do **not** substitute a post-move measurement and do
  **not** re-derive the comparand after the fact. Stop and replan the
  criterion, naming which of the two artifacts is missing and why. C2.6 exists
  precisely because one such criterion was found unevaluable post-move at the
  plan stage; a second occurrence is a signal the pre/post split is wrong, not
  a one-off.
- **The `README`/`LICENSE` OPEN turns out to be blocking** — i.e. a criterion is
  found that cannot be stated to hold under both answers → escalate it out of
  Chunk 5 task 1 into a decision the operator owns.

## Risks

- **The move is a wide, mechanical change across 45 files.** Mitigation: it is
  its own chunk and its own commit, with the whole two-root interface already
  built and green beforehand, so a failure after the move is a spelling failure
  and not a design failure.
- **Several criteria cite a pre-move sha.** Mitigation: Chunk 0 pins the baseline
  before anything edits, and Chunk 5 keeps the move's parent identifiable.
- **Two checks are ungated-but-suite-bound / gated-but-corpus-bound** (F11
  exceptions (i) and (ii)). These are the two places a wholesale binding is most
  tempting and most wrong. Mitigation: Chunk 2 tasks 1–2 name them explicitly
  and Chunk 6 task 3 forces the exceptions to be restated wherever F11 is.
- **Vacuous-pass criteria.** Three criteria in this cycle pass vacuously if a
  population derives empty (M3) or if a post-move walk replaces a pre-move
  enumeration. Mitigation: Chunk 5 task 5 and Chunk 7 task 4 assert non-emptiness
  before quantifying.
- **Reviewer-checkable residues** (M4, the three named in
  REQ-PKG-PACKAGING-010, and the grep-spelling gap in REQ-LINT-PACKAGING-004)
  are not mechanically closable. Mitigation: each is an explicit task or task
  clause that records the finding rather than leaving it implied.
