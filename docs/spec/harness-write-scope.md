---
status: Approved
last_updated: 2026-09-20
requires:
  - REQ-HARN-020
  - REQ-HARN-021
  - REQ-HARN-022
  - REQ-HARN-023
  - REQ-HARN-024
  - REQ-HARN-025
  - REQ-HARN-026
  - REQ-HARN-HARNESSP3-001
  - REQ-HARN-HARNESSP3-004
  - REQ-REDB-HARNESSP3-004
  - REQ-WS-HARNESSP3-001
  - REQ-HARN-HARNESSP4-004
  - REQ-HARN-HARNESSP4-005
  - REQ-HARN-HARNESSP6-001
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
`docs/ws/<id>/` equivalents (`docs/ws/<id>/traceability.md`), while
`docs/research/**`, `docs/requirements/**` and `docs/spec/**` stay shared.

[Amended 2026-09-18, REQ-WS-HARNESSP3-001] For an **orchestrated** dispatch the
shared aggregate `docs/requirements/traceability.md` is **not** part of any leaf
row: regenerating it is the orchestrator's post-gate bookkeeping (§7 commit
ownership). It appears in a leaf's `{write_scope}` only for a **standalone**
(non-orchestrated) run, where the writing skill regenerates it itself. The rows
below are stated in that amended form; §Leaf Rows Omit the Shared Aggregate
carries the rationale.

| Stage / dispatch | Default write scope | Note |
|---|---|---|
| research | `docs/research/RS-NNN-*/**`, `docs/research/index.md` | `sdd-research` Steps 5–6 |
| requirements | `docs/requirements/**`, minus `docs/requirements/traceability.md` when orchestrated | category files, `index.md`; marker `4`: rows are written to `docs/ws/<id>/traceability.md` |
| specs | `docs/spec/**`; marker `3`: `docs/requirements/traceability.md` — marker `4`: `docs/ws/<id>/traceability.md`; the shared aggregate is omitted when orchestrated | traceability: Spec column only |
| plan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**` | rewrite archives, never `-replan-` |
| implement (sequential, per chunk) | the chunk's source/test paths, `docs/plan.md`, `docs/plan-*.md`, the active traceability file (marker `3` `docs/requirements/traceability.md`, marker `4` `docs/ws/<id>/traceability.md`; the shared aggregate is omitted when orchestrated), `docs/spec/*.md` (**ADVISORY**), `docs/plan-history/*-complete.md`, `docs/research/RS-NNN-*/**` + `docs/research/index.md` | traceability: Test/Implementation columns; spec writes = Q-IMPL entries; `-complete` archives multi-milestone only; research paths spike tasks only |
| verify | `docs/verification.md`, the active traceability file (marker `3` `docs/requirements/traceability.md`, marker `4` `docs/ws/<id>/traceability.md`; the shared aggregate is omitted when orchestrated) | traceability: Verified column (Step 3b) |
| replan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**`, `docs/spec/*.md` (**ADVISORY**) | `-replan-` archives; spec only for a Level-2 inline change |
| fan-out leaf | the chunk-group's code and test paths **only** | plan + traceability barred by `fan-out.md` §2; `docs/spec/*.md` barred too — leaves never write Q-IMPL entries directly; a deviation is returned in `RETURN.open_questions` and the orchestrator files the Q-IMPL entry at merge (§3e) |
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
  `N` counts `OUT` paths plus a `HISTORY_REWRITE` finding plus a `GIT_STATE`
  finding (§Git-State Observation); `ADVISORY` paths do not count.
- The orchestrator branches on the token, not on prose. `VIOLATION` → the
  gate offers, per `OUT` path, `revert path | accept & widen scope | stop`
  **before the per-chunk gate's commit** (sequential) or the leaf's merge
  (fan-out): the scope options are resolved inside the per-chunk gate
  (`harness-chunk-verifier.md` §Sequencing — Sequential Mode), and `proceed`
  there is unavailable while any `OUT` path is unresolved. `CLEAN` → the
  per-chunk gate continues to `CHUNK_VERDICT:`; at a non-implement stage gate
  it continues to the review `VERDICT:`.
- Revert target: sequential dispatch → the working tree (`git checkout --
  <path>` for tracked, `rm` for untracked, `git reset --soft HEAD_before` +
  re-checkout if the leaf committed); fan-out leaf → the **leaf branch**
  (`git checkout`/`git reset` in the worktree), never the integration branch.
  Under marker `4` the integration branch is the workstream branch, not `main`.
- The block is rendered at the position REQ-ORCH-034 fixes
  (`orchestration.md` §v5): inside the per-chunk gate block after
  `RETURN.status` / `budget_consumed` and before `CHUNK_VERDICT:`; at a
  non-implement stage gate after `RETURN.status` and before the review
  `VERDICT:`.

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
| pipeline (sequential stage) | **orchestrator**, on `proceed` at the stage gate | `files_written`; leaf is not instructed to commit |
| pipeline (sequential per-chunk implement) | **orchestrator**, on `proceed` at the **per-chunk gate** (below) | `files_written`; leaf is not instructed to commit |
| fix re-dispatch / redo (sequential) | **orchestrator**, on `proceed` at the per-chunk gate (implement) / stage gate (other stages) | `files_written` |
| fan-out leaf (and its redo) | **leaf**, on its own branch with inline identity flags (REQ-ORCH-027); the orchestrator merges on `proceed` at the per-leaf gate | `commits` |
| review | nobody | — |
| chunk verifier | nobody | `files_written: []` |
| **post-gate bookkeeping (orchestrator-only)** | **orchestrator**, in a **second** commit after the chunk/stage commit | nothing — no leaf returns these paths |

**The second bookkeeping commit** [Added 2026-09-19, harness-p5]. After the
chunk/stage commit of the row above, the orchestrator makes **one further**
commit of its own for paths that are by construction outside **every** leaf's
write scope and therefore never appear in a leaf's observed writes:

| Bookkeeping write | When | Owning spec |
|---|---|---|
| `docs/requirements/traceability.md` — wholesale **regeneration** of the shared aggregate | after any gate whose leaf wrote a per-ws `traceability.md` | `ws-traceability.md`; `references/write-scope.md` §2, §7 |
| a **`descoped`** `Verified` cell in a *previous* workstream's `docs/ws/<other>/traceability.md` — a cross-workstream edit no leaf may make (REQ-WS-HARNESSP5-001) | at the gate that carries the row forward | `ws-traceability.md` §Legal `Verified` Cell Values |
| the `status: complete` flip in `docs/ws/<id>/plan.md` (REQ-HARN-HARNESSP5-001) | implement stage gate, on `proceed`, after the `COMMIT:` closing line | `harness-loop-control.md` §Plan Completion Ownership |

Two properties follow and are required. **(1) Ordering**: the bookkeeping
commit is made **after** `HEAD_landed` is captured, so its paths fall outside
the `COMMIT:` comparand range and can never render `landed, not observed` —
`harness-commit-fidelity.md` §Comparand Table states the same capture point
("right after the orchestrator's commit and before any bookkeeping commit").
**(2) Not a scope violation**: these paths are the orchestrator's own, not a
leaf's, so §Observed Writes Are a Strict Set never sees them; a leaf that wrote
any of them *would* be a `SCOPE: VIOLATION`, which is why the dispatch templates
omit them.

The comparand the `COMMIT:` line diffs is captured with the flags the tool
actually runs — `git diff --name-only --no-renames -z HEAD_before HEAD_landed`
(rename detection off so both sides name the same paths; NUL-separated, split
on `\0`) — stated once in `harness-commit-fidelity.md` §Comparand Table and
carried by the `references/write-scope.md` §7a table; this section does not
restate the table and cannot diverge from it (REQ-HARN-HARNESSP5-002).

**Per-chunk gate (implement stage).** After each chunk's implement dispatch
returns, the orchestrator runs the write-scope check, dispatches the chunk
verifier, then shows the operator a compact block — `RETURN.status`, the
`SCOPE:` line, the `CHUNK_VERDICT:` line, files changed — with the choices
**proceed** (the orchestrator commits the chunk) │ **fix** (re-dispatch the
chunk with a repair packet; counts toward the per-chunk redo cap) │ **stop**.
The single implement-stage review gate remains once, after all chunks. Under
fan-out the equivalent happens per leaf before its merge, with no commit by the
orchestrator (the leaf already committed on its branch). Stated identically in
`harness-chunk-verifier.md` §Sequencing — Sequential Mode and `orchestration.md`
§v5:

```
Per-chunk gate — implement dispatch #2 (Chunk 2: Reconciliation)   [fan-out: leaf wt-g1 / branch fanout-g1]
  RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 22, test_runs: 3}  vs  Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs
  SCOPE: CLEAN                                    # full write-scope block above when VIOLATION
  CHUNK_VERDICT: PASS                             # verifier findings (Check 1 / Check 3 / Gates) listed above when FAIL
  Files changed  : src/recon/engine.py M, tests/test_recon.py M, docs/plan.md M
  Redo           : 0 of 3 (per-chunk redo counter)
  Options: proceed (orchestrator commits the chunk) │ fix (re-dispatch Chunk 2 with a repair packet; counts toward the per-chunk redo cap) │ stop
```

Each template's return step states its row. A pipeline leaf that commits anyway
is not a scope violation (its commit falls inside the observed window and is
matched by path), but the template no longer invites it, and the orchestrator's
own commit then becomes a no-op for those paths.

[Added 2026-09-18, harness-p4 — REQ-HARN-HARNESSP4-001] Whether the
orchestrator's commit (or merge) actually landed every observed path is checked
**after** the `proceed` decision by the `COMMIT: COMPLETE | INCOMPLETE` closing
line — owned by `harness-commit-fidelity.md`, positioned by
`harness-loop-control.md` §Gate Signal Order item 8 (2b at the fan-out per-leaf
gate). Its `expected` operand is the observed-writes set of §Observation, so
this spec's strict-set rule (§Observed Writes Are a Strict Set) governs both
signals; the skill-side defining section is `references/write-scope.md` §7.

### Snapshot Ordering (REQ-HARN-025)

```
sequential : snapshot(before) → dispatch → await return → snapshot(after) → scope check
             → chunk verifier → PER-CHUNK GATE → orchestrator commit (on proceed)
fan-out    : snapshot(before) → dispatch → await return → snapshot(after) → scope check
             → chunk verifier → PER-LEAF GATE → merge (on proceed)   # leaf commits are inside the window by design
```

The "before" snapshot is taken immediately before dispatch and the "after"
snapshot immediately **on return** — before the verifier dispatch, before the
per-chunk gate and therefore before the per-chunk gate's commit (sequential) or
merge (fan-out), and before any §3e bookkeeping writes — so the orchestrator's
commit and bookkeeping are never inside the observed window and cannot be
flagged. The verifier is read-only and its own scope check must observe zero
writes, so running it after the snapshot changes nothing. The ordering is stated
in `references/write-scope.md` next to the three commands.

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
  concern, not this check's. ~~The shared stash stack is out of scope (skills
  never stash).~~ **[Retired 2026-09-20 — REQ-HARN-HARNESSP6-001.** The claim
  was falsified by the harness-p5 incident, in which a read-only verifier leaf
  ran `git stash` with nine files of uncommitted work in the tree. The stash
  stack is now observed: §Git-State Observation reads `git stash list | wc -l`
  inside the existing snapshot window, and a leaf that stashes renders a
  `GIT_STATE` line counting into `SCOPE: VIOLATION (N paths)`. Left visible
  rather than deleted, per the strike convention this cycle ships
  (REQ-PLAN-HARNESSP6-001).**]

### Marker-4 Rooting

Under `docs/.sdd-version` == `4` the default table's execution-artifact paths
resolve to `docs/ws/<id>/…`, the fan-out `<base>` is the workstream branch
point, and every revert/merge target is the workstream branch. Under marker `3`
the flat paths and `main` apply unchanged.

### Content-Hash Observation (REQ-HARN-HARNESSP3-001)

[Changed 2026-09-18: a fourth term is added to `observed writes`. Probe-evidenced
— RS-HARNESSP3-001 Q1 probe 1 reproduced the blindness and the remedy; probe 2
measured 134 files at 0.064 s and an 8-path set at 0.017 s against a 0.008 s
porcelain baseline.]

The observation of REQ-HARN-021 is blind to a path that is **already dirty or
untracked at snapshot time** and is written again during the dispatch: its
porcelain status letter is unchanged, so the delta cancels it, and an
uncommitted write leaves no committed delta. The remedy is a **content-hash
observation** — the name to use in prose; never "the fourth observation", since
§3 already calls the named-base observation a four-part one.

Contract:

```
ambiguous_set := paths listed as dirty or untracked by snapshot(before)
sha.before    := {(path, content_hash) for path in ambiguous_set}          # pre-dispatch
sha.after     := {(path, content_hash) for path in ambiguous_set INTERSECT snapshot(after)}
content_delta := {p | sha.before[p] != sha.after[p]}
                 UNION {p in sha.before and absent from the worktree on return}
observed writes := porcelain_delta UNION committed_delta UNION content_delta
```

- The cancel rule of §3 is amended: paths present in both snapshots cancel
  **only when their content hash is also unchanged**.
- A path deleted during the dispatch is recorded as a sentinel "absent" pair,
  which is itself a content change.
- Porcelain must be parsed with `-z`; **both** paths of a rename or copy
  (`R`, `C`) record enter the ambiguous set.
- The `SCOPE:` token, the `IN` / `ADVISORY` / `OUT` tags, the `N` count, the
  finding block, the operator options and the `HISTORY_REWRITE` rule are
  **unchanged** — this changes *what counts as an observed write*, not how one
  is matched or rendered. `HISTORY_REWRITE` still rests on the untouched
  ancestry check.
- Cost is bounded to O(dirty files), not O(repo), because the set is fixed
  before the dispatch.

**Rejected alternatives** (both measured in RS-HARNESSP3-001 Q1 probe 2):
`git stash create` writes seven loose objects per snapshot, so the orchestrator
would mutate the repository it is observing; a temp-index `read-tree HEAD` plus
`diff --stat` diffs against HEAD and reproduces the identical blindness.

The §5 limitation that a file modified and then reverted to its original content
within one dispatch stays invisible is **unchanged** — a content hash cannot see
a round trip either.

### Specs Row Names the Per-Workstream Traceability Path (REQ-HARN-HARNESSP3-004)

[Changed 2026-09-18: spec-read defect — the marker-4 note resolved the path but
the row did not, and the row is what fills `{write_scope}` at dispatch time.]

The **specs** row of the default scope table must name the per-workstream path
explicitly rather than delegating it to the section's marker-4 note:

| Stage / dispatch | Default write scope |
|------------------|---------------------|
| specs | `docs/spec/**`; marker `3`: `docs/requirements/traceability.md` (Spec column only) — marker `4`: `docs/ws/<id>/traceability.md` (Spec column only), plus the aggregate only for a standalone run (see below) |

Rationale: `docs/spec/ws-traceability.md` Q-IMPL-011 makes `sdd-specs` fill the
**Spec** column of `docs/ws/<id>/traceability.md` under marker `4`. With the row
as it stood, a specs leaf doing exactly what its skill mandates was tagged `OUT`
— the same false-`VIOLATION` class the 2026-09-17 re-walk note was written to
prevent for `sdd-verify`'s Verified-column write.

### Leaf Rows Omit the Shared Aggregate (REQ-WS-HARNESSP3-001)

[Changed 2026-09-18: constructed — ratifies one side of two committed texts that
disagreed; see `docs/spec/ws-traceability.md` for the owning contract.]

For **orchestrated** dispatches, every leaf row of the default scope table omits
`docs/requirements/traceability.md`: regeneration of the shared aggregate is the
orchestrator's post-gate bookkeeping, committed separately (§7 commit
ownership). The omission is not incidental — the dispatched `{write_scope}` slot
**is** the discriminator a writing skill reads: absent path → the orchestrator
regenerates; present path, or no dispatched scope at all → the skill regenerates
itself (standalone runs). No new flag or field is introduced.

### `## Post-cycle Fixes` Is Inside the Implement / `RED_BREAK` Scope (REQ-REDB-HARNESSP3-004)

The implement and `RED_BREAK` rows name the active plan path — marker `3`
`docs/plan.md`, marker `4` `docs/ws/<id>/plan.md` — so an orchestrator-owned
line appended under the plan's `## Post-cycle Fixes` section is tagged `IN`, not
unscoped. The section's format and ownership are defined in
`docs/spec/adversarial-verify.md`.

### Observed Writes Are a Strict Set (REQ-HARN-HARNESSP4-004)

[Added 2026-09-18, harness-p4 — REQ-HARN-HARNESSP4-004; spec-read defect,
`docs/ws/harness-p3/verification.md` §V7]

`observed writes := porcelain_delta UNION committed_delta UNION content_delta`
is a **set**, and the implementation must be one: a path that arrives from more
than one term is counted **once** in the `N` of `SCOPE: VIOLATION (N paths)`,
once in each `COMMIT:` operand (`harness-commit-fidelity.md`), and listed once on
the `Observed writes:` provenance line, which keeps the **richest** label for it:

```
label precedence:  committed  ≻  content  ≻  porcelain
                   # a path dirty at snapshot, committed during the dispatch and dirtied again
                   # is observed by two or three terms and rendered once, labelled "committed <sha>"
```

Why: the operator reads `N` to size a violation, and a rendered token must not
make a false statement about a count; the Approved contract already said
`UNION`, and an append-ordered list (`Observation.paths` in
`tools/sdd-scope-check-selftest.py` today) diverges from it. Nothing else in the
finding format, tags or options changes.

### `R`/`C` Records and `-z` Parsing Are Fixture-Exercised (REQ-HARN-HARNESSP4-005)

[Added 2026-09-18, harness-p4 — REQ-HARN-HARNESSP4-005; recorded in
`docs/ws/harness-p3/verification.md` §V6, fixture not added because `tools/`
was outside that cycle's verify scope]

The criterion "porcelain parsing uses `-z` and enters **both** paths of an
`R`/`C` record into the ambiguous set" (§Content-Hash Observation) is
implemented in `snapshot()` / `ambiguous_set` but no fixture F1–F13 renames,
copies, or uses a path with a space, quote or newline — the conditions under
which `-z` parsing is load-bearing. Two fixtures are added to
`tools/sdd-scope-check-selftest.py --self-test`:

| Fixture | Scenario | Asserts |
|---|---|---|
| rename across the scope boundary | `git mv` a scoped path to an out-of-scope path during the dispatch | **both** the old and the new path enter the ambiguous set and the observed set; the new path tags `OUT`; the rename is observed rather than cancelling |
| path with a space | a written path such as `docs/notes with space.md` | `-z` parsing keeps it **one** record; it is observed and rendered as one path |

Mutation contract: splitting the porcelain output on newline instead of NUL
makes the space-path fixture fail; dropping the rename's origin path from the
ambiguous set makes the `R` fixture fail. Fixture ids continue the F-series
(next free ids).

### Git-State Observation (REQ-HARN-HARNESSP6-001)

[Added 2026-09-20, harness-p6 — REQ-HARN-HARNESSP6-001; the harness-p5 incident
in which a read-only chunk verifier ran `git stash` over nine files of
uncommitted work and the gate still rendered `SCOPE: CLEAN`]

**Why the existing three commands cannot see it.** (a) is a *one-directional*
porcelain delta — lines in `after` not in `before` — so an operation that
**removes** porcelain lines is invisible to it. (b) sees nothing because `git
stash` leaves `HEAD` untouched. (c) passes for the same reason. The write scope
therefore constrained file writes but said nothing about mutation of **git
state**, which a read-only leaf could perform freely.

**Extra reads, same window.** No second observation window is introduced. The
existing `snapshot(before)` / `snapshot(after)` calls each record three extra
values alongside the `git status --porcelain` read they already take:

```bash
stash_count=$(git stash list | wc -l)
branch=$(git rev-parse --abbrev-ref HEAD)
orig_head=$(git rev-parse --verify --quiet ORIG_HEAD || echo "")
```

`ORIG_HEAD` is read with `--verify --quiet`; its **absence** is a legal value
(the empty string) and absent-in-both compares equal. For a fan-out leaf the
three reads run in the leaf's worktree, as the existing commands do.

**The comparand.** A `GIT_STATE` finding is raised when either clause holds:

| Clause | Condition |
|---|---|
| (i) state drift | `stash_count`, `branch` or `orig_head` differs between the two snapshots |
| (ii) reverse porcelain delta | the set of paths dirty in `before` and **not** dirty in `after`, **minus** the paths of the committed delta (b), is non-empty — a path stopped being dirty with no commit explaining it |

Clause (ii) is the general form: it catches `git stash`, `git checkout --
<path>`, `git restore` and `git clean` on a path the leaf did not commit, none
of which clause (i) alone would see (a `stash` followed by `stash pop` restores
the count but not, in general, the same instant; a `stash drop` changes it).
Clause (i) is the cheap form and catches a branch switch and a reset that leaves
the tree clean.

**Why it does not fire on a legitimate dispatch** — the discriminating property,
stated so an implementer can test it:

- A **normal implement leaf** only *adds* porcelain lines; any path it commits
  leaves the dirty set, and clause (ii) subtracts exactly the committed delta,
  so the reverse delta is empty. It does not stash, does not switch branch, and
  does not set `ORIG_HEAD`.
- A **fan-out merge** is an orchestrator step that runs **outside** any leaf's
  observation window, so no snapshot pair spans it; and a merge commit is a
  descendant, so the existing ancestry check (c) still passes.
- The orchestrator's **own bookkeeping commit** also lands after
  `snapshot(after)` (§Snapshot Ordering), outside the window.

**Rendering (Q-REQ-P6-A).** The finding renders as a **line inside the existing
write-scope block**, exactly parallel to the `HISTORY_REWRITE` line, above the
path list, and counts into `SCOPE: VIOLATION (N paths)`. **No new gate token is
introduced** and the REQ-ORCH-034 signal order is unchanged — a new own-line
token would have to be placed in that order and guarded by its own lint rows for
no gain. Shape:

```
  GIT_STATE  stash count 0 -> 1; 9 path(s) dirty before and clean after with no
             commit (docs/plan.md, docs/spec/telemetry.md, …)
```

**Options.** Because a stash is recoverable, the gate offers
`restore │ accept (note) │ stop` for the finding, and `proceed` is unavailable
while it is unresolved — the same withholding rule an unresolved `OUT` path
already carries. `restore` is `git stash pop` for the stash case and
`git checkout -- <path>` for a reverted path; `accept (note)` records the
operator's acceptance in ephemeral gate text only.

**Skill-side text.** `skills/sdd-orchestrate/references/write-scope.md` states
the three extra plumbing reads and the reverse-delta subtraction in §3, the
`GIT_STATE` line in §5, and its option set in §8. The `GIT_STATE` name is
guarded by a lint `REQUIRED` row (`skill-lint-v5.md`
§`REQUIRED` Rows — `PLAN:` and `GIT_STATE`).

**Self-test scenarios.** Four new `tools/sdd-scope-check-selftest.py` fixtures
close the Confidence gap that this design being derived from contract text
rather than from a replayed dispatch leaves open; they are required work, not
optional colour:

| Scenario | Expected |
|---|---|
| read-only leaf runs `git stash` then `git stash pop` | `GIT_STATE` finding, `SCOPE: VIOLATION` |
| read-only leaf runs `git stash` then `git stash drop` | `GIT_STATE` finding, `SCOPE: VIOLATION` |
| implement leaf commits a path that was already dirty at `snapshot(before)` | `SCOPE: CLEAN` — clause (ii) subtracts the committed delta |
| fan-out merge performed by the orchestrator between two dispatches | `SCOPE: CLEAN` — the merge lies outside any leaf's window |

## Verification

### Automated
- Lint `REQUIRED` rows: `Write scope:` in both template files
  (`skill-lint-v5.md`).
- Fixture: before snapshot `?? .claude/worktrees/` + after snapshot `?? .claude/
  worktrees/` and ` M docs/plan.md`, committed delta empty, scope
  `src/**` → one `OUT docs/plan.md uncommitted`, `SCOPE: VIOLATION (1 path)`.
- Fixture: porcelain clean after, committed delta `M docs/plan.md`, scope
  `docs/spec/**` → `OUT docs/plan.md committed`, `VIOLATION (1 path)`.
- Fixture: standalone marker-`3` verify dispatch writes `docs/verification.md` +
  `docs/requirements/traceability.md` → both `IN`, `SCOPE: CLEAN`.
- Fixture: orchestrated marker-`4` verify dispatch writes `docs/verification.md`
  + `docs/ws/<id>/traceability.md` → both `IN`, `SCOPE: CLEAN`.
- Fixture: orchestrated marker-`4` verify dispatch also writes
  `docs/requirements/traceability.md` → `OUT docs/requirements/traceability.md`,
  `SCOPE: VIOLATION (1 path)` (the aggregate is the orchestrator's to regenerate).
- Fixture: implement dispatch writes `docs/spec/recon.md` → `ADVISORY`,
  `SCOPE: CLEAN`.
- Fixture: `blocked_writes: [{path: docs/plan.md, …}]` from a fan-out leaf →
  not persisted, listed as `OUT … refused`.
- Fixtures: the four §Git-State Observation scenarios, each asserting the
  `GIT_STATE` finding's presence or absence and the resulting `SCOPE:` token
  (REQ-HARN-HARNESSP6-001).
- Fixture: `ORIG_HEAD` absent in both snapshots compares equal and raises
  nothing; present in `after` only raises `GIT_STATE` (REQ-HARN-HARNESSP6-001).
- Fixture: `HEAD_after` not descending from `HEAD_before` → `HISTORY_REWRITE`,
  `VIOLATION`.

### Manual
- Run one sequential implement chunk followed by `proceed` at the per-chunk
  gate: the gate showed `SCOPE: CLEAN` before `CHUNK_VERDICT:`, and the
  orchestrator's commit was not in the observed window.
- Fan-out with a leaf that edits `docs/plan.md`: `VIOLATION` shown before
  merge; `git log` on the integration branch shows no merge of that branch
  until the path is reverted.

### Acceptance Criteria
- [ ] Pipeline and fan-out templates carry `Write scope:`; the default table lives in `references/write-scope.md` with a `SKILL.md` stub; a verify dispatch filling the Verified column is `SCOPE: CLEAN` (REQ-HARN-020)
- [ ] Observation = porcelain delta ∪ committed delta, plus ancestry check; D/R count; noise cancels; committed out-of-scope writes are flagged with clean porcelain (REQ-HARN-021)
- [ ] The finding format and own-line `SCOPE:` token are in `references/write-scope.md`, referenced from `SKILL.md` §The gate; branching on the token; scope options resolved inside the per-chunk gate before its commit / merge; fan-out revert is on the leaf branch; nothing persisted (REQ-HARN-022)
- [ ] `blocked_writes` paths are scope-matched before persistence; out-of-scope entries are refused and listed (REQ-HARN-023)
- [ ] Commit ownership per dispatch type is stated in each template's return step and tabulated in `references/write-scope.md`; the orchestrator commits a chunk only on `proceed` at the per-chunk gate; fan-out leaves commit, the orchestrator merges on `proceed` at the per-leaf gate (REQ-HARN-024)
- [ ] Snapshot ordering excludes the orchestrator's commit: snapshot(after) on return, before verifier, per-chunk gate and commit / merge; stated beside the three commands (REQ-HARN-025)
- [ ] Both v1 limitations are recorded beside the finding format; spec-file writes under implement/replan show `ADVISORY` (REQ-HARN-026)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed
- [ ] `references/write-scope.md` §3 carries the content-hash observation block and the amended cancel bullet; §5's limitation wording matches (REQ-HARN-HARNESSP3-001)
- [ ] `tools/sdd-scope-check-selftest.py` fixture **F10** (next free id — F8 and F9 are taken): a path already dirty at snapshot time and re-touched by the leaf yields a non-empty observed-write set naming that path; the same fixture with the leaf leaving it untouched yields `SCOPE: CLEAN` (REQ-HARN-HARNESSP3-001)
- [ ] Porcelain parsing uses `-z` and enters both paths of an `R`/`C` record into the ambiguous set (REQ-HARN-HARNESSP3-001)
- [ ] The specs row of §2 names `docs/ws/<id>/traceability.md` under marker `4`; a marker-4 specs dispatch writing only `docs/spec/**` plus its per-ws row yields `SCOPE: CLEAN` (REQ-HARN-HARNESSP3-004)
- [ ] §2 leaf rows omit `docs/requirements/traceability.md` and §7 assigns the regeneration to the orchestrator (REQ-WS-HARNESSP3-001)
- [ ] The implement / `RED_BREAK` row names the active plan path so a `## Post-cycle Fixes` line is `IN` (REQ-REDB-HARNESSP3-004)
- [ ] `tools/sdd-scope-check-selftest.py --self-test` gains a fixture in which one path is observed by both the committed and the content delta and asserts the rendered `N` is `1` with provenance label `committed`; the shipped self-test exits 0; `references/write-scope.md` §3 states the de-duplication and label-precedence rule in one sentence (REQ-HARN-HARNESSP4-004)
- [ ] The `R` (scoped → out-of-scope `git mv`, both paths in the ambiguous set) and space-path (`-z` keeps one record) fixtures exist and pass under `--self-test`; the newline-split mutation fails the space-path fixture and dropping the origin path fails the `R` fixture; the shipped self-test exits 0 (REQ-HARN-HARNESSP4-005)
- [ ] §Commit Ownership carries the one-sentence pointer to `harness-commit-fidelity.md` for the `COMMIT:` closing line (REQ-HARN-HARNESSP4-001, owned there)
- [ ] `snapshot(before)` and `snapshot(after)` each record stash count, current branch and `ORIG_HEAD` alongside the existing porcelain read, within the **existing** window — no second window is introduced (REQ-HARN-HARNESSP6-001)
- [ ] A `GIT_STATE` finding is raised on clause (i) state drift or clause (ii) a non-empty reverse porcelain delta after subtracting the committed delta; it renders as a line inside the write-scope block parallel to `HISTORY_REWRITE`, counts into `SCOPE: VIOLATION (N paths)`, and introduces no new gate token (REQ-HARN-HARNESSP6-001)
- [ ] The finding's options are `restore │ accept (note) │ stop` with `proceed` withheld while unresolved (REQ-HARN-HARNESSP6-001)
- [ ] `python3 tools/sdd-scope-check-selftest.py` exits 0 with the four new scenarios: stash-with-pop and stash-and-drop each violate; an implement leaf committing an already-dirty path and an orchestrator fan-out merge are each `SCOPE: CLEAN` (REQ-HARN-HARNESSP6-001)
- [ ] `skills/sdd-orchestrate/references/write-scope.md` §3 states the three extra plumbing reads and the reverse-delta subtraction, §5 the `GIT_STATE` line, §8 its options; `python3 tools/sdd-skill-lint.py` exits 0 (REQ-HARN-HARNESSP6-001)
- [ ] §Commit Ownership names the **second** orchestrator bookkeeping commit with its three writes (aggregate regeneration, a cross-workstream `descoped` cell, the plan `status: complete` flip), states that it lands **after** `HEAD_landed` is captured, and states that a leaf writing any of them is a `SCOPE: VIOLATION`; `grep -cE '^actually runs — .git diff --name-only --no-renames -z' docs/spec/harness-write-scope.md` prints 1 — the `^` anchor matches only the §Comparand quotation, which begins its own line, and never this criterion, which begins `- [ ]`, so the check is not self-matching (the earlier corpus-wide `grep -n 'no-renames…'` form counted itself and could never print 1) — pointing at `harness-commit-fidelity.md` §Comparand Table and `references/write-scope.md` §7a rather than restating the table (REQ-HARN-HARNESSP5-001, REQ-WS-HARNESSP5-001, REQ-HARN-HARNESSP5-002, all owned elsewhere)

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
  Questions` in spec files — the `ADVISORY` hint quotes that heading verbatim;
  a fan-out leaf never writes them (routes via `RETURN.open_questions`, the
  orchestrator files the entry at merge) — additive to `fan-out.md` §2.
- The per-chunk gate block and `proceed │ fix │ stop` vocabulary are those of
  `harness-chunk-verifier.md` §Sequencing — Sequential Mode — consistent.
- `orchestration.md` §Gate Protocol vocabulary is extended only by
  `revert path | accept & widen scope`, as REQ-ORCH-034 states.
- `ws-integration.md` merge/revert target under marker `4` = workstream
  branch — restated identically.
- `RETURN.files_written`, `commits`, `blocked_writes` names match
  `harness-return-contract.md`.
- **No unresolved contradictions.**

**harness-p3 pass (2026-09-18).** No type definitions are introduced by this
amendment — the specs in this corpus are prose/table contracts, so the
type-extraction step reports "no extractable type definitions in
harness-write-scope.md" as an explicit result rather than a silent pass. Shared
tokens were checked instead:

- `SCOPE:`, `IN` / `ADVISORY` / `OUT`, `HISTORY_REWRITE`, `CATCH-UP` — unchanged
  here and consistent with `docs/spec/harness-return-contract.md`.

**harness-p6 pass (2026-09-20).** `GIT_STATE` is defined once, here, as a
**member of the `SCOPE:` finding family** — not an own-line token — and is
referenced by `docs/spec/skill-lint-v5.md` (the `REQUIRED` row that guards its
name) and by `skills/sdd-orchestrate/references/write-scope.md`. It appears in
no gate-signal-order table, which is the property that keeps
`docs/spec/harness-loop-control.md` §Gate Signal Order unchanged by this cycle's
write-scope work. No type definitions are introduced; the extraction step again
reports "no extractable type definitions in harness-write-scope.md".
- The specs write-scope row is repeated in `docs/spec/ws-traceability.md`
  (Q-IMPL-011) and both now read `docs/ws/<id>/traceability.md` for marker `4`.
- `## Post-cycle Fixes` is defined once, in `docs/spec/adversarial-verify.md`,
  and referenced (not redefined) here.

## Open Questions

1. **Scope for a research-stage spike inside implement** that needs a new
   `RS-NNN` directory: the default table already includes
   `docs/research/RS-NNN-*/**` for spike tasks; the orchestrator substitutes
   the assigned ID. Default: exact assigned-ID directory, not the wildcard.
2. **False-positive rate of the default table** is a dogfooding question
   (RS-008). Default: keep the table as written; widen at the gate and fold
   recurring widenings back into the table in the next cycle.
### Q-IMPL-062: "Recorded v1 Limitations" heading collides with a lint drift rule
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Recorded v1 Limitations
**Decision**: `tools/sdd-skill-lint.py` forbids the literal phrase "v1 limitations" in skill text (drift rule); `references/write-scope.md` uses the heading "Recorded limitations, accepted for v1 (REQ-HARN-026)". The spec heading is unchanged.
**Rationale**: the drift rule predates this cycle and protects skill prose from stale version-qualified wording; the reference must pass lint.
**Date**: 2026-09-17 (Chunk 4)


### Q-IMPL-HARNESSP2-002: observation, limitations and blocked-write fallback extended by three harness-p2 specs
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Observation: Three Commands, §Snapshot Ordering, §Recorded v1 Limitations, §Blocked-Write Fallback
**Decision**: Superseded/extended as follows (REQ-HARN-026 and REQ-HARN-HARNESSP2-001/-002 amendments 2026-09-17): (1) `dispatch-snapshot-base.md` §Snapshot Base Rule — `snapshot(before)` is taken at the branch tip the leaf is instructed to reach, the committed delta is based on the named base, and a `CATCH-UP <from>..<base> (N commits, excluded — base <sha>)` line names excluded catch-up commits; limitation (c) is recorded with both remedies; (2) `dispatch-snapshot-base.md` §Blocked-Write Staging Path — the scratchpad-staged-then-copied path is the expected fallback, points (i)–(iv); (3) `telemetry.md` §Third Observation — limitation (b) gains the `.sdd/` exception and a third, telemetry-specific observation whose finding string is defined there once; (4) `arbitrated-handoff.md` §Section Resolution — limitation (a) is partially closed for Markdown paths by hunk-to-heading resolution. The three commands, tags and `SCOPE:` token are unchanged.
**Rationale**: New behaviour lands in new spec files under marker 4; this entry is the pointer readers of this spec need.
**Date**: 2026-09-17 (harness-p2 specs stage)

### Q-IMPL-HARNESSP3-001: The contract is the `(path, sha)` pair set; `git hash-object` is the recommended hash
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Content-Hash Observation
**Decision**:

`REQ-HARN-HARNESSP3-001` specifies `(path, sha)` pairs without naming the hash.
Decision (the normative half): the contract is the **`(path, sha)` pair set
taken over working-tree content** — any hash function is conforming so long as
the same function is used for the before and after snapshot of a dispatch.
Working tree, not index, because the blindness being closed is an uncommitted
working-tree rewrite.

Recommendation (non-normative): `git hash-object --stdin-paths` over the
ambiguous set, so the value matches git's own blob identity and needs no second
hashing dependency. A plain `sha256` is an equally conforming substitute if a
probe shows the plumbing call is the slower path.
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP3-002: Deleted-path sentinel is a reserved non-hash token
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Content-Hash Observation
**Decision**:

The "absent" pair of REQ-HARN-HARNESSP3-001 is recorded as the literal string
`ABSENT` in the sha slot, which cannot collide with a hex digest, so the
comparison stays a plain inequality and needs no separate presence set.
**Date**: 2026-09-18 (specs stage)
