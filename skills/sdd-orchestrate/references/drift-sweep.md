# Drift Sweep Cadence — sdd-orchestrate reference

Procedure text for the two moments the driver runs `tools/sdd-gc.py`
(`docs/spec/drift-sweep.md` §Cadence, §Routing at DONE; REQ-GC-HARNESSP2-005,
-006; the gc half of REQ-SKILL-HARNESSP2-004). `../SKILL.md` §Phase Detection
(entry) and §Transition (DONE) carry a stub each and point here. The `GC:`
gate line is defined by that spec and nowhere else; this file only says when
to run the tool, how to render its output and where each finding class goes.

gc is a **sweep, not a stage**: it never runs between stages, never blocks a
gate (a fail at entry is informational), is never driven by `/schedule` or
`/loop` — a routine runs outside any cycle, so its fix step would have no gate
and no committer respecting commit ownership (REQ-HARN-024) — and never
creates or modifies a plan task (a task added to a complete plan would flip
phase detection back to implement; REQ-ORCH-014). It never reads the telemetry file (`telemetry.md`) and is
never a phase-detection input.

## 1. Entry — before the picker (marker `4`) / before phase detection (marker `3`)

```
run:     python3 tools/sdd-gc.py --report            # exit 0 | 1 | 2
render:  GC: clean                                    # exit 0 and summary `OK: … 0 warning(s) …`
         GC: F fail, W warn — run tools/sdd-gc.py --report   # otherwise (exit 1, or warnings)
         GC: unavailable (<first stdout line>)        # exit 2 — usage / repository error
then:    open the workstream picker (marker 4) / derive loop position (marker 3) REGARDLESS
```

`F` and `W` are read from the tool's own summary line (`FAIL: F finding(s), W
warning(s), I info` / `OK: N sweep(s) clean, W warning(s), I info`) — never
recounted from prose. The line is one line of gate text; it does not pause
the operator, does not ask a question and is not written anywhere. Under
marker `4` the entry run is unscoped (all workstreams) so a stale sibling
workstream is visible before the picker.

## 2. DONE — after the verify stage passes review and the operator approves

```
run:     python3 tools/sdd-gc.py --report [--workstream <id>]   # marker 4: the completed workstream
render:  the tool's findings verbatim (linter shape; WARN / INFO prefixes) + its summary line
route:   per the table below, one decision per finding class
```

| Finding class | Rules | Gate action |
|---|---|---|
| mechanical | `xlink-dead` (unique resolution), `index-requirements` row, `traceability-aggregate`, `plan-history-name` | `python3 tools/sdd-gc.py --fix <rule>`; the **operator** reviews the printed paths and commits the rewrite (REQ-HARN-024) — the driver never commits a `--fix` |
| needs a decision | `qimpl-broken-ref`, `stale-chain`, `traceability-aggregate` (when the per-ws inputs themselves look wrong), `spec-approval`, `trace-empty`, `kickoff-fields`, `id-missing`, `qimpl-undefined`, `index-research`, `lint` pass-through | `record \| ignore` (§3) |
| out of scope | sweep 15 (skill-text drift from spec wording; semantic orphaning — named in `--help`) | note only |
| informational | `qimpl-unreferenced` | shown, no decision |

**Dates are never auto-fixed.** `stale-chain` always routes to `record | ignore`;
the owning skill updates `last_updated` when it next touches the artifact
(`--fix` refuses `stale-chain` with exit 2 — editing a date mechanically would
mask the staleness it signals).

## 3. `record` — the only write, in an existing section

On `record`, append one line per recorded finding under the completed cycle's
`verification.md` `## Next Steps` (marker `4`: `docs/ws/<id>/verification.md`;
the section is part of the `sdd-verify` Step 6 template):

```
- gc <rule>: <file:line> — <fix>
```

`<file:line>` and `<fix>` are copied from the finding (`<file>` alone when the
finding has no line). The append is orchestrator bookkeeping **outside any
observed window** (`references/write-scope.md`) and is committed with the
cycle's artifacts. It is read by the next cycle's DISCUSS.

Invariants (`test_record_routing`, `docs/spec/drift-sweep.md` §Verification):
after a DONE gate with two recorded findings, `## Next Steps` has exactly two
new `- gc …` lines; `plan.md` is byte-identical; `git ls-files docs/` gains no
path (no `docs/gc/`, no issues file — REQ-HARN-027, REQ-ORCH-004). `ignore`
writes nothing.

## 3b. Convention: never quote another repository's `Q-IMPL` ids (REQ-GC-HARNESSP3-001)

Prose in this repository that describes **another** repository's artifacts — a
toy clone, an evidence record, a pilot log — must not quote that repository's
`Q-IMPL` id tokens verbatim; paraphrase them, or wrap them in a fenced code
block. `tools/sdd-gc.py`'s `qimpl-undefined` rule is **unchanged** and behaved
correctly when it flagged such a mention: those ids genuinely are undefined in
this corpus, and "ids that look local" is not decidable from text. The escape
hatch is therefore the **fenced span** — the sweep's Q-IMPL reference exclusion
already skips fenced content — never a gc allowlist entry
(`docs/spec/drift-sweep.md` Q-IMPL-HARNESSP3-012).

## 4. What the driver never does with gc

- run it between stages, or make a `proceed` depend on its exit code;
- schedule it (`/schedule`, `/loop`) or run `--fix` unattended;
- commit a `--fix` rewrite itself — the operator owns that commit;
- turn a finding into a plan task, a `docs/gc/` file or an issues list;
- pass its output to a leaf or a reviewer as context (paths only, as ever).

The optional pre-commit profile `python3 tools/sdd-gc.py --fast` (lint +
cross-links + Q-IMPL, no date or history walk) is a repository choice, not a
driver step.
