---
status: Approved
last_updated: 2026-09-21
requires:
  - REQ-AGENT-MARKETPLACE-001
  - REQ-AGENT-MARKETPLACE-002
  - REQ-AGENT-MARKETPLACE-003
  - REQ-AGENT-MARKETPLACE-004
  - REQ-AGENT-MARKETPLACE-005
  - REQ-AGENT-MARKETPLACE-006
---

# The Three Shipped Harness Agents

## Overview

Three roles have driven six cycles of this harness from inside the driver's
dispatch templates:

| Role | What it does | Closing token |
|---|---|---|
| **chunk verifier** | a fresh read-only leaf that closes each implement chunk | `CHUNK_VERDICT: PASS \| FAIL` |
| **red team** | a read-only leaf that attacks the weakest acceptance criteria at the verify stage | `RED_VERDICT: BROKEN \| HELD` |
| **reviewer** | the out-of-session external review at a stage boundary | `VERDICT: APPROVE \| APPROVE_WITH_FIXES \| REJECT` |

Each exists today only as prose inside the driver skill's dispatch-templates
reference, which after the rename of `skill-namespace-rename.md` is
`skills/orchestrate/references/dispatch-templates.md`. That full,
repository-rooted path is used at every mention below: a backticked relative path
is only mechanically verifiable if it resolves from the repository root, and a
bare `references/…` spelling resolves from nowhere — least of all from
`docs/spec/`, where this document lives. This spec's own citations therefore obey
the rule §Citation states. This spec extracts the three roles into three agent
files so they become plugin components a session can dispatch by name.

Research settled the open question: plugin-supplied agents **are** dispatchable —
seven agent files installed from a marketplace on this machine surface as seven
agent types under `<plugin>:<agent>` — so the kickoff's "ship either way"
contingency does not need its fallback branch.

**These agents change no behaviour.** Their vocabulary is the harness's existing
gate vocabulary, and the linter already enforces each of those tokens as a
producer/consumer pair between the dispatch templates and a skill. That
enforcement is a constraint on the extraction, not a side effect of it.

## Design

### Three top-level files, peers not children

```
agents/
  chunk-verifier.md    → sdd:chunk-verifier
  red-team.md          → sdd:red-team
  reviewer.md          → sdd:reviewer
```

A file directly under `agents/` surfaces as `<plugin>:<agent>`; a file in a
like-named subdirectory gains a **third** namespace segment and reads as a
sub-agent of a parent. The three roles are peers with no parent, so three
top-level files is the correct shape and yields the namespaced surface the
cycle specifies.

The directory's `.gitkeep` placeholder, left from before it had contents, is
**removed** with this change: `agents/` ends holding the three agent files and
nothing else. An empty-directory placeholder beside real content is stale, and
leaving it would let the "exactly three files" check pass on a directory that is
not what this design describes.

### The frontmatter contract

| Field | Required | Form |
|---|---|---|
| `name` | **yes** | kebab-case; string-equal to the filename stem |
| `description` | **yes** | a scalar ending in an explicit trigger clause ("Use when …") |
| `tools` | optional in general, **required for these three** | either a one-line comma-separated string or a YAML flow sequence — both forms are first-party |
| `model` | optional | one of the three model tier names when present |
| `color` | optional, **retained** | a colour word |

`description` is required to carry a trigger clause because the description is
what a dispatcher matches on; a description that only describes is not
dispatchable in practice. Nothing mechanical enforces the clause's wording, so
all three shipped agents open it with the same two words; that decision, and why
the illustration is read as literal rather than indicative, is
Q-IMPL-MARKETPLACE-013.

**Read-only is expressed by omission.** All three agents are read-only, so each
declares `tools` explicitly and that declaration excludes every mutating tool.
The mutating set is named here so the check is mechanical rather than a
judgement call: for this repository it is exactly `Write`, `Edit` and
`NotebookEdit`. `Bash` is **not** in that set and may be declared — a leaf that
must run `git diff` or a test needs it, and its read-only *use* is a constraint
the agent's body states, which no frontmatter field can express.

**Dropped fields.** `emoji` and `vibe` must not appear. They are this
repository's own invention, unattested in any first-party agent file swept, so
they are at best inert and at worst a validation failure. `color`, by contrast,
is a **real first-party field** set by a majority of the files swept and is
retained.

**Why frequency justifies keeping `color` but not the other two.** Field
frequency is evidence of what is *permitted*, not a read schema. Widely-used
refutes "unrecognised key"; never-observed does not establish acceptance. The
two rules point in opposite directions from the same evidence, which is why the
outcomes differ.

`CLAUDE.md` §Agents documents exactly this five-field list and no longer lists
the two dropped fields. The correction is **recorded** rather than silently
applied, because the repository's previous list was written before any agent
file existed in it (`project-docs.md`, REQ-DOCS-MARKETPLACE-005); the record is
Q-IMPL-MARKETPLACE-010 below.

### Vocabulary, and the token-relocation hazard

Each agent's body ends in the harness's existing structured token, written in
the same form the gate already consumes — at the start of a line, with its
enumerated values — not in generic reviewer prose.

The extraction is **additive with respect to tokens**. The linter checks that
each token's producing and consuming files both carry it, so *moving* a token
out of `skills/orchestrate/references/dispatch-templates.md` breaks the contract
row rather than
relocating it. The invariant is therefore a **superset** relation: for each of
the three tokens, the set of files carrying it after the change contains the set
that carried it before. Nothing is moved out; the agent files are added to it.

### Citation: by name **and** by path

Each dispatch template that dispatches one of the three roles cites it **twice**,
in one place:

- by its `subagent_type` name — `sdd:chunk-verifier`, `sdd:red-team`,
  `sdd:reviewer` — which is what makes the dispatch work;
- by a backticked `agents/<name>.md` path in one parenthetical, which is what
  makes the citation **mechanically verifiable**: the linter resolves
  backtick-quoted relative paths on disk, while a `subagent_type` name is
  checkable by nothing.

The name-plus-path form gets both, and keeps the template readable in a
repository checkout where the plugin is not installed. The linter resolves
backtick-quoted paths only for the path classes it knows, so making the cited
path checkable required one new repo-rooted class —
Q-IMPL-MARKETPLACE-012.

### The agent file is the single source

Where a dispatch template previously carried a role's full instructions inline,
those instructions **move into the agent file** and the template cites the agent
rather than restating it.

The split is by variability, not by length:

| Stays in the template | Moves to the agent file |
|---|---|
| the per-dispatch scope, the budget, the paths, the pinned `RETURN:` block | the role's standing definition — what it inspects, how it judges, what its token means |

Per-dispatch material varies per dispatch; a role's standing definition does
not. Two copies of a role's rules drift, and the harness has no mechanism that
would detect the drift. Each template keeps its pinned `RETURN:` block
**verbatim**, which the linter already checks — and that same `[template-drift]`
pinning bounds how much of a role's standing definition the extraction can
reach, recorded as Q-IMPL-MARKETPLACE-011.

## Acceptance Criteria

Both sides of every set comparison are derived at run time; no count appears as
a literal.

- [ ] `agents/` contains exactly three `*.md` files, no subdirectory and no other file; `test ! -e agents/.gitkeep` succeeds; each filename stem is kebab-case; all three are listed as components by the manifest check of REQ-PKG-MARKETPLACE-003 (REQ-AGENT-MARKETPLACE-001).
- [ ] For each of the three files, the parsed frontmatter carries `name` and `description`; `name` string-equals the filename stem; `description` contains a trigger clause; `tools` is present and its parsed value (string or sequence form) contains none of `Write`, `Edit`, `NotebookEdit`; neither dropped key is present — and a run-time grep for those two keys across `agents/` returns zero matches (REQ-AGENT-MARKETPLACE-002).
- [ ] The field list parsed from `CLAUDE.md` §Agents equals the five-field list of §The frontmatter contract, names `color`, and names neither dropped field (REQ-AGENT-MARKETPLACE-003).
- [ ] Each agent file contains its token at the start of a line; the skill linter exits 0 and its `--self-test` passes after the extraction; for each of the three tokens, the set of files carrying it — derived by the same grep before and after — is a superset of the pre-change set (REQ-AGENT-MARKETPLACE-004).
- [ ] For each of the three roles, `skills/orchestrate/references/dispatch-templates.md` contains both the namespaced name and a backticked `agents/<name>.md` path within the same template; the linter's link check resolves each cited path on disk (REQ-AGENT-MARKETPLACE-005).
- [ ] No rule text appears both in an agent file and in its dispatch template, derived by a run-time shingle comparison rather than by human reading of "role-definition paragraphs": for each agent/template pair, no normalised eight-word sequence from the agent file's rule section occurs in the template (the template cites the agent file instead — Q-IMPL-MARKETPLACE-025); each template retains its pinned `RETURN:` block verbatim (linter-checked); the count of linter contract rows is unchanged across the extraction, derived by running the same count before and after (REQ-AGENT-MARKETPLACE-006).

## Implementation Questions

### Q-IMPL-MARKETPLACE-010: The `CLAUDE.md` §Agents field list is corrected, not merely trimmed
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The frontmatter contract
**Date**: 2026-09-21 (implement stage, Chunk 4)

**Context**: the repository's `CLAUDE.md` §Agents listed seven frontmatter
fields — the five of §The frontmatter contract plus the two dropped ones — and
documented none of the per-field rules the contract states. The list predates
any agent file existing in this repository, so it described an intention, not a
measured shape.

**Decision**: replace the seven-field bullet with the five-field list, state
which fields are required and which are optional-but-required-for-these-three,
and add one bullet per field rule (kebab-case `name` equal to the stem, a
`description` ending in a trigger clause, `tools` in either first-party form
with the mutating tools omitted for a read-only agent, `model` tier names,
`color` a colour word). The two dropped fields are removed from the section
entirely rather than marked deprecated.

**Impact**: none on behaviour — `CLAUDE.md` is documentation. The correction is
recorded here because it changes a stated repository convention rather than
implementing one, which REQ-DOCS-MARKETPLACE-005 requires be visible.

### Q-IMPL-MARKETPLACE-011: The pinned `[template-drift]` fences bound the extraction
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The agent file is the single source
**Date**: 2026-09-21 (implement stage, Chunk 4)

**Context**: §The agent file is the single source says a role's standing
definition moves to the agent file. Four fenced bodies in
`skills/orchestrate/references/dispatch-templates.md` are pinned byte-for-byte
against Approved specs by the linter's `[template-drift]` rule — the chunk
verifier's dispatch body and verdict-rule fence, and the red team's dispatch
body and return-contract example. Some standing definition lives inside those
fences. Editing them would either fail the linter or require editing two
Approved specs that are outside this chunk's write scope, and deleting the
verdict-rule fence would fail the rule's "lost its anchored fence" branch.

**Decision**: the extraction moves the **unfenced** role-definition prose — the
section introductions, the verdict-rule trailer, the red team's judgement rules
and the reviewer's role sentence — and leaves every pinned fence byte-identical.
Where a pinned fence still carries standing text (notably the chunk verifier's
`iff` verdict rule), the agent file states the same rule in its own words and
the template's prose says where the meaning now lives, so no *paragraph* of rule
text exists in both files.

**Impact**: the "single source" property holds for the prose a future editor
would actually edit; the pinned fences remain single-sourced by the drift rule
itself, which is a stronger mechanism than prose de-duplication. Re-pinning
those fences against their specs is a separate change requiring both specs to be
re-approved.

### Q-IMPL-MARKETPLACE-012: The linter gains one repo-rooted `agents/<name>.md` path class
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Citation: by name **and** by path
**Date**: 2026-09-21 (implement stage, Chunk 4)

**Context**: §Citation says the backticked path is what makes the citation
mechanically verifiable, "the linter resolves backtick-quoted relative paths on
disk". It does — but only for the three classes its `resolve_backtick_path()`
knows (`references/…`, `skills/<skill>/references/…`, `docs/spec/….md`). A
backticked `agents/<name>.md` span resolved to nothing and was silently skipped,
so the citation was verifiable in principle and unchecked in fact.

**Decision**: add one class — a span matching `agents/<name>.md` resolves
against the repository root at severity `fail`, the same treatment as the
`skills/…` form, since both name files in this repository. No contract row is
added or removed; the `REQUIRED` row count is unchanged across the change,
asserted by deriving it on both sides.

**Impact**: a dispatch template that cites a non-existent agent file now fails
the linter. Any future document under `skills/` that backticks an
`agents/<name>.md` path is held to the same rule, which is the intent.

### Q-IMPL-MARKETPLACE-013: The trigger-clause illustration is read as literal

**Tier**: 2 (spec ambiguity)

**Spec reference**: §The frontmatter contract — `description` is "a scalar
ending in an explicit trigger clause ("Use when …")".

**Decision**: the parenthetical is read as **literal**, not illustrative: all
three shipped agents' descriptions end in a clause opening with the exact words
`Use when`. Two of them (`red-team`, `reviewer`) previously opened with `Use at
…`, which satisfies the criterion as worded but leaves the family
non-uniform; both were rewritten to the `Use when …` form with no change of
meaning or of the conditions they name.

**Rationale**: a dispatcher matches on the description, and one literal opener
across the family is the cheaper invariant to keep than a per-file judgement
about whether a stage-scoped `Use at` reads better. Nothing mechanical enforces
the wording, so uniformity is the only thing that keeps it stable; the
alternative — recording that the parenthetical is illustrative — would license
a third and fourth spelling with no way to notice.
