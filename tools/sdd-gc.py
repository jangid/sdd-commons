#!/usr/bin/env python3
"""sdd-gc — drift sweep for the SDD docs corpus (`docs/**`).

`tools/sdd-skill-lint.py` keeps `skills/` honest; this sibling sweeps `docs/`
for the mechanical drift that accumulates between cycles: dead cross-links,
missing ids, orphaned Q-IMPL entries, index/directory mismatches and
`plan-history` naming slips. It re-implements rules already stated as prose in
the skills and specs — it never invents one (`docs/spec/drift-sweep.md`).

Three sweep classes (rule ids in brackets):

  delegated  sweeps 1-5, obtained by INVOKING tools/sdd-skill-lint.py as a
             subprocess and passing its findings through [lint]; under
             marker 4 the kickoff field check [kickoff-fields] is gc's own
             (docs/ws/<id>/kickoff.md carries date: and research_id:) and is
             seen at sdd-orchestrate entry / DONE, the two cadence moments
  gc         sweeps 6-14, scoped to docs/**:
               6  cross-links + id existence      [xlink-dead] fail, [id-missing] fail
               7  staleness chain                 [stale-chain] warn
               8  Q-IMPL referenced, undefined    [qimpl-undefined] fail
               9  Q-IMPL defined, unreferenced    [qimpl-unreferenced] info
              10  Q-IMPL Spec reference / chain   [qimpl-broken-ref] warn
              11  empty traceability cells        [trace-empty] warn
              12  aggregate == regenerate(per-ws) [traceability-aggregate] warn (marker 4)
              13  index <-> directory             [index-research] fail, [index-requirements] fail,
                                                  [spec-approval] fail scoped / warn unscoped
              14  plan-history naming             [plan-history-name] fail
  excluded   sweep 15 — new drift of skill text from spec wording and semantic
             orphaning are NOT mechanical: review / dogfooding territory.

Q-IMPL counting rule (pinned; RS-HARNESSP2-001 Q4, `drift-sweep.md`
§Q-IMPL Counting Rule):

  * definition — a line matching `^### Q-IMPL-[A-Z0-9-]+` under docs/spec/**
  * reference  — any other occurrence of `Q-IMPL-[A-Z0-9]+(-\\d+)?` under docs/,
    skills/, agents/, tools/ EXCLUDING
      - docs/research/** (research cites foreign-repo ids);
      - id-format placeholders `Q-IMPL-NNN`, `Q-IMPL-1`, `Q-IMPL-ISSUE42*`,
        `Q-IMPL-ISSUE57-001`, and any id whose <WS> token is neither a
        directory under docs/ws/ nor absent (legacy bare counter);
      - occurrences inside fenced code blocks or inline backticks — the same
        skip the linter's resolve_backtick_path() applies, so illustrative ids
        in templates never count; a span may wrap one line break, and
        double-quoted literals ("…") are skipped the same way (the research's
        "fenced/quoted examples" — `Q-IMPL-HARNESSP2-054`);
      - the definition heading lines themselves (the `grep -v '### Q-IMPL-'`
        step of the reference commands).
  * ids may be legacy (`Q-IMPL-083`) or workstream-prefixed
    (`Q-IMPL-HARNESSP2-001`, `ws-ids.md`).
  * classes: both = defined and referenced; defined-only -> info (ii);
    referenced-only -> fail (i); (iii) over definitions: the entry's
    `**Spec reference**: §…` heading must exist in the same file after ordinal
    stripping, and a `[superseded by Q-IMPL-X]` note must name a defined id.

Reference commands (RS-HARNESSP2-001 Q4), whose raw counts this tool refines
with the fence/backtick and <WS>-token exclusions:

  # definitions -> 28
  grep -rhoE '^### Q-IMPL-[A-Z0-9-]+' docs/spec | sed 's/^### //' | sort -u
  # references (distinct ids, heading lines dropped) -> 28 raw, 23 after dropping the 5 placeholders
  grep -rHnE 'Q-IMPL-[A-Z0-9]+(-[0-9]+)?' docs skills agents tools --exclude-dir=research \\
    | grep -vE ':[0-9]+:### Q-IMPL-' | grep -oE 'Q-IMPL-[A-Z0-9]+(-[0-9]+)?' | sort -u
  # then: comm -12 (both) -> 20; comm -23 (defined only) -> 8; comm -13 (referenced only) -> 3, all template examples

Reference values on 2026-09-17 at commit 5e6142b (not pins): 28 definitions,
20 both, 8 defined-only, 0 referenced-only; template-example ids
`Q-IMPL-003` / `Q-IMPL-007` / `Q-IMPL-021` skipped.

Finding shape is the linter's, verbatim — `<file>:<line>: [<rule>] <msg>` plus
an indented `fix:` line; `WARN ` / `INFO ` prefixes for the lower tiers; the
summary line (`OK: N sweep(s) clean, W warning(s), I info` or `FAIL: F
finding(s), W warning(s), I info`) is always the last line of stdout.

Usage:
  tools/sdd-gc.py [--report] [--fast] [--workstream <id>] [--root <path>]
  tools/sdd-gc.py --fix <rule> [--workstream <id>] [--root <path>]
  tools/sdd-gc.py --self-test | --help

Exit codes: 0 = no fail finding; 1 = at least one fail finding;
2 = usage / repository error (not a git repository, missing docs/, unknown or
non-fixable --fix rule, linter missing).

`--fix <rule>` applies exactly one whitelisted rewrite (FIXABLE below —
`drift-sweep.md` §`--fix` Whitelist): xlink-dead (unique-candidate link
repair), index-requirements (ID-sorted Files-table row insertion),
traceability-aggregate (deterministic aggregate regeneration) and
plan-history-name (date-prefix rename).  Every fix prints the paths it changed
("no changes" otherwise), is a no-op on a second run, never touches a
`last_updated` field (dates are the owning skill's job — rewriting one would
mask the staleness it signals, so `stale-chain` is never fixable) and never
writes under `docs/ws/<other-id>/` when `--workstream <id>` is given.

gc never reads `.sdd/`, is never a phase-detection input, never creates a
plan task and never writes outside a `--fix` rule's whitelist.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Rule tables.  gc carries NO copy of the linter's FORBIDDEN / REQUIRED tables —
# skill-side rules are obtained by invoking the linter (sweep_lint).
# ---------------------------------------------------------------------------

# Rules `--fix` may rewrite (drift-sweep.md §`--fix` Whitelist).  Exactly these
# four; any other rule — known or not — exits 2 `not a fixable rule`.
# `stale-chain` is deliberately absent: dates are never auto-fixed.
FIXABLE = ["xlink-dead", "index-requirements", "traceability-aggregate", "plan-history-name"]

# Every rule id gc can emit, by class, for `--help` and for `--fix` validation.
DELEGATED_RULES = ["lint", "kickoff-fields"]   # kickoff-fields is gc-emitted under marker 4
GC_RULES = [
    "xlink-dead", "id-missing", "stale-chain", "qimpl-undefined",
    "qimpl-unreferenced", "qimpl-broken-ref", "trace-empty",
    "traceability-aggregate", "index-research", "index-requirements",
    "spec-approval", "plan-history-name",
]
ALL_RULES = DELEGATED_RULES + GC_RULES

# Placeholder ids that document the id FORMAT and never count as references.
PLACEHOLDER_IDS = {"Q-IMPL-NNN", "Q-IMPL-1", "Q-IMPL-ISSUE57-001"}
PLACEHOLDER_PREFIXES = ("Q-IMPL-ISSUE42",)

QIMPL_RE = re.compile(r"Q-IMPL-[A-Z0-9]+(?:-\d+)?")
QIMPL_DEF_RE = re.compile(r"^### (Q-IMPL-[A-Z0-9-]+)")
REQ_ID_RE = re.compile(r"REQ-[A-Z]+(?:-[A-Z0-9]+)?-\d+")
RS_ID_RE = re.compile(r"RS-(?:[A-Z][A-Z0-9]*-)?\d+")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")      # the linter's link regex
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")               # the linter's code regex
SEE_RE = re.compile(r"\(see ([^)]*)\)")
MD_TOKEN_RE = re.compile(r"[\w./-]+\.md(?:#[\w-]+)?")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ARCHIVE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*\.md$")

# Fixed remediation strings.
XLINK_FIX = "correct the relative path or create the target file"
ANCHOR_FIX = "point the anchor at an existing heading (anchors are matched after ordinal stripping)"
INDEX_FIX_RS = "add the row to docs/research/index.md or remove the stray RS-* directory"
INDEX_FIX_REQ = "add the Files-table row at its ID-sorted position or remove the stray category file"
ARCHIVE_FIX = ("rename to {YYYY-MM-DD}-{reason}.md (date from last_updated or the commit date); "
               "`-replan-` is reserved for sdd-replan archives")
STALE_FIX = ("update the downstream artifact through its owning skill and bump its last_updated "
             "there — dates are never auto-fixed (route: record | ignore at DONE)")
TRACE_FIX = "fill the cell in the owning docs/ws/<id>/traceability.md (sdd-implement) and regenerate the aggregate"
AGG_FIX = "run tools/sdd-gc.py --fix traceability-aggregate (regenerates from docs/ws/*/traceability.md)"
KICKOFF_FIX = "add `date: YYYY-MM-DD` and `research_id: RS-…` to the kickoff frontmatter (sdd-orchestrate KICKOFF)"

# Canonical aggregate table header (ws-traceability.md, Workstream = 3rd column).
AGG_HEADER = ("| Requirement | Spec | Workstream | Test | Implementation | Verified |",
              "|-------------|------|------------|------|----------------|----------|")
AGG_PREAMBLE = """---
regenerated_from: docs/ws/*/traceability.md
---

# Traceability Matrix

Derived aggregate (marker 4, `docs/spec/ws-traceability.md`): shipped legacy rows
(blank Workstream, shipped order preserved) followed by every
`docs/ws/<id>/traceability.md` row, stable-sorted by requirement id. Regenerated
wholesale — never hand-edited; per-workstream edits go in the owning
`docs/ws/<id>/traceability.md`.

"""


# ---------------------------------------------------------------------------
# Small text helpers (stdlib only).
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str | None:
    """UTF-8 text of a file, or None for binaries / unreadable files."""
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


# Inline code and double-quoted literals may wrap across one line break in
# prose; both are illustrative spans (the linter's backtick skip, RS-HARNESSP2-001
# Q4 "fenced/quoted examples").  Bounded by a blank line so an unbalanced
# delimiter cannot swallow a section.
SPAN_RE = re.compile(r"`(?:[^`\n]|\n(?!\n))*`|\"(?:[^\"\n]|\n(?!\n))*\"")


def visible_lines(text: str) -> list[tuple[int, str]]:
    """(line_no, line) pairs outside fenced code, with inline-code and quoted
    spans blanked (newlines kept, so line numbers stay true)."""
    # Fences first (line-based, blanked so line numbers and blank-line span
    # bounds survive); a fence marker's own backticks must never seed a span.
    kept: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            kept.append("")
            continue
        kept.append("" if in_fence else line)
    joined = SPAN_RE.sub(lambda m: "``" + "\n" * m.group(0).count("\n"), "\n".join(kept))
    return [(no, line) for no, line in enumerate(joined.split("\n"), 1) if line]


def frontmatter(text: str) -> dict[str, object]:
    """Minimal YAML frontmatter: scalars, `[a, b]` flow lists, `- x` block lists."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    fm: dict[str, object] = {}
    key: str | None = None
    for raw in text[3:end].splitlines():
        if not raw.strip():
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", raw)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                fm[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            elif val == "":
                fm[key] = []          # block list follows (or an empty value)
            else:
                fm[key] = val.strip("'\"")
        elif raw.lstrip().startswith("- ") and key and isinstance(fm.get(key), list):
            fm[key].append(raw.lstrip()[2:].strip().strip("'\""))  # type: ignore[union-attr]
    return fm


def headings(text: str) -> list[tuple[int, str]]:
    """(line_no, heading text) for every Markdown heading outside fences."""
    out = []
    in_fence = False
    for no, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            out.append((no, m.group(2)))
    return out


def strip_ordinal(title: str) -> str:
    """Drop leading list ordinals and `Step N:` / `Check N:` style prefixes."""
    t = re.sub(r"^\s*\d+[.)]?\s+", "", title)
    t = re.sub(r"^(Step|Check|Phase|Chunk|Part)\s+\d+[a-z]?\s*[:.—-]?\s*", "", t, flags=re.I)
    return t.strip()


def norm_title(title: str) -> str:
    """Comparison key for a heading or a `§…` token: ordinals, trailing
    `(REQ-…)` notes, dash-separated qualifiers, backticks and punctuation gone."""
    t = strip_ordinal(title)
    t = re.split(r"\s+[—–-]\s+", t)[0]
    t = re.sub(r"\((?:REQ|RS|Q-IMPL)[^)]*\)", "", t)
    t = t.replace("`", "").lower()
    return re.sub(r"[^a-z0-9]+", "", t)


def slug(title: str) -> str:
    """GitHub-style anchor slug."""
    t = re.sub(r"[^\w\s-]", "", title.strip().lower())
    return re.sub(r"\s+", "-", t)


def titles_match(token: str, heading: str) -> bool:
    a, b = norm_title(token), norm_title(heading)
    if not a or not b:
        return False
    return a == b or (min(len(a), len(b)) >= 5 and (a.startswith(b) or b.startswith(a)))


def ws_token(name: str) -> str:
    """`<WS>` id segment of a workstream directory name (`harness-p2` -> HARNESSP2)."""
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def compress_ids(ids: list[str]) -> str:
    """`REQ-AA-X-001, REQ-AA-X-002, REQ-AA-X-003` -> `REQ-AA-X-001..003`; runs
    per prefix, gaps kept as separate items (the Files-table convention)."""
    groups: dict[str, list[int]] = {}
    for i in ids:
        prefix, _, n = i.rpartition("-")
        groups.setdefault(prefix, []).append(int(n))
    out = []
    for prefix, nums in groups.items():
        nums = sorted(set(nums))
        start = prev = nums[0]
        for n in nums[1:] + [None]:  # type: ignore[list-item]
            if n is not None and n == prev + 1:
                prev = n
                continue
            out.append(f"{prefix}-{start:03d}" + (f"..{prev:03d}" if prev != start else ""))
            if n is not None:
                start = prev = n
    return ", ".join(out)


def rs_id_of_dir(name: str) -> str | None:
    m = RS_ID_RE.match(name)
    return m.group(0) if m else None


def artifact_date(text: str) -> str | None:
    """`last_updated:` (or the older `date:` field of verification reports) as
    an ISO string — lexicographic comparison is date order."""
    fm = frontmatter(text)
    for key in ("last_updated", "date"):
        v = fm.get(key)
        if isinstance(v, str) and re.match(r"^\d{4}-\d{2}-\d{2}", v):
            return v[:10]
    return None


def table_cells(line: str) -> list[str]:
    """Stripped cells of a `| a | b |` Markdown table row."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render_row(cells: list[str]) -> str:
    """Normalised row: one space padding, empty cell = two spaces."""
    return "| " + " | ".join(cells) + " |"


def trace_rows(text: str) -> list[tuple[int, list[str]]]:
    """(line_no, [Requirement, Spec, Workstream, Test, Implementation, Verified])
    for every REQ row of a traceability table; a 5-column (pre-v4) row gains an
    empty Workstream cell so callers see one shape."""
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        if re.match(r"^\|\s*REQ-", line):
            cells = table_cells(line)
            if len(cells) == 5:
                cells.insert(2, "")
            if len(cells) == 6:
                out.append((no, cells))
    return out


# ---------------------------------------------------------------------------
# The sweeper.
# ---------------------------------------------------------------------------

class Gc:
    """One run over one repository root.  Findings are (severity, text)."""

    def __init__(self, root: Path, workstream: str | None = None, fast: bool = False,
                 lint_suite_rules: bool = True):
        self.root = root
        self.docs = root / "docs"
        self.fast = fast
        self.findings: list[tuple[str, str]] = []
        self.sweeps_run: list[str] = []
        # `lint_suite_rules=False` runs the linter without its repo-specific
        # REQUIRED / version-gate rows so a temp fixture (no real skill suite)
        # can drive the delegated sweep end to end.  Production runs never
        # flip it.
        self.lint_suite_rules = lint_suite_rules
        marker = read_text(self.docs / ".sdd-version")
        self.marker = (marker or "").strip()
        self.ws_root = self.docs / "ws"
        self.ws_ids = (sorted(p.name for p in self.ws_root.iterdir() if p.is_dir())
                       if self.marker == "4" and self.ws_root.is_dir() else [])
        self.workstream = workstream
        if workstream and self.marker != "4":
            print(f"note: --workstream {workstream} ignored — docs/.sdd-version is not 4",
                  file=sys.stderr)
            self.workstream = None
        self.qimpl_counts: dict[str, int] = {}
        # Dead file links seen by sweep 6, consumed by `--fix xlink-dead`.
        self.dead_links: list[tuple[Path, int, str]] = []

    # -- finding shape (REQ-GC-HARNESSP2-004) --------------------------------

    def flag(self, path: Path | str, line_no: int | None, rule: str, msg: str, fix: str,
             severity: str = "fail") -> None:
        """Record a finding. `fix` is positional and required — a call without it
        is a TypeError, and an empty one is rejected here (self-test contract)."""
        assert severity in ("fail", "warn", "info"), severity
        assert fix, f"finding without fix: [{rule}] {msg}"
        p = Path(path)
        rel = p.relative_to(self.root) if p.is_absolute() else p
        loc = f"{rel}:{line_no}" if line_no else str(rel)
        self.findings.append((severity, f"{loc}: [{rule}] {msg}\n    fix: {fix}"))

    def passthrough(self, severity: str, text: str) -> None:
        """A linter finding, already rendered in the shared shape."""
        self.findings.append((severity, text))

    # -- corpus helpers ------------------------------------------------------

    def docs_md(self) -> list[Path]:
        return sorted(p for p in self.docs.rglob("*.md") if ".git" not in p.parts)

    def spec_files(self) -> list[Path]:
        d = self.docs / "spec"
        return sorted(d.rglob("*.md")) if d.is_dir() else []

    def plan_paths(self) -> dict[str, Path]:
        """workstream id (or '' under marker 3) -> plan path, existing plans only."""
        if self.marker == "4":
            return {ws: self.ws_root / ws / "plan.md" for ws in self.ws_ids
                    if (self.ws_root / ws / "plan.md").is_file()}
        p = self.docs / "plan.md"
        return {"": p} if p.is_file() else {}

    def plan_history_dirs(self) -> list[Path]:
        if self.marker == "4":
            return [self.ws_root / ws / "plan-history" for ws in self.ws_ids
                    if (self.ws_root / ws / "plan-history").is_dir()]
        d = self.docs / "plan-history"
        return [d] if d.is_dir() else []

    def traced_specs(self, plan: Path) -> set[str]:
        """Spec basenames a plan's tasks `trace to` (live plan-walk, ws-staleness.md)."""
        text = read_text(plan) or ""
        out: set[str] = set()
        for m in re.finditer(r"traces? to\s+((?:`[\w./-]+\.md`(?:\s*(?:,|and|/)?\s*)?)+)", text):
            out.update(Path(t).name for t in re.findall(r"`([\w./-]+\.md)`", m.group(1)))
        return out

    def defined_req_ids(self) -> set[str]:
        """Requirement ids defined in category files: `### REQ-…` headings or
        first-column table rows (no traceability file is read)."""
        ids: set[str] = set()
        for f in sorted((self.docs / "requirements").glob("*/*.md")):
            for line in (read_text(f) or "").splitlines():
                m = re.match(r"^(?:#{1,6}\s+|\|\s*)(REQ-[A-Z]+(?:-[A-Z0-9]+)?-\d+)\b", line)
                if m:
                    ids.add(m.group(1))
        return ids

    def research_dir_ids(self) -> dict[str, Path]:
        d = self.docs / "research"
        out: dict[str, Path] = {}
        if d.is_dir():
            for p in sorted(d.iterdir()):
                rid = rs_id_of_dir(p.name) if p.is_dir() else None
                if rid:
                    out[rid] = p
        return out

    # -- sweeps 1-5: delegated to the linter ---------------------------------

    def lint_path(self) -> Path | None:
        for cand in (Path(__file__).resolve().parent / "sdd-skill-lint.py",
                     self.root / "tools" / "sdd-skill-lint.py"):
            if cand.is_file():
                return cand
        return None

    def lint_command(self, lint: Path) -> list[str]:
        if self.lint_suite_rules:
            return [sys.executable, str(lint), str(self.root)]
        # Fixture mode: same linter, same output, suite-specific rows off.
        shim = ("import importlib.util, sys; from pathlib import Path; "
                "s = importlib.util.spec_from_file_location('sdd_skill_lint', sys.argv[1]); "
                "m = importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                "sys.exit(m.Linter(Path(sys.argv[2]), suite_rules=False).run())")
        return [sys.executable, "-c", shim, str(lint), str(self.root)]

    def sweep_lint(self) -> None:
        """Invoke tools/sdd-skill-lint.py and pass its findings through."""
        self.sweeps_run.append("lint")
        lint = self.lint_path()
        assert lint is not None  # main() exits 2 before we get here
        proc = subprocess.run(self.lint_command(lint), capture_output=True, text=True)
        lines = proc.stdout.splitlines()
        i = 0
        finding_re = re.compile(r"^(WARN |INFO )?(\S.*?): \[([\w-]+)\] (.*)$")
        while i < len(lines):
            m = finding_re.match(lines[i])
            if m and i + 1 < len(lines) and lines[i + 1].startswith("    fix: "):
                sev = {"WARN ": "warn", "INFO ": "info"}.get(m.group(1) or "", "fail")
                self.passthrough(sev, f"{lines[i][len(m.group(1) or ''):]}\n{lines[i + 1]}")
                i += 2
                continue
            i += 1
        summary = next((ln for ln in reversed(lines) if ln.strip()), "")
        if not re.match(r"^(OK|FAIL): ", summary) or proc.returncode not in (0, 1):
            self.flag(Path("tools/sdd-skill-lint.py"), None, "lint",
                      f"linter exited {proc.returncode} without a parseable summary",
                      "run tools/sdd-skill-lint.py directly and fix its error")

    # -- sweep 6: cross-links inside docs/ -----------------------------------

    def sweep_xlink(self) -> None:
        self.sweeps_run.append("xlink")
        req_ids = self.defined_req_ids()
        rs_dirs = self.research_dir_ids()
        for f in self.docs_md():
            if "plan-history" in f.relative_to(self.docs).parts:
                continue  # frozen snapshots; their links are historical (`Q-IMPL-HARNESSP2-052`)
            text = read_text(f) or ""
            fm = frontmatter(text)
            for rid in self._ids(fm.get("requires"), REQ_ID_RE):
                if rid not in req_ids:
                    self.flag(f, None, "id-missing", f"`requires:` names undefined {rid}",
                              f"define {rid} in docs/requirements/<category>/ or drop it from requires:")
            for rid in self._ids(fm.get("research_refs"), RS_ID_RE):
                if rid not in rs_dirs:
                    self.flag(f, None, "id-missing", f"`research_refs` names missing {rid}",
                              f"create docs/research/{rid}-<topic>/ or drop it from research_refs")
            for no, line in visible_lines(text):
                for target in LINK_RE.findall(line):
                    if target.startswith(("http://", "https://", "mailto:", "#")):
                        continue
                    self._check_target(f, no, target, [f.parent])
                for body in SEE_RE.findall(line):
                    for token in MD_TOKEN_RE.findall(body):
                        self._check_target(f, no, token,
                                           [f.parent, self.docs / "spec", self.docs, self.root])
                    for rid in RS_ID_RE.findall(body):
                        if rid not in rs_dirs:
                            self.flag(f, no, "id-missing", f"`(see …)` names missing {rid}",
                                      f"point at an existing docs/research/RS-* directory")

    @staticmethod
    def _ids(value: object, pat: re.Pattern) -> list[str]:
        items = value if isinstance(value, list) else ([value] if isinstance(value, str) else [])
        return [i for v in items for i in pat.findall(v)]

    def _check_target(self, f: Path, no: int, target: str, bases: list[Path]) -> None:
        path, _, anchor = target.partition("#")
        if not path:
            return
        hit = next((b / path for b in bases if (b / path).exists()), None)
        if hit is None:
            self.dead_links.append((f, no, target))
            self.flag(f, no, "xlink-dead", f"broken relative link `{target}`", XLINK_FIX)
            return
        if anchor and hit.suffix == ".md":
            wanted = slug(anchor)
            hs = [t for _, t in headings(read_text(hit) or "")]
            if not any(slug(h) == wanted or slug(strip_ordinal(h)) == wanted for h in hs):
                self.flag(f, no, "xlink-dead", f"anchor `#{anchor}` not found in `{path}`",
                          ANCHOR_FIX, "warn")

    # -- sweeps 8-10: Q-IMPL orphans (§Q-IMPL Counting Rule) -----------------

    def is_countable(self, qid: str) -> bool:
        """Apply the placeholder / <WS>-token exclusions to one id."""
        if qid in PLACEHOLDER_IDS or qid.startswith(PLACEHOLDER_PREFIXES):
            return False
        m = re.fullmatch(r"Q-IMPL-([A-Z0-9]+)(?:-(\d+))?", qid)
        if not m:
            return False
        if m.group(2) is None:
            return m.group(1).isdigit()          # legacy bare counter
        return m.group(1) in {ws_token(w) for w in self.ws_ids}

    def reference_files(self) -> list[Path]:
        out: list[Path] = []
        for top in ("docs", "skills", "agents", "tools"):
            d = self.root / top
            if not d.is_dir():
                continue
            for p in sorted(d.rglob("*")):
                rel = p.relative_to(self.root).parts
                if not p.is_file() or ".git" in rel or "__pycache__" in rel:
                    continue
                if rel[:2] == ("docs", "research"):
                    continue
                out.append(p)
        return out

    def sweep_qimpl(self) -> None:
        self.sweeps_run.append("qimpl")
        # definitions: id -> (file, line, entry body)
        defs: dict[str, tuple[Path, int, str]] = {}
        for f in self.spec_files():
            text = read_text(f) or ""
            lines = text.splitlines()
            for no, line in enumerate(lines, 1):
                m = QIMPL_DEF_RE.match(line)
                if not m:
                    continue
                body = []
                for nxt in lines[no:]:
                    if nxt.startswith("## ") or nxt.startswith("### "):
                        break
                    body.append(nxt)
                defs.setdefault(m.group(1), (f, no, "\n".join(body)))
        # references: id -> first (file, line)
        refs: dict[str, tuple[Path, int]] = {}
        for f in self.reference_files():
            text = read_text(f)
            if text is None:
                continue
            for no, line in visible_lines(text):
                if QIMPL_DEF_RE.match(line):
                    continue  # heading lines never count as references
                for qid in QIMPL_RE.findall(line):
                    if self.is_countable(qid):
                        refs.setdefault(qid, (f, no))
        both = sorted(set(defs) & set(refs))
        defined_only = sorted(set(defs) - set(refs))
        referenced_only = sorted(set(refs) - set(defs))
        self.qimpl_counts = {"definitions": len(defs), "both": len(both),
                             "defined_only": len(defined_only),
                             "referenced_only": len(referenced_only)}
        for qid in referenced_only:                                       # (i)
            f, no = refs[qid]
            self.flag(f, no, "qimpl-undefined", f"{qid} is referenced but defined in no spec",
                      f"add a `### {qid}: …` entry under a spec's ## Implementation Questions "
                      f"or correct the reference")
        for qid in defined_only:                                          # (ii)
            f, no, _ = defs[qid]
            self.flag(f, no, "qimpl-unreferenced", f"{qid} is defined but never referenced",
                      "informational — entries live in their spec (deviation-protocol.md); "
                      "cite it from the code or plan it resolved if useful", "info")
        for qid, (f, no, body) in sorted(defs.items()):                   # (iii)
            heading_line = (read_text(f) or "").splitlines()[no - 1]
            for sup in re.findall(r"\[superseded by (Q-IMPL-[A-Z0-9-]+)\]", heading_line + body):
                if sup not in defs:
                    self.flag(f, no, "qimpl-broken-ref",
                              f"{qid} is marked superseded by undefined {sup}",
                              f"point the [superseded by …] note at a defined entry", "warn")
            ref_line = next((ln for ln in body.splitlines()
                             if ln.startswith("**Spec reference**")), None)
            if ref_line is None:
                self.flag(f, no, "qimpl-broken-ref", f"{qid} has no **Spec reference** line",
                          "add `**Spec reference**: §<section>` naming the section it resolves",
                          "warn")
                continue
            hs = [t for _, t in headings(read_text(f) or "")]
            tokens = [t.strip() for t in re.findall(r"§\s*([^§,;]+?)(?=\s+[—–]\s|\s+\(|\s+\"|\"|,|;|\s+and\s|\s+enumerates|$)",
                                                    ref_line.replace("`", ""))]
            missing = [t for t in tokens if t and not any(titles_match(t, h) for h in hs)]
            if missing:
                self.flag(f, no, "qimpl-broken-ref",
                          f"{qid} **Spec reference** names no heading in {f.name}: "
                          + ", ".join(f"§{t}" for t in missing),
                          "rename the § reference to an existing heading of this spec", "warn")

    # -- sweep 13: index <-> directory, spec approval -------------------------

    def sweep_index(self) -> None:
        self.sweeps_run.append("index")
        # research/index.md rows <-> RS-* directories
        idx = self.docs / "research" / "index.md"
        rows: dict[str, int] = {}
        for no, line in enumerate((read_text(idx) or "").splitlines(), 1):
            m = re.match(r"^\|\s*(RS-(?:[A-Z][A-Z0-9]*-)?\d+)\s*\|", line)
            if m:
                rows.setdefault(m.group(1), no)
        dirs = self.research_dir_ids()
        for rid in sorted(set(dirs) - set(rows)):
            self.flag(idx, None, "index-research", f"{dirs[rid].name}/ has no index row", INDEX_FIX_RS)
        for rid in sorted(set(rows) - set(dirs)):
            self.flag(idx, rows[rid], "index-research", f"row {rid} has no RS-* directory", INDEX_FIX_RS)
        # requirements/index.md Files table <-> category files
        ridx = self.docs / "requirements" / "index.md"
        listed: dict[str, int] = {}
        for no, line in enumerate((read_text(ridx) or "").splitlines(), 1):
            if line.startswith("|"):
                for target in re.findall(r"\]\(([\w-]+/[\w-]+\.md)\)", line):
                    listed.setdefault(target, no)
        files = {str(p.relative_to(self.docs / "requirements"))
                 for p in (self.docs / "requirements").glob("*/*.md")}
        for rel in sorted(files - set(listed)):
            self.flag(ridx, None, "index-requirements", f"{rel} has no Files-table row", INDEX_FIX_REQ)
        for rel in sorted(set(listed) - files):
            self.flag(ridx, listed[rel], "index-requirements",
                      f"Files-table row points at missing {rel}", INDEX_FIX_REQ)
        # spec approval: scoped fail via the live plan-walk, unscoped warn
        status = {f: str(frontmatter(read_text(f) or "").get("status", "")) for f in self.spec_files()}
        plans = self.plan_paths()
        if self.workstream:
            plan = plans.get(self.workstream)
            if plan:
                traced = self.traced_specs(plan)
                for f, st in sorted(status.items()):
                    if f.name in traced and st != "Approved":
                        self.flag(f, None, "spec-approval",
                                  f"status: {st or '(none)'} but traced by docs/ws/{self.workstream}/plan.md",
                                  "approve the spec (sdd-specs) before implementing against it")
        elif plans:
            for f, st in sorted(status.items()):
                if st != "Approved":
                    self.flag(f, None, "spec-approval",
                              f"status: {st or '(none)'} while a plan exists",
                              "approve the spec, or confirm no plan traces it (--workstream <id>)",
                              "warn")

    # -- sweep 14: plan-history naming ---------------------------------------

    def sweep_plan_history(self) -> None:
        self.sweeps_run.append("plan-history")
        for d in self.plan_history_dirs():
            for f in sorted(d.glob("*.md")):
                if f.name.startswith("verification-"):
                    continue  # pre-v4 verification snapshots, not plan archives (`Q-IMPL-HARNESSP2-053`)
                if not ARCHIVE_NAME_RE.match(f.name):
                    self.flag(f, None, "plan-history-name",
                              "archive name lacks the {YYYY-MM-DD}-{reason}.md shape", ARCHIVE_FIX)
                elif "-replan-" in f.name and "replan" not in (read_text(f) or "").lower():
                    self.flag(f, None, "plan-history-name",
                              "`-replan-` archive never mentions a replan (written by sdd-replan only)",
                              ARCHIVE_FIX)

    # -- sweep 5 (marker 4): kickoff date: / research_id: per workstream ------

    def sweep_kickoff(self) -> None:
        """Under marker 4 the linter cannot see per-workstream kickoffs, so gc
        emits [kickoff-fields] itself; under marker 3 the linter owns the row."""
        if self.marker != "4":
            return
        self.sweeps_run.append("kickoff")
        for ws in self.ws_ids:
            k = self.ws_root / ws / "kickoff.md"
            if not k.is_file():
                continue  # a workstream without a kickoff is not yet a cycle
            fm = frontmatter(read_text(k) or "")
            missing = [key for key in ("date", "research_id") if not fm.get(key)]
            if missing:
                self.flag(k, None, "kickoff-fields",
                          "kickoff frontmatter lacks " + ", ".join(f"`{m}:`" for m in missing), KICKOFF_FIX)

    # -- sweep 7: staleness chain (ws-staleness.md live plan-walk) ------------

    def category_file_of(self) -> dict[str, Path]:
        """Requirement id -> the category file that defines it."""
        out: dict[str, Path] = {}
        for f in sorted((self.docs / "requirements").glob("*/*.md")):
            for line in (read_text(f) or "").splitlines():
                m = re.match(r"^(?:#{1,6}\s+|\|\s*)(REQ-[A-Z]+(?:-[A-Z0-9]+)?-\d+)\b", line)
                if m:
                    out.setdefault(m.group(1), f)
        return out

    def _stale(self, downstream: Path, d_date: str | None, upstream: Path, u_date: str | None,
               what: str) -> None:
        if d_date and u_date and u_date > d_date:
            self.flag(downstream, None, "stale-chain",
                      f"{what}: {upstream.relative_to(self.root)} ({u_date}) is newer than "
                      f"{downstream.name} ({d_date})", STALE_FIX, "warn")

    def sweep_stale(self) -> None:
        """research → requirements (shared, workstream-independent) → specs →
        plan → verification, per plan via `traces to` → `requires:` → category
        files; never reads a traceability file; stops at the last artifact."""
        self.sweeps_run.append("stale")
        r_idx, q_idx = self.docs / "research" / "index.md", self.docs / "requirements" / "index.md"
        if r_idx.is_file() and q_idx.is_file():
            self._stale(q_idx, artifact_date(read_text(q_idx) or ""), r_idx,
                        artifact_date(read_text(r_idx) or ""), "requirements older than research")
        cat_of = self.category_file_of()
        plans = self.plan_paths()
        if self.workstream:
            plans = {ws: p for ws, p in plans.items() if ws == self.workstream}
        for ws, plan in sorted(plans.items()):
            p_text = read_text(plan) or ""
            p_date = artifact_date(p_text)
            spec_by_name = {f.name: f for f in self.spec_files()}
            reqs: set[str] = set()
            for name in sorted(self.traced_specs(plan)):
                spec = spec_by_name.get(name)
                if spec is None:
                    continue  # a missing spec is sweep 6's finding, not staleness
                s_text = read_text(spec) or ""
                s_date = artifact_date(s_text)
                s_reqs = self._ids(frontmatter(s_text).get("requires"), REQ_ID_RE)
                reqs.update(s_reqs)
                for rid in s_reqs:
                    cf = cat_of.get(rid)
                    if cf:
                        self._stale(spec, s_date, cf, artifact_date(read_text(cf) or ""),
                                    f"spec older than requirement {rid}")
                self._stale(plan, p_date, spec, s_date, "plan older than a traced spec")
            for cf in sorted({cat_of[r] for r in reqs if r in cat_of}):
                self._stale(plan, p_date, cf, artifact_date(read_text(cf) or ""),
                            "plan older than a traced requirement category file")
            ver = plan.parent / "verification.md"
            if ver.is_file():
                v_text = read_text(ver) or ""
                status = str(frontmatter(v_text).get("status", ""))
                note = " (status: pending-red — verification exists, not passed)" if status == "pending-red" else ""
                self._stale(ver, artifact_date(v_text), plan, p_date, "verification older than the plan" + note)

    # -- sweep 11: empty traceability cells (sdd-verify Step 3b policy) --------

    def trace_files(self) -> list[Path]:
        if self.marker == "4":
            return [self.ws_root / ws / "traceability.md" for ws in self.ws_ids
                    if (self.ws_root / ws / "traceability.md").is_file()]
        t = self.docs / "requirements" / "traceability.md"
        return [t] if t.is_file() else []

    def legacy_rows(self) -> list[list[str]]:
        """Rows of the shared aggregate attributed to the blank/default
        workstream — the shipped legacy rows, in shipped order."""
        agg = self.docs / "requirements" / "traceability.md"
        return [cells for _, cells in trace_rows(read_text(agg) or "") if not cells[2]]

    def sweep_trace_empty(self) -> None:
        self.sweeps_run.append("trace-empty")
        legacy_spec = {c[0]: c[1] for c in self.legacy_rows()} if self.marker == "4" else {}
        for f in self.trace_files():
            for no, c in trace_rows(read_text(f) or ""):
                req, spec, _ws, test, impl, _ver = c
                # Amendment row (telemetry.md §XSPEC): Spec differs from the legacy
                # row for the same id — inherits the legacy Verified, never a gap.
                if c[2] and req in legacy_spec and spec and spec != legacy_spec[req]:
                    continue
                if not spec:
                    self.flag(f, no, "trace-empty", f"{req}: Spec cell empty", TRACE_FIX, "warn")
                elif impl and not test:
                    self.flag(f, no, "trace-empty", f"{req}: Implementation filled but Test empty",
                              TRACE_FIX, "warn")

    # -- sweep 12: aggregate == regenerate(per-ws files) (ws-traceability.md) --

    def regenerate_aggregate(self) -> tuple[Path, str]:
        """Deterministic aggregate text: the existing preamble (frontmatter and
        prose untouched — `last_updated` is never edited), the canonical header,
        legacy rows in shipped order, then every per-ws row stable-sorted by id;
        cells normalised, empty cell = two spaces."""
        agg = self.docs / "requirements" / "traceability.md"
        text = read_text(agg) or ""
        lines = text.splitlines()
        hdr = next((i for i, ln in enumerate(lines) if ln.startswith("| Requirement")), None)
        preamble = "\n".join(lines[:hdr]) + "\n" if hdr is not None else AGG_PREAMBLE
        rows = [render_row(c) for c in self.legacy_rows()]
        per_ws: list[list[str]] = []
        for f in self.trace_files():
            per_ws.extend(c for _, c in trace_rows(read_text(f) or ""))
        rows += [render_row(c) for c in sorted(per_ws, key=lambda c: c[0])]   # stable
        return agg, preamble + "\n".join(AGG_HEADER) + "\n" + "".join(r + "\n" for r in rows)

    def sweep_aggregate(self) -> None:
        if self.marker != "4":
            return  # no per-ws inputs under marker 3
        self.sweeps_run.append("aggregate")
        agg, want = self.regenerate_aggregate()
        if (read_text(agg) or "") != want:
            self.flag(agg, None, "traceability-aggregate",
                      "aggregate differs from regenerate(docs/ws/*/traceability.md)", AGG_FIX, "warn")

    # -- `--fix <rule>` whitelist (drift-sweep.md §`--fix` Whitelist) ---------

    def in_other_ws(self, p: Path) -> bool:
        """True when `--workstream <id>` is given and p lives under another ws."""
        rel = p.relative_to(self.root).parts
        return bool(self.workstream) and rel[:2] == ("docs", "ws") and len(rel) > 2 and rel[2] != self.workstream

    def fix(self, rule: str) -> int:
        """Apply one whitelisted rewrite; print changed paths (or `no changes`)."""
        changed = {"xlink-dead": self.fix_xlink_dead, "index-requirements": self.fix_index_requirements,
                   "traceability-aggregate": self.fix_traceability_aggregate,
                   "plan-history-name": self.fix_plan_history_name}[rule]()
        for p in changed:
            print(f"fixed [{rule}] {p.relative_to(self.root)}")
        if not changed:
            print(f"no changes ([{rule}] has nothing to fix)")
        return 0

    def fix_xlink_dead(self) -> list[Path]:
        self.sweep_xlink()          # collects self.dead_links; prints nothing
        by_name: dict[str, list[Path]] = {}
        for p in self.docs_md():
            by_name.setdefault(p.name, []).append(p)
        changed: set[Path] = set()
        for f, no, target in self.dead_links:
            if self.in_other_ws(f):
                continue
            path, _, anchor = target.partition("#")
            cands = by_name.get(Path(path).name, [])
            if len(cands) != 1:
                print(f"left [xlink-dead] {f.relative_to(self.root)}:{no} `{target}` — "
                      f"{len(cands)} candidate(s)" + (": " + ", ".join(str(c.relative_to(self.root)) for c in cands)
                                                      if cands else ""))
                continue
            new = os.path.relpath(cands[0], f.parent) + (f"#{anchor}" if anchor else "")
            lines = (read_text(f) or "").split("\n")
            if target in lines[no - 1]:
                lines[no - 1] = lines[no - 1].replace(f"({target})", f"({new})").replace(f"(see {target})", f"(see {new})")
                f.write_text("\n".join(lines), encoding="utf-8")
                changed.add(f)
        return sorted(changed)

    def fix_index_requirements(self) -> list[Path]:
        """Insert each missing Files-table row at its ID-sorted position: inside
        its category block, before the first row whose Domain sorts after it
        (ws-ids.md merge-safe insertion) — never at EOF."""
        ridx = self.docs / "requirements" / "index.md"
        text = read_text(ridx)
        if text is None:
            return []
        lines = text.split("\n")
        listed = {t for ln in lines if ln.startswith("|") for t in re.findall(r"\]\(([\w-]+/[\w-]+\.md)\)", ln)}
        files = sorted(str(p.relative_to(self.docs / "requirements"))
                       for p in (self.docs / "requirements").glob("*/*.md"))
        table = [i for i, ln in enumerate(lines) if re.match(r"^\|\s*\w[\w-]*\s*\|\s*\[", ln)]
        if not table:
            return []
        changed = False
        for rel in files:
            if rel in listed:
                continue
            cat, name = rel.split("/", 1)
            cf_text = read_text(self.docs / "requirements" / rel) or ""
            fm = frontmatter(cf_text)
            ids = sorted({m.group(1) for ln in cf_text.splitlines()
                          for m in [re.match(r"^(?:#{1,6}\s+|\|\s*)(REQ-[A-Z]+(?:-[A-Z0-9]+)?-\d+)\b", ln)] if m})
            domain = ", ".join(sorted({i.split("-")[1] for i in ids})) or ""
            row = render_row([cat, f"[{name}]({rel})", domain, compress_ids(ids),
                              str(fm.get("status", "")), str(fm.get("last_updated", ""))])
            block = [i for i in table if table_cells(lines[i])[0] == cat]
            pos = None
            for i in block:
                if table_cells(lines[i])[2] > domain:
                    pos = i
                    break
            if pos is None:
                pos = (block[-1] if block else table[-1]) + 1
            lines.insert(pos, row)
            table = [i + (1 if i >= pos else 0) for i in table] + [pos]
            table.sort()
            changed = True
        if changed:
            ridx.write_text("\n".join(lines), encoding="utf-8")
            return [ridx]
        return []

    def fix_traceability_aggregate(self) -> list[Path]:
        if self.marker != "4":
            print("left [traceability-aggregate] no per-ws inputs under marker 3")
            return []
        agg, want = self.regenerate_aggregate()
        if (read_text(agg) or "") == want:
            return []
        agg.write_text(want, encoding="utf-8")
        return [agg]

    def fix_plan_history_name(self) -> list[Path]:
        changed: list[Path] = []
        for d in self.plan_history_dirs():
            if self.in_other_ws(d):
                continue
            for f in sorted(d.glob("*.md")):
                if f.name.startswith("verification-") or ARCHIVE_NAME_RE.match(f.name):
                    continue
                date = artifact_date(read_text(f) or "")
                if not date:
                    log = subprocess.run(["git", "-C", str(self.root), "log", "-1", "--format=%as", "--", str(f)],
                                         capture_output=True, text=True)
                    date = log.stdout.strip() or None
                if not date:
                    print(f"left [plan-history-name] {f.relative_to(self.root)} — no last_updated or commit date")
                    continue
                stem = re.sub(r"^\d{4}-\d{2}-\d{2}-?", "", f.stem)          # a partial date prefix is replaced
                stem = re.sub(r"[^a-z0-9-]+", "-", stem.lower()).strip("-") or "archive"
                new = f.with_name(f"{date}-{stem}.md")
                if new.exists():
                    print(f"left [plan-history-name] {f.relative_to(self.root)} — {new.name} already exists")
                    continue
                f.rename(new)
                changed.append(new)
        return changed

    # -- driver --------------------------------------------------------------

    def run(self) -> int:
        self.sweep_lint()
        self.sweep_xlink()
        self.sweep_qimpl()
        if not self.fast:
            self.sweep_stale()
            self.sweep_trace_empty()
            self.sweep_aggregate()
            self.sweep_index()
            self.sweep_plan_history()
            self.sweep_kickoff()
        for severity, text in self.findings:
            print({"warn": "WARN ", "info": "INFO "}.get(severity, "") + text)
        counts = Counter(sev for sev, _ in self.findings)
        n_fail, n_warn, n_info = counts["fail"], counts["warn"], counts["info"]
        if n_fail:
            print(f"FAIL: {n_fail} finding(s), {n_warn} warning(s), {n_info} info")
            return 1
        print(f"OK: {len(self.sweeps_run)} sweep(s) clean, {n_warn} warning(s), {n_info} info")
        return 0


# ---------------------------------------------------------------------------
# Self-test: a temporary marker-4 fixture with SYMBOLIC counts — every expected
# number is incremented by the builder as it writes the element that causes it,
# never read from the live corpus.
# ---------------------------------------------------------------------------

def _w(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def qid(ws: str | None, n: int) -> str:
    """Compose a Q-IMPL id (kept out of literal source so the tool never
    references its own fixture ids)."""
    return f"Q-IMPL-{ws}-{n:03d}" if ws else f"Q-IMPL-{n:03d}"


def build_fixture(root: Path, clean: bool) -> dict[str, object]:
    """Write a git-initialised marker-4 tree with workstreams `alpha` and `beta`
    (drift-sweep.md §Self-Test Fixture).

    `clean=False` plants exactly one instance of every fail rule plus the warn /
    info cases; `clean=True` writes the same tree without defects.  Returns the
    symbolic expectations — every count is incremented by the element that
    causes it, never read from the live corpus.
    """
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    exp: dict[str, object] = {"fail": Counter(), "warn": Counter(), "info": Counter()}
    fail, warn, info = exp["fail"], exp["warn"], exp["info"]  # type: ignore[assignment]
    a1, a2, a3, a4 = (qid("ALPHA", i) for i in (1, 2, 3, 4))
    l7, l8 = qid(None, 7), qid(None, 8)
    D = 6                       # definitions written below (a1..a4, l7, l8)
    B = 3                       # referenced in prose: a1, a2 (SKILL.md), l7 (beta plan)
    info["qimpl-unreferenced"] += D - B

    _w(root, "docs/.sdd-version", "4\n")
    # -- research: RS-1 listed; RS-2 directory unlisted when dirty
    rows = "| ID | Topic | Date | Status | Summary |\n|---|---|---|---|---|\n| RS-1 | x | 2026-01-01 | Complete | x |\n"
    if clean:
        rows += "| RS-2 | y | 2026-01-01 | Complete | y |\n"
    else:
        fail["index-research"] += 1
    _w(root, "docs/research/index.md", f"---\nlast_updated: 2026-01-01\n---\n# Research\n\n{rows}")
    _w(root, "docs/research/RS-1-x/findings.md",
       f"---\nstatus: Complete\n---\n# RS-1\n\nForeign repo cites {l8} here — excluded.\n")
    _w(root, "docs/research/RS-2-y/findings.md", "---\nstatus: Complete\n---\n# RS-2\n")
    # -- requirements: two category files; `two.md` row missing when dirty.  The
    #    clean table is also the exact text `--fix index-requirements` must produce.
    files_tbl = ("| Category | File | Domain | Requirements | Status | Last Updated |\n"
                 "|---|---|---|---|---|---|\n"
                 "| functional | [one.md](functional/one.md) | AA | REQ-AA-ALPHA-001..002 | Approved | 2026-01-01 |\n")
    two_row = "| functional | [two.md](functional/two.md) | BB | REQ-BB-ALPHA-001..002 | Approved | 2026-01-01 |\n"
    if clean:
        files_tbl += two_row
    else:
        fail["index-requirements"] += 1
    index_text = f"---\nstatus: Approved\nlast_updated: 2026-01-01\n---\n# Requirements\n\n## Files\n\n{files_tbl}"
    _w(root, "docs/requirements/index.md", index_text)
    exp["index_fixed"] = index_text.replace(files_tbl, files_tbl + ("" if clean else two_row))
    _w(root, "docs/requirements/functional/one.md",
       "---\nstatus: Approved\nlast_updated: 2026-01-01\nresearch_refs: [RS-1]\n---\n"
       "# One\n\n### REQ-AA-ALPHA-001: first\n\nText — see a.md.\n\n"
       "### REQ-AA-ALPHA-002: second\n\nDesign lives in the spec (see a.md).\n")
    _w(root, "docs/requirements/functional/two.md",
       "---\nstatus: Approved\nlast_updated: 2026-01-01\n---\n# Two\n\n"
       "| REQ-BB-ALPHA-001 | table-defined |\n| REQ-BB-ALPHA-002 | table-defined |\n")
    # -- specs: a.md (Approved, traced by alpha), b.md (Draft when dirty, traced only by beta)
    requires = ["REQ-AA-ALPHA-001", "REQ-AA-ALPHA-002"]
    if not clean:
        requires.append("REQ-ZZ-999")
        fail["id-missing"] += 1
    # one dead link whose basename has exactly one candidate under docs/ -> fixable
    dead = "" if clean else "See [the gadget](../old/b.md) for the shape.\n"
    if not clean:
        fail["xlink-dead"] += 1
    anchor = "" if clean else "See [the widget](b.md#no-such-heading).\n"
    if not clean:
        warn["xlink-dead"] += 1          # anchor miss is warn severity
    a4_ref = "§Widget" if clean else "§Nonexistent Section"
    if not clean:
        warn["qimpl-broken-ref"] += 1
    # a.md newer than alpha's plan (2026-01-03) when dirty -> stale-chain on the plan
    a_date = "2026-01-02" if clean else "2026-01-04"
    if not clean:
        warn["stale-chain"] += 1
    _w(root, "docs/spec/a.md", f"""---
status: Approved
last_updated: {a_date}
requires: [{', '.join(requires)}]
---

# Spec A

## Design

### Widget

Widget text. {dead}{anchor}Cross-spec: (see b.md).

### Step 3: Ordinal Heading

## Implementation Questions

### {a1}: first choice
**Tier**: 2
**Spec reference**: §Widget
**Decision**: x

### {a2}: second choice
**Tier**: 2
**Spec reference**: §Ordinal Heading, §Design
**Decision**: y

### {a3}: defined only
**Tier**: 2
**Spec reference**: §Design (rationale)
**Decision**: z

### {a4}: broken reference
**Tier**: 2
**Spec reference**: {a4_ref}
**Decision**: w
""")
    b_status = "Approved" if clean else "Draft"
    if not clean:
        warn["spec-approval"] += 1       # unscoped warn; `--workstream beta` -> 1 fail; alpha -> 0
    _w(root, "docs/spec/b.md", f"""---
status: {b_status}
last_updated: 2026-01-02
requires: [REQ-BB-ALPHA-001, REQ-BB-ALPHA-002]
---

# Spec B

## Design

### Gadget

## Implementation Questions

### {l7}: legacy referenced
**Tier**: 2
**Spec reference**: §Gadget
**Decision**: legacy

### {l8}: legacy defined only
**Tier**: 2
**Spec reference**: §Gadget
**Decision**: legacy
""")
    # -- workstream alpha: traces a.md only
    _w(root, "docs/ws/alpha/kickoff.md", "---\nresearch_id: RS-1\ndate: 2026-01-01\n---\n# Kickoff\n")
    _w(root, "docs/ws/alpha/plan.md", """---
status: active
last_updated: 2026-01-03
---

# Plan

### Chunk 0: things
**Depends on**: none
1. [ ] [implement] widget — traces to `a.md` §Widget (REQ-AA-ALPHA-001).
""")
    # verification older than the plan and not passed when dirty -> stale-chain
    if clean:
        _w(root, "docs/ws/alpha/verification.md", "---\nlast_updated: 2026-01-03\nstatus: pass\n---\n# V\n\n## Next Steps\n")
    else:
        _w(root, "docs/ws/alpha/verification.md", "---\nlast_updated: 2026-01-02\nstatus: pending-red\n---\n# V\n\n## Next Steps\n")
        warn["stale-chain"] += 1
    alpha_rows = [["REQ-AA-ALPHA-001", "a.md", "alpha", "test_widget", "widget.py", ""]]
    if clean:
        _w(root, "docs/ws/alpha/plan-history/2026-01-01-replan-foo.md",
           "---\nlast_updated: 2026-01-01\n---\n# archived by sdd-replan\n")
    else:
        _w(root, "docs/ws/alpha/plan-history/replan-foo.md", "---\nlast_updated: 2026-01-01\n---\n# replan\n")
        fail["plan-history-name"] += 1
    # -- workstream beta: traces b.md only; kickoff lacks date: when dirty
    kick = "---\nresearch_id: RS-2\ndate: 2026-01-01\n---\n# Kickoff\n" if clean else "---\nresearch_id: RS-2\n---\n# Kickoff\n"
    if not clean:
        fail["kickoff-fields"] += 1
    _w(root, "docs/ws/beta/kickoff.md", kick)
    _w(root, "docs/ws/beta/plan.md", f"""---
status: active
last_updated: 2026-01-03
---

# Plan

### Chunk 0: things
**Depends on**: none
1. [ ] [implement] gadget — traces to `b.md` §Gadget; resolved via {l7}.
""")
    # trace-empty rows: (1) amendment row — Spec differs from the legacy row for the
    # same id — Implementation-filled / Test-empty yet never a gap; (2) Spec-empty;
    # (3) Implementation-filled / Test-empty; (4) prose-only row with empty Test.
    beta_rows = [
        ["REQ-BB-ALPHA-001", "b.md", "beta", "", "gadget.py", ""],
        ["REQ-AA-ALPHA-002", "a.md" if clean else "", "beta", "test_second", "second.py", ""],
        ["REQ-BB-ALPHA-002", "b.md", "beta", "test_gadget2" if clean else "", "gadget2.py", ""],
        ["REQ-AA-ALPHA-001", "a.md", "beta", "", "", ""],
    ]
    if not clean:
        warn["trace-empty"] += 2
    for ws, ws_rows in (("alpha", alpha_rows), ("beta", beta_rows)):
        _w(root, f"docs/ws/{ws}/traceability.md",
           f"---\nworkstream: {ws}\nlast_updated: 2026-01-03\n---\n\n"
           + "\n".join(AGG_HEADER) + "\n" + "".join(render_row(r) + "\n" for r in ws_rows))
    # -- shared aggregate: legacy rows in shipped (unsorted) order, then per-ws
    #    rows stable-sorted by id.  Dirty drops the last row -> differs from
    #    regeneration; the expected text is also what `--fix` must produce.
    legacy = [["REQ-BB-ALPHA-001", "old.md", "", "", "", "pass"],
              ["REQ-AA-ALPHA-001", "a.md", "", "", "", "pass"]]
    per_ws = sorted(alpha_rows + beta_rows, key=lambda r: r[0])
    agg_rows = [render_row(r) for r in legacy + per_ws]
    agg_pre = ("---\nlast_updated: 2026-01-03\nregenerated_from: docs/ws/*/traceability.md\n---\n\n"
               "# Traceability Matrix\n\nDerived aggregate.\n\n" + "\n".join(AGG_HEADER) + "\n")
    exp["aggregate"] = agg_pre + "\n".join(agg_rows) + "\n"
    if clean:
        _w(root, "docs/requirements/traceability.md", exp["aggregate"])  # type: ignore[arg-type]
    else:
        _w(root, "docs/requirements/traceability.md", agg_pre + "\n".join(agg_rows[:-1]) + "\n")
        warn["traceability-aggregate"] += 1
    # -- skills: one skill, > 400 lines so the linter's size warning passes through
    padding = "\n".join(f"filler line {i}." for i in range(1, 405))
    mutation = "" if clean else f"\nMutation: resolved per {qid(None, 999)} (undefined).\n"
    if not clean:
        fail["qimpl-undefined"] += 1
    _w(root, "skills/x/SKILL.md", f"""---
name: x
description: Use for x. Skip for everything else.
---

# x

Prose references {a1} and {a2}; placeholder {qid('ISSUE42', 1)} never counts.
Inline code `{a4}` never counts; a quoted literal ("{a3}" refers to one entry)
never counts; nor does a wrapped span `see
{a4} here`.

```
fenced {a3} never counts
```
{mutation}
{padding}
""")
    warn["lint-size"] += 1
    exp.update({"D": D, "B": B})
    return exp


def _run(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main(argv)
        except SystemExit as e:       # argparse --help exits; never let it end the self-test
            code = int(e.code or 0)
    return code, buf.getvalue()


_FINDING_RE = re.compile(r"^(WARN |INFO )?(\S.*?)(?::(\d+))?: \[([\w-]+)\] (.*)$")


def _parse(out: str) -> tuple[Counter, Counter, Counter, list[str]]:
    """(fail counts, warn counts, info counts, problems) by rule from a report."""
    lines = out.splitlines()
    fails, warns, infos, problems = Counter(), Counter(), Counter(), []
    for i, ln in enumerate(lines):
        m = _FINDING_RE.match(ln)
        if not m:
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if not nxt.startswith("    fix: ") or not nxt[len("    fix: "):].strip():
            problems.append(f"finding without fix: {ln}")
        {"WARN ": warns, "INFO ": infos}.get(m.group(1) or "", fails)[m.group(4)] += 1
    if not lines or not re.match(r"^(OK|FAIL): ", lines[-1]):
        problems.append(f"summary line not last: {lines[-1:] }")
    return fails, warns, infos, problems


def _dates(root: Path) -> Counter:
    """Multiset of every `last_updated:` / `date:` frontmatter line under docs/ —
    `--fix` must leave it untouched."""
    c: Counter = Counter()
    for p in sorted((root / "docs").rglob("*.md")):
        for ln in (read_text(p) or "").splitlines():
            if re.match(r"^(last_updated|date):", ln):
                c[ln] += 1
    return c


def _tree_bytes(d: Path) -> dict[str, bytes]:
    return {str(p.relative_to(d)): p.read_bytes() for p in sorted(d.rglob("*")) if p.is_file()}


def self_test() -> int:
    global _LINT_SUITE_RULES
    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    tmp = Path(tempfile.mkdtemp(prefix="sdd-gc-selftest-"))
    _LINT_SUITE_RULES = False
    try:
        dirty, clean, plain = tmp / "dirty", tmp / "clean", tmp / "plain"
        exp = build_fixture(dirty, clean=False)
        build_fixture(clean, clean=True)
        plain.mkdir()
        D, B = exp["D"], exp["B"]
        efail, ewarn, einfo = exp["fail"], exp["warn"], exp["info"]  # type: ignore[assignment]
        n_sweeps = 9            # lint, xlink, qimpl, stale, trace, aggregate, index, plan-history, kickoff

        # -- 1. dirty fixture: exit 1, every fail rule exactly once, symbolic counts
        code, out = _run(["--report", "--root", str(dirty)])
        fails, warns, infos, problems = _parse(out)
        check(code == 1, f"dirty fixture exit {code}, want 1")
        check(not problems, "shape problems: " + "; ".join(problems))
        for rule, n in efail.items():
            check(fails[rule] == n == 1, f"[{rule}] fail count {fails[rule]}, want exactly 1\n{out}")
        check(sum(fails.values()) == sum(efail.values()),
              f"unexpected fail rules: {dict(fails)} vs {dict(efail)}")
        for rule in ("qimpl-broken-ref", "xlink-dead", "spec-approval", "stale-chain",
                     "trace-empty", "traceability-aggregate"):
            check(warns[rule] == ewarn[rule], f"[{rule}] warn count {warns[rule]}, want {ewarn[rule]}\n{out}")
        check(warns["size"] == ewarn["lint-size"] and "[size]" in out,
              f"lint size warning did not pass through:\n{out}")
        check(infos["qimpl-unreferenced"] == D - B == einfo["qimpl-unreferenced"],
              f"defined-only info {infos['qimpl-unreferenced']}, want {D - B}")
        check(fails["qimpl-undefined"] == 1 and "999" in out, "Q-IMPL mutation not flagged once")
        check("WARN " in out and "INFO " in out, "missing WARN/INFO prefixes")
        check("pending-red" in out, "stale-chain did not read pending-red as not-passed")
        # counting-rule internals: D, B, D-B, 0 referenced-only before the mutation
        g = Gc(dirty, lint_suite_rules=False)
        g.sweep_qimpl()
        c = g.qimpl_counts
        check(c["definitions"] == D and c["both"] == B and c["defined_only"] == D - B
              and c["referenced_only"] == 1,   # the planted mutation is the only one
              f"counting rule {c}, want D={D} B={B}")
        check(out.strip().splitlines()[-1].startswith(f"FAIL: {sum(efail.values())} finding(s), "),
              f"summary wrong: {out.strip().splitlines()[-1]}")

        # -- 2. workstream scoping: alpha traces only Approved specs; beta traces the Draft one
        code, out = _run(["--report", "--root", str(dirty), "--workstream", "alpha"])
        fails, warns, _, _ = _parse(out)
        check(fails["spec-approval"] == 0 and warns["spec-approval"] == 0,
              f"alpha-scoped spec-approval fired: {dict(fails)} {dict(warns)}")
        check(warns["stale-chain"] == ewarn["stale-chain"], f"alpha-scoped stale-chain {dict(warns)}")
        check(fails["xlink-dead"] == 1, "scoped run lost the xlink finding")
        code, out = _run(["--report", "--root", str(dirty), "--workstream", "beta"])
        fails, warns, _, _ = _parse(out)
        check(fails["spec-approval"] == 1 and warns["spec-approval"] == 0,
              f"beta-scoped spec-approval: {dict(fails)} {dict(warns)}")
        check(warns["stale-chain"] == 0, f"beta-scoped stale-chain leaked alpha's: {dict(warns)}")

        # -- 3. --fast: lint + xlink + qimpl only — no date walk, no history, no tables
        code, out = _run(["--fast", "--root", str(dirty)])
        fails, warns, _, _ = _parse(out)
        check(code == 1 and fails["plan-history-name"] == 0 and fails["index-research"] == 0
              and fails["kickoff-fields"] == 0 and warns["stale-chain"] == 0
              and warns["trace-empty"] == 0 and warns["traceability-aggregate"] == 0
              and fails["xlink-dead"] == 1 and fails["qimpl-undefined"] == 1,
              f"--fast ran the wrong sweeps: {dict(fails)} {dict(warns)}")

        # -- 4. clean copy: exit 0, no fail, size warning passes through, summary shape
        code, out = _run(["--report", "--root", str(clean)])
        fails, warns, infos, problems = _parse(out)
        check(code == 0 and not fails, f"clean fixture exit {code}, fails {dict(fails)}\n{out}")
        check(not problems, "clean shape problems: " + "; ".join(problems))
        check(out.strip().splitlines()[-1] == f"OK: {n_sweeps} sweep(s) clean, 1 warning(s), {D - B} info",
              f"clean summary wrong: {out.strip().splitlines()[-1]}")
        check(warns["size"] == 1, "clean run lost the lint size pass-through")
        check(warns["traceability-aggregate"] == 0 and warns["trace-empty"] == 0,
              f"clean aggregate / amendment row flagged: {dict(warns)}")

        # -- 5. exit code 2 paths
        code, out = _run(["--fix", "nonexistent-rule", "--root", str(clean)])
        check(code == 2 and "not a fixable rule" in out, f"--fix nonexistent-rule: {code} {out!r}")
        code, out = _run(["--fix", "staleness", "--root", str(clean)])
        check(code == 2 and "not a fixable rule" in out, f"--fix staleness: {code} {out!r}")
        code, out = _run(["--fix", "stale-chain", "--root", str(clean)])
        check(code == 2 and "not a fixable rule" in out, f"--fix stale-chain (dates never fixed): {code}")
        code, out = _run(["--report", "--root", str(plain)])
        check(code == 2 and "not a git repository" in out, f"non-git root: {code} {out!r}")
        nodocs = tmp / "nodocs"
        nodocs.mkdir()
        subprocess.run(["git", "init", "-q", str(nodocs)], check=True)
        code, out = _run(["--report", "--root", str(nodocs)])
        check(code == 2 and "docs/" in out, f"missing docs/: {code} {out!r}")

        # -- 6. --help names every flag, the classes with rule ids, the counting rule, the exclusions
        code, out = _run(["--help"])
        check(code == 0, "--help exit")
        for needle in ("--report", "--fast", "--workstream", "--fix", "--root", "--self-test",
                       "delegated", "excluded", "counting rule", "review", *ALL_RULES, *FIXABLE):
            check(needle in out, f"--help lacks {needle!r}")
        check(len(FIXABLE) == 4, f"FIXABLE has {len(FIXABLE)} rules, want 4")

        # -- 7. flag() refuses an empty fix
        try:
            Gc(clean, lint_suite_rules=False).flag(clean / "docs/x.md", 1, "x", "m", "")
            check(False, "flag() accepted an empty fix")
        except AssertionError:
            pass

        # -- 8. --fix whitelist on the dirty tree: prints paths, idempotent, dates untouched,
        #       never writes under another workstream
        dates_before = _dates(dirty)
        beta_before = _tree_bytes(dirty / "docs/ws/beta")
        a_md = dirty / "docs/spec/a.md"
        code, out = _run(["--fix", "xlink-dead", "--root", str(dirty)])
        check(code == 0 and "docs/spec/a.md" in out, f"--fix xlink-dead: {code} {out!r}")
        check("](b.md)" in (read_text(a_md) or "") and "../old/b.md" not in (read_text(a_md) or ""),
              "xlink-dead fix did not rewrite the unique-candidate link")
        code, out = _run(["--fix", "xlink-dead", "--root", str(dirty)])
        check(code == 0 and "no changes" in out, f"second --fix xlink-dead changed something: {out!r}")
        _w(dirty, "docs/spec/a.md", (read_text(a_md) or "") + "\nCompare (see ../spec/nope.md).\n")
        code, out = _run(["--fix", "xlink-dead", "--root", str(dirty)])
        check(code == 0 and "no changes" in out and "left" in out and "nope.md" in out,
              f"dead link without a candidate was not left+reported: {out!r}")
        code, out = _run(["--report", "--root", str(dirty)])
        fails, _, _, _ = _parse(out)
        check(fails["xlink-dead"] == 1, f"after fix, xlink-dead fails {fails['xlink-dead']} (want the unfixable one)")

        idx = dirty / "docs/requirements/index.md"
        code, out = _run(["--fix", "index-requirements", "--root", str(dirty)])
        check(code == 0 and "docs/requirements/index.md" in out, f"--fix index-requirements: {code} {out!r}")
        check(read_text(idx) == exp["index_fixed"],
              f"index row not inserted at its sorted position:\n{read_text(idx)}")
        code, out = _run(["--fix", "index-requirements", "--root", str(dirty)])
        check(code == 0 and "no changes" in out, f"second --fix index-requirements: {out!r}")

        hist = dirty / "docs/ws/alpha/plan-history"
        code, out = _run(["--fix", "plan-history-name", "--root", str(dirty)])
        check(code == 0 and "2026-01-01-replan-foo.md" in out, f"--fix plan-history-name: {code} {out!r}")
        check((hist / "2026-01-01-replan-foo.md").is_file() and not (hist / "replan-foo.md").exists(),
              "archive not renamed with its last_updated prefix")
        code, out = _run(["--fix", "plan-history-name", "--root", str(dirty)])
        check(code == 0 and "no changes" in out, f"second --fix plan-history-name: {out!r}")

        agg = dirty / "docs/requirements/traceability.md"
        code, out = _run(["--fix", "traceability-aggregate", "--root", str(dirty), "--workstream", "alpha"])
        check(code == 0 and "docs/requirements/traceability.md" in out, f"--fix traceability-aggregate: {code} {out!r}")
        check(read_text(agg) == exp["aggregate"],
              f"regenerated aggregate differs from the expected text:\n{read_text(agg)}\n--- want ---\n{exp['aggregate']}")
        before = read_text(agg)
        code, out = _run(["--fix", "traceability-aggregate", "--root", str(dirty)])
        check(code == 0 and "no changes" in out and read_text(agg) == before,
              f"second --fix traceability-aggregate not a no-op: {out!r}")
        check(_tree_bytes(dirty / "docs/ws/beta") == beta_before, "--fix wrote under docs/ws/beta/")
        check(_dates(dirty) == dates_before, f"--fix touched a date field: {_dates(dirty) - dates_before}")
        code, out = _run(["--report", "--root", str(dirty)])
        fails, warns, _, _ = _parse(out)
        check(fails["index-requirements"] == 0 and fails["plan-history-name"] == 0
              and warns["traceability-aggregate"] == 0,
              f"fixed rules still fire: {dict(fails)} {dict(warns)}")
        check(fails["id-missing"] == 1 and fails["kickoff-fields"] == 1 and warns["stale-chain"] == ewarn["stale-chain"],
              f"--fix changed findings it does not own: {dict(fails)} {dict(warns)}")
    finally:
        _LINT_SUITE_RULES = True
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("SELF-TEST FAIL:\n- " + "\n- ".join(failures))
        return 1
    print("SELF-TEST OK: sweeps 5-14 fire once each on the two-workstream fixture; counting rule "
          "D/B/D-B hold; exit codes 0/1/2; finding shape; lint pass-through; four --fix rules "
          "idempotent with dates and other workstreams untouched")
    return 0


# Flipped only by self_test() so fixture trees can run the delegated sweep.
_LINT_SUITE_RULES = True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

HELP_EPILOG = """\
sweep classes and rule ids
  delegated (tools/sdd-skill-lint.py, invoked as a subprocess; never copied):
      [lint] skill structure, forbidden phrases, REQUIRED markers, ordinals, size,
             references/ links, docs/spec pointers, known drift phrases
      [kickoff-fields] fail kickoff date:/research_id: per workstream (linter at marker 3;
             gc at marker 4, seen at sdd-orchestrate entry and DONE)
  gc (scoped to docs/**):
      [xlink-dead] fail   dead [text](path) / (see …) links; anchor miss is warn
      [id-missing] fail   requires: / research_refs / (see RS-…) ids that do not exist
      [stale-chain] warn  research -> requirements -> specs -> plan -> verification dates,
             per workstream via plan `traces to` -> spec requires: -> category files;
             pending-red reads as "verification exists, not passed"; never fixable
      [qimpl-undefined] fail    Q-IMPL referenced but defined in no spec
      [qimpl-unreferenced] info Q-IMPL defined but never referenced (not a defect)
      [qimpl-broken-ref] warn   **Spec reference** heading missing; [superseded by …] names an undefined id
      [trace-empty] warn        Spec-empty rows; Implementation-filled / Test-empty rows
      [traceability-aggregate] warn  aggregate != regenerate(per-ws files) (marker 4)
      [index-research] fail     research/index.md rows <-> RS-* directories
      [index-requirements] fail requirements/index.md Files table <-> category files
      [spec-approval]           fail with --workstream (specs traced by that plan), warn unscoped
      [plan-history-name] fail  {YYYY-MM-DD}-{reason}.md; -replan- only from sdd-replan
  excluded (review / dogfooding territory, not mechanical):
      new drift of skill text from spec wording; semantic orphaning

Q-IMPL counting rule: a definition is `### Q-IMPL-…` under docs/spec/**; a
reference is any other occurrence under docs/, skills/, agents/, tools/
excluding docs/research/**, the placeholders (Q-IMPL-NNN, Q-IMPL-1,
Q-IMPL-ISSUE42*, Q-IMPL-ISSUE57-001, unknown <WS> tokens), and anything inside
fenced code or inline backticks.  Full text: the module docstring.

--fix whitelist (exactly these; each prints changed paths, is a no-op when
re-run, never touches last_updated, never writes under another workstream):
  %s
exit codes: 0 no fail finding; 1 fail finding(s); 2 usage / repository error
""" % ", ".join(FIXABLE)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="sdd-gc",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Drift sweep for the SDD docs corpus: delegated skill lint, docs/ cross-links "
                    "and ids, Q-IMPL orphans, index/directory and plan-history checks.",
        epilog=HELP_EPILOG,
    )
    ap.add_argument("--report", action="store_true",
                    help="run every sweep and print findings plus the summary line (default)")
    ap.add_argument("--fast", action="store_true",
                    help="lint + cross-links + Q-IMPL only; no history or date walks (pre-commit profile)")
    ap.add_argument("--workstream", metavar="ID",
                    help="marker 4: scope spec-approval (and staleness) to docs/ws/ID/; default all")
    ap.add_argument("--fix", metavar="RULE",
                    help="apply one whitelisted rewrite and print the paths changed")
    ap.add_argument("--root", metavar="PATH",
                    help="repository root (default: git rev-parse --show-toplevel)")
    ap.add_argument("--self-test", action="store_true",
                    help="build the temporary fixture tree and assert the sweep contracts")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()

    # Repository root: --root or the enclosing git toplevel; must be a git repo.
    if args.root:
        root = Path(args.root).resolve()
        probe = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True) if root.is_dir() else None
        if probe is None or probe.returncode != 0:
            print(f"error: {root} is not a git repository")
            return 2
    else:
        probe = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        if probe.returncode != 0:
            print("error: current directory is not a git repository (pass --root)")
            return 2
        root = Path(probe.stdout.strip())
    if not (root / "docs").is_dir():
        print(f"error: {root} has no docs/ directory")
        return 2

    if args.fix is not None:
        # Both unknown and known non-fixable rules exit 2 with the same phrase.
        if args.fix not in FIXABLE:
            kind = "" if args.fix in ALL_RULES else "unknown rule; "
            print(f"error: {kind}{args.fix} is not a fixable rule (fixable: {', '.join(FIXABLE)})")
            return 2

    gc = Gc(root, workstream=args.workstream, fast=args.fast, lint_suite_rules=_LINT_SUITE_RULES)
    if args.fix is not None:
        return gc.fix(args.fix)
    if gc.lint_path() is None:
        print(f"error: linter missing — expected {root / 'tools' / 'sdd-skill-lint.py'}")
        return 2
    return gc.run()


if __name__ == "__main__":
    sys.exit(main())
