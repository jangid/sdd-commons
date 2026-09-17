---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-HARN-HARNESSP2-001
  - REQ-HARN-HARNESSP2-002
  - REQ-SKILL-HARNESSP2-004
  - REQ-SKILL-HARNESSP2-007
---

# Dispatch Snapshot Base and Blocked-Write Staging

## Context

The write-scope check (`harness-write-scope.md`) takes its "before" snapshot at
the worktree's HEAD immediately before dispatch. RS-HARNESSP2-001 Q6 measured
what happens when that HEAD is stale: the first dispatch of this cycle was
provisioned at `087cb4b`, instructed to fast-forward to the branch tip
`ca17ce7`, and the committed delta `087cb4b..ca17ce7` contained **20 paths** —
all outside the leaf's declared scope, all false positives. This is recorded
as write-scope limitation **(c)**, the catch-up fast-forward false positive,
beside (a) hunk-level intent and (b) ignored paths.

The same research recorded, twice, that the blocked-write fallback of
REQ-HARN-023 is the **expected** path for leaves writing prose about the
harness: the harness's `Write` tool refused the research artifact and the
worktree guard refused a shell heredoc whose prose merely mentioned
version-control commands; staging under a neutral scratchpad name and copying
in worked both times.

This spec defines the snapshot-base rule and the `CATCH-UP` gate line,
documents the scratchpad-staging path as expected, and carries the
`sdd-implement` references split (Q-IMPL-083) as its skill changes. It fulfils
REQ-HARN-HARNESSP2-001 / -002 and the snapshot half of REQ-SKILL-HARNESSP2-004
plus REQ-SKILL-HARNESSP2-007. It **extends** `harness-write-scope.md`
§Observation, §Snapshot Ordering, §Recorded v1 Limitations and §Blocked-Write
Fallback (recorded there as Q-IMPL-HARNESSP2-002). `CATCH-UP` is defined here
and nowhere else.

## Design

### Snapshot Base Rule (REQ-HARN-HARNESSP2-001)

**Rule**: `snapshot(before)` is taken at the commit the leaf is **instructed to
reach** — never at a stale worktree HEAD.

Two remedies, (i) the default and (ii) the safety net:

| Remedy | What | When |
|---|---|---|
| **(i) provision at the intended base** (default) | every sequential-pipeline, fix, verifier, review and red worktree is provisioned at the intended base — the **workstream branch tip** under marker `4`, `main`/HEAD under marker `3` — exactly as fan-out §3 already does for leaves; the dispatch prompt then names no catch-up | always; the leaf never needs to catch up |
| **(ii) named-base exclusion** | when a dispatch prompt nevertheless names a base commit for the leaf to fast-forward or merge to, `HEAD_before` for the committed-delta and ancestry checks is that **named base**; commits reachable from the named base but not from the provisioned HEAD are excluded from the observed window and reported on the gate block | whenever a prompt carries "reach commit `<sha>`" |

Provisioning step (sequential and fix dispatches), inserted before
`snapshot(before)` in `references/write-scope.md` §3:

```
base      := git rev-parse <workstream-branch>          # marker 4; `main` or HEAD under marker 3
worktree  := provision at base  (git worktree add <path> base, or `git merge --ff-only base` in an existing worktree)
HEAD_prov := git -C <worktree> rev-parse HEAD           # == base under remedy (i)
HEAD_before := base                                     # the instructed tip, not HEAD_prov
snapshot(before) at HEAD_before
```

Observation on return, with the named base `base` and provisioned `HEAD_prov`:

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
  (remedy (i) in effect).
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

**Why (i) is the default**: it is cheaper (one `rev-parse` before provisioning)
and removes the class rather than reporting it; (ii) exists because prompts
written by hand, entry kickoffs and resumed sessions will still sometimes name
a base. Both are stated in `references/write-scope.md` §5 as limitation (c)'s
remedies.

Scenario **F9** in `tools/sdd-scope-check-selftest.py`: the worktree is
provisioned one commit behind the named base and the leaf fast-forwards →
`SCOPE: CLEAN` with a `CATCH-UP <from>..<base> (1 commits, excluded — base
<sha>)` line; the same scenario with one additional out-of-scope leaf write →
`SCOPE: VIOLATION (1 paths)` listing only that path.

### Blocked-Write Staging Path (REQ-HARN-HARNESSP2-002)

`references/write-scope.md` §6 (blocked-write fallback) documents the
following as the **expected** write path for research leaves and fix leaves
that write prose about the harness — not as an anomaly:

| # | Statement |
|---|---|
| (i) trigger | the harness's `Write` tool may refuse an artifact whose prose is about the harness or about version control, and the worktree guard may refuse a shell heredoc whose **prose** mentions version-control commands — including inside heredocs and even when no such command is executed |
| (ii) path | stage the content in the scratchpad under a **neutral filename** (no version-control or harness vocabulary in the name), then copy or patch it into the repository at its final path |
| (iii) scope match | the pre-persist match of REQ-HARN-023 and the snapshot pair observe the **final repository path**; the scratchpad name is never matched and never appears in the finding |
| (iv) `blocked_writes` | reserved for writes that the fallback **also** could not land; a leaf that used the staging path reports `blocked_writes: []` and the file appears in the observed window as an ordinary `IN` path |

The dispatch templates are unchanged (no template tells the leaf how to write
files); this is a documentation requirement on the reference only. The
orchestrator does not treat a staged-then-copied write differently from any
other `IN` path.

### Skill Changes (REQ-SKILL-HARNESSP2-004 snapshot half, REQ-SKILL-HARNESSP2-007)

| Where | Change |
|---|---|
| `skills/sdd-orchestrate/references/write-scope.md` §3 | provisioning step and the four-part observation above; the snapshot-base rule sentence |
| `skills/sdd-orchestrate/references/write-scope.md` §5 | limitation **(c)** with both remedies, listed beside (a) (partially closed by `arbitrated-handoff.md` §Section Resolution for Markdown paths) and (b) (with the `.sdd/` exception of `telemetry.md`) — `.sdd/` appears in `write-scope.md` only inside §3 and §5 |
| `skills/sdd-orchestrate/references/write-scope.md` §6 | the staging path, points (i)–(iv) |
| `skills/sdd-orchestrate/SKILL.md` / `references/dispatch-templates.md` | the sequential-pipeline and fix provisioning step names the branch tip the leaf is told to reach; the PIPELINE template's "reach commit" instruction is dropped when remedy (i) is in effect |
| `tools/sdd-scope-check-selftest.py` | scenario F9 (two assertions); the docstring's "six scenarios" wording becomes the current count (with F7 `telemetry.md`, F8 `arbitrated-handoff.md`) |

**`sdd-implement` references split (Q-IMPL-083, REQ-SKILL-HARNESSP2-007)** —
the same operation the v5 cycle performed on `sdd-orchestrate` (REQ-LINT-007):

| Section of `skills/sdd-implement/SKILL.md` | Moves to | Stub keeps |
|---|---|---|
| Step 3 detail: attempt ledger, oscillation rule, budget exhaustion, checkpoint composition | `skills/sdd-implement/references/stuck-detection.md` | the literals `oscillation` and `checkpoint` (lint `REQUIRED` rows, REQ-LINT-006), one-paragraph summary, a resolving `references/stuck-detection.md` link |
| leaf return contract (`RETURN:` block, `BUDGET_EXHAUSTED`, `budget_consumed`) | `skills/sdd-implement/references/leaf-return.md` | the `RETURN:` and `BUDGET_EXHAUSTED` literals, the status enum line, a resolving link |
| everything else (Steps 1–2, 4–6, Q-IMPL protocol, chunk close, rules) | stays | — |

Guards: `sdd-implement/SKILL.md` ≤ 400 lines (no size warn) — the live warn
set returns to {`sdd-orchestrate`, `sdd-migrate`}; every `REQUIRED` literal
either remains in the stub or its row is re-pointed at the reference file,
with `--self-test` §7 still covering it; standalone `sdd-implement` behaviour is
unchanged (the moved text is read on demand via the link, as `sdd-orchestrate`'s
references are). Q-IMPL-083 in `harness-loop-control.md` and Q-IMPL-084 in
`skill-lint-v5.md` are closed by a `[resolved by REQ-SKILL-HARNESSP2-007]`
note appended at implementation time (append-only).

## Verification

### Automated

- `test_provision_at_branch_tip`: a sequential dispatch's worktree HEAD equals
  the workstream branch tip at dispatch; the prompt names no catch-up commit.
- `test_catch_up_excluded` (scope self-test F9): worktree one commit behind the
  named base, leaf fast-forwards → `SCOPE: CLEAN` and `CATCH-UP <from>..<base>
  (1 commits, excluded — base <sha>)`.
- `test_catch_up_plus_out_write` (F9, second assertion): plus one out-of-scope
  write → `SCOPE: VIOLATION (1 paths)` naming only that path; the `CATCH-UP`
  line still present.
- `test_catch_up_by_merge`: leaf merges the named base instead of
  fast-forwarding → the merge commit's conflict-free paths are not `OUT`.
- `test_ancestry_still_enforced`: a rewrite that drops the named base from
  `HEAD_after`'s ancestry → `HISTORY_REWRITE`.
- `test_no_catch_up_line_when_current`: `N == 0` → no `CATCH-UP` line; output
  byte-identical to v5 for that case.
- `test_write_scope_reference_sections`: `write-scope.md` §5 lists (a), (b),
  (c); §3 states the snapshot-base rule; §6 contains points (i)–(iv) and the
  phrase "expected"; `.sdd/` occurs in `write-scope.md` only inside §3 and §5.
- `test_staged_write_is_plain_in`: a leaf that stages in the scratchpad and
  copies in reports `blocked_writes: []` and the path is `IN`.
- `test_implement_split`: `sdd-implement/SKILL.md` ≤ 400 lines; each stub has
  a resolving `references/` link; lint exits 0 and `--self-test` §7 covers the
  (re-pointed) rows; the size warn set is {`sdd-orchestrate`, `sdd-migrate`}.

### Manual

- Re-run the RS-HARNESSP2-001 Q6 situation (worktree behind the tip, prompt
  names the tip) and confirm zero false-positive `OUT` paths.

### Acceptance Criteria

- [ ] Snapshot base = the instructed tip; remedy (i) provisioning at the branch tip by default; remedy (ii) named-base exclusion with the four-part observation; `CATCH-UP <from>..<base> (N commits, excluded — base <sha>)` line; ancestry intact; limitation (c) in §5 with both remedies; scope self-test F9 with both assertions (REQ-HARN-HARNESSP2-001)
- [ ] `write-scope.md` §6 documents the staging path as expected with points (i)–(iv); a staged write is a plain `IN` with `blocked_writes: []`; templates unchanged (REQ-HARN-HARNESSP2-002)
- [ ] `write-scope.md` §3/§5/§6 changes and the provisioning step in `sdd-orchestrate` (REQ-SKILL-HARNESSP2-004)
- [ ] `sdd-implement` split: two reference files, stubs with resolving links and the `REQUIRED` literals, ≤ 400 lines, lint green, `--self-test` §7 coverage (REQ-SKILL-HARNESSP2-007)
- [ ] `python3 tools/sdd-scope-check-selftest.py` and `python3 tools/sdd-skill-lint.py` exit 0

## Edge Cases

- **Named base is not reachable from the branch** (typo in a hand-written
  prompt): `git rev-list HEAD_prov..base` fails → the orchestrator falls back to
  `HEAD_before := HEAD_prov` and renders `CATCH-UP base <sha> unresolved —
  window from <HEAD_prov>`; no exclusion is applied.
- **Leaf ignores the catch-up instruction**: `HEAD_after` does not contain
  `base` → the ancestry check fails → `HISTORY_REWRITE`? No: the leaf did not
  rewrite, it under-delivered. Default: when `base` is not an ancestor of
  `HEAD_after` **and** `HEAD_prov` is, render `CATCH-UP not performed (base
  <sha>)` as a warning, take `HEAD_before := HEAD_prov`, and do not count it as
  a violation; only a `HEAD_after` that contains neither is `HISTORY_REWRITE`.
- **Fan-out leaves**: already provisioned at the branch point (`fan-out.md`
  §3); `<base>` is the branch point and remedy (ii) never applies.
- **Under marker `3`**: `base` is `main`'s tip (or the current HEAD when
  working on a feature branch); the rule is identical.
- **The scratchpad is outside the repository**: writes there are the
  sandbox's concern (`harness-write-scope.md` §Recorded v1 Limitations) and are
  never observed — consistent with point (iii).

## Cross-Spec Consistency (XSPEC)

- `harness-write-scope.md` §Observation: the three commands are kept; (b) is
  re-based on the named base and (d) is added; §Snapshot Ordering: unchanged
  sequence, `snapshot(before)` now explicitly at `base`; §Recorded v1
  Limitations gains (c); §Blocked-Write Fallback gains the staging path —
  all recorded there as Q-IMPL-HARNESSP2-002.
- `harness-return-contract.md` §RETURN Block: `blocked_writes` semantics
  narrowed to "the fallback also failed" — consistent with its "leaf could not
  write" definition; `files_written` lists the final path.
- `orchestration.md` §Sequential Execution / `fan-out.md` §3: provisioning at
  the branch point for leaves is the model remedy (i) generalises to sequential
  dispatches — recorded as Q-IMPL-HARNESSP2-008.
- `ws-integration.md`: the workstream branch tip is the base under marker
  `4`; merge and revert targets unchanged.
- `telemetry.md` `git.head_before` records the **named base** (the effective
  `HEAD_before`), and `git.head_after` the return HEAD — consistent.
- `arbitrated-handoff.md` §Section Resolution operates on the same
  `HEAD_before`/`HEAD_after` pair — consistent.
- `skill-lint-v5.md` §Marker-4 Prose Move is the precedent for the
  `sdd-implement` split; `REQUIRED` rows for `oscillation`, `checkpoint`,
  `RETURN:`, `BUDGET_EXHAUSTED` are preserved or re-pointed; Q-IMPL-084's warn
  set note is closed.
- **No unresolved contradictions.**

## Open Questions

1. **Should remedy (ii) also require the named base's author date to precede
   `ts_dispatch`** (RS-HARNESSP2-001 Q6's original wording)? Default: no — a
   commit the orchestrator itself named is by construction pre-dispatch; the
   date check adds a clock dependency for no coverage.
2. **Reference file names for the `sdd-implement` split** (`stuck-detection.md`,
   `leaf-return.md`): Default: as tabled; the implementer may merge them into
   one file if the stub links still resolve and the size target holds.
3. **Should the staging path be mentioned in the templates after all?**
   Default: no (REQ-HARN-HARNESSP2-002 says reference only); revisit if a third
   data point shows leaves still stalling on the refusal.
