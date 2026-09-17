---
domain: LINT
last_updated: 2026-09-17
status: Approved
research_refs: [RS-008]
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
`skills/*/SKILL.md` and `skills/*/references/*.md` **except** the telemetry
stub section of `skills/sdd-orchestrate/SKILL.md` and
`skills/sdd-orchestrate/references/telemetry.md` (an explicit per-row allowlist
of paths — the linter must gain an `allow` field on `FORBIDDEN` rows if it lacks
one), with `reason` "telemetry is orchestrator-written and never a
phase-detection or staleness input (REQ-ORCH-014)" and a `fix:` that says to
remove the reference. Fenced code blocks are **not** exempt for this row — a
skill must not even show the path in an example — so the row scans raw text.
(see RS-HARNESSP2-001 Q1 guard (i); REQ-TELEM-HARNESSP2-007)
**Acceptance**: adding `.sdd/telemetry.jsonl` inside a fence in
`skills/sdd-plan/SKILL.md` makes the lint exit 1 with the row's fix; the two
allowlisted locations mentioning the path exit 0; `--self-test` covers the
allowlist.
[Priority: must]
