---
domain: HARN
last_updated: 2026-09-17
status: Approved
research_refs: [RS-008, RS-005, RS-006]
---

# Requirements: Harness Hardening

## Overview

Hardens the SDD harness (`sdd-orchestrate` driving `sdd-implement`, `sdd-review`,
`sdd-replan`) with the deterministic loop-control, decoupled-verification and
boundary patterns from the harness-engineering literature, as scoped in the
idea catalogue (`docs/superpowers/specs/2026-09-17-harness-engineering-ideas.md`,
ideas A1–A4, B5–B7, C8–C10, E13) and de-risked by RS-008. The domain covers:

- **Loop control** — a max-iteration guard on the review fix loop and on replan
  re-entries, a budget slot on every dispatch, an attempt ledger with an
  oscillation rule in stuck detection, and a bounded checkpoint on circuit-break
  (RS-008 Q1, Q3).
- **Decoupled verification** — a structured `RETURN:` block from every pipeline
  leaf, a fixed-shape repair packet for fix re-dispatches, a machine-parseable
  `VERDICT:` token from `sdd-review`, and a fresh chunk-close verifier that
  re-executes `sdd-implement` Step 4's mechanical checks (RS-008 Q2, Q3).
- **Context hygiene** — pruned state on re-dispatch and orchestrator-owned routing
  (RS-008 Q3; catalogue C8, C9). The SKILL.md size audit (C10) is specified in
  the LINT domain (`integration/skill-lint.md`).
- **Boundaries** — a declared write scope per dispatch, checked mechanically on
  return and surfaced as gate text (RS-008 Q5).

Standing constraints every requirement below respects: no new on-disk artifact
type (REQ-ORCH-004), reviews stay ephemeral (REQ-ORCH-013), no loop-position
marker or authoritative loop log (REQ-ORCH-014), fix re-dispatches carry findings
and paths only (REQ-ORCH-012), and `sdd-review` is never the chunk verifier
(REQ-REV-005, REQ-REV-006). `sdd-implement` standalone (no orchestrator) keeps
its current behavior; every orchestrate-only mechanism is a second pass layered
on top, not a replacement (REQ-ORCH-001).

Terminology: a **dispatch** is one subagent invocation by the orchestrator. The
five dispatch types are *pipeline* (one stage, sequential mode), *fix
re-dispatch* (loop-back-to-fix of a stage), *fan-out leaf* (one chunk-group in a
worktree), *review* (`sdd-review`), and *chunk verifier* (REQ-HARN-014). A
**leaf** is any non-review dispatch. **Observable units** are counts the
subagent can report about itself without harness support — tasks, chunks, tool
calls, test runs, approaches.

## Requirements

### Loop control

### REQ-HARN-001: Fix-loop max-iteration guard
The orchestrator must cap the number of loop-back-to-fix re-dispatches per stage
within one orchestrator session at a configurable maximum (default **3**). Each
fix re-dispatch must state its position as `iteration N of MAX`. When a stage's
review still does not pass after the MAX-th fix iteration, the orchestrator must
**not** dispatch another fix; it must exit to the operator at the gate with a
compiled findings log (the review's Critical/Material findings across the
iterations, by iteration) and offer only stop, manual intervention, or an
explicit operator-authorized extra iteration. The count is per-session — it is
not persisted to any artifact (REQ-ORCH-014) and restarts at 0 in a new session,
which is itself a human intervention. (see RS-008 Q1)
**Acceptance**: a session that reaches REJECT three times on one stage shows a
fourth gate with the compiled log and no automatic fourth dispatch; the
`iteration N of 3` line appears in each fix dispatch prompt; no file under
`docs/` records the counter.
[Priority: must]

### REQ-HARN-002: Replan re-entry cap, derived from plan-history
The orchestrator must cap replan re-entries per cycle at a configurable maximum
(default **3**). The count must be **derived**, not stored: it is the number of
`docs/plan-history/*-replan-*.md` archives whose filename date is on or after the
kickoff's `date:` frontmatter (falling back to the kickoff's commit date when the
field is absent, the same fallback `sdd-orchestrate` §KICKOFF uses for
`research_id`). On the MAX-th re-entry the orchestrator must surface the cap as a
gate event (REQ-ORCH-017) and must not route back into `sdd-replan` again without
an explicit operator decision. Minor in-place replans leave no archive and are
deliberately not counted. (see RS-008 Q1)
**Acceptance**: with three `-replan-` archives dated ≥ kickoff date, a fourth
replan trigger produces a gate pause naming the cap; archives dated before the
kickoff date or lacking the `-replan-` segment do not count.
[Priority: must]

### REQ-HARN-003: `-replan-` archive filename convention is a stated contract
Every plan archive written by `sdd-replan` must carry the `-replan-` segment in
its filename (`{date}-replan-{reason}.md`, or `{date}-m{N}-replan-{reason}.md`
per milestone), and no other skill (`sdd-plan` rewrite archives, milestone-
complete archives) may use that segment. `sdd-replan/SKILL.md` must state this
as an explicit contract, not an implicit convention, because REQ-HARN-002's
derivation depends on it. (see RS-008 Q1; lint row: REQ-LINT-005)
**Acceptance**: `sdd-replan/SKILL.md` contains the stated rule; `sdd-plan/SKILL.md`
archive names contain no `-replan-`; `tools/sdd-skill-lint.py` carries a
`REQUIRED` row for the pattern in `sdd-replan/SKILL.md`.
[Priority: must]

### REQ-HARN-004: Budget slot on every dispatch
Every dispatch template — pipeline, fix re-dispatch, fan-out leaf, review, and
chunk verifier — must carry an explicit `Budget:` slot stated in observable
units (e.g. "1 chunk, ≤ 25 tool calls, ≤ 3 test runs"; for a review "≤ 15 tool
calls, read-only"). The orchestrator must fill the slot on every dispatch; a
dispatch with an empty budget is a template violation. The read-only review
dispatch **does** get a budget slot (operator decision, Q-REQ-C in
`index.md`). (see RS-008 Q4 contract table, catalogue A2)
**Acceptance**: each fenced dispatch template in
`skills/sdd-orchestrate/references/dispatch-templates.md` and
`references/fan-out.md` contains `Budget:`; `tools/sdd-skill-lint.py` has a
`REQUIRED` row per template file (REQ-LINT-005).
[Priority: must]

### REQ-HARN-005: Budget exhaustion is a checkpointed return, never a silent overrun
A leaf that reaches its stated budget must stop, write the circuit-break
checkpoint (REQ-HARN-008) when the exhaustion occurs mid-task, and return with
`status: BUDGET_EXHAUSTED` and a `budget_consumed` field in the same observable
units the dispatch's `Budget:` slot was stated in. The orchestrator must use
`budget_consumed` to size the next repair packet's budget (REQ-HARN-011).
`budget_consumed` is **self-reported** by the leaf — the harness exposes no
tool-call counter to the orchestrator — so adherence is only as trustworthy as
the leaf; this is a recorded v1 limitation, not a defect to be fixed in this
cycle. (see RS-008 Q3)
**Acceptance**: the pipeline and fan-out templates instruct the leaf to
self-count in the stated units and to return `budget_consumed`; a `RETURN:`
block with `status: BUDGET_EXHAUSTED` and no `budget_consumed` is treated by the
orchestrator as malformed (REQ-HARN-009) and surfaced at the gate.
[Priority: must]

### REQ-HARN-006: Attempt ledger in sdd-implement
`sdd-implement` must keep, per task in its working context, an attempt ledger
with one entry per attempted fix: `attempt` (ordinal), `hypothesis` (one line),
`change` (files/lines touched, one line), `result` (which tests now pass/fail,
one line). The ledger must also carry a `verified_do_not_touch` list of paths
whose tests pass and that later attempts must not modify. The ledger lives in
the leaf's context only; its sole durable trace is the checkpoint
(REQ-HARN-008). It is **not** a Q-IMPL entry — Q-IMPL records deviation
decisions, the ledger records attempts; when an attempt reveals a spec ambiguity
the implementer files a Q-IMPL entry as today and cites its id in the ledger /
`open_questions`. (see RS-008 Q1, Q3; catalogue A3)
**Acceptance**: `sdd-implement/SKILL.md` Step 3 defines the four ledger fields and
`verified_do_not_touch`; no ledger text is written to `docs/spec/*.md` or
`docs/handoff/kickoff.md`.
[Priority: must]

### REQ-HARN-007: Oscillation rule in stuck detection
`sdd-implement` stuck detection must fire, in addition to its existing triggers
(same test failing 3+ times with different fixes, 2× expected effort, spec
contradiction), when the ledger shows oscillation: (a) an attempt's `result`
reports a test failing that an earlier attempt's `result` reported passing (a fix
re-introduced a fixed failure), or (b) an attempt's `change` matches an earlier
attempt's `change` (a repeated rejected patch). Both are string comparisons over
the ledger and need no new tooling. Firing follows the existing stuck path:
checkpoint (REQ-HARN-008) then replan trigger. (see RS-008 Q3; catalogue A3)
**Acceptance**: `sdd-implement/SKILL.md` Step 3 lists both oscillation conditions
with the word "oscillation"; a ledger fixture with `attempt 2: test_drift
REGRESSED` after `attempt 1: test_drift passes` is described as stuck.
[Priority: must]

### REQ-HARN-008: Circuit-break checkpoint in the plan's blocked-task note
When stuck detection (including oscillation), budget exhaustion, or the
fix-loop cap fires on an implement task, a structured checkpoint must be written
as the blocked-task note under that task in `docs/plan.md` — the slot
`sdd-replan` already defines ("mark blocked tasks — note why they're blocked and
what unblocks them"). The checkpoint must be bounded (≤ ~15 lines) and contain:
failing test names with one-line reasons, the last hypothesis, a one-line-per-
attempt ledger summary, and the open question (citing a Q-IMPL id where one was
filed, never duplicating it). Full tracebacks must not be stored — they are
regenerated by re-running the named tests. The checkpoint is composed from the
`RETURN:` block (REQ-HARN-009) with **no dedicated checkpoint field**: failing
tests + reasons ← `failures[].test` / `failures[].message`; last hypothesis ←
last `ledger[].hypothesis`; ledger summary ← `ledger[].change` + `ledger[].result`
one-liners; open question ← `open_questions[]`. In sequential mode the
implementer writes it; under fan-out the leaf returns it and the orchestrator
applies it in its post-merge bookkeeping (leaves are barred from writing the
plan). A blocked note does not change phase detection (the plan still has
incomplete tasks) and cannot make the plan stale. (see RS-008 Q1; catalogue A4)
**Acceptance**: `sdd-implement/SKILL.md` and `sdd-replan/SKILL.md` state the
checkpoint format and the RETURN-field mapping; a checkpoint fixture is ≤ 15
lines and contains no traceback frames; `sdd-replan` Step 1 reads the checkpoint
as its "stuck state" input instead of "recent conversation context".
[Priority: must]

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
block; the orchestrator skill text names the field-to-consumer mapping
(`tasks_completed` → plan `[x]`, `traceability_fills` → §3e, `failures` /
`ledger` → repair packet and checkpoint, `blocked_writes` → persistence with
scope check); `tools/sdd-skill-lint.py` has a `REQUIRED` row for `RETURN:` /
`status:` in the templates (REQ-LINT-006).
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
affected REQ ids, suggested fix — nothing else), `spec_excerpt` (path + section
+ line range, ≤ 20 quoted lines), `ledger_summary` (one line per prior attempt,
from `RETURN.ledger`), `verified_do_not_touch`. The packet must contain no
reviewer reasoning and no accumulated history beyond the ledger summary, so
REQ-ORCH-012 holds by construction. The leaf must be instructed to act on the
packet and not re-derive the history. (see RS-008 Q3 Schema 2; catalogue B6)
**Acceptance**: `dispatch-templates.md` has a `{repair_packet}` slot in the
`{on_fix_only}` block with the listed fields; `tools/sdd-skill-lint.py` has a
`REQUIRED` row for the slot (REQ-LINT-006); a filled packet fixture for a
two-iteration fix has exactly two `ledger_summary` lines.
[Priority: must]

### REQ-HARN-012: Orchestrator fills the packet from returns, reports and disk
The orchestrator must populate every repair-packet field from one of three
sources only: the previous leaf's or verifier's `RETURN:` block (`failures`,
`ledger_summary`, `verified_do_not_touch`), the review report's finding lines
(`findings`, lifted line-for-line), or files it reads from disk (`spec_excerpt`,
`target`). `iteration`, `budget` and `write_scope` are orchestrator state. It
must never paraphrase, summarize, or add its own or the reviewer's reasoning.
(see RS-008 Q3 "How the orchestrator fills it")
**Acceptance**: `sdd-orchestrate/SKILL.md` names the source of each field; a
packet's `findings` entries are byte-identical to the corresponding review
report lines apart from structural quoting.
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
`sdd-orchestrate/SKILL.md` §The gate branches on the three values;
`tools/sdd-skill-lint.py` carries the producer/consumer `REQUIRED` pair
(REQ-LINT-005).
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

### REQ-HARN-017: Verifier dispatch is paths-only, budgeted, and ephemeral
The chunk-verifier dispatch prompt must carry only: repository root or worktree
path, plan path + `Chunk N`, the spec paths the chunk's tasks trace to, the
project's gate commands, a `Budget:` in observable units (e.g. "1 chunk, ≤ 15
tool calls, ≤ 2 test runs"), the instruction to run Checks 1 and 3 plus gates
and return `CHUNK_VERDICT:` + findings, and the non-interactivity clause — no
implementer reasoning, no review report, no orchestrator conversation. The
verifier's result surfaces as gate text only and is never written to disk
(REQ-ORCH-013 analogue). (see RS-008 Q2 minimal contract)
**Acceptance**: the verifier template has the listed slots and nothing else; no
`docs/` file is written by or on behalf of a verifier.
[Priority: must]

### Context hygiene

### REQ-HARN-018: Pruned state on re-dispatch
A fix re-dispatch or redo dispatch must pass only the **latest** artifact paths
and the **latest** findings (the repair packet, REQ-HARN-011) — never
accumulated prior packets, prior review reports, or conversation history. Large
content must be referenced by path (spec excerpts ≤ 20 quoted lines or a line
range; everything else by path). The orchestrator must keep dispatch prompts
bounded to the template slots; an operator-visible warning is expected if a
prompt exceeds the template's slot set. (see RS-008 Q3; catalogue C8)
**Acceptance**: a second fix dispatch prompt for the same stage contains one
repair packet, not two; no fenced review report appears in a fix prompt.
[Priority: must]

### REQ-HARN-019: Orchestrator owns routing and verdict classification
Phase detection relay, verdict classification (REQ-HARN-013), `CHUNK_VERDICT:`
and `SCOPE:` interpretation (REQ-HARN-014, REQ-HARN-022), cap arithmetic
(REQ-HARN-001/002), repair-packet composition (REQ-HARN-012) and the decision to
merge, re-dispatch, replan or stop are **orchestrator-only** work and must never
be delegated to a pipeline, fix, fan-out or review subagent. `sdd-orchestrate/
SKILL.md` must state this as a principle alongside REQ-ORCH-030
(orchestrator-only dispatch). (see RS-008 Q4 "not mechanical"; catalogue C9)
**Acceptance**: no dispatch template asks the subagent to decide the next stage,
classify a verdict, or judge scope; the principle appears in §Orchestrator-Only
Work.
[Priority: must]

### Boundaries

### REQ-HARN-020: Declared write scope per dispatch
Every leaf dispatch prompt must carry a `Write scope:` slot — a glob list of the
repository paths the subagent may create, modify, delete or rename. The
orchestrator must fill it from a per-stage default table, which must include
each stage skill's legitimate side-writes: research → `docs/research/RS-NNN-*/**`,
`docs/research/index.md`; requirements → `docs/requirements/**`; specs →
`docs/spec/**`, `docs/requirements/traceability.md`; plan → `docs/plan*.md`,
`docs/plan-history/**`; implement (sequential) → the chunk's source/test paths +
`docs/plan.md` + `docs/requirements/traceability.md` + `docs/spec/*.md`; verify →
`docs/verification.md`; fan-out leaf → the chunk-group's code and test paths
**only** (plan and traceability are already barred by `fan-out.md` §2). Review
and verifier dispatches have an empty write scope. The operator may widen a
scope at the gate. (see RS-008 Q5; catalogue E13)
**Acceptance**: pipeline and fan-out templates contain `Write scope:`; the
default table is in `sdd-orchestrate` skill text; `tools/sdd-skill-lint.py` has a
`REQUIRED` row for the slot (REQ-LINT-006).
[Priority: must]

### REQ-HARN-021: Write-scope observation = porcelain delta + committed delta + ancestry
On a leaf's return, the orchestrator must compute the set of written paths as the
**union** of (a) the delta between a `git status --porcelain=v1
--untracked-files=all` snapshot taken before dispatch and one taken on return,
(b) the committed delta `git diff --name-status <HEAD_before> <HEAD_after>`, and
(c) must run `git merge-base --is-ancestor <HEAD_before> <HEAD_after>`, flagging a
non-zero exit as a history rewrite. For a fan-out worktree the same three
commands run against the worktree path and `<base>..<branch>`. Deletions and
renames (`D`/`R`) count as writes. Paths present in both snapshots (pre-existing
untracked noise) cancel. A porcelain-only check is explicitly insufficient
because committed writes vanish from porcelain output. Every observed path is
matched against the declared scope; any path outside it is a **boundary
finding**. (see RS-008 Q5)
**Acceptance**: the three commands are named in `sdd-orchestrate` skill text; a
dispatch that commits `docs/plan.md` outside its scope is flagged even though
porcelain is clean afterwards.
[Priority: must]

### REQ-HARN-022: `SCOPE:` finding surfaces as gate text only
The write-scope result must be presented at the gate **next to** the review
verdict as ephemeral text — never persisted (REQ-ORCH-013 analogue) — in a fixed
shape: the dispatch identity (stage, chunk, worktree/branch), declared scope,
observed writes tagged `IN`/`OUT` with status letter and committed/uncommitted
provenance, then `SCOPE: CLEAN` or `SCOPE: VIOLATION (N paths)` on its own line,
followed by the options `revert path | accept & widen scope | stop`. The
orchestrator must branch on the `SCOPE:` token, not prose. For a fan-out leaf the
check runs **before** merge, so a revert is a `git checkout`/`git reset` on the
leaf branch, never on `main`. (see RS-008 Q5 finding format)
**Acceptance**: the format block is in `sdd-orchestrate` skill text; a VIOLATION
fixture on a leaf shows no merge of that branch; no `docs/` file records the
finding.
[Priority: must]

### REQ-HARN-023: Scope check on the returned-content fallback
When a leaf returns `blocked_writes` (the labeled-content fallback for writes the
harness blocked), the orchestrator must run the same scope match on each labeled
path **before** persisting it, and must refuse — or ask the operator at the
gate — for any out-of-scope path. The orchestrator's own persistence is the
observable event in this case, so the porcelain/commit check alone cannot catch
it. (see RS-008 Q5)
**Acceptance**: a `blocked_writes` entry for `docs/plan.md` from a fan-out leaf is
not written and appears as a boundary finding.
[Priority: must]

### REQ-HARN-024: Commit ownership per dispatch type
Who commits must be pinned per dispatch type: for a **pipeline** dispatch and a
**fix re-dispatch** the orchestrator commits after the gate (the leaf returns
`files_written`, and is not instructed to commit); a **fan-out leaf** commits on
its own branch with inline identity flags (REQ-ORCH-027) and returns `commits`;
**review** and **verifier** dispatches never commit. The dispatch templates must
state the rule for their type. (see RS-008 Q5 "Requirement to pin")
**Acceptance**: each template's return step states commit ownership; a pipeline
leaf that commits anyway is not a scope violation (its commit is inside the
observed window and matched by path) but the template no longer invites it.
[Priority: must]

### REQ-HARN-025: Snapshot ordering excludes the orchestrator's own commit
The "before" snapshot (`HEAD` + porcelain) must be taken immediately before the
dispatch and the "after" snapshot immediately on return, **before** the
orchestrator's own gate commit, so the orchestrator's commit is never inside the
observed window and can never be flagged as a violation. (see RS-008 Q5)
**Acceptance**: the ordering is stated in `sdd-orchestrate` skill text; a
sequential pipeline stage followed by an orchestrator commit yields `SCOPE:
CLEAN` when the leaf stayed in scope.
[Priority: must]

### REQ-HARN-026: Write-scope check v1 limitations are recorded
The v1 write-scope check should record two accepted blind spots in
`sdd-orchestrate` skill text rather than fix them: (a) implement legitimately
edits spec files only inside their `## Implementation Questions` section (Q-IMPL);
a path-level check cannot see that, so a spec-file write in an implement scope is
tagged **advisory** ("verify hunks are under ## Implementation Questions") until a
hunk-level check exists; (b) paths matched by `.gitignore` are not observed
(`--ignored` is not used) — they are not project content. Writes outside the
repository are the sandbox's concern, not this check's. (see RS-008 Q5)
**Acceptance**: both limitations appear in the skill text next to the finding
format; a spec-file write in an implement scope shows the advisory tag in the
finding, not `OUT`.
[Priority: should]

### Constraints

### REQ-HARN-027: No new on-disk artifact type
Every mechanism in this domain must fit inside existing artifacts and dispatch
templates: fix counts are session-scoped, replan counts are derived from
`plan-history`, the ledger lives in leaf context, the checkpoint reuses the plan's
blocked-task note, the `RETURN:` block, repair packet, `VERDICT:`,
`CHUNK_VERDICT:` and `SCOPE:` tokens are return/gate text, and the write scope is
a template slot. REQ-ORCH-004 (kickoff is the only new artifact), REQ-ORCH-013
(reviews ephemeral) and REQ-ORCH-014 (no loop marker / loop log) must remain
satisfied verbatim; no `docs/reviews/`, `.sdd/` or telemetry file is created
(telemetry is deferred to the next cycle, catalogue D11). (see RS-008
Implications for Design)
**Acceptance**: `git ls-files docs/` after a full orchestrated cycle shows no file
type that did not exist before this feature, other than the `docs/plan-history/`
archives `sdd-replan` already produces.
[Priority: must]
