---
id: RS-HARNESSP6-001
workstream: harness-p6
status: Complete
date: 2026-09-20
last_updated: 2026-09-20
questions:
  - "Q1 — the shared-spec staleness sub-class: which rule change retires the 44 warnings, and what real staleness does each option then miss?"
  - "Q2 — how is git-state mutation by a read-only leaf observed, with a comparand that fires on `git stash` but not on a normal implement leaf or a fan-out merge?"
  - "Q3 — what countability rule makes the Q-IMPL sweep fence-symmetric without re-breaking `qimpl-undefined`?"
  - "Q4 — how is L2, the cross-layer convergence signal, built (cluster rule, window, rendering, cost and reduced form)?"
budget: "One spike, <= 45 tool calls; desk research over existing specs/references/tools plus read-only `sdd-gc.py --report` and `sdd-skill-lint.py`; two read-only probes."
---

# Research: Harness hardening, part 6 (terminal) — RS-HARNESSP6-001

## Questions

Exactly the four the kickoff asks (`docs/ws/harness-p6/kickoff.md` §Research
questions). Items (1), (4), (6) and (7) of the scope paragraph were decided at
DISCUSS and are not re-derived here; item (9), the deferral-backlog sweep, is
enumerated in §Deferral-Backlog Sweep below.

Two framings are fixed by operator direction and are **not** re-opened by this
spike: L2 ships in this cycle (Q4 settles *how*, not *whether*), and this cycle
is terminal — nothing may be queued to a successor cycle.

## Decided at DISCUSS (restated unchanged — requirements inherit these)

Copied from `docs/ws/harness-p6/kickoff.md` §Decided at DISCUSS at HEAD
`ac0fb43`, unaltered:

- Item (3) is settled as an **observable check**, not contract wording alone;
  the spike settles the mechanism, not whether to enforce.
- Items (1), (4), (6) and (7) are mechanical and need no research; they go
  straight to requirements as specified in §Scope.
- Items (1) and (2) are **two rules**, not one — they address disjoint halves
  of the 63 warnings and have different false-negative profiles.
- **L2 ships in this cycle** — reversing the harness-p3/-p4/-p5 deferrals on
  explicit operator direction. It is implemented as an orchestrator-derived
  gate signal, adds no finding field and is not a fifth layer. Q4 settles the
  mechanism; a Q4 answer of "defer again" is out of bounds.
- **This cycle is terminal for the series, enforced by a no-carry-forward DONE
  rule.** At the DONE gate, `docs/ws/harness-p6/verification.md` §Next Steps
  MUST contain no item phrased as carried, deferred, or queued to a next or
  later cycle. Anything found during the cycle is either fixed inside it or
  closed as **won't-do with its reasoning recorded** in
  `docs/requirements/index.md` §Out of Scope as a settled exclusion — not as a
  deferral. A finding too large to fix in-cycle triggers a **replan**, not a
  successor workstream.
- **§Out of Scope is swept, not grown.** When this cycle closes, no entry in
  `docs/requirements/index.md` §Out of Scope may read "deferred to a later
  cycle". Entries become either settled exclusions with reasoning, or scope.
- Terminality has one honest limit, recorded here so no downstream stage
  overstates it: it guarantees **no carried work**, not that no future defect
  can ever be found. A red round or review may still surface a genuine new
  defect; the rule is that such a defect is handled in this cycle.
- DONE rule: every requirement traced by this workstream `pass`; nothing
  closes as a deliberate `fail`; an item that cannot be exercised is descoped
  at replan.
- Scope priority for the plan is the order in §Scope, so a `stop` partway
  leaves the two gc rules landed first. L2 is sequenced **last** among the
  implementation items despite its importance, because it is the item most
  likely to trigger a replan and the other eight should be landed before that
  risk is taken.

## Measured baseline (this branch point, 2026-09-20)

`python3 tools/sdd-gc.py --report`: 63 warnings, 25 info, and **1 fail** —
`[index-research]` on this spike's own directory (`RS-HARNESSP6-001-…/ has no
index row`). That fail is an artefact of the empty directory existing before
`docs/research/index.md` gained its row; adding the row clears it. The row is
outside this spike's write scope, so it is an orchestrator follow-up at the
research gate, recorded in §Open Questions.

All 63 warnings are `[stale-chain]`, and they split cleanly into the two
sub-classes the kickoff separates:

| Sub-class (gc message) | Count | Downstream files |
|---|---|---|
| `spec older than requirement <RID>` (Q1) | 44 | `docs/spec/telemetry.md` 42, `docs/spec/adversarial-verify.md` 2 |
| `plan older than a traced spec` (item 1) | 10 | `docs/ws/harness-p3/plan.md`, `docs/ws/harness-p4/plan.md` |
| `plan older than a traced requirement category file` (item 1) | 9 | the same two closed-workstream plans |

Item (1) — skip a workstream whose `verification.md` is `status: pass` —
therefore retires exactly the 19 plan-level lines (both sub-kinds, on two
`status: pass` workstreams). Item (2) is the 44. The split is confirmed and the
two rules are disjoint, as decided.

Decisive extra measurement for Q1: the 44 lines fan out from only **three**
(downstream, upstream-file) pairs —

```
39  docs/spec/telemetry.md          <- docs/requirements/functional/telemetry.md
 3  docs/spec/telemetry.md          <- docs/requirements/integration/skill-lint.md
 2  docs/spec/adversarial-verify.md <- docs/requirements/integration/skill-lint.md
```

`python3 tools/sdd-skill-lint.py` → `OK: 25 file(s) clean`.

---

## Findings

## Q1 — The shared-spec staleness sub-class

**Classification: code (`tools/sdd-gc.py`) plus design-decision-for-requirements
(which severity the class carries).**

**Confidence**: option E (fold the per-id fan-out into one finding per pair)
**High** — the fan-out was counted directly from `--report` output and the
39/3/2 split over three (spec, category-file) pairs reproduces exactly; the
zero-false-negative claim follows from the fold being a presentation change
that drops no comparison. Option C (carry the folded finding at `info`)
**Medium** — it is a severity judgement about how much salience the class
deserves, not a measurement, and reasonable operators could disagree; it is
reversible in one line if the class ever hides a real staleness.

### What the rule does today

`sweep_stale()` walks each plan's `traces to` specs, reads each spec's
frontmatter `requires:` list, maps each requirement id to the category file that
defines it (`category_file_of()`), and emits one warning per
`(spec, requirement id)` pair whose category file's `last_updated:` is greater
than the spec's.

**A correction the requirements stage must carry forward:** the kickoff's option
*"compare against only those requirement IDs the spec actually `requires:`"* is
**already the implemented behaviour** — it is the `s_reqs` loop in
`sweep_stale()`. It retires zero warnings because it is the status quo. The real
imprecision is one level down: the comparand for a requirement id is its
**category file's** date, which moves whenever *any* requirement in that file
moves. There is no per-requirement date anywhere in the corpus (the category
files carry no per-entry date marker), so a per-requirement comparand has no
data source short of git history, which `--report` does not otherwise touch.

### Evidence that this class is a *structural* false positive

`docs/requirements/functional/telemetry.md` last moved in commit `44c5225`,
*"docs(spec): harness-p5 chunk 7 — spec-text housekeeping and split pointers"*
(2026-09-20). `docs/spec/telemetry.md` is dated 2026-09-19 and its content is
current — harness-p5's own verification says so and routed the finding `record`.
Under the v4 shared corpus this is not an accident but the design: requirements
are shared and per-cycle deltas are appended to the *same* category files, so
every workstream that adds one requirement re-dates the category file for
**every** spec that `requires:` any id in it. The class will therefore recur
every cycle, at a multiplicity equal to the spec's `requires:` length (39 for
`telemetry.md`).

### The options, each with warnings retired *and* real staleness then missed

| Option | Warnings retired (of 44) | Real staleness then missed |
|---|---|---|
| **A. Bump the spec date through `sdd-specs` whenever it fires** (status quo remedy) | 44, until the next requirement edit re-fires them | **All of it.** The date stops meaning "reviewed against its requirements" and starts meaning "last silenced". Any genuinely stale shared spec is silenced by the same gesture. Rejected by harness-p5's DONE note and barred by this kickoff's §Out of scope. |
| **B. Compare only against requirement ids the spec `requires:`** | **0 — already implemented** | Nothing new; it is the status quo, so no change is available here. |
| **C. Demote the shared-spec case to `info`** | 44 from the warn class (repo 63 warn → 19 warn; info 25 → 69, or → 28 combined with E) | A genuinely stale shared spec — a requirement whose *contract* changed under a spec that was never updated — now prints at the same severity as `qimpl-unreferenced`, i.e. below the attention the DONE routing gives warnings. The finding is still printed and still counted, so the loss is one of **salience, not visibility**. |
| **D. Per-requirement-id staleness comparison** (compare against the date the *individual requirement entry* last changed) | All 44 here, and it would keep firing on a genuine per-entry change | Structurally misses nothing, but buys precision with two new failure modes: it needs either a per-entry date marker maintained by hand across 24 category files (a marker nobody bumps is a silent false negative on **every** requirement), or `git log -L` per requirement per spec — history inside `--report`, which the tool deliberately avoids — plus ~40–60 lines of new code. |
| **E. Fold the per-id fan-out into one finding per (downstream, upstream-file) pair** *(not in the kickoff's list; added by this spike)* | 41 of 44 lines (44 → 3 findings, each naming its ids) | **Nothing.** The rule fires on exactly the same facts; only line multiplicity changes. Every (spec, category file) staleness relation still surfaces at warn. |

### Recommendation

**E then C: fold the fan-out (E), then carry the folded shared-spec finding at
`info` (C).** Reject A (barred, and it destroys the signal), B (no-op) and D
(its precision gain is over a comparand that is already structurally noisy, at
the highest cost and with a git-history dependency the tool otherwise avoids).

Rationale for the pairing: E is the change with a provably zero false-negative
cost, and alone it takes the repo from 63 to 22 warnings. C then addresses the
residual salience problem honestly — under a shared corpus this relation is
expected rather than defective, so warn is the wrong severity for the *class*,
not for the *instances*. Together: 63 warnings → 19 (all of which item (1) then
retires), with three `info` lines preserving the full relation. Nothing is
silenced by a date bump.

**Cost in files touched (4):** `tools/sdd-gc.py` (`_stale` gains a grouping
accumulator and a severity argument for the spec←requirement call site;
`sweep_stale()` emits once per pair after the id loop — roughly 15 lines — plus
the self-test fixture's `ewarn["stale-chain"]` expectations, which count
per-line today); `docs/spec/drift-sweep.md` (sweep-table row 7: severity and the
folded message shape); `docs/requirements/integration/drift-sweep.md` (one new
`REQ-GC-HARNESSP6-*` row); `docs/requirements/index.md` (Files-table date and
delta note). `CLAUDE.md` is **not** touched — it does not state the per-line
shape.

---

## Q2 — Observing git-state mutation by a read-only leaf

**Classification: mechanical (spec/reference text) with a small code surface in
`tools/sdd-scope-check-selftest.py`. No change to `tools/sdd-gc.py`; at most one
optional `REQUIRED` row in `tools/sdd-skill-lint.py`.**

**Confidence**: **Medium-High** — the one-directional porcelain delta is read
directly from the observation commands, and the comparand was checked on paper
against all three cases the kickoff names (`git stash`, a normal implement
leaf, a fan-out merge). It is derived from contract text and **not exercised
against a live dispatch**: the stash case is argued, not replayed. The
self-test scenario named under Cost is what would raise this to High, and
should be treated as required work rather than optional.

### Why the incident was invisible

The observation window (`skills/sdd-orchestrate/references/write-scope.md` §3)
is three commands: (a) a **forward** porcelain delta — "lines in `scope.after`
not in `scope.before`"; (b) the committed delta
`git diff --name-status HEAD_before HEAD_after`; (c) an ancestry check.
`git stash` **removes** lines from the porcelain output and leaves `HEAD`
untouched, so it is invisible to all three: (a) is one-directional by
construction, (b) sees no commit, (c) sees no rewrite. That is exactly the
harness-p5 incident — nine dirty files left the tree and `SCOPE:` printed
`CLEAN`.

### Candidate state, and which of it moves during a *legitimate* dispatch

| Candidate | Moves legitimately inside a dispatch window? | Verdict |
|---|---|---|
| `HEAD` sha | Yes — an implement leaf commits; a fan-out leaf commits on its branch | Already covered by (b)/(c); not a new comparand |
| Ancestry of `HEAD_after` from `HEAD_before` | No | Already covered as `HISTORY_REWRITE` |
| Current branch (`git rev-parse --abbrev-ref HEAD`) | No. Sequential leaves run at the workstream branch in the repo root; fan-out leaves run in their own worktree on their own branch, and the snapshot is taken per-worktree. The orchestrator's merge happens **after** the window ("AFTER return, BEFORE the orchestrator's own commit") | **Usable** |
| Stash count (`git rev-list --walk-reflogs --count refs/stash`, 0 when the ref is absent) | No. No leaf template, no fan-out step and no orchestrator gate step stashes | **Usable — the direct signal for the incident** |
| `ORIG_HEAD` | Set by merge/reset/rebase. Provisioning (`git merge --ff-only base`) happens **before** `snapshot(before)`; the fan-out merge is outside the window | Usable but derivative; include in the tuple, never rely on it alone |
| **Reverse porcelain delta** — lines in `scope.before` absent from `scope.after` | Yes, in exactly one legitimate way: a leaf **commits** a path that was already dirty at snapshot time | **Usable once that one case is subtracted** |

### The comparand

> **`GIT_STATE` finding.** After a dispatch, the orchestrator flags git-state
> mutation when either (i) the **stash count**, the **current branch** or
> **`ORIG_HEAD`** differs between `snapshot(before)` and `snapshot(after)`; or
> (ii) the **reverse porcelain delta is non-empty after subtracting the
> committed delta (b)** — a path that was dirty before the dispatch is no
> longer dirty and does not appear in
> `git diff --name-status HEAD_before HEAD_after`.

Checked against the three cases the kickoff names:

- **The `git stash` case → `VIOLATION`.** The stash count goes 0 → 1 (clause i)
  *and* nine paths leave the porcelain output with no commit explaining them
  (clause ii). Either clause alone catches it, which is what makes the comparand
  robust: a leaf that pops the stash back but leaves the ref still trips (i);
  a leaf that drops the ref still trips (ii).
- **A normal implement leaf → `CLEAN`.** It *adds* porcelain lines (the forward
  delta, already handled) and may commit. Any path it commits that was dirty
  beforehand leaves the reverse delta but appears in (b) and is subtracted.
  Stash count, branch and `ORIG_HEAD` are untouched. In practice
  `snapshot(before)` is clean anyway — the orchestrator commits at each gate —
  so the reverse delta is usually empty by construction.
- **A fan-out merge → `CLEAN`.** The merge is an orchestrator step outside any
  leaf's observation window; inside its window a leaf sees only its own worktree
  and branch. Even if a merge fell inside a window: git refuses to merge over
  conflicting dirty paths, so it clears no dirty state, and a merge commit is a
  descendant, so (c) still passes.

### Window and rendering

- **It rides the existing `snapshot(before)`/`snapshot(after)` window.** No
  second window is needed: the extra reads
  (`git rev-list --walk-reflogs --count refs/stash`,
  `git rev-parse --abbrev-ref HEAD`,
  `git rev-parse --verify --quiet ORIG_HEAD`) are taken alongside the existing
  `git status --porcelain` call at both ends — three plumbing commands per
  snapshot.
- **It renders as a member of the existing `SCOPE:` family, not a new token.**
  It is a finding **line** inside the write-scope block, exactly parallel to the
  existing `HISTORY_REWRITE` line, and it counts into
  `SCOPE: VIOLATION (N paths)`:

  ```
    GIT_STATE  stash 0 -> 1; 9 paths left the worktree with no commit (docs/spec/telemetry.md, ...)
    SCOPE: VIOLATION (1 path)
  ```

  Reasons to prefer this over a new token: the REQ-ORCH-034 order is unchanged;
  `SCOPE:` is already the load-bearing, lint-guarded token the orchestrator
  branches on; and no new `REQUIRED` row pair is strictly required. Options on
  the finding: `restore (git stash pop) │ accept (note) │ stop` — unlike
  `HISTORY_REWRITE`, a stash is recoverable, so `stop`-only would be needlessly
  harsh — with `proceed` unavailable while it is unresolved, per the existing
  `OUT`-path rule.

**Cost in files touched (5):**
`skills/sdd-orchestrate/references/write-scope.md` (§3 gains the extra reads and
the reverse-delta subtraction; §5 gains the `GIT_STATE` line and its options;
§8 the options summary); `docs/spec/harness-write-scope.md` (the contract);
`docs/requirements/functional/harness-boundaries.md` (one new
`REQ-HARN-HARNESSP6-*`); `tools/sdd-scope-check-selftest.py` (a scenario group:
stash-with-pop, stash-and-drop, implement-leaf-commits-a-dirty-path negative,
fan-out-merge negative); optionally `tools/sdd-skill-lint.py` if the `GIT_STATE`
line gets its own `REQUIRED` row — recommended only alongside scope item (4)'s
`PLAN:` row, so the two share one lint change.

---

## Q3 — A countability rule for the Q-IMPL sweep

**Classification: code (`tools/sdd-gc.py`), with accompanying spec text.**

**Confidence**: **High** — probe 1 enumerated all 82 definition ids (82
unfenced, 0 fence-only, 2 dual-site) and probe 2 ran a patched copy of gc with
the definition scan routed through `visible_lines()`, producing byte-identical
report output (1 fail / 63 warn / 25 info). Both probes were re-run
independently and reproduced. The `qimpl-undefined` non-regression is not a
judgement but a consequence: regressing it requires a fence-only-defined id,
and there are none.

### Probe result — the premise needs correcting, and the fix is cheaper than feared

Two read-only probes were run; neither mutated this repository's working tree or
git state.

1. A fence-aware scan of every `### Q-IMPL-…` heading under `docs/spec/`:
   **82 definition ids, and all 82 have at least one *unfenced* definition. Zero
   ids are defined only inside a fence.** Exactly two ids have two definition
   sites, one fenced and one not:
   - `Q-IMPL-001` — `docs/spec/chunk-close-review.md:261` (unfenced, real) and
     `docs/spec/deviation-protocol.md:101` (fenced illustration);
   - `Q-IMPL-002` — `docs/spec/deviation-protocol.md:110` (fenced illustration)
     and `docs/spec/milestone-plans.md:245` (unfenced, real).
2. A patched copy of `tools/sdd-gc.py` under `$TMPDIR` — `sweep_qimpl()`'s
   definition scan routed through `visible_lines()` — run `--report --root .`
   against this repository: **identical output, 1 fail / 63 warnings / 25 info.**

So making the two sides symmetric **un-defines no id**. The format illustrations
keep working because the ids they illustrate are ids that real entries define
elsewhere. The only behavioural change is which *site* the `qimpl-broken-ref`
sweep reads for `Q-IMPL-002`: today `defs.setdefault()` binds it to the fenced
illustration (`deviation-protocol.md` sorts before `milestone-plans.md`); after
the fix it binds to the real entry at `milestone-plans.md:245`. Probe 2 shows
that raises no new warning — that entry's `**Spec reference**` resolves.

### The rule

> **Q-IMPL countability (amended).** A **definition** is an `^### Q-IMPL-…`
> line under `docs/spec/**` that lies **outside a fenced block** — i.e. it is
> collected through `visible_lines()`, the same filter the reference side
> already uses. A heading inside a fence defines nothing and references nothing.
> Consequently an id used in a fenced **format illustration** must be either
> (a) an id that a real, unfenced entry defines elsewhere in the corpus — the
> present convention, `Q-IMPL-001` and `Q-IMPL-002` — or (b) one of the
> placeholder ids/prefixes the tool already excludes (`Q-IMPL-NNN`, `Q-IMPL-1`,
> the `ISSUE42`/`ISSUE57` tokens).

Rejected alternatives and why: an **explicit opt-in marker on the illustration
block** and a **whitelist of illustration ids** both create an allowlist, which
`CLAUDE.md` §Quality Checks explicitly says does not exist and which
`deviation-protocol.md` §Q-IMPL Entry Format re-states ("the gc rule is
unchanged and there is no allowlist"); an **info-fence language tag** makes
countability depend on a markdown attribute no other sweep reads, so editing a
fence's tag for rendering reasons would silently change gc behaviour;
**accepting the asymmetry** leaves the live defect where a fenced heading
anywhere under `docs/spec/**` defines an id that nothing can ever reference
(references in fences are skipped) — which is how the harness-p5 red round found
it.

### Check against `qimpl-undefined` (the criterion the rule must not re-break)

`qimpl-undefined` fires on ids that are **referenced but in no `defs`**.
Removing fenced headings from `defs` can only turn a reference into `undefined`
if some id is **fence-only defined** — probe 1 shows there are none, and probe 2
confirms the fail/warn/info counts are unchanged. The fence-skipping behaviour
recorded in `CLAUDE.md` §Quality Checks (prose about another repository's ids is
paraphrased or wrapped in a fence, which the `qimpl-undefined` sweep skips) is
**strengthened, not broken**: after the fix fences are inert on both sides, so
the documented "wrap it in a fenced code block" escape becomes symmetric and can
no longer accidentally *define* a foreign id either. The rule adds a standing
obligation in place of an allowlist, and the gc self-test gains the case that
proves it.

**Cost in files touched (5):** `tools/sdd-gc.py` (three lines in `sweep_qimpl()`
— build the visible-line set per spec file, skip headings outside it — plus the
module docstring's pinned counting rule and the `--help` counting-rule text, and
a new self-test case); `docs/spec/drift-sweep.md` §Q-IMPL Counting Rule;
`docs/spec/deviation-protocol.md` §Q-IMPL Entry Format (the "That is why the
format fence's `Q-IMPL-001` may keep pointing at …" paragraph gains the reuse
obligation); `docs/requirements/integration/drift-sweep.md` (one new
`REQ-GC-HARNESSP6-*` row); `docs/requirements/index.md` (dates/delta note).

---

## Q4 — The L2 convergence signal

**Classification: design-decision-for-requirements, with a mechanical
implementation (reference/spec text) and one small code surface (lint rows plus
a self-test scenario).**

**Confidence**: **Medium** — and this is the lowest-confidence recommendation
in the file, deliberately flagged because the operator has directed that L2
ship regardless. The cluster rule reuses a parser the harness already exercises
(A1-A3), which is solid; but the rule has **never been replayed against a real
finding set**, and L2's firing rate is **unmeasured** (see §Open Questions). The
design is sound in construction and unproven in operation. The honest floor in
(d) is the calibration that matters: against the harness-p3 origin case this
form clusters 2 of 3 layers, not 3. Requirements should inherit this at lower
weight than Q1-E, Q2 and Q3, and should not restate it as settled.

L2 ships. The answers below settle the mechanism.

### (a) What counts as "the same root cause", mechanically

**Recommendation: reuse the arbitration finding key the harness already has.**
`docs/spec/arbitrated-handoff.md` §key table defines a finding key of
`(file, section)` — with the leading-ordinal strip ratified as
REQ-ARB-HARNESSP5-003 (`§3. Foo` ≡ `§Foo`) — and a working parser, exercised by
the A1–A3 scenarios in `tools/sdd-scope-check-selftest.py`. L2 matches that key
**across layers** instead of across rounds. Nothing new is parsed, no finding
field is added, and no layer's `RETURN:` shape changes.

> **Cluster rule.** Two or more findings form a cluster when (i) they come from
> **different** layers or second-executors (blue pipeline, chunk verifier,
> review, red); (ii) they belong to the **same cycle**, by the `research_id`
> stamp cycle identity already uses; and (iii) their arbitration keys are equal
> at **section** granularity — same `file` **and** same `section`.

False-positive behaviour of each candidate — the deciding evidence:

| Candidate key | False-positive behaviour |
|---|---|
| **Shared file path alone** | **Unacceptable.** `docs/spec/telemetry.md` is 764 lines and `telemetry-reader.md` 700; a review finding about the schema table and a red break about the reader's exit code would cluster. Two findings in one large file are not one root cause, and a rule that says they are makes the signal noise. Rejected. |
| **Shared `(file, section)`** (recommended) | Low. A section is the unit one contract lives in here, and the arbitration rule already treats section equality as "the same ground" for contradiction detection — a reading that has held through two cycles. Residual false positives cost one informational line. A file-level-only match renders **nothing**, deliberately, mirroring the way the `REVIEW: CONTRADICTION` block distinguishes a `file-level` qualifier from a section match. |
| **Shared requirement / `Q-IMPL` id** | Low false-positive rate, very low recall: only review findings reliably cite a `REQ-*` id; the chunk verifier and red usually cite a path or a command. Kept as a **secondary** key — two findings citing the same `REQ-*` id cluster even when their sections differ. |
| **Shared `reproduce:` command** | Almost no false positives and almost no recall: only red emits `reproduce:`, and a cross-layer signal needs at least two layers. Not usable as the primary key; usable as a tie-break. |
| **Orchestrator-assigned cluster key** | A root-cause field by another name, assigned by the orchestrator instead of the leaf. Not barred by the kickoff (the exclusion is on the *leaf's* `RETURN:` shape) but it makes the signal a judgment the harness cannot audit or reproduce. Rejected in favour of a derived key. |
| **Operator confirmation of a proposed cluster** | Zero false positives by definition, at the price of an operator decision per gate. Adopted only in its cheap form: the signal is informational and *proposes* the cluster, so the operator confirms by acting on it, never by answering a prompt. |

### (b) Which layers can converge, and over what window

The four layers plus the two adversarial second-executors report at different
times: the chunk verifier per chunk, the blue pipeline per stage, review per
stage, red only at verify. Convergence is computed over a **session-scoped,
in-memory finding ledger** — the same class of state as the attempt ledger and
the loop counters, which REQ-ORCH-014 already defines as session-scoped and
non-durable. The ledger holds, per finding, only the arbitration key, the
emitting layer and the gate at which it arrived: no finding text, nothing on
disk.

**The signal is evaluated at every gate**, over everything recorded so far, and
each cluster renders **once**, at the gate where its second member arrives. It
therefore can and usually will fire mid-cycle — a chunk verifier finding at
chunk 3 meeting a review finding at the implement stage gate — not only at DONE.

Is a signal that can only fire at DONE still worth having? Where a cluster only
completes at DONE (red is the second member, and red runs only at verify) the
answer is **yes, but worth less**: its value is redirecting effort before the
next fix, which a DONE firing cannot do. Under this cycle's no-carry-forward
rule a DONE firing still has a concrete use — it routes the cluster into
`verification.md` §Issues Found, to be fixed or explicitly closed in-cycle,
rather than into §Next Steps, which the DONE rule forbids from carrying
anything. Evaluating at every gate is what keeps the DONE-only case rare.

### (c) How it renders, and what it changes

A new own-line token as **item 6c** of the REQ-ORCH-034 order
(`skills/sdd-orchestrate/references/loop-control.md` §5), placed **after 6b
(`PLAN:`) and immediately before 7 (`TELEMETRY:`)**:

```
CONVERGENCE: docs/spec/telemetry.md §Writer rule (review, red) — 2 layers
```

- **Position rationale.** L2 is derived from the findings carried by signals
  1–4 and from the round pair signal 6 names, so it must render after every
  finding-bearing signal and after both derived pauses. §5's clause that
  `TELEMETRY:` renders "last … (or, when the pause of signal 6 or of signal 6b
  fired, after that pause's token line)" gains 6c in the same enumeration — a
  bounded, single-sentence edit of the same shape as the one that inserted 6b.
- **Informational: it never pauses the gate and has no option set.** `proceed`
  is not withheld. This is the decisive design choice: with no root-cause field
  the cluster is a heuristic, and a pausing heuristic converts every false
  positive into an operator interruption — precisely the noise failure (a) warns
  about. An informational line costs one line when wrong and delivers the whole
  value when right, because the value *is* the operator noticing.
- **Invariants held.** No durable artifact under `docs/` (ephemeral gate text,
  like `SCOPE:` and the review `VERDICT:`); it cannot influence phase detection
  (no skill's entry check reads it and it is never written to a file a detector
  reads); the four-layer verification table stays byte-unchanged because L2 is a
  gate signal, not a layer; no leaf `RETURN:` shape changes.
- **No telemetry field this cycle.** A `convergence_n` integer would fit
  telemetry's "counts, enums, shas" rule, but any new record key is a `v` key-set
  change, and `v` staying `{1, 2}` was settled in harness-p5. Recorded as a
  **settled exclusion with its reasoning**, not a deferral (the no-carry-forward
  rule): the signal's value is at the gate, where the operator is, and a
  post-cycle count of clusters buys nothing the gate transcript does not show.

### (d) Cost, and the honest floor

**Files touched (7, of which two are code):**

| File | Change |
|---|---|
| `docs/requirements/functional/orchestration.md` | one `REQ-ORCH-HARNESSP6-*` row: the signal, its position, its informational status |
| `docs/requirements/functional/harness-verification.md` | one `REQ-HARN-HARNESSP6-*` row: the cluster rule and the session-scoped ledger |
| `docs/spec/harness-loop-control.md` | §Gate signal order gains 6c; a new §Convergence Signal defines the cluster rule |
| `docs/spec/arbitrated-handoff.md` | one cross-reference: the `(file, section)` key now has two consumers |
| `skills/sdd-orchestrate/references/loop-control.md` | §5 item 6c; the §7 "renders last" clause amended to name 6c |
| `skills/sdd-orchestrate/SKILL.md` | §The gate one-line summary gains the token (non-divergent-summary rule) |
| `tools/sdd-skill-lint.py` | one `REQUIRED` row pair (producer in `loop-control.md`, consumer in `SKILL.md`), mirroring the two `COMMIT:` rows |

Optionally `tools/sdd-scope-check-selftest.py` gains a cluster scenario group
reusing the existing key parser — recommended, since the A1–A3 key scenarios
already live there.

**The honest floor.** The *full* signal the harness-p3 §L2 note imagines — "a
defect found three ways" — is **conceptual** convergence: blue's dropped
`git add` in Chunk 7, review C1's unexercised requirement, and red R4's "nothing
mechanically blocks DONE on aggregate drift" shared a root cause but **not** a
file or a section. No derivation from what layers already return can recover
that; it needs a root-cause field on findings (a standing exclusion) or a fifth
layer whose job is correlation (also excluded). Claiming otherwise would be
overclaiming, so it is said plainly here.

**The reduced form that avoids both, and is what ships:** *co-located*
convergence — the `(file, section)` cluster over findings that already carry a
location (review findings cite `file:line` / `§section`; red's `Rn` carry
`failures[].location`, already parsed for chunk mapping under
REQ-REDB-HARNESSP3-*; the chunk verifier's findings carry the chunk's declared
paths), informational, at position 6c, with the secondary `REQ-*` / `Q-IMPL` id
key for cases where sections differ. Against the harness-p3 origin case this
form would have clustered review C1 with red R4 — both centred on the aggregate
traceability and the `pass` flip — and would **not** have pulled in blue's chunk
finding: two of the three, at zero new fields and zero new layers. That is the
smallest version still worth shipping, and it is the version recommended. A
signal that catches co-located convergence reliably is worth more than a signal
that claims to catch conceptual convergence and cannot.

---

## Deferral-Backlog Sweep (scope item 9)

Every live entry in `docs/requirements/index.md` §Out of Scope whose text reads
as a deferral, with a disposition. The section was read in full; these are all
of them.

| # | Entry (line) | Disposition |
|---|---|---|
| 1 | "Review of sdd-review's own output (recursive case deferred)" (:801) | **Retire as settled exclusion, because** the recursion has no terminating rule (a review of a review is itself reviewable) and REQ-REV-005/006 already fix `sdd-review` as a non-executor; two cycles of live review rounds produced no finding a second-order review would have caught. Reword as "declined — unbounded recursion, no observed need", with no re-raise clause. |
| 2 | "A one-shot upstream review before a non-research pipeline entry (RS-HARNESSP3-001 Q8-OUT row 5) — **deferred** … Re-raise in that cycle." (:833) | **Retire as settled exclusion, because** it is conditional on mid-pipeline entry, which is itself out of scope and has no cycle that will introduce it (this cycle is terminal). Reword the dependency as a *precondition on a feature that does not exist*, not as queued work: "declined — has no effect while orchestrate is research-entry and sequential; it would be designed with mid-pipeline entry if that is ever built." The conditional phrasing is what keeps it out of §Next Steps. |
| 3 | "Clearing the four pre-existing `qimpl-broken-ref` gc warnings (RS-HARNESSP3-001 Q8-OUT row 6) — **deferred**" (:837) | **Retire as satisfied.** `python3 tools/sdd-gc.py --report` reports **0** `qimpl-broken-ref` findings at this branch point (harness-p5 fixed them at source under REQ-QIMPL-HARNESSP5-002). The entry describes work that no longer exists: **mark it "closed 2026-09-20 — 0 remaining"** rather than deleting it, so the
closure stays auditable at the DONE gate. No work. |
| 4 | "L2 — a cross-layer convergence signal … — **deferred to harness-p5**" (:855) | **In scope** — superseded by Q4 above. Rewrite as a pointer to the shipped requirement, not as an exclusion. |
| 5 | "L2 (cross-layer convergence as a gate signal) — **deferred again**" (:872, the p5 list) | **In scope** — same supersession. Both L2 entries must be struck together; leaving either makes §Out of Scope contradict the shipped requirement. |

Boundary entries checked and **not** counted as deferrals, recorded so the
requirements stage does not re-litigate them:

- The N ≥ 30 headless evaluation harness (:814) reads "**blocked until** (a)…(c)"
  — a stated precondition on work that is out of scope, not a queue entry. It
  already carries its reasoning; leave as-is.
- The `table_cells()` pipe-escape fix (:843) reads "**declined** … Re-open if a
  real row ever needs an escaped pipe" — already a settled exclusion with
  reasoning and a falsifiable re-open condition.
- Occurrences at :307, :350, :436, :453, :579, :628, :659, :699, :734, :736 and
  :741 use the word "deferred" in prose about *past* decisions, not in §Out of Scope. Corrected
  attribution (the section offsets in `docs/requirements/index.md` are §Files
  109, §Q-REQ Resolutions 385, §Out of Scope 791, §Open Questions 896,
  §Research References 1071): :307 and :350 sit in **§Files**, and :436, :453,
  :579, :628, :659, :699, :734, :736 and :741 all sit in **§Q-REQ
  Resolutions**. (The review's enumeration of this set listed 8 occurrences;
  the full set is 11 — :350, :628 and :699 were missing. All three are the
  same kind and change no conclusion.) There is no
  §Decisions section, and §Open Questions contains zero "defer" occurrences.
  The reason they are outside the sweep is not their section but their kind:
  each is a per-cycle Q-REQ resolution recording what a **closed** cycle
  decided, never a standing authorisation for future work.

### Second block — `docs/ws/harness-p5/verification.md` §Next Steps

The DONE rule's closing condition names §Next Steps as well as §Out of Scope,
and harness-p5's report is an **approved** artifact whose §Next Steps still
holds live items. Without dispositions here, the requirements stage inherits
standing instructions that contradict this spike's own recommendations.

| # | Item (harness-p5 §Next Steps) | Disposition |
|---|---|---|
| 6 | "bump `docs/spec/telemetry.md` `last_updated:` to 2026-09-20 through `sdd-specs` **in a follow-up cycle** — Routed `record` at the DONE gc step" | **Superseded by Q1 (options E + C), explicitly.** This item *is* Q1's option A, which §Q1 rejects: bumping a date purely to silence a sweep destroys the signal, and the kickoff bars it. The two must not both stand. Strike the item and replace it with a pointer to the Q1 recommendation. This is the single most important disposition in the sweep, because it is the one place where an approved report and a shipped requirement would otherwise disagree. |
| 7 | "Requirements text: qualify `docs/requirements/integration/skill-lint.md` REQ-LINT-007 (~L128-130)…" | **Fixed in-cycle** — this is scope item 6 of the kickoff, already in plan scope. Strike from §Next Steps once landed. |
| 8 | "L2 … **remains deferred**, as decided at DISCUSS; the harness-p5 evidence adds nothing that changes the deferral." | **Superseded by Q4.** This is the *third* L2 entry (the other two are §Out of Scope rows 4 and 5 above) and must be struck with them. Leaving it makes p5's approved report contradict the shipped L2 requirement. |
| 9 | p5 `plan.md` §Open Questions stale `telemetry-reader.md` "says 61" entry, to be struck at archival | **Fixed in-cycle** — kickoff scope item 7; the value reads `67` in all three places. Strike at plan archival as planned. |
| 10 | The four "Carried to the next cycle (n/4)" items | **Already in scope** — they map onto kickoff scope items 1 and 4 and questions Q2 and Q3. Strike all four when those land; none may survive the DONE gate phrased as carried. |

### New §Out of Scope entries this cycle must write (M1)

The DISCUSS rule requires a won't-do to be recorded **with its reasoning** in
`docs/requirements/index.md` §Out of Scope. The sweep above says what to
*remove*; these are what to *add*, so that no settled exclusion exists only in
this research file — under the terminality rule an unrecorded exclusion is
indistinguishable at the DONE gate from a deferral.

1. **Per-requirement-date staleness comparison** (Q1 option D, rejected) —
   declined: it needs either a hand-maintained per-entry date marker or
   `git log -L` history inside `--report`, ~40-60 lines, and its extra
   precision sits on top of an already-noisy category-file comparand.
2. **A `convergence_n` telemetry field for L2** (Q4(c)) — declined: any new key
   is a `v` key-set change, and the signal is informational, so the record adds
   nothing a reader cannot derive. Not deferred; not to be re-raised.
3. **Conceptual (non-co-located) convergence for L2** (Q4(d)) — declined: it
   requires either a root-cause field on a leaf's `RETURN:` or a fifth
   verification layer, both standing exclusions. The shipped form is
   co-located convergence, and its 2-of-3 recall against the harness-p3 origin
   case is the accepted cost, recorded so no later reader mistakes L2 for the
   full signal described at `docs/ws/harness-p3/verification.md` §L2.

### Closing condition

After **both** blocks are applied, neither `docs/requirements/index.md`
§Out of Scope nor `docs/ws/harness-p5/verification.md` §Next Steps contains an
entry phrased as deferred, carried or queued to a later cycle, and the three
new exclusions above are recorded with reasoning — the closing condition the
DONE rule checks. (The first block alone, as originally written, would have
satisfied only half of it.)

## Implications for Design

- **Two gc rules, three findings changed.** Item (1) (skip `status: pass`
  workstreams) retires 19 warnings; Q1's E+C retires the other 44 as warnings
  and preserves them as 3 `info` lines. The end state is a repo at **0
  `[stale-chain]` warnings** with the relation still reported — which makes the
  warn class a usable drift signal again and makes the DONE gc routing
  meaningful for the first time since harness-p3.
- **`SCOPE:` becomes a git-state check, not only a file-write check.** The token
  family does not grow; the block gains a finding line. Everything downstream
  that branches on `SCOPE: CLEAN | VIOLATION` keeps working unchanged.
- **The Q-IMPL fix is smaller than the kickoff assumed** and needs no allowlist,
  marker or whitelist — the probes settle it. The "countability rule" the
  kickoff asks for exists, but as an obligation on future illustrations rather
  than as an exception mechanism.
- **L2 is an orchestrator-derived, informational gate signal at position 6c**,
  built on the arbitration key that already ships. Its largest risk is not the
  code but the claim: requirements must state the co-located scope explicitly,
  or verification will be asked to prove a conceptual-convergence property the
  design does not deliver. That framing is the single most important thing this
  spike hands to the requirements stage.
- **Replan exposure.** Per the kickoff's terminality rule, the credible replan
  trigger is Q4(c): if inserting 6c forces a restructuring of §5's "renders
  last" contract beyond one sentence, or if the cluster rule cannot be exercised
  against any real finding pair this cycle (no second layer fires), L2 is
  **descoped at replan** inside this cycle — never queued to a successor.

## Prototype

No branch. Two read-only probes, no mutation of this repository's working tree
or git state:

1. A `python3` scan of `docs/spec/**` for fenced vs unfenced `### Q-IMPL-…`
   headings → 82 ids, 82 with an unfenced definition, 0 fence-only, 2 ids with
   two sites.
2. `$TMPDIR/gcprobe/gc2.py --report --root .` — `tools/sdd-gc.py` with
   `sweep_qimpl()`'s definition scan routed through `visible_lines()` → output
   identical to the unpatched tool (1 fail, 63 warnings, 25 info).

What they do not prove: probe 2 shows the change is inert **on this corpus
today**; it does not prove a future fenced illustration is safe — that is what
the proposed self-test case and the stated obligation are for.

## Open Questions

- **`docs/research/index.md` row (orchestrator action).** This spike's write
  scope is its own directory only, so the index row for `RS-HARNESSP6-001` was
  not added and `sdd-gc.py --report` currently reports one `[index-research]`
  **fail** because of it. The orchestrator must add the row at the research
  gate; the fail clears with it. Recorded rather than silently left.
- **Ambiguity resolved by choice (Q2 rendering).** The kickoff offers "a new
  token, or a member of the existing `SCOPE:` family". Both work; a new token
  would need a new REQ-ORCH-034 position, two new lint `REQUIRED` rows and a new
  branch point at the gate. The reading most consistent with the existing
  artifacts — `HISTORY_REWRITE` is already a finding line inside the `SCOPE:`
  block rather than a token of its own — is the `SCOPE:`-family member, and that
  is what is recommended. Requirements may overrule it; the comparand in §Q2 is
  independent of the choice.
- **Ambiguity resolved by choice (Q4 position).** 6c (after `PLAN:`, before
  `TELEMETRY:`) versus a derived line under signal 4, like `RED:` under
  `RED_VERDICT:`. 6c is recommended because a convergence line spans producers
  and cannot honestly hang under one of them. The cost difference is one
  sentence in §5's "renders last" clause.
- **Unmeasured: L2's firing rate.** No cycle's finding set has been replayed
  through the cluster rule, so the false-positive rate of section-level matching
  across layers is unknown. **Default**: ship informational, where a false
  positive costs one line; the harness-p3 origin case is the only worked example
  and is discussed under Q4(d). If this cycle produces a qualifying finding
  pair, the verify stage is the natural place to record the first real firing.

## Budget consumed

`{tool_calls: 22, probes: 2}` against a budget of one spike, <= 45 tool calls.
Both probes were read-only: probe 1 enumerated `Q-IMPL` definition sites under
`docs/spec/`; probe 2 ran a patched copy of `sdd-gc.py` from `$TMPDIR`. No
mutating git command was run in the working directory.

## Recommended Next Step

**Proceed to requirements.** All four questions have a recommendation, its
evidence and its cost; the sweep list is enumerated with dispositions; the
§Decided at DISCUSS list is restated unchanged. Nine items, no successor-cycle
work.
