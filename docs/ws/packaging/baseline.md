---
workstream: packaging
artifact: pre-change baseline
captured: 2026-09-21
---

# Pre-change Baseline — workstream `packaging`

Captured by Chunk 0 task 1 of `docs/ws/packaging/plan.md`, **before any task in
this plan edited anything**. This is the comparand for the two **behavioural**
comparisons only — REQ-PKG-PACKAGING-004's equal-roots finding-set comparison
(C2.6) and REQ-LINT-PACKAGING-001's equal-roots set comparison (C1.7, C2.4).

It is **not** the comparand for REQ-PKG-PACKAGING-001's per-name membership
assertion (C5.5) or the `.py` loss check (C7.4): those cite the **pre-move
sha**, the parent of the Chunk 5 move commit, derived at C5.5 as
`git rev-parse <move commit>^`.

## The two shas

| Name | Sha | Used here? |
|------|-----|------------|
| Chunk 0 HEAD (`pre-change baseline`) | `93b113394a217020a45d7904c7d729108dfa23e2` (`93b1133`) | **Yes — this is the sha this baseline was captured at and the one the behavioural comparisons use.** |
| Requirement-pinned comparand from REQ-PKG-PACKAGING-004 | `a1ab5ba8ab1e8272dc707f4495448b7c93a9f2f1` (`a1ab5ba`) | No — substituted. |

**Substitution, recorded not silent.** REQ-PKG-PACKAGING-004 pins the comparand
at `a1ab5ba`. The plan substitutes the Chunk 0 HEAD sha for it: `a1ab5ba` was
the requirements-stage HEAD, and the specs-stage commits that followed it
changed `docs/spec/` — files the linter sweeps — so a finding-set comparison
against `a1ab5ba` would report specs-stage drift as a two-root regression. The
plan states the reason; it is not re-argued here.

The working tree was clean at capture time (`git status --porcelain` empty).

## Tree enumeration

`git ls-tree -r --name-only HEAD` at `93b1133`, restricted to `skills/`,
`agents/`, `tools/` and `.claude-plugin/plugin.json` — 45 paths:

```
.claude-plugin/plugin.json
agents/chunk-verifier.md
agents/red-team.md
agents/reviewer.md
skills/implement/SKILL.md
skills/implement/references/leaf-return.md
skills/implement/references/stuck-detection.md
skills/implement/references/workstream-layout.md
skills/migrate/SKILL.md
skills/migrate/references/v1-to-v2.md
skills/orchestrate/SKILL.md
skills/orchestrate/USAGE.md
skills/orchestrate/references/dispatch-templates.md
skills/orchestrate/references/drift-sweep.md
skills/orchestrate/references/fan-out.md
skills/orchestrate/references/isolation.md
skills/orchestrate/references/loop-control.md
skills/orchestrate/references/phase-detection.md
skills/orchestrate/references/return-contract.md
skills/orchestrate/references/telemetry.md
skills/orchestrate/references/v4-workstreams.md
skills/orchestrate/references/write-scope.md
skills/orchestrate/tools/gc.py
skills/orchestrate/tools/telemetry.py
skills/plan/SKILL.md
skills/replan/SKILL.md
skills/requirements/SKILL.md
skills/research/SKILL.md
skills/review/SKILL.md
skills/specs/SKILL.md
skills/verify/SKILL.md
tools/.gitkeep
tools/eval.py
tools/fixtures/README.md
tools/fixtures/arbitration-harness-p4-regen-2026-09-19/after.md
tools/fixtures/arbitration-harness-p4-regen-2026-09-19/before.md
tools/fixtures/arbitration-harness-p4-regen-2026-09-19/dispatch.txt
tools/fixtures/arbitration-harness-p4-regen-2026-09-19/round-1.txt
tools/fixtures/arbitration-harness-p4-regen-2026-09-19/round-2.txt
tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl
tools/fixtures/telemetry-harness-p4-2026-09-19.jsonl
tools/gc.py
tools/scope-check-selftest.py
tools/skill-lint.py
tools/telemetry.py
```

## Pre-change single-root linter finding set

Command, run from the repository root at `93b1133` with no argument (so the
single root is the repo containing the script):

```
python3 tools/skill-lint.py
```

Exit status `0`. Output, verbatim:

```
OK: 25 file(s) clean
```

**The finding set is empty.** 25 files were swept and no finding of any
severity was emitted. A later equal-roots two-root run must reproduce exactly
this: the same 25-file sweep and the same empty finding set.
