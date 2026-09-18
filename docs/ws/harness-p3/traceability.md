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

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-ARB-HARNESSP3-001 | arbitrated-handoff.md | harness-p3 | loop-control.md §2a replay fixture (REQ-ARB-HARNESSP3-001) | skills/sdd-orchestrate/references/loop-control.md §2a, §6 |  |
| REQ-CYCID-HARNESSP3-001 | cycle-identity.md | harness-p3 | Chunk 5 task 7 three-state phase-detection walkthrough (mismatch / absent / no kickoff) — inline; no executable fixture (skill text) | `skills/sdd-verify/SKILL.md` §Phase Detection, Step 6 (`research_id:` stamp), `skills/sdd-{plan,replan,implement,orchestrate}/SKILL.md` §Phase Detection, `CLAUDE.md` §Phase Detection |  |
| REQ-CYCID-HARNESSP3-002 | cycle-identity.md | harness-p3 | Chunk 5 task 7 plan-completion half of the same walkthrough; `references/loop-control.md` §3 unmodified (diff empty) | `skills/sdd-plan/SKILL.md` (frontmatter template `research_id:`, plan-writing note, §Phase Detection), `CLAUDE.md` §Phase Detection |  |
| REQ-GC-HARNESSP3-001 | drift-sweep.md | harness-p3 |  |  |  |
| REQ-HARN-HARNESSP3-001 | harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F10 | `tools/sdd-scope-check-selftest.py` (`observe`, `content_hashes`, `ambiguous_set`, `snapshot`), `skills/sdd-orchestrate/references/write-scope.md` §3, §5 |  |
| REQ-HARN-HARNESSP3-002 | harness-return-contract.md, harness-chunk-verifier.md, adversarial-verify.md | harness-p3 | Chunk 2 task 4 template-conformance walkthrough (inline; no executable fixture — skill text) | `skills/sdd-orchestrate/references/dispatch-templates.md` §CHUNK VERIFIER, §RED TEAM, §REVIEW (fenced bodies) |  |
| REQ-HARN-HARNESSP3-003 | harness-return-contract.md | harness-p3 | Chunk 2 task 8 replay: prose `budget_consumed` fixtures pause; missing-only-`ledger` fixture warns | `skills/sdd-orchestrate/references/return-contract.md` §1 Parsing and malformed returns |  |
| REQ-HARN-HARNESSP3-004 | harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F11 | `skills/sdd-orchestrate/references/write-scope.md` §2 (specs row) |  |
| REQ-HARN-HARNESSP3-005 | harness-return-contract.md | harness-p3 | Chunk 2 task 6 contract read (no executable fixture — packet-shape rule) | `skills/sdd-orchestrate/references/return-contract.md` §3 (Rules, out-of-fix-scope bullet) |  |
| REQ-REDB-HARNESSP3-001 | harness-return-contract.md, adversarial-verify.md | harness-p3 | Chunk 2 task 8 replay: both observed red breaks narrow past `all`; negative control still routes `all` | `skills/sdd-orchestrate/references/return-contract.md` §5 (step 1'), §3 (`RED_BREAK` table row) |  |
| REQ-REDB-HARNESSP3-002 | adversarial-verify.md | harness-p3 | Chunk 6 task 8 two-round replay of the 2026-09-18 second break (walkthrough only — see plan §Verify-Stage Acceptance Obligations V1) | `skills/sdd-orchestrate/references/loop-control.md` §2a Red round (new-ground vs regression), `skills/sdd-orchestrate/SKILL.md` §The gate (signal order 3b, re-run rule) |  |
| REQ-REDB-HARNESSP3-003 | adversarial-verify.md, ws-traceability.md | harness-p3 | Chunk 6 task 5 read of `tools/sdd-gc.py` `sweep_trace_empty` (no `Verified` vocabulary constraint — no code change) | `skills/sdd-verify/SKILL.md` Step 3b, Step 6; `skills/sdd-orchestrate/SKILL.md` §The gate (flip); `skills/sdd-orchestrate/references/v4-workstreams.md` §Legal `Verified` cell values; `skills/sdd-requirements/SKILL.md`, `skills/sdd-specs/SKILL.md`, `skills/sdd-implement/SKILL.md` |  |
| REQ-REDB-HARNESSP3-004 | adversarial-verify.md, harness-write-scope.md, milestone-plans.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F13 (no-open-chunk `RED_BREAK` append) | `skills/sdd-plan/SKILL.md` (plan template + note), `skills/sdd-replan/SKILL.md` Step 4 item 7, `skills/sdd-implement/SKILL.md` Step 1 item 2a |  |
| REQ-SKILL-HARNESSP3-001 | skill-updates.md | harness-p3 | Chunk 5 task 8 carry-or-close walkthrough over two unresolved Minors, repeated under case 3 — inline; no executable fixture (skill text) | `skills/sdd-verify/SKILL.md` Step 6 (carry-or-close rule) |  |
| REQ-TELEM-HARNESSP3-001 | telemetry.md | harness-p3 | Chunk 4 tasks 5-8 counter walkthroughs (happy increment, unwritable file, failure between successes, mid-cycle opt-out) — inline; no executable fixture (gate text) | `skills/sdd-orchestrate/references/telemetry.md` §3 (four-member family, `telemetry.rec`, walkthrough table) |  |
| REQ-TELEM-HARNESSP3-002 | telemetry.md | harness-p3 | `tools/sdd-telemetry.py --self-test` (gapless six-record fixture + `seq`-gap fixture); Chunk 4 task 4 synthetic-gap run | `tools/sdd-telemetry.py` (`session_rows`, `summarize` `records-vs-expected:` line), `skills/sdd-orchestrate/references/telemetry.md` §7 |  |
| REQ-WS-HARNESSP3-001 | ws-traceability.md, harness-write-scope.md | harness-p3 | `tools/sdd-scope-check-selftest.py` F12 | `skills/sdd-orchestrate/references/write-scope.md` §2, §7, §9, `skills/sdd-orchestrate/SKILL.md` §The gate, `skills/sdd-orchestrate/references/fan-out.md` §3e, `skills/sdd-{requirements,specs,implement,verify}/SKILL.md` |  |
