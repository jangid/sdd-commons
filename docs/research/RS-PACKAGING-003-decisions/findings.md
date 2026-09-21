---
id: RS-PACKAGING-003
workstream: packaging
status: Complete
date: 2026-09-21
last_updated: 2026-09-21
research_refs: [RS-PACKAGING-002]
code_pinned_at: 20f26ec
questions:
  - "D1 — Under the two-root split, the 56 suite rows resolve against the suite root. Is vacuous consumer pass the intended behaviour, or is a CLI surface needed?"
  - "D2 — After the root move `.claude-plugin/` exists at both roots. Which root does the retired-prefix scope bind it to, and what detects a wrong binding?"
  - "D3 — Is there a sound form for the `FILES_SWEPT` acceptance criterion?"
  - "D4 — Can the two-root behavioural fixture be built, and in what shape?"
budget: "12 tool calls, 0 test runs"
---

# Research: RS-PACKAGING-003 — the four open decisions

## Scope

Four decisions left open by `RS-PACKAGING-002`. Everything that spike measured —
the `git-subdir` install behaviour, the 56/40/9/7/13/4 populations, the 45/154/199
costing, option (B) and its set-union containment semantics, the absence of
`tools/skill-lint.rules.json` — is **input** here, cited and never re-derived
(`docs/research/RS-PACKAGING-002-root-interface/findings.md`).

Vocabulary used below, all from `RS-PACKAGING-002`: **corpus root** is the tree
being linted (a consumer's repository, or this one); **suite root** is the root of
the shipped `sdd` plugin — `plugins/sdd/` here after the move, the installed
plugin cache in a consumer's environment; **option (B)** defaults `suite_root` to
the script's own plugin root, gives `corpus_root` the positional argument, and
sweeps the generic walk over the set union of resolved absolute paths, admitting
`suite_root/skills/**` only when the suite root is contained in the corpus root
(equality counts as containment).

One caveat governs all four decisions and is stated **here once**: every
recommendation below is a design choice over measured evidence, not a measured
result; each names its own falsifier, none has been executed, and each heading
carries a confidence word (high = premise verifiable in the code read below; low =
pure design, nothing yet built).

Code read for this spike, every line anchor below pinned at commit `20f26ec`:
`tools/skill-lint.py` — `Linter.__init__` (:417), `skill_files()` (:442),
`retired_scope_files()` (:746), `check_retired_prefix()` (:769), `check_required()`
(:539), `check_template_drift()` (:594-613), `TEMPLATE_SOURCE`/`TEMPLATE_PAIRS`
(:304-309), the scope constants (:379-384), the policed-areas block (:1250-1259),
and `main()`'s argparse (:1295-1312).

## D1 — Consumer suite-row behaviour — **CLOSED** (confidence: high)

**Decision: adopt the flip as the rows' meaning, carried by the two-root
constructor parameter; the `--suite-root` CLI surface is deferred to
requirements. Do not add `--no-suite-rules`.**

The 56 suite-gated rows name this suite's own files (`skills/<name>/SKILL.md` and
the marker contracts inside them) — an integrity check on the shipped plugin, not
a portable style rule. Today a consumer's run resolves them against the consumer's
tree, where those files do not exist, so the consumer receives failures naming
skills they never wrote (population per `RS-PACKAGING-002`; the consumer failure
count is unmeasured). That is loud about the wrong tree, not worth preserving.

Under option (B) they resolve against the suite root, where the files do exist,
and pass — checking the thing they describe. The behaviour change is a
**retarget, not a weakening**: the rows never had consumer meaning to lose.

**Amended F11 target, stated once:** the suite rows assert the integrity of the
*installed suite*; what asserts anything about a *consumer's* corpus is the ungated
set — `FORBIDDEN`'s 13 rows, frontmatter, links, size, drift phrases — which keeps
resolving against the corpus root and failing loudly there. Nothing downstream may
restate the pre-split F11 wording.

**That enumeration carries two deliberate exceptions, one in each direction.**
(i) *Ungated but suite-bound:* the file has exactly two `suite_rules` guards, :540
(`check_required`) and :599 (`check_template_drift`); `check_retired_prefix()`
(:769) has none, so it runs ungated in a consumer tree — yet it polices *this
suite's own* retired filename prefix, a fact of this repository's rename history
with no meaning elsewhere. Its suite-history-specific directories (`skills`,
`tools`, `agents`) are therefore bound to the **suite** root under D2 by intent,
while its corpus-meaningful ones (`docs/spec`, `docs/requirements`) stay on the
corpus root. (ii) *Gated but corpus-bound:* `TEMPLATE_PAIRS` is `suite_rules`-gated
(:599) yet its `spec` side keys on `docs/spec/**`, which D2 binds to the corpus
root; in a consumer tree that side does not exist, and :610-613 would emit four
`warn` findings naming this suite's spec files there — so D2 skips the spec side
when the roots are disjoint. *Ungated* and *consumer-facing* coincide everywhere
except these two.

**Why the constructor parameter is decided here and the CLI flag is not.** The D4
fixtures pin their roots in-process (`Linter(rp_root, suite_rules=False)` at :845,
:979, :1183, :1215, :1270) and never reach argparse, so the constructor parameter
is not in question. The CLI flag rests on one case — a vendored or
repository-local plugin cache (the accepted residue in `RS-PACKAGING-002`) where
the containment default is wrong and no in-process construction can correct it — a
mitigation, not a closure, so `--suite-root` is a requirements-stage call.
`--no-suite-rules` is rejected outright as a disable switch on the checks most
likely to be inconvenient, the silent-disable class that spike already rejected
externalised rule data for; `suite_rules=False` stays a fixture argument.

**Cost:** one constructor parameter and the root bindings in D2; one argparse
option more if requirements adopts the CLI surface. No new artifact.

**Falsifier:** run the linter from a consumer repository containing no `skills/`
directory; the suite rows must be silent and the ungated checks must still report.

## D2 — The dual-rooted checks — **CLOSED** (confidence: medium)

**Decision: bind both dual-rooted checks per entry, not per root.** For the
retired-prefix scope, bind `.claude-plugin` and the six scope files to the union
of both roots; for `TEMPLATE_PAIRS`, bind each side to the root its paths follow.

`retired_scope_files()` (:746) walks `RETIRED_SCOPE_DIRS` and `RETIRED_SCOPE_FILES`
under a single `self.root`. Split into entries:

| Scope entry | Root after the move |
|---|---|
| `skills`, `tools`, `agents` | suite root (see D1's exception) |
| `docs/spec`, `docs/requirements` | corpus root |
| `.claude-plugin` | **both** (union) |
| `CLAUDE.md`, `README.md`, `README.org`, `CONTRIBUTING.md`, `LICENSE`, `.pre-commit-config.yaml` | **both** (union) |

The union is over **resolved absolute paths**, deduplicated (option (B)'s own
relation for the generic walk), so when `suite_root == corpus_root` — an unmoved
repository, or a consumer against a non-vendored install — the entry set is today's.

The union keeps `marketplace.json` in scope — it stays at the repository root
while `plugin.json` moves, and a single-root binding drops one or the other — and
covers the root files `CLAUDE.md` and `.pre-commit-config.yaml`, which the move
edits and which may exist at either root. `README.org` (:381, :1252) is tabulated
but absent from the tree; the carried repair `Q-IMPL-MARKETPLACE-017` drops it
from both tuples, leaving five names and the union binding unchanged.

**`TEMPLATE_PAIRS` is the second dual-rooted, `suite_rules`-gated check, and it
splits per side.** `TEMPLATE_SOURCE` (:304) is
`skills/orchestrate/references/dispatch-templates.md`, which **moves** to the
suite root; every row's `spec` key is `docs/spec/harness-chunk-verifier.md` or
`docs/spec/adversarial-verify.md`, which **stay** at the corpus root. Binding the
gated checks wholesale to the suite root resolves the spec side under
`plugins/sdd/docs/spec/`, which will not exist — and the docstring at :594-597
states that a spec file absent from the root **warns, never fails**. All four
rows would then degrade silently to warnings here the moment the move lands: the
silent-disable class D1 invokes to reject `--no-suite-rules`, rejected here too.
Bind the source side to the suite root and the `spec` side to the corpus root,
using the table's per-entry root tag. When the roots are **disjoint** (a consumer
run) the `spec` side is **skipped, not warned** — :610-613 would otherwise name this
suite's spec files in the consumer's tree, the defect D1 retargets the rows to
avoid; under containment the spec side is checked and an absent spec keeps warning.
(`RS-PACKAGING-001` flagged this dual rooting.)

**What detects a wrong binding: a membership assertion, not a count.** In a
two-root self-test fixture, assert that the set returned by
`retired_scope_files()` contains **both** `<suite_root>/.claude-plugin/plugin.json`
and `<corpus_root>/.claude-plugin/marketplace.json`. Any one-root binding drops
exactly one of the two, so the assertion fails on the defect it exists for.

The per-root policed-**file count** named as a candidate in `RS-PACKAGING-002` is
rejected for the reason D3 rejects a literal corpus count: files under a policed
area grow by ordinary contribution, so a pinned count false-positives on a correct
change and an unpinned one proves nothing. The existing block at :1250-1259, which
pins `RETIRED_SCOPE_DIRS`/`RETIRED_SCOPE_FILES` against literal name tuples, is
**retained unchanged** — it catches an area dropped from the enumeration, but not a
wrong root binding, since directory names survive one intact.

**Cost:** the entry table becomes data (a per-entry root tag on the two scope
constants and on the two `TEMPLATE_PAIRS` sides), the disjoint-root skip on the
spec side, plus one self-test fixture and its assertions.

**Falsifiers:** bind `.claude-plugin` to one root only; the membership assertion
must fail. Bind both `TEMPLATE_PAIRS` sides to the suite root here after the move;
all four rows must then emit the absent-spec warning and none may fail — the
observation the per-side binding exists to prevent. Run with disjoint roots; no
`template-drift` finding may appear.

## D3 — `FILES_SWEPT` — **CLOSED, by replacing the count with two properties** (confidence: medium)

**Decision: no absolute corpus count is sound. Replace the criterion with a
construction guard plus a fixture-local exact count.**

The criterion's job is unchanged: catch a generic walk bound to the wrong root
that sweeps zero files, and catch a tree swept twice. Neither job needs the
corpus's size — and every formulation encoding it fails (a literal fails on
ordinary contribution; a `git ls-files` comparand compares a working-tree walk
against a tracked list and hard-codes a path meaningless in a consumer repository;
re-deriving the comparand from `corpus_root` re-implements `skill_files()`'s own
`rglob` and asserts it against itself).

This retires `FILES_SWEPT=25` as an **acceptance criterion** only. It does not
retire the flag's `corpus: FILES_SWEPT=<n>  policed-areas=<n>` output line, which
keeps being emitted as informational output with no pinned comparand.

The replacement is two assertions:

1. **Duplicate-freeness (live, every run, any repository).** The swept list,
   resolved to absolute paths, contains no path twice —
   `len(swept) == len({p.resolve() for p in swept})`. Under option (B) the walk is
   a set union over resolved absolute paths and `skill_files()` (:442) is a
   `sorted(rglob(...))` over one root, so this cannot fail for an implementation
   built as specified: it pins that the union stays a **set**, never rebuilt as
   list concatenation by a later edit — a construction guard. The double-sweep
   mode it guards against is realizable **only when the two roots are equal**,
   where both walk terms name one subtree and a file is reachable from both;
   D4's case C is where that is exercised. **Observable on failure:** a
   `fail`-severity finding in the run's own findings list (the `flag()` default,
   :429) — not a warning, an exception or a bare exit code.
2. **Exact count in the fixture (self-test only).** The two-root fixtures of D4
   seed a known number of `.md` files, and the self-test asserts the sweep returns
   exactly that number. A literal is sound here because a fixture does not grow by
   contribution. A zero-sweep from a mis-bound root fails this immediately.

**Live zero-sweep detection is deliberately given up.** A bare `FILES_SWEPT >= 1`
is not adopted because an empty sweep is legitimate in a consumer repository with
no `skills/`; the conditioned form — a floor applied only when the corpus root
contains `skills/` — reads its condition through the same root binding it is meant
to test, so a mis-bound root makes it vacuous rather than failing. Zero-sweep is
therefore caught only at self-test time, by (2) and by the D4 fixtures, each
seeding a violation and asserting a **finding**, never silence.

**Cost:** one live assertion inside the sweep, one fixture literal per D4 fixture.

**Falsifier:** bind the corpus walk to a root containing no corpus; the fixture
count assertion must fail. Rebuild the union as list concatenation over two
**equal** roots; assertion (1) must fail.

## D4 — The two-root behavioural fixture — **CLOSED, as two fixtures and an equality case** (confidence: low)

**Decision: the criterion cannot be built as one fixture, and does not need to be.
Build two, one per deployment shape, plus an equality-root case for dedup.**

The obstruction is real and is not worked around: option (B) admits
`suite_root/skills/**` into the corpus walk **only** when the suite root is
contained in the corpus root, so in a disjoint pair the walk never visits the suite
skills and a seeded walk-class violation there is correctly invisible. Splitting by
shape turns that obstruction into the thing asserted.

**Fixture A — nested roots (the shipping shape).** `suite_root =
corpus_root/plugins/sdd`, the shape this repository will have after the move and so
the shape whose behaviour must be pinned. Seed a walk-class violation (a forbidden
phrase or bad frontmatter) under `suite_root/skills/**` and assert it is reported,
with its rendered relative path computed against the root it was walked from.

Nesting does not weaken what fixture A demonstrates: it asserts **per-root path
rendering**, which is exactly what collapses when the two bindings are conflated.
It does not assert single-sweep, and cannot — under nesting the walk terms
`corpus_root/skills` and `corpus_root/plugins/sdd/skills` are disjoint subtrees, so
no seeded file is reachable from both, as option (B)'s admission rule implies.

**Case C — equal roots (the unmoved repository; a consumer against a non-vendored
install).** `suite_root == corpus_root`, the one geometry where both walk terms name
the same subtree and a file *is* reachable from both. Seed one walk-class violation
under `skills/**` and assert it is reported **exactly once** — the assertion a
list-concatenation union fails and a set union passes. It needs no new fixture tree:
it is fixture A's corpus tree constructed with both roots equal.

**Fixture B — disjoint roots (the consumer shape).** `suite_root` outside
`corpus_root`. Assert two things: a **table-row** violation (from `REQUIRED`,
`VERSION_GATED_SKILLS` or `V4_CONTRACT_SKILLS`, which resolve `root / rel` directly
and bypass the walk) seeded under the suite root **is** reported; and a walk-class
violation seeded under `suite_root/skills/**` is **not**, asserted as a named absent
finding for a specific seeded path so it distinguishes "correctly excluded" from
"switched off". Add the D2 membership assertion and the D3 fixture count here, which
together prove both roots were walked.

No case asserts exit-code silence, so the objection that sank the silence-based
formulation in `RS-PACKAGING-002` does not apply: every assertion names a finding
present, or a seeded path absent amid other findings.

**The third recorded formulation — narrowing the containment rule so the walk term
does not depend on containment — is declined**, not for a recorded defect
(`RS-PACKAGING-002` records none) but because it changes option (B)'s *shipping
semantics* to make a test easier to write. If requirements rejects the containment
rule on its merits, this returns there as a change to option (B).

**Cost:** two fixture trees in the existing self-test harness plus one extra
construction for case C, all needing D1's two-root constructor parameter.

**Falsifier:** swap the two fixtures' expectations; each must fail.

## Open Questions

- **Whether `plugins/sdd/` carries its own `README`/`LICENSE`** (45 vs 47 installed
  files) — carried from `RS-PACKAGING-002`, still undecided; both names sit in D2's
  union-bound scope-file entry, so either answer changes which root supplies them,
  not whether they are policed.
- **The `file://`-vs-GitHub install gap** and the unrun non-conventional-path
  control — both recorded in `RS-PACKAGING-002`, both out of scope here, neither
  affected by any decision above.
- **Vendored or repository-local plugin caches.** The containment rule is a proxy
  for "this repository's own suite" and is wrong for a consumer who vendors the
  plugin; the residual risk is unclosed, and it is the sole case carrying the
  deferred `--suite-root` CLI surface as distinct from the constructor parameter.

## Recommended Next Step

**Proceed to requirements.** All four decisions are closed (recommendation, cost,
falsifier, confidence). Requirements inherits the three open questions, D1's
deferred CLI surface, and the kickoff's carried repairs, under two ordering
constraints. The headline 40-row acceptance criterion reads `--print-population`
output and that flag does not exist on `tools/skill-lint.py` (argparse exposes only
`root` and `--self-test`, :1301-1303), so a task producing the flag precedes any
task that writes or evaluates that criterion; and the carried repair to
`skills/verify/SKILL.md:169` is sequenced **after** D1 and D2, whose root bindings
fix what it describes.
