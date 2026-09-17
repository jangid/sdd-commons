---
last_updated: 2026-07-23
status: Approved
---

# Implementation Plan: Multi-Workstream SDD (v4)

## Overview

Reshape the nine `sdd-*` skills so a team can run several SDD cycles concurrently
in one repo — one branch/issue per **workstream** — without artifact collisions,
false staleness, ID races, or cross-workstream phase confusion, while keeping
requirements/specs/research/traceability a single shared corpus and keeping solo
use ceremony-free. This is a **meta-feature**: the implementation edits the SDD
skill definitions themselves (`skills/sdd-*/SKILL.md` and
`skills/sdd-orchestrate/references/`), the canonical convention docs
(`docs/spec/overview.md`, `CLAUDE.md`), and the migration logic
(`skills/sdd-migrate/`). The structural core is the **v4 layout**: execution
artifacts move under `docs/ws/<id>/` while the shared corpus stays at top level,
and `docs/.sdd-version` = `4` is the sole atomic gate that flips every skill's
step-0 to the per-workstream layout. Because the flip is atomic, v4 ships as one
coherent delivery (single milestone) — you cannot ship "layout" without
"migration". Chunks are ordered by dependency: the layout/phase-detection
foundation (Chunk 0) precedes the ID, traceability, staleness, integration,
migration, and orchestration work that all root on it, with documentation and
holistic verification last.

All four principal risk axes were de-risked by RS-007 (merge-safe shared writes,
staleness generalization, v3→v4 migration safety, ID-format blast radius), so this
plan carries **no spike** tasks — only `implement` and `verify`.

## Conventions

- **Task types**: `[implement]` edits SKILL.md / reference / convention-doc prose
  (there is no compiled code here — the "code" is the skills' described
  algorithms); `[verify]` validates behavior against a spec's verification criteria
  (concurrency/merge checks, migration interruption, unchanged-parser checks) — it
  goes beyond "markdown lints".
- **Chunk headers**: `### Chunk N: <name>`; each chunk carries a `**Depends on**`
  field naming the chunk(s) it requires (the orchestrator's fan-out boundary
  derivation parses these — see `docs/spec/plan-management.md`).
- **Traceability**: each task names the REQ-WS id(s) and spec section it implements.
  The traceability Impl column is filled during implement, not here.
- **Dates**: authored 2026-07-21.

## Chunks

### Chunk 0: v4 layout foundation & phase-detection parameterization
**Status**: CLOSED (2026-07-23) — tasks 1–5 done; all nine skill step-0 sections carry a marker-`4` workstream-aware branch, marker-`3` behavior retained byte-unchanged (see Q-IMPL-008 in `ws-layout.md`).
**Depends on**: none (first chunk).
**Goal**: Every `sdd-*` skill's step-0 is workstream-aware under marker `4`:
it takes a workstream argument defaulting to `default`, roots execution-artifact
reads at `docs/ws/<ws>/`, and leaves the shared corpus at top level. After this
chunk the layout contract and phase-detection function are defined for all skills;
solo use still resolves `default` with no ceremony. Traces to `ws-layout.md`.
**Tasks**:
1. [implement] Add a v4 branch to the step-0 phase detection of **each** of the nine
   skills (`sdd-research`, `sdd-requirements`, `sdd-specs`, `sdd-plan`,
   `sdd-implement`, `sdd-verify`, `sdd-replan`, `sdd-migrate`, `sdd-orchestrate`):
   accept a `workstream` arg (default `default`); when `docs/.sdd-version` == `4`,
   resolve `base = docs/ws/<ws>/` and read `plan.md`/`verification.md`/`kickoff.md`
   from there; keep the v3 branch (marker `3`) unchanged. — traces to
   `ws-layout.md` §Phase Detection Is a Function of (repo, workstream) (REQ-WS-003),
   §.sdd-version gate (REQ-WS-023 layout-read half).
2. [implement] Encode the shared-vs-owned invariant in the affected skills: a
   workstream owns only `kickoff.md`, `plan.md`, `plan-history/`, `verification.md`
   (+ its `traceability.md`) under `docs/ws/<id>/`; requirements/specs/research/
   aggregated-traceability stay shared at top level; **no** skill creates
   `docs/ws/<id>/requirements/` or `docs/ws/<id>/spec/`, and no skill reads/writes
   flat `docs/plan.md` / `docs/verification.md` under marker `4`. — traces to
   `ws-layout.md` §v4 Directory Layout (REQ-WS-001), §Workstream = Execution Unit
   (REQ-WS-004, REQ-WS-005), §A Workstream Owns Only Its Execution Artifacts
   (REQ-WS-006).
3. [implement] Scope `sdd-plan`'s plan rewrite/archive and `sdd-verify`'s fail-route
   to the active workstream only: archive within `docs/ws/<id>/plan-history/`, write
   only `docs/ws/<id>/verification.md`, route only `<id>` into replan — never another
   workstream's artifacts. — traces to `ws-layout.md` §A Workstream Owns Only Its
   Execution Artifacts (REQ-WS-006).
4. [implement] Encode approval as a bare per-scope `status` flag: workstream-owned
   `plan.md`/`verification.md` carry their own `status`; shared `requirements/*`,
   `spec/*` carry one product-wide `status`; no approver identity/quorum; and the
   implicit ceremony-free `default` workstream (never require naming a workstream;
   default the arg everywhere; solo artifacts land under `docs/ws/default/`). —
   traces to `ws-layout.md` §Approval Is a Per-Workstream Bare Status Flag
   (REQ-WS-019), §Solo Use Runs in an Implicit `default` Workstream (REQ-WS-020),
   and branch-per-issue isolation note (REQ-WS-002, boundary only; git mechanics in
   Chunk 4).
5. [verify] Confirm every skill's step-0 accepts a workstream arg defaulting to
   `default` and roots execution reads at `docs/ws/<ws>/`; no skill reads/writes flat
   `docs/plan.md`/`docs/verification.md` under marker `4`; no path creates a per-ws
   `requirements/`/`spec/` dir. — traces to `ws-layout.md` §Verification/Automated.
**Entry criteria**: none.
**Exit criteria**: all nine step-0 sections carry a marker-`4` workstream-aware
branch defaulting to `default`; shared-vs-owned and approval invariants documented;
verify task passes.

### Chunk 1: Workstream-prefixed IDs & merge-safe shared writes
**Status**: CLOSED (2026-07-23) — tasks 1–6 done; the four generators + sdd-review
convention string emit/accept ws-prefixed ids under a marker-`4` branch (marker-`3`
generation retained byte-unchanged), merge-safe shared-write rules encoded in
sdd-requirements/sdd-specs, and "do NOT touch" guards added to the four
RS-007-Q4-unaffected parsers (fan-out `Depends on: Chunk N`, requirements/traceability
row parsing, Q-REQ/Q-SPEC/Q-IMPL content checks, `### M\d+:` milestone regex). See
Q-IMPL-009/010 in `ws-ids.md`.
**Depends on**: Chunk 0.
**Goal**: The four ID generators + the `sdd-review` convention string emit and
accept ws-prefixed ids with per-workstream counters, and shared-table writes are
merge-safe (sorted insertion / owned rows) — never tail-append. Parsers proven
unaffected by RS-007 Q4 stay untouched. Traces to `ws-ids.md`.
**Tasks**:
1. [implement] Update the ID format + per-workstream counter in the four generators:
   `sdd-research` (`RS-<WS>-NNN` dir scan), `sdd-requirements`
   (`REQ-<DOMAIN>-<WS>-NNN`, max per domain+workstream), `sdd-implement`
   (`Q-IMPL-<WS>-NNN`, per-workstream), and `sdd-migrate`'s RS/REQ allocation/remap
   template (add the `<WS>` slot for NEW allocations only). Each parses `NNN` **after**
   the `<WS>` token and scopes its max-scan per workstream, replacing the global
   scan-and-increment. Add the v4 ID behavior as a **marker-`4` branch while
   retaining the marker-`3` (v3) un-prefixed generation unchanged**: `docs/.sdd-version`
   is the sole gate — a generator seeing marker `3` mints ids exactly as today (no
   `<WS>` slot, global scan), marker `4` selects the ws-prefixed per-workstream path
   (reconciling with the `ws-layout.md` step-0 contract, where marker != 4 routes to
   the sdd-migrate / v3 path). — traces to `ws-ids.md` §Workstream-Prefixed ID Format
   (REQ-WS-009), §Per-Workstream ID Counters (REQ-WS-011), §Exactly Four Generators
   rows 1–4 (REQ-WS-012).
2. [implement] Update `sdd-review`'s convention-validation string to assert
   `REQ-<DOMAIN>-<WS>-NNN` / accept the optional `<WS>` segment instead of flagging
   ws-prefixed ids. — traces to `ws-ids.md` §Exactly Four Generators row 5
   (REQ-WS-012).
3. [implement] Add an explicit "do NOT touch" note in the relevant skills naming the
   parsers RS-007 Q4 proved unaffected (fan-out `Depends on: Chunk N`, traceability/
   requirements row prefix-glob parsing, `sdd-review` Q-REQ/Q-SPEC/Q-IMPL content
   checks, `### M\d+:` milestone regex) so no one "fixes" a provably-fine parser. —
   traces to `ws-ids.md` §Exactly Four Generators (parsers-that-MUST-NOT-change,
   REQ-WS-012).
4. [implement] Encode the merge-safe shared-write model: new requirements append
   under a claimed domain prefix (registry in `requirements/index.md`); new specs are
   new files in `docs/spec/`; modifying an existing shared REQ/spec stays a human PR
   conflict; **no raw EOF append** to any shared table. — traces to `ws-ids.md`
   §Append Under a Claimed Prefix (REQ-WS-010), §Merge-Safe Shared Writes
   (REQ-WS-013).
5. [implement] Encode ID-sorted, one-row-per-line insertion for `requirements/
   index.md` (Files table, Domain Prefixes table, new category-file rows) at the
   correct sorted position, plus the distinct-domain-prefix precondition: distinct
   prefixes → clean 3-way merge; same-domain concurrency is an accepted human PR
   conflict the tooling must NOT auto-union (record the rejected `merge=union` driver
   as an Open Question default). — traces to `ws-ids.md` §ID-Sorted Insertion
   (REQ-WS-015), §Distinct-Domain-Prefix Precondition (REQ-WS-014).
6. [verify] Confirm each generator parses `NNN` after `<WS>` and scopes per workstream
   (per domain+workstream for requirements); `sdd-review` accepts the `<WS>` segment;
   and the four proven-unaffected parsers operate unchanged against ws-prefixed ids;
   no write path performs a raw EOF append to a shared table. — traces to
   `ws-ids.md` §Verification/Automated + Manual (concurrent `RS-ISSUE42-001` /
   `RS-ISSUE57-001` no-collision; distinct vs same-domain merge behavior).
**Entry criteria**: Chunk 0 complete.
**Exit criteria**: four generators + review string updated; merge-safe write rules
encoded; unaffected parsers documented as untouched; verify task passes.

### Chunk 2: Traceability restructuring — per-workstream files + derived aggregate
**Status**: CLOSED (2026-07-23) — tasks 1–4 done; `sdd-implement` carries the canonical
marker-`4` per-ws traceability block (file shape with appended `Workstream` column,
own-rows rule, wholesale-regenerated aggregate, recorded-join/compute-live boundary), and
`sdd-verify`/`sdd-specs`/`sdd-requirements` redirect their traceability writes to
`docs/ws/<ws>/traceability.md` + regenerate the aggregate under marker `4`; marker-`3`
single-shared-file behavior retained byte-unchanged. See Q-IMPL-011/012 in
`ws-traceability.md`. Covers REQ-WS-007, REQ-WS-008.
**Depends on**: Chunk 1.
**Goal**: Each workstream owns `docs/ws/<id>/traceability.md`; the shared
`docs/requirements/traceability.md` becomes a deterministically regenerated
aggregate (never hand-merged). Traces to `ws-traceability.md`.
**Tasks**:
1. [implement] Define the per-workstream traceability file shape
   `docs/ws/<id>/traceability.md` (frontmatter `workstream:`/`last_updated:`; the
   6-column matrix with the appended `Workstream` column) and the rule that a
   workstream only ever edits its own rows — never another ws's file or the shared
   aggregate directly. Rows may cover both new ws-prefixed REQs and re-used
   pre-existing shared REQs. — traces to `ws-traceability.md` §Decision: Separate
   Per-Workstream Files (REQ-WS-008), §Per-Workstream File Shape.
2. [implement] Define the aggregation contract: `docs/requirements/traceability.md`
   is **regenerated** (shipped legacy rows under blank/`default` workstream + concat
   of all per-ws files, stable-sorted by requirement id, wholesale replacement),
   never appended/hand-merged; confirm the appended trailing `Workstream` column does
   not disturb the REQ-WS-012 unchanged-parser guarantee. — traces to
   `ws-traceability.md` §Aggregation Contract (REQ-WS-008).
3. [implement] Record that traceability is the load-bearing **recorded** join but the
   staleness **computation** never reads it (the live plan-walk in Chunk 3 derives the
   same set); no traceability schema column is added for staleness. — traces to
   `ws-traceability.md` §Traceability Is the Recorded Join; Staleness Computes Live
   (REQ-WS-007).
4. [verify] Confirm tooling writes only `docs/ws/<id>/traceability.md`, never another
   ws's file or the shared aggregate in place; regeneration is deterministic
   (same inputs → byte-identical, sorted); two concurrent workstreams' additions
   3-way-merge with no conflict. — traces to `ws-traceability.md`
   §Verification/Automated + Manual.
**Entry criteria**: Chunk 1 complete (ws-prefixed ids appear in rows; merge-safe
model established).
**Exit criteria**: per-ws file shape + aggregation contract encoded; recorded-join /
compute-live boundary stated; verify task passes.

### Chunk 3: Workstream-scoped staleness
**Status**: CLOSED (2026-07-23) — tasks 1–5 done. Under a marker-`4` branch, the
milestone-scoped staleness traversal is **generalized verbatim** (plan path
`docs/plan.md` → `docs/ws/<ws>/plan.md`, milestone key → workstream key, chain
`task → spec requires: → requirement IDs → category-file dates` unchanged, computed
live, no traceability read, no schema column) in `sdd-plan`/`sdd-implement`/
`sdd-replan` (sdd-implement also drops the v3 plan-index caveat; sdd-replan re-points
its by-name reference); `sdd-verify` gains a **new** ws-scoped branch (same live
plan-walk) + a Chunk-4 regression-base pointer (`merge-base(<ws>, main)`); `sdd-specs`
gains a **new** branch that stops treating the flat plan as a monolith and defers plan
staleness to `sdd-plan`; `sdd-requirements` research→requirements staleness confirmed
workstream-independent (only research ID pattern → `RS-<WS>-NNN`). Marker-`3`
milestone-scoped behavior retained unchanged. No replan trigger fired. See Q-IMPL-013
in `ws-staleness.md`. Covers REQ-WS-026, REQ-WS-027, REQ-WS-028.
**Depends on**: Chunk 0.
**Goal**: Staleness is scoped by workstream, computed live from the workstream's
plan with no traceability read; the two skills that lacked a scoped branch gain one
(or defer); requirements-corpus staleness stays shared. Traces to `ws-staleness.md`.
**Tasks**:
1. [implement] Generalize the milestone-scoped staleness traversal in `sdd-plan`,
   `sdd-implement`, and `sdd-replan` to a **workstream** key: swap the plan path to
   `docs/ws/<id>/plan.md` and the milestone key for a workstream key, keeping the
   `task → spec requires: → requirement IDs → category-file dates` chain unchanged and
   reading no traceability file; drop the v3 `sdd-implement` caveat about the plan
   index (there is no plan index in v4). Add this generalized traversal as a
   **marker-`4` branch while retaining the marker-`3` (v3) milestone-scoped traversal
   unchanged**: `docs/.sdd-version` is the sole gate — a skill seeing marker `3`
   computes staleness exactly as today (flat `docs/plan.md`, milestone key), marker `4`
   selects the workstream-scoped path (reconciling with the `ws-layout.md` step-0
   contract, where marker != 4 routes to the sdd-migrate / v3 path). — traces to `ws-staleness.md` §Generalize
   Milestone-Scoped Staleness (REQ-WS-026) + per-skill step-0 notes.
2. [implement] Add a **new** workstream-scoped staleness branch to `sdd-verify`:
   compare `docs/ws/<id>/plan.md`/`verification.md` only against the shared specs/
   requirements that workstream traces (same live plan-walk), never reporting
   staleness from shared-input changes outside its traced set. Also re-point
   `sdd-verify`'s regression-base note toward Chunk 4 (branch-point diff). — traces to
   `ws-staleness.md` §New Per-Workstream Staleness Branches (REQ-WS-027, verify half).
3. [implement] Update `sdd-specs` to stop treating the flat plan as a monolith: under
   v4 specs are shared and plans are per-workstream, so `sdd-specs` checks only
   requirements→spec staleness and **defers** plan staleness to `sdd-plan`'s per-ws
   branch (adopted resolution). — traces to `ws-staleness.md` §New Per-Workstream
   Staleness Branches (REQ-WS-027, specs half).
4. [implement] Confirm the research→requirements staleness check (REQ-STALE-002) in
   `sdd-requirements` stays on the shared corpus with **no** workstream key — only the
   research ID pattern changes to `RS-<WS>-NNN`. — traces to `ws-staleness.md`
   §Requirements-Corpus Staleness Stays Workstream-Independent (REQ-WS-028).
5. [verify] Confirm plan/implement/replan/verify scope staleness to a workstream's
   traced inputs (updating an untraced shared input does not flag; updating a traced
   one does); `sdd-specs` no longer compares a global `docs/plan.md`; requirements
   staleness fires independent of any workstream; no traceability-file read on any
   staleness path. — traces to `ws-staleness.md` §Verification/Automated + Manual.
**Entry criteria**: Chunk 0 complete.
**Exit criteria**: three skills generalized, two gain new/deferred branches,
requirements staleness confirmed shared; verify task passes.

### Chunk 4: Git integration model — fan-out & verification re-anchor
**Status**: CLOSED (2026-07-23) — tasks 1–4 done. Under a marker-`4` branch, integration
is branch-per-workstream → PR to `main` (workstream branch is the integration unit,
concurrent open PRs supported, `main` a shared trunk); implement-stage fan-out
(`skills/sdd-orchestrate/references/fan-out.md` §0 + SKILL.md §Execution Model) branches
worktrees from the **workstream branch** (HEAD), merges back into it, leaves `main`
untouched until the workstream PR, and the `main`-ownership "conflict = boundary error"
inference is **removed** (guaranteed-termination sequential fallback retained);
`sdd-verify`'s regression base is re-anchored to `merge-base(<ws>, main)` and the Chunk-3
"deferred to Chunk 4" forward pointer is now fully reconciled (no deferral framing left).
Marker-`3` `main`-anchored fan-out and `main`-HEAD regression base retained byte-unchanged
(gated additions only). The `**Depends on**: Chunk N` parser untouched. No replan trigger
fired. See Q-IMPL-014 in `ws-integration.md`. Covers REQ-WS-016, REQ-WS-017, REQ-WS-018.
**Depends on**: Chunk 0.
**Goal**: Integration is branch-per-workstream → PR to `main`; fan-out branches
from and merges back into the workstream branch; `sdd-verify` diffs against the
workstream branch point. Traces to `ws-integration.md`.
**Tasks**:
1. [implement] Encode branch-per-workstream → PR-to-`main` integration in the
   relevant skills/docs: the workstream branch is the integration unit; a completed
   workstream merges via PR; concurrent open PRs are supported; `main` is a shared
   trunk, not a working surface. — traces to `ws-integration.md` §Integration Is
   Branch-per-Workstream → PR to main (REQ-WS-016).
2. [implement] Re-anchor implement-stage fan-out in
   `skills/sdd-orchestrate/references/fan-out.md` (and any SKILL.md prose): worktrees
   branch from the **workstream branch** (HEAD), merge back into it, `main` untouched
   until the workstream PR; **remove** the `main`-ownership "conflict-after-
   re-derivation = boundary error" inference; keep all other fan-out mechanics
   (worktree provisioning, sequential merge-back, inline git identity, conflict
   abort-and-redo) unchanged. Apply the workstream-branch re-anchor as a **marker-`4`
   branch while retaining the marker-`3` (v3) `main`-anchored fan-out unchanged**:
   `docs/.sdd-version` is the sole gate — under marker `3` fan-out behaves exactly as
   today, marker `4` selects the workstream-branch path (reconciling with the
   `ws-layout.md` step-0 contract, where marker != 4 routes to the sdd-migrate / v3
   path). — traces to `ws-integration.md` §Fan-out Worktrees
   Branch from the Workstream Branch (REQ-WS-017).
3. [implement] Change `sdd-verify`'s regression base to the workstream branch point:
   `regression_base(<id>) = merge-base(<id>, main)`; diff `<id>` HEAD vs that base,
   not `main` HEAD, so verification reflects only this workstream's delta. Apply this
   re-anchored base as a **marker-`4` branch while retaining the marker-`3` (v3)
   `main`-HEAD regression base unchanged**: `docs/.sdd-version` is the sole gate — under
   marker `3` `sdd-verify` diffs against `main` exactly as today, marker `4` selects the
   `merge-base(<id>, main)` path (reconciling with the `ws-layout.md` step-0 contract,
   where marker != 4 routes to the sdd-migrate / v3 path). — traces to
   `ws-integration.md` §Verification Regression Base Is the Workstream Branch Point
   (REQ-WS-018).
4. [verify] Confirm fan-out branches worktrees from the workstream branch and merges
   back into it with no `main`-ownership step and no boundary-error inference; and
   `sdd-verify` computes regression base as `merge-base(<id>, main)` — a workstream's
   verification is unaffected by unrelated workstreams merged to `main` meanwhile. —
   traces to `ws-integration.md` §Verification/Automated + Manual.
**Entry criteria**: Chunk 0 complete.
**Exit criteria**: integration/fan-out/regression-base re-anchored onto the
workstream branch; boundary-error inference removed; verify task passes.

### Chunk 5: v3 → v4 migration & the `.sdd-version` gate
**Status**: CLOSED (2026-07-23) — tasks 1–6 done. `skills/sdd-migrate/SKILL.md` gains
§ v3 to v4 Migration: the `3`→`4` routing arm + `version==4` clean no-op composed after
the v1→v2→v3 chain (marker written `4` last, once, at v3→v4 Finalization); the
copy-verify-flip-cleanup step order (copy-not-move so the flat layout stays valid across
the whole marker-`3` window, byte-identity verify, marker flipped `4` LAST, idempotent
cleanup of flat originals + empty `docs/handoff/`); the interrupted-migration invariant
(before flip → working v3 + idempotent copy-verify re-run; after flip → working v4 +
idempotent cleanup re-run); the kickoff decision (`docs/ws/<id>/kickoff.md`, no flat
`docs/handoff/` in v4); and the `.sdd-version` sole-layout-gate table (3=flat, 4=per-ws).
Verified on a throwaway `$TMPDIR` git v3 fixture (byte-identical copies, marker-last, flat
layout authoritative at every pre-flip interruption point, clean idempotent cleanup, shared
corpus untouched, verdicts/status preserved verbatim). THIS repo was NOT migrated — marker
stays `3`, no `docs/ws/` created here. No replan trigger fired. See Q-IMPL-015 in
`ws-migration.md`. Covers REQ-WS-021, REQ-WS-022, REQ-WS-023.
**Depends on**: Chunk 1.
**Goal**: `sdd-migrate` gains a copy-verify-flip-cleanup v3→v4 step; `.sdd-version`
is the sole layout gate; kickoff is absorbed per-workstream. Traces to
`ws-migration.md`.
**Tasks**:
1. [implement] Add the `3`→`4` arm to `sdd-migrate`'s version routing
   (`migrate_v3_to_v4()`; `version == 4` → clean "already at v4" exit); compose it
   after the existing v1→v2→v3 chain so the marker is written `4` last, once. —
   traces to `ws-migration.md` §Version-Routing Extension, §.sdd-version Is the Sole
   Layout Gate (REQ-WS-023 routing half).
2. [implement] Specify the copy-verify-flip-cleanup step order: precondition marker
   `3`; create `docs/ws/default/` + `plan-history/`; **copy** (not move)
   `plan.md`/`verification.md`/`plan-history/*`/flat `handoff/kickoff.md` (if present)
   into `docs/ws/default/` preserving `[x]`/`[ ]` and pass/fail verdicts verbatim;
   **verify byte-identical**; leave the shared corpus in place; write `.sdd-version` =
   `4` **last**; then idempotently delete the flat originals (and empty
   `docs/handoff/`). — traces to `ws-migration.md` §v3→v4 Migration:
   Copy-Verify-Flip-Cleanup (REQ-WS-021, REQ-WS-022).
3. [implement] Encode the interrupted-migration invariant: interrupted **before** the
   flip → working v3 repo (marker `3`, flat files intact), re-run restarts idempotent
   copy-verify; interrupted **after** the flip → working v4 repo (marker `4`), re-run
   re-does cleanup idempotently. — traces to `ws-migration.md` (REQ-WS-022).
4. [implement] Encode the kickoff decision: `kickoff.md` lives at
   `docs/ws/<id>/kickoff.md`; flat `docs/handoff/` is **not** retained in v4 (moved to
   `docs/ws/default/kickoff.md` at migration); no skill reads `docs/handoff/` under
   marker `4`. — traces to `ws-migration.md` §Decision: kickoff.md Absorbed
   Per-Workstream (REQ-WS-021).
5. [implement] Document the `.sdd-version` gate table in `sdd-migrate` (and cross-check
   the Chunk 0 step-0 branches): marker `3` = flat authoritative, `4` = per-workstream
   authoritative; a v3 skill never reads `docs/ws/`, a v4 skill never reads flat
   execution paths; a v4-aware skill under marker `3` suggests `sdd-migrate`. — traces
   to `ws-migration.md` §.sdd-version Is the Sole Layout Gate (REQ-WS-023).
6. [verify] Run v3→v4 on a v3 fixture: confirm `docs/ws/default/` holds the former flat
   artifacts, `.sdd-version` == `4`, no flat `plan.md`/`verification.md`/`handoff/`
   remain, verdicts/status preserved verbatim; interrupt before flip → working v3 +
   safe re-run; interrupt after flip → working v4 + idempotent cleanup. — traces to
   `ws-migration.md` §Verification/Automated + Manual.
**Entry criteria**: Chunk 1 complete (sdd-migrate ID-remap template already carries
the `<WS>` slot).
**Exit criteria**: v3→v4 step + gate table + interrupted invariants + kickoff
absorption encoded; verify task passes.

### Chunk 6: Orchestration entry — workstream picker & uniform research lifecycle
**Status**: CLOSED (2026-07-23) — tasks 1–5 done. Under a marker-`4` branch,
`skills/sdd-orchestrate/SKILL.md` gains a § Workstream Picker: enumerate `docs/ws/<id>/`,
list each id + description (from `docs/ws/<id>/kickoff.md`) + detected phase (per the
Chunk-0 §Phase Detection gate with `ws=<id>`), and select-existing-or-create-new;
done-vs-new-cycle is resolved **per workstream** (DONE ws offers "start a new cycle in
this workstream"; a new idea mints a new ws id) — the §New cycle vs. resume block gains a
marker-`4` gate pointing at the picker instead of a single global operator intent. Every
**new** workstream begins at **research** (uniform research-entry, no per-ws mid-pipeline
variant) and seeds `docs/ws/<id>/kickoff.md`; §Entry Points is scoped to marker-`3`
single-cycle; §KICKOFF gains the per-ws kickoff path gate.
`skills/sdd-research/SKILL.md` gains a § Research Early-Exit (marker `4`): when the shared
corpus already covers the workstream's needs, record a fast `early_exit: true` finding
("covered by shared corpus — no new spike"), skip Explore/budget, update the index, and
advance — distinct from a full spike, a `should`. Marker-`3` single-flat-cycle entry
(flat `docs/handoff/kickoff.md`, global-intent done-vs-new-cycle, mid-pipeline entry)
retained UNCHANGED (all changes are marker-`4`-gated additions). No replan trigger fired.
See Q-IMPL-016..018 in `ws-orchestration.md`. Covers REQ-WS-024, REQ-WS-025, REQ-WS-029.
**Depends on**: Chunk 5.
**Goal**: `sdd-orchestrate` presents a workstream picker, every new workstream
starts at research, and research early-exits fast when the shared corpus already
covers the work. Traces to `ws-orchestration.md`.
**Tasks**:
1. [implement] Add the workstream picker at `sdd-orchestrate` entry: enumerate
   `docs/ws/<id>/` directories, show each id + description (from
   `docs/ws/<id>/kickoff.md`) + detected phase (per Chunk 0 detection); let the
   operator select an existing workstream or create a new one; in a `default`-only
   repo the picker degenerates to one (no naming ceremony). — traces to
   `ws-orchestration.md` §Workstream Picker at Orchestration Entry (REQ-WS-029).
2. [implement] Resolve done-vs-new-cycle ambiguity **per workstream**: a DONE
   workstream offers "start a new cycle in this workstream"; a new idea creates a new
   workstream id — not by appealing to a single global operator intent. — traces to
   `ws-orchestration.md` §Workstream Picker (REQ-WS-029).
3. [implement] Encode the uniform research-entry lifecycle: every new workstream
   begins at research and seeds `docs/ws/<id>/kickoff.md`; the id is conventionally the
   branch/issue key; no per-workstream mid-pipeline entry variant at creation. —
   traces to `ws-orchestration.md` §Uniform Research-Entry Lifecycle (REQ-WS-024).
4. [implement] Add the research early-exit path in `sdd-research`/`sdd-orchestrate`:
   when the shared corpus already covers the workstream's needs, record a fast explicit
   early-exit finding ("covered by shared corpus — no new spike") distinct from a full
   spike, then advance the loop. — traces to `ws-orchestration.md` §Research Early-Exit
   (REQ-WS-025).
5. [verify] Confirm the picker lists existing workstreams with id/description/phase and
   supports select-or-create (two workstreams at different phases both shown);
   done-vs-new-cycle resolves within the selected workstream; new-workstream creation
   positions the loop at research + seeds kickoff; research supports a recorded
   early-exit; `default`-only repo imposes no ceremony. — traces to
   `ws-orchestration.md` §Verification/Automated + Manual.
**Entry criteria**: Chunk 5 complete (kickoff placement + phase detection finalized).
**Exit criteria**: picker + per-ws done/new resolution + uniform research entry +
early-exit encoded; verify task passes.

### Chunk 7: Convention & documentation updates (overview.md + CLAUDE.md)
**Status**: CLOSED (2026-07-23) — tasks 1–3 done. The MANDATORY deferred `overview.md`
update is applied: §Version Marker now lists `4` as a valid value (+ sole-layout-gate
note; directory-layout comment and the Manual/Acceptance-Criteria lines that said "`2`
and `3`" updated to include `4`), and §ID Namespaces gains a `#### v4:
Workstream-Prefixed IDs` block adding the `<WS>` segment to the RS / REQ / Q-IMPL
formats (Q-IMPL row also added to the v2/v3 table) with the "applies under marker `4`;
legacy bare ids = `default`, not remapped" note. `overview.md` `last_updated` bumped to
2026-07-23; `status: Approved` retained (shipped-contract doc update within the cycle —
no re-approval gate crossed). `CLAUDE.md` now documents v4: the `docs/ws/<id>/` +
shared-corpus layout, the workstream lifecycle (picker → per-ws research→verify,
per-ws done/new-cycle, research early-exit), phase = f(repo, workstream) with a
marker-gated phase-detection table, workstream-scoped staleness, ws-prefixed IDs +
merge-safe writes, branch-per-ws → PR-to-`main` integration + `merge-base` regression
base, and the `.sdd-version` v3(flat)/v4(per-ws) gate with `sdd-migrate` handling
v3→v4 — v3 compatibility preserved throughout (both markers documented; the flat
phase-detection description this cycle relies on is retained). THIS repo's
`.sdd-version` stays `3`; no `sdd-*` SKILL.md behavior changed (docs/convention only).
No replan trigger fired. See Q-IMPL-019 in `ws-migration.md`. Covers REQ-WS-009
(§ID-namespace doc half), REQ-WS-023 (§Version-Marker doc half).
**Depends on**: Chunks 3, 4, 6.
**Goal**: The canonical convention docs describe v4; the mandatory deferred
`overview.md` update is applied. Traces to `ws-migration.md` §Deferred work,
`ws-layout.md` §Deferred work.
**Tasks**:
1. [implement] **(MANDATORY deferred task)** Update `docs/spec/overview.md` to v4:
   §Version Marker — add `4` as a valid marker value (currently lists only `2`/`3`);
   §ID Namespaces — add the `<WS>` workstream segment to the RS / REQ / Q-IMPL formats
   (currently the un-prefixed v2 formats). — traces to `ws-migration.md` §Deferred
   work and `ws-layout.md` §Deferred work (REQ-WS-023 §Version-Marker part, REQ-WS-009
   §ID-namespace part).
2. [implement] Update `CLAUDE.md` to document v4: the `docs/ws/<id>/` + shared-corpus
   layout and workstream lifecycle (research-entry → PR-to-main); the updated
   phase-detection and staleness tables ((repo, workstream) function; per-ws plan
   path); the workstream-prefixed ID formats; and the updated commit/branch
   conventions (branch-per-issue, PR-per-workstream, `docs/.sdd-version` = `4`). —
   traces to `ws-layout.md`, `ws-ids.md`, `ws-integration.md`, `ws-staleness.md`,
   `ws-migration.md` (documentation of the shipped v4 contract).
3. [verify] Confirm `overview.md` §Version Marker lists `4` and §ID Namespaces shows
   the `<WS>` segment for RS/REQ/Q-IMPL; `CLAUDE.md` describes the v4 layout,
   lifecycle, phase-detection/staleness, and commit/branch conventions consistently
   with the specs. — traces to `ws-migration.md` §Deferred work.
**Entry criteria**: Chunk 6 complete (all v4 contracts final so docs describe the
shipped state).
**Exit criteria**: overview.md v4 update applied; CLAUDE.md documents v4; verify
task passes.

### Chunk 8: Holistic v4 verification
**Status**: CLOSED (2026-07-23) — tasks 1–4 done. All spec acceptance criteria
exercised on throwaway `$TMPDIR` git fixtures (deleted; nothing leaked into this repo)
plus a cross-skill consistency sweep of the shipped skills. Two-workstream isolation
(ISSUE-42 plan rewrite+archive left ISSUE-57 byte-unchanged), concurrency (RS-ISSUE42-001
/ RS-ISSUE57-001 no collision; distinct-prefix index/category/per-ws-traceability additions
3-way-merge CLEAN; same-domain additions surface a human conflict, NOT auto-unioned;
aggregate re-derives deterministically byte-identical), workstream-scoped staleness
isolation (updating a spec traced only by ISSUE-42 flags ISSUE-42 not ISSUE-57; checker
reads no traceability file; requirements-corpus staleness stays ws-independent), v3→v4
migration (copy-verify-flip-cleanup: byte-identity, marker-`4` written LAST, interrupted-
before-flip = working v3 + idempotent re-run, verdicts/status verbatim), fan-out re-anchor
(worktrees branch from & merge back into the ws branch, `main` untouched; regression base
= merge-base(<ws>, main) = branch point, excludes unrelated `main` merges), and
v3-solo-safety (marker-`3` fixture = flat layout, global ids, no `docs/ws/`) all PASS. No
acceptance criterion failed; no replan trigger fired. THIS repo stays at marker `3`;
`docs/verification.md` NOT written (that is the sdd-verify stage). See Q-IMPL-020 in
`ws-layout.md`. Verifies REQ-WS-001..029 (holistic).
**Depends on**: Chunks 2, 3, 4, 7.
**Goal**: End-to-end confirmation that v4 behaves per every spec's acceptance
criteria across the whole skill set, from a user/operator perspective.
**Tasks**:
1. [verify] Two-workstream isolation walkthrough: create `ISSUE-42` and `ISSUE-57`;
   confirm each has independent `docs/ws/<id>/plan.md`; `requirements/`/`spec/` are
   single shared trees; running `sdd-plan` (incl. rewrite/archive) in `ISSUE-42`
   leaves `ISSUE-57`'s plan/plan-history/verification byte-unchanged and does not
   route it to replan. — traces to `ws-layout.md` acceptance criteria (REQ-WS-001,
   REQ-WS-006).
2. [verify] Concurrency walkthrough: two workstreams allocate `RS-ISSUE42-001` /
   `RS-ISSUE57-001` with no collision; add requirements under distinct prefixes
   (clean 3-way merge) vs same domain (surfaced human PR conflict, not auto-unioned);
   per-ws traceability files merge clean and the aggregate re-derives. — traces to
   `ws-ids.md` / `ws-traceability.md` acceptance criteria (REQ-WS-009, 011, 013, 014,
   008).
3. [verify] Solo-parity walkthrough: run a full solo cycle without ever naming a
   workstream; confirm all artifacts land under `docs/ws/default/`, the shared corpus
   is used as-is, and the experience is ceremony-free. — traces to `ws-layout.md`
   (REQ-WS-020) + `ws-orchestration.md` picker-degenerates-to-one (REQ-WS-029).
4. [verify] Cross-skill consistency sweep: confirm all nine skills' step-0, the four
   generators, the fan-out/verify integration, the migration gate, and the docs agree
   on the v4 layout/marker with no residual flat-path reads under marker `4`. —
   traces to `ws-layout.md`/`ws-migration.md` gate criteria (REQ-WS-003, REQ-WS-023).
**Entry criteria**: Chunk 7 complete.
**Exit criteria**: all spec acceptance criteria demonstrably met; ready for
`sdd-verify` / operator sign-off.

## Replan Triggers

- **Append-only merge proves unclean in a real `docs/ws/<id>/` layout** (contrary to
  RS-007 Q1 / S8) — e.g. per-ws traceability files or sorted index insertion still
  3-way-conflict in practice → revisit `ws-ids.md` / `ws-traceability.md` write model
  (Chunks 1–2), potentially reconsidering the rejected `merge=union` driver.
- **A skill's phase detection cannot be made workstream-parameterized without breaking
  v3 solo use** (Chunk 0) — e.g. the `default` fallback changes solo behavior
  observably → redesign the step-0 threading in `ws-layout.md`.
- **The milestone→workstream staleness generalization does not hold verbatim** for one
  of `sdd-plan`/`sdd-implement`/`sdd-replan` (contrary to RS-007 Q2) → treat that skill
  as needing new logic like verify/specs (Chunk 3).
- **v3→v4 copy-verify-flip-cleanup cannot preserve byte-identity or the interrupted
  invariant** on a real v3 repo (contrary to RS-007 Q3) → revisit the migration step
  order in `ws-migration.md` (Chunk 5).
- **The ID-format change touches a parser beyond the four generators + review string**
  (contrary to RS-007 Q4) — e.g. fan-out `Depends on: Chunk N` or a traceability parser
  actually regresses → expand Chunk 1 scope and re-derive the blast radius.
- **The workstream picker cannot resolve done-vs-new-cycle per workstream** without a
  global-intent appeal (Chunk 6) → revisit `ws-orchestration.md` entry design.

## Risks

- **Breadth of edits**: v4 touches all nine skills at step-0 plus references and two
  convention docs; a missed skill leaves a flat-path read under marker `4`. Mitigation:
  Chunk 0 does the step-0 threading in one pass; Chunk 8's cross-skill consistency
  sweep is a dedicated backstop.
- **Meta-feature testability**: there is no compiled code — "verification" is prose
  review + git merge/interruption walkthroughs on fixtures. Mitigation: verify tasks
  are explicit and behavioral (concurrent merges, migration interruption), not
  markdown lints.
- **Atomic flip coupling**: because `.sdd-version` = `4` flips everything at once,
  partial delivery is not shippable. Mitigation: single-milestone plan; the marker flip
  (Chunk 5) lands only after layout/IDs/staleness/integration are in place.
- **Same-domain concurrent requirement additions** remain a human PR conflict by design
  (REQ-WS-014) — not a defect. Mitigation: documented as accepted degradation, surfaced
  not auto-merged.

## Open Questions / Assumptions

- **Operator approval pending (status: Draft).** This plan was authored by a
  non-interactive pipeline subagent with no operator present. Per the sdd-plan Step 7/8
  flow, operator sign-off at the orchestration gate is required before implementation;
  `status` is left `Draft`. Default: proceed to the gate as-is.
- **Single-milestone structure.** v4 ships as one atomic delivery (the `.sdd-version`
  flip), so a single-milestone `docs/plan.md` with nine chunks was chosen over
  per-milestone files despite nearing the ~10-chunk soft threshold. Default: keep
  single-milestone; split into per-milestone files only if the operator wants staged
  delivery (which the atomic flip discourages).
- **`merge=union` `.gitattributes` driver (RS-007 Q1 / `ws-ids.md` Open Question).**
  Default: **not adopted** — it interleaves rows out of sort order, breaking the
  deterministic-sort invariant REQ-WS-015 relies on. Flagged for the operator to
  optionally reconsider at approval; would only enter scope via the Chunk 1 replan
  trigger.
- **Verify-task depth.** Verify tasks assume walkthroughs on throwaway git fixtures
  (as RS-007's Q1 spike did) rather than an automated harness, since the artifacts are
  markdown skill definitions. Default: fixture-based behavioral walkthroughs.
- **Chunk 0 breadth.** Threading step-0 through nine skills is one chunk for coherence;
  if it proves larger than ~15h in practice it may be split per-skill at implement time
  without changing the plan's dependency graph.

## Completed
- Chunk 0 (v4 layout foundation & phase-detection parameterization): marker-`4`
  workstream-aware step-0 threaded through all nine skills; shared-vs-owned +
  approval invariants and ws-scoped plan-archive/verify-fail-route encoded;
  marker-`3` v3 behavior retained unchanged (Q-IMPL-008). (2026-07-23, 5 tasks)
- Chunk 1 (Workstream-prefixed IDs & merge-safe shared writes): four generators
  (`sdd-research` `RS-<WS>-NNN`, `sdd-requirements` `REQ-<DOMAIN>-<WS>-NNN`,
  `sdd-implement` `Q-IMPL-<WS>-NNN`, `sdd-migrate` `<WS>`-slot template) + the
  `sdd-review` convention string emit/accept ws-prefixed ids with per-workstream
  counters under a marker-`4` branch; merge-safe shared-write model (claimed-prefix
  append, ID-sorted index insertion, new-specs-are-new-files, no-EOF-append,
  distinct-prefix precondition) encoded in `sdd-requirements`/`sdd-specs`; "do NOT
  touch" guards added to the four RS-007-Q4-unaffected parsers; marker-`3` v3
  generation and write behavior retained unchanged (Q-IMPL-009, Q-IMPL-010). Covers
  REQ-WS-009..015. (2026-07-23, 6 tasks)
- Chunk 2 (Traceability restructuring — per-workstream files + derived aggregate):
  under a marker-`4` branch, traceability rows are per-workstream-owned in
  `docs/ws/<ws>/traceability.md` (frontmatter + 6-column matrix with appended
  `Workstream` column; a workstream only edits its own rows), and the shared
  `docs/requirements/traceability.md` becomes a deterministically **regenerated**
  aggregate (shipped legacy rows under blank/`default` + concat of all per-ws files,
  stable-sorted by requirement id, wholesale replacement, never hand-merged). The four
  traceability writers (`sdd-requirements` row-add, `sdd-specs` Spec, `sdd-implement`
  Test/Impl + chunk-close Check 2, `sdd-verify` Verified) redirect writes to the per-ws
  file then regenerate the aggregate; the appended `Workstream` column preserves the
  REQ-WS-012 unchanged-parser guarantee; the recorded-join vs compute-live-staleness
  boundary is stated (no traceability read on any staleness path, no staleness schema
  column). Marker-`3` single-shared-file behavior retained unchanged (Q-IMPL-011,
  Q-IMPL-012). Covers REQ-WS-007, REQ-WS-008. (2026-07-23, 4 tasks)
- Chunk 3 (Workstream-scoped staleness): under a marker-`4` branch, staleness is
  scoped by workstream and computed **live** from the workstream's plan with **no
  traceability read** and no new schema column. The milestone-scoped traversal
  generalizes **verbatim** in `sdd-plan`/`sdd-implement`/`sdd-replan` (plan path
  `docs/plan.md` → `docs/ws/<ws>/plan.md`, milestone key → workstream key, chain
  `task → spec requires: → requirement IDs → category-file dates` unchanged;
  sdd-implement drops the now-inapplicable v3 plan-index caveat; sdd-replan re-points
  its by-name reference). `sdd-verify` and `sdd-specs`, which had no scoped branch,
  gain **new** ones: sdd-verify compares a workstream's plan/verification only against
  its traced shared inputs (same live plan-walk) + a Chunk-4 regression-base pointer
  (`merge-base(<ws>, main)`); sdd-specs stops treating the flat plan as a monolith and
  defers plan staleness to sdd-plan (checks only requirements→spec). `sdd-requirements`
  research→requirements staleness confirmed **workstream-independent** (shared corpus,
  no ws key; only research ID pattern → `RS-<WS>-NNN`). Marker-`3` milestone-scoped
  behavior retained unchanged; no replan trigger fired (Q-IMPL-013). Covers
  REQ-WS-026, REQ-WS-027, REQ-WS-028. (2026-07-23, 5 tasks)
- Chunk 4 (Git integration model — fan-out & verification re-anchor): under a
  marker-`4` branch, integration is branch-per-workstream → PR to `main` (the
  workstream branch — not `main` — is the integration unit; concurrent open PRs
  supported; `main` is a shared trunk, not a working surface — REQ-WS-016). Implement-stage
  fan-out is re-anchored in `skills/sdd-orchestrate/references/fan-out.md` (new §0 gate +
  §3a/§3b/§3c anchors) and `skills/sdd-orchestrate/SKILL.md` §Execution Model: worktrees
  branch from the **workstream branch** (HEAD) and merge back into it, `main` untouched
  until the workstream PR, and the `main`-ownership "conflict-after-re-derivation =
  boundary error" inference is **removed** (the guaranteed-termination sequential fallback
  is retained, just no longer labeled a boundary error) — all other fan-out mechanics
  unchanged (REQ-WS-017). `sdd-verify` Step 5 regression base is re-anchored to
  `regression_base(<ws>) = merge-base(<ws>, main)` (diff `<ws>` HEAD vs branch point, not
  `main` HEAD), and the Chunk-3 forward pointer that deferred this contract "to Chunk 4"
  is now fully reconciled — the deferral framing is gone (REQ-WS-018). Marker-`3`
  `main`-anchored fan-out and `main`-HEAD regression base retained byte-unchanged (all
  changes are marker-`4`-gated additions); the `**Depends on**: Chunk N` parser untouched.
  No replan trigger fired (Q-IMPL-014). Covers REQ-WS-016, REQ-WS-017, REQ-WS-018.
  (2026-07-23, 4 tasks)
- Chunk 5 (v3→v4 migration & the `.sdd-version` gate): `skills/sdd-migrate/SKILL.md`
  gains § v3 to v4 Migration — the `3`→`4` routing arm plus a `version==4` clean
  no-op, composed after the existing v1→v2→v3 chain so the marker is written `4`
  LAST, once (v2→v3's `3` write becomes the checkpoint satisfying v3→v4's marker-`3`
  precondition; Q-IMPL-015). The `migrate_v3_to_v4()` step order is copy-verify-flip-
  cleanup: **copy** (not move) `plan.md`/`verification.md`/`plan-history/*`/flat
  `handoff/kickoff.md` into `docs/ws/default/` (so the flat layout stays authoritative
  across the whole marker-`3` window), **verify** byte-identical (STOP-on-mismatch),
  leave the shared corpus (`requirements/`, `spec/`, `research/`, aggregated
  `traceability.md`) in place, write `.sdd-version` = `4` **LAST**, then idempotently
  delete the flat originals + empty `docs/handoff/`. The interrupted-migration
  invariant (before flip → working v3, idempotent copy-verify re-run; after flip →
  working v4, idempotent cleanup re-run), the kickoff absorption decision
  (`docs/ws/<id>/kickoff.md`; no flat `docs/handoff/` in v4; no skill reads
  `docs/handoff/` under marker `4`), and the `.sdd-version` sole-layout-gate table
  (3=flat authoritative, 4=per-ws authoritative; v3 skill never reads `ws/`, v4 skill
  never reads flat paths, v4-aware skill under marker `3` suggests `sdd-migrate`) are
  all encoded. Frontmatter description + two forward-reference notes updated to point
  at the now-present section; v1→v3 Composition renamed/extended to v1→v4. Verified on
  a throwaway `$TMPDIR` git v3 fixture; THIS repo was NOT migrated (marker stays `3`,
  no `docs/ws/` here). No replan trigger fired (Q-IMPL-015). Covers REQ-WS-021,
  REQ-WS-022, REQ-WS-023. (2026-07-23, 6 tasks)
- Chunk 6 (Orchestration entry — workstream picker & uniform research lifecycle):
  under a marker-`4` branch, `skills/sdd-orchestrate/SKILL.md` gains § Workstream
  Picker — at entry it enumerates `docs/ws/<id>/` and lists each workstream's id +
  description (from `docs/ws/<id>/kickoff.md`) + detected phase (Chunk-0 §Phase
  Detection with `ws=<id>`), then lets the operator select an existing workstream or
  create a new one; a `default`-only repo degenerates to a picker of one (no naming
  ceremony, REQ-WS-020). Done-vs-new-cycle is resolved **per workstream** (a DONE ws —
  `docs/ws/<id>/verification.md` `status: pass` — offers "start a new cycle in this
  workstream"; a new idea mints a new ws id), and the §New cycle vs. resume block gains
  a marker-`4` gate replacing the single global-operator-intent appeal with the picker
  (REQ-WS-029). Every **new** workstream begins at **research** (uniform research-entry,
  no per-ws mid-pipeline entry variant at creation — §Entry Points scoped to marker-`3`
  single-cycle) and seeds `docs/ws/<id>/kickoff.md` (§KICKOFF gains a per-ws kickoff
  path gate) (REQ-WS-024). `skills/sdd-research/SKILL.md` gains § Research Early-Exit
  (marker `4`): when the shared corpus already covers the workstream's needs, record a
  fast `early_exit: true` finding ("covered by shared corpus — no new spike"), skip
  Explore/budget (Steps 3–4), update the index, and advance the loop — recorded and
  distinct from a full spike, a `should` not a `must` (REQ-WS-025). Marker-`3`
  single-flat-cycle entry (flat `docs/handoff/kickoff.md`, global-intent
  done-vs-new-cycle, mid-pipeline entry, full spike) retained byte-unchanged (all
  changes marker-`4`-gated additions). No replan trigger fired (Q-IMPL-016, Q-IMPL-017,
  Q-IMPL-018). Covers REQ-WS-024, REQ-WS-025, REQ-WS-029. (2026-07-23, 5 tasks)
- Chunk 7 (Convention & documentation updates — overview.md + CLAUDE.md): the
  MANDATORY deferred `docs/spec/overview.md` update is applied — §Version Marker adds
  `4` as a valid value (+ sole-layout-gate note; the directory-layout comment and the
  Manual/Acceptance-Criteria lines that read "`2` and `3`" now include `4`), and §ID
  Namespaces gains a `#### v4: Workstream-Prefixed IDs` block adding the `<WS>` segment
  to the RS / REQ / Q-IMPL formats (with per-workstream counter, "applies under marker
  `4`", and "legacy bare ids = `default`, not remapped" notes); `last_updated` bumped to
  2026-07-23, `status: Approved` retained. `CLAUDE.md` documents the v4 convention: the
  `docs/ws/<id>/` + shared-corpus layout, the workstream lifecycle (picker → per-ws
  research→verify, per-ws done/new-cycle, research early-exit), phase = f(repo,
  workstream) via a marker-gated phase-detection table, workstream-scoped staleness,
  ws-prefixed IDs + merge-safe shared writes, branch-per-ws → PR-to-`main` +
  `merge-base(<id>, main)` regression base, and the `.sdd-version` v3(flat)/v4(per-ws)
  gate with `sdd-migrate` doing v3→v4 — presented as the current convention while
  retaining the v3 flat description this cycle depends on (both markers documented).
  THIS repo stays at marker `3`; no `sdd-*` SKILL.md behavior changed. No replan
  trigger fired (Q-IMPL-019). Covers REQ-WS-009 (§ID-namespace doc half), REQ-WS-023
  (§Version-Marker doc half). (2026-07-23, 3 tasks)
- Chunk 8 (Holistic v4 verification): end-to-end confirmation that v4 behaves per every
  spec's acceptance criteria, exercised on throwaway `$TMPDIR` git fixtures (all deleted;
  nothing leaked into this repo/branch) + a cross-skill consistency sweep of the shipped
  skills. **Fixture A** (two-workstream isolation + concurrency): an `sdd-plan`
  rewrite+archive in ISSUE-42 left ISSUE-57's plan/traceability byte-identical (hash-equal)
  and touched only ISSUE-42 paths (REQ-WS-001, 006); `RS-ISSUE42-001` / `RS-ISSUE57-001`
  allocated with no collision (REQ-WS-009, 011); distinct-domain-prefix additions to
  `requirements/index.md` (ID-sorted, one-row-per-line), new category files, and per-ws
  `traceability.md` files 3-way-merged CLEAN (REQ-WS-008, 010, 013, 014, 015); same-domain
  concurrent additions surfaced a git conflict, NOT auto-unioned (REQ-WS-014); the shared
  aggregate regenerated deterministically byte-identical and ID-sorted (REQ-WS-008).
  **Fixture B** (workstream-scoped staleness, REQ-WS-026, 027, 028, 007): a live
  `stale_inputs(<id>)` plan-walk flagged ISSUE-42 stale when a spec ONLY it traces changed
  and left ISSUE-57 untouched (and vice-versa for a traced category file); the checker read
  no `traceability.md`; research→requirements staleness stayed shared/ws-independent.
  **Fixture C** (v3→v4 migration, REQ-WS-021, 022, 023): copy-verify-flip-cleanup produced
  byte-identical copies under `docs/ws/default/`, wrote marker `4` LAST, preserved `[x]`/
  `[ ]` + pass verdicts verbatim, left the shared corpus in place; interrupted-before-flip
  = working v3 repo (flat files intact, marker `3`) with an idempotent safe re-run; re-run
  after flip = idempotent cleanup no-op. **Fixture D** (fan-out re-anchor, REQ-WS-016, 017,
  018): a fan-out worktree branched from & merged back into ISSUE-42 with `main` untouched;
  `regression_base = merge-base(ISSUE-42, main)` equalled the branch point and excluded an
  unrelated ISSUE-57 change merged to `main` meanwhile (diff-vs-main-HEAD would have wrongly
  folded it in). **Fixture E + sweep** (v3-solo-safety + cross-skill consistency, REQ-WS-003,
  004, 005, 012, 019, 020, 023, 024, 025, 029): a marker-`3` fixture behaved exactly as
  today (flat layout, global un-prefixed ids, no `docs/ws/`); all nine shipped skills carry
  a marker-`4` step-0 branch, the four generators emit ws-prefixed ids, `overview.md`/
  `CLAUDE.md` document v4, the `docs/ws/<ws>/requirements|spec` guards are all negative
  "never creates" prohibitions, and `overview.md` explicitly documents "a skill under marker
  `4` never reads flat `docs/plan.md`". No acceptance criterion failed; no replan trigger
  fired. THIS repo stays at marker `3`; `docs/verification.md` was NOT written (Chunk 8 is
  the plan's own holistic verify chunk, distinct from and preceding the sdd-verify stage).
  See Q-IMPL-020 in `ws-layout.md`. Verifies REQ-WS-001..029. (2026-07-23, 4 tasks)
