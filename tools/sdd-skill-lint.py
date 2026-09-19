#!/usr/bin/env python3
"""sdd-skill-lint — consistency linter for the SDD skill suite.

Catches the classes of cross-skill drift found in the 2026-07-23 audit:

  * malformed or mismatched SKILL.md frontmatter (name != directory, missing
    description, orphan skill directories, agent files without frontmatter)
  * descriptions that violate the repo quality check "state when to use AND
    when not to use"
  * forbidden stale phrases that earlier audits removed (e.g. "upgrade to v2",
    "assign new domain prefixes") — each rule may allowlist legitimate
    negative mentions or historical citations
  * required cross-file contract markers (e.g. the `**Depends on**` field must
    exist in sdd-plan, `{qimpl_block}` in fan-out.md) so a contract edited in
    one file cannot silently vanish from its counterpart
  * duplicate/broken ordinals in numbered lists outside code fences
  * relative Markdown links and backtick-quoted `references/` /
    `skills/<skill>/references/` / `docs/spec/*.md` paths that do not resolve
  * SKILL.md entry points that outgrow a table of contents (warn > 400 lines,
    fail > 1000)

Every finding carries a `fix:` remediation line. Findings have a severity:
`fail` sets exit code 1; `warn` is printed with a `WARN ` prefix and counted
in the summary but never affects the exit code.

Usage:
  tools/sdd-skill-lint.py [REPO_ROOT]   # lint (default: repo containing this script)
  tools/sdd-skill-lint.py --self-test   # run built-in fixture tests
  tools/sdd-skill-lint.py --help

Exit codes: 0 = clean, 1 = findings, 2 = usage/internal error.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import re
import shutil
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Rule tables — extend these when a new audit closes a new class of drift.
# ---------------------------------------------------------------------------

# Phrases that must not (re)appear. `allow` regexes whitelist matching lines
# (negative mentions, historical citations). `files` limits the rule's scope
# to paths containing that substring; None means every linted file. The
# optional `allow_files` list names repo-relative files the row skips entirely
# (file-granular allowlist, consulted before the line loop; the scan itself
# stays raw-line and fence-inclusive) — rows without it behave as before.
FORBIDDEN = [
    {
        "pattern": r"docs/spikes",
        "files": None,
        # sdd-implement's "do not create docs/spikes" negative mention and the
        # citations of the shipped RS-006 artifact are legitimate.
        "allow": [r"Do not create a separate", r"dispatch-concurrency"],
        "reason": "spike artifacts belong under docs/research/RS-* (audit F1)",
        "fix": "point spike output at docs/research/RS-NNN-{topic}/ instead",
    },
    {"pattern": r"assign new domain prefixes", "files": None, "allow": [],
     "reason": "file splits must keep requirement IDs permanent (audit F3)",
     "fix": "say that split files keep their existing requirement IDs"},
    {"pattern": r"upgrade to v2", "files": None, "allow": [],
     "reason": "version-check wording must not hardcode v2 (audit F13)",
     "fix": "say `upgrade to the latest version` (or run sdd-migrate)"},
    {"pattern": r"start fresh with v2", "files": None, "allow": [],
     "reason": "greenfield wording must not hardcode v2 (final review #1)",
     "fix": "say `start fresh with the latest layout`"},
    {"pattern": r"30 min max", "files": None, "allow": [],
     "reason": "budgets are stated in observable units (audit P3)",
     "fix": "state the budget in tool calls / approaches / files, not minutes"},
    {"pattern": r"budget: 30min", "files": None, "allow": [],
     "reason": "budgets are stated in observable units (audit P3)",
     "fix": "state the budget in tool calls / approaches / files, not minutes"},
    {"pattern": r"\[Priority:", "files": None, "allow": [r"no separate"],
     "reason": "priority is encoded by the modal verb only (audit P7)",
     "fix": "drop the [Priority: …] tag; use MUST / SHOULD / MAY in the statement"},
    {"pattern": r"no plan index in v4", "files": None, "allow": [],
     "reason": "v4 per-workstream plan indexes exist (audit F17)",
     "fix": "say the plan index lives at docs/ws/<id>/plan.md under marker 4"},
    {"pattern": r"skills/\*/SKILL\.md", "files": "sdd-review", "allow": [],
     "reason": "sdd-review must not hardcode this repo's layout (audit F11)",
     "fix": "describe the reviewed skill files generically (`the skill files`)"},
    {"pattern": r"v1 limitations", "files": None, "allow": [],
     "reason": "stale USAGE heading (audit F14)",
     "fix": "rename the heading to `Limitations` (version-neutral)"},
    {"pattern": r"version: 2\.0", "files": "sdd-migrate", "allow": [],
     "reason": "index version: is a content counter, not a format signal (audit F20)",
     "fix": "gate on docs/.sdd-version, not on the index `version:` field"},
    {"pattern": r"Co-Authored-By", "files": None, "allow": [],
     "reason": "repo convention: no attribution lines in committed content",
     "fix": "delete the Co-Authored-By line"},
    # -- harness-p2: telemetry lives in gitignored `.sdd/` and is orchestrator-only.
    #    Raw-line scan (fences included) — a skill must not even show the path in
    #    an example. File-granular allowlist per telemetry.md §Lint Guard; USAGE.md
    #    is operator documentation that may name the path (REQ-SKILL-HARNESSP2-008;
    #    skill_files() also lints USAGE.md, so it is listed — deviation recorded as a
    #    Q-IMPL in the Chunk 6 return, minted by the orchestrator at plan close).
    {"pattern": r"\.sdd/", "files": None, "allow": [],
     "allow_files": ["skills/sdd-orchestrate/SKILL.md",
                     "skills/sdd-orchestrate/references/telemetry.md",
                     "skills/sdd-orchestrate/references/write-scope.md",
                     "skills/sdd-orchestrate/USAGE.md"],
     "reason": "telemetry is orchestrator-written and never a phase-detection or staleness input (REQ-ORCH-014)",
     "fix": "remove the reference — skills never read .sdd/; only sdd-orchestrate's telemetry stub "
            "and references/telemetry.md may name it"},
]

# Contract markers that must keep existing where a counterpart file relies on
# them. `min` is the minimum occurrence count in that file. Rows may carry
# `"severity": "warn"` (default `fail`).
REQUIRED = [
    {"file": "skills/sdd-orchestrate/SKILL.md", "pattern": r"research_id", "min": 3,
     "reason": "kickoff research_id contract (audit F10) spans table/KICKOFF/picker",
     "fix": "keep `research_id` in the entry table, KICKOFF and the picker stub"},
    {"file": "skills/sdd-plan/SKILL.md", "pattern": r"\*\*Depends on\*\*", "min": 3,
     "reason": "canonical chunk-dependency field consumed by fan-out (audit F7)",
     "fix": "restore the `**Depends on**` field in the chunk template, example and rules"},
    {"file": "skills/sdd-orchestrate/references/fan-out.md", "pattern": r"\{qimpl_block\}", "min": 2,
     "reason": "per-leaf Q-IMPL block slot (audit F5): template + slot contract",
     "fix": "keep the `{qimpl_block}` slot in the leaf template and its slot contract"},
    {"file": "skills/sdd-implement/SKILL.md", "pattern": r"Parallel-dispatch exception", "min": 1,
     "reason": "leaf-side half of the Q-IMPL block contract (audit F5)",
     "fix": "restore the `Parallel-dispatch exception` bullet under Q-IMPL numbering"},
    {"file": "skills/sdd-plan/SKILL.md", "pattern": r"last_updated: YYYY-MM-DD", "min": 1,
     "reason": "single-milestone plan frontmatter that staleness checks key off (audit F2)",
     "fix": "keep `last_updated: YYYY-MM-DD` in the plan frontmatter template"},
    {"file": "skills/sdd-research/SKILL.md", "pattern": r"early_exit: true", "min": 1,
     "reason": "research early-exit marker the orchestrate picker relies on",
     "fix": "keep the `early_exit: true` findings frontmatter marker"},
    {"file": "skills/sdd-review/SKILL.md", "pattern": r"`questions:` frontmatter", "min": 1,
     "reason": "research review reads questions from findings frontmatter (audit F9)",
     "fix": "say the research review reads the `questions:` frontmatter of findings.md"},
    {"file": "skills/sdd-orchestrate/references/dispatch-templates.md", "pattern": r"non-interactive", "min": 2,
     "reason": "both pipeline and review dispatch templates carry the clause (audit F15)",
     "fix": "add the `non-interactive` clause to every dispatch template"},
    {"file": "skills/sdd-implement/SKILL.md", "pattern": r"status:.*`active`", "min": 1,
     "reason": "plan status lifecycle executor: planned→active (final review #5)",
     "fix": "keep the step that flips plan `status:` to `active`"},
    {"file": "skills/sdd-implement/SKILL.md", "pattern": r"status:.*`complete`", "min": 1,
     "reason": "plan status lifecycle executor: →complete (final review #5)",
     "fix": "keep the completion step that sets plan `status:` to `complete`"},
    # -- v5 core contract rows (skill-lint-v5.md §REQUIRED Rows — Core, REQ-LINT-005)
    {"file": "skills/sdd-orchestrate/SKILL.md", "pattern": r"fix[- ]loop cap|iteration N of 3", "min": 1,
     "reason": "stage fix-loop cap the gate counts down (REQ-HARN-001)",
     "fix": "keep the `fix-loop cap` / `iteration N of 3` gate text in §The gate"},
    {"file": "skills/sdd-orchestrate/SKILL.md", "pattern": r"replan re-entry cap", "min": 1,
     "reason": "replan re-entry cap derived from `-replan-` archives (REQ-HARN-002)",
     "fix": "keep the `replan re-entry cap` paragraph in §The gate"},
    {"file": "skills/sdd-orchestrate/references/dispatch-templates.md", "pattern": r"Budget:", "min": 3,
     "reason": "pipeline + review + verifier dispatch templates carry a Budget: line (REQ-HARN-004)",
     "fix": "add the `Budget:` line to the pipeline, review and chunk-verifier dispatch templates"},
    {"file": "skills/sdd-orchestrate/references/fan-out.md", "pattern": r"Budget:", "min": 1,
     "reason": "fan-out leaf template carries a Budget: line (REQ-HARN-004)",
     "fix": "add the `Budget:` line to the leaf dispatch template in fan-out.md"},
    {"file": "skills/sdd-review/SKILL.md", "pattern": r"VERDICT: APPROVE \| APPROVE_WITH_FIXES \| REJECT", "min": 1,
     "reason": "review verdict token producer (REQ-HARN-013); consumer is sdd-orchestrate/SKILL.md",
     "fix": "restore the `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT` token line — "
            "its consumer lives in skills/sdd-orchestrate/SKILL.md"},
    {"file": "skills/sdd-orchestrate/SKILL.md", "pattern": r"(?<!CHUNK_)(?<!RED_)VERDICT:", "min": 1,
     "reason": "review verdict token consumer (REQ-HARN-013); producer is sdd-review/SKILL.md",
     "fix": "keep the review `VERDICT:` parse step in §The gate — its producer lives in "
            "skills/sdd-review/SKILL.md"},
    {"file": "skills/sdd-orchestrate/references/dispatch-templates.md", "pattern": r"CHUNK_VERDICT: PASS \| FAIL", "min": 1,
     "reason": "chunk-verifier verdict token producer (REQ-HARN-014); consumer is sdd-orchestrate/SKILL.md",
     "fix": "restore `CHUNK_VERDICT: PASS | FAIL` in the chunk-verifier dispatch template — "
            "its consumer lives in skills/sdd-orchestrate/SKILL.md"},
    {"file": "skills/sdd-orchestrate/SKILL.md", "pattern": r"CHUNK_VERDICT:", "min": 1,
     "reason": "chunk-verifier verdict consumer (REQ-HARN-014); producer is dispatch-templates.md",
     "fix": "keep the `CHUNK_VERDICT:` line in the per-chunk gate — its producer lives in "
            "skills/sdd-orchestrate/references/dispatch-templates.md"},
    {"file": "skills/sdd-replan/SKILL.md", "pattern": r"-replan-", "min": 1,
     "reason": "`-replan-` archive filename the re-entry cap counts (REQ-HARN-003)",
     "fix": "keep the `{date}-replan-{reason}.md` archive filename convention"},
    # -- v5 remaining contract rows (skill-lint-v5.md §REQUIRED Rows — Remaining, REQ-LINT-006)
    {"file": "skills/sdd-orchestrate/references/dispatch-templates.md", "pattern": r"RETURN:", "min": 2,
     "reason": "pipeline + verifier templates require the RETURN: block (REQ-HARN-009)",
     "fix": "keep the `RETURN:` block requirement in the pipeline and chunk-verifier templates"},
    {"file": "skills/sdd-orchestrate/references/fan-out.md", "pattern": r"RETURN:", "min": 1,
     "reason": "fan-out leaf template requires the RETURN: block (REQ-HARN-009)",
     "fix": "keep the `RETURN:` block requirement in the leaf dispatch template"},
    {"file": "skills/sdd-orchestrate/references/dispatch-templates.md",
     "pattern": r"status: COMPLETE \| PARTIAL \| BLOCKED \| BUDGET_EXHAUSTED", "min": 1,
     "reason": "own-line status token the orchestrator parses first (REQ-HARN-009)",
     "fix": "keep the `status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED` token line"},
    {"file": "skills/sdd-orchestrate/references/dispatch-templates.md", "pattern": r"\{repair_packet\}", "min": 2,
     "reason": "fix re-dispatch repair-packet slot: template + slot contract (REQ-HARN-011)",
     "fix": "keep the `{repair_packet}` slot in the fix re-dispatch template and its slot contract"},
    {"file": "skills/sdd-orchestrate/references/dispatch-templates.md", "pattern": r"Write scope:", "min": 3,
     "reason": "pipeline + review + verifier templates declare a Write scope: (REQ-HARN-020)",
     "fix": "add the `Write scope:` line to the pipeline, review and chunk-verifier templates"},
    {"file": "skills/sdd-orchestrate/references/fan-out.md", "pattern": r"Write scope:", "min": 1,
     "reason": "fan-out leaf template declares a Write scope: (REQ-HARN-020)",
     "fix": "add the `Write scope:` line to the leaf dispatch template in fan-out.md"},
    {"file": "skills/sdd-implement/SKILL.md", "pattern": r"oscillation", "min": 1,
     "reason": "attempt-ledger oscillation stuck rule (REQ-HARN-007)",
     "fix": "keep the `oscillation` rule under stuck detection"},
    {"file": "skills/sdd-implement/SKILL.md", "pattern": r"checkpoint", "min": 1,
     "reason": "circuit-break checkpoint format in the blocked-task note (REQ-HARN-008)",
     "fix": "keep the circuit-break `checkpoint` format under stuck detection"},
    {"file": "skills/sdd-replan/SKILL.md", "pattern": r"checkpoint", "min": 1,
     "reason": "circuit-break checkpoint intake as replan stuck state (REQ-HARN-008)",
     "fix": "keep the step that reads the blocked-task `checkpoint` note as stuck state"},
    # -- harness-p2 contract rows (REQ-LINT-HARNESSP2-001): adversarial-verify.md and
    #    arbitrated-handoff.md §Skill and Lint Changes
    {"file": "skills/sdd-orchestrate/references/dispatch-templates.md", "pattern": r"RED_VERDICT: BROKEN \| HELD", "min": 1,
     "reason": "red-team verdict token producer (adversarial-verify.md); consumer is sdd-orchestrate/SKILL.md",
     "fix": "restore `RED_VERDICT: BROKEN | HELD` in the RED TEAM dispatch template — "
            "its consumer lives in skills/sdd-orchestrate/SKILL.md"},
    {"file": "skills/sdd-orchestrate/SKILL.md", "pattern": r"RED_VERDICT:", "min": 1,
     "reason": "red-team verdict consumer in §The gate signal order; producer is dispatch-templates.md",
     "fix": "keep the `RED_VERDICT:` parse step in §The gate (verify stage) — its producer lives in "
            "skills/sdd-orchestrate/references/dispatch-templates.md"},
    {"file": "skills/sdd-orchestrate/references/loop-control.md", "pattern": r"REVIEW: CONTRADICTION", "min": 1,
     "reason": "contradiction pause is raised and handled by the orchestrator (REQ-SKILL-HARNESSP2-003); "
               "SKILL.md §The gate carries the pointer",
     "fix": "keep the `REVIEW: CONTRADICTION` pause in loop-control.md — its pointer lives in "
            "skills/sdd-orchestrate/SKILL.md §The gate"},
    {"file": "skills/sdd-review/SKILL.md", "pattern": r"M1:.*affects", "min": 1,
     "reason": "Material template line carries `affects` for contradiction-class resolution (REQ-SKILL-HARNESSP2-006)",
     "fix": "restore `affects` on the `M1:` Material template line — its consumer lives in "
            "skills/sdd-orchestrate/references/loop-control.md"},
    # -- harness-p4 contract row (REQ-LINT-HARNESSP4-002): the post-decision
    #    commit-fidelity token `COMMIT: COMPLETE | INCOMPLETE`
    #    (skill-lint-v5.md §`REQUIRED` Row — `COMMIT: COMPLETE | INCOMPLETE`).
    #    The pattern matches the token or its family spelling and never a file
    #    that only names `SCOPE:` — the same guard the `CHUNK_VERDICT:` row uses.
    {"file": "skills/sdd-orchestrate/references/loop-control.md",
     "pattern": r"COMMIT: (COMPLETE \| INCOMPLETE|COMPLETE|INCOMPLETE)", "min": 1,
     "reason": "post-decision `COMMIT:` gate signal — §5 order item 8 / position 2b (REQ-HARN-HARNESSP4-001)",
     "fix": "keep the `COMMIT: COMPLETE | INCOMPLETE` closing line in loop-control.md §5 — its defining "
            "section is skills/sdd-orchestrate/references/write-scope.md §7"},
    {"file": "skills/sdd-orchestrate/SKILL.md",
     "pattern": r"COMMIT: (COMPLETE \| INCOMPLETE|COMPLETE|INCOMPLETE)", "min": 1,
     "reason": "post-decision `COMMIT:` one-line summary in §The gate (REQ-HARN-HARNESSP4-001)",
     "fix": "keep the `COMMIT: COMPLETE | INCOMPLETE` line in SKILL.md §The gate — its defining "
            "section is skills/sdd-orchestrate/references/write-scope.md §7"},
]

# SKILL.md size thresholds (strict `>`), module constants so a later audit can
# retune them without touching check logic. references/*.md and USAGE.md are
# exempt — the entry point is what must read as a table of contents.
# skill-lint-v5.md §`[template-drift]` (REQ-LINT-HARNESSP4-001): fenced leaf
# bodies that a spec restates verbatim must stay byte-identical to their source
# of record, `references/dispatch-templates.md`. One row per restated body.
# `anchor` is the fence's FIRST line (so the rule survives a heading rename) and
# is matched on both sides; the comparison is byte-for-byte on the fence body
# with only the fence markers stripped — no whitespace normalisation, because
# the column-0 token contract of REQ-HARN-HARNESSP4-007 is itself a whitespace
# fact. Every row carries the one fix: the skill side is the source of record.
TEMPLATE_SOURCE = "skills/sdd-orchestrate/references/dispatch-templates.md"
TEMPLATE_DRIFT_FIX = (
    "edit skills/sdd-orchestrate/references/dispatch-templates.md (source of record) — "
    "the spec side is Approved and stable; if the spec is the intended change, amend both in one commit"
)
TEMPLATE_PAIRS = [
    {"anchor": "You are a non-interactive chunk-close verifier. Do NOT ask questions.",
     "body": "CHUNK VERIFIER dispatch prompt body (incl. the RETURN: block)",
     "spec": "docs/spec/harness-chunk-verifier.md", "section": "§Verifier Dispatch Template",
     "fix": TEMPLATE_DRIFT_FIX},
    {"anchor": "CHUNK_VERDICT: PASS  iff  Check 1 has zero blocking findings",
     "body": "CHUNK VERIFIER verdict rule",
     "spec": "docs/spec/harness-chunk-verifier.md", "section": "§Verdict Rule",
     "fix": TEMPLATE_DRIFT_FIX},
    {"anchor": "You are a non-interactive RED TEAM subagent — the adversarial second executor of",
     "body": "RED TEAM dispatch prompt body",
     "spec": "docs/spec/adversarial-verify.md", "section": "§Red Dispatch Template",
     "fix": TEMPLATE_DRIFT_FIX},
    {"anchor": "## Red team — <spec.md> acceptance criteria",
     "body": "RED TEAM RETURN: block (return-contract example)",
     "spec": "docs/spec/adversarial-verify.md", "section": "§Return Contract and `RED_VERDICT:`",
     "fix": TEMPLATE_DRIFT_FIX},
]

SIZE_WARN_LINES = 400   # entry point should read as a table of contents
SIZE_FAIL_LINES = 1000  # project guideline (REQ-ORCH-019)
SIZE_FIX = ("move detail to references/ and leave a stub; the entry point should "
            "read as a table of contents")

# Fixed remediation strings for the checks that have no rule table.
LINK_FIX = "correct the relative path or create the target file"
PATH_FIX = "create the referenced file or correct the path"
ORDINAL_FIX = "renumber the list so ordinals are consecutive from 1 outside code fences"
NAME_FIX = "set name: to the directory name"

# Every phase skill gates its layout on the version marker.
VERSION_GATED_SKILLS = [
    "sdd-research", "sdd-requirements", "sdd-specs", "sdd-plan",
    "sdd-implement", "sdd-verify", "sdd-replan", "sdd-migrate", "sdd-orchestrate",
]

# The seven skills that carry the collapsed v4 ownership summary (audit P1).
V4_CONTRACT_SKILLS = [
    "sdd-research", "sdd-requirements", "sdd-specs", "sdd-plan",
    "sdd-implement", "sdd-verify", "sdd-replan",
]

# Description must state when NOT to use the skill (repo quality check).
NOT_USE_RE = re.compile(r"\b(Skip|Do NOT|Do not use|not for)\b", re.IGNORECASE)


class Linter:
    def __init__(self, root: Path, suite_rules: bool = True):
        self.root = root
        # `suite_rules=False` skips the repo-specific contract rows (REQUIRED,
        # VERSION_GATED_SKILLS, V4_CONTRACT_SKILLS) so self-test fixtures can
        # drive `run()` end to end without the real skill suite present.
        self.suite_rules = suite_rules
        # (severity, rendered text) — severity is "fail" or "warn".
        self.findings: list[tuple[str, str]] = []

    # -- helpers ------------------------------------------------------------

    def flag(self, path: Path, line_no: int | None, rule: str, msg: str, fix: str,
             severity: str = "fail") -> None:
        """Record a finding. `fix` is a required positional so no code path can
        emit a finding without remediation (a call without it is a TypeError)."""
        assert severity in ("fail", "warn"), severity
        rel = path.relative_to(self.root) if path.is_absolute() else path
        loc = f"{rel}:{line_no}" if line_no else str(rel)
        self.findings.append((severity, f"{loc}: [{rule}] {msg}\n    fix: {fix}"))

    def skill_dir_of(self, f: Path) -> Path:
        """The `skills/<skill>/` directory a linted file belongs to."""
        rel = f.relative_to(self.root / "skills")
        return self.root / "skills" / rel.parts[0]

    def skill_files(self) -> list[Path]:
        """All lintable Markdown files under skills/ (SKILL.md, USAGE.md, references)."""
        return sorted((self.root / "skills").rglob("*.md")) if (self.root / "skills").is_dir() else []

    @staticmethod
    def frontmatter(text: str) -> dict[str, str] | None:
        """Parse the leading YAML frontmatter block; minimal, stdlib-only.

        Returns key -> raw value (folded `>` blocks concatenated), or None if
        the file does not start with a well-formed `---` block.
        """
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return None
        fields: dict[str, str] = {}
        key = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return fields
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                fields[key] = "" if val in (">", "|") else val
            elif key and (line.startswith("  ") or not line.strip()):
                fields[key] = (fields[key] + " " + line.strip()).strip()
            else:
                return None  # stray unindented line inside frontmatter
        return None  # unterminated block

    # -- checks -------------------------------------------------------------

    def check_structure(self) -> None:
        """Every skill dir has a SKILL.md; frontmatter well-formed; name matches dir."""
        skills_dir = self.root / "skills"
        if not skills_dir.is_dir():
            self.flag(self.root, None, "structure", "skills/ directory not found",
                      "run the linter from the repo root or pass REPO_ROOT")
            return
        for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            sk = d / "SKILL.md"
            if not sk.is_file():
                self.flag(d, None, "structure", "skill directory has no SKILL.md",
                          "add a SKILL.md with name/description frontmatter or delete the directory")
                continue
            fm = self.frontmatter(sk.read_text(encoding="utf-8"))
            if fm is None:
                self.flag(sk, 1, "frontmatter", "missing or malformed YAML frontmatter",
                          "start the file with a `---` block carrying name: and description:")
                continue
            name = fm.get("name", "")
            if not name:
                self.flag(sk, 1, "frontmatter", "frontmatter has no `name:`", NAME_FIX)
            elif name != d.name:
                self.flag(sk, 1, "frontmatter", f"name `{name}` != directory `{d.name}`",
                          NAME_FIX)
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name or "x"):
                self.flag(sk, 1, "frontmatter", f"name `{name}` is not kebab-case",
                          "rename the directory and name: to lowercase kebab-case")
            desc = fm.get("description", "")
            if not desc:
                self.flag(sk, 1, "frontmatter", "frontmatter has no `description:`",
                          "add a description: stating when to use and when not to use the skill")
            elif not NOT_USE_RE.search(desc):
                self.flag(sk, 1, "description",
                          "description never states when NOT to use the skill "
                          "(repo quality check)",
                          "add a `Skip …` / `Do NOT use …` clause to the description")
        # Agent files must carry frontmatter too (repo quality check).
        agents_dir = self.root / "agents"
        if agents_dir.is_dir():
            for a in sorted(agents_dir.glob("*.md")):
                fm = self.frontmatter(a.read_text(encoding="utf-8"))
                if fm is None:
                    self.flag(a, 1, "frontmatter", "agent file missing frontmatter",
                              "start the agent file with a `---` block carrying name:")
                elif not fm.get("name"):
                    self.flag(a, 1, "frontmatter", "agent frontmatter has no `name:`",
                              "set name: to the agent file's basename")

    def check_forbidden(self) -> None:
        for f in self.skill_files():
            rel = f.relative_to(self.root).as_posix()
            for rule in FORBIDDEN:
                if rule["files"] and rule["files"] not in rel:
                    continue
                # Per-row file-granular allowlist: the whole file is skipped for
                # this row only; every other row still scans it.
                if rel in rule.get("allow_files", ()):
                    continue
                pat = re.compile(rule["pattern"])
                allows = [re.compile(a) for a in rule["allow"]]
                for no, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if pat.search(line) and not any(a.search(line) for a in allows):
                        self.flag(f, no, "forbidden",
                                  f"`{rule['pattern']}` — {rule['reason']}",
                                  rule['fix'], rule.get("severity", "fail"))

    def check_required(self) -> None:
        if not self.suite_rules:
            return
        for rule in REQUIRED:
            rel, pattern, minimum = rule["file"], rule["pattern"], rule["min"]
            severity = rule.get("severity", "fail")
            f = self.root / rel
            if not f.is_file():
                self.flag(Path(rel), None, "required", "file missing entirely",
                          f"restore the file — {rule['reason']}", severity)
                continue
            n = len(re.findall(pattern, f.read_text(encoding="utf-8")))
            if n < minimum:
                self.flag(f, None, "required",
                          f"`{pattern}` found {n}x, need >= {minimum} — {rule['reason']}",
                          rule['fix'], severity)
        for name in VERSION_GATED_SKILLS:
            f = self.root / "skills" / name / "SKILL.md"
            if f.is_file() and "docs/.sdd-version" not in f.read_text(encoding="utf-8"):
                self.flag(f, None, "required", "never reads `docs/.sdd-version` "
                          "(every phase skill gates on the version marker)",
                          "add the version-gate paragraph that reads `docs/.sdd-version` on entry")
        for name in V4_CONTRACT_SKILLS:
            f = self.root / "skills" / name / "SKILL.md"
            if f.is_file() and "common v4 contract" not in f.read_text(encoding="utf-8"):
                self.flag(f, None, "required",
                          "lost the collapsed v4 ownership summary (audit P1)",
                          "restore the `common v4 contract` ownership summary paragraph")

    @staticmethod
    def fences(text: str) -> list[tuple[int, str]]:
        """Every ``` fence in `text` as (1-based line of the opening marker, body).

        The body is the raw text strictly between the two marker lines — the
        fence markers are stripped and nothing else is touched (no strip(), no
        whitespace fold), so a comparison of two bodies is byte-for-byte.
        """
        lines = text.split("\n")
        out: list[tuple[int, str]] = []
        i = 0
        while i < len(lines):
            if lines[i].startswith("```"):
                j = i + 1
                while j < len(lines) and not lines[j].startswith("```"):
                    j += 1
                out.append((i + 1, "\n".join(lines[i + 1:j])))
                i = j + 1
            else:
                i += 1
        return out

    def check_template_drift(self) -> None:
        """[template-drift]: each TEMPLATE_PAIRS restatement equals its source fence.

        Repo-specific (the rows name this repo's specs), so it runs with the
        other suite rows only. A spec file absent from the root warns, never
        fails (a consumer repo linted via REPO_ROOT has no docs/spec/ — the
        F11 principle); a present file that lost its anchored fence fails
        alone with the counterpart named (Q-IMPL-HARNESSP4-008).
        """
        if not self.suite_rules:
            return
        source = self.root / TEMPLATE_SOURCE
        if not source.is_file():
            return  # the REQUIRED rows already report a missing source of record
        # newline="" keeps CR/LF bytes as written — the comparison is byte-for-byte.
        src_fences = self.fences(source.read_text(encoding="utf-8", newline=""))
        for pair in TEMPLATE_PAIRS:
            anchor = pair["anchor"]
            src = [(n, b) for n, b in src_fences if b.split("\n", 1)[0].startswith(anchor)]
            spec_path = self.root / pair["spec"]
            if not spec_path.is_file():
                self.flag(spec_path, None, "template-drift",
                          f"restating spec for the {pair['body']} is absent — pair not checked",
                          pair["fix"], severity="warn")
                continue
            spec_fences = [(n, b) for n, b in self.fences(spec_path.read_text(encoding="utf-8", newline=""))
                           if b.split("\n", 1)[0].startswith(anchor)]
            if not src:
                self.flag(source, None, "template-drift",
                          f"no fence opens with `{anchor}` — the {pair['body']} source of record is gone "
                          f"while {pair['spec']} {pair['section']} still restates it", pair["fix"])
                continue
            if not spec_fences:
                self.flag(spec_path, None, "template-drift",
                          f"no fence opens with `{anchor}` — {pair['section']} no longer restates the "
                          f"{pair['body']} of dispatch-templates.md L{src[0][0]}", pair["fix"])
                continue
            src_line, src_body = src[0]
            for spec_line, spec_body in spec_fences:
                if spec_body != src_body:
                    self.flag(spec_path, spec_line, "template-drift",
                              f"fenced body diverges from dispatch-templates.md L{src_line}", pair["fix"])

    def check_ordinals(self) -> None:
        """Numbered-list ordinals outside code fences must increment by one.

        Catches the `4.` / `4.` duplicate the final review found. Blocks reset
        on blank lines, headings, or unindented prose; indented lines are item
        continuations.
        """
        item_re = re.compile(r"^(\d+)\.\s")
        for f in self.skill_files():
            in_fence = False
            prev: int | None = None
            for no, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    prev = None
                    continue
                if in_fence:
                    continue
                m = item_re.match(line)
                if m:
                    n = int(m.group(1))
                    if prev is not None and n != prev + 1:
                        self.flag(f, no, "ordinal",
                                  f"list ordinal {n} follows {prev} (expected {prev + 1})",
                                  ORDINAL_FIX)
                    prev = n
                elif line.startswith((" ", "\t")) and line.strip():
                    continue  # continuation of the current item
                else:
                    prev = None  # blank line / heading / prose ends the block

    def check_size(self) -> None:
        """`skills/*/SKILL.md` over SIZE_WARN_LINES warns, over SIZE_FAIL_LINES fails.

        Line count uses `wc -l` semantics (number of newline characters).
        Only entry points are checked — `references/*.md` and `USAGE.md` are exempt.
        """
        skills_dir = self.root / "skills"
        if not skills_dir.is_dir():
            return
        for sk in sorted(skills_dir.glob("*/SKILL.md")):
            n = sk.read_text(encoding="utf-8").count("\n")
            if n > SIZE_FAIL_LINES:
                self.flag(sk, None, "size", f"SKILL.md is {n} lines (> {SIZE_FAIL_LINES})",
                          SIZE_FIX)
            elif n > SIZE_WARN_LINES:
                self.flag(sk, None, "size", f"SKILL.md is {n} lines (> {SIZE_WARN_LINES})",
                          SIZE_FIX, "warn")

    def check_links(self) -> None:
        """Relative paths must resolve on disk.

        Two syntaxes outside fenced code: `[text](relative.md)` links resolve
        against the linting file's directory; backtick-quoted paths resolve per
        `resolve_backtick_path()`. Fenced examples are illustrative and skipped.
        """
        link_re = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
        code_re = re.compile(r"`([^`\n]+)`")
        for f in self.skill_files():
            in_fence = False
            for no, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue  # links inside template examples are illustrative
                for target in link_re.findall(line):
                    if target.startswith(("http://", "https://", "mailto:", "#")):
                        continue
                    path = target.split("#", 1)[0]
                    if not path:
                        continue
                    if not (f.parent / path).exists():
                        self.flag(f, no, "link", f"broken relative link `{target}`", LINK_FIX)
                for span in code_re.findall(line):
                    resolved = self.resolve_backtick_path(f, span)
                    if resolved is None:
                        continue
                    path, base, severity = resolved
                    if not (base / path).exists():
                        self.flag(f, no, "path", f"unresolved path `{path}`", PATH_FIX, severity)

    def resolve_backtick_path(self, f: Path, span: str) -> tuple[str, Path, str] | None:
        """Classify one backtick span; return (path, base dir, severity) or None.

        | span                                     | base            | severity |
        | `references/<file>`                      | the skill dir   | fail     |
        | `skills/<skill>/references/<file>`       | repo root       | fail     |
        | `docs/spec/<file>.md`                    | repo root       | warn     |

        Fragments (`#…`) and trailing punctuation are stripped. Globs and
        placeholders (`*`, `<`, `>`, `{`, `}`) and spans with whitespace are
        not literal filenames and are skipped. `docs/spec/` mentions only warn
        so the linter never assumes a consumer repo has this repo's layout.
        """
        path = span.split("#", 1)[0].rstrip(".,:;)")
        if not path or any(c in path for c in "*<>{}") or re.search(r"\s", path):
            return None
        if path.startswith("references/"):
            return path, self.skill_dir_of(f), "fail"
        if re.match(r"skills/[^/]+/references/", path):
            return path, self.root, "fail"
        if path.startswith("docs/spec/") and path.endswith(".md"):
            return path, self.root, "warn"
        return None

    # -- driver -------------------------------------------------------------

    def run(self) -> int:
        self.check_structure()
        self.check_forbidden()
        self.check_required()
        self.check_template_drift()
        self.check_ordinals()
        self.check_links()
        self.check_size()
        for severity, text in self.findings:
            print(("WARN " if severity == "warn" else "") + text)
        n_files = len(self.skill_files())
        n_fail = sum(1 for sev, _ in self.findings if sev == "fail")
        n_warn = len(self.findings) - n_fail
        # Exit 1 iff any `fail`; warnings are reported but never change the code.
        if n_fail:
            print(f"\nFAIL: {n_fail} finding(s), {n_warn} warning(s)")
            return 1
        if n_warn:
            print(f"OK: {n_files} file(s) clean, {n_warn} warning(s)")
        else:
            print(f"OK: {n_files} file(s) clean")
        return 0


# ---------------------------------------------------------------------------
# Self-test: seed a fixture repo with one violation per check and assert the
# linter reports each rule (and that a clean fixture passes).
# ---------------------------------------------------------------------------

def _fixture_skill(root: Path, name: str, body: str, *, lines: int | None = None) -> Path:
    """Write a minimal clean skill dir under `root/skills/<name>` and return its dir.

    `body` is appended after well-formed frontmatter. When `lines` is given the
    file is padded with filler lines so its `wc -l` count equals `lines`.
    """
    d = root / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    text = f"---\nname: {name}\ndescription: >\n  Use for X. Skip for Y.\n---\n\n# {name}\n\n{body}"
    if not text.endswith("\n"):
        text += "\n"
    if lines is not None:
        pad = lines - text.count("\n")
        assert pad >= 0, "fixture body longer than requested line count"
        text += "filler\n" * pad
    (d / "SKILL.md").write_text(text, encoding="utf-8")
    return d


def _run_capture(root: Path) -> tuple[int, str]:
    """Run the full driver on a fixture repo (suite-specific rows off) and capture stdout."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = Linter(root, suite_rules=False).run()
    return code, buf.getvalue()


def self_test() -> int:
    global FORBIDDEN  # step 8 swaps in a temp copy of the table, then restores it
    failures: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            failures.append(msg)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # -- 1. one violation per check class fires; every finding carries fix:
        bad = root / "skills" / "bad-skill"
        bad.mkdir(parents=True)
        (bad / "SKILL.md").write_text(
            "---\n"
            "name: wrong-name\n"          # frontmatter: name != dir
            "description: >\n"
            "  Does things.\n"            # description: no skip clause
            "---\n\n"
            "# Bad\n\n"
            "Spike output goes to docs/spikes/topic.md.\n"   # forbidden
            "See [ref](references/missing.md).\n\n"          # broken link
            "1. one\n"
            "2. two\n"
            "2. dup\n",                   # ordinal
            encoding="utf-8",
        )
        (root / "skills" / "orphan-dir").mkdir()             # structure: no SKILL.md
        linter = Linter(root)
        # Scope the fixture run to checks that do not assume the real suite.
        linter.check_structure()
        linter.check_forbidden()
        linter.check_ordinals()
        linter.check_links()
        text = "\n".join(t for _, t in linter.findings)
        expected = ["[frontmatter]", "[description]", "[forbidden]",
                    "[ordinal]", "[link]", "[structure]"]
        missing = [e for e in expected if e not in text]
        check(not missing, f"rules never fired: {missing}\n{text}")
        for sev, t in linter.findings:
            check(sev == "fail", f"unexpected severity {sev!r} in bad fixture: {t}")
            m = re.search(r"\n    fix: (.+)$", t)
            check(bool(m and m.group(1).strip()), f"finding without remediation: {t}")

        # -- 2. clean fixture: zero findings from the same checks
        good_root = root / "clean"
        _fixture_skill(good_root, "good-skill", "1. one\n2. two\n")
        clean = Linter(good_root)
        clean.check_structure()
        clean.check_forbidden()
        clean.check_ordinals()
        clean.check_links()
        check(not clean.findings,
              "clean fixture produced findings:\n" + "\n".join(t for _, t in clean.findings))

        # -- 3. flag() without fix is a TypeError (remediation is mandatory)
        try:
            Linter(root).flag(Path("x"), 1, "rule", "msg")  # type: ignore[call-arg]
            check(False, "flag() accepted a call without fix")
        except TypeError:
            pass

        # -- 4. size: 401 lines warns (exit 0, '1 warning(s)'); 400 is silent
        warn_root = root / "warn"
        _fixture_skill(warn_root, "long-skill", "prose\n", lines=401)
        code, out = _run_capture(warn_root)
        check(code == 0, f"warn-only fixture exited {code}:\n{out}")
        check("WARN " in out and "[size]" in out and "401 lines (> 400)" in out,
              f"401-line SKILL.md did not warn:\n{out}")
        check("OK: 1 file(s) clean, 1 warning(s)" in out, f"warn summary wrong:\n{out}")
        edge_root = root / "edge"
        _fixture_skill(edge_root, "edge-skill", "prose\n", lines=400)
        code, out = _run_capture(edge_root)
        check(code == 0 and "[size]" not in out and "OK: 1 file(s) clean\n" in out,
              f"400-line SKILL.md must not warn:\n{out}")

        # -- 5. size: 1001 lines fails (exit 1); references/*.md are exempt
        fail_root = root / "fail"
        d = _fixture_skill(fail_root, "huge-skill", "prose\n", lines=1001)
        (d / "references").mkdir()
        (d / "references" / "big.md").write_text("x\n" * 1200, encoding="utf-8")
        code, out = _run_capture(fail_root)
        check(code == 1, f"1001-line fixture exited {code}:\n{out}")
        check("1001 lines (> 1000)" in out and "big.md" not in out,
              f"size fail wrong or references/ not exempt:\n{out}")
        check("FAIL: 1 finding(s), 0 warning(s)" in out, f"fail summary wrong:\n{out}")

        # -- 6. backtick path resolution
        ref_root = root / "refs"
        d = _fixture_skill(
            ref_root, "ref-skill",
            "Read `references/present.md` first, then `references/missing.md`.\n"
            "Also `skills/ref-skill/references/present.md` and "
            "`skills/ref-skill/references/absent.md`:\n"
            "Contract: `docs/spec/nowhere.md#section`.\n"
            "Globs like `references/*.md` are skipped.\n"
            "```\n`references/fenced-missing.md`\n```\n",
        )
        (d / "references").mkdir()
        (d / "references" / "present.md").write_text("# ok\n", encoding="utf-8")
        code, out = _run_capture(ref_root)
        check(code == 1, f"backtick fixture exited {code}:\n{out}")
        check("`references/missing.md`" in out, f"backtick references/ miss not flagged:\n{out}")
        check("`skills/ref-skill/references/absent.md`" in out,
              f"backtick skills/<skill>/references/ miss not flagged:\n{out}")
        check("WARN " in out and "`docs/spec/nowhere.md`" in out,
              f"docs/spec/ mention should warn:\n{out}")
        check("present.md" not in out, f"existing backtick path flagged:\n{out}")
        check("fenced-missing" not in out and "*.md" not in out,
              f"fenced or glob backtick path flagged:\n{out}")
        check("FAIL: 2 finding(s), 1 warning(s)" in out, f"backtick summary wrong:\n{out}")
        for sev, t in Linter(ref_root, suite_rules=False).findings:
            check("fix: " in t, f"finding without fix: {t}")

        # -- 7. contract-row mutation: copy the real suite, strip one REQUIRED
        #       marker at a time; the suite lint must exit 1 and print that
        #       row's own fix string (REQ-LINT-005/006 mutation test).
        real_skills = Path(__file__).resolve().parent.parent / "skills"
        if real_skills.is_dir():
            for rule in REQUIRED:
                mut_root = root / "mut"
                if mut_root.exists():
                    shutil.rmtree(mut_root)
                shutil.copytree(real_skills, mut_root / "skills")
                target = mut_root / rule["file"]
                check(target.is_file(), f"REQUIRED row targets a missing file: {rule['file']}")
                if not target.is_file():
                    continue
                stripped, n = re.subn(rule["pattern"], "", target.read_text(encoding="utf-8"))
                check(n >= rule["min"],
                      f"marker `{rule['pattern']}` occurs {n}x in {rule['file']} (< {rule['min']})")
                target.write_text(stripped, encoding="utf-8")
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    code = Linter(mut_root).run()
                out = buf.getvalue()
                check(code == 1, f"stripping `{rule['pattern']}` from {rule['file']} did not fail:\n{out}")
                check(rule['fix'] in out,
                      f"fix string not printed for `{rule['pattern']}` in {rule['file']}:\n{out}")
            # every rule-table row carries a fix (the mutation loop above proves REQUIRED;
            # FORBIDDEN rows are asserted by shape)
            check(all(r.get('fix') for r in FORBIDDEN), "FORBIDDEN row without fix")
            # harness-p2 adds four REQUIRED rows (RED_VERDICT producer/consumer,
            # REVIEW: CONTRADICTION, Material `affects`) — REQ-LINT-HARNESSP2-001
            check(len(REQUIRED) >= 32, f"expected the harness-p2 REQUIRED rows (>= 32), found {len(REQUIRED)}")
            # d2 negative: a SKILL.md carrying only `RED_VERDICT: HELD` must NOT
            # satisfy the review-verdict consumer row (the `(?<!RED_)` lookbehind).
            d2 = next((r for r in REQUIRED
                       if r["file"] == "skills/sdd-orchestrate/SKILL.md" and "VERDICT" in r["pattern"]
                       and "CHUNK" in r["pattern"] and "RED_" in r["pattern"]),
                      {"pattern": "<missing d2 row>"})
            check(d2["pattern"] == r"(?<!CHUNK_)(?<!RED_)VERDICT:",
                  f"d2 consumer pattern drifted: {d2['pattern']}")
            check(re.search(d2["pattern"], "RED_VERDICT: HELD\nCHUNK_VERDICT: PASS\n") is None,
                  "d2 pattern matched RED_VERDICT:/CHUNK_VERDICT: — a file with only those tokens would pass")
            check(re.search(d2["pattern"], "parse the VERDICT: line") is not None,
                  "d2 pattern no longer matches a bare VERDICT:")
            # harness-p4 adds the two `COMMIT:` rows (REQ-LINT-HARNESSP4-002); the
            # mutation loop above already strips each one. Negative control: a
            # file carrying only `SCOPE: CLEAN` must NOT satisfy the row, and the
            # pattern must accept both the token and its family spelling.
            commit_rows = [r for r in REQUIRED if r["pattern"].startswith("COMMIT: ")]
            check(len(commit_rows) == 2, f"expected two COMMIT: REQUIRED rows, found {len(commit_rows)}")
            for r in commit_rows:
                check(re.search(r["pattern"], "SCOPE: CLEAN\nCHUNK_VERDICT: PASS\n") is None,
                      "COMMIT: row pattern matched a file with only SCOPE:/CHUNK_VERDICT: tokens")
                for good in ("COMMIT: COMPLETE (3 paths)", "COMMIT: INCOMPLETE (1 observed, not landed: x)",
                             "`COMMIT: COMPLETE | INCOMPLETE`"):
                    check(re.search(r["pattern"], good) is not None,
                          f"COMMIT: row pattern no longer matches `{good}`")
                check("write-scope.md §7" in r["fix"], "COMMIT: row fix must point at write-scope.md §7")
            # -- 7c. [template-drift] (REQ-LINT-HARNESSP4-001): the four pair rows
            #       compare byte-identical on the shipped set (skills + docs/spec
            #       copied to a temp root); one character changed inside the RED
            #       TEAM `RETURN:` block of the temp dispatch-templates.md exits 1
            #       with a finding naming adversarial-verify.md and the fix, and
            #       fires no chunk-verifier row.
            check(len(TEMPLATE_PAIRS) == 4, f"expected the four TEMPLATE_PAIRS rows, found {len(TEMPLATE_PAIRS)}")
            check(all(r.get("fix") for r in TEMPLATE_PAIRS), "TEMPLATE_PAIRS row without fix")
            real_spec = real_skills.parent / "docs" / "spec"
            check(real_spec.is_dir(), "docs/spec/ missing beside the real skill suite")
            if real_spec.is_dir():
                drift_root = root / "drift"
                shutil.copytree(real_skills, drift_root / "skills")
                shutil.copytree(real_spec, drift_root / "docs" / "spec")
                clean = Linter(drift_root)
                clean.check_template_drift()
                check(clean.findings == [],
                      "shipped restated bodies are not byte-identical:\n" + "\n".join(t for _, t in clean.findings))
                target = drift_root / TEMPLATE_SOURCE
                text = target.read_text(encoding="utf-8", newline="")
                red_return = next((b for _, b in Linter.fences(text)
                                   if b.startswith("## Red team — <spec.md> acceptance criteria")), None)
                check(red_return is not None and "RETURN:" in red_return,
                      "RED TEAM RETURN: fence not found in dispatch-templates.md")
                if red_return is not None and "RETURN:" in red_return:
                    body_lines = red_return.split("\n")
                    key_line = body_lines[body_lines.index("RETURN:") + 1]      # `  status: COMPLETE`
                    flipped = key_line[:-1] + ("X" if key_line[-1] != "X" else "Y")
                    target.write_text(text.replace(red_return, red_return.replace(key_line, flipped, 1), 1),
                                      encoding="utf-8", newline="")
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        code = Linter(drift_root).run()
                    out = buf.getvalue()
                    drift_lines = [ln for ln in out.splitlines() if "[template-drift]" in ln]
                    check(code == 1, f"RED TEAM RETURN: mutation did not fail the lint:\n{out}")
                    check(len(drift_lines) == 1 and "adversarial-verify.md" in drift_lines[0]
                          and "diverges from dispatch-templates.md L" in drift_lines[0],
                          f"expected one [template-drift] line naming adversarial-verify.md:\n{out}")
                    check(TEMPLATE_DRIFT_FIX in out, f"[template-drift] fix string not printed:\n{out}")
                    check(not any("harness-chunk-verifier.md" in ln for ln in drift_lines),
                          f"chunk-verifier pair fired on a RED TEAM mutation:\n{out}")

        # -- 7b. the shipped `\.sdd/` FORBIDDEN row (REQ-TELEM-HARNESSP2-007,
        #       REQ-LINT-HARNESSP2-002): fenced mention in a non-allowlisted skill
        #       fails with the row's fix; the same text at each allowlisted path
        #       passes (file-granular allow_files, raw-line fence-inclusive scan).
        sdd_row = next((r for r in FORBIDDEN if r["pattern"] == r"\.sdd/"), None)
        check(sdd_row is not None, "FORBIDDEN has no `\\.sdd/` row")
        if sdd_row is not None:
            check(sdd_row["files"] is None and sdd_row["allow"] == [], "`\\.sdd/` row must be repo-wide with allow: []")
            check(sdd_row.get("severity", "fail") == "fail", "`\\.sdd/` row must be fail severity")
            for required_allow in ("skills/sdd-orchestrate/SKILL.md",
                                   "skills/sdd-orchestrate/references/telemetry.md",
                                   "skills/sdd-orchestrate/references/write-scope.md"):
                check(required_allow in sdd_row["allow_files"], f"`\\.sdd/` allow_files lacks {required_allow}")
            sdd_root = root / "sddrow"
            fenced = "```\n.sdd/telemetry.jsonl\n```\n"
            _fixture_skill(sdd_root, "sdd-plan", fenced)            # non-allowlisted → must fail
            code, out = _run_capture(sdd_root)
            check(code == 1 and sdd_row["fix"] in out,
                  f"fenced .sdd/ mention in sdd-plan/SKILL.md did not fail with the row's fix:\n{out}")
            sdd_ok = root / "sddallow"
            for rel in sdd_row["allow_files"]:
                target = sdd_ok / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.name == "SKILL.md":
                    _fixture_skill(sdd_ok, target.parent.name, fenced)
                else:
                    target.write_text(fenced, encoding="utf-8")
            # every allowlisted path needs a well-formed SKILL.md beside it
            if not (sdd_ok / "skills" / "sdd-orchestrate" / "SKILL.md").is_file():
                _fixture_skill(sdd_ok, "sdd-orchestrate", "prose\n")
            code, out = _run_capture(sdd_ok)
            check(code == 0, f"allowlisted .sdd/ fixtures did not pass:\n{out}")

        # -- 8. allow_files mechanics: a synthetic FORBIDDEN row (never the
        #       shipped list) with a file-granular allowlist. The pattern inside
        #       a fence in a non-allowlisted fixture fails with the row's fix;
        #       the same text in an allowlisted fixture passes (raw-line scan).
        synthetic = {
            "pattern": r"\.selftest-forbidden/", "files": None, "allow": [],
            "allow_files": ["skills/allowed-skill/references/allowed.md"],
            "reason": "synthetic allow_files row", "fix": "SYNTHETIC-ALLOW-FILES-FIX",
        }
        af_root = root / "allowfiles"
        body = "```\n.selftest-forbidden/telemetry.jsonl\n```\n"
        _fixture_skill(af_root, "plain-skill", body)
        d = _fixture_skill(af_root, "allowed-skill", "prose\n")
        (d / "references").mkdir()
        (d / "references" / "allowed.md").write_text(body, encoding="utf-8")
        shipped = FORBIDDEN
        FORBIDDEN = shipped + [synthetic]       # temp copy of the table
        try:
            af = Linter(af_root, suite_rules=False)
            af.check_forbidden()
        finally:
            FORBIDDEN = shipped                  # shipped list untouched
        af_text = "\n".join(t for _, t in af.findings)
        check("plain-skill/SKILL.md" in af_text and "SYNTHETIC-ALLOW-FILES-FIX" in af_text,
              f"allow_files row did not fire on the non-allowlisted fenced fixture:\n{af_text}")
        check("allowed.md" not in af_text,
              f"allow_files did not skip the allowlisted file:\n{af_text}")
        check(len(af.findings) == 1, f"expected exactly one allow_files finding:\n{af_text}")

    if failures:
        print("SELF-TEST FAIL:\n- " + "\n- ".join(failures))
        return 1
    print("SELF-TEST OK: all rule classes fire; fix/warn/size/backtick/allow_files fixtures pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="sdd-skill-lint",
        description="Consistency linter for the SDD skill suite "
                    "(frontmatter, drift phrases, contract markers, ordinals, links, "
                    "backtick paths, SKILL.md size).",
    )
    ap.add_argument("root", nargs="?", default=None,
                    help="repository root to lint (default: repo containing this script)")
    ap.add_argument("--self-test", action="store_true",
                    help="run built-in fixture tests instead of linting")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    return Linter(root).run()


if __name__ == "__main__":
    sys.exit(main())
