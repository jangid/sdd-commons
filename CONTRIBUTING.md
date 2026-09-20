# Contributing

This repository is the source of the `sdd` plugin, published through the
`sdd-commons` marketplace. It is also a working SDD repository: the contracts
the skills describe live in `docs/`, and the cycle that produced them is
recorded in `docs/ws/`.

## The naming boundary

Skills and agents ship under the plugin namespace: `sdd:orchestrate`,
`sdd:implement`, `sdd:chunk-verifier`. The directories are bare —
`skills/orchestrate/`, `agents/chunk-verifier.md` — because the plugin prefix
supplies the namespace.

Artifacts that predate the marketplace release keep the retired `sdd-` names:
closed-cycle plans, verifications and kickoffs under `docs/ws/`, research
findings under `docs/research/`, and the vendored corpus under
`docs/superpowers/`. That is deliberate — those documents record what a past
cycle actually shipped, under the names that cycle actually used, and rewriting
them would make the record disagree with the commits it describes. **New work
uses the namespaced names.** This one statement is the whole boundary; it is not
a migration table, and no dated marker is added in place.

### The symlink hazard

Before the marketplace release, skills were installed by symlinking each
`skills/sdd-*` directory into `~/.claude/skills/`. On the author's machine ten
such `~/.claude/skills/sdd-*` entries point at `skills/sdd-*` directories in
this repository. The rename removes those targets, so **when this branch merges,
an existing symlink-based install dangles.** Work done in a worktree defers the
break until the merge; it does not avoid it.

At merge, an operator with such an install takes one of two actions:

1. **Re-point** each symlink at the new directory name (`skills/sdd-research` →
   `skills/research`, and so on for the other nine); or
2. **Retire** the symlink install in favour of the plugin:
   `/plugin marketplace add jangid/sdd-commons` then
   `/plugin install sdd@sdd-commons`. This is the install path this cycle exists
   to provide, and the one this repository recommends.

## Where the contracts live

Skill bodies cite contract files under `docs/spec/` as reading references.
**Those citations resolve in this repository, not in an installed plugin.** A
skill never opens them at runtime, so an installed skill works without them; but
a reader who follows a citation out of an installed skill will not find the file
under the install directory. Read it here instead. The skill linter classifies an
unresolvable citation as a warning rather than a failure for exactly this
reason — a consumer repository is not assumed to carry this repository's layout.

## Pre-commit

Install the gate once per checkout:

```bash
pip install pre-commit      # or: brew install pre-commit
pre-commit install
```

Run it over everything before a first commit or after a large change:

```bash
pre-commit run --all-files
```

The gate runs the two whole-corpus sweeps (`python3 tools/gc.py --fast` and
`python3 tools/skill-lint.py`) plus upstream file-hygiene hooks. It is a runner,
not a source of policy — every rule it enforces is stated in a requirement, a
skill, or one of the two tools' own rule tables.

### The three heavier checks, run explicitly

Three self-tests stay **out** of the commit path: they are slow, their inputs
are frozen fixtures, and a fixture-driven proof does not change between commits
that do not touch the fixture. Run the matching one yourself when you touch its
tool or its fixture:

| When you touch | Run |
|---|---|
| `tools/scope-check-selftest.py` or its fixtures | `python3 tools/scope-check-selftest.py --self-test` |
| `tools/telemetry.py` or `tools/fixtures/` telemetry data | `python3 tools/telemetry.py --self-test` |
| `tools/eval.py` or its fixture | `python3 tools/eval.py --self-test` |

## Adding new content

These conventions are **carried forward verbatim** from `CLAUDE.md`
§Adding New Content, which remains their single source — if the two ever
disagree, `CLAUDE.md` is correct and this section is the stale copy.

### New skill

1. Create `skills/<name>/SKILL.md` with frontmatter and body
2. Test the skill by invoking it in a Claude Code session
3. Commit with: `feat(skills): add <name>`

### New agent

1. Create `agents/<name>.md` with frontmatter and body
2. Verify the agent can be loaded as a subagent type
3. Commit with: `feat(agents): add <name>`

### New tool

1. Create the script in `tools/`
2. Ensure it runs standalone
3. Commit with: `feat(tools): add <name>`

A new skill or agent must also be added to the component lists in
`.claude-plugin/marketplace.json` and to `README.md` §Components — the two are
compared as sets, so a component missing from either is a failure.
