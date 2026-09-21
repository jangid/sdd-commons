---
domain: DOCS
last_updated: 2026-09-21
status: Approved
research_refs: [RS-MARKETPLACE-001]
workstream: marketplace
---

# Requirements: Project Documentation for Public Release

## Overview

The repository is about to be publicly installable and currently lacks the three
documents a public repository is read through: a licence, a contributing guide,
and a README that tells a stranger what this is and how to use it. The existing
`README.org` is structure-only — it describes the directory layout and has no
usage section — and is dropped rather than converted in place, matching the
marketplace convention that a repository's front door is `README.md`.

`CLAUDE.md` is in scope here too, for the parts this cycle's other domains
change: the component names (NAME), and the agent frontmatter field list that
RS-MARKETPLACE-001 Q5 measured and partly refuted.

Nothing in this domain changes any skill's behaviour. These are the documents a
human reads before running anything.

## Requirements

### REQ-DOCS-MARKETPLACE-001: MIT `LICENSE`
The repository must carry an MIT `LICENSE` file at its root, with the correct
copyright holder and year, matching the licence of the author's `sui-ai-commons`
marketplace. The plugin manifest's licence field must name the same licence.
(see kickoff §Decided at DISCUSS)
**Acceptance**: `LICENSE` exists, its first line identifies the MIT licence, and
it names the copyright holder; the `license` value parsed from
`.claude-plugin/plugin.json` is the MIT identifier.
[Priority: must]

### REQ-DOCS-MARKETPLACE-002: A real `README.md` with a usage section
The repository must carry a `README.md` that gives, at minimum: what the SDD
workflow is in a short paragraph; the **install commands** for adding the
marketplace and installing the plugin; a **usage section** showing how an
operator starts a cycle and how to invoke a single phase skill directly; the list
of shipped components under their namespaced names; and a pointer to
`CONTRIBUTING.md` and `LICENSE`. The usage section is the part `README.org`
lacked and is the reason the file is rewritten rather than converted.
(see kickoff §Scope part 2, §Decided at DISCUSS)
**Acceptance**: `README.md` exists and contains a heading whose text names usage;
the install commands it shows name the same marketplace and plugin as
`.claude-plugin/marketplace.json`, compared by parsing both rather than by
matching a written-out string; every component name the README lists is present
in the manifest's component list, compared as sets derived at run time over
**mapped paths**, using this derivation: a namespaced name `sdd:<x>` maps to the
skill path `skills/<x>` when a directory of that name containing a `SKILL.md`
exists, and otherwise to the agent path `agents/<x>.md`. The comparison is made
between those mapped paths and the manifest's listed paths; a README name that
maps to neither an existing skill directory nor an existing agent file is itself
a failure.
[Priority: must]

### REQ-DOCS-MARKETPLACE-003: `README.org` is deleted and nothing points at it
`README.org` must be deleted, not retained alongside `README.md`, and no
remaining file in the live rename scope may reference it. Two front doors that
disagree is worse than either alone. (see kickoff §Decided at DISCUSS)
**Acceptance**: `test ! -e README.org`; a run-time grep for `README.org` over the
live rename scope of REQ-NAME-MARKETPLACE-004 returns zero matches; `git log
--follow README.md` shows the deletion and the new file as separate history, or
the deletion is otherwise visible in the commit — the file must not be silently
renamed into place with its old content.
[Priority: must]

### REQ-DOCS-MARKETPLACE-004: `CONTRIBUTING.md` carries the four things this cycle owes it
`CONTRIBUTING.md` must exist and must state, at minimum:

1. the naming boundary of REQ-NAME-MARKETPLACE-006 — pre-marketplace artifacts
   keep the retired names, new work uses the namespaced form;
2. where the contracts live (REQ-PKG-MARKETPLACE-009) — spec citations inside
   skills resolve in the repository, not in an installed plugin;
3. the pre-commit setup, and the three heavier checks a contributor runs
   explicitly (REQ-PC-MARKETPLACE-004);
4. how to add a skill, an agent and a tool, carried forward from `CLAUDE.md`
   §Adding New Content rather than re-invented.

(see RS-MARKETPLACE-001 Q1 Recommendation, Q4 §Self-reference hazard)
**Acceptance**: each of the four items is present as an identifiable section or
paragraph; the acceptance checks of REQ-NAME-MARKETPLACE-006,
REQ-PKG-MARKETPLACE-009 and REQ-PC-MARKETPLACE-004 — each of which reads
`CONTRIBUTING.md` — all pass.
[Priority: must]

### REQ-DOCS-MARKETPLACE-005: `CLAUDE.md` is updated to the shipped names and layout
`CLAUDE.md` must be updated so that every component it names uses the post-rename
form, its §Repository Structure reflects the marketplace layout including the two
manifest files, and its §Quality Checks names the renamed linter. Its
description of the SDD phases, the driver, phase detection and the v4 layout is
**unchanged in substance** — this cycle renames and packages those contracts, it
does not alter them. (see REQ-NAME-MARKETPLACE-004; kickoff §Out of scope)
**Acceptance**: a run-time grep of `CLAUDE.md` for the retired prefix returns
zero matches outside the exemption set of REQ-NAME-MARKETPLACE-009; the file
names both manifest paths; a reviewer-checkable diff shows no change to the
phase-detection table, the cycle-identity rules or the v4 layout section beyond
name substitution.
[Priority: must]
