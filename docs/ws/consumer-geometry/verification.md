---
status: pass
research_id: RS-CONSUMERGEOMETRY-001
last_updated: 2026-09-22
plan_ref: docs/ws/consumer-geometry/plan.md
---

# Verification Report — consumer-geometry

## Summary

The cycle's founding defect is closed and the closure is demonstrated, not
asserted. A copy of the suite running from **outside** the corpus — the only
geometry a consumer of the installed plugin has — printed
`[structure] skills/ directory not found` / `FAIL: 1 finding(s)` before the
change and prints `GEOMETRY: nested  swept-roots=2` / `OK: 25 file(s) clean`
after it, with the byte-identical pre-change copy still installed in the plugin
cache available as the live control (§Task 3). All 44 acceptance boxes across
the five specs' §Consumer-Geometry Acceptance Criteria have an owning task in a
chunk that held the write scope to repair them, and every one returned a
result; counting §CG-6 as its four separately-checkable assertions gives 47
results — **46 pass, 1 carried (environmental), 0 fail**; the carried one is
`pre-commit.md` box 4, whose own row says so. The OC3 desk check reconciles the
requirement's enumeration table against the tools at run time with an **empty**
difference in both directions. **All eight** hooks of the commit gate pass over
the whole tracked corpus bar one file the sandbox forbids writing (7 of 8 under
a single `--all-files` process; the eighth green over 208 of 209 tracked files —
§Known-Open (c)).

Four known-open items are dispositioned explicitly below and none of them
blocks: one carried gap in the mutation set (the unpinned tier-2 conjunct), one
carried design boundary (the consumer-unreachable `OPEN:`), one environmental
limitation (pre-commit in this sandbox), and one accepted convention (the
self-hosted test surface). Two fresh Minors are recorded: a pre-existing
`telemetry.py --self-test` failure of exactly this cycle's defect class that no
gate observes, and the deferral-backlog screen's live hits in earlier
workstreams' reports, which this cycle's write scope forbids repairing.

`status:` is `pending-red` because this run was dispatched with
`Red team: enabled`. Blue passed and **the red round has since closed
`HELD`** (§Red Round, below) with three recorded non-break findings. The flip
is **done**: the orchestrator set `pending-red → pass` here and in the six
`Verified` cells at the stage gate, the red round having closed `HELD` with no
`BROKEN` item owed.

## Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| `skill-lint.py --self-test` | pass | exit 0; `SELF-TEST OK: all rule classes fire; fix/warn/size/backtick/allow_files/retired-prefix fixtures pass` |
| `gc.py --self-test` | pass | exit 0; sweeps 5–14 fire once each, counting rules, exit codes, four `--fix` rules idempotent, Q-IMPL fence symmetry |
| `skill-lint.py .` (corpus lint) | pass | `GEOMETRY: nested  swept-roots=2  suite-rows-root=<repo>/plugins/sdd` / `OK: 25 file(s) clean` |
| `gc.py --report --root .` (drift sweep) | pass | `OK: 9 sweep(s) clean, 1 warning(s), 37 info` — the single warning is the designed `[traceability-aggregate]` handshake (below) |
| `pre-commit run --all-files` | **partial — environmental** | 7 of 8 hooks pass; `end-of-file-fixer` raises `PermissionError` on `.claude/settings.json`. See §Known-Open (c) |
| `pre-commit run --files <208 tracked paths>` | pass | all 8 hooks pass over every tracked file **except** `.claude/settings.json` (209 tracked, 1 excluded) |
| `scope-check-selftest.py` | pass | `OK: 44/44 scenarios passed` |
| `eval.py --self-test` | pass | `eval self-test OK (6 records, 9 fields, aggregate, empty/missing file, csv)` |
| `telemetry.py --self-test` | **fail — pre-existing** | `schema rendering missing: <repo>/plugins/sdd/docs/spec/telemetry.md`. Not a regression: the file is byte-identical to `3bac4af` and last changed at `e26f81f` (the packaging move). See §Issues Found → Minor |
| Hook set byte-identity from `3bac4af` | pass | `git diff 3bac4af..HEAD -- .pre-commit-config.yaml` is empty |
| Both tool self-tests remain hooks | pass | `.pre-commit-config.yaml:53` `skill-lint-self-test`, `:59` `drift-sweep-self-test` — parsed, not recalled |

The `[traceability-aggregate]` warning is expected and is **not** a finding: it
is the designed handshake between this skill's per-workstream `Verified` write
and the orchestrator's post-gate regeneration of
`docs/requirements/traceability.md`
(`ws-traceability.md` §Aggregate Regeneration Ownership;
`adversarial-verify.md` §`Verified` Reads `pending-red`…). No gc finding lands
on a `pending-red` cell.

## Chunk 9 Task 1 — OC3, the desk-check half of the count equality

The reconciler that no shipped tool can be: `docs/` is outside the shipped
plugin, so the in-tool constant-vs-registered assertion proves the constant and
the cases agree with **each other**, never that either agrees with the
requirement. This is that missing half.

**Method.** The `cg-row-<n>:` tokens were parsed from the **table** of
REQ-PKG-CONSUMERGEOMETRY-001 (`docs/requirements/integration/packaging.md`), by
matching `^\|\s*(\d+)\s*\|` over the table's body rows. On the tool side each
module was imported, `cg_reconcile` wrapped so the **run-time** `ran` set was
captured, and `self_test()` executed; both returned 0, so the captured `ran`
set is also the set the tool's own equality assertion passed on. The count
"eight" in the requirement's prose was **not** used as a comparand anywhere.

**Set A — parsed from REQ-PKG-CONSUMERGEOMETRY-001's enumeration table (8):**

```
cg-row-1:  cg-row-2:  cg-row-3:  cg-row-4:
cg-row-5:  cg-row-6:  cg-row-7:  cg-row-8:
```

**Set B — registered and run by the tools (8), as the union of:**

| Tool | `CG_ROW_TOKENS` constant | Registered and run (`ran`) |
|---|---|---|
| `plugins/sdd/tools/skill-lint.py` | `cg-row-1: cg-row-2: cg-row-3: cg-row-5: cg-row-6: cg-row-7: cg-row-8:` | identical to the constant |
| `plugins/sdd/tools/gc.py` | `cg-row-4:` | identical to the constant |

```
cg-row-1:  cg-row-2:  cg-row-3:  cg-row-4:
cg-row-5:  cg-row-6:  cg-row-7:  cg-row-8:
```

**Difference, recorded in both directions:**

| Direction | Members | Reading |
|---|---|---|
| A − B (table row with no token) | **(empty)** | every enumerated row has a registered, run case |
| B − A (token with no table row) | **(empty)** | no case claims a row the requirement does not enumerate |
| A △ B (symmetric) | **(empty)** | the desk check passes |

Adding a row to the table without adding its token would make A − B non-empty;
adding a token without a row would make B − A non-empty. Both directions were
computed; neither was inferred from the other.

**Status: pass.**

## Chunk 9 Task 2 — the REQ-PKG-PACKAGING-003 sha back-fill

The Approved `[Updated: 2026-09-21]` note under REQ-PKG-PACKAGING-003 named its
clause-(ii) retirement endpoint as a **future event** — "from the close of the
`consumer-geometry` implement stage — whose sha the verify stage back-fills into
this note". The implement stage closed at **`f7886cd`** (*chore(consumer-geometry):
regenerate the aggregate after Chunk 8*), the last implement-stage commit on the
branch. That literal now stands in the note in place of the future-event
phrasing.

Write scope: `docs/requirements/integration/packaging.md` and no other file —
the **one** verify-stage write of that path, separately scoped from Chunk 7
task 1's single implement-stage write and deliberately not folded into it. The
edit is a note amendment only; no Approved sentence outside the note was
rewritten, and the diff is 5 insertions / 4 deletions confined to that
paragraph. `last_updated` was deliberately **not** bumped: the note carries its
own inline date (2026-09-22), and bumping the corpus date would re-stale the
five specs that §CG-11(b)'s same-commit pairing closed at `5dffff7` for no
change to what the requirement asserts.

**Status: pass.**

## Chunk 9 Task 3 — the machine-dependent observation (not a gate assertion)

Recorded as an **observation with its command**, never as a gate assertion: it
depends on an installed cache whose presence and version no gate can guarantee,
and the cache is a read-only measurement surface (kickoff constraint 1 — nothing
here wrote to it).

**Observation 3a — the installed cache, read-only.** The cache at
`~/.claude/plugins/cache/sdd-commons/sdd/0.1.0/` holds the **pre-change** tool:

```
$ diff -q ~/.claude/plugins/cache/sdd-commons/sdd/0.1.0/tools/skill-lint.py \
         plugins/sdd/tools/skill-lint.py
Files ... differ            # the cache is NOT this cycle's copy

$ python3 ~/.claude/plugins/cache/sdd-commons/sdd/0.1.0/tools/skill-lint.py .
.: [structure] skills/ directory not found
    fix: lint a root that holds skills/, or one containing the suite root that does …
FAIL: 1 finding(s), 0 warning(s)
```

This is the **founding defect, still live**, reproduced unchanged — and it is
the honest state of this machine: the branch is not merged, so the marketplace
has not re-materialised the plugin. The cache therefore serves as the *control*
rather than as the post-change measurement. Claiming `GEOMETRY: nested` from a
cache that predates the change would have been the assertion this task exists
to avoid.

**Observation 3b — the post-change measurement, from a genuinely disjoint
copy.** The same geometry, with this cycle's tool, taken by copying
`plugins/sdd` to a scratch root outside the corpus and running it against the
repository:

```
$ cp -R plugins/sdd "$TMPDIR/cg-farcopy/sdd"
$ python3 "$TMPDIR/cg-farcopy/sdd/tools/skill-lint.py" .
GEOMETRY: nested  swept-roots=2  suite-rows-root=<repo>/plugins/sdd
OK: 25 file(s) clean

$ python3 "$TMPDIR/cg-farcopy/sdd/tools/gc.py" --report --root .
GEOMETRY: nested  swept-roots=2  suite-rows-root=<repo>/plugins/sdd
OK: 9 sweep(s) clean, 0 warning(s), 37 info
# (0 warnings here, 1 under §Quality Gates: this run was taken BEFORE this
#  stage's `Verified` write. `traceability-aggregate` fires only once a
#  per-workstream traceability file is edited ahead of the aggregate, which
#  that write does. Same command, same root, byte-identical tool.)
```

The pair 3a/3b is the cycle's headline result: two copies of the suite, one
pre-change and one post-change, both disjoint from the corpus, one silently
reducing to a single `[structure]` finding and the other walking all 25 files.

**Status: observation recorded (not gating). The repair is demonstrated by 3b;
3a is its control.**

## Chunk 9 Task 4 — the box-walk

Every box below is **discharged by a named task in the chunk that holds the
write scope to repair it**; this task asserts that each has such an owner and
that each returned a result, and re-runs the mechanically cheap ones as a
completeness check. No box is evaluated here for the first time — a box first
evaluated at verify would be a loop-back, not a fix.

### docs/spec/two-root-linter.md §Consumer-Geometry Acceptance Criteria (19 boxes, 22 results)

| # | Criterion | Owner | Status | Evidence |
|---|---|---|---|---|
| 1 | Requirements-corpus writes scoped, enumerated, dated; pairing | Ch7 t1, t2, t9 | **pass with a stated deviation** | Exactly one implement write (`e8a274b`) and one verify write (this report's task 2); three `[Updated: 2026-09-21c` notes present under the named ids. **Deviation on the literal clause**: the criterion requires the note-carrying commit to also carry the spec touches it pairs with, *or* re-date the affected specs in that same commit. `e8a274b` carried `skill-lint-v5.md` and `two-root-linter.md` but not `marketplace-packaging.md` or `pre-commit.md`; those two were re-dated in a **separate** commit, `5dffff7`, by the orchestrator at Chunk 8's gate after its verifier argued the split was never closed. **Accepted** because the gap opened and closed entirely inside the implement stage and no note ever shipped unpaired — but it is a deviation, not a bare pass, and is recorded as one |
| 2 | The enumerated set is covered **and demonstrated** | Ch1 t3, Ch2 t5–6, Ch3 t3, Ch4 t1–4 | pass | All eight rows registered and run (task 1's Set B); each row's mutation applied, run and reverted at its owning chunk — recorded per row in `docs/ws/consumer-geometry/traceability.md` REQ-…-001 Test cell |
| 3 | Desk-check half of the count equality collected | **Ch9 t1** | pass | §Chunk 9 Task 1 — both sets recorded, difference empty both ways |
| 4 | Both tools' gates green and still hooks | Ch0 t5, Ch4 t5, Ch8 t1 | pass | Both `--self-test`s exit 0 (re-run here); `.pre-commit-config.yaml:53,:59` parsed |
| 5 | The per-geometry split holds (Option A restores, Option B rejected, C12.1 unmodified at 16) | Ch3 t5–6 | pass | `skill-lint.py --self-test` exit 0 carries `disjoint_suite_walk_excluded()` and C12.1 unmodified; fixture's suite subdir pinned to `vendor/suite`, not `plugins/sdd` |
| 6 | Surface exists, is discoverable, reaches the binding | Ch2 t1, t7 | pass | `skill-lint.py --help` names `--suite-root` (2 occurrences); tier-1 run renders the passed root (§CG-6 (b) below) |
| 7 | `gc.py` passes it through on **both** branches | Ch2 t3–4, t6 | pass | `gc.py --help` names `--suite-root`; `Gc.__init__` accepts `suite_root=` (introspected); branch (ii) shim asserted by row 4's case |
| 8 | Both absence sentences corrected; surviving clauses survive | Ch7 t3 (primary), Ch2 t10 (leg (i)), Ch7 t8 (residual) | pass | `grep -c 'no-suite-rules' plugins/sdd/tools/skill-lint.py` → **0**; leg (i) preserved; residual grep run-time-derived with the amendment exemption |
| 9 | `— NOTHING SWEPT` present iff nothing swept, all three sites | Ch1 t2, t5 | pass | Empty corpus → `OK: 0 file(s) clean — NOTHING SWEPT`; one-file corpus → `OK: 1 file(s) clean` (no suffix). Re-run here |
| 10a | §CG-6 (a) — three geometry values render | Ch1 t4(a) | pass | far corpus → `GEOMETRY: disjoint`; repo → `nested`; corpus==suite → `equal`. Three distinct values from one binary |
| 10b | §CG-6 (b) — `suite-rows-root=` renders the **effective** root at tier 1 | Ch1 t4(b) | pass | far corpus + `--suite-root <repo>/plugins/sdd` → `suite-rows-root=<repo>/plugins/sdd`, not the corpus root |
| 10c | §CG-6 (c) — fixture D renders the **tier-2 derived** `F/plugins/sdd` | Ch3 t4(c) | pass | corpus `F` holding `F/skills/**` + `F/plugins/sdd/skills/**` → `GEOMETRY: nested  swept-roots=2  suite-rows-root=$TMPDIR/cg6/F/plugins/sdd` — the derived root, not `default_suite_root()` |
| 10d | §CG-6 (d) — token unconditional on summary runs, absent from `--self-test` | Ch1 t4(d) | pass | A run with 42 findings still prints its `GEOMETRY:` line; `--self-test` prints **0** `GEOMETRY:` lines |
| 11 | The token survives the sweep; `gc.py` derives no geometry | Ch5 t1–3, Ch7 t4 | pass | Far `gc.py --report --root .` prints one `GEOMETRY:` line (3b); both halves (grep + duplicate-token mutation) run at Chunk 5 |
| 12 | Summary-line pins confirmed unanchored (observation) | Ch7 t5, t7 | pass (observation) | Four pins read at implement time; none end-anchored; the dead `tools/sdd-skill-lint.py` invocation corrected and the corrected path resolves |
| 13 | Disjoint invocation repaired end to end | Ch3 t1, Ch5 t4 | pass | 3a vs 3b above: `[structure]` finding + `FAIL: 1` → `GEOMETRY: nested` + `OK: 25`; far `gc.py --report` raises no `[structure]` finding |
| 14 | Every construction path resolves the same tiers (the `-c` shim) | Ch3 t7 | pass | Constructor resolution in `Linter.__init__` (`b137ec5`); shim and CLI agree, asserted at the owning task |
| 15 | Foreign consumer untouched, **both** negative directions | Ch3 t5 | pass | corpus with own `skills/`, no `plugins/sdd` → `disjoint  swept-roots=1`, own file still walked, no `NOTHING SWEPT`; `plugins/sdd` present but no `skills/` → `disjoint`, candidate declined. Both re-run here |
| 16 | Positive direction fires, observable four ways | Ch3 t2, t4 | pass | Fixture D (10c): `suite_contained()` true, `nested`, `swept-roots=2`, derived `F/plugins/sdd` rendered |
| 17 | Nested case not regressed | Ch3 t8, Ch8 t3 | pass | In-repo `skill-lint.py .` → `GEOMETRY: nested  swept-roots=2` / `OK: 25 file(s) clean`, count derived at run time |
| 18 | This file's three §CG-9 correction sites landed (`:89`, `:522-523`, `:366`) | Ch6 t2, Ch7 t3 | pass | Landed at `b7cc11a` / `e8a274b`; freeze item now names `0bdb076` at `:371` and `:778` |
| 19 | Machine-dependent observation | **Ch9 t3** | **not obtainable here — cache predates the change; recorded as control** | The box asserts the **installed cache's own** linter reports `GEOMETRY: nested` after the change. It cannot: this branch is unmerged, so the cache holds the pre-change tool and still prints `[structure] skills/ directory not found`. §Task 3 records that run as the **control** and takes the post-change half from a scratch `cp -R` copy — which is the separate §CG-8 construction already owned by box 13. Box 19's own content therefore goes unmeasured on this machine, as REQ-…-006's closing note anticipates ("a cache whose presence and **version** no gate can guarantee"). Obtainable only after merge |

### docs/spec/drift-sweep.md §Consumer-Geometry Acceptance Criteria (8 boxes)

| # | Criterion | Owner | Status | Evidence |
|---|---|---|---|---|
| 1 | Surface exists on the sweep too (`--help`, `Gc(...)` keyword) | Ch2 t8 | pass | `gc.py --help` names `--suite-root`; `inspect.signature(Gc.__init__)` contains `suite_root` |
| 2 | Omitting it changes nothing **in the constructed strings**, geometry not frozen | Ch2 t6 | pass | Pre/post string comparison at the owning task; the shim still resolves tier 2 in the constructor (box 14 above) |
| 3 | `lint_command()`: argv branch carries the root, `-c` shim constructs with it | Ch2 t3–4 | pass | Both branches asserted; fixing only argv leaves the shim half red by construction |
| 4 | `gc.py --self-test` registers `cg-row-4:`; mutation run both ways | Ch2 t5 | pass | `CG_ROW_TOKENS = ("cg-row-4:",)`, `ran == {"cg-row-4:"}` at run time; both plan-named mutations run at Chunk 2 |
| 5 | §CG-8 far `gc.py --report` prints `GEOMETRY:` and raises no `[structure]` | Ch5 t4 | pass | Observation 3b |
| 6 | `gc.py` derives no geometry — (a) grep, (b) duplicate-token mutation | Ch5 t2, Ch7 t4 | pass | Both halves run at their owning tasks; the far run carries exactly one `GEOMETRY:` line |
| 7 | `AGG_FIX` names a path that resolves | Ch6 t7 | pass | `AGG_FIX` = `run plugins/sdd/tools/gc.py --fix traceability-aggregate (…)`; the named path resolves at run time |
| 8 | `gc.py --self-test` exits 0 and stays a hook | Ch8 t1 | pass | exit 0; `.pre-commit-config.yaml:59` |

### docs/spec/skill-lint-v5.md §Consumer-Geometry Acceptance Criteria (3 boxes)

| # | Criterion | Owner | Status | Evidence |
|---|---|---|---|---|
| 1 | Four summary-line pins not end-anchored; dead invocation corrected and resolves | Ch7 t5, t7 | pass | Observation recorded at the owning task; corrected path `plugins/sdd/tools/skill-lint.py` resolves |
| 2 | Exactly one `GEOMETRY:` line, own line, before the summary, contributing to no count; none from `--self-test` | Ch1 t1, t7 | pass | Repo run → exactly **1** `GEOMETRY:` line; `--self-test` → **0**; count-invariance asserted by mutation at Chunk 1 t7 |
| 3 | `no-suite-rules` grep still empty; `suite_rules=False` still self-test-only | Ch2 t10 | pass | `grep -c 'no-suite-rules' plugins/sdd/tools/skill-lint.py` → **0** |

### docs/spec/marketplace-packaging.md §Consumer-Geometry Acceptance Criteria (removal half) (10 boxes)

| # | Criterion | Owner | Status | Evidence |
|---|---|---|---|---|
| 1 | **Gone** — directory absent, `orchestrate/tools` grep excluding `docs/` returns zero | Ch6 t1, t12 | pass | `test ! -d plugins/sdd/skills/orchestrate/tools` succeeds; the excluding grep returns **0** matches (re-run here) |
| 2 | Every class (A)/(C) file made true — primary, by named sentence | Ch6 t2 | pass | Three quoted sentences corrected, whitespace-normalised, at `b7cc11a`; file set read from the table at run time |
| 3 | Secondary residual grep with both exemptions | Ch6 t11, t12 | pass | Run-time derived bounds, fenced-block and amendment-section exemptions; class (B) deliberately out of scope |
| 4 | Every class (B) record carries its note and its original survives | Ch6 t3 | pass | `[Superseded 2026-09-21 — REQ-PKG-CONSUMERGEOMETRY-005` notes within three lines; insertion-only `git diff` over `b7cc11a` alone |
| 5 | Dead comparand corrected on both sides; regeneration byte-identical | Ch6 t5 + gate (D4) | pass | Per-ws `docs/ws/marketplace/traceability.md:57` and the aggregate's `-007` row located by id; regeneration run and diffed at the gate |
| 6 | Neither spec-checklist assertion survives — one excised, one retired | Ch6 t10, t11 | pass | `:366` clause excised with its surviving clauses intact; `:367` retired whole; residual grep run-time-bounded with three stated exemptions |
| 7 | Freeze item repinned, asserted on the named item | Ch6 t6 | pass | `marketplace-packaging.md:371` and `:778` name `0bdb076`; re-run here: `git show 3ddfdb3:tools/<t> \| cmp - <(git show 0bdb076:plugins/sdd/tools/<t>)` exits 0 for **both** tools |
| 8 | No invocation regressed **by the removal** | Ch6 t13 | pass | Evaluated across `b7cc11a` alone; `gc.py --report --root .` and the hooks unchanged in status |
| 9 | Corrected strings resolve; -007's binding untouched | Ch6 t7, t8 | pass | All **6** telemetry sites now spell `python3 plugins/sdd/tools/telemetry.py`, which resolves; no telemetry invocation under `plugins/sdd/skills/` passes a plugin-relative `--file` path |
| 10 | The consumer residue is recorded, **not closed** | Ch6 t9 | pass | The `OPEN:` survives at `marketplace-packaging.md:884` with its blocking constraint named; box 10 at `:1040` asserts it. See §Known-Open (b) |

### docs/spec/pre-commit.md §Consumer-Geometry Acceptance Criteria (4 boxes)

| # | Criterion | Owner | Status | Evidence |
|---|---|---|---|---|
| 1 | Q-IMPL-MARKETPLACE-019's context sentence re-tensed with an inline dated clause | Ch6 t2 | pass | Corrected at `b7cc11a`, whitespace-normalised match; the recorded context is not rewritten |
| 2 | Secondary residual grep, both exemptions, bounds derived at run time | Ch6 t11 | pass | Exactly one pre-heading match before the correction, zero after; both halves computed from the heading's run-time line number |
| 3 | Hook set byte-identical across the cycle | Ch8 t2 | pass | `git diff 3bac4af..HEAD -- .pre-commit-config.yaml` is **empty** (re-run here) |
| 4 | `pre-commit run --all-files` exits 0; both self-tests stay hooks | Ch8 t1 | **carried — environmental** | Both self-tests are hooks (`:53`, `:59`) and both exit 0. `--all-files` cannot complete in this sandbox; the recovered-coverage run over 208 of 209 tracked files passes all 8 hooks. See §Known-Open (c) |

**Completeness assertion.** 44 boxes; 47 results counting §CG-6 as four. Every
box maps to a named owning task in Chunks 0–8 (or, for boxes 3 and 19 of
`two-root-linter.md`, to Chunk 9 tasks 1 and 3, which the plan assigns to the
verify stage by design). **No box was found without an owning task**, so no
`sdd:replan` route is triggered by this walk. 46 results are `pass`; one
(`pre-commit.md` box 4) is carried as environmental with its assertable and
non-assertable halves stated separately.

## Known-Open Items — explicit dispositions

Each of the four items named at dispatch gets a written disposition. None is
left to be rediscovered.

### (a) The unpinned tier-2 conjunct — **CARRIED, with its blocking constraint named**

**Disposition: carried, argued, not fixed.** Recorded in the plan's §Risks at
Chunk 3's gate by both the implementer and the verifier independently; this
walk re-ran the mutation rather than restating it.

`derived_suite_root()` declines a candidate on three conjuncts
(`plugins/sdd/tools/skill-lint.py:479-484`):

```python
if not candidate.is_dir():                      return None   # conjunct 1
if not (candidate / "skills").is_dir():         return None   # conjunct 2
if candidate.resolve() == default_suite_root().resolve(): return None
```

**Demonstrated here, on a scratch copy** (`$TMPDIR/mutrepo`, unmutated control
first):

| Mutation | `--self-test` result |
|---|---|
| none (control) | `SELF-TEST OK` — exit 0 |
| remove conjunct 1 **alone** | `SELF-TEST OK` — **still exit 0, no case reds** |
| remove conjuncts 1 **and** 2 | `SELF-TEST FAIL:` with 8 red lines (tier-3 fall-through, foreign-consumer geometry, declined-candidate reporting) |

So the **conjunction** is pinned and that **single conjunct** is not: with
conjunct 1 removed, conjunct 2's `(candidate/"skills").is_dir()` still guards
the same non-existent path, so nothing observes the loss.

**Why it is carried rather than fixed.** Closing it needs a fixture whose corpus
holds a `plugins/sdd` **file** (not a directory) with a `skills/` path that
would otherwise resolve — the only tree shape in which the two conjuncts
disagree. That fixture is authored by no task in this plan and the write scope
to add it (`plugins/sdd/tools/skill-lint.py`) exists only in Chunks 1–4, which
have closed; adding it here would be a loop-back, not a fix.

**Why it is not a failure of REQ-PKG-CONSUMERGEOMETRY-001.** That requirement's
premise binds the **eight enumerated rows** of its table, and the tier-2
conjunction is not one of them — none of the eight red lines above carries a
`cg-row-` prefix, because tier-2 derivation is pinned by ordinary `check()`
cases. The requirement's acceptance 2 is therefore not falsified. What *is* true
is the weaker and still worth-recording claim: a site this cycle touched has a
sub-expression whose individual reversion nothing observes, which is one
granularity below the standard kickoff constraint 2 sets. Carried on that
footing, not waved through.

**Carried to:** a cycle with write scope over `skill-lint.py`'s fixtures, with
the fixture shape above as its specification.

### (b) The consumer-unreachable `OPEN:` — **CARRIED, by design, and asserted to survive**

**Disposition: carried as a stated boundary of the packaging design; its
survival is itself an acceptance criterion and that criterion passes.**

`docs/spec/marketplace-packaging.md:884` records that **no spelling of a
skill-body tool invocation resolves for a consumer of the installed plugin**: a
bare relative path fails, a `plugins/sdd/`-prefixed path works only in a
repository laid out like this one, and the plugin-root variable is forbidden in
skill bodies by REQ-PKG-MARKETPLACE-008.

The six telemetry sites and `AGG_FIX` were corrected to
`plugins/sdd/tools/…` and **do** resolve here — which satisfies
REQ-PKG-CONSUMERGEOMETRY-005 acceptance 7 while resolving for no consumer. In
the one cycle whose subject is consumers, deleting the `OPEN:` would have
claimed a closure that did not happen, so Chunk 6 task 9 sized the *survival* of
the record rather than its removal, and
`marketplace-packaging.md:1040` asserts it ("The consumer residue is recorded,
not closed"). Verified present: **pass**.

**Blocking constraint, named:** closure requires **either** an attested
skill-body expansion for the plugin root, **or** a requirement authorising
another mechanism. Neither is owned by any artifact in this cycle, and inventing
one here would be a scope widening, not a repair.

**Carried to:** a cycle that can amend REQ-PKG-MARKETPLACE-008 or introduce the
expansion.

### (c) The sandbox pre-commit limitation — **ACCEPTED, with what is and is not assertable stated**

**Disposition: accepted as environmental; the assertable half is asserted and
the non-assertable half is named.**

```
$ pre-commit run --all-files
drift sweep (fast profile).....Passed    skill linter................Passed
skill linter self-test.........Passed    drift sweep self-test.......Passed
trim trailing whitespace.......Passed    fix end of files............Failed
  PermissionError: [Errno 1] Operation not permitted: '.claude/settings.json'
check yaml.....................Passed    check json..................Passed
```

**What IS assertable.** All **8** hooks pass over every tracked file except one:

```
$ git ls-files | grep -v '^\.claude/settings\.json$' > "$TMPDIR/tracked"   # 208 of 209
$ pre-commit run --files $(cat "$TMPDIR/tracked")
… all 8 hooks Passed
```

Also assertable, and asserted: the hook **set** is byte-identical from `3bac4af`
(`git diff` over `.pre-commit-config.yaml` empty), both tool self-tests are hook
entries rather than run-explicitly entries, and both exit 0. Together these
discharge every clause of `pre-commit.md` box 4 **except its literal
`--all-files` exit code**.

**What is NOT assertable here.** That `pre-commit run --all-files` exits 0 as a
single command on this machine. `.claude/settings.json` is on the sandbox's
write-deny list, `end-of-file-fixer` opens every file `rb+`, and the failure is
raised by the hook's own file handling before any content check runs. The file
is outside this cycle's scope: it is not one of the 25 paths the cycle changed,
the cycle declares no write scope over it, and modifying it to satisfy a hook
would be a scope violation committed to make a gate green.

**Not a defect in the delivered work.** The gap is between a literal command
spelling and this execution environment, and the recovered-coverage run closes
it over every file the cycle could have broken.

### (d) The Check 3 advisory — **ACCEPTED, with its cost stated**

**Disposition: accepted; it is the repository's established convention, and the
cost is recorded rather than minimised.**

No external test file imports either tool. Coverage rests entirely on their
embedded `--self-test` entry points — which is the convention the suite has used
since before this cycle (both are `.pre-commit-config.yaml` hooks, `:53` and
`:59`, and no `tests/` directory exists).

**The cost, stated plainly.** This cycle's **entire** test surface is
self-hosted: every one of the eight `cg-row-` cases, every geometry fixture, and
every mutation demonstration lives inside the file under test. A defect that
disabled the self-test harness itself — rather than any individual case — would
not be observed by any other artifact. This cycle mitigated that in exactly one
place and it is worth naming: `cg_reconcile()` is falsifiable in **both**
directions on demand (Chunk 0 task 2 ran a token-without-case and a
case-without-token mutation), so the registration mechanism is pinned even
though the harness is not.

**Why accepted rather than repaired.** Introducing an external test framework is
a repository-wide convention change, owned by no requirement in this cycle, and
`docs/requirements/index.md` §Out of Scope does not admit it. Recorded here so
the next reader sees the exposure rather than inferring the convention is
costless.

**Related live consequence:** §Issues Found → Minor 1, a pre-existing
`telemetry.py --self-test` failure that no gate observes precisely because that
tool's self-test is a run-explicitly check rather than a hook.

## User-Perspective Validation

| Scenario | Status | Notes |
|---|---|---|
| A consumer runs the shipped linter from outside their corpus | **pass** | Post-change far copy: `GEOMETRY: nested  swept-roots=2` / `OK: 25 file(s) clean`. Pre-change copy (still in the cache): `[structure] skills/ directory not found` / `FAIL: 1 finding(s)` |
| A consumer can tell **which** tree the suite rows were evaluated against | **pass** | Every summary-bearing run prints `GEOMETRY: <enum>  swept-roots=N  suite-rows-root=<path>` — the signalling REQ-…-004 exists to provide. Previously there was no way to know |
| A zero-sweep run is distinguishable from a clean run | **pass** | `OK: 0 file(s) clean — NOTHING SWEPT` vs `OK: 1 file(s) clean`. This is the "silently reduced answer" class the cycle exists to close, made loud |
| A foreign consumer with their own `skills/` and no `plugins/sdd` is unaffected | **pass** | `GEOMETRY: disjoint  swept-roots=1`, their file still walked, no suffix, no findings about files they never wrote |
| A fork/marketplace tree holding `plugins/sdd/skills/` is re-rooted onto **its own** copy | **pass** | Fixture D: `suite-rows-root=$TMPDIR/cg6/F/plugins/sdd` — the tree being linted, never the tool's own location |
| A tree with `plugins/sdd` but no `skills/` under it is not mis-adopted | **pass** | Candidate declined; run reports `disjoint` rather than naming an empty suite root |
| Error messages are helpful | **pass** | The `[structure]` finding's `fix:` line now names both remedies ("lint a root that holds `skills/`, or one containing the suite root that does") and the corpus root's provenance |
| A consumer following a skill body's documented tool invocation | **fail — known, recorded** | No spelling resolves for a consumer of the installed plugin. This is §Known-Open (b), surfaced by this cycle and explicitly not closed by it |
| Passing `--suite-root` explicitly is discoverable | **pass** | Named in `--help` on **both** tools; previously the surface did not exist and the specs asserted its absence |
| The tools are still usable by a contributor in-repo | **pass** | In-repo behaviour unregressed: `nested`, `swept-roots=2`, 25 files, same counts as `3bac4af` |

## Regressions

**Regression base (marker 4):** `merge-base(consumer-geometry, main)` =
`3bac4aff1ed2b20eb6d5f43a3ac3477545f4221c` — the workstream branch point, not
`main` HEAD, so nothing merged to `main` meanwhile can produce a false
regression.

- **None found.** 27 commits, 25 files changed. The full-suite regression run at
  Chunk 8 (`64c4fe4`, *full-suite regression, no regression found*) is
  re-confirmed here: both tool self-tests exit 0, the corpus lint and drift
  sweep are clean, the two other contributor self-tests
  (`scope-check-selftest.py` 44/44, `eval.py`) pass.
- **Nested geometry unregressed:** in-repo `skill-lint.py .` reports the same
  geometry and the same swept-file count as before the change, both derived at
  run time.
- **Hook set unchanged:** `git diff 3bac4af..HEAD -- .pre-commit-config.yaml` is
  empty.
- **Unintended changes:** none. The 25 changed paths are all within the chunks'
  declared write scopes; the working tree is otherwise clean (as read at the
  close of the implement stage — at the time this report is read it also holds
  this report and the two verify-stage writes, all three in scope).
- **`telemetry.py --self-test` is red but is NOT a regression** — the file is
  untouched by this cycle (`git diff --stat 3bac4af..HEAD` shows no change) and
  last changed at `e26f81f`, the packaging move. Recorded as Minor 1.

## Deferral-Backlog Screen (Step 5b)

Scope: (i) `docs/requirements/index.md` §Out of Scope, and (ii) the §Next Steps
section of **every** path `docs/ws/*/verification.md` returns. The 22-phrase
table was read from `docs/spec/requirements-artifacts.md` §`## Out of Scope`
Discipline at run time, with the item-scoped liveness rule of §Item-Scoped
Liveness (2026-09-21, packaging) — a marker suppresses only its own item, and
marker lines attach downward.

**The glob returned 8 paths; 8 rows were walked.** Both counts derive from the
same run. (This report, the ninth, did not exist when the screen ran; its
§Next Steps below is written to the same rule and carries no live deferral
phrasing.)

| Path (§Next Steps) | Phrase hits | Live |
|---|---|---|
| `docs/ws/default/verification.md` | 3 | **1** |
| `docs/ws/harness-p2/verification.md` | 0 | 0 |
| `docs/ws/harness-p3/verification.md` | 12 | **2** |
| `docs/ws/harness-p4/verification.md` | 5 | **3** |
| `docs/ws/harness-p5/verification.md` | 6 | 0 |
| `docs/ws/harness-p6/verification.md` | 0 | 0 |
| `docs/ws/marketplace/verification.md` | 0 | 0 |
| `docs/ws/packaging/verification.md` | 2 | **2** |
| **rows walked** | **8** | = **8 paths returned** |

| Path (§Out of Scope) | Phrase hits | Live |
|---|---|---|
| `docs/requirements/index.md` | 2 | **2** |

**Findings and their dispositions.**

- The two `docs/requirements/index.md` hits (`:748` "the **successor**
  requirement permitting tool-source edits", `:756` "`lint_path()` **candidate**
  tuple") are **screen false positives**: both sit in the Q-REQ resolution table
  as citations. `:748` is a *pointer to the requirement that shipped it* —
  REQ-PKG-CONSUMERGEOMETRY-001 — which is the **superseded** disposition the
  rule explicitly permits, not a deferral; `:756` is the code identifier
  `candidate tuple`. No repair owed. The screen's own spec calls row 8
  (`candidate`) and row 7 (`successor`) best-effort vocabulary, and these are
  exactly the shape it warns about.
- The 8 live hits across four **earlier workstreams'** reports are pre-existing
  and **outside this cycle's write scope**: `docs/ws/{default,harness-p3,
  harness-p4,packaging}/verification.md` appear in no chunk's declared scope,
  and editing them here would be a `SCOPE: VIOLATION`. Recorded as Minor 2 with
  that constraint named, not silently passed.
- **Coverage caveat, stated as the spec requires:** phrase coverage is a
  **screen over observed backlog vocabulary, not a proof of absence**. A
  deferral written in vocabulary no cycle has used yet passes it. The zero rows
  above are **not** an assertion that those sections hold no latent work.

## Issues Found

### Critical (blocks release)

- None.

### Minor (can ship, fix later)

1. **`python3 plugins/sdd/tools/telemetry.py --self-test` exits non-zero**,
   printing `SELF-TEST FAIL: - schema rendering missing:
   <repo>/plugins/sdd/docs/spec/telemetry.md`. The tool derives a `docs/spec/`
   path from its **own** plugin root; `docs/` was deliberately left outside the
   shipped plugin by the packaging cycle, so that path has never existed
   (`git ls-tree -r 3bac4af | grep -c '^plugins/sdd/docs/'` → **0**). This is
   **exactly this cycle's defect class** — a tool reaching for a path relative
   to its own location rather than the tree it is working on — in the one
   contributor tool the cycle's enumeration does not name. It is **pre-existing
   and not a regression**: `telemetry.py` is byte-identical to `3bac4af` and
   last changed at `e26f81f`. No gate observes it because `telemetry.py` is one
   of the three run-explicitly contributor checks, not a `.pre-commit-config.yaml`
   hook (`CONTRIBUTING.md` §The heavier checks, run explicitly) — which is the
   live cost of §Known-Open (d). Not fixed here: `plugins/sdd/tools/telemetry.py`
   is in no chunk's write scope, and the enumeration in
   REQ-PKG-CONSUMERGEOMETRY-001 is amended by requirement, never by argument.
2. **Eight live deferral-screen occurrences in four earlier workstreams'
   `verification.md` §Next Steps** (`default:257`; `harness-p3:754, :815`;
   `harness-p4:405, :407, :409`; `packaging:435, :445`). Each is a backlog item
   written without an adjacent dated marker. Not repaired here: those paths are
   outside this cycle's declared write scope and a touch from this stage would
   be a `SCOPE: VIOLATION`. The repair is mechanical — add the adjacent
   bracketed dated marker, or close the item — and belongs to whichever
   workstream owns each file.
3. **One conjunct of the tier-2 adoption test is individually unpinned** — the
   full argument, the mutation run and the fixture shape that would close it are
   in §Known-Open (a). Recorded here so it appears in the Minor list a later
   cycle reads, not only in the prose above.

**Carry-or-close over the previous report:** none owed. This is the
`consumer-geometry` workstream's **first** cycle; `docs/ws/consumer-geometry/`
held no prior `verification.md` (the Step 5b glob returned 8 paths, none of them
this one), so there is no predecessor report whose Minors could be lost to the
overwrite.

## Recommendation

- [x] Ship as-is — **subject to the red round**. Blue verification passes with
      zero Critical findings and three Minors, none of which blocks. The
      frontmatter reads `pending-red`, so this is not a `pass` and not DONE: the
      orchestrator dispatches the red team, gates, and flips
      `pending-red → pass` here and in the six `Verified` cells of
      `docs/ws/consumer-geometry/traceability.md` before its own commit.
- [ ] Fix critical issues then ship (invoke replan)
- [ ] Significant rework needed (invoke replan)

## Red Round (2026-09-22) — `RED_VERDICT: HELD`

One read-only adversarial leaf attacked the cycle's acceptance criteria on
scratch constructions. **Nothing it built contradicted a stated criterion**: the
far-copy repair, both foreign-consumer negatives, §CG-4's positive direction with
all four observables, the token's iff-conditions across `--print-population`,
`--fix` and the rc-2 exit path, the `— NOTHING SWEPT` iff-condition on all three
print sites, and **all eight enumerated rows** — each mutation reddening its own
token, not merely a neighbour's — held under attack.

It returned three findings that are **not** breaks, because no criterion claims
otherwise. They are recorded here so the red round's value survives it.

- **R-a. Tier 1's "no existence test" is behaviour-changing and completely
  unpinned.** §CG-3 states tier 1 is adopted without an existence test, so an
  operator may name a root the derivation would reject. No criterion in the five
  specs or six requirements asserts it. Changing one line in `Linter.__init__` —
  `if suite_root is not None:` → `if suite_root is not None and
  Path(suite_root).is_dir():` — silently demotes an explicit operator root to
  tier 2/3 and flips every observable (`GEOMETRY: disjoint`/`swept-roots=1` vs
  `nested`/`2`; 40 findings vs 42), and **both `--self-test` gates stay green**.
  Re-verified at this gate by the orchestrator. This is a defect in the tier
  machinery itself that the self-hosted test surface cannot see — the sharpest
  live instance of known-open item (d). Closing it needs one case asserting that
  an explicit non-existent root is still adopted.
- **R-b. The third conjunct is individually unpinned.** Deleting
  `derived_suite_root()`'s `candidate.resolve() != default_suite_root().resolve()`
  guard reds nothing in either tool. Unlike R-a this is a semantic no-op — where
  it fires, tiers 2 and 3 name the same directory — so no behaviour and no
  criterion is violated, but the docstring's "all three conjuncts are required"
  is false as a *testable* statement. With the first conjunct already recorded
  unpinned (plan §Risks, Chunk 3's gate), only the middle conjunct
  (`(candidate/"skills").is_dir()`, REQ-PKG-CONSUMERGEOMETRY-006 acceptance 5) is
  genuinely pinned.
- **R-c. Two reader-facing inconsistencies, one of them a second live instance of
  Minor 1's class.** (i) With `plugins/sdd` a symlink to an out-of-tree
  directory, the derivation fires on the unresolved path while
  `suite_contained()` resolves it, so the token reads `GEOMETRY: disjoint` while
  `suite-rows-root=` renders a path *inside* the corpus. REQ-004 only asks the
  field to answer "which tree", which it does, so no criterion falls. (ii)
  `skill-lint.py --self-test` **fails from a far copy** — the very copy
  REQ-PKG-CONSUMERGEOMETRY-006's comparand recipe creates — with `docs/spec/ not
  found at the corpus root above the real skill suite`, silently skipping the
  template-drift case. No criterion claims the self-test is location-independent
  and every gate criterion is in-repo, so this is not a break. But it is the same
  defect class as Minor 1's `telemetry.py` instance, **in the tool this cycle's
  spine lives in**.

**Disposition.** `HELD`, so nothing is owed as a fix and `proceed` is not
withheld. R-a, R-b and R-c(ii) are carried as the strongest candidates for the
next cycle in this domain: each is a binding or a claim that the self-hosted test
surface structurally cannot observe, which is the boundary this cycle establishes
rather than one it crosses.

## Next Steps

- Minor 1 is a live defect of this cycle's own class in `telemetry.py`; amending
  REQ-PKG-CONSUMERGEOMETRY-001's enumeration is the mechanism that admits it,
  and the amendment is the work.
- Minor 2's eight occurrences are mechanical marker additions owned by the four
  workstreams whose files hold them.
- §Known-Open (a) closes with one fixture: a corpus holding a `plugins/sdd`
  **file** with a `skills/` path that would otherwise resolve.
- §Known-Open (b) closes only with an attested skill-body plugin-root expansion
  or a requirement authorising another mechanism; the `OPEN:` record stands
  until one exists.
- The active plan may be archived to `docs/ws/consumer-geometry/plan-history/`
  once the red round closes and the status flips to `pass`.
