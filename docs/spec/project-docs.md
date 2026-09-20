---
status: Approved
last_updated: 2026-09-21
requires:
  - REQ-DOCS-MARKETPLACE-001
  - REQ-DOCS-MARKETPLACE-002
  - REQ-DOCS-MARKETPLACE-003
  - REQ-DOCS-MARKETPLACE-004
  - REQ-DOCS-MARKETPLACE-005
---

# Project Documentation for Public Release

## Overview

The repository is about to be publicly installable and lacks the three documents
a public repository is read through: a licence, a contributing guide, and a
README that tells a stranger what this is and how to use it. The existing
`README.org` is structure-only — it describes the directory layout and has no
usage section — and is **dropped** rather than converted in place, matching the
marketplace convention that a repository's front door is `README.md`.

`CLAUDE.md` is in scope for the parts this cycle's other domains change: the
component names (`skill-namespace-rename.md`) and the agent frontmatter field
list (`harness-agents.md`).

Nothing here changes any skill's behaviour. These are the documents a human
reads before running anything.

## Design

### `LICENSE`

An MIT `LICENSE` at the repository root, with the correct copyright holder and
year, matching the licence of the author's `sui-ai-commons` marketplace. The
plugin manifest's `license` field names the same licence, so the two statements
cannot drift: the manifest value is the MIT identifier and the file's first line
identifies the MIT licence.

### `README.md`

The front door. Minimum contents, each an identifiable section:

1. **What this is** — the SDD workflow in a short paragraph.
2. **Install** — the two commands: adding the marketplace, then installing the
   plugin.
3. **Usage** — how an operator starts a full cycle through the driver, and how
   to invoke a single phase skill directly. This is the part `README.org` lacked
   and the reason the file is rewritten rather than converted.
4. **Components** — the shipped skills and agents under their **namespaced
   names** (`sdd:<name>`).
5. **Pointers** — to `CONTRIBUTING.md` and `LICENSE`.

**Two consistency contracts bind the README to the manifest**, both checked by
parsing rather than by string matching:

- the marketplace and plugin the install commands name must be the same ones
  `.claude-plugin/marketplace.json` declares;
- the component names the README lists must be **exactly** the manifest's
  component list, compared **as sets of mapped paths** — set equality, not
  containment. Containment would let a README that names three of the shipped
  components pass while the front door silently under-reports what the plugin
  installs, which is the failure this contract exists to catch. Equality in the
  other direction (a README name with no manifest entry) is already a failure by
  §The mapping rule.

**The mapping rule** (stated here so the check is mechanical rather than a
judgement call): a namespaced name `sdd:<x>` maps to the skill path `skills/<x>`
when a directory of that name containing a `SKILL.md` exists, and otherwise to
the agent path `agents/<x>.md`. The comparison is made between those mapped
paths and the manifest's listed paths. A README name mapping to neither an
existing skill directory nor an existing agent file is itself a failure — the
rule has no third branch and no silent fallthrough.

### `README.org` is deleted, visibly

`README.org` is deleted, not retained alongside `README.md`: two front doors
that disagree is worse than either alone. No remaining file in the live rename
scope may reference it **in running prose**.

**The sweep carries the same two-step skip order as the retired-prefix rule**
(`skill-namespace-rename.md` §The retired-prefix rule): occurrences inside
fenced code blocks and inside inline-backtick spans are skipped first, then an
explicit exception list. Without skip (1) the check fails by construction — the
documents that *specify* the deletion must name the retired filename to specify
it, and they name it in backticks.

**One bare occurrence is a documented exception**: the Implementation cell of
REQ-ORCH-021 in `docs/requirements/traceability.md`. That cell is a historical
record of what a past cycle actually shipped, under the filename that cycle
actually shipped. Retargeting it would make the record disagree with the commits
it describes — the same reasoning that excludes `docs/ws/`, `docs/research/` and
`docs/superpowers/` from the rename scope, applied to the one row inside a live
area that is a record rather than a description. The exception is named by path
in the checking script, not by a general allowlist, and it is the only one.

The deletion must be **visible in history** rather than disguised: `README.md`
is new content, not the old file renamed into place carrying its old body. The
check is that `git log --follow README.md` shows the two as separate history, or
that the deletion is otherwise visible in the commit.

### `CONTRIBUTING.md` — the four things this cycle owes it

`CONTRIBUTING.md` is the only place where four otherwise-scattered statements
land. Each is an identifiable section or paragraph:

| # | Statement | Owed to |
|---|---|---|
| 1 | The **naming boundary**: pre-marketplace artifacts keep the retired names, new work uses the namespaced form. It must also state the symlink hazard and the two operator actions at merge (re-point, or retire in favour of the plugin install). | `skill-namespace-rename.md` (REQ-NAME-MARKETPLACE-006, -010) |
| 2 | **Where the contracts live**: spec citations inside skills resolve in the repository, not in an installed plugin. | `marketplace-packaging.md` (REQ-PKG-MARKETPLACE-009) |
| 3 | **Pre-commit setup**, plus the three heavier checks a contributor runs explicitly, each with its command. | `pre-commit.md` (REQ-PC-MARKETPLACE-004) |
| 4 | **How to add a skill, an agent and a tool**, carried forward from `CLAUDE.md` §Adding New Content rather than re-invented. | this spec |

Item 4 is a **carry-forward, not a rewrite**: the conventions already exist and
have governed six cycles. Restating them in new words would create a second
source that drifts from the first.

Item 1 is why `CONTRIBUTING.md` sits on the retired-prefix rule's self-exemption
list: it must quote the retired form to explain the boundary.

### `CLAUDE.md`

Updated so that:

- every component it names uses the post-rename form;
- §Repository Structure reflects the marketplace layout, **including both
  manifest paths**;
- §Quality Checks names the renamed linter;
- §Agents documents exactly the five-field list of `harness-agents.md`.

**Unchanged in substance**: its description of the SDD phases, the driver, phase
detection, the cycle-identity rules and the v4 layout. This cycle renames and
packages those contracts; it does not alter them. A change to any of them is a
defect, not scope — which is why the criterion below is a *reviewer-checkable
diff*, not a free-text claim.

`CLAUDE.md` is **not** on the retired-prefix rule's self-exemption list: it is
prose about the system, not about the rule, and must reach zero bare occurrences
on its own. Where it must name a retired form (for example when describing the
historical corpus) it quotes it in backticks, which the rule skips.

## Acceptance Criteria

Both sides of every comparison are derived at run time; no count and no
component name is pinned as a literal in a check.

- [ ] `LICENSE` exists, its first line identifies the MIT licence, and it names the copyright holder; the `license` value parsed from `.claude-plugin/plugin.json` is the MIT identifier (REQ-DOCS-MARKETPLACE-001).
- [ ] `README.md` exists and contains a heading whose text names usage; the marketplace and plugin names in its install commands equal those parsed from `.claude-plugin/marketplace.json`; the set of README component names, mapped by §The mapping rule, **equals** the set of paths in the manifest's component list, and every README name maps to an existing skill directory or agent file (REQ-DOCS-MARKETPLACE-002).
- [ ] `test ! -e README.org` succeeds; a run-time grep for the retired README filename over the six live rename-scope areas returns zero matches after applying, in order, (1) the fenced-block and inline-backtick-span skip and (2) the single documented exception named in §`README.org` is deleted, visibly — both the skip and the exception path applied by the checking script, not pasted as a count; `git log --follow README.md` shows the deletion and the new file as separate history, or the deletion is visible in the commit (REQ-DOCS-MARKETPLACE-003).
- [ ] Each of the four `CONTRIBUTING.md` items is present as an identifiable section or paragraph, and the `CONTRIBUTING.md`-reading criteria of REQ-NAME-MARKETPLACE-006, REQ-NAME-MARKETPLACE-010, REQ-PKG-MARKETPLACE-009 and REQ-PC-MARKETPLACE-004 all pass (REQ-DOCS-MARKETPLACE-004).
- [ ] A run-time grep of `CLAUDE.md` for the retired prefix returns zero matches outside the skip set of REQ-NAME-MARKETPLACE-009 (fenced blocks and backtick spans); `CLAUDE.md` names both manifest paths; `git diff` of `CLAUDE.md` across the cycle shows no change to the phase-detection table, the cycle-identity rules or the v4 layout section beyond name substitution, confirmed by a reviewer against that diff (REQ-DOCS-MARKETPLACE-005).
- [ ] The field list in `CLAUDE.md` §Agents, parsed from the section, equals the five-field list of `harness-agents.md`; the section names `color` and names neither dropped field (REQ-DOCS-MARKETPLACE-005, REQ-AGENT-MARKETPLACE-003).
- [ ] The drift sweep and the skill linter both exit 0 after these documents land.
