---
status: Approved
last_updated: 2026-09-19
requires:
  - REQ-WS-024
  - REQ-WS-025
  - REQ-WS-029
---

# Multi-Workstream Orchestration Entry & Research Lifecycle

## Context

Under v4, phase is a function of `(repo, workstream)` (`ws-layout.md`), so
`sdd-orchestrate` can no longer infer a single active cycle from the repo — it must ask
which workstream the operator is driving. Separately, the workstream lifecycle needs a
uniform entry point: RS-007 and the design fixed every workstream to begin at research,
with a fast early-exit so uniform research-entry stays cheap.

This spec covers the orchestrate workstream picker (REQ-WS-029) and the uniform
research-entry lifecycle with early-exit (REQ-WS-024, REQ-WS-025).

## Design

### Workstream Picker at Orchestration Entry (REQ-WS-029)

`sdd-orchestrate` presents a **workstream picker** at entry that lists existing
workstreams and lets the operator select one or create a new one.

For each existing workstream (one `docs/ws/<id>/` directory each), the picker shows:

| Field | Source |
|-------|--------|
| id | the `docs/ws/<id>/` directory name |
| description | from `docs/ws/<id>/kickoff.md` (per `ws-migration.md` decision, kickoff is per-workstream) |
| detected phase | phase detection for that workstream (`ws-layout.md` REQ-WS-003) |

Behavior:
- The operator selects an existing workstream **or** creates a new one.
- The **done-vs-new-cycle ambiguity is resolved per workstream**, not by appealing to a
  single operator's global intent. Selecting a workstream whose detected phase is DONE
  (verified/shipped) vs. bringing a new idea is disambiguated **within that
  workstream's context** — a DONE workstream offers "start a new cycle in this
  workstream" while a new idea creates a new workstream id.

**Why an explicit picker**: with phase now `(repo, workstream)`, the driver cannot infer
a single active cycle from the repo — several may be live at once. An explicit picker
surfaces each workstream with its phase so the operator names the one they are driving,
rather than the driver guessing. This is the orchestration-level counterpart to
threading the workstream argument through each skill's step-0.

**Interaction with solo use**: in a repo with only `default`, the picker degenerates to
that single workstream (no naming ceremony — consistent with REQ-WS-020). It is a picker
of one, not a prompt the solo operator must answer.

### Uniform Research-Entry Lifecycle (REQ-WS-024)

Every new workstream **begins at the research stage**, regardless of how much shared
corpus already exists. There is no per-workstream mid-pipeline entry variant to select
at creation.

- Creating a new workstream positions its loop at research and seeds
  `docs/ws/<id>/kickoff.md`.
- The workstream id is conventionally the branch/issue key; the branch is created/used
  per `ws-integration.md`.

**Why a single uniform entry point**: it keeps the workstream lifecycle simple and
predictable — one shape for every workstream — rather than a matrix of entry variants
the operator must choose among at creation.

### Research Early-Exit When the Shared Corpus Already Covers the Work (REQ-WS-025)

The research stage **early-exits quickly** when the shared corpus already covers the
workstream's needs, so uniform research-entry (REQ-WS-024) imposes minimal overhead when
little or no new exploration is required.

Contract:
- On entry at research for a workstream whose needs are already covered by existing
  shared requirements/specs/research, the stage records a **fast, explicit early-exit**
  (a recorded finding of "covered by shared corpus — no new spike") rather than
  performing a full spike.
- The early-exit is recorded (so the workstream's research state is auditable), then the
  loop advances to the next stage.

**Why the early-exit is `should`, not `must`**: uniform research-entry must not become
busy-work. The fast early-exit is what makes uniformity cheap. It is a `should` because a
workstream is always free to run a real spike; the early-exit is the optimization that
keeps the common "already covered" case near-zero-cost, not a hard gate.

**Interaction with staleness**: whether the shared corpus "covers" the work is a
judgment recorded at the research early-exit; ongoing staleness of the shared inputs a
workstream traces is handled separately and live (`ws-staleness.md`).

### Migration Offer When the Project Is Behind the Latest Version (REQ-WS-030)

On entry, before deriving loop position, the driver compares `docs/.sdd-version` to the
latest version the installed skills support (currently `4` — the highest `sdd-migrate`
can reach) and, whenever the marker is **behind** that latest, offers migration.

Contract:
- **Trigger**: `docs/.sdd-version` is missing/pre-versioning, `2`, or `3` — i.e. any
  value behind the latest supported version. The check is `detected < latest`, so it
  generalizes to future versions (not hard-coded to v3→v4).
- **Form**: an **informational, non-forcing** offer to run `sdd-migrate` first. It is the
  single place a behind-version project is nudged toward the upgrade.
- **Accept** → hand off to `sdd-migrate` (migrates up through the latest), then re-derive
  phase from the migrated layout and continue.
- **Decline / non-interactive** → proceed on the current marker with downstream behavior
  **unchanged**. The offer alters no cycle mechanics, so the marker-`3` "behavior
  UNCHANGED" guarantees elsewhere still hold for anyone who does not migrate.
- **Already latest** → no offer; continue silently.

**Relationship to v3-solo-safety**: this is a deliberate, minimal departure from the
strict "marker-`3` entry emits no v4 output" reading — a single decline-able notice makes
the upgrade discoverable without forcing it. Declining preserves the unchanged v3 cycle
exactly.

## Verification

### Automated
- Verify `sdd-orchestrate` enumerates `docs/ws/<id>/` directories and, for each, reads
  the description from `docs/ws/<id>/kickoff.md` and computes detected phase.
- Verify new-workstream creation positions the loop at research and seeds
  `docs/ws/<id>/kickoff.md`.
- Verify the research stage supports a recorded early-exit path distinct from a full
  spike.

### Manual
- With `ISSUE-42` at implement and `ISSUE-57` at plan, enter `sdd-orchestrate`; confirm
  the picker lists both with id, description, and phase, and lets the operator pick or
  create.
- Select a DONE workstream vs. bring a new idea; confirm the done-vs-new-cycle choice is
  resolved within the selected workstream's context, not globally.
- Create a workstream whose needs the shared corpus already covers; confirm research
  early-exits fast with a recorded exit rather than a full spike.
- In a `default`-only repo, confirm the picker does not impose naming ceremony.

### Acceptance Criteria
- [ ] `sdd-orchestrate` presents a workstream picker listing existing workstreams (id,
      description from kickoff.md, detected phase) with select-or-create (REQ-WS-029)
- [ ] done-vs-new-cycle ambiguity resolved per workstream, not by global operator intent
      (REQ-WS-029)
- [ ] Every new workstream begins at research; no per-workstream mid-pipeline entry
      variant (REQ-WS-024)
- [ ] Research early-exits fast with a recorded exit when the shared corpus already
      covers the work (REQ-WS-025)
- [ ] Markdown well-formed; frontmatter valid

## Implementation Questions

### Q-IMPL-016: Picker & uniform-lifecycle changes are marker-`4`-gated [superseded by Q-IMPL-072]
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Workstream Picker at Orchestration Entry; §Uniform Research-Entry Lifecycle
**Decision**: The workstream picker, per-workstream done-vs-new-cycle resolution,
uniform research-entry, and research early-exit are all added as **marker-`4`
branches** in `skills/sdd-orchestrate/SKILL.md` / `skills/sdd-research/SKILL.md`, gated
on `docs/.sdd-version` == `4`. Under marker `3` (or earlier) the driver's existing
single-flat-cycle entry is retained **unchanged**: no `docs/ws/` enumeration, the single
`docs/handoff/kickoff.md`, the single global-operator-intent done-vs-new-cycle logic
(§New cycle vs. resume), and §Entry Points mid-pipeline entry all behave exactly as
today. This spec describes the picker generically; the marker gate is the same
sole-`.sdd-version`-gate discipline Chunks 0–5 used so the LIVE v3 repo's behavior is
untouched.
**Rationale**: There is no `docs/ws/` under marker `3`, so an ungated picker would break
v3 solo use. The gate is consistent with `ws-layout.md` §.sdd-version gate (marker != 4
routes to the migrate / v3 path).

### Q-IMPL-017: Research early-exit recording shape
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Research Early-Exit — "records a fast, explicit early-exit (a recorded finding of 'covered by shared corpus — no new spike')"
**Decision**: The early-exit reuses the normal RS artifact: assign the `RS-<WS>-NNN` id
per Step 2, then write `docs/research/RS-<WS>-NNN-{topic}/findings.md` with frontmatter
`status: Complete` **plus a distinguishing `early_exit: true` flag**, and a single
finding "Covered by shared corpus — no new spike" naming the shared REQ/SPEC/RS ids that
cover the work; Steps 3–4 (Explore, budget) are skipped, Step 6 (index) still runs. The
`early_exit: true` flag is what makes it auditable and **distinct** from a full spike.
**Rationale**: The spec fixes the recorded *content* but not the file shape; reusing the
existing findings.md schema (rather than a new artifact type) keeps the research state in
one place, and a single boolean flag is the minimal marker that distinguishes an
early-exit from a full spike without a new parser. No new artifact type is introduced.

### Q-IMPL-018: DONE signal & new-cycle overwrite for per-workstream done-vs-new-cycle
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Workstream Picker — "a DONE workstream offers 'start a new cycle in this workstream'"
**Decision**: A workstream's **DONE** state for the picker is read from its own
`docs/ws/<id>/verification.md` being `status: pass` (the marker-`4` per-ws execution
artifact, per `ws-layout.md`), never from a repo-global `docs/verification.md`. "Start a
new cycle in this workstream" **overwrites** that workstream's `docs/ws/<id>/kickoff.md`
at KICKOFF (mirroring the marker-`3` §New cycle vs. resume overwrite semantics, scoped to
the workstream); a genuinely new idea mints a **new** workstream id with a fresh kickoff.
**Rationale**: Resolving DONE per workstream from the per-ws `verification.md` is exactly
what makes done-vs-new-cycle a per-workstream decision rather than a global-intent appeal
(REQ-WS-029); reusing the established overwrite semantics avoids inventing a new marker.

### Q-IMPL-072: Picker prose lives in `references/v4-workstreams.md`
**Tier**: 1 (implementation choice)
**Spec reference**: §Workstream Picker at Orchestration Entry; `skill-lint-v5.md` section Marker-4 Prose Move, guard 2
**Decision**: The marker-`4` picker procedure (§Workstream Picker and its three
subsections), the v4 version gate, the done-vs-new-cycle gate, the entry-points
marker-4 scope, the kickoff path gate and the fan-out integration anchor live in
`skills/sdd-orchestrate/references/v4-workstreams.md`. The `docs/.sdd-version`
gate and a stub for each moved section — keeping the "behavior UNCHANGED under
marker 3" sentence, a resolving link and (for the picker) a `research_id`
mention — remain in `skills/sdd-orchestrate/SKILL.md`. This supersedes
Q-IMPL-016's **container statement** only ("added as marker-`4` branches in
`skills/sdd-orchestrate/SKILL.md`"); its gating decision and the marker-`3`
behavior guarantee are unchanged.
**Rationale**: `SKILL.md` is the entry point and should read as a table of
contents (REQ-LINT-003 size warn, REQ-LINT-007); the picker text is
marker-`4`-only procedure that a marker-`3` operator never needs, so it moves
behind a stub. Q-IMPL entries are append-only, hence a new entry rather than an
edit to Q-IMPL-016.
**Date**: 2026-09-17 (Chunk 5)
