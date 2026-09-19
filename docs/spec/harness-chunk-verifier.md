---
status: Approved
last_updated: 2026-09-19
requires:
  - REQ-HARN-014
  - REQ-HARN-015
  - REQ-HARN-016
  - REQ-HARN-017
  - REQ-HARN-HARNESSP3-002
  - REQ-HARN-HARNESSP4-007
---

# Harness Chunk-Close Verifier

## Context

`sdd-implement` Step 4 has the implementer run the four chunk-close checks and
then judge its own report. Under a non-interactive dispatch there is no operator
to confirm the report, so the leaf both produces and grades it — the
self-validation bias catalogue idea B5 targets. RS-008 Q2 found that Checks 1
and 3 and the project quality gates are deterministic (grep, import search,
command exit codes) and need no implementer context, so a fresh executor can
re-run them; that `sdd-review` must **not** be that executor (REQ-REV-005/006
place these checks outside review's scope and `review.md` §Trigger
Classification marks chunk-close boundaries *Skip*); and that fan-out §3e is
exactly where such a step slots in.

This spec defines the **chunk-close verifier**: a read-only leaf dispatch that
re-executes the mechanical part of the chunk-close layer and returns
`CHUNK_VERDICT: PASS | FAIL`. It fulfils REQ-HARN-014..017.

## Design

### Positioning: Second Executor, Not a Fifth Layer

The four verification layers (`review.md` §Verification Stack Positioning,
`CLAUDE.md`) are unchanged: chunk-close (mechanical), XSPEC (structural),
sdd-verify (holistic), sdd-review (semantic). The verifier is a **second,
independent executor of the chunk-close layer** under `sdd-orchestrate`:

| Check | Implementer (Step 4, unchanged) | Verifier | Implement-stage `sdd-review` |
|---|---|---|---|
| Check 1 type alignment (REQ-CHKC-002) | runs | **re-runs** | — |
| Check 2 traceability (REQ-CHKC-003) | runs (fan-out: defers) | — | — (orchestrator applies and verifies after the fill, `fan-out.md` §3e) |
| Check 3 test coverage (REQ-CHKC-004) | runs | **re-runs** | — |
| Check 4 Q-IMPL audit (REQ-CHKC-005) | runs | — | judges fidelity |
| Quality gates (build / lint / type / tests from `CLAUDE.md`) | runs per task | **re-runs** | — |
| Report semantics (silent scope reduction, stubbing) | — | — | judges |

No check runs three times. The implementer keeps Step 4 verbatim because
standalone `sdd-implement` has nobody to dispatch a verifier; the verifier is an
orchestrate-only pass. The verifier is **never `sdd-review`**: its template
invokes no skill, carries no review checklist and produces no review report.

**Why not extend `sdd-review`**: REQ-REV-005/006 are approved requirements
that forbid review from handling type alignment, traceability, test coverage
and Q-IMPL audit; a review-based verifier would contradict them. A separate
persona keeps review semantic and the verifier mechanical.

### Verifier Dispatch Template (REQ-HARN-017)

The verifier **is a leaf** (`harness-return-contract.md`): it carries the leaf
slots and nothing else. Template (in `dispatch-templates.md`, new §CHUNK
VERIFIER):

```
You are a non-interactive chunk-close verifier. Do NOT ask questions.

Working directory (absolute): {repo_root_or_worktree_path}
Plan: {plan_path} — verify Chunk {N} only.
Specs the chunk's tasks trace to: {spec_paths}
Quality gate commands (from CLAUDE.md): {gate_commands}
Budget: {budget}                       # e.g. "1 chunk, ≤ 15 tool calls, ≤ 2 test runs, read-only"
Write scope: (empty — read-only)       # you may not create, modify, delete or rename any file
Commit ownership: you never commit.

Task: re-run chunk-close Check 1 (spec-implementation type alignment) and
Check 3 (test coverage per spec) for Chunk {N} exactly as sdd-implement Step 4
defines them, then run every quality gate command and record exit codes. Do not
run Check 2 or Check 4; do not invoke sdd-review or sdd-implement; do not fix
anything.

Return: findings in the chunk-close report shape (Check 1, Check 3, Gates),
then this RETURN: block — every key present (empties allowed), `status` first,
`CHUNK_VERDICT:` on its own line, last:

RETURN:
  status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED
  budget_consumed: {tool_calls: N, test_runs: N}
  files_written: []                    # must be empty — read-only dispatch
  commits: []
  tasks_completed: []
  traceability_fills: []
  chunk_close: {chunk: N, check1: pass|fail, check2: deferred, check3: pass|advisory, check4: deferred, overrides: []}
  failures: []                         # one line each: test / kind / message / location
  ledger: []
  verified_do_not_touch: []
  open_questions: []
  blocked_writes: []
CHUNK_VERDICT: PASS | FAIL           # column 0 — the only key of the block not indented
```

[Amended 2026-09-18: template body synchronised with references/dispatch-templates.md per the spec's own byte-consistency clause]

Slot contract: `{repo_root_or_worktree_path}` (sequential: repo root; fan-out:
the leaf's worktree), `{plan_path}` + `{N}`, `{spec_paths}` (resolved by the
orchestrator from the chunk's `traces to` references), `{gate_commands}`,
`{budget}`. Nothing else — no implementer reasoning, no review report, no
orchestrator conversation, no repair history.

### Verdict Rule

```
CHUNK_VERDICT: PASS  iff  Check 1 has zero blocking findings
                     and  every gate command exits 0
CHUNK_VERDICT: FAIL  otherwise
```

Check 3 is advisory in `chunk-close-review.md` and stays advisory here: Check 3
findings are reported but never flip the verdict. Any implementer override
recorded in `RETURN.chunk_close.overrides` is *reported* by the orchestrator
next to the verifier's findings at the gate, never applied by the verifier.

Verifier return shape:

```yaml
## Chunk 2 Verification (independent re-run)
### Check 1: Type Alignment — pass | fail — findings: [...]
### Check 3: Test Coverage — pass | advisory — findings: [...]
### Gates — pytest -q: exit 1; ruff check .: exit 0; mypy src/: exit 0
RETURN:
  status: COMPLETE                     # the verifier's own dispatch status
  budget_consumed: {tool_calls: 11, test_runs: 2}
  files_written: []                    # must be empty — read-only dispatch
  commits: []
  tasks_completed: []
  traceability_fills: []
  chunk_close: {chunk: 2, check1: fail, check2: deferred, check3: advisory, check4: deferred, overrides: []}
  failures:
    - {test: "pytest -q", kind: assertion, message: "1 failed: tests/test_recon.py::test_gap_report", location: src/recon/engine.py:142}
  ledger: []
  verified_do_not_touch: []
  open_questions: []
  blocked_writes: []
CHUNK_VERDICT: FAIL                    # verifier-only key, last line, column 0
```

[Amended 2026-09-19, harness-p5 — folded from Q-IMPL-HARNESSP4-009 under
REQ-QIMPL-HARNESSP5-001: the example's token now sits at **column 0**, matching
the fenced contract of §Terminal Token at Column 0 and the paired dispatch body;
the example is illustrative and is not a `[template-drift]` pair, which is why
the p4 chunk left it indented.]

The verifier carries the **full** leaf key set (`harness-return-contract.md`
§RETURN Block — every key present, empties allowed) plus `CHUNK_VERDICT`, which
is the one verifier-only key; `check2` / `check4` read `deferred` because the
verifier does not run them. `CHUNK_VERDICT:` is the **last line of the block**, on its own line
[Amended 2026-09-18, REQ-HARN-HARNESSP3-002: the earlier text also accepted the
line immediately after the block; that latitude is withdrawn, matching the
sibling red rule where `RED_VERDICT:` off the last line is
`RETURN: MALFORMED`]. A token that is missing, unrecognized, or not on the last
line of the block is a malformed return (`harness-return-contract.md`
§Malformed Returns). `files_written` must be `[]`;
the scope check on a verifier return must observe zero writes
(`harness-write-scope.md`).

### Sequencing — Sequential Mode (REQ-HARN-016)

Under `sdd-orchestrate` sequential mode the implement stage is dispatched
**per chunk**, in plan order. `dispatch-templates.md` §PIPELINE (implement)
gains a `Chunk N` parameter in its deliverable contract, exactly as fan-out
already tells a leaf which chunk-group to run; `sdd-implement` is not modified
(REQ-ORCH-001).

```
for each `### Chunk N:` in plan order:
  1. snapshot(before) (harness-write-scope.md) → dispatch PIPELINE implement, Chunk N
  2. on return: snapshot(after) → parse RETURN → write-scope check → `SCOPE:` token
  3. branch on RETURN.status (harness-return-contract.md §RETURN.status Branching):
       COMPLETE / PARTIAL → dispatch CHUNK VERIFIER for Chunk N (repo root) → `CHUNK_VERDICT:`
       BLOCKED / BUDGET_EXHAUSTED → no verifier; checkpoint already in the plan (sequential leaf writes it)
  4. render the PER-CHUNK GATE (block below); wait for the operator:
       proceed → orchestrator commits the chunk (commit ownership) → next chunk
       fix     → compose repair packet (failures ← verifier RETURN.failures, findings: [],
                 iteration ← per-chunk redo counter, incremented) → redo dispatch for Chunk N → back to 2
       stop    → halt; the chunk's writes stay uncommitted in the working tree
after the last chunk: dispatch the implement-stage sdd-review ONCE on the merged state
                      → the single implement-stage review gate (proceed │ loop-back-to-fix │ stop)
```

**Per-chunk gate (lightweight).** After each chunk's implement dispatch returns,
the orchestrator runs the write-scope check, dispatches the chunk verifier, and
then shows the operator a compact block — the `RETURN.status` line, the `SCOPE:`
line, the `CHUNK_VERDICT:` line and the files changed — with three choices:
**proceed** (the orchestrator commits the chunk), **fix** (re-dispatch the chunk
with a repair packet; counts toward the per-chunk redo cap,
`harness-loop-control.md` §Redo Cap per Chunk) or **stop**. On
`CHUNK_VERDICT: PASS` with `SCOPE: CLEAN` the default is `proceed`; on `FAIL` or
`VIOLATION` the default is `fix`, and `proceed` is an explicit operator override
recorded as gate text. Any unresolved `OUT` path must first be resolved by the
scope options (`revert path | accept & widen scope`, `harness-write-scope.md`
§Finding Format). The block is stated identically in `harness-write-scope.md`
§Commit Ownership / §Snapshot Ordering and `orchestration.md` §v5 (those two
copies keep the block's two-space gate indentation on the token line; here it is
rendered at column 0 so that no indented `CHUNK_VERDICT:` remains anywhere in
this file — REQ-QIMPL-HARNESSP5-001's file-wide criterion; the content is
otherwise identical):

```
Per-chunk gate — implement dispatch #2 (Chunk 2: Reconciliation)   [fan-out: leaf wt-g1 / branch fanout-g1]
  RETURN.status  : COMPLETE    budget_consumed: {tool_calls: 22, test_runs: 3}  vs  Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs
  SCOPE: CLEAN                                    # full write-scope block above when VIOLATION
CHUNK_VERDICT: PASS                               # verifier findings (Check 1 / Check 3 / Gates) listed above when FAIL — the token as the verifier emitted it, column 0
  Files changed  : src/recon/engine.py M, tests/test_recon.py M, docs/plan.md M
  Redo           : 0 of 3 (per-chunk redo counter)
  Options: proceed (orchestrator commits the chunk) │ fix (re-dispatch Chunk 2 with a repair packet; counts toward the per-chunk redo cap) │ stop
```

The single implement-stage review gate remains **once**, after all chunks; the
per-chunk gate never shows a review `VERDICT:`. Under fan-out the equivalent
happens **per leaf before its merge** with no commit by the orchestrator — the
leaf has already committed on its branch (§Sequencing — Fan-out).

A three-chunk plan therefore yields three implement dispatches, three verifier
dispatches (plus redos), three per-chunk gates and **one** review dispatch with
**one** stage gate. The review still sees all chunks at once; the verifier sees
one.

### Sequencing — Fan-out (REQ-HARN-015)

`fan-out.md` §3 gains a verifier step between "await leaf return" and
"sequential merge":

```
for each leaf, on return:
  a. parse RETURN; scope check on <worktree>, <base>..<branch> → `SCOPE:` token
  b. dispatch CHUNK VERIFIER with Working directory = the leaf's worktree,
     Plan = the plan as seen on that branch, Chunk = the leaf's chunk(s)
     (BLOCKED / BUDGET_EXHAUSTED: no verifier; the orchestrator applies the
      returned checkpoint in §3e — harness-return-contract.md §RETURN.status Branching)
  c. render the PER-LEAF GATE — the same block as §Sequencing — Sequential Mode,
     `Files changed` taken from the branch's committed delta; NO commit by the
     orchestrator (the leaf already committed on its branch):
       proceed → branch is eligible for the sequential merge (§3b)
       fix     → NO merge; repair packet → redo dispatch on the same branch/worktree
                 (counts toward the per-chunk redo cap; or abort the group per REQ-ORCH-026)
       stop    → halt
```

Only branches whose per-leaf gate decision was `proceed` enter the merge order
(`proceed` is the default only on `CHUNK_VERDICT: PASS`; on `FAIL` it is an
explicit override). A leaf that owns several chunks gets
one verifier dispatch per chunk; all must PASS. The verifier runs **before**
merge so a FAIL never reaches the integration branch (marker `3`: `main`;
marker `4`: the workstream branch, `ws-integration.md`). After the last merge
the existing §3e bookkeeping runs (plan marks, traceability fills, the
orchestrator's Check 2 verification), then the single implement-stage review.

### FAIL Routing

A FAIL routes **only** to a repair packet for a redo dispatch of the same
chunk, chosen as `fix` at the per-chunk gate (`harness-return-contract.md`
§Repair Packet, with `failures` from the verifier and `findings: []`). It never
routes to a merge, to the implement-stage review, or to `sdd-replan` directly;
if redos exhaust the per-chunk cap (`harness-loop-control.md` §Redo Cap per
Chunk, `REDO_MAX`), the gate offers stop / manual intervention / authorized
extra redo, and the operator may choose a replan from there.

The reverse direction — routing the **implement-stage review's** findings back
to chunks for a loop-back-to-fix — is `harness-return-contract.md` §Finding →
Chunk Mapping: findings are grouped by affected REQ → spec → the chunk whose
tasks `trace to` that spec; unmappable or multi-chunk findings go into one
whole-plan fix dispatch (`target.chunk: all`). Each fix dispatch is followed by
the per-chunk gate for every chunk it touched, before the re-review.

### Ephemerality and Gate Text

The verifier's findings and token surface as text in the per-chunk gate block,
in the order REQ-ORCH-034 fixes (`RETURN.status` → `SCOPE:` →
`CHUNK_VERDICT:`); the review `VERDICT:` appears only at the stage gate after
all chunks (`orchestration.md` §v5). Nothing the verifier produces is written
to `docs/` by it or on its behalf; the durable effects are the redo's code
changes and, on exhaustion, the checkpoint under the task.

### Return Block Pinned Inside the Fenced Body (REQ-HARN-HARNESSP3-002)

[Changed 2026-09-18: the verifier template stated only "then the `RETURN:`
block, whose last line is `CHUNK_VERDICT:`", with the shape in a later prose
subsection. Spec-read defect.]

The verifier dispatch template's **fenced prompt body** must carry the literal
`RETURN:` key block in contract order — `status`, `budget_consumed`,
`files_written`, `commits`, `tasks_completed`, `traceability_fills`,
`chunk_close`, `failures`, `ledger`, `verified_do_not_touch`, `open_questions`,
`blocked_writes` — with `CHUNK_VERDICT: PASS | FAIL` as the last line, on its
own line, **inside** the block. A prose pointer outside the fence is no longer
sufficient. Everything else about the verifier — read-only write scope, budget,
ephemerality, never committing — is unchanged; this is a placement fix, and the
body here must stay byte-consistent with
`references/dispatch-templates.md` and `docs/spec/harness-return-contract.md`.

### Terminal Token at Column 0 (REQ-HARN-HARNESSP4-007)

[Added 2026-09-18, harness-p4 — REQ-HARN-HARNESSP4-007; `docs/ws/harness-p3/verification.md` §V9.
Contract only: the fenced body in §Verifier Dispatch Template is **not** edited
at this stage — it must stay byte-identical to `references/dispatch-templates.md`
until both change in one commit with the `[template-drift]` rule active.]

The `CHUNK_VERDICT: PASS | FAIL` line in the CHUNK VERIFIER dispatch body and its
`RETURN:` block sits at **column 0**, as `VERDICT:` (REVIEW) and `RED_VERDICT:`
(RED TEAM) already do, and `skills/sdd-orchestrate/SKILL.md` §The gate states
the parse rule as **`^CHUNK_VERDICT:` on the last non-blank line**, matching the
anchored wording it uses for the other two tokens. Today the template is the
outlier: two tokens are `^`-anchored, live leaves already render the third at
column 0, and an indented template invites a leaf to emit an indented token that
a future anchored parser would miss.

```
RETURN:
  status: …
  …
  blocked_writes: []
CHUNK_VERDICT: PASS | FAIL          # column 0 — the only key of the block not indented
```

Change discipline: `references/dispatch-templates.md` (source of record) and
this spec's §Verifier Dispatch Template fence are edited **in the same change**,
after the `[template-drift]` rule (`skill-lint-v5.md`, REQ-LINT-HARNESSP4-001)
has landed, so REQ-HARN-HARNESSP3-002's byte-consistency contract is preserved
mechanically. `docs/spec/adversarial-verify.md` restates no body that changes
here and is untouched.

## Verification

### Automated
- Lint `REQUIRED` rows: `CHUNK_VERDICT:` in `dispatch-templates.md` (verifier
  template) and its consumer in `sdd-orchestrate/SKILL.md`; `Budget:` and
  `Write scope:` present in the verifier template (`skill-lint-v5.md`).
- Grep: the verifier template contains no `sdd-review` and no `Skill tool`
  invocation.
- Grep: the four-layer table text in `skills/sdd-review/SKILL.md` and
  `CLAUDE.md` is unchanged (diff against the pre-cycle commit).
- Fixture: a verifier return with `check1: fail` yields FAIL; with `check1:
  pass`, `check3: advisory`, all gates exit 0 yields PASS.

### Manual
- Run a three-chunk plan sequentially under orchestrate: count 3 implement, 3
  verifier, 1 review dispatches; 3 per-chunk gates each showing
  `RETURN.status`, `SCOPE:`, `CHUNK_VERDICT:` and files changed, with the chunk
  committed only on `proceed`.
- Fan-out with two leaves, force one verifier FAIL: `git log` on the
  integration branch shows only the PASS branch merged; the FAIL leaf received a
  redo prompt carrying a repair packet.
- Scope check on a verifier return reports zero observed writes.

### Acceptance Criteria
- [ ] A fresh verifier re-runs Check 1, Check 3 and the quality gates per closed chunk and returns `CHUNK_VERDICT: PASS | FAIL` plus findings in the chunk-close report shape; Check 2 stays orchestrator-applied, Check 4 stays with implementer + review; implementer Step 4 unchanged; verifier is not `sdd-review`; FAIL routes to a repair packet only (REQ-HARN-014)
- [ ] Under fan-out one verifier runs per leaf inside its worktree before merge; FAIL branches are not merged (REQ-HARN-015)
- [ ] Sequential implement is dispatched per chunk with a `Chunk N` parameter; each chunk closes at a per-chunk gate (`proceed │ fix │ stop`; `fix` counts toward the per-chunk redo cap) before the orchestrator commits it; the review and its stage gate run once after all chunks (REQ-HARN-016)
- [ ] The verifier template carries only the listed slots including `Budget:`, an empty `Write scope:` and the `RETURN:` block with `CHUNK_VERDICT:`; it never commits; nothing is written to `docs/` for it (REQ-HARN-017)
- [ ] Four-layer table in `sdd-review` and `CLAUDE.md` unchanged (REQ-HARN-014)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed
- [ ] The chunk-verifier template's fenced body contains the full literal `RETURN:` key list in contract order plus the own-line `CHUNK_VERDICT:` token, and the shape is not reachable only from prose outside the fence (REQ-HARN-HARNESSP3-002)
- [ ] `grep -n '^  CHUNK_VERDICT:' docs/spec/harness-chunk-verifier.md` returns nothing — the §Verdict Rule example and the gate-text block both render the token at column 0; Q-IMPL-HARNESSP4-009 carries its fold-in status note with its body unchanged (REQ-QIMPL-HARNESSP5-001, owned by `deviation-protocol.md`)
- [ ] `grep -n '^  CHUNK_VERDICT:' skills/sdd-orchestrate/references/dispatch-templates.md` returns nothing and `grep -c '^CHUNK_VERDICT:'` on that file is ≥ 2; `SKILL.md` §The gate states `^CHUNK_VERDICT:`; the fenced bodies of `dispatch-templates.md` and this spec are byte-identical after the edit (`python3 tools/sdd-skill-lint.py` exits 0 with `[template-drift]` active) (REQ-HARN-HARNESSP4-007)

## Edge Cases

- **Plan has no `### Chunk N:` headers** (v2 vocabulary): chunk-close is
  inactive (`overview.md` §Plan Vocabulary), so no verifier is dispatched and
  the orchestrator says so at the gate; implement runs as one dispatch.
- **Chunk traces to a spec with no code-block types**: Check 1 reports "no
  extractable type definitions" (the XSPEC convention) and passes vacuously;
  the gate shows that line so a silent pass is visible.
- **Gate command missing from `CLAUDE.md`**: the orchestrator fills
  `{gate_commands}` from the project's build files or, failing that, dispatches
  with `tests only` and notes it at the gate — the verifier never invents
  commands.
- **Verifier budget exhausted before all gates ran**: `status:
  BUDGET_EXHAUSTED`, `CHUNK_VERDICT: FAIL` (unverified is not verified), and the
  orchestrator may re-dispatch the verifier with a larger budget before
  rendering the per-chunk gate (a verifier re-dispatch is not a redo).
- **Operator chooses `proceed` on a FAIL**: allowed as an explicit override; the
  gate text records `CHUNK_VERDICT: FAIL — proceeded by operator` and the chunk
  is committed / merged; nothing is persisted.
- **Flaky test**: a FAIL whose `failures[].test` passes on the redo with no
  code change is surfaced at the gate as `possible flake`; the orchestrator
  does not auto-PASS.
- **Verifier writes anyway**: the scope check tags every path `OUT`, the gate
  shows `SCOPE: VIOLATION`, and the writes are reverted before any redo.

## Cross-Spec Consistency (XSPEC)

- Check names, numbering and severities are those of `chunk-close-review.md`
  §Checklist (1 blocking, 2 blocking, 3 advisory, 4 advisory) — consistent; the
  verdict rule uses only Check 1 + gates for FAIL, matching the blocking tier.
- `review.md` §Trigger Classification "Skip — chunk-close boundaries" is
  honored: review is not dispatched per chunk; the verifier is not review.
- `orchestration.md` §Sequential Merge / §Merge-Conflict Handling (REQ-ORCH-025,
  -026, Q-IMPL-1 redo by re-derivation) are preserved; the verifier is inserted
  before merge and FAIL redo reuses the existing redo mechanism with a packet.
- `fan-out.md` §3e Check 2 deferral is preserved and referenced, not
  duplicated.
- `RETURN:` field names match `harness-return-contract.md`; the per-chunk gate
  consumes its §RETURN.status Branching table and `CHUNK_VERDICT` is listed
  there as the verifier-only key — consistent.
- The per-chunk gate block is byte-identical in `harness-write-scope.md`
  §Commit Ownership and `orchestration.md` §v5 — consistent.
- `ws-integration.md`: merge target under marker `4` is the workstream branch —
  restated identically.
- **No unresolved contradictions.**

**harness-p3 pass (2026-09-18).** No extractable type definitions in
harness-chunk-verifier.md. The verifier's fenced `RETURN:` key list is checked
identical to the one in `docs/spec/harness-return-contract.md` §RETURN Block;
`CHUNK_VERDICT:` is defined here and consumed by the per-chunk gate described
there.

## Open Questions

1. **Default-on vs opt-in.** RS-008 flagged per-chunk dispatch cost as a
   dogfooding question. Default: verifier **on** under orchestrate; the
   operator may disable it for a cycle at the fan-out opt-in gate (the same gate
   that chooses sequential vs fan-out), which is recorded as gate text only.
2. **Verifier for a chunk whose implementer already reported Check 1 `fail`
   and stopped.** Default: skip the verifier (the leaf is already BLOCKED) and
   go straight to the checkpoint / gate.
3. **REQ-ORCH-034 gate-text order vs the per-chunk gate.** REQ-ORCH-034 lists
   one ordered signal set per gate beginning with `VERDICT:`; with the
   per-chunk gate the implement stage has two gate kinds and no `VERDICT:`
   exists yet at the per-chunk one. Default adopted (operator decision D1,
   2026-09-17): per-chunk gate = `RETURN.status` → `SCOPE:` → `CHUNK_VERDICT:`;
   stage gate = the review `VERDICT:` plus the loop counters. **Resolved 2026-09-17**: REQ-ORCH-034 now carries an
   `[Updated 2026-09-17]` clarification stating exactly this split.

## Implementation Questions


### Q-IMPL-052: "grep for `sdd-review`" reads as "no sdd-review invocation"
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Verification — Automated
**Decision**: the verifier template is pasted verbatim and contains the prohibition line "do not invoke sdd-review or sdd-implement"; the automated check is read as zero hits for `Skill tool` and for `invoke sdd-` as an instruction, with the prohibition line as the sole `sdd-review` string.
**Rationale**: the spec's own template makes a literal zero-hit grep unsatisfiable.
**Date**: 2026-09-17 (Chunk 3)

### Q-IMPL-053: verifier opt-out renders a constant-shape gate line
**Tier**: 2 (spec ambiguity)
**Spec reference**: Open Question 1 (verifier default-on)
**Decision**: when the operator opts the verifier out at the implement gate, the per-leaf/per-chunk gate renders `CHUNK_VERDICT: (verifier disabled)` so the block shape stays constant.
**Rationale**: the spec says the opt-out is recorded as gate text but does not say how; a fixed-shape block stays greppable.
**Date**: 2026-09-17 (Chunk 3)

### Q-IMPL-054: PIPELINE slot naming for the per-chunk parameter
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sequencing — Sequential Mode
**Decision**: the PIPELINE template carries `{implement_only}Chunk: Chunk {N} — implement THIS chunk's tasks only`, mirroring the existing `{on_fix_only}` convention; the spec names the parameter "Chunk N" without a slot token.
**Rationale**: consistency with the template's existing conditional-slot style.
**Date**: 2026-09-17 (Chunk 3)

### Q-IMPL-HARNESSP4-009: The §Verdict Rule return-shape example keeps its indented token
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Terminal Token at Column 0 (REQ-HARN-HARNESSP4-007); §Acceptance Criteria (`grep -n '^  CHUNK_VERDICT:'` on `dispatch-templates.md` returns nothing)
**Decision**: the column-0 move is applied to the two `[template-drift]`-paired fences (the CHUNK VERIFIER dispatch body in `references/dispatch-templates.md` and this spec's §Verifier Dispatch Template restatement, byte-identical) and to the worked `yaml` return-shape example in `dispatch-templates.md` §Return contract, so the file-wide grep criterion holds. The twin `yaml` example under this spec's §Verdict Rule is **not** edited: it is not a lint pair, and the Chunk 7 write scope admits exactly one Approved-spec edit — the §Verifier Dispatch Template fence.
**Rationale**: the contract is the dispatch body a leaf is pasted, which now shows the unindented token; the §Verdict Rule example is illustrative prose whose indentation the acceptance criteria do not constrain, and widening an Approved-spec edit beyond the operator's one-path widening would be a scope violation, not a fix. A later specs pass may align the example.
**Date**: 2026-09-19 (harness-p4 Chunk 7)
**Status**: `[folded into §Verdict Rule, 2026-09-19]` (REQ-QIMPL-HARNESSP5-001) — the example's token is now at column 0; the entry body is unchanged.
