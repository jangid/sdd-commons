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

**Replanned 2026-09-20 (L2 descope).** The first replan trigger fired on the
Chunk 8 spike result — the co-located `(file, section)` key forms zero clusters
over three replayed cycles and 0 of 3 on the origin case. L2 still ships in this
cycle, at a measured floor: the shared-id key as the **primary** cluster key plus
a **sectionless-file** rule, with the equal-`(file, section)` key retained but
carrying no recall claim, and the noise guard for sectioned files unchanged.
Chunk 9 tasks 1, 3, 4 and 7 are rewritten to that floor; the previous plan is at
`docs/ws/harness-p6/plan-history/2026-09-20-replan-l2-descope.md`.

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
1. [x] [spike] Replay the cluster rule over the **recorded** findings of the
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
2. [x] [spike] From the same replay, state explicitly whether the rule reproduces
   the recorded **2-of-3 recall** against the harness-p3 §L2 origin case (blue's
   dropped `git add` in Chunk 7, review C1's unexercised requirement, red R4's
   aggregate-drift finding), and whether any cluster it forms is one an operator
   would reject — traces to `docs/spec/harness-loop-control.md` §Convergence
   Signal — L2 (REQ-ORCH-HARNESSP6-002).

**Spike Findings (recorded 2026-09-20, this session, from the artifacts)**

*Input set, stated honestly.* The replay covers only **durably recorded**
findings: `docs/ws/harness-p3/verification.md` §Issues Found (11 Minor bullets),
§Red Team R1 and §Verify-Stage Acceptance Obligations V1-V14;
`docs/ws/harness-p4/verification.md` §Issues Found (2 Minor, both red);
`docs/ws/harness-p5/verification.md` §Post-cycle Fixes (2) and §Issues Found
(8 Minor). **What it necessarily omits**: every review finding and every chunk
verifier finding, because reviews and `CHUNK_VERDICT:` are ephemeral by design
and were never written to disk — the harness-p3 origin case's review C1 survives
only as a paraphrase inside red R4's prose. Consequently, of the six
layers/second-executors condition (i) requires to differ, the durable record
contains only **two** in practice — red, and blue/verify (including the gc-routed
items). Cross-layer clustering therefore had only a red x blue axis available.
Live, the in-memory ledger would also see review and chunk-verifier entries, so
the replayed rate is a **floor**, not the live rate. The origin-case result below
is not subject to that caveat, and is what carries the verdict.

*Task 1 — cluster counts derived this session.*

| Cycle (`research_id`) | clusters by (iii) `(file, section)` | clusters by secondary id | cross-layer file-level-only matches (rule renders nothing) |
|---|---|---|---|
| harness-p3 / RS-HARNESSP3-001 | 0 | 0 | 2 |
| harness-p4 / RS-HARNESSP4-001 | 0 | 0 | 0 (both findings are red — (i) fails first) |
| harness-p5 / RS-HARNESSP5-001 | 0 | 1 | 0 |
| **total** | **0** | **1** | **2** |

- **Zero** clusters from the co-located `(file, section)` key over three real
  cycles. No section-granular key appears twice at all, in any cycle: the
  recorded section keys are singletons — `arbitrated-handoff.md` §Retained
  Per-Round State (blue/V11), `references/loop-control.md` §2a (blue/V10),
  `CLAUDE.md` §Phase Detection (blue/V13), `deviation-protocol.md` §Numbering
  (red), `harness-write-scope.md` §criterion (red).
- **One** cluster from the secondary id key, in harness-p5: red round 2 R1 (the
  unreproducible lint-summary criterion) and the blue finding on
  `docs/requirements/integration/skill-lint.md` both cite
  **REQ-LINT-HARNESSP5-001**, in different files and different sections.
  Operator split: **0 that an operator would confidently call one root cause,
  1 marginal** — both are stale text left behind by the Chunk 9 rescope of
  `skill-lint-v5.md`, but R1's criterion defect predates that rescope, so the
  shared id is a topical adjacency rather than a demonstrated common cause. It
  is contestable in both directions; it is not a clean win.
- **Two** cross-layer file-level-only matches, both in harness-p3, both
  correctly rendering nothing per the noise guard — and the guard scored 1-1 on
  them: (a) `.sdd/telemetry.jsonl` — red R1 and the blue restatement of the same
  8 malformed records: genuinely one root cause, **missed** (a JSONL data file
  has no sections, so no section key can ever exist for it); (b)
  `tools/sdd-telemetry.py` — red R1 (the reader hid a schema violation) and blue
  (the summarize table is ~190 columns wide): unrelated, **correctly
  suppressed**. On n=2 the section-granularity guard suppressed one true
  convergence for every one false positive it prevented.

*Task 2 — origin-case recall, and operator-rejectable clusters.*

- **The rule does NOT reproduce the recorded 2-of-3 recall.** Against the
  harness-p3 §L2 origin case it clusters **0 of 3**. Two of the three members'
  locations are recoverable from the record and they differ at **file** level,
  before section granularity is even consulted: blue's finding is the `CLAUDE.md`
  path dropped from Chunk 7's `git add` (`docs/ws/harness-p3/verification.md`
  §V14, repaired at `16e240b`); red R4's is the shared aggregate
  `docs/requirements/traceability.md` differing from
  `regenerate(docs/ws/*/traceability.md)`. Review C1 (a `docs/ws/harness-p3/`
  per-ws `Verified` cell about to flip to `pass`) is a third file again, and is
  not durably recorded at all. No pair shares a file, so no pair can share a
  `(file, section)`; the secondary key does not save it either (the cited ids
  differ). The 2-of-3 figure in `docs/spec/harness-loop-control.md` §Convergence
  Signal — L2 is **not reproducible from the record**, and the two keys that are
  recoverable actively contradict it.
- **Why this is structural, not a sampling artefact.** Different layers describe
  one defect at different granularities and from different directions — that is
  precisely the property the harness pays for (harness-p3 §L1). Blue names the
  path that did not land; red names the invariant that nothing enforces; review
  names the cell about to be asserted. Co-location is the one thing a genuine
  cross-layer convergence is least likely to exhibit. The ephemerality caveat
  above does not rescue it: adding the missing review/chunk-verifier entries
  supplies *more* findings in *more* files, not more co-located ones.
- **Operator-rejectable clusters formed: 0 outright, 1 marginal** (the harness-p5
  secondary-id cluster above). The rule's false-positive control works; it is the
  true-positive rate that is absent.

*Verdict.* **FIRE THE REPLAN TRIGGER** — the plan's first replan trigger, second
disjunct, is satisfied exactly and literally: the `(file, section)` key **forms
no cluster at all over the three replayed cycles** (0 of 3 cycles, 0 clusters
total), and it additionally fails the origin case it was specified against
(0-of-3, not 2-of-3). This is not the noise branch — the rule is not noisy, it is
**silent**. Descope L2 inside this cycle to its honest floor, and specifically to
**the secondary-id key alone**: it is the only key that fired at all over the
replay (1 cluster / 3 cycles), while "the co-located key evaluated at DONE only"
would still render zero — a DONE-only window cannot add a cluster that a
whole-cycle window never formed. The descope, with this reasoning, is recorded as
a settled exclusion in `docs/requirements/index.md` §Out of Scope, and Chunk 9's
tasks 1, 3, 4 and 7 are rewritten to the secondary-id floor (tasks 2, 5, 6, 8, 9,
10 stand). Next action: `sdd-replan`.

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
1. [x] [implement] **[Rewritten at replan 2026-09-20 — descoped floor]** State the
   cluster rule in `docs/spec/harness-loop-control.md`'s consumer texts and in
   `skills/sdd-orchestrate/references/loop-control.md`: the three conditions
   (different layers or second-executors; same cycle by the `research_id` stamp;
   arbitration finding keys matching under one of the **three key rules**), and
   the key rules themselves in this order — (1) **shared id, primary**: the same
   `REQ-*` or deviation-entry id clusters whatever the files and sections, the
   only key the Chunk 8 replay saw fire; (2) **sectionless file**: the
   file-level key is itself a cluster key when the arbitration key parser finds
   **no section** in the file (a `.jsonl`, `.py` or other file with no section
   structure), which is what recovers the one genuine convergence a
   section-granular key structurally cannot catch; (3) **equal
   `(file, section)`, retained**: still clusters when it occurs, reusing the
   existing key and its ratified leading-ordinal strip, but carries **no recall
   claim** — the Chunk 8 replay measured it at zero clusters over three cycles.
   State the false-positive control in its retained form: **in a file that has
   sections, a file-level-only match renders nothing** — traces to
   `docs/spec/harness-loop-control.md` §Convergence Signal — L2
   (REQ-HARN-HARNESSP6-002).
2. [x] [implement] State the ledger: session-scoped, in memory, of the same class as
   the loop counters, holding exactly three fields per finding
   (`key`, `layer`, `gate`). No finding text, nothing on disk, never read by any
   skill's phase detection, discarded at session end — traces to
   `docs/spec/harness-loop-control.md` §Convergence Signal — L2 → The ledger
   (REQ-HARN-HARNESSP6-002).
3. [x] [implement] **[Rewritten at replan 2026-09-20 — descoped floor]** State the
   window in terms of the amended key rules: evaluated at **every** gate over
   everything recorded so far; a cluster formed under **any** of the three key
   rules (shared id, sectionless file, retained `(file, section)`) renders
   **once**, at the gate where its second member arrives; a cluster completing only at DONE routes into
   `verification.md` §Issues Found — to be fixed or explicitly closed in this
   cycle — and **never** into §Next Steps — traces to
   `docs/spec/harness-loop-control.md` §Convergence Signal — L2 → The window
   (REQ-HARN-HARNESSP6-002).
4. [x] [implement] **[Rewritten at replan 2026-09-20 — descoped floor]** Render the
   own-line token `CONVERGENCE:` at position **6c** of the gate signal order —
   after 6b (`PLAN:`) and immediately before 7 (`TELEMETRY:`) — naming the
   cluster's **key in whichever of the three shapes formed it** (the shared id;
   the file alone, for a sectionless file; or file and section), the
   contributing layers and the layer count. Position 6c, the token spelling and
   the informational status are unchanged by the replan; only the key shapes the
   line must be able to render changed. Amend the "renders last before the options"
   clause to name 6c. `references/loop-control.md` §5 must agree item for item
   with the spec's §Gate Signal Order, and `SKILL.md` §The gate names the token
   in its non-divergent summary — traces to
   `docs/spec/harness-loop-control.md` §Rendering and position and Q-REQ-P6-B
   (REQ-ORCH-HARNESSP6-001).
5. [x] [implement] Make and state its informational status: no option set, never
   pauses the gate, never withholds `proceed` — traces to
   `docs/spec/harness-loop-control.md` §Rendering and position
   (REQ-ORCH-HARNESSP6-001).
6. [x] [implement] State the shipped scope explicitly — shared id primary,
   sectionless file, retained `(file, section)` — with the **measured**
   origin-case recall (Chunk 8: 0 of the 3 harness-p3 §L2 members) as the
   accepted cost of shipping without a root-cause field or a fifth layer, so
   verification is never asked to prove a property the design does not deliver.
   **[Corrected 2026-09-20 at replan — the task otherwise stands as the fired
   trigger directs; only the refuted 2-of-3 figure it quoted is replaced by the
   measured result. Recorded under §Open Questions 4.]**
   Add the one cross-reference in `docs/spec/arbitrated-handoff.md` recording
   that the `(file, section)` key now has two consumers — traces to
   `docs/spec/harness-loop-control.md` §Shipped scope
   (REQ-ORCH-HARNESSP6-002).
7. [x] [implement] **[Rewritten at replan 2026-09-20 — descoped floor]** Add the
   key-parser scenario group (**five** cases: different layers citing the same
   `REQ-*` id with different sections **cluster** — the primary key; different
   layers naming the same file in which the parser finds **no section** cluster
   on the file alone — the sectionless-file rule, with the `.jsonl` shape of the
   `.sdd/telemetry.jsonl` case the Chunk 8 replay found; different layers in the
   same **sectioned** file with different sections do **not** — the retained
   noise guard; the same layer does not; different layers with equal
   `(file, section)` **cluster** — the retained key), the
   different-`research_id` non-clustering fixture,
   the gate rendering fixture showing the line between 6b and 7 with `proceed`
   available, the no-new-path fixture, and — plan-review m7 — a
   `Q-IMPL-HARNESSP6-001` case asserting that a **third** layer joining an
   already-rendered cluster does **not** re-render it (the one ambiguity the
   spec resolved by choice, and the one most likely to regress silently) —
   traces to
   `docs/spec/harness-loop-control.md` §Verification → Automated
   (REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-001, REQ-ORCH-HARNESSP6-002).
8. [x] [implement] Append the `CONVERGENCE:` `REQUIRED` row **pair** to
   `tools/sdd-skill-lint.py` (producer `references/loop-control.md` §5 item 6c,
   consumer `SKILL.md` §The gate), extend `--self-test`'s mutation loop to the
   pair, and assert the **new `len(REQUIRED)` total exactly** — the table counts
   rows, not files, and this cycle's six new rows (`PLAN:` ×2, `GIT_STATE` ×2,
   `CONVERGENCE:` ×2) are now all present — traces to
   `docs/spec/skill-lint-v5.md` §`REQUIRED` Row — `CONVERGENCE:` and
   §Self-Test Extension (REQ-LINT-HARNESSP6-003, REQ-LINT-HARNESSP6-001).
9. [x] [verify] Assert the three invariants hold: no file under `docs/` is created
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
10. [x] [verify] Assert no leaf `RETURN:` shape in
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

- **[FIRED 2026-09-20 — resolved by the replan archived at
  `plan-history/2026-09-20-replan-l2-descope.md`; retained here as the record of
  what fired, and no longer armed.]** **The L2 spike (Chunk 8) finds the
  `(file, section)` cluster rule clusters
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

- **L2's firing rate is now measured, and it is low** (RS-HARNESSP6-001 Q4;
  Chunk 8 replay: one cluster over three cycles, from the shared-id key, plus
  the sectionless-file case the amended rule now catches). The residual risk is
  that the shipped floor fires rarely enough to be invisible in practice;
  accepted, because the signal is informational and costs one line either way,
  and because the measurement is on the record rather than estimated.
  Mitigation (as planned, and exercised):
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

4. **Whether the equal-`(file, section)` key survives the descope at all, and
   what to do about Chunk 9 task 6.** The operator decision specifies the floor
   as the shared-id key as primary plus the sectionless-file rule; it does not
   say whether the co-located key is deleted or demoted. Reading taken, as the
   most consistent with the spike's evidence: **demoted, not deleted** — the
   replay measured its precision at zero false positives, so removing it would
   lose clusters it can still form while removing nothing that misled anyone;
   what is declined, and what §Out of Scope records, is its use as the *primary*
   key and every recall claim resting on it. Second item: the fired trigger's
   text lists task 6 among those that stand, but task 6 as written quotes the
   refuted 2-of-3 recall. Reading taken: the task **stands** as work, and only
   the false figure inside it is corrected to the measured result — leaving a
   refuted number in an active task would re-introduce the defect this replan
   exists to remove. Chosen non-interactively; no operator was available to
   arbitrate.
