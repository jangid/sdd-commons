---
workstream: marketplace
status: in-progress
research_id: RS-MARKETPLACE-001
last_updated: 2026-09-21
---

# Implementation Plan: Marketplace release

## Overview

This cycle takes the SDD toolkit from a private repository of symlinked skills
to a publicly installable Claude Code marketplace, and adds the pre-commit gate
the repository has been missing since harness-p4. It delivers five Approved
specs — `docs/spec/skill-namespace-rename.md`,
`docs/spec/pre-commit.md`, `docs/spec/harness-agents.md`,
`docs/spec/marketplace-packaging.md`, `docs/spec/project-docs.md` — and all
thirty-seven `REQ-*-MARKETPLACE-*` requirements.

The shape of the work is decided by one structural fact: under
`"source": "./"` the packaging moves **zero** existing files
(`marketplace-packaging.md` §The manifest pair). That is what lets the
**rename** land first as a wholly separate, independently verifiable step, with
no reference edited twice. Everything else — agents, manifests, project
documents, the PR — follows the rename and uses post-rename spellings
throughout.

The cycle's terminal state is an **open PR against `main`**, not a merge
(kickoff §Decided at DISCUSS).

## Conventions

- **Task types**: `[implement]` produces code or contract text, `[spike]`
  produces findings and may trigger a replan, `[verify]` validates behaviour.
- **Chunk headers**: `### Chunk N: <name>` per work unit; every chunk carries a
  `**Depends on**:` field, which is the canonical dependency signal, and a
  `**Traces to**:` field naming its primary spec.
- **Post-rename spellings are used from Chunk 1 onward.** After Chunk 1 the
  tools are `tools/gc.py`, `tools/skill-lint.py`, `tools/telemetry.py`,
  `tools/scope-check-selftest.py`, `tools/eval.py`, and the skills are
  `skills/orchestrate/`, `skills/implement/` and their siblings. Tasks in
  Chunk 0 and Chunk 1 that must name a pre-rename path do so as "the
  pre-rename filename", never as a pasted literal, because the retired prefix
  is exactly what this cycle retires.
- **Exit criteria on every chunk include**: the skill linter exits 0, and
  `--self-test` exits 0 for any chunk that touched the linter. A chunk never
  closes with a red tool.
- **No chunk changes any skill's or the driver's behavioural contract.** This
  cycle moves, renames and packages them. A rename that changes a contract is a
  defect, not scope (kickoff §Out of scope).

### Execution context (binding on every chunk)

- Work happens in the git worktree `.worktrees/marketplace`, on branch
  `marketplace`, **inside** the main checkout. Every tree-walking command — a
  grep, a count, a linter run, a `find` — must exclude nested `.worktrees/`
  paths, or every measured count doubles. Say so wherever a count is reported.
- **Execution is sequential. There is no implement-stage fan-out.** The rename
  touches overlapping files across chunks, which is the collision case
  harness-p6 measured fan-out to be bad at. No chunk below may be run
  concurrently with another, even where its `**Depends on**` would permit it.
- The local directory `…/tools-skills-agents` is **not** renamed by this cycle.
- Renaming the skill directories dangles the ten `~/.claude/skills/` symlinks
  **at merge time**. That is a post-DONE operator action
  (REQ-NAME-MARKETPLACE-010) recorded in `CONTRIBUTING.md`, not a task here, and
  no check is made against any path outside this repository.

### Measurement discipline (binding on every task acceptance)

No task acceptance pins a corpus-measured count as a literal. Every criterion
involving a corpus count derives **both sides at run time**. Where a "before"
value is needed, it is re-derived from git at the moment it is compared —
`git show <sha>:<path>`, or the same command run against a temporary checkout of
`<sha>` — rather than carried forward as a number written down in an earlier
chunk. Chunk 0 exists to fix the shas that make this possible.

Harness-p6 corrected ten false acceptance criteria, two of them introduced by
its own repairs, and every one was a corpus-measured count asserted as a
constant. Expect also the **self-reference hazard**: this cycle edits a linter
whose subject is a forbidden string, a `CLAUDE.md` that must reach zero bare
occurrences of it, and a README that specifies its own predecessor's deletion.
It fired four times in harness-p6.

## Ordering Constraints

These four are stated in the specs and are re-derivable from the chunk sequence
below. They are constraints, not preferences.

1. **The rename lands strictly before any packaging work**
   (`skill-namespace-rename.md` §Ordering, REQ-NAME-MARKETPLACE-007). The
   verifiable intermediate state is: the skill linter exits 0 **and**
   `test ! -e .claude-plugin/marketplace.json` succeeds — the post-rename
   repository with the old layout and no manifest. **Chunk 3's close is the
   designated boundary** at which that state is asserted. This is a designation,
   not a uniqueness claim: the same conjunction also holds at Chunk 2's close and
   at Chunk 4's close by their own exit criteria, and claiming otherwise would be
   exactly the class of over-stated invariant §Measurement discipline warns
   about. What is particular to Chunk 3's close is that it is the **last** such
   point before any manifest file exists, which is what makes it the reference
   sha named by constraint 2.
2. **The pre-commit config and the whole-repository normalisation run inside the
   rename chunk, ahead of the rename-chunk-close sha**
   (`pre-commit.md` §Normalisation happens inside this cycle,
   REQ-PC-MARKETPLACE-005). Chunks 1–3 are collectively **the rename chunk**;
   Chunk 3 is its closing segment and **Chunk 3's close sha is the
   rename-chunk-close sha** referenced by REQ-PKG-MARKETPLACE-007,
   REQ-PC-MARKETPLACE-005 and REQ-NAME-MARKETPLACE-007. This resolves a
   three-way conflict: a normalisation commit landing *after* that sha would
   produce a non-empty `git diff` over the two bundled tools
   (REQ-PKG-MARKETPLACE-007) and could list a path under `docs/ws/`,
   `docs/research/` or `docs/superpowers/` in the implementing change
   (REQ-NAME-MARKETPLACE-005). Both are satisfied by ordering plus the config's
   `exclude` set — never by weakening either criterion.
3. **The agents follow the rename** (`harness-agents.md` §Overview). They are
   extracted from the driver's dispatch templates and their citation paths use
   post-rename spellings. They are sequenced *before* packaging because the
   manifest's `agents` component list must equal the set of `*.md` files
   directly under `agents/` (REQ-PKG-MARKETPLACE-003) — a manifest written
   against an `agents/` directory that still holds only its placeholder fails
   that derivation at its own chunk close.
4. **The real-install observation is last** (REQ-PKG-MARKETPLACE-010). It needs
   the branch pushed, and the `owner/repo` shorthand is **not** valid before
   merge — it always resolves the default branch. The two valid mechanisms are a
   local-path `/plugin marketplace add <absolute path to the worktree>` or a
   branch-qualified git URL `…/sdd-commons.git#marketplace`; the operator picks
   one at the verify stage.

## Chunks

### Chunk 0: Entry baselines and the reference shas

**Goal**: every "before" side of every later comparison is re-derivable from a
recorded sha, so no chunk has to carry a number forward.
**Depends on**: None.
**Traces to**: docs/spec/skill-namespace-rename.md §Acceptance Criteria
**Tasks**:
1. [x] [verify] Record the **cycle entry sha** (`git rev-parse HEAD` on
   `marketplace`) in the chunk return. It is the reference for
   `git diff <cycle entry sha> HEAD -- tools/fixtures/`
   (REQ-PC-MARKETPLACE-005) and for the `ls tools/*.py | wc -l` loss check
   (REQ-PKG-MARKETPLACE-006) — traces to `docs/spec/pre-commit.md`
   §Acceptance Criteria.
2. [x] [verify] Run `python3 tools/<pre-rename drift sweep> --report` from the
   repository root with nested `.worktrees/` excluded, and record its **full
   output** to a `$TMPDIR` file plus the finding-class summary in the chunk
   return. This is the **entry sweep** every later chunk compares against —
   the invariant is "no finding absent from the entry sweep", never a number —
   traces to `docs/spec/skill-namespace-rename.md` §Ordering.
3. [x] [verify] Run the pre-rename skill linter and its `--self-test`; both must
   exit 0 before anything is touched. A red tool at entry means the baseline is
   not a baseline. **Response if either is red**: stop Chunk 0 without starting
   Chunk 1, record the failing rule and its full output in the chunk return, and
   raise the entry-red-tool replan trigger below. The red is never repaired
   inline inside Chunk 1 — a repair mixed into the rename makes the rename's own
   diff unreadable and destroys the entry sweep's value as a comparison base —
   traces to `docs/spec/skill-namespace-rename.md` §The linter
   follows the rename.
4. [x] [verify] Confirm the worktree exclusion is real: run one representative
   tree-walking grep twice, once naively and once with nested `.worktrees/`
   pruned, and record that the pruned form is used everywhere below — traces to
   `docs/ws/marketplace/kickoff.md` §Budget (nested-checkout warning).

**Entry criteria**: None (first chunk).
**Exit criteria**: entry sha recorded; entry sweep output captured; linter and
`--self-test` both exit 0; no file in the repository modified by this chunk.

---

### Chunk 1: Rename — skill directories, tool filenames, tool self-references

**Goal**: the ten skill directories and the five tools carry their post-rename
names, and no tool's own source still names its retired filename. The system's
behaviour is byte-unchanged apart from `--help` text.
**Depends on**: Chunk 0.
**Traces to**: docs/spec/skill-namespace-rename.md
**Tasks**:
1. [x] [implement] Rename each directory under `skills/` that contains a
   `SKILL.md` so its basename drops the retired prefix, using `git mv` so
   history follows; update each `SKILL.md` frontmatter `name` to string-equal
   its new basename — the repository's existing convention, unchanged — traces
   to `docs/spec/skill-namespace-rename.md` §The rename surfaces
   (REQ-NAME-MARKETPLACE-001).
2. [x] [implement] Rewrite every cross-skill reference inside `skills/` to name
   the sibling by its **bare new name**. Two forms must not survive: any
   `skills/<other-skill>/…` path, and in particular the
   `skills/<other-skill>/references/<file>` form, which the linter treats as
   fail severity. Name coupling, not path coupling, is what makes the
   single-plugin decision safe — traces to
   `docs/spec/skill-namespace-rename.md` §Name coupling, not path coupling
   (REQ-NAME-MARKETPLACE-002).
3. [x] [implement] `git mv` each `tools/*.py` to its post-rename filename, and
   edit each tool's **own source** so it contains no occurrence of its retired
   filename: `prog=`, the usage/`--help` block, and any user-facing hint
   string. This `--help` change is the **only** source edit permitted to a
   bundled tool anywhere in this cycle, and it happens here rather than in the
   packaging chunk — traces to `docs/spec/skill-namespace-rename.md` §The
   rename surfaces (REQ-NAME-MARKETPLACE-003).
4. [x] [verify] Derive both sides at run time: for every directory under
   `skills/` holding a `SKILL.md`, assert the basename does not match the
   retired-prefix pattern and the frontmatter `name` string-equals the
   basename, both read from disk in the same run; assert `ls tools/*.py` yields
   no matching filename; run each renamed tool's `--help` and assert exit 0;
   assert a grep of each renamed tool's source for its retired filename returns
   zero — traces to `docs/spec/skill-namespace-rename.md` §Acceptance Criteria
   (REQ-NAME-MARKETPLACE-001, -003).
5. [x] [verify] Assert `git log --follow` resolves each renamed tool and each
   renamed skill file to its pre-rename history, so the rename is a move and not
   a delete-plus-add — traces to `docs/spec/skill-namespace-rename.md`
   §Acceptance Criteria (REQ-NAME-MARKETPLACE-003).

**Entry criteria**: Chunk 0 complete; entry sha and entry sweep recorded.
**Exit criteria**: no skill directory or `tools/*.py` filename matches the
retired prefix; every `name` equals its basename; every tool's `--help` exits 0;
zero `skills/<other-skill>/…` references remain. The linter may still be red at
this point — it is repaired in Chunk 2, which is why Chunk 1 does not close the
rename.

---

### Chunk 2: Rename — the linter's keyed rules, the retired-prefix rule, and the live corpus

**Goal**: the linter follows the rename and gains the rule that stops the
retirement eroding; the six live areas reach zero bare occurrences of the
retired form while the historical record provably keeps its.
**Depends on**: Chunk 1.
**Traces to**: docs/spec/skill-namespace-rename.md
**Tasks**:
1. [x] [implement] Update every linter rule keyed by a skill path or a skill
   name — including every producer/consumer contract row keyed by a `"file"` or
   `"files"` value — to the post-rename names, and remove every literal
   prefixed `skills/` path from the linter source — traces to
   `docs/spec/skill-namespace-rename.md` §The linter follows the rename
   (REQ-NAME-MARKETPLACE-008).
2. [x] [implement] Add the **retired-prefix rule**: it flags a retired-prefix
   skill or tool name appearing in the live rename scope, with the two-step skip
   order evaluated in order — (1) occurrences inside fenced code blocks and
   inline-backtick spans, the same skip the drift sweep's orphan-id sweep
   already applies; (2) the short self-exemption path list carried **in the rule
   itself**: `CONTRIBUTING.md`, `docs/requirements/integration/naming.md`, the
   linter's own source, and `docs/spec/skill-namespace-rename.md`. No general
   allowlist and no per-occurrence suppression comment — traces to
   `docs/spec/skill-namespace-rename.md` §The retired-prefix rule and
   Q-IMPL-MARKETPLACE-001 (REQ-NAME-MARKETPLACE-009).
3. [x] [implement] Add the rule's `--self-test` case with a **synthesized**
   fixture: four occurrences of the retired form (bare, backticked, fenced, and
   inside a self-exempt file) written into a temporary directory at self-test
   time and discarded afterwards, the self-test asserting exactly one flag — the
   bare one. No file carrying the bare occurrence may exist on disk in the
   repository, so that `test ! -e` succeeds for it in the checked-out tree; this
   is the same shape the self-test already uses when it copies the real skills
   tree into a scratch root — traces to
   `docs/spec/skill-namespace-rename.md` §The retired-prefix rule and
   Q-IMPL-MARKETPLACE-002 (REQ-NAME-MARKETPLACE-009).
4. [x] [implement] Sweep the retired form out of the four remaining live areas —
   `docs/spec/`, `docs/requirements/`, `CLAUDE.md`, and the README. **The README
   at this chunk is the `.org` front door, which Chunk 6 task 3 deletes
   wholesale**, so invest no editorial work in it: bring it to zero bare
   occurrences by the cheapest edit that satisfies task 5's six-area grep at this
   chunk's close. The README that survives the cycle is the `README.md` authored
   fresh in Chunk 6 task 2, which is written free of the retired form at birth
   and re-checked by Chunk 6's own gate — leaving
   `docs/ws/` (other than `docs/ws/marketplace/`), `docs/research/` and
   `docs/superpowers/` untouched. Where a live document must name a retired
   form to describe the historical corpus, it quotes it in backticks, which the
   rule skips. `CLAUDE.md` is deliberately **not** on the self-exemption list
   and must reach zero bare occurrences on its own — traces to
   `docs/spec/skill-namespace-rename.md` §The live rename scope is exactly six
   areas (REQ-NAME-MARKETPLACE-004, -005).
5. [x] [verify] Run the retired-prefix grep over exactly the six live areas and
   assert zero matches outside the exemption set; run the **same** grep over
   `docs/ws/` excluding `docs/ws/marketplace/`, over `docs/research/` and over
   `docs/superpowers/` and assert a **non-zero** count — the positive half that
   proves the historical record was left intact rather than silently swept.
   Both sides derived in the same run; nested `.worktrees/` excluded — traces to
   `docs/spec/skill-namespace-rename.md` §Acceptance Criteria
   (REQ-NAME-MARKETPLACE-004, -005).
6. [x] [verify] Assert `git diff --name-only` over the implementing change of
   Chunks 1–2 lists no path under `docs/ws/`, `docs/research/` or
   `docs/superpowers/`, except paths under `docs/ws/marketplace/` — traces to
   `docs/spec/skill-namespace-rename.md` §Acceptance Criteria
   (REQ-NAME-MARKETPLACE-005).
7. [x] [verify] Assert `python3 tools/skill-lint.py --self-test` exits 0; assert
   a grep of the linter source for a prefixed `skills/` literal returns zero;
   and assert the **count of contract rows keyed on a skill file is equal before
   and after** the rename, obtained by running the same count command against
   `git show <cycle entry sha>:<linter path>` and against the working file in
   one run. The linter exiting 0 is explicitly **not** sufficient evidence — a
   uniformly wrong rename would still pass it — traces to
   `docs/spec/skill-namespace-rename.md` §The linter follows the rename
   (REQ-NAME-MARKETPLACE-008).

**Entry criteria**: Chunk 1 complete.
**Exit criteria**: linter exits 0; `--self-test` exits 0; retired-prefix grep
zero over the six live areas and non-zero over the three excluded areas;
contract-row count unchanged; no manifest file exists yet.

---

### Chunk 3: The pre-commit gate, whole-repository normalisation, and the rename-chunk close

**Goal**: the commit gate exists and the repository is already normalised under
it, so the first contributor to install the hooks faces no mass rewrite. **This
chunk's close sha is the rename-chunk-close sha** (§Ordering Constraints 2).
**Depends on**: Chunk 2.
**Traces to**: docs/spec/pre-commit.md
**Tasks**:
1. [x] [implement] Write `.pre-commit-config.yaml` declaring **exactly six**
   hooks and no others: `drift-sweep` and `skill-lint` under `repo: local` with
   `language: system`, `pass_filenames: false`, `always_run: true`, invoking
   `python3 tools/gc.py --fast` and `python3 tools/skill-lint.py`; plus
   `trailing-whitespace`, `end-of-file-fixer`, `check-yaml` and `check-json`
   from the upstream `pre-commit-hooks` repo at an explicit non-empty `rev`.
   The entries spell the **post-rename** tool names, which is possible only
   because the config is authored inside the rename chunk. No hook entry carries
   an `args` value other than the drift sweep's profile selector — traces to
   `docs/spec/pre-commit.md` §The hook set and §No rule of the gate's own
   (REQ-PC-MARKETPLACE-001, -002, -003, -006).
2. [x] [implement] Add the `exclude` patterns, each with its reason stated in a
   YAML comment on that pattern: `tools/fixtures/` (frozen fixtures whose bytes
   are part of what they test), `docs/superpowers/` (vendored third-party
   corpus), and `docs/ws/` plus `docs/research/` (historical execution records
   of closed cycles). Excluding the last three is what lets the normalisation
   sit inside the rename chunk without violating REQ-NAME-MARKETPLACE-005 —
   traces to `docs/spec/pre-commit.md` §Normalisation happens inside this cycle
   (REQ-PC-MARKETPLACE-005).
3. [x] [implement] Run `pre-commit run --all-files` over the whole repository and
   commit the resulting normalisation **inside this chunk**, before its closing
   sha. The measured exposure is expected to be `end-of-file-fixer` and
   `check-yaml` rewrites rather than whitespace stripping; do not assume that —
   report what actually changed — traces to `docs/spec/pre-commit.md`
   §Normalisation happens inside this cycle (REQ-PC-MARKETPLACE-005).
4. [x] [verify] Assert `pre-commit validate-config .pre-commit-config.yaml`
   exits 0 and that the set of hook ids **parsed from the file** equals the
   six-id set of `pre-commit.md` §The hook set, both sides derived by parsing
   rather than by a pasted list; assert both local hooks parse with
   `pass_filenames: false` and `always_run: true`; assert the four hygiene ids
   sit under a `pre-commit-hooks` repo entry with a non-empty explicit `rev`;
   assert the set of excluded areas parsed from the config equals the spec's
   exclude table and that every `exclude` pattern carries its reason comment;
   and assert a run-time grep of `.pre-commit-config.yaml` for each of the three
   contributor tool names — the scope-check self-test, the telemetry tool's
   self-test, the evaluation tool — returns **zero** matches, so no contributor-only check has
   crept into the commit path. That is the config half of
   REQ-PC-MARKETPLACE-004; its `CONTRIBUTING.md`-reading half is asserted at
   Chunk 6 task 8 — traces to `docs/spec/pre-commit.md` §Acceptance Criteria
   (REQ-PC-MARKETPLACE-001, REQ-PC-MARKETPLACE-002, REQ-PC-MARKETPLACE-003,
   REQ-PC-MARKETPLACE-004, REQ-PC-MARKETPLACE-005, REQ-PC-MARKETPLACE-006).
5. [x] [verify] Assert **idempotence**: `pre-commit run --all-files` exits 0 and
   `git status --porcelain` is empty when run a second time immediately
   afterwards; and `git diff <cycle entry sha> HEAD -- tools/fixtures/` is
   empty, so the frozen fixtures are byte-identical to their pre-cycle content —
   traces to `docs/spec/pre-commit.md` §Acceptance Criteria
   (REQ-PC-MARKETPLACE-005).
6. [x] [verify] Assert the hook-failure behaviour: introduce a deliberate lint
   violation **in a scratch copy under `$TMPDIR`, never in this worktree**, and
   assert the corresponding hook exits non-zero. Pass the scratch copy an
   explicit root — a copied tool run without one silently scans the real corpus
   and returns a false green — traces to `docs/spec/pre-commit.md` §Acceptance
   Criteria (REQ-PC-MARKETPLACE-002).
7. [x] [verify] **The rename-close gate** (§Ordering Constraints 1). At this
   chunk's close, and **before any manifest file exists**, assert all three in
   one run: `test ! -e .claude-plugin/marketplace.json` succeeds; the skill
   linter exits 0; and the drift sweep's report contains **no finding absent
   from the recorded entry-sweep output** — compared against Chunk 0's captured
   output, not against a number. Record this chunk's close sha as the
   **rename-chunk-close sha** — traces to
   `docs/spec/skill-namespace-rename.md` §Ordering
   (REQ-NAME-MARKETPLACE-007).

**Entry criteria**: Chunk 2 complete; retired-prefix sweep green.
**Exit criteria**: all of task 7's three conditions hold simultaneously; the
rename-chunk-close sha is recorded; the working tree is clean after a second
`pre-commit run --all-files`.

---

### Chunk 4: The three harness agents

**Goal**: the chunk verifier, the red team and the reviewer exist as three
top-level agent files that a session can dispatch by name, and the dispatch
templates cite them instead of restating them.
**Depends on**: Chunk 3.
**Traces to**: docs/spec/harness-agents.md
**Tasks**:
1. [x] [verify] Before touching anything, derive the **before** sets this chunk
   must not shrink: for each of the three tokens (`CHUNK_VERDICT:`,
   `RED_VERDICT:`, `VERDICT:`), the set of files carrying it; and the count of
   linter contract rows. Derive them by command in this chunk, and re-derive the
   same "before" side later from `git show <rename-chunk-close sha>:…` rather
   than carrying the values forward — traces to
   `docs/spec/harness-agents.md` §Vocabulary, and the token-relocation hazard
   (REQ-AGENT-MARKETPLACE-004, -006).
2. [x] [implement] Write `agents/chunk-verifier.md`, `agents/red-team.md` and
   `agents/reviewer.md` as three **top-level** files — peers,
   not children: a file in a like-named subdirectory would gain a third
   namespace segment and read as a sub-agent of a parent. Remove
   `agents/.gitkeep`, so `agents/` ends holding the three files and nothing else
   — traces to `docs/spec/harness-agents.md` §Three top-level files, peers not
   children (REQ-AGENT-MARKETPLACE-001).
3. [x] [implement] Give each file the frontmatter contract: `name` (kebab-case,
   string-equal to the filename stem), `description` (a scalar ending in an
   explicit trigger clause), `tools` (required for these three; string or flow
   sequence, excluding every mutating tool — for this repository exactly
   `Write`, `Edit` and `NotebookEdit`; `Bash` is **not** in that set and may be
   declared), optional `model`, optional `color`. The two dropped fields —
   `emoji` and `vibe`, this repository's own invention — must not appear
   anywhere under `agents/` — traces to `docs/spec/harness-agents.md` §The
   frontmatter contract (REQ-AGENT-MARKETPLACE-002).
4. [x] [implement] **Move** each role's standing definition out of
   `skills/orchestrate/references/dispatch-templates.md` into its agent file,
   and have the template cite the agent instead of restating it. The split is by
   variability, not length: the per-dispatch scope, budget, paths and the pinned
   `RETURN:` block stay in the template; what the role inspects, how it judges
   and what its token means moves to the agent file. Each template keeps its
   pinned `RETURN:` block **verbatim** — traces to
   `docs/spec/harness-agents.md` §The agent file is the single source
   (REQ-AGENT-MARKETPLACE-006).
5. [x] [implement] Cite each role **twice in one place** in its dispatch
   template: by `subagent_type` name (`sdd:chunk-verifier`, `sdd:red-team`,
   `sdd:reviewer`) — which is what makes the dispatch work — and by a backticked
   `agents/<name>.md` path in one parenthetical, which is what makes the
   citation mechanically verifiable, since a `subagent_type` name is checkable
   by nothing — traces to `docs/spec/harness-agents.md` §Citation: by name
   **and** by path (REQ-AGENT-MARKETPLACE-005).
6. [x] [implement] Update `CLAUDE.md` §Agents to document exactly the five-field
   list of §The frontmatter contract, naming `color` and naming neither dropped
   field. The correction is recorded rather than silently applied: the previous
   list was written before any agent file existed in the repository — traces to
   `docs/spec/harness-agents.md` §The frontmatter contract
   (REQ-AGENT-MARKETPLACE-003, REQ-DOCS-MARKETPLACE-005).
7. [x] [verify] Derive both sides at run time: `agents/` contains exactly three
   `*.md` files, no subdirectory and no other file; `test ! -e agents/.gitkeep`
   succeeds; each stem is kebab-case; each file's parsed frontmatter satisfies
   the contract and its `tools` value contains none of the three mutating tools;
   a grep for the two dropped keys across `agents/` returns zero; the field list
   parsed from `CLAUDE.md` §Agents equals the spec's five-field list — traces to
   `docs/spec/harness-agents.md` §Acceptance Criteria
   (REQ-AGENT-MARKETPLACE-001, -002, -003).
8. [x] [verify] Assert the **superset** relation, not equality: for each of the
   three tokens, the set of files carrying it after the change **contains** the
   set that carried it before, derived by the same grep on both sides in one
   run. The extraction is additive with respect to tokens — *moving* a token out
   of the dispatch templates would break the linter's producer/consumer contract
   row rather than relocate it. Also assert each agent file carries its token at
   the start of a line, the linter and `--self-test` both exit 0, no rule text
   appears in both an agent file and its template, and the contract-row count is
   unchanged — traces to `docs/spec/harness-agents.md` §Acceptance Criteria
   (REQ-AGENT-MARKETPLACE-004, -006).

9. [x] [verify] Assert the **citation pair** for each of the three roles, both
   forms **in the same template block**: parse
   `skills/orchestrate/references/dispatch-templates.md`, derive its template
   block boundaries from the file's own headings rather than from a pinned line
   range, and for each role assert that its `subagent_type` name
   (`sdd:chunk-verifier`, `sdd:red-team`, `sdd:reviewer`) **and** a backticked
   `agents/<name>.md` path both occur inside that one block. A per-file grep is
   not sufficient — it would pass while one template cited the role another
   names. Then assert the linter's link check resolves each cited
   `agents/<name>.md` path to a file that exists on disk, which is what makes the
   citation mechanically verifiable at all — traces to
   `docs/spec/harness-agents.md` §Citation: by name **and** by path
   (REQ-AGENT-MARKETPLACE-005).

**Entry criteria**: Chunk 3 complete; rename-chunk-close sha recorded.
**Exit criteria**: `agents/` holds exactly the three files; linter and
`--self-test` exit 0; token file-sets are supersets of their before-sets;
contract-row count unchanged; each role's dispatch template carries both
citation forms inside the same template block and the linter's link check
resolves every cited `agents/<name>.md` path on disk.

---

### Chunk 5: The marketplace and plugin manifests

**Goal**: the repository is a marketplace named `sdd-commons` carrying one
plugin named `sdd`, declared by two JSON files, with **zero existing files
moved**.
**Depends on**: Chunk 4.
**Traces to**: docs/spec/marketplace-packaging.md
**Tasks**:
1. [x] [verify] Capture this chunk's own immediate baseline by command: the
   count of `docs/spec/*.md` citations inside `skills/`, and the count of
   `tools/*.py`. Both are compared against the same command run after the
   packaging change; the "before" side is re-derivable from
   `git show <this chunk's entry sha>:…` — traces to
   `docs/spec/marketplace-packaging.md` §Dangling spec citations
   (REQ-PKG-MARKETPLACE-009, -006).
2. [x] [implement] Write `.claude-plugin/marketplace.json` in a **top-level**
   `.claude-plugin/` directory: `name` `sdd-commons`, an `owner` object, and
   exactly one `plugins` entry whose `name` is `sdd` and whose `source` is
   `./`. The repository must **not** grow a `plugins/` directory — traces to
   `docs/spec/marketplace-packaging.md` §The manifest pair
   (REQ-PKG-MARKETPLACE-001, -002).
3. [x] [implement] Write `.claude-plugin/plugin.json` in the same top-level
   directory, carrying `name`, `description`, `version`, `author` and
   `license`, the `license` value being the MIT identifier so it cannot drift
   from the `LICENSE` file landed in Chunk 6. **Ordering consequence, stated
   here rather than left to be discovered**: this chunk therefore closes with a
   manifest naming an MIT licence whose `LICENSE` file does not yet exist. That
   is intended. No exit criterion of this chunk asserts the file's existence, the
   agreement between the two is asserted only at Chunk 6 task 8 once both sides
   exist, and a verifier at this chunk's close must not read the absent `LICENSE`
   as a defect — traces to
   `docs/spec/marketplace-packaging.md` §The manifest pair
   (REQ-PKG-MARKETPLACE-002, REQ-DOCS-MARKETPLACE-001).
4. [x] [implement] Populate the **explicit** component list in the plugin entry:
   every shipped skill directory and every shipped agent file named
   individually. It is not a wildcard, because the `docs/` and
   contributor-tool exclusions are expressed by **absence from it**. No listed
   path begins with `docs/`, and none of the three contributor tools — the
   scope-check self-test, the telemetry tool's self-test, the evaluation tool,
   read from `docs/spec/pre-commit.md` §What stays out of the commit path rather
   than restated here — appears anywhere in it — traces to
   `docs/spec/marketplace-packaging.md` §The component list and its derivation
   rule (REQ-PKG-MARKETPLACE-003, -004, -005).
5. [x] [implement] Duplicate the drift sweep and the telemetry tool into the
   driver skill's own `tools/` subdirectory as **regular files byte-identical
   to their repository-root originals** — duplicated, never symlinked: a plugin
   install may be materialised from a git archive, which does not reliably
   preserve symlinks, so a symlink is a silent broken-install mode. Make **no**
   source or behavioural change to either tool — traces to
   `docs/spec/marketplace-packaging.md` §Tools: root stays
   (REQ-PKG-MARKETPLACE-006).
6. [x] [implement] Make every skill-side invocation resolve to the **operator's**
   repository: each drift-sweep invocation found in `skills/` carries an
   explicit root argument naming the current directory, and no telemetry
   invocation passes a file path beginning with a skill or plugin directory.
   Without the explicit root the sweep defaults to its own script location and
   would return a false green about the plugin's copy — traces to
   `docs/spec/marketplace-packaging.md` §Root resolution for skill-side
   invocations (REQ-PKG-MARKETPLACE-007).
7. [x] [implement] Ensure no skill body depends on the plugin-root variable: the
   only permitted occurrence of its name under `skills/` is inside a fenced code
   block explicitly documenting its manifest-only scope. Every `docs/…` citation
   inside a skill body stays a **bare relative path**, so it resolves against
   the operator's own project working directory — traces to
   `docs/spec/marketplace-packaging.md` §No skill body depends on the
   plugin-root variable (REQ-PKG-MARKETPLACE-008, -004).
8. [x] [verify] Assert by parsing, never by comparing against a written-out
   list: both JSON files parse; `.claude-plugin/plugin.json` carries a non-empty
   `name`, a non-empty `description` and a non-empty `version`, each read from
   the parsed object — the criterion requires the file to parse **and** to carry
   the three fields, and parsing alone does not establish the second half;
   `name` equals `sdd-commons`; `owner` present;
   exactly one plugin entry named `sdd` with `source` equal to `./`;
   `test ! -d plugins` succeeds; a script derives at run time the set of
   basenames in the manifest's `skills` list and the set of directories under
   `skills/` containing a `SKILL.md` and asserts **set equality**; likewise the
   `agents` list against `*.md` files directly under `agents/`; and no listed
   path starts with `docs/`. The driver skill's bundled `tools/` subdirectory
   contains no `SKILL.md`, so the derivation already excludes it — traces to
   `docs/spec/marketplace-packaging.md` §Acceptance Criteria
   (REQ-PKG-MARKETPLACE-001, -002, -003).
9. [x] [verify] Assert the exclusion greps: the absolute/home-rooted/plugin-root
   `docs/` citation grep over `skills/` returns no match; a grep over `skills/`
   for an invocation prefix (`python3 ` or `./`) of any of the three
   contributor tools returns zero; a grep for the plugin-root variable name over
   `skills/**/*.md` returns no match outside the documenting fenced block —
   traces to `docs/spec/marketplace-packaging.md` §Acceptance Criteria
   (REQ-PKG-MARKETPLACE-004, REQ-PKG-MARKETPLACE-005,
   REQ-PKG-MARKETPLACE-008).
10. [x] [verify] Assert the bundled-tool invariants: for each of the two copies,
    `cmp` against the repository-root file exits 0 and `test ! -L` succeeds;
    `git diff <rename-chunk-close sha> HEAD -- <drift sweep> <telemetry tool>`
    is **empty**, which is what the §Ordering Constraints 2 placement of the
    normalisation protects; every drift-sweep invocation in `skills/` carries an
    explicit root — traces to
    `docs/spec/marketplace-packaging.md` §Acceptance Criteria
    (REQ-PKG-MARKETPLACE-006, -007).
11. [x] [verify] Assert the **loss check by identity, not by name** — a name-set
    comparison against git history would fail by construction, because the
    rename changed every tool's filename: `git log --follow` resolves each
    post-change `tools/*.py` to its pre-change history, and `ls tools/*.py | wc -l`
    now is **not less than** the same count taken at the cycle entry sha, both
    sides derived by command — traces to
    `docs/spec/marketplace-packaging.md` §Tools: root stays
    (REQ-PKG-MARKETPLACE-006).
12. [x] [verify] Assert the citation-count invariant: the same `docs/spec/*.md`
    citation grep over `skills/` yields the **same count** before and after the
    packaging change, both sides from the same command, the before side from
    this chunk's entry sha. Dangling spec citations are an accepted, documented
    gap closed by `CONTRIBUTING.md` in Chunk 6, not by rewriting them — traces
    to `docs/spec/marketplace-packaging.md` §Dangling spec citations
    (REQ-PKG-MARKETPLACE-009).
13. [x] [verify] Assert the skill linter exits 0, its `--self-test` passes, and
    the drift sweep's report raises no finding absent from Chunk 0's recorded
    entry sweep — traces to `docs/spec/marketplace-packaging.md` §Acceptance
    Criteria.

**Entry criteria**: Chunk 4 complete; `agents/` holds exactly three files, so
the manifest's agent derivation can pass at this chunk's close.
**Exit criteria**: both manifests parse and satisfy their derived set
equalities; `test ! -d plugins` succeeds; bundled copies are regular files
`cmp`-identical to their originals; bundled-tool diff from the rename-chunk-close
sha is empty; linter, `--self-test` and drift sweep all green.

---

### Chunk 6: LICENSE, README.md, CONTRIBUTING.md, and the `CLAUDE.md` close

**Goal**: the three documents a public repository is read through exist, the
front door is `README.md`, and `README.org` is gone — visibly.
**Depends on**: Chunk 5.
**Traces to**: docs/spec/project-docs.md
**Tasks**:
1. [x] [implement] Add an MIT `LICENSE` at the repository root with the correct
   copyright holder and year, its first line identifying the MIT licence, so it
   agrees with the `license` value already in `.claude-plugin/plugin.json` —
   traces to `docs/spec/project-docs.md` §`LICENSE`
   (REQ-DOCS-MARKETPLACE-001).
2. [x] [implement] Write `README.md` with five identifiable sections: **What
   this is** (the SDD workflow in a short paragraph), **Install** (the two
   commands — adding the marketplace, then installing the plugin),
   **Usage** (how an operator starts a full cycle through the driver and how to
   invoke a single phase skill directly — the part the old README lacked and the
   reason the file is rewritten rather than converted), **Components** (the
   shipped skills and agents under their namespaced `sdd:<name>` form), and
   **Pointers** to `CONTRIBUTING.md` and `LICENSE` — traces to
   `docs/spec/project-docs.md` §`README.md` (REQ-DOCS-MARKETPLACE-002).
3. [x] [implement] Delete `README.org` with `git rm`, as **new content, not the
   old file renamed into place carrying its old body**: two front doors that
   disagree is worse than either alone, and the deletion must be visible in
   history. Remove every running-prose reference to it from the live rename
   scope, leaving the one documented exception — the Implementation cell of
   REQ-ORCH-021 in `docs/requirements/traceability.md`, a historical record of
   what a past cycle actually shipped — traces to
   `docs/spec/project-docs.md` §`README.org` is deleted, visibly
   (REQ-DOCS-MARKETPLACE-003).
4. [x] [implement] Write `CONTRIBUTING.md` carrying its four owed statements,
   each an identifiable section or paragraph: (1) the **naming boundary** —
   pre-marketplace artifacts keep the retired names, new work uses the
   namespaced form — plus the **symlink hazard** and the two operator actions at
   merge (re-point an existing symlink-based install to the new directory names,
   or retire it in favour of `/plugin install sdd@sdd-commons`); (2) **where the
   contracts live** — spec citations inside skills resolve in the repository,
   not in an installed plugin; (3) **pre-commit setup** plus the three heavier
   checks a contributor runs explicitly, each named with its command; (4) **how
   to add a skill, an agent and a tool**, carried forward from `CLAUDE.md`
   §Adding New Content rather than re-invented — restating them in new words
   would create a second source that drifts from the first — traces to
   `docs/spec/project-docs.md` §`CONTRIBUTING.md` — the four things this cycle
   owes it (REQ-DOCS-MARKETPLACE-004, REQ-NAME-MARKETPLACE-006, -010,
   REQ-PKG-MARKETPLACE-009, REQ-PC-MARKETPLACE-004).
5. [x] [implement] Close out `CLAUDE.md`: §Repository Structure reflects the
   marketplace layout **including both manifest paths**, §Quality Checks names
   the renamed linter, and every component it names uses the post-rename form.
   Its description of the SDD phases, the driver, phase detection, the
   cycle-identity rules and the v4 layout stays **unchanged in substance** — a
   change to any of them is a defect, not scope — traces to
   `docs/spec/project-docs.md` §`CLAUDE.md` (REQ-DOCS-MARKETPLACE-005).
6. [x] [verify] Assert the two README↔manifest consistency contracts **by
   parsing**: the marketplace and plugin names in the README's install commands
   equal those parsed from `.claude-plugin/marketplace.json`; and the set of
   README component names, mapped by §The mapping rule (`sdd:<x>` maps to
   `skills/<x>` when a directory of that name containing a `SKILL.md` exists,
   otherwise to `agents/<x>.md`), **equals** — not contains — the set of paths
   in the manifest's component list, and every README name maps to an existing
   skill directory or agent file. Containment would let a README naming three of
   the shipped components pass while the front door under-reports what the
   plugin installs. Also assert that the README carries a **heading whose text
   names usage**, derived from the parsed heading list rather than from a fixed
   line number: the Usage section is the part the retired front door lacked and
   the reason the file is rewritten, so its presence is asserted, not merely
   written — traces to `docs/spec/project-docs.md` §`README.md`
   (REQ-DOCS-MARKETPLACE-002).
7. [x] [verify] Assert `test ! -e README.org` succeeds; run the retired-README
   grep over the six live areas applying, in order, (1) the fenced-block and
   inline-backtick-span skip and (2) the single documented exception path — both
   applied by the checking script, never pasted as a count — and assert zero
   remaining; assert `git log --follow README.md` shows the deletion and the new
   file as separate history, or that the deletion is otherwise visible in the
   commit — traces to `docs/spec/project-docs.md` §Acceptance Criteria
   (REQ-DOCS-MARKETPLACE-003).
8. [x] [verify] Assert `LICENSE` exists with an MIT first line and a named
   holder, and that the `license` parsed from `.claude-plugin/plugin.json` is
   the MIT identifier; assert each of the four `CONTRIBUTING.md` items is
   present as an identifiable section or paragraph and that the
   `CONTRIBUTING.md`-reading criteria of REQ-NAME-MARKETPLACE-006,
   REQ-NAME-MARKETPLACE-010, REQ-PKG-MARKETPLACE-009 and REQ-PC-MARKETPLACE-004
   all pass — traces to `docs/spec/project-docs.md` §Acceptance Criteria
   (REQ-DOCS-MARKETPLACE-001, -004).
9. [x] [verify] Assert a grep of `CLAUDE.md` for the retired prefix returns zero
   outside the fenced-block and backtick-span skip set; assert `CLAUDE.md` names
   both manifest paths; and produce the `git diff` of `CLAUDE.md` across the
   cycle for reviewer confirmation that the phase-detection table, the
   cycle-identity rules and the v4 layout section show **no change beyond name
   substitution**. This is a reviewer-checkable diff, not a free-text claim —
   traces to `docs/spec/project-docs.md` §Acceptance Criteria
   (REQ-DOCS-MARKETPLACE-005).
10. [x] [verify] Assert the drift sweep and the skill linter both exit 0 after
    these documents land, and that `pre-commit run --all-files` still exits 0
    and leaves the tree clean — traces to `docs/spec/project-docs.md`
    §Acceptance Criteria (REQ-PC-MARKETPLACE-005).

**Entry criteria**: Chunk 5 complete; the manifests exist, so the README's
component list has something to be compared against as a set.
**Exit criteria**: `LICENSE`, `README.md` and `CONTRIBUTING.md` exist;
`README.org` is gone and its deletion visible in history; README↔manifest set
equality holds; `CLAUDE.md` clean of bare retired prefixes and naming both
manifest paths; all gates green.

---

### Chunk 7: Push, real-install observation, and the open PR

**Goal**: the packaging is observed to work from a real install, and the cycle
reaches its terminal state — an open PR against `main`.
**Depends on**: Chunk 6.
**Traces to**: docs/spec/marketplace-packaging.md
**Tasks**:
1. [ ] [implement] Push the `marketplace` branch. This is the precondition for
   the branch-qualified install mechanism and therefore for the whole of this
   chunk — traces to `docs/spec/marketplace-packaging.md` §Install verification
   (REQ-PKG-MARKETPLACE-010).
2. [ ] [verify] Install the pushed branch as a marketplace **in a real session**
   using one of the two valid mechanisms — a local path
   `/plugin marketplace add <absolute path to the worktree>`, or the
   branch-qualified git URL
   `/plugin marketplace add https://github.com/jangid/sdd-commons.git#marketplace`.
   The `owner/repo` shorthand is **not** valid here: it resolves the default
   branch, and this cycle ends before merge. Record, as observations with their
   commands: the install command actually run, the namespaced skill names the
   session listed, and the name of the `references/*.md` file read from the
   **installed** copy — that those lazily-read files resolve from an installed
   plugin is the one packaging assumption research could not observe directly —
   traces to `docs/spec/marketplace-packaging.md` §Install verification
   (REQ-PKG-MARKETPLACE-010).
3. [ ] [verify] Final whole-repository gate, all in one run: the skill linter
   and its `--self-test` exit 0; `pre-commit run drift-sweep --all-files` and
   `pre-commit run skill-lint --all-files` each exit 0; `pre-commit run
   --all-files` exits 0 and a second immediate run leaves `git status
   --porcelain` empty; the drift sweep's report raises no finding absent from
   Chunk 0's recorded entry sweep. **And the `--name-only` half of
   REQ-PC-MARKETPLACE-005**, which is measurable only here because HEAD is final
   at this task: `git diff <rename-chunk-close sha> HEAD --name-only` lists no
   bundled tool and no path under `docs/ws/`, `docs/research/` or
   `docs/superpowers/`, **except paths under `docs/ws/marketplace/`**. The
   exception is applied **by the checking script**, never by a pasted count or a
   hand-waved allowance: this workstream's own `plan.md`, `traceability.md` and
   `verification.md` necessarily change after the rename-chunk-close sha, so the
   criterion as literally written is unsatisfiable without it. The carve-out is
   recorded as `Q-IMPL-MARKETPLACE-003` in `docs/spec/pre-commit.md`
   §Implementation Questions, mirroring the carve-out
   `skill-namespace-rename.md` already carries for REQ-NAME-MARKETPLACE-005 —
   traces to `docs/spec/pre-commit.md`
   §Acceptance Criteria (REQ-PC-MARKETPLACE-001, REQ-PC-MARKETPLACE-002, REQ-PC-MARKETPLACE-003,
   REQ-PC-MARKETPLACE-005, REQ-PC-MARKETPLACE-006, REQ-NAME-MARKETPLACE-005).
4. [ ] [implement] Open a PR from `marketplace` against `main` with a full body
   describing the rename, the gate, the agents, the manifests and the documents,
   and **do not merge** — the operator reviews the migration diff. No
   attribution trailer is added to any commit message or PR body — traces to
   `docs/ws/marketplace/kickoff.md` §Decided at DISCUSS and §Out of scope.

**Entry criteria**: Chunk 6 complete; all gates green; working tree clean.
**Exit criteria**: the branch is pushed; the install observation is recorded
with its command, the listed namespaced names and the read reference file; the
final whole-repository gate passes, including the `--name-only` window check
with its script-applied `docs/ws/marketplace/` exception; the PR is open and
unmerged.

## Replan Triggers

- **The real install (Chunk 7 task 2) fails once a mechanism has been used** →
  **replan inside this cycle**, not a documented limitation. A mechanism merely
  being *unavailable* (for example, the operator cannot run a local-path add) is
  **not** a trigger — fall back to the other mechanism
  (`marketplace-packaging.md` §Install verification).
- **The installed plugin cannot read the driver's lazily-read `references/*.md`
  files** → the single unobserved packaging assumption is false; replan the
  packaging chunk (bundling, or a restructure of the driver's reference
  loading). Descoping the observation is not an available outcome.
- **The rename-close gate (Chunk 3 task 7) cannot be made to hold** — the linter
  will not exit 0, or the drift sweep raises a finding absent from the entry
  sweep, while no manifest exists → the rename broke a producer/consumer
  contract row the linter checks. Replan Chunk 2 rather than weakening the gate,
  deferring it past the manifest, or bumping a `last_updated:` to silence a
  staleness finding.
- **The normalisation cannot be confined to the rename chunk** — a hygiene hook
  insists on rewriting a bundled tool or a path under `docs/ws/`,
  `docs/research/` or `docs/superpowers/` after the rename-chunk-close sha →
  replan the `exclude` set inside Chunk 3, **never** by relaxing
  REQ-PKG-MARKETPLACE-007's empty-diff criterion or
  REQ-NAME-MARKETPLACE-005's no-listed-path criterion.
- **The retired-prefix rule cannot reach zero findings on the live repository
  while its synthesized fixture still raises exactly one flag** → the two halves
  of REQ-NAME-MARKETPLACE-009 are in conflict; replan the fixture's location or
  the skip order, not the exemption list, which stays at four documents whose
  subject is the rule.
- **The manifest's component derivation cannot reach set equality** — a skill
  directory or an agent file exists that the list cannot legitimately name, or
  the list must name something absent from disk → replan the component list's
  derivation rule rather than converting it to a wildcard, which would destroy
  the `docs/` and contributor-tool exclusions that are expressed by absence.
- **The token superset relation (Chunk 4 task 8) fails** — a token's file set
  shrank → an agent extraction *moved* a token out of a dispatch template
  instead of adding to it, breaking a linter contract row. Replan Chunk 4 task
  4's split; the invariant is a superset, and it is not negotiable.
- **The entry tools are red at Chunk 0 task 3** — the pre-rename skill linter or
  its `--self-test` does not exit 0 before anything is touched → there is no
  baseline to rename against and the entry sweep's comparison base is
  meaningless. Replan a repair chunk **ahead of Chunk 1**, committed separately
  from the rename, and re-run Chunk 0 to establish the entry sha and sweep
  afresh. Proceeding into the rename with a red tool, or repairing it inside
  Chunk 1, is not an available outcome.
- **A rename is found to have changed a behavioural contract** → that is a
  defect, not scope (kickoff §Out of scope). Revert the offending edit and
  replan the chunk that made it.

**Scope-sizing replans are explicitly permitted and are not a stop condition.**
The operator directed "replan as needed and finish everything"; `REPLAN_MAX` is
lifted for scope-sizing replans only, though the cap's gate event still renders.
A replan for any other reason is handled normally. Nothing here is carried
forward to a later cycle: an item that cannot be delivered is rescoped **inside**
this cycle, recorded as a settled exclusion with its reasoning in
`docs/requirements/index.md` §Out of Scope.

## Risks

- **The rename is the largest single mechanical change in the cycle** — roughly
  ninety files and ten directory renames. It is split across Chunks 1–3 so each
  dispatch stays inside its budget, but the three chunks are one logical unit:
  the linter is red between Chunk 1 and Chunk 2 by construction, and only
  Chunk 3's close is a verifiable boundary. Mitigation: no gate is asserted at
  the Chunk 1 boundary that cannot hold there, and §Ordering Constraints 1 names
  the one boundary where the full intermediate state is checkable.
- **The self-reference hazard** — a rule about text living inside its own
  domain. It fired four times in harness-p6 and this cycle edits a linter whose
  subject is a forbidden string, a `CLAUDE.md` that must reach zero bare
  occurrences of it, and a README that specifies its own predecessor's deletion.
  Mitigation: the two-step skip order (backticks and fences first, then a
  four-document exemption list), the synthesized fixture, and the discipline
  that this plan itself writes every retired form inside a backtick span.
- **False greens from a tool run with the wrong root.** The drift sweep and the
  skill linter default their root to their own script location. A copy run
  without an explicit root silently scans the real corpus. Mitigation: every
  scratch probe passes an explicit root, and every skill-side drift-sweep
  invocation carries one (Chunk 5 task 6).
- **Doubled counts from the nested worktree.** This worktree sits inside the
  main checkout; any tree walk from the repository root that does not prune
  nested `.worktrees/` doubles every measured count. Mitigation: the pruning is
  a Conventions-level rule and Chunk 0 task 4 proves it is applied.
- **Requirement coverage is broad and thin in places.** Thirty-seven
  requirements across five specs, with several cross-spec criteria — a
  `CONTRIBUTING.md` paragraph owed to the packaging spec, a `CLAUDE.md` field
  list owed to the agents spec. Mitigation: those tasks trace to **both**
  requirement ids explicitly (Chunk 4 task 6, Chunk 6 tasks 4 and 8), so no
  cross-spec obligation sits in only one spec's chunk.
- **The install observation depends on an environment this plan cannot inspect.**
  Chunk 7 task 2 needs a real session and a pushed branch. If it slips, the
  cycle cannot close, because REQ-PKG-MARKETPLACE-010 is an observation
  requirement and no substitute satisfies it.

## Assumptions

- **"The rename chunk" means Chunks 1–3 collectively**, and the
  rename-chunk-close sha is Chunk 3's close sha. The specs speak of a single
  rename chunk; the sizing guidance asks for chunks a dispatch can complete, and
  the rename does not fit one. The split preserves both constraints the specs
  place on that boundary — the linter-exit-0-before-any-manifest gate and the
  normalisation-ahead-of-the-close-sha ordering — at a single stated boundary.
  If a reviewer prefers this recorded as a spec question rather than a plan
  decision, it should be minted as the next free implementation-question id in
  this workstream: `-001` and `-002` are taken by
  `docs/spec/skill-namespace-rename.md` and `-003` by `docs/spec/pre-commit.md`
  §Implementation Questions (the Chunk 7 task 3 carve-out).
- **The five tools' post-rename filenames** are taken to be their pre-rename
  filenames with the retired prefix removed, and the ten skill directories
  likewise. No spec enumerates the resulting names; the rule is mechanical and
  `skill-namespace-rename.md` §The rename surfaces states it as a basename
  transformation.
- **The two bundled tools** are the drift sweep and the telemetry tool; **the
  three contributor tools** are the skill linter, the scope-check self-test and
  the evaluation tool (`marketplace-packaging.md` §Tools). The plan names them
  by role rather than by filename wherever the filename is what the cycle is
  changing.
- **Aggregate traceability regeneration is orchestrator post-gate bookkeeping**,
  not a chunk task. No task below writes `docs/requirements/traceability.md`,
  and no chunk verifier should raise a finding for a traceability cell left
  unfilled by a chunk that filled its own per-workstream row.
