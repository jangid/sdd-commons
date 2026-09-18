---
domain: CYCID
last_updated: 2026-09-18
status: Approved
research_refs: [RS-HARNESSP3-001, RS-HARNESSP4-001]
workstream: harness-p3
---

# Requirements: Cycle Identity in Phase Detection

## Overview

Phase detection today cannot tell a **prior** cycle's execution artifacts from
the **current** cycle's: a `verification.md` with `status: pass`, or a `plan.md`
with `status: complete` and every task `[x]`, reads identically whether it was
written by this cycle or the last one, so a finished cycle can be misread as the
new one's completion. `research_id` is the discriminator that already exists —
but it is written **only** into `kickoff.md` today (repository grep, 2026-09-18)
and consumed only by `sdd-orchestrate` §Position, `references/loop-control.md`'s
`git log -S'research_id: <id>'` cycle-start-date derivation, and
`references/telemetry.md`'s `cycle.research_id`. This domain stamps it onto the
two execution artifacts that carry a completion signal and makes every reader
compare before trusting that signal.

Scope note: this adds a frontmatter **field** to two existing artifacts, not a
new artifact type, and the field is neither telemetry-, review- nor red-derived
— so it stays inside the harness-p3 kickoff's out-of-scope fence, and no marker
bump is implied.

**Deliberately excluded — requirements and specs status.** The shared corpus is
cumulative and `status: Approved` is a **product-wide** flag
(`docs/spec/ws-layout.md` §Approval), not a per-cycle one. A cycle boundary is
not expressible there and stamping one would break sharing, so
`docs/requirements/**` and `docs/spec/**` are explicitly **not** stamped.
Research findings are already per-spike and per-cycle by construction (the
kickoff names its `research_id`) and need no change.

## Requirements

### REQ-CYCID-HARNESSP3-001: `verification.md` carries `research_id` and readers compare it to the kickoff
`sdd-verify` Step 6 must stamp `research_id:` — copied from the active
workstream's `kickoff.md` — into `verification.md`'s frontmatter, and every
reader that treats `status: pass` as "this cycle is done" must first check
`verification.research_id == kickoff.research_id`. Three cases are defined, and
they are exhaustive:

1. **Mismatch** — the report's `research_id` differs from the kickoff's → "a
   previous cycle's report", i.e. the verify stage has not been reached in this
   cycle.
2. **Field absent** — the kickoff exists but the report carries no
   `research_id` (legacy reports) → same reading as a mismatch.
3. **No kickoff present** for the `(repo, workstream)` — no
   `docs/ws/<id>/kickoff.md` under marker `4`, no `docs/handoff/kickoff.md`
   under marker `3` → **the comparison is skipped entirely** and the existing
   `status:`-only rule applies unchanged. `kickoff.md` is written only by
   `sdd-orchestrate`, while `CLAUDE.md` explicitly supports invoking an
   individual `sdd-*` skill directly, so a repo that never ran the orchestrator
   must still have its `status: pass` report read as verified. Cycle identity is
   an orchestrated-cycle discriminator, never a precondition for detection.

The rule is marker-independent:
under marker `4` the kickoff is `docs/ws/<id>/kickoff.md`, under marker `3` it is
`docs/handoff/kickoff.md`, and the comparison is otherwise identical. The
`§Phase Detection` blocks of `sdd-verify`, `sdd-replan`, `sdd-plan`,
`sdd-implement` and `sdd-orchestrate`, and the detection table in `CLAUDE.md`,
must state the comparison. Existing reports are **not** back-filled — absence
reading as "previous cycle" is the safe direction and costs one re-entry into
verify per workstream that already has a passing report (see index §Open
Questions). (see RS-HARNESSP3-001 Q6 — the negative claim that `verification.md`
carries no `research_id` today is spec-read, from the harness-p2 artifacts'
frontmatter and a repository-wide grep; the stamp-and-compare remedy is
**constructed** and unexercised)
**Acceptance**: `skills/sdd-verify/SKILL.md`'s frontmatter template and Step 6
emit `research_id:`; a `verification.md` whose `research_id` differs from the
kickoff's is reported by every listed skill's phase detection as "verify not
reached this cycle" even at `status: pass`; a matching pair reports "verified";
a report with no `research_id` field behaves as a mismatch; and a repo/workstream
with **no `kickoff.md` at all** and a `status: pass` report reports "verified"
(the comparison is skipped, not failed).
[Priority: must]

### REQ-CYCID-HARNESSP3-002: `plan.md` carries `research_id` as the cycle-identity signal for plan completion
`sdd-plan` must stamp `research_id:` from the kickoff into `plan.md`'s
frontmatter, and readers that treat `status: complete` with every task `[x]` as
"this cycle's implementation is done" must compare it to the kickoff's the same
way REQ-CYCID-HARNESSP3-001 requires for `verification.md` — **including its
three-case rule**: mismatch and field-absent both read as "a previous cycle's
plan", and **no kickoff present** for the `(repo, workstream)` skips the
comparison and leaves the existing `status:`-only rule in force. `plan.md` has
the identical ambiguity — the harness-p2 plan reads exactly that today.

**Nothing is demoted.** The plan's `research_id` is the cycle-identity signal
for **plan completion** only. `references/loop-control.md` §3's
`git log -S'research_id: <id>'` command is a different thing: it runs against
the **kickoff**, is already a legacy fallback behind the kickoff's
`date:` field, and derives a **cycle-start date** for the replan re-entry cap
(REQ-HARN-002) — not a cycle identity for plan completion. A `research_id` stamp
on `plan.md` supplies identity, not a date, so it cannot replace or demote that
derivation, and this requirement leaves §3's cap arithmetic **unchanged**. (see
RS-HARNESSP3-001 Q6 — same evidence class as REQ-CYCID-HARNESSP3-001: the
absence is spec-read, the remedy constructed. The spike's own Q6 wording
["after which the git derivation becomes a fallback"] misdescribed that command
and has been corrected at source.)
**Acceptance**: `skills/sdd-plan/SKILL.md`'s frontmatter template and its
plan-writing step emit `research_id:`; a plan whose `research_id` differs from
the kickoff's is not read as this cycle's completed implementation; a plan with
no `research_id` behaves the same; a repo/workstream with no `kickoff.md` reads
a `status: complete` plan as complete; and `references/loop-control.md` §3 is
**unmodified** by this requirement.
[Priority: must]

### REQ-CYCID-HARNESSP4-001: `sdd-verify` and `sdd-plan` emit `research_id:` where Q-IMPL-HARNESSP3-014 pins it
`skills/sdd-verify/SKILL.md` Step 6 and `skills/sdd-plan/SKILL.md`'s frontmatter
template must emit `research_id:` **immediately after `status:`**, as
Q-IMPL-HARNESSP3-014 pins, rather than after `last_updated:` as both skills do
today. The two skills are reconciled to the Q-IMPL, not the Q-IMPL to the
skills: the Q-IMPL is the recorded decision, the comparison of
REQ-CYCID-HARNESSP3-001 is order-independent string equality so behaviour is
unchanged either way, and one position for the stamp lets a reader of any
`verification.md` or `plan.md` find it without searching. Cosmetic; carried
because it needs a cycle that can edit both skills. (workstream `harness-p4`; see
`docs/ws/harness-p3/verification.md` §Next Steps R4 — accepted at the verify
gate as a harness-p4 candidate)
**Acceptance**: the frontmatter templates in both skills show `status:` then
`research_id:` on consecutive lines; this cycle's `docs/ws/harness-p4/plan.md`
and `verification.md` frontmatter have `research_id:` on the line after
`status:`; `python3 tools/sdd-skill-lint.py` exits 0; the Q-IMPL text is
unchanged.
[Priority: should]

### REQ-CYCID-HARNESSP4-002: `CLAUDE.md`'s completion-signal rows carry the no-kickoff qualifier inline
The two completion-signal rows of `CLAUDE.md` §Phase Detection — the plan
`status: complete` row and the `verification.md` `status: pass` row — must carry
the case-3 relief inline, e.g. "**`research_id` matches the kickoff's**, when a
kickoff with one exists", so the table is independently correct. Today the
qualifier lives only in the §Cycle identity paragraph beneath the table, and a
reader consulting the table alone concludes a repo with no kickoff can never
read its own passing report as verified — the opposite of REQ-CYCID-HARNESSP3-001
case 3 and of what `sdd-verify` §Phase Detection implements. (workstream
`harness-p4`; see `docs/ws/harness-p3/verification.md` §V13 — recorded: yes,
qualify inline; `CLAUDE.md` was outside the verify write scope)
**Acceptance**: both rows in `CLAUDE.md` §Phase Detection contain the
qualifier; the §Cycle identity paragraph below still carries the three cases
unchanged; `python3 tools/sdd-gc.py --report` raises no new finding.
[Priority: should]

## Out of Scope

- Back-filling `research_id` into existing `verification.md` / `plan.md` files.
- Stamping any cycle identity onto the shared corpus (`docs/requirements/**`,
  `docs/spec/**`) — see the Overview's exclusion note.
- Any new artifact, marker bump, or use of telemetry / review / red output as a
  phase-detection input.
