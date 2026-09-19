---
status: Approved
last_updated: 2026-09-19
requires:
  - REQ-WS-016
  - REQ-WS-017
  - REQ-WS-018
---

# Multi-Workstream Git Integration Model

## Context

The v4 layout (`ws-layout.md`) makes each workstream a git branch (REQ-WS-002). Two
downstream mechanisms currently anchor on `main`: the implement-stage fan-out (which
took exclusive ownership of `main` and inferred "conflict after re-derivation =
boundary error" from that ownership), and `sdd-verify`'s regression diff (computed
against `main`). Under concurrent workstreams, both anchors are wrong: `main` now
accumulates other workstreams' merged work, so fan-out on `main` would collide across
workstreams and verify would report other workstreams' changes as false regressions.

This spec re-points the integration model onto the **workstream branch**. It covers
REQ-WS-016..018.

## Design

### Integration Is Branch-per-Workstream → PR to main (REQ-WS-016)

Each workstream integrates by opening a **pull request from its branch to `main`**.
The **workstream branch — not `main`** — is the integration unit for that workstream's
whole cycle.

- A completed workstream merges to `main` via PR.
- Two workstreams can have open PRs simultaneously; neither owns `main` exclusively.

**Why PR-per-workstream**: it keeps `main` free of any single workstream's exclusive
ownership and matches the branch-per-issue boundary (REQ-WS-002). `main` becomes the
shared trunk that workstreams land into, not a working surface.

### Fan-out Worktrees Branch from the Workstream Branch (REQ-WS-017)

Implement-stage fan-out (the orchestrator-owned, one-level-deep parallelism defined in
the ORCH specs) is re-anchored:

- Fan-out worktrees branch from the **WORKSTREAM branch**, not from `main`.
- They merge back into the **workstream branch**, not `main`.
- Fan-out no longer takes exclusive ownership of `main`.
- The **"conflict-after-re-derivation = boundary error" inference tied to
  `main`-ownership is REMOVED.** With per-workstream branches, `main` is not the
  fan-out integration point, so a conflict there no longer implies a chunk-boundary
  error.

```
fan-out (workstream <id>):
    base   = <id> branch (HEAD)
    for each concurrently-runnable chunk-group:
        worktree branched from base
    merge each worktree back into <id>          # not main
    # main is untouched until the workstream PR (REQ-WS-016)
```

**Why branch fan-out off the workstream branch**: with per-workstream branches, `main`
is not the fan-out integration point; branching fan-out from the workstream branch
keeps parallel implement work inside the workstream's isolation boundary and lets
other workstreams' `main` merges proceed independently.

**Interaction note**: this changes the base branch and the merge target of the existing
fan-out design; the fan-out mechanics (worktree provisioning ownership, sequential
merge-back, inline git identity, conflict abort-and-redo-at-orchestrator) are otherwise
unchanged. The one removed element is the `main`-ownership boundary-error inference.

### Verification Regression Base Is the Workstream Branch Point (REQ-WS-018)

`sdd-verify` computes its regression diff against the **workstream branch point** (the
merge-base of the workstream branch and `main` at branch creation), not against `main`.

```
regression_base(<id>) = merge-base(<id>, main)   # the point <id> branched
sdd-verify diff = <id> HEAD  vs  regression_base(<id>)
```

A workstream's verification reflects only that workstream's changes.

**Why diff against the branch point, not `main`**: diffing against current `main` would
fold in unrelated concurrent workstreams' changes that merged to `main` after this
workstream branched, producing false regressions. The branch point isolates this
workstream's own delta regardless of what else landed on `main` meanwhile.

## Verification

### Automated
- Verify the fan-out reference/spec branches worktrees from the workstream branch and
  merges back into it, with no step that takes exclusive ownership of `main`.
- Verify the `main`-ownership boundary-error inference is removed from the fan-out
  logic.
- Verify `sdd-verify` computes its regression base as `merge-base(<id>, main)`, not
  `main` HEAD.

### Manual
- Run a fan-out in `ISSUE-42`; confirm worktrees are branched from `ISSUE-42`, merged
  back into `ISSUE-42`, and `main` is untouched until the workstream PR.
- Merge an unrelated `ISSUE-57` to `main`, then run `sdd-verify` for `ISSUE-42`;
  confirm reported regressions are relative to `ISSUE-42`'s branch point and unaffected
  by `ISSUE-57`.
- Open PRs for two workstreams simultaneously; confirm both can be open at once.

### Acceptance Criteria
- [ ] Each workstream integrates via PR from its branch to `main`; the branch is the
      integration unit; concurrent open PRs are supported (REQ-WS-016)
- [ ] Fan-out worktrees branch from the workstream branch and merge back into it; no
      exclusive `main` ownership (REQ-WS-017)
- [ ] The `main`-ownership "conflict = boundary error" inference is removed (REQ-WS-017)
- [ ] `sdd-verify` regression base is the workstream branch point, not `main`
      (REQ-WS-018)
- [ ] A workstream's verification is independent of other workstreams merged to `main`
      meanwhile (REQ-WS-018)
- [ ] Markdown well-formed; frontmatter valid

## Implementation Questions

### Q-IMPL-014: Retaining the sequential fallback while removing the boundary-error inference
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Fan-out Worktrees Branch from the Workstream Branch (REQ-WS-017) — "the 'conflict-after-re-derivation = boundary error' inference tied to `main`-ownership is REMOVED"; `references/fan-out.md` section 3c, step 3
**Decision**: In `fan-out.md` §3c step 3, the pre-v4 text coupled *two* things: (a) the **inference** that a repeat conflict after re-derivation proves non-independence (a chunk-boundary error), and (b) the **guaranteed-termination sequential fallback** that path triggers. Under marker `4` I removed (a) — the labeling — but **retained (b)** unchanged, gated as a marker-`4` note: the affected groups are still re-run one at a time (each re-branched from the updated *workstream branch* and merged back into it), which cannot conflict by construction and guarantees termination. Rationale for keeping (b): the spec removes only the boundary-error *inference* ("main is not the fan-out integration point, so a conflict there no longer implies a chunk-boundary error") and states all other fan-out mechanics — including conflict abort-and-redo — are "otherwise unchanged". Without a terminating fallback the loop could spin, so the sequential collapse is preserved as a pure termination guarantee, just no longer justified by a non-independence claim (since `main` can now move under the workstream, a conflict is no longer diagnostic).
**Rationale**: Faithful to REQ-WS-017 (drop the `main`-ownership inference) while preserving the guaranteed-termination property the fan-out design depends on; marker-`3` text keeps both (a) and (b) byte-unchanged.
