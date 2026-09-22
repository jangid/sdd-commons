---
domain: REV
last_updated: 2026-09-22
status: Approved
research_refs: [RS-004, RS-PIPELINEOBSERVABILITY-001]
---

# Requirements: External Review

## Overview

Structured external review at SDD phase boundaries. The reviewer operates
in a separate session from the working session, applying phase-specific
checklists and producing a tiered findings report. Catches design coherence
issues, scope completeness gaps, and vocabulary inconsistencies that
in-session mechanisms (chunk-close, XSPEC, verify) cannot detect due
to context contamination. Derived from RS-004 findings on review
catch-zones and miss-zones across two projects. (see RS-004)

## Requirements

### REQ-REV-001: Phase detection
The review skill must detect which SDD phase artifacts are being reviewed
and apply a phase-appropriate checklist. Recognized phases: research,
requirements, specs, plan, implementation (per-chunk), and verification.
Detection must be based on the artifacts provided as input, not on the
project's current phase state.
[Priority: must]

### REQ-REV-002: Report format
The review must produce a structured report with these sections in order:
(a) verdict — one of Approve, Approve with fixes, or Reject;
(b) strengths — 2-4 substantive items demonstrating thorough reading;
(c) critical findings — must fix before next phase, each citing file,
section, and affected requirement;
(d) material findings — should fix, can proceed with carry-forward note;
(e) minor findings — fix if convenient, defer without documentation;
(f) recommendation — concrete next action with specific file/requirement
references. The report must be presented inline as conversation output
and must not be written to disk as a project artifact.
[Priority: must]
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> RS-PIPELINEOBSERVABILITY-001 R10; Q-REQ-PO-E, -V, -X, -Y, superseded by
> Q-REQ-PO-Z) `[Updated: 2026-09-22]`: the sections and their order are
> unchanged. Their **grammar** — the exact label text of each section, the
> gloss form, the section extent, the one tier vocabulary (`C<n>:` / `M<n>:` /
> `m<n>:`), the empty-tier rule and the three verdict definitions as disjoint
> predicates over the tier counts — is stated **once**, in
> REQ-REV-PIPELINEOBSERVABILITY-001, which binds it on the review skill's
> template and verdict definitions and on `agents/reviewer.md` alike. This
> note carries no verdict sentence of its own: the wording, the zero-count
> witness for the former `Approve` and `Approve with fixes` lines and the
> skill-lint pin are REQ-REV-PIPELINEOBSERVABILITY-001 (i)–(vi). Section (c)
> is the section whose list items REQ-HARN-PIPELINEOBSERVABILITY-005 counts.
> Why the text moved: the former `Approve with fixes` definition ("Critical
> findings exist but are bounded…") instructed a reviewer to emit exactly the
> shape the tier-count rule rejects, and the former `Approve` line left
> `Approve` and `Approve with fixes` indistinguishable by their predicates.
> no binding statement — this note carries no wording of its own; the grammar
> it names is bound and swept in REQ-REV-PIPELINEOBSERVABILITY-001
> (REQ-REQ-PIPELINEOBSERVABILITY-001 (e) exemption).

### REQ-REV-003: Required inputs
The review skill must specify its required inputs: (a) the deliverable
artifacts being reviewed, (b) the prior phase output that the deliverable
was produced from, and (c) the traceability matrix. The review must not
require or use the working session's conversation history, intermediate
drafts, or internal deliberations.
[Priority: must]

### REQ-REV-004: Bias disclosure
When the reviewer has prior involvement with the project (reviewed earlier
phases, provided requirements, wrote the kickoff, or participated in
implementation), the review report must include a bias disclosure section
stating the nature and extent of prior involvement. When the reviewer has
no prior involvement, the section is omitted.
[Priority: must]

### REQ-REV-005: Trigger classification
The skill must classify phase boundaries into three trigger categories
with rationale: (a) mandatory — review before proceeding, applied to
requirements→specs and specs→plan boundaries; (b) recommended — review is
valuable but operator decides, applied to plan→implement and
post-verification boundaries; (c) ad-hoc — operator invokes on demand for
any artifact at any time. The skill must not enforce mandatory triggers
(no mechanism to block phase transitions) but must document which
boundaries are highest-value.
[Priority: must]

### REQ-REV-006: Scope boundaries
The skill must explicitly define its scope boundaries against the three
existing verification layers: (a) chunk-close — mechanical checks
(type alignment, traceability, test coverage, Q-IMPL audit) are
chunk-close's territory, not review's; (b) XSPEC — structural type
reference validation between specs is XSPEC's territory; (c) verify —
holistic acceptance criteria walkthrough is verify's territory.
Review's scope is semantic coherence, scope completeness, external
readability, and translation fidelity between abstraction levels. If a
finding falls into another skill's territory, the review must flag it and
point to that skill rather than handling it directly.
[Priority: must]

### REQ-REV-007: Session isolation
The skill must include an explicit session-isolation confirmation prompt
as its opening step, verifying the reviewer is in a fresh session without
prior working context for the project under review. Verification that
isolation actually holds is the operator's responsibility. The skill must
not include logic that attempts to detect context contamination
programmatically, as this is unreliable.
[Priority: must]

### REQ-REV-008: Scope-completeness check
The review must check both content correctness (is what's here right?)
and scope completeness (is everything that should be here actually here?).
Phase checklists must include explicit scope-completeness items alongside
content-correctness items. This is a cross-cutting concern — every phase
checklist must address it, not just phases where misses have historically
occurred. Evidence: RS-004 F2 found that 3 of 4 systematic review misses
(including the v3 migration gap that spawned RS-003) traced to checking
content without checking scope.
[Priority: must]

### REQ-REV-PIPELINEOBSERVABILITY-001: the review report grammar — one section list, one tier vocabulary, one `VERDICT:` line, bound on both producers
Every review report the harness consumes must be an instance of **one**
grammar, stated here and nowhere else, and both shipped producers —
`plugins/sdd/skills/review/SKILL.md` (§Step 5 template and §Verdict
definitions) and `plugins/sdd/agents/reviewer.md` (the body the orchestrator
dispatches) — must carry it in the same words. Every rule that parses a report
(REQ-HARN-PIPELINEOBSERVABILITY-005's count, REQ-ARB-HARNESSP2-001/-008's
finding keys, the `verdict.findings` `{C, M, m}` record field) is defined
over this grammar and over nothing discovered downstream.

**(1) Sections, each opened by a label line, listed in the order the
template emits them (Q-REQ-PO-AF).** The list below is the **producer's
order** — the order §Step 5's template writes and a reviewer copies — and not
a parsed constraint: no consumer rule reads section position, and a report
whose sections are transposed is parsed section by section like any other.
Label lines take three forms. For sections 3–7 a label line is a line whose
text begins at column 0 with the bold label exactly as listed, optionally
followed on the same line by one bracketed gloss (`[…]`) and by nothing else.
Sections 1 and 2 are each their own form, stated at their entries. The
`VERDICT:` token line's rule is the shipped consumer contract —
`plugins/sdd/skills/orchestrate/references/return-contract.md` §6 `VERDICT:`
token and branching — quoted here as the authority and restated nowhere else
in this delta: the review emits it "on a line of its own, anywhere in its
report", exactly one such line, and when more than one is present "the last
occurrence wins":

1. `**Verdict:**` — the **Verdict form**: the bold label at column 0 followed
   on the same line by exactly one of `Approve`, `Approve with fixes`,
   `Reject`, and by nothing else;
2. `VERDICT: <TOKEN>` — the **token form** of REQ-HARN-013: no bold label,
   the literal `VERDICT: ` at column 0 followed by `<TOKEN>` — one of
   `APPROVE`, `APPROVE_WITH_FIXES`, `REJECT` — and by nothing else, on a line
   of its own, anywhere in the report (last occurrence wins —
   `return-contract.md` §6); a report holds exactly one such line;
3. `**Strengths:**`;
4. `**Critical findings:**` — the blocking tier; mandatory;
5. `**Material findings:**` — mandatory;
6. `**Minor findings:**` — mandatory;
7. `**Recommendation:**`.

The report title (`## Review: …`) and the optional `## Reviewer Context`
section (REQ-REV-004) precede section 1 and are the only markdown headings a
report carries; **no tier is ever a markdown heading**. A section's extent
runs from its label line to the line before the next label line of this list
or the `VERDICT:` line, whichever comes first, or to the end of the report —
the `VERDICT:` line is already item 2 of the list, but the token line is a
label line whose position is free, hence named separately as the escape. The
three tier sections are mandatory even when empty, and **an empty tier section
carries no list item**: its label line is followed directly by the next label
line, never by a placeholder such as `- None`, `- n/a` or `- —`.

**(2) Findings.** Each finding is exactly one list item — a line beginning
with `- ` directly under its tier's label line — whose text begins with the
tier prefix, a 1-based counter, a colon and a space: `C<n>: ` under Critical,
`M<n>: ` under Material, `m<n>: ` under Minor. Continuation lines (`Suggested
fix:`, citations) are indented and are not list items. This is the corpus's
**one** tier vocabulary — Critical / Material / Minor with prefixes `C` / `M`
/ `m`. The word "blocking" is a defined synonym for "Critical" and appears only
in verdict prose; the tier names `Blocking` and `Substantive` are retired from
both producers (Q-REQ-PO-Z).

**(3) Verdict predicates over the tier counts** (`C` := Critical items, `M`
:= Material items): `Approve` ↔ `APPROVE` iff `C = 0` and `M = 0`; `Approve
with fixes` ↔ `APPROVE_WITH_FIXES` iff `C = 0` and `M ≥ 1`; `Reject` ↔
`REJECT` iff `C ≥ 1`. The three are disjoint and exhaustive, so every
well-formed report has exactly one legal verdict. Both sides of the
`APPROVE` / `APPROVE_WITH_FIXES` boundary are **consumer-checked** by
REQ-HARN-PIPELINEOBSERVABILITY-005: a Critical item under a non-`REJECT`
token and, since round 8 (Q-REQ-PO-AJ), a Material item under `APPROVE` each
render a `REVIEW: MALFORMED` pause, so an `APPROVE` can never hide a Material
finding; the M-side is not a producer-only obligation; since the specs
review's round 5 M3 (Q-REQ-PO-AK) the same requirement's case table covers
every cell of this table — an empty report under `APPROVE_WITH_FIXES` and a
Critical-free report under `REJECT` pause too — so the consumer check is
exhaustive over these three predicates. The §Verdict definitions
in both producers must read, verbatim in the quoted parts: **Approve** = "No
findings above minor; nothing to apply before the next stage."; **Approve
with fixes** = "No blocking finding; at least one Material finding — fix them,
then proceed without re-review."; **Reject** = "Any blocking (Critical)
finding. Significant rework needed. Return to current or earlier phase.
Consider replan."

Why one grammar: the report previously lived in three texts never unified —
the skill's template, its verdict definitions and the agent body — and the
consumer of REQ-HARN-PIPELINEOBSERVABILITY-005 discovered the section's start,
end, label form and existence one review round at a time. REQ-REV-002's
section list (a)–(f) is preserved and now maps onto this grammar — (a) =
sections 1–2, (b) = 3, (c)–(e) = 4–6, (f) = 7; REQ-REV-002's and
REQ-AGENT-PIPELINEOBSERVABILITY-001's amendment notes point here and state no
wording of their own. (see RS-PIPELINEOBSERVABILITY-001 §Q3 tier-heading
parsing, R10; requirements review iteration 3 C1–C3, M1, M3, M4.) Touches
REQ-REV-002 and REQ-AGENT-PIPELINEOBSERVABILITY-001 (amended); leaves
REQ-HARN-013 (token contract), REQ-AGENT-MARKETPLACE-002 (frontmatter) and
REQ-AGENT-MARKETPLACE-006 (agent file is the single source for its own rules)
consistent.
**Acceptance** (every count is a `grep` over the named file; `today` values
were measured on this tree before the requirement was written): (i) each
producer carries the six bold label lines —
`grep -cE '^\*\*(Verdict|Strengths|Critical findings|Material findings|Minor findings|Recommendation):\*\*' plugins/sdd/skills/review/SKILL.md`
reads 6 (today 6) and the same command over `plugins/sdd/agents/reviewer.md`
reads 6 (today 0); (ii) each producer shows the three prefixes —
`grep -cE '^ *- (C|M|m)1: '` reads 3 over `plugins/sdd/skills/review/SKILL.md`
(today 3) and 3 over `plugins/sdd/agents/reviewer.md` (today 0); (iii) each
producer carries the three predicates — `grep -c 'No findings above minor'`,
`grep -c 'at least one Material finding'` and
`grep -c 'Any blocking (Critical) finding'` each read 1 over each producer
(today 0, 0, 0 in each); (iv) each producer states the empty-tier rule —
`grep -c 'carries no list item'` reads ≥ 1 over each producer (today 0 and 0);
(v) one zero-count witness for every retired wording —
`grep -cE 'No blocking findings\. Proceed to next phase|Critical findings exist but are bounded|blocking, then substantive|Substantive findings|^#+ +(Blocking|Critical)|^\*\*(Blocking|Substantive):\*\*' plugins/sdd/skills/review/SKILL.md plugins/sdd/agents/reviewer.md`
reads 0 for each file (today 2 for the skill — the old `Approve` line and the
old `Approve with fixes` line — and 1 for the agent — the `blocking, then
substantive, then minor` tier sentence; the regex covers both the heading
form and the bold-label form of the retired tiers; the skill's "its position
is not part of the contract" sentence is **not** retired — it is the live
consumer rule this requirement quotes); (vi) the skill-lint `REQUIRED` row whose pattern is `at least one
Material finding` names **both** producers in its `files:` (a row this cycle
adds; its count is unchanged), so that in a temp copy with the line removed from either file the
linter exits non-zero naming that file, and on this tree the linter exits 0.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG, 2026-09-22)**
over the four binding statements this requirement makes. Each command is a
listing grep over `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in this
requirement's own text and in the index rows that cite it are the statement
itself and are not listed. Every other hit is reconciled (consistent as-is,
with the reason) or retired (covered by a zero-count witness).
- **Label list** —
  `grep -rnE '^\*\*(Verdict|Strengths|Critical findings|Material findings|Minor findings|Recommendation|Blocking|Substantive):\*\*|^#+ +(Blocking|Critical findings|Substantive)|blocking, then substantive' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`:
  `plugins/sdd/skills/review/SKILL.md` §Step 5 template (six labels) —
  reconciled, it is the list this grammar transcribes; `docs/spec/review.md`
  §Report template (the same six) — reconciled, same list;
  `docs/spec/arbitrated-handoff.md` (`**Material findings:**` in the packet
  example) — reconciled, quotes the label form; `plugins/sdd/agents/reviewer.md`
  "blocking, then substantive, then minor" — retired, witness (v).
- **Prefixes** — `grep -rnE '^ *- (C|M|m)[0-9]+: ' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`:
  `plugins/sdd/skills/review/SKILL.md` §Step 5 template and
  `docs/spec/review.md` §Report template (`C1:`/`M1:`/`m1:` examples) —
  reconciled, the same three prefixes; `docs/spec/arbitrated-handoff.md`
  (`- M1:` in the packet example) — reconciled; `plugins/sdd/skills/plan/SKILL.md`
  (`- M1:`, `- M2:` under §Milestones) — reconciled, a different subject: plan
  milestone ids, and the prefix rule applies only to list items under a tier
  label line.
- **Verdict predicates** —
  `grep -rnE 'No findings above minor|at least one Material finding|Any blocking \(Critical\) finding|No blocking findings\. Proceed|Critical findings exist but are bounded|Material and minor findings only|[Nn]o blocking finding;' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`:
  `plugins/sdd/skills/review/SKILL.md` §Verdict definitions (the old `Approve`
  and `Approve with fixes` lines) — retired, witness (v), replaced under (iii);
  `plugins/sdd/agents/reviewer.md` §What your token means ("no blocking
  finding; the artifact can proceed as written") — retired, replaced by the
  three predicates under REQ-AGENT-PIPELINEOBSERVABILITY-001 (its per-wording
  greps read 1 after landing, today 0); `docs/spec/review.md` §Verdict
  definitions (old lines in the section of record) and §Pipeline-Observability
  Amendment (the live three, quoting the old as history) — reconciled by
  naming the requirement that amends it: REQ-REQ-PIPELINEOBSERVABILITY-001 (b)
  makes the specs re-derivation move the live three into the section of
  record; `docs/spec/harness-agents.md` (the live three for the agent) —
  reconciled, consistent; `docs/spec/pipeline-observability.md` (Q-REQ-PO-V's
  wording quoted as history beside the live three) — reconciled, the live
  three match (3); `docs/spec/skill-lint-v5.md` row p13 (`at least one
  Material finding`) — reconciled, it is witness (vi)'s row;
  `docs/requirements/index.md` Q-REQ-PO-V and -X — retired, their sentence
  bodies now read "(wording retired; see Q-REQ-PO-Z)" (round 6 m2), so a grep
  for a live sentence finds it in this requirement, the two producers and the
  specs only.
- **Token line** —
  `grep -rnE 'anywhere in its report|last occurrence wins|position is not part of the contract' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`:
  `plugins/sdd/skills/orchestrate/references/return-contract.md` §6,
  `plugins/sdd/skills/orchestrate/SKILL.md` §The gate,
  `plugins/sdd/skills/review/SKILL.md` §`VERDICT:` token paragraph,
  `plugins/sdd/skills/orchestrate/references/dispatch-templates.md` review
  dispatch ("on a line of its own"), `docs/spec/harness-return-contract.md`
  §`VERDICT:` token and its checklist line, `docs/spec/skill-lint-v5.md`
  (the consumer row's "last occurrence wins") — all reconciled, consistent:
  they state the rule (1) quotes, and the revert of Q-REQ-PO-AD is what makes
  them consistent; `docs/requirements/index.md` Q-REQ-PO-AD — retired, the
  entry now reads as reverted by Q-REQ-PO-AF.
- **Rule-table population** (re-run with the population terms, specs closing
  review C2, Q-REQ-PO-AL, 2026-09-22) —
  `grep -rnE 'REQUIRED=|FORBIDDEN=|print-population|population' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents plugins/sdd/tools/skill-lint.py`:
  the `REQUIRED` rows this requirement binds on the linter (rows p1–p14 of
  `docs/spec/skill-lint-v5.md` §`REQUIRED` Rows — Pipeline-Observability)
  move the population REQ-LINT-PACKAGING-007 compares — `REQUIRED` 42 today
  (measured with `python3 plugins/sdd/tools/skill-lint.py
  --print-population`) → `56` after the delta, beside `FORBIDDEN` 14 → `15`
  from REQ-LINT-PIPELINEOBSERVABILITY-001's row — and the requirement that
  moves them is REQ-LINT-PACKAGING-007 as amended (its comparand is the
  three-way equality between the flag's output, the code tables and
  `docs/spec/two-root-linter.md` §6's dated numbers, no longer a literal).
  `docs/spec/two-root-linter.md` §6 and its §Acceptance Criteria bullet
  (`42 / 9 / 7 / 14`) — reconciled, the second live surface, moved to
  `56 / 15` under a dated marker by the specs stage;
  `plugins/sdd/tools/skill-lint.py` self-test `pinned` dict (`42 / 14`) —
  reconciled, post-delta `56 / 15` under -007's equality;
  `docs/requirements/integration/skill-lint.md` REQ-LINT-PACKAGING-007 — the
  mover, amended; `docs/spec/skill-lint-v5.md` §Self-Test Extension ("grows by
  exactly six") — reconciled, the harness-p5 delta's history, the new total is
  §6's dated number; `docs/requirements/integration/packaging.md`
  REQ-PKG-PACKAGING-004 and `docs/requirements/index.md` packaging ledger
  (`40 / 13`) — reconciled by naming the mover, the packaging cycle's numbers
  as of its date; every other `population` hit — a different subject
  (bundled-tool and policed-area populations); `plugins/sdd/skills/**`,
  `plugins/sdd/agents/**` — no hit.
[Priority: must]
`[Updated: 2026-09-22]` — requirements review round 5 M2, m2, m3: the
label-line definition split into the Verdict form, the token form and the
bold-label form; the retired-wording witness extended to the bold-label tier
form; the row ordinal dropped. Requirements review round 6 C1, C2
(Q-REQ-PO-AF, reverting Q-REQ-PO-AD): the section order is the producer's
order and not a parsed constraint; the token line is "anywhere in the
report, last occurrence wins" per `return-contract.md` §6; the extent clause's
`VERDICT:` escape is restored; the token-position sentence leaves witness (v).
Requirements review round 8 M3 (Q-REQ-PO-AJ): (3)'s M-side named as
consumer-checked by REQ-HARN-PIPELINEOBSERVABILITY-005's `material_items`
count.
