# Leaf Return Contract — `RETURN:` Block Semantics

Detail behind `../SKILL.md` §Leaf Return Contract (the stub keeps the block
shape, the status enum and a summary). Read on demand when dispatched by
`orchestrate`. Contracts: REQ-HARN-005, -009, -010,
`docs/spec/harness-return-contract.md`; keys, types and consumers in
`orchestrate/references/return-contract.md` §1; ledger and checkpoint
detail in `stuck-detection.md`.

---

## Key-by-key semantics

- **`failures` are one-line** (REQ-HARN-010): each entry is
  `{test, kind, message, location}` — `test` the test id or gate command,
  `kind` ∈ {`assertion`, `error`, `lint`, `type`, `build`}, `message` the last
  frame on one line, ANSI-stripped, ≤ 200 chars (truncate with `…`, never wrap),
  `location` `path:line` where known. **Never** put a traceback or raw tool
  output in the return; it is regenerable by re-running `test`.
- **`ledger` / `verified_do_not_touch`** carry the Step 3 attempt ledger
  verbatim — one line per value, newest last — and the do-not-touch path list.
  They are the ledger's only durable trace besides the checkpoint.
- **`status: BLOCKED` / `BUDGET_EXHAUSTED`** — the circuit-break checkpoint is
  composed from `failures`, `ledger` and `open_questions` per the Step 3
  mapping table. A sequential dispatch writes it into the plan itself; a
  fan-out leaf returns the fields and the orchestrator applies the note
  (`orchestrate/references/fan-out.md` §3e). `BUDGET_EXHAUSTED` requires
  `budget_consumed` in the dispatched `Budget:` units (`stuck-detection.md` §Budget
  exhaustion).
- **`open_questions`** are one line each and cite the Q-IMPL id filed for the
  ambiguity (e.g. `"spec §Gap report silent on overlapping windows — filed
  Q-IMPL-021 (Tier 2)"`).
- **`tasks_completed` / `traceability_fills`** carry the plan `[x]` marks and
  Test/Implementation column fills when the dispatch bars you from writing the
  shared plan/traceability files (fan-out worktree pin); otherwise they mirror
  what you wrote.
- **`blocked_writes`** carries the full content of any file a harness policy
  refused to write, labeled by target path, so the orchestrator can persist it.
