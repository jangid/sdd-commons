---
domain: GC
last_updated: 2026-09-17
status: Approved
research_refs: [RS-HARNESSP2-001, RS-008]
workstream: harness-p2
---

# Requirements: Drift Sweep (`tools/sdd-gc.py`)

## Overview

A docs-scoped drift-sweep tool, `tools/sdd-gc.py`, that runs lint + staleness +
orphan Q-IMPL + stale cross-link + index-consistency sweeps across `docs/` on a
cadence and parks the resulting fix work without creating an artifact (idea
catalogue item G17, de-risked by RS-HARNESSP2-001 Q4). It is a stdlib-only
sibling of `tools/sdd-skill-lint.py` and `tools/sdd-scope-check-selftest.py`,
following the linter's architecture (rule tables, `flag()` with `fix`, exit
codes, `--self-test`, REQ-LINT-001). It re-implements only rules already stated
as prose in the skills and specs; it never invents a new rule. Its report is
ephemeral gate text (REQ-ORCH-013 analogue); non-mechanical follow-ups land in
the just-completed cycle's `verification.md` §Next Steps — an existing slot —
**never** as plan tasks, because adding a task to a complete plan flips phase
detection back to implement (a sweep must never move the loop).

Standing constraints: REQ-HARN-027 / REQ-ORCH-004 (no `docs/gc/`, no issues
file), REQ-ORCH-014 (gc reads artifacts but is never a phase-detection input),
REQ-HARN-024 (the operator commits `--fix` rewrites), REQ-WS-007 (no staleness
path reads a traceability file — gc's staleness sweep walks the plan chain).

## Requirements

### Tool

### REQ-GC-HARNESSP2-001: `tools/sdd-gc.py` — stdlib-only, `--help`, exit codes
`tools/sdd-gc.py` must be a self-contained Python 3 stdlib-only script with
subcommand-style flags `--report` (default), `--fix <rule>` (apply one
whitelisted mechanical rewrite), `--fast` (lint + links + Q-IMPL only, no
history or date walks — the pre-commit profile), `--workstream <id>` (marker
`4` staleness scope; default all workstreams), `--self-test` and `--help`. Exit
codes: **0** no findings (warnings allowed, counted in the summary line), **1**
at least one fail-severity finding, **2** usage or repository error (not a git
repo, missing `docs/`). It must reuse `tools/sdd-skill-lint.py` for the
skill-side checks by invoking it (never by copying its rule tables) and must
scope its own rules to `docs/**`. (see RS-HARNESSP2-001 Q4 answer)
**Acceptance**: `python3 tools/sdd-gc.py --help` exits 0 and lists the flags
above; on this repository at the 2026-09-17 baseline `--report` exits 0 with
the linter's three size warnings and no fail finding; `--self-test` exits 0;
`--fix nonexistent-rule` exits 2.
[Priority: must]

### REQ-GC-HARNESSP2-002: Sweep classification — checkable now, needs code, not mechanical
The tool must implement the RS-HARNESSP2-001 Q4 sweep table as follows. **Delegated to the linter (checkable now)**: skill structure / forbidden phrases / `REQUIRED` markers / ordinals / size; `references/` links and backtick paths; `docs/spec/*.md` pointers from skills; known drift phrases; kickoff `date:` / `research_id:` presence. **Implemented in gc (needs code)**: cross-links inside `docs/` (spec↔spec, requirement→spec `(see …)`, `research_refs`, `requires:` ids exist — the linter's two regexes over `docs/**/*.md` plus id existence for `RS-` / `REQ-` / `Q-IMPL-`); the staleness chain research → requirements → specs → plan → verification by `last_updated`, walked per workstream under marker `4` via plan `traces to` → spec `requires:` → category files (`docs/spec/ws-staleness.md`), never via a traceability file; orphan Q-IMPL classes (i) referenced-but-undefined, (ii) defined-never-referenced and (iii) `Spec reference` section missing / broken `[superseded by …]` chain, under the counting rule of REQ-GC-HARNESSP2-003; empty traceability cells under the `sdd-verify` Step 3b policy (flag Spec-empty rows and Implementation-filled/Test-empty rows only); aggregate `docs/requirements/traceability.md` equals `regenerate(per-ws files)` under marker `4` (`docs/spec/ws-traceability.md` contract); index ↔ directory consistency (`research/index.md` rows ↔ `RS-*` dirs; `requirements/index.md` Files table ↔ category files; every spec `status: Approved` when a plan exists); `plan-history` naming discipline (`-replan-` only from `sdd-replan`, REQ-HARN-003). **Excluded (not mechanical)**: new drift of skill text from spec wording, and semantic orphaning — noted in `--help` as review territory. Severities: cross-links, undefined Q-IMPL (i), naming discipline and index mismatch are **fail**; staleness, Q-IMPL (iii), empty cells and aggregate drift are **warn**; Q-IMPL (ii) is **informational** (not a defect per `deviation-protocol.md` — entries live in their specs). (see RS-HARNESSP2-001 Q4 sweep table)
**Acceptance**: `--help` prints the three classes with their rules; on the
2026-09-17 baseline the report shows 0 undefined Q-IMPL, 8 informational
Q-IMPL (ii) ids, 0 dead `docs/` cross-links and an aggregate-drift warning
iff the shared traceability differs from regeneration; the self-test fixtures
trigger each fail rule once.
[Priority: must]

### REQ-GC-HARNESSP2-003: Pinned Q-IMPL counting rule with fenced/quoted-example skip
The Q-IMPL sweeps must use exactly this rule: a **definition** is a
`### Q-IMPL-<id>` heading under `docs/spec/**`; a **reference** is any other
occurrence of a `Q-IMPL-` id under `docs/`, `skills/`, `agents/`, `tools/`,
**excluding `docs/research/**`** (research cites foreign-repo ids), **excluding
id-format placeholders** (`Q-IMPL-NNN`, `Q-IMPL-1`, `Q-IMPL-ISSUE42*`,
`Q-IMPL-ISSUE57-001` and any id whose `<WS>` token is not a workstream directory
under `docs/ws/` or a legacy bare counter), and **excluding occurrences inside
fenced code blocks or inline-backtick template examples** — the same skip the
linter's `resolve_backtick_path()` applies — so illustrative ids in templates
(e.g. `docs/spec/chunk-close-review.md`, `deviation-protocol.md`,
`harness-return-contract.md` and their skill mirrors) never count as
references. Ids may be legacy (`Q-IMPL-083`) or workstream-prefixed
(`Q-IMPL-<WS>-NNN`, `docs/spec/ws-ids.md`). The rule and the three reference
commands from RS-HARNESSP2-001 Q4 must appear in the tool's docstring so the
numbers are reproducible. (see RS-HARNESSP2-001 Q4 counting rule)
**Acceptance**: on the 2026-09-17 baseline the tool reports 28 definitions, 20
ids both defined and referenced, 8 defined-only, and **0** referenced-only
(the three template-example ids `Q-IMPL-003/-007/-021` are skipped); a fixture
adding a real `Q-IMPL-999` reference outside a fence produces one fail finding.
[Priority: must]

### REQ-GC-HARNESSP2-004: Finding shape is the linter's
Every gc finding must be printed as `<file>:<line> [<rule>] <message>` followed
by an indented `fix: <remediation>` line (REQ-LINT-001), with `WARN` / `INFO`
prefixes for the non-fail severities (REQ-LINT-002), and the run must end with
one summary line (`OK: N sweep(s) clean, W warning(s), I info` or `FAIL: F
finding(s)`). A finding without `fix:` is a self-test failure. (see
RS-HARNESSP2-001 Q4 "open targeted fix tasks")
**Acceptance**: the self-test asserts a non-empty `fix` on every emitted
finding; the summary line is the last line of stdout.
[Priority: must]

### Cadence and routing

### REQ-GC-HARNESSP2-005: Cadence — orchestrator at entry and at DONE; pre-commit optional
`sdd-orchestrate` must run `python3 tools/sdd-gc.py --report` at two moments:
at **entry** (before the workstream picker under marker `4`; before phase
detection under marker `3`), showing a one-line summary (`GC: clean` or `GC: F
fail, W warn — run tools/sdd-gc.py --report`), and at **DONE** (§Transition,
after the verify stage passes review and the operator approves), rendering the
full findings at the DONE gate. Under marker `4` the staleness sweep at DONE is
scoped to the completed workstream (`--workstream <id>`). A pre-commit hook
running `--fast` **may** be adopted (the user's conventions prefer pre-commit;
the repo has no `.pre-commit-config.yaml` today) and is a repository choice,
not a skill requirement; a scheduled routine (`/schedule`, `/loop`) must **not**
be the cadence — it runs outside any cycle, so its fix step would have no gate
and no committer respecting commit ownership. gc never runs between stages and
never blocks a gate: a fail finding at entry is informational to the operator.
(see RS-HARNESSP2-001 Q4 cadence mechanism)
**Acceptance**: `sdd-orchestrate/SKILL.md` names both moments with the command;
a fixture entry with one dead cross-link shows `GC: 1 fail, 0 warn` and still
opens the picker; the skill text contains no `/schedule` or `/loop` cadence.
[Priority: must]

### REQ-GC-HARNESSP2-006: Findings are parked in `verification.md` §Next Steps, never as plan tasks
Routing per finding class at the DONE gate: **mechanical** findings (dead link,
stale `last_updated`, missing index row, naming) are fixed by `--fix <rule>` —
a whitelisted rewrite the operator reviews and commits (REQ-HARN-024); findings
that **need a decision** (orphan Q-IMPL (iii), staleness, aggregate drift) are
offered `record | ignore`, and on `record` the orchestrator appends one line per
finding under the completed cycle's `verification.md` §Next Steps in the shape
`- gc <rule>: <file:line> — <fix>` (marker `4`: `docs/ws/<id>/verification.md`),
which the next cycle's DISCUSS reads; **out-of-scope** findings are noted only.
gc must never create or modify a plan task, never write any file other than
those a `--fix` rule whitelists, and never create `docs/gc/` or an issues file
(REQ-HARN-027, REQ-ORCH-004). (see RS-HARNESSP2-001 Q4 routing table)
**Acceptance**: after a DONE gate with two recorded findings, `verification.md`
§Next Steps has two new `- gc …` lines and `docs/ws/<id>/plan.md` is
byte-identical; `--fix` on a non-whitelisted rule exits 2; `git ls-files docs/`
gains no new path.
[Priority: must]

### REQ-GC-HARNESSP2-007: `--fix` whitelist is explicit and idempotent
The set of rules `--fix` may rewrite must be an explicit module-level list
(initially: dead relative link → nearest resolving path when unique; missing
`requirements/index.md` Files-table row → inserted at sorted position per
`docs/spec/ws-ids.md`; aggregate traceability → regenerated per
`docs/spec/ws-traceability.md`; `plan-history` filename missing its date
prefix → renamed). Each fix must be idempotent (a second run changes nothing)
and must print the paths it changed; `--fix` never touches `last_updated`
fields (that is the owning skill's job and would mask staleness) and never
edits `docs/ws/<other-id>/` when `--workstream <id>` is given. (see
RS-HARNESSP2-001 Q4 routing — mechanical class)
**Acceptance**: running `--fix traceability-aggregate` twice yields an empty
second diff; `--fix staleness` exits 2 with "not a fixable rule".
[Priority: should]
