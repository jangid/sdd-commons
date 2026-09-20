---
workstream: harness-p5
description: Harness hardening, part 5 — arbitration closure over regenerated artifacts, telemetry writer/reader fixes, skill and spec size housekeeping
cycle: harness-hardening-p5
research_id: RS-HARNESSP5-001
entry_stage: research
date: 2026-09-19
branch: harness-p5
---

# Kickoff: RS-HARNESSP5-001 — Harness hardening, part 5

Run `/sdd-research` for workstream `harness-p5`. This spike settles the three
design questions left open by the harness-p4 cycle; everything else in scope
was decided at DISCUSS on 2026-09-19 and goes straight to requirements.
Findings must land before requirements.

Reuse `docs/research/RS-008-harness-hardening/findings.md`,
`docs/research/RS-HARNESSP2-001-*/findings.md`,
`docs/research/RS-HARNESSP3-001-*/findings.md` and
`docs/research/RS-HARNESSP4-001-*/findings.md`; do not repeat them. The
evidence for this cycle lives in `docs/ws/harness-p4/verification.md`
§Issues Found → Minor (accepted red R7, R8), §Open Questions and §Next Steps,
and in `docs/ws/harness-p4/plan.md` §Replan Triggers and the O1 / O2 operator
task notes.

**Evidence discipline (operator direction, carried from p3 and p4).** Pick the
option the evidence supports and say what the evidence was. Where a question
has no evidence, say so and either run the cheap probe or hand the choice to
requirements — never split the difference silently.

**Git integration (operator decision).** This workstream runs on its own
branch `harness-p5`, branched from `main` after PR #1 (harness-p4) merged, and
merges to `main` by PR at DONE.

## Scope in one paragraph

(1) **Arbitration closure (lead).** `REQ-ARB-HARNESSP4-001` and the carried
`REQ-ARB-HARNESSP3-001` left harness-p4 with empty `Verified` cells because the
live O1 exercise was non-discriminating (fix #1 regenerated `plan.md` wholesale
but byte-identical outside three sections, and round 2 also raised a finding on
`skills/sdd-orchestrate/SKILL.md §Telemetry`, a file the loop never touched, so
class (b) fired under both readings). This cycle settles the spec question —
diff-based section resolution (`arbitrated-handoff.md` §`W_N`,
`loop-control.md` §2a) versus provenance-based `regen[N] = (file, *)`
(Q-IMPL-HARNESSP3-010) — and verifies the chosen rule with a **deterministic
offline fixture** (scripted review rounds over a regenerated file), never a
second live loop. It also adds a legal `descoped` value to
`docs/spec/ws-traceability.md` §Legal `Verified` Cell Values. Both ARB
requirements are traced in this workstream's own `traceability.md` and close
here; harness-p4's two empty cells are set to `descoped` in one orchestrator
bookkeeping commit after the vocabulary lands (a cross-workstream edit, so it
is never inside a leaf's write scope). (2) **Telemetry writer and reader
fixes.** Six findings from the p4 live run: `summarize` implies a first-attempt
pipeline for `(implement, chunk null)` from stage-level `fix` records (false
"1 missing pipeline"); stage-level `fix` records carry `chunk_verdict` with
`chunk: null` while their verifiers are recorded under a chunk (writer rule
needed); the `v: 1` records of a session that upgrades mid-cycle trip the
narrowed equal-heads rule (Q-IMPL-HARNESSP4-007 v1 branch — admit a migration
marker or document as expected); `summarize` admits `v: 2.0` (float) while
`--lint` rejects it; `COMMIT: INCOMPLETE: 0` in `summarize` although one
INCOMPLETE was forced live (the record carries the post-amend token); `--lint`
findings are not emitted in `seq` order. Tests run against
`tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` and a new frozen p4
fixture cut from the live file, never the live file. (3) **Size and spec
housekeeping.** Bring every `SKILL.md` under the 400-line lint warning —
`sdd-orchestrate` (551), `sdd-migrate` (464), `sdd-implement` (434) — by moving
detail to `references/` stubs, and split `docs/spec/telemetry.md` (1137 lines);
amend `skill-lint-v5.md` REQ-LINT-003 / REQ-LINT-007 so the baseline reads
"none" (accepted red R7, R8). Fold Q-IMPL-HARNESSP4-004..009 into Approved
text (equal-heads rule keyed on `commit.token`; `red_break` canonical spelling;
`migration` marker on every `v`; `--plan` shortfall operands; `[template-drift]`
absent-side behaviour; `harness-chunk-verifier.md` §Verdict Rule yaml example
indentation). Fix `harness-commit-fidelity.md` §Comparand Table (`--no-renames
-z` missing; C6 exists but plan text says C1–C5). Verifier advisories:
`commit.token`-on-non-committing-kind positive test beyond `review`; a test
that uppercase `RED_BREAK` is rejected; `migration.from` validator accepts any
string; `loop-control.md` §2a leading-ordinal strip rule absent from the spec
table; arbitration §Automated test names prose-only. Route the four gc
`[qimpl-broken-ref]` warnings (Q-IMPL-002, -009, -014, -072). Assign an owner
to `sdd-implement` Step 6.4 (the plan `status: complete` flip) under per-chunk
dispatch.

## Research questions

- **Q1 — Regen provenance (evidence: p4 O1 exercise, non-discriminating).**
  For a wholesale-regenerated artifact, should `regen[N]` be provenance-based
  `(file, *)` (any finding in a regenerated file is "written by the fix loop")
  or stay diff-based (only sections whose content changed)? State what each
  reading does to the p4 case (byte-identical outside 3 sections, plus a
  finding in an untouched file) and which reading the evidence in
  `docs/spec/arbitrated-handoff.md`, `loop-control.md` §2a and
  Q-IMPL-HARNESSP3-010 supports. Then specify the **offline fixture shape**
  that discriminates the two readings: inputs (round-N findings, round-N+1
  findings, the regenerated file's before/after, the observed-writes set),
  expected `REVIEW: CONTRADICTION` class per reading, and where the fixture
  lives (`tools/fixtures/`) and what runs it (`tools/sdd-*.py` test or a
  new script). Cost in files touched.

- **Q2 — Stage-level `fix` records and the null chunk (evidence: seq 21, 24,
  27 of p4 session 2; seq 2, 4, 6 for the v1 branch).** Should the **writer**
  stamp `dispatch.chunk` on a stage-level `fix` record whose verifier ran under
  a chunk, or should the **reader** exclude stage-level fixes from per-chunk
  pipeline implication? Which choice keeps `telemetry.md` §Record Schema
  simplest and keeps `--lint`'s cross-field finding meaningful? For the `v: 1`
  records of a session that upgrades mid-cycle: migration marker or documented
  expectation — check against Q-IMPL-HARNESSP4-007's v1 branch and the
  `migration` group. Say which of the six findings each choice closes.

- **Q3 — Who flips the plan to `status: complete` under per-chunk dispatch
  (evidence: p4 implement round 1 review C1).** `sdd-implement` Step 6.4
  flips `plan.md` `status: complete` when the last task closes, but per-chunk
  dispatch gives no leaf ownership of "last". Options: the last-chunk leaf
  (its dispatch prompt says so and `plan.md` is in its write scope); the
  orchestrator in its `proceed` commit (bookkeeping, outside any leaf's
  scope); `sdd-verify` on entry. Weigh against commit ownership
  (`write-scope.md` §7), the `COMMIT:` comparand, and phase detection's
  completion-signal rule. Cost in files touched; classify.

## Decided at DISCUSS (not research — requirements inherit these)

- ARB closure is by spec decision plus offline fixture; no live re-run.
- `descoped` is added as a legal `Verified` value; its use is limited to rows
  carried from a previous workstream that the DONE rule could not close.
- Size housekeeping target is lint warn-clean: all three skills under 400
  lines, `telemetry.md` split; REQ-LINT-003 baseline becomes "none".
- L2 (cross-layer convergence as a gate signal) stays deferred; the p4
  evidence (defect class caught 4× by review, 1× by lint) is recorded for a
  later cycle, not acted on here.
- DONE rule: every requirement traced by this workstream `pass`; nothing
  closes as a deliberate `fail`; an item that cannot be exercised is descoped
  at replan.
- Scope priority for the plan is the order in §Scope, so a `stop` partway
  leaves the arbitration closure and telemetry fixes landed first.

## Success criteria

- Q1, Q2 and Q3 each answered with a recommendation, its evidence, and the
  cost in files touched; each classified mechanical (spec/template text), code
  (`tools/*.py`), or design-decision-for-requirements.
- Q1 names a concrete fixture shape that yields different outcomes under the
  two readings on the p4 case.
- Q2 maps each of the six telemetry findings to the change that closes it.
- The findings restate the §Decided list unchanged so requirements sees one
  bounded scope.

## Budget

One spike, ≤ 30 tool calls. Desk research over the existing specs, references
and tools. A probe, if needed, runs in a scratch git repository under
`$TMPDIR`, never against this repository's working tree.

## Out of scope

- L2 (cross-layer convergence as a gate signal) — deferred again.
- A second live arbitration exercise.
- Re-opening anything settled by RS-008, RS-HARNESSP2-001, RS-HARNESSP3-001 or
  RS-HARNESSP4-001.
- Touching `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` or the live
  `.sdd/telemetry.jsonl` (the p4 fixture is a copy).
- Any change that adds a durable artifact type under `docs/`, or that lets
  telemetry, reviews or red findings influence phase detection.
- Marker-3 behaviour: unchanged this cycle.
