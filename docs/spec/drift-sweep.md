---
status: Approved
last_updated: 2026-09-22
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
  - REQ-GC-HARNESSP6-001
  - REQ-GC-HARNESSP6-002
  - REQ-GC-HARNESSP6-003
  - REQ-GC-HARNESSP6-004
  - REQ-PKG-CONSUMERGEOMETRY-001
  - REQ-PKG-CONSUMERGEOMETRY-003
  - REQ-PKG-CONSUMERGEOMETRY-004
  - REQ-PKG-CONSUMERGEOMETRY-005
  - REQ-GC-PIPELINEOBSERVABILITY-001
  - REQ-GC-PIPELINEOBSERVABILITY-002
  - REQ-GC-PIPELINEOBSERVABILITY-003
  - REQ-GC-PIPELINEOBSERVABILITY-004
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
| 7 | staleness chain research → requirements → specs → plan → verification by `last_updated`, per workstream via plan `traces to` → spec `requires:` → category files. Two sub-kinds: **plan-level** (a `docs/ws/<id>/plan.md` older than a traced spec or a traced requirement category file) and **shared-spec** (a `docs/spec/*.md` older than a category file it `requires:` ids from), the latter emitted **folded** — one finding per `(spec, category file)` pair naming every triggering id | gc | `stale-chain` | plan-level **warn**; shared-spec **info** | every skill's Phase Detection; `ws-staleness.md` (never a traceability file); §Closed-Workstream Skip; §Shared-Spec Staleness |
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

**Rows 16–19, added to the Sweep Table** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-GC-PIPELINEOBSERVABILITY-001, -002, -004; REQ-GC-HARNESSP2-002 as amended; Q-REQ-PO-AB, -R, -W; the record of why is §Pipeline-Observability Amendment).

| # | Sweep | Class | Rule id | Severity | Scope |
|---|---|---|---|---|---|
| 16 | live line-number citation in binding text (snapshot comparand, anchor form) | gc | `literal-anchor` | **warn**, folded per file | `docs/spec/**/*.md`, `docs/requirements/**/*.md`, unfenced lines |
| 17 | counting grep whose quoted pattern matches its own line (snapshot comparand, self-inflating form) | gc | `self-matching-grep` | **fail** | same |
| 18 | backtick-cited path the tree does not hold (snapshot comparand, path-only form) | gc | `dead-path-citation` | **warn**, folded per file | same |
| 19 | bare `Q-IMPL` reference with no bare definition (marker `4`) | gc | `qimpl-malformed` | **fail** | the reference scope of §Q-IMPL Counting Rule |

**Source-line discipline of rows 16–18, stated explicitly.** Source lines are
every line outside a fenced block — the **fence half** of `visible_lines()`
(REQ-GC-HARNESSP6-004) — read **whole**; the inline-code and quoted-span
**blanking half is NOT applied** by these three rules, because a line-number
citation, a counting criterion and a cited path are each almost always written
as inline code, so a span-blanked source has nothing to match. Measured on this
tree on 2026-09-22 with the `literal-anchor` pattern and the sha exemption
applied under both disciplines: fence-only → 69 anchors in 7 files;
fence-plus-span-blanking → 0 anchors in 0 files — the rule as previously worded
could never fire, which is the defect this clause closes (requirements review
round 5 C1). `docs/research/**` and `docs/ws/**` are **out of scope by
decision** for 16–18: research spikes and execution records are dated snapshots
by contract, where the line number *is* the evidence being recorded. None of
the four joins `--fix`.

**`literal-anchor`** (REQ-GC-PIPELINEOBSERVABILITY-001). An occurrence of
`[\w./-]+\.md:\d+` on a source line is a finding, **folded to one line per
file** carrying the count, **exempting the sha-pinned form** — a 7-to-40
hex-digit token within the 40 characters before the anchor, a frozen citation
by construction. Standing `warn` floor: the anchors in earlier cycles' approved
text (69 in 7 files on 2026-09-22, a reference value, never a pin) are **not
repaired by this cycle** (Q-REQ-PO-R) — rewriting a shared approved body is a
human PR decision, and every one of them names a comparand its own commit
froze; the DONE `GC:` line routes the folded lines `record | ignore`, and a
repair, if wanted, is a later cycle's task bounded to those files.

**`self-matching-grep`** (REQ-GC-PIPELINEOBSERVABILITY-002). Decidable at read
time from no literal list. **Command-line grammar** (the parser's input): each
inline-code span on a source line, and the line's remainder outside spans, is
a candidate text. A candidate holds an invocation iff it contains `grep` as a
shell word; the invocation is the text from that word to the end of the
candidate or to the first unquoted `|`, `;`, `&&`, `||` or `)`, split into
words by POSIX shell rules (`shlex`); a candidate that cannot be split
(unbalanced quotes) is skipped. Options are words beginning with `-`; `-e`,
`-f`, `--include`, `--exclude` take the next word as their argument and
`--include=G` / `--exclude=G` carry it inline. `P` := the argument of the first
`-e`, else the first non-option word after `grep`; `P` must have been
**quoted** in the candidate (`'…'` or `"…"`), else the invocation is skipped
(the unquoted form is out of scope). `T` := every non-option word after `P` —
grep's **own file operands**. `expand(T)`: shell globs expanded and, under
`-r` / `-R`, directories walked, relative to the corpus root, then the same
with `plugins/sdd/` prefixed for a word that resolves nowhere bare;
`--exclude=G` removes the files `G` matches. The line `L` of file `F` is
self-matching iff `F ∈ expand(T)` **and** `P` compiled as a regular expression
matches `L` itself. An invocation with `T = ∅` — the piped forms `sed … F |
grep P`, `cat F | grep P`, `… | grep -c P` — is **out of scope by decision**
(Q-REQ-PO-AB): the rule reads grep's own operands and never a producer
upstream of a pipe, so such a line yields no finding. Severity **`fail`**, so
the commit gate fails through REQ-PC-MARKETPLACE-002; the rule therefore lands
**in the same commit** as the repair of every instance the live corpus holds
(fence the criterion, or add `--exclude=<own file>`). Observed: 4
self-matching counting greps in `docs/spec` on 2026-09-22 (a reference value).

**`dead-path-citation`** (REQ-GC-PIPELINEOBSERVABILITY-004, `should`).
**Token grammar**, stated in full: a candidate token is the whole text of one
inline-code span (backtick to backtick) on a source line; it is a **citation**
iff (1) it holds no whitespace character, (2) it holds at least one `/`, (3)
it holds none of `<`, `>`, `*`, `{`, `…`, and (4) after stripping one trailing
line anchor — a colon followed by digits — its last path component ends in one
of `.md`, `.py`, `.yaml`, `.yml`, `.json`, `.jsonl`, `.toml`, `.el`. Clause (1)
is the **backticked-command exclusion** (Q-REQ-PO-W): a span holding whitespace
is a command or a phrase, never a citation, so a backticked `grep` command
whose last word is a path is not a token whether that path is live or dead. A
citation is **dead** iff the stripped token resolves to no file at the corpus
root **nor** under `plugins/sdd/`; a dead citation is a finding at **`warn`**,
folded per file, with the sha-pinned exemption of `literal-anchor`. A third gc
rule rather than an extension of skill-lint's retired-prefix sweep
(Q-REQ-PO-I): the class is corpus-comparand and its scope is gc's; `warn`
because the live count was not measured by the research. Beyond the three
spec lines the same-commit repair of `self-matching-grep` fixes (each also
cites a path dead since the packaging move), findings in earlier cycles'
approved text are not repaired by this cycle (Q-REQ-PO-R).

### Closed-Workstream Skip (REQ-GC-HARNESSP6-001)

[Added 2026-09-20, harness-p6 — REQ-GC-HARNESSP6-001]

`stale-chain`'s **plan-level** sub-kind is skipped entirely for a **closed**
workstream. A workstream is closed when `docs/ws/<id>/verification.md` exists
and its frontmatter `status:` is exactly `pass`. Both plan-level sub-kinds
(`plan older than a traced spec`, `plan older than a traced requirement category
file`) are skipped together — a half-skip would leave the same false positive in
a second shape.

Rationale: a closed workstream's plan *should* be older than specs and category
files that later cycles amended; the finding is structurally unfixable without
back-dating an artifact, and its count grows monotonically with every subsequent
cycle. Measured at the harness-p6 branch point (`ac0fb43`) the rule emitted 19 such lines
(13 on `harness-p3`'s plan, 6 on `harness-p4`'s).

Scope of the change, stated so an implementer does not widen it: this is a
**scoping predicate on an existing rule** — no new rule id, no severity change,
no allowlist, no file exempted by name. A workstream with no `verification.md`,
or one whose `status:` is any value other than `pass` (including `fail` and
`pending-red`), is **open** and is swept exactly as before, so real in-flight
staleness still surfaces. The skip is evaluated per workstream, never per file:
under marker `3` there is no `docs/ws/`, no sibling `verification.md` to read,
and the predicate is never consulted — marker-3 behaviour is unchanged.

### Shared-Spec Staleness: Fold and Severity (REQ-GC-HARNESSP6-002, REQ-GC-HARNESSP6-003)

[Added 2026-09-20, harness-p6 — REQ-GC-HARNESSP6-002, REQ-GC-HARNESSP6-003]

**The fold.** The spec-versus-requirement comparison emits **one** finding per
`(downstream spec, upstream category file)` pair, not one per
`(spec, requirement id)` pair. The message names the requirement ids that
triggered it, so no information is lost:

```
INFO  [stale-chain] docs/spec/telemetry.md:1 — spec last_updated 2026-09-18 is
      older than docs/requirements/functional/telemetry.md 2026-09-20
      (ids: REQ-TELEM-001, REQ-TELEM-002, … 39 ids)
      fix: review the spec against those requirements; bump last_updated via
           sdd-specs if it actually needs a change
```

The fold is a **presentation** change and drops no comparison: every
`(spec, id)` pair is still evaluated, and a pair that triggers still reaches the
operator through its pair's id list. Its false-negative cost is therefore
provably zero. It is preferred over the alternatives Q1 weighed — comparing only
against `requires:` ids (already the behaviour), demoting without folding
(leaves 44 lines at that branch point), and date-bumping to silence (rejected: it makes the signal
meaningless). At the harness-p6 branch point (`ac0fb43`) 44 lines fanned out from exactly
three pairs — **a dated measurement, not an invariant: the pair set grows
whenever any workstream re-dates a category file, and stood at 6 pairs by the
specs stage** — `docs/spec/telemetry.md` ← `functional/telemetry.md` (39),
`docs/spec/telemetry.md` ← `integration/skill-lint.md` (3),
`docs/spec/adversarial-verify.md` ← `integration/skill-lint.md` (2).

**The severity.** The folded finding is emitted at **`info`**, not `warn`. Under
the v4 shared corpus a category file is re-dated whenever *any* workstream
appends a requirement to it, so a shared spec lagging that date is the expected
steady state rather than a defect; carrying the class at `warn` is what made the
warn class unusable as a drift signal. The finding is still printed and still
counted, so the loss is one of **salience, not visibility**, and the severity is
a one-line reversal if the class is ever observed hiding real staleness. Only
the spec-versus-requirement sub-class moves — plan-level `stale-chain` findings
keep `warn`.

**The routing moves with the severity.** §Routing at DONE lists only the
**plan-level** sub-class under `record | ignore`; the folded shared-spec class
is informational and routes nowhere. This is binding, not tidiness: `record`
appends to `verification.md` §Next Steps, which REQ-REQ-HARNESSP6-001 forbids
from holding a carried item, so leaving the shared-spec class decision-routed
would set two requirements of the same cycle against each other at the DONE
gate.

**Ordering.** The two changes are independent in code but not in verification:
the "zero `[stale-chain]` warnings on this repository" condition cannot hold
until the closed-workstream skip of REQ-GC-HARNESSP6-001 has also landed, since
the 19 plan-level lines are `warn` and stay `warn`. A plan must not schedule the
severity check before that rule.

**Traced-by-active-plan stale-chain pairs are `warn`** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-GC-HARNESSP6-003 as amended; the record of why is §Pipeline-Observability Amendment).

§Shared-Spec Staleness' `info` gains one narrow exception: with `--workstream
<id>` given, a folded `(spec, category file)` pair whose spec is **traced by
the active workstream's plan** (`docs/ws/<id>/plan.md` `traces to`, the live
plan-walk of `ws-staleness.md`) is emitted at **`warn`**; an untraced pair
stays `info`. The steady-state rationale holds for untraced pairs; a spec this
cycle's own plan traces and this cycle's requirements re-dated is the cycle's
own stale chain, which consumer-geometry closed by argument rather than by a
gate. gc still never blocks a gate (REQ-GC-HARNESSP2-006): the `warn` routes
`record | ignore` at DONE, where §Routing at DONE's `stale-chain` entry now
reads "plan-level sub-kind, and the **traced** shared-spec sub-kind"; the
untraced shared-spec sub-class stays unrouted. The "0 `[stale-chain]`
warnings" clause of REQ-GC-HARNESSP6-003 is re-read as "0 warnings on
untraced pairs".

### Q-IMPL Counting Rule (REQ-GC-HARNESSP2-003)

Pinned so the numbers are reproducible (also in the tool's docstring with the
three reference commands from RS-HARNESSP2-001 Q4):

- **Definition**: a line matching `^### Q-IMPL-[A-Z0-9-]+` under `docs/spec/**`
  that lies **outside** a fenced code block — collected through the same
  `visible_lines()` filter the reference side uses
  (REQ-GC-HARNESSP6-004, added 2026-09-20). A heading inside a fence defines
  nothing, exactly as a reference inside a fence references nothing.
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
**Fence symmetry and the countability obligation (REQ-GC-HARNESSP6-004).**
Before this change references were filtered and definitions were not, so a
deviation-entry heading inside a fence registered as a real definition that
nothing could ever reference. Symmetry creates an **obligation on authors, not
an allowlist**: an id used inside a fenced format illustration must be either
(a) an id that a real, unfenced `### Q-IMPL-…` entry defines elsewhere in the
corpus — the present convention, which both illustration ids in
`deviation-protocol.md` already satisfy — or (b) one of the id-format
placeholders the tool already excludes. No marker, info-string language tag or
whitelist is introduced, so `CLAUDE.md` §Quality Checks' "there is no allowlist"
statement stays true, and its documented "wrap it in a fenced code block" escape
becomes symmetric: a fence can no longer accidentally *define* a foreign id
either. The rule is stated in the module docstring and in `--help` alongside the
reference commands.

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

**`qimpl-malformed` and the narrowed placeholder exclusion** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-GC-PIPELINEOBSERVABILITY-003; REQ-GC-HARNESSP2-003 as amended; the record of why is §Pipeline-Observability Amendment).

Under marker `4`, §Q-IMPL Counting Rule's exclusion "or a legacy bare counter"
is **narrowed**: a bare id (no `<WS>` segment) is well-formed only when a
**bare definition** with that counter exists — the set of bare `### Q-IMPL-`
headings under `docs/spec/**`, collected fence-symmetrically at read time. A
bare reference matching no bare definition is a new **`fail`** class
`[qimpl-malformed]`, distinct from `[qimpl-undefined]` and never skipped. A
workstream-prefixed reference whose `<WS>` is not a workstream directory stays
a placeholder; the fence/backtick skip and the `docs/research/**` exclusion are
unchanged. Membership is decided by the definition set, not by the id's shape,
so REQ-GC-HARNESSP3-001's declined "looks local" scoping is not reopened
(Q-REQ-PO-F). Reference values on 2026-09-22: 30 bare definitions beside 94
workstream-prefixed.

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
| needs a decision | `qimpl-broken-ref`, `stale-chain` (**plan-level sub-kind only**, REQ-GC-HARNESSP6-003), `traceability-aggregate` (when the per-ws inputs themselves look wrong), `spec-approval` | `record \| ignore`; on `record` the orchestrator appends `- gc <rule>: <file:line> — <fix>` under the completed cycle's `verification.md` §Next Steps (marker `4`: `docs/ws/<id>/verification.md`; the `## Next Steps` section added to the `sdd-verify` Step 6 template — `adversarial-verify.md` §Skill and Lint Changes, verify row) — read by the next cycle's DISCUSS |
| out of scope | sweep 15 | note only |

**Dates are never auto-fixed.** REQ-GC-HARNESSP2-006 lists a stale
`last_updated` among the mechanical findings, while REQ-GC-HARNESSP2-007 states
that `--fix` never touches `last_updated`; this spec follows -007 — plan-level
`stale-chain` routes to `record | ignore` and the owning skill updates the date
(editing it mechanically would mask the staleness it signals).

**The shared-spec sub-class is not routed.** Its findings are `info`, are
displayed and counted at DONE, and are offered no option — not `record`, not
`ignore`, not `--fix`. The class appears in no row of the table above
(REQ-GC-HARNESSP6-003).

gc never creates or modifies a plan task, never writes a file outside a
`--fix` rule's whitelist, never creates `docs/gc/` or an issues file
(REQ-HARN-027, REQ-ORCH-004); the `record` append is the orchestrator's
bookkeeping in an existing section, outside any observed window.

**Routing at DONE — rows added** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-GC-PIPELINEOBSERVABILITY-001..-004; REQ-GC-HARNESSP6-003 as amended; the record of why is §Pipeline-Observability Amendment).

| Finding class | Rules | Gate action |
|---|---|---|
| needs a decision (added) | `literal-anchor`, `dead-path-citation`, `stale-chain` traced shared-spec sub-kind | `record \| ignore` — standing `warn` floors; `record` appends under `verification.md` §Next Steps as the existing row does |
| fails the commit gate (added) | `self-matching-grep`, `qimpl-malformed` | not gate-routed: `fail` is caught by the pre-commit sweep before DONE (REQ-PC-MARKETPLACE-002) |

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
| `skills/sdd-verify/SKILL.md` | Step 6 template gains a `## Next Steps` section after `## Recommendation`, documented as the slot for `- gc <rule>: …` and deferral lines — the change is carried **once**, in `adversarial-verify.md` §Skill and Lint Changes (verify row); today the template ends at `## Recommendation` and only `docs/ws/default/verification.md` carries the section by hand |
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
- `test_stale_chain_skips_closed_workstream`: a fixture workstream whose
  `verification.md` is `status: pass` raises **no** plan-level `[stale-chain]`
  finding of either sub-kind; the same plan under a workstream whose
  `verification.md` is `status: fail`, is `status: pending-red`, or is absent
  raises them both as before (REQ-GC-HARNESSP6-001).
- `test_shared_spec_staleness_folds`: a fixture spec requiring three ids from
  one stale category file yields exactly **one** `[stale-chain]` finding whose
  message names all three ids; two stale category files for the same spec yield
  two findings (REQ-GC-HARNESSP6-002).
- `test_shared_spec_staleness_severity`: the folded finding is emitted at `info`
  and a plan-level finding on an open workstream is emitted at `warn`
  (REQ-GC-HARNESSP6-003).
- `test_qimpl_definition_is_fence_symmetric`: a `### Q-IMPL-…` heading inside a
  fenced block contributes **no** definition; a reference to an
  otherwise-undefined id that occurs only inside that fence raises no
  `qimpl-undefined`; an unfenced heading still defines, and a genuinely
  undefined unfenced reference still fails (REQ-GC-HARNESSP6-004).

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
- [ ] `stale-chain` skips both plan-level sub-kinds for a workstream whose sibling `verification.md` is `status: pass`, and sweeps an absent / `fail` / `pending-red` workstream unchanged; no new rule id, no allowlist; marker-3 unaffected (REQ-GC-HARNESSP6-001)
- [ ] `python3 tools/sdd-gc.py --report` on this repository reports zero `[stale-chain]` findings located in `docs/ws/harness-p3/plan.md` or `docs/ws/harness-p4/plan.md` (REQ-GC-HARNESSP6-001)
- [ ] The spec-versus-requirement comparison emits one finding per `(spec, category file)` pair, naming every triggering requirement id in the message; on this repository the count of such findings **equals the count of distinct `(spec, category file)` pairs those findings name** — both sides derived from the same `--report` run, neither pinned as a literal (REQ-GC-HARNESSP6-002)
- [ ] The folded finding is `info`; plan-level findings stay `warn`; §Sweep Table row 7 and §Routing at DONE both state the split, and the shared-spec sub-class is offered no `record` option (REQ-GC-HARNESSP6-003)
- [ ] `python3 tools/sdd-gc.py --report` on this repository exits `OK` with **0** `[stale-chain]` **warnings**, every remaining spec-versus-requirement `[stale-chain]` line emitted at `info`; the number of `info` lines is a property of the corpus at run time and is deliberately not pinned (REQ-GC-HARNESSP6-001 + REQ-GC-HARNESSP6-003 together)
- [ ] Q-IMPL definitions are collected through the same fence filter as references; the countability rule is an authoring obligation, not an allowlist, and is stated in the module docstring and `--help`; `--report` reports the same `qimpl-undefined` and `qimpl-broken-ref` counts as before the change, both 0 (REQ-GC-HARNESSP6-004)
- [ ] Row parser splits on unescaped pipes only (`\|` literal, re-emitted unchanged); a wrong cell count raises one `[traceability-rowdrop]` **fail** naming `<file>:<line>` instead of dropping the row; `traceability-rowdrop` is not in `FIXABLE`; `python3 tools/sdd-gc.py --report` on this repository raises none and `grep -c '^| REQ-ARB-HARNESSP4-003 \|^| REQ-CYCID-HARNESSP4-001 ' docs/requirements/traceability.md` prints `2` (both recovered harness-p4 rows present — a row-presence assertion, not a corpus-wide escape count) (REQ-GC-HARNESSP5-001)

**Pipeline-observability (2026-09-22, drift sweep)**

- [ ] `python3 plugins/sdd/tools/gc.py --self-test` exits 0 with a
  `literal-anchor` case whose fixture holds one file with three anchors — one
  **inside backticks** on an unfenced line (a finding), one inside a fenced
  block (no finding) and one sha-pinned on an unfenced line (no finding) — and
  reports exactly one folded `literal-anchor` warn naming that file with count
  **1**; the case fails when the rule is removed in a temp copy, and fails
  with count 0 when the span-blanking half is applied in a temp copy — the
  source-line discipline is what the case decides
  (REQ-GC-PIPELINEOBSERVABILITY-001).
- [ ] `--help` lists `literal-anchor` and `dead-path-citation` in the gc class
  at `warn`, `self-matching-grep` and `qimpl-malformed` at `fail`; a grep of
  the `FIXABLE` list in `plugins/sdd/tools/gc.py` for any of the four names
  returns nothing (REQ-GC-PIPELINEOBSERVABILITY-001..-004, REQ-GC-HARNESSP2-002
  as amended).
- [ ] `python3 plugins/sdd/tools/gc.py --report` on this repository exits `OK`
  with the `literal-anchor` and `dead-path-citation` folded lines counted at
  run time (7 files for `literal-anchor` on 2026-09-22 — a reference value,
  never a pin) and the exit status unaffected by them
  (REQ-GC-PIPELINEOBSERVABILITY-001, -004).
- [ ] `--self-test` names a `self-matching-grep` case whose fixture file holds,
  one per form of the command-line grammar: an unfenced line `grep -c
  'pending-red' <its own relative path>` (one fail); the same line inside a
  fence (none); the same line with a target set that excludes the file (none);
  the `-e 'pending-red'` form naming the file (one fail); the unquoted form
  `grep -c pending-red <its own path>` (none — skipped); the piped form `sed
  -n '1,9p' <its own path> | grep -c 'pending-red'` (none — `T = ∅`); the
  recursive form `grep -rc 'pending-red' <its own directory> --exclude=<its
  own file>` (none); the case fails when the rule is removed in a temp copy
  (REQ-GC-PIPELINEOBSERVABILITY-002).
- [ ] `--report` on this repository at the landing commit exits `OK` with 0
  `self-matching-grep` findings; on a scratch copy of the landing commit's
  parent it reports the pre-repair instances (4 on 2026-09-22 — a reference
  value); `pre-commit run --all-files` exits 0 at the landing commit
  (REQ-GC-PIPELINEOBSERVABILITY-002).
- [ ] `--self-test` names a `qimpl-malformed` case over a marker-`4` fixture:
  one bare definition, one bare reference to it (no finding), one bare
  reference matching no bare definition (exactly one `[qimpl-malformed]` and
  no `[qimpl-undefined]` for it), one workstream-prefixed undefined reference
  (one `[qimpl-undefined]`); the case fails when the class is removed in a temp
  copy and reports `[qimpl-undefined]` in its place; `--report` on this
  repository exits `OK` with 0 `qimpl-malformed` findings
  (REQ-GC-PIPELINEOBSERVABILITY-003, REQ-GC-HARNESSP2-003 as amended).
- [ ] `--self-test` names a `dead-path-citation` case whose fixture holds, one
  per form of the token grammar: a path cited alone and absent from the
  fixture tree (one folded warn); the same path present under the fixture's
  `plugins/sdd/` (none); a placeholder path holding `<id>` (none — clause 3);
  a sha-pinned dead path (none — exemption); a backticked `grep -c <pattern>
  <path>` command whose last word is a live path (none — clause 1) and the
  same command whose last word is a dead path (none — clause 1); the dead path
  carrying a trailing line anchor (one folded warn — the anchor is stripped
  first); the dead path inside a fence (none); the case fails when the rule is
  removed in a temp copy; `--report` at the landing commit reports 0
  `dead-path-citation` findings on the three repaired spec lines
  (REQ-GC-PIPELINEOBSERVABILITY-004).
- [ ] `--self-test` names a traced-stale-chain case: with `--workstream` set to
  the fixture's active workstream, a folded pair traced by that plan is `warn`
  and an untraced pair in the same fixture is `info`; the case fails when the
  exception is removed in a temp copy; the §Routing at DONE table's
  `needs a decision` row names the traced shared-spec sub-kind of
  `stale-chain` beside `literal-anchor` and `dead-path-citation` — decided by
  reading that row (REQ-GC-HARNESSP6-003 as amended).

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
**Decision**: Upstream `last_updated` must be strictly greater than downstream to flag; equal dates are never stale; verification `date:` is accepted as an alias; missing dates are skipped; a `pending-red` verification is rendered as "verification exists, not passed" but yields no finding when newer than its plan (pass status is verify's job).
**Rationale**: Avoids same-day false positives and keeps staleness separate from verdict.
**Date**: 2026-09-18 (Chunk 5)

### Q-IMPL-HARNESSP2-062: `trace-empty` scans per-workstream files only and never reads Verified
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 11
**Decision**: Under marker 4 the aggregate is derived, so only `docs/ws/*/traceability.md` rows are scanned; amendment rows (Spec differs from the legacy row for the same id — see `telemetry.md` §XSPEC amendment-row rule) are skipped entirely; the Verified column is verify Step 3b's and is never checked.
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

### Q-IMPL-HARNESSP5-001: the expected cell count is the table header's, not a fixed 6
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Row-Drop Safety
**Decision**:

Rule 2 says a row "does not yield the expected cell count" without fixing that
count. `trace_rows()` takes it from the **table's own header row** (the
`| Requirement …` line, defaulting to 6 when no header precedes the rows), so
the pre-v4 five-column table keeps its existing normalisation (a 5-cell row
under a 5-column header gains the empty `Workstream` cell) while a 5-cell row
under the canonical six-column header is the `[traceability-rowdrop]` fail the
acceptance asks for. A hard-coded 6 would have flagged every legacy
five-column table as a row drop, which §Row-Drop Safety's "no existing rule,
severity or counting rule changes" forbids.
**Date**: 2026-09-20 (implement stage, Chunk 4 task 5)

### Q-IMPL-PIPELINEOBSERVABILITY-007: the shared-spec stale-chain walk covers every plan; `--workstream` scopes only the plan-level sub-kinds
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Shared-Spec Staleness: Fold and Severity
**Decision**: `sweep_stale()` walks every `docs/ws/*/plan.md` for the folded shared-spec sub-kind and applies `--workstream <id>` only to the plan-level sub-kinds (plan-vs-spec, plan-vs-category, verification-vs-plan) and to the set of specs marked "traced by the active plan". A traced pair is `warn` with its own fix text (routed `record | ignore`); an untraced pair stays `info`.
**Rationale**: The amended section asks that "an untraced pair stays `info`" under `--workstream`, which is decidable only if the scoped run still sees pairs the active plan does not trace; before this change a scoped run walked one plan and could never emit an untraced pair. Unscoped output is unchanged (every plan was already walked), and a scoped run's plan-level findings are unchanged (the other plans' plan-level sub-kinds stay skipped, as `--workstream` promised).
**Date**: 2026-09-22 (implement stage, Chunk 3 task 5)

### Q-IMPL-PIPELINEOBSERVABILITY-008: the regenerated aggregate's `last_updated` is derived from the per-ws inputs
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Sweep Table row 12, §`--fix` Whitelist
**Decision**: `regenerate_aggregate()` sets the aggregate's frontmatter `last_updated` to the newest `last_updated` among the `docs/ws/*/traceability.md` files it regenerates from (added when the frontmatter lacks the key); the preamble prose is still kept verbatim. This narrows `Q-IMPL-HARNESSP2-065` — the aggregate's own date is a derived value, not an owned artifact's date — while "`--fix` never touches `last_updated`" keeps its meaning for every owned artifact: no per-ws file, plan, spec or requirement date is written. The live aggregate under `docs/requirements/` is not regenerated by the implement leaf (`ws-traceability.md` §Aggregate Regeneration Ownership); a `[traceability-aggregate]` warn on the live tree until the orchestrator's stage-close regeneration is the designed handshake.
**Rationale**: The aggregate read `2026-09-19` after a 2026-09-22 regeneration (plan §Carried notes, note 1); a derived file whose date lags its inputs misreports the staleness chain it is meant to make visible.
**Date**: 2026-09-22 (implement stage, Chunk 3 task 7)

### Q-IMPL-PIPELINEOBSERVABILITY-009: `self-matching-grep` finds 40 live instances under `docs/requirements/**` that no implement row may repair
**Tier**: 3 (contract change — escalated, not decided here)
**Spec reference**: §Sweep Table row 17 (scope "same" as row 16: `docs/spec/**` and `docs/requirements/**`)
**Decision**: The rule landed at the specified scope and severity with its five `docs/spec` instances repaired in the landing change (the four observed on 2026-09-22 plus the dated `grep -l` count over `docs/spec/*.md` in `pipeline-observability.md`, written at the specs stage after the measurement): each criterion is fenced (meaning preserved) or given `--exclude=<own file>` where a downstream pipe already dropped the file, and the dead `skills/…` / `tools/sdd-*` paths on those lines are corrected. On the same run the rule reports 40 further instances in 14 `docs/requirements/**` files — every one a requirements-stage `Command:` sweep block — a `grep -rn` listing whose quoted pattern runs over `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents`, the first operand holding the block's own file. The research measured `docs/spec` only ("4 … in `docs/spec`"), and the plan's replan trigger fires: the repair would touch more than the observed live instances, and `docs/requirements/**` is in no implement write scope (plan §Conventions, Q-PLAN-PO-E). The implement leaf therefore stops: the rule is not narrowed to `docs/spec` (the spec says "same"), the requirements lines are not edited, and the tree's `--report` fails on exactly those 40 lines until the operator either routes a requirements-stage repair (fence each `Command:` line or add `--exclude=<own file>`) or narrows row 17's scope through `sdd:specs`.
**Impact**: `pre-commit`'s fast sweep fails on the current tree by design of the rule; Chunk 3 tasks 2 and 8 stay open until the decision (checkpoint under the plan's Chunk 3 task 2).
**Date**: 2026-09-22 (implement stage, Chunk 3 task 2)
**Resolution (2026-09-22, implement stage, Chunk 3 redo 1)**: Routed as a requirements-stage repair, not a scope change — `sdd:requirements` amended clause (e) of the `Command:` sweep block to require `--exclude=<own basename>` and rewrote the 40 lines in the 14 `docs/requirements/**` files (Q-REQ-PO-AM, index 27.6). Row 17 keeps its scope ("same" as row 16) and its `fail` severity; `gc.py` is unchanged by the resolution. Witnessed: `--report` on the tree exits `OK` with 0 `[self-matching-grep]` findings, and a detached worktree of the parent commit `9a1235e` reports the 45 pre-repair instances (5 `docs/spec`, 40 `docs/requirements`) under the same rule. Chunk 3 tasks 2 and 8 are closed; the tier-3 escalation is discharged.

## Consumer-Geometry Amendment (2026-09-21, REQ-PKG-CONSUMERGEOMETRY-003, -004, -005)

**Source line numbers cited in this section identify content, not positions.**
This amendment cites `gc.py:175`, `:403`, `:507-516`, `:520-537` and
`:1825-1835`, and `skill-lint.py:516-523` — **all six are source lines the
implement stage itself moves**, since every one sits in or beside the code this
delta edits. Each is named alongside the symbol it belongs to (`AGG_FIX`,
`Gc.__init__`, `lint_command()`, `sweep_lint()`, the argparse block,
`Linter.__init__`), and **the symbol is what identifies the site**; the numbers
are a reading aid measured before any change, and no criterion below is stated
against one. The four sibling amendments carry the same note for their own
citations.

The sweep's own surface changes in three places under the `consumer-geometry`
delta. The design and the falsifying constructions live in
`two-root-linter.md` §Consumer-Geometry Amendment; this section states what
changes in **this** tool and pins the two things only this spec knows.

### 1. How a suite root enters `gc.py` — the surface, decided here

REQ-PKG-CONSUMERGEOMETRY-003 delegates the surface's **shape** to this stage ("a
CLI flag on both tools, a `gc.py` pass-through, or a documented second
positional"). `gc.py` today exposes `--report`, `--fast`, `--workstream`,
`--fix`, `--root` and `--self-test` (`gc.py:1825-1835`), and `Gc.__init__`
(`gc.py:403`) takes `root`, `workstream`, `fast` and `lint_suite_rules` — there
is **no** parameter and **no** flag by which an explicit suite root could enter.
Without one, neither half of REQ-PKG-CONSUMERGEOMETRY-003 acceptance 3 is
constructible. **Decision — the surface mirrors the linter's, in both halves:**

```
gc.py [--report] [--fast] [--workstream ID] [--fix RULE] [--root PATH]
      [--suite-root PATH] [--self-test]
  --suite-root PATH : suite root forwarded to the delegated skill lint
                      (default: none passed — the linter derives its own)

Gc(root, workstream=None, fast=False, lint_suite_rules=True, suite_root=None)
  suite_root : absolute, or None; stored on the instance and read by
               lint_command() on both of its return paths
```

Three properties are load-bearing and are stated rather than implied:

- **The flag and the constructor parameter are the same value**, the flag
  resolving its argument to an absolute path and handing it to the constructor.
  No third entry point — no environment variable, no positional — matching §2 of
  `two-root-linter.md` ("no other root-resolution mechanism is introduced").
- **The default is "pass nothing", not "pass a guess".** When `--suite-root` is
  omitted, `lint_command()` builds exactly the vector and shim it builds today
  plus nothing, and the linter's own tier-2 derivation (`two-root-linter.md`
  §CG-3) answers. A `gc.py`-side default would be a second derivation, which
  `two-root-linter.md` §CG-1 rejects.
- **`gc.py --help` names it.** That is the discoverability half; removing the
  flag from the parser makes the help assertion red, exactly as the linter's does.

`two-root-linter.md` §CG-2 carries the linter-side half of the same surface and
cross-references this section for the sweep side.

### 2. `lint_command()` passes that suite root through — on both branches

`lint_command()` has two return paths and both carry the suite root when one is
supplied to the sweep (i.e. when `self.suite_root` is not `None`; when it is
`None` both branches are byte-identical to today's). **That byte-identity is
about the constructed vector and shim *text*, never about the geometry the run
then resolves**: with no suite root passed, the linter's constructor answers with
tier 2 or tier 3 (`two-root-linter.md` §CG-3 pins the resolution **inside
`Linter.__init__`**, which is the only reason the shim — which never enters
`main()` — inherits the derivation at all). Reading the byte-identity pin as
"the shim stays on tier 3" would invert §CG-1 and is the misreading this sentence
exists to block:

- **(i) the `lint_suite_rules` argv branch**, today
  `[executable, str(lint), str(self.root)]` — the constructed vector gains the
  suite-root argument. Asserted **on the vector**, not on the subprocess result.
- **(ii) the `suite_rules=False` `-c` shim branch**, which today builds
  `Linter(Path(sys.argv[2]), suite_rules=False)` with no suite-root parameter
  anywhere — the shim passes the same suite root to that constructor. Asserted by
  parsing the shim text, or by running the shim against a fixture and reading back
  `suite_contained()`.

Q-IMPL-HARNESSP2-050 records that the fixture lint delegation uses this shim;
that record is unchanged in substance — the shim keeps `suite_rules=False`, and
only gains the suite-root parameter. Reverting branch (i) is row 4 of
REQ-PKG-CONSUMERGEOMETRY-001's enumerated comparand set and is therefore
demonstrated by running the mutation. Fixing branch (i) alone leaves branch (ii)
permanently degraded with nothing able to see it, which is why the criterion
covers both (REQ-PKG-CONSUMERGEOMETRY-003 acceptance 3).

The sweep **derives** no suite root of its own. The derivation lives in
`skill-lint.py` (`two-root-linter.md` §CG-1 and §CG-3), and the sweep inherits it
for free because the linter derives its candidate from the corpus root the sweep
already hands it.

### 3. `sweep_lint()` forwards the `GEOMETRY:` token verbatim

`sweep_lint()` passes through only two-line finding pairs matching its finding
regex, plus the last non-empty line when it matches `^(OK|FAIL): `; **every other
line of the linter's stdout is discarded**. The linter's new own-line `GEOMETRY:`
token (`two-root-linter.md` §CG-6) therefore reaches nobody through the sweep
unless the sweep forwards it. It must forward it **verbatim, on its own line**,
and must **not** compute the token itself — the linter is the only process that
knows its own roots, and a second derivation is a second thing to get wrong.

`§Finding Shape and Summary`'s contract is unaffected: the forwarded token is not
a finding, is not counted as one, and is not subject to the finding regex.

**The summary check is a prefix match and is therefore safe.** `sweep_lint()`
tests the last non-empty line with `re.match(r"^(OK|FAIL): ", summary)` —
unanchored at the right — so the linter's new `— NOTHING SWEPT` suffix cannot make
it flag `linter exited … without a parseable summary`. No amendment is needed; it
is audited here because it is the pin an implementer adding a suffix is most
likely to trip over.

**Falsifying construction**: in the disjoint scratch construction of
`two-root-linter.md` §CG-8, `python3 "$TMPDIR/cg/far/tools/gc.py" --report --root
"$REPO"` output contains a line beginning `GEOMETRY: `. It contains none today,
and removing the forwarding returns it to none
(REQ-PKG-CONSUMERGEOMETRY-004 forwarding clause).

### 4. `AGG_FIX` names a path that resolves

`AGG_FIX` (`gc.py:175`) tells the reader to run
`tools/gc.py --fix traceability-aggregate` — a path that resolves for nobody but a
pre-move in-repo operator. It is corrected to the post-move spelling, as a
documentation-only edit in scope under REQ-PKG-CONSUMERGEOMETRY-001's permission.
§`--fix` Whitelist's rule set is unchanged; only the hint string is.

`lint_path()`'s sibling-first resolution is **unchanged** and stays as
REQ-PKG-PACKAGING-010 froze it. It gains one thing: reordering its candidate tuple
is half of row 4's mutation, so the ordering is now demonstrated by a
`gc.py --self-test` case carrying the `cg-row-4:` token rather than only asserted.

### Consumer-Geometry Acceptance Criteria

- [ ] **The surface exists on the sweep too.** `python3
  plugins/sdd/tools/gc.py --help` names `--suite-root`, and `Gc(...)` accepts a
  `suite_root` keyword. Removing the flag from the parser, or the keyword from
  the constructor, makes this red — and it is red today, where neither exists
  (REQ-PKG-CONSUMERGEOMETRY-003 acceptance 1, sweep half).
- [ ] **Omitting it changes nothing *in the constructed strings*.** With
  `--suite-root` absent, the vector `lint_command()` returns and the `-c` shim it
  builds are byte-identical to today's, asserted by comparing both against the
  pre-change strings. **The geometry is not frozen with them**: the same shim run
  over a corpus holding `plugins/sdd/skills/` resolves tier 2 in the
  constructor and reports `suite_contained() == True`, which
  `two-root-linter.md` §Consumer-Geometry Acceptance Criteria asserts as its own
  bullet. An implementation that reads this pin as freezing the shim's geometry
  makes that bullet red. A
  `gc.py`-side default guess makes this red and would additionally install the
  second derivation `two-root-linter.md` §CG-1 rejects
  (REQ-PKG-CONSUMERGEOMETRY-003 acceptance 2,
  sweep half).
- [ ] `lint_command()`'s argv branch returns a vector carrying the suite root,
  asserted on the vector; its `-c` shim branch constructs its `Linter(...)` with
  the same suite root, asserted by running the shim against a fixture and reading
  back `suite_contained()`. Fixing only the argv branch leaves the shim half red
  (REQ-PKG-CONSUMERGEOMETRY-003 acceptance 3).
- [ ] `gc.py --self-test` registers a case whose failure string begins
  `cg-row-4:`, and applying row 4's mutation on a temporary copy — dropping the
  suite-root pass-through, or reordering `lint_path()`'s candidate tuple — makes
  the printed `SELF-TEST FAIL:` list contain a line beginning with that token;
  reverting it returns the run to exit 0 with no such line
  (REQ-PKG-CONSUMERGEOMETRY-001 acceptances 1, 2).
- [ ] In `two-root-linter.md` §CG-8's disjoint scratch construction, the far
  `gc.py --report --root "$REPO"` prints a line beginning `GEOMETRY: ` and raises
  **no** `[structure] skills/ directory not found` finding, where today it prints
  no such line and raises exactly one such finding. Removing the forwarding
  returns the token to absent; reverting `lint_command()` returns the finding
  (REQ-PKG-CONSUMERGEOMETRY-004 forwarding clause;
  REQ-PKG-CONSUMERGEOMETRY-006 acceptance 2).
- [ ] **`gc.py` derives no geometry of its own** — the sweep forwards, never
  computes. "Geometry-deriving expression" has no grep spelling, so this
  criterion is stated as **two halves, both required**; either alone is weak,
  the grep because it can be satisfied by renaming and the mutation because it
  leaves the prose undecidable. The mechanism under test is §3 above
  (*`sweep_lint()` forwards the `GEOMETRY:` token verbatim*) — **not** §4,
  which is a separate `AGG_FIX` criterion.
  - **(a) The grep.** `grep -nE '\bsuite_contained\b|\b(nested|equal|disjoint)\b'
    plugins/sdd/tools/gc.py`, ignoring comment lines, returns matches **only**
    inside the forwarding pass-through — that is, only on lines that read a
    token back off the linter's own stdout. Every other match is a derivation
    and fails this half. The permitted set is enumerated rather than counted:
    the `--self-test` assertions of row 4 that compare `cg4_geometry(...)`'s
    return — a string lifted verbatim from a linter run — against
    `"GEOMETRY: nested"` / `"GEOMETRY: disjoint"`. A match on any line that
    computes a member from `Path` comparison, containment or root equality is
    red.
  - **(b) The mutation, run and not described.** On a temporary copy of
    `gc.py`, compute the token inside the sweep (derive a member from the
    corpus/suite roots and emit a second `GEOMETRY:` line); in §CG-8's disjoint
    scratch construction the far `gc.py --report --root "$REPO"` output then
    carries a **duplicate** `GEOMETRY:` line — two where the forwarding alone
    gives exactly one. Reverting returns the count to one. A `gc.py` that
    already derived would show the duplicate before the mutation
    (REQ-PKG-CONSUMERGEOMETRY-004 forwarding clause).
- [ ] `AGG_FIX` names a path that resolves in this repository after the
  correction, asserted by resolving the named path at run time; a path that does
  not resolve fails this (REQ-PKG-CONSUMERGEOMETRY-005 acceptance 7).
- [ ] `python3 plugins/sdd/tools/gc.py --self-test` exits 0 after every edit made
  under REQ-PKG-CONSUMERGEOMETRY-001's permission, and remains in the committed
  `.pre-commit-config.yaml` hook set, asserted by parsing that file
  (REQ-PKG-CONSUMERGEOMETRY-001 acceptance 4).


## Pipeline-Observability Amendment (2026-09-22, REQ-GC-PIPELINEOBSERVABILITY-001, -002, -003, -004; REQ-GC-HARNESSP2-002, -003, REQ-GC-HARNESSP6-003 amended)

[Added 2026-09-22, workstream `pipeline-observability` —
RS-PIPELINEOBSERVABILITY-001 §Q5, §Q6 gaps 7 and 11, R9, R11, R15, §Open
Questions "Q5 dead-path citations"; Q-REQ-PO-F, -H, -I, -R, -W. Observed: the
snapshot-comparand class is behind 12 of the consumer-geometry cycle's 17
blocking review findings; 4 counting greps in `docs/spec` matched their own
line; a bare `Q-IMPL` id with no definition raised a live `qimpl-undefined`
fail instead of being rejected as malformed; the cycle's own stale chain closed
by argument, not by a gate.]

**Where the contract lives** (REQ-REQ-PIPELINEOBSERVABILITY-001 (b), 2026-09-22): this section is the record of *why* and states no contract of its own; the contract is in the sections of record named here, each edited in place under a `[Updated: 2026-09-22]` marker, and its acceptance criteria sit in this spec's own Acceptance Criteria section under the same date. §Sweep Table carries rows 16–19, the source-line discipline and the definitions of `literal-anchor`, `self-matching-grep` (command-line grammar; piped form out of scope) and `dead-path-citation` (token grammar, whitespace-free) (REQ-GC-PIPELINEOBSERVABILITY-001, -002, -004; REQ-GC-HARNESSP2-002 as amended); §Q-IMPL Counting Rule carries `qimpl-malformed` and the narrowed placeholder exclusion (REQ-GC-PIPELINEOBSERVABILITY-003; REQ-GC-HARNESSP2-003 as amended); §Shared-Spec Staleness carries the traced-by-active-plan `warn` exception (REQ-GC-HARNESSP6-003 as amended); §Routing at DONE carries the two added rows. Left consistent and not reopened: §CLI and Exit Codes (`warn` never fails `--report`; `fail` does), §Closed-Workstream Skip, §Finding Shape, §Cadence, §`--fix` Whitelist (none of the new rules joins it), §Row-Drop Safety, §Convention: Do Not Quote Another Repository's `Q-IMPL` Ids (REQ-GC-HARNESSP3-001's declined scoping is not reopened — membership is decided by the definition set, not by shape), and `pre-commit.md` (REQ-PC-MARKETPLACE-006: rules live in gc's table, not the hook).

**Why the span-blanking half is not applied** (requirements review round 5 C1): under the full `visible_lines()` the anchor rule measured 0 in 0 files against 69 in 7 under the fence half alone — a rule that could never fire. **Why the piped grep form is out of scope** (Q-REQ-PO-AB): the rule reads grep's own file operands, and a producer upstream of a pipe is not one; the earlier acceptance bullet of this spec that quoted a piped `sed … | grep -c` form as its own witness was self-referential and is rewritten to read the table row. **Why the token holds no whitespace** (Q-REQ-PO-W, Q-SPEC-PO-H): a backticked command ending in a path is a class the research's path-only measurement never counted. **Why `fail` for `self-matching-grep` only**: it is the one class whose live instances are counted and repaired in the same commit; the other three are standing `warn` floors (Q-REQ-PO-R).
