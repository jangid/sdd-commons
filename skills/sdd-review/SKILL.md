---
name: sdd-review
description: >
  Structured external review at SDD phase boundaries — runs in a separate
  session from the working session to catch coherence gaps, scope omissions,
  and readability issues that in-session verification layers miss. Produces
  an inline verdict with tiered findings. Use at phase transitions, especially
  requirements→specs and specs→plan. Do NOT use for in-session chunk-close
  checks or acceptance criteria walkthroughs.
---

# SDD: External Review

You are reviewing an SDD artifact in a session separate from the working session that produced it. Your job is to read the deliverable fresh, run a phase-specific checklist, and produce a structured review report with a verdict and findings.

## Phase Detection

Identify the phase from the artifacts the operator provides. Detection is input-driven — examine what was handed over, not what phase the project is currently in.

| Input pattern | Phase | Checklist |
|---------------|-------|-----------|
| `docs/research/RS-*/findings.md` | Research | §Research |
| `docs/requirements/**/*.md` | Requirements | §Requirements |
| `docs/spec/*.md` | Specs | §Specs |
| `docs/plan.md` / `docs/plan-*.md` (marker `4`: `docs/ws/<id>/plan.md`) | Plan | §Plan |
| changed source/test files (the implementation diff) + plan/chunk context | Implementation | §Implementation |
| `docs/verification.md` (marker `4`: `docs/ws/<id>/verification.md`) | Verification | §Verification |

If the input doesn't match a pattern, ask the operator which phase applies.

## Your Role

- Read the deliverable without prior context from the working session
- Run the phase-specific checklist (content correctness + scope completeness)
- Produce a structured review report with verdict and tiered findings
- Flag issues in other verification layers' territory and redirect — don't handle them

## Process

### Step 1: Confirm session isolation

**Before reading any artifacts**, confirm isolation.

> **Session isolation check.** This skill must run in a session that does NOT
> have prior working context for the project under review. If you have been
> involved in writing, implementing, or deciding on the artifacts being
> reviewed in this session, stop and ask the operator to invoke sdd-review
> in a fresh session.
>
> Confirm one of:
> - (a) This session has no prior context for this project. Proceed.
> - (b) This session has prior context. Stop — the operator should start
>   a new session.

Do not attempt to detect context contamination programmatically — Claude cannot reliably detect its own prior context. The prompt is a trip-wire for the most common mistake (operator forgetting to switch sessions). Verification that isolation actually holds is the operator's responsibility.

### Step 2: Collect inputs

Request three inputs from the operator:

1. **Deliverable** — the artifact(s) being reviewed (the phase output)
2. **Prior phase output** — the upstream artifact the deliverable was produced from (e.g., requirements when reviewing specs, specs when reviewing the plan)
3. **Traceability matrix** — `docs/requirements/traceability.md` for coverage checks

Do NOT accept as inputs:
- The working session's conversation history or chain-of-thought
- Kickoff prompts or internal planning notes
- Draft versions or intermediate states
- The implementer's reasoning for design choices

If the operator offers prohibited inputs, decline and explain: the reviewer's value comes from a fresh read. Receiving the working session's deliberation biases the reviewer toward the implementer's framing rather than forming an independent assessment.

### Step 3: Detect phase and select checklist

Match the deliverable against the phase detection table above. Read the deliverable and prior phase output. Then run the matching checklist from Step 4.

### Step 4: Run phase-specific checklist

Each checklist checks both **content correctness** (is what's here right?) and **scope completeness** (is everything that should be here actually here?). Three of four systematic review misses across two projects traced to checking content without checking scope — including a migration gap that spawned an entire research cycle (RS-004 F2). Check both.

#### Research

**Content correctness:**
- Check that findings are evidence-based (citations, prototypes, data), not speculative
- Check that each finding states confidence level with justification
- Check that the recommendation is concrete and actionable

**Scope completeness:**
- Check that every research question stated in the deliverable's own `questions:` frontmatter has a finding (even if "inconclusive") — the kickoff is a prohibited input (Step 2); the findings file's frontmatter is the authoritative question list
- Check that out-of-scope observations are captured for future cycles
- Check that budget and scope boundaries are documented

#### Requirements

**Content correctness:**
- Check that each requirement is testable (you could write a verification for it)
- Check that priorities (must/should/may) are appropriate for the scope
- Check that IDs follow the project's requirement-id convention. Under
  `docs/.sdd-version` marker `3` or earlier this is `REQ-{DOMAIN}-{NNN}`; under
  marker `4` it is `REQ-{DOMAIN}-<WS>-{NNN}` with an optional workstream segment
  (`<WS>`) inserted before the `{NNN}` counter. **Accept** the `<WS>` segment — do
  not flag ws-prefixed ids such as `REQ-AUTH-ISSUE42-001` as malformed (REQ-WS-012,
  `docs/spec/ws-ids.md`). Legacy bare ids remain valid (the `default` workstream).
- Check that Q-REQ decisions are documented with rationale

**Scope completeness:**
- Check that every research finding traces to at least one requirement
- Check that the out-of-scope section explicitly names what's excluded
- Check for implicit requirements hiding in prose (unstated assumptions)

#### Specs

**Content correctness:**
- Check that design rationale explains "why X not Y" for non-obvious decisions
- Check that acceptance criteria are independently verifiable
- Check that cross-references to other specs are accurate (file and section exist)
- Check that code blocks and examples use the vocabulary defined in the spec

**Scope completeness:**
- Check that every requirement has spec coverage (traceability.md Spec column)
- Check that every acceptance criterion traces to at least one requirement
- Check for orphan specs (specs that don't trace to requirements via `requires:`)

#### Plan

**Content correctness:**
- Check that chunks are reasonably sized (~5-15 hours each)
- Check that task dependencies are correct (no forward references to unfinished work)
- Check that replan triggers are realistic, not theatrical
- Check that risks name real concerns with mitigations

**Scope completeness:**
- Check that every requirement traces through specs to at least one task
- Check that every spec acceptance criterion will be exercised by some chunk
- Check that entry/exit criteria are concrete and testable

#### Implementation

**Content correctness:**
- Check that the chunk close report accurately reflects implementation state
- Check that traceability matrix columns are filled for covered requirements
- Check that Q-IMPL entries match actual implementation decisions. **Do NOT touch
  (RS-007 Q4 — provably unaffected):** the Q-REQ / Q-SPEC / Q-IMPL content checks
  make no numeric-suffix assumption (Q-REQ/Q-SPEC already use letter suffixes like
  `Q-REQ-G`) and match these ids as opaque strings — the v4 `<WS>` segment in
  `Q-IMPL-<WS>-NNN` is tolerated unchanged; do not add a numeric-suffix parser here.

**Scope completeness:**
- Check that every task in the chunk is completed or explicitly deferred with rationale
- Check for silent scope reductions (work removed without documentation)
- Check what changes for downstream operators — are migration paths, version markers, or documentation updates needed?

#### Verification

**Content correctness:**
- Check that every spec acceptance criterion is walked with evidence (not "pass" without verification)
- Check that pass/fail status matches the evidence presented
- Check that the recommendation is concrete and actionable

**Scope completeness:**
- Check that all specs are covered (not just newly-added ones)
- Check that prior verification reports are referenced where applicable
- Check that issues are sorted into Critical vs Minor with consistent severity criteria

### Step 5: Write and present report

Present a structured report inline. The report is NOT written to disk — operators may manually archive significant reviews if they choose, but the skill does not persist them.

Use this template:

```
## Review: [phase] — [project/artifact name]

## Reviewer Context
[Include ONLY if you have prior involvement — see §Bias Disclosure below.
Omit this section entirely if you have no prior involvement.]

**Verdict:** Approve | Approve with fixes | Reject
VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT

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
- **Approve with fixes**: Critical findings exist but are bounded. Fix them, then proceed without re-review.
- **Reject**: Significant rework needed. Return to current or earlier phase. Consider sdd-replan.

**`VERDICT:` token** (REQ-HARN-013): emit the token line **on a line of its own**, exactly one of `VERDICT: APPROVE`, `VERDICT: APPROVE_WITH_FIXES`, `VERDICT: REJECT`. Conventionally it sits beside the `**Verdict:**` line, but its position is not part of the contract — a consumer (e.g. `sdd-orchestrate`) matches `^VERDICT:` at line start, so nothing else may precede it on that line. The prose verdict and the token map 1:1 and **must agree**: `Approve` ↔ `APPROVE`, `Approve with fixes` ↔ `APPROVE_WITH_FIXES`, `Reject` ↔ `REJECT`. A report whose token and prose disagree (or that omits the token) is treated as malformed by the consumer and re-dispatched rather than acted on. The rest of the report shape (Strengths / Critical–Material–minor / Recommendation) and §Scope Boundaries are unchanged; the token only encodes the verdict already stated.

**Strengths section**: Required. Must be substantive — "the staleness detection chain correctly handles the multi-milestone case" is useful; "good work" is not. The strengths section demonstrates the reviewer read the work thoroughly, not just hunted for flaws.

## Bias Disclosure

When you have prior involvement with the project — reviewed earlier phases, provided requirements, participated in design decisions — include a "Reviewer Context" section at the top of the report:

```markdown
## Reviewer Context
- Prior involvement: [nature and extent, e.g., "Reviewed RS-004
  requirements and specs"]
- Potential bias: [what this involvement might cause you to over-
  or under-scrutinize]
```

When you have no prior involvement, omit the section entirely. Do not write "No bias to disclose" — its absence is the disclosure. The disclosure is informational — the operator decides how to weight findings given the disclosed bias.

## Trigger Classification

Phase boundaries ranked by historical catch rate (RS-004 F5):

| Trigger | Boundaries | Rationale |
|---------|-----------|-----------|
| **Mandatory** | Requirements→specs, specs→plan | Highest catch rate. Translation between abstraction levels compounds errors. |
| **Recommended** | Plan→implement, post-verification | Catches dependency errors and scope gaps before they're expensive. |
| **Ad-hoc** | Any artifact, any time | Operator invokes on demand for a second opinion. |
| **Skip** | Chunk-close boundaries | Already covered by in-session chunk-close mechanism. |

The skill does not enforce mandatory triggers — there is no mechanism to block phase transitions. The tiers document which boundaries are highest-value so operators know where to invest review time.

## Scope Boundaries

sdd-review is one of four verification layers in the SDD workflow. Each catches different failure modes:

| Layer | Scope | When | In-Session? |
|-------|-------|------|-------------|
| Chunk-close | Mechanical: type alignment, traceability, test coverage, Q-IMPL audit | Per-chunk during sdd-implement | Yes |
| XSPEC | Structural: type reference consistency between specs | During sdd-specs Step 4b | Yes |
| sdd-verify | Holistic: aggregate acceptance criteria, quality gates | End of project | Yes |
| **sdd-review** | **Semantic: coherence, scope completeness, readability** | **Phase boundaries** | **No** |

sdd-review does NOT:
- Run mechanical checks (chunk-close's territory) — type alignment, traceability fills, test coverage, Q-IMPL audit
- Validate type cross-references between specs (XSPEC's territory)
- Walk aggregate acceptance criteria (sdd-verify's territory)

If a finding falls into another layer's territory during review, flag it and point to that layer rather than handling it directly. For example: "Note: traceability matrix has empty Implementation column for REQ-X-005. This is chunk-close's territory; recommend running chunk-close on the latest chunk."

## Rules

- **Fresh eyes are the point**: if you have working-session context, the review is compromised. Stop and switch sessions
- **Check scope, not just content**: the most common review miss is confirming what's present without asking what's absent (RS-004 F2)
- **Be specific about findings**: "specs seem incomplete" is useless. "REQ-AUTH-003 has no spec coverage — traceability.md Spec column is empty" is actionable
- **Strengths are not filler**: cite specific things that worked well. If you can't name any, you haven't read the deliverable thoroughly enough
- **Don't fix, flag**: the review produces findings. Fixes happen in the working session. Decisions informed by the review land in the artifacts themselves (commits, spec edits, Q-IMPL entries, replan triggers)
- **Redirect cross-layer findings**: if a finding belongs to chunk-close, XSPEC, or sdd-verify, flag it and name the responsible layer
