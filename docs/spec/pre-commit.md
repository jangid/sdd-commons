---
status: Approved
last_updated: 2026-09-21
requires:
  - REQ-PC-MARKETPLACE-001
  - REQ-PC-MARKETPLACE-002
  - REQ-PC-MARKETPLACE-003
  - REQ-PC-MARKETPLACE-004
  - REQ-PC-MARKETPLACE-005
  - REQ-PC-MARKETPLACE-006
---

# Pre-Commit Gate

## Overview

The repository has no commit gate, a gap flagged during the harness-p4 cycle and
carried since. The two repository-maintenance tools that already exist — the
**drift sweep** and the **skill linter** — are exactly the checks a gate wants,
and the drift sweep already self-describes a fast profile as *the pre-commit
profile*: lint plus cross-links plus orphan-id sweeps, with no date walk and no
history walk.

This spec defines `.pre-commit-config.yaml`: two local hooks wrapping those
tools, four upstream file-hygiene hooks, and nothing else.

**Governing principle.** A pre-commit gate is a contributor convenience, not a
verification layer. It is a **runner, not a source of policy**: no hook may
enforce a rule that is not already stated in a requirement, a skill, or one of
the two tools' own rule tables. A rule that exists only in the gate is invisible
to every reader of the corpus and to every skill that must comply with it.

## Design

### The hook set — closed, six entries

The configuration declares exactly six hooks and no others. The set of hook ids
parsed from the file is the contract:

| Hook id | Repo | Role |
|---|---|---|
| `drift-sweep` | `local` | the drift sweep in its fast profile |
| `skill-lint` | `local` | the skill linter |
| `trailing-whitespace` | upstream `pre-commit-hooks` | hygiene |
| `end-of-file-fixer` | upstream `pre-commit-hooks` | hygiene |
| `check-yaml` | upstream `pre-commit-hooks` | hygiene |
| `check-json` | upstream `pre-commit-hooks` | hygiene |

`check-json` in particular guards the two new manifests
(`marketplace-packaging.md`), which are the only files in the repository whose
parseability the install depends on.

The set is closed at six **deliberately**, and one candidate was considered and
declined: a `cmp` assertion on the two tools duplicated into the driver skill.
Declining it is not a case of §No rule of the gate's own — REQ-PKG-MARKETPLACE-006
states that rule already, so a hook enforcing it would be a runner, not a new
policy. The reasoning is recorded in `marketplace-packaging.md` §Tools: the
identity is established once, in one chunk, so a once-per-cycle check is
proportionate. A reader finding no continuous guard for that invariant is looking
at a decision, not an omission.

### The two local hooks

Both are declared under `repo: local` with `language: system`, invoking the
repository's own Python scripts:

```yaml
- id: drift-sweep
  entry: python3 tools/gc.py --fast
  language: system
  pass_filenames: false
  always_run: true
- id: skill-lint
  entry: python3 tools/skill-lint.py
  language: system
  pass_filenames: false
  always_run: true
```

**Why once per commit over the repository, not once per changed file.** Each
tool is a whole-corpus sweep whose findings are cross-file — a dead cross-link
has two endpoints, a contract marker has a producer and a consumer. A per-file
invocation would both mis-report (a file is not a corpus) and multiply the cost
by the number of staged files. `pass_filenames: false` with `always_run: true`
is the mechanical expression of that.

A hook fails the commit exactly when its tool exits non-zero; neither hook
translates, filters or softens a tool's exit status.

### What stays out of the commit path

The scope-check self-test, the telemetry tool's self-test and the evaluation
tool must **not** appear in the configuration. They are slow and their inputs
are frozen fixtures, so a fixture-driven proof does not change between commits
that do not touch the fixture; running them per commit costs seconds on every
commit to re-prove something unchanged.

Excluding them must not make them invisible: `CONTRIBUTING.md` names all three
with the command that runs each, as the checks a contributor runs explicitly
when touching the corresponding tool or fixture (`project-docs.md`,
REQ-DOCS-MARKETPLACE-004 item 3).

### Normalisation happens inside this cycle

The whitespace and end-of-file hooks are run over the **whole repository**
within this cycle and any resulting normalisation is committed as part of it, so
that the first contributor to install the hooks does not face a mass rewrite of
files unrelated to their change.

**Ordering constraint: the normalisation runs inside the rename chunk.** The
config and the whole-repository normalisation land **within** the rename chunk,
strictly **before** the rename-chunk-close sha. Two other criteria measure from
or across that point and a normalisation commit landing after it would violate
either:

- REQ-PKG-MARKETPLACE-007 requires an empty `git diff` over the two bundled tools
  from the rename-chunk-close sha to HEAD. A later end-of-file or whitespace
  rewrite of a bundled tool is exactly such a diff.
- REQ-NAME-MARKETPLACE-005 requires the implementing change to list no path under
  `docs/ws/`, `docs/research/` or `docs/superpowers/`. A whole-repository
  normalisation that touches those areas would list them.

Both are satisfied by ordering plus the exclude set below, not by weakening
either criterion. One carve-out is needed on the first of the two windows and is
recorded as Q-IMPL-MARKETPLACE-003 below: the acting workstream's own
execution artifacts under `docs/ws/<ws>/` necessarily change after the
rename-chunk-close sha, so the `--name-only` check excepts that one directory,
exactly as `skill-namespace-rename.md` already excepts it for
REQ-NAME-MARKETPLACE-005. The bundled-tool half of that same window needs no
carve-out at all, because it is not checked as a `--name-only` listing: the
packaging chunk *creates* the bundled copies after the rename-chunk-close sha,
so the half is stated instead as a path-limited diff over the two
repository-root tools the requirement freezes, which is empty exactly when the
requirement holds. Q-IMPL-MARKETPLACE-019 below records the earlier
reinterpretation of the listing and the review that superseded it. The plan must carry this ordering as an
explicit chunk constraint — it is not inferable from the chunk list alone. It is also why the
YAML sample in §The two local hooks already spells the **post-rename** tool
names: the config is authored inside the rename chunk, after the tool filenames
change, so the sample is the form that is actually committed.

**Excluded paths, each with the reason inline.** Any path the hooks must not
normalise is named in an explicit `exclude` pattern in the config, with the
reason stated in a comment on that pattern (the comment form actually used is
recorded as Q-IMPL-MARKETPLACE-009 below):

| Excluded | Reason |
|---|---|
| `tools/fixtures/` | frozen fixtures whose bytes are part of what they test — silently normalising one would change what the fixture proves while leaving every test green |
| `docs/superpowers/` | vendored third-party corpus, not this repository's text to normalise; it is also one of the three areas REQ-NAME-MARKETPLACE-005 forbids the implementing change to touch |
| `docs/ws/`, `docs/research/` | execution records of closed cycles, excluded for the same reason `skill-namespace-rename.md` excludes them from the rename: a rewrite makes the record disagree with the commits it describes — and REQ-NAME-MARKETPLACE-005 forbids the implementing change from listing a path under either. The pattern is a whole-subtree one, so it also covers the **active** workstream, which is a live record rather than a closed one; that is deliberate — the gate must not rewrite a plan mid-cycle |

Excluding the last three areas is what lets the normalisation sit inside the
rename chunk without violating REQ-NAME-MARKETPLACE-005: with them excluded, a
whole-repository run cannot produce a path under them. The measured exposure is
small either way — no file under `docs/superpowers/`, `docs/research/` or
`docs/ws/` and no `tools/*.py` currently carries trailing whitespace, so the live
risk is `end-of-file-fixer` and `check-yaml` rewrites rather than whitespace
stripping.

The settled state is **idempotence**: a second `pre-commit run --all-files`
immediately after the first exits 0 and leaves the working tree clean.

### No rule of the gate's own

Each hook is either one of the two repository tools — whose rules live in their
own requirement domains (`drift-sweep.md`, `skill-lint-v5.md`) — or one of the
four upstream hygiene hooks. No hook entry carries a custom `args` value that
narrows or extends a rule beyond what the tool's own requirements state. The
drift sweep's `--fast` selector is not such a value: it selects the profile the
tool itself defines as the pre-commit profile, and adds no rule.

## Acceptance Criteria

All checks parse `.pre-commit-config.yaml` rather than comparing against a
written-out list, and derive both sides at run time.

- [ ] `pre-commit validate-config .pre-commit-config.yaml` exits 0; the set of hook ids parsed from the file equals the six-id set defined by §The hook set, derived by parsing the file and the spec's table rather than by a pasted list (REQ-PC-MARKETPLACE-001).
- [ ] Both local hooks appear in the parsed config with `pass_filenames: false` and `always_run: true`; `pre-commit run drift-sweep --all-files` and `pre-commit run skill-lint --all-files` each exit 0 at the close of this cycle; introducing a deliberate lint violation in a scratch copy (never in this worktree) makes the corresponding hook exit non-zero (REQ-PC-MARKETPLACE-002).
- [ ] The four hygiene hook ids are present in the parsed config under a `pre-commit-hooks` repo entry whose `rev` is a non-empty explicit string; `pre-commit run --all-files` exits 0 at the close of this cycle (REQ-PC-MARKETPLACE-003).
- [ ] A run-time grep of `.pre-commit-config.yaml` for each of the three excluded tool names returns zero matches; `CONTRIBUTING.md` names all three together with the command that runs each (REQ-PC-MARKETPLACE-004).
- [ ] `pre-commit run --all-files` exits 0 **and** `git status --porcelain` is empty when run a second time immediately afterwards; `git diff <cycle entry sha> HEAD -- tools/fixtures/` is empty, so the frozen fixtures are byte-identical to their pre-cycle content (REQ-PC-MARKETPLACE-005).
- [ ] Every hook entry in the parsed config is either one of the two local tool hooks or one of the four upstream hygiene hooks, and no entry carries an `args` value other than the drift sweep's profile selector (REQ-PC-MARKETPLACE-006).
- [ ] Every `exclude` pattern in the config is accompanied by a YAML comment stating its reason, checked by reading the file; the set of excluded areas parsed from the config equals the set in §Normalisation happens inside this cycle's exclude table, both sides derived by parsing rather than by a pasted list (REQ-PC-MARKETPLACE-005).
- [ ] The plan places the config and the whole-repository normalisation inside the rename chunk, ahead of the rename-chunk-close sha, checkable by reading the plan's chunk order; and `git diff <rename-chunk-close sha> HEAD --name-only` lists no path under `docs/ws/`, `docs/research/` or `docs/superpowers/` and no bundled tool, so the normalisation cannot have landed inside the windows REQ-PKG-MARKETPLACE-007 and REQ-NAME-MARKETPLACE-005 measure (REQ-PC-MARKETPLACE-005).

## Implementation Questions

### Q-IMPL-MARKETPLACE-003: The `--name-only` window excepts the acting workstream's own directory
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Normalisation happens inside this cycle
**Date**: 2026-09-21 (plan stage)

**Context**: the last criterion of REQ-PC-MARKETPLACE-005 above requires
`git diff <rename-chunk-close sha> HEAD --name-only` to list no path under
`docs/ws/`, `docs/research/` or `docs/superpowers/` and no bundled tool. As
literally written it is unsatisfiable: the cycle's own execution artifacts —
`plan.md`, `traceability.md` and `verification.md` under the acting
workstream's `docs/ws/<ws>/` — are necessarily written after the
rename-chunk-close sha, by the stages that follow it.

**Decision**: the criterion excepts paths under the **acting workstream's own**
`docs/ws/<ws>/` directory, and the exception is applied by the checking script
rather than by a pasted count or a hand-waved allowance. This mirrors the
carve-out `skill-namespace-rename.md` already carries for
REQ-NAME-MARKETPLACE-005, whose no-listed-path criterion excepts the same
directory; the two criteria measure the same window and were always meant to
read the same way.

**Impact**: none on what the criterion protects. The point of the check is that
the whole-repository normalisation cannot have landed after the
rename-chunk-close sha — the historical execution records of *closed* cycles,
the vendored corpus and the bundled tools all stay inside the check unchanged.
Only the directory the running cycle owns and is expected to write is excepted,
and no other workstream's directory is.

### Q-IMPL-MARKETPLACE-009: the per-pattern reason comments are verbose-regex comments
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Normalisation happens inside this cycle — "the reason
stated in a YAML comment on that pattern"
**Date**: 2026-09-21 (implement stage, Chunk 3)

**Context**: pre-commit's `exclude` is a **single regular expression**, one YAML
scalar value. YAML comments cannot appear inside a scalar, so a literal YAML
comment can sit above the `exclude:` key but never *on* an individual pattern —
the spec's wording and the format it describes cannot both be satisfied.

**Decision**: the `exclude` value is written as a verbose `(?x)` regex in a block
scalar, one excluded area per line, each followed by a `#` comment stating its
reason. Python's verbose mode makes those real comments in the compiled
expression, and they are comments in the file on exactly the pattern they
explain. A YAML comment block above the key records the excluded set as a whole.

**Impact**: none on what the criterion protects. The acceptance check still
parses the config: the set of excluded areas is read out of the `exclude` value
and compared against the table above, and every pattern line is checked to carry
a non-empty reason comment. Read "YAML comment" in that criterion as "comment in
the configuration file".

### Q-IMPL-MARKETPLACE-019: the bundled-tool half of the `--name-only` window measures modification, not creation
**Status**: superseded at the implement-stage review of 2026-09-21 — the
reinterpretation below is no longer what the plan checks. Chunk 7 task 3 now
states the bundled-tool half as its own **path-limited** diff,
`git diff <rename-chunk-close sha> HEAD -- <drift sweep> <telemetry tool>` is
empty — the form Chunk 5 task 10 already used. That is strictly better than
this entry's reading: it names the two repository-root paths the requirement
actually freezes, so nothing has to be reinterpreted about what "lists no
bundled tool" means, and the check is the same one a reader would write from
the requirement alone. The entry is kept, not deleted: it records the reading
the criterion was first closed under, and its Impact paragraph's three
observations still hold.
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Normalisation happens inside this cycle — "lists no path
under `docs/ws/`, `docs/research/` or `docs/superpowers/` and no bundled tool"
**Date**: 2026-09-21 (implement stage, Chunk 7 task 3)

**Context**: the same criterion Q-IMPL-MARKETPLACE-003 carves out for the acting
workstream's directory is unsatisfiable as literally written on its *second*
half too, and for the same structural reason. The bundled copies
`skills/orchestrate/tools/gc.py` and `skills/orchestrate/tools/telemetry.py` do
not exist at the rename-chunk-close sha: they are **created** by the packaging
chunk, which the plan deliberately orders *after* the rename chunk. Any run of
`git diff <rename-chunk-close sha> HEAD --name-only` at the end of this cycle
therefore lists two bundled tool paths, with status `A`, no matter how correct
the work is.

**Decision**: the bundled-tool half of the criterion is read as "no bundled tool
is **modified** inside the window" — status `M` or `D` on a bundled tool source
or on a copy that already existed at the window's base. A status `A` addition by
the packaging chunk is not a normalisation rewrite and does not violate it. As
with Q-IMPL-MARKETPLACE-003, the distinction is applied **by the checking
script**, from `git diff --name-status`, never by a pasted count or a
hand-waved allowance. The bundled tool set is likewise derived live — every file
under `skills/*/tools/` plus the repository-root source of the same basename —
never pinned as a literal list.

**Impact**: none on what the criterion protects. What the check exists to catch
is a whole-repository normalisation landing after the rename-chunk-close sha and
rewriting a bundled tool; that remains caught, because such a rewrite is a
modification. Three independent observations confirm the protected property
still holds at this cycle's close: the two bundled tool sources `tools/gc.py`
and `tools/telemetry.py` do not appear in the window at all; `cmp` between each
bundled copy and its root source exits 0, so neither copy carries a
normalisation the source does not; and the forbidden-directory half of the
criterion reports zero violations outside the Q-IMPL-MARKETPLACE-003 carve-out.
