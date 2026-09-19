---
status: Approved
last_updated: 2026-09-20
requires:
  - REQ-TELEM-HARNESSP2-007
  - REQ-TELEM-HARNESSP2-009
  - REQ-SKILL-HARNESSP2-001
  - REQ-SKILL-HARNESSP2-008
  - REQ-LINT-HARNESSP2-002
  - REQ-TELEM-HARNESSP3-002
  - REQ-TELEM-HARNESSP4-002
  - REQ-TELEM-HARNESSP4-003
  - REQ-TELEM-HARNESSP4-004
  - REQ-TELEM-HARNESSP4-005
  - REQ-TELEM-HARNESSP4-008
  - REQ-TELEM-HARNESSP5-002
  - REQ-TELEM-HARNESSP5-003
  - REQ-TELEM-HARNESSP5-004
  - REQ-TELEM-HARNESSP5-005
  - REQ-TELEM-HARNESSP5-006
  - REQ-TELEM-HARNESSP5-007
  - REQ-TELEM-HARNESSP5-008
  - REQ-LINT-HARNESSP5-003
---

# Per-Dispatch Telemetry — Reader, Lint and Fixture Contract

## Context

[Split from `telemetry.md` 2026-09-19, harness-p5 — REQ-LINT-HARNESSP5-003,
Q-REQ-P5-G.] `telemetry.md` defines the record the orchestrator **writes** —
placement, schema, writer sequence, third observation, non-interference proof. This file defines everything derived from that file **after** a
cycle by the operator's tools, plus the `\.sdd/` lint guard and the skill/lint
change table (moved here 2026-09-19 — lint-side, like §Schema Lint): `tools/sdd-telemetry.py summarize` and its
records-vs-expected implication, `--lint` from the one domain table, the
`migrate` rewriter, the optional `--plan` floor, and the frozen-fixture test
contract every reader-side test runs against. Nothing here runs inside the
loop; the orchestrator performs zero reads of the file (REQ-TELEM-HARNESSP2-004)
and no skill invokes the tool.

Terminology and every token are those of `telemetry.md`; the record schema is
rendered there (`telemetry.md` §Record Schema) and in `references/telemetry.md` §2, and the
domain table in the tool is the single source of truth (§Schema Lint). This
cycle folds the harness-p4 Tier-2 decisions Q-IMPL-HARNESSP4-004..007 into the
sections they amend (REQ-QIMPL-HARNESSP5-001) and adds the six reader/lint
findings of RS-HARNESSP5-001 §Q2 (REQ-TELEM-HARNESSP5-002..008), reproduced on
a frozen copy of the p4 live file that the operator cuts.

## Design

### Out-of-Loop Reader (REQ-TELEM-HARNESSP2-009)

`tools/sdd-telemetry.py` — stdlib-only, `--help`, `--self-test`, one
subcommand:

```
python3 tools/sdd-telemetry.py summarize [--file .sdd/telemetry.jsonl] [--workstream <id>] [--since <ISO>] [--plan <path>]
python3 tools/sdd-telemetry.py --lint    [--file .sdd/telemetry.jsonl]                      # REQ-TELEM-HARNESSP4-004
python3 tools/sdd-telemetry.py migrate   --file <path> [--out <path>]                       # REQ-TELEM-HARNESSP4-005, operator-run
python3 tools/sdd-telemetry.py --self-test
```

[Amended 2026-09-18, harness-p4] `--lint`, `migrate` and `--plan` are added
below (§Schema Lint, §In-Place Migration, §`--plan` Floor); all three are
post-cycle readers/rewriters run by the operator, never by a skill.

Output: one table per workstream, one row per `dispatch.stage`, columns:

| Column | Derivation |
|---|---|
| dispatches | count of records |
| tool calls mean / max / budget | `return.budget_consumed.tool_calls` vs `dispatch.budget.tool_calls` (records with `unparsed` or null are counted in an `n/a` column) |
| SCOPE violations | count `scope.token == VIOLATION` |
| MALFORMED | count `verdict.malformed` |
| fix iterations | max `gate.fix_iteration` per stage |
| redos per chunk | max `gate.redo_count` grouped by `dispatch.chunk` |
| contradiction pauses | count `verdict.contradiction_class != null` |
| red verdicts | counts of `BROKEN` / `HELD` |
| wall time dispatch | mean and max `ts_return − ts_dispatch` |
| wall time gate | mean and max `ts_gate − ts_return` |

followed by a per-chunk block (`implement` + `verifier` + `fix` + redo counts
per `dispatch.chunk`) — RS-008 probe 1 as a query. Records with an unknown `v`
are skipped and counted on a trailing `skipped: N unknown-schema record(s)`
line; a line that is not JSON is counted likewise. Admission of `v` is **one
shared helper** — `_is_int(v) and v in ADMITTED_V` — called from both `load()`
paths, so `summarize` and `--lint` agree: a float `v: 2.0` is skipped and
counted here exactly as `--lint` rejects it with a `[type] v` finding
[Amended 2026-09-19, harness-p5 — REQ-TELEM-HARNESSP5-004; `2.0 in {1, 2}` is
`True` in Python, so the bare membership test admitted it]. `--self-test` builds a
six-record fixture in a temporary directory and asserts one row per stage, the
per-chunk block and the skipped count. No skill invokes the tool inside the
loop; `sdd-orchestrate`'s telemetry stub names it only as a post-cycle step.

### Scorer Derivation (REQ-EVAL-HARNESSP2-002 cross-reference)

`evaluation.md` fixes the scorer field list; every field must be derivable from
the record key set plus `verification.md`'s `status` line. The derivation:

| Scorer field | Record keys |
|---|---|
| first-attempt pass rate | `verification.md status == pass` ∧ max `gate.fix_iteration` over `dispatch.stage == verify` records == 0 |
| mean fix iterations per stage | max `gate.fix_iteration` per (`cycle`, `dispatch.stage`), averaged over runs |
| `SCOPE: VIOLATION` rate | count `scope.token == VIOLATION` / count `scope.token != null` |
| `MALFORMED` rate | count `verdict.malformed` / count records |
| dispatches per chunk | count records grouped by `dispatch.chunk` with `kind ∈ {pipeline, fanout_leaf, verifier, fix}` |
| contradiction pauses per run | count `verdict.contradiction_class != null` per `cycle` |
| red `BROKEN` findings per run | sum `return.failures_n` over `dispatch.kind == red` per `cycle` |
| tool calls per run vs budget | sum `return.budget_consumed.tool_calls` and sum `dispatch.budget.tool_calls` per `cycle` |
| wall time per dispatch / per run | `ts_return − ts_dispatch`; `max(ts_gate) − min(ts_dispatch)` per `cycle` |

A run (`cycle`) is identified by (`cycle.workstream`, `cycle.kickoff_date`,
`cycle.research_id`). No field needs prose, and no field needs an artifact
other than `verification.md`'s `status`; if a future scorer field cannot be
derived this way, the schema — not the scorer — is defective.

### Records-vs-Expected in `summarize` (REQ-TELEM-HARNESSP3-002) [may]

`tools/sdd-telemetry.py summarize` **may** report a records-vs-expected count
per session, so a missing-append gap is visible post-cycle even when the
operator missed the absent gate line. The reporting slot already exists —
`summarize` skips and counts unparsable lines on a trailing `skipped:` line, and
this is a sibling of it.

This is an **optional backstop**, not a substitute for the gate line, and it is
a strictly post-cycle reader: it must not influence control flow, and the
orchestrator still performs zero reads of the file during a cycle
(REQ-TELEM-HARNESSP2-004). If the plan has no room, it is queued under
`verification.md` §Next Steps rather than dropped — the `may` acceptance is
conditioned accordingly.

#### Implication-Derived `expected` and the Headline (REQ-TELEM-HARNESSP4-002, -003)

[Changed 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-002, REQ-TELEM-HARNESSP4-003.
Q-IMPL-HARNESSP3-006's `expected` (highest `dispatch.seq` per session) saw no gap
on the p3 file because a writer that never appends also never increments; every
count below is recomputed from `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
(RS-HARNESSP4-001 §Q2, evidence-appendix §B).]

`expected` is derived from **cross-field implications already present in the
records** — fields the writer filled for its own gate rendering — and only
starts from the highest `seq`. Per session (Q-IMPL-HARNESSP3-018), per kind,
`dispatch.redo` read as 0 when null. The chunk-shaped implications are computed
**per `(stage, chunk)` group** — the `pipeline` and `fix` records sharing one
`dispatch.stage` and `dispatch.chunk` (a null `chunk` is its own group) — never
by summing `(1 + redo)` over records, because `telemetry.md` §Writer rule (iii) keeps the
first attempt's record *and* adds a `fix` record per redo, so a per-record sum
counts the same attempt twice [Amended 2026-09-18, harness-p4 specs review r1 —
C1]:

```
attempts(stage, chunk) := 1 + max(dispatch.redo) over that group's pipeline/fix records           # the redo counter is per chunk, so its max IS the attempt count
implied.verifier       := Σ over groups with ≥ 1 record carrying verdict.chunk_verdict != null (kind != verifier) of attempts(stage, chunk)
implied.pipeline       := Σ over implement groups with chunk != null of ( 1                                             # the first attempt is always a pipeline dispatch
                                                     + #records in the group with kind == pipeline and dispatch.redo ≥ 1 )   # a redo recorded as pipeline (the p3 collapsed shape) stands in for its own first attempt
implied.review         := #records with kind != review and verdict.review_verdict != null           # one per carrying record
implied.red            := #records with kind != red    and verdict.red_verdict    != null
implied.fix            := #records with gate.decision ∈ {loop-back-to-fix, fix, redo}               # clause (a): each such decision dispatches one fix (a per-chunk `fix` normalises to `redo`, `telemetry.md` §Writer rule (ii))
                        + #records with kind != fix and dispatch.reason ∈ FIX_ONLY_REASONS          # clause (b): a reason only a fix dispatch carries
missing.<kind>         := max(0, implied.<kind> − recorded.<kind>)   matched PER STAGE, never cross-stage, never negative
missing.fix            := 0 for an implied fix that is PRESENT as a record of another kind (mis-typed fix — a --lint finding, not a missing append)
expected               := highest dispatch.seq + Σ missing.<kind>
```

**Worked numbers, both record shapes** (the formula must hold on each):

| Shape | Records in one implement group | `attempts` | `implied.verifier` | `implied.pipeline` vs recorded |
|---|---|---|---|---|
| p3 collapsed (fixture `seq` 7, 10, 13) | one `pipeline` record, `redo: 1`, `chunk_verdict: PASS` | 2 | 2 | 1 + 1 = 2 vs 1 → 1 missing |
| p3 single attempt (fixture `seq` 6, 8, 9, 11, 12) | one `pipeline` record, `redo: null`, `chunk_verdict: PASS` | 1 | 1 | 1 vs 1 → 0 missing |
| compliant redo (`telemetry.md` §Writer rule (iii)) | `pipeline` `redo: 0` + `fix` `redo: 1`, both `chunk_verdict` non-null | 2 | **2** | 1 + 0 = **1** vs 1 → 0 missing |

On `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` (recomputed at this
amendment): 8 implement groups, three with `max(redo) = 1`, so
`implied.verifier = 5 × 1 + 3 × 2 = 11` against 0 recorded and
`implied.pipeline = 5 × 1 + 3 × 2 = 11` against 8 recorded (3 missing) —
`expected 39` is unchanged. The compliant redone chunk yields 2 verifiers and
1 pipeline against 2 `verifier` and 1 `pipeline` records, so
REQ-TELEM-HARNESSP4-001's "0 missing" holds on a live redo; the previous
per-record sum read it as 3 verifiers / 2 pipelines. Clause (a)'s `redo` member
counts the per-chunk `fix` decision that dispatches that `fix` record; the
fixture carries no `redo` decision, so its `implied.fix` stays 2.

**Chunk groups only** [Amended 2026-09-19, harness-p5 — REQ-TELEM-HARNESSP5-002,
Q-REQ-P5-B]: `expected_rows()` sums `implied.pipeline` over implement groups
with `chunk != null` **only**. A `(implement, null)` group — the stage-level
`fix` records of a `loop-back-to-fix` after the stage review, which
`telemetry.md` §Writer rule (i) keeps at `chunk_verdict: null` — implies no
pipeline dispatch: its first attempt was the per-chunk pipeline records, not a
null-chunk one. `attempts()` and `implied.verifier` are unchanged (a null group
with null `chunk_verdict` implies nothing). On the p4 live file the old sum read
the null group as "1 missing pipeline" (RS-HARNESSP5-001 §Q2 finding 1).

**Clause (a) counts deciding gates, not records** [folded from
Q-IMPL-HARNESSP4-004, 2026-09-19]: `telemetry.md` §Writer gives a verifier,
review or red record the `gate.decision` of the gate it fed, so on a compliant
file a chunk record and its `verifier` record both carry one per-chunk `redo`
(and a stage record and its `review` record both carry one `loop-back-to-fix`).
Clause (a) is therefore the number of **distinct `(stage, ts_gate)`** among
fix-deciding records (falling back to the record's `seq` when `ts_gate` is
null) — one gate decision dispatches exactly one fix. On the p3 fixture only
`seq` 1 decides a fix, so every worked number above is unchanged; the
`--self-test` gapless fixture asserts one implied fix for a `redo` shared by a
chunk record and its verifier.

`FIX_ONLY_REASONS` is a **`const` row of the domain table** (`telemetry.md` §Record Schema;
`{red_break}` today), so adding a reason later is a schema change, not a code
constant. Clause (b) is
needed: on the p3 fixture `seq` 18 (`pipeline`, `reason: red_break`) is
reachable only through it — its predecessor `seq` 17 has `gate.decision: null`.

**Mis-typed-fix rule.** An implied fix that exists as a record of another kind
— a `pipeline` record with `dispatch.iteration ≥ 1` whose predecessor at the
same stage decided `loop-back-to-fix`, or whose `dispatch.reason` is fix-only —
counts **0** toward `missing.fix` and is reported by `--lint` as
`[mistyped-fix]`; it is a wrong `kind`, not a missing append, and must not
inflate `expected`. `reason: REVIEW` at `iteration ≥ 1` with **no** preceding
`loop-back-to-fix` at the stage (p3 `seq` 3–5) is a `--lint` **warning**
`[reason-review]`, never a count: the fixture cannot distinguish a mis-recorded
fix from a mis-labelled first dispatch, and a legitimate chunk redo (`seq` 13)
carries the same reason. Promote to a clause at replan only if this cycle's live
file shows the pattern with a known cause.

**Headline definition (ratified, Q-REQ-P4-D).** The reported gap is the **total
shortfall of every implied append, per session**. Output shape:

```
records-vs-expected: 20 recorded, expected 39 (19 missing)                     # headline: Σ missing over all kinds
  implied vs recorded — verifier : 11 vs 0  (11 missing)
  implied vs recorded — pipeline : 11 vs 8  (3 missing)        [implement]
  implied vs recorded — review   :  6 vs 2  (5 missing)
  implied vs recorded — red      :  1 vs 2  (0 missing)
  implied vs recorded — fix      :  2 vs 0  (0 missing; 2 mis-typed — see --lint)
  implement: 14 missing (3 pipeline first attempts + 11 verifier)             # the FULL implication count, never 8 + 3
  secondary: 11 dispatches with no record of their own kind (8 verifier chunks + 3 first attempts)   # optional, never the headline
```

Why the total and not the 8 + 3 reading: `expected` counts appends that should
exist; any narrower headline understates the file's incompleteness, which is the
defect P2 exists to expose. The implications are independent of `seq` and of the
writer's append discipline because each is triggered by a field the writer *did*
fill; the original class (`seq` incremented, record lost) is retained because
`expected` starts from the highest `seq`. The tool still reads nothing but the
telemetry file, and the orchestrator still performs zero reads of it during a
cycle (REQ-TELEM-HARNESSP2-004).

**`COMMIT: INCOMPLETE (accepted): N`** [Amended 2026-09-19, harness-p5 —
REQ-TELEM-HARNESSP5-005]: the per-session `commit` count `summarize` prints
beside the headline is labelled `(accepted)`, because `telemetry.md` §Writer
records the gate's **closing** `COMMIT:` line — an amended omission lands as
`COMPLETE`, so `N` counts `accept (note)` resolutions, never the omissions
rendered. On the frozen p4 fixture it reads `0` although one `INCOMPLETE` was
forced and amended live (finding 5).

### Schema Lint — `--lint` From One Domain Table (REQ-TELEM-HARNESSP4-004)

[Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-004; `docs/ws/harness-p3/verification.md`
§P1/§P3: the R1 fix validated one field and the same session wrote `kind: "gate"`]

`python3 tools/sdd-telemetry.py --lint [--file <path>]` validates **every field
of every record** against its declared domain and exits 1 on any finding, 0
when clean. Finding line shape (one per violation, no record text beyond the
offending value):

```
seq <n>: [<class>] <group.key>: <message>          classes: enum │ type │ key-undeclared │ key-missing │ cross-field │ mistyped-fix
WARN seq <n>: [reason-review] dispatch.reason REVIEW at iteration ≥ 1 with no preceding loop-back-to-fix at <stage>
```

| Check | Rule |
|---|---|
| enum membership | `dispatch.kind`, `dispatch.stage`, `dispatch.reason`, `return.status`, `return.warnings[]`, `scope.token`, every `verdict.*` token, `gate.decision`, `gate.decision_by`, `replan_trigger`, `commit.token`, `cycle.marker` against the table's member sets |
| type | `dispatch.chunk` int-or-null (a header **string** is a finding); every counter int; `scope.widened` int ≥ 0; shas match `^[0-9a-f]{7,12}$` (`"HEAD"` literal and 40-char shas are findings); timestamps ISO-8601 UTC; `v` ∈ the admitted set `{1, 2}` (Q-IMPL-HARNESSP4-002) and **integer-typed** through the shared helper of §Out-of-Loop Reader — `v: 2.0` is a `[type] v` finding (REQ-TELEM-HARNESSP5-004) |
| fixed key set | per `v`: an undeclared key (e.g. `git.commit_n`) is `key-undeclared`; a declared key absent is `key-missing`; the optional `migration` marker (§In-Place Migration) is admitted only with its declared shape — and on **every** admitted `v` (`OPTIONAL_KEYS`, today only `migration`): never `key-undeclared`, never `key-missing`, its value still validated against `{from: chunk-string, at: date}` (a malformed marker is `[type]`, a `from` outside the enum is `[enum]`); the row keeps its `[p4]` mark, which still drives the required key set of the non-optional rows (folded from Q-IMPL-HARNESSP4-006, 2026-09-19) |
| cross-field | the two fix clauses and the mis-typed-fix rule (§Implication-Derived `expected`); non-null `chunk_verdict` on a non-verifier record with **no** `verifier` record for that chunk in the session; **equal-heads**: a `proceed` implement (`pipeline`/`fix`) record with `head_before == head_after` (valid short shas), `return.files_written_n > 0` **and nothing landed** — evaluated on **`v: 2` records only**, firing when `commit.token` is null and exempt when it is `COMPLETE` or `INCOMPLETE` (the `commit` group is the landed evidence — `HEAD_before → HEAD_landed` — not the `git` heads, which are the snapshot pair taken before the orchestrator commits, so equal heads at `proceed` are the compliant sequential shape); a **`v: 1` record is exempt** because it carries no field that can prove landing, and the `migration` marker is **not** stamped on it — `migration.from` keeps its one meaning, a `chunk-string` rewrite that `migrate` performed, and a live record is never edited to satisfy a lint; message `… head_before == head_after and no landed commit group (nothing landed)` (folded from Q-IMPL-HARNESSP4-005 item 2 and Q-IMPL-HARNESSP4-007, 2026-09-19; the `v: 1` exemption is REQ-TELEM-HARNESSP5-003, Q-REQ-P5-B — p4 session 2 `seq` 2, 4, 6 were the live false positive, and the branch has no true positive on record); `commit.token` non-null on a kind whose gate never commits (review, verifier, red) |

**The domain table in the tool is the single source of truth for the record
schema** — one table, two readers. `docs/spec/telemetry.md` §Record Schema and
`references/telemetry.md` §2 are **renderings** of it (stated there). Agreement
is enforced by **parse-and-diff**, not generation: the self-test
`test_schema_table_agrees` parses the `| Group | Key | Type / domain |` rows of
both documents — the `Key` cell may list several backticked keys sharing one
type; enum members are the backticked tokens separated by `\|`; scalar types
are the leading word (`int`, `bool`, `timestamp`, `short sha`, `date`, `string`,
`list`); a row whose `Group` cell is `const` is parsed into a **separate
constant set** `{name: members}` (`telemetry.md` §Record Schema, `const` rows) and never into
`group.key` — and asserts that the set of `group.key`, for enum-typed keys the
member set, and the constant set with each constant's members, equal the code
table's; it further asserts `FIX_ONLY_REASONS ⊆ dispatch.reason` members
[M3]. Adding a row on either side alone fails the self-test. Why not generate the spec block from the code: a generated block
would be a code-owned write into an Approved spec on every schema change,
which the write-scope contract tags `ADVISORY` and review must re-read; parsing
keeps the spec the human-reviewed artifact and the code the executable one.
The `Source (gate signal)` column is prose and is not compared.

**Finding order** [Added 2026-09-19, harness-p5 — REQ-TELEM-HARNESSP5-006]:
`lint()` stable-sorts its findings by `(int seq ascending, then non-int seqs in
insertion order)` before rendering, across its three passes (per-record
type/enum/key; per-session mis-typed-fix and cross-field; reason-review), so a
cross-field finding on `seq` 2 renders before a type finding on `seq` 5. The
frozen p3 fixture's finding **set** is unchanged; because the sort may reorder
its lines, every fixture assertion on `--lint` output compares the **sorted**
finding lines (sha256 over the sorted lines — order-insensitive), the same
comparison REQ-TELEM-HARNESSP5-003's acceptance uses.

**Verifier-advisory self-test cases** [Added 2026-09-19, harness-p5 —
REQ-TELEM-HARNESSP5-008; `docs/ws/harness-p4/verification.md` advisories]:
`--self-test` names three further cases, each failing when its check is removed
in a temp copy: (a) `commit.token` non-null on a non-committing kind **other
than** `review` (`verifier` or `red`) → `[cross-field]`; (b) `dispatch.reason:
RED_BREAK` (uppercase) → `[enum]`, so the canonical `red_break` spelling is
tested, not only stated; (c) `migration.from` outside the `chunk-string` enum →
`[enum]` (the validator accepted any string). The frozen fixtures' outputs are
unchanged by all three.

### Lint Guard (REQ-TELEM-HARNESSP2-007, REQ-LINT-HARNESSP2-002)

[Moved from `telemetry.md` 2026-09-19 with §Skill and Lint Changes — the guard
that keeps every skill from reading the file is lint-side, so it lives with the
schema lint; `telemetry.md` §Third Observation cites it.]

`tools/sdd-skill-lint.py` gains one `FORBIDDEN` row (fail severity):

| Field | Value |
|---|---|
| `pattern` | `\.sdd/` |
| `files` | `None` (every `skills/*/SKILL.md` and `skills/*/references/*.md`) |
| `allow_files` (**new** row field, file-granular) | `skills/sdd-orchestrate/SKILL.md`, `skills/sdd-orchestrate/references/telemetry.md`, `skills/sdd-orchestrate/references/write-scope.md` |
| `allow` (line-level) | `[]` |
| `reason` | `telemetry is orchestrator-written and never a phase-detection or staleness input (REQ-ORCH-014)` |
| `fix` | `remove the reference — skills never read .sdd/; only sdd-orchestrate's telemetry stub and references/telemetry.md may name it` |

- The existing `check_forbidden()` scans raw lines and does **not** skip fenced
  code, which is what this row needs: a skill must not even show the path in an
  example. `allow_files` is a new per-row field consulted before the line
  loop (`rel in allow_files` → skip the file for this row); rows without it
  behave as today.
- The row is file-granular. The §3/§5-only restriction inside `write-scope.md`
  and the "stub ≤ 10 lines" rule for `SKILL.md` are review checks, not lint
  checks.
- Operator documentation (`skills/sdd-orchestrate/USAGE.md`, `CLAUDE.md`) is
  outside `skill_files()` and may name the path; wherever it does, the text
  "gitignored, orchestrator-only, never read by phase detection" sits beside it
  (REQ-SKILL-HARNESSP2-008).
- `--self-test` gains: a fixture skill containing `.sdd/telemetry.jsonl` inside
  a fence fails with this row's fix string; a fixture named as one of the three
  allowlisted paths passes.

### Skill and Lint Changes (REQ-SKILL-HARNESSP2-001, -008; REQ-LINT-HARNESSP2-002)

| Where | Change |
|---|---|
| `skills/sdd-orchestrate/references/telemetry.md` (**new**) | record schema and field-source table, budget grammar, writer sequence, `TELEMETRY:` line family, third observation and the `OUT .sdd/telemetry.jsonl …` finding strings (defined once), non-interference table, scorer derivation, post-cycle pointer to `tools/sdd-telemetry.py summarize` |
| `skills/sdd-orchestrate/SKILL.md` | a telemetry **stub** ≤ 10 lines: default on, KICKOFF opt-out, "orchestrator appends after each gate", "never read by phase detection", link to the reference |
| `skills/sdd-orchestrate/references/write-scope.md` §3, §5 | §3 specifies the third observation; §5 adds limitation (b)'s `.sdd/` exception — both by citing `references/telemetry.md` for the finding string |
| `skills/sdd-orchestrate/references/dispatch-templates.md`, `fan-out.md` | **no change** — no template names `.sdd/` |
| `.gitignore` | `.sdd/` (may be written by the orchestrator's bootstrap) |
| `tools/sdd-skill-lint.py` | the `FORBIDDEN` row and `allow_files` field above; self-test cases |
| `tools/sdd-scope-check-selftest.py` | scenario **F7** "leaf appends to `.sdd/telemetry.jsonl`" → `SCOPE: VIOLATION (1 paths)`, the `OUT … (+1 records, leaf write — reverted)` line, and a post-revert line count equal to the before-count |
| `tools/sdd-telemetry.py` (**new**) | §Out-of-Loop Reader |
| `skills/sdd-orchestrate/USAGE.md` | one section per new signal across this cycle: `TELEMETRY:` lines and the KICKOFF choice (this spec); red opt-in / `RED_VERDICT:` / `pending-red` (`adversarial-verify.md`); `REVIEW: CONTRADICTION` and its four options (`arbitrated-handoff.md`); `GC:` summary at entry and DONE (`drift-sweep.md`) |
| `CLAUDE.md` §SDD | **one short paragraph** naming telemetry (gitignored, orchestrator-only, never read by phase detection), the red opt-in, the contradiction pause and the gc sweep; the four-verification-layer bullet is unchanged |

### In-Place Migration of the 8 p3 Records, Stamped Partial (REQ-TELEM-HARNESSP4-005)

[Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-005; decided at DISCUSS
(`docs/ws/harness-p4/kickoff.md`), inherited unchanged]

`python3 tools/sdd-telemetry.py migrate --file <path> [--out <path>]` rewrites
every `dispatch.chunk` header string `"Chunk N"` to the integer `N` and adds a
**migration marker** to each rewritten record:

```
"migration": {"from": "chunk-string", "at": "2026-09-18"}      # enum + date; admitted by the domain table as OPTIONAL, present only on migrated records
```

- **Operator-invoked, between sessions.** This is the **second exception** to
  `telemetry.md` §Writer's append-only rule (the first is the leaf-write revert). It is run by
  the operator with no orchestrator session open — never by a leaf (which would
  breach the orchestrator-only-writer rule) and never while a session is
  appending (a race with the orchestrator's appends). No dispatch template
  mentions it; `--help` and `references/telemetry.md` §7 state the rule.
- **In place** when `--out` is absent: write to a sibling temp file, verify the
  line count is unchanged, then rename over the original. `--out` writes
  elsewhere and leaves the input untouched.
- **Idempotent**: an already-int `chunk` and an already-present `migration`
  marker are left alone; a second run changes nothing.
- **Never a lint device** [Added 2026-09-19, harness-p5 — REQ-TELEM-HARNESSP5-003]:
  the marker records a `chunk-string` rewrite that happened; it is never
  stamped on a record to exempt it from a `--lint` rule (the `v: 1`
  equal-heads exemption of §Schema Lint needs no marker), and a live record
  carrying no defect is never rewritten.
- **Fixture guard**: a `--file` (or `--out`) path under `tools/fixtures/` is
  refused with exit 2 and **no write**; every test runs against the frozen
  fixture as input with `--out` in a temporary directory.
- **Ordered**: the plan schedules the migration task only after
  REQ-TELEM-HARNESSP4-001, -002, -003 and -004 have landed and `--lint` reports
  the migrated records clean on their **typed** fields; otherwise the migrated
  block asserts more than the evidence supports.

**Stamped-partial block shape.** `summarize`'s per-chunk block renders, for any
chunk whose records carry the marker, a `partial` stamp naming the kinds that
cannot be reconstructed:

```
per-chunk (implement)
  Chunk 0   pipeline 1   verifier 0   fix 0   redo 0   partial — migrated from "Chunk 0"; verifier, fix and redo records were never written and cannot be reconstructed
  …
  Chunk 7   pipeline 1   verifier 0   fix 0   redo 1   partial — migrated from "Chunk 7"; verifier, fix and redo records were never written and cannot be reconstructed
```

The block therefore cannot be read as a full per-chunk history. The frozen
fixture `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` is read-only
evidence and is **never** modified, reformatted or migrated (its sha256 is in
`tools/fixtures/README.md`).

### `--plan` Floor for Implement-Stage Expectations (REQ-TELEM-HARNESSP4-008) [may]

[Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-008; medium confidence, RS-HARNESSP4-001 §Q2 candidates table]

`summarize --plan <path>` **may** compute an implement-stage **floor**:
`chunk_count(plan)` pipeline dispatches, doubled when any chunk record in the
session carries a non-null `chunk_verdict` (the verifier was on), and report
`implement floor: 8 pipeline (16 with verifier); recorded implement records: N;
shortfall: max(0, floor − N)`. It is the only reader-side check that sees a
chunk whose pipeline **and** verifier records are both missing; it can never see
redos (session state the plan does not hold). Opt-in; reads an artifact that
already exists; no new artifact and no phase-detection input. If not built, it
is queued under `verification.md` §Next Steps.

**Shortfall operands** [folded from Q-IMPL-HARNESSP4-005 item 3, 2026-09-19]:
`shortfall = max(0, chunk_count − recorded implement pipeline records)`; the
"(2N with verifier)" figure is informational only, because the verifier half is
already reported by the implication line (`implied vs recorded — verifier`) and
counting it twice would contradict §Fixture-Based Test Contract's "no shortfall
against 8 recorded pipeline records" on the p3 fixture.

### Fixture-Based Test Contract

[Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-001..005]

Every reader-side test runs against `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
**as read-only input**: the test asserts the file's sha256
(`7e20b630…af9237`, `tools/fixtures/README.md`) before and after, writes any
output (`migrate --out`) under a temporary directory, and never opens the
fixture for writing. Expected values on the fixture:

| Command | Expected |
|---|---|
| `summarize --file <fixture>` | headline `expected 39` against 20 records (19 missing); implement line 14 missing; verifier 11 vs 0; pipeline 11 vs 8 at implement; review 6 vs 2 (5 missing); red 1 vs 2 (0 missing); fix implied 2, recorded 0, missing 0 |
| `--lint --file <fixture>` | exit 1; at minimum: `kind: gate` on `seq` 20; header strings in `dispatch.chunk` on `seq` 6–13; `head_after: "HEAD"` on `seq` 5; null `git` heads on `seq` 6–14; 40-character shas on `seq` 15–20; undeclared `git.commit_n` on `seq` 15–20; `[mistyped-fix]` on `seq` 2 and 18; `[reason-review]` warnings on `seq` 3–5 |
| `migrate --file <copy> --out <tmp>` | output on which `summarize` renders a per-chunk block for chunks 0–7 carrying `partial` and the unreconstructable kinds |
| `migrate --file <fixture>` | exit 2, no write, fixture sha unchanged |
| `summarize --plan docs/ws/harness-p3/plan.md --file <fixture>` (if built) | floor 8 (16 with verifier); no shortfall against 8 recorded pipeline records; the implication line still reports 14 missing |

`--self-test` builds synthetic fixtures in a temporary directory for: each
implication (verifier, redo first attempt, review, red), clause (b) (`red_break`
pipeline record with a null-decision predecessor), a `loop-back-to-fix` followed
by no record at all (1 missing fix), a gapless negative fixture (0 missing)
that **includes one compliant redone chunk** — `pipeline` `redo: 0` + `fix`
`redo: 1`, both carrying `chunk_verdict`, with their two `verifier` records —
asserting 2 implied verifiers / 1 implied pipeline / 0 missing [C1], a
`v: 1`-and-`v: 2` mixed fixture summarised with zero skipped records [M1], a
record carrying `FIX_ONLY_REASONS` as a key (`key-undeclared`) [M3], one
mutation per domain class, `scope.widened: 2` in-domain vs a string value,
`commit` in-domain (`INCOMPLETE, 1, 0`) vs `token: DROPPED`, the
schema-agreement diff (a row added on one side only), and a plan with a chunk
that has no record at all (if `--plan` is built).

**The frozen p4 fixture** [Added 2026-09-19, harness-p5 — REQ-TELEM-HARNESSP5-007;
RS-HARNESSP5-001 §Q2 "Fixture"]. `tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl`
is `head -67` of `.sdd/telemetry.jsonl` as it stood at harness-p4 DONE — **67
lines**: the p3 migrated records at lines 1–20, and harness-p4 at lines
21–67 — session 1 is 20 records at `v: 1`, session 2 is 27 records at `v: 2`
starting at `seq` 8, and the last record is `seq` 34, `kind: review`, stage
`verify` (`docs/ws/harness-p4/plan.md` O2). harness-p5's own records begin at
line 68 of the live file and are excluded from the fixture. It is cut by the **operator** as a plan
operator task scheduled before the telemetry chunk (leaves never read `.sdd/`),
its sha256 recorded in `tools/fixtures/README.md`, and the `migrate` fixture
guard covers it by path. Findings 1, 2, 3 and 5 of RS-HARNESSP5-001 §Q2 are
reproduced on it; 4 and 6 are synthetic self-test cases. The p3 fixture and the
live file are never modified. Expected values on the p4 fixture (the p3 rows
above are unchanged — sha256 asserted before and after each run):

| Command | Expected |
|---|---|
| `summarize --file <p4 fixture>` | **no** missing pipeline for the `(implement, chunk null)` group (REQ-TELEM-HARNESSP5-002); `COMMIT: INCOMPLETE (accepted): 0` (REQ-TELEM-HARNESSP5-005); every REQ-TELEM-HARNESSP4-002 number of the p3 rows unchanged |
| `--lint --file <p4 fixture>` | the three stage-level `fix` records of session 2 (`seq` 21, 24, 27 — `chunk_verdict` with `chunk: null`) listed as `[cross-field]` findings **by seq** (historical fact, like the p3 `seq` 20; REQ-TELEM-HARNESSP5-001, -006); **no** equal-heads finding on session 2 `seq` 2, 4, 6 (`v: 1`, REQ-TELEM-HARNESSP5-003) |
| `--self-test` | a session with three stage-level fixes and no chunk record → 0 implied pipeline; `v: 1` + equal heads + `files_written_n > 0` → no finding, the same shape as `v: 2` with null `commit.token` → finding; a `v: 2.0` record skipped and counted by `summarize` and `[type] v` under `--lint`; a type finding on `seq` 5 and a cross-field finding on `seq` 2 rendered 2, 5; the three advisory cases (a)–(c) |

## Verification

### Automated

- `test_summarize_six_record_fixture`: one row per stage with every column;
  `--self-test` exits 0; an unknown-`v` record is skipped and counted.
- `test_lint_forbidden_sdd_row`: `.sdd/telemetry.jsonl` inside a fence in a
  fixture `sdd-plan/SKILL.md` → exit 1 with the row's fix; the three allowlisted
  paths → exit 0; shipped skill set → exit 0.
- `test_null_chunk_group_implies_no_pipeline`: three stage-level `fix`
  records and no chunk record → `implied.pipeline` 0; the p3 fixture's
  `expected 39` / 19 missing unchanged (REQ-TELEM-HARNESSP5-002).
- `test_v1_exempt_from_equal_heads`: `v: 1`, equal heads, `files_written_n: 3`
  → no finding; `v: 2`, equal heads, `commit.token: null`, `files_written_n: 3`
  → finding; p4 fixture `seq` 2/4/6 clean (REQ-TELEM-HARNESSP5-003).
- `test_v_admission_is_int_typed`: `v: 2.0` → `summarize` `skipped: 1`,
  `--lint` `[type] v`; `grep -c 'ADMITTED_V' tools/sdd-telemetry.py` shows one
  helper called from both `load()` paths (REQ-TELEM-HARNESSP5-004).
- `test_lint_findings_in_seq_order`: findings on `seq` 5 (type) and `seq` 2
  (cross-field) render 2, 5; the p3 finding set's sha256 over sorted lines is
  unchanged (REQ-TELEM-HARNESSP5-006).
- `test_p4_fixture_frozen`: `wc -l` = 67 and the README sha256 asserted
  before and after every case that reads it (REQ-TELEM-HARNESSP5-007).
- `test_advisory_cases`: (a) `verifier` with `commit.token: COMPLETE` →
  `[cross-field]`; (b) `reason: RED_BREAK` → `[enum]`; (c) `migration.from:
  "other"` → `[enum]`; each fails when its check is removed (REQ-TELEM-HARNESSP5-008).

### Manual

- After a cycle, run `summarize` and `--lint` on the live file and confirm the
  per-kind lines and the `COMMIT: INCOMPLETE (accepted)` count match the gates
  the operator saw.

### Acceptance Criteria

- [ ] `tools/sdd-telemetry.py summarize` with the columns above, `--help`, `--self-test`, unknown-`v` tolerance; not invoked by any skill (REQ-TELEM-HARNESSP2-009)
- [ ] Scorer derivation table present and complete against `evaluation.md` §Scorer Fields
- [ ] **If built**: `python3 tools/sdd-telemetry.py summarize` on a fixture whose session records fewer appends than gates prints a records-vs-expected line for that session, and `--self-test` exits 0. **If not built**: it is queued under `verification.md` §Next Steps and nothing else changed (REQ-TELEM-HARNESSP3-002)
- [ ] `summarize --file tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` prints `expected 39` against 20 records (19 missing), an implement line of 14 missing, and per-kind lines verifier 11 vs 0, pipeline 11 vs 8 at implement, review 6 vs 2 (5 missing), red 1 vs 2 (0 missing); `--self-test` covers each implication and a gapless negative fixture reading 0 missing, that fixture including one compliant redone chunk (`pipeline` `redo: 0` + `fix` `redo: 1`, both with `chunk_verdict`) that yields 2 implied verifiers / 1 implied pipeline; the formulas are computed per `(stage, chunk)` group and §Records-vs-Expected states both worked shapes beside them; §Records-vs-Expected and `references/telemetry.md` §7 state the definition and the headline; Q-IMPL-HARNESSP3-006 is amended to name the fields; the tool reads only the telemetry file and the orchestrator performs zero reads of it (REQ-TELEM-HARNESSP4-002)
- [ ] On the fixture the tool reports `implied.fix 2, recorded 0, missing 0` with `seq` 2 and 18 listed as `[mistyped-fix]` by `--lint` and `seq` 3–5 as `[reason-review]` warnings; a `red_break` pipeline record with a null-decision predecessor is flagged (clause (b)); a `loop-back-to-fix` followed by no record counts 1 missing fix; `FIX_ONLY_REASONS` is a `const` row of the domain table rendered as a real row in `telemetry.md` §Record Schema and `references/telemetry.md` §2, parsed into the constant set (never `group.key`) by `test_schema_table_agrees`, with `--lint` asserting it is a subset of `dispatch.reason` (REQ-TELEM-HARNESSP4-003, -004)
- [ ] `--lint --file <fixture>` exits non-zero reporting at minimum `kind: gate` (`seq` 20), header strings (`seq` 6–13), `head_after: "HEAD"` (`seq` 5), null `git` heads (`seq` 6–14), 40-character shas and undeclared `git.commit_n` (`seq` 15–20); a gapless in-domain fixture exits 0; `--self-test` covers each domain class with one mutation; `test_schema_table_agrees` fails when a row is added to the code table but not this spec's table or vice versa; `telemetry.md` §Record Schema states it is a rendering of the code table; `python3 tools/sdd-skill-lint.py` exits 0 (REQ-TELEM-HARNESSP4-004)
- [ ] `sha256sum tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` reads `7e20b630…af9237` at DONE and `git diff --stat main -- tools/fixtures/` is empty; `migrate --file <copy> --out <tmp>` yields a file whose per-chunk block for chunks 0–7 carries `partial` and names the unreconstructable kinds; `migrate --file <fixture>` exits 2 without writing; the plan lists the migration task after the four prerequisite tasks; the operator ran `migrate` on the live file before the verify stage with no session open, and `verification.md` records the `--lint` result on the migrated records (no typed-field finding) (REQ-TELEM-HARNESSP4-005)
- [ ] **If built**: `summarize --plan docs/ws/harness-p3/plan.md --file <fixture>` prints an implement floor of 8 (16 with verifier), flags no shortfall against 8 recorded pipeline records while the implication line still reports 14 missing; `--self-test` covers a plan with a chunk that has no record. **If not built**: queued under `verification.md` §Next Steps (REQ-TELEM-HARNESSP4-008)
- [ ] Every fixture-based test asserts the fixture's sha256 before and after and writes outputs only under a temporary directory (§Fixture-Based Test Contract)
- [ ] `FORBIDDEN` row `\.sdd/` with the three-file `allow_files` allowlist, raw-text scan, stated reason and fix (REQ-TELEM-HARNESSP2-007, REQ-LINT-HARNESSP2-002)
- [ ] `references/telemetry.md` exists and resolves; `SKILL.md` stub ≤ 10 lines; no template names `.sdd/` (REQ-SKILL-HARNESSP2-001)
- [ ] `USAGE.md` has a section per new signal; `CLAUDE.md` diff is one paragraph and the four-layer bullet is unchanged (REQ-SKILL-HARNESSP2-008)
- [ ] `summarize --file tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl` reports no missing pipeline for the `(implement, chunk null)` group; the p3 fixture's `expected 39` / 19 missing and every REQ-TELEM-HARNESSP4-002 number are unchanged (sha256 asserted before and after); `--self-test` covers three stage-level fixes with no chunk record → 0 implied pipeline (REQ-TELEM-HARNESSP5-002)
- [ ] `--self-test`: `v: 1` + equal heads + `files_written_n > 0` → no finding, the same shape as `v: 2` with null `commit.token` → finding; on the p4 fixture `--lint` raises no equal-heads finding on session 2 `seq` 2/4/6; the p3 fixture's finding set is unchanged, compared order-insensitively; no `migration` marker is stamped (REQ-TELEM-HARNESSP5-003)
- [ ] `--self-test` feeds `v: 2.0`: `summarize` reports it skipped and counted, `--lint` emits `[type] v`; `grep -c 'ADMITTED_V' tools/sdd-telemetry.py` shows the membership test in one helper called from both `load()` paths (REQ-TELEM-HARNESSP5-004)
- [ ] `summarize` on the p4 fixture prints `COMMIT: INCOMPLETE (accepted): 0`; the label is stated in §Records-vs-Expected and §Fixture-Based Test Contract; `test_schema_table_agrees` still passes (REQ-TELEM-HARNESSP5-005)
- [ ] `--self-test` builds a type finding on `seq` 5 and a cross-field finding on `seq` 2 and asserts the rendered order 2, 5; the p3 finding set's sha256 over sorted lines is unchanged (REQ-TELEM-HARNESSP5-006)
- [ ] `shasum -a 256 tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl` matches `tools/fixtures/README.md`; `wc -l` = 67; `git diff --stat main -- tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` is empty; the fixture was cut by the operator (plan operator task before the telemetry chunk) and its sha256 is asserted before and after every `--self-test` case that reads it (REQ-TELEM-HARNESSP5-007)
- [ ] The three advisory cases are named in `--self-test` output and each fails when its check is removed in a temp copy; the frozen fixtures' outputs are unchanged (REQ-TELEM-HARNESSP5-008)
- [ ] The Q-IMPL-HARNESSP4-004..009 fold-in status notes count six across the three carrying specs (REQ-QIMPL-HARNESSP5-001's grep) — Q-IMPL-HARNESSP4-004, -005, -006, -007 here, -008 in `skill-lint-v5.md`, -009 in `harness-chunk-verifier.md` (REQ-QIMPL-HARNESSP5-001, owned by `deviation-protocol.md`)
- [ ] This file is under the amended ~800-line bound of REQ-LINT-HARNESSP5-003 (Q-REQ-P5-I, 2026-09-19; 697 lines as split); every `## Implementation Questions` entry sits with the section it amends, unrenumbered; `python3 tools/sdd-gc.py --report` raises no `qimpl-broken-ref` finding here (REQ-LINT-HARNESSP5-003)

## Edge Cases

- **Torn or non-JSON line** (two sessions appending, `telemetry.md` §Edge Cases):
  skipped and counted on the trailing `skipped:` line by both entry points.
- **Record with `v` outside the admitted set** (`3`, `"2"`, `2.0`, `true`):
  skipped and counted by `summarize`, a `[type] v` finding under `--lint` —
  never silently admitted (REQ-TELEM-HARNESSP5-004).
- **A `(implement, null)` group whose stage-level fix record does carry a
  `chunk_verdict`** (the p4 shape): a `[cross-field]` writer defect, not an
  implied pipeline — the reader never infers a chunk from it.
- **Marker `3` repositories**: identical; `cycle.workstream` is `default`.

## Cross-Spec Consistency (XSPEC)

- `telemetry.md` §Record Schema is the rendering this file's `--lint` is
  checked against; `telemetry.md` §Writer rule (i) (per-chunk-only `chunk_verdict`) and
  §Records-vs-Expected's chunk-group-only `implied.pipeline` are the two
  halves of Q-REQ-P5-B; the `commit` group's closing-line reading is stated in
  `telemetry.md` §Writer and labelled here.
- `harness-commit-fidelity.md` §Placement: `amend` re-renders `COMPLETE`
  before the gate closes, which is why the recorded token can read `COMPLETE`
  for an omission the operator saw.
- `harness-write-scope.md` §Observation / `references/write-scope.md` §3:
  `git.head_after` is the snapshot pair's `HEAD_after`, taken before the
  orchestrator commits — the reason the equal-heads rule keys on
  `commit.token`, not on the heads.
- `adversarial-verify.md`: `red_break` is the `RED_BREAK` packet lower-cased;
  the uppercase form is rejected by `--lint` and now tested.
- `evaluation.md` §Scorer Fields ↔ §Scorer Derivation: every field derivable.
- **No unresolved contradictions.**

**harness-p5 pass (2026-09-19).** No extractable type definitions in this file
(pseudocode formulas and tables only). Token checks: `[cross-field]`, `[type]`,
`[enum]`, `[mistyped-fix]`, `[reason-review]` are the finding classes of
§Schema Lint and appear nowhere else with another meaning; `COMMIT: INCOMPLETE
(accepted)` is a `summarize` label, not a gate token — the gate family stays
`COMPLETE | INCOMPLETE` (`harness-commit-fidelity.md`).

## Open Questions

1. **Runner placement for the p4 fixture cases.** Default: `tools/sdd-telemetry.py
   --self-test`, beside the p3 cases; no second tool.
2. Inherited from `telemetry.md` §Open Questions (locking, `gate.decision`
   completeness, timestamp precision) — unchanged.

## Implementation Questions

### Q-IMPL-HARNESSP3-006: `summarize`'s expected count is derived from gate records, not from the gate
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Records-vs-Expected in `summarize`
**Decision**:

REQ-TELEM-HARNESSP3-002's "expected" is computed from the records themselves —
the highest `dispatch.seq` observed per session versus the number of records
carrying that session id — so the reader needs no side channel from the
orchestrator and stays a pure post-cycle function of the file.
[Amended 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-002: "derived from gate
records" stays true; the **fields** used are now `verdict.chunk_verdict`,
`dispatch.redo`, `verdict.review_verdict`, `verdict.red_verdict`,
`gate.decision` and `dispatch.reason` (the cross-field implications of
§Records-vs-Expected), added to the highest `dispatch.seq`.]
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP4-004: clause (a) of `implied.fix` counts deciding gates, not records
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Implication-Derived `expected` and the Headline, clause (a) — "#records with `gate.decision` ∈ {loop-back-to-fix, fix, redo}"
**Decision**:

`telemetry.md` §Writer gives a verifier, review or red record the `gate.decision` of the gate
it fed, so on a **compliant** file a chunk record and its `verifier` record both
carry the per-chunk `redo` decision (and a stage record and its `review` record
both carry a `loop-back-to-fix`). Read literally per record, clause (a) implies
two fixes for one decision and REQ-TELEM-HARNESSP4-001's "0 missing on a live
redo" cannot hold. `tools/sdd-telemetry.py` counts clause (a) **per deciding
gate**: records sharing one gate share `ts_gate`, so the count is the number of
distinct `(stage, ts_gate)` among fix-deciding records (falling back to the
record's `seq` when `ts_gate` is null). On the p3 fixture only `seq` 1 decides
a fix, so `implied.fix` stays 2 and every worked number in the section is
unchanged; the `--self-test` gapless fixture asserts one implied fix for a
`redo` shared by a chunk record and its verifier.
**Rationale**: one gate decision dispatches exactly one fix — the intent the
clause's own comment states ("each such decision dispatches one fix"); no
record key is added and the reader still reads nothing but the telemetry file.
**Date**: 2026-09-19 (implement stage, Chunk 2)
**Status**: `[folded into §Implication-Derived \`expected\` and the Headline, 2026-09-19]` (REQ-QIMPL-HARNESSP5-001)

### Q-IMPL-HARNESSP4-005: `--lint` reason members, the `proceed`/equal-heads exemption and the `--plan` shortfall operands
**Tier**: 2 (spec ambiguity)
**Spec reference**: `telemetry.md` section Record Schema (`dispatch.reason` row); §Schema Lint (cross-field row), §`--plan` Floor
**Decision**: (1) The `dispatch.reason` cell only *names* the repair-packet enum, so the
code table carries its members explicitly: `REVIEW`, `VERIFIER_FAIL`, `PARTIAL_CONTINUE`,
`MERGE_CONFLICT` (`harness-return-contract.md` §Repair Packet), `THIRD_OPINION`
(`arbitrated-handoff.md`) and `red_break` — the RED_BREAK packet as the record spells it and
as the `const` row `FIX_ONLY_REASONS` lists it; the uppercase `RED_BREAK` is **not** admitted, so
one spelling is canonical and the subset relation holds. `replan_trigger`'s members (`stuck`,
`spike`, `verification`, `operator`) are likewise explicit. (2) The cross-field rule "`proceed`
implement record with `head_before == head_after`" applies to `pipeline`/`fix` records at
`implement` whose heads are valid short shas and whose `return.files_written_n` is non-zero — a
leaf that wrote nothing legitimately leaves `HEAD` unchanged. (3) `--plan`'s `shortfall` is
`max(0, chunk_count − recorded implement pipeline records)`; the "(2N with verifier)" figure
is informational, because the verifier half is already reported by the implication line
(`implied vs recorded — verifier`) and counting it twice would contradict §Fixture-Based Test
Contract's "no shortfall against 8 recorded pipeline records" on the p3 fixture.
**Rationale**: the table cells are Approved text and are parsed, not edited; members a cell only
names must live in the code table (the `members` override), and both refinements make the
lint's negative fixture and the fixture-contract expectations satisfiable without a contract change.
**Date**: 2026-09-19 (implement stage, Chunk 3)
**Status**: `[folded into telemetry.md section Record Schema (reason members), §Schema Lint (equal-heads) and §\`--plan\` Floor (shortfall operands), 2026-09-19]` (REQ-QIMPL-HARNESSP5-001)

### Q-IMPL-HARNESSP3-018: `summarize` derives a session boundary from a `dispatch.seq` reset
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Records-vs-Expected in `summarize`
**Decision**:

No record carries a session id, so the reader derives one: within a
(`cycle.workstream`, `cycle.research_id`) group ordered by `ts_dispatch`, a new
session opens at the first record and at every record whose `dispatch.seq` does
not exceed its predecessor's — `seq` is 1-based per session (`telemetry.md` §Record Schema), so
a reset is the only observable session boundary. `expected` is then the highest
`seq` in the session and `gap = expected - recorded`. Purely reader-side; no
record key is added and no side channel from the orchestrator is used
(Q-IMPL-HARNESSP3-006).
**Date**: 2026-09-18 (implement stage, Chunk 4)

### Q-IMPL-HARNESSP4-006: the OPTIONAL `migration` marker is admitted by `--lint` on every `v`
**Tier**: 2 (spec ambiguity)
**Spec reference**: §In-Place Migration of the 8 p3 Records, Stamped Partial — "admitted by the domain table as OPTIONAL, present only on migrated records"; §Schema Lint — the per-`v` key set is derived from the `[p4]` marks (Q-IMPL-HARNESSP4-002)
**Decision**: `--lint` treats a key in `OPTIONAL_KEYS` (today only `migration`) as declared for **every** admitted `v` — never `key-undeclared`, never `key-missing` — while still validating its value against the row's declared `{from: chunk-string, at: date}` shape (a malformed marker is a `[type]` finding). The row keeps its `[p4]` mark in both renderings; the mark still drives the required key set for the non-optional rows exactly as Q-IMPL-HARNESSP4-002 fixes it.
**Rationale**: the only records `migrate` ever rewrites are the p3 `v: 1` records (`seq` 6–13 of the frozen fixture); reading the `[p4]` mark strictly would make every migrated record a `key-undeclared` finding, so the migration could never leave the records lint-clean as §In-Place Migration ("Ordered") requires. `v` is not bumped by the migration because a `v: 2` record must carry the `commit` group and `scope.widened`, which were never observed for those dispatches and cannot be reconstructed — the same reason the block is stamped `partial`. The other fixture findings (`kind: gate` on `seq` 20, the sha and `git.commit_n` findings) are untouched by the migration and still exit 1.
**Date**: 2026-09-19 (implement stage, Chunk 4)
**Status**: `[folded into §Schema Lint (fixed key set row), 2026-09-19]` (REQ-QIMPL-HARNESSP5-001)

### Q-IMPL-HARNESSP4-007: the equal-heads cross-field rule fires only when nothing landed
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Schema Lint (cross-field row — "`proceed` implement record with `head_before == head_after`"); `telemetry.md` section Record Schema (`git` row — "the snapshot pair's `HEAD_before` / `HEAD_after`"); `skills/sdd-orchestrate/references/write-scope.md`, section 3 (snapshot pair) and section 7a (`HEAD_landed`)
**Decision**: `git.head_after` keeps its `telemetry.md` §Record Schema meaning — the snapshot pair's `HEAD_after`, taken on the leaf's return and **before** the orchestrator commits — so in sequential mode a compliant leaf that never commits always yields `head_before == head_after` at `proceed`. The cross-field rule is therefore narrowed to fire **only when the record shows nothing landed**: a `v: 2` record whose `commit.token` is null, or a `v: 1` record (which carries no `commit` group), with `return.files_written_n > 0` (Q-IMPL-HARNESSP4-005 item 2 unchanged). A record whose `commit.token` is `COMPLETE` or `INCOMPLETE` is exempt: the `commit` group is the landed evidence (`HEAD_before → HEAD_landed`), not the `git` heads. The finding message reads "… head_before == head_after and no landed commit group (nothing landed)". The worked `fix` example in `telemetry.md` §Record Schema shows distinct heads with `commit.token: COMPLETE`; that shape stays lint-clean, but distinct heads are not what the rule keys on. Approved text is not edited; the `--self-test` covers both directions (equal heads + `COMPLETE`/`INCOMPLETE` → no finding; equal heads + null token + `files_written_n > 0` → finding; equal heads + null token + `files_written_n: 0` → no finding).
**Rationale**: the previous reading — equal heads mean "nothing was committed" — treated `head_after` as the landed head, contradicting the `git` row and `write-scope.md` §3; on the first two fresh `v: 2` records of this cycle it flagged a compliant `proceed` record whose `commit.token` was `COMPLETE` with 6 paths landed. Keying the rule on the commit group makes the finding true by construction and keeps the frozen fixture's contract unchanged (its `v: 1` records have no commit group, so their behaviour is identical).
**Date**: 2026-09-19 (implement stage, Chunk 3 redo)
**Status**: `[folded into §Schema Lint (cross-field row), 2026-09-19]` (REQ-QIMPL-HARNESSP5-001) — the `v: 1` branch of this entry is superseded in Approved text by the REQ-TELEM-HARNESSP5-003 exemption stated there; the entry body is unchanged.

### Q-IMPL-HARNESSP2-070: `skill_files()` lints USAGE.md, so it is allowlisted for the `\.sdd/` row
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Lint Guard ("USAGE.md is outside `skill_files()`")
**Decision**: the linter's `skill_files()` rglobs every `skills/**/*.md`, including `skills/sdd-orchestrate/USAGE.md`; the spec's factual claim was wrong. `skills/sdd-orchestrate/USAGE.md` is added to the `\.sdd/` row's `allow_files` (exact path) so operator docs may name the path per REQ-SKILL-HARNESSP2-008. The allow set is therefore the spec's three files plus USAGE.md.
**Rationale**: minimal change preserving intent; excluding USAGE.md from `skill_files()` would silently drop its other lint coverage.
**Date**: 2026-09-18 (Chunk 6)

### Q-IMPL-HARNESSP2-071: a negative `.sdd/` mention in `references/drift-sweep.md` was reworded, not allowlisted
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Lint Guard (`allow: []`)
**Decision**: `references/drift-sweep.md` (Chunk 5) said gc "never reads `.sdd/`"; reworded to "never reads the telemetry file (`telemetry.md`)" so the allow set stays minimal.
**Rationale**: the row scans raw text incl. fences and negative mentions; rewording is cheaper and spec-conformant.
**Date**: 2026-09-18 (Chunk 6)
