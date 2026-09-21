---
workstream: packaging
status: complete
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
1. [x] [implement] Add the `--print-population` flag. It prints one line per rule
   table with its row count — **derived from the table at run time, never
   written into the flag** — plus the informational
   `corpus: FILES_SWEPT=<n>  policed-areas=<n>` line, which is **introduced**
   here, not retained. This task **must precede** any task evaluating the
   population criterion (the ordering constraint is part of
   REQ-LINT-PACKAGING-007, not a scheduling preference) — traces to
   `two-root-linter.md` §6 (REQ-LINT-PACKAGING-007, REQ-LINT-PACKAGING-004
   emission half)
2. [x] [verify] **The no-pinned-count check, as three runnable greps** over
   **`tools/skill-lint.py`** — the pre-move path, because this chunk runs
   before the Chunk 5 move and `plugins/sdd/tools/skill-lint.py` does not exist
   yet (a grep over a missing file exits 2 and this criterion would close on a
   result it never measured). The same three greps are **re-run at the post-move
   path** `plugins/sdd/tools/skill-lint.py` at **C7.8**, which is where
   REQ-LINT-PACKAGING-004's acceptance is written. Scope: that one file **only**
   — the linter source and the
   self-test it carries — excluding the self-test's fixture-literal assertions
   **as a class** (a count over a tree the case seeded itself, or over a
   hand-built literal path list), not the enumeration "fixtures A, B and case
   C" this task originally wrote, which the verify-stage red round showed goes
   stale as cases land — see Chunk 12 and `two-root-linter.md` §Verification. Each returns zero matches:
   `grep -nE '(FILES_SWEPT|files_swept|len\( *swept *\))[^\n]*(==|!=|>=|<=|<|>) *[0-9]+'`;
   `grep -nE '[0-9]+ *(==|!=) *(FILES_SWEPT|files_swept|len\( *swept *\))'`;
   `grep -n 'git ls-files'`. Prose is deliberately out of scope. Record as
   **reviewer-checkable** that no spec *asserts* a pinned count and that an
   assertion in a spelling none of the three greps matches would not be caught
   — traces to `two-root-linter.md` §6 (REQ-LINT-PACKAGING-004)
3. [x] [implement] **Lands the named checked-in self-test case
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
1. [x] [implement] **The `README`/`LICENSE` decision point** (the one standing
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
2. [x] [implement] **Perform the move**, recorded by git as a move and not as a
   delete plus an add (`git log --follow` must resolve each moved file).
   Membership rule: `skills/**`, `agents/**`, `tools/**` and
   `.claude-plugin/plugin.json` move to `plugins/sdd/`; **everything else stays**
   at the corpus root, including `.claude-plugin/marketplace.json`, `docs/**`,
   `CLAUDE.md`, `.pre-commit-config.yaml`, `README.md`, `LICENSE` and
   `CONTRIBUTING.md`. The "45 move, 154 stay" figure is carried costing, not the
   rule — traces to `two-root-linter.md` §1 (REQ-PKG-PACKAGING-001)
3. [x] [implement] In the **same change**: set the plugin entry's `source` in
   `.claude-plugin/marketplace.json` to name the `plugins/sdd` subdirectory
   rather than `./`, and resolve the marketplace-cycle placement amendments the
   move makes due — traces to `marketplace-packaging.md` §Placement
   (REQ-PKG-PACKAGING-001, REQ-PKG-PACKAGING-010)
4. [x] [implement] In the **same change**: prefix **both** `repo: local` hook entries
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
5. [x] [verify] The move criteria, all derived at run time: `test -d plugins/sdd`,
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
6. [x] [verify] **The drift sweep resolves its linter sibling-first** — three
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
7. [x] [verify] Reverting the `plugins/sdd/` prefix on either pre-commit hook alone
   makes that hook fail with a missing-file error; every `entry` value parsed
   from the two local hook entries names a path that exists, checked by `test -f`
   per parsed path; the linter hook's parsed `entry` carries no positional root
   argument — traces to `pre-commit.md` §Two-Root Amendment
   (REQ-PC-PACKAGING-001)
8. [x] [verify] **The membership criterion of `pre-commit.md` §Two-Root Amendment,
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
1. [x] [implement] Repair the last cwd-relative drift-sweep invocation in a skill
   body — `python3 tools/gc.py --report --root .` in the verify skill's gc
   criterion (`skills/verify/SKILL.md:169`, now under `plugins/sdd/`) — so
   **both** halves come out correct: the script path resolves to the tool inside
   the suite, and the root argument still names the operator's own working
   directory, never the suite. **Sequenced after** Chunk 1 and Chunk 2 — done
   first it would pin a spelling those bindings then change — traces to
   `two-root-linter.md` §8 (REQ-PKG-PACKAGING-009)
2. [x] [implement] Correct `docs/spec/orchestration.md` (~`:574`) to name the project
   README by its live filename; nothing else in the paragraph changes, and the
   symlink-install convention is untouched. **Carried note m2**: the criterion's
   drift-sweep leg has a pre-move/post-move binary the requirement's own wording
   drops — evaluate it as `python3 plugins/sdd/tools/gc.py --report` here,
   because this task runs after the move, and say so in the task close — traces
   to `project-docs.md` §Carried Documentation Repairs (REQ-DOCS-PACKAGING-001)
3. [x] [implement] **The amended F11 target.** Re-scope the pre-split F11 sentence
   wherever it is stated — the linter's own docstring or rule-table comment, and
   `docs/spec/skill-lint-v5.md` lines 322, 469-470, 494 and 566 — to name the
   **ungated** set as the consumer-facing one, with **both** exceptions stated
   alongside it every time: (i) *ungated but suite-bound* —
   `check_retired_prefix()`; (ii) *gated but corpus-bound* — `TEMPLATE_PAIRS`'s
   `spec` side. The sentence is re-scoped, never deleted — traces to
   `skill-lint-v5.md` §Two-Root Amendment (REQ-PKG-PACKAGING-005)
4. [x] [implement] Make the deferral-backlog screen's liveness rule **item-scoped**:
   a marker suppresses only the item it belongs to, so a marker introducing or
   closing one item never satisfies the rule for its neighbour. The phrase table
   and the marker regex stay where they are and keep being read from the spec
   rather than retyped; the screen's standing qualification is unchanged. Add the
   distinguishing fixture: two adjacent items, the first carrying a bracketed
   dated marker and the second a backlog phrase with no marker of its own —
   scored **live** under the new rule and **not-live** under `L`/`L-1` — traces
   to `project-docs.md` §Carried Documentation Repairs (REQ-DOCS-PACKAGING-003)
5. [x] [implement] **Carried note M5.** `docs/spec/requirements-artifacts.md`
   §`## Out of Scope` Discipline still carries the `L`/`L-1` rule as Approved
   text with no pointer to its superseding contract. Land the wording there:
   the rule is superseded by REQ-DOCS-PACKAGING-003's item-scoped contract, with
   a pointer rather than a silent rewrite — traces to `project-docs.md`
   §Carried Documentation Repairs (REQ-DOCS-PACKAGING-003)
6. [x] [verify] A run-time grep of `docs/spec/orchestration.md` for the retired front
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
7. [x] [verify] Re-run the deferral-backlog screen over `docs/ws/*/verification.md`
   with the item-scoped rule and report its counts; **assert no count that this
   run did not measure** — traces to `project-docs.md` §Acceptance Criteria
8. [x] [verify] **The scratch-consumer-repository run** — REQ-PKG-PACKAGING-009's
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
9. [x] [implement] **The root documents the move invalidates (carried note M4).**
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
10. [x] [implement] **The self-test fixture's single-root assumption.**
   `plugins/sdd/tools/skill-lint.py`'s `--self-test` derived `docs/spec/` as
   `real_skills.parent / "docs" / "spec"`, i.e. `plugins/sdd/docs/spec`, which
   never exists because `docs/spec` deliberately stayed at the corpus root; the
   self-test exited 1 post-move (it was green at `95c28b7`). The fixture
   locates `docs/spec` at the **corpus** root — the nearest ancestor of the
   suite that holds it, so the equal-roots geometry is unchanged. *Added
   post-plan, found by the Chunk 5 verification, chartered nowhere; C7.6
   requires `--self-test` green* — traces to `two-root-linter.md` §2, §4
11. [x] [implement] **`check_structure()` is not suite-root aware.** It checked
   `self.root / "skills"` (the corpus root) and never consulted `suite_root`;
   it predates this cycle and worked only while the two roots coincided, so
   post-move both hooks reported `.: [structure] skills/ directory not found`
   and every per-skill rule silently stopped running. `skills` and `agents`
   bind to the **suite** root per §4's table. The binding is fixed in
   `check_structure()`, `check_size()` and the `skills/…` / `agents/…` bases of
   `resolve_backtick_path()` (the same class, same table; `docs/spec/…` stays
   corpus-bound), with a checked-in self-test case
   `check_structure_binds_to_the_suite_root` proving it under nested roots and
   carrying its own inversion. *Added post-plan, found by the Chunk 5
   verification* — traces to `two-root-linter.md` §3, §4
12. [x] [implement] **The stale `exclude:` regex.** `.pre-commit-config.yaml`
   still spelled `tools/fixtures/`; the fixtures live at
   `plugins/sdd/tools/fixtures/`, so upstream hygiene hooks could rewrite bytes
   those fixtures need frozen. Re-spelled. *Added post-plan, found by the Chunk
   5 verification* — traces to `pre-commit.md` §Two-Root Amendment
13. [x] [implement] **Spec amendment: `skill_dir_of()`'s root binding.** Neither
   §3 nor §4 of `docs/spec/two-root-linter.md` assigned `skill_dir_of()` a
   root, and that silence produced the regression C3.10 fixed in code. §4 now
   states that it binds to the root the file was walked from — the same rule as
   `rel()` — together with the other `skills`/`agents`-keyed helpers, so a
   future edit cannot silently reintroduce it. *Added post-plan, found by the
   Chunk 5 verification* — traces to `two-root-linter.md` §4
14. [x] [implement] **Q-IMPL for the fifth population line.**
   `--print-population` prints five table lines while §6 states a closed
   four-table enumeration; the Chunk 4 verifier ruled the extra
   `TEMPLATE_PAIRS=4` line a benign deviation from §6's letter requiring a
   record. Minted as `Q-IMPL-PACKAGING-001` in `docs/spec/two-root-linter.md`
   per the deviation protocol (tier 2), reading §6's enumeration as a required
   **subset**. *Added post-plan, found by the Chunk 5 verification* — traces to
   `two-root-linter.md` §6, `deviation-protocol.md`
15. [x] [implement] **Reconcile `C7.3`'s wording with C6.14.** C7.3 said the flag
   "prints the **four** run-time-derived populations", which is false as
   written once the fifth line is recorded. Restated as a superset check naming
   the four required lines and their values, without weakening it to "prints
   something". *Added post-plan, found by the Chunk 5 verification* — traces to
   `two-root-linter.md` §6
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
1. [x] [verify] The zero-argument post-move run: `python3
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
2. [x] [verify] The retarget's **post-move** confirmation. The equal-roots
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
3. [x] [verify] `python3 plugins/sdd/tools/skill-lint.py --print-population` exits 0,
   prints the `corpus: FILES_SWEPT=<n>  policed-areas=<n>` line (asserted by
   **shape**, not number), and prints one run-time-derived line per rule table
   whose set **includes** the four required populations `REQUIRED=40
   VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=13` — each of the four asserted
   present **by name and by that exact value**, so a missing line or a changed
   value fails; the additional `TEMPLATE_PAIRS` line, recorded as
   Q-IMPL-PACKAGING-001 in `two-root-linter.md`, does not (restated at C6.15;
   the pre-C6.14 wording said "the four" and was false as written). This is the one
   place in the corpus where a row population is compared against a number, and
   it is the regression check on Chunk 2 task 3's retarget — traces to
   `two-root-linter.md` §6 (REQ-LINT-PACKAGING-007, REQ-LINT-PACKAGING-004)
4. [x] [verify] **Carried note M3 — the vacuous-glob hole.** The `test -d` guard in
   `marketplace-packaging.md`'s blanket clause does not cover glob-derived empty
   populations: a criterion quantifying over `skills/*/tools/*.py` still passes
   vacuously when the glob derives nothing. Before running the per-pair `cmp` /
   `test ! -L` assertions, **assert the derived population is non-empty**, and
   assert the loss check's two sides separately as the spec spells them
   (`ls plugins/sdd/tools/*.py | wc -l` not less than
   `git ls-tree --name-only <pre-move sha> tools/ | grep -c '\.py$'`) — traces to
   `marketplace-packaging.md` §Acceptance Criteria
5. [x] [verify] The paired retired-filename removal, evaluated post-move: a run-time
   grep of `plugins/sdd/tools/skill-lint.py` for the retired filename returns
   zero matches; the same grep over `docs/spec/skill-namespace-rename.md`
   returns zero matches and that file's tuple lists five names; both tuples have
   five entries and are equal — traces to `skill-namespace-rename.md`
   §Two-Root Amendment (REQ-LINT-PACKAGING-008)
6. [x] [verify] `python3 plugins/sdd/tools/skill-lint.py --self-test` passes (the
   whole named-case runner — the case set is enumerated in
   `two-root-linter.md` §Verification → Automated, which is the single
   authoritative statement of it; this task deliberately does **not** restate
   a count, the earlier "all fourteen cases" wording having drifted from the
   runner, repaired at C8.7) and `pre-commit run --all-files` exits 0 and leaves the
   working tree clean on an immediate second run — traces to
   `two-root-linter.md` §Acceptance Criteria, `pre-commit.md`
7. [x] [verify] Manual: re-run REQ-PKG-MARKETPLACE-010's real-install observation
   against the moved tree, recorded as an observation with its command — traces
   to `two-root-linter.md` §Verification → Manual
8. [x] [verify] **The no-pinned-count greps, re-run at the post-move path.** The
   three greps of C4.2, verbatim, over `plugins/sdd/tools/skill-lint.py` — the
   path at which REQ-LINT-PACKAGING-004's acceptance is written, and the first
   point in the plan at which that file exists. Each returns zero matches. The
   file must be confirmed present (`test -f`) **before** the greps run, so a
   missing-file exit 2 cannot be read as "empty" — traces to
   `two-root-linter.md` §6 (REQ-LINT-PACKAGING-004)
9. [x] [implement] **The §Acceptance Criteria bullet that is literally false.**
   *Provenance*: added at Chunk 7 on the Chunk 6 verifier's advisory finding.
   C6.14 recorded the fifth `--print-population` line as
   `Q-IMPL-PACKAGING-001` and C6.15 repaired the plan's C7.3, but the Approved
   bullet in `two-root-linter.md` §Acceptance Criteria still read "prints the
   **four** run-time-derived populations" while the flag prints five — true
   only by cross-referencing the Q-IMPL, which a criterion must not require.
   Restate the bullet as an explicit **required-subset** check naming the four
   by name and exact value (`REQUIRED=40`, `VERSION_GATED=9`,
   `V4_CONTRACT=7`, `FORBIDDEN=13`), citing `Q-IMPL-PACKAGING-001` for the
   further lines. Not weakened to "prints something": a missing line or a
   changed value still fails — traces to `two-root-linter.md` §6,
   §Acceptance Criteria (REQ-LINT-PACKAGING-007)
**C7.7 recorded observation (orchestrator-run, 2026-09-21).** The leaf could not
perform this — a non-interactive subagent has no slash commands and
`~/.claude/plugins` is sandbox write-denied — so the orchestrator ran it, as
`RS-PACKAGING-002` did, into a throwaway `CLAUDE_CONFIG_DIR`. Command:
`CLAUDE_CONFIG_DIR=<tmp> claude plugin marketplace add <repo>` then
`claude plugin install sdd@sdd-commons`, against local HEAD `7be5b63`. Result:
the cache root materialised as exactly `agents/ skills/ tools/` — the
`plugins/sdd` segment stripped and **no `docs/`**, versus `agents/ skills/
tools/ docs/ CLAUDE.md CONTRIBUTING.md LICENSE README.md` from `main`. Ten
skills (`implement`…`verify`) and three agents resolved;
`skills/orchestrate/references/loop-control.md` (806 lines) was read from the
installed copy. Installed file count **50**, against **199** pre-move. The
global install still shows the pre-move shape, correctly: its marketplace
tracks `main`, where the move is unmerged.

**Entry criteria**: Chunk 6 complete.
**Exit criteria**: Every after-the-move criterion across the 22 requirements has
been evaluated against the moved tree, with its result recorded.

### Chunk 8: Implement-stage repairs

**Depends on**: Chunk 7.

*Provenance*: every task below comes from the **implement-stage review** of the
packaging cycle (verdict REJECT, iteration 1 of 3), which found that the
Chunk 6/7 rebinding of `check_structure()` and `check_size()` from `self.root`
to `self.suite_root` had turned `python3 plugins/sdd/tools/gc.py --self-test`
red at `581a81e` — a tool no gate in this cycle ran. These are repairs to
committed work, not new scope.

1. [x] [implement] **Bind `check_structure()` and `check_size()` to the
   swept-root union.** Both take `swept_roots()` — the set `walk()`, `rel()`
   and `skill_dir_of()` already use — and render through the per-root `rel()`,
   never `self.suite_root` alone. Three consequences close together: `gc.py
   --self-test` returns to exit 0; the checks stop being a silent third and
   fourth exception to `REQ-PKG-PACKAGING-005`, which puts frontmatter and
   size on the **corpus** root with exactly two stated exceptions; and the
   uncaught `ValueError` that `rel()`'s final `relative_to(self.corpus_root)`
   raised on the first such finding under **disjoint** roots is gone
   (reproduced before the fix against an empty corpus + a disjoint suite
   holding one oversized, name-mismatched skill; neither check raises after)
   — traces to `two-root-linter.md` §2, §4 (REQ-PKG-PACKAGING-005,
   REQ-PKG-PACKAGING-002)
2. [x] [implement] **The invertible size case the check never had.** Land
   `check_size_binds_to_the_swept_roots` in the self-test runner: a **nested**
   half asserting the oversized `SKILL.md` at each of two distinct roots is
   measured, and a **disjoint** half asserting exactly the corpus root's is —
   the geometry `gc.py`'s frozen shim constructs. `_run_capture()` sets both
   roots equal, so every pre-existing size fixture is geometry-blind and stays
   green under either wrong binding; both mutations (`self.suite_root` alone,
   `self.corpus_root` alone) were run and both fail this case — traces to
   `two-root-linter.md` §Verification → Automated (REQ-PKG-PACKAGING-005)
3. [x] [implement] **Make the duplicate-freeness guard's observable reachable
   under `--print-population`.** That mode called the union builder, which runs
   the guard, and then discarded the findings, so the one mode `REQ-LINT-
   PACKAGING-005` says cannot skip the observable was the one mode that did.
   `print_population()` now prints its own findings and exits non-zero on a
   `fail`; `sweep_is_duplicate_free` is strengthened from "`_guard_done`
   flipped" to driving a duplicate-yielding walk through that mode and
   requiring the finding on stdout. Recorded as `Q-IMPL-PACKAGING-003` —
   traces to `two-root-linter.md` §6 (REQ-LINT-PACKAGING-005)
4. [x] [implement] **The four populations, asserted durably.**
   `print_population_shape` compared the flag's output against
   `population_tables()` — the same live tables — so it passed for any row
   count, and §6's `REQUIRED=40 VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=13`
   was compared exactly once, at C7.3. §6 calls that comparison a regression
   check on §3's retarget; one that cannot be re-run is not one. The four
   value assertions are now in the case — traces to `two-root-linter.md` §6
   (REQ-LINT-PACKAGING-007, REQ-LINT-PACKAGING-004)
5. [x] [implement] **Mint the Q-IMPL for the `retired_scope_entries()`
   substitution.** `REQ-PKG-PACKAGING-002`'s "sweeps at least one `docs/spec/`
   path" is unsatisfiable against `walk()` as §2 defines it; C7.1 closed it by
   asserting on `retired_scope_entries()` instead, recorded only in a commit
   body. Recorded as `Q-IMPL-PACKAGING-002` — traces to `two-root-linter.md`
   §2, §Implementation Questions (REQ-PKG-PACKAGING-002)
6. [x] [implement] **Resolve the frozen-`gc.py` caller conflict.** `gc.py`'s
   shim passes a corpus root only while `REQ-PKG-MARKETPLACE-007` freezes its
   source. Resolution: the freeze holds and `gc.py` is **not** edited — under
   the union binding of task 1 the single-root call is sound, because a
   disjoint suite root is excluded from `swept_roots()` and so unreachable by
   any ungated check. The invariant a future edit must preserve — *no ungated
   check binds to `self.suite_root` alone* — is recorded as
   `Q-IMPL-PACKAGING-004` — traces to `two-root-linter.md` §2,
   §Implementation Questions (REQ-PKG-MARKETPLACE-007)
7. [x] [implement] **Reconcile the self-test case count (M1).** Three
   statements disagreed: `two-root-linter.md` §Verification said twelve, C7.6
   said fourteen, the runner invoked seventeen. §Verification is now the single
   authoritative statement — the runner tuple **is** the enumeration and no
   number is pinned in prose — C7.6 points at it, and the one design-time name
   never landed (`zero_arg_run_sweeps_the_corpus`) is recorded there rather
   than left as a silent gap — traces to `two-root-linter.md` §Verification
8. [x] [implement] **`<plugin-dir>` as a stated convention (M2).**
   `verify/SKILL.md`'s gc criterion writes `<plugin-dir>` where
   `orchestrate/SKILL.md` writes `<skill-dir>`. One sentence in
   `two-root-linter.md` §8 states the convention — `<plugin-dir>` for the whole
   installed plugin root, `<skill-dir>` for one skill's own directory — so the
   two read as different referents rather than a divergence — traces to
   `two-root-linter.md` §8 (REQ-PKG-PACKAGING-009)
9. [x] [implement] **Close the gate hole (S5) and repair the stale remediation
   text (M3).** `CONTRIBUTING.md` §The three heavier checks gains a trigger row:
   touching `skill-lint.py` **or** `gc.py` requires running **both**
   `--self-test`s, with the reason (`gc.py` embeds the linter; the gate runs
   `gc.py --fast`, a corpus sweep that exercises no two-root fixture geometry).
   `gc.py --self-test` is **not** added to `.pre-commit-config.yaml`: not for
   cost (1.6s), but because `REQ-PC-MARKETPLACE-004`'s Approved acceptance pins
   a `--self-test` grep of that config at zero matches, already verified pass —
   amending it is a requirements change outside this packet. `check_structure()`'s
   remediation string ("run the linter from the repo root or pass REPO_ROOT")
   is replaced: `REPO_ROOT` no longer exists and the advice is wrong after the
   cwd/two-root change — traces to `pre-commit.md`, `two-root-linter.md` §2

**Entry criteria**: Chunk 7 complete; the implement-stage review returned REJECT.
**Exit criteria**: all four of `skill-lint.py --self-test`, `skill-lint.py`,
`gc.py --self-test` and `gc.py --fast` exit 0, each observed and recorded; every
review finding is either applied or recorded as a Q-IMPL with its resolution.

### Chunk 9: Implement-stage repairs, round 2

**Depends on**: Chunk 8.

*Provenance*: every task below comes from the **implement-stage review, round 2**
(iteration 2 of 3) of the packaging cycle. Round 1's review found `check_size()`
had no test that caught its own reversion; round 1's repair diagnosed exactly
that and then shipped two sibling bindings with the same hole. Round 2 proved it:
three separate mutations that revert load-bearing bindings left all four gates
green. The standard for this chunk is therefore not "the gates are green" — they
already were — but that **reverting any binding or default it touches makes a
gate fail**, demonstrated by running the mutation. Five mutations were run; all
five now fail `skill-lint.py --self-test`, and the `check_size()` one additionally
fails `gc.py --self-test`. These are repairs to committed work, not new scope.

1. [x] [implement] **Rebuild the vacuous structure case (B1-r2).**
   `check_structure_binds_to_the_suite_root` was vacuous against the binding it
   named: the fixture seeded skills only under the suite and gave the corpus
   root nothing but `docs/`, so the suite binding and the union binding were
   indistinguishable, and its "INVERSION" swapped the *fixture's* roots rather
   than the implementation's binding — proving only that a root with no
   `skills/` yields the not-found finding, true under every binding. Renamed
   `check_structure_binds_to_the_swept_roots` (M1-r2) and given the shape
   `check_size_binds_to_the_swept_roots` has: a corpus root that also holds a
   `skills/` tree with its own seeded frontmatter violation, asserted present,
   plus a disjoint half that must not raise out of `rel()`. Docstring corrected
   — it claimed §4 puts `skills` on the suite root. Mutation `roots =
   [self.suite_root]` now fails the case on both halves — traces to
   `two-root-linter.md` §4, §Verification (REQ-PKG-PACKAGING-005)
2. [x] [implement] **Land `zero_arg_run_sweeps_the_corpus` (B2-r2).** The cwd
   default had no guard at all: mutating it to `default_suite_root().resolve()`
   left both self-tests at 0. `REQ-PKG-PACKAGING-002` states of this exact
   mis-rooting that nothing downstream can distinguish it from a correct run and
   names a self-test case as the only guard; round 1 recorded the gap instead of
   closing it. The case drives `main()`'s real argument path — argv with no
   positional, cwd chdir'd to a fixture corpus, the constructed `Linter`
   captured — and asserts `swept_roots()[0]` resolves to the fixture and not to
   `default_suite_root()` — traces to `two-root-linter.md` §2, §Verification
   (REQ-PKG-PACKAGING-002)
3. [x] [implement] **Make `Q-IMPL-PACKAGING-004`'s invariant true (S1-r2).** It
   states that no ungated check binds to `self.suite_root` alone; `check_links()`
   is ungated and `resolve_backtick_path()` bound two bases to the suite root
   alone. No crash — the finding names the swept file, not the base — but in the
   disjoint consumer geometry that resolves a consumer's own
   `skills/…/references/…` span against the installed plugin cache: a false pass
   when the cache holds the path, a phantom failure when it does not. The union
   is applied (`Linter.swept_base()`, corpus-first, deepest swept root as the
   fallback for an unresolvable path) rather than the invariant carved out, since
   §4's C6.13 paragraph already places those bases under the same binding.
   Q-IMPL-PACKAGING-004 records that the invariant was false and is now true.
   New case `backtick_bases_bind_to_the_swept_roots` — traces to
   `two-root-linter.md` §4, §Implementation Questions (REQ-PKG-MARKETPLACE-007,
   REQ-PKG-PACKAGING-005)
4. [x] [implement] **Both self-tests on the commit gate (S2-r2).** The reason
   recorded in Chunk 8 task 9 for keeping `gc.py --self-test` off the gate —
   that `REQ-PC-MARKETPLACE-004` pins a `--self-test` grep of the config at zero
   — was **factually wrong**: that requirement's acceptance greps for the three
   contributor tool *names*, and neither new entry is one of them. Hook entries
   `skill-lint-self-test` and `drift-sweep-self-test` added; the three-name grep
   re-run after adding and still 0 for all three (the config comment deliberately
   does not spell the three names, so the comment cannot itself turn the grep
   non-zero). `CONTRIBUTING.md`'s reasoning corrected in place rather than
   deleted — traces to `pre-commit.md` (REQ-PC-MARKETPLACE-004)
5. [x] [implement] **Restate §4's self-contradicting paragraph (S3-r2).**
   `two-root-linter.md` §4 said the same binding governs `check_structure()` and
   `check_size()` "which §4's table already places on the **suite root**" and
   then warned only against re-binding to the corpus root — while the code
   unions. Restated for the union with the no-corpus-root-alone warning kept as
   an explicit second clause, both clauses load-bearing. This paragraph is the
   most likely cause of a future reintroduction of B1 — traces to
   `two-root-linter.md` §4
6. [x] [implement] **Pin `walk()`'s deduplication against production (S4-r2).**
   Deleting the dedupe loop left all gates green: `swept_roots()` appends the
   suite term only `if suite != corpus`, so equal roots yield one walk term and
   concatenation can produce no duplicate, §7's Case C premise is unrealisable
   against this implementation, and both negative cases use hand-built lists.
   New case `walk_dedupes_repeated_roots` monkeypatches `swept_roots()` to
   return `[r, r]` and asserts `walk()` returns each path once and the guard
   stays silent; §6 and §7 now say what each construct actually pins — traces to
   `two-root-linter.md` §6, §7 (REQ-LINT-PACKAGING-005, REQ-PKG-PACKAGING-008)
7. [x] [implement] **Name the broken contract instead of a traceback (M2-r2).**
   Under the suite-only `check_size` mutation the disjoint half surfaced as an
   uncaught `ValueError` that aborted the runner. Both disjoint halves
   (`check_size`, `check_structure`) now catch it and report a named `check()`
   failure — traces to `two-root-linter.md` §2
8. [x] [implement] **Rename the heavier-checks heading (M3-r2).**
   `CONTRIBUTING.md` §The three heavier checks → §The heavier checks, run
   explicitly, and the two citations this cycle already edited updated
   (`CLAUDE.md` §Quality Checks, `docs/spec/project-docs.md` items 3 and
   Q-IMPL-MARKETPLACE-018). **For verify's `## Next Steps`:**
   `docs/requirements/integration/project-docs.md:79` carries the same "three
   heavier checks" phrase and is out of this packet's write scope — a
   requirements edit, not an implement-stage one — traces to `project-docs.md`

**Entry criteria**: Chunk 8 complete; the implement-stage review returned REJECT
at round 2 with three reverted-binding mutations demonstrated green.
**Exit criteria**: all four gates exit 0 before and after; each of the five
named mutations applied in turn, the failing gate and its message recorded, and
the tree restored; `pre-commit run --all-files` passes with the two new hooks.

### Chunk 10: Implement-stage repairs, round 3

**Depends on**: Chunk 9.

*Provenance*: every task below comes from the **implement-stage review, round 3**
(iteration 3 of 3 — the last) of the packaging cycle, following the pattern the
round-3 reviewer endorsed for Chunk 9. Round 2's repairs held: all five
mutations it recorded were re-run here and all five still fail a gate. Round 3's
blocking finding was the orchestrator's own: round 2 added two self-test hooks
to `.pre-commit-config.yaml` after checking `REQ-PC-MARKETPLACE-004`'s
three-name grep and **not** `REQ-PC-MARKETPLACE-001`, which closes the hook set
— parsed ids became 8 against a required union of 6. The operator's decision was
to keep the hooks and amend the requirement and the spec, the two self-tests
being the control that catches this cycle's defect class. The rest of the chunk
closes five further unguarded bindings and states one boundary the four-gate
harness cannot observe. The standard is Chunk 9's, unchanged: **reverting any
binding, default or dedupe this chunk touches must fail a gate**, demonstrated
by running the mutation. Task numbers are the `C10.<n>` refs used in
`docs/ws/packaging/traceability.md`. These are repairs to committed work, not
new scope.

1. [x] [implement] **Pin `check_structure()`'s `seen_dirs` dedupe (B2b, first of
   two).** The file carries **four** deduplications, not one; §6's amended
   paragraph covered only `walk()`'s. (*Corrected 2026-09-21, round 4*: this
   task said **three**. The fourth, in `retired_scope_entries()`, is unpinned
   and recorded as an open finding in §Chunk 11 below.) `seen_dirs` was deletable with all four
   gates green, the deletion re-reporting every skill directory once per
   repeated root. New case `check_structure_dedupes_repeated_roots`, the
   `walk_dedupes_repeated_roots` shape (monkeypatch `swept_roots()` to `[r, r]`,
   the only path from production to the loop) — traces to `two-root-linter.md`
   §6 (REQ-LINT-PACKAGING-005)
2. [x] [implement] **Pin `check_size()`'s `seen_size` dedupe (B2b, second of
   two).** Same hole, same shape; new case
   `check_size_dedupes_repeated_roots` — traces to `two-root-linter.md` §6
   (REQ-LINT-PACKAGING-005)
3. [x] [implement] **Pin `swept_base()`'s two documented properties (B2c).**
   The docstring asserts corpus-first resolution order and deepest-root
   fallback as deliberate, and neither was guarded:
   `backtick_bases_bind_to_the_swept_roots` uses fixtures in which at most ONE
   swept root holds the span, so the tiebreak never fires. New case
   `swept_base_order_and_fallback` seeds the same relative path under **both**
   roots of a nested geometry so the order decides, and asks for a path under
   neither so the fallback decides. Pinned rather than softened — traces to
   `two-root-linter.md` §4 (REQ-PKG-PACKAGING-005)
4. [x] [implement] **Pin `rel()`'s and `skill_dir_of()`'s documented raise
   (S1).** `rel()`'s docstring says a path under no swept root raises
   `ValueError` "exactly as the former single-root rendering did", and
   `flag()`'s docstring leans on that raise to explain why a per-entry-bound
   check must supply its own rendering; `skill_dir_of()` states the same. New
   case `rel_raises_outside_the_swept_roots` drives both against a disjoint
   geometry. Pinned rather than softened. *Corrected 2026-09-21 (round 4)*:
   this task originally recorded that mutating `rel()`'s root set to suite-only
   "remains survivable" and is behaviour-preserving. **That is false** — the
   mutation `roots = [self.suite_root]` was run and is killed by
   `rel_raises_outside_the_swept_roots` itself (`SELF-TEST FAIL: - rel() must
   raise ValueError on a path under no swept root, as its docstring states;
   got skills/outside/SKILL.md`). The mutant errs conservatively, so coverage
   is better than was claimed, and the case pins `rel()`'s union binding as
   well as its documented raise — traces to `two-root-linter.md` §2
   (REQ-PKG-PACKAGING-002)
5. [x] [implement] **Pin `suite_contained()`'s equality clause (S2).** §2 states
   equality counts as containment, and `check_links()` reads the predicate to
   decide whether the `TEMPLATE_PAIRS` spec side is checked at all. New case
   `equal_roots_count_as_contained` pins the property. *Recorded, not claimed*:
   deleting the `suite == corpus or` disjunct still survives and **cannot** be
   killed — `Path(p).is_relative_to(p)` is already `True`, so the disjunct is
   redundant with the clause beside it and its deletion is behaviour-preserving.
   The case docstring says so rather than implying an invertibility it does not
   have — traces to `two-root-linter.md` §2 (REQ-PKG-PACKAGING-002)
6. [x] [implement] **Close `zero_arg_run_sweeps_the_corpus`'s other half
   (Minor).** The case asserted only the corpus root; the suite root's default
   to `default_suite_root()` was unasserted, and mutating it to the cwd left
   the case green. Asserted, and the `built: list[Linter]` annotation — which
   referenced the name the case rebinds — quoted — traces to
   `two-root-linter.md` §2 (REQ-PKG-PACKAGING-002)
7. [x] [implement] **Make requirement, spec and config agree on a closed set of
   eight (B1, blocking).** `REQ-PC-MARKETPLACE-001` amended in place with a
   dated note naming the authorising context: the set is eight, one `--self-test`
   hook per repository tool, and the acceptance's union is restated so **both**
   sides are still derived by parsing — the local set is derived from each
   parsed `entry`'s script, each tool appearing exactly twice. No renumbering, no
   history rewrite. `docs/spec/pre-commit.md` amended through its own
   §Two-Root Amendment mechanism: a new **§Hook-Set Amendment** records the move
   and puts its rationale beside the declined `cmp` candidate (proportionality
   measured against how often the guarded property can break), and §The hook
   set's heading, count sentence, table and the §Acceptance Criteria bullet are
   reconciled so no reader is told six by one and eight by another. Both checks
   re-run: parsed ids == derived union (8 == 8), `validate-config` exit 0, and
   `REQ-PC-MARKETPLACE-004`'s grep still 0/0/0 — traces to `pre-commit.md`
   (REQ-PC-MARKETPLACE-001)
8. [x] [implement] **State the `warn` severity class as a boundary (B2a).**
   Rebinding `resolve_backtick_path()`'s `docs/spec/…` base to the suite root
   yields **136 spurious `[path]` warnings and exit 0 on all four gates** — the
   third row of §4's table, whose other two rows this cycle unioned and pinned.
   Making the class gateable means changing the linter's exit contract, which is
   out of scope on the last iteration. Recorded instead in
   `two-root-linter.md` §Verification as an explicit stated boundary: what it
   exempts, why the harness cannot observe it, the technique available to a
   future case, and that it is a known limitation — traces to
   `two-root-linter.md` §4, §Verification
9. [x] [implement] **Correct §6's amended paragraph and pin
   `REQ-PC-MARKETPLACE-004`'s grep strings (B2b prose, S3).** §6 read as though
   deduplication in this file were closed; it covered one of three, now stated.
   `REQ-PC-MARKETPLACE-004`'s acceptance said "each of the three tool names"
   while the prose names them in short form and the config comment spells those
   short forms — 0/0/0 under one reading, 1/1/1 under the other. The three
   **script filenames** are pinned as the grep strings in both the requirement
   and the spec's criterion, so it has one truth value — traces to
   `two-root-linter.md` §6, `pre-commit.md` (REQ-LINT-PACKAGING-005,
   REQ-PC-MARKETPLACE-004)
10. [x] [implement] **Catch traceability and the coverage table up (S4).**
   `docs/ws/packaging/traceability.md` was last written at Chunk 6 and missed
   chunks 7–10. Rows extended for `REQ-PKG-PACKAGING-002` (whose evidence cell
   cited C1/C3 cases while the case its acceptance names landed at C9.2),
   `REQ-LINT-PACKAGING-005`, `REQ-PKG-PACKAGING-005`, and rows added for
   `REQ-PC-MARKETPLACE-001` and `REQ-PC-MARKETPLACE-004`, whose evidence this
   workstream delivered. §Requirement → Task Coverage below extended with the
   `C8.*` / `C9.*` / `C10.*` refs under its own rule — the owning task is the
   one that lands the checked-in case — traces to `ws-traceability.md`
11. [x] [implement] **Forward pointer on the stale YAML sample (Minor).**
   `pre-commit.md` §The two local hooks shows un-prefixed, two-entry YAML 240
   lines before the two corrections; a bracketed note now names both amendments
   and says to read the sample as the shape of a local entry, not the entry set
   — traces to `pre-commit.md`

**Entry criteria**: Chunk 9 complete; the implement-stage review returned REJECT
at round 3 with one blocking finding (the orchestrator's own hook-set error),
two further blocking items and four suggestions.
**Exit criteria**: all four gates exit 0 before and after; `pre-commit run
--all-files` passes; the parsed-hook-id set equals the derived union and
`REQ-PC-MARKETPLACE-004`'s three-filename grep is 0/0/0; every mutation this
chunk's pins target applied in turn with the failing gate and its message
recorded, plus the five round-2 classes re-run and still killed; any surviving
mutation reported as a finding rather than claimed as a repair.


### Chunk 11: Recorded open findings — carried to verify (no tasks)

**This section contains no tasks.** It is a record, written by the round-4
text-only correction pass (2026-09-21, operator-authorised extra iteration),
of gaps that were measured and left unrepaired because closing any of them
needs new test code or an exit-contract change — neither of which that pass
was authorised to make. Nothing here is to be ticked; each item carries the
mutation that demonstrates it so the verify stage, or a later cycle, does not
have to rediscover it.

1. **`check_retired_prefix()`'s `rel=Path(rel)` argument is unpinned.** Highest
   value of the three. Reverting the `rel=Path(rel)` clause at
   `plugins/sdd/tools/skill-lint.py:1163` survives all four gates
   (`skill-lint.py`, `skill-lint.py --self-test`, `gc.py --fast`,
   `gc.py --self-test`, all exit 0) and raises `ValueError` in the disjoint
   consumer geometry, where the entry's file lies under no swept root of the
   default rendering. The rule's finding severity is `fail` — so the breakage
   is gateable in principle — and `two-root-linter.md` §4 calls the clause
   load-bearing. Closing it is one new self-test case driving
   `check_retired_prefix()` against the disjoint geometry and asserting no
   raise.

2. **`main()`'s `print_population(root, default_suite_root())` wiring is
   unpinned.** Mis-rooting the call to `print_population(root, root)` reports
   `FILES_SWEPT=0` with exit 0 on every gate — the same mis-rooting class
   `REQ-PKG-PACKAGING-002` describes, and the same one C9.2/C10.6 closed for
   the `Linter` half of the identical wiring in `main()`. Only the `Linter`
   half is pinned; the `print_population()` half is not.

3. **The fourth deduplication, `retired_scope_entries()`'s `seen` set, is
   unpinned.** Deleting the `if key in seen: return` / `seen.add(key)` guard in
   its `add()` helper survives all four gates. It is reachable from production
   by the technique C10.1/C10.2 use — monkeypatching the union source,
   `lin.retired_scope_roots = lambda e: [d, d]`, which yields 1 finding with
   the guard and 2 without. Recorded in `two-root-linter.md` §6 as well; C10.1
   and C10.2's prose said *three* deduplications and now says *four*.

4. **The `warn` severity class stays exempt, as §Verification records it.**
   Unchanged from C10.8: rebinding `resolve_backtick_path()`'s `docs/spec/…`
   base to the suite root yields 136 spurious `[path]` warnings with exit 0 on
   all four gates, because no gate reads warning counts. Closing it means
   changing the linter's exit contract, which is out of scope for this cycle
   and is carried as a stated boundary rather than as work.


### Chunk 12: Red-team repairs

**Provenance.** The verify stage ran with the red team enabled and returned
`RED_VERDICT: BROKEN` — three breaks against the acceptance criteria this
cycle wrote (R2 Major, R3 Moderate, R1 Minor), plus one suspicion the round
did not claim as a break (the AC5 bare-`tools/gc.py` grep). The operator chose
**fix** for all three and **judge** for the suspicion. Reproductions and
dispositions are recorded in `docs/ws/packaging/verification.md` §Issues Found;
`status:` there stays `pending-red` until the orchestrator's flip.

1. [x] [implement] **R2 — re-point orchestrate's drift-sweep invocations at
   `<plugin-dir>/tools/gc.py`.** All eight `<skill-dir>/tools/gc.py` spellings
   in `plugins/sdd/skills/orchestrate/` (`SKILL.md` ×2, `USAGE.md` ×2,
   `references/drift-sweep.md` ×4) become `<plugin-dir>/tools/gc.py`, matching
   what C6.1 did for `verify/SKILL.md`, and the two prose passages that
   justified the skill-relative spelling are rewritten to the `<plugin-dir>`
   convention. The bundled copy under `skills/orchestrate/tools/` is **not**
   deleted — REQ-PKG-MARKETPLACE-007 freezes it and
   REQ-PKG-MARKETPLACE-006's duplicated-not-symlinked rule governs its fate.
   [Superseded 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-005: the bundled copy was removed; this observation was true at 0bdb076]
   Verified the way the break was found: from a scratch consumer repository
   with no `tools/` of its own, the re-pointed command exits 1 with findings
   naming **consumer** paths, while the old spelling still exits 2 with
   `error: linter missing` (REQ-PKG-PACKAGING-009)
2. [x] [implement] **R3 — pin `check_required()`'s two gated loops to the
   suite root.** New checked-in self-test case
   `check_required_gated_rows_bind_to_the_suite_root`, in the shape C8.1/C8.2
   use: a nested fixture whose two roots differ, the gated rows' targets
   present **only** under the suite root, a positive control carrying both
   markers, and a decoy seeded under the corpus root. Rebinding either loop to
   `self.corpus_root` fails three of the case's four assertions, so the
   reversion is gated where before it was a silent no-op across all sixteen
   rows (REQ-LINT-PACKAGING-002, REQ-PKG-PACKAGING-004)
3. [x] [implement] **R3 — correct `two-root-linter.md` §6 on what the four
   pinned populations catch.** The claim that they are "a regression check on
   §3's retarget, catching a row dropped or duplicated while moving the rows'
   binding" is false in its second half and is withdrawn: a population is
   `len(<table>)` and a retarget leaves every row in place. §6 now states that
   they catch **table** edits only, that bindings are pinned by the invertible
   geometry cases instead, and names task 2's case as the one covering these
   sixteen rows (REQ-LINT-PACKAGING-004, -007)
4. [x] [implement] **R1 — restate the no-pinned-count exclusion as a class.**
   `two-root-linter.md` §Verification and this plan's Chunk 4 task 2 excluded
   "fixtures A, B and case C" by name; the first grep now also matches
   `walk_dedupes_repeated_roots`'s `check(len(swept) == 1, …)`, a sound literal
   over a hand-built root list that the enumeration does not name, so the
   criterion was false as written. The exclusion is now the **class** of
   self-test fixture-literal assertions — a count over a tree the case seeded
   itself or over a hand-built literal path list — with everything else,
   including any count over a live corpus root, still a finding. Re-run: grep 1
   returns the one excluded match, greps 2 and 3 return none
   (REQ-LINT-PACKAGING-004)
5. [x] [implement] **AC5 suspicion — correct the criterion's wording, not the
   strings.** The bare `tools/gc.py` occurrences in
   `orchestrate/{SKILL.md,USAGE.md,references/drift-sweep.md}` are the `GC:`
   gate line the driver **prints**, whose wording `docs/spec/drift-sweep.md`
   owns; they are not invocations, and the criterion read as a literal grep was
   always false. AC5 now defines an invocation as a command line the body tells
   the reader to run and puts rendered messages out of scope. `gc.py`'s
   `AGG_FIX` string is the one a consumer would paste and names a path no
   consumer has — a real defect, but `gc.py` is frozen to this cycle's write
   scope, so it is **recorded** against REQ-PKG-PACKAGING-009 for a later cycle
   rather than repaired (REQ-PKG-PACKAGING-009)

**Standard held.** For every binding this chunk touches, the reversion fails a
gate: task 2's mutation turns `skill-lint.py --self-test` red (failure text in
`verification.md` §Issues Found → R3). All four gates — `skill-lint.py`,
`skill-lint.py --self-test`, `gc.py --fast`, `gc.py --self-test` — were exit 0
before this chunk and are exit 0 after it.

[Superseded 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-005: the bundled copy was removed; this observation was true at 0bdb076]

**Consequence to carry forward.** After task 1, **no invocation anywhere
resolves to the bundled copy** under `skills/orchestrate/tools/`. That
falsifies the added criterion `docs/ws/marketplace/verification.md` records for
REQ-PKG-MARKETPLACE-006 ("at least one invocation resolves to the bundled
copy"). The copy stays on disk under that requirement's duplication rule; the
marketplace workstream's record is out of this workstream's write scope and is
left for the operator.

## Requirement → Task Coverage

All 22 approved requirements, each mapped to the tasks that reach it, plus the
three `REQ-PC-MARKETPLACE-*` rows this workstream delivered evidence for at
chunks 9 and 10. This table
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
| REQ-PKG-PACKAGING-002 | two-root-linter.md | C1.1, C1.2, C1.3, C1.6, C1.7 (`two_roots_construct_distinct_and_equal`, `equal_roots_sweep_set_unchanged`, `sweep_is_duplicate_free`), C7.1, **C9.2** (`zero_arg_run_sweeps_the_corpus` — the case the acceptance names), **C10.6** (its suite-default half), **C10.4** (`rel_raises_outside_the_swept_roots`), **C10.5** (`equal_roots_count_as_contained`) |
| REQ-PKG-PACKAGING-003 | two-root-linter.md | C1.5, C7.1 |
| REQ-PKG-PACKAGING-004 | two-root-linter.md | C2.3, C2.5, **C2.6** (equal-roots comparison vs the **pre-change baseline** of C0.1), C7.2 (post-move confirmation) |
| REQ-PKG-PACKAGING-005 | skill-lint-v5.md | C6.3, C6.6, C8.1, **C8.2** (`check_size_binds_to_the_swept_roots`), **C9.1** (`check_structure_binds_to_the_swept_roots`), **C9.3** (`backtick_bases_bind_to_the_swept_roots`), **C10.3** (`swept_base_order_and_fallback`) |
| REQ-PKG-PACKAGING-006 | two-root-linter.md | C3.1, C3.7 |
| REQ-PKG-PACKAGING-007 | two-root-linter.md | C3.2, C3.7 |
| REQ-PKG-PACKAGING-008 | two-root-linter.md | C3.4, C3.5, C3.8 |
| REQ-PKG-PACKAGING-009 | two-root-linter.md | C6.1, C6.6, **C6.8** (scratch consumer repository) |
| REQ-PKG-PACKAGING-010 | marketplace-packaging.md | C5.3, C5.6 |
| REQ-LINT-PACKAGING-001 | two-root-linter.md | C2.1, C2.4 (`retired_scope_binds_per_entry`), C1.7 |
| REQ-LINT-PACKAGING-002 | two-root-linter.md | C2.2, **C3.9** (`template_pairs_bind_per_side`, three geometries + the both-sides-to-suite negative control) |
| REQ-LINT-PACKAGING-003 | two-root-linter.md | C3.3 |
| REQ-LINT-PACKAGING-004 | two-root-linter.md | C4.1, C4.2 (three greps, **pre-move** `tools/skill-lint.py`), C7.3, **C7.8** (same three greps, **post-move** `plugins/sdd/tools/skill-lint.py`) |
| REQ-LINT-PACKAGING-005 | two-root-linter.md | C1.4, C1.7 (`sweep_is_duplicate_free`), C3.5, C3.8, **C9.4** (`walk_dedupes_repeated_roots`), **C10.1**, **C10.2** (the other two deduplications) |
| REQ-LINT-PACKAGING-006 | two-root-linter.md | C3.6, C3.7 |
| REQ-LINT-PACKAGING-007 | two-root-linter.md | C4.1, **C4.3** (`print_population_shape`), C7.3 |
| REQ-LINT-PACKAGING-008 | skill-namespace-rename.md | C0.2, C0.4, C7.5 |
| REQ-PC-PACKAGING-001 | pre-commit.md | C5.4, C5.7, **C5.8** (membership: the entry run verbatim sweeps a `docs/spec/` path), C7.6 |
| REQ-PC-MARKETPLACE-001 | pre-commit.md | C9.4 (the two self-test hooks), **C10.7** (closed set amended to eight; parsed ids == derived union) |
| REQ-PC-MARKETPLACE-004 | pre-commit.md | C9.4 (three-name grep re-run), **C10.9** (grep strings pinned to the three script filenames) |
| REQ-PC-MARKETPLACE-006 | pre-commit.md | **C10.7** (re-checked against the amended eight-hook set: every entry one of the eight, no `args:` key; supersedes the `marketplace` row's six-entry assertion) |
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
