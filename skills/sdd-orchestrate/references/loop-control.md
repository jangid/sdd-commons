# Loop Control — sdd-orchestrate reference

Loop-control **procedure** text moved out of `SKILL.md` (REQ-LINT-007 size
target; REQ-HARN-001, REQ-HARN-002 procedure placement). Each section below is
referenced from a stub in `SKILL.md` that keeps the contract line and the lint
marker literals (`fix-loop cap`, `iteration N of 3`, `replan re-entry cap`,
`CHUNK_VERDICT:`); the canonical per-chunk gate block itself stays in
`SKILL.md` §Per-chunk implement dispatch and per-chunk gate. Every counter here is orchestrator
session state (`docs/spec/harness-loop-control.md` §State Placement) — nothing
is persisted, and no template tells a subagent to count anything
(`SKILL.md` §Orchestrator-Only Work). Contracts:
`docs/spec/harness-loop-control.md`, `docs/spec/harness-chunk-verifier.md`,
`docs/spec/harness-return-contract.md`.

## 1. Per-chunk implement loop — from §Per-chunk implement dispatch and per-chunk gate

The sequential implement stage runs this loop; the PER-CHUNK GATE block it
renders is the canonical copy in `SKILL.md`:

```
for each `### Chunk N:` in plan order:
  1. snapshot(before) → dispatch PIPELINE implement, Chunk N
  2. on return: snapshot(after) → parse RETURN → write-scope check → `SCOPE:` token
  3. branch on RETURN.status (references/return-contract.md §7):
       COMPLETE / PARTIAL → dispatch CHUNK VERIFIER for Chunk N (repo root) → `CHUNK_VERDICT:`
       BLOCKED / BUDGET_EXHAUSTED → no verifier; the leaf's checkpoint is already in the plan
  4. render the PER-CHUNK GATE (SKILL.md block); wait for the operator:
       proceed → orchestrator commits the chunk (commit ownership) → next chunk
       fix     → repair packet (reason: VERIFIER_FAIL, failures ← verifier RETURN.failures,
                 findings: [], iteration ← chunk_redo_count[<chunk header>] + 1) → redo Chunk N → back to 2
       stop    → halt; the chunk's writes stay uncommitted in the working tree
after the last chunk: dispatch the implement-stage sdd-review ONCE on the merged state
                      → the single implement-stage review gate (proceed │ loop-back-to-fix │ stop)
                      → proceed: after the COMMIT: closing line the ORCHESTRATOR (sole writer)
                        flips plan.md `status: complete` in its own bookkeeping commit,
                        `status:` only — signal 8b; a chunk leaf ticks tasks, never `status:`
                      → any numbered chunk task still unticked → no flip: the gate pauses on
                        `PLAN: INCOMPLETE (N of M ticked)` (signal 6b), `replan │ stop` only
```

### 1a. Gate defaults and per-chunk redo counter

- **Defaults.** `proceed` on `CHUNK_VERDICT: PASS` + `SCOPE: CLEAN`; `fix` on
  `FAIL` or `SCOPE: VIOLATION`. `proceed` on a FAIL is an explicit operator
  override recorded as gate text (`CHUNK_VERDICT: FAIL — proceeded by
  operator`); nothing is persisted. An unresolved `OUT` path is resolved by the
  scope options (`revert path | accept & widen scope`) before any choice.
- **Per-chunk redo counter.** `chunk_redo_count[<chunk header>]`, shown as
  `Redo: N of 3` against `REDO_MAX` (default 3, `harness-loop-control.md` §Redo
  Cap per Chunk), increments **only on `fix`** (a `PARTIAL_CONTINUE` or
  fresh-budget `fix` counts; a verifier re-dispatch does not). On exhaustion
  the gate behaves exactly like the fix-loop cap (§2) — `stop │ manual
  intervention │ authorized extra redo` — with the summary compiled from the
  verifier's findings; the operator may choose a replan from there. The redo
  counter is independent of the stage fix-iteration counter: the
  implement-stage review runs once after all chunks, so review-driven and
  verifier-driven loops are distinct.
- **Checkpoint on redo exhaustion (REQ-HARN-008).** When `REDO_MAX` fires at
  an implement chunk the implementer is not running, so the **orchestrator**
  composes the circuit-break checkpoint from the last `RETURN` (`failures`,
  `ledger`, `open_questions`) per the mapping table in
  `sdd-implement/SKILL.md` §Step 3, with trigger label `fix-cap`, and applies
  it as the blocked-task note under the chunk's open task (sequential: in the
  working tree before the gate renders; fan-out: after merge per
  `fan-out.md` §3e.4). `sdd-replan` Step 1 reads it as the stuck state.
- **FAIL routing.** A FAIL routes **only** to a repair packet for a redo of the
  same chunk (`fix`); never directly to a merge, to the implement-stage review,
  or to `sdd-replan`. The per-chunk gate never shows a review `VERDICT:`.
- **Review runs ONCE.** The implement-stage `sdd-review` and its stage gate run
  once, after all chunks, on the merged state: a three-chunk plan yields 3
  implement + 3 verifier dispatches (plus redos), 3 per-chunk gates, **1**
  review with **1** stage gate.
- **Post-review loop-back re-entry.** After a stage-level `loop-back-to-fix`,
  findings are mapped to chunks (`references/return-contract.md` §5 — REQ →
  spec → chunk; unmappable or multi-chunk → one `target.chunk: all` fix
  dispatch). Each fix dispatch is followed by the scope check, **one verifier
  per touched chunk**, and that chunk's per-chunk gate **before** the re-review.

### 1b. Verifier edge cases

- No `### Chunk N:` headers (v2 vocabulary) → one implement dispatch, no
  verifier, stated at the gate.
- A verifier returning `status: BUDGET_EXHAUSTED` is consumed as
  `CHUNK_VERDICT: FAIL`; you may re-dispatch it with a larger budget before
  rendering the gate — a **verifier re-dispatch is not a redo** and does not
  increment `chunk_redo_count`.
- A gate command that exits non-zero on the verifier's run but zero on your
  re-run (or on a redo with no code change) renders as `possible flake` — never
  auto-PASS.
- A verifier that writes anyway gets every path tagged `OUT`, `SCOPE:
  VIOLATION`, and its writes reverted before any redo.

## 2. Fix-loop cap (REQ-HARN-001) — from §The gate

`FIX_LOOP_MAX` is an orchestrator constant, default **3**, keyed by **stage**
and **session-only** — a new session restarts it at 0 (the restart is itself a
human intervention; nothing is persisted, REQ-ORCH-014). It increments once per
fix re-dispatch of that stage's pipeline subagent — never on `proceed`, `stop`
or a replan route. Every fix re-dispatch prompt carries the literal line
`iteration N of 3` (`iteration N of MAX` in general) inside the repair packet
(`references/return-contract.md` §3); `N of N` is the last attempt before
circuit-break. The operator may **raise the cap by one** for the current stage
at the gate by an explicit decision (not itself a fix iteration); each
authorization adds one and the gate renders the raise count — e.g.
`iteration 5 of 5 (cap raised ×2)` — so the history is visible without
persisting it.

### 2a. Exhaustion and the compiled findings log

**Retained per-round state (REQ-ARB-HARNESSP2-001).** Beside the compiled
findings log below, the orchestrator keeps — in session state only, never as
an artifact (REQ-HARN-027) — one tuple per review round and one per fix
dispatch of the active loop. Contract: `docs/spec/arbitrated-handoff.md`
§Retained Per-Round State; the schema is pasted from it:

```
round[N]      = { verdict: APPROVE | APPROVE_WITH_FIXES | REJECT,
                  lines: [ { tier: C | M, text: <verbatim line>,
                             key: { file: <repo-relative path>, section: <§Name> | "?",
                                    affects: { REQ-… } } } ] }
fix[N]        = { written: { (file, section) }, hunks: { (file, section): "L40-58, L120" } }
regen[N]      = { written: { (file, section) }, hunks: { (file, section): "L1-240" }, by: leaf | orchestrator }
                # every orchestrator-dispatched regeneration of the stage deliverable between round N and N+1
                # (a pipeline re-dispatch of the same stage — Q-IMPL-HARNESSP3-010), PLUS derived artifacts the
                # orchestrator itself regenerated in that window, e.g. docs/requirements/traceability.md
                # (by: orchestrator — Q-IMPL-HARNESSP3-017)
W_N           = sections(fix[N].written) UNION sections(regen[N].written)
                # the set §Contradiction classes tests against; (file, *) only where section resolution is unavailable
```

`regen[N]` is a **sibling** set beside `fix[N]`, not a rename of it
(Q-IMPL-HARNESSP3-009): `fix[N]` keeps meaning the fix dispatch's writes, and
`regen[N]` holds the writes of every **regeneration of the stage deliverable**
between round N and round N+1 — defined as a pipeline re-dispatch of the **same**
stage (Q-IMPL-HARNESSP3-010), never another stage's leaf and never an operator's
manual edit, which stays outside the loop's write set. The orchestrator's own
post-gate regeneration of an artifact **derived** from that leaf's output — the
shared aggregate `docs/requirements/traceability.md` — counts with it
(Q-IMPL-HARNESSP3-017). The two sets have
different provenance in the telemetry record and in the ledger, so they are kept
separable; only their union is contractual (§`W_N`, below).

Key parsing from a review line `- C1: <what> — [file:section] — affects
[REQ-A-001, REQ-A-004]` (finding ids `C1`/`M1` are not stable across rounds,
so the key is `(file:section, affects)`):

| Part | Rule |
|---|---|
| `file` | the text before the first `:` inside `[…]`, normalised to a repo-relative path (leading `./` stripped); an unresolvable path keeps the raw text |
| `section` | the text after that `:`, with a leading `§` or `#`s stripped, then a leading ordinal `\d+[.)]?\s*` stripped (`§3. Foo` ≡ `§Foo`), whitespace collapsed, kept case-sensitive → stored as `§Name`; missing → `?` |
| `affects` | every `REQ-[A-Z]+(-[A-Z0-9]+)?-\d{3}` id in the `affects` clause; `affects —` or none → `∅` |

A line whose `[file:section]` cannot be parsed at all is retained with
`section = ?`, `affects = ∅` and participates only in file-level comparison.
`fix[N].written` comes from section resolution of the fix dispatch's hunks
(`write-scope.md` §3, "Section resolution"); when that is unavailable for a
path it falls back to `(file, *)` — every section of the file — from the
path-level delta (REQ-HARN-021). A fix dispatch fanned into several
chunk-grouped dispatches contributes the **union** of their written pairs.

**`W_N` — regenerated is not new ground (REQ-ARB-HARNESSP3-001).** The retained
per-round write set is the **union** of the fix dispatch's written pairs and the
regeneration writes since round N:

```
W_N := sections(fix[N].written) UNION sections(regen[N].written)
       # falling back to (file, *) only where section resolution is unavailable,
       # which is the existing rule and already labels the pause "(file-level)"
```

This is a **regenerated-not-patched** rule at the §2a level, not a red-round
special case: it applies to **any** stage whose pipeline leaf rewrites its
deliverable wholesale between review rounds — specs, plan, verification alike.
Granularity is not lost: section resolution (`write-scope.md` §3) is a function
of a diff and applies to a regeneration diff exactly as it applies to a fix's;
the existing `(file, *)` fallback and its `(file-level)` pause label are
unchanged.

[Amended 2026-09-19, harness-p5 — REQ-ARB-HARNESSP5-001, ratified as Q-REQ-P5-A]
`W_N` is **diff-based**: a regeneration that re-emits a section
**byte-identically adds nothing to `W_N`**, and a round-N+1 Critical/Material
line keyed on such a section is on ground round N saw **unchanged** — the
class (b) signal, not the false positive this section removed. The provenance
reading `regen[N] = (file, *)` for a wholesale dispatch whose diff exists is
**not** adopted: `(file, *)` remains reserved for a *missing* diff (an untracked
or non-Markdown path, §Section Resolution / self-test F8).
`docs/spec/arbitrated-handoff.md` §`W_N` Includes Regeneration Writes carries
this same sentence; scenario A1 of its §Offline Arbitration Fixture is the
evidence.

**Contradiction classes (REQ-ARB-HARNESSP2-002, -003, -004).** Let `K_N` =
set of `(file, section)` keys of round N's C/M lines, `W_N` as defined just
above, `F(K)` = the files of a key set. With `∈` at section level unless degraded:

| Class | Rule | Detected? |
|---|---|---|
| **(b) new C/M on approved ground** | ∃ line ∈ round N+1 (tier C or M) with key `k` such that `k ∉ K_N` **and** `k ∉ W_N` | **yes** — set membership |
| **(c) verdict regression without new ground** | `round[N].verdict == APPROVE_WITH_FIXES` ∧ `round[N+1].verdict == REJECT` ∧ (i) `W_N ⊆ K_N` ∧ (ii) `K_{N+1} ⊆ K_N ∪ W_N` | **yes** — weaker signal, labelled `class c` |
| **(a) reversal** | a round-N+1 line with `k ∈ K_N` asking the opposite change | **no** — "opposite" is semantic; rendered `(persisting)` in the compiled log exactly as today and surfaced by REQ-HARN-001's exhausted-log gate |

Trigger = (b) ∨ (c); when both hold, (b) is reported (it is the stronger
signal). **Degradation**: when a key or a written pair has `section = ?` or
`*`, the comparison for that key is at **file level** (`file ∉ F(K_N)` ∧ `file
∉ F(W_N)`), the pause labels itself `(file-level)`, and the operator is told it
may over-fire when the fix touched the same file elsewhere. Section resolution
is the remedy, not a spike. Reversals are **not detected** by design: a rule
that guessed "opposite" from text would be a semantic judgement inside the
orchestrator, which REQ-HARN-019 and REQ-ORCH-012 keep out; the cap remains
the backstop for reversals. Red findings (`adversarial-verify.md`) are not
review lines and never enter `K_N` — arbitration compares review rounds only.

**Replay fixture (REQ-ARB-HARNESSP3-001).** The observed verify-stage sequence —
round 1 `APPROVE`, then a pipeline re-dispatch of `sdd-verify` that regenerated
the deliverable, then round 2 `APPROVE_WITH_FIXES` with three Material findings
(`RS-HARNESSP3-001` evidence appendix §B8) — resolves as follows under the
amended `W_N`:

```
round 1 (APPROVE):             K_1 = ∅
regen[1] (verify re-dispatch): docs/ws/<id>/verification.md §Criteria, §Issues Found, …   by: leaf
                               docs/ws/<id>/traceability.md  §(matrix)                        by: leaf
                               docs/requirements/traceability.md §(matrix)                    by: orchestrator
                                 # the shared aggregate, regenerated post-gate from the leaf-written
                                 # per-ws file — a derived artifact (Q-IMPL-HARNESSP3-017)
round 2 (APPROVE_WITH_FIXES):  M1 — docs/ws/<id>/verification.md:§Criteria        -> in W_1, no pause
                               M2 — docs/ws/<id>/verification.md:§Issues Found    -> in W_1, no pause
                               M3 — docs/requirements/traceability.md:§(matrix)   -> in W_1 (by: orchestrator), no pause
               synthetic M4 — docs/spec/telemetry.md:§Record Shape                -> k ∉ K_1, k ∉ W_1
                                                                                  -> REVIEW: CONTRADICTION (class b)
```

All three observed findings named sections of files the loop itself had just
regenerated — `M3` on the **orchestrator**-regenerated aggregate, not the
leaf-written per-ws file, and admitted through `regen[1]`'s `by: orchestrator`
entry — so the class (b) false positive is gone; the synthetic finding on a
file no loop dispatch touched still pauses, so the true positive is retained.
Pre-amendment, `W_1 = fix[1].written = ∅` (there was no fix between the rounds)
and all four fired.

**`REVIEW: CONTRADICTION` pause (REQ-ARB-HARNESSP2-006).** On (b) or (c) at a
**stage gate** (never the per-chunk gate, which shows no review verdict —
REQ-ORCH-018 precedent), the orchestrator pauses. Fixture, pasted from the
spec §`REVIEW: CONTRADICTION` Pause:

```
REVIEW: CONTRADICTION (round 1 vs round 2, class b) — stage: specs, iteration 2 of 3
  round 1 (APPROVE_WITH_FIXES): C1 <verbatim line> — docs/spec/x.md §A — affects REQ-X-001
  fix #1 wrote: docs/spec/x.md §A (hunks L40-58)
  round 2 (REJECT):             C1 <verbatim line> — docs/spec/x.md §C — affects REQ-X-004   <- section untouched by fix #1, not raised in round 1
  Options: accept round 2 (fix) | accept round 1 (proceed, note) | third opinion (re-dispatch review) | stop
```

Shape rules: the token line is `REVIEW: CONTRADICTION (round N vs round N+1,
class b|c[, file-level]) — stage: <stage>, iteration N of MAX`; both rounds'
verdicts and C/M lines verbatim with their keys, side by side; `fix #N wrote:`
between them; each new-ground line annotated `<- section untouched by fix #N,
not raised in round N`; verbatim lines and paths only, never reviewer reasoning
(REQ-ORCH-012); ephemeral (REQ-ORCH-013). When a fix renamed a heading the old
`§Name` is not in `W_N`, so (b) may over-fire — the pause shows both names and
the operator resolves (accepted; renames are rare inside a fix).

| Option | Effect | Iteration counter |
|---|---|---|
| `accept round N+1 (fix)` | normal fix re-dispatch with round N+1's packet | **+1** |
| `accept round N (proceed, note)` | proceed; the note lands where a gate decision already lands — the artifact's own Open Questions, or a Q-IMPL entry when the artifact is a spec — never a review store | unchanged |
| `third opinion (re-dispatch review)` | §Third Opinion | unchanged |
| `stop` | halt | unchanged |

The pause is not a dispatch and not an iteration; it can occur only at
iteration ≥ 2 and therefore always inside the `FIX_LOOP_MAX` window
(REQ-HARN-001 stays the terminal backstop). It is the **fourth** member of the
pause family in §6. Telemetry records the class as
`verdict.contradiction_class` (`∈ {null, b, c}`) on the round-N+1 review
record and the operator's option as `gate.decision` (`telemetry.md`).

**Third opinion (REQ-ARB-HARNESSP2-007).** `third opinion` dispatches a fresh
review of the same stage artifacts (reviews are idempotent and isolated,
REQ-ORCH-014) — **not** a fix iteration (the verifier re-dispatch rule).
Resolution against **both** prior rounds:

| Round 3 relation | Outcome |
|---|---|
| `K_3 == K_N`, or (`verdict_3 == verdict_N` ∧ `K_3 ⊆ K_N ∪ W_N`) | resolves in round N's favour → gate re-renders with round N's verdict and normal options |
| `K_3 == K_{N+1}`, or (`verdict_3 == verdict_{N+1}` ∧ `K_3 ⊆ K_{N+1} ∪ W_N`) | resolves in round N+1's favour → gate re-renders with round N+1's verdict and normal options |
| both (degenerate: rounds agree on keys) | round N+1 (the later, and the one whose packet is current) |
| neither | pause re-renders with **three columns** and only `fix | proceed | stop` |

At most **one** third opinion per contradiction; `iteration N of MAX` is
unchanged throughout. The third round's record is a `review` telemetry record
with `dispatch.reason: THIRD_OPINION`.

When the stage's review returns `VERDICT: REJECT` (or `APPROVE_WITH_FIXES` and
the operator would fix again) after iteration `MAX`, do **not** dispatch another
fix. Render the gate with the **compiled findings log** and offer only
`stop | manual intervention | authorize extra iteration`:

```
Fix loop exhausted — stage: specs, 3 of 3 iterations
  iteration 1: C1 <finding text> — <file:section>; M1 <...>
  iteration 2: C1 (persisting) <finding text>; M2 <...>
  iteration 3: C1 (persisting) <finding text>
  Options: stop | manual intervention | authorize extra iteration (cap → 4)
```

Each line is the review's Critical/Material finding line lifted verbatim, one
group per iteration; no reviewer reasoning, no prose summary (REQ-ORCH-012).
The per-chunk redo cap (§1a) renders the same shape with the verifier's
findings in place of the review's.

- **Checkpoint on fix-loop exhaustion at an implement chunk (REQ-HARN-008).**
  When `FIX_LOOP_MAX` fires while the stage is implement, the implementer is
  not running; the **orchestrator** composes the circuit-break checkpoint from
  the last `RETURN` (`failures`, `ledger`, `open_questions`) per the mapping
  table in `sdd-implement/SKILL.md` §Step 3, trigger label `fix-cap`, and
  applies it as the blocked-task note under the affected task (sequential:
  working tree; fan-out: after merge per `fan-out.md` §3e.4) before rendering
  the exhausted gate. Non-implement stages have no task to annotate — the
  compiled findings log above is their only record.

#### Red round (verify stage, opt-in — REQ-REDB-HARNESSP2-007, -009)

A **red round** is one RED TEAM dispatch (`dispatch-templates.md` §RED TEAM)
after a verify-pipeline return, its gate, and — when the operator routes a
`BROKEN` `Rn` to `fix` — the `RED_BREAK` repair packet
(`return-contract.md` §3) and the re-verify that follows. Counting rules:

- **One red round = at most one fix iteration of the verify stage's counter**
  (`iteration N of 3`), however many chunk-grouped `RED_BREAK` fix dispatches
  it fans into (`return-contract.md` §5) — the same rule as one review round.
- **Red rounds and review rounds share the verify stage's single counter**: a
  cycle cannot spend 3 red rounds *and* 3 review rounds; findings from both in
  the same round count as **one** iteration and may be merged into one
  implement fix dispatch per chunk by the mapping.
- **One default re-run, not an iteration.** After the fix dispatch → scope
  check → chunk verifier → per-chunk gate, the verify pipeline is re-dispatched
  (it regenerates `verification.md` from evidence and writes `pending-red`
  again) and red is re-run **once** by default — the verifier re-dispatch
  rule, not a counted iteration. A second red re-run after the same fix needs
  an explicit operator choice and is likewise not an iteration.
- `FIX_LOOP_MAX` (3) is the backstop: its exhaustion renders the compiled
  findings log above (red's `Rn` lines in place of review findings) with no
  fourth automatic dispatch.
- Red is dispatched only after `RETURN.status: COMPLETE` from blue; a blue
  `verification.md` `status: fail` or a non-`COMPLETE` return renders the
  non-token line `Red team: not run (blue status fail)` and proceeds to the
  normal fix/replan routing.

**New-ground vs regression on red round N >= 2 (REQ-REDB-HARNESSP3-002).** A
second `BROKEN` on the same acceptance criterion may be a *failed fix* or a
*different mechanism behind the first break*; the gate must distinguish them.
On a red round **N >= 2**, for each `BROKEN` `Rn` of the new round the
orchestrator re-runs the **previous round's** routed `reproduce:` command — it
holds those `Rn` lines verbatim from the earlier gate — and renders one derived
line per prior break, in `Rn` order (Q-IMPL-HARNESSP3-007):

```
RED: R1 new-ground (prior R6 reproduce now passes)
RED: R1 regression  (prior R6 reproduce still fails)
```

- `new-ground` — the prior round's `reproduce:` command now **passes**: the
  earlier break was really fixed and this is a fresh break behind it.
- `regression` — the prior round's `reproduce:` command **still fails**: the
  fix did not hold.
- The lines render **inside the `RED_VERDICT:` block, after red's own `Rn`
  lines** and **before the exit rule is applied** (the gate fixture below and
  `../SKILL.md` §The gate carry that position). On round 1 no `RED:` line is
  rendered.
- The lines are **derived in the orchestrator from evidence** — one command per
  prior break. Red's return shape is unchanged between rounds.

**Declined alternative**, recorded here with its reasons: no `supersedes:` or
`new-ground:` marker is added to red's return shape. Such a marker would
require handing red the previous round's findings, contradicting the
withholding default (REQ-REDB-HARNESSP2-004) — and re-attacking the same
criterion is exactly what found the second bug, so red must not be steered away
from it. The derived line costs one command per prior break and changes neither
red's return shape nor its isolation.

Sequence per red round:

```
fix dispatch (implement chunk) → scope check → chunk verifier → per-chunk gate
  → re-dispatch verify pipeline (regenerates verification.md from evidence; writes pending-red again)
  → red re-run ONCE by default (not an iteration — the verifier re-dispatch rule)
  → verify stage gate with a fresh RED_VERDICT:
```

Gate fixture — pasted verbatim from `docs/spec/adversarial-verify.md`
§Verify-Stage Gate and Exit Rule (signal order `RETURN.status` → `SCOPE:` →
`RED_VERDICT:` — its `Rn` lines verbatim, then the derived `RED:` lines on
round N >= 2 — → `VERDICT:` → counters; `proceed` withheld until every
`BROKEN` `Rn` is fixed or accepted):

```
Verify stage gate — pipeline #9 (sdd-verify), red #10, review #11
  RETURN.status  : COMPLETE   budget_consumed: {tool_calls: 41, test_runs: 6}  vs  Budget: ~70 tool calls
  SCOPE: CLEAN
  RED_VERDICT: BROKEN
    - R1: <criterion> — attack: … — observed: … — reproduce: `python -m app --window 0` — BROKEN
    - R2: <criterion> — attack: … — observed: held — reproduce: `pytest -q tests/test_recon.py::test_window` — HELD
  RED: R1 new-ground (prior R6 reproduce now passes)          # round N >= 2 only
  VERDICT: APPROVE
  iteration 0 of 3
  Options per BROKEN finding: R1 → fix (RED_BREAK packet) | accept (record) | stop
  proceed: unavailable until every BROKEN Rn is fixed or accepted
```

`accept (record)` appends `- Rn accepted at gate <YYYY-MM-DD>: <observed> —
reproduce: \`<cmd>\`` under `verification.md` §Issues Found → Minor (marker
`4`: `docs/ws/<id>/verification.md`) — bookkeeping in an existing section of
an existing artifact, outside the observed window; no review store is created.
On `proceed` the orchestrator flips `status: pending-red → pass` immediately
before its commit (`../SKILL.md` §The gate).

## 3. Replan re-entry cap derivation (REQ-HARN-002, REQ-HARN-003) — from §The gate

`REPLAN_MAX` is an orchestrator constant, default **3**. The count is never
stored; recompute it on every replan trigger, before routing into `sdd-replan`:

```
kickoff_date = frontmatter `date:` of <kickoff>            # PRIMARY — mandatory on every orchestrate-written kickoff
             | legacy fallback (kickoff predates the date: rule):
               git log -1 --format=%cs -S'research_id: <id>' -- <kickoff>
               # = the most recent commit whose diff of <kickoff> changed the `research_id:` line,
               #   i.e. the commit that started the CURRENT cycle (<id> = the kickoff's research_id)
             | neither determinable → cap treated as REACHED (see below)
count = number of files f in <plan-history>/ such that
          basename(f) matches ^(\d{4}-\d{2}-\d{2})-(m\d+-)?replan-.*\.md$
          and group(1) >= kickoff_date
```

- `<kickoff>` / `<plan-history>` are `docs/handoff/kickoff.md` /
  `docs/plan-history/` under marker `3` and `docs/ws/<id>/kickoff.md` /
  `docs/ws/<id>/plan-history/` under marker `4` — the count is per workstream.
- Only `sdd-replan` writes archives carrying the `-replan-` segment
  (`{date}-replan-{reason}.md`; per milestone `{date}-m{N}-replan-{reason}.md`).
  `sdd-plan` rewrite archives (`{date}-{reason}.md`) and milestone-complete
  archives (`{date}-m{N}-complete.md`) never count; archives dated before the
  kickoff date never count (previous cycle); minor in-place replans leave no
  archive and are deliberately not counted.
- The legacy fallback is deliberately **not** `git log --diff-filter=A
  --follow` (that yields first creation — wrong once the kickoff is overwritten
  per cycle); the `-S` pickaxe finds the commit that started the current cycle.
- **Neither determinable** (no `date:`, kickoff uncommitted, or `research_id:`
  unmatched): the cap is **treated as reached** — the gate shows
  `replan re-entry cap: kickoff date undeterminable — treated as reached` with
  every `-replan-` archive listed, and routes into `sdd-replan` only on an
  explicit operator decision. The cap is never silently unreachable.
- When `count >= REPLAN_MAX`, surface the cap as a gate event (REQ-ORCH-017
  shape) naming the count, the cap and the counted archive filenames; do not
  route into `sdd-replan` without an explicit operator decision.

## 4. Fan-out lifecycle summary — from §Execution Model

The full command sequence is `references/fan-out.md` §3; this is the contract
summary that used to sit in `SKILL.md`. Under marker `3` everything below
applies against `main` UNCHANGED; under marker `4` the provision base,
merge-back target and redo re-branch are the workstream branch and the
boundary-error inference is removed — `references/fan-out.md` §0/§3c,
`references/v4-workstreams.md` §Marker-4 anchor.

### 4a. Lifecycle (provision → dispatch → merge → teardown)

When the operator opts in and the graph has ≥2 independent branches:

1. **Provision** one worktree/branch per group yourself; worktree ownership is
   the orchestrator's (Q-REQ-G) so provisioning and teardown stay symmetric.
2. **Dispatch** one **leaf** implement subagent per group, pinned to its
   worktree/branch, carrying that group's chunks; a leaf runs `sdd-implement`
   and cannot sub-dispatch (REQ-ORCH-022). Non-interactivity and central ID
   assignment apply. Issue all dispatches **in one batch**, then **await all
   returns** before merging. Each leaf commits with an inline
   `git -c user.email=… -c user.name=…` identity — never by writing
   `.git/config`, which the sandbox blocks (RS-006 Q2).
3. **Sequential merge:** one branch at a time, **all** merges **before** the
   implement-stage review; one-at-a-time merging rules out partial-merge
   corruption. Each leaf's per-leaf gate (the §1 block, rendered before merge
   with no orchestrator commit — `references/fan-out.md` §3a.v) precedes its
   merge.
4. **Teardown** each worktree and branch after its clean merge, leaving only
   `main` for the review.

Batched leaves were **observed to run concurrently** (RS-006, medium
confidence) — a speedup (REQ-ORCH-028) correctness does not depend on.

### 4b. Conflict handling (redo by re-derivation)

On a merge conflict: abort the single failing merge (merged work is never
corrupted), then **redo the chunk-group by re-derivation** — a fresh worktree
re-branched from the updated `main`, a fresh leaf re-running `sdd-implement`.
**Never replay the stale returned patch.** A group that **still** conflicts
after re-derivation was not truly independent (a boundary error) → **run the
affected groups sequentially**, which cannot conflict and guarantees
termination. A merge-abort redo counts toward that group's chunks'
`chunk_redo_count` like any other `fix`. Full command sequence:
`references/fan-out.md` §3c (Q-IMPL-1).

## 5. Gate signal order (REQ-ORCH-034) — from §The gate

Signals surface in the order they are produced; everything is ephemeral
(REQ-ORCH-013). `SKILL.md` §The gate keeps the one-line summary; **this section
is the one canonical statement of the full order** and the per-signal detail —
every other surface (the `SKILL.md` summary, `USAGE.md` §7b, the fixtures in §1
and §2a) points here and must not restate the order in a form that can diverge
from it. The full order is `RETURN.status` → `SCOPE:` → (fan-out per-leaf gate
only) `COMMIT:` at 2b → `CHUNK_VERDICT:` → `RED_VERDICT:` (with its derived
`RED:` lines) → review `VERDICT:` → the loop counters → `REVIEW: CONTRADICTION`
→ the `TELEMETRY:` line, then the options, then — **post-decision** — the
`COMMIT:` closing line (item 8):

1. the leaf's `RETURN.status` and `budget_consumed` against the dispatched
   `Budget:` (`references/return-contract.md` §1, §7);
2. the write-scope block ending in the own-line `SCOPE: CLEAN | VIOLATION (N
   paths)` token (`references/write-scope.md` §5) — branch on the token, never
   prose: `VIOLATION` offers, per `OUT` path, `revert path | accept & widen
   scope | stop`, resolved before the chunk's commit (sequential) or the leaf's
   merge (fan-out), with `proceed` unavailable while any `OUT` path is
   unresolved; a `HISTORY_REWRITE` finding counts as a violation and offers only
   `stop` (`SKILL.md` §Isolation Discipline);
2b. **fan-out per-leaf gate only**: the own-line `COMMIT: COMPLETE | INCOMPLETE`
   token computed **pre-decision** from the leaf's observed writes vs its
   committed delta `base..tip`, with the `RETURN.commits not on branch: <sha>`
   clause appended on the same line when a claimed sha is absent from
   `git rev-list <base>..<tip>` — after `SCOPE:`, before `CHUNK_VERDICT:`
   (`references/write-scope.md` §7a comparand table; `references/fan-out.md`
   §3a.v). The data exists before the decision, so it renders before the
   options; on `INCOMPLETE` it pauses with `amend | accept (note) | stop` and
   `amend` commits the uncommitted paths on the **leaf branch**;
3. implement stage only, per chunk: the chunk's `CHUNK_VERDICT:` (parsed from
   the verifier's `RETURN:` block, last line; missing or unrecognized →
   `RETURN: MALFORMED`) with `Redo: N of 3` against `REDO_MAX` — signals 1–3
   (and 2b) render at the **per-chunk / per-leaf gate** (§1);
3b. verify stage only, and only when the operator opted in to a red round: the
   own-line `RED_VERDICT: BROKEN | HELD` token with red's own `Rn` lines
   rendered verbatim beneath it, then — on a red round **N >= 2** only — one
   derived `RED: Rn new-ground | regression` line per `BROKEN` `Rn`, in `Rn`
   order, **after** those `Rn` lines and **before** the exit rule is applied
   (§2a "Red round"; `docs/spec/adversarial-verify.md` §Gate position). The
   token renders **after** `SCOPE:` and **before** the review `VERDICT:`, because
   the red leaf is dispatched on the blue return and the review follows it;
4. the parsed review `VERDICT:`;
5. when a loop is active, the loop counters — `iteration N of MAX` for the
   fix-loop cap (§2) and the derived count against the replan re-entry cap
   (§3) — signals 3b–5 (and, for a non-implement stage, 1–2 with them) render
   at the **stage gate**;
6. when the arbitration rule fires at a stage gate (iteration ≥ 2), the
   `REVIEW: CONTRADICTION (round N vs round N+1, class b|c[, file-level])`
   pause block with both rounds' verbatim lines and `fix #N wrote:` (§2a; §6
   below) — it renders **after** the counters, because it is derived from the
   round pair the counters name, and it restates `iteration N of MAX` on its own
   token line, so signal 7 is still immediately after the last counter-bearing
   line;
6b. **implement stage gate only** — the completion parse of
   `docs/ws/<id>/plan.md`: when any numbered chunk task is unticked, the
   own-line `PLAN: INCOMPLETE (N of M ticked)` pause renders **after** signal 6
   and **before** the `TELEMETRY:` line, offering `replan │ stop` **only**
   (`proceed` withheld, so verify is never dispatched while the plan reads
   `implementing`); when every task is `[x]` no line renders. It **supersedes
   signal 6's option set** when both fire — 6's block still renders, its
   options are suppressed, and one `replan` closes both. The tick state exists
   on the leaf's return, so it renders before the options
   (`docs/spec/harness-loop-control.md` §Plan Completion Ownership; §6 below);
6c. **every gate**: the own-line `CONVERGENCE:` token — one line per cluster
   whose **second** member arrived at this gate, naming the cluster's key in
   whichever of the three key shapes formed it (the shared id; the file alone,
   for a sectionless file; or file and section), the contributing layers and the
   layer count, e.g. `CONVERGENCE: docs/spec/telemetry.md §Writer rule (review,
   red) — 2 layers`. It renders **after** signal 6b and **immediately before**
   the `TELEMETRY:` line of signal 7, because it is derived from the
   finding-bearing signals above it and from both derived pauses (6, 6b). It is
   **informational**: no option set, it never pauses the gate and it never
   withholds `proceed`. The ledger it is computed over holds every finding this
   gate surfaced, so its data exists before the decision and it renders before
   the options (§5b; `docs/spec/harness-loop-control.md` §Convergence Signal);
7. the `TELEMETRY:` line — the four-member family `rec <n> │ WRITE FAILED │ OFF
   │ .gitignore updated`, at most once each, rendered **last**, immediately
   after the `iteration`/cap line (or, when the pause of signal 6 or of signal
   6b fired, after that pause's token line — 6b renders between 6 and 7) and
   **before the options**
   (`references/telemetry.md` §3). `TELEMETRY: rec <n>` is the positive member
   (REQ-TELEM-HARNESSP3-001): `<n>` is the count of **successful appends this
   session**, not `dispatch.seq`, so a gate whose append failed shows
   `WRITE FAILED` and no `rec` line. No `TELEMETRY:` line ever pauses the gate
   or changes an option;
— the options (`proceed │ fix │ stop` per chunk; `proceed │ loop-back-to-fix │
   stop` per stage; pause-family options where a pause fired);
8. **post-decision**: the own-line `COMMIT: COMPLETE | INCOMPLETE` token —
   rendered immediately after the orchestrator's **own** commit (sequential
   per-chunk and stage gates, on `proceed`) or after the merge (fan-out merge
   step, per branch), as the **closing line of the same gate**, before the
   next dispatch; `landed` is the two-sha range `git diff --name-only
   --no-renames HEAD_before HEAD_landed` captured before any bookkeeping
   commit, `expected` the observed-writes set (sequential) or the leaf's
   committed delta (merge step) — comparands, token shape and pause options:
   `references/write-scope.md` §7a. On `INCOMPLETE` the gate **pauses** with
   `amend | accept (note) | stop` (`amend` unavailable at the merge step) and
   **no next dispatch — including the implement-stage review after the last
   chunk — is issued while the pause is unresolved**. `COMMIT:` joins the pause
   family beside `RETURN: MALFORMED`, `SCOPE: VIOLATION`, `REVIEW:
   CONTRADICTION` and budget exhaustion (§6). `COMPLETE` needs no
   acknowledgement;
8b. **post-decision, implement stage gate `proceed` only, after item 8**: the
   orchestrator — the **sole** writer of the plan's `status:` under
   orchestration — flips `docs/ws/<id>/plan.md` to `status: complete` in its
   **own** bookkeeping commit, the same post-gate slot as aggregate
   regeneration and the `pending-red → pass` flip (`references/write-scope.md`
   §7). It edits `status:` only; `sdd-plan`'s `research_id:` stamp is
   byte-identical before and after. `HEAD_landed` is captured **before** any
   bookkeeping commit, so the flip falls outside the `COMMIT:` comparand range
   and never renders `landed, not observed`. A chunk leaf ticks its tasks and
   never writes `status:`, `sdd-verify` never writes the plan, and a direct
   (unorchestrated) `sdd-implement` session keeps its own Step 6.4 flip
   (`docs/spec/harness-loop-control.md` §Plan Completion Ownership).

Two rules follow from "produced order": a signal whose data exists before the
decision renders before the options (items 1–7, 2b, 6b and 6c); a signal that is the
*consequence* of the decision renders after them (items 8 and 8b) and is **not**
deferred to the next gate — `TELEMETRY: rec <n>` is the one deferred signal,
and it may be because telemetry is never load-bearing. `COMMIT:` is
load-bearing and therefore closes the gate it belongs to. No `TELEMETRY:` line
and no `CONVERGENCE:` line ever pauses the gate or changes an option, and the
"renders last before the options" clause that governs item 7 covers 6c in the
same enumeration.

### 5a. Presentation of the gate block — from §The gate

Render the gate block **verbatim as text**: it is a fixture and its signal
order is the contract. Then collect the decision through the host's option
picker when the session has one, listing the gate's options as the choices, and
fall back to plain text when it does not. The picker never replaces, summarizes
or reorders the block above it, and never adds an option the gate does not
offer. This binds nothing about the loop: the options, their meaning and the
caps are unchanged.

**Approve-with-fixes shortcut.** For `APPROVE_WITH_FIXES` (`sdd-review`: "fix
the named findings, then proceed without re-review") `loop-back-to-fix` offers
re-dispatch then re-review (the default) or skipping the re-review; a *Reject*
never skips it.

### 5b. Convergence signal — L2, item 6c — from §The gate

[Added 2026-09-20, harness-p6 — REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-001,
REQ-ORCH-HARNESSP6-002; descoped at the 2026-09-20 replan to the floor the
Chunk 8 replay measured. Defining section:
`docs/spec/harness-loop-control.md` §Convergence Signal — L2.]

`CONVERGENCE:` is **orchestrator-derived**. It adds **no field to any leaf's
`RETURN:` shape**, it is **not a fifth verification layer** — the four-layer
verification table stays byte-unchanged wherever it appears — and it creates no
durable artifact.

**The cluster rule.** Two or more findings form a **cluster** when all three
conditions hold:

1. they come from **different** layers or second-executors — blue pipeline,
   chunk verifier, review, red;
2. they belong to the **same cycle**, by the `research_id` stamp cycle identity
   already uses (`docs/spec/cycle-identity.md`);
3. their **arbitration finding keys match under one of the three key rules
   below**, applied in this order.

**Key rule 1 — shared id (primary).** Two findings citing the same `REQ-*` id or
the same deviation-entry id cluster, whatever their files and sections. In the
Chunk 8 replay this was the **only** key that formed a cluster at all, so it is
the primary key of the shipped signal.

**Key rule 2 — sectionless file.** The **file-level** key is itself the cluster
key when the arbitration key parser finds **no section** in the file — a `.jsonl`
data file, a `.py` module, anything without section structure. Two findings from
different layers naming such a file cluster on the file alone. This recovers the
one genuine convergence a section-granular key structurally cannot catch (red
and blue hitting the same malformed records in one JSONL data file, which can
never carry a section key).

**Key rule 3 — equal `(file, section)` (retained, demoted).** Findings whose
keys are equal at section granularity still cluster, reusing the existing
`(file, section)` key of `references/write-scope.md` / `arbitrated-handoff.md`
with its ratified leading-ordinal strip (REQ-ARB-HARNESSP5-003) and its existing
parser. It carries **no recall claim**: the replay measured it at zero clusters
over three cycles. Its precision was never in question.

**The false-positive control, retained unchanged.** **In a file that HAS
sections, a file-level-only match renders nothing.** Two findings in two
different sections of one large prose file are not one root cause. Key rule 2
opens file-level matching only where there is no section to match on.

**The ledger.** Convergence is computed over a **session-scoped, in-memory**
finding ledger of the same class as the loop counters (§2, §3). Per finding it
holds exactly three fields — `key`, `layer`, `gate` — and no finding text. It is
never written to disk, never read by any `sdd-*` skill's phase detection, and is
discarded at session end; losing it on a session boundary costs a line, not a
decision.

**The window.** Evaluated at **every** gate over everything recorded so far, not
only at DONE. Each cluster renders **once**, at the gate where its **second**
member arrives — a third layer joining an already-rendered cluster does **not**
re-render it (`harness-loop-control.md` Q-IMPL-HARNESSP6-001). A cluster that
completes only at DONE routes into `verification.md` §Issues Found, to be fixed
or explicitly closed **in this cycle**, and **never** into §Next Steps.

**Shipped scope, stated so verification is never asked for more.** The signal
clusters findings that already carry a shared id or a shared location. Purely
conceptual convergence — a shared root cause with no common id, file or section
— cannot be derived from what the layers already return; it would need a
root-cause field on a leaf's `RETURN:` or a fifth correlating layer, and both are
standing exclusions. Against the harness-p3 §L2 origin case the shipped form
clusters **none of the three** members, as the Chunk 8 replay measured. That is
the accepted cost of shipping without a new field or a new layer.

## 6. Edge cases routed through the gate — from §The gate

- **Replan trigger**: if a pipeline subagent triggers a replan (stuck detection,
  spike invalidation, or a verification failure), surface it to the operator as a
  gate event — after recomputing the replan re-entry cap (§3). The loop may then
  route back to an earlier stage via `sdd-replan`, consistent with the cyclic
  SDD model. Do not silently absorb or auto-resolve a replan trigger.
- **Reject with no actionable findings**: if a review returns a reject/fail
  verdict carrying no actionable findings, **pause** and let the operator decide
  (re-dispatch, override, or stop). Do not auto-loop the pipeline.
- **`REVIEW: MALFORMED`**: if the review's `VERDICT:` token is missing,
  unrecognized, or disagrees with its prose verdict, **pause** with
  `re-dispatch review | accept prose manually | stop`. Never guess the verdict
  from prose (`references/return-contract.md` §6).
- **`RETURN: MALFORMED (<reason>)`**: if a leaf's `RETURN:` block is absent,
  `status:` is not its first key or not one of the four values, a value spans
  multiple lines, or the block is self-contradictory, **pause** with the raw
  tail of the return and `re-dispatch | accept manually | stop`. Never treat a
  malformed return as `COMPLETE` (`references/return-contract.md` §1).
- **`REVIEW: CONTRADICTION (round N vs round N+1, class b|c[, file-level])`**:
  if, inside a fix loop at a **stage gate** (iteration ≥ 2), round N+1 raises a
  Critical/Material on ground round N did not name and the fix did not write
  (class b), or regresses `APPROVE_WITH_FIXES → REJECT` without new ground
  (class c), **pause** with both rounds' verbatim lines and `fix #N wrote:`
  side by side and offer `accept round N+1 (fix) | accept round N (proceed,
  note) | third opinion (re-dispatch review) | stop`. The pause consumes no
  iteration; only `accept round N+1 (fix)` increments the counter; at most one
  third opinion per contradiction. Fourth member of the pause family, beside
  `REVIEW: MALFORMED`, `RETURN: MALFORMED` and reject-with-no-actionable-
  findings above (§2a; `docs/spec/arbitrated-handoff.md`). The arbitration
  guarantee is **unchanged** by `W_N`'s regeneration union (§2a): the pause still
  catches a reviewer raising new Critical/Material findings on ground the
  previous round approved **and the loop did not touch** — a
  wholesale-regenerated file *was* touched by the loop. Admitting regeneration
  writes removes false positives only; it cannot mask a contradiction about a
  file the loop left alone.
- **`PLAN: INCOMPLETE (N of M ticked)`**: at the **implement stage gate**, when
  the completion parse of `docs/ws/<id>/plan.md` finds any numbered chunk task
  unticked, the `status: complete` flip is **withheld** and the gate **pauses**
  with `replan │ stop` as its whole option set — `proceed` is not offered, so
  verify is never dispatched while the plan reads `implementing` and phase
  detection keeps reading the plan as incomplete until a replan closes the
  unticked tasks. **Fifth** member of the pause family, after `REVIEW:
  MALFORMED`, `RETURN: MALFORMED`, reject-with-no-actionable-findings and
  `REVIEW: CONTRADICTION`, and the only two-option one; it carries no finding
  text, only the two counts. **Precedence — 6b supersedes 6**: when both fire
  at the same gate, signal 6's block still renders (the operator needs its
  finding when choosing `replan`) but its options are suppressed, so no option
  resolving to `proceed` — `accept round N (proceed, note)` included — is
  offered, and one `replan` closes both
  (`docs/spec/harness-loop-control.md` §Plan Completion Ownership).

## 7. Mid-pipeline entry: detect → confirm → validate (REQ-ORCH-031..033) — from §Entry Points

**Detect → confirm → validate (REQ-ORCH-032).** **Auto-detect** the proposed
entry stage with the same phase detection (furthest-complete *approved*
upstream → the next stage); **present and confirm** it with the operator (who
may override to an *earlier* stage, never a later one whose upstream is unmet);
**validate** the chosen stage's upstream is approved/complete — otherwise route
to the earliest incomplete upstream stage and say why. Never guess an entry
stage silently — confirmation is mandatory.

**Entry kickoff (REQ-ORCH-033).** KICKOFF still writes `docs/handoff/kickoff.md`
(the only new artifact), but as an **entry kickoff** recording the *scope of
the change*, the *entry stage*, and *which upstream is assumed approved* — not
research questions. DISCUSS still runs first; from the entry stage on the LOOP
is identical to a research-entry cycle.


## 8. Driver rules (normative) — from §Rules

- **Compose, never reimplement**: stage logic lives in the nine `sdd-*` skills
  — dispatch them; never duplicate or modify them.
- **Two dispatches per stage, always**, and **paths only to the reviewer** —
  "helpful context" is exactly the leak the design prevents.
- **Human gate at every stage**: never auto-advance.
- **Reviews are ephemeral** and **artifacts are the source of truth for
  resume** (no `docs/reviews/`, no loop-position marker, no loop log).
- **Sequential by default**: fan-out only at the implement gate on operator
  opt-in with ≥2 independent chunk branches; mid-pipeline entry only per §Entry
  Points, never by guess.
