# Phase Detection — Loop Position, Cycle Identity, New-Cycle vs. Resume

Reference for `orchestrate` SKILL.md §Phase Detection. The driver
introduces **no loop-position marker**: on entry — including re-entry in a fresh
session mid-loop — loop position is derived from the existing SDD artifacts,
reusing the stage skills' own phase detection.

## 1. Cycle identity (REQ-CYCID-HARNESSP3-001, -002) — from §Phase Detection

Before reading a **completion signal** as "this cycle is done" —
`verification.md` `status: pass`, or `plan.md` `status: complete` with every
task `[x]` — compare that artifact's frontmatter `research_id:` against the
kickoff's (`docs/ws/<ws>/kickoff.md` under marker `4`,
`docs/handoff/kickoff.md` under marker `3`) by **exact string equality** on the
trimmed value — no normalisation, case folding or prefix matching
(Q-IMPL-HARNESSP3-015). The three cases are exhaustive:

1. **Mismatch** — the artifact's `research_id` differs from the kickoff's → **a
   previous cycle's artifact**; this stage has not been reached in this cycle.
2. **Field absent** — a kickoff with a `research_id` exists but the artifact
   carries none (legacy; existing files are **never back-filled**) → the same
   reading as a mismatch. Absence is the safe direction: it costs one re-entry,
   it never asserts a completion that did not happen.
3. **No usable discriminator** — no `kickoff.md` for this `(repo, workstream)`,
   **or** a kickoff that carries no `research_id` (Q-IMPL-HARNESSP3-016) → the
   comparison is **skipped entirely** and the existing `status:`-only rule
   applies unchanged. Cycle identity is an orchestrated-cycle discriminator,
   never a precondition for detection.

See `docs/spec/cycle-identity.md`. The last two rows of the table in §2
(`plan complete`, `verification.md` status pass) carry a completion signal and
are subject to it. **Nothing is demoted**: `loop-control.md` §3's
`git log -S'research_id: <id>'` runs against the **kickoff** and derives a
cycle-start *date* for the replan re-entry cap — a different thing from this
identity comparison, and its cap arithmetic is **unmodified**.

## 2. Loop-position table — from §Phase Detection

Execution-artifact paths below are the marker-`3` flat paths; under marker `4`
the same artifacts live at `docs/ws/<ws>/` (`v4-workstreams.md` §Workstream &
version gate).

| On disk | Loop position |
|---------|---------------|
| no `docs/handoff/kickoff.md` | before KICKOFF — run DISCUSS |
| kickoff exists, its `research_id` spike has no Complete findings | at the research stage |
| research done, requirements `Draft`/missing | at the requirements stage |
| requirements `Approved`, specs missing/stale | at the specs stage |
| specs `Approved`, no `docs/plan.md` (or stale) | at the plan stage |
| plan has incomplete tasks | at the implement stage |
| plan complete, no/failing `docs/verification.md` | at the verify stage |
| `docs/verification.md` status `pending-red` | at the verify stage — resume before the red dispatch (never DONE, never replan) |
| `docs/verification.md` status pass | at DONE (pending operator approval) |

For an **entry kickoff** (SKILL.md §Entry Points) the stages before its recorded
entry stage are *intentionally absent*: derive loop position from the entry
stage on, never "at the research stage" from missing research artifacts. Tell
the operator the detected position and confirm before proceeding. A review
leaves no on-disk trace by design — it is **reproduced** by re-dispatching the
review subagent.

## 3. New cycle vs. resume (REQ-ORCH-014) — from §Phase Detection

A **complete** prior cycle (`status: pass`) is both "DONE" and the next
feature's starting point. Classify entry as **resume** (a cycle is mid-loop →
continue it), **done** (no new idea → report DONE) or **new cycle** (a new idea
→ run DISCUSS and **overwrite** `docs/handoff/kickoff.md` at KICKOFF). Only
**operator intent** separates *done* from *new cycle*: surface your
interpretation and confirm, never silently report the prior DONE. No new marker
is introduced.

**Marker-`4` gate.** Under marker ≠ `4` behavior is UNCHANGED — the single
global operator intent above resolves it; under marker `4` it is resolved per
workstream via the picker: [`v4-workstreams.md`](v4-workstreams.md) §Marker-4
gate for done-vs-new-cycle.
