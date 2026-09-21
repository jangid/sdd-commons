#!/usr/bin/env python3
"""Self-test for the orchestrate write-scope check.

Builds throwaway git repositories under a temporary directory and replays the
write-scope scenarios of ``docs/spec/harness-write-scope.md`` §Verification
(plan Chunk 4 task 5) plus ``docs/spec/telemetry.md`` §Third Observation (F7),
``docs/spec/arbitrated-handoff.md`` §Section Resolution (F8) and
``docs/spec/dispatch-snapshot-base.md`` §Snapshot Base Rule (F9) and
``docs/spec/harness-write-scope.md`` §Content-Hash Observation (F10),
§Specs Row Names the Per-Workstream Traceability Path (F11) and
``docs/spec/ws-traceability.md`` §Aggregate Regeneration Ownership (F12),
``docs/spec/harness-write-scope.md`` §`## Post-cycle Fixes` Is Inside the
Implement / ``RED_BREAK`` Scope (F13) and §`R`/`C` Records and `-z` Parsing
Are Fixture-Exercised (F15, F16) and §Git-State Observation (G1..G5) against the
observation procedure defined in ``skills/orchestrate/references/write-scope.md``:

  §3  the three commands — porcelain delta, committed delta, ancestry check —
      plus the git-state observation (stash count, branch, ``ORIG_HEAD``, and
      the reverse porcelain delta minus the committed delta)
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
  F13 RED_BREAK fix with NO open chunk: the     -> IN, SCOPE: CLEAN, exactly one
      only write is the plan's ## Post-cycle       new line under the section
      Fixes append
  F14 strict set: a path already dirty, then    -> rendered once, labelled
      committed and dirtied again (committed       "committed <sha>",
      AND content delta)                           SCOPE: VIOLATION (1 path)
  F15 rename across the scope boundary:         -> both paths in the ambiguous and
      ``git mv src/a.py docs/moved.py``             observed sets (one ``R`` record),
                                                   new path OUT, VIOLATION (1 path)
  F16 path with a space, untracked              -> ``-z`` keeps ONE record; observed
      ``docs/notes with space.md``                  and rendered as one path, VIOLATION
                                                   (1 path)

Git-state fixtures (``docs/spec/harness-write-scope.md`` §Git-State Observation,
``references/write-scope.md`` §3/§5/§8) — the harness-p5 incident and the three
legitimate cases the comparand must stay quiet on:

  G1  read-only leaf: git stash then stash pop -> GIT_STATE (ORIG_HEAD drift),
                                                  SCOPE: VIOLATION
  G2  read-only leaf: git stash then stash     -> GIT_STATE (reverse porcelain
      drop (the work is gone)                     delta), SCOPE: VIOLATION
  G3  implement leaf commits a path already    -> SCOPE: CLEAN (clause (ii)
      dirty at snapshot(before)                   subtracts the committed delta)
  G4  orchestrator fan-out merge between two   -> SCOPE: CLEAN (outside any
      dispatches                                  leaf's window)
  G5  ORIG_HEAD absent in both / present in    -> CLEAN + GIT_STATE,
      after only                                  SCOPE: VIOLATION

Commit-fidelity fixtures (``docs/spec/harness-commit-fidelity.md`` §Self-Test
Helper and Fixtures, ``references/write-scope.md`` §7a) — the pure helper
``commit_check(expected, landed)`` renders the own-line ``COMMIT:`` token from
two path sets; ``landed`` is always the two-sha range ``HEAD_before..HEAD_landed``:

  C1  sequential omission: 2 of 3 staged        -> COMMIT: INCOMPLETE (1 observed, not
                                                   landed: docs/plan.md); amended ->
                                                   COMMIT: COMPLETE (3 paths)
  C2  sequential inverse: stray.txt committed   -> both clauses on ONE line
  C3  fan-out fast-forward, two leaf commits    -> COMPLETE (2 paths) from the range;
                                                   git show HEAD -> false INCOMPLETE
  C4  fan-out true merge after bookkeeping      -> COMPLETE with the leaf's full delta;
                                                   a later regeneration commit changes nothing
  C5  conflict -> abort -> redo                  -> the redo's own sets -> COMPLETE (1 path);
                                                   never a third token
  C6  sequential commit, observed and landed     -> COMPLETE (2 paths), the space path
      both hold ``docs/notes with space.md``        counted once (``-z``, split on ``\0``);
                                                   whitespace split -> false INCOMPLETE


Convergence scenarios added at red round 1 (``harness-loop-control.md``
§Convergence Signal), each mutation-proven — reverting that one fix fails that
one scenario and no other:

  L10 red R3: key rule 2 is gated on a         -> the ``.py`` pair renders nothing;
      genuinely STRUCTURELESS file, not on        the ``.jsonl`` control still clusters
      "not Markdown"
  L11 red R4: a path absent from the checkout  -> no cluster key at all, so two
      is not evidence of structurelessness        findings on different sections of it
                                                  render nothing
  L12 red R5: ``_headings()`` is fence-aware,  -> a Markdown file whose only ``#`` is
      so a ``#`` inside a fenced block is not     inside a fence parses to [] sections
      a heading                                   and its cluster is not dropped

Usage:
    python3 tools/scope-check-selftest.py [-v] [--keep]

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


@dataclass(frozen=True)
class GitState:
    """The three extra plumbing values recorded by each snapshot (§3 git-state observation).

    ``harness-write-scope.md`` §Git-State Observation: they are read inside the
    **existing** ``snapshot(before)`` / ``snapshot(after)`` window — no second
    window is introduced — so a leaf that mutates git state without adding a
    porcelain line (the harness-p5 ``git stash``) is observed.
    """

    stash_count: int
    branch: str
    orig_head: str  # "" when ORIG_HEAD is absent — a legal value; absent-in-both compares equal


def git_state(repo: str) -> GitState:
    """``git stash list | wc -l``, ``rev-parse --abbrev-ref HEAD``, ``rev-parse --verify --quiet ORIG_HEAD``."""
    stashes = [ln for ln in git(repo, "stash", "list").stdout.splitlines() if ln.strip()]
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    # --verify --quiet: absence exits non-zero with empty output, which is the
    # legal empty value, not an error.
    orig = git(repo, "rev-parse", "--verify", "--quiet", "ORIG_HEAD", check=False).stdout.strip()
    return GitState(len(stashes), branch, orig)


def _short(sha: str) -> str:
    """A short sha for rendering; ``<none>`` for the legal empty ORIG_HEAD value."""
    return sha[:7] if sha else "<none>"


# Label precedence of the strict observed-writes set (harness-write-scope.md
# §Observed Writes Are a Strict Set): a path arriving from more than one term
# keeps the richest label — committed ≻ content ≻ porcelain.
TERM_RANK = {"porcelain": 0, "content": 1, "committed": 2}


@dataclass
class Observed:
    """One observed write: path, porcelain/diff status letter, provenance label.

    ``term`` names the §3 term that observed the path (``porcelain``,
    ``content`` or ``committed``) and drives the label precedence when the
    observation is collapsed to a strict set.
    """

    path: str
    letter: str
    where: str  # "uncommitted", "uncommitted (content)" or "committed <sha>"
    term: str = "porcelain"


@dataclass
class Observation:
    writes: list[Observed] = field(default_factory=list)
    history_rewrite: str | None = None  # rendered HISTORY_REWRITE line, if any
    git_state: str | None = None  # rendered GIT_STATE line, if any (§Git-State Observation)
    catch_up: str | None = None  # rendered CATCH-UP note for the header line, if any
    # Third observation (telemetry.md §4): finding strings for leaf writes under
    # the gitignored ``.sdd/`` — each counts as one more OUT path.
    telemetry_findings: list[str] = field(default_factory=list)
    telemetry_after: "TelemetrySnapshot | None" = None

    def collapse(self) -> None:
        """Collapse ``writes`` to a strict set — one entry per path (REQ-HARN-HARNESSP4-004).

        ``observed writes := porcelain_delta UNION committed_delta UNION
        content_delta`` is a set: a path observed by several terms is kept once,
        in first-seen order, carrying the entry with the richest ``term``
        (``TERM_RANK``). ``N`` in ``SCOPE: VIOLATION (N paths)``, every ``COMMIT:``
        operand and the ``Observed writes:`` list therefore count each path once.
        """
        best: dict[str, Observed] = {}
        order: list[str] = []
        for w in self.writes:
            if w.path not in best:
                best[w.path] = w
                order.append(w.path)
            elif TERM_RANK[w.term] > TERM_RANK[best[w.path].term]:
                best[w.path] = w
        self.writes = [best[p] for p in order]

    def paths(self) -> set[str]:
        """The observed-writes set — the sequential ``expected`` operand of ``COMMIT:``."""
        return {w.path for w in self.writes}


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

    The strings are defined once in ``skills/orchestrate/references/telemetry.md``
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
            obs.writes.append(Observed(p, letter, f"committed {sha[:7]}", term="committed"))


def observe(
    repo: str,
    head_before: str,
    before: list[str],
    telemetry_before: TelemetrySnapshot | None = None,
    *,
    base: str | None = None,
    content_before: dict[str, str] | None = None,
    state_before: GitState | None = None,
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
        letters = {}
        for line in after:
            letter, paths = _porcelain_paths(line)
            for p in paths:
                letters.setdefault(p, letter)
        # A path may be observed here AND by term (a) above or (b) below; the
        # strict-set collapse at the end keeps one entry with the richest label.
        for p, sha_before in content_before.items():
            on_disk = os.path.isfile(os.path.join(repo, p))
            if not on_disk:
                sha_after = ABSENT
            elif p in after_paths:
                sha_after = content_hashes(repo, [p])[p]
            else:
                continue  # no longer dirty: the reverted/committed round trip of §5
            if sha_after != sha_before:
                obs.writes.append(
                    Observed(
                        p,
                        "D" if sha_after == ABSENT else letters.get(p, "M"),
                        "uncommitted (content)",
                        term="content",
                    )
                )

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

    # Git-state observation (REQ-HARN-HARNESSP6-001) — the comparand's two
    # clauses, evaluated inside this same window:
    #   (i)  state drift: stash count, branch or ORIG_HEAD differs between the
    #        two snapshots (requires ``state_before``, taken pre-dispatch);
    #   (ii) reverse porcelain delta: paths dirty in ``before`` and NOT dirty in
    #        ``after``, MINUS the committed delta — a path stopped being dirty
    #        with no commit explaining it. The existing delta (a) is
    #        one-directional (lines in after, not in before), so a REMOVAL of
    #        dirty lines — ``git stash``, ``git checkout -- <path>``,
    #        ``git restore``, ``git clean`` — is invisible to it.
    drift: list[str] = []
    if state_before is not None:
        state_after = git_state(repo)
        if state_after.stash_count != state_before.stash_count:
            drift.append(f"stash count {state_before.stash_count} -> {state_after.stash_count}")
        if state_after.branch != state_before.branch:
            drift.append(f"branch {state_before.branch} -> {state_after.branch}")
        if state_after.orig_head != state_before.orig_head:
            # Absence is the legal empty value, so absent-in-both compares equal
            # and raises nothing; present-in-after-only is drift.
            drift.append(f"ORIG_HEAD {_short(state_before.orig_head)} -> {_short(state_after.orig_head)}")
    committed_paths = {w.path for w in obs.writes if w.term == "committed"}
    after_dirty = set(ambiguous_set(after))
    reverse_delta = [
        p for p in ambiguous_set(before) if p not in after_dirty and p not in committed_paths
    ]
    if reverse_delta:
        shown = ", ".join(reverse_delta[:3]) + (", …" if len(reverse_delta) > 3 else "")
        drift.append(
            f"{len(reverse_delta)} path(s) dirty before and clean after with no commit ({shown})"
        )
    if drift:
        obs.git_state = "GIT_STATE  " + "; ".join(drift)

    # (c) ancestry — a non-zero exit is a HISTORY_REWRITE finding.
    rc = git(repo, "merge-base", "--is-ancestor", head_before, head_after, check=False).returncode
    if rc != 0:
        obs.history_rewrite = (
            f"HISTORY_REWRITE  HEAD_after {head_after[:7]} does not descend "
            f"from HEAD_before {head_before[:7]}"
        )
    # Strict set: the three terms are a UNION, so each path is kept once with
    # its richest provenance label (harness-write-scope.md, REQ-HARN-HARNESSP4-004).
    obs.collapse()
    return obs


# ---------------------------------------------------------------------------
# write-scope.md §7a — commit-fidelity check, COMMIT: COMPLETE | INCOMPLETE
# ---------------------------------------------------------------------------


def head_sha(repo: str) -> str:
    """``git rev-parse HEAD`` — captured as a sha, never used as a literal ``HEAD`` comparand."""
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def observed_paths(obs: Observation) -> set[str]:
    """The observed-writes set: the sequential ``expected`` operand (never ``RETURN.files_written``)."""
    return obs.paths()


def landed_paths(repo: str, head_before: str, head_landed: str) -> set[str]:
    """``git diff --name-only --no-renames -z <HEAD_before> <HEAD_landed>`` as a set.

    The two-sha RANGE comparand of §7a: captured right after the orchestrator's
    own commit or merge and before any bookkeeping commit. The same command
    yields a leaf's committed delta ``base..tip`` (write-scope term (b)), which
    is the fan-out ``expected``. ``--no-renames`` keeps a rename as two paths so
    both sides agree with §3's observation.
    """
    # ``-z`` NUL-separates the paths; split on ``\0`` and drop the empty trailing
    # token so a path containing a space (F16 / C6) stays one path.
    out = git(repo, "diff", "--name-only", "--no-renames", "-z", head_before, head_landed).stdout
    return {p for p in out.split("\0") if p}


def show_head_paths(repo: str, sha: str) -> set[str]:
    """``git show --name-only --format= -z <sha>`` — the REJECTED comparand, kept as C3's negative control.

    It names only that one commit's paths (empty for a merge commit), so after a
    fast-forward of a multi-commit leaf it renders a false ``INCOMPLETE``.
    """
    out = git(repo, "show", "--name-only", "--format=", "-z", sha).stdout
    return {p for p in out.split("\0") if p}


def commit_check(expected: set[str], landed: set[str]) -> str:
    """Render the own-line ``COMMIT:`` token (harness-commit-fidelity.md §Self-Test Helper).

    Pure: no git, no I/O. ``N`` counts distinct paths. Exactly two members:

      COMMIT: COMPLETE (N paths)                                  # expected == landed
      COMMIT: INCOMPLETE (k observed, not landed: <paths>[; j landed, not observed: <paths>])

    Paths are rendered sorted and comma-separated. The first clause is elided
    when ``k == 0``; the second is present whenever ``j > 0``.
    """
    expected, landed = set(expected), set(landed)
    missing = sorted(expected - landed)  # observed, not landed — the V14 omission
    stray = sorted(landed - expected)  # landed, not observed — the inverse error
    if not missing and not stray:
        n = len(landed)
        return f"COMMIT: COMPLETE ({n} path{'s' if n != 1 else ''})"
    clauses: list[str] = []
    if missing:
        clauses.append(f"{len(missing)} observed, not landed: {', '.join(missing)}")
    if stray:
        clauses.append(f"{len(stray)} landed, not observed: {', '.join(stray)}")
    return f"COMMIT: INCOMPLETE ({'; '.join(clauses)})"


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


# A fenced code block opens and closes on a line whose first non-space run is
# three or more backticks or tildes (CommonMark). Everything between the opening
# fence and the next fence of the SAME character is literal text, so a ``#``
# there is a shell comment or a Markdown example — never a heading.
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")


def _headings(lines: list[str]) -> list[tuple[int, str]]:
    """``(line number, §Name)`` for every ``#``-heading, 1-based, in file order.

    **Fence-aware** (REQ-HARN-HARNESSP6-002, red R5). Lines inside a fenced code
    block are skipped: a ``# comment`` in a fenced shell block is not a heading,
    and counting it made a genuinely structureless Markdown file look sectioned,
    which silently dropped a convergence that key rule 2 would have rendered.
    This is the same fence-blindness class REQ-GC-HARNESSP6-004 closed in
    ``tools/gc.py``; the sibling tool key rule 2 depends on had kept it.
    """
    out: list[tuple[int, str]] = []
    fence: str | None = None  # the opening fence's character run, while open
    for i, ln in enumerate(lines, start=1):
        m = FENCE.match(ln)
        if m:
            token = m.group(1)[0]
            if fence is None:
                fence = token
            elif token == fence:
                fence = None  # a closing fence of the same character
            continue
        if fence is None and ln.startswith("#"):
            out.append((i, section_name(ln)))
    return out


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
    # GIT_STATE renders inside this block, parallel to HISTORY_REWRITE and above
    # the path list; it introduces no new gate token (Q-REQ-P6-A).
    if obs.git_state:
        lines.append(f"  {obs.git_state}")
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
    # N counts OUT paths plus a HISTORY_REWRITE and a GIT_STATE finding;
    # ADVISORY never counts.
    n = len(out_paths) + (1 if obs.history_rewrite else 0) + (1 if obs.git_state else 0)
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
# RED_BREAK fix with NO open chunk: target.chunk resolves to nothing, so the
# chunk's source/test globs are absent and the row degenerates to the active
# plan path alone (marker 4: docs/ws/<id>/plan.md) — harness-write-scope.md
# §`## Post-cycle Fixes` Is Inside the Implement / `RED_BREAK` Scope.
RED_BREAK_NO_CHUNK_SCOPE = [ScopeGlob("docs/ws/harness/plan.md")]


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
    what ``specs`` mandates (fill the Spec column) is ``SCOPE: CLEAN`` — not
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


def scenario_f13(repo: str) -> tuple[bool, str, list[str]]:
    """`RED_BREAK` fix with NO open chunk: the only write is the plan's
    ``## Post-cycle Fixes`` append.

    ``harness-write-scope.md`` §`## Post-cycle Fixes` Is Inside the Implement /
    `RED_BREAK` Scope (REQ-REDB-HARNESSP3-004): the implement / `RED_BREAK` row
    names the active plan path, so when ``target.chunk`` resolves to nothing the
    scope degenerates to that path alone and the orchestrator-owned append is
    tagged ``IN`` -> ``SCOPE: CLEAN``. This is the case the spec's Open Question
    answers by default assumption, so it is exercised rather than assumed.
    """
    plan = (
        "# Implementation Plan\n\n## Chunks\n\n### Chunk 0: done\n"
        "**Tasks**:\n1. [implement] x — traces to recon.md\n\n## Post-cycle Fixes\n"
    )
    write(repo, "docs/ws/harness/plan.md", plan)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plan with an empty Post-cycle Fixes section")

    head, before, content_before = _begin(repo)
    # The RED_BREAK fix: exactly one line appended under the section.
    write(repo, "docs/ws/harness/plan.md", plan + "- R3 — window guard ignored 0, clamped in engine.run (abc1234)\n")
    f = render(RED_BREAK_NO_CHUNK_SCOPE, observe(repo, head, before, content_before=content_before), "F13")

    after = open(os.path.join(repo, "docs/ws/harness/plan.md"), encoding="utf-8").read().splitlines()
    idx = after.index("## Post-cycle Fixes")
    section = [ln for ln in after[idx + 1:] if ln.strip()]

    ok = (
        f.token == "SCOPE: CLEAN"
        and not f.out_paths
        and any(ln.strip().startswith("IN ") and "docs/ws/harness/plan.md" in ln for ln in f.lines)
        and len(section) == 1
        and section[0].startswith("- R3 — ")
    )
    return ok, f.token, f.lines


def scenario_f14(repo: str) -> tuple[bool, str, list[str]]:
    """Strict observed-writes set: one path seen by the committed AND the content delta.

    ``harness-write-scope.md`` §Observed Writes Are a Strict Set
    (REQ-HARN-HARNESSP4-004): ``docs/plan.md`` is dirty at snapshot time,
    committed during the dispatch and dirtied again, so its porcelain lines
    cancel while **both** the committed delta (b) and the content delta observe
    it. The path must be rendered once, labelled ``committed <sha>`` (the richest
    label), and counted once -> ``SCOPE: VIOLATION (1 path)`` — never ``(2 paths)``.
    """
    write(repo, "docs/plan.md", "# Plan\ndirty before the dispatch\n")
    head, before, content_before = _begin(repo)
    write(repo, "docs/plan.md", "# Plan\nleaf edit, committed\n")
    git(repo, "commit", "-q", "-am", "leaf: plan edit")
    write(repo, "docs/plan.md", "# Plan\nleaf edit, committed\ndirtied again\n")
    porcelain_cancels = snapshot(repo) == before
    obs = observe(repo, head, before, content_before=content_before)
    f = render(SEQ_SCOPE_SRC, obs, "F14")
    plan_writes = [w for w in obs.writes if w.path == "docs/plan.md"]
    plan_lines = [ln for ln in f.lines if ln.startswith("    ") and "docs/plan.md" in ln]
    ok = (
        porcelain_cancels
        and len(plan_writes) == 1
        and plan_writes[0].where.startswith("committed ")
        and len(plan_lines) == 1
        and "committed" in plan_lines[0]
        and f.token == "SCOPE: VIOLATION (1 path)"
        and f.out_paths == ["docs/plan.md"]
    )
    return ok, f.token, f.lines


def scenario_f15(repo: str) -> tuple[bool, str, list[str]]:
    """Rename across the scope boundary: ``git mv`` a scoped path out of scope.

    ``harness-write-scope.md`` §`R`/`C` Records and `-z` Parsing Are
    Fixture-Exercised (REQ-HARN-HARNESSP4-005): the leaf runs
    ``git mv src/a.py docs/moved.py`` during the dispatch. ``-z`` porcelain
    emits ONE ``R`` record whose original path is a second NUL-separated field;
    ``snapshot`` rejoins it and ``_porcelain_paths`` yields **both** paths, so
    both enter the ambiguous set and the observed set, the new path tags ``OUT``
    against ``src/**``, and the rename is observed rather than cancelling.
    """
    head, before, content_before = _begin(repo)
    git(repo, "mv", "src/a.py", "docs/moved.py")
    after = snapshot(repo)
    r_records = [rec for rec in after if rec.startswith("R")]
    ambiguous = ambiguous_set(after)                      # both sides of the R record
    obs = observe(repo, head, before, content_before=content_before)
    f = render(SEQ_SCOPE_SRC, obs, "F15")
    observed = {w.path for w in obs.writes}
    ok = (
        len(r_records) == 1
        and "\0" in r_records[0]                          # one record, two fields
        and "src/a.py" in ambiguous
        and "docs/moved.py" in ambiguous
        and observed == {"src/a.py", "docs/moved.py"}      # observed, not cancelled
        and all(w.letter == "R" for w in obs.writes)
        and any(ln.startswith("    IN") and "src/a.py" in ln for ln in f.lines)
        and any(ln.startswith("    OUT") and "docs/moved.py" in ln for ln in f.lines)
        and f.out_paths == ["docs/moved.py"]
        and f.token == "SCOPE: VIOLATION (1 path)"
    )
    return ok, f.token, f.lines


def scenario_f16(repo: str) -> tuple[bool, str, list[str]]:
    """Path with a space: ``-z`` keeps ``docs/notes with space.md`` one record.

    ``harness-write-scope.md`` §`R`/`C` Records and `-z` Parsing Are
    Fixture-Exercised (REQ-HARN-HARNESSP4-005): the written path contains a
    space, the condition under which newline/whitespace splitting of porcelain
    output would mangle or quote it. With ``-z`` it stays one unquoted record,
    is observed once and rendered as one ``OUT`` path.
    """
    head, before, content_before = _begin(repo)
    write(repo, "docs/notes with space.md", "# Notes\n")
    after = snapshot(repo)
    note_records = [rec for rec in after if "notes" in rec]
    obs = observe(repo, head, before, content_before=content_before)
    f = render(SEQ_SCOPE_SRC, obs, "F16")
    note_lines = [ln for ln in f.lines if ln.startswith("    ") and "notes" in ln]
    ok = (
        note_records == ["?? docs/notes with space.md"]  # one record, unquoted
        and [w.path for w in obs.writes] == ["docs/notes with space.md"]
        and len(note_lines) == 1
        and note_lines[0].startswith("    OUT")
        and f.out_paths == ["docs/notes with space.md"]
        and f.token == "SCOPE: VIOLATION (1 path)"
    )
    return ok, f.token, f.lines


# ---------------------------------------------------------------------------
# commit-fidelity fixtures C1–C5 (harness-commit-fidelity.md §Self-Test Helper)
# ---------------------------------------------------------------------------


def scenario_c1(repo: str) -> tuple[bool, str, list[str]]:
    """C1 sequential omission: leaf writes three paths, the orchestrator stages two.

    ``expected`` is the observed-writes set (never ``RETURN.files_written``);
    ``landed`` is the range ``HEAD_before..HEAD_landed``. Two of three staged ->
    ``COMMIT: INCOMPLETE (1 observed, not landed: docs/plan.md)``; after the
    ``amend`` remedy (stage the missing path, amend the orchestrator's own
    commit) the same range renders ``COMMIT: COMPLETE (3 paths)``.
    """
    head_before, before, content_before = _begin(repo)
    write(repo, "a.txt", "a\n")
    write(repo, "b.txt", "b\n")
    write(repo, "docs/plan.md", "# Plan\n- [x] task 1\n")
    expected = observed_paths(observe(repo, head_before, before, content_before=content_before))
    # Orchestrator commit: docs/plan.md is left unstaged (the V14 defect).
    git(repo, "add", "a.txt", "b.txt")
    git(repo, "commit", "-q", "-m", "chunk 1")
    line_omit = commit_check(expected, landed_paths(repo, head_before, head_sha(repo)))
    # amend: stage every ``observed, not landed`` path into the orchestrator's own commit.
    git(repo, "add", "docs/plan.md")
    git(repo, "commit", "-q", "--amend", "--no-edit")
    line_full = commit_check(expected, landed_paths(repo, head_before, head_sha(repo)))
    ok = (
        expected == {"a.txt", "b.txt", "docs/plan.md"}
        and line_omit == "COMMIT: INCOMPLETE (1 observed, not landed: docs/plan.md)"
        and line_full == "COMMIT: COMPLETE (3 paths)"
    )
    return ok, f"{line_omit} -> {line_full}", [line_omit, line_full]


def scenario_c2(repo: str) -> tuple[bool, str, list[str]]:
    """C2 sequential inverse: the orchestrator also commits ``stray.txt`` no leaf wrote.

    Both directions of the set difference are clauses of **one** line:
    ``INCOMPLETE (1 observed, not landed: b.txt; 1 landed, not observed: stray.txt)``.
    The pure form with an empty first clause elides it but keeps the second.
    """
    head_before, before, content_before = _begin(repo)
    write(repo, "a.txt", "a\n")
    write(repo, "b.txt", "b\n")
    expected = observed_paths(observe(repo, head_before, before, content_before=content_before))
    write(repo, "stray.txt", "orchestrator wrote this\n")
    git(repo, "add", "a.txt", "stray.txt")
    git(repo, "commit", "-q", "-m", "chunk 1 (with a stray path)")
    line = commit_check(expected, landed_paths(repo, head_before, head_sha(repo)))
    pure = commit_check({"a.txt"}, {"a.txt", "stray.txt"})
    ok = (
        line == "COMMIT: INCOMPLETE (1 observed, not landed: b.txt; 1 landed, not observed: stray.txt)"
        and "\n" not in line
        and pure == "COMMIT: INCOMPLETE (1 landed, not observed: stray.txt)"
    )
    return ok, line, [line, pure]


def scenario_c3(repo: str) -> tuple[bool, str, list[str]]:
    """C3 fan-out fast-forward: a two-commit leaf merges by fast-forward.

    ``expected`` is the leaf's committed delta ``base..tip``; ``landed`` is the
    range ``PRE_MERGE..HEAD`` -> ``COMMIT: COMPLETE (2 paths)``. Negative
    control: ``git show --name-only --format= HEAD`` names only the *last*
    commit's path, so the same comparison renders a false ``INCOMPLETE`` —
    which is why the range, never ``git show HEAD``, is the comparand.
    """
    base = head_sha(repo)
    git(repo, "checkout", "-q", "-b", "leaf")
    write(repo, "a.txt", "a\n")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-q", "-m", "leaf 1: a.txt")
    write(repo, "b.txt", "b\n")
    git(repo, "add", "b.txt")
    git(repo, "commit", "-q", "-m", "leaf 2: b.txt")
    tip = head_sha(repo)
    git(repo, "checkout", "-q", "main")
    expected = landed_paths(repo, base, tip)  # the leaf's committed delta — write-scope term (b)
    pre_merge = head_sha(repo)
    git(repo, "merge", "-q", "--ff-only", "leaf")
    head_landed = head_sha(repo)
    landed = landed_paths(repo, pre_merge, head_landed)  # C3 RANGE — the two-sha comparand
    line = commit_check(expected, landed)
    shown = show_head_paths(repo, head_landed)
    control = commit_check(expected, shown)
    ok = (
        expected == {"a.txt", "b.txt"}
        and line == "COMMIT: COMPLETE (2 paths)"
        and shown == {"b.txt"}
        and control.startswith("COMMIT: INCOMPLETE (")
        and "a.txt" in control
    )
    return ok, f"{line}; git show HEAD -> {control}", [line, f"negative control (git show): {control}"]


def scenario_c4(repo: str) -> tuple[bool, str, list[str]]:
    """C4 fan-out true merge after a bookkeeping commit on the integration branch.

    The integration branch diverges (a bookkeeping commit) before the leaf
    merges, so the merge is a true merge commit. ``PRE_MERGE..HEAD`` still
    equals the leaf's full delta -> ``COMPLETE (2 paths)``; a regeneration
    commit made *after* the two shas are captured leaves the line unchanged.
    """
    base = head_sha(repo)
    git(repo, "checkout", "-q", "-b", "leaf")
    write(repo, "a.txt", "a\n")
    write(repo, "b.txt", "b\n")
    git(repo, "add", "a.txt", "b.txt")
    git(repo, "commit", "-q", "-m", "leaf: a.txt b.txt")
    tip = head_sha(repo)
    git(repo, "checkout", "-q", "main")
    write(repo, "docs/requirements/traceability.md", "| REQ | Spec |\n| R1 | recon.md |\n")
    git(repo, "commit", "-q", "-am", "bookkeeping before the merge")
    expected = landed_paths(repo, base, tip)
    pre_merge = head_sha(repo)
    git(repo, "merge", "-q", "--no-ff", "--no-edit", "leaf")
    head_landed = head_sha(repo)
    is_merge = len(git(repo, "rev-list", "--parents", "-n1", head_landed).stdout.split()) == 3
    line = commit_check(expected, landed_paths(repo, pre_merge, head_landed))
    # Regeneration commit AFTER the range was captured: not inside the range.
    write(repo, "docs/requirements/traceability.md", "| REQ | Spec |\n| R1 | recon.md |\n| R2 | x.md |\n")
    git(repo, "commit", "-q", "-am", "regenerate aggregate")
    line_after = commit_check(expected, landed_paths(repo, pre_merge, head_landed))
    ok = (
        is_merge
        and expected == {"a.txt", "b.txt"}
        and line == "COMMIT: COMPLETE (2 paths)"
        and line_after == line
    )
    return ok, line, [line, f"after regeneration commit: {line_after}"]


def scenario_c5(repo: str) -> tuple[bool, str, list[str]]:
    """C5 conflict -> abort -> redo: the redo's own sets are compared.

    The first leaf commits ``a.txt b.txt`` and conflicts with the integration
    branch on ``a.txt``; the merge is aborted (tree restored). The redo is a new
    dispatch with its own base and tip, committing ``b.txt`` only -> ``COMMIT:
    COMPLETE (1 path)``. The first attempt's set never enters the comparison and
    no third token is rendered.
    """
    base = head_sha(repo)
    git(repo, "checkout", "-q", "-b", "leaf1")
    write(repo, "a.txt", "leaf version\n")
    write(repo, "b.txt", "b\n")
    git(repo, "add", "a.txt", "b.txt")
    git(repo, "commit", "-q", "-m", "leaf1: a.txt b.txt")
    tip1 = head_sha(repo)
    git(repo, "checkout", "-q", "main")
    write(repo, "a.txt", "integration version\n")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-q", "-m", "main: a.txt")
    pre_abort = head_sha(repo)
    snap_pre = snapshot(repo)
    conflicted = git(repo, "merge", "-q", "leaf1", check=False).returncode != 0
    git(repo, "merge", "--abort")
    restored = head_sha(repo) == pre_abort and snapshot(repo) == snap_pre
    first_attempt = landed_paths(repo, base, tip1)  # {a.txt, b.txt} — discarded by design
    # Redo: a new dispatch with its own snapshot, committed delta and per-leaf gate.
    base2 = head_sha(repo)
    git(repo, "checkout", "-q", "-b", "leaf2")
    write(repo, "b.txt", "b\n")
    git(repo, "add", "b.txt")
    git(repo, "commit", "-q", "-m", "leaf2 (redo): b.txt")
    tip2 = head_sha(repo)
    git(repo, "checkout", "-q", "main")
    expected = landed_paths(repo, base2, tip2)
    pre_merge = head_sha(repo)
    git(repo, "merge", "-q", "--ff-only", "leaf2")
    line = commit_check(expected, landed_paths(repo, pre_merge, head_sha(repo)))
    ok = (
        conflicted
        and restored
        and first_attempt == {"a.txt", "b.txt"}
        and expected == {"b.txt"}
        and line == "COMMIT: COMPLETE (1 path)"
        and re.fullmatch(r"COMMIT: (COMPLETE|INCOMPLETE) \(.*\)", line) is not None
    )
    return ok, line, [f"first attempt (aborted): {sorted(first_attempt)}", line]


def scenario_c6(repo: str) -> tuple[bool, str, list[str]]:
    """C6 sequential commit whose observed and landed sets hold ``docs/notes with space.md``.

    ``git diff --name-only`` prints a path containing a space unquoted, so a
    whitespace split of its output would break the landed operand into three
    tokens and render a false ``COMMIT: INCOMPLETE`` for the F16 path. Both
    comparands are parsed with ``-z`` and split on ``\0``, so the path is
    counted once and the gate renders ``COMMIT: COMPLETE (2 paths)``. The
    whitespace-split rendering is kept as the negative control.
    """
    head_before, before, content_before = _begin(repo)
    write(repo, "a.txt", "a\n")
    write(repo, "docs/notes with space.md", "# Notes\n")
    expected = observed_paths(observe(repo, head_before, before, content_before=content_before))
    git(repo, "add", "a.txt", "docs/notes with space.md")
    git(repo, "commit", "-q", "-m", "chunk with a space path")
    head_landed = head_sha(repo)
    landed = landed_paths(repo, head_before, head_landed)
    line = commit_check(expected, landed)
    # Negative control: the pre-fix whitespace split of the non-``-z`` output.
    naive = set(git(repo, "diff", "--name-only", "--no-renames", head_before, head_landed).stdout.split())
    line_naive = commit_check(expected, naive)
    ok = (
        expected == {"a.txt", "docs/notes with space.md"}
        and landed == expected
        and line == "COMMIT: COMPLETE (2 paths)"
        and line_naive.startswith("COMMIT: INCOMPLETE (1 observed, not landed: docs/notes with space.md;")
    )
    return ok, f"{line} (whitespace split would render: {line_naive})", [line, line_naive]


# ---------------------------------------------------------------------------
# arbitrated-handoff.md §Offline Arbitration Fixture — scenarios A1-A3
# ---------------------------------------------------------------------------

#: The frozen git capture of the harness-p4 implement-stage regeneration.
#: ``before.md`` / ``after.md`` are ``git show`` captures of 82d0af0 and 3772574
#: (see ``tools/fixtures/README.md``); the fixture is read-only here — every
#: mutation case below copies it in memory and writes the copy into a temp repo.
ARB_FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fixtures",
    "arbitration-harness-p4-regen-2026-09-19",
)
#: The path the captured plan is replayed at, per ``dispatch.txt``'s observed writes.
ARB_PLAN_PATH = "docs/ws/harness-p4/plan.md"

#: ``- M1: text — [path:§Section] — affects [REQ-…]`` (loop-control.md §2a key form).
FINDING_REF = re.compile(r"\[([^\[\]:]+):(§[^\[\]]+)\]")


@dataclass(frozen=True)
class Round:
    """A parsed review round: its verdict and its C/M findings' keys, in order."""

    verdict: str
    keys: tuple[tuple[str, str], ...]


def finding_key(line: str) -> tuple[str, str] | None:
    """``(path, §Name)`` for a C/M finding line, or ``None`` when it carries no ref.

    The section is normalised through :func:`section_name`, so a leading ordinal
    (``§3. Conventions``) resolves to the same key as ``§Conventions``
    (REQ-ARB-HARNESSP5-003).
    """
    m = FINDING_REF.search(line)
    if not m:
        return None
    return m.group(1).strip(), section_name(m.group(2).lstrip("§"))


def parse_round(text: str) -> Round:
    """Parse a review round's text into its verdict and its findings' keys."""
    verdict = ""
    keys: list[tuple[str, str]] = []
    for line in text.splitlines():
        if line.startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip()
            continue
        if not line.lstrip().startswith("-"):
            continue
        key = finding_key(line)
        if key is not None and key not in keys:
            keys.append(key)
    return Round(verdict, tuple(keys))


def _is_written(key: tuple[str, str], w_n: set[tuple[str, str]]) -> bool:
    """Whether ``key``'s section counts as written in ``w_n``.

    ``(path, *)`` — the file-level fallback reserved for a *missing* diff — makes
    every section of that path count as written (§Section Resolution).
    """
    return key in w_n or (key[0], "*") in w_n


def arbitrate(
    round_n: Round, round_n1: Round, w_n: set[tuple[str, str]]
) -> tuple[str | None, list[tuple[str, str]]]:
    """Pure §Contradiction Classes decision — no git, no I/O.

    Class (b): round-N+1 keys with ``k not in K_N`` and ``k not in W_N`` — a
    reviewer raising new ground the loop did not touch. Class (c): an
    ``APPROVE_WITH_FIXES`` round N followed by a ``REJECT`` round N+1 on the
    same refs. Returns ``(class | None, annotated_keys)``.
    """
    k_n = set(round_n.keys)
    if (
        round_n.verdict == "APPROVE_WITH_FIXES"
        and round_n1.verdict == "REJECT"
        and round_n1.keys
        and set(round_n1.keys) <= k_n
    ):
        return "c", []
    annotated = [k for k in round_n1.keys if k not in k_n and not _is_written(k, w_n)]
    return ("b", annotated) if annotated else (None, [])


def arb_fixture(name: str) -> str:
    """Read one file of the frozen fixture (read-only; never written back)."""
    with open(os.path.join(ARB_FIXTURE_DIR, name), encoding="utf-8") as fh:
        return fh.read()


def _replay_regeneration(repo: str, after_text: str | None = None) -> set[tuple[str, str]]:
    """Commit ``before.md`` at the plan path, write ``after.md``, return ``W_1``.

    ``after_text`` overrides the captured after-image (the m-ii mutation case);
    the fixture files themselves are never modified.
    """
    write(repo, ARB_PLAN_PATH, arb_fixture("before.md"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "plan before the wholesale regeneration")
    head = head_sha(repo)
    write(repo, ARB_PLAN_PATH, arb_fixture("after.md") if after_text is None else after_text)
    sections, _ = resolve_sections(repo, ARB_PLAN_PATH, head, head)
    return sections


def _a1(repo: str, round2_text: str | None = None, after_text: str | None = None):
    """Run the A1 comparison, returning ``(w_1, diff_based, provenance)``.

    ``diff_based`` applies this spec's rule (``W_1`` from the regeneration diff);
    ``provenance`` applies the rejected ``regen[N] = (file, *)`` reading.
    """
    w_1 = _replay_regeneration(repo, after_text)
    r1 = parse_round(arb_fixture("round-1.txt"))
    r2 = parse_round(arb_fixture("round-2.txt") if round2_text is None else round2_text)
    return w_1, arbitrate(r1, r2, w_1), arbitrate(r1, r2, {(ARB_PLAN_PATH, "*")})


def _a1_holds(diff_based, provenance) -> bool:
    """A1's asserted outcome: ``class b`` with two annotated keys, no provenance token."""
    cls, annotated = diff_based
    return cls == "b" and len(annotated) == 2 and provenance == (None, [])


def scenario_a1(repo: str) -> tuple[bool, str, list[str]]:
    """A1 — the discriminating p4 case: round 2 on the regenerated plan's unchanged sections.

    The capture leaves `§Conventions` and `§Verification Hand-off` byte-identical,
    so both round-2 keys are outside `W_1`: the diff-based rule raises `class b`
    with two annotated keys, while the rejected provenance reading
    (`regen[1] = (plan.md, *)`) raises no token. Both columns print side by side
    (REQ-ARB-HARNESSP5-001, -002).
    """
    w_1, diff_based, provenance = _a1(repo)
    cls, annotated = diff_based
    # REQ-ARB-HARNESSP5-003: the same line with and without its ordinal is one key.
    ordinal_same = finding_key(
        f"- M1: x — [{ARB_PLAN_PATH}:§3. Conventions] — affects —"
    ) == finding_key(f"- M1: x — [{ARB_PLAN_PATH}:§Conventions] — affects —")
    expected = [(ARB_PLAN_PATH, "§Conventions"), (ARB_PLAN_PATH, "§Verification Hand-off")]
    ok = _a1_holds(diff_based, provenance) and sorted(annotated) == sorted(expected) and ordinal_same
    token = f"diff-based: class {cls} ({len(annotated)} keys) | provenance: {provenance[0] or 'no token'}"
    return ok, token, [
        f"W_1 sections: {len(w_1)}",
        "annotated: " + ", ".join(f"{p}:{s}" for p, s in annotated),
        f"ordinal strip resolves to the same key: {ordinal_same}",
    ]


def scenario_a2(repo: str) -> tuple[bool, str, list[str]]:
    """A2 — the B8 case: round-2 findings in *changed* sections only → no token either way.

    The round-2 key is chosen live from ``W_1`` minus round 1's keys, so it is a
    section the regeneration actually rewrote and round 1 did not raise
    (REQ-ARB-HARNESSP3-001's false positive stays removed).
    """
    w_1 = _replay_regeneration(repo)
    r1 = parse_round(arb_fixture("round-1.txt"))
    candidates = sorted(k for k in w_1 if k not in set(r1.keys) and k[1] not in ("*", "?"))
    if not candidates:
        return False, "no changed section outside round 1's keys", []
    path, sec = candidates[0]
    r2 = parse_round(
        f"VERDICT: APPROVE_WITH_FIXES\n- M1: a gap in a rewritten section — [{path}:{sec}] — affects —\n"
    )
    diff_based = arbitrate(r1, r2, w_1)
    provenance = arbitrate(r1, r2, {(ARB_PLAN_PATH, "*")})
    ok = diff_based == (None, []) and provenance == (None, [])
    return ok, f"diff-based: no token | provenance: no token ({sec})", [f"round-2 key: {path}:{sec}"]


def scenario_a3(repo: str) -> tuple[bool, str, list[str]]:
    """A3 — control: one round-2 key on a second file the loop never touched.

    Both readings raise `class b` with one key: the rule stays armed for a file
    outside the regeneration (REQ-ARB-HARNESSP4-001 re-stated).
    """
    w_1 = _replay_regeneration(repo)
    r1 = parse_round(arb_fixture("round-1.txt"))
    other = "docs/spec/harness-write-scope.md"
    r2 = parse_round(
        f"VERDICT: APPROVE_WITH_FIXES\n- M1: §Commit Ownership contradicts the plan — [{other}:§Commit Ownership] — affects [REQ-HARN-HARNESSP4-002]\n"
    )
    diff_based = arbitrate(r1, r2, w_1)
    provenance = arbitrate(r1, r2, {(ARB_PLAN_PATH, "*")})
    ok = diff_based == ("b", [(other, "§Commit Ownership")]) and provenance == diff_based
    return ok, f"diff-based: class b (1 key) | provenance: class {provenance[0]} (1 key)", [
        f"round-2 key: {other}:§Commit Ownership"
    ]


def scenario_a1_mi(repo: str) -> tuple[bool, str, list[str]]:
    """Mutation (m-i) — one `round-2.txt` line deleted in a temp copy makes A1 fail.

    A1 cannot pass vacuously: with one Material line gone the diff-based reading
    annotates one key, not two, so A1's asserted outcome no longer holds. The
    fixture on disk is untouched.
    """
    lines = arb_fixture("round-2.txt").splitlines(keepends=True)
    mutated = "".join(lines[:-1])  # drop the last Material line
    _, diff_based, provenance = _a1(repo, round2_text=mutated)
    ok = not _a1_holds(diff_based, provenance) and len(diff_based[1]) == 1
    return ok, f"A1 fails as required (annotated {len(diff_based[1])} of 2)", [
        "mutation: last round-2 Material line deleted in a temp copy"
    ]


def scenario_a1_mii(repo: str) -> tuple[bool, str, list[str]]:
    """Mutation (m-ii) — flipping `§Conventions` to a *changed* section makes A1 fail.

    A line is appended under `§Conventions` in a temp copy of the after-image, so
    the regeneration diff now covers it: the section enters `W_1` and only one key
    is annotated. The fixture on disk is untouched.
    """
    after = arb_fixture("after.md")
    marker = "\n## Conventions\n"
    if marker not in after:
        return False, "§Conventions heading not found in after.md", []
    mutated = after.replace(marker, marker + "\n<!-- m-ii: §Conventions flipped to a changed section -->\n", 1)
    _, diff_based, provenance = _a1(repo, after_text=mutated)
    ok = not _a1_holds(diff_based, provenance) and len(diff_based[1]) == 1
    return ok, f"A1 fails as required (annotated {len(diff_based[1])} of 2)", [
        "mutation: §Conventions rewritten in a temp copy of after.md"
    ]


def _dirty_two(repo: str) -> list[str]:
    """Two tracked paths made dirty *before* the dispatch — the harness-p5 shape."""
    write(repo, "docs/plan.md", "# Plan\nuncommitted work in the tree\n")
    write(repo, "src/recon/engine.py", "def run():\n    return 7  # uncommitted work\n")
    return ["docs/plan.md", "src/recon/engine.py"]


def scenario_g1(repo: str) -> tuple[bool, str, list[str]]:
    """Read-only leaf runs ``git stash`` then ``git stash pop`` -> GIT_STATE, VIOLATION.

    ``harness-write-scope.md`` §Git-State Observation, the harness-p5 incident: a
    read-only verifier stashed uncommitted work and the gate still rendered
    ``SCOPE: CLEAN`` — the porcelain delta is one-directional, so a *removal* of
    dirty lines is invisible to it. The pop restores the dirty set, so clause
    (ii) is empty here and clause (i) carries the finding: ``git stash`` sets
    ``ORIG_HEAD``, which was absent before the dispatch.
    """
    dirty = _dirty_two(repo)
    head, before, content_before = _begin(repo)
    state_before = git_state(repo)
    git(repo, "stash", "-q")
    git(repo, "stash", "pop", "-q")
    obs = observe(repo, head, before, content_before=content_before, state_before=state_before)
    f = render(SEQ_SCOPE_SRC, obs, "G1")
    restored = all(p in " ".join(snapshot(repo)) for p in dirty)  # the pop put the work back
    ok = (
        restored
        and obs.git_state is not None
        and "ORIG_HEAD" in obs.git_state
        and f.token == "SCOPE: VIOLATION (1 path)"
        and any(ln.strip().startswith("GIT_STATE") for ln in f.lines)
    )
    return ok, f.token, f.lines


def scenario_g2(repo: str) -> tuple[bool, str, list[str]]:
    """Read-only leaf runs ``git stash`` then ``git stash drop`` -> GIT_STATE, VIOLATION.

    The work is gone: the paths dirty at ``snapshot(before)`` are clean at
    ``snapshot(after)`` with no commit explaining it, so clause (ii) — the
    reverse porcelain delta minus the committed delta — is non-empty. Clause (i)
    adds the ``ORIG_HEAD`` drift the stash left behind.
    """
    dirty = _dirty_two(repo)
    head, before, content_before = _begin(repo)
    state_before = git_state(repo)
    git(repo, "stash", "-q")
    git(repo, "stash", "drop", "-q")
    obs = observe(repo, head, before, content_before=content_before, state_before=state_before)
    f = render(SEQ_SCOPE_SRC, obs, "G2")
    gone = all(p not in " ".join(snapshot(repo)) for p in dirty)
    ok = (
        gone
        and obs.git_state is not None
        and "dirty before and clean after with no commit" in obs.git_state
        and all(p in obs.git_state for p in dirty)
        and f.token == "SCOPE: VIOLATION (1 path)"
    )
    return ok, f.token, f.lines


def scenario_g3(repo: str) -> tuple[bool, str, list[str]]:
    """Implement leaf commits a path already dirty at ``snapshot(before)`` -> SCOPE: CLEAN.

    The legitimate case clause (ii) must not fire on: the path leaves the dirty
    set, but the committed delta explains it, and the subtraction empties the
    reverse delta. A normal implement leaf only *adds* porcelain lines, does not
    stash, does not switch branch and does not set ``ORIG_HEAD``.
    """
    write(repo, "docs/plan.md", "# Plan\ndirty before the dispatch\n")
    head, before, content_before = _begin(repo)
    state_before = git_state(repo)
    write(repo, "docs/plan.md", "# Plan\ndirty before the dispatch\nleaf tick\n")
    git(repo, "commit", "-q", "-am", "leaf: tick a plan task")
    obs = observe(repo, head, before, content_before=content_before, state_before=state_before)
    f = render(IMPLEMENT_SCOPE, obs, "G3")
    left_dirty_set = "docs/plan.md" not in " ".join(snapshot(repo))
    ok = (
        left_dirty_set  # the precondition clause (ii) would otherwise fire on
        and obs.git_state is None
        and f.token == "SCOPE: CLEAN"
        and any("IN" in ln and "docs/plan.md" in ln and "committed" in ln for ln in f.lines)
    )
    return ok, f.token, f.lines


def scenario_g4(repo: str) -> tuple[bool, str, list[str]]:
    """Orchestrator fan-out merge between two dispatches -> SCOPE: CLEAN.

    The merge is an orchestrator step that runs **outside** any leaf's
    observation window, so no snapshot pair spans it: the ``ORIG_HEAD`` it sets
    is already present at the second dispatch's ``snapshot(before)`` and compares
    equal at ``snapshot(after)``. The merge commit is also a descendant, so the
    ancestry check (c) still passes.
    """
    # A fan-out leaf's branch, committed outside the sequential window.
    git(repo, "branch", "-q", "fanout-g1")
    git(repo, "checkout", "-q", "fanout-g1")
    write(repo, "src/recon/engine.py", "def run():\n    return 1  # leaf work\n")
    git(repo, "commit", "-q", "-am", "leaf: recon work")
    git(repo, "checkout", "-q", "-")
    write(repo, "src/recon/other.py", "x = 1\n")
    git(repo, "add", "-A", "src/recon/other.py")
    git(repo, "commit", "-q", "-m", "orchestrator: bookkeeping")

    # Between the two dispatches: the orchestrator merges the leaf branch.
    git(repo, "merge", "-q", "--no-ff", "-m", "orchestrator: merge fanout-g1", "fanout-g1")
    merged = "orchestrator: merge fanout-g1" in git(repo, "log", "--format=%s", "-5").stdout

    # Dispatch 2 — its window opens after the merge.
    head, before, content_before = _begin(repo)
    state_before = git_state(repo)
    write(repo, "src/recon/engine.py", "def run():\n    return 2  # dispatch 2\n")
    obs = observe(repo, head, before, content_before=content_before, state_before=state_before)
    f = render(SEQ_SCOPE_SRC, obs, "G4")
    ok = (
        merged
        and state_before.orig_head == git_state(repo).orig_head  # set by the merge, equal across the window
        and obs.git_state is None
        and obs.history_rewrite is None
        and f.token == "SCOPE: CLEAN"
    )
    return ok, f.token, f.lines


def scenario_g5(repo: str) -> tuple[bool, str, list[str]]:
    """``ORIG_HEAD``: absent in both raises nothing; present in ``after`` only raises GIT_STATE.

    Absence is the legal empty value, so absent-in-both compares equal — the
    read never turns a repository that has simply never reset into a finding.
    """
    # Half 1 — ORIG_HEAD absent in both snapshots.
    head, before, content_before = _begin(repo)
    state_before = git_state(repo)
    write(repo, "src/recon/engine.py", "def run():\n    return 3\n")
    obs_absent = observe(repo, head, before, content_before=content_before, state_before=state_before)
    f_absent = render(SEQ_SCOPE_SRC, obs_absent, "G5")
    ok1 = (
        state_before.orig_head == ""
        and git_state(repo).orig_head == ""
        and obs_absent.git_state is None
        and f_absent.token == "SCOPE: CLEAN"
    )

    # Half 2 — the leaf sets ORIG_HEAD without moving HEAD or dirtying a path.
    head2, before2, content_before2 = _begin(repo)
    state_before2 = git_state(repo)
    git(repo, "reset", "-q", "--soft", "HEAD")
    obs_set = observe(repo, head2, before2, content_before=content_before2, state_before=state_before2)
    f_set = render(SEQ_SCOPE_SRC, obs_set, "G5")
    ok2 = (
        state_before2.orig_head == ""
        and git_state(repo).orig_head != ""
        and obs_set.git_state is not None
        and "ORIG_HEAD <none> ->" in obs_set.git_state
        and obs_set.history_rewrite is None  # HEAD did not move
        and f_set.token == "SCOPE: VIOLATION (1 path)"
    )

    ok = ok1 and ok2
    return ok, f"{f_absent.token} + {f_set.token}", f_absent.lines + f_set.lines


# ---------------------------------------------------------------------------
# harness-loop-control.md §Convergence Signal — L2 — scenarios L1-L9
# ---------------------------------------------------------------------------
#
# L2 is orchestrator-derived: nothing below adds a field to any leaf's RETURN:
# shape, nothing is written to disk, and the ledger is a plain in-memory object
# discarded when the scenario returns. The key rules are applied in the spec's
# order — shared id (primary), sectionless file, equal (file, section)
# (retained) — and the false-positive control is retained unchanged: in a file
# that HAS sections, a file-level-only match renders nothing.


@dataclass(frozen=True)
class ConvFinding:
    """One layer's finding, as the orchestrator already has it at a gate.

    ``section`` is what the finding's own ref names; whether a section key is
    *available* is decided by the key parser against the file itself
    (:func:`parser_sections`), never by the finding's say-so.
    """

    layer: str  # blue | chunk-verifier | review | red
    research_id: str
    gate: str
    file: str | None = None
    section: str | None = None
    cited_id: str | None = None  # a REQ-* or deviation-entry id


# Key rule 2's discriminator (harness-loop-control.md §Convergence Signal, red
# R3): a **record/data file** — a flat sequence of records with no addressable
# structure of any kind. These are the files for which "the whole file" is the
# only key that exists, which is what makes the file-level key meaningful there.
# A source file is deliberately NOT in this set: a ``.py`` module has functions
# and classes, so the key parser finding no ``#``-headings in it is a limitation
# of the parser, not a property of the file.
DATA_SUFFIXES = (".jsonl", ".ndjson", ".csv", ".tsv", ".log", ".txt")


def parser_sections(repo: str, path: str) -> list[str]:
    """Sections the arbitration key parser finds in ``path`` — empty when there are none.

    Markdown only: headings are the only section structure the key parser reads.
    A non-Markdown file yields ``[]`` here, which is **not** on its own a licence
    to key on the file (see :func:`file_structure`).
    """
    full = os.path.join(repo, path)
    if not path.endswith(MARKDOWN_SUFFIXES) or not os.path.isfile(full):
        return []
    with open(full, encoding="utf-8") as fh:
        return [name for _, name in _headings(fh.read().splitlines())]


# file_structure() return values.
ABSENT_PATH = "absent"  # the path is not a file in the checkout — no key at all
STRUCTURELESS = "structureless"  # a record/data file, or Markdown with no headings
STRUCTURED = "structured"  # anything else: it has structure, whether or not we parse it


def file_structure(repo: str, path: str) -> str:
    """Classify ``path`` for key rule 2 (red R3, R4).

    ``ABSENT_PATH``    — not a file in this checkout. A finding may name a path
                         that is a typo, a rename, or a file living only in a
                         fan-out worktree; absence must not silently discard the
                         section discriminator and let two findings on DIFFERENT
                         sections of it cluster (red R4).
    ``STRUCTURELESS``  — a ``DATA_SUFFIXES`` record file, or a Markdown file in
                         which the fence-aware parser finds no heading. The whole
                         file is the only key that exists.
    ``STRUCTURED``     — everything else, including source files. Two unrelated
                         findings in a 1000-line module are not one root cause
                         (red R3), so no file-level key is minted for them.
    """
    if not os.path.isfile(os.path.join(repo, path)):
        return ABSENT_PATH
    if path.endswith(DATA_SUFFIXES):
        return STRUCTURELESS
    if path.endswith(MARKDOWN_SUFFIXES) and not parser_sections(repo, path):
        return STRUCTURELESS
    return STRUCTURED


def convergence_key(repo: str, f: ConvFinding) -> tuple[str, ...] | None:
    """The finding's cluster key under the three key rules, applied in order."""
    if f.cited_id:  # key rule 1 — shared id (primary), whatever the file and section
        return ("id", f.cited_id)
    if f.file is None:
        return None
    structure = file_structure(repo, f.file)
    if structure == ABSENT_PATH:
        # red R4: a path absent from the checkout yields NO cluster key. It is
        # not evidence of structurelessness, so it must not collapse to one.
        return None
    if structure == STRUCTURELESS:  # key rule 2 — structureless file
        return ("file", f.file)
    if f.section is None:
        # A sectioned file matched at file level only: the retained
        # false-positive control renders nothing.
        return None
    # key rule 3 — equal (file, section), reusing the ratified leading-ordinal strip
    return ("file-section", f.file, section_name(f.section.lstrip("§")))


def convergence_line(key: tuple[str, ...], layers: list[str]) -> str:
    """The own-line 6c token, naming the key in whichever shape formed the cluster."""
    display = key[1] if key[0] in ("id", "file") else f"{key[1]} §{key[2].lstrip('§')}"
    return f"CONVERGENCE: {display} ({', '.join(layers)}) — {len(layers)} layers"


class ConvergenceLedger:
    """Session-scoped, in-memory finding ledger — three fields per finding.

    The ledger belongs to one cycle (``research_id``), which is how condition
    (ii) is enforced: a finding stamped with another cycle's id is never
    recorded. Entries hold ``key``, ``layer`` and ``gate`` only — no finding
    text — and nothing is written to disk.
    """

    def __init__(self, research_id: str) -> None:
        self.research_id = research_id
        self.entries: list[dict] = []
        self.rendered: set[tuple[str, ...]] = set()

    def record(self, repo: str, f: ConvFinding) -> list[str]:
        """Record one finding; return the ``CONVERGENCE:`` lines this gate renders."""
        if f.research_id != self.research_id:  # condition (ii)
            return []
        key = convergence_key(repo, f)
        if key is None:
            return []
        self.entries.append({"key": key, "layer": f.layer, "gate": f.gate})
        layers: list[str] = []
        for e in self.entries:  # condition (i) — different layers or second-executors
            if e["key"] == key and e["layer"] not in layers:
                layers.append(e["layer"])
        if len(layers) < 2 or key in self.rendered:
            return []  # a third layer joining a rendered cluster does not re-render it
        self.rendered.add(key)
        return [convergence_line(key, layers)]


def render_gate(plan_line: str, conv_lines: list[str], telemetry_line: str) -> list[str]:
    """A stage gate block: 6b, then 6c, then 7, then the options."""
    return [plan_line, *conv_lines, telemetry_line,
            "options: proceed │ loop-back-to-fix │ stop"]


def _conv_repo(repo: str) -> None:
    """Write the files the key parser is asked about (a sectioned one and two sectionless)."""
    write(repo, "docs/spec/telemetry.md",
          "# Telemetry\n\n## Writer rule\n\ntext\n\n## Reader rule\n\ntext\n")
    write(repo, "docs/ws/harness/notes.jsonl", '{"rec": 1}\n{"rec": 2}\n')
    write(repo, "tools/reader.py", "def summarize():\n    return 0\n")
    # A Markdown file with NO real heading whose only ``#`` lines live inside a
    # fenced shell block (red R5 fixture).
    write(repo, "docs/ws/harness/fenced.md",
          "Intro prose, no heading anywhere.\n\n```sh\n# run the sweep\npython3 tools/gc.py\n```\n\nmore prose\n")


def _conv_run(repo: str, findings: list[ConvFinding], rid: str = "RS-HARNESSP6-001") -> list[str]:
    """Feed findings to a fresh ledger in order; return every line rendered."""
    ledger = ConvergenceLedger(rid)
    lines: list[str] = []
    for f in findings:
        lines.extend(ledger.record(repo, f))
    return lines


def scenario_l1(repo: str) -> tuple[bool, str, list[str]]:
    """Key rule 1 (primary): different layers, same `REQ-*` id, different sections -> cluster."""
    _conv_repo(repo)
    lines = _conv_run(repo, [
        ConvFinding("review", "RS-HARNESSP6-001", "specs", "docs/spec/telemetry.md",
                    "§Writer rule", "REQ-TELEM-HARNESSP6-001"),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", "docs/ws/harness/verification.md",
                    "§Issues Found", "REQ-TELEM-HARNESSP6-001"),
    ])
    ok = len(lines) == 1 and lines[0].startswith("CONVERGENCE: REQ-TELEM-HARNESSP6-001") \
        and lines[0].endswith("2 layers")
    return ok, lines[0] if lines else "no line", lines


def scenario_l2(repo: str) -> tuple[bool, str, list[str]]:
    """Key rule 2: different layers naming one sectionless file -> cluster on the file alone.

    The `.jsonl` shape of the convergence the Chunk 8 replay found and a
    section-granular key structurally cannot catch: a JSONL data file has no
    heading for a `(file, section)` key to be equal on.
    """
    _conv_repo(repo)
    path = "docs/ws/harness/notes.jsonl"
    ok_parser = parser_sections(repo, path) == []
    lines = _conv_run(repo, [
        ConvFinding("red", "RS-HARNESSP6-001", "verify", path),
        ConvFinding("blue", "RS-HARNESSP6-001", "verify", path),
    ])
    ok = ok_parser and len(lines) == 1 and lines[0] == \
        f"CONVERGENCE: {path} (red, blue) — 2 layers"
    return ok, lines[0] if lines else "no line", lines


def scenario_l3(repo: str) -> tuple[bool, str, list[str]]:
    """Retained noise guard: different layers, same SECTIONED file, different sections -> nothing.

    The decisive false-positive control: two findings in two sections of one
    prose file are not one root cause, and key rule 2 does not reach a file the
    parser does find sections in.
    """
    _conv_repo(repo)
    ok_parser = parser_sections(repo, "docs/spec/telemetry.md") == ["§Telemetry", "§Writer rule",
                                                                   "§Reader rule"]
    lines = _conv_run(repo, [
        ConvFinding("review", "RS-HARNESSP6-001", "specs", "docs/spec/telemetry.md", "§Writer rule"),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", "docs/spec/telemetry.md", "§Reader rule"),
    ])
    # and the file-level-only match in that same sectioned file renders nothing either
    file_only = _conv_run(repo, [
        ConvFinding("review", "RS-HARNESSP6-001", "specs", "docs/spec/telemetry.md"),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", "docs/spec/telemetry.md"),
    ])
    ok = ok_parser and lines == [] and file_only == []
    return ok, "no cluster (sectioned file, different sections)", lines + file_only


def scenario_l4(repo: str) -> tuple[bool, str, list[str]]:
    """Condition (i): the SAME layer twice on one key -> no cluster."""
    _conv_repo(repo)
    lines = _conv_run(repo, [
        ConvFinding("red", "RS-HARNESSP6-001", "verify", "docs/spec/telemetry.md", "§Writer rule"),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", "docs/spec/telemetry.md", "§Writer rule"),
    ])
    same_id = _conv_run(repo, [
        ConvFinding("blue", "RS-HARNESSP6-001", "implement", cited_id="REQ-HARN-HARNESSP6-002"),
        ConvFinding("blue", "RS-HARNESSP6-001", "verify", cited_id="REQ-HARN-HARNESSP6-002"),
    ])
    ok = lines == [] and same_id == []
    return ok, "no cluster (same layer)", lines + same_id


def scenario_l5(repo: str) -> tuple[bool, str, list[str]]:
    """Key rule 3 (retained, demoted): different layers, equal `(file, section)` -> cluster.

    Reuses the ratified leading-ordinal strip — `§3. Writer rule` and
    `§Writer rule` are the same key (REQ-ARB-HARNESSP5-003). No recall claim
    rests on this rule; the Chunk 8 replay measured it at zero clusters over
    three cycles.
    """
    _conv_repo(repo)
    lines = _conv_run(repo, [
        ConvFinding("chunk-verifier", "RS-HARNESSP6-001", "implement",
                    "docs/spec/telemetry.md", "§3. Writer rule"),
        ConvFinding("review", "RS-HARNESSP6-001", "implement",
                    "docs/spec/telemetry.md", "§Writer rule"),
    ])
    ok = lines == ["CONVERGENCE: docs/spec/telemetry.md §Writer rule "
                   "(chunk-verifier, review) — 2 layers"]
    return ok, lines[0] if lines else "no line", lines


def scenario_l6(repo: str) -> tuple[bool, str, list[str]]:
    """Condition (ii): two layers, same key, DIFFERENT `research_id` -> no cluster."""
    _conv_repo(repo)
    lines = _conv_run(repo, [
        ConvFinding("review", "RS-HARNESSP6-001", "specs", cited_id="REQ-ORCH-HARNESSP6-001"),
        ConvFinding("red", "RS-HARNESSP5-001", "verify", cited_id="REQ-ORCH-HARNESSP6-001"),
    ])
    return lines == [], "no cluster (different research_id)", lines


def scenario_l7(repo: str) -> tuple[bool, str, list[str]]:
    """Gate rendering: the line sits between 6b (`PLAN:`) and 7 (`TELEMETRY:`), `proceed` available."""
    _conv_repo(repo)
    conv = _conv_run(repo, [
        ConvFinding("review", "RS-HARNESSP6-001", "verify", cited_id="REQ-ORCH-HARNESSP6-001"),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", cited_id="REQ-ORCH-HARNESSP6-001"),
    ])
    block = render_gate("PLAN: INCOMPLETE (6 of 7 ticked)", conv, "TELEMETRY: rec 4")
    idx = [i for i, ln in enumerate(block) if ln.startswith("CONVERGENCE:")]
    ok = (
        len(conv) == 1
        and len(idx) == 1
        and block[idx[0] - 1].startswith("PLAN:")
        and block[idx[0] + 1].startswith("TELEMETRY:")
        and "proceed" in block[-1]  # informational: the line never withholds proceed
        and not any(o in block[idx[0]] for o in ("│", "proceed"))  # no option set of its own
    )
    return ok, block[idx[0]] if idx else "no line", block


def scenario_l8(repo: str) -> tuple[bool, str, list[str]]:
    """Invariant 1 demonstrated: a run in which a cluster fires adds no path under `docs/`."""
    _conv_repo(repo)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "convergence fixture files")
    before = git(repo, "ls-files", "docs/").stdout.splitlines()
    conv = _conv_run(repo, [
        ConvFinding("blue", "RS-HARNESSP6-001", "implement", "docs/ws/harness/notes.jsonl"),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", "docs/ws/harness/notes.jsonl"),
    ])
    after = git(repo, "ls-files", "docs/").stdout.splitlines()
    ok = len(conv) == 1 and before == after
    return ok, f"cluster fired, git ls-files docs/ unchanged ({len(after)} paths)", conv


def scenario_l9(repo: str) -> tuple[bool, str, list[str]]:
    """Q-IMPL-HARNESSP6-001: a THIRD layer joining a rendered cluster does not re-render it."""
    _conv_repo(repo)
    ledger = ConvergenceLedger("RS-HARNESSP6-001")
    first = ledger.record(repo, ConvFinding("review", "RS-HARNESSP6-001", "specs",
                                            cited_id="REQ-HARN-HARNESSP6-002"))
    second = ledger.record(repo, ConvFinding("red", "RS-HARNESSP6-001", "verify",
                                             cited_id="REQ-HARN-HARNESSP6-002"))
    third = ledger.record(repo, ConvFinding("blue", "RS-HARNESSP6-001", "verify",
                                            cited_id="REQ-HARN-HARNESSP6-002"))
    ok = first == [] and len(second) == 1 and third == [] and len(ledger.entries) == 3
    return ok, second[0] if second else "no line", second + third


def scenario_l10(repo: str) -> tuple[bool, str, list[str]]:
    """Red R3: key rule 2 is gated on a structureless file, not on "not Markdown".

    Two unrelated findings anywhere in a source module are not one root cause —
    a ``.py`` file has functions and classes, so the key parser finding no
    ``#``-headings in it is a limitation of the parser, not a property of the
    file. Mutation control: reverting the gate to "not Markdown" makes the
    ``.py`` pair cluster and this scenario fail, while the ``.jsonl`` control
    below must keep clustering so the fix does not simply delete key rule 2.
    """
    _conv_repo(repo)
    py_noise = _conv_run(repo, [
        ConvFinding("review", "RS-HARNESSP6-001", "implement", "tools/reader.py"),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", "tools/reader.py"),
    ])
    # the rule it exists for is preserved: red and blue on one record/data file
    data_control = _conv_run(repo, [
        ConvFinding("red", "RS-HARNESSP6-001", "verify", "docs/ws/harness/notes.jsonl"),
        ConvFinding("blue", "RS-HARNESSP6-001", "verify", "docs/ws/harness/notes.jsonl"),
    ])
    ok = (
        file_structure(repo, "tools/reader.py") == STRUCTURED
        and file_structure(repo, "docs/ws/harness/notes.jsonl") == STRUCTURELESS
        and py_noise == []
        and len(data_control) == 1
    )
    return ok, f"py-noise {len(py_noise)} cluster(s), data control {len(data_control)}", py_noise + data_control


def scenario_l11(repo: str) -> tuple[bool, str, list[str]]:
    """Red R4: a path absent from the checkout yields NO cluster key.

    A finding may name a typo, a renamed path, or a file living only in a
    fan-out worktree. Classifying it as structureless would cluster two findings
    naming DIFFERENT sections of it — exactly the case L3 asserts must not
    cluster. Mutation control: returning ``[]`` for a missing path makes both
    runs below cluster.
    """
    _conv_repo(repo)
    gone = "docs/spec/gone.md"
    diff_sections = _conv_run(repo, [
        ConvFinding("review", "RS-HARNESSP6-001", "specs", gone, "§A"),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", gone, "§B"),
    ])
    no_sections = _conv_run(repo, [
        ConvFinding("review", "RS-HARNESSP6-001", "specs", gone),
        ConvFinding("red", "RS-HARNESSP6-001", "verify", gone),
    ])
    ok = (
        file_structure(repo, gone) == ABSENT_PATH
        and convergence_key(repo, ConvFinding("red", "RS-HARNESSP6-001", "verify", gone, "§A")) is None
        and diff_sections == []
        and no_sections == []
    )
    return ok, "no cluster (absent path)", diff_sections + no_sections


def scenario_l12(repo: str) -> tuple[bool, str, list[str]]:
    """Red R5: ``_headings()`` is fence-aware, so a fenced ``#`` is not a section.

    A Markdown file whose only ``#`` line is a shell comment inside a fenced
    block has no sections, so key rule 2 applies and a genuine two-layer
    convergence on it renders. Mutation control: a fence-blind ``_headings``
    reports ``['§run the sweep']``, the file reads as sectioned, and the cluster
    is silently dropped.
    """
    _conv_repo(repo)
    fenced = "docs/ws/harness/fenced.md"
    lines = _conv_run(repo, [
        ConvFinding("red", "RS-HARNESSP6-001", "verify", fenced),
        ConvFinding("blue", "RS-HARNESSP6-001", "verify", fenced),
    ])
    # and a file that has BOTH a fenced ``#`` and a real heading keeps only the real one
    write(repo, "docs/ws/harness/mixed.md",
          "# Real\n\n```\n# not a heading\n```\n\n## Second\n")
    ok = (
        parser_sections(repo, fenced) == []
        and file_structure(repo, fenced) == STRUCTURELESS
        and parser_sections(repo, "docs/ws/harness/mixed.md") == ["§Real", "§Second"]
        and lines == [f"CONVERGENCE: {fenced} (red, blue) — 2 layers"]
    )
    return ok, lines[0] if lines else "no line", lines


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
    ("F13", "RED_BREAK fix with no open chunk: ## Post-cycle Fixes append only", scenario_f13),
    ("F14", "strict set: one path in committed AND content delta, counted once", scenario_f14),
    ("F15", "rename across the scope boundary: one -z R record, both paths observed", scenario_f15),
    ("F16", "path with a space: -z keeps one record, observed and rendered once", scenario_f16),
    ("G1", "git-state: read-only leaf stashes then pops (ORIG_HEAD drift)", scenario_g1),
    ("G2", "git-state: read-only leaf stashes then drops (reverse porcelain delta)", scenario_g2),
    ("G3", "git-state: implement leaf commits an already-dirty path (committed delta subtracted)", scenario_g3),
    ("G4", "git-state: orchestrator fan-out merge between two dispatches (outside the window)", scenario_g4),
    ("G5", "git-state: ORIG_HEAD absent in both vs present in after only", scenario_g5),
    ("C1", "COMMIT: sequential omission (2 of 3 staged), then amended", scenario_c1),
    ("C2", "COMMIT: sequential inverse (stray.txt landed, not observed)", scenario_c2),
    ("C3", "COMMIT: fan-out fast-forward of a two-commit leaf (range vs git show)", scenario_c3),
    ("C4", "COMMIT: fan-out true merge after a bookkeeping commit", scenario_c4),
    ("C5", "COMMIT: conflict -> abort -> redo compares the redo's own sets", scenario_c5),
    ("C6", "COMMIT: path with a space counted once (-z landed operand, NUL split)", scenario_c6),
    ("A1", "ARB: round 2 on the regenerated plan's unchanged sections (diff-based vs provenance)", scenario_a1),
    ("A2", "ARB: round-2 findings in changed sections only -> no token either way", scenario_a2),
    ("A3", "ARB: one round-2 key on an untouched second file -> class b under both readings", scenario_a3),
    ("A1m-i", "ARB mutation: a deleted round-2 line makes A1 fail", scenario_a1_mi),
    ("A1m-ii", "ARB mutation: §Conventions flipped to a changed section makes A1 fail", scenario_a1_mii),
    ("L1", "L2 key rule 1: different layers, same REQ-* id, different sections -> cluster", scenario_l1),
    ("L2", "L2 key rule 2: different layers, one sectionless (.jsonl) file -> cluster on the file", scenario_l2),
    ("L3", "L2 noise guard: sectioned file, different sections (and file-level only) -> nothing", scenario_l3),
    ("L4", "L2 condition (i): the same layer twice -> no cluster", scenario_l4),
    ("L5", "L2 key rule 3 retained: equal (file, section), ordinal-stripped -> cluster", scenario_l5),
    ("L6", "L2 condition (ii): same key, different research_id -> no cluster", scenario_l6),
    ("L7", "L2 rendering: CONVERGENCE: between PLAN: (6b) and TELEMETRY: (7), proceed available", scenario_l7),
    ("L8", "L2 invariant: a run in which a cluster fires adds no path under docs/", scenario_l8),
    ("L9", "L2 Q-IMPL-HARNESSP6-001: a third layer does not re-render the cluster", scenario_l9),
    ("L10", "L2 red R3: key rule 2 is gated on a structureless file, not on non-Markdown", scenario_l10),
    ("L11", "L2 red R4: a path absent from the checkout yields no cluster key", scenario_l11),
    ("L12", "L2 red R5: _headings() is fence-aware, so a fenced # is not a section", scenario_l12),
]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scope-check-selftest.py",
        description=(
            f"Replay the {len(SCENARIOS)} write-scope scenarios of docs/spec/harness-write-scope.md "
            "§Verification, docs/spec/telemetry.md §Third Observation, "
            "docs/spec/arbitrated-handoff.md §Section Resolution, "
            "docs/spec/harness-loop-control.md §Convergence Signal — L2 and "
            "docs/spec/dispatch-snapshot-base.md §Snapshot Base Rule in throwaway git repos. "
            "Exit 0 when all pass."
        ),
    )
    # Accepted for parity with ``skill-lint.py --self-test`` and the spec's
    # §Verification command; the self-test is this script's only mode
    # (harness-commit-fidelity.md Q-IMPL-HARNESSP4-003).
    parser.add_argument("--self-test", action="store_true", help="run the fixtures (the default and only mode)")
    parser.add_argument("-v", "--verbose", action="store_true", help="print each finding block")
    parser.add_argument("--keep", action="store_true", help="keep the temp repos (prints the path)")
    args = parser.parse_args(argv)

    if shutil.which("git") is None:
        print("FAIL: git binary not found", file=sys.stderr)
        return 1

    root = tempfile.mkdtemp(prefix="scope-selftest-")
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
