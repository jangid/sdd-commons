---
status: Approved
last_updated: 2026-09-21
requires:
  - REQ-NAME-MARKETPLACE-001
  - REQ-NAME-MARKETPLACE-002
  - REQ-NAME-MARKETPLACE-003
  - REQ-NAME-MARKETPLACE-004
  - REQ-NAME-MARKETPLACE-005
  - REQ-NAME-MARKETPLACE-006
  - REQ-NAME-MARKETPLACE-007
  - REQ-NAME-MARKETPLACE-008
  - REQ-NAME-MARKETPLACE-009
  - REQ-NAME-MARKETPLACE-010
---

# Skill Namespace Rename

## Overview

The skills carry a redundant `sdd-` prefix that exists only because skills sit
in a flat global namespace today. A plugin prefix **is** that namespace, so once
the repository ships as the `sdd` plugin the components surface as
`sdd:orchestrate`, `sdd:implement`, `sdd:chunk-verifier` — matching
`superpowers:brainstorming` rather than a stuttering doubled name.

This is the larger half of the cycle by blast radius and it is **code** as well
as text: the skill linter carries contract rows keyed on skill paths and skill
names and is the single densest rename surface in the repository.

**Note on this document.** This spec is about a text rule and therefore lives
inside the rule's own domain: every occurrence of the retired form below is
deliberately written inside a backtick span or a fenced block. See
§Self-reference and the exemption mechanism, and Q-IMPL-MARKETPLACE-001.

## Design

### The rename surfaces

| Surface | Change | Invariant after |
|---|---|---|
| `skills/<dir>/` | directory basename drops the leading `sdd-` | basename has no retired prefix |
| `skills/<dir>/SKILL.md` frontmatter `name` | updated to the new basename | `name` string-equals the directory basename (the repository's existing convention, unchanged) |
| `tools/*.py` filenames | drop the leading `sdd-` | `ls tools/*.py` yields no prefixed filename |
| tool source self-references | `prog=`, usage/`--help` block, user-facing hint strings | each tool's own source contains no occurrence of its retired filename |
| cross-skill references inside `skills/` | name the sibling by **bare new name** | no `skills/<other-skill>/…` reference exists |
| the skill linter's keyed rules | every rule and contract row keyed by a skill path or skill name follows the rename | `--self-test` passes |

Tool **behaviour, flags and exit codes are unchanged** — this is a filename
change, not a contract change. The one deliberate exception is `--help` output,
which changes because the tool's own name string changes; that is also the
**only** source edit permitted to a bundled tool anywhere in the cycle, and it
happens here rather than in the packaging step
(`marketplace-packaging.md`, REQ-PKG-MARKETPLACE-007). Its exact extent — a
sibling-lookup path and two hint strings beyond `prog=` and `--help` — is
recorded as Q-IMPL-MARKETPLACE-004, and the two reference forms rewritten
alongside it as Q-IMPL-MARKETPLACE-005.

### Name coupling, not path coupling

All cross-skill references inside `skills/` name a sibling by its bare new
name. Name coupling is what makes the single-plugin decision safe and what lets
a skill directory move without breaking its siblings. Two reference forms are
therefore forbidden after the rename: any `skills/<other-skill>/…` path, and in
particular the `skills/<other-skill>/references/<file>` form, which the linter
treats as fail severity.

### The live rename scope is exactly six areas

The rename covers exactly:

```
skills/   tools/   docs/spec/   docs/requirements/   CLAUDE.md   the README
```

These are the **live** corpus — the documents that describe the system as it is
now. The scope is stated explicitly in the plan so a later verifier can
**re-derive** it rather than infer it.

**Excluded, deliberately**: `docs/ws/` plans, verifications and kickoffs of
closed cycles; `docs/research/` findings; and the vendored third-party corpus
under `docs/superpowers/`. Those record what past cycles actually did, under the
names those cycles actually used; rewriting them would make the record disagree
with the commits it describes. The exclusion is **positively verified**: the
same grep that must return zero over the six live areas must return a
**non-zero** count over the excluded areas, proving the historical record was
left intact rather than silently swept.

The single exception inside `docs/ws/` is this cycle's own workstream directory
`docs/ws/marketplace/`, which is a live execution record, not a closed cycle.

Two consequences of drawing the line here are recorded rather than left
implicit: a path **into** the excluded corpus that appears inside a live
document is quoted, never rewritten, because rewriting it would break the link
(Q-IMPL-MARKETPLACE-006); and the shared aggregate `docs/requirements/traceability.md`
is left unswept, because it is regenerated from the per-workstream files the
exclusion covers (Q-IMPL-MARKETPLACE-008).

The dated-marker discipline this corpus uses for superseded text is applied
**once at the boundary** — one statement in `CONTRIBUTING.md` — rather than
thousands of times in place.

### Ordering: rename first, scaffold second

The rename lands **strictly before** any scaffold work, as two separately
verifiable steps.

- Rename-first leaves an intermediate state the linter can check **in full**:
  the repository with the old layout and the new names. The linter's root is
  its own script location (unchanged by the rename) and its checks are
  structural, so it still runs — and its contract rows verify that every
  producer/consumer marker pair still resolves, which is exactly the class of
  breakage a mass rename causes.
- Scaffold-first verifies almost nothing and leaves the whole rename as one
  undifferentiated step.
- Combining them removes the intermediate state entirely and makes a regression
  attributable to neither change. Under `"source": "./"` the scaffold moves zero
  existing files, so the combination saves **zero** double-touched references —
  it buys nothing for that loss.

The verifiable intermediate state is: **the skill linter exits 0**, and the
drift sweep's report raises no finding absent from the cycle's entry sweep —
both compared against the entry sweep's recorded output, not against a number.

### The linter follows the rename, proven by its self-test

Every linter rule that names a skill by path or by name — including every
producer/consumer contract row keyed by a `"file"` or `"files"` value — is
updated with the rename, and the linter's own `--self-test` must pass
afterwards. The self-test copies the real skills tree, so a contract row that no
longer resolves to its target fails loudly rather than silently degrading into a
rule that checks nothing.

**The linter exiting 0 is explicitly not sufficient evidence**: it checks
structure and marker pairs, not semantics, so a uniformly wrong rename would
still pass it. Two further invariants close that gap: the linter source contains
no literal prefixed skill path, and the **number of contract rows keyed on a
skill file is unchanged** across the rename — derived by running the same count
before and after.

### The retired-prefix rule

The linter gains a rule that flags a retired-prefix skill or tool name appearing
in the live rename scope, so the retirement does not erode as new text is
written.

**Skip order** (evaluated in this order):

1. occurrences inside **fenced code blocks** and inside **inline-backtick
   spans** — the same skip the drift sweep's orphan-id sweep already applies, so
   a document may quote the retired form as an example without tripping the rule;
2. an explicit, short **self-exemption path list carried in the rule itself**,
   naming the documents whose subject *is* the rule.

There is **no** general allowlist and **no** per-occurrence suppression comment:
a document not on the list quotes the retired form in backticks or not at all.

**The rule's self-test fixture is synthesized, not stored.** The four-occurrence
fixture the rule is tested against (bare, backticked, fenced, and inside a
self-exempt file) is written into a temporary directory at `--self-test` time and
discarded afterwards; no file carrying its deliberate **bare** occurrence exists
on disk in the repository. This is the same shape the self-test already uses when
it copies the real skills tree into a scratch root, so it adds no new mechanism.
The requirement does not say where the fixture lives; the choice is recorded as
Q-IMPL-MARKETPLACE-002 rather than left implicit.

Two paths are likewise outside the scope the rule **walks**, for one shared
reason — a finding there is unfixable by construction, not merely inconvenient.
`tools/fixtures/` holds bytes that are part of what they test and that
`pre-commit.md` (REQ-PC-MARKETPLACE-005) freezes (Q-IMPL-MARKETPLACE-007); the
shared aggregate `docs/requirements/traceability.md` is **derived** from the
per-workstream files this rename excludes, so sweeping it would only
desynchronize it from its own sources (Q-IMPL-MARKETPLACE-008). Both are
scope boundaries carried in the rule beside the scope list, not occurrence
allowlists, and the exemption list stays at four entries.

The alternative — storing the fixture under `tools/fixtures/` — is rejected
because `tools/` is one of the six live rename-scope areas: the live sweep would
flag the fixture's deliberate bare occurrence, and the exemption list (four
documents, none of them a fixture) does not and should not cover it. Extending
the list to a fixture would make the rule exempt the one file written to prove it
fires. Synthesizing dissolves the conflict instead of papering over it, so both
halves of REQ-NAME-MARKETPLACE-009's criterion — exactly one flag on the fixture,
zero findings on the live repository — hold simultaneously.

### Self-reference and the exemption mechanism

The self-exemption path list is: `CONTRIBUTING.md`, the naming requirements file
`docs/requirements/integration/naming.md`, the linter's own source, and **this
spec** — the four documents whose subject is the rule itself.

This spec's inclusion is a design extension of the requirement's enumerated
three; it is filed as Q-IMPL-MARKETPLACE-001 rather than applied silently. The
extension is belt-and-braces only: this spec is written so that **every**
occurrence of the retired form sits inside a backtick span or a fenced block, so
it passes skip (1) regardless of skip (2). The reason to list it anyway is that
a future edit to this spec should not be able to break the build by dropping a
pair of backticks in a document that exists to discuss the forbidden string.

`CLAUDE.md` is deliberately **not** on the list. It is prose about the system,
not about the rule, and must reach zero bare occurrences on its own
(`project-docs.md`, REQ-DOCS-MARKETPLACE-005).

### Symlink installs dangle, and the corpus says so

Renaming the skill directories breaks any existing install that reaches them by
symlink: a symlink whose target is a prefixed skill directory has no target
after the rename. The worktree defers the break until the branch merges, which
is why this is a documented operator step rather than a blocking defect — but
the corpus must not imply a clean rename.

`CONTRIBUTING.md` therefore states the hazard and the two operator actions taken
at merge: **re-point** an existing symlink-based install to the new directory
names, or **retire** it in favour of `/plugin install sdd@sdd-commons`, which is
the install path this cycle exists to provide and the one this repository
recommends. The action itself is the operator's, taken after DONE, alongside the
local-directory rename recorded in `index.md` §Out of Scope. This design covers
only that it is written down; **no check is made against any path outside this
repository**.

## Acceptance Criteria

Every criterion derives both sides at run time; no corpus-measured count appears
as a literal. `RETIRED` below denotes the retired-prefix search pattern, built
in the checking script rather than pasted into prose. All tree walks exclude any
nested `.worktrees/` path.

- [ ] For every directory under `skills/` containing a `SKILL.md`: the basename does not match `RETIRED`, and the file's frontmatter `name` string-equals the basename — both read from disk at run time. `python3 tools/skill-lint.py` exits 0 (REQ-NAME-MARKETPLACE-001).
- [ ] A run-time grep over `skills/` for a cross-skill reference of the form `skills/<other-skill>/…` returns zero matches, and the same grep for the `skills/<other-skill>/references/<file>` form likewise returns zero (REQ-NAME-MARKETPLACE-002).
- [ ] `ls tools/*.py` yields no filename matching `RETIRED`; each renamed tool's `--help` exits 0; a run-time grep over the live rename scope for a prefixed `tools/` path returns zero matches outside the exemption set; `git log --follow` resolves each renamed tool to its pre-rename history; and a grep of each renamed tool's own source for its retired filename returns zero matches (REQ-NAME-MARKETPLACE-003).
- [ ] A run-time grep for `RETIRED` over exactly the six live areas returns zero matches outside the exemption set, **and** the same grep over `docs/ws/` (excluding `docs/ws/marketplace/`), `docs/research/` and `docs/superpowers/` returns a non-zero count (REQ-NAME-MARKETPLACE-004, REQ-NAME-MARKETPLACE-005).
- [ ] `git diff --name-only` over the implementing change lists no path under `docs/ws/`, `docs/research/` or `docs/superpowers/`, except paths under `docs/ws/marketplace/` (REQ-NAME-MARKETPLACE-005).
- [ ] `CONTRIBUTING.md` contains a statement naming both the retired and the namespaced naming form and identifying the pre-marketplace corpus as the set that keeps the retired one (REQ-NAME-MARKETPLACE-006).
- [ ] The plan orders a rename chunk strictly before every scaffold chunk, checkable by reading the plan's chunk order; at the close of the rename chunk, and before any manifest file exists (`test ! -e .claude-plugin/marketplace.json`), the skill linter exits 0 and the drift sweep's report contains no finding absent from the recorded entry-sweep output (REQ-NAME-MARKETPLACE-007).
- [ ] `python3 tools/skill-lint.py --self-test` exits 0; a run-time grep over the linter source for a prefixed `skills/` literal returns zero matches; the count of contract rows keyed on a skill file is equal before and after the rename, obtained by running the same count command at both points (REQ-NAME-MARKETPLACE-008).
- [ ] The linter's `--self-test` fixture — synthesized into a temporary directory at self-test time per §The retired-prefix rule, so that `test ! -e` succeeds for it in the checked-out tree — contains four occurrences of the retired form (bare, backticked, fenced, and inside a self-exempt file), and the self-test asserts exactly one flag (the bare one); on the live repository the rule raises zero findings (REQ-NAME-MARKETPLACE-009).
- [ ] `CONTRIBUTING.md` contains a statement naming symlink-based installs of the pre-rename skill directories, stating that they dangle when this change merges, and naming both operator actions (re-point, or retire in favour of the plugin install); `index.md` §Out of Scope's local-directory entry names the same post-DONE step (REQ-NAME-MARKETPLACE-010).

## Implementation Questions

### Q-IMPL-MARKETPLACE-001: The self-exemption list gains this spec
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Self-reference and the exemption mechanism
**Date**: 2026-09-21 (specs stage)

**Context**: REQ-NAME-MARKETPLACE-009 enumerates the self-exemption path list as
`CONTRIBUTING.md`, the naming requirements file, and the linter's own source. It
also requires the list to stay short and to name "the documents whose subject
*is* the rule".

**Decision**: add `docs/spec/skill-namespace-rename.md` as a fourth entry. It is
this cycle's design document *for* the rule, it lives inside `docs/spec/` — one
of the six live rename-scope areas its own rule sweeps — and it is exactly the
class of document the requirement's own phrasing describes. The list stays at
four entries and the "no general allowlist, no per-occurrence suppression"
constraint is untouched.

**Impact**: none on behaviour. This spec is written so every retired-prefix
occurrence is already backticked or fenced and would pass skip (1) with the list
unchanged; the entry guards against a future edit to this document dropping a
backtick pair. If a reviewer prefers the literal three-entry list, remove the
entry and the spec still passes — the criterion above is unaffected.

### Q-IMPL-MARKETPLACE-002: The retired-prefix self-test fixture is synthesized, not stored
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The retired-prefix rule
**Date**: 2026-09-21 (specs stage)

**Context**: REQ-NAME-MARKETPLACE-009 requires the self-test fixture to contain a
**bare** retired-prefix occurrence (the one the rule must flag) and, in the same
criterion, that the rule raises zero findings on the live repository. It does not
say where the fixture lives. If it were stored under `tools/fixtures/` — where
this repository's existing fixtures live — the live sweep would flag that
deliberate bare occurrence, because `tools/` is one of the six live rename-scope
areas, and the two halves of the criterion would contradict each other.

**Decision**: the fixture is written into a temporary directory at `--self-test`
time and discarded afterwards. No file carrying the bare occurrence exists on
disk in the repository, so the live sweep has nothing to flag and both halves
hold. The alternative — storing it and adding it to the self-exemption list —
was rejected: the list names the four documents whose *subject is the rule*, and
extending it to a fixture would exempt the one file written to prove the rule
fires.

**Impact**: none on the rule's behaviour or on the exemption list, which stays at
four entries. It constrains the self-test's implementation to synthesize its
fixture, which is the same shape the self-test already uses when it copies the
real skills tree into a scratch root.
### Q-IMPL-MARKETPLACE-004: The bundled-tool source edit reaches the sibling lookup and the hint strings
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The rename surfaces
**Date**: 2026-09-21 (implement stage, Chunk 1)

**Context**: the table above permits exactly one source edit to a bundled tool —
`prog=`, the usage/`--help` block and user-facing hint strings — and forbids
every other edit, so the packaging step can assert an empty diff over the
bundled tools. The drift sweep locates the skill linter **by filename** to run
its delegated sweeps, which is neither a `prog=` string nor `--help` text.

**Decision**: the edit was extended past `prog=`/`--help` to that sibling-lookup
path in `tools/gc.py` and to both bundled tools' user-facing hint strings.
Stopping at `--help` would have left the sweep printing a "linter missing" error
— a behaviour change, which the spec forbids outright. Behaviour preservation
outranks the diff-hygiene restriction; no later chunk edits these files, so the
packaging chunk's empty-diff assertion still holds from its own reference sha.

**Impact**: none on any tool's flags, exit codes or output beyond the renamed
name strings. The restriction itself is unchanged: this is the same single
permitted edit, described at its true extent.

### Q-IMPL-MARKETPLACE-005: The skill-family glob and the dispatch placeholder take the namespaced form
**Tier**: 2 (spec ambiguity)
**Spec reference**: §Name coupling, not path coupling
**Date**: 2026-09-21 (implement stage, Chunk 1)

**Context**: two reference forms inside `skills/` name the skill family as a
pattern rather than naming one sibling: a glob over the family, and a dispatch
placeholder that interpolates a stage name into a prefixed spelling. Neither is
a `skills/<other-skill>/…` path, so neither is covered by the forbidden forms
above.

**Decision**: the glob was rewritten to the plugin-namespaced form and the
placeholder reduced to the bare `{stage}` token. One install-instruction line in
the driver's USAGE was **reworded** instead of rewritten, because there the glob
denotes on-disk directory names, which is a different referent from the plugin
namespace.

**Impact**: none on behaviour. It keeps name coupling total inside `skills/`:
after the rename no reference inside a skill reaches a sibling by a path or by a
retired spelling.

### Q-IMPL-MARKETPLACE-006: A path into the excluded corpus is quoted, not rewritten
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The live rename scope is exactly six areas
**Date**: 2026-09-21 (implement stage, Chunks 1–2)

**Context**: live documents cite artifacts in the deliberately excluded corpus —
a findings directory under `docs/research/` whose own name carries the retired
prefix. The live sweep must reach zero, but rewriting such a citation would
point it at a directory that does not exist.

**Decision**: the path is left verbatim and quoted in a backtick span, which
skip (1) of the retired-prefix rule already skips. Where the citation was a
Markdown link, the link was replaced by the same backticked path, because a link
target cannot sit inside a backtick span and the rule skips no link target.

**Impact**: none on the rule, which gains no case. It fixes the reading of the
zero-over-six-areas criterion: "zero **bare** occurrences", not "zero mentions".

### Q-IMPL-MARKETPLACE-007: `tools/fixtures/` is outside the walked scope
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The retired-prefix rule
**Date**: 2026-09-21 (implement stage, Chunk 2)

**Context**: `tools/` is one of the six live areas, and `tools/fixtures/` holds
frozen fixtures that carry retired-prefix names in their recorded bytes. Those
bytes are part of what they test, and `pre-commit.md` (REQ-PC-MARKETPLACE-005)
requires them to stay byte-identical across this cycle — so a finding raised
there could be satisfied neither by editing the file nor by exempting it.

**Decision**: the rule does not walk `tools/fixtures/`. This is a
directory-level scope boundary carried in the rule beside the scope list, not a
per-occurrence allowlist, and the self-exemption list stays at its four
documents. The self-test asserts the boundary directly: a synthesized fixture
file under `tools/fixtures/` is absent from the walked set.

**Impact**: the rule's live scope is the six areas minus one frozen fixture
directory. Anything a future cycle unfreezes is swept again by deleting one
tuple entry.

### Q-IMPL-MARKETPLACE-008: The derived aggregate traceability is outside the walked scope
**Tier**: 2 (spec ambiguity)
**Spec reference**: §The live rename scope is exactly six areas
**Date**: 2026-09-21 (implement stage, Chunk 2)

**Context**: `docs/requirements/traceability.md` sits inside a live area and
carried by far the largest share of the corpus's retired-prefix occurrences. It
is also **derived**: regenerated, never hand-merged, from the per-workstream
files under `docs/ws/`, which this cycle deliberately excludes. Sweeping it was
tried first and the drift sweep answered immediately — the swept aggregate no
longer equalled `regenerate(docs/ws/*/traceability.md)`, raising a
`[traceability-aggregate]` warning absent from the cycle's entry sweep, which
§Ordering forbids at the rename chunk's close.

**Decision**: the rule does not walk the aggregate, and its bytes are left
unchanged. Sweeping it is not a fix but a desynchronization: the only way to
make a swept aggregate stable would be to sweep the per-workstream sources,
which REQ-NAME-MARKETPLACE-005 forbids and whose verification asserts that no
`docs/ws/` path appears in the implementing change at all.

**Impact**: the rule's live scope is the six areas minus one frozen fixture
directory and one derived file. The aggregate keeps the retired spellings its
per-workstream sources record — the same historical-fidelity argument the
exclusion rests on — and regeneration stays a no-op rename-wise. A future cycle
that sweeps `docs/ws/` removes this boundary with the entry it added.
