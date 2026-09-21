---
workstream: marketplace
description: Public release as a Claude Code marketplace — pre-commit, plugin scaffold, LICENSE/CONTRIBUTING/README, the sdd-* → sdd: rename, and the three proven agents
cycle: marketplace-release
research_id: RS-MARKETPLACE-001
entry_stage: research
date: 2026-09-21
branch: marketplace
---

# Kickoff: RS-MARKETPLACE-001 — Marketplace release

Run `/sdd-research` for workstream `marketplace`. This is the first cycle of new
product work after the harness-hardening series closed (`docs/ws/harness-p6/`
verification `status: pass`, PR #3 merged at `7be04f8`). It takes the SDD
toolkit from a private repository of symlinked skills to a **publicly
installable Claude Code marketplace**, and it adds the pre-commit configuration
the repository has been missing since harness-p4 flagged it.

**Execution location.** The cycle runs entirely in the git worktree
`.worktrees/marketplace` on branch `marketplace`, never in the main checkout.
`~/.claude/skills/sdd-*` are symlinks into the main checkout, so the session
driving this cycle resolves its own driver — including ten lazily-read
`references/*.md` files — through those paths. Renaming `skills/sdd-orchestrate/`
in the main checkout would dangle the symlink and break the driver **mid-cycle**.
Editing only in the worktree keeps the running driver stable while the cycle
rewrites its committed copy. The worktree is excluded locally via
`.git/info/exclude`, so it is invisible to `git status` in both checkouts.

## Scope in one paragraph

Two parts, one cycle, no split. **(1) Pre-commit.** No `.pre-commit-config.yaml`
exists. The hooks are `tools/sdd-gc.py --fast` (which self-describes as the
pre-commit profile — lint + cross-links + Q-IMPL, no date or history walk) and
`tools/sdd-skill-lint.py`, plus the standard `trailing-whitespace`,
`end-of-file-fixer`, `check-yaml`, `check-json`. The three heavier self-tests
(`sdd-scope-check-selftest.py`, `sdd-telemetry.py --self-test`,
`sdd-eval.py`) stay out of the commit path — they are slow and their inputs are
frozen fixtures. **(2) Public release as a Claude Code marketplace**, modelled
on `github.com/AlphaFiTech/sui-ai-commons` (same author): a
`.claude-plugin/marketplace.json` that makes the repository a marketplace, a
`plugins/sdd/` plugin holding the ten skills, the tools and three agents, an MIT
`LICENSE`, a `CONTRIBUTING.md`, and a real `README.md` (the current `README.org`
is structure-only with no usage section and is dropped, not converted in place).
Install becomes `/plugin marketplace add jangid/sdd-commons` followed by
`/plugin install sdd@sdd-commons`. The **rename** is part of this cycle: skills
drop the now-redundant `sdd-` prefix and surface as `sdd:orchestrate`,
`sdd:implement`, and so on. The three agents — **chunk verifier**, **red team**,
**reviewer** — are extracted from the dispatch templates that have driven six
cycles, and ship as files whether or not they prove loadable as a
`subagent_type`.

## Decided at DISCUSS (2026-09-21 — requirements inherit these; not re-litigated)

These were settled with the operator before this kickoff was written. No
downstream stage re-opens them, and no stage stops to ask about them.

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

## Research questions

Every question below is a **spike question, not an operator question**: the
spike decides it on measured evidence and the cycle proceeds. Counts are to be
**derived at run time**, never pinned as literals from this file — the
harness-p6 cycle corrected ten false acceptance criteria, two of them introduced
by its own repairs, and every one was a corpus-measured count asserted as a
constant.

- **Q1 — Does `docs/` ship inside the plugin?** The corpus is six cycles of this
  repository's own SDD artifacts. It is simultaneously the **best available
  evidence that the system works** and a large body of text irrelevant to
  someone installing the plugin to run their own cycles. State the options —
  ship it all, ship none of it, ship a curated subset, or ship it in the
  repository but exclude it from the plugin directory — and for each say what an
  installing user gains, what the download costs, and whether any skill's phase
  detection or any tool's default root breaks when `docs/` is absent from the
  installed plugin. The last sub-question is the deciding one: a skill that
  cannot find `docs/spec/*.md` at install time is a broken install, not a
  trade-off. Cost in files touched; classify.

- **Q2 — Where do the tools live, and can `${CLAUDE_PLUGIN_ROOT}` absorb the
  path references?** Measure, at this branch point, how many references to
  `tools/sdd-*.py` paths exist and how they are distributed across `docs/`,
  `skills/` and `CLAUDE.md`. Then state, for each option — tools move under
  `plugins/sdd/tools/`, or tools stay repository-root-relative, or both via a
  shim — how a skill invoked from an **installed plugin** resolves the tool
  path, whether `${CLAUDE_PLUGIN_ROOT}` is available in skill body text or only
  in manifest fields, and what happens to a reference in a `docs/spec/` file
  that is documentation rather than an invocation. Distinguish **executable**
  references (a skill telling the operator to run a command) from **prose**
  references (a spec naming the tool): only the first class breaks. Cost in
  files touched; classify.

- **Q3 — One umbrella plugin or several?** The repository holds ten SDD skills,
  five tools and three agents that form one coherent workflow. State the
  options — one `sdd` plugin; a split such as `sdd` plus `sdd-tools`; or one
  plugin per skill — against the cost of installing, versioning and updating
  them, and against the fact that the skills cross-reference each other by path.
  A split that makes `sdd-orchestrate` unable to resolve `sdd-review` is not a
  trade-off. Cost in files touched; classify.

- **Q4 — Rename before, with, or after the marketplace move?** Both are large
  mechanical edits over the same files, so the ordering decides how many of them
  are touched twice and how verifiable each step is. Measure the blast radius of
  each: how many `sdd-<skill>` name references exist, how many of those are
  **path-shaped** (`skills/sdd-X/…`) and therefore break on rename versus how
  many are prose; and how many lines of `tools/sdd-skill-lint.py` are keyed on a
  skill path. State for each ordering what is independently verifiable after
  step one, and which ordering leaves the linter able to check the intermediate
  state. The leaning going in is **separate steps** (two smaller verifiable
  changes), but the spike measures rather than asserts it. Cost in files
  touched; classify.

- **Q5 — Are the three agents dispatchable as a `subagent_type`?** Unproven in
  this environment: `~/.claude/agents/` is empty and no user-level agent file
  exists on this machine to copy, so the only evidence available is a marketplace
  install or the documented agent frontmatter contract. Spike it **early and
  cheaply**. The answer does **not** block: the agents ship either way (see
  §Decided). What the spike must produce is the **frontmatter contract** the
  three files must satisfy (`name`, `description`, `tools`, `model`, and which
  of `color`/`emoji`/`vibe` are real fields versus this repository's own
  convention), and a statement of how the dispatch templates should cite them —
  by `subagent_type` name if loadable, by file path if not. Cost in files
  touched; classify.

## Success criteria

- Q1–Q5 each answered with a recommendation, its evidence, and the cost in files
  touched; each classified **mechanical** (text/scaffold), **code**
  (`tools/*.py`), or **design-decision-for-requirements**.
- Q1 states, for the recommended option, whether any skill's phase detection or
  any tool's default root breaks when `docs/` is absent from the installed
  plugin — answered by reading the phase-detection blocks and the tools' root
  resolution, not by assertion.
- Q2 reports the measured reference count **and its split into executable versus
  prose references**; an answer that gives one total without the split does not
  meet this criterion.
- Q4 reports both blast-radius measurements (path-shaped versus prose name
  references) and names the ordering that leaves an independently verifiable
  intermediate state.
- Q5 produces the agent frontmatter contract and the citation rule, whether or
  not dispatchability could be confirmed. "Could not be determined" is an
  acceptable answer to dispatchability; it is not an acceptable answer to the
  contract.
- The findings restate the §Decided list unchanged, so requirements sees one
  bounded scope.
- Every count in the findings is derived by a command shown in the findings, and
  no count from **this kickoff** is carried forward as a measured value.

## Budget

One spike, ≤ 45 tool calls. Desk research over this repository plus the
public `AlphaFiTech/sui-ai-commons` layout and the Claude Code plugin/marketplace
documentation. Read-only runs of `tools/sdd-gc.py` and `tools/sdd-skill-lint.py`
are permitted. Any probe that needs a scratch repository runs under `$TMPDIR`,
never against this worktree, and runs no mutating git command here.

**Tool-root warning, carried from harness-p6.** `tools/sdd-gc.py` and
`tools/sdd-skill-lint.py` default their root to their own repository. A copy of
a tool run without an explicit root silently scans the real corpus and returns a
false green. Any probe that copies a tool MUST pass an explicit root.

**Nested-checkout warning, specific to this cycle.** This worktree sits at
`.worktrees/marketplace` **inside** the main checkout. Any command that walks
the tree from the repository root — a linter, a `grep -r`, a count — must not
recurse into a nested `.worktrees/` copy of `docs/` or `skills/`, or every
measured count doubles. Exclude it explicitly and say so where a count is
reported.

## Out of scope

- Renaming the **local directory** `…/tools-skills-agents` (see §Decided).
- Renaming `docs/ws/*/` plans and verifications of closed cycles.
- Any change to the nine phase skills' or the driver's **behavioural contracts**
  — this cycle moves, renames and packages them; it does not alter what they do.
  A rename that changes a contract is a defect, not scope.
- Merging the `marketplace` branch to `main`: the cycle ends at an open PR.
- Publishing to any registry beyond making the repository itself a marketplace.
- Re-opening anything settled by RS-008 or `RS-HARNESSP2-001` …
  `RS-HARNESSP6-001`.
- Touching the frozen telemetry fixtures under `tools/fixtures/` or the live
  `.sdd/telemetry.jsonl`.
- Adding any attribution trailer to a commit message or PR body
  (`skills/sdd-orchestrate/references/write-scope.md` §7b — the driver carries
  this rule itself).

## Carried forward — each cost harness-p6 real rework

- Tell every **verifier** that aggregate-traceability regeneration is
  orchestrator post-gate bookkeeping, or it raises a false `FAIL` on every chunk
  that fills a traceability cell.
- **Declare write scope wide.** Five dispatches in harness-p6 were under-scoped;
  each cost a `PARTIAL` return or a gate-time repair.
- **Run every mechanical acceptance criterion when you write it**, and derive
  both sides of any count at run time rather than pinning a literal.
- **The self-reference hazard.** A rule about text lives inside its own domain: a
  marker quoting the phrase it retires, a criterion quoting its own search
  string, a skill file quoting a string its own linter forbids. It fired four
  times in harness-p6. This cycle edits `CLAUDE.md`, a README and a linter —
  expect it again.
