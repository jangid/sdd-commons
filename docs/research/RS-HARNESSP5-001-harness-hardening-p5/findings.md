---
id: RS-HARNESSP5-001
workstream: harness-p5
topic: harness-hardening-p5
status: Complete
date: 2026-09-19
last_updated: 2026-09-19
questions:
  - "Q1 — Regen provenance: for a wholesale-regenerated artifact, should regen[N] be provenance-based (file, *) or stay diff-based (changed sections only); what each reading does to the p4 case; which reading arbitrated-handoff.md, loop-control.md §2a and Q-IMPL-HARNESSP3-010 support; the offline fixture shape that discriminates the two readings, where it lives and what runs it; cost in files touched"
  - "Q2 — Stage-level fix records and the null chunk: writer stamps dispatch.chunk or reader excludes stage-level fixes from per-chunk implication; which keeps telemetry.md §Record Schema simplest and --lint's cross-field finding meaningful; migration marker or documented expectation for the v: 1 records of a mid-cycle upgrade; which of the six telemetry findings each choice closes"
  - "Q3 — Who flips plan.md status: complete under per-chunk dispatch: last-chunk leaf, orchestrator in its proceed commit, or sdd-verify on entry; weighed against commit ownership (write-scope.md §7), the COMMIT: comparand and phase detection's completion-signal rule; cost in files touched; classification"
budget: "One spike, <= 30 tool calls, 0 test runs, 0 prototypes; desk research over specs, references and tools. Consumed: 22 tool calls, 0 test runs, 0 prototypes, 0 probes (no scratch repository was needed — every question resolved from spec text, skill references, tool source and the p4 evidence records)."
research_refs: [RS-008, RS-HARNESSP2-001, RS-HARNESSP3-001, RS-HARNESSP4-001]
# Note: `last_updated`, `workstream`, `topic` and `research_refs` are extensions
# beyond the sdd-research findings template (staleness detection, marker-4
# workstream attribution, prior-research linkage) — same convention as RS-008,
# RS-HARNESSP2-001, RS-HARNESSP3-001 and RS-HARNESSP4-001.
---

# Research: Harness Hardening, Part 5 — regen provenance, stage-level fix telemetry, and plan-completion ownership

## Questions

Three design questions left open by the harness-p4 cycle
(`docs/ws/harness-p4/verification.md` §Issues Found → Minor, §Open Questions,
§Next Steps; `docs/ws/harness-p4/plan.md` §Operator Tasks O1/O2 and §Replan
Triggers). Everything else in the p5 scope was decided at DISCUSS on
2026-09-19 (restated unchanged in §Decided at DISCUSS below) and goes straight
to requirements. Nothing settled by RS-008, RS-HARNESSP2-001, RS-HARNESSP3-001
or RS-HARNESSP4-001 is re-opened here.

Phase-detection note (marker `4`, workstream `harness-p5`): `docs/ws/harness-p5/`
holds only `kickoff.md`; no plan, verification or traceability exists for this
workstream yet. The shared corpus is fully Approved from harness-p4 (PR #1
merged to `main`); the downstream artifacts this spike makes stale are the
p5 requirements/specs that do not yet exist. No early-exit: the shared corpus
does not answer any of the three questions (each is an explicit p4 hand-off).

## Findings

### Q1 — Regen provenance: keep `W_N` diff-based; the p4 pause on the regenerated plan was a true positive

**Answer**: Keep the diff-based section resolution as `arbitrated-handoff.md`
§`W_N` and `loop-control.md` §2a already state it. Do **not** adopt the
provenance reading `regen[N] = (file, *)`. Add one clarifying sentence to
§`W_N` (mirrored in §2a) stating that a regeneration which re-emits a section
byte-identically adds nothing to `W_N`, and that a round-N+1 C/M line on such a
section is on ground round N saw **unchanged** — which is exactly the class (b)
signal, not the false positive REQ-ARB-HARNESSP3-001 removed. Verify the rule
with a deterministic offline fixture (shape below) that runs as three new
scenarios of `tools/sdd-scope-check-selftest.py`, never a second live loop.

**What each reading does to the p4 case** (`docs/ws/harness-p4/verification.md`
§1; plan O1). Round 1 `APPROVE_WITH_FIXES` (C1, M1, M2, M3); fix #1 rewrote
`docs/ws/harness-p4/plan.md` in full but byte-identical outside
`§(frontmatter)`, `§Operator Tasks`, `§Completed`; `regen[1]` added no
sections (no aggregate regenerated that round). Round 2 raised new C/M ground
on (i) `skills/sdd-orchestrate/SKILL.md §Telemetry` — a file the loop never
touched — and (ii) the regenerated plan's untouched `§Conventions` and
`§Verification Hand-off`.

| Reading | `W_1` | Round-2 key (i) `SKILL.md §Telemetry` | Round-2 keys (ii) plan `§Conventions`, `§Verification Hand-off` | Gate |
|---|---|---|---|---|
| diff-based (§2a as written) | `{plan:§(frontmatter), plan:§Operator Tasks, plan:§Completed}` | `∉ K_1`, `∉ W_1` → class (b) | `∉ K_1`, `∉ W_1` → class (b) | `REVIEW: CONTRADICTION (class b)`, **three** annotated lines |
| provenance `(file, *)` | `{(plan, *)}` | `∉ K_1`, `∉ W_1` → class (b) | `∈ W_1` → admitted | `REVIEW: CONTRADICTION (class b)`, **one** annotated line |

The **token** rendered under both readings because of key (i) — that is what
made the live exercise non-discriminating for REQ-ARB-HARNESSP4-001's
"no pause although findings landed in the regenerated file" criterion. The
readings differ only in the annotated-line set, and a discriminating fixture
must therefore confine round N+1's findings to the regenerated file.

**Which reading the evidence supports — diff-based, on all three sources:**

1. `arbitrated-handoff.md` §`W_N` Includes Regeneration Writes: "`(file, *)`
   only where section resolution is unavailable, which is the existing rule and
   already labels the pause `(file-level)`"; "Granularity is **not** lost:
   section resolution is a function of a diff, and it applies to a regeneration
   diff exactly as it applies to a fix's." The `(file, *)` fallback is reserved
   for a *missing* diff (untracked file, non-Markdown path — §Section
   Resolution, scope self-test F8), never for a wholesale dispatch whose diff
   exists and is small.
2. `loop-control.md` §2a repeats the same two sentences and its replay fixture
   admits M1–M3 because the verify re-dispatch **changed** `§Criteria`,
   `§Issues Found` and the aggregate matrix (RS-HARNESSP3-001 §B8) — every
   admitted key sat in a section whose bytes changed. Nothing in the fixture
   admits an unchanged section.
3. Q-IMPL-HARNESSP3-010 decides **which dispatches** feed `regen[N]` (a
   same-stage pipeline re-dispatch; never another stage's leaf or an operator
   edit) — it says nothing about granularity. The provenance reading is an
   inference from the §`W_N` rationale sentence "a wholesale-regenerated file
   *was* touched by the loop", not a rule anywhere in Approved text.

Why diff-based is also the right semantics, not just the written one: the
pause exists to catch a reviewer raising new C/M ground that "the previous
round approved and the loop did not touch". In the p4 case round 1 saw
`§Conventions` and `§Verification Hand-off` unchanged, raised nothing, and
round 2 raised Critical/Material findings on the same bytes. Under diff-based
that is class (b) by definition — a reviewer contradicting its own prior
approval — and the operator's `accept round 2 (fix)` is precisely the
arbitration the pause is for. Under provenance a `regenerate-wholesale`
`{deliverable_contract}` becomes a blanket immunity for the whole file: any
reviewer self-contradiction on unchanged content inside it would go unpaused,
and the operator could switch arbitration off for a file by choosing the
regenerate contract. The §`W_N` guarantee "admitting it removes false positives
only and cannot mask a contradiction" holds for diff-based and is **broken** by
provenance. REQ-ARB-HARNESSP4-001's acceptance ("no `REVIEW: CONTRADICTION`
line although it raised findings in the regenerated file") was written against
the B8 shape (findings in changed sections) and should be re-stated in p5 as
"no pause on findings in **changed** sections of the regenerated file; pause on
findings in unchanged sections" — that is the contract the fixture below
asserts, and it closes both ARB rows without a live run (§Decided).

**Offline fixture shape** (deterministic; discriminates the two readings on
the p4 case).

Inputs, frozen under `tools/fixtures/arbitration-harness-p4-regen-2026-09-19/`
(five small text files; `tools/fixtures/README.md` gains a section that states
they are a **reconstruction** of the p4 implement-stage gate from
`verification.md` §1 and plan O1 — not a byte capture — so the README's
"captured from live runs" rule is stated per fixture rather than silently
broken):

- `before.md` — a plan-shaped Markdown file with headings `## Conventions`,
  `## Operator Tasks`, `## Verification Hand-off`, `## Completed` under a YAML
  frontmatter block (the after-image start-line rule of §Section Resolution
  puts the frontmatter under `§(preamble)`; the fixture labels it so).
- `after.md` — the "regenerated" file: byte-identical to `before.md` outside
  `§(preamble)`, `§Operator Tasks` and `§Completed`, each of which carries one
  changed line.
- `round-1.txt` — `VERDICT: APPROVE_WITH_FIXES` and four keyed lines
  (`C1`/`M1`–`M3`) whose `[file:section]` keys name `§Operator Tasks` and
  `§Completed` of the plan (so `K_1` is those two keys).
- `round-2.txt` — `VERDICT: APPROVE_WITH_FIXES` and two Material lines keyed
  `[docs/ws/harness-p4/plan.md:§Conventions]` and
  `[docs/ws/harness-p4/plan.md:§Verification Hand-off]` — **confined to the
  regenerated file**, no line on any untouched file.
- `dispatch.txt` — the fix dispatch's observed-writes set
  `{docs/ws/harness-p4/plan.md}` with `regenerate: true` (the p4 dispatch's
  contract) and `by: leaf`.

Runner: three scenarios `A1`–`A3` in `tools/sdd-scope-check-selftest.py`
(the only place the arbitration rule has code today — `resolve_sections()`
is the F8 function, the temp-repo harness exists, and `arbitrated-handoff.md`
§Automated's `test_class_b_*` names are prose-only, confirmed by grep: no
`K_N`/`W_N`/class-(b) code exists anywhere under `tools/`). Each scenario
commits `before.md`, commits `after.md` as "fix #1 (regenerate)", computes
`fix[1].written ∪ regen[1].written` with `resolve_sections()` (diff-based) and
separately `{(file, *)}` (provenance), parses the two rounds with the §2a key
rule (including the leading-ordinal strip), and applies the class (b)/(c)
table through a new pure `arbitrate(round_n, round_n1, w_n) -> (class | None,
annotated_keys)` helper:

| Scenario | Round-2 keys | Expected, diff-based | Expected, provenance | Purpose |
|---|---|---|---|---|
| A1 — p4 case | unchanged sections of the regenerated file | `class b`, 2 annotated keys | no token | **discriminates** the readings; asserts the diff-based outcome |
| A2 — B8 case | changed sections only (`§Operator Tasks`, `§Completed`) | no token | no token | the REQ-ARB-HARNESSP3-001 false positive stays removed |
| A3 — control | one key on an untouched second file | `class b`, 1 annotated key | `class b`, 1 annotated key | the true positive is kept under either reading (this is what p4 actually hit) |

A1's diff-based column is the assertion; the provenance column is computed
and printed alongside so the fixture demonstrably yields different outcomes
on the same inputs (the kickoff's Q1 success criterion). `--self-test`
exit 0 with `25/25` becomes the verify evidence for both ARB rows.

**Cost in files touched** (8): `tools/sdd-scope-check-selftest.py` (key
parser, `arbitrate()`, A1–A3), five fixture files + `tools/fixtures/README.md`
section, `docs/spec/arbitrated-handoff.md` (one §`W_N` sentence; §Automated
names A1–A3 and stops being prose-only, closing that verifier advisory; a new
Q-IMPL entry recording the reading; REQ-ARB-HARNESSP4-001's live-exercise
section re-pointed at the fixture), `skills/sdd-orchestrate/references/loop-control.md`
§2a (the mirror sentence). `docs/ws/harness-p5/traceability.md` carries both
ARB rows. No dispatch template changes; no `sdd-review` change.

**Classification**: design-decision-for-requirements (the reading — one
requirement stating "byte-identical re-emission is not a regeneration write";
requirements inherit it) + code (fixture runner, `tools/*.py`) + mechanical
(the two spec/reference sentences).

**Confidence**: High on the reading (three independent text sources agree and
the guarantee argument is closed-form); High on the fixture shape (A1 is a
direct transcription of the p4 gate with key (i) removed); Medium on the
runner location only in that a separate `tools/sdd-arbitrate-selftest.py`
would work equally well — the selftest is preferred because `resolve_sections`
and the temp-repo harness live there and it is already a verify gate.

### Q2 — Stage-level `fix` records: the writer leaves `chunk_verdict` null on them and the reader implies `pipeline` only for chunk groups; `v: 1` records are exempt from the equal-heads rule, no migration marker

**Answer**: Neither "writer stamps the chunk" nor "reader excludes" alone;
the evidence selects a **writer rule plus a one-line reader change**, and for
the `v: 1` records a **documented exemption** rather than a migration marker.

**Root cause of findings 1 and 2** (seq 21, 24, 27 of p4 session 2). These
are the implement-stage `loop-back-to-fix` dispatches after the stage review
(`iteration ≥ 1`, `redo: null`, `chunk: null` — correct per §Record Schema,
which defines `chunk` as "the `### Chunk N:` number for per-chunk dispatches").
Their chunk verifiers ran under chunks 1/3/0 and got `verifier` records with
`chunk: N`; §Writer rule (i) then copied each `CHUNK_VERDICT:` onto "the
chunk's own record" — but a stage-level fix has no chunk record, so the writer
put it on the `fix` record with `chunk: null`. The reader (`tools/sdd-telemetry.py`
`expected_rows()`) groups `pipeline`/`fix` records per `(stage, chunk)`; the
`(implement, null)` group holds three `fix` records, and the implication
"the first attempt is always a pipeline dispatch" adds `implied.pipeline += 1`
for it — one false `missing pipeline`. `--lint`'s cross-field rule
("`chunk_verdict` non-null on a non-verifier record with no verifier record for
chunk `None`") fires on the same three records — finding 2 is the lint's view
of the same writer gap.

**Why not stamp the chunk on the writer side**: a stage-level fix is not a
per-chunk dispatch (it may touch several chunks — the p4 fix #1 regenerated
`plan.md`, no chunk at all — and its verifiers may run under several chunks,
as seq 21/24/27 did under 1/3/0); one `dispatch.chunk` cannot hold that, and a
stamped value would put an `iteration ≥ 1, redo: null` record inside a chunk
group where `attempts()` and the redo semantics of §Writer rule (iii) do not
apply. The schema stays simplest when `chunk` keeps its one meaning.

**Recommended writer rule** (`telemetry.md` §Writer rule (i), mirrored in
`references/telemetry.md` §3): the verifier's `CHUNK_VERDICT:` is copied onto
the dispatched record **only when that record is a per-chunk dispatch**
(`chunk != null`); a stage-level `fix` record keeps `verdict.chunk_verdict:
null`, and its verifiers' verdicts live on their own `verifier` records.
**Recommended reader change** (`tools/sdd-telemetry.py`): `implied.pipeline`
sums over implement groups **with `chunk != null`** only; `attempts()` /
`implied.verifier` are unchanged (a null group with null `chunk_verdict`
implies nothing). With both, the cross-field rule is unchanged and becomes
true by construction — it keeps flagging a `chunk_verdict` on a record whose
`(stage, chunk)` has no verifier, which is now always a writer defect.

**`v: 1` records of a mid-cycle upgrade** (seq 2, 4, 6). The narrowed rule
(Q-IMPL-HARNESSP4-007) fires on a `proceed` implement record with equal
snapshot heads, `files_written_n > 0` and no landed commit group — which a
`v: 1` record can never carry. On the frozen p3 fixture the `v: 1` chunk
records have null heads (README failure mode), so the rule's `v: 1` branch
never fires there; its only observed firing is these three compliant p4
records. The branch therefore has no true positive on record and one live
false positive. A migration marker is the wrong instrument: `migration.from`
is the enum `chunk-string` for a rewrite `migrate` performed, the marker is
"present only on records rewritten by `migrate`", and the p4 records carry no
defect to rewrite — stamping them would edit a live record to satisfy a lint
(the fixture README forbids exactly this for fixtures). **Decision**: the
equal-heads cross-field rule evaluates `v: 2` records only; a `v: 1` record
is exempt because it has no field that can prove landing (documented in
§Schema Lint's cross-field row and in a Q-IMPL entry amending
Q-IMPL-HARNESSP4-007's v1 branch). Self-test: `v: 1` + equal heads +
`files_written_n > 0` → no finding; the same as `v: 2` with null token → finding.

**The six findings, each mapped to the change that closes it:**

| # | Finding (p4 live run) | Closing change | Kind | Evidence fixture |
|---|---|---|---|---|
| 1 | `summarize` false "1 missing pipeline" on `(implement, chunk null)` | reader: `implied.pipeline` over `chunk != null` implement groups only | code | new frozen p4 fixture (seq 21/24/27) |
| 2 | stage-level `fix` records carry `chunk_verdict` with `chunk: null`; writer rule needed | writer rule (i) amended: copy `CHUNK_VERDICT:` onto per-chunk records only; `--lint` cross-field row unchanged | mechanical (spec + `references/telemetry.md` §3) | same fixture: the three records stay a `[cross-field]` finding as historical fact, listed by seq in §Acceptance like the p3 `seq 20` |
| 3 | `v: 1` records of a mid-cycle upgrade trip the equal-heads rule | rule restricted to `v: 2`; no migration marker; Q-IMPL amendment | code + mechanical | same fixture (seq 2/4/6 → no finding after) |
| 4 | `summarize` admits `v: 2.0` while `--lint` rejects it | `load()` tests `_is_int(v) and v in ADMITTED_V` (today `2.0 in {1, 2}` is `True`); one shared `admitted_v()` helper for both entry points | code | synthetic self-test record `v: 2.0` → skipped + counted by `summarize`, `[type] v` by `--lint` |
| 5 | `COMMIT: INCOMPLETE: 0` although one `INCOMPLETE` was forced live | documented expectation: §Writer's `commit` source records the **closing** line — an `amend` re-renders `COMPLETE` before the append, so an amended omission is recorded as `COMPLETE`; `summarize` label becomes `COMMIT: INCOMPLETE (accepted): N` | mechanical + code (label) | p4 fixture (the O3 record carries `COMPLETE`) |
| 6 | `--lint` findings not emitted in `seq` order (three passes: per-record type/enum/key, per-session mistyped-fix + cross-field, then reason-review) | stable sort in `lint()` by `(int seq ascending, then non-int seqs in insertion order)` | code | synthetic: type finding on seq 5 + cross-field on seq 2 → rendered 2, 5 |

Finding 5's alternative — a `commit.amended` field — is a `v: 2` key-set change
(every existing `v: 2` record would read `key-missing` unless the key is
OPTIONAL) with no evidence anyone needs the count: telemetry records gate
outcomes, not intermediate renderings, exactly as `gate.decision` records the
final decision. Deferred, not adopted.

**Fixture**: `tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl`, a copy of
the live file as it stood at p4 DONE (61 lines: p3 migrated seq 1–20, p4
session 1 seq 1–13, p4 session 2 seq 1–28, per plan O2). It must be cut by
the **operator** (leaves never read `.sdd/`) as a plan operator task, with its
sha256 recorded in `tools/fixtures/README.md` and the `migrate` fixture guard
covering it automatically (path under `tools/fixtures/`). Findings 1, 2, 3
and 5 are reproducible only on it; 4 and 6 are synthetic self-test cases.
The p3 fixture is untouched (§Out of scope).

**Cost in files touched** (5): `tools/sdd-telemetry.py` (four small changes +
self-test cases), the new p4 fixture + `tools/fixtures/README.md`,
`docs/spec/telemetry.md` (§Writer rule (i), §Schema Lint cross-field row,
`summarize` label in §Records-vs-Expected / §Fixture-Based Test Contract, one
Q-IMPL amendment), `skills/sdd-orchestrate/references/telemetry.md` §3 mirror.

**Classification**: findings 1, 4, 6 code; 2 mechanical; 3 and 5 code +
mechanical. No design decision is left for requirements beyond ratifying the
writer rule ("a stage-level fix carries no `chunk_verdict`") and the `v: 1`
exemption.

**Confidence**: High — each finding was located to the exact code path or
spec sentence (`expected_rows()` group loop; `load()` membership test;
`lint_records()` three-pass order; `summarize()` token count; §Writer rule (i)
wording), and the closing change is one condition or one sentence in every
case.

### Q3 — The orchestrator flips `plan.md` to `status: complete` at the implement **stage gate** `proceed`, in its own bookkeeping commit; `sdd-implement` Step 6.4 keeps the flip for a direct session

**Answer**: Ownership follows whoever owns the **whole-plan** run.
`sdd-implement` Step 6 ("1. run the full suite, 2. walk every acceptance
criterion, 3. list Q-IMPL entries, **4. set `status:` to `complete`**, 5.
recommend `sdd-verify`") is the skill's end-of-run ritual; in a direct session
the skill owns the run and Step 6.4 stays as is. Under per-chunk dispatch no
leaf owns the run — each sees one chunk — and steps 1–3 are already performed
by the harness (chunk verifiers + the single implement-stage review after all
chunks, `loop-control.md` §1). The flip therefore belongs to the
**orchestrator**, at the implement stage gate's `proceed` (after the review
verdict, not at the last per-chunk gate), executed in a **bookkeeping commit
of its own**, after its completion parse shows every numbered chunk task `[x]`
(that parse already exists: plan O2 note, "the orchestrator's completion parse
counts numbered chunk tasks only").

**Why not the last-chunk leaf**: the orchestrator does know which chunk is
last, so it *could* say so in the dispatch prompt and `plan.md` is already in
the chunk leaf's write scope (task ticks) — but the flip would be premature by
construction: the stage review runs after the last chunk and a
`loop-back-to-fix` may add or re-open tasks, so the leaf would be asserting a
completion the harness has not yet decided. It would also make "last" a
dispatch-prompt fact a redo or fix re-dispatch must carry consistently
(`dispatch-templates.md` change). Evidence: p4 implement round 1 review C1
(kickoff) — the review, not the leaf, is where completion was contested.

**Why not `sdd-verify` on entry**: `sdd-verify`'s phase detection reads the
plan as an input ("if `plan.md` has incomplete tasks → use `sdd-implement`";
Step 1 "confirm all tasks marked done") and its default write scope is its own
`verification.md` / per-ws `traceability.md`; writing the plan would widen the
verify leaf's scope onto an upstream artifact, break "one writer per state"
(`ws-traceability.md` §Legal `Verified` Cell Values precedent), and make the
completion signal appear only after verify starts — so a session resumed
between implement DONE and verify dispatch would detect "implementing" on a
fully ticked plan.

**Against the three constraints named in the kickoff:**

- *Commit ownership* (`write-scope.md` §7): the review's gate "commits
  nothing", so the flip cannot ride a leaf commit at the stage gate; the table
  already has the row for this shape — "aggregate regeneration (marker `4`,
  post-gate bookkeeping): orchestrator, in its **own** commit, separate from
  any leaf's". The flip is a second entry of that row (same slot, same
  bookkeeping commit as the aggregate regeneration when both fire).
- *`COMMIT:` comparand* (`harness-commit-fidelity.md` §Comparand Table):
  `HEAD_landed` is captured "**before** the aggregate-regeneration commit or
  any other bookkeeping commit", so a flip in the bookkeeping commit is
  outside the range by definition and never renders `landed, not observed:
  docs/ws/<id>/plan.md`. Folding it into a leaf's `proceed` commit would be
  tolerated only by accident (plan.md is usually observed via task ticks) and
  is ruled out by §7's separation rule.
- *Phase detection's completion-signal rule* (`cycle-identity.md`,
  `CLAUDE.md` §Phase Detection): "Implementation done" = `status: complete`
  + all tasks `[x]` + `research_id` equal to the kickoff's. The stamp is
  written by `sdd-plan` and the flip must not touch it (frontmatter edit of
  `status:` only). Flipping at the stage `proceed` makes the artifact agree
  with the driver's own transition (the next dispatch is verify), so a session
  resumed at any point reads the same phase the orchestrator was in.

**Cost in files touched** (6): `skills/sdd-implement/SKILL.md` Step 6 (one
sentence: under orchestrated per-chunk dispatch the leaf never flips; the
orchestrator does at the stage gate), `skills/sdd-orchestrate/SKILL.md` §The
gate (implement stage `proceed` adds the flip to the bookkeeping step),
`references/loop-control.md` §1 (per-chunk loop: "after the review's
`proceed`: flip + bookkeeping commit"), `references/write-scope.md` §7 table
(second bookkeeping entry), `references/dispatch-templates.md` §PIPELINE
per-chunk (leaf instruction: tick tasks, never `status:`),
`docs/spec/harness-loop-control.md` (or `ws-orchestration.md` — whichever
requirements assign as the gate's contract owner) for the rule; plus a
`tools/sdd-skill-lint.py` REQUIRED row if requirements want the flip sentence
drift-checked (optional, +1 file). No `tools/*.py` logic beyond the optional
lint row; no fixture.

**Classification**: design-decision-for-requirements (ownership rule) +
mechanical (skill/reference/spec text). Zero code required.

**Confidence**: High — every alternative is excluded by an Approved rule
already in force (§7 separation, `HEAD_landed` capture point, verify's
read-only relation to the plan), and the chosen owner already performs the
adjacent bookkeeping (aggregate regeneration, `pending-red → pass` flip) in
the same slot.

## Implications for Design

- **Arbitration closure is a spec decision plus a fixture, no live run** —
  diff-based `W_N` is confirmed; one requirement ratifies "byte-identical
  re-emission is not a regeneration write", and REQ-ARB-HARNESSP4-001's
  acceptance is re-stated against the fixture (A1/A2/A3), letting both ARB
  rows trace and close in `docs/ws/harness-p5/traceability.md`.
- **Telemetry schema is unchanged** (`v` stays `{1, 2}`; no new key; the
  `migration` marker keeps its single `chunk-string` meaning). All six
  findings close with writer-rule text plus four one-condition reader changes.
- **The new p4 fixture is an operator task** (cut from `.sdd/telemetry.jsonl`,
  never by a leaf), scheduled before the telemetry chunk like p4's O2 ran
  before verify.
- **Plan completion becomes a driver responsibility under dispatch**, in the
  existing bookkeeping slot; `sdd-implement` keeps Step 6.4 for direct use.
  This adds no artifact, no counter and no telemetry field (the
  no-new-artifact invariant holds).
- Requirements sees one bounded scope: the three answers above plus the
  §Decided list, nothing else.

## Decided at DISCUSS (not research — requirements inherit these)

Restated unchanged from `docs/ws/harness-p5/kickoff.md`:

- ARB closure is by spec decision plus offline fixture; no live re-run.
- `descoped` is added as a legal `Verified` value; its use is limited to rows
  carried from a previous workstream that the DONE rule could not close.
- Size housekeeping target is lint warn-clean: all three skills under 400
  lines, `telemetry.md` split; REQ-LINT-003 baseline becomes "none".
- L2 (cross-layer convergence as a gate signal) stays deferred; the p4
  evidence (defect class caught 4× by review, 1× by lint) is recorded for a
  later cycle, not acted on here.
- DONE rule: every requirement traced by this workstream `pass`; nothing
  closes as a deliberate `fail`; an item that cannot be exercised is descoped
  at replan.
- Scope priority for the plan is the order in §Scope, so a `stop` partway
  leaves the arbitration closure and telemetry fixes landed first.

Size evidence for the housekeeping item (measured this spike, for the
requirements writer): `sdd-orchestrate/SKILL.md` 551, `sdd-migrate/SKILL.md`
464, `sdd-implement/SKILL.md` 434 against `SIZE_WARN_LINES = 400`;
`docs/spec/telemetry.md` 1137. `skill-lint-v5.md` REQ-LINT-003 acceptance
still reads "baseline warns on exactly `sdd-orchestrate` and `sdd-migrate`"
and REQ-LINT-007 "`SKILL.md` ≤ ~450 lines" (lines 276, 280).

## Prototype

None. No scratch repository was opened; the budget allowed one probe and none
was needed — Q1's fixture is specified from the p4 gate record and the F8
scenario's existing harness, Q2's six findings were located in tool source
and spec text, Q3 is closed by Approved rules.

## Open Questions

- Q1 runner placement: scenarios in `tools/sdd-scope-check-selftest.py`
  (recommended) versus a new `tools/sdd-arbitrate-selftest.py` — a plan-level
  choice; the fixture shape and assertions are identical either way.
- Q3 contract owner: which spec (`harness-loop-control.md` or
  `ws-orchestration.md`) carries the flip rule — for `sdd-specs` to place;
  the rule itself is settled.
- Finding 5's deferred `commit.amended` counter: revisit only if a later cycle
  needs amend counts from telemetry; no evidence today.
