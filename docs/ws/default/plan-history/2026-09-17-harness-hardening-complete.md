---
last_updated: 2026-09-17
status: complete
---

# Implementation Plan: Harness Hardening (v5)

## Overview

Harden the orchestrated SDD loop (`sdd-orchestrate` driving `sdd-implement`,
`sdd-review`, `sdd-replan`) with deterministic loop control and decoupled
verification — without adding an artifact type, a layout change, or a loop log.
This is a **meta-feature**: the implementation edits skill text
(`skills/sdd-orchestrate/SKILL.md`, its `references/` — two new files
`return-contract.md` and `write-scope.md`, a third `v4-workstreams.md` receiving
moved marker-4 prose, plus `dispatch-templates.md` and `fan-out.md`;
`skills/sdd-implement/SKILL.md`; `skills/sdd-review/SKILL.md`;
`skills/sdd-replan/SKILL.md`; `skills/sdd-orchestrate/USAGE.md`), one Python tool
(`tools/sdd-skill-lint.py`), the project convention doc (`CLAUDE.md`), one
append-only Q-IMPL entry in `docs/spec/ws-orchestration.md`, and the
Test/Implementation columns of `docs/requirements/traceability.md`. The five
harness specs decompose into: a structured leaf → orchestrator channel
(`RETURN:` block, repair packet, `VERDICT:` token — Chunk 1) on which three
independent contracts build — session/derived caps + ledger + checkpoint
(Chunk 2), the read-only chunk-close verifier with per-chunk sequential dispatch
(Chunk 3), and the declared write scope with the three-command check (Chunk 4).
The lint tool's v5 mechanics (Chunk 0) are independent of all skill-text work;
its new `REQUIRED` rows land only once the markers they enforce exist (Chunk 5,
together with the `SKILL.md` slimming that keeps the entry point at ≤ ~450
lines). Documentation, traceability closure and a holistic verify close the cycle
(Chunk 6). RS-008 de-risked every mechanism (Q1–Q5), so this plan carries **no
spike** tasks; the two RS-008 dogfooding probes are recorded as replan triggers.

## Conventions

- **Task types**: `[implement]` edits skill prose, templates, the lint tool or
  convention docs (the "code" here is the skills' described procedures plus one
  Python script); `[verify]` validates behavior against a spec's Verification
  section — fixture walkthroughs, mutation tests, greps and diffs — not "markdown
  lints".
- **Chunk headers**: `### Chunk N: <name>`; each chunk carries a `**Depends on**`
  line the fan-out boundary derivation parses (`fan-out.md` §1). Chunks 0 and 1
  are roots. Fan-out waves: wave 1 = Chunk 0 ‖ Chunk 1; wave 2 = Chunk 2 ‖
  Chunk 3 (both depend only on Chunk 1); then Chunk 4 → Chunk 5 → Chunk 6
  sequentially — Chunk 4 depends on Chunk 3 because its task 3 replaces the
  scope-check placeholder Chunk 3 task 4 inserts in `fan-out.md` §3.
- **Traceability**: each task names the spec section and REQ id(s) it implements.
  Test/Implementation columns of `docs/requirements/traceability.md` are filled at
  each chunk's close (Check 2); Chunk 6 sweeps the remainder.
- **Lint discipline**: `python3 tools/sdd-skill-lint.py` must exit 0 at every
  chunk close (size warnings permitted from Chunk 0 on). New `REQUIRED` rows are
  added only after their markers exist (Chunk 5) so no intermediate tree fails.
- **Per-chunk gate block**: the compact block in `harness-chunk-verifier.md`
  §Sequencing — Sequential Mode is the canonical text; every copy
  (`SKILL.md`, `references/write-scope.md`) is pasted from it, never
  paraphrased, so the byte-identical requirement holds
  (`references/return-contract.md` references the block but carries no copy).
- **Dates**: authored 2026-09-17. This repo stays at marker `3`; every marker-4
  path in the specs is written as a rooting rule, not exercised here.

## Chunks

### Chunk 0: Lint tool v5 mechanics (fix field, warn tier, size, path resolution)
**Goal**: `tools/sdd-skill-lint.py` prints a `fix:` line under every finding,
distinguishes `warn` from `fail`, warns on `SKILL.md` files over 400 lines (fails
over 1000), resolves backtick `references/` paths, and its `--self-test` covers all
of it. No new `REQUIRED` rows yet (see Conventions). Traces to `skill-lint-v5.md`.
**Depends on**: None.
**Tasks**:
1. [x] [implement] In `tools/sdd-skill-lint.py`: change `flag()` to
   `flag(path, line_no, rule, msg, fix, severity="fail")` with `fix` a required
   positional; store findings as `(severity, text)`; render each finding as
   `<path>:<line>: [<rule>] <message>` + indented `fix: <remediation>`; add a
   `fix` string to every existing `FORBIDDEN` and `REQUIRED` row (beside `reason`)
   and fixed remediation strings to the structure, ordinal and link checks. —
   traces to `skill-lint-v5.md` §Finding Shape and Remediation (REQ-LINT-001).
2. [x] [implement] Add the severity tier: rows may carry `"severity": "warn"`
   (default `fail`); `WARN ` prefix on warn findings; `run()` exits 1 iff any
   `fail`; summary line variants `OK: N file(s) clean`, `OK: N file(s) clean, K
   warning(s)`, `FAIL: N finding(s), K warning(s)`. — traces to
   `skill-lint-v5.md` §Severity Tier (REQ-LINT-002).
3. [x] [implement] Add `SIZE_WARN_LINES = 400`, `SIZE_FAIL_LINES = 1000` module
   constants and `check_size()` over `skills/*/SKILL.md` only (`references/*.md`,
   `USAGE.md` exempt; thresholds strict `>`), with the spec's fix string; wire it
   into `run()`. — traces to `skill-lint-v5.md` §SKILL.md Size Check (REQ-LINT-003).
4. [x] [implement] Extend `check_links()` to resolve backtick-quoted relative paths
   outside fenced code: `` `references/<file>` `` against the linted skill dir
   (fail), `` `skills/<skill>/references/<file>` `` against `REPO_ROOT` (fail),
   `` `docs/spec/<file>.md` `` against `REPO_ROOT` (warn); strip fragments and
   trailing punctuation; skip globs (`*`); keep the existing `[…](…)` resolution.
   — traces to `skill-lint-v5.md` §`references/` Path Resolution (REQ-LINT-004),
   Edge Cases.
5. [x] [implement] Extend `self_test()` with fixtures: `flag()` without `fix` raises
   `TypeError` (signature assertion); a warn-only fixture exits 0 and prints
   `1 warning(s)`; a 401-line SKILL.md warns and a 1001-line one fails; a backtick
   `references/missing.md` fails while an existing one passes; every emitted
   finding has a non-empty `fix`. Fixtures are temp dirs built inside the self-test
   (no new files under `tools/`). — traces to `skill-lint-v5.md` §Self-Test
   Extension (REQ-LINT-001..004).
6. [x] [verify] Run `python3 tools/sdd-skill-lint.py --self-test` (exit 0) and
   `python3 tools/sdd-skill-lint.py` on the untouched skill set: exit 0, output
   `OK: 13 file(s) clean, 2 warning(s)` with the two size warnings naming exactly
   `sdd-orchestrate` (607) and `sdd-migrate` (464); confirm the six existing
   `[…](references/…)` links in `sdd-orchestrate/SKILL.md` still resolve;
   `grep -n 'self.flag(' tools/sdd-skill-lint.py` shows a fix argument on every
   call. — traces to `skill-lint-v5.md` §Verification — Automated (REQ-LINT-001..004).
**Entry criteria**: none (root chunk).
**Exit criteria**: self-test and live lint exit 0; the only findings are the two
baseline size warnings; `grep -c '"fix"'`/`"fix"`-per-row count equals the number
of rule rows; traceability Test/Implementation filled for REQ-LINT-001..004 and
REQ-SKILL-023 (lint tool v5 mechanics half; the `REQUIRED` rows half closes in
Chunk 5).

### Chunk 1: Return contract — `RETURN:` block, repair packet, `VERDICT:` token
**Goal**: every leaf template ends with the structured `RETURN:` block, fix
re-dispatches carry a fixed-shape `{repair_packet}`, `sdd-review` emits an
own-line `VERDICT:` token, and `references/return-contract.md` holds the
procedure text (parsing, malformed rules, field sources, branching tables,
finding → chunk mapping, pruned-state check). Traces to
`harness-return-contract.md`.
**Depends on**: None.
**Tasks**:
1. [x] [implement] Create `skills/sdd-orchestrate/references/return-contract.md`
   carrying: the `RETURN:` key table with consumers and status semantics; the
   §Malformed Returns rules and the `RETURN: MALFORMED (<reason>)` /
   `RETURN: KEYS MISSING` / `RETURN: MULTIPLE` gate texts; the one-line
   `failures[]` shape; the repair-packet fixed shape and rules (`spec_excerpt` =
   path + heading + line range only; `findings` lifted line-for-line;
   `ledger_summary` one line per attempt; leaf instruction text); the §Field
   Sources table; the `VERDICT:` branching table (parser `^VERDICT:` at line
   start, last occurrence wins); the `RETURN.status` branching table; §Finding →
   Chunk Mapping steps 1–4; the pruned-state slot-set check
   (`DISPATCH: PROMPT EXCEEDS TEMPLATE SLOTS`); the Edge Cases (`MERGE_CONFLICT`
   packet with `conflict_paths` + `base`, `VERIFIER_FAIL` redo packet). —
   traces to `harness-return-contract.md` §RETURN Block, §Malformed Returns,
   §Failures Are One-Line, §Repair Packet, §Finding → Chunk Mapping, §Field
   Sources, §VERDICT Token, §RETURN.status Branching, §Pruned State
   (REQ-HARN-009, -010, -011, -012, -013, -018).
2. [x] [implement] In `references/dispatch-templates.md`: rewrite the PIPELINE
   template's return step 4 to end with the `RETURN:` block (status first on its
   own line, every key listed, `blocked_writes` as the labeled fallback); replace
   the `{on_fix_only}` / `{review_findings}` slot with `{repair_packet}` (fixed
   shape pasted from the spec) in both the template and the slot contract; add the
   leaf instruction "Act on the packet. Do not re-derive the history…". Add the
   grep guard: no template tells the subagent to decide the next stage, classify
   the verdict or judge scope. — traces to `harness-return-contract.md` §RETURN
   Block, §Repair Packet, §Orchestrator Owns Routing (REQ-HARN-009, -011, -019).
3. [x] [implement] In `references/fan-out.md` §2 leaf template: replace return step 4
   ("files written + commits + summary") with the `RETURN:` block (`commits`
   populated, `blocked_writes` for barred plan/traceability writes) and extend
   the slot contract; in §3e read `tasks_completed` / `traceability_fills` from
   the block for plan marks and traceability fills. — traces to
   `harness-return-contract.md` §RETURN Block key table (REQ-HARN-009).
4. [x] [implement] In `skills/sdd-review/SKILL.md` §Step 5 report format: add the
   own-line `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT` token beside the
   `**Verdict:**` line, with the 1:1 prose ↔ token mapping and the rule that they
   must agree; report shape and §Scope Boundaries otherwise unchanged. — traces
   to `harness-return-contract.md` §VERDICT Token (REQ-HARN-013);
   `skill-updates.md` §v5 (REQ-SKILL-021).
5. [x] [implement] In `skills/sdd-implement/SKILL.md`: under the dispatched-leaf
   guidance (next to the "Parallel-dispatch exception" rule) add the leaf return
   contract — when dispatched by `sdd-orchestrate`, end the return with the
   `RETURN:` block (keys as in `return-contract.md`; `failures` one-line,
   ANSI-stripped, ≤ 200 chars; `open_questions` cites Q-IMPL ids). Standalone
   behavior unchanged. — traces to `harness-return-contract.md` §RETURN Block,
   §Failures Are One-Line (REQ-HARN-009, -010); `skill-updates.md` §v5
   (REQ-SKILL-020).
6. [x] [implement] In `skills/sdd-orchestrate/SKILL.md`: §The gate names the three
   `VERDICT:` values and points to the `VERDICT:` and `RETURN.status` branching
   tables in `references/return-contract.md`; the `loop-back-to-fix` row now
   says "re-dispatch with a repair packet (findings + paths by construction)";
   add the `REVIEW: MALFORMED` and `RETURN: MALFORMED` pause rows under §Edge
   cases routed through the gate; §Orchestrator-Only Work gains the routing
   principle (verdict/status/token interpretation, cap arithmetic, packet
   composition, merge/re-dispatch/replan/stop decisions are orchestrator-only)
   with a pointer to `references/return-contract.md` (the `write-scope.md`
   pointer is added by Chunk 4, which creates that file); add a one-paragraph
   stub for `return-contract.md` in §LOOP. — traces to
   `harness-return-contract.md` §VERDICT Token, §Malformed Returns,
   §Orchestrator Owns Routing (REQ-HARN-013, -019); `orchestration.md` §v5.
7. [x] [verify] Fixture walkthrough per `harness-return-contract.md` §Verification:
   compose a two-iteration packet from a fixture `RETURN` (exactly two
   `ledger_summary` lines; rendered `spec_excerpt` matches
   `^docs/spec/[^ ]+\.md § .+ L\d+-\d+$`; no quoted spec text); a return and a
   packet fixture contain no multi-line `message` and no `Traceback`;
   `findings[].text` equals the report line after stripping `- C1: ` and
   ` — [file:section]`; grep all templates for "decide the next stage",
   "classify the verdict", "judge scope" (zero hits); lint exits 0. — traces to
   `harness-return-contract.md` §Verification — Automated (REQ-HARN-010..012,
   -018, -019).
**Entry criteria**: none (root chunk).
**Exit criteria**: both leaf templates and the review template state their return
contract; `references/return-contract.md` exists and `SKILL.md` links to it (link
resolves); lint exits 0; traceability Test/Implementation filled for
REQ-HARN-009..013, -018, -019, REQ-SKILL-021, REQ-SKILL-020 (`RETURN:` half —
task 5; the ledger half closes in Chunk 2).

### Chunk 2: Loop control — caps, budget, attempt ledger, circuit-break checkpoint
**Goal**: the fix loop and the replan re-entry are capped (session counter /
derived from `-replan-` archives), every template carries `Budget:`, budget
exhaustion has a defined return path, `sdd-implement` keeps an attempt ledger with
the oscillation rule and writes a bounded checkpoint into the plan's blocked-task
note that `sdd-replan` reads. Traces to `harness-loop-control.md`.
**Depends on**: Chunk 1.
**Tasks**:
1. [x] [implement] In `skills/sdd-orchestrate/SKILL.md` §The gate: state the
   **fix-loop cap** (`FIX_LOOP_MAX`, default 3, per stage, session-only; every fix
   prompt carries `iteration N of 3`; operator may raise it by one at the gate,
   and a raised cap renders as `iteration N of MAX` with the raise count — e.g.
   `iteration 5 of 5 (cap raised ×2)` — per the spec's Edge Cases);
   the exhaustion behavior (no automatic dispatch; gate shows the compiled
   findings log and offers `stop | manual intervention | authorize extra
   iteration`) with the compiled-log shape pasted from the spec; the **replan
   re-entry cap** (`REPLAN_MAX`, default 3) with the derivation rule — kickoff
   `date:` primary, `git log -1 --format=%cs -S'research_id: <id>' -- <kickoff>`
   legacy fallback, neither → "treated as reached" gate event — and the
   `^(\d{4}-\d{2}-\d{2})-(m\d+-)?replan-.*\.md$` regex; add the loop counters to
   the stage-gate signal list. — traces to `harness-loop-control.md` §State
   Placement, §Fix-Loop Cap, §Replan Re-entry Cap (REQ-HARN-001, -002).
2. [x] [implement] In `SKILL.md` §KICKOFF: make `date:` mandatory in the kickoff
   frontmatter written by orchestrate and add the pre-pipeline self-check for it;
   add the `Budget:` slot self-check (an empty slot is a template violation caught
   before dispatch). — traces to `harness-loop-control.md` §Replan Re-entry Cap
   (`date:` rule), §Budget Slot (REQ-HARN-002, -004).
3. [x] [implement] Budget slot everywhere: add `Budget: {budget}` to the REVIEW
   template in `dispatch-templates.md` (`≤ 15 tool calls, read-only`) and confirm
   the PIPELINE and fan-out leaf templates carry it; document the budget grammar
   (observable units only; `read-only`, `no prototypes` qualifiers) and the
   default-budget-per-dispatch-type table in `references/return-contract.md`
   next to the `RETURN:` key table, with the recorded v1 limitation that
   `budget_consumed` is self-reported. — traces to `harness-loop-control.md`
   §Budget Slot, §Budget Exhaustion (REQ-HARN-004, -005).
4. [x] [implement] In `skills/sdd-implement/SKILL.md` Step 3: add the **attempt
   ledger** (`attempt / hypothesis / change / result`, one line each, newest
   last) and `verified_do_not_touch` with its revert rule; list both
   **oscillation** conditions — (a) regression oscillation, (b) repeated patch
   after whitespace normalization — as stuck triggers under the word
   "oscillation"; state the ledger is context-only (never written to specs,
   kickoff or a new file; not a Q-IMPL entry) and surfaces as `RETURN.ledger`. —
   traces to `harness-loop-control.md` §Attempt Ledger, §Oscillation Rule
   (REQ-HARN-006, -007); `skill-updates.md` §v5 (REQ-SKILL-020).
5. [x] [implement] In `skills/sdd-implement/SKILL.md` Step 3 (stuck path) and the
   leaf return guidance: define the **circuit-break checkpoint** — trigger list,
   slot (blocked-task note under the task), the ≤ ~15-line format pasted from the
   spec, the RETURN-field → checkpoint-line mapping table, who writes it
   (sequential: implementer; fan-out: orchestrator in §3e); define the **budget
   exhaustion** path (stop new work, leave the tree consistent, checkpoint if
   mid-task, `status: BUDGET_EXHAUSTED` + `budget_consumed` in the dispatched
   units). — traces to `harness-loop-control.md` §Budget Exhaustion,
   §Circuit-Break Checkpoint (REQ-HARN-005, -008).
6. [x] [implement] In `skills/sdd-replan/SKILL.md`: Step 1 item 6 reads the
   checkpoint (blocked-task note) as the stuck state in place of "recent
   conversation context"; Step 4 defines the blocked-task note as the checkpoint
   slot and states the `-replan-` filename contract verbatim ("every archive this
   skill writes carries the `-replan-` segment … no other skill may use that
   segment"). In `references/fan-out.md` §3e add checkpoint application by the
   orchestrator for `BLOCKED` / `BUDGET_EXHAUSTED` leaves (nearest-chunk fallback
   with `task not found in plan` prefix). — traces to `harness-loop-control.md`
   §Replan Re-entry Cap (`-replan-` contract), §Circuit-Break Checkpoint, Edge
   Cases (REQ-HARN-003, -008); `skill-updates.md` §v5 (REQ-SKILL-022).
7. [x] [verify] Fixtures per `harness-loop-control.md` §Verification: a temp
   `plan-history/` with `2026-09-01-replan-a.md`, `2026-09-18-replan-b.md`,
   `2026-09-19-m1-replan-c.md`, `2026-09-19-rewrite.md`,
   `2026-09-20-m1-complete.md` + kickoff `date: 2026-09-17` derives count = 2; a
   temp git repo whose kickoff lacks `date:` but whose `research_id:` line was
   last changed by a 2026-09-17 commit derives 2, and one with neither yields
   "treated as reached"; the spec's ledger is stuck by rule (a) and a two-identical-
   `change` ledger by rule (b); the checkpoint composed from the RS-008 Schema 1
   example is ≤ 15 lines with no `Traceback` / `File "…", line N`;
   `grep -n -- '-replan-' skills/sdd-plan/SKILL.md` is empty; lint exits 0. —
   traces to `harness-loop-control.md` §Verification — Automated
   (REQ-HARN-002, -003, -007, -008).
**Entry criteria**: Chunk 1 complete (`return-contract.md` exists; `RETURN:` keys
`ledger`, `budget_consumed`, `failures`, `open_questions` defined).
**Exit criteria**: `SKILL.md` contains the phrases "fix-loop cap", "iteration N
of 3" and "replan re-entry cap"; every template in both reference files carries
`Budget:`; `sdd-implement` contains "oscillation" and "checkpoint";
`sdd-replan` contains "checkpoint" and the `-replan-` contract sentence; lint
exits 0; traceability filled for REQ-HARN-001..008, -027 (invariant table
checked: no new file under `docs/`), REQ-SKILL-020 (ledger half), REQ-SKILL-022.

### Chunk 3: Chunk-close verifier and per-chunk sequential implement
**Goal**: `dispatch-templates.md` carries a read-only CHUNK VERIFIER template
returning `CHUNK_VERDICT: PASS | FAIL`; sequential implement is dispatched per
chunk and closes at a lightweight per-chunk gate (`proceed │ fix │ stop`) with a
per-chunk redo counter; under fan-out the verifier runs per leaf before merge.
Traces to `harness-chunk-verifier.md`.
**Depends on**: Chunk 1.
**Tasks**:
1. [x] [implement] Add §CHUNK VERIFIER to `references/dispatch-templates.md`: the
   template pasted from the spec (non-interactive clause, `Working directory`,
   `Plan … verify Chunk {N} only`, `Specs the chunk's tasks trace to`,
   `Quality gate commands`, `Budget: {budget}`, `Write scope: (empty —
   read-only)`, `Commit ownership: you never commit`, the Check 1 / Check 3 /
   gates task, "do not invoke sdd-review or sdd-implement"), the slot contract
   (`{repo_root_or_worktree_path}`, `{plan_path}` + `{N}`, `{spec_paths}`,
   `{gate_commands}`, `{budget}` — nothing else), the verifier return shape with
   the full leaf key set plus `CHUNK_VERDICT: PASS | FAIL` as the last line, and
   the verdict rule (PASS iff Check 1 has zero blocking findings and every gate
   exits 0; Check 3 advisory). — traces to `harness-chunk-verifier.md`
   §Verifier Dispatch Template, §Verdict Rule (REQ-HARN-014, -017).
2. [x] [implement] In `dispatch-templates.md` §PIPELINE: add the `Chunk N`
   parameter to the implement-stage deliverable contract (one chunk per
   dispatch, plan order) and its slot; note the v2-vocabulary edge case (no
   `### Chunk N:` headers → one dispatch, no verifier). — traces to
   `harness-chunk-verifier.md` §Sequencing — Sequential Mode, Edge Cases
   (REQ-HARN-016).
3. [x] [implement] In `skills/sdd-orchestrate/SKILL.md` §LOOP: add a "Per-chunk
   implement dispatch and per-chunk gate" subsection with the sequential loop
   (snapshot → dispatch Chunk N → parse `RETURN` → scope check → branch on
   `RETURN.status` → verifier → per-chunk gate → commit on `proceed`), the
   per-chunk gate block pasted byte-identically from the spec, the defaults
   (`proceed` on PASS + CLEAN, `fix` on FAIL / VIOLATION, `proceed` on FAIL is a
   recorded override), the **per-chunk redo counter** `chunk_redo_count[<chunk
   header>]` against `REDO_MAX` (default 3; shown as `Redo: N of 3`; increments
   only on `fix`; same exhaustion behavior as the fix-loop cap, compiled from the
   verifier's findings), FAIL routing (repair packet with `reason: VERIFIER_FAIL`
   only — never merge, review or replan directly), the "review runs ONCE after
   all chunks" rule, the **post-review loop-back re-entry rule** — after a
   stage-level `loop-back-to-fix`, each fix dispatch is followed by the scope
   check, one verifier per touched chunk (per `harness-return-contract.md`
   §Finding → Chunk Mapping) and that chunk's per-chunk gate BEFORE the
   re-review (per `harness-chunk-verifier.md` §FAIL Routing) — the verifier
   edge cases (a verifier returning `status: BUDGET_EXHAUSTED` is treated as
   `CHUNK_VERDICT: FAIL` and "verifier re-dispatch is not a redo" — it does not
   increment `chunk_redo_count`; a gate that exits non-zero on the verifier's
   run but zero on the orchestrator's re-run renders the `possible flake` gate
   line), and the `CHUNK_VERDICT:` consumer statement in §The gate
   (per-chunk signal order `RETURN.status` → `SCOPE:` → `CHUNK_VERDICT:`;
   stage gate = review `VERDICT:` + loop counters). — traces to
   `harness-chunk-verifier.md` §Sequencing — Sequential Mode, §FAIL Routing,
   §Ephemerality and Gate Text, Edge Cases; `harness-return-contract.md`
   §Finding → Chunk Mapping; `harness-loop-control.md` §Redo Cap per Chunk;
   `orchestration.md` §v5 gate text order (REQ-HARN-014, -016, REQ-ORCH-034).
4. [x] [implement] In `references/fan-out.md` §3: insert the per-leaf step between
   "await leaf return" and "sequential merge" — (a) parse `RETURN` + scope-check
   placeholder (procedure in Chunk 4), (b) dispatch the verifier with the leaf's
   worktree / branch plan / chunk(s) (skipped on `BLOCKED` /
   `BUDGET_EXHAUSTED`), (c) the per-leaf gate (same block; no orchestrator
   commit; `fix` → redo on the same branch, no merge); only `proceed` branches
   enter §3b merge order; one verifier per chunk for multi-chunk leaves; add the
   verifier-before-merge line to §4 invariants. Add the verifier default-on /
   opt-out choice to the fan-out opt-in gate text in `SKILL.md` §Opt-in gate. —
   traces to `harness-chunk-verifier.md` §Sequencing — Fan-out, Open Questions
   #1 (REQ-HARN-015).
5. [x] [verify] Per `harness-chunk-verifier.md` §Verification: grep the verifier
   template for `sdd-review` and `Skill tool` (zero hits); walk a fixture
   verifier return with `check1: fail` → FAIL and one with `check1: pass`,
   `check3: advisory`, all gates 0 → PASS; on a two-chunk fixture plan trace the
   sequential procedure by hand and count 2 implement + 2 verifier + 1 review
   dispatches and 2 per-chunk gates; diff the four-layer table in
   `skills/sdd-review/SKILL.md` against `adb73e3` (unchanged); lint exits 0. —
   traces to `harness-chunk-verifier.md` §Verification — Automated
   (REQ-HARN-014..017).
**Entry criteria**: Chunk 1 complete (`RETURN:` key set and `RETURN.status`
branching table exist for the verifier to reference).
**Exit criteria**: `dispatch-templates.md` contains `CHUNK_VERDICT: PASS | FAIL`
and the verifier template carries `Budget:` and `Write scope:`; `SKILL.md`
contains `CHUNK_VERDICT:`; the per-chunk gate block in `SKILL.md` is byte-
identical to the spec's; lint exits 0; traceability filled for REQ-HARN-014..017.

### Chunk 4: Write scope — declared slot, three-command check, `SCOPE:` gate text
**Goal**: every leaf template declares `Write scope:`, the orchestrator observes
writes with the porcelain ∪ committed-delta ∪ ancestry procedure and surfaces
`SCOPE: CLEAN | VIOLATION (N paths)` before any commit or merge; commit ownership
and snapshot ordering are pinned per dispatch type; `blocked_writes` are
scope-matched before persistence. Traces to `harness-write-scope.md`.
**Depends on**: Chunk 1, Chunk 3.
**Tasks**:
1. [x] [implement] Create `skills/sdd-orchestrate/references/write-scope.md`
   carrying: the slot semantics (glob rules; `(empty — read-only)` for review
   and verifier; operator widening at the gate, session-only); the default scope
   table (all rows incl. ADVISORY markers, the fan-out-leaf bar on plan /
   traceability / spec writes, and the derivation of "the chunk's source/test
   paths" with the declared-roots fallback); the three commands with the
   fan-out `<base>` / branch-tip substitution; the `IN` / `ADVISORY` / `OUT`
   tags with hints; the finding format and `SCOPE:` token; revert targets
   (working tree vs leaf branch); the blocked-write pre-persist match; the
   commit-ownership table; the per-chunk gate block pasted byte-identically;
   snapshot ordering (both modes) beside the three commands; the two recorded v1
   limitations; marker-4 rooting. — traces to `harness-write-scope.md`
   §Declared Write Scope Slot, §Default Scope Table, §Observation,
   §Matching and Tags, §Finding Format, §Blocked-Write Fallback, §Commit
   Ownership, §Snapshot Ordering, §Recorded v1 Limitations, §Marker-4 Rooting
   (REQ-HARN-020..026).
2. [x] [implement] In `references/dispatch-templates.md`: add `Write scope:
   {write_scope}` to the PIPELINE template and `Write scope: (empty —
   read-only)` to the REVIEW template, with slot-contract entries; make each
   template's return step state its commit-ownership row (pipeline: "you are not
   instructed to commit — the orchestrator commits on `proceed`"; review:
   nobody commits). — traces to `harness-write-scope.md` §Declared Write Scope
   Slot, §Commit Ownership (REQ-HARN-020, -024).
3. [x] [implement] In `references/fan-out.md`: add `Write scope: {write_scope}`
   (the chunk-group's code and test paths only) to the §2 leaf template and slot
   contract; state the leaf's commit-ownership row (leaf commits on its branch
   with inline identity; the orchestrator merges on `proceed`); replace the
   scope-check placeholder from Chunk 3 step (a) with the worktree-rooted three
   commands and `SCOPE:` token; in §3e add the `blocked_writes` pre-persist
   scope match and the rule that leaf deviations arrive in
   `RETURN.open_questions` and the orchestrator files the Q-IMPL entry at merge.
   — traces to `harness-write-scope.md` §Default Scope Table (fan-out-leaf
   row), §Observation, §Blocked-Write Fallback, §Commit Ownership
   (REQ-HARN-020, -021, -023, -024).
4. [x] [implement] In `skills/sdd-orchestrate/SKILL.md`: add the `write-scope.md`
   stub in §LOOP (snapshot(before) immediately before dispatch, snapshot(after)
   immediately on return, scope check before verifier / gate / commit); §The
   gate references the `SCOPE:` token as signal (2) with the `revert path |
   accept & widen scope | stop` options resolved inside the per-chunk gate
   (`proceed` unavailable while an `OUT` path is unresolved); §Orchestrator-Only
   Work gains the `references/write-scope.md` pointer for `SCOPE:` branching;
   §Isolation Discipline gains the `HISTORY_REWRITE` rule (no automatic reset).
   — traces to `harness-write-scope.md` §Finding Format and `SCOPE:` Token,
   §Snapshot Ordering; `harness-return-contract.md` §Orchestrator Owns Routing
   (REQ-HARN-019, -022, -025); `orchestration.md` §v5.
5. [x] [verify] Fixtures per `harness-write-scope.md` §Verification, run in a temp
   git repo with the three commands: before `?? .claude/worktrees/`, after adds
   ` M docs/plan.md`, committed delta empty, scope `src/**` → one `OUT
   docs/plan.md uncommitted`, `SCOPE: VIOLATION (1 path)`; clean porcelain with
   committed `M docs/plan.md`, scope `docs/spec/**` → `OUT … committed`,
   `VIOLATION (1 path)`; verify dispatch writing `docs/verification.md` +
   `docs/requirements/traceability.md` → both `IN`, `CLEAN`; implement writing
   `docs/spec/recon.md` → `ADVISORY`, `CLEAN`; `blocked_writes: [{path:
   docs/plan.md}]` from a leaf → refused, listed `OUT … refused`; a rewritten
   `HEAD_after` → `HISTORY_REWRITE`, `VIOLATION`; lint exits 0. — traces to
   `harness-write-scope.md` §Verification — Automated (REQ-HARN-021..023, -026).
**Entry criteria**: Chunk 1 complete (`files_written`, `commits`,
`blocked_writes` keys defined; §Orchestrator-Only Work principle present to
extend); Chunk 3 complete (the `fan-out.md` §3 scope-check placeholder from
its task 4 step (a) exists for task 3 to replace; the per-chunk gate block is
in `SKILL.md` for task 4 to reference).
**Exit criteria**: `Write scope:` appears in the pipeline and review templates
and the fan-out leaf template; `references/write-scope.md` exists and the
`SKILL.md` stub link resolves; per-chunk gate block byte-identical to the spec;
lint exits 0; traceability filled for REQ-HARN-020..026.

### Chunk 5: Lint `REQUIRED` rows + `SKILL.md` slimming (marker-4 prose move)
**Goal**: the 18 new `REQUIRED` rows enforce every marker Chunks 1–4 introduced;
`sdd-orchestrate/SKILL.md` sheds its marker-4-only prose to
`references/v4-workstreams.md` behind stubs and reads at ≤ ~450 lines; the
integrated skill set passes the lint with size warnings only. Traces to
`skill-lint-v5.md`, `orchestration.md` §v5.
**Depends on**: Chunk 0, Chunk 2, Chunk 3, Chunk 4.
**Tasks**:
1. [x] [implement] Add the nine core `REQUIRED` rows to `tools/sdd-skill-lint.py`
   (a: `fix[- ]loop cap|iteration N of 3`; b: `replan re-entry cap`; c1/c2:
   `Budget:` ≥ 3 in `dispatch-templates.md`, ≥ 1 in `fan-out.md`; d1/d2:
   `VERDICT: APPROVE \| APPROVE_WITH_FIXES \| REJECT` in `sdd-review`,
   `(?<!CHUNK_)VERDICT:` in `sdd-orchestrate/SKILL.md`; e1/e2:
   `CHUNK_VERDICT: PASS \| FAIL` in `dispatch-templates.md`, `CHUNK_VERDICT:` in
   `SKILL.md`; f: `-replan-` in `sdd-replan`), each with `reason` and a `fix`
   string that names the counterpart file for the d/e pairs. — traces to
   `skill-lint-v5.md` §`REQUIRED` Rows — Core Contracts (REQ-LINT-005).
2. [x] [implement] Add the nine remaining rows (`RETURN:` ≥ 2 / ≥ 1; `status:
   COMPLETE \| PARTIAL \| BLOCKED \| BUDGET_EXHAUSTED`; `\{repair_packet\}` ≥ 2;
   `Write scope:` ≥ 3 / ≥ 1; `oscillation`; `checkpoint` in `sdd-implement` and
   `sdd-replan`) with `fix` strings; extend `self_test()` so each new row fails
   when its marker is removed from a temp copy. — traces to `skill-lint-v5.md`
   §`REQUIRED` Rows — Remaining Contracts, §Self-Test Extension (REQ-LINT-006).
3. [x] [implement] Create `skills/sdd-orchestrate/references/v4-workstreams.md` and
   move into it: §Workstream Picker + its three subsections; §Phase Detection
   "Workstream & version gate (v4)" and "Marker-4 gate for done-vs-new-cycle";
   the §Entry Points "Marker-4 scope" paragraph; §KICKOFF "Kickoff path —
   version gate"; §Integration anchor "Marker-4 anchor" paragraph (pointing at
   `references/fan-out.md` §0). Leave each section a stub that keeps the
   "behavior UNCHANGED under marker 3" sentence and a resolving link; the picker
   stub keeps a `research_id` mention (guard 1 — `research_id` ≥ 3 stays
   satisfied in `SKILL.md`); `docs/.sdd-version` stays mentioned. Do NOT move
   the upgrade offer, phase table, §The gate, dispatch contracts, §Isolation
   Discipline, §Rules, §Orchestrator-Only Work. — traces to `skill-lint-v5.md`
   §Marker-4 Prose Move (REQ-LINT-007); `skill-updates.md` §v5 (REQ-SKILL-024).
4. [x] [implement] Append a new Q-IMPL entry (Tier 1) to `docs/spec/ws-orchestration.md`
   §Implementation Questions — "Picker prose lives in
   `references/v4-workstreams.md`; gate and stub remain in `SKILL.md`;
   supersedes Q-IMPL-016's container statement" — and mark Q-IMPL-016
   `[superseded by Q-IMPL-NNN]` per `deviation-protocol.md` §Numbering; never
   edit Q-IMPL-016's body. — traces to `skill-lint-v5.md` §Marker-4 Prose Move
   guard 2 (REQ-LINT-007).
5. [x] [implement] Integration pass over `skills/sdd-orchestrate/SKILL.md` after the
   Chunk 2/3/4 merges: §The gate lists the REQ-ORCH-034 signal order once
   (per-chunk: `RETURN.status` + `budget_consumed` vs `Budget:` → `SCOPE:` →
   `CHUNK_VERDICT:` + `Redo: N of 3`; stage: review `VERDICT:` → `iteration N of
   MAX` / replan count) with pointers only; the two per-chunk-gate copies are
   collapsed to one canonical block; duplicated stub text is deduplicated; the
   fan-out `Depends on` parser, `research_id` contract and `VERSION_GATED_SKILLS`
   mention are intact; `wc -l` ≤ ~450. — traces to `orchestration.md` §v5
   (REQ-ORCH-034); `skill-lint-v5.md` §Marker-4 Prose Move size target
   (REQ-LINT-007); `skill-updates.md` §v5 (REQ-SKILL-019).
6. [x] [verify] `python3 tools/sdd-skill-lint.py --self-test` exits 0; the live lint
   exits 0 printing `OK: 17 file(s) clean, K warning(s)` (16 before task 7's `loop-control.md`) — 13 baseline files +
   the 3 new `references/` files (`return-contract.md`, `write-scope.md`,
   `v4-workstreams.md`), since the tool enumerates `skills/**/*.md` via
   `rglob` — with `K` ≥ 1 only from size warnings (17 files after task 7 adds `loop-control.md`); mutation test — for each of the nine core rows delete the
   marker in a temp copy → exit 1 with that row's `fix:` printed; `grep -c '"fix"'`
   equals the number of rule rows; `wc -l skills/sdd-orchestrate/SKILL.md` ≤ ~450;
   every moved section's stub contains "UNCHANGED" and a resolving link;
   `ws-orchestration.md` has the new Q-IMPL citing Q-IMPL-016; `git ls-files
   docs/` shows no new file type beyond `plan-history/` archives. — traces to
   `skill-lint-v5.md` §Verification — Automated / Manual (REQ-LINT-005..007);
   `harness-loop-control.md` §No-New-Artifact Invariant (REQ-HARN-027).
7. [x] [implement] (added by minor replan 2026-09-17; done — SKILL.md 469 lines, 17 files clean — size-target trigger fired at
   720 lines) Create `skills/sdd-orchestrate/references/loop-control.md` and move
   into it the loop-control procedure prose that no reference holds: the fix-loop
   cap detail and exhaustion compiled-log shape, the replan re-entry cap
   derivation block and its bullets, the per-chunk redo/edge-case bullets, and
   any remaining fan-out lifecycle prose duplicated in `fan-out.md`. Leave stubs
   in `SKILL.md` that keep every lint `REQUIRED` marker literal (`fix-loop cap`,
   `iteration N of 3`, `replan re-entry cap`, `CHUNK_VERDICT:`,
   `(?<!CHUNK_)VERDICT:`, `research_id`, `docs/.sdd-version`, the canonical
   per-chunk gate block byte-identical to the spec) and a resolving link. Target
   `wc -l` ≤ ~450; lint + self-test exit 0; the lint file count becomes 17. —
   traces to `skill-lint-v5.md` §Marker-4 Prose Move size target (REQ-LINT-007);
   `harness-loop-control.md` §Procedure placement (REQ-HARN-001, -002).
**Entry criteria**: Chunks 0, 2, 3, 4 complete and merged into one tree (all
markers present; lint v5 mechanics present).
**Exit criteria**: lint exits 0 reporting 17 file(s) clean (16 + `loop-control.md` from task 7) with size warnings only (three: sdd-orchestrate 469, sdd-migrate 464, sdd-implement 525 — the last accepted via Q-IMPL-083); all 18 new rows present and mutation-tested; `SKILL.md` ≤ ~450 lines;
`v4-workstreams.md` exists with both guards satisfied; traceability filled for
REQ-LINT-005..007, REQ-SKILL-019, REQ-SKILL-023 (`REQUIRED` rows half),
REQ-SKILL-024 (move half).

### Chunk 6: Documentation, traceability closure, holistic verify
**Goal**: operators can read the new gate signals in `USAGE.md` and `CLAUDE.md`;
every HARN / LINT / ORCH-034 / SKILL-019..024 traceability row is filled; the
whole cycle is walked end-to-end on fixtures. Traces to `skill-updates.md` §v5,
`orchestration.md` §v5, `overview.md` §v5.
**Depends on**: Chunk 5.
**Tasks**:
1. [x] [implement] `CLAUDE.md` §Driver (`sdd-orchestrate`): add one short paragraph
   on the v5 gate vocabulary — the per-chunk gate (`proceed │ fix │ stop`) with
   its `RETURN.status` / `SCOPE:` / `CHUNK_VERDICT:` signals, the stage gate
   (`proceed │ loop-back-to-fix │ stop`) with the review `VERDICT:` and the caps
   (`FIX_LOOP_MAX`, `REPLAN_MAX`, `REDO_MAX`, default 3), and the no-new-artifact
   invariant. The "Four verification layers" bullet stays byte-unchanged. —
   traces to `skill-updates.md` §v5 (REQ-SKILL-024); `harness-chunk-verifier.md`
   §Positioning (REQ-HARN-014).
2. [x] [implement] `skills/sdd-orchestrate/USAGE.md`: add a §"Gate signals and caps
   (v5)" operator guide — what the per-chunk gate block shows and how to read
   `SCOPE: VIOLATION` options, `CHUNK_VERDICT: FAIL` → `fix`, `iteration N of 3`
   and the compiled findings log, `Redo: N of 3`, the replan re-entry cap
   message, `RETURN: MALFORMED` / `REVIEW: MALFORMED` pauses, budget exhaustion
   and where the checkpoint appears; update §8 (fan-out) for verifier-before-
   merge and the verifier opt-out; update the abridged exchange in §3 to show one
   per-chunk gate. — traces to `skill-updates.md` §v5 (REQ-SKILL-024);
   `orchestration.md` §User Documentation, §v5 (REQ-ORCH-034).
3. [x] [implement] Traceability sweep: fill any still-empty Test / Implementation
   cells for REQ-HARN-001..027, REQ-LINT-001..007, REQ-ORCH-034 and
   REQ-SKILL-019..024 in `docs/requirements/traceability.md` (Verified column
   stays for `sdd-verify`); confirm `docs/spec/overview.md` §v5 needs no edit
   (it already names `return-contract.md`, `write-scope.md`,
   `v4-workstreams.md`) — edit only if a shipped filename differs. — traces to
   `skill-updates.md` §Shared Changes (traceability) ; `overview.md` §v5
   Harness Hardening.
4. [x] [verify] Holistic fixture walkthrough across the five specs' Manual sections
   without a live dispatch: on a throwaway two-chunk fixture repo, instantiate the
   PIPELINE (Chunk 1), CHUNK VERIFIER and REVIEW templates verbatim with filled
   `Budget:` / `Write scope:` / `Chunk N` slots and confirm no empty slot and no
   content outside the slot set; compose a fix prompt from a forced `REJECT`
   review and confirm one `Repair packet` header, no fenced report, no quoted
   spec text, then trace the loop-back re-entry by hand — fix dispatch → scope
   check → one verifier for the touched chunk → that chunk's per-chunk gate →
   re-review — confirming the re-review is never dispatched before the per-chunk
   gate; confirm the per-chunk gate block rendered from the fixture matches
   the canonical text; render the stage gate from the fixture review (`VERDICT:`
   token + `iteration N of MAX`) and confirm it shows the REQ-ORCH-034 stage
   signal order alongside the per-chunk block; run the three-command scope
   check around a simulated leaf edit; `git ls-files docs/` shows no counter /
   log / review file. —
   traces to `harness-return-contract.md`, `harness-loop-control.md`,
   `harness-chunk-verifier.md`, `harness-write-scope.md` §Verification — Manual;
   `orchestration.md` §v5 (REQ-HARN-001, -011, -016, -018, -020, -027,
   REQ-ORCH-034).
5. [x] [verify] Cross-skill consistency sweep: every reference to a token, cap
   constant, key name or gate option across `SKILL.md`, the four `references/`
   files, `sdd-implement`, `sdd-review`, `sdd-replan`, `USAGE.md` and `CLAUDE.md`
   uses the spec's spelling (`FIX_LOOP_MAX`, `REDO_MAX`, `REPLAN_MAX`,
   `chunk_redo_count`, `RETURN:`, `CHUNK_VERDICT:`, `SCOPE:`, `VERDICT:`,
   `proceed │ fix │ stop`); the four-layer table in `sdd-review` and `CLAUDE.md`
   diffs clean against `adb73e3`; standalone `sdd-implement` Step 4 diffs clean
   against `adb73e3`; lint exits 0 with size warnings only (three: sdd-orchestrate 469, sdd-migrate 464, sdd-implement 525 — the last accepted via Q-IMPL-083). — traces to `harness-chunk-verifier.md`
   §Positioning, §Verification (REQ-HARN-014); `skill-updates.md` §v5.
**Entry criteria**: Chunk 5 complete (integrated, lint-clean skill set).
**Exit criteria**: `CLAUDE.md` and `USAGE.md` updated; no empty Test /
Implementation cell for the cycle's REQ ids; both verify tasks pass with no
acceptance criterion failed; plan `status: complete`; ready for `sdd-verify`.

## Replan Triggers

- **Fired 2026-09-17 (Chunk 5, minor replan, inline)**: SKILL.md 720 lines vs ≤ ~450 — resolved by adding Chunk 5 task 7 (`references/loop-control.md`). No archive (minor, in-place).

- **Per-chunk dispatch cost too high (RS-008 dogfooding probe 1, Q2).** If the
  first real orchestrated implement stage shows per-chunk dispatch + verifier
  adding more than roughly one extra dispatch-equivalent per chunk over a single
  dispatch, or the operator finds the per-chunk gates intolerable → flip the
  verifier default to opt-in at the fan-out opt-in gate and revisit
  `harness-chunk-verifier.md` Open Question 1 (Chunk 3 / Chunk 6 docs).
- **Write-scope false-positive rate (RS-008 dogfooding probe 2, Q5).** If a
  real pipeline dispatch with the default table yields recurring `OUT` findings
  on legitimate side-writes (noise), → widen the default table in
  `references/write-scope.md` and fold the widenings back into
  `harness-write-scope.md` §Default Scope Table (Chunk 4); if the spec-file
  `ADVISORY` case proves noisy, revisit REQ-HARN-026.
- **`SKILL.md` cannot reach ≤ ~450 lines without breaking a lint `REQUIRED`
  row** (e.g. the `research_id` ≥ 3 row or the `(?<!CHUNK_)VERDICT:` consumer
  row) → apply guard 1 option b (split `research_id` into `SKILL.md` ≥ 2 +
  `v4-workstreams.md` ≥ 1) or move further stub-able sections; if the file
  cannot get below `SIZE_FAIL_LINES` (1000) the size contract itself needs
  replanning (Chunk 5).
- **Backtick path resolution flags legitimate prose** (globs, `docs/spec/`
  mentions in a consumer repo, paths inside inline tables) beyond the spec's edge
  cases → retune the regex / severity in Chunk 0 and record the change in
  `skill-lint-v5.md` Edge Cases.
- **Parallel Chunks 2/3 conflict in `dispatch-templates.md` or `SKILL.md`
  §The gate beyond what fan-out's redo-by-re-derivation resolves** → collapse
  wave 2 to sequential order 2 → 3 (Chunk 4 already follows Chunk 3;
  plan-level change, no spec change).
- **The `RETURN:` block proves too large for a leaf to emit reliably** (keys
  omitted in practice, multi-line values) → revisit the key set with
  `harness-return-contract.md` §RETURN Block's rename clause (markers and
  load-bearing decisions survive); Chunk 1 rework.
- **Operator prefers one shared per-stage counter over the per-chunk redo
  counter** (`harness-loop-control.md` Open Question 1) → collapse
  `chunk_redo_count` into the stage fix counter (Chunk 3 text; minor replan).

## Completed

- Multi-Workstream SDD (v4), Chunks 0–8: workstream-aware phase detection,
  ws-prefixed IDs + merge-safe writes, per-ws traceability, workstream-scoped
  staleness, branch-per-workstream integration, v3→v4 migration, workstream
  picker, convention docs and holistic verification (verified 2026-07-23, 9
  chunks, 42 tasks; archived to
  `plan-history/2026-09-17-pre-harness-hardening-rewrite.md`).

## Risks

- **Overlapping edit surfaces across parallel chunks.** Chunks 2 and 3 (wave 2)
  both touch `dispatch-templates.md`, `fan-out.md` and `SKILL.md` §The gate /
  §LOOP; Chunk 4 touches the same files but runs after Chunk 3 (declared
  dependency — it replaces Chunk 3's scope-check placeholder), so it only has
  to merge onto an integrated wave-2 tree. Mitigation: each chunk's tasks name
  distinct sections (Chunk 2: caps + KICKOFF + REVIEW `Budget:`; Chunk 3:
  verifier template + per-chunk subsection; Chunk 4: `Write scope:` lines +
  stub); Chunk 5 task 5 is the explicit integration pass; the replan trigger
  above collapses wave 2 to sequential if merges churn.
- **Lint row ordering.** Adding a `REQUIRED` row before its marker exists breaks
  `exit 0` for every intermediate tree and every parallel worktree. Mitigation:
  rows land only in Chunk 5 after Chunks 1–4 merge; Chunk 0 ships mechanics +
  self-test fixtures only.
- **Byte-identical per-chunk gate block in three places.** Paraphrase in any
  copy violates the XSPEC consistency claim. Mitigation: paste from the spec;
  Chunk 5 task 5 collapses `SKILL.md` to one canonical copy; Chunk 6 task 5
  diffs the copies.
- **Meta-feature testability.** No compiled code exercises the orchestrator
  procedures; verification is fixture walkthroughs plus the lint. Mitigation:
  verify tasks are behavioral (temp git repos for scope and replan-count
  fixtures, mutation tests for lint rows); the two live-dispatch probes are
  explicit replan triggers for the `sdd-verify` stage rather than pretended here.
- **Size target vs completeness.** Moving marker-4 prose out and adding HARN
  stubs may still leave `SKILL.md` above ~450. Mitigation: the target is a
  warn, not a fail; the replan trigger names the fallback.
- **Q-IMPL append in a shared spec file.** `ws-orchestration.md` is a shared
  corpus file; the append is the one spec write this cycle makes. Mitigation:
  append-only per `deviation-protocol.md`; `ADVISORY` under the write-scope
  table, so it is expected gate text, not a violation.

## Open Questions / Assumptions

- **Status `Approved` by instruction.** This plan was authored by a
  non-interactive pipeline subagent; the dispatch set `status: Approved` and
  `last_updated: 2026-09-17`. The orchestration gate remains the operator's
  point of sign-off before `sdd-implement`.
- **Single-milestone structure.** Seven chunks, one delivery (the lint rows and
  the skill text must ship together for `exit 0`), so a single `docs/plan.md`
  is used despite exceeding ~300 lines. Default: keep single-milestone.
- **Lint tests live in `--self-test`, not a pytest file.** `skill-lint-v5.md`
  §Self-Test Extension specifies fixtures inside the script's self-test;
  `CLAUDE.md` asks tools to stay self-contained. Default: no `tools/tests/`
  directory; temp-dir fixtures built inside `self_test()`.
- **`REQUIRED` rows deferred to Chunk 5.** The spec lists the rows under the
  lint but they are only satisfiable once Chunks 1–4 land. Default: Chunk 0 =
  mechanics, Chunk 5 = rows; if the operator wants earlier row scaffolding, add
  them commented-out in Chunk 0 (no behavior change).
- **Verifier template location.** `skill-lint-v5.md` Open Question 1: the
  verifier template goes into `dispatch-templates.md` (so `Budget:` ≥ 3 and
  `Write scope:` ≥ 3 hold there), not a separate file. Default: as stated.
- **Checkpoint marker word.** Default: the literal word `checkpoint`
  (`skill-lint-v5.md` Open Question 2); "circuit-break checkpoint" may be used
  as the heading as long as the bare word appears in both `sdd-implement` and
  `sdd-replan`.
- **Verifier default-on.** `harness-chunk-verifier.md` Open Question 1 default
  adopted (on under orchestrate; opt-out at the fan-out opt-in gate, gate text
  only). Revisited by the dogfooding replan trigger.
- **Redo counter granularity.** `harness-loop-control.md` Open Question 1
  default adopted: separate `chunk_redo_count[<chunk header>]` with
  `REDO_MAX = 3`, defined in Chunk 3 alongside the per-chunk gate; the fix-loop
  and replan caps stay in Chunk 2.
- **`overview.md` untouched.** Its §v5 section already names the three new
  `references/` files; Chunk 6 task 3 edits it only if a shipped filename
  differs.
- **Repo stays at marker `3`.** Every marker-4 rooting rule is written as text;
  no `docs/ws/` fixture is exercised in this cycle beyond the temp repos in the
  verify tasks.
