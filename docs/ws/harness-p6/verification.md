---
workstream: harness-p6
status: pending-red
research_id: RS-HARNESSP6-001
last_updated: 2026-09-20
plan_ref: docs/ws/harness-p6/plan.md
scope: REQ-GC / REQ-HARN / REQ-LINT / REQ-ORCH / REQ-PLAN / REQ-REQ (harness-p6) over docs/spec/{drift-sweep,harness-write-scope,harness-loop-control,skill-lint-v5,plan-management,requirements-artifacts,arbitrated-handoff}.md, skills/sdd-{orchestrate,plan,replan}/**, tools/sdd-{gc,skill-lint,scope-check-selftest}.py, and the corpus text swept under docs/requirements/** and docs/ws/harness-p5/**
---

# Verification Report

## Summary

Blue-team verification of the `harness-p6` cycle passes on every runnable
criterion. The plan reads `status: complete` with 49/49 tasks ticked and
`research_id: RS-HARNESSP6-001` string-equal to the kickoff's, so this is a
**this-cycle** completion signal, not a previous cycle's artifact. All five gate
commands exit 0: `sdd-skill-lint.py` prints `OK: 25 file(s) clean` **with no
warning clause** (the unsatisfiable `0 warning(s)` expectation was not restored),
`sdd-gc.py --report` prints `OK: 9 sweep(s) clean, 0 warning(s), 31 info`,
`sdd-scope-check-selftest.py` prints `OK: 41/41 scenarios passed`, and both
self-tests are green. All **13** `REQ-*-HARNESSP6-*` requirements are verified
against their governing acceptance criteria — including the two superseded in
place, where the governing form was walked and the withdrawn literal deliberately
**not** run. All **nine** kickoff scope items are delivered; item 8 (L2) landed
in a **descoped** form and that weakening is recorded in four independent places,
not silent. There are **no regressions** against the workstream branch point
`0b0287ce` and the four-layer verification table is **byte-unchanged**. No
critical issue. Two Minors, both prose-level and both stated here rather than
deferred. **§Next Steps is empty, and that is the intended terminal outcome.**

Red team is **enabled** for this stage, so this report carries
`status: pending-red` and every would-be-`pass` `Verified` cell reads
`pending-red`. The `pending-red → pass` flip is the orchestrator's at the verify
gate; this skill never performs it.

## Quality Gates

| Gate | Status | Notes |
|------|--------|-------|
| Drift sweep (`python3 tools/sdd-gc.py --report`) | pass | rc=0; `OK: 9 sweep(s) clean, 0 warning(s), 31 info`; 0 fail-class, 0 `qimpl-undefined`, 0 `qimpl-broken-ref` |
| Drift-sweep self-test (`--self-test`) | pass | rc=0; `SELF-TEST OK: sweeps 5-14 fire once each …`, last clause naming the fence-symmetric Q-IMPL case |
| Skill lint (`python3 tools/sdd-skill-lint.py`) | pass | rc=0; `OK: 25 file(s) clean` — **no** warning clause, as specified |
| Skill-lint self-test (`--self-test`) | pass | rc=0; `SELF-TEST OK: all rule classes fire; fix/warn/size/backtick/allow_files fixtures pass` |
| Write-scope / convergence self-test (`python3 tools/sdd-scope-check-selftest.py`) | pass | rc=0; `OK: 41/41 scenarios passed`, including `G1`–`G5` and `L1`–`L9` |
| Build / package | n/a | documentation-and-tooling corpus; no build target. The three `tools/*.py` entry points are the executable surface and all three run clean |
| Format / type check | n/a | no formatter or type checker is configured for this repo (`CLAUDE.md` §Quality Checks defines the gates, and they are the five above) |

Exit codes were captured directly, not through a pipe.

## Criteria

### drift-sweep.md — REQ-GC-HARNESSP6-001 (closed-workstream skip)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `--self-test` exits 0 with the closed-workstream fixture assertions (closed raises neither plan-level sub-kind; `fail` / `pending-red` / absent still raise both) | pending-red | rc=0. Self-test section 9 at `tools/sdd-gc.py:1590`, labelled `test_stale_chain_skips_closed_workstream (REQ-GC-HARNESSP6-001)`, runs inside `self_test()` |
| `--report` reports **zero** `[stale-chain]` findings located in `docs/ws/harness-p3/plan.md` or `docs/ws/harness-p4/plan.md` | pending-red | Parsed the live `--report` output: **0** such findings. In fact **0** plan-level `[stale-chain]` findings remain anywhere in the corpus |
| Scoping change only — no new rule id, no allowlist, marker-3 unaffected | pending-red | `ws_closed()` is marker-4-guarded; the close-out demonstrated this empirically on a `$TMPDIR` marker-3 flat fixture (`marker='3'` → `False`, forced `'4'` → `True`, `'4'` with `docs/ws/` removed → `False`). No deleted line in the cycle diff mentions marker 3, v3 or the flat layout |

### drift-sweep.md — REQ-GC-HARNESSP6-002 (shared-spec fold)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `--self-test` exits 0 with the one-spec/three-ids fixture yielding exactly one finding naming all three ids | pending-red | rc=0. Self-test sections 10./11. at `tools/sdd-gc.py:1634` |
| On this repository, one finding per distinct `(spec, category file)` pair — **both sides derived at run time, no literal pinned** | pending-red | Re-derived from a single `--report` run: **6** spec-versus-requirement `[stale-chain]` findings; the set of distinct `(spec, category file)` pairs those findings name has **6** members; the two are equal. Pairs: `adversarial-verify.md`←`functional/harness-verification.md`, `adversarial-verify.md`←`integration/skill-lint.md`, `harness-chunk-verifier.md`←`functional/harness-verification.md`, `harness-return-contract.md`←`functional/harness-verification.md`, `telemetry.md`←`functional/telemetry.md`, `telemetry.md`←`integration/skill-lint.md`. (The withdrawn "exactly 3" literal was **not** run — it is superseded by the requirement's own dated note.) |

### drift-sweep.md — REQ-GC-HARNESSP6-003 (`info` demotion)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `--report` exits `OK` with **0** `[stale-chain]` **warnings** | pending-red | rc=0; parsed: `[stale-chain]` WARN = **0**, INFO = **6**. Summary line `0 warning(s), 31 info` |
| Every remaining spec-versus-requirement `[stale-chain]` line emitted at `info`; the count deliberately not pinned | pending-red | All 6 carry the `INFO` prefix; the count is reported as a run-time property, not asserted |
| `--self-test` exits 0 with severity asserted on the folded finding and unchanged on a plan-level finding | pending-red | rc=0; self-test section 11 (shared with 10) at `tools/sdd-gc.py:1634` |
| `drift-sweep.md` row 7 reads `info` for the shared-spec sub-class; §DONE routing lists only the plan-level sub-kind under `record \| ignore`; a grep of the routing for the shared-spec class returns no `record` | pending-red | Row 7 (`docs/spec/drift-sweep.md:88`) reads "plan-level **warn**; shared-spec **info**". Routing row at `:299` reads `stale-chain` (**plan-level sub-kind only**, REQ-GC-HARNESSP6-003). No routing row names the shared-spec class, so it is offered no `record`. This is the interlock that keeps REQ-GC-HARNESSP6-003 and REQ-REQ-HARNESSP6-001 from contradicting each other at the DONE gate |

### drift-sweep.md — REQ-GC-HARNESSP6-004 (Q-IMPL fence symmetry)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `--self-test` exits 0 with the fenced-heading case (fenced heading defines nothing; fenced reference raises no `qimpl-undefined`) | pending-red | rc=0; self-test section 12 at `tools/sdd-gc.py:1687`. The self-test's own summary line ends "Q-IMPL definitions are fence-symmetric: a fenced heading defines nothing, an unfenced one still does, an undefined unfenced reference still fails" |
| `--report` reports the same `qimpl-undefined` and `qimpl-broken-ref` counts as before the change (both **0**) | pending-red | Live run: `qimpl-undefined` = **0**, `qimpl-broken-ref` = **0** |
| Module docstring and `--help` state the fence-symmetric counting rule as an **authoring obligation, not an allowlist** | pending-red | Docstring `tools/sdd-gc.py:37-80` ("no whitelist exists or may be added; a fence can no longer accidentally DEFINE a foreign id"); `--help` epilog lines 52-59 carry the same. `CLAUDE.md` §Quality Checks' "there is no allowlist" sentence is untouched (CLAUDE.md is absent from the cycle diff entirely) |

### harness-write-scope.md — REQ-HARN-HARNESSP6-001 (git-state observation)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Self-test exits 0 with stash-with-pop and stash-and-drop each yielding `GIT_STATE` + `SCOPE: VIOLATION` | pending-red | `PASS G1 … (ORIG_HEAD drift) -> SCOPE: VIOLATION (1 path)`; `PASS G2 … (reverse porcelain delta) -> SCOPE: VIOLATION (1 path)` |
| An implement leaf committing an already-dirty path yields `SCOPE: CLEAN` | pending-red | `PASS G3 … (committed delta subtracted) -> SCOPE: CLEAN` |
| A fan-out merge yields `SCOPE: CLEAN` | pending-red | `PASS G4 … (outside the window) -> SCOPE: CLEAN` |
| `ORIG_HEAD` absence is the legal empty value | pending-red | `PASS G5 … absent in both vs present in after only -> SCOPE: CLEAN + SCOPE: VIOLATION (1 path)` |
| `write-scope.md` §3 lists the three extra plumbing reads and the reverse-delta subtraction; §5 the `GIT_STATE` line; §8 its options | pending-red | §3 at `:248-:277` (`stash_count`, `--abbrev-ref HEAD`, `--verify --quiet ORIG_HEAD`; two-clause comparand table at `:259-:270`). §5 at `:398-:408` — the line renders inside the existing block and counts into `SCOPE: VIOLATION (N paths)`; no new own-line token. §8 at `:724` — `restore │ accept (note) │ stop`, `proceed` withheld. The former stash limitation is retired at `:476-:478` |
| `python3 tools/sdd-skill-lint.py` exits 0 | pending-red | rc=0, `OK: 25 file(s) clean` |

### harness-loop-control.md — REQ-HARN-HARNESSP6-002 (L2 cluster rule and ledger)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| §Convergence Signal states the three cluster conditions, the three key rules, the file-level-only non-render for sectioned files, and the ledger's contents | pending-red | `docs/spec/harness-loop-control.md` §Convergence Signal: conditions (i)/(ii)/(iii) in a table; key rules 1 (shared id, primary), 2 (sectionless file), 3 (equal `(file, section)`, retained with **no recall claim**); the non-render control stated as "the decisive false-positive control … retained unchanged"; the ledger stated as session-scoped, in-memory, three fields (`key`, `layer`, `gate`), no finding text, nothing on disk |
| Scenario group: same `REQ-*` id across layers, different sections → cluster (primary key) | pending-red | `PASS L1 … -> CONVERGENCE: REQ-TELEM-HARNESSP6-001 (review, red) — 2 layers` |
| Same sectionless file across layers → cluster on the file alone | pending-red | `PASS L2 … -> CONVERGENCE: docs/ws/harness/notes.jsonl (red, blue) — 2 layers` |
| Same **sectioned** file, different sections → no cluster | pending-red | `PASS L3 … -> no cluster (sectioned file, different sections)` |
| Two findings from the **same** layer → no cluster | pending-red | `PASS L4 … -> no cluster (same layer)` |
| Equal `(file, section)` across layers → cluster (retained key, ordinal-stripped) | pending-red | `PASS L5 … -> CONVERGENCE: docs/spec/telemetry.md §Writer rule (chunk-verifier, review) — 2 layers` |
| Same key, different `research_id` → no cluster (condition ii) | pending-red | `PASS L6 … -> no cluster (different research_id)` |
| Render-once when a third layer joins | pending-red | `PASS L9 … a third layer does not re-render the cluster` (Q-IMPL-HARNESSP6-001) |
| No field added to any leaf's `RETURN:` shape | pending-red | `docs/spec/harness-return-contract.md` and `skills/sdd-orchestrate/references/dispatch-templates.md` are absent from the cycle's `git diff --name-only` against `0b0287ce` |
| `python3 tools/sdd-skill-lint.py` exits 0 | pending-red | rc=0 |

### harness-loop-control.md — REQ-ORCH-HARNESSP6-001 (`CONVERGENCE:` at 6c, informational)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `loop-control.md` §5 lists 6c between 6b and 7 and its "renders last" clause names 6c | pending-red | `references/loop-control.md:564` (item 6c, own-line token, key/layers/layer count, worked example at `:568`) and `:617-:623` — "no `CONVERGENCE:` line ever pauses the gate or changes an option, and the 'renders last before the options' clause that governs item 7 covers 6c" |
| `SKILL.md` §The gate names the token in its non-divergent summary | pending-red | `skills/sdd-orchestrate/SKILL.md:285` — the `TELEMETRY:` row extended in place to `6c, 7`, naming the token, its three key shapes, the layers and layer count, and its informational status. The file gained no line |
| A gate-rendering fixture shows the token in the stated position with `proceed` available | pending-red | `PASS L7 L2 rendering: CONVERGENCE: between PLAN: (6b) and TELEMETRY: (7), proceed available` |
| `python3 tools/sdd-skill-lint.py` exits 0 | pending-red | rc=0 |

### harness-loop-control.md — REQ-ORCH-HARNESSP6-002 (co-located scope; three invariants)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| The four-layer verification table is **byte-unchanged** in `CLAUDE.md` and in every spec that restates it | pending-red | `CLAUDE.md` does not appear in `git diff --name-only 0b0287ce..HEAD` at all. Over the whole cycle diff, **every** `+`/`-` line matching `four verification layers`, `four-layer`, `fifth layer` or `fifth verification layer` is an **addition**; there is not one deletion. The table is untouched |
| §Convergence Signal states the shipped scope and the origin-case recall **as the Chunk 8 replay measured it**, with no recall figure the replay does not reproduce | pending-red | The spec states the shipped scope (shared id primary + sectionless file + retained `(file, section)`) and states that against the origin case the shipped form "clusters **nothing**", with the 2-of-3 figure explicitly "refuted by the replay and … withdrawn here and wherever else it was copied". **Re-derived, not accepted:** I re-read the origin case at `docs/ws/harness-p3/verification.md:909-918` — blue's dropped `git add` in Chunk 7, review C1 on unexercised requirements, red R4 on aggregate drift. The three share no `REQ-*` or deviation id, no file and no section, so under key rules 1, 2 and 3 they form **zero** clusters. The spec's claim reproduces |
| No file under `docs/` is created by L2 | pending-red | `PASS L8 … a run in which a cluster fires adds no path under docs/ -> cluster fired, git ls-files docs/ unchanged (8 paths)` — demonstrated in the same run, not asserted |
| No phase-detection rule in any `sdd-*` skill references `CONVERGENCE:` | pending-red | `grep -rn CONVERGENCE skills/` hits only `sdd-orchestrate/references/loop-control.md` and `sdd-orchestrate/SKILL.md`; the §Phase Detection section of each contains **0** occurrences. No other skill mentions the token |
| `--report` reports no new artifact class; no telemetry record key added | pending-red | rc=0, `OK: 9 sweep(s) clean`. `grep -n convergence docs/spec/telemetry.md tools/sdd-telemetry.py` returns nothing |
| The `(file, section)` key's second consumer is recorded | pending-red | `docs/spec/arbitrated-handoff.md:87` — `**[2026-09-20, harness-p6 — REQ-ORCH-HARNESSP6-002.]** This key now has **two** …`. This was the Chunk 9 leaf's out-of-scope deliverable, since landed; the traceability cell no longer claims it is missing (close-out finding CO-2 is therefore **closed**, verified: `grep -c "NOT included"` = 0) |

### skill-lint-v5.md — REQ-LINT-HARNESSP6-001 (`PLAN:` and `GIT_STATE` rows)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `python3 tools/sdd-skill-lint.py` exits 0 on the corpus as it stands | pending-red | rc=0, `OK: 25 file(s) clean` |
| With `PLAN:` removed from `loop-control.md` §6 it exits non-zero naming that `REQUIRED` row; likewise from `SKILL.md` | pending-red | Mutation run against a throwaway corpus copy under `$TMPDIR` (this repository's tree never touched): stripping `PLAN: INCOMPLETE` from `references/loop-control.md` → rc=1, `[required] \`PLAN: INCOMPLETE\` found 0x, need >= 1`; from `SKILL.md` → rc=1, same row family. Restored copy re-lints at `OK: 25 file(s) clean` |
| The same holds for `GIT_STATE` removed from `write-scope.md` (and, as adopted, from `SKILL.md`) | pending-red | Same fixture: `write-scope.md` → rc=1 `[required] \`GIT_STATE\` found 0x`; `SKILL.md` → rc=1, consumer row |
| `--self-test` exits 0 with the generic `REQUIRED` mutation loop and the pair-shape assertions | pending-red | rc=0. Rows at `tools/sdd-skill-lint.py:248-273`; the `GIT_STATE` pattern is deliberately bare (no trailing colon, no alternation) because the name renders inside the `SCOPE:` block |

### skill-lint-v5.md — REQ-LINT-HARNESSP6-002 (REQ-LINT-007 qualification)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| REQ-LINT-007 carries an `[Updated: 2026-09-20 …]` note naming REQ-LINT-HARNESSP5-001 as the authorising requirement | pending-red | `docs/requirements/integration/skill-lint.md:149` — "qualified, not amended … **REQ-LINT-HARNESSP5-001** … is the authorising requirement", with the §Isolation Discipline / §Orchestrator-Only Work move named as the instance |
| A reader of the two requirements in sequence finds no contradiction | pending-red | Read in sequence. REQ-LINT-007's `no` list is scoped to "*this* marker-4 prose move" and does not pin the sections to `SKILL.md` forever; the note points at `skill-lint-v5.md` §Scope of the `no` row for the reconciling reading. No contradiction remains |
| Id, number and original text unchanged | pending-red | The note is appended; the heading, number and body above it are untouched in the diff |
| Lint and gc findings on this file unchanged | pending-red | Lint rc=0. `--report` locates **0** findings on `docs/requirements/integration/skill-lint.md`; the file is *named* by 2 findings, as a stale-chain upstream — the same shape as before the edit |

### skill-lint-v5.md — REQ-LINT-HARNESSP6-003 (`CONVERGENCE:` row pair)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Lint exits 0 once the token ships | pending-red | rc=0, `OK: 25 file(s) clean` |
| Exits non-zero naming the respective row when the token is removed from either file | pending-red | `$TMPDIR` mutation: `references/loop-control.md` → rc=1, `[required] \`CONVERGENCE:\` found 0x, need >= 1 — \`CONVERGENCE:\` L2 gate token producer`; `SKILL.md` → rc=1, the consumer row |
| Pattern keeps its trailing colon (it **is** an own-line token, unlike bare `GIT_STATE`); exact `len(REQUIRED)` total replaces the `>= 32` bound | pending-red | Rows at `tools/sdd-skill-lint.py:280-288`; `--self-test` rc=0 with the exact-total assertion, so an accidental drop of any of the six new rows fails |

### plan-management.md — REQ-PLAN-HARNESSP6-001 (§Open Questions struck at archival)

The requirement's `grep -c 'says 61' … = 0` literal is **superseded in place and
was deliberately not run**: the strike rule this same requirement ships leaves the
entry visible, so the string necessarily survives (measured elsewhere: 1 before,
1 after). The governing form is `docs/spec/plan-management.md` §Resolved
`## Open Questions` Entries Are Struck at Archival / §Acceptance Criteria, walked
below.

| Criterion (governing form) | Status | Evidence |
|-----------|--------|----------|
| The archived file's §Open Questions entry count is **unchanged** by the strike, compared before and after in the same run | pending-red | `git show 0b0287ce:docs/ws/harness-p5/plan.md` vs the working copy, both parsed in one run: **8** top-level entries before, **8** after. Unchanged |
| The struck entry carries an **adjacent bracketed dated marker** | pending-red | `**[Struck 2026-09-20 — resolved: docs/spec/telemetry-reader.md now reads **67** in all three places … REQ-PLAN-HARNESSP6-001]**`, immediately following the entry body — struck, not deleted |
| The stale claim has no **unmarked** occurrence | pending-red | `says 61` occurs exactly **once** in the whole §Open Questions section, and that occurrence is inside the struck entry the marker covers |
| The strike rule is stated in both archiving skills | pending-red | `skills/sdd-plan/SKILL.md:194,209` and `skills/sdd-replan/SKILL.md:155,170` — "struck — left visible, and marked with a bracketed dated resolution marker", with the explicit caveat that unresolvable entries are carried unmarked (the rule strikes settled entries; it does not force a verdict) |

### requirements-artifacts.md — REQ-REQ-HARNESSP6-001 (§Out of Scope discipline; the deferral sweep)

The check below is the spec's own mechanical rule, reconstructed from
`docs/spec/requirements-artifacts.md` §`## Out of Scope` Discipline (its verbatim
phrase list and marker regex) and run by this stage — including the **§Next Steps
half that the Chunk 10 close-out split out as CO-1**, which was unrunnable at
implement time because `sdd-verify` is what creates the file.

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Scope (i) `docs/requirements/index.md` §Out of Scope returns no **live** entry | pending-red | Section extracted heading-to-next-same-or-higher-heading (178 lines): **0** matches of any of the five phrases, therefore **0 live** |
| Scope (ii) `docs/ws/harness-p6/verification.md` §Next Steps returns no **live** entry — **the CO-1 half, run here** | pending-red | Re-run over this very file after it was written: §Next Steps holds **0** phrase matches, therefore **0 live**. The section is empty by design (see §Next Steps below) |
| Scope (ii) is an **enumeration over the glob** `docs/ws/*/verification.md`, not a hand-list (corrected at red R2) | pending-red | `ls docs/ws/*/verification.md \| wc -l` → **6**; the sweep was re-run over all six and reports one row per returned path (§Issues Found → Red round 1). Rows walked = paths returned = 6, both derived from the same run. The pre-R2 run walked **3** and is superseded |
| Scope (iii) `docs/ws/harness-p5/verification.md` §Next Steps — the artifact this cycle's sweep edited — returns no **live** entry | pending-red | 93 lines, **4** phrase matches, **4** marker-satisfied, **0 live**. This is also the check's **non-vacuity** evidence: the matcher demonstrably fires on real text and is then silenced only by per-item adjacent markers |
| Liveness is decided mechanically: a match is live unless its own line or the line immediately preceding it carries the bracketed dated marker; matched-phrase anchored, at-or-above only; a block-level marker does not satisfy it | pending-red | Implemented exactly as specified — per-occurrence evaluation at lines `L` and `L-1` only, regex `(\*\*\[\|_\()(?i:superseded\|closed\|struck)[^\]\)]*20[0-9]{2}-[0-9]{2}-[0-9]{2}`. The p5 result (4 matched, 4 satisfied) shows each item carries its **own** adjacent marker |
| §Q-REQ Resolutions is outside the checked scopes | pending-red | The single `deferred to` occurrence in `index.md` (`promoted from \`may\`/deferred to \`must\``, §Q-REQ Resolutions) lies outside the extracted §Out of Scope line set and is not examined — consistent with the close-out's independent run |
| The three settled exclusions named by RS-HARNESSP6-001 are each present with their reasoning | pending-red | §Out of Scope carries: review of `sdd-review`'s own output (the recursive case) — **declined 2026-09-20 (settled exclusion, RS-HARNESSP6-001 §Deferral-Backlog Sweep)**; a one-shot upstream review before a non-research pipeline entry (RS-HARNESSP3-001 Q8-OUT row 5) — **declined 2026-09-20 (settled exclusion)**; clearing the four pre-existing `qimpl-broken-ref` warnings — closed as satisfied, with its evidence re-deriving at run time (`--report` names **0** `qimpl-broken-ref`, confirmed this run). A fourth entry records the L2 descope as a settled exclusion |
| A finding too large to fix in-cycle triggers a **replan**, never a successor workstream | pending-red | Stated in the spec's §Next Steps binding, in the plan's §Replan Triggers, and in the traceability header. One replan fired and was resolved **inside** this cycle (`plan-history/2026-09-20-replan-l2-descope.md`); replan count stands at **1 of 3** |

## Kickoff Scope Items

| # | Item | Delivered | Evidence |
|---|------|-----------|----------|
| 1 | `[stale-chain]` skips a closed workstream | yes | REQ-GC-HARNESSP6-001; 0 plan-level findings remain |
| 2 | Shared-spec staleness as its own rule | yes | REQ-GC-HARNESSP6-002/-003; fold 6=6, all `info` |
| 3 | Git-state mutation observed by the write-scope snapshot | yes | REQ-HARN-HARNESSP6-001; G1–G5 pass |
| 4 | `PLAN:` gains a lint `REQUIRED` row | yes | REQ-LINT-HARNESSP6-001; mutation rc=1 both sides |
| 5 | Q-IMPL sweep becomes fence-symmetric | yes | REQ-GC-HARNESSP6-004; counts unchanged at 0/0 |
| 6 | REQ-LINT-007's "must not move" list qualified | yes | REQ-LINT-HARNESSP6-002; note at `skill-lint.md:149` |
| 7 | The stale "says 61" entry struck at archival | yes | REQ-PLAN-HARNESSP6-001 governing form |
| 8 | **L2 — the cross-layer convergence signal** | yes, **descoped** | See below |
| 9 | The deferral-backlog sweep | yes | REQ-REQ-HARNESSP6-001; 0 live across all three scopes |

**Item 8's weakening is recorded, not silent.** The descope is stated in
**four** independent places, each dated and each naming its cause: (a) the plan's
§Overview "Replanned 2026-09-20 (L2 descope)" paragraph and the `[FIRED]` marker
on the first §Replan Triggers entry; (b) the archived prior plan at
`docs/ws/harness-p6/plan-history/2026-09-20-replan-l2-descope.md`; (c) dated
`[Updated: 2026-09-20 — amended at replan …]` notes on all three L2 requirements
(REQ-HARN-HARNESSP6-002, REQ-ORCH-HARNESSP6-001, REQ-ORCH-HARNESSP6-002),
including the explicit withdrawal of the refuted 2-of-3 recall figure; (d)
`docs/requirements/index.md` §Out of Scope, as a **settled exclusion with its
measured reasoning**, and `docs/spec/harness-loop-control.md` §Convergence Signal,
which states the shipped floor and the measured origin-case result in the spec
itself. The traceability header also carries a dated update superseding its own
"never replayed" confidence note. L2 shipped; it shipped smaller than specified;
the gap is on the record with its measurement.

## User-Perspective Validation

| Scenario | Status | Notes |
|----------|--------|-------|
| An operator runs the five gate commands cold | pass | All five exit 0 and each prints an actionable last line. `sdd-gc.py --report` now ends `0 warning(s), 31 info` instead of the 63-warning wall the cycle opened with — the warn class is usable as a drift signal again, which was item 1 and 2's whole point |
| An operator reads a folded shared-spec finding | pass | `INFO docs/spec/telemetry.md: [stale-chain] spec older than requirements it requires: docs/requirements/integration/skill-lint.md (2026-09-20) is newer than telemetry.md (2026-09-19) (ids: REQ-LINT-HARNESSP5-003)` — names the pair, the dates and every triggering id in one line, with a `fix:` line that says plainly "(informational — not routed at DONE)". No information was lost in the fold |
| A read-only leaf stashes the operator's uncommitted work | pass | This is the harness-p5 incident that motivated item 3. G1/G2 reproduce it and the gate now renders `GIT_STATE stash count 0 -> 1; 9 path(s) dirty before and clean after with no commit explaining it`, counts it into `SCOPE: VIOLATION (N paths)`, and offers `restore │ accept (note) │ stop` with `proceed` withheld. The incident is now observable, not merely forbidden |
| An operator sees a convergence line at a gate | pass | L7 shows it between `PLAN:` and `TELEMETRY:`, e.g. `CONVERGENCE: REQ-ORCH-HARNESSP6-001 (review, red) — 2 layers`, with `proceed` still available. One line, no new option set, no interruption |
| Someone deletes a guarded gate token | pass | Six mutation runs, six `rc=1` with a `[required]` line naming the row and a `fix:` string pointing at the governing spec section |
| Someone writes a deferral into a swept section | pass | The liveness rule fires on the phrase and is silenced only by an **adjacent** dated marker; the 4/4 result on harness-p5 shows both halves working on real text |
| This report's own §Next Steps is checked | pass | The CO-1 half runs here for the first time and returns 0 live — the check now has a scope that exists |

## Regressions

Regression base is the **workstream branch point**
`merge-base(harness-p6, main)` = `0b0287ce17c70d08f8c0d666a830015afbef585f`
(marker `4`, REQ-WS-018), not `main` HEAD.

- **None found.** `git diff --stat 0b0287ce..HEAD` touches 32 files, +5355/-95.
  Every touched path is inside the cycle's stated scope: the seven specs, the six
  requirement files plus `index.md` and the aggregate, the research findings and
  `research/index.md`, the three `tools/*.py`, four skill files, this
  workstream's own artifacts, and the two harness-p5 files the sweep and the
  strike were required to edit.
- `docs/ws/harness-p5/verification.md` (+41) is **purely additive** — the diff
  contains **zero** removed lines and its `status: pass` frontmatter is intact.
  The additions are the per-item dated markers the sweep required.
- `docs/ws/harness-p5/plan.md` (+5) is the REQ-PLAN-HARNESSP6-001 strike:
  visible, marked, nothing deleted (entry count 8 → 8).
- `CLAUDE.md` is **not in the diff at all**, so the four-layer verification table
  and the "there is no allowlist" sentence are byte-unchanged.
- No deleted line anywhere in the cycle diff mentions marker `3`, `v3` or the
  flat layout.
- `docs/spec/harness-return-contract.md` and
  `skills/sdd-orchestrate/references/dispatch-templates.md` are untouched, so no
  leaf `RETURN:` shape gained a field.
- All three self-test harnesses exit 0, including every pre-existing scenario
  (41/41 in the scope-check harness, which was 32 at cycle start).

## Issues Found

### Red round 1 — R1-R5 (recorded 2026-09-20; all five FIXED, none accepted, none carried)

The red team returned `RED_VERDICT: BROKEN` with five findings. The operator
decided the full fix for all five; every one was independently reproduced before
and after. Two are criterion defects in this cycle's own text (R1, R2) and three
are implementation defects in `tools/sdd-scope-check-selftest.py` (R3, R4, R5).
Each fix is mutation-proven: reverting it alone makes exactly one scenario fail.

| Rn | Sev | Disposition | Where fixed |
|---|---|---|---|
| R1 | HIGH | **FIXED** — the deferral screen was blind to how backlogs are actually written here, and the spec stated its own forbidden outcome in vocabulary its own phrase list did not contain. The list is widened from 5 phrasings to a 16-row table, and the claim is corrected: **marker adjacency is exact, phrase coverage is a best-effort screen**, with a reviewer still reading the section | `docs/spec/requirements-artifacts.md` §`## Out of Scope` Discipline; mirrored in `docs/requirements/functional/requirements-structure.md` REQ-REQ-HARNESSP6-001 |
| R2 | MEDIUM | **FIXED** — the scope is restated as an **enumeration over the glob** `docs/ws/*/verification.md`, never a hand-list, with the obligation that a conforming run reports one row per returned path and that rows-walked equals paths-returned, both derived from the same run. The sweep was then re-run over all **6** paths (below) | the spec, the requirement, and the §Criteria row for REQ-REQ-HARNESSP6-001 in this report |
| R3 | MEDIUM | **FIXED** — key rule 2 is gated on a genuinely **structureless** file (a `.jsonl`/`.ndjson`/`.csv`/`.tsv`/`.log`/`.txt` record file, or Markdown with no heading) instead of on "not Markdown". A source file has functions and classes, so a heading parser finding nothing in it is a limitation of the parser, not a property of the file. The rule is narrowed, not deleted — the `.jsonl` case it exists for is asserted in the same scenario | `file_structure()` in `tools/sdd-scope-check-selftest.py`; reasoning in `docs/spec/harness-loop-control.md` §Convergence Signal and `skills/sdd-orchestrate/references/loop-control.md` |
| R4 | MEDIUM | **FIXED** — a path absent from the checkout now yields **no** cluster key. Absence is not evidence of structurelessness, so it can no longer discard the section discriminator and cluster two findings naming different sections of a path nobody can see | `file_structure()` → `ABSENT_PATH`, consumed by `convergence_key()`; stated in both documents above |
| R5 | LOW | **FIXED** — `_headings()` is fence-aware: a `#` inside a fenced block is a comment or an example, not a heading. Latent today, but it is the same fence-blindness class REQ-GC-HARNESSP6-004 closed in `tools/sdd-gc.py`, surviving in the sibling parser key rule 2 newly depends on, and this cycle is terminal | `FENCE` / `_headings()` in `tools/sdd-scope-check-selftest.py` |

**`reproduce:` lines.**

- R1 (defect, at `fa44dc4`): `git show fa44dc4:docs/ws/harness-p4/verification.md | sed -n '/^## Next Steps/,$p' | grep -icE 'deferred to|carried to|queued for|re-raise in that cycle|next cycle'` → **0** on a §Next Steps that is a literal four-item successor-cycle backlog; the same command over `docs/ws/harness-p3/verification.md` also returns **0**. R1 (fixed): the 16-row screen returns **4** hits on that p4 section and **11** on the p3 section.
- R2 (defect): `ls docs/ws/*/verification.md | wc -l` → **6**, against the **3** paths the verify stage walked. R2 (fixed): the six-row table below, one row per returned path.
- R3: `python3 tools/sdd-scope-check-selftest.py 2>&1 | grep '^PASS L10'` — the `.py` pair renders no cluster while the `.jsonl` control still renders one. Reverting the gate to "not Markdown" prints `py-noise 1 cluster(s)` and fails L10.
- R4: `python3 tools/sdd-scope-check-selftest.py 2>&1 | grep '^PASS L11'` — two findings naming `§A` and `§B` of an absent `docs/spec/gone.md` render nothing. Reverting the absence branch makes L11 fail.
- R5: `python3 tools/sdd-scope-check-selftest.py 2>&1 | grep '^PASS L12'` — a Markdown file whose only `#` line is inside a fenced shell block parses to `[]` sections and its two-layer cluster renders. Reverting to the fence-blind `_headings()` drops the cluster and fails L12.

**The R2 re-run, one row per path the glob returned (6 of 6, 2026-09-20).**

| # | Path (`docs/ws/*/verification.md` §Next Steps) | phrase hits | live | note |
|---|---|---|---|---|
| 1 | `default` | 2 | **2** | pre-existing, outside this repair's write scope — see the blocked-write note below |
| 2 | `harness-p2` | 0 | 0 | — |
| 3 | `harness-p3` | 12 | **0** | 15 markers added by this repair's annotation pass |
| 4 | `harness-p4` | 4 | **0** | 7 markers added by this repair's annotation pass |
| 5 | `harness-p5` | 6 | **2** | pre-existing; both items are already closed, their markers merely sit *below* the phrase line — see below |
| 6 | `harness-p6` | 0 | 0 | this report; §Next Steps is empty by design |

Scope (i) `docs/requirements/index.md` §Out of Scope returns **0** hits and
**0 live** under the widened screen — the narrowing of rows 14-16 is what keeps
it there: a bare `harness-p<N>` token fires 11 times in that section, every one
a citation rather than a deferral.

**The four remaining live occurrences, stated rather than deferred.** They are
`docs/ws/default/verification.md:233` (`revisit`), `:255` (`Follow-up (minor)`),
`docs/ws/harness-p5/verification.md:311` (`follow-up cycle`, whose `**[Superseded
2026-09-20 …]**` marker sits at `:313`, two lines below the phrase) and `:386`
(`in a cycle that`, marker at `:388`). In all four the underlying item is
already closed or declined; what is wrong is **marker placement**, a one-line
edit each. Both files are other workstreams' artifacts and are outside this
repair's declared write scope, so the repair did not touch them and returns the
four edits as `blocked_writes` for the orchestrator to persist **in this
cycle**. Nothing about them is carried, deferred or queued.

### Critical (blocks release)

- None.

### Minor (can ship, fix later)

**[Dispositions recorded 2026-09-20 at the verify gate — both closed in-cycle,
neither carried.]** Minor 1 is **FIXED**: both `PLAN: INCOMPLETE` rows now cite
`REQ-LINT-HARNESSP6-001`, and the two `GIT_STATE` rows correctly still cite
`REQ-HARN-HARNESSP6-001`; `sdd-skill-lint.py` and its `--self-test` both re-run
clean. Minor 2 is **CLOSED as won't-do, with reasoning**: the self-test
"function" names are inline section labels inside `self_test()`, which is the
established convention of every tool in this corpus — none of them defines
`def test_*`. The traceability cells say "self-test section N" and so misstate
nothing, and the sections demonstrably run and are mutation-killed. Renaming
them to real functions would be a refactor of three tools for a naming
convention this corpus does not use. Not deferred: decided.


- **Mis-attributed `reason` strings on the two `PLAN: INCOMPLETE` lint rows.**
  `tools/sdd-skill-lint.py:249` and `:256` attribute those `REQUIRED` rows to
  **REQ-HARN-HARNESSP6-001** (the git-state requirement). The requirement that
  actually mandates them is **REQ-LINT-HARNESSP6-001**; REQ-HARN-HARNESSP6-001 is
  the correct citation only for the two `GIT_STATE` rows at `:265` and `:272`.
  The rows themselves are correct and both fire under mutation — this is a
  citation defect in operator-visible text, not a behavioural one. It is a
  two-token edit in a file outside this stage's write scope, so it is reported
  for the orchestrator to repair in-cycle or to close with reasoning; it is not
  carried anywhere.
- **Self-test section labels read like function names but are not callable.**
  The traceability Test cells name `test_stale_chain_skips_closed_workstream`,
  `test_shared_spec_staleness_folds` / `_severity` and
  `test_qimpl_definition_is_fence_symmetric`. These are **comment labels** on
  inline sections 9–12 of `self_test()` (`tools/sdd-gc.py:1590`, `:1634`,
  `:1687`), not defined functions — `grep -n "def test_…"` returns nothing. The
  cells do say "self-test section N", so nothing is misstated, and the sections
  demonstrably run (`--self-test` rc=0, and its summary line names the
  fence-symmetry case). Recorded so a later reader searching for the function by
  name is not misled. No repair is required for correctness; if the orchestrator
  prefers, the labels can be promoted to real functions, and if not, this closes
  as won't-do — the corpus convention is inline self-test sections.

**Carry-or-close from the previous report.** There is none to perform: no file
previously existed at `docs/ws/harness-p6/verification.md`, so this write replaces
nothing and no prior Minor is at risk from the overwrite. The harness-p5 report
belongs to a different workstream and is not this path's predecessor; its own
§Next Steps items were drawn into this cycle as scope items 4, 6 and 7 and are
closed by REQ-LINT-HARNESSP6-001, REQ-LINT-HARNESSP6-002 and
REQ-PLAN-HARNESSP6-001 respectively.

**Close-out findings.** CO-1 is **discharged** — its §Next Steps half ran at this
stage (see REQ-REQ-HARNESSP6-001, scope ii). CO-2 is **closed** — the
`arbitrated-handoff.md` cross-reference landed at `:87` and the traceability cell
no longer claims otherwise. CO-3 is **closed** — the close-out criterion was
narrowed to the closed-workstream predicate and the marker-independent delta is
recorded in the kickoff's §Out of scope as intended behaviour.

## Recommendation

- [x] Ship as-is — **subject to the red round**, which is outstanding.
- [ ] Fix critical issues then ship (invoke sdd-replan)
- [ ] Significant rework needed (invoke sdd-replan)

This report is `status: pending-red`: blue passed, the red verdict is pending. It
is **not** DONE and **not** a replan trigger. The orchestrator dispatches the red
team, gates, and performs the `pending-red → pass` flip in this frontmatter and in
the `Verified` cells of `docs/ws/harness-p6/traceability.md` immediately before
its own commit. The active plan may be archived to
`docs/ws/harness-p6/plan-history/` after that flip.

## Terminality

The cycle's terminality claim holds as the kickoff defined it — **no carried
work**, which is not the same as "no future defect can ever be found":

- Every requirement this workstream traces reads `pending-red`, which is the
  would-be-`pass` value while a red round is outstanding. **No row reads `fail`
  and no row reads `descoped`.**
- Nothing closes as a deliberate `fail`.
- The one item that could not be delivered as specified — L2 — was **descoped at
  replan inside this cycle** (replan 1 of 3), not carried. Its reduced form
  shipped and is exercised by nine scenarios.
- The deferral sweep leaves **0 live** deferral phrases across all three checked
  scopes, so `docs/requirements/index.md` §Out of Scope holds settled exclusions
  with reasoning and no latent successor-cycle work.
- The two Minors above are stated for in-cycle repair or won't-do closure. Neither
  is phrased as carried, deferred or queued, and neither appears in §Next Steps.

## Next Steps

**This section is deliberately empty.** That is the intended terminal outcome of
this cycle's DONE rule, not an omission: no item is held over for any future
cycle. (This sentence deliberately avoids the screen's own vocabulary, so the
declaration of emptiness cannot itself register as a live entry — the
self-reference hazard that fired twice earlier in this cycle, on a block-level
sweep marker and on an acceptance criterion that quoted its own search string.) The drift sweep contributed nothing to route here — the
shared-spec `[stale-chain]` class was demoted to `info` and removed from the DONE
routing by REQ-GC-HARNESSP6-003 precisely so that it could not append a line to a
section REQ-REQ-HARNESSP6-001 forbids from holding anything, and there are **0**
plan-level `[stale-chain]` findings and **0** fail-class findings to route. The
two Minors above are recorded under §Issues Found for in-cycle disposition and
are not repeated here.
