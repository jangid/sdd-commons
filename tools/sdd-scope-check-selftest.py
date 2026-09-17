#!/usr/bin/env python3
"""Self-test for the sdd-orchestrate write-scope check.

Builds throwaway git repositories under a temporary directory and replays the
six write-scope scenarios of ``docs/spec/harness-write-scope.md`` §Verification
(plan Chunk 4 task 5) against the observation procedure defined in
``skills/sdd-orchestrate/references/write-scope.md``:

  §3  the three commands — porcelain delta, committed delta, ancestry check
  §4  matching and tags — IN / ADVISORY / OUT
  §5  finding format and the own-line ``SCOPE:`` token
  §6  blocked-write fallback — pre-persist scope match

Scenarios (ids match the traceability Test cells for REQ-HARN-020..026):

  F1  porcelain-only OUT, uncommitted           -> SCOPE: VIOLATION (1 path)
  F2  committed OUT with a clean porcelain      -> SCOPE: VIOLATION (1 path)
  F3  verify writes verification + traceability -> both IN, SCOPE: CLEAN
  F4  implement writes docs/spec/recon.md       -> ADVISORY, SCOPE: CLEAN
  F5  blocked_writes docs/plan.md from a leaf   -> refused, listed OUT refused
  F6  amended HEAD                              -> HISTORY_REWRITE, VIOLATION

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


def git(repo: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command inside ``repo`` and return the completed process."""
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run(
        GIT_BASE + list(args),
        cwd=repo,
        env=env,
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
    """``git status --porcelain=v1 --untracked-files=all`` as a list of lines."""
    out = git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout
    return [ln for ln in out.splitlines() if ln]


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


def _porcelain_paths(line: str) -> tuple[str, list[str]]:
    """Split a porcelain v1 line into its status letter and path(s).

    ``XY path`` or ``XY old -> new`` for renames; both rename sides count (§3).
    """
    letter = (line[:2].strip() or "?")[0]
    rest = line[3:]
    if " -> " in rest:
        old, new = rest.split(" -> ", 1)
        return letter, [old, new]
    return letter, [rest]


def observe(repo: str, head_before: str, before: list[str]) -> Observation:
    """Run the AFTER half of §3 and return the union of the two deltas.

    (a) porcelain delta: lines in scope.after that are not in scope.before
    (b) committed delta: ``git diff --name-status HEAD_before HEAD_after``
    (c) ancestry: ``git merge-base --is-ancestor HEAD_before HEAD_after``
    """
    head_after = git(repo, "rev-parse", "HEAD").stdout.strip()
    after = snapshot(repo)
    obs = Observation()

    # (a) porcelain delta — paths present in both snapshots cancel.
    before_set = set(before)
    for line in after:
        if line in before_set:
            continue
        letter, paths = _porcelain_paths(line)
        for p in paths:
            obs.writes.append(Observed(p, letter, "uncommitted"))

    # (b) committed delta — catches writes that vanished from porcelain.
    if head_after != head_before:
        diff = git(repo, "diff", "--name-status", head_before, head_after).stdout
        for line in diff.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            letter = parts[0][0]
            paths = parts[1:]  # renames/copies carry old and new
            for p in paths:
                obs.writes.append(Observed(p, letter, f"committed {head_after[:7]}"))

    # (c) ancestry — a non-zero exit is a HISTORY_REWRITE finding.
    rc = git(repo, "merge-base", "--is-ancestor", head_before, head_after, check=False).returncode
    if rc != 0:
        obs.history_rewrite = (
            f"HISTORY_REWRITE  HEAD_after {head_after[:7]} does not descend "
            f"from HEAD_before {head_before[:7]}"
        )
    return obs


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


def _begin(repo: str) -> tuple[str, list[str]]:
    """The BEFORE half of §3: HEAD and porcelain snapshot immediately pre-dispatch."""
    return git(repo, "rev-parse", "HEAD").stdout.strip(), snapshot(repo)


def scenario_f1(repo: str) -> tuple[bool, str, list[str]]:
    """Porcelain-only OUT: uncommitted docs/plan.md edit against scope src/**."""
    head, before = _begin(repo)
    write(repo, "docs/plan.md", "# Plan\nleaf edit\n")
    f = render(SEQ_SCOPE_SRC, observe(repo, head, before), "F1")
    ok = (
        f.token == "SCOPE: VIOLATION (1 path)"
        and f.out_paths == ["docs/plan.md"]
        and any("OUT" in ln and "docs/plan.md" in ln and "uncommitted" in ln for ln in f.lines)
        and not any(".claude/worktrees" in ln for ln in f.lines)  # noise cancelled
    )
    return ok, f.token, f.lines


def scenario_f2(repo: str) -> tuple[bool, str, list[str]]:
    """Committed OUT with clean porcelain: docs/plan.md committed, scope docs/spec/**."""
    head, before = _begin(repo)
    write(repo, "docs/plan.md", "# Plan\nleaf edit, committed\n")
    git(repo, "commit", "-q", "-am", "leaf: plan edit")
    obs = observe(repo, head, before)
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
    head, before = _begin(repo)
    write(repo, "docs/verification.md", "# Verification\nstatus: pass\n")
    write(repo, "docs/requirements/traceability.md", "| REQ | Spec | Verified |\n")
    f = render(VERIFY_SCOPE, observe(repo, head, before), "F3")
    tags = [ln.split()[0] for ln in f.lines if ln.startswith("    ")]
    ok = f.token == "SCOPE: CLEAN" and tags == ["IN", "IN"]
    return ok, f.token, f.lines


def scenario_f4(repo: str) -> tuple[bool, str, list[str]]:
    """Implement dispatch writes docs/spec/recon.md: ADVISORY, CLEAN."""
    head, before = _begin(repo)
    write(repo, "docs/spec/recon.md", "# Recon\n\n## Implementation Questions\n### Q-IMPL-001: x\n")
    f = render(IMPLEMENT_SCOPE, observe(repo, head, before), "F4")
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
    head, before = _begin(repo)
    git(repo, "commit", "-q", "--amend", "--allow-empty", "-m", "base (amended by leaf)")
    obs = observe(repo, head, before)
    f = render(SEQ_SCOPE_SRC, obs, "F6")
    ok = (
        obs.history_rewrite is not None
        and f.token.startswith("SCOPE: VIOLATION")
        and any(ln.strip().startswith("HISTORY_REWRITE") for ln in f.lines)
    )
    return ok, f.token, f.lines


SCENARIOS = [
    ("F1", "porcelain-only OUT uncommitted", scenario_f1),
    ("F2", "committed OUT with clean porcelain", scenario_f2),
    ("F3", "verify writes verification + traceability", scenario_f3),
    ("F4", "implement writes docs/spec/recon.md (ADVISORY)", scenario_f4),
    ("F5", "blocked_writes docs/plan.md from a fan-out leaf", scenario_f5),
    ("F6", "amended HEAD (HISTORY_REWRITE)", scenario_f6),
]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sdd-scope-check-selftest.py",
        description=(
            "Replay the six write-scope scenarios of docs/spec/harness-write-scope.md "
            "§Verification in throwaway git repos. Exit 0 when all pass."
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
