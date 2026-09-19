---
status: Approved
last_updated: 2026-09-18
requires:
  - REQ-TELEM-HARNESSP2-001
  - REQ-TELEM-HARNESSP2-002
  - REQ-TELEM-HARNESSP2-003
  - REQ-TELEM-HARNESSP2-004
  - REQ-TELEM-HARNESSP2-005
  - REQ-TELEM-HARNESSP2-006
  - REQ-TELEM-HARNESSP2-007
  - REQ-TELEM-HARNESSP2-008
  - REQ-TELEM-HARNESSP2-009
  - REQ-HARN-027
  - REQ-SKILL-HARNESSP2-001
  - REQ-SKILL-HARNESSP2-008
  - REQ-LINT-HARNESSP2-002
  - REQ-TELEM-HARNESSP3-001
  - REQ-TELEM-HARNESSP3-002
  - REQ-TELEM-HARNESSP4-001
  - REQ-TELEM-HARNESSP4-002
  - REQ-TELEM-HARNESSP4-003
  - REQ-TELEM-HARNESSP4-004
  - REQ-TELEM-HARNESSP4-005
  - REQ-TELEM-HARNESSP4-006
  - REQ-TELEM-HARNESSP4-007
  - REQ-TELEM-HARNESSP4-008
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

This spec defines the record, the writer, the non-interference proof, the
scope-check interaction and the out-of-loop reader. It fulfils
REQ-TELEM-HARNESSP2-001..009, the REQ-HARN-027 amendment, the orchestrator-side
skill changes of REQ-SKILL-HARNESSP2-001 / -008 and the lint guard of
REQ-LINT-HARNESSP2-002. It **supersedes** the sentence "no `docs/reviews/`,
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
table (§Schema Lint), so a row added here without a code row — or the reverse —
fails the self-test. Rows marked `[p4]` were added 2026-09-18 for harness-p4
(REQ-TELEM-HARNESSP4-002, -003, -006, -007) and are written with `v: 2`.

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
| | `reason` | repair-packet `reason` enum or null; its fix-only subset is the `const` row `FIX_ONLY_REASONS` below | `harness-return-contract.md` §Repair Packet (plus `RED_BREAK`, `adversarial-verify.md`) |
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
| `gate` | `decision` | `proceed` \| `fix` \| `loop-back-to-fix` \| `stop` \| `redo` \| `replan` \| `revert` \| `widen` \| `accept` \| `third-opinion` \| `re-dispatch` \| `override` \| `other` | the operator's choice, normalised to one enum (table below) |
| | `decision_by` | `operator` \| `policy` | always `operator` this cycle (`evaluation.md`) |
| | `fix_iteration`, `fix_cap`, `cap_raised` | int | `iteration N of MAX (cap raised ×k)` |
| | `redo_count` | int or null | `Redo: N of REDO_MAX` |
| | `replan_count`, `replan_cap` | int | derived replan re-entry count and cap |
| — | `replan_trigger` | enum or null | replan trigger class surfaced at this gate (`stuck`, `spike`, `verification`, `operator`) |
| `git` | `head_before`, `head_after` | short sha (`^[0-9a-f]{7,12}$`) | the snapshot pair's `HEAD_before` / `HEAD_after` (`dispatch-snapshot-base.md`) |
| `commit` | `token` | `COMPLETE` \| `INCOMPLETE` \| null `[p4]` | the `COMMIT:` closing line (`harness-commit-fidelity.md`); null for a dispatch whose gate commits nothing |
| | `missing_n`, `extra_n` | int `[p4]` | the `observed, not landed` / `landed, not observed` counts of that line |
| — | `migration` | optional `{from: chunk-string, at: date}` `[p4]` | present only on records rewritten by `migrate` (§In-Place Migration) |

**`const` rows** [Added 2026-09-18, harness-p4 specs review r1 — M3]: a row
whose `Group` cell is the literal `const` declares a **schema constant** —
`FIX_ONLY_REASONS` is the only one today. It is rendered as a real table row in
both renderings (here and `references/telemetry.md` §2), it names no record key
(`--lint` reports a record carrying a `const` name as `key-undeclared`), its
members are the backticked tokens of its `Type / domain` cell, and the
parse-and-diff self-test (§Schema Lint) compares the set of `const` names and
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
| `manual intervention` · `authorize extra iteration` (recorded with `cap_raised`) | `override` |
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
  chunk's own record's `verdict.chunk_verdict`, which is the field the
  implication of §Records-vs-Expected reads; (ii) a fix dispatch — a stage
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
`\.sdd/` location of §Lint Guard. The revert happens before the gate, like the
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
| sdd-verify Step 3b, sdd-review Step 2 | `docs/requirements/traceability.md`, `docs/ws/<id>/traceability.md` — coverage only, never position |

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

### Lint Guard (REQ-TELEM-HARNESSP2-007, REQ-LINT-HARNESSP2-002)

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
line; a line that is not JSON is counted likewise. `--self-test` builds a
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
by summing `(1 + redo)` over records, because §Writer rule (iii) keeps the
first attempt's record *and* adds a `fix` record per redo, so a per-record sum
counts the same attempt twice [Amended 2026-09-18, harness-p4 specs review r1 —
C1]:

```
attempts(stage, chunk) := 1 + max(dispatch.redo) over that group's pipeline/fix records           # the redo counter is per chunk, so its max IS the attempt count
implied.verifier       := Σ over groups with ≥ 1 record carrying verdict.chunk_verdict != null (kind != verifier) of attempts(stage, chunk)
implied.pipeline       := Σ over implement groups of ( 1                                             # the first attempt is always a pipeline dispatch
                                                     + #records in the group with kind == pipeline and dispatch.redo ≥ 1 )   # a redo recorded as pipeline (the p3 collapsed shape) stands in for its own first attempt
implied.review         := #records with kind != review and verdict.review_verdict != null           # one per carrying record
implied.red            := #records with kind != red    and verdict.red_verdict    != null
implied.fix            := #records with gate.decision ∈ {loop-back-to-fix, fix, redo}               # clause (a): each such decision dispatches one fix (a per-chunk `fix` normalises to `redo`, §Writer rule (ii))
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
| compliant redo (§Writer rule (iii)) | `pipeline` `redo: 0` + `fix` `redo: 1`, both `chunk_verdict` non-null | 2 | **2** | 1 + 0 = **1** vs 1 → 0 missing |

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

`FIX_ONLY_REASONS` is a **`const` row of the domain table** (§Record Schema;
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
| type | `dispatch.chunk` int-or-null (a header **string** is a finding); every counter int; `scope.widened` int ≥ 0; shas match `^[0-9a-f]{7,12}$` (`"HEAD"` literal and 40-char shas are findings); timestamps ISO-8601 UTC; `v` ∈ the admitted set `{1, 2}` (Q-IMPL-HARNESSP4-002) |
| fixed key set | per `v`: an undeclared key (e.g. `git.commit_n`) is `key-undeclared`; a declared key absent is `key-missing`; the optional `migration` marker (§In-Place Migration) is admitted only with its declared shape |
| cross-field | the two fix clauses and the mis-typed-fix rule (§Implication-Derived `expected`); non-null `chunk_verdict` on a non-verifier record with **no** `verifier` record for that chunk in the session; `proceed` implement record with `head_before == head_after`; `commit.token` non-null on a kind whose gate never commits (review, verifier, red) |

**The domain table in the tool is the single source of truth for the record
schema** — one table, two readers. `docs/spec/telemetry.md` §Record Schema and
`references/telemetry.md` §2 are **renderings** of it (stated there). Agreement
is enforced by **parse-and-diff**, not generation: the self-test
`test_schema_table_agrees` parses the `| Group | Key | Type / domain |` rows of
both documents — the `Key` cell may list several backticked keys sharing one
type; enum members are the backticked tokens separated by `\|`; scalar types
are the leading word (`int`, `bool`, `timestamp`, `short sha`, `date`, `string`,
`list`); a row whose `Group` cell is `const` is parsed into a **separate
constant set** `{name: members}` (§Record Schema, `const` rows) and never into
`group.key` — and asserts that the set of `group.key`, for enum-typed keys the
member set, and the constant set with each constant's members, equal the code
table's; it further asserts `FIX_ONLY_REASONS ⊆ dispatch.reason` members
[M3]. Adding a row on either side alone fails the self-test. Why not generate the spec block from the code: a generated block
would be a code-owned write into an Approved spec on every schema change,
which the write-scope contract tags `ADVISORY` and review must re-read; parsing
keeps the spec the human-reviewed artifact and the code the executable one.
The `Source (gate signal)` column is prose and is not compared.

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
  §Writer's append-only rule (the first is the leaf-write revert). It is run by
  the operator with no orchestrator session open — never by a leaf (which would
  breach the orchestrator-only-writer rule) and never while a session is
  appending (a race with the orchestrator's appends). No dispatch template
  mentions it; `--help` and `references/telemetry.md` §7 state the rule.
- **In place** when `--out` is absent: write to a sibling temp file, verify the
  line count is unchanged, then rename over the original. `--out` writes
  elsewhere and leaves the input untouched.
- **Idempotent**: an already-int `chunk` and an already-present `migration`
  marker are left alone; a second run changes nothing.
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
`COMMIT: INCOMPLETE` counts. Because two record groups are added this cycle,
records that carry them are written with **`v: 2`**; `v: 1` records (every
record before this cycle, including the frozen fixture) remain valid against
the `v: 1` key set, so `--lint` does not report `key-missing` for `scope.widened`
or `commit` on them. Both versions are admitted by the domain table, by
`summarize` and by `--lint` — the bump is a schema decision recorded as
Q-IMPL-HARNESSP4-002, not prose: the shipped reader's `v != SCHEMA_V` skip
would otherwise drop every live p4 record from `summarize` at DONE
[Amended 2026-09-18, harness-p4 specs review r1 — M1].

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
- `test_lint_forbidden_sdd_row`: `.sdd/telemetry.jsonl` inside a fence in a
  fixture `sdd-plan/SKILL.md` → exit 1 with the row's fix; the three allowlisted
  paths → exit 0; shipped skill set → exit 0.
- `test_summarize_six_record_fixture`: one row per stage with every column;
  `--self-test` exits 0; an unknown-`v` record is skipped and counted.
- `test_no_ws_telemetry_path`: no `docs/ws/*/telemetry*` path exists after a
  cycle.

### Manual

- Run one orchestrated stage with telemetry on; open the gate text and confirm
  the record's counts equal what the gate rendered.

### Acceptance Criteria

- [ ] Record key set, value domains and counts-not-text rule as in §Record Schema; `dispatch.seq` 1-based per session with zero orchestrator reads of the file; run identity = `cycle.research_id`; `gate.decision` normalisation table incl. `other`; no resume-class key (REQ-TELEM-HARNESSP2-001, -003)
- [ ] `dispatch.budget` and `return.budget_consumed` are enumerated units; `self_reported: true`; unparsable → `{"unparsed": true}` (REQ-TELEM-HARNESSP2-002)
- [ ] Orchestrator-only, one append after each gate, never truncated except the leaf-write revert; `TELEMETRY: rec <n> | WRITE FAILED | OFF | .gitignore updated` lines; default on with KICKOFF opt-out; one file per repository (REQ-TELEM-HARNESSP2-004)
- [ ] Third observation (line count + entry list) and the `OUT .sdd/telemetry.jsonl (+k records, leaf write — reverted)` string defined once; revert to before-count; scope self-test scenario F7 (REQ-TELEM-HARNESSP2-005)
- [ ] Phase-detection input table as in §Non-Interference Proof; `rm -rf .sdd/` is behaviour-neutral (REQ-TELEM-HARNESSP2-006)
- [ ] `FORBIDDEN` row `\.sdd/` with the three-file `allow_files` allowlist, raw-text scan, stated reason and fix (REQ-TELEM-HARNESSP2-007, REQ-LINT-HARNESSP2-002)
- [ ] `.sdd/` gitignored at the repo root; `git ls-files docs/` unchanged by a cycle (REQ-TELEM-HARNESSP2-008, REQ-HARN-027)
- [ ] `tools/sdd-telemetry.py summarize` with the columns above, `--help`, `--self-test`, unknown-`v` tolerance; not invoked by any skill (REQ-TELEM-HARNESSP2-009)
- [ ] `references/telemetry.md` exists and resolves; `SKILL.md` stub ≤ 10 lines; no template names `.sdd/` (REQ-SKILL-HARNESSP2-001)
- [ ] `USAGE.md` has a section per new signal; `CLAUDE.md` diff is one paragraph and the four-layer bullet is unchanged (REQ-SKILL-HARNESSP2-008)
- [ ] Scorer derivation table present and complete against `evaluation.md` §Scorer Fields
- [ ] `python3 tools/sdd-skill-lint.py` exits 0; `--self-test` exits 0
- [ ] §3's gate-line table lists `rec <n>` and the writer sequence names the gate that renders it; `skills/sdd-orchestrate/SKILL.md` §The gate states it in one line (REQ-TELEM-HARNESSP3-001)
- [ ] A walkthrough of two gated dispatches with telemetry on renders `TELEMETRY: rec 1` then `TELEMETRY: rec 2` (REQ-TELEM-HARNESSP3-001)
- [ ] Every restatement of the `TELEMETRY:` family — `skills/sdd-orchestrate/SKILL.md` §The gate and `CLAUDE.md` §Driver — lists all four members, `rec <n>` included (REQ-TELEM-HARNESSP3-001)
- [ ] A walkthrough with telemetry on but the file unwritable renders `TELEMETRY: WRITE FAILED` and **no** `rec` line (REQ-TELEM-HARNESSP3-001)
- [ ] A resumption walkthrough of three gated dispatches whose second append fails renders `rec 1`, `WRITE FAILED`, `rec 2` — **not** `rec 3`; the same holds after a mid-cycle opt-out, whose `OFF` gates append nothing and do not advance `<n>` (REQ-TELEM-HARNESSP3-001)
- [ ] `grep` for a telemetry-file read in the orchestrator's gate path returns nothing (REQ-TELEM-HARNESSP3-001, REQ-TELEM-HARNESSP2-004)
- [ ] **If built**: `python3 tools/sdd-telemetry.py summarize` on a fixture whose session records fewer appends than gates prints a records-vs-expected line for that session, and `--self-test` exits 0. **If not built**: it is queued under `verification.md` §Next Steps and nothing else changed (REQ-TELEM-HARNESSP3-002)
- [ ] §Writer names every kind and states the one-record-per-dispatch rule with the verifier / fix / redo-first-attempt clauses; `references/telemetry.md` §2 states the same with worked `verifier` and `fix` examples (non-null `chunk`); this cycle's live file summarised at DONE shows `verifier` count = chunk verifiers dispatched and `fix` count = fix dispatches rendered, with `implied vs recorded` reporting 0 missing for both kinds in this cycle's session (REQ-TELEM-HARNESSP4-001)
- [ ] `summarize --file tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` prints `expected 39` against 20 records (19 missing), an implement line of 14 missing, and per-kind lines verifier 11 vs 0, pipeline 11 vs 8 at implement, review 6 vs 2 (5 missing), red 1 vs 2 (0 missing); `--self-test` covers each implication and a gapless negative fixture reading 0 missing, that fixture including one compliant redone chunk (`pipeline` `redo: 0` + `fix` `redo: 1`, both with `chunk_verdict`) that yields 2 implied verifiers / 1 implied pipeline; the formulas are computed per `(stage, chunk)` group and §Records-vs-Expected states both worked shapes beside them; §Records-vs-Expected and `references/telemetry.md` §7 state the definition and the headline; Q-IMPL-HARNESSP3-006 is amended to name the fields; the tool reads only the telemetry file and the orchestrator performs zero reads of it (REQ-TELEM-HARNESSP4-002)
- [ ] On the fixture the tool reports `implied.fix 2, recorded 0, missing 0` with `seq` 2 and 18 listed as `[mistyped-fix]` by `--lint` and `seq` 3–5 as `[reason-review]` warnings; a `red_break` pipeline record with a null-decision predecessor is flagged (clause (b)); a `loop-back-to-fix` followed by no record counts 1 missing fix; `FIX_ONLY_REASONS` is a `const` row of the domain table rendered as a real row in §Record Schema and `references/telemetry.md` §2, parsed into the constant set (never `group.key`) by `test_schema_table_agrees`, with `--lint` asserting it is a subset of `dispatch.reason` (REQ-TELEM-HARNESSP4-003, -004)
- [ ] `--lint --file <fixture>` exits non-zero reporting at minimum `kind: gate` (`seq` 20), header strings (`seq` 6–13), `head_after: "HEAD"` (`seq` 5), null `git` heads (`seq` 6–14), 40-character shas and undeclared `git.commit_n` (`seq` 15–20); a gapless in-domain fixture exits 0; `--self-test` covers each domain class with one mutation; `test_schema_table_agrees` fails when a row is added to the code table but not this spec's table or vice versa; §Record Schema states it is a rendering of the code table; `python3 tools/sdd-skill-lint.py` exits 0 (REQ-TELEM-HARNESSP4-004)
- [ ] `sha256sum tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl` reads `7e20b630…af9237` at DONE and `git diff --stat main -- tools/fixtures/` is empty; `migrate --file <copy> --out <tmp>` yields a file whose per-chunk block for chunks 0–7 carries `partial` and names the unreconstructable kinds; `migrate --file <fixture>` exits 2 without writing; the plan lists the migration task after the four prerequisite tasks; the operator ran `migrate` on the live file before the verify stage with no session open, and `verification.md` records the `--lint` result on the migrated records (no typed-field finding) (REQ-TELEM-HARNESSP4-005)
- [ ] The domain table declares `scope.widened` int default 0; §Record Schema and `references/telemetry.md` §2 render it; `summarize` prints widened dispatches per session; a fixture with `scope.widened: 2` is in-domain and a string value is a `--lint` finding; §Writer names the source without any telemetry-file read (REQ-TELEM-HARNESSP4-006)
- [ ] The domain table declares the `commit` group; both telemetry documents render it; `summarize` prints per-session `COMMIT: INCOMPLETE` counts; `{INCOMPLETE, 1, 0}` passes `--lint` and `token: DROPPED` fails it; `grep -n 'commit' skills/sdd-orchestrate/references/loop-control.md` shows the gate reading git, not telemetry; records carrying the group are `v: 2` and `v: 1` records lint clean against the `v: 1` key set (REQ-TELEM-HARNESSP4-007)
- [ ] `summarize` and `--lint` read `v: 2` records: a fixture mixing `v: 1` and `v: 2` records is summarised with `skipped: 0`; the shipped `v != SCHEMA_V` skip in `tools/sdd-telemetry.py` is replaced by membership in the admitted set `{1, 2}`; the per-`v` key sets are derived from the domain table's `[p4]` marks, not from a second constant; a record with `v: 3` is still skipped and counted (unknown-`v` tolerance) (REQ-TELEM-HARNESSP2-001, REQ-TELEM-HARNESSP2-009, REQ-TELEM-HARNESSP4-004, REQ-TELEM-HARNESSP4-007; Q-IMPL-HARNESSP4-002)
- [ ] **If built**: `summarize --plan docs/ws/harness-p3/plan.md --file <fixture>` prints an implement floor of 8 (16 with verifier), flags no shortfall against 8 recorded pipeline records while the implication line still reports 14 missing; `--self-test` covers a plan with a chunk that has no record. **If not built**: queued under `verification.md` §Next Steps (REQ-TELEM-HARNESSP4-008)
- [ ] Every fixture-based test asserts the fixture's sha256 before and after and writes outputs only under a temporary directory (§Fixture-Based Test Contract)

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

## Open Questions

1. **File locking for concurrent sessions.** Default: none; torn lines are
   skipped by the reader and counted.
2. **`gate.decision` enum completeness** as new gate options appear. Default:
   the normalisation table above; an unrecognised option is recorded as
   `other` with no text, and adding a row to the table is a change to this spec.
3. **Should `ts_*` be stamped with sub-second precision?** Default: whole
   seconds (`date -u +%Y-%m-%dT%H:%M:%SZ`); dispatch wall times are minutes.

## Implementation Questions

### Q-IMPL-HARNESSP2-010: `SCOPE: VIOLATION (1 path)` singular vs the spec's `(1 paths)` literal
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Third Observation (F7 expected line)
**Decision**: the shipped renderer pluralises (`1 path`, `2 paths`) as `write-scope.md` §5 and scenarios F1/F2/F6 already do; F7 asserts `SCOPE: VIOLATION (1 path)`. The `OUT .sdd/telemetry.jsonl (+1 records, leaf write — reverted)` string is byte-exact. The spec's `(N paths)` is read as a template.
**Rationale**: consistency with the v5 renderer; no contract value depends on the plural form.
**Date**: 2026-09-17 (Chunk 0)

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

### Q-IMPL-HARNESSP4-002: the schema version `v` becomes the admitted set `{1, 2}`
**Tier**: 2 (spec ambiguity — requirement literal amended)
**Spec reference**: §Record Schema, §`commit` Group, §Schema Lint
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

### Q-IMPL-HARNESSP4-004: clause (a) of `implied.fix` counts deciding gates, not records
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Implication-Derived `expected` and the Headline, clause (a) — "#records with `gate.decision` ∈ {loop-back-to-fix, fix, redo}"
**Decision**:

§Writer gives a verifier, review or red record the `gate.decision` of the gate
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

### Q-IMPL-HARNESSP4-005: `--lint` reason members, the `proceed`/equal-heads exemption and the `--plan` shortfall operands
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Record Schema (`dispatch.reason` row), §Schema Lint (cross-field row), §`--plan` Floor
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

### Q-IMPL-HARNESSP3-018: `summarize` derives a session boundary from a `dispatch.seq` reset
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Records-vs-Expected in `summarize`
**Decision**:

No record carries a session id, so the reader derives one: within a
(`cycle.workstream`, `cycle.research_id`) group ordered by `ts_dispatch`, a new
session opens at the first record and at every record whose `dispatch.seq` does
not exceed its predecessor's — `seq` is 1-based per session (§Record Schema), so
a reset is the only observable session boundary. `expected` is then the highest
`seq` in the session and `gap = expected - recorded`. Purely reader-side; no
record key is added and no side channel from the orchestrator is used
(Q-IMPL-HARNESSP3-006).
**Date**: 2026-09-18 (implement stage, Chunk 4)
