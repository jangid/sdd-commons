---
domain: PKG
last_updated: 2026-09-22
status: Approved
research_refs: [RS-MARKETPLACE-001, RS-PACKAGING-002, RS-PACKAGING-003, RS-CONSUMERGEOMETRY-001]
workstream: marketplace, packaging, consumer-geometry
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
[Updated: 2026-09-21b — the **duplication clause is superseded** by
REQ-PKG-CONSUMERGEOMETRY-005: the bundled copy under the driver skill's own
`tools/` subdirectory is **removed**, not maintained, because no invocation
reaches it that works. RS-CONSUMERGEOMETRY-001 Q5 measured the bundled
`gc.py` exiting on its linter-missing path in every geometry — the linter is
no longer bundled beside it, so `lint_path()`'s sibling-first candidate finds
nothing — and found the directory named by no other invocation. **This
requirement's acceptance was weaker than it read**: it asserted only that the
copy *exists on disk*, is byte-identical and is not a symlink; it never
asserted that invoking it works, and it does not. That gap is recorded here
rather than in a verification note, because it is the requirement text that
permitted it. What survives unchanged is the second half — no tool is lost
from the suite's `tools/` directory, compared by identity rather than by name —
and the duplicate-not-symlink rule, which stands as the rule that would govern
any *future* bundling. Authorising requirement: REQ-PKG-CONSUMERGEOMETRY-005,
workstream `consumer-geometry`.]
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
[Updated: 2026-09-21 — the third acceptance clause is **restated**, because as
written it is **un-re-runnable**, not because it was violated. Two corrections,
both from RS-CONSUMERGEOMETRY-001 Q2:

**(a) Scope — the freeze never covered the skill linter.** This requirement
names exactly two artefacts, the drift sweep and the telemetry tool
(`plugins/sdd/tools/gc.py` and `plugins/sdd/tools/telemetry.py`). It does not
name `plugins/sdd/tools/skill-lint.py`, in its body or its acceptance, and the
traceability row re-derives the freeze over those two files alone. The
`consumer-geometry` cycle's spine — every Class A/B/C repair and all three
`rel=` guard sites — lives in the linter. For that work the answer is not "the
freeze is step-scoped" but "there is no freeze to scope". For the two named
tools the freeze **is** step-scoped and its step has closed: the body's own
words are "to satisfy **this** requirement", the criterion is explicitly
bounded "across the **packaging step**", and `integration/naming.md` already
records an exception taken under that reading.

**(b) Comparand — restated against the post-move paths, with both endpoints
pinned.** The `marketplace` cycle re-derived the criterion as
`git diff 3ddfdb3 HEAD -- tools/gc.py tools/telemetry.py`. The packaging
cycle's own move deleted those paths, so that command evaluated at any sha
after the move reports the **move** (3982 deletions) and can neither confirm
nor deny the freeze. **This is not a regression against the `marketplace`
cycle** and must not be recorded as one: a criterion evaluated outside its own
window is not falsified by what it reports there. The restated criterion, with
`HEAD` replaced by the packaging cycle's end sha `0bdb076` and the comparand
made rename-proof by comparing content rather than paths:

```
git rev-parse 3ddfdb3:tools/gc.py            == git rev-parse 0bdb076:plugins/sdd/tools/gc.py
git rev-parse 3ddfdb3:tools/telemetry.py     == git rev-parse 0bdb076:plugins/sdd/tools/telemetry.py
```

Both equalities hold at the blobs `d800df5…` (`gc.py`) and `d696421…`
(`telemetry.py`). **How it fails**: any source edit to either tool inside the
window `3ddfdb3..0bdb076` changes that tool's blob sha and the equality is
false. The criterion is now re-runnable at any future HEAD and its verdict is
fixed, because both endpoints are shas rather than `HEAD`.

**Successor.** Tool-source edits made for consumer-geometry correctness are
permitted by REQ-PKG-CONSUMERGEOMETRY-001, workstream `consumer-geometry`,
which carries its own enumerated comparand set. This requirement's freeze does
not bind them.]
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
[Updated: 2026-09-21 — **two clauses, one standing and one superseded.**
(i) **The `--no-suite-rules` leg stands unchanged.** A disable switch on the
checks a contributor finds inconvenient is still rejected, `suite_rules=False`
is still constructor-only, and the acceptance's `no-suite-rules` grep still
returns zero matches.
(ii) **The `--suite-root` deferral is superseded** by
REQ-PKG-CONSUMERGEOMETRY-003: the surface is adopted, and this requirement's
acceptance clause "the argparse surface parsed from the script exposes no
`--suite-root` option this cycle" is **false once that requirement lands** —
deliberately, and the successor's acceptance 1 inverts this very grep as the
evidence of it. The deferral's stated ground ("it rests on the single unclosed
case of a vendored or repository-local plugin cache") was too narrow: the
disjoint geometry is the **only** geometry a consumer of the installed plugin
has, and the surface is what Option A depends on to reach the working tree at
all. The window is named rather than left implicit, because a criterion with an
implicit window is exactly what REQ-PKG-MARKETPLACE-007's `[Updated:]` note
corrects two requirements above: clause (ii) holds for the `packaging` cycle
and is retired from the close of the `consumer-geometry` implement stage —
whose sha the **verify stage back-fills into this note**, because an endpoint
named as a future event is the same implicit window this note exists to
correct, and only a literal sha makes the clause re-runnable the way
REQ-PKG-MARKETPLACE-007's restatement is (`0bdb076`).
Authorising requirement: REQ-PKG-CONSUMERGEOMETRY-003, workstream
`consumer-geometry`.]
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

### REQ-PKG-PACKAGING-010: The drift sweep resolves its linter sibling-first
The drift sweep must resolve the skill linter **sibling-first**: the copy beside
its own script file (`<gc.py dir>/skill-lint.py`) is tried first and takes
precedence; `<root>/tools/skill-lint.py`, resolved against the swept corpus
root, is the fallback; and when neither candidate is a file the sweep must keep
its existing `linter missing` behaviour — exit 2 with an `error: linter missing`
diagnostic — rather than silently skipping the structural sweeps.

This ordering is **load-bearing after the move**, not incidental. Under
REQ-PKG-PACKAGING-001 the sweep and the linter travel together into
`plugins/sdd/tools/`, so `<root>/tools/skill-lint.py` ceases to exist in this
repository and the sibling candidate becomes the **only** one that ever
resolves here. A root-first or root-only resolution would therefore break the
commit gate's own drift-sweep hook in this repository while a consumer tree
carrying a corpus-rooted linter kept working — a failure visible only here. The
move changes no tool source (REQ-PKG-MARKETPLACE-007), so this requirement
freezes behaviour that already exists rather than requesting a change.

**Source**: a behavioural contract of existing code, confirmed at
`tools/gc.py:501-502` (`lint_path()`), surfaced by the **specs-stage review of
this cycle**. It is **not** a finding of RS-PACKAGING-003 and rests on none of
its decisions. `docs/spec/marketplace-packaging.md` §Tools carries the prose.

**Acceptance** (evaluated **after** the move of REQ-PKG-PACKAGING-001) — three
assertions, each stated with the construction that makes it fail:
1. **Precedence.** With a distinguishable linter stub at **both** candidate
   locations (each printing its own marker), a sweep run invokes the sibling
   one, asserted on the marker observed. Reordering the candidate tuple in
   `lint_path()` makes the root marker appear and this assertion fail.
2. **Fallback.** With the sibling copy absent and only
   `<root>/tools/skill-lint.py` present, `lint_path()` resolves to the root
   candidate. Deleting the second tuple entry makes it return `None` and this
   assertion fail.
3. **Neither present.** With both absent, the run exits 2 and prints
   `error: linter missing` — unchanged from today. Making `lint_path()` return
   a path that does not exist makes the run fail elsewhere, not here, and this
   assertion fail.

**Reviewer-checkable residue**, stated rather than implied: (a) assertion 1
constructs both candidates artificially, so it does not show that the post-move
repository has exactly one — that is checked by REQ-PKG-PACKAGING-001's own
move criteria, not here; (b) nothing here pins the working directory the commit
gate's hook invokes the sweep from, which is REQ-PC-PACKAGING-001's binding;
(c) the `linter missing` diagnostic names only the corpus-root candidate in its
text — that wording is out of scope and deliberately left unchanged.
[Priority: must]

### The consumer (disjoint) geometry

These six requirements are the `consumer-geometry` delta, derived from
RS-CONSUMERGEOMETRY-001. Their subject is the geometry in which the suite root
is **disjoint** from the corpus root — the only geometry a consumer of the
installed plugin ever has, and the geometry in which
`swept_roots()`'s union collapses to the corpus root alone, so the suite is not
walked at all. The spike measured that all eight of the linter's checks are
affected, in three classes: one reduces loudly and returns (Class A), four pass
vacuously over an empty input set (Class B), and three run against the
installed plugin cache instead of the working tree (Class C). None of that is
re-derived here; it is cited.

Three geometries are named throughout and are the vocabulary these requirements
are written in:

| Name | corpus root | suite root | `suite_contained()` |
|---|---|---|---|
| **nested** | the repository | `plugins/sdd` under it | `True` |
| **observation** (this repository's operator, running an installed tool) | the repository | the plugin cache | `False` |
| **consumer** (a foreign repository with its own `skills/`) | that repository | the plugin cache | `False` |

### REQ-PKG-CONSUMERGEOMETRY-001: Tool source may be edited for consumer-geometry correctness, over an enumerated comparand set
Tool source under `plugins/sdd/tools/` **may** be edited when the edit is
required for correctness under the disjoint (consumer) geometry.
REQ-PKG-MARKETPLACE-007's freeze does not bind such an edit: for
`skill-lint.py` the freeze never covered the file at all, and for `gc.py` and
`telemetry.py` it is bounded to the packaging step, which has closed (see that
requirement's `[Updated: 2026-09-21]` note).

The permission is paired with the cycle's standing constraint — **every binding
this cycle touches must have its reversion fail a gate, demonstrated by running
the mutation, not asserted.** "Every such edit" is undecidable as a comparand,
so the set is **enumerated here**, in the table below, by
RS-CONSUMERGEOMETRY-001 Q2/Q4. The table is the comparand; the count "eight"
wherever it appears in this prose is **informational** and is never a literal a
criterion may be evaluated against (acceptance 3). A later cycle extends the set by **amending this
enumeration**, never by argument; an edit outside it is out of scope, not
silently admitted.

| # | Named site | Source | The mutation that must turn its case red |
|---|---|---|---|
| 1 | `check_retired_prefix()` under a **disjoint** suite root | Q4 gap (a) | rebind its scope walk to the corpus root only |
| 2 | `check_required()` under a **disjoint** suite root — all 56 gated rows | Q4 gap (b) | rebind the rows to the corpus root (the nested fixture C12.1 does not observe the disjoint case) |
| 3 | Class B non-vacuity — a zero-sweep run distinguishable from a clean one | Q4 gap (c) | drop the `— NOTHING SWEPT` suffix (REQ-PKG-CONSUMERGEOMETRY-004) |
| 4 | `gc.py`'s `lint_command()` root pinning **and** `lint_path()`'s second candidate | Q4 gap (d) | drop the suite-root pass-through; reorder the candidate tuple |
| 5 | `main()`'s `print_population(root, default_suite_root())` wiring **and** `retired_scope_entries()`'s `seen` set | Q4 gap (e) | mis-root the wiring to `(root, root)`; remove the deduplication |
| 6 | `check_retired_prefix()`'s `rel=Path(rel)` guard (`skill-lint.py:1166`, in the `self.flag(...)` call opening at `:1163`) | Q1 | delete the keyword argument — `rel()` then raises `ValueError` |
| 7 | `check_required()`'s `rel=Path(rel)` guards (three call sites, one row) | Q1 | delete the keyword arguments |
| 8 | `check_template_drift()`'s `rel=Path(TEMPLATE_SOURCE)` guard | Q1 | delete the keyword argument |

A **row** is the unit of the enumeration, not a call site: rows 4, 5 and 7
each cover more than one line of source and are each discharged by one
`--self-test` case. That granularity is stated so the count below is
unambiguous.

**The reporting surface these criteria rest on**, stated because they are
otherwise unobservable. `skill-lint.py`'s `--self-test` today accumulates every
failure into one `failures` list and prints it as `SELF-TEST FAIL:` followed by
one `- <string>` line per failure, returning `1` **once, for the process**; its
`SELF-TEST OK:` banner is a single hand-written prose sentence, not a
machine-readable case list. A case therefore does not exit — the process does.
So:

- Each of the eight rows is bound to a case whose failure string **begins with
  a stable row token** of the form `cg-row-<n>:`, contributed to that same
  `failures` list. The **failure-string list is the per-case surface**, and
  every assertion below is stated against it rather than against the banner or
  the process exit code.
- The eight row tokens are additionally carried in **one named constant inside
  the tool**, and `--self-test` asserts that every member of that constant is
  registered and run. That constant, not this table, is what the tool can
  reach: `docs/` is outside the shipped plugin, so no shipped tool may read
  this file — which is why the reconciliation in assertion 3 is a desk check
  with a named owner and not a tool assertion.

**What exercising this permission falsifies — one Approved spec criterion,
named here rather than left to a later reader.**
`docs/spec/marketplace-packaging.md:366` asserts REQ-PKG-MARKETPLACE-007's
source freeze **against the working tree**, by content identity
(`git show <sha>:tools/<tool> | cmp - plugins/sdd/tools/<tool>`), with the
accepted alternative `git diff -M <sha> HEAD -- tools/ plugins/sdd/tools/`.
**Both spellings leave the right endpoint unpinned.** Row 4 of the enumeration
above and REQ-PKG-CONSUMERGEOMETRY-005's `AGG_FIX` correction each edit
`plugins/sdd/tools/gc.py`, so that item turns red at the next gate — not
because the freeze was violated, but because it is evaluated outside its own
window. This is exactly the defect REQ-PKG-MARKETPLACE-007's `[Updated:]` note
corrects on the requirement side; leaving its spec-side twin unpinned would
reproduce it one artifact away. The item must be repinned to the packaging
cycle's end sha `0bdb076` — `git show 3ddfdb3:tools/<tool> | cmp - <(git show
0bdb076:plugins/sdd/tools/<tool>)`, or equivalently the blob-sha equality the
requirement states — so its verdict is fixed rather than drifting with `HEAD`.
Correcting it is in scope for the implement stage under this requirement, not a
follow-up.

**Acceptance** — five assertions, each with the construction that makes it
fail:
1. **Coverage.** For each of the eight rows there is a registered case whose
   failure string begins with that row's `cg-row-<n>:` token — in
   `skill-lint.py --self-test` for rows 1-3 and 5-8, in `gc.py --self-test` for
   row 4. A row with no registered token fails the tool's own
   constant-vs-registered assertion, which turns `--self-test` red.
2. **Demonstration, not assertion — and attributable to the new case.** For
   each row, the mutation in its right-hand column is **applied and run** on a
   temporary copy of the tool, and the assertion is that the printed
   `SELF-TEST FAIL:` list **contains a line beginning with that row's own
   `cg-row-<n>:` token**; the mutation is then reverted and the run observed to
   exit 0 with no such line. Membership, not the process exit code, is the
   comparand, and deliberately so: row 2's mutation — rebinding the 56 gated
   rows to the corpus root — **also** trips the pre-existing C12.1 fixture, so a
   green-to-red transition of the process would not show that the new disjoint
   case fired at all. A row whose mutation is described but not run fails this;
   so does one whose mutation turns the process red without its own token
   appearing.
3. **Count equality, with a named reconciler.** Two halves. **In the tool**:
   `--self-test` asserts that the named constant's membership and the set of
   registered `cg-row-` cases are equal, both derived at run time, so a case
   without a token or a token without a case turns it red. **At the verify
   stage, as a desk check**: the row tokens parsed from the table above are
   compared as a set against the tokens `--self-test` prints, and the
   comparison is recorded in this workstream's `verification.md`. The
   reconciler is named as the **verify stage** rather than a gate because no
   shipped tool may read `docs/` (see the surface note above), and its write
   scope is that verification report. Adding a row here without adding its
   token to the tool fails the desk check; adding a token without a row fails
   it symmetrically.
4. **The tools' own gates stay green.** `python3
   plugins/sdd/tools/skill-lint.py --self-test` and `python3
   plugins/sdd/tools/gc.py --self-test` both exit 0 after every edit made under
   this permission, and both remain in the committed `.pre-commit-config.yaml`
   hook set (they are hooks, not among the three checks run explicitly).
5. **The spec-side freeze criterion is repinned.** Asserted **on the named
   item** — `docs/spec/marketplace-packaging.md:366`, the
   REQ-PKG-MARKETPLACE-007 checklist item — and not as a file-wide grep: that
   item's comparand names `0bdb076` as its right endpoint, in place of the
   working tree / `HEAD` it names today. A file-wide grep is the wrong shape
   here, because `HEAD` occurs in that file in unrelated contexts and "the
   working tree" has no grep spelling at all. Editing `gc.py` under this permission and
   leaving that item unpinned makes the next gate red, which is how this
   assertion fails if it is skipped.
(see RS-CONSUMERGEOMETRY-001 Q2, Q4)
[Priority: must]

### REQ-PKG-CONSUMERGEOMETRY-002: The repair is a per-geometry split, not one fix
The disjoint geometry gets **two different answers**, because the operator's
own repository and a foreign consumer's are not the same problem.

- **Observation geometry (this repository, installed tool): Option A.** The
  invocation passes an **explicit suite root** naming the corpus's own
  `plugins/sdd`. **Which** invocation is not left to the specs stage:
  REQ-PKG-CONSUMERGEOMETRY-006 binds it to a committed one, because a surface
  that exists and is never used leaves this cycle's founding observation
  entirely unrepaired. That makes `suite_contained()` true and restores the nested
  geometry: the walk reaches the working tree's files, and all three Class C
  checks re-root onto the working tree instead of the plugin cache. Option A
  discharges Class C **for this geometry only**, as a side effect of
  re-rooting, with no rebinding of the 56 suite-gated rows.
- **Consumer geometry (a foreign repository): today's union, unchanged.** The
  consumer's corpus root holds their own `skills/`, which today's union already
  walks correctly. An explicit suite root pointed at their tree would name a
  plugin that is not there — **unless their tree happens to hold a
  `plugins/sdd/skills/` of its own**, as a fork of this repository or an
  identically laid out marketplace does, in which case
  REQ-PKG-CONSUMERGEOMETRY-006's derivation fires and re-roots them onto that
  copy. That is the one class for which "today's union, unchanged" does **not**
  hold, it is intended (the adopted root is a plugin really present in the tree
  being linted), and -006 acceptances 3 and 5 assert both directions of it. The
  exception is stated here because this bullet is the sentence a specs reader
  will quote as the rule, and a union reaching the cache would report
  findings in files they cannot fix. Their exposure is **signalling only** —
  which root the 56 suite rows were evaluated against — and that is
  REQ-PKG-CONSUMERGEOMETRY-004's job, not a binding's.
- **Option B is rejected.** Admitting a disjoint suite root into
  `swept_roots()` would make the four Class B checks walk the *cache's*
  `skills/**`, converting a loud reduction into a silent wrong-tree pass: a
  forbidden phrase introduced into the working tree's `plugins/sdd/skills/**`
  would stay invisible while the run printed a clean count. That is strictly
  worse than the defect it treats.
- **C-1 is withdrawn, and Class C is not closed for a foreign consumer.**
  Rebinding the 56 rows to the swept-root union would reverse a gate-pinned
  invariant — `check_required_gated_rows_bind_to_the_suite_root()`
  (`skill-lint.py:2452`, C12.1) seeds an identically-broken decoy under the
  corpus root and asserts it is **not** reported, and
  `docs/spec/two-root-linter.md` carries the same decision as spec. The
  narrower proposal (rebinding the 40 `REQUIRED` table rows alone, which C12.1
  does not pin) is handed to the specs stage as a separate, argued proposal and
  is **not** adopted here. REQ-PKG-PACKAGING-004 stands unamended.

**Acceptance** — three assertions over `--self-test` fixtures in the existing
scratch-root style, no cache write:
1. **Option A restores coverage.** In a two-root fixture whose suite root is
   given explicitly and lies under the corpus root, `len(skill_files())` is
   greater than zero and `suite_contained()` is `True`; in the same fixture
   with the suite root left to default to a **far** scratch root,
   `len(skill_files())` is zero. Making the explicit suite root inert — i.e.
   ignoring the passed value — makes the two halves equal and this assertion
   fail.
2. **The consumer geometry is unchanged.** In fixture B's disjoint consumer
   shape (`skill-lint.py:1963`, `disjoint_suite_walk_excluded()` at `:1996`),
   `swept_roots()` equals exactly `{corpus_root}` and the suite root
   contributes zero walked files. Implementing Option B — adding the disjoint
   suite root to the union — makes this assertion fail, which is how the
   rejection is enforced rather than merely recorded.
3. **The 16 gated rows keep their binding.** C12.1 still passes unmodified. A
   C-1 rebinding of those rows makes it fail; that failure is the intended
   tripwire, not a regression to repair. **The claim is deliberately 16, not
   56**: C12.1 pins only `VERSION_GATED_SKILLS` (9) + `V4_CONTRACT_SKILLS` (7),
   so a rebinding of the **40** `REQUIRED` table rows alone — precisely the
   proposal this requirement hands forward to the specs stage — passes this
   assertion unchanged. Stating 56 here would be a criterion that cannot
   detect the one change most likely to be attempted. The 40 rows carry **no**
   binding fixture in any geometry; supplying one is part of the specs-stage
   proposal, not of this cycle, and until it exists their binding is
   unasserted — recorded rather than implied.
(see RS-CONSUMERGEOMETRY-001 Q3)
[Updated: 2026-09-21c — **the cited direction is corrected, and the bullet's
claim is narrowed, not withdrawn.** The consumer bullet above says
"-006 acceptances 3 and 5 assert **both** directions" of the re-rooting
exception. They do not: both assert the **negative** direction only —
acceptance 3 that a tree with no `plugins/sdd` does **not** fire the
derivation, acceptance 5 that a tree with `plugins/sdd` present but no
`skills/` under it does **not** fire it either. The **positive** direction —
that a consumer tree really holding `plugins/sdd/skills/` **is** re-rooted onto
that copy, which is the half this bullet actually relies on — is asserted by
`two-root-linter.md` §CG-4's **new acceptance 6**, written for exactly this
gap. So the exception is asserted in both directions, but by three acceptances
across two artifacts rather than by two in one. Nothing about the bullet's rule
changes; the citation does. Authorising requirement:
REQ-PKG-CONSUMERGEOMETRY-006 via `two-root-linter.md` §CG-4, workstream
`consumer-geometry`.]
[Priority: must]

### REQ-PKG-CONSUMERGEOMETRY-003: An explicit suite-root surface must exist
Option A is not expressible today. `Linter`'s suite root is a constructor
parameter with **no CLI flag**, and `gc.py`'s `lint_command()`
(`gc.py:507`) passes **only** `str(self.root)`, so the linter's suite root
always falls back to `default_suite_root()` — i.e. to wherever the running
`gc.py` lives — which is what *constructs* the disjoint geometry
unconditionally for every consumer. The surface must therefore exist before any
invocation can use it. This is RS-PACKAGING-003 D1's deferred `--suite-root`
question — declined as "deferred, not adopted" by REQ-PKG-PACKAGING-003 — now
**load-bearing** and hereby adopted.

REQ-PKG-PACKAGING-003's two legs are not equally affected: its rejection of
`--no-suite-rules` stands unchanged, and only its deferral of `--suite-root`
is superseded. The surface's **shape** — a CLI flag on both tools, a `gc.py`
pass-through, or a documented second positional — and what an invocation that
omits it must print are specs-stage decisions, not fixed here — but **that it is
actually passed** by a committed invocation is not deferred: see
REQ-PKG-CONSUMERGEOMETRY-006.

**What adopting the surface falsifies — one Approved spec clause, named here
rather than left to a later stage.** `docs/spec/two-root-linter.md:516-517`
asserts that "the argparse surface exposes no `--suite-root`". This requirement
makes that false on implementation, exactly as it makes REQ-PKG-PACKAGING-003's
matching acceptance clause false. It is named inside the requirement for the
same reason REQ-PKG-CONSUMERGEOMETRY-005 enumerates its falsified records
inside its own body: leaving a falsified Approved clause for whoever next reads
the spec is the failure mode this delta exists to correct, and the cycle must
not reproduce it one requirement away from where it diagnoses it. Correcting
that clause is in scope for the implement stage under this requirement, not a
follow-up.

**Acceptance** — four assertions, each with its falsifier:
1. **The surface exists and is discoverable.** A run-time grep of
   `python3 plugins/sdd/tools/skill-lint.py --help` names the suite-root
   surface. Removing it from the parser makes this fail. (This deliberately
   inverts REQ-PKG-PACKAGING-003's negative-surface grep, which asserted the
   flag's *absence*; that clause is superseded, and the inversion is the
   evidence of it.)
2. **It reaches the binding.** In a scratch fixture, invoking with an explicit
   suite root that lies under the corpus root yields `suite_contained() ==
   True` and a non-empty `skill_files()`; invoking the same corpus without it
   yields the default-derived root. Accepting the argument and discarding it
   makes the two runs identical and this fail.
3. **`gc.py` passes it through — on both of its return paths.**
   `lint_command()` (`gc.py:507-516`) has **two** branches and the criterion
   covers both, because fixing one leaves the other permanently degraded with
   nothing able to see it:
   (i) the `lint_suite_rules` branch returns
   `[executable, str(lint), str(self.root)]` — the constructed vector must
   carry the suite root, asserted on the vector rather than on the subprocess
   result;
   (ii) the `suite_rules=False` **shim** branch builds no argv at all but a
   `-c` program constructing `Linter(Path(sys.argv[2]), suite_rules=False)`,
   with no suite-root parameter anywhere — the constructed shim must pass the
   same suite root to that constructor, asserted by parsing the shim text or by
   running it against a fixture and reading back `suite_contained()`.
   Reverting either branch makes this fail; fixing only branch (i) fails the
   branch (ii) half, which is the construction that makes the two-branch
   wording load-bearing rather than decorative. The branch (i) reversion is
   row 4 of REQ-PKG-CONSUMERGEOMETRY-001's enumeration, so it is demonstrated,
   not assumed.
4. **The falsified spec clause is excised — the clause, not the item.**
   `docs/spec/two-root-linter.md:516-517` is **one clause inside a multi-clause
   checklist item**: *"… is empty, the argparse surface exposes no
   `--suite-root`, and every `suite_rules=False` site is inside the
   self-test"*. Only the middle clause dies. The surrounding item — the
   `no-suite-rules` grep and the `suite_rules=False` containment check — is
   REQ-PKG-PACKAGING-003 leg (i), which **stands**, so retiring the whole item
   would delete a pin this delta explicitly preserves. Asserted as: that file
   contains no sentence asserting the **absence** of a `--suite-root` surface,
   **and** its `no-suite-rules` and `suite_rules=False` clauses are both still
   present. Landing the surface and leaving the middle clause standing makes
   the first half red; deleting the item wholesale makes the second half red.
   The two halves fail in opposite directions, which is what stops an
   implementer resolving this with a delete.
(see RS-CONSUMERGEOMETRY-001 Q3, and RS-PACKAGING-003 D1's deferred half)
[Updated: 2026-09-21c — **two line-number citations reconciled, and the shape
of the §2 edit stated, because acceptance 4 names sites by line.**
(i) `docs/spec/two-root-linter.md:516-517`, the three-clause checklist item this
acceptance excises the middle clause of, is now at **`:522-523`**; the §2
deferral sentence acceptance 4's first half retires is now at **`:89`** (it was
`:83`). The **content**, not the number, identifies both sites —
`two-root-linter.md` §CG-9's table carries the same reconciliation, and both
files are read at run time rather than by line at implement time.
(ii) The §2 sentence is **re-scoped in place**, not deleted: its
`--no-suite-rules` leg is REQ-PKG-PACKAGING-003 leg (i) and **stands**, so only
the `--suite-root` deferral half is marked superseded, in the shape §2's other
superseded claims carry. Deleting the bullet would retire a pin this delta
explicitly preserves — the same failure mode acceptance 4's second half exists
to catch one clause lower down. Authorising requirement:
REQ-PKG-CONSUMERGEOMETRY-003 via `two-root-linter.md` §CG-2, §CG-9, workstream
`consumer-geometry`.]
[Priority: must]

### REQ-PKG-CONSUMERGEOMETRY-004: Every run declares its geometry, and a zero-sweep run says so
A run that swept nothing must not be spelled like a run that swept everything.
Today a zero-sweep run prints `OK: 0 file(s) clean` — the word *clean* over an
empty set — and nothing in the output distinguishes it from a clean run over
twenty-five files. Two output tokens close that, and their text is fixed here
verbatim because their whole value is that a reader and a fixture can both
match on them. One **concrete instance**, printable exactly as shown — this is
the literal line shape, not a schema:

```
GEOMETRY: disjoint  swept-roots=1  suite-rows-root=<suite root as given>
OK: 0 file(s) clean — NOTHING SWEPT
```

The enum is prose, not part of any printed line: the word following
`GEOMETRY: ` takes exactly one of the three values `nested`, `equal` or
`disjoint`. The spelling `nested | equal | disjoint` appears in no output.

- `GEOMETRY:` is an **own-line token**, emitted by **every** run before its
  summary line. Its value has exactly three members — `nested`, `equal`,
  `disjoint` — derived from `suite_contained()` and root equality.
  `swept-roots=<n>` is the size of the `swept_roots()` set;
  `suite-rows-root=<path>` is the suite root **as given**, which is the answer
  to "which tree were the 56 suite-gated rows evaluated against" and is the
  whole of what a foreign consumer is owed here.
- The `— NOTHING SWEPT` suffix is present **iff** `len(skill_files()) == 0`,
  on **every** summary line. There are **three** print sites, not two, and all
  three are in scope: `skill-lint.py:1186` (`FAIL: …`), `:1189`
  (`OK: … clean, W warning(s)` — the warn variant) and `:1191`
  (`OK: … clean` — the clean variant). An earlier draft cited only `:1189,1191`,
  which is the two `OK:` variants and silently omits `FAIL:`; an implementer
  following that pair would patch neither the failing path nor necessarily
  notice the warn/clean split.

**This is explicitly not the existing `corpus: FILES_SWEPT=<n>` line
(`skill-lint.py:2962`) promoted.** That line is emitted only under
`--print-population`, and RS-PACKAGING-003 D3 gave up live zero-sweep detection
on the sound ground that a swept-file *count* from a live corpus cannot be
asserted. That reasoning is preserved: the count stays informational, and what
becomes load-bearing is an **enum** and a **presence-iff suffix**, neither of
which is a count. D3 is partially superseded on exactly this point and on no
other; REQ-LINT-PACKAGING-004's "`FILES_SWEPT=<n>` is informational" clause
stands unchanged.

**Acceptance** — five assertions over scratch runs, plus one negative:
1. **The suffix is present iff nothing was swept.** Two runs, one over a
   one-file corpus and one over an empty corpus: the string `— NOTHING SWEPT`
   appears in the second summary line and not in the first. **Dropping the
   suffix makes the two runs' summary lines identical and this fail** — that is
   the mutation, and it is run, not described.
2. **The enum is rendered and correct.** The far-root fixture's run prints
   `GEOMETRY: disjoint`, the nested fixture's prints `GEOMETRY: nested`, and
   the equal-roots fixture's prints `GEOMETRY: equal`. Collapsing the
   derivation to a constant makes at least two of the three fail.
3. **`suite-rows-root=` names the root as given.** In the far-root fixture the
   rendered path equals the suite root passed to the constructor, not the
   corpus root and not `default_suite_root()`. Rendering the corpus root
   instead makes this fail.
4. **The suffix is on the failing path too.** A scratch run over a corpus that
   sweeps **zero** skill files yet raises at least one `fail`-severity finding
   prints `FAIL: … — NOTHING SWEPT`. Patching only the two `OK:` sites
   (`:1189`, `:1191`) and leaving `:1186` alone makes this red — which is the
   concrete failure the corrected anchors above exist to prevent, and it is
   asserted rather than left to the anchor list.
5. **The suffix is absent whenever anything was swept.** The warn variant
   (`:1189`) over a non-empty corpus with a warning prints no suffix. Making
   the suffix unconditional on any of the three sites makes this red.
Negative: the token appears on **every** run, so a fixture asserting a run with
findings still carries its `GEOMETRY:` line. Emitting it only on the clean path
fails that assertion.
**`gc.py` must forward the token, or a consumer never sees it.** The token's
whole purpose is to tell a consumer which tree the 56 suite rows were evaluated
against — and a consumer runs `gc.py`, not the linter directly. But
`sweep_lint()` (`gc.py:520-537`) passes through only two-line finding pairs
matching its finding regex, plus the last non-empty line if it matches
`^(OK|FAIL): `; **every other line of the linter's stdout is discarded**, so an
own-line `GEOMETRY:` token emitted by the linter reaches nobody through the
sweep. `gc.py` must therefore forward it verbatim on its own line.
**Falsifying construction**: in the disjoint scratch construction of
REQ-PKG-CONSUMERGEOMETRY-006, `gc.py --report` output contains a line beginning
`GEOMETRY: `; it contains none today, and removing the forwarding returns it to
none. Note this is a forwarding requirement only — `gc.py` derives no geometry
of its own and must not compute the token itself, since the linter is the only
process that knows its own roots.

**The sweep's summary check is a prefix match, and therefore safe.**
`sweep_lint()` tests the linter's last non-empty line with
`re.match(r"^(OK|FAIL): ", summary)` — unanchored at the right, so the
`— NOTHING SWEPT` suffix cannot make it flag `linter exited … without a
parseable summary`. This pin is audited here because the two pins below are
audited and this one is the pin an implementer is most likely to trip over
while adding a suffix; it needs no amendment.

**Interaction with the existing summary-line pins**, stated for the same reason
the `FILES_SWEPT=<n>` relationship is stated above. Two Approved texts pin the
summary line — `docs/requirements/integration/skill-lint.md:276` and
`docs/spec/skill-lint-v5.md:427,452` — as matching `OK: N file(s) clean` with no
warning clause. The suffix is **additive and conditional**, appended only when
`len(skill_files()) == 0`, and `N` is non-zero on this corpus, so those pins are
unaffected today and need no amendment. They are named here because the exposure
is nonetheless real: an **end-anchored** match on that line would break on the
zero-sweep path and on the `FAIL:` path. The implement stage must confirm those
two matches are not end-anchored; if either is, amending it is in scope under
this requirement rather than a surprise at the gate.

(see RS-CONSUMERGEOMETRY-001 Q3 §C-2, verbatim at its S4)
[Updated: 2026-09-21c — **two of this requirement's literals are re-read by
`two-root-linter.md` §CG-6, and a third measurement is superseded. Recorded as
a note, never as a rewrite**: the literals below stay exactly as approved, and
this note carries what they are now read to mean. §CG-4 establishes this
cycle's rule for a spec that reinterprets an Approved literal, and it is applied
here rather than only to REQ-PKG-CONSUMERGEOMETRY-002 — exempting this
requirement would reproduce, one requirement away, the defect this delta
diagnoses.
(i) **`suite-rows-root=<path>`**. Approved as the suite root **as given**. Read
by §CG-6 as the **effective** suite root — the one §CG-3's three precedence
tiers resolve (explicit `--suite-root`, then the corpus-root derivation, then
the script's own plugin root). Under tier 1 the two readings coincide, which is
why the original wording was not wrong at the time; under tiers 2 and 3 "as
given" names nothing, so the token would be unprintable on precisely the runs
this delta exists to signal.
(ii) **"emitted by `every` run"**. Read by §CG-6 as **iff the run prints an
`OK:` or `FAIL:` summary line**, immediately before it — one token per summary,
never two, never one without the other. That **excludes `--self-test`**, whose
`SELF-TEST OK:` / `SELF-TEST FAIL:` banner is not a corpus summary; a self-test
*case* asserts on the token by constructing a sweep and reading that sweep's
output, not by grepping the self-test's own stdout. Without this scoping a
fixture asserting "exactly one `GEOMETRY:` line" over a `--self-test` run is
undecidable.
(iii) **The interaction note's "two named sites"** (`skill-lint-v5.md:427` and
`:452`) is a **measurement superseded by a run-time grep**, which finds a
**third** pin at `:127` (§Size Warn-Clean Baseline) — `:129`, `:429`, `:454`
after that file's amendment. The settled count is **three in
`skill-lint-v5.md`, four including the requirements-side twin**
`docs/requirements/integration/skill-lint.md:276`, and the string
`OK: N file(s) clean`, not the number, identifies each site. All four were read
at implement time and confirmed **not** end-anchored, so none needed amendment;
the three `python3 tools/sdd-skill-lint.py` invocations on those pin lines were
corrected to `python3 plugins/sdd/tools/skill-lint.py` in the same read.
Authorising requirement: REQ-PKG-CONSUMERGEOMETRY-004 via `two-root-linter.md`
§CG-6, §CG-4 and `skill-lint-v5.md` §The summary-line pins, workstream
`consumer-geometry`.]
[Priority: must]

### REQ-PKG-CONSUMERGEOMETRY-005: The bundled `skills/orchestrate/tools/` copy is removed, and every record it falsifies is corrected
`plugins/sdd/skills/orchestrate/tools/` must be **removed**. It holds two files,
`gc.py` and `telemetry.py`, each byte-identical to its `plugins/sdd/tools/`
counterpart, and no invocation reaches it that works:

- Running the bundled `gc.py` directly exits on its linter-missing path —
  `error: linter missing — expected <corpus>/tools/skill-lint.py` — in every
  geometry **this repository or a consumer repository can be in, because the
  fallback path exists in neither**. `lint_path()`'s sibling-first candidate
  looks for `skill-lint.py` *next to* `gc.py`, and the skill's `tools/`
  directory does not contain one; its second candidate,
  `<corpus>/tools/skill-lint.py`, was deleted here by the packaging move and
  never exists in a consumer tree. The evidence is one foreign-scratch
  invocation plus that dead second candidate — a consumer who happened to vendor
  their own `tools/skill-lint.py` would falsify the unqualified claim, which is
  why it is not made.
- The six bare `python3 tools/telemetry.py` sites in `orchestrate` resolve
  **cwd-relative**, to `<corpus>/tools/`, never to the skill directory.
- Outside `docs/`, the string `orchestrate/tools` appears exactly once, at
  `plugins/sdd/skills/orchestrate/references/drift-sweep.md:36`, and there it
  cites the directory's **existence**, not an invocation.

Removal falsifies every record that names the directory. The enumeration below
is **the comparand** — correcting them is part of this requirement, not a
follow-up — and it was built by measuring `grep -rn "skills/orchestrate/tools"`
across the repository rather than by recalling which records the research
happened to cite. Two earlier drafts of this requirement stated the set as "six
records across five surfaces / eight distinct files"; both counts were wrong,
and `docs/ws/packaging/plan.md` appeared in neither, so the plan stage would
have sized no work for a file it must edit. **No count is written down here**:
the table is the set, and any count a criterion needs is derived from it at run
time.

**Disposition classes.** Three, because one rule does not fit all three kinds of
artifact:

- **(A) In place — live, shipped and regenerated artifacts.** They describe the
  present, so they must be made true.
- **(B) Appended dated note — closed-cycle prose records.**
  `.pre-commit-config.yaml` excludes `docs/ws/` from every automated rewrite for
  a stated reason: *"a rewrite makes the record disagree with the commits it
  describes"*. The original sentence stays exactly as that cycle wrote it and a
  `[Superseded 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-005: the bundled copy was
  removed; this observation was true at <that cycle's sha>]` note is appended
  beneath it, within three lines of the sentence it supersedes.
- **(C) In place, as data — traceability rows.** A row in a machine-regenerated
  table cannot carry an appended prose note and survive regeneration, and the
  aggregate is regenerated **from** the per-workstream file, so correcting the
  aggregate alone would be undone at the next regeneration. Class (C) is the one
  place a `docs/ws/` file is edited in place, and the exclusion's rationale does
  not reach it: the exclusion protects a *narrative* record from disagreeing
  with its commits, while a traceability row is an index, not a narrative.

| File | Occurrences measured | Disposition | What it asserts that removal falsifies |
|---|---|---|---|
| `plugins/sdd/skills/orchestrate/references/drift-sweep.md` | 1 (`:36`) | **A** | cites the directory's existence. **A shipped plugin file**, so the removal edits the shipped surface and is in a different write scope from every docs record — the plan stage must not treat it as docs-only |
| `docs/spec/two-root-linter.md` | 1 (`:360`) | **A** | describes the duplication as a requirement |
| `docs/spec/pre-commit.md` | 1 (`:274`) | **A** | same |
| `docs/spec/marketplace-packaging.md` | 1 (`:565`), plus the two checklist items below | **A** | the restoration instruction |
| `docs/requirements/traceability.md` | 1 (`:317`) | **C** | the REQ-PKG-MARKETPLACE-006 Evidence column names both bundled paths |
| `docs/ws/marketplace/traceability.md` | 1 (`:56`) | **C** | the per-workstream source row the aggregate above is regenerated from — **correcting the aggregate without this one is undone at the next regeneration**. Note `:56` is the REQ-PKG-MARKETPLACE-006 row carrying this string; `:57` is the REQ-PKG-MARKETPLACE-007 row carrying the dead freeze comparand, corrected under acceptance 4 — two different rows, two different corrections |
| `docs/ws/marketplace/verification.md` | 11 | **B** | the added REQ-PKG-MARKETPLACE-006 criterion at `:557` (*"…which exists on disk as a regular file"*) and the row's `cmp` exit 0 / `test ! -L` duplication evidence "over two pairs", plus nine further prose occurrences |
| `docs/ws/packaging/verification.md` | 6 | **B** | `:434` ("the bundled copy … is now referenced …") and five further occurrences, one of which (`:394`) is the `AGG_FIX` record this requirement separately corrects — so it is not incidental |
| `docs/ws/packaging/baseline.md` | 2 (`:63-64`) | **B** | both paths in the baseline inventory |
| `docs/ws/packaging/plan.md` | 2 (`:1131`, `:1185`) | **B** | **named in no earlier draft of this requirement.** A falsified record the plan stage would otherwise size no work for |
| `docs/ws/consumer-geometry/kickoff.md` | 2 | **excluded** | this cycle's **own** kickoff, naming the directory as the question to decide. It is not a falsified record and must not be rewritten; it is listed so the grep in acceptance 2 has a stated exemption rather than an unexplained failure |
| `docs/research/index.md` | 1 | **excluded** | the RS-PACKAGING-001 summary row, a research record of what that spike found. Research findings are historical records of a measurement, not assertions about the present tree, so removal does not falsify them; listed for the same reason as the kickoff — a measured table must account for every occurrence it does not act on |
| `docs/research/RS-PACKAGING-001-packaging-followup/findings.md` | 6 | **excluded** | same class, and that spike was itself superseded at its own stage gate |

**Two spec-checklist items are affected differently, and both are owed
corrections under this requirement** — named here rather than left to a later
reader, for the same reason the records above are:

- `docs/spec/marketplace-packaging.md:364` derives the bundled-tool population
  at run time from the glob `skills/*/tools/*.py` and asserts that for **each**
  derived pair `cmp` exits 0 and `test ! -L` succeeds. After the removal that
  glob is **empty**, so the item passes **vacuously** — a checklist item that
  checks nothing while reading as green. That is Class B vacuity newly
  introduced *into a gate* by this cycle's own removal, which is the exact
  defect class this cycle exists to close; leaving it would make the delta
  self-contradicting. The item must be retired, not left to pass over the empty
  set.
- `docs/spec/marketplace-packaging.md:365` asserts that at least one
  drift-sweep invocation under the skills tree resolves to the **bundled** copy
  and that the file it names exists. That item does not go vacuous — it goes
  **false**, which is the safer of the two failures and the one a gate would
  surface. It must be retired with the same edit.

The `docs/ws/marketplace/verification.md` record acknowledges the equivalent
problem in that cycle's own report; these two are its spec-side twins, and the
vacuous one is the more dangerous because nothing announces it.

**The dead REQ-PKG-MARKETPLACE-007 comparand travels with this correction.**
`git diff 3ddfdb3 HEAD -- tools/gc.py tools/telemetry.py` — the un-re-runnable
form that requirement's `[Updated: 2026-09-21]` note restates — is re-derived
verbatim in three further places, and nothing else in this delta binds them:
`docs/requirements/traceability.md:318` and its per-workstream source
`docs/ws/marketplace/traceability.md:57` (both **class C**, corrected in place
to the pinned blob-sha form, the source first), and
`docs/ws/marketplace/verification.md:59,102,280,457,458` (**class B**, one
appended note covering the five). Correcting the aggregate without its source is
undone at the next regeneration, which is why the source is named.

The removal lands **after** REQ-PKG-MARKETPLACE-006's amendment, never before
(that amendment is already written; see its `[Updated: 2026-09-21b]` note).
Also corrected under this requirement, as the same family of
consumer-unreachable strings: `gc.py`'s `AGG_FIX` string (`gc.py:175`), which
tells the reader to run `tools/gc.py --fix traceability-aggregate`, a path that
resolves for nobody but a pre-move in-repo operator; and the six bare
`python3 tools/telemetry.py` sites in `orchestrate` (`USAGE.md:159,439,572`;
`references/telemetry.md:484,577,602`). Both are documentation-only edits,
in scope under REQ-PKG-CONSUMERGEOMETRY-001's permission.

**Acceptance** — seven assertions, each with the construction that makes it red:
1. **Gone.** `test ! -d plugins/sdd/skills/orchestrate/tools` succeeds, and a
   run-time grep for the string `orchestrate/tools` over the repository,
   excluding `docs/`, returns **zero** matches — where it returns one today, at
   the shipped `drift-sweep.md:36`. Removing the directory but leaving that
   citation makes this red.
2. **Every class (A) and class (C) file is made true, derived not listed.** For
   each file the table above marks **A** or **C**, a run-time grep for
   `skills/orchestrate/tools` returns zero matches outside a fenced code block
   recording the removal. The file set is read from the table at run time, not
   from a literal list, so adding a row without correcting its file makes this
   red. **The class (B) files are deliberately outside this grep's scope** —
   they keep their original sentences by policy, so including them would make
   this assertion unsatisfiable, which is exactly what an earlier draft did:
   the preserved originals hold 21 occurrences between them, none of them
   fenced, so a whole-repository grep could never return zero while the policy
   was obeyed.
3. **Every class (B) record carries its note, and its original survives.** For
   each file the table marks **B**, (i) a `[Superseded 2026-09-21 —
   REQ-PKG-CONSUMERGEOMETRY-005` note appears within three lines of each
   falsified sentence, and (ii) the original sentences are **unchanged**,
   asserted by `git diff` over that file **across the correction commit
   alone** — the same single-commit comparand assertion 6 uses for the removal,
   never an open-ended diff against a later `HEAD`, which would measure whatever
   else touched the file — showing insertions only and zero deletions. If the
   committed `trailing-whitespace` / `end-of-file-fixer` hooks introduce a
   deletion in an otherwise insertion-only edit, that is a hook artefact and not
   a policy violation: re-assert over the commit with those hook changes staged
   separately. Rewriting an original in place makes (ii) red; correcting the
   prose without the note makes (i) red. The two halves fail in opposite
   directions, which is how the policy is enforced rather than merely stated.
4. **The dead comparand is corrected on both sides of the regeneration.**
   `docs/ws/marketplace/traceability.md:57` and
   `docs/requirements/traceability.md:318` carry the pinned blob-sha form and no
   `3ddfdb3 HEAD` spelling; regenerating the aggregate from the per-workstream
   file afterwards leaves it byte-identical, asserted by running the
   regeneration and diffing. Correcting only the aggregate makes this red at the
   next regeneration, which is the failure this assertion exists to catch.
5. **Neither spec-checklist item survives.** A run-time grep of
   `docs/spec/marketplace-packaging.md` for the glob `skills/*/tools/*.py`
   returns zero matches, and no checklist item there asserts that a drift-sweep
   invocation resolves to a bundled copy. Retiring the false item (`:365`) and
   leaving the vacuous one (`:364`) fails this — and it is stated as a separate
   assertion precisely because the vacuous item would otherwise pass every gate
   while checking an empty set.
6. **No invocation regressed *by the removal*.** `python3
   plugins/sdd/tools/gc.py --report --root .` and the commit gate's hooks raise
   no new finding and exit with the same status as before the removal, since no
   working invocation referenced the bundled copy. A hook that breaks falsifies
   the reachability finding this requirement rests on. **Only the removal is
   held constant here.** Note that this command is **already nested** — the
   in-repo copy's `default_suite_root()` is `<repo>/plugins/sdd` — so there is
   no degraded default here to pin or to fix; an earlier draft of this note
   claimed its geometry changes from `disjoint` to `nested`, and that was
   wrong. What REQ-PKG-CONSUMERGEOMETRY-006 changes is the geometry of a copy
   running from **outside** the corpus. Evaluate this assertion across the
   removal commit alone, never across the cycle.
7. **The corrected strings resolve.** `AGG_FIX` and the six telemetry
   invocation sites name a path that exists in this repository after the
   correction, asserted by resolving each named path at run time. A path that
   does not resolve fails this.
(see RS-CONSUMERGEOMETRY-001 Q5, Q1)
[Updated: 2026-09-21c — **acceptance 2's secondary grep gains a stated
exemption, and acceptance 5's "returns zero matches" literal is re-read with
it.** For one class (A) file the per-file `skills/orchestrate/tools` grep is
unsatisfiable **against the spec's own prescription**:
`docs/spec/marketplace-packaging.md` prescribes Q-IMPL-MARKETPLACE-029's
corrected Decision text **verbatim**, and that text keeps the literal
`skills/orchestrate/tools/skill-lint.py`, unfenced and outside any amendment
section. The same holds for the `-006` **Evidence** cell of
`docs/ws/marketplace/traceability.md`, whose replacement text that spec also
specifies verbatim including the string. Both are therefore **stated
exemptions** to that grep — on the same footing as the fenced-block and
amendment-section exemptions acceptance 2 already carries, and as the **third**
glob exemption `marketplace-packaging.md` records for Q-IMPL-MARKETPLACE-028's
`REVERTED` entry: a reverted or prescribed record is narrative, not an assertion
about the present tree, so its text is preserved and no correction reaches its
occurrence. Zero is unreachable against a **correct** implementation here, and a
zero target would be discharged only by disobeying the spec that sets it —
the outcome the exemption exists to prevent. Nothing about which files are class
(A), (B) or (C), and nothing about the removal itself, changes. The durable
record of the three-way split this closes is
Q-IMPL-CONSUMERGEOMETRY-006. Authorising requirement:
REQ-PKG-CONSUMERGEOMETRY-005 via `marketplace-packaging.md` §Secondary — a
residual grep with two stated exemptions, workstream `consumer-geometry`.]
[Priority: must]

### REQ-PKG-CONSUMERGEOMETRY-006: A tool running from outside the corpus still reaches the working tree
REQ-PKG-CONSUMERGEOMETRY-003 requires the surface to **exist**;
REQ-PKG-CONSUMERGEOMETRY-002 requires Option A as the answer for the
observation geometry. Neither requires any **real** invocation to use it, and a
surface nothing invokes repairs nothing. This requirement binds one.

**A correction to how this was first written, because it matters for every
criterion below.** An earlier draft asserted that
`python3 plugins/sdd/tools/gc.py --report --root .` reports `GEOMETRY: disjoint`
today. It does not. `default_suite_root()` (`skill-lint.py:447-454`) returns
`Path(__file__).resolve().parent.parent`, which for the **in-repo** copy is
`<repo>/plugins/sdd` — nested, contained, 25 files swept. Measured:

```
python3 <repo>/plugins/sdd/tools/skill-lint.py <repo>   → OK: 25 file(s) clean
```

The disjoint geometry belongs to a copy of the tool that lives **outside the
corpus** — the installed plugin cache, which is what the research measured
(`Linter(<repo>, <cache>/sdd/0.1.0)`), or any other out-of-tree copy. Every
committed `.pre-commit-config.yaml` entry runs an in-repo copy and is therefore
already nested. A criterion whose failing state cannot occur is the defect this
delta exists to eliminate, so the comparand below is **disjoint by
construction** rather than by reference to any in-repo path.

**The comparand — machine-independent, and red today.** The research's own
reproduction recipe: copy the suite to a scratch root, which is disjoint by
construction, and run the copied tool against this repository as corpus.

```bash
REPO=$(git rev-parse --show-toplevel)
rm -rf "$TMPDIR/cg" && mkdir -p "$TMPDIR/cg"
cp -R "$REPO/plugins/sdd" "$TMPDIR/cg/far"     # disjoint by construction; the cache is never touched
python3 "$TMPDIR/cg/far/tools/skill-lint.py" "$REPO"
python3 "$TMPDIR/cg/far/tools/gc.py" --report --root "$REPO"
```

Measured at this requirement's writing, before any change:

| Command | Today | Required |
|---|---|---|
| the far `skill-lint.py` | `.: [structure] skills/ directory not found` then `FAIL: 1 finding(s), 0 warning(s)` | `GEOMETRY: nested`, no `structure` finding, a non-zero swept-file count |
| the far `gc.py --report` | the same `[structure]` finding passed through, `FAIL: 1 finding(s), 0 warning(s), 36 info` | that finding absent |
| the in-repo `skill-lint.py` | `OK: 25 file(s) clean` | unchanged: `GEOMETRY: nested`, 25 files |

**Where `gc.py` obtains a suite root, given it has none today.** It **derives**
one from its own corpus root rather than inventing one: the candidate is
`<corpus root>/plugins/sdd`, adopted **iff** that directory exists, contains a
`skills/` directory, **and** is not already the tool's own
`default_suite_root()` (in which case nothing needs passing). This is discovery,
not invention — the adopted root names a plugin demonstrably present in the tree
being linted — and it is what REQ-PKG-CONSUMERGEOMETRY-002 permits: a foreign
consumer has no such directory, nothing is passed, their union is untouched.
Precedence, in order: an explicit operator-supplied suite root wins; failing
that, the corpus-derived candidate; failing that, today's
`default_suite_root()`.

**The literal `plugins/sdd` is a real limitation, not a hidden one.** A foreign
tree that happens to hold `plugins/sdd/skills/` — a fork of this repository, or
an identically laid out marketplace — **will** fire the derivation and be
re-rooted onto its own copy. That is the correct outcome for a fork and a
tolerable one for a look-alike, since the adopted root is still a plugin that is
actually present in the tree being linted; what it must never do is fire on a
tree that has no such directory. Acceptance 3 tests the absence direction and
acceptance 5 the false-positive direction, so both are asserted rather than one.

**Acceptance** — five assertions, each with the construction that makes it red:
1. **The disjoint invocation is repaired, asserted on the linter's own output.**
   In the scratch construction above, the far `skill-lint.py` run prints
   `GEOMETRY: nested` and raises no `[structure] skills/ directory not found`
   finding. **It prints that finding and `FAIL: 1 finding(s)` today**, so the
   assertion is red before the change and green after. Reverting the derivation
   returns it to red. The assertion is stated against `skill-lint.py` because
   `gc.py` cannot carry the token — see assertion 2 and
   REQ-PKG-CONSUMERGEOMETRY-004's forwarding clause.
2. **End to end through the sweep.** In the same construction, the far
   `python3 "$TMPDIR/cg/far/tools/gc.py" --report --root "$REPO"` raises **no**
   `[structure]` finding, where it raises exactly one today. This is asserted on
   the finding set rather than on the `GEOMETRY:` token **because the token's
   forwarding is a separate requirement whose landing order is not fixed here**:
   REQ-PKG-CONSUMERGEOMETRY-004 requires `gc.py` to forward the token, and once
   it lands a token assertion at this point becomes decidable — but until then
   `sweep_lint()` (`gc.py:520-537`) passes through only two-line finding pairs
   and the final `^(OK|FAIL): ` summary, discarding every other line. The
   finding set is decidable under **both** orderings, which is why it is the
   comparand. -004 carries the token assertion; this one does not duplicate it.
   Reverting `lint_command()` makes the finding reappear.
3. **The foreign consumer is untouched.** In a scratch corpus with its own
   `skills/` and **no** `plugins/sdd/`, the derivation does not fire: no suite
   root is passed, `swept_roots()` equals exactly `{corpus_root}`, the token
   reads `disjoint`, and their own `skills/` is still walked so no
   `— NOTHING SWEPT` suffix appears. Making the derivation unconditional — for
   instance by falling back to the tool's own location — fires it here and makes
   this red.
4. **The nested case is not regressed.** The in-repo
   `python3 plugins/sdd/tools/skill-lint.py .` still reports `GEOMETRY: nested`
   and the same 25-file count it reports today, derived at run time rather than
   pinned as a literal. A derivation that re-roots or double-counts the already
   contained case makes this red — which is a live risk, not a theoretical one,
   since the in-repo copy's derived candidate and its `default_suite_root()` are
   the same directory.
5. **The derivation is conditional on what is actually there.** With
   `plugins/sdd/` present but holding no `skills/` directory, the candidate is
   **not** adopted and the run reports `disjoint` rather than naming a suite
   root with nothing in it. Dropping the `skills/` existence test makes this
   red.

**No assertion is made about the committed hook set, and that is deliberate.**
Every `.pre-commit-config.yaml` entry (`:29`, `:35`, `:55`, `:61`) runs an
in-repo copy, so every one is already nested and no hook can be "left on the
degraded default". An assertion over them would describe a state that cannot
occur. What would have to be true for such an assertion to be falsifiable is
that a hook invoked an out-of-tree copy of the tool — which none does and none
should. Assertion 4 covers the only hook-relevant risk that is real: that the
change regresses the nested case they all run in.

**One further criterion, labelled machine-dependent and therefore not
gating.** On a machine with the plugin installed, running the cache's own
`skill-lint.py` against this repository should likewise report
`GEOMETRY: nested` after the change, where it reports the `[structure]` finding
today. It is recorded as an observation for the verify stage, never as a gate
assertion, because it depends on an installed cache whose presence and version
no gate can guarantee — and per the kickoff the cache is a read-only
measurement surface.
(see RS-CONSUMERGEOMETRY-001 §Measurement technique and §Reproduction, and Q3
Option A cost (ii))
[Priority: must]
