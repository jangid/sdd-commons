---
name: sdd-migrate
description: >
  Migrates SDD artifact structures between versions (v1→v2→v3→v4). Handles
  research directory restructuring, requirements splitting with ID remapping,
  plan archival, plan vocabulary rename, v3 convention adoption, and the v3→v4
  copy-verify-flip-cleanup to the per-workstream `docs/ws/<id>/` layout. Use when
  other SDD skills detect old-format artifacts or when upgrading a project to
  the latest SDD conventions. Skip if docs/.sdd-version already shows `4`.
---

# SDD: Migrate

You are migrating a project's SDD artifacts from one structure version to another. This is a one-time operation per version transition. Each step is independent and idempotent — you can re-run safely after interruption.

## Version Detection

Before anything else, determine the current artifact version:

**Workstream & version gate (v4).** This skill accepts an optional `workstream`
argument that defaults to `default`. `docs/.sdd-version` is the **sole** layout
gate for every skill's step-0:

- **Marker is not `4` (v3 or earlier): behavior UNCHANGED.** Run exactly the
  version-routing table below; execution artifacts are the flat `docs/plan.md` /
  `docs/verification.md` / `docs/plan-history/` (and flat `docs/handoff/`). Never
  read or write `docs/ws/`.
- **Marker is `4` (workstream-aware layout).** Per-workstream execution artifacts
  are authoritative: resolve `ws` = the workstream argument (default `default`),
  set `base = docs/ws/<ws>/`, and treat `plan.md`, `verification.md`, `kickoff.md`,
  and `plan-history/` as living under `base` — never at flat `docs/`. The shared
  corpus (`docs/research/`, `docs/requirements/` incl. aggregated
  `traceability.md`, `docs/spec/`) stays at its top-level paths. A workstream never
  gets a `docs/ws/<ws>/requirements/` or `docs/ws/<ws>/spec/` dir. A v3-marked repo
  never reads `docs/ws/`; a v4-marked repo never reads flat execution paths.

The concrete v3→v4 migration routing (the `3`→`4` arm, copy-verify-flip-cleanup,
and the `4` = "already at v4" exit) is specified in `docs/spec/ws-migration.md` and
wired into the version-routing table via § v3 to v4 Migration below — this step-0
gate only establishes the workstream argument and the marker-`4` layout semantics.
Full layout contract: `docs/spec/ws-layout.md`.

1. **Greenfield check**: if there are no SDD artifacts to migrate — no `docs/` directory at all, or a `docs/` containing none of `requirements.md`, `requirements/`, `research/`, `spec/`, `plan.md` — there is nothing to *migrate*. Offer to **initialize** instead: create `docs/` (if absent) and write `docs/.sdd-version` containing `4` (the latest supported version), so other SDD skills stop detecting a pre-versioning layout and route correctly. Get confirmation, write the marker, report "initialized at v4 (greenfield — no artifacts migrated)", and exit. A "missing marker" therefore means *v1 legacy layout* only when legacy artifacts actually exist.
2. Read `docs/.sdd-version`:

| Disk state | Version | Action |
|------------|---------|--------|
| File missing | v1 | Run v1→v2 → v2→v3 → v3→v4 in one invocation (marker written `4` last) |
| Contains `2` | v2 | Run v2→v3 → v3→v4 (marker written `4` last) |
| Contains `3` | v3 | Offer v3→v4 migration (see § v3 to v4 Migration below) |
| Contains `4` | v4 | Already current — inform user and exit |
| Other value | Unknown | Warn and exit without changes |

**Routing logic:**

1. If v4 → "Already at v4, nothing to migrate." Exit (clean no-op — see § v3 to v4 Migration → Version-Routing Extension).
2. If v3 → run v3→v4 migration (see § v3 to v4 Migration below).
3. If v2 → run v2→v3 migration (see § v2 to v3 Migration below), then continue into v3→v4. The chain terminates by writing `4` last.
4. If v1 → run v1→v2 first (Steps 1-3 + Finalization below), then continue directly to v2→v3 without writing the intermediate version marker, then continue into v3→v4. The composition is sequential within a single invocation (see § v1 to v4 Composition). The marker is written `4` last, once, at the v3→v4 finalization.

Tell the user which version you detected and what will happen. Get confirmation before proceeding.

## Migration Pipeline Overview

The v1-to-v2 migration has three independent steps:

```
Step 1: Research    (docs/research/*.md    -> docs/research/RS-NNN-{topic}/)
Step 2: Requirements (docs/requirements.md -> docs/requirements/{category}/)
Step 3: Plan        (docs/plan.md          -> docs/plan-history/ + lean plan)
```

Each step checks its own preconditions. If research is already migrated but requirements are not, Step 2 runs without Step 1. This supports partial migrations and resumption after interruption.

**Ask the user for confirmation before each step.** Present what will change and wait for approval.

## Steps 1-3: The v1→v2 Migration

The three v1→v2 steps — research restructuring, requirements splitting with ID
remapping (including domain-prefix inference and the ID-remapping safety
rules), and plan archival — together with v1→v2 Finalization and the mid-cycle
phase-preservation table, live in
[`references/v1-to-v2.md`](references/v1-to-v2.md). Read that file when the
detected version is v1; the v2→v3 and v3→v4 sections below are self-contained.

## v2 to v3 Migration

v3 adds behavioral conventions (chunk-close review, Q-IMPL protocol, per-milestone plans, cross-spec consistency) on top of the v2 artifact layout. The only artifact change is plan vocabulary — work-unit headers shift from `### M N:` to `### Chunk N:`. Migration is opt-in; v2 projects work without it.

### Backward Compatibility

v2 projects that have not run v2→v3 migration continue to work:

- **Chunk-close review** is inactive when plan headers don't use `### Chunk N:` format.
- **Per-milestone logic** activates only when per-milestone files (`docs/plan-{id}.md`) exist.
- **Q-IMPL entries** accumulate on demand — specs without `## Implementation Questions` are fine.

### Step 1: Plan Vocabulary Rename

**Skip this step if:**
- `docs/plan.md` does not exist
- The plan already uses `### Chunk N:` headers (no `### M\d+:` matches found)
- The plan is complete with no active work

**Process:**

1. Read `docs/plan.md`.
2. Scan for lines matching the regex `### M\d+:` (M followed by one or more digits, then a colon). This matches `### M1:`, `### M12:`, etc. It does NOT match `### Migration`, `### Models`, or other section headers starting with M.

   **Do NOT touch (RS-007 Q4 — provably unaffected):** this `### M\d+:` milestone
   regex matches milestone **header** ordinals, a separate namespace from RS / REQ /
   Q-IMPL artifact ids. The workstream `<WS>` segment added in v4 never appears in a
   milestone header, so this regex is unaffected and must stay exactly as written —
   do not extend it for ws-prefixed ids.
3. Present proposed renames to the operator, preserving original numbering:
   ```
   ### M1: Foundation    →  ### Chunk 1: Foundation
   ### M2: Core Models   →  ### Chunk 2: Core Models
   ```
   Numbering is preserved (M1 → Chunk 1, not Chunk 0) — chunk-close triggers on `### Chunk N:` regardless of N's value, and renumbering would break external references for no functional benefit.
4. **Wait for operator confirmation before applying.** Do not rename automatically.
5. Apply renames in `docs/plan.md` only. Archive files in `docs/plan-history/` are historical snapshots — do not modify them.

**Edge cases:**
- **Mixed headers** (`### M1:` as delivery milestone alongside `### Chunk N:` as work units): Present the mixed state for operator confirmation; do not auto-rename delivery milestone headers.
- **Completed entries in `## Completed`**: Leave as-is — these are one-line summaries without `###` headers.

### Step 2: Multi-Milestone Split (Optional)

**Precondition:** `docs/plan.md` contains multiple delivery milestone groupings with distinct chunks under each.

1. Offer to split into per-milestone plan files (`docs/plan-{id}.md`) with `docs/plan.md` converted to an index. Each per-milestone file gets `milestone:`, `last_updated:`, and `status:` frontmatter.
2. **Operator confirms or declines. Declining is the default** — single-file plans are valid in v3.
3. If accepted, archive the pre-split plan to `docs/plan-history/` before splitting.

### Step 3: Capability Report

After completing required steps, report new v3 capabilities to the operator:

- **Chunk-close review**: Structured 4-check checklist at each `### Chunk N:` boundary during `sdd-implement`.
- **Q-IMPL deviation protocol**: Three-tier classification for implementation decisions diverging from spec.
- **Per-milestone plan support**: Optional structure for multi-milestone projects with milestone-scoped staleness.
- **Cross-spec consistency pass**: Type reference validation between specs during `sdd-specs`.

The report is informational — no operator action required. These mechanisms activate automatically during their respective skill phases.

### Step 4: Finalization

1. Write `3` to `docs/.sdd-version` (overwriting `2`).
2. Present a migration summary:
   - Plan vocabulary: N headers renamed (or "skipped — already using Chunk format")
   - Multi-milestone split: applied / declined / not applicable
   - New capabilities: listed in the capability report above

**Version marker is written last.** If any prior step fails or is interrupted, `.sdd-version` still contains `2`. Re-running `sdd-migrate` detects v2 and resumes the v2→v3 migration. In a v1→v4 / v2→v4 composition this `3` write is the checkpoint that satisfies v3→v4's marker-`3` precondition; the terminal `4` is written by v3→v4 Finalization (see § v3 to v4 Migration).

## v3 to v4 Migration

v4 relocates the flat execution artifacts under `docs/ws/default/` while leaving the
requirements/spec/research/traceability corpus shared at top level. A v3 repo adopts
v4 through this one-time step. Full contract: `docs/spec/ws-migration.md` (covers
REQ-WS-021, REQ-WS-022, REQ-WS-023); layout contract `docs/spec/ws-layout.md`.

### `.sdd-version` Is the Sole Layout Gate (REQ-WS-023)

`docs/.sdd-version` is the single switch selecting which execution layout every
skill's step-0 reads:

| Marker | Authoritative execution layout |
|--------|-------------------------------|
| `3` | flat: `docs/plan.md`, `docs/verification.md`, `docs/plan-history/`, flat `docs/handoff/kickoff.md` |
| `4` | per-workstream: `docs/ws/<id>/{kickoff,plan,verification}.md`, `docs/ws/<id>/plan-history/` (default ws `default`); `requirements/`, `spec/`, `research/`, aggregated `traceability.md` stay shared at top level |

- A v3 skill (marker `3`) must **never** read `docs/ws/`.
- A v4 skill (marker `4`) must **never** read flat execution paths (`docs/plan.md`,
  `docs/verification.md`, `docs/plan-history/`, `docs/handoff/`).
- A v4-aware skill invoked while the marker still reads `3` sees "not yet migrated"
  and suggests `sdd-migrate`. This cross-checks the Chunk 0 step-0 branches — every
  `sdd-*` skill gates on this same marker, so the on-disk layout and the marker are
  only ever read together and no skill misdetects phase during or after migration.

### Version-Routing Extension

The version routing (§ Version Detection) gains a `3`→`4` arm and a `4` no-op:

```
elif version == 3:
    migrate_v3_to_v4()      # this section
elif version == 4:
    inform("already at v4, nothing to do")   # clean exit, no changes
```

For missing/`2` markers, the existing v1→v2→v3 chain runs first (terminating by
writing the `3` checkpoint), then v3→v4 composes on the end. The marker is written
`4` **last, once** — at v3→v4 Finalization.

### Decision: kickoff.md Absorbed Per-Workstream; No Flat `docs/handoff/` in v4 (REQ-WS-021)

`kickoff.md` lives at `docs/ws/<id>/kickoff.md` (per-workstream). The flat
`docs/handoff/` directory is **NOT retained** in v4: the migration moves a flat
`docs/handoff/kickoff.md` (if present) to `docs/ws/default/kickoff.md`. Retaining a
flat `docs/handoff/` would reintroduce a repo-global singleton — exactly the
collision the v4 layout removes — and split kickoff state across two locations. Under
marker `4` **no skill reads `docs/handoff/`**; `sdd-orchestrate`'s picker and every
step-0 read `docs/ws/<id>/kickoff.md` (see `docs/spec/ws-orchestration.md`).

### `migrate_v3_to_v4()` — Copy-Verify-Flip-Cleanup (REQ-WS-021, REQ-WS-022)

The migration **copies** execution artifacts into `docs/ws/default/`, **verifies**
them byte-identical, writes the marker **last**, then deletes the flat originals as
idempotent cleanup. Copy-then-delete (not move) is the one deviation from prior
move-based migrations: while the marker still reads `3`, v3 skills must still find
the flat files, so the flat layout must stay valid across the entire `3` window.
Duplicates under `docs/ws/default/` are invisible to v3 skills; moving would break
the flat layout the instant it ran — before the marker flips — violating the
"version marker written last" invariant that makes interrupted migrations safe.

**Safe step order:**

1. **Precondition**: `docs/.sdd-version` == `3` (in a v1/v2 composition, control
   reaches here immediately after the chain wrote the `3` checkpoint). Create
   `docs/ws/default/` and `docs/ws/default/plan-history/`.
2. **Copy** (not move), preserving content verbatim — task `[x]`/`[ ]` status and
   pass/fail verdicts byte-for-byte:
   - `docs/plan.md` → `docs/ws/default/plan.md`
   - `docs/verification.md` (if present) → `docs/ws/default/verification.md`
   - `docs/plan-history/*` → `docs/ws/default/plan-history/`
   - `docs/handoff/kickoff.md` (if present) → `docs/ws/default/kickoff.md`
3. **Verify** each copy is **byte-identical** to its source (e.g. `cmp` / `diff` /
   hash comparison). If any copy fails verification, **STOP and report** — do NOT
   write the marker and do NOT delete anything.
4. Leave the **shared corpus** in place — `docs/requirements/`, `docs/spec/`,
   `docs/research/`, and `docs/requirements/traceability.md` are NOT moved. The legacy
   corpus keeps its bare ids (treated as the `default` workstream); **no id is
   remapped** (see `references/v1-to-v2.md` § Idempotency and `ws-migration.md` /
   `ws-traceability.md`).
5. **Write `docs/.sdd-version` = `4`** — the single atomic layout flip, written
   **LAST**, once.
6. **Cleanup** (idempotent): delete the now-orphaned flat `docs/plan.md`,
   `docs/verification.md`, `docs/plan-history/`, and flat `docs/handoff/kickoff.md`
   (and the now-empty `docs/handoff/`).

### Interrupted-Migration Invariant (REQ-WS-022)

- Interrupted **before** the flip (step 5): the marker still reads `3` and the flat
  files are intact → a **working v3 repo**. Re-running restarts copy-verify (copy is
  idempotent — it overwrites the `docs/ws/default/` duplicates with identical
  content, then re-verifies).
- Interrupted **after** the flip: the marker reads `4` and v4 skills already ignore
  the flat paths → a **working v4 repo**. Re-running detects marker `4`, and because
  the only work left after the flip is cleanup, it re-does cleanup idempotently
  (deleting any flat originals that survived).

At **every** interruption point before the marker flip, the flat layout is still
authoritative and every skill behaves exactly as v3 — the marker-written-last
ordering is what guarantees this: the flip happens only after all copies are verified
byte-identical, and cleanup is the only step after the flip.

### Finalization

1. The atomic flip (step 5 above) — write `4` to `docs/.sdd-version`, after
   byte-identity verification and before cleanup.
2. Present a v3→v4 migration summary:
   - Execution artifacts copied into `docs/ws/default/`: plan, verification (if
     present), plan-history, kickoff (if a flat `docs/handoff/kickoff.md` existed)
   - Byte-identity verification: pass
   - Shared corpus left in place: requirements, spec, research, traceability
   - Flat originals cleaned up: plan.md, verification.md, plan-history/, handoff/

**Version marker written last.** If any step before the flip fails or is interrupted,
`.sdd-version` still contains `3` and the flat layout stays authoritative — re-running
detects v3 and safely restarts copy-verify.

## v1 to v4 Composition

For v1 projects (`.sdd-version` missing), `sdd-migrate` runs v1→v2
(`references/v1-to-v2.md`, Steps 1-3), then v2→v3 (Steps 1-4 above), then v3→v4 (§ v3 to v4 Migration) in a single
invocation. A v2 project runs v2→v3 then v3→v4.

- **Intermediate state**: v1→v2 completes but does NOT write `.sdd-version` in the
  composition path. v2→v3 Finalization writes the `3` checkpoint (which satisfies
  v3→v4's marker-`3` precondition); v3→v4 Finalization then writes `4` last. The
  marker file is thus written `3` then `4` — the `4` value is written **once and
  last**.
- **Resumability**: interrupted before v2→v3 completes → `.sdd-version` is still
  missing/`2`, re-running restarts the chain (each step idempotent). Interrupted
  during v3→v4 after the `3` checkpoint but before the flip → `.sdd-version` reads
  `3`, the repo is a working v3 repo, and re-running detects v3 and runs only
  v3→v4's idempotent copy-verify-flip-cleanup. Interrupted after the flip →
  `.sdd-version` reads `4`, re-running re-does cleanup idempotently.
- **v1→v2 / v2→v3 logic unchanged**: the Step 1-3 detail in `references/v1-to-v2.md`
  and the v2→v3 section above are not
  modified. v3→v4 is a new section. Composition is routing logic only.

## Rules

- **Confirm before each step**: never modify files without user approval
- **Idempotent steps**: each step checks preconditions and skips if already done
- **No data loss**: archive before modifying, verify before deleting
- **Docs only**: never modify files outside `docs/` during migration
- **Preserve phase state**: task completion, draft statuses, in-progress research all survive migration
- **Log everything**: print the ID mapping, file moves, and changes so the user has a full audit trail
- **Stop on error**: if any verification check fails (missing ID mapping, failed replacement), halt and report rather than continuing with partial state
- **Domain prefixes are user-approved**: always propose and wait for confirmation before remapping IDs
