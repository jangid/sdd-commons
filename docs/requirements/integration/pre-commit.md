---
domain: PC
last_updated: 2026-09-21
status: Approved
research_refs: [RS-MARKETPLACE-001]
workstream: marketplace
---

# Requirements: Pre-Commit Hooks

## Overview

The repository has no `.pre-commit-config.yaml`, a gap flagged during the
harness-p4 cycle and carried since. The two repository-maintenance tools that
already exist — the drift sweep and the skill linter — are exactly the checks a
commit gate wants, and the drift sweep already self-describes a `--fast` profile
as *the pre-commit profile*: lint plus cross-links plus orphan-id sweeps, with
no date walk and no history walk. This domain adds the configuration that wires
them up, plus four standard file-hygiene hooks.

The three heavier self-tests — the scope-check self-test, the telemetry tool's
self-test and the evaluation tool — stay **out** of the commit path. They are
slow and their inputs are frozen fixtures, so running them per commit costs
seconds on every commit to re-prove something that only changes when the fixture
or the tool changes. They remain available as explicit commands.

A pre-commit gate is a contributor convenience, not a verification layer: it must
never become a place where a rule lives that is not also stated in a requirement
or a skill.

## Requirements

### REQ-PC-MARKETPLACE-001: `.pre-commit-config.yaml` exists and is valid
The repository must carry a `.pre-commit-config.yaml` at its root, parseable as
YAML, declaring the hooks required by REQ-PC-MARKETPLACE-002 and
REQ-PC-MARKETPLACE-003 and no others. (see kickoff §Scope part 1)
**Acceptance**: `pre-commit validate-config .pre-commit-config.yaml` exits 0; the
set of hook ids parsed from the file equals the union of the two sets named by
REQ-PC-MARKETPLACE-002 and REQ-PC-MARKETPLACE-003, derived by parsing the file
rather than by comparing against a written-out list.
[Priority: must]

### REQ-PC-MARKETPLACE-002: The two repository tools run as local hooks
The configuration must run the drift sweep in its fast profile and the skill
linter as `repo: local`, `language: system` hooks invoking the repository's own
Python scripts. Both must run **once per commit over the repository**, not once
per changed file, because each is a whole-corpus sweep whose findings are
cross-file; a per-file invocation would both mis-report and multiply the cost.
A hook must fail the commit exactly when its tool exits non-zero.
(see RS-MARKETPLACE-001 Q2; `integration/drift-sweep.md` REQ-GC-HARNESSP2-001)
**Acceptance**: both hooks appear in the parsed config with `pass_filenames:
false` and `always_run: true`; `pre-commit run <each hook id> --all-files` exits
0 on the repository at the close of this cycle; introducing a deliberate lint
violation in a scratch copy makes the corresponding hook exit non-zero.
[Priority: must]

### REQ-PC-MARKETPLACE-003: Four standard file-hygiene hooks
The configuration must include the upstream `pre-commit-hooks` hooks
`trailing-whitespace`, `end-of-file-fixer`, `check-yaml` and `check-json`,
pinned to an explicit `rev`. `check-json` in particular guards the two new
manifests of REQ-PKG-MARKETPLACE-001 and REQ-PKG-MARKETPLACE-002, which are the
only files in the repository whose parseability the install depends on.
(see kickoff §Scope part 1)
**Acceptance**: the four hook ids are present in the parsed config under a
`pre-commit-hooks` repo entry carrying a non-empty `rev`; `pre-commit run
--all-files` exits 0 at the close of this cycle.
[Priority: must]

### REQ-PC-MARKETPLACE-004: The three heavier self-tests stay out of the commit path
The scope-check self-test, the telemetry tool's self-test and the evaluation tool
must **not** appear in `.pre-commit-config.yaml`. They are slow, their inputs are
frozen fixtures, and a fixture-driven proof does not change between commits that
do not touch the fixture. `CONTRIBUTING.md` must name them as the checks a
contributor runs explicitly when touching the corresponding tool or fixture, so
that excluding them from the gate does not make them invisible.
(see kickoff §Scope part 1)
**Acceptance**: a run-time grep of `.pre-commit-config.yaml` for each of the
three tool names returns zero matches; `CONTRIBUTING.md` names all three with the
command that runs them.
[Priority: must]

### REQ-PC-MARKETPLACE-005: The first full run is normalised inside this cycle
The whitespace and end-of-file hooks must be run over the **whole repository**
within this cycle and any resulting normalisation committed as part of it, so
that the first contributor to install the hooks does not face a mass rewrite of
files unrelated to their change. Any path the hooks must not normalise — a
fixture whose bytes are part of what it tests — must be named in an explicit
`exclude` pattern in the config, with the reason stated in a comment on that
pattern. (see `tools/fixtures/`; kickoff §Out of scope — frozen fixtures)
**Acceptance**: `pre-commit run --all-files` exits 0 **and** leaves the working
tree clean (`git status --porcelain` is empty) when run a second time
immediately after; the frozen telemetry fixtures are byte-identical to their
pre-cycle content, compared with `git diff` over that directory.
[Priority: must]

### REQ-PC-MARKETPLACE-006: The gate adds no rule of its own
No hook may enforce a rule that is not already stated in a requirement, a skill,
or one of the two tools' own rule tables. The pre-commit configuration is a
runner, not a source of policy: a rule that exists only in the gate is invisible
to every reader of the corpus and to every skill that must comply with it.
**Acceptance**: each hook in the config is either one of the two repository tools
(whose rules live in their own requirement domains) or one of the four upstream
hygiene hooks; no hook entry carries a custom `args` value that narrows or
extends a rule beyond what the tool's own requirements state.
[Priority: must]
