---
workstream: consumer-geometry
description: Consumer geometry — the suite silently reduces its own checks when run from an installed plugin cache; close that and the packaging deferrals it shares a root cause with
cycle: consumer-geometry-1
research_id: RS-CONSUMERGEOMETRY-001
entry_stage: research
date: 2026-09-21
branch: consumer-geometry
supersedes: RS-PACKAGING-003
---

# Kickoff: RS-CONSUMERGEOMETRY-001 — the disjoint suite root

Run `/sdd:research` for workstream `consumer-geometry`. This spike is grounded
in a defect already observed live (§The observation); it does not have to
rediscover it, and re-deriving it is out of scope.

## The observation — carried as EVIDENCE, do not re-derive

Measured at DISCUSS on 2026-09-21, at `3bac4af`, before any edit:

```
repo copy:      python3 plugins/sdd/tools/skill-lint.py .            → OK: 25 file(s) clean
installed copy: python3 ~/.claude/plugins/cache/sdd-commons/sdd/0.1.0/tools/skill-lint.py .
                                                                     → FAIL: 1 finding — [structure] skills/ directory not found
```

The two files are **byte-identical** — `diff -q` over both `skill-lint.py` and
`gc.py` is silent. The corpus root is the same `.` in both runs. The only
difference is `default_suite_root()`, which derives from `__file__`:

- **In-repo**, the suite root resolves to `plugins/sdd`, which is *nested under*
  the corpus root, so `swept_roots()`' union reaches `plugins/sdd/skills/`.
- **Installed**, it resolves into the plugin cache — **disjoint** from the
  corpus root. The union holds no `skills/`, `check_structure()` takes its
  `if not skills_dirs:` branch, emits the single `structure` finding and
  **returns** — and every per-skill frontmatter, naming and size rule below that
  return silently stops running.

The disjoint geometry is not a hypothetical: it is the **only** geometry a
consumer has. `skills/orchestrate/SKILL.md` §Phase Detection documents the entry
command as `python3 <plugin-dir>/tools/gc.py --report --root .`, which is
exactly this shape. That command produced the degraded `FAIL` on this session's
own entry sweep.

**Why it outranks its size.** The failure is not a wrong answer but a *silently
reduced* one. The consumer reads `FAIL: 1 finding` as "one thing to fix", not as
"one thing to fix and twenty checks that did not run". It is the same shape the
`packaging` cycle kept finding — a binding whose failure nothing observes — and
`check_structure()`'s own docstring already records that this degradation
happened once before (C6.11) and was repaired for the nested case only.

## Scope — the spine

The disjoint geometry is the spine. The carried `packaging` deferrals are in
scope **because they are that geometry's debt**, not as an independent backlog
sweep.

1. **The degradation itself.** `check_structure()` is the instance found. The
   question is the *set*: every check that silently reduces, raises, or passes
   vacuously when the suite root is disjoint. Sweeping for that set is the work,
   not an assumption.
2. **Deferred item 1** — `check_retired_prefix()`'s `rel=Path(rel)` at
   `plugins/sdd/tools/skill-lint.py:1163`, whose reversion raises `ValueError`
   under exactly this geometry and survives all four gates. Highest-value of the
   carried items and the same root cause.
3. **Deferred items 5–7** — consumer-unreachable invocations: `gc.py`'s `AGG_FIX`
   string (`run tools/gc.py --fix …`), the six bare `python3 tools/telemetry.py`
   sites in `orchestrate` (`USAGE.md:159,439,572`;
   `references/telemetry.md:484,577,602`), and whether
   `plugins/sdd/skills/orchestrate/tools/` — now referenced by no invocation —
   still ships.
4. **Deferred items 2, 3, 10** — the unpinned `print_population(root,
   default_suite_root())` wiring, `retired_scope_entries()`'s `seen` set, and
   `gc.py`'s `lint_path()` candidate tuple. Each closes with a technique already
   in the file (`C9.2`/`C10.6` for wiring, `C10.1`/`C10.2` for deduplication).
5. **Deferred items 8, 9** — the text and traceability corrections downstream of
   the above, including the `marketplace` workstream record that item 7's
   decision falsifies.

## Out of scope

- **Deferred item 4** — the `warn` severity class cannot move an exit code, so no
  `warn`-only rebinding is gateable. Closing it needs an exit-contract change
  (`--strict`, or a warn-count comparand). Carried again as a stated boundary,
  **unless** research shows the spine cannot close without it — in which case say
  so explicitly rather than widening silently.
- Re-deriving §The observation.
- Any new SDD phase, skill or agent.
- Any change to the nine phase skills' own workflow semantics.

## Constraints — these bind every stage, not just this spike

1. **Writes land in `plugins/sdd/` in this repository.** The installed plugin
   cache at `~/.claude/plugins/cache/sdd-commons/` is a **read-only measurement
   surface** — it is how the disjoint geometry is reproduced and nothing else.
   No stage, leaf or fix packet writes to it. Reproduce disjointness the way the
   linter's own self-test already does, with a scratch root
   (`Linter(tr_corpus, tr_far, …)`), not by editing the cache.
2. **Every binding this cycle touches must have its reversion fail a gate,
   demonstrated by running the mutation — not asserted.** This is the rule the
   `packaging` cycle arrived at after four review rounds. It applies from the
   **first** dispatch here, not after the first rejection.
3. **`FIX_LOOP_MAX` = 3, no extra-iteration authorisations.** A stage that cannot
   close in three rounds routes to `replan`. Scope is open to what research
   finds; rounds are not.

## Open questions

**Q1 — What is the full set of checks that silently reduce under the disjoint
geometry?** `check_structure()` is one. Enumerate the rest across both tools:
checks that return early, raise, or pass vacuously when `swept_roots()` does not
contain the suite root. Name each with the observation that exposes it.

**Q2 — Does `REQ-PKG-MARKETPLACE-007` bind this cycle?** It froze tool source
last cycle and is why item 5 was carried rather than fixed; the spine defect sits
inside that freeze. Decide whether it is a standing product-wide constraint or a
`packaging`-scoped write-scope rule, and name the successor requirement that
permits tool-source edits for consumer-geometry correctness. The operator's
decision at DISCUSS is that this is settled **at the requirements stage, with the
amendment recorded** — not assumed here. This spike supplies the evidence for
that amendment.

**Q3 — Where does the fix belong?** Tool-side (suite-root derivation, or the
`swept_roots()` union admitting a disjoint suite root) or invocation-side (the
documented command passes an explicit suite root). State what each costs a
consumer, and what each does to the 56 suite-gated rows — `RS-PACKAGING-002` D1
recorded that under the corpus/suite pair those rows resolve against the
installed cache and pass vacuously. That interaction is live again here.

**Q4 — Can a gate in this repository observe a disjoint-geometry regression at
all?** Constraint 1 forbids writing the cache, and the in-repo geometry is nested
by construction, so the naturally-occurring gate cannot see the defect. The
existing scratch-root self-test technique is the candidate. If no gate can
observe it, say so — that answer makes constraint 2 unsatisfiable for the spine
and is the single most important thing this spike can return.

**Q5 — Is `plugins/sdd/skills/orchestrate/tools/` reachable by any invocation?**
If not, decide whether it ships, and name what removing it falsifies — the
`REQ-PKG-MARKETPLACE-006` criterion at `docs/ws/marketplace/verification.md:557`
is already recorded as affected.

## Success criteria

Q1 returns a set with an observation per member, not a single example. Q2 returns
a recommendation with the evidence an amendment would cite. Q3 returns a
recommendation with its cost to a consumer, or an explicit OPEN with the
blocking constraint named. Q4 returns a yes with the technique, or a no — and a
`no` is a success, not a shortfall. Q5 returns a decision and its falsified
criterion.

## Budget

**25 tool calls, 0 test runs.** Reading the two tools' root-binding regions and
reproducing the disjoint geometry in a scratch root is most of the work.

## Deliverable

`docs/research/RS-CONSUMERGEOMETRY-001-disjoint-suite-root/findings.md`, with
`status: Complete` when the five questions are answered or explicitly OPEN.
