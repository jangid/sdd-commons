---
id: RS-PIPELINEOBSERVABILITY-001
workstream: pipeline-observability
status: Complete
date: 2026-09-22
last_updated: 2026-09-22
questions:
  - "Q1 — Telemetry: what does the reader enforce versus what telemetry.md specifies; what must append validate so that `rec n` is rendered only on a validated write; can the 53 orphan records be migrated or must they be declared lost?"
  - "Q2 — Read-only leaves: can read-only be enforced (tool list, sandbox, hook) or only detected (a GIT_STATE check in the write-scope snapshot), given the leaves need Bash to run quality gates; name the observable that catches the git stash and the in-place edit."
  - "Q3 — Replay the 17 review rounds under a cap that counts consecutive REJECTs and treats APPROVE_WITH_FIXES at cap as apply-and-proceed: which routings change; would tier-heading parsing have caught specs round 4; is a stale cross-reference to a just-fixed section class (a), and what rule decides it?"
  - "Q4 — Replay the 4 manual interventions: would a default re-review have caught the 2 defects and 3 stale claims, and at what cost in rounds?"
  - "Q5 — The two lint rules (literal-anchor, self-matching-grep): false-positive rate on today's corpus, and a decidable definition of self-matching derived at read time."
  - "Q6 — Gaps 7–11: confirm each is a one-line fix and name its falsifier."
budget: "spike 30 tool calls, 0 test runs; each repair dispatch separately budgeted by the orchestrator (30, 20, 20 tool calls, 0 test runs)"
budget_consumed: "spike 17 of 30; repair dispatches 14 of 30, 11 of 20, 12 of 20; orchestrator manual fix at the round-4 gate: not a dispatch; 0 test runs throughout — read-only commands only (summarize, --lint, grep, python inspection). No dispatch overran its budget."
inputs:
  - docs/ws/pipeline-observability/kickoff.md
evidence:
  - .sdd/telemetry.jsonl (gitignored; line count derived by `wc -l`, and it grows during the session) and plugins/sdd/tools/telemetry.py
  - plugins/sdd/skills/orchestrate/references/telemetry.md, write-scope.md, loop-control.md, return-contract.md, dispatch-templates.md
  - plugins/sdd/agents/reviewer.md, chunk-verifier.md, red-team.md
  - plugins/sdd/tools/gc.py, skill-lint.py, .pre-commit-config.yaml
  - docs/ws/consumer-geometry/verification.md, plan.md; git log 89a89e7..ff1810e
---

# Research: The harness verifying itself (RS-PIPELINEOBSERVABILITY-001)

## Questions

Q1–Q6 as restated in the frontmatter. The eleven gaps are carried as evidence
from the kickoff (`docs/ws/pipeline-observability/kickoff.md` §The observation)
and are not re-derived; they are **restated** below so this file is
self-contained. Each gap gets a **falsifier** — a command or input that makes
today's harness render a wrong claim, and that the proposed fix turns red — in
§Falsifier Table (gaps 1–6) or §Q6 (gaps 7–11). Every command in this file was
run as written on 2026-09-22 at working tree `fb4635f` + the uncommitted
research files, and returns the value stated beside it.

**Line-number anchors — a rule for the whole document.** Every `file:NNN`
anchor anywhere below (telemetry.py, write-scope.md, return-contract.md,
loop-control.md, dispatch-templates.md, implement/SKILL.md, the three agent
bodies, gc.py, the consumer-geometry plan and verification, the requirements
category files) is a live line number valid on 2026-09-22 at `fb4635f` only,
and this cycle will edit most of those files. On transcription into
requirements or specs, dereference each anchor to its durable key — REQ id plus
section heading, function name, or the quoted phrase — and carry that; never the
line number. This is the snapshot-comparand class gap 5 names (§Q5), and this
document is itself an instance of it (§Q5's scope table counts 103 such anchors
under `docs/research/**`).

### The eleven gaps (from the kickoff, one line each)

| # | Statement | Answered in |
|---|---|---|
| 1 | Telemetry is written but not readable: the gate rendered `TELEMETRY: rec 39`, the file gained 53 records, `summarize` reads zero of them; `append` validates nothing and is not a subcommand. | Q1 |
| 2 | Read-only leaves are not read-only: the three harness agents declare `Bash` and carry no git-state or file-mutation prohibition; a `git stash` (chunk 0) and an in-place edit of `gc.py` (chunk 2) were observed. | Q2 |
| 3 | The fix-loop cap counts the wrong thing: `FIX_LOOP_MAX` fired at all four document stages on `APPROVE_WITH_FIXES` with zero blocking findings; the class-(b) contradiction pause fired twice on staleness the fix loop's own edits created. | Q3 |
| 4 | Manual orchestrator fixes skip review: four manual interventions introduced 2 defects and 3 stale claims; all 5 orchestrator errors were caught by subagents, none by a gate. | Q4 |
| 5 | No lint for the snapshot-comparand class behind 12 of 17 blocking findings: live `\.md:\d+` line citations and greps that match their own file. | Q5 |
| 6 | Tier headings are not parsed: a review listed entries under `### Blocking` and closed `VERDICT: APPROVE_WITH_FIXES`; nothing *implemented* caught it — the contract already forbade it (`docs/spec/harness-return-contract.md:269` "disagrees with prose → `REVIEW: MALFORMED` pause", §Edge Cases :487–488). | Q3, Falsifier row 6 |
| 7 | `QIMPL_RE` is too loose: a bare `Q-IMPL-029` raised a live `qimpl-undefined` fail instead of being rejected as malformed. | Q6 |
| 8 | The implement dispatch budget under-counts test runs (overruns 8/6 and 18/12); the honest formula is `test_runs = 2 × mutations + gates`. | Q6 |
| 9 | `.claude/` is inside the hygiene hooks' scope; `end-of-file-fixer` cannot open `.claude/settings.json`. | Q6 |
| 10 | Check 3 does not honour a declared test convention; the identical advisory fired 9 of 9 chunks. | Q6 |
| 11 | A same-cycle stale-chain finding is `info`; the §CG-11(b) gap closed only by argument, not by a gate. | Q6 |

### Corrections this spike makes

To the kickoff, by evidence:

1. **Gap 2** — the write-scope snapshot *does* name a `GIT_STATE` check, and it fired twice (Q2).
2. **Gap 7** — it is not a one-line fix (Q6).
3. **Gap 5** — 58 line-citation anchors → **69** (7 files); 5 self-matching greps → **4** parsed with quoted patterns (Q5; the fifth is carried as an open question, §Open Questions).
4. **Q3's premise** "`APPROVE_WITH_FIXES` *at cap*" cannot arise under consecutive-`REJECT` counting — an `APPROVE_WITH_FIXES` resets the run, so only a `REJECT` ever reaches the cap (Q3 V2 rule 2).
5. **Gap 3's framing** — the cap is a symptom; the cause is that the orchestrator re-reviews every `APPROVE_WITH_FIXES` fix although the review skill defines that verdict as "fix, then proceed without re-review" (§Gate observation 2026-09-22, V3).

To this file's own earlier text, by re-running its commands: the Q3 V2 replay is derived per stage from its own table and V2 is fully specified where it meets gap 6; two falsifier commands were replaced because they did not return the stated value as written (gap 1's `grep` — the file has no space after the colon; gap 8's `grep -nE 'test_runs.*(=|×)'` — it matches the budget-parsing regex table at `plugins/sdd/skills/orchestrate/references/telemetry.md:158`, so it returns 1, not 0); the consumer-geometry line range is **L204–L256**, the distinct key-set count is **31**, and the Q5 per-file list has seven files.

Reading convention: `L<n>` is a 1-based line of `.sdd/telemetry.jsonl`
(line count by `wc -l .sdd/telemetry.jsonl` — it grows during the session, so no literal is quoted); the consumer-geometry cycle occupies **L204–L256** — derived by
`grep -n 'consumer-geometry' .sdd/telemetry.jsonl | cut -d: -f1 | sed -n '1p;$p'`
→ `204 256`.

## Findings

### Q1 — Telemetry: what the reader enforces, what append must validate, what can be migrated

**Answer.** The reader enforces a schema the writer never applied. `load()`
admits only a JSON object whose `v` is an int in `{1, 2}` (telemetry.py:430–447);
everything else is counted as "unknown-schema" and dropped before any per-stage
row is built. The 53 consumer-geometry records carry no `v`, no `cycle`, no
nested `dispatch`/`return`/`gate` groups — they are a flat ad-hoc shape
(`ts`, `ws`, `stage`, `kind`, `dispatch` as an **int**, `status`, `budget`,
`consumed`, `paths_written`, `scope`, `sha`) in **31 distinct key sets across 53
records** (derived: `python3 -c "import json;r=[json.loads(l) for l in open('.sdd/telemetry.jsonl')];print(len({tuple(sorted(x)) for x in r if x.get('ws')=='consumer-geometry'}))"` → `31`), with kinds `gate` (14), `commit` (2) and `pr` (1) that are not in the
reader's `KINDS`. `rec 39` was rendered because the writer rule (telemetry.md §3)
counts *successful appends* and names no validation step: the counter measures
that a line was written, not that a record was.

**Evidence.**

- `python3 plugins/sdd/tools/telemetry.py summarize` → the `v`-stamped
  workstreams (harness-p3/p4/p5/p6 — 126 records at the time of the spike,
  growing with this session's appends, since this cycle's own
  `pipeline-observability` records are `v`-stamped; derive live with
  `python3 -c "import json;print(sum(1 for l in open('.sdd/telemetry.jsonl') if isinstance(json.loads(l).get('v'),int)))"`
  → ≥ 126) and `skipped: 130 unknown-schema record(s)` (the orphan population
  does not grow);
  `--workstream consumer-geometry` → `records: 0`. Against it: `grep -c '"ws":"consumer-geometry"' .sdd/telemetry.jsonl` → `53` (the writer emitted compact JSON — no space after the colon), or derived without a literal shape, `python3 -c "import json;print(sum(1 for l in open('.sdd/telemetry.jsonl') if json.loads(l).get('ws')=='consumer-geometry'))"` → `53`.
- `--lint` → `192 finding(s), 4 warning(s)`, every finding `[type] v: None is not an int in the admitted set [1, 2]` — the lint sees the orphans, the summarizer does not; and `--lint` is not run by any gate (it is a run-explicitly tool, CONTRIBUTING §The heavier checks).
- The `v`-less population is 130, of which 53 are consumer-geometry; **all 77 others carry `ws: packaging`** (derived: `python3 -c "import json;r=[json.loads(l) for l in open('.sdd/telemetry.jsonl')];print(sorted({x.get('ws') for x in r if 'v' not in x}))"` → `['consumer-geometry', 'packaging']`). They were not examined further and take the same reader path.
- Records-vs-expected inside the 53: 17 `pipeline` = 16 document-stage dispatches (4 per stage × 4 stages) + **1** implement dispatch (chunk 0, L242); chunks 1–8 have a `gate` record each (L245–L252) and **no** pipeline or verifier record; the single `verifier` record is chunk 0 (L243). Per stage the 17 `pipeline` records distribute research 4, requirements 4, specs 4, plan 4, implement 1, **verify 0** (derived: `python3 -c "import json,collections;print(collections.Counter(x.get('stage') for x in map(json.loads,open('.sdd/telemetry.jsonl')) if x.get('ws')=='consumer-geometry' and x.get('kind')=='pipeline'))"` → `Counter({'research': 4, 'requirements': 4, 'specs': 4, 'plan': 4, 'implement': 1})`): the verify stage has a `review` record (L254) and a `red` record but **no pipeline record for its own dispatch** — the stronger instance of gap 1, a whole stage-level dispatch that left no dispatch record at all. So even the orphan set under-records by ≥ 9 pipeline (8 implement chunks + the verify dispatch) + ≥ 8 verifier records — the count the implication-derived `expected` of `summarize`'s `records-vs-expected:` line (REQ-TELEM-HARNESSP4-002; `references/telemetry.md` §7) exists to expose.
- The example record telemetry.md §2 renders (`v:1`, nested groups) and the DOMAIN_TABLE in telemetry.py are in agreement with each other (the tool's `schema_diff` self-checks that); the writer simply did not use them.

**What `append` must validate** (recommendation, high confidence — all pieces exist in telemetry.py today):

1. The line parses as a JSON **object** (a torn or non-object line is `WRITE FAILED`, never `rec n`).
2. `v` is in `ADMITTED_V` (`v_admitted`, telemetry.py:355).
3. `lint_records([rec])` returns **zero** findings of classes `enum`, `type`, `key-undeclared`, `key-missing` (telemetry.py:1005) — reusing the existing lint, so the domain table stays the single source of truth; `cross-field` and `mistyped-fix` stay warnings at append time because they need the sibling record.
4. Exit non-zero on any of 1–3 **before** writing; the orchestrator renders `rec <n>` only on exit 0, and `<n>` stays the orchestrator's session counter of exit-0 appends (telemetry.md §3 "the append count wins" is unchanged; what changes is that an append now has a failure mode other than an I/O error).

Surface: `telemetry.py append [--file F] < record.json` (stdin), exit 0 on a
validated write and non-zero otherwise, printing **nothing that requires reading
the file** — the orchestrator's session counter, not a line number, is `<n>`
(REQ-TELEM-HARNESSP3-001's "zero reads of the file" rule stays intact; an earlier
form of this recommendation — printing the line number written — would have
needed a read and is withdrawn).
The `TELEMETRY:` family stays four members — no new token.

**Migration of the 53** (medium confidence): a mapping exists for **36** records
and not for 17. `pipeline` (17) and `review` (17) map field-for-field —
`ts` → the three timestamps (identical, honest about lost gate latency), `sha` →
`git.head_before`, `budget`/`consumed` → `dispatch.budget`/`return.budget_consumed`,
`findings.{blocking,substantive,minor}` → `verdict.findings.{C,M,m}`, the flat
`fix_iteration` → `gate.fix_iteration`; `verifier` (1) and `red` (1) map the same
way. `gate` (14), `commit` (2) and `pr` (1) have no v2 kind: a `gate` record is the
**gate group of a dispatch record that was never written** (chunks 1–8), so it
cannot be folded and must be declared lost, along with the two bookkeeping
`commit` records and the `pr` record. The 16 never-written implement/verifier
records are **missing, not lost** — the existing `partial_stamp` note
("verifier, fix and redo records were never written and cannot be
reconstructed") already renders that case. `migrate` already carries the
OPTIONAL `migration` key and the `--out` flag; a second `MIGRATION_FROM` value
(`flat-cg`) is the shape. Recommendation: migrate 36 with the marker, declare 17
lost in the migrated file's first record note, and let the summarizer show the
partial stamps for chunks 1–8 — never back-fill a number the writer did not observe.

**Confidence.** High on enforcement and validation (read from code); medium on
the 36/17 split (the mapping is derived from key sets, not run — 0 test runs).

### Q2 — Read-only leaves: enforce or detect; the observable

**Correction to the kickoff.** The write-scope snapshot **does** name a
`GIT_STATE` check: write-scope.md §3 lines 248–277 (`stash_count`, `branch`,
`ORIG_HEAD`, plus the reverse porcelain delta with the committed delta
subtracted), §8 row (`restore │ accept (note) │ stop`, `proceed` withheld while
unresolved), `plugins/sdd/skills/orchestrate/SKILL.md:279` (the gate's `SCOPE:` row naming `GIT_STATE`); it is in the installed cache too (7 mentions in the
cache's write-scope.md). And it **fired**: L243 records the chunk 0 verifier as
`"scope": "VIOLATION", "finding": "GIT_STATE", "resolved": "reverted_and_verified"`,
and L246 records chunk 2 as `"scope_verifier": "VIOLATION_inplace_edit_restored"`.
Detection is specified, shipped, and worked twice. The gap is elsewhere, in three places:

1. **The prohibition is not written where the leaf reads it.** reviewer.md:42
   ("You change nothing. You write no file and make no commit"), chunk-verifier.md:46
   ("You repair nothing. You write no file, fix no failure and make no commit"),
   red-team.md:42 ("You fix nothing and you commit nothing") — none names git
   state. `grep -lE 'stash|git state|ORIG_HEAD|checkout|reset' plugins/sdd/agents/*.md`
   → **0 files**. A leaf that stashes has broken no sentence it was given.
2. **A violating verifier's verdict is still consumed.** L243/L244: `GIT_STATE`
   → `restore` → `CHUNK_VERDICT: PASS` → `proceed`. Nothing in loop-control §1b
   voids a verdict produced by a leaf that mutated the state it was verifying
   (§1b:90 tags a *writing* verifier's paths `OUT`, but says nothing about the
   verdict; §8's `restore` resolves the finding and `proceed` reopens).
3. **No enforcement surface exists.** `tools:` frontmatter is per tool, not per
   subcommand — `Bash` is required for gates and admits `git stash`. The plugin
   ships no hooks (`ls plugins/sdd` → `agents skills tools`; no `hooks/`).

**Answer — enforce or detect.** Detection is done and should stay the gate's
ground truth. Enforcement is *possible* through one route only: a plugin
`hooks/hooks.json` `PreToolUse` hook on `Bash` refusing a deny-list
(`git (stash|checkout|switch|reset|restore|commit|clean)`, `sed -i`, `>`/`>>`
redirection into a tracked path) — but only if the hook can tell a read-only
leaf from the implementer, which needs the subagent type in the hook input.
**OPEN** on exactly that constraint: whether `PreToolUse` input carries the
subagent's type is not verifiable in this spike (0 test runs); one live dispatch
with a logging hook settles it. If it cannot, the hook is a session-wide rule
that would also block the implementer and is rejected.

**The observable that catches each case** (already specified, cited so the spec
can point at it): the `git stash` — clause (i) `stash_count 0 → 1` and
`ORIG_HEAD` set, plus clause (ii) the nine paths dirty-before/clean-after with no
commit explaining it (write-scope.md:259–270); the in-place edit of `gc.py` —
the **content-hash observation** (write-scope.md §3, REQ-HARN-HARNESSP3-001,
which names it so and forbids "the fourth observation"): `git hash-object` per
already-dirty path, differing hash → `OUT`.

**Recommendation.** (a) Add one git-state sentence to all three agent bodies and
pin it with a skill-lint REQUIRED row so its reversion fails the linter; (b)
make a `GIT_STATE` or `OUT` finding on a **read-only** leaf consume that leaf's
verdict as `FAIL`/`REJECT`/`BROKEN`-with-note — the "unverified is not verified"
rule the missing-token case already uses (dispatch-templates.md:356–358) — so
`restore` reopens `redo`, not `proceed`; (c) the hook as an opt-in, after the
OPEN is settled. Confidence: high on (a)/(b), low on (c).

### Q3 — Replay of the 17 review rounds

The rounds as recorded (verdict; blocking/substantive/minor; annotations):

| Stage | r1 | r2 | r3 | r4 |
|---|---|---|---|---|
| research | REJECT 2/2/3 | AWF **1**/4/4, class (b) pause | REJECT 2/4/4, class (b) pause | AWF **1**/4/4, cap exhausted |
| requirements | AWF 0/4/5 | REJECT 2/5/3 | REJECT 2/4/4 | AWF 0/6/5, cap exhausted |
| specs | REJECT 2/4/3 | AWF 0/4/4 | AWF 0/7/4, 2 orchestrator-caused | AWF **2 by prose**/3/4, cap exhausted |
| plan | REJECT 2/7/5 | REJECT 1/5/4, 1 orchestrator-caused | REJECT 2/4/3 | AWF 0/5/3, cap exhausted |
| verify | AWF 0/6/3 (+ red HELD) | | | |

(AWF = APPROVE_WITH_FIXES. Source: L205–L240, L254.)

**Why the cap fired four times.** loop-control §2 increments `FIX_LOOP_MAX` "once
per fix re-dispatch" regardless of verdict, and §2b routes "`REJECT` (or
`APPROVE_WITH_FIXES` and the operator would fix again)" into the same counter.
Three fix dispatches after *any* mix of verdicts exhaust it. Every one of the
four exhaustions (L211, L220, L230, L240) landed on an `APPROVE_WITH_FIXES`, and
each forced a `manual_intervention` gate decision (L212, L221, L231, L241) — the
four interventions of Q4 are **caused by** this counting, not independent of it.

**Replay under the proposed rule** (cap counts *consecutive* `REJECT`s; an
`APPROVE_WITH_FIXES` applies its fixes and proceeds). Two readings of
"proceeds" give different answers and the difference is the decision:

- **V1 — apply and proceed with no re-review.** Rounds become research 2,
  requirements 1, specs 2, plan 4 = **9 rounds (−7)**, cap exhaustions 0,
  forced interventions 0. Cost: the blocking findings raised *after* an AWF are
  never seen — research r3 (2), requirements r2+r3 (4): **6 blocking findings
  unseen**, all on ground the just-applied fixes touched. V1 is rejected on
  that count.
- **V2 — apply, then one re-review; the cap counts consecutive consumed
  `REJECT`s.** Stated in full because gap 6 changes what a round *is*:

  1. **Consumed verdict.** The verdict the counter reads is the one the gate
     consumes after parsing — including a gap-6 tier/verdict conflict (an
     `APPROVE` or `APPROVE_WITH_FIXES` carrying ≥ 1 item under a
     `Blocking`/`Critical` heading is the contract's existing
     "disagrees with prose" case, `REVIEW: MALFORMED` pause, §Tier-heading
     parsing; on `accept prose manually` the prose lists blocking items, so the
     consumed verdict is `REJECT`; on `re-dispatch review` a fresh round is
     consumed instead). **A prose-accepted `REJECT` counts toward the run
     exactly like a literal one**; the literal token is never read by the
     counter. **A voided verdict does not count** (R4: a read-only leaf that
     mutated git state or wrote a path has its verdict voided) — the void is a
     re-dispatch, like the post-manual review (Q4) and the third opinion
     (REQ-ARB-HARNESSP2-007), which the counter already excludes; otherwise a
     stashing reviewer could drive a stage to the cap with no defect in the
     artifact.
  2. **Counter.** `reject_run` := number of consecutive consumed `REJECT`s;
     any consumed `APPROVE` or `APPROVE_WITH_FIXES` resets it to 0. The cap
     fires when `reject_run` reaches `FIX_LOOP_MAX` (3): no further fix
     dispatch; exhausted gate `stop │ manual intervention` (an intervention
     is followed by a `post-manual` review, Q4). An `APPROVE_WITH_FIXES` can
     never be "at cap".
  3. **`APPROVE_WITH_FIXES` with zero blocking (AWF-b0).** Fixes applied by
     a fix dispatch (does not touch `reject_run`), then **one re-review**.
  4. **Terminators.** [Superseded at the round-4 gate by V3 — §Gate
     observation 2026-09-22: every `APPROVE_WITH_FIXES` is a terminator, not
     only the second consecutive one; rules 3–4 are kept below as the
     replayed design.] `APPROVE`; **two consecutive AWF-b0 rounds** — the
     second round's fixes are applied and `proceed` is offered **without a
     further review**, so this terminating batch is the one write in the
     loop that reaches the next stage un-reviewed. That is a deliberate
     exception to R8's rule, stated so requirements can bind or reject it:
     bounded convergence outranks it here because (a) the batch by
     definition carries zero blocking items — an AWF-b0's fixes are
     material/minor only — and (b) any rule that re-reviews it re-opens the
     chain (the re-review may return AWF-b0 again), leaving `ROUND_MAX` as
     the only terminator. The alternative — a **closing review** of the
     terminating batch whose findings are recorded into the next stage's
     input and never fix-dispatched (a blocking item under it is consumed as
     `REJECT` and extends the run) — costs one round per stage and keeps
     R8's invariant whole; it is decision (iii) in the R6 row, default
     as-written. Then the cap (rule 2); and a backstop **`ROUND_MAX`**
     (default `2 × FIX_LOOP_MAX` = 6 reviews per stage per session) for the
     alternation `REJECT, AWF-b0, REJECT, AWF-b0 …`, which neither rule 2 nor
     the two-AWF-b0 terminator ever stops — it renders the same exhausted
     gate. **`ROUND_MAX` counts every review dispatch at the stage** —
     consumed, voided (R4), post-manual (R8), third-opinion and
     re-dispatched-after-`MALFORMED` alike — because it bounds dispatches,
     not defects: a rule-1 exclusion removes a round from `reject_run`,
     never from `ROUND_MAX`; otherwise a leaf that mutates git state on every
     dispatch would loop unbounded. `ROUND_MAX` is a **fourth harness cap**
     beside `FIX_LOOP_MAX`, `REPLAN_MAX`, `REDO_MAX`; the three-cap
     inventories in CLAUDE.md §Gate vocabulary ("All three caps default to
     3"), `plugins/sdd/skills/orchestrate/SKILL.md` §The gate and
     `references/loop-control.md` §5 must all gain it (R6).
  5. **An `APPROVE_WITH_FIXES` carrying blocking items is never a
     terminator.** With gap 6 shipped and the prose accepted it is a consumed
     `REJECT` (rule 1) and the stage whose AWFs always carry ≥ 1 blocking item
     **terminates on the cap** — three of them in a row are three `REJECT`s.
     Before gap 6 lands (or when the operator re-dispatches the review at
     every conflict instead of accepting the prose) it resets the run but does
     not count toward the two-AWF-b0 terminator, so such a stage terminates on
     `ROUND_MAX`.

  **Replay, per stage, from the table above** (gap 6 shipped; a round the
  recorded cycle never ran is marked `r5?` and assumed to terminate — a lower
  bound):

  | Stage | Consumed sequence under V2 | Terminates | Cap fires | Forced interventions | Rounds (recorded → V2) |
  |---|---|---|---|---|---|
  | research | r1 REJECT (run 1) → r2 AWF b1 = **REJECT** (2) → r3 REJECT (3) → **cap** → intervention → post-manual r4 AWF b1 = **REJECT** (still exhausted) → intervention → r5? | r5? (post-manual) | at r3 | 2 (r3, r4) | 4 → ≥ 5 |
  | requirements | r1 AWF b0 (0) → fix, re-review → r2 REJECT (1) → r3 REJECT (2) → r4 AWF b0 (0) → fix, re-review → r5? | r5? | never | 0 | 4 → ≥ 5 |
  | specs | r1 REJECT (1) → r2 AWF b0 (0) → fix, re-review → r3 AWF b0 → **two consecutive AWF-b0**: r3's fixes applied un-reviewed (rule 4 as written), proceed | r3 | never | 0 | 4 → 3 (r4 never runs) |
  | plan | r1 REJECT (1) → r2 REJECT (2) → r3 REJECT (3) → **cap** → intervention → post-manual r4 AWF b0 (0) → fix, re-review → r5? | r5? | at r3 | 1 (r3) | 4 → ≥ 5 |
  | verify | r1 AWF b0 (0) → fix, re-review → r2? | r2? | never | 0 | 1 → ≥ 2 |

  Totals: recorded 17 rounds, 4 cap exhaustions, 4 forced interventions;
  V2 **2 cap exhaustions (research, plan), 3 forced interventions (research
  ×2, plan ×1)**, and 0 blocking findings ride through under an unconverted
  `APPROVE_WITH_FIXES`. **No V2 round total is claimed**: the per-stage
  "≥ N" figures rest on `r5?`/`r2?` rounds that never ran and are not
  refutable, so requirements should bind **V2 rules 1–4 and the `ROUND_MAX`
  backstop only** and quote no round total. The separable claims —
  the cap fires 2× not 4×; forced interventions are 3 not 4; specs closes at
  r3 — hold **only under two stated assumptions**: (a) *verdict invariance*,
  the recorded verdicts are reused for rounds whose upstream loop behaviour V2
  changes (different fix dispatches, a `MALFORMED` pause before r3); (b)
  *prose acceptance*, the operator picks `accept prose manually` at every
  tier/verdict conflict (research r2, r4) — on `re-dispatch review` the
  re-dispatched round's verdict is unknown and the routing on that branch is
  undetermined. Any acceptance criterion built on them must carry the
  condition "on the recorded verdict sequence, under prose acceptance of every
  tier/verdict conflict" or it is a false criterion. Cost: specs r4's two prose-blocking findings (L230) are never
  raised by a review under V2 — specs closes at r3 — and surface, if at all,
  at the plan stage's review; V2 does not spend fewer review rounds than the
  recorded cycle on any stage of the table.
  Without gap 6 (literal tokens only) research reads r1 REJECT (1), r2 AWF b1
  (0), r3 REJECT (1), r4 AWF b1 (0) → re-review r5?: no cap, no
  intervention, and two blocking-under-AWF rounds pass uncounted — the gap-6
  harm, and the reason gaps 3 and 6 land together.

Recommendation: V2 with gap 6, high confidence on the routing (arithmetic over
the table once the rules above are fixed); the round counts are not a claim
(every `r5?` is an assumed terminating round, so requirements binds the rules,
not a total). V2's saving is **not** review calls: it
is that the exhausted gate renders only on a genuine `REJECT` run (2 instead of
4), that two of the four interventions (requirements, specs) are not forced,
and that every applied fix is re-reviewed before `proceed`. Research is the
stage V2 does not rescue — its blocking items repeat across four rounds, which
is exactly the case the cap exists for.

**Tier-heading parsing.** The parser matches `^VERDICT:` at line start and
nothing else (return-contract.md:416). The binding already exists: the same
file (:422–423) and `docs/spec/harness-return-contract.md:269` (branching row
"missing / unrecognized / disagrees with prose → `REVIEW: MALFORMED` pause:
re-dispatch review │ accept prose manually │ stop") declare a token that
disagrees with its prose malformed, and the spec's §Edge Cases (:487–488)
states gap 6's exact example — "Review with `APPROVE` token but Critical
findings listed: token and prose disagree → malformed". What is missing is an
*operational* definition of "disagrees" that a parser can execute, and an
acceptance criterion that a gate can fail. A parser that also counts list items
under a `Blocking` heading would have caught **three** rounds, not one: specs r4
(recorded as `verdict_prose_conflict: 2_findings_labelled_blocking`, L230 —
noticed by the operator, not by a gate) **and research r2 and r4**, both
`APPROVE_WITH_FIXES` with `blocking: 1` (L207, L211), which nobody flagged.
Rule: `blocking_items := count of list items between the first heading matching
/^#+\s+.*\b(Blocking|Critical)\b/ and the next heading` (both spellings: `agents/reviewer.md` heads the tier `Blocking`, REQ-REV-002 (c) names it "critical findings"); `blocking_items > 0 ∧ VERDICT ≠ REJECT`
→ `REVIEW: MALFORMED (tier/verdict conflict: N blocking under <token>)` — the
existing pause and its existing option set (`return-contract.md:432`:
`re-dispatch review │ accept prose manually │ stop`); no new token, no
conversion. The predicate `VERDICT ≠ REJECT` covers **both** the contract's
literal example (`APPROVE` with blocking items) **and** the case the example
does not name — `APPROVE_WITH_FIXES` with blocking items, which is the shape
of all three recorded rounds and of this cycle's second research review
(returned `APPROVE_WITH_FIXES` beside a finding it tiered Critical). The V2
replay holds under either resolution of the pause: `accept prose manually`
consumes `REJECT` (the arithmetic above), `re-dispatch review` adds one
re-dispatched round per conflict and changes no routing.
reviewer.md:46 already defines `APPROVE` as "no blocking finding", so the rule
enforces the agent's own contract.

**The stale cross-reference.** Both class (b) pauses (research r2→r3) fired on a
reference to a section the fix had just **moved**: the round-N+1 key
`(file, §NewName)` is in neither `K_N` nor `W_N`, because section resolution
(write-scope.md §3) keys the diff's hunks on the heading they sat under
*before* the fix. It is not class (a) — nothing is being reversed — it is
**fix-induced ground**, and the decidable rule is: a round-N+1 finding whose
located section heading **did not exist at round N's sha**
(`git show <sha_N>:<file> | grep -c '^#\+ .*<section>'` = 0) is on ground the
fix created, belongs in `W_N`, and is an ordinary finding, not a pause.
Equivalently: section resolution should add both sides of a moved/renamed
heading to `W_N`. Confidence: high on the classification, medium on the rule
(derived from the two pauses' shape as recorded; the round texts are ephemeral).

### Gate observation 2026-09-22 — V3, adopted by the operator at this spike's own round-4 gate

Written by the orchestrator at the research gate, not by a dispatch, after
this file's own review loop reproduced the defect it describes. Evidence is
the recorded rounds of consumer-geometry (§Q3 table) plus this file's four:

| Stage | Round sequence (verdict / blocking) | Ended |
|---|---|---|
| cg research | REJECT 2, AWF 1, REJECT 2, AWF 1 | cap, manual intervention |
| cg requirements | AWF 0, REJECT 2, REJECT 2, AWF 0 | cap, manual intervention |
| cg specs | REJECT 2, AWF 0, AWF 0, AWF 0 | cap, manual intervention |
| cg plan | REJECT 2, REJECT 1, REJECT 2, AWF 0 | cap, manual intervention |
| this spike | REJECT 2, AWF 1, AWF 0, AWF 0 | cap, this gate |

Eight of the 21 rounds are `APPROVE_WITH_FIXES` with zero blocking findings.
Three contracts disagree on what such a round means:

- `skills/review/SKILL.md` §Verdict definitions: *"Approve with fixes: … Fix
  them, then proceed **without re-review**."* Material findings are "can
  proceed with note", minor ones "defer without documentation".
- `orchestrate/references/return-contract.md` §3: the packet carries
  Critical/Material lines only, *"Minor findings are not carried"*; §6: on
  `APPROVE_WITH_FIXES` re-review is *optional* via a shortcut whose default
  (`loop-control.md` §5a) is to re-review.
- `orchestrate/SKILL.md` §The gate: `loop-back-to-fix` = re-dispatch, *"then
  re-run the review for this stage"* — unconditionally.

The orchestrator follows the third. Every AWF-b0 therefore became a fix plus
a fresh review of a larger artifact (this file: 361 → 515 → 575 → 687 lines
across three fixes), read by a fresh adversarial reviewer with no memory of
the previous round, who finds four to six new Material items on the sections
the fix just wrote — ground the arbitration rule admits as legitimate
(`W_N` includes fix-written sections). Fresh reviewer + growing artifact +
mandatory re-review is a generator; no cap semantics converge it. V2's rule 3
("AWF-b0 → fix + one re-review") keeps the generator and merely bounds it.

**V3 (adopted).** The review skill's definition is the routing: `REJECT` →
fix (Critical/Material only in the packet) → re-review, counted by
`FIX_LOOP_MAX`; `APPROVE_WITH_FIXES` → fix → **proceed, no re-review**,
minor items dropped, the next stage's review reading the fixed artifact as
its upstream; `APPROVE` → proceed. Re-review after an AWF fix only on an
explicit operator opt-in at that gate. Consequences: rounds per stage ≤
`FIX_LOOP_MAX` REJECTs + 1; no `ROUND_MAX` is needed and V2 rules 3–4 and
R6 decisions (ii)–(iii) are moot; R8's invariant reads "no un-reviewed write
except an AWF batch"; gap 3's consecutive-`REJECT` counting still applies to
the cap but is no longer load-bearing on the recorded evidence (under V3
none of the five stages above reaches the cap: cg requirements closes at r1,
specs r2, verify r1, plan r4, research r2 with gap 6). A fourth cause the
orchestrator introduced here: the operator's requirement that research leave
no conflicting requirements was routed into this file as a fix-packet
finding (OP1), pushing requirements-grade content into a research artifact
and requirements-grade criteria onto its reviewers; the contract's own rule
(REQ-HARN-HARNESSP3-005) sends an out-of-fix-scope requirement into the
**next** dispatch's deliverable contract, which is where the requirements
stage receives it.

**Landed manually at this gate, before the requirements dispatch, each with
a skill-lint pin** (dogfooding, kickoff decision 3): `orchestrate/SKILL.md`
§The gate and `docs/spec/orchestration.md` (loop-back row split by verdict);
`loop-control.md` §5a shortcut inverted and §2a exhausted-gate clause for AWF;
`return-contract.md` §6 and `docs/spec/harness-return-contract.md` table row;
an informational `GROWTH:` line at the stage gate (§5 item 6d) rendering the
deliverable's line delta since the previous round. The requirements stage
records these as amendments already in force (R6, R8) rather than proposals.

### Q4 — Replay of the 4 manual interventions

**Evidence.** L212, L221, L231, L241: `decision: manual_intervention`,
`fixes_applied_by: orchestrator`, items applied 5 / 5 (+3 recorded to specs) /
3 (+6 recorded to plan) / 8 (+1 recorded), every one `commit_status: COMPLETE`,
and in every case the **next record is the next stage's dispatch** — no review
between. loop-control §2b offers `stop | manual intervention | authorize extra
iteration` and attaches no re-review to the middle option.

Of the five orchestrator errors, **three are attributable from the records**:
specs r3 `orchestrator_caused: 2` (L228) and plan r2 `orchestrator_caused: 1`
(L236) — each caught by the *next stage's* reviewer, one stage and 3–4 rounds
downstream. The remaining two are not distinguishable in telemetry (the flat
schema has no field for them) and cannot be checked from this deliverable; the
kickoff's 2-defects/3-stale-claims split is **unmeasured** here and is carried
from the kickoff, not asserted. R8's justification rests on the three
attributable cases (specs r3, plan r2) only.

**Answer.** Yes, with high likelihood for the three recorded: the reviewer that
caught each was reading the same file the intervention had just written; a
same-stage re-review dispatched immediately reads the same file one stage
earlier. Cost: **+4 review rounds** (one per intervention, the existing review
template, read-only, ≤ 15 tool calls each), against the ≥ 3 downstream rounds
the errors consumed — a wash, and **the round count is not the justification**.
The rule rests on correctness, as §Q3 already rests V2: an un-reviewed fix
carries defects (three attributable on this cycle), and a gate that offers
`proceed` on an un-reviewed artifact is the only place in the loop where a
write reaches the next stage with no review record between. Under Q3's V2
replay **three interventions are still forced** (research ×2, plan ×1 —
genuine consecutive-`REJECT` runs) and two (requirements, specs) are not, so
the realised cost on this cycle's evidence is **+3 review rounds** under V2
(+4 on the recorded cycle); the two interventions V2 removes are the ones
whose errors specs r3 and plan r2 caught, so under V2 those errors are never
made and the post-manual review's value lies on the research and plan
interventions. Rule: `manual intervention` at a gate → the orchestrator's edits are
observed like a leaf's (the p4 `COMMIT:` comparand already does this), then a
review dispatch labelled `post-manual` runs **before** `proceed` is offered; it
does not increment the fix-loop counter. Constraint 3 of the kickoff already
applies this from the first gate of this cycle.

### Q5 — The two lint rules on today's corpus

**Scope — an explicit decision, not an inherited default.** Both rules are
proposed for `docs/spec/**` and `docs/requirements/**` only, because that is
the corpus whose text is *binding* — a stale anchor or an inflated count there
becomes a false acceptance criterion, which is how 12 of 17 blocking findings
arose — and the corpus gc's other rules already sweep. The rest of the tree
carries the same class; measured read-only over every `.md` git tracks or
leaves untracked-unignored under `docs/` and `plugins/sdd/` (fence-aware,
quoted-pattern greps only — the same parser as the definition below):

| Root | Files | `literal-anchor` hits | in files | self-matching greps |
|---|---|---|---|---|
| `docs/spec` | 39 | 33 | 3 | 4 |
| `docs/requirements` | 32 | 36 | 4 | 0 |
| `docs/research` | 26 | 103 | 10 | 0 |
| `docs/ws` (plan, verification, kickoff, plan-history, traceability) | 58 | 286 | 16 | 0 |
| `plugins/sdd/skills/**/references` | 14 | 0 | 0 | 0 |
| `plugins/sdd/skills` (SKILL.md, USAGE.md) | 11 | 0 | 0 | 0 |
| `plugins/sdd/agents` | 3 | 0 | 0 | 0 |

Spec + requirements = 69 in 7 files, the figure used below; all four
self-matching greps are in `docs/spec`; `docs/research` includes this file,
itself the largest single instance among spikes. Decision and reason:
`docs/ws/**` (286) and `docs/research/**` (103) are **out** — execution and
research records are dated snapshots by contract (a plan's `traces to` line, a
verification's quoted evidence, a spike's "valid on <date>" anchors), where the
line number *is* the evidence being recorded, not a comparand a later reader is
asked to trust; 389 `warn` lines there would bury the 69 that bind.
`plugins/sdd/**` carries zero today, so covering it is free and keeps the class
out of the shipped skill text: recommended **in**, but through skill-lint's
existing drift-phrase mechanism (it already sweeps that tree) rather than by
widening gc's docs scope. Requirements binds: gc rules over `docs/spec/**` +
`docs/requirements/**`; the `literal-anchor` pattern as a skill-lint drift
phrase over `plugins/sdd/**`; `docs/research/**` and `docs/ws/**` out (a
folded `info` over research spikes is in §Open Questions). The measurements
below are over `docs/spec/**/*.md` and `docs/requirements/**/*.md`, fenced
blocks excluded (the same `visible_lines()` discipline gc.py uses).

**`literal-anchor`** (`[\w./-]+\.md:\d+` on a visible line): **69 anchors in 7
files**; two files hold 41 of them (`docs/requirements/integration/packaging.md`
21, `docs/spec/marketplace-packaging.md` 20; then `two-root-linter.md` 11,
`requirements/traceability.md` 8, `requirements/index.md` 6, `skill-lint-v5.md`
2, `requirements/integration/skill-lint.md` 1 — seven files, 69 anchors; the
counter is the fence-aware scan §Falsifier Table row 5 names, not a literal). Every one of the 69 `:NNN`-anchored paths resolves (0 missing **within the anchor set** — the claim is bounded to anchors, not corpus-wide) and **0** anchors cite a line past the
file's end — so the cheap staleness test proves nothing either way; the rule's
value is the *class* (a comparand the artifact itself invalidates), not a
staleness detector. False positives: the rule as specified has none in the
"wrong class" sense, but 69 `warn` lines on day one is the practical
false-positive rate — recommend **fold per file** (7 lines) and exempt the
sha-pinned form (`[0-9a-f]{7}` within 40 characters before the anchor, e.g.
"at `5dffff7`, `x.md:12`"), which is a frozen citation by construction. Severity
`warn`, folded. Confidence: high (measured).

**`self-matching-grep`.** Decidable definition, derived at read time, no
literal list: for a visible line `L` in file `F` containing a grep invocation
with a quoted pattern `P` (or `-e P`) and target arguments `T`: *self-matching*
iff `F ∈ expand(T)` (globs expanded and directories walked relative to the repo
root, the `plugins/sdd/` prefix tried for bare tool paths) **and** `P` compiled
as a regular expression matches `L` itself. Measured: **85** grep invocations
parsed, **4 self-matching outside fences, 0 inside**:
`docs/spec/adversarial-verify.md:529` (`pending-red`),
`docs/spec/arbitrated-handoff.md:475` (`byte-identical`),
`docs/spec/harness-commit-fidelity.md:310` (`COMMIT: `) and `:329`
(`no-renames -z`). All four are counting greps whose own line inflates the
count by one — true positives, matching the kickoff's observed class (it saw 5
live; the parser reads quoted patterns only, so unquoted-pattern invocations
are an undercount, not a false positive). False-positive rate on the parsed set:
0 of 4. As `fail` the rule turns the gate red immediately, so it lands with the
four lines repaired in the same commit (fence the criterion, or add
`--exclude=<own file>` to the command). Confidence: high on the count, medium
on completeness (unquoted patterns unparsed).

### Q6 — Gaps 7–11: one-liners and falsifiers

| Gap | One-liner? | Falsifier today | Fix, and what turns red | Confidence |
|---|---|---|---|---|
| 7 `QIMPL_RE` | **No — corrected.** `docs/spec/` holds **30 legacy bare** `### Q-IMPL-NNN` definitions beside 94 ws-prefixed, and gc.py's pinned counting rule (`docs/research/RS-HARNESSP2-001-harness-p2/findings.md` §Q4 — `sdd-gc` mechanics; `plugins/sdd/tools/gc.py:44–46`; REQ-GC-HARNESSP2-003) admits "absent (legacy bare counter)" as well-formed. Tightening the regex produces 30 false `qimpl-undefined` fails. | `python3 -c "import re;print(re.fullmatch(r'Q-IMPL-[A-Z0-9]+(?:-\d+)?','Q-IMPL-029') is not None)"` → `True`; a plan referencing `Q-IMPL-029` reports `[qimpl-undefined] fail`, never "malformed". | ≈5 lines + a self-test case: under marker 4, a bare reference not among the **defined** bare ids (derived from `QIMPL_DEF_RE` hits at read time, never a list) → new class `qimpl-malformed` fail. Red: the line above still prints `True`, and `--report` on a plan with `Q-IMPL-029` prints `[qimpl-malformed]`. | High on the 30/94 counts (`cat docs/spec/*.md \| grep -cE '^### Q-IMPL-[0-9]{3}\b'` → `30`); medium on the class boundary — see R11. |
| 8 implement budget | Yes | `grep -c mutations plugins/sdd/skills/orchestrate/references/dispatch-templates.md` → `0` (no derivation exists; `dispatch-templates.md:145` pins a fixed `≤ 3 test runs` example); L242 chunk 0 `budget test_runs 6, consumed 8, budget_overrun: test_runs`. | One sentence in the implement dispatch template: `test_runs = 2 × mutations + gates`, `mutations` = the chunk's mutation/reversion demonstrations, `gates` = quality-gate commands. Red: the `grep -c` above returns ≥ 1, and a chunk naming 2 mutations and 2 gates dispatched with `≤ 3 test runs` fails the template lint row. | High (measured; the formula is the kickoff's) |
| 9 `.claude/` in hook scope | Yes | `.claude/settings.json` is git-tracked (`git ls-files .claude` → 1) and on the sandbox write-deny list; `.pre-commit-config.yaml` `exclude:` has four alternatives and no `.claude/`; `pre-commit run end-of-file-fixer --files .claude/settings.json` inside the sandbox → `PermissionError: Operation not permitted` (quoted verbatim in consumer-geometry verification.md §Known-Open (c)). The file already ends in `\n` — the failure is the hook's `rb+` open, not content. | One alternative in the exclude regex: `\| \.claude/  # editor settings, sandbox-denied; not corpus`. Red: reverting it re-raises the `PermissionError` under `--all-files`. The falsifier as stated depends on the sandbox write-deny list, so an acceptance criterion will need a reproduction that does not depend on a sandboxed gate (a candidate, not run here because the hook mutates files: `pre-commit run end-of-file-fixer --all-files --verbose` lists `.claude/settings.json` among the files it processed only when the exclusion is absent). | High (the error is quoted verbatim in `docs/ws/consumer-geometry/verification.md` §Known-Open (c)) |
| 10 Check 3 convention | Yes | implement/SKILL.md:220–224 and chunk-verifier.md:36–39 define coverage as "test files that import from it" only; `grep -c convention plugins/sdd/agents/chunk-verifier.md` → 0; CLAUDE.md declares the `--self-test` convention and the advisory fired 9 of 9 chunks (verification.md §Known-Open (d)). | One sentence in both files: a test convention declared in `CLAUDE.md` (embedded `--self-test`, pre-commit hook entry) satisfies Check 3 for the modules it names. Red: the skill-lint REQUIRED row pinning the sentence fails when it is absent (R14); re-running the chunk verifier on a consumer-geometry chunk reporting 0 advisories instead of 1 is the behavioural consequence, not the pin. | High on the falsifier; the fix amends REQ-CHKC-004's text (R14) |
| 11 same-cycle stale-chain | Yes (severity only; see note below the table) | gc.py:19–20: `[stale-chain] plan-level warn, shared-spec info (folded per pair)`; the §CG-11(b) gap (clause (b) of the consumer-geometry cycle's write-scope acceptance section §CG-11 — `docs/ws/consumer-geometry/plan.md:28`, `verification.md:135`) closed by re-dating two specs (`ae7db6e`) — `gc.py --report` after touching a spec the active plan traces prints `INFO`, and gc never blocks a gate (CLAUDE.md §Cycle signals). | One condition at the fold site: a folded pair whose spec is traced by the **active workstream's** plan (`docs/ws/<id>/plan.md` `traces to`) is `warn`, not `info`. Red: the DONE `GC:` line carries it as `WARN` and routes it through `record | ignore`. Making it *block* a gate would reverse the never-blocks rule and is not recommended. | High on the falsifier; medium on the severity rule (amends REQ-GC-HARNESSP6-003, R15) |

Q6 result: **four one-liners (8, 9, 10, 11) and one that is not (7)**.

Gap 9's falsifier is the one falsifier in this file **not demonstrated as
written**: it depends on the sandbox write-deny list, and the
sandbox-independent reproduction offered in its row is a candidate that was not
run (the hook mutates files; 0 test runs). Every other falsifier command was
re-run and returned its stated value.

Note on gap 11: gate visibility of the stale-chain finding is **by design
absent** — gc never blocks a gate (REQ-GC-HARNESSP2-006) — so the one-liner is
a severity change only; making the finding block a gate is out of scope
(§Scope boundary for requirements).

## Falsifier Table — gaps 1–6 (the "reachable today" constructions)

| Gap | Construction today | Wrong claim rendered | Turns red after the fix | Confidence |
|---|---|---|---|---|
| 1 | `python3 plugins/sdd/tools/telemetry.py summarize --workstream consumer-geometry` → `records: 0`, vs `grep -c '"ws":"consumer-geometry"' .sdd/telemetry.jsonl` → `53`; `python3 plugins/sdd/tools/telemetry.py --help \| grep -c append` → `0` | `records: 0` against 53 lines; the gate said `rec 39` | `append` of `{"ts":"…","ws":"x"}` exits non-zero → `WRITE FAILED`, never `rec n` | High (measured) |
| 2 | A leaf prompt built from any of the three agent bodies (`grep -lE 'stash\|git state\|ORIG_HEAD\|checkout\|reset' plugins/sdd/agents/*.md \| wc -l` → `0`); `git stash` inside it | Verdict `PASS`/`APPROVE`/`HELD` consumed after `GIT_STATE` `restore` (L243→L244) | skill-lint REQUIRED row fails when the git-state sentence is absent (R3); the verdict is consumed as `FAIL`-with-note while the finding stands — pinned by the `--lint` cross-field assertion on `scope.token = VIOLATION` + positive verdict (R4) | High (both cases recorded live) |
| 3 | The requirements stage's recorded sequence `AWF b0, REJECT, REJECT, AWF b0` (Q3 table), or `REJECT, AWF b0, AWF b0` (specs) | `Fix loop exhausted — 3 of 3` at r4 (resp. r3's fixes counted as iteration 3) and a forced `manual intervention` | Under V2 `reject_run` resets at each AWF-b0: requirements' r4 fixes are applied and re-reviewed, specs closes at r3 on two consecutive AWF-b0; the exhausted gate renders only after three consecutive consumed `REJECT`s (plan, research) — pinned by the `--lint` cross-field assertion on `gate.fix_iteration` against the preceding verdict run (R6) | Medium — conditional on verdict invariance and prose acceptance (§Q3); superseded by V3 (§Gate observation 2026-09-22) |
| 4 | Choose `manual intervention`, edit the deliverable, `proceed` | Next stage dispatched with no review record between (L212→L213) | The gate withholds `proceed` until a `post-manual` review record exists — pinned by the `--lint` cross-field assertion that a `manual_intervention` gate record is followed by a `review` record (R8) | High (four recorded instances) |
| 5 | The four lines listed under Q5; `grep -c 'literal-anchor\|self-matching' plugins/sdd/tools/gc.py plugins/sdd/tools/skill-lint.py` → `0` for both files; the anchor count is derived by a fence-aware scan (`re.findall(r'[\w./-]+\.md:\d+', line)` over visible lines of `docs/spec/**/*.md` + `docs/requirements/**/*.md`) → `69` in `7` files | `OK: … clean` over a corpus with 4 self-inflated counts and 69 snapshot anchors | `self-matching-grep` fail ×4; `literal-anchor` warn ×7 (folded) | High on counts; medium on completeness (unquoted greps unparsed) |
| 6 | Review text `### Blocking` + one item + `VERDICT: APPROVE_WITH_FIXES` (parser: `^VERDICT:` only, `return-contract.md:416`; the contract already calls this shape malformed — `harness-return-contract.md:269`, §Edge Cases :487–488 — but nothing implemented counts the tier) | Consumed as `APPROVE_WITH_FIXES` (L207, L211, L230) | `REVIEW: MALFORMED (tier/verdict conflict)` pause under the existing :269 row, for `APPROVE` and `APPROVE_WITH_FIXES` alike — pinned by the `--lint` cross-field assertion on `verdict.findings.C ≥ 1` with a non-`REJECT` token (R10) | High (three recorded instances) |

## Implications for Design

- **One validator, three callers.** `lint_records` already encodes the schema;
  `append` (Q1), `--lint` and `summarize` should share it, so a record the
  summarizer will drop cannot be appended in the first place. No schema change.
- **The cap and the interventions are one defect, but not the whole of it.**
  Fixing gap 3 by V2 removes two of the four gap-4 interventions (requirements,
  specs) on this cycle's evidence; research and plan remain genuine
  consecutive-`REJECT` runs (research only once gap 6 converts its
  blocking-under-AWF rounds), so gap 4's post-manual review is load-bearing on
  the recorded evidence, not just in principle.
- **Detection stays the ground truth for read-only leaves**; enforcement is an
  opt-in hook pending the OPEN in Q2. The two cheap fixes (prohibition sentence
  under lint; violating leaf's verdict voided) close the observed harm.
- **Two parser additions, no new tokens**: tier-heading count on the review
  body (gap 6 — operationalising the contract's existing "disagrees with
  prose" pause, not a new condition) and fix-induced-ground detection by
  heading existence at the round-N sha (Q3). Both consume existing session
  state.
- **Requirements binds V2's rules, not its arithmetic.** The V2 replay's
  per-stage round figures rest on rounds that never ran; requirements should
  bind rules 1–4 and the `ROUND_MAX` backstop only and quote no round total.
  The claims a verify stage can falsify are: cap fires 2× not 4× on the
  recorded sequence; forced interventions 3 not 4; specs closes at r3 — each
  conditional on verdict invariance and prose acceptance (§Q3), and each
  superseded by the V3 routing adopted at the round-4 gate (§Gate observation
  2026-09-22), under which none of the five stages reaches the cap.
- **Lint rules land with their corpus repaired**: `self-matching-grep` as
  `fail` with the four lines fixed in the same commit; `literal-anchor` as
  `warn`, folded per file, sha-pinned form exempt; scope bound explicitly
  (spec + requirements via gc, `plugins/sdd/**` via skill-lint, research and
  ws records out — §Q5).
- **Gap 7 needs a spec sentence, not a regex** — the legacy bare counter is a
  pinned rule; the new class `qimpl-malformed` is scoped to marker 4 and derived
  from definitions at read time.
- **Cache divergence (kickoff constraint 1, recorded as a finding):** at this
  spike the installed cache `sdd-commons/sdd/0.1.0` differs from `plugins/sdd`
  in five files (`skills/orchestrate/USAGE.md`, `references/drift-sweep.md`,
  `references/telemetry.md`, `tools/gc.py`, `tools/skill-lint.py`) and still
  carries the removed `skills/orchestrate/tools/` directory. Nothing was edited
  in the cache; the operator's pre-dispatch update has not landed.

## Scope boundary for requirements

All eleven gaps are proposed for this cycle (kickoff §Scope: 1–8 as work, 9–11
as one-liners — gap 7 now at ≈ 5 lines plus a self-test case). **Not proposed**
this cycle, each an explicit sub-item of a gap:

- Gap 2 (c): the `PreToolUse` deny-list hook — OPEN on whether hook input
  carries the subagent type; detection stays the ground truth.
- Gap 1: back-filling the 17 lost (`gate`/`commit`/`pr`) and the 16
  never-written implement/verifier records — declared lost/missing, never
  reconstructed; migration of the 77 `packaging` records — see §Open Questions.
- Gap 11: making the same-cycle stale-chain finding **block** a gate — would
  reverse the never-blocks rule (REQ-GC-HARNESSP2-006; CLAUDE.md §Cycle signals).
- Gap 5: an unquoted-pattern form of `self-matching-grep` — pending the fifth
  observed case (§Open Questions); and `docs/ws/**` / `docs/research/**` as
  lint scope (§Q5 decision — dated snapshots by contract).

## Requirements-corpus impact

One row per recommended change. Quoted phrases are the binding text as read in
the named file on 2026-09-22; "amends" means the requirement's text must change,
"new" means no existing requirement binds the behaviour. Where an earlier form
of a recommendation contradicted a requirement, the row says whether it was
revised here or is left as a decision for requirements. The document-wide
line-number rule (§Questions) applies to every anchor in this table: carry the
REQ id and the quoted phrase, never the line number.

| # | Change (gap) | Amends / supersedes / conflicts — binding phrase | Must leave intact | Kind |
|---|---|---|---|---|
| R1 | `telemetry.py append` validating through `lint_records`; `rec <n>` only on exit 0 (gap 1) | **Amends** REQ-TELEM-HARNESSP2-004 (`functional/telemetry.md:99`) — "A write failure must not stop the loop: the orchestrator notes `TELEMETRY: WRITE FAILED`": a validation failure becomes a second cause of `WRITE FAILED`. **Amends** REQ-TELEM-HARNESSP3-001 (`:233`) — "`<n>` counts SUCCESSFUL appends": successful now means validated-and-written. **Revised here** to keep P3-001's "the orchestrator performs zero reads of the file" — `append` prints no line number. | REQ-TELEM-HARNESSP2-009 (`summarize` reader — a subcommand is added, none changed); REQ-TELEM-HARNESSP4-004 (`--lint` from "one domain table" — reused, not duplicated); REQ-TELEM-HARNESSP5-004 (shared `v` helper — reused); REQ-TELEM-HARNESSP2-005 (leaf writes → `OUT`); REQ-HARN-HARNESSP4-001/-004/-006 (`COMMIT:` — untouched) | amendment ×2 + new (the `append` subcommand contract) |
| R2 | `migrate` gains `MIGRATION_FROM = flat-cg`; 36 migrated, 17 declared lost (gap 1) | **Amends** REQ-TELEM-HARNESSP4-005 (`:425`) — `migrate` "rewrites the 8 `"Chunk N"` … in place": a second migration shape. **Amends** REQ-TELEM-HARNESSP5-008 (c) (`:650`) — "a `migration.from` value outside the `chunk-string` enum → `[enum]` finding": the enum gains `flat-cg`. | REQ-TELEM-HARNESSP5-003 (v1 records not stamped); REQ-TELEM-HARNESSP5-007 (the p4 fixture and its 67 lines — a **new** frozen fixture of the 53 lines is cut by the operator, the live file being gitignored); REQ-TELEM-HARNESSP4-002/-003/-008 (`expected` derivation renders the partial stamps unchanged) | amendment ×2 + new (fixture) |
| R3 | Git-state prohibition sentence in the three agent bodies, pinned by a skill-lint REQUIRED row (gap 2a) | **Amends** REQ-AGENT-MARKETPLACE-002 (`functional/agents.md:55`) — "its read-only use is a constraint the agent's body states, which no frontmatter field can express": the constraint becomes a named, lint-pinned sentence rather than an unspecified one. | REQ-LINT-HARNESSP6-001/-003 (existing `GIT_STATE` producer/consumer rows — `grep -c GIT_STATE plugins/sdd/tools/skill-lint.py` → `18` — stay; one row pair is added); REQ-HARN-017 (verifier "read-only leaf — paths-only") | amendment + new (lint row) |
| R4 | A `GIT_STATE` or `OUT` finding on a read-only leaf voids its verdict (`FAIL`/`REJECT`/`BROKEN`-with-note) (gap 2b) | **Amends** REQ-HARN-HARNESSP6-001 (`functional/harness-boundaries.md:472`) — "its options are `restore │ accept (note) │ stop`": after `restore` (or `accept`) the leaf's verdict is consumed as the negative token and the gate reopens `redo`/re-dispatch, not `proceed`. **A voided verdict does not count toward `reject_run` (R6)** — at a document stage the read-only leaf *is* the reviewer, so a voided `REJECT` counted as consumed would let a stashing reviewer drive the stage to the cap with no defect in the artifact; the void is a re-dispatch, like the post-manual review (R8) and the third opinion (REQ-ARB-HARNESSP2-007), which the counter already excludes. **Decision for requirements:** whether `accept (note)` also voids (this spike's default: yes — the verdict was produced by a leaf that mutated what it verified). | REQ-HARN-014 ("A FAIL must route to a repair packet" — consistent); REQ-HARN-022 (`SCOPE:` options and token — no new token); REQ-HARN-019 (classification is orchestrator-only — the void is orchestrator-side); REQ-HARN-HARNESSP3-001 (content-hash observation — reused) | amendment |
| R5 | `PreToolUse` deny-list hook (gap 2c) | **Not proposed** (OPEN). If it ever lands: REQ-PC-MARKETPLACE-006 (`integration/pre-commit.md:132`) — "No hook may enforce a rule that is not already stated in a requirement" — is the constraint (a git hook, but the principle transfers). | all | none |
| R6 | V2: cap counts consecutive consumed `REJECT`s; AWF-b0 → fix + one re-review; `ROUND_MAX` backstop (gap 3) | **Amends** REQ-HARN-001 (`functional/harness-loop-control.md:65`) — "cap the number of loop-back-to-fix re-dispatches per stage … at a configurable maximum (default 3)": the counted quantity becomes consecutive consumed `REJECT`s (its own acceptance already reads "a session that reaches REJECT three times on one stage"); `ROUND_MAX` is added beside it; a verdict voided under R4 is excluded from the count (a re-dispatch, not a consumed `REJECT`). Requirements binds rules 1–4 and `ROUND_MAX` only — no round total from the Q3 replay is a binding claim. **Conflicts with** REQ-HARN-013 (`functional/harness-verification.md:105`) — "APPROVE_WITH_FIXES → proceed or fix offered": V2 rule 3 withholds `proceed` on a single AWF-b0 until the re-review. **Amends the cap inventory:** CLAUDE.md §Gate vocabulary ("All three caps default to 3 (`FIX_LOOP_MAX`, `REPLAN_MAX`, `REDO_MAX`)"), `plugins/sdd/skills/orchestrate/SKILL.md` §The gate and `references/loop-control.md` §5 each enumerate three caps; `ROUND_MAX` makes four and every enumeration changes together (pinned by a skill-lint `REQUIRED` row on the fourth name). **Decisions for requirements:** (i) keep `proceed` as an operator option on AWF-b0 (V2 then changes only the counter) or (ii) withhold it until the second consecutive AWF-b0 or `APPROVE` (recommended: Q4 shows un-reviewed fixes carry defects; cost ≥ 1 round per stage); (iii) whether the terminating AWF-b0 batch's fixes go un-reviewed (rule 4 as written — this spike's default, bounded convergence outranking R8 for a batch with zero blocking items) or receive a record-only closing review (R8's invariant kept whole, +1 round per stage). Kickoff constraint 4 ("no extra-iteration authorisations") is operator policy for this cycle; REQ-HARN-001's "explicit operator-authorized extra iteration" option is not removed. | REQ-HARN-011 (`iteration N of MAX` field — `N` becomes `reject_run`); REQ-ORCH-034 (gate order — `loop-control.md` §5 gains a cap line, no ordering changes); REQ-HARN-002/-008 (`REPLAN_MAX`, `REDO_MAX` semantics untouched — only their enumeration grows); REQ-HARN-HARNESSP3-002; REQ-ORCH-018 (REJECT with no actionable findings pauses); REQ-ARB-* (arbitration keys are per round, unchanged) | amendment ×2 (REQ-HARN-001, REQ-HARN-013) |
| R7 | Fix-induced ground: a round-N+1 key whose section heading did not exist at `sha_N` belongs in `W_N` (gap 3b) | **Amends** REQ-ARB-HARNESSP2-002 (`functional/arbitrated-handoff.md:51`) — class (b) is "not among the `file:section` pairs written by the intervening fix dispatch": both sides of a moved/renamed heading are written pairs. **Amends** REQ-ARB-HARNESSP3-001 (`:170`) — "`W_N := sections(fix[N] writes) UNION sections(regeneration writes …)`": gains the heading-existence clause. Must not reopen REQ-ARB-HARNESSP5-001 (`:292`) — "a regeneration that re-emits a section byte-identically adds nothing to `W_N`": a heading that existed at `sha_N` with identical bytes stays out. | REQ-ARB-HARNESSP2-004 (class (a) undetected — this is not (a)); REQ-ARB-HARNESSP2-006/-007 (pause token, third opinion); REQ-ARB-HARNESSP2-001/-008 (keys); REQ-ARB-HARNESSP4-001 (p4 live exercise — historical); REQ-ARB-HARNESSP5-002 (frozen fixture — a **new** case is added, existing cases unchanged) | amendment ×2 + new (fixture case) |
| R8 | `manual intervention` → orchestrator edits observed like a leaf's, then a `post-manual` review before `proceed`; no counter increment (gap 4) | **Amends** REQ-HARN-001 — "offer only stop, manual intervention, or an explicit operator-authorized extra iteration": the middle option gains the mandatory review. Precedent: REQ-ARB-HARNESSP2-007 — a third opinion "is **not** a fix iteration". Justification rests on the three attributable orchestrator errors (specs r3 `orchestrator_caused: 2`, plan r2 `orchestrator_caused: 1`) only; the kickoff's 2-defects/3-stale-claims split is unmeasured (§Q4). | REQ-HARN-019 (routing orchestrator-only); REQ-HARN-HARNESSP4-001 (`COMMIT:` comparand — reused to observe the orchestrator's edits); REQ-REV-003 (review inputs — the post-manual review is an ordinary review dispatch); REQ-TELEM-HARNESSP4-001 (one record per dispatch — the post-manual review gets a `review` record) | new + amendment (REQ-HARN-001) |
| R9 | gc rules `literal-anchor` (warn, folded, sha-pinned exempt) and `self-matching-grep` (fail), corpus repaired in the same commit (gap 5) | **Amends** REQ-GC-HARNESSP2-002 (`integration/drift-sweep.md:56`) — the sweep classification table ("Implemented in gc (needs code)") gains two rules. `fail` fails the commit through REQ-PC-MARKETPLACE-002 ("A hook must fail the commit exactly when its tool exits non-zero") — hence the same-commit repair. | REQ-GC-HARNESSP2-006 (DONE routing: `literal-anchor` → `record \| ignore`; no `--fix`); REQ-GC-HARNESSP2-007 (`--fix` whitelist — neither rule joins it); REQ-PC-MARKETPLACE-006 (rules live in gc's table, not the hook); REQ-GC-HARNESSP6-004 (`visible_lines()` — reused) | new ×2 + amendment (P2-002) |
| R10 | Operationalise the contract's existing "disagrees with prose" malformed condition: `blocking_items` := list items under the first `Blocking`/`Critical` heading; `blocking_items > 0 ∧ VERDICT ≠ REJECT` → the existing `REVIEW: MALFORMED` pause (gap 6) | **Existing binding, no amendment:** `docs/spec/harness-return-contract.md:269` (branching row "missing / unrecognized / disagrees with prose → `REVIEW: MALFORMED` pause: re-dispatch review │ accept prose manually │ stop") and its §Edge Cases (:487–488, "Review with `APPROVE` token but Critical findings listed: token and prose disagree → malformed"); `return-contract.md:422–423` says the same. The contract forbade the recorded rounds; nothing implemented executes "disagrees". The change is (i) the count rule as the executable definition of "disagrees" — a *structural* check on the section REQ-REV-002 (c) requires, which stays inside REQ-HARN-013's "never classify a verdict by parsing prose" and its malformed branch — and (ii) a **new acceptance criterion** on REQ-HARN-013 + REQ-REV-002: a review body with ≥ 1 item under the critical/blocking heading and a token other than `REJECT` renders `REVIEW: MALFORMED (tier/verdict conflict)`. The predicate covers **both** `APPROVE`-with-blocking (the spec's literal example) **and** `APPROVE_WITH_FIXES`-with-blocking (the recorded shape, and this cycle's second research review — `APPROVE_WITH_FIXES` beside a Critical finding); the acceptance criterion should name both. The regex admits both `Blocking` (`agents/reviewer.md:46`) and `Critical` (REQ-REV-002 (c)). The earlier consume-as-`REJECT` form is withdrawn: the pause is the existing binding. | REQ-REV-002 (report sections — unchanged); REQ-HARN-013 (branch table — unchanged; gains acceptance only); REQ-ARB-HARNESSP2-001/-008 (keys per Critical/Material line); REQ-AGENT-MARKETPLACE-002; REQ-HARN-019 | new acceptance criterion on REQ-HARN-013 + REQ-REV-002 (no text amended) |
| R11 | `qimpl-malformed` fail: under marker 4 a bare `Q-IMPL-NNN` reference not among the **defined** bare ids (gap 7) | **Amends** REQ-GC-HARNESSP2-003 (`integration/drift-sweep.md:70`) — placeholders exclude "any id whose `<WS>` token is not a workstream directory under `docs/ws/` **or a legacy bare counter**": a bare id stays admitted only when a bare definition exists (`^### Q-IMPL-NNN` outside fences, `docs/spec/**` — 30 today), otherwise it is malformed, not undefined. **Must not reopen** REQ-GC-HARNESSP3-001 (`:164`) — "Scoping the rule to 'ids that look local' is **declined** — that is not decidable": the new class is derived from the definition set at read time, never from what looks local — requirements must confirm this reading. | REQ-WS-009 (`multi-workstream.md:172` — ids carry a `<WS>` segment; legacy bare ids valid as `default` — the rule enforces it); REQ-GC-HARNESSP6-004 (fence-symmetric definitions — reused); REQ-QIMPL-HARNESSP5-001/-002 (folded entries, broken refs — historical); REQ-LINT-006, REQ-LINT-HARNESSP5-003 (no lint change) | amendment (P2-003) + new class |
| R12 | Implement dispatch template states `test_runs = 2 × mutations + gates`; a lint row pins it (gap 8) | No binding text amends: REQ-HARN-005 (`harness-loop-control.md:126`) binds exhaustion, not sizing; REQ-TELEM-HARNESSP2-002 binds the parsed integer form (the formula yields one); REQ-HARN-009/-017 bind the leaf/verifier slots (the verifier's own `≤ 2 test runs` example is separate). | REQ-HARN-004 (`Budget:` slot present); REQ-HARN-HARNESSP3-003 (`budget_consumed` shape) | new |
| R13 | `.pre-commit-config.yaml` `exclude:` gains `\.claude/` with a reason comment (gap 9) | Satisfies REQ-PC-MARKETPLACE-005 (`integration/pre-commit.md:118`) by construction — "Any path the hooks must not normalise … must be named in an explicit `exclude` pattern in the config, with the reason stated in a comment". | REQ-PC-MARKETPLACE-001..-004, -006; REQ-PC-PACKAGING-001 | new (one requirement naming the path, so the exclusion has a requirement behind it) |
| R14 | Check 3 honours a test convention declared in `CLAUDE.md` (embedded `--self-test`, pre-commit entry) (gap 10) | **Conflicts with** REQ-CHKC-004 (`functional/chunk-close.md:44`) — "at least one corresponding test file that **imports from** the implementation module": an embedded self-test is neither a file nor an import. **Amends** it: a declared convention satisfies the check for the modules it names. | REQ-CHKC-006 (coverage gaps stay advisory); REQ-CHKC-007 (report shape); REQ-HARN-014 (verifier re-runs Check 3 "per REQ-CHKC-004" — follows the amendment by reference) | amendment (REQ-CHKC-004) |
| R15 | Folded stale-chain pair whose spec is traced by the **active** workstream's plan → `warn`, else `info` (gap 11) | **Conflicts with** REQ-GC-HARNESSP6-003 (`integration/drift-sweep.md:274`) — "must be emitted at **`info`** severity, not `warn`" for the folded finding. **Amends** it with the traced-by-active-plan exception; the rationale ("a shared spec lagging that date is the expected steady state") holds for untraced pairs and is the reason the exception is narrow. | REQ-GC-HARNESSP6-001 (closed workstreams skipped); REQ-GC-HARNESSP6-002 (fold per pair); REQ-GC-HARNESSP2-006 (`record \| ignore` routing; gc never blocks a gate); REQ-STALE-001 (skills' own staleness detection — gc does not change it) | amendment (P6-003) |

Two rows revise an earlier recommendation of this spike: R1 (no line number
printed) and R10 (the existing `REVIEW: MALFORMED` pause plus an acceptance
criterion, not a conversion to `REJECT` and not a new malformed condition).
Two rows carry three decisions to requirements: R4 (`accept (note)` voids?) and
R6 (`proceed` on a single AWF-b0? and whether the terminating AWF-b0 batch is
reviewed). No row supersedes a requirement outright.

### Mechanical pin per change

Requirements should write an acceptance criterion only where a run-time check
decides it. For each row above, the surface that **goes red when the change is
reverted** — or an explicit `prose-only` mark where none exists. "Cross-field"
means a `--lint` assertion of the kind `verdict.chunk_verdict`-without-verifier
already is (telemetry.py:1086), checked against the frozen fixtures
(REQ-TELEM-HARNESSP5-007 and R2's new 53-line fixture), so the recorded
consumer-geometry shapes are the reversion witnesses.

| Row | Mechanical surface (red on reversion) | Behavioural consequence (prose-only, not a criterion) |
|---|---|---|
| R1 | `telemetry.py --self-test` case: `append` of a `v`-less object exits non-zero; reversion exits 0 | `rec <n>` never renders on a dropped record |
| R2 | `--self-test` case over the frozen 53-line fixture: `migrate` output is `--lint`-clean and `summarize` shows 36 records + 8 partial stamps | — |
| R3 | skill-lint `REQUIRED` row pinning the git-state sentence in each of the three agent bodies (`skill-lint.py` `REQUIRED` list, :122) | a leaf that stashes has broken a sentence it was given |
| R4 | (i) skill-lint `REQUIRED` row pinning the void sentence in `loop-control.md` §1b / `write-scope.md` §8; (ii) cross-field: a `verifier`/`review`/`red` record with `scope.token = VIOLATION` and the positive verdict token (`PASS`/`APPROVE`/`HELD`) consumed at its gate → finding; the L243→L244 shape is the witness | `restore` reopens `redo`, not `proceed` |
| R5 | none — not proposed | — |
| R6 | (i) cross-field: at a document stage `gate.fix_iteration` equals the run of consecutive `REJECT` tokens over the preceding same-stage `review` records of the cycle; a value that increments across an `APPROVE_WITH_FIXES` → finding (witness: L211, L220, L230, L240); (ii) skill-lint `REQUIRED` rows on `loop-control.md` for `consecutive` and `ROUND_MAX`, and on the four-cap inventory phrase in `orchestrate/SKILL.md` §The gate | the exhausted gate renders only on a genuine `REJECT` run |
| R7 | `scope-check-selftest.py` §Offline Arbitration Fixture: scenarios A1–A3 gain **A4** — a round-N+1 finding under a heading absent at `sha_N` classifies as an ordinary finding in `W_N`; reversion flips A4 to class (b) and the self-test exits non-zero | no class-(b) pause on a heading the fix created |
| R8 | cross-field: a `gate` record with `decision: manual_intervention` whose next same-stage record is not a `review` record labelled `post-manual` → finding (witness: L212→L213) | no un-reviewed write reaches the next stage **except** the fixes of an `APPROVE_WITH_FIXES` batch, which the review skill's own verdict definition sends to `proceed` without re-review (V3, §Gate observation 2026-09-22) — the next stage's review reads that artifact as its upstream |
| R9 | gc `--self-test` cases for both rules; pre-commit fails on the four `docs/spec` lines until repaired | — |
| R10 | cross-field: a `review` record with `verdict.findings.C ≥ 1` and a token other than `REJECT`, at a gate whose decision is not the malformed pause → finding (witness: L207, L211, L230); plus a skill-lint `REQUIRED` row on the tier/verdict sentence in `return-contract.md` | the pause fires where the operator noticed L230 by eye |
| R11 | gc `--self-test` case: a plan citing `Q-IMPL-029` reports `[qimpl-malformed]`; reversion reports `[qimpl-undefined]` | — |
| R12 | skill-lint `REQUIRED` row on the formula sentence in `dispatch-templates.md` (`grep -c mutations` ≥ 1) | budget overruns stop being the honest outcome |
| R13 | sandbox-dependent only (see the note under §Q6): the sandbox-independent reproduction is a candidate, not run | — |
| R14 | skill-lint `REQUIRED` row pinning the convention sentence in both `chunk-verifier.md` and `implement/SKILL.md` (`grep -c convention` → 0 today, ≥ 1 after) | **prose-only:** "re-running the chunk verifier reports 0 advisories" is the consequence a leaf produces, not a gate-decidable check |
| R15 | gc `--self-test` case: a folded pair traced by the active plan is `warn`, an untraced one `info` | the DONE `GC:` line routes it through `record \| ignore` |

## Prototype

None. All evidence is from read-only commands (`summarize`, `--lint`, `grep`,
Python inspection over the corpus); 0 test runs, no throwaway branch.

## Open Questions

- **Q2 enforcement (OPEN):** does `PreToolUse` hook input carry the subagent
  type, so a deny-list hook can bind to read-only leaves only? One live dispatch
  with a logging hook decides it. Until then the hook is not proposed.
- **Q1 migration:** the 36/17 split is derived from key sets, not executed;
  the `migrate` extension should be written against a frozen fixture of the 53
  lines before touching the live file (which is gitignored and unversioned).
- **Q5 dead-path citations (raised at the round-4 gate):** the snapshot-comparand
  class has a path-only form neither rule sees — `literal-anchor` requires `:\d+`.
  The three spec lines Q5 names as self-matching greps also cite paths dead since
  the packaging move (`docs/spec/adversarial-verify.md:529` → `skills/sdd-verify/SKILL.md`;
  `docs/spec/arbitrated-handoff.md:475` → `skills/sdd-orchestrate/references/loop-control.md`;
  `docs/spec/harness-commit-fidelity.md:329` → `tools/sdd-scope-check-selftest.py`,
  `tools/sdd-gc.py`; `ls skills tools` at the repo root → no such directory). So the
  four-line repair Q5 recommends is a repair of two defects per line, and requirements
  must decide whether a third rule (`dead-path-citation`: a repo-relative path inside
  an acceptance criterion that `git ls-files` does not know) lands beside the two, or
  whether the retired-prefix sweep that skill-lint already runs is extended to specs.
- **Q5 completeness:** greps with unquoted patterns are not parsed by the
  definition above; whether the kickoff's fifth observed case is one of them
  decides if the rule needs an unquoted-token form.
- **Q5 scope, research spikes:** `docs/research/**` is out of both rules by
  the §Q5 decision (103 anchors, dated by contract); whether a folded `info`
  line per spike is worth having is left to requirements, default no.
- **The 77 other `v`-less records** (all `ws: packaging`) were not examined;
  they share the reader path and presumably the migration shape. Default for
  requirements: migrate them under the same marker only where their key sets map
  field-for-field as the 36 do, otherwise declare them lost in the same note.
- **V2's `ROUND_MAX` default** (rule 4) is this spike's proposal, not a kickoff
  decision; default `2 × FIX_LOOP_MAX` unless requirements sets another.
- **R4's `accept (note)` voiding** is a decision for the requirements stage,
  default stated in §Requirements-corpus impact. R6's decisions (i)–(iii) are
  closed by V3 (§Gate observation 2026-09-22): an `APPROVE_WITH_FIXES` always
  proceeds after its fix, and no terminating-batch rule exists. (R10's form is no longer open: the pause is the
  contract's existing binding.)

## Recommendation

**Proceed to requirements.** Q1–Q5 close with a recommendation and evidence
(one named OPEN inside Q2, on enforcement only); Q6 returns four one-liners and
names gap 7 as the one that is not; every gap has a falsifier reachable today (gap 9's demonstrated only under
the sandbox — §Q6 note), every recommended change names the requirement ids it
amends or leaves intact and the mechanical surface that goes red on reversion
or is marked prose-only (§Requirements-corpus impact, §Mechanical pin per
change), with one decision (R4) handed to the requirements stage rather than
invented here. The requirements stage binds the V3 routing (§Gate observation
2026-09-22) as the resolution of gaps 3 and 4 together, and receives the
no-conflicting-requirements rule through its own deliverable contract.
