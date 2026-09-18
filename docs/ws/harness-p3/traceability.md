---
workstream: harness-p3
last_updated: 2026-09-18
---

# Traceability — harness-p3

Rows owned by the `harness-p3` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd-specs`, `sdd-implement` and `sdd-verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited.

`Verified` takes exactly three values (`docs/spec/ws-traceability.md` §Legal
`Verified` Cell Values). The orchestrator's DONE flip ran at the verify gate on
2026-09-18: the 15 `pending-red` cells became `pass`, and REQ-REDB-HARNESSP3-002 —
written `fail` while obligation V1 was undischarged — became `pass` when the
second red round was driven live and rendered its derived `RED:` lines
(`verification.md` §V1).

One cell remains **`fail` deliberately**: REQ-ARB-HARNESSP3-001 (obligation V3).
No fix loop this cycle regenerated its deliverable between review rounds, so the
amended `W_N` was never operative and the requirement is fixture-backed only.
`fail` here means **not verified in this cycle**, not *broken* — the vocabulary
admits no fourth value and the specs are frozen. Carry it to the next cycle.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-ARB-HARNESSP3-001 | arbitrated-handoff.md | harness-p3 | loop-control.md §2a replay fixture (REQ-ARB-HARNESSP3-001) | skills/sdd-orchestrate/references/loop-control.md §2a, §6 | fail |
| REQ-CYCID-HARNESSP3-001 | cycle-identity.md | harness-p3 | Chunk 5 task 7 three-state phase-detection walkthrough (mismatch / absent / no kickoff) — inline; no executable fixture (skill text) | `skills/sdd-verify/SKILL.md` §Phase Detection, Step 6 (`research_id:` stamp), `skills/sdd-{plan,replan,implement,orchestrate}/SKILL.md` §Phase Detection, `CLAUDE.md` §Phase Detection | pass |
| REQ-CYCID-HARNESSP3-002 | cycle-identity.md | harness-p3 | Chunk 5 task 7 plan-completion half of the same walkthrough; `references/loop-control.md` §3 unmodified (diff empty) | `skills/sdd-plan/SKILL.md` (frontmatter template `research_id:`, plan-writing note, §Phase Detection), `CLAUDE.md` §Phase Detection | pass |
| REQ-GC-HARNESSP3-001 | drift-sweep.md | harness-p3 | Chunk 7 task 6 positive control: `qimpl-undefined` still fires on a genuinely undefined local id in a throwaway clone (exit 1), and the same id fenced raises nothing | `CLAUDE.md` §Quality Checks, `skills/sdd-orchestrate/references/drift-sweep.md` §3b (convention; rule unchanged, fence not allowlist) | pass |
| REQ-HARN-HARNESSP3-001 | harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F10 | `tools/sdd-scope-check-selftest.py` (`observe`, `content_hashes`, `ambiguous_set`, `snapshot`), `skills/sdd-orchestrate/references/write-scope.md` §3, §5 | pass |
| REQ-HARN-HARNESSP3-002 | harness-return-contract.md, harness-chunk-verifier.md, adversarial-verify.md | harness-p3 | Chunk 2 task 4 template-conformance walkthrough (inline; no executable fixture — skill text) | `skills/sdd-orchestrate/references/dispatch-templates.md` §CHUNK VERIFIER, §RED TEAM, §REVIEW (fenced bodies) | pass |
| REQ-HARN-HARNESSP3-003 | harness-return-contract.md | harness-p3 | Chunk 2 task 8 replay: prose `budget_consumed` fixtures pause; missing-only-`ledger` fixture warns | `skills/sdd-orchestrate/references/return-contract.md` §1 Parsing and malformed returns | pass |
| REQ-HARN-HARNESSP3-004 | harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F11 | `skills/sdd-orchestrate/references/write-scope.md` §2 (specs row) | pass |
| REQ-HARN-HARNESSP3-005 | harness-return-contract.md | harness-p3 | Chunk 2 task 6 contract read (no executable fixture — packet-shape rule) | `skills/sdd-orchestrate/references/return-contract.md` §3 (Rules, out-of-fix-scope bullet) | pass |
| REQ-REDB-HARNESSP3-001 | harness-return-contract.md, adversarial-verify.md | harness-p3 | Chunk 2 task 8 replay: both observed red breaks narrow past `all`; negative control still routes `all` | `skills/sdd-orchestrate/references/return-contract.md` §5 (step 1'), §3 (`RED_BREAK` table row) | pass |
| REQ-REDB-HARNESSP3-002 | adversarial-verify.md | harness-p3 | Chunk 6 task 8 two-round replay, **plus a live second red round driven at this cycle's verify gate 2026-09-18** rendering `RED: R1 new-ground` and `RED: R6 regression` from re-run `reproduce:` commands (verification.md §V1) | `skills/sdd-orchestrate/references/loop-control.md` §2a Red round (new-ground vs regression), `skills/sdd-orchestrate/SKILL.md` §The gate (signal order 3b, re-run rule) | pass |
| REQ-REDB-HARNESSP3-003 | adversarial-verify.md, ws-traceability.md | harness-p3 | Chunk 6 task 5 read of `tools/sdd-gc.py` `sweep_trace_empty` (no `Verified` vocabulary constraint — no code change) | `skills/sdd-verify/SKILL.md` Step 3b, Step 6; `skills/sdd-orchestrate/SKILL.md` §The gate (flip); `skills/sdd-orchestrate/references/v4-workstreams.md` §Legal `Verified` cell values; `skills/sdd-requirements/SKILL.md`, `skills/sdd-specs/SKILL.md`, `skills/sdd-implement/SKILL.md` | pass |
| REQ-REDB-HARNESSP3-004 | adversarial-verify.md, harness-write-scope.md, milestone-plans.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F13 (no-open-chunk `RED_BREAK` append) | `skills/sdd-plan/SKILL.md` (plan template + note), `skills/sdd-replan/SKILL.md` Step 4 item 7, `skills/sdd-implement/SKILL.md` Step 1 item 2a | pass |
| REQ-SKILL-HARNESSP3-001 | skill-updates.md | harness-p3 | Chunk 5 task 8 carry-or-close walkthrough over two unresolved Minors, repeated under case 3 — inline; no executable fixture (skill text) | `skills/sdd-verify/SKILL.md` Step 6 (carry-or-close rule) | pass |
| REQ-TELEM-HARNESSP3-001 | telemetry.md | harness-p3 | Chunk 4 tasks 5-8 counter walkthroughs (happy increment, unwritable file, failure between successes, mid-cycle opt-out) — inline; no executable fixture (gate text) | `skills/sdd-orchestrate/references/telemetry.md` §3 (four-member family, `telemetry.rec`, walkthrough table) | pass |
| REQ-TELEM-HARNESSP3-002 | telemetry.md | harness-p3 | `tools/sdd-telemetry.py --self-test` (gapless six-record fixture + `seq`-gap fixture + out-of-domain `dispatch.chunk` fixture, R1); Chunk 4 task 4 synthetic-gap run | `tools/sdd-telemetry.py` (`session_rows`, `summarize` `records-vs-expected:` line, `out_of_domain_chunks`/`_chunk_label` — R1), `skills/sdd-orchestrate/references/telemetry.md` §7 | pass |
| REQ-WS-HARNESSP3-001 | ws-traceability.md, harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F12 | `skills/sdd-orchestrate/references/write-scope.md` §2, §7, §9, `skills/sdd-orchestrate/SKILL.md` §The gate, `skills/sdd-orchestrate/references/fan-out.md` §3e, `skills/sdd-{requirements,specs,implement,verify}/SKILL.md` | pass |
