---
status: Approved
last_updated: 2026-09-17
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

One JSON object per line. `v` is the schema version and is `1` for this spec.
Every value is a **count, enum, sha, boolean, null or ISO-8601 UTC timestamp**;
the record never contains a finding line, a path list, file content, reviewer
reasoning, or any other prose (REQ-ORCH-012/013). The key set is fixed; field
names are as below.

| Group | Key | Type / domain | Source (gate signal) |
|---|---|---|---|
| — | `v` | int, `1` | constant |
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
| | `reason` | repair-packet `reason` enum or null | `harness-return-contract.md` §Repair Packet (plus `RED_BREAK`, `adversarial-verify.md`) |
| | `budget` | budget object (below) | parsed from the dispatched `Budget:` line |
| | `write_scope_n` | int | number of declared scope globs |
| `return` | `status` | `COMPLETE` \| `PARTIAL` \| `BLOCKED` \| `BUDGET_EXHAUSTED` \| `MALFORMED` | `RETURN.status`; `MALFORMED` when the block failed to parse |
| | `budget_consumed` | budget object + `self_reported: true` | `RETURN.budget_consumed` |
| | `files_written_n`, `commits_n`, `tasks_completed_n`, `failures_n`, `ledger_n`, `open_questions_n`, `blocked_writes_n` | int | lengths of the corresponding `RETURN` lists |
| | `warnings` | list of enums ⊆ {`KEYS_MISSING`, `MULTIPLE_STATUS`, `FOREIGN_TOKEN`} | parser warnings (`return-contract.md` §1) |
| `scope` | `token` | `CLEAN` \| `VIOLATION` \| null | `SCOPE:` line (null for a dispatch with no scope check) |
| | `in`, `advisory`, `out` | int | tag counts in the write-scope block |
| | `history_rewrite` | bool | `HISTORY_REWRITE` finding present |
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
| `git` | `head_before`, `head_after` | short sha | the snapshot pair's `HEAD_before` / `HEAD_after` (`dispatch-snapshot-base.md`) |

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
| `TELEMETRY: WRITE FAILED` | the previous append raised an error |
| `TELEMETRY: OFF` | first gate of a cycle in which the operator disabled telemetry |
| `TELEMETRY: .gitignore updated` | the orchestrator added the `.sdd/` ignore line |

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
python3 tools/sdd-telemetry.py summarize [--file .sdd/telemetry.jsonl] [--workstream <id>] [--since <ISO>]
```

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
- [ ] Orchestrator-only, one append after each gate, never truncated except the leaf-write revert; `TELEMETRY: WRITE FAILED | OFF | .gitignore updated` lines; default on with KICKOFF opt-out; one file per repository (REQ-TELEM-HARNESSP2-004)
- [ ] Third observation (line count + entry list) and the `OUT .sdd/telemetry.jsonl (+k records, leaf write — reverted)` string defined once; revert to before-count; scope self-test scenario F7 (REQ-TELEM-HARNESSP2-005)
- [ ] Phase-detection input table as in §Non-Interference Proof; `rm -rf .sdd/` is behaviour-neutral (REQ-TELEM-HARNESSP2-006)
- [ ] `FORBIDDEN` row `\.sdd/` with the three-file `allow_files` allowlist, raw-text scan, stated reason and fix (REQ-TELEM-HARNESSP2-007, REQ-LINT-HARNESSP2-002)
- [ ] `.sdd/` gitignored at the repo root; `git ls-files docs/` unchanged by a cycle (REQ-TELEM-HARNESSP2-008, REQ-HARN-027)
- [ ] `tools/sdd-telemetry.py summarize` with the columns above, `--help`, `--self-test`, unknown-`v` tolerance; not invoked by any skill (REQ-TELEM-HARNESSP2-009)
- [ ] `references/telemetry.md` exists and resolves; `SKILL.md` stub ≤ 10 lines; no template names `.sdd/` (REQ-SKILL-HARNESSP2-001)
- [ ] `USAGE.md` has a section per new signal; `CLAUDE.md` diff is one paragraph and the four-layer bullet is unchanged (REQ-SKILL-HARNESSP2-008)
- [ ] Scorer derivation table present and complete against `evaluation.md` §Scorer Fields
- [ ] `python3 tools/sdd-skill-lint.py` exits 0; `--self-test` exits 0

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

## Open Questions

1. **File locking for concurrent sessions.** Default: none; torn lines are
   skipped by the reader and counted.
2. **`gate.decision` enum completeness** as new gate options appear. Default:
   the normalisation table above; an unrecognised option is recorded as
   `other` with no text, and adding a row to the table is a change to this spec.
3. **Should `ts_*` be stamped with sub-second precision?** Default: whole
   seconds (`date -u +%Y-%m-%dT%H:%M:%SZ`); dispatch wall times are minutes.
