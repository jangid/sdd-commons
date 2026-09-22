---
domain: HARN
last_updated: 2026-09-22
status: Approved
research_refs: [RS-008, RS-005, RS-006, RS-HARNESSP3-001, RS-HARNESSP4-001, RS-HARNESSP5-001, RS-HARNESSP6-001]
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

### REQ-HARN-HARNESSP3-001: Write-scope observation is a content decision, bounded to the already-dirty set
The write-scope check must add a **content-hash observation** to
`references/write-scope.md` §3 beside the existing observation commands (named
"content-hash observation", never "the fourth observation" — §3 already calls
the named-base observation a four-part one). It computes `(path, sha)` pairs
over **only the ambiguous set** — the paths `snapshot(before)` already lists as
dirty or untracked — before the dispatch, and over the intersection of that set
with `snapshot(after)` afterwards; the content delta is the pairs whose sha
changed plus paths present in `sha.before` and now absent. `observed writes` is
the union of the porcelain delta, the committed delta and the content delta.
§3's rule "Paths present in both snapshots ... cancel — only the *delta* is a
write" must become "cancel **only when their content hash is also unchanged**".
The `SCOPE:` token, the `IN`/`ADVISORY`/`OUT` tags, the `N` count, the finding
block, the operator options and the `HISTORY_REWRITE` rule (which rests on the
untouched ancestry check) are all unchanged — this changes *what counts as an
observed write*, not how one is matched or rendered. Implementation must parse
porcelain with `-z`, enter **both** paths of a rename/copy (`R`, `C`) record
into the set, and record a path deleted during the dispatch as a sentinel
"absent" pair (itself a content change). The accepted §5 limitation that a file
modified and reverted within one dispatch stays invisible is unchanged. Bounding
to the dirty set keeps the cost O(dirty files), not O(repo). (see
RS-HARNESSP3-001 Q1 — probe-evidenced: probe 1 reproduced the blindness and the
remedy; probe 2 measured 134 files = 0.064 s, an 8-path set = 0.017 s against a
0.008 s porcelain baseline, and rejected `git stash create` (7 loose objects
written per snapshot — the orchestrator would mutate the repo it observes) and a
temp-index `read-tree HEAD` + `diff --stat` (diffs against HEAD, identical
blindness))
**Acceptance**: `references/write-scope.md` §3 contains the content-hash
observation block and the amended cancel bullet, §5's limitation wording
matches, and `docs/spec/harness-write-scope.md` carries the same contract; a new
`tools/sdd-scope-check-selftest.py` fixture **F10** (the next free id — F8 and
F9 are taken) in which a path is already dirty at snapshot time and the leaf
re-touches it yields a non-empty observed-write set naming that path, while the
same fixture with the leaf leaving it untouched yields `SCOPE: CLEAN`.
[Priority: must]

### REQ-HARN-HARNESSP3-004: The marker-4 specs write-scope row names the per-workstream traceability path
The **specs** row of the default write-scope table in
`references/write-scope.md` §2 must name `docs/ws/<id>/traceability.md` under
marker `4`, not leave it to the section's marker-4 note. §2's note and §9
already resolve the traceability write to its `docs/ws/<id>/` equivalent, but
the row itself reads `docs/spec/**, docs/requirements/traceability.md`, and the
table is what fills `{write_scope}` at dispatch time. Because
`docs/spec/ws-traceability.md` Q-IMPL-011 makes `sdd-specs` fill the **Spec**
column of `docs/ws/<id>/traceability.md` under marker `4`, a specs leaf doing
exactly what its skill mandates is tagged `OUT` — a false `VIOLATION` of the
same class the 2026-09-17 re-walk note in §2 was written to prevent for
`sdd-verify`'s Verified-column write. (see RS-HARNESSP3-001 Q7(a) — spec-read;
the false `VIOLATION` follows from the two committed texts as they stand)
**Acceptance**: the specs row of `references/write-scope.md` §2 names
`docs/ws/<id>/traceability.md` for marker `4`, and
`docs/spec/harness-write-scope.md` carries the same row wherever it repeats the
table; a marker-4 specs dispatch that writes only `docs/spec/**` plus its
per-ws traceability row yields `SCOPE: CLEAN`.
[Priority: must]

### REQ-HARN-HARNESSP4-001: `COMMIT: COMPLETE | INCOMPLETE` — the orchestrator's commit is checked against what it observed
Whenever the orchestrator commits on `proceed` in sequential mode (per-chunk
gate and stage gate alike), it must compare the **observed-writes set** of the
dispatch it is committing against the set of paths that actually **landed** on
the integration line, and render the result as its own gate signal:

```
landed   := git diff --name-only <HEAD_gate> <HEAD_landed>   # two-sha range, captured BEFORE any bookkeeping commit
expected := observed writes                                  # REQ-HARN-HARNESSP4-002 fixes this term
COMMIT: COMPLETE (N paths)
COMMIT: INCOMPLETE (k observed, not landed: <paths>[; j landed, not observed: <paths>])
```

`HEAD_gate` is the integration-line HEAD when the gate decision is taken and
`HEAD_landed` its HEAD immediately after the orchestrator's own commit, before
the aggregate-regeneration commit of REQ-WS-HARNESSP3-001 or any other
bookkeeping commit. The comparand is a **two-sha `git diff --name-only`**, never
`git show --name-only --format= HEAD`: the latter names only the last commit,
which is the regeneration commit at every marker-4 implement chunk and is empty
on a merge commit. The signal has exactly **two members** — `INCOMPLETE` carries
both directions of the set difference (observed-not-landed and
landed-not-observed) as clauses of one line, so the inverse error (the
orchestrator committing a path no leaf wrote) needs no third token. Because the
commit is the *consequence* of the `proceed` decision, the line renders as a
**post-decision closing line of the same gate** (`references/loop-control.md`
§5 item 8) — not between `SCOPE:` and `CHUNK_VERDICT:`, where it would assert a
commit that has not happened, and not deferred to the next gate the way
`TELEMETRY: rec <n>` is, because `COMMIT:` is load-bearing where telemetry is by
contract never load-bearing. On `INCOMPLETE` the gate pauses with
`amend (add the missing paths to the commit) | accept (note) | stop`; the
`accept (note)` note is **recorded in the gate text** and, if the path is never
landed in a later commit of the cycle, in the plan's existing blocked-task note
— the only durable traces REQ-HARN-027 / REQ-ORCH-014 allow; no new artifact is
created. No next dispatch — including the implement-stage review after the last chunk — is
issued until the pause is resolved: the review must see the landed tree, not a
partial one. `amend` does not re-run the write-scope check: every amended path
came from the observed set and was already classified there. (workstream
`harness-p4`; see RS-HARNESSP4-001 §Q1 — comparand probe-evidenced in five
scratch-repo cases, placement constructed; evidence `docs/ws/harness-p3/verification.md`
§V14: Chunk 7's `CLAUDE.md` edits were `IN`, the gate rendered `SCOPE: CLEAN`,
and the path was omitted from the commit, repaired only at `16e240b` after a
human read; review C1 and red R4 share the root cause)
**Acceptance**: `references/write-scope.md` §7 defines the check, the comparand
table (sequential / fan-out per-leaf / fan-out merge step), the two-member token
and the `amend | accept | stop` options; `references/loop-control.md` §5 lists
item 8 "post-decision: `COMMIT:`" and `skills/sdd-orchestrate/SKILL.md` §The
gate, `USAGE.md` §7b, `CLAUDE.md` §Gate vocabulary and `docs/spec/harness-write-scope.md`
state it in one sentence each; a walkthrough of a sequential chunk whose leaf
wrote `a.txt`, `b.txt`, `docs/plan.md` and whose orchestrator staged only two
renders `COMMIT: INCOMPLETE (1 observed, not landed: docs/plan.md)` and pauses
before the next dispatch, while the same chunk fully staged renders
`COMMIT: COMPLETE (3 paths)`; a walkthrough in which the orchestrator also
commits `stray.txt` renders the `landed, not observed: stray.txt` clause on the
same line; a walkthrough where the regeneration commit follows the feature
commit still renders `COMPLETE` (the range is captured before it); this cycle's
`verification.md` records at least one live gate rendering the line.
[Priority: must]

### REQ-HARN-HARNESSP4-002: sequential `expected` is observed writes only — `RETURN.files_written` is never a `COMMIT:` term
In sequential mode the `expected` term of `COMMIT:` must be exactly the
observed-writes set (porcelain ∪ committed ∪ content deltas of
`references/write-scope.md` §3) and must **not** union in the leaf's
`RETURN.files_written`. A path the leaf claims but never wrote — or wrote and
reverted, so no delta observes it — cannot land, and a comparand that unioned
the claim would render `COMMIT: INCOMPLETE (observed, not landed)` for a defect
of the leaf's *return*, not of the orchestrator's commit: a false pause. The
difference `RETURN.files_written − observed` is instead surfaced as a
**return-drift warning** owned by `references/return-contract.md` (which already
owns return-side defects) and excluded from `COMMIT:`. This is the sequential
analogue of the fan-out clause `RETURN.commits ⊆ git rev-list <base>..<tip>`
(REQ-HARN-HARNESSP4-003): both keep a leaf's return error out of the
landed-vs-observed comparison. This ratifies the research's
design-decision-for-requirements and departs from V14's proposed
"`files_written` plus the observed set". (workstream `harness-p4`; see
RS-HARNESSP4-001 §Q1 "Why `RETURN.files_written` is not a term of `expected`" —
constructed; the V14 proposal is in `docs/ws/harness-p3/verification.md` §V14)
**Acceptance**: `references/write-scope.md` §7's comparand table names
observed writes as the sole sequential `expected` term and cross-references the
return-drift warning; `references/return-contract.md` §1 or §3 defines
`RETURN.files_written − observed` as a warning, not a pause; a walkthrough of a
leaf that lists `docs/extra.md` in `files_written` without writing it renders
`COMMIT: COMPLETE` plus a return-drift warning naming `docs/extra.md`, and
never `COMMIT: INCOMPLETE`.
[Priority: must]

### REQ-HARN-HARNESSP4-003: `COMMIT:` under fan-out — per-leaf and merge-step comparands, no third member
Under implement-stage fan-out the same two-member `COMMIT:` signal must be
computed at two points with mode-specific comparands. At the **per-leaf gate**
`expected` is the leaf's observed writes in its worktree and `landed` is its
committed delta `git diff --name-only <base> <tip>` (the write-scope check's own
term (b)), so the comparison reduces to the leaf's uncommitted writes — exactly
what worktree teardown (`references/fan-out.md` §3d) would discard; because the
data exists before the decision, the line renders in position **2b** of the §5
order, after `SCOPE:` and before `CHUNK_VERDICT:`. A second per-leaf clause
checks `RETURN.commits ⊆ git rev-list <base>..<tip>` and reports a claimed sha
not on the branch in the same line. At the **merge step** (`fan-out.md` §3b),
per branch, `expected` is that leaf's committed delta `base..tip` and `landed`
is `git diff --name-only PRE_MERGE HEAD` on the integration branch, rendered as
a post-`proceed` closing line. No third token member is added for a merge that
drops a path: a clean `git merge` — fast-forward or true merge commit — cannot
lose one (`diff PRE HEAD` equalled the leaf delta in both probe cases), and the
conflict → abort → redo path re-derives from a **new** dispatch whose own sets
are compared, so the first attempt's set is discarded by design; preserving the
aborted attempt's path list, if ever wanted, is a repair-packet concern, not a
gate token. (workstream `harness-p4`; see RS-HARNESSP4-001 §Q1 cases 3–5 —
probe-evidenced for the merge behaviour, spec-read for the redo semantics)
**Acceptance**: `references/fan-out.md` §3a.v carries the per-leaf clause and
its 2b placement and §3b the merge-step comparand `PRE_MERGE..HEAD`;
`references/loop-control.md` §5 names position 2b for the per-leaf gate; a
walkthrough of a leaf that made two commits (`a.txt`, then `b.txt`) merged by
fast-forward renders `COMMIT: COMPLETE (2 paths)` — not the false `INCOMPLETE`
that `git show HEAD` would produce; a walkthrough of a true merge commit after an
integration-branch bookkeeping commit renders `COMPLETE` with the leaf's full
delta; a leaf whose `RETURN.commits` names a sha absent from `rev-list` is
reported in the per-leaf `COMMIT:` line; the token family in every file remains
exactly `COMPLETE | INCOMPLETE`.
[Priority: must]

### REQ-HARN-HARNESSP4-004: observed writes are a strict set — `N` counts distinct paths
The observed-writes union of `references/write-scope.md` §3
(`porcelain_delta ∪ committed_delta ∪ content_delta`) must be implemented with
**set** semantics: a path that arrives from more than one term is counted once
in the `N` of `SCOPE: VIOLATION (N paths)` and once in `COMMIT:`'s sets, and the
`Observed writes:` provenance line keeps the **richest** label for it
(committed ≻ content ≻ porcelain). Today `Observation.paths` in
`tools/sdd-scope-check-selftest.py` is an append-ordered list, so a path dirty
at snapshot, committed during the dispatch and dirtied again is appended by two
terms and counted twice — the rendered token then makes a false statement about
a path count the operator reads to size a violation, and the implementation
diverges from an Approved contract that already says `UNION`. (workstream
`harness-p4`; see `docs/ws/harness-p3/verification.md` §V7 — confirmed by
reading, no fixture reaches it)
**Acceptance**: `tools/sdd-scope-check-selftest.py --self-test` gains a fixture
in which one path is observed by both the committed and the content delta and
asserts the rendered `N` is `1` with provenance label `committed`; the shipped
self-test exits 0; `references/write-scope.md` §3 states the de-duplication and
label-precedence rule in one sentence.
[Priority: must]

### REQ-HARN-HARNESSP4-005: `R`/`C` records and `-z` parsing are exercised by self-test fixtures
`tools/sdd-scope-check-selftest.py` must gain fixtures exercising the
`docs/spec/harness-write-scope.md` criterion "porcelain parsing uses `-z` and
enters **both** paths of an `R`/`C` record into the ambiguous set": one scenario
that `git mv`s a scoped path to an out-of-scope path and asserts both the old and
the new path enter the ambiguous set (so the rename is observed rather than
cancelling), and one whose path contains a space, asserting `-z` parsing keeps it
one record. The behaviour is implemented in `snapshot()` / `ambiguous_set` but
none of F1–F13 renames, copies, or uses a path with a space, quote or newline —
the two conditions that make `-z` parsing load-bearing. (workstream `harness-p4`;
see `docs/ws/harness-p3/verification.md` §V6 — recorded, fixture not added
because `tools/` was outside the verify write scope)
**Acceptance**: the two fixtures exist and pass under `--self-test`; mutating
the parser to split on newline instead of NUL makes the space-path fixture fail;
dropping the rename's origin path from the ambiguous set makes the `R` fixture
fail; the shipped self-test exits 0.
[Priority: should]

### REQ-HARN-HARNESSP4-006: `COMMIT:` has a self-test helper covering the five probe cases
`tools/sdd-scope-check-selftest.py` must gain a pure `commit_check(expected,
landed)` helper that renders the `COMMIT:` line of REQ-HARN-HARNESSP4-001 from
two path sets, plus one fixture per case the research probed: sequential
omission (observed-not-landed), sequential inverse (landed-not-observed), fan-out
fast-forward over a two-commit leaf, fan-out true merge commit after an
integration-branch bookkeeping commit, and conflict → abort → redo with a
narrower second leaf (asserting the redo's own sets are compared and no third
member is rendered). The fixtures build throwaway repositories under a temporary
directory exactly as the existing F-series does; nothing touches this
repository's working tree. (workstream `harness-p4`; see RS-HARNESSP4-001 §Q1
cost table — code; the probe transcript is `evidence-appendix.md` §A)
**Acceptance**: `python3 tools/sdd-scope-check-selftest.py --self-test` exits 0
with the five fixtures listed in its output; replacing the two-sha range in the
fast-forward fixture with `git show --name-only --format= HEAD` makes that
fixture fail with a false `INCOMPLETE`, demonstrating why the comparand is the
range.
[Priority: should]

<!-- REQ-HARN-HARNESSP5-NNN (continued from harness-loop-control.md -001). -->

### REQ-HARN-HARNESSP5-002: `harness-commit-fidelity.md` §Comparand Table states `--no-renames -z` and counts C6
`docs/spec/harness-commit-fidelity.md` §Comparand Table must show the
`git diff --name-only` comparands with the flags the tool actually runs —
`--no-renames -z` (rename detection off so both sides agree; NUL-separated so
paths with spaces are one record, REQ-HARN-HARNESSP4-005) — instead of naming
`--no-renames` only in later prose, and its plan-text references to "five
fixtures C1–C5" must read C1–C6, since `tools/sdd-scope-check-selftest.py`
ships C6. Spec text only. (workstream `harness-p5`; see
`docs/ws/harness-p4/verification.md` — the table omits the flags and the count
is stale)
**Acceptance**: `grep -n 'no-renames -z' docs/spec/harness-commit-fidelity.md`
hits inside §Comparand Table; `grep -n 'C1–C5' docs/spec/harness-commit-fidelity.md`
returns nothing; `python3 tools/sdd-scope-check-selftest.py --self-test` lists
C1–C6; `python3 tools/sdd-gc.py --report` raises no new finding.
[Priority: should]

### REQ-HARN-HARNESSP6-001: the write-scope snapshot must observe git-state mutation by a leaf
The write-scope observation window must observe mutation of **git state**, not
only of files. Today the window is a one-directional porcelain delta, a
committed delta between the two `HEAD` shas, and an ancestry check; `git stash`
*removes* lines from the porcelain output and leaves `HEAD` untouched, so it is
invisible to all three — which is exactly why a read-only verifier that ran
`git stash` over nine files of uncommitted work in the harness-p5 cycle produced
`SCOPE: CLEAN`. The orchestrator must therefore record, alongside the existing
`git status --porcelain` read at **both** ends of the existing
`snapshot(before)` / `snapshot(after)` window (no second window): the **stash
count**, the **current branch**, and **`ORIG_HEAD`**. It must raise a
`GIT_STATE` finding when either (i) the stash count, the current branch or
`ORIG_HEAD` differs between the two snapshots; or (ii) the **reverse** porcelain
delta — paths dirty before and not dirty after — is non-empty **after
subtracting the committed delta**, i.e. a path stopped being dirty with no
commit explaining it. The finding renders as a line **inside the existing
write-scope block**, exactly parallel to the existing history-rewrite line, and
counts into `SCOPE: VIOLATION (N paths)`; no new gate token is introduced and
the REQ-ORCH-034 order is unchanged. Because a stash is recoverable, its options
are `restore │ accept (note) │ stop`, with `proceed` unavailable while it is
unresolved. The comparand must not fire on a legitimate dispatch: a normal
implement leaf only *adds* porcelain lines and any dirty path it commits is
subtracted by clause (ii); a fan-out merge is an orchestrator step outside any
leaf's window, and a merge commit is a descendant, so the ancestry check still
passes. (workstream `harness-p6`; kickoff §Scope item 3, settled at DISCUSS as
an **observable** check rather than contract wording; RS-HARNESSP6-001 Q2,
Confidence Medium-High — derived from contract text, not replayed against a
live dispatch, which the self-test scenarios below close)
**Acceptance**: `python3 tools/sdd-scope-check-selftest.py` exits 0 with four
new scenarios — stash-with-pop and stash-and-drop each yield a `GIT_STATE`
finding and `SCOPE: VIOLATION`; an implement leaf that commits a path which was
already dirty at `snapshot(before)` yields `SCOPE: CLEAN`; a fan-out merge
yields `SCOPE: CLEAN`; `skills/sdd-orchestrate/references/write-scope.md` §3
lists the three extra plumbing reads and the reverse-delta subtraction, §5 the
`GIT_STATE` line, §8 its options; `python3 tools/sdd-skill-lint.py` exits 0.
[Priority: must]
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> RS-PIPELINEOBSERVABILITY-001 R4; Q-REQ-PO-B) `[Updated: 2026-09-22]`: the
> options `restore │ accept (note) │ stop` are unchanged, but on a **read-only
> leaf** neither `restore` nor `accept (note)` returns the gate to `proceed`
> on that leaf's verdict — the verdict is **voided** and the gate reopens
> `redo` / re-dispatch (REQ-HARN-PIPELINEOBSERVABILITY-004). Observed: the
> chunk-0 verifier's `GIT_STATE` finding was resolved `restore` and its
> `CHUNK_VERDICT: PASS` was then consumed and the chunk proceeded — detection
> worked twice and the verdict was still trusted. The snapshot, the three
> plumbing reads, the reverse-delta subtraction and the self-test scenarios are
> unchanged.
> **Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
> 2026-09-22)** over the voided verdict on a read-only leaf — a listing grep
> over `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`;
> hits in this requirement's own text and in the index rows citing it are the
> statement itself and are excluded.
> Command: `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/functional/harness-boundaries.md -exec grep -nHwE 'voided' {} +`.
> the listing is REQ-HARN-PIPELINEOBSERVABILITY-004's: `plugins/sdd/skills/**`,
> `plugins/sdd/agents/**` — no hit (today 0; the §1b and §8 sentences are that
> requirement's acceptance); `docs/spec/harness-write-scope.md`
> §Pipeline-Observability Amendment — reconciled, carries the void; the same
> spec's `GIT_STATE` option row and `references/write-scope.md` §7's option row
> (`restore │ accept (note) │ stop`) — reconciled, the options are unchanged
> and the verdict consequence is REQ-HARN-PIPELINEOBSERVABILITY-004's, which
> amends `references/write-scope.md` §8.
> Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
> files the `-l` listing names:
> `plugins/sdd/skills/orchestrate/references/loop-control.md` §1b (the voided
> verdict and its `voided re-dispatch` bound) and
> `references/dispatch-templates.md` (the missing-token rule applied to a
> voided verdict) — reconciled, the sentences
> REQ-HARN-PIPELINEOBSERVABILITY-004's acceptance adds, landed by the
> implement stage, so the "no hit" baseline above is history;
> `docs/spec/harness-loop-control.md` §Fix-Loop Cap ("re-dispatches that count
> nothing"), `docs/spec/skill-lint-v5.md` rows p7–p8 and
> `docs/spec/telemetry-reader.md` assertion (a) — reconciled, they carry or
> check the void; `docs/spec/pipeline-observability.md` — reconciled, the
> cycle's index spec, it lists;
> `docs/requirements/functional/harness-loop-control.md` (REQ-HARN-001's note)
> and `docs/requirements/functional/telemetry.md` (assertion (a)) —
> reconciled, citations of the void.

### REQ-HARN-PIPELINEOBSERVABILITY-004: a `GIT_STATE` or `OUT` finding on a read-only leaf voids that leaf's verdict
When the write-scope observation raises a `GIT_STATE` finding
(REQ-HARN-HARNESSP6-001) or an `OUT` path (including the content-hash
observation of REQ-HARN-HARNESSP3-001) against a **read-only** leaf — the
reviewer, the chunk verifier or the red team — the orchestrator must consume
that leaf's verdict as the negative token with a note (`CHUNK_VERDICT: FAIL
(voided: GIT_STATE)`, `VERDICT: REJECT (voided: …)`, `RED_VERDICT: BROKEN
(voided: …)`): the "unverified is not verified" rule the missing-token case
already applies. The void holds whichever option the operator picks — `restore`
**or** `accept (note)` (Q-REQ-PO-B: the verdict was produced by a leaf that
mutated what it was verifying, and restoring the tree does not restore the
verdict) — and the gate reopens `redo` / a fresh re-dispatch of the leaf, never
`proceed` on the voided verdict. A voided verdict counts toward **no** fix or
redo counter (REQ-HARN-001 as amended — otherwise a stashing reviewer could
drive a stage to the cap with no defect in the artifact); the re-dispatch it
causes is bounded by a per-gate count of voided re-dispatches,
`voided_redispatch_count[<gate>]`, capped at the `REDO_MAX` value — **the same
integer value as the per-chunk redo cap, counted per gate, not per chunk; the
per-chunk cap's semantics are untouched** (Q-REQ-PO-AI). `REDO_MAX` is defined
once, in `docs/spec/harness-loop-control.md` §Redo Cap per Chunk, as the
orchestrator constant (default 3) that `chunk_redo_count[<chunk header>]` is
counted against and that the per-chunk gate renders as `Redo: N of REDO_MAX`;
**no requirement establishes it** — that section is marked an extension of
REQ-HARN-001, REQ-HARN-008 governs the checkpoint written when the cap fires
and not the cap, and every `REDO_MAX` mention in `docs/requirements/**` is a
citation — so this requirement states the definition it relies on: `REDO_MAX`
is that spec section's constant, reused here as a **value** only. The voided
count is a second counter under its own name: it never increments
`chunk_redo_count`, is never shown in the `Redo: N of REDO_MAX` render string
(which stays the per-chunk counter's), and on reaching `REDO_MAX` renders the
existing exhausted gate `stop │ manual intervention` — a session-scoped
counter, no new artifact and no fourth cap name. The bound is a binding clause, not a stated default: its comparand is one
sentence in `references/loop-control.md` §1b naming `REDO_MAX` as the cap on
voided re-dispatches, pinned by a skill-lint `REQUIRED` row (Q-REQ-PO-Q). (see RS-PIPELINEOBSERVABILITY-001 §Q2 recommendation (b), R4,
§Mechanical pin R4.) Touches REQ-HARN-HARNESSP6-001 (amended); leaves
REQ-HARN-014 (a `FAIL` routes to a repair packet — consistent), REQ-HARN-022
(`SCOPE:` token and options — no new token), REQ-HARN-019 (classification
orchestrator-only — the void is orchestrator-side) and REQ-HARN-HARNESSP3-001
(content-hash observation — reused) consistent.
**Acceptance**: `references/loop-control.md` §1b and `references/write-scope.md`
§8 carry the void sentence, pinned by a skill-lint `REQUIRED` row whose removal
in a temp copy makes the linter exit non-zero; `references/loop-control.md` §1b
carries one sentence containing both `voided re-dispatch` and `REDO_MAX`,
pinned by a second skill-lint `REQUIRED` row on that file (pattern: `voided
re-dispatch` and `REDO_MAX` on the same visible line) whose removal in a temp
copy makes the linter exit non-zero, and `python3 plugins/sdd/tools/skill-lint.py
--self-test` exits 0 with its pinned `REQUIRED` count including both rows; `references/dispatch-templates.md`'s
missing-token rule is cross-referenced from it; the cross-field assertion (a)
of REQ-TELEM-PIPELINEOBSERVABILITY-003 fails on the recorded shape (a
`verifier` record with `scope.token = VIOLATION`, a `PASS` verdict and a
`proceed` decision); `docs/spec/harness-write-scope.md` (or the spec the specs
stage names) walks the recorded chunk-0 sequence and shows it now rendering
`CHUNK_VERDICT: FAIL (voided: GIT_STATE)` with `redo` offered and `proceed`
withheld.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
2026-09-22)** over the voided verdict and its `REDO_MAX` bound — a listing grep
over `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits
in this requirement's own text and in the index rows citing it are the
statement itself and are excluded.
Command: `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/functional/harness-boundaries.md -exec grep -nHwE 'voided|REDO_MAX' {} +`.
(word-bounded, so `avoided` in `plugins/sdd/skills/implement/SKILL.md` and
`docs/spec/skill-updates.md` is not a hit; widened from `voided` alone at
requirements review round 8 M1 — Q-REQ-PO-AI — because the bound reuses
`REDO_MAX` and the narrower pattern never listed that constant's definition.)
Every hit, by tree:
- `plugins/sdd/agents/**` — no hit (today 0).
- `plugins/sdd/skills/**` — `voided`: no hit (today 0; the §1b and §8
  sentences and their `REQUIRED` rows are the acceptance above). `REDO_MAX`,
  eight sentences, every one the **per-chunk** cap:
  `orchestrate/references/loop-control.md` §1a (the per-chunk scoping
  sentence — `chunk_redo_count[<chunk header>]`, shown as `Redo: N of 3`
  against `REDO_MAX`, increments only on `fix`, "a verifier re-dispatch does
  not"), §1a checkpoint on redo exhaustion (REQ-HARN-008, trigger label
  `fix-cap`) and §5 signal 3 (the `Redo: N of 3` render);
  `orchestrate/SKILL.md` §The gate (`REDO_MAX` in the per-chunk gate summary);
  `orchestrate/USAGE.md` ("`Redo: N of 3` — the per-chunk redo counter");
  `orchestrate/references/telemetry.md` `redo_count` row (`Redo: N of
  REDO_MAX`); `orchestrate/references/fan-out.md` (`fix-cap` trigger label);
  `implement/references/stuck-detection.md` (the per-chunk redo cap firing at
  that chunk's gate) — all reconciled as-is: each scopes `chunk_redo_count` per
  chunk, which this requirement leaves untouched; the voided count is a
  distinct counter that never appears in the `Redo: N of REDO_MAX` render
  string and reaches the same exhausted gate by its own count, and §1a's "a
  verifier re-dispatch does not" increment is the per-chunk side of this
  requirement's counts-nothing rule.
- `docs/spec/**` — `docs/spec/harness-loop-control.md` §Redo Cap per Chunk
  (the definition: `chunk_redo_count[<chunk header>]` against the orchestrator
  constant `REDO_MAX`, default 3, `Redo: N of REDO_MAX`), its state-table row,
  its §Circuit-Break sentence (per-chunk cap firing), its signal-order row 3,
  its §Pipeline-Observability Amendment ("§Redo Cap per Chunk does not reopen",
  the voided-verdict counts-nothing sentence, the bound cross-reference) and
  its closing routing sentence — reconciled: the definition this requirement
  names, per chunk, untouched; **except** that the amendment's consistency line
  reads "REQ-HARN-002/-008 (`REPLAN_MAX`, `REDO_MAX`)", citing the
  circuit-break checkpoint requirement as the redo cap's — a miscitation
  (round 8 M2) **noted for the specs re-derivation**
  (REQ-REQ-PIPELINEOBSERVABILITY-001 (b)): no requirement establishes
  `REDO_MAX`, and the line must cite §Redo Cap per Chunk instead;
  `docs/spec/harness-write-scope.md` §Pipeline-Observability Amendment (render
  table, §Counting's `voided_redispatch_count[<gate>]` capped at `REDO_MAX`,
  the bound sentence, the chunk-0 walkthrough showing `Redo: 0 of 3` beside
  the voided verdict) and `docs/spec/skill-lint-v5.md` rows p6–p8 with the p8
  note — reconciled, they carry this requirement and already keep the two
  counters distinct; `docs/spec/pipeline-observability.md` (the
  `REDO_MAX`-as-value row: "the counter `voided_redispatch_count[<gate>]` is
  distinct from `chunk_redo_count[<chunk header>]`") — reconciled, the scope
  this body now states; `docs/spec/harness-chunk-verifier.md` §Sequencing,
  `docs/spec/orchestration.md` (`Redo: N of REDO_MAX`), `docs/spec/telemetry.md`
  `redo_count` row and `docs/spec/skill-updates.md` ("`REDO_MAX` with the
  per-chunk session counter") — reconciled, per-chunk citations;
  `docs/spec/telemetry-reader.md` assertion (a) — reconciled, restatement by
  citation.
- `docs/requirements/**` — `harness-boundaries.md` REQ-HARN-HARNESSP6-001's
  note (amended beside) and this requirement — the statement itself;
  `harness-loop-control.md` REQ-HARN-001's note (after round 8 M2 it cites
  §Redo Cap per Chunk as `REDO_MAX`'s only definition) and
  REQ-HARN-PIPELINEOBSERVABILITY-003 ("the chunk's `gate.redo_count` (`Redo: N
  of REDO_MAX`) is untouched" by a `post-manual` review) — reconciled,
  per-chunk, consistent with the scope stated here; `telemetry.md` ("redo
  count per chunk" in REQ-TELEM-HARNESSP2-009's aggregate list, and
  REQ-TELEM-PIPELINEOBSERVABILITY-003 (a)) — reconciled, per-chunk / points
  here; `index.md` Q-REQ-PO-B, -Q, -AI and the pipeline-observability §Open
  Questions entry — the statement itself.
  Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
  files the `-l` listing names: `voided` now hits
  `plugins/sdd/skills/orchestrate/references/loop-control.md` §1b,
  `references/write-scope.md` §8's rows and `references/dispatch-templates.md`
  (the missing-token rule) — reconciled, the sentences the acceptance above
  adds, landed by the implement stage, so the "no hit" baseline above is
  history.
[Priority: must]
