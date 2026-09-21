---
workstream: packaging
status: pass
research_id: RS-PACKAGING-003
last_updated: 2026-09-21
plan_ref: docs/ws/packaging/plan.md
---

# Verification Report — workstream `packaging`

## Summary

Blue verification passes. All 22 in-scope requirements
(`REQ-PKG-PACKAGING-001..010`, `REQ-LINT-PACKAGING-001..008`,
`REQ-PC-PACKAGING-001`, `REQ-DOCS-PACKAGING-001..003`) were evaluated by
executing the observable each acceptance clause names — not by reading a green
gate — and every one is satisfied. All eight pre-commit hooks and all four
tool gates pass. No regression was found against
`merge-base(packaging, main)` = `0f5ec26`: the 45-file move is recorded as 45
renames with zero adds and zero deletes, and the `.py` population is unchanged
at 7.

`status:` is `pending-red` rather than `pass` because the verify stage was
dispatched with `Red team: enabled`. The red round has not run; the
`pending-red → pass` flip is the orchestrator's.

Five issues are recorded, all Minor, all of one class: **a binding whose
reversion no gate catches.** Four are the findings `plan.md` §Chunk 11 carried
here; all four were reproduced exactly as recorded. A fifth of the same class
was found during this pass (`gc.py`'s `lint_path()` candidate order). None
changes observed behaviour — every one of the five is correct in the shipped
tree, and each was confirmed correct by direct observation. What is missing is
the gate that would catch a future reversion. That is the same defect class the
implement stage's four review rounds kept finding, so the honest reading is
that the cycle **reduced** it rather than closed it, and the report says so
rather than reporting a clean sheet.

## Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| `python3 plugins/sdd/tools/skill-lint.py` | pass | exit 0 — `OK: 25 file(s) clean` |
| `python3 plugins/sdd/tools/skill-lint.py --self-test` | pass | exit 0 — all rule classes fire; fix/warn/size/backtick/allow_files/retired-prefix fixtures pass. All 23 two-root test functions named in `traceability.md` are present **and invoked** (checked: zero declared-but-never-called) |
| `python3 plugins/sdd/tools/gc.py --fast` | pass | exit 0 — `3 sweep(s) clean, 0 warning(s), 28 info` |
| `python3 plugins/sdd/tools/gc.py --self-test` | pass | exit 0 |
| `python3 plugins/sdd/tools/gc.py --report --root .` | pass | exit 0 — `9 sweep(s) clean, 0 warning(s), 36 info`. No `[traceability-aggregate]` warning before this report's own per-ws write |
| `pre-commit run --all-files` | pass | exit 0, **8/8** hooks Passed: drift sweep (fast), skill linter, skill linter self-test, drift sweep self-test, trim trailing whitespace, fix end of files, check yaml, check json |
| Working tree | clean | `git status --porcelain` empty at `6adb25d`; still empty after every mutation below (all mutations were run in a throwaway `git archive` copy under `$TMPDIR`, never in the repository) |

No language toolchain gate (ruff/mypy/pytest) applies: the project's own gates
are the two tools and the commit hook set, per `CLAUDE.md` §Quality Checks.

## Acceptance Criteria

### two-root-linter.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-PKG-PACKAGING-001 — suite moves to `plugins/sdd/`, recorded as a move | pass | `plugins/sdd/` and `plugins/sdd/.claude-plugin/plugin.json` exist; `.claude-plugin/marketplace.json` exists at the corpus root and **not** under the suite; the parsed `source` (`./plugins/sdd`) resolves to the `plugins/sdd` directory; all 13 component-list entries resolve under the suite by `Path.exists()` per entry (0 unresolvable), derived from the parsed manifest, not a written-out list. Per-name membership against the pre-move sha `95c28b7`: 45 names enumerated by `git ls-tree -r --name-only`, **all 45** present under `plugins/sdd/` and **none** surviving at the corpus root. Each of `.claude-plugin/marketplace.json`, `docs/`, `CLAUDE.md`, `.pre-commit-config.yaml`, `README.md`, `LICENSE`, `CONTRIBUTING.md` present at the corpus root. Move commit `e26f81f`: `R`=45, `A`=0, `D`=0. `git log --follow` resolves every one of the 45 to pre-move history (0 files whose follow-history is the move commit alone). No count is asserted in the criterion; the 45 is derived |
| REQ-PKG-PACKAGING-002 — two roots as constructor parameters | pass | `Linter(corpus, suite)` constructs distinct and equal without touching argparse. Zero-arg wiring from the repository root resolves `corpus_root=<repo>`, `suite_root=<repo>/plugins/sdd`, `swept_roots` = both. Swept set derived at run time contains 39 `docs/spec/` members — membership asserted, not exit code. Nested rendering asserted per root by `nested_roots_render_per_root` (negative control run below). `--help` carries no "repo containing this script" claim; `docs/spec/skill-lint-v5.md:613` states the opposite ("No text here may claim the root defaults to the script's own repository") |
| REQ-PKG-PACKAGING-003 — no `--no-suite-rules`, `--suite-root` deferred | pass | `grep -c no-suite-rules` = 0; `grep -c -- --suite-root` = 0. 42 `suite_rules=False` occurrences: 40 inside `self_test()` (lines 1233–2866), one at `:527` which is a **comment**, one at `:1229` inside `_run_capture()`, a self-test-only fixture driver. No production construction site |
| REQ-PKG-PACKAGING-004 — suite-gated rows retarget to the suite root | pass | Ran `Linter(<scratch repo with no skills/>, default_suite_root())`: exit 1, rules fired = `['structure']` only. **Zero** findings from `REQUIRED` / `VERSION_GATED_SKILLS` / `V4_CONTRACT_SKILLS`; the ungated `[structure]` check still reports. Equal-roots finding-set identity is pinned by `--self-test` (`retarget_seeds_an_ungated_finding`, `equal_roots_count_as_contained`), against the Chunk 0 baseline `93b1133` — the substitution for the requirement-pinned `a1ab5ba` is recorded in `baseline.md`, not silent |
| REQ-PKG-PACKAGING-006 — Fixture A, nested, per-root rendering | pass | `nested_roots_render_per_root` present and invoked. **Negative control executed**: rewriting its expectation to `plugins/sdd/skills/suite-skill/SKILL.md` makes `--self-test` exit 1 |
| REQ-PKG-PACKAGING-007 — Fixture B, disjoint, consumer shape | pass | `disjoint_suite_walk_excluded` present and invoked; asserts `not lin.suite_contained()`, that the gated table row fires, and that the suite-root walk seed appears in no finding |
| REQ-PKG-PACKAGING-008 — Case C, equal roots, single sweep | pass | `case_c_counts_once` + `case_c_negative_double_count` present and invoked; `fixture_counts_exact` asserts case C sweeps exactly 1 |
| REQ-PKG-PACKAGING-009 — verify skill's sweep root survives the move | pass | Only one drift-sweep invocation in `plugins/sdd/skills/` outside the bundled tool's own help text and the orchestrate references: `verify/SKILL.md:169` = `python3 <plugin-dir>/tools/gc.py --report --root .`. Zero bare `tools/gc.py` invocations; every invocation carries an explicit root. **Scratch consumer run executed**: from an empty repo holding only `docs/.sdd-version`, the shipped `gc.py` reports `.: [structure] skills/ directory not found` — the root resolved to the consumer, not the suite; zero swept paths under the suite |
| REQ-LINT-PACKAGING-001 — retired-prefix scope binds per entry | pass | Live run: `retired_scope_entries()` returns entries under **both** bases (`<repo>` and `<repo>/plugins/sdd`); 39 `docs/spec/` members bound to the corpus root. No two-root construction raised `ValueError` in any geometry exercised here, including the disjoint one. `retired_scope_binds_per_entry` present and invoked |
| REQ-LINT-PACKAGING-002 — `TEMPLATE_PAIRS` binds per side | pass | `template_pairs_bind_per_side` present and invoked (three geometries + the both-sides-to-suite negative control); `--self-test` exit 0 |
| REQ-LINT-PACKAGING-003 — set-membership over both manifest paths | pass | **Negative control executed**: rebinding `".claude-plugin": "both"` → `"suite"` makes `--self-test` exit 1 with the precise diagnostic `retired_scope_files() is missing <corpus_root>/.claude-plugin/marketplace.json` — the acceptance's "fail naming the missing path" |
| REQ-LINT-PACKAGING-005 — live duplicate-freeness guard, `fail` severity | pass | `_guard_duplicate_free()` is called from `walk()` itself, so it runs on every invocation and cannot be skipped by `--print-population`, `--self-test` or a plain run; it emits through `self.flag()` (default `fail`), never an exception or a bare exit. Four tests present and invoked: `sweep_is_duplicate_free`, `duplicate_guard_negative_case`, `walk_dedupes_repeated_roots`, `check_structure_dedupes_repeated_roots`, `check_size_dedupes_repeated_roots`. See Minor 3 for the one deduplication this does **not** cover |
| REQ-LINT-PACKAGING-006 — exact fixture-local counts | pass | `fixture_counts_exact` asserts 2 / 1 / 1 per geometry plus the corpus-less-root case. **Negative control executed**: changing fixture A's count 2 → 3 makes `--self-test` exit 1 |

### skill-lint-v5.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-PKG-PACKAGING-005 — amended F11 target with both exceptions | pass | 23 `F11` matches across `docs/spec/`, `plugins/sdd/skills/`, `plugins/sdd/tools/`. Every match in `skill-lint-v5.md` sits inside a scoping clause naming the ungated set or naming an exception; the four `scope-check-selftest.py` matches are the documented unrelated-scenario-id exception recorded at `skill-lint-v5.md:643`. Zero unscoped restatements — consistent with C6.6's recorded 18-block / 0-failing scan |

### skill-namespace-rename.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-LINT-PACKAGING-008 — retired front door dropped from both tuples | pass | `grep -c 'README\.org'` = **0** in `plugins/sdd/tools/skill-lint.py` and **0** in `docs/spec/skill-namespace-rename.md`; `--self-test` exit 0 |

### marketplace-packaging.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-PKG-PACKAGING-010 — drift sweep resolves its linter sibling-first | pass | All three assertions executed against a scratch geometry with distinguishable stubs. (1) **Precedence**: both candidates present → `lint_path()` returns `<gc.py's own dir>/skill-lint.py`. (2) **Fallback**: sibling absent → returns `<root>/tools/skill-lint.py`. (3) **Neither**: returns `None`; the run exits **2** printing `error: linter missing — expected …/tools/skill-lint.py`, unchanged. The three named failing constructions are not pinned by any automated test — see Minor 5 |

### pre-commit.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-PC-PACKAGING-001 — both local hook entries take the `plugins/sdd/` prefix | pass | Four `entry:` values parsed from `.pre-commit-config.yaml`; every `.py` token in each resolves by `test -f` (4/4), checked per parsed path. The linter hook's parsed entry is exactly `python3 plugins/sdd/tools/skill-lint.py` — **no positional root argument**. Running that entry's wiring verbatim from the repository root sweeps a set containing `docs/spec/` paths, asserted by membership on the run-time set. `pre-commit run --all-files` exits 0. The revert-either-prefix failure is pinned by C5.7 and is structurally evident: a missing `entry` path fails the hook with a missing-file error |
| REQ-PC-MARKETPLACE-001 / -004 / -006 (evidence delivered by this workstream) | pass | Parsed hook-id set is the eight-entry closed set: `drift-sweep`, `skill-lint`, `skill-lint-self-test`, `drift-sweep-self-test` (four local) + four upstream hygiene hooks. **No parsed entry carries an `args:` key** — the `--fast` / `--self-test` selectors live inside `entry:`. Grep of `.pre-commit-config.yaml` for the three contributor-tool script filenames returns 0/0/0. These three rows carry the recorded **supersedes** note against the `marketplace` workstream's older six-id assertion |

### project-docs.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-DOCS-PACKAGING-001 — `orchestration.md` names the README by its live filename | pass | `grep -c 'README\.org' docs/spec/orchestration.md` = **0**; `:574` reads "The project README (`README.md`)". `gc.py --report --root .` exit 0, zero warnings — no broken-link finding on the file |
| REQ-DOCS-PACKAGING-002 — `CLAUDE.md` states one marker | pass | `docs/.sdd-version` = `4`. Exactly one line in `CLAUDE.md` names a marker as this repository's own (`:216`, "this repo migrated to marker `4` on 2026-09-17") — string-equal to the file's trimmed contents, both read at run time. `:252`'s contradicting "and is what this repo uses today" is gone; the v4 section now reads "marker `3` (flat) remains fully supported." The phase-detection table and v4 section are otherwise unchanged |
| REQ-DOCS-PACKAGING-003 — the screen's marker rule is item-scoped | pass | The distinguishing fixture was evaluated under both rules: the `backlog:` occurrence scores **not live** under the superseded `L`/`L-1` rule and **live** under the item-scoped rule — the fixture distinguishes them rather than merely passing under the new one. The screen was re-run over the glob (below); every count reported was measured by that run |

## Deferral-Backlog Screen (REQ-REQ-HARNESSP6-001)

Run with the 22-phrase table and the marker regex **read from**
`docs/spec/requirements-artifacts.md`, under the item-scoped liveness rule of
§Item-Scoped Liveness (downward attachment of standalone marker lines).

| Path | Phrase hits | Live |
|------|-------------|------|
| `docs/ws/default/verification.md` | 3 | 0 |
| `docs/ws/harness-p2/verification.md` | 0 | 0 |
| `docs/ws/harness-p3/verification.md` | 12 | 0 |
| `docs/ws/harness-p4/verification.md` | 5 | 0 |
| `docs/ws/harness-p5/verification.md` | 6 | 0 |
| `docs/ws/harness-p6/verification.md` | 0 | 0 |
| `docs/ws/marketplace/verification.md` | 0 | 0 |
| `docs/requirements/index.md` §Out of Scope | 0 | 0 |

The glob returned **7** paths and **7** rows were walked — both derived from the
same run. Total phrase hits 26, total live **0**. (C6.7 recorded 24 hits / 0
live over the same seven paths; the two-hit difference is this run's slightly
wider rendering of rows 10 and 16 of the phrase table, not a liveness
difference.) A first pass that scored 6 occurrences live was wrong — it
attached standalone marker lines **upward**; re-run with the spec's
downward-attachment clause, all 6 resolve to markers inside their own item.

**Phrase coverage is a screen over observed backlog vocabulary, not a proof of
absence.** A live-count of 0 says no occurrence of the 22 known shapes is
unmarked; it does not say the sections hold no latent work, and it is not
reported here as one.

## User-Perspective Validation

| Scenario | Status | Notes |
|----------|--------|-------|
| Operator runs the linter from the repository root with zero arguments | pass | `python3 plugins/sdd/tools/skill-lint.py` → `OK: 25 file(s) clean`, exit 0. Corpus root = cwd, suite root = `plugins/sdd` — the nested geometry, sweeping both |
| Operator asks for the population | pass | `--print-population` → `REQUIRED=40 VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=13 TEMPLATE_PAIRS=4`, `corpus: FILES_SWEPT=25 policed-areas=11`, exit 0. Counts derived from the tables at run time |
| Consumer runs the shipped linter against their own repository (disjoint geometry) | pass | Against a scratch repo with no `skills/`: the three suite-gated tables stay silent, the ungated `[structure]` check reports against the **consumer's** root. No suite-gated false green, no crash |
| Consumer runs the shipped drift sweep against their own repository | pass, with one nit | `gc.py --report --root .` roots on the consumer and reports `.: [structure] skills/ directory not found`. It also emits `WARN docs/requirements/traceability.md: [traceability-aggregate] aggregate differs from …` in a repo that has neither an aggregate nor any per-ws traceability file — see Minor 6 |
| Missing-linter diagnostic | pass | Exits 2 with `error: linter missing — expected <root>/tools/skill-lint.py`. The message names only the corpus-root candidate; that wording is deliberately out of scope per REQ-PKG-PACKAGING-010 residue (c) |
| Contributor commits | pass | `pre-commit run --all-files` exits 0 with all eight hooks Passed |
| Install shape | pass, by reference | Not re-measured. Recorded observation stands: install into a throwaway `CLAUDE_CONFIG_DIR` gave a cache root of `agents/ skills/ tools/`, **no `docs/`**, 50 files against 199 — the move's stated purpose. The global install still shows the pre-move shape because its marketplace tracks `main`, where the move is unmerged; that is expected, not a defect |

## Regressions

Base: `merge-base(packaging, main)` = `0f5ec2675fcc0c4a993922fd6ba1702ddec426d9`
— the workstream branch point, not `main`'s tip. 23 commits, 74 files,
+8893 / −1645.

- **None found.**
- Suite move is loss-free: `.py` population `95c28b7` → `HEAD` is 7 → 7, zero
  lost files (each pre-move `.py` accounted for at its post-move path).
- Move commit `e26f81f` is 45 renames + 3 content modifications
  (`.claude-plugin/marketplace.json`, `.pre-commit-config.yaml`, the plan),
  0 adds, 0 deletes.
- Corpus-root paths touched outside `docs/` and `plugins/sdd/`:
  `.claude-plugin/marketplace.json`, `.pre-commit-config.yaml`, `CLAUDE.md`,
  `CONTRIBUTING.md` (all intended by REQ-PC-PACKAGING-001,
  REQ-DOCS-PACKAGING-002 and the carried repairs) and the deletion of
  `tools/skill-lint.py`, which is the move. No unintended change.
- The corpus root no longer carries a `tools/` directory: the three contributor
  tools (`eval.py`, `scope-check-selftest.py`, `telemetry.py`) moved with the
  suite. They remain **outside** the plugin's component list, which is what the
  marketplace cycle's Q2 exclusion governs, so this is not a regression of that
  decision.
- Equal-roots behavioural comparison against the pre-change baseline `93b1133`
  is carried by `--self-test`, which passes.

## Issues Found

### Critical (blocks release)

- None.

### Minor (can ship, fix later)

There is no previous `docs/ws/packaging/verification.md`; nothing to carry
forward.

All five below are one class — **a binding whose reversion no gate catches**.
None is a behavioural defect: every one was observed correct in the shipped
tree. Each is stated with the mutation that demonstrates the gap, reproduced in
a throwaway copy of `HEAD`, never in the repository.

1. **`check_retired_prefix()`'s `rel=Path(rel)` at
   `plugins/sdd/tools/skill-lint.py:1163` is unpinned — highest priority.**
   Reproduced: deleting the clause leaves `skill-lint.py`, `skill-lint.py
   --self-test`, `gc.py --fast` and `gc.py --self-test` **all exit 0**, and
   driving `check_retired_prefix()` in the disjoint geometry then raises
   `ValueError: '<suite>/skills/foo/SKILL.md' is not in the subpath of
   '<corpus>'` where the unmutated code returns one finding rendered
   `skills/foo/SKILL.md`. The disjoint geometry is exactly what a consumer
   install has (`swept_roots()` drops an uncontained suite root, so
   `rel()` falls through to `relative_to(corpus_root)`), and the rule's own
   severity is `fail`, so the breakage is gateable in principle.
   **Judgement — why this is Minor and not Critical**: nothing crashes today.
   The clause is present and the consumer-shape run was executed above and is
   clean. What ships is an unguarded load-bearing clause, not a crash. It is
   the first thing a follow-on pass should close, and the close is one
   self-test case driving `check_retired_prefix()` against the disjoint
   geometry and asserting no raise.
2. **`main()`'s `print_population(root, default_suite_root())` wiring is
   unpinned.** Reproduced: mis-rooting to `print_population(root, root)`
   reports `corpus: FILES_SWEPT=0 policed-areas=11` against the correct
   `FILES_SWEPT=25`, with **exit 0 on all four gates**. A silent zero-sweep is
   the mis-rooting class `REQ-PKG-PACKAGING-002` exists to prevent. The
   `Linter` half of the identical wiring in the same function **is** pinned
   (C9.2 / C10.6); only the `print_population()` half is not.
3. **The fourth deduplication — `retired_scope_entries()`'s `seen` set — is
   unpinned.** Reproduced: deleting the `if key in seen: return` / `seen.add`
   guard leaves all four gates at exit 0, while the C10.1/C10.2 technique
   (`lin.retired_scope_roots = lambda e: [d, d]`) yields **1** finding with the
   guard and **2** without. Three of the four deduplications are pinned; this
   one is reachable from production by the same technique that pins them.
4. **The `warn` severity class is not gateable — a stated boundary, confirmed
   not rediscovered.** Reproduced: rebinding `resolve_backtick_path()`'s
   `docs/spec/` base from `self.corpus_root` to `self.suite_root` produces
   **136** `[path]` warnings against a control of 0, with exit 0 on all four
   gates, because no gate reads warning counts. `two-root-linter.md`
   §Verification records this as a boundary and closing it means changing the
   linter's exit contract. Carried as a boundary, not as unfinished work.
5. **`gc.py`'s `lint_path()` candidate tuple is unpinned — found in this pass,
   same class.** REQ-PKG-PACKAGING-010 states three failing constructions
   (reorder the tuple, delete the second entry, return a nonexistent path), but
   `grep lint_path plugins/sdd/tools/gc.py` finds only the definition (`:500`),
   its one production call (`:520`) and the `main()` guard (`:1869`) — no
   self-test constructs the two candidates. All three assertions were executed
   by hand here and hold; a reordering would pass every gate. The requirement's
   acceptance is satisfied as written; the gate coverage is not there.
6. **`gc.py` warns `[traceability-aggregate]` in a repository that has no
   traceability at all.** In a scratch consumer holding only
   `docs/.sdd-version`, `gc.py --report --root .` emits `WARN
   docs/requirements/traceability.md: [traceability-aggregate] aggregate
   differs from regenerate(docs/ws/*/traceability.md)` — an aggregate that does
   not exist, regenerated from zero files. Pre-existing behaviour, outside this
   cycle's 22 requirements, no effect on this repository (`--report` here is
   clean). Recorded so a consumer-facing pass does not have to rediscover it.

### Red-team round 1 — `RED_VERDICT: BROKEN`, three breaks, all fixed

The verify stage was dispatched with the red team enabled. One read-only round
attacked the weakest acceptance criteria and returned `RED_VERDICT: BROKEN`
with three breaks. The operator chose **fix** for all three; the repairs
landed as `plan.md` §Chunk 12. All four gates (`skill-lint.py`,
`skill-lint.py --self-test`, `gc.py --fast`, `gc.py --self-test`) were exit 0
before the repairs and are exit 0 after them.

**R2 — Major. The orchestrate skill's bundled drift sweep was dead in every
install. FIXED.**

`plugins/sdd/skills/orchestrate/tools/gc.py` is byte-identical to
`plugins/sdd/tools/gc.py` but has no sibling `skill-lint.py` — that directory
holds only `gc.py` and `telemetry.py`. `gc.py` resolves the linter
sibling-first, so it fell through to `<root>/tools/skill-lint.py`, the path
this cycle's move deleted. The command the skill documents therefore did not
run anywhere. Reproduction:

```
$ python3 plugins/sdd/skills/orchestrate/tools/gc.py --report --root .
error: linter missing — expected <repo>/tools/skill-lint.py      # exit 2
```

A regression this cycle introduced: it worked at `merge-base(packaging, main)`
= `0f5ec26`.

*Fix.* All eight `<skill-dir>/tools/gc.py` spellings in
`plugins/sdd/skills/orchestrate/` — `SKILL.md:42`, `:396`, `USAGE.md:519`,
`:529`, `references/drift-sweep.md:21`, `:50`, `:57`, `:108` — are re-pointed
to `<plugin-dir>/tools/gc.py`, the convention C6.1 already gave
`verify/SKILL.md`, so both skills use one spelling and no second linter copy
is bundled. The two prose passages that justified the skill-relative form
(`SKILL.md:42`'s parenthetical, `drift-sweep.md` §1's paragraph) are rewritten;
`two-root-linter.md` §8 records the convention now covering every gc
invocation. A sweep of `plugins/sdd/skills/` for further `<skill-dir>/tools/`
invocations returns none.

*Verified as the break was found* — from a scratch consumer repository
(`git init`, `docs/.sdd-version` = `4`, a `docs/requirements/index.md`, a
`docs/ws/demo/` note, **no** `tools/` directory) against a copy of the plugin
root as an install:

```
$ python3 <install>/tools/gc.py --report --root .          # the NEW spelling
.: [structure] skills/ directory not found
WARN docs/requirements/traceability.md: [traceability-aggregate] …
FAIL: 1 finding(s), 1 warning(s), 0 info                          # exit 1
$ python3 <install>/skills/orchestrate/tools/gc.py --report --root .   # the OLD one
error: linter missing — expected <consumer>/tools/skill-lint.py   # exit 2
```

Every path in the new spelling's output is the consumer's; nothing under the
install is swept.

*The bundled copy was not deleted* — REQ-PKG-MARKETPLACE-007 freezes
`plugins/sdd/skills/orchestrate/*` and REQ-PKG-MARKETPLACE-006's
duplicated-not-symlinked rule governs it. **It is now referenced by no
invocation at all.** What still names it is descriptive only: its traceability
`Implementation` cells for REQ-PKG-MARKETPLACE-006
(`docs/requirements/traceability.md:317`,
`docs/ws/marketplace/traceability.md:56`), `docs/spec/pre-commit.md:274`,
`docs/spec/marketplace-packaging.md:565`, and the new explanatory sentence in
`references/drift-sweep.md`. One consequence, out of this workstream's write
scope and left for the operator: the added criterion
`docs/ws/marketplace/verification.md:557` records for REQ-PKG-MARKETPLACE-006
— "at least one invocation resolves to the bundled copy" — no longer holds.

**R3 — Moderate. A gated-row rebinding silently no-opped sixteen rules with
all four gates green. FIXED.**

Rebinding `check_required()`'s `VERSION_GATED_SKILLS` and `V4_CONTRACT_SKILLS`
loops (`plugins/sdd/tools/skill-lint.py:845`, `:852`) from `self.suite_root` to
`self.corpus_root` left all four gates at exit 0 while making all sixteen rows
no-ops: each loop is guarded by `if f.is_file() and …`, and the corpus root has
no `skills/` after the move. The red round demonstrated a real `[required]`
violation going unreported under the mutation. Sixth member of this cycle's
defect class, and the worst — the others hid rendering or a printed count; this
suppressed rule enforcement.

*Fix.* A checked-in self-test case
`check_required_gated_rows_bind_to_the_suite_root`, in the shape
`check_size_binds_to_the_swept_roots` and
`check_structure_binds_to_the_swept_roots` already use: a nested fixture whose
corpus and suite roots differ, `skills/verify/SKILL.md` (a member of both gated
tables, carrying neither marker) seeded **only** under the suite root, a
positive control `skills/research/SKILL.md` carrying both markers so the rows
are pinned conditional rather than unconditional, and an identically-broken
decoy `skills/replan/SKILL.md` under the corpus root. Findings are filtered to
the two gated messages, because the `REQUIRED` rows resolve against the same
root and also fire on this fixture.

*The mutation, run.* With both loops rebound to `self.corpus_root`,
`skill-lint.py` `--fast`/`--self-test` for `gc.py` all still exit 0 — and
`python3 plugins/sdd/tools/skill-lint.py --self-test` exits **1**:

```
SELF-TEST FAIL:
- the VERSION_GATED row must fire on the SUITE root's seeded skills/verify/SKILL.md:
skills/replan/SKILL.md: [required] never reads `docs/.sdd-version` …
- the V4_CONTRACT row must fire on the SUITE root's seeded skills/verify/SKILL.md:
skills/replan/SKILL.md: [required] lost the collapsed v4 ownership summary (audit P1)
- the gated rows must not resolve against the CORPUS root: the decoy seeded there was reported:
```

Three of the case's four assertions fail, and the failure text names both the
row that stopped firing and the decoy that started.

*`two-root-linter.md` §6 corrected.* The sentence claiming the four pinned
populations are "a regression check on §3's retarget, catching a row dropped or
duplicated **while moving the rows' binding**" is withdrawn as false in its
second half. What they actually catch is an edit to the rule **tables** — a row
dropped, duplicated or added to `REQUIRED`, `VERSION_GATED_SKILLS`,
`V4_CONTRACT_SKILLS` or `FORBIDDEN` changes a printed count. A population is
`len(<table>)`, read off the table object; a retarget changes which root a row
is *resolved against* and leaves every row and every count identical, which is
exactly what the red round showed. §6 now says so and points bindings at the
invertible geometry cases, naming the new one for these sixteen rows.

**R1 — Minor. One of the three no-pinned-count greps is not empty. FIXED (the
criterion, not the code).**

```
$ grep -nE '(FILES_SWEPT|files_swept|len\( *swept *\))[^\n]*(==|!=|>=|<=|<|>) *[0-9]+' \
      plugins/sdd/tools/skill-lint.py
2654:            check(len(swept) == 1,
```

The match is inside `walk_dedupes_repeated_roots()`, a case the criterion's
exclusion list does not name — it enumerates only fixtures A, B and case C. The
assertion is sound (a hand-built two-element root list, which cannot grow by
contribution); the criterion was false as written, and would go false again
each time a case lands a fixture literal.

*Fix.* `two-root-linter.md` §Verification and `plan.md` §Chunk 4 task 2 now
state the exclusion as a **class**: a match inside `self_test()` whose counted
list was derived entirely from a tree the case seeded under the self-test's
scratch root, or hand-built in the case as a literal path list. It is not
weakened — everything else is still a finding, explicitly including any
assertion whose counted list comes from a live corpus root (the construction
the requirement actually bars) and any such assertion outside `self_test()`.
Re-run after the restatement: grep 1 returns the one excluded match, greps 2
and 3 return zero.

**AC5 suspicion — judged: the criterion's wording was wrong, the strings are
not.**

The red round raised, without claiming it as a break, that AC5's "a grep for a
bare `tools/gc.py` drift-sweep invocation over `plugins/sdd/skills/` is empty"
is literally false: `orchestrate/SKILL.md:44`, `USAGE.md:513` and
`references/drift-sweep.md:23` each contain `run tools/gc.py --report`, as does
`skills/orchestrate/tools/gc.py:175`'s `AGG_FIX` string.

*Judgement: correct the criterion.* The first three are one thing — the `GC: F
fail, W warn — run tools/gc.py --report` gate line, text the driver **prints**
to the operator, whose wording `docs/spec/drift-sweep.md` owns and nothing
executes. Repairing them would edit a gate line's spelling to satisfy a grep
aimed at invocations, which is the criterion being wrong, not the text. AC5 now
defines an invocation as a command line the body tells the reader to run and
puts rendered messages out of scope.

`AGG_FIX` is different and the red round was right to single it out: it is the
one a consumer would paste, and it names a path a consumer does not have. It is
still a printed message, so it is outside AC5 either way — but it is a real
consumer-facing defect. It could not be repaired here: `plugins/sdd/tools/gc.py`
and `plugins/sdd/skills/orchestrate/tools/*` are frozen to this cycle's write
scope by REQ-PKG-MARKETPLACE-007. Recorded against REQ-PKG-PACKAGING-009 in
`two-root-linter.md` §Verification, and in §Next Steps below, for a later
cycle.


## Recommendation

- [x] Ship as-is *(subject to the red round — `status:` is `pending-red`; the
      `pending-red → pass` flip is the orchestrator's, not this report's)*
- [ ] Fix critical issues then ship (invoke replan)
- [ ] Significant rework needed (invoke replan)

## Next Steps

- `plugins/sdd/tools/gc.py`'s `AGG_FIX` remediation string tells the reader to
  `run tools/gc.py --fix traceability-aggregate` — a cwd-relative path that
  exists in this repository and in no consumer install. Observed live in the
  R2 scratch-consumer run above. `gc.py` was frozen to this cycle's write
  scope; carry it to a later cycle (REQ-PKG-PACKAGING-009).
- `plugins/sdd/skills/orchestrate/` invokes `python3 tools/telemetry.py` at
  `USAGE.md:159`, `:439`, `:572` and `references/telemetry.md:484`, `:577`,
  `:602` — the same cwd-relative shape R2 fixed for `gc.py`, unreachable from a
  consumer repository. Found by R2's sweep; not repaired, because the
  telemetry reader is documented as a maintainer command run from this
  repository and no acceptance criterion in this cycle covers it.
- The bundled copy at `plugins/sdd/skills/orchestrate/tools/` is now referenced
  by no invocation (R2). Its fate — and the added REQ-PKG-MARKETPLACE-006
  criterion at `docs/ws/marketplace/verification.md:557` that R2 falsifies —
  is a later cycle's decision.

- `docs/requirements/integration/project-docs.md:79` says "the three heavier
  checks" while `CONTRIBUTING.md:74`'s heading is now §The heavier checks, run
  explicitly. A requirements file, out of implement-stage write scope; routed
  here. The same stale spelling survives in two traceability `Test` cells
  (`docs/requirements/traceability.md:306`,
  `docs/ws/marketplace/traceability.md:48`) and in
  `docs/ws/marketplace/verification.md` — the latter two are the `marketplace`
  workstream's rows and that workstream's record.
- Close Minor 1 with one self-test case driving `check_retired_prefix()` against
  the disjoint geometry and asserting no raise; close Minors 2, 3 and 5 with the
  pinning technique already used for their siblings (C9.2/C10.6 for the wiring,
  C10.1/C10.2 for the deduplication). Minor 4 requires an exit-contract change.
