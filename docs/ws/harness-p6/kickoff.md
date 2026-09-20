---
workstream: harness-p6
description: Harness hardening, part 6 (terminal) — L2 convergence signal, drift-sweep rule scoping, read-only git-state observation, gate-token lint coverage, the carried text fixes, and the deferral-backlog sweep
cycle: harness-hardening-p6
research_id: RS-HARNESSP6-001
entry_stage: research
date: 2026-09-20
branch: harness-p6
---

# Kickoff: RS-HARNESSP6-001 — Harness hardening, part 6

Run `/sdd-research` for workstream `harness-p6`. **This cycle is intended to be
terminal for the harness-hardening series**, and terminality is a scope
decision *and* a stopping-rule decision — see §Decided at DISCUSS. It drains
the backlog that `docs/ws/harness-p5/verification.md` §Next Steps carried
forward (four mechanical items and three text fixes), implements **L2**, the
cross-layer convergence signal deferred through harness-p3, -p4 and -p5, and
sweeps the remaining live deferrals out of `docs/requirements/index.md`
§Out of Scope. Four of the nine items carry a real design question and are the
spike's subject; the rest were decided at DISCUSS on 2026-09-20 and go straight
to requirements. Findings must land before requirements.

**Operator direction (2026-09-20).** The orchestrator recommended splitting L2
into its own workstream on the grounds that it is open-ended and would stretch
this cycle. The operator was told that cost and directed that L2 ship in this
cycle regardless, because L2 is the only backlog item that structurally
guarantees a successor cycle. That direction stands and is not re-litigated by
any downstream stage. The known consequence is a larger plan and a higher
chance of a replan trigger inside this cycle; a replan is the expected handling
if L2's design proves harder than the spike predicts — a successor workstream
is not.

Reuse `docs/research/RS-008-harness-hardening/findings.md` and the
`RS-HARNESSP2-001` … `RS-HARNESSP5-001` findings rather than re-deriving the
harness contract. `docs/ws/harness-p5/verification.md` §Next Steps and
§Issues Found → Minor are the authoritative statement of what is carried.

## Scope in one paragraph

Seven items, in plan order. (1) `tools/sdd-gc.py`'s `[stale-chain]` rule flags
closed workstreams forever, so the repo's warning count grows monotonically —
teach it to skip a workstream whose `verification.md` is `status: pass`.
(2) The same rule flags a **shared spec** for being older than a requirement
file the spec did not need to change; this is a distinct sub-class from (1)
and needs its own rule. (3) The write-scope contract forbids a read-only leaf
from creating, modifying or deleting files but says nothing about mutating
**git state**; a harness-p5 verifier ran `git stash` with nine files of
uncommitted work in the tree, and `SCOPE:` did not and could not observe it —
extend the snapshot to observe git state. (4) `PLAN:` is the only gate token
with no `REQUIRED` row in `tools/sdd-skill-lint.py`, so deleting it from
`loop-control.md` §6 is unguarded. (5) gc's Q-IMPL sweep is fence-asymmetric —
references use `visible_lines()` while definitions scan raw lines
(`tools/sdd-gc.py:611`), so a fenced illustrative heading registers as a real
definition; the symmetric fix un-defines the format examples and therefore
needs a countability rule. (6) `docs/requirements/integration/skill-lint.md`
REQ-LINT-007's "must not move" list is qualified to match the Chunk 9
rescoping that REQ-LINT-HARNESSP5-001 authorised in the same file. (7) The
stale `telemetry-reader.md` "says 61" entry in `docs/ws/harness-p5/plan.md`
§Open Questions is struck at plan archival. (8) **L2** — a cross-layer
convergence signal: when two or more verification layers in one cycle produce
findings sharing a root cause, the harness surfaces that convergence as its own
gate signal instead of leaving the correlation to the operator's eye. (9) The
**deferral-backlog sweep**: every live "deferred to a later cycle" entry in
`docs/requirements/index.md` §Out of Scope is either brought into this cycle or
retired by an explicit recorded decision, so the section holds no latent
successor-cycle work when this cycle closes.

**L2's provenance.** L2 originates at `docs/ws/harness-p3/verification.md`
§L2, generalising the V14 blind spot that three layers hit independently in
that cycle (blue: a dropped `git add` in Chunk 7; review C1: an unexercised
requirement about to flip to `pass`; red R4: nothing mechanically blocking DONE
on aggregate drift). It has never held a `REQ-*` id, a spec file or a plan
task; the harness has no root-cause field on findings today, and adding fields
to red's `RETURN:` shape is itself a standing exclusion. L2 is a **gate-level
signal derived by the orchestrator**, not a fifth verification layer — the
four-layer table stays byte-unchanged.

**Live deferrals in scope for the sweep (9).** The four pre-existing
`qimpl-broken-ref` gc warnings (RS-HARNESSP3-001 Q8-OUT row 6) — **already
moot**: `sdd-gc.py --report` reports `0` of them at this branch point, so the
entry is retired as satisfied, not worked. The one-shot upstream review before
a non-research pipeline entry (Q8-OUT row 5). Review of `sdd-review`'s own
output (the recursive case). Each is brought in or retired by decision; none is
left reading "deferred".

**Measured starting point (2026-09-20, this branch point).** `sdd-gc.py
--report` exits `OK` with 0 fail-class findings, 63 warnings and 25 info. All
63 warnings are `[stale-chain]`, distributed: `docs/spec/telemetry.md` 42,
`docs/ws/harness-p3/plan.md` 13, `docs/ws/harness-p4/plan.md` 6,
`docs/spec/adversarial-verify.md` 2. Item (1) therefore addresses 19 and item
(2) addresses 44 — the split that makes them two rules rather than one.

## Research questions

- **Q1 — The shared-spec staleness sub-class (evidence: 44 of 63 warnings).**
  `[stale-chain]` compares a downstream artifact's `last_updated:` against its
  upstream's. For a **shared** spec under `docs/spec/`, a requirement file may
  legitimately move — a later cycle adds a requirement to the same file —
  without the spec needing any edit; `docs/spec/telemetry.md` is current in
  content and lags only in date. State the options: bump the date through
  `sdd-specs` whenever it fires (the status quo, which harness-p5's DONE note
  rejected as making the signal meaningless); compare against only those
  requirement IDs the spec actually `requires:`; demote the shared-spec case
  to info; or a per-requirement-ID staleness comparison. For each, say what it
  does to the 44 warnings **and** what real staleness it would then miss —
  the false-negative cost is the deciding evidence, not the warning count.
  Cost in files touched; classify.

- **Q2 — Observing git-state mutation by a read-only leaf (evidence: the
  harness-p5 `git stash` incident, recorded in that cycle's §Next Steps 3/4).**
  The decision to make this **observable rather than contract-only** was taken
  at DISCUSS; the spike settles *how*. Which git state can be snapshotted
  cheaply around every dispatch — candidates: `HEAD` sha, `git stash list`
  count, index and worktree dirtiness, current branch, `ORIG_HEAD` — and which
  of those change during a **legitimate** dispatch, since the orchestrator's
  own commits, the fan-out worktree provisioning and merges all move git state
  by design. Specify the comparand precisely enough that a read-only leaf
  running `git stash` yields `SCOPE: VIOLATION` while a normal implement leaf
  and a fan-out merge do not. Say whether this rides the existing
  `snapshot(before)`/`snapshot(after)` window or needs its own, and how it
  renders — a new token, or a member of the existing `SCOPE:` family.
  Cost in files touched; classify.

- **Q3 — A countability rule for the Q-IMPL sweep (evidence: harness-p5 red
  round 1 R1, accepted under §Issues Found → Minor).** References are
  collected through `visible_lines()` (fences skipped) and definitions are
  scanned raw (`tools/sdd-gc.py:611`), so a heading inside a fence counts as a
  definition while a reference inside one does not. Making the two symmetric
  un-defines the `Q-IMPL-001`/`-002` format illustrations, which are fenced on
  purpose. State the rule that lets a fenced **format illustration** stay
  defined while a fenced **heading** elsewhere stops counting — candidates: an
  explicit opt-in marker on the illustration block, an info-fence language tag,
  a whitelist of illustration ids, or accepting the asymmetry and documenting
  it. Check each against the existing `qimpl-undefined` sweep's fence-skipping
  behaviour recorded in `CLAUDE.md` §Quality Checks, which the rule must not
  break. Cost in files touched; classify.

- **Q4 — The L2 convergence signal (evidence: three deferrals for want of a
  mechanism).** L2 ships this cycle; the spike settles **how**, not whether.
  Four sub-questions, all four required:
  (a) **What counts as "the same root cause" mechanically.** The harness has no
  root-cause field, and adding one to red's `RETURN:` shape is a standing
  exclusion — so the correlation must be derived by the orchestrator from what
  layers already return. Candidates: shared file path, shared requirement or
  `Q-IMPL` id, shared `reproduce:` command, an orchestrator-assigned cluster
  key, or operator confirmation of a proposed cluster. State the false-positive
  behaviour of each: two findings in one large file are *not* the same root
  cause, and a rule that says they are makes the signal noise.
  (b) **Which layers can converge.** The four layers plus the two adversarial
  second-executors (red team, chunk verifier) report at different times — the
  chunk verifier per chunk, review per stage, red at verify. Say over what
  window convergence is computed, given that the cycle's findings are not all
  in hand until DONE, and whether a signal that can only fire at DONE is still
  worth having.
  (c) **How it renders and what it changes.** A new gate signal in the
  REQ-ORCH-034 order, or a member of an existing family. Say where it sits in
  that order, whether it is informational or pauses the gate, and its option
  set if it pauses. It must not influence phase detection and must add no
  durable artifact under `docs/`.
  (d) **Cost, and the honest floor.** Files touched, and the smallest version
  of L2 that is still worth shipping. If the full signal proves to need a
  finding field or a fifth layer, say so plainly and name the reduced form that
  avoids both — the operator has directed that L2 ship, so "cannot be done" is
  not an available answer; "ships in this reduced form, for these reasons" is.

## Decided at DISCUSS (not research — requirements inherit these)

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

## Success criteria

- Q1, Q2, Q3 and Q4 each answered with a recommendation, its evidence, and the
  cost in files touched; each classified mechanical (spec/template text), code
  (`tools/*.py`), or design-decision-for-requirements.
- Q4 answers all four sub-questions (a)–(d), names a cluster rule with its
  false-positive behaviour stated, places the signal in the REQ-ORCH-034 order,
  and names the reduced form of L2 that avoids both a new finding field and a
  fifth layer. A Q4 answer that recommends deferring L2 does not meet this
  criterion.
- The sweep list is enumerated: every live "deferred" entry in
  `docs/requirements/index.md` §Out of Scope is listed with a disposition of
  either *in scope* or *retire as settled exclusion, because …*.
- Q1 states, for each option, both the warnings retired and the real staleness
  then missed — an option assessed only on warning count is not answered.
- Q2 names a comparand under which the `git stash` case violates and a normal
  implement leaf and a fan-out merge do not; an answer that flags legitimate
  dispatches is not answered.
- Q3's rule is checked against the existing fence-skipping behaviour and does
  not re-break `qimpl-undefined`.
- The findings restate the §Decided list unchanged so requirements sees one
  bounded scope.

## Budget

One spike, ≤ 45 tool calls (raised from 30 when L2 and the sweep entered
scope). Desk research over the existing specs, references
and tools, plus read-only runs of `tools/sdd-gc.py` and
`tools/sdd-skill-lint.py`. A probe, if needed, runs in a scratch git
repository under `$TMPDIR`, never against this repository's working tree, and
runs no mutating git command in this repository.

## Out of scope

- Bumping any `last_updated:` purely to silence a sweep, ahead of Q1's answer.
- A **fifth verification layer**, and any new field on a leaf's `RETURN:`
  shape — L2 is derived by the orchestrator from what layers already return.
- Deferring any in-scope item to a successor workstream: this cycle is
  terminal, and an item too large to fix triggers a replan instead.
- Re-opening anything settled by RS-008, RS-HARNESSP2-001, RS-HARNESSP3-001,
  RS-HARNESSP4-001 or RS-HARNESSP5-001.
- Touching the frozen telemetry fixtures under `tools/fixtures/` or the live
  `.sdd/telemetry.jsonl`.
- Any change that adds a durable artifact type under `docs/`, or that lets
  telemetry, reviews or red findings influence phase detection.
- Changing the four-layer verification table, which stays byte-unchanged.
- Marker-3 behaviour: unchanged this cycle.
