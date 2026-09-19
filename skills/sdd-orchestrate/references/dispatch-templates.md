# Dispatch Prompt Templates

Copy-ready templates the `sdd-orchestrate` driver fills in at dispatch time.
`{...}` are orchestrator-filled slots. The contract these templates satisfy is
defined in `../SKILL.md` (§Pipeline subagent dispatch, §Review subagent
dispatch). Both were validated by live subagent dispatches in RS-005. The
CHUNK VERIFIER and RED TEAM templates below are read-only **leaves** —
second executors of an existing layer, never `sdd-review`.

---

## PIPELINE subagent template

Front-loads every decision so the non-interactive subagent never needs to ask
the operator a question. The `{on_fix_only}` block is included only when
re-dispatching after a loop-back-to-fix gate.

```
You are a non-interactive pipeline subagent executing ONE stage of an SDD
pipeline. Do NOT ask questions — you have no user to answer them.

Working directory (absolute): {repo_root}
Stage skill to invoke: sdd-{stage}
Assigned IDs (use these verbatim, do not scan/guess): {ids_if_any}
Success criterion: {success_criterion}
Budget: {budget}
Write scope: {write_scope}          # repo-relative globs you may create/modify/delete/rename; nothing else
Deliverable contract (exact files + frontmatter to produce): {deliverable_contract}
{implement_only}Chunk: Chunk {N} — implement THIS chunk's tasks only (one chunk per dispatch, plan order)
{verify_red_only}Red team: enabled            # verify stage only; present iff the operator chose `red team: on` at the verify gate

Inputs you have been given:
  - Kickoff / upstream artifact path(s): {input_paths}
  {on_fix_only}- Repair packet (fixed shape — act on it; do not re-derive the history):
    {repair_packet}
    Act on the packet. Do not re-derive the history, re-read prior reviews, or
    re-open attempts listed in `ledger_summary`. Do not modify
    `verified_do_not_touch` paths.

Precedence: where the sdd-{stage} skill tells you to scan for the next ID,
update an index, or choose an output path, THESE dispatch instructions override
it — use the assigned IDs, the deliverable contract's paths, and (if told) do not
touch index files. The skill's other guidance still applies.

Task:
  1. Invoke the sdd-{stage} skill via the Skill tool and follow it.
  2. Where the skill instructs you to "ask the user", instead use the inputs
     above. If a required decision is genuinely missing, record it under an
     "Open Questions" / "Assumptions" section in the artifact and proceed with
     a stated default — NEVER invent requirements or fabricate operator consent.
  3. Write the stage's SDD artifact(s) to disk per the deliverable contract.
  4. Return: end your return text with the RETURN: block below — every key
     present (empty list / omitted value where not applicable), status: first
     on its own line, values are path references and one-line strings only,
     no tracebacks. If a write is blocked, put the file's full content under
     blocked_writes with the target path labeled so the orchestrator can
     persist it.
     Commit ownership: you are not instructed to commit — the orchestrator
     commits on `proceed` at the stage gate (implement: at the per-chunk
     gate). Leave your writes in the working tree and list them in
     files_written.

RETURN:
  status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED   # own line, first key
  budget_consumed: {tool_calls: N, test_runs: N}            # same units as the dispatched Budget:
  files_written: []                                          # paths
  commits: []                                                # fan-out leaves only; else []
  tasks_completed: []                                        # task labels, e.g. "Chunk 2 task 1"
  traceability_fills: []                                     # [{req, test, impl}]
  chunk_close: {}                                            # {chunk, check1..check4, overrides}
  failures: []                                               # [{test, kind, message, location}] one-line each; empty when COMPLETE
  ledger: []                                                 # [{attempt, hypothesis, change, result}]
  verified_do_not_touch: []                                  # paths
  open_questions: []                                         # one-line each, citing Q-IMPL ids
  blocked_writes: []                                         # [{path, content}] labeled fallback

Do not perform any stage other than sdd-{stage}.
```

### Slot contract (pipeline)
- `{repo_root}` — absolute path; pins cwd so phase detection reads the right tree.
  **Provisioning (remedy (i), `write-scope.md` §3):** when the dispatch runs
  in a worktree, the orchestrator provisions it at the tip the leaf is told to
  reach — `git rev-parse <workstream-branch>` under marker `4`, `main`/HEAD
  under marker `3` — before `snapshot(before)`; the template therefore carries
  **no** "reach commit `<sha>`" instruction and the leaf never catches up.
  A hand-written prompt, entry kickoff or resumed session that still names a
  base commit is remedy (ii): the orchestrator takes `HEAD_before` at that
  named base and renders the `CATCH-UP` line on the gate block. Verifier,
  review and red worktrees are provisioned the same way — a deliberate
  extension beyond REQ-HARN-HARNESSP2-001, so read-only dispatches observe
  the tip rather than a stale tree.
- `{stage}` — one of research, requirements, specs, plan, implement, verify.
- `{ids_if_any}` — IDs the orchestrator assigned centrally (e.g. `RS-006`). Never
  let the subagent pick its own ID.
- `{success_criterion}` — how the stage knows it is done (mandated by REQ-ORCH-007).
- `{budget}` — explicit scope/time bound for the stage (mandated by REQ-ORCH-007).
- `{write_scope}` — comma-separated repo-relative globs the subagent may
  create, modify, delete or rename (REQ-HARN-020), filled by the orchestrator
  from the default scope table in `write-scope.md` §2 (per stage; for
  `stage = implement` the chunk's source/test paths plus the plan, traceability
  and advisory spec paths). An operator widening at the gate applies to the
  redo and later dispatches of the stage in this session only. On return the
  orchestrator observes writes with the three commands (`write-scope.md` §3)
  and surfaces `SCOPE: CLEAN | VIOLATION (N paths)` at the gate — the subagent
  never checks its own scope. An empty slot is a template violation.
- `{deliverable_contract}` — the exact files to write and their frontmatter
  (mandated by REQ-ORCH-007). Also pins output paths, which the Precedence note
  uses to override the skill's default path/index behavior.
- `{input_paths}` — kickoff path (research stage) or prior SDD artifact paths.
- `{implement_only}` / `{N}` — present only for `stage = implement`: the
  `### Chunk N:` header of the ONE chunk this dispatch implements. Sequential
  implement is dispatched **per chunk, in plan order** — one dispatch per
  chunk, each closed at the per-chunk gate (`../SKILL.md` §Per-chunk implement
  dispatch and per-chunk gate) before the next is issued; the chunk verifier
  (§CHUNK VERIFIER below) runs against the same `{N}`. Fan-out leaves receive
  their chunk-group through `fan-out.md` §2 instead. **v2-vocabulary edge
  case**: a plan with no `### Chunk N:` headers has chunk-close inactive
  (`overview.md` §Plan Vocabulary) — omit this line, issue **one** implement
  dispatch for the whole plan, dispatch **no** verifier, and say so at the gate.
- `{verify_red_only}` — present only for `stage = verify` **and** only when the
  operator answered `red team: on` at the verify gate's opt-in (asked before
  this dispatch — `../SKILL.md` §The gate). The literal slot text is
  `Red team: enabled`; `sdd-verify` Step 6 keys on it to write
  `status: pending-red` instead of `pass` (`docs/spec/adversarial-verify.md`
  §`status: pending-red`, REQ-REDB-HARNESSP2-008). Omit the whole line
  otherwise — standalone `sdd-verify` and a red-off cycle must see no slot, so
  their Step 6 output stays byte-identical to v5.
- `{on_fix_only}` / `{repair_packet}` — present only on a fix re-dispatch
  (pipeline loop-back-to-fix, or a fan-out / per-chunk redo after
  `CHUNK_VERDICT: FAIL` or a merge abort). The packet is the **only** fix
  context the leaf receives — a fixed shape composed by the orchestrator from
  the three sources in `return-contract.md` §4 (previous `RETURN`, the review
  report's Critical/Material lines, disk), nothing of the reviewer's
  chain-of-thought, no prior packets, no quoted spec text. The fixed shape:

```yaml
Repair packet (fixed shape — act on it; do not re-derive the history):
  stage: implement
  reason: REVIEW                                     # REVIEW | VERIFIER_FAIL | PARTIAL_CONTINUE | MERGE_CONFLICT
  iteration: 2 of 3                                  # harness-loop-control.md §Fix-Loop Cap (REVIEW) / per-chunk redo counter (others)
  budget: "1 chunk, ≤ 25 tool calls, ≤ 3 test runs"
  write_scope: [src/recon/**, tests/test_recon.py, docs/spec/recon.md]   # harness-write-scope.md
  target: {artifact_paths: [docs/plan.md], chunk: "Chunk 2: Reconciliation"}   # chunk: all — whole-plan fix (return-contract.md §5)
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

  `spec_excerpt` is path + section heading + line range only (rendered
  `docs/spec/<file>.md § <heading> L<from>-<to>`); `MERGE_CONFLICT` packets
  add `conflict_paths` and `base`. Full rules: `return-contract.md` §3.

### Return contract (pipeline)

Step 4 is the leaf half of `return-contract.md` §1: the orchestrator parses the
`RETURN:` block and never infers success from prose. A return without the
block, with `status:` not first, or with any multi-line value is malformed and
pauses at the gate (`RETURN: MALFORMED`). `failures[]` entries are one line
each — `test / kind / message / location`, `message` ANSI-stripped and ≤ 200
chars — never a traceback (`return-contract.md` §2).

**Grep guard (REQ-HARN-019).** No template in this file — pipeline or review —
delegates a routing decision to the subagent: no next-stage decision, no
verdict classification, no scope judgement. Templates say what to *produce*
(the block, the token, findings); the orchestrator alone routes
(`return-contract.md` §9, which lists the guarded phrases — they must have zero
hits in any template).

**Disk-write reality (validated live):** a dispatched subagent's write can be
blocked by harness policy (e.g. writing a report-style file to a non-conventional
path). The `blocked_writes` labeled-content fallback in step 4 is therefore
load-bearing, not decorative — the orchestrator MUST be ready to persist
returned content itself when a subagent reports a blocked write.

---

## REVIEW subagent template (isolation-critical)

Carries only artifact paths + the repo root + "invoke sdd-review" + a
`Budget:` bound. Nothing else.
This is the dispatch-time enforcement of `sdd-review` Step 2's prohibited-inputs
list.

```
You are an external reviewer for an SDD artifact. Review the deliverable below.

Repository root: {repo_root}
Deliverable to review: {deliverable_path}
{upstream_path_line}      # e.g. "Upstream artifact: docs/requirements/index.md"
                          # OMIT this line for the research stage — sdd-review
                          # prohibits kickoff prompts as input; the reviewer
                          # reads the research questions from the deliverable's
                          # own frontmatter.
Budget: {budget}          # default: ≤ 15 tool calls, read-only
Write scope: (empty — read-only)   # you may not create, modify, delete or rename any file
Commit ownership: nobody commits — you write nothing and the orchestrator
commits nothing for a review.

You are non-interactive — do NOT ask questions; you have no operator to answer
them. Where sdd-review Step 2 says to request inputs from the operator, use the
paths above instead and read everything else from the repository.

Invoke the sdd-review skill and follow it to produce a tiered verdict on the
deliverable. Obtain any context you need by reading files from the repository
yourself — none is provided in this prompt by design.

Emit no RETURN: block — a review returns its report plus, on a line of its own,
the verdict token:

VERDICT: APPROVE │ APPROVE_WITH_FIXES │ REJECT
```

### Slot contract (review)
- `{repo_root}` — absolute repository path.
- `{deliverable_path}` — the artifact(s) the pipeline just wrote.
- `{upstream_path_line}` — the upstream SDD artifact for the stage. **Omit
  entirely for the research stage.** For later stages supply requirements (for a
  specs review), specs (for a plan review), etc.
- `{budget}` — explicit bound in observable units, default
  `≤ 15 tool calls, read-only` (REQ-HARN-004; grammar and the per-type default
  table: `return-contract.md` §Budget grammar). An empty slot is a template
  violation the orchestrator's pre-dispatch self-check catches. The budget is a
  bound, not an input — it leaks nothing about the artifact.
- `Write scope: (empty — read-only)` — a literal, not a slot (REQ-HARN-020):
  the reviewer may write nothing; the orchestrator's scope check on a review
  return must observe zero writes and tags any write `OUT`
  (`write-scope.md` §2, §4). Commit ownership row: **nobody commits**
  (`write-scope.md` §7). Like the budget, the literal leaks nothing.

### What the review template MUST NOT contain
(verified absent in the RS-005 dispatch; mirrors `sdd-review` Step 2)
- the orchestrator's conversation history or chain-of-thought
- the pipeline subagent's reasoning / "here's what I was thinking" framing
- a kickoff prompt or internal planning notes
- draft / intermediate versions of the artifact
- the author's out-of-band rationale for design choices

Isolation holds **by construction**: a freshly dispatched subagent has no shared
context window to leak through.

---

## CHUNK VERIFIER subagent template (read-only leaf)

A second, independent executor of the chunk-close layer
(`docs/spec/harness-chunk-verifier.md`): it re-runs Check 1, Check 3 and the
project quality gates for ONE chunk and returns `CHUNK_VERDICT: PASS | FAIL`.
It is a **leaf** (`return-contract.md` §1) — it carries the leaf slots and
nothing else — and it is **never `sdd-review`**: the template invokes no skill,
carries no review checklist and produces no review report. Dispatched by the
orchestrator after every implement dispatch returns `COMPLETE` / `PARTIAL`
(sequential: against the repo root; fan-out: inside the leaf's worktree before
its merge — `fan-out.md` §3a.v). Pasted verbatim from the spec:

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

### Slot contract (chunk verifier)
- `{repo_root_or_worktree_path}` — sequential mode: the repo root; fan-out: the
  leaf's worktree (so the verifier sees the branch's committed state).
- `{plan_path}` + `{N}` — the plan as seen in that working directory and the
  ONE `### Chunk N:` to verify (a leaf that owns several chunks gets one
  verifier dispatch per chunk).
- `{spec_paths}` — resolved by the orchestrator from the chunk's `traces to`
  references; the verifier never searches for specs.
- `{gate_commands}` — the build / lint / type-check / test commands from
  `CLAUDE.md`; failing that, from the project's build files; failing that,
  `tests only`, noted at the gate. The verifier never invents commands.
- `{budget}` — read-only budget, e.g. `1 chunk, ≤ 15 tool calls, ≤ 2 test runs,
  read-only`.

**Nothing else** — no implementer reasoning, no review report, no orchestrator
conversation, no repair history, no prior verifier findings.

### Verdict rule

```
CHUNK_VERDICT: PASS  iff  Check 1 has zero blocking findings
                     and  every gate command exits 0
CHUNK_VERDICT: FAIL  otherwise
```

Check 3 is advisory (`chunk-close-review.md`) and never flips the verdict. Any
implementer override in the implement dispatch's `RETURN.chunk_close.overrides`
is *reported* by the orchestrator next to the verifier's findings at the
per-chunk gate — never applied by the verifier.

### Return contract (chunk verifier)

The literal key block lives **inside the fenced body above** (REQ-HARN-HARNESSP3-002);
what follows is that block worked through, not a second source for it.
The verifier returns the **full** leaf key set (`return-contract.md` §1 — every
key present, empties allowed) plus the one verifier-only key,
`CHUNK_VERDICT`, as the last line of the block (or the line immediately after
it — the orchestrator accepts either placement). `check2` / `check4` read
`deferred` because the verifier does not run them; `files_written` MUST be
`[]` and the scope check on a verifier return must observe zero writes
(`harness-write-scope.md`). A missing or unrecognized `CHUNK_VERDICT:` token
is a malformed return (`return-contract.md` §1); `status: BUDGET_EXHAUSTED`
is consumed as `CHUNK_VERDICT: FAIL` (unverified is not verified).

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

The verifier produces the token; only the orchestrator interprets it
(`return-contract.md` §9). Its findings are ephemeral gate text — nothing it
returns is written to `docs/` by it or on its behalf.

---

## RED TEAM subagent template (read-only leaf, verify stage only)

The adversarial second executor of `sdd-verify` Steps 3–4
(`docs/spec/adversarial-verify.md`): **Blue** is the verify pipeline, **Red**
is a third dispatch kind (`telemetry.md` `dispatch.kind: red`) that picks the
weakest acceptance criteria and constructs inputs or commands that violate
them. It is **opt-in, default off** — asked as `red team: off | on` at the
verify gate *before* the verify pipeline is dispatched (`../SKILL.md` §The
gate) — and is dispatched **once per verify-pipeline return** that came back
`RETURN.status: COMPLETE`, after that return and before the verify-stage
review. It is never dispatched at chunk close or any other stage, and never
after a non-`COMPLETE` blue return or a blue `verification.md` `status: fail`
(the gate then renders `Red team: not run (blue status fail)`). Like the chunk
verifier it is a **leaf** (`return-contract.md` §1) and **never `sdd-review`**:
it invokes no skill, carries no review checklist, and the four-layer table is
unchanged. Pasted verbatim from the spec:

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
       suspicion under `observed:`.
Return, in this order — one `## Red team — <spec.md>` heading per spec examined, one Rn line per
attempted criterion, then this RETURN: block (every key present, empties allowed, `status` first),
then the token on its own last line:

## Red team — <spec.md> acceptance criteria
- R1: <criterion text> — attack: <what was tried> — observed: <one line> — reproduce: `<command or test id>` — BROKEN | HELD
RETURN:
  status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED
  budget_consumed: {tool_calls: N, test_runs: N}
  files_written: []                    # must be empty — read-only dispatch
  commits: []
  tasks_completed: []
  traceability_fills: []
  chunk_close: {}
  failures:                            # exactly one entry per BROKEN line; [] when none
    - {test: "<reproduce command or test id>", kind: assertion|error|lint|type|build, message: "<one line>", location: <path:line>}
  ledger: []
  verified_do_not_touch: []
  open_questions: []
  blocked_writes: []
RED_VERDICT: BROKEN | HELD
```

### Slot contract (red team)

Input contract — checked by the orchestrator's pre-dispatch self-check
(REQ-REDB-HARNESSP2-004):

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

- `{repo_root}` — sequential: the repo root; marker `4`: the workstream branch
  checkout; provisioned at the tip like every other read-only dispatch (§Slot
  contract (pipeline), `{repo_root}`).
- `{spec_paths}` — resolved by the orchestrator from the plan's `traces to`
  references; red reads each spec's `## Acceptance Criteria` itself and never
  searches for specs.
- `{plan_path}` — the plan as seen in that working directory; supplies the
  `### Chunk N:` vocabulary red uses in `failures[].location`.
- `{gate_commands}` — verbatim from `CLAUDE.md` (the chunk verifier's rule for
  fallbacks); red never invents commands.
- `{red_input_override}` — **empty by default**. Only when the operator chose
  `red input: +verification.md` at the opt-in does it render as
  `Blue's report: {verification_path}`. Blue's evidence is withheld otherwise
  — the reviewer-isolation argument: reading what was already checked anchors
  red on the same criteria and the same inputs.
- `Budget:`, `Write scope: (empty — read-only)`, `Commit ownership: you never
  commit` — literals, not slots; the same leaf slot set as the chunk verifier.

**Nothing else** — no finding text, no review reasoning, no blue evidence
outside the override, no orchestrator conversation, no repair history.

**Write-revert rule (REQ-REDB-HARNESSP2-003).** Red is read-only. Any write the
orchestrator's scope check observes on a red return is `OUT` and is reverted
before the gate — the chunk verifier's rule
(`docs/spec/harness-chunk-verifier.md`, `write-scope.md` §4), reused verbatim:
the gate renders `SCOPE: VIOLATION (N paths)` naming the path(s) and the file
is absent at gate time. A reproducible break is a **command line in the
return**, never a committed test.

### Return contract (red team)

The literal key block lives **inside the fenced body above**
(REQ-HARN-HARNESSP3-002); what follows is that block worked through, not a
second source for it. Red's return text, in order — one
`## Red team — <spec.md>` heading per spec examined, one `Rn` line per
attempted criterion (numbering is global per return across headings), then the
full leaf `RETURN:` block, then the token:

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

Rules (REQ-REDB-HARNESSP2-005, -006):

- One `Rn` line per attempted criterion, in the fixed shape; `Rn` numbering is
  per return.
- `failures[]` holds **exactly one entry per `BROKEN` line**: `test` = the
  `reproduce:` command or test id, `kind ∈ {assertion, error, lint, type,
  build}`, `message`, `location` (`return-contract.md` §2).
- `RED_VERDICT: BROKEN | HELD` is the **last line**, on its own; `BROKEN` iff
  `failures[]` is non-empty.
- A claim without a runnable `reproduce:` is **advisory**: reported as `HELD`
  with the suspicion in `observed:`; it never enters `failures[]`, never
  affects the token, never gates the pass commit.
- `files_written` MUST be `[]`; the scope check on a red return must observe
  zero writes (write-revert rule above).

Red produces the token; only the orchestrator interprets it
(`return-contract.md` §6a, §9 — `^RED_VERDICT:` parsing, the malformed table
and the `FOREIGN_TOKEN` warning). Its `Rn` lines are ephemeral gate text —
nothing it returns is written to `docs/` by it; the orchestrator's
`accept (record)` bookkeeping line in `verification.md` §Issues Found → Minor
is the one exception, and the orchestrator writes it (`../SKILL.md` §The gate).
