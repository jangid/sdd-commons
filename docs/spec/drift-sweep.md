---
status: Approved
last_updated: 2026-09-20
requires:
  - REQ-GC-HARNESSP2-001
  - REQ-GC-HARNESSP2-002
  - REQ-GC-HARNESSP2-003
  - REQ-GC-HARNESSP2-004
  - REQ-GC-HARNESSP2-005
  - REQ-GC-HARNESSP2-006
  - REQ-GC-HARNESSP2-007
  - REQ-SKILL-HARNESSP2-004
  - REQ-GC-HARNESSP3-001
  - REQ-GC-HARNESSP5-001
---

# Drift Sweep (`tools/sdd-gc.py`)

## Context

`tools/sdd-skill-lint.py` keeps `skills/` honest; nothing sweeps `docs/`. Dead
cross-links between specs and requirements, stale `last_updated` chains,
orphaned Q-IMPL entries, empty traceability cells and index/directory drift
accumulate between cycles and are found by reviewers by accident.
RS-HARNESSP2-001 Q4 measured which sweeps are mechanical: eight of fifteen are
checkable today through the linter, the rest need a docs-scoped sibling tool
that re-implements rules already stated as prose in the skills and specs — it
never invents a rule. Its report is ephemeral gate text; follow-ups that need
a decision are parked in the completed cycle's `verification.md` §Next Steps,
**never** as plan tasks (a task added to a complete plan flips phase detection
back to implement — a sweep must never move the loop).

This spec defines `tools/sdd-gc.py`: CLI, exit codes, the sweep table with
severities, the pinned Q-IMPL counting rule, the finding shape, the self-test
fixture, the cadence and the routing of findings. It fulfils
REQ-GC-HARNESSP2-001..007 and the gc half of REQ-SKILL-HARNESSP2-004. The
`GC:` gate line is defined here and nowhere else.

## Design

### CLI and Exit Codes (REQ-GC-HARNESSP2-001)

Stdlib-only Python 3, a sibling of `sdd-skill-lint.py` and
`sdd-scope-check-selftest.py` (rule tables, `flag()` with `fix`, `--self-test`).

```
python3 tools/sdd-gc.py [--report] [--fast] [--workstream <id>] [--root <path>]
python3 tools/sdd-gc.py --fix <rule> [--workstream <id>] [--root <path>]
python3 tools/sdd-gc.py --self-test | --help
```

| Flag | Meaning |
|---|---|
| `--report` (default) | run every sweep, print findings and the summary line |
| `--fast` | lint + cross-links + Q-IMPL only; no history or date walks — the pre-commit profile |
| `--workstream <id>` | marker `4`: scope the staleness sweep and the spec-approval rule to `docs/ws/<id>/`; default all workstreams |
| `--fix <rule>` | apply one whitelisted rewrite (§`--fix` Whitelist); prints the paths it changed |
| `--root <path>` | repository root (default: `git rev-parse --show-toplevel`) |
| `--self-test` | build the temporary fixture tree and assert §Self-Test |
| `--help` | flags, the three sweep classes with their rules, the counting rule, the exclusions noted as review territory |

| Exit | Meaning |
|---|---|
| **0** | no fail-severity finding (warnings and info allowed, counted in the summary) |
| **1** | at least one fail-severity finding |
| **2** | usage or repository error: not a git repository, missing `docs/`, unknown `--fix` rule, non-fixable rule |

Skill-side checks are obtained by **invoking** `tools/sdd-skill-lint.py` as a
subprocess and parsing its findings and summary (its size warnings pass
through to gc's summary); gc never copies the linter's rule tables. gc's own
rules are scoped to `docs/**`. `sdd-gc.py` never reads `.sdd/`
(`telemetry.md`) and is never a phase-detection input (REQ-ORCH-014).

### Sweep Table (REQ-GC-HARNESSP2-002)

| # | Sweep | Class | Rule id | Severity | Source of the rule |
|---|---|---|---|---|---|
| 1 | skill structure, forbidden phrases, `REQUIRED` markers, ordinals, size | delegated (lint) | `lint` | as lint reports | `skill-lint-v5.md` |
| 2 | `references/` links and backtick paths in skills | delegated (lint) | `lint` | fail | `skill-lint-v5.md` §Path Resolution |
| 3 | `docs/spec/*.md` pointers from skills | delegated (lint) | `lint` | warn | `skill-lint-v5.md` §Path Resolution |
| 4 | known drift phrases | delegated (lint) | `lint` | fail | `FORBIDDEN` table |
| 5 | kickoff `date:` / `research_id:` present per workstream | delegated (lint) under marker `3` — the linter emits it at any run; gc under marker `4` — emitted at `sdd-orchestrate` entry and DONE (§Cadence) | `kickoff-fields` | fail | `orchestration.md` §Kickoff Artifact |
| 6 | cross-links inside `docs/`: spec↔spec, requirement→spec `(see …)`, `research_refs`, `requires:` ids exist; `RS-` / `REQ-` / `Q-IMPL-` id existence | gc | `xlink-dead`, `id-missing` | **fail** | the linter's two regexes over `docs/**/*.md` + id existence |
| 7 | staleness chain research → requirements → specs → plan → verification by `last_updated`, per workstream via plan `traces to` → spec `requires:` → category files | gc | `stale-chain` | warn | every skill's Phase Detection; `ws-staleness.md` (never a traceability file) |
| 8 | orphan Q-IMPL (i) referenced-but-undefined | gc | `qimpl-undefined` | **fail** | §Q-IMPL Counting Rule |
| 9 | orphan Q-IMPL (ii) defined-never-referenced | gc | `qimpl-unreferenced` | info | `deviation-protocol.md` — not a defect |
| 10 | orphan Q-IMPL (iii) `Spec reference` section missing / broken `[superseded by …]` chain | gc | `qimpl-broken-ref` | warn | `deviation-protocol.md` §Numbering |
| 11 | empty traceability cells — Spec-empty rows; Implementation-filled/Test-empty rows only; an amendment row (Spec differs from the legacy row for the same id, `telemetry.md` §XSPEC) inherits the legacy Verified and is never a gap | gc | `trace-empty` | warn | `sdd-verify` Step 3b policy |
| 12 | aggregate `docs/requirements/traceability.md` == `regenerate(per-ws files)` (marker `4`); **and** no per-ws row is dropped by the row parser | gc | `traceability-aggregate`; `traceability-rowdrop` | warn; `traceability-rowdrop` **fail** | `ws-traceability.md` §Aggregation Contract; §Row-Drop Safety |
| 13 | index ↔ directory: `research/index.md` rows ↔ `RS-*` dirs; `requirements/index.md` Files table ↔ category files; spec approval | gc | `index-research`, `index-requirements`, `spec-approval` | **fail**; `spec-approval` **fail** with `--workstream` (every spec traced by that workstream's plan must be Approved when `docs/ws/<id>/plan.md` exists), **warn** unscoped (any non-Approved spec while any plan exists) | `sdd-specs` / `sdd-plan` Phase Detection; `ws-staleness.md` live plan-walk |
| 14 | `plan-history` naming discipline (`-replan-` only from `sdd-replan`; date prefix) | gc | `plan-history-name` | **fail** | `harness-loop-control.md` §Replan Re-entry Cap (REQ-HARN-003) |
| 15 | new drift of skill text from spec wording; semantic orphaning | **excluded** (not mechanical) | — | — | review / dogfooding; named in `--help` |

**Why the unscoped `spec-approval` is warn**: under marker `4` another
workstream may legitimately hold Draft specs while this one has a plan; only
the specs a given plan traces must be Approved, and that set is computable only
with `--workstream`.

`stale-chain` reads `verification.md` `status: pending-red`
(`adversarial-verify.md`) as "verification exists, not passed".

### Q-IMPL Counting Rule (REQ-GC-HARNESSP2-003)

Pinned so the numbers are reproducible (also in the tool's docstring with the
three reference commands from RS-HARNESSP2-001 Q4):

- **Definition**: a line matching `^### Q-IMPL-[A-Z0-9-]+` under `docs/spec/**`.
- **Reference**: any other occurrence of `Q-IMPL-[A-Z0-9]+(-\d+)?` under
  `docs/`, `skills/`, `agents/`, `tools/`, **excluding**:
  - `docs/research/**` (research cites foreign-repo ids);
  - id-format placeholders: `Q-IMPL-NNN`, `Q-IMPL-1`, `Q-IMPL-ISSUE42*`,
    `Q-IMPL-ISSUE57-001`, and any id whose `<WS>` token is neither a directory
    under `docs/ws/` nor absent (legacy bare counter);
  - occurrences inside **fenced code blocks** (between ``` fences) or inside
    **inline backticks** — the same skip the linter's `resolve_backtick_path()`
    applies — so illustrative ids in templates (`chunk-close-review.md`,
    `deviation-protocol.md`, `harness-return-contract.md` and their skill
    mirrors) never count.
- Ids may be legacy (`Q-IMPL-083`) or workstream-prefixed
  (`Q-IMPL-<WS>-NNN`, `ws-ids.md`).
- Classes: **both** = defined ∧ referenced; **defined-only** → info (ii);
  **referenced-only** → fail (i); (iii) is computed over definitions: the
  entry's `**Spec reference**: §…` heading must exist in the same file (after
  ordinal stripping), and a `[superseded by Q-IMPL-X]` note must name a
  defined id.

Reference values on 2026-09-17 at commit 5e6142b (not pins): 28 definitions,
20 both, 8 defined-only, 0 referenced-only; template-example ids
`Q-IMPL-003/-007/-021` skipped.

### Finding Shape and Summary (REQ-GC-HARNESSP2-004)

The linter's shape, verbatim:

```
<file>:<line> [<rule>] <message>
    fix: <remediation>
WARN <file>:<line> [<rule>] <message>
    fix: <remediation>
INFO <file>:<line> [<rule>] <message>
    fix: <remediation>
OK: N sweep(s) clean, W warning(s), I info        # or:  FAIL: F finding(s), W warning(s), I info
```

`flag(path, line, rule, msg, fix, severity)` with `fix` positional and
required; a finding without `fix` is a self-test failure. The summary line is
always the last line of stdout; lint pass-through findings keep their own
prefix and are counted in the summary.

### Self-Test Fixture (REQ-GC-HARNESSP2-001, -002, -003)

`--self-test` builds a **temporary** tree (`tempfile.mkdtemp`, initialised as a
git repository, removed afterwards) with symbolic counts asserted, never live
numbers:

| Fixture element | Purpose | Assertion |
|---|---|---|
| `docs/.sdd-version` = `4`; workstreams `alpha`, `beta` under `docs/ws/` with `kickoff.md`, `plan.md`, `traceability.md` | marker `4` scoping | picker-free; `--workstream` resolves both |
| shared `docs/spec/a.md` (Approved, traced by alpha's plan), `docs/spec/b.md` (**Draft**, traced only by beta's plan) | `spec-approval` scoping | `--workstream beta` → 1 **fail**; `--workstream alpha` → 0; unscoped → 1 **warn** |
| `D` Q-IMPL definitions across the specs; `B` of them referenced from `skills/x/SKILL.md` prose; `D−B` defined-only | counting rule | reports exactly `D`, `B`, `D−B`, **0** referenced-only |
| one id inside a fenced block, one inside inline backticks, one in `docs/research/RS-1-x/findings.md`, one `Q-IMPL-ISSUE42-001` placeholder | exclusions | none counted |
| a mutation step adding `Q-IMPL-999` outside a fence | (i) | exactly one `qimpl-undefined` fail |
| one entry whose `**Spec reference**` names a missing heading | (iii) | one warn |
| `requirements/index.md` Files table with one category file missing a row; `research/index.md` with one `RS-*` dir unlisted | index rules | one fail each |
| one dead `(see ../spec/nope.md)` link; one `requires: [REQ-ZZ-999]` | `xlink-dead`, `id-missing` | one fail each |
| a `plan-history/replan-foo.md` without date prefix | naming | one fail |
| shared traceability that differs from regeneration | `traceability-aggregate` | one warn; equal → none |
| a per-ws row whose `Test` cell holds `\|` | row-drop safety | row survives `--fix traceability-aggregate` byte-for-byte (escape re-emitted); no `traceability-rowdrop` finding |
| a per-ws row with five cells and no escaped pipe | `traceability-rowdrop` | exactly one **fail** at `<file>:<line>`; the row is not silently dropped |
| a Spec-empty traceability row; an Implementation-filled/Test-empty row; a prose-only row with empty Test | `trace-empty` | two warns, not three |
| a clean copy of the tree | baseline | `--report` exits 0 with no fail; lint size warnings pass through |
| `--fix traceability-aggregate` twice | idempotence | second diff empty |
| every emitted finding | shape | non-empty `fix`; summary line last |
| `--fix nonexistent-rule`, `--fix staleness` | exit codes | 2, with "not a fixable rule" for the latter |

Each fail rule fires exactly once somewhere in the fixture.

### Cadence (REQ-GC-HARNESSP2-005)

| Moment | Command | Rendering |
|---|---|---|
| `sdd-orchestrate` **entry** — before the workstream picker (marker `4`) / before phase detection (marker `3`) | `python3 tools/sdd-gc.py --report` | one line: `GC: clean` or `GC: F fail, W warn — run tools/sdd-gc.py --report`; then the picker opens regardless |
| `sdd-orchestrate` **DONE** — §Transition, after the verify stage passes review and the operator approves | `python3 tools/sdd-gc.py --report [--workstream <id>]` (marker `4`: the completed workstream) | full findings at the DONE gate, with §Routing |
| pre-commit hook (**optional**, repository choice) | `python3 tools/sdd-gc.py --fast` | the hook's own output |

gc never runs between stages, never blocks a gate (a fail at entry is
informational), and is **never** driven by `/schedule` or `/loop` — a routine
runs outside any cycle, so its fix step would have no gate and no committer
respecting commit ownership (REQ-HARN-024).

### Routing at DONE (REQ-GC-HARNESSP2-006)

| Finding class | Rules | Gate action |
|---|---|---|
| mechanical | `xlink-dead` (unique resolution), `index-requirements` row, `traceability-aggregate`, `plan-history-name` | `--fix <rule>` — the operator reviews and commits the rewrite (REQ-HARN-024) |
| needs a decision | `qimpl-broken-ref`, `stale-chain`, `traceability-aggregate` (when the per-ws inputs themselves look wrong), `spec-approval` | `record \| ignore`; on `record` the orchestrator appends `- gc <rule>: <file:line> — <fix>` under the completed cycle's `verification.md` §Next Steps (marker `4`: `docs/ws/<id>/verification.md`; the `## Next Steps` section added to the `sdd-verify` Step 6 template — `adversarial-verify.md` §Skill and Lint Changes, sdd-verify row) — read by the next cycle's DISCUSS |
| out of scope | sweep 15 | note only |

**Dates are never auto-fixed.** REQ-GC-HARNESSP2-006 lists a stale
`last_updated` among the mechanical findings, while REQ-GC-HARNESSP2-007 states
that `--fix` never touches `last_updated`; this spec follows -007 — `stale-chain`
routes to `record | ignore` and the owning skill updates the date (editing it
mechanically would mask the staleness it signals).

gc never creates or modifies a plan task, never writes a file outside a
`--fix` rule's whitelist, never creates `docs/gc/` or an issues file
(REQ-HARN-027, REQ-ORCH-004); the `record` append is the orchestrator's
bookkeeping in an existing section, outside any observed window.

### `--fix` Whitelist (REQ-GC-HARNESSP2-007)

Module-level list `FIXABLE`:

| Rule | Rewrite | Idempotent by |
|---|---|---|
| `xlink-dead` | relative link → the nearest resolving path when exactly one candidate exists (same basename under `docs/`); otherwise left, reported | resolved links no longer match |
| `index-requirements` | insert the missing Files-table row at its ID-sorted position (`ws-ids.md` merge-safe insertion) | row present |
| `traceability-aggregate` | regenerate `docs/requirements/traceability.md` per `ws-traceability.md` (legacy rows in shipped order + per-ws rows stable-sorted by id; cells normalised, empty cell = two spaces) | deterministic output |
| `plan-history-name` | prefix the file with its `last_updated` date (or the commit date) | name matches |

Every fix prints the paths it changed and changes nothing on a second run;
`--fix` never touches a `last_updated` field (the owning skill's job — editing
it would mask staleness) and never edits `docs/ws/<other-id>/` when
`--workstream <id>` is given. Any other rule → exit 2, `not a fixable rule`.

### Row-Drop Safety (REQ-GC-HARNESSP5-001)

The aggregate sweeps must not be able to **lose** a row. Two rules govern the
row parser (`table_cells()`) and the row filter (`trace_rows()`):

1. **Split on unescaped pipes only.** A `\|` inside a cell is literal content,
   not a cell boundary; the parser consumes the escape and the regenerator
   **re-emits it unchanged**, so a round-trip through
   `--fix traceability-aggregate` is byte-identical for that cell. An HTML
   entity (`&#124;`) is ordinary text and was never a boundary. Raw-pipe
   splitting is the defect: it turned a `Test` cell holding a grep alternation
   into seven cells, and the six-cell filter then discarded the row.
2. **A wrong cell count is a finding, never a discard.** When a row still does
   not yield the expected cell count after rule 1, gc emits
   `<file>:<line> [traceability-rowdrop] <message>` at **fail** severity, with
   a `fix:` naming the escape (`write a literal pipe as \| or &#124;`). The row
   is then excluded from the regenerated aggregate for that run — but loudly,
   and the run exits 1, so `--fix traceability-aggregate` is never committed
   over a silent loss.

Scope: this is a rule **addition**. No existing rule id, severity, counting
rule or `FIXABLE` entry changes, and no allowlist is introduced.
`traceability-rowdrop` is **not** fixable (`--fix traceability-rowdrop` → exit
2, `not a fixable rule`): the repair is an author edit to the offending cell.

**Historical evidence.** Two rows of `docs/ws/harness-p4/traceability.md` —
one whose `Test` cell held `'^status: pass | fail'`, one holding
`` `by: leaf | orchestrator` `` — were dropped from
`docs/requirements/traceability.md` at commit 3b50220 and stayed missing until
2026-09-20, when they were recovered in commit 9c7cb9c by rewriting the pipes
as `&#124;`.

### Skill Changes (REQ-SKILL-HARNESSP2-004, gc half)

| Where | Change |
|---|---|
| `skills/sdd-orchestrate/SKILL.md` | entry step: run gc, show the `GC:` line, open the picker; §Transition: run gc at DONE, render findings, `record \| ignore` routing |
| `skills/sdd-verify/SKILL.md` | Step 6 template gains a `## Next Steps` section after `## Recommendation`, documented as the slot for `- gc <rule>: …` and deferral lines — the change is carried **once**, in `adversarial-verify.md` §Skill and Lint Changes (sdd-verify row); today the template ends at `## Recommendation` and only `docs/ws/default/verification.md` carries the section by hand |
| `skills/sdd-orchestrate/USAGE.md` | section: the `GC:` summary, DONE findings and routing |
| `tools/sdd-gc.py` (**new**) | this spec |

### Convention: Do Not Quote Another Repository's `Q-IMPL` Ids (REQ-GC-HARNESSP3-001)

[Added 2026-09-18: spec-read — the disposition rests on reading the gc sweep
that produced the finding. This is a **documentation convention**, not a code
change; the sweep is unchanged.]

Prose in this repository that describes **another** repository's artifacts — a
toy clone, an evidence record, a pilot log — must not quote that repository's
`Q-IMPL-NNN` id tokens verbatim. Paraphrase them, or fence them, instead.

`tools/sdd-gc.py`'s `qimpl-undefined` rule behaved **correctly** when it flagged
such a mention on 2026-09-18: those ids genuinely are undefined in this corpus.
Scoping the rule to "ids that look local" is **declined** — that is not decidable
from text and would weaken a `fail`-class rule.

The whole change is one sentence in `CLAUDE.md` and one in
`skills/sdd-orchestrate/references/drift-sweep.md`, which also records that the
`qimpl-undefined` rule is unchanged.

## Verification

### Automated

- `test_help_lists_flags_and_classes`: `--help` exits 0, names every flag, the
  three classes with their rules, and the exclusions.
- `test_exit_codes`: clean fixture → 0; one dead link → 1; not a git repo,
  missing `docs/`, `--fix nonexistent-rule`, `--fix staleness` → 2.
- `test_lint_is_invoked_not_copied`: gc's module has no `FORBIDDEN` /
  `REQUIRED` tables; the linter's size warnings appear in gc's summary.
- `test_sweep_table_fixture` (§Self-Test): every row's assertion.
- `test_qimpl_counting_rule`: `D`, `B`, `D−B`, 0 referenced-only; the
  `Q-IMPL-999` mutation → one fail; each exclusion class skipped.
- `test_finding_shape_and_summary`: every finding has a non-empty `fix`;
  summary line last; `WARN`/`INFO` prefixes.
- `test_workstream_scoped_spec_approval`: fail only with `--workstream beta`;
  warn unscoped.
- `test_row_drop_safety`: an escaped-pipe cell round-trips through
  `--fix traceability-aggregate` byte-for-byte and raises no finding; a
  five-cell row raises exactly one `[traceability-rowdrop]` fail naming
  `<file>:<line>`; `--fix traceability-rowdrop` → exit 2.
- `test_fix_idempotent`: `--fix traceability-aggregate` twice → empty second
  diff; `--fix` never changes a `last_updated`; never writes under another
  workstream.
- `test_cadence_text`: `sdd-orchestrate/SKILL.md` names both moments with the
  command; contains no `/schedule` or `/loop` cadence; a fixture entry with one
  dead link shows `GC: 1 fail, 0 warn` and still opens the picker.
- `test_record_routing`: after a DONE gate with two recorded findings,
  `verification.md` §Next Steps has two new `- gc …` lines, `plan.md` is
  byte-identical, `git ls-files docs/` gains no new path.
- `test_live_repo_clean`: on this repository `--report` exits 0 with no fail
  finding (warn/info counts are not pinned).

### Manual

- Run `--report` on the live repository after this cycle and compare the
  Q-IMPL counts with the reference values (drift expected: this cycle adds
  `Q-IMPL-HARNESSP2-*` entries).

### Acceptance Criteria

- [ ] CLI flags, exit codes 0/1/2, stdlib-only, linter invoked not copied, rules scoped to `docs/**` (REQ-GC-HARNESSP2-001)
- [ ] Fifteen-row sweep table with class, rule id and severity as specified; unscoped `spec-approval` warn, scoped fail (REQ-GC-HARNESSP2-002); row 12 carries the second rule id `traceability-rowdrop` at fail (REQ-GC-HARNESSP5-001)
- [ ] Pinned counting rule with the four exclusion classes, in the docstring with the reference commands (REQ-GC-HARNESSP2-003)
- [ ] Linter finding shape, `WARN`/`INFO` prefixes, required `fix`, summary line last (REQ-GC-HARNESSP2-004)
- [ ] Entry and DONE cadence in `sdd-orchestrate`; `GC:` line; no scheduler cadence; never blocks a gate (REQ-GC-HARNESSP2-005)
- [ ] Routing table; `record` appends `- gc <rule>: <file:line> — <fix>` to §Next Steps; no plan mutation; no new path under `docs/` (REQ-GC-HARNESSP2-006)
- [ ] Explicit `FIXABLE` list of four rules, idempotent, prints paths, never touches `last_updated` or another workstream (REQ-GC-HARNESSP2-007)
- [ ] Skill changes tabled (REQ-SKILL-HARNESSP2-004)
- [ ] `python3 tools/sdd-gc.py --self-test` exits 0; `python3 tools/sdd-skill-lint.py` exits 0
- [ ] `references/drift-sweep.md` states the convention and records that the `qimpl-undefined` rule is unchanged; `CLAUDE.md` carries the same sentence (REQ-GC-HARNESSP3-001)
- [ ] `python3 tools/sdd-gc.py --report` raises no new `qimpl-undefined` finding on the amended prose, and the rule still fires on a genuinely undefined local id (REQ-GC-HARNESSP3-001)
- [ ] Row parser splits on unescaped pipes only (`\|` literal, re-emitted unchanged); a wrong cell count raises one `[traceability-rowdrop]` **fail** naming `<file>:<line>` instead of dropping the row; `traceability-rowdrop` is not in `FIXABLE`; `python3 tools/sdd-gc.py --report` on this repository raises none and `grep -c '&#124;' docs/requirements/traceability.md` prints `2` (REQ-GC-HARNESSP5-001)

## Edge Cases

- **Repository at marker `3`**: no `docs/ws/`; the staleness sweep walks the
  flat `docs/plan.md`; `--workstream` is ignored with a note; `traceability-aggregate`
  is skipped (no per-ws inputs).
- **Workstream with no plan yet**: `spec-approval` does not apply to it;
  `stale-chain` stops at the last existing artifact.
- **`(see …)` pointing at a heading anchor** (`file.md#section`): the file
  must exist; the anchor is resolved after ordinal stripping and a miss is
  `xlink-dead` at warn severity (anchors drift more than files).
- **Two `--fix` candidates for a dead link**: not rewritten; reported with
  both candidates in the `fix:` text.
- **Huge `docs/`**: gc reads each file once; no history walk except
  `plan-history/` listing; `--fast` skips dates entirely.
- **Lint unavailable** (`tools/sdd-skill-lint.py` missing): exit 2 with the
  path named.

## Cross-Spec Consistency (XSPEC)

- `skill-lint-v5.md` §Finding Shape and §Severity Tier are reused verbatim;
  gc adds an `INFO` prefix for the informational tier — additive.
- `deviation-protocol.md` §Numbering: definitions live in specs, no index;
  `[superseded by Q-IMPL-NNN]` note — the (iii) rule follows it; (ii) is
  informational per its "no separate index" principle.
- `ws-traceability.md` §Aggregation Contract: `traceability-aggregate` compares
  against the same regeneration and `--fix traceability-aggregate` performs it.
- `ws-staleness.md` live plan-walk: `stale-chain` and scoped `spec-approval`
  use it; no traceability file is read (REQ-WS-007).
- `ws-ids.md`: legacy and `<WS>`-prefixed Q-IMPL ids; ID-sorted insertion for
  the index row fix.
- `harness-loop-control.md` §Replan Re-entry Cap depends on `-replan-` naming
  — `plan-history-name` protects it.
- `orchestration.md` §Driver Phases: entry (before the picker) and DONE
  (§Transition) are the two moments — recorded there as Q-IMPL-HARNESSP2-008.
- `adversarial-verify.md`: `pending-red` read as not-passed; the `## Next
  Steps` template section (its sdd-verify row) is the slot, shared with `- Rn accepted …` lines in §Issues Found → Minor (different
  sections, no collision).
- `telemetry.md`: gc never reads `.sdd/` — consistent with the
  non-interference table.
- **No unresolved contradictions.**

**harness-p3 pass (2026-09-18).** No extractable type definitions in
drift-sweep.md. The `qimpl-undefined` rule id and its `fail` class are unchanged
here and in the sweep table; the new convention adds no rule id, no exit code and
no `--fix` entry, so the CLI contract in §CLI and Exit Codes is untouched.

## Open Questions

1. **Adopt a `.pre-commit-config.yaml` running `--fast`?** Default: propose it
   at the DONE gate of this cycle as a repository choice; not a skill
   requirement.
2. **Should `qimpl-unreferenced` (info) be silenced by default?** Default:
   shown; `--quiet-info` may be added later.
3. **Anchor resolution for `(see file.md#section)`**: Default: warn, as above.

## Implementation Questions

### Q-IMPL-HARNESSP2-050: Fixture lint delegation uses a `suite_rules=False` shim
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Self-Test Fixture / §Sweep Table rows 1–5
**Decision**: The self-test runs the linter as a subprocess via a `-c` importlib shim with `Linter(root, suite_rules=False)` because the REQUIRED/version-gate rows fail any tree that lacks the real skill suite, making the "clean copy → exit 0" assertion impossible otherwise. Production runs never flip it.
**Rationale**: The linter CLI exposes no such flag; the shim is the smallest change that keeps "lint is invoked, never copied".
**Date**: 2026-09-18 (Chunk 4)

### Q-IMPL-HARNESSP2-051: Finding location rendered exactly as the linter emits it
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Finding Shape and Summary
**Decision**: gc renders `<file>:<line>: [<rule>] <msg>` (colon after the location) — the linter's literal shape — rather than the spec block's `<file>:<line> [<rule>]`.
**Rationale**: "The linter's shape, verbatim" wins over the illustrative block, so pass-through and native findings are indistinguishable.
**Date**: 2026-09-18 (Chunk 4)

### Q-IMPL-HARNESSP2-052: `xlink-dead` skips `docs/**/plan-history/**`
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 6
**Decision**: Archived plans are frozen snapshots whose relative links were valid at their original location; the live tree holds 38 such historical links and rewriting them via `--fix` would falsify history.
**Rationale**: Narrows row 6's `docs/**/*.md` glob deliberately.
**Date**: 2026-09-18 (Chunk 4)

### Q-IMPL-HARNESSP2-053: `plan-history-name` exempts `verification-*.md` and checks `-replan-` provenance by body text
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 14
**Decision**: Pre-v4 hand-suffixed verification snapshots are not plan archives and are exempt; `-replan-` archives are checked by requiring the body to mention a replan, since no archive-reason field exists.
**Rationale**: No mechanical provenance signal is available.
**Date**: 2026-09-18 (Chunk 4)

### Q-IMPL-HARNESSP2-054: Q-IMPL reference exclusion also skips double-quoted literals and one-line-wrapped inline-code spans
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Q-IMPL Counting Rule
**Decision**: Required to reproduce the pinned 0 referenced-only (e.g. `"Q-IMPL-007"` at deviation-protocol.md and a wrapped span in leaf-return.md would otherwise be false fails). Small false-negative risk accepted.
**Rationale**: The research's "fenced/quoted examples" skip, applied literally.
**Date**: 2026-09-18 (Chunk 4)

### Q-IMPL-HARNESSP2-055: `id-missing` scope is `requires:`, `research_refs` and `(see RS-…)` ids only
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 6
**Decision**: Bare REQ/RS mentions in prose are template examples and are not checked; `(see …)` `.md` targets resolve against the file dir, `docs/spec/`, `docs/`, then repo root; REQ ids count as defined from `### REQ-…` headings or first-column table rows under `docs/requirements/*/*.md`.
**Rationale**: Keeps the sweep free of traceability-file reads and prose false positives.
**Date**: 2026-09-18 (Chunk 4)

### Q-IMPL-HARNESSP2-060: `kickoff-fields` is gc's own sweep under marker 4
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 5
**Decision**: Under marker 4 the linter cannot see `docs/ws/*/kickoff.md`, so gc emits row 5 itself, unscoped by `--workstream`; under marker 3 the linter owns it and gc skips. The plan's Chunk 5 task list omitted row 5; recorded here.
**Rationale**: Matches the sweep-table row; closes a plan omission.
**Date**: 2026-09-18 (Chunk 5)

### Q-IMPL-HARNESSP2-061: `stale-chain` compares dates strictly and only annotates `pending-red`
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 7
**Decision**: Upstream `last_updated` must be strictly greater than downstream to flag; equal dates are never stale; verification `date:` is accepted as an alias; missing dates are skipped; a `pending-red` verification is rendered as "verification exists, not passed" but yields no finding when newer than its plan (pass status is sdd-verify's job).
**Rationale**: Avoids same-day false positives and keeps staleness separate from verdict.
**Date**: 2026-09-18 (Chunk 5)

### Q-IMPL-HARNESSP2-062: `trace-empty` scans per-workstream files only and never reads Verified
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 11
**Decision**: Under marker 4 the aggregate is derived, so only `docs/ws/*/traceability.md` rows are scanned; amendment rows (Spec differs from the legacy row for the same id — see `telemetry.md` §XSPEC amendment-row rule) are skipped entirely; the Verified column is sdd-verify Step 3b's and is never checked.
**Rationale**: Prevents double-reporting and respects the amendment-row rule.
**Date**: 2026-09-18 (Chunk 5)

### Q-IMPL-HARNESSP2-063: `--fix index-requirements` inserts within the category block, keyed by Domain
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`--fix` Whitelist
**Decision**: The row is inserted inside its category block before the first row whose Domain sorts after the new domain, else at the block end (the live Files table is not globally sorted); the row is derived from the category file (domain, compressed id range, status, last_updated).
**Rationale**: Satisfies REQ-WS-015 (sorted position, one row per line, never EOF) for the table as it actually exists.
**Date**: 2026-09-18 (Chunk 5)

### Q-IMPL-HARNESSP2-064: `--fix plan-history-name` date source
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`--fix` Whitelist
**Decision**: The date prefix is taken from the archive's `last_updated`, else `git log -1 --format=%as`; a partial date prefix is replaced; `-replan-` provenance failures are never renamed.
**Rationale**: Exactly the spec text, pinned for the self-test.
**Date**: 2026-09-18 (Chunk 5)

### Q-IMPL-HARNESSP2-065: Aggregate regeneration keeps the preamble verbatim
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 12
**Decision**: Per `ws-traceability.md` §Aggregation Contract, `regenerate_aggregate` rewrites only the header and rows; the aggregate's frontmatter (incl. `last_updated`) and prose are kept byte-for-byte; 5-column legacy rows gain a blank Workstream cell.
**Rationale**: Consistent with REQ-GC-HARNESSP2-007 (never touches `last_updated`) and the row-level regeneration contract.
**Date**: 2026-09-18 (Chunk 5)


### Q-IMPL-HARNESSP3-012: The convention's escape hatch is a fenced span, not an allowlist
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Convention: Do Not Quote Another Repository
**Decision**:

Where a foreign `Q-IMPL` id must be reproduced exactly (an evidence quotation
that would lose meaning paraphrased), wrap it in a fenced code block rather than
adding a gc allowlist entry: the sweep's Q-IMPL reference exclusion already skips
fenced content (Q-IMPL-HARNESSP2-054), so no rule change is needed and the
exemption stays visible at the point of use.
**Date**: 2026-09-18 (specs stage)
