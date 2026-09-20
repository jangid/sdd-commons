---
domain: PLAN
last_updated: 2026-09-20
status: Approved
research_refs: [RS-HARNESSP6-001]
---

# Requirements: Plan Management

## Overview

How the implementation plan stays lean across SDD cycles through archival
and summarization of completed work.

## Requirements

### REQ-PLAN-001: Active plan size bound
`docs/plan.md` must contain only current and future milestones with their tasks.
Completed milestones must be summarized to a single line each (milestone name,
completion date, task count) in a `## Completed` section at the bottom of the
active plan.
[Priority: must]

### REQ-PLAN-002: Plan archival
When `sdd-plan` rewrites a plan (due to staleness or new cycle) or `sdd-replan`
makes significant changes, the previous plan must be archived to
`docs/plan-history/{YYYY-MM-DD}-{reason}.md` before modification.
[Priority: must]

### REQ-PLAN-003: Changelog in archive only
Replan changelogs must be written to the archived plan file, not appended to the
active `docs/plan.md`. The active plan must not contain a changelog section.
[Priority: must]

### REQ-PLAN-004: Removed tasks cleanup
When tasks are invalidated during replanning, they must be moved to the archive
file. The active plan must not contain `[removed: ...]` markers.
[Priority: must]

### REQ-PLAN-HARNESSP6-001: a resolved §Open Questions entry is struck at plan archival
When `sdd-plan` or `sdd-replan` archives a plan, any `## Open Questions` entry
whose question has since been answered must be struck from the archived plan
rather than carried forward unresolved, so an archive never reads as a live
question. The concrete instance this cycle closes is
`docs/ws/harness-p5/plan.md` §Open Questions, which still states that
`docs/spec/telemetry-reader.md` "says 61" while the value reads `67` in all
three places that carry it. (workstream `harness-p6`; kickoff §Scope item 7,
mechanical and decided at DISCUSS)
**Acceptance**: `grep -c 'says 61' docs/ws/harness-p5/plan.md` (or the archived
file that replaces it) prints `0`, and the struck entry is visible as a struck
or dated-resolved line rather than deleted history.
[Priority: must]
