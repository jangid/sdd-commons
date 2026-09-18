---
workstream: harness-p3
status: active
last_updated: 2026-09-18
research_id: RS-HARNESSP3-001
---

# Implementation Plan: Harness Hardening, Part 3

## Overview

This cycle hardens this repository's own SDD harness against seventeen defects
found by two live exercises of the v5 harness (the N = 3 pilot and the manual
red-team run of 2026-09-18). The implementation surface is the harness itself:
`skills/sdd-orchestrate/SKILL.md` and `skills/sdd-orchestrate/references/*.md`,
the other `skills/sdd-*/SKILL.md` files, `tools/sdd-scope-check-selftest.py`,
`tools/sdd-telemetry.py`, `CLAUDE.md` and `skills/sdd-orchestrate/USAGE.md`
(there is no repo-root `USAGE.md`). Most items are documentation-contract edits;
two carry real code (the content-hash write-scope observation with self-test
fixture F10, and the optional `summarize` backstop). The approach is to land the
independent contract changes in parallel-capable chunks (Chunks 0–7, all
dispatchable by the implement stage), integrate the orchestrator's gate surface
once, and then **exercise** the three constructed-and-unevidenced items on a real
verify stage rather than declaring them done by walkthrough. That last part is
**not** an implement chunk: it is the operator-executed section
[§Verify-Stage Acceptance Obligations](#verify-stage-acceptance-obligations),
which lives outside the implement fan-out.

## Conventions

- **Task types**: `[implement]` produces the change, `[spike]` produces
  findings, `[verify]` validates behaviour beyond "the gates are green".
- **Chunk headers**: `### Chunk N: <name>` per work unit; `**Depends on**:` is
  the canonical dependency signal the implement-stage fan-out parses.
- **Spec-text vs skill-text**: `docs/spec/*.md` are already Approved and are
  **not** edited by this plan. Every task changes the *harness* files the specs
  describe (`skills/**`, `tools/**`, `CLAUDE.md`,
  `skills/sdd-orchestrate/USAGE.md`).
- **Quality gates** (from `CLAUDE.md`, run at every chunk close):
  `python3 tools/sdd-skill-lint.py` exits 0; `python3 tools/sdd-gc.py --report`
  no worse than baseline (9 sweeps clean / 6 warnings / 40 info);
  `python3 tools/sdd-scope-check-selftest.py` passes where it applies. Three
  further `--self-test` entry points are named as acceptance criteria by Approved
  specs and are part of this cycle's gate list — run them at every chunk close in
  a chunk that touches the corresponding tool, and unconditionally in Chunk 7:
  `python3 tools/sdd-telemetry.py --self-test` exits 0 (`telemetry.md`
  §Acceptance Criteria), `python3 tools/sdd-gc.py --self-test` exits 0
  (`drift-sweep.md` §Acceptance Criteria), `python3 tools/sdd-skill-lint.py
  --self-test` exits 0 (`telemetry.md` §Acceptance Criteria).
- **Independence**: Chunks 2, 3, 4 and 5 touch disjoint files and may run
  concurrently. Chunks 0 → 1 → 6 are a chain because they share
  `references/write-scope.md` and `tools/sdd-scope-check-selftest.py`; Chunk 6
  additionally depends on Chunks 3 and 5 because it edits
  `references/loop-control.md` (also edited by Chunk 3) and
  `skills/sdd-plan/SKILL.md` + `skills/sdd-verify/SKILL.md` (also edited by
  Chunk 5). Chunk 7 depends on everything. **Effort estimates** (implement-stage
  chunks only): Chunk 0 ≈ 6 h, Chunk 1 ≈ 10 h, Chunk 2 ≈ 8 h, Chunk 3 ≈ 4 h,
  Chunk 4 ≈ 7 h, Chunk 5 ≈ 10 h, Chunk 6 ≈ 12 h, Chunk 7 ≈ 8 h.

## Chunks

### Chunk 0: Content-hash write-scope observation

**Goal**: the write-scope observation is a **content** decision, so a path that
was already dirty at snapshot time and re-touched during a dispatch is observed.
**Depends on**: None.
**Tasks**:
1. [x] [implement] Add the content-hash observation block to
   `skills/sdd-orchestrate/references/write-scope.md` §3: the
   `ambiguous_set` / `sha.before` / `sha.after` / `content_delta` contract, the
   fourth term in `observed writes`, the amended cancel bullet ("paths present
   in both snapshots cancel only when their content hash is also unchanged"),
   the deleted-path sentinel, `-z` porcelain parsing with both paths of an
   `R`/`C` record entering the ambiguous set, and the O(dirty files) cost note.
   Use the name "content-hash observation" in prose — never "the fourth
   observation" — traces to `harness-write-scope.md` §Content-Hash Observation
   (REQ-HARN-HARNESSP3-001)
2. [x] [implement] Reconcile the recorded v1 limitations in `write-scope.md` §5
   (titled "Finding format and `SCOPE:` token"): the modify-then-revert
   round-trip limitation is **unchanged**; the already-dirty blindness is
   removed from the limitation list — traces to `harness-write-scope.md`
   §Content-Hash Observation
3. [x] [implement] Implement the content-hash term in
   `tools/sdd-scope-check-selftest.py`'s `observe()` and `_porcelain_paths()`
   (`git hash-object` per Q-IMPL-HARNESSP3-001; reserved non-hash token for a
   deleted path per Q-IMPL-HARNESSP3-002) without changing `render()`, the
   `IN`/`ADVISORY`/`OUT` tags, the `N` count or the `HISTORY_REWRITE` rule —
   traces to `harness-write-scope.md` §Content-Hash Observation
4. [x] [implement] Add self-test fixture **F10** (next free id — F8 and F9 are
   taken), both halves: a path already dirty at snapshot time and re-touched by
   the leaf yields a non-empty observed-write set naming that path; the same
   fixture with the leaf leaving it untouched yields `SCOPE: CLEAN` — traces to
   `harness-write-scope.md` §Acceptance Criteria (REQ-HARN-HARNESSP3-001)
5. [x] [verify] Run `python3 tools/sdd-scope-check-selftest.py`: F1–F10 all pass,
   and F1–F9 are unchanged in output (the change alters *what counts as a
   write*, not how one is matched or rendered) — traces to
   `harness-write-scope.md` §Verification

**Entry criteria**: None (first chunk).
**Exit criteria**: self-test green including both halves of F10; `write-scope.md`
§3 carries the contract block and §5's limitation wording matches the spec;
`sdd-skill-lint.py` exits 0.

### Chunk 1: Write-scope table rows and aggregate-regeneration ownership

**Goal**: the dispatched `{write_scope}` slot is correct for marker-4 specs
dispatches, and the shared aggregate traceability is unambiguously the
orchestrator's to regenerate.
**Depends on**: Chunk 0.
**Tasks**:
1. [implement] `references/write-scope.md` §2 default scope table: the **specs**
   row names `docs/ws/<id>/traceability.md` (Spec column only) under marker `4`
   explicitly, instead of delegating to the section's marker-4 note — traces to
   `harness-write-scope.md` §Specs Row Names the Per-Workstream Traceability
   Path (REQ-HARN-HARNESSP3-004)
2. [implement] `references/write-scope.md` §2: drop
   `docs/requirements/traceability.md` from **every leaf row** for orchestrated
   dispatches, and record that the slot's omission *is* the discriminator
   (absent path → orchestrator regenerates; present path, or no dispatched scope
   at all → the skill regenerates itself) — traces to `ws-traceability.md`
   §Aggregate Regeneration Ownership (REQ-WS-HARNESSP3-001)
3. [implement] `references/write-scope.md` §7 commit-ownership table: add the
   orchestrator's post-gate aggregate-regeneration bookkeeping commit, separate
   from any leaf's commit — traces to `ws-traceability.md` §Aggregate
   Regeneration Ownership item (2)
4. [implement] `references/fan-out.md` §3e: cross-reference the new
   bookkeeping step beside the existing plan marks — traces to
   `ws-traceability.md` §Affected surfaces
5. [implement] `skills/sdd-orchestrate/SKILL.md`: add the post-gate regeneration
   step, triggered on **every** gate outcome (`proceed`, `loop-back-to-fix` and
   `stop` alike) and before the session ends, whenever a leaf wrote per-ws
   traceability rows since the last regeneration; track that with the session
   dirty flag of Q-IMPL-HARNESSP3-011 — traces to `ws-traceability.md`
   §Regeneration trigger
6. [implement] Add the marker-4 unless-clause to the four traceability-writing
   skills — `skills/sdd-requirements/SKILL.md`, `skills/sdd-specs/SKILL.md`,
   `skills/sdd-implement/SKILL.md`, `skills/sdd-verify/SKILL.md`: regenerate the
   aggregate after the per-ws write **unless dispatched with a write scope that
   omits that path** — traces to `ws-traceability.md` §Affected surfaces
7. [implement] Add self-test fixtures: a marker-4 **specs** dispatch writing
   `docs/spec/**` plus its per-ws row → both `IN`, `SCOPE: CLEAN`; an
   orchestrated marker-4 verify dispatch that also writes
   `docs/requirements/traceability.md` → `OUT`, `SCOPE: VIOLATION (1 path)`;
   the standalone marker-3 verify dispatch fixture (F3) stays `CLEAN` — traces
   to `harness-write-scope.md` §Automated
8. [verify] Walk one orchestrated marker-4 specs dispatch and one standalone
   `sdd-specs` run on paper against the amended table: the orchestrated one is
   `SCOPE: CLEAN` and does not regenerate the aggregate; the standalone one
   does. Confirm no false `VIOLATION` remains for a skill doing exactly what its
   own SKILL.md mandates — traces to `harness-write-scope.md` §Acceptance
   Criteria
9. [verify] Walk a gate resolved **`stop`** with the session dirty flag set: the
   amended `SKILL.md` step regenerates `docs/requirements/traceability.md` from
   the per-ws files and commits it **before the session ends**, i.e. the
   regeneration is not skipped because the cycle is being abandoned — traces to
   `ws-traceability.md` §Acceptance Criteria
10. [verify] Walk a gate resolved **`loop-back-to-fix`** with the dirty flag set:
    the aggregate is regenerated and committed at that gate, and the flag is
    cleared so the following fix round does not regenerate a second time with no
    intervening per-ws write — traces to `ws-traceability.md` §Acceptance
    Criteria

**Entry criteria**: Chunk 0 complete (both chunks edit `write-scope.md` and the
self-test).
**Exit criteria**: self-test green with the new fixtures; the two committed texts
that disagreed (`ws-traceability.md` Q-IMPL-011 vs `fan-out.md` §3e) now agree in
the harness files; gates green.

### Chunk 2: Leaf return conformance

**Goal**: no leaf template's `RETURN:` shape is reachable only from prose outside
its fence, and the two keys the gate arithmetic consumes both have a malformed
condition.
**Depends on**: None.
**Tasks**:
1. [implement] `references/dispatch-templates.md` — **chunk verifier** template:
   move the literal `RETURN:` key block (all twelve keys in contract order)
   inside the fenced prompt body, with `CHUNK_VERDICT: PASS | FAIL` as the
   own-line last line inside the block; delete the prose pointer as the sole
   source — traces to `harness-chunk-verifier.md` §Return Block Pinned Inside
   the Fenced Body (REQ-HARN-HARNESSP3-002)
2. [implement] `references/dispatch-templates.md` — **red team** template: move
   the literal key block inside the fence, `Rn` line shape above the block,
   `RED_VERDICT: BROKEN | HELD` as the own-line last line — traces to
   `adversarial-verify.md` §Red Dispatch Template — Key Block Inside the Fence
3. [implement] `references/dispatch-templates.md` — **review** template: pin the
   own-line `VERDICT: APPROVE │ APPROVE_WITH_FIXES │ REJECT` token inside the
   fenced body (a review still emits no `RETURN:` block by contract) — traces to
   `harness-return-contract.md` §Every Leaf Template Pins Its Return Block
4. [verify] Confirm PIPELINE, fan-out leaf and the fix re-dispatch
   (PIPELINE + `{on_fix_only}`) are already conformant and need **no** change;
   confirm the verifier and red bodies are byte-consistent across
   `references/dispatch-templates.md`, `references/return-contract.md` and the
   `SKILL.md` stubs — traces to `harness-return-contract.md` §Every Leaf
   Template Pins Its Return Block (template table)
5. [implement] `references/return-contract.md` §Parsing: add exactly one
   condition, `RETURN: MALFORMED (budget_consumed shape)` — present but not a
   map of unit → integer, checked **structurally**, not by unit vocabulary
   (Q-IMPL-HARNESSP3-004). Record beside it that the other nine keys stay a
   `RETURN: KEYS MISSING` warning, with the `blocked_writes` borderline
   reasoning written out so the boundary reads as a decision — traces to
   `harness-return-contract.md` §Malformed `budget_consumed` Is a Pause
   (REQ-HARN-HARNESSP3-003)
6. [implement] `references/return-contract.md` §3: a review finding raised
   against an artifact the fix leaf is **not** scoped to touch is carried into
   the **next pipeline dispatch's** `{deliverable_contract}` slot, not into the
   repair packet. No schema change, no `carry_to_next_dispatch:` field — traces
   to `harness-return-contract.md` §Out-of-Fix-Scope Review Findings Route to
   the Next Deliverable Contract (REQ-HARN-HARNESSP3-005)
7. [implement] `references/return-contract.md` §5: insert **step 1'** ahead of
   the heading-spec step — if the routed `Rn`'s `failures[].location` names a
   file or chunk, resolve it to the chunk whose tasks' implementation modules
   include that file (Q-IMPL-HARNESSP3-003); otherwise fall back to the
   heading spec and continue at step 2 unchanged — traces to
   `harness-return-contract.md` §Red Break → Chunk Mapping Narrows on
   `failures[].location` (REQ-REDB-HARNESSP3-001)
8. [verify] Replay the two drifting returns of 2026-09-18 against the amended
   parsing rules: a prose `budget_consumed` now pauses; the return that was
   **missing only `ledger`** still only warns (`RETURN: KEYS MISSING`), i.e. the
   new pause condition did not widen to the other nine keys. Replay both observed
   red breaks against step 1': at least one resolves to a narrower chunk than
   `all`, and neither resolves to something the old fallback would have excluded.
   Include the **negative control**: an `Rn` whose `failures[].location` names no
   usable location (absent, or a path no chunk's implementation modules contain)
   still routes `target.chunk: all` via the unchanged heading-spec fallback —
   traces to `harness-return-contract.md` §Acceptance Criteria

**Entry criteria**: None.
**Exit criteria**: every leaf template's return shape lives inside its fence; the
malformed condition is in §Parsing; §3 and §5 carry the two routing rules; gates
green.

### Chunk 3: Arbitration over regenerated artifacts

**Goal**: a review round raising findings in a wholesale-regenerated deliverable
no longer trips `REVIEW: CONTRADICTION` class (b) by construction.
**Depends on**: None.
**Tasks**:
1. [implement] `references/loop-control.md` §2a: redefine the retained per-round
   write set as
   `W_N := sections(fix[N] writes) UNION sections(regeneration writes since round N)`,
   with the existing `(file, *)` fallback and its `(file-level)` pause label
   unchanged. State it as a general **regenerated-not-patched** rule at the §2a
   level — it applies to any stage whose pipeline leaf rewrites its artifact
   wholesale (specs, plan, verification), not only to red — traces to
   `arbitrated-handoff.md` §`W_N` Includes Regeneration Writes
   (REQ-ARB-HARNESSP3-001)
2. [implement] Record the retained state as a sibling set `regen[N]` beside
   `fix[N]` rather than renaming `fix[N]` (Q-IMPL-HARNESSP3-009), and define
   "regeneration of the stage deliverable" as a **pipeline re-dispatch of the
   same stage** (Q-IMPL-HARNESSP3-010) — traces to `arbitrated-handoff.md`
   §Implementation Questions
3. [implement] `references/loop-control.md` §6: state that the arbitration
   guarantee is unchanged — the pause still catches a reviewer raising new
   Critical/Material findings on ground the previous round approved *and the
   loop did not touch*; admitting regeneration writes removes false positives
   only — traces to `arbitrated-handoff.md` §`W_N` Includes Regeneration Writes
4. [verify] Replay the observed `APPROVE → APPROVE_WITH_FIXES` red-round
   sequence (three material findings, all having paused as class (b)) against
   the amended `W_N`: none of the three pauses now, and a synthetic finding
   about a file the loop left alone **still** pauses — traces to
   `arbitrated-handoff.md` §Acceptance Criteria

**Entry criteria**: None.
**Exit criteria**: `loop-control.md` §2a carries the union contract as a
stage-general rule; the replay shows the false positives gone and the true
positive retained; gates green.

### Chunk 4: Telemetry assurance

**Goal**: a cycle that never appends a telemetry record is distinguishable from a
healthy one, at the gate and post-cycle.
**Depends on**: None.
**Tasks**:
1. [implement] `references/telemetry.md` §3: extend the gate-line family to
   `rec <n> | WRITE FAILED | OFF | .gitignore updated` and specify
   `TELEMETRY: rec <n>`, rendered on the gate **after** an append. `<n>` counts
   **successful appends this session**, is **not** `dispatch.seq`, and is a new
   session-scoped counter named `telemetry.rec` (Q-IMPL-HARNESSP3-005)
   maintained beside `dispatch.seq`. Record that an operator who sees no `rec`,
   no `OFF` and no `WRITE FAILED` line knows the append did not happen — traces
   to `telemetry.md` §Positive Gate Line (REQ-TELEM-HARNESSP3-001)
2. [implement] State explicitly in the same section that the line is never a
   read of the telemetry file — the zero-reads rule
   (REQ-TELEM-HARNESSP2-004) and the §5 non-interference proof are preserved
   intact, and the line is text — traces to `telemetry.md` §Positive Gate Line
3. [implement] `tools/sdd-telemetry.py summarize`: report a
   records-vs-expected count per session as a sibling of the existing trailing
   `skipped:` line, with expected derived **from the gate records in the file**,
   not from a gate (Q-IMPL-HARNESSP3-006). Strictly post-cycle: it must not
   influence control flow — traces to `telemetry.md` §Records-vs-Expected in
   `summarize` (REQ-TELEM-HARNESSP3-002) **[may — decided: build, see Open
   Questions Q-A]**
4. [verify] Run `python3 tools/sdd-telemetry.py summarize` against a synthetic
   `.sdd/telemetry.jsonl` with a deliberate gap: the gap is reported, the exit
   code is unchanged, and nothing in the orchestrator reads the file during a
   cycle — traces to `telemetry.md` §Verification
5. [verify] Counter walkthrough — **happy increment**: two dispatches in one
   session render `TELEMETRY: rec 1` at the first gate and `TELEMETRY: rec 2` at
   the second, with `<n>` tracked by the session-scoped `telemetry.rec` counter
   and **not** by `dispatch.seq` — traces to `telemetry.md` §Positive Gate Line
6. [verify] Counter walkthrough — **unwritable file**: with
   `.sdd/telemetry.jsonl` unwritable, the gate renders `TELEMETRY: WRITE FAILED`
   and **no** `rec` line, and `telemetry.rec` does not advance — traces to
   `telemetry.md` §Acceptance Criteria
7. [verify] Counter walkthrough — **failure between successes**: three dispatches
   where the second append fails render `rec 1`, then `WRITE FAILED`, then
   `rec 2` — not `rec 3`. This is the discriminating case for "successful appends
   this session" — traces to `telemetry.md` §Acceptance Criteria
8. [verify] Counter walkthrough — **mid-cycle opt-out**: after the operator turns
   telemetry off mid-cycle, subsequent gates render `TELEMETRY: OFF` and
   `telemetry.rec` does not advance; if telemetry is turned back on, `<n>`
   resumes from its retained value rather than restarting — traces to
   `telemetry.md` §Acceptance Criteria

**Entry criteria**: None.
**Exit criteria**: the gate-line family has a positive member; `summarize`
reports the gap; zero-reads and non-interference are re-stated and intact; gates
green.

### Chunk 5: Cycle identity and carried-forward Minors

**Goal**: a prior cycle's `status: pass` report can no longer be misread as the
current cycle's completion, and unresolved Minors survive the per-cycle
overwrite.
**Depends on**: None.
**Tasks**:
1. [implement] `skills/sdd-plan/SKILL.md`: emit `research_id:` in the plan
   frontmatter template, immediately after `status:`
   (Q-IMPL-HARNESSP3-014), copied verbatim from the active workstream's
   `kickoff.md` — never derived or invented — traces to `cycle-identity.md`
   §The Stamp (REQ-CYCID-HARNESSP3-001)
2. [implement] `skills/sdd-verify/SKILL.md` Step 6: emit the same
   `research_id:` stamp in `verification.md`'s frontmatter — traces to
   `cycle-identity.md` §The Stamp
3. [implement] State the three exhaustive comparison cases (mismatch / field
   absent / no usable discriminator) in the `§Phase Detection` blocks of
   `skills/sdd-verify`, `skills/sdd-replan`, `skills/sdd-plan`,
   `skills/sdd-implement` and `skills/sdd-orchestrate`, compared by **exact
   string equality** (Q-IMPL-HARNESSP3-015). Case 3 covers both "no kickoff" and
   "a kickoff carrying no `research_id`" (Q-IMPL-HARNESSP3-016) and skips the
   comparison entirely — cycle identity is an orchestrated-cycle discriminator,
   never a precondition for detection — traces to `cycle-identity.md` §Readers
   That Must State the Comparison (REQ-CYCID-HARNESSP3-002)
4. [implement] `CLAUDE.md` §Phase Detection table: add the same comparison to
   the completion-signal rows (`verification.md` `status: pass`, `plan.md`
   `status: complete` with every task `[x]`) — traces to `cycle-identity.md`
   §Readers That Must State the Comparison
5. [implement] Record the three explicit non-changes where they are load-bearing:
   no back-fill of existing files (they read as case 2), no cycle identity on the
   shared corpus (`docs/requirements/**`, `docs/spec/**`), and no demotion of
   `references/loop-control.md` §3's `git log -S'research_id: <id>'`
   cycle-start-date derivation — its cap arithmetic is unmodified — traces to
   `cycle-identity.md` §What Is Explicitly Not Changed
6. [implement] `skills/sdd-verify/SKILL.md` Step 6: add the carry-or-close rule
   — unresolved **Minor** entries from the previous cycle's report are either
   carried into this cycle's §Issues Found → Minor (keeping their original text
   plus a carry marker, Q-IMPL-HARNESSP3-013) or explicitly marked closed with a
   reason. Identify "the previous cycle's report" via the `research_id` stamp,
   **including case 3**, where the rule applies to whatever report the overwrite
   is about to replace, identified by its position on disk alone — absence of a
   kickoff must not suppress the rule — traces to `skill-updates.md`
   §harness-p3 (REQ-SKILL-HARNESSP3-001)
7. [verify] Walk phase detection for three synthetic `(repo, workstream)`
   states — mismatched `research_id`, absent field, and no kickoff at all — and
   confirm the readings are previous-cycle / previous-cycle / status-only. Walk
   a repo that never ran the orchestrator and confirm its `status: pass` report
   is still read as verified — traces to `cycle-identity.md` §Acceptance
   Criteria
8. [verify] Walk the carry-or-close rule over a synthetic previous
   `verification.md` holding **two** unresolved Minor entries: the new report
   contains both under §Issues Found → Minor with their original text plus a
   carry marker, **or** marks each closed with a stated reason — no Minor
   silently disappears across the per-cycle overwrite. Repeat the walkthrough
   under case 3 (no kickoff, so the previous report is identified by its position
   on disk alone) and confirm the rule still applies — traces to
   `skill-updates.md` §harness-p3 (REQ-SKILL-HARNESSP3-001)

**Entry criteria**: None.
**Exit criteria**: both stamps emitted; five `§Phase Detection` blocks and
`CLAUDE.md` state the comparison; the carry-or-close rule is in `sdd-verify`
Step 6 and works under case 3; gates green.

### Chunk 6: Red-team follow-ups

**Goal**: a second break behind the first is distinguishable from a failed fix,
the durable matrix never asserts `pass` while a red round is outstanding, and a
fix owned by no open chunk has a specified home.
**Depends on**: Chunk 1, Chunk 2, Chunk 3, Chunk 5.
*(Chunks 3 and 5 are file-contention dependencies, not input dependencies: this
chunk edits `references/loop-control.md` — also edited by Chunk 3 — and
`skills/sdd-plan/SKILL.md` / `skills/sdd-verify/SKILL.md` — also edited by
Chunk 5. Serialising them keeps the implement-stage fan-out off concurrent edits
to the same file.)*
**Tasks**:
1. [implement] In `references/loop-control.md`'s red section (mechanism) and
   `skills/sdd-orchestrate/SKILL.md` §The gate (position, see Open Questions
   Q-C): on a red round N >= 2, for each
   `BROKEN` `Rn` the orchestrator re-runs the **previous round's** routed
   `reproduce:` command (held verbatim) and renders one derived line per prior
   break, in `Rn` order (Q-IMPL-HARNESSP3-007):
   `RED: R1 new-ground (prior R6 reproduce now passes)` /
   `RED: R1 regression  (prior R6 reproduce still fails)`. The lines render
   inside the `RED_VERDICT:` block **after** red's own `Rn` lines and **before**
   the exit rule is applied — traces to `adversarial-verify.md` §New-Ground vs
   Regression on Red Round N >= 2 (REQ-REDB-HARNESSP3-002)
2. [implement] Record the declined alternative beside it: no `supersedes:` or
   `new-ground:` marker is added to red's return shape, because that would
   require handing red the previous round's findings and contradict the
   withholding default (REQ-REDB-HARNESSP2-004), and re-attacking the same
   criterion is what found the second bug — traces to `adversarial-verify.md`
   §New-Ground vs Regression
3. [implement] `skills/sdd-verify/SKILL.md`: when writing `status: pending-red`,
   write `pending-red` into the `Verified` cell of **every row it would
   otherwise have marked `pass`**; a `fail` row stays `fail` — traces to
   `adversarial-verify.md` §`Verified` Reads `pending-red`
   (REQ-REDB-HARNESSP3-003)
4. [implement] `skills/sdd-orchestrate/SKILL.md`: the existing
   `pending-red → pass` flip at DONE flips exactly those cells and regenerates
   the aggregate in the same bookkeeping step (the step added in Chunk 1) —
   traces to `adversarial-verify.md` §`Verified` Reads `pending-red`
5. [implement] Name `pending-red` as a legal `Verified` value beside `pass` and
   `fail` wherever the harness states the column's vocabulary (the per-ws
   traceability guidance in the four writing skills and
   `references/v4-workstreams.md`). Confirm by reading
   `tools/sdd-gc.py`'s `trace-empty` sweep that **no code change follows** — it
   flags only empty `Spec` cells and Implementation-filled / Test-empty rows —
   traces to `ws-traceability.md` §Legal `Verified` Cell Values
6. [implement] Add `## Post-cycle Fixes` to the plan-structure contract as
   **optional, orchestrator-owned, outside the task list**, in
   `skills/sdd-plan/SKILL.md`'s plan template and in
   `skills/sdd-replan/SKILL.md` (carry it across a rewrite, never strip it);
   state in `skills/sdd-implement/SKILL.md` that its lines are not read as
   tasks. The section is appended at the end of the plan
   (Q-IMPL-HARNESSP3-008), one line per fix:
   `- R3 — <what was broken, what was changed, path> (<sha>)` — traces to
   `adversarial-verify.md` §`## Post-cycle Fixes` in the Active Plan and
   `milestone-plans.md` §Milestone Plan File Format (REQ-REDB-HARNESSP3-004)
7. [verify] Confirm the `## Post-cycle Fixes` write is tagged `IN` by the
   implement / `RED_BREAK` default scope row (which names the active plan path,
   marker 3 `docs/plan.md` / marker 4 `docs/ws/<id>/plan.md`) — add or extend a
   self-test fixture if the existing rows do not already cover it. Add the
   **no-open-chunk fixture** explicitly: a `RED_BREAK` fix dispatched with **no
   open chunk** (so `target.chunk` resolves to nothing and the only write is the
   `## Post-cycle Fixes` append) yields `SCOPE: CLEAN` and exactly **one** new
   line under that section — this is the case Q-B answers by default assumption
   and must be exercised, not assumed — traces to
   `harness-write-scope.md` §`## Post-cycle Fixes` Is Inside the Implement /
   `RED_BREAK` Scope and `adversarial-verify.md` §Acceptance Criteria
   (REQ-REDB-HARNESSP3-004)
8. [verify] Replay the 2026-09-18 second-break sequence on paper: round 2's
   `BROKEN` on the same criterion by a different mechanism renders
   `RED: … new-ground`, and a genuinely failed fix renders
   `RED: … regression` — traces to `adversarial-verify.md` §Acceptance Criteria.
   **This is a walkthrough only and does not discharge REQ-REDB-HARNESSP3-002 —
   see §Verify-Stage Acceptance Obligations, obligation V1.**

**Entry criteria**: Chunks 1 and 2 complete (the scope row and the red return
template are inputs).
**Exit criteria**: the `RED:` derived lines are specified with their gate
position; `pending-red` propagates into the matrix and flips at DONE; the plan
contract records `## Post-cycle Fixes`; gates green.

### Chunk 7: Integration — gate surface, conventions and quality gates

**Goal**: the orchestrator's single gate surface renders every new signal in a
stated order, the repo's own conventions are updated, and every gate is green.
**Depends on**: Chunk 0, Chunk 1, Chunk 2, Chunk 3, Chunk 4, Chunk 5, Chunk 6.
**Tasks**:
1. [implement] Update the **canonical** signal order where it lives:
   `skills/sdd-orchestrate/references/loop-control.md` §5 "Gate signal order
   (REQ-ORCH-034)". That section is the per-signal detail and states so outright
   ("SKILL.md §The gate keeps the one-line summary; this is the per-signal
   detail"), so it — not `SKILL.md` — is the target for the full order. Extend
   its five-signal enumeration to the full order `RETURN.status`, `SCOPE:`,
   `CHUNK_VERDICT:`, `VERDICT:`, `RED_VERDICT:` with its `RED:` lines,
   `REVIEW: CONTRADICTION`, `TELEMETRY: rec <n>`, adding the three new signals
   (`RED:`, `TELEMETRY: rec <n>`, and `REVIEW: CONTRADICTION`'s position) with
   their per-signal detail, reconciling the lines added by Chunks 2, 3, 4 and 6
   so no two sections disagree about position — traces to
   `adversarial-verify.md` §Gate position and `telemetry.md` §Positive Gate Line
2. [implement] Keep `skills/sdd-orchestrate/SKILL.md` §The gate as the **one-line
   summary**, preserving the existing layering: name the three new signals and
   their positions in that summary and point at `references/loop-control.md` §5
   for the per-signal detail. `SKILL.md` must not restate the full order in a
   form that can diverge from §5 — traces to `adversarial-verify.md` §Gate
   position
3. [implement] Add one sentence to `CLAUDE.md` and one to
   `skills/sdd-orchestrate/references/drift-sweep.md`: prose describing
   **another** repository's artifacts (a toy clone, an evidence record, a pilot
   log) must not quote that repository's `Q-IMPL-NNN` id tokens verbatim —
   paraphrase or fence them. Record that `tools/sdd-gc.py`'s `qimpl-undefined`
   rule is **unchanged** and behaved correctly, and that the escape hatch is a
   fenced span, not an allowlist (Q-IMPL-HARNESSP3-012) — traces to
   `drift-sweep.md` §Convention: Do Not Quote Another Repository's `Q-IMPL` Ids
   (REQ-GC-HARNESSP3-001)
4. [implement] Update `CLAUDE.md` §Spec-Driven Development and
   `skills/sdd-orchestrate/USAGE.md` (there is no repo-root `USAGE.md`) to
   describe this cycle's harness behaviour in the same register as the existing
   v5 paragraphs — the content-hash observation, the pinned return blocks and
   the `budget_consumed` pause, the regenerated-not-patched arbitration rule,
   `TELEMETRY: rec <n>`, the cycle-identity comparison, and the `RED:` lines.
   **Amend every restatement of the `TELEMETRY:` family to list all four
   members**, `rec <n>` included: `CLAUDE.md` §Driver's enumeration (currently
   `TELEMETRY: WRITE FAILED | OFF | .gitignore updated`, three members) and
   `skills/sdd-orchestrate/SKILL.md` §The gate — traces to `skill-updates.md`
   §harness-p3 and `telemetry.md` §Acceptance Criteria
   (REQ-TELEM-HARNESSP3-001)
5. [verify] `python3 tools/sdd-skill-lint.py` exits 0, and
   `python3 tools/sdd-skill-lint.py --self-test` exits 0 — traces to
   `harness-write-scope.md` §Acceptance Criteria and `telemetry.md` §Acceptance
   Criteria
6. [verify] `python3 tools/sdd-gc.py --report` is no worse than the recorded
   baseline (9 sweeps clean / 6 warnings / 40 info); any new finding is either
   fixed or recorded with a reason. Include the **positive control** for the
   convention added in task 3: the `qimpl-undefined` rule still fires on a
   genuinely undefined local `Q-IMPL` id — the fence escape hatch must not have
   silenced the rule itself. Also run `python3 tools/sdd-gc.py --self-test`
   (exits 0) — traces to `drift-sweep.md` §Verification and §Acceptance Criteria
   (REQ-GC-HARNESSP3-001)
7. [verify] `python3 tools/sdd-telemetry.py --self-test` exits 0 after the
   `summarize` change of Chunk 4 task 3 — traces to `telemetry.md` §Acceptance
   Criteria (REQ-TELEM-HARNESSP3-002)
8. [verify] `python3 tools/sdd-scope-check-selftest.py` passes, F1–F10 plus the
   fixtures added in Chunks 1 and 6 — traces to `harness-write-scope.md`
   §Automated
9. [verify] Cross-spec consistency pass: the return-block bodies are
   byte-consistent across `references/dispatch-templates.md`,
   `references/return-contract.md` and the `SKILL.md` stubs; the
   aggregate-regeneration rule reads the same in `write-scope.md` §2/§7,
   `fan-out.md` §3e and the four writing skills; no `docs/spec/*.md` file was
   edited by this cycle — traces to the XSPEC sections of
   `harness-return-contract.md` and `ws-traceability.md`

**Entry criteria**: Chunks 0–6 complete.
**Exit criteria**: all quality gates green, including the three `--self-test`
entry points (`sdd-skill-lint.py`, `sdd-gc.py`, `sdd-telemetry.py`);
`references/loop-control.md` §5 states the one canonical signal order and
`SKILL.md` §The gate is a non-divergent summary of it; `CLAUDE.md` and
`skills/sdd-orchestrate/USAGE.md` describe the cycle and the `TELEMETRY:` family
reads four members everywhere; no spec file modified. This is the **last chunk
the implement stage dispatches** — the remaining obligations are operator-executed
at the verify stage.

## Verify-Stage Acceptance Obligations

**This section is operator-executed and sits OUTSIDE the implement fan-out.** It
is not a chunk; the implement stage never dispatches it and no implement leaf can
discharge it. Every item below is a stage-level action that happens during **this
cycle's own verify stage** — an implement leaf cannot drive its own cycle's verify
stage, so stating these as chunk tasks would guarantee `BLOCKED` returns or a
quiet waiver, which is exactly the "constructed and unevidenced" failure these
items exist to prevent.

**Entry criterion**: Chunk 7 is complete, all quality gates are green, and **the
verify stage has been dispatched with `red team: on`**.

**Orchestrator obligation**: when dispatching the verify stage, the orchestrator
must carry obligations V1–V5 below into that dispatch's
`{deliverable_contract}` slot, and `sdd-verify` must walk them as acceptance
criteria. They are written here as explicit acceptance obligations with their
spec references so that the dispatching operator has a single place to copy them
from; the verify stage's deliverable contract is written by the orchestrator at
dispatch time, not by this plan.

**Precondition already satisfied**: telemetry was enabled at this cycle's KICKOFF
and records are already being appended to `.sdd/telemetry.jsonl`, so V2 needs no
KICKOFF-time action — it observes the counter on the gates this cycle already
renders.

**Obligations**:

- **V1** — Drive the verify stage's red team to a **second red round**, so that
  REQ-REDB-HARNESSP3-002's derived `RED: … new-ground | regression` line is
  actually rendered from a re-run `reproduce:` command. Record in
  `verification.md` which line was rendered, from which prior `Rn`, and whether
  the operator could act on it. A walkthrough does **not** discharge this
  requirement — traces to `adversarial-verify.md` §New-Ground vs Regression on
  Red Round N >= 2 (REQ-REDB-HARNESSP3-002) [needs-exercise]
- **V2** — Observe the live telemetry counter across this cycle's gates: every
  gate after the first append carries `TELEMETRY: rec <n>` with `<n>`
  incrementing only on successful appends. At DONE,
  `python3 tools/sdd-telemetry.py summarize` reports no records-vs-expected gap
  — traces to `telemetry.md` §Positive Gate Line (REQ-TELEM-HARNESSP3-001,
  REQ-TELEM-HARNESSP3-002)
- **V3** — Exercise REQ-ARB-HARNESSP3-001 on the live fix loop of whichever stage
  regenerates its deliverable between review rounds: confirm that a finding in a
  regenerated artifact does **not** pause as class (b), and that the pause still
  fires for a file the loop left alone — traces to `arbitrated-handoff.md`
  §`W_N` Includes Regeneration Writes (REQ-ARB-HARNESSP3-001)
- **V4** — Confirm end-to-end that the `Verified` column reads `pending-red`
  while the red round is outstanding and flips to `pass` at DONE in the same
  bookkeeping step that regenerates the aggregate — traces to
  `ws-traceability.md` §Legal `Verified` Cell Values (REQ-REDB-HARNESSP3-003)
- **V5** — Re-run `python3 tools/sdd-gc.py --report` **after** V4 has produced a
  live `pending-red` cell (gc's Chunk 7 run happens before any such cell exists):
  confirm gc raises **no new finding** on a `pending-red` `Verified` cell — traces
  to `adversarial-verify.md` §Acceptance Criteria and `drift-sweep.md`
  §Verification

- **V6** — Close the `R`/`C` acceptance gap left open by Chunk 0: the criterion
  "porcelain parsing uses `-z` and enters **both** paths of an `R`/`C` record
  into the ambiguous set" is implemented but exercised by no fixture (no
  scenario renames a path, and none uses a path containing a space, quote or
  newline). Add the fixture or record it under §Next Steps with the reason —
  traces to `harness-write-scope.md` §Acceptance Criteria
  [Carried from the Chunk 0 per-chunk gate, 2026-09-18, on the chunk verifier's
  Check 3 finding; operator decision `proceed, carry both notes`.]
- **V7** — Resolve the observed-writes union edge the Chunk 0 verifier found by
  reading (no fixture reaches it): a path that is dirty at `snapshot(before)`,
  committed during the dispatch, and then dirtied again is appended twice — once
  by the content delta, once by the committed delta — so it counts twice in `N`,
  while the spec defines `observed writes` as a set union. Either collapse to
  strict set semantics or record the divergence — traces to
  `harness-write-scope.md` §Content-Hash Observation
  [Carried from the Chunk 0 per-chunk gate, 2026-09-18, Check 1 minor note 1.]

**Exit criteria**: `verification.md` records observed evidence (not a
walkthrough) for REQ-REDB-HARNESSP3-002, REQ-TELEM-HARNESSP3-001,
REQ-ARB-HARNESSP3-001 and REQ-REDB-HARNESSP3-003; any obligation that could not be
exercised is recorded under §Next Steps with the reason, not silently marked pass.

## Replan Triggers

- If the content-hash observation (Chunk 0) measures materially worse than the
  spike's probe on this repo — say > 0.5 s per snapshot on a normal dirty set —
  → re-open the snapshot mechanism question and replan Chunk 0 rather than
  shipping a slow observation on every dispatch.
- If pinning the literal key block inside every fence (Chunk 2) pushes a
  dispatch template past a workable prompt size, or the verifier and red bodies
  cannot be kept byte-consistent across three files → replan Chunk 2 toward a
  single canonical body with pointer stubs, and reconcile with
  `harness-return-contract.md` §Every Leaf Template Pins Its Return Block.
- If the regenerated-not-patched rule (Chunk 3) is found to admit a real
  contradiction — a review round raising new Critical/Material findings on
  ground the previous round approved and that the loop genuinely did not touch —
  → stop and replan the arbitration contract; the guarantee is the reason the
  pause exists.
- If obligation V1's verify stage cannot be driven to a second red round after a
  reasonable attempt → do **not** mark REQ-REDB-HARNESSP3-002 verified. Record
  it under `verification.md` §Next Steps as still `[needs-exercise]` with the
  reason, and treat that as a `fail`-class item for the cycle's acceptance, per
  the requirement's own weakest-evidence note.
- If `tools/sdd-gc.py --report` regresses below baseline in a way that Chunk 7
  cannot fix without touching a sweep's logic → replan: a sweep change is a code
  change this cycle did not scope (the gc pipe-escape fix was explicitly
  deferred at requirements).
- If any task turns out to require editing a `docs/spec/*.md` file → stop. The
  specs are Approved; a spec change is a `sdd-replan` trigger, not an
  implementation task.

## Risks

- **Three constructed, unexercised items** (REQ-REDB-HARNESSP3-002,
  REQ-ARB-HARNESSP3-001's remedy, REQ-CYCID-HARNESSP3-001/-002 and
  REQ-WS-HARNESSP3-001's discriminator): a walkthrough can make all of them look
  correct while none has run. Mitigation: §Verify-Stage Acceptance Obligations
  exists solely to exercise them at the verify stage — where they can actually
  run — and the replan trigger above forbids silently passing
  REQ-REDB-HARNESSP3-002.
- **File contention across chunks**: `references/write-scope.md`,
  `references/return-contract.md`, `skills/sdd-orchestrate/SKILL.md`,
  `skills/sdd-orchestrate/references/loop-control.md` (Chunks 3 and 6),
  `skills/sdd-plan/SKILL.md` (Chunks 5 and 6) and `skills/sdd-verify/SKILL.md`
  (Chunks 5 and 6) are each touched by more than one chunk. Mitigation:
  `**Depends on**:` serialises every chain that shares a file
  (0 → 1 → 6, 2 → 6, 3 → 6, 5 → 6, and everything → 7), so no two concurrently
  dispatched chunks edit the same file; Chunk 7 owns the single reconciliation
  pass over `loop-control.md` §5 and `SKILL.md` §The gate.
- **No test runner**: `tools/sdd-scope-check-selftest.py` is the only executable
  check for the one real code change. Mitigation: F10 is specified in both
  directions (re-touched *and* untouched), and Chunks 1 and 6 add fixtures
  rather than relying on prose review.
- **`git hash-object` cost on a large repo**: bounded to O(dirty files) by
  construction, but unmeasured outside this repo. Mitigation: the bound is
  stated in the contract; the replan trigger covers a bad measurement.
- **Documentation drift between three copies of each template body**: the
  pinned-block change multiplies the places a body appears. Mitigation: Chunk 7
  task 7 is an explicit byte-consistency check, and `sdd-skill-lint.py` covers
  the `REQUIRED` rows.

## Open Questions

- **Q-A — REQ-TELEM-HARNESSP3-002 (`may`): build or queue?** *Decided here:
  **build**, as Chunk 4 task 3.* Rationale: the spec calls it a sibling of the
  existing trailing `skipped:` line in `summarize`, so the reporting slot already
  exists and the change is small and strictly post-cycle; and it is the named
  backstop for the one residual REQ-TELEM-HARNESSP3-001 admits (no spec read
  establishes that an operator notices an *absent* gate line). **Fallback**: if
  Chunk 4 runs out of budget, queue it under `verification.md` §Next Steps with
  that reason — the `may` acceptance is conditioned for exactly this, and the
  gate line remains the primary assurance either way.
- **Q-B — Which chunk owns a `RED_BREAK` fix that lands in `## Post-cycle
  Fixes`?** Default assumed here: **none** — the section is orchestrator-owned
  and outside the task list, so such a fix never re-opens a chunk and never
  appears as a plan task. Chunk 6 task 6 writes that down, and Chunk 6 task 7
  **exercises** the no-open-chunk case with a self-test fixture rather than
  leaving it assumed (`adversarial-verify.md` requires `SCOPE: CLEAN` and exactly
  one new line under that section); if implementation finds a case where the fix
  genuinely needs a task, that is a replan, not an ad-hoc plan edit.
- **Q-C — Where does the `RED:` derived line's rendering logic live?** Default
  assumed here: **`references/loop-control.md`** owns the mechanism (it already
  holds the routed `reproduce:` lines) and `skills/sdd-orchestrate/SKILL.md`
  §The gate names only the position in the signal order — consistent with
  `loop-control.md` §5 being the canonical per-signal detail and `SKILL.md` §The
  gate the one-line summary. Chunk 6 task 1 and Chunk 7 tasks 1–2 are split on
  that boundary; if the mechanism reads better in `SKILL.md`, that is a replan of
  the layering, not an ad-hoc split.
