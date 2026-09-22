---
status: Approved
last_updated: 2026-09-22
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
  - REQ-ARB-HARNESSP3-001
  - REQ-ARB-HARNESSP4-001
  - REQ-ARB-HARNESSP4-002
  - REQ-ARB-HARNESSP4-003
  - REQ-ARB-HARNESSP5-001
  - REQ-ARB-HARNESSP5-002
  - REQ-ARB-HARNESSP5-003
  - REQ-ARB-PIPELINEOBSERVABILITY-001
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
regen[N]      = { written: { (file, section) }, hunks: { (file, section): "…" }, by: leaf | orchestrator }
                # every orchestrator-dispatched regeneration of the stage deliverable between round N and N+1
                # (a pipeline re-dispatch of the same stage — Q-IMPL-HARNESSP3-010), PLUS derived artifacts the
                # orchestrator itself regenerated in that window, e.g. docs/requirements/traceability.md
                # (by: orchestrator — Q-IMPL-HARNESSP3-017)
new[N]        = { (file, §heading) : no visible heading line naming §heading exists in `git show <sha_N>:<file>` }
                # fix-induced ground — both sides of a moved/renamed heading (added 2026-09-22, REQ-ARB-PIPELINEOBSERVABILITY-001)
W_N           = sections(fix[N].written) UNION sections(regen[N].written) UNION new[N]
                # the set §Contradiction Classes tests against; (file, *) only where section resolution is unavailable
```

[Amended 2026-09-18, harness-p4 — REQ-ARB-HARNESSP4-003: the schema block above
gains `regen[N]` and the `W_N` union that §Contradiction Classes, §`W_N`
Includes Regeneration Writes and `references/loop-control.md` §2a already carry,
so a reader taking this section as the schema of record builds the amended
state (`docs/ws/harness-p3/verification.md` §V11). `regen[N]` is a sibling set,
not a rename of `fix[N]` — Q-IMPL-HARNESSP3-009.]

Key parsing from a review line `- C1: <what> — [file:section] — affects
[REQ-A-001, REQ-A-004]`:

| Part | Rule |
|---|---|
| `file` | the text before the first `:` inside `[…]`, normalised to a repo-relative path (leading `./` stripped); an unresolvable path keeps the raw text |
| `section` | the text after that `:`, with a leading `§` or `#`s stripped, **then a leading ordinal `\d+[.)]?\s*` stripped** (`§3. Foo` ≡ `§Foo` — the rule `references/loop-control.md` §2a applies when computing `K_N`; added here 2026-09-19, REQ-ARB-HARNESSP5-003, closing Open Question 3), whitespace collapsed, kept case-sensitive → stored as `§Name`; missing → `?` |
| `affects` | every `REQ-[A-Z]+(-[A-Z0-9]+)?-\d{3}` id in the `affects` clause; `affects —` or none → `∅` |

**[2026-09-20, harness-p6 — REQ-ORCH-HARNESSP6-002.]** This key now has **two**
consumers: the round-arbitration rule in this spec, and key rule 3 of
`harness-loop-control.md` §Convergence Signal — L2, which reuses it — with this
section's ratified leading-ordinal strip — as its **retained, demoted** cluster
key. A change to the key's shape or to the strip rule therefore affects both;
the L2 consumer carries no recall claim, the Chunk 8 replay having measured the
`(file, section)` key at zero clusters over three cycles.

A line whose `[file:section]` cannot be parsed at all is retained with
`section = ?`, `affects = ∅` and participates only in file-level comparison.
`fix[N].written` comes from §Section Resolution; when that is unavailable for a
path it falls back to `(file, *)` — every section of the file — from the
path-level delta (REQ-HARN-021).

### Contradiction Classes (REQ-ARB-HARNESSP2-002, -003, -004)

Let `K_N` = set of `(file, section)` keys of round N's C/M lines, `W_N` =
`sections(fix[N].written)` **UNION** `sections(regeneration writes since round
N)` [Amended 2026-09-18, REQ-ARB-HARNESSP3-001 — `W_N` was `fix[N].written`
alone; see §`W_N` Includes Regeneration Writes], `F(K)` = the files of a key
set. With `∈` at section
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

**Fix-induced ground is written ground — the third term of `W_N`** — **Amended 2026-09-22** `[Updated: 2026-09-22]` (workstream `pipeline-observability`, REQ-ARB-PIPELINEOBSERVABILITY-001; REQ-ARB-HARNESSP2-002 as amended; the schema line of §Retained Per-Round State is edited in place; the record of why is §Pipeline-Observability Amendment).

```
new[N]  = { (file, §heading) : no visible heading line naming §heading exists in `git show <sha_N>:<file>` }
          # fence-aware scan; the leading-ordinal strip of §Retained Per-Round State applied to both sides
W_N     = sections(fix[N].written) UNION sections(regen[N].written) UNION new[N]
```

A round-N+1 Critical/Material key `(file, §heading)` whose heading **did not
exist** in `file` at round N's sha is ground the loop created: it belongs to
`W_N`, and the finding is ordinary — never a `REVIEW: CONTRADICTION (class b)`
pause. Equivalently, section resolution adds **both sides** of a moved or
renamed heading to `W_N`, because a diff's hunks are keyed on the heading they
sat under *before* the fix, so the new heading is otherwise absent from
`fix[N].written` although the fix wrote it. Decision procedure: read `git show
<sha_N>:<file>` through the same fence filter section resolution uses, strip
leading ordinals on both the round-N+1 key and the candidate heading lines, and
compare the normalised `§Name`s. A heading that existed at `sha_N` with
identical bytes is unchanged ground and stays out (REQ-ARB-HARNESSP5-001 is not
reopened). This is **not class (a)**: nothing is reversed. The
set-operation character of class (b) and its `(file-level)` degradation are
unchanged (REQ-ARB-HARNESSP2-002 as amended).

Skill side: `skills/orchestrate/references/loop-control.md` §2a's `W_N` definition carries the
same third term. Fixture: `python3 plugins/sdd/tools/scope-check-selftest.py`
gains scenario **A4** beside A1–A3.

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

### `W_N` Includes Regeneration Writes — Regenerated Is Not New Ground (REQ-ARB-HARNESSP3-001)

[Changed 2026-09-18. The defect is spec-read and run-corroborated (§B8: class (b)
fires by construction on every finding in a regenerated deliverable); the remedy
is **constructed** — it reuses the already-specified section-resolution
mechanism but has not yet been exercised by any run.]

The retained per-round write set is redefined as the union of the fix dispatch's
written pairs **and** the written pairs of every orchestrator-dispatched
**regeneration of the stage deliverable** between review round N and round N+1:

```
W_N := sections(fix[N] writes) UNION sections(regeneration writes since round N)
       # falling back to (file, *) only where section resolution is unavailable,
       # which is the existing rule and already labels the pause "(file-level)"
```

This is stated as a general **regenerated-not-patched** rule at the §2a level,
**not** inside the red section, because it applies to any stage whose pipeline
leaf rewrites its artifact wholesale between rounds — specs, plan, verification.

`fix[N]` generalises from "the fix dispatch" to "the loop dispatches between
round N and round N+1". Whether that is a rename or a sibling `regen[N]` whose
pairs union in is an **implementation choice**; the **union** is the contract.

Granularity is **not** lost: section resolution (REQ-ARB-HARNESSP2-005) is a
function of a diff, and it applies to a regeneration diff exactly as it applies
to a fix's.

[Amended 2026-09-19, harness-p5 — REQ-ARB-HARNESSP5-001, ratified as Q-REQ-P5-A]
`W_N` is **diff-based**: a regeneration that re-emits a section
**byte-identically adds nothing to `W_N`**, and a round-N+1 Critical/Material
line keyed on such a section is on ground round N saw **unchanged** — the
class (b) signal, not the false positive this section removed. The provenance
reading `regen[N] = (file, *)` for a wholesale dispatch whose diff exists is
**not** adopted: `(file, *)` remains reserved for a *missing* diff (an untracked
or non-Markdown path, §Section Resolution / self-test F8). Why: under
provenance a `regenerate-wholesale` deliverable contract would be blanket
immunity for the whole file and the guarantee below ("cannot mask a
contradiction") would break; the p4 O1 pause
(`docs/ws/harness-p4/verification.md` §1 — two Material lines on the
regenerated plan's unchanged §Conventions and §Verification Hand-off) was a
**true positive** under this rule. `references/loop-control.md` §2a carries the
same sentence; the fixture of §Offline Arbitration Fixture (scenario A1) is the
evidence. Q-IMPL-HARNESSP3-010 is unaffected — it decides *which dispatches*
feed `regen[N]`, not the granularity of their writes; no further Q-IMPL entry is
added, since this Approved sentence is the record.

The arbitration guarantee is **not** weakened. The pause exists to catch a
reviewer raising new Critical/Material findings on ground the previous round
approved **and the loop did not touch**; a wholesale-regenerated file *was*
touched by the loop. Admitting it removes false positives only and cannot mask a
contradiction about a file the loop left alone.

**Amended 2026-09-22** `[Updated: 2026-09-22]` (REQ-ARB-HARNESSP3-001 as amended): the union gains a third term, `new[N]` — fix-induced ground, both sides of a moved or renamed heading — defined in §Contradiction Classes; the regenerated-is-not-new-ground rule of this section is unchanged and the diff-based rule of REQ-ARB-HARNESSP5-001 (a heading present at `sha_N` with identical bytes stays out) still bounds it.

### Live Exercise of the Union in harness-p4 (REQ-ARB-HARNESSP4-001)

[Added 2026-09-18, harness-p4 — REQ-ARB-HARNESSP4-001; decided at DISCUSS. The
carried REQ-ARB-HARNESSP3-001 closed `fail` = *not exercised* in p3
(`docs/ws/harness-p3/verification.md` §V3): no fix loop regenerated its
deliverable between review rounds, so the union was fixture-evidenced only.]

This cycle exercises §`W_N` Includes Regeneration Writes on a **live** fix loop:

| Step | Contract |
|---|---|
| trigger | the **first** `APPROVE_WITH_FIXES` stage review of the cycle |
| fix dispatch | its `{deliverable_contract}` carries the instruction to **regenerate the deliverable wholesale** (rewrite the artifact, not patch it) |
| expected gate | the next review round's Material or Critical findings **in the regenerated sections** raise **no** class (b) `REVIEW: CONTRADICTION` pause; the rule stays armed for any file the loop left alone (a finding there still pauses) |
| `regen[N]` | retained per §Retained Per-Round State, including the orchestrator-regenerated `docs/requirements/traceability.md` where the stage produced one (`by: orchestrator`) |
| record | `docs/ws/harness-p4/verification.md` §Criteria has an item stating the stage, the round numbers (N, N+1), the regenerated paths, the `regen[N]` entry the gate retained and the observed absence of the pause |
| traceability | the carried `REQ-ARB-HARNESSP3-001` row in `docs/ws/harness-p4/traceability.md` reads `pass` at DONE **on run evidence**; the regenerated aggregate shows the same |

**Duplicate id in the aggregate.** The aggregate carries **both** rows for
`REQ-ARB-HARNESSP3-001` — `harness-p3` `fail` (history) and `harness-p4` `pass`
(authoritative). The authority rule and its consequences for `sdd-gc.py` and
`sdd-verify` are decided in `ws-traceability.md` Q-IMPL-HARNESSP4-001; this spec
only requires that the `harness-p4` row is the one a reader, gc and the DONE
rule consult. **DONE rule of the cycle**: every traced requirement reads `pass`;
nothing closes as a deliberate `fail`; an item that cannot be exercised live is
**descoped at replan**, not failed.

[Re-stated 2026-09-19, harness-p5 — Q-REQ-P5-A; REQ-ARB-HARNESSP5-002. The p4
exercise ran but was **non-discriminating**: the pause it produced keyed on
sections of the regenerated file, which both the diff-based and the
provenance reading could explain, and neither cell in
`docs/ws/harness-p4/traceability.md` could be closed (`verification.md` §Open
Questions). Its acceptance is therefore re-stated **in place**, not inherited
silently: **no pause on findings in changed sections of the regenerated file;
a pause on findings in unchanged sections of it** — closed on the deterministic
offline fixture of §Offline Arbitration Fixture, never on a second live loop.
The `harness-p4` `Verified` cells of REQ-ARB-HARNESSP3-001 and
REQ-ARB-HARNESSP4-001 read `descoped` (REQ-WS-HARNESSP5-001/-002,
`ws-traceability.md`); the `harness-p5` rows read `pass` on fixture evidence and
are authoritative. The requirement text above is otherwise unchanged.]

### §2a Replay Fixture Demonstrates the Derived-Artifact Case (REQ-ARB-HARNESSP4-002)

[Added 2026-09-18, harness-p4 — REQ-ARB-HARNESSP4-002; `docs/ws/harness-p3/verification.md` §V10]

Skill-side text only: `references/loop-control.md` §2a's replay fixture must
exercise the Q-IMPL-HARNESSP3-017 clause it sits beneath —

- its `regen[1]` entry lists `docs/requirements/traceability.md §(matrix)`
  labelled **`by: orchestrator`** (orchestrator regeneration), distinct from the
  leaf-written `docs/ws/<id>/traceability.md` entry;
- finding `M3` writes its path **in full** (`docs/requirements/traceability.md`
  or `docs/ws/<id>/traceability.md`), so a reader can tell which of the two files
  it is on; no bare `traceability.md` remains in the fixture's finding lines.

Today `regen[1]` names only the per-workstream file and `M3` names
`traceability.md` bare, so the derived-artifact case is demonstrated only by an
ambiguity. The fixture's expected outcome (no pause on the regenerated file,
pause on an untouched one) is unchanged.

### Offline Arbitration Fixture — Scenarios A1–A3 (REQ-ARB-HARNESSP5-002, REQ-ARB-HARNESSP5-001, REQ-ARB-HARNESSP5-003)

[Added 2026-09-19, harness-p5 — decided at DISCUSS (kickoff §Scope item 1): the
carried ARB rows close by spec decision plus a frozen fixture, never a second
live loop. Runner placement per Q-REQ-P5-H.]

**Fixture** — `tools/fixtures/arbitration-harness-p4-regen-2026-09-19/`, a
**git capture** of the p4 implement-stage regeneration: `before.md` and
`after.md` are `git show 82d0af0:docs/ws/harness-p4/plan.md` and
`git show 3772574:docs/ws/harness-p4/plan.md`, the real before/after images of
the regenerated deliverable, not a hand reconstruction; the three round and
dispatch files are authored from `docs/ws/harness-p4/verification.md` §1 and
plan O1. `tools/fixtures/README.md` records the capture per fixture — naming
**both shas** and the **sha256 of each file** — and the two shas are provenance
only: the captured bytes live in the fixture, so it stands if they become
unreachable:

| File | Content |
|---|---|
| `before.md`, `after.md` | the plan before and after the wholesale regeneration, captured at `82d0af0` and `3772574` — a broad diff (35 hunks, `§(preamble)` through `§Replan Triggers`) that nonetheless discriminates because the two sections round 2 keys on, `§Conventions` and `§Verification Hand-off`, are **byte-identical** across the pair |
| `round-1.txt` | `VERDICT: APPROVE_WITH_FIXES`; its C/M lines keyed on the two changed sections |
| `round-2.txt` | two Material lines keyed on the plan's **unchanged** `§Conventions` and `§Verification Hand-off`, confined to the regenerated file |
| `dispatch.txt` | observed writes `{docs/ws/harness-p4/plan.md}`, `regenerate: true`, `by: leaf` |

**Runner** — three scenarios of `tools/sdd-scope-check-selftest.py --self-test`
(default per Q-REQ-P5-H: it already holds `resolve_sections()` and the
temp-repo harness and is a verify gate; a separate
`tools/sdd-arbitrate-selftest.py` with identical assertions is acceptable at
plan time). The runner parses both rounds with the key rule of §Retained
Per-Round State (ordinal strip included), computes `W_1` from the
`before.md → after.md` diff via `resolve_sections()`, and applies the class
(b)/(c) table of §Contradiction Classes through one **pure** helper:

```
arbitrate(round_n, round_n1, w_n) -> (class | None, annotated_keys)
    # no git, no I/O; annotated_keys = the round-N+1 keys with k ∉ K_N and k ∉ W_N (class b)
```

| Scenario | Builds | Diff-based `W_1` (this spec) | Provenance `(file, *)` (rejected) |
|---|---|---|---|
| **A1** p4 case — the discriminating one | round 2 on the two **unchanged** sections of the regenerated plan | `class b`, **two** annotated keys | no token |
| **A2** B8 case | round 2 findings in **changed** sections only | no token | no token |
| **A3** control | one round-2 key on an **untouched second file** | `class b`, one key | `class b`, one key |

A1 prints the provenance column **alongside** the diff-based result so the
rejected reading is visible in the same run; A2 shows the REQ-ARB-HARNESSP3-001
false positive stays removed; A3 shows the rule stays armed for a file the loop
left alone. The key parser resolves a round line with and without a `C1`/`M2`
ordinal to the same key (REQ-ARB-HARNESSP5-003). Mutation checks: deleting one
`round-2.txt` line, or flipping `§Conventions` to a changed section in a temp
copy of `after.md`, makes A1 fail.

**Closure** — this run is the evidence `verification.md` §Criteria records for
both carried rows; `docs/ws/harness-p5/traceability.md` reads `pass` for
REQ-ARB-HARNESSP3-001 and REQ-ARB-HARNESSP4-001 at DONE, and the regenerated
aggregate carries their `harness-p3` `fail` / `harness-p4` `descoped` rows as
history (`ws-traceability.md` §Legal `Verified` Cell Values). Sized at nine
files (selftest, five fixture files, README, this spec, `loop-control.md`) plus
the workstream's `traceability.md`.

## Verification

### Automated

- `test_key_parse`: `- C1: x — [docs/spec/x.md:§A] — affects [REQ-X-001]` →
  `(docs/spec/x.md, §A, {REQ-X-001})`; `[x.md:§3. A]` and `[x.md:§A]` → the
  same key (leading-ordinal strip, REQ-ARB-HARNESSP5-003); a Material line with `affects —` → `∅`;
  an unparsable ref → `(?, ∅)`.
- `test_class_b_fires_on_untouched_section`: round 1 names §A; fix wrote only
  §A; round 2 raises C1 at §C → `REVIEW: CONTRADICTION (… class b)`; the same
  fixture with round 2 at §A → no token.
- `test_class_b_regenerated_unchanged_section` — fixture scenario **A1**:
  wholesale regeneration whose diff leaves `§Conventions` and `§Verification
  Hand-off` byte-identical; round 2 keyed on them → `class b`, two annotated
  keys; the provenance column prints no token (REQ-ARB-HARNESSP5-001, -002).
- `test_class_b_not_raised_in_regenerated_changed_sections` — scenario **A2**:
  round-2 findings only in changed sections → no token either way
  (REQ-ARB-HARNESSP3-001, REQ-ARB-HARNESSP5-002).
- `test_class_b_untouched_second_file` — scenario **A3**: one key on a file
  the loop never touched → `class b`, one key under both readings
  (REQ-ARB-HARNESSP4-001 re-stated, REQ-ARB-HARNESSP5-002).
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
- [ ] §Retained Per-Round State and §Contradiction Classes carry the union and the regenerated-not-patched rule, and `references/loop-control.md` §2a's state schema and `W_N` definition match (REQ-ARB-HARNESSP3-001)
- [ ] `docs/spec/adversarial-verify.md` §Fix-Loop Interaction carries the cross-reference (REQ-ARB-HARNESSP3-001)
- [ ] A fixture in which round 1 `APPROVE`s, a pipeline re-dispatch regenerates the deliverable, and round 2 raises Material findings in regenerated sections yields **no** `REVIEW: CONTRADICTION` pause (REQ-ARB-HARNESSP3-001)
- [ ] The same fixture with the findings in a file the loop never touched still pauses as class (b) (REQ-ARB-HARNESSP3-001)
- [ ] The first `APPROVE_WITH_FIXES` fix dispatch of the harness-p4 cycle carries the regenerate-wholesale instruction in its `{deliverable_contract}`; the following review round's gate renders `VERDICT:` with no `REVIEW: CONTRADICTION` line although it raised findings in the regenerated file; `docs/ws/harness-p4/verification.md` §Criteria records stage, round numbers, regenerated paths and the retained `regen[N]`; the carried `REQ-ARB-HARNESSP3-001` row in `docs/ws/harness-p4/traceability.md` reads `pass` at DONE and the aggregate shows both rows with the `harness-p4` row authoritative (REQ-ARB-HARNESSP4-001, REQ-ARB-HARNESSP3-001)
- [ ] `grep -n 'docs/requirements/traceability.md' skills/sdd-orchestrate/references/loop-control.md` hits inside the §2a fixture's `regen[1]` block with an orchestrator-regeneration label; no bare `traceability.md` remains in the fixture's finding lines; `python3 tools/sdd-skill-lint.py` exits 0 (REQ-ARB-HARNESSP4-002)
- [ ] `grep -n 'byte-identical' docs/spec/arbitrated-handoff.md skills/sdd-orchestrate/references/loop-control.md` hits inside §`W_N` Includes Regeneration Writes and §2a respectively with matching wording; scenario A1 yields `class b` with two annotated keys under the diff-based rule and no token under provenance, printed side by side; no Q-IMPL-HARNESSP5-* entry is needed (the Approved sentence is the record); `python3 tools/sdd-skill-lint.py` exits 0 (REQ-ARB-HARNESSP5-001)
- [ ] `python3 <runner> --self-test` — where `<runner>` is whichever of `tools/sdd-scope-check-selftest.py` (the Q-REQ-P5-H default) or `tools/sdd-arbitrate-selftest.py` the plan selects, named once in the plan and used verbatim by `verification.md` — exits 0 with A1–A3 listed and A1's provenance column printed alongside; deleting one `round-2.txt` line or flipping `§Conventions` to a changed section in a temp copy makes A1 fail; `tools/fixtures/README.md` labels the fixture a **git capture** naming both shas (`82d0af0`, `3772574`) with its files' sha256; `verification.md` §Criteria records the run as the evidence for both ARB rows, which read `pass` at DONE in `docs/ws/harness-p5/traceability.md` and in the regenerated aggregate (REQ-ARB-HARNESSP5-002, REQ-ARB-HARNESSP3-001, REQ-ARB-HARNESSP4-001)
- [ ] The key table's `section` row states the leading-ordinal strip rule and Open Question 3 reads closed, pointing at that row; `references/loop-control.md` §2a agrees; the A1–A3 key parser implements it and a round line with and without the ordinal resolves to the same key in `--self-test`; `python3 tools/sdd-gc.py --report` raises no new finding on this spec (REQ-ARB-HARNESSP5-003)
- [ ] §Retained Per-Round State's fenced schema shows `round[N]`, `fix[N]` and `regen[N]` with the `W_N` union; its text and `references/loop-control.md` §2a agree on the definition (side-by-side read at specs); `python3 tools/sdd-gc.py --report` raises no new finding on this spec (REQ-ARB-HARNESSP4-003)

**Pipeline-observability (2026-09-22, arbitration)**

- [ ] `python3 plugins/sdd/tools/scope-check-selftest.py` exits 0 with
  scenario A4: a round-N+1 finding under a heading absent at `sha_N`
  classifies as an ordinary finding in `W_N`, and a control finding under a
  heading present at `sha_N` and unwritten by the loop still classifies
  class (b); in a temp copy with the heading-existence clause removed A4 flips
  to class (b) and the self-test exits non-zero; A1–A3's outputs are unchanged
  (REQ-ARB-PIPELINEOBSERVABILITY-001, REQ-ARB-HARNESSP2-002 as amended).
- [ ] The `W_N` line of §Retained Per-Round State in this spec and in
  `skills/orchestrate/references/loop-control.md` §2a both carry the third term (`new[N]`) —
  `sed -n '/^### Retained Per-Round State/,/^### Contradiction/p' docs/spec/arbitrated-handoff.md | grep -c 'new\[N\]'`
  reads ≥ 1 and `grep -c 'new\[N\]' plugins/sdd/skills/orchestrate/references/loop-control.md`
  reads ≥ 1 (0 before this delta)
  (REQ-ARB-PIPELINEOBSERVABILITY-001, REQ-ARB-HARNESSP3-001 as amended).
- [ ] A4's fixture includes a **moved** heading (present under a new name at
  `sha_{N+1}`, absent at `sha_N`) and shows both the old and the new
  `(file, §heading)` in `W_N` (REQ-ARB-PIPELINEOBSERVABILITY-001).

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
- [Added 2026-09-19, harness-p5] `ws-traceability.md` §Legal `Verified` Cell
  Values admits `descoped` for the carried p4 rows this spec closes; the
  `harness-p5` rows are authoritative (Q-IMPL-HARNESSP4-001 authority rule
  unchanged). `harness-write-scope.md` §Observation's `resolve_sections()` is the
  function A1–A3 call; its `(path, *)` fallback keeps the missing-diff meaning.
- **No unresolved contradictions.**

**harness-p5 pass (2026-09-19).** No extractable type definitions;
`arbitrate(round_n, round_n1, w_n)` is a pseudocode signature whose operands
are the sets of §Retained Per-Round State. `class b`, `(file, *)` and `W_N` keep
their single definitions; the fixture scenario ids A1–A3 do not collide with the
scope self-test's F-series or the commit fixtures C1–C6
(`harness-commit-fidelity.md`).

**harness-p3 pass (2026-09-18).** No extractable type definitions in
arbitrated-handoff.md — `W_N` is a set-valued definition in pseudocode, not a
language type, so the extraction step reports no definitions explicitly.
`sections(...)` is the section-resolution function of REQ-ARB-HARNESSP2-005,
defined in this spec and unchanged; `REVIEW: CONTRADICTION`, class `(b)` and
`(file-level)` keep their existing meanings and render identically in
`docs/spec/adversarial-verify.md` §Fix-Loop Interaction.

## Open Questions

1. **Class (b) false-positive rate** (`index.md` Open Questions): a
   legitimately new Critical the first reviewer missed pauses the loop.
   Default: accept — the pause costs one operator decision and is the intended
   ROUTE_TO_HUMAN; telemetered via `contradiction_class`.
2. **Use section resolution to automate the `ADVISORY` hint** (hunks under
   `## Implementation Questions` → `IN`)? Default: not this cycle; the hint text
   stays, the operator verifies.
3. **Heading normalisation across `§Name` variants** (`§3. Foo` vs `§Foo`) —
   **closed 2026-09-19** (REQ-ARB-HARNESSP5-003): the leading-ordinal strip
   `\d+[.)]?\s*` is now a rule of the key table (§Retained Per-Round State,
   `section` row), matching `references/loop-control.md` §2a; exercised by the
   A1–A3 key parser.

## Implementation Questions

### Q-IMPL-HARNESSP3-009: `regen[N]` is a sibling set, not a rename of `fix[N]`
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`W_N` Includes Regeneration Writes
**Decision**:

REQ-ARB-HARNESSP3-001 leaves the shape as an implementation choice. Decision:
keep `fix[N]` meaning the fix dispatch's writes and add a sibling `regen[N]` for
regeneration writes, with `W_N := sections(fix[N]) UNION sections(regen[N])`.
Rationale: the two sets have different provenance in the telemetry record and in
the ledger, and keeping them separable costs nothing while a rename would make
the distinction unrecoverable.
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP3-010: "Regeneration of the stage deliverable" means a pipeline re-dispatch of the same stage
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`W_N` Includes Regeneration Writes
**Decision**:

The regeneration writes admitted into `W_N` are those of an
orchestrator-dispatched leaf **for the same stage** between rounds N and N+1 —
not writes from a different stage's leaf, and not an operator's manual edit,
which remains outside the loop's write set and therefore still able to raise a
class (b) pause.
**Date**: 2026-09-18 (specs stage)

### Q-IMPL-HARNESSP3-017: A derived artifact regenerated by the orchestrator counts as a regeneration write
**Tier**: 2 (spec ambiguity)
**Spec reference**: §`W_N` Includes Regeneration Writes; Q-IMPL-HARNESSP3-010
**Decision**:

Q-IMPL-HARNESSP3-010 admits the writes of a pipeline re-dispatch of the same
stage. The §B8 replay exposed one case it does not name: the shared aggregate
`docs/requirements/traceability.md` is regenerated by the **orchestrator** after
the gate, wholesale and byte-deterministically, from the per-ws file the stage
leaf just wrote. Decision: such a derived regeneration enters `regen[N]` with the
leaf write it derives from. Rationale: it is machine-derived bookkeeping of the
same stage's deliverable, not an operator edit, so treating it as untouched
ground would reintroduce exactly the false positive REQ-ARB-HARNESSP3-001
removes. An operator's manual edit of the aggregate remains outside `W_N`.
**Date**: 2026-09-18 (implement stage, Chunk 3)


## Pipeline-Observability Amendment (2026-09-22, REQ-ARB-PIPELINEOBSERVABILITY-001; REQ-ARB-HARNESSP2-002, REQ-ARB-HARNESSP3-001 amended)

[Added 2026-09-22, workstream `pipeline-observability` —
RS-PIPELINEOBSERVABILITY-001 §Q3 "The stale cross-reference", R7, §Mechanical
pin R7. Observed defect: both class-(b) pauses of the consumer-geometry
research stage fired on a cross-reference to a section the fix had just
moved.]

**Where the contract lives** (REQ-REQ-PIPELINEOBSERVABILITY-001 (b), 2026-09-22): this section is the record of *why* and states no contract of its own; the contract is in the sections of record named here, each edited in place under a `[Updated: 2026-09-22]` marker, and its acceptance criteria sit in this spec's own Acceptance Criteria section under the same date. §Retained Per-Round State's schema block carries the `W_N` line with its third term `new[N]` (edited in place, as REQ-ARB-HARNESSP4-003 did for `regen[N]`); §Contradiction Classes carries the definition and decision procedure of fix-induced ground (REQ-ARB-PIPELINEOBSERVABILITY-001; REQ-ARB-HARNESSP2-002 as amended — class (b)'s "pairs written by the intervening fix" now includes it); §`W_N` Includes Regeneration Writes records that the union gains the term (REQ-ARB-HARNESSP3-001 as amended). Left consistent and not reopened: §Section Resolution of Fix Hunks (the diff-keyed resolution is exactly why the term is needed), §`REVIEW: CONTRADICTION` Pause, §Third Opinion, §Review Key on Material Lines, REQ-ARB-HARNESSP5-001's diff-based rule, §Offline Arbitration Fixture (A1–A3 unchanged; A4 added beside them).

**Why a third term rather than a wider class (b)**: a diff's hunks are keyed on the heading they sat under *before* the fix, so a heading the fix created is absent from `fix[N].written` although the fix wrote it — both class-(b) pauses of the consumer-geometry research stage fired on exactly this. Nothing is reversed, so this is not class (a), and the `(file-level)` degradation is unchanged.
