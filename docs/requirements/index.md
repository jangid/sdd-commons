---
version: "15.0"
status: Approved
last_updated: 2026-09-18
traceability: traceability.md
---

# Requirements Index

## Summary

Requirements for SDD (Spec-Driven Development) skill improvements in the
tools-skills-agents repository. Covers ten scopes:

1. **v2 artifact structure** (RS-001): Research structure, requirements
   splitting, plan management, staleness detection, migration, and per-skill
   updates for the v2 layout.
2. **Workflow improvements** (RS-002): Chunk-close review, Q-IMPL deviation
   protocol, multi-milestone plan iteration, cross-spec consistency, and
   per-skill updates for workflow changes.
3. **v3 migration** (RS-003): Migration path from v2 to v3 — plan vocabulary
   rename, version marker update, backward compatibility, documentation
   consistency.
4. **External review** (RS-004): Formal sdd-review skill for structured
   out-of-session review at phase boundaries — phase detection, report
   format, session isolation, scope-completeness checking.
5. **Orchestration driver** (RS-005): `sdd-orchestrate` driver skill running
   the nine SDD skills as a single-operator loop with per-stage subagent
   review — DISCUSS/KICKOFF/LOOP/DONE phases, dispatch-time isolation,
   non-interactivity contract, human gates, resume via phase detection.
6. **Multi-workstream SDD** (RS-007): concurrent SDD cycles in one repo via a
   v4 layout — execution artifacts under `docs/ws/<id>/`, requirements/specs a
   shared corpus, workstream-prefixed IDs, merge-safe shared writes,
   workstream-scoped staleness, branch-per-workstream → PR integration, v3→v4
   migration, and a ceremony-free implicit `default` workstream for solo use.
7. **Harness hardening** (RS-008): deterministic loop control and decoupled
   verification for the orchestrated loop — fix-loop and replan re-entry caps,
   budgets on every dispatch, attempt ledger with oscillation-aware stuck
   detection, circuit-break checkpoint, structured `RETURN:` block and repair
   packet, machine-parseable `VERDICT:` / `CHUNK_VERDICT:` / `SCOPE:` tokens, a
   fresh chunk-close verifier, declared write scope per dispatch, and lint
   changes (remediation text, warn tier, SKILL.md size check, `references/`
   resolution, new contract markers, marker-4 prose moved to `references/`).
8. **Harness hardening part 2** (RS-HARNESSP2-001, workstream `harness-p2`):
   per-dispatch telemetry in a gitignored root-level `.sdd/telemetry.jsonl`
   that is provably not a loop-position marker (TELEM), an opt-in read-only
   Red/Blue adversarial pass at verify gating the `pass` commit via
   `RED_VERDICT:` and `status: pending-red` (REDB), arbitration of
   contradicting review rounds via a `REVIEW: CONTRADICTION` pause (ARB), a
   docs-scoped `tools/sdd-gc.py` drift sweep run at entry and DONE (GC), a
   defined-not-built evaluation mode with fixed scorer fields and a manual
   N = 3 pilot (EVAL), plus the write-scope catch-up limitation (c)
   (REQ-HARN-HARNESSP2-001), the `sdd-implement` references split (Q-IMPL-083)
   and the corresponding lint rows and per-skill updates.
9. **Harness hardening part 3** (RS-HARNESSP3-001, workstream `harness-p3`):
   the defects and design decisions surfaced by two live exercises of the v5
   harness (the N = 3 pilot and the 2026-09-18 manual red-team run) — a
   content-hash write-scope observation bounded to the already-dirty set
   (HARN), `RETURN:` blocks pinned inside every leaf template body plus one new
   `budget_consumed`-shape pause (HARN), `W_N` unioned with regeneration writes
   so a regenerated deliverable is not false new ground (ARB), a positive
   `TELEMETRY: rec <n>` gate line (TELEM), red-team follow-ups — chunk mapping
   from `failures[].location`, a derived new-ground/regression gate line, a
   `pending-red` `Verified` cell and a `## Post-cycle Fixes` section (REDB) —
   `research_id` stamped onto `verification.md` and `plan.md` so phase
   detection can tell one cycle from the last (CYCID, new domain), the
   orchestrator taking ownership of aggregate-traceability regeneration with
   the dispatched `{write_scope}` slot as the orchestrated/standalone
   discriminator (WS), a no-foreign-`Q-IMPL`-tokens convention (GC) and
   carry-forward of unresolved Minors between cycles (SKILL).
10. **Harness hardening part 4** (RS-HARNESSP4-001, workstream `harness-p4`):
   orchestrator commit fidelity — a load-bearing, post-decision
   `COMMIT: COMPLETE | INCOMPLETE` gate signal comparing observed writes against
   a two-sha `git diff` range, with sequential `expected` = observed writes only,
   fan-out per-leaf and merge-step comparands and an `amend | accept | stop`
   pause (HARN); telemetry completeness and validation — one record per dispatch
   kind, an implication-derived `expected` whose headline is the total shortfall,
   a two-clause fix implication with a mis-typed-fix rule, whole-schema `--lint`
   from a single domain table, an ordered in-place stamped-partial migration of
   the 8 p3 records that never touches the frozen fixture, a `scope.widened`
   field, a `commit` record group and an opt-in `--plan` floor (TELEM); the live
   exercise of the carried REQ-ARB-HARNESSP3-001 plus the §2a fixture and
   §Retained Per-Round State repairs (ARB); and housekeeping — `R`/`C` and `-z`
   fixtures, strict-set observed writes, a `[template-drift]` lint rule and a
   `COMMIT:` lint row, terminal tokens at column 0, the `research_id:` stamp
   order, the `pending-red` gc criterion wording and the `CLAUDE.md`
   completion-row qualifier (HARN, LINT, CYCID, REDB).

## Stakeholders

- **Pankaj Jangid** — skills owner and operator. Used all SDD skills across
  the rubric M1 cycle (7 chunks, ~46h). Provided friction observations.

## Files

| Category | File | Domain | Requirements | Status | Last Updated |
|----------|------|--------|-------------|--------|--------------|
| functional | [research-structure.md](functional/research-structure.md) | RS | REQ-RS-001..003 | Approved | 2026-04-28 |
| functional | [requirements-structure.md](functional/requirements-structure.md) | REQ | REQ-REQ-001..007 | Approved | 2026-04-28 |
| functional | [plan-management.md](functional/plan-management.md) | PLAN | REQ-PLAN-001..004 | Approved | 2026-04-28 |
| functional | [staleness-detection.md](functional/staleness-detection.md) | STALE | REQ-STALE-001..003 | Approved | 2026-05-25 |
| functional | [migration.md](functional/migration.md) | MIG | REQ-MIG-001..015 | Approved | 2026-05-25 |
| functional | [chunk-close.md](functional/chunk-close.md) | CHKC | REQ-CHKC-001..008 | Approved | 2026-05-25 |
| functional | [deviation-protocol.md](functional/deviation-protocol.md) | QIMPL | REQ-QIMPL-001..003 | Approved | 2026-05-25 |
| functional | [milestone-plans.md](functional/milestone-plans.md) | MPLAN | REQ-MPLAN-001..004 | Approved | 2026-05-25 |
| functional | [cross-spec-consistency.md](functional/cross-spec-consistency.md) | XSPEC | REQ-XSPEC-001..002 | Approved | 2026-05-25 |
| functional | [review.md](functional/review.md) | REV | REQ-REV-001..008 | Approved | 2026-05-25 |
| functional | [orchestration.md](functional/orchestration.md) | ORCH | REQ-ORCH-001..034 | Approved | 2026-09-17 |
| functional | [multi-workstream.md](functional/multi-workstream.md) | WS | REQ-WS-001..030, REQ-WS-HARNESSP3-001 | Approved | 2026-09-18 |
| functional | [harness-loop-control.md](functional/harness-loop-control.md) | HARN | REQ-HARN-001..008, 027 | Approved | 2026-09-17 |
| functional | [harness-verification.md](functional/harness-verification.md) | HARN | REQ-HARN-009..019, REQ-HARN-HARNESSP3-002..003, -005, REQ-HARN-HARNESSP4-007 | Approved | 2026-09-18 |
| functional | [harness-boundaries.md](functional/harness-boundaries.md) | HARN | REQ-HARN-020..026, REQ-HARN-HARNESSP2-001..002, REQ-HARN-HARNESSP3-001, -004, REQ-HARN-HARNESSP4-001..006 | Approved | 2026-09-18 |
| functional | [arbitrated-handoff.md](functional/arbitrated-handoff.md) | ARB | REQ-ARB-HARNESSP2-001..008, REQ-ARB-HARNESSP3-001, REQ-ARB-HARNESSP4-001..003 | Approved | 2026-09-18 |
| functional | [adversarial-verify.md](functional/adversarial-verify.md) | REDB | REQ-REDB-HARNESSP2-001..009, REQ-REDB-HARNESSP3-001..004, REQ-REDB-HARNESSP4-001 | Approved | 2026-09-18 |
| functional | [telemetry.md](functional/telemetry.md) | TELEM | REQ-TELEM-HARNESSP2-001..009, REQ-TELEM-HARNESSP3-001..002, REQ-TELEM-HARNESSP4-001..008 | Approved | 2026-09-18 |
| functional | [cycle-identity.md](functional/cycle-identity.md) | CYCID | REQ-CYCID-HARNESSP3-001..002, REQ-CYCID-HARNESSP4-001..002 | Approved | 2026-09-18 |
| non-functional | [context-and-compatibility.md](non-functional/context-and-compatibility.md) | CTX, COMPAT | REQ-CTX-001..002, REQ-COMPAT-001..002 | Approved | 2026-05-25 |
| non-functional | [evaluation.md](non-functional/evaluation.md) | EVAL | REQ-EVAL-HARNESSP2-001..004 | Approved | 2026-09-17 |
| integration | [drift-sweep.md](integration/drift-sweep.md) | GC | REQ-GC-HARNESSP2-001..007, REQ-GC-HARNESSP3-001 | Approved | 2026-09-18 |
| integration | [skill-updates.md](integration/skill-updates.md) | SKILL | REQ-SKILL-001..024, REQ-SKILL-HARNESSP2-001..008, REQ-SKILL-HARNESSP3-001 | Approved | 2026-09-18 |
| integration | [skill-lint.md](integration/skill-lint.md) | LINT | REQ-LINT-001..007, REQ-LINT-HARNESSP2-001..002, REQ-LINT-HARNESSP4-001..002 | Approved | 2026-09-18 |
| configuration | [version-marker.md](configuration/version-marker.md) | CFG | REQ-CFG-001 | Approved | 2026-05-25 |

> **ORCH delta note:** The ORCH domain mixes shipped requirements (REQ-ORCH-001..015,
> 017..021, all traced and `pass`) with a freshly-added implement-fan-out delta —
> REQ-ORCH-016 (promoted) and REQ-ORCH-022..028. That delta was added at the
> requirements phase and is **not yet specced or implemented**; its traceability
> Spec/Impl/Verified columns are intentionally blank pending the specs and implement
> phases. The specs phase should treat REQ-ORCH-016 and REQ-ORCH-022..028 as the
> new work to design.

> **WS delta note:** The `WS` domain (REQ-WS-001..030, RS-007) is the
> multi-workstream v4 feature. REQ-WS-001..029 were specced, implemented across
> the 9-chunk plan, and verified (`docs/verification.md`, status: pass);
> REQ-WS-030 (offer migration when the project is behind the latest version) was
> added afterward during dogfooding as a small in-branch enhancement. This
> supersedes the earlier "Forward planning to v4" / "Formal 4 → migration"
> out-of-scope note below, which applied to the RS-002/003 cycle: v4 is the
> shipped work of this cycle.

> **HARN / LINT delta note:** The `HARN` (REQ-HARN-001..027) and `LINT`
> (REQ-LINT-001..007) domains, plus REQ-ORCH-034 and REQ-SKILL-019..024, are the
> RS-008 harness-hardening delta added at the requirements phase on 2026-09-17.
> They are **not yet specced or implemented**; their traceability columns are
> intentionally blank. The specs phase should treat them as the new work to
> design. Standing constraints they must not contradict: REQ-ORCH-004/012/013/014
> and REQ-REV-005/006.

> **harness-p2 delta note (marker 4, workstream `harness-p2`):** the `TELEM`,
> `REDB`, `ARB`, `GC` and `EVAL` domains plus REQ-HARN-HARNESSP2-001,
> REQ-SKILL-HARNESSP2-001..008 and REQ-LINT-HARNESSP2-001..002 are the
> RS-HARNESSP2-001 delta added at the requirements phase on 2026-09-17. Their
> ids carry the `HARNESSP2` workstream token per `docs/spec/ws-ids.md`; their
> traceability rows are owned by `docs/ws/harness-p2/traceability.md` and
> aggregated into `traceability.md`. They are **not yet specced or
> implemented**. Standing constraints they must not contradict: REQ-ORCH-011
> (no auto-advance — the EVAL carve-out is defined, not adopted), REQ-ORCH-013/014,
> REQ-REV-005/006 (red is never review), and REQ-HARN-027 **as amended** (the
> gitignored root-level telemetry file is the one permitted exception; the
> `docs/` invariant is unchanged). Plan ordering constraint: TELEM lands first.

> **harness-p3 delta note (marker 4, workstream `harness-p3`):** the new
> `CYCID` domain plus REQ-HARN-HARNESSP3-001..005, REQ-ARB-HARNESSP3-001,
> REQ-TELEM-HARNESSP3-001..002, REQ-REDB-HARNESSP3-001..004,
> REQ-WS-HARNESSP3-001, REQ-GC-HARNESSP3-001 and REQ-SKILL-HARNESSP3-001 are the
> RS-HARNESSP3-001 delta added at the requirements phase on 2026-09-18. Their ids
> carry the `HARNESSP3` workstream token per `docs/spec/ws-ids.md`. They are
> **not yet specced or implemented**; their traceability columns are
> intentionally blank. Standing constraints they must not contradict:
> REQ-ORCH-011/012/013/014 (no auto-advance, no orchestrator-only work in
> leaves, no new artifact), REQ-REV-005/006 (red is never review), REQ-HARN-019
> (leaves make no ownership judgements), REQ-HARN-027 as amended, and
> REQ-TELEM-HARNESSP2-004 (the orchestrator performs zero reads of the telemetry
> file — REQ-TELEM-HARNESSP3-001's `<n>` is the session counter, not a read).
> **Evidence classes are carried deliberately:** REQ-HARN-HARNESSP3-001 is
> probe-evidenced; REQ-HARN-HARNESSP3-002/-004, REQ-REDB-HARNESSP3-001/-003 and
> REQ-GC-HARNESSP3-001 rest on spec reads; REQ-ARB-HARNESSP3-001's defect is
> spec-read but its remedy, REQ-REDB-HARNESSP3-002, REQ-CYCID-HARNESSP3-001..002
> and REQ-WS-HARNESSP3-001's discriminator are **constructed** and unexercised.
> REQ-REDB-HARNESSP3-002 is the weakest-evidenced and is paired with an open
> question naming where to exercise it. Two of the fifteen inherited items also
> carry code: REQ-HARN-HARNESSP3-001 (self-test fixture F10) and
> REQ-TELEM-HARNESSP3-002 (the optional `summarize` backstop, priority `may`).
> Provenance note: REQ-SKILL-HARNESSP3-001 and REQ-HARN-HARNESSP3-005 were
> raised by the 2026-09-18 run itself rather than carried in from the kickoff's
> Q8 seed list — treat them as new scope, not already-agreed items.

### harness-p3 item coverage (15 inherited items, none dropped)

RS-HARNESSP3-001 §Implications for Design bounds this cycle at **15 items** —
11 question-level plus 4 Q8-IN. Each maps to at least one requirement:

| Spike item | Requirement(s) |
|---|---|
| Q1 write-scope fidelity | REQ-HARN-HARNESSP3-001 |
| Q2(i) pin `RETURN:` in template bodies | REQ-HARN-HARNESSP3-002 |
| Q2(ii) `budget_consumed` shape pauses | REQ-HARN-HARNESSP3-003 |
| Q3 arbitration over regenerated artifacts | REQ-ARB-HARNESSP3-001 |
| Q4 telemetry assurance | REQ-TELEM-HARNESSP3-001 (+ optional REQ-TELEM-HARNESSP3-002) |
| Q5(a) chunk mapping for red breaks | REQ-REDB-HARNESSP3-001 |
| Q5(b) second break behind the first | REQ-REDB-HARNESSP3-002 |
| Q5(c) `Verified` under `pending-red` | REQ-REDB-HARNESSP3-003 |
| Q6 cycle identity in phase detection | REQ-CYCID-HARNESSP3-001, REQ-CYCID-HARNESSP3-002 |
| Q7(a) marker-4 specs write-scope row | REQ-HARN-HARNESSP3-004 |
| Q7(b) aggregate regeneration + discriminator | REQ-WS-HARNESSP3-001 |
| Q8-IN 1 `## Post-cycle Fixes` | REQ-REDB-HARNESSP3-004 |
| Q8-IN 2 foreign `Q-IMPL` tokens in prose | REQ-GC-HARNESSP3-001 |
| Q8-IN 3 minors carried between cycles | REQ-SKILL-HARNESSP3-001 |
| Q8-IN 4 findings for the next dispatch | REQ-HARN-HARNESSP3-005 |

The three **Q8-OUT** rows (one-shot upstream review, the four
`qimpl-broken-ref` warnings, the gc `table_cells()` pipe escape) are deliberately
**not** requirements — see Out of Scope, which records each with its reason.

> **harness-p4 delta note (marker 4, workstream `harness-p4`):**
> REQ-HARN-HARNESSP4-001..007 (001..006 in harness-boundaries.md, 007 in
> harness-verification.md — one per-domain counter across the two files, as for
> `HARNESSP3`), REQ-TELEM-HARNESSP4-001..008, REQ-ARB-HARNESSP4-001..003,
> REQ-LINT-HARNESSP4-001..002, REQ-CYCID-HARNESSP4-001..002 and
> REQ-REDB-HARNESSP4-001 are the RS-HARNESSP4-001 delta added at the requirements
> phase on 2026-09-18 — 23 new requirements, no new domain. Their ids carry the
> `HARNESSP4` workstream token per `docs/spec/ws-ids.md`; their traceability rows
> are owned by `docs/ws/harness-p4/traceability.md`, which also carries the
> **carried** row for REQ-ARB-HARNESSP3-001 (closed `fail` = not exercised in
> p3; REQ-ARB-HARNESSP4-001 directs its live exercise). They are **not yet
> specced or implemented**. Standing constraints they must not contradict:
> REQ-ORCH-011/012/013/014 (no auto-advance, no orchestrator-only work in
> leaves, no new artifact), REQ-HARN-027 as amended (the gitignored telemetry
> file is the only exception), REQ-TELEM-HARNESSP2-004 (zero orchestrator reads
> of the telemetry file — `--lint`, `summarize` and `migrate` are post-cycle
> readers), REQ-TELEM-HARNESSP2-002 (counts and enums, never text — `scope.widened`
> and the `commit` group are counts), and the marker-3 path, which is unchanged.
> **Load-bearing vs non-load-bearing is kept apart on purpose:** `COMMIT:` is
> rendered from git and pauses the gate; telemetry records it but never drives
> it, so the `TELEMETRY: rec <n>` "assert on the next gate" precedent is not
> copied for `COMMIT:`. **Evidence classes:** the `COMMIT:` comparand
> (REQ-HARN-HARNESSP4-001/-003) is probe-evidenced in five scratch-repo cases;
> its post-decision placement and the observed-writes-only rule
> (REQ-HARN-HARNESSP4-002) are constructed; every TELEM count in
> REQ-TELEM-HARNESSP4-002..004 is recomputed from the frozen fixture; the
> housekeeping items rest on the p3 verify session's own reads
> (`docs/ws/harness-p3/verification.md` §V5–V14, R4, R6).

### harness-p4 item coverage (kickoff §Scope and §Decided at DISCUSS, none dropped)

| Kickoff item | Requirement(s) |
|---|---|
| (1) V14 `COMMIT:` signal, two-sha comparand, post-decision placement, `amend \| accept \| stop` | REQ-HARN-HARNESSP4-001, REQ-HARN-HARNESSP4-006, REQ-LINT-HARNESSP4-002, REQ-TELEM-HARNESSP4-007 |
| (1) sequential `expected` = observed writes only | REQ-HARN-HARNESSP4-002 |
| (1) fan-out per-leaf and merge-step comparands | REQ-HARN-HARNESSP4-003 |
| (2) P2 record verifier and fix dispatches | REQ-TELEM-HARNESSP4-001 |
| (2) P2 implication-derived `expected`, explicit headline | REQ-TELEM-HARNESSP4-002 (+ optional floor REQ-TELEM-HARNESSP4-008) |
| (2) mis-typed-fix rule, fix-only reason set | REQ-TELEM-HARNESSP4-003 |
| (2) P3 whole-schema `--lint`, domain table as single source of truth | REQ-TELEM-HARNESSP4-004 |
| (2) P1 in-place stamped-partial migration after P2 and P3, fixture untouched | REQ-TELEM-HARNESSP4-005 |
| (2) L6 `scope.widened` | REQ-TELEM-HARNESSP4-006 |
| (2) `commit` record group (research recommends) | REQ-TELEM-HARNESSP4-007 |
| (3) live exercise of REQ-ARB-HARNESSP3-001 | REQ-ARB-HARNESSP4-001 |
| (4) V6 `R`/`C` fixtures | REQ-HARN-HARNESSP4-005 |
| (4) V7 observed-writes set semantics | REQ-HARN-HARNESSP4-004 |
| (4) V8 `[template-drift]` | REQ-LINT-HARNESSP4-001 |
| (4) R4 `research_id:` stamp order | REQ-CYCID-HARNESSP4-001 |
| (4) R6 V5 criterion wording | REQ-REDB-HARNESSP4-001 |
| (4) V9 terminal token column 0 | REQ-HARN-HARNESSP4-007 |
| (4) V10 §2a fixture repair | REQ-ARB-HARNESSP4-002 |
| (4) V11 §Retained Per-Round State `regen[N]` | REQ-ARB-HARNESSP4-003 |
| (4) V13 `CLAUDE.md` completion-row qualifier | REQ-CYCID-HARNESSP4-002 |
| Decided: DONE rule (every traced requirement `pass`, descope at replan) | REQ-ARB-HARNESSP4-001 (stated), applies to every row |
| Decided: plan priority = §Scope order | recorded for `sdd-plan` in Q-REQ-P4-F below |

## Domain Prefixes

| Prefix | Domain | File |
|--------|--------|------|
| RS | Research Structure | functional/research-structure.md |
| REQ | Requirements Structure | functional/requirements-structure.md |
| PLAN | Plan Management | functional/plan-management.md |
| STALE | Staleness Detection | functional/staleness-detection.md |
| MIG | Migration | functional/migration.md |
| CHKC | Chunk-Close Review | functional/chunk-close.md |
| QIMPL | Q-IMPL Deviation Protocol | functional/deviation-protocol.md |
| MPLAN | Milestone Plan Iteration | functional/milestone-plans.md |
| XSPEC | Cross-Spec Consistency | functional/cross-spec-consistency.md |
| REV | External Review | functional/review.md |
| ORCH | SDD Orchestration Driver | functional/orchestration.md |
| WS | Multi-Workstream SDD | functional/multi-workstream.md |
| HARN | Harness Hardening | functional/harness-loop-control.md, functional/harness-verification.md, functional/harness-boundaries.md (one domain, one ID sequence, three files; `HARNESSP2`-prefixed additions in harness-boundaries.md, `HARNESSP3`-prefixed additions split across harness-verification.md and harness-boundaries.md — the `HARNESSP3` counter is per domain and runs 001..005 across both files; `HARNESSP4` likewise runs 001..007 — 001..006 in harness-boundaries.md, 007 in harness-verification.md) |
| ARB | Arbitrated Handoff (contradicting review rounds) | functional/arbitrated-handoff.md |
| REDB | Adversarial (Red/Blue) Verify | functional/adversarial-verify.md |
| TELEM | Per-Dispatch Telemetry | functional/telemetry.md |
| CYCID | Cycle Identity in Phase Detection | functional/cycle-identity.md |
| CTX | AI Context Budget | non-functional/context-and-compatibility.md |
| COMPAT | Git Compatibility | non-functional/context-and-compatibility.md |
| EVAL | Multi-Run Evaluation | non-functional/evaluation.md |
| GC | Drift Sweep (`tools/sdd-gc.py`) | integration/drift-sweep.md |
| SKILL | Skill Updates | integration/skill-updates.md |
| LINT | Skill Lint (`tools/sdd-skill-lint.py`) | integration/skill-lint.md |
| CFG | Configuration | configuration/version-marker.md |

## Q-REQ Resolutions

Resolved during requirements gathering for RS-HARNESSP4-001 (harness hardening
part 4, workstream `harness-p4`). The spike answered Q1 and Q2 with an
evidence-backed recommendation each and routed six design decisions to this
stage; the §Decided at DISCUSS list is inherited unchanged. Where the spike left
an Open Question, the decision taken here is recorded with its reason:

- **Q-REQ-P4-A** (`COMMIT:` comparand and placement): **ratified** — two-sha
  `git diff --name-only HEAD_gate HEAD_landed` captured before any bookkeeping
  commit, never `git show HEAD`; post-decision closing line of the same gate in
  sequential mode, position 2b at the fan-out per-leaf gate; two members, no
  third (REQ-HARN-HARNESSP4-001/-003). The `TELEMETRY:` next-gate precedent is
  explicitly not copied because `COMMIT:` is load-bearing.
- **Q-REQ-P4-B** (`INCOMPLETE` at the last chunk before the implement review):
  **the pause blocks the review dispatch.** The V14 omission survived two gates
  and a commit and was caught only by a later human read; a review dispatched
  against the un-landed tree reviews the wrong artifact. `amend` does not
  re-run the write-scope check — the amended paths came from the observed set
  and are `IN` by construction (REQ-HARN-HARNESSP4-001; the spike's first two
  Open Questions).
- **Q-REQ-P4-C** (sequential `expected`): **observed writes only.**
  `RETURN.files_written − observed` is a return-drift warning owned by
  `return-contract.md`, never a `COMMIT:` term, so a leaf's return error cannot
  force a false pause (REQ-HARN-HARNESSP4-002).
- **Q-REQ-P4-D** (the `records-vs-expected` headline): **total shortfall of every
  implied append per session** (19 missing / `expected 39` on the p3 fixture),
  with the implement line reporting the full implication count (14) and the
  8 + 3 own-kind reading at most secondary. Reason: `expected` counts appends
  that should exist; any narrower headline understates the file's
  incompleteness, which is the defect P2 exists to expose
  (REQ-TELEM-HARNESSP4-002).
- **Q-REQ-P4-E** (the fix implication): **two clauses** — gate decision and
  fix-only `dispatch.reason` — with the mis-typed-fix rule (a fix present under
  the wrong kind is a `--lint` finding, not a missing append); the fix-only
  reason set `{red_break}` is a domain-table row; p3 `seq` 3–5's `reason: REVIEW`
  at `iteration ≥ 1` stays a **warning**, not a count, because the fixture
  cannot distinguish a mis-recorded fix from a mis-labelled first dispatch and a
  legitimate redo carries the same reason (REQ-TELEM-HARNESSP4-003).
- **Q-REQ-P4-F** (`--lint` domain table as single source of truth): **ratified**
  — the code table is the schema of record; the two telemetry documents render it
  and a self-test asserts agreement. Whether the spec block is generated from the
  code or parsed and diffed is left to specs (REQ-TELEM-HARNESSP4-004). Plan
  ordering constraint inherited from DISCUSS: the plan's chunk order follows the
  kickoff §Scope order — `COMMIT:` first, then TELEM in P2 → P3 → P1 order with the
  migration (REQ-TELEM-HARNESSP4-005) scheduled after -001..-004, then the ARB
  exercise, then housekeeping — so a `stop` partway leaves V14 and telemetry
  landed.
- **Q-REQ-P4-G** (record-field additions): **both adopted** — `scope.widened`
  (`should`, REQ-TELEM-HARNESSP4-006) and the `commit` group (`should`,
  REQ-TELEM-HARNESSP4-007); the `--plan` floor is `may`
  (REQ-TELEM-HARNESSP4-008) with the same queue-in-§Next-Steps fallback as the
  p3 backstop.
- **Q-REQ-P4-H** (R4 — which side moves): **the two skills follow
  Q-IMPL-HARNESSP3-014**, not the reverse; the Q-IMPL is the decision record and
  string equality is order-independent, so only the reader's convenience is at
  stake (REQ-CYCID-HARNESSP4-001).
- **Q-REQ-P4-I** (the carried REQ-ARB-HARNESSP3-001 row): its requirement text is
  **unchanged**; a "carried" note sits beneath it and REQ-ARB-HARNESSP4-001 is
  the requirement that this cycle's `verification.md` records the live
  regeneration loop and its non-pause so the carried row can read `pass`.

Resolved during requirements gathering for RS-HARNESSP3-001 (harness hardening
part 3, workstream `harness-p3`). The spike answered all eight research
questions with a recommendation and an explicit confidence clause; these entries
record where this stage **ratified**, **narrowed** or **closed** one rather than
inheriting it:

- **Q-REQ-A** (Q2(ii) — which `RETURN:` keys pause the gate): **exactly two** —
  `status` (already malformed-checked) and `budget_consumed`, the pair the gate
  arithmetic consumes. The other nine stay a `KEYS MISSING` **warning**, and
  `blocked_writes` — the deliberate borderline case — stays a warning with its
  reasoning recorded in `return-contract.md` §1 so the boundary reads as a
  decision, not a drift (REQ-HARN-HARNESSP3-003). The spike routed this to
  requirements precisely because the boundary is a judgement with no run
  evidence either way.
- **Q-REQ-B** (Q7(b) — the orchestrated-vs-standalone discriminator): **closed
  on the dispatched `{write_scope}` slot**, not on a new flag or an explicit
  PIPELINE instruction line (REQ-WS-HARNESSP3-001). The spike required this be
  closed one way or the other; the slot already exists, so the split costs no
  schema change and a skill never has to know who invoked it.
- **Q-REQ-C** (Q3 — arbitration granularity): the union applies **section
  resolution** (REQ-ARB-HARNESSP2-005) to the regeneration diff, so nothing is
  weakened. Where a regeneration is a true wholesale rewrite, section resolution
  degenerates to `(file, *)` and the existing `(file-level)` pause label
  applies — the spec must say so, so the label is not surprising
  (REQ-ARB-HARNESSP3-001).
- **Q-REQ-D** (Q6 — legacy reports): **confirmed acceptable, no back-fill.**
  Absence of the `research_id` **field**, where a kickoff exists, reads as "a
  previous cycle's report", which is the safe direction; the cost is one
  re-entry into verify per workstream that already holds a passing report, paid
  once (REQ-CYCID-HARNESSP3-001). This is distinct from Q-REQ-I below: a missing
  **field** fails the comparison, a missing **kickoff** skips it.
- **Q-REQ-E** (Q6 — shared corpus): requirements and specs status is **not**
  stamped with cycle identity. `status: Approved` is product-wide
  (`docs/spec/ws-layout.md` §Approval); a cycle boundary is not expressible
  there and stamping one would break sharing. Recorded as an explicit exclusion
  in `functional/cycle-identity.md`.
- **Q-REQ-F** (Q4 — the `summarize` backstop): kept **optional** (`may`,
  REQ-TELEM-HARNESSP3-002), counted inside the Q4 item rather than as a
  sixteenth item, and deferrable to `verification.md` §Next Steps if the plan
  has no room — same treatment as the harness-p2 scorer.
- **Q-REQ-G** (Q5(a) and Q5(b) — red's return shape): **unchanged in both.**
  Chunk narrowing is derived by the orchestrator from `failures[].location`, and
  new-ground-vs-regression is derived by re-running the prior round's
  `reproduce:` — neither adds a field red must fill, so REQ-HARN-019 /
  REQ-ORCH-012 (no ownership judgements in leaves) and REQ-REDB-HARNESSP2-004
  (withholding) both hold.
- **Q-REQ-H** (Q8 — the in/out fence): the four Q8-IN rows are carried as
  requirements (REQ-REDB-HARNESSP3-004, REQ-GC-HARNESSP3-001,
  REQ-SKILL-HARNESSP3-001, REQ-HARN-HARNESSP3-005); the three Q8-OUT rows are
  recorded under Out of Scope below with their reasons and are **not** carried.
  Red's write-revert rule (REQ-REDB-HARNESSP2-003) remains unexercised — noted
  under Open Questions so a future cycle does not mistake "never fired" for
  "verified".
- **Q-REQ-I** (Q6 — the no-kickoff case): **the comparison is skipped, not
  failed.** `kickoff.md` is written only by `sdd-orchestrate`, but `CLAUDE.md`
  supports invoking an individual `sdd-*` skill directly, so where no kickoff
  exists for the `(repo, workstream)` the cycle-identity check does not apply and
  the existing `status:`-only rule stands. Carried as an explicit third case in
  REQ-CYCID-HARNESSP3-001, mirrored in REQ-CYCID-HARNESSP3-002 and in
  REQ-SKILL-HARNESSP3-001's identification of "the previous cycle's report".
  Cycle identity is an orchestrated-cycle discriminator, never a precondition
  for phase detection.
- **Q-REQ-J** (Q6 — `loop-control.md` §3 is not demoted): **no change to the
  replan-cap derivation.** §3's `git log -S'research_id: <id>'` runs against the
  **kickoff**, is already a legacy fallback behind the kickoff's `date:` field,
  and yields a **cycle-start date** for the replan re-entry cap (REQ-HARN-002) —
  not a cycle identity for plan completion. A `research_id` stamp on `plan.md`
  supplies identity, not a date, so it cannot demote §3.
  REQ-CYCID-HARNESSP3-002 now says so explicitly, and the spike's Q6 wording has
  been corrected at source so the imprecision does not re-enter at specs.
- **Q-REQ-K** (Q7(b) — when the aggregate is regenerated): **on every gate
  outcome, before the session ends** — `proceed`, `loop-back-to-fix` and `stop`
  alike — not only on `proceed`. Moving regeneration behind the gate must not
  make a stopped or looped-back stage leave the shared aggregate stale, which
  today's inline leaf regeneration never does. Regeneration is wholesale and
  idempotent, so one per gate costs nothing (REQ-WS-HARNESSP3-001).
- **Q-REQ-L** (Q4 — what `<n>` in `TELEMETRY: rec <n>` counts): **successful
  appends, not `dispatch.seq`.** The two diverge after a `WRITE FAILED` or a
  mid-cycle opt-out, and the append count wins: binding `<n>` to the dispatch
  sequence would have a gate assert an append that never happened, which is the
  exact assurance the line exists to give. `<n>` is a session-scoped counter
  incremented only on a successful append, held beside `dispatch.seq` in
  existing session state — no new artifact, and still zero reads of the
  telemetry file (REQ-TELEM-HARNESSP3-001).

Resolved during requirements gathering for RS-HARNESSP2-001 (harness hardening
part 2, workstream `harness-p2`) — the operator approved the scope (five
deferred ideas + Q-IMPL-083) at the research gate; the defaults below are the
research's stated defaults carried as decided, except where noted:

- **Q-REQ-A** (telemetry default and placement): **on** under orchestrate,
  operator may switch off at KICKOFF; file `.sdd/telemetry.jsonl`, root-level,
  gitignored, one file per repo attributed by `cycle.workstream`; budget recorded
  as enumerated units (REQ-TELEM-HARNESSP2-002, -004, -008). REQ-HARN-027 amended
  in place; REQ-ORCH-004/013/014 unamended.
- **Q-REQ-B** (red default): **off**, opt-in at the verify gate
  (REQ-REDB-HARNESSP2-001); red input withholds `verification.md` by default
  (REQ-REDB-HARNESSP2-004; A/B is an open question).
- **Q-REQ-C** (red exit-rule strictness): **narrowed from the research default.**
  RS-HARNESSP2-001 stated "rely on commit ownership" as its default and
  `pending-red` as the safer variant; this cycle adopts **`status: pending-red`**
  (REQ-REDB-HARNESSP2-008) because the operator's success criterion requires
  that `verification.md` never read `pass` on disk while red is pending, which
  commit ownership alone cannot guarantee across sessions. Commit ownership
  (REQ-HARN-024) remains the second guard. Cost: one `sdd-verify` Step 6 edit
  plus a position-table row.
- **Q-REQ-D** (arbitration default): **on** — it only pauses and consumes no
  iteration (REQ-ARB-HARNESSP2-006); class (a) reversals are not detected;
  class (b) is file-level until section resolution lands
  (REQ-ARB-HARNESSP2-005, needs code, not a spike).
- **Q-REQ-E** (gc cadence): orchestrator at **entry and DONE**; pre-commit
  `--fast` optional (repo choice); scheduled routine rejected
  (REQ-GC-HARNESSP2-005). Findings park in `verification.md` §Next Steps, never
  as plan tasks (REQ-GC-HARNESSP2-006).
- **Q-REQ-F** (evaluation): **not built** beyond the mode definition, the scorer
  field list and a manual N = 3 pilot; the REQ-ORCH-011 evaluation-mode
  carve-out is **not adopted** (REQ-EVAL-HARNESSP2-001, -004). The pilot
  (REQ-EVAL-HARNESSP2-003) is **should**, with the same "ship if the plan has
  room, else queue in `verification.md` §Next Steps" deferral as the scorer
  (REQ-EVAL-HARNESSP2-002): a `must` pilot would make ~1k operator-gated tool
  calls a hard gate on this cycle's verification, and its records live in the
  toy repo's own `.sdd/telemetry.jsonl`, summarized by hand into harness-p2's
  `verification.md`.
- **Q-REQ-G** (write-scope limitation (c)): new `REQ-HARN-HARNESSP2-001` rather
  than an edit of REQ-HARN-026, so the remedy has its own traceability row;
  provisioning at the intended base is the default remedy.

Resolved during requirements gathering for RS-008 (harness hardening) — the
operator approved the scope (12 in-scope ideas) in DISCUSS; the defaults below
are RS-008's stated defaults, carried as decided:

- **Q-REQ-A** (cap values): fix-loop max-iteration cap **3** per stage per
  session; replan re-entry cap **3** per cycle, derived from `-replan-` archives
  since the kickoff date — no persisted counter (REQ-HARN-001, REQ-HARN-002,
  REQ-HARN-003).
- **Q-REQ-B** (SKILL.md size thresholds): **400 lines warn / 1000 lines fail**
  (REQ-LINT-002, REQ-LINT-003). At baseline this warns on `sdd-orchestrate` and
  `sdd-migrate` only.
- **Q-REQ-C** (budget on read-only review dispatches): **yes** — every dispatch
  type, including review and the chunk verifier, carries a `Budget:` slot
  (REQ-HARN-004); cheap and consistent.
- **Q-REQ-D** (who runs chunk-close checks): the **implementer keeps Step 4**
  unchanged; the fresh verifier is an orchestrate-only second executor of Checks
  1, 3 and the gates, never `sdd-review` (REQ-HARN-014; REQ-REV-005/006 hold).
- **Q-REQ-E** (implement dispatch granularity in sequential mode): **per chunk**
  (RS-008 Q2 option (i)) so the verifier, budget and write scope have a natural
  unit; `sdd-implement` itself is unchanged (REQ-HARN-016).
- **Q-REQ-F** (commit ownership and snapshot ordering): pipeline and fix
  re-dispatch → orchestrator commits after the gate; fan-out leaf → leaf commits
  on its branch; review/verifier never commit; snapshots bracket the dispatch
  and exclude the orchestrator's own commit (REQ-HARN-024, REQ-HARN-025).
- **Q-REQ-G** (loop-control state placement): no new artifact — session-scoped
  fix count, derived replan count, ledger in leaf context, checkpoint in the
  plan's existing blocked-task note (REQ-HARN-027; REQ-ORCH-014 satisfied).

Resolved during requirements gathering for RS-006 (implement-stage fan-out):

- **Q-REQ-A** (fan-out feasibility / design): Implement-stage fan-out is now
  **supported** (REQ-ORCH-016 promoted from `may`/deferred to `must`), built as
  **Design B — orchestrator-owned fan-out, one level deep** (REQ-ORCH-022). RS-006
  Q1 proved a dispatched subagent has no subagent-dispatch tool, so the nested
  Design A (implement subagent owns its own fan-out) is infeasible; the
  orchestrator must dispatch the parallel implement subagents itself.
- **Q-REQ-B** (fan-out boundaries & worktrees): Fan out along the plan's
  independent chunk-dependency branches, one git worktree per concurrently-runnable
  chunk-group (REQ-ORCH-016, REQ-ORCH-023).
- **Q-REQ-C** (opt-in vs default): Fan-out is opt-in at the implement gate
  (REQ-ORCH-024); sequential execution remains the default (REQ-ORCH-015 updated).
- **Q-REQ-D** (merge & conflict policy): Worktree branches merge sequentially into
  `main` before the implement-stage review (REQ-ORCH-025); conflicts are resolved
  automatically, with `git merge --abort` + redo-at-orchestrator as the fallback,
  never corrupting already-merged work (REQ-ORCH-026). RS-006 Q3 proved this safe.
- **Q-REQ-E** (subagent git identity): Fan-out subagents commit with inline
  `git -c user.email=... -c user.name=...` flags because the subagent sandbox
  blocks shared `.git/config` writes (REQ-ORCH-027; RS-006 Q2 caveat).
- **Q-REQ-F** (dispatch concurrency): Whether N parallel subagents run truly
  concurrently vs serialized is **unverified** and carried as a `[needs-spike]`
  requirement (REQ-ORCH-028) to resolve at spec/implementation time. The design
  holds either way; only wall-clock speedup is at stake (RS-006 Open Questions).
- **Q-REQ-G** (worktree ownership): **Decision — the orchestrator provisions the
  worktrees** (REQ-ORCH-023), not the fan-out subagents. RS-006 Q2 showed BOTH
  approaches work — an orchestrator-pre-created worktree and a subagent-created
  worktree both succeed — and permitted either; orchestrator ownership was merely
  noted as "cleaner." We harden that preference into a requirement so worktree
  lifecycle and cleanup belong to a single owner (the orchestrator), which keeps
  provisioning and teardown symmetric and avoids orphaned subagent-created
  worktrees. RS-006 permitted either approach; this entry records the deliberate
  narrowing to orchestrator-provisioned.

Resolved during requirements gathering for RS-005:

- **Q-REQ-A** (entry points): Research-entry only for v1 (REQ-ORCH-005). The
  kickoff writer emits a research kickoff and the loop starts at research.
  Mid-pipeline entry deferred — keeps the driver's phase logic minimal and
  matches the dogfooding path.
- **Q-REQ-B** (fan-out scope): Deferred from v1 (REQ-ORCH-015). v1 runs every
  stage sequentially in the main workspace; parallel implement-stage fan-out is
  a follow-on feature. Gets the loop working before adding worktree merge
  complexity that RS-005 flagged as reasoned-not-prototyped.
- **Q-REQ-C** (fan-out boundary rule): _(superseded — see RS-006 Q-REQ-A)_ Pinned
  now even though deferred (REQ-ORCH-016, priority may). Fan out along independent
  branches of the plan's chunk dependency graph; one worktree per
  concurrently-runnable chunk-group; merge sequentially to main before the
  implement-stage review. Documents a settled rule so the later feature inherits a
  design, not a [needs-spike].
- **Q-REQ-D** (resume marker): No new marker, no authoritative loop log
  (REQ-ORCH-014). Resume relies on existing phase detection + staleness; reviews
  are reproduced by re-dispatch. Preserves D5 (kickoff.md the only new artifact).

Resolved during requirements gathering for RS-004:

- **Q-REQ-A** (scope-completeness placement): Separate requirement
  (REQ-REV-008). F2's root-cause finding is cross-cutting — folding it
  into phase checklists risks the lesson being lost. Dedicated requirement
  makes the concern visible.
- **Q-REQ-B** (review persistence): Locked down as non-persistent.
  Reviews are transient working artifacts; decisions land in the artifacts
  themselves (commits, Q-IMPL entries, replan triggers). No `docs/reviews/`
  directory.
- **Q-REQ-C** (session isolation enforcement): Combined approach. Skill
  includes confirmation prompt as opening step; actual isolation is operator
  responsibility. Claude cannot reliably detect its own context
  contamination.

Resolved during requirements gathering for RS-003:

- **Q-REQ-A** (renumbering policy): Preserve original numbering during
  vocabulary rename (M1 → Chunk 1, not Chunk 0). Chunk-close doesn't care
  about N's value; renumbering breaks external references for no functional
  benefit.
- **Q-REQ-B** (version marker semantics): Marker tracks SDD process version,
  not just artifact layout. "3" means v3 conventions available.
- **Q-REQ-C** (overview.md update scope): Promoted into scope. Documentation
  and version marker must be consistent at the moment of version bump.

Resolved during requirements gathering for RS-002:

- **Q-REQ-A** (milestone scoping): Requirements are milestone-agnostic.
  Milestones are a planning concern — plans scope themselves to milestones
  via task tracing to specs and requirements. No milestone field in
  requirements.
- **Q-REQ-B** (chunk-close enforcement): Tiered. Type-name mismatches and
  missing traceability hard-block. Q-IMPL audit and test coverage are
  advisory with operator override.
- **Q-REQ-C** (Q-IMPL vs replan): Keep 3 tiers as self-contained protocol.
  Tier 3 cross-references `sdd-replan` Level 2 but doesn't collapse into it.
- **Q-REQ-D** (external review): Not formalized. Strengthen P1 chunk-close
  checklist instead. External review remains ad-hoc — its value comes from
  being outside the implementing session's context window.

## Out of Scope

- Code changes to skills (implementation phase)
- Redesigning the broader SDD methodology
- _(superseded 2026-09-17 — the corpus now also traces RS-HARNESSP2-001; see
  Research References)_ New skills not derived from the research this corpus
  traces (RS-002 through RS-008, RS-HARNESSP2-001)
- Forward planning to v4
- Cross-project review (sdd-review operates on one SDD project at a time)
- Review automation or auto-triggering
- Review of sdd-review's own output (recursive case deferred)
- _(superseded 2026-09-17 by plan entry, REQ-ORCH-031..033 in
  `functional/orchestration.md`)_ Non-research orchestrator entry points /
  starting the loop mid-pipeline (v1)
- Nested subagent fan-out (Design A) — infeasible: a dispatched subagent has no
  subagent-dispatch tool (RS-006 Q1). Fan-out is orchestrator-owned, one level deep
- Fan-out of any stage other than implement; changes to `sdd-implement` itself
- Persisting review verdicts to disk (no docs/reviews/ — reaffirmed for the driver)
- Two literal human terminal sessions (superseded by the orchestrator + subagent model)
- _(superseded 2026-09-17 by scope item 8 — the five ideas D11, D12, F14, F15,
  G17 from `docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md` are
  now in scope via RS-HARNESSP2-001; D12 only as the mode definition, scorer
  fields and manual pilot)_
- An automated N ≥ 30 headless evaluation harness for the SDD skills
  (REQ-EVAL-HARNESSP2-004) — blocked until (a) telemetry ships and the N = 3
  pilot is recorded, (b) an evaluation-mode carve-out to REQ-ORCH-011 is
  explicitly adopted, and (c) an orchestrator-only outer loop (human or verified
  headless driver) exists
- `sdd-review` as a red team or as any executor of acceptance-criteria breaks
  (REQ-REV-005/006; red is a second executor of `sdd-verify`)
- Semantic contradiction detection between review rounds (class (a) reversals)
  and any persisted review store for arbitration
- Non-mechanical gc sweeps (new skill-text drift from spec wording, semantic
  orphaning) and a scheduled-routine cadence for gc
- A `.sdd/` entry under `docs/ws/<id>/` or any per-workstream telemetry file
- A marker bump (the layout stays at `4`)
- Persisting loop-control counters across sessions (a cap that resets per
  session is the accepted v1; REQ-ORCH-014 holds)
- A hunk-level write-scope check for spec-file `## Implementation Questions`
  edits (path-level + advisory tag in v1, REQ-HARN-026)
- Hard-fixing self-reported `budget_consumed` (harness exposes no counter;
  recorded v1 limitation, REQ-HARN-005)
- A one-shot upstream review before a non-research pipeline entry
  (RS-HARNESSP3-001 Q8-OUT row 5) — **deferred**: mid-pipeline entry is out of
  scope this cycle and orchestrate v1 is research-entry and sequential, so the
  item only pays off once mid-pipeline entry exists. Re-raise in that cycle.
- Clearing the four pre-existing `qimpl-broken-ref` gc warnings
  (RS-HARNESSP3-001 Q8-OUT row 6) — **deferred**: housekeeping, not harness
  behaviour. They are the stable entry baseline (`GC: 0 fail, 6 warn`) the last
  two runs measured drift against; clearing them mid-cycle moves the baseline
  without changing the harness. Route through the `tools/sdd-gc.py --report`
  sweep at a DONE gate as a `record` item.
- A pipe-escape fix in `tools/sdd-gc.py`'s `table_cells()` (RS-HARNESSP3-001
  Q8-OUT row 7) — **declined**: the function mis-splits only a cell containing a
  literal escaped `\|`, no such row has been observed in any run, and the
  failure mode is a cosmetic mis-parse of one row in a `warn`-class sweep.
  Re-open if a real row ever needs an escaped pipe.
- Adding any field to red's `RETURN:` shape (a `supersedes:` / `new-ground:`
  marker on `Rn`, or a narrowest-owning-symbol field) — both declined in favour
  of orchestrator-derived signals (REQ-REDB-HARNESSP3-001/-002).
- A `carry_to_next_dispatch:` field on the repair packet — the existing
  `{deliverable_contract}` slot carries those findings (REQ-HARN-HARNESSP3-005).
- Back-filling `research_id` into existing `verification.md` / `plan.md` files,
  and any marker bump (the layout stays at `4`).
- L2 — a cross-layer **convergence signal** when two or more layers in one cycle
  share a root cause (`docs/ws/harness-p3/verification.md` §L2) — **deferred to
  harness-p5**: no evidence yet on what the signal should look like
  (`docs/ws/harness-p4/kickoff.md` §Out of scope).
- Re-opening anything settled by RS-008, RS-HARNESSP2-001 or RS-HARNESSP3-001;
  a third `COMMIT:` token member for a merge that drops a path (a clean merge
  cannot; the abort-and-redo path re-derives — RS-HARNESSP4-001 §Q1 case 5).
- Modifying `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` in any way —
  it is read-only evidence (REQ-TELEM-HARNESSP4-005; `tools/fixtures/README.md`).
- Letting telemetry, reviews or red findings influence phase detection, and
  any new durable artifact type under `docs/` — both answers of RS-HARNESSP4-001
  read only artifacts and history that already exist.
- Marker-3 behaviour changes.
- _(superseded 2026-09-17 — this repo now runs at marker `4`; see "A marker
  bump (the layout stays at `4`)" above and `functional/multi-workstream.md`)_
  This repo's v3→v4 migration (stays at marker `3` for this cycle)

## Open Questions

- **Subagent nesting (fan-out):** RESOLVED by RS-006 Q1 — a dispatched subagent
  has no subagent-dispatch tool, so nesting is impossible. Fan-out is therefore
  orchestrator-owned, one level deep (Design B; REQ-ORCH-022).
- **Fan-out dispatch concurrency [needs-spike]:** whether the orchestrator can run
  multiple implement subagents truly concurrently (vs. issued-together-but-serialized)
  is unverified (REQ-ORCH-028). The fan-out design is correct either way — only
  wall-clock speedup depends on it. Resolve at spec/implementation time before
  claiming a speedup guarantee. (RS-006 Open Questions; see also RS-005 Q4)

- **Per-chunk implement dispatch cost (RS-008 Q2):** the added wall time / tool
  calls of per-chunk dispatch + chunk verifier versus one implement dispatch is
  unmeasured (needs a live dispatch the research subagent could not perform).
  **Default**: the verifier is default-on under orchestrate (REQ-HARN-014,
  REQ-HARN-016); dogfood one implement stage and revisit opt-in at verify.
- **Write-scope false positives (RS-008 Q5):** the noise rate of the default
  scope table is unmeasured. The table in REQ-HARN-020 was re-walked on
  2026-09-17 against every stage skill's `SKILL.md` (review finding C1 caught
  `sdd-verify`'s Verified-column write), so skill-instructed side-writes are all
  `IN`; residual noise is expected from project files a chunk touches beyond its
  declared source/test globs, not from the skills. **Default**: ship the table
  with the spec-file case `ADVISORY` (REQ-HARN-026); dogfood one real pipeline
  dispatch and tune at verify.

- **Red input A/B (RS-HARNESSP2-001 Q2, dispatch-requiring):** whether giving
  red `verification.md` finds more or fewer breaks is unmeasured. **Default**:
  withhold it (REQ-REDB-HARNESSP2-004); the orchestrator runs red twice on one
  toy verify stage during the N = 3 pilot and records the BROKEN counts.
- **Headless outer driver (RS-HARNESSP2-001 Q5, dispatch-requiring):** whether
  the harness can run `/sdd-orchestrate` non-interactively is unverified from
  a subagent. **Default**: manual-N-only (REQ-EVAL-HARNESSP2-003/-004); no
  requirement depends on the answer this cycle.
- **Probe 1 / probe 2 (RS-HARNESSP2-001 Q6):** the per-chunk dispatch table is
  filled by the orchestrator from this cycle's implement stage; the snapshot
  base used for dispatch #1 decides whether the 20-path `VIOLATION` was the
  catch-up false positive (REQ-HARN-HARNESSP2-001). **Default**: telemetry makes
  probe 1 a query (REQ-TELEM-HARNESSP2-009); limitation (c) is adopted on the
  self-reported evidence regardless.
- **Class (b) false-positive rate (RS-HARNESSP2-001 Q3):** a legitimately new
  Critical the first reviewer missed will pause the loop. **Default**: accepted
  — the pause costs one operator decision and is the intended ROUTE_TO_HUMAN
  behaviour; the rate is telemetered via `verdict.contradiction_class`.
- **`integration/skill-updates.md` size:** the file is 314 lines after the
  harness-p2 additions. Not split this cycle (operator decision, review
  iteration 1); it is a candidate for a `tools/sdd-gc.py` sweep finding once
  REQ-GC-HARNESSP2-001 ships.
- **Traceability row for REQ-HARN-HARNESSP2-002 (orchestrator action):** the
  requirement was added in review iteration 1 under a `docs/requirements/**`
  write scope; the orchestrator must add its row to
  `docs/ws/harness-p2/traceability.md` and regenerate the shared
  `docs/requirements/traceability.md` (`docs/spec/ws-traceability.md`).

Added for RS-HARNESSP3-001 (harness hardening part 3):

- **REQ-REDB-HARNESSP3-002 has no run evidence [needs-exercise]:** the derived
  `RED: <Rn> new-ground | regression` gate line was **constructed** during the
  spike and never probed — the weakest evidential footing of this cycle's
  requirements. **Default**: adopt it as specified; the natural place to
  exercise it is the first harness-p3 verify stage run with `red team: on` that
  reaches a second red round. If that round never happens this cycle, the
  requirement ships spec-only and the gap is recorded in `verification.md`
  §Next Steps rather than silently closed.
- **REQ-ARB-HARNESSP3-001 remedy unexercised:** the defect (class (b) firing by
  construction on a regenerated deliverable) is spec-read and run-corroborated,
  but no run has exercised the unioned `W_N`. **Default**: adopt; the union can
  only remove false positives, never mask a contradiction about a file the loop
  left alone.
- **Whether an operator notices an absent `TELEMETRY: rec <n>` line:** no spec
  read can establish it, and this cycle is also the standing candidate for the
  **first live telemetry cycle in this repo** (open since harness-p2).
  **Default**: telemetry stays default-on at KICKOFF — a run-time choice, not a
  spec change — and the `rec <n>` line is what makes its success observable.
- **Per-workstream traceability rows (orchestrator action):** this stage was
  dispatched with a `docs/requirements/**` write scope, so it added the
  seventeen new rows to the shared aggregate `docs/requirements/traceability.md`
  directly. The orchestrator must create `docs/ws/harness-p3/traceability.md`
  with the same rows (workstream-owned, per `docs/spec/ws-traceability.md`) and
  regenerate the aggregate from it — the same follow-up recorded for
  REQ-HARN-HARNESSP2-002 in the previous cycle. Note this is exactly the
  ownership question REQ-WS-HARNESSP3-001 settles going forward.
- **`integration/skill-updates.md` size:** now ~360 lines (was 314), past the
  300-line split threshold for the second cycle running. **Default**: still not
  split (operator decision carried from harness-p2); it remains a candidate for
  a `tools/sdd-gc.py` sweep finding. The same note now also lives in that file's
  own §Open Questions so the unsplit state reads as a decision from either end;
  revisit at ~500 lines.
- **REQ-REDB-HARNESSP2-003 (red's write-revert rule) is still unexercised:** red
  left a clean worktree in every observed run, so the rule has never fired. Not
  a finding and needs no change — recorded so a future cycle does not mistake
  "never fired" for "verified".

Added for RS-HARNESSP4-001 (harness hardening part 4):

- **`COMMIT:` placement is constructed [needs-exercise]:** the comparand is
  probe-evidenced, but the post-decision pause, its `amend` option and an
  `INCOMPLETE` at the last chunk before the implement review have never been
  rendered in a live orchestrated run. **Default**: adopt as specified
  (Q-REQ-P4-A/-B); this cycle's implement stage is the live exercise and
  REQ-HARN-HARNESSP4-001's acceptance requires at least one live rendering in
  `verification.md`.
- **Marker-4 `merge-base(<ws>, main)` regression rule — first real exercise:**
  `harness-p4` is the first workstream on its own branch, so `sdd-verify`'s
  Step 5 regression base is under load for the first time (p3 §Next Steps).
  Not a requirement of this cycle (settled by RS-007); `verification.md`
  §Assumptions should state the resolved base rather than silently skip it.
- **File sizes past the 300-line advisory split threshold:**
  `functional/telemetry.md` is now ~507 lines and
  `functional/harness-boundaries.md` ~449 (both past the threshold for the
  first time), alongside `integration/skill-updates.md` (~361, carried). The
  dispatch's write scope did not include an operator decision on splitting, so
  the stated default is **not split this cycle** — `TELEM` reads as one schema
  and `HARN` is already three files with one counter; a split is proposed for
  the operator at the stage gate (`telemetry.md` → `telemetry.md` +
  `telemetry-reader.md` carrying the `summarize` / `--lint` / `migrate`
  requirements, same `TELEM` prefix, ids unchanged).
- **Seq 3–5 `reason: REVIEW` records:** whether they are fix dispatches whose
  gate decision was mis-recorded as `proceed` cannot be settled from the fixture
  (Q-REQ-P4-E). **Default**: `--lint` warning only; if this cycle's live file
  shows the same pattern with a known cause, promote the clause at replan.
- **Per-workstream traceability rows:** written this stage to
  `docs/ws/harness-p4/traceability.md` (24 rows: 23 new + the carried
  REQ-ARB-HARNESSP3-001); the shared aggregate `docs/requirements/traceability.md`
  was **not** touched — its absence from the dispatched write scope is the
  REQ-WS-HARNESSP3-001 signal that regeneration is the orchestrator's post-gate
  bookkeeping.
- **Duplicate id across per-ws traceability files (for specs):**
  `REQ-ARB-HARNESSP3-001` has a row in both `docs/ws/harness-p3/traceability.md`
  (`fail`, history) and `docs/ws/harness-p4/traceability.md` (authoritative for
  this cycle — REQ-ARB-HARNESSP4-001). `tools/sdd-gc.py regenerate_aggregate()`
  concatenates and stable-sorts without de-duplication, so the aggregate will
  carry two rows for one id with divergent `Verified` values once p4 writes
  `pass`. Legal under `ws-traceability.md` re-use rows; specs must decide
  whether gc / sdd-verify need a duplicate-id tolerance (newest-workstream row
  wins) or whether the two-row aggregate is simply documented as-is.

All other Q-REQ items resolved.

## Research References

- [RS-001: SDD Artifact Structure](../research/RS-001-sdd-artifact-structure/findings.md)
- [RS-002: SDD Skill Improvements](../research/RS-002-skill-improvements/findings.md)
- [RS-003: v3 Migration Path](../research/RS-003-v3-migration/findings.md)
- [RS-004: sdd-review Skill Design](../research/RS-004-sdd-review/findings.md)
- [RS-005: sdd-orchestrate Feasibility](../research/RS-005-sdd-orchestrate-feasibility/findings.md)
- [RS-006: Subagent Nesting & Worktrees (implement-stage fan-out)](../research/RS-006-subagent-nesting-worktrees/findings.md)
- [RS-007: Multi-Workstream SDD (concurrent cycles in one repo)](../research/RS-007-multi-workstream/findings.md)
- [RS-008: Harness Hardening (loop control, decoupled verification, boundaries)](../research/RS-008-harness-hardening/findings.md)
- [RS-HARNESSP2-001: Harness Hardening, Part 2 (telemetry, adversarial verify, arbitration, drift sweep, evaluation)](../research/RS-HARNESSP2-001-harness-p2/findings.md)
- [RS-HARNESSP4-001: Harness Hardening, Part 4 (`COMMIT:` under fan-out, independent `expected` source for telemetry)](../research/RS-HARNESSP4-001-harness-hardening-p4/findings.md) — with its committed [evidence appendix](../research/RS-HARNESSP4-001-harness-hardening-p4/evidence-appendix.md)
- [RS-HARNESSP3-001: Harness Hardening, Part 3 (write-scope fidelity, return conformance, arbitration over regenerated artifacts, telemetry assurance, red-team follow-ups)](../research/RS-HARNESSP3-001-harness-hardening-p3/findings.md) — with its committed [evidence appendix](../research/RS-HARNESSP3-001-harness-hardening-p3/evidence-appendix.md)

## See Also

- [Traceability Matrix](traceability.md)
