# Fixtures

Frozen real-world artifacts kept as test inputs. Unlike the synthetic records
built inline by each tool's `--self-test`, these are **captured from live runs**
and are never regenerated — their value is that they contain defects exactly as
they occurred.

Treat every file here as read-only evidence. Do not repair, reformat or migrate
one in place; a tool that learns to handle a defect should be tested *against*
the fixture, not by editing it.

---

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
