---
workstream: marketplace
status: pending-red
research_id: RS-MARKETPLACE-001
last_updated: 2026-09-21
plan_ref: docs/ws/marketplace/plan.md
---

# Verification Report — marketplace

## Summary

Blue verification passes. All 37 `REQ-*-MARKETPLACE-*` requirements were walked
against evidence derived at run time; every one holds. All eight plan chunks are
complete (59 typed tasks, all `[x]`), the quality gates are green, and the
regression diff against the workstream branch point `7be04f8` contains only this
cycle's own delta — 93 files, no unintended path. Three Minor issues are
recorded, none of which blocks the PR: an accepted packaging cost the operator
settled on 2026-09-21, a pre-existing contradiction inside a section this cycle
was forbidden to change in substance, and two behaviour-neutral stale spellings
of a retired filename. One gate result is a **sandbox artefact, not a repository
defect**: `end-of-file-fixer` cannot open `.claude/settings.json` with `rb+`
inside this sandbox; the file already ends in `\n`, so the hook is a no-op
outside it. `status:` is `pending-red` because the dispatch carries
`Red team: enabled` — blue passed, the red verdict is outstanding, and the
orchestrator flips `pending-red -> pass` at the DONE gate.

## Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| Skill linter (`python3 tools/skill-lint.py`) | pass | `OK: 25 file(s) clean`, exit 0 |
| Skill linter self-test (`--self-test`) | pass | all rule classes fire, including the new `retired-prefix` fixture; exit 0 |
| Drift sweep (`python3 tools/gc.py --report`) | pass | `9 sweep(s) clean, 0 warning(s), 31 info` before the traceability write; finding-line set **identical** to the Chunk 0 entry sweep (31 == 31, `comm` both ways empty) |
| Drift sweep after the traceability write | pass (designed handshake) | `1 warning(s)` — `[traceability-aggregate] aggregate differs from regenerate(...)`. That is the expected handshake between this per-workstream write and the orchestrator's post-gate regeneration (`ws-traceability.md` §Aggregate Regeneration Ownership); it is not a finding on any `pending-red` cell, and the 31 info findings are unchanged |
| `pre-commit validate-config` | pass | exit 0 |
| `pre-commit run drift-sweep --all-files` | pass | exit 0 |
| `pre-commit run skill-lint --all-files` | pass | exit 0 |
| `pre-commit run trailing-whitespace / check-yaml / check-json --all-files` | pass | exit 0 each |
| `pre-commit run --all-files` | pass with a sandbox artefact | five of six hooks Passed; `end-of-file-fixer` raised `PermissionError: Operation not permitted: '.claude/settings.json'` opening the file `rb+`. `.claude/settings.json` is a sandbox-protected path in this session; `tail -c 1` on it is `0a`, so the hook has nothing to fix. Working tree clean (`git status --porcelain` empty) after the run |
| `tools/scope-check-selftest.py` | pass | `OK: 44/44 scenarios passed`; `--self-test` also exits 0 |
| `tools/telemetry.py --self-test` | pass | full self-test OK, frozen p3/p4 fixture sha256 unchanged |
| `tools/eval.py --self-test` | pass | `6 records, 9 fields, aggregate, empty/missing file, csv` |

## Acceptance Criteria

### skill-namespace-rename.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-NAME-MARKETPLACE-001 — skill dirs free of the retired prefix, `name` == basename, linter 0 | pass | 10 directories under `skills/` hold a `SKILL.md`; every basename fails the retired-prefix pattern and every frontmatter `name` string-equals its basename, both read from disk in one run; 0 mismatches. `tools/skill-lint.py` exits 0 |
| REQ-NAME-MARKETPLACE-002 — no `skills/<other>/…` cross-skill path references | pass | run-time grep over `skills/` for `skills/<other-skill>/` = 0 matches; the `…/references/<file>` form = 0 matches |
| REQ-NAME-MARKETPLACE-003 — tool filenames, `--help`, self-references, history | pass | `ls tools/*.py` yields 5 files, none matching the retired pattern; `--help` exits 0 for all five (`eval.py:0, gc.py:0, scope-check-selftest.py:0, skill-lint.py:0, telemetry.py:0`); grep of each tool's own source for its retired filename = 0; `git log --follow` resolves each to pre-rename history (2/7/16/14/13 commits) |
| REQ-NAME-MARKETPLACE-004 — six live areas clean | pass | scan using the linter's own `RETIRED_RE` over `skills/`, `tools/`, `docs/spec/`, `docs/requirements/`, `CLAUDE.md`, `README.md`, applying the fenced-block + inline-backtick skip and the four-path self-exemption: **0** bare occurrences |
| REQ-NAME-MARKETPLACE-005 — historical record provably intact | pass | the same scan over `docs/ws/` (excluding `docs/ws/marketplace/`), `docs/research/` and `docs/superpowers/` returns **497** occurrences; `git diff --name-only bceac64 f7a1a6d` (the Chunk 1–2 implementing change) lists **no** path under those three areas |
| REQ-NAME-MARKETPLACE-006 — CONTRIBUTING names both forms and the pre-marketplace corpus | pass | `CONTRIBUTING.md` §The naming boundary names `sdd:orchestrate` / `sdd:implement` and the retired `sdd-` form, and identifies closed-cycle `docs/ws/`, `docs/research/` and `docs/superpowers/` as the set that keeps it |
| REQ-NAME-MARKETPLACE-007 — rename ordered before scaffold; the rename-close gate | pass | plan chunk order: Chunks 1–3 rename, Chunk 5 manifests. At `3ddfdb3`, `git ls-tree -r --name-only` matches **0** `.claude-plugin` paths, the linter exits 0, and the sweep's finding set equals the entry sweep's |
| REQ-NAME-MARKETPLACE-008 — linter follows the rename; contract rows unchanged | pass | grep of `tools/skill-lint.py` for a prefixed `skills/` literal = 0; REQUIRED contract rows keyed on a skill file, counted by the same command against `git show <sha>:<linter>`: `d1ef8f2`=40, `61d9498`=40, `f7a1a6d`=40, `3ddfdb3`=40, HEAD=40 |
| REQ-NAME-MARKETPLACE-009 — retired-prefix rule + synthesized fixture | pass | the `--self-test` synthesizes four occurrences (bare, backticked, fenced, self-exempt) into a temp root and asserts exactly one finding, on `docs/spec/bare.md`, at `fail` severity, with its fix string; the three skipped files are asserted absent. On the live repository the rule raises 0 findings (linter exit 0) |
| REQ-NAME-MARKETPLACE-010 — symlink hazard and both operator actions | pass | `CONTRIBUTING.md` §The symlink hazard states the dangle, and names both actions (re-point each symlink; retire in favour of `/plugin install sdd@sdd-commons`). `docs/requirements/index.md` §Out of Scope names the same post-DONE step and extends it to the ten symlinks themselves |

### pre-commit.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-PC-MARKETPLACE-001 — six hook ids, config validates | pass | `pre-commit validate-config` exit 0; ids parsed from the file = `{check-json, check-yaml, drift-sweep, end-of-file-fixer, skill-lint, trailing-whitespace}`, 6 entries, equal to §The hook set |
| REQ-PC-MARKETPLACE-002 — local hook shape, both exit 0, violation fails | pass | `drift-sweep` and `skill-lint` both carry `pass_filenames: false` and `always_run: true` under `repo: local` with `language: system`; `pre-commit run drift-sweep --all-files` and `pre-commit run skill-lint --all-files` each exit 0. The scratch-copy violation half was executed in Chunk 3 task 6 under an explicit root |
| REQ-PC-MARKETPLACE-003 — four hygiene hooks at an explicit rev | pass | all four sit under `repo: https://github.com/pre-commit/pre-commit-hooks` at `rev: v6.0.0` (non-empty explicit string). `pre-commit run --all-files`: see the sandbox artefact note in §Quality Gates |
| REQ-PC-MARKETPLACE-004 — contributor tools out of the commit path, named in CONTRIBUTING | pass | grep of `.pre-commit-config.yaml` for `scope-check-selftest`, `eval.py`, `--self-test` = **0** matches; `CONTRIBUTING.md` §The three heavier checks names all three with their commands in a table |
| REQ-PC-MARKETPLACE-005 — idempotence, frozen fixtures, excludes with reasons, window | pass | `git status --porcelain` empty after `pre-commit run --all-files`; `git diff d1ef8f2 HEAD -- tools/fixtures/` = **0** lines; the `exclude:` verbose regex carries four patterns — `tools/fixtures/`, `docs/superpowers/`, `docs/ws/`, `docs/research/` — each with its reason on its own line, equal to the spec's exclude table. Window halves re-run at Chunk 7 task 3: `git diff 3ddfdb3 HEAD -- tools/gc.py tools/telemetry.py` empty; the `--name-only` listing yields only `docs/ws/marketplace/plan.md` under the three excluded areas, carved out by the script-applied exception (`Q-IMPL-MARKETPLACE-003`) |
| REQ-PC-MARKETPLACE-006 — no rule of the gate's own | pass | every parsed entry is one of the two local or four hygiene hooks; `grep -c '^\s*args:'` on the config = **0**, so no entry carries an `args` value at all (the drift sweep's `--fast` profile selector sits in `entry:`) |

### harness-agents.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-AGENT-MARKETPLACE-001 — three top-level files, no `.gitkeep`, kebab-case | pass | `ls -a agents/` = `chunk-verifier.md`, `red-team.md`, `reviewer.md` and nothing else; no subdirectory; `agents/.gitkeep` deleted in the cycle diff; all three stems match `[a-z0-9]+(-[a-z0-9]+)*`; all three appear in the manifest component list (see REQ-PKG-MARKETPLACE-003) |
| REQ-AGENT-MARKETPLACE-002 — frontmatter contract, no mutating tools, dropped keys absent | pass | each file parses with `name` == stem, a `description` ending in an explicit `Use when …` trigger clause, `tools: Read, Grep, Glob, Bash` (no `Write`/`Edit`/`NotebookEdit`), plus `model` and `color`; `grep -rn '^emoji:\|^vibe:' agents/` = 0 |
| REQ-AGENT-MARKETPLACE-003 — `CLAUDE.md` §Agents field list | pass | the section states "`name`, `description`, `tools`, `model`, `color` — exactly five, and no others", names `color`, and contains neither dropped field (grep over the section = 0) |
| REQ-AGENT-MARKETPLACE-004 — token at line start, linter green, superset relation | pass | each agent file carries its token at the start of a line; token file-sets derived by the same grep against a `git archive` of `3ddfdb3` and against HEAD, with pre-rename skill paths normalised: `CHUNK_VERDICT:` 62 -> 63, `RED_VERDICT:` 45 -> 46, `VERDICT:` 76 -> 79, **no file missing** from any after-set. Linter and `--self-test` exit 0 |
| REQ-AGENT-MARKETPLACE-005 — citation by name and by path in the same template block | pass | template blocks derived from the file's own headings; each role's `sdd:<name>` and its backticked `agents/<name>.md` occur inside exactly one shared block — `## CHUNK VERIFIER subagent template`, `## RED TEAM subagent template`, `## REVIEW subagent template`. All three cited paths exist on disk and the linter's link check exits 0 |
| REQ-AGENT-MARKETPLACE-006 — single source, `RETURN:` verbatim, contract rows unchanged | pass | no sentence of 60 characters or more is shared between any agent file and `dispatch-templates.md` (0 for all three roles); 5 `RETURN:` blocks remain in the templates and the linter's verbatim contract rows pass; REQUIRED contract rows 40 before and after the extraction |

### marketplace-packaging.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-PKG-MARKETPLACE-001 — marketplace manifest parses and declares one plugin | pass | `.claude-plugin/marketplace.json` parses; `name` == `sdd-commons`; `owner` present; `plugins` = one entry named `sdd` |
| REQ-PKG-MARKETPLACE-002 — `source: ./`, plugin manifest fields, no `plugins/` | pass | `source` == `'./'`; `.claude-plugin/plugin.json` parses with `name` `sdd`, `version` `0.1.0`, a 199-character `description`; `os.path.isdir('plugins')` is `False` |
| REQ-PKG-MARKETPLACE-003 — component list set equality, no `docs/` path | pass | manifest `skills` basenames vs directories under `skills/` holding a `SKILL.md`: 10 == 10, sets equal; manifest `agents` vs `agents/*.md`: `{chunk-verifier.md, red-team.md, reviewer.md}`, sets equal; listed paths starting `docs/` = `[]` |
| REQ-PKG-MARKETPLACE-004 — no absolute / home / plugin-root `docs/` citation | pass | the spec's own `grep -rnE` over `--include='*.md' skills/` returns **0** matches; the manifest check above shows no `docs/` path |
| REQ-PKG-MARKETPLACE-005 — contributor tools out of both the skills and the list | pass | grep over `skills/` for a `python3 ` or `./` invocation prefix of any of the three = **0**; none of the three appears in the component list |
| REQ-PKG-MARKETPLACE-006 — bundled copies are regular byte-identical files; no tool lost | pass | `cmp skills/orchestrate/tools/gc.py tools/gc.py` exit 0, `islink` False; same for `telemetry.py`; `ls tools/*.py \| wc -l` = 5 now vs 5 at `d1ef8f2` (not less); `git log --follow` resolves all five to pre-change history |
| REQ-PKG-MARKETPLACE-007 — explicit root on every skill-side invocation; bundled tools frozen | pass | 9 drift-sweep invocations found in `skills/`, **9** carrying an explicit root; 0 telemetry invocations passing a skill- or plugin-rooted path; `git diff 3ddfdb3 HEAD -- tools/gc.py tools/telemetry.py` = 0 lines |
| REQ-PKG-MARKETPLACE-008 — no skill body depends on the plugin-root variable | pass | fence-aware scan of `skills/**/*.md` for `CLAUDE_PLUGIN_ROOT` outside a fenced code block: **0** occurrences |
| REQ-PKG-MARKETPLACE-009 — dangling spec citations documented, count invariant | pass | `CONTRIBUTING.md` §Where the contracts live states "Those citations resolve in this repository, not in an installed plugin"; the same `docs/spec/*.md` citation grep over `skills/` yields **150** at `016da07` (the packaging chunk's entry) and **150** at HEAD |
| REQ-PKG-MARKETPLACE-010 — install observation recorded with commands | pass | recorded in plan Chunk 7 task 2, performed by the operator in a real session (the install commands write the operator's own configuration and are outside a dispatched leaf's permissions, so this verifier cites rather than re-runs). Commands: `claude plugin marketplace add /Users/pankaj/work/github/jangid/tools-skills-agents/.worktrees/marketplace` -> "Successfully added marketplace: sdd-commons"; `claude plugin install sdd@sdd-commons` -> "Successfully installed plugin: sdd@sdd-commons (scope: user)". The plugin materialised to a **separate** cache copy, `~/.claude/plugins/cache/sdd-commons/sdd/0.1.0`, pinned to `gitCommitSha` `0d2d71eb7e2e8091b98cea18d78eec405c92459a`, which is what makes the reference-resolution observation non-circular. `claude plugin details sdd@sdd-commons` listed Skills (10): implement, migrate, orchestrate, plan, replan, requirements, research, review, specs, verify; Agents (3): reviewer, red-team, chunk-verifier — equal to the manifest's 13 declared components. All ten of the driver's lazily-read reference files resolve from the installed copy under `<install path>/skills/orchestrate/references/`: `dispatch-templates.md`, `drift-sweep.md`, `fan-out.md`, `isolation.md`, `loop-control.md`, `phase-detection.md`, `return-contract.md`, `telemetry.md`, `v4-workstreams.md`, `write-scope.md` |
| linter, self-test and sweep green after the packaging change | pass | see §Quality Gates; sweep finding-line set identical to the entry sweep |

### project-docs.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-DOCS-MARKETPLACE-001 — MIT `LICENSE` agreeing with the manifest | pass | `LICENSE` first line is `MIT License`; a `Copyright (c)` line names the holder within the first five lines; `license` parsed from `.claude-plugin/plugin.json` is `MIT` |
| REQ-DOCS-MARKETPLACE-002 — README usage heading and README↔manifest set equality | pass | `README.md` carries a heading whose text is `Usage`, parsed from the heading list; both install commands name `sdd-commons` and `sdd@sdd-commons`, equal to the values parsed from the marketplace manifest; the set of `sdd:<name>` component names in the README (13) **equals** the manifest's component set (13) — symmetric difference empty — and every README name maps to an existing `skills/<x>/` directory or `agents/<x>.md` file |
| REQ-DOCS-MARKETPLACE-003 — the retired front door is gone, visibly | pass (with one stale spelling, below) | `test ! -e README.org` succeeds; `git log --diff-filter=D -- README.org` shows the deletion at `1b6295a docs: add LICENSE, README.md and CONTRIBUTING.md; retire README.org`. The scripted scan over the six live areas, applying the fenced/backtick skip and then the rule's own self-exemption list, returns **0** — the sole raw hit is `tools/skill-lint.py:374`, a self-exempt path, and is recorded as a Minor below |
| REQ-DOCS-MARKETPLACE-004 — four `CONTRIBUTING.md` items, cross-spec criteria pass | pass | the four items are identifiable sections: §The naming boundary (+ §The symlink hazard), §Where the contracts live, §Pre-commit (+ §The three heavier checks, run explicitly), §Adding new content (§New skill / §New agent / §New tool). The four cross-spec criteria — REQ-NAME-MARKETPLACE-006, REQ-NAME-MARKETPLACE-010, REQ-PKG-MARKETPLACE-009, REQ-PC-MARKETPLACE-004 — were each re-run here and each passes |
| REQ-DOCS-MARKETPLACE-005 — `CLAUDE.md` clean, names both manifests, no substantive change elsewhere | pass | fence-aware retired-name scan of `CLAUDE.md` = **0**; the file names `.claude-plugin/marketplace.json` (lines 8, 18) and `.claude-plugin/plugin.json` (lines 9, 19). `git diff 7be04f8 HEAD -- CLAUDE.md` is 56 insertions / 32 deletions; filtering the changed lines for anything beyond name substitution leaves 11 lines, all inside §Repository Structure, §Agents and §Quality Checks — the three sections Chunk 6 task 5 is scoped to. The phase-detection table, the cycle-identity rules and the v4 layout section show name substitution only |
| `CLAUDE.md` §Agents field list equals the spec's five | pass | duplicate of REQ-AGENT-MARKETPLACE-003 above; passes |
| sweep and linter exit 0 after these documents land | pass | see §Quality Gates |

## Traceability Verification

- 37 rows in `docs/ws/marketplace/traceability.md`; **every** row has a non-empty Spec column, and Test, Implementation and Verified are now filled for all 37.
- `Verified` reads `pending-red` on all 37 — the red round is outstanding, so the durable matrix asserts no `pass` (REQ-REDB-HARNESSP3-003). No row is `fail` and none is `descoped`.
- gc criterion for those cells: `python3 tools/gc.py --report` after the write raises **no** new finding on a `pending-red` cell. The one `[traceability-aggregate]` warning is the designed handshake with the orchestrator's post-gate regeneration and is not a finding against any cell.
- The shared aggregate `docs/requirements/traceability.md` was **not** touched: the dispatched write scope omits it, which is the signal that regeneration is orchestrator post-gate bookkeeping.
- No gaps: no requirement is missing a spec, a test or an implementation reference.

## User-Perspective Validation

| Scenario | Status | Notes |
|----------|--------|-------|
| Install the plugin as a user would | pass | operator-performed, Chunk 7 task 2: marketplace add + plugin install both succeed; the plugin lands in a separate pinned cache copy |
| The installed plugin exposes what the manifest declares | pass | `claude plugin details` lists exactly 10 skills and 3 agents, equal to the manifest's 13 components; 0 hooks, 0 MCP servers; always-on cost ~1,728 tokens |
| The driver works from an installed copy | pass | all ten lazily-read `references/*.md` resolve under the installed `skills/orchestrate/references/` — the one packaging assumption research could not observe |
| A contributor installs the commit gate from scratch | pass | `.pre-commit-config.yaml` validates, all six hooks resolve, and the repository is already normalised under them: `pre-commit run --all-files` leaves the tree clean, so the first contributor faces no mass rewrite |
| Each tool is still runnable after the rename | pass | `--help` exits 0 for all five; the three contributor self-tests all pass |
| A reader arrives at the repository front door | pass | `README.md` carries What this is / Install / Usage / Components / Pointers; `README.org` is gone; `LICENSE` and `CONTRIBUTING.md` are linked |
| An operator with a symlink install is warned | pass | `CONTRIBUTING.md` §The symlink hazard states the dangle at merge and names both remedies |

## Regressions

Regression base is the workstream branch point `merge-base(marketplace, main)` =
`7be04f8` (not `main` HEAD), per `ws-integration.md`.

- `git diff --shortstat 7be04f8 HEAD` — 93 files changed, 10,052 insertions, 686 deletions.
- Distribution: `docs/` 49, `skills/` 27, `tools/` 5, `agents/` 4, `.claude-plugin/` 2, and one each of `README.org`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CLAUDE.md`, `.pre-commit-config.yaml`.
- Deletions across the window: `README.org` and `agents/.gitkeep` — both intended and both specified.
- **None found.** No unintended path appears in the diff; the historical corpus (`docs/ws/` outside `marketplace`, `docs/research/`, `docs/superpowers/`) is untouched by the rename chunks; the drift sweep's 31 findings are the same 31 lines the Chunk 0 entry sweep recorded, so no sweep regression was introduced. No behavioural contract of any skill or of the driver changed — the `CLAUDE.md` diff confirms the phase-detection, cycle-identity and v4 sections moved by name substitution only, and the linter's 40 contract rows are unchanged end to end.

## Deferral-Backlog Screen (Step 5b)

Two enumerations, both evaluated at run time with the phrase table of
`requirements-artifacts.md` §`## Out of Scope` Discipline and the bracketed
dated-marker regex applied at `L` and `L-1` only.

The screen was run twice. Before this report existed, the glob
`docs/ws/*/verification.md` returned **6** paths and **6** rows were walked.
After it was written the same glob returned **7** paths and **7** rows were
walked. In both runs the rows-walked count equals the paths-returned count, and
both sides of that equality come from the same run. The table below is the
second, seven-row run.

| Path | Phrase hits | Live |
|---|---|---|
| `docs/ws/default/verification.md` | 3 | 0 |
| `docs/ws/harness-p2/verification.md` | 0 | 0 |
| `docs/ws/harness-p3/verification.md` | 12 | 0 |
| `docs/ws/harness-p4/verification.md` | 5 | 0 |
| `docs/ws/harness-p5/verification.md` | 6 | 0 |
| `docs/ws/harness-p6/verification.md` | 0 | 0 |
| `docs/ws/marketplace/verification.md` (this report) | 0 | 0 |
| `docs/requirements/index.md` §Out of Scope | 0 | 0 |

Phrase coverage is a **screen over observed backlog vocabulary, not a proof of
absence**: a deferral written in vocabulary no cycle has used yet passes it. The
zero above is therefore the absence of a *detected* deferral, not an assertion
that no latent work exists.

## Issues Found

### Red round (2026-09-21) — round 1, four `BROKEN`, all fixed

`RED_VERDICT: BROKEN`. Four criteria fell to reproducible attacks. Each was
repaired in a single implement re-dispatch (`RED_BREAK` packet, iteration 1 of
3); the disposition below records, per `Rn`, the evidence that its own
`reproduce:` command no longer demonstrates the break. The frontmatter stays
`status: pending-red` — the orchestrator performs the `pending-red → pass` flip
at the DONE gate.

- **R1 — fixed.** The retired-prefix rule's population omitted `agents/`,
  `.pre-commit-config.yaml` and `LICENSE`, so bare retired names injected there
  linted clean. The rule's live scope now enumerates `skills/`, `tools/`,
  `agents/`, `.claude-plugin/`, `docs/spec/`, `docs/requirements/`, `CLAUDE.md`,
  both READMEs, `CONTRIBUTING.md`, `LICENSE` and `.pre-commit-config.yaml`;
  `docs/spec/skill-namespace-rename.md`, `docs/requirements/integration/naming.md`
  and the rule's own comment were reworded with the code (the "exactly six areas"
  wording predates `agents/`), and the growth is recorded as
  Q-IMPL-MARKETPLACE-022.
  *Evidence*: the break's own command — inject the two bare names into an archive
  of `HEAD` and lint it — previously exited 0 with no finding; it now prints
  `agents/reviewer.md:56: [retired-prefix] \`sdd-verify\`` and
  `.pre-commit-config.yaml:51: [retired-prefix] \`sdd-gc\`` and exits 1.
- **R2 — fixed.** `--self-test` asserted that the rule *fires* but never which
  population it fires over, so gutting `RETIRED_SCOPE_DIRS` still passed. The
  suite gained block 9b: it carries its **own** literal enumeration of the
  policed areas (independent of the constants the rule reads, or the assertion
  would shrink with the mutation), asserts the rule's constants equal it, seeds
  one bare occurrence in every area and requires one finding per non-exempt area
  — the self-exempt `CONTRIBUTING.md` is seeded and silent, so the exemption is
  exercised against a walked area (Q-IMPL-MARKETPLACE-023).
  *Evidence by mutation*: the break's own command — set `RETIRED_SCOPE_DIRS` to
  `("docs/spec",)` and `RETIRED_SCOPE_FILES` to `()` in a scratch copy — used to
  print `SELF-TEST OK`; it now exits 1 with `scope dirs drifted from the policed
  population`, `scope files drifted …` and one `seeded but unwalked` line per
  deleted area. The unmutated suite exits 0.
- **R5 — fixed (with one residual, recorded as a Minor below).** No skill body
  reached the bundled tool copies: every invocation was cwd-relative
  `python3 tools/gc.py`, so the byte-identical copies were unreachable and the
  `cmp` / `test ! -L` criteria measured the copies' properties rather than
  whether anything resolves to them. The driver skill's eight drift-sweep
  invocations now name the script as `<skill-dir>/tools/gc.py` —
  skill-directory-relative, with `<skill-dir>` defined in the skill body as the
  directory holding its `SKILL.md` — and keep the explicit `--root .`, so the
  binary comes from the plugin and the subject stays the operator's repository
  (Q-IMPL-MARKETPLACE-024). The plugin-root environment variable is **not** used:
  `docs/spec/marketplace-packaging.md` §No skill body depends on the plugin-root
  variable forbids a skill body from depending on it. A criterion measuring
  resolution — the one R5 showed was missing — was added to that spec's
  `## Acceptance Criteria`.
  *Evidence*: substituting `<skill-dir>` = `skills/orchestrate` in a skill-side
  invocation yields `skills/orchestrate/tools/gc.py`, which exists; run from a
  consumer repository that has no `tools/` directory, the bundled path now
  *executes* (it reports on the consumer's own tree) where the previous spelling
  died with `can't open file '<consumer>/tools/gc.py'`. The break's literal grep
  for `skills/orchestrate/tools` under `skills/` stays empty by design — that
  absolute cross-skill spelling is the form REQ-NAME-MARKETPLACE-002 forbids; the
  resolving form is the `<skill-dir>`-relative one, and it is what the new
  criterion measures.
- **R8 — fixed.** The RED TEAM dispatch template restated all three of the agent
  file's judging rules in substance, violating REQ-AGENT-MARKETPLACE-006's
  no-duplication invariant; the criterion survived only because
  "role-definition paragraphs" is a human-judgement population. The template's
  `Rules:` line now cites `agents/red-team.md` §How you judge as the single
  source and says the rules are not restated. Because the linter's
  `template-drift` rule pins the template byte-for-byte against
  `docs/spec/adversarial-verify.md` §Red Dispatch Template, the identical edit was
  mirrored into that spec (Q-IMPL-MARKETPLACE-025), exactly as an earlier chunk
  did for two other specs. The criterion in `docs/spec/harness-agents.md` and in
  REQ-AGENT-MARKETPLACE-006 was restated as a run-time shingle comparison so its
  population is derived rather than judged.
  *Evidence*: the break's own command shows the three-line `Rules:` block replaced
  by the one-line citation, and a run-time shingle comparison of the agent's
  `## How you judge` section against the template body reports **0** shared
  eight-word sequences. `python3 tools/skill-lint.py` exits 0, so the
  `template-drift` pair is still byte-identical.

After the repairs: `python3 tools/skill-lint.py` → `OK: 25 file(s) clean`
(exit 0); `python3 tools/skill-lint.py --self-test` → `SELF-TEST OK` (exit 0);
`python3 tools/gc.py --report --root .` → exit 0, and its only warning
(`[traceability-aggregate]`) is the designed handshake between the
per-workstream write and the orchestrator's post-gate regeneration
(`docs/spec/ws-traceability.md` §Aggregate Regeneration Ownership) — no finding
is attributable to these repairs.

### Critical (blocks release)

- None.

### Material

- None.

### Minor (can ship, fix later)

- **[closed 2026-09-21 — operator decision: accept and document; recorded as `Q-IMPL-MARKETPLACE-020`]** The installed plugin carries `docs/` (144 files, 48,462 lines) because `"source": "./"` materialises the whole repository tree. This is an **accepted cost, not a correctness defect**: the component list governs what Claude Code *loads*, not what an install *copies*; `claude plugin details` reports zero components from `docs/`; and every `docs/` citation in a skill body is a bare relative path that resolves against the operator's own project. The over-claiming text in `docs/requirements/integration/packaging.md` and `docs/spec/marketplace-packaging.md` was corrected in-cycle to state what the component list actually governs.
- `CLAUDE.md:251` says marker `3` is "what this repo uses today" while `CLAUDE.md:215` says the repository migrated to marker `4` on 2026-09-17. Pre-existing contradiction, inherited from before this cycle; left alone because §Multi-Workstream Layout (v4) is one of the sections this cycle was forbidden to change in substance (`project-docs.md` §`CLAUDE.md`).
- Two behaviour-neutral stale spellings of the deleted front door's filename: `docs/spec/orchestration.md:574` names the project README by its retired `.org` filename in backticked prose (passes the sweep by the backtick skip rule, factually stale), and `tools/skill-lint.py:374` still lists that filename in `RETIRED_SCOPE_FILES` (`Q-IMPL-MARKETPLACE-017`) — harmless, since the walk simply never finds a file by that name.
- **[closed 2026-09-21 — operator decision: bundle the linter and add the
  provenance conditional; recorded as Q-IMPL-MARKETPLACE-026]** Residual of R5.
  With the bundled sweep reachable, a consumer-repository run got further and
  then exited 2 with `error: linter missing — expected <root>/tools/skill-lint.py`.
  The operator was shown the cost — it amends REQ-PKG-MARKETPLACE-007, a
  criterion the red round had already verified — and chose it over both bundling
  the linter alone and deferring. Two changes landed: `tools/skill-lint.py` is
  bundled beside the bundled sweep as a regular byte-identical file (`cmp` exit
  0, `test ! -L` succeeds), still **absent from the plugin's component list**, so
  REQ-PKG-MARKETPLACE-005 is untouched — it is bundled as a file, not declared as
  a component; and `tools/gc.py` gained one **provenance conditional**: when the
  linter it resolves is a sibling of the running script and that sibling
  directory is not the subject root's own `tools/`, the linter runs with this
  repository's suite-specific contract rows off. Bundling the linter *alone* was
  rejected because it turns a clean failure into a **misleading success**: the
  consumer run then reports 40 `[required]` "file missing entirely" findings
  drawn from this repository's contract rows, which an operator cannot tell from
  real ones. REQ-PKG-MARKETPLACE-007's freeze is narrowed, not dropped — the
  telemetry tool's source stays frozen unconditionally, the sweep's source is
  frozen apart from this conditional — and a criterion measuring a
  consumer-repository run was added, because that is the object the old criterion
  did not measure.
  *Evidence, each with its command.* Freeze: `git diff 3ddfdb3 HEAD -- tools/telemetry.py`
  is empty (0 lines); `git diff 3ddfdb3 HEAD -- tools/gc.py` shows exactly one
  hunk — the `bundled_run()` helper, its use in `lint_command()`, and the
  adjacent comment — and no other. Consumer repository: a scratch git repo under
  `$TMPDIR` with a `docs/` corpus (marker `4`, one requirement, one spec, one
  `docs/ws/default/plan.md`, one `skills/mine/SKILL.md`) and **no** `tools/`
  directory, swept with the driver's documented invocation
  `python3 <skill-dir>/tools/gc.py --report --root .` from inside that repo, exits
  **1** (not 2) with finding classes `[index-requirements]` ×1 and
  `[traceability-aggregate]` ×1 — both derived from the consumer's own corpus,
  **none** from this repository's contract rows. The same repo swept by the
  pre-change bundled script plus a bundled linter exits 1 with 41 findings,
  40 of them `[required]`. (A consumer with no `skills/` directory additionally
  gets one `[structure] skills/ directory not found`, also consumer-derived.)
  This repository unchanged: `python3 tools/gc.py --report --root .` exits 0,
  `9 sweep(s) clean, 1 warning(s), 31 info`, and its output is **byte-identical**
  to the pre-change script's output on the same tree (`diff` empty, the
  pre-change script recovered with `git show HEAD:tools/gc.py`); against the
  recorded Chunk 0 entry sweep the only differences are the three already-recorded
  pre-existing ones (the designed `[traceability-aggregate]` handshake warning, one
  line-number shift in `adversarial-verify.md`, and the `sdd-specs` → `specs`
  rename inside a fix hint) — 31 info findings on both sides, 0 fail.
  Self-tests: `python3 tools/gc.py --self-test`, `python3 tools/skill-lint.py`
  and `python3 tools/skill-lint.py --self-test` each exit 0. All three bundled
  copies `cmp` clean against their root originals and each `test ! -L` succeeds.
- `pre-commit run --all-files` cannot complete `end-of-file-fixer` in this sandbox: the hook opens `.claude/settings.json` with `rb+` and the sandbox denies write to that path. A **sandbox artefact, not a repository defect** — the file already ends in `\n`, so the hook is a no-op outside the sandbox, and the other five hooks pass with a clean tree.

No previous `docs/ws/marketplace/verification.md` existed, so the carry-or-close
rule for unresolved Minors has no prior report to read: `marketplace` is this
workstream's first cycle.

## Recommendation

- [x] Ship as-is — subject to the outstanding red round. `status:` is `pending-red`; the orchestrator dispatches the red team, gates, and flips `pending-red -> pass` before its own commit.
- [ ] Fix critical issues then ship (invoke sdd-replan)
- [ ] Significant rework needed (invoke sdd-replan)

The cycle's terminal state is reached: branch `marketplace` is pushed
(`git ls-remote origin marketplace` = `56a858a` at the time of the push record),
PR #4 against `main` is **open and unmerged**, and no attribution trailer appears
in the PR body or in any of the cycle's commits.

## Next Steps

- **[closed 2026-09-21 — operator decision: accept and document]** Moving `docs/` outside the installed tree: the component list cannot express the exclusion, so a criterion written against the manifest passes while the condition persists — any future assertion must be made against the **materialised install tree**, not the manifest. Cheapest path first: establish whether an exclusion declaration exists before considering a subdirectory plugin root. Recorded as `Q-IMPL-MARKETPLACE-020`.
- gc note: `docs/spec/orchestration.md:574` — name the project README by its current filename.
- gc note: `tools/skill-lint.py:374` — drop the deleted front door's filename from `RETIRED_SCOPE_FILES` (`Q-IMPL-MARKETPLACE-017`); behaviour-neutral.
- gc note: `CLAUDE.md:251` — reconcile with `CLAUDE.md:215` on which marker the repository uses; blocked in this cycle by the must-not-change-in-substance fence on that section.
- `Q-IMPL-MARKETPLACE-021` (informational): a local-path install copies the working tree verbatim, including gitignored content such as `.sdd/telemetry.jsonl`. A property of this verification mechanism only, never of a user installing from the marketplace.
