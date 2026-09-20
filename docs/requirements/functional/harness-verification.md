---
domain: HARN
last_updated: 2026-09-20
status: Approved
research_refs: [RS-008, RS-005, RS-006, RS-HARNESSP3-001, RS-HARNESSP4-001, RS-HARNESSP6-001]
---

# Requirements: Harness Hardening — Decoupled Verification

## Overview

Second of the three `HARN` files (see `harness-loop-control.md` for the domain
overview, standing constraints, marker-4 resolution rule, procedure-placement
rule and terminology; `harness-boundaries.md` for the write-scope check). This
file covers **decoupled verification** and **context hygiene** (RS-008 Q2–Q4;
catalogue B5–B7, C8, C9): a structured `RETURN:` block from every leaf, a
fixed-shape repair packet for fix re-dispatches, a machine-parseable `VERDICT:`
token from `sdd-review`, a fresh chunk-close verifier that re-executes
`sdd-implement` Step 4's mechanical checks, pruned state on re-dispatch, and
orchestrator-owned routing.

Marker-4 resolution rule (restated): under `docs/.sdd-version` == `4` the same
artifacts are rooted at `docs/ws/<id>/` and the revert/merge target is the
workstream branch, not `main`; marker `3` is unchanged. Procedure text for the
`RETURN:` field-source mapping, repair-packet field sources and verdict branching
lands in the new `skills/sdd-orchestrate/references/return-contract.md`, with a
stub/pointer in `SKILL.md`.

## Requirements

### Decoupled verification

### REQ-HARN-009: Structured `RETURN:` block from every leaf
Every leaf dispatch template (pipeline, fix re-dispatch, fan-out leaf, chunk
verifier) must instruct the subagent to end its return text with a `RETURN:`
block whose first line is `status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED`
on its own line, followed by these keys (empty where not applicable):
`budget_consumed`, `files_written`, `commits`, `tasks_completed`,
`traceability_fills`, `chunk_close` (per-check pass/deferred/advisory/fail plus
overrides), `failures` (REQ-HARN-010), `ledger` (REQ-HARN-006),
`verified_do_not_touch`, `open_questions`, `blocked_writes` (the labeled-content
fallback, as `[{path, content}]`). Values are path references and one-line
strings only — no prose reasoning. The orchestrator must parse the block rather
than free-form prose, and must treat a missing or malformed block as a gate
pause (REQ-ORCH-018 analogue), never as success. `sdd-specs` may rename keys;
the load-bearing decisions are: structured block first, own-line status token,
one-line failures, no tracebacks. (see RS-008 Q3 Schema 1)
**Acceptance**: the pipeline and fan-out templates' return step includes the
block; `references/return-contract.md` names the field-to-consumer mapping
(`tasks_completed` → plan `[x]`, `traceability_fills` → §3e, `failures` /
`ledger` → repair packet and checkpoint, `blocked_writes` → persistence with
scope check) and `SKILL.md` points to it; `tools/sdd-skill-lint.py` has a
`REQUIRED` row for `RETURN:` / `status:` in the templates (REQ-LINT-006).
[Priority: must]

### REQ-HARN-010: Failures are one-line and traceback-free
Each `failures[]` entry in a `RETURN:` block must carry `test` (test id or
command), `kind` ∈ {assertion, error, lint, type, build}, `message` (the last
frame / one line, ANSI-stripped) and `location` (`path:line` where known). Full
tracebacks and tool output must never be carried in a return or a repair packet;
they are regenerable by re-running the named test. (see RS-008 Q3)
**Acceptance**: the template shows the four-field shape; a repair packet fixture
contains no multi-line traceback.
[Priority: must]

### REQ-HARN-011: Repair packet for fix re-dispatches
A fix re-dispatch (pipeline loop-back-to-fix, and a fan-out redo after a verifier
FAIL or merge abort) must carry a fixed-shape **repair packet** in place of the
free-form `{review_findings}` slot, with the fields: `stage`, `iteration N of
MAX` (REQ-HARN-001), `budget` (REQ-HARN-004), `write_scope` (REQ-HARN-020),
`target` (artifact paths + chunk), `failures` (verbatim from the previous
`RETURN.failures` or the verifier's return), `findings` (verbatim Critical/
Material finding lines from the `sdd-review` report — id, text, spec ref,
affected REQ ids, suggested fix — nothing else), `spec_excerpt` (**path + section
heading + line range only — no quoted spec text**; the leaf reads the lines
itself), `ledger_summary` (one line per prior attempt, from `RETURN.ledger`),
`verified_do_not_touch`. The packet must contain no reviewer reasoning, no
quoted artifact content and no accumulated history beyond the ledger summary, so
REQ-ORCH-012 ("findings and paths only") holds by construction. The leaf must be
instructed to act on the packet and not re-derive the history. (see RS-008 Q3
Schema 2; catalogue B6)
**Acceptance**: `dispatch-templates.md` has a `{repair_packet}` slot in the
`{on_fix_only}` block with the listed fields; `tools/sdd-skill-lint.py` has a
`REQUIRED` row for the slot (REQ-LINT-006); a filled packet fixture for a
two-iteration fix has exactly two `ledger_summary` lines and its `spec_excerpt`
is of the form `docs/spec/<file>.md § <heading> L<from>-<to>` with no quoted
text.
[Priority: must]

### REQ-HARN-012: Orchestrator fills the packet from returns, reports and disk
The orchestrator must populate every repair-packet field from one of three
sources only: the previous leaf's or verifier's `RETURN:` block (`failures`,
`ledger_summary`, `verified_do_not_touch`), the review report's finding lines
(`findings`, lifted line-for-line), or files it reads from disk (`target`, and
the path / section heading / line range that make up `spec_excerpt` — never the
spec's content). `iteration`, `budget` and `write_scope` are orchestrator state.
It must never paraphrase, summarize, or add its own or the reviewer's reasoning.
(see RS-008 Q3 "How the orchestrator fills it")
**Acceptance**: `skills/sdd-orchestrate/references/return-contract.md` carries the
field-source table and `SKILL.md` has a stub pointing to it; a packet's
`findings` entries are byte-identical to the corresponding review report lines
apart from structural quoting.
[Priority: must]

### REQ-HARN-013: Machine-parseable `VERDICT:` token from sdd-review
`sdd-review` must emit `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT` as a
single line on its own, in addition to its existing report (Verdict / Strengths
/ Critical-Material-minor findings / Recommendation). The orchestrator must
branch on that token — APPROVE → proceed offered; APPROVE_WITH_FIXES → proceed
or fix offered, findings carried into the packet; REJECT → fix offered subject
to REQ-HARN-001, or REQ-ORCH-018 pause when no actionable findings — and must
never classify a verdict by parsing prose. A missing or unrecognized token must
be surfaced at the gate as a malformed review, not interpreted. (see RS-008 Q4;
catalogue B7)
**Acceptance**: `sdd-review/SKILL.md` report template contains the token line;
`sdd-orchestrate/SKILL.md` §The gate names the three values and points to the
branching table in `references/return-contract.md`; `tools/sdd-skill-lint.py`
carries the producer/consumer `REQUIRED` pair (REQ-LINT-005).
[Priority: must]

### REQ-HARN-014: Fresh chunk-close verifier re-executes Step 4 mechanics
Under `sdd-orchestrate`, the orchestrator must dispatch a fresh, context-isolated
**chunk-close verifier** per closed chunk that independently re-runs the
deterministic parts of `sdd-implement` Step 4 — Check 1 (spec-implementation type
alignment, REQ-CHKC-002), Check 3 (test coverage per spec, REQ-CHKC-004) and the
project's quality gates (build / lint / type / tests from `CLAUDE.md`) — and
returns `CHUNK_VERDICT: PASS | FAIL` on its own line plus findings in the
existing chunk-close report shape (REQ-CHKC-007). Check 2 (traceability,
REQ-CHKC-003) stays orchestrator-applied and is verified after the fill; Check 4
(Q-IMPL audit, REQ-CHKC-005) stays with the implementer and the implement-stage
`sdd-review`. The verifier is a **second executor** of the existing chunk-close
layer, not a fifth verification layer: the implementer keeps Step 4 unchanged
(standalone `sdd-implement` has no one to dispatch a verifier), and the verifier
must **not** be `sdd-review` (REQ-REV-005/006 place these checks outside review's
scope). A FAIL must route to a repair packet (REQ-HARN-011), never to a merge or
to the implement-stage review. (see RS-008 Q2; catalogue B5)
**Acceptance**: the verifier dispatch template invokes no `sdd-review`; its
return contains the token line; the four-layer table in `sdd-review` and
`CLAUDE.md` is unchanged; `tools/sdd-skill-lint.py` has a `REQUIRED` row for
`CHUNK_VERDICT:` (REQ-LINT-005).
[Priority: must]

### REQ-HARN-015: Verifier runs per fan-out leaf, in the worktree, before merge
Under fan-out, the orchestrator must run one chunk-close verifier per leaf
**inside that leaf's worktree on its branch, before** the branch is merged. A
`CHUNK_VERDICT: FAIL` means the branch is not merged; the orchestrator issues a
repair packet to a redo dispatch on that branch (or aborts the group per
REQ-ORCH-026). Only PASS branches proceed to the sequential merge
(REQ-ORCH-025). (see RS-008 Q2)
**Acceptance**: `fan-out.md` §3 sequences verifier → merge for each leaf; a FAIL
fixture shows no `git merge` of that branch.
[Priority: must]

### REQ-HARN-016: Per-chunk implement dispatch in sequential mode
Under `sdd-orchestrate` in sequential mode, the implement stage must be dispatched
**per chunk** (one pipeline dispatch per `### Chunk N`, in plan order) rather than
as one dispatch covering all chunks, so that the chunk-close verifier
(REQ-HARN-014), the budget (REQ-HARN-004) and the write scope (REQ-HARN-020)
have a natural per-chunk unit. This is a driver-level change: `sdd-implement`
is not modified — it is told which chunk to run, exactly as fan-out already does
(REQ-ORCH-001 unaffected). The implement-stage `sdd-review` still runs once,
after all chunks (or after the fan-out merge), on the merged state. (see RS-008
Q2 option (i); Q-REQ-E in `index.md`)
**Acceptance**: `dispatch-templates.md` §PIPELINE (implement) takes a `Chunk N`
parameter; a three-chunk plan run sequentially yields three implement dispatches,
three verifier dispatches and one review dispatch.
[Priority: must]

### REQ-HARN-017: Verifier dispatch is a read-only leaf — paths-only, budgeted, ephemeral
The chunk verifier **is a leaf dispatch** (REQ-HARN-009): its template carries
the leaf slots and nothing else. The dispatch prompt must carry only: repository
root or worktree path, plan path + `Chunk N`, the spec paths the chunk's tasks
trace to, the project's gate commands, a `Budget:` in observable units (e.g. "1
chunk, ≤ 15 tool calls, ≤ 2 test runs"), a `Write scope:` slot that is **empty
(read-only)**, the instruction to run Checks 1 and 3 plus gates, the
non-interactivity clause, and the instruction to end with the `RETURN:` block
(REQ-HARN-009) with `CHUNK_VERDICT: PASS | FAIL` on its own line inside or
immediately alongside it, plus findings in the chunk-close report shape — no
implementer reasoning, no review report, no orchestrator conversation. The
verifier never commits (REQ-HARN-024) and its result surfaces as gate text only;
it is never written to disk (REQ-ORCH-013 analogue). (see RS-008 Q2 minimal
contract)
**Acceptance**: the verifier template has the listed slots — including `Budget:`,
an empty `Write scope:` and a `RETURN:` block ending with or carrying
`CHUNK_VERDICT:` — and nothing else; the scope check (REQ-HARN-021) on a
verifier return observes zero writes; no `docs/` file is written by or on
behalf of a verifier.
[Priority: must]

### Context hygiene

### REQ-HARN-018: Pruned state on re-dispatch
A fix re-dispatch or redo dispatch must pass only the **latest** artifact paths
and the **latest** findings (the repair packet, REQ-HARN-011) — never
accumulated prior packets, prior review reports, or conversation history. Large
content must be referenced by path (spec references as path + section heading +
line range per REQ-HARN-011; everything else by path). The orchestrator must
keep dispatch prompts bounded to the template slots; an operator-visible warning
is expected if a prompt exceeds the template's slot set. (see RS-008 Q3;
catalogue C8)
**Acceptance**: a second fix dispatch prompt for the same stage contains one
repair packet, not two; no fenced review report and no quoted spec text appears
in a fix prompt.
[Priority: must]

### REQ-HARN-019: Orchestrator owns routing and verdict classification
Phase detection relay, verdict classification (REQ-HARN-013), `CHUNK_VERDICT:`
and `SCOPE:` interpretation (REQ-HARN-014, REQ-HARN-022), cap arithmetic
(REQ-HARN-001/002), repair-packet composition (REQ-HARN-012) and the decision to
merge, re-dispatch, replan or stop are **orchestrator-only** work and must never
be delegated to a pipeline, fix, fan-out, verifier or review subagent.
`sdd-orchestrate/SKILL.md` must state this as a principle alongside REQ-ORCH-030
(orchestrator-only dispatch); the per-token interpretation procedures themselves
(verdict branching, `SCOPE:` branching, packet composition) live in
`references/return-contract.md` and `references/write-scope.md`, not in the
SKILL.md body. (see RS-008 Q4 "not mechanical"; catalogue C9)
**Acceptance**: no dispatch template asks the subagent to decide the next stage,
classify a verdict, or judge scope; the principle appears in §Orchestrator-Only
Work with pointers to the two references files.
[Priority: must]

### REQ-HARN-HARNESSP3-002: Every leaf template pins its return block inside the fenced prompt body
The literal `RETURN:` key block must live **inside the fenced prompt body** of
every leaf dispatch template, not in adjacent or later prose. Today the PIPELINE
template (`references/dispatch-templates.md` §PIPELINE) and the fan-out leaf
template (`references/fan-out.md` §2) already pin the literal key block inside
the fence; the **chunk verifier** template states only "then the `RETURN:`
block, whose last line is `CHUNK_VERDICT:`" with the shape in a later prose
subsection, and the **red team** template says "Return in the shape below" with
the shape in an adjacent subsection. Move the literal key block inside the
fenced bodies of the chunk-verifier and red-team templates (red keeps its `Rn`
line shape above the block and `RED_VERDICT:` on its own last line). The fix
re-dispatch needs no separate change — it is the PIPELINE template with
`{on_fix_only}`. The **review** template carries no `RETURN:` block by contract
(`references/return-contract.md` §6, a review emits `VERDICT:` only), but its
own-line `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT` token must be pinned
inside its fenced body on the same principle. (see RS-HARNESSP3-001 Q2(i) —
spec-read: the template table maps the observed drift exactly onto
inside-the-fence vs outside-the-fence; the run corroboration behind it is n = 3
and uncontrolled)
**Acceptance**: the fenced bodies of the chunk-verifier and red-team templates
in `references/dispatch-templates.md` each contain the full literal key list in
contract order, and the review body contains the literal `VERDICT:` token line;
`docs/spec/harness-return-contract.md`, `docs/spec/harness-chunk-verifier.md`
and `docs/spec/adversarial-verify.md` §Red Dispatch Template carry the same
bodies; no template's `RETURN:` shape is reachable only from prose outside its
fence.
[Priority: must]

### REQ-HARN-HARNESSP3-003: A malformed `budget_consumed` shape is a pause, not a warning
`references/return-contract.md` §Parsing must gain exactly one condition:

```
RETURN: MALFORMED (budget_consumed shape)   # present but not a map of unit -> integer
```

`status` and `budget_consumed` are the only two keys the **gate arithmetic**
consumes — `budget_consumed` is rendered at every gate against the dispatched
`Budget:` and sizes the next repair packet's `budget` — and `status` already has
a malformed condition, so this closes the pair. The other nine keys stay a
`RETURN: KEYS MISSING` **warning**: `files_written` is independently
cross-checked by the write-scope observation so an omitted list cannot hide a
write, and `tasks_completed`, `traceability_fills`, `chunk_close`, `failures`,
`ledger`, `verified_do_not_touch`, `open_questions` and `commits` feed
bookkeeping that degrades to "nothing to do" or that the orchestrator can
observe for itself. `blocked_writes` is the deliberate borderline case — an
omitted list silently loses content, but only when the leaf also failed to
write, which surfaces as the deliverable being absent from the observed window;
§1 must record that reasoning beside the warning so the boundary reads as a
decision rather than an omission. (see RS-HARNESSP3-001 Q2(ii) — spec-read plus
judgement; the "elevate exactly these two" boundary has no run evidence either
way and is ratified here rather than inherited as an edit)
**Acceptance**: `references/return-contract.md` §Parsing lists the
`budget_consumed` shape row and §1 carries the `blocked_writes`-stays-a-warning
note; `docs/spec/harness-return-contract.md` matches; a fixture return whose
`budget_consumed` is prose rather than a map of unit → integer pauses the gate
as `RETURN: MALFORMED (budget_consumed shape)`, and a fixture missing only
`ledger` still renders a `KEYS MISSING` warning and does not pause.
[Priority: must]

### REQ-HARN-HARNESSP3-005: Review findings a fix leaf must not touch route to the next dispatch's deliverable contract
`references/return-contract.md` §3 must state that review findings raised
against an artifact the fix leaf is **not** scoped to touch are carried into the
**next pipeline dispatch's** `{deliverable_contract}` slot rather than into the
repair packet. No schema change: a `carry_to_next_dispatch:` field was
considered and is not worth the cost, and the slot already exists. This
specifies what the operator did by hand on 2026-09-18 when a repair packet had
no place for such a finding. (see RS-HARNESSP3-001 Q8-IN row 4 — provenance:
raised by the 2026-09-18 run itself, not carried in from the kickoff's Q8 seed
list; observed gap with a constructed remedy, cheap enough that being wrong
costs one edit)
**Acceptance**: `references/return-contract.md` §3 names the
`{deliverable_contract}` slot as the destination for out-of-fix-scope review
findings and states that no repair-packet field is added;
`docs/spec/harness-return-contract.md` carries the same sentence.
[Priority: should]

### REQ-HARN-HARNESSP4-007: the three leaf terminal tokens sit at column 0 in every template and restating spec
The `CHUNK_VERDICT: PASS | FAIL` token in `references/dispatch-templates.md`'s
CHUNK VERIFIER dispatch body and `RETURN:` block must sit at **column 0**, as
`VERDICT:` (REVIEW) and `RED_VERDICT:` (RED TEAM) already do, and
`skills/sdd-orchestrate/SKILL.md` must state the verifier token's parse rule as
`^CHUNK_VERDICT:` on the last non-blank line, matching the anchored wording it
already uses for the other two. The Approved specs that restate the fenced
bodies byte-for-byte — `docs/spec/harness-chunk-verifier.md` (and
`docs/spec/adversarial-verify.md` where a body it restates changes) — are
amended in the same change so REQ-HARN-HARNESSP3-002's byte-consistency
contract is preserved, and the `[template-drift]` rule of REQ-LINT-HARNESSP4-001
is the mechanical check that they were. The template is the outlier today: two
tokens are `^`-anchored, live leaves already render the third at column 0, and
an indented template invites a leaf to emit an indented token a future anchored
parser would miss. (workstream `harness-p4`; see `docs/ws/harness-p3/verification.md`
§V9 — recorded with a recommendation; needs a cycle that can amend the two
Approved specs)
**Acceptance**: `grep -n '^  CHUNK_VERDICT:' skills/sdd-orchestrate/references/dispatch-templates.md`
returns nothing and `grep -c '^CHUNK_VERDICT:'` on the same file is ≥ 2;
`SKILL.md` §The gate states `^CHUNK_VERDICT:`; the fenced bodies of
`dispatch-templates.md` and `harness-chunk-verifier.md` are byte-identical after
the edit (`python3 tools/sdd-skill-lint.py` exits 0 with the `[template-drift]`
rule active).
[Priority: should]

### REQ-HARN-HARNESSP6-002: the L2 convergence cluster rule and its session-scoped finding ledger
The orchestrator must derive cross-layer convergence (L2) from what the layers
and second-executors **already return** — no field is added to any leaf's
`RETURN:` shape and no root-cause field is introduced. Two or more findings form
a **cluster** when (i) they come from **different** layers or second-executors
(blue pipeline, chunk verifier, review, red); (ii) they belong to the **same
cycle**, by the `research_id` stamp that cycle identity already uses; and (iii)
their **arbitration finding keys are equal at section granularity** — same
`file` **and** same `section`, reusing the existing `(file, section)` key with
its ratified leading-ordinal strip and its existing parser. A file-level-only
match must render **nothing**: two findings in one large file are not one root
cause, and a rule that says they are makes the signal noise. A **secondary** key
applies — two findings citing the same `REQ-*` or deviation-entry id cluster
even when their sections differ. Convergence is computed over a **session-scoped,
in-memory finding ledger** of the same class as the loop counters: per finding it
holds only the arbitration key, the emitting layer and the gate at which the
finding arrived — no finding text, nothing on disk, no durable artifact. The
signal must be evaluated at **every** gate over everything recorded so far, and
each cluster renders **once**, at the gate where its second member arrives, so it
can and usually will fire mid-cycle rather than only at DONE; a cluster that
completes only at DONE routes into `verification.md` §Issues Found, to be fixed
or explicitly closed in-cycle, never into §Next Steps. (workstream `harness-p6`;
kickoff §Scope item 8, shipping on explicit operator direction; RS-HARNESSP6-001
Q4(a)/(b), Confidence **Medium** — the rule reuses an exercised parser but has
never been replayed against a real finding set, and its firing rate is
unmeasured; this requirement is deliberately carried at lower weight than the
Q1-Q3 items and is the cycle's credible replan trigger)
**Acceptance**: `docs/spec/harness-loop-control.md` §Convergence Signal states
the three cluster conditions, the secondary id key, the file-level-only
non-render and the ledger's contents; a self-test scenario group exercises the
key parser across layers — two findings from different layers with equal
`(file, section)` cluster; two from the **same** layer do not; two with the same
file and different sections do not; two from different layers citing the same
`REQ-*` id with different sections do; `python3 tools/sdd-skill-lint.py` exits 0.
[Priority: must]
