---
domain: GC
last_updated: 2026-09-20
status: Approved
research_refs: [RS-HARNESSP2-001, RS-008, RS-HARNESSP3-001, RS-HARNESSP5-001, RS-HARNESSP6-001]
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
above; `--self-test` builds a temporary fixture tree and asserts that
`--report` on it exits 0, passes the linter's size warnings through to the
summary line and emits no fail finding; on the live repository `--report`
exits 0 with no fail finding (the linter's size-warning count is a moving
number — three were observed on 2026-09-17 at commit 5e6142b, and
REQ-SKILL-HARNESSP2-007 removes one — so it is not an acceptance pin);
`--self-test` exits 0; `--fix nonexistent-rule` exits 2.
[Priority: must]

### REQ-GC-HARNESSP2-002: Sweep classification — checkable now, needs code, not mechanical
The tool must implement the RS-HARNESSP2-001 Q4 sweep table as follows. **Delegated to the linter (checkable now)**: skill structure / forbidden phrases / `REQUIRED` markers / ordinals / size; `references/` links and backtick paths; `docs/spec/*.md` pointers from skills; known drift phrases; kickoff `date:` / `research_id:` presence. **Implemented in gc (needs code)**: cross-links inside `docs/` (spec↔spec, requirement→spec `(see …)`, `research_refs`, `requires:` ids exist — the linter's two regexes over `docs/**/*.md` plus id existence for `RS-` / `REQ-` / `Q-IMPL-`); the staleness chain research → requirements → specs → plan → verification by `last_updated`, walked per workstream under marker `4` via plan `traces to` → spec `requires:` → category files (`docs/spec/ws-staleness.md`), never via a traceability file; orphan Q-IMPL classes (i) referenced-but-undefined, (ii) defined-never-referenced and (iii) `Spec reference` section missing / broken `[superseded by …]` chain, under the counting rule of REQ-GC-HARNESSP2-003; empty traceability cells under the `sdd-verify` Step 3b policy (flag Spec-empty rows and Implementation-filled/Test-empty rows only); aggregate `docs/requirements/traceability.md` equals `regenerate(per-ws files)` under marker `4` (`docs/spec/ws-traceability.md` contract); index ↔ directory consistency (`research/index.md` rows ↔ `RS-*` dirs; `requirements/index.md` Files table ↔ category files; spec approval scoped to the workstream — with `--workstream <id>`, every spec **traced by that workstream's plan** (live plan-walk per `docs/spec/ws-staleness.md`: task `traces to` → spec) must be `status: Approved` when `docs/ws/<id>/plan.md` exists, **fail**; without `--workstream`, the unscoped form — any non-Approved spec while any plan exists — is **warn** only, because under marker `4` another workstream may legitimately hold Draft specs); `plan-history` naming discipline (`-replan-` only from `sdd-replan`, REQ-HARN-003). **Excluded (not mechanical)**: new drift of skill text from spec wording, and semantic orphaning — noted in `--help` as review territory. Severities: cross-links, undefined Q-IMPL (i), naming discipline and index mismatch (including the workstream-scoped spec-approval form; the unscoped form is warn) are **fail**; staleness, Q-IMPL (iii), empty cells and aggregate drift are **warn**; Q-IMPL (ii) is **informational** (not a defect per `deviation-protocol.md` — entries live in their specs). (see RS-HARNESSP2-001 Q4 sweep table)
**Acceptance**: `--help` prints the three classes with their rules; the
`--self-test` fixture tree (temporary, two workstreams, one holding a Draft
spec traced only by the other's plan) yields 0 undefined Q-IMPL, the fixture's
known informational Q-IMPL (ii) count, 0 dead `docs/` cross-links, a
spec-approval **fail** only with `--workstream` naming the tracing workstream
and a **warn** without it, and an aggregate-drift warning iff the fixture's
shared traceability differs from regeneration; the self-test fixtures trigger
each fail rule once. (Observed on the live repository on 2026-09-17 at commit
5e6142b: 0 undefined, 8 informational (ii), 0 dead cross-links — reference
values, not pins.)
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
**Acceptance**: the `--self-test` fixture tree (temporary) contains a known
set of definitions, of ids both defined and referenced, of defined-only ids, a
fenced and an inline-backtick template-example id, a `docs/research/` citation
and a foreign-`<WS>` placeholder, and the tool reports exactly the fixture's
definition / both / defined-only counts with **0** referenced-only (every
excluded class skipped); the same fixture with a real `Q-IMPL-999` reference
added outside a fence produces one fail finding. (Observed on the live
repository on 2026-09-17 at commit 5e6142b: 28 definitions, 20 both, 8
defined-only, 0 referenced-only, template-example ids `Q-IMPL-003/-007/-021`
skipped — reference values, not pins.)
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

### REQ-GC-HARNESSP3-001: Prose about another repository's artifacts must not quote its `Q-IMPL` id tokens
A documentation **convention** — not a code change — must state that prose in
this repository describing another repository's artifacts (a toy clone, an
evidence record, a pilot log) must not quote that repository's `Q-IMPL-NNN` id
tokens verbatim; paraphrase or fence them instead. `tools/sdd-gc.py`'s
`qimpl-undefined` rule behaved **correctly** when it flagged such a mention on
2026-09-18: the ids genuinely are undefined in this corpus. Scoping the rule to
"ids that look local" is **declined** — that is not decidable from text and
would weaken a `fail`-class rule. One sentence in `CLAUDE.md` and in
`skills/sdd-orchestrate/references/drift-sweep.md` is the whole change. (see
RS-HARNESSP3-001 Q8-IN row 2, §B12 — spec-read: the disposition rests on reading
the gc sweep that produced the finding)
**Acceptance**: `references/drift-sweep.md` states the convention and records
that the `qimpl-undefined` rule is unchanged; `python3 tools/sdd-gc.py --report`
raises no new `qimpl-undefined` finding on the amended prose, and the rule still
fires on a genuinely undefined local id.
[Priority: should]

### REQ-GC-HARNESSP5-001: aggregate regeneration must never silently drop a row
`tools/sdd-gc.py`'s `[traceability-aggregate]` sweep and its
`--fix traceability-aggregate` rewrite must not be able to **lose** a
per-workstream traceability row. Today `table_cells()` splits a row on **raw**
`|` and `trace_rows()` keeps only rows yielding exactly six cells, so a row
whose cell content contains a literal pipe — a grep alternation, a code-span
alternation — is silently discarded from `docs/requirements/traceability.md`.
Two rows of `docs/ws/harness-p4/traceability.md` were lost this way at commit
3b50220 and stayed missing until they were recovered on 2026-09-20 (commit
9c7cb9c) by rewriting the pipes as `&#124;`. Markdown-legal `\|` escaping does
**not** save the row either (verified: gc drops those too). Two changes are
required: (a) the row splitter must split on **unescaped** pipes only, treating
`\|` as literal cell content and re-emitting it unchanged on regeneration; and
(b) a row that still does not yield the expected cell count must raise a
**fail** finding, rule id `traceability-rowdrop`, naming the file and the row
(`<file>:<line>`), instead of being dropped. Data loss must be impossible
without a visible finding. This is a rule **addition** scoped to the aggregate
sweeps — no existing rule id, severity or counting rule changes, and no
allowlist is introduced. (workstream `harness-p5`; see
`docs/ws/harness-p5/traceability.md` recovery commit 9c7cb9c and
`docs/spec/ws-traceability.md` §Aggregation Contract)
**Acceptance**: `python3 tools/sdd-gc.py --self-test` exits 0 with three new
fixture assertions — a per-ws row whose `Test` cell holds `\|` survives
`--fix traceability-aggregate` byte-for-byte (the escape is re-emitted, the row
is present in the regenerated aggregate), the same row raises **no**
`traceability-rowdrop` finding, and a genuinely malformed row (five cells, no
escaped pipe) raises exactly one `[traceability-rowdrop]` **fail** finding whose
location is `<file>:<line>`; `python3 tools/sdd-gc.py --report` on this
repository exits 0 with no `traceability-rowdrop` finding and
`grep -c '^| REQ-ARB-HARNESSP4-003 \|^| REQ-CYCID-HARNESSP4-001 ' docs/requirements/traceability.md`
prints `2` (both recovered harness-p4 rows are still present in the
aggregate; a row-anchored presence assertion rather than a corpus-wide count of an
escape sequence, which every future correctly-escaped cell would inflate);
`python3 tools/sdd-skill-lint.py` exits 0.
[Priority: must]

### REQ-GC-HARNESSP6-001: `[stale-chain]` must skip a closed (`status: pass`) workstream
`tools/sdd-gc.py`'s `[stale-chain]` sweep must not flag a plan under
`docs/ws/<id>/` whose sibling `verification.md` carries `status: pass`. A closed
workstream's plan is correctly older than specs and requirement files that later
cycles amended — it *should* be older — so the finding is a structural false
positive whose count grows monotonically with every subsequent cycle. Measured
at the branch point `ac0fb43`, the rule emitted 19 such lines (13 on `harness-p3`'s plan,
6 on `harness-p4`'s), split between the `plan older than a traced spec` and
`plan older than a traced requirement category file` sub-kinds; both sub-kinds
must be skipped for a closed workstream. An open workstream (no
`verification.md`, or one that is not `status: pass`) is unaffected, so real
in-flight staleness still surfaces. This is a scoping change to an existing
rule — no new rule id, no severity change elsewhere, no allowlist. (workstream
`harness-p6`; kickoff §Scope item 1, decided at DISCUSS; RS-HARNESSP6-001
§Measured baseline)
**Acceptance**: `python3 tools/sdd-gc.py --self-test` exits 0 with new fixture
assertions — a plan in a workstream whose `verification.md` is `status: pass`
raises no `[stale-chain]` finding of either sub-kind, and the same plan in a
workstream whose `verification.md` is `status: fail` or absent still does;
`python3 tools/sdd-gc.py --report` on this repository reports **zero**
`[stale-chain]` findings located in `docs/ws/harness-p3/plan.md` or
`docs/ws/harness-p4/plan.md`.
[Priority: must]

### REQ-GC-HARNESSP6-002: the shared-spec staleness fan-out folds to one finding per (spec, category file) pair
`[stale-chain]`'s spec-versus-requirement comparison must emit **one** finding
per `(downstream spec, upstream category file)` pair, naming the requirement ids
that triggered it, instead of one finding per `(spec, requirement id)` pair.
Today the per-id loop multiplies a single staleness relation by the spec's
`requires:` length: at this branch point 44 warning lines fan out from only
three pairs (`docs/spec/telemetry.md` ← `functional/telemetry.md`, 39;
`docs/spec/telemetry.md` ← `integration/skill-lint.md`, 3;
`docs/spec/adversarial-verify.md` ← `integration/skill-lint.md`, 2). The fold is
a presentation change that drops no comparison and therefore has a provably zero
false-negative cost: every staleness relation still surfaces, with the full id
list in the message. No date is bumped to silence anything. (workstream
`harness-p6`; RS-HARNESSP6-001 Q1 option E, Confidence High)
**Acceptance**: `python3 tools/sdd-gc.py --self-test` exits 0 with a fixture
where one spec requiring three ids from one stale category file yields exactly
**one** `[stale-chain]` finding whose message names all three ids;
on this repository, `python3 tools/sdd-gc.py --report` emits exactly **one**
spec-versus-requirement `[stale-chain]` finding per distinct `(spec, category
file)` pair present in the corpus at the time it runs — verified by a command
that derives both sides rather than pinning a literal: the count of such
findings equals the count of distinct pairs those findings name.
**[Updated: 2026-09-20 — the criterion originally read "exactly **3** findings,
one per pair above", pinning the count measured at the kickoff. By the specs
stage the corpus held **6** distinct pairs (the requirements commit re-dated
five category files, widening the class onto `harness-return-contract.md` and
`harness-chunk-verifier.md`), so the literal was already unsatisfiable. The
count is a property of the shared corpus at run time, not of this change;
pinning it is the fragile-criterion failure recorded as harness-p5's headline
lesson. The fold property — one finding per pair — is what this requirement
actually asserts, and it is stable.]**
[Priority: must]

### REQ-GC-HARNESSP6-003: the folded shared-spec staleness finding is carried at `info`
The folded `(spec, category file)` staleness finding of REQ-GC-HARNESSP6-002
must be emitted at **`info`** severity, not `warn`. Under the v4 shared corpus a
category file is re-dated whenever *any* workstream appends a requirement to it,
so a shared spec lagging that date is the expected steady state rather than a
defect; carrying the class at `warn` is what made the warn class unusable as a
drift signal. The finding is still printed and still counted, so the loss is one
of salience, not visibility, and the severity is reversible in one line if the
class is ever observed hiding real staleness. Only the spec-versus-requirement
sub-class moves; plan-level `[stale-chain]` findings keep their current
severity. (workstream `harness-p6`; RS-HARNESSP6-001 Q1 option C, Confidence
Medium — a severity judgement, not a measurement)
The demotion also moves the class out of the DONE gate's decision-needing
routing, and both places that pin its handling must move with it:
`docs/spec/drift-sweep.md` sweep-table **row 7** (severity `warn` and the
finding's message shape) and the same file's **§DONE routing**, where
`stale-chain` currently sits in the `record | ignore` class. This matters beyond
tidiness: `record` appends to `verification.md` §Next Steps, which
REQ-REQ-HARNESSP6-001 forbids from holding anything, so leaving the routing
unchanged would set two of this cycle's own requirements against each other at
the DONE gate. After this requirement only the **plan-level** sub-class remains
decision-routed; the folded shared-spec class is informational and routes
nowhere.
**Acceptance**: `python3 tools/sdd-gc.py --report` on this repository exits `OK`
with **0** `[stale-chain]` **warnings**, and with every remaining
spec-versus-requirement `[stale-chain]` line emitted at `info` (their number is
whatever the corpus holds at run time and is deliberately not pinned — see
REQ-GC-HARNESSP6-002's dated note);
`python3 tools/sdd-gc.py --self-test` exits 0 with the severity asserted on the
folded finding and unchanged on a plan-level finding; `docs/spec/drift-sweep.md`
row 7 reads `info` for the shared-spec sub-class and its §DONE routing lists
only the plan-level sub-class under `record | ignore`; and a grep of §DONE
routing for the shared-spec class returns no `record` option.
**Depends on**: REQ-GC-HARNESSP6-001 — the "0 `[stale-chain]` warnings"
clause cannot pass until the closed-workstream skip also lands, so a plan must
not schedule this verification before that requirement (m3).
[Priority: must]

### REQ-GC-HARNESSP6-004: the Q-IMPL definition scan must be fence-symmetric with the reference scan
`tools/sdd-gc.py`'s Q-IMPL sweep must treat fenced blocks identically on both
sides of the comparison. References are collected through `visible_lines()`
(fenced lines skipped) while definitions are scanned raw, so a deviation-entry
heading inside a fence registers as a real definition that nothing can ever
reference. A **definition** must therefore be an `^### Q-IMPL-…` line under
`docs/spec/**` that lies **outside** a fenced block, collected through the same
filter the reference side uses: a heading inside a fence defines nothing and
references nothing. The countability rule this creates is an **obligation, not
an allowlist**: an id used in a fenced format illustration must be either an id
that a real, unfenced entry defines elsewhere in the corpus (the present
convention — both illustration ids in `docs/spec/deviation-protocol.md` are
already of this kind) or one of the placeholder ids the tool already excludes.
No marker, language tag or whitelist is introduced, so `CLAUDE.md` §Quality
Checks' "there is no allowlist" statement stays true and the documented
"wrap it in a fenced code block" escape becomes symmetric — a fence can no
longer accidentally *define* a foreign id either. (workstream `harness-p6`;
kickoff §Scope item 5; RS-HARNESSP6-001 Q3, Confidence High — probe 1 found 82
definition ids, all with an unfenced definition and none fence-only; probe 2 ran
the patched scan against this repository with byte-identical output)
**Acceptance**: `python3 tools/sdd-gc.py --self-test` exits 0 with a new case
where a deviation heading inside a fenced block raises no definition and a
reference to an otherwise-undefined id in that fence raises no
`qimpl-undefined`; `python3 tools/sdd-gc.py --report` on this repository reports
the same `qimpl-undefined` and `qimpl-broken-ref` counts as before the change
(both **0**); the module docstring's and `--help`'s counting-rule text state the
fence-symmetric rule.
[Priority: must]
