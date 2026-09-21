---
id: RS-MARKETPLACE-001
workstream: marketplace
status: Complete
date: 2026-09-21
last_updated: 2026-09-21
questions:
  - "Q1 — Does `docs/` ship inside the plugin, and does any skill's phase detection or any tool's default root break when `docs/` is absent from the installed plugin?"
  - "Q2 — Where do the tools live, and can `${CLAUDE_PLUGIN_ROOT}` absorb the `tools/sdd-*.py` path references (split executable versus prose)?"
  - "Q3 — One umbrella plugin or several, given that the ten skills cross-reference each other?"
  - "Q4 — Rename before, with, or after the marketplace move, measured by path-shaped versus prose blast radius and by which ordering leaves a verifiable intermediate state?"
  - "Q5 — Are the three agents dispatchable as a `subagent_type`, and what frontmatter contract and citation rule must the three files satisfy?"
budget: "One spike, <= 45 tool calls; desk research over this repository, the public AlphaFiTech/sui-ai-commons layout and the Claude Code plugin/marketplace documentation; read-only tool runs only."
---

# Research: Marketplace release — RS-MARKETPLACE-001

## Questions

Exactly the five the kickoff asks (`docs/ws/marketplace/kickoff.md` §Research
questions). Each is a **spike question**, decided here on measured evidence; the
§Decided list is restated unchanged below and is not re-litigated.

## Measurement protocol

Every count in this document was derived at run time by the command shown beside
it, executed from the worktree root
`/Users/pankaj/work/github/jangid/tools-skills-agents/.worktrees/marketplace`.

Two hazards, both handled explicitly:

1. **Nested checkout.** This worktree sits at `.worktrees/marketplace` inside the
   main checkout. Every repo-walking command below passes
   `--exclude-dir=.worktrees --exclude-dir=.git`, or targets named
   subdirectories, so nothing is double-counted. (Measured: this worktree's own
   top level contains no `.worktrees/` directory — `ls -1` shows
   `agents CLAUDE.md docs README.org skills tools` — so the exclusion is
   belt-and-braces here, but it is stated because a count taken from the *main*
   checkout without it would double.)
2. **Tool root.** No tool was copied anywhere. Both tools were read, not run
   against a relocated root, so no false green is possible.

A **measured correction to a carried-forward assumption** belongs here rather
than in one answer, because it changes two of them. The kickoff's tool-root
warning says "`tools/sdd-gc.py` and `tools/sdd-skill-lint.py` default their root
to their own repository". That is true of `sdd-skill-lint.py` and **false of
`sdd-gc.py`**:

```
sed -n '1840,1860p' tools/sdd-gc.py
grep -n 'args.root' tools/sdd-skill-lint.py
```

- `tools/sdd-gc.py` (lines 1840–1857): root is `--root` if given, otherwise
  `git rev-parse --show-toplevel` of the **current working directory**; it then
  hard-requires a git repository and a `docs/` directory, exiting `2` with
  `error: <root> has no docs/ directory` otherwise.
- `tools/sdd-skill-lint.py` (line 1084):
  `root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent`
  — i.e. the repository **containing the script**.

So gc follows the operator; lint follows itself. That asymmetry is the hinge of
Q1 and Q2.

## Q1 — Does `docs/` ship inside the plugin?

### Options

| Option | Installing user gains | Download cost | Install-breaking? |
|---|---|---|---|
| A. Ship all of `docs/` | Six cycles of worked SDD artifacts as reference | +3.1 MB, 130 files | No |
| B. Ship none of `docs/` | Nothing; smallest install | Baseline | No (see evidence) |
| C. Ship a curated subset (`docs/spec/` only) | The contracts the skills cite | +~0.8 MB | No |
| D. Keep `docs/` in the repository, exclude it from the plugin's component list | Repository readers get the evidence; installers do not | Baseline for the installer | No |

### Evidence

**Sizes** (`du -sh docs skills tools`; `find … -name '*.md' | wc -l`):

```
docs   3.1M   130 markdown files
skills 548K    25 markdown files
tools  668K
```

Shipping `docs/` multiplies the installed payload by roughly six.

**Phase detection does not break.** The deciding sub-question is answered by
reading how skills address `docs/`, not by assertion:

```
grep -rhoE 'docs/[A-Za-z0-9._/*-]+' --include='*.md' skills/ | wc -l        # 796
grep -rnE '(/[A-Za-z0-9._-]+)*/docs/|~/.*docs/|CLAUDE_PLUGIN_ROOT' --include='*.md' skills/ | wc -l   # 0
```

All **796** `docs/…` citations inside `skills/` are **bare relative paths**;
**zero** are absolute, home-rooted, or plugin-variable-rooted. Every
phase-detection read — `docs/.sdd-version`, `docs/requirements/index.md`,
`docs/spec/*.md`, `docs/ws/<id>/plan.md` — therefore resolves against the
**operator's project working directory**, which is exactly where the installing
user's own SDD corpus lives. A skill installed from a plugin with no `docs/`
looks for the *user's* `docs/`, finds it (or correctly reports a greenfield repo
and suggests `sdd-migrate`), and behaves identically. The `docs/` directory in
this repository is never an input to phase detection; it is this repository's own
project corpus.

**Tool default roots.** `sdd-gc.py` roots on the operator's cwd git toplevel and
requires *that* repository to have `docs/` — correct behaviour, unaffected by
whether the plugin carries `docs/`. `sdd-skill-lint.py` roots on its own script
location, so from an installed plugin it lints the *plugin's* `skills/`; it does
not need `docs/` at all, and its `docs/spec/<file>.md` backtick check is
explicitly downgraded to `warn` for this exact reason
(`resolve_backtick_path()`, lines 653–675):

> `docs/spec/` mentions only warn so the linter never assumes a consumer repo
> has this repo's layout.

and `check_template_drift()` (line 534) documents the same principle:

> a consumer repo linted via REPO_ROOT has no docs/spec/ — the F11 principle

The linter's authors already anticipated a `docs/`-less root. **No skill's phase
detection and no tool's root resolution breaks when `docs/` is absent from the
installed plugin.**

**The one real cost of omitting `docs/`** is dangling prose citations, measured:

```
grep -rhoE 'docs/spec/[A-Za-z0-9._-]+\.md' --include='*.md' skills/ | wc -l   # 150
grep -rlE  'docs/spec/[A-Za-z0-9._-]+\.md' --include='*.md' skills/ | wc -l   # 24
```

**150** `docs/spec/<file>.md` citations across **24** skill files ("See
`docs/spec/ws-layout.md`") point at a path the installing user does not have.
These are reading citations, not reads the skill performs — the skill never opens
them at runtime. They are a documentation-quality defect, warn-severity in the
linter, and not a broken install.

### Recommendation

**Option D** — `docs/` stays in the repository (it is the evidence that the
system works, and `sdd-gc.py` and this repo's own cycles depend on it) and is
**not** listed as a plugin component. Because the marketplace manifest supports
an explicit component list (see Q3 evidence), exclusion is a manifest statement,
not a file move: nothing under `docs/` is touched.

The 150 dangling `docs/spec/` citations are recorded as a **known, accepted
documentation gap** to be noted in `CONTRIBUTING.md` (the contracts live in the
repository, not the install) rather than rewritten — rewriting them is 150 edits
across 24 files for no runtime benefit, and the linter already classifies them
`warn`.

### Cost in files touched

**2** — `.claude-plugin/marketplace.json` (new, states the component list) and
`CONTRIBUTING.md` (new, one paragraph on where the contracts live). Zero files
under `docs/` or `skills/` change.

### Classification

**design-decision-for-requirements** (what ships is a product decision), with a
**mechanical** implementation (two new files).

### Confidence

**High.** The deciding claim is a negative over a complete enumeration, not a
sample: all 796 `docs/…` citations in `skills/` were matched and **0** were
absolute, home-rooted or plugin-variable-rooted, so there is no residual class
of citation that could break. The two tools' root resolution was read from
source (`sdd-gc.py` lines 1840–1857, `sdd-skill-lint.py` line 1084) rather than
inferred, and the linter's own comments state the `docs/`-less-root principle
explicitly. The one soft edge is the *cost* judgment — that 150 dangling
`docs/spec/` citations are acceptable — which is a taste call routed to
requirements, not a measurement.

## Q2 — Where do the tools live, and can `${CLAUDE_PLUGIN_ROOT}` absorb the path references?

### Measured reference count and its split

```
grep -rnoE 'tools/sdd-[a-z-]+\.py' --include='*.md' --include='*.yaml' --include='*.yml' \
     --include='*.py' --exclude-dir=.worktrees --exclude-dir=.git . | wc -l
```
→ **1206** total `tools/sdd-*.py` path references, repo-wide, `.worktrees`
excluded.

```
grep -rnoE '(python3 |\./)tools/sdd-[a-z-]+\.py' --include='*.md' --include='*.py' \
     --exclude-dir=.worktrees --exclude-dir=.git . | wc -l
```
→ **432 executable** references (the reference is preceded by `python3 ` or
`./`, i.e. it is a command someone runs).

**774 prose** references (1206 − 432) — a spec or a requirement naming the tool,
a fix string, a docstring.

Distribution of the 1206 by top-level area
(`… | sed 's|^\./||' | cut -d/ -f1 | sort | uniq -c`): `docs` 1015, `tools` 149,
`skills` 38, `CLAUDE.md` 4.

The split that decides the answer is the one **inside `skills/`**, because only a
skill runs from an installed plugin:

```
grep -rnoE 'tools/sdd-[a-z-]+\.py'               --include='*.md' skills/ | wc -l   # 38
grep -rnoE '(python3 |\./)tools/sdd-[a-z-]+\.py' --include='*.md' skills/ | wc -l   # 15
```

**38** references in `skills/`, of which **15 are executable** and **23 prose**,
spread over 8 files. The 15 executable ones live in exactly 5 files:

| File | Executable refs |
|---|---|
| `skills/sdd-orchestrate/USAGE.md` | 5 |
| `skills/sdd-orchestrate/references/drift-sweep.md` | 4 |
| `skills/sdd-orchestrate/references/telemetry.md` | 3 |
| `skills/sdd-orchestrate/SKILL.md` | 2 |
| `skills/sdd-verify/SKILL.md` | 1 |

Only `sdd-gc.py` and `sdd-telemetry.py` are ever invoked from a skill.
`sdd-skill-lint.py`, `sdd-scope-check-selftest.py` and `sdd-eval.py` are
**never** invoked from `skills/` — they are repository-maintenance tools.

### Is `${CLAUDE_PLUGIN_ROOT}` available in skill body text?

Evidence from the three marketplaces installed on this machine
(`~/.claude/plugins/marketplaces/`):

```
grep -rn 'CLAUDE_PLUGIN_ROOT' ~/.claude/plugins/marketplaces
```

Every occurrence that is an **actual use** (rather than documentation *about* the
variable) sits in a **manifest field** or a **command**:

- `plugins/learning-output-style/hooks/hooks.json`:
  `"command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks-handlers/session-start.sh\""`
- `manifest-reference.md` hook example: `"command": "bash ${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"`
- `manifest-reference.md` MCP example: `"args": ["${CLAUDE_PLUGIN_ROOT}/servers/github-mcp.js"]`
- `command-development` reference: *"Plugin **commands** have access to
  `${CLAUDE_PLUGIN_ROOT}`, an environment variable that resolves to the plugin's
  absolute path"*, used inside a command's bash block.

No installed skill body uses it. The contrasting, documented pattern for a skill
is **skill-directory-relative**: `anthropic-agent-skills`' `docx` skill cites its
bundled scripts as `scripts/office/soffice.py`, `scripts/merge_runs.py`,
`scripts/comment.py` — never through the variable:

```
grep -noE '(\$\{CLAUDE_PLUGIN_ROOT\}[^ `)"]*|scripts/[A-Za-z0-9._/-]+)' \
     ~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/docx/SKILL.md
```
→ 12 matches, **all** of the `scripts/…` form, **zero** of the variable form.

**Answer: `${CLAUDE_PLUGIN_ROOT}` is available in manifest fields (hooks, MCP
servers) and in command bodies, and there is no evidence it is expanded in skill
body text.** A skill must not rely on it.

### Options

- **(a) Tools move under a `plugins/sdd/tools/`.** Resolution from an installed
  skill is still a problem: the skill body has no variable to name the plugin
  root, and the operator's cwd is their own project. Breaks all 15 executable
  references identically. Also changes `sdd-skill-lint.py`'s self-root to
  `plugins/sdd/` — tolerable only if `skills/` moves with it.
- **(b) Tools stay repository-root-relative.** Correct for *this* repository,
  unchanged for the 774 prose references and the 417 executable references
  outside `skills/` (all of which document historical runs in `docs/`). Wrong for
  the 15 executable references in `skills/`: from an installed plugin,
  `python3 tools/sdd-gc.py` resolves against the user's project, which has no
  `tools/`.
- **(c) Shim.** A wrapper that locates the tool — extra code, extra failure mode,
  and it still needs a way to find the plugin root from a skill body. Rejected.

### Recommendation

**(b) plus a skill-relative bundling of the two tools skills actually run.**
Concretely:

1. `tools/` stays at the repository root. Nothing moves, and the 1206 references
   keep their spelling — **1191 of them (774 prose + 417 executable outside
   `skills/`) are provably unaffected**, because a prose reference names a tool
   and an executable reference in `docs/` records what a past cycle ran in this
   repository.
2. The plugin ships `sdd-gc.py` and `sdd-telemetry.py` **inside the skill that
   runs them** (`skills/sdd-orchestrate/tools/`), the documented
   skill-dir-relative pattern, and the 15 executable references are rewritten to
   that form with an explicit root argument:
   `python3 tools/sdd-gc.py --report` becomes the skill-relative path plus
   `--root .`. The `--root` flag already exists on `sdd-gc.py`. **No tool code
   change is required** to make the root explicit — for both bundled tools,
   measured on the two tools actually being bundled (not on `sdd-skill-lint.py`,
   which is excluded from the plugin three paragraphs below and is therefore not
   evidence for this claim):

   ```
   grep -n 'DEFAULT_FILE\|add_argument' tools/sdd-telemetry.py
   ```

   `tools/sdd-telemetry.py` has **no `--root`**. Its root-equivalent is
   `--file`, present on `summarize` (line 2055), `--lint` (line 2052) and
   `migrate` (line 2073, required there), defaulting to `DEFAULT_FILE =
   ".sdd/telemetry.jsonl"` (line 79) — a **cwd-relative** path. The
   skill-relative invocations in `skills/` **do not pass `--file`**; they rely on
   that default (`python3 tools/sdd-telemetry.py summarize` in
   `skills/sdd-orchestrate/USAGE.md` lines 159, 439, 572;
   `references/telemetry.md` line 484 shows `--file` as optional). Relying on the
   default is **correct** here and needs no change: `.sdd/telemetry.jsonl` is
   written into, and read from, the **operator's own repository**, which is the
   cwd — unlike the tool's own location, which after bundling is the plugin. So
   the two tools reach the right root by opposite means — `sdd-gc.py` via an
   explicit `--root .`, `sdd-telemetry.py` via its cwd-relative `--file` default
   — and neither needs a source edit.
3. `sdd-skill-lint.py`, `sdd-scope-check-selftest.py` and `sdd-eval.py` are
   **contributor tools, not plugin components.** `sdd-skill-lint.py`'s suite
   rules are hardcoded to this repository's ten skills (see Q4 measurement), and
   its self-root means that from an installed plugin it would lint the plugin's
   own copy and report a green that says nothing about the user's repository —
   precisely the false-green hazard the kickoff warns about. They stay in the
   repository and out of the plugin's component list.

Whether the two runnable tools are duplicated into the skill directory or
symlinked is a requirements-stage decision; duplication is the safer default
because a git-archived plugin install may not preserve symlinks.

### Cost in files touched

**5** skill files rewritten (the table above), **2** tool files copied/linked
into `skills/sdd-orchestrate/tools/`, **1** manifest listing components. Zero
files under `docs/`, zero tool source edits.

### Classification

**design-decision-for-requirements** (where tools live is a packaging contract),
implemented as **mechanical** edits. No `code` change to `tools/*.py` is implied.

### Confidence

**Medium-high.** The reference counts are exhaustive greps over the repository
(n = 1206 total, 38 inside `skills/`), and the "no tool code change" claim is now
read from the source of **both** bundled tools. The `${CLAUDE_PLUGIN_ROOT}`
finding is the weaker leg: it is a **negative over a sample of three installed
marketplaces**, not a documented guarantee — every actual use found sits in a
manifest field or a command body and zero in a skill body, but absence of a
skill-body use in three marketplaces is not proof the variable is unexpanded
there. The recommendation is deliberately robust to being wrong about it
(skill-dir-relative bundling works either way). **Caveat on the repo-wide
counts:** they were taken before this document existed and therefore exclude it;
re-running them now returns higher numbers, because this file itself contains
`tools/sdd-*.py` strings.

### Confidence in the `${CLAUDE_PLUGIN_ROOT}` leg specifically

**Medium.** Resolvable cheaply at the verify stage by the same real
`/plugin marketplace add` already listed under §Open Questions.

## Q3 — One umbrella plugin or several?

### Options

- **One `sdd` plugin** holding ten skills, the runnable tools and three agents.
- **A split** (`sdd` plus `sdd-tools`, or similar).
- **One plugin per skill** (ten plugins).

### Evidence

**The skills couple by *name*, not by path.**

```
S='sdd-(research|requirements|specs|plan|implement|verify|replan|migrate|review|orchestrate)'
grep -rnoE "$S"        --include='*.md' skills/ | wc -l   # 263
grep -rnoE "skills/$S" --include='*.md' skills/ | wc -l   #   2
grep -rhoE 'skills/sdd-[a-z-]+/references/[A-Za-z0-9._-]+\.md' --include='*.md' skills/ | wc -l  # 0
```

**263** cross-skill name references inside `skills/`, of which only **2** are
path-shaped, and **zero** are the `skills/<skill>/references/<file>` form that
`sdd-skill-lint.py` treats as `fail` severity. Intra-skill references use the
skill-dir-relative `references/<file>` form, which survives any relocation.

This is decisive in a specific way: `sdd-orchestrate` dispatches `sdd-review`,
`sdd-implement`, `sdd-verify` and the rest **by skill name**. A split that puts
the driver in one plugin and a phase skill in another leaves the driver naming a
skill that may not be installed — the kickoff's own disqualifier ("a split that
makes `sdd-orchestrate` unable to resolve `sdd-review` is not a trade-off"). A
name reference across a plugin boundary is not a broken path the linter can
catch; it is a silent runtime failure at dispatch time.

**The manifest supports selective components within one plugin.** From
`~/.claude/plugins/marketplaces/anthropic-agent-skills/.claude-plugin/marketplace.json`,
a plugin entry may set `"source": "./"` and an explicit `"skills": [ … ]` list:

```json
{ "name": "document-skills", "source": "./", "strict": false,
  "skills": ["./skills/xlsx", "./skills/docx", "./skills/pptx", "./skills/pdf"] }
```

Two plugins in that marketplace share `"source": "./"` and differ only in their
skill lists. So **one plugin can be carved out of the repository root without
moving any file**, and a future split is a manifest edit, not a migration. This
also means the `plugins/sdd/` subdirectory implied by §Scope is **optional**, not
required: `sui-ai-commons` uses `"source": "./plugins/sui-ai"` because that
marketplace is an umbrella for several unrelated plugins; a single-plugin
marketplace can point at `./`.

**Versioning.** `plugin.json` carries one `version` per plugin
(`sui-ai/.claude-plugin/plugin.json` → `"version": "2.0.0"`). Ten plugins mean
ten version numbers for one workflow whose stages must agree on the gate
vocabulary — the `VERDICT:` / `CHUNK_VERDICT:` / `RED_VERDICT:` producer-consumer
pairs the linter enforces across skill boundaries (42 `"file"`/`"files"` keyed
rows, Q4) would become cross-plugin version constraints with no mechanism to
express them.

### Recommendation

**One umbrella `sdd` plugin** in a `sdd-commons` marketplace, exactly as
§Decided. Prefer `"source": "./"` with an explicit component list over creating a
`plugins/sdd/` subdirectory, because it makes Q1's `docs/` exclusion and Q2's
tool exclusion manifest statements and leaves `skills/` and `tools/` in place —
which in turn keeps the 558 path-shaped rename references of Q4 from being
touched twice.

### Cost in files touched

**2** new files (`.claude-plugin/marketplace.json` and
`.claude-plugin/plugin.json` — the latter at the repository root under
`"source": "./"`). Zero existing files move.

### Classification

**design-decision-for-requirements** (one plugin, `source: "./"`), implemented as
**mechanical** scaffolding.

### Confidence

**High** on rejecting the split, **medium** on `"source": "./"`. The rejection
rests on an exhaustive count (263 name-keyed cross-skill references, of which 2
are path-shaped and 0 are the linter's `fail`-severity form) plus a structural
argument — a cross-plugin name reference fails silently at dispatch and no
linter can catch it — so no additional sampling would change it. The
`"source": "./"` recommendation rests on **one** observed marketplace
(`anthropic-agent-skills`, two entries sharing `"source": "./"` with explicit
skill lists); it is a demonstrated-possible, not a surveyed-best-practice, and
it is explicitly routed to requirements as open rather than carried as settled.

## Q4 — Rename before, with, or after the marketplace move?

### Blast radius — both measurements

All counts exclude `.worktrees/` and `.git/`.

**Repo-wide `sdd-<skill>` name references:**

```
S='sdd-(research|requirements|specs|plan|implement|verify|replan|migrate|review|orchestrate)'
grep -rnoE "$S" --include='*.md' --include='*.py' --include='*.org' \
     --exclude-dir=.worktrees --exclude-dir=.git . | wc -l
```
→ **3756** name occurrences.

**Repo-wide path-shaped (`skills/sdd-X…`) references:**

```
grep -rnoE "skills/$S" --include='*.md' --include='*.py' --include='*.org' \
     --exclude-dir=.worktrees --exclude-dir=.git . | wc -l
```
→ **1155** path-shaped occurrences; the remaining **2601** are prose.

Per top-level area (`for d in …; do grep -rnoE … "$d" | wc -l; done`):

| Area | Name refs | Path-shaped | In rename scope? |
|---|---:|---:|---|
| `skills/` | 263 | 2 | yes |
| `tools/` | 216 | 157 | yes |
| `docs/spec/` | 638 | 134 | yes |
| `docs/requirements/` | 690 | 261 | yes |
| `CLAUDE.md` | 28 | 2 | yes |
| `README.org` | 6 | 2 | yes (dropped for `README.md`) |
| `docs/ws/` | 1297 | 404 | **no** — historical record (§Decided) |
| `docs/research/` | 346 | 49 | **no** — historical record |
| `docs/superpowers/` | 272 | 144 | **no** — vendored third-party corpus |

**Live rename scope** (the six "yes" rows):

```
grep -rnoE "$S"        --include='*.md' --include='*.py' --include='*.org' \
     skills tools docs/spec docs/requirements CLAUDE.md README.org | wc -l   # 1841
grep -rnoE "skills/$S" --include='*.md' --include='*.py' --include='*.org' \
     skills tools docs/spec docs/requirements CLAUDE.md README.org | wc -l   #  558
grep -rlE  "$S"        --include='*.md' --include='*.py' --include='*.org' \
     skills tools docs/spec docs/requirements CLAUDE.md README.org | wc -l   #   91
```

→ **1841** name references, of which **558 are path-shaped** and **1283 prose**,
across **91 files**.

**Linter lines keyed on a skill path or name:**

```
wc -l tools/sdd-skill-lint.py                                    # 1092
grep -cE "skills/$S" tools/sdd-skill-lint.py                     #   72
grep -cE '"(file|files)":\s*"[^"]*sdd-' tools/sdd-skill-lint.py  #   42
grep -cE "$S" tools/sdd-skill-lint.py                            #   91
```

**91** of 1092 lines mention a skill name; **72** carry a literal
`skills/sdd-<skill>/…` path; **42** are contract rows keyed by a `"file"` or
`"files"` value naming a skill. The linter is the single densest rename surface
in the repository and it is **code**, not text.

### What each ordering leaves verifiable after step one

- **Rename first, then marketplace move.** Step one renames ten skill
  directories, 558 path-shaped and 1283 prose references, and the linter's 91
  keyed lines. The intermediate state is a repository with the *old* layout and
  *new* names — and `tools/sdd-skill-lint.py` still runs against it, because its
  root is `Path(__file__).parent.parent` (unchanged) and its checks are
  structural (`skills/<dir>/SKILL.md` exists, frontmatter `name` matches the
  directory, contract markers present). **`tools/sdd-skill-lint.py` exiting 0 is
  an independently verifiable intermediate state**, and it is a *strong* one: the
  42 contract rows verify that every producer/consumer marker pair still resolves
  after the rename, which is exactly the class of breakage a mass rename causes.
- **Marketplace move first, then rename.** Step one adds two manifest files and
  (under the `"source": "./"` recommendation) moves nothing. That is trivially
  verifiable but verifies almost nothing, and it leaves the whole rename as one
  undifferentiated second step. If the move *did* relocate `skills/` into
  `plugins/sdd/skills/`, step one would silently invalidate the linter's 72
  literal `skills/sdd-X/…` paths **and** its self-root, so the linter would run
  against `plugins/` and report clean on nothing — the false-green hazard, now
  inside the cycle's own verification.
- **Combined in one step.** The 558 path-shaped references would be edited once
  instead of twice, but no intermediate state exists to check, and a regression
  is attributable to neither change. Rejected: the kickoff's own carried-forward
  lesson is that unverified mass edits are how false criteria enter.

The claim that a combined step saves work is measurably weak under the Q3
recommendation: with `"source": "./"`, the marketplace move touches **zero**
existing files, so **zero** of the 558 path-shaped references are touched twice
by separating the steps. The "touched twice" cost of separation is nil.

### Recommendation

**Separate steps, rename first** — confirming the kickoff's leaning on measured
grounds rather than intuition:

1. **Step 1 — rename.** Ten directories, 1841 name references over 91 files (558
   path-shaped), plus 91 lines of `tools/sdd-skill-lint.py`. Gate:
   `tools/sdd-skill-lint.py` exits 0 and `python3 tools/sdd-gc.py --report`
   raises no new finding. `docs/ws/` (1297) and `docs/research/` (346) are left
   untouched per §Decided; `docs/superpowers/` (272) is a vendored corpus and is
   out of scope.
2. **Step 2 — marketplace scaffold.** Two manifest files, `LICENSE`,
   `CONTRIBUTING.md`, `README.md` (dropping the 47-line `README.org`), the three
   agent files, `.pre-commit-config.yaml`. Gate: the manifests parse and list the
   ten renamed skills.

The rename is a **code** change to `tools/sdd-skill-lint.py` (91 lines) as well
as a text change, so it must carry the linter's own self-test
(`tools/sdd-skill-lint.py --self-test`) as an acceptance criterion — the
self-test copies the real `skills/` tree (line 854,
`Path(__file__).resolve().parent.parent / "skills"`) and would fail loudly if a
contract row and its target diverged.

**Self-reference hazard, flagged as the kickoff predicted.** Step 1 edits the
linter that checks step 1, and edits `CLAUDE.md`, which contains both the old
names (28 occurrences) and prose *about* the naming rule. A rename rule written
into `CONTRIBUTING.md` will itself have to quote the old prefix it retires.
Requirements must state whether the linter gains a rule forbidding the old
prefix — and if so, exempt the document that defines the rule.

### Cost in files touched

Step 1: **91** files (which already include `tools/sdd-skill-lint.py`) plus ten
directory renames. Step 2: **6–7** new files, **1** deletion (`README.org`).

### Classification

**code** for `tools/sdd-skill-lint.py` (91 lines, 42 contract rows);
**mechanical** for the remaining 90 files; the *ordering itself* is a
**design-decision-for-requirements**.

### Confidence

**High on the blast radius, medium-high on the ordering.** Every number is an
exhaustive grep with `.worktrees`/`.git` excluded and the in-scope/out-of-scope
split taken directly from §Decided, and the linter's rename surface (91 of 1092
lines, 72 literal paths, 42 contract rows) was counted in the file itself. The
ordering argument is a **judgment on top of** those measurements — that an
independently verifiable intermediate state is worth more than a saving that
measures to zero — and its weak point is the assumption that
`tools/sdd-skill-lint.py` exiting 0 after a rename means the rename is correct;
the linter checks structure and contract-marker pairs, not semantics, so a
rename that is uniformly wrong would still pass. That is why the self-test is
made an acceptance criterion rather than treated as already sufficient.
**Caveat:** these counts likewise predate this document and exclude it.

## Q5 — Are the three agents dispatchable as a `subagent_type`?

### Answer: yes — confirmed by direct local evidence, not inference

`agents/` in this repository is empty (`ls -1 agents/` returns no entries), and
`~/.claude/agents/` holds no user-level agent file. But a **plugin-supplied**
agent is installed and loaded on this machine:

```
find ~/.claude/plugins/marketplaces/sui-ai-commons/plugins -not -path '*/.git/*'
```
→
```
plugins/sui-ai/.claude-plugin/plugin.json
plugins/sui-ai/agents/sui-move-auditor.md
plugins/sui-ai/agents/sui-move-auditor/defi-amm-and-slippage.md
plugins/sui-ai/agents/sui-move-auditor/defi-lending-and-liquidation.md
plugins/sui-ai/agents/sui-move-auditor/defi-shares-and-vaults.md
plugins/sui-ai/agents/sui-move-auditor/defi-staking-and-rewards.md
plugins/sui-ai/agents/sui-move-auditor/sui-native-pitfalls.md
plugins/sui-ai/agents/sui-move-auditor/verification-and-false-positives.md
```

and this spike's own session lists, among its available agent types:

```
sui-ai:sui-move-auditor
sui-ai:sui-move-auditor:defi-amm-and-slippage
sui-ai:sui-move-auditor:defi-lending-and-liquidation
sui-ai:sui-move-auditor:defi-shares-and-vaults
sui-ai:sui-move-auditor:defi-staking-and-rewards
sui-ai:sui-move-auditor:sui-native-pitfalls
sui-ai:sui-move-auditor:verification-and-false-positives
```

Seven files on disk, seven dispatchable agent types, naming `<plugin>:<agent>`
for a top-level file and `<plugin>:<parent>:<child>` for a file in a
subdirectory of the same name. This is a **positive, reproducible observation in
this environment** — the kickoff's "unproven" status is resolved. Plugin skills
namespace identically (`superpowers:brainstorming`, `anthropic-skills:docx`),
which corroborates the §Decided `sdd:orchestrate` surface.

### The frontmatter contract

**Derived from a sweep, not from one file.** The first draft of this table
generalised from the single `sui-ai` agent and was wrong on three of five rows.
It is re-derived here from **every** agent file in the first-party marketplace
installed on this machine, plus the `sui-ai` files:

```
cd ~/.claude/plugins/marketplaces/claude-plugins-official/plugins
find . -path '*/agents/*.md' -not -path '*/.git/*' | wc -l          # 35
for f in $(find . -path '*/agents/*.md' -not -path '*/.git/*'); do
  awk '/^---$/{n++; next} n==1{print}' "$f" | grep -oE '^[a-z_-]+:'
done | sort | uniq -c | sort -rn
```

35 files found; **3** (`skill-creator/skills/skill-creator/agents/{grader,
comparator,analyzer}.md`) carry no YAML frontmatter at all and are excluded, so
the sample is **n = 32 first-party agent files across 40 official plugins**, plus
`sui-ai/agents/sui-move-auditor.md` (the six files under
`sui-ai/agents/sui-move-auditor/` likewise carry no frontmatter — they are
sub-agent bodies). Field frequency over the n = 32:

| Field | `name` | `description` | `model` | `tools` | `color` | `effort` | `emoji` | `vibe` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Files carrying it | 32 | 32 | 24 | 23 | 20 | 8 | 0 | 0 |

**Contract for the three agent files** (caption: frequencies are over the n = 32
first-party agent files swept above; the `sui-ai` file agrees with every row):

| Field | Required | Form | Evidence |
|---|---|---|---|
| `name` | yes | kebab-case, matches the filename stem | 32/32 carry it; `sui-move-auditor.md` ↔ `name: sui-move-auditor` |
| `description` | yes | scalar, folded (`>`) or literal (`\|`); ends with an explicit trigger clause ("Use for …", "Use this agent when …"), because it is what the dispatcher matches on | 32/32 carry it; the loaded description is verbatim the file's |
| `tools` | **no** (omit = inherit) | **either** a one-line comma-separated string **or** a YAML flow sequence — both forms are first-party | 23/32 carry it. Comma string: `tools: Read, Glob, Grep, Bash` (6 files). Flow sequence: `tools: ["Write", "Read"]` — `plugin-dev/agents/agent-creator.md`, `plugin-dev/agents/skill-reviewer.md`, `plugin-dev/agents/plugin-validator.md`, `hookify/agents/conversation-analyzer.md` |
| `model` | **no** | `opus` \| `sonnet` \| `haiku` | 24/32 carry it; the **8** `code-modernization/agents/*.md` files carry no `model:` key and load fine |
| `color` | no | a colour word (`magenta`, `yellow`, `red`, `green`, …) | **20/32** across **5** plugins (`claude-security`, `feature-dev`, `hookify`, `plugin-dev`, `pr-review-toolkit`) — e.g. `plugin-dev/agents/agent-creator.md` line 33, `color: magenta` |
| `effort` | no | (first-party, undocumented here) | 8/32 — noted only so the table is not read as exhaustive |
| `emoji`, `vibe` | **no — unattested** | — | `grep -rlE '^(emoji\|vibe):'` over all 35 files returns **nothing** |

**`color` is a real field; only `emoji` and `vibe` are this repository's own
invention.** `CLAUDE.md` §Agents lists all three. `color` is set by 20 of 32
first-party agent files across five of Anthropic's own plugins, so the rationale
for dropping it — that an unrecognised key is at best inert and at worst a
validation failure — simply does not apply: it is a recognised key.
Requirements must therefore decide only about `emoji` and `vibe` (recommended:
drop, on the unattested-key rationale) or keep them documented as non-functional
decoration; **`color` is RETAINED in `CLAUDE.md` §Agents unchanged.**

Two further corrections the sweep forces, both against the single-file draft:
`tools` is **not** required to be a one-line comma string (the first-party
reference `plugin-dev/agents/agent-creator.md` uses `tools: ["Write", "Read"]`),
and `model` is **not** required at all (8 of 32 omit it). Neither affects
dispatchability: the answer to Q5 — yes, the three agents are dispatchable as
`subagent_type` — rests on the seven installed `sui-ai` files loading as seven
agent types, which is independent of every row above and **stands unchanged**.

Subdirectory nesting (`agents/<parent>/<child>.md`) yields a third namespace
segment. The three SDD agents are peers, not children, so they are **three
top-level files**: `agents/chunk-verifier.md`, `agents/red-team.md`,
`agents/reviewer.md`, surfacing as `sdd:chunk-verifier`, `sdd:red-team`,
`sdd:reviewer` — consistent with §Decided's `sdd:chunk-verifier`.

### The citation rule

Since dispatchability **is** confirmed, the rule is the primary branch of
§Decided's contingency:

> Dispatch templates cite each agent **by `subagent_type` name** —
> `sdd:chunk-verifier`, `sdd:red-team`, `sdd:reviewer` — and each template
> additionally names the **source file path** (`agents/<name>.md`) in one
> parenthetical, so the template remains readable and lint-checkable in a
> repository checkout where the plugin is not installed.

The path half is not redundancy for its own sake: `tools/sdd-skill-lint.py`'s
`check_links()` resolves backtick-quoted relative paths on disk, so a cited file
path is *mechanically verified* while a `subagent_type` name is not. The
name-plus-path form gets both the working dispatch and the linted citation. The
§Decided fallback ("ship as the single source the dispatch templates cite by
path") is unchanged and simply does not need to be exercised.

The agents' vocabulary is the harness's, per §Decided: `CHUNK_VERDICT: PASS |
FAIL`, `RED_VERDICT: BROKEN | HELD`, `VERDICT: APPROVE | APPROVE_WITH_FIXES |
REJECT`. Note the coupling this creates with Q4: `tools/sdd-skill-lint.py`
already enforces each of those tokens as a producer/consumer pair between
`skills/sdd-orchestrate/references/dispatch-templates.md` and a skill
(`grep -n 'VERDICT' tools/sdd-skill-lint.py` → rows at lines 161–176, 211–218).
Extracting the agents must not move a token out of a file the linter names, or
the contract rows fail.

### Cost in files touched

**3** new agent files, **1** `CLAUDE.md` §Agents correction, **1** manifest
entry, and **up to 3** dispatch-template citations updated in
`skills/sdd-orchestrate/references/dispatch-templates.md` (one file).

### Classification

**mechanical** (three new files and three citations), with one
**design-decision-for-requirements**: whether `emoji`/`vibe` are dropped from
`CLAUDE.md` or retained as documented non-fields (`color` is a real field and is
not part of that decision).

### Confidence

**High on dispatchability, medium-high on the frontmatter contract.**
Dispatchability is a **positive reproducible observation in this environment** —
seven files on disk, seven agent types listed in this session, names matching
`<plugin>:<agent>` — and needs no sampling argument at all.

The contract table is the part that had to be repaired: its first draft was
**Low**-confidence evidence presented without a confidence line, generalised from
**n = 1**, and it was wrong on three of five rows (`color`, `tools` form, `model`
requiredness). It is now **Medium-high**, from **n = 32** first-party agent files
across 40 official plugins plus the `sui-ai` file. The residual uncertainty is
that field *frequency* is not the same as field *requiredness*: 32/32 carrying
`name` is strong evidence it is required, but a field at 20/32 (`color`) or 8/32
(`effort`) is proven **permitted**, not proven optional-by-spec — no schema was
read, only the corpus. That distinction is exactly why `color` may not be
dropped: permitted-and-widely-used is sufficient to refute "unrecognised key",
which was the entire rationale for dropping it.

## Decided at DISCUSS (restated unchanged)

Restated verbatim from `docs/ws/marketplace/kickoff.md` §Decided at DISCUSS
(2026-09-21 — requirements inherit these; not re-litigated). No stage re-opens
them, and no stage stops to ask about them.

- **Repository name.** The GitHub repository is **already renamed** to
  `jangid/sdd-commons` (done 2026-09-21; the old URL redirects, PRs #2 and #3
  survive, the local remote is updated). The **local directory is deliberately
  still `…/tools-skills-agents`** and MUST NOT be renamed by this cycle — doing
  so would break every `~/.claude/skills/*` symlink and orphan the path-keyed
  session memory. The operator renames it after the cycle is DONE.
- **Marketplace name** `sdd-commons`; **plugin** `sdd`; components surface as
  `sdd:orchestrate`, `sdd:chunk-verifier`.
- **Naming rationale.** The `sdd-` prefix exists only because skills currently
  sit in a flat global namespace. A plugin prefix *is* that namespace, so
  `sdd:orchestrate` matches `superpowers:brainstorming` rather than the
  stuttering `code-simplifier:code-simplifier`.
- **Rename split — the historical record is not rewritten.** `skills/sdd-*/`
  directories and their frontmatter, `tools/sdd-*.py`, the live corpus under
  `docs/spec/` and `docs/requirements/`, `CLAUDE.md` and the README are renamed.
  `docs/ws/*/` plans and verifications of **closed** cycles are **not** — they
  are the historical record of what those cycles did. One `CONTRIBUTING.md` line
  notes that pre-marketplace artifacts use the old names: the dated-marker
  discipline applied once at the boundary, not thousands of times.
- **License** MIT, as `sui-ai-commons`.
- **README** converts to `README.md`; **`README.org` is dropped**, matching the
  marketplace convention.
- **Agents ship either way.** If the spike finds they cannot load as a
  `subagent_type`, they still ship as the single source the dispatch templates
  cite by path — never dead documentation. Their vocabulary is the harness's
  (`CHUNK_VERDICT:`, `RED_VERDICT:`, `VERDICT:`), not generic reviewer prose.
- **Execution is sequential.** No implement-stage fan-out: the rename touches
  overlapping files across chunks, which is exactly the collision case
  harness-p6 measured fan-out to be bad at.
- **Telemetry on. Red team on at verify.** Both earned their cost in harness-p6
  — red found the ninth false acceptance criterion and the chunk verifier caught
  a real dropped traceability row.
- **No split, and replanning is not a stop condition.** The operator directed
  "replan as needed and finish everything". The scope guard is therefore: replan
  inside this cycle until everything lands — pre-commit, marketplace scaffold,
  manifests, LICENSE, CONTRIBUTING, README, the rename, and the three agents.
  `REPLAN_MAX` is lifted **for scope-sizing replans only**; the cap's gate event
  still renders, and a replan for any other reason is handled normally.
- **Terminal state is a PR, not a merge.** Push the `marketplace` branch, open a
  PR against `main` with a full body, and **do not merge** — the operator
  reviews the migration diff.

## Recommendation for requirements

**Proceed to requirements.** All five questions are answered on measured
evidence; none produced a pivot or a blocker.

**Carried into requirements as settled by this spike:**

1. `docs/` stays in the repository and is excluded from the plugin's component
   list. No skill's phase detection and no tool's root resolution breaks
   (796 relative citations, 0 non-relative; gc roots on the operator's cwd).
2. `tools/` stays at the repository root. The two tools a skill actually invokes
   (`sdd-gc.py`, `sdd-telemetry.py`) are bundled skill-dir-relative and invoked
   with an explicit root; `${CLAUDE_PLUGIN_ROOT}` is **not** usable from a skill
   body. `sdd-skill-lint.py`, `sdd-scope-check-selftest.py` and `sdd-eval.py`
   are contributor tools, not plugin components.
3. One umbrella `sdd` plugin, `"source": "./"`, explicit component list. A split
   is rejected on 263 name-keyed cross-skill references.
4. Rename first, marketplace scaffold second; `tools/sdd-skill-lint.py` exit 0 is
   the verifiable intermediate state. Under `"source": "./"` the separation costs
   zero double-touched files.
5. Agents are dispatchable. The contract, swept over n = 32 first-party agent
   files: `name` and `description` are required (32/32); `tools` (23/32) and
   `model` (24/32) are **optional**, and `tools` accepts **either** a one-line
   comma string **or** a YAML flow sequence. `color` is a **real** first-party
   field (20/32, five official plugins) and stays in `CLAUDE.md`; only `emoji`
   and `vibe` are unattested (0/32). The citation is the `subagent_type` name
   plus a parenthetical file path.

**Design decisions requirements must record (this spike recommends, does not
decide):**

- Whether the marketplace uses `"source": "./"` (recommended) or creates a
  `plugins/sdd/` subdirectory as §Scope's prose implies. This spike recommends
  `"source": "./"`; it is not in §Decided, so it is open.
- Whether the two runnable tools are duplicated into
  `skills/sdd-orchestrate/tools/` or symlinked (recommendation: duplicate).
- Whether `emoji`/`vibe` are dropped from `CLAUDE.md` §Agents (recommendation:
  drop — 0 of 32 first-party agent files carry either) or retained as documented
  non-fields. **`color` is not part of this decision**: it is a real field set by
  20 of those 32 files, and is retained unchanged.
- Whether `tools/sdd-skill-lint.py` gains a rule forbidding the retired `sdd-`
  skill prefix, and if so how the document that defines the rule is exempted
  (self-reference hazard).
- Whether the 150 dangling `docs/spec/*.md` citations in 24 skill files are
  accepted as a documented gap (recommendation) or rewritten.

## Open Questions

- **Does a plugin skill's own `references/<file>.md` resolve from an installed
  plugin?** Every installed example (`anthropic-agent-skills`, `plugin-dev`)
  ships `references/` and `scripts/` inside the skill directory and cites them
  relatively, so the pattern is clearly supported; this spike did not install
  `sdd-commons` and observe a lazy `references/` read at runtime. The ten
  lazily-read `sdd-orchestrate` reference files depend on it. Verify at the
  verify stage with a real `/plugin marketplace add` against the pushed branch.
- **Does the marketplace `renames` field help the `sdd-` to `sdd:` transition?**
  `sui-ai-commons/.claude-plugin/marketplace.json` carries
  `"renames": {"sui-move-auditor": "open-agents", "open-agents": "sui-ai"}`,
  which migrates already-installed users across a plugin rename. It is
  plugin-scoped, and the SDD skills have never been distributed as a plugin, so
  it is probably inapplicable — but requirements should confirm rather than
  assume, since it is cheap if it applies.

## Assumptions

- **No operator was available** (non-interactive pipeline stage). Every question
  was decided on measured evidence per the kickoff's instruction that all five
  are spike questions, not operator questions. Nothing was asked and no consent
  was assumed; the five items above are explicitly routed to requirements rather
  than decided here.
- **Claude Code plugin/marketplace documentation was read from the three
  marketplaces installed on this machine** (`claude-plugins-official/plugin-dev`,
  `anthropic-agent-skills`, `sui-ai-commons`) rather than fetched from the web.
  These are the shipped, authoritative copies and they double as working
  examples; no network access was used.

## Budget consumed

Against the dispatched budget of "one spike, <= 45 tool calls, no prototypes",
across both dispatches of this spike:

| Dispatch | Tool calls | Test runs |
|---|---:|---:|
| Initial spike | 19 | 1 |
| Review-repair (C1, C2, M1, M2, M3) | 24 | 0 |
| **Total** | **43** | **1** |

Within budget (43 of ~45 across both dispatches; the repair dispatch's own
sub-budget was <= 25 and it used 24). **All figures are self-reported** — the agent's own
count of its tool invocations, not a harness measurement, and there is no
independent record to reconcile them against. The single test run was reported by
the initial dispatch; the repair dispatch ran no tests, only read-only greps and
the edits themselves. No mutating command ran in this worktree in either
dispatch.

## Prototype

None. No prototype was built (`no prototypes` per the dispatched budget), no tool
was copied, and no mutating command ran in this worktree.
