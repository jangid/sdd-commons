# Write Scope — Declared Slot, Observation, `SCOPE:` Gate Text

Procedure text for the declared write scope per dispatch: the slot every leaf
template carries, the default scope table the orchestrator fills it from, the
three-command observation on return, the `SCOPE:` finding surfaced as gate
text, the pre-persist check on `blocked_writes`, commit ownership per dispatch
type, snapshot ordering and the limitations recorded for v1. Contract:
`docs/spec/harness-write-scope.md` (REQ-HARN-020..026). Stub: `../SKILL.md`
§LOOP; the `SCOPE:` token is signal (2) at `../SKILL.md` §The gate.

Everything here is **orchestrator-owned** (`../SKILL.md` §Orchestrator-Only
Work, `return-contract.md` §9): the leaf produces writes and a `RETURN:` block;
the orchestrator observes, tags and branches. No template asks a subagent to
judge its own scope.

---

## 1. Declared write scope slot (REQ-HARN-020)

Every leaf template carries `Write scope: {write_scope}` — a comma-separated
glob list of repository-relative paths the subagent may create, modify, delete
or rename. Glob semantics: `**` matches any depth, `*` within a segment; a
directory path with trailing `/**` covers everything under it; an exact file
path matches only that file. The review and verifier templates carry the slot
with the literal value `(empty — read-only)`.

The orchestrator fills the slot from the default table (§2); the operator may
**widen** it at the gate (`accept & widen scope`). A widening is **session-only
gate text**: the widened glob applies to that dispatch's redo and the following
dispatches of the same stage in this session, and is never written to a file
(REQ-ORCH-013 analogue). Recurring widenings are folded back into the table in
a later cycle, not mid-session.

Where the slot appears: `dispatch-templates.md` §PIPELINE (`{write_scope}`),
§REVIEW and §CHUNK VERIFIER (`(empty — read-only)`), `fan-out.md` §2
(`{write_scope}` = the chunk-group's code and test paths only). A repair packet
carries the same list as its `write_scope` field (`return-contract.md` §3) —
the redo's scope is the (possibly widened) scope of the dispatch it repairs.

---

## 2. Default scope table

Marker `3` paths. Under marker `4`, `docs/plan*.md`, `docs/plan-history/**`,
`docs/verification.md` and the traceability write resolve to their
`docs/ws/<id>/` equivalents (`docs/ws/<id>/traceability.md`), while
`docs/research/**`, `docs/requirements/**` and `docs/spec/**` stay shared
(§9).

**Leaf rows omit the shared aggregate (REQ-WS-HARNESSP3-001).** For an
**orchestrated** dispatch the shared aggregate `docs/requirements/traceability.md`
is **not** part of any leaf row: regenerating it is the orchestrator's post-gate
bookkeeping, committed separately (§7). The path appears in a leaf's
`{write_scope}` only for a **standalone** (non-orchestrated) run, where the
writing skill regenerates the aggregate itself. The omission *is* the
discriminator, and no new flag or field is introduced: **absent path → the
orchestrator regenerates; present path, or no dispatched write scope at all →
the skill regenerates itself.** A skill therefore never has to know *who*
invoked it, only what it was scoped to write. The rows below are stated in that
amended form; the owning contract is `docs/spec/ws-traceability.md` §Aggregate
Regeneration Ownership.

| Stage / dispatch | Default write scope | Note |
|---|---|---|
| research | `docs/research/RS-NNN-*/**`, `docs/research/index.md` | `research` Steps 5–6 |
| requirements | `docs/requirements/**`, minus `docs/requirements/traceability.md` when orchestrated | category files, `index.md`; marker `4`: rows go to `docs/ws/<id>/traceability.md` |
| specs | `docs/spec/**`; marker `3`: `docs/requirements/traceability.md` (Spec column only) — marker `4`: `docs/ws/<id>/traceability.md` (Spec column only), plus the aggregate only for a standalone run | traceability: Spec column only |
| plan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**` | rewrite archives, never `-replan-` |
| implement (sequential, per chunk) | the chunk's source/test paths, `docs/plan.md`, `docs/plan-*.md`, the active traceability file (marker `3` `docs/requirements/traceability.md`, marker `4` `docs/ws/<id>/traceability.md`; the aggregate only for a standalone run), `docs/spec/*.md` (**ADVISORY**), `docs/plan-history/*-complete.md`, `docs/research/RS-NNN-*/**` + `docs/research/index.md` | traceability: Test/Implementation columns; spec writes = Q-IMPL entries; `-complete` archives multi-milestone only; research paths spike tasks only |
| verify | `docs/verification.md`, the active traceability file (marker `3` `docs/requirements/traceability.md`, marker `4` `docs/ws/<id>/traceability.md`; the aggregate only for a standalone run) | traceability: Verified column (Step 3b) |
| replan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**`, `docs/spec/*.md` (**ADVISORY**) | `-replan-` archives; spec only for a Level-2 inline change |
| fan-out leaf | the chunk-group's code and test paths **only** | plan + traceability barred by `fan-out.md` §2; `docs/spec/*.md` barred too — leaves never write Q-IMPL entries directly; a deviation is returned in `RETURN.open_questions` and the orchestrator files the Q-IMPL entry at merge (§3e) |
| review, chunk verifier | *(empty — read-only)* | any write is `OUT` |

**Deriving "the chunk's source/test paths".** The orchestrator derives them
from the chunk's task list and the spec's implementation-module convention
(`chunk-close-review.md` Check 3 step 1: task → `traces to` spec → expected
implementation module and its test file). When they cannot be derived, the
orchestrator declares the project's source and test roots (e.g. `src/**`,
`tests/**`) and **notes the widening at the gate** — a declared-roots fallback
is a widening like any other (§1), stated, not silent.

**`RS-NNN` for a spike inside implement.** Substitute the assigned ID — the
exact `docs/research/RS-<assigned>-*/**` directory, not the wildcard — so a
spike cannot write a sibling research directory.

**Re-walk note (rationale).** The table was re-walked on 2026-09-17 against
every stage skill's `SKILL.md` after review finding C1 showed a first draft
omitted `verify`'s Verified-column write; a legitimate side-write a skill
instructs today is tagged `IN`, never a false `VIOLATION`. A verify dispatch
filling the Verified column is `SCOPE: CLEAN`.

---

## 3. Observation: three commands (REQ-HARN-021)

**Snapshot base rule (REQ-HARN-HARNESSP2-001).** `snapshot(before)` is taken at
the commit the leaf is **instructed to reach** — never at a stale worktree
HEAD. Remedy **(i)**, the default: every sequential-pipeline, fix, verifier,
review and red worktree is provisioned at the intended base — the **workstream
branch tip** under marker `4`, `main`/HEAD under marker `3` — exactly as
`fan-out.md` §3 already does for leaves, so the dispatch prompt names no
catch-up and the leaf never needs to catch up. Remedy **(ii)**, the safety
net: when a prompt nevertheless names a base commit for the leaf to
fast-forward or merge to ("reach commit `<sha>`"), `HEAD_before` for the
committed-delta and ancestry checks is that **named base**; commits reachable
from the named base but not from the provisioned HEAD are excluded from the
observed window and reported on the gate block as a `CATCH-UP` line (the
named-base observation below). Contract: `docs/spec/dispatch-snapshot-base.md`;
both remedies are restated under limitation (c) in §5.

Provisioning step (sequential and fix dispatches), before `snapshot(before)`:

```
base      := git rev-parse <workstream-branch>          # marker 4; `main` or HEAD under marker 3
worktree  := provision at base  (git worktree add <path> base, or `git merge --ff-only base` in an existing worktree)
HEAD_prov := git -C <worktree> rev-parse HEAD           # == base under remedy (i)
HEAD_before := base                                     # the instructed tip, not HEAD_prov
snapshot(before) at HEAD_before
```

On a leaf's return the orchestrator computes the set of written paths as the
union of a porcelain delta and a committed delta, plus an ancestry check:

```bash
# BEFORE dispatch (sequential: repo root; fan-out: the leaf's worktree)
HEAD_before=$(git rev-parse HEAD)
git status --porcelain=v1 --untracked-files=all > "$TMPDIR/scope.before"

# ... dispatch, await return ...

# AFTER return, BEFORE the orchestrator's own commit
HEAD_after=$(git rev-parse HEAD)
git status --porcelain=v1 --untracked-files=all > "$TMPDIR/scope.after"
(a) porcelain delta : lines in scope.after not in scope.before   → paths, status letter, "uncommitted"
(b) committed delta : git diff --name-status "$HEAD_before" "$HEAD_after"  → paths, status letter, "committed <sha>"
(c) ancestry        : git merge-base --is-ancestor "$HEAD_before" "$HEAD_after" || flag HISTORY_REWRITE
```

**Fan-out substitution.** For a fan-out leaf the same three commands run
against the **worktree path** with `<base>` (the branch point, `fan-out.md`
§3a) in place of `HEAD_before` and the **branch tip** in place of
`HEAD_after`. The leaf's own commits are inside the window by design — that is
what (b) exists to see.

**Snapshot ordering (REQ-HARN-025)** — both modes, stated here beside the
commands because the window is the whole point:

```
sequential : snapshot(before) → dispatch → await return → snapshot(after) → scope check
             → chunk verifier → PER-CHUNK GATE → orchestrator commit (on proceed)
fan-out    : snapshot(before) → dispatch → await return → snapshot(after) → scope check
             → chunk verifier → PER-LEAF GATE → merge (on proceed)   # leaf commits are inside the window by design
```

The "before" snapshot is taken immediately before dispatch — at `base`, the
instructed tip, per the snapshot base rule above — and the "after"
snapshot immediately **on return** — before the verifier dispatch, before the
per-chunk gate and therefore before the per-chunk gate's commit (sequential) or
merge (fan-out), and before any `fan-out.md` §3e bookkeeping writes (plan
marks, traceability fills, checkpoint notes, marker-4 aggregate regeneration) —
so the orchestrator's commit and bookkeeping are never inside the observed
window and cannot be flagged. The verifier is read-only and its own scope check
must observe zero writes, so running it after the snapshot changes nothing. A
non-implement stage follows the sequential line with the review in place of
the verifier and the stage gate in place of the per-chunk gate.

**Rules.**
- `--untracked-files=all` expands untracked directories to file paths.
- Paths present in both snapshots (pre-existing untracked noise such as
  `.claude/worktrees/`) cancel **only when their content hash is also
  unchanged** (content-hash observation below) — otherwise only the *delta*
  is a write.
- Deletions (`D`) and renames (`R`, both old and new path) count as writes; a
  rename across the scope boundary (`R src/a.py -> docs/a.py`) tags the new
  path `OUT` and the old path `IN` — one finding.
- A file modified and reverted within the dispatch — or created then deleted —
  is invisible to both deltas (accepted).
- A **porcelain-only check is explicitly insufficient**: committed writes
  vanish from porcelain output; (b) catches them with a clean porcelain.
- A non-zero ancestry exit (c) is a **`HISTORY_REWRITE`** finding, surfaced
  above the path list and counted as a violation. The option offered is
  `stop` plus a manual recovery hint (`git reflog` in the affected tree) —
  **never an automatic reset** (`../SKILL.md` §Isolation Discipline).

**Content-hash observation (REQ-HARN-HARNESSP3-001).** The porcelain pair is
blind to a path that is **already dirty or untracked at snapshot time** and is
written again during the dispatch: its status letter is unchanged, so the delta
cancels it, and an uncommitted write leaves no committed delta either. A fourth
term closes that gap — call it the **content-hash observation** in prose, never
"the fourth observation" (the named-base observation above is already a
four-part one).

```
ambiguous_set := paths listed as dirty or untracked by snapshot(before)
sha.before    := {(path, content_hash) for path in ambiguous_set}          # pre-dispatch
sha.after     := {(path, content_hash) for path in ambiguous_set INTERSECT snapshot(after)}
content_delta := {p | sha.before[p] != sha.after[p]}
                 UNION {p in sha.before and absent from the worktree on return}

observed writes := porcelain_delta UNION committed_delta UNION content_delta
```

- The hash is taken over **working-tree** content — the blindness being closed
  is an uncommitted working-tree rewrite. The contract is the `(path, sha)`
  pair set, so any hash function conforms as long as the same one is used for
  the before and the after snapshot of a dispatch; `git hash-object
  --stdin-paths` over the ambiguous set is the recommendation, since the value
  is git's own blob identity and needs no second hashing dependency
  (`harness-write-scope.md` Q-IMPL-HARNESSP3-001).
- A path **deleted** during the dispatch records the reserved non-hash sentinel
  `ABSENT` in the sha slot — it cannot collide with a hex digest, so the
  comparison stays a plain inequality and needs no separate presence set
  (Q-IMPL-HARNESSP3-002). The sentinel pair is itself a content change.
- Porcelain is parsed with **`-z`** (NUL-separated fields, no shell quoting or
  mangling of paths containing spaces or newlines), and **both** paths of a
  rename or copy (`R`, `C`) record enter the ambiguous set.
- The `SCOPE:` token, the `IN` / `ADVISORY` / `OUT` tags, the `N` count, the
  finding block, the operator options and the `HISTORY_REWRITE` rule are
  **unchanged**: this changes *what counts as an observed write*, not how one
  is matched or rendered, and `HISTORY_REWRITE` still rests on the untouched
  ancestry check (c).
- Cost is bounded to **O(dirty files)**, never O(repo), because the ambiguous
  set is fixed before the dispatch (probe: 134 files in 0.064 s, an 8-path set
  in 0.017 s, against a 0.008 s porcelain baseline — RS-HARNESSP3-001 Q1).
  `git stash create` and a temp-index `read-tree HEAD` were both measured and
  rejected: the first mutates the repository being observed, the second diffs
  against HEAD and reproduces the identical blindness.
- **Strict set (REQ-HARN-HARNESSP4-004).** The `UNION` is a set and the
  implementation must be one: a path observed by more than one term is counted
  **once** in the `N` of `SCOPE: VIOLATION (N paths)`, once in each `COMMIT:`
  operand (§7a) and listed once on the `Observed writes:` provenance line,
  keeping its richest label — `committed ≻ content ≻ porcelain` (fixture F14
  of `tools/scope-check-selftest.py`: dirty at snapshot, committed during
  the dispatch, dirtied again → one entry, `committed <sha>`, `(1 path)`).
- Fixture: scenario F10 of `tools/scope-check-selftest.py` (both halves).

**Git-state observation (REQ-HARN-HARNESSP6-001).** The porcelain delta (a) is
*one-directional* — lines in `after` not in `before` — so an operation that
**removes** dirty lines is invisible to it, and `git stash` leaves `HEAD`
untouched so (b) and (c) see nothing either (the harness-p5 incident: a
read-only chunk verifier stashed nine files of uncommitted work and the gate
still rendered `SCOPE: CLEAN`). **No second observation window is introduced**:
`snapshot(before)` and `snapshot(after)` each record three extra plumbing reads
alongside the `git status --porcelain` read they already take.

```bash
stash_count=$(git stash list | wc -l)
branch=$(git rev-parse --abbrev-ref HEAD)
orig_head=$(git rev-parse --verify --quiet ORIG_HEAD || echo "")
```

- `ORIG_HEAD` is read with `--verify --quiet`: its **absence** is the legal
  empty value, and absent-in-both compares equal — a repository that has never
  reset is never a finding.
- For a fan-out leaf the three reads run in the leaf's worktree, as the
  existing commands do.

**The comparand** — a `GIT_STATE` finding is raised when **either** clause holds:

| Clause | Condition |
|---|---|
| (i) state drift | `stash_count`, `branch` or `orig_head` differs between the two snapshots |
| (ii) reverse porcelain delta | the set of paths dirty in `before` and **not** dirty in `after`, **minus** the paths of the committed delta (b), is non-empty — a path stopped being dirty with no commit explaining it |

- Clause (ii) is the general form: it catches `git stash`, `git checkout --
  <path>`, `git restore` and `git clean` on a path the leaf did not commit.
  Clause (i) is the cheap form and catches a branch switch and a reset that
  leaves the tree clean (`git stash` itself sets `ORIG_HEAD`, so a
  stash-then-pop that restores the dirty set is still observed).
- **It does not fire on a legitimate dispatch.** A normal implement leaf only
  *adds* porcelain lines and any path it commits leaves the dirty set — the
  subtraction in clause (ii) removes exactly that committed delta, so the
  reverse delta is empty. An orchestrator **fan-out merge**, and the
  orchestrator's own bookkeeping commit, run **outside** any leaf's window
  (§Snapshot ordering above), so no snapshot pair spans them.
- Rendering is the `GIT_STATE` line of §5; its options are in §8.
- Fixtures: scenarios G1–G5 of `tools/scope-check-selftest.py`.

**Third observation (telemetry) — REQ-TELEM-HARNESSP2-005.** Because `.sdd/`
is gitignored (limitation (b), §5), the porcelain pair cannot see a leaf write
there. In the same window take a third observation: before dispatch `n_before`
(line count of `.sdd/telemetry.jsonl`, 0 if absent) and `e_before` (sorted
entry list of `.sdd/`, empty if absent); with `snapshot(after)` — before the
orchestrator's own append — `n_after` / `e_after`. Any delta is a leaf write:
render it inside the finding block as one more `OUT` counted in
`SCOPE: VIOLATION (N paths)`, using the finding strings defined **once** in
`telemetry.md` §4 (never restated here), and **revert before the gate**
(truncate the file back to `n_before` lines; remove entries the leaf added).
Fixture: scenario F7 of `tools/scope-check-selftest.py`.

**Named-base observation (remedy (ii)).** With the named base `base` and the
provisioned `HEAD_prov`, the observation on return has four parts:

```
(a) porcelain delta : unchanged (scope.after − scope.before)
(b) committed delta : paths of commits in  git rev-list HEAD_after ^base ^HEAD_prov
                      (== git diff --name-status base HEAD_after when HEAD_prov is an ancestor of base)
(c) ancestry        : git merge-base --is-ancestor base HEAD_after || HISTORY_REWRITE
(d) catch-up        : N := git rev-list --count HEAD_prov..base
                      N > 0 → render  CATCH-UP <HEAD_prov>..<base> (N commits, excluded — base <base>)
```

- `CATCH-UP <from>..<base> (N commits, excluded — base <sha>)` is rendered in
  the write-scope block's "Observed writes" header line, before the path list,
  so the finding format names the base. Short shas. Absent when `N == 0`
  (remedy (i) in effect) — the block is then byte-identical to the
  three-command rendering.
- The ancestry check stays intact: a leaf that rewrites history so that `base`
  is no longer an ancestor of `HEAD_after` still fails it, even if the rewrite
  also drops catch-up commits.
- A catch-up performed by **merge** rather than fast-forward: the merge commit
  is in `HEAD_after ^base ^HEAD_prov` and contributes only its conflict
  resolutions (`git show --name-status --format=` on a merge commit lists the
  combined-diff paths); commits reachable from `HEAD_prov` alone were in the
  worktree before dispatch and are outside the window by definition.
- Remedy (ii) never widens the window: a commit reachable from the named base
  is by construction authored before the dispatch (the orchestrator named it),
  so excluding it cannot hide a leaf write.
- **Edge cases.** Named base not reachable from the branch (typo in a
  hand-written prompt): `git rev-list HEAD_prov..base` fails → fall back to
  `HEAD_before := HEAD_prov` and render `CATCH-UP base <sha> unresolved —
  window from <HEAD_prov>`; no exclusion is applied. Leaf ignores the catch-up
  instruction: `base` is not an ancestor of `HEAD_after` **and** `HEAD_prov`
  is → render `CATCH-UP not performed (base <sha>)` as a warning, take
  `HEAD_before := HEAD_prov`, and do not count it as a violation; only a
  `HEAD_after` that contains neither is `HISTORY_REWRITE`. Fan-out leaves are
  already provisioned at the branch point (`fan-out.md` §3): `<base>` is the
  branch point and remedy (ii) never applies. The third observation above is
  unaffected by the base choice — it reads `.sdd/`, not history.

**Section resolution of fix hunks (REQ-ARB-HARNESSP2-005).** An extension of
the observation commands, run for each path in a **fix dispatch's** written
set so that `fix[N].written` (`loop-control.md` §2a) is keyed at section level
rather than file level. It partially closes limitation (a) of §5 for Markdown
paths; contract: `docs/spec/arbitrated-handoff.md` §Section Resolution.

```
committed  : git diff -U0 <HEAD_before> <HEAD_after> -- <path>
uncommitted: git diff -U0 <HEAD_after> -- <path>            # porcelain-only writes
untracked  : every heading of the file → (path, *)          # a new file is written in full
```

For each hunk header `@@ -a,b +c,d @@`: take the after-image start line `c`
(for a pure deletion, `d == 0`, use `c` as well); the enclosing section is the
nearest `#`-heading line ≤ `c` in the after-image (`git show <HEAD_after>:<path>`
or the working file); normalise the heading text as `loop-control.md` §2a does
for review keys (`§Name` — leading `#`s and a leading ordinal stripped,
whitespace collapsed, case kept). A hunk above the first heading resolves to
`§(preamble)`. Non-Markdown paths resolve to `(path, ?)` and fall back to
file-level comparison. The result per path is the set of `(path, §Name)` pairs
plus the hunk ranges for rendering (`docs/spec/x.md §A (hunks L40-58)`; a
one-line hunk renders `L120`). Under remedy (ii) `<HEAD_before>` is the named
base, as for (b) above. Fixture: scenario F8 of
`tools/scope-check-selftest.py`.

---

## 4. Matching and tags

Every observed path is matched against the declared scope:

| Tag | Condition |
|---|---|
| `IN` | matches a declared glob |
| `ADVISORY` | matches a glob marked **ADVISORY** in the default table (`docs/spec/*.md` under implement or replan) — hunk-level intent cannot be verified by path |
| `OUT` | matches nothing → boundary finding |

`ADVISORY` paths carry a hint: implement → "verify hunks are under ##
Implementation Questions"; replan → "verify this is the Level-2 spec change".
`ADVISORY` applies only where the table marks it: under a fan-out leaf, a
review or a verifier, a spec-file write is plain `OUT`.

A per-chunk implement dispatch that writes a **later chunk's** source paths is
`OUT` — the scope is the *chunk's* paths, which is precisely the drift the
check exists to catch; the operator may widen.

---

## 5. Finding format and `SCOPE:` token (REQ-HARN-022)

Gate text only — ephemeral like review verdicts (REQ-ORCH-013 analogue), never
persisted:

```
Write-scope check — implement dispatch #2 (Chunk 2, worktree wt-g1 / branch fanout-g1)
  Declared scope : src/recon/**, tests/test_recon.py, docs/spec/recon.md (advisory)
  Observed writes: uncommitted delta + committed a1b2c3..d4e5f6 (ancestry ok)
    IN        src/recon/engine.py       M  committed d4e5f6
    IN        tests/test_recon.py       M  committed d4e5f6
    ADVISORY  docs/spec/recon.md        M  committed d4e5f6  (verify hunks are under ## Implementation Questions)
    OUT       docs/plan.md              M  uncommitted      <- boundary finding (leaf pin violated)
  SCOPE: VIOLATION (1 path)
  Options: revert path (git checkout -- docs/plan.md) | accept & widen scope | stop
```

- The token line is `SCOPE: CLEAN` or `SCOPE: VIOLATION (N paths)` on its own;
  `N` counts `OUT` paths plus a `HISTORY_REWRITE` and a `GIT_STATE` finding;
  `ADVISORY` paths do not count. A `HISTORY_REWRITE` line is rendered above the
  path list
  (`  HISTORY_REWRITE  HEAD_after d4e5f6 does not descend from HEAD_before a1b2c3`).
- A **`GIT_STATE`** finding (§3 git-state observation) renders as a line
  **inside this block**, exactly parallel to `HISTORY_REWRITE` and above the
  path list, and counts into `SCOPE: VIOLATION (N paths)`. **No new gate token
  is introduced** and the REQ-ORCH-034 signal order is unchanged. Shape:

  ```
    GIT_STATE  stash count 0 -> 1; 9 path(s) dirty before and clean after with no
               commit (docs/plan.md, docs/spec/telemetry.md, …)
  ```

  Its options are `restore │ accept (note) │ stop` (§8), and `proceed` is
  withheld while the finding is unresolved — the same withholding rule an
  unresolved `OUT` path carries.
- **The orchestrator branches on the token, not on prose.** `VIOLATION` → the
  gate offers, per `OUT` path, `revert path | accept & widen scope | stop`
  **before the per-chunk gate's commit** (sequential) or the leaf's merge
  (fan-out): the scope options are resolved inside the per-chunk gate
  (`harness-chunk-verifier.md` §Sequencing — Sequential Mode; §7 below), and
  `proceed` there is unavailable while any `OUT` path is unresolved. `CLEAN`
  → the per-chunk gate continues to `CHUNK_VERDICT:`; at a non-implement stage
  gate it continues to the review `VERDICT:`.
- **Revert targets.** Sequential dispatch → the **working tree**:
  `git checkout -- <path>` for tracked, `rm` for untracked, and
  `git reset --soft HEAD_before` + re-checkout if the leaf committed. Fan-out
  leaf → the **leaf branch** (`git checkout` / `git reset` in the leaf's
  worktree), never the integration branch. Under marker `4` the integration
  branch is the workstream branch, not `main` (§9).
- **Position.** The block is rendered where REQ-ORCH-034 fixes it
  (`orchestration.md` §v5): inside the per-chunk gate block after
  `RETURN.status` / `budget_consumed` and before `CHUNK_VERDICT:`; at a
  non-implement stage gate after `RETURN.status` and before the review
  `VERDICT:`. When `CLEAN`, only the token line appears in the gate block; the
  full finding block appears only on `VIOLATION`.
- **Catch-up.** Under remedy (ii) (§3) the `Observed writes` header line
  carries `CATCH-UP <from>..<base> (N commits, excluded — base <sha>)` before
  the path list; the line is absent when `N == 0`.

**Recorded limitations, accepted for v1 (REQ-HARN-026)** — not fixed in this cycle:

- **(a) Hunk-level intent.** Implement legitimately edits spec files only
  inside `## Implementation Questions` (Q-IMPL); replan only for a Level-2
  inline change. A path-level check cannot see that, so such writes are
  `ADVISORY` until a hunk-level check (`git diff -U0`, verify every hunk's
  enclosing heading) exists. Partially closed for Markdown paths by §3 section
  resolution (`arbitrated-handoff.md`) — it resolves each fix hunk to its
  enclosing `§Name` for arbitration; the `ADVISORY` tag rule itself is
  unchanged (Q-IMPL-HARNESSP2-002).
- **(b) Ignored paths.** Paths matched by `.gitignore` are not observed
  (`--ignored` is not used) — they are not project content.
  - **Exception — `.sdd/`.** The telemetry file is observed by the third
    observation of §3 (line count + entry list), not by porcelain; its finding
    strings and the revert rule are defined once in `telemetry.md` §4.
- **(c) Catch-up fast-forward false positive.** A worktree provisioned at a
  stale HEAD and told to fast-forward to the tip shows the whole
  `HEAD_prov..tip` delta as committed writes (RS-HARNESSP2-001 Q6: 20 false
  `OUT` paths on the first dispatch of the harness-p2 cycle). Remedied by the
  snapshot base rule (§3, REQ-HARN-HARNESSP2-001): **(i)** provision every
  sequential-pipeline, fix, verifier, review and red worktree at the tip the
  leaf is told to reach — the default, cheaper (one `rev-parse` before
  provisioning) and removes the class rather than reporting it; **(ii)** when
  a hand-written prompt, entry kickoff or resumed session still names a base,
  take `HEAD_before` at that named base, exclude `HEAD_prov..base` from the
  window and render the `CATCH-UP` line. Contract:
  `docs/spec/dispatch-snapshot-base.md`.
- **(d) Round trip within one dispatch.** A file modified and then reverted to
  its original content inside the dispatch — or created and then deleted —
  stays invisible: **unchanged**, because a content hash cannot see a round
  trip either.
- **Closed, not a limitation:** a path **already dirty or untracked at snapshot
  time** and written again during the dispatch is now observed by the
  content-hash observation of §3 (REQ-HARN-HARNESSP3-001); it is no longer
  recorded here.
- Writes outside the repository (scratchpad, `$TMPDIR`) are the sandbox's
  concern, not this check's.
- **Closed, not a limitation:** the stash stack and the rest of git state are
  observed by the git-state observation of §3 (REQ-HARN-HARNESSP6-001) — a leaf
  that stashes, switches branch or reverts a dirty path raises `GIT_STATE`
  instead of the `SCOPE: CLEAN` the harness-p5 incident produced.

---

**`HISTORY_REWRITE` — no automatic reset (from `../SKILL.md` §Isolation
Discipline rule 4).** The finding covers an amend, rebase or reset inside the
dispatch. The orchestrator surfaces it above the path list, counts it as a
`SCOPE: VIOLATION`, and offers **only `stop`** plus a manual recovery hint
(`git reflog` in the affected tree). It never runs `git reset` on the working
tree or a branch, never force-moves a ref and never merges a rewritten leaf
branch on its own initiative — observe and report; the operator decides.

## 6. Blocked-write fallback: pre-persist match (REQ-HARN-023)

When `RETURN.blocked_writes` is non-empty, the orchestrator runs the **same
scope match** (§4) on each labeled `path` **before** persisting its `content`:

- `IN` → persist, then include the path in the finding as `IN … persisted by
  orchestrator`.
- `ADVISORY` → persist and tag as above.
- `OUT` → **do not persist**; list it as a boundary finding
  (`OUT docs/plan.md  blocked-write  <- refused`) and let the operator choose
  `persist & widen scope | drop | stop` at the gate.

The orchestrator's persistence is the observable event here, so the three
commands alone cannot catch it — hence the pre-persist match. A fan-out leaf
returning `blocked_writes: [{path: docs/plan.md, …}]` is therefore refused
(plan writes are barred by `fan-out.md` §2); its plan marks belong in
`tasks_completed`, its column fills in `traceability_fills`, and its spec
deviations in `open_questions` — the orchestrator files the Q-IMPL entry at
merge (`fan-out.md` §3e).

**Scratchpad staging path — expected, not an anomaly (REQ-HARN-HARNESSP2-002).**
For research leaves and fix leaves that write prose about the harness, the
following is the **expected** write path (RS-HARNESSP2-001 recorded it twice:
the `Write` tool refused the research artifact and the worktree guard refused a
shell heredoc whose prose merely mentioned version-control commands; staging
under a neutral name and copying in worked both times):

| # | Statement |
|---|---|
| (i) trigger | the harness's `Write` tool may refuse an artifact whose prose is about the harness or about version control, and the worktree guard may refuse a shell heredoc whose **prose** mentions version-control commands — including inside heredocs and even when no such command is executed |
| (ii) path | stage the content in the scratchpad under a **neutral filename** (no version-control or harness vocabulary in the name), then copy or patch it into the repository at its final path |
| (iii) scope match | the pre-persist match of REQ-HARN-023 and the snapshot pair observe the **final repository path**; the scratchpad name is never matched and never appears in the finding |
| (iv) `blocked_writes` | reserved for writes that the fallback **also** could not land; a leaf that used the staging path reports `blocked_writes: []` and the file appears in the observed window as an ordinary `IN` path |

The dispatch templates are unchanged (no template tells the leaf how to write
files); this is a documentation statement on this reference only. The
orchestrator does not treat a staged-then-copied write differently from any
other `IN` path. Contract: `docs/spec/dispatch-snapshot-base.md` §Blocked-Write
Staging Path.

---

## 7. Commit ownership (REQ-HARN-024)

| Dispatch type | Who commits | Return carries |
|---|---|---|
| pipeline (sequential stage) | **orchestrator**, on `proceed` at the stage gate | `files_written`; leaf is not instructed to commit |
| pipeline (sequential per-chunk implement) | **orchestrator**, on `proceed` at the **per-chunk gate** (below) | `files_written`; leaf is not instructed to commit |
| fix re-dispatch / redo (sequential) | **orchestrator**, on `proceed` at the per-chunk gate (implement) / stage gate (other stages) | `files_written` |
| fan-out leaf (and its redo) | **leaf**, on its own branch with inline identity flags (REQ-ORCH-027); the orchestrator merges on `proceed` at the per-leaf gate | `commits` |
| review | nobody | — |
| chunk verifier | nobody | `files_written: []` |
| aggregate regeneration (marker `4`, post-gate bookkeeping) | **orchestrator**, in its **own** commit, separate from any leaf's | — (not a dispatch; driven by the session dirty flag) |
| plan `status: complete` flip (post-gate bookkeeping) | **orchestrator**, in its **own** commit at the implement **stage gate** on `proceed`, after the `COMMIT:` closing line | — (not a dispatch; no leaf returns this path) |

### 7b. Commit message attribution — the driver adds none

**The orchestrator adds no attribution trailer to any commit it makes, and
instructs no leaf to add one.** No co-authorship trailer, no "generated with"
footer, no tool-identifying line of any kind. This holds for every commit in
the table above — stage, per-chunk, fix, bookkeeping, `status:` flip — and for
any pull-request body the driver composes. (The trailer keys are deliberately
not spelled out here: `tools/skill-lint.py` carries a `[forbidden]` rule
against them appearing in committed content, and this file is committed
content.)

**This rule lives here, in the driver, on purpose.** It does **not** depend on
a project-level `CLAUDE.md`, an `AGENTS.md`, or a harness-supplied attribution
default being read, present, or correctly precedence-ordered. A driver that
commits at every gate must carry its own commit conventions; relying on a file
outside the skill is how the convention silently lapses in a repository whose
`CLAUDE.md` is missing, unread, or overridden.

**Recorded 2026-09-21**, after the driver added a co-authorship trailer to
twenty consecutive commits in *this* repository — whose `CLAUDE.md` forbids it
and whose own linter already rejects the same string in file content — having
deferred to a harness-supplied default that itself stated the project's
instructions take precedence. The convention was encoded in two places and the
driver still missed it, because neither place is consulted at commit time. That
is the gap this section closes.

**Precedence, stated once so it needs no re-derivation.** If a project's own
instructions specify an attribution format, follow them. If they forbid
attribution, add none. If they are silent, add none — silence is not consent to
a trailer, and a commit with no trailer is trivially amendable while twenty with
one are not. A harness- or tool-supplied attribution default never overrides
either the project's instructions or this rule.

**Aggregate-regeneration bookkeeping commit (REQ-WS-HARNESSP3-001).** Under
marker `4` the shared `docs/requirements/traceability.md` is regenerated
wholesale from the per-ws files by the **orchestrator**, never by a leaf, and
committed on its own — it is never folded into the chunk/stage commit that
carries the leaf's `files_written`, and never into a leaf's branch commit under
fan-out. It runs **after** the snapshot window closes, so it is never observed
by the write-scope check (§9), and it fires at **every** gate outcome —
`proceed`, `loop-back-to-fix` and `stop` alike — whenever a leaf wrote per-ws
traceability rows since the last regeneration (`../SKILL.md` §The gate;
`fan-out.md` §3e for the fan-out path). Regeneration is wholesale and
idempotent, so a repeat costs nothing and never compounds.

The trigger is a **session dirty flag** (`docs/spec/ws-traceability.md`
Q-IMPL-HARNESSP3-011) set whenever a leaf's `RETURN.traceability_fills` is
non-empty and cleared after a successful regeneration commit — so a gate whose
flag is clear regenerates nothing, and a stopped or looped-back stage never
leaves the aggregate stale. The flag is session state, not an artifact; on a
resumed session it starts **set**, costing at most one redundant regeneration
and never a missed one. Leaves never write this path: it is absent from every
orchestrated `{write_scope}` by construction (§2), and that absence *is* the
signal the leaf reads.

**Plan-completion bookkeeping commit (REQ-HARN-HARNESSP5-001).** The second
bookkeeping write, beside aggregate regeneration: at the implement **stage
gate**, on `proceed`, after the `COMMIT:` closing line, the orchestrator flips
`docs/ws/<id>/plan.md` `status:` to `status: complete` in its **own** commit,
editing `status:` only — `plan`'s `research_id:` stamp is byte-identical
before and after. The path is the orchestrator's, never a leaf's: the per-chunk
PIPELINE template says "tick tasks, never `status:`", `verify` never writes
the plan, and a leaf that wrote `status:` would be a `SCOPE: VIOLATION`. Because
`HEAD_landed` is captured before any bookkeeping commit (§7a), the flip falls
outside the `COMMIT:` comparand range and can never render `landed, not
observed`. When the completion parse finds an unticked task the flip is withheld
and the gate pauses on `PLAN: INCOMPLETE (N of M ticked)` with `replan │ stop`
only (`loop-control.md` §5 signal 6b, §6). Owning specs:
`docs/spec/harness-loop-control.md` §Plan Completion Ownership Under
Orchestration; `docs/spec/harness-write-scope.md` §Commit Ownership.

Each template's return step states its row (`dispatch-templates.md` §PIPELINE
step 4, §REVIEW, §CHUNK VERIFIER; `fan-out.md` §2 step 3). A pipeline leaf that
commits anyway is not a scope violation (its commit falls inside the observed
window and is matched by path), but the template no longer invites it, and the
orchestrator's own commit then becomes a no-op for those paths.

**Per-chunk gate (implement stage).** After each chunk's implement dispatch
returns, the orchestrator runs the write-scope check, dispatches the chunk
verifier, then shows the operator a compact block — `RETURN.status`, the
`SCOPE:` line, the `CHUNK_VERDICT:` line, files changed — with the choices
**proceed** (the orchestrator commits the chunk) │ **fix** (re-dispatch the
chunk with a repair packet; counts toward the per-chunk redo cap) │ **stop**.
The single implement-stage review gate remains once, after all chunks. Under
fan-out the equivalent happens per leaf before its merge, with no commit by the
orchestrator (the leaf already committed on its branch). Stated identically in
`harness-chunk-verifier.md` §Sequencing — Sequential Mode, `orchestration.md`
§v5 and `../SKILL.md` §Per-chunk implement dispatch and per-chunk gate:

```
Per-chunk gate — implement dispatch #2 (Chunk 2: Reconciliation)   [fan-out: leaf wt-g1 / branch fanout-g1]
  RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 22, test_runs: 3}  vs  Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs
  SCOPE: CLEAN                                    # full write-scope block above when VIOLATION
  CHUNK_VERDICT: PASS                             # verifier findings (Check 1 / Check 3 / Gates) listed above when FAIL
  Files changed  : src/recon/engine.py M, tests/test_recon.py M, docs/plan.md M
  Redo           : 0 of 3 (per-chunk redo counter)
  Options: proceed (orchestrator commits the chunk) │ fix (re-dispatch Chunk 2 with a repair packet; counts toward the per-chunk redo cap) │ stop
```

`proceed` is unavailable while any `OUT` path is unresolved; the scope options
(`revert path | accept & widen scope | stop`) are resolved first, inside this
gate, and the gate is re-rendered with the resulting `SCOPE:` line.

### 7a. Commit-fidelity check — `COMMIT: COMPLETE | INCOMPLETE` (REQ-HARN-HARNESSP4-001, -002, -003)

This is the **skill-side defining section** for the check (the lint row's
`fix:` points here; spec: `docs/spec/harness-commit-fidelity.md`). The write-
scope check above asks *did the leaf write only where it was allowed to?* —
a pre-decision question about the leaf. The commit-fidelity check asks *did
the orchestrator land everything the leaf wrote?* — a **post-decision**
question about the orchestrator's own commit, computable only after `proceed`.
It shares the observed-writes set as an input and nothing else: subject, gate
position, token family, pause options and telemetry group are its own.

**Comparands.**

```
landed   := git diff --name-only --no-renames -z <HEAD_before> <HEAD_landed>
            # -z: NUL-separated output, split on \0, so a space in a path stays one path
            # a two-sha RANGE, captured right after the orchestrator's own commit
            # (or merge) and BEFORE any bookkeeping commit — never `git show HEAD`
expected := <mode-specific path set — table below>
COMMIT: COMPLETE (N paths)                                        # expected == landed; N = |landed|, distinct paths
COMMIT: INCOMPLETE (k observed, not landed: <paths>[; j landed, not observed: <paths>])
```

- `HEAD_before` is the integration-line HEAD taken by `snapshot(before)`
  immediately before the dispatch — the same sha `committed_delta` (§3, term
  (b)) starts from — and it is the range start **unconditionally**: it equals
  the gate-time HEAD whenever the leaf did not commit, and precedes the leaf's
  commits when it did, so a compliant-but-eager leaf that committed anyway
  (§7 above tolerates it) counts as landed with no special case.
- `HEAD_landed` is the integration-line HEAD immediately after the
  orchestrator's own chunk/stage commit (sequential) or merge (fan-out merge
  step), **before** the aggregate-regeneration commit or any other bookkeeping
  commit. Capture both shas first, then diff the range; never diff against a
  moving `HEAD`.
- **Why the range and not `git show --name-only HEAD`** (RS-HARNESSP4-001 §Q1):
  `git show HEAD` names only the *last* commit — under fan-out a fast-forward of
  a two-commit leaf renders a false `INCOMPLETE`, a true merge commit shows an
  empty combined diff, and in sequential marker-4 mode the aggregate-
  regeneration commit at every implement chunk would hide the chunk commit.
  `--no-renames` keeps a rename as two paths on both sides (§3 observes both).
- The token has **exactly two members**. `COMPLETE (N paths)` counts
  **distinct** paths (the strict-set rule of §3 applies to both operands);
  `INCOMPLETE` carries the `k observed, not landed: …` clause and, only when
  `j > 0`, the `; j landed, not observed: …` clause on the **same line**. Paths
  are repo-relative, sorted, comma-separated; the line is an own-line token
  parsed as `^COMMIT:`, like `SCOPE:`. No third token exists for any case
  (`fan-out.md` §3b explains why a merge drop needs none). A read-only or no-op
  dispatch that reached `proceed` renders `COMMIT: COMPLETE (0 paths)`; review,
  verifier and red dispatches never commit and render no `COMMIT:` line at all.

**Comparand table.**

| Gate | `expected` | `landed` | When computable | Position in the gate |
|---|---|---|---|---|
| sequential per-chunk gate and stage gate, on `proceed` | **observed writes only** — `porcelain_delta ∪ committed_delta ∪ content_delta` (§3) | `git diff --name-only --no-renames -z HEAD_before HEAD_landed` (NUL-separated, split on `\0`), captured right after the orchestrator's commit and before any bookkeeping commit | post-decision | closing line of the same gate — item 8 of `loop-control.md` §5 |
| fan-out **per-leaf** gate | the leaf's observed writes in its worktree | the leaf's committed delta `git diff --name-only --no-renames -z <base> <tip>` (split on `\0`) — the write-scope check's own term (b) | pre-decision | position **2b** of `loop-control.md` §5 — after `SCOPE:`, before `CHUNK_VERDICT:` (`fan-out.md` §3a.v) |
| fan-out **merge step**, per branch | that leaf's committed delta `base..tip` | `git diff --name-only --no-renames -z PRE_MERGE HEAD` on the integration branch (split on `\0`) | post-`proceed`, at merge | closing line after the merge — item 8 (`fan-out.md` §3b) |

`base`, `tip` and `PRE_MERGE` are the shas `fan-out.md` §3a.v / §3b already
compute; the check introduces no git state, no leaf, no counter and no artifact.

**Sequential `expected` is the observed-writes set only (REQ-HARN-HARNESSP4-002).**
`RETURN.files_written` is **never an operand** of `expected`. A path the leaf
*claims* but never wrote — or wrote and reverted, so no delta observes it —
cannot land; unioning the claim in would render `COMMIT: INCOMPLETE (observed,
not landed)` for a defect of the leaf's *return*, not of the orchestrator's
commit: a false pause on a load-bearing signal. The claim-vs-observation gap is
instead the **return-drift warning** `RETURN drift: <k> path(s) claimed, not
observed: <paths>` (`RETURN.files_written − observed`), owned by
`return-contract.md` §1 — a warning beside `KEYS MISSING`, never a pause and
never a `COMMIT:` term. This is the sequential analogue of the fan-out clause
`RETURN.commits ⊆ git rev-list <base>..<tip>` (`fan-out.md` §3a.v): both keep a
leaf's return error out of the landed-vs-observed comparison.

**Placement.** In sequential mode the line cannot sit between `SCOPE:` and
`CHUNK_VERDICT:` without asserting a commit that has not happened, so it renders
as the **post-decision closing line of the same gate**, immediately after the
commit and **before the next dispatch** — never deferred to the next gate the
way `TELEMETRY: rec <n>` is (telemetry is never load-bearing; `COMMIT:` exists
to be). The canonical order — item 8 and position 2b — is `loop-control.md`
§5; this section states the comparands, not the order.

**On `INCOMPLETE` the gate pauses** with three options:

| Option | Effect |
|---|---|
| `amend (add the missing paths to the commit)` | the orchestrator stages every `observed, not landed` path and amends **its own** commit — never a leaf's commit and never a merge commit (`fan-out.md` §3b: `amend` is unavailable at the merge step) — then re-renders the line, which must now read `COMPLETE`. The write-scope check is **not** re-run: every amended path came from the observed set and was already classified there (`IN` / `ADVISORY` by construction — an `OUT` path could not have reached `proceed`). A `landed, not observed` clause is not amendable; it resolves by `accept (note)` or `stop` |
| `accept (note)` | the note is recorded in the gate text and — if the path is never landed in a later commit of the cycle — in the plan's existing blocked-task note (`loop-control.md` §Circuit-break checkpoint): the only durable traces REQ-HARN-027 / REQ-ORCH-014 allow. No new artifact |
| `stop` | as everywhere: the session ends at this gate; the partial commit stands and the pause text names the un-landed paths |

**No next dispatch is issued until the pause is resolved** — including the
implement-stage review after the last chunk: a review dispatched against an
un-landed tree reviews the wrong artifact. `COMPLETE` needs no acknowledgement
and does not alter the options. The pause is a member of the pause family
beside `RETURN: MALFORMED`, `SCOPE: VIOLATION`, `REVIEW: CONTRADICTION` and
budget exhaustion (`loop-control.md` §5, §6); telemetry normalises `amend` to
`gate.decision: other`.

---

## 8. Operator options — summary

| Finding | Options at the gate | Effect |
|---|---|---|
| `OUT` path (observed write) | `revert path` │ `accept & widen scope` │ `stop` | revert per §5 targets; widen = session-only (§1); `proceed` blocked until resolved |
| `OUT` path (`blocked_writes`) | `persist & widen scope` │ `drop` │ `stop` | never persisted without an explicit widen (§6) |
| `ADVISORY` path | none required — hint shown | operator eyeballs the hunk; counts 0 toward `N` |
| `HISTORY_REWRITE` | `stop` + manual recovery hint | never an automatic reset |
| `GIT_STATE` (§3 git-state observation) | `restore` │ `accept (note)` │ `stop` | a stash is recoverable: `restore` is `git stash pop` for the stash case and `git checkout -- <path>` for a reverted path; `accept (note)` records the acceptance in ephemeral gate text only; `proceed` is withheld while the finding is unresolved |
| verifier / review wrote anything | every path `OUT`; revert before any redo | `loop-control.md` §1b Verifier edge cases |
| `COMMIT: INCOMPLETE` (post-decision, §7a) | `amend` │ `accept (note)` │ `stop` | `amend` stages only `observed, not landed` paths into the orchestrator's own commit, no write-scope re-run; no next dispatch until resolved |

---

## 9. Marker-4 rooting

Under `docs/.sdd-version` == `4` the default table's execution-artifact paths
resolve to `docs/ws/<id>/…` (`docs/ws/<id>/plan.md`, `docs/ws/<id>/plan-*.md`,
`docs/ws/<id>/plan-history/**`, `docs/ws/<id>/verification.md`,
`docs/ws/<id>/traceability.md` — the aggregate
`docs/requirements/traceability.md` is **not** in any orchestrated leaf row, §2);
the shared corpus paths
(`docs/research/**`, `docs/requirements/**`, `docs/spec/**`) are unchanged.
The fan-out `<base>` is the workstream branch point (`fan-out.md` §0), and
every revert / merge target is the **workstream branch**, never `main`. Under
marker `3` the flat paths and `main` apply unchanged. The orchestrator's
marker-4 aggregate regeneration — `fan-out.md` §3e under fan-out, the post-gate
step of `../SKILL.md` §The gate in sequential mode — happens after the snapshot
and is never observed, and lands in its own bookkeeping commit (§7).
