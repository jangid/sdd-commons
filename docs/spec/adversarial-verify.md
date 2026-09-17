---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-REDB-HARNESSP2-001
  - REQ-REDB-HARNESSP2-002
  - REQ-REDB-HARNESSP2-003
  - REQ-REDB-HARNESSP2-004
  - REQ-REDB-HARNESSP2-005
  - REQ-REDB-HARNESSP2-006
  - REQ-REDB-HARNESSP2-007
  - REQ-REDB-HARNESSP2-008
  - REQ-REDB-HARNESSP2-009
  - REQ-SKILL-HARNESSP2-002
  - REQ-SKILL-HARNESSP2-005
  - REQ-LINT-HARNESSP2-001
---

# Adversarial (Red/Blue) Verify

## Context

`sdd-verify` is confirmatory: it walks every acceptance criterion and records
pass/fail. Nobody in the loop is told to *break* the system. RS-HARNESSP2-001 Q2
positioned an adversarial pass exactly as RS-008 positioned the chunk verifier:
a **second executor of `sdd-verify` Steps 3–4**, dispatched by the orchestrator
as a read-only leaf, never a fifth verification layer and never `sdd-review`
(REQ-REV-005/006 keep behavioural work out of review). **Blue** is `sdd-verify`;
**Red** is a third dispatch kind at the verify stage that picks the weakest
acceptance criteria and constructs inputs or commands that violate them. A
break counts only when it is reproducible.

This spec defines the red dispatch (opt-in, default off), its input and return
contracts, the `RED_VERDICT:` token, the exit rule at the verify gate, the
`status: pending-red` guard that keeps `pass` off disk while red is pending,
and the fix-loop interaction. It fulfils REQ-REDB-HARNESSP2-001..009, the
skill changes of REQ-SKILL-HARNESSP2-002 / -005 and rows (a) of
REQ-LINT-HARNESSP2-001. `RED_VERDICT:` and `RED_BREAK` are defined here and
nowhere else.

## Design

### Positioning (REQ-REDB-HARNESSP2-001, -002)

| Property | Value |
|---|---|
| Dispatch kind | `red` (`telemetry.md` `dispatch.kind`) |
| Stage | verify only — never chunk close, never any other stage |
| Opt-in | at the verify gate, **before** the verify pipeline is dispatched: `red team: off | on` (default `off`); the same device as fan-out's opt-in (REQ-ORCH-024) |
| Position in the stage | after the verify pipeline returns with `RETURN.status: COMPLETE`, before the verify-stage review |
| Executor of | `sdd-verify` Steps 3–4 (acceptance-criteria walkthrough, user-perspective behaviour) in adversarial mode |
| Not | `sdd-review`, not a mode of it, not a fifth layer; the four-layer table in `sdd-verify` §Verification Layers and `CLAUDE.md` is unchanged |
| Standalone `sdd-verify` | unchanged except for the `pending-red` input below |

**Why an executor and not a layer**: the layer table classifies *what* is
checked (mechanical / structural / holistic / semantic); red checks the same
acceptance criteria blue does, by a different method. The chunk verifier set the
precedent (REQ-HARN-014); keeping the table stable keeps `sdd-review`'s scope
boundaries (REQ-REV-006 (c)) intact.

**Why opt-in and default off**: one extra dispatch per cycle is cheap, but red
has no value on a cycle whose specs carry prose-only acceptance criteria (most
of this repository's); the operator knows which cycles have behaviour to break.

### Red Dispatch Template (REQ-REDB-HARNESSP2-003, -004)

Lives in `skills/sdd-orchestrate/references/dispatch-templates.md` as the
**RED TEAM** template, beside REVIEW and CHUNK VERIFIER. Paths and slots only —
no finding text, no blue evidence:

```
You are a non-interactive RED TEAM subagent — the adversarial second executor of
sdd-verify Steps 3–4. Do NOT ask questions. Do NOT fix anything. Run, don't read.
Repository root: {repo_root}                     # marker 4: the workstream branch checkout
Specs (read each `## Acceptance Criteria` yourself): {spec_paths}
Plan: {plan_path}
Quality-gate commands (from CLAUDE.md): {gate_commands}
{red_input_override}                             # empty by default; "Blue's report: {verification_path}" when the operator set `red input: +verification.md`
Budget: ≤ 25 tool calls, ≤ 3 test runs, read-only
Write scope: (empty — read-only)
Commit ownership: you never commit
Rules: pick the weakest criteria; construct inputs/commands that violate them; a break counts ONLY
       with a reproducible `reproduce:` command or test id — otherwise report it as HELD with your
       suspicion under `observed:`. Return in the shape below; end with RED_VERDICT: on its own last line.
```

Input contract (checked by the orchestrator's pre-dispatch self-check):

| Input | Present | Notes |
|---|---|---|
| repository root | yes | marker `4`: workstream branch checkout |
| spec paths | yes | red reads `## Acceptance Criteria` itself |
| plan path | yes | for chunk vocabulary in `location` |
| gate commands | yes | verbatim from `CLAUDE.md` |
| `Budget:` | yes | default `≤ 25 tool calls, ≤ 3 test runs, read-only` (REQ-HARN-004) |
| `Write scope: (empty — read-only)` | yes, verbatim | REQ-HARN-020 |
| `Commit ownership: you never commit` | yes, verbatim | REQ-HARN-024 |
| non-interactive clause | yes | |
| `verification.md` | **withheld by default** | operator override `red input: +verification.md` at the opt-in; the A/B is `index.md` Open Questions |
| finding text, review reasoning | never | |

**Why withhold blue's evidence**: the reviewer-isolation argument — reading what
was already checked anchors red on the same criteria and the same inputs.

Any write observed by red is `OUT`, reverted before the gate (the chunk
verifier's rule, `harness-chunk-verifier.md`); a reproducible break is a
command line in the return, never a committed test.

### Return Contract and `RED_VERDICT:` (REQ-REDB-HARNESSP2-005, -006)

Red's return text, in order:

```
## Red team — <spec.md> acceptance criteria            # one heading per spec examined
- R1: <criterion text> — attack: <what was tried> — observed: <one line> — reproduce: `<command or test id>` — BROKEN
- R2: <criterion text> — attack: <what was tried> — observed: <one line> — reproduce: `<command>` — HELD
- R3: <criterion text> — attack: <what was tried> — observed: suspected <…>, no reproducible input found — reproduce: n/a — HELD
RETURN:
  status: COMPLETE
  budget_consumed: {tool_calls: 19, test_runs: 3}
  files_written: []
  commits: []
  tasks_completed: []
  traceability_fills: []
  chunk_close: {}
  failures:
    - {test: "python -m app --window 0", kind: error, message: "ZeroDivisionError at engine.py:140", location: src/recon/engine.py:140}
  ledger: []
  verified_do_not_touch: []
  open_questions: []
  blocked_writes: []
RED_VERDICT: BROKEN
```

Rules:

- One `Rn` line per attempted criterion, in the fixed shape; `Rn` numbering is
  per return.
- `failures[]` holds **exactly one entry per `BROKEN` line**: `test` = the
  `reproduce:` command or test id, `kind ∈ {assertion, error, lint, type,
  build}`, `message`, `location` (`harness-return-contract.md` §Failures Are
  One-Line).
- `RED_VERDICT: BROKEN | HELD` is the **last line**, on its own; `BROKEN` iff
  `failures[]` is non-empty.
- A claim without a runnable `reproduce:` is **advisory**: reported as `HELD`
  with the suspicion in `observed:`; it never enters `failures[]`, never
  affects the token, never gates the pass commit.

Orchestrator parsing (`references/return-contract.md`): match `^RED_VERDICT:`
at line start (the `CHUNK_VERDICT` precedent). Malformed — surfaced as
`RETURN: MALFORMED (<reason>)` with the standard pause `re-dispatch | accept
manually | stop` — when any of:

| Condition | Reason string |
|---|---|
| token missing | `RED_VERDICT missing` |
| token not on the last non-blank line | `RED_VERDICT not last` |
| `HELD` with non-empty `failures[]` | `RED_VERDICT/failures disagree` |
| `BROKEN` with empty `failures[]` | `RED_VERDICT/failures disagree` |
| a `BROKEN` line whose `reproduce:` is `n/a`, empty, or not a backticked command | `BROKEN without reproduce` |
| `Rn` count of `BROKEN` ≠ `len(failures)` | `Rn/failures count mismatch` |

The token is red-only: `RED_VERDICT:` in any other dispatch's return is a
`FOREIGN_TOKEN` warning at the gate (`telemetry.md` `return.warnings`), never
branched on. The review consumer's lint regex becomes
`(?<!CHUNK_)(?<!RED_)VERDICT:` so a red token never satisfies the review row.

### Verify-Stage Gate and Exit Rule (REQ-REDB-HARNESSP2-007)

Signal order at the verify stage gate extends REQ-ORCH-034: `RETURN.status` →
`SCOPE:` → **`RED_VERDICT:`** → review `VERDICT:` → counters. Red's `Rn` lines
are rendered verbatim under the token.

```
Verify stage gate — pipeline #9 (sdd-verify), red #10, review #11
  RETURN.status  : COMPLETE   budget_consumed: {tool_calls: 41, test_runs: 6}  vs  Budget: ~70 tool calls
  SCOPE: CLEAN
  RED_VERDICT: BROKEN
    - R1: <criterion> — attack: … — observed: … — reproduce: `python -m app --window 0` — BROKEN
    - R2: <criterion> — attack: … — observed: held — reproduce: `pytest -q tests/test_recon.py::test_window` — HELD
  VERDICT: APPROVE
  iteration 0 of 3
  Options per BROKEN finding: R1 → fix (RED_BREAK packet) | accept (record) | stop
  proceed: unavailable until every BROKEN Rn is fixed or accepted
```

Exit rule: `proceed` (→ DONE, which flips `pending-red` and commits
`verification.md`) is offered **iff** `VERDICT ≠ REJECT` **and** (red was not
run, or `RED_VERDICT: HELD`, or every `BROKEN` `Rn` is resolved by `fix` or
`accept`). Per `BROKEN` finding:

| Option | Effect |
|---|---|
| `fix (RED_BREAK packet)` | §Fix-Loop Interaction; consumes one verify-stage fix iteration per red round |
| `accept (record)` | the orchestrator appends `- Rn accepted at gate <YYYY-MM-DD>: <observed> — reproduce: \`<cmd>\`` under `verification.md` §Issues Found → Minor (marker `4`: `docs/ws/<id>/verification.md`) — bookkeeping in an existing section of an existing artifact, outside the observed window (REQ-HARN-025), the same device as fan-out §3e plan marks; no review store is created |
| `stop` | halt |

The decision is the operator's (REQ-ORCH-011). When the verify pipeline
returned `status: fail` in `verification.md`, red is **not dispatched** for
that return (there is nothing to break past a failing blue); the gate shows the
non-token line `Red team: not run (blue status fail)` and proceeds to the
normal fix/replan routing.

### `status: pending-red` (REQ-REDB-HARNESSP2-008)

When red is on for the cycle, the verify pipeline template carries the slot
`Red team: enabled`, and `sdd-verify` Step 6 writes:

| Blue's own result | Slot absent (standalone, or red off) | Slot present |
|---|---|---|
| pass | `status: pass` | **`status: pending-red`** |
| fail | `status: fail` | `status: fail` |

Lifecycle:

```
sdd-verify (pipeline) writes status: pending-red
  → orchestrator dispatches red → gate
  → exit rule satisfied → orchestrator flips pending-red → pass (frontmatter edit, own bookkeeping)
  → orchestrator commits verification.md (commit ownership, REQ-HARN-024)
  → DONE
```

If red is enabled but not run after all (operator chose `stop` on the opt-in
after the pipeline, or blue failed), the orchestrator flips the same way at the
gate. Phase detection everywhere maps `pending-red` to **"verification
incomplete — re-enter the verify stage"** — never DONE, never needs-replan:

| Reader | `pending-red` means |
|---|---|
| `sdd-verify` Phase Detection | re-verification state (item 5), like an existing report after fixes |
| `sdd-replan` Phase Detection | not a verification failure; route to `sdd-verify` |
| `sdd-orchestrate` position table | verify stage, resume before the red dispatch |
| `sdd-gc.py` staleness sweep | treated as "verification exists, not passed" (`drift-sweep.md`) |

**Decision recorded**: RS-HARNESSP2-001 Q2 offered commit ownership alone as
the default; requirements adopted `pending-red` because the operator's success
criterion — `verification.md` never reads `pass` on disk while red is pending —
cannot be guaranteed across sessions by commit ownership. Both guards hold.
Under marker `3` and with red off, `sdd-verify` Step 6 output is byte-identical
to v5.

### Fix-Loop Interaction (REQ-REDB-HARNESSP2-009)

A `BROKEN` finding routed to `fix` produces an **implement**-stage repair packet
(`harness-return-contract.md` §Repair Packet):

| Packet field | Value |
|---|---|
| `reason` | `RED_BREAK` (new enum value; defined here) |
| `failures` | red's `RETURN.failures` verbatim (one per `BROKEN` line routed) |
| `findings` | the routed `Rn` lines verbatim |
| `target.chunk` | resolved by the finding → chunk mapping of `harness-return-contract.md` §Finding → Chunk Mapping, with the **spec** taken from the `## Red team — <spec.md>` heading the `Rn` line sits under (red lines carry no `affects`); a spec traced by no chunk → `all` |
| `write_scope`, `budget` | that chunk's default row |

Sequence per red round:

```
fix dispatch (implement chunk) → scope check → chunk verifier → per-chunk gate
  → re-dispatch verify pipeline (regenerates verification.md from evidence; writes pending-red again)
  → red re-run ONCE by default (not an iteration — the verifier re-dispatch rule)
  → verify stage gate with a fresh RED_VERDICT:
```

Counting: one red round = at most **one** fix iteration of the **verify**
stage's counter (REQ-HARN-001), however many chunk-grouped fix dispatches it
fans into; `FIX_LOOP_MAX` (3) is the backstop and its exhaustion renders the
compiled findings log with no fourth automatic dispatch. A second red re-run
after the same fix requires an explicit operator choice and is likewise not an
iteration. Red rounds and review rounds share the verify stage's single
counter — a cycle cannot spend 3 red rounds *and* 3 review rounds.

### Skill and Lint Changes (REQ-SKILL-HARNESSP2-002, -005; REQ-LINT-HARNESSP2-001 (a))

| Where | Change |
|---|---|
| `skills/sdd-orchestrate/references/dispatch-templates.md` | **RED TEAM** template (§Red Dispatch Template) with `Budget:`, `Write scope:`, `Commit ownership:`, `RETURN:`, `RED_VERDICT: BROKEN \| HELD`; the verify PIPELINE template gains the `Red team: enabled` slot |
| `skills/sdd-orchestrate/references/return-contract.md` | `^RED_VERDICT:` parsing, the malformed table, `FOREIGN_TOKEN` warning, `RED_BREAK` packet row and the heading-based spec resolution |
| `skills/sdd-orchestrate/SKILL.md` §The gate | opt-in line `red team: off \| on` (+ `red input: +verification.md`), signal order with `RED_VERDICT:` after `SCOPE:`, exit rule, `fix \| accept (record) \| stop`, `pending-red` → `pass` flip; position table row `pending-red → verify` |
| `skills/sdd-orchestrate/references/loop-control.md` | red round = one verify-stage iteration; re-run rule |
| `skills/sdd-verify/SKILL.md` | Step 6 `pending-red` rule guarded by the slot; Phase Detection lists `pending-red`; §Issues Found → Minor documented as the `- Rn accepted at gate …` slot and §Next Steps as the `- gc <rule>: …` slot (`drift-sweep.md`); §Verification Layers states red is a second executor of this layer; four-layer table unchanged |
| `skills/sdd-replan/SKILL.md` | Phase Detection: `pending-red` routes to `sdd-verify` |
| `skills/sdd-review/SKILL.md` | **no change** for red |
| `tools/sdd-skill-lint.py` `REQUIRED` | (a1) `dispatch-templates.md` ∋ `RED_VERDICT: BROKEN \| HELD` min 1 — producer; (a2) `skills/sdd-orchestrate/SKILL.md` or `references/return-contract.md` ∋ `RED_VERDICT:` min 1 — consumer; existing d2 pattern becomes `(?<!CHUNK_)(?<!RED_)VERDICT:`; `--self-test` §7 mutation loop covers both rows |
| `tools/sdd-scope-check-selftest.py` | no new scenario — red's write revert reuses the verifier's rule; the write fixture of REQ-REDB-HARNESSP2-003 is a lint/gate fixture |
| `CLAUDE.md` | four-layer bullet **unchanged** |

## Verification

### Automated

- `test_opt_in_default_off`: the verify gate shows `red team: off | on`
  before the pipeline dispatch; with `off` no `red` telemetry record exists and
  the gate text equals v5's.
- `test_one_red_per_verify_return`: with `on`, exactly one `red` dispatch per
  verify-pipeline return precedes the review; a re-verify after a fix gets one
  more.
- `test_template_slots_verbatim`: RED TEAM template contains `Write scope:
  (empty — read-only)` and `Commit ownership: you never commit`, names
  `sdd-verify` Steps 3–4, lists no `verification.md` path unless the override
  is set, and contains no finding text.
- `test_red_write_is_out_and_reverted`: a fixture in which red writes
  `tests/test_break.py` yields `SCOPE: VIOLATION (1 paths)` and the file is
  absent at the gate.
- `test_parse_broken_two_findings`: two `BROKEN` lines + two `failures[]` +
  `RED_VERDICT: BROKEN` → BROKEN with two findings.
- `test_malformed_matrix`: each row of the malformed table yields `RETURN:
  MALFORMED (<reason>)`; `reproduce: n/a — BROKEN` is malformed.
- `test_gate_blocks_proceed_until_resolved`: `RED_VERDICT: BROKEN` (R1) +
  `VERDICT: APPROVE` → no `proceed`; after `accept`, `verification.md` §Issues
  Found → Minor has the R1 line, `proceed` is offered, and no other file under
  `docs/` changed.
- `test_pending_red_never_pass_on_disk`: with red on, `verification.md` never
  contains `status: pass` between the pipeline's return and `proceed`; with red
  off, Step 6 output is byte-identical to v5.
- `test_position_table_pending_red`: `sdd-orchestrate` maps `pending-red` to
  verify; `sdd-verify` Phase Detection lists it; `sdd-replan` routes it to
  verify.
- `test_red_break_packet`: `reason: RED_BREAK`, `failures[]` verbatim, chunk
  resolved from the spec heading; the gate after the fix shows `iteration 1 of
  3` and a fresh `RED_VERDICT:`; three `BROKEN` rounds exhaust the cap with no
  fourth automatic dispatch.
- `test_lint_red_rows`: removing `RED_VERDICT:` from the template → exit 1
  with the row's fix; a file containing only `RED_VERDICT: HELD` does not
  satisfy the review consumer row; shipped set → exit 0.

### Manual

- Run red once on a toy with a deliberately weak criterion; confirm the
  `reproduce:` command fails when run by hand and that `accept` lands exactly
  one line in §Issues Found → Minor.

### Acceptance Criteria

- [ ] `red` is an opt-in third dispatch kind at the verify gate, default off, one per verify-pipeline return, never at chunk close or another stage (REQ-REDB-HARNESSP2-001)
- [ ] Red is specified as the adversarial second executor of `sdd-verify` Steps 3–4; `sdd-review` unmodified for red; four-layer table unchanged (REQ-REDB-HARNESSP2-002)
- [ ] Template carries the empty write scope and never-commit slots verbatim; red writes are `OUT` and reverted (REQ-REDB-HARNESSP2-003)
- [ ] Input contract exactly as tabled; `verification.md` withheld by default with the gate override (REQ-REDB-HARNESSP2-004)
- [ ] Return shape, `failures[]` one-per-BROKEN, own-line last `RED_VERDICT:`, `^RED_VERDICT:` parsing, malformed table, red-only token warning (REQ-REDB-HARNESSP2-005)
- [ ] Reproducibility rule in the template's Rules; non-reproducible claims are `HELD` advisory (REQ-REDB-HARNESSP2-006)
- [ ] Gate order `SCOPE:` → `RED_VERDICT:` → `VERDICT:`; exit rule; `fix | accept (record) | stop`; accept line shape in §Issues Found → Minor (REQ-REDB-HARNESSP2-007)
- [ ] `Red team: enabled` slot; Step 6 `pending-red` table; flip-then-commit; phase detection maps `pending-red` to verify everywhere (REQ-REDB-HARNESSP2-008)
- [ ] `RED_BREAK` packet, one verify-stage iteration per red round, one default re-run, cap backstop (REQ-REDB-HARNESSP2-009)
- [ ] Skill changes tabled for `sdd-orchestrate`, `sdd-verify`, `sdd-replan`; lint rows (a1), (a2) and the `(?<!RED_)` regex change; `--self-test` §7 covers them (REQ-SKILL-HARNESSP2-002, -005; REQ-LINT-HARNESSP2-001)
- [ ] `python3 tools/sdd-skill-lint.py` exits 0

## Edge Cases

- **Red returns `PARTIAL` or `BUDGET_EXHAUSTED`**: treated per
  `harness-return-contract.md` §`RETURN.status` Branching for a non-implement
  stage — gate pause before any review; the token, if present, is still
  validated; `proceed` is unavailable until the operator chooses `accept
  manually` or re-dispatches red.
- **Red finds a break in a criterion blue marked `unable-to-verify`**: still
  `BROKEN` if reproducible; blue's table is regenerated on re-verify.
- **Red and review both raise findings**: review findings route through the
  normal `loop-back-to-fix` packet (`reason: REVIEW_FINDINGS`), red through
  `RED_BREAK`; both in the same round count as **one** verify-stage iteration
  and may be merged into one implement fix dispatch per chunk by the mapping.
- **Multiple specs, one `Rn` numbering**: `Rn` is global per return across
  spec headings; the heading above each line is what resolves its spec.
- **Marker `3`**: identical; `verification.md` is the flat path.
- **Operator sets the override after the first red run**: the re-run uses the
  new input set; the A/B observation is the operator's to log.

## Cross-Spec Consistency (XSPEC)

- `harness-chunk-verifier.md` §Positioning (second executor, not a layer) is
  mirrored; red's slot set equals the verifier's (`Budget:`, empty `Write
  scope:`, never commit, `RETURN:`, own-line token); the write-revert rule is
  reused.
- `harness-return-contract.md`: `failures[]` field names and `kind` enum match
  §Failures Are One-Line; §Repair Packet `reason` gains `RED_BREAK`;
  §Finding → Chunk Mapping is reused with spec-from-heading in place of
  `affects` — recorded there as Q-IMPL-HARNESSP2-003; §Malformed Returns is
  extended by the table above; §VERDICT Token's lint regex gains `(?<!RED_)`.
- `harness-loop-control.md` §Fix-Loop Cap: red rounds consume the verify
  stage's counter; the verifier re-dispatch rule is applied to the red re-run.
- `harness-write-scope.md` §Commit Ownership: pipeline → orchestrator commits
  on `proceed` — the `pending-red` flip is performed immediately before that
  commit, outside the observed window (§Snapshot Ordering).
- `orchestration.md` §v5 gate order: extended by `RED_VERDICT:` between (2)
  and (4) at the verify stage gate only; vocabulary extended by `fix (RED_BREAK
  packet) | accept (record)` — recorded there as Q-IMPL-HARNESSP2-008.
- `review.md` §Trigger Classification (post-verification = semantic read of
  the report) is unchanged; `sdd-review` is not modified for red.
- `telemetry.md`: `dispatch.kind: red`, `verdict.red_verdict`,
  `dispatch.reason: RED_BREAK` consumed with the same names.
- `evaluation.md` policy definition uses `RED_VERDICT: HELD` as a conjunct —
  same token, same meaning.
- `ws-integration.md`: under marker `4` the repository root handed to red is
  the workstream branch checkout — consistent.
- **No unresolved contradictions.**

## Open Questions

1. **Red input A/B** (`index.md` Open Questions): does `+verification.md` find
   more breaks? Default: withheld; the operator runs the override on one cycle
   and records the comparison in that cycle's `verification.md`.
2. **Red on a cycle with prose-only acceptance criteria** (this repository):
   Default: red runs the lint / self-test commands as its attack surface and
   reports mostly `HELD`; the operator keeps it off for such cycles.
3. **Should `accept (record)` lines also carry the `Rn` attack text?** Default:
   `observed:` and `reproduce:` only — the line must stay one line.
