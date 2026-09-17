---
id: RS-008
topic: harness-hardening
status: Complete
date: 2026-09-17
last_updated: 2026-09-17
questions:
  - "Q1 — Where does loop-control state live? (fix-iteration count, replan re-entry count, attempt ledger) without violating REQ-ORCH-014"
  - "Q2 — Fresh verifier at chunk close vs. existing layers: new layer or re-homing of sdd-implement Step 4; who runs it per fan-out worktree"
  - "Q3 — Repair packet + ledger shape: exact fields a fix re-dispatch carries and how the orchestrator obtains them from a leaf return"
  - "Q4 — Mechanical checks: which new contracts tools/sdd-skill-lint.py can check now, SKILL.md size baseline, which sdd-orchestrate sections can move to references/"
  - "Q5 — Write-scope check feasibility: is a git status --porcelain snapshot before/after a dispatch sufficient; finding format and where it surfaces"
budget: "Analysis-only spike, ~60 tool calls (~12 per question); no prototypes beyond reading and running tools/sdd-skill-lint.py; no live subagent dispatch. Consumed: ~30 tool calls."
research_refs: [RS-002, RS-004, RS-005, RS-006]
# Note: `last_updated` and `research_refs` are extensions beyond the sdd-research
# findings template (added for staleness detection and prior-research linkage).
---

# Research: Harness Hardening (loop control, decoupled verification, boundaries)

## Questions

This spike de-risks the twelve in-scope ideas of the harness-hardening cycle
(catalogue: `docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md`,
ideas A1–A4, B5–B7, C8–C10, E13, G16). Five questions were open after DISCUSS:

1. **Q1** — Where does loop-control state (fix-iteration count, replan re-entry
   count, attempt ledger) live, given REQ-ORCH-014 forbids a loop-position marker?
2. **Q2** — How does a fresh chunk-close verifier compose with `sdd-implement`
   Step 4, the implement-stage `sdd-review`, and fan-out leaves?
3. **Q3** — What exact fields does a fix re-dispatch (repair packet) carry, and how
   does the orchestrator obtain them from a leaf's return today?
4. **Q4** — Which new contracts can `tools/sdd-skill-lint.py` check with its
   current architecture; what is the SKILL.md size baseline; which
   `sdd-orchestrate/SKILL.md` sections are safe to move to `references/`?
5. **Q5** — Is a `git status --porcelain` before/after snapshot sufficient for a
   write-scope check; how are scratch files, legitimate index writes, and the
   returned-content fallback handled?

Repo state examined: SDD marker `3` (`docs/.sdd-version`), commit `741cb33`.
`tools/sdd-skill-lint.py` runs clean today (`OK: 13 file(s) clean`, exit 0).

## Findings

### Q1 — Where does loop-control state live?

**Answer**: Split the three counters by what they protect against; none needs a
new artifact. (a) The **review fix-iteration count is per-session only**; (b) the
**replan re-entry count is derived, not stored** — it is the number of
`docs/plan-history/*-replan-*.md` archives dated on/after the kickoff's `date:`;
(c) the **attempt ledger is per-session (in the leaf's context) and its only
durable trace is the circuit-break checkpoint**, which lands in an existing slot:
`sdd-replan`'s already-defined "mark blocked tasks — note why they're blocked and
what unblocks them" note under the task in `docs/plan.md`. Under fan-out, leaves
return the checkpoint in their return text and the orchestrator applies it in
`fan-out.md` §3e bookkeeping (leaves are barred from writing the plan).

**Evidence**:

- REQ-ORCH-014 (`docs/requirements/functional/orchestration.md`) forbids a
  "dedicated loop-position marker file" and an "authoritative loop log" in
  `kickoff.md`; REQ-ORCH-004 makes `kickoff.md` the only new artifact type;
  REQ-ORCH-013 forbids review verdicts on disk but explicitly allows "decisions
  land in the artifacts themselves (commits, Q-IMPL entries, replan triggers)".
  RS-005 Q3 established that loop *position* is fully encoded by artifact
  existence/status/staleness; a per-stage fix count is not position — it does not
  change which stage phase detection resolves to.
- Every loop-back-to-fix is already an explicit operator decision at the gate
  (REQ-ORCH-011, `sdd-orchestrate/SKILL.md` §The gate). A new session is therefore
  itself a human intervention; a cap that resets per session still stops
  unattended ping-pong inside one session, which is the ADK `ROUTE_TO_HUMAN`
  hazard the cap exists for. Persisting the count would only guard against an
  operator deliberately restarting sessions to evade it — not a threat model
  worth a new artifact.
- `sdd-replan/SKILL.md` Step 4 archives every **significant** replan to
  `docs/plan-history/{date}-replan-{reason}.md` (per-milestone:
  `{date}-m{N}-replan-{reason}.md`) with a `## Changelog` carrying `Trigger:`.
  Minor replans edit in place and leave no archive — acceptable: they are task
  reorders, not the approach-oscillation the cap targets. **Requirement to pin
  (and lint)**: the derivation depends on the `-replan-` filename segment being
  the *only* way to tell a replan archive apart from an `sdd-plan` rewrite
  archive (`{date}-{reason}.md`) or a milestone-complete archive — today this is
  an implicit convention in `sdd-replan` Step 4, not a stated contract.
  Requirements must pin "every archive written by `sdd-replan` carries
  `-replan-` in its filename; no other skill uses that segment", and
  `tools/sdd-skill-lint.py` should carry a `REQUIRED` row for the pattern in
  `sdd-replan/SKILL.md` (Q4). The RS-008 kickoff
  carries `date: 2026-09-17` in frontmatter, so "archives since kickoff date" is
  computable; kickoffs predating the field fall back to the kickoff's commit date
  (the same fallback `sdd-orchestrate` §KICKOFF already uses for `research_id`).
- `sdd-implement` Step 3 stuck detection ("same test has failed 3+ times with
  different attempted fixes", "2x expected effort") already implies an in-context
  attempt history but never writes it; `sdd-replan` Step 1 item 6 reads "recent
  conversation context — what was the stuck state" — a gap under orchestrate,
  where the leaf's conversation is gone when it returns. The plan's blocked-task
  note is the one existing durable slot both skills already agree on.
- Placement alternatives ruled out: **Q-IMPL entries** are spec-deviation
  decisions in the shared spec corpus (REQ-QIMPL-001/002); an attempt log there
  pollutes specs and is not a deviation. **Kickoff frontmatter** is the
  "authoritative loop log" REQ-ORCH-014 forbids. **A telemetry file** is D11,
  deferred. **Plan task notes for the full ledger** would re-create the RS-001
  plan-bloat problem; only the bounded checkpoint goes there.
- REQ-ORCH-014 check: no new file; `docs/plan.md` is an existing execution
  artifact; a blocked note does not alter phase detection (plan still has
  incomplete tasks → implement stage) and the resulting replan surfaces as a gate
  event per REQ-ORCH-017. Bumping the plan's `last_updated` cannot make the plan
  stale (staleness compares the plan against *upstream* dates only).

**Resume semantics** (to be written into requirements):

| State | Lifetime | Resume in a new session |
|---|---|---|
| Fix-iteration count per stage (cap default 3) | session | restarts at 0; prior loops visible in git history (one commit per fix re-dispatch) and in the stage artifact's Open Questions |
| Replan re-entry count per cycle (cap default 3) | derived | recomputed from `docs/plan-history/*-replan-*.md` dated ≥ kickoff `date:` |
| Attempt ledger per task | session (leaf context) | not resumed; the checkpoint under the blocked task is what a fresh session reads |
| Circuit-break checkpoint | durable | `docs/plan.md` blocked-task note (≤ ~15 lines: failing test names + one-line reasons, last hypothesis, ledger summary, open question); full tracebacks are regenerated by re-running tests, never stored. Composed by the orchestrator from the leaf's `RETURN:` block (Q3 Schema 1) — there is **no dedicated checkpoint field**: failing tests + reasons ← `failures[].test` / `failures[].message`; last hypothesis ← the last `ledger[].hypothesis`; ledger summary ← `ledger[].change` + `ledger[].result` one-liners; open question ← `open_questions[]` |

**Confidence**: High for the placement (follows from shipped requirements and
skill text). Medium for the replan-count derivation covering enough cases (minor
replans are invisible by design).

### Q2 — Fresh verifier at chunk close vs. existing layers

**Answer**: It is a **re-homing of the executor of `sdd-implement` Step 4's
mechanical checks, not a new verification layer** — and it must **not** be
`sdd-review`. The four-layer table stays; chunk-close gains a second, independent
executor under orchestrate. Minimal contract: a paths-only "chunk-close verifier"
dispatch that re-runs Check 1 (type alignment), Check 3 (test coverage) and the
quality gates (build/lint/type/tests) for one chunk and returns a machine-parseable
`CHUNK_VERDICT: PASS | FAIL` plus findings in the existing chunk-close report
shape. Check 2 (traceability) stays orchestrator-applied (fan-out §3e already
does this) and is verified after the fill; Check 4 (Q-IMPL audit) stays with the
implementer and the implement-stage `sdd-review` (judgment, not mechanics). Under
fan-out the orchestrator runs one verifier per leaf **in the leaf's worktree,
before merge** — a FAIL means no merge, straight to a repair packet (Q3).

**Evidence**:

- `sdd-review/SKILL.md` §Trigger Classification marks chunk-close boundaries
  **Skip** ("already covered by in-session chunk-close mechanism"); REQ-REV-005
  and REQ-REV-006 place type alignment, traceability, test coverage and Q-IMPL
  audit in chunk-close's territory and forbid review from handling them. A
  `sdd-review`-based chunk verifier would contradict approved requirements; a
  separate verifier persona does not.
- `sdd-implement` Step 4 today has the **implementer** run all four checks and
  "present the chunk close report to the operator", then "resolve all blocking
  findings" itself. Under a non-interactive dispatch there is no operator, so the
  leaf both produces and judges the report — the self-validation bias B5 targets.
  Checks 1 and 3 and the gates are deterministic (grep / import search / command
  exit codes) and need no implementer context — ideal for a fresh executor.
- `fan-out.md` §2 already bars leaves from writing `docs/plan.md` and
  traceability and defers Check 2 to the orchestrator (§3e step 3: "re-run any
  chunk-close Check 2 that a leaf deferred"). The verifier slots in exactly there.
- Granularity: in **sequential** mode the implement stage is one pipeline
  dispatch covering all chunks (`dispatch-templates.md` §PIPELINE), so an
  orchestrator-run verifier between chunks is impossible without changing
  dispatch granularity. Two options: (i) dispatch implement **per chunk** even
  when sequential (also yields the natural budget unit for A2 and the write scope
  for E13), or (ii) run the verifier post-hoc over every chunk the dispatch closed.
  Recommend (i); it is a driver-level change (REQ-ORCH-001 unaffected —
  `sdd-implement` is not modified, it is simply told which chunk to run, as
  fan-out already does).
- Duplication check: the implement-stage `sdd-review` Implementation checklist
  item "chunk close report accurately reflects implementation state" overlaps
  only in that both look at the report; the reviewer judges semantics (silent
  scope reductions, Q-IMPL fidelity), the verifier re-executes mechanics. No
  check runs three times: implementer (self, first pass) → verifier (independent
  re-run of 1/3/gates) → review (semantic).
- The implementer keeps Step 4 unchanged, because standalone `sdd-implement`
  (no orchestrator) has no one to dispatch a verifier; the verifier is an
  orchestrate-only second pass.

**Minimal verifier dispatch contract** (paths only, mirrors the review template):
repo root or worktree path; plan path + `Chunk N`; the spec paths the chunk's
tasks trace to; the project's gate commands (from `CLAUDE.md`); budget in
observable units (e.g. "1 chunk, ≤ 15 tool calls, ≤ 2 test runs"); instruction to
run Checks 1 and 3 + gates and return `CHUNK_VERDICT:` + findings; non-interactive
clause. Result surfaces as gate text only (ephemeral, like reviews).

**Confidence**: High on the layering (directly constrained by REQ-REV-005/006 and
the shipped fan-out §3e). Medium on per-chunk dispatch cost — not measurable
without a live dispatch (open question for the orchestrator).

### Q3 — Repair packet + ledger shape

**Answer**: Today the orchestrator receives only free-form text from a leaf —
`dispatch-templates.md` step 4: "the list of files written + a one-paragraph
summary" (fan-out adds "commits made"; blocked writes add labeled content) — and
from the reviewer the `sdd-review` report (Verdict / Strengths / C-M-m findings /
Recommendation). There is **no structured failure or attempt data in any return**,
so a fixed-shape repair packet requires a **structured return block** on the
pipeline template first. Propose two schemas: a `RETURN:` block every pipeline
leaf emits, and a `Repair packet` slot that replaces the free-form
`{review_findings}` on fix re-dispatches. Both use only path references and
one-line strings; no prose reasoning.

**Schema 1 — leaf return block** (appended to the pipeline and fan-out templates'
step 4; keys optional where noted):

```yaml
RETURN:
  status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED   # machine-parseable, own line
  budget_consumed: {tool_calls: 22, test_runs: 3}           # same observable units as the dispatch's Budget: slot
  files_written: [docs/plan.md, src/recon/engine.py, tests/test_recon.py]
  commits: [3f2a1c9]                                         # fan-out / any committing stage
  tasks_completed: ["Chunk 2 task 1", "Chunk 2 task 2"]      # fan-out: orchestrator marks [x]
  traceability_fills:                                        # fan-out: orchestrator applies (§3e)
    - {req: REQ-RECON-003, test: tests/test_recon.py::test_drift, impl: src/recon/engine.py}
  chunk_close: {chunk: 2, check1: pass, check2: deferred, check3: advisory, check4: pass,
                overrides: ["check3: covered by tests/test_e2e.py"]}
  failures:                                                  # empty when status COMPLETE
    - {test: tests/test_recon.py::test_gap_report, kind: assertion,
       message: "AssertionError: expected 3 gaps, got 2", location: src/recon/engine.py:142}
  ledger:                                                    # attempt ledger, newest last
    - {attempt: 1, hypothesis: "gaps keyed by symbol", change: "engine.py: key by contract_id",
       result: "test_drift passes; test_gap_report still fails"}
    - {attempt: 2, hypothesis: "off-by-one in window", change: "engine.py:140 range(n+1)",
       result: "test_gap_report passes; test_drift REGRESSED"}          # <- oscillation signal
  verified_do_not_touch: [tests/test_bootstrap.py, src/recon/bootstrap.py]
  open_questions: ["spec §Gap report silent on overlapping windows — filed Q-IMPL-021 (Tier 2)"]
  blocked_writes: []                                         # [{path, content}] labeled fallback
```

`budget_consumed` is the leaf's self-count in the same observable units the
dispatch's `Budget:` slot was stated in (A2); it is what makes
`status: BUDGET_EXHAUSTED` checkable and lets the orchestrator size the next
repair packet's `budget`. It is self-reported (the harness exposes no tool-call
counter to the orchestrator), so adherence is only as trustworthy as the leaf —
record this as a v1 limitation in requirements.

`kind` ∈ {assertion, error, lint, type, build}. `message` is the **last frame /
one line, ANSI-stripped** — the "clean traceback" of the source literature; the
full trace is regenerable by re-running the named test, so it is never carried.

**Schema 2 — repair packet** (fills a new `{repair_packet}` slot in the PIPELINE
template's `{on_fix_only}` block; fan-out redo dispatches use the same block):

```yaml
Repair packet (fixed shape — act on it; do not re-derive the history):
  stage: implement
  iteration: 2 of 3                          # fix-loop cap (A1); 3 of 3 = last attempt before circuit-break
  budget: "1 chunk, <= 25 tool calls, <= 3 test runs"          # A2, observable units
  write_scope: [src/recon/, tests/test_recon.py, "docs/spec/recon.md ## Implementation Questions"]  # E13
  target: {artifact_paths: [docs/plan.md], chunk: "Chunk 2: Reconciliation"}
  failures:                                  # verbatim from the verifier's / leaf's RETURN.failures
    - {test: tests/test_recon.py::test_gap_report, kind: assertion,
       message: "AssertionError: expected 3 gaps, got 2", location: src/recon/engine.py:142}
  findings:                                  # verbatim finding lines from the sdd-review report, nothing else
    - {id: C1, text: "gap detection ignores overlapping windows", ref: "docs/spec/recon.md §Gap report",
       affects: [REQ-RECON-003], fix: "treat overlap as one gap"}
  spec_excerpt: {path: docs/spec/recon.md, section: "§Gap report", lines: "88-104"}   # <= 20 lines quoted, or a line range
  ledger_summary:                            # from RETURN.ledger; hypotheses already falsified
    - "attempt 1: key by contract_id -> test_gap_report still fails"
    - "attempt 2: range(n+1) -> test_drift regressed (reverted)"
  verified_do_not_touch: [tests/test_bootstrap.py, src/recon/bootstrap.py]
```

**How the orchestrator fills it**: `failures`, `ledger_summary`,
`verified_do_not_touch` come from the previous leaf's `RETURN:` (or the chunk
verifier's return, Q2); `findings` are lifted line-for-line from the review
report's Critical/Material items (REQ-ORCH-012 already restricts a fix dispatch to
"findings + paths"); `spec_excerpt` is a path + section/line range the orchestrator
reads from disk; `iteration`, `budget`, `write_scope` are orchestrator state
(Q1/Q5). Nothing in the packet is reviewer reasoning, so REQ-ORCH-012 and the
isolation discipline hold; the packet is by construction the "pruned state" of
idea C8 (latest paths + latest findings, never accumulated history).

**Fit with the Q-IMPL protocol** (`docs/spec/deviation-protocol.md`): the ledger
is **not** a Q-IMPL entry — Q-IMPL records a spec-deviation *decision*
(Tier/Spec reference/Decision/Rationale), the ledger records *attempts*. They meet
in one place: when an attempt reveals a spec ambiguity or contract change, the leaf
files a Q-IMPL entry as today (Tier 2 continue / Tier 3 stop) and cites it in
`open_questions`; the circuit-break checkpoint (Q1) cites the Q-IMPL id rather than
duplicating it. Q-IMPL numbering rules (global scan; fan-out block) are untouched.

**Oscillation rule for stuck detection** (A3), expressed on the ledger: stuck also
fires when (a) a `result` reports a test failing that a previous attempt's `result`
reported passing (fix re-introduced a fixed failure), or (b) an attempt's `change`
matches an earlier attempt's `change` (repeated rejected patch). Both are string
comparisons over the ledger — no new tooling.

**Confidence**: High that the shape is sufficient and compatible with the shipped
templates (all fields map to existing returns or existing artifacts). Medium on
field naming — `sdd-specs` may rename; the load-bearing decisions are: structured
`RETURN:` block first, own-line status/verdict tokens, one-line failures, no
tracebacks, findings verbatim from the review.

### Q4 — Mechanical checks and SKILL.md sizes

**Answer**: `tools/sdd-skill-lint.py` has five check classes (structure,
forbidden phrases, required contract markers, ordinals, relative Markdown links)
driven by two rule tables (`FORBIDDEN`, `REQUIRED`) plus fixed lists. Every
"marker present" contract is checkable **now** by adding a `REQUIRED` row; three
contracts need **new check methods** (size soft limit, backtick `references/` path
resolution, template-block completeness); two are **not mechanical**. The lint
currently has **no warning tier** — every finding exits 1 — so a *soft* size limit
also requires a severity change. Lint messages today carry a `reason` for
forbidden/required rules only; structure/ordinal/link findings have no remediation
text, so G16 ("every finding says how to fix it") needs a `fix:` field on rules and
in `flag()`.

**Contract table**:

| Contract | Checkable now (rule-table row) | Needs lint change | Not mechanical |
|---|---|---|---|
| Fix-loop cap stated in `sdd-orchestrate/SKILL.md` (e.g. regex `fix[- ]loop cap` / `iteration 3 of 3`) | yes — `REQUIRED` row; presence of the phrase only | — | the cap being *honored* |
| Replan re-entry cap stated | yes — `REQUIRED` row | — | — |
| Budget slot in every dispatch template (`Budget: {budget}`) | yes — one `REQUIRED` row per file: `dispatch-templates.md` (pipeline) and `fan-out.md` (leaf); the **review** template has no budget slot today — decide in requirements whether read-only reviews get one | stronger form: "every fenced block containing `non-interactive pipeline subagent` also contains `Budget:` and `Write scope:`" = new `check_templates()` | — |
| Verdict token in `sdd-review/SKILL.md` (`VERDICT: APPROVE \| APPROVE_WITH_FIXES \| REJECT` on its own line) and its consumer in `sdd-orchestrate/SKILL.md` | yes — two `REQUIRED` rows (producer + consumer), same pattern as the existing `**Depends on**` / fan-out pair | — | — |
| `CHUNK_VERDICT:` / `RETURN: status:` tokens (Q2/Q3) | yes — `REQUIRED` rows once the text exists | — | — |
| Write-scope slot in dispatch templates (`Write scope:`) | yes — `REQUIRED` rows | covered by the stronger `check_templates()` above | — |
| Repair-packet slot `{repair_packet}` in `dispatch-templates.md` `{on_fix_only}` block | yes — `REQUIRED` row (mirrors the existing `{qimpl_block}` row) | — | — |
| `references/` cross-links resolve | partly — `check_links()` already resolves `[text](references/x.md)` outside code fences (6 such links in `sdd-orchestrate/SKILL.md` today: 2× `dispatch-templates.md`, 4× `fan-out.md`) | backtick-quoted paths (e.g. the existing `docs/spec/ws-*.md` mentions, and the proposed `references/v4-workstreams.md` once it exists — it does not yet) are **not** checked → extend `check_links()` with a backtick-path rule for `references/` (and optionally `docs/spec/`) | — |
| SKILL.md soft size limit | — | new `check_size()` + a **warn** severity (findings are a flat list; `run()` exits 1 on any) | choosing the threshold |
| Lint findings carry remediation (G16) | — | add `fix` to `FORBIDDEN`/`REQUIRED` entries and a `fix` argument to `flag()`; give structure/ordinal/link checks fixed remediation strings | — |
| Attempt-ledger / oscillation rule present in `sdd-implement/SKILL.md` | yes — `REQUIRED` row (`oscillation`) | — | the rule firing correctly |
| Checkpoint format present (Q1) | yes — `REQUIRED` row (blocked-note format) | — | — |
| Pruned state on re-dispatch (C8), orchestrator owns routing (C9) | phrase presence only | — | **yes** — behavioral principles; verified by review/dogfooding, not lint |

**SKILL.md size baseline (2026-09-17, `wc -l`)**:

| File | Lines |
|---|---|
| `skills/sdd-orchestrate/SKILL.md` | 607 |
| `skills/sdd-migrate/SKILL.md` | 464 |
| `skills/sdd-requirements/SKILL.md` | 354 |
| `skills/sdd-implement/SKILL.md` | 351 |
| `skills/sdd-plan/SKILL.md` | 276 |
| `skills/sdd-specs/SKILL.md` | 261 |
| `skills/sdd-review/SKILL.md` | 255 |
| `skills/sdd-research/SKILL.md` | 253 |
| `skills/sdd-verify/SKILL.md` | 245 |
| `skills/sdd-replan/SKILL.md` | 187 |
| **Total (10 SKILL.md)** | **3253** (median ≈ 265) |
| `skills/sdd-orchestrate/references/fan-out.md` | 340 |
| `skills/sdd-orchestrate/references/dispatch-templates.md` | 116 |

The project's existing guideline is ~1000 lines (REQ-ORCH-019, relaxed from ~500
and reframed as a soft review in the RS-006 cycle — `docs/verification-rs006-fanout.md:143`).
A soft limit of **400** would flag exactly the two files that have absorbed
gate prose (`sdd-orchestrate` 607, `sdd-migrate` 464) and leave the other eight
untouched; 500 would flag only orchestrate. Recommend 400 as a warn (exit 0)
threshold and keep 1000 as the hard fail — decide in requirements.

**Which `sdd-orchestrate/SKILL.md` sections can move to `references/v4-workstreams.md`**
(section sizes measured with an awk pass over headings):

| Section (lines today) | Size | Move? | Constraint to respect |
|---|---|---|---|
| §Workstream Picker + 3 subsections (147–225) | ~79 | **yes**, leave a ~5-line stub (gate sentence + link) | the lint `REQUIRED` row `research_id` ≥ 3 in SKILL.md counts an occurrence at line 209 inside this section (the others are the phase table l.95 and §KICKOFF l.312). Either keep the `research_id` mention in the stub or re-point that lint row's third occurrence to the new file — otherwise lint FAILS |
| §Phase Detection: "Workstream & version gate (v4)" block (69–89) and "Marker-4 gate for done-vs-new-cycle" (130–146) | ~38 | **yes**, one-line gate stubs each | `docs/.sdd-version` must remain in SKILL.md (`VERSION_GATED_SKILLS` check) — it does, at lines 50 and 352 regardless |
| §Phase Detection: "Upgrade offer (entry, all markers)" (47–67) | ~21 | **no** — it is what a marker-3 operator sees (REQ-WS-030 applies to behind-version repos) | — |
| §Entry Points "Marker-4 scope" paragraph (232–238) | ~7 | yes | — |
| §KICKOFF "Kickoff path — version gate" (300–307) | ~8 | yes, stub | — |
| §Execution Model → §Integration anchor (446–465) and the "Marker-4 anchor" paragraph in §Conflict handling (533–541) | ~29 | **yes**, but point at `references/fan-out.md` §0, which already holds the full contract (today the text exists in three places: SKILL.md, fan-out.md §0, `docs/spec/ws-integration.md`) | — |
| Phase table, §The gate, dispatch contracts, §Isolation Discipline, §Rules, §Orchestrator-Only Work | — | **no** — marker-agnostic core | — |

Net: ~160 lines move → SKILL.md ≈ 445–450 lines, i.e. still above a 400 soft
limit but below 500; a further pass (e.g. §Entry Points detail) is optional.
Requirements-wording check: REQ-WS-029/030 and `docs/spec/ws-orchestration.md`
name the **skill** (`sdd-orchestrate`), never `SKILL.md` as the container; the only
text pinning the picker to `SKILL.md` is **Q-IMPL-016** in `ws-orchestration.md`
("added as marker-4 branches in `skills/sdd-orchestrate/SKILL.md`"). Q-IMPL entries
are append-only, so the move needs a superseding Q-IMPL entry, not an edit.
REQ-ORCH-019 permits `references/` for templates; `fan-out.md` (340 lines, not a
template) is accepted precedent for procedure text living there. Every
"behavior UNCHANGED under marker 3" sentence must survive in the stub so a marker-3
reader is not sent to the reference at all.

**Confidence**: High — all claims come from reading the linter source, running it,
and counting the files.

### Q5 — Write-scope check feasibility

**Answer**: A `git status --porcelain` before/after diff is **necessary but not
sufficient**, because a dispatch's writes may be committed and committed files
vanish from porcelain output. **Who commits is not pinned by shipped contracts**
and differs per dispatch type: the **pipeline sequential** template
(`dispatch-templates.md` §PIPELINE, step 4) has **no commit instruction** — the
leaf returns "files written" and the orchestrator commits at the gate
(`SKILL.md` §DONE "recommend committing"; some dispatches, like this one, commit
anyway); **fan-out leaves** are told to commit on their branch (`fan-out.md`
leaf template success criterion; `SKILL.md` §Subagent git identity); a **fix
re-dispatch** reuses the pipeline template and so inherits its silence.
**Requirement to pin**: state per dispatch type who commits (proposal: pipeline
and fix re-dispatch → orchestrator commits after the gate; fan-out leaf → leaf
commits on its branch), and pin the **snapshot ordering**: the "before"
snapshot (`HEAD` + porcelain) is taken immediately before dispatch and the
"after" snapshot immediately on return, **before** the orchestrator's own
gate commit — so the orchestrator's commit is never inside the observed window
and cannot be flagged as a violation. The sufficient observation is the **union** of
(a) the porcelain delta (`--porcelain=v1 --untracked-files=all`, so untracked
directories are expanded to file paths) and (b) the committed delta
`git diff --name-status <HEAD_before> <HEAD_after>`, plus (c) an ancestry check
`git merge-base --is-ancestor <HEAD_before> <HEAD_after>` to flag history
rewrites. For fan-out worktrees the same three commands run against the worktree
path and its branch (`<base>..<branch>`); the orchestrator owns the worktree so it
may run them. Every path in the union is matched against the dispatch's declared
write scope (glob list); anything outside is a **boundary finding**.

**Evidence**:

- Observed in this worktree: `git status --porcelain=v1 --untracked-files=all` is
  empty after the kickoff commit, while `git diff --name-status HEAD~1 HEAD`
  lists `M docs/handoff/kickoff.md` / `A docs/superpowers/specs/...` — the
  committed writes appear only in (b). `git merge-base --is-ancestor` returns 0
  on linear history. Git 2.55.0.
- Pre-existing untracked noise cancels: the main checkout showed
  `?? .claude/worktrees/` (harness worktree directory) before this dispatch; a
  snapshot *delta* ignores anything present in both snapshots.
- Scratch files: the harness scratchpad (`/private/tmp/claude-501/...`) and
  `$TMPDIR` are outside the repo and invisible to git — correct, they are not
  repo writes. Skill-conventional in-repo scratch (`docs/research/RS-*/notes.md`,
  `prototype/`) falls inside the stage's deliverable directory and is in scope
  by declaration. Paths matched by `.gitignore` are invisible to porcelain unless
  `--ignored=matching` is added — recommend **not** checking ignored paths (they
  are not project content); record the blind spot.
- Legitimate side-writes each stage skill makes must be part of the declared
  scope, or every dispatch flags itself. From the skills: research →
  `docs/research/RS-NNN-*/**`, `docs/research/index.md`; requirements →
  `docs/requirements/**`; specs → `docs/spec/**`, `docs/requirements/traceability.md`
  (Spec column); plan → `docs/plan*.md`, `docs/plan-history/**`; implement →
  the chunk's source/test paths + `docs/plan.md` + `docs/requirements/traceability.md`
  + `docs/spec/*.md`; verify → `docs/verification.md`. Fan-out leaves: chunk-group
  code paths **only** — `fan-out.md` §2 already bars plan/traceability writes, so
  the check mechanically enforces an existing pin.
- Path granularity limit: implement legitimately edits spec files only in their
  `## Implementation Questions` section (Q-IMPL). A path-level check cannot see
  that; a hunk-level check (`git diff -U0` and verify every hunk's enclosing
  heading is `## Implementation Questions`) can. Feasible, but mark the spec-file
  case **advisory** in v1 and hunk-check it later.
- Returned-content fallback (`dispatch-templates.md` "Disk-write reality"): a
  blocked write leaves no git trace from the subagent; the orchestrator's own
  persistence is the observable event, so the orchestrator runs the **same scope
  match on each labeled path before writing it** and refuses/asks on an
  out-of-scope path. `RETURN.blocked_writes` (Q3) gives it the path list. (This
  spike hit the fallback itself: the harness blocked a direct `findings.md` write
  and the artifact had to be staged through the scratchpad — the fallback is
  load-bearing, exactly as `dispatch-templates.md` warns.)
- Other edge cases: deletions/renames appear as `D`/`R` in both listings — treat
  as writes; a file modified and reverted within the dispatch is invisible
  (acceptable); writes outside the repository are the sandbox's job, not this
  check's; the shared stash stack is out of scope (skills never stash).

**Finding format** — gate text only, ephemeral like review verdicts (REQ-ORCH-013
analogue); never persisted:

```
Write-scope check — implement dispatch #2 (Chunk 2, worktree wt-g1 / branch fanout-g1)
  Declared scope : src/recon/**, tests/test_recon.py, docs/spec/recon.md
  Observed writes: uncommitted delta + committed a1b2c3..d4e5f6 (ancestry ok)
    IN   src/recon/engine.py                  M  committed d4e5f6
    IN   tests/test_recon.py                  M  committed d4e5f6
    IN   docs/spec/recon.md                   M  committed d4e5f6  (advisory: verify hunks are under ## Implementation Questions)
    OUT  docs/plan.md                         M  uncommitted      <- boundary finding (leaf pin violated)
  SCOPE: VIOLATION (1 path)        # or SCOPE: CLEAN — own line, machine-parseable
  Options: revert path (git checkout -- docs/plan.md) | accept & widen scope | stop
```

It is presented at the gate **next to** the review verdict; the operator's
decision vocabulary mirrors the existing gate (proceed/fix/stop). A `SCOPE:
VIOLATION` on a fan-out leaf is checked **before** the branch is merged, so a
revert is a `git checkout`/`git reset` on the leaf branch, never on `main`.

**Confidence**: High on the mechanism (three plain git commands, all observed).
Medium on the false-positive rate of the default scope table — unknown until one
real dispatch is dogfooded with the check on (open question for the orchestrator).

## Implications for Design

- **No new artifact type.** All twelve ideas fit inside existing artifacts and
  templates: counters are session-scoped or derived; the checkpoint reuses
  `sdd-replan`'s blocked-task note; the repair packet and return block are
  dispatch-template slots; verdict/scope/status tokens are return-text lines.
  REQ-ORCH-004, -013, -014 remain satisfiable verbatim.
- **Two driver-level design decisions for requirements**: (1) implement dispatch
  granularity becomes **per chunk** under orchestrate even when sequential (enables
  the chunk verifier, per-dispatch budget and write scope); (2) whether the
  read-only **review** dispatch also carries a budget slot (A2 says "every
  dispatch"; the template has none today).
- **Contract pairs to lint**: producer/consumer token pairs (`VERDICT:` in
  sdd-review ↔ branch in sdd-orchestrate; `RETURN: status:` / `CHUNK_VERDICT:` in
  the templates ↔ their consumers) follow the existing `**Depends on**` ↔ fan-out
  pattern and slot into `REQUIRED` unchanged.
- **Lint architecture changes are small and three in number**: `check_size()` +
  a warn severity; backtick `references/` path resolution in `check_links()`; a
  `fix` remediation field. Everything else is rule-table rows.
- **Moving marker-4 prose out of `sdd-orchestrate/SKILL.md`** is safe with two
  guards: keep a `research_id` mention in the picker stub (or re-point the lint
  row), and add a superseding Q-IMPL for Q-IMPL-016 in `ws-orchestration.md`.
- **Approaches ruled out**: `sdd-review` as the chunk verifier (REQ-REV-005/006);
  Q-IMPL entries or kickoff frontmatter as ledger storage; the full ledger in
  `docs/plan.md` (RS-001 plan bloat); porcelain-only write detection.

## Ideas needing no further research

All **12** in-scope ideas are research-complete after this spike:

| Idea | Status | Open item (none blocks requirements) |
|---|---|---|
| A1 max-iteration guard (fix loop, replan re-entry) | Q1 answered | — |
| A2 budgets on every dispatch | slot already present in the pipeline template (`dispatch-templates.md` l.24) and fan-out leaf template (`fan-out.md` l.113); only the **review** template lacks it — add slot + lint row (Q4) | review-dispatch budget: yes/no |
| A3 attempt ledger / oscillation | Q1 + Q3 schema | — |
| A4 checkpoint on circuit-break | Q1 placement | — |
| B5 fresh verifier at chunk close | Q2 contract | per-chunk dispatch cost — dogfood, not research |
| B6 repair packet template | Q3 schema | — |
| B7 machine-parseable verdict tokens | trivial; Q4 lint pair | — |
| C8 pruned state on re-dispatch | the repair packet *is* the pruned state | — |
| C9 orchestrator owns routing | already true in shipped skill text; document as a principle | — |
| C10 SKILL.md size audit / marker-4 prose to `references/` | Q4 tables | — |
| E13 declared write scope | Q5 mechanism + format | false-positive rate — dogfood, not research |
| G16 lint remediation + new checks | Q4 table | threshold choice (400 warn / 1000 fail) |

## Prototype

None — analysis-only spike per the kickoff budget. The only executions were
`python3 tools/sdd-skill-lint.py` (clean, exit 0), `wc -l`, an awk heading-size
pass, and read-only git probes inside this worktree.

## Open Questions

For the orchestrator (both need a live dispatch, which this subagent cannot
perform — RS-006 Q1):

1. **Per-chunk implement dispatch cost** (Q2): dogfood one implement stage with a
   per-chunk dispatch + chunk verifier and note the added wall time / tool calls
   versus a single dispatch. Decides whether the verifier is default-on or opt-in.
2. **Write-scope false positives** (Q5): run one real pipeline dispatch with the
   three-command check on and the default scope table; count noise findings.
   Decides whether the spec-file case stays advisory.

Decisions deferred to requirements (defaults stated): fix-loop and replan caps
default **3**; review dispatches **do** get a budget slot (cheap, consistent);
SKILL.md soft limit **400 warn / 1000 fail**; the implementer keeps Step 4 and the
verifier is an orchestrate-only second pass.

## Assumptions

- The repo stays at marker `3` for this cycle (kickoff); every recommendation
  above is marker-agnostic except the `references/v4-workstreams.md` move, which
  touches only marker-4 prose.
- The harness's return-text channel remains the only leaf-to-orchestrator channel
  (no shared memory) — true today per RS-005/RS-006.

## Summary

Loop-control state needs no new artifact: fix counts are per-session, replan
re-entries are derived from `plan-history` archives since the kickoff date, and
the attempt ledger's only durable trace is a bounded checkpoint in
`sdd-replan`'s existing blocked-task note (REQ-ORCH-014 satisfied). The chunk-close
verifier is a second executor of `sdd-implement` Step 4's mechanical checks — never
`sdd-review` — run per fan-out leaf before merge and, in sequential mode, via
per-chunk implement dispatches. Fix re-dispatches get a structured `RETURN:` block
and a fixed-shape repair packet (one-line failures, verbatim review findings,
spec excerpt by path, ledger summary, do-not-touch list, budget, write scope).
`sdd-skill-lint.py` can check every marker-presence contract now via `REQUIRED`
rows; size soft-limit, backtick reference resolution and remediation text need
three small code changes; SKILL.md sizes range 187–607 lines (orchestrate 607,
migrate 464 exceed a 400 soft limit) and ~160 lines of marker-4 prose can move
to `references/` if the `research_id` lint row and Q-IMPL-016 are handled. The
write-scope check works with porcelain delta + committed delta + ancestry check,
surfaced as gate text. **Recommend: proceed to requirements** — all twelve
in-scope ideas are research-complete; two dogfooding probes are logged for the
orchestrator.
