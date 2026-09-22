---
status: Approved
last_updated: 2026-09-22
requires:
  - REQ-PC-MARKETPLACE-001
  - REQ-PC-MARKETPLACE-002
  - REQ-PC-MARKETPLACE-003
  - REQ-PC-MARKETPLACE-004
  - REQ-PC-MARKETPLACE-005
  - REQ-PC-MARKETPLACE-006
  - REQ-PC-PACKAGING-001
  - REQ-PKG-CONSUMERGEOMETRY-001
  - REQ-PKG-CONSUMERGEOMETRY-005
  - REQ-PKG-CONSUMERGEOMETRY-006
  - REQ-PC-PIPELINEOBSERVABILITY-001
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

### The hook set — closed, eight entries

[Amended 2026-09-21: six at design time, **eight** as amended — see §Hook-Set
Amendment at the end of this spec for the two added rows and why they were
added. The two rows marked *[added 2026-09-21]* below are that amendment's; the
other six are the design-time set, and the reasoning paragraphs in this section
are the design-time reasoning, preserved rather than rewritten.]

The configuration declares exactly eight hooks and no others. The set of hook ids
parsed from the file is the contract:

| Hook id | Repo | Role |
|---|---|---|
| `drift-sweep` | `local` | the drift sweep in its fast profile |
| `skill-lint` | `local` | the skill linter |
| `skill-lint-self-test` | `local` | the skill linter's own self-test *[added 2026-09-21]* |
| `drift-sweep-self-test` | `local` | the drift sweep's own self-test *[added 2026-09-21]* |
| `trailing-whitespace` | upstream `pre-commit-hooks` | hygiene |
| `end-of-file-fixer` | upstream `pre-commit-hooks` | hygiene |
| `check-yaml` | upstream `pre-commit-hooks` | hygiene |
| `check-json` | upstream `pre-commit-hooks` | hygiene |

`check-json` in particular guards the two new manifests
(`marketplace-packaging.md`), which are the only files in the repository whose
parseability the install depends on.

The set was closed at six **deliberately** at design time, and one candidate was
considered and declined: a `cmp` assertion on the two tools duplicated into the driver skill.
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

[Amended 2026-09-21, twice, and the sample above is the **pre-amendment** form.
(i) Both `entry` paths now carry the `plugins/sdd/` prefix — §Two-Root
Amendment below. (ii) Two further `repo: local` entries now sit beside these
two, one `--self-test` hook per repository tool — §Hook-Set Amendment below.
Read the sample as the shape of a local entry, not as the current entry set.]

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
| `.claude/` | editor settings, sandbox-denied for writing, not corpus text; `.claude/settings.json` is git-tracked, already ends in a newline, and the hook fails on opening it for writing rather than on its content *[added 2026-09-22, REQ-PC-PIPELINEOBSERVABILITY-001 — `[Updated: 2026-09-22]`; the record of why is §Pipeline-Observability Amendment]* |

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

- [ ] `pre-commit validate-config .pre-commit-config.yaml` exits 0; the set of hook ids parsed from the file equals the eight-id set defined by §The hook set **as amended** by §Hook-Set Amendment, derived by parsing the file and the spec's table rather than by a pasted list (REQ-PC-MARKETPLACE-001).
- [ ] Both local hooks appear in the parsed config with `pass_filenames: false` and `always_run: true`; `pre-commit run drift-sweep --all-files` and `pre-commit run skill-lint --all-files` each exit 0 at the close of this cycle; introducing a deliberate lint violation in a scratch copy (never in this worktree) makes the corresponding hook exit non-zero (REQ-PC-MARKETPLACE-002).
- [ ] The four hygiene hook ids are present in the parsed config under a `pre-commit-hooks` repo entry whose `rev` is a non-empty explicit string; `pre-commit run --all-files` exits 0 at the close of this cycle (REQ-PC-MARKETPLACE-003).
- [ ] A run-time grep of `.pre-commit-config.yaml` for each of the three excluded tools' **script filenames** — `scope-check-selftest.py`, `telemetry.py`, `eval.py`, pinned as the grep strings so the criterion has one truth value (REQ-PC-MARKETPLACE-004, amended 2026-09-21) — returns zero matches; `CONTRIBUTING.md` names all three together with the command that runs each (REQ-PC-MARKETPLACE-004).
- [ ] `pre-commit run --all-files` exits 0 **and** `git status --porcelain` is empty when run a second time immediately afterwards; `git diff <cycle entry sha> HEAD -- tools/fixtures/` is empty, so the frozen fixtures are byte-identical to their pre-cycle content (REQ-PC-MARKETPLACE-005).
- [ ] Every hook entry in the parsed config is either one of the four local tool entries — the two repository tools, each appearing plain and with `--self-test` (§Hook-Set Amendment, 2026-09-21) — or one of the four upstream hygiene hooks; the requirement's own wording, "one of the two repository **tools**", is unchanged by the amendment because the added entries invoke the same two tools. No entry carries an `args` value at all: `--fast` and `--self-test` are mode selectors inside `entry:` (REQ-PC-MARKETPLACE-006).
- [ ] Every `exclude` pattern in the config is accompanied by a YAML comment stating its reason, checked by reading the file; the set of excluded areas parsed from the config equals the set in §Normalisation happens inside this cycle's exclude table, both sides derived by parsing rather than by a pasted list (REQ-PC-MARKETPLACE-005).
- [ ] The plan places the config and the whole-repository normalisation inside the rename chunk, ahead of the rename-chunk-close sha, checkable by reading the plan's chunk order; and `git diff <rename-chunk-close sha> HEAD --name-only` lists no path under `docs/ws/`, `docs/research/` or `docs/superpowers/` and no bundled tool, so the normalisation cannot have landed inside the windows REQ-PKG-MARKETPLACE-007 and REQ-NAME-MARKETPLACE-005 measure (REQ-PC-MARKETPLACE-005).

**Pipeline-observability (2026-09-22, pre-commit) — sandbox-independent**

- [ ] Parsing the `exclude` value of `.pre-commit-config.yaml` with Python `re`
  and matching it against `.claude/settings.json` succeeds, and against
  `plugins/sdd/tools/gc.py` fails; in a scratch copy of the config with the
  `\.claude/` alternative removed the first match fails
  (REQ-PC-PIPELINEOBSERVABILITY-001).
- [ ] `pre-commit run end-of-file-fixer --files .claude/settings.json` reports
  the hook skipped with no files to check and exits 0; in the scratch copy it
  reports the file processed (REQ-PC-PIPELINEOBSERVABILITY-001).
- [ ] The `\.claude/` alternative carries a `#` comment stating the reason —
  `grep -c '#.*\.claude/' .pre-commit-config.yaml` reads ≥ 1 (0 before this
  delta); `pre-commit run --all-files` exits 0 on this branch
  (REQ-PC-PIPELINEOBSERVABILITY-001, REQ-PC-MARKETPLACE-005).

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
half too, and for the same structural reason. The bundled copies of `gc.py`
and `telemetry.py` under the driver skill's own `tools/` subdirectory did not
exist at the rename-chunk-close sha: they were **created** by the packaging
chunk, which the plan deliberately orders *after* the rename chunk (that
directory was itself removed on 2026-09-21 under REQ-PKG-CONSUMERGEOMETRY-005,
so the `--name-only` window's bundled-tool half now has an empty population; the
recorded context stands as what this Q-IMPL was decided against). Any run of
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
modification. The bundled-tool set is **derived live** by the checking script —
every `skills/*/tools/*.py` paired with the repository-root source of the same
basename — so no sentence here states which tools are in it, and bundling a
further tool extends the set by itself.

Two properties are distinct and must not be conflated. *Frozen across the
packaging step* means the packaging chunk itself performed no source edit: that
holds for every derived source, and it is what the criterion protects.
*Unchanged since the rename close* is the stronger property, and at this cycle's
close it happens to hold for every derived bundled source as well: the
path-limited diff against the rename-chunk-close sha is empty for each of them.
It is empty for different reasons, and the difference is worth recording. The
telemetry tool was never touched inside the window at all. The drift sweep was
modified inside the window by the verify stage's red rounds and then restored
byte-for-byte when the operator reverted the consumer-repository extension on
2026-09-21 (Q-IMPL-MARKETPLACE-029), so its net diff is empty although its
history inside the window is not — a `--name-status` run over the window will
show it. That is ordinary corrective work against the specs, not a
packaging-step edit or a normalisation rewrite, so it falls outside what this
criterion freezes either way; the criterion is not weakened to make that so, it
never covered it. Two further observations confirm the protected property still
holds: `cmp` between each derived bundled copy and its root source exits 0, so
no copy carries a normalisation its source does not; and the
forbidden-directory half of the criterion reports zero violations outside the
Q-IMPL-MARKETPLACE-003 carve-out.

## Two-Root Amendment (2026-09-21, REQ-PC-PACKAGING-001)

[Changed 2026-09-21: the suite moved to `plugins/sdd/`, so both local hook
entries take that prefix.] Both `repo: local` entries — the drift sweep and the
skill linter — have their `entry` script paths prefixed with `plugins/sdd/` in
the **same change** that performs the move (`two-root-linter.md` §1); editing
one alone leaves the gate invoking a dead path for the other, failing the
commit for a reason unrelated to the contributor's change. Every other field is
unchanged: each hook still runs once per commit over the repository
(`pass_filenames: false`, `always_run: true`) and still fails the commit
exactly when its tool exits non-zero. The linter hook's entry stays
**zero-argument**, the prefix being the only edit — correct only because the
corpus root defaults to the invocation cwd (`two-root-linter.md` §2): left
defaulting to the script's own location it would take `plugins/sdd` as its
corpus and stop sweeping `docs/` silently, with a green exit. The drift sweep's
root argument is governed by `two-root-linter.md` §8 — the gate sweeps the
repository, not the suite.

*Criterion*: every `entry` parsed from the two local hooks names a path that
exists after the move (`test -f` per parsed path); the linter hook's parsed
`entry` carries no positional root; running that entry verbatim from the
repository root sweeps a set containing at least one `docs/spec/` path
(membership, not exit code); `pre-commit run --all-files` exits 0 at the close
of this cycle; reverting the prefix on either hook alone makes that hook fail
with a missing-file error (REQ-PC-PACKAGING-001).

## Hook-Set Amendment (2026-09-21, REQ-PC-MARKETPLACE-001)

[Changed 2026-09-21: the closed hook set moves from **six** entries to
**eight**.] The two added entries are one `--self-test` hook per repository
tool — `skill-lint-self-test` (`python3 plugins/sdd/tools/skill-lint.py
--self-test`) and `drift-sweep-self-test` (`python3 plugins/sdd/tools/gc.py
--self-test`) — declared under `repo: local` with `language: system`,
`pass_filenames: false` and `always_run: true`, exactly like the two sweep
hooks they sit beside. The set stays **closed** and stays derived by parsing:
§The hook set's table is the contract, and its two amended rows are marked as
such.

**Why, stated beside where §The hook set records the declined candidate.** That
paragraph declined a `cmp` assertion on the two bundled tools because the
identity it guards is established once, in one chunk, so a once-per-cycle check
is proportionate. The two self-tests are the opposite case and the contrast is
the whole argument: what they guard is not established once but re-decided by
every edit to either tool's root bindings, and this cycle demonstrated twice
that the gate as designed cannot see such an edit go wrong. The two corpus
sweeps exercise no two-root fixture geometry, so a reverted root binding stays
green in both of them; and `gc.py` embeds the linter — its fixture sweep shells
out to `skill-lint.py` and passes the findings through — so a linter change can
turn `gc.py --self-test` red while `skill-lint.py --self-test` and both corpus
sweeps stay green. Nine binding changes landed across this cycle without the
embedding tool's self-test on the gate. A declined candidate and an adopted one
are therefore consistent, not in tension: proportionality is measured against
how often the guarded property can be broken.

The alternative — keeping the self-tests as a `CONTRIBUTING.md` trigger row —
was tried first and is what failed: a trigger row is discipline, and the defect
class it was guarding against is exactly a discipline failure.
`CONTRIBUTING.md` §The heavier checks, run explicitly records that reversal in
place.

**What is not weakened.** §What stays out of the commit path is untouched: the
scope-check self-test, the telemetry tool's self-test and the evaluation tool
stay out, and the run-time grep REQ-PC-MARKETPLACE-004 states was re-run after
the two entries landed and is still zero for each of the three. §No rule of the
gate's own is likewise untouched: each added entry invokes one of the two
repository tools, whose rules live in their own requirement domains, and
`--self-test` is a mode selector exactly as `--fast` is — it selects the tool's
own fixture-driven proof and adds no rule.

*Criterion*: the set of hook ids parsed from `.pre-commit-config.yaml` equals
the union of the four upstream hygiene ids and the set derived from the parsed
`repo: local` entries, in which each of the two repository tool scripts appears
exactly twice — once in its sweep invocation and once with `--self-test` —
the pairing derived by parsing each local entry's `entry` value rather than
compared against a pasted list of ids; `pre-commit validate-config` exits 0;
`pre-commit run --all-files` exits 0 at the close of this cycle
(REQ-PC-MARKETPLACE-001).

## Consumer-Geometry Amendment (2026-09-21, REQ-PKG-CONSUMERGEOMETRY-005, -006)

**The hook set does not change.** No entry is added, removed or re-rooted by the
`consumer-geometry` delta, and §The hook set — closed, eight entries stands.

**No assertion is made about the hook set, and that is deliberate.** Every
committed entry runs an **in-repo** copy of its tool, so every one is already in
the **nested** geometry and none can be "left on the degraded default". An
assertion over them would describe a state that cannot occur — the defect class
this delta exists to eliminate. What would have to be true for such an assertion
to be falsifiable is that a hook invoked an out-of-tree copy, which none does and
none should. The only hook-relevant risk that is real is that the derivation of
`two-root-linter.md` §CG-3 regresses the nested case they all run in, and
REQ-PKG-CONSUMERGEOMETRY-006 acceptance 4 covers exactly that.

**One record in this file is falsified by the removal.**
Q-IMPL-MARKETPLACE-019's context paragraph names
`skills/orchestrate/tools/gc.py` and `skills/orchestrate/tools/telemetry.py` as
files the packaging chunk creates. REQ-PKG-CONSUMERGEOMETRY-005's table marks this
file **class (A)** — made true in place, not annotated — so the paragraph is
restated against the removal: those two paths no longer exist, and the
`--name-only` window's bundled-tool half no longer has a population. The Q-IMPL's
**decision** is unaffected; only its context sentence is. Cited at `:274` before
this amendment was appended; appending it added three lines to the frontmatter's
`requires:` list, so the sentence is now at `:277`. **The content, not the number,
identifies the site**: the criterion below quotes it.

### Consumer-Geometry Acceptance Criteria

- [ ] **Primary, by named sentence.** Q-IMPL-MARKETPLACE-019's context sentence
  *"`skills/orchestrate/tools/gc.py` and `skills/orchestrate/tools/telemetry.py`
  do not exist at the rename-chunk-close sha"* no longer asserts those paths as a
  population the `--name-only` window measures — corrected the way
  `marketplace-packaging.md` §The three disposition classes specifies for a
  Q-IMPL **Context** sentence (re-tensed, with an inline dated clause; the
  recorded context is not rewritten), and matched **whitespace-normalised**
  because the sentence spans a line break. It is present and uncorrected
  today — that is what makes this red before the change — and removing the
  directory while leaving the paragraph makes it red after
  (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2, class A).
- [ ] **Secondary, residual grep with both exemptions.** A run-time grep of
  `docs/spec/pre-commit.md` for `skills/orchestrate/tools` returns zero matches
  outside (i) a fenced code block and (ii) this §Consumer-Geometry Amendment,
  which cites the string in order to say which sentence to correct; every
  occurrence inside this section is such a citation, never an assertion that the
  directory exists. **No baseline count is written here, deliberately**: this
  section's own citation lines change whenever it is edited, and a written count
  has already been wrong twice. The assertion is derived instead — *exactly one*
  matching line lies **before** this section's heading (the
  Q-IMPL-MARKETPLACE-019 sentence), every other match lies after it, and the
  correction is what takes that one to zero. Both halves are computed from the
  heading's line number at run time.
  `marketplace-packaging.md` §The shape every string criterion in this delta
  takes gives the reasoning for the two-part form
  (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 2, class A).
- [ ] The committed hook set is byte-identical across the cycle, asserted by
  `git diff` over `.pre-commit-config.yaml`'s hook entries from the cycle's entry
  sha, **except** for any change the delta explicitly authorises — of which there
  are none. Adding or re-rooting a hook under this delta makes this red
  (REQ-PKG-CONSUMERGEOMETRY-006 closing note; REQ-PC-PACKAGING-001 unchanged).
- [ ] `pre-commit run --all-files` exits 0 at the close of the cycle, and both
  tool self-tests remain hook entries rather than being moved to the
  run-explicitly set (REQ-PKG-CONSUMERGEOMETRY-001 acceptance 4;
  REQ-PKG-CONSUMERGEOMETRY-005 acceptance 6).


## Pipeline-Observability Amendment (2026-09-22, REQ-PC-PIPELINEOBSERVABILITY-001)

[Added 2026-09-22, workstream `pipeline-observability` —
RS-PIPELINEOBSERVABILITY-001 §Q6 gap 9, R13; Q-REQ-PO-K. Observed:
`end-of-file-fixer` fails on opening `.claude/settings.json` for writing under
the sandbox, recurring since the marketplace cycle.]

**Where the contract lives** (REQ-REQ-PIPELINEOBSERVABILITY-001 (b), 2026-09-22): this section is the record of *why* and states no contract of its own; the contract is in the sections of record named here, each edited in place under a `[Updated: 2026-09-22]` marker, and its acceptance criteria sit in this spec's own Acceptance Criteria section under the same date. §Design's "Excluded paths, each with the reason inline" table — the table of record — carries the `.claude/` row (REQ-PC-PIPELINEOBSERVABILITY-001), the form REQ-PC-MARKETPLACE-005 requires for a path the hooks must not normalise, so that requirement's parsed-set-equals-table acceptance now includes the new area. Left consistent and not reopened: the hook set and exit contract (REQ-PC-MARKETPLACE-001..-004), §Two-Root Amendment, §Hook-Set Amendment, §Consumer-Geometry Amendment, and Q-IMPL-MARKETPLACE-009's verbose-regex comment form, which the new alternative uses.

**Why an exclusion and not a hook change**: the failure is on opening the file for writing under the sandbox, not on its content, and the hook set is closed (REQ-PC-MARKETPLACE-001); the exclusion table is where such a path already goes (Q-REQ-PO-K).
