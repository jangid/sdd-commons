# Implement-Stage Fan-out Procedure (Design B)

The full, bulky procedure for **orchestrator-owned, one-level-deep** implement-stage
fan-out. `../SKILL.md` (§Execution Model) describes this behavior in concise prose
and points here for the dispatch template and the exact command sequence. The
contract is defined by `docs/spec/orchestration.md` §"Sequential Execution and
Implement-Stage Fan-out" (REQ-ORCH-015/016, REQ-ORCH-022..028).

Fan-out is the orchestrator's job, never a subagent's: a dispatched subagent has
**no subagent-dispatch tool** in its toolset (RS-006 Q1), so each fan-out implement
subagent is a **leaf** that runs `sdd-implement` on its chunk-group and cannot fan
out further (REQ-ORCH-022). Design A (a pipeline subagent owning nested fan-out) is
ruled out infeasible; Design B (this procedure) is the spec.

---

## 0. Integration anchor: the version gate (marker-3 `main` vs marker-4 workstream branch)

`docs/.sdd-version` is the **sole** gate for the fan-out integration anchor
(`docs/spec/ws-integration.md`, REQ-WS-016/017):

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Read every `main`
  reference in §§1–4 below literally: the fan-out base is `main`, worktrees merge
  back into `main`, redo worktrees re-branch from the updated `main`, and the §3c
  step 3 `main`-ownership "conflict-after-re-derivation = boundary error" inference
  applies exactly as written. The v3 path is untouched.
- **Marker is `4` (workstream-aware layout).** Fan-out runs **inside the workstream's
  branch isolation** (branch-per-workstream → PR to `main`, REQ-WS-016 — the
  **workstream branch**, not `main`, is the integration unit for the whole cycle;
  `main` is a shared trunk, not a working surface; concurrent workstreams may hold
  open PRs at once). Everywhere §§1–4 name `main` as the fan-out integration anchor,
  substitute the **workstream branch `<ws>` (HEAD)** (REQ-WS-017):
  - the fan-out **base** is the workstream branch HEAD, not `main` (§3a);
  - worktrees **merge back into the workstream branch**, not `main` (§3b);
  - a redo worktree **re-branches from the updated workstream branch**, not `main` (§3c);
  - **`main` is untouched** until the workstream PR (REQ-WS-016) — fan-out no longer
    takes exclusive ownership of `main`;
  - the §3c step 3 **`main`-ownership "conflict = boundary error" inference is
    REMOVED** (see §3c): with per-workstream branches `main` is not the fan-out
    integration point, so a conflict no longer implies a chunk-boundary error. The
    guaranteed-termination **sequential fallback** in §3c step 3 is retained — only
    the boundary-error *labeling* is dropped.

  All other fan-out mechanics — worktree provisioning ownership, sequential
  merge-back, inline git identity, conflict abort-and-redo-by-re-derivation — are
  **unchanged**; only the base branch and the merge-back target move from `main` to
  the workstream branch.

**Do NOT touch (RS-007 Q4):** this gate re-anchors the branch/merge **lifecycle**
only. It does **not** alter the `**Depends on**: Chunk N` boundary-derivation parser
in §1 (which parses chunk ordinals, a separate namespace from ws-prefixed ids and
already guarded below).

---

## 1. Boundary derivation (which chunks run in parallel)

Fan-out occurs along the **independent branches of the plan's chunk dependency
graph** — not per-milestone (too coarse; milestones are sequential) and not
per-task (too fine) (REQ-ORCH-016).

Derive the parallel groups by **reading `docs/plan.md`** (marker `4`: `docs/ws/<ws>/plan.md`), never by modifying
`sdd-implement` (REQ-ORCH-001, REQ-ORCH-016):

- The canonical signal is each chunk's `**Depends on**: Chunk N` field (defined in
  `docs/spec/plan-management.md`). The live plan may instead express the same
  relation as chunk-level prose — `Entry criteria: Chunk N complete` — which you
  treat as the equivalent of that field.
- These are **chunk-level** declarations. Do **not** use the coarser
  milestone-level Entry/Exit criteria from milestone-plans to derive chunk fan-out.
- **Do NOT touch (RS-007 Q4 — provably unaffected):** this `**Depends on**: Chunk N`
  derivation parses chunk **ordinals** (`### Chunk N:` headers), a separate namespace
  from RS / REQ / Q-IMPL artifact ids. The v4 workstream `<WS>` segment is inserted
  only into artifact ids, which appear here (if at all) as inert prose — it never
  enters a chunk ordinal. This parser is unaffected by the ws-prefixed ID format and
  must stay exactly as written; do not add ws-awareness to it (`docs/spec/ws-ids.md`,
  REQ-WS-012).
- Two chunks are **independent** (concurrently runnable) when neither (transitively)
  depends on the other. A maximal set of mutually-independent chunks is a
  **chunk-group** that can run in its own worktree.

**Degrade-to-sequential conditions** (never guess a boundary):

- The plan does **not** express parseable chunk-level dependencies in either form, OR
- The dependency graph is a **single chain** (every chunk depends on the previous —
  no ≥2 independent branches exist).

In either case, run the implement stage sequentially in the main workspace even if
the operator opted into fan-out, and tell the operator at the gate (see SKILL.md
§Execution Model).

---

## 2. Per-group implement dispatch template

One dispatch per chunk-group, pinned to that group's orchestrator-provisioned
worktree/branch. The non-interactivity contract (REQ-ORCH-007) and central ID
assignment (REQ-ORCH-008) apply exactly as for any pipeline dispatch (see
`dispatch-templates.md` §PIPELINE). The fan-out-specific additions are the
**worktree pin**, the **leaf clause**, and the **inline git identity**.

```
You are a non-interactive pipeline subagent executing ONE stage of an SDD
pipeline. Do NOT ask questions — you have no user to answer them.

Working directory (absolute): {worktree_path}
Stage skill to invoke: sdd-implement
Assigned IDs (use these verbatim, do not scan/guess): {ids_if_any}
Q-IMPL number block (allocate sequentially from the start of this block; do
  NOT scan for the next number): {qimpl_block}
Success criterion: the chunk-group's tasks are implemented and committed on
  branch {branch} within this worktree.
Budget: {budget}
Deliverable contract: implement these chunks only — {chunk_group_tasks}.

Worktree pin (HARD boundary):
  - Operate ONLY within this worktree ({worktree_path}) and ONLY on its branch
    ({branch}). Do not touch the main workspace, other worktrees, or other
    branches.
  - Do NOT edit the shared plan or traceability files (docs/plan.md /
    docs/ws/<ws>/plan.md; docs/requirements/traceability.md /
    docs/ws/<ws>/traceability.md): every fan-out leaf writes them, so any two
    groups would conflict on merge regardless of code independence. Where
    sdd-implement says to mark tasks [x] or fill traceability columns
    (including chunk-close Check 2), instead RECORD the completed task list
    and the column fills in your return; the orchestrator applies them once
    after all merges (§3e).

Leaf clause:
  - You are a LEAF subagent. Do NOT dispatch any sub-subagent and do NOT fan out
    further — run sdd-implement directly on your chunk-group. (You have no
    subagent-dispatch tool; this is enforced by the harness as well.)

Commit identity (sandbox-safe):
  - Commit with inline identity flags, NEVER by writing .git/config:
      git -c user.email={git_email} -c user.name={git_name} commit ...
    Writing the main repo's .git/config is blocked by the sandbox
    ("Operation not permitted"); the inline -c flags let commits, merges, and
    branch ops succeed.

Precedence: where sdd-implement tells you to scan for the next ID or choose an
output path, THESE dispatch instructions override it.

Task:
  1. Invoke sdd-implement via the Skill tool and follow it on your chunk-group.
  2. Where the skill instructs "ask the user", use the inputs above; record any
     genuinely missing decision under Open Questions/Assumptions with a stated
     default and proceed — NEVER fabricate operator consent.
  3. Commit your work on {branch} using the inline git identity above.
  4. Return: end your return text with the RETURN: block below — every key
     present, status: first on its own line, values are path references and
     one-line strings only, no tracebacks. Populate commits with the shas you
     made on {branch}. Put the plan [x] marks you were barred from writing in
     tasks_completed and the Test/Implementation column fills in
     traceability_fills (the orchestrator applies them after all merges, §3e).
     If any other write is blocked, put the file's full content under
     blocked_writes with the target path labeled so the orchestrator can
     persist it.

RETURN:
  status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED   # own line, first key
  budget_consumed: {tool_calls: N, test_runs: N}            # same units as the dispatched Budget:
  files_written: []                                          # paths
  commits: []                                                # shas on {branch}
  tasks_completed: []                                        # task labels, e.g. "Chunk 2 task 1"
  traceability_fills: []                                     # [{req, test, impl}]
  chunk_close: {}                                            # {chunk, check1..check4, overrides}; check2: deferred
  failures: []                                               # [{test, kind, message, location}] one-line each; empty when COMPLETE
  ledger: []                                                 # [{attempt, hypothesis, change, result}]
  verified_do_not_touch: []                                  # paths
  open_questions: []                                         # one-line each, citing Q-IMPL ids
  blocked_writes: []                                         # [{path, content}] labeled fallback

Do not perform any stage other than sdd-implement.
```

### Slot contract (fan-out dispatch)
- `{worktree_path}` — absolute path of this group's worktree (orchestrator pins cwd).
- `{branch}` — this group's branch, created by the orchestrator in step 1 below.
- `{chunk_group_tasks}` — the chunk(s)/tasks this leaf owns; nothing outside them.
- `{ids_if_any}` — IDs the orchestrator assigned centrally (REQ-ORCH-008).
- `{qimpl_block}` — a **disjoint** Q-IMPL number range per leaf (e.g. group 1:
  `011–030`, group 2: `031–050`), allocated by the orchestrator above the current
  scanned max. Q-IMPL entries arise dynamically mid-implementation, so they cannot
  be pre-assigned individually — but two parallel leaves scanning globally would
  mint the same next number. Unused block numbers stay unused forever (IDs are
  append-only and never reused; gaps are fine).
- `{git_email}` / `{git_name}` — identity for the inline `-c` flags (REQ-ORCH-027).
- `{budget}` — explicit bound (REQ-ORCH-007).
- **Return contract** — step 4 is the leaf half of `return-contract.md` §1: the
  orchestrator parses the `RETURN:` block (never prose); `commits` is populated
  (unlike a pipeline dispatch, where it is `[]`); `tasks_completed` and
  `traceability_fills` carry the plan/traceability writes the worktree pin bars
  (consumed in §3e); `chunk_close.check2` is `deferred`; `blocked_writes` is the
  labeled fallback for any other barred write. A redo dispatch (§3c) adds the
  pipeline template's `{on_fix_only}` / `{repair_packet}` block with
  `reason: MERGE_CONFLICT`, `conflict_paths` and `base`
  (`return-contract.md` §10).

**Concurrency note (RS-006 spike, 2026-06-05):** issuing all per-group dispatches
**in a single batch** was **observed to run them concurrently** on this harness —
medium confidence, since the spike's ~4s probe workload inside a ~426s agent lifetime
is latency-dominated (`docs/spikes/dispatch-concurrency.md`, REQ-ORCH-028). Where it
holds, that is a wall-clock speedup, not merely worktree isolation. **Correctness does
not depend on it** — the design is correct whether dispatches run concurrently or
serialized; only the speedup depends on concurrency.

---

## 3. Orchestrator command sequence (provision → await → merge → teardown)

The orchestrator (not any subagent) owns worktree provisioning, merging, and
teardown — a single owner keeps lifecycle symmetric and avoids orphaned worktrees
(Q-REQ-G).

### 3a. Provision one worktree/branch per group (REQ-ORCH-023)

```bash
# base = main (or the current tip the implement stage builds on)
git worktree add -b <branch> <worktree_path> <base>
```

**Marker-4 anchor (§0):** under `docs/.sdd-version` == `4`, `<base>` is the
**workstream branch `<ws>` HEAD**, not `main` — worktrees branch from the workstream
branch so parallel implement work stays inside the workstream's isolation and other
workstreams' `main` merges proceed independently (REQ-WS-017). Under marker `3` the
base is `main` as above, unchanged.

Then dispatch one leaf implement subagent per group (§2), **all in one batch** so
they run concurrently. Await **all** returns before merging (REQ-ORCH-022/023).

### 3b. Sequential merge to main (REQ-ORCH-025)

Merge the branches **one at a time** into `main`; complete **all** merges **before**
the implement-stage review runs (the review sees the merged state, never an unmerged
branch). For each branch in turn:

**Marker-4 anchor (§0):** under `docs/.sdd-version` == `4`, merge each group's branch
back into the **workstream branch `<ws>`**, not `main`; `main` stays untouched until
the workstream PR (REQ-WS-016/017). The one-at-a-time merge mechanics are otherwise
identical. Under marker `3` merge into `main` as below, unchanged.

```bash
git merge --no-edit <branch>
#   exit 0  -> merged cleanly (fast-forward or auto-merge); go to teardown (3d)
#   exit !=0 -> conflict; go to conflict handling (3c)
```

Because merges are one-at-a-time, each branch's merge is either fully applied or
fully unwound — partial-merge corruption across branches cannot occur.

### 3c. Merge-conflict handling (REQ-ORCH-026, Q-IMPL-1)

On a non-zero `git merge` exit:

1. **(Optional) best-effort auto-resolve.** You MAY first attempt automatic
   resolution. This is best-effort and never the only path. A conflict that
   auto-resolves cleanly (no abort) is a normal success — the merge completes,
   continue to teardown (3d) as for a clean `exit 0`.
2. **Guaranteed fallback — abort and redo by re-derivation.** If auto-resolve is not
   attempted or does not cleanly succeed:

   ```bash
   git merge --abort                                   # restores the last good state
   git worktree add -b <branch>-redo <redo_path> main  # re-branch from UPDATED main
   ```

   **Marker-4 anchor (§0):** under `docs/.sdd-version` == `4`, re-branch the redo
   worktree from the **updated workstream branch `<ws>`**, not `main` (the workstream
   branch already contains the groups merged back so far); `main` stays untouched
   (REQ-WS-017). Under marker `3` re-branch from `main` as shown, unchanged.

   Re-dispatch a **leaf** implement subagent (§2 template, pinned to `<redo_path>` /
   `<branch>-redo`) to **re-run `sdd-implement`** for that chunk-group in the fresh
   worktree. Because the work is re-derived against the updated `main` (which already
   contains the branches merged so far), the already-merged changes are integrated by
   re-derivation — **never replay the stale returned patch**, which would reproduce
   the identical conflict. Then re-attempt:

   ```bash
   git merge --no-edit <branch>-redo
   ```

3. **Convergence / guaranteed termination.** If the chunk-group **still** conflicts
   after re-derivation against the updated `main`, that proves the groups were **not
   truly independent** — a fan-out boundary-selection error (genuinely independent
   branches cannot conflict after re-derivation against a `main` already containing
   the other branch — and with the shared
   plan/traceability writes excluded from leaves per §2, a conflict genuinely
   indicates overlapping *code* changes, not bookkeeping collisions).
   **Fall back to running the affected chunk-groups sequentially**
   (one implement run re-branched from `main`, merged, then the next), which cannot
   conflict by construction. This guarantees termination: each round either merges
   cleanly or proves non-independence and collapses to the always-terminating
   sequential path.

   **Marker-4 anchor (§0) — boundary-error inference REMOVED (REQ-WS-017).** Under
   `docs/.sdd-version` == `4`, the fan-out integration point is the **workstream
   branch**, not `main`, so a repeat conflict after re-derivation **no longer implies
   a chunk-boundary error** — the `main`-ownership inference above does not apply. The
   **guaranteed-termination sequential fallback is retained unchanged** (re-run the
   affected groups one at a time, each re-branched from the updated **workstream
   branch** and merged back into it, which cannot conflict by construction), but it is
   reached **without** labeling the conflict a boundary error: `main` may have moved
   under this workstream meanwhile, so a conflict is no longer diagnostic of
   non-independence. Under marker `3` the `main`-ownership boundary-error inference
   applies exactly as written above, unchanged.
4. **No-corruption invariant.** The abort-and-redo path must **never** corrupt or
   unwind already-merged work. A `git merge --abort` unwinds only the single failing
   merge (RS-006 Q3 proved clean restoration with no loss of prior merges); the redo
   worktree re-branches from that intact `main`, inheriting — never undoing — the
   already-merged branches.

Conflict detection relies on the `git merge` exit code as the contract signal
(`git status --porcelain` `AA` markers and `<<<<<<<` file markers corroborate it,
RS-006 Q3).

### 3d. Teardown after each successful merge

Once a branch is merged into `main`, remove its worktree and delete its branch so
the review sees a clean repo with only `main` (REQ-ORCH-023, Q-REQ-G):

```bash
git worktree remove <worktree_path>
git branch -d <branch>
```

Redo worktrees (`<branch>-redo`) are torn down the same way after their merge. All
teardown happens **before** the implement-stage review.

### 3e. Post-merge bookkeeping (orchestrator-owned)

After all merges and teardowns, before the implement-stage review, the
orchestrator applies the shared-doc updates the leaves were barred from making
(§2 worktree pin):

1. Mark each task listed in the leaf's `RETURN.tasks_completed` `[x]` in the
   plan (`docs/plan.md`, or `docs/ws/<ws>/plan.md` under marker `4`) and bump
   its `last_updated`. Read the labels from the block (`return-contract.md`
   §1), never from the leaf's prose.
2. Apply each `{req, test, impl}` entry of the leaf's
   `RETURN.traceability_fills` to the Test/Implementation columns per the
   active marker's contract (marker `3`: the single shared
   `docs/requirements/traceability.md`; marker `4`: the workstream's own
   `docs/ws/<ws>/traceability.md`, then regenerate the shared aggregate).
3. Re-run any chunk-close Check 2 that a leaf deferred, now that the columns
   are filled.
4. **Checkpoint application** for every leaf whose `RETURN.status` is
   `BLOCKED` or `BUDGET_EXHAUSTED` (`harness-loop-control.md` §Circuit-Break
   Checkpoint): compose the checkpoint from the block's `failures`, `ledger`
   and `open_questions` per the mapping table in `sdd-implement/SKILL.md`
   §Step 3 — trigger label `oscillation` (or the leaf's stuck reason) for
   `BLOCKED`, `budget` for `BUDGET_EXHAUSTED`, with `budget_consumed` shown
   against the dispatched `Budget:` — and apply it as the blocked-task note
   under the named task in the plan (≤ ~15 lines, no traceback frames; one
   checkpoint per task). Leaves are barred from the plan, so the orchestrator is
   the writer here. If the named task is not in the plan (the leaf drifted),
   apply the note under the **nearest chunk header** (the chunk the leaf was
   dispatched for) with a `task not found in plan` prefix and raise it at the
   gate — never invent a task. `sdd-replan` Step 1 reads this note as the
   stuck state.

Only then dispatch the implement-stage review, which sees the fully merged,
fully book-kept state.

---

## 4. Invariants checklist

- [ ] Boundary derived from `**Depends on**`/`Entry criteria: Chunk N` prose, not
      milestone Entry/Exit; degrade to sequential if unparseable or single-chain.
- [ ] One orchestrator-provisioned worktree/branch per concurrently-runnable group.
- [ ] Each fan-out subagent is a leaf (no sub-dispatch), pinned to its worktree.
- [ ] Subagents commit with inline `git -c user.email=… -c user.name=…` (no
      `.git/config` write).
- [ ] All subagents return before any merge; merges are sequential into `main`
      (marker `4`: the workstream branch — §0), completed before the
      implement-stage review.
- [ ] Conflicts: optional auto-resolve → else `git merge --abort` → redo by
      re-derivation in a worktree re-branched from updated `main` (marker `4`:
      the workstream branch — §0) → sequential fallback on repeat conflict
      (guaranteed termination); never corrupt merged work.
- [ ] Leaves never edit the shared plan/traceability files; the orchestrator
      applies returned completions and fills after all merges (§3e), before the
      review.
- [ ] Each merged worktree/branch is torn down before review.
