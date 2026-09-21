---
domain: PKG
last_updated: 2026-09-21
status: Approved
research_refs: [RS-MARKETPLACE-001, RS-PACKAGING-002, RS-PACKAGING-003]
workstream: marketplace, packaging
---

# Requirements: Marketplace and Plugin Packaging

## Overview

This repository becomes a **Claude Code marketplace** named `sdd-commons`
carrying a single umbrella plugin named `sdd`, so that the ten SDD skills, the
two runnable tools and the three agents install with
`/plugin marketplace add jangid/sdd-commons` followed by
`/plugin install sdd@sdd-commons`. The **marketplace** cycle packaged this as a
manifest statement over the existing tree: under RS-MARKETPLACE-001 Q3 the
plugin entry set `"source": "./"` with an explicit component list, so what
shipped and what stayed behind were decided in two new JSON files and no
existing file moved — which is what kept that cycle's rename (NAME domain) from
touching the same references twice. The `packaging` workstream supersedes that
shape (¶3 below).

Two exclusions are packaging decisions rather than omissions, both settled by
RS-MARKETPLACE-001: `docs/` stays in the repository but is not a plugin
component (Q1 — it is this repository's own SDD corpus, never an input to any
skill's phase detection), and the three contributor tools stay out of the plugin
(Q2 — from an installed plugin they would root on the plugin's own copy and
report a false green about the user's repository).

Both exclusions are exclusions from the plugin's **component list** — the set
Claude Code loads as skills and agents. Under the marketplace cycle's
`"source": "./"` they were not also exclusions from what an install copies: the
installed plugin carried the whole repository tree, and the real-session install
of REQ-PKG-MARKETPLACE-010 measured `docs/` at 144 files and 48,462 lines, most
of the install's ~5 MB. REQ-PKG-PACKAGING-001 ends that — the shipped suite
moves to `plugins/sdd/` and the plugin entry's `source` names that subdirectory,
so `docs/` is outside the install entirely rather than copied-but-unloaded.

Standing constraints: the §Decided list in `docs/ws/marketplace/kickoff.md`
(marketplace `sdd-commons`, plugin `sdd`, components surfacing as
`sdd:orchestrate`) is inherited, not re-litigated. No requirement here changes
any phase skill's or the driver's behavioural contract — a packaging change that
alters what a skill does is a defect, not scope.

## Requirements

### Marketplace and plugin manifests

### REQ-PKG-MARKETPLACE-001: `.claude-plugin/marketplace.json` makes the repository a marketplace
The repository must carry `.claude-plugin/marketplace.json` declaring a
marketplace named `sdd-commons` with an `owner` and exactly one plugin entry.
The file must be valid JSON and must name the plugin `sdd`, so that
`/plugin marketplace add jangid/sdd-commons` followed by
`/plugin install sdd@sdd-commons` is the documented install path.
(see RS-MARKETPLACE-001 Q3)
**Acceptance**: `python3 -c "import json,sys;json.load(open('.claude-plugin/marketplace.json'))"`
exits 0; the parsed document's marketplace name equals the string `sdd-commons`
and its plugin list has exactly one entry whose `name` is `sdd`; both assertions
are made against the parsed file, not against a value copied into the test.
[Priority: must]

### REQ-PKG-MARKETPLACE-002: One umbrella plugin, `"source": "./"`, no `plugins/sdd/` subdirectory
The plugin entry must use `"source": "./"` with the plugin manifest at
`.claude-plugin/plugin.json` in the repository root, and the repository must
**not** grow a `plugins/sdd/` subdirectory. A single plugin is required because
the driver dispatches its sibling skills **by name**, not by path: a split that
places the driver and a phase skill in different plugins leaves a name that
resolves to nothing at dispatch time — a silent runtime failure no linter can
catch. `"source": "./"` is required over a subdirectory because it makes the
`docs/` and contributor-tool exclusions manifest statements and moves no
existing file, which is what makes the rename of the NAME domain a
single-touch edit. (see RS-MARKETPLACE-001 Q3 Recommendation)
**Acceptance**: the plugin entry's `source` value parsed from
`.claude-plugin/marketplace.json` equals `./`; `.claude-plugin/plugin.json`
exists, parses, and carries `name`, `description` and `version`; `test ! -d
plugins` succeeds.
[Updated: 2026-09-21 — the **no-`plugins/sdd/`-subdirectory** clause, the
`"source": "./"` value and the `test ! -d plugins` acceptance clause are
superseded by REQ-PKG-PACKAGING-001, which moves the shipped suite into
`plugins/sdd/` so that the suite root and the corpus root are distinct objects
(RS-PACKAGING-002 §Option (B), RS-PACKAGING-003 D1). The single-plugin leg — one
umbrella plugin, because the driver dispatches its sibling skills by name — is
**unchanged and still binding**; only the placement changes. The reason
originally given for `"source": "./"`, that it moves no existing file, was a
property of the marketplace cycle's single-touch rename and is not a standing
constraint. Authorising requirement: REQ-PKG-PACKAGING-001, workstream
`packaging`.]
[Priority: must]

### REQ-PKG-MARKETPLACE-003: Explicit component list — skills and agents enumerated, `docs/` absent
The plugin entry must carry an **explicit** component list naming each shipped
skill directory and each shipped agent file. The list must name every skill
directory present under `skills/` and every agent file required by
REQ-AGENT-MARKETPLACE-001, and must name **no path under `docs/`**. A "skill
directory present under `skills/`" means a directory under `skills/` that
contains a `SKILL.md`: the `tools/` subdirectory REQ-PKG-MARKETPLACE-006 bundles
inside the driver skill is part of that skill's own directory, not a skill
directory of its own, so it is neither listed separately nor counted as a missing
component. Enumeration
is required rather than a wildcard because the exclusions of
REQ-PKG-MARKETPLACE-005 and of `docs/` are expressed by absence from this list —
absence from what Claude Code **loads**, not from what the install copies.
(see RS-MARKETPLACE-001 Q1 Recommendation, Q3 Evidence)
**Acceptance**: a check derives both sides at run time — the set of skill
directory basenames listed in the manifest equals the set of directories under
`skills/` that contain a `SKILL.md` — a derivation that already excludes the
bundled `tools/` subdirectory, which contains none — and the set of agent paths listed equals
the set of `*.md` files directly under `agents/`; no listed path begins with
`docs/`. No count is written into the criterion.
[Priority: must]

### REQ-PKG-MARKETPLACE-004: `docs/` stays in the repository and is loaded as no plugin component
`docs/` must remain in the repository unchanged — it is the corpus this
repository's own cycles read and `tools/sdd-gc.py` sweeps — and must be absent
from the plugin's component list. The system must not require `docs/` to be
present in an installed plugin: every `docs/…` citation inside a skill body is a
**bare relative path** that resolves against the operator's own project working
directory, which is where the installing user's own SDD corpus lives.
(see RS-MARKETPLACE-001 Q1 Evidence)

Absence from the component list means `docs/` is loaded as no component; it does
not mean `docs/` is withheld from the install. Under `"source": "./"` the
installed plugin contains a copy of `docs/` — 144 files, 48,462 lines as
measured by the REQ-PKG-MARKETPLACE-010 install — and that copy is inert,
because no component is loaded from it and every skill-body citation resolves
outside it. The acceptance criteria below are true of the manifest and of skill
bodies, which is what this requirement guarantees; they establish nothing about
the install's file inventory.
**Acceptance**: a run-time grep over `skills/` for `docs/` citations that are
absolute, home-rooted, or rooted on a plugin path variable returns zero matches;
the manifest component check of REQ-PKG-MARKETPLACE-003 shows no `docs/` path.
[Updated: 2026-09-21 — the "accepted, documented cost" of the install carrying
`docs/` (144 files, 48,462 lines) is **removed**, not accepted: under
REQ-PKG-PACKAGING-001 the suite moves to `plugins/sdd/` and `docs/` stays at the
corpus root, outside the install. What survives is what this requirement
guarantees — `docs/` loaded as no component, every `docs/…` citation in a skill
body a bare relative path. The acceptance above is evaluated on the pre-move
tree; after the move its `skills/` reads `plugins/sdd/skills/`. Authorising
requirement: REQ-PKG-PACKAGING-001, workstream `packaging`.]
[Priority: must]

### Tools

### REQ-PKG-MARKETPLACE-005: Contributor tools are loaded as no plugin component
The skill-lint, scope-check self-test and evaluation tools must stay in the
repository and must be absent from the plugin's component list — which, as
above, keeps them from being **loaded**; under REQ-PKG-PACKAGING-001's
`tools/**` rule they ship in the install, so the exclusion is from the list
only. They are
repository-maintenance tools: none is ever invoked from a skill body, the
linter's suite rules are keyed to this repository's own skill set, and its root
is its own script location — so from an installed plugin it would lint the
plugin's copy of itself and report a green that says nothing about the
installing user's repository. That is exactly the false-green hazard this
cycle's kickoff warns against. (see RS-MARKETPLACE-001 Q2 Recommendation item 3)
**Acceptance**: a run-time grep over `skills/` for an invocation (a `python3 ` or
`./` prefix) of any of the three contributor tools returns zero matches; none of
the three appears in the manifest's component list.
[Priority: must]

### REQ-PKG-MARKETPLACE-006: `tools/` stays at the repository root; the two runnable tools are duplicated into the driver skill
The tools directory must stay at the repository root, so that every existing
`tools/…` reference in `docs/` (a record of what a past cycle ran here) and every
prose reference keeps its spelling. The **two** tools a skill actually invokes —
the drift sweep and the telemetry tool — must additionally be present **inside
the driver skill's own directory**, in a `tools/` subdirectory of that skill, as
the documented skill-directory-relative bundling pattern. They must be
**duplicated, not symlinked**: a plugin install may be materialised from a git
archive, which does not reliably preserve symlinks, so a symlink is a silent
broken-install mode. (see RS-MARKETPLACE-001 Q2 Recommendation items 1-2)
**Acceptance**: for each of the two bundled tools, the copy under the driver
skill's `tools/` directory is byte-identical to the repository-root file
(`cmp` exits 0) and is a regular file, not a symlink (`test ! -L`); no tool is lost
from the repository-root `tools/` directory, compared by **identity rather than
by name**: `git log --follow` resolves each post-change `tools/*.py` file to its
pre-change history, and the count of `tools/*.py` files after the change is not
less than the count before, both derived at run time rather than from a literal
list. A name-set equality is explicitly **not** the check — REQ-NAME-MARKETPLACE-003
renames every tool, so a name comparison against git history would fail by
construction.
[Updated: 2026-09-21 — "the tools directory must stay at the **repository**
root" is superseded by REQ-PKG-PACKAGING-001: `tools/` moves with the rest of
the shipped suite to `plugins/sdd/tools/`, and the drift sweep and skill linter
are invoked from there by the commit gate (REQ-PC-PACKAGING-001) and by skill
bodies (REQ-PKG-PACKAGING-009). What survives unchanged is everything this
requirement was written to guarantee: the two invoked tools are **duplicated,
not symlinked** into the driver skill's own `tools/` subdirectory, and no tool
is lost from the suite's `tools/` directory, compared by identity rather than by
name. Authorising requirement: REQ-PKG-PACKAGING-001, workstream `packaging`.]
[Priority: must]

### REQ-PKG-MARKETPLACE-007: Skill-side tool invocations resolve their root explicitly
Every invocation of a bundled tool from a skill body must reach the **operator's
own repository** as its root, never the plugin's. The drift sweep must be
invoked with an explicit root argument naming the current directory. The
telemetry tool must continue to rely on its cwd-relative default file path and
must **not** be given a plugin-relative path, because the telemetry file is
written into and read from the operator's repository. Neither tool's source may
be edited to satisfy **this** requirement: the packaging step makes no
behavioural and no source change to either tool. The self-referential name
strings inside them — `prog=`, the usage block, user-facing hint strings — are
renamed earlier, in the rename step, under REQ-NAME-MARKETPLACE-003, and that
rename is the sole permitted source edit. (see RS-MARKETPLACE-001 Q2
Recommendation item 2)
**Acceptance**: every drift-sweep invocation found in `skills/` by a run-time
grep carries an explicit root argument; no telemetry invocation in `skills/`
passes a file path that begins with a skill or plugin directory; `git diff` over
the two tools' source files across the **packaging step** — measured from the
close of the rename chunk (REQ-NAME-MARKETPLACE-007) to the end of the cycle — is
empty, so no edit is made to either tool beyond REQ-NAME-MARKETPLACE-003's rename
of its self-referential name strings.
[Priority: must]

### REQ-PKG-MARKETPLACE-008: No skill body may depend on the plugin-root environment variable
Skill bodies must not resolve any path through the plugin-root environment
variable. Across the marketplaces installed on this machine every actual use of
that variable sits in a manifest field (hook or MCP server) or in a command
body, and none in a skill body; the documented pattern for a skill's bundled
files is skill-directory-relative. A skill that depends on it is relying on an
unattested expansion. (see RS-MARKETPLACE-001 Q2 §Is `${CLAUDE_PLUGIN_ROOT}`
available in skill body text?)
**Acceptance**: a run-time grep for the plugin-root variable name over
`skills/**/*.md` returns zero matches outside a fenced code block that is
explicitly documenting the variable's manifest-only scope.
[Priority: must]

### Accepted gaps and install verification

### REQ-PKG-MARKETPLACE-009: Dangling spec citations in skills are an accepted, documented gap
Skill bodies cite contract files under `docs/spec/` as reading references. Those
citations must **not** be rewritten for this cycle: the skill never opens them at
runtime, the linter already classifies an unresolvable one as warn severity
precisely so that a consumer repository is not assumed to have this
repository's layout, and rewriting them is a large edit across many files for no
runtime benefit. Instead, `CONTRIBUTING.md` must state that the contracts live in
the repository and not in the install, so a reader who follows a citation from an
installed skill knows where to find it. (see RS-MARKETPLACE-001 Q1
Recommendation)
**Acceptance**: `CONTRIBUTING.md` contains a paragraph stating that spec
citations inside skills resolve in the repository, not in an installed plugin;
the count of such citations in `skills/` is unchanged across the implementing
change, compared by running the same grep before and after rather than against a
pinned number.
[Priority: must]

### REQ-PKG-MARKETPLACE-010: A real install must load the skills and resolve their lazily-read references
Before the cycle closes, the pushed branch must be installed as a marketplace in
a session and the install must be observed to (a) list the plugin's skills under
their namespaced names, and (b) successfully read at least one of the driver's
lazily-read `references/*.md` files from the installed copy. The driver reads ten
such files on demand; that they resolve from an installed plugin is the one
packaging assumption RS-MARKETPLACE-001 could not observe directly, and it is
cheap to settle with an actual install. If the observation fails, the failure is a
replan trigger for this cycle, not a documented limitation.
(see RS-MARKETPLACE-001 §Open Questions)

**Install mechanism for an unmerged branch** — settled at the requirements stage
gate (2026-09-21) against the first-party documentation, because the cycle's
terminal state is an open PR and `/plugin marketplace add jangid/sdd-commons`
would install `main`, not this branch. Two documented mechanisms exist and either
satisfies this requirement; the operator picks one at the verify stage:

| Mechanism | Invocation | Source |
|---|---|---|
| local path | `/plugin marketplace add <absolute path to the worktree>` | Plugin Marketplaces guide, "Add from local paths" |
| branch-qualified git URL | `/plugin marketplace add https://github.com/jangid/sdd-commons.git#marketplace` — the `#` anchor takes a branch, tag or commit sha | Discover Plugins guide, "Add from other Git hosts" |

The GitHub `owner/repo` shorthand always resolves the default branch and is
therefore **not** a valid mechanism for this requirement before merge. The
replan trigger above fires only if the install itself fails once a mechanism has
been used — never merely because one mechanism was unavailable.

**Acceptance**: the verification report records the install command run, the
namespaced skill names the session listed, and the name of the reference file
read from the installed copy, each as an observation with its command — not as an
assertion.
[Priority: must]

### The `plugins/sdd/` root move and the two-root linter interface

_(added 2026-09-21, workstream `packaging`, RS-PACKAGING-003 over RS-PACKAGING-002)_

### REQ-PKG-PACKAGING-001: The shipped suite moves to `plugins/sdd/`
The files the plugin ships must move out of the repository root into a
`plugins/sdd/` subdirectory — the **suite root** — while the repository root
stays the **corpus root** that this repository's own SDD cycles are linted and
swept against. `.claude-plugin/plugin.json` moves with the suite;
`.claude-plugin/marketplace.json` stays at the repository root, because it
describes the marketplace rather than the plugin, and the plugin entry's
`source` must name the subdirectory rather than `./`. The move is what makes the
two roots distinct objects; every other requirement in this group is a
consequence of their being distinct. The costing is carried evidence and is not
re-measured here: 45 files move, 154 stay, 199 total (RS-PACKAGING-002 §The
costing, measured at `0f5ec26`). (see RS-PACKAGING-003 §Scope; RS-PACKAGING-002)

**Membership rule.** A file moves to `plugins/sdd/` if and only if it is a
plugin component, a file bundled inside one, or the plugin's own manifest —
concretely `skills/**`, `agents/**`, `tools/**` and
`.claude-plugin/plugin.json`; **everything else stays at the corpus root**,
including `.claude-plugin/marketplace.json`, `docs/**`, `CLAUDE.md`,
`.pre-commit-config.yaml`, `README.md`, `LICENSE` and `CONTRIBUTING.md`. The
"45 move, 154 stay" figure is carried costing, not the rule: the rule is what
decides membership, and the count is what it happened to produce at `0f5ec26`.
The only undecided names are the two in the OPEN below, which would be
**duplicated** into the suite rather than moved out of the corpus root.

OPEN (inherited from RS-PACKAGING-003 §Open Questions, not blocking): whether
`plugins/sdd/` carries its own `README`/`LICENSE` — 45 versus 47 installed
files. Either answer changes which root supplies those two names, not whether
they are policed, because REQ-LINT-PACKAGING-001 binds both to the union of the
two roots.
**Acceptance**: after the move `test -d plugins/sdd` and `test -f
plugins/sdd/.claude-plugin/plugin.json` succeed; `test -f
.claude-plugin/marketplace.json` succeeds and `test ! -e
plugins/sdd/.claude-plugin/marketplace.json`; the plugin entry's `source` value
parsed from `.claude-plugin/marketplace.json` resolves to the `plugins/sdd`
directory; every path in the plugin's component list resolves relative to the
suite root, checked by `test -e` per entry rather than against a written-out
list; and `git log --follow` resolves each moved file to its pre-move history,
so the move is recorded as a move and not as a delete plus an add.
**Membership is asserted per name, derived at run time**: for every path in the
plugin's component list, and for every file under `skills/`, `agents/` and
`tools/` and `.claude-plugin/plugin.json` enumerated by
`git ls-tree -r --name-only <pre-move sha>` at the move commit's **parent** —
never a walk of the post-move working tree, where those corpus-root directories
are gone, the enumeration is empty and the clause passes vacuously — the name
exists under `plugins/sdd/` and not at the corpus root; and for each of
`.claude-plugin/marketplace.json`, `docs/`, `CLAUDE.md`,
`.pre-commit-config.yaml`, `README.md`, `LICENSE` and `CONTRIBUTING.md` the
name exists at the corpus root — the two names of the OPEN below being the only
ones permitted to exist at both. No count is written into the criterion.
[Priority: must]

### REQ-PKG-PACKAGING-002: `tools/skill-lint.py` takes a suite root and a corpus root as constructor parameters
The linter must accept the two roots as **constructor parameters** — option (B)
of RS-PACKAGING-002: the corpus root keeps the positional argument's value and
the suite root defaults to the script's own plugin root. **The corpus root must
default to the invocation cwd, never to the script's location.** The linter
today defaults its positional root to the script's own parent-of-parent
(`tools/skill-lint.py:1308`); after the move that expression names
`plugins/sdd`, so a zero-argument run would take the suite as its corpus and
silently stop sweeping `docs/spec/`, `docs/requirements/` and the rest of the
corpus. The cwd default is what keeps the zero-argument invocation — the form
the commit gate uses (REQ-PC-PACKAGING-001) — sweeping the operator's
repository. This is not recoverable at run time: REQ-LINT-PACKAGING-005
deliberately gives up live zero-sweep detection, and an empty corpus sweep is
legitimate in a consumer repository, so nothing downstream can distinguish this
mis-rooting from a correct run. **The documented default must change with the
code**: the positional argument's help string (`tools/skill-lint.py:1301-1302`,
"repository root to lint (default: repo containing this script)") and the
`docs/spec/skill-lint-v5.md` sentences describing a consumer run via
`REPO_ROOT` (:322, :469, :566) must be restated for the cwd default and the two
roots — REQ-PKG-PACKAGING-005 touches those same spec lines on the F11 axis
only, so without this clause both would describe a default the code lacks.
The generic walk must
sweep the **set union** of the two roots resolved to absolute paths, admitting
`suite_root/skills/**` only when the suite root is contained in the corpus root,
with equality counting as containment and degenerating to today's single walk;
and each swept file's rendered relative path must be computed against the root
it was walked from, not against a single fixed root. No other root-resolution
mechanism may be introduced. (see RS-PACKAGING-003 D1, confidence high;
RS-PACKAGING-002 §Option (B))
**Acceptance**: the linter class can be constructed with a suite root and a
corpus root that differ, and with the two equal, without touching argparse; with
the two roots equal the set of swept paths is identical to the pre-change
single-root sweep over the same tree, compared as sets derived at run time;
under a nested pair each finding's rendered path is relative to the root that
file was walked from, asserted on a seeded file under each root; and, evaluated
**after the move**, running `python3 plugins/sdd/tools/skill-lint.py` with zero
arguments from the repository root sweeps a set that includes at least one
`docs/spec/` path, asserted by membership on the swept set derived at run time
rather than on the exit code; and a run-time grep of the shipped help text and
of `docs/spec/skill-lint-v5.md` returns no surviving claim that the root
defaults to the script's own repository.
[Priority: must]

### REQ-PKG-PACKAGING-003: No `--no-suite-rules` flag; `--suite-root` is deferred, not adopted
The linter must **not** grow a `--no-suite-rules` option. A disable switch on
the checks a contributor is most likely to find inconvenient is the
silent-disable class RS-PACKAGING-002 already rejected externalised rule data
for; `suite_rules=False` must remain what it is today — a constructor argument
used only by self-test fixtures, with no CLI surface. The `--suite-root` CLI
option is **deferred and is not a requirement of this cycle**: it rests on the
single unclosed case of a vendored or repository-local plugin cache, where the
containment default is wrong and no in-process construction can correct it, and
a mitigation for one residual case is not a closure. Deferring it is recorded
here so that its absence reads as a decision rather than an omission.
(see RS-PACKAGING-003 D1 §Why the constructor parameter is decided here)
**Acceptance** (evaluated **after** the move of REQ-PKG-PACKAGING-001, at
`plugins/sdd/tools/skill-lint.py`): a run-time grep of
`plugins/sdd/tools/skill-lint.py` for `no-suite-rules`
returns zero matches; the argparse surface parsed from the script exposes no
`--suite-root` option this cycle; every `suite_rules=False` construction site is
inside the self-test.
[Priority: must]

### REQ-PKG-PACKAGING-004: The suite-gated rows retarget to the suite root
The 56 suite-gated rows — `REQUIRED` 40, `VERSION_GATED_SKILLS` 9,
`V4_CONTRACT_SKILLS` 7 (population carried from RS-PACKAGING-002, not
re-measured) — must resolve their path keys against the **suite root**. In a
consumer's environment that root is the installed plugin cache, where the named
files exist, so the rows pass there; this flip from "fail loudly against the
consumer's tree" to "pass against the shipped plugin" is the **intended**
behaviour and must not be treated as a regression. The rows name this suite's
own files and were never portable style rules: resolved against a consumer's
tree they reported failures naming skills that consumer never wrote, which is
loud about the wrong tree. The change is a retarget, not a weakening.

"Carried, not re-measured" means the populations are not re-derived **as
evidence** — no requirement here re-counts the tables to establish what they
contain. It does not mean the numbers are never compared: they are compared
**once**, at exactly one place, by REQ-LINT-PACKAGING-007's `--print-population`
criterion, which asserts `REQUIRED=40 VERSION_GATED=9 V4_CONTRACT=7
FORBIDDEN=13` against counts the flag derives from the tables at run time. That
single comparison is a regression check on the retarget — it catches an
implementation that dropped or duplicated a row while moving the rows' root
binding — and it is sound because rule-table rows are static in-code data that
do not grow by ordinary contribution. It is not in tension with
REQ-LINT-PACKAGING-004, which bans pinning a **swept-file** count from a live
corpus; a rule-table row count is not a corpus walk.
(see RS-PACKAGING-003 D1, confidence high)
**Acceptance**: running the linter from a corpus root containing no `skills/`
directory and a suite root that does produces **no** finding from any of the
three suite-gated tables, while the ungated checks still report; and, evaluated
on the **pre-move** tree (pinned at `a1ab5ba`, where both roots are the
repository root and so carry `skills/` and `docs/` alike), the equal-roots
finding set is unchanged from the pre-change single-root run over that same
tree, compared as a set derived at run time.
[Priority: must]

### REQ-PKG-PACKAGING-005: The amended F11 target, with its two exceptions
What the linter asserts about a **consumer's** corpus must be stated as the
**ungated** set — `FORBIDDEN`'s 13 rows, frontmatter, links, size and drift
phrases — which keeps resolving against the corpus root and failing loudly
there; what the suite-gated rows assert is the integrity of the **installed
suite**. No downstream artifact may restate the pre-split F11 wording, under
which the suite rows carried consumer meaning. The enumeration carries exactly
two deliberate exceptions, which must be stated wherever it is stated:
(i) *ungated but suite-bound* — `check_retired_prefix()` has no `suite_rules`
guard and so runs in a consumer tree, yet polices this suite's own retired
filename prefix, a fact of this repository's rename history with no meaning
elsewhere (its bindings are REQ-LINT-PACKAGING-001); and (ii) *gated but
corpus-bound* — `TEMPLATE_PAIRS` is gated yet its `spec` side keys on
`docs/spec/**`, which stays on the corpus root (its binding is
REQ-LINT-PACKAGING-002). Outside those two, *ungated* and *consumer-facing*
coincide. (see RS-PACKAGING-003 D1 §Amended F11 target)

**The pre-split F11 wording, quoted so the grep has a target.** Its home is
`docs/spec/skill-lint-v5.md`, where it appears three times — as the
parenthetical "(the F11 principle)" at lines 322 and 566, as
"layout-independence (F11)" at line 494, and in full at lines 469-470:

```
warn, never fail — the linter must not assume this repo's layout
(existing audit F11 principle)
```

The superseded claim is the **unqualified scope** of that sentence: pre-split
it was stated of what the linter asserts as a whole, so every row read as
consumer-facing. Post-split it is true of the ungated set only, plus exception
(i); the suite-gated rows assert the integrity of the installed suite and do
assume this suite's layout, by intent. The sentence is not deleted from
`skill-lint-v5.md` — it is re-scoped there to the ungated set, with both
exceptions named alongside it. The baseline for this amendment sits in
RS-PACKAGING-001 (rejected at its stage gate; its two-root finding survives as
an input to RS-PACKAGING-002).
**Acceptance**: every place the F11 target is stated — the linter's own
docstring or rule-table comment, and any spec or skill text that restates it,
`docs/spec/skill-lint-v5.md` lines 322, 469-470, 494 and 566 included —
names the ungated set as the consumer-facing one and names both exceptions; a
run-time grep across `docs/spec/` at the corpus root and `plugins/sdd/skills/`
and `plugins/sdd/tools/` at the suite root (evaluated **after** the move of
REQ-PKG-PACKAGING-001) for the quoted sentence above **unaccompanied by** a
scoping clause naming the ungated set returns zero matches.
[Priority: must]

### REQ-PKG-PACKAGING-006: Fixture A — nested roots pin per-root path rendering
The self-test must carry a fixture in which `suite_root =
corpus_root/plugins/sdd` — the shape this repository has after the move — that
seeds a walk-class violation (a forbidden phrase or bad frontmatter) under
`suite_root/skills/**` and asserts the violation **is** reported with its path
rendered relative to the root it was walked from. This fixture pins per-root
path rendering, which is exactly what collapses when the two bindings are
conflated. It does **not** pin single-sweep and must not be written as though it
did: under nesting the two walk terms are disjoint subtrees, so no seeded file
is reachable from both. (see RS-PACKAGING-003 D4, confidence low)
**Acceptance**: the fixture's seeded violation appears in the findings list with
the expected relative path; swapping the fixture's expectation makes the
self-test fail.
[Priority: must]

### REQ-PKG-PACKAGING-007: Fixture B — disjoint roots pin the consumer shape
The self-test must carry a fixture in which the suite root lies **outside** the
corpus root — the consumer shape — asserting two things: a **table-row**
violation seeded under the suite root (from `REQUIRED`, `VERSION_GATED_SKILLS`
or `V4_CONTRACT_SKILLS`, which resolve `root / rel` directly and bypass the
walk) **is** reported; and a walk-class violation seeded under
`suite_root/skills/**` is **not** reported, asserted as a **named absent
finding for a specific seeded path** so that "correctly excluded" is
distinguishable from "switched off". No assertion in this fixture may rest on
exit-code silence. The membership assertion of REQ-LINT-PACKAGING-003 and the
fixture count of REQ-LINT-PACKAGING-006 belong here too, since together they
prove both roots were walked. (see RS-PACKAGING-003 D4)
**Acceptance**: the seeded table-row violation appears in the findings list; the
named seeded walk-class path appears in **no** finding while other findings are
present; swapping the two expectations makes the self-test fail.
[Priority: must]

### REQ-PKG-PACKAGING-008: Case C — equal roots is the only geometry that pins single-sweep
The self-test must carry a case in which `suite_root == corpus_root` — the
unmoved repository, and a consumer running against a non-vendored install — that
seeds one walk-class violation under `skills/**` and asserts it is reported
**exactly once**. This is the only geometry in which both walk terms name the
same subtree and a file is reachable from both, so it is the only one that can
distinguish a set union from a list concatenation; neither fixture A nor fixture
B may be described as pinning single-sweep. It needs no new fixture tree — it is
fixture A's corpus tree constructed with both roots equal.
(see RS-PACKAGING-003 D4, D3 assertion 1)
**Acceptance**: the seeded violation is counted exactly once in the findings
list; rebuilding the union as list concatenation over the two equal roots makes
this assertion fail.
[Priority: must]

### REQ-PKG-PACKAGING-009: `skills/verify/SKILL.md:169` invokes the drift sweep with a root the move keeps correct
The last cwd-relative drift-sweep invocation in a skill body — the
`python3 tools/gc.py --report --root .` line in the verify skill's gc criterion
— must be updated so that both its **script path** and its **root argument**
stay correct after the root move: the script path resolves to the tool inside
the suite, and the root argument still names the operator's own repository,
never the suite. This repair is carried unchanged from the marketplace cycle and
is **sequenced after** REQ-PKG-PACKAGING-002 and REQ-LINT-PACKAGING-001..002,
whose root bindings fix what the line describes; repairing it first would pin a
spelling the bindings then change. (see `docs/ws/packaging/kickoff.md` §Carried
repairs; RS-PACKAGING-003 §Recommended Next Step)
**Acceptance** (evaluated **after** the move of REQ-PKG-PACKAGING-001): a
run-time grep over `plugins/sdd/skills/` for a drift-sweep invocation
whose script path is bare `tools/gc.py` returns zero matches; every
drift-sweep invocation found in `plugins/sdd/skills/` carries an explicit root
argument naming the operator's working directory; the invocation in the verify
skill runs from a scratch consumer repository without resolving its root to the
suite.
[Priority: must]
