---
domain: PC
last_updated: 2026-09-22
status: Approved
research_refs: [RS-MARKETPLACE-001, RS-PACKAGING-002, RS-PACKAGING-003]
workstream: marketplace, packaging
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
REQ-PC-MARKETPLACE-003, one **self-test** hook per repository tool, and no
others — a closed set of **eight**. (see kickoff §Scope part 1)
**Acceptance**: `pre-commit validate-config .pre-commit-config.yaml` exits 0; the
set of hook ids parsed from the file equals the union of the set named by
REQ-PC-MARKETPLACE-003 and the set derived from the parsed `repo: local`
entries — each of the two repository tools of REQ-PC-MARKETPLACE-002 appearing
exactly twice, once in its sweep invocation and once with `--self-test`, the
pairing derived by parsing each local entry's `entry` value rather than by
comparing against a written-out list of ids.
[Updated: 2026-09-21 — the closed set grows from **six** to **eight**, the two
added entries being one `--self-test` hook per repository tool
(`skill-lint-self-test`, `drift-sweep-self-test`); the acceptance's derivation
is restated over the parsed local entries so both sides are still derived.
The requirement was written before this cycle discovered the need: the two
corpus sweeps exercise no two-root fixture geometry, so a wrong root binding
stays green in both, and `gc.py` embeds the linter, so a linter change can turn
`gc.py --self-test` red while every other gate passes. Both happened inside this
cycle, twice. The two self-test hooks are the control that catches that defect
class, and a control a contributor must remember to run is discipline, which is
what failed. Nothing is weakened: the set is still **closed** and still derived
by parsing, and the three heavier self-tests REQ-PC-MARKETPLACE-004 keeps out
stay out — the grep that requirement states was re-run after the addition and
is still zero for all three. REQ-PC-MARKETPLACE-006 is unaffected: each added
entry invokes one of the two repository tools, whose rules live in their own
requirement domains, and `--self-test` is a mode selector exactly as `--fast`
is, not an `args` value that narrows or extends a rule. Authorising context:
the implement-stage review of workstream `packaging`, round 2 finding S2-r2 and
the operator's round-3 decision to keep the hooks and amend the requirement
rather than delete them.]
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
three **script filenames** — `scope-check-selftest.py`, `telemetry.py`,
`eval.py` — returns zero matches; `CONTRIBUTING.md` names all three with the
command that runs them.
[Updated: 2026-09-21 — the criterion said "each of the three tool names" while
the prose above names them in short form ("the scope-check self-test, the
telemetry tool's self-test and the evaluation tool"), and the configuration's
explanatory comment spells those short forms. The criterion therefore read
0/0/0 under the filename interpretation and 1/1/1 under the short-form one —
two truth values for one criterion. The three grep strings are pinned above as
the **script filenames**, which is what "must not appear in the configuration"
has always meant: a hook that ran one of these tools would have to name its
script. A comment that discusses a tool is not a hook that runs it. No hook set
changes; only the criterion's ambiguity is removed. Authorising context: the
implement-stage review of workstream `packaging`, round 3 finding S3.]
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

### REQ-PC-PACKAGING-001: Both local hook entries take the `plugins/sdd/` prefix at the move
Both `repo: local` hook entries in `.pre-commit-config.yaml` — the drift sweep
and the skill linter — must have their `entry` script paths prefixed with
`plugins/sdd/` in the **same change** that performs the root move
(REQ-PKG-PACKAGING-001). Editing one and not the other leaves the commit gate
invoking a dead path for the unedited hook, which fails the gate for a reason
unrelated to the contributor's change. The hooks' other fields are unchanged:
each still runs once per commit over the repository (`pass_filenames: false`,
`always_run: true`) and still fails the commit exactly when its tool exits
non-zero, per REQ-PC-MARKETPLACE-002. The drift sweep's root argument is a
separate concern and is governed by REQ-PKG-PACKAGING-009 — the gate must sweep
the repository, not the suite. (see `docs/ws/packaging/kickoff.md` §Carried
repairs; RS-PACKAGING-003 §Scope)

The linter hook's entry stays **zero-argument** — `python3
plugins/sdd/tools/skill-lint.py`, the prefix being the only edit. That is
correct only because REQ-PKG-PACKAGING-002 requires the corpus root to default
to the **invocation cwd**; were it left defaulting to the script's own
location, the prefixed zero-argument entry would take `plugins/sdd` as its
corpus and the gate would stop sweeping `docs/spec/`, `docs/requirements/` and
the rest of the corpus, silently and with a green exit. The two requirements
are therefore one change, and the observation below is stated here as well as
there.
**Acceptance**: every `entry` value parsed from the two local hook entries names
a path that exists after the move, checked by `test -f` per parsed path rather
than against a written-out list; the linter hook's parsed `entry` carries no
positional root argument; running that parsed `entry` verbatim from the
repository root after the move sweeps a set that includes at least one
`docs/spec/` path, asserted by membership on the swept set derived at run time
rather than on the exit code; `pre-commit run --all-files` exits 0 on the
repository at the close of this cycle; reverting the prefix on either hook alone
makes that hook fail with a missing-file error.
[Priority: must]

### REQ-PC-PIPELINEOBSERVABILITY-001: `.claude/` is excluded from the hygiene hooks, with its reason on the pattern
`.pre-commit-config.yaml`'s `exclude` regex must gain the alternative
`\.claude/` with a comment stating the reason (editor settings, sandbox-denied
for writing, not corpus text). This is the exclusion REQ-PC-MARKETPLACE-005's
"named in an explicit `exclude` pattern … with the reason stated in a comment"
form requires for a path the hooks must not normalise: `.claude/settings.json`
is git-tracked, already ends in a newline, and `end-of-file-fixer` fails on
opening it for writing under the sandbox — recurring since the marketplace
cycle. (see RS-PIPELINEOBSERVABILITY-001 §Q6 gap 9, R13; Q-REQ-PO-K.) Leaves
REQ-PC-MARKETPLACE-001..-004 (hook set, exit contract), -005 (satisfied by
construction), -006 (no rule enforced that no requirement states — this is
that requirement) and REQ-PC-PACKAGING-001 consistent.
**Acceptance** (sandbox-independent, because the research's falsifier depends
on the sandbox write-deny list): (1) parsing the `exclude` value of
`.pre-commit-config.yaml` with Python `re` and matching it against
`.claude/settings.json` succeeds, and against `plugins/sdd/tools/gc.py` fails;
(2) `pre-commit run end-of-file-fixer --files .claude/settings.json` reports
the hook skipped with no files to check — it never opens the file — and exits
0; in a scratch copy of the config with the alternative removed, (1)'s first
match fails and (2) reports the file processed; (3) the comment on the
alternative states the reason; (4) `pre-commit run --all-files` exits 0 on this
branch.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
2026-09-22)** over the `\.claude/` exclusion — a listing grep over
`docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in
this requirement's own text and in the index rows citing it are the statement
itself and are excluded.
Command: `grep -rnE '\\.claude/|exclude (regex|pattern|value)' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
`docs/spec/pre-commit.md` §Pipeline-Observability Amendment (the alternative,
its comment, the scratch-copy check) — reconciled, carries this requirement;
`plugins/sdd/skills/**`, `plugins/sdd/agents/**` — no hit (the hook
configuration is repository-side, not plugin text);
`docs/requirements/integration/pre-commit.md` — the hit is this requirement;
REQ-PC-MARKETPLACE-005's "named in an explicit `exclude` pattern … with the
reason stated in a comment" (bold in the source, so outside this grep; found by
reading) — reconciled, it is the form this requirement instantiates.
[Priority: must]
