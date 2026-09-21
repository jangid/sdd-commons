---
workstream: marketplace
last_updated: 2026-09-21
---

# Traceability — marketplace

Rows owned by the `marketplace` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd-specs`, `sdd-implement` and `sdd-verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited, and never by a leaf: regeneration is the
orchestrator's post-gate bookkeeping.

`Verified` takes the values of `docs/spec/ws-traceability.md` §Legal `Verified`
Cell Values — `pass | fail | pass | descoped`. The DONE rule for this
cycle (kickoff §Decided at DISCUSS — "replan as needed and finish everything"):
every row reads `pass`. Nothing closes as a deliberate `fail`, and nothing is
carried forward to a later cycle; an item that cannot be delivered is rescoped
inside this cycle by replan.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-AGENT-MARKETPLACE-001 | harness-agents.md | marketplace | Chunk 4 task 7 — `agents/` holds exactly 3 `*.md`, no subdir, no `.gitkeep`, stems kebab-case | `agents/chunk-verifier.md`, `agents/red-team.md`, `agents/reviewer.md` | pass |
| REQ-AGENT-MARKETPLACE-002 | harness-agents.md | marketplace | Chunk 4 task 7 — frontmatter parsed per file; `tools` free of `Write`/`Edit`/`NotebookEdit`; dropped-key grep zero | `agents/*.md` frontmatter | pass |
| REQ-AGENT-MARKETPLACE-003 | harness-agents.md | marketplace | Chunk 4 task 7 — five-field list parsed from `CLAUDE.md` §Agents | `CLAUDE.md` §Agents | pass |
| REQ-AGENT-MARKETPLACE-004 | harness-agents.md | marketplace | Chunk 4 task 8 — token file-set superset check at `3ddfdb3` vs HEAD; linter + `--self-test` exit 0 | `agents/*.md` token lines; `tools/skill-lint.py` | pass |
| REQ-AGENT-MARKETPLACE-005 | harness-agents.md | marketplace | Chunk 4 task 9 — both citation forms inside one template block, per role | `skills/orchestrate/references/dispatch-templates.md` | pass |
| REQ-AGENT-MARKETPLACE-006 | harness-agents.md | marketplace | Chunk 4 task 8 — no shared role-definition sentence; `RETURN:` blocks retained; contract-row count unchanged | `agents/*.md` + `dispatch-templates.md` | pass |
| REQ-DOCS-MARKETPLACE-001 | project-docs.md | marketplace | Chunk 6 task 8 — MIT first line + named holder; `license` parsed from plugin manifest | `LICENSE`, `.claude-plugin/plugin.json` | pass |
| REQ-DOCS-MARKETPLACE-002 | project-docs.md | marketplace | Chunk 6 task 6 — README↔manifest name equality (13 == 13), Usage heading parsed | `README.md` | pass |
| REQ-DOCS-MARKETPLACE-003 | project-docs.md | marketplace | Chunk 6 task 7 — retired front door absent; deletion visible at `1b6295a` | `README.md` (replaces the deleted `.org` front door) | pass |
| REQ-DOCS-MARKETPLACE-004 | project-docs.md | marketplace | Chunk 6 task 8 — four owed statements present as sections; cross-spec criteria re-run | `CONTRIBUTING.md` | pass |
| REQ-DOCS-MARKETPLACE-005 | project-docs.md | marketplace | Chunk 6 task 9 — retired-prefix grep zero; both manifest paths named; diff shows only name substitution outside the three edited sections | `CLAUDE.md` | pass |
| REQ-NAME-MARKETPLACE-001 | skill-namespace-rename.md | marketplace | Chunk 1 task 4 — 10 skill dirs, basename free of retired prefix, frontmatter `name` == basename | `skills/*/SKILL.md` | pass |
| REQ-NAME-MARKETPLACE-002 | skill-namespace-rename.md | marketplace | Chunk 1 task 4 — cross-skill path-reference greps return zero | `skills/**/*.md` | pass |
| REQ-NAME-MARKETPLACE-003 | skill-namespace-rename.md | marketplace | Chunk 1 tasks 4–5 — `--help` exit 0 per tool; self-reference grep zero; `git log --follow` resolves each tool | `tools/*.py` | pass |
| REQ-NAME-MARKETPLACE-004 | skill-namespace-rename.md | marketplace | Chunk 2 task 5 — retired-name scan over the six live areas = 0 | `docs/spec/`, `docs/requirements/`, `CLAUDE.md`, `README.md`, `skills/`, `tools/` | pass |
| REQ-NAME-MARKETPLACE-005 | skill-namespace-rename.md | marketplace | Chunk 2 tasks 5–6 — historical areas retain 497 occurrences; Chunk 1–2 diff lists no path under them | historical corpus left untouched (exclusion) | pass |
| REQ-NAME-MARKETPLACE-006 | skill-namespace-rename.md | marketplace | Chunk 6 task 8 — naming-boundary statement read from the file | `CONTRIBUTING.md` §The naming boundary | pass |
| REQ-NAME-MARKETPLACE-007 | skill-namespace-rename.md | marketplace | Chunk 3 task 7 — at `3ddfdb3`: no `.claude-plugin/` path, linter 0, sweep finding set == entry sweep | plan chunk order (1–3 before 5); `3ddfdb3` | pass |
| REQ-NAME-MARKETPLACE-008 | skill-namespace-rename.md | marketplace | Chunk 2 task 7 — prefixed `skills/` literal grep zero; REQUIRED contract rows 40 == 40 across the rename | `tools/skill-lint.py` | pass |
| REQ-NAME-MARKETPLACE-009 | skill-namespace-rename.md | marketplace | Chunk 2 tasks 2–3 — synthesized 4-occurrence fixture yields exactly 1 flag; live repository 0 | `tools/skill-lint.py` retired-prefix rule + `--self-test` | pass |
| REQ-NAME-MARKETPLACE-010 | skill-namespace-rename.md | marketplace | Chunk 6 task 8 — symlink hazard, dangle statement and both operator actions; `index.md` §Out of Scope post-DONE step | `CONTRIBUTING.md` §The symlink hazard; `docs/requirements/index.md` §Out of Scope | pass |
| REQ-PC-MARKETPLACE-001 | pre-commit.md | marketplace | Chunk 3 task 4 — `pre-commit validate-config` exit 0; parsed id set == the six-id set **[superseded 2026-09-21 by the packaging cycle — the set is now closed at eight; see docs/ws/packaging/traceability.md]** | `.pre-commit-config.yaml` | pass |
| REQ-PC-MARKETPLACE-002 | pre-commit.md | marketplace | Chunk 3 tasks 4, 6 — both local hooks `pass_filenames: false` / `always_run: true`; scratch-copy violation exits non-zero; both hooks exit 0 at close | `.pre-commit-config.yaml` local repo entry | pass |
| REQ-PC-MARKETPLACE-003 | pre-commit.md | marketplace | Chunk 3 task 4 / Chunk 7 task 3 — four hygiene ids under `pre-commit-hooks` at `rev: v6.0.0` | `.pre-commit-config.yaml` upstream repo entry | pass |
| REQ-PC-MARKETPLACE-004 | pre-commit.md | marketplace | Chunk 3 task 4 + Chunk 6 task 8 — config grep for the three contributor tools = 0; all three named with commands in CONTRIBUTING | `.pre-commit-config.yaml`; `CONTRIBUTING.md` §The three heavier checks | pass |
| REQ-PC-MARKETPLACE-005 | pre-commit.md | marketplace | Chunk 3 task 5 / Chunk 7 task 3 — tree clean after re-run; `git diff d1ef8f2 HEAD -- tools/fixtures/` empty; four excludes each with a reason comment | `.pre-commit-config.yaml` `exclude:`; normalisation committed at `3ddfdb3` | pass |
| REQ-PC-MARKETPLACE-006 | pre-commit.md | marketplace | Chunk 3 task 4 — every entry is one of the six; no `args:` key in the config **[superseded 2026-09-21 — re-checked against the eight-entry set; see docs/ws/packaging/traceability.md]** | `.pre-commit-config.yaml` | pass |
| REQ-PKG-MARKETPLACE-001 | marketplace-packaging.md | marketplace | Chunk 5 task 8 — parsed `name` == `sdd-commons`, `owner` present, one plugin entry `sdd` | `.claude-plugin/marketplace.json` | pass |
| REQ-PKG-MARKETPLACE-002 | marketplace-packaging.md | marketplace | Chunk 5 task 8 — `source` == `./`; plugin manifest carries name/description/version; `test ! -d plugins` | `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json` | pass |
| REQ-PKG-MARKETPLACE-003 | marketplace-packaging.md | marketplace | Chunk 5 task 8 — derived set equality: skills 10 == 10, agents 3 == 3; no listed path under `docs/` | `.claude-plugin/marketplace.json` component list | pass |
| REQ-PKG-MARKETPLACE-004 | marketplace-packaging.md | marketplace | Chunk 5 task 9 — absolute/home/plugin-root `docs/` citation grep over `skills/` = 0 | `skills/**/*.md` bare relative `docs/` citations | pass |
| REQ-PKG-MARKETPLACE-005 | marketplace-packaging.md | marketplace | Chunk 5 task 9 — contributor-tool invocation grep over `skills/` = 0; none in the component list | component list by absence; `skills/**/*.md` | pass |
| REQ-PKG-MARKETPLACE-006 | marketplace-packaging.md | marketplace | Chunk 5 tasks 10–11 — `cmp` exit 0 and `test ! -L` for both copies; `ls tools/*.py` 5 >= 5 at `d1ef8f2`; `git log --follow` resolves all five | `skills/orchestrate/tools/gc.py`, `skills/orchestrate/tools/telemetry.py` | pass |
| REQ-PKG-MARKETPLACE-007 | marketplace-packaging.md | marketplace | Chunk 5 task 10 / Chunk 7 task 3 — 9/9 sweep invocations carry an explicit root; `git diff 3ddfdb3 HEAD -- tools/gc.py tools/telemetry.py` empty | `skills/**/*.md` invocation sites | pass |
| REQ-PKG-MARKETPLACE-008 | marketplace-packaging.md | marketplace | Chunk 5 task 9 — plugin-root variable outside a fenced block over `skills/**/*.md` = 0 | `skills/**/*.md` | pass |
| REQ-PKG-MARKETPLACE-009 | marketplace-packaging.md | marketplace | Chunk 5 task 12 + Chunk 6 task 8 — `docs/spec/*.md` citation count 150 == 150 across the packaging change; CONTRIBUTING paragraph present | `CONTRIBUTING.md` §Where the contracts live | pass |
| REQ-PKG-MARKETPLACE-010 | marketplace-packaging.md | marketplace | Chunk 7 task 2 — real install by the operator; 10 skills + 3 agents listed; all ten `references/*.md` resolve from the installed copy | `.claude-plugin/` manifest pair as installed at cache sha `0d2d71e` | pass |
