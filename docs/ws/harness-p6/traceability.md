---
workstream: harness-p6
last_updated: 2026-09-20
---

# Traceability — harness-p6

Rows owned by the `harness-p6` workstream (per `docs/spec/ws-traceability.md`).
One row per requirement this workstream delivers; Spec / Test / Implementation /
Verified are filled by `sdd-specs`, `sdd-implement` and `sdd-verify`. The shared
aggregate `docs/requirements/traceability.md` is regenerated from this file and
its siblings — never hand-edited.

`Verified` takes the values of `docs/spec/ws-traceability.md` §Legal `Verified`
Cell Values — `pass | fail | pending-red | descoped`. The DONE rule for this
cycle (kickoff §Decided at DISCUSS): every row reads `pass`; nothing closes as a
deliberate `fail`, and an item that cannot be exercised is descoped at replan.

**Terminal cycle.** `harness-p6` is the terminal cycle of the harness-hardening
series (kickoff §Decided at DISCUSS). No row may be closed by carrying it to a
successor workstream; an item too large to fix triggers a replan inside this
cycle. There are no carried rows from a previous workstream.

**Confidence carried from RS-HARNESSP6-001.** The three L2 rows
(REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-001, REQ-ORCH-HARNESSP6-002) rest on
the findings' **Medium**-confidence Q4: the cluster rule reuses an exercised
parser but has never been replayed against a real finding set, and L2's firing
rate is unmeasured. Their verification should not be treated as routine.

| Requirement | Spec | Workstream | Test | Implementation | Verified |
|-------------|------|------------|------|----------------|----------|
| REQ-GC-HARNESSP6-001 | drift-sweep.md | harness-p6 | Chunk 1 task 2: `python3 tools/sdd-gc.py --self-test` exits 0 with `test_stale_chain_skips_closed_workstream` (self-test section 9) — on a fixture whose alpha plan raises both plan-level sub-kinds, a workstream whose `verification.md` is `status: pass` raises neither, while `status: fail`, `status: pending-red` and an absent `verification.md` each raise both, and the shared-spec sub-kind on `docs/spec/a.md` survives the skip. Chunk 1 task 3: `python3 tools/sdd-gc.py --report` exits `OK` and, with both sides derived from that same run, every workstream whose own `verification.md` reads `status: pass` in that run (harness-p3 and harness-p4 among them) contributes zero `[stale-chain]` findings located at its `plan.md`; no count is pinned as a literal | tools/sdd-gc.py: `Gc.ws_closed()` — the marker-4-guarded per-workstream predicate reading `docs/ws/<id>/verification.md` frontmatter `status:` — and the `closed` guard in `Gc.sweep_stale()` over both plan-level `_stale()` call sites (plan older than a traced spec; plan older than a traced requirement category file); self-test section 9 in `self_test()`. A scoping predicate on the existing rule only: no new rule id, no severity change, no allowlist, no file exempted by name, and never consulted under marker 3 | |
| REQ-GC-HARNESSP6-002 | drift-sweep.md | harness-p6 | Chunk 2 task 4: `python3 tools/sdd-gc.py --self-test` exits 0 with `test_shared_spec_staleness_folds` (self-test section 10) — a fixture spec requiring three ids from one re-dated category file yields exactly one `[stale-chain]` finding whose message names all three ids, and a second stale category file for the same spec yields a second finding naming a distinct category file. Chunk 2 task 5: `python3 tools/sdd-gc.py --report`, with both sides derived from that same run, reports as many spec-versus-requirement `[stale-chain]` findings as there are distinct `(spec, category file)` pairs those findings name; neither side is pinned as a literal | tools/sdd-gc.py: the `spec_stale` accumulator in `Gc.sweep_stale()` keyed by `(downstream spec, upstream category file)` with the triggering ids collected via the new `Gc._is_stale()` predicate, emitted as one finding per pair after the plan walk (so a spec traced by several workstreams still yields one finding per pair); every `(spec, id)` pair is still evaluated — the fold is presentation only; self-test section 10 in `self_test()` | |
| REQ-GC-HARNESSP6-003 | drift-sweep.md | harness-p6 | Chunk 2 task 4: `python3 tools/sdd-gc.py --self-test` exits 0 with `test_shared_spec_staleness_severity` (self-test section 11) — on the same fixture the folded shared-spec findings carry the `INFO` prefix while the plan-level finding on the open workstream `alpha` carries `WARN`. Chunk 2 task 6: `python3 tools/sdd-gc.py --report` exits `OK` with zero `[stale-chain]` **warnings** and every spec-versus-requirement `[stale-chain]` line emitted at `info`, both derived from the same run as the pair check; the number of info lines is a run-time property of the corpus and is deliberately not pinned | tools/sdd-gc.py: the `severity` argument on `Gc._stale()` (default `warn`, so plan-level and verification-level findings are unchanged) and the `info` severity plus dedicated `SPEC_STALE_FIX` text on the folded shared-spec emission in `Gc.sweep_stale()`; the module docstring sweep-7 row and the `--help` epilog state the split and that the class is not routed at DONE. docs/spec/drift-sweep.md §Sweep Table row 7 and §Routing at DONE carry the split — the shared-spec sub-class appears in no routing row and is offered no `record` option; self-test section 11 in `self_test()` | |
| REQ-GC-HARNESSP6-004 | drift-sweep.md | harness-p6 | | | |
| REQ-HARN-HARNESSP6-001 | harness-write-scope.md | harness-p6 | Chunk 3 task 5: five new `tools/sdd-scope-check-selftest.py` scenarios — G1 (read-only leaf runs `git stash` then `git stash pop` → `GIT_STATE` on clause (i) `ORIG_HEAD` drift, `SCOPE: VIOLATION`), G2 (`git stash` then `git stash drop` → `GIT_STATE` on clause (ii), the reverse porcelain delta naming the paths whose work vanished, `SCOPE: VIOLATION`), G3 (implement leaf commits a path already dirty at `snapshot(before)` → `SCOPE: CLEAN`, the committed delta subtracted), G4 (orchestrator fan-out merge between two dispatches → `SCOPE: CLEAN`, outside any leaf's window), G5 (`ORIG_HEAD` absent in both raises nothing; present in `after` only raises `GIT_STATE`). Chunk 3 task 6: `python3 tools/sdd-scope-check-selftest.py` exits 0 with those five scenarios plus every fixture present in the fixture list captured at the task's own start still passing — no fixture count is pinned as a literal | `tools/sdd-scope-check-selftest.py`: the `GitState` record and `git_state()` helper (stash count, `--abbrev-ref HEAD`, `--verify --quiet ORIG_HEAD` with absence as the legal empty value), the `state_before` argument and the two-clause comparand inside the existing `observe()` window (no second window), `Observation.git_state`, the `GIT_STATE` line rendered in `render()` parallel to `HISTORY_REWRITE` above the path list and counted into `SCOPE: VIOLATION (N paths)`, and scenarios `scenario_g1`..`scenario_g5`. `skills/sdd-orchestrate/references/write-scope.md`: §3 git-state observation block (three extra plumbing reads, reverse-delta subtraction, the legitimate cases), §5 `GIT_STATE` line and its `N` contribution — no new own-line gate token, REQ-ORCH-034 signal order unchanged — with the stash limitation in §5 retired, and the §8 option row `restore │ accept (note) │ stop` with `proceed` withheld | |
| REQ-HARN-HARNESSP6-002 | harness-loop-control.md | harness-p6 | | | |
| REQ-LINT-HARNESSP6-001 | skill-lint-v5.md | harness-p6 | | | |
| REQ-LINT-HARNESSP6-002 | skill-lint-v5.md | harness-p6 | | | |
| REQ-LINT-HARNESSP6-003 | skill-lint-v5.md | harness-p6 | | | |
| REQ-ORCH-HARNESSP6-001 | harness-loop-control.md | harness-p6 | | | |
| REQ-ORCH-HARNESSP6-002 | harness-loop-control.md | harness-p6 | | | |
| REQ-PLAN-HARNESSP6-001 | plan-management.md | harness-p6 | | | |
| REQ-REQ-HARNESSP6-001 | requirements-artifacts.md | harness-p6 | | | |
