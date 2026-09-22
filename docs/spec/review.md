---
status: Approved
last_updated: 2026-09-22
requires:
  - REQ-REV-001
  - REQ-REV-002
  - REQ-REV-003
  - REQ-REV-004
  - REQ-REV-005
  - REQ-REV-006
  - REQ-REV-007
  - REQ-REV-008
  - REQ-REV-PIPELINEOBSERVABILITY-001
---

# External Review

## Context

SDD has three in-session verification layers: chunk-close (mechanical
per-chunk checks), XSPEC (structural type references between specs),
and verify (holistic acceptance criteria at project end). All three
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
| Chunk-close | Mechanical: type alignment, traceability, test coverage, Q-IMPL audit | Per-chunk during implement | Yes |
| XSPEC | Structural: type reference consistency between specs | During specs Step 4b | Yes |
| verify | Holistic: aggregate acceptance criteria, quality gates | End of project | Yes |
| **review** | **Semantic: coherence, scope completeness, readability** | **Phase boundaries** | **No** |

Review's unique value is the combination of semantic judgment and
session isolation. Mechanical checks (does type X exist in impl?)
belong to chunk-close. Structural checks (does spec A's type match
spec B's?) belong to XSPEC. Criteria walkthrough (does criterion C
pass?) belongs to verify. Review asks: does this deliverable make
sense as a whole, is everything that should be here actually here, and
would an external operator understand it?

### Session Isolation

The skill's opening step, before any artifact reading:

> **Session isolation check.** This skill must run in a session that
> does NOT have prior working context for the project under review.
> If you have been involved in writing, implementing, or deciding on
> the artifacts being reviewed in this session, stop and ask the
> operator to invoke review in a fresh session.
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

**Verdict definitions** `[Updated: 2026-09-22]` (REQ-REV-PIPELINEOBSERVABILITY-001 (3):
three mutually disjoint predicates over the tier counts, verbatim in the
quoted parts in both producers; the former lines are retired by the
zero-count witness below):
- **Approve** (`C = 0` and `M = 0`): "No findings above minor; nothing to
  apply before the next stage."
- **Approve with fixes** (`C = 0` and `M ≥ 1`): "No blocking finding; at
  least one Material finding — fix them, then proceed without re-review."
- **Reject** (`C ≥ 1`): "Any blocking (Critical) finding. Significant rework
  needed. Return to current or earlier phase. Consider replan."


**Strengths section**: Required. Must be substantive — "the staleness
detection chain correctly handles the multi-milestone case" is useful;
"good work" is not. Its purpose is calibration: the reviewer
demonstrates they read the work thoroughly, not just hunted for flaws.

**Non-persistence**: The report is presented as conversation output.
It must not be written to disk as a project artifact. Decisions
informed by the review land in the artifacts themselves (commits,
spec edits, Q-IMPL entries, replan triggers). Operators may manually
archive significant reviews if they choose.

**The report grammar** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-REV-PIPELINEOBSERVABILITY-001; REQ-REV-002 as amended; Q-REQ-PO-AF, -Z, -AJ; the record of why is §Pipeline-Observability Amendment).

Every review report the harness consumes is an instance of **one** grammar,
stated by REQ-REV-PIPELINEOBSERVABILITY-001 and carried in the same words by
both shipped producers — `skills/review/SKILL.md` (§Step 5 template, §Verdict
definitions) and `agents/reviewer.md` (`harness-agents.md` §The frontmatter
contract). Every rule that parses a report (`harness-return-contract.md`
§VERDICT Token's count, `arbitrated-handoff.md` §Review Key on Material Lines,
the `verdict.findings` `{C, M, m}` record field) is defined over this grammar
and over nothing discovered downstream. REQ-REV-002's section list (a)–(f) is
preserved and maps onto it — (a) = sections 1–2, (b) = 3, (c)–(e) = 4–6,
(f) = 7.

1. **Sections**, each opened by a label line, in the **producer's order** —
   the order the template above writes and a reviewer copies; not a parsed
   constraint (no consumer rule reads section position, and a report whose
   sections are transposed is parsed section by section like any other):
   (1) `**Verdict:**` — the **Verdict form**: the bold label at column 0
   followed on the same line by exactly one of `Approve`, `Approve with
   fixes`, `Reject`, and by nothing else; (2) `VERDICT: <TOKEN>` — the
   **token form** of REQ-HARN-013: no bold label, the literal `VERDICT: ` at
   column 0 followed by one of `APPROVE`, `APPROVE_WITH_FIXES`, `REJECT` and
   by nothing else, on a line of its own, **anywhere** in the report, exactly
   one such line, and when more than one is present the **last occurrence
   wins** — `skills/orchestrate/references/return-contract.md` §6 is the
   authority, quoted here and restated nowhere; (3) `**Strengths:**`;
   (4) `**Critical findings:**` — the blocking tier, mandatory;
   (5) `**Material findings:**` — mandatory; (6) `**Minor findings:**` —
   mandatory; (7) `**Recommendation:**`. For sections 3–7 a label line is a
   line whose text begins at column 0 with the bold label exactly as listed,
   optionally followed on the same line by one bracketed gloss (`[…]`) and by
   nothing else. The report title (`## Review: …`) and the optional
   `## Reviewer Context` section (REQ-REV-004) precede section 1 and are the
   only markdown headings a report carries; **no tier is ever a markdown
   heading**. A section's **extent** runs from its label line to the line
   before the next label line of this list or the `VERDICT:` line, whichever
   comes first, or to the end of the report. The three tier sections are
   mandatory even when empty, and **an empty tier section carries no list
   item**: its label line is followed directly by the next label line, never
   by a placeholder such as `- None`, `- n/a` or `- —`.
2. **Findings.** Each finding is exactly one list item — a line beginning
   `- ` directly under its tier's label line — whose text begins with the
   tier prefix, a 1-based counter, a colon and a space: `C<n>: ` under
   Critical, `M<n>: ` under Material, `m<n>: ` under Minor. Continuation
   lines (`Suggested fix:`, citations) are indented and are not list items.
   This is the corpus's **one** tier vocabulary — Critical / Material / Minor
   with prefixes `C` / `M` / `m`; "blocking" is a defined synonym for
   "Critical" and appears only in verdict prose; the tier names `Blocking`
   and `Substantive` are retired from both producers (Q-REQ-PO-Z).
3. **Verdict predicates over the tier counts** (`C` := Critical items, `M`
   := Material items) — the three definitions below, disjoint and
   exhaustive, so every well-formed report has exactly one legal verdict.
   Both sides of the `APPROVE` / `APPROVE_WITH_FIXES` boundary are
   **consumer-checked** by `harness-return-contract.md` §VERDICT Token: a
   Critical item under a non-`REJECT` token, and a Material item under
   `APPROVE`, each render a `REVIEW: MALFORMED` pause, so an `APPROVE` can
   never hide a Material finding — the M-side is not a producer-only
   obligation (Q-REQ-PO-AJ); since the specs review's round 5 M3
   (Q-REQ-PO-AK) that consumer's 4×3 case table covers every cell of this
   predicate table — an empty report under `APPROVE_WITH_FIXES` and a
   Critical-free report under `REJECT` pause too — so the consumer check is
   exhaustive over these three predicates, whose three cells are its three
   `legal` cells. Section 4 is section (c) of REQ-REV-002, the
   section whose items that count reads first; the producer's obligation is
   unchanged — a reviewer who finds a blocking item writes Reject.

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
- Run review against a real phase output and verify the report
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
- [ ] Scope boundaries against chunk-close, XSPEC, verify explicit (REQ-REV-006)

**Pipeline-observability (2026-09-22, review)**

- [ ] The report template in `skills/review/SKILL.md` still carries the
  `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT` line and the seven
  label lines in the producer's order — `python3 plugins/sdd/tools/skill-lint.py`
  exits 0 with the d1 producer row (REQ-REV-002 as amended).
- [ ] Each producer carries the six bold label lines —
  `grep -cE '^\*\*(Verdict|Strengths|Critical findings|Material findings|Minor findings|Recommendation):\*\*' plugins/sdd/skills/review/SKILL.md`
  reads 6 and the same command over `plugins/sdd/agents/reviewer.md` reads 6
  (6 and 0 before this delta); each shows the three prefixes —
  `grep -cE '^ *- (C|M|m)1: '` reads 3 over each producer (3 and 0 before);
  each carries the three predicates — `grep -c 'No findings above minor'`,
  `grep -c 'at least one Material finding'` and `grep -c 'Any blocking
  (Critical) finding'` each read 1 over each producer (0 before); each states
  the empty-tier rule — `grep -c 'carries no list item'` reads ≥ 1 over each
  producer (0 before) (REQ-REV-PIPELINEOBSERVABILITY-001 (i)–(iv)).
- [ ] One zero-count witness for every retired wording —
  `grep -cE 'No blocking findings\. Proceed to next phase|Critical findings exist but are bounded|blocking, then substantive|Substantive findings|^#+ +(Blocking|Critical)|^\*\*(Blocking|Substantive):\*\*' plugins/sdd/skills/review/SKILL.md plugins/sdd/agents/reviewer.md`
  reads 0 for each file (2 and 1 before this delta); the skill's "its
  position is not part of the contract" sentence is not retired — it is the
  live consumer rule the grammar quotes (REQ-REV-PIPELINEOBSERVABILITY-001 (v)).
- [ ] The skill-lint `REQUIRED` row whose pattern is `at least one Material
  finding` (row p13 of `skill-lint-v5.md` §`REQUIRED` Rows —
  Pipeline-Observability) names **both** producers in its `files:`; in a
  temp copy with the line removed from either file the linter exits non-zero
  naming that file, and on this tree it exits 0
  (REQ-REV-PIPELINEOBSERVABILITY-001 (vi)).
- [ ] No fenced template block in `skills/review/SKILL.md` shows a tier label
  line followed by a list item whose normalised text is in the placeholder set
  of `harness-return-contract.md` §VERDICT Token — `none`, `n/a`, `—` after
  stripping the list marker, emphasis or backticks, trailing punctuation and
  whitespace, then case-folding — and no other placeholder rule is applied
  (REQ-REV-002 as amended; REQ-REV-PIPELINEOBSERVABILITY-001 (1)).
- [ ] Fixture F2 (F1 plus one `C1:` item, `VERDICT: APPROVE_WITH_FIXES`)
  renders the malformed pause with `N = 1` and F1 renders none; fixtures F8
  (empty Critical and Material sections under `APPROVE_WITH_FIXES`) and F9
  (the same under `REJECT`) each render a `tier/verdict conflict` pause, so
  every non-`legal` cell of the consumer's case table is exercised — the
  fixture walkthrough of `harness-return-contract.md` §VERDICT Token
  (REQ-REV-PIPELINEOBSERVABILITY-001 (3), REQ-HARN-PIPELINEOBSERVABILITY-005;
  F8/F9 by Q-REQ-PO-AK).

## Implementation Questions

### Q-IMPL-HARNESSP2-004: Material finding template line gains `affects`
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Report Format — Material findings template line
**Decision**: Superseded by `arbitrated-handoff.md` §Review Key on Material Lines (REQ-ARB-HARNESSP2-008 amendment 2026-09-17): the Material template line becomes `- M1: [what's wrong] — [file:section] — affects [REQ-*] | affects —`. Nothing else in the report format (REQ-REV-002) or the scope boundaries (REQ-REV-005/006) changes; `sdd-review` gains no red, telemetry or arbitration text.
**Rationale**: The arbitration key must be computable on both tiers; the change is one template line.
**Date**: 2026-09-17 (harness-p2 specs stage)


## Pipeline-Observability Amendment (2026-09-22, REQ-REV-PIPELINEOBSERVABILITY-001; REQ-REV-002 amended)

[Added 2026-09-22, workstream `pipeline-observability` —
RS-PIPELINEOBSERVABILITY-001 R10, §Q3 tier-heading parsing; Q-REQ-PO-E, -V, -X,
-Y, superseded by Q-REQ-PO-Z; Q-REQ-PO-AF, -AJ. Observed defect: the report lived
in three texts never unified — the skill's template, its verdict definitions and
the agent body — and the consumer of REQ-HARN-PIPELINEOBSERVABILITY-005
discovered the section's start, end, label form and existence one review round
at a time; the former `Approve with fixes` definition instructed a reviewer to
emit exactly the shape the tier-count rule rejects.]

**Where the contract lives** (REQ-REQ-PIPELINEOBSERVABILITY-001 (b), 2026-09-22): this section is the record of *why* and states no contract of its own; the contract is in the sections of record named here, each edited in place under a `[Updated: 2026-09-22]` marker, and its acceptance criteria sit in this spec's own Acceptance Criteria section under the same date. §Report Format carries the report grammar — the seven label lines and their forms, the extent clause, the one tier vocabulary, the empty-tier rule and the three verdict predicates in §Verdict definitions (REQ-REV-PIPELINEOBSERVABILITY-001; REQ-REV-002 as amended — the sections and their order are unchanged, their grammar is now stated). Left consistent and not reopened: §Non-persistence, §Trigger Classification, §Session Isolation, §Required Inputs.

**Why (3) names the consumer's case table** (Q-REQ-PO-AK, specs review round 5 M3 routed to its requirements origin): the three predicates are the producer's obligation, but exhaustiveness of the consumer check over them is shown by `harness-return-contract.md` §VERDICT Token's 4×3 case table — its three `legal` cells are these three predicates — so §Report Format (3) cross-references it rather than restating a rule; the producer's text is otherwise unchanged. **Why one grammar**: three producers' texts drifting independently is how three reviews of this cycle carried Critical findings under `APPROVE_WITH_FIXES`. **Why the skill text is the side that moves** (Q-SPEC-PO-I): the count rule of `harness-return-contract.md` §VERDICT Token made the former `Approve with fixes` line unreachable, and the former `Approve` line left `Approve` and `Approve with fixes` sharing a predicate; the three predicates are disjoint and exhaustive. **Why the token line's position is not binding** (Q-REQ-PO-AF, reverting Q-REQ-PO-AD): four shipped texts already state "anywhere in its report, last occurrence wins", and the grammar quotes that authority rather than contradicting it. **Why the producer forbids the placeholder the consumer tolerates** (Q-REQ-PO-Y, -AE): a template must not teach a shape the parser has to normalise away.
