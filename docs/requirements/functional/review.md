---
domain: REV
last_updated: 2026-09-22
status: Approved
research_refs: [RS-004]
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
> RS-PIPELINEOBSERVABILITY-001 R10; Q-REQ-PO-E) `[Updated: 2026-09-22]`: the
> sections and their order are unchanged. **Acceptance, added**: section (c) is
> the section whose list items REQ-HARN-PIPELINEOBSERVABILITY-005 counts — a
> report with ≥ 1 item under its critical/blocking heading (headed `Critical`
> here, `Blocking` in `agents/reviewer.md`; both spellings are matched) and a
> verdict other than Reject is consumed as malformed (`tier/verdict conflict`)
> by the orchestrator, never acted on as the stated verdict; `agents/reviewer.md`
> already defines Approve as "no blocking finding", so the rule enforces the
> agent's own contract.

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
