# sdd-commons

Spec-Driven Development for Claude Code, packaged as the `sdd` plugin.

## What this is

SDD is a cyclic, phase-based workflow for building software with AI assistance:
**research → requirements → specs → plan → implement → verify**, with
**replan**, **migrate** and **review** as cross-cutting phases. Each phase
writes its artifacts to disk under `docs/`, and those artifacts are the state —
any new session reads them, detects the current phase, and resumes where the
last one stopped. On top of the nine phase skills sits a driver that runs a
whole cycle as a single-operator loop, dispatching every stage and every review
as a separate, context-isolated subagent and pausing at an operator gate after
each one.

## Install

```
/plugin marketplace add jangid/sdd-commons
/plugin install sdd@sdd-commons
```

The first command registers this repository as a marketplace; the second
installs the `sdd` plugin from it. Restart the session afterwards so the skills
and agents load.

## Usage

**A whole cycle through the driver.** Invoke `sdd:orchestrate`. It opens with a
workstream picker, walks DISCUSS → KICKOFF → LOOP → DONE, and gates with you
after every stage (`proceed │ loop-back-to-fix │ stop`) and after every
implementation chunk (`proceed │ fix │ stop`). Use it when you want the full
pipeline with built-in external review.

**A single phase directly.** Invoke the phase skill by name — `sdd:research`,
`sdd:requirements`, `sdd:specs`, `sdd:plan`, `sdd:implement`, `sdd:verify`,
`sdd:replan`, `sdd:migrate` or `sdd:review`. Each one detects the current phase
from the artifacts already on disk and tells you if you are in the wrong place.
Use a direct invocation when you need one phase and not a cycle — for example
`sdd:review` on an artifact at a phase boundary, or `sdd:migrate` to upgrade an
older artifact layout.

Use SDD for non-trivial work (multi-file, multi-day, architectural impact).
Skip it for bug fixes, small tweaks, and well-understood changes.

## Components

**Skills**

| Component | What it does |
|---|---|
| `sdd:research` | Time-boxed exploration to reduce uncertainty before committing |
| `sdd:requirements` | Elicits and documents requirements |
| `sdd:specs` | Translates requirements into design specs |
| `sdd:plan` | Breaks specs into ordered, typed tasks |
| `sdd:implement` | Executes the plan with a TDD inner loop and stuck detection |
| `sdd:verify` | Holistic validation: quality gates, acceptance criteria, UX |
| `sdd:replan` | Structured replanning when assumptions break |
| `sdd:migrate` | One-time migration between artifact structure versions |
| `sdd:review` | Structured external review in a separate session |
| `sdd:orchestrate` | The driver — runs the nine phase skills as one operator loop |

**Agents**

| Component | What it does |
|---|---|
| `sdd:chunk-verifier` | Fresh read-only verifier for a single implementation chunk |
| `sdd:red-team` | Attacks the weakest acceptance criteria at the verify stage |
| `sdd:reviewer` | Runs the external review leaf at a stage boundary |

## Pointers

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — naming boundary, where the contracts
  live, pre-commit setup, and how to add a skill, an agent or a tool.
- [`LICENSE`](LICENSE) — MIT.
