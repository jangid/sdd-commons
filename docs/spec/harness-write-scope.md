---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-HARN-020
  - REQ-HARN-021
  - REQ-HARN-022
  - REQ-HARN-023
  - REQ-HARN-024
  - REQ-HARN-025
  - REQ-HARN-026
---

# Harness Write Scope

## Context

A dispatched leaf can write anywhere in the repository; the only boundary today
is the fan-out worktree pin's prose ("do NOT edit the shared plan or
traceability files"), which nothing checks. RS-008 Q5 established that a
`git status --porcelain` before/after diff is necessary but not sufficient
(committed writes vanish from porcelain), that who commits differs per dispatch
type and is not pinned by any shipped contract, and that the observation must
be taken before the orchestrator's own gate commit.

This spec defines the declared write scope per dispatch, the default scope
table, the three-command observation, the `SCOPE:` finding surfaced as gate
text, the check on the blocked-write fallback, commit ownership per dispatch
type, snapshot ordering and the recorded v1 limitations. It fulfils
REQ-HARN-020..026. Procedure text lands in
`skills/sdd-orchestrate/references/write-scope.md` with a stub in `SKILL.md`.

## Design

### Declared Write Scope Slot (REQ-HARN-020)

Every leaf template carries `Write scope: {write_scope}` — a comma-separated
glob list of repository-relative paths the subagent may create, modify, delete
or rename. Glob semantics: `**` matches any depth, `*` within a segment; a
directory path with trailing `/**` covers everything under it; an exact file
path matches only that file. The review and verifier templates carry the slot
with the literal value `(empty — read-only)`.

The orchestrator fills the slot from the default table; the operator may widen
it at the gate (the widened scope applies to that dispatch's redo and the
following dispatches of the same stage in this session).

### Default Scope Table

Marker `3` paths. Under marker `4`, `docs/plan*.md`, `docs/plan-history/**`,
`docs/verification.md` and the traceability write resolve to their
`docs/ws/<id>/` equivalents (`docs/ws/<id>/traceability.md` plus the
regenerated aggregate `docs/requirements/traceability.md`), while
`docs/research/**`, `docs/requirements/**` and `docs/spec/**` stay shared.

| Stage / dispatch | Default write scope | Note |
|---|---|---|
| research | `docs/research/RS-NNN-*/**`, `docs/research/index.md` | `sdd-research` Steps 5–6 |
| requirements | `docs/requirements/**` | category files, `index.md`, `traceability.md` rows |
| specs | `docs/spec/**`, `docs/requirements/traceability.md` | traceability: Spec column only |
| plan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**` | rewrite archives, never `-replan-` |
| implement (sequential, per chunk) | the chunk's source/test paths, `docs/plan.md`, `docs/plan-*.md`, `docs/requirements/traceability.md`, `docs/spec/*.md` (**ADVISORY**), `docs/plan-history/*-complete.md`, `docs/research/RS-NNN-*/**` + `docs/research/index.md` | traceability: Test/Implementation columns; spec writes = Q-IMPL entries; `-complete` archives multi-milestone only; research paths spike tasks only |
| verify | `docs/verification.md`, `docs/requirements/traceability.md` | traceability: Verified column (Step 3b) |
| replan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**`, `docs/spec/*.md` (**ADVISORY**) | `-replan-` archives; spec only for a Level-2 inline change |
| fan-out leaf | the chunk-group's code and test paths **only** | plan + traceability barred by `fan-out.md` §2 |
| review, chunk verifier | *(empty — read-only)* | any write is `OUT` |

"The chunk's source/test paths" are derived by the orchestrator from the
chunk's task list and the spec's implementation-module convention
(`chunk-close-review.md` Check 3 step 1); when they cannot be derived, the
orchestrator declares the project's source and test roots (e.g. `src/**`,
`tests/**`) and notes the widening at the gate.

**Re-walk note (rationale)**: the table was re-walked on 2026-09-17 against
every stage skill's `SKILL.md` after review finding C1 showed a first draft
omitted `sdd-verify`'s Verified-column write; a legitimate side-write a skill
instructs today is tagged `IN`, never a false `VIOLATION`.

### Observation: Three Commands (REQ-HARN-021)

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

For a fan-out leaf the same three commands run against the worktree path with
`<base>` (the branch point) in place of `HEAD_before` and the branch tip in
place of `HEAD_after`.

Rules: `--untracked-files=all` expands untracked directories to file paths;
paths present in both snapshots (pre-existing untracked noise such as
`.claude/worktrees/`) cancel; deletions (`D`) and renames (`R`, both old and new
path) count as writes; a file modified and reverted within the dispatch is
invisible (accepted). A porcelain-only check is explicitly insufficient because
committed writes vanish from porcelain output. A non-zero ancestry exit is a
`HISTORY_REWRITE` finding, surfaced above the path list and counted as a
violation.

### Matching and Tags

Every observed path is matched against the declared scope:

| Tag | Condition |
|---|---|
| `IN` | matches a declared glob |
| `ADVISORY` | matches a glob marked **ADVISORY** in the default table (`docs/spec/*.md` under implement or replan) — hunk-level intent cannot be verified by path |
| `OUT` | matches nothing → boundary finding |

`ADVISORY` paths carry a hint: implement → "verify hunks are under ##
Implementation Questions"; replan → "verify this is the Level-2 spec change".

### Finding Format and `SCOPE:` Token (REQ-HARN-022)

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
  `N` counts `OUT` paths plus a `HISTORY_REWRITE` finding; `ADVISORY` paths do
  not count.
- The orchestrator branches on the token, not on prose. `CLEAN` → the gate
  proceeds to the review verdict; `VIOLATION` → the gate offers, per `OUT`
  path, `revert path | accept & widen scope | stop` before any merge or commit.
- Revert target: sequential dispatch → the working tree (`git checkout --
  <path>` for tracked, `rm` for untracked, `git reset --soft HEAD_before` +
  re-checkout if the leaf committed); fan-out leaf → the **leaf branch**
  (`git checkout`/`git reset` in the worktree), never the integration branch.
  Under marker `4` the integration branch is the workstream branch, not `main`.
- The block is rendered at the position REQ-ORCH-034 fixes (after `VERDICT:`
  and any `CHUNK_VERDICT:` lines, before `RETURN.status` / budget).

### Blocked-Write Fallback (REQ-HARN-023)

When `RETURN.blocked_writes` is non-empty, the orchestrator runs the **same
scope match** on each labeled `path` **before** persisting its `content`:

- `IN` → persist, then include the path in the finding as `IN … persisted by
  orchestrator`.
- `ADVISORY` → persist and tag as above.
- `OUT` → **do not persist**; list it as a boundary finding
  (`OUT docs/plan.md  blocked-write  <- refused`) and let the operator choose
  `persist & widen scope | drop | stop` at the gate.

The orchestrator's persistence is the observable event here, so the three
commands alone cannot catch it — hence the pre-persist match.

### Commit Ownership (REQ-HARN-024)

| Dispatch type | Who commits | Return carries |
|---|---|---|
| pipeline (sequential stage, per-chunk implement) | **orchestrator**, after the gate | `files_written`; leaf is not instructed to commit |
| fix re-dispatch / redo (sequential) | **orchestrator**, after the gate | `files_written` |
| fan-out leaf (and its redo) | **leaf**, on its own branch with inline identity flags (REQ-ORCH-027) | `commits` |
| review | nobody | — |
| chunk verifier | nobody | `files_written: []` |

Each template's return step states its row. A pipeline leaf that commits anyway
is not a scope violation (its commit falls inside the observed window and is
matched by path), but the template no longer invites it, and the orchestrator's
own commit then becomes a no-op for those paths.

### Snapshot Ordering (REQ-HARN-025)

```
snapshot(before) → dispatch → await return → snapshot(after) → scope check → gate → orchestrator commit
```

The "before" snapshot is taken immediately before dispatch and the "after"
snapshot immediately on return, **before** the orchestrator's own gate commit
and before any §3e bookkeeping writes, so the orchestrator's commit and
bookkeeping are never inside the observed window and cannot be flagged. The
ordering is stated in `references/write-scope.md` next to the three commands.

### Recorded v1 Limitations (REQ-HARN-026)

Documented in `references/write-scope.md` beside the finding format; accepted,
not fixed in this cycle:

- **(a) Hunk-level intent.** Implement legitimately edits spec files only
  inside `## Implementation Questions` (Q-IMPL); replan only for a Level-2
  inline change. A path-level check cannot see that, so such writes are
  `ADVISORY` until a hunk-level check (`git diff -U0`, verify every hunk's
  enclosing heading) exists.
- **(b) Ignored paths.** Paths matched by `.gitignore` are not observed
  (`--ignored` is not used) — they are not project content.
- Writes outside the repository (scratchpad, `$TMPDIR`) are the sandbox's
  concern, not this check's. The shared stash stack is out of scope (skills
  never stash).

### Marker-4 Rooting

Under `docs/.sdd-version` == `4` the default table's execution-artifact paths
resolve to `docs/ws/<id>/…`, the fan-out `<base>` is the workstream branch
point, and every revert/merge target is the workstream branch. Under marker `3`
the flat paths and `main` apply unchanged.

## Verification

### Automated
- Lint `REQUIRED` rows: `Write scope:` in both template files
  (`skill-lint-v5.md`).
- Fixture: before snapshot `?? .claude/worktrees/` + after snapshot `?? .claude/
  worktrees/` and ` M docs/plan.md`, committed delta empty, scope
  `src/**` → one `OUT docs/plan.md uncommitted`, `SCOPE: VIOLATION (1 path)`.
- Fixture: porcelain clean after, committed delta `M docs/plan.md`, scope
  `docs/spec/**` → `OUT docs/plan.md committed`, `VIOLATION (1 path)`.
- Fixture: verify dispatch writes `docs/verification.md` +
  `docs/requirements/traceability.md` → both `IN`, `SCOPE: CLEAN`.
- Fixture: implement dispatch writes `docs/spec/recon.md` → `ADVISORY`,
  `SCOPE: CLEAN`.
- Fixture: `blocked_writes: [{path: docs/plan.md, …}]` from a fan-out leaf →
  not persisted, listed as `OUT … refused`.
- Fixture: `HEAD_after` not descending from `HEAD_before` → `HISTORY_REWRITE`,
  `VIOLATION`.

### Manual
- Run one sequential pipeline stage followed by the orchestrator commit: the
  gate showed `SCOPE: CLEAN` and the orchestrator's commit was not in the
  observed window.
- Fan-out with a leaf that edits `docs/plan.md`: `VIOLATION` shown before
  merge; `git log` on the integration branch shows no merge of that branch
  until the path is reverted.

### Acceptance Criteria
- [ ] Pipeline and fan-out templates carry `Write scope:`; the default table lives in `references/write-scope.md` with a `SKILL.md` stub; a verify dispatch filling the Verified column is `SCOPE: CLEAN` (REQ-HARN-020)
- [ ] Observation = porcelain delta ∪ committed delta, plus ancestry check; D/R count; noise cancels; committed out-of-scope writes are flagged with clean porcelain (REQ-HARN-021)
- [ ] The finding format and own-line `SCOPE:` token are in `references/write-scope.md`, referenced from `SKILL.md` §The gate; branching on the token; fan-out revert is on the leaf branch; nothing persisted (REQ-HARN-022)
- [ ] `blocked_writes` paths are scope-matched before persistence; out-of-scope entries are refused and listed (REQ-HARN-023)
- [ ] Commit ownership per dispatch type is stated in each template's return step and tabulated in `references/write-scope.md` (REQ-HARN-024)
- [ ] Snapshot ordering excludes the orchestrator's commit; stated beside the three commands (REQ-HARN-025)
- [ ] Both v1 limitations are recorded beside the finding format; spec-file writes under implement/replan show `ADVISORY` (REQ-HARN-026)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed

## Edge Cases

- **Rename across scope boundary** (`R src/a.py -> docs/a.py`): the new path
  is `OUT`, the old path `IN`; one finding.
- **Leaf creates then deletes a file**: invisible to both deltas — accepted.
- **Leaf amends `HEAD_before`** (history rewrite on a sequential dispatch):
  ancestry check fails → `HISTORY_REWRITE` violation; the option offered is
  `stop` plus a manual recovery hint, never an automatic reset.
- **Operator widens scope at the gate**: recorded as gate text; the widened
  glob applies to the redo and later dispatches of the stage in this session;
  it is never written to a file.
- **Per-chunk implement writes a later chunk's source paths**: `OUT` — the
  scope is the *chunk's* paths, which is precisely the drift the check exists
  to catch; the operator may widen.
- **Marker `4` aggregate traceability regeneration** by the orchestrator in §3e
  happens after the snapshot → never observed.

## Cross-Spec Consistency (XSPEC)

- Default table side-writes agree with `skill-updates.md` per-skill write paths
  (research `RS-NNN-*/findings.md` + index; specs traceability Spec column;
  implement traceability Test/Implementation; verify Verified column; replan
  `-replan-` archives) — consistent.
- `fan-out.md` §2 worktree pin (no plan / traceability writes by leaves) is
  the fan-out-leaf row — consistent; the check mechanically enforces an existing
  pin.
- `deviation-protocol.md` Q-IMPL entries live under `## Implementation
  Questions` in spec files — the `ADVISORY` hint quotes that heading verbatim.
- `orchestration.md` §Gate Protocol vocabulary is extended only by
  `revert path | accept & widen scope`, as REQ-ORCH-034 states.
- `ws-integration.md` merge/revert target under marker `4` = workstream
  branch — restated identically.
- `RETURN.files_written`, `commits`, `blocked_writes` names match
  `harness-return-contract.md`.
- **No unresolved contradictions.**

## Open Questions

1. **Scope for a research-stage spike inside implement** that needs a new
   `RS-NNN` directory: the default table already includes
   `docs/research/RS-NNN-*/**` for spike tasks; the orchestrator substitutes
   the assigned ID. Default: exact assigned-ID directory, not the wildcard.
2. **False-positive rate of the default table** is a dogfooding question
   (RS-008). Default: keep the table as written; widen at the gate and fold
   recurring widenings back into the table in the next cycle.
