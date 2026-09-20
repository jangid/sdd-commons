---
domain: NAME
last_updated: 2026-09-21
status: Approved
research_refs: [RS-MARKETPLACE-001]
workstream: marketplace
---

# Requirements: Component Naming and the Prefix Retirement

## Overview

The skills carry a redundant `sdd-` prefix that exists only because skills
currently sit in a flat global namespace. A plugin prefix **is** that namespace,
so once the repository ships as the `sdd` plugin the components surface as
`sdd:orchestrate`, `sdd:implement`, `sdd:chunk-verifier` — matching
`superpowers:brainstorming` rather than a stuttering doubled name. This domain
covers the rename: what is renamed, what is deliberately left alone, in what
order, and how the change is verified.

The rename is the larger half of this cycle by blast radius, and it is
**code** as well as text: the skill linter carries contract rows keyed on skill
paths and skill names, and it is the single densest rename surface in the
repository. RS-MARKETPLACE-001 Q4 settles the ordering on measured grounds —
rename first, marketplace scaffold second — because the linter exiting 0 is an
independently verifiable intermediate state, and because under
REQ-PKG-MARKETPLACE-002's `"source": "./"` the scaffold moves zero existing
files, so separating the two steps costs zero double-touched references.

**Self-reference hazard.** A rule about text lives inside its own domain. Every
requirement in this file quotes the prefix it retires, `CONTRIBUTING.md` must
quote it to explain the boundary, and the linter rule that forbids it contains
it. REQ-NAME-MARKETPLACE-009 therefore states the exemption mechanism as part of
the requirement rather than leaving it to implementation.

## Requirements

### What is renamed

### REQ-NAME-MARKETPLACE-001: Skill directories and frontmatter drop the redundant prefix
Each skill directory under `skills/` must be renamed to drop its leading `sdd-`
prefix, and each `SKILL.md`'s frontmatter `name` must be updated to match its new
directory name. The repository's existing convention that frontmatter `name`
equals the directory name is unchanged and continues to hold after the rename.
(see RS-MARKETPLACE-001 Q4)
**Acceptance**: for every directory under `skills/` containing a `SKILL.md`, the
directory basename does not begin with `sdd-` and the file's frontmatter `name`
string-equals the directory basename; both sides are read from disk at run time.
`python3 tools/skill-lint.py` exits 0.
[Priority: must]

### REQ-NAME-MARKETPLACE-002: Components surface under the plugin namespace
Skills must be referable as `sdd:<name>` and agents as `sdd:<agent-name>` once
installed, and all cross-skill references inside `skills/` must name a sibling by
its **bare new name**, never by a path into another skill's directory. Name
coupling rather than path coupling is what makes the single-plugin decision of
REQ-PKG-MARKETPLACE-002 safe and what lets a skill directory move without
breaking its siblings. (see RS-MARKETPLACE-001 Q3 Evidence, Q5)
**Acceptance**: a run-time grep over `skills/` for a cross-skill reference of the
form `skills/<other-skill>/…` returns zero matches; the same grep for the
`skills/<other-skill>/references/<file>` form — the form the linter treats as
fail severity — likewise returns zero.
[Priority: must]

### REQ-NAME-MARKETPLACE-003: Tool filenames drop the prefix
The Python tools under `tools/` must be renamed to drop their leading `sdd-`
prefix, and every invocation and prose reference to them **within the live
rename scope** (REQ-NAME-MARKETPLACE-004) must be updated to the new spelling.
The tools' own behaviour, flags and exit codes are unchanged — this is a filename
change, not a contract change. The **self-referential name strings inside the
tools' own source are in scope for this rename**: the `prog=` value, the
usage/`--help` block and any user-facing hint string that spells the tool's
retired filename must be updated to the new spelling. `--help` output therefore
does change, and that change is deliberate and is the one exception to
"behaviour unchanged"; it is also the only source edit
REQ-PKG-MARKETPLACE-007's no-source-edit clause permits, and it happens here, in
the rename step, not in the packaging step. (see RS-MARKETPLACE-001 Q2, Q4)
**Acceptance**: `ls tools/*.py` yields no filename beginning with `sdd-`; each
renamed tool's `--help` exits 0; a run-time grep over the live rename scope for
`tools/sdd-` returns zero matches outside the exemption set of
REQ-NAME-MARKETPLACE-009; `git log --follow` resolves each renamed tool to its
pre-rename history, confirming the rename was recorded as a rename; and a
run-time grep of each renamed tool's own source for its retired filename returns
zero matches, so the `prog=`, usage-block and hint-string occurrences were
renamed with it.
[Priority: must]

### REQ-NAME-MARKETPLACE-004: The live rename scope is exactly six areas
The rename must cover exactly: `skills/`, `tools/`, `docs/spec/`,
`docs/requirements/`, `CLAUDE.md`, and the README. These are the **live** corpus
— the documents that describe the system as it is now. The scope must be stated
explicitly in the plan so that a later verifier can re-derive it rather than
infer it. (see RS-MARKETPLACE-001 Q4 §Blast radius; kickoff §Decided at DISCUSS)
**Acceptance**: after the rename, a run-time grep for the retired skill-name
prefix over exactly those six areas returns zero matches outside the exemption
set of REQ-NAME-MARKETPLACE-009; the same grep over the excluded areas of
REQ-NAME-MARKETPLACE-005 returns a **non-zero** count, confirming the historical
record was left intact rather than silently swept.
[Priority: must]

### REQ-NAME-MARKETPLACE-005: The historical record is not rewritten
`docs/ws/` plans, verifications and kickoffs of closed cycles, `docs/research/`
findings, and the vendored third-party corpus under `docs/superpowers/` must
**not** be renamed. Those files record what past cycles actually did, under the
names those cycles actually used; rewriting them would make the record disagree
with the commits it describes. The dated-marker discipline this corpus uses for
superseded text is applied **once at the boundary** — one line in
`CONTRIBUTING.md` (REQ-NAME-MARKETPLACE-006) — rather than thousands of times
in place. (see kickoff §Decided at DISCUSS)
**Acceptance**: `git diff --name-only` over the implementing change lists no path
under `docs/ws/`, `docs/research/` or `docs/superpowers/` — with the single
exception of this cycle's own workstream directory `docs/ws/marketplace/`, which
is this cycle's live execution record and not a closed cycle.
[Priority: must]

### REQ-NAME-MARKETPLACE-006: One contributing line marks the naming boundary
`CONTRIBUTING.md` must carry a statement that artifacts predating the
marketplace release use the retired `sdd-` names, that this is deliberate, and
that new work uses the namespaced names. One sentence naming the boundary is the
whole requirement; it must not grow into a migration table.
(see kickoff §Decided at DISCUSS)
**Acceptance**: `CONTRIBUTING.md` contains a statement naming both the old and
the new naming form and identifying the pre-marketplace corpus as the set that
keeps the old one.
[Priority: must]

### Ordering and verification

### REQ-NAME-MARKETPLACE-007: Rename first, marketplace scaffold second
The implementation must land the rename **before** the marketplace scaffold, as
two separately verifiable steps. Rename-first leaves an intermediate state that
the skill linter can check in full — the repository with the old layout and the
new names — whereas scaffold-first verifies almost nothing and leaves the whole
rename as one undifferentiated step. Combining them removes the intermediate
state entirely and makes any regression attributable to neither change; under
`"source": "./"` the combination saves zero double-touched files, so it buys
nothing for that loss. (see RS-MARKETPLACE-001 Q4 Recommendation)
**Acceptance**: the plan orders a rename chunk strictly before every scaffold
chunk; at the close of the rename chunk, and before any manifest file exists,
the skill linter exits 0 and the drift sweep's report raises no finding that was
not present at the cycle's entry sweep — both sides compared against the entry
sweep's recorded output rather than against a pinned number.
[Priority: must]

### REQ-NAME-MARKETPLACE-008: The linter's contract rows follow the rename, proven by its self-test
The skill linter's rules that name a skill by path or by name — including every
producer/consumer contract row keyed by a `"file"` or `"files"` value — must be
updated with the rename, and the linter's own `--self-test` must pass
afterwards. The self-test copies the real skills tree, so a contract row that no
longer resolves to its target fails loudly rather than silently degrading to a
rule that checks nothing. The linter exiting 0 alone is **not** sufficient
evidence: it checks structure and marker pairs, not semantics, so a uniformly
wrong rename would still pass it. (see RS-MARKETPLACE-001 Q4 Recommendation)
**Acceptance**: `python3 tools/skill-lint.py --self-test` exits 0; a run-time
grep over the linter source for a `skills/sdd-` literal returns zero matches; the
number of contract rows keyed on a skill file is unchanged across the rename,
derived by running the same count before and after rather than pinned.
[Priority: must]

### REQ-NAME-MARKETPLACE-009: A retired-prefix lint rule, with its exemption mechanism stated here
The skill linter must gain a rule that flags a `sdd-`-prefixed skill or tool name
appearing in the live rename scope, so that the retirement does not silently
erode as new text is written. Because the rule is about text, it lives inside its
own domain, and its exemption mechanism is part of this requirement rather than
an implementation choice. The rule must skip, in this order:

1. occurrences inside **fenced code blocks** and inside **inline-backtick
   spans** — the same skip the drift sweep's orphan-id sweep already applies, so
   that a document may quote the retired form as an example without tripping the
   rule; and
2. an explicit, short **self-exemption path list carried in the rule itself**,
   naming the documents whose subject *is* the rule — `CONTRIBUTING.md`, this
   requirements file, and the linter's own source.

There is no general allowlist and no per-occurrence suppression comment: a
document that is not on the list quotes the retired form in backticks or not at
all. (see RS-MARKETPLACE-001 Q4 §Self-reference hazard)
**Acceptance**: the linter's `--self-test` fixture contains a bare retired-prefix
occurrence (flagged), a backticked one (not flagged), a fenced one (not flagged)
and one in a self-exempt file (not flagged), and the self-test asserts exactly
that outcome; on the live repository the rule raises zero findings.
[Priority: must]

### REQ-NAME-MARKETPLACE-010: The rename dangles existing symlink installs, and says so
Renaming the skill directories breaks any existing install that reaches them by
symlink. On the author's machine ten `~/.claude/skills/sdd-*` symlinks point at
`skills/sdd-*` in this repository; after the rename each target no longer exists.
The worktree defers the break until the branch merges, which is why this is a
documented operator step rather than a blocking defect — but the corpus must not
imply a clean rename. `CONTRIBUTING.md` must therefore state the hazard and the
operator action: at merge, an existing symlink-based install is either
**re-pointed** to the new directory names or **retired** in favour of
`/plugin install sdd@sdd-commons`, which is the install path this cycle exists to
provide and the one this repository recommends. The action itself is the
operator's, taken after DONE, alongside the local-directory rename recorded in
`index.md` §Out of Scope; this requirement covers only that it is written down.
(see kickoff §Decided at DISCUSS; REQ-NAME-MARKETPLACE-001)
**Acceptance**: `CONTRIBUTING.md` contains a statement naming symlink-based
installs of the pre-rename skill directories, saying they dangle when this change
merges, and naming both operator actions (re-point, or retire in favour of the
plugin install); `index.md` §Out of Scope's local-directory entry names the same
post-DONE step. No check is made against any path outside this repository.
[Priority: must]
