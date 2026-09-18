#!/usr/bin/env python3
"""Self-test for the sdd-orchestrate write-scope check.

Builds throwaway git repositories under a temporary directory and replays the
write-scope scenarios of ``docs/spec/harness-write-scope.md`` §Verification
(plan Chunk 4 task 5) plus ``docs/spec/telemetry.md`` §Third Observation (F7),
``docs/spec/arbitrated-handoff.md`` §Section Resolution (F8) and
``docs/spec/dispatch-snapshot-base.md`` §Snapshot Base Rule (F9) and
``docs/spec/harness-write-scope.md`` §Content-Hash Observation (F10),
§Specs Row Names the Per-Workstream Traceability Path (F11) and
``docs/spec/ws-traceability.md`` §Aggregate Regeneration Ownership (F12) against the
observation procedure defined in ``skills/sdd-orchestrate/references/write-scope.md``:

  §3  the three commands — porcelain delta, committed delta, ancestry check —
      plus the content-hash observation (already-dirty paths), the named-base
      catch-up (d) and its ``CATCH-UP`` line (remedy (ii))
      and the section resolution of fix hunks (hunk -> enclosing ``§Name``)
  §4  matching and tags — IN / ADVISORY / OUT
  §5  finding format and the own-line ``SCOPE:`` token
  §6  blocked-write fallback — pre-persist scope match
  telemetry.md §4  third observation of ``.sdd/`` and the leaf-write revert

Scenarios (ids match the traceability Test cells for REQ-HARN-020..026):

  F1  porcelain-only OUT, uncommitted           -> SCOPE: VIOLATION (1 path)
  F2  committed OUT with a clean porcelain      -> SCOPE: VIOLATION (1 path)
  F3  verify writes verification + traceability -> both IN, SCOPE: CLEAN
  F4  implement writes docs/spec/recon.md       -> ADVISORY, SCOPE: CLEAN
  F5  blocked_writes docs/plan.md from a leaf   -> refused, listed OUT refused
  F6  amended HEAD                              -> HISTORY_REWRITE, VIOLATION
  F7  leaf appends to .sdd/telemetry.jsonl      -> OUT (+1 records, leaf write — reverted)
  F8  section resolution (L40-58 under ## A,   -> {x.md:§A, x.md:§C}; untracked -> (path, *);
      L120 under ## C of docs/spec/x.md)           .py -> (path, ?)
  F9  catch-up base (worktree 1 commit behind)  -> CLEAN + CATCH-UP line; plus one
                                                   OUT write -> VIOLATION (1 path)
  F10 already-dirty path re-touched by the leaf -> OUT (content delta) -> VIOLATION
      (1 path); the same fixture untouched         (1 path); untouched -> SCOPE: CLEAN
  F11 marker-4 specs dispatch: docs/spec/** +   -> both IN, SCOPE: CLEAN
      docs/ws/<id>/traceability.md row
  F12 marker-4 verify dispatch also writes      -> OUT the aggregate,
      docs/requirements/traceability.md            SCOPE: VIOLATION (1 path)

Usage:
    python3 tools/sdd-scope-check-selftest.py [-v] [--keep]

Prints one PASS/FAIL line per scenario. Exit 0 when every scenario passes,
1 otherwise. Requires only the Python standard library and a ``git`` binary.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Iterable

# ---------------------------------------------------------------------------
# git plumbing
# ---------------------------------------------------------------------------

# Identity and safety flags for every git call: no global hooks, no signing,
# a fixed author so the fixture repos are reproducible anywhere.
GIT_BASE = [
    "git",
    "-c", "user.email=selftest@example.invalid",
    "-c", "user.name=scope-selftest",
    "-c", "commit.gpgsign=false",
    "-c", "core.hooksPath=/dev/null",
    "-c", "init.defaultBranch=main",
]


def git(repo: str, *args: str, check: bool = True, stdin: str | None = None) -> subprocess.CompletedProcess:
    """Run a git command inside ``repo`` and return the completed process.

    ``stdin`` feeds the command's standard input (used by ``hash-object
    --stdin-paths`` for the content-hash observation).
    """
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(
        GIT_BASE + list(args),
        cwd=repo,
        env=env,
        input=stdin,
        text=True,
        capture_output=True,
        check=check,
    )


def write(repo: str, rel: str, content: str) -> None:
    """Create or overwrite ``rel`` under ``repo``, creating parent dirs."""
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def make_repo(root: str, name: str) -> str:
    """Create a fixture repo with one commit and pre-existing untracked noise.

    The tracked tree mirrors the paths the scenarios touch. ``.claude/worktrees/``
    is left untracked in *both* snapshots so the noise-cancellation rule of §3
    is exercised by every scenario, not just F1.
    """
    repo = os.path.join(root, name)
    os.makedirs(repo)
    git(repo, "init", "-q")
    for rel, body in {
        "src/a.py": "x = 1\n",
        "src/recon/engine.py": "def run():\n    return 0\n",
        "tests/test_recon.py": "def test_run():\n    assert True\n",
        "docs/plan.md": "# Plan\n",
        "docs/spec/recon.md": "# Recon\n\n## Implementation Questions\n",
        "docs/verification.md": "# Verification\n",
        "docs/requirements/traceability.md": "| REQ | Spec |\n",
        "docs/ws/harness/traceability.md": "| REQ | Spec | Workstream |\n",
        "docs/ws/harness/verification.md": "# Verification\n",
    }.items():
        write(repo, rel, body)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    # Pre-existing untracked noise, present before and after the dispatch.
    write(repo, ".claude/worktrees/leaf/.keep", "")
    return repo


# ---------------------------------------------------------------------------
# write-scope.md §3 — the three commands
# ---------------------------------------------------------------------------


def snapshot(repo: str) -> list[str]:
    """``git status --porcelain=v1 -z --untracked-files=all`` as a list of records.

    ``-z`` (§3 content-hash observation) so a path containing a space, a quote
    or a newline is never mangled or shell-quoted: fields are NUL-separated and
    a rename/copy record is followed by a second field carrying its original
    path. Such a record is rejoined here as ``XY new\0orig`` so that one record
    stays one comparable string for the cancel rule, while ``_porcelain_paths``
    still yields **both** of its paths.
    """
    out = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    fields = out.split("\0")
    records: list[str] = []
    i = 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if not entry:
            continue
        xy = entry[:2]
        if ("R" in xy or "C" in xy) and i < len(fields):
            records.append(entry + "\0" + fields[i])  # XY new\0orig
            i += 1
        else:
            records.append(entry)
    return records


@dataclass
class Observed:
    """One observed write: path, porcelain/diff status letter, provenance label."""

    path: str
    letter: str
    where: str  # "uncommitted" or "committed <sha>"


@dataclass
class Observation:
    writes: list[Observed] = field(default_factory=list)
    history_rewrite: str | None = None  # rendered HISTORY_REWRITE line, if any
    catch_up: str | None = None  # rendered CATCH-UP note for the header line, if any
    # Third observation (telemetry.md §4): finding strings for leaf writes under
    # the gitignored ``.sdd/`` — each counts as one more OUT path.
    telemetry_findings: list[str] = field(default_factory=list)
    telemetry_after: "TelemetrySnapshot | None" = None


# ---------------------------------------------------------------------------
# telemetry.md §4 — third observation of .sdd/ (gitignored, invisible to §3)
# ---------------------------------------------------------------------------

TELEMETRY_DIR = ".sdd"
TELEMETRY_FILE = ".sdd/telemetry.jsonl"


@dataclass(frozen=True)
class TelemetrySnapshot:
    """``n`` = line count of .sdd/telemetry.jsonl (0 if absent); ``entries`` = sorted .sdd/ listing."""

    n: int
    entries: tuple[str, ...]


def telemetry_snapshot(repo: str) -> TelemetrySnapshot:
    """Take ``n_before``/``e_before`` (or the ``after`` pair) per telemetry.md §4."""
    d = os.path.join(repo, TELEMETRY_DIR)
    f = os.path.join(repo, TELEMETRY_FILE)
    entries = tuple(sorted(os.listdir(d))) if os.path.isdir(d) else ()
    n = 0
    if os.path.isfile(f):
        with open(f, "rb") as fh:
            n = sum(1 for _ in fh)
    return TelemetrySnapshot(n, entries)


def telemetry_delta(before: TelemetrySnapshot, after: TelemetrySnapshot) -> list[str]:
    """Render the telemetry.md §4 finding strings for any leaf write under .sdd/.

    The strings are defined once in ``skills/sdd-orchestrate/references/telemetry.md``
    §4 and mirrored here verbatim; nothing else in the harness restates them.
    """
    findings: list[str] = []
    if after.n > before.n:
        findings.append(f"OUT {TELEMETRY_FILE} (+{after.n - before.n} records, leaf write — reverted)")
    elif after.n < before.n:
        findings.append(f"OUT {TELEMETRY_FILE} (−{before.n - after.n} records, leaf write — unrecoverable)")
    for entry in sorted(set(after.entries) ^ set(before.entries)):
        if f"{TELEMETRY_DIR}/{entry}" == TELEMETRY_FILE and after.n != before.n:
            continue  # already reported by the record-count line above
        findings.append(f"OUT {TELEMETRY_DIR}/{entry} (leaf write — reverted)")
    return findings


def revert_telemetry(repo: str, before: TelemetrySnapshot, obs: "Observation") -> None:
    """Revert leaf writes under .sdd/ before the gate (telemetry.md §4).

    Truncates the telemetry file back to ``n_before`` lines — the single
    exception to the never-truncate rule — and removes entries the leaf added.
    Lines a leaf removed cannot be restored (reported as unrecoverable).
    """
    if not obs.telemetry_findings or obs.telemetry_after is None:
        return
    f = os.path.join(repo, TELEMETRY_FILE)
    if obs.telemetry_after.n > before.n and os.path.isfile(f):
        with open(f, "rb") as fh:
            kept = fh.readlines()[: before.n]
        with open(f, "wb") as fh:
            fh.writelines(kept)
    for entry in set(obs.telemetry_after.entries) - set(before.entries):
        path = os.path.join(repo, TELEMETRY_DIR, entry)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)


def _porcelain_paths(line: str) -> tuple[str, list[str]]:
    """Split a porcelain v1 line into its status letter and path(s).

    ``XY path``; a ``-z`` rename/copy record is ``XY new\0orig`` and the legacy
    non-``-z`` form is ``XY old -> new``. Both sides of a rename or copy are
    returned, so both enter the observed set and the ambiguous set (§3).
    """
    letter = (line[:2].strip() or "?")[0]
    rest = line[3:]
    if "\0" in rest:
        new, orig = rest.split("\0", 1)
        return letter, [orig, new]
    if " -> " in rest:
        old, new = rest.split(" -> ", 1)
        return letter, [old, new]
    return letter, [rest]


# ---------------------------------------------------------------------------
# write-scope.md §3 — content-hash observation (already-dirty paths)
# ---------------------------------------------------------------------------

# Reserved non-hash sentinel for a path absent from the worktree
# (Q-IMPL-HARNESSP3-002): it cannot collide with a hex digest, so the
# comparison stays a plain inequality and needs no separate presence set.
ABSENT = "ABSENT"


def ambiguous_set(records: Iterable[str]) -> list[str]:
    """Paths listed as dirty or untracked by ``snapshot(before)`` — both sides of an R/C record.

    The set is fixed *before* the dispatch, which is what bounds the cost of the
    content-hash observation to O(dirty files) rather than O(repo).
    """
    paths: list[str] = []
    for record in records:
        _letter, record_paths = _porcelain_paths(record)
        for p in record_paths:
            if p not in paths:
                paths.append(p)
    return paths


def content_hashes(repo: str, paths: Iterable[str]) -> dict[str, str]:
    """``{path: content_hash}`` over **working-tree** content (Q-IMPL-HARNESSP3-001).

    ``git hash-object --stdin-paths`` so the value is git's own blob identity and
    no second hashing dependency is needed; the contract is the ``(path, sha)``
    pair set, so any hash is conforming as long as the same one is used for the
    before and after snapshot of a dispatch. A path that is not a file in the
    worktree records the ``ABSENT`` sentinel.
    """
    paths = list(paths)
    hashes = {p: ABSENT for p in paths}
    present = [p for p in paths if os.path.isfile(os.path.join(repo, p))]
    if present:
        out = git(repo, "hash-object", "--stdin-paths", stdin="\n".join(present) + "\n").stdout.split()
        for p, sha in zip(present, out):
            hashes[p] = sha
    return hashes


def _add_name_status(obs: Observation, text: str, sha: str) -> None:
    """Append every path of a ``--name-status`` listing as a committed write."""
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        letter = parts[0][0]
        paths = parts[1:]  # renames/copies carry old and new
        for p in paths:
            obs.writes.append(Observed(p, letter, f"committed {sha[:7]}"))


def observe(
    repo: str,
    head_before: str,
    before: list[str],
    telemetry_before: TelemetrySnapshot | None = None,
    *,
    base: str | None = None,
    content_before: dict[str, str] | None = None,
) -> Observation:
    """Run the AFTER half of §3 and return the union of the two deltas.

    (a) porcelain delta: lines in scope.after that are not in scope.before
    (b) committed delta: ``git diff --name-status HEAD_before HEAD_after``; under a
        named base, the paths of every commit in ``git rev-list HEAD_after ^base ^HEAD_prov``
    (c) ancestry: ``git merge-base --is-ancestor HEAD_before HEAD_after``
    content delta: with ``content_before`` (the ``(path, sha)`` pairs of the ambiguous
        set, taken pre-dispatch), every ambiguous path whose working-tree hash changed
        — the term that sees a path already dirty at snapshot time and written again,
        which the porcelain cancel rule would otherwise drop
    (d) catch-up: ``N = git rev-list --count HEAD_prov..base``; ``N > 0`` renders the
        ``CATCH-UP <from>..<base> (N commits, excluded — base <sha>)`` note
    Third observation (telemetry.md §4), when ``telemetry_before`` is given:
    ``n_after``/``e_after`` of .sdd/ taken here, before the orchestrator's own append.

    ``head_before`` is the provisioned HEAD (``HEAD_prov``). ``base`` is the commit
    the leaf was told to reach (remedy (ii) of the snapshot base rule); when it
    is given and resolves, the effective ``HEAD_before`` becomes ``base`` and the
    catch-up commits are excluded from the window. With ``N == 0`` the plain
    three-command path runs, so the rendering is byte-identical to v5.
    """
    head_after = git(repo, "rev-parse", "HEAD").stdout.strip()
    after = snapshot(repo)
    obs = Observation()
    head_prov = head_before

    # (d) catch-up — resolve the named base and pick the effective HEAD_before.
    if base is not None:
        count = git(repo, "rev-list", "--count", f"{head_prov}..{base}", check=False)
        if count.returncode != 0:
            # Named base not reachable (typo): window from HEAD_prov, no exclusion.
            obs.catch_up = f"CATCH-UP base {base[:7]} unresolved — window from {head_prov[:7]}"
            base = None
        else:
            base = git(repo, "rev-parse", base).stdout.strip()
            base_reached = git(repo, "merge-base", "--is-ancestor", base, head_after, check=False).returncode == 0
            prov_reached = git(repo, "merge-base", "--is-ancestor", head_prov, head_after, check=False).returncode == 0
            n = int(count.stdout.strip())
            if not base_reached and prov_reached:
                # Leaf ignored the catch-up instruction: a warning, not a violation.
                obs.catch_up = f"CATCH-UP not performed (base {base[:7]})"
                base = None
            elif n == 0:
                base = None  # remedy (i) in effect — nothing to exclude
            else:
                obs.catch_up = (
                    f"CATCH-UP {head_prov[:7]}..{base[:7]} ({n} commits, excluded — base {base[:7]})"
                )
                head_before = base
    if telemetry_before is not None:
        obs.telemetry_after = telemetry_snapshot(repo)
        obs.telemetry_findings = telemetry_delta(telemetry_before, obs.telemetry_after)

    # (a) porcelain delta — paths present in both snapshots cancel.
    before_set = set(before)
    for line in after:
        if line in before_set:
            continue
        letter, paths = _porcelain_paths(line)
        for p in paths:
            obs.writes.append(Observed(p, letter, "uncommitted"))

    # Content delta — the cancel rule above is amended: a path present in both
    # snapshots cancels only when its content hash is also unchanged. sha.after
    # is taken over ambiguous_set INTERSECT snapshot(after), plus the ABSENT
    # sentinel for a path deleted during the dispatch (itself a content change).
    if content_before:
        after_paths = set(ambiguous_set(after))
        seen = {w.path for w in obs.writes}
        letters = {}
        for line in after:
            letter, paths = _porcelain_paths(line)
            for p in paths:
                letters.setdefault(p, letter)
        for p, sha_before in content_before.items():
            if p in seen:
                continue  # already observed by (a) or (b)
            on_disk = os.path.isfile(os.path.join(repo, p))
            if not on_disk:
                sha_after = ABSENT
            elif p in after_paths:
                sha_after = content_hashes(repo, [p])[p]
            else:
                continue  # no longer dirty: the reverted/committed round trip of §5
            if sha_after != sha_before:
                obs.writes.append(Observed(p, "D" if sha_after == ABSENT else letters.get(p, "M"), "uncommitted"))

    # (b) committed delta — catches writes that vanished from porcelain.
    if head_after != head_before:
        if base is not None:
            # Named base: only the commits the leaf added on top of base and
            # HEAD_prov, each contributing its own paths (a merge commit only
            # its conflict resolutions — combined diff).
            shas = git(repo, "rev-list", head_after, f"^{base}", f"^{head_prov}").stdout.split()
            for sha in reversed(shas):
                _add_name_status(obs, git(repo, "show", "--name-status", "--format=", sha).stdout, sha)
        else:
            _add_name_status(obs, git(repo, "diff", "--name-status", head_before, head_after).stdout, head_after)

    # (c) ancestry — a non-zero exit is a HISTORY_REWRITE finding.
    rc = git(repo, "merge-base", "--is-ancestor", head_before, head_after, check=False).returncode
    if rc != 0:
        obs.history_rewrite = (
            f"HISTORY_REWRITE  HEAD_after {head_after[:7]} does not descend "
            f"from HEAD_before {head_before[:7]}"
        )
    return obs


# ---------------------------------------------------------------------------
# write-scope.md §3 — section resolution of fix hunks (arbitrated-handoff.md)
# ---------------------------------------------------------------------------

HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
MARKDOWN_SUFFIXES = (".md", ".markdown")


def section_name(heading: str) -> str:
    """Normalise a heading line to ``§Name`` as loop-control.md §2a does for review keys.

    Leading ``#``s and a leading ordinal (``3.``, ``3)``, ``3``) are stripped,
    whitespace is collapsed, case is kept — so ``## 3. Foo`` and ``§Foo`` compare equal.
    """
    text = heading.lstrip("#").strip()
    text = re.sub(r"^\d+[.)]?\s*", "", text)
    return "§" + " ".join(text.split())


def _headings(lines: list[str]) -> list[tuple[int, str]]:
    """``(line number, §Name)`` for every ``#``-heading, 1-based, in file order."""
    return [(i, section_name(ln)) for i, ln in enumerate(lines, start=1) if ln.startswith("#")]


def _hunk_ranges(diff_text: str) -> list[tuple[int, int]]:
    """After-image ``(start, end)`` line pairs for every ``@@ -a,b +c,d @@`` header.

    A missing count means 1; a pure deletion (``d == 0``) keeps ``c`` as both ends.
    """
    ranges: list[tuple[int, int]] = []
    for line in diff_text.splitlines():
        m = HUNK_HEADER.match(line)
        if not m:
            continue
        c = int(m.group(3))
        d = int(m.group(4)) if m.group(4) is not None else 1
        ranges.append((c, c + d - 1 if d > 0 else c))
    return ranges


def resolve_sections(
    repo: str, path: str, head_before: str, head_after: str
) -> tuple[set[tuple[str, str]], dict[tuple[str, str], str]]:
    """Resolve a written path's hunks to ``(path, §Name)`` pairs per write-scope.md §3.

    committed  : ``git diff -U0 HEAD_before HEAD_after -- path`` against ``git show HEAD_after:path``
    uncommitted: ``git diff -U0 HEAD_after -- path`` against the working file
    untracked  : ``(path, *)`` — a new file is written in full
    non-Markdown: ``(path, ?)`` — falls back to file-level comparison

    Each hunk's after-image start line ``c`` resolves to the nearest ``#``-heading
    at or above it; a hunk above the first heading resolves to ``§(preamble)``.
    Returns the pair set and, per pair, the rendered hunk ranges (``L40-58, L120``).
    """
    if not path.endswith(MARKDOWN_SUFFIXES):
        return {(path, "?")}, {}
    tracked = git(repo, "ls-files", "--error-unmatch", path, check=False).returncode == 0
    if not tracked:
        return {(path, "*")}, {}

    sections: set[tuple[str, str]] = set()
    hunks: dict[tuple[str, str], list[str]] = {}

    def resolve(diff_text: str, after_lines: list[str]) -> None:
        heads = _headings(after_lines)
        for start, end in _hunk_ranges(diff_text):
            name = "§(preamble)"
            for line_no, sec in heads:
                if line_no <= start:
                    name = sec
                else:
                    break
            key = (path, name)
            sections.add(key)
            hunks.setdefault(key, []).append(f"L{start}" if start == end else f"L{start}-{end}")

    # committed hunks, read against the after-image at HEAD_after
    if head_before != head_after:
        diff = git(repo, "diff", "-U0", head_before, head_after, "--", path).stdout
        shown = git(repo, "show", f"{head_after}:{path}", check=False)
        if diff and shown.returncode == 0:
            resolve(diff, shown.stdout.splitlines())
    # uncommitted hunks (porcelain-only writes), read against the working file
    diff = git(repo, "diff", "-U0", head_after, "--", path).stdout
    if diff:
        with open(os.path.join(repo, path), encoding="utf-8") as fh:
            resolve(diff, fh.read().splitlines())
    return sections, {k: ", ".join(v) for k, v in hunks.items()}


# ---------------------------------------------------------------------------
# write-scope.md §4 — matching and tags
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScopeGlob:
    pattern: str
    advisory: bool = False


def glob_to_regex(glob: str) -> re.Pattern:
    """Translate a write-scope glob to a regex per §1 semantics.

    ``**`` matches any depth (including none), ``*`` matches within a single
    path segment, and an exact file path matches only that file. ``fnmatch`` is
    deliberately not used: its ``*`` crosses ``/`` and would over-match.
    """
    out = []
    i = 0
    while i < len(glob):
        ch = glob[i]
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif ch == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(ch))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def tag(path: str, scope: Iterable[ScopeGlob]) -> str:
    """Return ``IN``, ``ADVISORY`` or ``OUT`` for one observed path."""
    for g in scope:
        if glob_to_regex(g.pattern).match(path):
            return "ADVISORY" if g.advisory else "IN"
    return "OUT"


# ---------------------------------------------------------------------------
# write-scope.md §5 — finding block and SCOPE: token
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    lines: list[str]
    token: str
    out_paths: list[str]


def render(scope: list[ScopeGlob], obs: Observation, label: str) -> Finding:
    """Render the §5 finding block and compute the own-line ``SCOPE:`` token."""
    declared = ", ".join(g.pattern + (" (advisory)" if g.advisory else "") for g in scope)
    lines = [f"Write-scope check — {label}", f"  Declared scope : {declared}"]
    # The "Observed writes" header carries the CATCH-UP note under remedy (ii);
    # it is omitted entirely when there is none so the v5 rendering is unchanged.
    if obs.catch_up:
        lines.append(f"  Observed writes: {obs.catch_up}")
    if obs.history_rewrite:
        lines.append(f"  {obs.history_rewrite}")
    out_paths: list[str] = []
    for w in obs.writes:
        t = tag(w.path, scope)
        suffix = ""
        if t == "OUT":
            out_paths.append(w.path)
            suffix = "  <- boundary finding"
        elif t == "ADVISORY":
            suffix = "  (verify hunks are under ## Implementation Questions)"
        lines.append(f"    {t:<9}{w.path:<38}{w.letter}  {w.where}{suffix}")
    # Third observation: each telemetry finding is one more OUT path (telemetry.md §4).
    for finding in obs.telemetry_findings:
        out_paths.append(finding.split()[1])
        lines.append(f"    {finding}")
    # N counts OUT paths plus a HISTORY_REWRITE finding; ADVISORY never counts.
    n = len(out_paths) + (1 if obs.history_rewrite else 0)
    token = "SCOPE: CLEAN" if n == 0 else f"SCOPE: VIOLATION ({n} path{'s' if n != 1 else ''})"
    lines.append(f"  {token}")
    return Finding(lines, token, out_paths)


# ---------------------------------------------------------------------------
# write-scope.md §6 — blocked-write pre-persist match
# ---------------------------------------------------------------------------


def persist_blocked_writes(
    repo: str, scope: list[ScopeGlob], entries: list[dict]
) -> tuple[list[str], list[str]]:
    """Scope-match each ``blocked_writes`` entry before persisting it.

    Returns ``(finding_lines, refused_paths)``. ``IN``/``ADVISORY`` entries are
    written to disk; ``OUT`` entries are never written and are listed as
    ``OUT <path>  blocked-write  <- refused``.
    """
    lines: list[str] = []
    refused: list[str] = []
    for e in entries:
        t = tag(e["path"], scope)
        if t == "OUT":
            refused.append(e["path"])
            lines.append(f"    OUT       {e['path']}  blocked-write  <- refused")
        else:
            write(repo, e["path"], e["content"])
            lines.append(f"    {t:<9}{e['path']}  blocked-write  persisted by orchestrator")
    return lines, refused


# ---------------------------------------------------------------------------
# scenarios
# ---------------------------------------------------------------------------

SEQ_SCOPE_SRC = [ScopeGlob("src/**")]
SPEC_SCOPE = [ScopeGlob("docs/spec/**")]
VERIFY_SCOPE = [ScopeGlob("docs/verification.md"), ScopeGlob("docs/requirements/traceability.md")]
IMPLEMENT_SCOPE = [
    ScopeGlob("src/recon/**"),
    ScopeGlob("tests/test_recon.py"),
    ScopeGlob("docs/plan.md"),
    ScopeGlob("docs/requirements/traceability.md"),
    ScopeGlob("docs/spec/*.md", advisory=True),
]
LEAF_SCOPE = [ScopeGlob("src/recon/**"), ScopeGlob("tests/test_recon.py")]
# Marker-4 orchestrated scopes: the shared aggregate docs/requirements/traceability.md
# is absent by construction (write-scope.md §2, REQ-WS-HARNESSP3-001).
SPECS_WS4_SCOPE = [ScopeGlob("docs/spec/**"), ScopeGlob("docs/ws/harness/traceability.md")]
VERIFY_WS4_SCOPE = [
    ScopeGlob("docs/ws/harness/verification.md"),
    ScopeGlob("docs/ws/harness/traceability.md"),
]


def _begin(repo: str) -> tuple[str, list[str], dict[str, str]]:
    """The BEFORE half of §3, immediately pre-dispatch.

    HEAD, the porcelain snapshot and the ``(path, sha)`` pairs of the ambiguous
    set (the content-hash observation's ``sha.before``).
    """
    before = snapshot(repo)
    return (
        git(repo, "rev-parse", "HEAD").stdout.strip(),
        before,
        content_hashes(repo, ambiguous_set(before)),
    )


def scenario_f1(repo: str) -> tuple[bool, str, list[str]]:
    """Porcelain-only OUT: uncommitted docs/plan.md edit against scope src/**."""
    head, before, content_before = _begin(repo)
    write(repo, "docs/plan.md", "# Plan\nleaf edit\n")
    f = render(SEQ_SCOPE_SRC, observe(repo, head, before, content_before=content_before), "F1")
    ok = (
        f.token == "SCOPE: VIOLATION (1 path)"
        and f.out_paths == ["docs/plan.md"]
        and any("OUT" in ln and "docs/plan.md" in ln and "uncommitted" in ln for ln in f.lines)
        and not any(".claude/worktrees" in ln for ln in f.lines)  # noise cancelled
    )
    return ok, f.token, f.lines


def scenario_f2(repo: str) -> tuple[bool, str, list[str]]:
    """Committed OUT with clean porcelain: docs/plan.md committed, scope docs/spec/**."""
    head, before, content_before = _begin(repo)
    write(repo, "docs/plan.md", "# Plan\nleaf edit, committed\n")
    git(repo, "commit", "-q", "-am", "leaf: plan edit")
    obs = observe(repo, head, before, content_before=content_before)
    porcelain_clean = not any(w.where == "uncommitted" for w in obs.writes)
    f = render(SPEC_SCOPE, obs, "F2")
    ok = (
        porcelain_clean
        and f.token == "SCOPE: VIOLATION (1 path)"
        and f.out_paths == ["docs/plan.md"]
        and any("OUT" in ln and "docs/plan.md" in ln and "committed" in ln for ln in f.lines)
    )
    return ok, f.token, f.lines


def scenario_f3(repo: str) -> tuple[bool, str, list[str]]:
    """Verify dispatch writes verification.md + traceability.md: both IN, CLEAN."""
    head, before, content_before = _begin(repo)
    write(repo, "docs/verification.md", "# Verification\nstatus: pass\n")
    write(repo, "docs/requirements/traceability.md", "| REQ | Spec | Verified |\n")
    f = render(VERIFY_SCOPE, observe(repo, head, before, content_before=content_before), "F3")
    tags = [ln.split()[0] for ln in f.lines if ln.startswith("    ")]
    ok = f.token == "SCOPE: CLEAN" and tags == ["IN", "IN"]
    return ok, f.token, f.lines


def scenario_f4(repo: str) -> tuple[bool, str, list[str]]:
    """Implement dispatch writes docs/spec/recon.md: ADVISORY, CLEAN."""
    head, before, content_before = _begin(repo)
    write(repo, "docs/spec/recon.md", "# Recon\n\n## Implementation Questions\n### Q-IMPL-001: x\n")
    f = render(IMPLEMENT_SCOPE, observe(repo, head, before, content_before=content_before), "F4")
    tags = [ln.split()[0] for ln in f.lines if ln.startswith("    ")]
    ok = f.token == "SCOPE: CLEAN" and tags == ["ADVISORY"]
    return ok, f.token, f.lines


def scenario_f5(repo: str) -> tuple[bool, str, list[str]]:
    """Fan-out leaf returns blocked_writes for docs/plan.md: refused, not persisted."""
    original = open(os.path.join(repo, "docs/plan.md"), encoding="utf-8").read()
    lines, refused = persist_blocked_writes(
        repo, LEAF_SCOPE, [{"path": "docs/plan.md", "content": "# Plan\nleaf wants this\n"}]
    )
    unchanged = open(os.path.join(repo, "docs/plan.md"), encoding="utf-8").read() == original
    listed = any(ln.strip() == "OUT       docs/plan.md  blocked-write  <- refused" for ln in lines)
    ok = refused == ["docs/plan.md"] and unchanged and listed
    return ok, "refused" if refused else "persisted", lines


def scenario_f6(repo: str) -> tuple[bool, str, list[str]]:
    """Amended HEAD: HEAD_after does not descend from HEAD_before -> HISTORY_REWRITE."""
    head, before, content_before = _begin(repo)
    git(repo, "commit", "-q", "--amend", "--allow-empty", "-m", "base (amended by leaf)")
    obs = observe(repo, head, before, content_before=content_before)
    f = render(SEQ_SCOPE_SRC, obs, "F6")
    ok = (
        obs.history_rewrite is not None
        and f.token.startswith("SCOPE: VIOLATION")
        and any(ln.strip().startswith("HISTORY_REWRITE") for ln in f.lines)
    )
    return ok, f.token, f.lines


def scenario_f7(repo: str) -> tuple[bool, str, list[str]]:
    """Leaf appends one line to the gitignored .sdd/telemetry.jsonl.

    telemetry.md §4: porcelain cannot see the write (limitation (b)), so the
    third observation must flag it as ``OUT .sdd/telemetry.jsonl (+1 records,
    leaf write — reverted)``, count it in ``SCOPE: VIOLATION (1 paths)`` and
    truncate the file back to ``n_before`` lines before the gate.
    """
    write(repo, ".gitignore", ".sdd/\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-q", "-m", "gitignore .sdd/")
    n_before = 3
    write(repo, ".sdd/telemetry.jsonl", "".join(f'{{"v":1,"seq":{i}}}\n' for i in range(1, n_before + 1)))
    ignored = git(repo, "check-ignore", "-q", ".sdd/telemetry.jsonl", check=False).returncode == 0
    head, before, content_before = _begin(repo)
    tele_before = telemetry_snapshot(repo)
    # the leaf appends one record
    with open(os.path.join(repo, ".sdd/telemetry.jsonl"), "a", encoding="utf-8") as fh:
        fh.write('{"v":1,"seq":99,"leaf":true}\n')
    obs = observe(repo, head, before, tele_before, content_before=content_before)
    revert_telemetry(repo, tele_before, obs)  # before the gate, like the verifier revert
    f = render(SEQ_SCOPE_SRC, obs, "F7")
    with open(os.path.join(repo, ".sdd/telemetry.jsonl"), encoding="utf-8") as fh:
        n_after_revert = sum(1 for _ in fh)
    expected = "OUT .sdd/telemetry.jsonl (+1 records, leaf write — reverted)"
    ok = (
        ignored
        and f.token == "SCOPE: VIOLATION (1 path)"
        and f.out_paths == [".sdd/telemetry.jsonl"]
        and any(ln.strip() == expected for ln in f.lines)
        and n_after_revert == n_before
        and not any(w.path.startswith(".sdd/") for w in obs.writes)  # invisible to porcelain
    )
    return ok, f.token, f.lines


def scenario_f9(repo: str) -> tuple[bool, str, list[str]]:
    """Catch-up base: worktree provisioned one commit behind the named base.

    Self-contained replay of ``dispatch-snapshot-base.md`` §Snapshot Base Rule
    (F9) with three assertions:

      1. leaf fast-forwards to the named base and commits one in-scope write
         -> SCOPE: CLEAN, the CATCH-UP <from>..<base> (1 commits, excluded — base
         <sha>) note in the "Observed writes" header, the tip's out-of-scope
         path NOT listed;
      2. plus one uncommitted out-of-scope write -> SCOPE: VIOLATION (1 path)
         naming only that path, the CATCH-UP note still present;
      3. N == 0 (base == HEAD_prov) -> no CATCH-UP line; the block is
         byte-identical to the plain three-command rendering (the F1 shape).
    """
    head_prov = git(repo, "rev-parse", "HEAD").stdout.strip()
    # The branch moves on after the worktree's base: one commit touching an
    # out-of-scope path (RS-HARNESSP2-001 Q6's 20-path delta, in miniature).
    write(repo, "docs/plan.md", "# Plan\ntip commit, authored before dispatch\n")
    git(repo, "commit", "-q", "-am", "tip: plan edit")
    base = git(repo, "rev-parse", "HEAD").stdout.strip()
    # Provision the leaf's worktree one commit behind the named base.
    wt = os.path.join(os.path.dirname(repo), os.path.basename(repo) + "-wt")
    git(repo, "worktree", "add", "--detach", wt, head_prov)
    before = snapshot(wt)
    # Leaf: catch up by fast-forward, then one in-scope committed write.
    git(wt, "merge", "-q", "--ff-only", base)
    write(wt, "src/recon/engine.py", "def run():\n    return 1\n")
    git(wt, "commit", "-q", "-am", "leaf: engine")
    catch = f"CATCH-UP {head_prov[:7]}..{base[:7]} (1 commits, excluded — base {base[:7]})"
    f_clean = render(LEAF_SCOPE, observe(wt, head_prov, before, base=base), "F9")
    ok1 = (
        f_clean.token == "SCOPE: CLEAN"
        and f_clean.out_paths == []
        and any(ln == f"  Observed writes: {catch}" for ln in f_clean.lines)
        and not any("docs/plan.md" in ln for ln in f_clean.lines)  # catch-up excluded
        and any("IN" in ln and "src/recon/engine.py" in ln and "committed" in ln for ln in f_clean.lines)
    )
    # Assertion 2: plus one out-of-scope uncommitted write.
    write(wt, "docs/verification.md", "# Verification\nleaf edit\n")
    f_out = render(LEAF_SCOPE, observe(wt, head_prov, before, base=base), "F9")
    ok2 = (
        f_out.token == "SCOPE: VIOLATION (1 path)"
        and f_out.out_paths == ["docs/verification.md"]
        and any(ln == f"  Observed writes: {catch}" for ln in f_out.lines)
    )
    # Assertion 3: N == 0 — replay the F1 shape with and without a named base
    # equal to HEAD_prov; the two renderings must be byte-identical.
    git(wt, "checkout", "-q", "--", "docs/verification.md")
    head0, before0, content_before0 = _begin(wt)
    write(wt, "docs/plan.md", "# Plan\nleaf edit\n")
    plain = render(SEQ_SCOPE_SRC, observe(wt, head0, before0, content_before=content_before0), "F1")
    named = render(SEQ_SCOPE_SRC, observe(wt, head0, before0, base=head0, content_before=content_before0), "F1")
    ok3 = (
        plain.lines == named.lines
        and plain.token == "SCOPE: VIOLATION (1 path)"
        and not any("CATCH-UP" in ln for ln in named.lines)
    )
    ok = ok1 and ok2 and ok3
    token = f"{f_clean.token} + {f_out.token}" + ("" if ok3 else " (N==0 rendering differs)")
    return ok, token, f_clean.lines + f_out.lines


def scenario_f8(repo: str) -> tuple[bool, str, list[str]]:
    """Section resolution of fix hunks (arbitrated-handoff.md §Section Resolution).

    Self-contained replay of write-scope.md §3 "Section resolution" with four
    assertions over one fixture ``docs/spec/x.md`` carrying ``## A`` / ``## B`` /
    ``## C``:

      1. a committed diff touching lines 40–58 under ``## A`` and line 120
         under ``## C`` -> ``{x.md:§A, x.md:§C}`` with hunk strings ``L40-58``
         and ``L120`` (``## B`` untouched, absent);
      2. an untracked new Markdown file -> ``(path, *)`` (written in full);
      3. a ``.py`` path -> ``(path, ?)`` (non-Markdown, file-level fallback);
      4. an uncommitted edit above the first heading -> ``§(preamble)``.
    """
    # Fixture: a two-line preamble (no heading), then A at line 3, B at line 70,
    # C at line 100; 130 lines total.
    body = ["intro", ""]
    for name, start, end in (("A", 3, 69), ("B", 70, 99), ("C", 100, 130)):
        body.append(f"## {name}")
        body.extend(f"{name.lower()} line {i}" for i in range(start + 1, end + 1))
    assert len(body) == 130 and body[2] == "## A" and body[69] == "## B" and body[99] == "## C"
    write(repo, "docs/spec/x.md", "\n".join(body) + "\n")
    git(repo, "add", "docs/spec/x.md")
    git(repo, "commit", "-q", "-m", "fixture x.md")
    head_before = git(repo, "rev-parse", "HEAD").stdout.strip()
    # The fix rewrites lines 40–58 (under A) and line 120 (under C), committed.
    for i in range(39, 58):
        body[i] = f"a line {i + 1} (fixed)"
    body[119] = "c line 120 (fixed)"
    write(repo, "docs/spec/x.md", "\n".join(body) + "\n")
    git(repo, "commit", "-q", "-am", "fix #1")
    head_after = git(repo, "rev-parse", "HEAD").stdout.strip()
    sections, hunks = resolve_sections(repo, "docs/spec/x.md", head_before, head_after)
    ok1 = (
        sections == {("docs/spec/x.md", "§A"), ("docs/spec/x.md", "§C")}
        and hunks[("docs/spec/x.md", "§A")] == "L40-58"
        and hunks[("docs/spec/x.md", "§C")] == "L120"
    )
    # Assertion 2: untracked new Markdown file -> every section, rendered (path, *).
    write(repo, "docs/spec/new.md", "# New\n\n## Only\nbody\n")
    sections_new, _ = resolve_sections(repo, "docs/spec/new.md", head_before, head_after)
    ok2 = sections_new == {("docs/spec/new.md", "*")}
    # Assertion 3: non-Markdown path -> (path, ?), file-level comparison.
    write(repo, "src/a.py", "x = 2\n")
    sections_py, _ = resolve_sections(repo, "src/a.py", head_before, head_after)
    ok3 = sections_py == {("src/a.py", "?")}
    # Assertion 4: uncommitted hunk above the first heading -> §(preamble).
    body[0] = "intro (edited)"
    write(repo, "docs/spec/x.md", "\n".join(body) + "\n")
    sections_pre, hunks_pre = resolve_sections(repo, "docs/spec/x.md", head_before, head_after)
    ok4 = ("docs/spec/x.md", "§(preamble)") in sections_pre and hunks_pre.get(("docs/spec/x.md", "§(preamble)")) == "L1"
    ok = ok1 and ok2 and ok3 and ok4
    rendered = [f"docs/spec/x.md {sec} (hunks {hunks[('docs/spec/x.md', sec)]})" for sec in ("§A", "§C") if ("docs/spec/x.md", sec) in hunks]
    token = "{" + ", ".join(f"x.md:{s}" for _, s in sorted(sections)) + "}"
    if not ok2:
        token += " (untracked != *)"
    if not ok3:
        token += " (.py != ?)"
    if not ok4:
        token += " (preamble)"
    return ok, token, rendered + [f"docs/spec/new.md {s}" for _, s in sections_new] + [f"src/a.py {s}" for _, s in sections_py]


def scenario_f10(repo: str) -> tuple[bool, str, list[str]]:
    """Already-dirty path re-touched by the leaf (content-hash observation).

    ``harness-write-scope.md`` §Content-Hash Observation: ``docs/plan.md`` is
    already dirty *before* the dispatch, so its porcelain line is byte-identical
    in both snapshots and the §3 cancel rule drops it; the write is uncommitted,
    so the committed delta is empty too. Both halves of the fixture:

      1. the leaf writes the already-dirty path again -> its content hash
         differs, the path is observed and tagged OUT against a src-only scope
         -> ``SCOPE: VIOLATION (1 path)``;
      2. the same fixture with the leaf leaving that path untouched (it writes
         an in-scope path instead) -> no content delta, no false positive
         -> ``SCOPE: CLEAN``.
    """
    # Half 1 — dirty before the dispatch, re-touched during it.
    write(repo, "docs/plan.md", "# Plan\ndirty before the dispatch\n")
    head, before, content_before = _begin(repo)
    write(repo, "docs/plan.md", "# Plan\ndirty before the dispatch\nleaf re-touch\n")
    porcelain_cancels = snapshot(repo) == before  # the porcelain delta is empty
    f_dirty = render(SEQ_SCOPE_SRC, observe(repo, head, before, content_before=content_before), "F10")
    ok1 = (
        porcelain_cancels
        and f_dirty.token == "SCOPE: VIOLATION (1 path)"
        and f_dirty.out_paths == ["docs/plan.md"]
        and any("OUT" in ln and "docs/plan.md" in ln for ln in f_dirty.lines)
    )

    # Half 2 — same fixture, the leaf leaves the already-dirty path untouched.
    head2, before2, content_before2 = _begin(repo)
    write(repo, "src/recon/engine.py", "def run():\n    return 2\n")
    f_clean = render(SEQ_SCOPE_SRC, observe(repo, head2, before2, content_before=content_before2), "F10")
    ok2 = (
        f_clean.token == "SCOPE: CLEAN"
        and not any("docs/plan.md" in ln for ln in f_clean.lines)
        and any("IN" in ln and "src/recon/engine.py" in ln for ln in f_clean.lines)
    )

    ok = ok1 and ok2
    token = f"{f_dirty.token} + {f_clean.token}"
    return ok, token, f_dirty.lines + f_clean.lines



def scenario_f11(repo: str) -> tuple[bool, str, list[str]]:
    """Orchestrated marker-4 specs dispatch: docs/spec/** + its per-ws row, both IN.

    ``harness-write-scope.md`` §Specs Row Names the Per-Workstream Traceability
    Path (REQ-HARN-HARNESSP3-004): the specs row names
    ``docs/ws/<id>/traceability.md`` explicitly, so a specs leaf doing exactly
    what ``sdd-specs`` mandates (fill the Spec column) is ``SCOPE: CLEAN`` — not
    the false ``VIOLATION`` the unresolved row produced.
    """
    head, before, content_before = _begin(repo)
    write(repo, "docs/spec/recon.md", "# Recon\n\n## Design\n")
    write(repo, "docs/ws/harness/traceability.md", "| REQ | Spec | Workstream |\n| R1 | recon.md | harness |\n")
    f = render(SPECS_WS4_SCOPE, observe(repo, head, before, content_before=content_before), "F11")
    tags = [ln.split()[0] for ln in f.lines if ln.startswith("    ")]
    ok = f.token == "SCOPE: CLEAN" and tags == ["IN", "IN"] and not f.out_paths
    return ok, f.token, f.lines


def scenario_f12(repo: str) -> tuple[bool, str, list[str]]:
    """Orchestrated marker-4 verify dispatch that also writes the shared aggregate.

    ``ws-traceability.md`` §Aggregate Regeneration Ownership
    (REQ-WS-HARNESSP3-001): the aggregate is the orchestrator's post-gate
    bookkeeping, so it is absent from the leaf scope and a leaf that writes it
    anyway is ``OUT`` -> ``SCOPE: VIOLATION (1 path)``. The in-scope per-ws
    writes stay ``IN``.
    """
    head, before, content_before = _begin(repo)
    write(repo, "docs/ws/harness/verification.md", "# Verification\nstatus: pass\n")
    write(repo, "docs/ws/harness/traceability.md", "| REQ | Spec | Workstream | Verified |\n")
    write(repo, "docs/requirements/traceability.md", "| REQ | Spec | Verified |\n")
    f = render(VERIFY_WS4_SCOPE, observe(repo, head, before, content_before=content_before), "F12")
    ok = (
        f.token == "SCOPE: VIOLATION (1 path)"
        and f.out_paths == ["docs/requirements/traceability.md"]
        and any("OUT" in ln and "docs/requirements/traceability.md" in ln for ln in f.lines)
        and sum(1 for ln in f.lines if ln.strip().startswith("IN ")) == 2
    )
    return ok, f.token, f.lines


SCENARIOS = [
    ("F1", "porcelain-only OUT uncommitted", scenario_f1),
    ("F2", "committed OUT with clean porcelain", scenario_f2),
    ("F3", "verify writes verification + traceability", scenario_f3),
    ("F4", "implement writes docs/spec/recon.md (ADVISORY)", scenario_f4),
    ("F5", "blocked_writes docs/plan.md from a fan-out leaf", scenario_f5),
    ("F6", "amended HEAD (HISTORY_REWRITE)", scenario_f6),
    ("F7", "leaf appends to .sdd/telemetry.jsonl (third observation, reverted)", scenario_f7),
    ("F8", "section resolution: hunks L40-58 under ## A, L120 under ## C", scenario_f8),
    ("F9", "catch-up base: worktree one commit behind, leaf fast-forwards", scenario_f9),
    ("F10", "already-dirty path re-touched by the leaf (content-hash observation)", scenario_f10),
    ("F11", "orchestrated marker-4 specs dispatch: spec + per-ws row, both IN", scenario_f11),
    ("F12", "orchestrated marker-4 verify dispatch also writes the shared aggregate", scenario_f12),
]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sdd-scope-check-selftest.py",
        description=(
            f"Replay the {len(SCENARIOS)} write-scope scenarios of docs/spec/harness-write-scope.md "
            "§Verification, docs/spec/telemetry.md §Third Observation, "
            "docs/spec/arbitrated-handoff.md §Section Resolution and "
            "docs/spec/dispatch-snapshot-base.md §Snapshot Base Rule in throwaway git repos. "
            "Exit 0 when all pass."
        ),
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="print each finding block")
    parser.add_argument("--keep", action="store_true", help="keep the temp repos (prints the path)")
    args = parser.parse_args(argv)

    if shutil.which("git") is None:
        print("FAIL: git binary not found", file=sys.stderr)
        return 1

    root = tempfile.mkdtemp(prefix="sdd-scope-selftest-")
    failures = 0
    try:
        for sid, title, fn in SCENARIOS:
            repo = make_repo(root, sid)
            try:
                ok, token, lines = fn(repo)
            except Exception as exc:  # a crashed scenario is a failure, not a traceback
                ok, token, lines = False, f"error: {exc}", []
            failures += 0 if ok else 1
            print(f"{'PASS' if ok else 'FAIL'} {sid} {title} -> {token}")
            if args.verbose:
                for ln in lines:
                    print("      " + ln)
    finally:
        if args.keep:
            print(f"kept fixtures under {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)

    total = len(SCENARIOS)
    print(f"{'OK' if failures == 0 else 'FAILED'}: {total - failures}/{total} scenarios passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
