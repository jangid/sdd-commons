---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-HARN-009
  - REQ-HARN-010
  - REQ-HARN-011
  - REQ-HARN-012
  - REQ-HARN-013
  - REQ-HARN-018
  - REQ-HARN-019
---

# Harness Return Contract

## Context

Today a dispatched leaf returns free-form text ("files written + a one-paragraph
summary"), and `sdd-review` returns a prose report whose verdict the orchestrator
has to read out of a bold line. RS-008 Q3 found there is no structured failure
or attempt data in any return, so a fixed-shape fix re-dispatch is impossible
without first making the leaf return structured. RS-008 Q4 found the review
verdict is not machine-parseable.

This spec defines the leaf → orchestrator and reviewer → orchestrator channel:
the `RETURN:` block every leaf ends with, the one-line `failures[]` shape, the
repair packet a fix re-dispatch carries, the three sources the orchestrator may
fill it from, the `VERDICT:` token and its branching table, the pruned-state
rule for re-dispatches and the principle that routing is orchestrator-only. It
fulfils REQ-HARN-009..013, REQ-HARN-018 and REQ-HARN-019. The procedure text
lands in `skills/sdd-orchestrate/references/return-contract.md` with a stub in
`SKILL.md` (procedure-placement rule, `harness-loop-control.md`).

## Design

### RETURN Block (REQ-HARN-009)

Every **leaf** dispatch template — pipeline, fix re-dispatch, fan-out leaf,
chunk verifier — instructs the subagent to end its return text with a `RETURN:`
block. The block is YAML-shaped, indented under the literal line `RETURN:`, with
`status:` as its **first** key on its own line.

```yaml
RETURN:
  status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED   # own line, first key
  budget_consumed: {tool_calls: 22, test_runs: 3}           # same units as the dispatched Budget:
  files_written: [docs/plan.md, src/recon/engine.py, tests/test_recon.py]
  commits: [3f2a1c9]                                         # fan-out leaves only; else []
  tasks_completed: ["Chunk 2 task 1", "Chunk 2 task 2"]
  traceability_fills:
    - {req: REQ-RECON-003, test: tests/test_recon.py::test_drift, impl: src/recon/engine.py}
  chunk_close: {chunk: 2, check1: pass, check2: deferred, check3: advisory, check4: pass,
                overrides: ["check3: covered by tests/test_e2e.py"]}
  failures: []                                               # see §Failures; empty when COMPLETE
  ledger: []                                                 # harness-loop-control.md §Attempt Ledger
  verified_do_not_touch: []
  open_questions: ["spec §Gap report silent on overlapping windows — filed Q-IMPL-021 (Tier 2)"]
  blocked_writes: []                                         # [{path, content}] labeled fallback
```

Key table — every key is present (empty list / omitted-value where not
applicable); values are path references and one-line strings only.

| Key | Type | Consumer |
|---|---|---|
| `status` | enum, first key | gate text (REQ-ORCH-034); `BLOCKED`/`BUDGET_EXHAUSTED` → checkpoint path |
| `budget_consumed` | map unit → count | gate text; sizes next packet `budget` |
| `files_written` | path list | scope check (`harness-write-scope.md`); orchestrator commit for pipeline dispatches |
| `commits` | sha list | scope check committed delta; fan-out merge |
| `tasks_completed` | task label list | plan `[x]` marks (`fan-out.md` §3e step 1) |
| `traceability_fills` | `{req,test,impl}` list | traceability Test/Implementation columns (§3e step 2) |
| `chunk_close` | per-check status + overrides | gate text; verifier cross-check |
| `failures` | `{test,kind,message,location}` list | repair packet; checkpoint `failing:` lines |
| `ledger` | `{attempt,hypothesis,change,result}` list | repair packet `ledger_summary`; checkpoint |
| `verified_do_not_touch` | path list | repair packet, verbatim |
| `open_questions` | one-line list | checkpoint `open question:`; gate text |
| `blocked_writes` | `{path, content}` list | orchestrator persistence **after** scope match (REQ-HARN-023) |

Status semantics: `COMPLETE` — deliverable contract met; `PARTIAL` — some
tasks done, none blocked, budget not exhausted (e.g. the leaf hit its
deliverable boundary early); `BLOCKED` — stuck detection fired, checkpoint
composed; `BUDGET_EXHAUSTED` — per `harness-loop-control.md` §Budget
Exhaustion, `budget_consumed` mandatory.

**Why a block, not a summary paragraph**: the orchestrator's downstream steps
(plan marks, traceability fills, packet composition, checkpoint, scope check)
each need one field; a paragraph forces the orchestrator to paraphrase, which
REQ-HARN-012 forbids. Key names may be renamed by implementation only if the
lint markers (`RETURN:` / `status:`) and the load-bearing decisions — block
first, own-line status, one-line failures, no tracebacks — survive.

### Malformed Returns

The orchestrator parses the block; it never infers success from prose. A return
is **malformed** when: the `RETURN:` line is absent; `status:` is not the first
key or not one of the four values; `status: BUDGET_EXHAUSTED` lacks
`budget_consumed`; a `failures[]` entry lacks `test` or `message`; or any value
spans multiple lines (traceback smuggling). A malformed return is a **gate
pause** (REQ-ORCH-018 analogue): the gate shows `RETURN: MALFORMED (<reason>)`,
the raw tail of the return, and `re-dispatch | accept manually | stop`. It is
never treated as `COMPLETE`.

### Failures Are One-Line (REQ-HARN-010)

```yaml
failures:
  - {test: tests/test_recon.py::test_gap_report, kind: assertion,
     message: "AssertionError: expected 3 gaps, got 2", location: src/recon/engine.py:142}
```

- `test`: test id or the gate command that failed (`ruff check .`).
- `kind` ∈ {`assertion`, `error`, `lint`, `type`, `build`}.
- `message`: the last frame / one line, ANSI-stripped, ≤ 200 chars.
- `location`: `path:line` where known, else omitted.

Tracebacks and raw tool output are never carried in a return or a packet; they
are regenerable by re-running `test`.

### Repair Packet (REQ-HARN-011)

A fix re-dispatch — pipeline loop-back-to-fix, or a fan-out / per-chunk redo
after `CHUNK_VERDICT: FAIL` or a merge abort — carries a `{repair_packet}` slot
in the pipeline template's `{on_fix_only}` block, replacing the free-form
`{review_findings}` slot. Fixed shape:

```yaml
Repair packet (fixed shape — act on it; do not re-derive the history):
  stage: implement
  iteration: 2 of 3                                  # harness-loop-control.md §Fix-Loop Cap
  budget: "1 chunk, ≤ 25 tool calls, ≤ 3 test runs"
  write_scope: [src/recon/**, tests/test_recon.py, docs/spec/recon.md]   # harness-write-scope.md
  target: {artifact_paths: [docs/plan.md], chunk: "Chunk 2: Reconciliation"}
  failures:                                          # verbatim RETURN.failures / verifier failures
    - {test: tests/test_recon.py::test_gap_report, kind: assertion,
       message: "AssertionError: expected 3 gaps, got 2", location: src/recon/engine.py:142}
  findings:                                          # verbatim Critical/Material lines from the review
    - {id: C1, text: "gap detection ignores overlapping windows", ref: "docs/spec/recon.md §Gap report",
       affects: [REQ-RECON-003], fix: "treat overlap as one gap"}
  spec_excerpt: [{path: docs/spec/recon.md, section: "§Gap report", lines: "88-104"}]
  ledger_summary:
    - "attempt 1: engine.py key by contract_id -> test_gap_report still fails"
    - "attempt 2: engine.py:140 range(n+1) -> test_drift REGRESSED (reverted)"
  verified_do_not_touch: [tests/test_bootstrap.py, src/recon/bootstrap.py]
```

Rules:

- `spec_excerpt` entries are **path + section heading + line range only**,
  rendered in prose as `docs/spec/<file>.md § <heading> L<from>-<to>`. No quoted
  spec text — the leaf reads the lines itself. *(Changed from RS-008 Schema 2,
  which allowed "≤ 20 lines quoted": REQ-HARN-011 pins path-only so the packet
  can never carry accumulated artifact content.)*
- `findings` entries are the review report's Critical/Material lines split into
  `id / text / ref / affects / fix` — byte-identical to the report apart from
  that structural quoting. Minor findings are not carried.
- `ledger_summary` has exactly one line per prior attempt, formed
  `attempt N: <change> -> <result>` from `RETURN.ledger`.
- The packet contains no reviewer reasoning, no quoted artifact content, no
  prior packets — REQ-ORCH-012 holds by construction.
- Leaf instruction (template text): "Act on the packet. Do not re-derive the
  history, re-read prior reviews, or re-open attempts listed in
  `ledger_summary`. Do not modify `verified_do_not_touch` paths."

### Field Sources (REQ-HARN-012)

The orchestrator fills every packet field from exactly one of three sources, or
from its own state. It never paraphrases, summarizes, or adds reasoning.

| Field | Source |
|---|---|
| `failures` | previous leaf's or verifier's `RETURN.failures`, verbatim |
| `ledger_summary` | previous `RETURN.ledger`, one line per entry |
| `verified_do_not_touch` | previous `RETURN.verified_do_not_touch`, verbatim |
| `findings` | review report Critical/Material lines, lifted line-for-line |
| `target` | disk: plan path + chunk header the stage is working |
| `spec_excerpt` | disk: the spec file, heading and line range the finding's `ref` resolves to — path/heading/lines only |
| `stage`, `iteration`, `budget`, `write_scope` | orchestrator state (`harness-loop-control.md`, `harness-write-scope.md`) |

This table lives in `references/return-contract.md`; `SKILL.md` carries a stub.

### VERDICT Token (REQ-HARN-013)

`sdd-review` emits, immediately after its `**Verdict:**` line, a single line on
its own:

```
VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
```

The prose verdict and the token must agree (`Approve` ↔ `APPROVE`, `Approve
with fixes` ↔ `APPROVE_WITH_FIXES`, `Reject` ↔ `REJECT`); the rest of the
report (Strengths / Critical–Material–minor / Recommendation) and `sdd-review`'s
scope boundaries are unchanged.

Branching table (orchestrator; procedure in `references/return-contract.md`,
value list in `SKILL.md` §The gate):

| Token | Gate offers | Packet |
|---|---|---|
| `APPROVE` | proceed (default) │ stop | none |
| `APPROVE_WITH_FIXES` | proceed │ loop-back-to-fix (re-review optional per the existing shortcut) │ stop | findings carried into the packet |
| `REJECT` with actionable findings | loop-back-to-fix (subject to the fix-loop cap) │ stop | findings carried into the packet |
| `REJECT` with no actionable findings | pause: re-dispatch │ override │ stop (REQ-ORCH-018) | none |
| missing / unrecognized / disagrees with prose | `REVIEW: MALFORMED` pause: re-dispatch review │ accept prose manually │ stop | none |

The orchestrator never classifies a verdict by parsing prose; when the token is
missing it surfaces the review as malformed rather than guessing.

### Pruned State on Re-dispatch (REQ-HARN-018)

A fix or redo dispatch prompt contains exactly the template's slot set with:

- **one** repair packet — the latest — never prior packets or prior reports;
- the **latest** artifact paths only;
- large content by reference (spec by path + heading + line range; everything
  else by path);
- no conversation history, no fenced review report, no quoted spec text.

Before dispatching, the orchestrator checks the prompt against the template's
slot set; any content outside a slot, or a second `Repair packet` header,
triggers an operator-visible warning `DISPATCH: PROMPT EXCEEDS TEMPLATE SLOTS`
at the gate and the prompt is trimmed before dispatch. The packet *is* the
pruned state; no separate mechanism is needed.

### Orchestrator Owns Routing (REQ-HARN-019)

The following are orchestrator-only and never appear as instructions in a
pipeline, fix, fan-out, verifier or review template: phase-detection relay;
`VERDICT:` classification; `CHUNK_VERDICT:` and `SCOPE:` interpretation;
fix / redo / replan cap arithmetic; packet composition; the decision to merge,
re-dispatch, replan or stop. `sdd-orchestrate/SKILL.md` §Orchestrator-Only Work
states this as a principle beside REQ-ORCH-030 with pointers to
`references/return-contract.md` (verdict / status branching, packet
composition) and `references/write-scope.md` (`SCOPE:` branching). Templates
tell a subagent what to *produce* (block, token, findings) — never what to
*decide next*.

## Verification

### Automated
- Lint `REQUIRED` rows: `RETURN:` and `status:` in the leaf templates;
  `{repair_packet}` in `dispatch-templates.md`; `VERDICT:` producer in
  `sdd-review/SKILL.md` and consumer in `sdd-orchestrate/SKILL.md`
  (`skill-lint-v5.md`).
- Grep: no dispatch template contains "decide the next stage", "classify the
  verdict" or "judge scope" as an instruction to the subagent.
- Fixture: a two-iteration packet has exactly two `ledger_summary` lines; its
  `spec_excerpt` matches `^docs/spec/[^ ]+\.md § .+ L\d+-\d+$` when rendered
  and contains no quoted spec text.
- Fixture: a packet fixture and a return fixture contain no multi-line
  `message` and no `Traceback` token.
- Fixture: `findings[].text` equals the review report line text after stripping
  the `- C1: ` prefix and ` — [file:section]` suffix.

### Manual
- Dispatch a pipeline stage, force a `REJECT`, loop-back once: the second fix
  prompt contains one `Repair packet` header, no fenced report, no quoted spec
  text; the gate showed `VERDICT: REJECT` as a parsed value.
- Remove the `VERDICT:` line from a review return: the gate shows
  `REVIEW: MALFORMED` and offers re-dispatch, not proceed.

### Acceptance Criteria
- [ ] Every leaf template's return step ends with the `RETURN:` block, `status:` first on its own line, the listed keys, path/one-line values only; missing or malformed block pauses at the gate (REQ-HARN-009)
- [ ] `failures[]` entries carry `test / kind / message / location`; no traceback anywhere in a return or packet (REQ-HARN-010)
- [ ] `dispatch-templates.md` `{on_fix_only}` carries `{repair_packet}` with the listed fields; `spec_excerpt` is path + heading + line range only (REQ-HARN-011)
- [ ] `references/return-contract.md` carries the field-source table; `SKILL.md` stubs to it; `findings` are byte-identical to report lines apart from structural quoting (REQ-HARN-012)
- [ ] `sdd-review` emits the own-line `VERDICT:` token; `SKILL.md` §The gate names the three values and points to the branching table; missing token → malformed review (REQ-HARN-013)
- [ ] A second fix prompt for one stage holds one packet, latest paths only, no fenced report; slot-set overflow warns (REQ-HARN-018)
- [ ] §Orchestrator-Only Work states the routing principle with pointers to both references files; no template delegates a routing decision (REQ-HARN-019)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed

## Edge Cases

- **Leaf returns the block twice** (e.g. once per chunk): the orchestrator
  takes the last block and flags `RETURN: MULTIPLE` as a warning, not a pause.
- **`status: COMPLETE` with non-empty `failures`**: contradictory → malformed.
- **Review with `APPROVE` token but Critical findings listed**: token and
  prose disagree → malformed (the reviewer's own definitions forbid this).
- **Finding `ref` that does not resolve to a heading**: `spec_excerpt` carries
  the path with `section: (unresolved)` and no line range; the orchestrator
  notes it at the gate rather than quoting text to compensate.
- **Redo packet with no review findings** (verifier FAIL before any review):
  `findings: []`, `failures` from the verifier's `RETURN.failures`; `stage:
  implement`, `iteration` from the per-chunk redo counter.
- **Blocked write for a path outside scope**: `blocked_writes` is parsed here
  but the refusal is `harness-write-scope.md` §Blocked-Write Fallback.

## Cross-Spec Consistency (XSPEC)

- No language-typed code blocks; XSPEC runs on YAML field names.
- `ledger` fields match `harness-loop-control.md` §Attempt Ledger exactly.
- `chunk_close` per-check names (`check1..check4`, `pass | deferred | advisory
  | fail`, `overrides`) map onto `chunk-close-review.md` §Chunk Close Report
  statuses (`pass | block`, `pass | advisory`); `deferred` is the fan-out Check 2
  deferral already defined in `fan-out.md` §2 — consistent, additive.
- `VERDICT:` values are a 1:1 encoding of `review.md` §Report Format's three
  verdicts; the "Approve with fixes → proceed without re-review" definition is
  preserved via the existing gate shortcut in `orchestration.md` — consistent.
- `orchestration.md` §Gate Protocol `loop-back-to-fix` ("only the review
  findings + relevant artifact paths") is satisfied by the packet's `findings`
  + `target` + `spec_excerpt` — consistent; `{review_findings}` slot is
  superseded by `{repair_packet}` (recorded in the orchestration.md v5 section).
- `SCOPE:` and `CHUNK_VERDICT:` are defined in `harness-write-scope.md` and
  `harness-chunk-verifier.md`; referenced here by name only — consistent.
- **No unresolved contradictions.**

## Open Questions

1. **`PARTIAL` vs `COMPLETE` for a per-chunk implement dispatch that
   legitimately leaves later chunks untouched.** Default: `COMPLETE` refers to
   the dispatch's deliverable contract (the assigned chunk), not the plan.
2. **`message` length cap.** Default 200 characters; the leaf truncates with
   `…` and never wraps to a second line.
