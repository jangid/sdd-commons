---
status: Approved
last_updated: 2026-09-22
requires:
  - REQ-PKG-MARKETPLACE-001
  - REQ-PKG-MARKETPLACE-002
  - REQ-PKG-MARKETPLACE-003
  - REQ-PKG-MARKETPLACE-004
  - REQ-PKG-MARKETPLACE-005
  - REQ-PKG-MARKETPLACE-006
  - REQ-PKG-MARKETPLACE-007
  - REQ-PKG-MARKETPLACE-008
  - REQ-PKG-MARKETPLACE-009
  - REQ-PKG-MARKETPLACE-010
  - REQ-PKG-PACKAGING-010
  - REQ-PKG-CONSUMERGEOMETRY-001
  - REQ-PKG-CONSUMERGEOMETRY-005
---

# Marketplace and Plugin Packaging

## Overview

This repository becomes a Claude Code **marketplace** named `sdd-commons`
carrying exactly one umbrella **plugin** named `sdd`. The packaging is a
*manifest statement over the existing tree*: two new JSON files declare what
ships, and **no existing file moves**. That property is the whole design —
it is what lets the rename (`skill-namespace-rename.md`) land first as an
independently verifiable step without any reference being edited twice
(REQ-NAME-MARKETPLACE-007). [Superseded 2026-09-21 — see §Placement: the
shipped suite moves to `plugins/sdd/`, so "no existing file moves" no longer
holds and is no longer the design. It was true of the marketplace cycle, and
the rename it sequenced had already landed by the time this cycle moved the
tree; nothing downstream of the move rests on it.]

Two exclusions are deliberate statements rather than omissions: `docs/` is not
a plugin component (REQ-PKG-MARKETPLACE-004), and the three contributor tools
are not plugin components (REQ-PKG-MARKETPLACE-005). Both are expressed by
**absence from an explicit component list**, which is why the list is
enumerated rather than wildcarded.

**What that absence does and does not mean.** The component list governs what
Claude Code **loads as a component** — what a session surfaces as a skill or an
agent. It does not govern what is **copied into the install**: under
`"source": "./"` the whole repository tree is materialised into the installed
plugin, `docs/` and contributor tools included. [Superseded 2026-09-21 — see
§Placement: `source` now names `plugins/sdd`, so the install materialises the
**suite root only** and `docs/` is outside the install entirely rather than
copied-but-inert. The observation below records the pre-move `"./"` install and
is kept as the evidence for why the exclusion was made real.] The real-session install
observation measured this directly (Q-IMPL-MARKETPLACE-020): the install carries
144 files and 48,462 lines of `docs/`, most of its ~5 MB, while
`claude plugin details` reports zero components from it. The shipped copy is
inert — see §`docs/` stays behind for why it cannot shadow anything.

This spec assumes the rename has already landed, so every name it uses is the
post-rename name: skills are `skills/<name>/` with no prefix, tools are
`tools/<name>.py` with no prefix, and components surface as `sdd:<name>`.

## Design

### The manifest pair

Two new files, both valid JSON, both inside the `.claude-plugin/` directory **at
the repository root** — that is, in a top-level `.claude-plugin/`, not nested
somewhere deeper in the tree. "At the repository root" below always means that
top-level `.claude-plugin/` directory, never a file sitting loose in the root
itself; the manifests are `.claude-plugin/marketplace.json` and
`.claude-plugin/plugin.json`, and neither exists anywhere else.

| Path | Role |
|---|---|
| `.claude-plugin/marketplace.json` | Declares the marketplace, its owner, and its single plugin entry (including the component list). |
| `.claude-plugin/plugin.json` | Declares the plugin's own identity: `name`, `description`, `version`, `author`, `license`. |

`.claude-plugin/plugin.json` sits in the **root-level `.claude-plugin/`
directory**, not under a `plugins/sdd/` subdirectory, because the plugin entry
sets `"source": "./"`. The repository must not grow a `plugins/` directory at
all. [Superseded 2026-09-21 — see §Placement: the suite moves to `plugins/sdd/`
and the plugin manifest moves with it; only the single-plugin decision survives.]

**Marketplace manifest shape** (field names follow the installed first-party
marketplaces observed by RS-MARKETPLACE-001 Q3):

```json
{
  "name": "sdd-commons",
  "owner": { "name": "<owner name>" },
  "plugins": [
    { "name": "sdd", "source": "./", "description": "…",
      "skills": ["./skills/<name>", "…"],
      "agents": ["./agents/<name>.md", "…"] }
  ]
}
```

**Plugin manifest shape**:

```json
{ "name": "sdd", "version": "<semver>", "description": "…",
  "author": { "name": "<author>" }, "license": "MIT" }
```

The `license` value is the MIT identifier and must agree with the `LICENSE`
file (`project-docs.md`, REQ-DOCS-MARKETPLACE-001). The spec fixes the shape of
`version` (a semver string) but not its opening value; the first published
version is recorded as Q-IMPL-MARKETPLACE-015 rather than left to be inferred
from the file.

**Why `"source": "./"` and one plugin, not a split or a subdirectory.** The
driver dispatches its sibling phase skills **by name**, not by path. A split
that places the driver and a phase skill in different plugins leaves a name
resolving to nothing at dispatch time — a silent runtime failure no linter can
catch. A `plugins/sdd/` subdirectory would additionally have to move `skills/`
and `tools/`, which would invalidate the linter's literal skill paths and its
own root resolution at the same moment the rename is being verified. `"./"`
moves zero files and keeps both steps separable. [Superseded 2026-09-21 — see
§Placement: the subdirectory argument is overtaken, the single-plugin one is not;
the two roots and the linter's root resolution are `two-root-linter.md` §1–§2.]

### The component list and its derivation rule

The component list is **explicit**: every shipped skill directory and every
shipped agent file is named. It is not a wildcard, because the `docs/` and
contributor-tool exclusions are expressed by absence from it — absence from the
set Claude Code loads, not absence from the copied tree (§Overview,
Q-IMPL-MARKETPLACE-020).

The list is checked by deriving **both sides at run time** — never against a
count or a written-out list:

- **Skills.** A "skill directory" is a directory under `skills/` that contains
  a `SKILL.md`. The set of basenames in the manifest's `skills` list must equal
  the set of such directories. The `tools/` subdirectory bundled inside the
  driver skill contains no `SKILL.md`, so this derivation already excludes it:
  it is part of the driver skill's own directory, not a skill of its own, and
  is neither listed separately nor counted as missing.
- **Agents.** The set of paths in the manifest's `agents` list must equal the
  set of `*.md` files directly under `agents/` (`harness-agents.md`,
  REQ-AGENT-MARKETPLACE-001).
- **Exclusions.** No listed path may begin with `docs/`, and none of the three
  contributor tools may appear anywhere in the list.

### `docs/` stays behind

`docs/` remains in the repository unchanged — it is the corpus this
repository's own cycles read and the drift sweep sweeps — and is absent from
the component list.

"Stays behind" is a statement about **loading**, not about copying. An install
made under `"source": "./"` carries the repository tree including `docs/` — the
observed cost is 144 files and 48,462 lines, most of the install's ~5 MB — and
that copy is **inert**: no manifest entry names it, `claude plugin details`
reports zero components from it, and no skill body can reach it, because every
`docs/…` citation in a skill body is a bare relative path resolving against the
operator's own working directory. The shipped copy therefore cannot shadow an
installing user's own corpus. [Superseded 2026-09-21 — see §Placement: with
`source` naming `plugins/sdd` there is no shipped copy of `docs/` at all. The
"stays behind" conclusion is unchanged and now holds by exclusion from the
install rather than by inertness of a copy; the bare-relative-path invariant
below is unaffected and still binds.]

The system must not require `docs/` to be present in an installed plugin.
Every `docs/…` citation inside a skill body is a **bare relative path**, which
resolves against the operator's own project working directory — which is where
an installing user's own SDD corpus lives. The invariant to preserve is
therefore negative and mechanically checkable: **no `docs/…` citation in
`skills/` may be absolute, home-rooted, or rooted on a plugin path variable.**

### Tools: root stays, the skill-runnable set is duplicated into the driver skill

`tools/` stays at the repository root, so that every existing `tools/…`
reference in `docs/` (a record of what a past cycle ran here) and every prose
reference keeps its spelling. [Superseded 2026-09-21 — see §Placement and
`two-root-linter.md` §1: `tools/` is a suite member and moves to
`plugins/sdd/tools/`. Existing `tools/…` spellings in `docs/` are historical
records and are not rewritten; live skill-body invocations are repaired by
`two-root-linter.md` §8.]

Two classes of tool, with different destinations. No count is stated. A
bundled population was formerly derived at run time from the `*.py` files under
each skill's own `tools/` subdirectory, and every check over it derived the same
way; that population is **empty** since the driver skill's `tools/`
subdirectory was removed on 2026-09-21 under REQ-PKG-CONSUMERGEOMETRY-005, so
nothing is bundled and no check derives over it.

| Class | Tools | Ships in plugin? | Why |
|---|---|---|---|
| **Runnable from a skill** | the drift sweep, the telemetry tool | yes — in the suite's own `tools/` directory [Updated: 2026-09-21 — the duplicate under the driver skill's own `tools/` subdirectory was removed under REQ-PKG-CONSUMERGEOMETRY-005] | a skill body tells the operator to run them |
| **Contributor-only** | the skill linter, the scope-check self-test, the evaluation tool | no | never invoked from a skill body; the linter's rules are keyed to *this* repository's skill set, so from an installed plugin it would assert this repository's contract rows about the user's tree |

The drift sweep delegates its structural sweeps to the linter as a subprocess.
[Superseded 2026-09-21 — see §Placement.] Its resolution is **sibling-first**,
not corpus-rooted: it tries the linter beside its own script file first and
falls back to `<root>/tools/skill-lint.py` only if that is absent. That order is
what keeps the commit gate working after the move — the sweep and the linter
travel together into `plugins/sdd/tools/`, so the sibling candidate resolves and
the corpus-rooted candidate, which after the move never exists in this
repository, is never reached. The earlier text here predicted a `linter missing`
exit 2 for the gate's own sweep; that prediction was wrong about the existing
behaviour and is retired. This resolution order — sibling first,
`<root>/tools/skill-lint.py` as the fallback, `linter missing` when neither
exists — is the contract of **REQ-PKG-PACKAGING-010**, which states it as a
requirement of the existing code so it is not silently reordered later.
**The move changes no tool source**: sibling-first
resolution is already implemented, so REQ-PKG-MARKETPLACE-007's source freeze
still binds and the move is a rename with zero content hunks. The residual
consumer-repository case is unchanged: a consumer invoking a sweep that has
neither a sibling linter nor a `<root>/tools/skill-lint.py` still exits 2 with
`error: linter missing` — a documented limitation, carried to a later cycle
rather than patched here (Q-IMPL-MARKETPLACE-029).

**Duplicated, not symlinked.** A plugin install may be materialised from a git
archive, which does not reliably preserve symlinks, so a symlink is a silent
broken-install mode. Each bundled copy must be a regular file byte-identical to
its **suite-root** original [Amended 2026-09-21 — §Placement: post-move the
originals are `plugins/sdd/tools/*.py`; there is no repository-root `tools/`].

**The identity is verified once per cycle, by design — not continuously.** The
`cmp` assertion of the criterion below runs at this cycle's close and is not
added as a seventh hook to the commit gate. This is a deliberate choice, recorded
here so a later reader does not read the gap as an oversight. `pre-commit.md`
§No rule of the gate's own would not forbid such a hook — the rule it would
enforce is stated right here, in a requirement — but the gate's hook set is
closed at six (`pre-commit.md` §The hook set) and the cost/benefit does not
justify reopening it: the duplication is created once, in one chunk, by one
mechanical copy, and the far more likely failure mode is a future edit to a
bundled tool that forgets the copy — a hazard a later cycle can answer, either by
reopening the hook set or by folding the assertion into the drift sweep, which is
already a whole-corpus invariant checker and already runs in the gate. Either
route is preferable to a bespoke seventh hook today. If the duplication ever
grows past the population one packaging chunk creates by one mechanical copy —
measured by the same run-time derivation, never by a count written here — that
reconsideration becomes due.

**Loss check by identity, not by name.** Because the rename changed every
tool's filename, a name-set comparison against git history would fail by
construction. The check is therefore: `git log --follow` resolves each
post-change `tools/*.py` to its pre-change history, and the count of
`tools/*.py` after is not less than before — both derived at run time.

### Root resolution for skill-side invocations

Every invocation of a bundled tool from a skill body must reach the
**operator's own repository** as its root, never the plugin's:

The **binary** and the **subject** are two separate resolutions, and an
invocation needs both to be right:

- **Drift sweep** — the path to the script is **skill-directory-relative**
  (`<skill-dir>/tools/gc.py`, where `<skill-dir>` is the driver skill's own
  directory), so the copy REQ-PKG-MARKETPLACE-006 bundles is the copy that runs
  and the invocation still resolves in a consumer repository that has no
  repository-root `tools/` directory. It is invoked with an explicit root
  argument naming the current directory. Without it the tool defaults to its own
  script location and would sweep the plugin's copy, returning a false green
  about the user's repository. Bundling a tool that nothing resolves to is a
  dead copy; keeping `--root .` on a bundled binary is what keeps the subject
  the operator's tree — the two properties are required together
  (Q-IMPL-MARKETPLACE-024).
- **Telemetry tool** — continues to rely on its cwd-relative default **file**
  path and is **not** given a plugin-relative path for that file, because the
  telemetry file is written into and read from the operator's repository.

What counts as an *invocation* for that grep is the same test this spec already
applies to the contributor tools — an occurrence carrying a shell invocation
prefix (`python3 ` or `./`) — and not a bare prose or gate-line mention of the
tool's path; that reading is recorded as Q-IMPL-MARKETPLACE-014.

Neither tool's source is edited to satisfy this. The packaging step makes **no**
behavioural and no source change to either tool; the only permitted source edit
to them in this cycle is the rename of their self-referential name strings,
which happens earlier, in the rename step (REQ-NAME-MARKETPLACE-003).

**The freeze holds unnarrowed (Q-IMPL-MARKETPLACE-029).** A narrowing of this
freeze was written on 2026-09-21 to admit a provenance conditional in the drift
sweep, so that a bundled sweep run from a consumer repository would suppress this
repository's suite-specific contract rows. The predicate failed in both
directions — keyed to the script's location it disabled this repository's own
rows under the invocation the driver documents; keyed to the root swept it could
not distinguish a consumer tree from this one by anything a consumer tree
carries. The operator reverted the whole extension rather than patch the
predicate a third time, so the freeze stands exactly as written above: no source
edit to either bundled tool beyond REQ-NAME-MARKETPLACE-003's rename.

### No skill body depends on the plugin-root variable

Across the marketplaces installed on this machine, every actual use of the
plugin-root environment variable sits in a **manifest field** (hook or MCP
server) or in a **command body** — never in a skill body. The documented
pattern for a skill's bundled files is skill-directory-relative. A skill that
resolved a path through that variable would be relying on an unattested
expansion, so no skill body may do so. The only permitted occurrence of the
variable's name under `skills/` is inside a fenced code block that is
explicitly documenting its manifest-only scope.

### Dangling spec citations: an accepted, documented gap

Skill bodies cite contract files under `docs/spec/` as reading references. Those
citations are **not** rewritten by this cycle: the skill never opens them at
runtime, and the linter already classifies an unresolvable one as *warn*
severity precisely so a consumer repository is not assumed to have this
repository's layout. Rewriting them would be a large edit across many files for
no runtime benefit.

The gap is closed by documentation instead: `CONTRIBUTING.md` states that the
contracts live in the repository and not in the install, so a reader who
follows a citation from an installed skill knows where to look. The design
invariant is that the **count of such citations is unchanged** across the
packaging change — measured by running the same grep before and after, never
against a pinned number. The counted population is the **skill bodies**
(`*.md` under `skills/`), not every file that happens to sit under `skills/`;
the bundled tool sources carry their own `docs/spec/…` strings and are outside
this invariant, as Q-IMPL-MARKETPLACE-016 records.

### Install verification

Before the cycle closes, the pushed branch is installed as a marketplace in a
real session, and the install is **observed** to (a) list the plugin's skills
under their namespaced names, and (b) successfully read at least one of the
driver's lazily-read `references/*.md` files from the installed copy. That
those lazily-read files resolve from an installed plugin is the one packaging
assumption research could not observe directly.

Because the cycle's terminal state is an **open PR**, the `owner/repo`
shorthand is not usable — it always resolves the default branch. Two documented
mechanisms are valid and the operator picks one at the verify stage:

| Mechanism | Invocation |
|---|---|
| local path | `/plugin marketplace add <absolute path to the worktree>` |
| branch-qualified git URL | `/plugin marketplace add https://github.com/jangid/sdd-commons.git#marketplace` |

A failed install once a mechanism has been used is a **replan trigger for this
cycle**, not a documented limitation. A mechanism merely being unavailable is
not a trigger.

The local-path mechanism carries one property worth knowing before it is reused:
it copies the working tree verbatim, gitignored content included, so its install
cache can hold local state a git-sourced install would never carry
(Q-IMPL-MARKETPLACE-021).

## Acceptance Criteria

Every criterion derives both sides at run time. No corpus-measured count is
written into a criterion as a literal. All commands run from the repository
root with any nested `.worktrees/` path excluded from tree walks.

**[Amended 2026-09-21 — §Placement.] Every bare `skills/`, `agents/` and
`tools/` path below reads as `plugins/sdd/<path>` after the move**, and each
command that walks one asserts `test -d` on that directory **first**. Without
that guard the move turns most of this block into vacuous passes: a `grep -rn …
skills/` over a directory that no longer exists at the corpus root returns no
match and the criterion reads as satisfied, which is a criterion that cannot
fail rather than one that holds. The corpus-root paths in the block
(`CONTRIBUTING.md`, `docs/`) are unaffected. **This clause is a reading aid for
the purely post-move, single-tree criteria only.** Three criteria below have one
side that straddles the move commit, or compare paths rooted differently on
their two halves, and a uniform re-reading breaks them; each carries its own
`[Amended 2026-09-21]` note in place and that note governs — REQ-PKG-MARKETPLACE-003
(the agents half), -006 (the pre-move loss count) and -007 (the source freeze).

- [ ] `python3 -c "import json;json.load(open('.claude-plugin/marketplace.json'))"` exits 0, and the parsed document's `name` equals `sdd-commons`, its `owner` is present, and its `plugins` list has exactly one entry whose `name` is `sdd` — all read from the parsed file (REQ-PKG-MARKETPLACE-001).
- [ ] ~~The parsed plugin entry's `source` equals `./`; … `test ! -d plugins` succeeds~~ **[Superseded 2026-09-21 — §Placement.]** This criterion is retired, not merely re-worded: after the move `source` names `plugins/sdd` and a `plugins/` directory must exist, so both clauses are now false by design and no plan task is scheduled against them. What survives of REQ-PKG-MARKETPLACE-002 is checked by `two-root-linter.md` §Acceptance Criteria bullet 1 (the manifest pair, the resolved `source`, the component-list `test -e` sweep) plus the single-plugin clause below (REQ-PKG-MARKETPLACE-002).
- [ ] The parsed marketplace document's `plugins` list still has exactly **one** entry — the single-plugin decision of REQ-PKG-MARKETPLACE-002, which §Placement leaves binding — and `plugins/sdd/.claude-plugin/plugin.json` parses and carries `name`, `description` and `version` (REQ-PKG-MARKETPLACE-002).
- [ ] A script derives, at run time, the set of basenames in the manifest's `skills` list and the set of directories under `skills/` containing a `SKILL.md`, and asserts set equality; likewise the manifest's `agents` list against `*.md` files directly under `agents/`, **compared as basenames on both halves** — [Amended 2026-09-21 — §Placement] manifest-listed component paths are read relative to the **suite root** and stay suite-relative (`./agents/<name>.md`, since `source` names `plugins/sdd`) while the filesystem half becomes `plugins/sdd/agents/<name>.md`, so a literal path-set equality would compare differently-rooted strings and fail on every row; the skills half already compares basenames and is unaffected — and asserts no listed path starts with `docs/` (REQ-PKG-MARKETPLACE-003).
- [ ] `grep -rnE '(^|[^A-Za-z0-9._/-])(/|~/|\$\{?[A-Z_]*PLUGIN_ROOT)[A-Za-z0-9._/-]*docs/' --include='*.md' skills/` returns no match, and the manifest check above shows no `docs/` path (REQ-PKG-MARKETPLACE-004).
- [ ] A run-time grep over `skills/` for an invocation prefix (`python3 ` or `./`) of any of the three contributor tools returns zero matches, and none of the three appears in the manifest component list (REQ-PKG-MARKETPLACE-005).
- [ ] [Amended 2026-09-21b — REQ-PKG-CONSUMERGEOMETRY-005: this item's **bundled-population clause is excised**, and the item survives. That clause derived a population at run time from the `*.py` files under each skill's own `tools/` subdirectory, paired each with the suite-root file of the same basename, and asserted `cmp` exit 0 and `test ! -L` on every derived pair; the driver skill's `tools/` subdirectory was removed under that requirement, so the population is now empty and the clause would pass **vacuously**. The clauses below are REQ-PKG-MARKETPLACE-006's surviving half — its `[Updated: 2026-09-21b]` note's "no tool is lost from the suite's `tools/` directory, compared by identity rather than by name" — and are this item's only live pin, which is why the item is not retired whole. The prior `[Amended 2026-09-21 — §Placement]` note attached to the excised clause and goes with it.] `git log --follow` resolves every post-change `plugins/sdd/tools/*.py` to pre-change history. **The loss check spells its two sides separately**, because they straddle the move commit and no single spelling is correct on both: the post-move side is `ls plugins/sdd/tools/*.py | wc -l`, the pre-move side is `git ls-tree --name-only <cycle entry sha> tools/ | grep -c '\.py$'` (the entry commit is pre-move, so a uniform rewrite would make it zero), and the former is asserted not less than the latter — both sides derived by command (REQ-PKG-MARKETPLACE-006).
- [ ] ~~At least one drift-sweep invocation under `skills/` resolves to the **bundled** copy: a run-time grep over `skills/**/*.md` for invocations of the sweep returns a non-empty set whose script path is skill-directory-relative rather than cwd-relative, and the file that path names exists under the driver skill's own directory — derived by command, no count pinned~~ **[Retired 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-005.]** This criterion is retired whole, not re-worded: it rests entirely on REQ-PKG-MARKETPLACE-006's duplication clause, which that requirement's `[Updated: 2026-09-21b]` note supersedes. The driver skill's `tools/` subdirectory is removed, so no invocation anywhere resolves to a bundled copy and the item goes **false** rather than vacuous. No plan task is scheduled against it (REQ-PKG-MARKETPLACE-006).
- [ ] Every drift-sweep invocation found in `skills/` by a run-time grep carries an explicit root argument; no telemetry invocation in `skills/` passes a file path beginning with a skill or plugin directory; and the **source freeze** is asserted by content identity rather than by an empty diff [Amended 2026-09-21 — §Placement]: for each of the two tools, `git show <rename-chunk-close-sha>:tools/<tool> | cmp - <(git show 0bdb076:plugins/sdd/tools/<tool>)` exits 0 [Repinned 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-001 acceptance 5: the right endpoint was the **working tree**, which leaves the window open, so once REQ-PKG-CONSUMERGEOMETRY-001's permitted edits touch `plugins/sdd/tools/gc.py` the item turns red for being evaluated outside its own window rather than because the freeze was violated. It is repinned to the packaging cycle's end sha `0bdb076`; equivalently, the blob-sha equality `git rev-parse <rename-chunk-close-sha>:tools/<tool> == git rev-parse 0bdb076:plugins/sdd/tools/<tool>`]. The former `git diff <rename-chunk-close-sha> HEAD -- tools/<drift sweep> tools/<telemetry tool>` **is empty** form is retired as false by construction after the move, and the blanket clause cannot repair it under any path spelling: rewritten to `plugins/sdd/tools/…` the pathspec names nothing at the old sha and the whole file reports as added; left as `tools/…` it reports as deleted; with `-M` it reports a rename. An equivalent accepted form is `git diff -M <rename-chunk-close-sha> 0bdb076 -- tools/ plugins/sdd/tools/` [repinned with the clause above, same date and requirement — `HEAD` left this form's right endpoint open too], asserted to contain only rename records with zero content hunks (REQ-PKG-MARKETPLACE-007).
- [ ] A run-time grep for the plugin-root variable name over `skills/**/*.md` returns no match outside a fenced code block documenting its manifest-only scope (REQ-PKG-MARKETPLACE-008).
- [ ] `CONTRIBUTING.md` contains a paragraph stating that spec citations inside skills resolve in the repository, not in an installed plugin; the same `docs/spec/*.md` citation grep over `skills/` yields the same count before and after the packaging change — **the two sides straddle the move commit**, so the before-side grep is run over the pre-move `skills/` tree at the cycle's entry commit and the after-side over `plugins/sdd/skills/`; only the counts are compared, which is invariant under the re-rooting [Amended 2026-09-21 — §Placement] (REQ-PKG-MARKETPLACE-009).
- [ ] The verification report records, as observations with their commands: the install command run, the namespaced skill names the session listed, and the name of the `references/*.md` file read from the installed copy (REQ-PKG-MARKETPLACE-010).
- [ ] The skill linter exits 0 and its `--self-test` passes after the packaging change; the drift sweep's report raises no finding absent from the cycle's entry sweep, compared against that sweep's recorded output.

## Implementation Questions

### Q-IMPL-MARKETPLACE-014: "Invocation" for the root-argument grep means a shell invocation prefix
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Root resolution for skill-side invocations; §Acceptance Criteria, the REQ-PKG-MARKETPLACE-007 criterion
**Decision**: An occurrence of the drift sweep under `skills/` is an
*invocation* — and so must carry an explicit `--root .` — when it is prefixed by
`python3 ` or `./`. A bare mention of the tool's path in prose, in a table cell
describing it, or inside the rendered `GC:` gate-line token is a *reference*,
not an invocation, and is left alone.
**Rationale**: The spec already uses exactly this prefix test to define an
invocation of a contributor tool (REQ-PKG-MARKETPLACE-005), so reusing it keeps
one definition rather than two. The alternative — treating every textual
occurrence as an invocation — would rewrite the fixed `GC: F fail, W warn — run
tools/gc.py --report` gate-line token, which `harness-loop-control.md` pins as a
verbatim rendered string; changing it to satisfy a packaging grep would be a
behavioural contract change, which this cycle explicitly forbids.

### Q-IMPL-MARKETPLACE-015: The plugin manifest opens at version 0.1.0
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The manifest pair, the plugin manifest shape
**Decision**: `.claude-plugin/plugin.json` carries `"version": "0.1.0"`.
**Rationale**: The spec requires a semver string but names no opening value. The
cycle's terminal state is an open PR, not a release, and the install has not yet
been observed in a real session (§Install verification), so a `0.x` line states
"published, not yet stabilised" honestly. `1.0.0` would assert a stability
commitment no criterion of this cycle establishes.

### Q-IMPL-MARKETPLACE-016: The citation-count invariant is scoped to skill bodies
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Dangling spec citations; §Acceptance Criteria, the REQ-PKG-MARKETPLACE-009 criterion
**Decision**: The before/after `docs/spec/*.md` citation grep over `skills/` is
run with `--include='*.md'`, so it counts citations in skill **bodies** only.
Measured that way the count is unchanged across the packaging change.
**Rationale**: The invariant exists because a skill body's citation must keep
resolving the same way for a reader. The unscoped grep is not stable across this
chunk by construction: bundling the drift sweep and the telemetry tool into the
driver skill's `tools/` subdirectory copies their own `docs/spec/…` strings under
`skills/`, and those are tool source, not citations a skill body offers a reader
to follow. The two populations were measured separately to confirm the whole
difference is exactly the bundled copies' own strings and nothing in any skill
body moved.

### Q-IMPL-MARKETPLACE-020: The component list governs loading, not copying — `docs/` ships inside the install
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Overview; §The component list and its derivation rule; §`docs/` stays behind
**Decision**: Keep the layout and the acceptance criteria unchanged, and correct
the text that read the component list as an exclusion from what is *copied*. The
list expresses what Claude Code **loads as a component**; under `"source": "./"`
the whole repository tree is materialised into the install, `docs/` included.
The requirement and spec text now say so plainly, at the measured cost. Operator
decision, 2026-09-21: accept and document.
**Rationale**: The real-session install observation (plan Chunk 7 task 2)
measured the installed copy directly: 144 files and 48,462 lines of `docs/`,
most of the install's ~5 MB. The acceptance criteria as written passed — they
parse the manifest, and the manifest does name no `docs/` path — so they were
true but measured the wrong object, the same species of false criterion this
cycle's measurement discipline warns about. They are therefore left intact and
what they do not establish is stated rather than the criteria weakened. This is
not a correctness defect: every `docs/…` citation in a skill body is a bare
relative path that resolves against the operator's own project, so the plugin's
copy is unreachable from any skill and `claude plugin details` reports zero
components from it.
**Carried forward, not settled.** The operator's decision closes this *cycle*,
not the question: `docs/` is to be moved outside the install in a following
cycle. The decisive constraint for whoever designs that change is the one this
entry records — the component list cannot express it, so a criterion written
against the manifest will pass while the condition persists, exactly as these
did. Assert against the **materialised install tree**. Cheapest path first: spike
whether the plugin format offers an exclusion declaration at all, before
considering a subdirectory plugin root, which would move every skill and agent
file and forfeit the zero-files-moved property this cycle's chunk ordering rests
on.

### Q-IMPL-MARKETPLACE-021: A local-path install copies the working tree verbatim, gitignored content included
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Install verification, the local-path mechanism
**Decision**: Record, as a property of the local-path **verification mechanism**,
that it copies the working tree as-is — including untracked and gitignored files
— so a future cycle verifying by local path knows its install cache can carry
local state. No change to the packaging, and no change to what a marketplace
user receives.
**Rationale**: The install cache produced by the Chunk 7 observation contains
`.sdd/telemetry.jsonl` with that cycle's 30 telemetry records, although `.sdd/`
is gitignored and holds zero tracked files; the cache has no `.git`, confirming a
plain directory copy rather than a clone or an archive. A GitHub-sourced install
clones and therefore carries neither untracked nor ignored files, so the property
is confined to the local-path mechanism and never reaches a user installing from
the marketplace. Informational: it changes no contract, but silently reusing a
local-path install without knowing it would be a way to leak local state into a
copy that looks like a clean install.

### Q-IMPL-MARKETPLACE-024: the bundled sweep is reached by a skill-directory-relative path
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Root resolution for skill-side invocations
**Decision**: The driver skill's drift-sweep invocations name the script as
`<skill-dir>/tools/gc.py` — skill-directory-relative, `<skill-dir>` defined in
the skill body as the directory holding its `SKILL.md` — and keep the explicit
`--root .`. The plugin-root environment variable is not used, per §No skill body
depends on the plugin-root variable. The telemetry tool's binary path is left
cwd-relative, so the REQ-PKG-MARKETPLACE-007 grep over telemetry invocations
still sees no path beginning with a skill or plugin directory.
**Impact**: the bundled sweep becomes reachable from an installed plugin rather
than byte-identical but dead; the acceptance criterion above measures
resolution, not only the copies' file properties.

### Q-IMPL-MARKETPLACE-026: the bundled sweep gets a provenance conditional, narrowing a passing criterion
**Status**: REVERTED 2026-09-21 by operator decision after the verify stage's
third red round (see Q-IMPL-MARKETPLACE-029) — the narrowing it recorded is withdrawn and REQ-PKG-MARKETPLACE-007's freeze reads in its original unamended form again — a freeze narrowed to admit a change that no longer exists protects nothing. The entry is kept as
the record of a decision that was made and then withdrawn; it is not deleted.
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Root resolution for skill-side invocations; §Acceptance Criteria, the REQ-PKG-MARKETPLACE-007 criteria
**Decision**: Bundle `tools/skill-lint.py` beside the bundled sweep as a regular
file (byte-identical, never a symlink, not a plugin component), and add one
conditional to the drift sweep: when the linter it resolves is a **sibling of the
running script** and that sibling directory is not the subject root's own
`tools/`, run the linter with its suite-specific contract rows off. Narrow
REQ-PKG-MARKETPLACE-007's source freeze accordingly — the telemetry tool's source
stays frozen unconditionally, the sweep's source is frozen apart from this
conditional — and keep the criterion rather than deleting it.
**Rationale**: Two alternatives were weighed and rejected. *Bundling the linter
alone* makes the consumer-repo sweep run and report ~40 spurious `[required]`
"file missing entirely" findings drawn from this repository's own contract rows —
a **misleading success**, which is worse than the clean failure (`exit 2`,
"linter missing") it would replace, because an operator cannot tell the spurious
rows from real ones. *Deferring* leaves the bundled sweep shipped and unusable
from the install this cycle publishes. The conditional is derived from paths at
run time — no flag, environment variable or config file — so this repository's own
`python3 tools/gc.py --root .` behaves exactly as before, measured by an identical
finding set against the pre-change script.
**Impact**: this amends a criterion the red round had already verified and
passed. The operator was shown that cost on 2026-09-21 and accepted it: a
criterion that is true but guards the wrong object is the failure mode this
cycle's measurement discipline exists to catch, so the honest move is to narrow
the criterion with the reason stated and add a criterion that measures what was
actually missing — a consumer-repository run. The freeze is narrowed, not
dropped: any further edit to either tool remains outside it.

### Q-IMPL-MARKETPLACE-027: the provenance conditional is keyed to the root swept, not to where the script lives
**Status**: REVERTED 2026-09-21 by operator decision after the verify stage's
third red round (see Q-IMPL-MARKETPLACE-029) — the re-keyed predicate went out with the conditional it re-keyed; keying on the root swept could not tell a consumer tree from this one by anything a consumer tree itself carries. The entry is kept as
the record of a decision that was made and then withdrawn; it is not deleted.
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Root resolution for skill-side invocations; §Acceptance Criteria, the REQ-PKG-MARKETPLACE-007 criteria
**Decision**: Replace the script-location predicate of Q-IMPL-MARKETPLACE-026
with a root predicate: the suite-specific contract rows are ON if and only if
`<root>/tools/skill-lint.py` is a file — the root being swept is the repository
that owns the rules. The old helper is removed rather than kept dead.
**Rationale**: the original predicate asked "was the linter resolved as a sibling
of the running script, in a directory that is not the subject root's `tools/`?"
That is true whenever the **bundled** copy sweeps **this** repository — precisely
the invocation the driver skill documents — so this repository's own REQUIRED and
version-gate rows were silently disabled by its own documented command. Measured
on a clean clone with one skill's version-gate paragraph broken: the root script
reported `FAIL: 1 finding` while the bundled copy on the same `--root` reported
`OK: 9 sweeps clean`. Keying on the root makes the two agree by construction,
because ownership of the rules is a property of the corpus being swept, not of
the file system location of the interpreter's argv[0]. It is also strictly
simpler — one `is_file()` test, still derived at run time, still no flag,
environment variable or config.
**Impact**: the narrowing REQ-PKG-MARKETPLACE-007 records stands, with its
condition corrected; the consumer-repository criterion is unaffected, since a
consumer tree carries no `tools/skill-lint.py` and is still swept with the
suite-specific rows off.

### Q-IMPL-MARKETPLACE-028: bundled-copy byte identity is a linter rule, not a seventh hook
**Status**: REVERTED 2026-09-21 by operator decision after the verify stage's
third red round (see Q-IMPL-MARKETPLACE-029) — the `bundled-drift` rule and its `--self-test` fixture are removed with the extension; bundled-copy identity is verified once per cycle again, as §Tools describes. The entry is kept as
the record of a decision that was made and then withdrawn; it is not deleted.
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Tools: root stays, the skill-runnable set is duplicated into the driver skill; §Acceptance Criteria, the REQ-PKG-MARKETPLACE-006 criteria
**Decision**: Add a `bundled-drift` rule to the skill linter. It derives its
population at run time — every `skills/*/tools/*.py` paired with the
repository-root file of the same basename — and raises one blocking finding per
pair that differs byte-for-byte, has no root source, or is a symlink. A
`--self-test` fixture seeds all four shapes and pins which of them must speak.
[Superseded 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-005: the directory this
decision's derivation would have derived over, the driver skill's own `tools/`
subdirectory, was removed on that date. The Decision text above is preserved
verbatim because this entry is **REVERTED** and is kept as the record of a
decision that was made and then withdrawn — a narrative record, not an
assertion about the present tree — so it takes the class (B) shape rather than
an in-place correction. This is the third stated exemption to the residual glob
grep of §Consumer-Geometry Acceptance Criteria.]
**Rationale**: byte identity was asserted once, by a criterion, and enforced by
nothing standing: on a clean clone, appending to a root tool left both quality
gates exiting 0 while `cmp` reported the bundled copy had drifted. A seventh
pre-commit hook would enforce it but would reopen REQ-PC-MARKETPLACE-006's
closed six-hook set; the linter is already a hook, so a rule there is enforced
on every commit at no new hook cost. The symlink clause is not redundant with
`cmp`: a link compares equal while resolving its run-time paths from the source
directory.
**Impact**: the population is derived, never pinned, so the rule and the
REQ-PKG-MARKETPLACE-006 criterion both extend themselves when a further tool is
bundled — which is what Q-IMPL-MARKETPLACE-022's measurement discipline requires
of both.

### Q-IMPL-MARKETPLACE-029: the consumer-repository extension is reverted whole
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Tools: root stays, the skill-runnable set is duplicated into the driver skill; §Root resolution for skill-side invocations
**Decision**: Revert the consumer-repository extension in full — delete the
bundled `skills/orchestrate/tools/skill-lint.py` (that directory was itself
removed on 2026-09-21 under REQ-PKG-CONSUMERGEOMETRY-005; the instruction stands
as the record of what this Q-IMPL decided), restore `tools/gc.py` to its
rename-chunk-close content (the provenance predicate and its helper are removed,
not left dead), remove the linter's `bundled-drift` rule and its `--self-test`
fixture, and restore REQ-PKG-MARKETPLACE-007's freeze criterion to its original
unamended wording. The three Q-IMPL entries the extension produced
(Q-IMPL-MARKETPLACE-026, -027, -028) are kept and marked REVERTED rather than
deleted. The run-time derivation of the bundled population is kept everywhere it
was introduced: deriving that set is correct practice regardless of its size, and
the set is simply two again.
**Rationale**: the provenance predicate failed twice, in opposite directions.
Keyed to the running script's location it disabled this repository's own REQUIRED
and version-gate rows under the very invocation the driver skill documents; keyed
to the root being swept it cannot distinguish a consumer tree from this one by
anything a consumer tree carries, so the third red round found it wrong again.
What the predicate actually needs is a marker of the repository that owns the
suite rules — an owning-repository declaration the swept corpus carries — and
that is a design question, not a patch. The operator chose to revert and to take
the question, together with what an installed plugin needs of `docs/`, into a
later cycle measured against a real install rather than a manifest. The cycle's
own deliverables — the rename, the commit gate, the agents, the manifests and the
project docs — are untouched by this reversal and were verified 37/37 twice.
**Impact**: the bundled sweep resolves and runs correctly in **this** repository,
where `<root>/tools/skill-lint.py` exists and both copies of the sweep produce
identical findings. In a consumer repository with no `tools/` directory it exits
2 with `error: linter missing`. [Amended 2026-09-21 — see §Tools: resolution is
**sibling-first**, so post-move this repository's gate resolves the linter beside
the sweep inside `plugins/sdd/tools/`; the limitation survives only for a
consumer tree carrying neither a sibling linter nor `<root>/tools/skill-lint.py`.]
That is the honest, documented limitation this reversal restores; it is recorded as a Minor in the cycle's verification report
with its reproduce command, and carried forward as a Next Step.

## Placement (superseded 2026-09-21)

[Changed 2026-09-21: `"source": "./"` and the no-`plugins/` clause of
REQ-PKG-MARKETPLACE-002 are superseded.] The shipped suite now lives at
`plugins/sdd/` and the plugin entry's `source` names that subdirectory, so
`docs/` is outside the install rather than copied-but-inert. The contract is
stated once, in `two-root-linter.md` §1 and §2; it is not restated here. The
**single-plugin** decision of REQ-PKG-MARKETPLACE-002 — one umbrella plugin,
because the driver dispatches its sibling skills by name — is unchanged and
still binding; only the placement changes. The exclusions of
REQ-PKG-MARKETPLACE-004 and -005 remain exclusions from the component list, and
after the move `docs/` is additionally outside the install.

## Consumer-Geometry Amendment (2026-09-21, REQ-PKG-CONSUMERGEOMETRY-005, -001)

This amendment removes the bundled tool directory this spec's §Tools introduced,
and corrects every record the removal falsifies — including three checklist items
in this file's own §Acceptance Criteria. The design for the rest of the
`consumer-geometry` delta lives in `two-root-linter.md` §Consumer-Geometry
Amendment; this section is only the removal and its corrections.

**Line numbers cited in this delta, reconciled once.**
REQ-PKG-CONSUMERGEOMETRY-005 cites this file at `:364`, `:365` and `:565`, and
REQ-PKG-CONSUMERGEOMETRY-001 at `:366`, all measured before this amendment was
appended. Appending it added two lines to the frontmatter's `requires:` list, so
every citation has shifted by **+2**: the vacuous item is now `:366`, the false
item `:367`, the unpinned freeze item `:368`, and the Q-IMPL-MARKETPLACE-029
sentence `:567`. **The content, not the number, identifies each site** — each is
stated below against a quoted string so it stays decidable after any further
shift.

### The removal (REQ-PKG-CONSUMERGEOMETRY-005)

`plugins/sdd/skills/orchestrate/tools/` is **removed**. It holds `gc.py` and
`telemetry.py`, each byte-identical to its `plugins/sdd/tools/` counterpart, and
**no invocation reaches it that works**:

- Running the bundled `gc.py` directly exits on its linter-missing path —
  `error: linter missing — expected <corpus>/tools/skill-lint.py` — in every
  geometry this repository or a consumer repository can be in, **because the
  fallback path exists in neither**. `lint_path()`'s sibling-first candidate looks
  for `skill-lint.py` next to `gc.py`, and that directory holds none; its second
  candidate, `<corpus>/tools/skill-lint.py`, was deleted here by the packaging
  move and never exists in a consumer tree. The claim is deliberately qualified:
  a consumer who happened to vendor their own `tools/skill-lint.py` would falsify
  an unqualified one.
- The six bare `python3 tools/telemetry.py` sites in `orchestrate` resolve
  **cwd-relative**, to `<corpus>/tools/`, never to the skill directory.
- Outside `docs/`, the string `orchestrate/tools` appears exactly once, at the
  shipped `plugins/sdd/skills/orchestrate/references/drift-sweep.md:36`, and there
  it cites the directory's **existence**, not an invocation.

REQ-PKG-MARKETPLACE-006's duplication clause is already amended to permit this
(its `[Updated: 2026-09-21b]` note). The removal lands **after** that amendment,
never before — the second of the plan-ordering constraints recorded in
`docs/requirements/index.md`.

Removal falsifies every record naming the directory.
**REQ-PKG-CONSUMERGEOMETRY-005's table is the comparand**, and the file set for
every criterion below is read from that table at run time rather than from a list
copied into a check. No count is written down anywhere: two earlier drafts of the
requirement stated counts and both were wrong.

### The three disposition classes

- **(A) In place — live, shipped and regenerated artifacts.** They describe the
  present, so they are made true. **Two class (A) sites sit inside a Q-IMPL
  record**, and "make true in place" is under-specified there:
  `marketplace-packaging.md:567` is inside Q-IMPL-MARKETPLACE-029's **Decision**
  text and `pre-commit.md:277` inside Q-IMPL-MARKETPLACE-019's **Context**.
  Rewriting a recorded decision to describe a later world is precisely the hazard
  the class (B) policy exists to prevent, so the rule for these two is narrower
  than for live prose: **a Q-IMPL Decision or Context sentence is made true by
  re-tensing it and appending an inline dated clause, never by changing what was
  decided or what it was decided against.** Concretely —

  - `marketplace-packaging.md:567`, today *"delete the bundled
    `skills/orchestrate/tools/skill-lint.py`, restore `tools/gc.py` to its
    rename-chunk-close content"*, becomes *"delete the bundled
    `skills/orchestrate/tools/skill-lint.py`* **(that directory was itself
    removed on 2026-09-21 under REQ-PKG-CONSUMERGEOMETRY-005; the instruction
    stands as the record of what this Q-IMPL decided)** *, restore …"* — the
    decision text is untouched, the clause says only that its object is gone.
  - `pre-commit.md:277`, today asserting that the two bundled paths *"do not
    exist at the rename-chunk-close sha"* and are created by the packaging
    chunk, keeps that sentence and gains the same inline dated clause recording
    that the directory was removed on 2026-09-21, so the `--name-only` window's
    bundled-tool half now has an empty population.

  **The escape hatch is stated rather than implied**: if an implementer finds a
  site where re-tensing plus a dated clause cannot be done without altering what
  was decided, that site is handled as class (B) — original preserved, dated note
  appended beneath — and the departure is recorded as a deviation. Silently
  rewriting the decision is not an option in either direction. The shipped
  `plugins/sdd/skills/orchestrate/references/drift-sweep.md:36` is class A **and
  is a plugin file**, so its correction sits in a different write scope from every
  docs record; the plan stage must not size it as docs-only.
- **(B) Appended dated note — closed-cycle prose records.**
  `.pre-commit-config.yaml` excludes `docs/ws/` from every automated rewrite for a
  stated reason — *"a rewrite makes the record disagree with the commits it
  describes"*. The original sentence stays exactly as that cycle wrote it and a
  `[Superseded 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-005: the bundled copy was
  removed; this observation was true at <that cycle's sha>]` note is appended
  beneath it, within three lines of the sentence it supersedes.
- **(C) In place, as data — traceability rows.** A row in a machine-regenerated
  table cannot carry an appended prose note and survive regeneration, and the
  aggregate is regenerated **from** the per-workstream file, so correcting the
  aggregate alone is undone at the next regeneration. The per-workstream source is
  corrected **first**. Class C is the one place a `docs/ws/` file is edited in
  place; the exclusion's rationale protects a *narrative* record, and a
  traceability row is an index, not a narrative.

### The shape every string criterion in this delta takes, and why

**A criterion about a file must not be decidable by prose the cycle itself writes
into that file.** Stating it as a bare file-wide grep fails that test twice over:
the amendments below must *cite* `skills/orchestrate/tools` in order to say which
sentences to correct, and a citation inside a Markdown table cell cannot be
fenced. So every string criterion in this delta is stated in **two parts**:

- **Primary — by named quoted sentence.** For each site to be corrected, the
  criterion quotes the pre-amendment sentence and asserts it no longer asserts the
  directory's existence. This half is decidable no matter what prose any later
  cycle adds, and it is what actually catches a skipped correction.
  **Matching is whitespace-normalised**, because every quoted sentence in this
  delta spans a line break in its source file and none is greppable as a literal:
  the target file and the quoted sentence are each passed through
  `tr '\n' ' '` and had runs of whitespace collapsed to one space before the
  substring test (`python3 -c "import re,sys; ..."` or
  `tr '\n' ' ' | tr -s ' ' | grep -F`). Two spans that a naive `grep -F` would
  miss, named so the normalisation is not left theoretical:
  `two-root-linter.md` §8's *"the copy bundled under `skills/orchestrate/tools/`
  … would then run"* crosses `:363-366`, and Q-IMPL-MARKETPLACE-029's *"delete
  the bundled `skills/orchestrate/tools/skill-lint.py`"* crosses
  `marketplace-packaging.md:566-567`. Where a shorter single-line anchor exists
  it may be used instead, provided it is unique in the file — the requirement is
  mechanical decidability, not a particular spelling.
- **Secondary — a residual grep with two stated exemptions**: a fenced code block,
  and the file's own `## Consumer-Geometry Amendment` section. The second
  exemption is the same shape REQ-PKG-CONSUMERGEOMETRY-005 itself grants
  `docs/ws/consumer-geometry/kickoff.md` — this cycle's own instruction text,
  naming the directory in order to retire it, is not a falsified record. The
  exemption is **bounded**: within an amendment section every occurrence must be a
  **citation of a site to be corrected**, never an assertion that the directory
  exists or is required. A live claim reintroduced there is a defect the primary
  half does not catch and a reviewer must.

This shape is adopted because the bare-grep form is this cycle's signature defect
— a criterion whose state is decided by the very prose written to satisfy it —
and fixing the instances without fixing the shape would leave the next amendment
free to reintroduce it.

Two files in the table are **excluded** and the exclusion is stated rather than
left as an unexplained grep failure: `docs/ws/consumer-geometry/kickoff.md` (this
cycle's own kickoff, naming the directory as the question to decide — not a
falsified record) and the two RS-PACKAGING-001 research records (historical
records of a measurement, not assertions about the present tree).

### The three checklist items in this file that the removal or the delta falsifies

Named here rather than left to a later reader, with the requirement and
acceptance each lands under, so the plan stage can size them separately:

| Item | What happens to it | Landing requirement |
|---|---|---|
| `marketplace-packaging.md:364`, now `:366` — derives the bundled population from the glob `skills/*/tools/*.py` and asserts `cmp` exit 0 / `test ! -L` per derived pair | after the removal the glob is **empty**, so the item passes **vacuously** — a checklist item that checks nothing while reading as green. Class B vacuity newly introduced *into a gate* by this cycle's own removal, which is the exact defect class this cycle exists to close. **Clause excised, item survives** — the deriving clause goes, not the item: its `git log --follow` and two-sided loss-check clauses are REQ-PKG-MARKETPLACE-006's surviving half (`[Updated: 2026-09-21b]`), and retiring the item whole would delete the only live pin for them. Not left to pass over the empty set either | REQ-PKG-CONSUMERGEOMETRY-005 acceptance 5 |
| `marketplace-packaging.md:365`, now `:367` — asserts at least one drift-sweep invocation under the skills tree resolves to the **bundled** copy and that the file it names exists | goes **false**, not vacuous — the safer of the two failures and the one a gate surfaces. **Retired** with the same edit | REQ-PKG-CONSUMERGEOMETRY-005 acceptance 5 |
| `marketplace-packaging.md:366`, now `:368` — REQ-PKG-MARKETPLACE-007's source freeze, asserted by content identity against the **working tree**, with an accepted alternative naming `HEAD` | neither vacuous nor false: **unpinned**. Both spellings leave the right endpoint open, so once row 4 of the REQ-PKG-CONSUMERGEOMETRY-001 enumeration and the `AGG_FIX` correction edit `plugins/sdd/tools/gc.py`, the item turns red at the next gate — not because the freeze was violated but because it is evaluated outside its own window. **Repinned** to the packaging cycle's end sha `0bdb076`: `git show 3ddfdb3:tools/<tool> \| cmp - <(git show 0bdb076:plugins/sdd/tools/<tool>)`, or equivalently the blob-sha equality | REQ-PKG-CONSUMERGEOMETRY-001 acceptance 5 |

The freeze-item repin is asserted **on that named item** and never as a file-wide
grep: `HEAD` occurs in this file in unrelated contexts, and "the working tree" has
no grep spelling at all. That is the same defect
REQ-PKG-MARKETPLACE-007's own `[Updated: 2026-09-21]` note corrects on the
requirement side; leaving its spec-side twin unpinned would reproduce it one
artifact away.

`marketplace-packaging.md:565`, now `:567` (inside Q-IMPL-MARKETPLACE-029's decision text,
naming the bundled `skills/orchestrate/tools/skill-lint.py`) is a **class A**
correction under REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2 — made true in place,
not retired, since that Q-IMPL's decision about the reverted consumer-repository
extension is otherwise unaffected.

### The dead REQ-PKG-MARKETPLACE-007 comparand travels with this correction

`git diff 3ddfdb3 HEAD -- tools/gc.py tools/telemetry.py` — the un-re-runnable
form that requirement's `[Updated: 2026-09-21]` note restates — is re-derived
verbatim in three further places, and nothing else in this delta binds them:
the **REQ-PKG-MARKETPLACE-007 row of `docs/requirements/traceability.md`** and
its per-workstream source `docs/ws/marketplace/traceability.md:57` (both class C,
corrected in place to the pinned blob-sha form, **the source first**), and
`docs/ws/marketplace/verification.md:59,102,280,457,458` (class B, one appended
note covering the five). Note `docs/ws/marketplace/traceability.md:56` is the
REQ-PKG-MARKETPLACE-006 row carrying the bundled-path string and `:57` is the
REQ-PKG-MARKETPLACE-007 row carrying the dead comparand — two different rows, two
different corrections.

**The aggregate's line numbers are cited by requirement id, not by number.**
REQ-PKG-CONSUMERGEOMETRY-005 cites `docs/requirements/traceability.md:317` and
`:318`; the aggregate was regenerated at `71998e4` (six new `consumer-geometry`
rows), so the REQ-PKG-MARKETPLACE-006 row is now `:323` and the
REQ-PKG-MARKETPLACE-007 row `:324`. **Both numbers can move again before the
implement stage**, because the aggregate is regenerated by the orchestrator from
the per-workstream files whenever any workstream's rows change, and that
regeneration is outside every stage's write scope. So the two rows are identified
**by their requirement id** in every criterion below, and the numbers are given
once, here, as a reading aid only. The per-workstream source's `:56`/`:57` are
stable — that file is hand-owned by the `marketplace` workstream and nothing
regenerates it.

**What the REQ-PKG-MARKETPLACE-006 rows' Evidence cell says after the correction
— specified, not left to the implementer.** For the -007 rows the replacement is
stated exactly (the pinned blob-sha form); the -006 rows need the same treatment
or the two sides of the regeneration can disagree. Today that cell names
`skills/orchestrate/tools/gc.py` and `skills/orchestrate/tools/telemetry.py` as
the two duplicated copies the `cmp` / `test ! -L` evidence was gathered over.
**The replacement keeps the historical evidence and dates its retirement**, in
one cell, in this shape:

> `plugins/sdd/tools/gc.py`, `plugins/sdd/tools/telemetry.py` (bundled copies
> under `skills/orchestrate/tools/` removed 2026-09-21,
> REQ-PKG-CONSUMERGEOMETRY-005; duplication evidence historical)

Three properties are why it is worded that way: it names paths that **resolve
today**, so the row is not an index into nothing; it does **not** claim the
duplication still holds, which is what removal falsified; and it carries the
authorising id, so a reader who meets the row knows which cycle retired it
without opening a verification report. The parenthetical is the **only**
permitted departure from naming live paths, and it must read identically in the
per-workstream source and in the aggregate — the source is edited first and the
aggregate's copy is whatever regeneration produces from it, which is what
acceptance 4's regenerate-and-diff proves.

### Consumer-unreachable strings corrected as the same family

Documentation-only edits, in scope under REQ-PKG-CONSUMERGEOMETRY-001's
permission:

- `gc.py`'s `AGG_FIX` string (`gc.py:175`), which tells the reader to run
  `tools/gc.py --fix traceability-aggregate` — a path that resolves for nobody
  but a pre-move in-repo operator.
- the six bare `python3 tools/telemetry.py` sites in `orchestrate`
  (`USAGE.md:159,439,572`; `references/telemetry.md:484,577,602`).

**The telemetry spelling, decided here, with its reconciliation and its residue.**
These six differ from `AGG_FIX` in kind: they are operator-facing invocations
inside a **shipped skill body**, so this spec's §Root resolution for skill-side
invocations owns them. **Decision: the script path becomes
`python3 plugins/sdd/tools/telemetry.py`, and the telemetry *file* path stays
absent — the tool keeps its cwd-relative `.sdd/telemetry.jsonl` default.**

- **Reconciliation with REQ-PKG-MARKETPLACE-007.** That requirement's
  prohibition is on the telemetry **file** path — "must **not** be given a
  plugin-relative path, because the telemetry file is written into and read from
  the operator's repository", and its acceptance is "no telemetry invocation in
  `skills/` passes a **file path** that begins with a skill or plugin directory".
  It says nothing about the **script** path, and the drift sweep's sibling
  requirement REQ-PKG-PACKAGING-009 already re-rooted the *sweep's* script path
  the same way. The decision therefore touches the script path only and leaves
  -007's actual binding untouched, which is asserted rather than assumed below.
- **Reconciliation with REQ-PKG-MARKETPLACE-008.** `plugins/sdd/` is a literal
  relative path, not the plugin-root environment variable, so the no-plugin-root
  rule is untouched. -008 is also why the consumer-resolving spelling is
  unavailable: the one mechanism that would resolve from an installed plugin is
  the variable -008 forbids in a skill body.
- **The residue, stated because a grep-satisfying string would hide it.**
  `plugins/sdd/tools/telemetry.py` resolves **in this repository, from the
  repository root** — which is what REQ-PKG-CONSUMERGEOMETRY-005 acceptance 7
  asks ("name a path that exists **in this repository** after the correction") —
  and resolves for **no consumer of the installed plugin**. This delta does not
  close the consumer half, and the corrected sites must not be read as though it
  did. In the one cycle about consumers, that is recorded as an OPEN rather than
  spelled over.

`OPEN:` **no spelling of a skill-body tool invocation resolves for a consumer of
the installed plugin.** A bare relative path resolves against the operator's cwd
(where no `tools/` exists); a `plugins/sdd/`-prefixed path resolves only in a tree
laid out like this repository; and the plugin-root variable, the only mechanism
that would resolve from an installed plugin, is forbidden in a skill body by
REQ-PKG-MARKETPLACE-008 on the ground that its expansion in skill-body text is
unattested. Blocking constraint: either an attested skill-body expansion for the
plugin root, or a requirement authorising some other mechanism — neither owned by
any artifact in this cycle. Recorded here rather than left implicit because the
decided spelling satisfies acceptance 7 while leaving the consumer case exactly
where it was.

### Consumer-Geometry Acceptance Criteria (removal half)

- [ ] **Gone.** `test ! -d plugins/sdd/skills/orchestrate/tools` succeeds, and a
  run-time grep for the string `orchestrate/tools` over the repository
  **excluding `docs/`** returns **zero** matches — where it returns one today, at
  the shipped `references/drift-sweep.md:36`. Removing the directory and leaving
  that citation makes this red (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 1).
- [ ] **Every class (A) and class (C) file is made true — primary half, by named
  sentence.** For each file REQ-PKG-CONSUMERGEOMETRY-005's table marks **A** or
  **C**, the file set read from that table at run time, the specific
  pre-amendment sentence is asserted to no longer assert the directory's
  existence. The three class (A) spec sentences are quoted here so the assertion
  has a target that no later prose can move: in `two-root-linter.md` §8, *"the
  copy bundled under `skills/orchestrate/tools/` (REQ-PKG-MARKETPLACE-006's
  duplicated-not-symlinked rule) would then run"*; in this file's
  Q-IMPL-MARKETPLACE-029, *"delete the bundled
  `skills/orchestrate/tools/skill-lint.py`"*; in `pre-commit.md`'s
  Q-IMPL-MARKETPLACE-019, *"`skills/orchestrate/tools/gc.py` and
  `skills/orchestrate/tools/telemetry.py` do not exist at the
  rename-chunk-close sha"*. **All three span line breaks in their source files,
  so the match is whitespace-normalised** as §The shape every string criterion in
  this delta takes specifies. Each is present and uncorrected today, which is what
  makes this red before the change; adding a row to the table without correcting
  its file makes it red after (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2).
- [ ] **Secondary half — residual grep, with both exemptions stated.** For each
  class (A)/(C) file, a run-time grep for `skills/orchestrate/tools` returns zero
  matches outside (i) a fenced code block and (ii) that file's own
  `## Consumer-Geometry Amendment` section, and every occurrence inside the
  exempted section is a **citation of a site to be corrected** rather than an
  assertion that the directory exists. §The shape every string criterion in this
  delta takes gives the reasoning; a live claim reintroduced inside an amendment
  section is what the bounded half exists to catch. **Class (B) files are
  deliberately outside this grep's scope** — they keep their original sentences by
  policy, and the preserved originals hold unfenced occurrences, so a
  whole-repository grep could never return zero while the policy was obeyed
  (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2).
- [ ] **Every class (B) record carries its note, and its original survives.** For
  each file the table marks **B**: (i) a `[Superseded 2026-09-21 —
  REQ-PKG-CONSUMERGEOMETRY-005` note appears within three lines of each falsified
  sentence, and (ii) the original sentences are **unchanged**, asserted by
  `git diff` over that file **across the correction commit alone** — never an
  open-ended diff against a later `HEAD`, which would measure whatever else
  touched the file — showing insertions only and zero deletions. A
  `trailing-whitespace` / `end-of-file-fixer` deletion in an otherwise
  insertion-only edit is a hook artefact: re-assert over the commit with those
  hook changes staged separately. Rewriting an original in place makes (ii) red;
  correcting the prose without the note makes (i) red — opposite directions, which
  is how the policy is enforced rather than stated
  (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 3).
- [ ] **The dead comparand is corrected on both sides of the regeneration.**
  `docs/ws/marketplace/traceability.md:57` and
  the **REQ-PKG-MARKETPLACE-007 row** of `docs/requirements/traceability.md`
  — located by its requirement id, never by line number, because the aggregate is
  orchestrator-regenerated and its numbering moves (§The dead comparand) — carry
  the pinned blob-sha form and no `3ddfdb3 HEAD` spelling. **The
  REQ-PKG-MARKETPLACE-006 rows** on both sides carry the Evidence replacement
  §The dead comparand specifies, character-for-character identical to each other.
  Regenerating the aggregate from the per-workstream file afterwards leaves it
  byte-identical, asserted by **running** the regeneration and diffing.
  Correcting only the aggregate makes this red at the next regeneration; letting
  the two -006 cells drift apart makes the diff non-empty, which is the same
  failure one row over (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 4).
- [ ] **Neither spec-checklist assertion survives — one by excision, one by
  retirement.** Stated in the two-part shape of §The shape every string criterion
  in this delta takes, because the amendment writes the glob into this very file
  and a file-wide grep would therefore be decided by this cycle's own prose.

  **Primary, by named site.** (i) The item now at `:366` no longer derives a
  bundled population: its first clause — "every file matching
  `skills/*/tools/*.py` paired with the **suite-root** file of the same basename
  … and for **each** derived pair `cmp` exits 0 and `test ! -L` succeeds" — is
  **excised**, and the item survives. This is a **clause-level excision, not a
  retirement**, exactly as `two-root-linter.md:522-523` is specified in §CG-9:
  the item's remaining clauses — `git log --follow` resolving every post-change
  `plugins/sdd/tools/*.py` to pre-change history, and the two-sided loss check
  whose sides are spelled separately across the move commit — are
  REQ-PKG-MARKETPLACE-006's **surviving half**, which its
  `[Updated: 2026-09-21b]` note preserves in terms ("no tool is lost from the
  suite's `tools/` directory, compared by identity rather than by name").
  Retiring the item whole would delete the only live pin for an Approved clause
  this cycle does not supersede. (ii) The item now at `:367` — asserting a
  drift-sweep invocation resolves to the bundled copy — is **retired whole**,
  because it rests entirely on the superseded duplication clause.

  **Secondary, residual.** A run-time grep of
  `docs/spec/marketplace-packaging.md` for the glob returns matches only inside a
  fenced code block, inside this file's own `## Consumer-Geometry Amendment`
  section, or at the Q-IMPL-MARKETPLACE-028 reverted-record line — with the same
  bound on the second: every occurrence inside the amendment must be a
  **citation of a site to be corrected**, never an assertion that a bundled
  population is derived. The amendment section's line number is **read at run
  time**, never written down, and a literal enumeration of matches is wrong the
  moment anything moves. **Zero is unreachable against a correct
  implementation**, because the amendment carries the glob after its own heading
  (a table cell, which cannot be fenced, among others); a zero target is
  discharged only by deleting the amendment's own citations, which is the
  outcome the exemption exists to prevent.
  [Updated: 2026-09-21c — the **third exemption** is added by
  REQ-PKG-CONSUMERGEOMETRY-005's implementation. Q-IMPL-MARKETPLACE-028's
  **Status** is `REVERTED 2026-09-21` and the entry is kept *"as the record of a
  decision that was made and then withdrawn"*; a reverted record is narrative,
  not an assertion about the present tree, so its Decision text is preserved
  verbatim under the class (B) rule and no correction reaches its glob
  occurrence. Listed here so the grep has a **stated** exemption rather than an
  unexplained failure, on the same footing as this cycle's own kickoff and the
  research records in REQ-PKG-CONSUMERGEOMETRY-005's disposition table.
  REQ-PKG-CONSUMERGEOMETRY-005 acceptance 5's own literal still reads "returns
  zero matches"; the matching requirements-side note is landed under that
  acceptance by Chunk 7, so requirement, spec and plan say one thing rather than
  three. §CG-4's rule for reinterpreting an Approved literal, applied to the
  literal this cycle is reinterpreting.]

  **Why both halves are stated separately:** excising (i) and retiring (ii) are
  different edits with different failure modes. Leaving (i)'s clause in place
  makes it pass **vacuously** after the removal — a checklist item that checks an
  empty set while reading as green — and retiring (i) instead of excising it
  destroys the surviving loss check. Doing either one alone fails this criterion
  (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 5).
- [ ] **The freeze item is repinned, asserted on the named item.**
  The freeze item's comparand names `0bdb076` as its right
  endpoint, in place of the working tree / `HEAD` it names today, and the
  equivalent accepted form is repinned with it. Editing `gc.py` under
  REQ-PKG-CONSUMERGEOMETRY-001's permission and leaving that item unpinned makes
  the next gate red, which is how this fails if it is skipped
  (REQ-PKG-CONSUMERGEOMETRY-001 acceptance 5).
- [ ] **No invocation regressed *by the removal*.** `python3
  plugins/sdd/tools/gc.py --report --root .` and the commit gate's hooks raise no
  new finding and exit with the same status as before the removal, since no
  working invocation referenced the bundled copy; a hook that breaks falsifies the
  reachability finding the removal rests on. Evaluated **across the removal commit
  alone**, never across the cycle. This command is **already nested** — the
  in-repo copy's `default_suite_root()` is `<repo>/plugins/sdd` — so there is no
  degraded default here to pin (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 6).
- [ ] **The corrected strings resolve, and -007's binding is untouched.**
  `AGG_FIX` and the six telemetry invocation sites name a path that exists in this
  repository after the correction, asserted by resolving each named path at run
  time from the repository root — a path that does not resolve fails this.
  **Separately**, the REQ-PKG-MARKETPLACE-007 acceptance the correction could
  break is re-run: no telemetry invocation under `plugins/sdd/skills/` passes a
  **file path** beginning with a skill or plugin directory, asserted by grep. Any
  repair that moves the script path by also giving the tool a plugin-relative
  `--file` argument makes that half red, which is the construction that
  distinguishes the decided spelling from the one -007 forbids
  (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 7; REQ-PKG-MARKETPLACE-007, unchanged).
- [ ] **The consumer residue is recorded, not closed.** The `OPEN:` above appears
  in this spec and names its blocking constraint. Deleting it while the six sites
  still resolve only in this repository makes the record claim a closure that did
  not happen — a reviewer check, not a tool one
  (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 7, residue).
