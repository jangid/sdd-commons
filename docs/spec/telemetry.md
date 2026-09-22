---
status: Approved
last_updated: 2026-09-22
requires:
  - REQ-TELEM-HARNESSP2-001
  - REQ-TELEM-HARNESSP2-002
  - REQ-TELEM-HARNESSP2-003
  - REQ-TELEM-HARNESSP2-004
  - REQ-TELEM-HARNESSP2-005
  - REQ-TELEM-HARNESSP2-006
  - REQ-TELEM-HARNESSP2-008
  - REQ-HARN-027
  - REQ-TELEM-HARNESSP3-001
  - REQ-TELEM-HARNESSP4-001
  - REQ-TELEM-HARNESSP4-006
  - REQ-TELEM-HARNESSP4-007
  - REQ-TELEM-HARNESSP5-001
  - REQ-TELEM-HARNESSP5-005
  - REQ-LINT-HARNESSP5-003
  - REQ-TELEM-PIPELINEOBSERVABILITY-001
---

# Per-Dispatch Telemetry

## Context

The v5 harness renders every loop signal as ephemeral gate text — `RETURN:`,
`SCOPE:`, `CHUNK_VERDICT:`, `VERDICT:`, the fix/redo/replan counters — and then
forgets it. RS-008's two dogfooding probes (per-chunk dispatch cost, write-scope
false positives) therefore had to be hand-counted, and no dispatch has ever
been timed. RS-HARNESSP2-001 Q1 established that a transcript of those signals
can be recorded **without** creating a loop-position marker (REQ-ORCH-014) or a
project artifact (REQ-HARN-027), provided four conditions hold: the file lives
outside `docs/` and is gitignored; only the orchestrator writes it, after each
gate; nothing inside the loop reads it and it carries no resume field, guarded
by lint; and records hold counts, enums, shas and timestamps — never finding
text. REQ-HARN-027 was amended on 2026-09-17 to permit exactly that.

This spec defines the record, the writer, the non-interference proof and the
scope-check interaction. [Split 2026-09-19, harness-p5 — REQ-LINT-HARNESSP5-003:
the out-of-loop reader, the records-vs-expected implication, the schema lint,
the migration rewriter, the `--plan` floor, the fixture-based test contract, the
`\.sdd/` lint guard and the skill/lint change table now live in
`telemetry-reader.md`; §Moved Sections maps every relocated heading.
The two files are one topic — this one owns what the **writer** produces, the
other what a **post-cycle reader** derives from it.] It fulfils
REQ-TELEM-HARNESSP2-001..006 and -008 and the REQ-HARN-027 amendment
(REQ-TELEM-HARNESSP2-007 / -009, the skill changes of REQ-SKILL-HARNESSP2-001 /
-008 and the lint guard of REQ-LINT-HARNESSP2-002 are owned by
`telemetry-reader.md`). It **supersedes** the sentence "no `docs/reviews/`,
`.sdd/` or telemetry file is created" in `harness-loop-control.md`
§No-New-Artifact Invariant (recorded there as Q-IMPL-HARNESSP2-001); the
`docs/` invariant, the `docs/reviews/` prohibition and REQ-ORCH-004 stand.

Terminology follows `harness-loop-control.md`: a **dispatch** is one subagent
invocation; a **gate** is the operator decision that follows it. Every token
this spec introduces is defined here and nowhere else: the `TELEMETRY:` gate
line family and the `OUT .sdd/telemetry.jsonl (+k records, leaf write —
reverted)` finding string.
## Design

### Placement (REQ-TELEM-HARNESSP2-008, REQ-HARN-027 amendment)

| Property | Value | Why |
|---|---|---|
| Path | `<repo root>/.sdd/telemetry.jsonl` | outside `docs/`, so `git ls-files docs/` is unchanged — REQ-HARN-027's acceptance holds verbatim |
| Tracking | gitignored: `.sdd/` line in `.gitignore` (precedent `.superpowers/`) | not a project artifact; REQ-ORCH-004 (kickoff is the only new tracked artifact type) holds |
| Cardinality | **one file per repository**, all workstreams | a `docs/ws/<id>/telemetry*` file would become an owned execution artifact under `ws-layout.md`; records are attributed by `cycle.workstream` instead |
| Format | JSON Lines, one record per line, append-only | append is atomic enough for a single writer; no rewrite ever needed except the leaf-write revert below |
| Creation | the orchestrator creates `.sdd/` on first append | no setup step for the operator |
| `.gitignore` bootstrap | if `git check-ignore -q .sdd/telemetry.jsonl` exits non-zero, the orchestrator appends `.sdd/` to `.gitignore` as its own bookkeeping commit, outside any observed window (REQ-HARN-025), and renders `TELEMETRY: .gitignore updated` once at the next gate | the ignore line is the mechanism that keeps telemetry out of the porcelain snapshot and out of the repository |

**Why root-level and not `$TMPDIR` or `~/.claude/`**: the reader
(`tools/sdd-telemetry.py`) and the N = 3 pilot (`evaluation.md`) need the
records to survive the session and to sit beside the repository they describe;
a per-repo gitignored directory is the smallest thing that does both.

### Record Schema (REQ-TELEM-HARNESSP2-001, -002, -003)

One JSON object per line. `v` is the schema version: `1` for every record
written before harness-p4 and `2` for a record carrying the `[p4]` fields
(Q-IMPL-HARNESSP4-002 amends REQ-TELEM-HARNESSP2-001's literal `1` to the
admitted set `{1, 2}`).
Every value is a **count, enum, sha, boolean, null or ISO-8601 UTC timestamp**;
the record never contains a finding line, a path list, file content, reviewer
reasoning, or any other prose (REQ-ORCH-012/013). The key set is fixed; field
names are as below.

[Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-004] **This table is a
rendering of the domain table in `tools/sdd-telemetry.py`, which is the
schema's single source of truth**; `references/telemetry.md` §2 is the second
rendering. The tool's self-test parses this table and diffs it against the code
table (`telemetry-reader.md` §Schema Lint), so a row added here without a code row — or the reverse —
fails the self-test. Rows marked `[p4]` were added 2026-09-18 for harness-p4
(REQ-TELEM-HARNESSP4-002, -003, -006, -007) and are written with `v: 2`.
Of those four ids, **-006 and -007** are required by this file; **-002 and
-003** moved to `telemetry-reader.md` with the reader sections they govern
(§Moved Sections) and appear in that file's `requires:` — a backwards trace
from a `[p4]` row lands on the reader for those two.

| Group | Key | Type / domain | Source (gate signal) |
|---|---|---|---|
| — | `v` | int, `1` \| `2` — `2` for records carrying the `[p4]` fields; `1` records keep the pre-p4 key set; the per-`v` key set is the domain table filtered by its `[p4]` marks (Q-IMPL-HARNESSP4-002) | constant per writer version |
| — | `ts_dispatch` | timestamp | orchestrator clock, immediately before dispatch |
| — | `ts_return` | timestamp | orchestrator clock, on return, before `snapshot(after)` |
| — | `ts_gate` | timestamp | orchestrator clock, when the gate decision is taken |
| `cycle` | `workstream` | string id (`default` under marker `3`) | picker / argument |
| | `research_id` | `RS-…` id or null | kickoff `research_id` |
| | `kickoff_date` | date or null | kickoff `date` |
| | `marker` | `"3"` \| `"4"` | `docs/.sdd-version` |
| `dispatch` | `seq` | int, **1-based per session** — restarts at 1 in every new orchestrator session; cycle/run identity comes from `cycle.research_id`, never from `seq` | orchestrator session counter (never read back from the file) |
| | `kind` | `pipeline` \| `fix` \| `fanout_leaf` \| `verifier` \| `review` \| `red` | template used |
| | `stage` | `research` \| `requirements` \| `specs` \| `plan` \| `implement` \| `verify` \| `replan` | the stage **that was dispatched** (historical fact) |
| | `chunk` | int or null | `### Chunk N:` number for per-chunk dispatches |
| | `iteration` | int or null | fix-loop iteration this dispatch belongs to |
| | `redo` | int or null | per-chunk redo count at dispatch |
| | `reason` | repair-packet `reason` enum or null; its fix-only subset is the `const` row `FIX_ONLY_REASONS` below | `harness-return-contract.md` §Repair Packet; members, folded from Q-IMPL-HARNESSP4-005 (2026-09-19): `REVIEW`, `VERIFIER_FAIL`, `PARTIAL_CONTINUE`, `MERGE_CONFLICT`, `THIRD_OPINION` (`arbitrated-handoff.md`), `POST_MANUAL` (the `post-manual` review of `harness-loop-control.md` §Fix-Loop Cap §Footprint — added 2026-09-22, upper case, outside the fix-only subset) and `red_break` — the `RED_BREAK` packet of `adversarial-verify.md` as the record spells it and as the `const` row lists it, the one canonical spelling; uppercase `RED_BREAK` is **not** admitted (`--lint` `[enum]`) |
| `const` | `FIX_ONLY_REASONS` | subset of `dispatch.reason`: `red_break` `[p4]` — a **schema constant, not a record key**; no record carries it | §Implication-Derived `expected` clause (b); `--lint` asserts the subset relation |
| | `budget` | budget object (below) | parsed from the dispatched `Budget:` line |
| | `write_scope_n` | int | number of declared scope globs |
| `return` | `status` | `COMPLETE` \| `PARTIAL` \| `BLOCKED` \| `BUDGET_EXHAUSTED` \| `MALFORMED` | `RETURN.status`; `MALFORMED` when the block failed to parse |
| | `budget_consumed` | budget object + `self_reported: true` | `RETURN.budget_consumed` |
| | `files_written_n`, `commits_n`, `tasks_completed_n`, `failures_n`, `ledger_n`, `open_questions_n`, `blocked_writes_n` | int | lengths of the corresponding `RETURN` lists |
| | `warnings` | list of enums ⊆ {`KEYS_MISSING`, `MULTIPLE_STATUS`, `FOREIGN_TOKEN`, `RETURN_DRIFT` `[p4]`} | parser warnings (`return-contract.md` §1; `RETURN_DRIFT` = `harness-return-contract.md` §Return-Drift Warning) |
| `scope` | `token` | `CLEAN` \| `VIOLATION` \| null | `SCOPE:` line (null for a dispatch with no scope check) |
| | `in`, `advisory`, `out` | int | tag counts in the write-scope block |
| | `history_rewrite` | bool | `HISTORY_REWRITE` finding present |
| | `widened` | int, default 0 `[p4]` | globs the operator added to the dispatched scope beyond the stage's template default (§`scope.widened`) |
| `verdict` | `chunk_verdict` | `PASS` \| `FAIL` \| null | `CHUNK_VERDICT:` |
| | `review_verdict` | `APPROVE` \| `APPROVE_WITH_FIXES` \| `REJECT` \| null | `VERDICT:` |
| | `red_verdict` | `BROKEN` \| `HELD` \| null | `RED_VERDICT:` (`adversarial-verify.md`) |
| | `findings` | `{"C": int, "M": int, "m": int}` | counts of C/M/m lines |
| | `malformed` | bool | `REVIEW: MALFORMED` or `RETURN: MALFORMED` raised |
| | `contradiction_class` | null \| `b` \| `c` | `REVIEW: CONTRADICTION` class (`arbitrated-handoff.md`) |
| `gate` | `decision` | `proceed` \| `fix` \| `loop-back-to-fix` \| `stop` \| `redo` \| `replan` \| `revert` \| `widen` \| `accept` \| `third-opinion` \| `re-dispatch` \| `override` \| `manual_intervention` \| `malformed` \| `other` | the operator's choice, normalised to one enum (table below); `manual_intervention` and `malformed` added 2026-09-22 (`telemetry-reader.md` §Schema Lint, assertions (c) and (d)) |
| | `decision_by` | `operator` \| `policy` | always `operator` this cycle (`evaluation.md`) |
| | `fix_iteration`, `fix_cap`, `cap_raised` | int | `iteration N of MAX (cap raised ×k)` |
| | `redo_count` | int or null | `Redo: N of REDO_MAX` |
| | `replan_count`, `replan_cap` | int | derived replan re-entry count and cap |
| — | `replan_trigger` | enum or null | replan trigger class surfaced at this gate (`stuck`, `spike`, `verification`, `operator`) |
| `git` | `head_before`, `head_after` | short sha (`^[0-9a-f]{7,12}$`) | the snapshot pair's `HEAD_before` / `HEAD_after` (`dispatch-snapshot-base.md`) |
| `commit` | `token` | `COMPLETE` \| `INCOMPLETE` \| null `[p4]` | the `COMMIT:` closing line (`harness-commit-fidelity.md`); null for a dispatch whose gate commits nothing |
| | `missing_n`, `extra_n` | int `[p4]` | the `observed, not landed` / `landed, not observed` counts of that line |
| — | `migration` | optional `{from: chunk-string \| flat-cg, at: date, lost?: {<kind>: int}}` `[p4]` | present only on records rewritten by `migrate` (`telemetry-reader.md` §In-Place Migration); admitted by `--lint` on **every** `v` as an optional key (folded from Q-IMPL-HARNESSP4-006, 2026-09-19); `flat-cg` and `lost` — admitted only beside `flat-cg`, the per-kind count of a workstream's dropped flat records on its first migrated record — added 2026-09-22 (REQ-TELEM-PIPELINEOBSERVABILITY-002) |

**`const` rows** [Added 2026-09-18, harness-p4 specs review r1 — M3]: a row
whose `Group` cell is the literal `const` declares a **schema constant** —
`FIX_ONLY_REASONS` is the only one today. It is rendered as a real table row in
both renderings (here and `references/telemetry.md` §2), it names no record key
(`--lint` reports a record carrying a `const` name as `key-undeclared`), its
members are the backticked tokens of its `Type / domain` cell, and the
parse-and-diff self-test (`telemetry-reader.md` §Schema Lint) compares the set of `const` names and
each one's member set against the code table's constants — separately from the
`group.key` set, so the constant can never be mistaken for a key.

**`gate.decision` normalisation** — every gate option rendered anywhere in the
harness maps to exactly one enum value; an option not in this table is `other`
(no text is recorded):

| Gate option (as rendered) | `gate.decision` |
|---|---|
| `proceed` | `proceed` |
| `fix` (stage gate) · `accept round N+1 (fix)` | `fix` |
| `fix` (per-chunk gate — increments `Redo:`) | `redo` |
| `loop-back-to-fix` | `loop-back-to-fix` |
| `stop` | `stop` |
| `revert path` | `revert` |
| `accept & widen scope` | `widen` |
| `manual intervention` (the exhausted gate's option; the `post-manual` review of `harness-loop-control.md` §Fix-Loop Cap follows it with `reason: POST_MANUAL` — 2026-09-22) | `manual_intervention` |
| `authorize extra iteration` (recorded with `cap_raised`) | `override` |
| whichever option was chosen at a `REVIEW: MALFORMED` or `RETURN: MALFORMED` pause (2026-09-22) | `malformed` |
| `accept round N (proceed, note)` · `accept manually` · `accept (record)` | `accept` |
| `third opinion` | `third-opinion` |
| `re-dispatch` | `re-dispatch` |
| `route to sdd-replan` | `replan` |
| `amend` (the `COMMIT: INCOMPLETE` pause, `harness-commit-fidelity.md`) | `other` — decided at the specs gate 2026-09-18; the `commit` group already records the outcome |
| anything else | `other` |

**Resume-class keys are forbidden** (REQ-TELEM-HARNESSP2-003): no `next_stage`,
`resume`, `current_phase`, `pending`, `position` or equivalent. `dispatch.stage`
is what was dispatched, not what comes next; a reader cannot derive "where does
the loop resume" from any record, and the orchestrator never consults the file
on re-entry. A cycle (run) is identified by `cycle.research_id` — stamped on
every record — and a cycle boundary is a change of that id; readers order
records by `ts_dispatch` within a run and never rely on `dispatch.seq` being
monotonic across sessions.

**Budget object** (REQ-TELEM-HARNESSP2-002): `{"tool_calls": int|null,
"test_runs": int|null, "prototypes": bool, "read_only": bool}`. Parsing rules
for the dispatched `Budget:` line (`harness-loop-control.md` §Budget Slot
grammar):

| Fragment (case-insensitive) | Effect |
|---|---|
| `[~≤<=]?\s*(\d+)\s*tool calls?` | `tool_calls` = the integer |
| `[~≤<=]?\s*(\d+)\s*test runs?` | `test_runs` = the integer |
| `no prototypes` | `prototypes: false` (also the default) |
| `prototypes` without a preceding `no` | `prototypes: true` |
| `read[- ]only` | `read_only: true` (default false) |
| no fragment matched at all | the whole object is `{"unparsed": true}` — no text copied |

`return.budget_consumed` uses the same keys, taken from the `RETURN:` block's
`budget_consumed:` map, plus `"self_reported": true` — the harness exposes no
tool-call counter (REQ-HARN-005's recorded limitation), so the record labels
the self-report instead of pretending precision. A missing
`budget_consumed` yields `{"self_reported": true}` with no unit keys.

Example (a review dispatch with two Material findings):

```json
{"v":1,"ts_dispatch":"2026-09-17T21:40:03Z","ts_return":"2026-09-17T21:52:41Z","ts_gate":"2026-09-17T21:54:10Z",
 "cycle":{"workstream":"harness-p2","research_id":"RS-HARNESSP2-001","kickoff_date":"2026-09-17","marker":"4"},
 "dispatch":{"seq":2,"kind":"review","stage":"research","chunk":null,"iteration":null,"redo":null,"reason":null,
             "budget":{"tool_calls":15,"test_runs":null,"prototypes":false,"read_only":true},"write_scope_n":0},
 "return":{"status":"COMPLETE","budget_consumed":{"tool_calls":11,"test_runs":null,"self_reported":true},
           "files_written_n":0,"commits_n":0,"tasks_completed_n":0,"failures_n":0,"ledger_n":0,"open_questions_n":0,"blocked_writes_n":0,"warnings":[]},
 "scope":{"token":"CLEAN","in":0,"advisory":0,"out":0,"history_rewrite":false},
 "verdict":{"chunk_verdict":null,"review_verdict":"APPROVE_WITH_FIXES","red_verdict":null,"findings":{"C":0,"M":2,"m":3},"malformed":false,"contradiction_class":null},
 "gate":{"decision":"proceed","decision_by":"operator","fix_iteration":0,"fix_cap":3,"cap_raised":0,"redo_count":null,"replan_count":0,"replan_cap":3},
 "replan_trigger":null,"git":{"head_before":"8515816","head_after":"8515816"}}
```


[Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-001, -004] Two further
worked examples with a **non-null `chunk`** — the p3 mis-typing (`"Chunk 0"`
strings, `seq` 6–13) traces to the sole `"chunk":null` example above. A
**verifier** record for Chunk 3 (its own record, not a field on the chunk's
record):

```json
{"v":2,"ts_dispatch":"2026-09-19T10:02:00Z","ts_return":"2026-09-19T10:06:30Z","ts_gate":"2026-09-19T10:07:10Z",
 "cycle":{"workstream":"harness-p4","research_id":"RS-HARNESSP4-001","kickoff_date":"2026-09-18","marker":"4"},
 "dispatch":{"seq":9,"kind":"verifier","stage":"implement","chunk":3,"iteration":null,"redo":0,"reason":null,
             "budget":{"tool_calls":15,"test_runs":2,"prototypes":false,"read_only":true},"write_scope_n":0},
 "return":{"status":"COMPLETE","budget_consumed":{"tool_calls":9,"test_runs":2,"self_reported":true},
           "files_written_n":0,"commits_n":0,"tasks_completed_n":0,"failures_n":0,"ledger_n":0,"open_questions_n":0,"blocked_writes_n":0,"warnings":[]},
 "scope":{"token":"CLEAN","in":0,"advisory":0,"out":0,"history_rewrite":false,"widened":0},
 "verdict":{"chunk_verdict":"PASS","review_verdict":null,"red_verdict":null,"findings":{"C":0,"M":0,"m":1},"malformed":false,"contradiction_class":null},
 "gate":{"decision":"proceed","decision_by":"operator","fix_iteration":0,"fix_cap":3,"cap_raised":0,"redo_count":0,"replan_count":0,"replan_cap":3},
 "replan_trigger":null,"git":{"head_before":"a1b2c3d","head_after":"a1b2c3d"},
 "commit":{"token":null,"missing_n":0,"extra_n":0}}
```

A **fix** record — the redo of Chunk 2 after `CHUNK_VERDICT: FAIL` (`kind: fix`,
`redo: 1`, `reason: VERIFIER_FAIL`; the first attempt's `pipeline` record with
`redo: 0` and `gate.decision: redo` stays in the file):

```json
{"v":2,"ts_dispatch":"2026-09-19T09:20:00Z","ts_return":"2026-09-19T09:41:12Z","ts_gate":"2026-09-19T09:45:00Z",
 "cycle":{"workstream":"harness-p4","research_id":"RS-HARNESSP4-001","kickoff_date":"2026-09-18","marker":"4"},
 "dispatch":{"seq":7,"kind":"fix","stage":"implement","chunk":2,"iteration":null,"redo":1,"reason":"VERIFIER_FAIL",
             "budget":{"tool_calls":25,"test_runs":3,"prototypes":false,"read_only":false},"write_scope_n":4},
 "return":{"status":"COMPLETE","budget_consumed":{"tool_calls":18,"test_runs":2,"self_reported":true},
           "files_written_n":3,"commits_n":0,"tasks_completed_n":1,"failures_n":0,"ledger_n":2,"open_questions_n":0,"blocked_writes_n":0,"warnings":[]},
 "scope":{"token":"CLEAN","in":3,"advisory":0,"out":0,"history_rewrite":false,"widened":1},
 "verdict":{"chunk_verdict":"PASS","review_verdict":null,"red_verdict":null,"findings":{"C":0,"M":0,"m":0},"malformed":false,"contradiction_class":null},
 "gate":{"decision":"proceed","decision_by":"operator","fix_iteration":0,"fix_cap":3,"cap_raised":0,"redo_count":1,"replan_count":0,"replan_cap":3},
 "replan_trigger":null,"git":{"head_before":"a1b2c3d","head_after":"e4f5a6b"},
 "commit":{"token":"COMPLETE","missing_n":0,"extra_n":0}}
```

`scope.widened: 1` on the fix record says the operator added one glob to the
template default for that dispatch (§`scope.widened`); the verifier's
`commit.token: null` says its gate commits nothing (§`commit` Group).

**Why a transcript and not a log**: every value under `return`, `scope`,
`verdict` and `gate` is copied from what the gate already renders, so the record
can never expose more than the operator already saw — and because the gate
renders counts of findings alongside the verbatim lines, copying only the counts
keeps REQ-ORCH-012/013 intact by construction.

### Writer (REQ-TELEM-HARNESSP2-004)

Only `sdd-orchestrate` writes the file. Sequence per dispatch:

```
ts_dispatch := date -u          # before snapshot(before) and dispatch
… dispatch → await return …
ts_return   := date -u          # on return, before snapshot(after)
… scope check (incl. the third observation below) → verifier / red / review → gate …
ts_gate     := date -u          # when the operator's decision is taken
append one record                # AFTER the gate decision, so gate.decision is filled
```

Rules:

- **One append per dispatch**, after that dispatch's gate. A verifier, red or
  review dispatch is its own dispatch and gets its own record (its
  `gate.decision` is the stage/per-chunk gate decision it fed).
  [Amended 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-001] **One record per
  dispatch, for every kind the schema admits** — `pipeline`, `fix`,
  `fanout_leaf`, `verifier`, `review`, `red` — with `dispatch.kind` set to the
  kind **actually dispatched**. Concretely: (i) a chunk verifier gets a
  `verifier` record of its own; its `CHUNK_VERDICT:` is *also* copied onto the
  chunk's own record's `verdict.chunk_verdict` — **only when that record is a
  per-chunk dispatch (`dispatch.chunk != null`)** — which is the field the
  implication of `telemetry-reader.md` §Records-vs-Expected reads. A
  **stage-level `fix` record** (`iteration ≥ 1`, `redo: null`, `chunk: null` —
  the implement-stage `loop-back-to-fix` dispatch after the stage review) keeps
  `verdict.chunk_verdict: null`; its verifiers' verdicts live on their own
  `verifier` records. `dispatch.chunk` keeps its one meaning (the `### Chunk N:`
  number of a per-chunk dispatch): the writer never stamps a chunk on a
  stage-level fix, which may touch several chunks and whose verifiers may run
  under several. The `--lint` cross-field rule is unchanged and becomes true by
  construction — a `chunk_verdict` on a record whose `(stage, chunk)` has no
  verifier is always a writer defect [Amended 2026-09-19, harness-p5 —
  REQ-TELEM-HARNESSP5-001, Q-REQ-P5-B; p4 session 2 `seq` 21, 24, 27 carried a
  `chunk_verdict` with `chunk: null`, `docs/ws/harness-p4/verification.md`
  §Next Steps]; (ii) a fix dispatch — a stage
  `loop-back-to-fix`, a per-chunk `fix` (redo) or a `RED_BREAK` packet — gets a
  `fix` record, **never** a `pipeline` one; (iii) the first attempt of a redone
  chunk **keeps its record** when the redo is dispatched; the redo is a further
  `fix` record with `dispatch.redo` incremented and `dispatch.reason` set
  (`VERIFIER_FAIL`, `REVIEW`, …). The p3 file held zero `verifier` and zero
  `fix` records across eight verifiers and three redos, and its one fix at
  `seq` 18 was typed `pipeline` — the writer text above did not say where the
  verifier's record goes, so none was written.
- **`scope.widened` source** [Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-006]:
  `|dispatched write scope globs| − |template default globs for the stage|`,
  both held in session state at dispatch time (the filled `Write scope:` slot
  and the default table of `references/write-scope.md` §2); floor 0; no read
  of the telemetry file.
- **`commit` source** [Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-007]:
  the `COMMIT:` line the gate rendered for this dispatch, read from the
  orchestrator's own rendering state — the token and the two clause counts;
  `{null, 0, 0}` for a dispatch whose gate commits nothing. Because the append
  happens after the gate decision and the `COMMIT:` line is a post-decision
  closing line, the append is ordered **after** that line is rendered.
  The line recorded is the gate's **closing** `COMMIT:` line: an `amend`
  re-renders `COMPLETE` before the append, so an amended omission is recorded
  as `COMPLETE`, and only an `accept (note)` leaves `INCOMPLETE` on record.
  `summarize` therefore labels the per-session count
  `COMMIT: INCOMPLETE (accepted): N` (`telemetry-reader.md` §Records-vs-Expected),
  never the number of omissions rendered. A
  `commit.amended` field is **deferred** (Q-REQ-P5-E): it would change the
  `v: 2` key set with no evidence anyone needs the count [Amended 2026-09-19,
  harness-p5 — REQ-TELEM-HARNESSP5-005; p4 finding 5: `COMMIT: INCOMPLETE: 0`
  although one `INCOMPLETE` was forced live and amended].
- **Append-only.** The orchestrator never rewrites or truncates the file, with
  the **single exception** of the leaf-write revert in §Third Observation.
- **Never load-bearing.** On any write error (unwritable directory, disk full)
  the orchestrator renders `TELEMETRY: WRITE FAILED` as one line of the next
  gate's text and continues with the unchanged `proceed │ loop-back-to-fix │
  stop` options. No retry, no pause.
- **Default on; KICKOFF opt-out.** Telemetry is on for every orchestrated cycle
  unless the operator disables it at KICKOFF; when off, no record is written and
  the first gate shows `TELEMETRY: OFF` once. The choice is session state, not
  an artifact (it is not written to `kickoff.md`).
- **Write-only for the orchestrator.** `dispatch.seq` is a session-state
  counter starting at 1; the orchestrator performs **zero reads** of the file —
  not for position, not for the counter.
- **No leaf ever writes it.** No stage skill, review, verifier, fan-out leaf or
  red dispatch is instructed to write it and no dispatch template names the
  path; `.sdd/**` is never in any default or widened write scope
  (REQ-HARN-020), so a leaf write is `OUT` by construction.

**`TELEMETRY:` gate-line family** (defined here; rendered at most once each per
gate, immediately after the `iteration`/cap line, before the options):

| Line | When |
|---|---|
| `TELEMETRY: rec <n>` | the previous append succeeded; `<n>` counts successful appends this session [Amended 2026-09-18, REQ-TELEM-HARNESSP3-001 — see §Positive Gate Line] |
| `TELEMETRY: WRITE FAILED` | the previous append raised an error |
| `TELEMETRY: OFF` | first gate of a cycle in which the operator disabled telemetry |
| `TELEMETRY: .gitignore updated` | the orchestrator added the `.sdd/` ignore line |

[Amended 2026-09-18, REQ-TELEM-HARNESSP3-001] The family has **four** members;
every restatement of it — `skills/sdd-orchestrate/SKILL.md` §The gate and
`CLAUDE.md` §Driver ("`TELEMETRY: WRITE FAILED | OFF | .gitignore updated` are
its only gate lines", a sentence this amendment makes false) — must carry the
same four.

**The append is `telemetry.py append`, and it validates before it writes** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-TELEM-PIPELINEOBSERVABILITY-001; REQ-TELEM-HARNESSP2-004 as amended; the record of why is §Pipeline-Observability Amendment).

The "append one record" step of §Writer's sequence is performed by one
subcommand, `python3 plugins/sdd/tools/telemetry.py append [--file F]`, which
reads exactly one JSON value from stdin and, **before** writing, checks in
order:

| # | Check | On failure |
|---|---|---|
| 1 | the value parses as a JSON **object** | exit non-zero, nothing written |
| 2 | `v` is in the admitted set, through the shared `v` helper (REQ-TELEM-HARNESSP5-004) | exit non-zero, nothing written |
| 3 | `lint_records([record])` returns **zero** findings of the classes `enum`, `type`, `key-undeclared`, `key-missing` — the same domain table `--lint` and `summarize` read (`telemetry-reader.md` §Schema Lint) | exit non-zero, nothing written |

`cross-field` and `mistyped-fix` findings are **warnings** at append time
(printed to stderr, exit unaffected) because both need a sibling record the
single-record call cannot see. Exit 0 follows one successful append-only write
of exactly one line. The subcommand prints nothing that requires reading the
file — no line number, no count — so the zero-reads rule of §Writer holds by
construction and `<n>` stays the orchestrator's session counter.

Why validate in the writer rather than tolerate at the reader: a record the
summarizer would drop is a record the gate has claimed and nobody can read; the
whole value of `rec <n>` is that it asserts a readable append. Why not run
`--lint` over the file on each append: that would be a read of the file inside
the loop, which §Writer forbids.

### Third Observation and Leaf-Write Revert (REQ-TELEM-HARNESSP2-005)

`.sdd/` is gitignored, so a leaf write there is invisible to the porcelain
snapshot pair (`harness-write-scope.md` limitation (b)). The orchestrator
therefore takes a **third, telemetry-specific observation** beside the two
snapshots of REQ-HARN-021, in the same window (REQ-HARN-025 ordering — before
its own append):

```
before dispatch : n_before := line count of .sdd/telemetry.jsonl (0 if absent)
                  e_before := sorted entry list of .sdd/ (empty if absent)
on return       : n_after, e_after — taken with snapshot(after), before the orchestrator's append
```

Any delta is a leaf write and is rendered inside the write-scope block as a
boundary finding counted in `SCOPE: VIOLATION (N paths)`:

- `n_after > n_before` →
  **`OUT .sdd/telemetry.jsonl (+k records, leaf write — reverted)`** with
  `k = n_after − n_before`; the orchestrator truncates the file back to
  `n_before` lines (the single exception to the never-truncate rule) and never
  treats the removed lines as telemetry.
- `n_after < n_before`, or `e_after ≠ e_before` →
  `OUT .sdd/<entry> (leaf write — reverted)` per differing entry; the
  orchestrator removes entries the leaf added and, for a truncated telemetry
  file, notes `TELEMETRY: WRITE FAILED`-equivalent loss as `OUT
  .sdd/telemetry.jsonl (−k records, leaf write — unrecoverable)` (it cannot
  restore lines it did not keep).

These finding strings are defined **once**, here (mirrored verbatim in
`skills/sdd-orchestrate/references/telemetry.md`); `references/write-scope.md`
§3 (the third observation) and §5 (limitation (b)'s `.sdd/` exception) cite
this definition instead of restating it — they are the third allowlisted
`\.sdd/` location of `telemetry-reader.md` §Lint Guard. The revert happens before the gate, like the
chunk verifier's write revert (`harness-chunk-verifier.md`); the gate then
offers the normal `VIOLATION` options for any other `OUT` path.

### Non-Interference Proof (REQ-TELEM-HARNESSP2-003, -006)

A marker is something phase detection **reads**. The complete set of
phase-detection and staleness inputs, enumerated from every skill's §Phase
Detection block, is:

| Reader | Inputs (all under `docs/`) |
|---|---|
| all nine stage skills + orchestrate | `docs/.sdd-version` |
| research, requirements | `docs/research/RS-*/findings.md` `status`; `docs/research/index.md` |
| requirements, specs, plan, implement, verify, replan | `docs/requirements/index.md` + category files (`status`, `last_updated`); `docs/spec/*.md` (`status`, `last_updated`, `requires:`) |
| plan, implement, verify, replan, orchestrate | `docs/ws/<id>/plan.md` (task marks, `last_updated`, `traces to`); `docs/ws/<id>/plan-history/` (`-replan-` archives) |
| verify, replan, orchestrate | `docs/ws/<id>/verification.md` `status` (incl. `pending-red`, `adversarial-verify.md`) |
| orchestrate | `docs/ws/<id>/kickoff.md` (`research_id`, `date`) |
| verify Step 3b, review Step 2 | `docs/requirements/traceability.md`, `docs/ws/<id>/traceability.md` — coverage only, never position |

(Flat `docs/` equivalents under marker `3`.) `.sdd/` appears in no row and this
table is the contract: adding a reader of `.sdd/` to any skill is a change to
this spec, not an implementation detail. Consequences that must hold:

1. `rm -rf .sdd/` leaves every skill's detected phase, every staleness verdict
   and the orchestrator's position table byte-identical.
2. The record carries no resume-class key (§Record Schema), so even a reader
   that violated rule 1 could not answer "where am I".
3. The lint guard below makes rule 1 mechanical.

`tools/sdd-gc.py` (`drift-sweep.md`) and `tools/sdd-telemetry.py` are
out-of-loop tools, not skills; gc never reads `.sdd/` either.

### Moved Sections — Reader, Lint and Fixture Contracts (REQ-LINT-HARNESSP5-003)

[Added 2026-09-19, harness-p5 — REQ-LINT-HARNESSP5-003; Q-REQ-P5-G. The file
stood at 1137 lines; the split is by **who acts** — writer-side contracts stay
here, everything a post-cycle reader or the operator's tools derive from the
file moves. Every `## Implementation Questions` entry moved with the section it
amends, append-only and unrenumbered; the `| Group | Key | Type / domain |`
table that `tools/sdd-telemetry.py` `test_schema_table_agrees` parses stays in
this file under §Record Schema, so the tool's path constant is unchanged. The
split landed at 748 / 697 lines; REQ-LINT-HARNESSP5-003's guide was amended to
~800 lines per file at the specs gate (Q-REQ-P5-I, 2026-09-19) rather than
cutting further, because the schema's three worked examples and the writer
rules are one contract — see §Open Questions 5.]

A `docs/spec/telemetry.md §<heading>` pointer to one of these headings — in
`docs/requirements/functional/telemetry.md`, `tools/sdd-telemetry.py`'s
docstring, `references/telemetry.md` or a traceability `Spec` cell — resolves
through this table until the pointer is re-aimed at `telemetry-reader.md` (the
tool and skill pointers are re-aimed at implement; the requirements corpus is
never edited for a spec split).

For a `Spec` cell in a **closed** workstream's traceability file
(`docs/ws/harness-p2|p3|p4/traceability.md`), this table is the **permanent**
resolution path, not a stopgap: those files are owned by workstreams that have
shipped and are never rewritten (a workstream owns its own rows —
`ws-traceability.md`), so no later cycle re-aims their pointers. The table is
therefore retained indefinitely and is the contract that keeps those cells
resolvable:

| Heading (was here) | Now in `telemetry-reader.md` |
|---|---|
| §Out-of-Loop Reader (REQ-TELEM-HARNESSP2-009) | §Out-of-Loop Reader |
| §Scorer Derivation | §Scorer Derivation |
| §Records-vs-Expected in `summarize` (REQ-TELEM-HARNESSP3-002) and §Implication-Derived `expected` and the Headline (REQ-TELEM-HARNESSP4-002, -003) | same headings |
| §Schema Lint — `--lint` From One Domain Table (REQ-TELEM-HARNESSP4-004) | §Schema Lint |
| §In-Place Migration of the 8 p3 Records, Stamped Partial (REQ-TELEM-HARNESSP4-005) | §In-Place Migration |
| §`--plan` Floor for Implement-Stage Expectations (REQ-TELEM-HARNESSP4-008) | §`--plan` Floor |
| §Fixture-Based Test Contract | §Fixture-Based Test Contract |
| §Lint Guard (REQ-TELEM-HARNESSP2-007, REQ-LINT-HARNESSP2-002) | §Lint Guard |
| §Skill and Lint Changes (REQ-SKILL-HARNESSP2-001, -008; REQ-LINT-HARNESSP2-002) | §Skill and Lint Changes |
| Q-IMPL-HARNESSP2-070, -071, Q-IMPL-HARNESSP3-006, -018, Q-IMPL-HARNESSP4-004, -005, -006, -007 | its `## Implementation Questions` |

### Positive Gate Line `TELEMETRY: rec <n>` (REQ-TELEM-HARNESSP3-001)

[Changed 2026-09-18: the `TELEMETRY:` gate-line family had no member for "on,
and the append happened". Spec-read, with a direct negative observation — on
2026-09-18 the gate rendered telemetry as on, nothing was ever appended, and the
text actually rendered (`TELEMETRY: on (record written after your decision)`)
was not a member of the family §3 defines.]

The family becomes `rec <n> | WRITE FAILED | OFF | .gitignore updated`:

```
TELEMETRY: rec <n>     # rendered on the gate AFTER an append; <n> counts SUCCESSFUL appends this session
```

Contract:

- `<n>` **counts successful appends in this session**. It is **not**
  `dispatch.seq`. The two diverge whenever a dispatch produces no append (a
  `WRITE FAILED`, or a mid-cycle opt-out), and where they diverge the **append
  count wins** — the line exists to assert that the append happened, so binding
  `<n>` to the dispatch sequence would have a later gate assert an append count
  that never occurred, weakening exactly the assurance the line provides.
- `<n>` is a new **session-scoped counter**, incremented **only** on a
  successful append, maintained beside `dispatch.seq` in the orchestrator's
  existing session state (§3). No new artifact.
- It is still **never a read of the telemetry file**: the write-only rule
  (REQ-TELEM-HARNESSP2-004, "the orchestrator performs zero reads of the file")
  is preserved intact, and the line is text, so §5's non-interference proof is
  untouched.
- Position: the writer sequence already appends *after* the gate decision, so
  the **next** gate is where the previous append is asserted.
- An operator who sees a gate carrying no `rec` line, no `OFF` line and no
  `WRITE FAILED` line knows the append did not happen.

Known residual: no spec read establishes whether an operator actually notices an
absent line — which is what REQ-TELEM-HARNESSP3-002 backstops.

**Consequences for the gate line** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-TELEM-HARNESSP3-001 as amended; REQ-TELEM-HARNESSP2-004 as amended; the record of why is §Pipeline-Observability Amendment).

- **`rec <n>` counts validated writes.** `<n>` is incremented only when
  `append` exits 0 (REQ-TELEM-HARNESSP3-001 as amended). A non-zero exit — I/O
  failure **or** validation failure — renders `TELEMETRY: WRITE FAILED` and does
  not advance `<n>` (REQ-TELEM-HARNESSP2-004 as amended: validation failure is
  the second cause of `WRITE FAILED`). The loop continues; telemetry is still
  never load-bearing.
- The `TELEMETRY:` family stays at **four** members. No dispatch template names
  the subcommand: the orchestrator is its only caller, and a leaf that ran it
  would still be an `OUT` write (§Third Observation).
- `skills/orchestrate/references/telemetry.md` §3's writer sequence names
  `append`'s exit code as the condition for `rec <n>`; its gate-line table is
  unchanged in membership.

### `scope.widened` (REQ-TELEM-HARNESSP4-006)

[Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-006; `docs/ws/harness-p3/verification.md` §L6]

`scope.widened` (int, default 0) is the number of globs the operator added to
the dispatched write scope beyond the stage's template default — a count, never
the glob text (REQ-TELEM-HARNESSP2-002). Source: §Writer. `summarize` prints
the number of widened dispatches per session (`widened dispatches: N`). Why:
fixing R1 in p3 required widening the verify scope to `tools/` and `skills/`;
the check read those paths `IN` and `SCOPE: CLEAN` looked identical to an
unwidened stage, so nothing durable recorded that a widening happened.

### `commit` Group (REQ-TELEM-HARNESSP4-007)

[Added 2026-09-18, harness-p4 — REQ-TELEM-HARNESSP4-007; RS-HARNESSP4-001 §Q1 cost table]

`commit: {token: COMPLETE | INCOMPLETE | null, missing_n: int, extra_n: int}` is
the post-cycle trace of the `COMMIT:` signal (`harness-commit-fidelity.md`) for
the dispatch the record describes: `missing_n` = the `observed, not landed`
count, `extra_n` = the `landed, not observed` count; `{null, 0, 0}` for a
dispatch whose gate does not commit (review, verifier, red). Only the token and
the two counts are recorded, never paths. **Telemetry remains non-load-bearing**:
`COMMIT:` is rendered from git and the record copies the rendering; nothing
reads the record to render the line. `summarize` prints per-session
`COMMIT: INCOMPLETE (accepted)` counts — the token is the gate's **closing**
line (§Writer, REQ-TELEM-HARNESSP5-005). Because two record groups are added this cycle,
records that carry them are written with **`v: 2`**; `v: 1` records (every
record before this cycle, including the frozen fixture) remain valid against
the `v: 1` key set, so `--lint` does not report `key-missing` for `scope.widened`
or `commit` on them. Both versions are admitted by the domain table, by
`summarize` and by `--lint` — the bump is a schema decision recorded as
Q-IMPL-HARNESSP4-002, not prose: the shipped reader's `v != SCHEMA_V` skip
would otherwise drop every live p4 record from `summarize` at DONE
[Amended 2026-09-18, harness-p4 specs review r1 — M1].

## Verification

### Automated

- `test_record_key_set_matches_schema`: a record produced from a fixture gate
  has exactly the top-level keys `v, ts_dispatch, ts_return, ts_gate, cycle,
  dispatch, return, scope, verdict, gate, replan_trigger, git` and no
  resume-class key.
- `test_review_with_two_material_findings_counts_only`:
  `verdict.findings.M == 2`; no string value longer than 12 characters other
  than timestamps and ids; `grep -c '"C1' .sdd/telemetry.jsonl` is 0.
- `test_budget_line_parses_to_units`: `Budget: ~70 tool calls, no prototypes`
  → `{"tool_calls": 70, "test_runs": null, "prototypes": false, "read_only":
  false}`; `Budget: ≤ 25 tool calls, ≤ 3 test runs, read-only` → `{25, 3,
  false, true}`; `Budget: whatever fits` → `{"unparsed": true}`; no record
  contains the substring `tool calls`.
- `test_budget_consumed_is_labelled_self_reported`.
- `test_one_record_per_gated_dispatch`: after N gated dispatches the file has
  N more lines, each with non-null `gate.decision`.
- `test_write_failure_is_one_gate_line`: an unwritable `.sdd/` yields
  `TELEMETRY: WRITE FAILED` at the next gate and unchanged options.
- `test_gitignore_bootstrap_once`: missing ignore line → line appended,
  `TELEMETRY: .gitignore updated` rendered once, `git check-ignore
  .sdd/telemetry.jsonl` exits 0.
- `test_leaf_append_is_out_and_reverted` (scope self-test F7): line count after
  revert equals the before-count; the finding string matches exactly.
- `test_delete_sdd_leaves_phase_detection_identical`: position table and each
  skill's detection output before and after `rm -rf .sdd/` are byte-identical.
- `test_no_ws_telemetry_path`: no `docs/ws/*/telemetry*` path exists after a
  cycle.
- `test_stage_level_fix_has_null_chunk_verdict`: a walkthrough of an
  implement-stage `loop-back-to-fix` (`chunk: null`, `iteration: 1`) whose two
  chunk verifiers both return `PASS` appends a `fix` record with
  `verdict.chunk_verdict: null` and two `verifier` records carrying `PASS`; a
  per-chunk redo (`chunk: 2`) still copies the verdict onto its own record
  (REQ-TELEM-HARNESSP5-001).
- `test_commit_group_records_closing_line`: a gate that renders
  `COMMIT: INCOMPLETE`, is amended and re-renders `COMPLETE` appends
  `commit.token: COMPLETE`; the same gate resolved `accept (note)` appends
  `INCOMPLETE` (REQ-TELEM-HARNESSP5-005).

### Manual

- Run one orchestrated stage with telemetry on; open the gate text and confirm
  the record's counts equal what the gate rendered.

### Acceptance Criteria

- [ ] Record key set, value domains and counts-not-text rule as in §Record Schema; `dispatch.seq` 1-based per session with zero orchestrator reads of the file; run identity = `cycle.research_id`; `gate.decision` normalisation table incl. `other`; no resume-class key (REQ-TELEM-HARNESSP2-001, -003)
- [ ] `dispatch.budget` and `return.budget_consumed` are enumerated units; `self_reported: true`; unparsable → `{"unparsed": true}` (REQ-TELEM-HARNESSP2-002)
- [ ] Orchestrator-only, one append after each gate, never truncated except the leaf-write revert; `TELEMETRY: rec <n> | WRITE FAILED | OFF | .gitignore updated` lines; default on with KICKOFF opt-out; one file per repository (REQ-TELEM-HARNESSP2-004)
- [ ] Third observation (line count + entry list) and the `OUT .sdd/telemetry.jsonl (+k records, leaf write — reverted)` string defined once; revert to before-count; scope self-test scenario F7 (REQ-TELEM-HARNESSP2-005)
- [ ] Phase-detection input table as in §Non-Interference Proof; `rm -rf .sdd/` is behaviour-neutral (REQ-TELEM-HARNESSP2-006)
- [ ] `.sdd/` gitignored at the repo root; `git ls-files docs/` unchanged by a cycle (REQ-TELEM-HARNESSP2-008, REQ-HARN-027)
- [ ] `python3 tools/sdd-skill-lint.py` exits 0; `--self-test` exits 0
- [ ] §3's gate-line table lists `rec <n>` and the writer sequence names the gate that renders it; `skills/sdd-orchestrate/SKILL.md` §The gate states it in one line (REQ-TELEM-HARNESSP3-001)
- [ ] A walkthrough of two gated dispatches with telemetry on renders `TELEMETRY: rec 1` then `TELEMETRY: rec 2` (REQ-TELEM-HARNESSP3-001)
- [ ] Every restatement of the `TELEMETRY:` family — `skills/sdd-orchestrate/SKILL.md` §The gate and `CLAUDE.md` §Driver — lists all four members, `rec <n>` included (REQ-TELEM-HARNESSP3-001)
- [ ] A walkthrough with telemetry on but the file unwritable renders `TELEMETRY: WRITE FAILED` and **no** `rec` line (REQ-TELEM-HARNESSP3-001)
- [ ] A resumption walkthrough of three gated dispatches whose second append fails renders `rec 1`, `WRITE FAILED`, `rec 2` — **not** `rec 3`; the same holds after a mid-cycle opt-out, whose `OFF` gates append nothing and do not advance `<n>` (REQ-TELEM-HARNESSP3-001)
- [ ] `grep` for a telemetry-file read in the orchestrator's gate path returns nothing (REQ-TELEM-HARNESSP3-001, REQ-TELEM-HARNESSP2-004)
- [ ] §Writer names every kind and states the one-record-per-dispatch rule with the verifier / fix / redo-first-attempt clauses; `references/telemetry.md` §2 states the same with worked `verifier` and `fix` examples (non-null `chunk`); this cycle's live file summarised at DONE shows `verifier` count = chunk verifiers dispatched and `fix` count = fix dispatches rendered, with `implied vs recorded` reporting 0 missing for both kinds in this cycle's session (REQ-TELEM-HARNESSP4-001)
- [ ] The domain table declares `scope.widened` int default 0; §Record Schema and `references/telemetry.md` §2 render it; `summarize` prints widened dispatches per session; a fixture with `scope.widened: 2` is in-domain and a string value is a `--lint` finding; §Writer names the source without any telemetry-file read (REQ-TELEM-HARNESSP4-006)
- [ ] The domain table declares the `commit` group; both telemetry documents render it; `summarize` prints per-session `COMMIT: INCOMPLETE` counts; `{INCOMPLETE, 1, 0}` passes `--lint` and `token: DROPPED` fails it; `grep -n 'commit' skills/sdd-orchestrate/references/loop-control.md` shows the gate reading git, not telemetry; records carrying the group are `v: 2` and `v: 1` records lint clean against the `v: 1` key set (REQ-TELEM-HARNESSP4-007)
- [ ] `summarize` and `--lint` read `v: 2` records: a fixture mixing `v: 1` and `v: 2` records is summarised with `skipped: 0`; the shipped `v != SCHEMA_V` skip in `tools/sdd-telemetry.py` is replaced by membership in the admitted set `{1, 2}`; the per-`v` key sets are derived from the domain table's `[p4]` marks, not from a second constant; a record with `v: 3` is still skipped and counted (unknown-`v` tolerance) (REQ-TELEM-HARNESSP2-001, REQ-TELEM-HARNESSP2-009, REQ-TELEM-HARNESSP4-004, REQ-TELEM-HARNESSP4-007; Q-IMPL-HARNESSP4-002)
- [ ] §Writer rule (i) states the per-chunk-only condition (`dispatch.chunk != null`) for copying `CHUNK_VERDICT:` onto the dispatched record and that a stage-level `fix` record keeps `chunk_verdict: null`; `references/telemetry.md` §3 and `skills/sdd-orchestrate/SKILL.md` §Telemetry agree; on the frozen p4 fixture `--lint` still lists the three records as `[cross-field]` findings by seq (`telemetry-reader.md` §Fixture-Based Test Contract); `python3 tools/sdd-skill-lint.py` exits 0 (REQ-TELEM-HARNESSP5-001)
- [ ] §Writer states that the `commit` source records the gate's **closing** `COMMIT:` line (`amend` → `COMPLETE`, `accept (note)` → `INCOMPLETE`); `references/telemetry.md` §3 agrees; `summarize` on the frozen p4 fixture prints `COMMIT: INCOMPLETE (accepted): 0`; `test_schema_table_agrees` still passes (no key added; `commit.amended` deferred, Q-REQ-P5-E) (REQ-TELEM-HARNESSP5-005)
- [ ] `wc -l docs/spec/telemetry*.md` shows no file over ~800 lines (the bound amended at the specs gate 2026-09-19, Q-REQ-P5-I — the split landed at 748 / 697 and is not cut further); the `| Group | Key | Type / domain |` table stays under §Record Schema of this file and `test_schema_table_agrees` passes; every moved section is listed in §Moved Sections; the Q-IMPL-HARNESSP4-004..009 fold-in status notes count six across `telemetry-reader.md`, `skill-lint-v5.md` and `harness-chunk-verifier.md` (REQ-QIMPL-HARNESSP5-001's grep, owned by `deviation-protocol.md`); `python3 tools/sdd-gc.py --report` raises no `qimpl-broken-ref` or broken-link finding on either file (REQ-LINT-HARNESSP5-003)

**Pipeline-observability (2026-09-22, telemetry writer)**

- [ ] `python3 plugins/sdd/tools/telemetry.py --help` names `append` — the word
  occurs at least once in the output (it occurs 0 times before this delta)
  (REQ-TELEM-PIPELINEOBSERVABILITY-001).
- [ ] `python3 plugins/sdd/tools/telemetry.py --self-test` exits 0 and names
  three `append` cases: a `v`-less object (`{"ts":"x","ws":"x"}`) exits
  non-zero and the target file's line count is unchanged; a non-object (`[]`)
  exits non-zero and writes nothing; the `skills/orchestrate/references/telemetry.md` §2 example
  record exits 0, adds exactly one line, and `summarize --file <that file>`
  counts 1 record. **Reversion witness**: in a temp copy of the tool with the
  validation step removed, the first case exits 0 and the self-test prints its
  failure (REQ-TELEM-PIPELINEOBSERVABILITY-001).
- [ ] The gate-line table in `skills/orchestrate/references/telemetry.md` §3
  lists exactly four `TELEMETRY:` members (`rec <n>`, `WRITE FAILED`, `OFF`,
  `.gitignore updated`), and the writer sequence in the same section states
  that `rec <n>` is rendered only on `append`'s exit 0 —
  `grep -c '^| .TELEMETRY: ' plugins/sdd/skills/orchestrate/references/telemetry.md`
  reads 4 and
  `sed -n '/^## 3\./,/^## 4\./p' plugins/sdd/skills/orchestrate/references/telemetry.md | grep -c 'append'`
  reads ≥ 1; `skills/orchestrate/SKILL.md` §The gate still names the same
  four — `grep -c 'rec <n>' plugins/sdd/skills/orchestrate/SKILL.md` and
  `grep -c '.gitignore updated' plugins/sdd/skills/orchestrate/SKILL.md` each
  read ≥ 1 (REQ-TELEM-HARNESSP2-004, -HARNESSP3-001 as amended).
- [ ] The orchestrator's gate path performs no read of the telemetry file: the
  fenced writer sequence of `skills/orchestrate/references/telemetry.md` §3 and
  `skills/orchestrate/SKILL.md` §The gate contain no `summarize`, `--lint`,
  `tail`, `wc` or `cat` invocation over the telemetry path —
  `sed -n '/^## 3\./,/^## 4\./p' plugins/sdd/skills/orchestrate/references/telemetry.md | grep -Ec '(summarize|--lint|tail|wc|cat).*telemetry\.jsonl'`
  reads 0, and the same pipeline with §The gate of
  `plugins/sdd/skills/orchestrate/SKILL.md` (its heading to the next heading of
  the same level) as the `sed` range reads 0
  (REQ-TELEM-PIPELINEOBSERVABILITY-001).
- [ ] `grep -rn 'telemetry.py append' plugins/sdd/skills/orchestrate/references/dispatch-templates.md plugins/sdd/skills/orchestrate/references/fan-out.md`
  returns nothing — no dispatch template mentions the subcommand
  (REQ-TELEM-PIPELINEOBSERVABILITY-001).

## Edge Cases

- **Two orchestrator sessions on the same repository** (two workstreams,
  marker `4`): both append to one file; JSON Lines appends of one line each do
  not interleave within a line on POSIX filesystems for records under the pipe
  buffer size; if a torn line ever occurs, `summarize` counts it as skipped.
  No locking is added (Open Question 1).
- **Dispatch with no gate** (operator aborts the session mid-dispatch): no
  record is written; the next session's `seq` restarts at 1, as it does on
  **every** new session — `seq` is per session, not per cycle; the run is still
  identified by `cycle.research_id` and ordered by `ts_dispatch`.
- **Telemetry disabled mid-cycle**: not offered; the KICKOFF choice holds for
  the cycle.
- **Leaf deletes `.sdd/`**: `e_after` is empty → `OUT .sdd/telemetry.jsonl (−k
  records, leaf write — unrecoverable)`; the orchestrator recreates the
  directory on its next append.
- **Marker `3` repositories**: identical behaviour; `cycle.workstream` is
  `default`, `cycle.marker` is `"3"`.
- **Red or verifier dispatch with no scope violation and no verdict of its
  own kind**: null fields are written as `null`, never omitted — the key set is
  constant.

## Cross-Spec Consistency (XSPEC)

- `harness-loop-control.md` §No-New-Artifact Invariant's "no `.sdd/` or
  telemetry file" sentence is **superseded** by §Placement under the
  REQ-HARN-027 amendment; recorded as Q-IMPL-HARNESSP2-001 there. Its table of
  mechanisms is otherwise unchanged.
- `harness-write-scope.md` §Observation (two snapshots) is extended by the
  third observation; §Recorded v1 Limitations (b) gains the `.sdd/` exception
  — recorded as Q-IMPL-HARNESSP2-002 there; `SCOPE: VIOLATION (N paths)`
  counting (`OUT` + `HISTORY_REWRITE`) is reused, the `.sdd/` finding is one
  more `OUT`.
- `harness-return-contract.md` §RETURN Block field names map 1:1 onto
  `return.*_n` counts; `status` values match plus `MALFORMED` for a failed
  parse.
- `orchestration.md` §Resume and Phase Detection (no marker file) — satisfied
  by §Non-Interference Proof; REQ-ORCH-014 holds by mechanism.
- `ws-layout.md`: no `docs/ws/<id>/` entry is created — one root file per
  repository, attributed by `cycle.workstream`.
- `skill-lint-v5.md` `FORBIDDEN` row shape (`pattern`, `files`, `allow`,
  `reason`, `fix`) is extended by `allow_files`; existing rows are unaffected.
- `evaluation.md` §Scorer Fields ↔ §Scorer Derivation: every field derivable.
- `adversarial-verify.md` `red_verdict`, `arbitrated-handoff.md`
  `contradiction_class`, `dispatch-snapshot-base.md` `git.head_before` are
  consumed here with the same names.
- `docs/ws/harness-p2/traceability.md` row `REQ-HARN-027 | telemetry.md` is
  an **amendment-only row**. Rule: a per-ws row whose Spec differs from the
  legacy row for the same id (`docs/requirements/traceability.md`
  `REQ-HARN-027 | harness-loop-control.md`, Verified `pass`) is an amendment
  row. Its Test and Implementation cells point to the amendment evidence
  (`.sdd/` gitignored, `git ls-files docs/` unchanged by a cycle); its Verified
  cell **inherits the legacy row's `pass`** and is never read as a gap by gc
  `trace-empty` (`drift-sweep.md` sweep 11) or `sdd-verify` Step 3b. The
  aggregate keeps both rows (`ws-traceability.md` regeneration is row-preserving).
- **No unresolved contradictions.**

**harness-p3 pass (2026-09-18).** No extractable type definitions in
telemetry.md beyond the JSON record schema, which is unchanged by this
amendment. Token checks: the `TELEMETRY:` family is defined here and restated in
`skills/sdd-orchestrate/SKILL.md` §The gate **and** `CLAUDE.md` §Driver, whose
sentence "`TELEMETRY: WRITE FAILED | OFF | .gitignore updated` are its only gate
lines" this amendment falsifies — all three must carry the same four members
after this change. `dispatch.seq` keeps its existing meaning and is
explicitly **not** the source of `<n>`.
- [Added 2026-09-18, harness-p4] `commit.token`'s domain `COMPLETE | INCOMPLETE |
  null` equals the two-member family of `harness-commit-fidelity.md`;
  `return.warnings` member `RETURN_DRIFT` is the warning of
  `harness-return-contract.md` §Return-Drift Warning; `FIX_ONLY_REASONS =
  {red_break}` is the `RED_BREAK` packet reason of `adversarial-verify.md`
  lower-cased as the existing `dispatch.reason` enum does — consistent.
- [Added 2026-09-19, harness-p5] `telemetry-reader.md` consumes `dispatch.chunk`,
  `verdict.chunk_verdict`, `commit.token` and `v` with the meanings fixed here;
  the writer rule (i) per-chunk-only condition and the reader's chunk-group-only
  `implied.pipeline` (REQ-TELEM-HARNESSP5-001/-002) are the two halves of one
  decision (Q-REQ-P5-B) and name the same `(stage, chunk)` group; `COMMIT:
  INCOMPLETE (accepted)` is the closing-line reading of
  `harness-commit-fidelity.md` §Placement (`amend` re-renders `COMPLETE`).

**harness-p5 pass (2026-09-19).** No extractable type definitions beyond the
JSON record schema, whose key set is unchanged by this cycle (no `commit.amended`).
The split introduced no second definition: every token (`TELEMETRY:` family, the
`OUT .sdd/…` strings, the record schema) is defined in exactly one of the two
files and the other cites it.

## Open Questions

1. **File locking for concurrent sessions.** Default: none; torn lines are
   skipped by the reader and counted.
2. **`gate.decision` enum completeness** as new gate options appear. Default:
   the normalisation table above; an unrecognised option is recorded as
   `other` with no text, and adding a row to the table is a change to this spec.
3. **Should `ts_*` be stamped with sub-second precision?** Default: whole
   seconds (`date -u +%Y-%m-%dT%H:%M:%SZ`); dispatch wall times are minutes.
4. **Re-aiming the tool and skill pointers after the split.** `tools/sdd-telemetry.py`
   (docstring) and `references/telemetry.md` §2/§7 still say `docs/spec/telemetry.md`
   for sections now in `telemetry-reader.md`. Default: re-aim them in the
   implement chunk that touches each file (they are outside the specs write
   scope); §Moved Sections resolves them meanwhile.
5. ~~**Residual size.**~~ **Resolved 2026-09-19 (Q-REQ-P5-I).** The question
   was whether the post-split sizes (748 / 697) should force a further cut
   against REQ-LINT-HARNESSP5-003's original ~600-line guide. The operator
   amended the bound to ~800 lines per file instead; both files are inside it
   and both §Acceptance Criteria state the amended number. Revisit only if
   `sdd-skill-lint.py` ever sizes specs.

## Implementation Questions

### Q-IMPL-HARNESSP2-010: `SCOPE: VIOLATION (1 path)` singular vs the spec's `(1 paths)` literal
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Third Observation (F7 expected line)
**Decision**: the shipped renderer pluralises (`1 path`, `2 paths`) as `write-scope.md` §5 and scenarios F1/F2/F6 already do; F7 asserts `SCOPE: VIOLATION (1 path)`. The `OUT .sdd/telemetry.jsonl (+1 records, leaf write — reverted)` string is byte-exact. The spec's `(N paths)` is read as a template.
**Rationale**: consistency with the v5 renderer; no contract value depends on the plural form.
**Date**: 2026-09-17 (Chunk 0)

### Q-IMPL-HARNESSP3-005: The append counter is session state named `telemetry.rec`
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Positive Gate Line
**Decision**:

`<n>` lives beside `dispatch.seq` in the orchestrator's session state under the
key `telemetry.rec`, initialised to 0 at KICKOFF and incremented only after a
successful append returns. On resumption in a new session it restarts at 0 —
consistent with "counts successful appends **this session**" — so a resumed
cycle's first `rec` line reads `rec 1` and is not a claim about earlier
sessions.
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP4-002: the schema version `v` becomes the admitted set `{1, 2}`
**Tier**: 2 (spec ambiguity — requirement literal amended)
**Spec reference**: §Record Schema, §`commit` Group; `telemetry-reader.md` section Schema Lint
**Decision**:

REQ-TELEM-HARNESSP2-001 fixes `v` as the integer `1`, and the shipped reader
skips any record whose `v` differs from its single `SCHEMA_V` constant. This
cycle adds two record groups (`scope.widened`, `commit`) and writes records
carrying them with `v: 2` (decided at the specs gate 2026-09-18, kept). The
literal is amended to the **admitted set `{1, 2}`**: the writer stamps `2`;
`summarize` and `--lint` accept both members; the key set a record is validated
against is the domain table filtered by `[p4]` marks (`v: 1` → unmarked rows
only, `v: 2` → all rows), so there is no second constant to drift; a `v`
outside the set is skipped and counted exactly as before (REQ-TELEM-HARNESSP2-009's
unknown-`v` tolerance). The frozen p3 fixture stays `v: 1` and lints clean
against the `v: 1` key set. Resolves review finding M1 (the bump was prose only
and `summarize` at DONE would have skipped every live p4 record).
**Date**: 2026-09-18 (specs stage, review round 1)


## Pipeline-Observability Amendment (2026-09-22, REQ-TELEM-PIPELINEOBSERVABILITY-001; REQ-TELEM-HARNESSP2-004, REQ-TELEM-HARNESSP3-001 amended)

[Added 2026-09-22, workstream `pipeline-observability` —
RS-PIPELINEOBSERVABILITY-001 §Q1, R1. Observed defect: the consumer-geometry
cycle's gates rendered `TELEMETRY: rec 39`, the file gained 53 records, and
`summarize` read 0 of them, because the writer never applied the schema the
reader enforces.]

**Where the contract lives** (REQ-REQ-PIPELINEOBSERVABILITY-001 (b), 2026-09-22): this section is the record of *why* and states no contract of its own; the contract is in the sections of record named here, each edited in place under a `[Updated: 2026-09-22]` marker, and its acceptance criteria sit in this spec's own Acceptance Criteria section under the same date. §Writer carries the `append` subcommand and its validate-before-write table (REQ-TELEM-PIPELINEOBSERVABILITY-001, REQ-TELEM-HARNESSP2-004 as amended); §Positive Gate Line `TELEMETRY: rec <n>` carries what a counted append is (REQ-TELEM-HARNESSP3-001 as amended). Left consistent and not reopened: §Placement, §Record Schema, §Third Observation and Leaf-Write Revert, §Non-Interference Proof, §`scope.widened`, §`commit` Group, and `telemetry-reader.md` §Out-of-Loop Reader.

**Why validate in the writer rather than tolerate at the reader**: a record the summarizer would drop is a record the gate has claimed and nobody can read; the whole value of `rec <n>` is that it asserts a readable append. Why not run `--lint` over the file on each append: that would be a read of the file inside the loop, which §Writer forbids. Why the family stays at four members: a validation failure is a write that did not happen, which `WRITE FAILED` already names.
