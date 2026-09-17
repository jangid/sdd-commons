---
status: Approved
last_updated: 2026-09-17
requires:
  - REQ-ARB-HARNESSP2-001
  - REQ-ARB-HARNESSP2-002
  - REQ-ARB-HARNESSP2-003
  - REQ-ARB-HARNESSP2-004
  - REQ-ARB-HARNESSP2-005
  - REQ-ARB-HARNESSP2-006
  - REQ-ARB-HARNESSP2-007
  - REQ-ARB-HARNESSP2-008
  - REQ-SKILL-HARNESSP2-003
  - REQ-SKILL-HARNESSP2-006
  - REQ-LINT-HARNESSP2-001
---

# Arbitrated Handoff Between Contradicting Review Rounds

## Context

Inside a fix loop every review round is a fresh, isolated reader (REQ-REV-007,
`sdd-review` §Bias Disclosure). When round N+1 raises a Critical on content
nobody changed, or regresses the verdict without new ground, the v5 default —
treat the latest round as authoritative and `loop-back-to-fix` — makes the loop
ping-pong until `FIX_LOOP_MAX`. RS-HARNESSP2-001 Q3 showed that two
contradiction classes are decidable by **string and set comparison** over state
the orchestrator already holds: each round's Critical/Material lines (the
compiled findings log, `harness-loop-control.md` §Fix-Loop Cap) and each fix
dispatch's written delta (`harness-write-scope.md` §Observation). Finding ids
(`C1`, `M1`) are not stable across rounds, so the key is `(file:section,
affects)`.

This spec defines the retained per-round state, the two detected classes and
the undetected one, section resolution of fix hunks, the `REVIEW:
CONTRADICTION` pause and its four options, the third-opinion rule, and the
`affects` key on Material lines. It fulfils REQ-ARB-HARNESSP2-001..008, the
skill changes of REQ-SKILL-HARNESSP2-003 / -006 and rows (b), (c) of
REQ-LINT-HARNESSP2-001. `REVIEW: CONTRADICTION` is defined here and nowhere
else. Arbitration is **default on** — it only pauses.

## Design

### Retained Per-Round State (REQ-ARB-HARNESSP2-001)

Session state only — no artifact (REQ-HARN-027); it lives beside the compiled
findings log in `references/loop-control.md`:

```
round[N]      = { verdict: APPROVE | APPROVE_WITH_FIXES | REJECT,
                  lines: [ { tier: C | M, text: <verbatim line>,
                             key: { file: <repo-relative path>, section: <§Name> | "?",
                                    affects: { REQ-… } } } ] }
fix[N]        = { written: { (file, section) }, hunks: { (file, section): "L40-58, L120" } }
```

Key parsing from a review line `- C1: <what> — [file:section] — affects
[REQ-A-001, REQ-A-004]`:

| Part | Rule |
|---|---|
| `file` | the text before the first `:` inside `[…]`, normalised to a repo-relative path (leading `./` stripped); an unresolvable path keeps the raw text |
| `section` | the text after that `:`, with a leading `§` or `#`s stripped, whitespace collapsed, kept case-sensitive → stored as `§Name`; missing → `?` |
| `affects` | every `REQ-[A-Z]+(-[A-Z0-9]+)?-\d{3}` id in the `affects` clause; `affects —` or none → `∅` |

A line whose `[file:section]` cannot be parsed at all is retained with
`section = ?`, `affects = ∅` and participates only in file-level comparison.
`fix[N].written` comes from §Section Resolution; when that is unavailable for a
path it falls back to `(file, *)` — every section of the file — from the
path-level delta (REQ-HARN-021).

### Contradiction Classes (REQ-ARB-HARNESSP2-002, -003, -004)

Let `K_N` = set of `(file, section)` keys of round N's C/M lines, `W_N` =
`fix[N].written`, `F(K)` = the files of a key set. With `∈` at section
level unless degraded:

| Class | Rule | Detected? |
|---|---|---|
| **(b) new C/M on approved ground** | ∃ line ∈ round N+1 (tier C or M) with key `k` such that `k ∉ K_N` **and** `k ∉ W_N` | **yes** — set membership |
| **(c) verdict regression without new ground** | `round[N].verdict == APPROVE_WITH_FIXES` ∧ `round[N+1].verdict == REJECT` ∧ (i) `W_N ⊆ K_N` ∧ (ii) `K_{N+1} ⊆ K_N ∪ W_N` | **yes** — weaker signal, labelled `class c` |
| **(a) reversal** | a round-N+1 line with `k ∈ K_N` asking the opposite change | **no** — "opposite" is semantic; rendered `(persisting)` in the compiled log exactly as today and surfaced by REQ-HARN-001's exhausted-log gate |

Trigger = (b) ∨ (c); when both hold, (b) is reported (it is the stronger
signal). **Degradation**: when a key or a written pair has `section = ?` or
`*`, the comparison for that key is at **file level** (`file ∉ F(K_N)` ∧ `file
∉ F(W_N)`), the pause labels itself `(file-level)`, and the operator is told it
may over-fire when the fix touched the same file elsewhere. Section resolution
is the remedy, not a spike (§Section Resolution).

**Why not detect (a)**: a rule that guessed "opposite" from text would be a
semantic judgement inside the orchestrator, which REQ-HARN-019 and REQ-ORCH-012
keep out; the cap remains the backstop for reversals.

### Section Resolution of Fix Hunks (REQ-ARB-HARNESSP2-005) [needs-code]

Extends the write-scope observation (`harness-write-scope.md` §Observation;
`references/write-scope.md` §3) — this closes limitation (a) for Markdown
paths. For each path in the fix dispatch's written set:

```
committed  : git diff -U0 <HEAD_before> <HEAD_after> -- <path>
uncommitted: git diff -U0 <HEAD_after> -- <path>            # porcelain-only writes
untracked  : every heading of the file → (path, *)          # a new file is written in full
```

For each hunk header `@@ -a,b +c,d @@`: take the after-image start line `c`
(for a pure deletion, `d == 0`, use `c` as well); the enclosing section is the
nearest `#`-heading line ≤ `c` in the after-image (`git show <HEAD_after>:<path>`
or the working file); normalise the heading text as in §Retained Per-Round
State (`§Name`). A hunk above the first heading resolves to `§(preamble)`.
Non-Markdown paths resolve to `(path, ?)` and fall back to file-level
comparison. The result per path is the set of `(path, §Name)` pairs plus the
hunk ranges for rendering (`docs/spec/x.md §A (hunks L40-58)`).

`tools/sdd-scope-check-selftest.py` gains scenario **F8** "section resolution":
a fixture diff touching lines 40–58 under `## A` and line 120 under `## C` of
`docs/spec/x.md` yields `{x.md:§A, x.md:§C}` and the hunk strings.

### `REVIEW: CONTRADICTION` Pause (REQ-ARB-HARNESSP2-006)

On (b) or (c) at a **stage gate** (never the per-chunk gate, which shows no
review verdict — REQ-ORCH-018 precedent), the orchestrator pauses:

```
REVIEW: CONTRADICTION (round 1 vs round 2, class b) — stage: specs, iteration 2 of 3
  round 1 (APPROVE_WITH_FIXES): C1 <verbatim line> — docs/spec/x.md §A — affects REQ-X-001
  fix #1 wrote: docs/spec/x.md §A (hunks L40-58)
  round 2 (REJECT):             C1 <verbatim line> — docs/spec/x.md §C — affects REQ-X-004   <- section untouched by fix #1, not raised in round 1
  Options: accept round 2 (fix) | accept round 1 (proceed, note) | third opinion (re-dispatch review) | stop
```

Shape rules: the token line is `REVIEW: CONTRADICTION (round N vs round N+1,
class b|c[, file-level]) — stage: <stage>, iteration N of MAX`; both rounds'
verdicts and C/M lines verbatim with their keys, side by side; `fix #N wrote:`
between them; each new-ground line annotated `<- section untouched by fix #N,
not raised in round N`; verbatim lines and paths only, never reviewer reasoning
(REQ-ORCH-012); ephemeral (REQ-ORCH-013).

| Option | Effect | Iteration counter |
|---|---|---|
| `accept round N+1 (fix)` | normal fix re-dispatch with round N+1's packet | **+1** |
| `accept round N (proceed, note)` | proceed; the note lands where a gate decision already lands — the artifact's own Open Questions, or a Q-IMPL entry when the artifact is a spec — never a review store | unchanged |
| `third opinion (re-dispatch review)` | §Third Opinion | unchanged |
| `stop` | halt | unchanged |

The pause is not a dispatch and not an iteration; it can occur only at
iteration ≥ 2 and therefore always inside the `FIX_LOOP_MAX` window
(REQ-HARN-001 stays the terminal backstop). It is the **fourth** member of the
pause family in `references/loop-control.md` §6 beside `REVIEW: MALFORMED`,
`RETURN: MALFORMED` and reject-with-no-actionable-findings. Telemetry records
the class as `verdict.contradiction_class` on the round-N+1 review record and
the operator's option as `gate.decision` (`telemetry.md`).

### Third Opinion (REQ-ARB-HARNESSP2-007)

`third opinion` dispatches a fresh review of the same stage artifacts (reviews
are idempotent and isolated, REQ-ORCH-014) — **not** a fix iteration (the
verifier re-dispatch rule). Resolution against **both** prior rounds:

| Round 3 relation | Outcome |
|---|---|
| `K_3 == K_N`, or (`verdict_3 == verdict_N` ∧ `K_3 ⊆ K_N ∪ W_N`) | resolves in round N's favour → gate re-renders with round N's verdict and normal options |
| `K_3 == K_{N+1}`, or (`verdict_3 == verdict_{N+1}` ∧ `K_3 ⊆ K_{N+1} ∪ W_N`) | resolves in round N+1's favour → gate re-renders with round N+1's verdict and normal options |
| both (degenerate: rounds agree on keys) | round N+1 (the later, and the one whose packet is current) |
| neither | pause re-renders with **three columns** and only `fix | proceed | stop` |

At most **one** third opinion per contradiction; `iteration N of MAX` is
unchanged throughout. The third round's record is a `review` telemetry record
with `dispatch.reason: THIRD_OPINION`.

### Review Key on Material Lines (REQ-ARB-HARNESSP2-008)

`sdd-review`'s report template changes exactly one line and its example:

```
**Material findings:** [should fix; can proceed with note]
- M1: [what's wrong] — [file:section] — affects [REQ-*] | affects —
```

Critical lines already carry `[file:section]` and `affects`; the rest of the
report format (REQ-REV-002) and review's scope boundaries (REQ-REV-005/006)
are unchanged. `sdd-review` gains no red, telemetry or arbitration text — the
reviewer is not told about arbitration, which keeps rounds independent.

### Skill and Lint Changes (REQ-SKILL-HARNESSP2-003, -006; REQ-LINT-HARNESSP2-001 (b), (c))

| Where | Change |
|---|---|
| `skills/sdd-orchestrate/references/loop-control.md` | retained tuple beside the compiled findings log; class table with the reversal limitation; the pause fixture text; options table; third-opinion resolution; §6 lists `REVIEW: CONTRADICTION` as the fourth pause |
| `skills/sdd-orchestrate/SKILL.md` §The gate | one pointer line next to the `MALFORMED` family |
| `skills/sdd-orchestrate/references/write-scope.md` §3 | section resolution procedure (hunk → enclosing heading) as an extension of the three commands |
| `skills/sdd-review/SKILL.md` | Material template line gains `affects` (one line + its example; nothing else) |
| `tools/sdd-scope-check-selftest.py` | scenario F8 (§Section Resolution) |
| `tools/sdd-skill-lint.py` `REQUIRED` | (b) `references/loop-control.md` ∋ `REVIEW: CONTRADICTION` min 1 — consumer-only (the orchestrator raises and handles it), with `SKILL.md` §The gate carrying the pointer; (c) `skills/sdd-review/SKILL.md` ∋ a Material template line matching `M1:.*affects` min 1; both with `reason` and `fix`; `--self-test` §7 covers them; total REQUIRED rows ≥ 32 with `adversarial-verify.md`'s two |
| `skills/sdd-orchestrate/USAGE.md` | section: the pause, its four options, what "note" means (`telemetry.md` §Skill and Lint Changes lists all USAGE sections) |

## Verification

### Automated

- `test_key_parse`: `- C1: x — [docs/spec/x.md:§A] — affects [REQ-X-001]` →
  `(docs/spec/x.md, §A, {REQ-X-001})`; a Material line with `affects —` → `∅`;
  an unparsable ref → `(?, ∅)`.
- `test_class_b_fires_on_untouched_section`: round 1 names §A; fix wrote only
  §A; round 2 raises C1 at §C → `REVIEW: CONTRADICTION (… class b)`; the same
  fixture with round 2 at §A → no token.
- `test_class_b_file_level_degradation`: sections unresolved → fires at file
  level with `(file-level)` in the token line.
- `test_class_c_regression`: `APPROVE_WITH_FIXES → fix touching only round-1
  refs → REJECT with the same refs` → `class c`; round 2 as
  `APPROVE_WITH_FIXES` → no token.
- `test_reversal_not_detected`: identical keys across rounds → no
  `CONTRADICTION`; the compiled log shows `(persisting)`.
- `test_section_resolution` (scope self-test F8): hunks at L40–58 under `## A`
  and L120 under `## C` → `{x.md:§A, x.md:§C}`; an untracked new file → `(path,
  *)`; a `.py` path → `(path, ?)`.
- `test_pause_text_shape`: the fixture in `loop-control.md` matches §Pause
  byte-for-byte in structure (token line, two rounds, `fix #N wrote:`,
  annotation, four options).
- `test_pause_consumes_no_iteration`: after the pause and `accept round N
  (proceed, note)` the fix counter is unchanged; `accept round N+1 (fix)`
  increments it by one.
- `test_pause_only_at_stage_gate_and_iteration_ge_2`.
- `test_third_opinion_two_of_three`: round 3 matching round 1 re-renders the
  normal gate with `iteration N of MAX` unchanged; round 3 matching neither
  renders three columns and no `third opinion` option; a second `third
  opinion` is not offered.
- `test_lint_contradiction_and_affects_rows`: removing `REVIEW: CONTRADICTION`
  from `loop-control.md`, or `affects` from the Material template line, → exit
  1 with that row's fix; shipped set → exit 0.
- `test_review_diff_is_one_line`: `sdd-review/SKILL.md` diff against v5
  touches only the Material template line and its example.

### Manual

- Replay a real two-round fix loop from a past cycle's gate text; confirm the
  class the rule assigns matches the operator's reading.

### Acceptance Criteria

- [ ] Retained tuple (verdict, C/M lines with `(file:section, affects)` keys, fix written pairs) defined in `loop-control.md`, session-only (REQ-ARB-HARNESSP2-001)
- [ ] Class (b) rule as a set operation; `(file-level)` degradation labelled (REQ-ARB-HARNESSP2-002)
- [ ] Class (c) rule with conditions (i) and (ii); labelled `class c` (REQ-ARB-HARNESSP2-003)
- [ ] Reversals not detected, stated beside the two classes, rendered `(persisting)` (REQ-ARB-HARNESSP2-004)
- [ ] Section resolution procedure (`git diff -U0`, enclosing heading, `§Name`, non-Markdown → `?`, untracked → `*`); scope self-test F8 (REQ-ARB-HARNESSP2-005)
- [ ] Pause token and text shape; four options with their counter effects; stage-gate only; iteration ≥ 2; fourth pause-family member; `contradiction_class` in telemetry (REQ-ARB-HARNESSP2-006)
- [ ] Third opinion: independent re-dispatch, not an iteration, two-of-three table, at most one (REQ-ARB-HARNESSP2-007)
- [ ] Material template line carries `affects` / `affects —`; nothing else in the report format changes (REQ-ARB-HARNESSP2-008)
- [ ] Skill changes tabled; lint rows (b), (c) with `--self-test` coverage (REQ-SKILL-HARNESSP2-003, -006; REQ-LINT-HARNESSP2-001)
- [ ] `python3 tools/sdd-skill-lint.py` exits 0

## Edge Cases

- **Round N+1 raises a new finding in a file the fix created** (untracked →
  `(path, *)`): every section counts as written → no class (b) — correct, the
  reviewer is reading new content.
- **Fix dispatch fanned into several chunk-grouped dispatches**: `W_N` is the
  union of their written pairs.
- **Round N had no C/M lines** (`APPROVE` then a fix for minor items, then
  `REJECT`): `K_N = ∅`; any C/M in round N+1 outside `W_N` is class (b) — the
  intended behaviour (new ground on approved content).
- **Review line references a section heading that was renamed by the fix**:
  the old `§Name` is not in `W_N` (which holds the new name) → class (b) may
  fire; the pause shows both names and the operator resolves. Default: accept
  the over-fire; renames are rare inside a fix.
- **Contradiction at the verify stage with red active**: red findings are
  not review lines and never enter `K_N`; arbitration compares review rounds
  only.
- **Marker `3`**: identical; paths are flat.

## Cross-Spec Consistency (XSPEC)

- `harness-loop-control.md` §Fix-Loop Cap: the pause consumes no iteration;
  `accept round N+1 (fix)` is a normal fix re-dispatch (+1); the compiled
  findings log's `(persisting)` rendering is reused for reversals; the
  `MALFORMED` pause family gains a fourth member.
- `harness-write-scope.md` §Observation gains section resolution; limitation
  (a) is partially closed for Markdown paths — recorded there as
  Q-IMPL-HARNESSP2-002; the `ADVISORY` tag rule is unchanged (section
  resolution informs the hint but does not yet automate it — Open Question 2).
- `harness-return-contract.md` §Repair Packet: `findings` verbatim lines are
  the same lines retained here; `dispatch.reason: THIRD_OPINION` is a review
  record annotation, not a packet reason.
- `review.md` §Report Format: one line changes (Material `affects`) — recorded
  there as Q-IMPL-HARNESSP2-004; verdict definitions, Strengths, scope
  boundaries unchanged; REQ-REV-007 isolation is the premise of arbitration.
- `orchestration.md` §Gate Protocol: `REVIEW: CONTRADICTION` is a stage-gate
  event like REQ-ORCH-018's pause; vocabulary extended by the four options —
  recorded there as Q-IMPL-HARNESSP2-008.
- `telemetry.md`: `verdict.contradiction_class ∈ {null, b, c}` and the
  `gate.decision` enum include `third-opinion` — consistent.
- `harness-chunk-verifier.md`: the per-chunk gate cannot raise this pause —
  consistent with "no review verdict at the per-chunk gate".
- `skill-lint-v5.md`: rows (b), (c) follow the `REQUIRED` row shape.
- **No unresolved contradictions.**

## Open Questions

1. **Class (b) false-positive rate** (`index.md` Open Questions): a
   legitimately new Critical the first reviewer missed pauses the loop.
   Default: accept — the pause costs one operator decision and is the intended
   ROUTE_TO_HUMAN; telemetered via `contradiction_class`.
2. **Use section resolution to automate the `ADVISORY` hint** (hunks under
   `## Implementation Questions` → `IN`)? Default: not this cycle; the hint text
   stays, the operator verifies.
3. **Heading normalisation across `§Name` variants** (`§3. Foo` vs `§Foo`):
   Default: strip a leading ordinal `\d+[.)]?\s*` before comparing.
