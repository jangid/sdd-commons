---
status: Approved
last_updated: 2026-05-25
requires:
  - REQ-REV-001
  - REQ-REV-002
  - REQ-REV-003
  - REQ-REV-004
  - REQ-REV-005
  - REQ-REV-006
  - REQ-REV-007
  - REQ-REV-008
---

# External Review

## Context

SDD has three in-session verification layers: chunk-close (mechanical
per-chunk checks), XSPEC (structural type references between specs),
and sdd-verify (holistic acceptance criteria at project end). All three
share a blind spot: they operate within the working session's context
window, inheriting its sunk-cost bias, unstated assumptions, and scope
framing.

External review addresses this by running in a separate session. The
reviewer reads the deliverable fresh — no implementation history, no
context contamination, no defensiveness about prior decisions. Across
two projects (rubric M1, skills repo RS-001 through RS-003), external
review caught critical issues at 4 of 7 phase boundaries where it was
applied, including terminology overload that would have propagated
through all downstream artifacts and scope gaps that spawned entire
research cycles (see RS-004 F1).

This spec defines the review skill: what it checks, how it reports,
when it runs, and what it explicitly does not do.

## Design

### Verification Stack Positioning

| Layer | Scope | When | In-Session? |
|-------|-------|------|-------------|
| Chunk-close | Mechanical: type alignment, traceability, test coverage, Q-IMPL audit | Per-chunk during sdd-implement | Yes |
| XSPEC | Structural: type reference consistency between specs | During sdd-specs Step 4b | Yes |
| sdd-verify | Holistic: aggregate acceptance criteria, quality gates | End of project | Yes |
| **sdd-review** | **Semantic: coherence, scope completeness, readability** | **Phase boundaries** | **No** |

Review's unique value is the combination of semantic judgment and
session isolation. Mechanical checks (does type X exist in impl?)
belong to chunk-close. Structural checks (does spec A's type match
spec B's?) belong to XSPEC. Criteria walkthrough (does criterion C
pass?) belongs to sdd-verify. Review asks: does this deliverable make
sense as a whole, is everything that should be here actually here, and
would an external operator understand it?

### Session Isolation

The skill's opening step, before any artifact reading:

> **Session isolation check.** This skill must run in a session that
> does NOT have prior working context for the project under review.
> If you have been involved in writing, implementing, or deciding on
> the artifacts being reviewed in this session, stop and ask the
> operator to invoke sdd-review in a fresh session.
>
> Confirm one of:
> - (a) This session has no prior context for this project. Proceed.
> - (b) This session has prior context. Stop — the operator should
>   start a new session.

The prompt is a trip-wire for the most common mistake (operator
forgetting to switch sessions). Verification that isolation actually
holds is the operator's responsibility. The skill does not attempt
programmatic context-contamination detection — Claude cannot reliably
detect its own prior context.

### Phase Detection

The reviewer identifies the phase from the artifacts the operator
provides:

| Input pattern | Phase | Checklist |
|---------------|-------|-----------|
| `docs/research/RS-*/findings.md` | Research | §Research Checklist |
| `docs/requirements/**/*.md` | Requirements | §Requirements Checklist |
| `docs/spec/*.md` | Specs | §Specs Checklist |
| `docs/plan.md` (or `docs/plan-*.md`) | Plan | §Plan Checklist |
| `skills/*/SKILL.md` + chunk context | Implementation | §Implement Checklist |
| `docs/verification.md` | Verification | §Verify Checklist |

Detection is input-driven, not project-state-driven. The reviewer
examines what the operator hands over, not what phase the project is
currently in. If the operator provides spec files, the specs checklist
applies regardless of whether the project has moved on to
implementation.

### Required Inputs

For every review, the reviewer needs three things:

1. **Deliverable** — the artifact(s) being reviewed (the phase output)
2. **Prior phase output** — the upstream artifact the deliverable was
   produced from (e.g., requirements when reviewing specs, specs when
   reviewing the plan)
3. **Traceability matrix** — `docs/requirements/traceability.md` for
   coverage checks

The reviewer does NOT receive:
- The working session's conversation history or chain-of-thought
- Kickoff prompts or internal planning notes
- Draft versions or intermediate states

**Why exclude working-session context**: The reviewer's value comes
from a fresh read. Receiving the implementer's reasoning biases the
reviewer toward the implementer's framing rather than forming an
independent assessment.

### Bias Disclosure

When the reviewer has prior involvement with the project — reviewed
earlier phases, provided requirements, participated in design
decisions — the review report opens with a disclosure:

```markdown
## Reviewer Context
- Prior involvement: [nature and extent, e.g., "Reviewed RS-004
  requirements and specs"]
- Potential bias: [what this involvement might cause the reviewer
  to over- or under-scrutinize]
```

When the reviewer has no prior involvement, this section is omitted
entirely. The disclosure is informational — the operator decides how
to weight findings given the disclosed bias.

### Per-Phase Checklists

Each checklist has two categories per RS-004 F2's root-cause finding:
**content correctness** (is what's here right?) and **scope
completeness** (is everything that should be here actually here?).
Three of four systematic review misses across two projects traced to
checking content without checking scope — including the v3 migration
gap that spawned RS-003.

#### Research Checklist

**Content correctness:**
- Findings are evidence-based (citations, prototypes, data) not
  speculative
- Each finding states confidence level with justification
- Recommendation is concrete and actionable

**Scope completeness:**
- All stated research questions have findings (even if "inconclusive")
- Out-of-scope observations are captured (may inform future cycles)
- Budget and scope boundaries are documented

#### Requirements Checklist

**Content correctness:**
- Each requirement is testable (can write a verification for it)
- Priorities (must/should/may) are appropriate for the scope
- IDs follow the project's `REQ-{DOMAIN}-{NNN}` convention
- Q-REQ decisions are documented with rationale

**Scope completeness:**
- Every research finding traces to at least one requirement
- Out-of-scope section explicitly names what's excluded
- No implicit requirements hiding in prose (unstated assumptions)

#### Specs Checklist

**Content correctness:**
- Design rationale explains "why X not Y" for non-obvious decisions
- Acceptance criteria are independently verifiable
- Cross-references to other specs are accurate (file exists, section
  exists)
- Code blocks and examples use the vocabulary defined in the spec

**Scope completeness:**
- Every requirement has spec coverage (check traceability.md Spec
  column)
- Every acceptance criterion traces to at least one requirement
- No orphan specs (every spec traces to requirements via `requires:`)

#### Plan Checklist

**Content correctness:**
- Chunks are reasonably sized (~5-15 hours each)
- Task dependencies are correct (no forward references to unfinished
  work)
- Replan triggers are realistic, not theatrical
- Risks name real concerns with mitigations

**Scope completeness:**
- Every requirement traces through specs to at least one task
- Every spec acceptance criterion will be exercised by some chunk
- Entry/exit criteria are concrete and testable

#### Implement Checklist

**Content correctness:**
- Chunk close report accurately reflects implementation state
- Traceability matrix columns are filled for covered requirements
- Q-IMPL entries match actual implementation decisions

**Scope completeness:**
- Every task in the chunk is completed or explicitly deferred with
  rationale
- No silent scope reductions (work removed without documentation)
- After this chunk ships, what changes for downstream operators?
  Are there migration paths, version markers, or documentation that
  need updating?

#### Verify Checklist

**Content correctness:**
- Every spec acceptance criterion is walked with evidence (not
  "pass" without verification)
- Pass/fail status matches the evidence presented
- Recommendation is concrete and actionable

**Scope completeness:**
- All specs are covered (not just newly-added ones)
- Prior verification reports are referenced where applicable
- Issues are sorted into Critical vs Minor with consistent severity
  criteria

### Report Format

The review produces a structured report presented inline as
conversation output:

```
## Review: [phase] — [project/artifact name]

**Verdict:** Approve | Approve with fixes | Reject

**Strengths:**
- [2-4 substantive items demonstrating thorough reading]

**Critical findings:** [must fix before next phase]
- C1: [what's wrong] — [file:section] — affects [REQ-*]
  Suggested fix: [concrete action]

**Material findings:** [should fix; can proceed with note]
- M1: [what's wrong] — [file:section]

**Minor findings:** [polish; defer without documentation]
- m1: [observation]

**Recommendation:** [specific next action with file/REQ references]
```

**Verdict definitions:**
- **Approve**: No blocking findings. Proceed to next phase.
- **Approve with fixes**: Critical findings exist but are bounded.
  Fix them, then proceed without re-review.
- **Reject**: Significant rework needed. Return to current or
  earlier phase. Consider sdd-replan.

**Strengths section**: Required. Must be substantive — "the staleness
detection chain correctly handles the multi-milestone case" is useful;
"good work" is not. Its purpose is calibration: the reviewer
demonstrates they read the work thoroughly, not just hunted for flaws.

**Non-persistence**: The report is presented as conversation output.
It must not be written to disk as a project artifact. Decisions
informed by the review land in the artifacts themselves (commits,
spec edits, Q-IMPL entries, replan triggers). Operators may manually
archive significant reviews if they choose.

### Trigger Classification

Phase boundaries ranked by historical catch rate (RS-004 F5):

| Trigger | Boundaries | Rationale |
|---------|-----------|-----------|
| **Mandatory** | Requirements→specs, specs→plan | Highest catch rate. Translation between abstraction levels compounds errors. |
| **Recommended** | Plan→implement, post-verification | Catches dependency errors and scope gaps before they're expensive. |
| **Ad-hoc** | Any artifact, any time | Operator invokes on demand for a second opinion. |
| **Skip** | Chunk-close boundaries | Already covered by in-session chunk-close mechanism. |

The skill does not enforce mandatory triggers — it has no mechanism
to block phase transitions. It documents which boundaries are
highest-value so operators know where to invest review time.

## Verification

### Manual
- Confirm the skill includes the session-isolation prompt with
  confirm/stop options
- Confirm all six per-phase checklists are present
- Confirm the report format template matches the structure above
- Run sdd-review against a real phase output and verify the report
  follows the format

### Acceptance Criteria
- [ ] Skill includes opening session-isolation prompt with confirm/stop options (REQ-REV-007)
- [ ] Skill does not attempt programmatic context-contamination detection (REQ-REV-007)
- [ ] Six per-phase checklists present: research, requirements, specs, plan, implement, verify (REQ-REV-001)
- [ ] Each checklist includes both content-correctness and scope-completeness items (REQ-REV-008)
- [ ] Scope-completeness rationale cites RS-004 F2 evidence (REQ-REV-008)
- [ ] Report format specifies verdict (three states), strengths (required), tiered findings, recommendation (REQ-REV-002)
- [ ] Report is presented inline, not persisted to disk (REQ-REV-002)
- [ ] Required inputs enumerated: deliverable, prior phase output, traceability matrix (REQ-REV-003)
- [ ] Inputs explicitly exclude working-session deliberations (REQ-REV-003)
- [ ] Bias disclosure section described with omission rule when no prior involvement (REQ-REV-004)
- [ ] Trigger classification has mandatory/recommended/ad-hoc/skip tiers with specific boundaries (REQ-REV-005)
- [ ] Chunk-close boundaries explicitly excluded from review scope (REQ-REV-005, REQ-REV-006)
- [ ] Scope boundaries against chunk-close, XSPEC, sdd-verify explicit (REQ-REV-006)

## Implementation Questions

### Q-IMPL-HARNESSP2-004: Material finding template line gains `affects`
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Report Format — Material findings template line
**Decision**: Superseded by `arbitrated-handoff.md` §Review Key on Material Lines (REQ-ARB-HARNESSP2-008 amendment 2026-09-17): the Material template line becomes `- M1: [what's wrong] — [file:section] — affects [REQ-*] | affects —`. Nothing else in the report format (REQ-REV-002) or the scope boundaries (REQ-REV-005/006) changes; `sdd-review` gains no red, telemetry or arbitration text.
**Rationale**: The arbitration key must be computable on both tiers; the change is one template line.
**Date**: 2026-09-17 (harness-p2 specs stage)
