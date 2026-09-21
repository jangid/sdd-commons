---
id: RS-PACKAGING-001
workstream: packaging
status: Complete
date: 2026-09-21
last_updated: 2026-09-21
questions:
  - "Does any mechanism exclude paths from a materialised plugin install?"
  - "Can tools/gc.py's suite-specific contract rows be expressed as data carried by the swept corpus rather than hardcoded in the tool?"
  - "What is the cheapest fixture that materialises an install non-circularly?"
budget: "dispatch 1 (original spike, Q1-Q3): 30 tool calls; dispatch 2 (repair): 18 tool calls; dispatch 3 (repair): 16 tool calls; dispatch 4 (repair): 20 tool calls; 0 test runs in all four"
research_refs:
  - "RS-MARKETPLACE-001 — docs/research/RS-MARKETPLACE-001-marketplace-release/findings.md"
  - "docs/ws/marketplace/verification.md (§Next Steps — the two questions deferred at that cycle's close, which this spike answers)"
  - "docs/ws/packaging/kickoff.md (§Decided at DISCUSS — the authorizations this spike inherits)"
---

# Research: Packaging follow-up — install exclusion, corpus-carried rule data, and a non-circular install fixture

## Questions

1. **Q1** — Does any mechanism exclude paths from a materialised plugin install?
   If not, cost the move of the plugin root to a `plugins/sdd/` subdirectory.
2. **Q2** — Can the drift sweep's suite-specific contract rows be expressed as
   data carried by the swept corpus rather than hardcoded in the tool?
3. **Q3** — What is the cheapest fixture that materialises an install
   non-circularly?

All three are answered from commands run against the live install, the
repository at pinned shas, and a synthetic foreign consumer tree. No answer
below rests on reading a manifest or a document alone.

**What "the previous cycle" means throughout this document.** Every reference
below to *the previous cycle*, *the recorded 11/40 vectors*, *the derivation
constraint recorded last cycle*, *the provenance predicate*, *a carried repair*
or *the previous cycle's criterion* means the **marketplace** cycle,
`RS-MARKETPLACE-001`, whose research deliverable is
`docs/research/RS-MARKETPLACE-001-marketplace-release/findings.md` and whose
verification report is `docs/ws/marketplace/verification.md` — the 11/40 vector
baseline and the derivation constraint are in the former, and the two questions
this spike picks up are deferred in the latter's `## Next Steps`. The
authorizations this spike works under are in `docs/ws/packaging/kickoff.md`
§Decided at DISCUSS.

## Findings

### Q1 — Does any mechanism exclude paths from a materialised install?

**Answer**: **Split.** There is **no path-exclusion declaration** — no ignore
file, no manifest `files:` / `exclude:` filter, and the component list does not
affect what is copied for a `github` source. But there **is** a mechanism that
produces a `docs/`-free install: a marketplace entry whose `source` is
**`git-subdir`**, which sparse-checkouts one subdirectory and installs *only*
that subdirectory. It is not an exclusion filter; it is a subdirectory-scoped
source, so it still requires the plugin root to move. The `plugins/sdd/` root
move authorized at DISCUSS is therefore **required**, and `git-subdir` is what
makes it pay off. The one other source that receives a component-path argument,
`archive`, is **dismissed below with its reason** — it is not a zero-move
alternative.

The **symmetric** alternative — keep `"source": "./"` and relocate the 146
`docs/` files *out of* the plugin repository, which satisfies "no filter
exists" from the other side — is **not costed here because it was already
rejected upstream**: `docs/ws/packaging/kickoff.md` §Decided at DISCUSS item 1
considered splitting `docs/` into a separate repository and rejected it, on the
ground that it breaks the single shared corpus that every `sdd:*` skill's phase
detection, staleness chain and traceability assume. That decision is cited, not
re-derived.

**Evidence (negative half — no exclusion declaration):**

The live install's file list is byte-for-byte the repository's tracked tree at
the pinned sha, with exactly one runtime addition:

```bash
git -C <repo> ls-tree -r --name-only 29febe6 | sort > $TMPDIR/git.txt
(cd ~/.claude/plugins/cache/sdd-commons/sdd/0.1.0 && find . -type f | sed 's|^\./||' | sort) > $TMPDIR/install.txt
comm -23 $TMPDIR/git.txt $TMPDIR/install.txt   # -> empty (nothing tracked was dropped)
comm -13 $TMPDIR/git.txt $TMPDIR/install.txt   # -> .in_use/1853 (a runtime lock marker)
```

198 tracked files in, 199 files installed, 145 of them under `docs/`. Nothing
was filtered. The same list is reproduced offline by `git archive` (see Q3),
which confirms the materialisation is a plain checkout of tracked paths.

No ignore file exists or is looked for. Every installer claim below is read
from one artifact — the Claude Code binary at
`/Users/pankaj/.local/share/claude/versions/2.1.278` — extracted once and
grepped; `$S` names that extraction throughout:

```bash
S=$TMPDIR/cli-strings.txt
strings -a /Users/pankaj/.local/share/claude/versions/2.1.278 > $S
wc -l < $S                          # 635094
grep -o claudeignore $S | wc -l     # 0   (occurrences, not matching lines)
grep -o pluginignore $S | wc -l     # 0
```

The component list's non-effect is **confirmed, not inherited**: in the
installer's source dispatch, the `github` branch is called with the repo, ref
and sha only, while a component-path argument (`declaredComponentPaths`) is
threaded to the **`archive`** branch alone:

```bash
python3 -c 'import re,sys; s=open(sys.argv[1],errors="replace").read(); \
  i=s.find("case\"git-subdir\":B=await"); print(s[i-120:i+260])' $S
```

```
case "github":     await M(), B = await Aqo(e.repo, y, e.ref, e.sha); break;
case "url":        await M(), B = await BPn(e.url, y, e.ref, e.sha); break;
case "git-subdir": B = await Mqo(e.url, y, e.path, e.ref, e.sha, w); break;
case "archive":    U = await Nqo(e, y, w, n?.archiveAuth,
                                 n?.entryDeclaresComponents ?? false,
                                 n?.declaredComponentPaths === undefined ? []
                                                                        : n.declaredComponentPaths); break;
```

(Minified in the binary; whitespace added here, tokens verbatim.)

So for the source this repository actually uses, the component list governs what
is *loaded*, never what is *copied* — the previous cycle's finding, now
re-derived from the installer rather than assumed.

`.gitignore` semantics hold only in the trivial sense that untracked files are
never in the tree to begin with; they cannot exclude a tracked path.

**The `archive` option, costed and dismissed.** The snippet above invites the
question: does an `archive`-sourced entry with declared components yield a
`docs/`-free install with **zero** files moved? **No** — for two reasons, both
read from the same `$S`:

1. `archive` is not a repository source. Its schema is *"HTTPS URL of a zip
   archive containing the plugin. The plugin root (the directory holding
   `.claude-plugin/`) …"*, fetched by URL with an optional `sha256` pin
   read with:

   ```bash
   grep -oE 'HTTPS URL of a zip archive containing the plugin.{0,120}' $S | head -1
   ```

   ```
   HTTPS URL of a zip archive containing the plugin. The plugin root (the directory holding .claude-plugin/) may be at the top of the archive
   ```

   It cannot install from
   `jangid/sdd-commons` at a ref at all. Choosing it means building and hosting
   a release zip per version, pinning its digest, and giving up the
   install-from-the-repo shape the marketplace uses today — a release pipeline,
   not a zero-cost swap.
2. The component-path argument is **not** a copy filter — **read, not
   measured** (the minified `Nqo` body was located with the same `re.search`
   recipe used for `Mqo` below and read by eye; no command output is shown for
   it, and the dismissal does not rest on it). In `Nqo`'s body the
   argument `h` is used once, as a safety check — `if (h === null) throw …
   "its marketplace entry declares only unsafe or malformed component paths"` —
   after which the archive is extracted whole (`$F(w, O)`), with a
   wrapper-directory unwrap and an empty-archive refusal. What the archive
   contains is decided when the zip is **built**, not by the component list.

So the exclusion would come from the zip's build step, not from a declaration,
and the cost is a hosted artifact rather than a directory move. `git-subdir`
keeps the install sourced from the repository at a sha. **Dismissed.**

**Evidence (positive half — `git-subdir`):** the schema strings were surfaced
from the same `$S` by these greps —

```bash
grep -oE 'Subdirectory within the repo[^"]{0,150}' $S | head -1
grep -oE 'sparse-checkout","set","--cone' $S | head -1
grep -oE '\-\-filter=tree:0|\-\-no-checkout' $S | head -2
```

— giving the declared source schema

```
source: "git-subdir", url: <owner/repo | https:// | git@>, path: <subdirectory>, ref?, sha?
```

with `path` described as *"Subdirectory within the repo containing the plugin
… Cloned sparsely using partial clone (--filter=tree:0) to minimize bandwidth
for monorepos"*. That `path` carries `min(1)` — i.e. is required — was **read**
from the schema literal beside that string, not measured.

The clone/sparse/checkout/move sequence is not read from prose: the `Mqo` body
is printed whole and quoted from its output —

```bash
python3 -c 'import re,sys; s=open(sys.argv[1],errors="replace").read(); \
  m=re.search(r"(async )?function Mqo\(", s); print(s[m.start():m.start()+3200])' $S
```

```
async function Mqo(e,n,r,s,g,h=n){ … let w=`${h}${HQn}` …
  U=[...qSe,...M,"clone","--depth","1","--filter=tree:0","--no-checkout"]; … U.push("--",y,w);
  … pR(w,[...O,"sparse-checkout","set","--cone","--",r],_e) …
  … pR(w,[...O,"checkout",g],_e) …
  let xe=eet(w,r); await Cqo(w,xe,r);
  try{ if(Gu(n)!==mm())await le().mkdir(Gu(n)); await $o(xe,n) }
  catch(Le){ if(j(Le))throw Error(`Subdirectory '${r}' not found in repository …`) … }
  … finally{ await qz(w,{recursive:!0,force:!0}) } }
```

(Minified in the binary; the excerpt above is elided at the `…` marks and
re-wrapped, tokens verbatim.) So the installer clones
`--depth 1 --filter=tree:0 --no-checkout` into a scratch directory `w`, runs
`sparse-checkout set --cone -- <path>`, checks out the ref or sha, then **moves
only `<scratch>/<path>` — `$o(xe, n)`, where `xe = eet(w, <path>)` — to the
install directory `n`** and deletes the scratch clone in a `finally`.
Repository-root files therefore do **not** leak into the install; the installed
tree is exactly the subdirectory.

**Correction to an earlier revision of this document.** A previous repair
asserted that "a path traversal guard and a 'passes through a symbolic link'
refusal sit in between", citing
`grep -oE '.{0,60}outside the repository.{0,40}' $S | head -3` with no output
shown. The command runs, but its output is about **git worktree creation**, not
about `git-subdir`:

```
r .claude/worktrees/<name> could redirect worktree creation outside the repository. Remove the symlink and retry.
symlink below the checkout root could redirect the worktree outside the repository. Remove the symlink (or emit a path out
could redirect the worktree outside the repository
```

That claim is **withdrawn**. What the `Mqo` body above does show is a call
`Cqo(w, xe, r)` on the resolved subdirectory immediately before the move; its
body was not read, so whether it guards traversal or symlinks is **not
established here** and is recorded under Open Questions. No conclusion in Q1
depends on it.

Materialisation was reproduced offline against this repository (sparse cone
checkout of an existing subdirectory at the unmerged `packaging` HEAD):

```bash
git clone --quiet --no-checkout "file:///…/sdd-commons" $TMPDIR/B
git -C $TMPDIR/B sparse-checkout set --cone -- skills
git -C $TMPDIR/B checkout --quiet 0f5ec2675fcc0c4a993922fd6ba1702ddec426d9
find $TMPDIR/B -path ./.git -prune -o -type f -print | wc -l   # 33
```

33 files, **0 under `docs/`**, versus 198. The 33 are 27 `skills/` files plus
the 6 top-level regular files that cone mode always retains — and those 6 are
precisely what the installer's final subdirectory move then discards.

**Costing — the `plugins/sdd/` root move** (needed because `path` must name a
directory that *contains* the plugin root):

All three rows below are counted at **one** sha — `0f5ec26`, the `packaging`
HEAD, where `git ls-files | wc -l` is **199**. (The install evidence above is at
`29febe6`, which has **198** tracked files, 145 of them under `docs/`; the
install's 199th file is the `.in_use/` runtime marker. The two 199s are
different numbers and are not compared.)

| Item | Count | Disposition |
|------|-------|-------------|
| Files that move under `plugins/sdd/` | **45** | `.claude-plugin/plugin.json` (1), `skills/` (27), `agents/` (3), `tools/` (14) |
| Files that stay in the repository (outside `plugins/sdd/`) | **154** | `docs/` (146), `.claude-plugin/marketplace.json`, `README.md`, `LICENSE`, `CLAUDE.md`, `CONTRIBUTING.md`, `.gitignore`, `.pre-commit-config.yaml`, `.claude/settings.json` |
| Total | **199** | 45 + 154 = `git ls-files` at `0f5ec26` |
| Resulting install size | **~45 files** | `docs/` (146 files, 3.5 MB at `0f5ec26`) gone by construction |

Both figures in the last row are read at `0f5ec26`, the table's single sha
(`git ls-tree -r --name-only 0f5ec26 -- docs/ | wc -l` → `146`; `du -sh` over the
`git archive 0f5ec26 docs/` materialisation used for the token count below →
`3.5M`). An earlier revision took `146` from `0f5ec26` and `3.5 MB` from the
145-file `29febe6` install, mixing shas in a table that is otherwise pinned to
one.

What breaks, itemised against the four named risks:

- **The driver's ten skill-directory-relative `references/*.md`** — do **not**
  break. All ten (`dispatch-templates`, `drift-sweep`, `fan-out`, `isolation`,
  `loop-control`, `phase-detection`, `return-contract`, `telemetry`,
  `v4-workstreams`, `write-scope`) live inside `skills/orchestrate/` and move
  with it; every reference to them is relative to the skill directory, so the
  relative distance is unchanged. **Zero edits.**
- **The marketplace `source` field** — breaks, and is the point of the exercise.
  `.claude-plugin/marketplace.json` must **stay at the repository root** (it is
  the marketplace's own manifest); only `plugin.json` moves. The entry changes
  from `"source": "./"` to
  `"source": {"source": "git-subdir", "url": "jangid/sdd-commons", "path": "plugins/sdd"}`,
  and the ten `./skills/...` / three `./agents/...` component paths must be
  re-rooted to the new plugin root. **1 file, 14 lines.**
- **The bundled tools' own paths** — 54 `tools/<name>.py` path-shaped tokens
  inside `skills/` and `agents/`. The executable ones are already
  skill-directory-relative and travel intact; the prose ones name
  `tools/gc.py` etc. relative to the repository root and would need the
  `plugins/sdd/` prefix *or* an explicit statement that they are plugin-root
  relative. A further **2 486** path-shaped `(skills|agents|tools)/…` tokens
  exist in `docs/` and **22** in the **three** root Markdown files; these are
  prose about the repository, and re-rooting them is the bulk of the move's
  cost. Both numbers are counted with the same token shape, and both commands
  are shown with their output:

  ```bash
  grep -ohE '\b(skills|agents|tools)/[A-Za-z0-9_./-]+' CLAUDE.md CONTRIBUTING.md README.md | wc -l
  #   22
  ```

  The `docs/` count is **pinned to a sha and materialised out of the working
  tree**, because counting it in place is self-referential: this deliverable
  lives under `docs/` and contributes tokens of its own, so an in-place count
  changes every time the document is edited. `0f5ec26` is the sha the whole
  costing table is pinned to, and this deliverable is **not** in that tree (it
  was untracked when `0f5ec26` was written), so the population excludes it by
  construction rather than by a filter:

  ```bash
  rm -rf $TMPDIR/D && mkdir -p $TMPDIR/D && git archive 0f5ec26 docs/ | tar -x -C $TMPDIR/D
  cd $TMPDIR/D && grep -rohE '\b(skills|agents|tools)/[A-Za-z0-9_./-]+' docs/ | wc -l
  #  2486
  ls docs/research/ | grep -c PACKAGING
  #     0        (the deliverable is absent from the pinned population)
  ```

  An earlier revision recorded **2 523** from an in-place `grep -r docs/`; that
  number was measured over a population that included the document reporting it,
  and it does not reproduce. The magnitude conclusion is unchanged.

  The population is corrected here: this repository has **three** root Markdown
  files, not four — `git ls-files | grep -v /` returns `.gitignore`,
  `.pre-commit-config.yaml`, `CLAUDE.md`, `CONTRIBUTING.md`, `LICENSE`,
  `README.md`. `LICENSE` carries no extension, and `README.org` does not exist:
  it is only a retired **name** in `RETIRED_SCOPE_FILES`. An earlier revision's
  "**30** in the four root Markdown files" counted over a population that
  includes a file that is not there, and does not reproduce.
- **The linter's path-keyed rows** — break, uniformly and mechanically. The 40
  `REQUIRED` rows key on 10 distinct files (`skills/orchestrate/SKILL.md` ×10,
  `.../references/dispatch-templates.md` ×8, `skills/implement/SKILL.md` ×5,
  `.../fan-out.md` ×4, `.../loop-control.md` ×4, `skills/review/SKILL.md` ×3,
  `skills/plan/SKILL.md` ×2, `skills/replan/SKILL.md` ×2,
  `skills/research/SKILL.md` ×1, `.../write-scope.md` ×1), plus 2 file-scoped
  `FORBIDDEN` rows, `TEMPLATE_SOURCE`, and `RETIRED_SCOPE_DIRS`
  (`skills`, `tools`, `agents`, `.claude-plugin`, …). **The fix is not to
  re-root 40 strings, but it is not one root either — the linter needs TWO.**
  The 40 `REQUIRED` rows key on 10 files all under `skills/`, so a plugin-root
  run keeps every one of them as written. The rest key on files this table says
  **stay**:
  - `RETIRED_SCOPE_FILES` = `CLAUDE.md`, `README.md`, `README.org`,
    `CONTRIBUTING.md`, `LICENSE`, `.pre-commit-config.yaml` — all six stay at
    the repository root.
  - `RETIRED_SCOPE_DIRS` = `skills`, `tools`, `agents`, `.claude-plugin`,
    `docs/spec`, `docs/requirements` — the last two are under `docs/`, which
    stays.
  - `TEMPLATE_PAIRS` compares a `skills/…` anchor against a `docs/spec/*.md`
    spec side: one comparand moves, the other stays.

  Rooted at `plugins/sdd/` those rows resolve to nonexistent paths and police
  **nothing, silently** — the vacuous-pass shape the recorded derivation
  constraint exists to prevent (and which `tools/skill-lint.py`'s own fixture
  pins the policed population against, precisely so a shrinking scope fails
  rather than passes). So the move needs a **plugin root** for the suite files
  and a **repository root** for the root-corpus retired-prefix scope and the
  spec side of the template pairs — two roots, one of which is not the swept
  suite's. That is a contract change, not a flag flip, and Q2's data file
  inherits it.

Two further breakages that the four named risks above do **not** reach, itemised
here because neither token count can see them:

- **`.pre-commit-config.yaml`** stays at the repository root (it is the repo's
  commit gate, not the plugin's), but it carries **three** repository-root-relative
  references to files that move. It is neither Markdown nor under `docs/`, so
  neither token count covers it:

  ```bash
  grep -nE 'entry:|tools/fixtures' .pre-commit-config.yaml
  ```

  ```
  14:      tools/fixtures/      # frozen fixtures whose bytes are part of what they test …
  29:        entry: python3 tools/gc.py --fast
  35:        entry: python3 tools/skill-lint.py
  ```

  After the move those become `plugins/sdd/tools/…` (the two `entry:` lines) and
  `plugins/sdd/tools/fixtures/` (the `exclude:` regex member). **1 file, 3
  lines.**

- **`tools/skill-lint.py`'s own self-test `policed_files` tuple** — the same class
  of item, named elsewhere in this document only in passing as a *guard* rather
  than as a path-keyed thing the two-root change must carry:

  ```bash
  grep -n policed_files tools/skill-lint.py | head -4
  ```

  ```
  1252:        policed_files = ("CLAUDE.md", "README.md", "README.org", "CONTRIBUTING.md",
  1257:        check(tuple(RETIRED_SCOPE_FILES) == policed_files,
  1259:              f"{tuple(RETIRED_SCOPE_FILES)} != {policed_files}")
  1264:        seeded = [f"{d}/seeded.md" for d in policed_dirs] + list(policed_files)
  ```

  It pins `RETIRED_SCOPE_FILES` against a frozen literal and seeds a fixture tree
  from it. All six of those files **stay at the repository root**, so under the
  two-root contract the tuple keeps its spelling but acquires a root selector —
  and the self-test must seed against the **repository** root while the suite rows
  seed against the plugin root. A one-root design makes this self-test seed into
  the wrong tree and pass vacuously, which is exactly the failure it was written
  to prevent. **1 file, the tuple plus its two seeding sites.**

**Confidence**: High for the negative half (a byte-level tree comparison plus a
zero-hit string scan of the binary that performs the install). High for the
`git-subdir` mechanism's shape (schema text, the installer's clone/sparse/move
sequence, and a reproduced sparse checkout). Medium for the claim that a
`git-subdir` entry in *this* marketplace resolves exactly as modelled — that is
read from the installer's code path and a simulated checkout, not from an
executed `plugin install`, which was out of bounds for this spike. **Every
installer fact above is an internal of one specific CLI release** — the binary
at `/Users/pankaj/.local/share/claude/versions/2.1.278` — and internals are not
a published contract: function names, the dispatch shape and even the set of
supported `source` kinds may change on upgrade, and the whole `git-subdir`
selection rests on them; the schema strings (`source`, `path`, the `archive`
zip-URL description) are the most durable part, the minified identifiers the
least, and a re-derivation against the then-current release is cheap enough to
be worth repeating before the move is executed. High for the
`archive` dismissal's first reason (the schema string is explicit that it is an
HTTPS zip URL, and its grep output is shown above); Medium for its second (the component-path argument's only
visible use in `Nqo` is the null guard, read from a minified body, so "never a
copy filter" is a read, not a measurement — it does not carry the dismissal on
its own). The costing row counts are High: three `git ls-tree` counts at one sha
that sum to that sha's file count.

### Q2 — Can the suite-specific contract rows be corpus-carried data?

**Answer**: **Yes — every suite-specific row is pure data; none needs code.**
The engine that evaluates them is already generic. And the split is cleaner than
expected: **`tools/gc.py` carries no suite-specific rows at all.** It emits
**15** distinct rule ids (`grep -oE 'self\.flag\([^,]+,[^,]+, *"[a-z-]+"'
tools/gc.py`, 26 call sites, 15 unique ids). One, `lint`, is the delegation
passthrough and is not a rule of its own. The other **14** are its own, and all
14 are generic to any SDD corpus: the 13 listed in `GC_RULES`, plus
`kickoff-fields`, which `DELEGATED_RULES` lists but which gc emits itself
(sweep 6, marker 4). `kickoff-fields` keys on SDD **kickoff frontmatter**
(`date:`, `research_id:`) — a property of the artifact structure, not of this
repository — so the conclusion is unchanged; it is named here because a reader
grepping the source gets 15, not 13. The only suite-specific content reaches gc
by **invoking `tools/skill-lint.py` as a subprocess**. The defect is entirely in
that delegation.

**The current state is worse than the record says — but it is gated, and the
gate is the precondition every number below is conditioned on.** With the
provenance predicate reverted, the bundled sweep fires this repository's rows in
any foreign tree **that has a `docs/` directory**, including one with nothing at
`tools/skill-lint.py`. A foreign tree **without** `docs/` never reaches the
delegation at all: it exits 2 with zero findings, from a check in `main()` that
precedes both the linter resolution and the sweep itself (diagnosed below under
*The `docs/` precondition*). The precondition is stated here because an earlier
revision of this document recorded the fixture recipe **without** `docs/` and
recorded the 41-finding output against it; that pairing was false, and the recipe
is corrected below.

The fixture, **as run**, with `docs/` present:

```bash
rm -rf $TMPDIR/foreign
mkdir -p $TMPDIR/foreign/src $TMPDIR/foreign/docs && cd $TMPDIR/foreign && git init -q .
echo '# a foreign project' > README.md && echo 'print(1)' > src/app.py
git add -A && git -c user.email=a@b -c user.name=a commit -qm init
I=~/.claude/plugins/cache/sdd-commons/sdd/0.1.0
python3 $I/tools/gc.py --report --root $TMPDIR/foreign | tail -1
```

```
FAIL: 41 finding(s), 0 warning(s), 0 info
```

(exit 1). `docs/` is empty and untracked — `git add -A` does not stage an empty
directory — so it is a bare directory the consumer happens to have, which is the
weakest form the precondition can take. The rule-id histogram, machine-counted
from the same run:

```bash
python3 $I/tools/gc.py --report --root $TMPDIR/foreign > $TMPDIR/o1.txt 2>&1
grep -oE '\[[a-z-]+\]' $TMPDIR/o1.txt | sort | uniq -c
```

```
  40 [required]
   1 [structure]
```

(the `[structure]` one is `.: [structure] skills/ directory not found`.)

| Vector (all on a tree **with** `docs/`) | Result today |
|--------|--------------|
| (0) foreign tree, **nothing** at `tools/skill-lint.py` | `FAIL: 41 finding(s)`, exit 1 — **41** naming this repository's paths |
| (a) foreign tree with a real unrelated file at `tools/skill-lint.py` | `FAIL: 41 finding(s)` — identical |
| (b) foreign tree with a **symlink** at `tools/skill-lint.py` | `FAIL: 41 finding(s)` — identical |
| (c) the **same** tree with `docs/` removed | `error: <root> has no docs/ directory`, exit 2, **0 findings** |

Vector (0) is the one measured above. (a) and (b) are **not re-measured in this
repair** — they were measured in the original dispatch, and the reason they are
identical is structural and is given in the next paragraph (the sibling wins
before the swept root is ever consulted, so what sits at `<foreign>/tools/` is
never read). They are recorded as expected-identical rather than as fresh
measurements. (c) **is** measured — it is the recorded recipe's own output, shown
under *The `docs/` precondition* below.

The counts 11 and 40 from the previous cycle described a predicate that no longer
exists; the baseline **on a `docs/`-bearing tree** is 41. Vectors (a) and (b)
must still be in the acceptance set — they are cheap and they pin the symlink
behaviour — but the **primary** vector is (0), a foreign tree with nothing
suite-shaped in it at all, and (c) is now a vector in its own right because it is
the most ordinary consumer shape.

**Why it fires whenever it runs at all**: the sweep resolves the linter by trying
its own sibling first and the swept root second —

```python
for cand in (Path(__file__).resolve().parent / "skill-lint.py",
             self.root / "tools" / "skill-lint.py"):
```

— and in the materialised install the sibling always exists. Past the `docs/`
gate there is no symlink to fake and no predicate to get wrong: the tool finds a
linter every time and runs its suite rows every time.

**The `docs/` precondition, diagnosed.** The bail is in `main()` in
`tools/gc.py`, immediately after the git-repository probe resolves `root` and
**before** either the `--fix` dispatch, the `Gc(...)` construction or the
`gc.lint_path()` "linter missing" check:

```python
    if not (root / "docs").is_dir():
        print(f"error: {root} has no docs/ directory")
        return 2
```

Measured on the very same fixture with `docs/` removed:

```bash
rm -rf $TMPDIR/foreign/docs
python3 $I/tools/gc.py --report --root $TMPDIR/foreign; echo "EXIT=$?"
```

```
error: /private/tmp/claude-501/foreign has no docs/ directory
EXIT=2
```

Three consequences, all of which the requirements stage must carry:

1. It is gated by **neither** of the two changes this answer proposes. It is not
   `lint_suite_rules` (that flag is read one line later, when `Gc` is
   constructed) and it is not the `skills/` `[structure]` check (that runs inside
   `Gc.run()`, which is never reached). So it is a **third, independent** gating
   condition on the swept root, alongside the `skills/`-absent one.
2. A consumer repository **with no `docs/` directory** — the most ordinary
   consumer shape, since `docs/` here means an *SDD artifact corpus*, not a
   documentation folder — therefore cannot reach `exit 0` no matter what is done
   to the suite rows.
3. It does **not** fabricate anything. It emits zero findings, names the
   consumer's own root, and declines. On the harm the previous cycle's criterion
   was written to catch — a consumer seeing findings that name *this
   repository's* paths — vector (c) is already clean today.

**Restated acceptance target.** Because of (3), the target `exit 0, zero
findings` was the wrong shape: it conflated "does not fabricate" with "sweeps
successfully", and it is unreachable for vector (c) after both proposed changes.
The target is restated per-shape, and each half is independently checkable:

| Consumer shape | Required outcome |
|---|---|
| Has `docs/` (an SDD corpus) | `exit 0`, **zero** findings — needs both changes below |
| No `docs/` | `exit 2`, **zero** findings, message naming the **consumer's** root — holds today, no change |

The invariant that spans both, and the one an acceptance criterion should
actually assert, is: **no finding line names a path belonging to this
repository, under any vector.** Exit code is then a per-shape expectation, not a
universal constant.

**So the change count is two, not three — and the third condition is a recorded
decision, not an omission.** Reaching the restated target needs: (1) source the
rows from a corpus-carried data file instead of module constants, and (2) make an
absent `skills/` directory mean *nothing to lint* rather than a structural
failure. The `docs/` bail needs **no** change under the restated target, because
declining to sweep a non-corpus is correct behaviour for a corpus sweep. The
alternative reading — that a consumer sweep should exit 0 on a tree with no
`docs/`, treating "no corpus" as "nothing to do" exactly as change (2) treats "no
`skills/`" — is coherent, symmetric with (2), and would make it three changes. It
is **not** adopted here, for one reason: an `exit 2` naming the consumer's own
root is a **diagnosable** outcome (the operator learns the sweep was pointed at
the wrong tree), whereas a silent `exit 0` over an empty corpus is the same
vacuous-pass shape the recorded derivation constraint exists to prevent. The
choice is recorded under Open Questions so a later cycle can reverse it cheaply;
nothing else in this document depends on which way it goes.

**Which bundled copy is invoked changes the failure, and both are wrong.** The
install ships the sweep twice (root-side, recursive, all file types, non-empty
— the derivation constraint recorded last cycle):

```bash
git ls-files | grep -vE '^tools/' | grep -E '/tools/'
# skills/orchestrate/tools/gc.py
# skills/orchestrate/tools/telemetry.py
```

Both copies are byte-identical to their `tools/` originals (`cmp -s`). Run in
the same foreign tree, **`docs/` present** (without it both copies take the
`docs/` bail above and the divergence does not arise):

```bash
python3 $I/skills/orchestrate/tools/gc.py --report --root $TMPDIR/foreign; echo "EXIT=$?"
```

```
error: linter missing — expected /private/tmp/claude-501/foreign/tools/skill-lint.py
EXIT=2
```

| Invoked copy (foreign tree **with** `docs/`) | Behaviour |
|--------------|------------------------|
| `tools/gc.py` (plugin root; sibling linter present) | `exit 1`, 41 findings naming this repository's paths |
| `skills/orchestrate/tools/gc.py` (the skill-directory-relative copy the driver documents) | `exit 2`, `error: linter missing — expected <foreign>/tools/skill-lint.py` |

The divergence is the sibling-first resolution: under `skills/orchestrate/tools/`
the sibling is `skill-lint.py`'s *absent* neighbour — only `gc.py` and
`telemetry.py` are bundled there — so resolution falls through to the swept root,
finds nothing, and the linter-missing check fires. So the consumer-facing entry
point does not fabricate findings — it refuses to run. Under the restated
acceptance target above, the second row already satisfies the spanning invariant
(zero findings naming this repository) but not the `docs/`-bearing shape's
`exit 0`; the first row satisfies neither.

**The rule split.**

| Class | Where | Count | Generic? |
|-------|-------|-------|----------|
| Sweep's own rule ids (`xlink-dead`, `id-missing`, `stale-chain`, `qimpl-undefined`, `qimpl-unreferenced`, `qimpl-broken-ref`, `trace-empty`, `traceability-aggregate`, `traceability-rowdrop`, `index-research`, `index-requirements`, `spec-approval`, `plan-history-name`, **`kickoff-fields`**) | `tools/gc.py` | 14 (+ `lint`, the delegation passthrough, = 15 emitted ids) | **Generic** — they key on the SDD `docs/` layout and on kickoff frontmatter, carry no repository-specific literal, and are meaningful in any repository that uses this artifact structure |
| `REQUIRED` marker rows | `tools/skill-lint.py` | **40** | Suite-specific |
| `FORBIDDEN` phrase rows | `tools/skill-lint.py` | **13** | Suite-specific (patterns such as a retired spike directory name, a superseded version-check wording) |
| `TEMPLATE_PAIRS` | `tools/skill-lint.py` | **4** (machine-counted — see the `ast.parse` command below) | Suite-specific rows; generic comparison |
| `VERSION_GATED_SKILLS` | `tools/skill-lint.py` | **9** | Suite-specific |
| Retired-prefix names and scope — one rule over six literal lists: `RETIRED_SKILLS` 10, `RETIRED_TOOLS` 5, `RETIRED_SCOPE_DIRS` 6, `RETIRED_SCOPE_FILES` 6, exclusions 2 (`RETIRED_SCOPE_EXCLUDE_DIRS` 1 + `..._FILES` 1), `RETIRED_SUFFIXES` 9 | `tools/skill-lint.py` | **1 rule, 38 literal entries** (27 of them names and scope paths) | Suite-specific rows; generic scan |
| Structural checks (frontmatter well-formedness, `name` matches directory, ordinals, size thresholds, `references/` link resolution) | `tools/skill-lint.py` | — | **Generic** for any skill suite, *except* the premise below |

**No headline total is claimed.** The exact, machine-counted per-class figures
are 40 `REQUIRED` + 13 `FORBIDDEN` + 9 `VERSION_GATED_SKILLS` = **62 rows**,
plus `TEMPLATE_PAIRS` (**4**) and the retired-prefix rule (one rule over 38
literal entries). Summing a rule against its list entries would be comparing
unlike units, so the per-class counts stand on their own.

`TEMPLATE_PAIRS` is machine-countable after all. The literal contains a `Name`
reference (`TEMPLATE_DRIFT_FIX`) so it does not `literal_eval`, but it parses,
and the element count is read off the AST without evaluating anything:

```bash
python3 -c "
import ast
for n in ast.parse(open('tools/skill-lint.py').read()).body:
    if isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'TEMPLATE_PAIRS':
        print('TEMPLATE_PAIRS elements:', len(n.value.elts))
"
```

```
TEMPLATE_PAIRS elements: 4
```

The earlier "read by eye — not independently machine-verified" hedge is
**retired**: 4 is confirmed independently of the reading that produced it.

**Does any suite-specific rule need code rather than data?** **No.** Each row is
already a flat record over string fields, and every algorithm that consumes them
is row-agnostic:

- `FORBIDDEN` = `{pattern, files, allow[], reason, fix, severity}`
- `REQUIRED` = `{file, pattern, min, reason, fix, severity}`
- `TEMPLATE_PAIRS` = a list of file pairs; the byte-for-byte fenced-block
  comparison is the generic part and stays in code
- `VERSION_GATED_SKILLS` = a list of names
- retired-prefix = name lists plus directory/suffix scope lists

**Minimum expressive form** for the data file, therefore: five named arrays of
records whose fields are strings, integers and string arrays — no expressions,
no callbacks, no regex beyond what `pattern` already is. JSON is sufficient and
is stdlib in both directions; no new dependency is introduced. What does **not**
exist today, and what Q1's costing shows is not one field: **rows must declare
which root they resolve against.** A single root prefix is insufficient — the
`REQUIRED`/`FORBIDDEN`/`VERSION_GATED_SKILLS` rows and the anchor side of
`TEMPLATE_PAIRS` resolve against the **plugin root**, while the retired-prefix
scope (`RETIRED_SCOPE_FILES`, and the `docs/spec` + `docs/requirements` members
of `RETIRED_SCOPE_DIRS`) and the spec side of `TEMPLATE_PAIRS` resolve against
the **repository root**, which after the move is the plugin root's parent. So
the minimum form carries a per-row (or per-class) root selector over two named
roots, and the tool must accept both. This is still a data change rather than a
code change, and it is still the same concept Q1's move forces — which is why
the two should be solved together — but it is a two-root concept, not a
one-prefix one, and a design that assumes one root will silently produce
vacuous passes.

**The plumbing already exists.** Both tools already carry a fixture-only switch
that does exactly the required thing — `Linter(root, suite_rules=False)` skips
`REQUIRED` (line 540) and the template-pair check (line 599), and
`Gc(root, lint_suite_rules=False)` drives it through a subprocess shim. The
reframing is to make that switch **derived from the swept corpus** instead of
from a fixture flag: rows present in the tree under sweep → run them; rows
absent → do not.

**Stated constraint — swept-root-only resolution, and where the file lives.**
This is the one thing a spec author could get wrong while satisfying every other
sentence in this answer, so it is stated as a requirement rather than implied.
The rule-data file is

```
<swept root>/tools/skill-lint.rules.json
```

and it **must be resolved from the swept root alone** — `self.root / "tools" /
"skill-lint.rules.json"` — with **no fallback whatsoever** to the tool's own
directory (`Path(__file__).resolve().parent`). The defect diagnosed above *is*
sibling-first resolution: in a materialised install the tool's sibling always
exists, so a data file resolved sibling-first would always be found too, and the
fabrication failure mode would return unchanged — with the data file merely
standing in for the linter as the thing that is always present. A design that
ships the rule data beside the bundled linter under `plugins/sdd/tools/` **and**
lets the linter read it from beside itself reproduces today's bug exactly.

Shipping the file beside the bundled linter is nonetheless correct — it is this
repository's own rule payload, and this repository's plugin root is a swept root
in its own right (its self-sweep points `--root` at the plugin root). The
invariant that makes both true at once is: *the file is found only where the
sweep is pointed.* When this repository sweeps itself the swept root is the
plugin root and the file is found; when a consumer sweeps their tree the swept
root is theirs, they carry no such file, and the suite rows are off by
construction — no predicate to invert, nothing a symlink can fake. (If a
consumer deliberately places a file at `<their root>/tools/skill-lint.rules.json`,
the rows they get are rows *they* installed, keyed relative to *their* root.)

The two named roots of the paragraph above are a property of the **rows**, not
of the **file**: the file is located at exactly one place — the swept root — and
each row then declares which of the two roots, plugin root or repository root,
its own paths resolve against.

**Measured acceptance shape — how close the existing switch already gets:**

```python
g = Gc(Path('$TMPDIR/foreign'), lint_suite_rules=False)
rc = g.run()     # exit: 1, findings: 1
```

**40 of 41 findings disappear.** The residual is the one `[structure]` finding,
`.: [structure] skills/ directory not found` — a check that is *not* gated by
the switch and whose premise ("the swept root is a skill suite") is itself
suite-specific. It alone keeps the exit code at 1. So the **restated** acceptance
target's `docs/`-bearing row (`exit 0`, zero findings naming a path in this
repository) is reachable with **two** changes and no new design: (1) source the
rows from a corpus-carried data file instead of module constants, and (2) make an
absent `skills/` directory mean *nothing to lint* rather than a structural
failure. The `no docs/` row of that target is satisfied today by the bail
diagnosed above and needs no change — under the stated decision to keep the
diagnosable `exit 2`. If that decision is reversed, the count becomes three.

**Confidence**: High. The split, the counts, the unconditional 41-finding
baseline, the two-copy divergence and the 41→1 reduction are all measured
outputs, not readings. Medium only on the claim that no *other* generic check
carries a hidden suite premise the way `[structure]` does — the foreign tree
used here has no `skills/` directory, so any rule that only fires inside a
populated `skills/` tree (notably the 13 `FORBIDDEN` phrase rows, which are
**not** gated by the existing switch) was never exercised. A consumer repository
that happens to have its own `skills/` directory is an untested third vector and
should be added to the acceptance set. The rule-id enumeration and the per-class
row counts are High (grepped literals), and `TEMPLATE_PAIRS` = 4 is now High as
well — confirmed by an `ast.parse` element count independent of the reading that
first produced it. The two-root conclusion
inherited from Q1 is High on the *need* (the keyed paths are enumerated and
their dispositions are in Q1's costing table) and Medium on the *form* (no
two-root run was executed).

### Q3 — The cheapest non-circular install fixture

**Answer**: **`git archive <sha> | tar -x` into a throwaway directory.** It is
one command, needs no network, no clone, no working tree and no plugin
configuration, works on an unmerged branch, and it reproduces the live
GitHub-sourced install's file list **exactly**. The circularity trap is avoided
structurally: the tree is materialised from a named commit object, so nothing
about the working tree — dirty files, untracked files, ignored files — can reach
it.

**Evidence** (the whole fixture, and its assertion):

```bash
mkdir -p $TMPDIR/A && git -C <repo> archive 29febe6 | tar -x -C $TMPDIR/A
(cd $TMPDIR/A && find . -type f | sed 's|^\./||' | sort) > $TMPDIR/A.txt
# live install, minus its runtime lock marker
(cd ~/.claude/plugins/cache/sdd-commons/sdd/0.1.0 && find . -type f | sed 's|^\./||' | sort) \
  | grep -v '^\.in_use/' > $TMPDIR/live.txt
diff $TMPDIR/live.txt $TMPDIR/A.txt    # -> no output: IDENTICAL file lists (198)
```

That `diff` is the fixture's own validation: the cheap offline mechanism and the
real GitHub-sourced install agree file for file. `.in_use/` is a runtime lock
directory the installer creates, not content, and is the only exclusion.

**Why it is representative**, stated explicitly: the installer materialises a
`github` source by cloning and checking out the sha, and `git archive <sha>`
emits exactly the tracked tree of that commit. The comparison above measures
that equivalence rather than assuming it. It is *not* representative of the
`.in_use` marker or of file modes beyond what `git archive` preserves, neither
of which any acceptance criterion in this cycle depends on.

**Four things the fixture must provide, and the command for each:**

1. **Full-tree install at a named commit** (the `github` source, today's shape):
   `git archive <sha> | tar -x -C <dir>`. Works for an unmerged branch —
   validated at `0f5ec2675fcc0c4a993922fd6ba1702ddec426d9`, the `packaging`
   HEAD, which exists on no remote.
2. **Subdirectory install at a named commit** (the `git-subdir` shape Q1
   selects): `git archive <sha> <path> | tar -x -C <dir>` gives the subtree
   directly; the fuller simulation, which also exercises cone mode and the
   installer's final subdirectory move, is the clone/sparse-checkout/checkout
   sequence recorded under Q1. The `git archive` form is cheaper and is the
   right default; the clone form is worth keeping for one assertion that cone
   mode does not surprise us.
3. **A foreign consumer tree** for Q2's vectors — recorded verbatim under Q2
   (`git init`, two unrelated files, **an empty `docs/` directory**, one commit).
   The `docs/` directory is **load-bearing, not incidental**: without it the
   sweep exits 2 at the `docs/` gate before any rule runs, so a fixture that
   omits it silently measures the gate rather than the delegation. Variants:
   a real file and a symlink at `tools/skill-lint.py`; the same tree with
   `docs/` **removed** (vector (c), which asserts the gate itself); and a fourth
   that should be added — a foreign tree carrying its own `skills/` directory.
4. **Assertions against real trees, never against a manifest.** The comparands
   are `find <dir> -type f` (sorted, root-relative) and
   `git ls-tree -r --name-only <sha> [-- <path>]`; the pass conditions are set
   equality and a file count. For the sweep the comparands are the process exit
   code and the finding lines themselves, grepped for paths belonging to this
   repository. No assertion reads `marketplace.json` — that is precisely the
   substitution that let the previous cycle's criterion pass while the condition
   persisted.

**Where it should live.** `plugins/sdd/tools/`, **inside** the plugin root,
beside the bundled `gc.py` and `skill-lint.py` it exercises. **Recorded choice,
not a measurement** — it is the one place this answer had to decide rather than
measure, and the rejected alternative and its cost are stated in the two
paragraphs below.

Two placements were available and they are mutually exclusive, so this answer
picks one and says which. **(a) Inside the plugin root**, where it ships to
consumers along with everything else under `plugins/sdd/`. **(b) In a dev-only
`tools/` left at the repository root** — which would require Q1's costing to
split `tools/` into a shipped subset and a dev-only subset and to re-derive the
45/154 numbers accordingly. **(a) is chosen.** It keeps Q1's costing table
exactly as counted — all 14 `tools/` files move, `tools/` does not split, and
nothing named `tools/` survives at the repository root — and it keeps the
fixture next to the two tools it materialises and asserts against, which are
themselves inside the plugin root.

The cost of the choice is stated plainly: **the fixture ships.** An earlier
revision of this document claimed "everything under `plugins/sdd/` ships,
everything left in `tools/` does not"; after Q1's move nothing is left in a root
`tools/`, so that sentence had no referent and it is **withdrawn**, along with
the "outside the plugin root" placement it justified. A few tens of KB of
development apparatus inside the install is the price. It is not a declared
component in `marketplace.json`, so — by the copy/load distinction Q1
establishes for the component list — it is copied into the install but never
loaded by anything, and no consumer is required to run it.

It should expose
the four materialisations above as subcommands so that this cycle's
verification, the pre-existing self-tests and later cycles all call the same
code. It is **not** shipped in this spike; the commands above are the record.

**Confidence**: High. The equivalence to the live install is a measured `diff`
producing no output, and the unmerged-branch case was materialised and counted.

## Implications for Design

- **Requirements should carry the `plugins/sdd/` root move as decided, not as an
  option.** Q1's mechanism is subdirectory-scoped; there is no filter that would
  let the plugin root stay at the repository root, and the one apparent
  alternative — an `archive` entry with declared components — is dismissed under
  Q1: it installs a hosted zip by URL rather than the repository at a ref, and
  its component-path argument is a safety guard, not a copy filter. The
  symmetric alternative — keeping `"source": "./"` and moving `docs/` out of the
  repository — is not on the table either: it was rejected at DISCUSS
  (`docs/ws/packaging/kickoff.md` §Decided at DISCUSS item 1) for breaking the
  single shared corpus the skills' phase detection, staleness chain and
  traceability assume. The move
  takes the install from ~199 files / 5.0 MB to roughly **45** files, and
  removes `docs/` by construction rather than by a rule anyone has to maintain.
- **PROVE-FIRST GATE — sequence one real `plugin install` BEFORE the 45-file
  move.** "Decided, not an option" above is a decision about *direction*; the
  evidence under it is **Medium** confidence and **unexecuted**: Q1's confidence
  paragraph states plainly that a `git-subdir` entry in *this* marketplace
  resolving as modelled is read from one CLI release's minified internals, with
  no install performed. That no-install constraint was **this spike's**, not the
  next stage's, and it must not be inherited silently by a stage that is about to
  move 45 files and re-root ~2 500 prose tokens. So the first task of the next
  stage is a throwaway proof, not the move:

  1. In a scratch directory, create a throwaway git repository containing a
     subdirectory plugin (`<repo>/plugins/sdd-probe/.claude-plugin/plugin.json`
     plus one trivial skill) **and**, at its root, a
     `.claude-plugin/marketplace.json` whose single entry is
     `{"source": {"source": "git-subdir", "url": "<file:// or owner/repo>",
     "path": "plugins/sdd-probe"}}` — i.e. the same-repository shape Q1 could
     only model.
  2. Add that marketplace and run one real `claude plugin install`.
  3. Assert against the **materialised** tree, never the manifest: the installed
     directory contains the subdirectory's files and **nothing** from the
     repository root (no `README.md`, no sibling directories), and the plugin's
     skill loads.

  It is a handful of files and one install. If it fails, the entire `git-subdir`
  selection is refuted **before** anything is moved, and the `archive` route or a
  repository split comes back onto the table. This gate **replaces** the softer
  "worth repeating before the move is executed" wording in Q1's confidence
  paragraph as the operative instruction: that sentence is about re-deriving the
  internals on a newer CLI; this is about executing the thing at all. Both are
  cheap; this one is blocking.
- **Sequence the move before the rule-data work, and let the two share one
  two-root concept.** The 40 path-keyed rows and the 54 tool-path tokens
  re-root onto the plugin root, but the retired-prefix scope and the spec side
  of the template pairs stay at the repository root — so the shared concept the
  corpus-carried rule file needs is a *pair* of named roots with a per-row
  selector, not a single prefix. Doing the two separately pays for that concept
  twice; designing it as one root ships a silent vacuous pass.
- **The rule-data file's location is a requirement, not an implementation
  detail.** Specs must carry it as a constraint: the file is
  `<swept root>/tools/skill-lint.rules.json`, resolved from the swept root
  **only**, never from the linter's own directory. The bundled copy under
  `plugins/sdd/tools/` is this repository's own payload and is read only when
  the plugin root *is* the swept root. A sibling-first fallback reinstates the
  exact fabrication bug this cycle exists to remove, while satisfying every
  other sentence of Q2.
- **The install fixture lives inside the plugin root and therefore ships.**
  `plugins/sdd/tools/`, beside the two tools it exercises — chosen over a
  dev-only root `tools/`, which would have forced `tools/` to split and Q1's
  45/154 costing to be re-derived. Requirements should say so, and should not
  carry any claim that development apparatus is excluded from the install: after
  the move there is no unshipped directory to put it in.
- **`tools/gc.py` needs no rule-data file of its own.** Its 14 own rules (15
  emitted ids, one of which is the `lint` passthrough) are generic, including
  `kickoff-fields`, which keys on SDD kickoff frontmatter rather than on this
  repository. The data file belongs to `tools/skill-lint.py`; the sweep's only
  change is how it decides to delegate.
- **The two recorded Q2 test vectors are necessary but no longer sufficient.**
  The unconditional case (0) is the real baseline at 41 findings, and a foreign
  tree with its own `skills/` directory is an untested third vector that the
  ungated `FORBIDDEN` phrase rows can reach. The acceptance set should be four
  vectors, not two.
- **`skills/verify/SKILL.md`'s cwd-relative sweep invocation** (a carried repair)
  should be spelled relative to the plugin root and pointed at whichever copy
  survives the bundled-duplicate decision — the two copies behave *differently*
  in a consumer repository (exit 2 versus 41 findings), so "which copy" is a
  contract question, not a tidiness one.
- **Ruled out**: any design that infers whose tree is being swept. Q2's measured
  result removes the need — absence of the data file is the whole signal.

## Prototype

No branch. Four throwaway trees were materialised under `$TMPDIR`
(`A` — full-tree archive at `29febe6`; `B` — sparse cone checkout at the
`packaging` HEAD; `D` — `docs/` only at `0f5ec26`, for the pinned token count;
`foreign` — the synthetic consumer repository with its vector variants) and
discarded. Every command that produced a number above is quoted inline; nothing
was committed and no probe script survives.

What the probes demonstrate: that the install equals the tracked tree at a sha,
that a cone-mode subdirectory checkout drops `docs/` entirely, that the bundled
sweep fires 41 findings in a foreign tree **that has a `docs/` directory** and
exits 2 with zero findings in one that does not, and that the existing
suite-rows-off switch removes 40 of the 41.

What they do **not** prove: that an executed `claude plugin install` of a
`git-subdir` entry behaves as the installer's code path says (no install was
performed, by constraint — which is why §Implications now carries a blocking
prove-first gate), and that the `FORBIDDEN` phrase rows stay quiet in a foreign
tree that has its own `skills/` directory.

## Budget consumed

| Dispatch | Tool calls | Test runs |
|---|---:|---:|
| 1 — original spike (Q1-Q3) | 25 of 30 | 0 of 0 |
| 2 — repair (S1-S6, m1-m3, m6) | 10 of 18 | 0 of 0 |
| 3 — repair (the six substantive findings above, plus m7-m12) | 8 of 16 | 0 of 0 |
| 4 — repair (B1 the `docs/` precondition, S2-S4, m1-m4) | 15 of 20 | 0 of 0 |

## Open Questions

- Does a `git-subdir` entry inside a marketplace hosted in the **same**
  repository resolve as modelled? The code path is unconditional on that, but it
  was not executed.
- Does a foreign tree carrying its own `skills/` directory draw findings from the
  13 ungated `FORBIDDEN` phrase rows? Untested; the fixture's third vector.
- Should the bundled duplicate at `skills/orchestrate/tools/` survive the root
  move at all, or should the skill body point at the plugin root's single copy?
  The duplicate is byte-identical today; after the move, one copy would suffice
  and the drift check would have an empty population — which is exactly the
  vacuous-pass shape the recorded derivation constraint warns against, so the
  check would need retiring rather than emptying.
- Does `Nqo` prune an extracted archive to its declared component paths anywhere
  beyond the null guard read here? Not established. Recorded as a question
  rather than asserted, because Q1's `archive` dismissal does not depend on it —
  reason 1 (a hosted zip is not a repository source) stands alone.
- Does `Cqo(w, xe, r)` — called on the resolved subdirectory immediately before
  the `git-subdir` move — guard path traversal or symbolic links? Its body was
  not read. An earlier revision asserted such guards on the strength of a grep
  whose output turns out to describe git **worktree** creation; the assertion is
  withdrawn above and the question recorded here instead. Nothing in Q1 depends
  on the answer.
- Should the installed plugin tree (`plugins/sdd/`) carry its own `README.md` and
  `LICENSE`? Q1's costing counts **45** installed files with **neither** — both
  stay at the repository root, where `git-subdir` leaves them behind, so a
  consumer's installed tree would arrive with no statement of what it is and no
  licence text. That is a defaulted-into outcome, not a chosen one: nothing in
  this spike decided it, and the count simply fell out of "everything that is not
  the plugin stays". The options are (a) accept it — the marketplace listing and
  the repository carry both, and the install is a loaded artifact rather than a
  distributed one; (b) add a short plugin-root `README.md` and a copy of
  `LICENSE` under `plugins/sdd/`, making the install **47** files and the licence
  travel with the code it covers. Requirements should choose explicitly. (b) is
  the conventional answer for anything installed onto a third party's machine,
  but it duplicates `LICENSE` and creates a second file to keep in sync, so it is
  recorded as a question rather than pre-decided here.
- Should a foreign tree with **no `docs/`** exit 0 ("nothing to sweep") rather
  than the diagnosable `exit 2` this document keeps? The restated Q2 acceptance
  target adopts `exit 2`, for the reason given there; reversing it is symmetric
  with the `skills/`-absent change and would make the change count three instead
  of two. Nothing else in this document depends on the answer.
- The two-root linter contract is derived, not exercised: no run with a plugin
  root distinct from the repository root was performed. The acceptance set needs
  a vector that asserts the root-corpus retired-prefix rows still fire after the
  move — the failure mode is silence, so an assertion that they *fire* is the
  only thing that catches it.
