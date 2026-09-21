---
status: Approved
last_updated: 2026-07-21
requires:
  - REQ-WS-001
  - REQ-WS-002
  - REQ-WS-003
  - REQ-WS-004
  - REQ-WS-005
  - REQ-WS-006
  - REQ-WS-019
  - REQ-WS-020
---

# Multi-Workstream Layout & Isolation (v4)

## Context

The SDD workflow's execution artifacts are repo-global singletons: `docs/plan.md`,
`docs/verification.md`, `docs/plan-history/`, and a flat `docs/handoff/kickoff.md`.
Under concurrent use — a team running several SDD cycles at once, one branch/issue
each — these fixed paths collide, one cycle's plan overwrites another's, and phase
detection (a pure function of the shared repo) misroutes one cycle's session into
another's state. RS-007 confirmed the fix is structural, not conventional.

This spec establishes the **v4 layout**: a "workstream" is an execution unit that
owns its artifacts under `docs/ws/<id>/`, while requirements, specs, research, and
the traceability corpus stay shared at their existing top-level paths. Phase becomes
a function of `(repo, workstream)`. It is the foundational spec for the
multi-workstream feature; `ws-ids.md`, `ws-traceability.md`, `ws-staleness.md`,
`ws-integration.md`, `ws-migration.md`, and `ws-orchestration.md` build on the layout
and identifiers defined here.

Covers REQ-WS-001..006, REQ-WS-019, REQ-WS-020.

## Design

### v4 Directory Layout (REQ-WS-001)

```
docs/
  .sdd-version                    # "4" — sole layout gate (see ws-migration.md)
  research/                       # SHARED corpus (ws-prefixed IDs, see ws-ids.md)
  requirements/                   # SHARED corpus (index + category files)
    index.md
    traceability.md               # SHARED aggregated matrix (see ws-traceability.md)
  spec/                           # SHARED corpus (append-only new files)
  ws/
    <id>/                         # one directory per workstream
      kickoff.md                  # workstream-owned handoff (see ws-orchestration.md)
      plan.md                     # workstream-owned plan
      plan-history/               # workstream-owned archived plans
      traceability.md             # workstream-owned rows (see ws-traceability.md)
      verification.md             # workstream-owned verification report
```

**Workstream id (`<id>`)**: a slug identifying the workstream, conventionally the
branch/issue key (e.g. `ISSUE-42`, `ISSUE-57`). The reserved id `default` is the
implicit workstream for migrated and solo repos (REQ-WS-020).

**Shared vs. owned split** — the load-bearing invariant:

| Corpus | Location | Ownership | Write model |
|--------|----------|-----------|-------------|
| research | `docs/research/` | shared | append new ws-prefixed dirs |
| requirements | `docs/requirements/` | shared | append new IDs/rows, sorted insertion |
| specs | `docs/spec/` | shared | append new files only |
| aggregated traceability | `docs/requirements/traceability.md` | shared (derived) | regenerated, never hand-merged |
| kickoff / plan / plan-history / verification / per-ws traceability | `docs/ws/<id>/` | workstream | free read/write within own dir |

**Why scope execution paths by workstream**: fixed singletons collide under
concurrency; a per-workstream directory makes isolation structural rather than a
naming convention that a second operator can forget. No flat `docs/plan.md` or
`docs/verification.md` is read or written in a v4 repo.

### Workstream = Execution Unit Over a Shared Subset (REQ-WS-004, REQ-WS-005)

Requirements and specs remain a **single common product corpus**. New work ADDs to
the shared sets (new IDs, new files — see `ws-ids.md`); it never forks or copies them
per workstream. A directory `docs/ws/<id>/requirements/` or `docs/ws/<id>/spec/` must
never be created.

A workstream is modeled as an execution unit that **references** a subset of the
shared corpus through traceability — not as a copy of the docs. Its scope (which
shared REQ/SPEC it delivers) is discoverable from the traceability join
(`ws-traceability.md`) and is derivable live by walking its plan's `task → spec
requires: → requirement` chain (`ws-staleness.md`). The requirement text itself
stays product-wide and carries **no** workstream-ownership marker.

**Why decouple product-scope from execution-scope**: one product has one requirement
set and one spec set; per-workstream copies would diverge and defeat traceability.
The reference model is also what bounds each workstream's staleness
(REQ-WS-007 / REQ-WS-026).

### Phase Detection Is a Function of (repo, workstream) (REQ-WS-003)

Every `sdd-*` skill's step-0 phase detection takes a **workstream argument** that
defaults to `default`, and resolves the current phase from that workstream's
`docs/ws/<id>/` execution artifacts plus the shared corpus — not from repo-global
execution paths.

Contract (per skill step-0, v4 branch):

```
detect_phase(repo, ws = "default"):
    if read(docs/.sdd-version) != "4":  route to sdd-migrate   # see ws-migration.md
    base   = docs/ws/<ws>/
    plan   = base + "plan.md"
    verif  = base + "verification.md"
    # phase resolved from THIS ws's execution artifacts + the shared corpus,
    # exactly as the v3 detection table did, but rooted at docs/ws/<ws>/ not docs/
```

**Result**: with `ISSUE-42` at implement and `ISSUE-57` at plan, invoking a skill
against each id reports that id's phase; omitting the id resolves `default`. One
workstream's state can no longer misroute another's session.

**Why an explicit argument with a default**: today "the current phase" is a pure
function of the shared repo, so concurrent cycles alias onto one state. A workstream
key threaded through step-0 disambiguates them while the `default` fallback keeps solo
use argument-free (REQ-WS-020).

### Branch-per-Issue Isolation Boundary (REQ-WS-002)

Each workstream corresponds to its own git branch (branch-per-issue). Isolation
between concurrent workstreams is provided by **git branching plus the
`docs/ws/<id>/` scoping** — never by naming discipline within a single branch.

- Opening a workstream creates or uses a dedicated branch.
- Two workstreams' execution artifacts never share a path on the same branch (each
  lives under its own `docs/ws/<id>/`).

**Why lean on git**: git already provides isolation and merge machinery. Leaning on
it avoids the ad-hoc hand-suffixed workaround files the current model produced (e.g.
`verification-rs002.md`). The integration model for these branches is specified in
`ws-integration.md`.

### A Workstream Owns Only Its Execution Artifacts (REQ-WS-006)

A workstream owns exactly `kickoff.md`, `plan.md`, `plan-history/`, and
`verification.md` under `docs/ws/<id>/` (plus its own `traceability.md`, per
`ws-traceability.md`). Concurrent planning or verification in one workstream must
not archive, overwrite, or route the plan/verification of any other workstream.

Contract:
- `sdd-plan`'s plan rewrite/archive operates only within `docs/ws/<id>/plan.md` and
  `docs/ws/<id>/plan-history/`.
- A failing `sdd-verify` writes only `docs/ws/<id>/verification.md` and routes only
  `<id>` into replan — never another workstream.

**Why**: the current `sdd-plan` archive-and-overwrite of the singleton `plan.md`,
and the single global `verification.md` pass/fail, cross-contaminate unrelated
sessions. Per-workstream ownership removes the shared write point for execution
artifacts entirely (shared-corpus writes are handled merge-safely — see `ws-ids.md`).

### Approval Is a Per-Workstream Bare Status Flag (REQ-WS-019)

Approval remains a bare `status` frontmatter flag. It is scoped:

- **per workstream** where the artifact is workstream-owned — `docs/ws/<id>/plan.md`,
  `docs/ws/<id>/verification.md` carry their own `status`;
- **per shared artifact** where the corpus is shared — `docs/requirements/*` and
  `docs/spec/*` carry a single product-wide `status`.

No approver identity, signature, or quorum is recorded. One workstream's approval
`status` does not gate another's.

**Why bare status**: identity/quorum is explicitly out of scope (YAGNI); a bare flag
suffices for the single-operator-per-workstream model. Recording an approver would
add a field with no consumer.

### Solo Use Runs in an Implicit Ceremony-Free `default` Workstream (REQ-WS-020)

Solo (single-operator) use runs in the implicit `default` workstream and must feel
unchanged:

- The operator is never required to name a workstream.
- Every skill defaults the workstream argument to `default` throughout.
- All execution artifacts land under `docs/ws/default/`; the shared corpus is used
  as-is.

**Why an implicit default**: the feature must not tax the common single-operator case
with multi-workstream ceremony. `default` is a real workstream id, so the solo path
exercises the same code paths as the multi-workstream path — no separate legacy
branch to maintain.

## Deferred work

**`docs/spec/overview.md` must be updated to v4 during the implement phase.** Its
§Version Marker still lists only `2` and `3` (must add `4`, per REQ-WS-023) and its §ID
Namespaces still documents the un-prefixed v2 ID formats (must add the `<WS>` workstream
segment to the RS / REQ / Q-IMPL formats, per `ws-ids.md` / REQ-WS-009). This edit is
deferred to implement and tracked in `ws-migration.md` § Deferred work so `sdd-plan`
emits an explicit `overview.md`-update task.

## Verification

### Automated
- Verify each `sdd-*` skill's step-0 accepts a workstream argument defaulting to
  `default` and roots execution-artifact reads at `docs/ws/<ws>/`.
- Verify no skill reads or writes flat `docs/plan.md` / `docs/verification.md` under
  marker `4`.
- Verify no code path creates `docs/ws/<id>/requirements/` or `docs/ws/<id>/spec/`.

### Manual
- In a v4 repo, create `ISSUE-42` and `ISSUE-57`; confirm each has independent
  `docs/ws/<id>/plan.md` and that `docs/requirements/` and `docs/spec/` are single
  shared trees.
- Run `sdd-plan` (including a rewrite/archive) in `ISSUE-42`; confirm `ISSUE-57`'s
  plan/plan-history/verification are byte-unchanged and `ISSUE-57` is not routed to
  replan.
- Run a full solo cycle without ever naming a workstream; confirm all artifacts land
  under `docs/ws/default/`.

### Acceptance Criteria
- [ ] v4 layout: execution artifacts under `docs/ws/<id>/`; requirements/spec/research/
      traceability shared at top level (REQ-WS-001)
- [ ] Reserved id `default` used for migrated/solo repos (REQ-WS-001, REQ-WS-020)
- [ ] No flat `docs/plan.md` / `docs/verification.md` read or written in v4 (REQ-WS-001)
- [ ] Each workstream corresponds to its own git branch; isolation via git + scoping,
      not naming discipline (REQ-WS-002)
- [ ] Every skill's step-0 takes a workstream arg (default `default`) and resolves phase
      from `docs/ws/<id>/` + shared corpus (REQ-WS-003)
- [ ] Requirements and specs stay a single shared corpus; new work only ADDs IDs/files;
      no per-ws requirements/spec dir (REQ-WS-004)
- [ ] A workstream references a shared REQ/SPEC subset via traceability, not a copy; its
      scope is enumerable (REQ-WS-005)
- [ ] A workstream owns only kickoff/plan/plan-history/verification; concurrent plan or
      verify never touches another ws's artifacts (REQ-WS-006)
- [ ] Approval is a bare `status`, scoped per-ws for owned artifacts and per shared
      artifact for the corpus; no approver identity/quorum (REQ-WS-019)
- [ ] Solo use runs in implicit `default` with no workstream naming required (REQ-WS-020)
- [ ] Type checking / markdown well-formedness passes; frontmatter valid

## Implementation Questions

### Q-IMPL-008: Step-0 gate condition preserves marker-`3` behavior verbatim
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Phase Detection Is a Function of (repo, workstream) — the
`detect_phase` pseudocode `if read(docs/.sdd-version) != "4": route to sdd-migrate`.
**Decision**: The nine skills' step-0 gate is implemented as `if marker == "4":
<workstream-aware v4 path>  else: <run the existing v3 detection UNCHANGED>` — the
`else` arm does **not** unconditionally "route to migrate". `docs/.sdd-version`
is the sole gate; a repo at marker `3` (the current live state of this repo) runs
its existing detection exactly as before, which itself only suggests `sdd-migrate`
when the marker is missing/v1 — never for a working v3 repo.
**Rationale**: Taken literally, `!= "4" → route to sdd-migrate` would force every
marker-`3` entry to redirect to migration, observably changing v3 solo behavior and
violating the v3-solo-safety invariant (a marker-`3` repo must behave exactly as it
does today). The pseudocode describes the v4-side contract; the transition window
requires marker `3` to remain a fully working layout (REQ-WS-023: "with marker `3`,
skills read flat paths and a v4-aware skill suggests migration" — the suggestion is
*available*, not a forced redirect on every entry). The actual v3→v4 migration
routing is added by `sdd-migrate` in a later chunk (`ws-migration.md`). Default
carried: gate strictly on `marker == "4"`; leave all marker-`3` detection paths
byte-unchanged.

### Q-IMPL-020: Chunk 8 holistic verification runs on throwaway fixtures; this repo stays marker `3`
**Tier**: 2 (spec ambiguity)
**Spec reference**: § Verification (all `ws-*.md` specs) — the acceptance criteria are
behavioral (concurrent merges, staleness dates, migration interruption, regression base)
but there is no compiled code to unit-test; the plan's Risks note "verification is prose
review + git merge/interruption walkthroughs on fixtures".
**Decision**: Chunk 8 verified every spec's acceptance criteria WITHOUT flipping this
repo to marker `4`. Load-bearing runtime behaviors were exercised on throwaway `$TMPDIR`
git fixtures (two-workstream isolation + concurrent 3-way merges, `stale_inputs(<id>)`
plan-walk, v3→v4 copy-verify-flip-cleanup with interruption, fan-out re-anchor +
`merge-base` regression base, marker-`3` v3-solo-safety), each reproducing the algorithm
the relevant SKILL.md prose describes; the prose-encoded criteria not reducible to a
runnable merge/date check (all-nine-skills step-0 gate, four generators, integration/
migration/doc consistency) were confirmed by a cross-skill grep sweep of the shipped
`skills/`. Fixtures were deleted; nothing leaked into this repo or its branch. The
Verified column of the marker-`3` shared 5-column `docs/requirements/traceability.md`
was filled `pass` for REQ-WS-001..029 (chunk-close Check 2). `docs/verification.md` was
NOT written — that is the separate verify STAGE, which Chunk 8 (the plan's own
holistic verify chunk) precedes.
**Rationale**: Constraint #1 (v3-solo-safety) forbids flipping this repo's marker, so v4
behavior must be verified on isolated fixtures rather than in-place. For a meta-feature
whose "code" is markdown skill prose, fixture walkthroughs that re-run the described
algorithm are the strongest available evidence and match the plan's own verify-task
depth default; the cross-skill sweep is the plan's designated backstop for the breadth-
of-edits risk. Recording Verified in the marker-`3` shared matrix (not per-ws files)
follows the marker-`3` traceability rule since this repo is still at marker `3`.
