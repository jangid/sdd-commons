---
id: RS-PACKAGING-002
workstream: packaging
status: Complete
date: 2026-09-21
last_updated: 2026-09-21
research_refs: [RS-PACKAGING-001, RS-MARKETPLACE-001]
questions:
  - "Q1 — Does a `git-subdir` marketplace entry actually install as modelled: subdirectory-only contents, same-repo entry resolution, plugin-root-relative component paths?"
  - "Q2 — After the `plugins/sdd/` root move, which root is the sweep pointed at, and how is the rule data found from it without a tool-directory fallback? (kickoff's premise corrected — see §Open Questions)"
budget: "25 tool calls, 0 test runs"
---

# Research: RS-PACKAGING-002 — the git-subdir mechanism and the post-move root interface

## Questions

Cycle 1 (`RS-PACKAGING-001`) answered its three questions but was rejected at the
stage gate. Two things it rested on were never settled: the install mechanism was
**read, not executed**, and two of its own answers contradicted each other about
which root the sweep runs against. This spike proves the first and settles the
second. Everything under the kickoff's §Carried forward is INPUT here and is
cited, not re-derived.

Environment for every measurement below: CLI `2.1.278`, repository HEAD
`c95c024ab25575af03c4ecdf0c908565eacd296b` (branch `packaging`), 2026-09-21.

## Findings

### Q1 — Does a `git-subdir` entry actually install as modelled?

**Answer: YES on (a) and (b); (c) resolves in the weaker, measured form.** A
real install was performed. The materialised tree contains the subdirectory's
contents and nothing else — (a), directly observed — and the entry resolved from
a `marketplace.json` living in the same repository — (b), directly observed. For
(c), component paths written relative to the plugin root do resolve, but what
the evidence actually measures is that conventional discovery yields the full
inventory **regardless of what the entry declares**, and both controls named
paths that are *absent from the installed tree*; the stronger claim that the
declaration is never consulted is not established (§Open Questions). Either way
component discovery is **conventional** for this layout, so `marketplace.json`
costs **1 line** (the `source` field), not 14.

**The schema, from the shipped CLI.** Cycle 1 rated the mechanism Medium
confidence from a read. The source shape it implies is confirmed by the bundle's
own describe strings:

```bash
strings -n 6 /Users/pankaj/.local/share/claude/versions/2.1.278 \
  | grep -o 'git-subdir[^A-Za-z][^\n]\{0,160\}' | sort -u
```

The decisive line (excerpted from that output):

```
git-subdir"),url:o().describe("Git repository: GitHub owner/repo shorthand, https://, or git@ URL"),path:o().min(1).describe('Subdirectory within the repo containing the p
```

So the entry is `{"source": "git-subdir", "url": <repo>, "path": <subdir>}`,
with optional `ref`/`sha`. The same sweep shows the sparse-checkout plumbing
cycle 1 described (`sparse-checkout","set","--cone"`, an unshallow-fetch
fallback, and a `git-subdir SHA+path version` cache key that hashes the `path`).

**The fixture** (throwaway, `$TMPDIR`, never committed to this repository). It
deliberately carries root-level files — `README.md`, `docs/rootdoc.md`,
`tools/roottool.py` — whose appearance in the install would be leakage, and a
plugin at `plugins/demo/` with conventional `skills/` and `agents/`
subdirectories. The root `.claude-plugin/marketplace.json` names the plugin's
own repository as `url` and `plugins/demo` as `path`, with component paths
written **relative to the plugin root**:

```bash
R="$TMPDIR/rs-pkg-002/upstream"
mkdir -p "$R/plugins/demo/.claude-plugin" "$R/plugins/demo/skills/alpha" \
         "$R/plugins/demo/agents" "$R/.claude-plugin" "$R/docs" "$R/tools"
echo "ROOT README - must not be installed" > "$R/README.md"
echo "root doc"                            > "$R/docs/rootdoc.md"
echo "print('root tool')"                  > "$R/tools/roottool.py"
printf '%s\n' '{ "name": "demo", "version": "0.1.0", "description": "git-subdir probe plugin" }' \
  > "$R/plugins/demo/.claude-plugin/plugin.json"
printf '%s\n' '---' 'name: alpha' 'description: Probe skill shipped from a plugin subdirectory.' '---' 'Probe skill body.' \
  > "$R/plugins/demo/skills/alpha/SKILL.md"
printf '%s\n' '---' 'name: beta' 'description: Probe agent. Use when probing.' 'tools: Read' '---' 'Probe agent body.' \
  > "$R/plugins/demo/agents/beta.md"
cat > "$R/.claude-plugin/marketplace.json" <<EOF
{
  "name": "rs-pkg-002-probe",
  "owner": { "name": "probe" },
  "plugins": [
    {
      "name": "demo",
      "source": { "source": "git-subdir", "url": "file://$R", "path": "plugins/demo" },
      "description": "probe",
      "skills": ["./skills/alpha"],
      "agents": ["./agents/beta.md"]
    }
  ]
}
EOF
git -C "$R" init -q && git -C "$R" add -A \
  && git -C "$R" -c user.email=probe@example.com -c user.name=probe commit -q -m "probe fixture"
git -C "$R" ls-files; echo "HEAD=$(git -C "$R" rev-parse HEAD)"
```

Output:

```
.claude-plugin/marketplace.json
README.md
docs/rootdoc.md
plugins/demo/.claude-plugin/plugin.json
plugins/demo/agents/beta.md
plugins/demo/skills/alpha/SKILL.md
tools/roottool.py
HEAD=85f305a2255b6e9372de16192d38c4852aca75f6
```

Seven tracked files: **three** inside the plugin subdirectory, **four** at the
repository root.

**The install.** Every plugin command below ran with `CLAUDE_CONFIG_DIR` pointed
at a throwaway directory, so the operator's live configuration was not merely
left alone by convention — it was **out of reach of the commands entirely**:

```bash
export CLAUDE_CONFIG_DIR="$TMPDIR/rs-pkg-002/cfg"; mkdir -p "$CLAUDE_CONFIG_DIR"
claude plugin marketplace add "$TMPDIR/rs-pkg-002/upstream"
claude plugin install demo@rs-pkg-002-probe
```

Output:

```
Adding marketplace…✔ Successfully added marketplace: rs-pkg-002-probe (declared in user settings)
Installing plugin "demo@rs-pkg-002-probe"...✔ Successfully installed plugin: demo@rs-pkg-002-probe (scope: user)
```

**(b) — same-repository entry resolution: YES.** The marketplace entry lives at
`.claude-plugin/marketplace.json` in the very repository whose `plugins/demo`
subdirectory the entry's `source` names, and it installed without special
handling. Cycle 1 read this as unconditional in code; it is now executed.
Confidence **High**, with the caveat under §Open Questions that the `url` was a
`file://` URL rather than a GitHub remote.

**(a) — subdirectory-only contents: YES, nothing from the repository root.**

```bash
C="$TMPDIR/rs-pkg-002/cfg"
find "$C/plugins/cache/rs-pkg-002-probe/demo/0.1.0" -type f \
  | sed "s|$C/plugins/cache/rs-pkg-002-probe/demo/0.1.0|<plugin>|" | sort
```

Output:

```
<plugin>/.claude-plugin/plugin.json
<plugin>/agents/beta.md
<plugin>/skills/alpha/SKILL.md
```

Exactly the three files tracked under `plugins/demo/`, re-rooted at the install
directory with the `plugins/demo/` segment stripped. `README.md`,
`docs/rootdoc.md` and `tools/roottool.py` are **absent**. This is the property
the whole root move exists to buy, and it is now observed rather than inferred:
`RS-PACKAGING-001`'s "no path-exclusion declaration exists" stands, and
`git-subdir` is the lever that makes exclusion unnecessary.

The install record pins the commit it materialised:

```bash
cat "$TMPDIR/rs-pkg-002/cfg/plugins/installed_plugins.json"
```

```
        "installPath": "/tmp/claude-501/rs-pkg-002/cfg/plugins/cache/rs-pkg-002-probe/demo/0.1.0",
        "version": "0.1.0",
        "gitCommitSha": "85f305a2255b6e9372de16192d38c4852aca75f6"
```

**(c) — plugin-root-relative component paths: YES, they resolve; the
declaration cannot subtract from or redirect the conventional inventory.**
The installed plugin's component inventory resolves both components:

```bash
CLAUDE_CONFIG_DIR="$TMPDIR/rs-pkg-002/cfg" claude plugin details demo@rs-pkg-002-probe
```

```
demo 0.1.0
  Description: probe
  Source: demo@rs-pkg-002-probe

Component inventory
  Skills (1)  alpha
  Agents (1)  beta
  Hooks (0)
  MCP servers (0)
  LSP servers (0)
```

Two controls were run to stop this from being a vacuous pass. A second entry
`demo2` with the identical `source` but component paths written **repo-root
relative** (`./plugins/demo/skills/alpha`), and a third entry `demo3` with paths
that **do not exist anywhere** (`./nonexistent/skills/alpha`), were added,
committed, and installed after `claude plugin marketplace update
rs-pkg-002-probe`. Both produced the same inventory as `demo` above.

> **Uncaptured controls.** Unlike the primary install, the tree listing and
> `claude plugin details demo` — each a command with its verbatim output above —
> the two controls are recorded here as a **hand-written summary of runs whose
> stdout was not captured**. They have not been re-run: the install question is
> closed and the operator's live configuration is not to be disturbed again for
> it. The fixture recorded under §Prototype covers the primary install only, so the
> controls are **not reproducible from this document**. The claim below that
> "a stale or wrong component list fails silently" therefore rests on **these two
> uncaptured runs alone**: anything citing it must cite it as **inferred from an
> uncaptured run**, not as measured, and must not inherit the High confidence
> that (a) and the primary (c) observation carry.

**Reading.** For a conventional layout — `skills/` and `agents/` directories at
the plugin root, which is exactly what `plugins/sdd/` will be — components are
discovered **by convention from the installed plugin root**, and that discovery
happens **regardless of what the entry declares**: an entry whose paths point at
a location that does not exist in the installed tree still yields the full
inventory, so a stale or wrong component list fails **silently**, never loudly
(inferred, not measured — see §Q1, uncaptured controls).

Stated precisely, because requirements will quote it: what the two controls
measure is that the declaration cannot *subtract from* or *redirect* the
conventional inventory. Both controls named paths that are **absent from the
installed tree** (`demo2` repo-root-relative, `demo3` nowhere at all), so they do
**not** establish the stronger claim that the arrays are never consulted at all —
that would need a control declaring a **real** component at a **non-conventional**
location, which was not run (recorded under §Open Questions). The stronger claim
is not needed for anything below. Therefore:

- The thirteen component lines in this repository's `marketplace.json` need
  **no edit** after the move. They are already plugin-root-relative
  (`./skills/implement`, `./agents/reviewer.md`, …) and would remain correct
  even if they were load-bearing.
- `marketplace.json` costs **one field**: `"source": "./"` becomes
  `"source": { "source": "git-subdir", "url": "jangid/sdd-commons", "path": "plugins/sdd" }`.
  Cycle 1's unmeasured S1 is settled at the cheap end.
- A stricter corollary the controls bought for free: the component list cannot
  be relied on as a *guard*. It will not fail loudly if it goes stale. Any
  "the manifest lists every component" check must be a repository-side lint
  row, not an install-time expectation. `CLAUDE.md` already requires the
  manifest list and `README.md` §Components to be compared as sets; that
  comparison stays the only thing keeping the list honest.

**Confidence: High** for (a) — directly observed. **(c) splits**: **High** that
declared plugin-root-relative component paths resolve in the installed tree,
which rests on the captured `claude plugin details demo` output above;
**Low — inferred from uncaptured runs** for the clause that the declaration can
neither *subtract from* nor *redirect* the conventional inventory, which rests on
the `demo2`/`demo3` controls alone — a hand-written summary of runs whose stdout
was not captured and which are not reproducible from this document (see the boxed
note above). That clause must not be cited at High. **High** for (b) with one
scoped caveat (see §Open Questions).

**Teardown, and the live configuration.** All three probe plugins were
uninstalled and the probe marketplace removed; the probe config directory then
reports `No marketplaces configured`. The live configuration was verified intact
*after* teardown, in a shell with `CLAUDE_CONFIG_DIR` unset:

```bash
unset CLAUDE_CONFIG_DIR
claude plugin marketplace list | grep -A1 sdd-commons
claude plugin list | grep -A2 "sdd@"
```

```
  ❯ sdd-commons
    Source: GitHub (jangid/sdd-commons)

  ❯ sdd@sdd-commons
    Version: 0.1.0
    Scope: user
```

`claude plugin marketplace update sdd-commons` was never run. The only
`marketplace update` invocations in this spike named `rs-pkg-002-probe`, inside
the throwaway config directory.

### Q2 — Which root is the sweep pointed at, and how is the rule data found?

**Answer: recommend (B), the explicit corpus-root / suite-root pair — and drop
the externalised rule file that option (A) presupposes, because that file is
what creates the silent-disable failure class in the first place.**

**A premise correction first, and it changes the shape of the problem.** Cycle 1
specified the rule data at `<swept root>/tools/skill-lint.rules.json`, resolved
from the swept root with no fallback. **That file does not exist:**

```bash
ls -l tools/skill-lint.rules.json
```

```
ls: tools/skill-lint.rules.json: No such file or directory
```

The suite rows are in-code module constants in `tools/skill-lint.py`, and the
linter already carries an explicit on/off for them — `Linter.__init__(self, root:
Path, suite_rules: bool = True)` at `tools/skill-lint.py:417`, checked at `:540`
(`check_required`) and `:599` (`check_template_drift`). So the rule file is a
**proposed** artifact of cycle 1's design, not an existing constraint. Both
recorded candidates inherit their framing from it, and the silent-disable failure
mode the kickoff names — a missing rule file loading zero rows — is a property
that externalisation would *introduce*. Today, a wrongly-rooted sweep fails
**loudly on the suite-gated, `skills/`-keyed rows** (see the population table
below), not silently. The scope matters: the `docs/`-keyed families *warn*
rather than fail (`tools/skill-lint.py:595`), so they are exactly the rows that
would go quiet under a plugin-root-bound linter — see §Implications.

**Which rows the `suite_rules` switch actually governs.** The switch guards
`check_required` and `check_template_drift` only, and `check_required` iterates
**three** tables, not one — the linter's own comment names them:

```
# `suite_rules=False` skips the repo-specific contract rows (REQUIRED,
# VERSION_GATED_SKILLS, V4_CONTRACT_SKILLS) so self-test fixtures can
# drive `run()` end to end without the real skill suite present.
```
(`tools/skill-lint.py:419`–`:421`; `:418` is `self.root = root`)

`VERSION_GATED_SKILLS` (9 names, `:401`) and `V4_CONTRACT_SKILLS` (7 names,
`:407`) are each resolved as `self.root / "skills" / name / "SKILL.md"` at
`:556` and `:562` (`:555` and `:561` are the `for name in …:` headers above
them) — i.e. both key on `skills/**` and both **move** with the plugin root,
exactly like `REQUIRED`.

**`FORBIDDEN` is not a suite row.** `check_forbidden` (`:521`–`:537`) has **no**
`suite_rules` guard and runs over `self.skill_files()` for every corpus, consumer
repositories included. It is generic pattern policy with no path key, hence no
root of its own at all — it inherits whichever root the corpus walk uses (§the
generic walk, below). The suite-gated population is therefore **40 + 9 + 7 = 56
rows** plus the 4 template pairs.

**The population, pinned at `c95c024`.** Derived by importing the module and
counting its tables:

```bash
python3 - <<'EOF'
import importlib.util, collections
spec = importlib.util.spec_from_file_location("sl", "tools/skill-lint.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def side(p):
    return "MOVES" if p.split("/")[0] in ("skills","agents","tools",".claude-plugin") else "STAYS"
print("REQUIRED =", len(m.REQUIRED), dict(collections.Counter(side(r["file"]) for r in m.REQUIRED)))
print("distinct REQUIRED files =", len({r["file"] for r in m.REQUIRED}))
print("VERSION_GATED_SKILLS =", len(m.VERSION_GATED_SKILLS))
print("V4_CONTRACT_SKILLS =", len(m.V4_CONTRACT_SKILLS))
print("suite-gated rows =", len(m.REQUIRED) + len(m.VERSION_GATED_SKILLS) + len(m.V4_CONTRACT_SKILLS))
print("FORBIDDEN =", len(m.FORBIDDEN), "(not suite-gated)")
print("TEMPLATE_PAIRS =", len(m.TEMPLATE_PAIRS))
print("policed areas =", len(m.RETIRED_SCOPE_DIRS) + len(m.RETIRED_SCOPE_FILES))
EOF
```

Output:

```
REQUIRED = 40 {'MOVES': 40}
distinct REQUIRED files = 10
VERSION_GATED_SKILLS = 9
V4_CONTRACT_SKILLS = 7
suite-gated rows = 56
FORBIDDEN = 13 (not suite-gated)
TEMPLATE_PAIRS = 4
policed areas = 12
```

And the size of the generic corpus walk at the same commit, from the repository
root — the count the acceptance vector pins alongside the row counts:

```bash
python3 - <<'EOF'
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("sl", "tools/skill-lint.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print("skill_files() at repo root =", len(m.Linter(Path(".").resolve()).skill_files()))
EOF
```

```
skill_files() at repo root = 25
```

The 40 contract rows resolve as `self.root / rel` (`tools/skill-lint.py:545`) and
**all forty** name files under `skills/` — ten distinct files, all of which
**move** into the plugin root. The same is true of the other two suite-gated
tables. The remaining families are genuinely split:

| Row family | Keys on | Root after the move |
|---|---|---|
| `REQUIRED` (40 rows, 10 files) | `skills/**` | **plugin** root |
| `VERSION_GATED_SKILLS` (9 rows) | `skills/<name>/SKILL.md` | **plugin** root |
| `V4_CONTRACT_SKILLS` (7 rows) | `skills/<name>/SKILL.md` | **plugin** root |
| `TEMPLATE_PAIRS` source (`TEMPLATE_SOURCE`) | `skills/orchestrate/references/dispatch-templates.md` | **plugin** root |
| `TEMPLATE_PAIRS` spec side (4 rows, 2 files) | `docs/spec/*.md` | **repo** root |
| `RETIRED_SCOPE_DIRS` (3 of 6) | `skills`, `tools`, `agents` | **plugin** root |
| `RETIRED_SCOPE_DIRS` (1 of 6) | `.claude-plugin` | **both** roots — `plugins/sdd/.claude-plugin/plugin.json` moves, `.claude-plugin/marketplace.json` stays |
| `RETIRED_SCOPE_DIRS` (2 of 6) | `docs/spec`, `docs/requirements` | **repo** root |
| `RETIRED_SCOPE_FILES` (6) | `CLAUDE.md`, `README.md`, `README.org`, `CONTRIBUTING.md`, `LICENSE`, `.pre-commit-config.yaml` | **repo** root |
| `FORBIDDEN` (13 rows) | *no path key* — pattern policy over the corpus walk | whichever root `skill_files()` uses (below) |

**Ten** row families over seven tables. Two tables spread their rows across
roots — `TEMPLATE_PAIRS` (source side vs spec side, **2** rows) and
`RETIRED_SCOPE_DIRS` (3 moving dirs, 1 dual-rooted dir, 2 staying dirs, **3**
rows) — and the remaining five tables contribute one row each: 2 + 3 + 5 = 10.
Counted by root rather than by table, **three** of the ten families are not
plugin-root-only, and one of those three — the `.claude-plugin` row — resolves
against **both** roots at once. `FORBIDDEN`, the tenth, has no path key at all.
Not in the table, because it is not a rule table, is the generic corpus walk
itself — it is treated separately below, because it is where the acceptance
vector had its blind spot.

**`.claude-plugin` is the second straddling case, and it straddles inside a
single row.** `RETIRED_SCOPE_DIRS` is
`("skills", "tools", "agents", ".claude-plugin", "docs/spec", "docs/requirements")`
(`tools/skill-lint.py:379`) and `RETIRED_SUFFIXES` includes `.json`
(`:385`), so every `.json` under a policed directory is walked for a retired
`sdd-` prefix today. `.claude-plugin/` currently holds **two** files:
`marketplace.json` and `plugin.json`. Only `plugin.json` travels with the move —
it is the `plugin.json 1` line of the carried 45-file costing — while
`.claude-plugin/marketplace.json` **stays at the repository root**, because a
marketplace entry lives in the root of the repository whose subdirectory it
sources, which is exactly the shape Q1's fixture installs from. After the move
`.claude-plugin/` therefore exists at **both** roots, with one policed `.json`
file at each.

Under option (B) as written below ("a row is resolved against exactly one root"),
`retired_scope_files()` would walk `<plugin_root>/.claude-plugin` only, and
`marketplace.json` would drop **silently** out of the retired-prefix policed
scope — the one file the move actually edits, and the one carrying the plugin
and component **names**, which is precisely where a retired `sdd-` prefix would
appear. So the retired-prefix walk is **dual-rooted**: the `.claude-plugin` row
must resolve against both roots, and option (B)'s one-row-one-root rule holds for
the other nine families only.

**No current acceptance criterion detects a wrong root binding here.** Part 3 of
the acceptance vector pins `policed_dirs`, a tuple of directory **names**, and a
name survives a wrong root binding intact — the tuple compares equal whether
`.claude-plugin` is walked from one root or from both, so part 3 cannot catch
this regression. `policed-areas=12` cannot either: it is declared **informational
output, not a criterion** (§The acceptance vector), and it too counts names. The
kind of criterion that would catch it is a **per-root policed-file count** — how
many files `retired_scope_files()` actually yields under each root, which after
the move must be non-zero at both. It is named here **as needed, PROVISIONAL**;
no form is settled and none is proposed, and it is recorded under §Open Questions
with the other unsettled criteria. A planner must not write it as an acceptance
criterion as it stands.

`TEMPLATE_PAIRS` is the sharpest case: a single rule compares a fenced block in a
file that moves against a fenced block in a file that stays. No single root can
express it. This confirms `RS-PACKAGING-001`'s "the linter needs two roots after
the move" and adds the exact split.

**What each root does today, and after the move.** `main()` resolves the root as
`Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent`,
and the pre-commit entry passes **no** argument:

```yaml
      - id: skill-lint
        name: skill linter
        entry: python3 tools/skill-lint.py
        language: system
        pass_filenames: false
        always_run: true
```

**Two hooks carry a `tools/` entry path, and the move edits both.** Alongside
`skill-lint` sits the drift sweep at `.pre-commit-config.yaml:27`–`:32`:
`- id: drift-sweep`, `name: drift sweep (fast profile)`,
`entry: python3 tools/gc.py --fast`, with the same
`language: system` / `pass_filenames: false` / `always_run: true`. `tools/gc.py`
is one of the 14 `tools/` files the carried costing moves, so its entry has to
become `python3 plugins/sdd/tools/gc.py --fast` exactly as `skill-lint`'s becomes
`python3 plugins/sdd/tools/skill-lint.py`. Only gc's **root logic** is untouched
by option (B) (§Implications); its **hook entry path** is not. Cost the move as
*two* entry edits, one per hook — an author who edits one and not the other
leaves the commit gate invoking a path that no longer exists. (No edit is made
here; this spike changes no configuration.)

So the gate's swept root is derived **from the script's own location**. After the
move that derivation silently re-points: `plugins/sdd/tools/skill-lint.py` →
`plugins/sdd/`. That is the correct root for all 56 suite-gated rows (40
`REQUIRED` + 9 `VERSION_GATED_SKILLS` + 7 `V4_CONTRACT_SKILLS`) and wrong for
every `docs/`-keyed and root-file-keyed row — and it is a change nobody
edits, which is the dangerous kind.

**Why a root decision touches the generic rules at all.** The kickoff's §Out of
scope rules out "rewriting the sweep's generic rules", and nothing below rewrites
one: `check_forbidden` and the frontmatter, name, size, ordinal and link checks
keep their rule *content* byte-for-byte. What changes is **which root their
corpus walk is anchored to** — and, as a mechanical consequence of that, **how a
swept file's repo-relative path is rendered**, which today derives from a single
`self.root` at five sites and must become relative to the root each file was
walked from (spelled out under §The rule adopted here, below; several `FORBIDDEN`
path keys depend on it). Root binding is the subject Q2 was opened to settle, and
the generic half cannot be exempted from it, because root binding is precisely
where a wrongly-rooted sweep goes silently quiet.

**Option (A) — the rule file stays at `<repo>/tools/skill-lint.rules.json`.**

- Presupposes work that does not exist: externalising the **56 suite-gated rows**
  (`REQUIRED` 40 + `VERSION_GATED_SKILLS` 9 + `V4_CONTRACT_SKILLS` 7) plus the 4
  `TEMPLATE_PAIRS` into a JSON file, with a loader and a schema — and a decision
  about the 13 `FORBIDDEN` rows, which are **not** suite-gated and would either
  have to stay in code (two rule homes) or be externalised too, changing what a
  consumer repo enforces.
- Forces `tools/` to split into a shipped subset and a dev-only subset, which
  **re-derives the carried 45/154 costing**: `tools/` contributes 14 of the 45
  moving files (`RS-PACKAGING-001`), so every tool kept back moves one file from
  the 45 column to the 154 column. The rule file itself is a *new* file in the
  154 column. The carried arithmetic `45 + 154 = 199 = git ls-files` no longer
  reconciles without restating both numbers.
- Contradicts cycle 1's own fixture placement.
- Creates the silent-disable class: a rule file resolved from the swept root with
  no fallback, missing, yields zero rows and a quiet exit 0. This is exactly the
  silent-disable failure the kickoff names as already rejected. Reinstating a fallback is not available
  — it is the fabrication bug the work exists to remove.
- Does not by itself solve `TEMPLATE_PAIRS`, which still straddles two roots.

**Option (B) — an explicit corpus-root / suite-root pair. RECOMMENDED.**

- **Zero new artifacts.** The rule data stays in `tools/skill-lint.py`, which is
  one of the 14 `tools/` files that move. The rows travel *with* the code that
  reads them, so there is no resolution step that can come up empty — the
  silent-disable class is not merely detected, it is **structurally absent**.
- **The carried 45/154 costing survives unchanged.** All of `tools/` moves; 45
  files move, 154 stay, `45 + 154 = 199 = git ls-files` at `0f5ec26` holds as
  `RS-PACKAGING-001` recorded it.
- Shape: `suite_root` defaults to `Path(__file__).resolve().parent.parent` — i.e.
  the plugin root, which after the move is *automatically* correct for the 40
  rows and needs no flag. `corpus_root` takes over today's optional positional
  `root` argument and defaults to the invocation cwd, so the pre-commit entry
  becomes `python3 plugins/sdd/tools/skill-lint.py` with still **zero**
  arguments, and a consumer repo keeps its `REPO_ROOT` positional meaning
  ("the corpus to sweep"), unchanged.
- Each row family declares which root it resolves against — a per-family
  selector on the nine **path-keyed** families above (the tenth, `FORBIDDEN`,
  has no path key and rides the corpus walk), not a fallback: a miss is a
  finding, never a silent skip. Eight of those nine resolve against exactly one
  root; the ninth, `.claude-plugin`, resolves against **both** and is the one
  documented exception (§Q2, row-family table).
- **The generic corpus walk follows `corpus_root`, with one containment rule and
  no fallback.** This has to be stated explicitly, because the bulk of the linter
  is not table-driven: `check_forbidden`, the frontmatter, name, size, ordinal
  and link checks all iterate `skill_files()`, which today is
  `(self.root / "skills").rglob("*.md")` (`tools/skill-lint.py:442`–`:444`) — 25
  files at `c95c024`. After the move this repository's `skills/` sits under the
  **plugin** root while `corpus_root` defaults to the invocation cwd (the
  **repository** root, which then has no `skills/` at all). Bind the walk to
  `suite_root` and a consumer repository's own skills stop being swept, breaking
  F11; bind it naively to `corpus_root` and *this* repository's skills stop being
  swept — a silent disable of exactly the class Q2 exists to close.

  **The rule adopted here.** The swept file set is the **set union, over resolved
  absolute paths**, of `corpus_root/skills/**` and `suite_root/skills/**`, the
  second term included only when `suite_root` is *contained within*
  `corpus_root`. **And each swept file's repo-relative path is computed against
  the root it was walked from** — not against one fixed `self.root`. This second
  sentence is not a detail: today the relative rendering is derived from the
  single `self.root` at five sites — `flag()` (`tools/skill-lint.py:433`),
  `skill_dir_of()` (`:439`, `f.relative_to(self.root / "skills")`),
  `check_forbidden()` (`:523`), `retired_scope_files()` (the retired-scope walk,
  which contributes two of the six lines, `:756` and `:760`) and
  `check_retired_prefix()` (`:772`). Five sites, six lines: the count is of
  functions, and `retired_scope_files()` renders a relative path twice.
  Under a union drawn from two *distinct* roots, `relative_to(self.root)` raises
  `ValueError` for whichever term is not under `self.root`; and the `FORBIDDEN`
  rows' `rule["files"]` substring key and the `allow_files` exact keys (e.g.
  `skills/orchestrate/SKILL.md`, `docs/requirements/traceability.md`) only match
  when the relative path was computed against the root the file was actually
  walked from. Omit this and option (B) can be implemented faithfully to every
  other sentence here and still produce code that throws. "Set union over resolved absolute paths" is load-bearing, and it
  is stated first because the **common case is the degenerate one**. A path
  contains itself, so equality counts as containment — deliberately — and the two
  roots *are* equal at all twelve existing `Linter(...)` call sites and at
  today's no-argument invocation, which is exactly what the cheap constructor
  (`Linter(root, suite_root=None)` → `suite_root or root`) produces. When
  `suite_root == corpus_root` the second term therefore names the *same* 25
  files as the first: under a set union they resolve to one set, every file is
  visited once, every finding is reported once, and the walk **degenerates to
  exactly today's single walk**. Under a naive list concatenation the same
  configuration would walk one tree twice and double every finding. One
  containment test, no fallback, no cwd sniffing.

  After the move in this repository the suite root (`<repo>/plugins/sdd`) is
  nested *strictly* inside the corpus root, so the two terms differ and their
  union is the same 25 files, swept exactly as today; in a consumer repository
  the suite root is the installed plugin cache, outside the corpus, so only the
  consumer's own skills are swept and the shipped plugin's own files are never
  linted as the consumer's. Both regressions are additionally caught by the
  files-swept count in the acceptance vector (part 1) — a count no row-count
  assertion can see. That count is a **backstop**, not the design: the union is
  specified as a set here so double-reporting is impossible by construction
  rather than merely detectable after the fact.

- **Known limit: containment is a proxy, not a proof, of "this repository's own
  suite".** The rationale above — "in a consumer repository the suite root is the
  installed plugin cache, outside the corpus" — holds only while the plugin cache
  lives outside the consumer's tree. A consumer that sets a repository-local
  `CLAUDE_CONFIG_DIR`, or vendors a copy of the plugin into its own tree, puts
  the installed plugin **inside** the corpus. The containment test then fires and
  the shipped plugin's own 25 skill files are swept as the consumer's corpus —
  precisely the outcome the rule was chosen to avoid, and directly F11-relevant.
  Option (B) is therefore recommended **with this residue**, not as a rule that
  closes both regressions with nothing left over. The requirements stage decides
  whether to accept it (the arrangement is unusual and self-inflicted) or to
  narrow the test — e.g. require the two roots to belong to the same git work
  tree, or exclude any `suite_root` lying under a plugin cache directory.

- **`corpus_root` defaulting to the invocation cwd is a deliberate behaviour
  change, stated here rather than left to be discovered.** Today `main()` derives
  the root as `Path(__file__).resolve().parent.parent`
  (`tools/skill-lint.py:1308`), which makes the swept corpus **independent of the
  directory the command is run from**. Defaulting `corpus_root` to the cwd gives
  that property up: after the move, `python3 plugins/sdd/tools/skill-lint.py` run
  from the repository root sweeps the repository, while the *same command* run
  from inside `plugins/sdd/` — or any other subdirectory — sweeps a different
  corpus, with no error and no warning. This finding **accepts** that: the cwd
  default is the only default that gives a consumer repository the meaning it
  needs ("sweep the repository I am standing in"), and the pre-commit gate, the
  only automated caller, always runs from the repository root, so the gate is
  safe by construction. A wrong cwd on a manual invocation is therefore **the
  operator's error, not a linter defect**, and no criterion is proposed for it.
  Requirements adopting option (B) must record cwd-scoping as a stated property
  of the tool; an author unwilling to accept it must instead specify an explicit
  anchor (e.g. derive `corpus_root` from `git rev-parse --show-toplevel`) and
  restate part 1 of the acceptance vector, which as written says only "from the
  repository root" and so does not pin cwd-dependence either way.
- **OPEN DECISION — option (B) flips what the suite rows mean for a consumer.**
  `suite_rules=False` is **not** a consumer-facing surface: `main()`'s argparse
  exposes only `root` and `--self-test` (`tools/skill-lint.py:1301`–`1304`), and
  `:1312` is `return Linter(root).run()` — always `suite_rules=True`. Every
  `suite_rules=False` construction in the file (`:845`, `:979`, `:1183`, `:1215`,
  `:1270`) is a **self-test fixture**. So a consumer runs today **with the suite
  rows on**, resolved against their own repository root, where the 40 `REQUIRED`
  rows flag "file missing entirely" — which is precisely why the kickoff carries
  an **amended** acceptance target (exit 0 in their own repository is
  unachievable; exit 2 is deliberate). Under option (B) the 56 suite rows resolve
  against `suite_root`, which in a consumer's install is the **installed plugin
  cache** — files that exist and pass. Option (B) therefore flips
  consumer-visible behaviour from "the suite rows fail loudly against the
  consumer's tree" to "the suite rows pass vacuously against the shipped
  plugin". That may be the wanted outcome, but it is a **design decision**, it is
  **F11-relevant**, and it is **not settled here**. Candidate remedies, named
  without choosing between them: (i) add a consumer-facing `--no-suite-rules` or
  `--suite-root` CLI surface, so the consumer decides which tree the suite rows
  judge; or (ii) decide explicitly that the suite rows now self-evaluate against
  the shipped plugin, and restate the amended acceptance target to match.
  **Requirements must not inherit "F11 untouched" as settled** (§Open
  Questions).
- Cost, honestly stated: one argparse pair, one default derivation, a root
  selector on the eight path-keyed families, the containment rule in
  `skill_files()`, and
  the `tools/skill-lint.py:381` / `:1252` `RETIRED_SCOPE_FILES` repair that is
  already queued (`Q-IMPL-MARKETPLACE-017`). One further cost, counted because
  option (A) is being priced against it: `Linter(...)` is constructed with a
  **single** root at **twelve** call sites — `:845`, `:878`, `:897`, `:907`,
  `:979`, `:1002`, `:1103`, `:1121`, `:1183`, `:1215`, `:1270`, `:1312`
  (`:907` is `Linter(root).flag(...)`; `:1312` is `main()`'s own invocation; the
  list is exhaustive at `c95c024`, from `grep -n 'Linter(' tools/skill-lint.py`)
  — so a constructor taking a *pair* touches each of them. The cheap form is a
  second parameter defaulting to the first (`Linter(root, suite_root=None)` →
  `suite_root or root`), which leaves every existing call site compiling and
  behaving as today, and only the two-distinct-root fixture in part 2 passes both.
  Note what that default implies, and what the walk rule above must therefore
  define first: at all twelve sites, and at today's no-argument invocation,
  `suite_root == corpus_root`. No new file, no new format, no loader.

**The acceptance vector that catches the silent disable.** An assertion on the
**policed count**, not on exit 0 — a criterion that only checks for silence
cannot tell "correctly quiet" from "switched off". Three parts, all run-time
decidable, modelled on the pattern the self-test already uses at block 9b
(`tools/skill-lint.py:1243`–`1284`), where the expected population is pinned as a
**literal in the fixture, independently of the constants the rule reads**, so
that gutting a constant cannot make the assertion shrink with it:

1. **Count, from the gate's own invocation.** After the move, from the
   repository root, run exactly what `.pre-commit-config.yaml` runs —
   `python3 plugins/sdd/tools/skill-lint.py` — with a population-reporting flag,
   and assert the number, not the exit code:

   **Planning note.** Part 1 **presupposes an implementation task** (a
   `Q-IMPL-…` row) that adds the `--print-population` flag; parts 2 and 3 are
   decidable against the code exactly as it stands at `c95c024`. Do not write
   part 1 as an acceptance criterion without a producing task in the plan.

   **Proposed shape, not observed output** — `--print-population` does not exist
   yet (§Open Questions). The line below is the format this vector *requires*
   the flag to emit, written so a requirements author can specify it; it has
   never been printed by anything:

   ```
   # PROPOSED — flag not implemented at c95c024; illustrative shape only
   $ cd <repo root> && python3 plugins/sdd/tools/skill-lint.py --print-population
   suite rows evaluated: REQUIRED=40 VERSION_GATED=9 V4_CONTRACT=7 TEMPLATE_PAIRS=4
   ungated rows: FORBIDDEN=13
   corpus: FILES_SWEPT=25  policed-areas=12
   ```

   **The criteria set, stated once and only here: five of the printed numbers
   are criteria — `REQUIRED=40`, `VERSION_GATED=9`, `V4_CONTRACT=7`,
   `FORBIDDEN=13`, and `FILES_SWEPT` (PROVISIONAL, form unsettled — below).
   Every other number on the line, namely `TEMPLATE_PAIRS` and `policed-areas`,
   is informational output, not a criterion.** The first three are **literals**,
   pinned at `c95c024` by the first command
   under §The population above. Pinning them as literals is sound for the same
   reason it is sound at block 9b: all three are hand-maintained **policy**
   tables that change only by deliberate decision, so a change to one is a change
   someone meant to make and should have to restate. `REQUIRED=0` with exit 0 —
   the silent disable — fails it; so does `VERSION_GATED=0` or `V4_CONTRACT=0`,
   the sixteen suite rows a `REQUIRED`-only assertion cannot see. `FORBIDDEN=13`
   is reported under a separate heading because it is **not** suite-gated and
   stays 13 in a consumer repository where every gated count is legitimately 0.

   **The fifth criterion, `FILES_SWEPT`, is PROVISIONAL — no formulation of it
   is settled here.** Its *job* is settled and is the one no row count can do: it
   must fail if the generic walk is bound to the wrong root and quietly sweeps
   zero files, and (as a consequence of the set union) it would also catch a tree
   swept twice. Its *form* is not settled: two formulations were written and both
   are defective, each recorded with its defect under §Open Questions. Settling
   the form is requirements-stage work; no third formulation is proposed here.
   **`25` is retained only as the value observed at `c95c024`** (second command
   under §The population), which is what the sample block's `FILES_SWEPT=25` line
   records — it is not a criterion.

2. **Behavioural half, per root — PROVISIONAL, and possibly unsatisfiable as
   written.** In the self-test, build a fixture whose two roots are *distinct
   directories*, seed one violation in a moving area (`skills/`, resolved against
   the suite root) and one in a staying area (`docs/spec/`, resolved against the
   corpus root), and require **one finding from each**. A single-root regression
   loses exactly one of the two, which no exit-code check would notice. That is
   the intent; the fixture as specified may not be able to express it. The defect
   and the two formulations already tried are recorded under §Open Questions; a
   planner must not treat this part as decided.

3. **Population half, pinned as literals.** Extend block 9b's tuple comparison to
   the suite rows: pin `len(REQUIRED) == 40`, `len(VERSION_GATED_SKILLS) == 9`,
   `len(V4_CONTRACT_SKILLS) == 7` and the 10 distinct `REQUIRED` files as
   literals beside the existing `policed_dirs` / `policed_files` tuples, so a row
   silently dropped during the move fails the suite by name. Pin the two
   name lists as literal tuples, not just their lengths — a renamed skill that
   drops out of `VERSION_GATED_SKILLS` keeps the length if another is added.

Together these decide, at run time, the question the kickoff says is the whole
point: the sweep is quiet **because the corpus is clean**, not because the rows
were never loaded.

**Confidence: High** on the root split, the 40/13/4/12 counts and the premise
correction (all read directly from the code at `c95c024`). **Medium** on the
option-A costing, since it prices work that has not been specified in detail.

## Implications for Design

- **The root move is unblocked.** Q1 was cycle 1's blocking, sequenced gate
  before the 45-file move. It passes on all three sub-questions, so requirements
  may now assume `git-subdir` as the mechanism rather than proposing it.
- `marketplace.json` is a **one-field** change. The 13 component lines stay as they
  are. Budget the move accordingly.
- The component list appears **not** to be an install-time guard — a stale or
  wrong list seems to fail silently rather than loudly. This bullet is inferred,
  not measured, and anything quoting it must carry that hedge rather than the
  High confidence (a) and the primary (c) observation carry (see §Q1, uncaptured
  controls). It does not change what to do: keep the manifest-vs-`README.md`
  §Components set comparison as the thing that keeps the list honest.
- **The kickoff's headline acceptance demand is blocked on a producing task.**
  The kickoff requires that "this repository's own post-move sweep, run exactly
  as the pre-commit gate runs it, must still report the full 40-row population".
  Only part 1 of the acceptance vector discharges that demand, and part 1 needs a
  `--print-population` flag that does not exist at `c95c024`. So the kickoff's
  central criterion — not merely one part of the vector — cannot be evaluated
  until an implementation task adds that flag. The requirements and plan stages
  must sequence that task **before** any criterion that quotes the 40-row
  population, and must not write the kickoff's demand as an acceptance criterion
  without it.
- **Two parts of the acceptance vector are PROVISIONAL and must not be planned as
  written** — the behavioural two-root fixture (part 2) and the `FILES_SWEPT`
  criterion; both defects, and the formulations already tried, are under §Open
  Questions. The remaining criteria — `REQUIRED=40`, `VERSION_GATED=9`,
  `V4_CONTRACT=7`, `FORBIDDEN=13`, and part 3's literal-pinned population — stand.
  `TEMPLATE_PAIRS` and `policed-areas` are informational output, not criteria.
- **Do not externalise the linter's rules.** That design is what manufactures the
  silent-disable failure mode. Requirements should carry option (B) and record
  option (A) as considered and rejected, with the reason (it creates the class it
  is trying to survive).
- The two-root pair is the same two-root concept the move already forces;
  `skills/verify/SKILL.md:169` (the queued cwd-relative drift-sweep invocation,
  sequenced *after* this decision per the kickoff) resolves the same way: a
  bundled tool copy lives under the plugin root and is pointed at the corpus root
  with an explicit `--root`, exactly as `RS-MARKETPLACE-001` settled for
  `gc.py`/`telemetry.py`.
- `tools/gc.py:1855`'s `no docs/ directory` bail sits in `main()` before `Gc(...)`
  (carried from `RS-PACKAGING-001`) and is **untouched** by option (B): the gc
  sweep keeps rooting on the corpus, and the plugin root is never passed to it.
  That bail is also the only place the kickoff's second horn exists: the
  "there is no `docs/`, so the sweep exits 2" failure belongs to `tools/gc.py`,
  **not** to `tools/skill-lint.py`, which has no `docs/` bail at all — its own
  comment at `tools/skill-lint.py:595` records the opposite expectation ("a
  consumer repo linted via `REPO_ROOT` has no `docs/spec/`", a case that warns
  rather than fails). A plugin-root-bound `skill-lint.py` would therefore go
  **silently quiet** on the `docs/`-keyed rows rather than exit 2, which is the
  same silent-disable failure the first horn describes, not a second, louder one.

## Prototype

Throwaway, under `$TMPDIR/rs-pkg-002/` — not committed, not a branch. It is a
7-file git repository plus an isolated `CLAUDE_CONFIG_DIR`. The fixture listing
above covers the **primary install only**; the two control entries (`demo2`,
`demo3`) are not reproduced in it. It demonstrates git-subdir install semantics end to end. It
does **not** prove anything about GitHub-hosted resolution, `ref`/`sha` pinning,
or update behaviour over time; and it does not execute the root move.

## Open Questions

- **`file://` vs a GitHub remote.** The probe's `url` was a `file://` path, since
  the fixture had to live under `$TMPDIR`. The CLI's own schema accepts
  `owner/repo` shorthand, `https://` and `git@` on the same field, and the clone
  path taken is identical, so the risk is low — but the GitHub-hosted shape is
  inferred, not executed. Recorded here rather than assumed away: the finding
  stays falsifiable by installing `sdd` from `jangid/sdd-commons` once the move
  lands, which the plan stage will do anyway. The registration transport is part
  of the same caveat: what was observed is a locally-added marketplace whose
  entry's `url` names the same local directory, so (b)'s High confidence must not
  be generalised to the GitHub-registered shape this repository will ship.
- **Ambiguity resolved by choice.** The kickoff frames Q2 around a rule file that
  does not exist on disk. Rather than answering a hypothetical, this spike
  answered the question the corpus actually poses — where the *in-code* rows
  resolve from — and states the premise correction explicitly, because that
  reading is falsifiable against `c95c024`.
- **`--print-population` is proposed, not present.** The acceptance vector's part
  1 names a flag the linter does not yet have, and the sample output under it is
  a **proposed format, never printed**; it is one of the small code changes
  option (B) implies. The four pinned literals themselves are measured (see §The
  population). Parts 2 and 3 need no new surface.
- **The unrun Q1(c) control.** No control declared a **real** component at a
  **non-conventional** path, so "the entry's arrays are inert" is stated here only
  in the weaker, measured form: conventional discovery happens regardless of the
  declaration, and a declaration naming an absent path neither subtracts from nor
  redirects the inventory. Whether a real component at a declared non-conventional
  path is *also* picked up is untested. The decision it feeds — leave this
  repository's 13 component lines alone — is unaffected either way, since those
  lines are already conventional and plugin-root-relative.
- **Ambiguity resolved by choice: the root of the generic walk.** Option (B)'s
  containment rule (`corpus_root/skills/**` plus `suite_root/skills/**` when the
  suite root is contained in the corpus root) was chosen over the two simple
  bindings because both simple readings silently disable a sweep — and over
  "sweep the union unconditionally", which would lint an installed plugin's own
  shipped skills as if they were a consumer's corpus. Two sub-choices are made
  explicitly rather than left open: the combination is a **set union over
  resolved absolute paths**, and **equality counts as containment**, so the
  overwhelmingly common `suite_root == corpus_root` case degenerates to exactly
  today's single 25-file walk instead of doubling it. The choice is falsifiable
  by the `FILES_SWEPT` criterion; a requirements stage preferring a different
  binding must restate that relation and say which of the two regressions it
  accepts.
- **Accepted residue: containment vs a repo-local or vendored plugin cache.** The
  containment test is a proxy for "this repository's own suite" and is wrong for
  a consumer that vendors the plugin or sets a repository-local
  `CLAUDE_CONFIG_DIR`; that consumer's sweep would lint the shipped plugin's 25
  skill files as its own corpus. Recorded as a known limit of the
  recommendation, not closed here — §Q2 names the two candidate narrowings.
- **Ambiguity resolved by choice: `corpus_root` is cwd-scoped.** Defaulting
  `corpus_root` to the invocation cwd trades away today's
  invocation-directory-independent root derivation
  (`tools/skill-lint.py:1308`). The choice is to accept it — a consumer repo
  needs "the repository I am standing in", and the only automated caller always
  runs from the repository root — and to treat a wrong cwd as operator error, so
  no criterion pins it. An alternative anchor (`git rev-parse --show-toplevel`)
  is available if the requirements stage disagrees.
- **Ambiguity resolved by choice: `FILES_SWEPT` as a relation.** The corpus-walk
  count is pinned as a comparison against the tracked file list rather than as
  the literal `25`, because `skills/**` grows by ordinary contribution and a
  literal would fire as a false positive and be edited away. `25` is kept only as
  the value observed at `c95c024`. The three row-count literals keep literal
  pinning, since they are policy populations.
- **OPEN, not decided: acceptance vector part 2 may be unsatisfiable as written.**
  Part 2 asks for a self-test fixture whose two roots are *distinct directories*,
  with "one violation in a moving area (`skills/`, resolved against the suite
  root)". But the containment rule adopted under §Q2 admits `suite_root/skills/**`
  into the corpus walk **only when `suite_root` is contained in `corpus_root`**.
  If the fixture's two roots are distinct *and disjoint*, the corpus-walk checks
  never visit `suite_root/skills/**` at all, so a `check_forbidden`- or
  frontmatter-class violation seeded there produces **no finding** and the part
  cannot pass. It works only in two configurations: the seeded violation is a
  **table-row** violation (`REQUIRED`, `VERSION_GATED_SKILLS`,
  `V4_CONTRACT_SKILLS`), which resolve `self.root / rel` directly and bypass the
  walk; or the fixture's two roots are **nested** rather than disjoint, which
  weakens what "distinct roots" demonstrates. Two formulations have been written
  and neither holds: (1) assert the sweep's **exit code / silence** across the two
  roots — rejected because a criterion that only checks for silence cannot tell
  "correctly quiet" from "switched off", which is the whole failure class Q2 was
  opened to close; (2) the distinct-directory fixture above — defective for the
  containment reason just given. **No third formulation is proposed here.**
  Choosing between "seed a table-row violation", "nest the roots", and "narrow the
  containment rule so the walk term does not depend on containment" is
  requirements-stage work, and part 2 is marked PROVISIONAL in §Q2 so no planner
  treats it as decided.
- **OPEN, not decided: the `FILES_SWEPT` criterion has no settled form.** The
  criterion's job stands — catch a generic walk bound to the wrong root that
  quietly sweeps zero files, and catch a tree swept twice — but both formulations
  written for it are defective. (1) The literal `FILES_SWEPT=25`: rejected,
  because `skill_files()` counts every `*.md` under `skills/**` and so grows by
  ordinary contribution (any skill gaining a `references/` file), making the
  literal a false positive on a correct change — and a criterion that fires
  spuriously gets edited away. (2) The relation
  `FILES_SWEPT == $(git ls-files -- ':(glob)plugins/sdd/skills/**/*.md' | wc -l)`:
  **reintroduces the same false-positive class it was chosen to avoid, and is
  repo-specific.** It compares a **working-tree** walk (`skill_files()` is
  `rglob("*.md")`) against the **tracked** file list, so any untracked or
  not-yet-added `.md` under `skills/` — an ordinary, correct working state, and
  precisely the state a pre-commit gate runs in — makes the relation fail.
  Separately it hard-codes `plugins/sdd/skills/`, so it is meaningless in a
  consumer repository, where `FILES_SWEPT` counts the consumer's own corpus and no
  such path exists. **No third formulation is proposed here.** Settling it —
  whether by comparing against a working-tree listing rather than `git ls-files`,
  by deriving the comparand from `corpus_root` rather than a fixed path, or by
  abandoning a count in favour of a different signal — is requirements-stage work,
  and the criterion is marked PROVISIONAL in §Q2.
- **OPEN, not decided: nothing detects a wrong root binding for the dual-rooted
  `.claude-plugin` row.** After the move `.claude-plugin/` exists at both roots —
  `plugin.json` under the plugin root, `marketplace.json` at the repository root —
  and a one-root binding would drop `marketplace.json` out of the retired-prefix
  scope silently (§Q2). No criterion sees that: part 3 pins `policed_dirs` as a
  tuple of directory **names**, which a wrong root binding leaves intact, and
  `policed-areas=12` is informational, not a criterion, and is likewise a count of
  names. A **per-root policed-file count** — the number of files
  `retired_scope_files()` yields under each root — is named in §Q2 as the kind of
  criterion needed and is **PROVISIONAL**: no form is settled here and no
  formulation is proposed. Settling it is requirements-stage work, alongside
  `FILES_SWEPT` and part 2.
- **OPEN, not decided: what option (B) does to F11 and the amended acceptance
  target.** `suite_rules=False` is a self-test fixture switch, not a consumer
  surface (`main()` never sets it), so a consumer runs the 56 suite rows against
  their own root today and they fail loudly by design. Under option (B) the same
  rows resolve against `suite_root` — the installed plugin cache — and pass
  vacuously. Whether that flip is wanted, and whether it is paid for with a
  `--no-suite-rules` / `--suite-root` CLI surface or adopted as the rows' new
  meaning with the amended acceptance target restated, is requirements-stage
  work. **Nothing downstream may treat the F11 principle as untouched by the root
  split.**
- **Whether `plugins/sdd/` carries its own `README`/`LICENSE`** (45 vs 47
  installed files) remains recorded, not decided — carried forward by the
  kickoff, still for the requirements stage.

## Recommended Next Step

**Proceed to requirements.** Both questions are answered: the mechanism is
proven by a real install, and the root interface has one recommended design with
both options costed. The acceptance vector is stated in run-time-decidable form
for the row-count criteria and part 3; **two of its parts arrive at requirements
open, not decided** — the behavioural two-root fixture (part 2) and the
`FILES_SWEPT` criterion, each with its defect and its already-rejected
formulations recorded under §Open Questions. Part 1 additionally waits on a
`--print-population` producing task, which carries the kickoff's headline 40-row
demand with it. The requirements stage also inherits the five carried repairs and
the two amendments listed in the kickoff.
