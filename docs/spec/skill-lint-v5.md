---
status: Approved
last_updated: 2026-09-22
requires:
  - REQ-LINT-001
  - REQ-LINT-002
  - REQ-LINT-003
  - REQ-LINT-004
  - REQ-LINT-005
  - REQ-LINT-006
  - REQ-LINT-007
  - REQ-LINT-HARNESSP4-001
  - REQ-LINT-HARNESSP4-002
  - REQ-LINT-HARNESSP5-001
  - REQ-LINT-HARNESSP5-002
  - REQ-LINT-HARNESSP6-001
  - REQ-LINT-HARNESSP6-002
  - REQ-LINT-HARNESSP6-003
  - REQ-PKG-PACKAGING-005
  - REQ-PKG-CONSUMERGEOMETRY-003
  - REQ-PKG-CONSUMERGEOMETRY-004
  - REQ-LINT-PIPELINEOBSERVABILITY-001
---

# Skill Lint v5

## Context

`tools/sdd-skill-lint.py` has five check classes (structure, forbidden phrases,
required contract markers, ordinals, relative Markdown links) driven by two
rule tables (`FORBIDDEN`, `REQUIRED`) plus fixed lists. RS-008 Q4 found: every
"marker present" contract of the harness-hardening cycle is checkable by a
`REQUIRED` row; a soft size limit, backtick `references/` path resolution and
remediation text need three small code changes; the linter has no warn tier
(every finding exits 1); structure/ordinal/link findings carry no remediation.
Baseline 2026-09-17: `sdd-orchestrate/SKILL.md` 607 lines, `sdd-migrate` 464,
eight others 187–354.

This spec defines the v5 linter: a `fix` field on every finding, a warn
severity, a SKILL.md size check, backtick path resolution, the `REQUIRED` rows
for the new contracts, and the marker-4 prose move out of
`sdd-orchestrate/SKILL.md` with its two guards. It fulfils REQ-LINT-001..007.

## Design

### Finding Shape and Remediation (REQ-LINT-001)

Every finding is rendered as:

```
<path>:<line>: [<rule>] <message>
    fix: <one-line remediation>
```

- `FORBIDDEN` and `REQUIRED` rows gain a `fix` string beside `reason`.
- `flag(path, line_no, rule, msg, fix, severity="fail")` — `fix` is a required
  positional; a call without it is a `TypeError`, so no code path can emit a
  finding without remediation.
- Structure, ordinal and link checks (no rule table) emit fixed remediation
  strings, e.g. ordinals → `fix: renumber the list so ordinals are consecutive
  from 1 outside code fences`; links → `fix: correct the relative path or
  create the target file`; frontmatter → `fix: set name: to the directory
  name`.
- The self-test asserts every emitted finding has a non-empty `fix`.

### Severity Tier (REQ-LINT-002)

Two severities: `fail` (exit 1, current behavior) and `warn` (printed with a
`WARN ` prefix, does not affect the exit code). Rule-table rows may carry
`"severity": "warn"`; rows without it default to `fail`. `check_size()` emits
`warn` or `fail` by threshold. Summary line:

```
OK: 13 file(s) clean                      # no findings
OK: 13 file(s) clean, 2 warning(s)         # warnings only → exit 0
FAIL: 3 finding(s), 2 warning(s)           # any fail → exit 1
```

Findings are stored as `(severity, text)`; `run()` exits 1 iff any `fail`.

### SKILL.md Size Check (REQ-LINT-003)

```python
SIZE_WARN_LINES = 400   # entry point should read as a table of contents
SIZE_FAIL_LINES = 1000  # project guideline (REQ-ORCH-019)
```

`check_size()` counts lines (`wc -l` semantics) of every `skills/*/SKILL.md`
only — `references/*.md` and `USAGE.md` are exempt. Over `SIZE_WARN_LINES` →
`WARN [size] SKILL.md is N lines (> 400)`, `fix: move detail to references/ and
leave a stub; the entry point should read as a table of contents`. Over
`SIZE_FAIL_LINES` → `fail`. The baseline is **none** [Amended 2026-09-19,
harness-p5 — REQ-LINT-HARNESSP5-002; the 2026-09-17 text named a two-file warn
set, `sdd-orchestrate` (607) and `sdd-migrate` (464)]: the shipped skill set
warns on no file and fails on none (§Size Warn-Clean Baseline).

**Why 400 warn / 1000 fail**: 400 flags exactly the two files that absorbed
gate prose while leaving the other eight untouched (RS-008 Q4 size table); 1000
is the existing REQ-ORCH-019 guideline. Both are module constants so a later
audit can retune without touching check logic.

### Size Warn-Clean Baseline (REQ-LINT-HARNESSP5-001, REQ-LINT-HARNESSP5-002)

[Added 2026-09-19, harness-p5 — decided at DISCUSS (kickoff §Scope item 3): the
size target is **lint warn-clean**, not a raised constant. Evidence:
RS-HARNESSP5-001 §Decided, measured 2026-09-19; the p4 accepted reds R7/R8
(`docs/ws/harness-p4/verification.md` §Issues Found → Minor).]

The shipped skill set must produce **no `[size]` warning**. Three entry points
are over the threshold today and each moves detail to `references/*.md`:

| File | Measured 2026-09-19 | Target | Mechanism |
|---|---|---|---|
| `skills/sdd-orchestrate/SKILL.md` | 551 | **< 400** | move to existing or new `references/*.md`; stubs stay |
| `skills/sdd-migrate/SKILL.md` | 464 | **< 400** | same |
| `skills/sdd-implement/SKILL.md` | 434 | **< 400** | same |

**Invariants of every move** (the contract; which sections move and into which
file is the implementer's choice):

- each moved section leaves a **stub** carrying the marker-3 "behavior
  UNCHANGED" sentence where one applies and a resolving link (REQ-LINT-004);
- every `REQUIRED` marker row stays satisfied — a row **may be re-pointed** to
  the new references file, **never dropped** (REQ-LINT-005/-006);
- the `VERSION_GATED_SKILLS` `docs/.sdd-version` mention stays in `SKILL.md`;
- the `[template-drift]` pair fences stay byte-identical — if a paired fence
  moves, its pair-table row is re-pointed in the same commit
  (REQ-LINT-HARNESSP4-001);
- `python3 plugins/sdd/tools/skill-lint.py` exits 0 **and** its summary line matches
  `OK: N file(s) clean` with **no** warning clause — the linter appends
  `, W warning(s)` only when `W > 0`, so a warn-clean run prints no count and a
  `0 warning(s)` expectation can never be satisfied; do not restore it.

**Why warn-clean rather than a higher `SIZE_WARN_LINES`**: the constant encodes
"the entry point reads as a table of contents"; retuning it would hide exactly
the growth RS-008 Q4 sized, and the three files grew by absorbing gate prose
that the references layer exists to hold.

**Baseline restatements** (REQ-LINT-HARNESSP5-002): this spec's REQ-LINT-003
restatement reads **none** (§SKILL.md Size Check) and its REQ-LINT-007 bound
reads **under 400** (§Marker-4 Prose Move), matching the `[Updated]` notes on
those two requirements. Q-IMPL-073 and Q-IMPL-084 record the historical
figures and read as history; their bodies are unchanged, and Q-IMPL-073's
**Spec reference** quote is re-aimed at the amended bound (the text-only
re-point device of `deviation-protocol.md` §Spec-Reference Integrity). The R7/R8
`reproduce:` commands — `python3 tools/sdd-skill-lint.py | grep -c '\[size\]'`
→ `0`, `wc -l skills/sdd-orchestrate/SKILL.md` → a number below 400 — are the
closing evidence `docs/ws/harness-p5/verification.md` `## Post-cycle Fixes`
records.

The sibling size item of the same kickoff scope, the `docs/spec/telemetry.md`
split (REQ-LINT-HARNESSP5-003, Q-REQ-P5-G), is owned by `telemetry.md` §Moved
Sections and `telemetry-reader.md`; the lint does not size-check specs.

### `references/` Path Resolution (REQ-LINT-004)

`check_links()` continues to resolve `[text](relative.md)` links outside code
fences and additionally resolves backtick-quoted relative paths:

| Pattern (outside fenced code) | Resolved against | Severity |
|---|---|---|
| `` `references/<file>` `` | the linted file's skill directory | fail |
| `` `skills/<skill>/references/<file>` `` | repository root | fail |
| `` `docs/spec/<file>.md` `` | repository root | warn |

Paths inside fenced code blocks are ignored, as today. Fragments (`#…`) and
trailing punctuation are stripped before resolution. Fix strings: `fix: create
the referenced file or correct the path`. A SKILL.md mentioning
`` `references/v4-workstreams.md` `` before that file exists must fail; the six
existing `[…](references/…)` links in `sdd-orchestrate/SKILL.md` must still
resolve.

### `REQUIRED` Rows — Core Contracts (REQ-LINT-005)

Nine rows, each with `reason` and `fix`:

| # | File | Pattern (regex) | min | Contract |
|---|---|---|---|---|
| a | `skills/sdd-orchestrate/SKILL.md` | `fix[- ]loop cap\|iteration N of 3` | 1 | REQ-HARN-001 |
| b | `skills/sdd-orchestrate/SKILL.md` | `replan re-entry cap` | 1 | REQ-HARN-002 |
| c1 | `skills/sdd-orchestrate/references/dispatch-templates.md` | `Budget:` | 3 | pipeline + review + verifier templates (REQ-HARN-004) |
| c2 | `skills/sdd-orchestrate/references/fan-out.md` | `Budget:` | 1 | leaf template (REQ-HARN-004) |
| d1 | `skills/sdd-review/SKILL.md` | `VERDICT: APPROVE \| APPROVE_WITH_FIXES \| REJECT` | 1 | producer (REQ-HARN-013) |
| d2 | `skills/sdd-orchestrate/SKILL.md` | `(?<!CHUNK_)VERDICT:` | 1 | consumer (REQ-HARN-013) |
| e1 | `skills/sdd-orchestrate/references/dispatch-templates.md` | `CHUNK_VERDICT: PASS \| FAIL` | 1 | verifier template (REQ-HARN-014) |
| e2 | `skills/sdd-orchestrate/SKILL.md` | `CHUNK_VERDICT:` | 1 | consumer (REQ-HARN-014) |
| f | `skills/sdd-replan/SKILL.md` | `-replan-` | 1 | archive filename contract (REQ-HARN-003) |

Producer/consumer pairs (d, e) follow the existing `**Depends on**` ↔ fan-out
pattern: removing either half fails the lint with that row's fix string. Row d2
uses a negative lookbehind so that the e2 marker `CHUNK_VERDICT:` can never
satisfy the review-verdict consumer row (a plain `VERDICT:` would match inside
`CHUNK_VERDICT:`). The lint checks marker presence only; the orchestrator's own
token parser matches `^VERDICT:` at line start, last occurrence wins
(`harness-return-contract.md` §VERDICT Token).
Removing any one of the nine markers exits 1; with all present the lint exits 0
(modulo size warnings).

### `REQUIRED` Rows — Remaining Contracts (REQ-LINT-006)

| File | Pattern | min | Contract |
|---|---|---|---|
| `skills/sdd-orchestrate/references/dispatch-templates.md` | `RETURN:` | 2 | pipeline + verifier templates (REQ-HARN-009) |
| `skills/sdd-orchestrate/references/fan-out.md` | `RETURN:` | 1 | leaf template (REQ-HARN-009) |
| `skills/sdd-orchestrate/references/dispatch-templates.md` | `status: COMPLETE \| PARTIAL \| BLOCKED \| BUDGET_EXHAUSTED` | 1 | own-line status token (REQ-HARN-009) |
| `skills/sdd-orchestrate/references/dispatch-templates.md` | `\{repair_packet\}` | 2 | template + slot contract (REQ-HARN-011, mirrors `{qimpl_block}`) |
| `skills/sdd-orchestrate/references/dispatch-templates.md` | `Write scope:` | 3 | pipeline + review + verifier (REQ-HARN-020) |
| `skills/sdd-orchestrate/references/fan-out.md` | `Write scope:` | 1 | leaf template (REQ-HARN-020) |
| `skills/sdd-implement/SKILL.md` | `oscillation` | 1 | stuck rule (REQ-HARN-007) |
| `skills/sdd-implement/SKILL.md` | `checkpoint` | 1 | blocked-note format (REQ-HARN-008) |
| `skills/sdd-replan/SKILL.md` | `checkpoint` | 1 | blocked-note intake (REQ-HARN-008) |

Behavioral principles (pruned state, orchestrator owns routing) are not linted
beyond phrase presence; review verifies them.

### Marker-4 Prose Move (REQ-LINT-007)

`skills/sdd-orchestrate/SKILL.md`'s marker-4-only sections move to
`skills/sdd-orchestrate/references/v4-workstreams.md`, each leaving a stub that
keeps the "behavior UNCHANGED under marker 3" sentence and a resolving link:

| Section | Moves | Stub |
|---|---|---|
| §Workstream Picker + 3 subsections (~79 lines) | yes | ~5 lines: marker-3 sentence + link + a `research_id` mention (guard 1) |
| §Phase Detection "Workstream & version gate (v4)" and "Marker-4 gate for done-vs-new-cycle" (~38) | yes | one-line stubs |
| §Entry Points "Marker-4 scope" paragraph | yes | one line |
| §KICKOFF "Kickoff path — version gate" | yes | one line |
| §Integration anchor + "Marker-4 anchor" paragraph | yes → point at `references/fan-out.md` §0 | one line |
| "Upgrade offer (entry, all markers)", phase table, §The gate, dispatch contracts, §Isolation Discipline, §Rules, §Orchestrator-Only Work | **no** — not part of *this* move | — |

**Scope of the `no` row.** The `Moves: no` row is scoped to **this**
marker-4 prose move into `references/v4-workstreams.md` — it says those
sections are not marker-4-only prose and so are not carried by REQ-LINT-007,
**not** that they are pinned to `SKILL.md` forever. The general size work of
§Size Warn-Clean Baseline governs them, and there "which sections move and
into which file is the implementer's choice" applies as written: any of them
may later move into another `references/*.md` under that section's invariants
(stub with the marker-3 sentence, `REQUIRED` rows re-pointed not dropped,
`[template-drift]` fences kept paired). [Clarified 2026-09-20, harness-p5 —
the Chunk 8 move of §Isolation Discipline and §Orchestrator-Only Work into
`references/isolation.md` relied on exactly that reading.]

#### Qualification of the "must not move" Row (REQ-LINT-HARNESSP6-002)

[Added 2026-09-20, harness-p6 — REQ-LINT-HARNESSP6-002]

Read in sequence, `docs/requirements/integration/skill-lint.md`'s REQ-LINT-007
and REQ-LINT-HARNESSP5-001 contradict each other: the earlier one's "must not
move" list forbids movement that the later one, in the same file, requires (the
Chunk 8/9 rescoping). The contradiction is textual, not behavioural — this
spec's §Scope of the `no` row already states the reconciling reading — so the
fix is a **qualification on the requirement text**, not a design change:

- REQ-LINT-007 gains a bracketed dated `[Updated: 2026-09-20 …]` note naming the
  authorised exception and **REQ-LINT-HARNESSP5-001** as the authorising
  requirement.
- The requirement's **id, its number and its original text are not changed** —
  amending the original in place would break every artifact that cites it and
  would erase the record that the two requirements once disagreed.
- No lint rule, no linter table and no skill file changes for this item; it is a
  requirements-corpus text fix whose contract is recorded here so the implement
  stage has a spec to trace to.

Two mandatory guards:

1. **`research_id` lint row.** The `REQUIRED` row `research_id` ≥ 3 in
   `SKILL.md` counts one occurrence inside the picker section. Either the picker
   stub keeps a `research_id` mention (preferred — no lint change) or the row is
   split into `SKILL.md` ≥ 2 + `references/v4-workstreams.md` ≥ 1.
2. **Q-IMPL-016 supersession.** Q-IMPL-016 in `docs/spec/ws-orchestration.md`
   pins the picker to `SKILL.md`; Q-IMPL entries are append-only, so the
   implementation appends a **new** Q-IMPL entry (Tier 1, "Picker prose lives
   in `references/v4-workstreams.md`; gate and stub remain in `SKILL.md`;
   supersedes Q-IMPL-016's container statement") and marks Q-IMPL-016
   `[superseded by Q-IMPL-NNN]` per `deviation-protocol.md` §Numbering — never
   an edit to Q-IMPL-016's body.

`docs/.sdd-version` must remain mentioned in `SKILL.md` (`VERSION_GATED_SKILLS`
check). Target size after the move plus the HARN stubs (pointers to
`references/write-scope.md` and `references/return-contract.md`): **under 400
lines** [Amended 2026-09-19, harness-p5 — REQ-LINT-HARNESSP5-002; the earlier
bound accepted a residual size warn] — warn-clean per §Size Warn-Clean Baseline;
a size fail was never acceptable.

### `[template-drift]` — Fenced Leaf Bodies Restated in Specs Stay Byte-Identical (REQ-LINT-HARNESSP4-001)

[Added 2026-09-18, harness-p4 — REQ-LINT-HARNESSP4-001; `docs/ws/harness-p3/verification.md` §V8;
guards REQ-HARN-HARNESSP3-002's byte-consistency contract]

A new rule extracts the fenced bodies of named **pairs** — source of record on
the skill side, restatement on the spec side — hashes them and, on divergence,
emits:

```
<spec file>:<line>: [template-drift] fenced body diverges from dispatch-templates.md L<n>
  fix: edit skills/sdd-orchestrate/references/dispatch-templates.md (source of record) — the spec side is Approved and stable; if the spec is the intended change, amend both in one commit
```

The pair list is a **table in the linter**, so a future restated body is one
row:

| Source (skill side) | Body | Restated in (spec side) |
|---|---|---|
| `references/dispatch-templates.md` §CHUNK VERIFIER | dispatch prompt body (incl. the `RETURN:` block) | `docs/spec/harness-chunk-verifier.md` §Verifier Dispatch Template |
| `references/dispatch-templates.md` §CHUNK VERIFIER | verdict rule | `docs/spec/harness-chunk-verifier.md` §Verdict Rule |
| `references/dispatch-templates.md` §RED TEAM | dispatch prompt body | `docs/spec/adversarial-verify.md` §Red Dispatch Template |
| `references/dispatch-templates.md` §RED TEAM | `RETURN:` block | `docs/spec/adversarial-verify.md` §Return Contract and `RED_VERDICT:` |

Matching is by the **fence's first line** (an anchor text per row, e.g. `You are
a non-interactive chunk-close verifier`) so the rule survives a heading rename;
comparison is byte-for-byte on the fence body after stripping the fence markers
only — no whitespace normalisation, because the token-position contract of
REQ-HARN-HARNESSP4-007 is itself a whitespace fact. The four bodies (the
four rows above) are byte-identical today and nothing keeps them so; a divergence would first surface
as a leaf returning the wrong shape. Severity: **fail** (exit 1), with
`--self-test` mutating one character inside the RED TEAM `RETURN:` block and
asserting the finding names `adversarial-verify.md` and the fix.

**Absent side and rendered order** [folded from Q-IMPL-HARNESSP4-008,
2026-09-19 — REQ-QIMPL-HARNESSP5-001; the rendered shape above was amended in
the same edit, the tag after the location as every other rule renders]: the
pair table is the linter's `TEMPLATE_PAIRS` (four rows, each carrying its one
`fix` string) with the source of record as the constant `TEMPLATE_SOURCE`, and
the check runs with the other suite rows only. A restating **spec file absent**
from the linted **corpus root** — the root the CLI positional names, defaulting
to the invocation cwd, the suite root being the script's own plugin root
(`two-root-linter.md` §2) — **warns**, never fails: a consumer repo has no
`docs/spec/` (the F11 principle, **ungated set only**; exceptions
`check_retired_prefix` and `TEMPLATE_PAIRS` — §Two-Root Amendment). A **present** spec that has
lost its anchored fence, or a source of record that has lost its anchored fence
while a spec still restates it, **fails** alone, naming the counterpart in the
message. Anchors match by `startswith` on the fence's first line (the RED TEAM
return-contract fence's first line carries a trailing `# one heading per spec
examined` comment). The finding renders through the linter's common `flag()`
shape, so `<line>` is the restating fence's opening line in the spec and the
"no finding without a fix" guarantee holds for this rule as for every other.

**Plan-ordering constraint** (carried from requirements): this rule
(REQ-LINT-HARNESSP4-001) lands **before** the terminal-token column-0 edit
(REQ-HARN-HARNESSP4-007, `harness-chunk-verifier.md` §Terminal Token at Column
0), and that edit is made with the rule active in the same commit on both
sides, leaving the lint at exit 0.

### `REQUIRED` Row — `COMMIT: COMPLETE | INCOMPLETE` (REQ-LINT-HARNESSP4-002)

[Added 2026-09-18, harness-p4 — REQ-LINT-HARNESSP4-002; every gate token so far shipped with a lint pair]

| File | Pattern (regex) | min | Contract |
|---|---|---|---|
| `skills/sdd-orchestrate/references/loop-control.md` | the fenced pattern below | 1 | §5 order, item 8 (REQ-HARN-HARNESSP4-001) |
| `skills/sdd-orchestrate/SKILL.md` | same | 1 | §The gate one-line summary |

```
COMMIT: (COMPLETE \| INCOMPLETE|COMPLETE|INCOMPLETE)
```

The pattern matches `COMMIT: COMPLETE` / `COMMIT: INCOMPLETE` (and the family
spelling `COMMIT: COMPLETE | INCOMPLETE`) and does **not** match a file that
only names `SCOPE:` — the same guard the `CHUNK_VERDICT:` row applies. `fix:`
points at `references/write-scope.md` §7 as the defining section. Removing the
line from either file exits 1 with the row's fix; `--self-test`'s mutation loop
covers the row.

### `REQUIRED` Rows — `PLAN:` and `GIT_STATE` (REQ-LINT-HARNESSP6-001)

[Added 2026-09-20, harness-p6 — REQ-LINT-HARNESSP6-001; `PLAN:` was the only
gate token shipping without a lint pair, and the new `GIT_STATE` finding name
would have shipped the same way]

**Why.** Every gate token so far shipped with a producer/consumer `REQUIRED`
pair, so deleting it from either file fails the lint. `PLAN:` did not, which
means its deletion from `references/loop-control.md` §6 is today unguarded while
the identical deletion of any sibling token fails. The `GIT_STATE` finding name
of REQ-HARN-HARNESSP6-001 would be equally unguarded in
`references/write-scope.md`; RS-HARNESSP6-001 Q2 recommended the two land
together as one lint change, and that recommendation is **adopted** here rather
than declined.

| File | Pattern (regex) | min | Contract |
|---|---|---|---|
| `skills/sdd-orchestrate/references/loop-control.md` | `PLAN: INCOMPLETE` | 1 | §6 pause family, the producer (`harness-loop-control.md` §Plan Completion Ownership) |
| `skills/sdd-orchestrate/SKILL.md` | same | 1 | §The gate one-line summary, the consumer |
| `skills/sdd-orchestrate/references/write-scope.md` | `GIT_STATE` | 1 | §5, the producer (`harness-write-scope.md` §Git-State Observation) |
| `skills/sdd-orchestrate/SKILL.md` | same | 1 | §The gate one-line summary, the consumer |

`fix:` on the `PLAN:` rows points at `harness-loop-control.md` §Plan Completion
Ownership; on the `GIT_STATE` rows at `harness-write-scope.md`
§Git-State Observation. `GIT_STATE` is a finding **name inside the `SCOPE:`
block**, not an own-line gate token, so its pattern carries no trailing colon
and no option-set alternation — the row guards the name's presence, which is all
that is needed to make its deletion fail.

### `REQUIRED` Row — `CONVERGENCE:` (REQ-LINT-HARNESSP6-003)

[Added 2026-09-20, harness-p6 — REQ-LINT-HARNESSP6-003]

The L2 gate token of REQ-ORCH-HARNESSP6-001 gets the same pair that guards
`COMMIT:` — one row for the producer, one for the consumer:

| File | Pattern (regex) | min | Contract |
|---|---|---|---|
| `skills/sdd-orchestrate/references/loop-control.md` | `CONVERGENCE:` | 1 | §5 order, item 6c (`harness-loop-control.md` §Convergence Signal) |
| `skills/sdd-orchestrate/SKILL.md` | same | 1 | §The gate one-line summary |

`fix:` points at `harness-loop-control.md` §Convergence Signal as the defining
section. These three **pairs** — **six rows**: the `PLAN:` pair, the
`GIT_STATE` pair adopted into it, and this pair — are **this cycle's only lint
changes**, and they land
together as one change to the `REQUIRED` table.

### `FORBIDDEN` Row — `literal-anchor` over the swept markdown set (REQ-LINT-PIPELINEOBSERVABILITY-001)

`[Updated: 2026-09-22]` (workstream `pipeline-observability`; the record of why
is §Pipeline-Observability Amendment). One `FORBIDDEN` row with pattern
`[\w./-]+\.md:\d+`, `files: None` — every markdown file the linter sweeps
under `plugins/sdd/**`, the **swept markdown set**, not `plugins/sdd/tools/*.py`
nor `plugins/sdd/tools/fixtures/**` (Q-REQ-PO-S) — with `reason` and `fix`
strings, keeps the snapshot-comparand class out of the shipped skill, reference
and agent text through the mechanism that already sweeps that tree.
**Source-line discipline, stated as `drift-sweep.md` §Sweep Table states it**:
every line outside a fenced block is read **whole**; inline-code (backticked)
and quoted spans are **not** blanked, so an anchor written as
`` `<file>.md:<line>` `` on a visible line is a finding, while an anchor inside a
fenced block is an illustration and raises nothing. The `FORBIDDEN` scan is
raw-line and fence-inclusive by default, so this row carries a per-row flag —
name chosen at implementation (Q-SPEC-PO-E; `visible_only`,
Q-IMPL-PIPELINEOBSERVABILITY-002) — that restricts its scan to
unfenced lines through the linter's existing fence filter; rows without the
flag behave exactly as before. The tree carried 0 such anchors on 2026-09-22
(measured over the 28 swept files; the three markdown files outside the swept
set are the fixtures README, which holds the tree's single live anchor, and the
two arbitration fixture bodies), so the phrase lands at no repair cost. The
`--self-test` `FORBIDDEN` count pin moves by one with the row
(REQ-LINT-PACKAGING-008's discipline).

### `REQUIRED` Rows — Pipeline-Observability (p1–p15)

`[Updated: 2026-09-22]` (workstream `pipeline-observability`). Two rows landed
before the specs stage with the V3 routing (`proceeds **without re-review**`
on `skills/orchestrate/SKILL.md`, `GROWTH: ` on
`skills/orchestrate/references/loop-control.md`) and one `FORBIDDEN` phrase
(`then re-run the review for this stage`); they are in force and are **not**
counted among the fifteen below.

| # | File | Pattern | min | Contract |
|---|---|---|---|---|
| p1 | `agents/reviewer.md` | `git stash` | 1 | git-state sentence (`harness-agents.md` §The frontmatter contract, REQ-AGENT-PIPELINEOBSERVABILITY-001) |
| p2 | `agents/chunk-verifier.md` | `git stash` | 1 | same |
| p3 | `agents/red-team.md` | `git stash` | 1 | same |
| p4 | `skills/orchestrate/references/loop-control.md` | `consecutive consumed` | 1 | `reject_run` counts consecutive `REJECT`s, §2 (`harness-loop-control.md` §Fix-Loop Cap, REQ-HARN-001 as amended) |
| p5 | `skills/orchestrate/references/loop-control.md` | `post-manual` | 1 | §2b manual intervention → `post-manual` review (REQ-HARN-PIPELINEOBSERVABILITY-003) |
| p6 | `skills/orchestrate/references/loop-control.md` | `voids its verdict` | 1 | §1b void sentence, a pattern disjoint from row p8's bound line (`harness-write-scope.md` §Git-State Observation, REQ-HARN-PIPELINEOBSERVABILITY-004) |
| p7 | `skills/orchestrate/references/write-scope.md` | `voided` | 1 | §8 void sentence, the consumer half (REQ-HARN-PIPELINEOBSERVABILITY-004) |
| p8 | `skills/orchestrate/references/loop-control.md` | `voided re-dispatch.*REDO_MAX\|REDO_MAX.*voided re-dispatch` | 1 | §1b bound — `voided re-dispatch` and `REDO_MAX` on one visible line (REQ-HARN-PIPELINEOBSERVABILITY-004, Q-REQ-PO-Q) |
| p9 | `skills/orchestrate/references/return-contract.md` | `tier/verdict conflict` | 1 | §Tier-heading parsing — both counts and the six pauses (`harness-return-contract.md` §VERDICT Token, REQ-HARN-PIPELINEOBSERVABILITY-005) |
| p10 | `skills/orchestrate/references/dispatch-templates.md` | `mutations \+ gates` | 1 | the test-run derivation sentence (`harness-loop-control.md` §Budget Slot, REQ-HARN-PIPELINEOBSERVABILITY-006) |
| p11 | `skills/implement/SKILL.md` | `script path in a command` | 1 | Check 3's derived module set (`chunk-close-review.md` §Checklist, REQ-CHKC-004 as amended) |
| p12 | `agents/chunk-verifier.md` | `script path in a command` | 1 | the verifier's Check 3 clause (REQ-CHKC-004 as amended) |
| p13 | `skills/review/SKILL.md`, `agents/reviewer.md` | `at least one Material finding` | 1 | the `Approve with fixes` predicate in **both** producers (`review.md` §Report Format, REQ-REV-PIPELINEOBSERVABILITY-001 (vi)) |
| p14 | `skills/orchestrate/references/return-contract.md` | `counts as zero` | 1 | §Tier-heading parsing's placeholder normalisation (REQ-HARN-PIPELINEOBSERVABILITY-005) |
| p15 | `skills/orchestrate/USAGE.md` | `proceeds without re-review` | 1 | §7b `Reading the stage gate` — the operator guide restates the routing by verdict (`review.md` §Report Format; added by the implement-stage fix, Q-IMPL-PIPELINEOBSERVABILITY-011) |

Each row carries `reason` and `fix`. Rows p4, p10, p11 and p12 pin a phrase
from the sentence they protect rather than a single common word (`consecutive`,
`mutations`, `convention` each occur in unrelated prose — `skills/implement/SKILL.md`
already says "conventions" of `CLAUDE.md`), so the row fails when the sentence
goes, not only when the word does. Row p13 is one row with two `files:`
entries, so a temp copy with the line removed from either producer fails
naming that file. The self-test's mutation loop covers all fifteen;
`len(REQUIRED)` grows by exactly fifteen (fourteen at Chunk 1, one at the
implement-stage fix) and the suite asserts the new **exact** total, never a
`>=` bound. Row p15 is the one row on `USAGE.md`, the operator-facing guide:
the routing sentence it pins is prose a human reads, not a gate line, and the
row exists because the guide contradicted the landed routing for a whole
stage before the closing review caught it. Row p8's pattern is the one place the
linter pins a co-occurrence on one visible line; it is a single row because the
bound is one sentence. Row p6's pattern is chosen so that p8's bound line
cannot satisfy it: the bound line says `voided re-dispatch`, never `voids its
verdict`, so deleting the §1b void sentence while the bound stays leaves p6
unsatisfied and the linter red.

### Self-Test Extension

`--self-test` gains fixtures for: a finding without `fix` (must be impossible —
asserted via signature); a warn-only fixture exits 0 with `1 warning(s)`; a
401-line SKILL.md warns and a 1001-line one fails; a backtick
`references/missing.md` fails while an existing one passes; each new `REQUIRED`
row fails when its marker is removed from a temp copy.
The harness-p6 delta's mutation loop covered the **six** rows that cycle added
— `PLAN:` ×2, `GIT_STATE` ×2, `CONVERGENCE:` ×2 (the table counts rows, not
files, so the two rows that both target `SKILL.md` are distinct rows) — and
asserted the total it landed; that is history, kept as the record of the
loop's shape, and the total it asserted is superseded below.

`[Updated: 2026-09-22]` (workstream `pipeline-observability`,
REQ-LINT-PACKAGING-007 as amended, Q-REQ-PO-AL; REQ-LINT-PIPELINEOBSERVABILITY-001):
**this cycle's totals.** The mutation loop extends over the fifteen
`REQUIRED` rows p1–p15 of §`REQUIRED` Rows — Pipeline-Observability and the one
`FORBIDDEN` row of §`FORBIDDEN` Row — `literal-anchor`:
`len(REQUIRED)` grows by exactly fifteen (fourteen at Chunk 1, one at the
implement-stage fix, Q-IMPL-PIPELINEOBSERVABILITY-011) and `len(FORBIDDEN)` by exactly one,
so the populations land at `REQUIRED=57 FORBIDDEN=15` (`VERSION_GATED=9
V4_CONTRACT=7` untouched). The
suite asserts those **exact** totals — never a `>=` bound — but not as a
literal frozen in the test: the assertion is the three-way equality
REQ-LINT-PACKAGING-007 defines, `--print-population`'s printed counts ==
`len()` of the code tables == the numbers `two-root-linter.md` §6 states under
its dated marker. The `pinned = {…}` dict the self-test carries today (`42 / 9 /
7 / 14`, each `label=value` asserted present among the printed lines) is that
third surface's copy and is replaced by a read of §6's numbers, so a cycle that
adds a row moves §6 in the same change and the self-test fails the change that
moves one side alone (a row added without §6, a §6 number edited without a
row, a count written into the flag as a literal). The totals stated here are
the delta's arithmetic, not a fourth surface: the contract lives in
`two-root-linter.md` §6 and REQ-LINT-PACKAGING-007.

## Verification

### Automated
- `python3 tools/sdd-skill-lint.py --self-test` exits 0 and exercises every
  new check.
- `python3 plugins/sdd/tools/skill-lint.py` on the implemented skill set exits 0 and
  prints `OK: N file(s) clean` with **no** warning clause — the `, W warning(s)`
  clause is emitted only when `W > 0`, so warn-clean shows no count and a
  `0 warning(s)` expectation must not be restored — warn-clean since 2026-09-19
  (REQ-LINT-HARNESSP5-001).
- Mutation test: for each of the nine core rows, delete the marker in a temp
  copy → exit 1 and the row's `fix:` printed.
- `grep -c '"fix"' tools/sdd-skill-lint.py` equals the number of rule rows;
  `grep -n 'self.flag(' tools/sdd-skill-lint.py` shows a fix argument on every
  call.

### Manual
- Run the linter before and after the marker-4 move: exit 0 both times; after
  the move `wc -l skills/sdd-orchestrate/SKILL.md` < 400; every moved section
  has a stub containing "UNCHANGED" and a link that resolves;
  `ws-orchestration.md` has a new Q-IMPL entry citing Q-IMPL-016.

### Acceptance Criteria
- [ ] Every finding prints `fix:`; `flag()` requires it; rule tables carry `fix` (REQ-LINT-001)
- [ ] Warn tier exists; warn-only run exits 0 and prints the warning count; one fail still exits 1 (REQ-LINT-002)
- [ ] Size check at 400 warn / 1000 fail as module constants; baseline warns on none — the shipped skill set is `[size]`-clean (REQ-LINT-003; baseline amended 2026-09-19 by REQ-LINT-HARNESSP5-002)
- [ ] Backtick `references/` and `skills/<skill>/references/` paths resolve (fail), `docs/spec/*.md` mentions resolve (warn); code fences ignored (REQ-LINT-004)
- [ ] Nine core `REQUIRED` rows present with fix text; mutation of any one exits 1 (REQ-LINT-005)
- [ ] Remaining `REQUIRED` rows present; lint exits 0 on the implemented skill set (REQ-LINT-006)
- [ ] Marker-4 prose moved to `references/v4-workstreams.md` with stubs, `research_id` guard and superseding Q-IMPL; `SKILL.md` under 400 lines; lint exits 0 (REQ-LINT-007; bound amended 2026-09-19 by REQ-LINT-HARNESSP5-002)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed
- [ ] `python3 plugins/sdd/tools/skill-lint.py` exits 0 and its summary line matches `OK: N file(s) clean` with no warning clause (the linter omits the count when there are none, so a `0 warning(s)` expectation is unsatisfiable and must not be restored); `python3 tools/sdd-skill-lint.py | grep -c '\[size\]'` prints 0; `wc -l skills/*/SKILL.md` shows every file < 400; every new `references/*.md` is linked from its stub and resolves; every `REQUIRED` row, the `VERSION_GATED_SKILLS` `docs/.sdd-version` mention and the `[template-drift]` fences stay satisfied (REQ-LINT-HARNESSP5-001)
- [ ] REQ-LINT-HARNESSP5-002's file-wide grep for the two legacy baseline figures (the two-file warn set and the four-hundred-fifty bound) returns nothing in this spec; the R7/R8 `reproduce:` commands print 0 and a number < 400; `docs/ws/harness-p5/verification.md` `## Post-cycle Fixes` records both reds closed (REQ-LINT-HARNESSP5-002)
- [ ] §`[template-drift]` states the absent-side behaviour (warn, never fail) and the rendered finding order (tag after the location); Q-IMPL-HARNESSP4-008 carries its fold-in status note and its body is unchanged (REQ-QIMPL-HARNESSP5-001, owned by `deviation-protocol.md`)
- [ ] `[template-drift]` rule present with the four-row pair table; the shipped skill set exits 0; changing one character inside the RED TEAM `RETURN:` block of `dispatch-templates.md` exits 1 with a `[template-drift]` line naming `adversarial-verify.md` and the fix; `--self-test`'s mutation loop covers it; REQ-HARN-HARNESSP4-007's edit is made with the rule active and leaves exit 0 (REQ-LINT-HARNESSP4-001)
- [ ] `REQUIRED` rows for `PLAN:` (producer `references/loop-control.md` §6, consumer `SKILL.md` §The gate) and for the `GIT_STATE` finding name (producer `references/write-scope.md` §5, consumer `SKILL.md` §The gate); `python3 tools/sdd-skill-lint.py` exits 0 on the corpus as it stands, and exits non-zero naming the respective row when the guarded line is removed from any one of those three files (REQ-LINT-HARNESSP6-001)
- [ ] `REQUIRED` row pair for `CONVERGENCE:` (producer `references/loop-control.md` §5 item 6c, consumer `SKILL.md` §The gate); lint exits 0 once the token ships and non-zero naming the respective row when it is removed from either file (REQ-LINT-HARNESSP6-003)
- [ ] `--self-test`'s mutation loop covers all six new rows and asserts the new `len(REQUIRED)` total exactly (REQ-LINT-HARNESSP6-001, REQ-LINT-HARNESSP6-003)
- [ ] REQ-LINT-007 in `docs/requirements/integration/skill-lint.md` carries a bracketed dated `[Updated: 2026-09-20 …]` note naming REQ-LINT-HARNESSP5-001 as the authorising requirement for the moved sections; the id, its number and its original text are unchanged; a reader of the two requirements in sequence finds no contradiction; the findings of `tools/sdd-skill-lint.py` and `tools/sdd-gc.py --report` on that file are unchanged (REQ-LINT-HARNESSP6-002)
- [ ] `REQUIRED` row for `COMMIT: COMPLETE | INCOMPLETE` in `loop-control.md` and `SKILL.md`; removing either line exits 1 with the row's fix (pointing at `write-scope.md` §7); a file containing only `SCOPE: CLEAN` does not satisfy it; `--self-test` covers it; shipped skill set exits 0 (REQ-LINT-HARNESSP4-002)

**Pipeline-observability (2026-09-22, skill lint)**

- [ ] `python3 plugins/sdd/tools/skill-lint.py` exits 0 on this tree; in a temp
  copy with a `.md` path followed by a colon and a line number (the anchor
  form) placed on a visible line of one `SKILL.md` the linter exits non-zero
  with the phrase finding naming that file; with the same anchor placed
  **inside backticks** on a visible line it likewise exits non-zero naming
  that file (the span discipline is what this case decides); with the same
  text inside a fenced block it exits 0; the same anchor form placed in a
  `.py` file under `plugins/sdd/tools/` in the temp copy raises no finding
  from this row (REQ-LINT-PIPELINEOBSERVABILITY-001).
- [ ] `python3 plugins/sdd/tools/skill-lint.py --self-test` exits 0; its
  pinned `FORBIDDEN` count equals the row count after the addition and its
  pinned `REQUIRED` count equals the row count after the fifteen are added;
  in a temp copy with any one of the fifteen markers removed from its file
  the linter exits non-zero with that row's `fix` string; for row p13 the
  check is run once per producer (REQ-LINT-PIPELINEOBSERVABILITY-001; the
  fourteen owning requirements).

## Edge Cases

- **Marker present only inside a code fence**: `REQUIRED` rows count raw
  occurrences today (e.g. `{qimpl_block}` lives in a fence) — keep that
  behavior; the template rows above intentionally match fenced text.
- **Backtick path with a trailing period or colon** (`` `references/x.md`. ``):
  strip punctuation outside the backticks; the regex targets the quoted span
  only.
- **Backtick path that is a glob** (`` `references/*.md` ``): skip — only
  literal filenames are resolved.
- **`docs/spec/` mention in a project without `docs/spec/`** (the linter run
  on a consumer repo — its **corpus root** is the invocation cwd by default,
  its suite root the plugin root holding the script, `two-root-linter.md` §2):
  warn, never fail — the linter must not
  assume this repo's layout (existing audit F11 principle). Scoped to the
  **ungated** set, with exceptions `check_retired_prefix` and `TEMPLATE_PAIRS`
  — §Two-Root Amendment.
- **SKILL.md exactly 400 lines**: no warn (thresholds are strict `>`).
- **Producer present, consumer removed**: the pair row for the consumer fails
  alone; the fix string names the counterpart file.

## Cross-Spec Consistency (XSPEC)

- Python identifiers named here (`flag`, `check_size`, `check_links`, `run`,
  `SIZE_WARN_LINES`, `SIZE_FAIL_LINES`, `REQUIRED`, `FORBIDDEN`) match
  `tools/sdd-skill-lint.py`'s existing names where they exist; new names are
  introduced only here — no duplicate type definitions across specs.
- Row patterns match the literal tokens defined in
  `harness-return-contract.md` (`VERDICT: APPROVE | APPROVE_WITH_FIXES |
  REJECT`, `status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED`,
  `RETURN:`, `{repair_packet}`), `harness-chunk-verifier.md`
  (`CHUNK_VERDICT: PASS | FAIL`), `harness-write-scope.md` (`Write scope:`),
  `harness-loop-control.md` (`Budget:`, `-replan-`, `oscillation`,
  `checkpoint`) — consistent.
- `orchestration.md` REQ-ORCH-019 (~1000 lines, templates in `references/`) is
  the fail threshold and the precedent for procedure text in `references/` —
  consistent.
- `ws-orchestration.md` Q-IMPL-016 is superseded by appending, per
  `deviation-protocol.md` §Numbering supersession rule — consistent.
- `review.md`: the size check does not touch `sdd-review`'s
  layout-independence (F11, **ungated set only**; exceptions
  `check_retired_prefix` and `TEMPLATE_PAIRS` — §Two-Root Amendment) —
  `docs/spec/` mentions are warn-only.
- **No unresolved contradictions.**

**harness-p5 pass (2026-09-19).** No extractable type definitions in this spec
(the two Python constants are module scalars, not types). `SIZE_WARN_LINES` /
`SIZE_FAIL_LINES` keep their single definition here; the "under 400" bound is
now stated once in §Size Warn-Clean Baseline and referenced from §SKILL.md Size
Check and §Marker-4 Prose Move. `telemetry.md` §Moved Sections owns the spec
split (REQ-LINT-HARNESSP5-003) and names this spec only as the domain owner;
`deviation-protocol.md` §Fold-In Status Note defines the fold-in status-note
device this spec's Q-IMPL-HARNESSP4-008 note uses. No unresolved
contradictions.

## Open Questions

1. **`Budget:` minimum count in `dispatch-templates.md`.** Default 3 (pipeline,
   review, verifier). If the verifier template is placed in a separate
   references file during implementation, the row splits accordingly and the
   pair contract in `harness-chunk-verifier.md` must be re-pointed.
2. **`checkpoint` as the REQ-HARN-008 marker word.** Default: the literal word
   `checkpoint`; a more specific phrase (`circuit-break checkpoint`) may be
   used if the implemented skill text adopts it consistently in both files.

## Implementation Questions

### Q-IMPL-022: `suite_rules` constructor flag for end-to-end fixtures
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Self-Test Extension — "a warn-only fixture exits 0 with `1 warning(s)`"
**Decision**: `Linter(root, suite_rules: bool = True)`; when False, `check_required()` skips the repo-specific REQUIRED / VERSION_GATED_SKILLS / V4_CONTRACT_SKILLS rows so temp fixtures can drive `run()` (and its summary line) end to end. Default behavior and the CLI are unchanged.
**Rationale**: `run()` unconditionally checks the real suite's contract rows, which would fail with "file missing entirely" on any temp fixture; the spec asks for the fixture's exit code and summary, which only `run()` produces.
**Date**: 2026-09-17 (Chunk 0)

### Q-IMPL-023: FAIL summary counts and warning suffix
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Severity Tier summary block
**Decision**: `FAIL: N finding(s), K warning(s)` always prints the warning count (K may be 0); N counts fail-severity findings only. `OK:` omits the suffix when K = 0. The old `across M file(s)` tail is dropped.
**Rationale**: the spec shows exactly one FAIL variant; keeping it fixed-shape makes it greppable, and counting fails separately from warnings matches "exits 1 iff any fail".
**Date**: 2026-09-17 (Chunk 0)

### Q-IMPL-024: backtick path rule tag and placeholder skipping
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`references/` Path Resolution, Edge Cases (globs)
**Decision**: backtick-path findings use the rule tag `[path]` (Markdown links keep `[link]`). Spans containing `*`, `<`, `>`, `{`, `}` or whitespace are treated as non-literal (globs/placeholders such as `references/<file>`) and skipped. `docs/spec/` spans must end in `.md` to be resolved. REQUIRED rows changed from tuples to dicts (`file`/`pattern`/`min`/`reason`/`fix`, optional `severity`) to carry the fix field — internal shape only.
**Rationale**: the spec names the glob case but skill prose also uses `<placeholder>` paths, which would otherwise be false failures; a distinct tag keeps link vs. backtick findings distinguishable.
**Date**: 2026-09-17 (Chunk 0)

### Q-IMPL-073: a fourth references file (`loop-control.md`) is needed for the size target
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Marker-4 Prose Move — the size target as it then read (607 − ~160 moved; the bound was amended to under 400 on 2026-09-19, REQ-LINT-HARNESSP5-002)
**Decision**: the move table listed only marker-4 prose; Chunks 2–4 added ~270 lines of loop-control procedure that no reference held, leaving `SKILL.md` at 720 after the move and dedup. A minor replan adds `skills/sdd-orchestrate/references/loop-control.md`; `SKILL.md` keeps marker stubs so REQUIRED rows a/b/d2/e2 still target it. The lint file count becomes 17.
**Rationale**: the spec's arithmetic predates the loop-control prose; the progressive-disclosure goal is served by one more reference, not by relaxing the target.
**Date**: 2026-09-17 (Chunk 5 replan)

### Q-IMPL-084: baseline warn set is three after v5 (cross-reference)
**Tier**: 2 (spec ambiguity)
**Spec reference**: §SKILL.md Size Check — REQ-LINT-003 acceptance names the baseline warn set as exactly {`sdd-orchestrate`, `sdd-migrate`}
**Decision**: after this cycle the live warn set is {`sdd-orchestrate` 469, `sdd-migrate` 464, `sdd-implement` 525}; the third is accepted via Q-IMPL-083 in `harness-loop-control.md` (the `references/` split is **declined**, not queued — see `harness-loop-control.md` Q-IMPL-083). The acceptance snapshot is historical, not a ceiling.
**Rationale**: a reader of this spec needs the pointer; the requirement text never fixed the count.
**Date**: 2026-09-17 (verify-stage review m4)

**Status**: `[resolved by REQ-SKILL-HARNESSP2-007]` — `skills/sdd-implement/SKILL.md` split into `references/stuck-detection.md` and `references/leaf-return.md` (harness-p2 Chunk 1).

### Q-IMPL-HARNESSP2-006: new REQUIRED rows, the FORBIDDEN `\.sdd/` row and the `allow_files` field
**Tier**: 2 (spec ambiguity)
**Spec reference**: §REQUIRED Rows — Core Contracts (row d2), §Self-Test Extension
**Decision**: REQ-LINT-HARNESSP2-001/-002 are specified in `adversarial-verify.md` §Skill and Lint Changes (rows a1/a2 for `RED_VERDICT:`, and the d2 pattern change to `(?<!CHUNK_)(?<!RED_)VERDICT:`), `arbitrated-handoff.md` §Skill and Lint Changes (rows b for `REVIEW: CONTRADICTION` and c for the Material `affects` line) and `telemetry.md` §Lint Guard (the `FORBIDDEN` `\.sdd/` row with a new file-granular `allow_files` field, raw-text scan). `--self-test` §7's mutation loop covers the four new REQUIRED rows (`len(REQUIRED) >= 32`); the size-warn baseline of Q-IMPL-084 returns to two after `dispatch-snapshot-base.md`'s implement split.
**Rationale**: Rule-table rows are owned by the spec that defines the token they guard.
**Date**: 2026-09-17 (harness-p2 specs stage)

### Q-IMPL-HARNESSP4-008: `[template-drift]` when a pair side is absent, and the finding's rendered order
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`[template-drift]` — Fenced Leaf Bodies Restated in Specs Stay Byte-Identical; §Edge Cases ("docs/spec/ mention in a project without docs/spec/", "Producer present, consumer removed")
**Decision**: the pair table is `TEMPLATE_PAIRS` (four rows, each carrying the one `fix` string) with the source of record as the constant `TEMPLATE_SOURCE`; the check runs with the other suite rows only (`suite_rules=True`). A restating spec file absent from the linted **corpus root** (the CLI positional, defaulting to the invocation cwd — `two-root-linter.md` §2; read under that default, not under the retired script-location one) **warns** (never fails — a consumer repo has no `docs/spec/`, the F11 principle — **ungated set only**; exceptions `check_retired_prefix` and `TEMPLATE_PAIRS`, §Two-Root Amendment); a present spec that has lost its anchored fence, or a source of record that has lost its anchored fence while the spec still restates it, **fails** alone with the counterpart named in the message. Anchors match by `startswith` on the fence's first line (the RED TEAM return-contract fence's first line carries a trailing `# one heading per spec examined` comment). The finding renders through the linter's common `flag()` shape — `<spec>:<line>: [template-drift] fenced body diverges from dispatch-templates.md L<n>` — the rule tag after the location, as every other rule renders; `<line>` is the restating fence's opening line in the spec.
**Rationale**: the spec fixes the message, the fix string and the severity but not the absent-side behaviour or the tag position; reusing `flag()` keeps the "no finding without a fix" signature guarantee and the self-test's fix assertion for this rule.
**Date**: 2026-09-19 (harness-p4 Chunk 6)
**Status**: `[folded into §\`[template-drift]\` — Fenced Leaf Bodies Restated in Specs Stay Byte-Identical, 2026-09-19]` (REQ-QIMPL-HARNESSP5-001) — the entry body is unchanged; the section carries the decision as Approved text.

## Two-Root Amendment (2026-09-21, REQ-PKG-PACKAGING-005)

[Changed 2026-09-21: the suite moves to `plugins/sdd/` and the linter takes two
roots — `two-root-linter.md` carries that design. Two claims stated in this
spec are re-scoped here, and the two restatements of the same claim in the
linter's own source are re-scoped with them; nothing else changes.]

**The amended F11 target.** What the linter asserts about a **consumer's**
corpus is the **ungated** set — `FORBIDDEN`'s rows, frontmatter, links, size
and drift phrases — which keeps resolving against the corpus root and failing
loudly there; the suite-gated rows assert the integrity of the **installed
suite** and do assume this suite's layout, by intent. The F11 sentence is
re-scoped, not deleted. Exactly two exceptions exist and must be named wherever
the enumeration is — **including the linter's own source**, which
REQ-PKG-PACKAGING-005 names by hand ("the linter's own docstring or rule-table
comment"). Two such restatements exist today and are **in-scope edits for the
implement stage**, not clean-as-found text: `tools/skill-lint.py` (post-move
`plugins/sdd/tools/skill-lint.py`) at the `check_retired_prefix` rule row's
`reason` string, `"review must not hardcode this repo's layout (audit F11)"`,
and in `check_template_drift()`'s docstring, `"a consumer repo linted via
REPO_ROOT has no docs/spec/ — the F11 principle"`. The exceptions being (i)
*ungated but suite-bound* — `check_retired_prefix()`
has no `suite_rules` guard yet polices this suite's own retired filename
prefix; (ii) *gated but corpus-bound* — `TEMPLATE_PAIRS`'s `spec` side keys on
`docs/spec/**`, which stays on the corpus root. Outside those two, *ungated*
and *consumer-facing* coincide.

**The documented root default.** The positional argument's help string no
longer reads "repo containing this script": the corpus root defaults to the
**invocation cwd**, the suite root to the script's own plugin root
(`two-root-linter.md` §2). Every `REPO_ROOT` sentence above is read under that
default — a consumer run is one whose corpus root is the consumer's cwd. No
text here may claim the root defaults to the script's own repository.

**Verification — the F11 grep, made decidable.** The four spellings in this
file ("(the F11 principle)", "existing audit F11 principle",
"layout-independence (F11)", and the Q-IMPL restatement) share no line-oriented
substring, so the check is anchored on the token: take every match of `grep
-rnE '\bF11\b'` over `docs/spec/` (corpus root) and `plugins/sdd/skills/`,
`plugins/sdd/tools/` (suite root), and require of each match's enclosing
blank-line-delimited block (a) that it contain the literal `ungated`, and (b)
where the block **enumerates** the ungated set — detected mechanically by its
containing `FORBIDDEN` — that it also contain both exception tokens
`check_retired_prefix` and `TEMPLATE_PAIRS`. Zero blocks may fail either
conjunct and the match count is derived at run time. The scan is a short
run-time script over the greps' output, not one grep expression; no residue is
left reviewer-checkable (REQ-PKG-PACKAGING-005).

Two readings the scan must pin, because prose blocks are not the only shape it
meets:

- **A source site is not blank-line-delimited.** In `skill-lint.py` the
  `(audit F11)` match sits in a `reason` string inside a dict literal in the
  `FORBIDDEN` table — the `check_retired_prefix` row — where a blank-line block
  would run to the table's edges; the other match sits in
  `check_template_drift()`'s docstring, which is where `TEMPLATE_PAIRS`
  restates the rule. The block for a `.py` match is therefore the **enclosing
  syntactic unit** — the single dict literal for a table row, the docstring for
  a docstring — not a blank-line run, and it is inside that unit that the
  re-scoped `ungated` wording must land. Conjunct (b)'s trigger is read on the
  block so computed, so a one-row dict literal does not drag the whole table
  in.
- **`F11` is also an unrelated scenario id.** `scope-check-selftest.py` labels
  write-scope self-test scenarios `F11`; those matches are not the audit
  principle, say nothing about the `ungated` set, and are **excluded by path** —
  the exclusion stated here so the scan is decidable rather than discovered
  failing at implement time.

**Current status, stated honestly.** The scan run over `docs/spec/` today
reports zero failing blocks; run over the suite source it reports **two**
failing blocks — the two sites named above, neither of which contains
`ungated`. Making them pass is the REQ-PKG-PACKAGING-005 implement task, and
this criterion is discharged only when the scan is clean over **both** sides.

## Consumer-Geometry Amendment (2026-09-21, REQ-PKG-CONSUMERGEOMETRY-003, -004)

The linter's two-root behaviour under a **disjoint** suite root is specified in
`two-root-linter.md` §Consumer-Geometry Amendment — the `--suite-root` surface
(§CG-2), the corpus-root derivation and its three precedence tiers (§CG-3), the
`GEOMETRY:` token and the `— NOTHING SWEPT` suffix (§CG-6). This section records
only what touches **this** spec's own text.

### The summary-line pins: three sites here, not two

REQ-PKG-CONSUMERGEOMETRY-004's interaction note names `:427` and `:452` in this
file. A run-time grep finds a **third**, at `:127`, in §Size Warn-Clean Baseline.

**Line numbers cited in this section, reconciled once.** Those three are
pre-amendment. Appending this section added two lines to the frontmatter's
`requires:` list, so all three have shifted by **+2**: the §Size Warn-Clean
Baseline pin is now `:129`, and the two §Verification pins are now `:429` and
`:454`. **The content, not the number, identifies each site** — all three are
`OK: N file(s) clean` pins with no warning clause, and the criterion below is
stated against that string so it stays decidable after any further shift. The
requirements-side twin, `docs/requirements/integration/skill-lint.md:276`, is in
another file and is unshifted.

The `— NOTHING SWEPT` suffix is **additive and conditional** — appended only when
`len(skill_files()) == 0` — and `N` is non-zero on this corpus, so none of the
four pins is expected to need amendment. The exposure is nonetheless real: an
**end-anchored** match on that line would break on the zero-sweep path and on the
`FAIL:` path. The implement stage **confirms** each of the four is a prefix or
substring match rather than an end-anchored one, recorded as an observation with
its command; amending any that turns out to be end-anchored is in scope under
REQ-PKG-CONSUMERGEOMETRY-004 rather than a surprise at the gate.
REQ-LINT-HARNESSP5-001's "no `0 warning(s)` expectation" rule is untouched by
either the suffix or this check.

**One of the three pins also names a path that exists under neither spelling.**
The §Verification checklist pin invokes `python3 tools/sdd-skill-lint.py` — the
pre-rename basename at the pre-move root, so it resolves neither before the move
(the file is `tools/skill-lint.py` after REQ-NAME-MARKETPLACE-003) nor after it
(the suite root is `plugins/sdd/tools/`). The implement stage is already reading
that exact line for the end-anchoring check, so the dead path is corrected to
`python3 plugins/sdd/tools/skill-lint.py` **in the same read**, rather than
scheduled as a separate sweep. This is a spelling repair on a path, not a change
to what the criterion asserts, and it is in scope under
REQ-PKG-CONSUMERGEOMETRY-004 for the same reason the end-anchoring confirmation
is. Other `tools/sdd-skill-lint.py` occurrences elsewhere in this spec are **not**
in scope here — they are pre-existing and belong to whatever cycle next touches
them.

### The `GEOMETRY:` token is not a finding

The token is emitted on its own line immediately before the summary, including
on runs with findings. It is not a finding, carries no severity, is not counted
in `N`, and does not participate in §Finding Shape and Remediation. Its three
values are `nested`, `equal` and `disjoint`; the spelling
`nested | equal | disjoint` appears in no output.

**"Every run" is scoped to runs that print a summary.** The token is emitted
**iff** the run prints an `OK:` or `FAIL:` summary line, immediately before it —
one token per summary, never two, never one without the other. That excludes
`--self-test`, whose `SELF-TEST OK:` / `SELF-TEST FAIL:` banner is not a corpus
summary and which prints none; a self-test *case* asserts on the token by
constructing a sweep and reading that sweep's output, not by grepping the
self-test's own stdout. Whether `--print-population` prints a summary is settled
by Q-IMPL-PACKAGING-003, not restated here: the rule follows the summary
wherever it goes, so no second statement can drift from it. Without this scoping
a fixture asserting "exactly one `GEOMETRY:` line" over a self-test run would be
undecidable.

### The amended F11 target is unchanged by this delta

§Two-Root Amendment's re-scoping of the F11 sentence to the **ungated** set, with
its two named exceptions, stands exactly as REQ-PKG-PACKAGING-005 left it. The
`consumer-geometry` delta rebinds **no** rule table: the 56 suite-gated rows keep
the suite-root binding of `two-root-linter.md` §3, and C12.1 passes unmodified.
What changes is signalling — which root those rows were evaluated against is now
printed — not scope.

### Consumer-Geometry Acceptance Criteria

- [ ] The four summary-line pins — the three `OK: N file(s) clean` pins in this
  file (`:127`, `:427`, `:452` pre-amendment; `:129`, `:429`, `:454` after it, the
  string identifying them either way) and
  `docs/requirements/integration/skill-lint.md:276` — are each read at implement
  time and confirmed not end-anchored, recorded as an observation with its
  command; any that is end-anchored is amended. **In the same read**, the
  §Verification checklist pin's dead `python3 tools/sdd-skill-lint.py`
  invocation is corrected to `python3 plugins/sdd/tools/skill-lint.py`, asserted
  by resolving the named path at run time — it resolves under neither the pre-
  nor the post-move spelling today, which is what makes that half red before the
  change. Leaving an end-anchored pin in place makes the zero-sweep and `FAIL:`
  runs of REQ-PKG-CONSUMERGEOMETRY-004 acceptances 1 and 4 red against it; a
  still-unresolvable path makes the other half red
  (REQ-PKG-CONSUMERGEOMETRY-004 interaction note, extended here from two named
  sites to three).
- [ ] A run over this corpus emits **exactly one** `GEOMETRY:` line, on its own
  line, immediately before the summary, and that line contributes to no finding
  count. The no-contribution half is asserted **by mutation**, the shape the rest
  of the delta uses: on a temporary copy with the emission removed, the finding
  count and the `N` of the summary line are unchanged from the unmutated run —
  "without the token present" has no construction once the token lands, so the
  mutation supplies one. A run of `--self-test`, which prints no summary, emits
  **no** token. Emitting the token inside a finding, counting it in `N`, emitting
  it only on the clean path, or emitting it from a run with no summary makes this
  red (REQ-PKG-CONSUMERGEOMETRY-004 acceptance 2 and its negative).
- [ ] `grep -n 'no-suite-rules' plugins/sdd/tools/skill-lint.py` is still empty
  and every `suite_rules=False` construction site is still inside the self-test —
  REQ-PKG-PACKAGING-003 leg (i), which this delta preserves while superseding its
  `--suite-root` deferral. Adding a disable switch alongside the new surface makes
  this red (REQ-PKG-CONSUMERGEOMETRY-003 acceptance 4, second half).


## Pipeline-Observability Amendment (2026-09-22, REQ-LINT-PIPELINEOBSERVABILITY-001; the fifteen `REQUIRED` rows this cycle adds)

[Added 2026-09-22, workstream `pipeline-observability` —
RS-PIPELINEOBSERVABILITY-001 §Q5 scope decision, §Mechanical pin R3, R4, R6,
R8, R10, R12, R14; Q-REQ-PO-S. Two rows landed before this stage with the V3
routing (`proceeds **without re-review**` on `skills/orchestrate/SKILL.md`,
`GROWTH: ` on `skills/orchestrate/references/loop-control.md`) and one `FORBIDDEN` phrase (`then
re-run the review for this stage`); they are recorded here as in force and are
**not** counted among the rows below.]

**Where the contract lives** (REQ-REQ-PIPELINEOBSERVABILITY-001 (b), 2026-09-22): this section is the record of *why* and states no contract of its own; the contract is in the sections of record named here, each edited in place under a `[Updated: 2026-09-22]` marker, and its acceptance criteria sit in this spec's own Acceptance Criteria section under the same date. §`FORBIDDEN` Row — `literal-anchor` carries the drift phrase and its source-line discipline (REQ-LINT-PIPELINEOBSERVABILITY-001); §`REQUIRED` Rows — Pipeline-Observability carries the fifteen rows this cycle adds (fourteen at Chunk 1, p15 at the implement-stage fix); §Self-Test Extension's exact totals move with them. Left consistent and not reopened: §Finding Shape, §Severity Tier, §Size Check and baseline, §`references/` Path Resolution, §`[template-drift]`, the `COMMIT:`, `PLAN:`/`GIT_STATE` and `CONVERGENCE:` rows (the `GIT_STATE` pair is unchanged — one row is added beside it), §Two-Root Amendment and §Consumer-Geometry Amendment.

**Why the linter and not gc for the shipped tree**: the snapshot-comparand class REQ-GC-PIPELINEOBSERVABILITY-001 warns on in the binding corpus is kept out of the shipped skill, reference and agent text through the mechanism that already sweeps that tree, not by widening gc's docs scope (RS-PIPELINEOBSERVABILITY-001 §Q5). **Why spans are read, not blanked** (requirements review round 5 M3): the same discipline as gc's rule, so an anchor in backticks is a finding on both sides. **Why p13 names both producers** (REQ-REV-PIPELINEOBSERVABILITY-001 (vi)): the grammar is bound on the skill template and the agent body alike, and one row with two files fails naming whichever lost the line.

## Pipeline-Observability Implementation Questions

### Q-IMPL-PIPELINEOBSERVABILITY-002: the per-row visible-lines flag is named `visible_only`
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`FORBIDDEN` Row — `literal-anchor` — "a per-row flag — name chosen at implementation (Q-SPEC-PO-E) — that restricts its scan to unfenced lines"
**Decision**: the row carries `"visible_only": True`. `forbidden_findings()` honours it with the same ```` ``` ```` toggle the ordinal check uses (a line whose stripped text opens with a fence flips the state and is itself skipped); nothing else about the line is altered, so a backticked span on a visible line is still read and an inline-code anchor is a finding. Rows without the key scan raw lines, fence-inclusive, as before. The self-test case `literal_anchor_visible_only` reads the shipped row from the table (the one row carrying the key) and runs the four cases the section names — visible, backticked, fenced, `.py` under `tools/`.
**Rationale**: the name says what the flag does and nothing about why (the "why" is the row's `reason`); a boolean rather than a mode string keeps the default — absent key, old behaviour — a one-line `dict.get`.

### Q-IMPL-PIPELINEOBSERVABILITY-011: the operator guide is refreshed at the implement-stage fix, and row p15 pins it
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`REQUIRED` Rows — Pipeline-Observability; `review.md` §Report Format (the three predicates and the `Approve with fixes` routing)
**Date**: 2026-09-22 (pipeline-observability, implement-stage fix, review round 3 M1)
**Decision**: `plugins/sdd/skills/orchestrate/USAGE.md` §7b is rewritten to the landed vocabulary — routing by verdict (`APPROVE_WITH_FIXES` proceeds without re-review unless the operator opts in; `REJECT` re-reviews), `iteration N` as `reject_run` counting consecutive consumed `REJECT`s, the `GROWTH:` line's position, the `post-manual` review after a manual intervention, and the voided-verdict pause with `restore │ accept (note) │ stop` then `redo │ stop` — mirroring `orchestrate/SKILL.md` §The gate and `references/loop-control.md` §1b/§2/§2b/§5 and inventing no rule. This is an **implement-stage scope addition**: no plan task named the guide (the plan's chunks bind skill, reference and agent text; the operator guide was left to drift for a stage). One `REQUIRED` row, p15 on `skills/orchestrate/USAGE.md` pinning `proceeds without re-review`, is added so the guide cannot silently revert; §6 of `two-root-linter.md` moves to `REQUIRED=57` in the same change (three-way equality).
**Rationale**: the guide is the human-facing statement of the same gate; a reader who follows it would expect a re-review the driver no longer runs. A row on the guide is the cheapest binding that fails on reversion — the rule of this cycle — and the phrase chosen is the one the skill's own row already pins on `SKILL.md`, so the two surfaces fail together.
