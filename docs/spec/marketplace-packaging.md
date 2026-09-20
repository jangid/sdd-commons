---
status: Approved
last_updated: 2026-09-21
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
---

# Marketplace and Plugin Packaging

## Overview

This repository becomes a Claude Code **marketplace** named `sdd-commons`
carrying exactly one umbrella **plugin** named `sdd`. The packaging is a
*manifest statement over the existing tree*: two new JSON files declare what
ships, and **no existing file moves**. That property is the whole design —
it is what lets the rename (`skill-namespace-rename.md`) land first as an
independently verifiable step without any reference being edited twice
(REQ-NAME-MARKETPLACE-007).

Two exclusions are deliberate statements rather than omissions: `docs/` stays
in the repository and is not a plugin component (REQ-PKG-MARKETPLACE-004), and
the three contributor tools stay out of the plugin (REQ-PKG-MARKETPLACE-005).
Both are expressed by **absence from an explicit component list**, which is why
the list is enumerated rather than wildcarded.

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
all.

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
file (`project-docs.md`, REQ-DOCS-MARKETPLACE-001).

**Why `"source": "./"` and one plugin, not a split or a subdirectory.** The
driver dispatches its sibling phase skills **by name**, not by path. A split
that places the driver and a phase skill in different plugins leaves a name
resolving to nothing at dispatch time — a silent runtime failure no linter can
catch. A `plugins/sdd/` subdirectory would additionally have to move `skills/`
and `tools/`, which would invalidate the linter's literal skill paths and its
own root resolution at the same moment the rename is being verified. `"./"`
moves zero files and keeps both steps separable.

### The component list and its derivation rule

The component list is **explicit**: every shipped skill directory and every
shipped agent file is named. It is not a wildcard, because the `docs/` and
contributor-tool exclusions are expressed by absence from it.

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

The system must not require `docs/` to be present in an installed plugin.
Every `docs/…` citation inside a skill body is a **bare relative path**, which
resolves against the operator's own project working directory — which is where
an installing user's own SDD corpus lives. The invariant to preserve is
therefore negative and mechanically checkable: **no `docs/…` citation in
`skills/` may be absolute, home-rooted, or rooted on a plugin path variable.**

### Tools: root stays, two are duplicated into the driver skill

`tools/` stays at the repository root, so that every existing `tools/…`
reference in `docs/` (a record of what a past cycle ran here) and every prose
reference keeps its spelling.

Two classes of tool, with different destinations:

| Class | Tools | Ships in plugin? | Why |
|---|---|---|---|
| **Runnable from a skill** | the drift sweep, the telemetry tool | yes — duplicated into the driver skill's own `tools/` subdirectory | a skill body tells the operator to run them |
| **Contributor-only** | the skill linter, the scope-check self-test, the evaluation tool | no | never invoked from a skill body; the linter's rules are keyed to *this* repository's skill set and its root is its own script location, so from an installed plugin it would lint the plugin's copy of itself and report a green that says nothing about the user's repository |

**Duplicated, not symlinked.** A plugin install may be materialised from a git
archive, which does not reliably preserve symlinks, so a symlink is a silent
broken-install mode. Each bundled copy must be a regular file byte-identical to
its repository-root original.

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
grows past two files or past one chunk, that reconsideration becomes due.

**Loss check by identity, not by name.** Because the rename changed every
tool's filename, a name-set comparison against git history would fail by
construction. The check is therefore: `git log --follow` resolves each
post-change `tools/*.py` to its pre-change history, and the count of
`tools/*.py` after is not less than before — both derived at run time.

### Root resolution for skill-side invocations

Every invocation of a bundled tool from a skill body must reach the
**operator's own repository** as its root, never the plugin's:

- **Drift sweep** — invoked with an explicit root argument naming the current
  directory. Without it the tool defaults to its own script location and would
  sweep the plugin's copy, returning a false green about the user's repository.
- **Telemetry tool** — continues to rely on its cwd-relative default file path
  and is **not** given a plugin-relative path, because the telemetry file is
  written into and read from the operator's repository.

Neither tool's source is edited to satisfy this. The packaging step makes **no**
behavioural and no source change to either tool; the only permitted source edit
to them in this cycle is the rename of their self-referential name strings,
which happens earlier, in the rename step (REQ-NAME-MARKETPLACE-003).

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
against a pinned number.

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

## Acceptance Criteria

Every criterion derives both sides at run time. No corpus-measured count is
written into a criterion as a literal. All commands run from the repository
root with any nested `.worktrees/` path excluded from tree walks.

- [ ] `python3 -c "import json;json.load(open('.claude-plugin/marketplace.json'))"` exits 0, and the parsed document's `name` equals `sdd-commons`, its `owner` is present, and its `plugins` list has exactly one entry whose `name` is `sdd` — all read from the parsed file (REQ-PKG-MARKETPLACE-001).
- [ ] The parsed plugin entry's `source` equals `./`; `.claude-plugin/plugin.json` parses and carries `name`, `description` and `version`; `test ! -d plugins` succeeds (REQ-PKG-MARKETPLACE-002).
- [ ] A script derives, at run time, the set of basenames in the manifest's `skills` list and the set of directories under `skills/` containing a `SKILL.md`, and asserts set equality; likewise the manifest's `agents` list against `*.md` files directly under `agents/`; and asserts no listed path starts with `docs/` (REQ-PKG-MARKETPLACE-003).
- [ ] `grep -rnE '(^|[^A-Za-z0-9._/-])(/|~/|\$\{?[A-Z_]*PLUGIN_ROOT)[A-Za-z0-9._/-]*docs/' --include='*.md' skills/` returns no match, and the manifest check above shows no `docs/` path (REQ-PKG-MARKETPLACE-004).
- [ ] A run-time grep over `skills/` for an invocation prefix (`python3 ` or `./`) of any of the three contributor tools returns zero matches, and none of the three appears in the manifest component list (REQ-PKG-MARKETPLACE-005).
- [ ] For each of the two bundled tools: `cmp` against the repository-root file exits 0 and `test ! -L` succeeds on the bundled copy. `git log --follow` resolves every post-change `tools/*.py` to pre-change history, and `ls tools/*.py | wc -l` after is not less than the same count taken at the cycle's entry commit — both sides derived by command (REQ-PKG-MARKETPLACE-006).
- [ ] Every drift-sweep invocation found in `skills/` by a run-time grep carries an explicit root argument; no telemetry invocation in `skills/` passes a file path beginning with a skill or plugin directory; `git diff <rename-chunk-close-sha> HEAD -- tools/<drift sweep> tools/<telemetry tool>` is empty (REQ-PKG-MARKETPLACE-007).
- [ ] A run-time grep for the plugin-root variable name over `skills/**/*.md` returns no match outside a fenced code block documenting its manifest-only scope (REQ-PKG-MARKETPLACE-008).
- [ ] `CONTRIBUTING.md` contains a paragraph stating that spec citations inside skills resolve in the repository, not in an installed plugin; the same `docs/spec/*.md` citation grep over `skills/` yields the same count before and after the packaging change (REQ-PKG-MARKETPLACE-009).
- [ ] The verification report records, as observations with their commands: the install command run, the namespaced skill names the session listed, and the name of the `references/*.md` file read from the installed copy (REQ-PKG-MARKETPLACE-010).
- [ ] The skill linter exits 0 and its `--self-test` passes after the packaging change; the drift sweep's report raises no finding absent from the cycle's entry sweep, compared against that sweep's recorded output.
