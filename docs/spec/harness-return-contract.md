---
status: Approved
last_updated: 2026-09-18
requires:
  - REQ-HARN-009
  - REQ-HARN-010
  - REQ-HARN-011
  - REQ-HARN-012
  - REQ-HARN-013
  - REQ-HARN-018
  - REQ-HARN-019
  - REQ-HARN-HARNESSP3-002
  - REQ-HARN-HARNESSP3-003
  - REQ-HARN-HARNESSP3-005
  - REQ-REDB-HARNESSP3-001
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
  # CHUNK_VERDICT: PASS | FAIL                               # chunk verifier returns ONLY (last line)
```

Key table — **every key is present** (empty list / omitted value where not
applicable); values are path references and one-line strings only. A key the
leaf omitted anyway **reads as empty** (`[]` / no value) and is surfaced as a
`RETURN: KEYS MISSING (<names>)` warning, not a pause. **Unknown keys are
ignored**, with one exception: `CHUNK_VERDICT`, the verifier-only key
(`harness-chunk-verifier.md` §Verdict Rule) — required on a verifier return,
and a warning when present on any other return.

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
| `CHUNK_VERDICT` | enum `PASS \| FAIL`, **verifier only**, last line | per-chunk gate (`harness-chunk-verifier.md`); ignored-with-warning elsewhere |

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
`budget_consumed`; `budget_consumed` is present but is not a map of unit →
integer (`RETURN: MALFORMED (budget_consumed shape)`) [Amended 2026-09-18,
REQ-HARN-HARNESSP3-003 — see §Malformed `budget_consumed` Is a Pause; the other
nine keys stay a `RETURN: KEYS MISSING` warning]; a `failures[]` entry lacks
`test` or `message`; or any value spans multiple lines (traceback smuggling). A malformed return is a **gate
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
  reason: REVIEW                                     # REVIEW | VERIFIER_FAIL | PARTIAL_CONTINUE | MERGE_CONFLICT
  iteration: 2 of 3                                  # harness-loop-control.md §Fix-Loop Cap (REVIEW) / per-chunk redo counter (others)
  budget: "1 chunk, ≤ 25 tool calls, ≤ 3 test runs"
  write_scope: [src/recon/**, tests/test_recon.py, docs/spec/recon.md]   # harness-write-scope.md
  target: {artifact_paths: [docs/plan.md], chunk: "Chunk 2: Reconciliation"}   # chunk: all — whole-plan fix (§Finding → Chunk Mapping)
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
- `reason` names why the packet exists; `MERGE_CONFLICT` packets add
  `conflict_paths` and `base` (see Edge Cases).

[Amended 2026-09-18, REQ-HARN-HARNESSP3-005] The packet carries **only**
findings against artifacts the fix leaf is scoped to touch. A review finding
raised against an out-of-scope artifact is **not** put in the packet (no
`carry_to_next_dispatch:` field is added): it is carried into the **next
pipeline dispatch's** `{deliverable_contract}` slot. See §Out-of-Fix-Scope
Review Findings Route to the Next Deliverable Contract.

### Finding → Chunk Mapping (implement-stage loop-back-to-fix)

The implement-stage review runs once after all chunks, so its findings must be
routed back to chunks before a fix dispatch can carry a chunk-sized `target`,
`write_scope` and `budget`. The orchestrator groups the Critical/Material
findings mechanically — no judgement, no paraphrase:

1'. **Location first (red-routed findings)** [Amended 2026-09-18,
   REQ-REDB-HARNESSP3-001]: if the routed finding's `failures[].location` names
   a file or chunk, resolve it to the chunk whose tasks' implementation modules
   include that file, and continue at step 2. Otherwise fall through to step 1.
   See §Red Break → Chunk Mapping Narrows on `failures[].location`.
1. **REQ → spec**: each finding's `affects` REQ IDs → the spec file(s) whose
   `requires:` frontmatter lists them (or the finding's `ref` path when it
   names a spec directly).
2. **Spec → chunk**: the plan chunk whose tasks `trace to` that spec
   (`### Chunk N:` headers; under marker `4` the workstream's plan).
3. **Group**: findings that resolve to exactly one chunk are grouped per chunk
   → one fix dispatch per affected chunk, in plan order, each with
   `target.chunk: "Chunk N: …"`, that chunk's default write scope and per-chunk
   budget.
4. **Unmappable or multi-chunk**: findings with no `affects`, a `ref` that is
   not a spec, a spec traced by no chunk, or a mapping to more than one chunk go
   together into **one whole-plan fix dispatch** with `target.chunk: all`, the
   union of the plan's chunk write scopes, dispatched after the per-chunk fix
   dispatches.

One review round is one fix iteration for the stage (`iteration N of MAX`)
regardless of how many chunk-grouped dispatches it fans into. Every fix
dispatch is followed by the scope check, one verifier dispatch per chunk it
touched (from `files_written`), and that chunk's per-chunk gate
(`harness-chunk-verifier.md` §Sequencing — Sequential Mode) before the
re-review.

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
| `reason` | orchestrator state: which event composed the packet |
| `conflict_paths`, `base` (`MERGE_CONFLICT` only) | disk: the paths `git merge` reported as conflicting; `git rev-parse` of the integration branch after the abort |

This table lives in `references/return-contract.md`; `SKILL.md` carries a stub.

### VERDICT Token (REQ-HARN-013)

`sdd-review` emits, on a line of its own, anywhere in its report
(conventionally next to the `**Verdict:**` line — position is not part of the
contract), a single token line:

```
VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
```

The orchestrator's token parser matches `^VERDICT:` **at line start** — so a
`CHUNK_VERDICT:` line never matches — and when the token occurs more than once
the **last occurrence wins** (the lint row for the consumer uses the equivalent
`(?<!CHUNK_)VERDICT:`, `skill-lint-v5.md` §REQUIRED Rows — Core Contracts). The
prose verdict and the token must agree (`Approve` ↔ `APPROVE`, `Approve
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

### `RETURN.status` Branching (per-chunk gate)

The leaf's `status` decides what runs between the return and the gate. For an
implement dispatch (sequential per chunk, or a fan-out leaf) the gate is the
**per-chunk gate** of `harness-chunk-verifier.md` §Sequencing — Sequential Mode
(`proceed │ fix │ stop`; under fan-out the per-leaf gate before merge). The
scope check always runs first (`harness-write-scope.md`).

| `status` | Then | Gate | Default choice | Per-chunk redo counter |
|---|---|---|---|---|
| `COMPLETE` | scope check → verifier on the chunk | per-chunk gate | `proceed` on PASS + CLEAN; `fix` otherwise | `fix` → +1 |
| `PARTIAL` | scope check → verifier on `tasks_completed` only | per-chunk gate | **`continue same chunk`** — a `fix` dispatch whose packet has `reason: PARTIAL_CONTINUE`, `failures: []`, `target` = the chunk with the remaining tasks named | counts as a redo → +1 |
| `BLOCKED` | scope check; **no verifier**; checkpoint written (sequential: by the leaf, into the plan) or applied (fan-out: by the orchestrator, §3e) | per-chunk gate **with a replan option** (REQ-ORCH-017 gate event) | replan route | not a redo |
| `BUDGET_EXHAUSTED` | as `BLOCKED`, plus `budget_consumed` shown against the dispatched `Budget:` | as `BLOCKED`; `fix` re-dispatches with a fresh per-chunk budget | replan │ `fix` (fresh budget) | `fix` → +1 |

For a non-implement stage (no chunks, no verifier) the same rows apply with
"verifier" removed and the gate being the stage gate after the review:
`COMPLETE` → scope check → review; any other status → gate pause before any
review is dispatched.

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

### Every Leaf Template Pins Its Return Block Inside the Fence (REQ-HARN-HARNESSP3-002)

[Changed 2026-09-18: spec-read — the template table maps the observed drift
exactly onto inside-the-fence vs outside-the-fence; the run corroboration behind
it is n = 3 and uncontrolled, so this is a structural fix, not a measured one.]

The literal `RETURN:` key block — every key, in contract order — must live
**inside the fenced prompt body** of every leaf dispatch template, never in
adjacent or later prose. Current state and required change:

| Template | Today | Required |
|----------|-------|----------|
| PIPELINE (`references/dispatch-templates.md` §PIPELINE) | literal key block inside the fence | unchanged |
| fan-out leaf (`references/fan-out.md` §2) | literal key block inside the fence | unchanged |
| fix re-dispatch | PIPELINE + `{on_fix_only}` | unchanged — no separate change needed |
| chunk verifier | prose pointer only ("then the `RETURN:` block, whose last line is `CHUNK_VERDICT:`"), shape in a later subsection | move the literal key block inside the fence, `CHUNK_VERDICT:` on its own line |
| red team | "Return in the shape below", shape in an adjacent subsection | move the literal key block inside the fence; the `Rn` line shape stays above the block and `RED_VERDICT:` is the own-line last line |
| review | no `RETURN:` block **by contract** (§6 — a review emits `VERDICT:` only) | pin the own-line `VERDICT: APPROVE │ APPROVE_WITH_FIXES │ REJECT` token inside the fenced body, on the same principle |

Invariant: no template's `RETURN:` shape is reachable only from prose outside
its fence. The same bodies are carried by
`docs/spec/harness-chunk-verifier.md` and `docs/spec/adversarial-verify.md`
§Red Dispatch Template.

### Malformed `budget_consumed` Is a Pause (REQ-HARN-HARNESSP3-003)

[Changed 2026-09-18: constructed boundary, ratified here rather than inherited —
the "elevate exactly these two" judgement has no run evidence either way.]

§Parsing gains exactly one condition:

```
RETURN: MALFORMED (budget_consumed shape)   # present but not a map of unit -> integer
```

Rationale: `status` and `budget_consumed` are the only two keys the **gate
arithmetic** consumes — `budget_consumed` is rendered at every gate against the
dispatched `Budget:` and sizes the next repair packet's `budget` — and `status`
already has a malformed condition, so this closes the pair.

The other nine keys stay a `RETURN: KEYS MISSING` **warning**:
`files_written` is independently cross-checked by the write-scope observation,
so an omitted list cannot hide a write; `tasks_completed`,
`traceability_fills`, `chunk_close`, `failures`, `ledger`,
`verified_do_not_touch`, `open_questions` and `commits` feed bookkeeping that
degrades to "nothing to do" or that the orchestrator can observe for itself.

`blocked_writes` is the **deliberate borderline case**, and §1 must record the
reasoning beside the warning so the boundary reads as a decision rather than an
omission: an omitted list silently loses content, but only when the leaf also
failed to write, which surfaces independently as the deliverable being absent
from the observed window.

### Out-of-Fix-Scope Review Findings Route to the Next Deliverable Contract (REQ-HARN-HARNESSP3-005)

[Changed 2026-09-18: observed gap, constructed remedy — specifies what the
operator did by hand on 2026-09-18 when a repair packet had no place for such a
finding.]

§3 states: a review finding raised against an artifact the fix leaf is **not**
scoped to touch is carried into the **next pipeline dispatch's**
`{deliverable_contract}` slot, not into the repair packet. No schema change — a
`carry_to_next_dispatch:` field was considered and is **not** worth the cost,
and the destination slot already exists.

### Red Break → Chunk Mapping Narrows on `failures[].location` (REQ-REDB-HARNESSP3-001)

[Changed 2026-09-18: the defect is spec-read (§5 step 4 produces `all` whenever
a spec is traced by more than one chunk; §B4 observed both breaks landing as
`target.chunk: all`); the narrowing step itself is **constructed and
unexercised** — but it cannot regress anything, because it inserts a more
specific resolution ahead of an unchanged fallback.]

§5's red entry gains a **step 1'**, ahead of the heading-spec step:

```
1'. If the routed Rn's failures[].location names a file or chunk, resolve it to
    the chunk whose tasks' implementation modules include that file.
    Otherwise fall back to the spec named in the
    "## Red team — <spec.md>" heading and continue at step 2 as today.
```

The whole-plan fallback stays the rule; this only narrows the input, using
evidence red already returns — the red template is given the plan for exactly
that purpose ("supplies the `### Chunk N:` vocabulary red uses in
`failures[].location`").

**Declined**: asking red to name the narrowest owning symbol as a new field on
`Rn`. That would make the read-only adversarial leaf judge code ownership, which
REQ-HARN-019 / REQ-ORCH-012 keep out of leaves, and it widens red's return shape
for a mapping the orchestrator can perform from `location` alone.

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
- [ ] Every leaf template's return step ends with the `RETURN:` block, `status:` first on its own line, the listed keys, path/one-line values only; missing keys read as empty with a warning, unknown keys are ignored except `CHUNK_VERDICT`; missing or malformed block pauses at the gate (REQ-HARN-009)
- [ ] `failures[]` entries carry `test / kind / message / location`; no traceback anywhere in a return or packet (REQ-HARN-010)
- [ ] `dispatch-templates.md` `{on_fix_only}` carries `{repair_packet}` with the listed fields; `spec_excerpt` is path + heading + line range only (REQ-HARN-011)
- [ ] `references/return-contract.md` carries the field-source table; `SKILL.md` stubs to it; `findings` are byte-identical to report lines apart from structural quoting (REQ-HARN-012)
- [ ] `sdd-review` emits the own-line `VERDICT:` token; the orchestrator parses `^VERDICT:` at line start, last occurrence wins; `SKILL.md` §The gate names the three values and points to the `VERDICT:` and `RETURN.status` branching tables; missing token → malformed review (REQ-HARN-013)
- [ ] A second fix prompt for one stage holds one packet, latest paths only, no fenced report; slot-set overflow warns (REQ-HARN-018)
- [ ] §Orchestrator-Only Work states the routing principle with pointers to both references files; no template delegates a routing decision (REQ-HARN-019)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed
- [ ] The fenced bodies of the chunk-verifier and red-team templates each contain the full literal `RETURN:` key list in contract order; the review body contains the literal own-line `VERDICT:` token line (REQ-HARN-HARNESSP3-002)
- [ ] No template's `RETURN:` shape is reachable only from prose outside its fence (REQ-HARN-HARNESSP3-002)
- [ ] §Parsing lists the `RETURN: MALFORMED (budget_consumed shape)` row; a fixture return whose `budget_consumed` is prose pauses the gate, and a fixture missing only `ledger` renders a `KEYS MISSING` warning and does **not** pause (REQ-HARN-HARNESSP3-003)
- [ ] §1 carries the `blocked_writes`-stays-a-warning note with its reasoning (REQ-HARN-HARNESSP3-003)
- [ ] §3 names `{deliverable_contract}` as the destination for out-of-fix-scope review findings and states that no repair-packet field is added (REQ-HARN-HARNESSP3-005)
- [ ] §5's red entry lists step 1' ahead of the heading-spec step; a fixture `Rn` whose `failures[].location` names a file owned by one chunk routes `target.chunk: <that chunk>`, and a fixture with no usable `location` still routes `target.chunk: all` (REQ-REDB-HARNESSP3-001)

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
  `reason: VERIFIER_FAIL`, `findings: []`, `failures` from the verifier's
  `RETURN.failures`; `stage: implement`, `iteration` from the per-chunk redo
  counter.
- **Merge-abort re-derivation packet** (`orchestration.md` §Merge-Conflict
  Handling, REQ-ORCH-026 / Q-IMPL-1): `reason: MERGE_CONFLICT`, `failures: []`,
  `findings: []`, `conflict_paths: [<paths git merge reported>]`, `base: <sha>`
  — the fresh integration-branch commit the leaf must branch from and
  re-derive its chunk on — plus the usual `target`, `write_scope`, `budget`,
  `iteration` (per-chunk redo counter) and `ledger_summary` /
  `verified_do_not_touch` lifted from the leaf's last `RETURN`. No diff or
  conflict-marker text is carried.
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
- §RETURN.status Branching feeds the per-chunk gate of
  `harness-chunk-verifier.md` (identical `proceed │ fix │ stop` vocabulary) and
  the `PARTIAL_CONTINUE` / `VERIFIER_FAIL` redos increment the same per-chunk
  redo counter as `harness-loop-control.md` §Redo Cap per Chunk — consistent.
- §Finding → Chunk Mapping uses the plan's `traces to` and the spec `requires:`
  frontmatter only (`plan-management.md`, `overview.md` §Frontmatter) — no new
  metadata.
- **No unresolved contradictions.**

**harness-p3 pass (2026-09-18).** No extractable type definitions in
harness-return-contract.md (prose/table contracts only) — reported explicitly
rather than passing silently. Token-level checks:

- `RETURN:`, `status:`, `budget_consumed`, `blocked_writes`, `VERDICT:`,
  `CHUNK_VERDICT:`, `RED_VERDICT:`, `RED_BREAK` — the key list here is
  byte-consistent with `docs/spec/harness-chunk-verifier.md` and
  `docs/spec/adversarial-verify.md` after this amendment.
- `target.chunk` is defined in this spec's `RED_BREAK` packet and referenced by
  `docs/spec/adversarial-verify.md` §Fix-Loop Interaction; both carry step 1'.
- `{deliverable_contract}` is a `references/dispatch-templates.md` slot name,
  used here and not redefined.

## Open Questions

1. **`PARTIAL` vs `COMPLETE` for a per-chunk implement dispatch that
   legitimately leaves later chunks untouched.** Default: `COMPLETE` refers to
   the dispatch's deliverable contract (the assigned chunk), not the plan.
2. **`message` length cap.** Default 200 characters; the leaf truncates with
   `…` and never wraps to a second line.

## Implementation Questions

### Q-IMPL-082: repair packet header emitted once, slot holds the body
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Repair Packet
**Decision**: the PIPELINE template's `{on_fix_only}` block carries the `Repair packet (fixed shape …):` header; the `{repair_packet}` slot holds the body from `stage:` on. Literal composition from the spec's fixture (which shows the header as line 1) would emit two headers.
**Rationale**: found by the Chunk 6 holistic fixture walkthrough; one header keeps the slot-set check (§8) exact.
**Date**: 2026-09-17 (Chunk 6)


### Q-IMPL-HARNESSP2-003: RED_VERDICT parsing, RED_BREAK packet reason and the review-consumer regex
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Malformed Returns, §Repair Packet, §Finding → Chunk Mapping, §VERDICT Token
**Decision**: Extended by `adversarial-verify.md` (REQ-REDB-HARNESSP2-005/-009 amendment 2026-09-17): the malformed table gains the `RED_VERDICT:` rows; the repair-packet `reason` enum gains `RED_BREAK`; the finding → chunk mapping is reused with the spec taken from red's `## Red team — <spec.md>` heading in place of `affects`; the review-consumer lint regex becomes `(?<!CHUNK_)(?<!RED_)VERDICT:`. `arbitrated-handoff.md` annotates third-opinion review records with `dispatch.reason: THIRD_OPINION` in telemetry only — not a packet reason.
**Rationale**: Tokens are defined once, in the spec that introduces them; this spec keeps the parser rules it already owns and points at the extensions.
**Date**: 2026-09-17 (harness-p2 specs stage)

### Q-IMPL-HARNESSP3-003: Step 1' resolves a file to a chunk via the plan's task-to-module mapping
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Red Break
**Decision**:

`failures[].location` is a `path:line` or a chunk name. Decision: match the path
against the implementation modules named by each `### Chunk N` task in the active
plan; a path owned by exactly one chunk resolves to that chunk, a path owned by
more than one, or by none, falls through to the unchanged heading-spec step
rather than guessing. A `location` that already names a chunk is used verbatim.
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP3-004: "map of unit -> integer" is checked structurally, not by unit vocabulary
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Malformed `budget_consumed` Is a Pause
**Decision**:

The `budget_consumed` malformed condition tests that the value parses as a
mapping whose every value is an integer. The **unit names** are not
constrained — `tool_calls`, `test_runs` and any stage-specific unit are all
legal — so the check never pauses a gate over vocabulary drift, only over shape.
**Date**: 2026-09-18 (specs stage)
