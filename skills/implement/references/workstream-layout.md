# Marker-4 Detail — Cycle Identity, Per-Workstream Traceability, Prefixed Q-IMPL IDs

Detail behind three stubs in `../SKILL.md`: § Phase Detection (cycle identity),
§ Task Completion Checklist (per-workstream traceability and aggregate
regeneration) and § Numbering Rules (workstream-prefixed Q-IMPL ids). All three
are gated on `docs/.sdd-version` == `4`; under marker `3` or earlier the
behaviour stated in `SKILL.md` is unchanged and nothing here applies.
Contracts: `docs/spec/cycle-identity.md`, `docs/spec/ws-traceability.md`,
`docs/spec/ws-ids.md`.

---

## 1. Cycle identity (REQ-CYCID-HARNESSP3-001, -002)

**Cycle identity (REQ-CYCID-HARNESSP3-001, -002).** Before reading a
**completion signal** as "this cycle is done" — `verification.md` `status: pass`,
or `plan.md` `status: complete` with every task `[x]` — compare that artifact's
frontmatter `research_id:` against the kickoff's (`docs/ws/<ws>/kickoff.md` under
marker `4`, `docs/handoff/kickoff.md` under marker `3`) by **exact string
equality** on the trimmed value — no normalisation, case folding or prefix
matching (Q-IMPL-HARNESSP3-015). The three cases are exhaustive:

1. **Mismatch** — the artifact's `research_id` differs from the kickoff's → **a
   previous cycle's artifact**; this stage has not been reached in this cycle.
2. **Field absent** — a kickoff with a `research_id` exists but the artifact
   carries none (legacy; existing files are **never back-filled**) → the same
   reading as a mismatch. Absence is the safe direction: it costs one re-entry,
   it never asserts a completion that did not happen.
3. **No usable discriminator** — no `kickoff.md` for this `(repo, workstream)`,
   **or** a kickoff that carries no `research_id` (Q-IMPL-HARNESSP3-016) → the
   comparison is **skipped entirely** and the existing `status:`-only rule
   applies unchanged. Cycle identity is an orchestrated-cycle discriminator,
   never a precondition for detection.

See `docs/spec/cycle-identity.md`.


---

## 2. Per-workstream traceability (REQ-WS-008, REQ-WS-007, REQ-WS-HARNESSP3-001)

**Per-workstream traceability (marker `4` only).** `docs/.sdd-version` is the sole gate;
under marker `3` or earlier the shared `docs/requirements/traceability.md` is written
**directly** as above (historical 5-column shape, no per-ws files, no regeneration) and
this note does not apply. Under marker `4`, rows are **per-workstream-owned**
(REQ-WS-008): fill **Test** / **Implementation** in the active workstream's OWN file
`docs/ws/<ws>/traceability.md` — never another ws's file, never the shared aggregate in
place — then **regenerate** the aggregate (below). Full contract: `docs/spec/ws-traceability.md`.

- **Per-workstream file shape (REQ-WS-008).** `docs/ws/<ws>/traceability.md` carries
  frontmatter `workstream: <ws>` / `last_updated:` and the matrix with **Workstream** as
  the **3rd column** — `| Requirement | Spec | Workstream | Test | Implementation | Verified |` —
  holding **only** this workstream's rows (new `REQ-<DOMAIN>-<WS>-NNN` plus shared REQs it
  re-uses); a workstream never edits another ws's file. The **Verified** cell is
  `verify`'s to write and has three legal values — `pass`, `fail` and
  `pending-red` (`docs/spec/ws-traceability.md` §Legal `Verified` Cell Values);
  never fill it here.
- **Aggregate is regenerated, never hand-merged (REQ-WS-008).** `docs/requirements/traceability.md`
  is a **derived** aggregate. After updating the per-ws file, rebuild it **wholesale**: shipped
  legacy rows (predating the v4 migration, attributed to the blank/default workstream)
  `+ concat(` every `docs/ws/<id>/traceability.md` `)`, **stable-sorted by requirement id**.
  Same inputs → byte-identical output; never append or hand-edit it, so two concurrent
  workstreams never conflict — each writes only its own file and the aggregate re-derives on
  merge. The `Workstream` column does not disturb the REQ-WS-012 unchanged-parser guarantee.
- **Recorded join vs. compute-live staleness (REQ-WS-007).** The per-ws files and the aggregate
  are the **recorded** coverage join ONLY; the staleness computation **MUST NOT read any
  traceability file** — it derives the same scoped set live from the plan's
  `task → spec requires: → requirement` chain. And **no traceability schema column is added for
  staleness**: the `Workstream` column exists only to attribute aggregated rows, not to feed staleness.

**Unless the dispatched write scope omits the aggregate (REQ-WS-HARNESSP3-001).**
Regenerate the aggregate after the per-ws write **unless this run was dispatched
with a write scope that omits `docs/requirements/traceability.md`** — under
`orchestrate` that path is absent from every leaf scope by construction, and
its absence *is* the signal that regeneration is the orchestrator's post-gate
bookkeeping (`orchestrate/references/write-scope.md` §2, §7). Its presence in
the dispatched scope, or no dispatched write scope at all (a standalone run),
means regenerate here. No flag or field beyond the scope slot is involved.

---

## 3. Workstream-prefixed Q-IMPL ids (REQ-WS-009, REQ-WS-011)

**Workstream-prefixed IDs (marker `4` only).** `docs/.sdd-version` is the sole gate.
When the marker is **not** `4` (v3 or earlier), number exactly as above — bare
`Q-IMPL-NNN`, global sequential scan, behavior UNCHANGED. When the marker is `4`,
resolve `ws` (the workstream argument, default `default`) and allocate
`Q-IMPL-<WS>-NNN` with a **per-workstream counter**:
- `{NNN}` is parsed **after** the `<WS>` token and scanned for its max per workstream
  — not globally — so each workstream advances an independent Q-IMPL sequence
  (`Q-IMPL-ISSUE42-003`, `Q-IMPL-ISSUE57-001`) with no cross-workstream collision
  (REQ-WS-009, REQ-WS-011)
- The entry heading becomes `### Q-IMPL-<WS>-NNN: <short topic>`
- Legacy bare `Q-IMPL-NNN` entries from a v3 corpus are treated as the `default`
  workstream and are NOT remapped. See `docs/spec/ws-ids.md`.

**Do NOT touch (RS-007 Q4 — provably unaffected):** the chunk-close Q-IMPL audit and
`review`'s Q-REQ/Q-SPEC/Q-IMPL content checks make no numeric-suffix assumption
(Q-REQ/Q-SPEC already use letter suffixes) and match these ids as opaque strings —
they tolerate the inserted `<WS>` segment unchanged. Do not add a numeric-suffix
parser to them.
