---
domain: LINT
last_updated: 2026-09-22
status: Approved
research_refs: [RS-008, RS-HARNESSP4-001, RS-HARNESSP5-001, RS-HARNESSP6-001, RS-PACKAGING-002, RS-PACKAGING-003]
workstream: harness-p2, packaging
---

# Requirements: Skill Lint (`tools/skill-lint.py`)

## Overview

Changes to `tools/skill-lint.py` so it mechanically enforces the new
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
**Acceptance**: `tools/skill-lint.py` exits 0 after the move; every moved
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
[Updated: 2026-09-20, harness-p6 — REQ-LINT-HARNESSP6-002] The "must **not**
move" list above is **qualified, not amended**. Moving any of those sections out
of `SKILL.md` for size reasons is an **authorised exception** to that list, and
**REQ-LINT-HARNESSP5-001** — which requires every `SKILL.md` to be brought under
400 lines by moving detail into `references/*.md` — is the authorising
requirement; the harness-p5 move of §Isolation Discipline and §Orchestrator-Only
Work into `references/isolation.md` is the instance. The two requirements
conflict textually only: the `no` list scopes those sections out of *this*
marker-4 prose move, it does not pin them to `SKILL.md` forever — see
`docs/spec/skill-lint-v5.md` §Scope of the `no` row for the reconciling reading,
and the moved-section invariants there (stub with the marker-3 sentence,
`REQUIRED` rows re-pointed never dropped, fenced bodies kept paired) continue to
apply. This requirement's id, its number and its original text above are
deliberately left unchanged: amending them in place would break every artifact
that cites REQ-LINT-007 and would erase the record that the two requirements
once disagreed.

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
`tools/skill-lint.py` must gain a `[template-drift]` rule that extracts the
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
**Acceptance**: `python3 tools/skill-lint.py` exits 0 and its summary line
matches `OK: N file(s) clean` with **no** warning clause — the linter appends
`, W warning(s)` only when `W > 0`, so a warn-clean run prints no count at all
and a `0 warning(s)` expectation is unsatisfiable; do not "restore" that
wording; `python3 tools/skill-lint.py | grep -c '\[size\]'`
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
§Issues Found → Minor R7, R8 — reproduce: `python3 tools/skill-lint.py | grep -c '\[size\]'`,
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
`python3 tools/gc.py --report` raises no `qimpl-broken-ref` or broken-link
finding on the split files; `python3 tools/skill-lint.py` exits 0.
[Priority: should]

### REQ-LINT-HARNESSP6-001: REQUIRED row — `PLAN:` stated in `loop-control.md` and `SKILL.md`
`tools/skill-lint.py` must carry a `REQUIRED` row pair for the `PLAN:` gate
token, mirroring the existing pairs for the other gate tokens. `PLAN:` is today
the only gate token with no `REQUIRED` row, so deleting it from
`skills/sdd-orchestrate/references/loop-control.md` §6 is unguarded while the
same deletion of any sibling token fails the lint. One row asserts the producer
(the token's definition in `loop-control.md`) and one the consumer (its mention
in `skills/sdd-orchestrate/SKILL.md` §The gate). (workstream `harness-p6`;
kickoff §Scope item 4, mechanical and decided at DISCUSS; carried from
`docs/ws/harness-p5/verification.md` §Next Steps 4/4 and closed here)
The same row pair must also guard the `GIT_STATE` finding name of
REQ-HARN-HARNESSP6-001. RS-HARNESSP6-001 Q2 recommended it land alongside the
`PLAN:` row so the two share one lint change; it is adopted here rather than
declined, since a `GIT_STATE` line deleted from `write-scope.md` would otherwise
be as unguarded as `PLAN:` is today.
**Acceptance**: `python3 tools/skill-lint.py` exits 0 on the corpus as it
stands; with the `PLAN:` line removed from `loop-control.md` §6 it exits
non-zero naming that `REQUIRED` row, and likewise with the token removed from
`SKILL.md`; and the same holds for the `GIT_STATE` name removed from
`skills/sdd-orchestrate/references/write-scope.md`.
[Priority: must]

### REQ-LINT-HARNESSP6-002: REQ-LINT-007's "must not move" list is qualified for the Chunk 9 rescoping
`docs/requirements/integration/skill-lint.md` REQ-LINT-007's "must not move"
list must be qualified so that it matches the Chunk 9 rescoping that
REQ-LINT-HARNESSP5-001 authorised in the same file. As written the two
requirements read as contradicting each other: the earlier one forbids movement
that the later one requires. The qualification is added as a bracketed dated
`[Updated: …]` note on REQ-LINT-007 naming the authorised exception and its
authorising requirement — the requirement id, its number and its original text
are not changed. (workstream `harness-p6`; kickoff §Scope item 6, mechanical and
decided at DISCUSS; carried from `docs/ws/harness-p5/verification.md` §Next
Steps and closed here)
**Acceptance**: REQ-LINT-007 carries an `[Updated: 2026-09-20 …]` note naming
REQ-LINT-HARNESSP5-001 as the authorising requirement for the moved items; a
reader of the two requirements in sequence finds no contradiction;
`python3 tools/skill-lint.py` and `python3 tools/gc.py --report` are
unchanged in their findings on this file.
[Priority: must]

### REQ-LINT-HARNESSP6-003: REQUIRED row pair — `CONVERGENCE:` stated in `loop-control.md` and `SKILL.md`
`tools/skill-lint.py` must carry a `REQUIRED` row pair for the
`CONVERGENCE:` gate token of REQ-ORCH-HARNESSP6-001, mirroring the two rows that
guard the `COMMIT:` token: one asserting the producer (the token's definition
and position in `loop-control.md` §5) and one the consumer (its mention in
`SKILL.md` §The gate). This, REQ-LINT-HARNESSP6-001 and the `GIT_STATE`
row adopted into it are the cycle's only lint changes, and they land together. (workstream `harness-p6`; RS-HARNESSP6-001 Q4(d)
cost table)
**Acceptance**: `python3 tools/skill-lint.py` exits 0 once the token ships,
and exits non-zero naming the respective row when the token is removed from
either file.
[Priority: must]

### REQ-LINT-PACKAGING-001: The retired-prefix scope binds per entry, not per root
`retired_scope_files()` today walks `RETIRED_SCOPE_DIRS` and
`RETIRED_SCOPE_FILES` under one root. After the `plugins/sdd/` move
(REQ-PKG-PACKAGING-001) each entry must carry its own root binding:

| Scope entry | Root |
|---|---|
| `skills`, `tools`, `agents` | suite root |
| `docs/spec`, `docs/requirements` | corpus root |
| `.claude-plugin` | **both** — the deduplicated union |
| `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `LICENSE`, `.pre-commit-config.yaml` | **both** — the deduplicated union |

**Ordering note:** the scope-file row above already shows the **five**-name
list this entry has *after* REQ-LINT-PACKAGING-008 drops the sixth name from
`RETIRED_SCOPE_FILES`; while that removal is outstanding the live tuple carries
six, so this table is the post-`-008` state and `-008` must land first (or in
the same change) for the two to agree.

The union is taken over **resolved absolute paths** and deduplicated, so when
the two roots are equal the entry set is exactly today's. `.claude-plugin` must
be union-bound because after the move it exists at both roots —
`marketplace.json` stays at the corpus root, `plugin.json` moves to the suite
root — and a one-root binding silently drops whichever manifest the other root
holds, `marketplace.json` being the one file the move itself edits. The root
files are union-bound because `CLAUDE.md` and `.pre-commit-config.yaml` are
edited by the move and may exist at either root. The three suite-history
directories are suite-bound because `check_retired_prefix()` polices this
repository's own rename history, which has no meaning in a consumer tree
(REQ-PKG-PACKAGING-005 exception (i)). The existing self-test block that pins
the two constants against literal name tuples is **retained unchanged**: it
catches an area dropped from the enumeration, and it cannot catch a wrong root
binding, because directory names survive one intact. A per-root policed-**file
count** must not be added, for the reason REQ-LINT-PACKAGING-004 gives.
**Per-entry path rendering.** Each entry's findings must render their path
relative to the root that entry is bound to — a union-bound entry relative to
whichever root supplied the file. REQ-PKG-PACKAGING-002's per-root rule covers
the generic walk only and does not reach this check: `check_retired_prefix()`
(`tools/skill-lint.py:772`) and `retired_scope_files()` (`:756`, `:760`) each do
`f.relative_to(self.root)`, which raises `ValueError` on a suite-root file once
a second root is in the set — so without this clause the requirement is
unimplementable literally. (see RS-PACKAGING-003 D2, confidence medium)
**Acceptance**: with a nested root pair, the set returned by
`retired_scope_files()` contains the suite-root spellings of `skills`, `tools`
and `agents` and the corpus-root spellings of `docs/spec` and
`docs/requirements`, each asserted by membership on a seeded file **and each
finding's rendered path asserted relative to the root its entry is bound to**;
no construction with two distinct roots raises `ValueError`; and on a fixture
tree carrying both `skills/` and `docs/`, with the two roots set equal to that
tree, the returned set is identical to the pre-change single-root result over
that same fixture, compared as a set derived at run time.
[Priority: must]

### REQ-LINT-PACKAGING-002: `TEMPLATE_PAIRS` binds per side, and its `spec` side is skipped under disjoint roots
`TEMPLATE_PAIRS` is the second dual-rooted check and must bind each side to the
root its paths follow: the `TEMPLATE_SOURCE` side —
`skills/orchestrate/references/dispatch-templates.md` — moves and binds to the
**suite root**; every row's `spec` key is a `docs/spec/…` path that stays and
binds to the **corpus root**. Binding the gated check wholesale to the suite
root would resolve the spec side under the suite, where it will not exist, and
an absent spec file **warns rather than fails** — so all four rows would
silently degrade to warnings the moment the move lands, which is the
silent-disable class REQ-PKG-PACKAGING-003 rejects. When the two roots are
**disjoint** the `spec` side must be **skipped, not warned**, because warning
there names this suite's spec files inside a consumer's tree — the defect
REQ-PKG-PACKAGING-004 retargets the rows to avoid. Under containment the spec
side is checked and an absent spec keeps warning, unchanged.
(see RS-PACKAGING-003 D2; RS-PACKAGING-001 flagged the dual rooting)
**Acceptance**: with a nested root pair after the move, no `TEMPLATE_PAIRS` row
emits an absent-spec warning and none fails; binding both sides to the suite
root makes all four rows emit that warning, which the self-test asserts must not
happen; with disjoint roots no `template-drift` finding of any severity appears.
[Priority: must]

### REQ-LINT-PACKAGING-003: A set-membership assertion over both manifest paths detects a wrong root binding
The self-test must assert, in a two-root fixture, that the set returned by
`retired_scope_files()` contains **both** `<suite_root>/.claude-plugin/plugin.json`
and `<corpus_root>/.claude-plugin/marketplace.json`. Any one-root binding drops
exactly one of the two, so the assertion fails on precisely the defect it exists
for. A count-based assertion must not be used in its place: files under a
policed area grow by ordinary contribution, so a pinned count false-positives on
a correct change and an unpinned one proves nothing.
(see RS-PACKAGING-003 D2 §What detects a wrong binding)
**Acceptance**: both paths are members of the returned set in the two-root
fixture; binding `.claude-plugin` to the suite root alone, and to the corpus
root alone, each makes the self-test fail naming the missing path.
[Priority: must]

### REQ-LINT-PACKAGING-004: No absolute corpus count is asserted; `FILES_SWEPT=<n>` stays informational
No acceptance criterion and no assertion may pin the number of files swept from
a real corpus. Every formulation that encodes it fails: a literal fails on
ordinary contribution; a `git ls-files` comparand compares a working-tree walk
against a tracked list and hard-codes a path meaningless in a consumer
repository; and re-deriving the comparand from the corpus root re-implements the
sweep's own `rglob` and asserts it against itself. A swept-file count is
therefore **barred as an acceptance criterion**. It is not barred as output:
the `corpus: FILES_SWEPT=<n>  policed-areas=<n>` line is **introduced**, not
retained — no such line exists under `tools/` or `docs/spec/` today, only as a
sample block in RS-PACKAGING-002 labelled "Proposed shape, not observed output"
— and it is emitted **under REQ-LINT-PACKAGING-007's `--print-population`
flag**, as informational output with no pinned comparand, so the number stays
readable without being asserted. The two jobs a pinned count would have done —
catching a walk bound to a root that sweeps zero files, and catching a tree
swept twice — are taken over by REQ-LINT-PACKAGING-005 and -006.
(see RS-PACKAGING-003 D3, confidence medium)
**Acceptance** (the emission half is evaluated **after** REQ-LINT-PACKAGING-007
lands the flag — a plan ordering constraint): a run-time grep of the corpus for
an assertion comparing a sweep count against a literal or against
`git ls-files` returns zero matches outside REQ-LINT-PACKAGING-006's fixtures;
and `python3 plugins/sdd/tools/skill-lint.py --print-population` emits the
line, asserted by matching the line's shape rather than its number.
[Priority: must]

### REQ-LINT-PACKAGING-005: A live duplicate-freeness construction guard, reported as a `fail`-severity finding
Every run, in any repository, must assert that the swept list resolved to
absolute paths contains no path twice — `len(swept) == len({p.resolve() for p in
swept})`. This cannot fail for an implementation built as specified, because the
walk is a set union over resolved absolute paths: it is a **construction
guard**, pinning that the union stays a set and is never rebuilt as list
concatenation by a later edit. The double-sweep mode it guards is realizable
only when the two roots are equal, which is the geometry
REQ-PKG-PACKAGING-008 exercises. On failure the observable must be a
**`fail`-severity finding in the run's own findings list** — the `flag()`
default — not a warning, not an exception and not a bare exit code.
**Live zero-sweep detection is deliberately given up**, and this must be
recorded rather than quietly patched: a bare `FILES_SWEPT >= 1` is wrong because
an empty sweep is legitimate in a consumer repository with no `skills/`, and the
conditioned form — a floor applied only when the corpus root contains `skills/`
— reads its condition through the same root binding it is meant to test, so a
mis-bound root makes it vacuous instead of failing. Zero-sweep is caught at
self-test time only, by REQ-LINT-PACKAGING-006 and the fixtures of
REQ-PKG-PACKAGING-006..008. (see RS-PACKAGING-003 D3)
**Acceptance**: the assertion runs on every invocation; rebuilding the union as
list concatenation over two **equal** roots produces a finding whose severity is
`fail` and whose text names the duplicated path; no `--print-population`,
`--self-test` or plain run can skip it.
[Priority: must]

### REQ-LINT-PACKAGING-006: Each two-root fixture asserts an exact, fixture-local sweep count
Each fixture of REQ-PKG-PACKAGING-006..008 must seed a known number of `.md`
files and the self-test must assert the sweep returns **exactly** that number. A
literal is sound here and only here: a fixture does not grow by contribution. A
zero sweep from a mis-bound root fails this immediately, which is what replaces
the retired live count of REQ-LINT-PACKAGING-004.
(see RS-PACKAGING-003 D3 assertion 2)
**Acceptance**: each fixture's assertion names its own seeded count; adding a
file to a fixture tree without updating its count makes the self-test fail;
binding the corpus walk to a root containing no corpus makes the count
assertion fail.
[Priority: must]

### REQ-LINT-PACKAGING-007: `--print-population` emits the row populations, and states the population criterion
The skill linter must grow a `--print-population` flag that prints the
per-table row populations (the suite-gated tables and the ungated `FORBIDDEN`
table) together with the informational
`corpus: FILES_SWEPT=<n>  policed-areas=<n>` line of
REQ-LINT-PACKAGING-004. The flag does not exist today — argparse exposes only
the positional root and `--self-test`.

**The population criterion, stated here rather than referenced.** The flag's
output must report the four rule-table populations — `REQUIRED`,
`VERSION_GATED`, `V4_CONTRACT`, `FORBIDDEN` — each count derived from its
table at run time rather than written into the flag. The comparand is
**derived, not frozen**: the criterion is a three-way consistency check between
two live surfaces and the flag's output. The self-test asserts that
`--print-population`'s four counts equal the row counts of the four tables in
the code **and** equal the four numbers stated in
`docs/spec/two-root-linter.md` §6, and §6 states those numbers under a dated
marker as "current at <date>, moved by any cycle that adds rows" — so a cycle
that adds a row moves §6's numbers in the same change as the table row, and the
self-test fails the change that moves one side without the other. No
requirement carries the numbers as its own comparand; this one names the two
surfaces that must agree. On 2026-09-22 the surfaces agree at `REQUIRED=42
VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=14` (measured with `python3
plugins/sdd/tools/skill-lint.py --print-population`); the
pipeline-observability delta — fifteen `REQUIRED` rows (p1–p14 at the requirements stage; p15 added by the implement-stage fix, Q-IMPL-PIPELINEOBSERVABILITY-011) under
REQ-REV-PIPELINEOBSERVABILITY-001 and one `FORBIDDEN` row under
REQ-LINT-PIPELINEOBSERVABILITY-001 — lands `REQUIRED=57 FORBIDDEN=15`, and §6
moves with it. This is the only place in the corpus where a row population is
compared against a number; REQ-PKG-PACKAGING-004's "carried, not re-measured"
governs the populations **as evidence** and explicitly reserves this one
comparison as a regression check on the retarget (the numbers it quotes are the
packaging cycle's, as of its date; the comparand it delegates to is this
requirement's), and REQ-LINT-PACKAGING-004's ban applies to swept-**file**
counts from a live corpus, not to static in-code rule-table rows. A previous
drafting of this requirement referred to a "headline 40-row criterion" that was
stated nowhere; that dangling reference is replaced by the criterion above.

**Ordering constraint.** The task that produces the flag must precede any task
that evaluates the population criterion above — that is, the acceptance of
**this** requirement, REQ-LINT-PACKAGING-007, is the consuming side, and no
other requirement's acceptance names it. This is part of the requirement, not a
scheduling preference: a criterion written against a flag that does not exist
cannot be evaluated at all.
(see RS-PACKAGING-003 §Recommended Next Step, sequencing constraint confirmed)
**Acceptance** (evaluated **after** the move of REQ-PKG-PACKAGING-001, at
`plugins/sdd/tools/skill-lint.py`): `python3
plugins/sdd/tools/skill-lint.py --print-population` exits 0 and
prints one line per rule table with its row count, each count derived from the
table at run time rather than written into the flag; the three-way equality
holds today — the printed counts equal the code tables' row counts and equal
the numbers `docs/spec/two-root-linter.md` §6 states under its dated marker
(`REQUIRED=42 VERSION_GATED=9 V4_CONTRACT=7 FORBIDDEN=14` on 2026-09-22,
measured with the command above; `57` / `15` once the pipeline-observability
rows land); the self-test asserts the same equality, and in a temp copy it
fails when any one of the three is changed alone — a row added to a table
without moving §6, a number edited in §6 without a row, or a count written
into the flag as a literal; the plan orders the task producing the flag before
the task evaluating this criterion.
[Priority: must]
> **Amended 2026-09-22** (workstream `pipeline-observability`,
> specs closing review C2, Q-REQ-PO-AL; the stated totals moved `56 → 57` at the
> verify-stage red round R1, index 27.8) `[Updated: 2026-09-22]`: the comparand
> became derived. Cause: the criterion was written
> as a frozen literal (`40 / 9 / 7 / 13`, carried from RS-PACKAGING-002) that
> every row-adding cycle had to chase in three places — this requirement, §6 and
> the self-test's pinned dict — and the pin failed the moment a delta landed.
> This requirement lagged the spec by one manual landing: the orchestrator's
> manual pin landing at the pipeline-observability research gate (two routing
> `REQUIRED` rows and one `FORBIDDEN` row, `40 / 13 → 42 / 14`) updated
> `docs/spec/two-root-linter.md` §6 and the self-test's pinned dict but not this
> requirement, which still read `40 / 13` against a tree measuring `42 / 14`
> with the command above. The pin is now a consistency check between §6's dated
> numbers and the live tables, so the fifteen `REQUIRED` rows and one
> `FORBIDDEN` row this cycle adds move §6 to `57 / 15` instead of breaking a
> frozen number; the same hits are also reconciled in
> REQ-LINT-PIPELINEOBSERVABILITY-001's and REQ-REV-PIPELINEOBSERVABILITY-001's
> second sweep blocks, which state the post-delta populations.
> **Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG, Q-REQ-PO-AL,
> 2026-09-22)** over the binding statement of this amendment — the population
> comparand is the three-way equality, and the numbers live in
> `docs/spec/two-root-linter.md` §6 under a dated marker. A listing grep over
> `docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents
> plugins/sdd/tools/skill-lint.py`; hits in this requirement's own text and in
> the index rows citing it are the statement itself and are excluded.
> Command: `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents plugins/sdd/tools/skill-lint.py -type f ! -path docs/requirements/integration/skill-lint.md -exec grep -nHE 'REQUIRED=|FORBIDDEN=|print-population|population' {} +`.
> `docs/spec/two-root-linter.md` §6 (the criterion sentence at `42 / 9 / 7 /
> 14`), its §Acceptance Criteria bullet naming "the four §6 populations by name
> and value" and Q-IMPL-PACKAGING-001 (quoting §6) — reconciled, §6 is the
> second live surface of the equality; the specs stage places its numbers under
> the dated marker and moves them to `57 / 15` with the rows;
> `plugins/sdd/tools/skill-lint.py` self-test `pinned` dict (`42 / 14`, with the
> research-gate comment) — reconciled, the dict's assertion becomes the
> three-way equality and reads `57 / 15` after the delta;
> `docs/spec/skill-lint-v5.md` §Self-Test Extension (formerly "grows by
> exactly six" (harness-p6), now "grows by exactly fifteen" under the
> 2026-09-22 marker; `grep -c 'grows by exactly fifteen'
> docs/spec/skill-lint-v5.md` = 2, "asserts the new total") — reconciled, the
> delta's history under its dated marker; the new total is §6's dated number; `docs/requirements/integration/packaging.md`
> REQ-PKG-PACKAGING-004 ("compared once … `REQUIRED=40 … FORBIDDEN=13`", "the
> 56 suite-gated rows" = 40 + 9 + 7) — reconciled by naming this requirement as
> the mover; the sentence records the packaging cycle's numbers as of its date
> and is another workstream's shared body, not rewritten here;
> `docs/requirements/index.md` packaging item coverage and Q-REQ-PKG-B
> (`40 / 13`) — reconciled, the packaging ledger's history;
> `docs/spec/skill-lint-v5.md` (the `--print-population` summary sentence),
> `docs/spec/marketplace-packaging.md`, `docs/spec/pre-commit.md`,
> `docs/spec/skill-namespace-rename.md`, `docs/spec/adversarial-verify.md`,
> `docs/requirements/integration/naming.md` and the linter's `policed_*` tuples
> — reconciled, a different subject (bundled-tool and policed-area populations,
> no rule-table count); `plugins/sdd/skills/**`, `plugins/sdd/agents/**` — no
> hit.
> Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
> files the `-l` listing names: `docs/requirements/functional/review.md`
> (REQ-REV-PIPELINEOBSERVABILITY-001's rule-table population re-run) —
> reconciled, the same re-run; `docs/spec/requirements-artifacts.md` (the
> amended-row population of REQ-REQ-PIPELINEOBSERVABILITY-001 (d)) — a
> different subject, reconciled; `docs/spec/pipeline-observability.md` —
> reconciled, the cycle's index spec, it lists Q-SPEC-PO-U, the
> `--print-population` equality by citation of -007.

### REQ-LINT-PACKAGING-008: The retired front door's filename is dropped from both tuples together
The retired front door's filename —

```
README.org
```

— must be removed from `RETIRED_SCOPE_FILES`
and from the self-test's independent `policed_files` tuple **in the same
change**, leaving five names in each. The two tuples are compared against each
other by the scope-drift check, so editing one alone trips it; the entry is
behaviour-neutral today only because the walk never finds a file by that name.
The union binding of REQ-LINT-PACKAGING-001 is unchanged by the removal.
`docs/spec/skill-namespace-rename.md:76` documents the same tuple by name and
must drop the retired filename **in the same change**, or the spec contradicts
the code it documents. This
repair is carried unchanged from the marketplace cycle, where it was recorded as

```
Q-IMPL-MARKETPLACE-017
```

(see `docs/ws/packaging/kickoff.md` §Carried repairs;
`docs/spec/project-docs.md`; RS-PACKAGING-003 D2)
**Acceptance** (evaluated **after** the move of REQ-PKG-PACKAGING-001, at
`plugins/sdd/tools/skill-lint.py`): a run-time grep of
`plugins/sdd/tools/skill-lint.py` for the retired
filename — the grep pattern is the name fenced above, `README` followed by
`.org` — returns zero matches; the same grep over
`docs/spec/skill-namespace-rename.md` returns zero matches and that file's
tuple lists five names; both tuples have five entries and are equal;
`python3 plugins/sdd/tools/skill-lint.py --self-test` passes, and removing the
name from only one tuple makes it fail naming the scope drift.
[Priority: must]

### REQ-LINT-PIPELINEOBSERVABILITY-001: the `literal-anchor` pattern is a skill-lint drift phrase over the shipped skill text
`plugins/sdd/tools/skill-lint.py` must carry the `literal-anchor` pattern
(`[\w./-]+\.md:\d+` on a visible, non-fenced line) as a `FORBIDDEN` drift
phrase — **source-line discipline, stated explicitly as
REQ-GC-PIPELINEOBSERVABILITY-001 states it**: every line outside a fenced
block is read **whole**; inline-code (backticked) and quoted spans are **not**
blanked, so an anchor written as `` `<file>.md:<line>` `` on a visible line is a
finding — over the **swept markdown set** — every `*.md` the linter sweeps under
`plugins/sdd/**` (files: the swept markdown set, not `plugins/sdd/tools/*.py`
nor `plugins/sdd/tools/fixtures/**`, which the zero-cost measurement did not
cover; Q-REQ-PO-S), so the
snapshot-comparand class REQ-GC-PIPELINEOBSERVABILITY-001 warns on in the
binding corpus is kept **out** of the shipped skill, reference and agent text
through the mechanism that already sweeps that tree — not by widening gc's docs
scope. The tree carries 0 such anchors on 2026-09-22 (measured over 28 files),
so the phrase lands at no repair cost. (see RS-PIPELINEOBSERVABILITY-001 §Q5
scope decision.) Leaves REQ-LINT-002/-003 (drift-phrase mechanism — one row
added), REQ-LINT-HARNESSP5-003 and REQ-LINT-PACKAGING-001..-008 consistent; the
row moves the `FORBIDDEN` population REQ-LINT-PACKAGING-007 (as amended
2026-09-22, Q-REQ-PO-AL) compares — `14 → 15`, stated in
`docs/spec/two-root-linter.md` §6 under its dated marker in the same change as
the row, as REQ-LINT-PACKAGING-008's same-change discipline requires. Extending the phrase to the
Python tools and their fixtures is a later decision, taken only after a
read-only measurement over that set.
**Acceptance**: `python3 plugins/sdd/tools/skill-lint.py` exits 0 on this
tree; in a temp copy with a `.md` path followed by a colon and a line number
(the anchor form) placed on a visible line of one `SKILL.md` the linter exits
non-zero with the phrase finding naming that file, with the same anchor
placed **inside backticks** on a visible line it likewise exits non-zero
naming that file (the span discipline is what this case decides), and with
the same text inside a fenced block it exits 0; the same anchor form placed in a `.py` file
under `plugins/sdd/tools/` in the temp copy raises no finding from this row;
after the addition `python3 plugins/sdd/tools/skill-lint.py
--print-population` prints `FORBIDDEN=15` (`FORBIDDEN=14` on 2026-09-22,
measured with that command, plus this row), the same number
`docs/spec/two-root-linter.md` §6 states under its dated marker, and
REQ-LINT-PACKAGING-007's three-way equality holds.
**Corpus sweep (REQ-REQ-PIPELINEOBSERVABILITY-001 (e), Q-REQ-PO-AG,
2026-09-22)** over the `literal-anchor` drift phrase over the swept markdown
set — a listing grep over `docs/requirements docs/spec plugins/sdd/skills
plugins/sdd/agents`; hits in this requirement's own text and in the index rows
citing it are the statement itself and are excluded.
Command: `find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents -type f ! -path docs/requirements/integration/skill-lint.md -exec grep -nH 'literal-anchor' {} +`.
`docs/spec/skill-lint-v5.md` §`literal-anchor` as a `FORBIDDEN` drift phrase —
reconciled, carries this requirement; `docs/spec/drift-sweep.md` rows 16–19,
§`literal-anchor` and §Routing at DONE, and
`docs/spec/pipeline-observability.md` (Q-SPEC-PO-E, the measured counts) —
reconciled, gc's rule over the docs corpus (REQ-GC-PIPELINEOBSERVABILITY-001),
whose own sweep covers the docs-side sentences; `plugins/sdd/skills/**`,
`plugins/sdd/agents/**` — no hit (`plugins/sdd/tools/skill-lint.py` is outside
the swept trees; its row is the acceptance above);
`docs/requirements/integration/drift-sweep.md` REQ-GC-PIPELINEOBSERVABILITY-001
— reconciled, the two rules share the pattern and differ in tree.
Re-run with the population terms (specs closing review C2, Q-REQ-PO-AL,
2026-09-22) —
`find docs/requirements docs/spec plugins/sdd/skills plugins/sdd/agents plugins/sdd/tools/skill-lint.py -type f ! -path docs/requirements/integration/skill-lint.md -exec grep -nHE 'REQUIRED=|FORBIDDEN=|print-population|population' {} +`:
the post-delta populations this cycle lands are `REQUIRED=57` (42 today,
measured with `python3 plugins/sdd/tools/skill-lint.py --print-population`,
plus the fifteen rows p1–p15 of `docs/spec/skill-lint-v5.md` §`REQUIRED`
Rows — Pipeline-Observability) and `FORBIDDEN=15` (14 today, plus this
requirement's `literal-anchor` row), and the requirement that moves them is
REQ-LINT-PACKAGING-007 as amended. `docs/spec/two-root-linter.md` §6 (the
criterion sentence at `42 / 9 / 7 / 14`), its §Acceptance Criteria bullet
("the four §6 populations by name and value") and Q-IMPL-PACKAGING-001
(quoting §6) — reconciled, §6 is the second live surface of -007's three-way
equality: after the delta it reads `REQUIRED=57 VERSION_GATED=9 V4_CONTRACT=7
FORBIDDEN=15` under a dated marker, moved by the specs stage;
`plugins/sdd/tools/skill-lint.py` self-test `pinned` dict (`42 / 14`, with the
research-gate comment) — reconciled, post-delta `57 / 15`, and its assertion
becomes -007's three-way equality; REQ-LINT-PACKAGING-007 — the mover,
amended; `docs/spec/skill-lint-v5.md` §Self-Test Extension ("grows by exactly
six", "asserts the new total") — reconciled, the harness-p5 six-row delta's
history; the new total is §6's dated number, and the fifteen rows move it
`42 → 57`; `docs/requirements/integration/packaging.md`
REQ-PKG-PACKAGING-004 ("compared once … `REQUIRED=40 … FORBIDDEN=13`", "the
56 suite-gated rows" = 40 + 9 + 7) — reconciled by naming the mover: the
sentence records the packaging cycle's numbers as of its date and delegates the
single comparison to -007, whose comparand is now §6's dated number; another
workstream's shared body, not rewritten here; `docs/requirements/index.md`
packaging item coverage and Q-REQ-PKG-B (`40 / 13`) — reconciled, the
packaging ledger's history; `docs/spec/skill-lint-v5.md` (the
`--print-population` summary sentence), `docs/spec/marketplace-packaging.md`,
`docs/spec/pre-commit.md`, `docs/spec/skill-namespace-rename.md`,
`docs/spec/adversarial-verify.md`, `docs/requirements/integration/naming.md`
and the linter's `policed_*` tuples — reconciled, a different subject
(bundled-tool and policed-area populations, no rule-table count);
`plugins/sdd/skills/**`, `plugins/sdd/agents/**` — no hit.
Re-run under the path-precise form (Q-REQ-PO-AN, 2026-09-22), the further
files the `-l` listing names: `docs/requirements/functional/review.md`
(REQ-REV-PIPELINEOBSERVABILITY-001's rule-table population re-run) —
reconciled, the same re-run; `docs/spec/requirements-artifacts.md` (the
amended-row population of REQ-REQ-PIPELINEOBSERVABILITY-001 (d)) — a
different subject, reconciled; `docs/spec/pipeline-observability.md` —
reconciled, the cycle's index spec, it lists Q-SPEC-PO-U, the
`--print-population` equality by citation of -007.
[Priority: must]
`[Updated: 2026-09-22]` — requirements review round 5 M3: the backticked-span
discipline is stated (spans read, not blanked) and the temp-copy check gains
the backticked-anchor case.
