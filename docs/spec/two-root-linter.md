---
status: Approved
last_updated: 2026-09-22
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
  - REQ-LINT-PIPELINEOBSERVABILITY-001
  - REQ-PKG-CONSUMERGEOMETRY-001
  - REQ-PKG-CONSUMERGEOMETRY-002
  - REQ-PKG-CONSUMERGEOMETRY-003
  - REQ-PKG-CONSUMERGEOMETRY-004
  - REQ-PKG-CONSUMERGEOMETRY-005
  - REQ-PKG-CONSUMERGEOMETRY-006
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
  fixtures. **The `--suite-root` deferral recorded here held for the
  `packaging` cycle and is superseded by REQ-PKG-CONSUMERGEOMETRY-003 (§CG-2):
  the surface is adopted.** The deferral rested on reading the vendored-cache
  case as one residual case; the `consumer-geometry` delta re-measures it as the
  geometry every consumer of the installed plugin runs in, which is a closure
  owed rather than a mitigation offered. The `--no-suite-rules` leg of this
  bullet is **untouched** — the disable switch is still rejected and
  `suite_rules=False` is still constructor-only (REQ-PKG-PACKAGING-003
  leg (i)).

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
Its population criterion is stated here and nowhere else — the one place in
the corpus where a row population is compared against a number, sound because
rule-table rows are static in-code data.

`[Updated: 2026-09-22]` (workstream `pipeline-observability`,
REQ-LINT-PACKAGING-007 as amended, Q-REQ-PO-AL; the record of why is
§Pipeline-Observability Amendment): **the numbers are dated, and the comparand
is derived.** Current at 2026-09-22: `REQUIRED=42 VERSION_GATED=9 V4_CONTRACT=7
FORBIDDEN=14` (measured with `python3 plugins/sdd/tools/skill-lint.py
--print-population`); after this cycle's rows land — fourteen `REQUIRED` rows
p1–p14 and one `FORBIDDEN` row (`skill-lint-v5.md` §`REQUIRED` Rows —
Pipeline-Observability, §`FORBIDDEN` Row — `literal-anchor`,
REQ-LINT-PIPELINEOBSERVABILITY-001): `REQUIRED=56 FORBIDDEN=15`, the other two
unchanged. These numbers are **moved by any cycle that adds rows**, in the same
change as the table row. The criterion itself is a **three-way equality**, not
a frozen literal: `--print-population`'s printed counts == `len()` of the four
code tables == the numbers this paragraph states under its dated marker. The
self-test asserts that equality — it reads this section's numbers rather than
carrying its own `pinned = {…}` copy (today's dict is the third surface's
duplicate and goes) — so in a temp copy the suite fails when any one of the
three is changed alone: a row added to a table without moving this paragraph,
a number edited here without a row, or a count written into the flag as a
literal. Why derived: the earlier frozen form (`40 / 9 / 7 / 13`, then `42 /
14` after the research-gate routing rows) had to be chased in three places per
row-adding cycle and failed on the first landing that forgot one.

**What the four populations catch, stated exactly.** They catch an edit to the
rule **tables**: a row dropped, duplicated or added to `REQUIRED`,
`VERSION_GATED_SKILLS`, `V4_CONTRACT_SKILLS` or `FORBIDDEN` changes a printed
count and fails the criterion. They do **not** catch anything about the rows'
**binding**. The earlier wording here — that they are "a regression check on
§3's retarget, catching a row dropped or duplicated while moving the rows'
binding" — was false in its second half and is withdrawn: a population is
`len(<table>)`, read from the table object, and a retarget changes which root a
row is *resolved against*, leaving every row in place and every count
identical. The verify-stage red round demonstrated the gap — rebinding
`check_required()`'s two gated loops from `self.suite_root` to
`self.corpus_root` turns all sixteen gated rows into silent no-ops (each loop
is guarded by `if f.is_file()`, and a corpus root with no `skills/` satisfies
none of them) with all four gates at exit 0 and all four populations unchanged.
Bindings are pinned by the invertible geometry cases instead, one per bound
check — `check_required_gated_rows_bind_to_the_suite_root` for these sixteen
rows, alongside `check_structure_binds_to_the_swept_roots` and
`check_size_binds_to_the_swept_roots`. The flag lands **before** anything
evaluates it.

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
`skills/`) and `<skill-dir>` when it is that one skill's own directory
(`orchestrate/SKILL.md`'s `references/` links). The two are different
referents, not a divergence; each occurrence still expands its placeholder
inline at first use.

**Every gc invocation in every skill body takes `<plugin-dir>`** — the eight
in `orchestrate/` (`SKILL.md`, `USAGE.md`, `references/drift-sweep.md`)
alongside the one in `verify/SKILL.md`. The orchestrate eight were written
`<skill-dir>/tools/gc.py` on the reasoning that the copy then bundled under
the driver skill's own `tools/` subdirectory (REQ-PKG-MARKETPLACE-006's
duplicated-not-symlinked rule) would run. That reasoning was wrong and the sweep
was dead in every install: `gc.py` embeds the linter by sibling-first
resolution, that directory held only `gc.py` and `telemetry.py`, and the
fallback `<root>/tools/skill-lint.py` was exactly the path the move deleted, so
the documented command printed `error: linter missing` and exited 2 everywhere.
That bundled directory was itself removed on 2026-09-21 under
REQ-PKG-CONSUMERGEOMETRY-005, so no copy of it survives to be named.
One convention, one place a consumer's linter is looked for. A consequence to
carry forward: **no invocation anywhere now resolves to the bundled copy**, so
REQ-PKG-MARKETPLACE-006's added criterion "at least one invocation resolves to
the bundled copy" (`docs/ws/marketplace/verification.md`) no longer holds; the
copy stays on disk under that requirement's duplication rule and its fate is a
later cycle's decision. The repair is **sequenced
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
  -n 'no-suite-rules' plugins/sdd/tools/skill-lint.py` is empty and every
  `suite_rules=False` site is inside the self-test (REQ-PKG-PACKAGING-003
  leg (i), which stands; the middle clause of this item was excised under
  REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4 when §CG-2's surface landed).
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
- [ ] Over `plugins/sdd/skills/`, a run-time grep for a drift-sweep
  **invocation** whose script path is bare `tools/gc.py` is empty; every
  drift-sweep invocation carries an explicit root argument naming the
  operator's working directory; and the invocation runs from a scratch consumer
  repository without resolving its root to the suite — asserted for the verify
  skill's and for `orchestrate/`'s, both of which now spell the script
  `<plugin-dir>/tools/gc.py` (§8) (REQ-PKG-PACKAGING-009).
  **An invocation is a command line the body tells the reader to run** — in
  practice a `python3 …gc.py …` span. A bare `tools/gc.py` inside a *rendered
  message* is not one and is out of this criterion's scope: the `GC: F fail, W
  warn — run tools/gc.py --report` gate line (`orchestrate/SKILL.md`,
  `USAGE.md`, `references/drift-sweep.md`) is text the driver prints to the
  operator, whose wording is fixed by `docs/spec/drift-sweep.md`, not a command
  the skill runs. The distinction is stated here because the criterion read as
  a literal grep is false and always was — the red round checked it and found
  those three sites (R1's sibling suspicion at the verify stage). **One
  recorded residue, not repaired here:** `plugins/sdd/tools/gc.py`'s `AGG_FIX`
  remediation string also names a bare `tools/gc.py`, and *that* one a
  consumer would paste, in a repository where the path does not exist. It is a
  printed message and so outside this criterion, but it is a real consumer
  defect; `gc.py` was frozen to this cycle's write scope, so it is recorded
  against `REQ-PKG-PACKAGING-009` for a later cycle rather than fixed.
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
  assertion contexts the requirement bars — excluding **as a class, not as a
  list of case names**, the self-test's *fixture-literal* assertions: a match
  inside `self_test()` whose counted list was derived entirely from a tree the
  case itself seeded under the self-test's scratch root, or hand-built inside
  the case as a literal list of paths. Those counts are sound — such a list
  cannot grow by contribution, and a literal is the only comparand that catches
  a mis-bound root sweeping nothing (§7). Everything else is a finding,
  including any assertion whose counted list comes from a **live** corpus root
  (a `Linter` built on a path the case did not seed), which is exactly the
  construction the requirement bars, and including any such assertion outside
  `self_test()`. The exclusion is deliberately **not** the enumeration
  "fixtures A, B and case C" it was first written as: that went stale the first
  time a later case landed a sound fixture literal —
  `walk_dedupes_repeated_roots`'s `check(len(swept) == 1, …)` over a
  two-element hand-built root list — which the first grep matches while the
  enumeration does not name it, making the criterion false as written while
  nothing was wrong with the code (verify-stage red round, R1). Each returns
  zero matches **after** that class is set aside: `grep -nE
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
  (REQ-LINT-PACKAGING-005).

**Pipeline-observability (2026-09-22, two-root linter)**

- [ ] `[Updated: 2026-09-22]` (REQ-LINT-PACKAGING-007 as
  amended, Q-REQ-PO-AL): `--print-population` exits 0 and its run-time-derived
  output **includes**, as a required subset, the four §6 populations by name;
  the **three-way equality** holds — the printed counts equal `len()` of the
  four code tables and equal the numbers §6 states under its dated marker
  (`REQUIRED=42 VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=14` on 2026-09-22,
  measured with the command §6 names; `56` / `15` once this cycle's rows land)
  — and the self-test asserts the same equality, failing in a temp copy when
  any one of the three is changed alone (a row added without moving §6, a §6
  number edited without a row, a count written into the flag as a literal), a
  missing population line failing likewise; further table lines (today
  `TEMPLATE_PAIRS`) neither satisfy nor break it, per Q-IMPL-PACKAGING-001. The
  plan orders the flag task before the task evaluating that criterion
  (REQ-LINT-PACKAGING-007).
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
**Spec reference**: §6 Counts: asserted, or only printed — "`REQUIRED=42
VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=14`"
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

## Consumer-Geometry Amendment (2026-09-21, REQ-PKG-CONSUMERGEOMETRY-001..006)

This amendment is the design for the `consumer-geometry` delta. Its subject is
the geometry in which the suite root is **disjoint** from the corpus root — the
only geometry a consumer of the installed plugin ever has, and the geometry in
which §2's `swept_roots()` union collapses to the corpus root alone so the suite
is not walked at all. The three-class impact (one loud reduction, four vacuous
passes, three wrong-tree runs) is carried evidence from RS-CONSUMERGEOMETRY-001
and is cited, never re-derived.

Three geometry names are used throughout, and they are the same three §7 already
names: **nested** (suite root contained in the corpus root), **equal**, and
**disjoint** (suite root outside the corpus root). "Observation geometry" is the
disjoint case where the corpus is *this* repository and the suite root is an
out-of-tree copy of the tool; "consumer geometry" is the disjoint case where the
corpus is a foreign repository.

**Line numbers cited in this delta, reconciled once.**
REQ-PKG-CONSUMERGEOMETRY-003 and -005 cite this file at `:83`, `:360` and
`:516-517`, measured before this amendment was appended. Appending it added six
lines to the frontmatter's `requires:` list, so every citation below the
frontmatter has shifted by **+6**: the deferral sentence is now `:89`, the
`skills/orchestrate/tools/` prose is now `:366`, and the three-clause checklist
item is now `:522-523`. **The content, not the number, identifies each site** —
every criterion in this amendment is stated against a quoted string so it stays
decidable after any further shift, and the numbers are given only as a reading
aid. The same reconciliation for `marketplace-packaging.md` (`+2`) is in that
file's §Consumer-Geometry Amendment.

### CG-1. Where the derivation lives: `skill-lint.py`, not `gc.py`

REQ-PKG-CONSUMERGEOMETRY-006's body scopes the derivation to `gc.py` ("Where
`gc.py` obtains a suite root, given it has none today") while its acceptance 1
asserts on a **directly invoked** `skill-lint.py` that never passes through
`gc.py`. That is the first of the three items the requirements stage recorded as
owed to this stage (`docs/requirements/index.md` §Open Questions, the
`[consumer-geometry, OWED TO SPECS]` entry, item 1). **Decision: the derivation
lives in `skill-lint.py`, and `gc.py` inherits it for free.** The criterion is
not weakened; the body sentence is read as satisfied *derivatively*, because the
suite root `gc.py`'s sweep ends up with is the one the linter derives from the
corpus root `gc.py` hands it.

Why this way and not the other: of REQ-PKG-CONSUMERGEOMETRY-006's five
acceptances, 1, 4 and 5 are stated against a `skill-lint.py` invocation and 3 is
stated against `swept_roots()`, which is the linter's own function. Only
acceptance 2 goes through `gc.py`, and it goes through it as a *consumer* of the
linter's behaviour ("the far `gc.py --report` raises no `[structure]` finding").
A `gc.py`-only derivation would leave four of the five undecidable or
permanently red and would additionally leave a directly invoked linter — the
form a contributor types — unrepaired. A linter-side derivation makes all five
decidable, and assertion 2 follows from assertion 1 by the sweep's
pass-through rather than by a second implementation.

This decision does **not** absorb REQ-PKG-CONSUMERGEOMETRY-003 assertion 3.
`gc.py` must still *pass through* an **explicit** operator-supplied suite root on
both of `lint_command()`'s branches (§CG-2): the derivation covers the case where
nobody supplied one, and the pass-through covers the case where somebody did.
The two are different code paths and different precedence tiers (§CG-3), and
implementing only the derivation leaves the explicit surface unreachable through
the sweep, which is exactly what assertion 3 turns red on.

### CG-2. The `--suite-root` surface (REQ-PKG-CONSUMERGEOMETRY-003)

§2's sentence "`--suite-root` is **deferred**, not adopted" is **superseded**.
The surface is adopted. §2's no-`--no-suite-rules` decision is untouched and
stands.

```
skill-lint.py [corpus_root] [--suite-root PATH]
  --suite-root PATH : absolute or cwd-relative; resolved to an absolute path and
                      passed to Linter(..., suite_root=PATH)
  omitted           : the derivation of §CG-3 runs
```

`gc.py` grows the matching pass-through. **How the suite root enters `gc.py` is
decided in `drift-sweep.md` §1** — a `--suite-root PATH` flag plus a
`Gc(..., suite_root=None)` constructor parameter carrying the same value, with
"pass nothing" as the default so the linter's tier-2 derivation answers. Neither
exists today, and until one does neither half of the criterion below is
constructible. `lint_command()` has **two** return
paths and both are in scope, because repairing one leaves the other permanently
degraded with nothing able to observe it:

- **(i) the `lint_suite_rules` argv branch** returns
  `[executable, str(lint), str(self.root)]`. The constructed vector must carry
  the suite root. Asserted **on the vector**, not on the subprocess result, so
  the assertion does not depend on what the linter then does with it.
- **(ii) the `suite_rules=False` `-c` shim branch** builds no argv at all: it
  builds a `-c` program constructing `Linter(Path(sys.argv[2]), suite_rules=False)`
  with no suite-root parameter anywhere. The shim must pass the same suite root
  to that constructor. Asserted by parsing the shim text for the parameter **or**
  by running the shim against a fixture and reading back `suite_contained()`;
  either is sufficient, and the fixture form is preferred because it also
  exercises the argument-passing. Q-IMPL-PACKAGING-004 records that this shim is
  the frozen caller under the two-root interface; that freeze is retired for this
  edit by REQ-PKG-CONSUMERGEOMETRY-001 row 4.

**What turns each red.** (i): reverting the branch to `[executable, str(lint),
str(self.root)]` drops the suite root from the vector — that is row 4 of the
REQ-PKG-CONSUMERGEOMETRY-001 enumeration, so it is demonstrated by running the
mutation, not asserted. (ii): fixing (i) alone and leaving the shim's
`Linter(...)` call unchanged leaves the shim's `suite_contained()` reading the
default-derived root, so the branch-(ii) half is red while the branch-(i) half is
green. That opposite-direction pair is what makes the two-branch wording
load-bearing rather than decorative.

**Two sentences in this file assert the surface's absence, not one.**
REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4 names `two-root-linter.md:516-517`. A
run-time grep finds a **second** site the requirement does not name: §2's
"`--suite-root` is **deferred**, not adopted — it mitigates the one unclosed
vendored-cache case…" (:83). Acceptance 4 is stated as "that file contains no
sentence asserting the **absence** of a `--suite-root` surface", which is a
file-wide claim, so both sites are in scope and correcting only the named one
leaves acceptance 4 red. Recorded here because it is a requirement-side omission
the implement stage would otherwise discover at the gate.

The two corrections are **not the same edit**:

- **:516-517 — excise one clause, keep the item.** The checklist item reads
  *"… is empty, the argparse surface exposes no `--suite-root`, and every
  `suite_rules=False` site is inside the self-test"*. Only the middle clause
  dies. The `no-suite-rules` grep clause and the `suite_rules=False` containment
  clause are REQ-PKG-PACKAGING-003 leg (i), which **stands**; retiring the whole
  item would delete a pin this delta explicitly preserves.
- **:83 — re-scope the sentence in place**, recording that the deferral held for
  the `packaging` cycle and is superseded here, in the same shape §2's other
  superseded claims carry.

Both land under REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4.

### CG-3. The corpus-root derivation and its precedence (REQ-PKG-CONSUMERGEOMETRY-006)

When no explicit suite root is supplied, the linter **derives** a candidate from
its own corpus root rather than inventing one. This is discovery, not invention:
the adopted root names a plugin demonstrably present in the tree being linted.

```
candidate = corpus_root / "plugins" / "sdd"
adopt candidate  iff  candidate.is_dir()
                 and  (candidate / "skills").is_dir()
                 and  candidate.resolve() != default_suite_root().resolve()
```

**Where the tiers are resolved: inside `Linter.__init__`, not in `main()`.**
This is load-bearing and is pinned rather than left to the implementer.
`Linter.__init__` (`skill-lint.py:516-523`) already resolves the tier-3 fallback
in the constructor — `self.suite_root = default_suite_root() if suite_root is
None else suite_root` — and **tier 2 joins it there**, in the same expression's
place, so the resolution order is one piece of code that every construction path
reaches. Three paths exist and all three must get the same answer:

| Construction path | Reaches tier 2 iff it lives in the constructor |
|---|---|
| the CLI (`main()` → `Linter(...)`) | yes either way |
| **`gc.py`'s branch-(ii) `-c` shim** — `m.Linter(Path(sys.argv[2]), suite_rules=False)` (`gc.py:507-516`) | **only if it lives in the constructor**; the shim never enters `main()` |
| a self-test fixture constructing `Linter(...)` directly | same |

If tier 2 lived in argument handling, the shim would be frozen on tier 3
**permanently** — and `drift-sweep.md` §2's "with `suite_root is None` both
branches are byte-identical to today's" would freeze it there by contract rather
than by accident. That pin is about the **constructed argv vector and shim
text**, not about the geometry the shim then resolves: the shim passes no suite
root, and the constructor answers with tier 2 or tier 3 exactly as the CLI would.
This is also the whole content of §CG-1's "`gc.py` inherits the derivation for
free" — it is true **only** under constructor resolution, so the two statements
stand or fall together.

**Precedence, in order** — exactly three tiers, and no fourth:

1. an explicit operator-supplied suite root (`--suite-root`, or the constructor
   parameter, or `gc.py`'s pass-through of either) — always wins, adopted
   without any existence test, so an operator can still name a root the
   derivation would have rejected;
2. the corpus-derived candidate above, when all three conditions hold;
3. today's `default_suite_root()` — `Path(__file__).resolve().parent.parent`.

The third condition of tier 2 is not cosmetic: for an **in-repo** copy the
candidate and `default_suite_root()` are the same directory, so tier 2 must
decline and leave tier 3 to answer, or a contained case risks being re-rooted or
double-counted. REQ-PKG-CONSUMERGEOMETRY-006 acceptance 4 is the assertion that
it does not.

**The literal `plugins/sdd` is a stated limitation.** A foreign tree that holds
`plugins/sdd/skills/` — a fork of this repository, or an identically laid out
marketplace — **will** fire tier 2 and be re-rooted onto its own copy. That is
correct for a fork and tolerable for a look-alike, since the adopted root is a
plugin actually present in the tree being linted. What it must never do is fire
on a tree that has no such directory.

### CG-4. The owed criterion: the derivation's **positive** direction

Second of the three owed items. REQ-PKG-CONSUMERGEOMETRY-002's consumer bullet
cites REQ-PKG-CONSUMERGEOMETRY-006 acceptances 3 and 5 as asserting "both
directions" of the fork/look-alike exception. **They do not.** Acceptance 3 is
"no `plugins/sdd/` → does not fire" and acceptance 5 is "`plugins/sdd/` present
but no `skills/` → does not fire" — both negative. The positive case, a foreign
tree that *does* hold `plugins/sdd/skills/` being re-rooted onto it, is the one
behaviour REQ-PKG-CONSUMERGEOMETRY-002 admits departs from "today's union,
unchanged", and it has no fixture. This section supplies the criterion and the
fixture shape.

**Fixture D — the look-alike corpus** (new, in the existing `--self-test`
scratch-root style, no cache write). A scratch corpus root `F`, disjoint by
construction from the running tool, holding **both**:

```
F/skills/<name>/SKILL.md                  # the foreign repo's own skill
F/plugins/sdd/skills/<name>/SKILL.md      # a look-alike suite, seeded with one
                                          # walk-class violation (forbidden
                                          # phrase or bad frontmatter)
```

The tool is invoked with corpus root `F` and **no** explicit suite root.

**Criterion (REQ-PKG-CONSUMERGEOMETRY-006, acceptance 6 — added by this spec):**
the derivation fires and is observable in four ways at once —
`suite_contained()` is `True`; the emitted token reads `GEOMETRY: nested` with
`swept-roots=2`; `suite-rows-root=` renders `F/plugins/sdd`; and the violation
seeded under `F/plugins/sdd/skills/**` **is** reported, with its path rendered
relative to the root it was walked from (so `skills/…`, with no `plugins/sdd/`
segment), asserted **by name on that seeded path** rather than by a count.

**What turns it red, and that state exists today.** Today no derivation exists:
the suite root falls to `default_suite_root()`, which for a tool running outside
`F` is outside `F`, so `suite_contained()` is `False`, the token would read
`disjoint`, `swept-roots=1`, and the seeded suite-side violation is **not**
reported. The criterion is therefore red before the change and green after. After
the change, three separate mutations return it to red: dropping tier 2 of §CG-3's
precedence; keying tier 2 on the tool's own location instead of the corpus root
(which is also the mutation acceptance 3 catches, in the opposite direction); and
rendering the suite seed against the corpus root, which makes the path
`plugins/sdd/skills/…` and fails the by-name assertion. The last of these is the
per-root-rendering pin of §7 fixture A, re-exercised in a geometry fixture A
does not reach.

**REQ-PKG-CONSUMERGEOMETRY-002's citation must be corrected at the same time**,
and the correction is in scope for the implement stage under this section rather
than a follow-up. The mechanism is the one this corpus already uses for an
Approved requirement a later cycle amends: an appended dated
`[Updated: 2026-09-21c — …]` note beneath REQ-PKG-CONSUMERGEOMETRY-002 in
`docs/requirements/integration/packaging.md`, recording that acceptances 3 and 5
assert the **negative** direction only and that the positive direction is
acceptance 6, specified here. The consumer bullet's own sentence is not rewritten
— appending a dated note is how every other supersession in that file is
recorded, and rewriting the sentence would make the record disagree with the
commit that approved it.

### CG-5. The per-geometry split (REQ-PKG-CONSUMERGEOMETRY-002)

The disjoint geometry gets **two different answers**, because the operator's own
repository and a foreign consumer's are not the same problem.

- **Observation geometry — Option A.** The invocation reaches an explicit or
  derived suite root naming the corpus's own `plugins/sdd`. That makes
  `suite_contained()` true and restores the nested geometry: the walk reaches the
  working tree's files and all three Class C checks re-root onto the working tree
  instead of the plugin cache. Option A discharges Class C **for this geometry
  only**, as a side effect of re-rooting, with **no** rebinding of the 56
  suite-gated rows. §3's retarget stands unamended.
- **Consumer geometry — today's union, unchanged**, with the single stated
  exception of §CG-4's look-alike class. Their corpus root holds their own
  `skills/`, which §2's union already walks correctly. Their exposure is
  **signalling only** — which tree the 56 suite rows were evaluated against — and
  that is §CG-6's job, not a binding's.
- **Option B is rejected**, and the rejection is *enforced*, not recorded:
  admitting a disjoint suite root into `swept_roots()` would make the four
  Class B checks walk the *cache's* `skills/**`, converting a loud reduction into
  a silent wrong-tree pass. §7 fixture B's `swept_roots() == {corpus_root}`
  assertion is what fails if Option B is implemented.
- **C-1 is withdrawn; Class C is not closed for a foreign consumer.** Rebinding
  the 56 rows to the swept-root union would reverse the gate-pinned invariant
  C12.1. The narrower proposal — rebinding the **40** `REQUIRED` rows alone,
  which C12.1 does not pin — was handed to this stage as a separate argued
  proposal. **This spec declines it.** It is declined on scope, not on merit: the
  40 rows' binding is currently unasserted in every geometry, so adopting the
  rebinding would land a behaviour change with no fixture able to falsify it —
  the defect class this delta exists to close. Supplying that fixture is not in
  this cycle's requirement set. Recorded in §Open Items below rather than left
  as a silent non-decision.

### CG-5a. Tier 2 makes one inherited fixture shape unsatisfiable

REQ-PKG-CONSUMERGEOMETRY-002 acceptance 1's second half — "in the same fixture
with the suite root left to default to a **far** scratch root,
`len(skill_files())` is zero" — was written before §CG-3's tier 2 existed. Once
tier 2 lands, a corpus root that holds its suite at **`plugins/sdd`** fires the
derivation in exactly that half: no explicit root is passed, the candidate
`corpus_root/plugins/sdd` exists and holds `skills/`, so it is adopted, the walk
reaches it and `len(skill_files())` is **not** zero. The criterion would be red
by construction, against a correct implementation.

This is not hypothetical, and it is the trap an implementer walks into: §7
**fixture A is defined as `suite_root = corpus_root/plugins/sdd`**, so reusing
fixture A's tree for the -002 criterion reproduces the failure exactly.

**Decision — pin the fixture's spelling, do not restate the criterion.** The
fixture for REQ-PKG-CONSUMERGEOMETRY-002 acceptance 1 places its suite
subdirectory under a name **other than `plugins/sdd`** — `vendor/suite` is the
spelling this spec adopts — so tier 2 **declines by construction** (its first
condition, `candidate.is_dir()`, is false) and the second half falls to tier 3,
the far scratch default, with `len(skill_files()) == 0` exactly as the
requirement words it. Tier 1 is unaffected: an explicitly passed suite root is
adopted whatever the directory is called, so the first half is unchanged. The
requirement's wording therefore needs no restatement and none is made.

**Belt and braces, for a reader who meets a `plugins/sdd`-named fixture anyway:**
in such a fixture the second half yields the **tier-2** root, not the tier-3
default, and the correct expectation there is `GEOMETRY: nested` with a non-zero
`skill_files()` — which is §CG-4's fixture D, a different criterion with a
different verdict. The two must not be conflated, and naming the subdirectory
differently is what keeps them apart.

**The twin case is already reconciled.** REQ-PKG-CONSUMERGEOMETRY-003
acceptance 2's "yields the default-derived root" is restated in this spec's
criterion as "yields the tier-2-or-3 root of §CG-3", which is correct under
either spelling because that criterion asserts only that the two runs *differ*.
-002 acceptance 1 asserts a **zero**, which is why it needs the fixture pin and
-003 acceptance 2 does not.

### CG-6. `GEOMETRY:` and `— NOTHING SWEPT` (REQ-PKG-CONSUMERGEOMETRY-004)

A run that swept nothing must not be spelled like a run that swept everything.
Two output tokens close that, and their text is fixed verbatim because their
whole value is that a reader and a fixture can both match on them. One concrete
instance, printable exactly as shown — the literal line shape, not a schema:

```
GEOMETRY: disjoint  swept-roots=1  suite-rows-root=<suite root as given>
OK: 0 file(s) clean — NOTHING SWEPT
```

- **`GEOMETRY:` is an own-line token emitted immediately before the summary
  line**, whether or not the run has findings. "Every run" is scoped to runs that
  print one: the token is emitted **iff** the run prints an `OK:`/`FAIL:` summary
  line — one token per summary, never two, never one without the other — which
  excludes `--self-test`, whose banner is not a corpus summary. A self-test case
  asserts on the token by constructing a sweep and reading that sweep's output.
  `skill-lint-v5.md` §The `GEOMETRY:` token is not a finding carries the same
  scoping, and neither restates `--print-population`'s summary behaviour, which
  is Q-IMPL-PACKAGING-003's. Its value has exactly three
  members — `nested`, `equal`, `disjoint` — derived from `suite_contained()` and
  root equality. The spelling `nested | equal | disjoint` appears in **no**
  output; the enum is prose. `swept-roots=<n>` is `len(swept_roots())`.
  `suite-rows-root=<path>` is the **effective** suite root — the one the run
  actually resolved through §CG-3's three tiers, whether it was **given**
  (tier 1), **derived** (tier 2) or **defaulted** (tier 3). The upstream
  requirement words it "as given", which has no verdict for a tier-2 run because
  tier 2 did not exist when it was written; the effective-root reading is the
  only one that renders a value in all three tiers, and it preserves the field's
  whole purpose — the answer to "which tree were the 56 suite-gated rows
  evaluated against", and the whole of what a foreign consumer is owed here. The
  exclusion is restated to match: the field renders **neither the corpus root,
  nor `default_suite_root()` when tier 1 or tier 2 supplied a root**. In a
  tier-3 run it renders `default_suite_root()`, because there the default *is*
  the effective root. **This re-reading, and the "every run" scoping below, each
  owe REQ-PKG-CONSUMERGEOMETRY-004 an appended `[Updated:]` note** — §CG-4's rule
  for a spec that reinterprets an Approved literal applies to -004 exactly as it
  applies to -002, and §CG-11 carries both notes in the implement stage's
  requirements-write task.
- **The `— NOTHING SWEPT` suffix is present iff `len(skill_files()) == 0`**, on
  **every** summary line. There are **three** print sites and all three are in
  scope: `skill-lint.py:1186` (`FAIL: …`), `:1189` (`OK: … clean, W warning(s)`,
  the warn variant) and `:1191` (`OK: … clean`, the clean variant). Patching only
  the two `OK:` sites leaves the failing path unsuffixed, which is the concrete
  failure REQ-PKG-CONSUMERGEOMETRY-004 acceptance 4 exists to catch.

**This is not the existing `corpus: FILES_SWEPT=<n>` line promoted.** §6's
give-up on live zero-sweep detection stands: a swept-file *count* from a live
corpus still cannot be asserted, the count stays informational, and what becomes
load-bearing is an **enum** and a **presence-iff suffix**, neither of which is a
count. REQ-LINT-PACKAGING-004's "`FILES_SWEPT=<n>` is informational" clause is
unchanged.

**`gc.py` forwards the token verbatim, and derives none of its own.**
`sweep_lint()` (`gc.py:520-537`) passes through only two-line finding pairs
matching its finding regex plus the last non-empty line when it matches
`^(OK|FAIL): `; every other line of the linter's stdout is discarded, so an
own-line `GEOMETRY:` token reaches nobody through the sweep. `gc.py` must forward
it on its own line, unmodified. It must **not** compute the token: the linter is
the only process that knows its own roots, and a second derivation is a second
thing to get wrong. Falsifying construction: in §CG-8's disjoint scratch
construction, `gc.py --report` output contains a line beginning `GEOMETRY: `; it
contains none today, and removing the forwarding returns it to none.

**The sweep's summary check is a prefix match and is therefore safe.**
`sweep_lint()` tests the linter's last non-empty line with
`re.match(r"^(OK|FAIL): ", summary)` — unanchored at the right — so the suffix
cannot make it flag `linter exited … without a parseable summary`. No amendment
needed; audited here because it is the pin an implementer adding a suffix is most
likely to trip over.

**The summary-line pins elsewhere: three sites, not two.**
REQ-PKG-CONSUMERGEOMETRY-004's interaction note names
`docs/spec/skill-lint-v5.md:427,452` and
`docs/requirements/integration/skill-lint.md:276`. A run-time grep finds a
**third** in the same spec, at `skill-lint-v5.md:127`, in §Size Warn-Clean
Baseline. **Those three numbers are pre-amendment**: appending
`skill-lint-v5.md` §Consumer-Geometry Amendment added two `requires:` lines, so
they are now `:129`, `:429` and `:454`, and the content identifies each site —
all three are `OK: N file(s) clean` pins. The requirements-side `:276` is
unshifted. All are `OK: N file(s) clean` pins and all are in scope for the
implement stage's "confirm these matches are not end-anchored" check; amending
any that is end-anchored is in scope under REQ-PKG-CONSUMERGEOMETRY-004. `N` is
non-zero on this corpus and the suffix is additive and conditional, so none is
expected to need amendment — the check is that the expectation is verified rather
than assumed. `skill-lint-v5.md` §Consumer-Geometry Amendment carries the
spec-side statement.

### CG-7. The enumerated comparand set and its reporting surface (REQ-PKG-CONSUMERGEOMETRY-001)

Tool source under `plugins/sdd/tools/` may be edited for consumer-geometry
correctness, over the **enumerated** eight-row set in
REQ-PKG-CONSUMERGEOMETRY-001's table. The table is the comparand; the count
"eight" is informational prose and is never a literal a criterion is evaluated
against. A row is the unit — rows 4, 5 and 7 each cover more than one line of
source and are each discharged by one `--self-test` case.

**The per-case reporting surface, stated because the criteria are otherwise
unobservable.** `--self-test` accumulates every failure into one `failures` list
and prints it as `SELF-TEST FAIL:` followed by one `- <string>` line per failure,
returning `1` **once, for the process**; the `SELF-TEST OK:` banner is a single
hand-written prose sentence, not a machine-readable case list. A case does not
exit — the process does. Therefore:

- Each of the eight rows is bound to a case whose failure string **begins with a
  stable row token** `cg-row-<n>:`, contributed to that same `failures` list. The
  **failure-string list is the per-case surface**, and every assertion is stated
  against it rather than against the banner or the process exit code.
- The eight tokens are additionally carried in **one named constant inside the
  tool**, and `--self-test` asserts that every member of that constant is
  registered and run. Rows 1-3 and 5-8 register in `skill-lint.py --self-test`;
  row 4 registers in `gc.py --self-test`.
- **Membership, not the process exit code, is the comparand for every mutation
  run.** Row 2's mutation — rebinding the 56 gated rows to the corpus root — also
  trips the pre-existing C12.1 fixture, so a green-to-red transition of the
  *process* would not show that the new disjoint case fired at all. The assertion
  is that the printed list contains a line beginning with that row's own
  `cg-row-<n>:` token.
- The tool cannot read this table: `docs/` is outside the shipped plugin, so no
  shipped tool may read it. That is why the set-equality reconciliation between
  the requirement's table and the tokens `--self-test` prints is a **desk check
  owned by the verify stage**, recorded in
  `docs/ws/consumer-geometry/verification.md`, and carries a plan task of its own
  (the third plan-ordering constraint of `docs/requirements/index.md`).

**The spec-side freeze criterion is repinned under this requirement, not
under -005.** `docs/spec/marketplace-packaging.md:366` asserts
REQ-PKG-MARKETPLACE-007's source freeze against the **working tree**, by content
identity, with an accepted alternative naming `HEAD`; both spellings leave the
right endpoint unpinned. Row 4 of the enumeration and
REQ-PKG-CONSUMERGEOMETRY-005's `AGG_FIX` correction each edit
`plugins/sdd/tools/gc.py`, so that item turns red at the next gate — not because
the freeze was violated but because it is evaluated outside its own window. It is
repinned to the packaging cycle's end sha `0bdb076`, asserted **on that named
item** and never as a file-wide grep (`HEAD` occurs in that file in unrelated
contexts, and "the working tree" has no grep spelling at all).
`marketplace-packaging.md` §Consumer-Geometry Amendment carries the edit.

### CG-8. The disjoint scratch construction

Every criterion in this amendment that needs a disjoint geometry uses one
construction, **disjoint by construction rather than by reference to any in-repo
path**, because every committed hook and every in-repo invocation is already
nested:

```bash
REPO=$(git rev-parse --show-toplevel)
rm -rf "$TMPDIR/cg" && mkdir -p "$TMPDIR/cg"
cp -R "$REPO/plugins/sdd" "$TMPDIR/cg/far"     # the installed cache is never touched
python3 "$TMPDIR/cg/far/tools/skill-lint.py" "$REPO"
python3 "$TMPDIR/cg/far/tools/gc.py" --report --root "$REPO"
```

Measured before any change: the far `skill-lint.py` prints
`.: [structure] skills/ directory not found` then `FAIL: 1 finding(s), 0
warning(s)`; the far `gc.py --report` passes that same finding through. Required
after: `GEOMETRY: nested`, no `[structure]` finding, a non-zero swept-file count
from the linter, and that finding absent from the sweep. The in-repo
`skill-lint.py` is unchanged at `GEOMETRY: nested` and its 25-file count, derived
at run time rather than pinned as a literal.

**No assertion is made about the committed hook set, deliberately.** Every
`.pre-commit-config.yaml` entry runs an in-repo copy, so every one is already
nested and none can be "left on the degraded default"; an assertion over them
would describe a state that cannot occur. The only real hook-relevant risk is
that the change regresses the nested case they all run in, and
REQ-PKG-CONSUMERGEOMETRY-006 acceptance 4 covers it.

### CG-9. The correction landing sites owned by this file

**Three** edits to **this** file are owed, under two different requirements,
and they are named so the plan stage can size them separately — the count is the
table's row count below, which this sentence now agrees with and this section's
closing criterion already did:

| Site | Requirement / acceptance | Edit |
|---|---|---|
| `two-root-linter.md:83`, now `:89` (§2, "`--suite-root` is **deferred**, not adopted") | REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4 | re-scope in place: the deferral held for the `packaging` cycle and is superseded here |
| `two-root-linter.md:516-517`, now `:522-523` (§Acceptance Criteria, the middle clause of a three-clause item) | REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4 | excise the middle clause only; the `no-suite-rules` grep and `suite_rules=False` containment clauses stand (REQ-PKG-PACKAGING-003 leg (i)) |
| `two-root-linter.md:360`, now `:366` (§8 prose, `skills/orchestrate/tools/`) | REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2 (class A) | make true in place: the directory is removed, so the sentence's account of why the bundled sweep was dead is restated in the past tense against the removal |

### CG-10. Plan-ordering constraints — a fourth, and why

Three are recorded in `docs/requirements/index.md`. This is the **fourth**, and
it settles the third owed item:

> **REQ-PKG-CONSUMERGEOMETRY-004's `GEOMETRY:` token lands before
> REQ-PKG-CONSUMERGEOMETRY-006's acceptance 1 is evaluated.**

REQ-PKG-CONSUMERGEOMETRY-006 acceptance 2 already explains that it asserts on the
finding set rather than on the token "because the token's forwarding is a
separate requirement whose landing order is not fixed here" — while acceptance 1
asserts `GEOMETRY: nested` **directly**, which is undecidable until -004 lands.
The requirement offers two remedies; this spec takes the ordering constraint
rather than splitting acceptance 1, because the split would leave acceptance 1's
token clause homeless and §CG-4's new acceptance 6 asserts on the token too — so
a split would have to be repeated for every token-bearing criterion, while one
ordering constraint covers all of them.

For completeness, acceptance 1's clauses **are** separable and the plan may use
that as a fallback if the orders conflict: its `[structure] skills/ directory not
found` clause is decidable the moment the derivation lands and depends on nothing
from -004; only its `GEOMETRY: nested` clause depends on -004. No such conflict
is expected — -004 is a print-site change with no dependency on the derivation,
so it can always be ordered first.

### CG-11. The implement stage writes the shared requirements corpus, and what that costs

**Two** stages write `docs/requirements/integration/packaging.md` in this cycle,
not one, and the specs stage writes it in neither: requirements are Approved and
closed to it.

**Implement stage — the appended dated notes.** Three, enumerated:

| Note | Beneath | Why |
|---|---|---|
| `[Updated: 2026-09-21c — …]` | REQ-PKG-CONSUMERGEOMETRY-002 | its consumer bullet cites -006 acceptances 3 and 5 as asserting "both directions"; they assert the negative direction only, and the positive is §CG-4's new acceptance 6 |
| `[Updated: 2026-09-21c — …]` | REQ-PKG-CONSUMERGEOMETRY-004 | §CG-6 re-reads two of its literals — `suite-rows-root=<path>` from "the suite root **as given**" to the **effective** root of §CG-3's three tiers, and "emitted by **every** run" as "iff the run prints an `OK:`/`FAIL:` summary", which excludes `--self-test`. Both re-readings are right and neither is expressible as "the requirement already said this" (S5) |
| the requirement-side halves paired with §CG-2's and §CG-9's corrections | REQ-PKG-CONSUMERGEOMETRY-003, -005 | already specified in those sections |

The -004 note exists because **§CG-4 establishes this cycle's own rule for
exactly this situation** — a spec that reinterprets an Approved literal appends a
dated note rather than leaving the literal standing — and applying that rule to
-002 while exempting -004 would reproduce, one requirement away, the defect this
delta diagnoses. No re-reading in this delta is left note-less.

**Verify stage — the REQ-PKG-PACKAGING-003 sha back-fill.** That requirement's
Approved `[Updated: 2026-09-21]` note (`packaging.md:474`) says its clause (ii)
"is retired from the close of the `consumer-geometry` implement stage — **whose
sha the verify stage back-fills into this note**". The literal written is that
close sha, replacing the future-event phrasing, in the same file. It is named
here because nothing else in this delta names, sizes or schedules it, and because
an exclusivity clause that did not know about it would read the back-fill as a
`SCOPE: VIOLATION` — which is the "criterion assigned to a stage with no task
behind it is uncollectable debt" hazard §CG-7 names four sections earlier.

Two consequences, stated concretely rather than as a caution.

**(a) The plan must size a requirements write scope, in two places.** Exactly one
**implement-stage** task owns `docs/requirements/integration/packaging.md` and is
the only implement task with that path in scope; the **verify-stage** back-fill
is the one other write and carries a task of its own, in the same file and no
other. Under the harness's write-scope observation an unexpected touch of that
path from any **other** chunk is a `SCOPE: VIOLATION`, so both scopes are
declared where they belong rather than discovered at a gate. Both tasks' content
is appended or in-place dated notes — never a rewrite of an approved sentence,
which is why every correction in this delta is specified as a note.

**(b) The edit bumps the requirements corpus's `last_updated`, which can make
these specs and the plan read as stale mid-cycle.** The staleness rule walks
`docs/requirements/index.md` → specs → plan, and these five specs and this
workstream's plan all carry dates at or before that edit. **Expected handling,
decided here: the requirements note lands in the same commit as the spec and plan
touches it is paired with**, so no intermediate commit exists in which the
corpus is newer than the artifacts that trace it. Where a pairing is impossible —
the note lands alone — the stage that lands it re-dates the affected specs'
`last_updated` in that same commit, which is a date bump and not a content
change. A `[stale-chain]` finding raised between those two events is an artefact
of the split, not a real staleness, and the drift sweep classifies `[stale-chain]`
as **informational and not routed at DONE**, so it blocks no gate either way —
that is why same-commit pairing is a discipline here and not a gate assertion.

**Not in scope of this decision**: `docs/requirements/index.md` itself. Nothing in
this delta edits it, so the requirements-corpus staleness reference the rule
actually keys on moves only if the implement stage chooses to record the delta
there, which no section here requires.


**The other paths the implement stage writes, and who regenerates the aggregate
(added at the specs cap gate, 2026-09-21).** §CG-11 above scopes one path
precisely and left the rest unenumerated, which is a `SCOPE: VIOLATION` hazard
of the same kind it was written to prevent. REQ-PKG-CONSUMERGEOMETRY-005's
corrections reach **other workstreams' owned artifacts** —
`docs/ws/marketplace/traceability.md`, `docs/ws/marketplace/verification.md`,
`docs/ws/packaging/verification.md`, `docs/ws/packaging/baseline.md`,
`docs/ws/packaging/plan.md` — plus the shared aggregate
`docs/requirements/traceability.md` and the shipped
`plugins/sdd/skills/orchestrate/references/drift-sweep.md`. Two rules, decided
here because the plan stage must size them:

1. **Cross-workstream writes are authorised for this cycle, by disposition class
   only.** Under the v4 layout a workstream owns only its own
   `kickoff`/`plan`/`plan-history`/`verification`/`traceability`, so these are
   departures and must be declared in the owning task's write scope rather than
   discovered at a gate. They are permitted **only** in the shape §The three
   disposition classes fixes: class (B) prose records take an appended dated
   note, never a rewrite; class (C) traceability rows are corrected in place as
   data. A cross-workstream write of any other shape is a violation, not a
   judgement call.
2. **No leaf regenerates the aggregate.** `docs/requirements/traceability.md` is
   regenerated wholesale from the per-workstream files by the **orchestrator**,
   as post-gate bookkeeping — the rule
   `docs/ws/consumer-geometry/traceability.md`'s own preamble states ("never
   hand-edited, and never by a leaf"). REQ-PKG-CONSUMERGEOMETRY-005 acceptance
   4's regenerate-and-diff is therefore split: the leaf corrects the
   **per-workstream source** row and asserts the aggregate's current row by
   **reading** it; the orchestrator regenerates at the gate and the diff is
   evaluated there. A leaf that regenerates is a violation even when its output
   is correct, because the aggregate's numbering moves and every other stage
   reads it.

### Consumer-Geometry Acceptance Criteria

- [ ] **The requirements-corpus writes are scoped, enumerated and dated.**
  Exactly **one implement-stage** task declares
  `docs/requirements/integration/packaging.md` in its write scope, and exactly
  **one verify-stage** task declares it for REQ-PKG-PACKAGING-003's sha
  back-fill; no other task in either stage does. The implement task lands all
  **three** notes §CG-11 enumerates — beneath REQ-PKG-CONSUMERGEOMETRY-002, -004,
  and the -003/-005 halves — asserted by grepping the file for a
  `[Updated: 2026-09-21c` note under each of the named ids, so a note omitted is
  red rather than silently absent. The commit carrying them also carries the
  spec/plan touches they pair with, or re-dates the affected specs'
  `last_updated` in that same commit. Asserted by reading the plan's scope table
  and `git show --name-only` over the note-bearing commit. A third task touching
  that path, a missing -004 note, or a commit that lands a note with neither
  pairing nor re-dating, makes this red (§CG-11; no upstream acceptance — this is
  a specs-stage consequence of §CG-4, §CG-2, §CG-6 and §CG-9).
- [ ] **The enumerated set is covered and demonstrated.** For each of the eight
  rows of REQ-PKG-CONSUMERGEOMETRY-001's table there is a registered case whose
  failure string begins with that row's `cg-row-<n>:` token (rows 1-3, 5-8 in
  `skill-lint.py --self-test`, row 4 in `gc.py --self-test`); the tool's named
  token constant and the set of registered `cg-row-` cases are asserted equal at
  run time; and for **each** row the mutation in its right-hand column is
  **applied and run** on a temporary copy of the tool, the printed
  `SELF-TEST FAIL:` list asserted to contain a line beginning with that row's own
  token, the mutation then reverted and the run observed to exit 0 with no such
  line. A described-but-unrun mutation fails this; so does one whose mutation
  turns the process red without its own token appearing
  (REQ-PKG-CONSUMERGEOMETRY-001 acceptances 1, 2).
- [ ] **The desk-check half of the count equality is collected.** At the verify
  stage, the `cg-row-<n>:` tokens parsed from REQ-PKG-CONSUMERGEOMETRY-001's
  enumeration table are compared **as a set** against the tokens
  `skill-lint.py --self-test` and `gc.py --self-test` print, and the comparison
  — both sets, and their difference — is recorded in
  `docs/ws/consumer-geometry/verification.md`. Adding a row to the table without
  adding its token to the tool makes the difference non-empty; adding a token
  without a row fails it symmetrically. The reconciler is the **verify stage**
  rather than a gate because `docs/` is outside the shipped plugin, so no shipped
  tool may read that table (§CG-7), and it carries a plan task of its own — a
  criterion assigned to a stage with no task behind it is uncollectable debt.
  **This is the half the in-tool assertion cannot reach**: the tool's own
  constant-vs-registered check proves the constant and the cases agree with each
  other, not that either agrees with the requirement
  (REQ-PKG-CONSUMERGEOMETRY-001 acceptance 3, desk-check half).
- [ ] **Both tools' gates stay green and stay hooks.** `python3
  plugins/sdd/tools/skill-lint.py --self-test` and `python3
  plugins/sdd/tools/gc.py --self-test` exit 0 after every edit made under the
  permission, and both remain in the committed `.pre-commit-config.yaml` hook
  set, asserted by parsing that file rather than by recollection
  (REQ-PKG-CONSUMERGEOMETRY-001 acceptance 4).
- [ ] **The per-geometry split holds.** In a two-root fixture whose suite root is
  given explicitly and lies under the corpus root, `len(skill_files()) > 0` and
  `suite_contained()` is `True`; in the same fixture with the suite root left to
  a **far** scratch default, `len(skill_files()) == 0` — ignoring the passed
  value makes the two halves equal and this red. **The fixture's suite
  subdirectory must not be named `plugins/sdd`** (§CG-5a); §7 fixture A's tree,
  which is, cannot be reused here. In §7 fixture B's disjoint
  consumer shape, `swept_roots()` equals exactly `{corpus_root}` and the suite
  root contributes zero walked files — implementing Option B makes this red,
  which is how the rejection is enforced rather than recorded. C12.1 passes
  unmodified, pinning the **16** rows it pins (`VERSION_GATED_SKILLS` 9 +
  `V4_CONTRACT_SKILLS` 7) and deliberately not 56
  (REQ-PKG-CONSUMERGEOMETRY-002 acceptances 1-3).
- [ ] **The surface exists, is discoverable, and reaches the binding.** `python3
  plugins/sdd/tools/skill-lint.py --help` names the suite-root surface —
  removing it from the parser makes this red, and this deliberately inverts
  REQ-PKG-PACKAGING-003's negative-surface grep. In a scratch fixture, invoking
  with an explicit suite root under the corpus root yields
  `suite_contained() == True` and a non-empty `skill_files()`, while invoking the
  same corpus without it yields the tier-2-or-3 root of §CG-3 — accepting the
  argument and discarding it makes the two runs identical and this red
  (REQ-PKG-CONSUMERGEOMETRY-003 acceptances 1, 2).
- [ ] **`gc.py` passes it through on both branches.** Branch (i): the vector
  `lint_command()` returns carries the suite root, asserted on the vector.
  Branch (ii): the `-c` shim passes the same suite root to its
  `Linter(...)` constructor, asserted by running the shim against a fixture and
  reading back `suite_contained()`. Reverting branch (i) is
  REQ-PKG-CONSUMERGEOMETRY-001 row 4 and is demonstrated; fixing only branch (i)
  leaves the branch-(ii) half red (REQ-PKG-CONSUMERGEOMETRY-003 acceptance 3).
- [ ] **Both absence sentences in this file are corrected, and the surviving
  clauses survive.** Stated in the two-part shape
  `marketplace-packaging.md` §The shape every string criterion in this delta
  takes defines. **Primary, by named sentence**: neither §2's *"`--suite-root` is
  **deferred**, not adopted — it mitigates the one unclosed vendored-cache case"*
  nor §Acceptance Criteria's *"the argparse surface exposes no `--suite-root`"*
  still asserts the surface's absence. Both are present and uncorrected today,
  which is what makes this red before the change. **Secondary, residual grep**:
  `docs/spec/two-root-linter.md` contains no other sentence asserting the
  **absence** of a `--suite-root` surface, outside a fenced code block and outside
  this §Consumer-Geometry Amendment — which quotes both sentences, in prose and in
  §CG-9's table, **in order to retire them**, and a table cell cannot be fenced.
  Every occurrence inside this amendment must be such a citation, never a fresh
  assertion of absence. The exemption is the same shape
  REQ-PKG-CONSUMERGEOMETRY-005 grants this cycle's own kickoff — **and** its `no-suite-rules` grep clause and its
  `suite_rules=False` containment clause are both still present. Landing the
  surface and leaving either absence sentence standing makes the first half red;
  deleting the checklist item wholesale makes the second half red. The two halves
  fail in opposite directions, which is what stops an implementer resolving this
  with a delete (REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4).
- [ ] **The suffix is present iff nothing was swept, on all three sites.** Two
  scratch runs, one over a one-file corpus and one over an empty corpus: the
  string `— NOTHING SWEPT` appears in the second summary line and not in the
  first — dropping the suffix makes the two lines identical and this red, and the
  mutation is run, not described. A scratch run over a corpus sweeping **zero**
  skill files that nonetheless raises at least one `fail`-severity finding prints
  `FAIL: … — NOTHING SWEPT`; patching only `:1189` and `:1191` makes this red.
  The warn variant `:1189` over a non-empty corpus with a warning prints **no**
  suffix; making the suffix unconditional on any of the three sites makes this
  red (REQ-PKG-CONSUMERGEOMETRY-004 acceptances 1, 4, 5).
- [ ] **The enum is rendered, correct, and unconditional.** The far-root fixture
  prints `GEOMETRY: disjoint`, the nested fixture `GEOMETRY: nested`, the
  equal-roots fixture `GEOMETRY: equal` — collapsing the derivation to a constant
  makes at least two of the three red. In the far-root fixture
  `suite-rows-root=` renders the **effective** suite root — there, the one passed
  at tier 1 — and not the corpus root; in §CG-4's fixture D it renders the tier-2
  derived `F/plugins/sdd` and not `default_suite_root()`. Rendering the corpus
  root in either, or `default_suite_root()` in the tier-2 case, makes this red. A fixture whose run has findings still carries its
  `GEOMETRY:` line, and a `--self-test` run — which prints no summary — carries
  none; emitting the token only on the clean path, or emitting it from a run with
  no summary, makes that red
  (REQ-PKG-CONSUMERGEOMETRY-004 acceptances 2, 3, negative).
- [ ] **The token survives the sweep.** In §CG-8's disjoint scratch
  construction, `gc.py --report` output contains a line beginning `GEOMETRY: `,
  forwarded verbatim on its own line; it contains none today, and removing the
  forwarding returns it to none. **`gc.py` derives no geometry of its own**, and
  because "geometry-deriving expression" has no grep spelling the claim is
  asserted as **two halves, both required** — the twin of `drift-sweep.md`
  §4's statement, which this says the same way rather than a second way:
  **(a)** `grep -nE '\bsuite_contained\b|\b(nested|equal|disjoint)\b'
  plugins/sdd/tools/gc.py`, ignoring comment lines, returns matches **only** on
  lines that read a token back off the linter's own stdout — the enumerated
  permitted set being the row-4 `--self-test` assertions that compare
  `cg4_geometry(...)`'s return against `"GEOMETRY: nested"` /
  `"GEOMETRY: disjoint"` — and a match on any line computing a member from
  `Path` comparison, containment or root equality is red; **(b)** on a
  temporary copy of `gc.py` that derives the member inside the sweep and emits
  a second token, §CG-8's far `gc.py --report --root "$REPO"` carries a
  **duplicate** `GEOMETRY:` line where the unmutated control carries exactly
  one. Either half alone is weak — the grep because a rename satisfies it, the
  mutation because it leaves the prose undecidable
  (REQ-PKG-CONSUMERGEOMETRY-004 forwarding clause).
- [ ] **The summary-line pins are confirmed unanchored** — no count written; the
  set is the `OK: N file(s) clean` pins derived by grep. The three
  `OK: N file(s) clean` pins in `docs/spec/skill-lint-v5.md` (`:127`, `:427`,
  `:452` before that file's amendment; `:129`, `:429`, `:454` after it — the
  content, not the number, identifies them) and
  `docs/requirements/integration/skill-lint.md:276` are each read at
  implement time and confirmed to state a prefix or substring match rather than
  an end-anchored one; any that is end-anchored is amended under
  REQ-PKG-CONSUMERGEOMETRY-004. The check is recorded as an observation with its
  command, not asserted (REQ-PKG-CONSUMERGEOMETRY-004 interaction note, extended
  here from two named sites to three).
- [ ] **The disjoint invocation is repaired end to end.** In §CG-8's
  construction the far `skill-lint.py` prints `GEOMETRY: nested` and raises no
  `[structure] skills/ directory not found` finding — **it prints that finding
  and `FAIL: 1 finding(s)` today**, so the assertion is red before the change and
  green after, and reverting the derivation returns it to red. In the same
  construction the far `gc.py --report --root "$REPO"` raises **no** `[structure]`
  finding where it raises exactly one today, asserted on the finding set (which
  is decidable under both landing orders) rather than on the token. Reverting
  `lint_command()` makes the finding reappear
  (REQ-PKG-CONSUMERGEOMETRY-006 acceptances 1, 2; §CG-10's ordering constraint
  makes the token clause of acceptance 1 decidable).
- [ ] **Every construction path resolves the same tiers.** Asserted on the path
  no other criterion in these five files reaches: `gc.py`'s branch-(ii) `-c`
  shim, run in fixture mode over a scratch corpus holding `plugins/sdd/skills/`
  and with **no** explicit suite root passed, yields `suite_contained() == True`
  and a non-empty `skill_files()` — the same answer the CLI gives on the same
  corpus, asserted by comparing the two. Implementing tier 2 in `main()` instead
  of `Linter.__init__` leaves the shim on tier 3, so `suite_contained()` is
  `False` and the two paths disagree, which is how this fails; it is also red
  today, since tier 2 does not exist on any path
  (REQ-PKG-CONSUMERGEOMETRY-006 acceptances 1 and 3, via §CG-3's
  constructor-resolution pin; no upstream acceptance covers the shim's geometry
  under an omitted suite root, which is why the pin is stated here).
- [ ] **The foreign consumer is untouched, in both negative directions.** In a
  scratch corpus with its own `skills/` and **no** `plugins/sdd/`, the derivation
  does not fire: no suite root is adopted at tier 2, `swept_roots()` equals
  exactly `{corpus_root}`, the token reads `disjoint`, their own `skills/` is
  still walked and no `— NOTHING SWEPT` suffix appears. With `plugins/sdd/`
  present but holding no `skills/` directory the candidate is **not** adopted and
  the run reports `disjoint` rather than naming an empty suite root. Making the
  derivation unconditional — for instance by falling back to the tool's own
  location — fires it in the first case and makes it red; dropping the `skills/`
  existence test makes the second red
  (REQ-PKG-CONSUMERGEOMETRY-006 acceptances 3, 5).
- [ ] **The positive direction fires, and is observable four ways.** §CG-4's
  fixture D: with corpus root `F` holding both `F/skills/**` and
  `F/plugins/sdd/skills/**`, and no explicit suite root, `suite_contained()` is
  `True`, the token reads `GEOMETRY: nested` with `swept-roots=2`,
  `suite-rows-root=` renders `F/plugins/sdd`, and the violation seeded under
  `F/plugins/sdd/skills/**` is reported with its path rendered `skills/…`
  relative to the suite root, asserted **by name on the seeded path**. Red today,
  because no derivation exists and the suite root falls outside `F`; returned to
  red after the change by dropping tier 2, by keying tier 2 on the tool's own
  location, or by rendering the suite seed against the corpus root
  (REQ-PKG-CONSUMERGEOMETRY-006 acceptance 6, added by this spec).
- [ ] **The nested case is not regressed.** In-repo `python3
  plugins/sdd/tools/skill-lint.py .` still reports `GEOMETRY: nested` and the
  same swept-file count it reports today, both derived at run time rather than
  pinned as literals. A derivation that re-roots or double-counts the already
  contained case makes this red — a live risk, since the in-repo copy's tier-2
  candidate and its `default_suite_root()` are the same directory, which is what
  §CG-3's third condition exists to decline
  (REQ-PKG-CONSUMERGEOMETRY-006 acceptance 4).
- [ ] **This file's three correction sites are landed**, as §CG-9's table
  specifies and under the requirement each names (REQ-PKG-CONSUMERGEOMETRY-003
  acceptance 4; REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2).
- [ ] **Machine-dependent observation, not gating.** On a machine with the plugin
  installed, running the cache's own `skill-lint.py` against this repository
  reports `GEOMETRY: nested` after the change where it reports the `[structure]`
  finding today. Recorded at verify as an observation with its command, never as
  a gate assertion: it depends on an installed cache whose presence and version no
  gate can guarantee, and the cache is a read-only measurement surface
  (REQ-PKG-CONSUMERGEOMETRY-006 closing note).

### Consumer-Geometry Open Items

**Recorded at the specs cap gate (2026-09-21) as named plan inputs.** Raised at
review round 4, verified, and not repaired because the stage's fix-loop cap was
reached. They are inputs the plan stage must size, not gaps:

- **A decidable comparand for "`gc.py` derives no geometry of its own"**
  (`drift-sweep.md` §4's criterion and its twin here). "Geometry-deriving
  expression" has no grep spelling — the same objection this delta raises against
  "the working tree" in the freeze item. Restate it as a decidable comparand: a
  grep for the enum literals `nested`/`equal`/`disjoint` and for `suite_contained`
  in `gc.py` returning zero outside the forwarding pass-through, or a mutation
  (compute the token in `gc.py`, assert a duplicate `GEOMETRY:` line).
- **All three `skill-lint-v5.md` summary-line pins name the dead
  `python3 tools/sdd-skill-lint.py` path, not one.** Measured: `:128`, `:428`,
  `:453-454`. The stated reason for repairing only the `:454` pin — that the
  implementer is already reading that line for the end-anchoring check — applies
  identically to the other two, which the same criterion also requires them to
  read. Either repair all three in that read, or restate the sentence so the
  omission is a recorded decision rather than an inaccuracy.
- **Three minor count/aggregation inconsistencies**: §CG-9 opens "**Two** edits
  … are owed" above a three-row table (its closing criterion correctly says
  three); the summary-line pins are counted three ways across two files (three in
  `skill-lint-v5.md`, four including the requirements-side twin); and the §CG-6
  acceptance box bundles four distinct assertions — enum rendering,
  `suite-rows-root=` under tier 1, under tier 2, and unconditional emission —
  into one checkbox, so a partial pass is invisible to the gate. The third is the
  one worth splitting; the plan can size it as separate boxes.

[Updated: 2026-09-21c — **all three open items above are closed by the
implement stage; the raised text is left standing as the record of what was
raised, and this note carries what was decided.**
(1) The decidable comparand is landed in this file's §Consumer-Geometry
Acceptance Criteria, in the two-half form (grep + mutation) its
`drift-sweep.md` §4 twin already carries, so the two files state one criterion.
(2) **All three** `skill-lint-v5.md` summary-line pins are repaired, which is
the first of the two options offered — the cheaper one, and the one that leaves
no recorded inaccuracy behind. The three `python3 tools/sdd-skill-lint.py`
invocations on those pin lines now read `python3
plugins/sdd/tools/skill-lint.py`, asserted by resolving the named path at run
time. Other `tools/sdd-skill-lint.py` occurrences elsewhere in that spec stay
out of scope, as `skill-lint-v5.md` §The summary-line pins states.
(3) Both counts are corrected to agree with their tables. §CG-9's opening
sentence now reads **three**, matching its three-row table and its closing
criterion. The summary-line pins are **three in `skill-lint-v5.md` and four
including the requirements-side twin** `docs/requirements/integration/skill-lint.md:276`
— one count, stated the same way in both places; the "two named sites" of
REQ-PKG-CONSUMERGEOMETRY-004's interaction note is a **measurement superseded by
a run-time grep**, recorded in that requirement's own `[Updated: 2026-09-21c]`
note rather than rewritten there. The third inconsistency — the §CG-6
four-assertion checkbox — was split by the plan into separate boxes and is
discharged there.]


- `OPEN:` **the 40 `REQUIRED` rows have no binding fixture in any geometry.**
  REQ-PKG-CONSUMERGEOMETRY-002 hands the narrower C-1 proposal — rebinding those
  40 rows alone to the swept-root union — to this stage as a separate argued
  proposal. §CG-5 **declines** it for this cycle, on the ground that the rebinding
  would land a behaviour change with no fixture able to falsify it. Supplying such
  a fixture is the closure, and it is not in this cycle's requirement set.
  Blocking constraint: a requirement authorising the fixture, owned by no artifact
  in this cycle.
- `OPEN:` **whether `--suite-root` should also be honoured from an environment
  variable.** Not adopted, and not proposed: §2's "no other root-resolution
  mechanism is introduced" stands, and §CG-3's three precedence tiers are
  exhaustive. Recorded only so that its absence reads as a decision rather than an
  omission, in the shape REQ-PKG-PACKAGING-003 used for the deferral this
  amendment supersedes.

## Consumer-Geometry Implementation Questions

Six observations were recorded provisionally, with **no id**, in Chunks 0–6 of
`docs/ws/consumer-geometry/plan.md` (that plan's §Conventions: a chunk that
declares no `docs/spec/**` path cannot define a `### Q-IMPL-…` heading, and an id
written before its heading exists raises a `fail`-severity `qimpl-undefined`
finding). Their durable entries are minted here, in the one chunk that holds this
file open, so that each id and its heading are born in the same commit.

### Q-IMPL-CONSUMERGEOMETRY-001: the `cg` helpers are mirrored in both tools, and nothing asserts the pair
**Tier**: 3 (implementation detail with a standing drift risk)
**Spec reference**: §CG-1. Where the derivation lives
**Decision**: **accept the duplication, and record it** rather than assert the
pair. `gc.py` cannot import `skill-lint.py` — it invokes it as a **subprocess**,
which is the forwarding relationship §CG-1 and §CG-8 both rest on — so
`disjoint_scratch_suite()` and `cg_reconcile()` exist once per tool rather than
once. The two copies are byte-equivalent in behaviour and nothing asserts they
stay so; if a later chunk edits one half, the drift is silent.
**Rationale**: the alternative — a shared module both tools import — would give
`gc.py` an import edge into the linter, which is precisely the coupling §CG-1
declines when it puts the derivation in `skill-lint.py` and leaves `gc.py`
forwarding. The helpers are **self-test scaffolding**, not production geometry:
a drift between them can make one tool's self-test weaker, never a corpus run
wrong. Recording the exposure is therefore proportionate to it. A later cycle
that wants the assertion can add a self-test case comparing the two function
bodies; it is not owed by this cycle's requirement set.

### Q-IMPL-CONSUMERGEOMETRY-002: "one token per summary" is structural only because `run()` is the sole emitter
**Tier**: 2 (spec ambiguity — the scope of "every run")
**Spec reference**: §Consumer-Geometry Acceptance Criteria
**Decision**: **keep every corpus summary inside `Linter.run()`**, and treat
that as the binding rather than pairing the two prints in a helper. The
`GEOMETRY:` token is emitted by `Linter.run()` alone, immediately before the
`OK:`/`FAIL:` summary that `run()` also prints, which is what makes "one token
per summary, never two, never one without the other" **structural** rather than
asserted.
**Rationale**: the property is real today and is what lets §CG-6 scope "every
run" to runs that print a summary — the rule follows the summary wherever it
goes, so no second statement can drift from it. The exposure is a **future**
summary printed outside `run()` (a `--print-population` corpus summary, say),
which would break the one-for-one pairing with no fixture to catch it. Binding
the pair in a helper now would add an indirection that no current caller needs
and would still not prevent a new caller printing its own summary. The cheaper
guard is the recorded rule: a summary line is `run()`'s to print. Whether
`--print-population` prints a summary at all is settled by Q-IMPL-PACKAGING-003,
not restated here.

### Q-IMPL-CONSUMERGEOMETRY-003: `print_population()` resolved tier 1 a second time
**Tier**: 3 (implementation detail, resolved within this cycle)
**Spec reference**: §CG-3. The corpus-root derivation and its precedence
**Decision**: **one resolution serves both paths** — `print_population()` builds
its `Linter` from `(corpus_root, suite_root_or_None)` and lets the constructor
resolve, exactly as the lint path does.
**Rationale**: raised in Chunk 2, when `print_population()` took a `suite_root`
positional and `main()` therefore decided tier 1 twice — once for
`print_population(root, …)` and once for `Linter(root, suite_root)` — with the
`--print-population` path passing `default_suite_root()` explicitly where the
lint path passed `None`. Once Chunk 3 landed tier 2 **in the constructor**, the
`--print-population` path would have been the only caller bypassing that
resolution, and would have reported a **tier-3** root where the lint path
reported **tier 2** — two answers to "which suite root" from one invocation,
which §CG-3's precedence exists to forbid. Chunk 2 did not act on it because
Chunk 3 owns the constructor; Chunk 3 landed the single resolution. Recorded
because the defect was real between the two chunks and the resolution is a
constraint on any future caller, not a one-off repair.

### Q-IMPL-CONSUMERGEOMETRY-004: a comparand table that quotes a source expression is a standing hazard
**Tier**: 2 (spec/requirement ambiguity)
**Spec reference**: §CG-7. The enumerated comparand set and its reporting surface
**Decision**: **name mutation sites by function, not by source expression**, in
any future extension of the enumerated comparand set; the existing rows are
**not** rewritten, and row 5's staleness is recorded in
REQ-PKG-CONSUMERGEOMETRY-001's own `[Updated: 2026-09-21c]` note rather than
edited into the approved table.
**Rationale**: REQ-PKG-CONSUMERGEOMETRY-001's enumeration names row 5's site by
a source expression, `print_population(root, default_suite_root())`, which
Q-IMPL-CONSUMERGEOMETRY-003's repair — landed by this cycle's own Chunk 3 — made
stale. The row's **mutation** survived the drift, so nothing was red; but an
enumeration keyed on source text is falsified by any refactor of that text, and
the next one may not survive. The requirement is Approved and its table is a
comparand set the acceptance criteria evaluate against, so rewriting a row would
make the record disagree with the commit that approved it — the rule §CG-11
states for this corpus. Naming sites by function is stable under refactor and
costs nothing at the point of writing.

### Q-IMPL-CONSUMERGEOMETRY-005: §CG-8's repair is attributable to tier 2, not to the pass-through
**Tier**: 2 (spec ambiguity — which change the criterion measures)
**Spec reference**: §CG-8. The disjoint scratch construction
**Decision**: the criterion is **decidable on the finding set under either
landing order and is left as written**; the attribution is recorded here.
`lint_command()`'s suite-root pass-through is **inert when no `--suite-root` is
supplied**, so §CG-8's construction is repaired by the linter's **tier-2
derivation**, not by the pass-through.
**Rationale**: measured, not reasoned. Under the landing order actually taken,
reverting the pass-through **alone** leaves the finding set empty; reverting the
tier-2 derivation in `Linter.__init__` (with the pass-through already reverted)
makes exactly one `[structure]` finding reappear. A reader of the criterion could
reasonably infer that the pass-through is what closes the construction, and it
is not. Note also that the forwarded `GEOMETRY:` line is still present in the
mutated run, reading `disjoint` — forwarding is independent of geometry, which
is the "forwards, never computes" property of
Q-IMPL-CONSUMERGEOMETRY-001's sibling criterion observed directly. The clause
itself needs no amendment: both landing orders satisfy it, and only the
attribution differs.

### Q-IMPL-CONSUMERGEOMETRY-006: one class (A) file keeps a string a bare per-file grep would forbid
**Tier**: 2 (requirement/spec/plan disagreement, closed by exemption)
**Spec reference**: §CG-9. The correction landing sites owned by this file
**Decision**: **the exemption is stated, in all three places**, rather than the
grep being widened or the prescribed text being altered.
`marketplace-packaging.md` keeps the literal `skills/orchestrate/tools/skill-lint.py`
inside Q-IMPL-MARKETPLACE-029's Decision, because
`marketplace-packaging.md` **prescribes that corrected text verbatim** and the
text retains the string; the same applies to the `-006` Evidence cell in
`docs/ws/marketplace/traceability.md`, whose replacement text that spec also
specifies verbatim including the string.
**Rationale**: read as a bare per-file `skills/orchestrate/tools` grep over
every class (A) file, REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2's *secondary*
half is unsatisfiable for this one file **against the spec's own prescription**
— a criterion that can be satisfied only by disobeying the spec that carries it.
The plan assigns no such grep to that file (it assigns the glob grep there and
the `skills/orchestrate/tools` grep to `pre-commit.md`), so no chunk was ever
red; but requirement, spec and plan each said something different about it,
which is the three-way split this delta exists to close. The closure is
symmetric with the third glob exemption `marketplace-packaging.md` already
carries: a **stated** exemption rather than an unexplained failure, with the
requirement-side half landed as an appended dated note under -005 and the
plan-side half recorded in Chunk 6's notes. §CG-4's rule for a spec
reinterpreting an Approved literal, applied once more.

## Pipeline-Observability Amendment (2026-09-22, REQ-LINT-PACKAGING-007 amended; REQ-LINT-PIPELINEOBSERVABILITY-001)

**Trigger.** The pipeline-observability delta adds fourteen `REQUIRED` rows and
one `FORBIDDEN` row to the linter (`skill-lint-v5.md` §`REQUIRED` Rows —
Pipeline-Observability, §`FORBIDDEN` Row — `literal-anchor`,
REQ-LINT-PIPELINEOBSERVABILITY-001). §6 pinned `REQUIRED=42 VERSION_GATED=9
V4_CONTRACT=7 FORBIDDEN=14` as a literal and its acceptance asserted the four
values "present and unchanged", so the pin fails on the landing of the very
rows it cannot know about; the specs closing review raised this as C2 and its
origin was fixed in the requirements at 27.4 (Q-REQ-PO-AL), the spec mirroring
it here (Q-SPEC-PO-U).

**Where the contract lives.** §6, edited in place under `[Updated:
2026-09-22]`: the numbers are stated as current-at-date, moved by any
row-adding cycle, and the criterion is the three-way equality —
`--print-population` == the code tables == §6's numbers — that
REQ-LINT-PACKAGING-007 as amended defines; the acceptance bullet under
§Acceptance Criteria carries the same equality and its three single-side
mutation cases. `skill-lint-v5.md` §Self-Test Extension states this cycle's
totals (`56` / `15`) as the delta's arithmetic and defers to §6 for the
comparand. No other section of this spec changes; Q-IMPL-PACKAGING-001 quotes
the pre-amendment §6 wording as history and is not rewritten. This section
states no contract of its own.

**Why.** A frozen literal is a fourth copy of a number already present in the
code tables, the flag's output and the self-test, and every row-adding cycle
had to chase it in each; the research-gate routing landing moved §6 and the
self-test but not the requirement, which is exactly the one-side-moved failure
the derived comparand now catches. Naming the surfaces that must agree, and
dating the numbers, keeps the population check — the one place a row count is
compared against a number — without making it fail on the contribution it
exists to police.
