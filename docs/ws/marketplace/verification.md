---
workstream: marketplace
status: pending-red
research_id: RS-MARKETPLACE-001
last_updated: 2026-09-21
plan_ref: docs/ws/marketplace/plan.md
---

# Verification Report — marketplace

## Summary

**This is a re-verification at `d2741f1`, not the first pass.** The first pass
ran at `a576316`; since then a red round found four breaks, all four were
repaired, and an operator-directed change made the bundled drift sweep usable
from a consumer repository. Four acceptance criteria were **amended** by those
repairs, so the earlier pass's assertions about them no longer describe what the
criteria say. Every one of the 37 `REQ-*-MARKETPLACE-*` requirements has been
re-walked against the criteria **as they now read**, with both sides of every
comparison derived at run time and no corpus count carried forward as a literal.

Result: **37/37 pass, 0 Critical, 0 Material, 6 Minor.** The eight plan chunks
are complete (59 typed tasks, all `[x]`, 0 open), the quality gates are green,
and the regression diff against the workstream branch point `7be04f8` is 95
files with no path outside this cycle's declared areas. Two assertions the first
pass made are no longer true as written and are corrected here rather than
repeated: the bundled tools are no longer byte-frozen against `3ddfdb3` (the
sweep carries one provenance conditional, which is exactly what the narrowed
REQ-PKG-MARKETPLACE-007 now permits), and the skill-body spec-citation count is
151 at HEAD rather than 150 — the one added citation arrived with the red repair,
**after** the packaging change the criterion is scoped to, which still measures
150 == 150. Two new Minors are recorded that the first pass did not have.

`status:` is `pending-red` because the dispatch carries `Red team: enabled`:
blue passes, the red verdict is outstanding, and the orchestrator flips
`pending-red → pass` at the DONE gate. This skill never writes `pass` while a
red round is open.

## Quality Gates

All run from the worktree root at `d2741f1`, with nested `.worktrees/` and
`.git/` pruned on **relative** path parts.

| Gate | Status | Notes |
|------|--------|-------|
| Skill linter (`python3 tools/skill-lint.py`) | pass | `OK: 25 file(s) clean`, exit 0 |
| Skill linter self-test (`--self-test`) | pass | `SELF-TEST OK: all rule classes fire; fix/warn/size/backtick/allow_files/retired-prefix fixtures pass`, exit 0 |
| Drift sweep (`python3 tools/gc.py --report --root .`) | pass | exit 0; `OK: 9 sweep(s) clean, 1 warning(s), 31 info` |
| Drift sweep vs. the recorded entry sweep | pass | finding **lines** compared both ways against `/tmp/claude-501/chunk0-entry-sweep.txt`: 31 info on both sides, 0 fail on both sides. Exactly two differences, both accounted for — one line-number shift (`docs/spec/adversarial-verify.md:606 → :610`, same `[qimpl-unreferenced]` finding) and the `[traceability-aggregate]` warning, which is the designed handshake with the orchestrator's post-gate regeneration |
| Drift sweep self-test (`--self-test`) | pass | `SELF-TEST OK: sweeps 5-14 fire once each …`, exit 0 |
| `pre-commit validate-config .pre-commit-config.yaml` | pass | exit 0 |
| `pre-commit run --all-files` | pass with a sandbox artefact | `drift sweep (fast profile)`, `skill linter`, `trim trailing whitespace`, `check yaml`, `check json` all **Passed**; `end-of-file-fixer` raised `PermissionError: [Errno 1] Operation not permitted: '.claude/settings.json'` opening the file `rb+`. That path is sandbox-protected in this session; `tail -c 1` on it is `0a`, so the hook is a no-op outside the sandbox. Working tree clean after the run |
| `python3 tools/scope-check-selftest.py` | pass | `OK: 44/44 scenarios passed` |
| `python3 tools/telemetry.py --self-test` | pass | full self-test OK; frozen p3/p4 fixture sha256 unchanged |
| `python3 tools/eval.py --self-test` | pass | `6 records, 9 fields, aggregate, empty/missing file, csv` |

## The Four Amended Criteria — Re-Derived Explicitly

The red round rewrote four criteria. Each is re-derived here against its
**current** text, independently of the first pass.

### 1. REQ-PKG-MARKETPLACE-007 — narrowed freeze (`Q-IMPL-MARKETPLACE-026`)

The criterion no longer says both bundled tools are byte-frozen from the
rename-chunk close. It now says the **telemetry tool's source is frozen
outright** and the **drift sweep's source is frozen apart from one provenance
conditional**, with no other hunk.

- `git diff 3ddfdb3 -- tools/telemetry.py` → **0 lines**. Frozen outright: holds.
- `git diff 3ddfdb3 -- tools/gc.py` → **one hunk, 16 lines changed**, and that
  hunk is exactly the provenance conditional: the added `bundled_run(self, lint)`
  helper (which returns true when the linter was resolved as a sibling of the
  running script and that sibling directory is not the subject root's own
  `tools/`), its single use as `if self.lint_suite_rules and not
  self.bundled_run(lint):` in `lint_command()`, and the adjacent comment
  rewritten from `# Fixture mode:` to `# Fixture mode / bundled run:`. No other
  hunk in the file. Frozen apart from the conditional: holds.
- **Verdict: pass.** The freeze is narrowed, not dropped, and what remains is
  exactly what the criterion now permits.

### 2. REQ-NAME-MARKETPLACE-004 — the live scope grew past "six areas" (`Q-IMPL-MARKETPLACE-022`)

The criterion requires the enumeration to be **read from the enforcing rule
itself, never retyped**, and the stated and enforced scopes to agree. Both sides
derived:

- **Enforced**, imported live from `tools/skill-lint.py`:
  `RETIRED_SCOPE_DIRS = ('skills', 'tools', 'agents', '.claude-plugin',
  'docs/spec', 'docs/requirements')`;
  `RETIRED_SCOPE_FILES = ('CLAUDE.md', 'README.md', 'README.org',
  'CONTRIBUTING.md', 'LICENSE', '.pre-commit-config.yaml')`.
- **Stated**, read from `docs/requirements/integration/naming.md`
  REQ-NAME-MARKETPLACE-004: `skills/`, `tools/`, `agents/`, `.claude-plugin/`,
  `docs/spec/`, `docs/requirements/`, `CLAUDE.md`, the README, `CONTRIBUTING.md`,
  `LICENSE`, `.pre-commit-config.yaml`.
- **Agreement**: the two sets are equal once "the README" is resolved. The
  enforced set carries the README in both spellings (`README.md` and the deleted
  `README.org`); `enforced \ stated = {README.org}`, which is the already-recorded
  stale entry (`Q-IMPL-MARKETPLACE-017`, Minor below). `agents/`,
  `.claude-plugin/`, `CONTRIBUTING.md`, `LICENSE` and `.pre-commit-config.yaml`
  — the five areas the original "six areas" omitted — are present on **both**
  sides.
- Running the rule live over that scope (`Linter(root, suite_rules=False)
  .check_retired_prefix()`) yields **0 findings**; the exemption set is
  `('CONTRIBUTING.md', 'docs/requirements/integration/naming.md',
  'tools/skill-lint.py', 'docs/spec/skill-namespace-rename.md')`.
- **Verdict: pass.** Enforced scope and stated scope agree, both derived.

### 3. REQ-NAME-MARKETPLACE-009 — the self-test asserts the policed population (`Q-IMPL-MARKETPLACE-023`)

The criterion no longer settles for "the rule fires". It now requires the
self-test to assert the **population the rule fires over**, against an
enumeration the fixture carries independently, "so that deleting an area from the
rule's scope makes `--self-test` exit non-zero (demonstrated by mutation)".

*Verified by mutation, executed here.* A scratch copy of `tools/skill-lint.py`
with `RETIRED_SCOPE_DIRS` gutted to `("docs/spec",)` and `RETIRED_SCOPE_FILES`
gutted to `()`:

```
SELF-TEST FAIL:
- retired-prefix scope dirs drifted from the policed population: ('docs/spec',) != (…six…)
- retired-prefix scope files drifted from the policed population: () != (…six…)
- policed area .claude-plugin/seeded.md produced no retired-prefix finding — the area is seeded but unwalked
  … (one such line per deleted area: .pre-commit-config.yaml, CLAUDE.md, LICENSE,
     README.md, README.org, agents/, docs/requirements/, skills/, tools/)
- expected one retired-prefix finding per policed area (11), got 1
exit=1
```

The unmutated suite exits 0. Eleven expected findings over twelve seeded areas —
`CONTRIBUTING.md` is seeded and silent, which exercises the self-exemption
against a walked area rather than against an unwalked one.

- **Verdict: pass.** Gutting the scope now fails the suite loudly; before the
  repair it printed `SELF-TEST OK`.

### 4. REQ-AGENT-MARKETPLACE-006 — no-duplication is a run-time shingle comparison (`Q-IMPL-MARKETPLACE-025`)

The criterion no longer rests on the human-judgement population
"role-definition paragraphs". It now requires that, for each agent/template
pair, **no normalised eight-word sequence** from the agent file's rule section
occurs in the template.

Re-derived for **all three** role/template pairs, both sides read from disk,
normalised for case and whitespace, template blocks split from the file's own
`##` headings:

| Agent file, rule section | Dispatch template block | Shared 8-word shingles |
|---|---|---|
| `agents/chunk-verifier.md` §How you judge | `## CHUNK VERIFIER subagent template (read-only leaf)` | **0** |
| `agents/red-team.md` §How you judge | `## RED TEAM subagent template (read-only leaf, verify stage only)` | **0** |
| `agents/reviewer.md` §How you judge | `## REVIEW subagent template (isolation-critical)` | **0** |

The rest of the criterion holds with it: **5** `RETURN:` blocks remain in
`dispatch-templates.md` and the linter's `template-drift` rule (which pins each
template byte-for-byte against its spec) exits 0; REQUIRED contract rows are
**40** before and after the extraction (below).

- **Verdict: pass**, on a derived population rather than a judged one.

## The New Consumer-Repository Criterion — Re-Measured

REQ-PKG-MARKETPLACE-007 gained a criterion the old one did not measure: a
scratch consumer repository with a `docs/` corpus and **no** `tools/` directory,
swept with the driver skill's documented bundled invocation, must exit non-2
and raise no finding from a rule keyed to this repository's contract rows. The
earlier measurement was **not** taken on trust; a fresh scratch repository was
built and swept here.

*The scratch repository*: a fresh `git init` under `$TMPDIR` with
`docs/.sdd-version` = `4`, `docs/requirements/index.md` (one requirement,
`REQ-APP-DEFAULT-001`), `docs/requirements/functional/app.md`, `docs/spec/app.md`,
`docs/ws/default/plan.md`, `docs/ws/default/traceability.md`, and one
`skills/mine/SKILL.md`. `test -d tools` → **NO**.

*The run*, in the driver's documented form (`skills/orchestrate/SKILL.md:42`
spells it `python3 <skill-dir>/tools/gc.py --report --root .`, `<skill-dir>`
being the directory holding the skill's own `SKILL.md`):

```
$ python3 <worktree>/skills/orchestrate/tools/gc.py --report --root .
skills/mine/SKILL.md:1: [description] description never states when NOT to use the skill (repo quality check)
WARN docs/requirements/traceability.md: [traceability-aggregate] aggregate differs from regenerate(docs/ws/*/traceability.md)
docs/requirements/index.md: [index-requirements] functional/app.md has no Files-table row
FAIL: 2 finding(s), 1 warning(s), 0 info
exit=1
```

- **exit 1, not 2** — the criterion's "does not exit 2" holds.
- Three findings, classes `[description]`, `[traceability-aggregate]`,
  `[index-requirements]`. **Every one is derived from the consumer's own corpus**
  — its skill's description, its own missing aggregate, its own index table.
  **None** comes from a rule keyed to this repository's contract rows.

*Counterfactual, measured rather than assumed.* The same scratch repository
swept by the **pre-change** script (`git show 3ddfdb3:tools/gc.py`) with the
linter bundled beside it: `FAIL: 42 finding(s), 1 warning(s), 0 info`, of which
**40 are `[required]`** — this repository's contract rows reported as missing
files in a stranger's tree. That is the misleading success the provenance
conditional exists to prevent, and it confirms the conditional is load-bearing,
not decorative.

*This repository unchanged.* `python3 tools/gc.py --report --root .` exits 0 with
`9 sweep(s) clean, 1 warning(s), 31 info`; its finding **lines** were compared
both ways against the recorded Chunk 0 entry sweep — 31 info on each side, the
only two differences a line-number shift and the designed
`[traceability-aggregate]` handshake warning (see §Quality Gates).

## Red Round 2 — Dispositions

Four breaks (`R1`, `R2`, `R4`, `R5`); all four **fixed**, none accepted. Each is
recorded with the command that proves it, re-run after the repair. All mutation
happened in `$TMPDIR` clones; the worktree was never mutated.

### R1 (BROKEN → fixed) — the provenance conditional took the OFF branch inside this repository

`Gc.bundled_run()` keyed on where the running **script** lived, so the bundled
copy sweeping **this** repository — the invocation the driver skill documents —
silently disabled this repository's own REQUIRED and version-gate contract rows.

**Fix**: the predicate is keyed to the **root being swept** — suite rules are on
iff `<root>/tools/skill-lint.py` is a file. `bundled_run()` is removed, not left
dead. Recorded as Q-IMPL-MARKETPLACE-027; the §One narrowing design text and the
REQ-PKG-MARKETPLACE-007 criterion's parenthetical were corrected with it.

`reproduce:` on a clean clone, break one skill's version-gate paragraph
(`perl -pi -e 's{docs/\.sdd-version}{docs/.SDD-VERSION-BROKEN}g' skills/implement/SKILL.md`),
then run both `python3 tools/gc.py --report --root .` and
`python3 skills/orchestrate/tools/gc.py --report --root .`.

| | root script | bundled copy |
|---|---|---|
| before the fix | `FAIL: 1 finding(s)` | `OK: 9 sweep(s) clean` |
| after the fix | `FAIL: 2 finding(s)` | `FAIL: 2 finding(s)` |

The two now agree by construction, and the bundled copy names the seeded
`skills/implement/SKILL.md: [required] never reads docs/.sdd-version`. (Two
findings rather than one because the same substitution also drops a REQUIRED
pattern below its minimum.)

**Consumer measurement re-confirmed**: a scratch `git`-initialised repository
with a `docs/` corpus and no `tools/` directory, swept with the bundled
invocation, exits **1** (non-2) and its rule set is `[structure]`,
`[traceability-aggregate]` — **no** finding from a rule keyed to this
repository's contract rows. The earlier repair still holds.

### R2 (BROKEN → fixed) — a literal count in the bundled-tool criterion

The REQ-PKG-MARKETPLACE-006 criterion pinned "the two bundled tools" while three
exist, leaving the bundled linter covered by no `cmp` and no `test ! -L`.

**Fix**: the criterion now derives its population at run time — every
`skills/*/tools/*.py` paired with the repository-root file of the same basename
— and states no count; the same derivation drives the new linter rule. The
§Tools design section was corrected with it: its heading no longer says "two",
its class table gains the linter as a **dependency of a bundled tool** (bundled,
not a plugin component), and the section states that no count is written down.

`reproduce:` `Linter(root).bundled_tool_pairs()` derives, at this close:

```
skills/orchestrate/tools/gc.py         <- tools/gc.py
skills/orchestrate/tools/skill-lint.py <- tools/skill-lint.py
skills/orchestrate/tools/telemetry.py  <- tools/telemetry.py
```

`cmp` exits 0 and `test ! -L` succeeds for all three derived pairs.

### R4 (BROKEN → fixed) — a false statement of the live freeze-window set

`pre-commit.md`'s impact paragraph asserted that the two bundled tool sources
`gc.py` and `telemetry.py` "do not appear in the window at all" — false now that
the linter is bundled and that the red rounds edited two of the three sources.

**Fix**: the paragraph is corrected, not the criterion. It now (a) says the set
is derived live and names no tool as the set, and (b) separates two properties
that were being conflated: *frozen across the packaging step* (true of every
derived source, and what the criterion protects) from *unchanged since the
rename close* (true of `tools/telemetry.py`, whose path-limited diff against
`3ddfdb3` is empty; **not** true of `tools/gc.py` and `tools/skill-lint.py`,
which are status `M` because the red rounds repaired them — legitimate
corrective work the criterion never covered, not packaging-step edits). No
criterion was weakened.

`reproduce:` `git diff 3ddfdb3 -- tools/telemetry.py` is empty;
`git diff 3ddfdb3 -- tools/gc.py | grep -c '^@@'` is **1**, so
REQ-PKG-MARKETPLACE-007's "the provenance conditional and no other hunk" still
holds over the drift sweep.

### R5 (BROKEN → fixed) — byte identity was asserted once and enforced by nothing

**Fix**: a `bundled-drift` **rule** in `tools/skill-lint.py` — not a seventh
pre-commit hook, so REQ-PC-MARKETPLACE-006's closed six-hook set stays closed and
the check still runs on every commit, because the linter is already a hook. The
rule derives the same population as R2 and raises one blocking finding per pair
that differs byte-for-byte, has no root source, or is a **symlink** (a link
compares equal to its source while resolving run-time paths from the source
directory — the property `test ! -L` exists for, and the property R1's old
predicate turned on). Recorded as Q-IMPL-MARKETPLACE-028.

`reproduce:` on a clean clone, `echo '# …' >> tools/telemetry.py`:

| | before the rule | after the rule |
|---|---|---|
| `tools/skill-lint.py` | exit **0** | exit **1**, `[bundled-drift]` naming the pair |
| `tools/gc.py --report` | exit **0** | the same finding, through the lint pass-through |
| `cmp` on the pair | exit 1 (drifted) | exit 1 (drifted) |

**Fixture bites by mutation**: replacing the rule's loop subject with an empty
list makes `python3 tools/skill-lint.py --self-test` exit **1** with three
failures — the drifted, the orphaned and the symlinked copy each reported silent
— and the identical-copy silence assertion keeps the fixture from passing
vacuously.

### Round 1 regression check — all four still hold

| Round 1 fix | `reproduce:` | outcome |
|---|---|---|
| retired-prefix rule reaches `agents/` | inject `sdd-review` bare into `agents/reviewer.md` in a `git archive` export | export baseline exit 0; after injection **exit 1**, `agents/reviewer.md:56 [retired-prefix]` |
| the self-test pins the policed population | gut `RETIRED_SCOPE_DIRS` to `("skills",)` | `--self-test` **exit 1**, scope-drift and per-area failures |
| agent role text is not duplicated from the templates | shingle-compare each agent's §How you judge against its template block | **0** shared normalised 8-word shingles for all three pairs |
| the templates keep their `RETURN:` blocks | count `RETURN:` in `dispatch-templates.md` | present and `template-drift` passes (linter exit 0) |

### Quality gates after the round-2 repairs

| Command | Exit |
|---|---|
| `python3 tools/skill-lint.py` | **0** — `OK: 25 file(s) clean` |
| `python3 tools/skill-lint.py --self-test` | **0** |
| `python3 tools/gc.py --report --root .` | **0** — `OK: 9 sweep(s) clean, 1 warning(s), 31 info` |
| `python3 tools/gc.py --self-test` | **0** |

One sweep line is absent from the cycle's entry sweep: the
`[traceability-aggregate]` warning on `docs/requirements/traceability.md`. It is
**pre-existing at `HEAD`**, not introduced by these repairs — reproduced on a
fresh clone of `HEAD` before any round-2 edit, where it reports identically. Both
traceability files are outside this chunk's write scope; regenerating the
aggregate (`tools/gc.py --fix traceability-aggregate`) is the orchestrator's
post-gate bookkeeping. The 31 info lines are unchanged in count from the entry
sweep.

All three bundled copies were re-synced after the last edit; `cmp` exits 0 for
each, now also enforced by the `bundled-drift` rule itself.

## Acceptance Criteria

### skill-namespace-rename.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-NAME-MARKETPLACE-001 — skill dirs free of the retired prefix, `name` == basename, linter 0 | pass | 10 directories under `skills/` hold a `SKILL.md` (`implement, migrate, orchestrate, plan, replan, requirements, research, review, specs, verify`); **0** basenames carry the retired prefix; **0** frontmatter `name` mismatches, both sides read from disk in one run. `python3 tools/skill-lint.py` exits 0 |
| REQ-NAME-MARKETPLACE-002 — no `skills/<other>/…` cross-skill path references | pass | every `skills/<name>/` occurrence inside `skills/**/*.md` was matched against its own owning skill directory: **0** references name a sibling. The `…/references/<file>` form is included in that zero |
| REQ-NAME-MARKETPLACE-003 — tool filenames, `--help`, self-references, history | pass | `tools/*.py` = `eval.py, gc.py, scope-check-selftest.py, skill-lint.py, telemetry.py`; **0** carry the retired prefix; **0** tools reference their own retired filename in their own source. `--help` exit-0 and `git log --follow` resolution recorded at Chunk 1 tasks 4–5 and unchanged by the red repair, which touched no tool filename |
| REQ-NAME-MARKETPLACE-004 — every enumerated live area clean, enumeration read from the rule | pass | **re-derived in full above** (§The Four Amended Criteria, item 2): enforced and stated scopes agree across all eleven areas including the five the original "six areas" omitted; the rule run live over that scope raises **0** findings |
| REQ-NAME-MARKETPLACE-005 — historical record provably intact | pass | the same `RETIRED_RE` over `docs/ws/` (excluding `docs/ws/marketplace/`), `docs/research/` and `docs/superpowers/` returns **2696** occurrences across **65** files — non-zero, as required; `git diff --name-only bceac64 f7a1a6d` (the Chunk 1–2 implementing change) lists **0** paths under those three areas |
| REQ-NAME-MARKETPLACE-006 — CONTRIBUTING names both forms and the pre-marketplace corpus | pass | `CONTRIBUTING.md` §The naming boundary names `sdd:orchestrate` / `sdd:implement` / `sdd:chunk-verifier` and the retired `sdd-` form, and identifies closed-cycle `docs/ws/`, `docs/research/` and `docs/superpowers/` as the set that keeps it |
| REQ-NAME-MARKETPLACE-007 — rename ordered before scaffold; the rename-close gate | pass | plan chunk order: Chunks 1–3 rename, Chunk 5 manifests. At `3ddfdb3`, `git ls-tree -r --name-only` matches **0** `.claude-plugin/` paths; the linter exit-0 and the entry-sweep finding-set equality at that sha are recorded at Chunk 3 task 7 and are unaffected by later commits |
| REQ-NAME-MARKETPLACE-008 — linter follows the rename; contract rows unchanged | pass | grep of `tools/skill-lint.py` for a prefixed `skills/` literal = **0**. REQUIRED contract rows counted by the same command against `git show <sha>:<linter>` (resolving the pre-rename filename where needed): `d1ef8f2`=40, `61d9498`=40, `f7a1a6d`=40, `3ddfdb3`=40, `a576316`=40, **HEAD=40** — unchanged across the rename *and* across the red repair. `--self-test` exits 0 |
| REQ-NAME-MARKETPLACE-009 — the self-test asserts the policed population | pass | **re-derived by mutation above** (§The Four Amended Criteria, item 3): gutting the scope makes `--self-test` exit 1 with a drift line per constant and a `seeded but unwalked` line per deleted area; the unmutated suite exits 0; the live repository raises 0 findings |
| REQ-NAME-MARKETPLACE-010 — symlink hazard and both operator actions | pass | `CONTRIBUTING.md` §The symlink hazard states that an existing symlink install **dangles at merge** and names both actions — re-point each symlink (`skills/sdd-research` → `skills/research`, and the other nine), or retire the install in favour of `/plugin marketplace add jangid/sdd-commons` + `/plugin install sdd@sdd-commons`. `docs/requirements/index.md` §Out of Scope names the same post-DONE step |

### pre-commit.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-PC-MARKETPLACE-001 — six hook ids, config validates | pass | `pre-commit validate-config .pre-commit-config.yaml` exit 0; ids parsed from the file = `{check-json, check-yaml, drift-sweep, end-of-file-fixer, skill-lint, trailing-whitespace}`, exactly **6** |
| REQ-PC-MARKETPLACE-002 — local hook shape, both exit 0, violation fails | pass | `pass_filenames: false` appears **2×** and `always_run: true` **2×**, one pair per local hook under `repo: local`; `pre-commit run --all-files` reports `drift sweep (fast profile) … Passed` and `skill linter … Passed`. The scratch-copy violation half was executed at Chunk 3 task 6 under an explicit root |
| REQ-PC-MARKETPLACE-003 — four hygiene hooks at an explicit rev | pass | the two parsed `repo:` values are `local` and `https://github.com/pre-commit/pre-commit-hooks`; the single `rev:` is `v6.0.0`, a non-empty explicit string, and the four hygiene ids sit under it. `end-of-file-fixer`'s result in this session is the sandbox artefact noted in §Quality Gates |
| REQ-PC-MARKETPLACE-004 — contributor tools out of the commit path, named in CONTRIBUTING | pass | grep of `.pre-commit-config.yaml` for `scope-check-selftest`, `eval.py` or `--self-test` = **0** matches; `CONTRIBUTING.md` §The three heavier checks, run explicitly names all three with their commands |
| REQ-PC-MARKETPLACE-005 — idempotence, frozen fixtures, excludes with reasons | pass | `git status --porcelain` empty after `pre-commit run --all-files`; `git diff d1ef8f2 HEAD -- tools/fixtures/` = **0 lines**; the `exclude: \|` verbose regex carries four patterns — `tools/fixtures/`, `docs/superpowers/`, `docs/ws/`, `docs/research/` — each with its reason on its own line |
| REQ-PC-MARKETPLACE-006 — no rule of the gate's own | pass | every parsed entry is one of the two local or four hygiene hooks; `^\s*args:` over the config = **0**, so no entry carries an `args` value at all (the sweep's `--fast` profile selector sits in `entry:`) |

### harness-agents.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-AGENT-MARKETPLACE-001 — three top-level files, no `.gitkeep`, kebab-case | pass | `agents/` holds exactly `chunk-verifier.md`, `red-team.md`, `reviewer.md`; **0** subdirectories; `agents/.gitkeep` absent; all three stems match `[a-z0-9]+(-[a-z0-9]+)*`; all three appear in the manifest component list (REQ-PKG-MARKETPLACE-003) |
| REQ-AGENT-MARKETPLACE-002 — frontmatter contract, no mutating tools, dropped keys absent | pass | each file parses with keys `{color, description, model, name, tools}`; `name` string-equals its stem in all three; each `description` carries a `Use when …` trigger clause; **0** of `Write`/`Edit`/`NotebookEdit` appear in any `tools` value; `grep -rnE '^(emoji\|vibe):' agents/` = **0** |
| REQ-AGENT-MARKETPLACE-003 — `CLAUDE.md` §Agents field list | pass | the section's field bullet reads `` `name`, `description`, `tools`, `model`, `color` `` — exactly five; it names `color`; neither `emoji` nor `vibe` occurs anywhere in the section |
| REQ-AGENT-MARKETPLACE-004 — token at line start, linter green, superset relation | pass | each agent file carries its token at the start of a line (`CHUNK_VERDICT:` → `agents/chunk-verifier.md`, `RED_VERDICT:` → `agents/red-team.md`, `VERDICT:` → `agents/reviewer.md`). Token file-sets derived by the same `git grep -l -E '^<token>'` at `3ddfdb3` and at HEAD, pre-rename skill paths normalised: `CHUNK_VERDICT:` 3 → 4, `RED_VERDICT:` 3 → 4, `VERDICT:` 6 → 7; **superset holds for all three, 0 files missing** from any after-set. Linter and `--self-test` exit 0 |
| REQ-AGENT-MARKETPLACE-005 — citation by name and by path in the same template block | pass | template blocks split from the file's own `##` headings; for each role the namespaced name and the backticked `agents/<name>.md` path both occur inside the **same** block (`CHUNK VERIFIER…`, `RED TEAM…`, `REVIEW…`). All three cited paths exist on disk and the linter's link check exits 0 |
| REQ-AGENT-MARKETPLACE-006 — single source, `RETURN:` verbatim, contract rows unchanged | pass | **re-derived above** (§The Four Amended Criteria, item 4): **0** shared normalised eight-word shingles for all three pairs; 5 `RETURN:` blocks retained and `template-drift` passes; REQUIRED rows 40 == 40 |

### marketplace-packaging.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-PKG-MARKETPLACE-001 — marketplace manifest parses and declares one plugin | pass | `.claude-plugin/marketplace.json` parses; `name` == `sdd-commons`; `owner` present; `plugins` has exactly **1** entry, named `sdd` |
| REQ-PKG-MARKETPLACE-002 — `source: ./`, plugin manifest fields, no `plugins/` | pass | `source` == `./`; `.claude-plugin/plugin.json` parses with `name` `sdd`, `version` `0.1.0`, `license` `MIT` and a 199-character `description`; `os.path.isdir('plugins')` is `False` |
| REQ-PKG-MARKETPLACE-003 — component list set equality, no `docs/` path | pass | manifest `skills` basenames vs directories under `skills/` holding a `SKILL.md`: **10 == 10**, sets equal; manifest `agents` vs `agents/*.md`: sets equal; listed paths starting `docs/` = **[]** |
| REQ-PKG-MARKETPLACE-004 — no absolute / home / plugin-root `docs/` citation | pass | the spec's own `grep -rnE '(^\|[^A-Za-z0-9._/-])(/\|~/\|\$\{?[A-Z_]*PLUGIN_ROOT)[A-Za-z0-9._/-]*docs/' --include='*.md' skills/` returns **0** matches |
| REQ-PKG-MARKETPLACE-005 — contributor tools out of both the skills and the list | pass | grep over `skills/**/*.md` for a `python3 ` or `./` invocation prefix of `scope-check-selftest.py` or `eval.py` = **0**. None of the three appears in the component list; note the linter is now *bundled as a file* (below) but is still **not declared as a component** — the list holds 13 entries and contains none of the three |
| REQ-PKG-MARKETPLACE-006 — bundled copies are regular byte-identical files; no tool lost | pass | `cmp skills/orchestrate/tools/<f> tools/<f>` exits 0 and `test ! -L` succeeds for **all three** bundled files — `gc.py`, `telemetry.py` and the newly bundled `skill-lint.py`. `ls tools/*.py` = 5, not less than the 5 at `d1ef8f2`; `git log --follow` resolves all five (Chunk 5 tasks 10–11) |
| REQ-PKG-MARKETPLACE-006 (added criterion) — at least one invocation resolves to the bundled copy | pass | **8** invocations under `skills/` spell the script as `<skill-dir>/tools/<tool>.py` — skill-directory-relative, not cwd-relative. Substituting `<skill-dir>` = `skills/orchestrate` yields `skills/orchestrate/tools/gc.py`, which exists on disk as a regular file. This is the criterion R5 showed was missing |
| REQ-PKG-MARKETPLACE-007 — explicit root, narrowed freeze, consumer repository | pass | **all three halves re-derived above.** Explicit root: **9** drift-sweep invocations found under `skills/`, **9** carrying an explicit root; **0** telemetry invocations pass a skill- or plugin-rooted file path. Narrowed freeze: `git diff 3ddfdb3 -- tools/telemetry.py` empty; `git diff 3ddfdb3 -- tools/gc.py` = the provenance conditional and nothing else. Consumer repository: freshly built scratch repo, exit **1** (not 2), 3 findings, **0** from a contract-row rule. See the Minor below on the one remaining cwd-relative invocation |
| REQ-PKG-MARKETPLACE-008 — no skill body depends on the plugin-root variable | pass | fence-aware scan of `skills/**/*.md` for `PLUGIN_ROOT` outside a fenced code block: **0** occurrences |
| REQ-PKG-MARKETPLACE-009 — dangling spec citations documented, count invariant | pass | `CONTRIBUTING.md` §Where the contracts live states "**Those citations resolve in this repository, not in an installed plugin.**" The `docs/spec/*.md` citation count over `skills/**/*.md`, derived with the same command at each sha: `d1ef8f2`=150, `016da07`=150, `464107a`=150, `1b6295a`=150, `a576316`=150, **HEAD=151**. The criterion is scoped to the **packaging change**, and across it the count is **150 == 150** — it passes. The single added citation arrived with `d2741f1` (the R5 repair citing `docs/spec/marketplace-packaging.md` §No skill body depends on the plugin-root variable); it is recorded as a Minor below so the first pass's "150 at HEAD" is not carried forward as true |
| REQ-PKG-MARKETPLACE-010 — install observation recorded with commands | pass (cited, not re-run) | recorded at plan Chunk 7 task 2, performed by the operator in a real session — the install commands write the operator's own Claude Code configuration, outside a dispatched leaf's permissions, so this verifier **cites** rather than re-runs it, as the dispatch directs. `claude plugin marketplace add <worktree>` → "Successfully added marketplace: sdd-commons"; `claude plugin install sdd@sdd-commons` → "Successfully installed plugin: sdd@sdd-commons (scope: user)". The plugin materialised to a **separate** cache copy, `~/.claude/plugins/cache/sdd-commons/sdd/0.1.0`, pinned to `gitCommitSha` `0d2d71eb…`, which is what makes the reference-resolution observation non-circular. `claude plugin details sdd@sdd-commons` listed Skills (10) and Agents (3) — equal to the manifest's 13 declared components, re-derived as 13 here. All ten of the driver's lazily-read reference files resolved from the installed copy under `<install>/skills/orchestrate/references/` |
| linter, self-test and sweep green after the packaging change | pass | see §Quality Gates; the sweep's finding **lines** match the entry sweep bar the two accounted differences |

### project-docs.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-DOCS-MARKETPLACE-001 — MIT `LICENSE` agreeing with the manifest | pass | `LICENSE` line 1 is `MIT License`; line 3 is `Copyright (c) 2026 Pankaj Jangid`; `license` parsed from `.claude-plugin/plugin.json` is `MIT` |
| REQ-DOCS-MARKETPLACE-002 — README usage heading and README↔manifest set equality | pass | `README.md` headings parsed: `# sdd-commons`, `## What this is`, `## Install`, `## Usage`, `## Components`, `## Pointers` — the `Usage` heading is present. Both install commands name `sdd-commons` and `sdd@sdd-commons`. The set of `sdd:<name>` component names in the README (**13**) equals the manifest's component set (**13**); symmetric difference **empty** |
| REQ-DOCS-MARKETPLACE-003 — the retired front door is gone, visibly | pass (with one stale spelling, Minor below) | `test ! -e README.org` succeeds; `git log --diff-filter=D -- README.org` shows the deletion at `1b6295a docs: add LICENSE, README.md and CONTRIBUTING.md; retire README.org`. The live retired-prefix scan over the enumerated scope returns **0**; the two remaining textual spellings of the deleted filename (`tools/skill-lint.py:381`, `docs/spec/orchestration.md:574`) are recorded as Minors |
| REQ-DOCS-MARKETPLACE-004 — four `CONTRIBUTING.md` items, cross-spec criteria pass | pass | the four items are identifiable sections, parsed from the heading list: §The naming boundary (+ §The symlink hazard), §Where the contracts live, §Pre-commit (+ §The three heavier checks, run explicitly), §Adding new content (§New skill / §New agent / §New tool). The four cross-spec criteria — REQ-NAME-MARKETPLACE-006, REQ-NAME-MARKETPLACE-010, REQ-PKG-MARKETPLACE-009, REQ-PC-MARKETPLACE-004 — were each re-run above and each passes |
| REQ-DOCS-MARKETPLACE-005 — `CLAUDE.md` clean, names both manifests, no substantive change elsewhere | pass | the live retired-prefix rule raises **0** findings on `CLAUDE.md` (it is in the enforced scope and is **not** self-exempt); the file names `.claude-plugin/marketplace.json` at lines 8 and 18 and `.claude-plugin/plugin.json` at lines 9 and 19. The Chunk 6 diff confines substantive change to §Repository Structure, §Agents and §Quality Checks; the phase-detection table, the cycle-identity rules and the v4 layout section show name substitution only |
| `CLAUDE.md` §Agents field list equals the spec's five | pass | duplicate of REQ-AGENT-MARKETPLACE-003; passes |
| sweep and linter exit 0 after these documents land | pass | see §Quality Gates |

## Traceability Verification

- **37 rows** in `docs/ws/marketplace/traceability.md`. Every row has a non-empty
  Spec column; Test, Implementation and Verified are filled for all 37. Row
  distribution re-derived: AGENT 6, DOCS 5, NAME 10, PC 6, PKG 10 = 37.
- `Verified` reads **`pending-red` on all 37** — the red round is outstanding, so
  the durable matrix asserts no `pass` (REQ-REDB-HARNESSP3-003). No row is `fail`
  and none is `descoped`. The file needed no edit in this re-verification: the
  values it already carries are the values this pass derives.
- gc criterion for those cells: `python3 tools/gc.py --report --root .` raises
  **no** finding on a `pending-red` cell. The single `[traceability-aggregate]`
  warning is the designed handshake with the orchestrator's post-gate
  regeneration (`ws-traceability.md` §Aggregate Regeneration Ownership) and is
  not a finding against any cell.
- The shared aggregate `docs/requirements/traceability.md` was **not** touched:
  the dispatched write scope omits it, which is the signal that regeneration is
  the orchestrator's post-gate bookkeeping.
- No gaps: no requirement is missing a spec, a test or an implementation
  reference.

## Deferral-Backlog Screen (REQ-REQ-HARNESSP6-001)

Run at verification time over both enumerations, with the phrase table and the
marker regex read from `docs/spec/requirements-artifacts.md` §`## Out of Scope`
Discipline rather than retyped. Each section is delimited heading-to-next-
same-or-higher-heading; an occurrence at line `L` is live unless a bracketed
dated marker sits on `L` or `L-1`.

The glob `docs/ws/*/verification.md` returned **7** paths and **7** rows were
walked — the two counts are equal and both derived from the same run.

| Path (§Next Steps) | Phrase hits | Live |
|---|---|---|
| `docs/ws/default/verification.md` | 3 | 0 |
| `docs/ws/harness-p2/verification.md` | 0 | 0 |
| `docs/ws/harness-p3/verification.md` | 12 | 0 |
| `docs/ws/harness-p4/verification.md` | 5 | 0 |
| `docs/ws/harness-p5/verification.md` | 6 | 0 |
| `docs/ws/harness-p6/verification.md` | 0 | 0 |
| `docs/ws/marketplace/verification.md` | 0 | 0 |
| `docs/requirements/index.md` §Out of Scope | 0 | 0 |

**Zero live occurrences.** Stated with the qualification the spec itself
requires: phrase coverage is a **screen over observed backlog vocabulary, not a
proof of absence**. A deferral written in vocabulary no cycle has used yet
passes it, and this zero must not be restated as an absence of latent work. The
one item in this report's §Next Steps that reads as a future cycle carries its
bracketed dated `[closed 2026-09-21 …]` marker on the same line as the phrase,
which is what makes it settled rather than live.

## User-Perspective Validation

| Scenario | Status | Notes |
|---|---|---|
| Operator installs the plugin from a real session | pass (cited) | Chunk 7 task 2: marketplace added, plugin installed to a separate cache copy pinned at `0d2d71eb…`, 10 skills + 3 agents listed, all ten lazily-read `references/*.md` resolved from the installed copy |
| Consumer runs the bundled drift sweep in **their own** repository | pass (re-measured) | freshly built scratch repo with no `tools/`: exits 1, 3 findings, all derived from the consumer's own corpus, none from this repository's contract rows. Before the repair the same invocation died with `can't open file '<consumer>/tools/gc.py'`; before the provenance conditional it reported 40 spurious `[required]` findings |
| Consumer's error paths are honest rather than misleading | pass | the failure mode the operator decision removed was a **misleading success** (40 contract-row findings about a stranger's tree, indistinguishable from real ones). What remains is a clean, consumer-attributable finding list |
| Contributor runs the commit gate for the first time | pass with a sandbox artefact | `pre-commit validate-config` exit 0; `pre-commit run --all-files` passes five of six hooks with a clean tree, `end-of-file-fixer` blocked only by this sandbox's write denial on `.claude/settings.json` (which already ends in `\n`) |
| Maintainer narrows the retired-prefix scope by accident | pass | the self-test now fails loudly with a per-area `seeded but unwalked` line, demonstrated by mutation above. Before the repair this silently printed `SELF-TEST OK` |
| Reader follows a spec citation from an installed skill body | pass, documented | the citations are bare `docs/spec/…` paths that resolve in this repository, not in an install; `CONTRIBUTING.md` §Where the contracts live says so explicitly |
| Consumer repository with no `skills/` directory | pass (recorded, not fixed) | one additional `[structure] skills/ directory not found` finding — consumer-derived, not a contract row. Carried from the earlier measurement; the scratch repo built here deliberately included a `skills/` directory, so this row cites rather than re-measures |

## Regressions

- **None found.** Regression base is the workstream branch point
  `merge-base(marketplace, main)` = `7be04f8`, not `main` HEAD (marker `4`,
  REQ-WS-018). `git diff --stat 7be04f8 HEAD` = **95 files changed, 11962
  insertions(+), 694 deletions(-)**. Filtering the changed path list for anything
  outside this cycle's declared areas (`skills/`, `tools/`, `agents/`, `docs/`,
  `CLAUDE.md`, `README.*`, `CONTRIBUTING.md`, `LICENSE`,
  `.pre-commit-config.yaml`, `.claude-plugin/`, `.gitignore`) leaves **0 paths**.
- Working tree clean (`git status --porcelain` empty) both before and after
  `pre-commit run --all-files`.
- All eleven quality gates green (one with the documented sandbox artefact).
- Contract-row count and the three verdict-token file-sets are unchanged or
  supersets across every measured sha, including across the red repair.

## Issues Found

### Critical (blocks release)

- None.

### Material

- None.

### Minor (can ship, fix later)

- **[closed 2026-09-21 — operator decision: accept and document; recorded as `Q-IMPL-MARKETPLACE-020`]** The installed plugin carries `docs/` (144 files, 48,462 lines) because `"source": "./"` materialises the whole repository tree. An **accepted cost, not a correctness defect**: the component list governs what Claude Code *loads*, not what an install *copies*; `claude plugin details` reports zero components from `docs/`; every `docs/` citation in a skill body is a bare relative path resolving against the operator's own project. The over-claiming text in `docs/requirements/integration/packaging.md` and `docs/spec/marketplace-packaging.md` was corrected in-cycle. Note for whoever picks this up: the component list **cannot express the exclusion**, so a criterion written against the manifest passes while the condition persists — assert against the **materialised install tree**.
- **[closed 2026-09-21 — operator decision: bundle the linter and add the provenance conditional; recorded as `Q-IMPL-MARKETPLACE-026`]** Residual of red break R5. With the bundled sweep reachable, a consumer run got further and exited 2 for want of a sibling linter. `tools/skill-lint.py` is now bundled beside the bundled sweep as a regular byte-identical file (`cmp` exit 0, `test ! -L` succeeds, re-derived above), still **absent from the component list** so REQ-PKG-MARKETPLACE-005 is untouched; and `tools/gc.py` gained one **provenance conditional**. Bundling the linter alone was rejected because it turns a clean failure into a misleading success — measured here as 42 findings, 40 of them `[required]`, against a stranger's tree. REQ-PKG-MARKETPLACE-007's freeze is narrowed, not dropped.
- **New in this re-verification.** One drift-sweep invocation under `skills/` is still **cwd-relative**: `skills/verify/SKILL.md:169` spells it `python3 tools/gc.py --report --root .`. It satisfies REQ-PKG-MARKETPLACE-007's letter — it carries an explicit root — and it satisfies REQ-PKG-MARKETPLACE-006's added criterion, which asks only that *at least one* invocation resolve to the bundled copy (8 do). But it is the same class of unreachability R5 found: read out of an installed plugin in a consumer repository that has no `tools/`, that command does not resolve. Behaviour-neutral in this repository. Fix by spelling it `<skill-dir>/tools/gc.py` as the driver skill's eight invocations already do — with the caveat that `skills/verify/` bundles no `tools/` of its own, so the fix needs a decision about where a non-driver skill's bundled copy lives.
- **New in this re-verification.** The `docs/spec/*.md` citation count over `skills/**/*.md` is **151 at HEAD**, not the 150 the first pass recorded. The delta is one citation added by the R5 repair (`docs/spec/marketplace-packaging.md` §No skill body depends on the plugin-root variable, cited from a driver-skill body). REQ-PKG-MARKETPLACE-009 is scoped to the packaging change and measures 150 == 150 across it, so the criterion holds; this is recorded so the superseded "150 at HEAD" assertion is not inherited as true by a later reader.
- `CLAUDE.md:251` says marker `3` is "what this repo uses today" while `CLAUDE.md:215` says the repository migrated to marker `4` on 2026-09-17. Pre-existing contradiction, inherited from before this cycle; left alone because §Multi-Workstream Layout (v4) is one of the sections this cycle was forbidden to change in substance (`project-docs.md` §`CLAUDE.md`). Both line numbers re-measured at HEAD.
- Two behaviour-neutral stale spellings of the deleted front door's filename: `docs/spec/orchestration.md:574` names the project README by its retired `.org` filename in backticked prose (passes the sweep by the backtick skip, factually stale), and `tools/skill-lint.py:381` still lists that filename in `RETIRED_SCOPE_FILES` (`Q-IMPL-MARKETPLACE-017`) — harmless, since the walk never finds a file by that name, but note it is also mirrored at `tools/skill-lint.py:1252` in the self-test's independent `policed_files` tuple, so removing it means editing **both** or the drift check fires.
- `pre-commit run --all-files` cannot complete `end-of-file-fixer` in this sandbox: the hook opens `.claude/settings.json` with `rb+` and the sandbox denies write to that path. A **sandbox artefact, not a repository defect** — `tail -c 1` on the file is `0a`, so the hook is a no-op outside the sandbox, and the other five hooks pass with a clean tree.

**Carry-or-close.** The report this write replaces is the first pass at
`a576316`, which belongs to **this same cycle** (`research_id:
RS-MARKETPLACE-001`, string-equal to the kickoff's), not to a previous one. Its
four Minors are therefore not inherited findings but this pass's own subject
matter: two are reproduced above with their closure markers intact, one (the
`CLAUDE.md` marker contradiction) is reproduced with its line numbers
re-measured, one (the stale front-door spellings) is reproduced and extended
with a second occurrence this pass found, and the sandbox artefact is
reproduced. Nothing from it is dropped. `marketplace` is this workstream's first
cycle, so there is no earlier cycle's report to carry from.

## Recommendation

- [x] Ship as-is — subject to the outstanding red round. `status:` is `pending-red`; the orchestrator dispatches the red team, gates, and flips `pending-red → pass` before its own commit.
- [ ] Fix critical issues then ship (invoke sdd-replan)
- [ ] Significant rework needed (invoke sdd-replan)

**Terminal state, re-measured at verification time.** PR #4 against `main` is
`OPEN` ("Public release as a Claude Code marketplace, plus the pre-commit gate")
and unmerged. `git ls-remote origin marketplace` resolves to `0d2d71e`, while
local HEAD is `d2741f1` — the branch is **4 commits ahead of its remote**
(`56a858a`, `b203613`, `a576316`, `d2741f1`), which includes this report and the
red repairs. That is a fact about the push, not a defect: the orchestrator pushes
at the DONE gate. No attribution trailer appears in the PR body or in any of the
cycle's commits.

## Next Steps

- **[closed 2026-09-21 — operator decision: accept and document]** Moving `docs/` outside the installed tree in a following cycle: the component list cannot express the exclusion, so a criterion written against the manifest passes while the condition persists — any future assertion must be made against the **materialised install tree**, not the manifest. Cheapest path first: spike whether an exclusion declaration exists before touching the plugin root layout. Recorded as `Q-IMPL-MARKETPLACE-020`.
- gc note: `skills/verify/SKILL.md:169` — the one remaining cwd-relative drift-sweep invocation in a shipped skill body; decide where a non-driver skill's bundled tool copy lives, then spell it skill-directory-relative.
- gc note: `docs/spec/orchestration.md:574` — name the project README by its current filename.
- gc note: `tools/skill-lint.py:381` **and** `tools/skill-lint.py:1252` — drop the deleted front door's filename from `RETIRED_SCOPE_FILES` and from the self-test's independent `policed_files` tuple together (`Q-IMPL-MARKETPLACE-017`); behaviour-neutral, but editing one alone trips the scope-drift check.
- gc note: `CLAUDE.md:251` — reconcile with `CLAUDE.md:215` on which marker the repository uses; blocked in this cycle by the must-not-change-in-substance fence on that section.
- `Q-IMPL-MARKETPLACE-021` (informational): a local-path install copies the working tree verbatim, including gitignored content such as `.sdd/telemetry.jsonl`. A property of this verification mechanism only, never of a user installing from the marketplace.
