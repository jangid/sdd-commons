---
workstream: harness-p4
status: active
research_id: RS-HARNESSP4-001
last_updated: 2026-09-19
---

# Implementation Plan: Harness Hardening, Part 4

## Overview

This cycle closes the gap the harness-p3 verify session left open: the harness
verifies what a leaf **wrote** but nothing verifies that the orchestrator
**committed** it, and the telemetry file that should have recorded the cycle
held zero `verifier` and zero `fix` records without any reader noticing. The
implementation surface is the harness itself — `skills/sdd-orchestrate/SKILL.md`
and its `references/{write-scope,loop-control,fan-out,return-contract,
dispatch-templates,telemetry}.md`, `skills/sdd-orchestrate/USAGE.md`,
`skills/sdd-plan/SKILL.md`, `skills/sdd-verify/SKILL.md`, `CLAUDE.md`, and three
tools (`tools/sdd-scope-check-selftest.py`, `tools/sdd-telemetry.py`,
`tools/sdd-skill-lint.py`). The chunk order is the kickoff's §Scope priority
(Q-REQ-P4-F): the `COMMIT:` signal first (Chunks 0–1), then telemetry in
P2 → P3 → P1 order (Chunks 2–4, with the P1 migration *run* an operator task
after Chunk 4), then the arbitration exercise (Chunk 5), then housekeeping
(Chunks 6–7, the `[template-drift]` rule landing one chunk before the
column-0 edit it guards). A `stop` after any chunk therefore leaves V14 and
telemetry landed first and every intermediate tree lint-clean. Three items are
**exercised live** rather than declared done by walkthrough — the `COMMIT:`
rendering, the arbitration union on a wholesale-regenerated deliverable, and
the `--lint` result on the migrated live telemetry file — and are recorded
under [§Operator Tasks](#operator-tasks) and
[§Verification Hand-off](#verification-hand-off), outside the implement
fan-out.

## Conventions

- **Task types**: `[implement]` produces the change, `[spike]` produces
  findings, `[verify]` validates behaviour beyond "the gates are green".
- **Chunk headers**: `### Chunk N: <name>` per work unit; `**Depends on**:` is
  the canonical dependency signal the implement-stage fan-out parses;
  `**Delivers**:` lists the requirement ids whose traceability row the chunk's
  tasks fill (Test / Implementation columns are written by `sdd-implement`,
  never by this plan).
- **Spec-text vs skill-text**: `docs/spec/*.md` are Approved and are **not**
  edited by this plan, with **one deliberate exception**: Chunk 7 task 1 edits
  the fenced body of `docs/spec/harness-chunk-verifier.md` §Verifier Dispatch
  Template in the *same commit* as `references/dispatch-templates.md`, because
  `harness-chunk-verifier.md` §Terminal Token at Column 0 requires the two
  fences to stay byte-identical under the `[template-drift]` rule. The
  dispatched write scope for that chunk must name that one spec path; every
  other task changes only `skills/**`, `tools/**`, `CLAUDE.md` and
  `tools/fixtures/README.md` (never the fixture file itself).
- **Quality gates** (run at every chunk close — the "close-out" block of each
  chunk): `python3 tools/sdd-skill-lint.py` exits 0; `python3 tools/sdd-gc.py
  --report` stays at the 7-warning baseline (no new finding); and the
  self-test of every tool the chunk touched exits 0 — `python3
  tools/sdd-scope-check-selftest.py --self-test`, `python3 tools/sdd-telemetry.py
  --self-test`, `python3 tools/sdd-skill-lint.py --self-test`, `python3
  tools/sdd-gc.py --self-test`. Every telemetry test reads
  `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` **read-only** and
  asserts its sha256 (`tools/fixtures/README.md`) before and after; `git diff
  --stat main -- tools/fixtures/` is empty at every chunk close.
- **Independence and shared files**: Chunk 0 → 1 chain on
  `references/write-scope.md` and `tools/sdd-scope-check-selftest.py`; Chunks
  2 → 3 → 4 chain on `tools/sdd-telemetry.py` and `references/telemetry.md`
  (and the P2 → P3 → P1 order is a requirement, not a convenience); Chunk 2
  also depends on Chunk 0 because both edit `skills/sdd-orchestrate/SKILL.md`.
  Chunk 5 depends on Chunk 0 (both edit `references/loop-control.md`). Chunk 6
  depends on Chunk 1 (both edit the scope self-test) and Chunk 0 (the lint
  rows). Chunk 7 depends on Chunks 0 and 6 (`CLAUDE.md`, `SKILL.md` and the
  active `[template-drift]` rule). Nothing is marked `Depends on: None` except
  Chunk 0: this cycle's chunks form a chain by design, so the operator should
  expect a sequential implement stage. **Effort estimates**: Chunk 0 ≈ 8 h,
  Chunk 1 ≈ 8 h, Chunk 2 ≈ 9 h, Chunk 3 ≈ 10 h, Chunk 4 ≈ 5 h, Chunk 5 ≈ 3 h,
  Chunk 6 ≈ 7 h, Chunk 7 ≈ 6 h.

## Milestones

| ID | Name | Chunks | Status |
|----|------|--------|--------|
| M1 | Harness hardening, part 4 — single delivery | Chunks 0–7 + §Operator Tasks | Active |

One delivery scope; per-milestone plan files are not activated.

## Chunks

### Chunk 0: `COMMIT:` signal — the harness contract text

**Goal**: every restating surface defines or points to the post-decision
`COMMIT: COMPLETE | INCOMPLETE` closing line, its two-sha comparand table
(sequential / fan-out per-leaf / fan-out merge step), the `amend | accept |
stop` pause and the return-drift warning, and the lint enforces the two
`REQUIRED` lines.
**Depends on**: None.
**Delivers**: REQ-HARN-HARNESSP4-001, REQ-HARN-HARNESSP4-002,
REQ-HARN-HARNESSP4-003, REQ-LINT-HARNESSP4-002.
**Tasks**:
1. [x] [implement] `skills/sdd-orchestrate/references/write-scope.md` §7
   (commit ownership): add the **skill-side defining section** for the check —
   `expected` vs `landed` from `git diff --name-only --no-renames HEAD_before
   HEAD_landed` captured *before* any bookkeeping commit (never `git show
   HEAD`), the comparand table for the three modes, the two-member token with
   the `(N observed, not landed: …; M landed, not observed: …)` clause shape,
   `COMPLETE (N paths)` counting distinct paths, and the `amend | accept | stop`
   options with `amend` staging only the orchestrator's own commit and not
   re-running the write-scope check — traces to `harness-commit-fidelity.md`
   §Signal and Token Family, §Comparand Table, §Placement and the `amend |
   accept | stop` Pause (REQ-HARN-HARNESSP4-001). Files:
   `skills/sdd-orchestrate/references/write-scope.md`
2. [x] [implement] Same file, comparand table: the sequential `expected` is the
   **observed-writes set only**; `RETURN.files_written` is never an operand;
   cross-reference the return-drift warning of task 4 — traces to
   `harness-commit-fidelity.md` §Sequential `expected` Is Observed Writes Only
   (REQ-HARN-HARNESSP4-002)
3. [x] [implement] `references/loop-control.md` §5 (gate signal order): add
   item 8 "post-decision: `COMMIT:`" for sequential gates and position **2b**
   (after `SCOPE:`) for the fan-out per-leaf gate; state that no next dispatch —
   including the implement-stage review after the last chunk — is issued while
   an `INCOMPLETE` pause is unresolved; `COMMIT:` joins the pause family beside
   `RETURN: MALFORMED`, `SCOPE: VIOLATION`, `REVIEW: CONTRADICTION` and budget
   exhaustion — traces to `harness-loop-control.md` §Gate Signal Order;
   `harness-commit-fidelity.md` §Placement (REQ-HARN-HARNESSP4-001,
   REQ-HARN-HARNESSP4-003). Files: `skills/sdd-orchestrate/references/loop-control.md`
4. [x] [implement] `references/return-contract.md` §1 (or §3): add the fourth
   parser warning `RETURN drift: <k> path(s) claimed, not observed: <paths>`
   (`RETURN.files_written − observed`), a warning never a pause, excluded from
   `COMMIT:`; the inverse set is not a warning; telemetry enum `RETURN_DRIFT` —
   traces to `harness-return-contract.md` §Return-Drift Warning
   (REQ-HARN-HARNESSP4-002). Files: `skills/sdd-orchestrate/references/return-contract.md`
5. [x] [implement] `references/fan-out.md` §3a.v: the per-leaf clause —
   `expected` = the leaf's observed writes, `landed` = the union of
   `--name-only` over `git rev-list base..tip` of the leaf branch, plus the
   `RETURN.commits ⊆ rev-list` check whose failure renders a `RETURN.commits
   not on branch` clause on the same line, at position 2b; §3b: the merge-step
   comparand `PRE_MERGE..HEAD` against the union of the merged leaves' sets;
   a conflict → abort → redo compares the redo's own sets only; exactly two
   members, no `DROPPED`/third token anywhere — traces to
   `harness-commit-fidelity.md` §Fan-out: Per-Leaf and Merge-Step Clauses, No
   Third Member (REQ-HARN-HARNESSP4-003). Files: `skills/sdd-orchestrate/references/fan-out.md`
6. [x] [implement] One-sentence restatements, never the order or the table:
   `skills/sdd-orchestrate/SKILL.md` §The gate (the closing line, pointing at
   `write-scope.md` §7 and `loop-control.md` §5); `skills/sdd-orchestrate/USAGE.md`
   §7b gate fixtures gain the `COMMIT:` closing line after `proceed`;
   `CLAUDE.md` §Gate vocabulary one sentence — traces to
   `harness-commit-fidelity.md` §Restatement Surfaces (REQ-HARN-HARNESSP4-001).
   Files: `skills/sdd-orchestrate/SKILL.md`, `skills/sdd-orchestrate/USAGE.md`, `CLAUDE.md`
7. [x] [implement] `tools/sdd-skill-lint.py`: add the `REQUIRED` row
   `COMMIT: (COMPLETE \| INCOMPLETE|COMPLETE|INCOMPLETE)` for
   `references/loop-control.md` and `SKILL.md` (min 1 each), `fix:` pointing at
   `write-scope.md` §7; a file containing only `SCOPE: CLEAN` does not satisfy
   it; extend the `--self-test` mutation loop with the row — traces to
   `skill-lint-v5.md` §`REQUIRED` Row — `COMMIT: COMPLETE | INCOMPLETE`
   (REQ-LINT-HARNESSP4-002). Files: `tools/sdd-skill-lint.py`
8. [x] [verify] Walk the four spec walkthroughs on paper against the amended
   text: (a) leaf wrote `a.txt b.txt docs/plan.md`, orchestrator staged two →
   `COMMIT: INCOMPLETE (1 observed, not landed: docs/plan.md)` and the pause
   precedes the next dispatch; fully staged → `COMPLETE (3 paths)`; `stray.txt`
   also committed → the `landed, not observed` clause on the same line; a
   regeneration commit after the range → still `COMPLETE`; (b) a leaf claiming
   `docs/extra.md` unwritten → `COMPLETE` plus the drift warning; (c) an
   `INCOMPLETE` at the last chunk blocks the implement review; (d) `grep -rn
   'COMMIT: ' skills docs/spec CLAUDE.md` shows only the two members — traces
   to `harness-commit-fidelity.md` §Acceptance Criteria (REQ-HARN-HARNESSP4-001,
   -002, -003)

**Entry criteria**: None (first chunk).
**Exit criteria**: `write-scope.md` §7 is the defining section; `loop-control.md`
§5 lists item 8 and 2b and agrees item for item with
`harness-loop-control.md` §Gate Signal Order; removing either `COMMIT:` line
exits the lint 1 with the row's fix.
**Close-out**: `python3 tools/sdd-skill-lint.py` exit 0; `python3
tools/sdd-skill-lint.py --self-test` exit 0 (new row mutated); `python3
tools/sdd-gc.py --report` at the 7-warning baseline.

### Chunk 1: `COMMIT:` self-test helper, fixtures C1–C5 and the strict observed-writes set

**Goal**: the check is executable and fixture-evidenced, and every count it
renders is a count of distinct paths.
**Depends on**: Chunk 0.
**Delivers**: REQ-HARN-HARNESSP4-006, REQ-HARN-HARNESSP4-004.
**Tasks**:
1. [x] [implement] `tools/sdd-scope-check-selftest.py`: make the observation a
   **set** — `Observation.paths` de-duplicated across `porcelain_delta ∪
   committed_delta ∪ content_delta`, one entry per path with the richest
   provenance label (`committed ≻ content ≻ porcelain`); `N` in `SCOPE:
   VIOLATION (N paths)` and the `Observed writes:` line count each path once;
   add the fixture in which one path is observed by both the committed and the
   content delta and assert `N == 1` labelled `committed` — traces to
   `harness-write-scope.md` §Observed Writes Are a Strict Set
   (REQ-HARN-HARNESSP4-004). Files: `tools/sdd-scope-check-selftest.py`
2. [x] [implement] `references/write-scope.md` §3: state the de-duplication and
   label-precedence rule in one sentence — traces to `harness-write-scope.md`
   §Observed Writes Are a Strict Set (REQ-HARN-HARNESSP4-004). Files:
   `skills/sdd-orchestrate/references/write-scope.md`
3. [x] [implement] Add the pure helper `commit_check(expected: set[str],
   landed: set[str]) -> str` (no git, no I/O; `N` = distinct paths; the second
   clause is always present when non-empty, the first may be elided when empty)
   — traces to `harness-commit-fidelity.md` §Self-Test Helper and Fixtures
   (REQ-HARN-HARNESSP4-006). Files: `tools/sdd-scope-check-selftest.py`
4. [x] [implement] Add fixtures C1 (sequential omission → `INCOMPLETE (1
   observed, not landed: docs/plan.md)`, then fully staged → `COMPLETE (3
   paths)`), C2 (inverse — `stray.txt` clause on the same line), C3 (fan-out
   fast-forward, two leaf commits → `COMPLETE (2 paths)` from the range, with
   the `git show --name-only --format= HEAD` computation asserted to render a
   false `INCOMPLETE`), C4 (true merge after a bookkeeping commit → `COMPLETE`
   with the leaf's full delta; a regeneration commit after the range leaves it
   `COMPLETE`), C5 (conflict → abort → redo compares the redo's own sets →
   `COMPLETE (1 path)`, never a third member). Throwaway repos under a temp
   dir as the F-series does; ids may be renumbered to the tool's convention,
   the five scenarios are the contract — traces to `harness-commit-fidelity.md`
   §Self-Test Helper and Fixtures (REQ-HARN-HARNESSP4-006). Files:
   `tools/sdd-scope-check-selftest.py`
5. [x] [verify] Run the self-test and confirm its output lists the five
   `COMMIT:` fixtures and the strict-set fixture; apply the C3 `git show`
   mutation in a temp copy and confirm it fails with a false `INCOMPLETE`;
   confirm `commit_check({"a","b","c"}, {"a","b"})` and `commit_check(S, S)`
   render as the spec's §Verification lists — traces to
   `harness-commit-fidelity.md` §Verification / Automated
   (REQ-HARN-HARNESSP4-006, REQ-HARN-HARNESSP4-004)

**Entry criteria**: Chunk 0 complete (both chunks edit `write-scope.md` and the
self-test; the helper renders the line §7 defines).
**Exit criteria**: `--self-test` green with C1–C5 and the strict-set fixture;
the C3 mutation contract holds.
**Close-out**: `python3 tools/sdd-scope-check-selftest.py --self-test` exit 0;
`python3 tools/sdd-skill-lint.py` exit 0; gc at the 7-warning baseline.

### Chunk 2: Telemetry P2 — one record per dispatch kind and implication-derived `expected`

**Goal**: a writer that never appends can no longer report "no gap": the
orchestrator writes a record for every dispatched kind, and `summarize` derives
`expected` from cross-field implications, headline = total shortfall.
**Depends on**: Chunk 0.
**Delivers**: REQ-TELEM-HARNESSP4-001, REQ-TELEM-HARNESSP4-002,
REQ-TELEM-HARNESSP4-003.
**Tasks**:
1. [ ] [implement] `skills/sdd-orchestrate/SKILL.md` telemetry-append step and
   `references/telemetry.md` §2: state the one-record-per-dispatch rule for
   every kind (`pipeline`, `fix`, `fanout_leaf`, `verifier`, `review`, `red`)
   with the three clauses — (i) a chunk verifier gets its own `verifier` record
   and its `CHUNK_VERDICT:` is also copied onto the chunk record's
   `verdict.chunk_verdict`; (ii) every fix dispatch (stage `loop-back-to-fix`,
   per-chunk redo, `RED_BREAK`) is a `fix` record, never `pipeline`; (iii) the
   first attempt keeps its record and the redo is a further `fix` record with
   `redo` incremented and `reason` set — with worked `verifier` and `fix`
   examples carrying a non-null `chunk` — traces to `telemetry.md` §Writer
   (REQ-TELEM-HARNESSP4-001). Files: `skills/sdd-orchestrate/SKILL.md`,
   `skills/sdd-orchestrate/references/telemetry.md`
2. [ ] [implement] `tools/sdd-telemetry.py` `summarize`: replace the
   highest-`seq` `expected` with the implication formula — per session, per
   kind, `attempts(stage, chunk) = 1 + max(redo)` per `(stage, chunk)` group;
   `implied.verifier`, `implied.pipeline`, `implied.review`, `implied.red`,
   `implied.fix` (clause (a) gate decisions ∈ `{loop-back-to-fix, fix, redo}`,
   clause (b) `reason ∈ FIX_ONLY_REASONS` on a non-fix record);
   `missing.<kind>` matched per stage, never negative; `expected = highest seq
   + Σ missing`; render the `records-vs-expected:` headline and the per-kind
   `implied vs recorded` lines exactly as §Implication-Derived `expected`
   shows — traces to `telemetry.md` §Implication-Derived `expected` and the
   Headline (REQ-TELEM-HARNESSP4-002). Files: `tools/sdd-telemetry.py`
3. [ ] [implement] Same tool: the mis-typed-fix rule — an implied fix present
   as a record of another kind counts 0 toward `missing.fix` and is reported by
   `--lint` as `[mistyped-fix]` (landed fully in Chunk 3; in this chunk the
   `summarize` line already renders the spec's verbatim suffix `(0 missing;
   2 mis-typed — see --lint)`, whose `see --lint` pointer resolves once Chunk 3
   ships the `[mistyped-fix]` class); `reason:
   REVIEW` at `iteration ≥ 1` with no preceding `loop-back-to-fix` at the stage
   is the warning `[reason-review]`, never a count; `FIX_ONLY_REASONS` is parsed
   from a `const` row of the domain table, not a bare code constant — traces to
   `telemetry.md` §Implication-Derived `expected` and the Headline
   (REQ-TELEM-HARNESSP4-003). Files: `tools/sdd-telemetry.py`
4. [ ] [implement] `references/telemetry.md` §7 (Post-cycle reader — or the
   section that documents `summarize`): document the implication formula, the headline definition and
   both record shapes (p3 collapsed vs compliant redo) with the fixture's worked
   numbers — traces to `telemetry.md` §Implication-Derived `expected` and the
   Headline (REQ-TELEM-HARNESSP4-002). Files:
   `skills/sdd-orchestrate/references/telemetry.md`
5. [ ] [implement] `--self-test`: synthetic fixtures for each implication
   (verifier, redo first attempt, review, red), clause (b) (`red_break`
   pipeline record with a null-decision predecessor), a `loop-back-to-fix`
   followed by no record (1 missing fix), and the gapless negative fixture that
   includes one compliant redone chunk (`pipeline redo: 0` + `fix redo: 1`,
   both with `chunk_verdict`, plus two `verifier` records) asserting 2 implied
   verifiers / 1 implied pipeline / 0 missing [C1]; every test asserts the
   frozen fixture's sha256 before and after — traces to `telemetry.md`
   §Fixture-Based Test Contract (REQ-TELEM-HARNESSP4-001, -002, -003). Files:
   `tools/sdd-telemetry.py`
6. [ ] [verify] `python3 tools/sdd-telemetry.py summarize --file
   tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` prints `expected 39`
   against 20 records (19 missing), implement line 14 missing, verifier 11 vs 0,
   pipeline 11 vs 8 at implement, review 6 vs 2 (5 missing), red 1 vs 2 (0
   missing), fix implied 2 / recorded 0 / missing 0; `sha256sum` of the fixture
   unchanged; `git diff --stat main -- tools/fixtures/` empty — traces to
   `telemetry.md` §Acceptance Criteria (REQ-TELEM-HARNESSP4-002,
   REQ-TELEM-HARNESSP4-003)

**Entry criteria**: Chunk 0 complete.
**Exit criteria**: the fixture numbers above hold; the compliant-redo negative
fixture reads 0 missing; the writer text names where every kind's record goes.
**Close-out**: `python3 tools/sdd-telemetry.py --self-test` exit 0; `python3
tools/sdd-skill-lint.py` exit 0; gc at the 7-warning baseline; fixture sha
unchanged.

### Chunk 3: Telemetry P3 — whole-schema `--lint`, `v: 2`, `scope.widened` and the `commit` group

**Goal**: every field of every record is validated against one domain table
that both telemetry documents render, and the two new record groups are
declared, written and linted.
**Depends on**: Chunk 2.
**Delivers**: REQ-TELEM-HARNESSP4-003, REQ-TELEM-HARNESSP4-004,
REQ-TELEM-HARNESSP4-006, REQ-TELEM-HARNESSP4-007, REQ-TELEM-HARNESSP4-008
(optional, `may`).
**Tasks**:
1. [ ] [implement] `tools/sdd-telemetry.py`: make the domain table the single
   source of truth — every `group.key` with type / enum members / `[p4]` mark /
   `const` rows (`FIX_ONLY_REASONS = {red_break}`); admit `v ∈ {1, 2}` by
   membership (replacing the `v != SCHEMA_V` skip; `v: 3` still skipped and
   counted); derive the per-`v` key set from the `[p4]` marks, not a second
   constant — traces to `telemetry.md` §Schema Lint — `--lint` From One Domain
   Table; §`commit` Group (Q-IMPL-HARNESSP4-002) (REQ-TELEM-HARNESSP4-004).
   Files: `tools/sdd-telemetry.py`
2. [ ] [implement] Same tool: the `--lint [--file <path>]` subcommand — enum,
   type (`dispatch.chunk` int-or-null, counters int, shas `^[0-9a-f]{7,12}$`
   with `"HEAD"` and 40-char shas as findings, ISO-8601 UTC timestamps),
   fixed key set per `v` (`key-undeclared`, `key-missing`, the optional
   `migration` marker admitted only in its declared shape), cross-field (the two
   fix clauses and `[mistyped-fix]`, `chunk_verdict` without a `verifier` record
   for the chunk, `proceed` implement record with `head_before == head_after`,
   `commit.token` non-null on a non-committing kind); finding line `seq <n>:
   [<class>] <group.key>: <message>`; exit 1 on any finding — traces to
   `telemetry.md` §Schema Lint — `--lint` From One Domain Table
   (REQ-TELEM-HARNESSP4-004). Files: `tools/sdd-telemetry.py`
3. [ ] [implement] Declare `scope.widened` (int ≥ 0, default 0, `[p4]`) and the
   `commit` group (`token: COMPLETE | INCOMPLETE | null`, `missing_n`, `extra_n`,
   `[p4]`); `summarize` prints `widened dispatches: N` and per-session `COMMIT:
   INCOMPLETE` counts; records carrying the groups are written `v: 2`; `v: 1`
   records lint clean against the `v: 1` key set — traces to `telemetry.md`
   §`scope.widened`; §`commit` Group (REQ-TELEM-HARNESSP4-006,
   REQ-TELEM-HARNESSP4-007). Files: `tools/sdd-telemetry.py`
4. [ ] [implement] `skills/sdd-orchestrate/SKILL.md` telemetry step and
   `references/telemetry.md` §2: render the domain table rows for
   `scope.widened`, the `commit` group, the `const` row `FIX_ONLY_REASONS`, the
   `v: 2` note and the optional `migration` marker; name the writer sources —
   `scope.widened = |dispatched globs| − |template default globs|` from session
   state, `commit` copied from the gate's own `COMMIT:` rendering — with **no
   read of the telemetry file** and the statement that the table is a rendering
   of the code table; document `--lint` in §7 (reader) — traces to
   `telemetry.md` §Writer; §Record Schema; §Out-of-Loop Reader
   (REQ-TELEM-HARNESSP4-004, -006, -007). Files: `skills/sdd-orchestrate/SKILL.md`,
   `skills/sdd-orchestrate/references/telemetry.md`
5. [ ] [implement] `--self-test`: `test_schema_table_agrees` parses the `| Group
   | Key | Type / domain |` rows of `docs/spec/telemetry.md` §Record Schema and
   `references/telemetry.md` §2 (multi-key cells, `\|`-separated enum members,
   leading scalar type word, `const` rows into a separate constant set) and
   asserts equality with the code table plus `FIX_ONLY_REASONS ⊆
   dispatch.reason` [M3]; one mutation per domain class; `scope.widened: 2`
   in-domain vs a string finding; `commit {INCOMPLETE, 1, 0}` passes vs `token:
   DROPPED` fails; a mixed `v: 1`/`v: 2` fixture summarised with `skipped: 0`
   [M1]; a record carrying `FIX_ONLY_REASONS` as a key is `key-undeclared`;
   a row added on one side only fails — traces to `telemetry.md` §Schema Lint;
   §Fixture-Based Test Contract (REQ-TELEM-HARNESSP4-004, -006, -007). Files:
   `tools/sdd-telemetry.py`
6. [ ] [implement] **Optional (`may`)** — `summarize --plan <path>`: implement
   floor = `chunk_count(plan)` pipeline dispatches, doubled when any chunk
   record carries a non-null `chunk_verdict`; print `implement floor: N pipeline
   (2N with verifier); recorded implement records: M; shortfall: max(0, floor −
   M)`; `--self-test` covers a plan with a chunk that has no record. If the
   chunk's budget does not stretch to it, **do not start it** — record
   "not built" in the chunk's `RETURN:` so `sdd-verify` queues it under
   `verification.md` §Next Steps — traces to `telemetry.md` §`--plan` Floor for
   Implement-Stage Expectations (REQ-TELEM-HARNESSP4-008). Files:
   `tools/sdd-telemetry.py`
7. [ ] [verify] `--lint --file tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
   exits 1 reporting at minimum `kind: gate` (`seq` 20), header strings (`seq`
   6–13), `head_after: "HEAD"` (`seq` 5), null git heads (`seq` 6–14),
   40-character shas and undeclared `git.commit_n` (`seq` 15–20),
   `[mistyped-fix]` on `seq` 2 and 18, `[reason-review]` warnings on `seq` 3–5;
   a gapless in-domain fixture exits 0; `grep -n 'commit'
   skills/sdd-orchestrate/references/loop-control.md` shows the gate reading
   git, not telemetry; if `--plan` was built, `summarize --plan
   docs/ws/harness-p3/plan.md --file <fixture>` prints floor 8 (16 with
   verifier), no shortfall against 8 recorded, implication line still 14
   missing — traces to `telemetry.md` §Acceptance Criteria
   (REQ-TELEM-HARNESSP4-004, -006, -007, -008)

**Entry criteria**: Chunk 2 complete (the implication code and `[mistyped-fix]`
hook exist).
**Exit criteria**: the fixture's `--lint` findings match the table above; the
schema-agreement self-test passes against both documents; `v: 2` records are
summarised.
**Close-out**: `python3 tools/sdd-telemetry.py --self-test` exit 0; `python3
tools/sdd-skill-lint.py` exit 0; gc at the 7-warning baseline; fixture sha
unchanged.

### Chunk 4: Telemetry P1 — the `migrate` subcommand (code only; the live run is an operator task)

**Goal**: an operator can rewrite the 8 mis-typed `chunk` records in place,
stamped `partial`, without touching the frozen fixture; nothing in this chunk
runs against the live file.
**Depends on**: Chunk 3.
**Delivers**: REQ-TELEM-HARNESSP4-005 (code half; the run is
[§Operator Tasks](#operator-tasks) O2).
**Tasks**:
1. [ ] [implement] `tools/sdd-telemetry.py migrate --file <path> [--out
   <path>]`: rewrite every `dispatch.chunk` header string `"Chunk N"` to int
   `N` and add `"migration": {"from": "chunk-string", "at": "<date>"}` to each
   rewritten record; in place = sibling temp file → line-count check → rename;
   `--out` leaves the input untouched; idempotent (int chunk / existing marker
   left alone); **fixture guard**: any `--file` or `--out` under
   `tools/fixtures/` exits 2 with no write; the `migration` marker is admitted
   by the domain table as OPTIONAL — traces to `telemetry.md` §In-Place
   Migration of the 8 p3 Records, Stamped Partial (REQ-TELEM-HARNESSP4-005).
   Files: `tools/sdd-telemetry.py`
2. [ ] [implement] `summarize` per-chunk block: for any chunk whose records carry
   the marker render the `partial — migrated from "Chunk N"; verifier, fix and
   redo records were never written and cannot be reconstructed` stamp —
   traces to `telemetry.md` §In-Place Migration, "Stamped-partial block shape"
   (REQ-TELEM-HARNESSP4-005). Files: `tools/sdd-telemetry.py`
3. [ ] [implement] `--help` and `references/telemetry.md` §7: state the
   operator-invoked-between-sessions rule (second exception to append-only;
   never a leaf, never during a session), the fixture guard and the ordering
   (after -001..-004 land and `--lint` reports the migrated records clean on
   their typed fields); no dispatch template mentions `migrate` — traces to
   `telemetry.md` §In-Place Migration; §Out-of-Loop Reader
   (REQ-TELEM-HARNESSP4-005). Files: `tools/sdd-telemetry.py`,
   `skills/sdd-orchestrate/references/telemetry.md`
4. [ ] [implement] `--self-test`: `migrate --file <copy> --out <tmp>` yields a
   file on which `summarize` renders `partial` for chunks 0–7 naming the
   unreconstructable kinds and on which `--lint` reports no `type` finding for
   `dispatch.chunk`; a second run changes nothing; `migrate --file <fixture>`
   exits 2, no write, sha unchanged — traces to `telemetry.md` §Fixture-Based
   Test Contract (REQ-TELEM-HARNESSP4-005). Files: `tools/sdd-telemetry.py`
5. [ ] [verify] Confirm `grep -rn 'migrate' skills/sdd-orchestrate/references/dispatch-templates.md`
   is empty, `sha256sum tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
   equals the value in `tools/fixtures/README.md`, and `git diff --stat main --
   tools/fixtures/` is empty — traces to `telemetry.md` §Acceptance Criteria
   (REQ-TELEM-HARNESSP4-005)

**Entry criteria**: Chunk 3 complete (`--lint` exists to validate the migrated
records; the `migration` marker is a domain-table row).
**Exit criteria**: `migrate` self-tests green; the fixture guard holds; the
live file is **untouched** by this chunk.
**Close-out**: `python3 tools/sdd-telemetry.py --self-test` exit 0; `python3
tools/sdd-skill-lint.py` exit 0; gc at the 7-warning baseline; fixture sha
unchanged.

### Chunk 5: Arbitration — §2a fixture repair and the `regen[N]` schema, ready for the live exercise

**Goal**: `references/loop-control.md` §2a demonstrates the derived-artifact
case unambiguously and its state schema agrees with the amended spec, so the
live exercise of the union (operator task O1) has a correct rule to run
against.
**Depends on**: Chunk 0.
**Delivers**: REQ-ARB-HARNESSP4-002, REQ-ARB-HARNESSP4-003; enables
REQ-ARB-HARNESSP4-001 and the carried REQ-ARB-HARNESSP3-001 (delivered on run
evidence by O1 + §Verification Hand-off).
**Tasks**:
1. [ ] [implement] `references/loop-control.md` §2a replay fixture: `regen[1]`
   lists `docs/requirements/traceability.md §(matrix)` labelled `by:
   orchestrator`, distinct from the leaf-written `docs/ws/<id>/traceability.md`
   entry; finding `M3` names its path in full; no bare `traceability.md` remains
   in any finding line; the fixture's expected outcome (no pause on the
   regenerated file, pause on an untouched one) is unchanged — traces to
   `arbitrated-handoff.md` §§2a Replay Fixture Demonstrates the Derived-Artifact
   Case (REQ-ARB-HARNESSP4-002). Files: `skills/sdd-orchestrate/references/loop-control.md`
2. [ ] [verify] Side-by-side read: `references/loop-control.md` §2a's retained
   state schema shows `round[N]`, `fix[N]` and `regen[N]` with the `W_N` union
   and agrees with `arbitrated-handoff.md` §Retained Per-Round State as amended
   (`regen[N]` a sibling set, not a rename of `fix[N]`); fix any divergence on
   the skill side only — traces to `arbitrated-handoff.md` §Retained Per-Round
   State (REQ-ARB-HARNESSP4-003). Files (only if divergent):
   `skills/sdd-orchestrate/references/loop-control.md`
3. [ ] [verify] Confirm the fix-loop dispatch path can carry the
   regenerate-wholesale instruction without a template change: the
   `{deliverable_contract}` slot of the fix dispatch in
   `references/dispatch-templates.md` accepts free text, and `loop-control.md`
   §2a's regenerated-not-patched rule reads a wholesale rewrite as `regen[N]`
   for every section of the file. Record the finding as one line in this task;
   if a template change *is* needed, flag it as a replan trigger rather than
   editing the template here — traces to `arbitrated-handoff.md` §Live Exercise
   of the Union in harness-p4 (REQ-ARB-HARNESSP4-001, REQ-ARB-HARNESSP3-001)
4. [ ] [verify] `grep -n 'docs/requirements/traceability.md'
   skills/sdd-orchestrate/references/loop-control.md` hits inside the §2a
   fixture's `regen[1]` block with the orchestrator label; `python3
   tools/sdd-skill-lint.py` exits 0 — traces to `arbitrated-handoff.md`
   §Acceptance Criteria (REQ-ARB-HARNESSP4-002)

**Entry criteria**: Chunk 0 complete.
**Exit criteria**: the §2a fixture and schema match the Approved spec; the
live-exercise path is confirmed dispatchable as-is.
**Close-out**: `python3 tools/sdd-skill-lint.py` exit 0; gc at the 7-warning
baseline (no new finding on `arbitrated-handoff.md`).

### Chunk 6: Tooling housekeeping — `[template-drift]` lint rule and the `R`/`C` + `-z` scope fixtures

**Goal**: the four restated fenced bodies are kept byte-identical mechanically
(a prerequisite of Chunk 7), and `-z` porcelain parsing is fixture-exercised.
**Depends on**: Chunk 0, Chunk 1.
**Delivers**: REQ-LINT-HARNESSP4-001, REQ-HARN-HARNESSP4-005.
**Tasks**:
1. [ ] [implement] `tools/sdd-skill-lint.py`: the `[template-drift]` rule — a
   pair table (source `references/dispatch-templates.md` fence → restatement in
   `docs/spec/harness-chunk-verifier.md` §Verifier Dispatch Template and
   §Verdict Rule; `docs/spec/adversarial-verify.md` §Red Dispatch Template and
   §Return Contract and `RED_VERDICT:`) matched by the fence's **first line**
   anchor text; byte-for-byte comparison after stripping fence markers only (no
   whitespace normalisation); finding `[template-drift] <spec>:<line>: fenced
   body diverges from dispatch-templates.md L<n>` with the `fix:` naming
   `dispatch-templates.md` as source of record; severity fail (exit 1) — traces
   to `skill-lint-v5.md` §`[template-drift]` — Fenced Leaf Bodies Restated in
   Specs Stay Byte-Identical (REQ-LINT-HARNESSP4-001). Files:
   `tools/sdd-skill-lint.py`
2. [ ] [implement] `--self-test`: mutate one character inside the RED TEAM
   `RETURN:` block of a temp copy of `dispatch-templates.md` and assert exit 1
   with a `[template-drift]` line naming `adversarial-verify.md` and the fix;
   the shipped skill set exits 0 — traces to `skill-lint-v5.md`
   §`[template-drift]`; §Self-Test Extension (REQ-LINT-HARNESSP4-001). Files:
   `tools/sdd-skill-lint.py`
3. [ ] [implement] `tools/sdd-scope-check-selftest.py`: add the rename fixture
   (`git mv` a scoped path to an out-of-scope path during the dispatch — both
   paths enter the ambiguous and observed sets, the new path tags `OUT`, the
   rename is observed rather than cancelling) and the space-path fixture
   (`docs/notes with space.md` — `-z` keeps one record, observed and rendered as
   one path); next free F-ids — traces to `harness-write-scope.md` §`R`/`C`
   Records and `-z` Parsing Are Fixture-Exercised (REQ-HARN-HARNESSP4-005).
   Files: `tools/sdd-scope-check-selftest.py`
4. [ ] [verify] Mutation contract: in a temp copy, split porcelain output on
   newline instead of NUL → the space-path fixture fails; drop the rename's
   origin path from the ambiguous set → the `R` fixture fails; shipped
   self-test exits 0 — traces to `harness-write-scope.md` §Acceptance Criteria
   (REQ-HARN-HARNESSP4-005)
5. [ ] [verify] `python3 tools/sdd-skill-lint.py` exits 0 on the shipped set
   with `[template-drift]` active — i.e. the four bodies are byte-identical
   **today**, before Chunk 7 touches them; `grep -c '"fix"'
   tools/sdd-skill-lint.py` equals the rule-row count — traces to
   `skill-lint-v5.md` §Acceptance Criteria (REQ-LINT-HARNESSP4-001)

**Entry criteria**: Chunks 0 and 1 complete.
**Exit criteria**: `[template-drift]` is active and green; both new scope
fixtures pass and their mutations fail.
**Close-out**: `python3 tools/sdd-skill-lint.py` exit 0; `python3
tools/sdd-skill-lint.py --self-test` exit 0; `python3
tools/sdd-scope-check-selftest.py --self-test` exit 0; gc at the 7-warning
baseline.

### Chunk 7: Text housekeeping — column-0 terminal token, `research_id:` stamp order, `pending-red` wording, `CLAUDE.md` qualifier

**Goal**: the carried p3 text findings are closed, with the column-0 edit made
under the active `[template-drift]` rule on both sides in one commit.
**Depends on**: Chunk 0, Chunk 6.
**Delivers**: REQ-HARN-HARNESSP4-007, REQ-CYCID-HARNESSP4-001,
REQ-CYCID-HARNESSP4-002, REQ-REDB-HARNESSP4-001.
**Tasks**:
1. [ ] [implement] Move `CHUNK_VERDICT: PASS | FAIL` to **column 0** in the
   CHUNK VERIFIER dispatch body and its `RETURN:` block of
   `references/dispatch-templates.md` **and, in the same commit,** in the
   byte-identical fence of `docs/spec/harness-chunk-verifier.md` §Verifier
   Dispatch Template (the one Approved-spec edit of this plan — the dispatched
   write scope for this chunk must include that path); `skills/sdd-orchestrate/SKILL.md`
   §The gate states the parse rule `^CHUNK_VERDICT:` on the last non-blank
   line; `docs/spec/adversarial-verify.md` is untouched — traces to
   `harness-chunk-verifier.md` §Terminal Token at Column 0
   (REQ-HARN-HARNESSP4-007). Files: `skills/sdd-orchestrate/references/dispatch-templates.md`,
   `docs/spec/harness-chunk-verifier.md` (fence only), `skills/sdd-orchestrate/SKILL.md`
2. [ ] [implement] `skills/sdd-plan/SKILL.md` and `skills/sdd-verify/SKILL.md`
   frontmatter templates and prose: emit `research_id:` on the line
   **immediately after `status:`** (the skills follow Q-IMPL-HARNESSP3-014, whose
   text is unchanged) — traces to `cycle-identity.md` §The Stamp
   (REQ-CYCID-HARNESSP4-001). Files: `skills/sdd-plan/SKILL.md`,
   `skills/sdd-verify/SKILL.md`
3. [ ] [implement] `CLAUDE.md` §Phase Detection: both completion-signal rows
   (plan `status: complete`, `verification.md` `status: pass`) gain the inline
   qualifier "when a kickoff with one exists"; the §Cycle identity paragraph's
   three cases stay unchanged — traces to `cycle-identity.md` §`CLAUDE.md`
   Completion-Signal Rows Carry the Case-3 Qualifier Inline
   (REQ-CYCID-HARNESSP4-002). Files: `CLAUDE.md`
4. [ ] [implement] `skills/sdd-verify/SKILL.md` Step 3b / Step 6 gc criterion:
   qualify to "no new finding **on a `pending-red` cell**" and name the
   `[traceability-aggregate]` warning between the per-ws write and the
   orchestrator's regeneration as the designed handshake, expected and not a
   finding — traces to `adversarial-verify.md` §`Verified` Reads `pending-red`
   While a Red Round Is Outstanding, gc criterion wording
   (REQ-REDB-HARNESSP4-001). Files: `skills/sdd-verify/SKILL.md`
5. [ ] [verify] `grep -n '^  CHUNK_VERDICT:' skills/sdd-orchestrate/references/dispatch-templates.md`
   returns nothing and `grep -c '^CHUNK_VERDICT:'` on it is ≥ 2; `python3
   tools/sdd-skill-lint.py` exits 0 with `[template-drift]` active (both fences
   moved together); the frontmatter templates of the two skills show `status:`
   then `research_id:` on consecutive lines and this plan's own frontmatter
   does too; `grep -rn 'pending-red' docs/spec/adversarial-verify.md
   docs/spec/ws-traceability.md skills/sdd-verify/SKILL.md` shows the qualified
   wording and the named handshake warning in each place — traces to
   `harness-chunk-verifier.md`, `cycle-identity.md`, `adversarial-verify.md`
   §Acceptance Criteria (REQ-HARN-HARNESSP4-007, REQ-CYCID-HARNESSP4-001,
   REQ-REDB-HARNESSP4-001)
6. [ ] [verify] Integration sweep across the whole cycle: run every gate in
   §Conventions (four self-tests, lint, gc); `grep -rn 'COMMIT: ' skills
   docs/spec CLAUDE.md` shows only `COMPLETE`/`INCOMPLETE`; the four-layer
   table text in `skills/sdd-review/SKILL.md` and `CLAUDE.md` is unchanged
   against the pre-cycle commit; no file under `docs/requirements/**` or
   `docs/spec/**` (other than the Chunk 7 task 1 fence) differs from the
   specs-stage commit — traces to `cycle-identity.md` §Acceptance Criteria
   (no back-fill); `harness-commit-fidelity.md` §Verification / Automated
   (REQ-CYCID-HARNESSP4-002, REQ-HARN-HARNESSP4-007)

**Entry criteria**: Chunks 0 and 6 complete (`CLAUDE.md`/`SKILL.md` already
carry the `COMMIT:` sentence; `[template-drift]` is active).
**Exit criteria**: all four text findings closed; every gate green; the tree is
ready for O2 and the verify stage.
**Close-out**: `python3 tools/sdd-skill-lint.py` exit 0 (with
`[template-drift]` active); `python3 tools/sdd-gc.py --report` at the 7-warning
baseline; all four `--self-test` entry points exit 0.

## Operator Tasks

These are **not** leaf tasks: no dispatch template mentions them, no chunk
delivers them, and the implement fan-out never sees them. They are executed by
the operator at the gates named, and their evidence is what `sdd-verify` records
(§Verification Hand-off).

- [ ] **O1 — Live arbitration exercise** (REQ-ARB-HARNESSP4-001, carried
  REQ-ARB-HARNESSP3-001; `arbitrated-handoff.md` §Live Exercise of the Union in
  harness-p4). At the **first `APPROVE_WITH_FIXES`** stage review of this cycle
  — whichever stage that is, possibly this plan's own review — the operator
  directs the fix dispatch's `{deliverable_contract}` to **regenerate the
  deliverable wholesale** (rewrite, not patch). At the following review round's
  gate the operator confirms `VERDICT:` renders with **no** class (b) `REVIEW:
  CONTRADICTION` line although findings landed in the regenerated file, and
  notes the retained `regen[N]` entry (including the orchestrator-regenerated
  `docs/requirements/traceability.md` where the stage produced one, `by:
  orchestrator`). Record stage, round numbers N / N+1, regenerated paths and the
  absence of the pause in the gate text for `sdd-verify`. If no
  `APPROVE_WITH_FIXES` occurs before the verify stage, the item is **descoped at
  replan** under the cycle's DONE rule — never closed `fail`.
- [ ] **O2 — Telemetry migration of the live file** (REQ-TELEM-HARNESSP4-005;
  `telemetry.md` §In-Place Migration). **After Chunk 4 lands and before the
  verify stage is dispatched, with no orchestrator session open**: `python3
  tools/sdd-telemetry.py --lint --file .sdd/telemetry.jsonl` (record the
  pre-migration findings), then `python3 tools/sdd-telemetry.py migrate --file
  .sdd/telemetry.jsonl` (in place), then `--lint` again — the 8 p3 `chunk`
  records must report no `type` finding on `dispatch.chunk`, and `summarize`
  must render `partial` for chunks 0–7 of the p3 session. Never point `migrate`
  at `tools/fixtures/`. Keep both `--lint` outputs (line counts and finding
  classes, no record text) for the hand-off. If the pre-migration `--lint`
  shows findings on the migrated records' **typed** fields beyond the 8
  `chunk` strings, do not migrate — raise the replan trigger below.
- [ ] **O3 — Live `COMMIT:` observation** (REQ-HARN-HARNESSP4-001;
  `harness-commit-fidelity.md` §Live Exercise Required). From the first
  implement gate that runs after Chunk 0 lands in the orchestrator's own loaded
  skill text, the operator notes each `COMMIT:` line as rendered (token, counts)
  and, once, forces an omission by unstaging one observed path before the
  orchestrator commits to observe the `INCOMPLETE` pause and `amend`
  re-rendering `COMPLETE` with no scope block re-rendered. If the running
  orchestrator session predates Chunk 0 and never renders the line, the
  operator records that fact so `sdd-verify` descopes at replan rather than
  failing the row.
- [ ] **O4 — Chunk 7 write scope**. When dispatching Chunk 7 the operator widens
  the leaf's write scope by exactly one path, `docs/spec/harness-chunk-verifier.md`
  (fence only), and expects `scope.widened: 1` on that record and `SCOPE: CLEAN`.

## Replan Triggers

- If the two-sha comparand (`HEAD_before..HEAD_landed`) cannot be captured
  before the orchestrator's aggregate-regeneration bookkeeping commit in the
  real gate flow — i.e. the `sdd-orchestrate` step order forces the regeneration
  commit inside the range — → re-open `harness-commit-fidelity.md` §Marker-4
  Rooting's exclusion rule at replan rather than shipping a `COMMIT:` that
  renders `landed, not observed: docs/requirements/traceability.md` on every
  gate.
- If Chunk 5 task 3 finds that carrying the regenerate-wholesale instruction
  needs a `dispatch-templates.md` change → replan Chunk 5 to add the slot text
  before O1 runs; do not improvise the instruction in the gate.
- If no `APPROVE_WITH_FIXES` review occurs in the cycle before the verify stage
  (O1 never fires), or the live `COMMIT:` line never renders (O3), or the
  running orchestrator session's loaded skill text predates Chunk 2 and never
  writes `verifier` / `fix` records (Verification Hand-off item 4) → descope
  REQ-ARB-HARNESSP4-001 / carried REQ-ARB-HARNESSP3-001,
  REQ-HARN-HARNESSP4-001's live-render criterion, or
  REQ-TELEM-HARNESSP4-001's live-count criterion respectively, at replan under
  the DONE rule (every remaining row `pass`, nothing a deliberate `fail`); the
  operator records the predating-session fact in each case, never closing the
  row `fail`.
- If O2's pre-migration `--lint` shows findings on typed fields of the 8 p3
  `chunk` records other than the header string itself → do not migrate; replan
  REQ-TELEM-HARNESSP4-005 (the migrated block would assert more than the
  evidence supports).
- If the schema-agreement self-test (Chunk 3 task 5) cannot parse
  `docs/spec/telemetry.md` §Record Schema deterministically because the
  Approved table's cell format is irregular → replan toward a narrower parse
  (keys and enum members only) recorded as a Q-IMPL under `telemetry.md`, never
  toward generating the spec block from code (Q-REQ-P4-F ruled that out).
- If the `[template-drift]` rule (Chunk 6) finds the four bodies **already**
  divergent → stop before Chunk 7; reconcile on the skill side in a dedicated
  fix commit and record the divergence, since the p3 byte-consistency contract
  was then broken silently.
- If the live implement stage renders `COMMIT: INCOMPLETE` at more than one
  gate for the **same** root cause → the orchestrator's staging step is
  systematically wrong; replan Chunk 0 task 6's `SKILL.md` wording rather than
  amending gate by gate.

## Completed

(none yet)

## Risks

- **Same-file chain limits fan-out**: `SKILL.md`, `loop-control.md`,
  `write-scope.md` and the two tools are each edited by two or more chunks, so
  the chunks are a chain and the implement stage is effectively sequential. This
  is accepted: the kickoff's priority order is sequential anyway, and a stop
  after any chunk leaves a coherent, lint-clean tree.
- **The Approved-spec fence edit (Chunk 7 task 1)** is the only write into
  `docs/spec/**` this cycle. Mitigation: the chunk's write scope names the one
  path (O4), the leaf edits the fence body only, and `[template-drift]` proves
  the two sides equal at close.
- **Live-exercise items depend on the running session**: O1 and O3 need events
  the plan cannot schedule (an `APPROVE_WITH_FIXES` review; a gate rendering a
  line the orchestrator's loaded skill text may not yet carry). Mitigation: the
  DONE rule descopes at replan; the plan never lets them close `fail`.
- **Telemetry fixture integrity**: every telemetry test could accidentally
  open the fixture for writing. Mitigation: sha256 assertion before and after in
  every test, the `migrate` fixture guard, and `git diff --stat main --
  tools/fixtures/` at every chunk close.
- **`--lint` false findings on live `v: 2` records** if a writer field the
  orchestrator emits is missing from the domain table. Mitigation: O2's
  pre-migration `--lint` run on the live file surfaces it before verify;
  `key-undeclared` findings there go to replan, not to a silent table patch.

## Open Questions

- **Q-PLAN-P4-1 — where O1 fires.** The first `APPROVE_WITH_FIXES` of the cycle
  may already have occurred (specs review r1 amended `telemetry.md` — whether
  that loop was directed to regenerate wholesale is not recorded in any input
  to this plan) or may be this plan's own review. Default assumed: O1 applies
  to the **next** `APPROVE_WITH_FIXES` from this plan's review onward; if the
  operator confirms an earlier loop already met the contract, that evidence is
  used instead. Cited contract: `arbitrated-handoff.md` §Live Exercise of the
  Union in harness-p4; authority rule for the duplicated aggregate row per
  Q-IMPL-HARNESSP4-001 (no code change).
- **Q-PLAN-P4-2 — `--plan` floor (REQ-TELEM-HARNESSP4-008, `may`).** Built only
  if Chunk 3's budget allows after tasks 1–5; otherwise queued under
  `verification.md` §Next Steps as the spec permits. No operator decision is
  fabricated here; the leaf reports `built | not built` in its `RETURN:`.
- **Q-PLAN-P4-3 — `v: 2` writer surface.** The plan assumes the orchestrator's
  writer text in `SKILL.md` is the only place that needs the `v: 2` bump
  (Q-IMPL-HARNESSP4-002); if a dispatch template also embeds the record shape,
  Chunk 3 task 4 extends to it — inside the same write scope.

## Verification Hand-off

`docs/ws/harness-p4/verification.md` (frontmatter `status:` then
`research_id: RS-HARNESSP4-001` on the next line, per REQ-CYCID-HARNESSP4-001)
must record, beyond the per-spec acceptance criteria:

1. **Live arbitration exercise (O1)** — stage, review rounds N / N+1, the
   regenerated paths, the retained `regen[N]` entry (with the `by: orchestrator`
   aggregate where present) and the observed **absence** of a class (b)
   `REVIEW: CONTRADICTION` line; on that evidence the carried
   `REQ-ARB-HARNESSP3-001` row and `REQ-ARB-HARNESSP4-001` read `pass` in
   `docs/ws/harness-p4/traceability.md`, and the regenerated aggregate shows
   the `harness-p4` row as authoritative beside the `harness-p3` history row
   (Q-IMPL-HARNESSP4-001).
2. **Live `COMMIT:` rendering (O3)** — at least one gate's `COMMIT:` line as
   rendered (token and counts, no paths needed), its position after the commit
   and before the next dispatch, and, if forced, the `INCOMPLETE` → `amend` →
   `COMPLETE` sequence with no scope block re-rendered
   (REQ-HARN-HARNESSP4-001).
3. **`--lint` on the migrated live file (O2)** — the pre- and post-migration
   `--lint` summaries (finding classes and counts only), the `partial` stamp on
   chunks 0–7 of the p3 session in `summarize`, `sha256sum
   tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` unchanged and `git
   diff --stat main -- tools/fixtures/` empty (REQ-TELEM-HARNESSP4-005).
4. **Telemetry completeness of this cycle's own session** — `summarize` at DONE
   shows `verifier` count = chunk verifiers dispatched, `fix` count = fix
   dispatches rendered, `implied vs recorded` 0 missing for both kinds, the
   `widened dispatches` line (≥ 1, from O4) and the `COMMIT: INCOMPLETE` count
   (REQ-TELEM-HARNESSP4-001, -006, -007); `--plan` result or its §Next Steps
   entry (REQ-TELEM-HARNESSP4-008). Descope path, as O3 has: if the running
   orchestrator session's loaded skill text predates Chunk 2 and never writes
   `verifier` / `fix` records, the operator records that fact and `sdd-verify`
   descopes REQ-TELEM-HARNESSP4-001's live-count criterion at replan under the
   DONE rule rather than failing the row.
5. **gc criterion on a `pending-red` cell** — if red is enabled at the verify
   gate, the gc run after the per-ws write and before regeneration records the
   `[traceability-aggregate]` warning as expected and passes on the qualified
   criterion (REQ-REDB-HARNESSP4-001); if red is off, state so and pass on the
   text criterion.
6. **Regression base** — `merge-base(harness-p4, main)`, the first live use of
   the marker-4 regression rule (kickoff §Git integration).
7. **DONE rule** — every one of the 24 rows in `docs/ws/harness-p4/traceability.md`
   reads `pass`; anything not exercisable live is descoped at replan and listed
   under §Next Steps, never closed `fail`.
