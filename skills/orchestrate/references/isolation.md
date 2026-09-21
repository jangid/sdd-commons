# Isolation Discipline and Orchestrator-Only Work

Reference for `orchestrate` SKILL.md §Isolation Discipline (normative) and
§Orchestrator-Only Work. Nothing here is optional: these are the invariants the
two-dispatch design rests on.

## 1. Isolation discipline (normative) — from §Isolation Discipline

The driver MUST:

1. Dispatch the pipeline and the review as **two separate subagents** per stage.
2. Construct the review dispatch from **artifact paths only** (plus the repo
   root and, for non-research stages, the upstream path). Never include your
   conversation, the pipeline subagent's reasoning, kickoff prose beyond the
   artifact, or draft/intermediate states.
3. On a fix loop, pass the pipeline subagent **only** the review findings plus
   artifact paths — not a re-litigation of the reviewer's reasoning.
4. **`HISTORY_REWRITE` — no automatic reset.** When the write-scope ancestry
   check fails (`HEAD_after` — or a leaf's branch tip — does not descend from
   `HEAD_before` / `<base>`), surface `HISTORY_REWRITE` above the path list,
   count it as a `SCOPE: VIOLATION`, and offer **only `stop`** plus a
   `git reflog` hint; never reset, force-move or merge a rewritten branch on
   your own initiative ([`write-scope.md`](write-scope.md) §3, §5).

Rules 1–3 mirror `review` Step 2's "Do NOT accept as inputs" list, enforced
at dispatch time; rule 4 is the write-scope analogue — observe and report.
Isolation holds **by construction**: a freshly dispatched subagent has no
shared context window to leak through (repo-level context — `CLAUDE.md`,
project memory — is still inherited; the guarantee covers the session's
reasoning and drafts, not repo docs).

## 2. Orchestrator-only work — from §Orchestrator-Only Work

A dispatched subagent's toolset contains **no dispatch tool** (RS-006 Q1), so
work that requires dispatching a subagent is yours — never hand it to a
pipeline dispatch, which would stall or silently under-deliver. The two cases:

1. **Implement-stage fan-out execution** — provisioning worktrees and
   dispatching one leaf per chunk-group is itself dispatch (why fan-out is
   Design B, not nested Design A).
2. **A spike or task that measures or uses dispatch** — e.g. a concurrency
   probe (the RS-006 spike was run this way).

Ordinary stage work — invoking an `sdd:*` skill, reading/writing files — stays
delegable. The test: *does executing this task require dispatching a subagent?*
If yes, you do it.

## 3. Routing is orchestrator-only (REQ-HARN-019) — from §Orchestrator-Only Work

Phase-detection relay; `VERDICT:` classification; `CHUNK_VERDICT:`,
`RED_VERDICT:` and `SCOPE:` interpretation; fix / redo / replan cap arithmetic;
repair-packet composition; and the decision to merge, re-dispatch, replan or
stop never appear as instructions in any pipeline, fix, fan-out, verifier or
review template. Templates say what to *produce* (the `RETURN:` block, the
verdict token, findings) — never what to *decide next*; `Write scope:` is a
bound you check, not something the subagent judges:
[`return-contract.md`](return-contract.md) §9; `SCOPE:` branching
[`write-scope.md`](write-scope.md); counters
[`loop-control.md`](loop-control.md).
