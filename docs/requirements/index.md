---
version: "13.0"
last_updated: 2026-09-17
traceability: traceability.md
---

# Requirements Index

## Summary

Requirements for SDD (Spec-Driven Development) skill improvements in the
tools-skills-agents repository. Covers three scopes:

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
| functional | [multi-workstream.md](functional/multi-workstream.md) | WS | REQ-WS-001..030 | Approved | 2026-07-23 |
| functional | [harness-loop-control.md](functional/harness-loop-control.md) | HARN | REQ-HARN-001..008, 027 | Approved | 2026-09-17 |
| functional | [harness-verification.md](functional/harness-verification.md) | HARN | REQ-HARN-009..019 | Approved | 2026-09-17 |
| functional | [harness-boundaries.md](functional/harness-boundaries.md) | HARN | REQ-HARN-020..026, REQ-HARN-HARNESSP2-001 | Approved | 2026-09-17 |
| functional | [arbitrated-handoff.md](functional/arbitrated-handoff.md) | ARB | REQ-ARB-HARNESSP2-001..008 | Approved | 2026-09-17 |
| functional | [adversarial-verify.md](functional/adversarial-verify.md) | REDB | REQ-REDB-HARNESSP2-001..009 | Approved | 2026-09-17 |
| functional | [telemetry.md](functional/telemetry.md) | TELEM | REQ-TELEM-HARNESSP2-001..009 | Approved | 2026-09-17 |
| non-functional | [context-and-compatibility.md](non-functional/context-and-compatibility.md) | CTX, COMPAT | REQ-CTX-001..002, REQ-COMPAT-001..002 | Approved | 2026-05-25 |
| non-functional | [evaluation.md](non-functional/evaluation.md) | EVAL | REQ-EVAL-HARNESSP2-001..004 | Approved | 2026-09-17 |
| integration | [drift-sweep.md](integration/drift-sweep.md) | GC | REQ-GC-HARNESSP2-001..007 | Approved | 2026-09-17 |
| integration | [skill-updates.md](integration/skill-updates.md) | SKILL | REQ-SKILL-001..024, REQ-SKILL-HARNESSP2-001..008 | Approved | 2026-09-17 |
| integration | [skill-lint.md](integration/skill-lint.md) | LINT | REQ-LINT-001..007, REQ-LINT-HARNESSP2-001..002 | Approved | 2026-09-17 |
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
| HARN | Harness Hardening | functional/harness-loop-control.md, functional/harness-verification.md, functional/harness-boundaries.md (one domain, one ID sequence, three files; `HARNESSP2`-prefixed additions in harness-boundaries.md) |
| ARB | Arbitrated Handoff (contradicting review rounds) | functional/arbitrated-handoff.md |
| REDB | Adversarial (Red/Blue) Verify | functional/adversarial-verify.md |
| TELEM | Per-Dispatch Telemetry | functional/telemetry.md |
| CTX | AI Context Budget | non-functional/context-and-compatibility.md |
| COMPAT | Git Compatibility | non-functional/context-and-compatibility.md |
| EVAL | Multi-Run Evaluation | non-functional/evaluation.md |
| GC | Drift Sweep (`tools/sdd-gc.py`) | integration/drift-sweep.md |
| SKILL | Skill Updates | integration/skill-updates.md |
| LINT | Skill Lint (`tools/sdd-skill-lint.py`) | integration/skill-lint.md |
| CFG | Configuration | configuration/version-marker.md |

## Q-REQ Resolutions

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
  carve-out is **not adopted** (REQ-EVAL-HARNESSP2-001, -004).
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
- New skills not derived from the research this corpus traces (RS-002 through
  RS-008)
- Forward planning to v4
- Cross-project review (sdd-review operates on one SDD project at a time)
- Review automation or auto-triggering
- Review of sdd-review's own output (recursive case deferred)
- Non-research orchestrator entry points / starting the loop mid-pipeline (v1)
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
- This repo's v3→v4 migration (stays at marker `3` for this cycle)

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

## See Also

- [Traceability Matrix](traceability.md)
