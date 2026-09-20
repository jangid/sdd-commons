---
status: Approved
last_updated: 2026-09-20
requires:
  - REQ-PLAN-001
  - REQ-PLAN-002
  - REQ-PLAN-003
  - REQ-PLAN-004
  - REQ-SKILL-005
  - REQ-SKILL-008
  - REQ-PLAN-HARNESSP6-001
---

# Plan Management

## Context

In v1, `docs/plan.md` grows monotonically across SDD cycles. Three mechanisms
cause this: replan changelogs are appended, removed tasks are marked with
`[removed: reason]` instead of deleted, and completed milestones are preserved
in full. After several cycles, the plan file consumes excessive AI context and
becomes hard to navigate.

v2 introduces an archive pattern: the active plan stays lean, and history moves
to `docs/plan-history/`.

This spec covers single-milestone projects. For multi-milestone projects,
`docs/plan.md` becomes an index of milestone plans per milestone-plans.md,
which extends this design.

## Design

### Active Plan Structure

`docs/plan.md` contains only actionable content:

```markdown
# Implementation Plan: [Project Name]

## Overview
One paragraph: what we're implementing and the approach.

## Conventions
...

## Chunks

### Chunk 3: [Name] — [one-line description]
**Goal**: ...
**Tasks**:
1. [implement] ... — traces to [spec.md]
2. [verify] ... — traces to [spec.md]
**Verify**: ...

### Chunk 4: [Name] — [one-line description]
**Depends on**: Chunk 3
...

## Replan Triggers
- [Condition] → [what changes in the plan]

## Risks
- [Risk]: [Impact and mitigation]

## Completed
- Chunk 0: Repo bootstrap (2026-04-20, 3 tasks)
- Chunk 1: Core models (2026-04-22, 4 tasks)
- Chunk 2: First feature (2026-04-25, 5 tasks)
```

**Key differences from v1**:
- The `## Completed` section contains one-line summaries, not full chunk
  details. Format: `- Chunk N: {description} ({date}, {task count})`.
- No `## Plan Changelog` section — changelogs live in archive files.
- No `[removed: reason]` markers — removed tasks are moved to the archive.
- Multi-milestone projects archive whole milestone plans to `plan-history/`
  per milestone-plans.md rather than summarizing completed milestones here.

**Why summarize instead of remove entirely**: The one-line summaries provide
context for chunk dependencies ("Chunk 4 depends on Chunk 3" is meaningful
only if you can see what Chunk 3 was). A single line per chunk adds
negligible size.

### Plan History

```
docs/plan-history/
  2026-04-20-initial.md
  2026-04-25-replan-api-change.md
  2026-04-28-pre-v2-migration.md
```

Archive files are complete snapshots of the plan at the time of archival,
including:
- All chunks (completed and pending at that time)
- Task completion status
- The changelog entry that triggered the archival

**Naming convention**: `{YYYY-MM-DD}-{reason}.md` where reason is kebab-case,
describing why the plan was archived (e.g., `replan-api-change`, `cycle-complete`,
`pre-v2-migration`).

**Per-milestone archival**: When a project uses per-milestone plan files
(see milestone-plans.md), completed milestone plans are archived with the
milestone ID as part of the reason: `{date}-{milestone-id}-complete.md`
(e.g., `2026-04-20-m1-complete.md`). The archive pattern and naming
convention are the same — only the reason segment changes to include the
milestone identifier.

### Archival Triggers

The active plan is archived before these operations:

1. **Plan rewrite** (`sdd-plan`): When the plan is stale and needs rewriting
   from updated specs, archive the current plan as
   `{date}-stale-rewrite.md` before creating the new one.

2. **Significant replan** (`sdd-replan`): When replanning changes more than
   task reordering — adding/removing chunks, changing approach. Archive as
   `{date}-replan-{reason}.md`. Minor replans (reordering tasks within a
   chunk) do not trigger archival.

3. **Cycle completion** (`sdd-verify`): When verification passes and the cycle
   is complete, the plan becomes historical. Archive as
   `{date}-cycle-complete.md`.

**What counts as "significant"**: If the replan adds or removes chunks, or
changes the approach described in the Overview section, it's significant.
Task-level changes within existing chunks are minor.

### Replan Behavior Changes

When `sdd-replan` revises the plan:

1. If significant (per above): archive current plan, then write the revised
   plan fresh.
2. If minor: edit the plan in place.
3. In both cases:
   - Removed tasks go to the archive file, not marked inline.
   - Changelog entries go to the archive file, not appended to the active plan.
   - Completed chunk summaries are preserved in the `## Completed` section.

### Resolved `## Open Questions` Entries Are Struck at Archival (REQ-PLAN-HARNESSP6-001)

[Added 2026-09-20, harness-p6 — REQ-PLAN-HARNESSP6-001]

When `sdd-plan` or `sdd-replan` archives a plan, every `## Open Questions` entry
whose question has since been answered is **struck** in the archived copy rather
than carried forward unresolved. Without this, an archive reads as a live
question forever, and a later reader cannot tell a genuinely open item from one
that was settled three cycles ago.

**Struck, not deleted.** The entry stays visible, marked with a bracketed dated
resolution marker on **a line of its own directly abutting the entry** —
immediately after the entry's heading line, or immediately after its last line
when the entry wraps — or appended to the entry's own line, naming the date and
what resolved it. This uses the same marker **token** shape as the requirements
corpus (`requirements-artifacts.md` §`## Out of Scope` Discipline), but not the
same **adjacency**: there the anchor is a matched phrase and only at-or-above
placement counts (the occurrence's own line or the one immediately preceding
it); here the anchor is the **entry block**, and the marker normally sits
*below* it. The two rules govern disjoint scopes — that corpus rule reads
`requirements/index.md` §Out of Scope and `verification.md` §Next Steps for
deferral phrasings; this one reads archived `plan-history/` §Open Questions for
answered entries — and neither regex is ever applied to the other's scope.

**[Clarified 2026-09-20 — REQ-PLAN-HARNESSP6-001.** The earlier wording read
"on its own line or the line immediately preceding it", which the worked
example below contradicts: the example places the marker on the line
*following* the heading. Read entry-anchored, the spec's own example violated
the spec. The ambiguity was found at the harness-p6 Chunk 6 verification, where
a real struck entry wrapped across six lines and its marker landed below the
entry rather than above the matched phrase.**]

**Note for whoever implements §Verification → Automated.** That validator must
anchor on the **entry block**, not on a matched phrase, and must accept a
marker *below* the entry. Borrowing the requirements corpus's `L` / `L-1`
at-or-above semantics would flag correctly-struck entries — including the one
this cycle wrote — as live.

```
### 3. Does telemetry-reader.md still say 61?
**[Struck 2026-09-20 — resolved: the value reads 67 in all three places that
carry it; REQ-PLAN-HARNESSP6-001]**
```

Deleting the entry would erase the record that the question was ever open, which
is exactly the auditability the archive exists to hold. Rewording it in place
would leave no evidence that it had been resolved rather than silently dropped.

**Who decides "answered".** The archiving skill, at archival time, from the
artifacts in front of it: an entry is answered when the spec, tool or plan text
it asks about now states the answer. An entry the skill cannot resolve stays
unmarked and is carried into the archive as-is — this rule strikes settled
entries, it does not force a verdict.

**Scope.** The rule applies to the archived copy under `plan-history/`
(marker `4`: `docs/ws/<id>/plan-history/`). It changes no active-plan behaviour
and adds no file, section or marker type.

### Interaction with Staleness Detection

`sdd-plan` reads staleness from `docs/requirements/index.md` (per overview
spec). When the plan is stale:

1. Archive the current plan.
2. Re-read all approved specs.
3. Produce a new plan, carrying forward the `## Completed` section from the
   archived plan.

## Verification

### Automated
- Validate that an archived plan's `## Open Questions` section contains no entry
  that the corpus has since answered and that lacks an adjacent bracketed dated
  resolution marker (REQ-PLAN-HARNESSP6-001).
- Validate that striking an entry leaves it present in the archive — the
  archived file's entry count is unchanged by the strike (REQ-PLAN-HARNESSP6-001).
- Validate `docs/plan.md` contains no `## Plan Changelog` section
- Validate `docs/plan.md` contains no `[removed: ...]` markers
- Validate completed chunks are single-line summaries
- Validate `docs/plan-history/` files follow the naming convention

### Manual
- After a replan, confirm the archived file contains the full pre-replan state
- After a cycle, confirm the archive captures the final plan state

### Acceptance Criteria
- [ ] Active plan contains only current/future chunks (REQ-PLAN-001)
- [ ] Completed chunks are one-line summaries (REQ-PLAN-001)
- [ ] Plan is archived before rewrite or significant replan (REQ-PLAN-002)
- [ ] Archive files use `{YYYY-MM-DD}-{reason}.md` naming (REQ-PLAN-002)
- [ ] Changelogs are written to archive only (REQ-PLAN-003)
- [ ] Active plan never contains a changelog section (REQ-PLAN-003)
- [ ] Removed tasks are moved to archive, not marked inline (REQ-PLAN-004)
- [ ] `sdd-plan` reads staleness from `requirements/index.md` (REQ-SKILL-005)
- [ ] `sdd-replan` writes changelogs and removed tasks to archive (REQ-SKILL-008)
- [ ] `sdd-plan` and `sdd-replan` strike resolved `## Open Questions` entries at archival, marking each with an adjacent bracketed dated resolution marker rather than deleting it (REQ-PLAN-HARNESSP6-001)
- [ ] The concrete instance this cycle closes — the `docs/spec/telemetry-reader.md` "says 61" entry in `docs/ws/harness-p5/plan.md` §Open Questions — is struck with its date and evidence, and the stale claim no longer appears unmarked in that file or in the archive that replaces it (REQ-PLAN-HARNESSP6-001)
