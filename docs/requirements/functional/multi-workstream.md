---
domain: WS
last_updated: 2026-09-18
status: Approved
research_refs: [RS-007, RS-HARNESSP3-001]
---

# Requirements: Multi-Workstream SDD

## Overview

Requirements for letting a team run several SDD cycles concurrently in one repo —
each on its own branch/issue ("a workstream") — without artifact collisions, false
staleness, ID races, or cross-workstream phase confusion, while keeping
requirements and specs a single shared product corpus and keeping solo use
ceremony-free.

Derived from the approved design
`docs/superpowers/specs/2026-07-21-multi-workstream-sdd-design.md` (10 decisions)
and research findings RS-007 (four resolved questions: merge-safe shared writes,
staleness generalization, v3→v4 migration safety, ID-format blast radius). The
core structural change is a **v4 layout**: execution artifacts move under
`docs/ws/<id>/` while `requirements/`, `spec/`, `research/`, and traceability
remain a shared corpus. Phase becomes a function of `(repo, workstream)` rather
than `repo`.

This domain scopes ONLY multi-workstream behavior. It intentionally keeps
compatibility and migration requirements under the `WS` prefix (rather than
touching `MIG`/`COMPAT` numbering) so the feature's requirements are cohesive and
concurrency-safe to add.

## Requirements

### Layout & Isolation

### REQ-WS-001: v4 per-workstream execution layout
The system must introduce a v4 artifact layout in which each workstream's
execution artifacts live under `docs/ws/<id>/` (`kickoff.md`, `plan.md`,
`plan-history/`, `verification.md`), while `docs/requirements/`, `docs/spec/`,
`docs/research/`, and the traceability matrix remain shared at their existing
top-level paths. The migrated/solo repo uses a reserved workstream id `default`.
[Priority: must]

Rationale: fixed singleton execution paths (`docs/plan.md`,
`docs/verification.md`) collide under concurrent use; scoping them by workstream
makes concurrency structural rather than conventional.

Acceptance: in a v4 repo, two workstreams `ISSUE-42` and `ISSUE-57` each have
independent `docs/ws/ISSUE-42/plan.md` and `docs/ws/ISSUE-57/plan.md`; no flat
`docs/plan.md` or `docs/verification.md` is read or written; `docs/requirements/`
and `docs/spec/` are single shared trees.

### REQ-WS-002: Branch-per-issue isolation boundary
Each workstream must correspond to its own git branch (branch-per-issue). Isolation
between concurrent workstreams must be provided by git branching plus the
per-workstream `docs/ws/<id>/` scoping, not by naming discipline within a single
branch.
[Priority: must]

Rationale: git already provides isolation and merge machinery; leaning on it
avoids ad-hoc hand-suffixed workaround files (e.g. the existing
`verification-rs002.md`).

Acceptance: opening a workstream creates/uses a dedicated branch; two workstreams'
execution artifacts never share a path on the same branch.

### REQ-WS-003: Phase detection is a function of (repo, workstream)
Every `sdd-*` skill's step-0 phase detection must take a workstream argument that
defaults to `default`, and must resolve the current phase from that workstream's
`docs/ws/<id>/` execution artifacts plus the shared corpus — not from
repo-global execution paths.
[Priority: must]

Rationale: today "the current phase" is a pure function of the shared repo, so one
workstream's state misroutes another's session.

Acceptance: with `ISSUE-42` at implement and `ISSUE-57` at plan, invoking a skill
against each id reports that id's phase; omitting the id resolves the `default`
workstream.

### Shared Corpus (Requirements & Specs)

### REQ-WS-004: Requirements and specs are a single common corpus
Requirements and specs must remain a single common product corpus shared across
all workstreams. New work must ADD to the shared requirement/spec sets; it must
never fork or copy them per workstream.
[Priority: must]

Rationale: one product has one requirement set and one spec set; per-workstream
copies would diverge and defeat traceability.

Acceptance: adding requirements/specs for a new workstream produces new IDs/files
within `docs/requirements/` and `docs/spec/`; no `docs/ws/<id>/requirements/` or
`docs/ws/<id>/spec/` directory is ever created.

### REQ-WS-005: A workstream is an execution unit referencing a shared subset
A workstream must be modeled as an execution unit that references a subset of the
shared requirements and specs via traceability — not as a copy of the docs. Its
scope (which shared REQ/SPEC it depends on) must be discoverable from
traceability.
[Priority: must]

Rationale: decouples "what the product requires" (shared) from "what this
execution unit is delivering" (scoped), which is also what bounds staleness
(REQ-WS-007).

Acceptance: given a workstream, one can enumerate the shared REQ/SPEC IDs it
traces to; requirements text stays product-wide with no workstream ownership
marker on the requirement itself.

### Workstream-Owned Execution Artifacts

### REQ-WS-006: A workstream owns only its execution artifacts
A workstream must own only `kickoff.md`, `plan.md`, `plan-history/`, and
`verification.md` under `docs/ws/<id>/`. Concurrent planning or verification in
one workstream must not archive, overwrite, or route the plan/verification of any
other workstream.
[Priority: must]

Rationale: the current `sdd-plan` archive-and-overwrite of the singleton
`plan.md`, and the single global `verification.md` pass/fail, cross-contaminate
unrelated sessions.

Acceptance: running `sdd-plan` (including a plan rewrite/archive) or a failing
`sdd-verify` in `ISSUE-42` leaves `ISSUE-57`'s `plan.md`/`plan-history/`/
`verification.md` byte-unchanged and does not route `ISSUE-57` into replan.

### Traceability as the Load-Bearing Join

### REQ-WS-007: Traceability is the load-bearing REQ→SPEC→workstream→verification join
Traceability must be the load-bearing join recording, for each workstream, which
shared REQ and SPEC it depends on through to its verification — the
coverage/derivation join across `REQ → SPEC → workstream → verification`. This
join is what logically defines the set of shared inputs a workstream cares about.
The staleness *computation* itself, however, must NOT read the traceability file:
it walks the workstream's plan `task → spec requires: → requirement` chain live —
the same logical join — to derive the scoped set of shared inputs whose updates
can make that workstream's plan/verification stale. Traceability is the recorded
coverage/derivation join; the live plan walk is how staleness scope is computed
(see REQ-WS-026).
[Priority: must]

Rationale: with requirements/specs shared and execution per-workstream, the
join is the only structure that says which workstream cares about which shared
input.

Acceptance: for a workstream, the exact shared REQ/SPEC set that scopes its
staleness is derived live by walking its plan's `task → spec requires: →
requirement` chain — with no traceability-file read — and coincides with the
coverage set the traceability join records for that workstream (REQ-WS-026).

### REQ-WS-008: Traceability rows are per-workstream-owned (merge-safe)
Traceability must be structured so each workstream owns its own rows, via either
(a) a per-workstream file `docs/ws/<id>/traceability.md` that a shared matrix
aggregates/regenerates deterministically, or (b) a delimited per-workstream
section in the shared file (`<!-- ws:<id> -->…<!-- /ws:<id> -->`) seeded at
workstream creation. Approach (a) is preferred because concurrent creation of two
new per-workstream sections in one shared file still conflicts, whereas separate
files never do. A workstream must only ever edit its own traceability rows.
[Priority: must]

Rationale: RS-007 Q1 proved a single hand-appended shared traceability table
conflicts on every concurrent append (every workstream appends rows). Per-ws
ownership removes the shared write point.

Acceptance: two concurrent workstreams each append their traceability rows and the
branches 3-way-merge with no conflict; the aggregated matrix (if used) is derived,
not hand-merged.

### Workstream-Prefixed IDs

### REQ-WS-009: Downstream IDs are workstream-prefixed
Downstream artifact IDs must carry a workstream segment: research
`RS-<WS>-NNN`, implement deviations `Q-IMPL-<WS>-NNN`, and new requirements
`REQ-<DOMAIN>-<WS>-NNN`. The `NNN` counter must be parsed AFTER the workstream
token.
[Priority: must]

Rationale: scan-and-increment allocation races across concurrent workstreams;
a per-workstream segment makes each counter independent and collision-free.

Acceptance: `RS-ISSUE42-001` and `Q-IMPL-ISSUE42-003` are valid; a generator
scanning for the next id parses the numeric suffix after the `ISSUE42` token.

### REQ-WS-010: New requirements append under a claimed prefix; new specs are new files
New requirements must be appended under a claimed domain prefix (recorded in the
requirements index prefix registry), and new specs must be new files in
`docs/spec/` — never edits to existing spec files. Modifying an existing shared
requirement or spec remains a human PR-conflict to resolve and is not automated.
[Priority: must]

Rationale: append-only new-file/new-row writes 3-way-merge cleanly (REQ-WS-013);
in-place edits to shared artifacts are the genuinely conflicting case and are left
to human resolution (design decision #6, out-of-scope for automation).

Acceptance: a workstream adding design lands a new `docs/spec/<name>.md`; adding
requirements lands new `REQ-<DOMAIN>-<WS>-NNN` IDs under a registered prefix; no
existing spec file body is rewritten by the tooling.

### REQ-WS-011: Per-workstream ID counters
ID generators must scope their max-scan per workstream (and, for requirements, per
domain+workstream), so each workstream advances an independent counter. This must
replace the global "scan the whole tree, take max, +1" allocation.
[Priority: must]

Rationale: independent counters eliminate the cross-workstream allocation race at
its root, not just its symptom.

Acceptance: two workstreams concurrently allocate `RS-ISSUE42-001` and
`RS-ISSUE57-001` without coordination or collision.

### REQ-WS-012: ID-format change touches exactly the four generators plus one convention string
The workstream-prefixed ID format must update exactly four scan-increment
generators — `sdd-research`, `sdd-requirements`, `sdd-implement`, `sdd-migrate` —
and one convention-validation string in `sdd-review`. It must NOT break fan-out's
`Depends on: Chunk N` derivation, traceability/requirements row parsing, or the
`sdd-review` Q-REQ/Q-SPEC/Q-IMPL content checks, which use a separate namespace or
opaque/prefix-glob matching.
[Priority: must]

Rationale: RS-007 Q4 exhaustively bounded the blast radius; over-touching parsers
risks regressions in fan-out and review that are provably unaffected.

Acceptance: after the change, `### Chunk N:` parsing, traceability row matching,
and the Q-REQ/Q-SPEC/Q-IMPL checks operate unchanged against ws-prefixed IDs;
`sdd-review`'s convention check accepts the ws segment rather than flagging it.

### Merge-Safe Shared-Corpus Writes

### REQ-WS-013: Shared-corpus writes must be merge-safe, never tail-append
All writes to shared-corpus table artifacts must be merge-safe: either
sorted-insertion into distinct, non-adjacent regions, or per-workstream-owned
rows/files. Naive append-to-EOF (or insert-before-a-trailing-sentinel) must not be
used for any shared table.
[Priority: must]

Rationale: RS-007 Q1 empirically proved that append-to-EOF is the same git
location for both branches and always conflicts, regardless of row content; only
distinct-region or owned-region writes merge cleanly.

Acceptance: concurrent shared-table writes by two workstreams that target distinct
regions (or owned regions/files) 3-way-merge with no conflict; no skill's write
path performs a raw EOF append to a shared table.

### REQ-WS-014: Distinct-domain-prefix precondition for clean index merges
The clean-merge guarantee for `docs/requirements/index.md` new rows must be stated
as conditional on each concurrent workstream owning a DISTINCT claimed domain
prefix (so their new IDs sort into distinct, non-adjacent regions). Same-domain
concurrent additions are an accepted degradation to an ordinary human PR conflict,
not something the tooling must auto-merge.
[Priority: must]

Rationale: RS-007 Q1 proved sorted insertion merges cleanly only when the new IDs
sort to non-adjacent regions; same/adjacent regions conflict. The design already
accepts same-domain concurrency as a human PR conflict (decision #6).

Acceptance: two workstreams adding requirements under distinct prefixes merge
clean; two adding under the same domain concurrently surface a human-resolvable
conflict and the tooling does not attempt to silently union them.

### REQ-WS-015: requirements/index.md uses ID-sorted one-row-per-line insertion
Additions to `docs/requirements/index.md` (Files table, Domain Prefixes table, and
new requirement rows within a category file) must be inserted at the correct
sorted position, one row per line, rather than appended at EOF, to keep the sort
deterministic and merges clean under the REQ-WS-014 precondition.
[Priority: must]

Rationale: deterministic sorted insertion is what places concurrent additions in
distinct regions (RS-007 Q1 recommendation 2/3).

Acceptance: a new domain prefix row is inserted in sorted position; the table stays
one row per line; a concurrent distinct-prefix addition merges without conflict.

### Git Integration Model

### REQ-WS-016: Integration is branch-per-workstream → PR to main
Each workstream must integrate by opening a pull request from its branch to
`main`. The workstream branch — not `main` — is the integration unit for that
workstream's whole cycle.
[Priority: must]

Rationale: PR-per-workstream keeps `main` free of any single workstream's
exclusive ownership and matches the branch-per-issue boundary (REQ-WS-002).

Acceptance: a completed workstream is merged to `main` via PR; two workstreams can
have open PRs simultaneously.

### REQ-WS-017: Fan-out worktrees branch from the workstream branch
Implement-stage fan-out worktrees must branch from the WORKSTREAM branch (not from
`main`) and merge back into the workstream branch. Fan-out must no longer take
exclusive ownership of `main`, and the "conflict-after-re-derivation = boundary
error" inference tied to `main`-ownership must be removed.
[Priority: must]

Rationale: with per-workstream branches, `main` is not the fan-out integration
point; branching fan-out from the workstream branch keeps parallel implement work
inside the workstream's isolation.

Acceptance: a fan-out run in `ISSUE-42` creates worktrees branched from the
`ISSUE-42` branch and merges them back into `ISSUE-42`, leaving `main` untouched
until the workstream PR.

### REQ-WS-018: Verification regression base is the workstream branch point
`sdd-verify` must compute its regression diff against the workstream branch point,
not against `main`. A workstream's verification must reflect only that
workstream's changes.
[Priority: must]

Rationale: diffing against `main` would fold in unrelated concurrent workstreams'
merged changes, producing false regressions.

Acceptance: `sdd-verify` for `ISSUE-42` reports regressions relative to where
`ISSUE-42` branched, independent of other workstreams merged to `main` meanwhile.

### Approval Scoping

### REQ-WS-019: Approval is a per-workstream bare status flag
Approval must remain a bare `status` flag, scoped per workstream where the artifact
is workstream-owned (plan, verification) and per shared artifact where the corpus
is shared (requirements, specs). No approver identity, signature, or quorum is
recorded.
[Priority: must]

Rationale: identity/quorum is explicitly out of scope (design decision #8, YAGNI);
a bare status flag is sufficient for the single-operator-per-workstream model.

Acceptance: a workstream's plan/verification carries only a `status` value; no
approver field exists; one workstream's approval status does not gate another's.

### Compatibility, Migration & Solo Use

### REQ-WS-020: Solo use runs in an implicit ceremony-free default workstream
Solo (single-operator) use must run in an implicit `default` workstream and feel
unchanged: the operator must not be required to name a workstream, and the skills
must default the workstream argument to `default` throughout.
[Priority: must]

Rationale: the feature must not tax the common single-operator case with
multi-workstream ceremony (design decision #9).

Acceptance: a solo operator runs a full cycle without ever specifying a workstream
id; all artifacts land under `docs/ws/default/` and the shared corpus.

### REQ-WS-021: sdd-migrate gains a v3→v4 migration step
`sdd-migrate` must gain a v3→v4 migration that moves the flat execution artifacts
(`docs/plan.md`, `docs/verification.md`, `docs/plan-history/`, and a flat
`docs/handoff/kickoff.md` if present) into `docs/ws/default/`, leaving the shared
corpus (`docs/requirements/`, `docs/spec/`, `docs/research/`, traceability) in
place, and set `docs/.sdd-version` to `4`.
[Priority: must]

Rationale: v4 is a one-time layout change; migration is how existing v3 repos adopt
it (design decision #9). Dual-layout-forever support is out of scope.

Acceptance: running the v3→v4 migration on a v3 repo yields `docs/ws/default/`
containing the former flat artifacts, `.sdd-version` = `4`, and no remaining flat
`docs/plan.md`/`docs/verification.md`.

### REQ-WS-022: v3→v4 migration is copy-verify-flip-cleanup with the version marker written last
The v3→v4 migration must COPY (not move) execution artifacts into
`docs/ws/default/`, VERIFY them byte-identical (preserving task `[x]`/`[ ]` status
and pass/fail verdicts verbatim), then write `docs/.sdd-version` = `4` LAST as the
single atomic layout gate, then delete the now-orphaned flat originals as
idempotent cleanup. If interrupted, re-running must detect the marker and resume
safely.
[Priority: must]

Rationale: RS-007 Q3 — while the marker still reads `3`, v3 skills must still find
the flat files, so the flat layout must stay valid across the whole `3` window;
copy-then-delete (the one deviation from prior move-based migrations) preserves the
"version marker written last" interrupted-migration invariant.

Acceptance: interrupting the migration before the flip leaves a working v3 repo
(flat files intact, marker `3`); interrupting after the flip leaves a working v4
repo and re-running completes cleanup idempotently.

### REQ-WS-023: .sdd-version is the sole layout gate
`docs/.sdd-version` must be the single switch selecting which layout every skill's
step-0 reads: `3` means flat execution artifacts are authoritative
(`docs/plan.md`, `docs/verification.md`); `4` means per-workstream execution
artifacts are authoritative (`docs/ws/<id>/{plan,verification,kickoff}.md`, default
ws `default`) with `requirements/`, `spec/`, `research/`, and traceability as the
shared corpus. A v3 skill must never read `ws/`; a v4 skill must never read flat
execution paths.
[Priority: must]

Rationale: RS-007 Q3 — a single marker gating the layout guarantees no skill
misdetects phase during or after migration.

Acceptance: with marker `3`, skills read flat paths and a v4-aware skill suggests
migration; with marker `4`, skills read `docs/ws/<id>/` and never the flat paths.

### Research Entry (Uniform)

### REQ-WS-024: Every new workstream starts at research
For uniformity, every new workstream must begin at the research stage, regardless
of how much shared corpus already exists.
[Priority: must]

Rationale: a single uniform entry point keeps the workstream lifecycle simple and
predictable (design decision #10).

Acceptance: creating a new workstream positions its loop at research; there is no
per-workstream mid-pipeline entry variant to select at creation.

### REQ-WS-025: Research early-exits when the shared corpus already covers the work
The research stage should early-exit quickly when the shared corpus already covers
the workstream's needs, so that starting at research (REQ-WS-024) imposes minimal
overhead when little or no new exploration is required.
[Priority: should]

Rationale: uniform research-entry must not become busy-work; the fast early-exit is
what makes uniformity cheap (design decision #10).

Acceptance: a workstream whose needs are already covered passes through research
with a fast, recorded early-exit rather than a full spike.

### Staleness Scoping

### REQ-WS-026: Generalize milestone-scoped staleness to workstream scope (compute-live)
The existing milestone-scoped staleness traversal in `sdd-plan`, `sdd-implement`,
and `sdd-replan` must be generalized to a workstream key by swapping the plan path
(`docs/plan.md` → `docs/ws/<id>/plan.md`) and the milestone key for a workstream
key, keeping the `task → spec requires: → requirement IDs → category-file dates`
chain unchanged. Staleness scope must be computed live from the workstream's plan
(RS-007 Q2 Option A) with NO new traceability schema column.
[Priority: must]

Rationale: RS-007 Q2 showed the milestone traversal generalizes verbatim and needs
no schema change; computing live is the lowest-cost option.

Acceptance: `sdd-plan`/`sdd-implement`/`sdd-replan` in `ISSUE-42` scope staleness to
the specs/requirements that `ISSUE-42`'s plan traces, ignoring updates to shared
inputs no `ISSUE-42` task references; no traceability column is added for this.

### REQ-WS-027: New per-workstream staleness branches for sdd-specs and sdd-verify
`sdd-specs` and `sdd-verify`, which today have no scoped staleness branch, must gain
new per-workstream-scoped staleness logic (using the milestone traversal as the
template): `sdd-verify` must compare a workstream's plan/verification only against
the shared specs/requirements that workstream traces, and `sdd-specs` must stop
treating the flat plan as a monolith (defer plan staleness to `sdd-plan` or gain a
per-workstream branch).
[Priority: must]

Rationale: RS-007 Q2 identified these two skills as the ones needing NEW logic
because specs are now shared and plans are per-workstream.

Acceptance: `sdd-verify` for a workstream does not report staleness from shared
input changes outside that workstream's traced set; `sdd-specs` no longer flags
staleness against a global `docs/plan.md`.

### REQ-WS-028: Requirements-corpus staleness stays workstream-independent
The research→requirements staleness check (REQ-STALE-002) must remain on the shared
corpus and must NOT be scoped by workstream. Only the research ID pattern changes
if research becomes workstream-prefixed.
[Priority: must]

Rationale: RS-007 Q2 — requirements are shared product-wide, so their staleness is
not a per-workstream concern.

Acceptance: updating shared research triggers the shared requirements staleness
check independent of any workstream; no workstream key is applied to it.

### Orchestration Entry Picker

### REQ-WS-029: Workstream picker at orchestration entry
`sdd-orchestrate` must present a workstream picker at entry that lists existing
workstreams (id, description from `kickoff.md`, and detected phase) and lets the
operator select an existing workstream or create a new one, and it must resolve the
done-vs-new-cycle ambiguity per workstream rather than by appealing to a single
operator's global intent.
[Priority: should]

Rationale: with phase now a function of `(repo, workstream)`, the driver can no
longer infer a single active cycle from the repo; an explicit picker disambiguates
which workstream the operator is driving.

Acceptance: at entry the operator sees each workstream with its phase and can pick
or create; selecting a DONE workstream vs. bringing a new idea is disambiguated
within that workstream's context, not globally.

### REQ-WS-030: Offer migration when the project is behind the latest version
On entry, `sdd-orchestrate` must compare `docs/.sdd-version` to the latest version
the installed skills support and, whenever the project's marker is **behind** that
latest (missing/pre-versioning, `2`, or `3`), present an **informational, non-forcing
offer** to run `sdd-migrate` first before proceeding with the cycle. The offer must
generalize to any behind-version case, not only v3→v4. If the operator declines (or
the session is non-interactive), the driver proceeds on the current marker with
downstream behavior unchanged; if the marker already equals the latest, no offer is
shown.
[Priority: should]

Rationale: found during dogfooding — entering a v3 project ran a v3 cycle without
mentioning that a v4 upgrade was available, so a behind-version project could stay on
the old layout purely because nothing surfaced the option. A one-time entry offer
makes the upgrade discoverable without forcing it, preserving the v3-solo-safety
guarantee for anyone who declines. This intentionally softens the strict
"marker-`3` entry emits no v4 output" reading of the driver's "behavior UNCHANGED"
entry clauses with a single, benign, decline-able notice; declining changes no cycle
mechanics.

Acceptance: entering a repo whose `.sdd-version` is behind the latest supported
version surfaces a migrate offer that routes to `sdd-migrate` on accept and proceeds
unchanged on decline; entering a repo already at the latest version surfaces no
offer.

### REQ-WS-HARNESSP3-001: The orchestrator owns aggregate-traceability regeneration for orchestrated dispatches
Regeneration of the shared `docs/requirements/traceability.md` must belong to
the **orchestrator**, in its own post-gate bookkeeping commit, for every
orchestrated dispatch — resolving the standing inconsistency between
`docs/spec/ws-traceability.md` Q-IMPL-011 (every writing skill regenerates the
aggregate immediately after its per-ws write: `sdd-requirements`, `sdd-specs`,
`sdd-implement` including chunk-close Check 2, and `sdd-verify`) and
`references/fan-out.md` §3e (the orchestrator regenerates at merge). Adopting it
means (i) dropping `docs/requirements/traceability.md` from the leaf default
write scopes for orchestrated dispatches, (ii) adding a post-gate orchestrator
bookkeeping step and a separate commit beside fan-out §3e's, and (iii) **keeping
Q-IMPL-011's behaviour for standalone, non-orchestrated skill runs**, so the
aggregate does not go stale when someone invokes a single `sdd-*` skill outside
the harness.

**Regeneration trigger — every gate outcome, before the session ends.** Moving
the regeneration behind the gate must not let a non-`proceed` outcome leave the
shared aggregate stale: today the leaf regenerates inline, so a stopped or
looped-back stage still leaves the aggregate consistent. The orchestrator must
therefore run the regeneration **on every gate outcome — `proceed`,
`loop-back-to-fix` and `stop` alike — and before the session ends**, not only on
`proceed`. Concretely: after any gate at which a leaf wrote per-ws traceability
rows since the last regeneration, the orchestrator regenerates and commits, so
the aggregate is consistent with the per-ws files at every point an operator
could walk away. Within a fix loop this means one regeneration per gate, each
superseding the last (regeneration is wholesale and idempotent, so repeating it
costs nothing and never compounds).

**Discriminator — decided, not left open.** The dispatched `{write_scope}` slot
**is** the signal; no new flag, field or schema is added. A writing skill
regenerates the aggregate after its per-ws write **unless it was dispatched with
a write scope that omits that path**, in which case the regeneration is the
orchestrator's. Under item (i) the orchestrated leaf scopes omit the path by
construction, so its absence from `{write_scope}` *is* the orchestrated signal
and its presence — or the absence of any dispatched scope at all — *is* the
standalone signal. A skill therefore never has to know **who** invoked it, only
what it was scoped to write. The alternative considered and **not** adopted is an
explicit instruction line in the PIPELINE template body: more legible, but it
adds text to every dispatch, and the slot-based signal already exists. (see
RS-HARNESSP3-001 Q7(b) — the inconsistency is spec-read from two committed texts
that disagree and needs no run; which side wins and the discriminator are
**constructed** judgements ratified here. The spike flagged this as larger than
the pilot expected — ~7 files, not a one-line table edit — and required
requirements to close the discriminator one way or the other, because adopting
the split without naming a signal leaves the two regeneration rules silently
contradictory)
**Acceptance**: `docs/spec/ws-traceability.md` Q-IMPL-011 carries the
orchestrated/standalone split stated against `{write_scope}`;
`references/write-scope.md` §2 leaf rows omit `docs/requirements/traceability.md`
and §7's commit-ownership table assigns the regeneration to the orchestrator;
`references/fan-out.md` §3e cross-references the same rule; the marker-4
traceability notes in `sdd-requirements`, `sdd-specs`, `sdd-implement` and
`sdd-verify` state the unless-clause. A walkthrough of an orchestrated dispatch
shows the aggregate regenerated in a separate orchestrator commit and the leaf's
`files_written` containing no aggregate path; a standalone run of the same skill
regenerates the aggregate itself. A walkthrough of a gate resolved `stop`, and of
one resolved `loop-back-to-fix`, each shows the aggregate regenerated and
committed before the session ends — the aggregate is never left inconsistent
with the per-ws files by a non-`proceed` outcome.
[Priority: must]

## Open Questions / Assumptions

- **Requirements status is `Approved`.** This domain was originally authored by a
  non-interactive pipeline subagent and left at `Draft` pending operator
  sign-off; the operator approved it at the orchestration gate, and both this
  file's frontmatter and `index.md` now read `Approved`. Recorded here so the
  earlier "approval pending" note is not mistaken for the current state.

- **Traceability structure choice (RS-007 Q1/Q2, Assumption).** REQ-WS-008 permits
  either per-workstream files (preferred) or delimited per-workstream sections;
  REQ-WS-026 mandates compute-live staleness (Option A) with NO new traceability
  column. Default carried forward: adopt Option A (no schema column); pick the
  concrete per-ws traceability structure (separate file vs delimited section) at
  the specs stage. Recorded so specs decide the exact shape, not requirements.

- **kickoff.md placement at migration (RS-007 Q3, Assumption).** A flat
  `docs/handoff/kickoff.md`, if present at v3→v4 migration, maps to
  `docs/ws/default/kickoff.md` (REQ-WS-021). Whether a flat `docs/handoff/` is
  retained for the orchestrator's active-cycle handoff or fully absorbed per-ws is
  left for specs to confirm; default is per-workstream absorption.

- **Union merge driver (RS-007 Q1, Assumption).** A `merge=union` `.gitattributes`
  driver on the shared table files is a possible belt-and-suspenders mitigation not
  spiked. Default: do NOT rely on `union` (it can interleave rows unsorted); prefer
  the structural fix in REQ-WS-013/015. Flagged for specs to optionally consider.

- **File size vs. 300-line guideline (REQ-CTX-001).** This file exceeds the
  300-line soft guideline because the feature carries 29 requirements each with
  rationale + acceptance. The deliverable contract pins a single WS category file
  and no operator was present to approve a split. Default: keep one cohesive file;
  a future split (e.g. layout/IDs vs. staleness/migration) can be proposed at
  operator approval if desired.

## Out of Scope

- Approver identity, signature, or quorum (REQ-WS-019 keeps a bare status flag).
- Any locking daemon or coordination server — git is the coordination substrate.
- Dual-layout-forever support — migrate once (v3→v4), then v4 only.
- Automating merges of modifications to EXISTING shared requirements/specs — those
  stay human PR conflicts (REQ-WS-010, REQ-WS-014).
