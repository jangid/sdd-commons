# Marker-4 Workstreams (v4) — orchestrate reference

Marker-`4`-only procedure text moved out of `SKILL.md` (REQ-LINT-007). Each
section below is referenced from a stub in `SKILL.md` that keeps the
"behavior UNCHANGED under marker 3" sentence; `docs/.sdd-version` is the sole
gate throughout. Contracts: `docs/spec/ws-orchestration.md`,
`docs/spec/ws-layout.md`, `docs/spec/ws-integration.md`.

## Upgrade offer at entry (REQ-WS-030) — from §Phase Detection

**Upgrade offer (entry, all markers).** First read `docs/.sdd-version`; if it
is **behind** the latest version the installed skills support (currently `4`),
**offer to run `/migrate` first** — informational, non-forcing, and the
single place a behind-version project is nudged (REQ-WS-030). On accept, hand
off to `migrate` and re-derive phase from the migrated layout; on decline
(or non-interactive) proceed on the current marker with behavior **unchanged**;
at the latest marker, say nothing.

## Workstream & version gate (v4) — from §Phase Detection

**Workstream & version gate (v4).** The driver accepts an optional `workstream`
argument that defaults to `default`, threaded through to every dispatched stage
skill. `docs/.sdd-version` is the **sole** layout gate:

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Ignore the workstream
  argument and derive loop position from the flat artifacts exactly as the table
  below states — `docs/handoff/kickoff.md`, `docs/plan.md`, `docs/verification.md`.
  Never read `docs/ws/`.
- **Marker is `4` (workstream-aware layout).** Resolve `ws` = the workstream
  argument (default `default`), set `base = docs/ws/<ws>/`, and read that
  workstream's **execution artifacts** — `kickoff.md`, `plan.md`,
  `verification.md`, `plan-history/` — from `base` (so the table below maps
  `docs/handoff/kickoff.md` → `docs/ws/<ws>/kickoff.md`, `docs/plan.md` →
  `docs/ws/<ws>/plan.md`, `docs/verification.md` → `docs/ws/<ws>/verification.md`),
  never from flat `docs/`. The **shared corpus** stays at its top-level paths:
  `docs/research/`, `docs/requirements/` (incl. aggregated `traceability.md`),
  `docs/spec/`. Omitting the argument resolves the implicit `default` workstream,
  so solo use needs no naming. Enumerating `docs/ws/<id>/` to present a workstream
  picker is specified separately in `docs/spec/ws-orchestration.md`; this step-0
  gate only establishes the workstream argument and marker-`4` execution-artifact
  rooting. Full layout contract: `docs/spec/ws-layout.md`.

## Marker-4 gate for done-vs-new-cycle — from §Phase Detection

**Marker-`4` gate for done-vs-new-cycle.** `docs/.sdd-version` is the sole gate for
how this ambiguity is resolved:

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** The repo holds a single
  flat cycle (`docs/handoff/kickoff.md`, `docs/plan.md`, `docs/verification.md`) and
  the *done* vs *new cycle* choice is resolved by the **single global operator
  intent** described just above — verbatim, unchanged.
- **Marker is `4`: resolved PER WORKSTREAM via the picker (REQ-WS-029), not by a
  global intent.** Phase is now a function of `(repo, workstream)`, so there is no
  single repo-wide "done" state to appeal to — several workstreams may sit at
  different phases at once. The **Workstream Picker** (§Workstream Picker) surfaces
  each workstream with its detected phase and resolves *done vs new cycle* **within
  the selected workstream's context**: selecting a workstream whose phase is DONE
  (its `docs/ws/<id>/verification.md` is `status: pass`) offers "start a new cycle in
  **this** workstream", while a genuinely new idea creates a **new** workstream id —
  never by appealing to one global operator intent.

## Workstream Picker — from SKILL.md §Workstream Picker

`docs/.sdd-version` is the **sole** gate for whether the driver opens with a
workstream picker:

- **Marker is not `4` (v3 or earlier): NO picker — behavior UNCHANGED.** There is no
  `docs/ws/` under marker `3`; the driver drives the single flat cycle exactly as
  today: derive loop position from the flat artifacts (§Phase Detection table),
  resolve done-vs-new-cycle by the single global operator intent (§New cycle vs.
  resume), and use the one `docs/handoff/kickoff.md`. Skip this whole section.
- **Marker is `4`: present a workstream picker at entry (REQ-WS-029).** Because phase
  is a function of `(repo, workstream)`, the driver cannot infer a single active
  cycle from the repo — several workstreams may be live at once — so it must ask which
  workstream the operator is driving before entering the LOOP.

### Present existing workstreams (marker `4`, REQ-WS-029)

Enumerate the `docs/ws/<id>/` directories (each directory is one workstream) and, for
**each**, show a row:

| Field | Source |
|-------|--------|
| id | the `docs/ws/<id>/` directory name |
| description | the description recorded in `docs/ws/<id>/kickoff.md` (kickoff is per-workstream, per `ws-migration.md`) |
| detected phase | that workstream's phase, computed by the §Phase Detection gate with `ws = <id>` (`base = docs/ws/<id>/`) |

Then let the operator **select an existing workstream or create a new one**. Two
workstreams sitting at different phases (e.g. `ISSUE-42` at implement, `ISSUE-57` at
plan) are **both** listed with their own phase, so the operator names the one they are
driving rather than the driver guessing.

**Solo degenerates to a picker of one (REQ-WS-020).** In a repo whose only workstream
is `default` (the migrated/solo case), the picker collapses to that single workstream
with **no naming ceremony** — it is a picker of one, not a prompt the solo operator
must answer. Resolve `default` and proceed exactly as a solo v3 cycle would feel.

### Resolve done-vs-new-cycle per workstream (REQ-WS-029)

Disambiguation is **per workstream**, never by a single global operator intent
(§New cycle vs. resume, marker-`4` gate):

- **Select an existing workstream** → drive it from its detected phase. If that phase
  is **DONE** (`docs/ws/<id>/verification.md` is `status: pass`), offer **"start a new
  cycle in this workstream"** — resolved inside that workstream's context (a new cycle
  overwrites `docs/ws/<id>/kickoff.md` at KICKOFF, as §KICKOFF describes), or report
  DONE if the operator has no new idea for it.
- **Create a new workstream** for a genuinely new idea → mint a **new workstream id**
  (conventionally the branch/issue key, per `ws-integration.md`) and enter the uniform
  research-entry lifecycle below. A new idea is a new id, not a "new cycle" appended to
  someone else's workstream.

### Uniform research-entry lifecycle for a new workstream (REQ-WS-024)

Every **new** workstream begins at the **research stage**, regardless of how much
shared corpus already exists — there is **no per-workstream mid-pipeline entry variant
to select at creation** (mid-pipeline entry, §Entry Points, is a marker-`3`
single-cycle concept; a marker-`4` new workstream always starts at research). Creating
a new workstream:

1. mints the workstream id and creates/uses its branch (`ws-integration.md`);
2. **positions its loop at research** (§Phase Detection: `docs/ws/<id>/kickoff.md`
   exists and research is **not yet complete for `<id>`** → the research stage).
   Research is complete for this cycle when the kickoff's recorded `research_id`
   spike (`docs/research/RS-<id>-NNN-*/findings.md`) exists with
   `status: Complete` (an explicit early-exit finding counts as Complete) —
   scoped to the kickoff's spike, not "any `RS-<id>-*`", so a prior cycle in the
   same workstream never masks a new cycle's research stage. Research findings are **shared**
   — they live in the common `docs/research/` tree, ws-keyed **only** by the
   `RS-<WS>-` id prefix (there is **no** `docs/ws/<id>/research/` dir); the
   workstream owns `docs/ws/<id>/` kickoff, plan, and verification;
3. seeds `docs/ws/<id>/kickoff.md` as a research kickoff (§KICKOFF).

Uniformity keeps the lifecycle one predictable shape for every workstream. It stays
cheap because the research stage **early-exits fast** when the shared corpus already
covers the new workstream's needs: the research pipeline subagent records a fast,
explicit early-exit ("covered by shared corpus — no new spike") rather than running a
full spike, then the loop advances (REQ-WS-025 — see `research` §Research
Early-Exit and `docs/spec/ws-orchestration.md`).

## Marker-4 scope — from §Entry Points

**Marker-`4` scope.** Non-research mid-pipeline entry described in this section is a
**marker-`3` single-cycle** concept. Under marker `4` a **new** workstream always
begins at research (uniform research-entry, §Workstream Picker → REQ-WS-024) — there
is no per-workstream mid-pipeline entry variant to select at its creation; selecting
an **existing** marker-`4` workstream simply resumes it from its detected phase via
the picker, which is resume, not entry.

## Legal `Verified` cell values (REQ-REDB-HARNESSP3-003) — from §The gate

The per-ws `docs/ws/<id>/traceability.md` `Verified` column has **three** legal
values — it tracks the *report's* status, not a separate judgement:

| Value | Meaning |
|---|---|
| `pass` | the report covering that row is `status: pass` |
| `fail` | the row's requirement failed verification |
| `pending-red` | the report is `status: pending-red` — a red round is outstanding |

`verify` writes `pending-red` into every cell it would otherwise have marked
`pass` (a `fail` row stays `fail`); the orchestrator's `pending-red → pass` flip
at DONE flips exactly those cells and regenerates the aggregate in the same
post-gate bookkeeping step (`../SKILL.md` §The gate). No sweep in
`tools/gc.py` constrains this cell's vocabulary. Full contract:
`docs/spec/ws-traceability.md` §Legal `Verified` Cell Values.

## Kickoff path — version gate — from §KICKOFF

**Kickoff path — version gate.** `docs/.sdd-version` selects where the kickoff lives:
- **Marker is not `4`:** the single flat `docs/handoff/kickoff.md` (unchanged).
- **Marker is `4`:** the per-workstream `docs/ws/<id>/kickoff.md` for the workstream
  selected/created at the picker (kickoff is absorbed per-workstream, `ws-migration.md`;
  no flat `docs/handoff/` in v4). Its `description` is what the §Workstream Picker
  reads back when listing workstreams. A **new cycle in a DONE workstream** overwrites
  that workstream's `docs/ws/<id>/kickoff.md`; a **new workstream** seeds a fresh one.

## Integration anchor (version gate) — from §Execution Model

### Integration anchor (version gate — marker-3 `main` vs marker-4 workstream branch)

`docs/.sdd-version` is the **sole** gate for the fan-out integration anchor
(`docs/spec/ws-integration.md`):

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Fan-out branches from
  and merges into `main`; `verify` diffs against `main`; the §Conflict-handling
  `main`-ownership boundary-error inference applies. The v3 path is untouched.
- **Marker is `4`: integration is branch-per-workstream → PR to `main` (REQ-WS-016).**
  The **workstream branch — not `main`** — is the integration unit for that
  workstream's whole cycle: a completed workstream merges to `main` via **PR**, two
  workstreams can hold **open PRs simultaneously**, and `main` is a shared trunk, not
  a working surface. Consequently, implement-stage fan-out branches its worktrees from
  the **workstream branch** (HEAD) and merges them **back into it**, leaving `main`
  untouched until the workstream PR (REQ-WS-017); the `main`-ownership boundary-error
  inference is **removed**; and `verify`'s regression base is the **workstream
  branch point** `merge-base(<ws>, main)`, not `main` HEAD (REQ-WS-018). Full contract
  and the exact command substitutions: [`references/fan-out.md`](fan-out.md)
  §0.

## Marker-4 anchor — from §Conflict handling

**Marker-4 anchor (§Integration anchor):** under `docs/.sdd-version` == `4` the
provision base, merge-back target, and redo re-branch are the **workstream branch**
(not `main`), and the "**still conflicts → boundary error**" inference is **removed**
(REQ-WS-017) — `main` may have moved under the workstream meanwhile, so a repeat
conflict is not diagnostic of non-independence. The guaranteed-termination sequential
fallback is retained (re-run affected groups one at a time off the updated workstream
branch). Under marker `3` this paragraph applies against `main` exactly as written,
unchanged. See [`references/fan-out.md`](fan-out.md) §0/§3c.
