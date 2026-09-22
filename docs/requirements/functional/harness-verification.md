---
domain: HARN
last_updated: 2026-09-22
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

### REQ-HARN-013: Machine-parseable `VERDICT:` token from review
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
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> RS-PIPELINEOBSERVABILITY-001 R6, R10; Q-REQ-PO-D, Q-REQ-PO-E)
> `[Updated: 2026-09-22]`: the `APPROVE_WITH_FIXES` branch reads **"fix, then
> proceed without re-review (re-review on explicit operator opt-in), findings
> carried into the packet"** — REQ-HARN-PIPELINEOBSERVABILITY-001 — in place
> of "proceed or fix offered"; the `APPROVE` and `REJECT` branches and the
> never-parse-prose rule are unchanged. **Acceptance, added** (no text of the
> malformed branch changes): a review body with at least one list item under
> its critical/blocking heading and a token other than `REJECT` — `APPROVE`
> with blocking items (the spec's literal example) **and** `APPROVE_WITH_FIXES`
> with blocking items (the recorded shape, three rounds) alike — renders the
> existing `REVIEW: MALFORMED` pause as `(tier/verdict conflict)`, per
> REQ-HARN-PIPELINEOBSERVABILITY-005; the branching table names the routing
> above and `tools/skill-lint.py`'s producer/consumer pair still holds.
> **Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
> 2026-09-22)** over the `APPROVE_WITH_FIXES` branch text — a listing grep over
> `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in
> this requirement's own text and in the index rows citing it are the statement
> itself and are excluded.
> Command: `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/functional/harness-verification.md -exec grep -nHE 'proceed without re-review|proceed or fix offered|fix, then proceed' {} +`.
> the listing is REQ-HARN-PIPELINEOBSERVABILITY-001's, re-run 2026-09-22:
> `plugins/sdd/skills/orchestrate/references/return-contract.md` §6 branching
> table and `references/loop-control.md` §5a — reconciled, they state this
> routing; `plugins/sdd/skills/review/SKILL.md` §Verdict definitions ("… then
> proceed without re-review") — the routing half is consistent, the predicate
> half is retired under REQ-REV-PIPELINEOBSERVABILITY-001 (v);
> `docs/spec/harness-return-contract.md`, `docs/spec/harness-loop-control.md`,
> `docs/spec/review.md` and `docs/spec/pipeline-observability.md` — reconciled;
> this requirement's original body sentence "proceed or fix offered" —
> reconciled, this note supersedes it in place.
> Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
> files the `-l` listing names:
> `docs/requirements/functional/harness-loop-control.md`
> REQ-HARN-PIPELINEOBSERVABILITY-001 — reconciled, the amender this note
> cites; `docs/requirements/functional/review.md`
> REQ-REV-PIPELINEOBSERVABILITY-001 (v) (quoting the old line as history) —
> reconciled.

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
their **arbitration finding keys match** under one of three key rules. The
**primary** key rule is the shared id — two findings citing the same `REQ-*` or
deviation-entry id cluster whatever their files and sections. The **sectionless
file** rule makes the file-level key a cluster key when the file has no section
structure to key on (a data or code file such as `.jsonl` or `.py`, or any file
in which the arbitration key parser finds no section): two findings from
different layers naming such a file cluster on the file alone. Equal
`(file, section)` keys — same `file` **and** same `section`, reusing the existing
`(file, section)` key with its ratified leading-ordinal strip and its existing
parser — are **retained** as a third key rule but carry no recall claim. For a
file that **does** have sections, a file-level-only match must render
**nothing**: two findings in two sections of one large prose file are not one
root cause, and a rule that says they are makes the signal noise.

**[Updated: 2026-09-20 — amended at replan, caused by the Chunk 8 resolving
spike, which replayed the cluster rule over the recorded findings of harness-p3,
-p4 and -p5. The co-located `(file, section)` key formed **zero** clusters in
each of the three cycles and zero in total, and clustered **none** of the three
layers of the harness-p3 §L2 origin case. The requirement therefore no longer
rests on that key: the shared-id key that did fire becomes primary, and the
sectionless-file rule is added because it recovers the one genuine convergence
the replay found and a section-granular key structurally cannot catch (red and
blue on the same malformed records in a `.jsonl` file, which has no sections).
The noise guard for sectioned files is unchanged. Requirement id, number and
priority are unchanged; see `docs/ws/harness-p6/plan.md` §Chunk 8 → Spike
Findings and `docs/requirements/index.md` §Out of Scope.]**

**[Stated limitation: 2026-09-20 — verify-stage review M4.** The sectionless-file
rule's motivating case, named in this requirement and in the spec, is red and
blue on `.sdd/telemetry.jsonl`. That path is gitignored and telemetry is an
operator opt-out at KICKOFF, so with telemetry off, or before the first append,
the file is absent; the absent-path rule (red R4) then yields no key and the
motivating case renders nothing. The self-test asserts rule 2 against a
fixture-created data file, so the rule's behaviour — not that specific case —
is what is demonstrated. The structureless discriminator's suffix set
(`.jsonl`, `.ndjson`, `.csv`, `.tsv`, `.log`, `.txt`) also draws an arbitrary
line: `.json`, `.yaml` and `.toml` read as structured. Recorded as a disclosure
against the shipped floor; the code is unchanged and the R3 discriminator
stands. Requirement id, number and priority are unchanged.]** Convergence is computed over a **session-scoped,
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
the three cluster conditions, the three key rules, the file-level-only
non-render for files that have sections, and the ledger's contents; a self-test
scenario group exercises the key parser across layers — two findings from
different layers citing the same `REQ-*` id with different sections cluster
(primary key); two from different layers naming the same file in which the
parser finds no section cluster on the file alone; two from different layers in
the same sectioned file with different sections do not; two from the **same**
layer do not; two from different layers with equal `(file, section)` cluster
(retained key); `python3 tools/sdd-skill-lint.py` exits 0. **[Updated: 2026-09-20 — the Chunk 8 resolving spike replayed the rule over the recorded finding sets of harness-p3, -p4 and -p5. This sentence is superseded: the rule HAS been replayed. What it measured is that the co-located `(file, section)` key formed zero clusters over three cycles and clusters none of the three on the harness-p3 §L2 origin case, which is why L2 shipped at a descoped floor. What remains unmeasured is the **live** firing rate of the shipped floor, not the replay.]**
[Priority: must]

### REQ-HARN-PIPELINEOBSERVABILITY-005: a token that disagrees with its Critical or Material section is the existing `REVIEW: MALFORMED` pause, decided by a count over the report grammar
The orchestrator must execute REQ-HARN-013's "token disagrees with prose →
`REVIEW: MALFORMED`" condition (`docs/spec/harness-return-contract.md` §Edge
Cases) by one structural rule over the report grammar of
REQ-REV-PIPELINEOBSERVABILITY-001, and by nothing else. Parse the report into
sections by REQ-REV-PIPELINEOBSERVABILITY-001 (1)'s extent clause — a section
runs to the next label line of the grammar or the `VERDICT:` line, whichever
comes first — and that clause is restated nowhere here: the label form, the
gloss and the token line's free position are its (Q-REQ-PO-AF). This
requirement states only the two count rules, the placeholder rule and the
six pauses, which are exhaustive over the predicate table of
REQ-REV-PIPELINEOBSERVABILITY-001 (3) (Q-REQ-PO-AK).
`blocking_items` := the number of list items in the `**Critical findings:**`
section **after normalising the placeholder out** (Q-REQ-PO-AE): every item
whose visible text — list marker, surrounding emphasis or backticks, trailing
punctuation and whitespace stripped, then case-folded — is `none`, `n/a` or
`—` (U+2014) is dropped before counting, so a lone placeholder counts as **0**
and a placeholder beside real items adds nothing (the consumer tolerates the
placeholder the producer grammar forbids and never over-reports by it).
`material_items` := the same count, with the same normalisation, over the
`**Material findings:**` section (round 8 M3, Q-REQ-PO-AJ — the operator's
exit bar is a clean `APPROVE`, and a producer-only M-side would let an
`APPROVE` hide Material findings). Then, in this order: the `**Critical
findings:**` label absent → `REVIEW: MALFORMED (missing section: Critical
findings)`, never a silent zero; the `**Material findings:**` label absent →
`REVIEW: MALFORMED (missing section: Material findings)`, the same rule;
`blocking_items > 0` and the token not `REJECT` →
`REVIEW: MALFORMED (tier/verdict conflict: N blocking under <token>)`;
`blocking_items = 0`, `material_items > 0` and the token `APPROVE` →
`REVIEW: MALFORMED (tier/verdict conflict: N material under APPROVE)`;
`blocking_items = 0`, `material_items = 0` and the token `APPROVE_WITH_FIXES`
→ `REVIEW: MALFORMED (tier/verdict conflict: 0 material under
APPROVE_WITH_FIXES)` (specs review round 5 M3, Q-REQ-PO-AK — without it that
combination routed fix-then-proceed with an empty repair packet);
`blocking_items = 0` and the token `REJECT` →
`REVIEW: MALFORMED (tier/verdict conflict: 0 blocking under REJECT)`
(Q-REQ-PO-AK — the cell the case table below exposed while proving the
packet's five conditions exhaustive; a `REJECT` with no Critical item is the
same "token disagrees with prose" shape). The four conflict conditions are
mutually exclusive over `(blocking_items, material_items, token)`, so their
order after the two missing-section pauses is immaterial. Case table —
rows are the count pairs, columns the token, each cell the pause's
parenthesised text or `legal`; the three `legal` cells are exactly the three
predicates of REQ-REV-PIPELINEOBSERVABILITY-001 (3), so the six conditions
are exhaustive by inspection:

| counts | `APPROVE` | `APPROVE_WITH_FIXES` | `REJECT` |
|---|---|---|---|
| C = 0, M = 0 | legal | `0 material under APPROVE_WITH_FIXES` | `0 blocking under REJECT` |
| C = 0, M ≥ 1 | `N material under APPROVE` | legal | `0 blocking under REJECT` |
| C ≥ 1, M = 0 | `N blocking under APPROVE` | `N blocking under APPROVE_WITH_FIXES` | legal |
| C ≥ 1, M ≥ 1 | `N blocking under APPROVE` | `N blocking under APPROVE_WITH_FIXES` | legal |

Every
pause offers the existing `re-dispatch review │ accept prose manually │ stop`
— no new token, no conversion. On `accept prose manually` the consumed verdict
is the one the counts legally imply under REQ-REV-PIPELINEOBSERVABILITY-001
(3): `REJECT` for a blocking conflict, counting toward `reject_run`;
`APPROVE_WITH_FIXES` for a material conflict, routed as
REQ-HARN-PIPELINEOBSERVABILITY-001's fix-then-proceed and resetting
`reject_run` as any consumed `APPROVE_WITH_FIXES` does; for the two
Q-REQ-PO-AK conflicts the verdict the counts imply is read off the table's
row — `APPROVE` when `material_items = 0`, `APPROVE_WITH_FIXES` when
`material_items > 0` — and routed as that consumed verdict; on `re-dispatch
review` the re-dispatched round is consumed instead and nothing counts. The rule reads
label lines and list markers only, never prose, so REQ-HARN-013's
never-parse-prose rule is kept; because the grammar binds
`plugins/sdd/agents/reviewer.md` to the same label list, the check is live for
the harness's own dispatched reviews and not only for the skill's template.
Observed shape: the recorded `APPROVE_WITH_FIXES`-with-Critical rounds (specs
round 4 and research rounds 2 and 4 of consumer-geometry, this cycle's second
research review). (see RS-PIPELINEOBSERVABILITY-001 §Q3 tier-heading parsing,
R10, §Mechanical pin R10.) Consumes REQ-REV-PIPELINEOBSERVABILITY-001; touches
REQ-HARN-013 (acceptance-only); leaves REQ-ARB-HARNESSP2-001/-008 (keys per
Critical/Material line), REQ-HARN-019 and REQ-AGENT-MARKETPLACE-002 consistent.
**Acceptance**: `references/return-contract.md` §Tier-heading parsing states
the count rule, the placeholder rule and both pause texts —
`grep -c 'tier/verdict conflict'`, `grep -c 'missing section'`,
`grep -c 'counts as zero'`, `grep -c 'material under APPROVE'`,
`grep -c '0 material under APPROVE_WITH_FIXES'` and
`grep -c '0 blocking under REJECT'` over
`plugins/sdd/skills/orchestrate/references/return-contract.md` each read ≥ 1
(today 0, 0, 0, 0, 0, 0 — the last two measured 2026-09-22 with those exact
commands, Q-REQ-PO-AK) — pinned by a skill-lint `REQUIRED` row on
`tier/verdict conflict` whose removal in a temp copy makes the linter exit
non-zero. Fixtures, each a **whole report** in the grammar (all label lines
present, glosses as the template writes them): F1 — empty Critical section,
two `M<n>:` items, `VERDICT: APPROVE_WITH_FIXES` → no pause; F2 — F1 plus one
`C1:` item → pause, `N = 1`; F3 — F1 with the `**Critical findings:**` label
line deleted → `REVIEW: MALFORMED (missing section: Critical findings)`; F4 —
Critical section holding only `- None`, `VERDICT: APPROVE` → no pause, and the
same with `- n/a` or `- —` → no pause, and `- None` followed by a `C1:` item →
pause, `N = 1` (the placeholder is normalised out, not counted); F5 — F2 with `VERDICT: REJECT` → no pause; F6 — F1 through F5
re-emitted in the shape `plugins/sdd/agents/reviewer.md` prescribes after
landing (the same label list) → the same results, which is the witness that
the two producers share the grammar; F7 — F1 with `VERDICT: APPROVE` (empty
Critical section, two `M<n>:` items) → pause, `N = 2`, and the same with the
Material section holding only `- None` → no pause (normalised out), and F7
with the `**Material findings:**` label line deleted → `REVIEW: MALFORMED
(missing section: Material findings)`, and F7 with `VERDICT:
APPROVE_WITH_FIXES` → no pause (it is F1); F8 — whole report, empty
Critical section, empty Material section, `VERDICT: APPROVE_WITH_FIXES` →
`REVIEW: MALFORMED (tier/verdict conflict: 0 material under
APPROVE_WITH_FIXES)`, and the same with one `M1:` item → no pause; F9 — F8
with `VERDICT: REJECT` → `REVIEW: MALFORMED (tier/verdict conflict: 0
blocking under REJECT)`, and the same with one `C1:` item → no pause (it is
F5's shape). The cross-field assertion (d) of
REQ-TELEM-PIPELINEOBSERVABILITY-003 fails on a `review` record with
`verdict.findings.C ≥ 1`, a non-`REJECT` token and a non-pause gate decision,
on one with `verdict.findings.C = 0`, `verdict.findings.M ≥ 1`, the token
`APPROVE` and a non-pause gate decision, on one with `verdict.findings.C = 0`,
`verdict.findings.M = 0`, the token `APPROVE_WITH_FIXES` and a non-pause gate
decision, and on one with `verdict.findings.C = 0`, the token `REJECT` and a
non-pause gate decision (Q-REQ-PO-AK).
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG, 2026-09-22)**
over the two binding statements this requirement makes; listing greps over
`docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`, hits in this requirement's own
text and in the index rows citing it excluded.
- **Count rule and its two pauses** —
  `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/functional/harness-verification.md -exec grep -nHE 'tier/verdict conflict|missing section: (Critical|Material)|token disagrees with prose|blocking_items|material_items|material under APPROVE' {} +`:
  `docs/spec/harness-return-contract.md` §Tier-heading parsing (the
  `blocking_items` definition, the `blocking_items > 0 and token != REJECT`
  predicate and the `tier/verdict conflict` rendering) — reconciled,
  consistent with the count rule; `docs/spec/review.md` §Pipeline-Observability
  Amendment (the pause rendering) and `docs/spec/skill-lint-v5.md` row p9 —
  reconciled, consistent; REQ-HARN-013's amendment note in this file —
  reconciled, it points here and states no rule of its own;
  `plugins/sdd/**` — no hit (today 0, the acceptance's baseline: the shipped
  consumer carries the rule only after landing); the M-side terms
  (`material_items`, `material under APPROVE`, `missing section: Material`)
  — no hit in any of the four trees outside this requirement and the index
  rows citing it (today 0; the rule is new at round 8 and the acceptance above
  adds it to `return-contract.md`; REQ-REV-PIPELINEOBSERVABILITY-001 (3)
  cites it), and `docs/spec/harness-return-contract.md` §Tier-heading
  parsing's `blocking_items`-only rule — reconciled by naming this requirement
  as its amender, which the specs re-derivation applies per
  REQ-REQ-PIPELINEOBSERVABILITY-001 (b).
  Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
  files the `-l` listing names:
  `plugins/sdd/skills/orchestrate/references/return-contract.md` §Tier-heading
  parsing (`blocking_items`, `material_items`, the conflict table) —
  reconciled, the rule the acceptance above adds, landed by the implement
  stage, so the "no hit" baseline above is history (the M-side terms
  included); `docs/spec/pipeline-observability.md` — reconciled, the cycle's
  index spec, it lists; `docs/requirements/functional/review.md`
  REQ-REV-PIPELINEOBSERVABILITY-001 (3) — reconciled, its citation.
- **Placeholder rule** —
  `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/functional/harness-verification.md -exec grep -nHE 'counts as zero|normalis(ed|ing) out|- None' {} +`:
  `docs/spec/harness-return-contract.md` §Tier-heading parsing's placeholder
  step ("a lone placeholder counts as zero … two or more items count as
  written") — states Q-REQ-PO-Y's lone-only rule, which Q-REQ-PO-AE replaced
  by normalise-out; reconciled by naming the requirement that amends it: this
  one, whose F4 mixed case (`N = 1`) the specs re-derivation writes into that
  step per REQ-REQ-PIPELINEOBSERVABILITY-001 (b); `docs/spec/review.md`
  (producer side: "never by a placeholder item") and `docs/spec/skill-lint-v5.md`
  row p14 (`counts as zero`) — reconciled, consistent; `plugins/sdd/**` — no
  hit (today 0).
  Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
  files the `-l` listing names:
  `plugins/sdd/skills/orchestrate/references/return-contract.md` §Tier-heading
  parsing ("counts as zero", the normalised-out placeholder) and
  `plugins/sdd/agents/reviewer.md` ("never by a placeholder such as `- None`")
  — reconciled, landed by the implement stage, so the "no hit" baseline above
  is history; `docs/requirements/functional/review.md`
  REQ-REV-PIPELINEOBSERVABILITY-001 (the producer-side sentence) — reconciled,
  consistent.
- **Exhaustiveness over the predicate table (Q-REQ-PO-AK, 2026-09-22)** —
  `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/functional/harness-verification.md -exec grep -nHwE 'material under|blocking under|tier/verdict' {} +`:
  REQ-HARN-013's amendment note in this file — reconciled, it points here;
  `docs/spec/harness-return-contract.md` §Tier-heading parsing (a two-row
  conflict table rendering `N blocking under <token>` and `N material under
  APPROVE`, the four-grep acceptance list and the F7 restatement) — carries
  the round-8 shape and none of the Q-REQ-PO-AK cells; reconciled by naming
  this requirement as its amender, which the specs re-derivation applies per
  REQ-REQ-PIPELINEOBSERVABILITY-001 (b) (the two rows, the two greps, F8 and
  F9); `docs/spec/skill-lint-v5.md` row p9 (`tier/verdict conflict`) —
  consistent, the pin's text is shared by every conflict pause; the index
  §Summary sentence and ledger rows citing it — excluded as citations;
  `plugins/sdd/**` — no hit (today 0, the acceptance's baseline).
  Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
  files the `-l` listing names:
  `plugins/sdd/skills/orchestrate/references/return-contract.md` (the two-row
  conflict table and the exhaustiveness table) — reconciled, the Q-REQ-PO-AK
  cells, landed by the implement stage, so the "no hit" baseline above is
  history; `docs/spec/review.md` §Pipeline-Observability Amendment (the
  `tier/verdict conflict` pause) and `docs/spec/pipeline-observability.md` —
  reconciled, the cycle's index spec, it lists (the amendment table and the
  exhaustiveness note) — reconciled, they cite.
[Priority: must]
`[Updated: 2026-09-22]` — rewritten at requirements review iteration 3
(C1–C3) over the grammar of REQ-REV-PIPELINEOBSERVABILITY-001; the section
end "the next heading", the heading-or-bold-label dual form and the `Blocking`
spelling are withdrawn, and the Q-REQ-PO-Y placeholder rule is folded into the
body. Requirements review round 5 m1 (Q-REQ-PO-AE): the placeholder is normalised
out before counting (F4's mixed case reads `N = 1`). Requirements review round
6 C1, C2, M3 (Q-REQ-PO-AF, reverting Q-REQ-PO-AD): the out-of-order malformed
condition is removed — it had no render string, option set, fixture or
witness — the extent clause's `VERDICT:` escape is restored and cited from
REQ-REV-PIPELINEOBSERVABILITY-001 (1) rather than restated, so REQ-HARN-013's
"(no text of the malformed branch changes)" is true again. Requirements
review round 8 M3 (Q-REQ-PO-AJ): `material_items` counted over the Material
section with the same normalisation, a third pause for a Material item under
`APPROVE`, the missing-Material-section pause, fixture F7 and the M-side
clause of telemetry assertion (d). Specs review round 5 M3, routed to its
requirements origin (Q-REQ-PO-AK): the empty report under
`APPROVE_WITH_FIXES` and the Critical-free report under `REJECT` are the
fifth and sixth pauses, the case table proves the six exhaustive over
REQ-REV-PIPELINEOBSERVABILITY-001 (3), fixtures F8 and F9, two witness greps
and the two further clauses of assertion (d).

### REQ-HARN-PIPELINEOBSERVABILITY-006: the implement dispatch's test-run budget is derived, not fixed
`references/dispatch-templates.md`'s implement template must state the
derivation `test_runs = 2 × mutations + gates`, where `mutations` is the number
of mutation/reversion demonstrations the chunk's tasks name and `gates` is the
number of quality-gate commands the chunk runs, and the orchestrator must size
each chunk's `Budget:` test-run slot with it rather than with a fixed example
value. Observed defect: the template pins a fixed `≤ 3 test runs` example and
the consumer-geometry chunks overran 8 against 6 and 18 against 12, so a budget
overrun was the honest outcome of an honest chunk. (see
RS-PIPELINEOBSERVABILITY-001 §Q6 gap 8, R12, §Mechanical pin R12.) No existing
text is amended: REQ-HARN-005 binds exhaustion, not sizing, and
REQ-TELEM-HARNESSP2-002 binds the parsed integer form, which the formula
yields; leaves REQ-HARN-004 (`Budget:` slot present), REQ-HARN-009/-017 (the
verifier's own `≤ 2 test runs` example is separate) and REQ-HARN-HARNESSP3-003
(`budget_consumed` shape) consistent.
**Acceptance**: `grep -c mutations plugins/sdd/skills/orchestrate/references/dispatch-templates.md`
reads ≥ 1 (today 0), pinned by a skill-lint `REQUIRED` row on the formula
sentence whose removal in a temp copy makes the linter exit non-zero; the
template's worked example dispatches a chunk naming 2 mutations and 2 gates
with `≤ 6 test runs`; the orchestrate skill's implement dispatch step cites the
derivation.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
2026-09-22)** over the derived test-run budget — a listing grep over
`docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in
this requirement's own text and in the index rows citing it are the statement
itself and are excluded.
Command: `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/functional/harness-verification.md -exec grep -nHE 'mutations \+ gates|≤ [0-9]+ test runs' {} +`.
`plugins/sdd/skills/orchestrate/references/dispatch-templates.md` implement
example (`budget: "1 chunk, ≤ 25 tool calls, ≤ 3 test runs"`) — the fixed
example this requirement replaces; reconciled by naming this requirement as its
amender (the formula sentence and the `≤ 6 test runs` worked example land in
that file); the same file's chunk-verifier (`≤ 2 test runs`) and red-team (`≤ 3
test runs`) examples, and the verifier and red-team rows of
`references/return-contract.md` §Budget table — reconciled, separate leaves
(REQ-HARN-009/-017, REQ-HARN-004's default); the implement-per-chunk and
fan-out-leaf rows of that table and of `docs/spec/harness-return-contract.md` —
the fixed value as a stated default; reconciled by naming this requirement as
their amender, so those rows read the derivation, not a number;
`orchestrate/SKILL.md`, `USAGE.md`, `references/write-scope.md`,
`docs/spec/orchestration.md`, `harness-chunk-verifier.md`,
`harness-write-scope.md` and `harness-loop-control.md` §2 gate renderings
(`budget_consumed: {…, test_runs: 3} vs Budget: … ≤ 3 test runs`) — reconciled,
rendered examples of a gate line, not a sizing rule;
`docs/spec/harness-loop-control.md` §Pipeline-Observability Amendment
(`test_runs = 2 × mutations + gates`) — reconciled, carries this requirement;
`docs/spec/adversarial-verify.md` and `docs/spec/telemetry.md` — reconciled,
the red-team default; `docs/requirements/functional/adversarial-verify.md` and
`harness-loop-control.md` — reconciled, the red-team and verifier budgets by
citation.
[Priority: must]
