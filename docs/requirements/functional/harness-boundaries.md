---
domain: HARN
last_updated: 2026-09-17
status: Approved
research_refs: [RS-008, RS-005, RS-006]
---

# Requirements: Harness Hardening — Boundaries

## Overview

Third of the three `HARN` files (see `harness-loop-control.md` for the domain
overview, standing constraints, marker-4 resolution rule, procedure-placement
rule and terminology; `harness-verification.md` for the `RETURN:` block, repair
packet and chunk verifier). This file covers **boundaries** (RS-008 Q5;
catalogue E13): a declared write scope per dispatch, filled from a per-stage
default table, checked mechanically on return (porcelain delta + committed delta
+ ancestry) and surfaced as gate text, plus commit ownership per dispatch type
and the snapshot ordering that keeps the orchestrator's own commit out of the
observed window.

Marker-4 resolution rule (restated): under `docs/.sdd-version` == `4` the same
artifacts are rooted at `docs/ws/<id>/` and the revert/merge target is the
workstream branch, not `main`; marker `3` is unchanged. Procedure text for the
scope default table, the three-command check, the finding format, commit
ownership, snapshot ordering and the v1 limitations lands in the new
`skills/sdd-orchestrate/references/write-scope.md`, with a stub/pointer in
`SKILL.md`.

## Requirements

### Boundaries

### REQ-HARN-020: Declared write scope per dispatch
Every leaf dispatch prompt must carry a `Write scope:` slot — a glob list of the
repository paths the subagent may create, modify, delete or rename. The
orchestrator must fill it from a per-stage default table, which must include
each stage skill's legitimate side-writes. The default table (marker `3` paths;
under `docs/.sdd-version` == `4` `docs/plan*.md`, `docs/plan-history/**`,
`docs/verification.md` and the traceability write resolve to `docs/ws/<id>/`
equivalents, while `docs/research/**`, `docs/requirements/**` and `docs/spec/**`
stay shared; marker `3` unchanged):

| Stage / dispatch | Default write scope |
|------------------|---------------------|
| research | `docs/research/RS-NNN-*/**`, `docs/research/index.md` |
| requirements | `docs/requirements/**` (category files, `index.md`, `traceability.md` rows) |
| specs | `docs/spec/**`, `docs/requirements/traceability.md` (Spec column only — no other requirements write) |
| plan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**` (rewrite archives, never `-replan-`) |
| implement (sequential, per chunk) | the chunk's source/test paths, `docs/plan.md`, `docs/plan-*.md`, `docs/requirements/traceability.md` (Test/Implementation columns), `docs/spec/*.md` (Q-IMPL entries — advisory, REQ-HARN-026), `docs/plan-history/*-complete.md` (milestone-complete archives, multi-milestone plans only), `docs/research/RS-NNN-*/**` + `docs/research/index.md` (spike tasks only) |
| verify | `docs/verification.md`, `docs/requirements/traceability.md` (Verified column, Step 3b) |
| replan | `docs/plan.md`, `docs/plan-*.md`, `docs/plan-history/**` (`-replan-` archives); `docs/spec/*.md` only for a Level-2 inline spec change (advisory) |
| fan-out leaf | the chunk-group's code and test paths **only** (plan and traceability are already barred by `fan-out.md` §2) |
| review, chunk verifier | *(empty — read-only)* |

The operator may widen a scope at the gate. **Rationale / re-walk note:** the
table was re-walked on 2026-09-17 against every stage skill's `SKILL.md`
(`sdd-research` Step 5–6, `sdd-requirements` Step 5, `sdd-specs` Step 3b,
`sdd-plan` Step 6 archival, `sdd-implement` Steps 3–4 + spike tasks + milestone
completion, `sdd-verify` Step 3b, `sdd-replan` Steps 3–4) after review finding
C1 showed the first draft omitted `sdd-verify`'s Verified-column write; the
side-writes listed are the ones those skills instruct today, so a legitimate
side-write is tagged `IN`, never a false `VIOLATION`. (see RS-008 Q5; catalogue
E13)
**Acceptance**: pipeline and fan-out templates contain `Write scope:`; the
default table is in `skills/sdd-orchestrate/references/write-scope.md` and
`SKILL.md` has a stub pointing to it; a sequential verify dispatch that fills
the Verified column yields `SCOPE: CLEAN`; `tools/sdd-skill-lint.py` has a
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
**Acceptance**: the three commands are named in
`skills/sdd-orchestrate/references/write-scope.md` (with a one-line pointer in
`SKILL.md`); a dispatch that commits `docs/plan.md` outside its scope is flagged
even though porcelain is clean afterwards.
[Priority: must]

### REQ-HARN-022: `SCOPE:` finding surfaces as gate text only
The write-scope result must be presented at the gate **next to** the review
verdict as ephemeral text — never persisted (REQ-ORCH-013 analogue) — in a fixed
shape: the dispatch identity (stage, chunk, worktree/branch), declared scope,
observed writes tagged `IN` / `OUT` / `ADVISORY` (REQ-HARN-026) with status
letter and committed/uncommitted provenance, then `SCOPE: CLEAN` or `SCOPE:
VIOLATION (N paths)` on its own line (`ADVISORY` paths do not count toward N),
followed by the options `revert path | accept & widen scope | stop`. The
orchestrator must branch on the `SCOPE:` token, not prose. A path listed in the
stage's default scope (REQ-HARN-020) — e.g. `sdd-verify`'s Verified-column
write to `docs/requirements/traceability.md` — is `IN` and never a finding. For
a fan-out leaf the check runs **before** merge, so a revert is a `git checkout`
/ `git reset` on the leaf branch, never on the integration branch. Under
`docs/.sdd-version` == `4` the integration branch — and therefore the
revert/merge target for a sequential dispatch — is the workstream branch, not
`main`; marker `3` is unchanged. (see RS-008 Q5 finding format)
**Acceptance**: the format block is in
`skills/sdd-orchestrate/references/write-scope.md` and `SKILL.md` §The gate
points to it; a VIOLATION fixture on a leaf shows no merge of that branch; no
`docs/` file records the finding.
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
state the rule for their type, and the rule table lives in
`skills/sdd-orchestrate/references/write-scope.md` (pointer in `SKILL.md`).
(see RS-008 Q5 "Requirement to pin")
**Acceptance**: each template's return step states commit ownership; a pipeline
leaf that commits anyway is not a scope violation (its commit is inside the
observed window and matched by path) but the template no longer invites it.
[Priority: must]

### REQ-HARN-025: Snapshot ordering excludes the orchestrator's own commit
The "before" snapshot (`HEAD` + porcelain) must be taken immediately before the
dispatch and the "after" snapshot immediately on return, **before** the
orchestrator's own gate commit, so the orchestrator's commit is never inside the
observed window and can never be flagged as a violation. (see RS-008 Q5)
**Acceptance**: the ordering is stated in
`skills/sdd-orchestrate/references/write-scope.md` next to the three commands;
a sequential pipeline stage followed by an orchestrator commit yields `SCOPE:
CLEAN` when the leaf stayed in scope.
[Priority: must]

### REQ-HARN-026: Write-scope check v1 limitations are recorded
The v1 write-scope check should record two accepted blind spots in
`skills/sdd-orchestrate/references/write-scope.md` rather than fix them: (a)
implement legitimately edits spec files only inside their `## Implementation
Questions` section (Q-IMPL), and replan only for a Level-2 inline change; a
path-level check cannot see that, so a spec-file write in an implement or replan
scope is tagged **`ADVISORY`** ("verify hunks are under ## Implementation
Questions" / "verify this is the Level-2 spec change") until a hunk-level check
exists; (b) paths matched by `.gitignore` are not observed (`--ignored` is not
used) — they are not project content. Writes outside the repository are the
sandbox's concern, not this check's. (see RS-008 Q5)
**Acceptance**: both limitations appear in the references file next to the
finding format; a spec-file write in an implement scope shows the `ADVISORY` tag
in the finding, not `OUT`.
[Priority: should]
[Updated 2026-09-17, RS-HARNESSP2-001] A third limitation, (c) the catch-up
fast-forward false positive, is recorded and remedied by
REQ-HARN-HARNESSP2-001 below; limitation (a) is partially closed for Markdown
paths by the section resolution of REQ-ARB-HARNESSP2-005; limitation (b) gains
the `.sdd/` exception of REQ-TELEM-HARNESSP2-005.

<!-- REQ-HARN-HARNESSP2-NNN: workstream-prefixed additions to the HARN domain
     (marker 4, workstream harness-p2, per docs/spec/ws-ids.md). -->

### REQ-HARN-HARNESSP2-001: Snapshot base is the branch tip the leaf is instructed to reach
The "before" snapshot of REQ-HARN-021/025 must be taken at the commit the leaf
is **instructed to reach**, never at a stale worktree HEAD. Concretely: (i) the
orchestrator must provision every sequential-pipeline and fix worktree at the
intended base — the workstream branch tip under `docs/.sdd-version` == `4`,
`main`/HEAD under marker `3` — exactly as fan-out §3 already does, so the leaf
never needs to catch up; and (ii) when a dispatch prompt nevertheless names a
base commit for the leaf to fast-forward or merge to, `HEAD_before` for the
committed-delta and ancestry checks must be that named base, and any commit
reachable from the named base but not from the provisioned HEAD is excluded
from the observed window and reported on the gate block as `CATCH-UP
<from>..<base> (N commits, excluded — base <sha>)` so the finding format names
the base. The ancestry check stays intact (a rewrite still fails it). Without
this, an instructed catch-up merge renders every commit it brings in as `OUT` —
RS-HARNESSP2-001 Q6 measured 20 false-positive paths on this cycle's first
dispatch. This is limitation (c), recorded beside (a) and (b) in
`references/write-scope.md` §5 with both remedies; (i) is the cheaper and the
default. (see RS-HARNESSP2-001 Q6 probe 2; Implications for Design)
**Acceptance**: `write-scope.md` §5 lists limitation (c) and §3 states the
snapshot-base rule; a `tools/sdd-scope-check-selftest.py` scenario in which the
worktree is provisioned one commit behind the named base and the leaf
fast-forwards yields `SCOPE: CLEAN` with a `CATCH-UP` line naming the base;
the same scenario with an additional out-of-scope leaf write still yields
`VIOLATION (1 paths)`.
[Priority: must]

### REQ-HARN-HARNESSP2-002: Blocked-write fallback documents the scratchpad-staging path as expected, not anomalous
`references/write-scope.md` §6 (blocked-write fallback, REQ-HARN-023) must
document "stage the file in the scratchpad under a neutral name, then copy or
patch it into the repository" as the **expected** write path for research
leaves and fix leaves that write prose about the harness — not as an anomaly
to be reported. Two dispatches in this cycle hit the same two blocks verbatim
(RS-HARNESSP2-001 Q6, and the research artifact's own fix dispatch, iteration
1): the harness's `Write` tool refused the research artifact and the worktree
guard refused a shell heredoc whose *prose* merely mentioned version-control
commands. §6 must state (i) the trigger (prose about version control or the
harness, including inside heredocs), (ii) the staged-then-copied path with a
neutral scratchpad filename, (iii) that the pre-persist match of REQ-HARN-023
applies to the **final** repository path, not the scratchpad name, and (iv)
that `blocked_writes` in the `RETURN:` block is reserved for writes that the
fallback also could not land. The dispatch templates are unchanged; this is a
documentation requirement on the reference only. (see RS-HARNESSP2-001
Implications for Design — "second data point for `write-scope.md` §6")
**Acceptance**: `write-scope.md` §6 contains the staged-then-copied path with
the four points above and cites it as the expected path; a research or fix
leaf that uses it reports `blocked_writes: []` and the file lands in the
observed window as an ordinary `IN` path.
[Priority: should]
