---
workstream: packaging
description: Packaging follow-up, cycle 3 (capped) — close the four open decisions left by RS-PACKAGING-002, under a hard deliverable ceiling
cycle: packaging-followup-3
research_id: RS-PACKAGING-003
entry_stage: research
date: 2026-09-21
branch: packaging
supersedes: RS-PACKAGING-002
---

# Kickoff: RS-PACKAGING-003 — the four open decisions, capped

Run `/sdd:research` for workstream `packaging`. This spike closes four named
decisions. It re-derives nothing and re-argues nothing.

## Why there is a cycle 3, and what is actually being changed

`RS-PACKAGING-002` (`docs/research/RS-PACKAGING-002-root-interface/findings.md`,
commit `829ce38`) ran **eight review rounds and seven fix iterations** without
reaching `APPROVE`. Every round found a **new, true** defect — none were
repeats, and each was verified against the code. The artifact grew **496 → 962
lines** absorbing them.

That is the failure to fix, and it is not a scope failure. Cycle 2's scope
worked: two questions instead of cycle 1's three, evidence carried forward
instead of re-derived, Q1 proven on the first pass and confirmed eight times.
What failed was the **deliverable**. Each true defect, honestly fixed, cost
lines; more lines meant more checkable claims; more claims meant the next round
found another true defect. Cycle 2's kickoff called itself narrow but placed no
ceiling on the artifact, so nothing stopped that loop.

**The one variable this cycle changes is the cap.** See §The cap — it is a
requirement, not a style note.

## Carried forward as EVIDENCE — cite, never re-derive, never re-measure

All of the following was independently re-derived by cold reviewers in **eight**
consecutive rounds and was correct every time. Cite
`RS-PACKAGING-002` for any of it. Re-measuring any of it is out of scope and
counts against the cap for no gain.

- **`git-subdir` installs as modelled** — proven by a real install into a
  throwaway `CLAUDE_CONFIG_DIR`: the install contains the named subdirectory's
  contents with the path segment stripped and nothing from the repository root;
  a same-repository marketplace entry resolves; components are discovered **by
  convention** from the installed plugin root, so `marketplace.json` costs
  **one field**, not fourteen component edits. (Observed over a `file://` url,
  not a GitHub remote — that gap is recorded there and is **not** this spike's
  question.)
- **The population**: 56 suite-gated rows — `REQUIRED` 40, `VERSION_GATED_SKILLS`
  9, `V4_CONTRACT_SKILLS` 7 — plus `TEMPLATE_PAIRS` 4. `FORBIDDEN` 13 is
  **ungated** and has no path key. `skill_files()` = 25 at the repository root;
  policed areas 12.
- **The costing**: 45 files move, 154 stay, 45 + 154 = 199 at `0f5ec26`.
- **Option (B)** — the corpus-root / suite-root pair — with its set-union
  semantics (over resolved absolute paths; equality counts as containment and
  degenerates to today's single walk) and its per-root relative-path rendering
  rule (each swept file's relative path is computed against the root it was
  walked from).
- **`tools/skill-lint.rules.json` does not exist.** It was a proposal, never a
  file. Externalising the rows would *manufacture* the silent-disable class.
- **`tools/gc.py:1855`** — the `no docs/` bail sits in `main()` before `Gc(...)`.
  The kickoff-of-cycle-2's "exit 2" horn belongs to `gc.py`; `skill-lint.py` has
  no `docs/` bail and goes quiet instead.
- **`suite_rules` has no CLI surface** — argparse exposes only `root` and
  `--self-test`; all five `suite_rules=False` sites are self-test fixtures.

## The four decisions to close

Each already has attempted formulations **and their recorded defects** in
`RS-PACKAGING-002` §Open Questions. Read them there. Do not retry a rejected
formulation; if the right answer is one of them, say which and why the recorded
defect does not apply.

**D1 — Consumer suite-row behaviour under option (B).** Under (B) the 56 suite
rows resolve against `suite_root`, which in a consumer's install is the
**installed plugin cache** — files that exist and pass. So (B) flips consumer
behaviour from "fail loudly against the consumer's tree" to "pass vacuously
against the shipped plugin". Decide: is that the intended behaviour, or does the
linter need a `--no-suite-rules` / `--suite-root` surface? F11-relevant.

**D2 — The dual-rooted `.claude-plugin` row.** After the move `.claude-plugin/`
exists at both roots (`plugin.json` moves, `marketplace.json` stays). A one-root
binding silently drops `marketplace.json` from the retired-prefix scope — the one
file the move edits. Decide the binding, and name what detects a wrong one.
Note the existing block-9b pin cannot: it pins directory **names**, which survive
a wrong root binding intact.

**D3 — `FILES_SWEPT`.** Two formulations rejected: the literal `25` (a corpus
that grows fails it on ordinary contribution) and `git ls-files` equality (a
working-tree walk against a tracked list fails on any untracked `.md`, and it
hard-codes a path meaningless in a consumer repo). Decide a form, or state that
no sound form exists and what replaces it.

**D4 — The two-root behavioural fixture.** Part 2 requires two *distinct* roots,
but the containment rule only admits `suite_root/skills/**` when nested — so
disjoint roots make a seeded walk-class violation invisible. Decide the fixture
shape, or state the criterion cannot be built as specified.

**Plus one sequencing constraint to confirm, not re-derive:** the headline
40-row criterion needs `--print-population`, which does not exist. Confirm in one
line that a producing task must precede it.

## The cap

**The deliverable must not exceed 300 lines.** `wc -l` on
`docs/research/RS-PACKAGING-003-decisions/findings.md` is a gate, not guidance.

Three rules make it survivable:

1. **Evidence is cited, never restated.** One line per decision may reference
   `RS-PACKAGING-002`; reproducing its numbers or arguments is a defect.
2. **A correction that does not fit becomes an open question.** If closing a
   decision properly needs more room than the cap allows, record the decision as
   OPEN with its constraint named and move on. An honest open question costs two
   lines; an argument costs twenty.
3. **One statement per claim.** Cycle 2 restated its two principal caveats four
   times each, because each repair packet asked for the hedge in one more place.
   State a caveat once and cross-reference it.

If the cap and completeness genuinely conflict, **the cap wins and the shortfall
is recorded**. A short document with three decisions closed and one open beats a
long one with four closed and a ninth review round pending.

## Success criteria

Four decisions each carry a recommendation and its cost, or an explicit OPEN with
its blocking constraint named. The sequencing constraint is confirmed in one
line. The artifact is at most 300 lines and cites `RS-PACKAGING-002` rather than
reproducing it.

## Budget

**12 tool calls**, 0 test runs. The evidence is already gathered; this spike
decides over it. Reading `RS-PACKAGING-002` §Open Questions and the relevant
`tools/skill-lint.py` regions is most of the work.

## Out of scope

- Re-deriving or re-measuring anything under §Carried forward.
- `claude plugin install` / `marketplace` commands — Q1 is closed.
- Executing the root move. This cycle decides; the plan stage moves files.
- The `file://`-vs-GitHub install gap, and the unrun Q1(c) non-conventional-path
  control — both recorded in `RS-PACKAGING-002`, neither is a decision here.
- Any new SDD phase, skill or agent.

## Carried repairs — unchanged, entering at requirements

- Deferral-backlog screen marker leakage (`docs/ws/marketplace/verification.md`
  §Deferral-Backlog Screen).
- `skills/verify/SKILL.md:169` — the last cwd-relative drift-sweep invocation;
  sequence after D1/D2.
- `docs/spec/orchestration.md:574` — name the project README by its filename.
- `tools/skill-lint.py:381` and `:1252` — drop the retired front door's filename
  from `RETIRED_SCOPE_FILES` and the self-test's `policed_files` tuple
  **together** (`Q-IMPL-MARKETPLACE-017`).
- `CLAUDE.md:251` vs `:215` — reconcile which marker the repository uses.
- **Both** `.pre-commit-config.yaml` hook entries (`drift-sweep` at `:27-32`,
  `skill-lint` at `:33-38`) need the `plugins/sdd/` prefix at the move — editing
  one and not the other leaves the gate calling a dead path.
