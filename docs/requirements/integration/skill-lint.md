---
domain: LINT
last_updated: 2026-09-20
status: Approved
research_refs: [RS-008, RS-HARNESSP4-001, RS-HARNESSP5-001]
---

# Requirements: Skill Lint (`tools/sdd-skill-lint.py`)

## Overview

Changes to `tools/sdd-skill-lint.py` so it mechanically enforces the new
harness-hardening contracts (HARN domain) and acts as a teacher rather than a
gate — every finding says how to fix it (catalogue G16), and the entry-point
SKILL.md files stay small enough to read as a table of contents (catalogue C10).
RS-008 Q4 established that the linter has five check classes (structure,
forbidden phrases, required contract markers, ordinals, relative Markdown links)
driven by two rule tables (`FORBIDDEN`, `REQUIRED`); every "marker present"
contract is checkable now via a `REQUIRED` row, while a soft size limit,
backtick `references/` path resolution and remediation text need three small
code changes. The linter had no warning tier — every finding exits 1.

Baseline (2026-09-17, `wc -l`): `sdd-orchestrate/SKILL.md` 607, `sdd-migrate`
464, `sdd-requirements` 354, `sdd-implement` 351, six others 187–276; total 3253,
median ≈ 265. `references/fan-out.md` 340, `references/dispatch-templates.md` 116.

## Requirements

### REQ-LINT-001: Every finding carries remediation text
Every lint finding must include a `fix:` string stating how to remedy it. The
`FORBIDDEN` and `REQUIRED` rule tables must gain a `fix` field alongside their
existing `reason`, `flag()` must accept and print it, and the structure, ordinal
and link checks (which have no rule table) must emit fixed remediation strings.
A finding without remediation text is itself a lint defect (the self-test must
assert every emitted finding has a non-empty `fix`). (see RS-008 Q4; catalogue
G16)
**Acceptance**: running the linter against its own bad-fixture self-test prints
`fix:` on every finding; no code path calls `flag()` without a fix argument.
[Priority: must]

### REQ-LINT-002: Warn severity tier
The linter must support two severities: **fail** (current behavior, exit 1) and
**warn** (printed with a `WARN` prefix, does not affect the exit code). A run
with only warnings must exit 0 and print the warning count in its summary line
(e.g. `OK: 13 file(s) clean, 2 warning(s)`). Rule-table rows and check methods
must be able to declare their severity; existing rows default to fail. (see
RS-008 Q4)
**Acceptance**: a fixture that triggers only the size soft limit (REQ-LINT-003)
exits 0 and prints one `WARN`; a fixture with one fail finding still exits 1.
[Priority: must]

### REQ-LINT-003: SKILL.md size check (400 warn / 1000 fail)
The linter must check the line count of every `skills/*/SKILL.md`: over **400**
lines → warn ("entry point should read as a table of contents; move detail to
`references/`"); over **1000** lines → fail (the project's existing ~1000-line
guideline, REQ-ORCH-019). Both thresholds must be module-level constants with
the defaults from RS-008 Q4 (operator decision, Q-REQ-B in `index.md`).
`references/*.md` and `USAGE.md` are not size-checked. (see RS-008 Q4 size table)
**Acceptance**: at the 2026-09-17 baseline the check warns on exactly
`sdd-orchestrate` (607) and `sdd-migrate` (464) and fails on none; after the
REQ-LINT-007 move `sdd-orchestrate` is ≤ ~450 lines (still a warn unless a
further pass is made — the warn is acceptable, the fail is not).
[Priority: must]
[Updated: 2026-09-19, RS-HARNESSP5-001] The acceptance baseline above is stale
(`sdd-implement/SKILL.md` was already 434 lines at p4's base `0182bf2`; p4 red
R7 accepted). The harness-p5 target is **warn-clean**: after
REQ-LINT-HARNESSP5-001 the check warns on **none** and fails on none — see
REQ-LINT-HARNESSP5-002 for the `skill-lint-v5.md` amendment.

### REQ-LINT-004: `references/` backtick paths and relative links resolve
`check_links()` must, in addition to resolving `[text](relative.md)` Markdown
links outside code fences, resolve backtick-quoted relative paths of the form
`` `references/<file>` `` (and `` `skills/<skill>/references/<file>` ``) against
the repository, failing on a path that does not exist. `docs/spec/*.md` mentions
may be resolved as a warn. Paths inside fenced code blocks are ignored, as
today. (see RS-008 Q4 contract table)
**Acceptance**: a SKILL.md mentioning `` `references/v4-workstreams.md` `` before
that file exists fails with a fix string; the six existing
`[…](references/…)` links in `sdd-orchestrate/SKILL.md` still resolve.
[Priority: must]

### REQ-LINT-005: REQUIRED marker rows for the core hardening contracts
The `REQUIRED` table must gain rows asserting presence of the following
contracts, each with `reason` and `fix` text: (a) the fix-loop cap in
`skills/sdd-orchestrate/SKILL.md` (pattern matching `iteration N of 3` / "fix-loop
cap", REQ-HARN-001); (b) the replan re-entry cap in the same file (REQ-HARN-002);
(c) a `Budget:` slot in **both** dispatch template files —
`skills/sdd-orchestrate/references/dispatch-templates.md` (pipeline and review
templates, plus the new chunk-verifier template) and
`skills/sdd-orchestrate/references/fan-out.md` (leaf template) — one row per
file, two rows (REQ-HARN-004); (d) the `VERDICT:` token as a
producer/consumer pair — `skills/sdd-review/SKILL.md` and
`skills/sdd-orchestrate/SKILL.md` (REQ-HARN-013), following the existing
`**Depends on**` ↔ fan-out pair pattern; (e) the `CHUNK_VERDICT:` token in the
verifier template and its consumer in `sdd-orchestrate` (REQ-HARN-014); (f) the
`-replan-` filename segment in `skills/sdd-replan/SKILL.md` (REQ-HARN-003). (see
RS-008 Q4 contract table)
Row count: (a) 1 + (b) 1 + (c) 2 + (d) 2 + (e) 2 + (f) 1 = **nine** rows.
**Acceptance**: removing any one of the nine markers from its file makes the lint
exit 1 with that row's fix string; with all present the lint exits 0 (modulo
size warnings).
[Priority: must]

### REQ-LINT-006: REQUIRED marker rows for the remaining hardening contracts
The `REQUIRED` table should also gain rows for: the `RETURN:` block / `status:`
token in the leaf templates (REQ-HARN-009); the `{repair_packet}` slot in
`dispatch-templates.md`'s `{on_fix_only}` block (REQ-HARN-011, mirroring the
existing `{qimpl_block}` row); the `Write scope:` slot in the leaf templates
(REQ-HARN-020); the word "oscillation" in `skills/sdd-implement/SKILL.md`
(REQ-HARN-007); and the checkpoint / blocked-note format in `sdd-implement` and
`sdd-replan` (REQ-HARN-008). Behavioral principles (pruned state, orchestrator
owns routing) are phrase-presence only and are verified by review, not lint.
(see RS-008 Q4 contract table)
**Acceptance**: each listed marker has a `REQUIRED` row with fix text; the lint
exits 0 on the implemented skill set.
[Priority: should]

### REQ-LINT-007: Move marker-4 prose to `references/v4-workstreams.md` with two guards
`skills/sdd-orchestrate/SKILL.md`'s marker-4-only sections must move to
`skills/sdd-orchestrate/references/v4-workstreams.md`, each leaving a stub that
keeps the "behavior UNCHANGED under marker 3" sentence and a link, so a marker-3
reader is never sent to the reference: §Workstream Picker and its three
subsections (~79 lines, ~5-line stub), the §Phase Detection "Workstream & version
gate (v4)" and "Marker-4 gate for done-vs-new-cycle" blocks (~38 lines, one-line
stubs), the §Entry Points "Marker-4 scope" paragraph, the §KICKOFF version-gate
paragraph, and the §Integration anchor / "Marker-4 anchor" paragraphs (which
should point at `references/fan-out.md` §0, where the full contract already
lives). The "Upgrade offer (entry, all markers)" block, the phase table, §The
gate, dispatch contracts, §Isolation Discipline, §Rules and §Orchestrator-Only
Work must **not** move. Two guards are mandatory: (1) the lint `REQUIRED` row
`research_id` ≥ 3 in `SKILL.md` counts one occurrence inside the picker section —
either the stub keeps a `research_id` mention or the row is re-pointed so its
third occurrence is in the new file; (2) Q-IMPL-016 in `docs/spec/
ws-orchestration.md` pins the picker to `SKILL.md` and Q-IMPL entries are
append-only, so a **superseding Q-IMPL entry** must be added (never an edit).
`docs/.sdd-version` must remain mentioned in `SKILL.md` (`VERSION_GATED_SKILLS`
check). (see RS-008 Q4 section table; catalogue C10)
**Acceptance**: `tools/sdd-skill-lint.py` exits 0 after the move; every moved
section has a stub containing "UNCHANGED" (or equivalent marker-3 sentence) and a
resolving link (REQ-LINT-004); `ws-orchestration.md` has a new Q-IMPL entry
citing Q-IMPL-016; `sdd-orchestrate/SKILL.md` after this cycle — the marker-4
move plus the HARN stubs pointing at `references/write-scope.md` and
`references/return-contract.md` — is no larger than ~450 lines.
[Priority: must]
[Updated: 2026-09-19, RS-HARNESSP5-001] The "no larger than ~450 lines" clause
is superseded: `sdd-orchestrate/SKILL.md` was 551 lines at p4 DONE (p4 red R8
accepted); the p5 target for every `SKILL.md` is **under 400** — see
REQ-LINT-HARNESSP5-001 / -002.

<!-- REQ-LINT-HARNESSP2-NNN: workstream-prefixed additions for the harness-p2
     cycle (RS-HARNESSP2-001; marker 4, per docs/spec/ws-ids.md). -->

### REQ-LINT-HARNESSP2-001: REQUIRED rows for the `RED_VERDICT:` pair, the `REVIEW: CONTRADICTION` consumer and the Material `affects` key
The `REQUIRED` table must gain, each with `reason` and `fix` text: (a) the
`RED_VERDICT: BROKEN | HELD` token as a producer/consumer pair — producer in
the red template in `skills/sdd-orchestrate/references/dispatch-templates.md`,
consumer in `skills/sdd-orchestrate/SKILL.md` or `references/return-contract.md`
(REQ-REDB-HARNESSP2-005), following the `CHUNK_VERDICT:` pair pattern; (b) the
`REVIEW: CONTRADICTION` token in `skills/sdd-orchestrate/references/loop-control.md`
with its pointer in `SKILL.md` §The gate (REQ-ARB-HARNESSP2-006) — consumer-only,
the orchestrator both raises and handles it; (c) `affects` on the Material
template line of `skills/sdd-review/SKILL.md` (REQ-ARB-HARNESSP2-008). The
existing review-verdict consumer row's negative look-behind `(?<!CHUNK_)VERDICT:`
must also exclude `RED_` (`(?<!CHUNK_)(?<!RED_)VERDICT:`) so a red token never
satisfies the review consumer row. Row count: (a) 2 + (b) 1 + (c) 1 = **four**
rows plus one regex change; `--self-test` §7's mutation loop must cover them
(`len(REQUIRED) >= 32`). (see RS-HARNESSP2-001 Implications for Design — "two
new tokens need lint pairs")
**Acceptance**: removing `RED_VERDICT:` from the red template, or `REVIEW:
CONTRADICTION` from `loop-control.md`, or `affects` from the Material template
line, each makes the lint exit 1 with that row's fix string; a file containing
only `RED_VERDICT: HELD` does not satisfy the review `VERDICT:` consumer row;
the shipped skill set exits 0.
[Priority: must]

### REQ-LINT-HARNESSP2-002: FORBIDDEN row — telemetry path never read by a skill
The `FORBIDDEN` table must gain a fail-severity row matching `\.sdd/` in every
`skills/*/SKILL.md` and `skills/*/references/*.md` **except** exactly three
locations: the telemetry stub section of `skills/sdd-orchestrate/SKILL.md`,
`skills/sdd-orchestrate/references/telemetry.md`, and
`skills/sdd-orchestrate/references/write-scope.md` — §3 (the third, telemetry-
specific observation of REQ-TELEM-HARNESSP2-005) and §5 (limitation (b)'s
`.sdd/` exception, REQ-HARN-HARNESSP2-001 / REQ-SKILL-HARNESSP2-004) **only**;
the `OUT .sdd/telemetry.jsonl (+k records, leaf write — reverted)` finding
string is defined **once**, in `references/telemetry.md`, and `write-scope.md`
references it rather than restating it (an explicit per-row allowlist of paths
— the linter must gain an `allow` field on `FORBIDDEN` rows if it lacks one;
the row is file-granular, so the §3/§5 restriction is a review check, not a
lint check), with `reason` "telemetry is orchestrator-written and never a
phase-detection or staleness input (REQ-ORCH-014)" and a `fix:` that says to
remove the reference. Fenced code blocks are **not** exempt for this row — a
skill must not even show the path in an example — so the row scans raw text.
(see RS-HARNESSP2-001 Q1 guard (i); REQ-TELEM-HARNESSP2-007)
**Acceptance**: adding `.sdd/telemetry.jsonl` inside a fence in
`skills/sdd-plan/SKILL.md` makes the lint exit 1 with the row's fix; the three
allowlisted locations mentioning the path exit 0; `--self-test` covers the
allowlist. Operator documentation (`skills/sdd-orchestrate/USAGE.md`,
`CLAUDE.md`) is not scanned by this row and may name the path
(REQ-SKILL-HARNESSP2-008).
[Priority: must]

### REQ-LINT-HARNESSP4-001: `[template-drift]` — fenced leaf bodies restated in specs stay byte-identical
`tools/sdd-skill-lint.py` must gain a `[template-drift]` rule that extracts the
fenced bodies of the named pairs — the CHUNK VERIFIER dispatch, verdict rule and
`RETURN:` block of `skills/sdd-orchestrate/references/dispatch-templates.md`
against `docs/spec/harness-chunk-verifier.md`, and the RED TEAM dispatch and
`RETURN:` block against `docs/spec/adversarial-verify.md` — compares their
hashes, and on divergence emits
`[template-drift] <file>:<line>: fenced body diverges from dispatch-templates.md L<n>`
with a `fix:` line naming the source of record (the skill side changes; the
spec side is Approved and stable). The pair list is a table in the linter so a
future restated body is one row. The five bodies are byte-identical today and
nothing keeps them so; the contract is invisible at edit time and a divergence
would first surface as a leaf returning the wrong shape. (workstream
`harness-p4`; see `docs/ws/harness-p3/verification.md` §V8 — verified identical
today, rule recommended; REQ-HARN-HARNESSP3-002 is the contract it guards)
**Acceptance**: the shipped skill set exits 0; changing one character inside
the RED TEAM `RETURN:` block of `dispatch-templates.md` makes the lint exit 1
with a `[template-drift]` line naming `adversarial-verify.md` and the fix;
`--self-test`'s mutation loop covers the rule; REQ-HARN-HARNESSP4-007's edit is
made with the rule active and leaves it at exit 0.
[Priority: must]

### REQ-LINT-HARNESSP4-002: REQUIRED row — `COMMIT: COMPLETE | INCOMPLETE` stated in `loop-control.md` and `SKILL.md`
The `REQUIRED` table must gain one row asserting the `COMMIT:` token family of
REQ-HARN-HARNESSP4-001 is stated in
`skills/sdd-orchestrate/references/loop-control.md` (the §5 order) and in
`skills/sdd-orchestrate/SKILL.md` §The gate, with a pattern that matches
`COMMIT: COMPLETE` / `COMMIT: INCOMPLETE` and does **not** match a file that
only names `SCOPE:` — the same guard the existing `CHUNK_VERDICT:` row already
applies — and with a `fix:` string pointing at `write-scope.md` §7 as the
defining section. (workstream `harness-p4`; see RS-HARNESSP4-001 §Q1 cost table
— code; every new gate token so far has shipped with a lint pair,
REQ-LINT-HARNESSP2-001)
**Acceptance**: removing the `COMMIT:` line from `loop-control.md` §5 or from
`SKILL.md` §The gate makes the lint exit 1 with the row's fix; a file containing
only `SCOPE: CLEAN` does not satisfy the row; `--self-test`'s mutation loop
covers the row; the shipped skill set exits 0.
[Priority: must]

<!-- REQ-LINT-HARNESSP5-NNN: workstream-prefixed additions for the harness-p5
     cycle (RS-HARNESSP5-001; marker 4, per docs/spec/ws-ids.md). The
     docs/spec/telemetry.md split (-003) sits in this domain by the deliverable
     contract — size housekeeping under one owner — not because the lint
     size-checks specs; Q-REQ-P5-G. -->

### REQ-LINT-HARNESSP5-001: every `SKILL.md` is under the 400-line warn threshold
`skills/sdd-orchestrate/SKILL.md` (551), `skills/sdd-migrate/SKILL.md` (464) and
`skills/sdd-implement/SKILL.md` (434) must each be brought **under 400 lines**
by moving detail to `references/*.md` files, each moved section leaving a stub
with the marker-3 "behavior UNCHANGED" sentence where one applies and a
resolving link (REQ-LINT-004), with every `REQUIRED` marker row, the
`VERSION_GATED_SKILLS` `docs/.sdd-version` mention and the `[template-drift]`
fences kept satisfied (a row may be re-pointed to the new file, never dropped).
The size evidence is RS-HARNESSP5-001 §Decided (measured 2026-09-19). Decided
at DISCUSS: the target is lint warn-clean. (workstream `harness-p5`; kickoff
§Scope item 3; p4 red R7/R8)
**Acceptance**: `python3 tools/sdd-skill-lint.py` exits 0 and its summary line
matches `OK: N file(s) clean` with **no** warning clause — the linter appends
`, W warning(s)` only when `W > 0`, so a warn-clean run prints no count at all
and a `0 warning(s)` expectation is unsatisfiable; do not "restore" that
wording; `python3 tools/sdd-skill-lint.py | grep -c '\[size\]'`
prints 0; `wc -l skills/*/SKILL.md` shows every file < 400; every new
`references/*.md` is linked from its stub and resolves.
[Priority: must]

### REQ-LINT-HARNESSP5-002: `skill-lint-v5.md` REQ-LINT-003 / REQ-LINT-007 baselines read "none" and "under 400"
`docs/spec/skill-lint-v5.md`'s restatements of REQ-LINT-003 ("baseline warns on
exactly `sdd-orchestrate` and `sdd-migrate`") and REQ-LINT-007
("`sdd-orchestrate/SKILL.md` ≤ ~450 lines") must be amended so the size
baseline reads **none** (no `[size]` warning on the shipped skill set) and the
`sdd-orchestrate` bound reads **under 400**, matching the `[Updated]` notes on
those two requirements in this file; the p4 accepted reds R7 and R8 close on
this edit. (workstream `harness-p5`; see `docs/ws/harness-p4/verification.md`
§Issues Found → Minor R7, R8 — reproduce: `python3 tools/sdd-skill-lint.py | grep -c '\[size\]'`,
`wc -l skills/sdd-orchestrate/SKILL.md`)
**Acceptance**: `grep -n '450\|exactly .sdd-orchestrate. and .sdd-migrate' docs/spec/skill-lint-v5.md`
returns nothing (file-wide); the R7/R8 `reproduce:` commands
print 0 and a number < 400; `docs/ws/harness-p5/verification.md`
`## Post-cycle Fixes` records both reds closed.
[Priority: must]

### REQ-LINT-HARNESSP5-003: `docs/spec/telemetry.md` (1137 lines) is split with its parsed tables intact
`docs/spec/telemetry.md` must be split into cohesive files under the same
`telemetry` topic (for example `telemetry.md` — schema, writer, lint — and
`telemetry-reader.md` — `summarize`, `--plan`, migration, fixture contract),
such that: the §Record Schema table that `tools/sdd-telemetry.py`
`test_schema_table_agrees` parses stays at the path the tool reads (or the
tool's path constant moves with it in the same change); every
`## Implementation Questions` entry stays with the section it amends
(append-only, never renumbered); every `research_refs`/spec reference from
`docs/requirements/functional/telemetry.md`, the per-ws traceability `Spec`
cells and skill text resolves; no file exceeds ~800 lines. The exact split is
for specs to decide.
[Updated: 2026-09-19 — the original guide read ~600 lines. The split landed at
748 (`telemetry.md`) and 697 (`telemetry-reader.md`) lines and the bound is
amended to **~800 lines per file**, an accepted residual rather than a silent
overrun. Reason: the two remaining cuts both break a contract in half — the
`| Group | Key | Type / domain |` table's three worked examples belong with the
writer rules that produce them, and the reader / lint / fixture contract is one
consumer-side whole. A further split to satisfy a line count would trade
cohesion (the rule the number proxies for) for the number itself. Recorded as
Q-REQ-P5-I in `docs/requirements/index.md` §Q-REQ Resolutions.] (workstream `harness-p5`; kickoff §Scope item 3; the
requirements-side split of `functional/telemetry.md` proposed in `index.md`
§Open Questions (p4) stays deferred — ids are unchanged either way)
**Acceptance**: `wc -l docs/spec/telemetry*.md` shows no file over ~800 lines
(amended bound, above);
`python3 tools/sdd-telemetry.py --self-test` passes `test_schema_table_agrees`;
`python3 tools/sdd-gc.py --report` raises no `qimpl-broken-ref` or broken-link
finding on the split files; `python3 tools/sdd-skill-lint.py` exits 0.
[Priority: should]
