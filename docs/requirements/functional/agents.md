---
domain: AGENT
last_updated: 2026-09-21
status: Approved
research_refs: [RS-MARKETPLACE-001]
workstream: marketplace
---

# Requirements: The Three Shipped Agents

## Overview

Three roles have driven six cycles of this harness from inside the driver's
dispatch templates: the **chunk verifier** (a fresh read-only leaf that closes
each implement chunk with `CHUNK_VERDICT:`), the **red team** (a read-only leaf
that attacks the weakest acceptance criteria at the verify stage with
`RED_VERDICT:`), and the **reviewer** (the out-of-session external review that
ends with `VERDICT:`). Each exists today only as prose inside
`references/dispatch-templates.md`. This domain extracts them into three agent
files so they become plugin components a session can dispatch by name.

RS-MARKETPLACE-001 Q5 resolved the open question the kickoff carried:
plugin-supplied agents **are** dispatchable — seven agent files installed from a
marketplace on this machine surface as seven agent types under
`<plugin>:<agent>` — so the §Decided contingency ("ship either way") does not need
its fallback branch. The same question's sweep over thirty-two first-party agent
files produced the frontmatter contract below, and corrected this repository's
own `CLAUDE.md` §Agents convention on two counts.

These agents change no behaviour. Their vocabulary is the harness's existing gate
vocabulary, and the linter already enforces each of those tokens as a
producer/consumer pair between the dispatch templates and a skill — which is a
constraint on the extraction, stated in REQ-AGENT-MARKETPLACE-004.

## Requirements

### REQ-AGENT-MARKETPLACE-001: Three top-level agent files, peers not children
The repository must carry exactly three agent files directly under `agents/` —
one for the chunk verifier, one for the red team, one for the reviewer — and must
not nest them in a subdirectory. A file directly under `agents/` surfaces as
`<plugin>:<agent>`; a file in a like-named subdirectory gains a third namespace
segment and reads as a sub-agent of a parent. The three are peers with no parent,
so three top-level files is the correct shape and yields the `sdd:<agent-name>`
surface §Decided specifies. The directory currently holds a `.gitkeep`
placeholder from before it had contents; that file must be **removed** with this
change, so `agents/` ends up holding the three agent files and nothing else — an
empty-directory placeholder beside real content is stale, and leaving it would
let the criterion below pass on a directory that is not what this requirement
describes. (see RS-MARKETPLACE-001 Q5)
**Acceptance**: `agents/` contains exactly three `*.md` files, no subdirectory
and no other file — in particular `test ! -e agents/.gitkeep` succeeds; each filename stem is a kebab-case name; the three are listed as
components by REQ-PKG-MARKETPLACE-003's manifest check.
[Priority: must]

### REQ-AGENT-MARKETPLACE-002: The frontmatter contract each agent file satisfies
Each agent file must carry YAML frontmatter with:

- **`name`** — required; kebab-case; **string-equal to the filename stem**.
- **`description`** — required; a scalar ending in an explicit trigger clause
  ("Use when …"), because the description is what a dispatcher matches on.
- **`tools`** — optional; when present, either a one-line comma-separated string
  or a YAML flow sequence (both forms are first-party). Omitting it inherits the
  caller's tools. All three of these agents are **read-only**, so each must
  declare `tools` explicitly and that declaration must exclude every mutating
  tool. The mutating set is named here so the check is mechanical rather than a
  judgement call: for this repository it is exactly `Write`, `Edit` and
  `NotebookEdit` — the write-capable tools a read-only agent omits from the
  `tools` list `CLAUDE.md` §Agents describes. `Bash` is **not** in that set and
  may be declared: a leaf that must run `git diff` or a test needs it, and its
  read-only use is a constraint the agent's body states, which no frontmatter
  field can express.
- **`model`** — optional; one of the three model tier names when present.
- **`color`** — permitted; a colour word. It is a **real first-party field**, set
  by a majority of the agent files swept, and is retained.

The fields `emoji` and `vibe` must **not** appear: they are this repository's own
invention and are unattested in any first-party agent file, so they are at best
inert and at worst a validation failure. Field frequency is evidence of what is
**permitted**, not a read schema — which is precisely why `color` is kept
(permitted-and-widely-used refutes "unrecognised key") and `emoji`/`vibe` are
dropped. (see RS-MARKETPLACE-001 Q5 §The frontmatter contract)
**Acceptance**: for each of the three files, the parsed frontmatter carries
`name` and `description`, `name` string-equals the filename stem, `description`
contains a trigger clause, `tools` is present and its parsed value contains none of
the three mutating tool names named above, and neither `emoji` nor `vibe` is a key; a run-time grep for
those two keys across `agents/` returns zero matches.
[Priority: must]

### REQ-AGENT-MARKETPLACE-003: `CLAUDE.md` §Agents documents exactly this field list
`CLAUDE.md` §Agents must document the field list of REQ-AGENT-MARKETPLACE-002 —
`name`, `description`, `tools`, `model`, `color` — and must no longer list
`emoji` or `vibe`. The correction is recorded rather than silently applied,
because the repository's previous list was written before any agent file existed
in it. (see RS-MARKETPLACE-001 Q5)
**Acceptance**: the field list in `CLAUDE.md` §Agents, parsed from the section,
equals the five-field list above; the section names `color` and does not name
`emoji` or `vibe`.
[Priority: must]

### REQ-AGENT-MARKETPLACE-004: The agents carry the harness's vocabulary, and no token leaves a linter-named file
Each agent's body must end in the harness's existing structured token — the chunk
verifier in `CHUNK_VERDICT: PASS | FAIL`, the red team in `RED_VERDICT: BROKEN |
HELD`, the reviewer in `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT` — written
in the same form the gate already consumes, not in generic reviewer prose. The
extraction must **not** remove any of those tokens from a file the skill linter
names in a producer/consumer contract row: the linter checks that each token's
producing and consuming files both carry it, so moving a token out of the
dispatch-templates file breaks the contract row rather than relocating it.
(see RS-MARKETPLACE-001 Q5 §The citation rule; `integration/skill-lint.md`)
**Acceptance**: each agent file contains its token at the start of a line; the
skill linter exits 0 and its `--self-test` passes after the extraction; the set of
files carrying each of the three tokens, derived at run time, is a **superset** of
the set that carried it before the change — nothing was moved out, only added.
[Priority: must]

### REQ-AGENT-MARKETPLACE-005: Dispatch templates cite each agent by name **and** by path
Each dispatch template that dispatches one of the three roles must cite it by its
`subagent_type` name — `sdd:chunk-verifier`, `sdd:red-team`, `sdd:reviewer` — and
must additionally name the agent's source file path in one parenthetical. The
name is what makes the dispatch work; the backticked path is what makes the
citation **mechanically verifiable**, because the linter resolves backtick-quoted
relative paths on disk while a `subagent_type` name is checkable by nothing. The
name-plus-path form gets both, and keeps the template readable in a repository
checkout where the plugin is not installed.
(see RS-MARKETPLACE-001 Q5 §The citation rule)
**Acceptance**: for each of the three roles, the dispatch-templates file contains
both the namespaced name and a backticked `agents/<name>.md` path in the same
template; the linter's link check resolves each cited path on disk.
[Priority: must]

### REQ-AGENT-MARKETPLACE-006: The agent file is the single source; the template does not restate its rules
Where a dispatch template previously carried a role's full instructions inline,
those instructions must move into the agent file and the template must cite the
agent rather than restate it. What stays in the template is the **per-dispatch**
material — the scope, the budget, the paths, the pinned `RETURN:` block — because
that varies per dispatch; what moves is the role's standing definition, because
that does not. Two copies of a role's rules drift, and the harness has no
mechanism that would detect the drift.
**Acceptance**: no rule text appears both in an agent file and in its dispatch
template; each template retains its pinned `RETURN:` block verbatim, which the
linter already checks; the behavioural contract of every gate token is unchanged,
confirmed by the linter's contract rows passing unmodified in number.
[Priority: must]
