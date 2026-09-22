# Fixtures

Frozen real-world artifacts kept as test inputs. Unlike the synthetic records
built inline by each tool's `--self-test`, these are **captured from live runs**
and are never regenerated — their value is that they contain defects exactly as
they occurred.

Treat every file here as read-only evidence. Do not repair, reformat or migrate
one in place; a tool that learns to handle a defect should be tested *against*
the fixture, not by editing it.

---

## `telemetry-harness-p4-2026-09-19.jsonl`

**Provenance.** A byte-identical copy of `.sdd/telemetry.jsonl` as it stood at
the close of the `harness-p4` cycle — `head -67` of the live file, cut
2026-09-20 by the orchestrator during the `harness-p5` cycle (operator task O1;
leaves never read `.sdd/`). 67 records: `harness-p3` migrated at lines 1–20,
`harness-p4` at lines 21–67 (session 1 is 20 records at `v: 1`; session 2 is 27
records at `v: 2`, starting `seq` 8). The last record is `seq` 34,
`kind: review`, `stage: verify` — p4's final verify review, which is the DONE
boundary. `harness-p5` begins at line 68 of the live file and is excluded.

    sha256  ff5cf2864abc74c2c05449b86e5117f5c4ed8851b6b5f96617859b8b061ef370

**Correction (2026-09-20).** The `harness-p5` plan and
`docs/requirements/functional/telemetry.md` originally specified this cut as
**61 lines** with the composition "p4 session 1 seq 1–13, p4 session 2 seq
1–28". Both were wrong; the measured boundary is 67. The correction is
consequence-free: `python3 tools/sdd-telemetry.py --lint` produces
byte-identical output on a 61-line and a 67-line cut — 65 findings, 4 warnings,
the same three `[cross-field]` records at `seq` 21, 24 and 27 — so no acceptance
number moved. [Re-measured 2026-09-20 after Chunk 4's reader fixes: **62 findings, 4 warnings** — the `v: 2`-only equal-heads guard correctly removed the three findings at `seq` 2, 4 and 6. 65/4 is the figure as measured before those fixes; the equivalence claim is unchanged — both cuts still produce byte-identical output, with the same three `[cross-field]` records at `seq` 21, 24 and 27.] The six extra records (`seq` 29–34: p4's verify stage, two red
rounds, two reviews) add no lint finding, and the 67-line cut is the more
faithful one because the 61-line cut silently truncated the verify stage.

**Why it is here.** It is the evidence behind the six telemetry writer/reader
findings in scope for `harness-p5` (see
`docs/requirements/functional/telemetry.md` REQ-TELEM-HARNESSP5-001…008).
Findings 1, 2, 3 and 5 are reproduced on it; 4 and 6 are synthetic self-test
cases. It is a **snapshot**: the live file keeps growing, this one does not, and
it is never edited to satisfy a code change.

## `telemetry-harness-p3-2026-09-18.jsonl`

**Provenance.** A byte-identical copy of `.sdd/telemetry.jsonl` as it stood at
the close of the `harness-p3` cycle, 2026-09-18, repo `e0d71ef`. 20 records,
`seq` 1–20 contiguous, `cycle.research_id: RS-HARNESSP3-001`.

    sha256  7e20b6307da09355f9aee504c451f0ed59e79ef9a33861cd72f370ea84af9237

**Why it is here.** `.sdd/` is gitignored, so the live file exists on one machine
and in no commit. It is the only evidence behind findings P1–P3 in
`docs/ws/harness-p3/verification.md` §Post-DONE Findings. This copy makes those
failure modes reproducible after the live file is eventually repaired or lost.
It is a **snapshot**: the live file keeps growing, this one does not.

**The three failure modes it preserves** — all deliberate, none to be fixed here:

| Mode | Where | What |
|---|---|---|
| Out-of-domain `dispatch.chunk` | `seq` 6–13 | the header **string** `"Chunk 0"`…`"Chunk 7"` where `docs/spec/telemetry.md:92` fixes the domain to `int or null`. Root cause P1: the only worked example in both the spec and the writer doc showed `"chunk":null`, so the non-null case was specified in prose only, while the rendered dispatch line `Chunk: Chunk 0` sat in the writer's hand. |
| Out-of-domain `dispatch.kind` | `seq` 20 | `"gate"`, which the schema does not admit (`pipeline \| fix \| fanout_leaf \| verifier \| review \| red`). Finding P3: the R1 fix validates `chunk` only, so this still passes silently. |
| Missing appends the backstop cannot see | whole file | **zero** `verifier` and **zero** `fix` records exist, though the implement stage ran 8 chunk verifiers and 3 redos (~11 unwritten appends). Finding P2: `records-vs-expected` derives `expected` from the highest `seq`, so a writer that never appends *and* never increments reports no gap. `seq` 18 is also a `fix` dispatch recorded as `kind: "pipeline"` — legal, but the wrong choice. |

**Suggested uses.** A regression test that `summarize` reports
`out-of-domain dispatch.chunk: 8 record(s)`; a test for the P3 remedy (validate
every field against its declared domain — a `kind` check should flag `seq` 20);
a test for the P2 remedy (an `expected` derived from an independent source should
report a gap here, where the current one reports none); and, once a migration
exists, an input whose expected output is a per-chunk block stamped **partial**
rather than one that looks complete.

Quick look:

```bash
python3 tools/sdd-telemetry.py summarize --file tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl

python3 -c "import json,sys
for r in map(json.loads, open(sys.argv[1])):
    d = r['dispatch']
    print(d['seq'], d['kind'], repr(d['chunk']))
" tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl
```

---

## `arbitration-harness-p4-regen-2026-09-19/`

**Provenance — a git capture, not a reconstruction.** `before.md` and `after.md`
are `git show` captures of `docs/ws/harness-p4/plan.md` at two commits of this
repository, taken 2026-09-19:

| File | Capture | sha256 |
|---|---|---|
| `before.md` | `git show 82d0af0:docs/ws/harness-p4/plan.md` | `ec1bc1bdc7cee4787dd209c9361a7d522b62ed072ac8deae0f546bf13a569e25` |
| `after.md` | `git show 3772574:docs/ws/harness-p4/plan.md` | `2a5c40ac21e60ddd7f7464fa8bfab6d65f588ae23686d21dc0d3de002dbced6d` |
| `round-1.txt` | authored — `VERDICT: APPROVE_WITH_FIXES`, C/M lines on two **changed** sections | `d7625fba849557433e41e500838279bcff10f029b29e6d31e58e709d315345d8` |
| `round-2.txt` | authored — two Material lines on the plan's **unchanged** `§Conventions` and `§Verification Hand-off` | `ebd2c691a615e83159dd677f750416a074565784f602732f37b30b736dd3cca9` |
| `dispatch.txt` | authored — observed writes `{docs/ws/harness-p4/plan.md}`, `regenerate: true`, `by: leaf` | `95b8e5a1039835feca64870e8bb83d841cb806e5149df4d15bbee3ad887b1a73` |

The two shas are **provenance, not a runtime dependency**: the captured bytes
live here, so the fixture stands even if the commits are ever unreachable.

**Why it is here.** It is the deterministic evidence that closes the carried
arbitration rows REQ-ARB-HARNESSP3-001 and REQ-ARB-HARNESSP4-001 — the p4 live
exercise was non-discriminating — without a second live fix loop
(`docs/spec/arbitrated-handoff.md` §Offline Arbitration Fixture). The pair's
diff is broad (35 hunks, `§(preamble)` through `§Replan Triggers`), yet it
discriminates because the two sections round 2 keys on, `§Conventions` and
`§Verification Hand-off`, are **byte-identical** across the capture: under the
Approved diff-based `W_N` those keys are new ground (`class b`, two annotated
keys), while under the rejected provenance reading `regen[1] = (plan.md, *)`
they would be immune (no token).

**How it is used.** `tools/sdd-scope-check-selftest.py --self-test` replays it as
scenarios `A1` (the discriminating case, both readings printed side by side),
`A2` (round-2 findings in changed sections only → no token either way) and `A3`
(a key on an untouched second file → `class b` under both readings), plus two
mutation scenarios that prove A1 cannot pass vacuously: `A1m-i` deletes a
`round-2.txt` line and `A1m-ii` flips `§Conventions` to a changed section. Both
mutations operate on in-memory copies written into a throwaway repo — the files
here are never modified.

```bash
python3 tools/sdd-scope-check-selftest.py --self-test -v
shasum -a 256 tools/fixtures/arbitration-harness-p4-regen-2026-09-19/*
```

---

## `check3-declared-convention-2026-09-22/`

**Provenance — authored, not captured.** The two-sided fixture
`chunk-close-review.md` §Checklist's dated acceptance bullet requires
(REQ-CHKC-004 as amended, workstream `pipeline-observability`, Chunk 1 task 7):
two plan-chunk fragments of the same shape whose only difference is the
module they name, and the derivation command's expected output beside them.

| File | What |
|---|---|
| `chunk-gc.md` | a chunk whose module is `plugins/sdd/tools/gc.py` — **in** the derived set (a commit-gate `entry:`), with no test file importing from it → Check 3 reports **no** advisory |
| `chunk-scope-check.md` | the same chunk with `plugins/sdd/tools/scope-check-selftest.py` — named by `CLAUDE.md` in prose only, **outside** the set → Check 3 still reports **one** advisory |
| `derived-set.txt` | the derivation command's output on this tree on 2026-09-22: `gc.py`, `skill-lint.py`, `telemetry.py` — a reference value, never a pin |
| `check3.sh` | runs the derivation, diffs it against `derived-set.txt`, and decides Check 3 for the chunk's `**Module**:` line (exit 0 pass, 2 advisory) |

**Why it is here.** The identical coverage advisory fired on 9 of 9
consumer-geometry chunks against modules whose self-tests `CLAUDE.md` names
and whose commit gate runs; the clause that stops it must be shown to
discriminate — a fixture on which the advisory is absent for the covered
module and present for the uncovered one — rather than to silence Check 3.

```bash
sh plugins/sdd/tools/fixtures/check3-declared-convention-2026-09-22/check3.sh \
   plugins/sdd/tools/fixtures/check3-declared-convention-2026-09-22/chunk-gc.md            # exit 0
sh plugins/sdd/tools/fixtures/check3-declared-convention-2026-09-22/check3.sh \
   plugins/sdd/tools/fixtures/check3-declared-convention-2026-09-22/chunk-scope-check.md   # exit 2
```

## telemetry-flat-2026-09-22.jsonl — frozen flat-record fixture (OP-1, pipeline-observability)

Every `v`-less line of the live `.sdd/telemetry.jsonl` on 2026-09-22, cut once
by the orchestrator before Chunk 2 of the `pipeline-observability` plan and never
modified afterwards. Chunk 2's `flat-cg` migration self-test reads it. Counts are
derived at run time by the case, never pinned here.

sha256: `de57b9608ba3a78fbcdbc2525b8e91870481fe2bc3ecfbfa10eef4a4f7afd358`
