# Telemetry — Per-Dispatch Record, Writer, Third Observation, Reader

Procedure text for the orchestrator's per-dispatch telemetry transcript:
the v1 record schema and its gate-signal sources, the `Budget:` grammar, the
writer sequence and rules, the `TELEMETRY:` gate-line family, the third
(telemetry-specific) write-scope observation with its finding strings, the
non-interference table of phase-detection inputs, the scorer derivation and
the post-cycle reader. Contract: `docs/spec/telemetry.md`
(REQ-TELEM-HARNESSP2-001..009, REQ-HARN-027 amendment,
REQ-SKILL-HARNESSP2-001). Stub: `../SKILL.md` §LOOP; the KICKOFF opt-out is
at `../SKILL.md` §KICKOFF; the `TELEMETRY:` line position is named at
`../SKILL.md` §The gate. Every token below is **defined here and nowhere
else**: the four-member `TELEMETRY:` line family (`rec <n>` included) and the
`OUT .sdd/telemetry.jsonl (+k records, leaf write — reverted)` finding string.

Everything here is **orchestrator-owned** (`../SKILL.md` §Orchestrator-Only
Work): the orchestrator writes the file after each gate; no leaf, review,
verifier or red dispatch is ever instructed to write or read it, and nothing
inside the loop reads it — it is **never** a phase-detection or staleness
input (§6).

---

## 1. Placement (REQ-TELEM-HARNESSP2-008, REQ-HARN-027 amendment)

| Property | Value | Why |
|---|---|---|
| Path | `<repo root>/.sdd/telemetry.jsonl` | outside `docs/`, so `git ls-files docs/` is unchanged — REQ-HARN-027's acceptance holds verbatim |
| Tracking | gitignored: `.sdd/` line in `.gitignore` (precedent `.superpowers/`) | not a project artifact; REQ-ORCH-004 (kickoff is the only new tracked artifact type) holds |
| Cardinality | **one file per repository**, all workstreams | a `docs/ws/<id>/telemetry*` file would become an owned execution artifact under `ws-layout.md`; records are attributed by `cycle.workstream` instead |
| Format | JSON Lines, one record per line, append-only | append is atomic enough for a single writer; no rewrite ever needed except the leaf-write revert below |
| Creation | the orchestrator creates `.sdd/` on first append | no setup step for the operator |
| `.gitignore` bootstrap | if `git check-ignore -q .sdd/telemetry.jsonl` exits non-zero, the orchestrator appends `.sdd/` to `.gitignore` as its own bookkeeping commit, outside any observed window (REQ-HARN-025), and renders `TELEMETRY: .gitignore updated` once at the next gate | the ignore line is the mechanism that keeps telemetry out of the porcelain snapshot and out of the repository |

---

## 2. Record schema (REQ-TELEM-HARNESSP2-001, -002, -003)

One JSON object per line. `v` is the schema version: `1` for every record
written before harness-p4 and `2` for a record carrying the `[p4]` fields
(Q-IMPL-HARNESSP4-002 — the admitted set is `{1, 2}`). Every value is a
**count, enum, sha, boolean, null or ISO-8601 UTC timestamp**; the record never
contains a finding line, a path list, file content, reviewer reasoning, or any
other prose (REQ-ORCH-012/013). The key set is fixed; null fields are written
as `null`, never omitted.

**This table is a rendering of the domain table in `tools/sdd-telemetry.py`**,
the schema's single source of truth (REQ-TELEM-HARNESSP4-004);
`docs/spec/telemetry.md` §Record Schema is the other rendering. The tool's
`--self-test` parses the `| Group | Key | Type / domain |` rows below and
diffs them against the code table, so a row added here without a code row —
or the reverse — fails it. Rows marked `[p4]` were added for harness-p4 and are
written with `v: 2`; a `v: 1` record is validated against the unmarked rows only.

| Group | Key | Type / domain | Source (gate signal) |
|---|---|---|---|
| — | `v` | int, `1` \| `2` — `2` for records carrying the `[p4]` fields; `1` records keep the pre-p4 key set (Q-IMPL-HARNESSP4-002) | constant per writer version |
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
| | `chunk` | int or null — the **integer N parsed** from the `### Chunk N:` header, **never** the header string (`"Chunk 3"`, `"### Chunk 3: …"`) and never a quoted digit; `null` for every non-chunk dispatch | `### Chunk N:` number for per-chunk dispatches |
| | `iteration` | int or null | fix-loop iteration this dispatch belongs to |
| | `redo` | int or null | per-chunk redo count at dispatch |
| | `reason` | repair-packet `reason` enum or null; its fix-only subset is the `const` row `FIX_ONLY_REASONS` below | `harness-return-contract.md` §Repair Packet (plus `RED_BREAK`, `adversarial-verify.md`) |
| `const` | `FIX_ONLY_REASONS` | subset of `dispatch.reason`: `red_break` `[p4]` — a **schema constant, not a record key**; no record carries it (`--lint` reports one that does as `key-undeclared`) | §7 implied-fix clause (b); `--lint` asserts the subset relation |
| | `budget` | budget object (below) | parsed from the dispatched `Budget:` line |
| | `write_scope_n` | int | number of declared scope globs |
| `return` | `status` | `COMPLETE` \| `PARTIAL` \| `BLOCKED` \| `BUDGET_EXHAUSTED` \| `MALFORMED` | `RETURN.status`; `MALFORMED` when the block failed to parse |
| | `budget_consumed` | budget object + `self_reported: true` | `RETURN.budget_consumed` |
| | `files_written_n`, `commits_n`, `tasks_completed_n`, `failures_n`, `ledger_n`, `open_questions_n`, `blocked_writes_n` | int | lengths of the corresponding `RETURN` lists |
| | `warnings` | list of enums ⊆ {`KEYS_MISSING`, `MULTIPLE_STATUS`, `FOREIGN_TOKEN`, `RETURN_DRIFT` `[p4]`} | parser warnings (`return-contract.md` §1; `RETURN_DRIFT` = the return-drift warning of `harness-return-contract.md`) |
| `scope` | `token` | `CLEAN` \| `VIOLATION` \| null | `SCOPE:` line (null for a dispatch with no scope check) |
| | `in`, `advisory`, `out` | int | tag counts in the write-scope block |
| | `history_rewrite` | bool | `HISTORY_REWRITE` finding present |
| | `widened` | int, default 0 `[p4]` | count of dispatched scope globs minus the stage template's default glob count, from session state at dispatch — a count, never glob text (REQ-TELEM-HARNESSP4-006) |
| `verdict` | `chunk_verdict` | `PASS` \| `FAIL` \| null | `CHUNK_VERDICT:` |
| | `review_verdict` | `APPROVE` \| `APPROVE_WITH_FIXES` \| `REJECT` \| null | `VERDICT:` |
| | `red_verdict` | `BROKEN` \| `HELD` \| null | `RED_VERDICT:` (`adversarial-verify.md`) |
| | `findings` | `{"C": int, "M": int, "m": int}` | counts of C/M/m lines |
| | `malformed` | bool | `REVIEW: MALFORMED` or `RETURN: MALFORMED` raised |
| | `contradiction_class` | null \| `b` \| `c` | `REVIEW: CONTRADICTION` class (`arbitrated-handoff.md`) |
| `gate` | `decision` | `proceed` \| `fix` \| `loop-back-to-fix` \| `stop` \| `redo` \| `replan` \| `revert` \| `widen` \| `accept` \| `third-opinion` \| `re-dispatch` \| `override` \| `other` | the operator's choice, normalised to one enum (table below) |
| | `decision_by` | `operator` \| `policy` | always `operator` this cycle (`evaluation.md`) |
| | `fix_iteration`, `fix_cap`, `cap_raised` | int | `iteration N of MAX (cap raised ×k)` |
| | `redo_count` | int or null | `Redo: N of REDO_MAX` |
| | `replan_count`, `replan_cap` | int | derived replan re-entry count and cap |
| — | `replan_trigger` | enum or null | replan trigger class surfaced at this gate (`stuck`, `spike`, `verification`, `operator`) |
| `git` | `head_before`, `head_after` | short sha (`^[0-9a-f]{7,12}$`) | the snapshot pair's `HEAD_before` / `HEAD_after` (`dispatch-snapshot-base.md`) — never the `HEAD` literal, never a 40-character sha |
| `commit` | `token` | `COMPLETE` \| `INCOMPLETE` \| null `[p4]` | the gate's own `COMMIT:` closing line (`write-scope.md` §7a, `harness-commit-fidelity.md`), copied after it renders; null for a dispatch whose gate commits nothing (review, verifier, red) (REQ-TELEM-HARNESSP4-007) |
| | `missing_n`, `extra_n` | int `[p4]` | that line's `observed, not landed` / `landed, not observed` counts — counts only, never paths |
| — | `migration` | optional `{from: chunk-string, at: date}` `[p4]` | present only on records rewritten by `migrate` (`docs/spec/telemetry.md` §In-Place Migration); the writer never sets it |

**Writer sources of the `[p4]` fields — no read of the telemetry file.**
`scope.widened` is computed from session state the orchestrator already holds
at dispatch: the dispatched scope's glob count minus the stage template's
default glob count (0 when the operator widened nothing). `commit` is copied
from the `COMMIT:` line the gate has just rendered from `git` — token and the
two counts. Both are copies of what the operator already saw; neither consults
`.sdd/telemetry.jsonl`, whose zero-reads rule (§3) is unchanged. A record
carrying either group is stamped `v: 2`.

**Resume-class keys are forbidden** (REQ-TELEM-HARNESSP2-003): no `next_stage`,
`resume`, `current_phase`, `pending`, `position` or equivalent. `dispatch.stage`
is what was dispatched, not what comes next; a reader cannot derive "where does
the loop resume" from any record, and the orchestrator never consults the file
on re-entry. A cycle (run) is identified by `cycle.research_id` — stamped on
every record — and a cycle boundary is a change of that id; readers order
records by `ts_dispatch` within a run and never rely on `dispatch.seq` being
monotonic across sessions.

**`dispatch.chunk` is a number, not a heading** — the orchestrator is the only
writer of this file, so this field's domain is enforced nowhere but here. Write
the **integer N** parsed out of the plan's `### Chunk N:` header
(`### Chunk 3: Telemetry` → `"chunk": 3`), and `null` for every dispatch that is
not per-chunk. Never write the header text, the header's `Chunk N` fragment, or
N as a string: `"chunk": "Chunk 3"` and `"chunk": "3"` are both out of domain.
A record that violates it still parses, so it is not dropped by the reader's
`skipped:` tally — it is excluded from `summarize`'s per-chunk block and counted
on the `out-of-domain dispatch.chunk: N record(s)` line instead. Live history is
never rewritten to repair it (§3 Append-only), so a writer-side slip stays visible for the
rest of the cycle.

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
| `manual intervention` · `authorize extra iteration` (recorded with `cap_raised`) | `override` |
| `accept round N (proceed, note)` · `accept manually` · `accept (record)` | `accept` |
| `third opinion` | `third-opinion` |
| `re-dispatch` | `re-dispatch` |
| `route to sdd-replan` | `replan` |
| anything else | `other` |

**Budget object** (REQ-TELEM-HARNESSP2-002): `{"tool_calls": int|null,
"test_runs": int|null, "prototypes": bool, "read_only": bool}`. Parsing rules
for the dispatched `Budget:` line (`harness-loop-control.md` §Budget Slot grammar; mirrored in `return-contract.md` §1):

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

Example (the **`verifier` record** of Chunk 3's first attempt — its own
dispatch, its own append; `chunk` is the parsed integer, never a header string;
`gate.decision` is the per-chunk gate it fed — §3 rule (i)):

```json
{"v":1,"ts_dispatch":"2026-09-19T12:30:11Z","ts_return":"2026-09-19T12:36:02Z","ts_gate":"2026-09-19T12:38:40Z",
 "cycle":{"workstream":"harness-p4","research_id":"RS-HARNESSP4-001","kickoff_date":"2026-09-19","marker":"4"},
 "dispatch":{"seq":9,"kind":"verifier","stage":"implement","chunk":3,"iteration":null,"redo":0,"reason":null,
             "budget":{"tool_calls":20,"test_runs":2,"prototypes":false,"read_only":true},"write_scope_n":0},
 "return":{"status":"COMPLETE","budget_consumed":{"tool_calls":14,"test_runs":2,"self_reported":true},
           "files_written_n":0,"commits_n":0,"tasks_completed_n":0,"failures_n":1,"ledger_n":0,"open_questions_n":0,"blocked_writes_n":0,"warnings":[]},
 "scope":{"token":null,"in":0,"advisory":0,"out":0,"history_rewrite":false},
 "verdict":{"chunk_verdict":"FAIL","review_verdict":null,"red_verdict":null,"findings":{"C":0,"M":0,"m":0},"malformed":false,"contradiction_class":null},
 "gate":{"decision":"redo","decision_by":"operator","fix_iteration":0,"fix_cap":3,"cap_raised":0,"redo_count":1,"replan_count":0,"replan_cap":3},
 "replan_trigger":null,"git":{"head_before":"1753b8d","head_after":"1753b8d"}}
```

Example (the **`fix` record** of that chunk's redo — the first attempt's
`pipeline` record at `redo: 0` is kept; this is a *further* record, `kind:
"fix"`, `redo` incremented, `reason` set, its own verifier's `CHUNK_VERDICT:`
copied onto `verdict.chunk_verdict` — §3 rules (ii)–(iii)):

```json
{"v":1,"ts_dispatch":"2026-09-19T12:40:05Z","ts_return":"2026-09-19T13:02:19Z","ts_gate":"2026-09-19T13:09:51Z",
 "cycle":{"workstream":"harness-p4","research_id":"RS-HARNESSP4-001","kickoff_date":"2026-09-19","marker":"4"},
 "dispatch":{"seq":10,"kind":"fix","stage":"implement","chunk":3,"iteration":null,"redo":1,"reason":"VERIFIER_FAIL",
             "budget":{"tool_calls":45,"test_runs":6,"prototypes":false,"read_only":false},"write_scope_n":6},
 "return":{"status":"COMPLETE","budget_consumed":{"tool_calls":31,"test_runs":4,"self_reported":true},
           "files_written_n":3,"commits_n":0,"tasks_completed_n":2,"failures_n":0,"ledger_n":1,"open_questions_n":0,"blocked_writes_n":0,"warnings":[]},
 "scope":{"token":"CLEAN","in":3,"advisory":0,"out":0,"history_rewrite":false},
 "verdict":{"chunk_verdict":"PASS","review_verdict":null,"red_verdict":null,"findings":{"C":0,"M":0,"m":0},"malformed":false,"contradiction_class":null},
 "gate":{"decision":"proceed","decision_by":"operator","fix_iteration":0,"fix_cap":3,"cap_raised":0,"redo_count":1,"replan_count":0,"replan_cap":3},
 "replan_trigger":null,"git":{"head_before":"1753b8d","head_after":"4c2e9a1"}}
```

**Why a transcript and not a log**: every value under `return`, `scope`,
`verdict` and `gate` is copied from what the gate already renders, so the record
can never expose more than the operator already saw — and because the gate
renders counts of findings alongside the verbatim lines, copying only the counts
keeps REQ-ORCH-012/013 intact by construction.

---

## 3. Writer (REQ-TELEM-HARNESSP2-004)

Only `sdd-orchestrate` writes the file. Sequence per dispatch:

```
ts_dispatch := date -u          # before snapshot(before) and dispatch
… dispatch → await return …
ts_return   := date -u          # on return, before snapshot(after)
… scope check (incl. the third observation, §4) → verifier / red / review → gate …
ts_gate     := date -u          # when the operator's decision is taken
append one record                # AFTER the gate decision, so gate.decision is filled
                                # on success: telemetry.rec += 1, asserted as
                                # `TELEMETRY: rec <n>` on the NEXT gate
```

Timestamps are whole seconds (`date -u +%Y-%m-%dT%H:%M:%SZ`).

Rules:

- **One append per dispatch**, after that dispatch's gate. A verifier, red or
  review dispatch is its own dispatch and gets its own record (its
  `gate.decision` is the stage/per-chunk gate decision it fed). A dispatch
  that never reaches a gate (session aborted mid-dispatch) writes no record.
- **One record per dispatch, for every kind the schema admits**
  (REQ-TELEM-HARNESSP4-001) — `pipeline`, `fix`, `fanout_leaf`, `verifier`,
  `review`, `red` — with `dispatch.kind` set to the kind **actually
  dispatched**. Where each kind's record goes:
  - (i) **a chunk verifier gets a `verifier` record of its own** (`kind:
    "verifier"`, `chunk: N`, `verdict.chunk_verdict` = its `CHUNK_VERDICT:`,
    `gate.decision` = the per-chunk gate it fed); its `CHUNK_VERDICT:` is
    *also* copied onto the chunk's own `pipeline`/`fix` record's
    `verdict.chunk_verdict` — the field the post-cycle reader's implication
    reads (§7). Two appends per verified chunk attempt, not one.
  - (ii) **every fix dispatch is a `fix` record, never `pipeline`** — a stage
    `loop-back-to-fix` (`iteration: N`, `reason: REVIEW`), a per-chunk `fix`
    (redo — `chunk: N`, `redo: N`, `reason: VERIFIER_FAIL`), or a `RED_BREAK`
    packet (`reason: red_break`).
  - (iii) **a redo keeps the first attempt's record**; the redo is a further
    `fix` record with `dispatch.redo` incremented and `dispatch.reason` set.
    A redone chunk therefore leaves `pipeline redo: 0` + `fix redo: 1`, each
    with its own `verifier` record — four appends.
  Worked `verifier` and `fix` examples with a non-null `chunk` are in §2. The
  p3 file held zero `verifier` and zero `fix` records across eight verifiers
  and three redos, and its one fix (`seq` 18) was typed `pipeline`, because
  the text above did not say where the verifier's record goes.
- **Append-only.** The orchestrator never rewrites or truncates the file, with
  the **single exception** of the leaf-write revert in §4.
- **Never load-bearing.** On any write error (unwritable directory, disk full)
  the orchestrator renders `TELEMETRY: WRITE FAILED` as one line of the next
  gate's text and continues with the unchanged `proceed │ loop-back-to-fix │
  stop` options. No retry, no pause.
- **Default on; KICKOFF opt-out, changeable mid-cycle.** Telemetry is on for
  every orchestrated cycle unless the operator disables it at KICKOFF; when off,
  no record is written and the first gate shows `TELEMETRY: OFF` once. The
  question is **asked once, at KICKOFF**, and the answer is session state, not an
  artifact (it is never written to `kickoff.md`) — but the operator may change it
  mid-cycle, and the behaviour of such a change is exactly the `OFF` row of the
  gate-line family below ("every gate after a mid-cycle opt-out") plus the
  mid-cycle walkthrough at the end of this section.
- **Write-only for the orchestrator.** `dispatch.seq` is a session-state
  counter starting at 1, and `telemetry.rec` (the append counter below) is a
  second one beside it; the orchestrator performs **zero reads** of the file —
  not for position, not for either counter.
- **No leaf ever writes it.** No stage skill, review, verifier, fan-out leaf or
  red dispatch is instructed to write it and no dispatch template names the
  path; `.sdd/**` is never in any default or widened write scope
  (REQ-HARN-020), so a leaf write is `OUT` by construction.
- **Marker `3` repositories**: identical behaviour; `cycle.workstream` is
  `default`, `cycle.marker` is `"3"`.

**`TELEMETRY:` gate-line family** (defined here; rendered at most once each per
gate, immediately after the `iteration`/cap line, before the options —
`../SKILL.md` §The gate):

| Line | When |
|---|---|
| `TELEMETRY: rec <n>` | the previous dispatch's append **succeeded**; `<n>` is the count of successful appends this session |
| `TELEMETRY: WRITE FAILED` | the previous append raised an error |
| `TELEMETRY: OFF` | first gate of a cycle in which the operator disabled telemetry, and every gate after a mid-cycle opt-out |
| `TELEMETRY: .gitignore updated` | the orchestrator added the `.sdd/` ignore line |

The family is `rec <n> │ WRITE FAILED │ OFF │ .gitignore updated` — four
members. `rec <n>` is the **positive** member (REQ-TELEM-HARNESSP3-001): without
it a gate that rendered telemetry as on looked identical whether or not the
append happened.

**`<n>` — the append counter** (`telemetry.rec`, Q-IMPL-HARNESSP3-005):

- `<n>` counts **successful appends this session**. It is **not** `dispatch.seq`.
  The two diverge whenever a dispatch produces no append (a `WRITE FAILED`, or a
  mid-cycle opt-out), and where they diverge **the append count wins** — the line
  exists to assert that the append happened, so binding `<n>` to the dispatch
  sequence would have a later gate assert an append count that never occurred.
- It is a new **session-scoped counter named `telemetry.rec`**, maintained beside
  `dispatch.seq` in the orchestrator's existing session state: initialised to 0 at
  KICKOFF, incremented **only** after an append returns successfully, and never
  decremented (a leaf-write revert, §4, removes lines the orchestrator never
  counted). It restarts at 0 in a new session. **No new artifact.**
- Position: the writer appends *after* the gate decision, so the **next** gate is
  where the previous append is asserted; the line renders at most once per gate,
  immediately after the `iteration`/cap line and before the options
  (`../SKILL.md` §The gate).
- **Absence is the signal**: an operator who sees a gate carrying no `rec` line,
  no `OFF` line and no `WRITE FAILED` line knows the append did not happen —
  **except at a session's first gate**, where no append has yet been attempted
  (the writer appends *after* the gate decision), so a bare first gate is
  expected and not a signal.
  `tools/sdd-telemetry.py summarize`'s `records-vs-expected:` line (§7) is the
  post-cycle backstop for a gate whose absent line went unnoticed.

**The line is never a read of the telemetry file.** `<n>` comes from session
state, not from counting lines in `.sdd/telemetry.jsonl`: the write-only rule
above (REQ-TELEM-HARNESSP2-004, "the orchestrator performs **zero reads** of the
file") is preserved **intact**, and the line is text on the gate, so §5's
non-interference proof is **untouched** — `.sdd/` still appears in no row of the
phase-detection input table, and `rm -rf .sdd/` still leaves every detected
phase, staleness verdict and position table byte-identical (it costs at most the
accuracy of a text line, never a decision).

Walkthroughs (the discriminating cases):

| Session | Gates render | Why |
|---|---|---|
| two gated dispatches, both appends succeed | `rec 1`, then `rec 2` | one increment per successful append |
| file unwritable | `WRITE FAILED`, and **no** `rec` line | a failed append never advances `telemetry.rec` |
| three dispatches, the second append fails | `rec 1`, `WRITE FAILED`, `rec 2` — **not** `rec 3` | `<n>` counts appends, not dispatches |
| mid-cycle opt-out, then opt back in | `OFF` gates render no `rec` and do not advance `<n>`; the next successful append resumes from the retained value | the counter is retained, not reset, while telemetry is off |

---

## 4. Third observation and leaf-write revert (REQ-TELEM-HARNESSP2-005)

`.sdd/` is gitignored, so a leaf write there is invisible to the porcelain
snapshot pair (`write-scope.md` §5 limitation (b)). The orchestrator therefore
takes a **third, telemetry-specific observation** beside the two snapshots of
REQ-HARN-021, in the same window (REQ-HARN-025 ordering — before its own
append):

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
- **Leaf deletes `.sdd/`**: `e_after` is empty → `OUT .sdd/telemetry.jsonl (−k
  records, leaf write — unrecoverable)`; the orchestrator recreates the
  directory on its next append.

These finding strings are defined **once, here**; `write-scope.md` §3 (the
third observation) and §5 (limitation (b)'s `.sdd/` exception) cite this
section instead of restating them. The revert happens **before the gate**,
like the chunk verifier's write revert (`loop-control.md` §1b); the gate then
offers the normal `VIOLATION` options for any other `OUT` path. Fixture:
`tools/sdd-scope-check-selftest.py` scenario F7.

---

## 5. Non-interference proof (REQ-TELEM-HARNESSP2-003, -006)

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
| sdd-verify Step 3b, sdd-review Step 2 | `docs/requirements/traceability.md`, `docs/ws/<id>/traceability.md` — coverage only, never position |

(Flat `docs/` equivalents under marker `3`.) `.sdd/` appears in no row and this
table is the contract: adding a reader of `.sdd/` to any skill is a change to
`docs/spec/telemetry.md`, not an implementation detail. Consequences that must
hold:

1. `rm -rf .sdd/` leaves every skill's detected phase, every staleness verdict
   and the orchestrator's position table byte-identical.
2. The record carries no resume-class key (§2), so even a reader that violated
   rule 1 could not answer "where am I".
3. The lint guard (a `FORBIDDEN` `\.sdd/` row allowlisting only `../SKILL.md`,
   this file and `write-scope.md`) makes rule 1 mechanical.

`tools/sdd-gc.py` (drift sweep) and `tools/sdd-telemetry.py` are out-of-loop
tools, not skills; gc never reads `.sdd/` either.

---

## 6. Scorer derivation (REQ-EVAL-HARNESSP2-002 cross-reference)

`evaluation.md` §Scorer Fields fixes the scorer field list; every field must be derivable
from the record key set plus `verification.md`'s `status` line. The derivation:

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
other than `verification.md`'s `status`.

---

## 7. Post-cycle reader (REQ-TELEM-HARNESSP2-009)

After a cycle — never inside the loop, and never from a skill — the operator
summarises the transcript with the out-of-loop tool:

```
python3 tools/sdd-telemetry.py summarize [--file .sdd/telemetry.jsonl] [--workstream <id>] [--since <ISO>]
```

It prints one table per workstream, one row per `dispatch.stage` (dispatches;
tool calls mean/max/budget with an `n/a` column; SCOPE violations; MALFORMED;
fix iterations; redos per chunk; contradiction pauses; red BROKEN/HELD; wall
time dispatch and gate mean/max), then a per-chunk block (RS-008 probe 1 as a
query). Unknown-`v` and non-JSON lines are skipped and counted on a trailing
`skipped: N …` line. A **sibling** of that line,
`records-vs-expected: N session(s), K with a missing append`, reports per session
how many appends the records imply versus how many are present
(REQ-TELEM-HARNESSP3-002). "Expected" is derived **from the records themselves**
and never from a gate or any side channel from the orchestrator
(Q-IMPL-HARNESSP3-006); a session boundary is a `dispatch.seq` that does not
exceed its predecessor within one (`cycle.workstream`, `cycle.research_id`) group
ordered by `ts_dispatch` (Q-IMPL-HARNESSP3-018). It is **strictly post-cycle**:
it is a backstop for a missed gate line, it never influences control flow, and it
does not weaken the zero-reads rule — nothing inside the loop runs this tool.

**Implication-derived `expected`** (REQ-TELEM-HARNESSP4-002, -003;
`docs/spec/telemetry.md` §Implication-Derived `expected` and the Headline). The
highest `seq` alone saw no gap on the p3 file, because a writer that never
appends also never increments. `expected` therefore **starts** from the highest
`seq` and adds every append implied by a cross-field value the writer *did*
fill, per session, per kind, `redo` read as 0 when null. The chunk-shaped
implications are computed **per `(stage, chunk)` group** — the `pipeline` and
`fix` records sharing one stage and chunk — never by summing `1 + redo` over
records, since §3 rule (iii) keeps the first attempt's record *and* adds a
`fix` record per redo:

```
attempts(stage, chunk) := 1 + max(dispatch.redo) over the group's pipeline/fix records
implied.verifier       := Σ attempts over groups with a non-verifier record carrying verdict.chunk_verdict
implied.pipeline       := Σ over implement groups of (1 + #pipeline records with redo ≥ 1)   # a redo typed pipeline stands in for its own first attempt
implied.review         := #records with kind != review and verdict.review_verdict != null
implied.red            := #records with kind != red    and verdict.red_verdict    != null
implied.fix            := #gates deciding loop-back-to-fix | fix | redo                       # clause (a) — records sharing one gate share ts_gate and count once (Q-IMPL-HARNESSP4-004)
                        + #records with kind != fix and dispatch.reason ∈ FIX_ONLY_REASONS     # clause (b) — the `const` row of the schema table ({red_break})
missing.<kind>         := Σ per stage of max(0, implied − recorded)      never cross-stage, never negative
missing.fix            := 0 for an implied fix PRESENT as a record of another kind (mis-typed — a --lint [mistyped-fix] finding, not a missing append)
expected               := highest dispatch.seq + Σ missing.<kind>
```

**Both record shapes** the formula must hold on, one implement group each:

| Shape | Records | `attempts` | implied verifier | implied pipeline vs recorded |
|---|---|---|---|---|
| p3 collapsed (fixture `seq` 7, 10, 13) | one `pipeline`, `redo: 1`, `chunk_verdict: PASS` | 2 | 2 | 2 vs 1 → 1 missing |
| p3 single attempt (fixture `seq` 6, 8, 9, 11, 12) | one `pipeline`, `redo: null`, `chunk_verdict: PASS` | 1 | 1 | 1 vs 1 → 0 missing |
| compliant redo (§3 rule (iii)) | `pipeline redo: 0` + `fix redo: 1`, both with `chunk_verdict`, + two `verifier` records | 2 | 2 (vs 2 recorded) | 1 vs 1 → 0 missing |

**Headline** — the **total shortfall of every implied append, per session**
(ratified, Q-REQ-P4-D): `records-vs-expected: <recorded> recorded, expected <n>
(<n − recorded> missing)`, followed by one `implied vs recorded` line per kind
(the `pipeline` line is implement-scoped, tagged `[implement]`; the `fix` line
carries `; N mis-typed — see --lint` when mis-typed fixes exist) and an
`implement: N missing (…)` line giving the **full** implication count. On the
frozen fixture `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` (20
records, read-only, sha256 asserted before and after — `tools/fixtures/README.md`):

```
records-vs-expected: 20 recorded, expected 39 (19 missing)
  implied vs recorded — verifier : 11 vs 0  (11 missing)
  implied vs recorded — pipeline : 11 vs 8  (3 missing)        [implement]
  implied vs recorded — review   :  6 vs 2  (5 missing)
  implied vs recorded — red      :  1 vs 2  (0 missing)
  implied vs recorded — fix      :  2 vs 0  (0 missing; 2 mis-typed — see --lint)
  implement: 14 missing (3 pipeline first attempts + 11 verifier)
```

Eight implement groups, three with `max(redo) = 1`: `implied.verifier = 5 × 1
+ 3 × 2 = 11` against 0 recorded; `implied.pipeline = 11` against 8 (3
missing); review 6 vs 2 with the 5 missing matched per stage (research 2,
requirements, specs, plan 1 each — the implement and verify reviews exist);
red 1 vs 2 (0 missing, never negative); fix implied 2 (`seq` 1's
`loop-back-to-fix`, clause (a); `seq` 18's `reason: red_break`, clause (b))
against 0 recorded, both **present as `pipeline` records** (`seq` 2 and 18) and
so mis-typed, 0 missing. `reason: REVIEW` at `iteration ≥ 1` with no preceding
`loop-back-to-fix` at the stage (`seq` 3–5) is the `--lint` **warning**
`[reason-review]`, never a count. The `see --lint` pointer resolves when the
`--lint` subcommand lands (P3); `summarize` renders the suffix already.

After the per-kind lines each session prints `widened dispatches: N; COMMIT:
INCOMPLETE: M` — the number of records with `scope.widened > 0` and the number
whose `commit.token` is `INCOMPLETE` (§2; a `v: 1` record has neither key and
counts 0). `summarize --plan <path>` adds an implement-stage **floor** from the
plan's `### Chunk N:` headers: `implement floor: N pipeline (2N with verifier);
recorded implement records: M; shortfall: max(0, N − M)`, `M` = implement
`pipeline` records (REQ-TELEM-HARNESSP4-008; Q-IMPL-HARNESSP4-005).

**Schema lint** (REQ-TELEM-HARNESSP4-004, `docs/spec/telemetry.md` §Schema Lint):

```
python3 tools/sdd-telemetry.py --lint [--file .sdd/telemetry.jsonl]
```

validates **every field of every record** against the domain table §2 renders
— enum membership, types (`dispatch.chunk` int-or-null, counters int, shas
`^[0-9a-f]{7,12}$` with the `HEAD` literal and 40-character shas as findings,
ISO-8601 UTC timestamps, `v ∈ {1, 2}`), the fixed key set per `v`
(`key-undeclared`, `key-missing`, the optional `migration` marker only in its
declared shape) and the cross-field rules (`[mistyped-fix]`, a `chunk_verdict`
with no `verifier` record for the chunk, a `proceed` implement record with
`head_before == head_after`, a non-null `commit.token` on a kind whose gate
never commits). One line per finding, `seq <n>: [<class>] <group.key>:
<message>`; `WARN seq <n>: [reason-review] …` is a warning and never affects
the exit code. Exit 1 on any finding, 0 when clean. Like `summarize`, it is
post-cycle and out-of-loop: nothing in the orchestrator runs it.

A missing or empty telemetry file is an empty run set: `summarize` prints `records: 0` and an empty table and exits 0 (the same
`n_before := 0 if absent` rule the writer and `sdd-eval.py` follow), never an
error. `--help` and `--self-test` are available.
