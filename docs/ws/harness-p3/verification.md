---
workstream: harness-p3
status: pass
last_updated: 2026-09-18
research_id: RS-HARNESSP3-001
plan_ref: docs/ws/harness-p3/plan.md
---

# Verification Report

## Summary

Blue-team verification of the `harness-p3` cycle (17 requirements, 8 implement
chunks, HEAD `b0b69be`) passes on delivered behaviour: every quality gate is
green, all seven executable fixture suites run clean (13/13 write-scope
scenarios including the four new F10-F13, gc self-test, telemetry self-test,
skill-lint self-test), and all 17 `REQ-*-HARNESSP3-*` requirements have spec,
test and implementation coverage. **No critical issues.** One red-team break —
**R1**, a telemetry schema violation live in `.sdd/telemetry.jsonl` — returned
`BROKEN` at the verify gate and is **fixed in this revision** (§R1). Two
requirements are **not discharged** this cycle and their `Verified` cells read
`fail`, not `pending-red`: REQ-REDB-HARNESSP3-002 (V1 — the second red round is
not driven to N = 2 at this writing) and REQ-ARB-HARNESSP3-001 (V3 —
fixture-backed only; no live fix loop regenerated its deliverable). Nine
findings are recorded as Minor and eighteen items under §Next Steps — all of
them contract-precision, fixture-coverage or readability items, plus one
**deferred** spec-internal gap (`arbitrated-handoff.md` §Retained Per-Round
State, specs frozen — V11); none of them is a defect in delivered behaviour, and
none is labelled `fail`. The verify stage was dispatched with
`Red team: enabled`, so this report is `status: pending-red` and every
**would-be-`pass`** `Verified` cell in `docs/ws/harness-p3/traceability.md`
reads `pending-red`; the two `fail` cells above are outside the DONE flip by
construction (§Recommendation).

## Quality Gates

All commands run at HEAD `b0b69be`, clean working tree, from the repo root.

| Gate | Status | Notes |
|------|--------|-------|
| `python3 tools/sdd-skill-lint.py` | pass | exit 0 — `OK: 21 file(s) clean, 3 warning(s)`; the 3 warnings are the `[size]` warnings on sdd-implement (434), sdd-migrate (464), sdd-orchestrate (535) — see V12 |
| `python3 tools/sdd-skill-lint.py --self-test` | pass | exit 0 — `SELF-TEST OK: all rule classes fire; fix/warn/size/backtick/allow_files fixtures pass` |
| `python3 tools/sdd-gc.py --report` (pre-V4) | pass | exit 0 — `OK: 9 sweep(s) clean, 7 warning(s), 25 info`; matches the accepted Chunk 7 baseline exactly (3 `[size]` + 4 pre-existing `qimpl-broken-ref`) |
| `python3 tools/sdd-gc.py --self-test` | pass | exit 0 — `SELF-TEST OK: sweeps 5-14 fire once each on the two-workstream fixture; counting rule D/B/D-B hold; exit codes 0/1/2; finding shape; lint pass-through; four --fix rules idempotent…` |
| `python3 tools/sdd-telemetry.py --self-test` | pass | exit 0 — `SELF-TEST OK: budget grammar, six-record fixture …, records-vs-expected (gapless + a seq gap), missing file → records: 0` |
| `python3 tools/sdd-scope-check-selftest.py` | pass | exit 0 — `OK: 13/13 scenarios passed`, F1–F13 all PASS, including the four new fixtures F10 (content-hash re-touch), F11 (marker-4 specs per-ws row), F12 (aggregate in a verify dispatch → VIOLATION), F13 (`## Post-cycle Fixes` append) |
| `python3 tools/sdd-telemetry.py summarize` (pre-R1) | pass (rendering defect) | 14 records, `runs (cycle.research_id): RS-HARNESSP3-001`, `skipped: 0`, `records-vs-expected: 1 session(s), 0 with a missing append` — but the stage row rendered `cChunk 0:0 …` and the per-chunk block printed `(no per-chunk dispatches)`. This is red break **R1** (§R1) |
| `python3 tools/sdd-telemetry.py summarize` (post-R1) | pass | exit 0 — 16 records; `redos per chunk` now renders `c?:1`, the per-chunk block states `(per-chunk block empty: 8 record(s) excluded — dispatch.chunk out of domain; see the counter below)` instead of a bare `(no per-chunk dispatches)`, and a new sibling line reads `out-of-domain dispatch.chunk: 8 record(s) (schema: int or null — telemetry.md §Record Schema)`. The live history is unchanged — the violation is now **visible**, not repaired |
| `python3 tools/sdd-telemetry.py --self-test` (post-R1) | pass | exit 0 — summary line now ends `… out-of-domain dispatch.chunk counted and folded to c?, missing file → records: 0`; the new case asserts the counter, the absence of a doubled `c` prefix, the `c?` fold and the exclusion note |
| `python3 tools/sdd-gc.py --report` (post-V4, re-run) | pass (expected delta) | exit 0 — `OK: 9 sweep(s) clean, 8 warning(s), 25 info`. The one added warning is `[traceability-aggregate] aggregate differs from regenerate(docs/ws/*/traceability.md)` — the designed handshake, not a `pending-red` finding. See V5 |

There is no compile/build/test gate beyond these: this repository's deliverable
is Markdown contracts plus four self-testing Python tools, and `CLAUDE.md`
§Quality Checks names exactly `sdd-skill-lint.py` (plus `sdd-gc.py` under the
orchestrator) as the gates.

## Acceptance Criteria

Walked per requirement, using each row's `Test` column in
`docs/ws/harness-p3/traceability.md` as the named verification. `pending-red` in
the Status column means "blue-team pass, red verdict outstanding" (Step 3b /
`docs/spec/adversarial-verify.md`).

### harness-write-scope.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| `IN`/`ADVISORY`/`OUT` is a **content** decision: a path already dirty at snapshot and re-touched is observed (REQ-HARN-HARNESSP3-001) | pending-red | `sdd-scope-check-selftest.py` **F10** ran and passed: `already-dirty path re-touched by the leaf (content-hash observation) -> SCOPE: VIOLATION (1 path) + SCOPE: CLEAN` — both arms (re-touched → VIOLATION; untouched-but-dirty → CLEAN) exercised in one scenario. `observe()` takes `content_before` `(path, sha)` pairs over the ambiguous set; `write-scope.md` §3 line 201 states `observed writes := porcelain_delta UNION committed_delta UNION content_delta` |
| The marker-4 **specs** dispatch scope names `docs/ws/<id>/traceability.md` (REQ-HARN-HARNESSP3-004) | pending-red | **F11** passed: `orchestrated marker-4 specs dispatch: spec + per-ws row, both IN -> SCOPE: CLEAN`; `write-scope.md` §2 specs row now names the path explicitly |
| Porcelain parsing uses `-z` and enters **both** paths of an `R`/`C` record into the ambiguous set | unable (implemented, unexercised) | Implemented in `snapshot()`/`ambiguous_set`; **no fixture reaches it** — no F-scenario renames a path or uses a path containing a space, quote or newline. Recorded as **V6** / §Next Steps, not claimed pass |
| `observed writes` is a set union (REQ-HARN-HARNESSP3-001, §Content-Hash Observation) | pass with a recorded divergence | Read of `observe()`: `Observation.paths` is an append-ordered list, so a path dirty at snapshot, committed during the dispatch, **then** dirtied again is appended twice (committed delta + content delta) and counts twice in the rendered `N`. Divergence from the spec's set semantics — see **V7** |

### harness-return-contract.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| Every leaf template pins its `RETURN:` block **verbatim** (REQ-HARN-HARNESSP3-002) | pending-red | Byte comparison run this stage (see **V8**): all five fenced bodies shared between `references/dispatch-templates.md` and the two restating specs are **byte-identical** (sha1 pairs `4fbd706935`, `c14becdb2c`, `7046bf9c0a` for CHUNK VERIFIER; `fdb4500cb7`, `b1edf32cd0` for RED TEAM). No automated enforcement exists — see V8 |
| A malformed `budget_consumed` shape pauses; a merely-missing non-arithmetic key warns (REQ-HARN-HARNESSP3-003) | pending-red | Chunk 2 task 8 replay (recorded in plan): prose `budget_consumed` fixtures pause, missing-only-`ledger` fixture warns; `return-contract.md` §1 carries the redrawn boundary. Fixture is a replay walkthrough, not an executable suite |
| Out-of-fix-scope writes in a fix packet are refused (REQ-HARN-HARNESSP3-005) | pending-red | `return-contract.md` §3 Rules read this stage; corroborated by **F5** (`blocked_writes docs/plan.md from a fan-out leaf -> refused`) |

### adversarial-verify.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| A red `Rn` narrows past `target.chunk: all` where a narrower owning symbol exists (REQ-REDB-HARNESSP3-001) | pending-red | Chunk 2 task 8 replay: both observed 2026-09-18 breaks narrow past `all`; negative control still routes `all`. `return-contract.md` §5 step 1' + §3 `RED_BREAK` row read this stage |
| Red round N ≥ 2 renders a derived `RED: <Rn> new-ground \| regression` line from a re-run `reproduce:` command (REQ-REDB-HARNESSP3-002) | **fail (needs-exercise — see V1)** | **Not discharged at this return.** Its `Verified` cell therefore reads `fail`, not `pending-red` (REVIEW C1: `pending-red` marks exactly the cells the DONE flip turns to `pass`, and this is not one of them). If the orchestrator drives a red round to N = 2 immediately after this dispatch and it renders the derived line, the row returns to `pending-red` at the gate. The red rounds are dispatched by the orchestrator *after* this stage returns, so no round-2 line exists yet. Contract text verified present (`loop-control.md` §2a Red round; `SKILL.md` §The gate signal order 3b). See **V1** and its placeholder subsection |
| `Verified` reads `pending-red` while a red round is outstanding, flipping to `pass` at DONE with the aggregate regeneration (REQ-REDB-HARNESSP3-003) | pending-red (first half observed) | Produced live this stage: 15 of the 17 `Verified` cells in `docs/ws/harness-p3/traceability.md` read `pending-red` — exactly the would-be-`pass` rows — written under the `Red team: enabled` slot; the two undischarged rows read `fail` and are outside the flip (REVIEW C1). The flip is the orchestrator's at DONE — see **V4** |
| A `RED_BREAK` with no open chunk appends under `## Post-cycle Fixes` only (REQ-REDB-HARNESSP3-004) | pending-red | **F13** passed: `RED_BREAK fix with no open chunk: ## Post-cycle Fixes append only -> SCOPE: CLEAN` |

### arbitrated-handoff.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| `W_N` = `sections(fix[N].written)` UNION `sections(regen[N].written)`; a finding in a regenerated artifact is not class (b) (REQ-ARB-HARNESSP3-001) | fail (not live-exercised — see V3) | `loop-control.md` §2a read this stage: `regen[N]` is present as a sibling of `fix[N]`, the `W_N` union block is stated, and the replay fixture resolves the three observed M-findings as `in W_1, no pause` while synthetic `M4` on an untouched file still pauses class (b). **No live fix loop with a regeneration occurred this cycle** — see **V3** |
| Both §Retained Per-Round State and §Contradiction Classes carry the union and the regenerated-not-patched rule | deferred (spec frozen — see V11) | Read of `docs/spec/arbitrated-handoff.md`: §Contradiction Classes **does** carry `UNION sections(regeneration writes since round N)` with the amendment note; §Retained Per-Round State's schema block still shows **only** `round[N]` and `fix[N]` — no `regen[N]`, no union prose. The skill-side `loop-control.md` §2a is correct and complete. Specs are Approved and frozen — recorded, not edited, hence **deferred** rather than `fail`: the gap is confined to the spec's internal consistency, the skill-side surface implementations actually read is correct, and no delivered behaviour is affected. This is the single label used at all four sites (§Summary, this row, §Issues Found → Minor, V4) per REVIEW C2. See **V11** |

### telemetry.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| The `TELEMETRY:` family has four members, `rec <n>` the positive one, `<n>` incrementing only on successful appends (REQ-TELEM-HARNESSP3-001) | pending-red | `telemetry.md` §3 carries the four-member family, `telemetry.rec` and the walkthrough table (happy increment / unwritable file / failure between successes / mid-cycle opt-out). Live corroboration: 14 records at `.sdd/telemetry.jsonl`, seq 1–14, one per gate this cycle — see **V2** |
| `summarize` reports a records-vs-expected gap when appends are missing (REQ-TELEM-HARNESSP3-002) | pending-red | `sdd-telemetry.py --self-test` passed, explicitly naming `records-vs-expected (gapless + a seq gap)` and `missing file → records: 0`. Live run on this cycle's file: `records-vs-expected: 1 session(s), 0 with a missing append`. **Extended this stage by red break R1**: a record whose `dispatch.chunk` violates the schema's `int or null` domain is now counted on its own `out-of-domain dispatch.chunk: N record(s)` line and folded into a single `c?` bucket instead of being silently dropped (§R1) |

### cycle-identity.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| A completion signal counts for this cycle only when `research_id:` string-equals the kickoff's; three exhaustive cases (REQ-CYCID-HARNESSP3-001) | pending-red | `sdd-verify` §Phase Detection + Step 6 carry the rule and the stamp position (line immediately after `status:`). Exercised live by this report: its `research_id: RS-HARNESSP3-001` is copied verbatim from `docs/ws/harness-p3/kickoff.md` frontmatter (`research_id: RS-HARNESSP3-001`) and string-equals it |
| The plan-completion half carries the same rule; `loop-control.md` §3 unmodified (REQ-CYCID-HARNESSP3-002) | pending-red | `docs/ws/harness-p3/plan.md` frontmatter read this stage carries `status: complete` **and** `research_id: RS-HARNESSP3-001` — matches the kickoff, so the plan reads as this cycle's completion signal |

### drift-sweep.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| Prose about another repo's artifacts must not quote its `Q-IMPL` tokens verbatim; a fenced token raises nothing, the rule itself unchanged, no allowlist (REQ-GC-HARNESSP3-001) | pending-red | `gc --report` at HEAD raises **no** `qimpl-undefined` finding despite this cycle's prose discussing other repos' ids; `gc --self-test` passes with all sweeps firing once. Chunk 7 task 6 positive control (undefined local id → exit 1; same id fenced → clean) recorded in the plan |

### skill-updates.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| Carry-or-close for unresolved Minors across the per-cycle overwrite (REQ-SKILL-HARNESSP3-001) | pending-red | Rule read in `sdd-verify` Step 6 and **applied** this stage: `docs/ws/harness-p3/verification.md` did not previously exist (`ls docs/ws/harness-p3/` → `kickoff.md plan.md traceability.md`), so there is no previous report at this path and nothing to carry. The neighbouring `docs/ws/harness-p2/verification.md` is another workstream's file and is correctly **not** a carry source |

### ws-traceability.md

| Criterion (requirement) | Status | Evidence |
|---|---|---|
| The shared aggregate is absent from every leaf write scope; its absence is the signal that regeneration is orchestrator post-gate bookkeeping (REQ-WS-HARNESSP3-001) | pending-red | **F12** passed: `orchestrated marker-4 verify dispatch also writes the shared aggregate -> SCOPE: VIOLATION (1 path)`. Exercised live: this dispatch's write scope omits `docs/requirements/traceability.md` and this stage did **not** write it |

## User-Perspective Validation

| Scenario | Status | Notes |
|---|---|---|
| An operator runs the repo's gate commands cold, from `CLAUDE.md` alone | pass | All seven commands run from the repo root with no arguments, no setup and no venv; each prints a single `OK:`/`SELF-TEST OK:` summary line and exits 0 |
| A failing gate is actionable | pass | Every `sdd-skill-lint` / `sdd-gc` finding renders `file:line: [rule] message` plus an indented `fix:` line naming the remedy |
| `summarize` is readable as a post-cycle report | partial | The stage table is wide (≈190 columns). The `redos per chunk` cell previously packed eight malformed `cChunk N:M` pairs into one column; after R1 it renders the single token `c?:1`, so the width problem is now the table's own column count, not the cell. Recorded as Minor |
| `summarize` per-chunk block on a real cycle | pass (after R1) | Before R1 it printed a bare `(no per-chunk dispatches)` while the stage table showed per-chunk data — the two views read as disagreeing, and the cause (8 records with an out-of-domain `dispatch.chunk`) was invisible. It now prints the exclusion note and the counter line, so a reader is told **why** the block is empty. The underlying writer-side violation is recorded, not rewritten |
| A reader of `CLAUDE.md` §Phase Detection learns the cycle-identity rule correctly | partial | The two completion-signal rows state the `research_id` match unconditionally; the case-3 relief is only in the paragraph below. See **V13** |

## Regressions

- **None found.** Regression base under marker `4` is
  `merge-base(harness-p3, main)`; this workstream's branch *is* `main`
  (`git merge-base HEAD main` = `b0b69be`, `git log main..HEAD` empty), so the
  base equals HEAD and the cycle's delta is the eight already-reviewed chunk
  commits. `git status --porcelain` is empty at entry — no unintended working-tree
  changes.
- No pre-existing suite regressed: `gc --report` reproduces the accepted Chunk 7
  baseline (9 clean / 7 warnings / 25 info) **exactly**, and the four
  `qimpl-broken-ref` warnings are the same four pre-existing ones
  (`deviation-protocol.md:108`, `ws-ids.md:209`, `ws-integration.md:121`,
  `ws-orchestration.md:195`), untouched by this cycle.

## Verify-Stage Acceptance Obligations

Walked per `docs/ws/harness-p3/plan.md` §Verify-Stage Acceptance Obligations.
Verdicts: `verified` (exercised, evidence recorded) / `recorded` (decided and
written down; no exercise possible or needed) / `needs-exercise` (requires an
action this stage cannot perform).

### V1 — second red round renders the derived `RED:` line — **verified (live, 2026-09-18)**

**Not discharged, and not claimed.** REQ-REDB-HARNESSP3-002's derived
`RED: <Rn> new-ground | regression` line can only be rendered by the
orchestrator, which dispatches the red rounds **after** this stage returns; a
verify leaf cannot drive its own cycle's red team. What was verified here is
only that the contract is in place: `loop-control.md` §2a §Red round defines the
`new-ground | regression` derivation and the re-run of the previous round's
`reproduce:` command, and `SKILL.md` §The gate lists it as signal 3b with
`^RED_VERDICT:` anchored parsing.

**Evidence that would discharge V1** (and nothing less): a red round N = 2 that
returns at least one `BROKEN` `Rn`, with the orchestrator rendering one derived
`RED: <Rn> new-ground` **or** `RED: <Rn> regression` line per `BROKEN` `Rn`,
where the classification came from an **actually re-run** round-1 `reproduce:`
command (the command string and its observed exit/output recorded), plus a note
of whether the operator could act on the line at the gate without further
investigation.

<!-- ORCHESTRATOR: fill the subsection below at the verify gate after red round 2. -->

#### V1 observed round-2 `RED:` lines (filled by the orchestrator at the verify gate)

The second red round was driven. Two `RED:` lines were derived, **both labels
exercised** — each by re-running the *previous* round's routed `reproduce:`
command, held verbatim, not by reasoning about it.

| Round-2 `BROKEN` `Rn` | Classified against | Round-1 `reproduce:` re-run | Observed result | Rendered line |
|---|---|---|---|---|
| R1 (`dispatch.chunk` history still malformed) | round-1 **R1**, routed `fix` | `python3 tools/sdd-telemetry.py summarize \| grep -E "cChunk\|no per-chunk"` | no lines, exit 1 — **passes** | `RED: R1 new-ground` |
| R4 (aggregate differs from regenerate) | round-1 **R6**, routed `accept` | `python3 tools/sdd-gc.py --report \| grep traceability-aggregate` | WARN still emitted, exit 0 — **still fails** | `RED: R6 regression` |

**Could the operator act on it at the gate?** Yes, and the two lines routed
differently, which is the point of the distinction:

- `new-ground` told the operator that round 2's R1 is *not* a re-raise of the
  fixed break. The round-1 defect (the reader silently dropping out-of-domain
  values) is gone; round 2 stands on separate ground — the 8 historical records
  the fix deliberately did not rewrite. The operator accepted it as a recorded
  harness-p4 item rather than re-opening a closed fix.
- `regression` told the operator that round 2's R4 re-raises ground round 1
  already covered as R6 and that the operator had already accepted. No new
  decision was warranted, and it was folded into V14 rather than routed afresh.

**Evidence quality.** This discharges `REQ-REDB-HARNESSP3-002` by exercise, not
by walkthrough: the commands were re-run against the live tree, their exit codes
observed, and the labels derived from those exit codes. The plan's fourth replan
trigger is therefore **armed but not fired**.

**Isolation note.** The round-2 leaf's own return states under its R11 that "this
dispatch is round 1" — correct from inside its context and *expected*: round
number is orchestrator state, and leaves are isolated by construction. The
derivation is the orchestrator's, which is why `references/loop-control.md` §2a
places it there. The leaf's local view being wrong about the round is evidence
the isolation held, not a defect.

### V2 — live telemetry counter — **verified**

`.sdd/telemetry.jsonl` holds **14 records** at this stage's entry, seq 1–14
contiguous, all carrying `cycle.research_id: RS-HARNESSP3-001`. The live
`summarize` run breaks them down as research 2, requirements 1, specs 1, plan 1,
implement 9 = 14 — one record per gate this cycle rendered, with the second
research record accounting for that stage's fix iteration. Observed output:

```
workstream: harness-p3   records: 14   runs (cycle.research_id): RS-HARNESSP3-001
…
skipped: 0 unknown-schema record(s)
records-vs-expected: 1 session(s), 0 with a missing append
```

**No records-vs-expected gap is reported** — this is the first live telemetry
cycle in this repo and it closed with zero missing appends, which is exactly the
negative result Q4 of the kickoff was opened by (the 2026-09-18 run rendered
`TELEMETRY: on` and appended nothing). The `TELEMETRY: rec <n>` positive line is
what carried this: `<n>` reached 14 and incremented only on successful appends.
(REQ-TELEM-HARNESSP3-001, REQ-TELEM-HARNESSP3-002.)

### V3 — arbitration over a regenerated artifact on a live fix loop — **recorded (not exercised)**

**No live fix loop that regenerated its deliverable between review rounds
occurred in this cycle.** Telemetry records one `fix iterations: 1` for each of
research, requirements, specs, plan and implement, but each of those was a patch
of the existing deliverable, not a wholesale pipeline re-dispatch, so `regen[N]`
was empty throughout and the amended `W_N` was never the operative term. The
amendment therefore remains **fixture-backed, not live-exercised** this cycle:
`loop-control.md` §2a's replay fixture replays the observed 2026-09-18 verify
sequence (round 1 `APPROVE` → verify re-dispatch → round 2 `APPROVE_WITH_FIXES`
with three Material findings) and resolves all three as `in W_1, no pause`,
while a synthetic `M4` on `docs/spec/telemetry.md:§Record Shape` — a file no loop
dispatch touched — still fires `REVIEW: CONTRADICTION (class b)`. Both halves of
the obligation (no pause on regenerated ground; pause retained on untouched
ground) are demonstrated by the fixture; neither is demonstrated live. This is
recorded, not claimed exercised. **The verify stage's own red-driven fix loop,
if the orchestrator re-dispatches this report, is the natural live exercise** —
see §Next Steps.

**Matrix consequence (REVIEW C1).** Because V3 is `recorded (not exercised)` and
not a would-be-`pass`, REQ-ARB-HARNESSP3-001's `Verified` cell reads **`fail`**,
not `pending-red`. `fail` here means "not verified in this cycle", not "broken":
§Legal `Verified` Cell Values of `docs/spec/ws-traceability.md` admits exactly
three values (`pass`, `fail`, `pending-red`) and the specs are frozen, so no
fourth "unexercised" marker can be minted this cycle. The honest reading of a
closed vocabulary is `fail`; the reason is on this line and in §Recommendation,
and the cell is excluded from the DONE flip.

### V4 — `Verified` reads `pending-red` while red is outstanding — **verified (first half)**

Produced live: `docs/ws/harness-p3/traceability.md` carries `pending-red` in the
`Verified` cell of **15 of the 17** `REQ-*-HARNESSP3-*` rows — exactly the rows
this stage would otherwise have marked `pass`. The remaining two
(REQ-REDB-HARNESSP3-002, REQ-ARB-HARNESSP3-001) read **`fail`**, because V1 is
`needs-exercise` and V3 is `recorded (not exercised)` and neither is a
would-be-`pass` row (REVIEW C1); they are therefore outside the DONE flip. The
single `deferred` label of the `arbitrated-handoff.md` row-2 criterion is a
**criterion** label in §Acceptance Criteria, not a matrix value — the matrix
vocabulary has no `deferred` cell (REVIEW C2). No other
workstream's rows were touched, and the shared aggregate
`docs/requirements/traceability.md` was **not** written (it is absent from this
dispatch's write scope — REQ-WS-HARNESSP3-001, corroborated by fixture F12). The
durable matrix therefore asserts no `pass` while the red round is outstanding,
which is precisely the falsehood Q5(c) of the kickoff was opened by.

The second half — the `pending-red → pass` flip in the same bookkeeping step
that regenerates the aggregate — is the **orchestrator's at DONE** and cannot be
performed or observed by this skill (`sdd-verify` Step 3b: "this skill never
performs that flip"). Recorded as the orchestrator's obligation; the flip's own
observation belongs at the DONE gate.

### V5 — gc raises no new finding on a `pending-red` cell — **verified (with one expected, unrelated warning)**

Ordering honoured: the `pending-red` cells of V4 were written **first**, then
`python3 tools/sdd-gc.py --report` was re-run. Observed result: exit 0,
`OK: 9 sweep(s) clean, 8 warning(s), 25 info` — 9 clean sweeps and 25 info
unchanged from the pre-V4 baseline, with **one** added warning:

```
WARN docs/requirements/traceability.md: [traceability-aggregate] aggregate differs from regenerate(docs/ws/*/traceability.md)
    fix: run tools/sdd-gc.py --fix traceability-aggregate (regenerates from docs/ws/*/traceability.md)
```

**This is not a finding on a `pending-red` cell, and it is not a defect.** It
fires on the *shared aggregate* `docs/requirements/traceability.md`, because the
per-workstream file just changed and the aggregate has not yet been regenerated.
That is the designed handshake of REQ-WS-HARNESSP3-001: the aggregate is absent
from every leaf write scope precisely so that regeneration is the orchestrator's
**post-gate** bookkeeping, and gc's sweep is the signal that the bookkeeping is
outstanding. It will clear at DONE in the same step that performs the
`pending-red → pass` flip. Reporting it as "no new findings" would have been
false, so it is recorded here in full.

**The obligation's actual claim is confirmed:** gc raised **zero** findings of
any class on the 17 live `pending-red` `Verified` cells. No matrix sweep,
`sweep_trace_empty` included, objects to the value — gc imposes no
`Verified`-column vocabulary constraint, as the Chunk 6 task 5 code read
predicted, and that prediction is now confirmed against a live `pending-red`
matrix rather than by reading alone. Had `pending-red` been an illegal cell
value to gc, this run is exactly where it would have shown.

**Note for the DONE gate**: the 7-warning baseline recorded under V12 is the
*aggregate-regenerated* baseline. A run between a per-ws write and the
orchestrator's regeneration legitimately shows 8.

### V6 — the `R`/`C` acceptance gap — **recorded (fixture not added)**

The `harness-write-scope.md` criterion "porcelain parsing uses `-z` and enters
**both** paths of an `R`/`C` record into the ambiguous set" is implemented in
`snapshot()`/`ambiguous_set` but **exercised by no fixture**: none of F1–F13
renames or copies a path, and none uses a path containing a space, quote or
newline — the two conditions that make `-z` parsing load-bearing. Adding the
fixture would require editing `tools/sdd-scope-check-selftest.py`, which is
**outside this stage's write scope**, so per the obligation's own instruction it
is recorded under §Next Steps with the reason rather than added here.
Recommended fixture shape: one scenario that `git mv`s a scoped path to an
out-of-scope path (asserting both the old and new path enter the ambiguous set,
so the rename is observed rather than cancelling) and one whose path contains a
space, asserting `-z` parsing keeps it one record.

### V7 — the observed-writes double-count edge — **recorded, with a recommendation**

**Confirmed by reading** (no fixture reaches it). `write-scope.md` §3 line 201
defines `observed writes := porcelain_delta UNION committed_delta UNION
content_delta` — a **set** union. In `tools/sdd-scope-check-selftest.py`,
`Observation.paths` is an append-ordered **list**, and the three delta terms
append independently, so a path that is dirty at `snapshot(before)`, committed
during the dispatch, and then dirtied again is appended twice — once by the
committed delta, once by the content delta — and counts **twice** in the `N` of
`SCOPE: VIOLATION (N paths)`.

**Recommendation: collapse to strict set semantics.** Reasons: (1) the rendered
token literally says `N paths`, so a doubled `N` is a false statement about a
path count, not a harmless cosmetic; (2) the operator reads `N` at a gate to size
a violation, and `2` vs `1` changes the reading; (3) the spec already says
`UNION`, so this is the implementation diverging from an Approved contract, not a
contract question. Cheapest correct fix: de-duplicate by path at render time,
keeping the **richest** provenance label when the same path arrives from more
than one term (committed ≻ content ≻ porcelain), so the `Observed writes:` line
still says how the path was seen while `N` counts distinct paths. Cost: one
function in one file plus one fixture asserting the doubled case renders
`N = 1`. This is a harness-p4 item — fixing it here would violate
"don't fix during verify".

### V8 — byte-consistency of the restated fenced bodies — **verified (identical today)**

Comparison performed this stage by extracting every fenced block from the three
files and sha1-ing the bodies. **All five shared bodies are byte-identical
today:**

| Body | `references/dispatch-templates.md` | restating spec | sha1 (first 10) |
|---|---|---|---|
| CHUNK VERIFIER dispatch (34 lines) | L264–299 | `harness-chunk-verifier.md` L65–100 | `4fbd706935` |
| CHUNK VERIFIER verdict rule (3 lines) | L320–324 | `harness-chunk-verifier.md` L112–116 | `c14becdb2c` |
| CHUNK VERIFIER `RETURN:` block (19 lines) | L345–365 | `harness-chunk-verifier.md` L125–145 | `7046bf9c0a` |
| RED TEAM dispatch (34 lines) | L390–425 | `adversarial-verify.md` L76–111 | `fdb4500cb7` |
| RED TEAM `RETURN:` block (19 lines) | L483–503 | `adversarial-verify.md` L141–161 | `b1edf32cd0` |

**Recommendation: add a `tools/sdd-skill-lint.py` rule.** The contract is
mechanically checkable in about the same code this stage just wrote — extract
fenced bodies from the named pairs, compare hashes, emit
`[template-drift] <file>:<line>: fenced body diverges from dispatch-templates.md
L<n>` with a `fix:` line. Leaving it manual is the weaker option precisely
because the contract is invisible at edit time: an editor of either side gets no
signal, and the divergence would first surface as a leaf that returns the wrong
shape. Note the specs are Approved and frozen, so the **spec** side of the pair
is stable and the rule would in practice guard the skill side — which is the side
that changes. Recorded for harness-p4, not implemented here.

### V9 — terminal-token indentation — **recorded, with a recommendation**

Current state in `references/dispatch-templates.md`:

| Token | Where | Column |
|---|---|---|
| `VERDICT: APPROVE │ APPROVE_WITH_FIXES │ REJECT` | REVIEW template, L219 | **0** |
| `RED_VERDICT: BROKEN \| HELD` | RED TEAM template, L424 and L502 | **0** |
| `CHUNK_VERDICT: PASS \| FAIL` | CHUNK VERIFIER template, L298 and L364 | **2 (indented inside the key block)** |
| `CHUNK_VERDICT: PASS \| FAIL` (verdict rule, L321/L323) | prose rule block | 0 |

So the asymmetry is real and is **inside the `RETURN:` key blocks**: the
verifier's terminal token sits with the other return keys at indent 2, while
review's and red's stand alone at column 0. `SKILL.md` anchors red's and
review's tokens with `^` (L310 `match ^VERDICT:`, L372 `^RED_VERDICT: … on the
last non-blank line`) but states the verifier's at L283 as "`CHUNK_VERDICT:` on
its own line, last" — *own line*, not *column 0*. Live dispatches this cycle
rendered `CHUNK_VERDICT:` at column 0, i.e. matching the anchored siblings
rather than the template.

**Recommendation: unify at column 0.** The three tokens are parsed the same way
by the same gate, two of the three are already `^`-anchored, and live leaves
already render the third at column 0 — so the template is the outlier, and an
indented template body invites a leaf to emit an indented token that a future
`^`-anchored parser would miss. The alternative (declare the asymmetry
deliberate) would require changing `SKILL.md` to promise non-anchored parsing for
one token only, which is strictly more contract for less. Cost: two lines in one
file plus the V8 byte-consistency update to `harness-chunk-verifier.md` — which
is an Approved spec, so this change must wait for a cycle that can amend it.
Recorded for harness-p4.

### V10 — does the §2a replay fixture demonstrate Q-IMPL-HARNESSP3-017? — **recorded: no, only implicitly**

Checked. `loop-control.md` §2a's prose **does** state the case: "The
orchestrator's own post-gate regeneration of an artifact **derived** from that
leaf's output — the shared aggregate `docs/requirements/traceability.md` — counts
with it (Q-IMPL-HARNESSP3-017)." But the replay fixture below it does **not**
exercise that clause:

```
regen[1] (verify re-dispatch): docs/ws/<id>/verification.md §Criteria, §Issues Found, …
                               docs/ws/<id>/traceability.md  §(matrix)
round 2 …                      M3 — traceability.md:§(matrix)       -> in W_1, no pause
```

`regen[1]` lists only the **per-workstream** file, which the verify leaf writes
itself; the orchestrator-regenerated **shared aggregate**
`docs/requirements/traceability.md` — the artifact Q-IMPL-HARNESSP3-017 exists to
cover — appears nowhere in the fixture. And `M3` names `traceability.md` **bare**,
so a reader cannot tell which of the two files the finding is on; if read as the
aggregate, the fixture would be asserting the Q-IMPL-017 case, but only by an
ambiguity. **Verdict: the fixture demonstrates the leaf-written case and leaves
the derived-artifact case undemonstrated.** Recommended repair (harness-p4, and
it is skill-side text only): add `docs/requirements/traceability.md §(matrix)` to
`regen[1]` as an explicitly labelled orchestrator-regenerated entry, and
disambiguate `M3` by writing its path in full.

### V11 — arbitrated-handoff.md §Retained Per-Round State — **recorded: the gap is real**

The spec's acceptance criterion says **both** §Retained Per-Round State and
§Contradiction Classes carry the union and the regenerated-not-patched rule.
Read this stage:

- §Contradiction Classes — **carries it.** `W_N = sections(fix[N].written)
  **UNION** sections(regeneration writes since round N) [Amended 2026-09-18,
  REQ-ARB-HARNESSP3-001 — …]`.
- §Retained Per-Round State — **does not.** Its schema block still shows only
  `round[N]` and `fix[N]`; there is no `regen[N]` line and no union prose. A
  reader who takes that section as the schema of record would build the
  pre-amendment state.

The skill-side surface that implementations actually read,
`references/loop-control.md` §2a, **is** complete — it carries `regen[N]` as an
explicit sibling with the Q-IMPL-HARNESSP3-009/-010/-017 rationale and the `W_N`
union block. So the defect is confined to the spec's own internal consistency
and does not reach behaviour. **Specs are Approved and frozen this cycle — the
gap is recorded, the spec is not edited.** Repair for a cycle that can amend
specs: add the `regen[N]` line to §Retained Per-Round State's schema block so it
matches `loop-control.md` §2a, which is the pasted-from source it claims to
mirror.

### V12 — the three over-threshold skills — **recorded, with a recommendation**

Measured this stage (`sdd-skill-lint.py`, threshold 400):

| File | Lines | Over by |
|---|---|---|
| `skills/sdd-implement/SKILL.md` | 434 | 34 |
| `skills/sdd-migrate/SKILL.md` | 464 | 64 |
| `skills/sdd-orchestrate/SKILL.md` | 535 | 135 |

The gc baseline moved 6 → 7 warnings this cycle and the operator accepted it at
the Chunk 5 gate; that accounts for the third file crossing.

**Recommendation: record the new baseline as intentional, and do not split or
raise.** Reasoning: (1) *Don't raise the threshold* — 400 is doing its job; it
caught a real growth trend three times, and moving it to ~550 would silence the
signal for every future skill while buying nothing, since the warning is already
non-blocking. (2) *Don't split these three now* — `CLAUDE.md` §Conventions itself
says "size is a soft signal, not a hard limit" and asks that skills stay
*cohesive*; `sdd-orchestrate` is a driver whose gate vocabulary is only
comprehensible read end-to-end, and it already delegates its bulk to nine
`references/` files. A split driven by a line count rather than by a cohesion
argument would make the entry point *less* useful. (3) The honest action is to
make the acceptance explicit rather than let three permanent warnings train the
operator to skim gc output — so the three files should be reviewed for
cohesion-driven extraction **on their own merits** in a later cycle, and until
then 7 warnings is the recorded baseline for `harness-p3`. The regression rule is stated against a **baseline**, not against fixed
constants: **at the aggregate-regenerated baseline, any unexplained movement in
the gc counts is a regression.** The baseline recorded for `harness-p3` is 9
clean sweeps / 7 warnings / 25 info, and the only *explained* movement is the
`[traceability-aggregate]` warning that legitimately appears between a per-ws
write and the orchestrator's regeneration (V5) — which is why the count must be
read after that regeneration, and why a run showing 8 in that window is not a
regression.

### V13 — `CLAUDE.md` completion-signal rows — **recorded: yes, qualify inline**

Confirmed by reading `CLAUDE.md` §Phase Detection. The two completion-signal
rows read "**`research_id` matches the kickoff's**" with no qualifier, while the
case-3 relief — no kickoff, or a kickoff without `research_id` → the comparison
is skipped entirely — lives only in the §Cycle identity paragraph beneath the
table. A reader who consults the table alone (which is what a table is for) will
conclude that a repo with no kickoff can never read its own `status: pass`
report as verified, which is the exact opposite of the spec's intent and of what
`sdd-verify` §Phase Detection case 3 implements.

**Recommendation: carry the qualifier inline** — e.g. "**`research_id` matches
the kickoff's**, when a kickoff with one exists". Six words per row, it makes
the table independently correct, and it costs nothing in the paragraph below,
which still carries the three-case detail. Recorded for harness-p4 (editing
`CLAUDE.md` is outside this stage's write scope).

### V14 — the orchestrator-side commit blind spot — **recorded as a harness-p4 lead**

**The defect, as observed this cycle.** The write-scope check answers "what did
the **leaf** write?" — it snapshots before dispatch, observes after, and renders
`SCOPE: CLEAN | VIOLATION`. Nothing anywhere in the harness answers the next
question: "did the **orchestrator** then commit everything it observed?" Chunk 7
is the live instance: its `CLAUDE.md` edits were observed, classified `IN`, the
gate rendered `SCOPE: CLEAN`, and the path was nevertheless omitted from the
commit's `git add`. The omission survived the per-chunk gate, the stage gate and
the commit, and was caught only by a later human read — repaired at `16e240b`
("fix(harness): commit the CLAUDE.md half of Chunk 7").

**Why the existing checks cannot catch it.** Every current signal is computed
*before* the commit: `SCOPE:` reads the working tree, `CHUNK_VERDICT:` reads the
leaf's return, `VERDICT:` reads the review. The commit is the last unobserved
step in the loop, and it is performed by the one actor — the orchestrator — that
no leaf and no verifier inspects. `SCOPE: CLEAN` is therefore actively
misleading here: it truthfully reports that the leaf stayed in scope while the
work it reports on silently fails to land.

**Proposed remedy (harness-p4).** At the moment the orchestrator commits on
`proceed`, compare the leaf's `files_written` (the `RETURN:` key, now pinned
verbatim by REQ-HARN-HARNESSP3-002 and therefore reliably present) plus the
observed-writes set against the **commit's own diff** (`git show --name-only
--format= HEAD`), and surface any path in the former but not the latter at the
gate — e.g. `COMMIT: INCOMPLETE (1 path observed, not committed: CLAUDE.md)`
against a positive `COMMIT: COMPLETE (N paths)`. It needs no new artifact, no new
leaf and no new counter, it reuses two sets the harness already computes, and it
closes the loop's last unobserved step. Note it would also have caught the
inverse error — the orchestrator committing a path no leaf wrote.

**This cycle records it; it does not fix it.** It is the natural lead item for
harness-p4, alongside V7 (set semantics), V8 (template-drift lint rule), V9
(token column), V10 (fixture repair) and V11 (spec-side `regen[N]` line).

## Red Team

Round 1 of the adversarial verify executor (`docs/spec/adversarial-verify.md`)
returned `RED_VERDICT: BROKEN` with one break. It is **fixed**, not accepted, so
no `- Rn accepted at gate …` line is filed under §Issues Found.

### R1 — `dispatch.chunk` carries the header string, and the reader hides it — **fixed this stage**

**The break.** `docs/spec/telemetry.md` §Record Schema fixes `dispatch.chunk` to
`int or null`. The live `.sdd/telemetry.jsonl` records 6–13 carry the **strings**
`"Chunk 0"` … `"Chunk 7"`. Two consequences, both reproduced by re-running the
reader: (a) the stage row interpolated the malformed value verbatim into the
`c{c}:{n}` cell and rendered `cChunk 0:0 cChunk 1:1 …` — a doubled `c` prefix;
(b) `chunk_rows()`'s `if not isinstance(ch, int): continue` dropped every such
record from the per-chunk block, which printed `(no per-chunk dispatches)`, and
the record was **not** counted in `skipped: N unknown-schema record(s)` — so a
writer-side schema violation left no trace anywhere in the report.

`reproduce:` `python3 tools/sdd-telemetry.py summarize | grep -E "cChunk|no per-chunk"`
— before the fix this printed both a `cChunk …` cell and a bare
`(no per-chunk dispatches)`; after the fix it prints **neither** (verified: the
grep returns no lines), and the two explanatory lines appear in their place.

**Fix, part 1 — reader (`tools/sdd-telemetry.py`).** Three changes, all
observation-only:

- `_chunk_label()` renders `cN` for an int, `c-` for null and a single `c?`
  bucket for anything else, and `stage_rows()` now keys `redo_by_chunk` by that
  label — so a malformed value can no longer be interpolated verbatim. (`bool`
  is excluded explicitly: it is an `int` subclass and is not a chunk number.)
- `out_of_domain_chunks()` counts records whose `dispatch.chunk` is neither an
  int nor null, and `summarize()` prints
  `out-of-domain dispatch.chunk: N record(s) (schema: int or null — telemetry.md §Record Schema)`
  as a **sibling of the `skipped:` line**. `skipped` itself is left alone: it
  means "torn line or unknown `v`", and these records parse cleanly, so widening
  it would have blurred two different failures into one number.
- The per-chunk block never prints a bare `(no per-chunk dispatches)` when such
  records exist: it prints
  `(per-chunk block empty: N record(s) excluded — dispatch.chunk out of domain; see the counter below)`,
  so the empty block states its own cause. (A block that has valid rows *and*
  excluded records prints the table plus an exclusion note.)

**No record in `.sdd/telemetry.jsonl` was rewritten, migrated or deleted** — the
history stays as observed evidence, which is why the live counter reads 8.

**Self-test.** `--self-test` gains a case built from the live break: two records
carrying `"chunk": "Chunk 0"` / `"Chunk 1"`, asserting the counter line, the
absence of any `cChunk` substring, the `c?:1` fold, the exclusion note, that
`chunk_rows()` still returns `[]`, and that a clean report renders
`out-of-domain dispatch.chunk: 0 record(s)`. Exit 0.

**Fix, part 2 — writer contract
(`skills/sdd-orchestrate/references/telemetry.md`).** The orchestrator is the
only writer, so the domain is enforced nowhere but in its own procedure text.
The §2 schema row now reads "int or null — the **integer N parsed** from the
`### Chunk N:` header, **never** the header string … and never a quoted digit;
`null` for every non-chunk dispatch", and a new paragraph beneath the
resume-class rule (**`dispatch.chunk` is a number, not a heading**) states it at
the point a writer reads the schema, names both out-of-domain forms
(`"Chunk 3"`, `"3"`), and explains that a violating record is *not* in `skipped:`
but on the out-of-domain counter. `docs/spec/**` was not touched: the spec is
already correct and frozen — the writer was wrong, not the contract.

## Issues Found

### Critical (blocks release)

- None.

### Minor (can ship, fix later)

- **Red round 2, R1 — accepted at the verify gate.** The R1 fix made the schema
  violation *visible* (`out-of-domain dispatch.chunk: 8 record(s)`) but repaired
  nothing: the 8 records this cycle already wrote still carry `"Chunk N"` as a
  string, so **harness-p3's per-chunk metrics are permanently unrecoverable** —
  the per-chunk block will read `(per-chunk block empty: 8 record(s) excluded …)`
  for this cycle forever. Accepted deliberately: `.sdd/telemetry.jsonl` is this
  cycle's observed evidence and rewriting it mid-verification would edit the
  record under audit. A `--fix`/migration mode is a harness-p4 candidate.
  Red's framing is worth preserving verbatim: *visibility is not repair*.
- **Red round 2, R4 — accepted at the verify gate, folded into V14.** The shared
  aggregate differs from `regenerate(docs/ws/*/traceability.md)` for the whole
  window between the per-ws write and the orchestrator's post-gate regeneration,
  and — red's actual point — **nothing mechanical blocks DONE on it**; the
  invariant is held only by the orchestrator's prose promise to regenerate. This
  is the **third independent sighting** of the V14 blind spot in this cycle
  (blue found it in Chunk 7's dropped `git add`; the review found it as C1, an
  unexercised requirement about to flip to `pass`; red found it here, from a
  direction neither of the others took). Every check in this harness runs
  *before* the orchestrator's own commit step, so the orchestrator's steps are
  the unobserved ones. That convergence is this cycle's strongest finding and
  is carried to harness-p4 under V14.
- `docs/spec/arbitrated-handoff.md` §Retained Per-Round State's schema block
  shows only `round[N]` and `fix[N]`, omitting `regen[N]`, while its own
  acceptance criterion says the section carries the union and the
  regenerated-not-patched rule. The skill-side `loop-control.md` §2a is correct,
  so behaviour is unaffected. Spec is Approved and frozen — not edited (V11).
- `references/loop-control.md` §2a's replay fixture lists only the
  per-workstream `docs/ws/<id>/traceability.md` in `regen[1]` and names `M3`'s
  file bare, so Q-IMPL-HARNESSP3-017's motivating case — the orchestrator's
  post-gate regeneration of the **derived shared aggregate** — is demonstrated
  only implicitly (V10).
- Terminal-token indentation is not uniform across the three leaf templates:
  `CHUNK_VERDICT:` sits at indent 2 inside the `RETURN:` key block while
  `VERDICT:` and `RED_VERDICT:` are at column 0, and live dispatches render
  `CHUNK_VERDICT:` at column 0 — the template is the outlier (V9).
- The observed-writes union is implemented as an append-ordered list, so a path
  that is committed and then re-dirtied within one dispatch counts twice in the
  `N` of `SCOPE: VIOLATION (N paths)` (V7).
- `CLAUDE.md` §Phase Detection's two completion-signal rows state the
  `research_id` match unconditionally; the case-3 relief is only in the prose
  below, so the table read alone is misleading (V13).
- `tools/sdd-telemetry.py summarize`'s stage table is ~190 columns wide (14
  columns), so it wraps in a normal terminal. The `redos per chunk` cell no
  longer contributes to that width after R1 (it renders one `c?:1` token), but
  the table itself was not narrowed.
- The live `.sdd/telemetry.jsonl` holds 8 records whose `dispatch.chunk` is the
  header **string** rather than the parsed integer. The reader now makes them
  visible and the writer contract now forbids them (R1), but the records
  themselves are deliberately left as written — the per-chunk block of this
  cycle's telemetry is therefore permanently empty.
- `sdd-verify` emits the `research_id:` stamp **after** `last_updated:` rather
  than on the line immediately after `status:` as Q-IMPL-HARNESSP3-014 pins, and
  `sdd-plan`'s own frontmatter template shows the same wrong order — so the
  skill contradicts itself. Cosmetic only: the comparison is exact string
  equality and is order-independent, and phase detection is unaffected. Accepted
  at the verify gate (red finding **R4**); no frontmatter was reordered and no
  skill was edited. Carried to harness-p4 (§Next Steps).
- Writing the `pending-red` cells raises `[traceability-aggregate]` until the
  orchestrator's post-gate regeneration — the designed REQ-WS-HARNESSP3-001
  handshake, already recorded under V5. Accepted at the verify gate (red finding
  **R6**). What is imprecise is the **wording** of the obligation's criterion: it
  says "no new finding" where it means "no new finding **on a `pending-red`
  cell**". Restating it is a spec-amending change, so it is recorded rather than
  fixed this cycle.

(No Minors were carried: `docs/ws/harness-p3/verification.md` did not previously
exist, so the carry-or-close rule of `sdd-verify` Step 6 had no prior report at
this path to read. The nearest prior report,
`docs/ws/harness-p2/verification.md` — the `harness-p2` cycle that this cycle
continues, and whose Q4/Q5 findings this kickoff was opened by — belongs to a
**different workstream** and is correctly not a carry source under
REQ-SKILL-HARNESSP3-001; it is cited here so a reader can find the precedent
without git archaeology.)

## Recommendation

- [x] Ship as-is — **red round settled, `pending-red → pass` flipped at the
      verify gate on 2026-09-18.** Two red rounds ran. Round 1 returned three
      `BROKEN` `Rn` (R1 routed `fix`, R4 and R6 routed `accept`); round 2
      returned two (R1 and R4, both routed `accept`). With every `BROKEN` `Rn`
      routed and `VERDICT: APPROVE_WITH_FIXES` on the review, `proceed` was
      granted and the flip ran.
- [ ] Fix critical issues then ship (invoke sdd-replan)
- [ ] Significant rework needed (invoke sdd-replan)

**Which cells the DONE flip may touch (REVIEW C1).** The
`pending-red → pass` flip applies to **exactly the 15 `pending-red` cells** of
`docs/ws/harness-p3/traceability.md` and to nothing else. It **must not** touch
the two `fail` cells — REQ-REDB-HARNESSP3-002 and REQ-ARB-HARNESSP3-001 — which
are not would-be-`pass` rows and are not waiting on the red verdict. The stated exception **was taken**: the
orchestrator drove a second red round, it rendered `RED: R1 new-ground` and
`RED: R6 regression` from re-run `reproduce:` commands (§V1), so
REQ-REDB-HARNESSP3-002 was discharged, returned to `pending-red`, and flipped to
`pass` with the rest. **Final state: 16 `pass`, 1 `fail`.**
REQ-ARB-HARNESSP3-001 stayed `fail` as predicted — nothing in either red round
exercised a live regeneration loop.

**Replan trigger status (REVIEW M1).** The plan's fourth replan trigger —
§Replan Triggers, *"If obligation V1's verify stage cannot be driven to a second
red round after a reasonable attempt → do not mark REQ-REDB-HARNESSP3-002
verified … and treat that as a `fail`-class item for the cycle's acceptance"* —
was **ARMED and has now STOOD DOWN**. It fires if and only if the red round is
not driven to N = 2; round 2 was driven on 2026-09-18 and rendered its derived
lines from genuinely re-run commands, so the trigger did not fire and
REQ-REDB-HARNESSP3-002 is verified by exercise rather than walkthrough.

No other replan is recommended. The nine Minors are contract-precision,
fixture-coverage or readability items, plus the two accepted red findings (R4,
R6); none of them invalidates a plan assumption.

## Next Steps

- **V1 (DISCHARGED at the verify gate, 2026-09-18)** — the second red round ran
  and §V1 now records both derived lines: `RED: R1 new-ground` (round-1 R1's
  `reproduce:` now returns no lines, exit 1) and `RED: R6 regression` (round-1
  R6's still emits its WARN). Both labels of REQ-REDB-HARNESSP3-002's
  distinction were exercised on live commands, and the two lines routed
  *differently* at the gate — which is the whole point of the distinction.
  Nothing carries forward from V1.
- **R1 (fixed, not deferred)** — the reader now surfaces out-of-domain
  `dispatch.chunk` values and the writer contract forbids them. Two follow-ups
  remain: (a) the 8 live records stay malformed by design, so this cycle's
  per-chunk block is permanently empty; (b) nothing *mechanically* enforces the
  writer contract — a `sdd-telemetry.py --lint` mode, or a check at append time,
  is the harness-p4 candidate.
- **R4 (accepted at the verify gate — harness-p4 candidate)** — `sdd-verify`
  emits `research_id:` after `last_updated:` rather than immediately after
  `status:` as Q-IMPL-HARNESSP3-014 pins, and `sdd-plan`'s frontmatter template
  shows the same order. Reconcile the two skills with the Q-IMPL (or amend the
  Q-IMPL) in a cycle that can edit both. Cosmetic: string equality is
  order-independent.
- **R6 (accepted at the verify gate)** — the V5 criterion's wording ("no new
  finding") should read "no new finding **on a `pending-red` cell**"; the
  `[traceability-aggregate]` warning between a per-ws write and the
  orchestrator's regeneration is the designed handshake, not a finding. Needs a
  spec-amending cycle.
- **Marker-4 merge-base regression rule — never exercised this cycle.** Step 5's
  `regression_base(<ws>) = merge-base(<ws>, main)` rule was not put under load:
  this workstream has no branch of its own, so the merge-base resolved to HEAD
  and the regression diff was empty by construction (§Assumptions). The rule's
  isolating property — a workstream's verification being unaffected by unrelated
  work merged to `main` meanwhile — remains unverified in practice and wants a
  genuinely branched workstream to exercise it.
- **V3 (not exercised)** — REQ-ARB-HARNESSP3-001 is fixture-backed only; no live
  fix loop regenerated its deliverable between review rounds this cycle. Reason:
  every fix iteration this cycle patched rather than regenerated. If the red
  round causes a verify-stage re-dispatch, that loop is the live exercise and
  should be recorded here.
- **V4 second half** — the `pending-red → pass` flip, in the same bookkeeping
  step that regenerates `docs/requirements/traceability.md`, is the
  orchestrator's at DONE and is not observable from this stage.
- **V6** — add an `R`/`C` fixture to `tools/sdd-scope-check-selftest.py`: one
  scenario renaming a scoped path to an out-of-scope path (both paths must enter
  the ambiguous set) and one with a space in the path (asserting `-z` parsing
  keeps it one record). Reason not added here: `tools/` is outside this stage's
  write scope, and `sdd-verify` does not fix during verify.
- **V7** — collapse the observed-writes union to strict set semantics
  (de-duplicate by path at render, keeping the richest provenance label) so `N`
  counts distinct paths. harness-p4.
- **V8** — add a `tools/sdd-skill-lint.py` `[template-drift]` rule comparing the
  fenced bodies of `references/dispatch-templates.md` against
  `harness-chunk-verifier.md` and `adversarial-verify.md`; the five bodies are
  byte-identical today but nothing keeps them so. harness-p4.
- **V9** — unify the three leaf templates' terminal tokens at column 0; needs a
  cycle that can also amend the two Approved specs restating the bodies.
- **V10** — repair the §2a replay fixture: add
  `docs/requirements/traceability.md §(matrix)` to `regen[1]` labelled as an
  orchestrator regeneration, and write `M3`'s path in full.
- **V11** — add the `regen[N]` line to `arbitrated-handoff.md` §Retained
  Per-Round State; needs a cycle that can amend Approved specs.
- **V12** — recorded baseline: 9 clean sweeps / 7 warnings / 25 info, with the
  three `[size]` warnings (434 / 464 / 535) accepted as intentional. Do not
  raise the threshold and do not split on line count; revisit the three files on
  cohesion grounds in a later cycle. Any run above 7 warnings is a regression.
- **V13** — qualify `CLAUDE.md` §Phase Detection's two completion-signal rows
  inline ("when a kickoff with one exists"). harness-p4.
- **V14 (harness-p4 lead)** — nothing verifies that the orchestrator committed
  what it observed; Chunk 7's `CLAUDE.md` edits were `IN` and `SCOPE: CLEAN` yet
  omitted from the commit (repaired at `16e240b`). Proposed remedy: at commit
  time compare the leaf's `files_written` plus the observed-writes set against
  `git show --name-only --format= HEAD` and surface a mismatch at the gate as
  `COMMIT: INCOMPLETE (…)`. No new artifact required.
- Four pre-existing `qimpl-broken-ref` warnings remain outside this cycle's
  scope (`deviation-protocol.md:108`, `ws-ids.md:209`, `ws-integration.md:121`,
  `ws-orchestration.md:195`) — unchanged, carried as the accepted baseline.
- `tools/sdd-telemetry.py summarize` rendering: narrow the stage table (14
  columns, ~190 chars). The per-chunk/stage-table disagreement is closed by R1.

## Assumptions

- **Regression base.** This workstream has no branch of its own — HEAD is `main`
  and `git log main..HEAD` is empty — so `merge-base(harness-p3, main)` resolves
  to HEAD and the regression diff is empty by construction. Verified against the
  cycle's eight chunk commits instead, each of which closed at its own per-chunk
  gate. Stated rather than silently skipped.
- **Red-team slot.** The dispatch carries `Red team: enabled`, so Step 6's table
  yields `status: pending-red` for a blue-team pass. This report never writes
  `pass` and never performs the flip.
- **Shared aggregate.** `docs/requirements/traceability.md` is absent from this
  dispatch's write scope; per REQ-WS-HARNESSP3-001 that absence is the signal
  that regeneration is the orchestrator's post-gate bookkeeping, so it was not
  written here.
- **`fail` as the "not exercised" cell value.** `docs/spec/ws-traceability.md`
  §Legal `Verified` Cell Values admits exactly `pass`, `fail` and `pending-red`,
  and the specs are frozen this cycle, so no fourth marker for "constructed but
  never exercised" could be minted. The two undischarged requirements therefore
  read `fail`, with the reason stated in their §Acceptance Criteria rows, in V1
  and V3, and in §Recommendation. Stated rather than silently softened to
  `pending-red`, which would have made the DONE flip assert a `pass` that no
  evidence supports.
- **Fixing during verify.** `sdd-verify` §Rules says "don't fix during verify".
  This revision does contain a fix — the R1 reader and writer-contract change —
  because the dispatch that produced it was an explicit `RED_BREAK` repair packet
  from the verify gate, which overrides the skill's default. No other issue in
  this report was fixed; every V-item and Minor is recorded only.
- **Two specs without their own §Acceptance Criteria heading (review M3):**
  checked and **not reproduced** — every file in `docs/spec/*.md` carries exactly
  one `## Acceptance Criteria` heading (`grep -c` over all specs returns 1 for
  each). Recorded as closed rather than carried.
