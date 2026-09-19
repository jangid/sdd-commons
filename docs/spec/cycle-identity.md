---
status: Approved
last_updated: 2026-09-18
requires:
  - REQ-CYCID-HARNESSP3-001
  - REQ-CYCID-HARNESSP3-002
  - REQ-CYCID-HARNESSP4-001
  - REQ-CYCID-HARNESSP4-002
---

# Cycle Identity in Phase Detection

## Context

Phase detection cannot today tell a **prior** cycle's execution artifacts from
the **current** cycle's. A `verification.md` with `status: pass`, or a `plan.md`
with `status: complete` and every task `[x]`, reads identically whether it was
written by this cycle or the last one — so a finished cycle is misread as the new
one's completion. The harness-p2 plan reads exactly that way today.

`research_id` is the discriminator that already exists, but it is written **only**
into `kickoff.md` (repository grep, 2026-09-18) and consumed only by
`sdd-orchestrate` §Position, `references/loop-control.md`'s
`git log -S'research_id: <id>'` cycle-start-date derivation, and
`references/telemetry.md`'s `cycle.research_id`. This spec stamps it onto the two
execution artifacts that carry a completion signal, and makes every reader compare
before trusting that signal.

Requirements: REQ-CYCID-HARNESSP3-001 (`verification.md`),
REQ-CYCID-HARNESSP3-002 (`plan.md`).

**Evidence class.** The negative claim — that neither artifact carries
`research_id` today — is **spec-read**, from the harness-p2 artifacts'
frontmatter and a repository-wide grep. The stamp-and-compare remedy is
**constructed and unexercised**, so verification must exercise it rather than
assume it.

**Scope.** This adds a frontmatter **field** to two existing artifacts. It is not
a new artifact type, and the field is neither telemetry-, review- nor red-derived,
so it stays inside the harness-p3 kickoff's out-of-scope fence and implies **no
marker bump**.

## Design

### The Stamp

| Artifact | Writer | Source of the value |
|----------|--------|---------------------|
| `verification.md` | `sdd-verify` Step 6 | the active workstream's `kickoff.md` `research_id:` |
| `plan.md` | `sdd-plan`, in its plan-writing step | the same |

Both skills' frontmatter templates emit `research_id:` **on the line
immediately after `status:`** — before `last_updated:` — as Q-IMPL-HARNESSP3-014
pins. The value is copied verbatim; no skill derives or invents one.

[Amended 2026-09-18, harness-p4 — REQ-CYCID-HARNESSP4-001; `docs/ws/harness-p3/verification.md`
§Next Steps R4] Both skills emit the field after `last_updated:` today. The two
**skills are reconciled to the Q-IMPL**, not the Q-IMPL to the skills: the
Q-IMPL is the recorded decision, the comparison is order-independent string
equality (Q-IMPL-HARNESSP3-015) so behaviour is unchanged either way, and one
position lets a reader of any `verification.md` or `plan.md` find the stamp
without searching. Contract:

```yaml
---
status: pass            # or complete (plan.md)
research_id: RS-HARNESSP4-001
last_updated: 2026-09-18
---
```

The Q-IMPL text is unchanged; `skills/sdd-verify/SKILL.md` Step 6 and
`skills/sdd-plan/SKILL.md`'s frontmatter template are the two edits.

### `CLAUDE.md` Completion-Signal Rows Carry the Case-3 Qualifier Inline (REQ-CYCID-HARNESSP4-002)

[Added 2026-09-18, harness-p4 — REQ-CYCID-HARNESSP4-002; `docs/ws/harness-p3/verification.md` §V13]

The two completion-signal rows of `CLAUDE.md` §Phase Detection — the plan
`status: complete` row and the `verification.md` `status: pass` row — carry the
case-3 relief **inline**, so the table is independently correct without the
§Cycle identity paragraph beneath it:

```
… (`status: complete`, all tasks done, **`research_id` matches the kickoff's — when a kickoff with one exists**) …
… (status: pass, **`research_id` matches the kickoff's — when a kickoff with one exists**) …
```

Why: today the qualifier lives only in the paragraph below the table, and a
reader consulting the table alone concludes a repo with no kickoff can never
read its own passing report as verified — the opposite of case 3 (§The
Comparison) and of what `sdd-verify` §Phase Detection implements. The §Cycle
identity paragraph keeps its three cases unchanged; only the two rows gain the
qualifier. `CLAUDE.md` was outside the p3 verify write scope, hence carried.

### The Comparison — Three Exhaustive Cases

Every reader that treats a completion signal as "this cycle is done" must first
compare the artifact's `research_id` to the kickoff's. The completion signals are
`verification.md` `status: pass` and `plan.md` `status: complete` with every task
`[x]`.

| Case | Condition | Reading |
|------|-----------|---------|
| 1. Mismatch | artifact `research_id` differs from the kickoff's | **a previous cycle's artifact** — the stage has not been reached in this cycle |
| 2. Field absent | kickoff exists, artifact carries no `research_id` (legacy) | same reading as a mismatch |
| 3. No usable discriminator | no `docs/ws/<id>/kickoff.md` (marker `4`) / no `docs/handoff/kickoff.md` (marker `3`) — **or** a kickoff that carries no `research_id` | **the comparison is skipped entirely**; the existing `status:`-only rule applies unchanged |

[Amended 2026-09-18, REQ-CYCID-HARNESSP3-001] Case 3's condition reads "no
usable discriminator", widened from "no kickoff present" so that a kickoff
without a `research_id` falls inside it rather than outside the three cases. The
three cases stay **exhaustive** — this widens one case's condition, it does not
add a fourth. A kickoff without the field cannot distinguish cycles, and failing
closed there would block detection in a repo the orchestrator merely started.
Downstream consumers (`docs/spec/skill-updates.md`'s carry-or-close
identification, `docs/spec/telemetry.md`'s `cycle.research_id`) read the same
three cases. Recorded as Q-IMPL-HARNESSP3-016.

Case 3 is load-bearing, not a convenience. `kickoff.md` is written only by
`sdd-orchestrate`, while `CLAUDE.md` explicitly supports invoking an individual
`sdd-*` skill directly — so a repo that never ran the orchestrator must still have
its `status: pass` report read as verified. **Cycle identity is an
orchestrated-cycle discriminator, never a precondition for detection.**

Rationale for case 2 reading as a mismatch: absence is the **safe direction**. It
costs one re-entry into verify per workstream that already has a passing report,
and it never asserts completion that did not happen.

### Marker Independence

The rule is marker-independent: under marker `4` the kickoff is
`docs/ws/<id>/kickoff.md`, under marker `3` it is `docs/handoff/kickoff.md`, and
the comparison is otherwise identical. Under marker `4` the comparison is
resolved per `(repo, workstream)`, like every other phase-detection input.

### Readers That Must State the Comparison

The `§Phase Detection` blocks of `sdd-verify`, `sdd-replan`, `sdd-plan`,
`sdd-implement` and `sdd-orchestrate`, and the detection table in `CLAUDE.md`.

### What Is Explicitly Not Changed

- **No back-fill.** Existing `verification.md` / `plan.md` files are not
  retro-stamped; they fall into case 2 and read as previous-cycle.
- **No cycle identity on the shared corpus.** `docs/requirements/**` and
  `docs/spec/**` are **not** stamped: the shared corpus is cumulative and
  `status: Approved` is a **product-wide** flag (`docs/spec/ws-layout.md`
  §Approval), not a per-cycle one. A cycle boundary is not expressible there and
  stamping one would break sharing. Research findings are already per-spike and
  per-cycle by construction.
- **Nothing is demoted.** The plan's `research_id` is the cycle-identity signal
  for **plan completion** only. `references/loop-control.md` §3's
  `git log -S'research_id: <id>'` command is a different thing: it runs against
  the **kickoff**, is already a legacy fallback behind the kickoff's `date:`
  field, and derives a **cycle-start date** for the replan re-entry cap
  (REQ-HARN-002) — not a cycle identity for plan completion. A `research_id`
  stamp on `plan.md` supplies identity, not a date, so it cannot replace or
  demote that derivation: §3's cap arithmetic is **unmodified** by this spec.

### Downstream Consumer

`docs/spec/skill-updates.md` §harness-p3 (REQ-SKILL-HARNESSP3-001) uses this
comparison to identify "the previous cycle's report" for its carry-or-close rule
on unresolved Minor entries — **including case 3**, where the rule still applies
to whatever report the overwrite is about to replace, identified by its position
on disk alone.

## Verification

### Automated

- `phase_detection_reports_previous_cycle_on_research_id_mismatch` — a
  `verification.md` at `status: pass` whose `research_id` differs from the
  kickoff's is reported by each listed skill as "verify not reached this cycle".
- `phase_detection_reports_verified_on_research_id_match` — a matching pair
  reports "verified".
- `phase_detection_treats_absent_research_id_as_mismatch` — a `status: pass`
  report with no `research_id` behaves as case 1.
- `phase_detection_skips_comparison_when_no_kickoff` — a repo/workstream with no
  `kickoff.md` at all and a `status: pass` report reports "verified"; the
  comparison is **skipped, not failed**.
- `plan_completion_honours_the_same_three_cases` — the four scenarios above,
  applied to `plan.md` `status: complete` with every task `[x]`.
- `loop_control_section_3_unmodified` — a diff of
  `references/loop-control.md` §3 against its pre-change text is empty.

### Manual

- Walk one orchestrated cycle end to end in a workstream that already holds a
  passing report from an earlier cycle, and confirm the verify stage is entered
  rather than skipped. This is the **constructed-evidence** exercise for this
  spec.

### Acceptance Criteria

- [ ] `skills/sdd-verify/SKILL.md`'s frontmatter template and Step 6 emit
      `research_id:` (REQ-CYCID-HARNESSP3-001)
- [ ] `skills/sdd-plan/SKILL.md`'s frontmatter template and its plan-writing step
      emit `research_id:` (REQ-CYCID-HARNESSP3-002)
- [ ] The `§Phase Detection` blocks of `sdd-verify`, `sdd-replan`, `sdd-plan`,
      `sdd-implement` and `sdd-orchestrate`, and the detection table in
      `CLAUDE.md`, state the comparison and its three cases
      (REQ-CYCID-HARNESSP3-001, -002)
- [ ] A mismatched or absent `research_id` reads as a previous cycle's artifact
      for both artifacts; a matching pair reads as this cycle's
      (REQ-CYCID-HARNESSP3-001, -002)
- [ ] A repo/workstream with **no** `kickoff.md` reads a `status: pass` report as
      verified and a `status: complete` plan as complete
      (REQ-CYCID-HARNESSP3-001, -002)
- [ ] `references/loop-control.md` §3 is **unmodified** by this change
      (REQ-CYCID-HARNESSP3-002)
- [ ] The frontmatter templates in `skills/sdd-verify/SKILL.md` and
      `skills/sdd-plan/SKILL.md` show `status:` then `research_id:` on consecutive
      lines; this cycle's `docs/ws/harness-p4/plan.md` and `verification.md` have
      `research_id:` on the line after `status:`; `python3 tools/sdd-skill-lint.py`
      exits 0; Q-IMPL-HARNESSP3-014's text is unchanged (REQ-CYCID-HARNESSP4-001)
- [ ] Both completion-signal rows in `CLAUDE.md` §Phase Detection contain the
      inline qualifier "when a kickoff with one exists"; the §Cycle identity
      paragraph below still carries the three cases unchanged; `python3
      tools/sdd-gc.py --report` raises no new finding (REQ-CYCID-HARNESSP4-002)
- [ ] No existing `verification.md` / `plan.md` is back-filled, and no file under
      `docs/requirements/**` or `docs/spec/**` gains a `research_id`
- [ ] Markdown frontmatter parses in every touched artifact; `python3
      tools/sdd-gc.py --report` raises no new finding

## Edge Cases

- **Kickoff present but carries no `research_id`.** Not an edge case: it is
  inside case 3's condition — see §The Comparison and Q-IMPL-HARNESSP3-016.
- **Two workstreams, one stale.** Under marker `4` the comparison is per
  `(repo, workstream)`, so a mismatch in one workstream never affects another.
- **A cycle that reuses a `research_id`.** Starting a new cycle in a workstream
  without minting a new `research_id` makes the previous cycle's artifacts
  indistinguishable — the same failure this spec closes. Minting a new
  `research_id` per cycle is already `sdd-orchestrate`'s KICKOFF behaviour and is
  a precondition, not a new requirement.

## Cross-Spec Consistency (XSPEC)

**harness-p3 pass (2026-09-18).** No extractable type definitions in
cycle-identity.md — the contract is a frontmatter field and a three-case rule,
reported explicitly rather than passing silently. Reference checks:

- `research_id` is defined here and referenced by `docs/spec/telemetry.md`
  (`cycle.research_id`), `docs/spec/skill-updates.md` (previous-report
  identification) and `references/loop-control.md` §3 (kickoff-only, date
  derivation) — all three uses are consistent with the definition, and §3 is
  explicitly untouched.
- `status: pass` / `status: complete` / `status: pending-red` keep the meanings
  given in `docs/spec/adversarial-verify.md` and the plan-structure contract;
  this spec adds a **second** condition on top of `status`, never a new status
  value.
- The kickoff paths match `docs/spec/ws-layout.md` (marker `4`) and the flat
  marker-`3` layout.

## Implementation Questions

### Q-IMPL-HARNESSP3-014: The field is emitted immediately after `status:` in frontmatter
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The Stamp
**Decision**:

`research_id:` is written as the line following `status:` in both artifacts, so a
reader scanning for the completion signal sees the discriminator adjacent to it.
Position is cosmetic — parsers read the mapping — but a fixed position keeps the
templates and the gc sweep's frontmatter expectations stable.
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP3-015: Readers compare by exact string equality
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The Comparison
**Decision**:

The comparison is byte equality on the trimmed value. No normalisation, case
folding or prefix matching: `research_id` values are minted ids
(`RS-<WS>-NNN`-shaped), and a fuzzy match could silently equate two cycles.
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP3-016: A kickoff without `research_id` is inside case 3, not a fourth case
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The Comparison — Three Exhaustive Cases
**Decision**:

`REQ-CYCID-HARNESSP3-001` declares the three cases exhaustive and states case 3
as "no kickoff present", leaving a kickoff that carries no `research_id`
unclassified. Decision (stated default): widen case 3's condition to "no usable
discriminator" — kickoff absent **or** kickoff present without the field — so
the comparison is skipped and the `status:`-only rule applies. Rationale: the
alternative (treat it as case 2, a mismatch) fails closed and would block
detection in a repo the orchestrator merely started, while the safe-direction
argument for case 2 applies only where a *cycle* was actually stamped. The
change is to a case's condition, not to the number of cases, so exhaustiveness
is preserved for `docs/spec/skill-updates.md`'s carry-or-close consumer.
**Date**: 2026-09-18 (specs stage)
