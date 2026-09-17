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
`docs/ws/<id>/` equivalents (`docs/ws/<id>/traceability.md` plus the
regenerated aggregate `docs/requirements/traceability.md`), while
`docs/research/**`, `docs/requirements/**` and `docs/spec/**` stay shared
(§9).

| Stage / dispatch | Default write scope | Note |
|---|---|---|
| research | `docs/research/RS-NNN-*/**`, `docs/research/index.md` | `sdd-research` Steps 5–6 |
| requirements | `docs/requirements/**` | category files, `index.md`, `traceability.md` rows |
| specs | `docs/spec/**`, `docs/requirements/traceability.md` | traceability: Spec column only |
| plan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**` | rewrite archives, never `-replan-` |
| implement (sequential, per chunk) | the chunk's source/test paths, `docs/plan.md`, `docs/plan-*.md`, `docs/requirements/traceability.md`, `docs/spec/*.md` (**ADVISORY**), `docs/plan-history/*-complete.md`, `docs/research/RS-NNN-*/**` + `docs/research/index.md` | traceability: Test/Implementation columns; spec writes = Q-IMPL entries; `-complete` archives multi-milestone only; research paths spike tasks only |
| verify | `docs/verification.md`, `docs/requirements/traceability.md` | traceability: Verified column (Step 3b) |
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
omitted `sdd-verify`'s Verified-column write; a legitimate side-write a skill
instructs today is tagged `IN`, never a false `VIOLATION`. A verify dispatch
filling the Verified column is `SCOPE: CLEAN`.

---

## 3. Observation: three commands (REQ-HARN-021)

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

The "before" snapshot is taken immediately before dispatch and the "after"
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
  `.claude/worktrees/`) cancel — only the *delta* is a write.
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
  `N` counts `OUT` paths plus a `HISTORY_REWRITE` finding; `ADVISORY` paths do
  not count. A `HISTORY_REWRITE` line is rendered above the path list
  (`  HISTORY_REWRITE  HEAD_after d4e5f6 does not descend from HEAD_before a1b2c3`).
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

**Recorded limitations, accepted for v1 (REQ-HARN-026)** — not fixed in this cycle:

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

---

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

---

## 8. Operator options — summary

| Finding | Options at the gate | Effect |
|---|---|---|
| `OUT` path (observed write) | `revert path` │ `accept & widen scope` │ `stop` | revert per §5 targets; widen = session-only (§1); `proceed` blocked until resolved |
| `OUT` path (`blocked_writes`) | `persist & widen scope` │ `drop` │ `stop` | never persisted without an explicit widen (§6) |
| `ADVISORY` path | none required — hint shown | operator eyeballs the hunk; counts 0 toward `N` |
| `HISTORY_REWRITE` | `stop` + manual recovery hint | never an automatic reset |
| verifier / review wrote anything | every path `OUT`; revert before any redo | `../SKILL.md` §Verifier edge cases |

---

## 9. Marker-4 rooting

Under `docs/.sdd-version` == `4` the default table's execution-artifact paths
resolve to `docs/ws/<id>/…` (`docs/ws/<id>/plan.md`, `docs/ws/<id>/plan-*.md`,
`docs/ws/<id>/plan-history/**`, `docs/ws/<id>/verification.md`,
`docs/ws/<id>/traceability.md` + the regenerated aggregate
`docs/requirements/traceability.md`); the shared corpus paths
(`docs/research/**`, `docs/requirements/**`, `docs/spec/**`) are unchanged.
The fan-out `<base>` is the workstream branch point (`fan-out.md` §0), and
every revert / merge target is the **workstream branch**, never `main`. Under
marker `3` the flat paths and `main` apply unchanged. The orchestrator's
marker-4 aggregate regeneration in `fan-out.md` §3e happens after the snapshot
and is never observed.
