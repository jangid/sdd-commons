---
id: RS-CONSUMERGEOMETRY-001
workstream: consumer-geometry
status: Complete
date: 2026-09-21
last_updated: 2026-09-21
research_refs: [RS-PACKAGING-001, RS-PACKAGING-002, RS-PACKAGING-003, RS-MARKETPLACE-001]
supersedes: RS-PACKAGING-003 (D3 only — D1, D2 and D4 are inputs; see §Supersession)
questions:
  - "Q1 — What is the full SET of checks that silently reduce, raise, or pass vacuously under a disjoint suite root, across both skill-lint.py and gc.py?"
  - "Q2 — Does REQ-PKG-MARKETPLACE-007 bind this cycle, and what evidence would a requirements amendment cite?"
  - "Q3 — Tool-side or invocation-side fix? Cost to a consumer, and interaction with the 56 suite-gated rows (RS-PACKAGING-002 D1)."
  - "Q4 — Can any gate in THIS repository observe a disjoint-geometry regression, given the plugin cache cannot be written?"
  - "Q5 — Is plugins/sdd/skills/orchestrate/tools/ reachable by any invocation, and what does removing it falsify?"
budget: "25 tool calls, 0 test runs"
---

# Research: RS-CONSUMERGEOMETRY-001 — the disjoint suite root

## Questions

The kickoff's §The observation is carried as **evidence** and is not re-derived
here. Everything below is measured against repository HEAD `e95671f` (branch
`consumer-geometry`), 2026-09-21, with **no edit to any tool source** and **no
write to the plugin cache**.

**Measurement technique.** The disjoint geometry is reproduced exactly as the
linter's own `--self-test` reproduces it — by constructing a `Linter` over a
scratch corpus root and a far suite root (`Linter(tr_corpus, tr_far, …)`), and,
for the observation geometry specifically, by constructing
`Linter(<repo>, ~/.claude/plugins/cache/sdd-commons/sdd/0.1.0)` — the cache is
**read** as a suite root and never written. Each of the eight checks was then
invoked individually and its finding delta recorded. Three geometries were
probed:

| Geometry | corpus root | suite root | `suite_contained()` | `walk()` files |
|---|---|---|---|---|
| **nested** (in-repo, the only geometry a gate sees naturally) | `<repo>` | `<repo>/plugins/sdd` | `True` | **25** |
| **observation** (installed tool, operator's own repo) | `<repo>` | `<cache>/sdd/0.1.0` | `False` | **0** |
| **consumer** (installed tool, foreign repo with its own `skills/`) | scratch | `<repo>/plugins/sdd` | `False` | **1** (the consumer's own) |

**Reproduction.** Copy-pasteable, machine-independent, no cache read — it
copies the suite to a scratch root, which is disjoint by construction. It
reproduces the three measurements a later stage must act on: Class B's
`walk() == 0`, `rel()`'s `ValueError`, and the 36 rebinding scope entries.

```bash
REPO=$(git rev-parse --show-toplevel)
rm -rf "$TMPDIR/cg" && mkdir -p "$TMPDIR/cg"
cp -R "$REPO/plugins/sdd" "$TMPDIR/cg/far"      # a disjoint suite root; the cache is never touched
python3 - "$REPO" "$TMPDIR/cg/far" <<'PY'
import importlib.util, sys
from collections import Counter
from pathlib import Path
repo, far = map(Path, sys.argv[1:3])
s = importlib.util.spec_from_file_location("sl", repo / "plugins/sdd/tools/skill-lint.py")
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
for label, suite in (("nested", repo / "plugins/sdd"), ("disjoint", far)):
    L = m.Linter(repo, suite)
    print(label, "contained=", L.suite_contained(), "walk=", len(L.walk()),
          "scope=", Counter(str(b) for _f, b in L.retired_scope_entries()))
    probe = next(iter((suite / "skills").rglob("SKILL.md")))
    try:
        print("   rel(suite file) ->", L.rel(probe))
    except ValueError as exc:
        print("   rel(suite file) RAISED ValueError:", exc)
PY
```

Expected: `nested … walk= 25 … {<repo>: 76, <repo>/plugins/sdd: 36}` and a
rendered `skills/<x>/SKILL.md`; `disjoint … walk= 0 … {<repo>: 76,
$TMPDIR/cg/far: 36}` and `rel(suite file) RAISED ValueError`. Every other
number below that derives from this machine's installed cache is labelled as
such at its point of use.

## Findings

### Q1 — The set of checks that reduce under a disjoint suite root

**Answer: all eight checks in `skill-lint.py` are affected; they fall into three
distinct failure classes, and `check_structure()` is only the loudest member.**
`gc.py` contributes no *additional* reducing check — it has no suite-root
binding of its own — but it is the **producer** of the disjoint geometry for
every consumer, and it holds two invocation-side defects of the same family.

The single mechanism behind every member: `swept_roots()` returns
`{corpus_root} ∪ {suite_root if contained}`, so under a disjoint suite root the
union collapses to the corpus root alone and the suite is **not walked at all**.

**Class A — reduces loudly, then stops (1 member).**

| Check | Observation that exposes it |
|---|---|
| `check_structure()` (`skill-lint.py:728`) | Observation geometry: emits exactly **1** finding (`. : [structure] skills/ directory not found`) and `return`s. Every per-skill frontmatter, `name`-vs-directory, description and ordinal rule below that return does not run. Nested geometry: 0 findings over 25 files. In the *consumer* geometry it does **not** return — it walks the consumer's own `skills/` and produced 2 findings there, so the loud reduction is specific to a corpus with no top-level `skills/`. |

**Class B — passes vacuously and says nothing (4 members).** These are driven by
`walk()`/`skill_files()`. With `walk() == 0` they each report `+0 findings` — a
clean run that checked nothing, with no line in the output distinguishing it
from a clean run that checked 25 files.

| Check | Observation that exposes it |
|---|---|
| `check_forbidden()` | `+0` findings in the observation geometry over **0** walked files vs `+0` over **25** in the nested one. The output is identical; the coverage is not. |
| `check_ordinals()` | Same: `+0` over 0 files. |
| `check_links()` | Same: `+0` over 0 files. In the *consumer* geometry it produced the one true finding it should (`unresolved path`), confirming the check works and only its input set is empty. |
| `check_size()` | Same: `+0` over 0 files. The SIZE_FAIL/SIZE_WARN thresholds are never applied to any `SKILL.md`. Note this is not a *binding* defect — `check_size()` is already union-bound and correctly so (Q4 lists it among the checks a fixture pins); what is empty is its input set, which no binding can supply once the union has collapsed. |

The summary line reinforces the reduction rather than exposing it: the
`OK: N file(s) clean` count is `len(self.skill_files())`, so a run that swept
nothing reports **`OK: 0 file(s) clean`** — the word `clean` over an empty set.

**Class C — runs, but measures the wrong tree (3 members).** These bind to
`self.suite_root` deliberately, so under a disjoint suite root they resolve
against the **installed plugin cache** and report on *it* while the operator
believes they report on the corpus. This is RS-PACKAGING-002 decision **D1**
live again.

| Check | Observation that exposes it |
|---|---|
| `check_required()` (`skill-lint.py:820`) | The **56 suite-gated rows** are `len(REQUIRED)=40` + `len(VERSION_GATED_SKILLS)=9` + `len(V4_CONTRACT_SKILLS)=7`. Measured: **0 of the 40 REQUIRED files are missing under the cache suite root** (machine-local evidence — this machine's cache holds a stale pre-move `0.1.0` install; the number evidences the geometry, it is not a property of it), so all 56 rows pass — against the cache's frozen `0.1.0` content, not against the working tree. Delete a REQUIRED anchor from `plugins/sdd/` and the installed linter still reports `required` clean. |
| `check_template_drift()` (`skill-lint.py:884`) | The `TEMPLATE_SOURCE` side reads `self.suite_root / TEMPLATE_SOURCE` → the cache's copy. The **spec side is explicitly `continue`d** when `not self.suite_contained()` (`skill-lint.py:919`). So under the observation geometry the source is read from the cache and the restating spec in the operator's own `docs/spec/` is never compared — the pair is not checked in either direction against the working tree. |
| `check_retired_prefix()` (`skill-lint.py:1145`) | `retired_scope_entries()` returns **112** entries in both geometries — but the split moves: nested = 76 corpus-bound + **36 bound to `<repo>/plugins/sdd`**; observation = 76 corpus-bound + **36 bound to `<cache>/sdd/0.1.0`**. The same 36-file scope is scanned in the *cache* instead of the working tree. A retired-prefix violation introduced into `plugins/sdd/skills/**` is invisible to the installed linter, and a stale cache can produce a phantom finding rendered against a cache-relative path. |

**The latent raise (kickoff deferred item 1), demonstrated.** `flag()`'s generic
`self.rel()` raises on any path under no swept root. Measured directly:

```
Linter(<repo>, <cache>).rel(<cache>/skills/research/SKILL.md)
  → ValueError: '…/cache/sdd-commons/sdd/0.1.0/skills/research/SKILL.md'
    is not in the subpath of '/Users/pankaj/work/github/jangid/sdd-commons'
```

The nested geometry returns `skills/research/SKILL.md` for the equivalent file
and never raises. The only thing standing between that `ValueError` and an
uncaught traceback out of `check_retired_prefix()` is the explicit
`rel=Path(rel)` argument at `skill-lint.py:1166` (the keyword; the `self.flag(...)` call it belongs to opens at `:1163`). **Reverting that one keyword
argument crashes the installed linter** for any of the 36 suite-bound scope
entries — and, per the kickoff, survives all four gates today. Same guard, same
reason, at `check_required()` (`rel=Path(rel)`, three sites) and
`check_template_drift()` (`rel=Path(TEMPLATE_SOURCE)`). These three call sites
are load-bearing and currently untested in the disjoint geometry.

**`gc.py` — two invocation-side members, no reducing check of its own.** A
`grep` for `suite_root` / `default_suite_root` over `plugins/sdd/tools/gc.py`
returns **zero** hits; every other sweep (`qimpl-undefined`, traceability, the
aggregate) is corpus-bound through `--root` and is geometry-independent. Its two
members are:

1. `lint_command()` (`gc.py:507`) passes **only** `str(self.root)`, so the
   linter's suite root always falls back to `default_suite_root()` — i.e. to
   wherever `gc.py` itself lives. When `gc.py` is the installed copy this
   *constructs* the disjoint geometry unconditionally. Every `gc.py --report`
   a consumer runs is therefore a Class A + Class B + Class C run.
2. `lint_path()` (`gc.py:500`) prefers the sibling `tools/skill-lint.py` (correct
   post-move) and falls back to `self.root / "tools" / "skill-lint.py"` — a
   path that no longer exists in this repository after the move to
   `plugins/sdd/tools/` and that a consumer repository will never hold. The
   fallback candidate is dead in every geometry; it can only ever match a
   coincidence in a foreign tree.

**Two further unpinned wirings (kickoff deferred items 2 and 3).** Neither
reduces under the disjoint geometry — they are *pinning* gaps of the class this
section already characterises, and they belong with Q4's list, not with Q1's
three classes. (i) `main()`'s `print_population(root, default_suite_root())`
(`skill-lint.py:3005`) is an unpinned two-root wiring: mis-rooting it to
`(root, root)` reports `FILES_SWEPT=0` at exit 0 on every gate — the same class
C9.2/C10.6 closed for the `Linter` half of the identical wiring, left open for
the `print_population` half. (ii) `retired_scope_entries()`'s `seen` set is a
**fourth** deduplication with no construction guard of its own, reachable by
monkeypatching `retired_scope_roots()` — the other three carry `C10.1`/`C10.2`
or the `walk()` guard. Both are routed to the plan stage as Q4 gap (e).

Two further consumer-unreachable strings, same family, not checks:
`AGG_FIX` (`gc.py:175`) tells the reader to `run tools/gc.py --fix
traceability-aggregate`, which resolves for nobody but an in-repo pre-move
operator; and six bare `python3 tools/telemetry.py` sites in `orchestrate`
(`USAGE.md:159,439,572`; `references/telemetry.md:484,577,602`) resolve
cwd-relative to `<corpus>/tools/telemetry.py`, which exists in no consumer repo.

### Q2 — Does `REQ-PKG-MARKETPLACE-007` bind this cycle?

**Answer: NO — in two different ways, and the distinction matters because most
of the spine is `skill-lint.py`.**

- **For `skill-lint.py`: the clause never covered it.** REQ-PKG-MARKETPLACE-007
  (`docs/requirements/integration/packaging.md:194-209`) names exactly two
  artefacts — the drift sweep and the telemetry tool, i.e. `gc.py` and
  `telemetry.py`. The linter is not in its scope, in the requirement body or in
  its acceptance, and the traceability row (`docs/requirements/traceability.md:318`)
  re-derives the freeze over those two files alone. Every Q1 Class A/B/C repair,
  and all three `rel=` guards, live in `skill-lint.py`. For them the answer is
  not "the freeze is step-scoped" but "there is no freeze to scope".
- **For `gc.py` and `telemetry.py`: the freeze is step-scoped and its step has
  closed.** These carry the two `gc.py` items in Q1 and the `AGG_FIX` string.

The evidence an amendment would cite, in order of force:

1. **The requirement's own scoping words**
   (`docs/requirements/integration/packaging.md:200`): *"Neither tool's source
   may be edited **to satisfy this requirement**"* — the freeze is on edits made
   *for packaging*, not on edits as such.
2. **The acceptance criterion is explicitly time-bounded**
   (`packaging.md:209`): *"`git diff` over the two tools' source files across
   the **packaging step** — measured from the close of the rename chunk
   (REQ-NAME-MARKETPLACE-007) to the end of the cycle — is empty."* A criterion
   with a start and an end sha cannot bind a later cycle.
3. **The clause has already been read as scoped, and an exception taken under
   it** (`docs/requirements/integration/naming.md:76`): the `prog=`/usage/hint
   string rename is recorded as *"the only source edit
   REQ-PKG-MARKETPLACE-007's no-source-edit clause permits, and it happens here,
   in the rename step, not in the packaging step."* Precedent that the clause is
   read step-wise.

**The one operative correction the amendment must make — the criterion is
un-re-runnable as written.** The `marketplace` cycle's verification
re-derived the criterion as `git diff 3ddfdb3 HEAD -- tools/gc.py`
(`docs/ws/marketplace/verification.md:558`, and the aggregate row at
`docs/requirements/traceability.md:318`). That comparand names a path that no
longer exists, so re-running it at today's HEAD measures the move, not this
cycle:

```
$ git diff 3ddfdb3 HEAD --stat -- tools/gc.py tools/telemetry.py
 tools/gc.py        | 1876 ----------------------------------------------
 tools/telemetry.py | 2106 ----------------------------------------------------
 2 files changed, 3982 deletions(-)
```

The deletions are the **packaging cycle's own** move of `tools/` to
`plugins/sdd/tools/`. This is **not** a regression against the `marketplace`
cycle and must not be recorded as one: evidence item 2 above establishes that the
criterion is bounded to the packaging step, and a criterion evaluated outside its
own window is not falsified by what it reports there. What is true is narrower
and sufficient — the comparand path `tools/gc.py` no longer exists, so the
criterion as written is **un-re-runnable**: it can neither confirm nor deny
anything at any sha after the move. The amendment must restate it
against the post-move path and **pin the end sha** (or restate the comparand as
the packaging cycle's own range) and name a successor requirement that permits
tool-source edits for consumer-geometry correctness. Suggested shape, for the
requirements stage to accept or reject: `REQ-PKG-CONSUMERGEOMETRY-001` —
*tool source may be edited when the edit is required for correctness under the
disjoint (consumer) geometry, and every such edit's reversion must fail a
gate.* That second half is kickoff constraint 2 made into a requirement, and Q4
shows it is satisfiable — but only if the comparand set is **enumerated**, since
"every such edit" is undecidable otherwise. **The set is fixed here:** Q4's gaps
(a)–(e), plus the three `rel=` guard sites of Q1 (`check_retired_prefix()`
`skill-lint.py:1166`; `check_required()`, three sites; `check_template_drift()`'s
`rel=Path(TEMPLATE_SOURCE)`). **Acceptance**: each named site has a
`--self-test` case whose stated mutation is *run* and observed red, and the
enumeration is itself checked — the count of named sites equals the count of
cases. A later cycle extends the set by amending the enumeration, never by
argument.

### Q3 — Where does the fix belong?

**Recommendation: a per-geometry split, not one fix.** Option **A** (an explicit
suite root) for the operator's own geometry — the observation geometry — because
it is the only mechanism examined that reaches the working tree there at all;
**today's union unchanged** for a foreign consumer; and **C-2**'s non-vacuity
rendering in every geometry. Option **B** — admitting a disjoint suite root into
the walk — is **rejected**. An earlier draft of this section recommended B; the
correction below is what the walk's actual mechanism forces.

**What the union actually walks — the fact that decides this.** `walk()`
(`skill-lint.py:585-601`) does `d = r / "skills"` **per swept root**: a per-root
join, not a recursive search for `skills/` directories. `<repo>/skills/` **does
not exist** — this repository's skills live at `plugins/sdd/skills/`. So in the
observation geometry the corpus root contributes **zero** files no matter what
the union does, and the only `skills/` tree any union can reach through the
suite root is `<cache>/skills/**` — the frozen `0.1.0` install, not the working
tree.

**Option B — tool-side, `swept_roots()` admits the disjoint suite root.
REJECTED.** Under B the four Class B checks in the observation geometry would
run over the **cache's** `skills/**/*.md` (measured on this machine:
`find <cache>/skills -name '*.md' | wc -l` = **25**, coincidentally the same
count as the working tree's). `OK: 0 file(s) clean` would become
`OK: 25 file(s) clean` — while a forbidden phrase introduced into
`plugins/sdd/skills/**` in the **working tree** stays invisible, because no
swept root reaches it. That is exactly the wrong-tree property this document
isolates as Class C and declines to close. B therefore does not discharge Class
B: it converts a **loud** reduction into a **silent wrong-tree pass**, which is
strictly worse than the defect it treats. The conditional-on-`suite_rules`
refinement an earlier draft proposed does not help — it changes *when* the cache
is walked, never *which tree* is walked.

**Option A — invocation-side (the invocation passes an explicit suite root).**
Passing `<repo>/plugins/sdd` as the suite root makes `suite_contained()` true
again, which restores the **nested** geometry: the walk reaches the working
tree's 25 files, and all three Class C checks re-root onto the working tree
rather than the cache. In the observation geometry it is the only one of the two
that reaches the working tree at all — the earlier draft's rejection ("cannot fix
the observation geometry as a class") was inverted and is withdrawn. Its real
costs are two: (i) the surface does not exist yet — `Linter`'s suite root is a
constructor parameter with no CLI flag, and `gc.py`'s `lint_command()` passes
only the corpus root, so the flag must be added before any invocation can use it.
This is precisely the `--suite-root` CLI surface **RS-PACKAGING-003 D1 deferred
to requirements**, live again and now load-bearing. (ii) an operator who types
the short form still gets the degraded run — which is why A is only safe when
**paired with C-2**, so the degraded run announces itself instead of printing
`OK`.

**And for a foreign consumer, A must not be used and B must not happen.** Their
corpus root holds their own `skills/`, which today's union already walks
correctly; an explicit suite root pointed at their tree names a plugin that is
not there, and a union reaching the cache reports findings in files they cannot
fix. Today's behaviour is right for them. The defect they are exposed to is
purely **signalling** — which root the 56 suite rows were evaluated against —
and that is C-2's job, not a binding's.

**Class B's repair, restated: non-vacuity, not coverage.** No binding change can
give the observation geometry's corpus root files it does not have. Coverage is
restored only by re-rooting the suite (A). What the tool owes in *every* geometry
is narrower and always achievable: a run that swept nothing must not be spelled
like a run that swept everything.

**Interaction with the 56 suite-gated rows (RS-PACKAGING-002 D1) — this is the
sharp edge.** Under **either** option the rows' *binding* is unchanged (still
`self.suite_root`); what differs is what that root points at. Under B (rejected)
it stays the cache, so the rows keep passing vacuously w.r.t. the working tree
(measured: 0/40 missing) — fixing the *walk* does **not** fix Class C. Under A it
becomes `<repo>/plugins/sdd`, and the rows measure the working tree with no
rebinding at all: **A discharges Class C for the operator's geometry as a side
effect of re-rooting**, which is a second reason to prefer it. What A cannot
reach is the foreign-consumer geometry, where the rows will always resolve
against the cache. That residue needs its own decision, and there are only two
coherent ones:

- **C-1 — rebind the 56 rows to the swept-root union** (as `check_structure()`
  and `check_size()` are). Superficially the consistent answer; **withdrawn as a
  recommendation**, because for 16 of the 56 rows it is a *reversal of a
  gate-pinned invariant*, not a repair. `check_required_gated_rows_bind_to_the_suite_root()`
  (`skill-lint.py:2452`, C12.1) builds a two-root fixture, seeds an
  identically-broken decoy under the **corpus** root, and asserts the decoy is
  **not** reported; its docstring records that a verify-stage red round found a
  real `[required]` violation going unreported under exactly a corpus-root
  rebinding. `docs/spec/two-root-linter.md:196-207` carries the same decision as
  spec. Under the nested geometry the union *contains* the corpus root, so C-1
  makes that decoy report and turns `--self-test` red. Anyone proposing C-1 must
  therefore propose overturning **both** that fixture and that spec clause, and
  must answer the red round's finding on its own terms. This spike does not.
  Scope note: C12.1 pins the **16** gated rows (`VERSION_GATED_SKILLS` 9 +
  `V4_CONTRACT_SKILLS` 7). The **40** `REQUIRED` table rows are not pinned by
  it, so a union rebinding *of those 40 alone* is arguable — but it is a
  separate proposal from C-1 as stated, and it still owes the specs stage an
  argument against §4's binding table.
- **C-2 — leave the rows suite-bound and make the vacuity visible.** Concretely,
  and falsifiably: every run gains one **own-line token** before its summary, and
  a zero-sweep run gains a suffix —

  ```
  GEOMETRY: disjoint  swept-roots=1  suite-rows-root=<suite root as given>
  OK: 0 file(s) clean — NOTHING SWEPT
  ```

  `GEOMETRY:` takes exactly three members, `nested | equal | disjoint`, from
  `suite_contained()` and root equality; the `— NOTHING SWEPT` suffix is present
  **iff** `len(self.skill_files()) == 0`, on both the `OK:` and `FAIL:` summary
  lines (`skill-lint.py:1189,1191`). This is a **new** token, *not* the existing
  `corpus: FILES_SWEPT=<n>` line (`skill-lint.py:2962`) promoted: that line is
  emitted only under `--print-population`, and RS-PACKAGING-003 D3 gave up live
  zero-sweep detection on the sound ground that a swept-file *count* from a live
  corpus cannot be asserted. The count stays informational; what becomes
  load-bearing is the **enum and the suffix**, neither of which is a count.
  Q4 gap (c)'s fixture is then writable: two scratch runs, a one-file corpus and
  an empty one, asserting `"— NOTHING SWEPT"` appears in the second and not the
  first, plus `GEOMETRY: disjoint` on the far-root fixture. Its mutation —
  dropping the suffix — makes the two runs' output identical and turns the
  fixture red.
  Cheaper, and — given C-1's collision with C12.1 — the only one of the two
  that does not require overturning a gate-pinned invariant. It documents the
  suite-bound answer rather than removing it, which is the honest trade while
  the binding itself stands. Class C is therefore **not closed** by this cycle's
  recommendation; it is made visible, and the 40-row question is handed to the
  specs stage as a separate, argued proposal.

**Recommendation, combined:** A + **C-2**, plus the three `rel=` guards from Q1
promoted from incidental keyword arguments to gated invariants, plus the
`AGG_FIX` / bare-`tools/` string corrections as documentation-only edits. The
`warn`-severity boundary (kickoff out-of-scope item, deferred item 4) is **not**
reached by this recommendation: every binding above is `fail`-severity, so the
spine closes without an exit-contract change. That boundary can stay closed.

### Q4 — Can a gate in this repository observe a disjoint-geometry regression?

**Answer: YES — and the technique already exists, is already in the file, and is
already run by a gate.** This is the most consequential finding here, because
the kickoff flagged a `no` as the answer that would make constraint 2
unsatisfiable.

The evidence:

1. **The technique.** `skill-lint.py`'s `--self-test` already constructs
   disjoint geometries in scratch directories and asserts against them:
   `tr_far = tr / "elsewhere"` with `disjoint = Linter(tr_corpus, tr_far,
   suite_rules=False)` (`skill-lint.py:1684,1705`); fixture B, the explicitly
   named *consumer shape*, at `skill-lint.py:1963` with
   `disjoint_suite_walk_excluded()` at `:1996`; the retarget fixture at
   `:1804` (`rs_suite = rs / "suite"  # disjoint: NOT under rs_corpus`); the
   `TEMPLATE_PAIRS` disjoint fixture at `:2103–2177`; and
   `check_structure_binds_to_the_swept_roots()` at `:2320`, whose own docstring
   enumerates the mutations that must break it and which asserts the disjoint
   half **does not raise out of `rel()`**.
2. **A gate runs it.** `.pre-commit-config.yaml:53` (`skill-lint-self-test`,
   `python3 plugins/sdd/tools/skill-lint.py --self-test`) and `:59`
   (`drift-sweep-self-test`). These are in the committed hook set, not among the
   three heavier checks run explicitly.
3. **No cache write is required.** Every fixture above is a scratch tree. The
   read-only constraint on `~/.claude/plugins/cache/` is fully compatible with
   gating the geometry.

So constraint 2 ("every binding this cycle touches must have its reversion fail
a gate, demonstrated by running the mutation") **is satisfiable for the entire
spine**, via `--self-test` fixtures in the existing style.

**The precise gap, stated so the plan can target it.** The gate observes the
geometry for the checks that *already* carry a disjoint fixture
(`swept_roots()`, `walk()`, `check_structure()`, `check_size()`,
`skill_dir_of()`, `TEMPLATE_PAIRS`). It does **not** observe:
(a) `check_retired_prefix()` under a disjoint suite root — which is exactly why
deferred item 1's `rel=Path(rel)` reversion (`skill-lint.py:1166`) survives all
four gates;
(b) `check_required()` under a **disjoint** suite root — the 16 gated rows are
pinned, but only in the **nested** two-root fixture C12.1 builds
(`skill-lint.py:2452`); no fixture asserts what any of the 56 rows resolve
against when the suite root is outside the corpus, and the 40 `REQUIRED` table
rows carry no binding fixture in any geometry;
(c) Class B's vacuity — no fixture asserts that a run which swept zero files is
distinguishable from a clean run;
(d) `gc.py`'s `lint_command()` root pinning and `lint_path()`'s second
candidate;
(e) the two unpinned wirings from Q1 — `main()`'s `print_population(root,
default_suite_root())` and `retired_scope_entries()`'s `seen` set (kickoff
deferred items 2 and 3).
Each of (a)–(e) is a fixture of the kind already present, not a new mechanism.

### Q5 — Is `plugins/sdd/skills/orchestrate/tools/` reachable?

**Answer: NO invocation reaches it that works. Recommendation: REMOVE it — but
only *after* `REQ-PKG-MARKETPLACE-006` is amended or superseded, never before
(see the closing paragraph of this section; removal falsifies three records).**

Measured. The directory holds exactly two files, `gc.py` and `telemetry.py`,
each byte-identical to its `plugins/sdd/tools/` counterpart (`diff -q` silent
for both). Reachability, by invocation class:

- **Skill-directory-relative invocations** — the 8 invocations the `marketplace`
  cycle counted as reaching the bundled copy. Running the bundled `gc.py`
  directly, against a scratch corpus, reproduces RS-PACKAGING-001's measurement:

  ```
  python3 plugins/sdd/skills/orchestrate/tools/gc.py --report --root $TMPDIR/foreign
  error: linter missing — expected /private/tmp/…/foreign/tools/skill-lint.py
  ```

  `lint_path()`'s sibling-first candidate looks for `skill-lint.py` *next to
  gc.py* — and `skills/orchestrate/tools/` does not contain one, because the
  linter is no longer bundled at all after the 2026-09-21 reversal. So the
  bundled copy is reachable but **non-functional**: it exits on the linter-missing
  path in every geometry.
- **Bare `tools/…` invocations** — the six `python3 tools/telemetry.py` sites
  resolve cwd-relative, i.e. to `<corpus>/tools/`, never to the skill directory.
- **No other reference.** Measured —
  `grep -rn "orchestrate/tools" . --include="*.md" --include="*.py" --include="*.json"
  --include="*.yaml" --exclude-dir=docs` returns **1** line: the string appears
  outside `docs/` only at
  `plugins/sdd/skills/orchestrate/references/drift-sweep.md:36`, and
  there it cites the directory's *existence* under REQ-PKG-MARKETPLACE-006, not
  an invocation.

**What removing it falsifies — six records, named:**

1. `docs/ws/marketplace/verification.md:557`, the **added criterion** under
   REQ-PKG-MARKETPLACE-006 — *"at least one invocation resolves to the bundled
   copy … Substituting `<skill-dir>` = `skills/orchestrate` yields
   `skills/orchestrate/tools/gc.py`, which exists on disk as a regular file."*
   Removal falsifies the "exists on disk" half outright. Note the criterion only
   ever asserted **existence**, never that the invocation *works* — and the
   measurement above shows it does not. That criterion was already weaker than
   it reads, which is itself a correction the cycle should record.
2. `docs/ws/marketplace/verification.md`'s REQ-PKG-MARKETPLACE-006 row — the
   `cmp` exit 0 / `test ! -L` duplication evidence over "two pairs after the
   reversal" becomes a statement about zero pairs.
3. `docs/requirements/traceability.md:317`, whose REQ-PKG-MARKETPLACE-006
   Evidence column names `skills/orchestrate/tools/gc.py` and
   `skills/orchestrate/tools/telemetry.py` as the artefacts. Plus three spec
   citations that describe the duplication as a requirement:
   `docs/spec/two-root-linter.md:360`, `docs/spec/pre-commit.md:274`, and the
   restoration instruction at `docs/spec/marketplace-packaging.md:565`.
4. `plugins/sdd/skills/orchestrate/references/drift-sweep.md:36` — the same file
   the reachability bullet above cites. It is a **plugin** file, not a doc
   record: removal therefore edits the **shipped surface**, which puts it in a
   different write scope from items 1–3 and means the plan stage cannot treat
   this as a docs-only change.
5. `docs/ws/packaging/verification.md:434` — "The bundled copy at
   `plugins/sdd/skills/orchestrate/tools/` is now referenced …".
6. `docs/ws/packaging/baseline.md:63-64` — both paths named in the baseline
   inventory.

So removal touches **six** numbered records spanning **five** surfaces — one
shipped plugin file, two `packaging` workstream records, one `marketplace`
workstream record (items 1 and 2 are both `verification.md`), the shared
traceability table and three spec citations. Counting each cited file once,
that is eight distinct files. It is a wider edit than the
reachability finding alone implies.

Removal is therefore **not** a tidy-up: it requires amending
REQ-PKG-MARKETPLACE-006 (or superseding it), which is requirements-stage work
and belongs with Q2's amendment, not before it.

## Supersession — what this spike overturns in RS-PACKAGING-003

The frontmatter's `supersedes:` is **narrow**, and the distinction matters
because D1 is the live comparand for Q3's C-1/C-2 split. Following
RS-PACKAGING-003's own convention (its index row declares RS-PACKAGING-002 an
**input**, not a superseded predecessor), the dispositions are:

- **D1 (high) — the 56 suite rows retarget to the suite root.** **STANDS, and is
  an input.** C-2 explicitly *leaves it standing*; C-1, which would overturn it,
  is withdrawn at Q3. One deferred half of D1 is reactivated rather than
  overturned: the `--suite-root` CLI surface it deferred to requirements is what
  Q3's Option A now depends on.
- **D2 (medium) — per-entry bindings**, including `TEMPLATE_PAIRS`' spec side
  skipped under disjoint roots. **STANDS, and is an input** — Q1 measured it
  behaving exactly as D2 specifies, and reports its *consequence* (the pair
  unchecked in both directions), not a defect in the binding.
- **D3 (medium) — live zero-sweep detection given up; `FILES_SWEPT=<n>` left
  informational.** **PARTIALLY SUPERSEDED — this is the only supersession.** D3's
  reasoning holds for a *count*, and C-2 preserves it: the count stays
  informational. What D3 concluded too widely is that live zero-sweep detection
  is unavailable at all. Q1's Class B shows the cost of that gap (a 0-file gate
  spelled `OK: … clean`), and C-2 supplies a detector that is not a count — an
  enum plus a presence-iff suffix — so no comparand is asserted against the
  sweep itself.
- **D4 (low) — the three geometries A/B/C.** **STANDS, and is an input.** Its
  geometry B ("walk-class violation specifically absent") is corroborated here
  by the mechanism in Q3: the disjoint corpus root contributes zero files, so
  there is no walk-class violation to observe.

## Recommendations

1. **Requirements stage** — amend `REQ-PKG-MARKETPLACE-007` per Q2 (pin the
   freeze's end sha; state the step scoping) and add the successor requirement
   permitting consumer-geometry correctness edits to tool source. Amend or
   supersede `REQ-PKG-MARKETPLACE-006` per Q5 before any removal.
2. **Specs stage** — ratify Q3's per-geometry split: **Option A + C-2** for the
   operator's own geometry, **today's union unchanged** for a foreign consumer.
   Option B is rejected at Q3 and C-1 is withdrawn there (it collides with the
   C12.1 gate pin) — ratify neither. Specify the `--suite-root` surface
   (RS-PACKAGING-003 D1's deferred half) and C-2's two output tokens verbatim,
   and state what a foreign consumer's `gc.py --report` must and must not report.
3. **Plan stage** — one chunk per Q4 gap (a)–(e), each a `--self-test` fixture in
   the existing scratch-root style, each with its mutation *run* per constraint 2.
   Item (a) is highest value: it is deferred item 1 and it is a live crash.
4. **Ordering** — the Q4 fixtures land **before** the Q3 changes, so each
   change's reversion is observable at the moment it is made. Within Q5, the
   requirements amendment lands before the removal, never after.
5. Treat the Class B vacuity (`OK: 0 file(s) clean`) as a first-class defect, not
   cosmetics: it is what turned a 25-file gate into a 0-file gate without a word
   of output. Note what C-2 does and does not buy — it makes that run *announce*
   itself; it does **not** restore the 25. Only Option A's re-rooting does, and
   nothing at all restores them for a foreign consumer, who never had them.

## Open Questions

None of Q1–Q5 is left OPEN. Three items are deliberately deferred **to a named
later stage** rather than answered here:

- **The shape of the `--suite-root` surface (Q3).** With Option B rejected, the
  `suite_rules` widening it needed is moot and is withdrawn. What replaces it is
  RS-PACKAGING-003 D1's deferred question, now load-bearing: whether the explicit
  suite root arrives as a CLI flag on both tools, as a `gc.py` pass-through, or
  as a documented second positional — and what an invocation that omits it must
  print. Specs-stage work; this spike fixes the requirement (A must be
  expressible) and not the surface.
- **The 40-row-only proposal (Q3).** C-1 is withdrawn; what Q3 hands forward is
  the narrower question of rebinding the **40** `REQUIRED` table rows alone —
  the 16 gated rows are pinned to the suite root by C12.1 and are not in play.
  That proposal is specs-stage work and still owes an argument against §4's
  binding table. Measured here: 0 of 40 REQUIRED files are missing under either
  root, so no row would change verdict *today* — but the specs stage must
  re-derive that, not cite it.
- **Whether `AGG_FIX` and the six bare `tools/` strings are in this cycle's
  write scope (Q2-dependent).** They are pure documentation edits to tool source
  and skill bodies; if the Q2 amendment lands as recommended they are trivially
  in scope, and if it does not, they are blocked on it.

The kickoff's out-of-scope boundary on deferred item 4 (the `warn` severity
class / exit-contract change) **holds**: Q3's recommendation reaches the spine
entirely through `fail`-severity bindings, so no `--strict` flag or warn-count
comparand is needed. Stated explicitly, per the kickoff's instruction not to
widen silently.

## Budget consumed

25 tool calls / 0 test runs dispatched; **18 drawn** in the first pass, **7**
in repair iteration 1 (`FIX_LOOP_MAX` 3) against that iteration's own 15-call
allowance. No test run was used in either pass.
