# Return Contract (leaf → orchestrator, reviewer → orchestrator)

The full procedure text for the structured channel between a dispatched
subagent and the `orchestrate` driver. `../SKILL.md` (§LOOP, §The gate,
§Orchestrator-Only Work) carries a stub and points here. The contract is
defined by `docs/spec/harness-return-contract.md` (REQ-HARN-009..013,
REQ-HARN-018, REQ-HARN-019); the schemas and tables below are pasted from it,
never paraphrased.

Two producers, one consumer:

- every **leaf** dispatch (pipeline, fix re-dispatch, fan-out leaf, chunk
  verifier, red team) ends its return text with the `RETURN:` block (§1);
- `review` emits an own-line `VERDICT:` token (§6); the red team leaf
  emits an own-line last-line `RED_VERDICT:` token (§6a);
- the **orchestrator** parses both, composes repair packets (§4) and branches
  (§6, §7). Routing is orchestrator-only (§9) — templates tell a subagent what
  to *produce*, never what to *decide next*.

---

## 1. `RETURN:` block (REQ-HARN-009)

The block is YAML-shaped, indented under the literal line `RETURN:`, with
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
  failures: []                                               # see §2; empty when COMPLETE
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
(`docs/spec/harness-chunk-verifier.md` §Verdict Rule) — required on a verifier
return, and a warning when present on any other return. `RED_VERDICT:` is the
red-team analogue (§6a): required on a red return, a `FOREIGN_TOKEN` warning
on any other.

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
| `RED_VERDICT` | enum `BROKEN \| HELD`, **red team only**, last non-blank line of the return text (after the block) | verify-stage gate (§6a; `docs/spec/adversarial-verify.md`); `FOREIGN_TOKEN` warning elsewhere, never branched on |

Status semantics: `COMPLETE` — deliverable contract met; `PARTIAL` — some
tasks done, none blocked, budget not exhausted (e.g. the leaf hit its
deliverable boundary early); `BLOCKED` — stuck detection fired, checkpoint
composed; `BUDGET_EXHAUSTED` — per `harness-loop-control.md` §Budget
Exhaustion, `budget_consumed` mandatory.

`COMPLETE` refers to the dispatch's **deliverable contract** (the assigned
chunk or stage), not the whole plan — a per-chunk implement dispatch that
legitimately leaves later chunks untouched returns `COMPLETE`.

**Why a block, not a summary paragraph**: the orchestrator's downstream steps
(plan marks, traceability fills, packet composition, checkpoint, scope check)
each need one field; a paragraph forces the orchestrator to paraphrase, which
REQ-HARN-012 forbids.

### Budget grammar and default budgets (REQ-HARN-004, REQ-HARN-005)

Every dispatch template — pipeline, fix re-dispatch, fan-out leaf, review,
chunk verifier — carries `Budget: {budget}`. The orchestrator fills it on every
dispatch; an empty slot is a template violation its pre-dispatch self-check
catches (`../SKILL.md` §KICKOFF), not lint. `budget` (dispatched) and
`budget_consumed` (returned, key table above) are paired here so both halves
are documented in one place.

Budget grammar — a comma-separated list of `<count> <unit>` or `≤ <count>
<unit>` terms in **observable units** the subagent can count about itself:

```
Budget: 1 chunk, ≤ 25 tool calls, ≤ 3 test runs          # implement, per chunk
Budget: ≤ 15 tool calls, read-only                          # review
Budget: 1 chunk, ≤ 15 tool calls, ≤ 2 test runs, read-only  # chunk verifier
Budget: ~70 tool calls, no prototypes                       # pipeline (specs stage)
```

Recognized units: `chunk(s)`, `task(s)`, `tool call(s)`, `test run(s)`,
`approach(es)`; `read-only` and `no prototypes` are qualifiers. Wall-clock
units are forbidden (the existing lint `FORBIDDEN` rows already enforce this).
If a wall-clock term slips through anyway, the leaf reports `budget_consumed`
in the units it *can* count and notes the mismatch in `open_questions`.

Default budget per dispatch type (the orchestrator may tighten or widen a
default from the kickoff's budget; it never leaves the slot empty):

| Dispatch type | Template | Default `Budget:` |
|---|---|---|
| pipeline stage (non-implement) | `dispatch-templates.md` §PIPELINE | `~70 tool calls, no prototypes` |
| implement, per chunk (sequential) | `dispatch-templates.md` §PIPELINE | `1 chunk, ≤ 25 tool calls, ≤ 3 test runs` |
| fix re-dispatch (any stage) | §PIPELINE with `{on_fix_only}` | the remaining allowance or a fresh per-chunk allowance, sized from the previous `budget_consumed` |
| fan-out leaf | `fan-out.md` §2 | `1 chunk, ≤ 25 tool calls, ≤ 3 test runs` |
| review | `dispatch-templates.md` §REVIEW | `≤ 15 tool calls, read-only` |
| chunk verifier | `dispatch-templates.md` §CHUNK VERIFIER | `1 chunk, ≤ 15 tool calls, ≤ 2 test runs, read-only` |
| red team (verify stage, opt-in) | `dispatch-templates.md` §RED TEAM | `≤ 25 tool calls, ≤ 3 test runs, read-only` |

`budget_consumed` is reported in **the same units** the `Budget:` slot was
stated in, e.g. `budget_consumed: {tool_calls: 25, test_runs: 3, chunks: 0}`.
The orchestrator uses it to size the next repair packet's `budget` and surfaces
`RETURN.status` + `budget_consumed` against the dispatched `Budget:` at the gate
(REQ-ORCH-034). `status: BUDGET_EXHAUSTED` without `budget_consumed` is
malformed (next section). The leaf-side exhaustion procedure (stop new work,
consistent tree, checkpoint if mid-task) is `implement/SKILL.md` §Step 3.

**Recorded v1 limitation**: `budget_consumed` is **self-reported**. The harness
exposes no tool-call counter to the orchestrator, so adherence is as
trustworthy as the leaf. This is not fixed in this cycle (telemetry is
deferred, catalogue D11).

**Pre-pipeline self-checks (from `../SKILL.md` §KICKOFF).** Before the first pipeline dispatch, the kickoff carries `date:` and `research_id:` (fix it first if not). Before **every** dispatch (pipeline, fix, fan-out leaf, review, chunk verifier, red) the prompt's `Budget:` slot holds a non-empty value in observable units (the grammar above) — never dispatch around an empty one.

### Parsing and malformed returns

The orchestrator parses the block; it **never infers success from prose**. A
return is **malformed** when:

- the `RETURN:` line is absent;
- `status:` is not the first key or not one of the four values;
- `status: BUDGET_EXHAUSTED` lacks `budget_consumed`;
- `budget_consumed` is present but is **not a map of unit -> integer**
  (`RETURN: MALFORMED (budget_consumed shape)`, REQ-HARN-HARNESSP3-003) —
  checked **structurally**: the value must parse as a mapping whose every value
  is an integer. Unit *names* are not constrained (`tool_calls`, `test_runs` and
  any stage-specific unit are all legal), so the check never pauses a gate over
  vocabulary drift, only over shape (Q-IMPL-HARNESSP3-004);
- a `failures[]` entry lacks `test` or `message`;
- any value spans multiple lines (traceback smuggling);
- `status: COMPLETE` with non-empty `failures` (contradictory).

A malformed return is a **gate pause** (REQ-ORCH-018 analogue): the gate shows
the raw tail of the return and the pause text below, and waits for the
operator. It is never treated as `COMPLETE`.

```
RETURN: MALFORMED (<reason>)
  <raw tail of the return>
  re-dispatch | accept manually | stop
```

Warnings (not pauses), shown on the gate line:

```
RETURN: KEYS MISSING (<names>)     # the named keys read as empty ([] / no value)
RETURN: MULTIPLE                   # block returned more than once (e.g. once per chunk); the LAST block is taken
RETURN drift: <k> path(s) claimed, not observed: <paths>   # RETURN.files_written − observed writes
```

`CHUNK_VERDICT` present on a non-verifier return is likewise a warning, and the
key is ignored.

**Return-drift warning (REQ-HARN-HARNESSP4-002).** The fourth parser warning,
`RETURN drift: <k> path(s) claimed, not observed: <paths>`, is the set
difference `RETURN.files_written − observed_writes` (observed writes =
`porcelain_delta ∪ committed_delta ∪ content_delta`, `write-scope.md` §3):
paths the leaf *claims* to have written that no delta observed — never written,
or written and reverted. It is a **warning, never a pause**, rendered on the
gate line beside `KEYS MISSING` / `MULTIPLE` / `FOREIGN_TOKEN`, sorted,
repo-relative, comma-separated, and it is **excluded from the `COMMIT:`
comparison**: `RETURN.files_written` is never an operand of the
commit-fidelity check's `expected` set (`write-scope.md` §7a), so a return
defect can never render a false `COMMIT: INCOMPLETE`. The inverse set
(`observed − files_written`, a path written but not claimed) is **not** a
warning — `KEYS MISSING` already covers an omitted list and the write-scope
observation cross-checks every write independently. Telemetry records it as
the `return.warnings` enum member `RETURN_DRIFT` (`telemetry.md` §Record
Schema). This is the sequential analogue of the fan-out clause
`RETURN.commits ⊆ git rev-list <base>..<tip>` (`fan-out.md` §3a.v).

**Why only these two keys pause (REQ-HARN-HARNESSP3-003).** `status` and
`budget_consumed` are the only two keys the **gate arithmetic** consumes —
`budget_consumed` is rendered at every gate against the dispatched `Budget:` and
sizes the next repair packet's `budget` — and `status` already had a malformed
condition, so the condition above closes the pair. The other nine keys stay a
`RETURN: KEYS MISSING` **warning**: `files_written` is independently
cross-checked by the write-scope observation (`write-scope.md` §2), so an
omitted list cannot hide a write; `tasks_completed`, `traceability_fills`,
`chunk_close`, `failures`, `ledger`, `verified_do_not_touch`, `open_questions`
and `commits` feed bookkeeping that degrades to "nothing to do" or that the
orchestrator can observe for itself.

`blocked_writes` is the **deliberate borderline case**, recorded here so the
boundary reads as a decision rather than an omission: an omitted list silently
loses content, which argues for a pause — but only when the leaf **also** failed
to write, and that failure surfaces independently as the deliverable being
absent from the observed write window. A warning therefore loses nothing the
gate would not already show, so `blocked_writes` stays on the warning side.

**Red-team returns (REQ-REDB-HARNESSP2-005).** A red return is additionally
malformed — the same `RETURN: MALFORMED (<reason>)` pause with
`re-dispatch | accept manually | stop` — when any of:

| Condition | Reason string |
|---|---|
| token missing | `RED_VERDICT missing` |
| token not on the last non-blank line | `RED_VERDICT not last` |
| `HELD` with non-empty `failures[]` | `RED_VERDICT/failures disagree` |
| `BROKEN` with empty `failures[]` | `RED_VERDICT/failures disagree` |
| a `BROKEN` line whose `reproduce:` is `n/a`, empty, or not a backticked command | `BROKEN without reproduce` |
| `Rn` count of `BROKEN` ≠ `len(failures)` | `Rn/failures count mismatch` |

The token is red-only: `RED_VERDICT:` in any other dispatch's return
(pipeline, fix, fan-out leaf, verifier, review) is surfaced as the warning
`FOREIGN_TOKEN` on the gate line (`telemetry.md` `return.warnings`) and is
**never branched on**. Parser: §6a.

---

## 2. Failures are one-line (REQ-HARN-010)

```yaml
failures:
  - {test: tests/test_recon.py::test_gap_report, kind: assertion,
     message: "AssertionError: expected 3 gaps, got 2", location: src/recon/engine.py:142}
```

- `test`: test id or the gate command that failed (`ruff check .`).
- `kind` ∈ {`assertion`, `error`, `lint`, `type`, `build`}.
- `message`: the last frame / one line, ANSI-stripped, ≤ 200 chars (the leaf
  truncates with `…` and never wraps to a second line).
- `location`: `path:line` where known, else omitted.

Tracebacks and raw tool output are never carried in a return or a packet; they
are regenerable by re-running `test`.

---

## 3. Repair packet (REQ-HARN-011)

> **Slot boundary (Q-IMPL-082).** The `{repair_packet}` slot holds the packet **body from `stage:` on**; the `Repair packet (fixed shape …):` header line is emitted once by the PIPELINE template's `{on_fix_only}` block, never inside the slot.


A fix re-dispatch — pipeline loop-back-to-fix, or a fan-out / per-chunk redo
after `CHUNK_VERDICT: FAIL` or a merge abort — carries a `{repair_packet}` slot
in the pipeline template's `{on_fix_only}` block (`dispatch-templates.md`
§PIPELINE), replacing the former free-form `{review_findings}` slot. Fixed
shape:

```yaml
Repair packet (fixed shape — act on it; do not re-derive the history):
  stage: implement
  reason: REVIEW                                     # REVIEW | VERIFIER_FAIL | PARTIAL_CONTINUE | MERGE_CONFLICT | RED_BREAK
  iteration: 2 of 3                                  # harness-loop-control.md §Fix-Loop Cap (REVIEW, RED_BREAK) / per-chunk redo counter (others)
  budget: "1 chunk, ≤ 25 tool calls, ≤ 3 test runs"
  write_scope: [src/recon/**, tests/test_recon.py, docs/spec/recon.md]   # harness-write-scope.md
  target: {artifact_paths: [docs/plan.md], chunk: "Chunk 2: Reconciliation"}   # chunk: all — whole-plan fix (§5)
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
  spec text — the leaf reads the lines itself. A finding `ref` that does not
  resolve to a heading is carried as the path with `section: (unresolved)` and
  no line range; the orchestrator notes it at the gate rather than quoting text
  to compensate.
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
  `conflict_paths` and `base` (§10).
- **Out-of-fix-scope findings go to the next dispatch, not into the packet**
  (REQ-HARN-HARNESSP3-005). A review finding raised against an artifact the fix
  leaf is **not** scoped to touch (`write_scope` above) is carried into the
  **next pipeline dispatch's** `{deliverable_contract}` slot
  (`dispatch-templates.md` §PIPELINE), verbatim as one line, and is **not** put
  in `findings`. The packet stays what the fix leaf can act on. No schema change
  and no `carry_to_next_dispatch:` field — the destination slot already exists,
  and a field was considered and declined as not worth the cost.
- **`RED_BREAK`** (REQ-REDB-HARNESSP2-009; defined in
  `docs/spec/adversarial-verify.md` §Fix-Loop Interaction) — a red-team
  `BROKEN` finding the operator routed to `fix` at the verify-stage gate
  produces an **implement**-stage packet:

  | Packet field | Value |
  |---|---|
  | `reason` | `RED_BREAK` |
  | `failures` | red's `RETURN.failures` verbatim (one per `BROKEN` line routed) |
  | `findings` | the routed `Rn` lines verbatim (`id` = `Rn`, `text` = the line; no `affects`) |
  | `target.chunk` | resolved by §5 — **step 1'** narrows on the routed `Rn`'s `failures[].location` first; otherwise the **spec** taken from the `## Red team — <spec.md>` heading the `Rn` line sits under (red lines carry no `affects`); a spec traced by no chunk → `all` |
  | `write_scope`, `budget` | that chunk's default row (`write-scope.md` §2; §Budget grammar) |
  | `iteration` | the **verify** stage's fix-loop counter — one red round = at most one iteration (`loop-control.md` §2a "Red round") |

---

## 4. Field sources (REQ-HARN-012)

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

---

## 5. Finding → chunk mapping (implement-stage loop-back-to-fix)

The implement-stage review runs once after all chunks, so its findings must be
routed back to chunks before a fix dispatch can carry a chunk-sized `target`,
`write_scope` and `budget`. The orchestrator groups the Critical/Material
findings mechanically — no judgement, no paraphrase:

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

**Red-team findings** (`reason: RED_BREAK`) enter the mapping at **step 1'**,
inserted ahead of the heading-spec step (REQ-REDB-HARNESSP3-001):

```
1'. If the routed Rn's failures[].location names a file or chunk, resolve it to
    the chunk whose tasks' implementation modules include that file.
    Otherwise fall back to the spec named in the
    "## Red team — <spec.md>" heading and continue at step 2 as today.
```

`location` is a `path:line` or a chunk name (Q-IMPL-HARNESSP3-003): a
`location` that already names a chunk is used verbatim; a path is matched
against the implementation modules named by each `### Chunk N:` task in the
active plan, and resolves only when **exactly one** chunk owns it — a path owned
by more than one chunk, or by none, falls through rather than guessing.

On fall-through, step 2 is unchanged: the spec is the `## Red team — <spec.md>`
heading the routed `Rn` line sits under (red lines carry no `affects`, so step 1
is skipped); a spec traced by no chunk → `all` per step 4
(`docs/spec/harness-return-contract.md` Q-IMPL-HARNESSP2-003). Step 1' only
**narrows** the input to an otherwise unchanged mapping — the whole-plan
fallback stays the rule, and nothing that resolved to a chunk before can be
excluded by it.

One review round is one fix iteration for the stage (`iteration N of MAX`)
regardless of how many chunk-grouped dispatches it fans into. Every fix
dispatch is followed by the scope check, one verifier dispatch per chunk it
touched (from `files_written`), and that chunk's per-chunk gate
(`docs/spec/harness-chunk-verifier.md` §Sequencing — Sequential Mode) before
the re-review.

---

## 6. `VERDICT:` token and branching (REQ-HARN-013)

`review` emits, on a line of its own, anywhere in its report
(conventionally next to the `**Verdict:**` line — position is not part of the
contract), a single token line:

```
VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT
```

**Parser.** Match `^VERDICT:` **at line start** — so a `CHUNK_VERDICT:` or
`RED_VERDICT:` line never matches — and when the token occurs more than once
the **last occurrence wins**. The lint consumer row for this token uses
`(?<!CHUNK_)(?<!RED_)VERDICT:` (`tools/skill-lint.py` `REQUIRED` d2), so
a red token never satisfies the review row. The prose verdict and the token must agree (`Approve` ↔ `APPROVE`,
`Approve with fixes` ↔ `APPROVE_WITH_FIXES`, `Reject` ↔ `REJECT`); a report
whose token and prose disagree (e.g. `APPROVE` beside Critical findings) is
malformed. The orchestrator never classifies a verdict by parsing prose; when
the token is missing it surfaces the review as malformed rather than guessing.

| Token | Gate offers | Packet |
|---|---|---|
| `APPROVE` | proceed (default) │ stop | none |
| `APPROVE_WITH_FIXES` | proceed │ loop-back-to-fix (fix, then proceed **without re-review** — re-review only on explicit operator opt-in, `loop-control.md` §5a) │ stop | findings carried into the packet |
| `REJECT` with actionable findings | loop-back-to-fix (subject to the fix-loop cap) │ stop | findings carried into the packet |
| `REJECT` with no actionable findings | pause: re-dispatch │ override │ stop (REQ-ORCH-018) | none |
| missing / unrecognized / disagrees with prose | `REVIEW: MALFORMED` pause: re-dispatch review │ accept prose manually │ stop | none |

### 6a. `RED_VERDICT:` token (verify stage, red team only)

The red team leaf (`dispatch-templates.md` §RED TEAM) ends its return text
with, on its own **last non-blank line**, after the `RETURN:` block:

```
RED_VERDICT: BROKEN | HELD
```

**Parser.** Match `^RED_VERDICT:` **at line start** (the `CHUNK_VERDICT`
precedent); it must be the last non-blank line of the return. `BROKEN` iff
`failures[]` is non-empty; every `BROKEN` `Rn` line needs a backticked
`reproduce:` command or test id. The six malformed conditions and their
reason strings are the red table in §Parsing and malformed returns; a
non-reproducible claim is advisory (`HELD`, suspicion under `observed:`) and
never enters `failures[]`.

| Token | Gate offers |
|---|---|
| `HELD` | the verify-stage exit rule is satisfied on red's side; `proceed` follows the review `VERDICT:` (§6) |
| `BROKEN` | per `BROKEN` `Rn`: `fix (RED_BREAK packet)` (§3) │ `accept (record)` │ `stop`; `proceed` unavailable until every `BROKEN` `Rn` is fixed or accepted |
| missing / not last / disagrees with `failures[]` | `RETURN: MALFORMED (<reason>)` pause: re-dispatch │ accept manually │ stop |

Signal order at the verify-stage gate: `RETURN.status` → `SCOPE:` →
`RED_VERDICT:` (with its `Rn` lines rendered verbatim) → review `VERDICT:` →
counters; exit rule and the `accept (record)` line shape: `../SKILL.md` §The
gate; the rendered fixture: `loop-control.md` §2a "Red round".

---

## 7. `RETURN.status` branching (per-chunk gate)

The leaf's `status` decides what runs between the return and the gate. For an
implement dispatch (sequential per chunk, or a fan-out leaf) the gate is the
**per-chunk gate** of `docs/spec/harness-chunk-verifier.md` §Sequencing —
Sequential Mode (`proceed │ fix │ stop`; under fan-out the per-leaf gate before
merge). The scope check always runs first (`harness-write-scope.md`).

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

---

## 8. Pruned state on re-dispatch (REQ-HARN-018)

A fix or redo dispatch prompt contains exactly the template's slot set with:

- **one** repair packet — the latest — never prior packets or prior reports;
- the **latest** artifact paths only;
- large content by reference (spec by path + heading + line range; everything
  else by path);
- no conversation history, no fenced review report, no quoted spec text.

**Slot-set check.** Before dispatching, the orchestrator checks the prompt
against the template's slot set; any content outside a slot, or a second
`Repair packet` header, triggers an operator-visible warning at the gate and
the prompt is trimmed before dispatch:

```
DISPATCH: PROMPT EXCEEDS TEMPLATE SLOTS
```

The packet *is* the pruned state; no separate mechanism is needed.

---

## 9. Orchestrator owns routing (REQ-HARN-019)

The following are orchestrator-only and never appear as instructions in a
pipeline, fix, fan-out, verifier or review template: phase-detection relay;
`VERDICT:` classification; `CHUNK_VERDICT:`, `RED_VERDICT:` and `SCOPE:`
interpretation;
fix / redo / replan cap arithmetic; packet composition; the decision to merge,
re-dispatch, replan or stop. Templates tell a subagent what to *produce*
(block, token, findings) — never what to *decide next*. Grep guard: no
template contains "decide the next stage", "classify the verdict" or
"judge scope" as an instruction to the subagent.

---

## 10. Edge cases

- **Leaf returns the block twice** (e.g. once per chunk): take the last block
  and flag `RETURN: MULTIPLE` as a warning, not a pause.
- **`status: COMPLETE` with non-empty `failures`**: contradictory → malformed.
- **Review with `APPROVE` token but Critical findings listed**: token and
  prose disagree → malformed (the reviewer's own definitions forbid this).
- **Finding `ref` that does not resolve to a heading**: `spec_excerpt` carries
  the path with `section: (unresolved)` and no line range; note it at the gate
  rather than quoting text to compensate.
- **Redo packet with no review findings** (verifier FAIL before any review):
  `reason: VERIFIER_FAIL`, `findings: []`, `failures` from the verifier's
  `RETURN.failures`; `stage: implement`, `iteration` from the per-chunk redo
  counter.
- **Merge-abort re-derivation packet** (`fan-out.md` §3c, REQ-ORCH-026 /
  Q-IMPL-1): `reason: MERGE_CONFLICT`, `failures: []`, `findings: []`,
  `conflict_paths: [<paths git merge reported>]`, `base: <sha>` — the fresh
  integration-branch commit the leaf must branch from and re-derive its chunk
  on — plus the usual `target`, `write_scope`, `budget`, `iteration` (per-chunk
  redo counter) and `ledger_summary` / `verified_do_not_touch` lifted from the
  leaf's last `RETURN`. No diff or conflict-marker text is carried.
- **Blocked write for a path outside scope**: `blocked_writes` is parsed here
  but the refusal is `harness-write-scope.md` §Blocked-Write Fallback.
