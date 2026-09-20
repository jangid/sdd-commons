---
workstream: harness-p6
description: Harness hardening, part 6 — drift-sweep rule scoping, read-only git-state observation, gate-token lint coverage, and the harness-p5 carried text fixes
cycle: harness-hardening-p6
research_id: RS-HARNESSP6-001
entry_stage: research
date: 2026-09-20
branch: harness-p6
---

# Kickoff: RS-HARNESSP6-001 — Harness hardening, part 6

Run `/sdd-research` for workstream `harness-p6`. This cycle drains the backlog
that `docs/ws/harness-p5/verification.md` §Next Steps carried forward: four
mechanical items and three text fixes. It introduces no new harness concept.
Three of the seven items carry a real design question and are the spike's
subject; the rest were decided at DISCUSS on 2026-09-20 and go straight to
requirements. Findings must land before requirements.

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
§Open Questions is struck at plan archival.

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

## Decided at DISCUSS (not research — requirements inherit these)

- Item (3) is settled as an **observable check**, not contract wording alone;
  the spike settles the mechanism, not whether to enforce.
- Items (1), (4), (6) and (7) are mechanical and need no research; they go
  straight to requirements as specified in §Scope.
- Items (1) and (2) are **two rules**, not one — they address disjoint halves
  of the 63 warnings and have different false-negative profiles.
- L2 (cross-layer convergence as a gate signal) stays deferred for a **third**
  cycle and gets its own successor workstream. A reconstruction produced at
  this DISCUSS records that L2 has never held a `REQ-*` id or a spec file, and
  that implementing it requires a mechanical definition of "same root cause"
  for which the harness has no field today. That reconstruction is DISCUSS
  context for the *next* workstream and is not an input to this one.
- DONE rule: every requirement traced by this workstream `pass`; nothing
  closes as a deliberate `fail`; an item that cannot be exercised is descoped
  at replan.
- Scope priority for the plan is the order in §Scope, so a `stop` partway
  leaves the two gc rules landed first.

## Success criteria

- Q1, Q2 and Q3 each answered with a recommendation, its evidence, and the
  cost in files touched; each classified mechanical (spec/template text), code
  (`tools/*.py`), or design-decision-for-requirements.
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

One spike, ≤ 30 tool calls. Desk research over the existing specs, references
and tools, plus read-only runs of `tools/sdd-gc.py` and
`tools/sdd-skill-lint.py`. A probe, if needed, runs in a scratch git
repository under `$TMPDIR`, never against this repository's working tree, and
runs no mutating git command in this repository.

## Out of scope

- L2 (cross-layer convergence as a gate signal) — deferred a third time, to
  its own workstream.
- Bumping any `last_updated:` purely to silence a sweep, ahead of Q1's answer.
- Re-opening anything settled by RS-008, RS-HARNESSP2-001, RS-HARNESSP3-001,
  RS-HARNESSP4-001 or RS-HARNESSP5-001.
- Touching the frozen telemetry fixtures under `tools/fixtures/` or the live
  `.sdd/telemetry.jsonl`.
- Any change that adds a durable artifact type under `docs/`, or that lets
  telemetry, reviews or red findings influence phase detection.
- Changing the four-layer verification table, which stays byte-unchanged.
- Marker-3 behaviour: unchanged this cycle.
