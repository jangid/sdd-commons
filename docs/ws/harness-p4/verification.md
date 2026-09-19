---
workstream: harness-p4
status: pass
research_id: RS-HARNESSP4-001
last_updated: 2026-09-19
plan_ref: docs/ws/harness-p4/plan.md
---

# Verification Report — harness-p4

## Summary

Blue verification of the harness-p4 cycle **passes on every automated gate and
every walked acceptance criterion**, with **no critical and no minor failure**
and no regression against the workstream branch point `0182bf2`. The report is
written `status: pending-red` because the operator enabled the red team at the
verify gate. **Red rounds (orchestrator record, appended at the gate):** two
read-only red leaves ran after this report was written — round 1 attacked 19
criteria (17 HELD) and round 2 attacked 27 criteria across 11 specs (25 HELD);
both returned `RED_VERDICT: BROKEN` on the same two prior-cycle criteria only
(R7 stale size baseline, R8 `SKILL.md` line bound), which the operator
accepted at the round-1 gate (§Issues Found → Minor); round 2 rendered the
derived lines `RED: R7 regression` / `RED: R8 regression` from a re-run of
round 1's `reproduce:` commands. The orchestrator then flipped
`pending-red → pass` at DONE; this leaf never wrote `pass`. Of the 24
traceability rows, 22 read `pending-red` (would-be `pass`) and 2 —
`REQ-ARB-HARNESSP4-001` and the carried `REQ-ARB-HARNESSP3-001` — are
**descoped under the cycle's DONE rule** (the live exercise was
non-discriminating; hand-off item 1), routed to replan and listed under §Next
Steps, never closed `fail`. Their per-ws `Verified` cells are left **empty**
(the descope is recorded only in this report), and the orchestrator's DONE
flip turns **only** `pending-red` cells to `pass` and leaves those two empty —
so the DONE rule's "24 rows `pass`" is reachable only after the replan task
under §Next Steps fills or drops them. Phase detected on entry: plan `status: complete`, all
numbered chunk tasks `[x]`, `research_id: RS-HARNESSP4-001` equal to the
kickoff's; no prior `verification.md` existed at this path, so carry-or-close
had nothing to carry.

## Quality Gates

Every gate the plan's §Conventions names was run in this session (exit codes
recorded verbatim; 9 test runs in total — one per table row; the repair
pass's additional gc run is recorded in the note below the table).

| Gate | Status | Notes |
|------|--------|-------|
| `python3 tools/sdd-skill-lint.py` | pass | exit 0 — `OK: 21 file(s) clean, 3 warning(s)`; the 3 are `[size]` warns (sdd-implement 434, sdd-migrate 464, sdd-orchestrate 551 lines); `[template-drift]` active, no drift |
| `python3 tools/sdd-skill-lint.py --self-test` | pass | exit 0 — `SELF-TEST OK: all rule classes fire` (covers `[template-drift]` §7c and the two `COMMIT:` `REQUIRED` rows) |
| `python3 tools/sdd-scope-check-selftest.py --self-test` | pass | exit 0 — `OK: 22/22 scenarios passed`, F14–F16 and C1–C6 listed by name |
| `python3 tools/sdd-telemetry.py --self-test` | pass | exit 0 — implication-derived expected, frozen fixture expected 39 with sha256 unchanged, `--lint` one mutation per class, `scope.widened` / `commit` group, `--plan` floor, `migrate` (out, in place, idempotent, fixture guard) |
| `python3 tools/sdd-gc.py --self-test` | pass | exit 0 |
| `python3 tools/sdd-gc.py --report` (after the per-ws Verified write) | pass | exit 0 — 8 warnings = 7-warning baseline (4 `[qimpl-broken-ref]`, 3 `[size]`) + the one `[traceability-aggregate]` handshake; no new finding on any `pending-red` cell (hand-off item 5) |
| `shasum -a 256 tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` | pass | `7e20b6307da09355f9aee504c451f0ed59e79ef9a33861cd72f370ea84af9237`, equal to `tools/fixtures/README.md` line 20; re-checked unchanged after every telemetry run in this session |
| `git diff --stat main -- tools/fixtures/` | pass | empty |
| Markdown / frontmatter well-formed | pass | lint's `xlink-dead` and `index-requirements` sweeps clean; every touched artifact parses |

Repair pass (2026-09-19, verify-stage review iteration 1): after the patch
that corrected the O1 rationale, emptied the two ARB `Verified` cells in the
per-ws file, added the ws-traceability / orchestration walks and the
relayed-evidence caveat —
`python3 tools/sdd-gc.py --report` exited 0 with `OK: 9 sweep(s) clean, 8 warning(s), 25 info` (the 7-warning baseline + the one `[traceability-aggregate]` handshake, unchanged from the pre-repair run); the only
finding on the per-ws traceability file remains the single
`[traceability-aggregate]` handshake, and no `trace-empty` finding is raised
on a `Verified`-empty cell.

Baseline note: the `[size]` warning on `skills/sdd-implement/SKILL.md` (434
lines) is **pre-existing at the branch point** (`git show
0182bf2:skills/sdd-implement/SKILL.md | wc -l` = 434, file untouched this
cycle); `skill-lint-v5.md`'s REQ-LINT-003 wording "exactly `sdd-orchestrate`
and `sdd-migrate`" is stale text from an earlier cycle, not a p4 regression —
recorded under §Next Steps.

## Acceptance Criteria

Criteria owned by earlier cycles (p2/p3) that the traced specs still list were
re-run through the shipped self-tests and lint rows that encode them; the p4
criteria were walked individually. Evidence column names the command or the
file:line read.

### harness-commit-fidelity.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `write-scope.md` §7 defines the check, comparand table, two-member token, `amend \| accept \| stop`; one-sentence restatements in `SKILL.md` §The gate, `USAGE.md` §7b, `CLAUDE.md` §Gate vocabulary, `harness-write-scope.md` (REQ-HARN-HARNESSP4-001) | pass | `references/write-scope.md:530` §7a heading + comparand table at :584–585; `SKILL.md:375`; `USAGE.md:331,357`; `CLAUDE.md:138`; `harness-write-scope.md:233` |
| §Gate Signal Order / `loop-control.md` §5 list item 8 post-decision `COMMIT:` and 2b; no other spec restates (REQ-HARN-HARNESSP4-001, -003) | pass | `loop-control.md:504` (2b), `:548` (item 8); `harness-loop-control.md:366,374`; `orchestration.md:617` points, does not restate |
| Walkthrough: 2-of-3 staged → `INCOMPLETE (1 observed, not landed: docs/plan.md)`; fully staged → `COMPLETE (3 paths)`; stray → `landed, not observed`; regeneration commit after feature commit still `COMPLETE` | pass | scope self-test C1, C2, C4 outputs (exact strings rendered) |
| `INCOMPLETE` at the last chunk blocks the review dispatch; `amend` does not re-run scope check | pass | `loop-control.md:548` item 8 text; O3 live: `amend` re-rendered `COMPLETE (10 paths)` with no scope block re-rendered |
| This cycle's `verification.md` records ≥ 1 live gate rendering `COMMIT:` | pass | hand-off item 2 below (O3: nine gates, one forced `INCOMPLETE`) |
| Observed writes sole sequential `expected`; return-drift is a warning not a pause; `docs/extra.md` walkthrough (REQ-HARN-HARNESSP4-002) | pass | `write-scope.md:584,597–598`; `return-contract.md:174,180–182`; `harness-return-contract.md:415` |
| `fan-out.md` §3a.v per-leaf clause incl. `RETURN.commits ⊆ rev-list`, §3b `PRE_MERGE..HEAD`; C3 fast-forward `COMPLETE (2 paths)`; C4 true merge; token family exactly two members (REQ-HARN-HARNESSP4-003) | pass | `fan-out.md:290,295,349,355`; C3/C4 outputs; `grep -rhoE 'COMMIT: [A-Z]+' skills docs/spec CLAUDE.md` → only `COMPLETE` (30) and `INCOMPLETE` (19) |
| scope self-test exits 0 with C1–C5; `git show` mutation of C3 fails with false `INCOMPLETE`; `commit_check` pure (REQ-HARN-HARNESSP4-006) | pass | 22/22 incl. C1–C6; C3's output shows the `git show HEAD` counter-rendering `INCOMPLETE (1 observed, not landed: a.txt)`; mutation-in-temp-copy per plan Chunk 1 task 5 (not re-run here) |
| lint exits 0; gc no new finding on this spec; Markdown well-formed | pass | gates table |

### harness-loop-control.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-HARN-001…008, -027 (caps, `-replan-`, `Budget:`, `BUDGET_EXHAUSTED`, ledger, oscillation, checkpoint, no new file type) | pass | lint `REQUIRED` rows exit 0; `git ls-files docs/` path-type set unchanged (only `docs/ws/<id>/*.md`, `plan-history/*.md` beyond the shared corpus — no telemetry/loop-log type) |
| §Gate Signal Order lists item 8 and 2b and agrees with `loop-control.md` §5; `orchestration.md` points (REQ-ORCH-034 / p4 placement) | pass | spec :366,:374 vs reference :504,:548; `orchestration.md:617` |
| lint 0; Markdown | pass | gates table |

### harness-return-contract.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-HARN-009…013, -018, -019; REQ-HARN-HARNESSP3-002/-003/-005; REQ-REDB-HARNESSP3-001 | pass | lint `REQUIRED` rows (RETURN:, status:, {repair_packet}, VERDICT:) exit 0; `[template-drift]` proves every fenced `RETURN:` body equals its source |
| §Return-Drift Warning defines `files_written − observed` as warning, excluded from `COMMIT:`; `references/return-contract.md` §1 states it; `docs/extra.md` fixture renders warning + `COMPLETE` (REQ-HARN-HARNESSP4-002) | pass | spec :415; reference :174–182; `write-scope.md:597–598` |
| lint 0; Markdown | pass | gates table |

### harness-write-scope.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-HARN-020…026; REQ-HARN-HARNESSP3-001/-004; REQ-WS-HARNESSP3-001; REQ-REDB-HARNESSP3-004 | pass | scope self-test F1–F13 pass (F7 telemetry revert, F10 content hash, F12 aggregate OUT, F13 Post-cycle Fixes); `write-scope.md:215` `-z` porcelain |
| F14 strict set: one path in committed AND content delta rendered once, label `committed`; §3 one-sentence rule (REQ-HARN-HARNESSP4-004) | pass | `PASS F14 … SCOPE: VIOLATION (1 path)`; `write-scope.md:229–233` "Strict set … `committed ≻ content ≻ porcelain`" |
| F15 `R` fixture (both paths in ambiguous set) and F16 space-path (`-z` one record) pass; mutations fail them (REQ-HARN-HARNESSP4-005) | pass | `PASS F15`, `PASS F16`; mutation runs per plan Chunk 6 task 4 (temp copies, not re-run here); shipped 22/22 |
| §Commit Ownership one-sentence pointer to `harness-commit-fidelity.md` | pass | spec :233 |
| lint 0; Markdown | pass | gates table |

### telemetry.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-TELEM-HARNESSP2-001…009, REQ-SKILL-HARNESSP2-001/-008, REQ-TELEM-HARNESSP3-001/-002 (schema, budget units, writer, third observation, non-interference, `FORBIDDEN .sdd/` row, gitignore, `summarize`, `rec <n>` family) | pass | telemetry self-test; lint `FORBIDDEN` row; `.gitignore:36` `.sdd/` and `git check-ignore .sdd/telemetry.jsonl` exit 0; no `docs/ws/*/telemetry*`; no template names `.sdd/` (0 hits in dispatch-templates.md, fan-out.md); `--help` exit 0 |
| §Writer names every kind with verifier / fix / redo clauses; `references/telemetry.md` §2 worked examples; live file at DONE: verifier count = verifiers dispatched, fix = fixes rendered, 0 missing both kinds (REQ-TELEM-HARNESSP4-001) | pass (live part on orchestrator evidence) | `SKILL.md:228–235` "one record per dispatch, for every kind … `v: 2`"; hand-off item 4: session summary verifier 12 / fix 5, 0 missing both kinds |
| Fixture `summarize` prints expected 39 vs 20 (19 missing), implement 14 missing, verifier 11 vs 0, pipeline 11 vs 8, review 6 vs 2, red 1 vs 2 (0 missing); per-(stage,chunk) formulas; §7 headline; Q-IMPL-HARNESSP3-006 amended; zero orchestrator reads (REQ-TELEM-HARNESSP4-002) | pass | run this session on the fixture — every number matches verbatim; `telemetry.md:571,1031`; `loop-control.md` mentions telemetry only as record-class text (:135,:255), never a read |
| `implied.fix 2, recorded 0, missing 0` with seq 2/18 `[mistyped-fix]`, seq 3–5 `[reason-review]`; clause (b); loop-back with no record; `FIX_ONLY_REASONS` const row parsed by `test_schema_table_agrees` (REQ-TELEM-HARNESSP4-003, -004) | pass | fixture `summarize` line `fix : 2 vs 0 (0 missing; 2 mis-typed — see --lint)`; `--lint` on fixture: 2 `[mistyped-fix]`, 3 `[reason-review]`; const row at `docs/spec/telemetry.md:115` and `references/telemetry.md:72` |
| `--lint --file <fixture>` exits non-zero with the named classes; gapless fixture 0; one mutation per class; schema-table agreement; §Record Schema "rendering of the code table" (REQ-TELEM-HARNESSP4-004) | pass | fixture `--lint` exit 1: type 43, cross-field 8, enum 7, key-undeclared 6, mistyped-fix 2, reason-review 3 (66 findings, 3 warnings); `docs/spec/telemetry.md:91`, `references/telemetry.md:47`; self-test |
| Fixture sha `7e20b630…af9237` at DONE, fixtures diff empty; `migrate --out` partial stamp chunks 0–7; `migrate --file <fixture>` exits 2 no write; plan orders migration last; operator ran `migrate` live before verify; `--lint` on migrated records (REQ-TELEM-HARNESSP4-005) | pass | sha and diff in gates table; this session: guard on fixture → exit 2 "refused … no write performed", `--out` under `tools/fixtures/` → exit 2, `tools/fixtures/` unchanged; temp copy → "migrated 8 record(s) of 20", note `partial — migrated from "Chunk 0"`, 0 `dispatch.chunk` lint findings; hand-off item 3 (O2) |
| `scope.widened` int default 0 declared and rendered; `summarize` prints widened dispatches; string → finding; §Writer names the source (REQ-TELEM-HARNESSP4-006) | pass | `docs/spec/telemetry.md:125`; `references/telemetry.md:101`; fixture `widened dispatches: 0`; self-test; O4 live `scope.widened: 1` |
| `commit` group declared and rendered; `summarize` prints `COMMIT: INCOMPLETE` count; `{INCOMPLETE,1,0}` passes, `DROPPED` fails; gate reads git not telemetry; `v: 2` / `v: 1` key sets (REQ-TELEM-HARNESSP4-007) | pass | `references/telemetry.md:543–567`; fixture `COMMIT: INCOMPLETE: 0`; self-test; `loop-control.md` has no telemetry read |
| `v ∈ {1, 2}` admitted, `v: 3` skipped and counted (Q-IMPL-HARNESSP4-002) | pass | self-test "v ∈ {1, 2} admitted (v: 3 skipped)"; `docs/spec/telemetry.md:1047` |
| `--plan` floor 8 (16 with verifier), no shortfall vs 8 recorded, implication still 14 missing (REQ-TELEM-HARNESSP4-008) | pass | run this session: `implement floor: 8 pipeline (16 with verifier); recorded implement records: 8; shortfall: 0`; `implement: 14 missing` |
| §Fixture-Based Test Contract: sha asserted before/after, temp-only outputs | pass | self-test text; every fixture run in this session left the sha unchanged and wrote only under `$TMPDIR` |

### arbitrated-handoff.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-ARB-HARNESSP2-001…008, REQ-SKILL-HARNESSP2-003/-006 (retained tuple, classes b/c, reversals, section resolution F8, pause shape, third opinion, `affects`) | pass | scope self-test F8; lint rows `REVIEW: CONTRADICTION` / `affects` exit 0 |
| §Retained Per-Round State and §Contradiction Classes carry the union; `loop-control.md` §2a schema and `W_N` match (REQ-ARB-HARNESSP3-001 text) | pass | spec :54–64 (`round[N]`, `fix[N]`, `regen[N] … by: leaf \| orchestrator`, `W_N = … UNION …`) vs `loop-control.md:117–161` — same definition |
| Fixture: round 1 approves, regeneration, round 2 Materials in regenerated sections → no pause; untouched file still pauses (REQ-ARB-HARNESSP3-001 fixture) | pass | `loop-control.md:203–211` replay fixture (`M3 … -> in W_1 (by: orchestrator), no pause`; synthetic M4 `k ∉ W_1`) |
| First `APPROVE_WITH_FIXES` fix carries regenerate-wholesale; next round renders `VERDICT:` with **no** `REVIEW: CONTRADICTION`; carried row `pass` at DONE (REQ-ARB-HARNESSP4-001, REQ-ARB-HARNESSP3-001 live) | **descoped** | hand-off item 1: the instruction was carried and the union exercised, but the gate DID render `REVIEW: CONTRADICTION (round 1 vs round 2, class b)` — not demonstrated; descoped at replan under the DONE rule, never `fail` |
| `grep -n 'docs/requirements/traceability.md' loop-control.md` hits the §2a `regen[1]` block with `by: orchestrator`; no bare `traceability.md` in finding lines; lint 0 (REQ-ARB-HARNESSP4-002) | pass | hits at :205 (`regen[1] … by: orchestrator`) and :210 (`M3 — docs/requirements/traceability.md:§(matrix)`); regex for bare `traceability.md` in `- C/Mn:` lines → 0 hits |
| §Retained fenced schema shows `round[N]`, `fix[N]`, `regen[N]` with `W_N`; agrees with §2a; gc no new finding on this spec (REQ-ARB-HARNESSP4-003) | pass | spec :54–64; gc report has no finding on `arbitrated-handoff.md` |
| lint 0 | pass | gates table |

### skill-lint-v5.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-LINT-001…007 (fix on every finding, warn tier, size constants, backtick paths, nine core rows, remaining rows, marker-4 move) | pass (one stale-text note) | `--self-test` exit 0; shipped set exit 0 with 3 size warns — REQ-LINT-003's "exactly sdd-orchestrate and sdd-migrate" is stale wording (sdd-implement at 434 predates this cycle; §Next Steps) |
| `[template-drift]` rule with four-row pair table; one-character flip in the RED TEAM `RETURN:` block → exit 1 naming `adversarial-verify.md`; self-test covers; REQ-HARN-HARNESSP4-007's edit leaves exit 0 (REQ-LINT-HARNESSP4-001) | pass | `tools/sdd-skill-lint.py:248–261` `TEMPLATE_PAIRS`, `:482–497` check; self-test §7c; shipped lint exit 0 after the Chunk 7 fence move |
| `REQUIRED` row `COMMIT: COMPLETE \| INCOMPLETE` in `loop-control.md` and `SKILL.md`; removal exits 1 with the §7 fix; `SCOPE: CLEAN`-only does not satisfy; self-test covers; shipped 0 (REQ-LINT-HARNESSP4-002) | pass | `tools/sdd-skill-lint.py:229–241` (two rows, fix text points at write-scope §7); self-test |
| lint 0; Markdown | pass | gates table |

### harness-chunk-verifier.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-HARN-014…017, four-layer table unchanged, REQ-HARN-HARNESSP3-002 fence contract | pass | `git diff 0182bf2 HEAD -- skills/sdd-review/SKILL.md` → 0 lines; `CLAUDE.md` diff touches no four-layer line (only §Gate vocabulary paragraph and the two completion rows); lint `CHUNK_VERDICT:` rows |
| `grep -n '^  CHUNK_VERDICT:' dispatch-templates.md` empty; `grep -c '^CHUNK_VERDICT:'` ≥ 2; `SKILL.md` §The gate states `^CHUNK_VERDICT:`; the two fences byte-identical under `[template-drift]` (REQ-HARN-HARNESSP4-007) | pass | indented: 0, column-0: 4; `SKILL.md:317` "`^CHUNK_VERDICT:` on the last non-blank line"; lint exit 0 with the rule active; `git diff 1ca92e1 HEAD -- docs/spec` removed-line count = 1 (the fence line, the single Approved-spec contract edit) |
| lint 0; Markdown | pass | gates table |

### cycle-identity.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-CYCID-HARNESSP3-001/-002 (templates emit `research_id:`, three cases in every Phase Detection block, §3 of loop-control unmodified) | pass | `skills/sdd-plan/SKILL.md:197–198`, `skills/sdd-verify/SKILL.md:224–225`; this report's own detection applied the three-case rule |
| Templates show `status:` then `research_id:` consecutively; this cycle's `plan.md` and `verification.md` have it on the next line; lint 0; Q-IMPL-HARNESSP3-014 unchanged (REQ-CYCID-HARNESSP4-001) | pass | grep `-A1` shows both templates consecutive; `plan.md` lines 3–4 and this file's lines 3–4; `git diff 1ca92e1 -- docs/spec/cycle-identity.md` → 0 lines |
| Both `CLAUDE.md` completion rows carry "when a kickoff with one exists"; §Cycle identity three cases unchanged; gc no new finding (REQ-CYCID-HARNESSP4-002) | pass | `grep -c` = 2, both on the §Phase Detection rows (diff shows only those two rows changed); gc baseline |
| No back-fill; no `docs/requirements/**` / `docs/spec/**` file gains a `research_id` | pass | `grep -rn '^research_id:' docs/requirements docs/spec` → one hit, `docs/spec/cycle-identity.md:67`, inside a fenced ` ```yaml ` illustration of the stamp order (not frontmatter) |
| Frontmatter parses; gc | pass | gates table |

### adversarial-verify.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-REDB-HARNESSP2-001…009, REQ-SKILL-HARNESSP2-002/-005, REQ-HARN-HARNESSP3-002, REQ-REDB-HARNESSP3-002/-004 (opt-in red, template slots, return shape, gate order, `pending-red` table, `RED_BREAK`, `## Next Steps` slot, `RED:` derived line, Post-cycle Fixes) | pass | lint `RED_VERDICT:` rows; `[template-drift]` on the red fence; `skills/sdd-orchestrate/SKILL.md:94,385,399` and `skills/sdd-replan/SKILL.md:67` map `pending-red` to verify; this dispatch carried `Red team: enabled` and this report writes `pending-red` |
| Constructed-evidence gate for REQ-REDB-HARNESSP3-002 (real verify stage, `red team: on`, second round) | pass (orchestrator evidence) | two red rounds ran in this verify stage (#30, #33); round 2 rendered one derived `RED: Rn new-ground \| regression` line per BROKEN `Rn` (R7, R8 → `regression`, the round-1 `reproduce:` commands still failing: 3 size warnings, 551 lines) — recorded here by the orchestrator at the gate, not by the leaf |
| §`status: pending-red` and `sdd-verify` Step 3b / Step 6 instruct the `pending-red` cell write; `ws-traceability.md` lists three legal values (REQ-REDB-HARNESSP3-003) | pass | `skills/sdd-verify/SKILL.md:164,346–347`; `ws-traceability.md:183–191`; 22 cells written `pending-red` this session |
| gc raises no new finding **on a `pending-red` cell**; `[traceability-aggregate]` between per-ws write and regeneration is the handshake (REQ-REDB-HARNESSP3-003 / REQ-REDB-HARNESSP4-001) | pass | hand-off item 5 |
| `grep -rn 'pending-red'` across the three files shows the qualified wording and the named handshake in each; this cycle's gc item recorded (REQ-REDB-HARNESSP4-001) | pass | `adversarial-verify.md:405,524`; `ws-traceability.md:203–204,248`; `skills/sdd-verify/SKILL.md:164,346–347`; hand-off item 5 |
| lint 0 | pass | gates table |

### ws-traceability.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| §Legal `Verified` Cell Values states the qualified gc criterion ("no new finding on a `pending-red` cell") and names the `[traceability-aggregate]` handshake warning as expected (spec :248; REQ-REDB-HARNESSP4-001) | pass | `ws-traceability.md:203–204` qualified wording; gc report: one `[traceability-aggregate]` WARN and no finding on any of the 22 `pending-red` cells (hand-off item 5) |
| A requirement id present in two per-workstream files yields two adjacent aggregate rows; the newest-kickoff workstream's row is authoritative (spec :249; Q-IMPL-HARNESSP4-001, REQ-ARB-HARNESSP4-001 cross-reference) | pass | `docs/requirements/traceability.md:208` (`REQ-ARB-HARNESSP3-001 … harness-p3`, history) immediately followed by `:209` (`REQ-ARB-HARNESSP3-001 … harness-p4`, authoritative — the newer kickoff); `:210` is the `REQ-ARB-HARNESSP4-001` row |
| `trace-empty` runs per file unchanged on a duplicated id (spec :249) | pass | `python3 tools/sdd-gc.py --report` after this patch: `OK: 9 sweep(s) clean, 8 warning(s), 25 info` with no `[trace-empty]` line on either `docs/ws/harness-p3/traceability.md` (its `REQ-ARB-HARNESSP3-001` row at `:29`, Spec/Test/Implementation filled, `fail`) or `docs/ws/harness-p4/traceability.md` (its rows at `:36–37`, Spec filled, Test/Implementation/Verified empty) — the sweep flags only an empty Spec cell or Implementation-filled-with-Test-empty (`tools/sdd-gc.py:820,822`), evaluated per file, so the duplicated id neither merges nor cross-flags; `[traceability-aggregate]` is the sole WARN touching traceability |

### orchestration.md

| Criterion | Status | Evidence |
|-----------|--------|----------|
| The p4 paragraph points at `harness-loop-control.md` §Gate Signal Order as the canonical full order (incl. the post-decision `COMMIT:` line) and does not restate it (REQ-HARN-HARNESSP4-001 placement) | pass | `orchestration.md:612–618` — "This spec does not restate it; `COMMIT:` itself is owned by `harness-commit-fidelity.md`" (already cited under harness-commit-fidelity.md row 2) |
- gc qimpl-broken-ref: docs/spec/deviation-protocol.md:108 — Q-IMPL-002 has no **Spec reference** line; add `**Spec reference**: §<section>` naming the section it resolves (pre-existing, recorded at DONE 2026-09-19)
- gc qimpl-broken-ref: docs/spec/ws-ids.md:209 — Q-IMPL-009 **Spec reference** names no heading (§ID-Sorted Insertion); rename the § reference to an existing heading (pre-existing, recorded at DONE 2026-09-19)
- gc qimpl-broken-ref: docs/spec/ws-integration.md:121 — Q-IMPL-014 **Spec reference** names no heading (§3c step 3); rename the § reference to an existing heading (pre-existing, recorded at DONE 2026-09-19)
- gc qimpl-broken-ref: docs/spec/ws-orchestration.md:195 — Q-IMPL-072 **Spec reference** names no heading (§Marker-4 Prose Move guard 2); rename the § reference to an existing heading (pre-existing, recorded at DONE 2026-09-19)

## Verification Hand-off Items (plan §Verification Hand-off)

### 1. Live arbitration exercise (O1) — exercised, not demonstrated → descoped

**Implement-stage evidence (plan §Operator Tasks O1, 2026-09-19).** Stage:
implement (stage review after Chunk 7). Round 1 `APPROVE_WITH_FIXES` (C1, M1,
M2, M3). Fix #1 was dispatched with a regenerate-wholesale
`{deliverable_contract}` for `docs/ws/harness-p4/plan.md`; the leaf rewrote
the file in full, but the rewrite was byte-identical outside three sections,
so diff-based section resolution (`loop-control.md` §2a as written) put only
`§(frontmatter)`, `§Operator Tasks`, `§Completed` into `W_1`. Retained
`regen[1]`: **no sections added** (no orchestrator-regenerated aggregate that
round). Round 2 `APPROVE_WITH_FIXES` raised new Critical/Material ground on
`skills/sdd-orchestrate/SKILL.md §Telemetry` and on the regenerated plan's
untouched `§Conventions` / `§Verification Hand-off`; the gate **did** render
`REVIEW: CONTRADICTION (round 1 vs round 2, class b)`; operator accepted round
2 (fix). Two readings of `W_N`: (i) diff-based, as §2a is written — a
byte-identical regeneration contributes nothing to `W_N`; (ii)
provenance-based, `regen[N] = (file, *)` per Q-IMPL-HARNESSP3-010 — a
wholesale regeneration marks the whole plan file written. **Neither reading
would have spared the pause**: round 2's new ground **also** included
`skills/sdd-orchestrate/SKILL.md §Telemetry`, a file fix #1 (`3772574`) never
touched, and `arbitrated-handoff.md` §Live Exercise keeps the rule armed "for
any file the loop left alone (a finding there still pauses)". The class (b)
pause was therefore forced under **both** readings, and the p4 exercise was
**non-discriminating** for the byte-identical-regeneration question — it could
never have rendered the no-contradiction gate the criterion asks for. Which
reading the contract intends remains a **p5 spec question** (§Next Steps); a
discriminating re-run needs the next round's findings confined to the
regenerated file.

**Earlier research-gate evidence (orchestrator state, 2026-09-18, not on
disk).** Research review round 1 `APPROVE_WITH_FIXES` (C1, M1, M2); fix #1
regenerated `docs/research/RS-HARNESSP4-001-*/findings.md` wholesale; round 2
raised two new Materials on the regenerated file; the gate did **not** raise
`REVIEW: CONTRADICTION` (the fix wrote the ground; no regression). This case
differs from the implement-stage case because the regenerated findings file
had content changes across the file, so diff-based resolution placed the
round-2 keys inside `W_1`. It is consistent with reading (i) but was not the
directed exercise (the regenerate-wholesale instruction was directed from the
plan's review onward, Q-PLAN-P4-1), so it does not discharge the criterion.

**Row status.** `REQ-ARB-HARNESSP4-001` and carried `REQ-ARB-HARNESSP3-001`:
**descoped at replan under the DONE rule** — never `fail`, never `pass` on
this evidence. The per-ws Verified cells are left **empty** — the descope
text lives only in this report (see §Open Questions on the cell vocabulary).
The regenerated aggregate keeps both rows
for `REQ-ARB-HARNESSP3-001` (`harness-p3` history at
`docs/requirements/traceability.md:208`, `harness-p4` authoritative at :209 —
Q-IMPL-HARNESSP4-001).

### 2. Live `COMMIT:` rendering (O3) — REQ-HARN-HARNESSP4-001

Plan §Operator Tasks O3, verbatim: "Observed live 2026-09-19 at the Chunk 0
per-chunk gate: forced omission rendered `COMMIT: INCOMPLETE (1 observed, not
landed: docs/ws/harness-p4/traceability.md)`; `amend` re-rendered
`COMMIT: COMPLETE (10 paths)` with no scope block re-rendered, before the next
dispatch; every later gate rendered `COMMIT: COMPLETE` (5, 6, 6, 5, 3, 3, 5, 8
paths for Chunks 1, 2, 3, 4, 3-redo, 5, 6, 7)." Position: closing line after
the commit and before the next dispatch (item 8). The forced
`INCOMPLETE → amend → COMPLETE` sequence was observed once. No replan trigger
fired (no repeated `INCOMPLETE` for one root cause). **Row: `pending-red`**
(would-be pass).

### 3. `--lint` on the migrated live file (O2) — REQ-TELEM-HARNESSP4-005

Plan §Operator Tasks O2, verbatim: "Run by the operator 2026-09-19 with no
orchestrator session open, on the live file (61 lines, 3 sessions: p3 seq
1–20, p4 session 1 seq 1–13, p4 session 2 seq 1–28). Pre-migration `--lint`:
73 findings, 4 warnings (classes: type 43 incl. the 8 `dispatch.chunk` header
strings on seq 6–13 and null/`"HEAD"`/40-char git heads; enum 7;
key-undeclared 6; cross-field 17; mistyped-fix 3; `[reason-review]` warnings
on seq 1, 3–5). `migrate`: 8 records rewritten in place, marker
`at: 2026-09-19`. Post-migration `--lint`: 65 findings, 4 warnings — exactly
the 8 `dispatch.chunk` findings gone, no `migration` finding, every other
finding identical. `summarize` renders `partial — migrated from "Chunk N"` for
p3 chunks 0–7 and the p3 block still reads 20 recorded / expected 39. Fixture
sha256 `7e20b630…` unchanged; `git diff --stat main -- tools/fixtures/`
empty." The accepted replan-trigger note (null `git.head_*` on seq 6–13 are the
fixture README's documented failure mode, not asserted by the `partial` stamp)
is recorded in the plan and accepted here. Independently confirmed this
session: fixture sha equal to README; fixtures diff empty; `migrate` guard
refuses the fixture path and any `--out` under `tools/fixtures/` (exit 2, no
write). **Row: `pending-red`.**

### 4. Telemetry completeness of this cycle's own session — REQ-TELEM-HARNESSP4-001, -006, -007, -008

`.sdd/` is orchestrator-only and was not read by this leaf. Evidence is the
orchestrator's session summary as relayed in the dispatch and the counts in
the plan's O2 entry — **relayed by the orchestrator; not independently
verifiable by this leaf (`.sdd/` is out of its scope)**: p4 session 2 holds 28 records, seq 1–28 — verifier 12,
fix 5, pipeline 8, review 3; `widened dispatches: 1` (O4); `COMMIT:
INCOMPLETE: 0` (the O3 forced omission was amended before the record's gate
closed); `implied vs recorded` 0 missing for verifier and fix — the live-count part of
this row therefore passes on relayed evidence only, and the shipped `summarize`
still prints one false `missing pipeline` on the `(implement, chunk null)`
group for the live file until the p5 reader fix lands (§Next Steps). One reader
artefact: `summarize` reports a false "missing pipeline" on the
`(implement, chunk null)` group because stage-level `fix` records (seq 21, 24,
27) carry `chunk_verdict` with `chunk: null` while their verifiers were
recorded under chunks 1/3/0 — a writer/reader mismatch, recorded under §Next
Steps as a p5 telemetry item together with the second O2 writer finding (the
session's first three `v: 1` chunk records, seq 2/4/6, tripping the narrowed
equal-heads rule). `--plan` was built (Q-PLAN-P4-2 resolved) and passes on the
fixture; its result on the live file is for the orchestrator's DONE summary.
The descope path (session predating Chunk 2) did **not** apply — the session
wrote verifier and fix records. **Rows: `pending-red`.**

### 5. gc criterion on a `pending-red` cell — REQ-REDB-HARNESSP4-001

Red is **enabled** at this gate, so the qualified criterion applies. After the
per-ws Verified write (22 `pending-red` cells, 2 left empty) and before the
orchestrator's regeneration, `python3 tools/sdd-gc.py --report` exited 0 with
`OK: 9 sweep(s) clean, 8 warning(s), 25 info`: the 7-warning baseline (4
`[qimpl-broken-ref]`, 3 `[size]`) plus exactly one
`WARN docs/requirements/traceability.md: [traceability-aggregate] aggregate
differs from regenerate(docs/ws/*/traceability.md)` — the designed handshake,
not a finding. No finding on any `pending-red` cell. **Pass on the qualified
criterion.**

### 6. Regression base

`merge-base(harness-p4, main)` = `0182bf243cfc9a1a64eaf2c75ec32254774167c5`
(`0182bf2`), first live use of the marker-4 rule; HEAD at verification
`dd396b1`. See §Regressions.

### 7. DONE rule — the 24 rows

22 of 24 rows read `pending-red` (would-be `pass`; flipped to `pass` by the
orchestrator at DONE). 2 rows — `REQ-ARB-HARNESSP4-001`, carried
`REQ-ARB-HARNESSP3-001` — are **descoped at replan** (item 1) and listed under
§Next Steps; their `Verified` cells are **empty** in the per-ws file
(`ws-traceability.md`'s three-value contract is kept — empty is not a fourth
value, and gc `trace-empty` does not flag a `Verified`-empty cell). **No row
reads `fail`.** The DONE flip (`pending-red → pass`) turns **only** the 22
`pending-red` cells to `pass` and leaves the two empty cells untouched, so the
DONE rule's "24 rows `pass`" is **not reachable by the flip alone** — it is
satisfied only after (a) the red verdict and (b) the replan task under §Next
Steps (owner: replan, p5) fills or drops the two cells.

## User-Perspective Validation

| Scenario | Status | Notes |
|----------|--------|-------|
| `sdd-telemetry.py summarize --plan` on the frozen fixture as a post-cycle reader | pass | readable per-stage table, per-kind implication lines, floor line; the `partial` note names what cannot be reconstructed |
| `sdd-telemetry.py --lint` on the fixture (error path) | pass | exit 1, one line per finding tagged by class, warnings separated, summary line names the file |
| `migrate` pointed at the fixture / `--out` under `tools/fixtures/` (guard) | pass | exit 2 with a clear "refused … read-only evidence, no write performed"; directory unchanged |
| `migrate --file <copy> --out <tmp>` then `summarize` / `--lint` on the result | pass | "migrated 8 record(s) of 20 line(s) → … (source untouched)"; partial stamp rendered; 0 `dispatch.chunk` findings |
| `--help` on all four tools | pass | exit 0 |
| Operator reading a gate: `COMMIT:` as the closing line | pass (live, O3) | one `INCOMPLETE` pause with `amend` resolving it, no scope re-render |
| Contradiction pause on a byte-identical regeneration | observed, ambiguous | the pause was correct under §2a's text but surprising to the operator who had directed a wholesale rewrite — the p5 question in §Next Steps |

## Regressions

- One accepted: `skills/sdd-orchestrate/SKILL.md` grew 535 → 551 lines this
  cycle against `skill-lint-v5.md` REQ-LINT-007's ≤ ~450 target (red R8,
  accepted at gate 2026-09-19 — see §Issues Found → Minor; p5 housekeeping).
- Otherwise none. `git diff --stat 0182bf2 HEAD`: 41 files, +6219/−177 — all within
  this workstream's declared surface (shared corpus additions under
  `docs/requirements/**`, `docs/research/**`, `docs/spec/**`; the ws artifacts;
  `skills/sdd-{orchestrate,plan,verify}/**`; the three tools; `CLAUDE.md`).
- `docs/spec/**` contract text: exactly one removed line against `1ca92e1`, the
  Chunk 7 fence line in `harness-chunk-verifier.md` (the planned exception).
- Four-layer text: `skills/sdd-review/SKILL.md` diff empty; `CLAUDE.md`
  four-layer bullet untouched.
- Pre-existing suites: all four self-tests and the lint exit 0; `git ls-files
  docs/` gains no new path type; working tree clean before this leaf's two
  writes.

## Issues Found

### Critical (blocks release)
- None.

### Minor (can ship, fix later)
- No carried issue. (No previous `verification.md` existed at
  `docs/ws/harness-p4/verification.md`, so there was nothing to carry or close.)
- R7 accepted at gate 2026-09-19: `skill-lint-v5.md` REQ-LINT-003 says the size baseline warns on exactly `sdd-orchestrate` and `sdd-migrate`; the shipped run warns on three (`sdd-implement` 434, `sdd-migrate` 464, `sdd-orchestrate` 551) — `sdd-implement` was already 434 at base 0182bf2, so the spec baseline is stale, not a p4 regression; amend the baseline list in a specs pass — reproduce: `python3 tools/sdd-skill-lint.py | grep -c '\[size\]'`
- R8 accepted at gate 2026-09-19: `skill-lint-v5.md` REQ-LINT-007 says `sdd-orchestrate/SKILL.md` ≤ ~450 lines; it is 551 (535 at base 0182bf2; lint exit 0 because the fail tier is 1000) — a p5 housekeeping item, not fixed under the red-team clock — reproduce: `wc -l skills/sdd-orchestrate/SKILL.md`

## Recommendation
- [ ] Ship as-is
- [x] Red rounds done (2, both BROKEN only on accepted R7/R8); flip `pending-red → pass` at DONE; then replan (p5) to settle the two ARB rows (`descoped` vocabulary or removal) — no critical issue; no rework
- [ ] Significant rework needed (invoke sdd-replan)

## Open Questions
- Verified-cell vocabulary for a descoped row: `ws-traceability.md` §Legal
  `Verified` Cell Values admits exactly `pass | fail | pending-red`, but the
  DONE rule forbids `fail` and the hand-off forbids a would-be `pass`
  (`pending-red`) for the two ARB rows. Default taken: the two cells are left
  **empty** in `docs/ws/harness-p4/traceability.md` (no fourth value is
  written into a durable artifact; the descope text lives only in this
  report); gc `trace-empty` does not flag a `Verified`-empty cell, and the
  orchestrator's `pending-red → pass` flip leaves them empty. The replan task
  under §Next Steps (owner: replan, p5) settles whether descoped rows get a
  legal `descoped` value or are removed from the per-ws file.

## Next Steps
- p5 spec question (REQ-ARB): `arbitrated-handoff.md` §`W_N` / `loop-control.md` §2a — diff-based section resolution vs provenance reading `regen[N] = (file, *)` (Q-IMPL-HARNESSP3-010) for a byte-identical wholesale regeneration. The p4 exercise was non-discriminating: round 2's new ground also hit `skills/sdd-orchestrate/SKILL.md §Telemetry`, a file the fix loop left alone, so the pause was forced under both readings; a discriminating re-run needs the next round's findings confined to the regenerated file. `REQ-ARB-HARNESSP4-001` and carried `REQ-ARB-HARNESSP3-001` descoped this cycle on that ground.
- replan (p5), owner: replan: add a legal `descoped` value to `ws-traceability.md` §Legal `Verified` Cell Values or remove `REQ-ARB-HARNESSP4-001` / `REQ-ARB-HARNESSP3-001` from `docs/ws/harness-p4/traceability.md`, then fill or drop the two cells — until then the DONE rule's "24 rows `pass`" is unreachable (hand-off item 7).
- p5 telemetry (reader): `summarize` false "missing pipeline" on the `(implement, chunk null)` group when stage-level `fix` records carry `chunk_verdict` with `chunk: null` (seq 21, 24, 27 of p4 session 2) — decide whether the writer stamps the chunk or the reader excludes stage-level fixes from per-chunk implication.
- p5 telemetry (writer): the first three `v: 1` chunk records of a session that upgrades mid-cycle (seq 2, 4, 6) trip the narrowed equal-heads rule (Q-IMPL-HARNESSP4-007 v1 branch) — either admit a migration marker for them or document as expected.
- `--plan` on the live file: run `python3 tools/sdd-telemetry.py summarize --plan docs/ws/harness-p4/plan.md` at DONE (orchestrator; this leaf does not read `.sdd/`).
- gc: `skill-lint-v5.md` REQ-LINT-003 acceptance text "baseline warns on exactly `sdd-orchestrate` and `sdd-migrate`" is stale — `sdd-implement/SKILL.md` has been over 400 lines since before `0182bf2`; amend the wording or trim the skill.
- gc: the 4 `[qimpl-broken-ref]` warnings in the 7-warning baseline predate this cycle; route at DONE per the orchestrator's `--fix | record | ignore` step.
