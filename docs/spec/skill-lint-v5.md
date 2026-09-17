---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-LINT-001
  - REQ-LINT-002
  - REQ-LINT-003
  - REQ-LINT-004
  - REQ-LINT-005
  - REQ-LINT-006
  - REQ-LINT-007
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
`SIZE_FAIL_LINES` → `fail`. At the 2026-09-17 baseline this warns on exactly
`sdd-orchestrate` (607) and `sdd-migrate` (464) and fails on none.

**Why 400 warn / 1000 fail**: 400 flags exactly the two files that absorbed
gate prose while leaving the other eight untouched (RS-008 Q4 size table); 1000
is the existing REQ-ORCH-019 guideline. Both are module constants so a later
audit can retune without touching check logic.

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
| "Upgrade offer (entry, all markers)", phase table, §The gate, dispatch contracts, §Isolation Discipline, §Rules, §Orchestrator-Only Work | **no** | — |

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
`references/write-scope.md` and `references/return-contract.md`): ≤ ~450 lines —
still a size warn, which is acceptable; a size fail is not.

### Self-Test Extension

`--self-test` gains fixtures for: a finding without `fix` (must be impossible —
asserted via signature); a warn-only fixture exits 0 with `1 warning(s)`; a
401-line SKILL.md warns and a 1001-line one fails; a backtick
`references/missing.md` fails while an existing one passes; each new `REQUIRED`
row fails when its marker is removed from a temp copy.

## Verification

### Automated
- `python3 tools/sdd-skill-lint.py --self-test` exits 0 and exercises every
  new check.
- `python3 tools/sdd-skill-lint.py` on the implemented skill set exits 0 and
  prints `OK: N file(s) clean, K warning(s)` with `K` ≥ 1 only for size warns.
- Mutation test: for each of the nine core rows, delete the marker in a temp
  copy → exit 1 and the row's `fix:` printed.
- `grep -c '"fix"' tools/sdd-skill-lint.py` equals the number of rule rows;
  `grep -n 'self.flag(' tools/sdd-skill-lint.py` shows a fix argument on every
  call.

### Manual
- Run the linter before and after the marker-4 move: exit 0 both times; after
  the move `wc -l skills/sdd-orchestrate/SKILL.md` ≤ ~450; every moved section
  has a stub containing "UNCHANGED" and a link that resolves;
  `ws-orchestration.md` has a new Q-IMPL entry citing Q-IMPL-016.

### Acceptance Criteria
- [ ] Every finding prints `fix:`; `flag()` requires it; rule tables carry `fix` (REQ-LINT-001)
- [ ] Warn tier exists; warn-only run exits 0 and prints the warning count; one fail still exits 1 (REQ-LINT-002)
- [ ] Size check at 400 warn / 1000 fail as module constants; baseline warns on exactly `sdd-orchestrate` and `sdd-migrate` (REQ-LINT-003)
- [ ] Backtick `references/` and `skills/<skill>/references/` paths resolve (fail), `docs/spec/*.md` mentions resolve (warn); code fences ignored (REQ-LINT-004)
- [ ] Nine core `REQUIRED` rows present with fix text; mutation of any one exits 1 (REQ-LINT-005)
- [ ] Remaining `REQUIRED` rows present; lint exits 0 on the implemented skill set (REQ-LINT-006)
- [ ] Marker-4 prose moved to `references/v4-workstreams.md` with stubs, `research_id` guard and superseding Q-IMPL; `SKILL.md` ≤ ~450 lines; lint exits 0 (REQ-LINT-007)
- [ ] `tools/sdd-skill-lint.py` exits 0; Markdown well-formed

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
  on a consumer repo via `REPO_ROOT`): warn, never fail — the linter must not
  assume this repo's layout (existing audit F11 principle).
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
  layout-independence (F11) — `docs/spec/` mentions are warn-only.
- **No unresolved contradictions.**

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
**Spec reference**: §Marker-4 Prose Move — size target "≤ ~450 lines (607 − ~160 moved)"
**Decision**: the move table listed only marker-4 prose; Chunks 2–4 added ~270 lines of loop-control procedure that no reference held, leaving `SKILL.md` at 720 after the move and dedup. A minor replan adds `skills/sdd-orchestrate/references/loop-control.md`; `SKILL.md` keeps marker stubs so REQUIRED rows a/b/d2/e2 still target it. The lint file count becomes 17.
**Rationale**: the spec's arithmetic predates the loop-control prose; the progressive-disclosure goal is served by one more reference, not by relaxing the target.
**Date**: 2026-09-17 (Chunk 5 replan)

