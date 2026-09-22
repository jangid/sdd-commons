---
domain: DOCS
last_updated: 2026-09-22
status: Approved
research_refs: [RS-MARKETPLACE-001, RS-PACKAGING-002, RS-PACKAGING-003, RS-PIPELINEOBSERVABILITY-001]
workstream: marketplace, packaging, pipeline-observability
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

### REQ-DOCS-PACKAGING-001: `docs/spec/orchestration.md` names the project README by its live filename
`docs/spec/orchestration.md` §the project README paragraph (line 574 at
`a1ab5ba`) still names the project README by the retired front door's filename

```
README.org
```

in backticked prose. It passes the drift sweep only by the backtick skip and is
factually stale: that file was deleted by REQ-DOCS-MARKETPLACE-003 and the
repository's front door is `README.md`. The spelling must be corrected to the
live filename; nothing else in the paragraph changes, and the symlink-install
convention it documents is untouched by this repair. (see
`docs/ws/packaging/kickoff.md` §Carried repairs;
`docs/ws/marketplace/verification.md` §Issues Found)
**Acceptance**: a run-time grep of `docs/spec/orchestration.md` for the retired
front door's filename — the grep pattern is the name fenced above,
`README` followed by `.org` — returns zero matches, inside backticks or out; the
paragraph names `README.md`; the drift sweep — `python3 tools/gc.py --report`
before the move of REQ-PKG-PACKAGING-001, `python3 plugins/sdd/tools/gc.py
--report` after it — raises no new broken-link finding on the file.
[Priority: must]

### REQ-DOCS-PACKAGING-002: `CLAUDE.md` states one marker for this repository
`CLAUDE.md` contradicts itself about which layout marker this repository uses:
§Phase Detection states the repository migrated to marker `4` on 2026-09-17,
while §Multi-Workstream Layout (v4) states that marker `3` "remains fully
supported and is what this repo uses today". Both sentences are read by every
skill that consults `CLAUDE.md` for project context, and they cannot both be
true. The two passages must be reconciled to the marker `docs/.sdd-version`
actually carries, keeping the true statement that marker `3` remains
**supported** and removing the false statement that it is what this repository
uses. The substance of neither section otherwise changes. (see
`docs/ws/packaging/kickoff.md` §Carried repairs)
**Acceptance**: the marker named as this repository's own in `CLAUDE.md`
string-equals the trimmed contents of `docs/.sdd-version`, compared by reading
both at run time rather than against a written-out value; exactly one marker is
named as this repository's own anywhere in the file; the phase-detection table
and the v4 layout section are otherwise unchanged, shown by a reviewer-checkable
diff.
[Priority: must]

### REQ-DOCS-PACKAGING-003: The deferral-backlog screen's marker rule is item-scoped
The deferral-backlog screen's liveness rule examines line `L` and `L-1` and
nothing else, so an adjacent item's own bracketed dated marker can mark a
following item not-live — which is how the marketplace cycle's report scored a
live carried-to-a-later-cycle bullet as not live, its own date sitting in
parentheses the marker regex does not match. That is the block-level leakage
`docs/spec/requirements-artifacts.md` §`## Out of Scope` Discipline already
forbids in prose, unenforced by the mechanism. The rule must be **item-scoped**:
a marker suppresses only the item it belongs to, so a marker introducing or
closing one item never satisfies the rule for its neighbour. The phrase table
and the marker regex stay where they are and keep being read from the spec
rather than retyped, and the screen's standing qualification — it is a screen
over observed backlog vocabulary, not a proof of absence — is unchanged.
(see `docs/ws/packaging/kickoff.md` §Carried repairs;
`docs/ws/marketplace/verification.md` §Deferral-Backlog Screen)
**Acceptance**: a fixture of two adjacent items, the first carrying a bracketed
dated marker and the second carrying a backlog phrase with no marker of its own,
scores the second **live**; the same fixture scores it not-live under the
`L`/`L-1` rule, so the fixture distinguishes the two rules; re-running the
screen over `docs/ws/*/verification.md` reports its counts with the item-scoped
rule and no count is asserted that was not measured by that run.
[Priority: must]

### REQ-DOCS-PIPELINEOBSERVABILITY-001: `CLAUDE.md` states the verdict-split routing, the counted quantity, the `GROWTH:` line and the real plugin manifest path
`CLAUDE.md` is the project context every skill and every reviewer reads first,
and on 2026-09-22 it lags the landed harness: §Gate vocabulary says the stage
gate shows `iteration N of FIX_LOOP_MAX`, describes `loop-back-to-fix` as one
route with no verdict split, and names no `GROWTH:` line; §Repository
Structure lists the plugin manifest at the repository root, beside
`marketplace.json`, where no `plugin.json` exists — the plugin manifest is
`plugins/sdd/.claude-plugin/plugin.json`; only `.claude-plugin/marketplace.json`
sits at the root. `CLAUDE.md` must be updated so that
(1) §Gate vocabulary and §Cycle signals state the routing of
REQ-HARN-PIPELINEOBSERVABILITY-001 — `REJECT` → fix → re-review, counted by
`FIX_LOOP_MAX`; `APPROVE_WITH_FIXES` → fix → proceed **without re-review**
unless the operator opts in; (2) the quantity the gate counts against
`FIX_LOOP_MAX` is named as the run of **consecutive consumed `REJECT`s**
(REQ-HARN-001 as amended), and the phrase `iteration N of FIX_LOOP_MAX` no
longer appears; (3) the informational `GROWTH:` line of
REQ-HARN-PIPELINEOBSERVABILITY-002 is named in the gate order, after
`CONVERGENCE:` and before `TELEMETRY:`; and (4) §Repository Structure names
the plugin manifest at its real path and names no root-level `plugin.json`.
Every other section — the phase-detection table, cycle identity, the v4
layout — is unchanged in substance, as REQ-DOCS-MARKETPLACE-005 and
REQ-DOCS-PACKAGING-002 already require. (see
RS-PIPELINEOBSERVABILITY-001 §Gate observation 2026-09-22; review round 1 of
this stage, C2.) Leaves REQ-DOCS-MARKETPLACE-005 (both manifest paths named —
now at their real locations) and REQ-DOCS-PACKAGING-002 (one marker) consistent.
**Acceptance**: each of the following run-time greps over `CLAUDE.md` decides
one clause — `grep -c 'without re-review' CLAUDE.md` ≥ 1; `grep -c 'consecutive
consumed' CLAUDE.md` ≥ 1; `grep -Fc 'iteration N of FIX_LOOP_MAX' CLAUDE.md`
= 0; `grep -c 'GROWTH:' CLAUDE.md` ≥ 1 and the line naming it also names
`CONVERGENCE:` or `TELEMETRY:`; `grep -Fc 'plugins/sdd/.claude-plugin/plugin.json'
CLAUDE.md` ≥ 1; `grep -Ec '(^|[^/])\.claude-plugin/plugin\.json' CLAUDE.md`
= 0 (no root-level manifest path remains); and the two paths the file names
exist — `test -f plugins/sdd/.claude-plugin/plugin.json && test -f
.claude-plugin/marketplace.json && test ! -e .claude-plugin/plugin.json`; a
reviewer-checkable diff shows no change outside §Repository Structure, §Gate
vocabulary and §Cycle signals beyond these substitutions.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
2026-09-22)** over the retired `iteration N of FIX_LOOP_MAX` phrase and the
root-level manifest path — a listing grep over `docs/requirements docs/spec
plugins/sdd/skills plugins/sdd/agents`; hits in this requirement's own text and
in the index rows citing it are the statement itself and are excluded.
Command: `grep -rnF 'iteration N of FIX_LOOP_MAX' --exclude=project-docs.md docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
`docs/spec/project-docs.md` §Pipeline-Observability Amendment (the defect quote
and the `grep -Fc … = 0` check) and `docs/spec/harness-loop-control.md` (naming
the phrase as retired from `CLAUDE.md`) — reconciled, both name the phrase in
order to retire it; `plugins/sdd/skills/**`, `plugins/sdd/agents/**` — no hit
(the skill texts say `iteration N of MAX`, the label REQ-HARN-001 as amended
keeps); `CLAUDE.md` itself is outside the four trees and is this requirement's
target, retired by the `grep -Fc` zero-count witness above; for the manifest-path clause, `grep -rnE '(^|[^/])\.claude-plugin/plugin\.json'
docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents` hits
`docs/requirements/integration/packaging.md`, `docs/spec/two-root-linter.md`
and `docs/spec/project-docs.md` (the packaging cycle's own texts describing the
move — "`.claude-plugin/plugin.json` moves with the suite" — and the `test !
-e` witness this requirement shares) — reconciled;
`docs/spec/marketplace-packaging.md` §Manifests and its dated `"version":
"0.1.0"` decision (the root-level location as of the marketplace cycle) —
reconciled as that cycle's record, superseded by the packaging cycle's move;
whether that spec's section of record was re-dated is REQ-PKG-PACKAGING's
concern, not this clause's, which binds `CLAUDE.md` alone; no `plugins/sdd/**`
hit.
[Priority: must]
