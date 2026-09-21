---
status: Approved
last_updated: 2026-09-21
requires:
  - REQ-PKG-PACKAGING-001
  - REQ-PKG-PACKAGING-002
  - REQ-PKG-PACKAGING-003
  - REQ-PKG-PACKAGING-004
  - REQ-PKG-PACKAGING-006
  - REQ-PKG-PACKAGING-007
  - REQ-PKG-PACKAGING-008
  - REQ-PKG-PACKAGING-009
  - REQ-LINT-PACKAGING-001
  - REQ-LINT-PACKAGING-002
  - REQ-LINT-PACKAGING-003
  - REQ-LINT-PACKAGING-004
  - REQ-LINT-PACKAGING-005
  - REQ-LINT-PACKAGING-006
  - REQ-LINT-PACKAGING-007
---

# The Suite Root Move and the Two-Root Linter

## Context

The marketplace cycle packaged this repository as a manifest statement over the
existing tree — `"source": "./"`, nothing moved, the install carrying the whole
corpus. This cycle replaces that shape: the shipped suite moves into
`plugins/sdd/` (the **suite root**) and the repository root stays the **corpus
root** this repository's own cycles are linted and swept against.
`marketplace-packaging.md` §Placement records the supersession; the
single-plugin decision it carries is unchanged. Everything else follows from
the two roots being distinct objects — the linter is the one program reading
both, so it grows a two-root interface, each dual-rooted check binds per entry
or per side, and the self-test grows the three geometries in which a
mis-binding is observable.

## Design

### 1. The two roots and the membership rule (REQ-PKG-PACKAGING-001)

A file belongs to the **suite** iff it is a plugin component, a file bundled
inside one, or the plugin's own manifest: `skills/**`, `agents/**`, `tools/**`,
`.claude-plugin/plugin.json`. Everything else stays at the corpus root,
`.claude-plugin/marketplace.json` included — it describes the marketplace, not
the plugin. The plugin entry's `source` names `plugins/sdd` rather than `./`,
so `docs/` is outside the install entirely rather than copied-but-inert. The
move is recorded by git as a move, and membership is asserted per name against
the enumeration of the move commit's **parent** — never against a walk of the
post-move tree, where the corpus-root copies are gone and the walk is empty.
Rationale: absence from the component list governs what Claude Code *loads*,
never what the install *copies*, and two distinct roots is the smallest change
that makes the exclusion real.

### 2. The linter's two-root interface (REQ-PKG-PACKAGING-002, -003)

The two roots are **constructor parameters**. No other root-resolution
mechanism is introduced — no environment variable, no new CLI option.

```
Linter(corpus_root, suite_root=None, suite_rules=True)
  corpus_root : absolute; CLI positional, default = invocation cwd
  suite_root  : absolute; default = the script's own plugin root
  swept_roots() -> {corpus_root} | {suite_root if contained in corpus_root}
  walk()       -> deduplicated union of <root>/skills/**/*.md over swept_roots()
  rel(f)       -> f rendered relative to the root f was walked from
```

- **The corpus root defaults to the invocation cwd, never the script's
  location.** After the move the script's parent-of-parent names `plugins/sdd`,
  so the old default would silently take the suite as the corpus and stop
  sweeping `docs/` — undetectable downstream, since an empty corpus sweep is
  legitimate in a consumer repository and live zero-sweep detection is given up
  (§6). The cwd default keeps the zero-argument commit-gate invocation
  (`pre-commit.md` §Two-Root Amendment) sweeping the operator's repository.
- **Containment gates the suite term.** `suite_root/skills/**` joins the walk
  only when the suite root is contained in the corpus root, equality counting
  as containment; with equal roots the walk degenerates to today's single walk.
- **Rendering is per root** — against the root a file was walked from.
- **No `--no-suite-rules`**: a disable switch on the checks a contributor finds
  most inconvenient is the silent-disable class this cycle rejects, so
  `suite_rules=False` stays a constructor argument used only by self-test
  fixtures. `--suite-root` is **deferred**, not adopted — it mitigates the one
  unclosed vendored-cache case, and a mitigation for one residual case is not a
  closure; its absence is a decision, not an omission.

The documented default changes with the code: the positional argument's help
string and the `REPO_ROOT` sentences of `skill-lint-v5.md` are restated for the
cwd default and the two roots (`skill-lint-v5.md` §Two-Root Amendment).

### 3. The suite-gated rows retarget to the suite root (REQ-PKG-PACKAGING-004)

`REQUIRED`, `VERSION_GATED_SKILLS` and `V4_CONTRACT_SKILLS` resolve their path
keys against the **suite root**; in a consumer environment that is the
installed plugin cache, where the named files exist, so the rows pass there.
The flip from "fail against the consumer's tree" to "pass against the shipped
plugin" is intended — the rows name this suite's own files and were never
portable style rules. It is a retarget, not a weakening: the **ungated** set
keeps failing loudly in a consumer tree (`skill-lint-v5.md` §Two-Root
Amendment).

### 4. The retired-prefix scope binds per entry (REQ-LINT-PACKAGING-001)

`retired_scope_files()` stops walking one root; each scope entry carries its
own binding:

| Scope entry | Root |
|---|---|
| `skills`, `tools`, `agents` | suite root |
| `docs/spec`, `docs/requirements` | corpus root |
| `.claude-plugin` | both — deduplicated union |
| `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `LICENSE`, `.pre-commit-config.yaml` | both — deduplicated union |

The union is over resolved absolute paths, so with equal roots the entry set is
exactly today's. `.claude-plugin` must be union-bound because after the move it
exists at both roots and a one-root binding silently drops whichever manifest
the other holds; the five root files, because the move edits some of them and
they may exist at either root.

**`skill_dir_of()` binds to the root the file was walked from** — the same rule
`rel()` states in §2, written here because neither §3 nor §4 assigned this
helper a root and that silence is what produced the regression C3.10 fixed in
code: `self.root / "skills"` alone names the corpus root's tree, which after
the move does not exist, so every suite-root file carrying a `references/…`
backtick span raised `ValueError`. §3's "links keep resolving against the
corpus root" governs where a link **target** resolves, not where a swept
**file's** skill directory is located. The same binding governs the other
`skills`- and `agents`-keyed helpers — `check_structure()`, `check_size()`,
and the `skills/…` and `agents/…` bases of `resolve_backtick_path()` — and
that binding is the **swept-root union**, `swept_roots()`, not one root. The
`docs/spec/…` base stays on the corpus root.

Two clauses, and both are load-bearing. (i) **Not the corpus root alone.**
§4's table places these keys on the suite root because the files they name
ship inside the plugin; a corpus-only binding reports every one of them
unresolved, and `check_structure()` degrades to a single `skills/ directory
not found` finding that silently stops every per-skill rule (C6.11). (ii)
**Not the suite root alone.** The suite root alone re-opens the corpus root's
own `skills/` tree to nothing, making frontmatter and size a silent third and
fourth exception to `REQ-PKG-PACKAGING-005`, and in the **disjoint** consumer
geometry it resolves the operator's own `skills/…` and `agents/…` spans
against an installed plugin cache outside their repository — a false pass when
the cache happens to hold the path, a phantom `unresolved path` finding when it
does not, and for the walking checks an uncaught `ValueError` out of `rel()`,
whose swept roots do not contain that path. The union satisfies both: nested
and equal roots reach the suite's trees exactly as the suite binding did, the
corpus's own trees are policed again, and a disjoint suite is not consulted.
A future edit that re-binds any of them to **either** root alone contradicts
this paragraph, not merely a comment (C6.13 from the Chunk 5 verification;
restated for the union at C9.1/C9.3, implement-stage review round 2, whose
first repair had unioned the code and left this paragraph saying suite root).

**Per-entry rendering.** Each entry's findings render relative to the root that
entry is bound to — a union-bound entry relative to whichever root supplied the
file. §2's per-root rule covers the generic walk only: `retired_scope_files()`
and `check_retired_prefix()` render through `relative_to(self.root)`, which
raises on a suite-root file once a second root joins the set, so without this
clause the requirement is unimplementable literally. The existing self-test
block pinning the two scope constants against literal name tuples is **retained
unchanged**: it catches an area dropped from the enumeration and cannot catch a
wrong binding, since directory names survive one intact. No per-root
policed-**file** count is added (§6).

### 5. `TEMPLATE_PAIRS` binds per side (REQ-LINT-PACKAGING-002)

The `TEMPLATE_SOURCE` side moves and binds to the **suite root**; every row's
`spec` key is a `docs/spec/…` path that stays and binds to the **corpus root**.
Binding the gated check wholesale to the suite root would resolve the spec side
where it will not exist, and an absent spec **warns** rather than fails — so
all four rows would silently degrade to warnings the moment the move lands.
With **disjoint** roots the spec side is **skipped, not warned** (warning there
names this suite's spec files inside a consumer's tree); under containment it
is checked and an absent spec keeps warning.

### 6. Counts: asserted, or only printed (REQ-LINT-PACKAGING-004, -005, -007)

**No swept-file count from a live corpus is ever asserted.** A literal fails on
ordinary contribution; a `git ls-files` comparand compares a working-tree walk
against a tracked list and hard-codes a path meaningless in a consumer
repository; re-deriving the comparand from the corpus root re-implements the
sweep and asserts it against itself. The count survives as **output only**:
`--print-population` emits `corpus: FILES_SWEPT=<n>  policed-areas=<n>`, an
informational line with no pinned comparand.

**`--print-population`** also prints one line per rule table with its row
count, derived from the table at run time rather than written into the flag.
Its population criterion is stated here and nowhere else: `REQUIRED=40
VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=13` — the one place in the corpus where
a row population is compared against a number, sound because rule-table rows
are static in-code data. It is a regression check on §3's retarget, catching a
row dropped or duplicated while moving the rows' binding. The flag lands
**before** anything evaluates it.

**The duplicate-freeness construction guard.** Every run, in any repository,
asserts the swept list resolved to absolute paths holds no path twice. It
cannot fail for an implementation built as §2 specifies, so it is a
**construction guard**: it pins that the union stays a set and is never rebuilt
as list concatenation by a later edit. On failure the observable is a
`fail`-severity finding in the run's own findings list (the `flag()` default) —
never a warning, an exception or a bare exit code — and no invocation mode can
skip it. **Injection point, decided here:** the guard is a pure function over a
list of paths returning findings, and the self-test carries a **checked-in
negative case** calling it with a hand-built list holding one path twice, the
shape concatenation over equal roots produces. No source mutation, no manual
step; the reviewer-checkable residue is that §2's union builder is its only
production call site.

**What the guard alone does not pin, and the case that does.** The negative
case above hands the guard a hand-built list, so it exercises the guard and
not the deduplication the guard is a backstop for. Deduplication itself is
unreachable from production input: `swept_roots()` appends the suite term only
when it differs from the corpus, so no geometry yields two walk terms over the
same subtree and the dedupe loop can be deleted with every gate green. The
case `walk_dedupes_repeated_roots` closes that by monkeypatching
`swept_roots()` to return one root twice — the only way to reach the loop from
`walk()` — and asserting each path comes back once and the guard stays silent
(C9.4, implement-stage review round 2).

**There are four such deduplications, not one; three are pinned and the
fourth is an open gap (see below).**
The paragraph above was written as though `walk()` were the file's only one; it
is the only one the §6 guard backstops, which is not the same thing.
`check_structure()` and `check_size()` each carry their own resolved-path
`seen` set over the swept-root union, and each was unreachable from production
input for exactly the reason stated above — so each could be deleted with all
four gates green, the deletion re-reporting every skill directory, and
re-measuring every `SKILL.md`, once per repeated root. The cases
`check_structure_dedupes_repeated_roots` and
`check_size_dedupes_repeated_roots` close those two by the same monkeypatch,
asserting the seeded finding is reported exactly once (C10.1, C10.2,
implement-stage review round 3). A future edit that removes any of those three
deduplications contradicts this paragraph.

**The fourth deduplication is unpinned — a recorded open gap (round 4).** The
count above read *three* until round 4; it was wrong. `retired_scope_entries()`
(`plugins/sdd/tools/skill-lint.py`) carries its **own** resolved-path `seen`
set, over the `both`-bound `retired_scope_roots()` union rather than over
`swept_roots()`, and nothing pins it:

- **Mutation that survives:** delete the `if key in seen: return` / `seen.add(key)`
  guard in `retired_scope_entries()`'s `add()` helper. All four gates
  (`skill-lint.py`, `skill-lint.py --self-test`, `gc.py --fast`,
  `gc.py --self-test`) exit 0, and a repeated root then re-reports every
  `retired-prefix` finding once per repetition.
- **Reachable from production by the same technique as C10.1/C10.2:** the
  entry union is built from `retired_scope_roots()`, so monkeypatching it —
  `lin.retired_scope_roots = lambda e: [d, d]` — reaches the loop. Measured:
  1 finding with the guard, 2 without.

This is recorded, not repaired: closing it is a new self-test case, which the
round-4 correction pass was not authorised to add. It carries into the verify
stage as an open finding, recorded with the other carried gaps in
`docs/ws/packaging/plan.md` §Chunk 11.

**Live zero-sweep detection is deliberately given up.** A bare `FILES_SWEPT >=
1` is wrong (an empty sweep is legitimate in a consumer repository) and the
conditioned form reads its condition through the binding it tests, so a
mis-bound root makes it vacuous. Zero-sweep is caught at self-test time only,
by §7's fixture counts.

### 7. The three geometries (REQ-PKG-PACKAGING-006..-008; REQ-LINT-PACKAGING-003, -006)

Each fixture seeds a known number of `.md` files and asserts the sweep returns
**exactly** that number — a literal is sound here and only here, a fixture not
growing by contribution, and a zero sweep from a mis-bound root fails at once,
replacing §6's retired live count.

**Fixture A — nested** (`suite_root = corpus_root/plugins/sdd`, this repository
after the move). Seeds a walk-class violation (forbidden phrase or bad
frontmatter) under **each** root — one under `corpus_root/skills/**`, one under
`suite_root/skills/**` — and asserts **both** are reported, each with its path
rendered relative to the root it was walked from, so both seeds render as
`skills/…` with **no** `plugins/sdd/` segment. Two seeds are required because
one cannot discriminate: a seed under the suite root alone renders identically
under per-root rendering and under suite-rooted rendering, and the corpus seed
is what a suite-rooted binding cannot render at all; conversely a corpus-rooted
single binding renders the suite seed as `plugins/sdd/skills/…`, which the
suite seed's assertion rejects. Fixture A does **not** pin single-sweep and
must not be described as though it did — under nesting the two walk terms are
disjoint subtrees.

**Fixture B — disjoint** (suite root outside the corpus root, the consumer
shape). Asserts (i) a **table-row** violation seeded under the suite root — the
gated tables resolve `root / rel` directly and bypass the walk — **is**
reported; (ii) a walk-class violation seeded under `suite_root/skills/**` is
**not** reported, asserted as a **named absent finding for a specific seeded
path** while other findings are present, so "correctly excluded" is
distinguishable from "switched off"; no assertion rests on exit-code silence. B
also asserts `retired_scope_files()` contains **both**
`<suite>/.claude-plugin/plugin.json` and
`<corpus>/.claude-plugin/marketplace.json` — any one-root binding drops exactly
one, and a count-based assertion must not replace it.

**Case C — equal roots** (the unmoved repository; a consumer on a non-vendored
install). Seeds one walk-class violation under `skills/**` and asserts it is
counted **exactly once** — the only geometry in which both walk terms name the
same subtree, hence the only one distinguishing a set union from a
concatenation. It reuses fixture A's corpus tree with both roots equal.
Note the premise is **not** realisable against §2's builder as implemented —
equal roots collapse to one walk term before `walk()` sees them — so Case C
pins the counting path, and production deduplication is pinned separately by
§6's `walk_dedupes_repeated_roots`.

**Case C's own invertibility (REQ-PKG-PACKAGING-008).** The seam goes on the
**consuming** side, mirroring §6's shape rather than sitting inside the union.
The counting path is a pure function taking the swept list and returning
findings — one finding per violation it finds in that list — and the count-once
assertion reads that findings list. Deduplication stays where §2 puts it,
inside the union builder, whose only production consumer is this counting
function. Case C's negative case calls the counting function **directly** with
a hand-built swept list holding the seeded violating path **twice** — the shape
a concatenation over two equal roots produces — and asserts the count-once
assertion **fails**, naming the seeded path. It can fail because the counting
function is not the deduplicator: given the path twice it emits the finding
twice, so the count-once assertion cannot pass. No source mutation, no manual
step; the reviewer-checkable residue is the one §6 already names — that §2's
union builder is this function's only production caller. §6's negative case
calls the duplicate-freeness guard with a hand-built path list and exercises
that guard alone; it cannot fail a count assertion and must not be cited as
discharging this one.

### 8. The last cwd-relative skill-body invocation (REQ-PKG-PACKAGING-009)

The drift-sweep invocation in the verify skill's gc criterion must come out of
the move with **both** halves correct: its script path resolves to the tool
inside the suite, and its root argument still names the operator's own working
directory, never the suite. A bare `tools/gc.py` path is what the move breaks;
an implicit root would silently retarget the sweep.

**Placeholder convention, stated here once.** A skill body that must name the
suite root it ships inside writes `<plugin-dir>` when the referent is the
whole installed plugin root (the tree holding `tools/`, `agents/` and
`skills/` — `verify/SKILL.md`'s gc invocation) and `<skill-dir>` when it is
that one skill's own directory (`orchestrate/SKILL.md`'s `references/` links).
The two are different referents, not a divergence; each occurrence still
expands its placeholder inline at first use. The repair is **sequenced
after** §2, §4 and §5 — done first it would pin a spelling those bindings then
change.

**Sequencing, whole-cycle.** §1 and §2 land with the commit-gate prefix
(`pre-commit.md` §Two-Root Amendment), a prefixed zero-argument hook entry
being correct only because the corpus root defaults to cwd; §6's flag precedes
anything evaluating its population criterion; the retired-filename removal
(`skill-namespace-rename.md` §Two-Root Amendment) lands before or with §4, §4's
table being the post-removal five-name state.

## Verification

### Automated

**The named-case runner in `self_test()` — the `for _case in (…)` tuple — is
the single authoritative enumeration of the self-test cases, and its
membership is the count.** No number is pinned in prose here or anywhere else:
the set grows whenever a post-plan repair lands a case, and a number restated
in a second place is drift, not a check. Any other statement of the case set
(the plan's C7.6 included) points at that tuple rather than counting. Every
case is asserted **invertible** — swapping its expectation fails the
self-test.

Twelve cases were specified at design time, covering the acceptance criteria
below (several criteria carry more than one):
`two_roots_construct_distinct_and_equal`, `equal_roots_sweep_set_unchanged`,
`nested_roots_render_per_root`, `zero_arg_run_sweeps_the_corpus`,
`retired_scope_binds_per_entry`, `manifest_pair_membership`,
`template_pairs_bind_per_side`, `sweep_is_duplicate_free`,
`fixture_counts_exact`, `case_c_counts_once`, `print_population_shape`,
`retarget_seeds_an_ungated_finding`. Cases added after the plan — each from a
verification or review finding, each named in its own docstring — are
`disjoint_suite_walk_excluded`, `case_c_negative_double_count`,
`duplicate_guard_negative_case`, `skill_dir_of_binds_per_root`,
`forbidden_allow_files_root_correct`,
`check_structure_binds_to_the_swept_roots`,
`check_size_binds_to_the_swept_roots`, `walk_dedupes_repeated_roots`,
`backtick_bases_bind_to_the_swept_roots`,
`check_structure_dedupes_repeated_roots`, `check_size_dedupes_repeated_roots`,
`swept_base_order_and_fallback`, `rel_raises_outside_the_swept_roots` and
`equal_roots_count_as_contained`.

**Every design-time name is now landed.** `zero_arg_run_sweeps_the_corpus`
was the last outstanding one: round 1 of the implement-stage review recorded
it here as a known gap on the grounds that the cwd default is exercised by the
zero-argument commit-gate entry (`pre-commit.md` §Two-Root Amendment) and by
the plan's C1.1. That is not a guard — `REQ-PKG-PACKAGING-002` says of this
mis-rooting that *"nothing downstream can distinguish this mis-rooting from a
correct run"*, and mutating the default to `default_suite_root()` did in fact
leave both self-tests at 0. The case landed at C9.2 (review round 2) and
drives `main()`'s own argument path with the cwd set to a fixture corpus.

**A second, narrower boundary, recorded for the same reason.**
`suite_contained()`'s `suite == corpus or` disjunct cannot be pinned by any
case: `Path(p).is_relative_to(p)` is already `True`, so the disjunct is
redundant with the clause beside it and deleting it is behaviour-preserving,
not a defect. `equal_roots_count_as_contained` pins the **property** §2 states
— equality counts as containment, which `check_links()` reads to decide
whether the `TEMPLATE_PAIRS` spec side is checked at all — and its docstring
says plainly that the disjunct itself is documentary.

**Correction (2026-09-21, round 4).** An earlier revision of the paragraph
above extended the same claim to `rel()`, saying that mutating its root set to
the suite alone *"survives every gate because the corpus fallback returns the
same rendering the union would"*. **That claim is false**, and was verified
false by running the mutation. `roots = [self.suite_root]` in `rel()` is killed
by `rel_raises_outside_the_swept_roots` — the very case the sentence named:

```
SELF-TEST FAIL:
- rel() must raise ValueError on a path under no swept root, as its docstring states; got skills/outside/SKILL.md
```

The mutant errs conservatively — it raises where the union would have rendered
— so `rel()`'s coverage is **better** than the sentence advertised, not worse.
`rel_raises_outside_the_swept_roots` therefore pins both the documented raise
that `flag()`'s docstring leans on **and** `rel()`'s binding to the swept-root
union. The `suite_contained()` half of this boundary is unaffected and stands
exactly as written above. Recorded here, in the section written to stop making
unverified survivability claims, because it was one.

**Stated boundary: the `warn` severity class is outside what the four-gate
harness can observe.** Recorded here as a limitation rather than left as a
silent exemption, because a silent exemption is the defect class this cycle
spent three review rounds on.

The linter emits findings at two severities. `fail` decides the exit code;
`warn` is printed and never does. Every check in §4's binding table whose
finding is `fail` — `check_structure()`, `check_size()`, the `skills/…` and
`agents/…` bases of `resolve_backtick_path()`, `skill_dir_of()`,
`check_retired_prefix()`, the `TEMPLATE_SOURCE` side — has its binding pinned
by a self-test case above, and reverting that binding fails
`skill-lint.py --self-test`. The table's third row does not and cannot be
pinned the same way: `resolve_backtick_path()`'s `docs/spec/<file>.md` span is
corpus-bound and `warn`, deliberately, so that the linter never assumes a
consumer repository carries this repository's layout. Rebinding that base to
the suite root was run as a mutation on 2026-09-21 and produced **136 spurious
`[path]` warnings with exit 0 on all four gates** — `skill-lint.py`,
`skill-lint.py --self-test`, `gc.py --fast` and `gc.py --self-test`. Nothing
in the harness observes it, because nothing in the harness reads warning
*counts*: the gates read exit codes, and a `warn` finding by construction does
not change one.

What this exempts, precisely: the root binding of the one `warn`-severity
backtick class, and any future check whose findings are `warn`-only. What it
does not exempt: every `fail`-severity binding above, and the `warn` findings
the self-test asserts by name and location (`template_pairs_bind_per_side`
reads the absent-spec warnings out of `Linter.findings` directly, which is the
technique available to any future case that needs a `warn` pinned).

Closing the gap in general means changing the linter's exit contract — a
`--strict` mode, or a warning-count comparand — and a change to the exit
contract is not something to land on the last iteration of a fix loop. It is
recorded here as a known limitation, in scope for a later cycle, and it is a
**boundary of the harness**, not an oversight in the bindings.

### Manual

- `REQ-PKG-MARKETPLACE-010`'s real-install observation is re-run against the
  moved tree at verify, recorded as an observation with its command.

### Acceptance Criteria

- [ ] `test -d plugins/sdd`, `test -f plugins/sdd/.claude-plugin/plugin.json`
  and `test -f .claude-plugin/marketplace.json` succeed; `test ! -e
  plugins/sdd/.claude-plugin/marketplace.json`; the parsed `source` resolves to
  `plugins/sdd`; every component-list path passes `test -e` under the suite
  root; membership is asserted per name against `git ls-tree -r --name-only` at
  the move commit's **parent**, and `git log --follow` resolves each moved file.
  **The stay-list is policed too**: each of `.claude-plugin/marketplace.json`,
  `docs/`, `CLAUDE.md`, `.pre-commit-config.yaml`, `README.md`, `LICENSE` and
  `CONTRIBUTING.md` is asserted **by name** to exist at the corpus root after
  the move — `README.md` and `LICENSE` being the only two that §Open Items also
  permits under the suite root, so only those two are exempt from a paired
  `test ! -e` under `plugins/sdd/` (REQ-PKG-PACKAGING-001).
- [ ] Constructor accepts distinct and equal pairs; equal roots reproduce the
  pre-change swept set; nested roots render per root; the zero-argument
  post-move run sweeps at least one `docs/spec/` path; and, on a pinned
  pattern rather than a reading — `grep -nE 'repo containing this
  script|defaults? to the (script|tool)' ` — the shipped `--help` output
  returns zero matches and `skill-lint-v5.md` returns matches **only** inside
  its §Two-Root Amendment, where the old wording is quoted in order to retire
  it (the one exclusion, stated here so the check does not fail on the sentence
  that fixes it) (REQ-PKG-PACKAGING-002). `grep
  -n 'no-suite-rules' plugins/sdd/tools/skill-lint.py` is empty, the argparse
  surface exposes no `--suite-root`, and every `suite_rules=False` site is
  inside the self-test (REQ-PKG-PACKAGING-003).
- [ ] **The retarget check, with a seeded ungated violation.** On a scratch
  tree whose corpus root has no `skills/` and whose suite root does, seeding
  `<corpus_root>/docs/spec/seeded-retired.md` with one unfenced retired-prefix
  tool name — the `check_retired_prefix` rule, ungated and corpus-bound,
  exception (i) of the amended F11 target: **no** finding carries a tag from
  `REQUIRED`, `VERSION_GATED_SKILLS` or `V4_CONTRACT_SKILLS`, **and** the
  findings list holds a finding whose path is `docs/spec/seeded-retired.md` and
  whose tag is `[retired-prefix]`, asserted by name. That seeded finding is
  what distinguishes a correctly retargeted linter from one whose checks are
  all switched off. Separately, on the pre-move tree pinned at `a1ab5ba` with
  equal roots, the finding set is unchanged from the pre-change single-root
  run, compared as a set derived at run time (REQ-PKG-PACKAGING-004).
- [ ] Fixture A reports **both** its seeded violations — one per root — each
  with the expected relative path and neither carrying a `plugins/sdd/` segment
  (REQ-PKG-PACKAGING-006); fixture B reports the table-row violation and **no**
  finding naming the seeded walk-class path while other findings are present
  (REQ-PKG-PACKAGING-007); case C counts its violation exactly once and **its
  own** negative case — §7's counting function (the pure function from swept
  list to findings) called with a hand-built swept list holding the seeded path
  twice — makes that count assertion fail and names the seeded path, §6's
  duplicate-guard negative case discharging nothing here
  (REQ-PKG-PACKAGING-008); each
  fixture asserts its own seeded count, adding a file without updating it
  fails, and binding the corpus walk to a root holding no corpus fails the
  count assertion (REQ-LINT-PACKAGING-006).
- [ ] Over `plugins/sdd/skills/`, a run-time grep for a drift-sweep invocation
  whose script path is bare `tools/gc.py` is empty, every drift-sweep
  invocation carries an explicit root argument naming the operator's working
  directory, and the verify skill's invocation runs from a scratch consumer
  repository without resolving its root to the suite (REQ-PKG-PACKAGING-009).
- [ ] Per-entry binding and rendering hold, no `ValueError` on two distinct
  roots, equal roots reproduce the pre-change set (REQ-LINT-PACKAGING-001).
  `TEMPLATE_PAIRS`, asserted per geometry rather than delegated: under nesting
  each row resolves its `TEMPLATE_SOURCE` side against the suite root and its
  `spec` side against the corpus root, and a row whose spec is present and
  anchored passes; under disjoint roots the spec side is **skipped**, asserted
  as **no** row emitting the absent-spec warning while other findings are
  present; with equal roots all four rows behave as before the change, compared
  as a set derived at run time. The negative control: binding both sides to the
  suite root makes all four rows emit the absent-spec warning, **which the
  self-test asserts must not happen** (REQ-LINT-PACKAGING-002). Both manifest paths are members of the two-root
  fixture's set and each one-root binding fails naming the missing path
  (REQ-LINT-PACKAGING-003).
- [ ] **The no-pinned-count check, as three runnable greps.** Scope, stated
  here rather than left to the implementer: `plugins/sdd/tools/skill-lint.py`
  **only** — the linter source and the self-test it carries, which are the only
  assertion contexts the requirement bars — excluding the self-test bodies of
  fixtures A, B and case C (identified by §7's fixture function names), whose
  seeded counts are sound literals. Each returns zero matches: `grep -nE
  '(FILES_SWEPT|files_swept|len\( *swept *\))[^\n]*(==|!=|>=|<=|<|>) *[0-9]+'`;
  `grep -nE '[0-9]+ *(==|!=) *(FILES_SWEPT|files_swept|len\( *swept *\))'`;
  `grep -n 'git ls-files'`. **Prose is deliberately out of scope**: a string
  grep over `docs/spec/` or over the other suite tools matches text that merely
  *names* the banned construction in order to ban it — §6 above, and
  `scope-check-selftest.py`'s status message — so run there it is
  self-falsifying rather than a check, and the requirement bars an assertion,
  not a mention. That no spec **asserts** a pinned count is therefore
  **reviewer-checkable** and named as such, as is an assertion in a spelling
  none of the three greps matches: the greps close the mechanical half, not the
  whole. The emission half is evaluated once the flag lands
  (REQ-LINT-PACKAGING-004).
- [ ] The guard runs on every invocation and is skippable by no mode; the
  checked-in negative case produces a `fail` finding naming the duplicated path
  (REQ-LINT-PACKAGING-005). `--print-population` exits 0 and its run-time-derived
  output **includes**, as a required subset, the four §6 populations by name and
  value — `REQUIRED=40`, `VERSION_GATED=9`, `V4_CONTRACT=7`, `FORBIDDEN=13` —
  each asserted present and unchanged, a missing line or a changed value
  failing; further table lines (today `TEMPLATE_PAIRS`) neither satisfy nor
  break it, per Q-IMPL-PACKAGING-001. The plan orders the flag task before the
  task evaluating that criterion (REQ-LINT-PACKAGING-007).
- [ ] `python3 plugins/sdd/tools/skill-lint.py --self-test` passes and
  `pre-commit run --all-files` exits 0 at the close of the cycle.

## Open Items

- `OPEN:` whether `plugins/sdd/` carries its own `README`/`LICENSE` — 45 versus
  47 installed files. Inherited and **not blocking**: either answer changes
  which root supplies those names, not whether they are policed, since §4 binds
  both to the union. Blocking constraint: a packaging-surface decision about
  what an installed plugin shows a reader, owned by no artifact in this cycle.

## Implementation Questions

### Q-IMPL-PACKAGING-001: `--print-population` prints a fifth table line
**Tier**: 2 (spec ambiguity)
**Spec reference**: §6 Counts: asserted, or only printed — "`REQUIRED=40
VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=13`"
**Decision**: the flag prints **one line per rule table**, derived from the
live tables at run time, which is **five** lines today — the four §6 names it
enumerates plus `TEMPLATE_PAIRS=4`. §6's enumeration is read as the **required
subset**, not as a closed list: every criterion phrased "prints the four
run-time-derived populations" (this spec's §Acceptance Criteria, the plan's
C7.3) is satisfied by a superset that carries those four lines with those
values, and is **not** satisfied by an output missing any of them. No number is
written into the flag or into `population_tables()`; both sides of the
self-test's `print_population_shape` case read the table lengths at call time.
**Rationale**: §6's own stated purpose for the flag is to catch a rule-table
row dropped or duplicated by §3's retarget. `TEMPLATE_PAIRS` is a rule table
subject to exactly that risk, so omitting it would leave the one table whose
per-side binding this cycle changed (§5) unwatched — the deviation serves §6's
purpose rather than diluting it. Recording it as a closed-enumeration deviation
rather than silently amending §6 keeps the pinned four values, and the sentence
that makes them the one asserted population in the corpus, exactly as approved.
The Chunk 4 verifier raised the extra line as a deviation from §6's letter;
this entry is that record (C6.14, added post-plan from the Chunk 5
verification).

### Q-IMPL-PACKAGING-002: `REQ-PKG-PACKAGING-002`'s `docs/spec/` sweep membership
**Tier**: 2 (spec ambiguity)
**Spec reference**: §2 The linter's two-root interface — `walk() ->
deduplicated union of <root>/skills/**/*.md over swept_roots()`; and
REQ-PKG-PACKAGING-002 §Acceptance, "sweeps at least one `docs/spec/` path"
**Decision**: that acceptance clause is **unsatisfiable against `walk()` as §2
defines it** — the walk is scoped to `<root>/skills/**/*.md` and reaches no
`docs/` path in any geometry. C7.1 evaluated it instead against
`retired_scope_entries()`, the one production surface that does bind a
`docs/spec` scope entry to the corpus root (§4's binding table), asserting
that a corpus-rooted run's entry set contains a `docs/spec/` path. The
substituted observable is kept; the criterion's literal wording is not.
**Impact**: the criterion is satisfied by a **different** surface from the one
its wording names, so a reader checking it against `walk()` finds nothing. Any
restatement must say `retired_scope_entries()`, not `walk()`. Recorded here
because the substitution had lived only in a commit body — a deviation from an
Approved acceptance criterion, which §Verification requires be traceable in
the spec (C8.5, added post-plan from the implement-stage review).

### Q-IMPL-PACKAGING-003: `--print-population` prints the guard's findings and may exit non-zero
**Tier**: 2 (spec ambiguity)
**Spec reference**: §6 Counts — "On failure the observable is a
`fail`-severity finding in the run's own findings list … and no invocation
mode can skip it", against the same section's "`--print-population` … Exits 0"
**Decision**: `print_population()` prints the findings its own
`skill_files()` call accumulated and returns 1 when any carries `fail`
severity. The two §6 sentences are in tension only for this mode:
`print_population()` invokes the union builder — which runs the
duplicate-freeness guard — and then discarded the findings, so the guard could
fire in that mode and be observed by nobody, which is exactly what
"no invocation mode can skip it" forbids. The unconditional-`exit 0` reading
is the weaker of the two: it is stated of the flag's *normal* behaviour, in a
paragraph whose subject is that the flag asserts no count, whereas the guard's
observability is stated as an absolute. Every run of a correctly constructed
union still prints nothing extra and still exits 0, so no green path changes.
**Rationale**: the guard is a construction guard whose whole value is that a
later edit rebuilding the union as concatenation is *seen*. A mode that
computes the guard and throws the answer away is the one way that value is
lost silently (C8.3, added post-plan from the implement-stage review).

### Q-IMPL-PACKAGING-004: the frozen `gc.py` shim under the two-root interface
**Tier**: 2 (spec ambiguity)
**Spec reference**: §2 The linter's two-root interface;
REQ-PKG-MARKETPLACE-007 (`gc.py` source frozen)
**Decision**: `gc.py` is **not edited**; the repair belongs entirely on the
linter side, and the freeze is left intact. `gc.py`'s fixture shim
(`lint_command()`) constructs `Linter(Path(sys.argv[2]), suite_rules=False)` —
a corpus root only, so `suite_root` falls back to `default_suite_root()`, the
**live installed suite**, disjoint from the fixture tree. Under the two-root
interface that is a *correct* call: §2 makes `suite_root` default to the
script's own plugin root, and the disjoint geometry excludes it from
`swept_roots()`. The hazard was never the shim — it was two checks
(`check_structure()`, `check_size()`) bound to `self.suite_root` instead of the
swept-root union, which made a disjoint suite root reachable by a check that
had no business reaching it: `check_size()` then measured the live suite from
inside a gc fixture run, `gc.py --self-test` went red, and a finding naming a
path outside `swept_roots()` raised an uncaught `ValueError` out of `rel()`.
With both checks on the union (§4, and REQ-PKG-PACKAGING-005's corpus-root
binding for size and frontmatter), the frozen shim's single-root call is
sound as written and needs no counterpart to `_run_capture()`'s guard.
**Impact**: the invariant a future edit must preserve is that **no ungated
check binds to `self.suite_root` alone**. When this entry was first written
the invariant was already false in this file: `check_links()` is ungated and
`resolve_backtick_path()` bound its `skills/…` and `agents/…` bases to the
suite root alone, which §4's C6.13 paragraph explicitly places under the same
binding as the two checks above. That was not a crash — the finding names the
swept file, not the base — but under the disjoint consumer geometry it
resolved a consumer's own span against the installed plugin cache. Those two
bases now take the union as well (`Linter.swept_base()`, C9.3, implement-stage
review round 2), so the invariant is stated true. Ungated checks take
`swept_roots()`; the suite-gated rows (§3) and the per-entry bindings of §4
and §5 supply their own rendering via `flag(..., rel=…)` precisely because
`rel()` cannot render a disjoint suite root's file. A caller that passes one
root is relying on that invariant, and `gc.py` is frozen, so the invariant
cannot be renegotiated from the caller's side (C8.6, added post-plan from the
implement-stage review).
