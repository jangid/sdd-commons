---
workstream: packaging
description: Packaging follow-up — docs/ outside the materialised install, the bundled drift sweep usable in a consumer repository via corpus-carried rule data, and a reusable install fixture that makes both falsifiable
cycle: packaging-followup
research_id: RS-PACKAGING-001
entry_stage: research
date: 2026-09-21
branch: packaging
---

# Kickoff: RS-PACKAGING-001 — Packaging follow-up

Run `/sdd:research` for workstream `packaging`. This spike settles the two
questions the marketplace cycle deferred together
(`docs/ws/marketplace/verification.md` §Next Steps, first two bullets) plus the
measurement apparatus both of them need. Its findings must land before
requirements.

## Scope in one paragraph

The marketplace cycle shipped a working plugin and, in doing so, proved that
this repository does not yet know what an *installed* plugin is. Two conditions
were measured, both deferred: the install materialises the entire repository
tree, `docs/` included, and the bundled drift sweep is unusable outside this
repository. They are the same question — *what an installed plugin actually
needs, measured against a materialised install rather than a manifest* — and
they are addressed together here. A third item joins them because the first two
cannot be honestly verified without it: a reusable fixture that materialises an
install into a throwaway tree and a foreign consumer tree, so that every
acceptance criterion in this cycle asserts against real files. Four carried
repairs from the previous cycle ride along; they are known work with known
fixes and enter at requirements, not research.

## Confirmed at DISCUSS (2026-09-21) — measured, not assumed

The previous cycle's install was directory-sourced and **loaded in place**,
which made every install-shaped measurement circular. That is no longer true.
Measured at DISCUSS against the live install:

```
marketplace sdd-commons : {"source": "github", "repo": "jangid/sdd-commons"}
git worktree list       : main checkout only (.worktrees/marketplace removed)
install                 : ~/.claude/plugins/cache/sdd-commons/sdd/0.1.0
                          gitCommitSha 29febe6 — a frozen copy, not a pointer
install total           : 199 files, 5.0 MB
  docs/                 : 145 files, 3.5 MB   (73% of files, 70% of bytes)
  everything else       :  54 files
```

Three consequences carry into the cycle. The marketplace re-point and the
worktree removal that the previous cycle listed as outstanding operator actions
are **done**; this session dispatched from the cache copy, which confirms the
install works. The `docs/`-in-the-install condition is **confirmed on a real
GitHub-sourced tree**, not inferred from the manifest — the failure mode that
let the criterion pass last cycle cannot recur on this evidence. And the
baseline above is the number any exclusion work must move.

## Decided at DISCUSS (2026-09-21 — requirements inherit these; not re-litigated)

1. **The `docs/` fallback is authorized.** Spike the exclusion declaration
   first — it is by far the cheapest lever. If no declaration exists, the cycle
   **may move the plugin root** to a `plugins/sdd/` subdirectory. This is
   expensive on purpose: it relocates every skill and agent file and forfeits
   the zero-files-moved property the previous cycle's chunk ordering rested on.
   It is authorized because it is the only lever that works, and because doing
   it before external consumers exist is strictly cheaper than after. Splitting
   `docs/` into a separate repository was considered and **rejected** — it
   breaks the single shared corpus that every `sdd:*` skill's phase detection,
   staleness chain and traceability assume.

2. **The consumer-repo fix is corpus-carried rule data, not a provenance
   predicate.** The previous cycle built a predicate twice and reverted both:
   script-keyed, the bundled copy sweeping *this* repository took the OFF branch
   and silently disabled this repository's own 40 contract rows under the
   command its own driver documents (round 2 `R1`); root-keyed, any foreign tree
   containing a file at `tools/skill-lint.py` got this repository's rules run
   against it — 11 fabricated findings naming this repository's paths, and 40
   via `ln -s`, because `is_file()` follows symlinks (round 3 `R1`). The
   reframing this cycle adopts: the defect is not that the tool cannot tell
   whose tree it is, but that **suite-specific contract rows are hardcoded in a
   tool that ships away from the corpus they describe**. Move those rows into a
   data file the swept repository carries and the question dissolves — a
   consumer tree has none, so the sweep runs its generic rules and exits clean.
   There is no predicate left to get wrong in a third direction, and nothing a
   symlink can fake. **Do not re-open the predicate design.**

3. **Every acceptance criterion in this cycle is measured against a
   materialised install.** The lesson the previous cycle taught was *checks that
   don't check* — fourteen false acceptance criteria, whose recurring shape is a
   criterion whose population the change itself redefines. The `docs/` criterion
   was one of them: written against the component list, it passed while the
   condition persisted, because the component list governs what Claude Code
   *loads* and not what an install *copies*. Manual per-criterion discipline is
   what failed; this cycle builds the fixture instead.

## Research questions

**Q1 — Does any mechanism exclude paths from a materialised install?**
Answer by materialising an install and inspecting the resulting tree. A manifest
field that is *documented* to exclude but does not change the tree is a negative
answer. Candidates to try: `.claudeignore` or a similar ignore file, a manifest
`files:`/`exclude:` filter, `.gitignore` semantics, and whether the component
list has any effect on what is copied (the previous cycle's finding says it does
not — confirm rather than inherit). If no mechanism exists, the question becomes
a costing: for the `plugins/sdd/` root move, enumerate which files move, and
determine what breaks — specifically the driver's ten lazily-read
skill-directory-relative `references/*.md`, the marketplace `source` field, the
bundled tools' own paths, and the linter's 40 path-keyed exemptions.

**Q2 — Can the sweep's suite-specific rows be expressed as corpus-carried
data?** Establish the split: of `tools/gc.py`'s rules, how many are generic
(meaningful in any repository) and how many are specific to this suite's
contracts? Does any suite-specific rule need *code* rather than data — and if
so, which, and what is the minimum expressive form the data file needs? Then the
acceptance shape: with the rows absent, a foreign tree must produce **exit 0 and
zero findings naming this repository's paths**. The previous cycle's two failure
cases are the test vectors — a foreign tree carrying `tools/skill-lint.py`
(11 fabricated findings) and one carrying a symlink at that path (40). Both must
now yield nothing. Note also the derivation constraint recorded last cycle: the
bundled-drift check must be root-side and recursive over all file types with a
non-empty guarantee, because one level deep and `.py`-only was blind to nested
and non-`.py` copies, and emptying the population made the criterion pass
vacuously.

**Q3 — What is the cheapest fixture that materialises an install
non-circularly?** The trap on record: a directory-sourced plugin loads in place
from its source directory, so a fixture built that way tests the working tree
against itself and always passes. The live install is now GitHub-sourced and
frozen at a sha, which is the property the fixture must reproduce — including
for a branch that is not yet merged. Determine how to materialise an install
pinned to a named commit, how to build a *foreign consumer tree* for Q2's
vectors, how the fixture asserts (file lists and counts against the real tree,
not against the manifest), and where it lives so that both this cycle's
verification and later cycles can call it.

## Success criteria

The cycle is done when a consumer installing `jangid/sdd-commons` from the
marketplace gets a tree **without `docs/`**, and `python3 tools/gc.py --report`
run from that install inside **their own repository** exits 0 with no finding
naming a path in this repository. Both demonstrated against materialised trees
produced by the fixture, with the 199/145-file baseline above as the before
measurement.

The research spike itself is complete when Q1 has a yes-with-mechanism or a
no-with-costing, Q2 has a rule split and a decided data format, and Q3 has a
working non-circular materialisation command.

## Budget

Research is time-boxed to **30 tool calls** across Q1–Q3. A question that
exhausts its share records what it learned and what remains rather than
overrunning; an early answer on Q1 (a mechanism exists) makes its costing half
unnecessary and returns that budget to Q2 and Q3.

## Out of scope

- Rewriting the sweep's **generic** rules. This cycle relocates suite-specific
  rows; it does not redesign what the sweep checks.
- Any new SDD phase, skill or agent.
- The `sdd:*` naming and the marketplace manifest structure — settled last
  cycle.
- Re-opening the provenance-predicate design (decision 2 above).
- Publishing, versioning or announcing the plugin beyond what the success
  criteria require.

## Carried forward — known work, entering at requirements

These are the previous cycle's loose ends. They are not research questions; each
has a known fix.

- **Deferral-backlog screen marker leakage.** The L-1 adjacency check reads the
  *preceding* bullet's `[closed …]` marker as satisfying the *following* entry —
  the rule examines that line without asking which entry the marker belongs to.
  It scored the marketplace cycle's own carried item not-live by accident. The
  true before/after row is recorded in `docs/ws/marketplace/verification.md`
  §Deferral-Backlog Screen. This is the same failure class as decision 3: a
  check that does not check.
- **`skills/verify/SKILL.md:169`** — the one remaining cwd-relative drift-sweep
  invocation in a shipped skill body. Decide where a non-driver skill's bundled
  tool copy lives, then spell it skill-directory-relative. This interacts with
  Q1's root move; sequence it after that answer.
- **`docs/spec/orchestration.md:574`** — name the project README by its current
  filename.
- **`tools/skill-lint.py:381` and `:1252`** — drop the deleted front door's
  filename from `RETIRED_SCOPE_FILES` and from the self-test's independent
  `policed_files` tuple **together** (`Q-IMPL-MARKETPLACE-017`);
  behaviour-neutral, but editing one alone trips the scope-drift check.
- **`CLAUDE.md:251` vs `CLAUDE.md:215`** — reconcile which marker the repository
  uses. Blocked last cycle by a must-not-change-in-substance fence on that
  section; that fence no longer applies.

## Already done — do not re-do

Listed because the previous cycle's §Next Steps records them as outstanding and
a reader of that file would otherwise plan them:

- Re-pointing the marketplace at `jangid/sdd-commons` — done; verified above.
- Removing the load-bearing `.worktrees/marketplace` — done; `git worktree list`
  shows the main checkout only. The ordering constraint it carried (re-point and
  confirm dispatch **before** removal) was satisfied.
- Retiring the ten `~/.claude/skills/sdd-*` symlinks — operator decision
  2026-09-21.
