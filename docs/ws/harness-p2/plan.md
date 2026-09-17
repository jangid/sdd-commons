---
workstream: harness-p2
last_updated: 2026-09-17
status: active
---

# Implementation Plan: Harness Hardening, Part 2 (workstream `harness-p2`)

## Overview

Extend the v5 orchestrated loop with the five deferred harness ideas plus the
queued follow-ups, without a marker bump, a new tracked artifact type under
`docs/`, or a loop-position marker. This is again a **meta-feature**: the
implementation edits skill text (`skills/sdd-orchestrate/SKILL.md` and its
`references/` — one new file `telemetry.md`, edits to `write-scope.md`,
`loop-control.md`, `return-contract.md`, `dispatch-templates.md`;
`skills/sdd-verify/SKILL.md`; `skills/sdd-review/SKILL.md`;
`skills/sdd-replan/SKILL.md`; `skills/sdd-implement/SKILL.md` split into two new
`references/` files; `skills/sdd-orchestrate/USAGE.md`), three Python tools
(`tools/sdd-skill-lint.py` extended; `tools/sdd-telemetry.py` and
`tools/sdd-gc.py` new; `tools/sdd-scope-check-selftest.py` gains F7–F9),
`.gitignore`, `CLAUDE.md`, two append-only `[resolved by …]` notes on
Q-IMPL-083/-084, and the per-workstream traceability file. The six specs
decompose into two independent roots — the **telemetry record** (Chunk 0), on
whose field names red, arbitration and gc all depend, and the **dispatch
snapshot base + `sdd-implement` split** (Chunk 1) — followed by three
independent feature chunks (red, arbitration, gc core), a second gc chunk
(remaining sweeps, `--fix`, cadence hooks), a late chunk that adds the
lint rows only once every marker exists and integrates `SKILL.md` within its
size budget (the v5 Chunk 5 pattern), and a closing chunk for docs, the
evaluation deliverables, traceability closure and the holistic verify that also
records this cycle's own probe measurements. RS-HARNESSP2-001 de-risked every
mechanism (Q1–Q6), so the plan carries **no spike** tasks.

## Conventions

- **Task types**: `[implement]` edits skill prose, templates, tools or
  convention docs; `[verify]` validates behaviour against a spec's Verification
  section — fixture walkthroughs in temp git repos, mutation tests, greps and
  diffs — never a bare "markdown lints".
- **Chunk headers**: `### Chunk N: <name>`; every chunk carries a
  `**Depends on**` line the fan-out boundary derivation parses (`fan-out.md`
  §1). Chunk ids are plain integers — that derivation parses chunk
  **ordinals** and its text must stay exactly as written, so the gc split is
  Chunk 4 / Chunk 5, never `4a` / `4b`. Chunks 0 and 1 are roots. Expected
  waves: wave 1 = Chunk 0 ‖ Chunk 1; wave 2 = Chunk 2 ‖ Chunk 3 ‖ Chunk 4
  (each needs Chunks 0 and 1 — every wave-2 chunk adds `SKILL.md` text that
  must land on the integrated wave-1 tree); wave 3 = Chunk 5; wave 4 =
  Chunk 6; wave 5 = Chunk 7.
- **Traceability**: each task names the spec section(s) and REQ id(s) it
  implements. Test / Implementation cells of
  `docs/ws/harness-p2/traceability.md` are filled at each chunk's close
  (chunk-close Check 2) — this plan does not edit that file; Chunk 7 sweeps the
  remainder and regenerates the shared aggregate.
- **Lint discipline**: `python3 tools/sdd-skill-lint.py` must exit 0 at every
  chunk close (size warnings permitted). New `REQUIRED` / `FORBIDDEN` rows land
  only in Chunk 6, after their markers exist, so no intermediate tree or
  parallel worktree fails. Chunk 0 ships the `allow_files` **mechanics** only.
- **Single definition of the `## Next Steps` section**: the `sdd-verify` Step 6
  template change (a `## Next Steps` section after `## Recommendation`, plus
  the `pending-red` rule) is owned by **Chunk 2 task 4** — the
  `adversarial-verify.md` sdd-verify row is its single definition. Chunk 5 (gc
  `record` routing) and Chunk 7 (evaluation deferral lines) **reference** that
  section and never re-define it.
- **Token ownership**: `TELEMETRY:` and the `OUT .sdd/telemetry.jsonl …` string
  (Chunk 0), `RED_VERDICT:` / `RED_BREAK` (Chunk 2), `REVIEW: CONTRADICTION` /
  `THIRD_OPINION` (Chunk 3), `GC:` (Chunk 5), `CATCH-UP` (Chunk 1) — each is
  pasted from its spec, defined once in the owning reference, and pointed at
  from everywhere else.
- **Size budgets**: `skills/sdd-orchestrate/SKILL.md` ≤ ~470 lines (today 469;
  new gate text is stubs + pointers, detail goes to `references/`); the
  telemetry stub's ≤ 10-line rule counts the **§LOOP block only** (the
  KICKOFF opt-out line and the §The gate pointer are outside that count);
  `skills/sdd-implement/SKILL.md` ≤ 400 after the split (today 525).
- **Tools**: stdlib-only Python 3, `--help`, `--self-test` building temp-dir
  fixtures inside the script (no `tools/tests/`), the linter's finding shape.
- **Repo facts**: marker `4`, workstream branch `harness-p2`, base commit
  `c38922d`. Under marker `4` every execution artifact is rooted at
  `docs/ws/harness-p2/`; `docs/ws/default/**` is never touched.

## Chunks

### Chunk 0: Telemetry — record schema, writer, third observation, reader, guard mechanics
**Goal**: `references/telemetry.md` defines the v1 record and every derived
table; `SKILL.md` carries a ≤ 10-line §LOOP stub (default on, KICKOFF opt-out,
append-after-gate, never read by phase detection); `.sdd/` is gitignored; the
orchestrator's third observation and the leaf-write revert are specified in
`write-scope.md` §3/§5 by citation; `tools/sdd-telemetry.py summarize` works
on a fixture; the linter supports a per-row `allow_files` field (row itself in
Chunk 6); scope self-test F7 passes. Traces to `telemetry.md`.
**Depends on**: None.
**Tasks**:
1. [x] [implement] Create `skills/sdd-orchestrate/references/telemetry.md`
   carrying, pasted from the spec: the record schema table (all groups and
   keys, value domains, gate-signal sources; `v: 1`; `dispatch.seq` 1-based per
   session with zero reads; run identity = `cycle.research_id`), the
   forbidden resume-class key list, the `gate.decision` normalisation table
   (once — the spec's duplicate is not reproduced) incl. `other`, the budget
   object and `Budget:` grammar with `{"unparsed": true}` and
   `self_reported: true`, the example record, the writer sequence and rules
   (one append per dispatch after its gate; append-only except the leaf-write
   revert; never load-bearing; default on / KICKOFF opt-out as session state;
   no leaf ever writes it), the `TELEMETRY: WRITE FAILED | OFF | .gitignore
   updated` line family and its rendering position, the third observation
   (`n_before`/`e_before`, `n_after`/`e_after`) with the `OUT
   .sdd/telemetry.jsonl (+k records, leaf write — reverted)` /
   `(−k records, leaf write — unrecoverable)` / `OUT .sdd/<entry> (leaf write —
   reverted)` strings **defined once here**, the non-interference table of
   phase-detection inputs (incl. `pending-red` and the gc/telemetry tools as
   out-of-loop), the scorer derivation table (nine fields, keys only), and a
   post-cycle pointer to `python3 tools/sdd-telemetry.py summarize`. — traces to
   `telemetry.md` §Record Schema, §Writer, §Third Observation, §Non-Interference
   Proof, §Scorer Derivation (REQ-TELEM-HARNESSP2-001..006, -009,
   REQ-SKILL-HARNESSP2-001); `evaluation.md` §Scorer Fields
   (REQ-EVAL-HARNESSP2-002 derivation half).
2. [x] [implement] In `skills/sdd-orchestrate/SKILL.md`: add the telemetry
   **stub** (≤ 10 lines — the rule counts the §LOOP block only) in §LOOP —
   default on, the KICKOFF opt-out choice
   (session state, not written to `kickoff.md`), "the orchestrator appends one
   record after each gate", "never read by phase detection — `rm -rf .sdd/` is
   behaviour-neutral", the `.gitignore` bootstrap (`git check-ignore -q
   .sdd/telemetry.jsonl` → append `.sdd/` as a bookkeeping commit outside any
   observed window) and a resolving link to `references/telemetry.md`; §KICKOFF
   gains the one-line opt-out prompt; §The gate names the `TELEMETRY:` line
   family position (after the iteration/cap line, before the options) by
   pointer only. Add `.sdd/` to `.gitignore` (beside `.superpowers/`). —
   traces to `telemetry.md` §Placement, §Writer, §Skill and Lint Changes
   (REQ-TELEM-HARNESSP2-004, -008, REQ-HARN-027 amendment,
   REQ-SKILL-HARNESSP2-001).
3. [x] [implement] In `skills/sdd-orchestrate/references/write-scope.md`: §3
   gains the third, telemetry-specific observation (line count + sorted entry
   list of `.sdd/`, taken with `snapshot(before)` / `snapshot(after)`, before
   the orchestrator's own append) and the revert-before-gate rule; §5 gains
   limitation (b)'s `.sdd/` exception — both **cite**
   `references/telemetry.md` for the finding strings instead of restating
   them (`.sdd/` may appear in `write-scope.md` only inside §3 and §5). —
   traces to `telemetry.md` §Third Observation, §Lint Guard (REQ-TELEM-HARNESSP2-005).
4. [x] [implement] In `tools/sdd-scope-check-selftest.py`: add scenario **F7**
   "leaf appends to `.sdd/telemetry.jsonl`" — fixture repo with a gitignored
   `.sdd/telemetry.jsonl` of `n_before` lines, the leaf appends one line →
   `SCOPE: VIOLATION (1 paths)`, the exact `OUT .sdd/telemetry.jsonl (+1
   records, leaf write — reverted)` line, and a post-revert line count equal to
   `n_before`; extend `observe()`/`render()` with the third observation; the
   scenario table and docstring list F7 (the "six scenarios" wording becomes
   the current count — Chunk 1 and Chunk 3 bump it again). — traces to
   `telemetry.md` §Third Observation, §Skill and Lint Changes
   (REQ-TELEM-HARNESSP2-005).
5. [x] [implement] Create `tools/sdd-telemetry.py` (stdlib-only): `summarize
   [--file .sdd/telemetry.jsonl] [--workstream <id>] [--since <ISO>]` printing
   one table per workstream, one row per `dispatch.stage`, with every column of
   §Out-of-Loop Reader (dispatches; tool calls mean/max/budget with an `n/a`
   column; SCOPE violations; MALFORMED; fix iterations; redos per chunk;
   contradiction pauses; red BROKEN/HELD; wall time dispatch and gate mean/max),
   followed by the per-chunk block (RS-008 probe 1 as a query); unknown-`v` and
   non-JSON lines skipped and counted on a trailing `skipped: N …` line;
   `--help`; `--self-test` builds a six-record fixture in a temp dir and asserts
   one row per stage, the per-chunk block and the skipped count. No skill
   invokes it inside the loop. — traces to `telemetry.md` §Out-of-Loop Reader
   (REQ-TELEM-HARNESSP2-009).
6. [x] [implement] In `tools/sdd-skill-lint.py`: add the per-row `allow_files`
   field to `check_forbidden()` — a file whose repo-relative path is in the
   row's `allow_files` is skipped for that row before the line loop; rows
   without the field behave as today; the raw-line (fence-inclusive) scan is
   unchanged. Extend `self_test()` with a synthetic `FORBIDDEN` row carrying
   `allow_files` (injected into a temp copy of the table, never the shipped
   list): the pattern inside a fence in a non-allowlisted fixture fails with
   the row's `fix`; the same text in an allowlisted fixture passes. The shipped
   `\.sdd/` row itself lands in Chunk 6. — traces to `telemetry.md` §Lint Guard
   (REQ-TELEM-HARNESSP2-007 mechanics half, REQ-LINT-HARNESSP2-002 mechanics half);
   `skill-lint-v5.md` Q-IMPL-HARNESSP2-006.
7. [x] [verify] Per `telemetry.md` §Verification — Automated, on fixtures:
   compose a record from the spec's example gate → exactly the top-level keys
   `v, ts_dispatch, ts_return, ts_gate, cycle, dispatch, return, scope,
   verdict, gate, replan_trigger, git`, no resume-class key, `findings.M == 2`,
   no string value longer than 12 chars other than timestamps/ids; parse the
   three `Budget:` lines of `test_budget_line_parses_to_units` against the
   grammar in `references/telemetry.md`; `git check-ignore -q
   .sdd/telemetry.jsonl` exits 0; `grep -rn '\.sdd/' skills/` hits only
   `sdd-orchestrate/SKILL.md`, `references/telemetry.md` and
   `references/write-scope.md` (§3/§5 lines only); grep every skill's §Phase
   Detection block for `.sdd` (zero hits) — the mechanical form of `rm -rf
   .sdd/` neutrality; `python3 tools/sdd-telemetry.py --self-test` exits 0 and
   an unknown-`v` record is counted as skipped; `python3
   tools/sdd-scope-check-selftest.py` passes 7/7; no `docs/ws/*/telemetry*`
   path exists; `python3 tools/sdd-skill-lint.py` and `--self-test` exit 0.
   Fixture walkthroughs owned here: `test_one_record_per_gated_dispatch` (a
   fixture gate sequence of k gated dispatches → exactly k appended lines,
   one per gate, none for an un-gated dispatch);
   `test_write_failure_is_one_gate_line` (make `.sdd/` unwritable → the gate
   renders exactly one `TELEMETRY: WRITE FAILED` line, the gate options are
   unchanged and nothing else is written); the **rendering half** of
   `test_gitignore_bootstrap_once` (a repo without `.sdd/` in `.gitignore` →
   `TELEMETRY: .gitignore updated` rendered once, on the first gate only;
   the bookkeeping commit falls outside any observed window). —
   traces to `telemetry.md` §Verification — Automated
   (REQ-TELEM-HARNESSP2-001..009).
**Entry criteria**: none (root chunk).
**Exit criteria**: `references/telemetry.md` exists and the `SKILL.md` stub
link resolves; `.sdd/` in `.gitignore`; F7 passes; `sdd-telemetry.py`
self-test exits 0; lint exits 0 (size warnings only, file count 18);
traceability Test / Implementation filled for REQ-TELEM-HARNESSP2-001..006,
-008, -009, REQ-SKILL-HARNESSP2-001, REQ-HARN-027 (amendment row: Test =
`git check-ignore` + `git ls-files docs/` unchanged, Implementation =
`.gitignore` + stub; Verified inherits the legacy `pass` per `telemetry.md`
§XSPEC) — the -007 / REQ-LINT-HARNESSP2-002 rows close in Chunk 6.

### Chunk 1: Dispatch snapshot base, blocked-write staging, F9, `sdd-implement` references split
**Goal**: `snapshot(before)` is taken at the commit the leaf is told to reach
(remedy (i) provisioning at the branch tip by default; remedy (ii) named-base
exclusion with the `CATCH-UP` line); the scratchpad staging path is documented
as expected; scope self-test F9 passes; `skills/sdd-implement/SKILL.md` reads
≤ 400 lines with its Step 3 detail and leaf return contract behind resolving
`references/` links, lint still green. Traces to `dispatch-snapshot-base.md`.
**Depends on**: None.
**Tasks**:
1. [x] [implement] In `skills/sdd-orchestrate/references/write-scope.md`: §3
   gains the snapshot-base rule sentence, the provisioning step block (`base :=
   git rev-parse <workstream-branch>` … `HEAD_before := base`) inserted before
   `snapshot(before)`, and the four-part observation (a) porcelain, (b)
   committed delta `git rev-list HEAD_after ^base ^HEAD_prov`, (c) ancestry,
   (d) catch-up count → `CATCH-UP <from>..<base> (N commits, excluded — base
   <sha>)` rendered in the "Observed writes" header line, absent when `N == 0`;
   the merge-catch-up and never-widens notes; the two edge cases (`CATCH-UP
   base <sha> unresolved — window from <HEAD_prov>`, `CATCH-UP not performed
   (base <sha>)`); §5 gains limitation **(c)** with both remedies, listed
   beside (a) and (b) (the (b) `.sdd/` exception is Chunk 0's line, the (a)
   partial-closure note is Chunk 3's — this task adds only the (c) bullet); §6
   gains the blocked-write staging path, points (i)–(iv), with the word
   "expected". — traces to `dispatch-snapshot-base.md` §Snapshot Base Rule,
   §Blocked-Write Staging Path, §Skill Changes, Edge Cases
   (REQ-HARN-HARNESSP2-001, -002, REQ-SKILL-HARNESSP2-004 snapshot half).
2. [x] [implement] In `skills/sdd-orchestrate/SKILL.md` §Pipeline subagent
   dispatch and `references/dispatch-templates.md` §PIPELINE: the sequential
   and fix provisioning step names the branch tip the leaf is told to reach
   (marker `4`: the workstream branch; marker `3`: `main`/HEAD) — one sentence
   plus a pointer to `write-scope.md` §3; drop the PIPELINE template's "reach
   commit" instruction when remedy (i) is in effect (the slot stays for
   hand-written prompts, documented as remedy (ii)); note that verifier,
   review and red worktrees are provisioned the same way (deliberate
   extension). — traces to `dispatch-snapshot-base.md` §Snapshot Base Rule
   (scope of (i)), §Skill Changes (REQ-SKILL-HARNESSP2-004).
3. [x] [implement] In `tools/sdd-scope-check-selftest.py`: add scenario **F9**
   with two assertions — a worktree provisioned one commit behind the named
   base whose leaf fast-forwards → `SCOPE: CLEAN` with the `CATCH-UP
   <from>..<base> (1 commits, excluded — base <sha>)` line; the same plus one
   out-of-scope write → `SCOPE: VIOLATION (1 paths)` naming only that path with
   the `CATCH-UP` line still present; extend `observe()` with the named base
   and the (b)/(d) commands; a third assertion that `N == 0` yields output
   byte-identical to the F1 rendering (no `CATCH-UP` line); update the scenario
   table and docstring count. — traces to `dispatch-snapshot-base.md`
   §Snapshot Base Rule (F9), §Verification (REQ-HARN-HARNESSP2-001).
4. [x] [implement] Split `skills/sdd-implement/SKILL.md` (Q-IMPL-083): move
   Step 3 detail — attempt ledger, oscillation rule, budget exhaustion,
   circuit-break checkpoint composition — to
   `skills/sdd-implement/references/stuck-detection.md`, and the §Leaf Return
   Contract detail (`RETURN:` block, `BUDGET_EXHAUSTED`, `budget_consumed`) to
   `skills/sdd-implement/references/leaf-return.md`; leave stubs that keep the
   literals `oscillation`, `checkpoint`, `RETURN:`, `BUDGET_EXHAUSTED`, the
   status enum line `status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED`,
   a one-paragraph summary each and a resolving `references/<file>` link;
   Steps 1–2, 4–6, the Q-IMPL protocol, chunk close and rules stay; target ≤
   400 lines; standalone behaviour unchanged. Append (append-only) a `[resolved
   by REQ-SKILL-HARNESSP2-007]` note to Q-IMPL-083 in
   `docs/spec/harness-loop-control.md` and to Q-IMPL-084 in
   `docs/spec/skill-lint-v5.md` (an `ADVISORY` spec write under the default
   scope table — expected gate text, not a violation). — traces to
   `dispatch-snapshot-base.md` §Skill Changes — `sdd-implement` references
   split (REQ-SKILL-HARNESSP2-007); `skill-lint-v5.md` §Marker-4 Prose Move
   precedent.
5. [x] [implement] In `tools/sdd-skill-lint.py`: confirm the four `REQUIRED`
   rows guarding `sdd-implement` (`oscillation`, `checkpoint`, `RETURN:`,
   `BUDGET_EXHAUSTED` / status enum) are still satisfied by the stubs; where a
   literal legitimately left the stub, re-point that row's `files` at the new
   reference file and keep its `--self-test` §7 mutation coverage (the mutation
   loop strips the marker from whichever file the row names). No new rows. —
   traces to `dispatch-snapshot-base.md` §Skill Changes guards
   (REQ-SKILL-HARNESSP2-007); `skill-lint-v5.md` Q-IMPL-HARNESSP2-006 (warn-set
   baseline returns to two).
6. [x] [verify] Per `dispatch-snapshot-base.md` §Verification — Automated:
   `python3 tools/sdd-scope-check-selftest.py` passes with F9's assertions; in
   a temp repo replay `test_catch_up_by_merge` (leaf merges the named base →
   merge commit's conflict-free paths not `OUT`) and
   `test_ancestry_still_enforced` (rewrite dropping the named base →
   `HISTORY_REWRITE`) by hand with the §3 commands; grep `write-scope.md` —
   §5 lists (a), (b), (c), §3 contains the snapshot-base rule sentence, §6
   contains points (i)–(iv) and "expected"; walk a staged-then-copied write
   through the §6 text and confirm it is a plain `IN` with `blocked_writes:
   []`; `wc -l skills/sdd-implement/SKILL.md` ≤ 400; each stub's
   `references/` link resolves; `python3 tools/sdd-skill-lint.py` exits 0 with
   size warnings naming exactly `sdd-orchestrate` and `sdd-migrate`;
   `--self-test` exits 0; standalone `sdd-implement` Steps 1–2 and 4–6 diff
   clean against `c38922d`. Fixture walkthrough owned here:
   `test_provision_at_branch_tip` — provision a worktree per the PIPELINE /
   fix provisioning text in `SKILL.md` §Pipeline subagent dispatch and
   `dispatch-templates.md` §PIPELINE, assert the worktree `HEAD` equals the
   workstream-branch tip, that the instantiated prompt names **no** catch-up
   or "reach commit" instruction, and that the rendered write-scope block has
   no `CATCH-UP` line. — traces to `dispatch-snapshot-base.md`
   §Verification — Automated (REQ-HARN-HARNESSP2-001, -002,
   REQ-SKILL-HARNESSP2-004, -007).
**Entry criteria**: none (root chunk).
**Exit criteria**: `write-scope.md` §3/§5/§6 carry the snapshot-base rule,
limitation (c) and the staging path; F9 passes; `sdd-implement/SKILL.md` ≤
400 with two resolving reference files; lint exits 0 with the two-file warn
set; Q-IMPL-083/-084 carry the `[resolved by …]` note; traceability Test /
Implementation filled for REQ-HARN-HARNESSP2-001, -002,
REQ-SKILL-HARNESSP2-007 and the snapshot half of REQ-SKILL-HARNESSP2-004 (the
gc half closes in Chunk 5).

### Chunk 2: Adversarial (Red/Blue) verify — RED TEAM template, `RED_VERDICT:`, `pending-red`, `RED_BREAK`
**Goal**: the verify gate offers `red team: off | on` (default off); with `on`
the orchestrator dispatches one read-only RED TEAM leaf per verify-pipeline
return, parses `^RED_VERDICT:` with the malformed table, blocks `proceed`
until every `BROKEN` `Rn` is fixed (`RED_BREAK` packet) or accepted
(one-line record in §Issues Found → Minor), and `sdd-verify` writes
`status: pending-red` while red is pending — flipped to `pass` by the
orchestrator before its commit. `sdd-verify`'s Step 6 template gains the
`## Next Steps` section (single definition). Traces to `adversarial-verify.md`.
**Depends on**: Chunk 0, Chunk 1.
(Chunk 1 because task 3's `SKILL.md` §The gate additions — the largest new
gate block — must land on the integrated wave-1 tree, after Chunk 1 task 2
has edited `SKILL.md` §Pipeline subagent dispatch; otherwise the two edits
churn on merge and the ≤ ~470 budget is measured on the wrong tree.)
**Tasks**:
1. [x] [implement] In `skills/sdd-orchestrate/references/dispatch-templates.md`:
   add the **RED TEAM** template pasted from the spec (non-interactive clause,
   `Repository root`, `Specs`, `Plan`, `Quality-gate commands`, the empty
   `{red_input_override}` slot, `Budget: ≤ 25 tool calls, ≤ 3 test runs,
   read-only`, `Write scope: (empty — read-only)`, `Commit ownership: you never
   commit`, the reproducibility Rules), its slot contract (the input-contract
   table: `verification.md` withheld by default, operator override `red input:
   +verification.md`; finding text and review reasoning never), the return
   shape (`## Red team — <spec.md>` headings, `Rn` line shape, `failures[]` one
   per `BROKEN`, own-line last `RED_VERDICT: BROKEN | HELD`) and the
   write-revert rule by pointer to the verifier's; the verify PIPELINE template
   gains the `Red team: enabled` slot. — traces to `adversarial-verify.md`
   §Red Dispatch Template, §Return Contract, §`status: pending-red`
   (REQ-REDB-HARNESSP2-003, -004, -005, -006, -008).
2. [x] [implement] In `skills/sdd-orchestrate/references/return-contract.md`:
   `^RED_VERDICT:` parsing (line start; last non-blank line), the six-row
   malformed table (`RED_VERDICT missing`, `not last`, `RED_VERDICT/failures
   disagree` ×2, `BROKEN without reproduce`, `Rn/failures count mismatch`) with
   the standard `re-dispatch | accept manually | stop` pause, the
   `FOREIGN_TOKEN` warning for a red token in any other dispatch, the
   `RED_BREAK` row in §3 Repair Packet (`failures` verbatim, `findings` = the
   routed `Rn` lines, `target.chunk` via §5 with the spec taken from the
   `## Red team — <spec.md>` heading, a spec traced by no chunk → `all`), and
   the `(?<!CHUNK_)(?<!RED_)VERDICT:` note beside §6. — traces to
   `adversarial-verify.md` §Return Contract and `RED_VERDICT:`, §Fix-Loop
   Interaction (REQ-REDB-HARNESSP2-005, -009); `harness-return-contract.md`
   Q-IMPL-HARNESSP2-003.
3. [x] [implement] In `skills/sdd-orchestrate/SKILL.md` §The gate: the opt-in
   line `red team: off | on` (+ `red input: +verification.md`) asked before the
   verify pipeline is dispatched; the verify-stage signal order `RETURN.status`
   → `SCOPE:` → `RED_VERDICT:` → `VERDICT:` → counters (one sentence extending
   the REQ-ORCH-034 pointer list); the exit rule (`proceed` iff `VERDICT ≠
   REJECT` ∧ (red not run ∨ `HELD` ∨ every `BROKEN` fixed/accepted)); per-`BROKEN`
   options `fix (RED_BREAK packet) | accept (record) | stop` with the
   `- Rn accepted at gate <date>: <observed> — reproduce: \`<cmd>\`` append
   under §Issues Found → Minor; `Red team: not run (blue status fail)`; the
   `pending-red → pass` flip immediately before the orchestrator's commit; the
   position table row `pending-red → verify (resume before the red dispatch)`.
   In `references/loop-control.md`: red round = at most one verify-stage fix
   iteration however many chunk dispatches it fans into; one default re-run
   (not an iteration); shared counter with review rounds; the gate fixture
   text from §Verify-Stage Gate pasted verbatim. Keep `SKILL.md` additions to
   stubs + pointers (≤ ~470 lines). — traces to `adversarial-verify.md`
   §Positioning, §Verify-Stage Gate and Exit Rule, §Fix-Loop Interaction,
   §Skill and Lint Changes (REQ-REDB-HARNESSP2-001, -007, -009,
   REQ-SKILL-HARNESSP2-002); `orchestration.md` Q-IMPL-HARNESSP2-008.
4. [x] [implement] In `skills/sdd-verify/SKILL.md`: Step 6 gains the
   `pending-red` table (slot absent → `pass`/`fail` byte-identical to v5; slot
   `Red team: enabled` present → `pending-red`/`fail`) and the lifecycle note
   (flipped by the orchestrator, never by this skill); Phase Detection item 5
   lists `pending-red` as the re-verification state; §Issues Found → Minor is
   documented as the slot for `- Rn accepted at gate …` lines; the Step 6
   template gains a **`## Next Steps`** section after `## Recommendation`,
   documented as the slot for `- gc <rule>: <file:line> — <fix>` lines
   (`drift-sweep.md`) and deferral lines (`evaluation.md`) — **this task is
   the single definition of that section**; §Verification Layers states that
   red is a second executor of this layer; the four-layer table is unchanged.
   — traces to `adversarial-verify.md` §Positioning, §`status: pending-red`,
   §Skill and Lint Changes (sdd-verify row) (REQ-REDB-HARNESSP2-002, -008,
   REQ-SKILL-HARNESSP2-005).
5. [x] [implement] In `skills/sdd-replan/SKILL.md` Phase Detection: a
   `verification.md` with `status: pending-red` is not a verification failure
   — route to `sdd-verify` (one bullet). `skills/sdd-review/SKILL.md` receives
   **no** red change. — traces to `adversarial-verify.md` §`status:
   pending-red` reader table (REQ-REDB-HARNESSP2-008, REQ-SKILL-HARNESSP2-002).
6. [x] [verify] Per `adversarial-verify.md` §Verification — Automated: grep the
   RED TEAM template for `Write scope: (empty — read-only)`, `Commit ownership:
   you never commit`, `sdd-verify` Steps 3–4, no `verification.md` path
   outside the override slot, no finding text; walk the malformed matrix on
   six fixture returns (each row → its reason string; `reproduce: n/a —
   BROKEN` malformed) and a two-`BROKEN` return → BROKEN with two findings;
   render the verify gate from a fixture (`RED_VERDICT: BROKEN` R1 + `VERDICT:
   APPROVE` → no `proceed`; after `accept` exactly one new line under §Issues
   Found → Minor and no other `docs/` change); compose a `RED_BREAK` packet
   from the fixture and confirm chunk resolution from the spec heading and
   `iteration 1 of 3` after the fix; diff `sdd-verify` Step 6 output with the
   slot absent against `c38922d` (byte-identical apart from the new `## Next
   Steps` section); grep `sdd-verify`, `sdd-replan`, `sdd-orchestrate` for
   `pending-red` (each present); `git diff c38922d -- skills/sdd-review/SKILL.md`
   is empty for this chunk; four-layer table in `sdd-verify` unchanged; lint
   exits 0. Fixture walkthroughs owned here: `test_red_write_is_out_and_reverted`
   (a red leaf in a fixture repo writes `tests/test_break.py` → the gate
   renders `SCOPE: VIOLATION (1 paths)` naming that path and the file is
   absent at gate time — reverted by the verifier's write-revert rule the RED
   TEAM template points at); `test_one_red_per_verify_return` (two
   verify-pipeline returns in one stage → exactly two red dispatches, one per
   return, and a fix iteration's re-run counts as its own return). — traces
   to `adversarial-verify.md` §Verification — Automated
   (REQ-REDB-HARNESSP2-001..009).
**Entry criteria**: Chunk 0 complete (`references/telemetry.md` names
`dispatch.kind: red`, `verdict.red_verdict`, `dispatch.reason: RED_BREAK`;
`return.warnings` `FOREIGN_TOKEN`); Chunk 1 complete (`SKILL.md` §Pipeline
subagent dispatch and `dispatch-templates.md` §PIPELINE carry the
provisioning sentence, so the §The gate block and the verify PIPELINE
`Red team: enabled` slot are added to the integrated wave-1 tree).
**Exit criteria**: `dispatch-templates.md` contains `RED_VERDICT: BROKEN |
HELD`; `SKILL.md` or `return-contract.md` contains `RED_VERDICT:`;
`sdd-verify` template has `## Next Steps` after `## Recommendation` and the
`pending-red` rule; lint exits 0; traceability filled for
REQ-REDB-HARNESSP2-001..009, REQ-SKILL-HARNESSP2-002, -005 (lint rows a1/a2
close in Chunk 6).

### Chunk 3: Arbitrated handoff — retained round state, classes (b)/(c), `REVIEW: CONTRADICTION`, third opinion, F8
**Goal**: the orchestrator keeps per-round `(verdict, C/M lines keyed by
file:section + affects)` and per-fix written `(file, section)` pairs in
session state, detects classes (b) and (c) by set comparison (file-level
degradation labelled), pauses at the stage gate with the four-option text,
resolves a single third opinion two-of-three, and `sdd-review`'s Material
line carries `affects`. Section resolution of fix hunks lands in
`write-scope.md` §3 with scope self-test F8. Traces to `arbitrated-handoff.md`.
**Depends on**: Chunk 0, Chunk 1.
**Tasks**:
1. [x] [implement] In `skills/sdd-orchestrate/references/loop-control.md`: the
   retained tuple (`round[N]`, `fix[N]`) beside the compiled findings log in
   §2a with the key-parsing table (file / section `§Name` incl. the leading
   ordinal strip / `affects` regex; unparsable → `(?, ∅)`; fallback `(file,
   *)`); the class table — (b) new C/M on approved ground, (c) verdict
   regression without new ground with conditions (i) and (ii), (a) reversal
   **not detected**, rendered `(persisting)`; trigger = (b) ∨ (c), (b) reported
   when both; `(file-level)` degradation and its over-fire warning; the pause
   fixture text pasted from §`REVIEW: CONTRADICTION` Pause; the options table
   with counter effects (`accept round N+1 (fix)` +1; `accept round N
   (proceed, note)` — note lands in the artifact's Open Questions or a Q-IMPL
   entry, never a review store; `third opinion`; `stop`); stage-gate-only,
   iteration ≥ 2; the third-opinion resolution table (two-of-three, degenerate
   → round N+1, neither → three columns with `fix | proceed | stop`; at most
   one; `dispatch.reason: THIRD_OPINION` telemetry annotation); §6 lists
   `REVIEW: CONTRADICTION` as the fourth pause-family member. — traces to
   `arbitrated-handoff.md` §Retained Per-Round State, §Contradiction Classes,
   §`REVIEW: CONTRADICTION` Pause, §Third Opinion (REQ-ARB-HARNESSP2-001..004,
   -006, -007, REQ-SKILL-HARNESSP2-003).
2. [x] [implement] In `skills/sdd-orchestrate/SKILL.md` §The gate: one pointer
   line for `REVIEW: CONTRADICTION (round N vs round N+1, class b|c)` next to
   the `MALFORMED` family in "Edge cases routed through the gate" — options
   named, detail in `references/loop-control.md` §6. — traces to
   `arbitrated-handoff.md` §Skill and Lint Changes (REQ-ARB-HARNESSP2-006,
   REQ-SKILL-HARNESSP2-003); `orchestration.md` Q-IMPL-HARNESSP2-008.
3. [x] [implement] In `skills/sdd-orchestrate/references/write-scope.md` §3: the
   section-resolution procedure as an extension of the observation commands —
   `git diff -U0 <HEAD_before> <HEAD_after> -- <path>` (committed), `git diff
   -U0 <HEAD_after> -- <path>` (uncommitted), untracked → every heading `(path,
   *)`; hunk header `@@ -a,b +c,d @@` → after-image line `c` → nearest
   `#`-heading ≤ `c` → `§Name` (preamble → `§(preamble)`); non-Markdown →
   `(path, ?)`; result = `(path, §Name)` pairs + hunk ranges for rendering;
   §5's limitation (a) bullet gains "partially closed for Markdown paths by
   §3 section resolution (`arbitrated-handoff.md`)". — traces to
   `arbitrated-handoff.md` §Section Resolution of Fix Hunks
   (REQ-ARB-HARNESSP2-005); `harness-write-scope.md` Q-IMPL-HARNESSP2-002.
4. [x] [implement] In `tools/sdd-scope-check-selftest.py`: add scenario **F8**
   "section resolution" — a fixture `docs/spec/x.md` with `## A`, `## B`,
   `## C`; a diff touching lines 40–58 under `## A` and line 120 under `## C`
   → `{x.md:§A, x.md:§C}` and the hunk strings `L40-58`, `L120`; an untracked
   new file → `(path, *)`; a `.py` path → `(path, ?)`; a `resolve_sections()`
   helper mirroring §3; update the scenario table and docstring count (F1–F9
   after Chunks 0 and 1 merge). — traces to `arbitrated-handoff.md` §Section
   Resolution (F8), §Verification (REQ-ARB-HARNESSP2-005).
5. [x] [implement] In `skills/sdd-review/SKILL.md` §Step 5 report format: the
   Material template line becomes `- M1: [what's wrong] — [file:section] —
   affects [REQ-*] | affects —` and its example is updated; nothing else in
   the report format, verdict definitions or scope boundaries changes;
   `sdd-review` gains no red, telemetry or arbitration text. — traces to
   `arbitrated-handoff.md` §Review Key on Material Lines
   (REQ-ARB-HARNESSP2-008, REQ-SKILL-HARNESSP2-006); `review.md`
   Q-IMPL-HARNESSP2-004.
6. [x] [verify] Per `arbitrated-handoff.md` §Verification — Automated, by hand on
   fixtures: `test_key_parse` (three lines → keys); class (b) fires on the
   untouched §C and not on §A; file-level degradation labels `(file-level)`;
   class (c) fires on `APPROVE_WITH_FIXES → REJECT` with (i)/(ii) and not when
   round 2 is `APPROVE_WITH_FIXES`; identical keys → no token, `(persisting)`
   in the compiled log; the pause fixture in `loop-control.md` matches §Pause
   structurally (token line, two rounds, `fix #N wrote:`, annotation, four
   options); `accept round N (proceed, note)` leaves the counter unchanged and
   `accept round N+1 (fix)` increments once; third opinion matching round 1
   re-renders with `iteration N of MAX` unchanged, matching neither → three
   columns and no second `third opinion`; `python3
   tools/sdd-scope-check-selftest.py` passes with F8; `git diff c38922d --
   skills/sdd-review/SKILL.md` touches only the Material line and its example;
   lint exits 0. — traces to `arbitrated-handoff.md` §Verification — Automated
   (REQ-ARB-HARNESSP2-001..008).
**Entry criteria**: Chunk 0 complete (`verdict.contradiction_class`,
`gate.decision: third-opinion`, `dispatch.reason: THIRD_OPINION` named in
`references/telemetry.md`); Chunk 1 complete (`write-scope.md` §3 carries the
provisioning step and the `HEAD_before`/`HEAD_after` pair section resolution
extends; F9 numbering settled so F8's docstring count is final).
**Exit criteria**: `loop-control.md` contains `REVIEW: CONTRADICTION`;
`sdd-review/SKILL.md` Material line matches `M1:.*affects`; F8 passes; lint
exits 0; traceability filled for REQ-ARB-HARNESSP2-001..008,
REQ-SKILL-HARNESSP2-003, -006 (lint rows b/c close in Chunk 6).

### Chunk 4: Drift sweep, part 1 — `tools/sdd-gc.py` core: CLI, exit codes, finding shape, delegated lint, sweeps 6/8/9/10/13/14
**Goal**: `python3 tools/sdd-gc.py --report` exists with the argparse CLI, exit
codes 0/1/2, the linter's finding shape and summary line, sweeps 1–5 delegated
to `tools/sdd-skill-lint.py` by subprocess (never copied), sweeps 6, 8, 9, 10,
13, 14 implemented (incl. the Q-IMPL counting rule), a complete `--help`, and a
`--self-test` **skeleton** whose fixture asserts **symbolic** counts for exactly
those sweeps. No `--fix` rule is fixable yet (`FIXABLE = []`); sweeps 7/11/12,
the whitelist, the full two-workstream fixture and the cadence hooks are
Chunk 5. Traces to `drift-sweep.md`.
**Depends on**: Chunk 0, Chunk 1.
**Budget**: ≤ 80 tool calls for the dispatched leaf (one new tool file plus
its skeleton self-test; no skill text in this chunk).
**Risk**: the skeleton self-test must derive its `D`/`B` counts from the
fixture it builds, never from the live corpus — a hard-coded live count is
the fifth replan trigger waiting to fire in Chunk 5.
**Tasks**:
1. [x] [implement] Create `tools/sdd-gc.py` (stdlib-only): argparse CLI
   (`--report` default, `--fast`, `--workstream <id>`, `--fix <rule>`,
   `--root <path>`, `--self-test`, `--help` listing flags, the three sweep
   classes with rule ids, the counting rule and the review-territory
   exclusions); exit codes 0/1/2 (2 for not-a-git-repo, missing `docs/`,
   unknown or non-fixable `--fix`, linter missing); `flag(path, line, rule,
   msg, fix, severity)` with `fix` required and the `WARN`/`INFO` prefixes;
   the summary line `OK: N sweep(s) clean, W warning(s), I info` / `FAIL: …`
   always last; sweeps 1–5 obtained by invoking `tools/sdd-skill-lint.py` as a
   subprocess and parsing its findings and summary (size warnings pass
   through; no `FORBIDDEN`/`REQUIRED` table in gc's module); the docstring
   with the Q-IMPL counting rule and RS-HARNESSP2-001 Q4's three reference
   commands; `--fix <rule>` is parsed but module-level `FIXABLE = []`, so
   every `--fix` exits 2 `not a fixable rule` until Chunk 5 fills the list. —
   traces to `drift-sweep.md` §CLI and Exit Codes, §Finding Shape
   and Summary, §Q-IMPL Counting Rule (docstring) (REQ-GC-HARNESSP2-001, -003,
   -004).
2. [x] [implement] gc sweeps 6, 8, 9, 10, 13, 14: `xlink-dead` / `id-missing`
   (the linter's two link regexes over `docs/**/*.md` plus `(see …)` links,
   `research_refs`, `requires:` ids; `RS-`/`REQ-`/`Q-IMPL-` existence; anchor
   miss → warn); the Q-IMPL counting rule (`^### Q-IMPL-[A-Z0-9-]+` under
   `docs/spec/**`; references anywhere under `docs/`, `skills/`, `agents/`,
   `tools/` minus `docs/research/**`, placeholders, fenced blocks and inline
   backticks; legacy and `<WS>`-prefixed ids) → `qimpl-undefined` fail,
   `qimpl-unreferenced` info, `qimpl-broken-ref` warn (missing `**Spec
   reference**` heading after ordinal strip; `[superseded by …]` naming an
   undefined id); `index-research`, `index-requirements`, `spec-approval`
   (scoped fail via the live plan-walk of `docs/ws/<id>/plan.md`, unscoped
   warn); `plan-history-name` (`-replan-` only from `sdd-replan`; date
   prefix). — traces to `drift-sweep.md` §Sweep Table rows 6, 8–10, 13, 14,
   §Q-IMPL Counting Rule (REQ-GC-HARNESSP2-002, -003).
3. [x] [implement] `--self-test` **skeleton**: a `build_fixture()` function
   creating a temporary git-initialised marker-`4` tree with one workstream
   (`alpha`, Approved `a.md` traced by its plan), `D` Q-IMPL definitions / `B`
   references with the four exclusion cases and the `Q-IMPL-999` mutation, one
   broken `**Spec reference**`, one missing index row each, one dead link, one
   `requires: [REQ-ZZ-999]`, one undated `plan-history/replan-foo.md`, and a
   clean copy; assert the symbolic counts for sweeps 6, 8, 9, 10, 13, 14, exit
   codes 0 (clean copy) / 1 (fixture) / 2 (`--fix nonexistent-rule`,
   `--root` at a non-git dir), non-empty `fix` on every finding, summary line
   last, lint size warnings passing through. Chunk 5 **extends** this builder
   (second workstream, aggregate, `trace-empty` rows) rather than rewriting
   it. — traces to `drift-sweep.md` §Self-Test Fixture (REQ-GC-HARNESSP2-001,
   -002 partial, -003 partial).
4. [x] [verify] `python3 tools/sdd-gc.py --self-test` exits 0; `--help` exits 0
   and names every flag, the three sweep classes with rule ids, the counting
   rule and the exclusions; `grep -n 'FORBIDDEN =\|REQUIRED =' tools/sdd-gc.py`
   is empty; `grep -n 'FIXABLE = \[\]' tools/sdd-gc.py` hits once; on this
   repository `--report` exits 0 with no fail finding from the implemented
   sweeps (warn/info counts unpinned) and the `qimpl-*` counts are compared
   with the 2026-09-17 reference values from the docstring (drift from
   `Q-IMPL-HARNESSP2-*` expected and noted); lint exits 0. — traces to
   `drift-sweep.md` §Verification — Automated (REQ-GC-HARNESSP2-001, -003,
   -004).
**Entry criteria**: Chunk 0 complete (non-interference table names gc as an
out-of-loop tool that never reads `.sdd/`; lint `allow_files` mechanics in
place so gc's pass-through parser sees the final finding shape); Chunk 1
complete (the Q-IMPL-083/-084 `[resolved by …]` appends and the
`sdd-implement` split have landed, so the `qimpl-*` sweeps and the live
`--report` baseline see the final spec and skill text).
**Exit criteria**: `tools/sdd-gc.py` exists with `--help` and a passing
skeleton `--self-test`; live `--report` exits 0; `FIXABLE = []`; lint exits 0;
traceability Test / Implementation filled for REQ-GC-HARNESSP2-001, -004 (the
-002 / -003 rows close in Chunk 5 once every sweep exists).

### Chunk 5: Drift sweep, part 2 — sweeps 7/11/12, `--fix` whitelist, full marker-4 fixture, cadence hooks, DONE routing
**Goal**: `tools/sdd-gc.py` carries the full fifteen-row table — `stale-chain`,
`trace-empty`, `traceability-aggregate` added, the pinned Q-IMPL counting rule
confirmed against its reference values — the four-rule idempotent `--fix`
whitelist and the complete two-workstream marker-`4` fixture of §Self-Test
Fixture; `sdd-orchestrate` runs it at entry (`GC:` line) and at DONE
(`record | ignore` routing into `verification.md` §Next Steps). Traces to
`drift-sweep.md`.
**Depends on**: Chunk 4.
**Budget**: ≤ 80 tool calls for the dispatched leaf (gc extension, fixture
growth, `SKILL.md` stubs + pointers, the verify task).
**Risk**: `stale-chain` and `traceability-aggregate` re-implement the
`ws-staleness.md` / `ws-traceability.md` contracts inside gc — any divergence
surfaces as a false **fail** on the live repository; triage per Risks
(genuine defect → corpus, tool bug → gc), never silence.
**Tasks**:
1. [x] [implement] gc sweeps 7, 11, 12: `stale-chain` (research → requirements
   → specs → plan → verification by `last_updated`; per workstream via plan
   `traces to` → spec `requires:` → category files; `pending-red` read as
   "verification exists, not passed"; marker `3` walks flat `docs/plan.md`
   and ignores `--workstream` with a note; stops at the last existing
   artifact); `trace-empty` (Spec-empty rows; Implementation-filled /
   Test-empty rows; an amendment row — Spec differs from the legacy row for
   the same id — inherits the legacy Verified and is never a gap);
   `traceability-aggregate` (aggregate == `regenerate(per-ws files)` per
   `ws-traceability.md`; skipped at marker `3`). Never reads `.sdd/`. Confirm
   the **pinned Q-IMPL counting rule** from Chunk 4 is unchanged and that the
   docstring's three reference commands still reproduce the 2026-09-17
   reference values (the rule text is not restated here). —
   traces to `drift-sweep.md` §Sweep Table rows 7, 11, 12 (REQ-GC-HARNESSP2-002);
   `telemetry.md` §XSPEC amendment-row rule.
2. [x] [implement] `--fix` whitelist: replace Chunk 4's `FIXABLE = []` with
   `FIXABLE = [xlink-dead,
   index-requirements, traceability-aggregate, plan-history-name]` with the
   tabled rewrites (unique-candidate link repair, ID-sorted Files-table row
   insertion, deterministic aggregate regeneration with legacy rows in shipped
   order + per-ws rows stable-sorted and empty cell = two spaces, date-prefix
   rename); every fix prints changed paths, is a no-op on a second run, never
   touches `last_updated`, never writes under `docs/ws/<other-id>/` when
   `--workstream` is given; any other rule → exit 2 `not a fixable rule`. —
   traces to `drift-sweep.md` §`--fix` Whitelist, §Routing at DONE (dates
   never auto-fixed) (REQ-GC-HARNESSP2-006, -007).
3. [x] [implement] `--self-test`, full fixture: extend Chunk 4's
   `build_fixture()` to the complete tree of §Self-Test Fixture (marker `4`,
   workstreams `alpha`/`beta`, Approved `a.md` traced by alpha, Draft `b.md`
   traced only by beta, a differing aggregate, the three `trace-empty` rows,
   the clean copy) and assert every row's symbolic counts, exit codes (0 / 1 /
   2 incl. `--fix nonexistent-rule` and `--fix staleness`), `--fix
   traceability-aggregate` idempotence, non-empty `fix` on every finding,
   summary line last, lint size warnings passing through, and that each fail
   rule fires exactly once. — traces to `drift-sweep.md` §Self-Test Fixture
   (REQ-GC-HARNESSP2-001, -002, -003).
4. [x] [implement] In `skills/sdd-orchestrate/SKILL.md`: the **entry** step —
   run `python3 tools/sdd-gc.py --report` before the workstream picker (marker
   `4`) / before phase detection (marker `3`) and render one line `GC: clean`
   or `GC: F fail, W warn — run tools/sdd-gc.py --report`, then open the picker
   regardless (informational, never blocks); §Transition — at DONE run
   `python3 tools/sdd-gc.py --report [--workstream <id>]`, render the findings,
   route per the table (mechanical → `--fix <rule>` reviewed and committed by
   the operator; needs-a-decision → `record | ignore`, `record` appends `- gc
   <rule>: <file:line> — <fix>` under the completed cycle's `verification.md`
   `## Next Steps` — the section defined by Chunk 2 task 4 — outside any
   observed window; out-of-scope → note); state that gc never runs between
   stages, never blocks a gate and is never driven by `/schedule` or `/loop`;
   never creates or modifies a plan task. Stubs + pointers only. — traces to
   `drift-sweep.md` §Cadence, §Routing at DONE, §Skill Changes
   (REQ-GC-HARNESSP2-005, -006, REQ-SKILL-HARNESSP2-004 gc half);
   `orchestration.md` Q-IMPL-HARNESSP2-008.
5. [x] [verify] Per `drift-sweep.md` §Verification — Automated: `python3
   tools/sdd-gc.py --self-test` exits 0 on the full fixture; `--help` exits 0 and names every flag,
   the three classes with rule ids and the exclusions; `grep -n 'FORBIDDEN =\|
   REQUIRED =' tools/sdd-gc.py` is empty; on this repository `--report` exits 0
   with no fail finding (warn/info counts unpinned) and the Q-IMPL counts are
   compared with the 2026-09-17 reference values (drift from
   `Q-IMPL-HARNESSP2-*` expected and noted); `--fast` completes without a date
   walk; `grep -n '/schedule\|/loop' skills/sdd-orchestrate/SKILL.md` is empty
   and both cadence moments name the command; on a fixture copy with one dead
   link the entry line reads `GC: 1 fail, 0 warn` and the picker still opens;
   replay `test_record_routing` on a fixture `verification.md` (two `- gc …`
   lines appended under `## Next Steps`, `plan.md` byte-identical, `git
   ls-files docs/` gains no path); lint exits 0. — traces to `drift-sweep.md`
   §Verification — Automated / Manual (REQ-GC-HARNESSP2-001..007).
**Entry criteria**: Chunk 4 complete (gc core, finding shape, `FIXABLE = []`
and the skeleton `build_fixture()` in place; Chunk 1's `SKILL.md` provisioning
text is already on Chunk 4's base, so the ≤ ~470 budget for the entry/DONE
stubs is measured on the integrated tree).
**Exit criteria**: `tools/sdd-gc.py` carries all fifteen rows with `--help` and
a passing full `--self-test`; live `--report` exits 0; `FIXABLE` has four
rules, each idempotent; `SKILL.md` names both cadence moments and the
`record | ignore` routing; lint exits 0; traceability filled for
REQ-GC-HARNESSP2-002, -003, -005..007 and the gc half of REQ-SKILL-HARNESSP2-004.

### Chunk 6: Lint rows (`REQUIRED` a1/a2/b/c, d2 regex, `FORBIDDEN` `\.sdd/`) + self-test mutations + `SKILL.md` integration pass
**Goal**: the linter enforces every marker Chunks 0–5 introduced — four new
`REQUIRED` rows, the `(?<!CHUNK_)(?<!RED_)VERDICT:` consumer regex and the
file-granular `FORBIDDEN` `\.sdd/` row — with `--self-test` §7 mutation
coverage; `skills/sdd-orchestrate/SKILL.md` carries every new gate stub once,
within ≤ ~470 lines, and the integrated skill set is lint-clean with size
warnings only. Traces to `telemetry.md` §Lint Guard, `adversarial-verify.md`,
`arbitrated-handoff.md` §Skill and Lint Changes, `skill-lint-v5.md`
Q-IMPL-HARNESSP2-006, `orchestration.md` Q-IMPL-HARNESSP2-008.
**Depends on**: Chunk 2, Chunk 3, Chunk 5.
**Tasks**:
1. [x] [implement] In `tools/sdd-skill-lint.py` `REQUIRED`: (a1)
   `dispatch-templates.md` ∋ `RED_VERDICT: BROKEN \| HELD` min 1 (producer);
   (a2) `skills/sdd-orchestrate/SKILL.md` ∋ `RED_VERDICT:` min 1 (consumer —
   pinned to `SKILL.md`, where the d2 row and the Chunk 2 task 3 parse step
   live; `references/return-contract.md` also carries the token but is not
   this row's file); (b) `references/loop-control.md` ∋
   `REVIEW: CONTRADICTION` min 1 (consumer-only); (c) `skills/sdd-review/SKILL.md`
   ∋ a line matching `M1:.*affects` min 1; change the existing d2 pattern to
   `(?<!CHUNK_)(?<!RED_)VERDICT:`; each row with `reason` and a `fix` naming
   the counterpart file; `len(REQUIRED) >= 32`. — traces to
   `adversarial-verify.md` §Skill and Lint Changes (rows a1, a2, d2);
   `arbitrated-handoff.md` §Skill and Lint Changes (rows b, c)
   (REQ-LINT-HARNESSP2-001).
2. [x] [implement] In `tools/sdd-skill-lint.py` `FORBIDDEN`: the `\.sdd/` row
   (`files: None`, `allow_files` = `skills/sdd-orchestrate/SKILL.md`,
   `skills/sdd-orchestrate/references/telemetry.md`,
   `skills/sdd-orchestrate/references/write-scope.md`, `allow: []`, the spec's
   `reason` and `fix`, fail severity, raw-text scan incl. fences). Extend
   `self_test()`: §7's mutation loop covers the four new `REQUIRED` rows (strip
   each marker from a temp copy → exit 1 with that row's `fix`); a fixture
   `sdd-plan/SKILL.md` containing `.sdd/telemetry.jsonl` inside a fence → exit
   1 with the `\.sdd/` row's fix; fixtures at the three allowlisted paths →
   exit 0; a file containing only `RED_VERDICT: HELD` does not satisfy row d2.
   — traces to `telemetry.md` §Lint Guard (REQ-TELEM-HARNESSP2-007,
   REQ-LINT-HARNESSP2-002); `skill-lint-v5.md` Q-IMPL-HARNESSP2-006.
3. [x] [implement] Integration pass over `skills/sdd-orchestrate/SKILL.md`
   after the wave-2 and wave-3 merges: §The gate lists the REQ-ORCH-034 signal order
   **once** including `RED_VERDICT:` at the verify stage; the pause family
   (`REVIEW: MALFORMED`, `RETURN: MALFORMED`, reject-with-no-actionable-findings,
   `REVIEW: CONTRADICTION`) is one list with pointers; the telemetry stub is ≤
   10 lines counting the §LOOP block only; the gc entry and DONE steps, the provisioning sentence, the red
   opt-in and the `pending-red → verify` position row each appear once;
   duplicated stub text is deduplicated; the never-auto-advance sentence,
   `research_id` ≥ 3, `docs/.sdd-version`, the fan-out `Depends on` parser,
   the canonical per-chunk gate block and every existing `REQUIRED` literal
   are intact; `wc -l` ≤ ~470 — move overflow prose to the owning reference
   file, never delete a marker. — traces to `orchestration.md`
   Q-IMPL-HARNESSP2-008 (REQ-ORCH-034); `telemetry.md` §Skill and Lint Changes
   (stub ≤ 10 lines, REQ-SKILL-HARNESSP2-001); `adversarial-verify.md`,
   `arbitrated-handoff.md`, `drift-sweep.md`, `dispatch-snapshot-base.md`
   §Skill Changes (REQ-SKILL-HARNESSP2-002, -003, -004).
4. [x] [verify] `python3 tools/sdd-skill-lint.py --self-test` exits 0; the live
   lint exits 0 printing `OK: 21 file(s) clean, K warning(s)` (17 baseline + `references/drift-sweep.md` (Chunk 5) +
   `references/telemetry.md` + `sdd-implement/references/stuck-detection.md`
   + `leaf-return.md`) with `K` from size warnings naming exactly
   `sdd-orchestrate` and `sdd-migrate`; mutation test — for each of the four
   new rows and the `\.sdd/` row, mutate a temp copy → exit 1 with that row's
   `fix:`; `grep -rn '\.sdd/' skills/` hits only the three allowlisted files;
   `grep -rn 'decision_by' skills/` hits only
   `sdd-orchestrate/references/telemetry.md`; `wc -l
   skills/sdd-orchestrate/SKILL.md` ≤ ~470; `wc -l skills/sdd-implement/SKILL.md`
   ≤ 400; `python3 tools/sdd-scope-check-selftest.py` passes 9/9; `python3
   tools/sdd-telemetry.py --self-test` and `python3 tools/sdd-gc.py --self-test`
   exit 0; `python3 tools/sdd-gc.py --report` exits 0 on the integrated tree. —
   traces to `telemetry.md`, `adversarial-verify.md`, `arbitrated-handoff.md`
   §Verification (lint rows) (REQ-LINT-HARNESSP2-001, -002,
   REQ-TELEM-HARNESSP2-007); `skill-lint-v5.md` Q-IMPL-HARNESSP2-006.
**Entry criteria**: Chunks 2, 3, 5 (and 4 through 5) complete and merged into one tree (every
marker present: `RED_VERDICT:`, `REVIEW: CONTRADICTION`, the Material
`affects` line, the `.sdd/` mentions confined to the three files).
**Exit criteria**: lint exits 0 with 21 files clean and the two-file warn set;
all five new rows present and mutation-tested; `SKILL.md` ≤ ~470;
traceability filled for REQ-LINT-HARNESSP2-001, -002, REQ-TELEM-HARNESSP2-007
and the `SKILL.md`-integration halves of REQ-SKILL-HARNESSP2-001..004.

### Chunk 7: Documentation, evaluation deliverables, traceability closure, holistic verify + probe report
**Goal**: operators can read every new signal in `USAGE.md` and one paragraph
in `CLAUDE.md`; the evaluation mode is defined-not-built with its guards
verified, the scorer ships if there is room and the N = 3 pilot is recorded or
deferred to §Next Steps; every `harness-p2` traceability row has Test and
Implementation cells and the aggregate is regenerated; the six specs' Manual
sections are walked on fixtures; the two RS-008 probes and this cycle's own
measurements are recorded from real dispatch facts. Traces to `evaluation.md`,
`telemetry.md` §Skill and Lint Changes, and the §Verification — Manual
sections of all six specs.
**Depends on**: Chunk 6.
**Tasks**:
1. [ ] [implement] `CLAUDE.md` §Driver (`sdd-orchestrate`): **one short
   paragraph** naming per-dispatch telemetry (`.sdd/telemetry.jsonl` —
   gitignored, orchestrator-only, never read by phase detection), the verify
   red-team opt-in (`RED_VERDICT:`, `pending-red`), the `REVIEW: CONTRADICTION`
   pause and the `tools/sdd-gc.py` sweep at entry/DONE; the "Four verification
   layers" bullet stays byte-unchanged. — traces to `telemetry.md` §Skill and
   Lint Changes (`CLAUDE.md` row) (REQ-SKILL-HARNESSP2-008);
   `adversarial-verify.md` §Skill and Lint Changes (`CLAUDE.md` row unchanged).
2. [ ] [implement] `skills/sdd-orchestrate/USAGE.md`: one section per new signal
   — the `TELEMETRY:` lines and the KICKOFF opt-out (plus the post-cycle
   `sdd-telemetry.py summarize` step); the red opt-in, `RED_VERDICT:` gate
   block, `fix | accept (record) | stop` and `pending-red`; `REVIEW:
   CONTRADICTION`, its four options and what "note" means; the `GC:` summary at
   entry, DONE findings and `record | ignore` routing; the `CATCH-UP` line in
   the write-scope block; update §7b's pause list and the abridged exchange in
   §3 for the verify gate. Beside every `.sdd/` mention the text "gitignored,
   orchestrator-only, never read by phase detection". — traces to
   `telemetry.md` §Skill and Lint Changes (`USAGE.md` row)
   (REQ-SKILL-HARNESSP2-008); `arbitrated-handoff.md`, `drift-sweep.md`,
   `adversarial-verify.md`, `dispatch-snapshot-base.md` §Skill Changes
   (REQ-ARB-HARNESSP2-006, REQ-GC-HARNESSP2-005, REQ-REDB-HARNESSP2-007,
   REQ-HARN-HARNESSP2-001).
3. [ ] [implement] (**should** — ship only if the chunk has room; otherwise the
   deferral line `- REQ-EVAL-HARNESSP2-002: build tools/sdd-eval.py` goes to
   `verification.md` §Next Steps) Create `tools/sdd-eval.py` (stdlib-only):
   reads `.sdd/telemetry.jsonl` plus a `verification.md` `status` line, groups
   records into runs by (`cycle.workstream`, `cycle.kickoff_date`,
   `cycle.research_id`), computes the nine scorer fields per run and one
   aggregate row (CSV or aligned text) using only the derivation table of
   `references/telemetry.md`; empty file → zero rows, `N = 0`, no error;
   `--help`; `--self-test` on a six-record fixture yielding every field. No
   `tools/sdd-eval-run*` or headless-driver script. — traces to
   `evaluation.md` §Scorer Fields (REQ-EVAL-HARNESSP2-002); `telemetry.md`
   §Scorer Derivation.
4. [ ] [verify] Evaluation-mode guards per `evaluation.md` §Verification —
   Automated: `grep -rn 'decision_by' skills/` matches only
   `sdd-orchestrate/references/telemetry.md`; `sdd-orchestrate/SKILL.md`
   §Rules still contains the never-auto-advance sentence and REQ-ORCH-011 text
   is unamended; no record in this repository's `.sdd/telemetry.jsonl` has
   `decision_by: policy`; `ls tools/ | grep -c 'sdd-eval-run'` is 0 and no
   headless-driver file exists; this plan contains no task that dispatches the
   orchestrator (grep this file for `/sdd-orchestrate` invocations — the pilot
   task below is operator-run and only records); `evaluation.md` names the
   N ≥ 30 harness out of scope with conditions (a)–(c); the nine scorer fields
   each have a derivation row naming only record keys and `verification.md
   status`. — traces to `evaluation.md` §Evaluation Mode — Defined, Not
   Built, §Out of Scope (REQ-EVAL-HARNESSP2-001, -002, -004).
5. [ ] [verify] (**should**, operator-run; default **deferred**) Manual N = 3
   pilot per `evaluation.md` §Manual N = 3 Pilot: build the toy repository
   (`tools/sdd-scope-check-selftest.py` `make_repo()` shape + one requirement,
   one spec with two acceptance criteria, a two-chunk plan, `CLAUDE.md` with
   `pytest -q` and `sdd-eval-toy: true`, `docs/.sdd-version` = `4`, workstream
   `default`); the operator runs three orchestrated cycles (≥ 1 research-entry,
   the rest plan-entry; every gate operator-decided; a distinct `research_id`
   per run); score with `tools/sdd-telemetry.py summarize` on the toy's own
   `.sdd/telemetry.jsonl`; record a "Pilot (N = 3)" section with the three-row
   table and observed wall time for `docs/ws/harness-p2/verification.md`. This
   task **cannot** be executed by a dispatched implement leaf (it requires the
   operator to drive the orchestrator); if not run during the verify stage,
   the deliverable is the line `- REQ-EVAL-HARNESSP2-003: run the N = 3 pilot
   on the toy` under `verification.md` `## Next Steps` (the section defined by
   Chunk 2 task 4). — traces to `evaluation.md` §Manual N = 3 Pilot
   (REQ-EVAL-HARNESSP2-003).
6. [ ] [implement] Traceability closure: fill any still-empty Test /
   Implementation cell in `docs/ws/harness-p2/traceability.md` for the 49
   HARNESSP2 rows + the REQ-HARN-027 amendment row (50 in total: REQ-TELEM-,
   REDB-, ARB-, GC-, EVAL-, HARN-HARNESSP2-, LINT-HARNESSP2-,
   SKILL-HARNESSP2-, plus the REQ-HARN-027 amendment row — Verified inherits `pass`;
   REQ-EVAL-HARNESSP2-003 Test cell = "pilot recorded" or "deferred to §Next
   Steps"); the Verified column stays for `sdd-verify`; regenerate the shared
   aggregate with `python3 tools/sdd-gc.py --fix traceability-aggregate`
   (never hand-merged); confirm `docs/spec/overview.md` needs no edit beyond
   naming the new reference/tool files — edit only if a shipped filename
   differs. — traces to `ws-traceability.md` §Aggregation Contract;
   `drift-sweep.md` §`--fix` Whitelist (REQ-GC-HARNESSP2-007); `telemetry.md`
   §XSPEC amendment-row rule.
7. [ ] [verify] Holistic fixture walkthrough across the six specs' Manual
   sections, without a live dispatch: on a throwaway two-chunk fixture repo,
   instantiate the RED TEAM and verify PIPELINE (`Red team: enabled`) templates
   verbatim and confirm no empty slot and nothing outside the slot set; render
   the verify stage gate from a fixture red return + review (`SCOPE:` →
   `RED_VERDICT:` → `VERDICT:` → counters) and confirm `proceed` is withheld
   until `accept`; replay a two-round fix loop from a past cycle's gate text
   (v5 cycle, `docs/ws/default/verification.md` context) through the class
   rule and confirm the assigned class matches the operator's reading; run
   the RS-HARNESSP2-001 Q6 situation (worktree one commit behind, prompt names
   the tip) with the §3 commands → zero false-positive `OUT` paths and a
   `CATCH-UP` line; append two fixture records to a temp `.sdd/telemetry.jsonl`
   and confirm `summarize` counts equal the fixture gate text; run
   `tools/sdd-gc.py --report` on the live repository and compare the Q-IMPL
   counts with the reference values; `git ls-files docs/` gained only
   `docs/ws/harness-p2/{plan.md,verification.md,plan-history/*}` and Q-IMPL
   appends this cycle; no `docs/ws/*/telemetry*`. — traces to the
   §Verification — Manual sections of `telemetry.md`, `adversarial-verify.md`,
   `arbitrated-handoff.md`, `drift-sweep.md`, `dispatch-snapshot-base.md`
   (REQ-TELEM-HARNESSP2-004, REQ-REDB-HARNESSP2-007, REQ-ARB-HARNESSP2-002,
   REQ-GC-HARNESSP2-003, REQ-HARN-HARNESSP2-001, REQ-HARN-027).
8. [ ] [verify] Probe report from **real dispatch facts** of this cycle (never
   simulated): from the workstream branch's `git log`, the orchestrator's gate
   text and, once Chunk 0 has landed, `.sdd/telemetry.jsonl` (`summarize`
   per-chunk block), tabulate — RS-008 probe 1: implement + verifier + fix +
   redo dispatches per chunk for Chunks 0–7 against the "≤ 1 extra
   dispatch-equivalent per chunk" trigger; RS-008 probe 2: every `SCOPE:`
   finding this cycle, classed true violation / false positive (incl. any
   catch-up false positives before Chunk 1 landed) against the
   "recurring `OUT` on legitimate side-writes" trigger; this cycle's own
   counts: `REVIEW: CONTRADICTION` pauses by class, `RED_VERDICT:` outcomes if
   red was enabled, `TELEMETRY: WRITE FAILED` occurrences, `GC:` entry/DONE
   findings. Deliver the table in the form used by RS-008 probes 1 and 2 (see
   `docs/ws/default/verification.md` — never written there), for the
   sdd-verify stage to place in `docs/ws/harness-p2/verification.md`; state explicitly which replan
   triggers below fired or did not. — traces to `docs/ws/harness-p2/kickoff.md`
   Q6; `evaluation.md` §Scorer Fields (fields 3, 5, 6, 7 as live values);
   `telemetry.md` §Out-of-Loop Reader (REQ-TELEM-HARNESSP2-009).
9. [ ] [verify] Cross-skill consistency sweep: every token, key and option is
   spelled as its owning spec spells it across `SKILL.md`, the six
   `references/` files, `sdd-verify`, `sdd-review`, `sdd-replan`,
   `sdd-implement` (+ its two references), `USAGE.md` and `CLAUDE.md` —
   `RED_VERDICT:`, `RED_BREAK`, `pending-red`, `Red team: enabled`, `REVIEW:
   CONTRADICTION`, `THIRD_OPINION`, `CATCH-UP`, `TELEMETRY:`, `GC:`,
   `decision_by`, `contradiction_class`, `allow_files`, `FIXABLE`,
   `## Next Steps` (confirm every pointer to that section — gc `record`
   routing, the evaluation deferral lines, `USAGE.md` — resolves to the one
   definition in `sdd-verify` Step 6 on the integrated tree); the
   four-layer table in `sdd-verify`, `sdd-review` and `CLAUDE.md` diffs clean
   against `c38922d`; `sdd-review` diff against `c38922d` is the Material line
   + example only; lint, all three tool self-tests and the scope self-test
   exit 0. — traces to `adversarial-verify.md` §Positioning (four-layer table
   unchanged, REQ-REDB-HARNESSP2-002); `arbitrated-handoff.md` §Review Key
   (REQ-ARB-HARNESSP2-008); `telemetry.md` §Skill and Lint Changes
   (REQ-SKILL-HARNESSP2-008).
**Entry criteria**: Chunk 6 complete (integrated, lint-clean skill set with
all rows; every token defined).
**Exit criteria**: `CLAUDE.md` and `USAGE.md` updated; no empty Test /
Implementation cell in `docs/ws/harness-p2/traceability.md`; aggregate
regenerated; scorer shipped or deferral line prepared; pilot recorded or
deferral line prepared; probe table produced from real facts; all verify tasks
pass with no acceptance criterion failed; plan `status: complete`; ready for
`sdd-verify`.

## Replan Triggers

- **`SKILL.md` cannot absorb the new gate text within ~470 lines without
  breaking a lint `REQUIRED` row** (e.g. the `research_id` ≥ 3 row, the d2
  consumer row, or the canonical per-chunk gate block) → move further
  stub-able prose (red exit rule, gc routing table, provisioning block) into
  the owning reference file and keep a one-line pointer; if a pointer alone
  cannot satisfy a consumer row, re-point that row at the reference file
  (`skill-lint-v5.md` guard 1 option b precedent) — Chunk 6, minor replan.
- **Class (b) contradiction false-positive rate observed > 1 per cycle** (a
  legitimately new Critical pauses the loop more than once; `arbitrated-
  handoff.md` Open Question 1) → narrow the trigger to Critical-only lines or
  require `affects` overlap with round N for class (b); record the change in
  `arbitrated-handoff.md` §Contradiction Classes — Chunk 3 text.
- **Per-chunk dispatch cost > 1 extra dispatch-equivalent per chunk** (RS-008
  probe 1, measured by Chunk 7 task 8 from this cycle's dispatches) → flip the
  chunk verifier default to opt-in at the fan-out opt-in gate and revisit
  `harness-chunk-verifier.md` Open Question 1 — a `SKILL.md` §Opt-in gate
  text change plus `USAGE.md`.
- **Write-scope `OUT` false positives on legitimate side-writes** (RS-008
  probe 2, measured by Chunk 7 task 8; catch-up false positives before Chunk 1
  lands are expected and excluded) → widen the default scope table in
  `references/write-scope.md` §2 and fold the widenings back into
  `harness-write-scope.md` §Default Scope Table; if spec-file `ADVISORY` proves
  noisy, revisit REQ-HARN-026.
- **`sdd-gc.py` self-test fixture counts drift when specs change** (a
  symbolic `D`/`B` assertion breaks because the fixture mirrored live text, or
  the live `--report` gains a fail finding from a genuine corpus defect this
  cycle introduced) → fixture must use synthetic counts only (Chunk 4 task 3 /
  Chunk 5 task 3 rework); a genuine corpus defect is fixed in the corpus by
  the owning skill, never silenced in gc.
- **`sdd-implement/SKILL.md` cannot reach ≤ 400 lines while keeping every
  `REQUIRED` literal in the stub** → re-point the affected rows at
  `references/stuck-detection.md` / `leaf-return.md` (Chunk 1 task 5 already
  allows it); if the two files must merge into one (`dispatch-snapshot-base.md`
  Open Question 2) the stub links change, nothing else.
- **A phase-detection reader mis-maps `pending-red`** (a skill treats it as
  `pass` or as `fail` → replan) discovered by Chunk 2 task 6 or the holistic
  verify → add the missing reader row (`sdd-plan`/`sdd-implement` only read
  `plan.md`, so this should be confined to `sdd-verify`, `sdd-replan`,
  `sdd-orchestrate`, gc) — Chunk 2 / Chunk 5 text.
- **Parallel wave-2 chunks conflict in `SKILL.md` §The gate or
  `write-scope.md` §3/§5 beyond what fan-out's redo-by-re-derivation
  resolves** → collapse wave 2 to sequential order 2 → 3 → 4 (plan-level
  change, no spec change).
- **The record schema cannot express a gate option or a scorer field**
  (`telemetry.md` Open Question 2; `evaluation.md` derivation contract) → the
  schema, not the scorer, is defective: bump `v` to `2` in
  `references/telemetry.md` with the added enum/key, keep `summarize`
  tolerant of both — Chunk 0 rework, spec amendment via a new Q-IMPL entry.

## Completed

(none — new workstream)

## Risks

- **Three chunks edit `write-scope.md` §3/§5** (Chunk 0: third observation +
  (b) exception; Chunk 1: provisioning + (c); Chunk 3: section resolution +
  (a) note). Mitigation: Chunk 0 and Chunk 1 add distinct, non-adjacent
  bullets (each task says exactly which line it adds); Chunk 3 depends on both
  and lands on the merged tree; Chunk 6 task 3 and Chunk 7 task 9 check that
  `.sdd/` appears only in §3/§5 and that (a), (b), (c) each appear once.
- **Wave-2 chunks (2, 3) and wave-3 Chunk 5 all touch
  `sdd-orchestrate/SKILL.md` §The gate** (red opt-in and exit rule;
  contradiction pointer; gc entry/DONE). Mitigation: each adds a stub in a
  named position (red: signal-order sentence + verify gate paragraph;
  arbitration: one pointer line in "Edge cases routed through the gate"; gc:
  entry step and §Transition); every one of them depends on Chunk 1 so the
  stubs land on the integrated wave-1 tree; Chunk 6 task 3 is the explicit
  integration pass; the replan trigger collapses wave 2 to sequential if
  merges churn.
- **Lint row ordering.** A `REQUIRED` or `FORBIDDEN` row added before its
  marker exists (or before `.sdd/` mentions are confined) breaks `exit 0` for
  every intermediate tree and every parallel worktree. Mitigation: Chunk 0
  ships `allow_files` mechanics + a synthetic self-test row only; all shipped
  rows land in Chunk 6 after Chunks 2–5 merge.
- **`SKILL.md` size budget.** Five features add gate text to a 469-line file
  with a ~470 target. Mitigation: every task in Chunks 0–5 is written as
  "stub + pointer", detail goes to the owning reference; the first replan
  trigger names the fallback; the target is a warn threshold (400) already
  exceeded, so the hard constraint is the `REQUIRED` rows, not the count.
- **Meta-feature testability.** No compiled code exercises the orchestrator's
  telemetry writer, red gate, arbitration or provisioning; verification is
  fixture walkthroughs plus the three tools' self-tests and the scope
  self-test. Mitigation: verify tasks are behavioural (temp git repos, exact
  finding strings, mutation tests); the live measurements are Chunk 7 task 8
  from this cycle's own dispatches, not pretended.
- **Two leaves may append to `.sdd/telemetry.jsonl` inadvertently** once
  Chunk 0's stub exists but before the lint row (Chunk 6) exists. Mitigation:
  `.sdd/**` is never in any write scope, so the third observation (Chunk 0
  task 3/4) already reverts it; the templates never name the path.
- **`sdd-gc.py` live `--report` may surface pre-existing corpus drift**
  (dead anchors, unreferenced Q-IMPL, stale dates in `docs/ws/default/`).
  Mitigation: warn/info are not pinned; a **fail** finding on the live repo is
  triaged at Chunk 4 task 4 / Chunk 5 task 5 — genuine defect → fixed in the
  corpus by the owning skill's rule (`--fix` where whitelisted), tool bug → fixed in gc;
  never silenced.
- **The pilot and the scorer are `should` items.** Both may be deferred to
  §Next Steps by design (`evaluation.md` Open Question 2); the plan stays
  complete either way because the deferral line is the alternative
  deliverable, defined once in Chunk 2 task 4's `## Next Steps` section.
- **Spec writes in the shared corpus.** The two `[resolved by …]` appends
  (Chunk 1 task 4) are the only spec writes this cycle makes; they are
  append-only per `deviation-protocol.md` and `ADVISORY` under the default
  scope table — expected gate text, not a violation.

## Open Questions / Assumptions

- **Status `planned`.** This plan was authored by a non-interactive pipeline
  subagent with `last_updated: 2026-09-17`; the frontmatter uses the plan
  status vocabulary (`planned → active → complete`, `sdd-plan` SKILL.md) —
  `sdd-implement` flips it to `active` and later `complete`. Operator sign-off
  is the orchestration gate, not a frontmatter value.
- **Single-milestone structure.** Eight chunks, one delivery (lint rows and
  skill text must ship together for `exit 0`); a single
  `docs/ws/harness-p2/plan.md` is used although it exceeds ~300 lines, as the
  v5 plan did. Default: keep single-milestone.
- **Chunks 2, 3 and 4 depend on Chunk 1 as well as Chunk 0.** Chunk 3
  extends the same `write-scope.md` §3 block that Chunk 1 rewrites
  (provisioning + `HEAD_before`/`HEAD_after`); Chunk 2's §The gate block and
  Chunk 5's entry/DONE stubs (via Chunk 4) must fit the `SKILL.md` budget on
  the integrated wave-1 tree, after Chunk 1 task 2 edits §Pipeline subagent
  dispatch; Chunk 4's `qimpl-*` baseline needs Chunk 1's Q-IMPL appends. Two
  independent roots still exist (0 ‖ 1) and wave 2 still fans out three ways
  (2 ‖ 3 ‖ 4); the gc split (4 → 5) adds one sequential wave.
- **gc split into Chunk 4 / Chunk 5, integer ids.** The review asked for
  `4a`/`4b`; `fan-out.md` §1 parses chunk **ordinals** from `### Chunk N:`
  headers and its text must stay exactly as written, so alphanumeric ids are
  not demonstrably tolerated — the halves are Chunk 4 and Chunk 5 and the
  former Chunks 5/6 are now 6/7.
- **`allow_files` mechanics in Chunk 0, row in Chunk 5.** The `\.sdd/` row
  would fail on any tree where `.sdd/` is still mentioned outside the three
  files (none today, but the risk table applies); mechanics + a synthetic
  self-test row in Chunk 0 keep every intermediate tree green; the row lands
  in Chunk 6. Default: as
  stated.
- **`gate.decision` table duplicated in `telemetry.md`.** The spec contains
  the normalisation table twice (identical); `references/telemetry.md` carries
  it once. Not a spec contradiction; no Q-IMPL needed.
- **`references/telemetry.md` is the third lint-allowlisted file, and the
  `sdd-implement` split adds two reference files** → the live lint file count
  becomes 20. Default: assert 20 in Chunk 6 task 4; adjust only if Chunk 1
  merges the two `sdd-implement` references into one (then 19).
- **Reference file names for the `sdd-implement` split**: `stuck-detection.md`
  and `leaf-return.md` (`dispatch-snapshot-base.md` Open Question 2 default).
- **Scorer (`tools/sdd-eval.py`) ships only if Chunk 7 has room**
  (`evaluation.md` Open Question 2 default); Chunk 7 task 3 is `should`. The
  pilot (task 5) is `should` and **deferred by default** — a dispatched
  implement leaf cannot drive the orchestrator; the operator may run it during
  the verify stage instead.
- **Red team stays OFF for this cycle's own verify stage** — operator
  decision at the plan review gate (`adversarial-verify.md` Open Question 2:
  prose-only acceptance criteria); Chunk 2 is exercised by its fixture
  walkthroughs, not live; the probe report records `RED_VERDICT:` outcomes
  only if the operator overrides this at the verify gate.
- **Telemetry for this cycle starts when Chunk 0 merges.** Dispatches before
  that are counted by hand from `git log` and gate text (Chunk 7 task 8);
  `summarize` covers the rest.
- **Heading normalisation** in arbitration keys strips a leading ordinal
  (`arbitrated-handoff.md` Open Question 3 default); the same rule serves gc's
  `qimpl-broken-ref` anchor check.
- **No `.pre-commit-config.yaml`** is added by this plan (`drift-sweep.md`
  Open Question 1: proposed at the DONE gate as a repository choice).
- **Repo layout**: marker `4`, workstream `harness-p2`; all `docs/ws/default/**`
  paths are read-only inputs for probes and are never written.
