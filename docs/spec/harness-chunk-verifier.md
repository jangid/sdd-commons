---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-HARN-014
  - REQ-HARN-015
  - REQ-HARN-016
  - REQ-HARN-017
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
then the RETURN: block, whose last line is
  CHUNK_VERDICT: PASS | FAIL
on its own.
```

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
  files_written: []
  failures:
    - {test: "pytest -q", kind: assertion, message: "1 failed: tests/test_recon.py::test_gap_report", location: src/recon/engine.py:142}
  CHUNK_VERDICT: FAIL
```

`CHUNK_VERDICT:` is the last line of the block (or the line immediately after
it); the orchestrator accepts either placement and treats a missing or
unrecognized token as a malformed return (`harness-return-contract.md`
§Malformed Returns). `files_written` must be `[]`; the scope check on a verifier
return must observe zero writes (`harness-write-scope.md`).

### Sequencing — Sequential Mode (REQ-HARN-016)

Under `sdd-orchestrate` sequential mode the implement stage is dispatched
**per chunk**, in plan order. `dispatch-templates.md` §PIPELINE (implement)
gains a `Chunk N` parameter in its deliverable contract, exactly as fan-out
already tells a leaf which chunk-group to run; `sdd-implement` is not modified
(REQ-ORCH-001).

```
for each `### Chunk N:` in plan order:
  1. snapshot (harness-write-scope.md) → dispatch PIPELINE implement, Chunk N
  2. parse RETURN; scope check → gate text
  3. dispatch CHUNK VERIFIER for Chunk N (repo root)
  4. CHUNK_VERDICT: PASS → orchestrator commits (commit ownership) → next chunk
     CHUNK_VERDICT: FAIL → compose repair packet (failures ← verifier RETURN.failures,
                          findings: [], iteration ← per-chunk redo counter)
                          → redo dispatch for Chunk N → back to 2
after the last chunk: dispatch the implement-stage sdd-review once on the merged state
```

A three-chunk plan therefore yields three implement dispatches, three verifier
dispatches (plus redos) and **one** review dispatch. The review still sees all
chunks at once; the verifier sees one.

### Sequencing — Fan-out (REQ-HARN-015)

`fan-out.md` §3 gains a verifier step between "await leaf return" and
"sequential merge":

```
for each leaf, on return:
  a. parse RETURN; scope check on <worktree>, <base>..<branch> → gate text
  b. dispatch CHUNK VERIFIER with Working directory = the leaf's worktree,
     Plan = the plan as seen on that branch, Chunk = the leaf's chunk(s)
  c. CHUNK_VERDICT: PASS → branch is eligible for the sequential merge (§3b)
     CHUNK_VERDICT: FAIL → NO merge; repair packet → redo dispatch on the same
                          branch/worktree (or abort the group per REQ-ORCH-026)
```

Only PASS branches enter the merge order. A leaf that owns several chunks gets
one verifier dispatch per chunk; all must PASS. The verifier runs **before**
merge so a FAIL never reaches the integration branch (marker `3`: `main`;
marker `4`: the workstream branch, `ws-integration.md`). After the last merge
the existing §3e bookkeeping runs (plan marks, traceability fills, the
orchestrator's Check 2 verification), then the single implement-stage review.

### FAIL Routing

A FAIL routes **only** to a repair packet for a redo dispatch of the same
chunk (`harness-return-contract.md` §Repair Packet, with `failures` from the
verifier and `findings: []`). It never routes to a merge, to the implement-stage
review, or to `sdd-replan` directly; if redos exhaust the per-chunk cap
(`harness-loop-control.md` §Redo Cap), the gate offers stop / manual
intervention / authorized extra redo, and the operator may choose a replan from
there.

### Ephemerality and Gate Text

The verifier's findings and token surface at the gate as text, per chunk, in
the order REQ-ORCH-034 fixes (after the review `VERDICT:`, before the `SCOPE:`
block). Nothing the verifier produces is written to `docs/` by it or on its
behalf; the durable effects are the redo's code changes and, on exhaustion, the
checkpoint under the task.

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
  verifier, 1 review dispatches.
- Fan-out with two leaves, force one verifier FAIL: `git log` on the
  integration branch shows only the PASS branch merged; the FAIL leaf received a
  redo prompt carrying a repair packet.
- Scope check on a verifier return reports zero observed writes.

### Acceptance Criteria
- [ ] A fresh verifier re-runs Check 1, Check 3 and the quality gates per closed chunk and returns `CHUNK_VERDICT: PASS | FAIL` plus findings in the chunk-close report shape; Check 2 stays orchestrator-applied, Check 4 stays with implementer + review; implementer Step 4 unchanged; verifier is not `sdd-review`; FAIL routes to a repair packet only (REQ-HARN-014)
- [ ] Under fan-out one verifier runs per leaf inside its worktree before merge; FAIL branches are not merged (REQ-HARN-015)
- [ ] Sequential implement is dispatched per chunk with a `Chunk N` parameter; review runs once after all chunks (REQ-HARN-016)
- [ ] The verifier template carries only the listed slots including `Budget:`, an empty `Write scope:` and the `RETURN:` block with `CHUNK_VERDICT:`; it never commits; nothing is written to `docs/` for it (REQ-HARN-017)
- [ ] Four-layer table in `sdd-review` and `CLAUDE.md` unchanged (REQ-HARN-014)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed

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
  orchestrator may re-dispatch the verifier with a larger budget before issuing
  a repair packet.
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
- `RETURN:` field names match `harness-return-contract.md` — consistent.
- `ws-integration.md`: merge target under marker `4` is the workstream branch —
  restated identically.
- **No unresolved contradictions.**

## Open Questions

1. **Default-on vs opt-in.** RS-008 flagged per-chunk dispatch cost as a
   dogfooding question. Default: verifier **on** under orchestrate; the
   operator may disable it for a cycle at the fan-out opt-in gate (the same gate
   that chooses sequential vs fan-out), which is recorded as gate text only.
2. **Verifier for a chunk whose implementer already reported Check 1 `fail`
   and stopped.** Default: skip the verifier (the leaf is already BLOCKED) and
   go straight to the checkpoint / gate.
