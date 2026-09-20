---
workstream: harness-p6
status: planned
research_id: RS-HARNESSP6-001
last_updated: 2026-09-20
---

# Implementation Plan: Harness hardening, part 6 (terminal)

## Overview

Nine scope items from `docs/ws/harness-p6/kickoff.md`, delivered against six
Approved specs and thirteen `REQ-*-HARNESSP6-*` requirements. The order is the
kickoff's §Scope order, so a `stop` partway leaves the two `tools/sdd-gc.py`
rules landed first: the closed-workstream `[stale-chain]` skip, then the
shared-spec fold and its `info` demotion, then git-state observation in the
write-scope snapshot, the lint `REQUIRED` rows that guard the new and the
previously unguarded gate tokens, the Q-IMPL fence-symmetry fix, the two carried
requirements/plan text fixes, the §Out of Scope deferral sweep, and finally
**L2** — the cross-layer convergence signal — which is sequenced last among the
implementation items because it is the item most likely to trigger a replan and
the other eight should be landed before that risk is taken (kickoff §Decided at
DISCUSS). L2's spec section is `[high-uncertainty]`, so it opens with a
mandatory in-cycle spike whose result steers its implement tasks.

**This cycle is terminal.** No task, note, risk or replan trigger here is
phrased as deferred, carried or queued to a next or later cycle. An item too
large to complete triggers a **replan inside this cycle**; a descope is recorded
as a settled exclusion with its reasoning in `docs/requirements/index.md`
§Out of Scope, never as a successor workstream.

**Acceptance discipline (binding on every task below).** No task acceptance
pins a corpus-measured count as a literal. The kickoff's "44 of 63 warnings /
three pairs" and the specs' "19 lines" are **dated branch-point measurements**
and are already stale. Every criterion that involves a corpus count derives
**both sides at run time** from the same command run, or compares against a
baseline captured at that task's own start. Six false acceptance criteria
shipped this way in harness-p5 and two more were caught in this cycle's earlier
stages; it is the single most repeated defect in this corpus.

## Conventions

- **Task types**: [implement] produces code or contract text, [spike] produces
  findings and may trigger a replan, [verify] validates behaviour.
- **Chunk headers**: `### Chunk N: <name>` per work unit; every chunk carries a
  `**Depends on**:` field, which is the canonical dependency signal.
- **Exit criteria on every chunk include**: `python3 tools/sdd-skill-lint.py`
  exits 0 and `python3 tools/sdd-gc.py --self-test` exits 0 where the chunk
  touched gc. A chunk never closes with a red tool.
- Marker-3 behaviour is unchanged by every chunk; no chunk adds a durable
  artifact type under `docs/`; the four-layer verification table stays
  byte-unchanged in `CLAUDE.md` and in every spec that restates it.

## Chunks

### Chunk 1: `[stale-chain]` skips a closed workstream — scope item 1

**Goal**: `tools/sdd-gc.py` stops emitting plan-level `[stale-chain]` findings
for workstreams whose `verification.md` is `status: pass`, so the repo's warning
count stops growing monotonically with every closed cycle.
**Depends on**: None.
**Tasks**:
1. [x] [implement] Add the closed-workstream predicate to `sweep_stale()`: a
   workstream is closed when `docs/ws/<id>/verification.md` exists and its
   frontmatter `status:` is exactly `pass`; both plan-level sub-kinds (plan
   older than a traced spec, plan older than a traced requirement category
   file) are skipped together. No new rule id, no severity change, no
   allowlist, no file exempted by name; the predicate is evaluated per
   workstream, never per file, and is never consulted under marker `3` —
   traces to `docs/spec/drift-sweep.md` §Closed-Workstream Skip.
2. [x] [implement] Add the self-test case `test_stale_chain_skips_closed_workstream`:
   a fixture workstream at `status: pass` raises neither plan-level sub-kind;
   the same plan under `status: fail`, under `status: pending-red`, and with no
   `verification.md` at all raises both as before — traces to
   `docs/spec/drift-sweep.md` §Verification → Automated.
3. [x] [verify] Run `python3 tools/sdd-gc.py --report` and assert **zero**
   `[stale-chain]` findings whose location is under `docs/ws/harness-p3/` or
   `docs/ws/harness-p4/`, both of which are `status: pass` at run time (confirm
   that status from the file in the same run rather than assuming it); assert
   that at least one open workstream's plan-level findings, if any exist in
   that run, are still emitted — traces to `docs/spec/drift-sweep.md`
   §Acceptance Criteria (REQ-GC-HARNESSP6-001).

**Entry criteria**: None (first chunk).
**Exit criteria**: `--self-test` exits 0; `--report` exits `OK`; no
`[stale-chain]` line located in a closed workstream's plan; marker-3 code path
provably untouched (the predicate is guarded by the presence of `docs/ws/`).

### Chunk 2: shared-spec staleness folds and demotes to `info` — scope item 2

**Goal**: the spec-versus-requirement `[stale-chain]` comparison emits one
finding per `(spec, category file)` pair at `info`, and its DONE routing moves
with its severity.
**Depends on**: Chunk 1.
**Tasks**:
1. [x] [implement] Fold the fan-out: `_stale` gains a grouping accumulator and
   `sweep_stale()` emits once per `(downstream spec, upstream category file)`
   pair after the id loop, the message naming every triggering requirement id.
   Every `(spec, id)` pair is still evaluated — the fold is a presentation
   change with provably zero false-negative cost — traces to
   `docs/spec/drift-sweep.md` §Shared-Spec Staleness: Fold and Severity
   (REQ-GC-HARNESSP6-002).
2. [x] [implement] Demote the folded finding to `info` via a severity argument on
   the spec←requirement call site; plan-level `[stale-chain]` findings keep
   `warn`. Update §Sweep Table row 7 and the self-test fixture's
   `ewarn["stale-chain"]` expectations, which count per line today — traces to
   `docs/spec/drift-sweep.md` §Shared-Spec Staleness (REQ-GC-HARNESSP6-003).
3. [x] [implement] Move the routing with the severity: §Routing at DONE lists only
   the **plan-level** sub-class under `record | ignore`; the folded shared-spec
   class is informational and routes nowhere, so nothing can append it to
   `verification.md` §Next Steps — traces to `docs/spec/drift-sweep.md`
   §Routing at DONE and Q-REQ-P6-E (REQ-GC-HARNESSP6-003).
4. [x] [implement] Add `test_shared_spec_staleness_folds` and
   `test_shared_spec_staleness_severity` — traces to
   `docs/spec/drift-sweep.md` §Verification → Automated.
5. [x] [verify] From a **single** `--report` run, derive both sides and assert they
   are equal: the number of spec-versus-requirement `[stale-chain]` findings,
   and the number of distinct `(spec, category file)` pairs those same findings
   name. Neither side is a literal; the pair set grows whenever any workstream
   re-dates a category file — traces to `docs/spec/drift-sweep.md` §Acceptance
   Criteria (REQ-GC-HARNESSP6-002).
6. [x] [verify] From the same run, assert `--report` exits `OK` with **0**
   `[stale-chain]` **warnings** and that every remaining spec-versus-requirement
   `[stale-chain]` line is `info`. The number of `info` lines is a property of
   the corpus at run time and is deliberately not pinned. This check is
   scheduled **after** Chunk 1 by the spec's §Ordering clause: the plan-level
   lines are `warn` and stay `warn`, so the zero-warnings condition cannot hold
   until the closed-workstream skip has landed — traces to
   `docs/spec/drift-sweep.md` §Ordering (REQ-GC-HARNESSP6-001 +
   REQ-GC-HARNESSP6-003 together).

**Entry criteria**: Chunk 1 complete and its verify task passing.
**Exit criteria**: `--self-test` exits 0; the fold-equality assertion holds on a
run-time-derived pair count; zero `[stale-chain]` warnings; §Sweep Table row 7
and §Routing at DONE both state the split and offer the shared-spec sub-class no
`record` option.

### Chunk 3: git-state observation in the write-scope snapshot — scope item 3

**Goal**: a read-only leaf that mutates git state (the harness-p5 `git stash`
incident) is observed, instead of rendering `SCOPE: CLEAN`.
**Depends on**: None (independent of Chunks 1–2; may be worked in parallel with
them).
**Tasks**:
1. [x] [implement] `skills/sdd-orchestrate/references/write-scope.md` §3: state the
   three extra plumbing reads taken inside the **existing**
   `snapshot(before)` / `snapshot(after)` window — `git stash list | wc -l`,
   `git rev-parse --abbrev-ref HEAD`, `git rev-parse --verify --quiet ORIG_HEAD`
   (absence is the legal empty value, absent-in-both compares equal) — and the
   reverse-porcelain-delta subtraction. No second observation window is
   introduced — traces to `docs/spec/harness-write-scope.md` §Git-State
   Observation (REQ-HARN-HARNESSP6-001).
2. [x] [implement] State the comparand's two clauses: (i) state drift in stash
   count, branch or `ORIG_HEAD`; (ii) the set of paths dirty in `before` and not
   dirty in `after`, **minus** the committed delta, being non-empty — traces to
   `docs/spec/harness-write-scope.md` §Git-State Observation
   (REQ-HARN-HARNESSP6-001).
3. [x] [implement] `references/write-scope.md` §5: the `GIT_STATE` line, rendered
   **inside** the existing write-scope block exactly parallel to
   `HISTORY_REWRITE`, above the path list, counting into
   `SCOPE: VIOLATION (N paths)`. No new own-line gate token; the REQ-ORCH-034
   signal order is unchanged — traces to `docs/spec/harness-write-scope.md`
   §Git-State Observation and Q-REQ-P6-A (REQ-HARN-HARNESSP6-001).
4. [x] [implement] `references/write-scope.md` §8: the option set
   `restore │ accept (note) │ stop`, with `proceed` withheld while the finding
   is unresolved — the same withholding rule an unresolved `OUT` path carries;
   `restore` is `git stash pop` for the stash case and `git checkout -- <path>`
   for a reverted path; `accept (note)` lives in ephemeral gate text only —
   traces to `docs/spec/harness-write-scope.md` §Git-State Observation
   (REQ-HARN-HARNESSP6-001).
5. [x] [implement] Four new `tools/sdd-scope-check-selftest.py` scenarios:
   stash-then-pop → `GIT_STATE`, `VIOLATION`; stash-then-drop → `GIT_STATE`,
   `VIOLATION`; an implement leaf committing a path already dirty at
   `snapshot(before)` → `SCOPE: CLEAN` (clause (ii) subtracts the committed
   delta); an orchestrator fan-out merge between two dispatches →
   `SCOPE: CLEAN` (it lies outside any leaf's window). Plus the `ORIG_HEAD`
   fixture: absent in both raises nothing, present in `after` only raises
   `GIT_STATE` — traces to `docs/spec/harness-write-scope.md` §Self-Test
   Scenarios and §Verification → Automated (REQ-HARN-HARNESSP6-001).
6. [x] [verify] `python3 tools/sdd-scope-check-selftest.py` exits 0 with all four
   new scenarios plus the `ORIG_HEAD` pair, and every pre-existing fixture still
   passes (compare against the fixture list captured at this task's start, not
   against a remembered count) — traces to
   `docs/spec/harness-write-scope.md` §Acceptance Criteria
   (REQ-HARN-HARNESSP6-001).

**Entry criteria**: None.
**Exit criteria**: self-test exits 0; `references/write-scope.md` §3/§5/§8 carry
the reads, the line and the options; no new gate token exists anywhere;
`python3 tools/sdd-skill-lint.py` exits 0.

### Chunk 4: lint `REQUIRED` rows — `PLAN:` and `GIT_STATE` — scope item 4

**Goal**: the only gate token shipping without a producer/consumer lint pair
gets one, and the new `GIT_STATE` finding name does not ship equally unguarded.
**Depends on**: Chunk 3.
**Tasks**:
1. [x] [implement] Add four `REQUIRED` rows to `tools/sdd-skill-lint.py`:
   `PLAN: INCOMPLETE` in `references/loop-control.md` (producer) and in
   `SKILL.md` (consumer); `GIT_STATE` in `references/write-scope.md` (producer)
   and in `SKILL.md` (consumer). `GIT_STATE` is a finding name inside the
   `SCOPE:` block, so its pattern carries no trailing colon and no option-set
   alternation. `fix:` points at `harness-loop-control.md` §Plan Completion
   Ownership and `harness-write-scope.md` §Git-State Observation respectively —
   traces to `docs/spec/skill-lint-v5.md` §`REQUIRED` Rows — `PLAN:` and
   `GIT_STATE` (REQ-LINT-HARNESSP6-001).
2. [x] [implement] Add `SKILL.md` §The gate's one-line summary mention of
   `GIT_STATE` if it is not already present, so the consumer row is satisfied
   without divergence from the canonical statement — traces to
   `docs/spec/skill-lint-v5.md` §`REQUIRED` Rows — `PLAN:` and `GIT_STATE`
   (REQ-LINT-HARNESSP6-001).
3. [x] [implement] Extend `--self-test`'s mutation loop to cover these four rows —
   traces to `docs/spec/skill-lint-v5.md` §Self-Test Extension.
4. [x] [verify] `python3 tools/sdd-skill-lint.py` exits 0 on the corpus as it
   stands, and exits non-zero naming the respective row when the guarded line is
   removed from a temp copy of each of the three files
   (`references/loop-control.md`, `references/write-scope.md`, `SKILL.md`) —
   traces to `docs/spec/skill-lint-v5.md` §Acceptance Criteria
   (REQ-LINT-HARNESSP6-001).

**Entry criteria**: Chunk 3 complete — `GIT_STATE` must already appear in
`references/write-scope.md` §5, or its `REQUIRED` row fails on the shipped
corpus.
**Exit criteria**: lint exits 0; each of the four rows demonstrably fails when
its marker is removed; `--self-test` exits 0.

### Chunk 5: Q-IMPL definition scan becomes fence-symmetric — scope item 5

**Goal**: a `### Q-IMPL-…` heading inside a fence defines nothing, exactly as a
reference inside a fence references nothing, without introducing a marker, an
info-string tag or an allowlist.
**Depends on**: None (independent of Chunks 1–4).
**Tasks**:
1. [x] [verify] Capture the pre-change baseline in the same session: run
   `python3 tools/sdd-gc.py --report` and record the `qimpl-undefined` and
   `qimpl-broken-ref` counts. This baseline is the comparand for task 5 — it is
   derived, never quoted from an earlier document — traces to
   `docs/spec/drift-sweep.md` §Q-IMPL Counting Rule (REQ-GC-HARNESSP6-004).
2. [x] [implement] In `sweep_qimpl()`, build the visible-line set per spec file and
   collect `^### Q-IMPL-[A-Z0-9-]+` definitions through the same
   `visible_lines()` filter the reference side already uses — traces to
   `docs/spec/drift-sweep.md` §Q-IMPL Counting Rule (REQ-GC-HARNESSP6-004).
3. [x] [implement] State the countability obligation in the module docstring and in
   `--help` alongside the reference commands: an id used inside a fenced format
   illustration must be either an id a real unfenced `### Q-IMPL-…` entry
   defines elsewhere, or one of the id-format placeholders the tool already
   excludes. It is an **authoring obligation, not an allowlist**, so
   `CLAUDE.md` §Quality Checks' "there is no allowlist" sentence stays true and
   is not edited — traces to `docs/spec/drift-sweep.md` §Fence symmetry and the
   countability obligation (REQ-GC-HARNESSP6-004).
4. [x] [implement] Add `test_qimpl_definition_is_fence_symmetric`: a fenced heading
   contributes no definition; a reference to an otherwise-undefined id occurring
   only inside that fence raises no `qimpl-undefined`; an unfenced heading still
   defines; a genuinely undefined unfenced reference still fails — traces to
   `docs/spec/drift-sweep.md` §Verification → Automated.
5. [x] [verify] Re-run `--report` and assert the `qimpl-undefined` and
   `qimpl-broken-ref` counts **equal the baseline captured in task 1** — both
   sides from runs in this session, neither pinned as a literal — traces to
   `docs/spec/drift-sweep.md` §Acceptance Criteria (REQ-GC-HARNESSP6-004).

**Entry criteria**: None.
**Exit criteria**: `--self-test` exits 0; `--report` counts match the in-session
baseline; the obligation is stated in both the docstring and `--help`; no
allowlist, marker or language tag was introduced.

### Chunk 6: the two carried text fixes — scope items 6 and 7

**Goal**: the REQ-LINT-007 contradiction is qualified without amending the
original, and the resolved `telemetry-reader.md` "says 61" question is struck at
archival rather than carried forward as live.
**Depends on**: None (independent of Chunks 1–5). **Note**: task 5 touches
`tools/sdd-gc.py`; do not fan this chunk out concurrently with Chunks 1, 2 or 5,
which edit the same file (plan-review M3).
**Write scope** (widened beyond the implement default — the orchestrator
declares it here and notes the widening at the per-chunk gate, per
`docs/spec/harness-write-scope.md` §Default Scope Table): `tools/sdd-gc.py`,
`docs/requirements/integration/skill-lint.md` (task 1, named by
REQ-LINT-HARNESSP6-002) and `docs/ws/harness-p5/plan.md` (task 4, named
explicitly by REQ-PLAN-HARNESSP6-001 — a **cross-workstream** write into a
closed workstream's owned artifact, annotation-only, no deletion) and
`skills/sdd-plan/SKILL.md` + `skills/sdd-replan/SKILL.md` (task 3, the two
archiving skills the strike rule is taught to — corrected 2026-09-20 at
dispatch; the earlier line omitted them). Without this
declaration all three render `OUT` and the per-chunk gate withholds `proceed`.
**Tasks**:
1. [x] [implement] Add a bracketed dated `[Updated: 2026-09-20 …]` note to
   REQ-LINT-007 in `docs/requirements/integration/skill-lint.md`, naming the
   authorised exception and **REQ-LINT-HARNESSP5-001** as the authorising
   requirement. The id, its number and its original text are **not** changed —
   amending the original would break every artifact citing it and erase the
   record that the two requirements once disagreed. No lint rule, linter table
   or skill file changes for this item — traces to
   `docs/spec/skill-lint-v5.md` §Qualification of the "must not move" Row
   (REQ-LINT-HARNESSP6-002).
2. [x] [verify] A reader of REQ-LINT-007 and REQ-LINT-HARNESSP5-001 in sequence
   finds no contradiction (**manual criterion — judgement, not mechanism;
   plan-review m4**); the findings of `python3 tools/sdd-skill-lint.py`
   and `python3 tools/sdd-gc.py --report` **on that file** are unchanged from a
   baseline captured immediately before the edit — traces to
   `docs/spec/skill-lint-v5.md` §Acceptance Criteria (REQ-LINT-HARNESSP6-002).
3. [x] [implement] Teach `sdd-plan` and `sdd-replan` the archival strike rule: at
   archival, every `## Open Questions` entry the corpus has since answered is
   **struck** — left visible, marked with a bracketed dated resolution marker on
   its own line or the line immediately preceding it, naming the date and what
   resolved it — never deleted and never reworded in place. An entry the skill
   cannot resolve stays unmarked and is carried into the archive as-is; the rule
   strikes settled entries, it does not force a verdict. It applies to the
   archived copy under `plan-history/` only and adds no file, section or marker
   type — traces to `docs/spec/plan-management.md` §Resolved `## Open Questions`
   Entries Are Struck at Archival (REQ-PLAN-HARNESSP6-001).
4. [x] [implement] Close the concrete instance: strike the `telemetry-reader.md`
   "says 61" entry in `docs/ws/harness-p5/plan.md` §Open Questions / Assumptions with its date
   and the evidence that resolved it, so the stale claim no longer appears
   unmarked in that file or in the archive that replaces it — traces to
   `docs/spec/plan-management.md` §Acceptance Criteria
   (REQ-PLAN-HARNESSP6-001).
5. [x] [verify] The struck entry is still **present** — the archived file's entry
   count is unchanged by the strike (compare entry counts before and after in
   the same run) — and carries an adjacent bracketed dated marker; a search for
   the stale claim finds no **unmarked** occurrence — traces to
   `docs/spec/plan-management.md` §Verification → Automated
   (REQ-PLAN-HARNESSP6-001).
   **[Supersession, recorded 2026-09-20 (plan-review M5) — do not verify the
   requirement's literal.]** REQ-PLAN-HARNESSP6-001's own acceptance text reads
   `grep -c 'says 61' … ` prints `0`. That literal is **unsatisfiable and
   self-contradictory**: the strike rule shipped by this same cycle leaves the
   entry visible and never reworded in place, so the string necessarily
   survives — measured, the count is `1` and striking leaves it `1`. The
   governing form is `docs/spec/plan-management.md` §Acceptance Criteria — the
   stale claim no longer appears **unmarked** — which this task implements. The
   requirement's literal is superseded by the spec bullet; `sdd-verify` must
   walk the spec form, not the requirement's grep. This is the fourth
   pinned-literal criterion this cycle has had to correct.

**Entry criteria**: None.
**Exit criteria**: lint exits 0; gc `--report` findings on
`integration/skill-lint.md` unchanged against the in-chunk baseline; the struck
entry present-and-marked; no requirement id, number or original text altered.

### Chunk 7: §Out of Scope discipline and the deferral sweep — scope item 9

**Goal**: when this cycle closes, no entry in `docs/requirements/index.md`
§Out of Scope and no item in a `verification.md` §Next Steps reads as deferred,
carried or queued to a later cycle.
**Depends on**: Chunk 6 — matching this chunk's own entry criteria, so the
canonical dependency field and the entry criteria cannot disagree (plan-review
M2). The dependency is a **convention** one, not a data one: Chunk 6 task 3
establishes the plan-archival strike convention that is the ambient rule when
this sweep annotates entries.
**Write scope** (widened beyond the implement default, declared here per
`docs/spec/harness-write-scope.md` §Default Scope Table):
`docs/requirements/index.md` (task 3, named by REQ-REQ-HARNESSP6-001) and
`docs/spec/requirements-artifacts.md`. Without this declaration task 3 renders
`OUT` and the per-chunk gate withholds `proceed`.
**Tasks**:
1. [x] [implement] State the four dispositions (settled exclusion with reasoning /
   closed with date and evidence / superseded by a pointer / in scope) and the
   adjacent-marker liveness rule in the requirements corpus contract, including
   both deliberate consequences: every annotated item carries its **own
   adjacent** marker, a block-level marker introducing several items does not
   satisfy the rule, and §Q-REQ Resolutions prose recording what a **closed**
   cycle decided is outside the checked scopes — traces to
   `docs/spec/requirements-artifacts.md` §`## Out of Scope` Discipline
   (REQ-REQ-HARNESSP6-001).
2. [x] [implement] Bind the same rule to `verification.md` §Next Steps: a finding
   too large to fix inside the cycle triggers a **replan**, never a successor
   workstream — traces to `docs/spec/requirements-artifacts.md` §`## Out of
   Scope` Discipline (REQ-REQ-HARNESSP6-001).
3. [x] [implement] Sweep `docs/requirements/index.md` §Out of Scope: every live
   deferral entry becomes a settled exclusion with reasoning, a closed entry
   with date and evidence, a pointer to the superseding requirement, or is
   removed because a requirement now carries it. **Already satisfied at the
   requirements stage (plan-review m2)**: all three exclusions are present with
   their reasoning in `docs/requirements/index.md` §Out of Scope (written
   2026-09-20) and the liveness check reports nothing live, so this is a
   **confirm-presence** step, not re-authoring, and must not read as undone
   work at the gate. The three settled exclusions
   named by RS-HARNESSP6-001 — the already-moot `qimpl-broken-ref` entry
   (retired as satisfied, with the run-time evidence that gc reports none), the
   one-shot upstream review before a non-research pipeline entry, and review of
   `sdd-review`'s own output — are each present with their reasoning — traces to
   `docs/spec/requirements-artifacts.md` §Acceptance Criteria
   (REQ-REQ-HARNESSP6-001).
4. [x] [verify] Run the mechanical liveness check — a case-insensitive search for
   the deferral phrasings over the two scopes, accepting only an adjacent
   bracketed dated `Superseded | Closed | Struck` marker on the entry's own or
   immediately preceding line — and assert it reports **no live entry**; assert
   separately that a block-level marker fixture does **not** satisfy the rule
   and that §Q-REQ Resolutions prose is not examined — traces to
   `docs/spec/requirements-artifacts.md` §Verification → Automated
   (REQ-REQ-HARNESSP6-001).

**Entry criteria**: Chunk 6 complete.
**Exit criteria**: the liveness check reports nothing live in either scope; the
three named settled exclusions are present with reasoning; no entry was deleted
that should have been marked closed.

### Chunk 8: L2 resolving spike — the cluster rule replayed [high-uncertainty]

**Goal**: measure what the `(file, section)` cluster rule would actually have
clustered, before any L2 implement task is written, so the implement tasks are
steered by data rather than by the rule's stated intent.
**Depends on**: Chunk 7 (**sequencing only** — kickoff §Decided at DISCUSS
binds L2 to run last among the implementation items; there is no data
dependency, since the spike replays the harness-p3/-p4/-p5 finding sets and
needs nothing Chunk 7 produces. Recorded so the canonical graph does not hide
why 6→7→8 is serial, plan-review M2).
**Tasks**:
1. [ ] [spike] Replay the cluster rule over the **recorded** findings of the
   harness-p3, harness-p4 and harness-p5 cycles (their `verification.md`
   §Issues Found, review findings recorded in those cycles' artifacts, and red
   rounds where recorded). Count the clusters the three conditions produce —
   different layers, same cycle by `research_id`, equal arbitration finding key
   at section granularity, plus the secondary `REQ-*` / deviation-entry id key —
   and split them into clusters an operator would call the same root cause and
   ones they would not. Report both numbers and the file-level-only matches the
   rule deliberately renders nothing for. **Budget: three cycles' finding sets,
   ~15 tool calls, no code written.** Record the outcome as a finding, not as a
   spec edit — traces to `docs/spec/harness-loop-control.md` §Convergence Signal
   — L2 → Uncertainty, spike and fallback (REQ-HARN-HARNESSP6-002).
2. [ ] [spike] From the same replay, state explicitly whether the rule reproduces
   the recorded **2-of-3 recall** against the harness-p3 §L2 origin case (blue's
   dropped `git add` in Chunk 7, review C1's unexercised requirement, red R4's
   aggregate-drift finding), and whether any cluster it forms is one an operator
   would reject — traces to `docs/spec/harness-loop-control.md` §Convergence
   Signal — L2 (REQ-ORCH-HARNESSP6-002).

**Entry criteria**: Chunk 7 complete. The spike reads only; it writes no spec,
tool or skill file.
**Exit criteria**: a stated cluster count split into operator-agreeable and
operator-rejectable, the origin-case recall stated, and an explicit verdict:
**proceed with the co-located key as specified**, or **fire the replan trigger**
below.

### Chunk 9: L2 implementation — the convergence signal — scope item 8

**Goal**: `CONVERGENCE:` ships as an orchestrator-derived, informational gate
line at position 6c, with a session-scoped in-memory ledger, adding no finding
field, no fifth layer and no durable artifact.
**Depends on**: Chunk 8.
**Tasks**:
1. [ ] [implement] State the cluster rule in `docs/spec/harness-loop-control.md`'s
   consumer texts and in `skills/sdd-orchestrate/references/loop-control.md`:
   the three conditions (different layers or second-executors; same cycle by the
   `research_id` stamp; arbitration finding keys equal at **section**
   granularity, reusing the existing `(file, section)` key and its ratified
   leading-ordinal strip), the secondary id key, and the decisive
   false-positive control — a **file-level-only match renders nothing** —
   traces to `docs/spec/harness-loop-control.md` §Convergence Signal — L2
   (REQ-HARN-HARNESSP6-002).
2. [ ] [implement] State the ledger: session-scoped, in memory, of the same class as
   the loop counters, holding exactly three fields per finding
   (`key`, `layer`, `gate`). No finding text, nothing on disk, never read by any
   skill's phase detection, discarded at session end — traces to
   `docs/spec/harness-loop-control.md` §Convergence Signal — L2 → The ledger
   (REQ-HARN-HARNESSP6-002).
3. [ ] [implement] State the window: evaluated at **every** gate over everything
   recorded so far; each cluster renders **once**, at the gate where its second
   member arrives; a cluster completing only at DONE routes into
   `verification.md` §Issues Found — to be fixed or explicitly closed in this
   cycle — and **never** into §Next Steps — traces to
   `docs/spec/harness-loop-control.md` §Convergence Signal — L2 → The window
   (REQ-HARN-HARNESSP6-002).
4. [ ] [implement] Render the own-line token `CONVERGENCE:` at position **6c** of
   the gate signal order — after 6b (`PLAN:`) and immediately before 7
   (`TELEMETRY:`) — naming the cluster's file and section, the contributing
   layers and the layer count. Amend the "renders last before the options"
   clause to name 6c. `references/loop-control.md` §5 must agree item for item
   with the spec's §Gate Signal Order, and `SKILL.md` §The gate names the token
   in its non-divergent summary — traces to
   `docs/spec/harness-loop-control.md` §Rendering and position and Q-REQ-P6-B
   (REQ-ORCH-HARNESSP6-001).
5. [ ] [implement] Make and state its informational status: no option set, never
   pauses the gate, never withholds `proceed` — traces to
   `docs/spec/harness-loop-control.md` §Rendering and position
   (REQ-ORCH-HARNESSP6-001).
6. [ ] [implement] State the shipped **co-located** scope explicitly, with the
   recorded 2-of-3 recall against the harness-p3 §L2 origin case as the
   accepted cost of shipping without a root-cause field or a fifth layer, so
   verification is never asked to prove a property the design does not deliver.
   Add the one cross-reference in `docs/spec/arbitrated-handoff.md` recording
   that the `(file, section)` key now has two consumers — traces to
   `docs/spec/harness-loop-control.md` §Shipped scope
   (REQ-ORCH-HARNESSP6-002).
7. [ ] [implement] Add the key-parser scenario group (four cases: different layers
   with equal `(file, section)` cluster; same layer does not; same file with
   different sections does not; different layers citing the same `REQ-*` id with
   different sections do), the different-`research_id` non-clustering fixture,
   the gate rendering fixture showing the line between 6b and 7 with `proceed`
   available, the no-new-path fixture, and — plan-review m7 — a
   `Q-IMPL-HARNESSP6-001` case asserting that a **third** layer joining an
   already-rendered cluster does **not** re-render it (the one ambiguity the
   spec resolved by choice, and the one most likely to regress silently) —
   traces to
   `docs/spec/harness-loop-control.md` §Verification → Automated
   (REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-001, REQ-ORCH-HARNESSP6-002).
8. [ ] [implement] Append the `CONVERGENCE:` `REQUIRED` row **pair** to
   `tools/sdd-skill-lint.py` (producer `references/loop-control.md` §5 item 6c,
   consumer `SKILL.md` §The gate), extend `--self-test`'s mutation loop to the
   pair, and assert the **new `len(REQUIRED)` total exactly** — the table counts
   rows, not files, and this cycle's six new rows (`PLAN:` ×2, `GIT_STATE` ×2,
   `CONVERGENCE:` ×2) are now all present — traces to
   `docs/spec/skill-lint-v5.md` §`REQUIRED` Row — `CONVERGENCE:` and
   §Self-Test Extension (REQ-LINT-HARNESSP6-003, REQ-LINT-HARNESSP6-001).
9. [ ] [verify] Assert the three invariants hold: no file under `docs/` is created
   by L2 — **demonstrated, not asserted (plan-review M4)**: capture
   `git ls-files docs/` before and after a run of the task-7 ledger/gate-render
   fixture in which a cluster actually fires, and assert the two listings are
   identical. The original phrasing ("across a full orchestrated cycle in which
   a cluster fired") could not be exercised inside this cycle, since nothing
   here makes a real cluster fire during a real cycle; that is the assert-rather-
   than-demonstrate failure this corpus keeps repeating, so the fixture run is
   the comparand. No phase-detection branch in any `sdd-*` skill
   references the signal or the ledger; the four-layer verification table is
   byte-identical in `CLAUDE.md` and in every spec that restates it (compare
   against the pre-chunk content, not against a remembered rendering); and no
   telemetry record key was added — traces to
   `docs/spec/harness-loop-control.md` §Three invariants
   (REQ-ORCH-HARNESSP6-002).
10. [ ] [verify] Assert no leaf `RETURN:` shape in
    `docs/spec/harness-return-contract.md` or in any dispatch template gained a
    field for L2 — traces to `docs/spec/harness-loop-control.md` §Acceptance
    Criteria (REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-002).

**Entry criteria**: Chunk 8 complete with a `proceed` verdict, or with a replan
having reshaped this chunk's tasks to the descoped form.
**Exit criteria**: lint exits 0 and fails when either `CONVERGENCE:` line is
removed; the key-parser group and the gate rendering fixture pass; `proceed` is
available while the line renders; the three invariants verified; `--self-test`
asserts the exact new `len(REQUIRED)`.

### Chunk 10: cycle close-out verification

**Goal**: the terminal cycle's closing conditions are demonstrated, not
asserted.
**Depends on**: Chunk 9.
**Tasks**:
1. [ ] [verify] Run `python3 tools/sdd-gc.py --self-test`, `python3
   tools/sdd-gc.py --report`, `python3 tools/sdd-skill-lint.py`,
   `python3 tools/sdd-skill-lint.py --self-test` and
   `python3 tools/sdd-scope-check-selftest.py`; all exit 0 / `OK`, and the lint
   summary matches `OK: N file(s) clean` **with no warning clause** (the linter
   omits the count when there are none, so a `0 warning(s)` expectation is
   unsatisfiable and must not be restored) — traces to
   `docs/spec/skill-lint-v5.md` §Verification → Automated and
   `docs/spec/drift-sweep.md` §Acceptance Criteria.
2. [ ] [verify] Re-run the mechanical liveness check of Chunk 7 task 4 over both
   scopes after every other chunk has landed, so a deferral phrased by a later
   chunk is caught: no live deferral in `docs/requirements/index.md`
   §Out of Scope, none in this cycle's `verification.md` §Next Steps — traces to
   `docs/spec/requirements-artifacts.md` §Acceptance Criteria
   (REQ-REQ-HARNESSP6-001).
3. [ ] [verify] Walk every row of `docs/ws/harness-p6/traceability.md` and confirm
   each of the thirteen requirements has an exercised Test and Implementation
   reference; the DONE rule is that every row reads `pass`, nothing closes as a
   deliberate `fail`, and an item that cannot be exercised is descoped at
   replan — traces to `docs/spec/ws-traceability.md` and the kickoff §Decided at
   DISCUSS.
4. [ ] [verify] Confirm marker-3 behaviour is unchanged: no code path added this
   cycle is reachable without `docs/ws/`, and no marker-3 contract text was
   edited — traces to `docs/spec/drift-sweep.md` §Closed-Workstream Skip and the
   kickoff §Out of scope.

**Entry criteria**: Chunks 1–9 complete.
**Exit criteria**: every command above green; no live deferral in either scope;
thirteen traceability rows exercisable.

## Replan Triggers

- **The L2 spike (Chunk 8) finds the `(file, section)` cluster rule clusters
  unrelated findings at a rate an operator would call noise, or forms no cluster
  at all over the three replayed cycles** → **replan inside this cycle** that
  descopes L2 to its honest floor: the secondary-id key alone (highest
  precision, lowest recall), or the co-located key evaluated at DONE only. The
  descope is recorded as a settled exclusion with its reasoning in
  `docs/requirements/index.md` §Out of Scope. Chunk 9's tasks 1, 3, 4 and 7 are
  rewritten to the chosen floor; tasks 2, 5, 6, 8, 9 and 10 stand unchanged.
- **L2 as specified proves to need a root-cause field on a leaf's `RETURN:`, or
  a fifth verification layer** → replan to the reduced form immediately; both
  are standing exclusions and neither is negotiable, and "cannot be done" is not
  an available outcome (kickoff §Decided at DISCUSS).
- **Chunk 2's zero-`[stale-chain]`-warnings condition does not hold after Chunk
  1 has landed** → a plan-level sub-kind exists that the closed-workstream
  predicate does not cover; replan Chunk 1 rather than weakening the Chunk 2
  criterion or bumping any `last_updated:` to silence it (bumping a date to
  silence a sweep is out of scope by the kickoff).
  **Exception — diagnose before firing this trigger (plan-review M1).**
  `harness-p6` is an **open** workstream, so the closed-workstream predicate
  never skips **its own** plan. If the only remaining plan-level findings are
  located in `docs/ws/harness-p6/plan.md`, the cause is not Chunk 1's
  predicate: it is that this cycle re-dated a spec past this plan's own
  `last_updated:` (a replan, or work spanning midnight). The correct response is
  to bump `docs/ws/harness-p6/plan.md` `last_updated:` to the current date —
  which is not silencing a sweep, because the plan genuinely did change — and
  **not** to replan Chunk 1. Check the finding locations before deciding.
- **Chunk 5's fence-symmetry change moves the `qimpl-undefined` or
  `qimpl-broken-ref` count off its in-session baseline** → the countability
  obligation is not satisfied by the corpus as it stands; replan to add the
  authoring fix to the corpus, never an allowlist or a marker.
- **Chunk 3's clause (ii) fires on a legitimate dispatch in the self-test** →
  the comparand is wrong, not the fixture; replan the comparand. A criterion
  that flags a normal implement leaf or a fan-out merge is not acceptable.
- **Chunk 7's sweep uncovers an §Out of Scope entry that is neither retirable
  with reasoning nor small enough to bring into this cycle** → replan **inside
  this cycle** to size it; it is never moved to a successor workstream.

## Risks

- **L2 is Medium-confidence and its firing rate is unmeasured**
  (RS-HARNESSP6-001 Q4; carried onto the three L2 traceability rows). Mitigation:
  the mandatory spike at Chunk 8 precedes every L2 implement task, the signal is
  informational so a false positive costs one line rather than an operator
  interruption, and the descope path is a named in-cycle replan rather than a
  deferral.
- **Six new lint `REQUIRED` rows land in two chunks, not one.** The spec says
  they "land together as one change to the `REQUIRED` table". A row for a token
  that has not shipped fails the lint on the shipped corpus, and every chunk
  exits with lint green. Mitigation: the four `PLAN:` / `GIT_STATE` rows land at
  Chunk 4 and the `CONVERGENCE:` pair at Chunk 9 task 8, which also asserts the
  exact new `len(REQUIRED)` — so the six are one table state by cycle close.
  Recorded under §Open Questions.
- **Counted acceptance criteria are the corpus's most repeated defect.** Every
  criterion above derives both sides at run time or compares against an
  in-session baseline. Mitigation: any criterion added during implementation
  that quotes a corpus count is treated as a defect at the chunk gate, not as a
  detail.
- **Chunk 6 edits the requirements corpus** (`integration/skill-lint.md`), which
  is shared. Mitigation: the edit is additive — a dated bracketed note — and the
  requirement's id, number and original text are untouched, so nothing that
  cites it breaks.
- **Chunk 3's design is derived from contract text rather than a replayed
  dispatch** (Confidence Medium-High). Mitigation: the four self-test scenarios
  are required work, not optional colour, and two of them are negatives.

## Open Questions

1. **Why the six lint rows land in two chunks.** `docs/spec/skill-lint-v5.md`
   §`REQUIRED` Row — `CONVERGENCE:` says the three pairs "land together as one
   change to the `REQUIRED` table". Read literally against the rule that every
   chunk exits with `python3 tools/sdd-skill-lint.py` at 0, a `CONVERGENCE:` row
   added before the token ships would fail immediately, and a `GIT_STATE` row
   added before Chunk 3 likewise. The reading taken: "one change to the table"
   is a statement about the table's **end state** and its single self-test
   assertion, not a scheduling constraint. The four `PLAN:` / `GIT_STATE` rows
   land at Chunk 4 (after their markers exist) and the `CONVERGENCE:` pair at
   Chunk 9, whose task 8 asserts the exact new `len(REQUIRED)` covering all six.
   Chosen non-interactively; no operator was available to arbitrate.
2. **Chunk 7's placement.** The kickoff's §Scope order puts the deferral sweep
   ninth — after L2 (item 8). It is scheduled **before** the L2 chunks here
   because the sweep is a corpus text change with no dependency on L2, while L2
   is the designated replan risk; landing the sweep first keeps a `stop` after
   Chunk 7 leaving eight of nine items complete. The kickoff's own binding
   instruction — "L2 is sequenced **last** among the implementation items" — is
   what this ordering follows; the §Scope numbering is a listing order, and the
   two are read as consistent with L2 last.
3. **Which harness-p3/-p4/-p5 findings the Chunk 8 spike replays.** The recorded
   finding sets are the three cycles' `verification.md` §Issues Found plus the
   red rounds and review findings those files record; reviews were ephemeral, so
   any review finding not recorded in a durable artifact cannot be replayed. The
   spike reports its input set explicitly so its recall figure is interpretable,
   rather than implying it replayed findings that no longer exist.
