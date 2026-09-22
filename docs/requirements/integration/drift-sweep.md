---
domain: GC
last_updated: 2026-09-22
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
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> RS-PIPELINEOBSERVABILITY-001 R9, R11; Q-REQ-PO-I) `[Updated: 2026-09-22]`:
> the **Implemented in gc (needs code)** class gains four rules — the
> snapshot-comparand pair `literal-anchor` (**warn**, folded per file) and
> `self-matching-grep` (**fail**), the `dead-path-citation` rule (**warn**,
> folded per file), all three over `docs/spec/**` + `docs/requirements/**`
> only (REQ-GC-PIPELINEOBSERVABILITY-001, -002, -004), and the `qimpl-malformed`
> class (**fail**, REQ-GC-PIPELINEOBSERVABILITY-003). The `--help` listing, the
> self-test fixture tree and every existing rule's severity are otherwise
> unchanged; none of the new rules joins the `--fix` whitelist
> (REQ-GC-HARNESSP2-007).
> **Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
> 2026-09-22)** over the four rules added to the needs-code class — a listing
> grep over `docs/requirements docs/spec plugins/sdd/skills
> plugins/sdd/agents`; hits in this requirement's own text and in the index
> rows citing it are the statement itself and are excluded.
> Command: `grep -rnE 'needs code|Implemented in gc' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
> hits only in `docs/requirements/**` — this requirement's class heading and an
> REQ-ARB-HARNESSP2 confidence note ("needs code, not research", off-subject) —
> reconciled; no spec or skill text restates the class list; the four rules
> themselves are swept by REQ-GC-PIPELINEOBSERVABILITY-001..-004, each naming
> its `docs/spec/drift-sweep.md` row 16–19.

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
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> RS-PIPELINEOBSERVABILITY-001 R11; Q-REQ-PO-F) `[Updated: 2026-09-22]`: the
> placeholder exclusion "or a legacy bare counter" is narrowed — a bare id is
> well-formed only when a **bare definition** with that counter exists under
> `docs/spec/**` (derived from the definition scan at read time, never from a
> list); a bare reference with no bare definition is reported as
> `[qimpl-malformed]` under marker `4`, not as `[qimpl-undefined]` and not
> skipped (REQ-GC-PIPELINEOBSERVABILITY-003). The fence/backtick skip, the
> `docs/research/**` exclusion, the foreign-`<WS>` placeholder rule and the
> definition/reference vocabulary are unchanged.
> **Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
> 2026-09-22)** over the narrowed "legacy bare counter" exclusion — a listing
> grep over `docs/requirements docs/spec plugins/sdd/skills
> plugins/sdd/agents`; hits in this requirement's own text and in the index
> rows citing it are the statement itself and are excluded.
> Command: `grep -rnE 'qimpl-malformed|legacy bare counter|bare definition' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
> the listing is REQ-GC-PIPELINEOBSERVABILITY-003's: `docs/spec/drift-sweep.md`
> §Q-IMPL Counting Rule "nor absent (legacy bare counter)" — the old side,
> narrowed in place by the dated paragraph below it and carried by
> §`qimpl-malformed` and the narrowed placeholder exclusion — reconciled; no
> `plugins/sdd/**` hit.

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
fail, W warn — run tools/gc.py --report`), and at **DONE** (§Transition,
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
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> RS-PIPELINEOBSERVABILITY-001 R15; Q-REQ-PO-H) `[Updated: 2026-09-22]`: the
> `info` severity gains one narrow exception — a folded `(spec, category
> file)` pair whose spec is **traced by the active workstream's plan**
> (`docs/ws/<id>/plan.md` `traces to`, the live plan-walk of
> `docs/spec/ws-staleness.md`, with `--workstream <id>` given) is emitted at
> **`warn`**; an untraced pair stays `info`. The rationale above holds for
> untraced pairs and is why the exception is narrow: a spec this cycle's own
> plan traces and this cycle's requirements re-dated is not the steady state
> but the cycle's own stale chain, which the consumer-geometry cycle closed by
> argument (its write-scope acceptance section, clause (b)) rather than by a
> gate. gc still never blocks a gate (REQ-GC-HARNESSP2-006): the `warn` routes
> through `record | ignore` at DONE, and the §DONE routing of
> `docs/spec/drift-sweep.md` lists the traced sub-class there beside the
> plan-level one. **Acceptance, added**: `--self-test` gains a case in which a
> folded pair traced by the fixture's active plan is `warn` and an untraced
> pair in the same fixture is `info`, failing when the exception is removed in
> a temp copy; the "0 `[stale-chain]` warnings" clause above is re-read as "0
> warnings on untraced pairs". Leaves REQ-GC-HARNESSP6-001 (closed workstreams
> skipped), -HARNESSP6-002 (fold per pair) and REQ-STALE-001 (the skills' own
> staleness detection) consistent.
> **Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
> 2026-09-22)** over the traced-pair `warn` exception — a listing grep over
> `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in
> this requirement's own text and in the index rows citing it are the statement
> itself and are excluded.
> Command: `grep -rn 'stale-chain' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
> `plugins/sdd/skills/orchestrate/references/drift-sweep.md` routing table and
> "`stale-chain` always routes to `record | ignore` … `--fix` refuses it", and
> `USAGE.md` — reconciled, the traced `warn` routes the same way and is never
> auto-fixed; `docs/spec/drift-sweep.md` §Traced-by-active-plan stale-chain
> pairs are `warn` and §Routing at DONE (added row) — reconciled, they carry
> this exception; the same spec's acceptance "exits `OK` with 0 `[stale-chain]`
> warnings" — reconciled, re-read as "on untraced pairs" by that amendment
> section; the same spec's rules table, closed-workstream skip and
> `pending-red` note — reconciled, unchanged sub-kinds;
> `docs/spec/two-root-linter.md` (a split artefact classified `[stale-chain]`)
> and `docs/spec/pipeline-observability.md` — off-subject and lists.

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

### REQ-GC-PIPELINEOBSERVABILITY-001: `literal-anchor` — a live line-number citation in binding text is a `warn`, folded per file
The tool must gain a rule `literal-anchor` over `docs/spec/**/*.md` and
`docs/requirements/**/*.md`: an occurrence of `[\w./-]+\.md:\d+` is a finding
at **`warn`** severity, **folded to one line per file** carrying the count,
**exempting the sha-pinned form** — a 7-to-40 hex-digit token within 40
characters before the anchor — which is a frozen citation by construction.
**Source-line discipline (stated explicitly, as REQ-GC-PIPELINEOBSERVABILITY-002
and -004 state theirs).** Source: every line outside a fenced block — the
**fence half** of `visible_lines()` (REQ-GC-HARNESSP6-004) — read **whole**;
the **inline-code and quoted-span blanking half is NOT applied** by this rule,
because a line-number citation is almost always written as inline code
(`` `<file>.md:<line>` ``), so a span-blanked source has nothing to match. Measured
on this tree on 2026-09-22 with the pattern above and the sha exemption
applied under both disciplines: fence-only → **69 anchors in 7 files**;
fence-plus-span-blanking (the full `visible_lines()`) → **0 anchors in 0
files** — the rule as previously worded could never fire, which is the defect
this clause closes (requirements review round 5 C1). `docs/research/**` and `docs/ws/**` are **out of
scope by decision**: research spikes and execution records are dated snapshots
by contract, where the line number is the evidence being recorded rather than a
comparand a later reader is asked to trust. The rule never joins `--fix`
(REQ-GC-HARNESSP2-007) and routes `record | ignore` at DONE
(REQ-GC-HARNESSP2-006). Observed: 69 such anchors in 7 binding files on
2026-09-22 (a reference value, never a pin), and the class is behind 12 of the consumer-geometry cycle's 17
blocking review findings — a criterion whose comparand the artifact itself
invalidates. Those 69 anchors in 7 binding files are **not repaired by this
cycle** (Q-REQ-PO-R): they sit in earlier cycles' approved requirement and spec
text, rewriting a shared approved body is a human PR decision rather than a
leaf's, and every one of them names a comparand the anchor's own commit froze.
The rule therefore lands as a standing `warn` floor — the folded per-file lines
the DONE `GC:` line routes `record | ignore` — and the repair, if any, is a
later cycle's bounded task over exactly those 7 files. (see
RS-PIPELINEOBSERVABILITY-001 §Q5, R9, §Mechanical pin R9.)
Touches REQ-GC-HARNESSP2-002 (amended); leaves REQ-GC-HARNESSP2-006/-007 and
REQ-PC-MARKETPLACE-006 (rules live in gc's table, not the hook) consistent.
**Acceptance**: `--self-test` gains a case whose fixture holds one file with
three anchors — one **inside backticks** on a visible line (a finding), one
inside a fenced block (no finding) and one sha-pinned on a visible line (no
finding) — and reports exactly one folded `literal-anchor` warn naming that
file with count **1**, so the source-line discipline is what the case decides;
the case fails when the rule is removed in a temp copy, and fails with count 0
when the span-blanking half is applied in a temp copy; `--help` lists the rule
in the gc class at `warn`; `--report` on this repository exits `OK` with the
rule's folded lines counted at run time (7 files on 2026-09-22 — a reference
value, never a pin) and the run's exit status is unaffected by them (`warn`
never fails `--report`); a grep of the `--fix` whitelist for the rule name
returns nothing.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG, 2026-09-22)** over the `literal-anchor` source-line discipline — a listing grep over `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in this requirement's own text and in the index rows citing it are the statement itself and are excluded.
Command: `grep -rnE 'literal-anchor' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
`docs/spec/drift-sweep.md` (the rule's section of record and its amendment)
and `docs/spec/pipeline-observability.md` — reconciled, consistent;
`docs/spec/skill-lint-v5.md` §`literal-anchor` as a `FORBIDDEN` drift phrase
and `docs/requirements/integration/skill-lint.md`
REQ-LINT-PIPELINEOBSERVABILITY-001 — reconciled, the same pattern applied by
the linter over the shipped skill text, no second definition;
`docs/requirements/index.md` (ledger rows, Q-REQ-PO-R, §Out of Scope) —
reconciled, they cite this rule; `plugins/sdd/skills/**` and
`plugins/sdd/agents/**` — no hit (the rule lives in `plugins/sdd/tools/gc.py`,
outside the swept trees, and no skill restates it).
[Priority: must]
`[Updated: 2026-09-22]` — requirements review round 5 C1: the source-line
discipline is now stated explicitly (fence half applied, span-blanking half
not), the 69/7 observation is restated against it with the 0/0 counter-measure,
and the self-test fixture decides the discipline (backticked anchor = finding).

### REQ-GC-PIPELINEOBSERVABILITY-002: `self-matching-grep` — a counting criterion that matches its own line is a `fail`, landed with the corpus repaired
The tool must gain a rule `self-matching-grep` over the same scope and
visible-line discipline as REQ-GC-PIPELINEOBSERVABILITY-001, with this
decidable definition derived at read time and from no literal list: for a
visible line `L` of file `F` holding a `grep` invocation with a **quoted**
pattern `P` (or `-e P`) and target arguments `T`, the line is self-matching iff
`F ∈ expand(T)` — globs expanded and directories walked relative to the
corpus root, the `plugins/sdd/` prefix tried for a bare tool path — **and** `P`
compiled as a regular expression matches `L` itself. Severity **`fail`**, so
the commit gate fails through REQ-PC-MARKETPLACE-002; the rule therefore lands
**in the same commit** as the repair of every instance the live corpus holds
(fence the criterion, or add `--exclude=<own file>` to the command). **Command-line grammar (the parser's input, stated here).** Source: every
line outside a fenced block (the fence half of `visible_lines()`); the
inline-code blanking half is **not** applied by this rule, because a counting
criterion is written as inline code — each inline-code span on such a line,
and the line's remainder outside spans, is a candidate text. A candidate holds
an invocation iff it contains `grep` as a shell word; the invocation is the
text from that word to the end of the candidate or to the first unquoted `|`,
`;`, `&&`, `||` or `)`, split into words by POSIX shell rules (`shlex`); a
candidate that cannot be split (unbalanced quotes) is skipped. Options are
words beginning with `-`; `-e`, `-f`, `--include`, `--exclude` take the next
word as their argument and `--include=G` / `--exclude=G` carry it inline. `P`
:= the argument of the first `-e`, else the first non-option word after
`grep`; `P` must have been **quoted** in the candidate (`'…'` or `"…"`), else
the invocation is skipped (the unquoted form is out of scope,
RS-PIPELINEOBSERVABILITY-001 §Open Questions). `T` := every non-option word
after `P` — grep's **own file operands**. `expand(T)`: shell globs expanded
and, under `-r` / `-R`, directories walked, relative to the corpus root, then
the same with `plugins/sdd/` prefixed for a word that resolves nowhere bare;
`--exclude=G` removes the files `G` matches. An invocation with `T = ∅` — the
piped forms `sed … F | grep P`, `cat F | grep P`, `… | grep -c P` — is **out
of scope by decision** (Q-REQ-PO-AB): the rule reads grep's own operands and
never a producer upstream of a pipe, so such a line yields no finding. Observed: 4 self-matching counting greps in `docs/spec` on
2026-09-22, each inflating its own count by one; 0 false positives among the
85 invocations parsed. (see RS-PIPELINEOBSERVABILITY-001 §Q5, R9.) Touches
REQ-GC-HARNESSP2-002 (amended); leaves REQ-GC-HARNESSP2-006/-007 and
REQ-PC-MARKETPLACE-006 consistent.
**Acceptance**: `--self-test` gains a case whose fixture file holds, one per
form of the grammar: an unfenced line `grep -c 'pending-red' <its own relative
path>` (one fail); the same line inside a fence (none); the same line with a
target set that excludes the file (none); the `-e 'pending-red'` form naming
the file (one fail); the unquoted form `grep -c pending-red <its own path>`
(none — skipped); the piped form `sed -n '1,9p' <its own path> | grep -c
'pending-red'` (none — `T = ∅`); the recursive form `grep -rc 'pending-red'
<its own directory> --exclude=<its own file>` (none); the case fails when the
rule is removed in a temp copy; `--report` on this
repository at the landing commit exits `OK` with 0 `self-matching-grep`
findings, and on a scratch copy of the parent commit reports the pre-repair
instances (4 on 2026-09-22 — a reference value); `pre-commit run --all-files`
exits 0 at the landing commit.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG, 2026-09-22)** over the `self-matching-grep` operand rule — a listing grep over `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in this requirement's own text and in the index rows citing it are the statement itself and are excluded.
Command: `grep -rnE 'self-matching-grep' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
`docs/spec/drift-sweep.md` (section of record and amendment) and
`docs/spec/pipeline-observability.md` — reconciled, consistent with the
operand grammar and the piped-form exclusion (Q-REQ-PO-AB);
`docs/requirements/index.md` (ledger, Q-REQ-PO-AB, §Out of Scope) —
reconciled, citations only; `plugins/sdd/skills/**` and `plugins/sdd/agents/**`
— no hit.
[Priority: must]
`[Updated: 2026-09-22]` — the command-line grammar and one fixture per form
added at requirements review iteration 3.

### REQ-GC-PIPELINEOBSERVABILITY-003: `qimpl-malformed` — a bare Q-IMPL reference with no bare definition is malformed, not undefined
Under marker `4` the Q-IMPL reference sweep must report a **bare** reference
(no `<WS>` segment) whose counter matches **no bare definition** — the set of
bare `### Q-IMPL-` headings under `docs/spec/**`, derived fence-symmetrically
at read time (REQ-GC-HARNESSP6-004), never from a list — as a new **`fail`**
class `[qimpl-malformed]`, distinct from `[qimpl-undefined]`. A bare reference
that matches a bare definition stays well-formed (the legacy counter,
REQ-WS-009; 30 bare definitions beside 94 workstream-prefixed on 2026-09-22 —
reference values); a workstream-prefixed reference whose `<WS>` is not a
workstream directory stays a placeholder (REQ-GC-HARNESSP2-003 as amended).
The class is derived from the definition set, not from what "looks local", so
REQ-GC-HARNESSP3-001's declined scoping is not reopened (Q-REQ-PO-F). Observed:
a bare id with a three-digit counter and no definition raised a live
`qimpl-undefined` fail at the consumer-geometry plan gate instead of being
rejected as malformed; this is not a one-line fix (RS-PIPELINEOBSERVABILITY-001
§Corrections). (see §Q6 gap 7, R11, §Mechanical pin R11.) Touches
REQ-GC-HARNESSP2-002/-003 (amended); leaves REQ-GC-HARNESSP3-001,
REQ-QIMPL-HARNESSP5-001/-002 and REQ-LINT-006 consistent.
**Acceptance**: `--self-test` gains a case whose marker-`4` fixture holds one
bare definition, one bare reference to it (well-formed, no finding), one bare
reference whose counter matches no bare definition (exactly one
`[qimpl-malformed]` fail and **no** `[qimpl-undefined]` for it), and one
workstream-prefixed undefined reference (one `[qimpl-undefined]`, unchanged);
the case fails when the class is removed in a temp copy and reports
`[qimpl-undefined]` in its place; `--help` names the class; `--report` on this
repository exits `OK` with 0 `qimpl-malformed` findings.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
2026-09-22)** over the `qimpl-malformed` class and the narrowed placeholder
exclusion — a listing grep over `docs/requirements docs/spec plugins/sdd/skills
plugins/sdd/agents`; hits in this requirement's own text and in the index rows
citing it are the statement itself and are excluded.
Command: `grep -rnE 'qimpl-malformed|legacy bare counter|bare definition' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
`docs/spec/drift-sweep.md` §Q-IMPL Counting Rule "nor absent (legacy bare
counter)" — the old exclusion; reconciled: its dated in-place amendment below
it narrows the exclusion, and §`qimpl-malformed` and the narrowed placeholder
exclusion carries this requirement; the same file's rules table row 19 and
§Routing at DONE (fails the commit gate, not gate-routed) — reconciled;
`docs/spec/pipeline-observability.md` — reconciled, the convention note;
`plugins/sdd/skills/**`, `plugins/sdd/agents/**` — no hit
(`references/drift-sweep.md`'s routing table lists only gate-routed classes,
and a `fail` is caught at the commit gate, so no skill text names the class);
`docs/requirements/integration/drift-sweep.md` REQ-GC-HARNESSP2-002 and -003
(amended) — reconciled, they point here.
[Priority: must]

### REQ-GC-PIPELINEOBSERVABILITY-004: `dead-path-citation` — a cited path the tree does not hold is a `warn`, folded per file
The tool must gain a third snapshot-comparand rule, `dead-path-citation`, over
the same file scope as REQ-GC-PIPELINEOBSERVABILITY-001 and the same source
lines as REQ-GC-PIPELINEOBSERVABILITY-002 (unfenced lines, inline-code spans
read rather than blanked), with this **token grammar** stated in full: a
candidate token is the whole text of one inline-code span (backtick to
backtick) on an unfenced line; it is a **citation** iff (1) it holds no
whitespace character, (2) it holds at least one `/`, (3) it holds none of `<`,
`>`, `*`, `{`, `…`, and (4) after stripping one trailing line anchor — a colon
followed by digits — its last path component ends in one of `.md`, `.py`,
`.yaml`, `.yml`, `.json`, `.jsonl`, `.toml`, `.el`. Clause (1) is the
**backticked-command exclusion** (Q-REQ-PO-W): a span holding whitespace is a
command or a phrase, never a citation, so
`grep -c convention plugins/sdd/agents/chunk-verifier.md` is not a token even
though its last word is a live path, and the same command ending in a dead path
is not one either. A citation is **dead** iff the stripped token resolves to no
file at the corpus root **nor** under `plugins/sdd/`; a dead citation is a
finding at **`warn`** severity, folded per file, with the sha-pinned exemption
of REQ-GC-PIPELINEOBSERVABILITY-001. The path-only form is the same class as
the anchor form and `literal-anchor` cannot see it: the three `docs/spec` lines
the research names as self-matching greps also cite paths dead since the
packaging move, so the same-commit repair of REQ-GC-PIPELINEOBSERVABILITY-002
repairs two defects per line. Decision (Q-REQ-PO-I): a gc rule, not an
extension of skill-lint's retired-prefix sweep — the class is corpus-comparand,
its scope is gc's, and REQ-PC-MARKETPLACE-006 keeps rules in gc's table;
`warn` rather than `fail` because the live count was not measured by the
research. Beyond the three repaired spec lines, findings of this rule in
earlier cycles' approved text are **not repaired by this cycle** (Q-REQ-PO-R,
the same decision as REQ-GC-PIPELINEOBSERVABILITY-001's): the rule lands as a
standing `warn` floor routed `record | ignore` at DONE. (see
RS-PIPELINEOBSERVABILITY-001 §Open Questions "Q5 dead-path citations".)
Touches REQ-GC-HARNESSP2-002 (amended); leaves REQ-LINT-PACKAGING-008 and the
retired-prefix sweep untouched.
**Acceptance**: `--self-test` gains a case whose fixture holds, one per form
of the token grammar: a path cited alone and absent from the fixture tree (one
folded warn); the same path present under the fixture's `plugins/sdd/` (none);
a placeholder path holding `<id>` (none — clause 3); a sha-pinned dead path
(none — exemption); a backticked `grep -c <pattern> <path>` command whose last
word is a live path (none — clause 1) and the same command whose last word is
a dead path (none — clause 1); the dead path carrying a trailing line anchor
(one folded warn — the anchor is stripped first); the dead path inside a fence
(none); the case fails when the rule is removed in a temp copy; `--report` on
this repository at the landing commit reports 0 `dead-path-citation` findings
on the three repaired spec lines and counts the rest at run time (never
pinned); `--help` lists the rule at `warn`.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG, 2026-09-22)** over the `dead-path-citation` source-line discipline — a listing grep over `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`; hits in this requirement's own text and in the index rows citing it are the statement itself and are excluded.
Command: `grep -rnE 'dead-path-citation' docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`.
`docs/spec/drift-sweep.md` (section of record and amendment) and
`docs/spec/pipeline-observability.md` — reconciled, consistent with the token
grammar (Q-REQ-PO-W); `docs/requirements/index.md` (ledger, Q-REQ-PO-W, -R) —
reconciled, citations only; `plugins/sdd/skills/**` and `plugins/sdd/agents/**`
— no hit.
[Priority: should]
`[Updated: 2026-09-22]` — the token grammar (with the Q-REQ-PO-W whitespace
clause folded in as its first clause) and one fixture per form stated at
requirements review iteration 3; the earlier amendment note is subsumed.
