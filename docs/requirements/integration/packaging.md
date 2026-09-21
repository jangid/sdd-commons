---
domain: PKG
last_updated: 2026-09-21
status: Approved
research_refs: [RS-MARKETPLACE-001]
workstream: marketplace
---

# Requirements: Marketplace and Plugin Packaging

## Overview

This repository becomes a **Claude Code marketplace** named `sdd-commons`
carrying a single umbrella plugin named `sdd`, so that the ten SDD skills, the
two runnable tools and the three agents install with
`/plugin marketplace add jangid/sdd-commons` followed by
`/plugin install sdd@sdd-commons`. The packaging is a **manifest statement over
the existing tree**, not a file migration: under RS-MARKETPLACE-001 Q3 a plugin
entry may set `"source": "./"` and an explicit component list, so what ships and
what stays behind are decided in two new JSON files and **zero existing files
move**. That property is what keeps this cycle's rename (NAME domain) from
touching the same references twice.

Two exclusions are packaging decisions rather than omissions, both settled by
RS-MARKETPLACE-001: `docs/` stays in the repository but is not a plugin
component (Q1 — it is this repository's own SDD corpus, never an input to any
skill's phase detection), and the three contributor tools stay out of the plugin
(Q2 — from an installed plugin they would root on the plugin's own copy and
report a false green about the user's repository).

Both exclusions are exclusions from the plugin's **component list** — the set
Claude Code loads as skills and agents. They are not exclusions from what an
install copies: under `"source": "./"` the installed plugin carries the whole
repository tree, `docs/` and the contributor tools included. The real-session
install of REQ-PKG-MARKETPLACE-010 measured `docs/` at 144 files and 48,462
lines, most of the install's ~5 MB. That copy is inert — no component is loaded
from it and no skill body can reach it — so the exclusions still hold as
statements about loading, which is what they were written to guarantee.

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
the install's file inventory, and the install's carrying `docs/` is an accepted,
documented cost rather than a violation.
**Acceptance**: a run-time grep over `skills/` for `docs/` citations that are
absolute, home-rooted, or rooted on a plugin path variable returns zero matches;
the manifest component check of REQ-PKG-MARKETPLACE-003 shows no `docs/` path.
[Priority: must]

### Tools

### REQ-PKG-MARKETPLACE-005: Contributor tools are loaded as no plugin component
The skill-lint, scope-check self-test and evaluation tools must stay in the
repository and must be absent from the plugin's component list — which, as
above, keeps them from being loaded, not from being copied into the install. They are
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
