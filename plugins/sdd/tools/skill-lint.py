#!/usr/bin/env python3
"""skill-lint — consistency linter for the SDD skill suite.

Catches the classes of cross-skill drift found in the 2026-07-23 audit:

  * malformed or mismatched SKILL.md frontmatter (name != directory, missing
    description, orphan skill directories, agent files without frontmatter)
  * descriptions that violate the repo quality check "state when to use AND
    when not to use"
  * forbidden stale phrases that earlier audits removed (e.g. "upgrade to v2",
    "assign new domain prefixes") — each rule may allowlist legitimate
    negative mentions or historical citations
  * required cross-file contract markers (e.g. the `**Depends on**` field must
    exist in plan, `{qimpl_block}` in fan-out.md) so a contract edited in
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
  tools/skill-lint.py [CORPUS_ROOT] # lint (default: the invocation cwd; the
                                    # suite root defaults to the plugin root
                                    # containing this script)
  tools/skill-lint.py --self-test   # run built-in fixture tests
  tools/skill-lint.py --help

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
from collections.abc import Callable
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
        # implement's "do not create docs/spikes" negative mention and the
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
     "fix": "say `upgrade to the latest version` (or run migrate)"},
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
    {"pattern": r"skills/\*/SKILL\.md", "files": "skills/review/", "allow": [],
     "reason": "review must not hardcode this repo's layout (audit F11 — ungated set "
               "only; exceptions check_retired_prefix and TEMPLATE_PAIRS's spec side)",
     "fix": "describe the reviewed skill files generically (`the skill files`)"},
    {"pattern": r"v1 limitations", "files": None, "allow": [],
     "reason": "stale USAGE heading (audit F14)",
     "fix": "rename the heading to `Limitations` (version-neutral)"},
    {"pattern": r"version: 2\.0", "files": "skills/migrate/", "allow": [],
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
     "allow_files": ["skills/orchestrate/SKILL.md",
                     "skills/orchestrate/references/telemetry.md",
                     "skills/orchestrate/references/write-scope.md",
                     "skills/orchestrate/USAGE.md"],
     "reason": "telemetry is orchestrator-written and never a phase-detection or staleness input (REQ-ORCH-014)",
     "fix": "remove the reference — skills never read .sdd/; only orchestrate's telemetry stub "
            "and references/telemetry.md may name it"},
]

# Contract markers that must keep existing where a counterpart file relies on
# them. `min` is the minimum occurrence count in that file. Rows may carry
# `"severity": "warn"` (default `fail`).
REQUIRED = [
    {"file": "skills/orchestrate/SKILL.md", "pattern": r"research_id", "min": 3,
     "reason": "kickoff research_id contract (audit F10) spans table/KICKOFF/picker",
     "fix": "keep `research_id` in the entry table, KICKOFF and the picker stub"},
    {"file": "skills/plan/SKILL.md", "pattern": r"\*\*Depends on\*\*", "min": 3,
     "reason": "canonical chunk-dependency field consumed by fan-out (audit F7)",
     "fix": "restore the `**Depends on**` field in the chunk template, example and rules"},
    {"file": "skills/orchestrate/references/fan-out.md", "pattern": r"\{qimpl_block\}", "min": 2,
     "reason": "per-leaf Q-IMPL block slot (audit F5): template + slot contract",
     "fix": "keep the `{qimpl_block}` slot in the leaf template and its slot contract"},
    {"file": "skills/implement/SKILL.md", "pattern": r"Parallel-dispatch exception", "min": 1,
     "reason": "leaf-side half of the Q-IMPL block contract (audit F5)",
     "fix": "restore the `Parallel-dispatch exception` bullet under Q-IMPL numbering"},
    {"file": "skills/plan/SKILL.md", "pattern": r"last_updated: YYYY-MM-DD", "min": 1,
     "reason": "single-milestone plan frontmatter that staleness checks key off (audit F2)",
     "fix": "keep `last_updated: YYYY-MM-DD` in the plan frontmatter template"},
    {"file": "skills/research/SKILL.md", "pattern": r"early_exit: true", "min": 1,
     "reason": "research early-exit marker the orchestrate picker relies on",
     "fix": "keep the `early_exit: true` findings frontmatter marker"},
    {"file": "skills/review/SKILL.md", "pattern": r"`questions:` frontmatter", "min": 1,
     "reason": "research review reads questions from findings frontmatter (audit F9)",
     "fix": "say the research review reads the `questions:` frontmatter of findings.md"},
    {"file": "skills/orchestrate/references/dispatch-templates.md", "pattern": r"non-interactive", "min": 2,
     "reason": "both pipeline and review dispatch templates carry the clause (audit F15)",
     "fix": "add the `non-interactive` clause to every dispatch template"},
    {"file": "skills/implement/SKILL.md", "pattern": r"status:.*`active`", "min": 1,
     "reason": "plan status lifecycle executor: planned→active (final review #5)",
     "fix": "keep the step that flips plan `status:` to `active`"},
    {"file": "skills/implement/SKILL.md", "pattern": r"status:.*`complete`", "min": 1,
     "reason": "plan status lifecycle executor: →complete (final review #5)",
     "fix": "keep the completion step that sets plan `status:` to `complete`"},
    # -- v5 core contract rows (skill-lint-v5.md §REQUIRED Rows — Core, REQ-LINT-005)
    {"file": "skills/orchestrate/SKILL.md", "pattern": r"fix[- ]loop cap|iteration N of 3", "min": 1,
     "reason": "stage fix-loop cap the gate counts down (REQ-HARN-001)",
     "fix": "keep the `fix-loop cap` / `iteration N of 3` gate text in §The gate"},
    {"file": "skills/orchestrate/SKILL.md", "pattern": r"replan re-entry cap", "min": 1,
     "reason": "replan re-entry cap derived from `-replan-` archives (REQ-HARN-002)",
     "fix": "keep the `replan re-entry cap` paragraph in §The gate"},
    {"file": "skills/orchestrate/references/dispatch-templates.md", "pattern": r"Budget:", "min": 3,
     "reason": "pipeline + review + verifier dispatch templates carry a Budget: line (REQ-HARN-004)",
     "fix": "add the `Budget:` line to the pipeline, review and chunk-verifier dispatch templates"},
    {"file": "skills/orchestrate/references/fan-out.md", "pattern": r"Budget:", "min": 1,
     "reason": "fan-out leaf template carries a Budget: line (REQ-HARN-004)",
     "fix": "add the `Budget:` line to the leaf dispatch template in fan-out.md"},
    {"file": "skills/review/SKILL.md", "pattern": r"VERDICT: APPROVE \| APPROVE_WITH_FIXES \| REJECT", "min": 1,
     "reason": "review verdict token producer (REQ-HARN-013); consumer is orchestrate/SKILL.md",
     "fix": "restore the `VERDICT: APPROVE | APPROVE_WITH_FIXES | REJECT` token line — "
            "its consumer lives in skills/orchestrate/SKILL.md"},
    {"file": "skills/orchestrate/SKILL.md", "pattern": r"(?<!CHUNK_)(?<!RED_)VERDICT:", "min": 1,
     "reason": "review verdict token consumer (REQ-HARN-013); producer is review/SKILL.md",
     "fix": "keep the review `VERDICT:` parse step in §The gate — its producer lives in "
            "skills/review/SKILL.md"},
    {"file": "skills/orchestrate/references/dispatch-templates.md", "pattern": r"CHUNK_VERDICT: PASS \| FAIL", "min": 1,
     "reason": "chunk-verifier verdict token producer (REQ-HARN-014); consumer is orchestrate/SKILL.md",
     "fix": "restore `CHUNK_VERDICT: PASS | FAIL` in the chunk-verifier dispatch template — "
            "its consumer lives in skills/orchestrate/SKILL.md"},
    {"file": "skills/orchestrate/SKILL.md", "pattern": r"CHUNK_VERDICT:", "min": 1,
     "reason": "chunk-verifier verdict consumer (REQ-HARN-014); producer is dispatch-templates.md",
     "fix": "keep the `CHUNK_VERDICT:` line in the per-chunk gate — its producer lives in "
            "skills/orchestrate/references/dispatch-templates.md"},
    {"file": "skills/replan/SKILL.md", "pattern": r"-replan-", "min": 1,
     "reason": "`-replan-` archive filename the re-entry cap counts (REQ-HARN-003)",
     "fix": "keep the `{date}-replan-{reason}.md` archive filename convention"},
    # -- v5 remaining contract rows (skill-lint-v5.md §REQUIRED Rows — Remaining, REQ-LINT-006)
    {"file": "skills/orchestrate/references/dispatch-templates.md", "pattern": r"RETURN:", "min": 2,
     "reason": "pipeline + verifier templates require the RETURN: block (REQ-HARN-009)",
     "fix": "keep the `RETURN:` block requirement in the pipeline and chunk-verifier templates"},
    {"file": "skills/orchestrate/references/fan-out.md", "pattern": r"RETURN:", "min": 1,
     "reason": "fan-out leaf template requires the RETURN: block (REQ-HARN-009)",
     "fix": "keep the `RETURN:` block requirement in the leaf dispatch template"},
    {"file": "skills/orchestrate/references/dispatch-templates.md",
     "pattern": r"status: COMPLETE \| PARTIAL \| BLOCKED \| BUDGET_EXHAUSTED", "min": 1,
     "reason": "own-line status token the orchestrator parses first (REQ-HARN-009)",
     "fix": "keep the `status: COMPLETE | PARTIAL | BLOCKED | BUDGET_EXHAUSTED` token line"},
    {"file": "skills/orchestrate/references/dispatch-templates.md", "pattern": r"\{repair_packet\}", "min": 2,
     "reason": "fix re-dispatch repair-packet slot: template + slot contract (REQ-HARN-011)",
     "fix": "keep the `{repair_packet}` slot in the fix re-dispatch template and its slot contract"},
    {"file": "skills/orchestrate/references/dispatch-templates.md", "pattern": r"Write scope:", "min": 3,
     "reason": "pipeline + review + verifier templates declare a Write scope: (REQ-HARN-020)",
     "fix": "add the `Write scope:` line to the pipeline, review and chunk-verifier templates"},
    {"file": "skills/orchestrate/references/fan-out.md", "pattern": r"Write scope:", "min": 1,
     "reason": "fan-out leaf template declares a Write scope: (REQ-HARN-020)",
     "fix": "add the `Write scope:` line to the leaf dispatch template in fan-out.md"},
    {"file": "skills/implement/SKILL.md", "pattern": r"oscillation", "min": 1,
     "reason": "attempt-ledger oscillation stuck rule (REQ-HARN-007)",
     "fix": "keep the `oscillation` rule under stuck detection"},
    {"file": "skills/implement/SKILL.md", "pattern": r"checkpoint", "min": 1,
     "reason": "circuit-break checkpoint format in the blocked-task note (REQ-HARN-008)",
     "fix": "keep the circuit-break `checkpoint` format under stuck detection"},
    {"file": "skills/replan/SKILL.md", "pattern": r"checkpoint", "min": 1,
     "reason": "circuit-break checkpoint intake as replan stuck state (REQ-HARN-008)",
     "fix": "keep the step that reads the blocked-task `checkpoint` note as stuck state"},
    # -- harness-p2 contract rows (REQ-LINT-HARNESSP2-001): adversarial-verify.md and
    #    arbitrated-handoff.md §Skill and Lint Changes
    {"file": "skills/orchestrate/references/dispatch-templates.md", "pattern": r"RED_VERDICT: BROKEN \| HELD", "min": 1,
     "reason": "red-team verdict token producer (adversarial-verify.md); consumer is orchestrate/SKILL.md",
     "fix": "restore `RED_VERDICT: BROKEN | HELD` in the RED TEAM dispatch template — "
            "its consumer lives in skills/orchestrate/SKILL.md"},
    {"file": "skills/orchestrate/SKILL.md", "pattern": r"RED_VERDICT:", "min": 1,
     "reason": "red-team verdict consumer in §The gate signal order; producer is dispatch-templates.md",
     "fix": "keep the `RED_VERDICT:` parse step in §The gate (verify stage) — its producer lives in "
            "skills/orchestrate/references/dispatch-templates.md"},
    {"file": "skills/orchestrate/references/loop-control.md", "pattern": r"REVIEW: CONTRADICTION", "min": 1,
     "reason": "contradiction pause is raised and handled by the orchestrator (REQ-SKILL-HARNESSP2-003); "
               "SKILL.md §The gate carries the pointer",
     "fix": "keep the `REVIEW: CONTRADICTION` pause in loop-control.md — its pointer lives in "
            "skills/orchestrate/SKILL.md §The gate"},
    {"file": "skills/review/SKILL.md", "pattern": r"M1:.*affects", "min": 1,
     "reason": "Material template line carries `affects` for contradiction-class resolution (REQ-SKILL-HARNESSP2-006)",
     "fix": "restore `affects` on the `M1:` Material template line — its consumer lives in "
            "skills/orchestrate/references/loop-control.md"},
    # -- harness-p4 contract row (REQ-LINT-HARNESSP4-002): the post-decision
    #    commit-fidelity token `COMMIT: COMPLETE | INCOMPLETE`
    #    (skill-lint-v5.md §`REQUIRED` Row — `COMMIT: COMPLETE | INCOMPLETE`).
    #    The pattern matches the token or its family spelling and never a file
    #    that only names `SCOPE:` — the same guard the `CHUNK_VERDICT:` row uses.
    {"file": "skills/orchestrate/references/loop-control.md",
     "pattern": r"COMMIT: (COMPLETE \| INCOMPLETE|COMPLETE|INCOMPLETE)", "min": 1,
     "reason": "post-decision `COMMIT:` gate signal — §5 order item 8 / position 2b (REQ-HARN-HARNESSP4-001)",
     "fix": "keep the `COMMIT: COMPLETE | INCOMPLETE` closing line in loop-control.md §5 — its defining "
            "section is skills/orchestrate/references/write-scope.md §7"},
    {"file": "skills/orchestrate/SKILL.md",
     "pattern": r"COMMIT: (COMPLETE \| INCOMPLETE|COMPLETE|INCOMPLETE)", "min": 1,
     "reason": "post-decision `COMMIT:` one-line summary in §The gate (REQ-HARN-HARNESSP4-001)",
     "fix": "keep the `COMMIT: COMPLETE | INCOMPLETE` line in SKILL.md §The gate — its defining "
            "section is skills/orchestrate/references/write-scope.md §7"},
    # -- harness-p6 contract rows (REQ-LINT-HARNESSP6-001): the `PLAN:` pause
    #    token — the only gate token that shipped without a producer/consumer
    #    pair — and the `GIT_STATE` finding name, which would have shipped the
    #    same way (skill-lint-v5.md §`REQUIRED` Rows — `PLAN:` and `GIT_STATE`).
    {"file": "skills/orchestrate/references/loop-control.md",
     "pattern": r"PLAN: INCOMPLETE", "min": 1,
     "reason": "`PLAN: INCOMPLETE (N of M ticked)` pause producer — §6 pause family (REQ-LINT-HARNESSP6-001)",
     "fix": "keep the `PLAN: INCOMPLETE (N of M ticked)` pause in loop-control.md §6 — its defining "
            "section is docs/spec/harness-loop-control.md §Plan Completion Ownership; its consumer "
            "lives in skills/orchestrate/SKILL.md §The gate"},
    {"file": "skills/orchestrate/SKILL.md",
     "pattern": r"PLAN: INCOMPLETE", "min": 1,
     "reason": "`PLAN: INCOMPLETE` one-line summary in §The gate signal order (REQ-LINT-HARNESSP6-001)",
     "fix": "keep the `PLAN: INCOMPLETE (N of M ticked)` line in SKILL.md §The gate — its defining "
            "section is docs/spec/harness-loop-control.md §Plan Completion Ownership; its producer "
            "lives in skills/orchestrate/references/loop-control.md"},
    # `GIT_STATE` is a finding NAME rendered inside the `SCOPE:` block, not an
    # own-line gate token, so the pattern carries no trailing colon and no
    # option-set alternation — the row guards the name's presence, which is all
    # that is needed to make its deletion fail.
    {"file": "skills/orchestrate/references/write-scope.md",
     "pattern": r"GIT_STATE", "min": 1,
     "reason": "`GIT_STATE` finding name producer — §5 rendering / §3 git-state observation "
               "(REQ-HARN-HARNESSP6-001)",
     "fix": "keep the `GIT_STATE` finding in write-scope.md §5 — its defining section is "
            "docs/spec/harness-write-scope.md §Git-State Observation; its consumer lives in "
            "skills/orchestrate/SKILL.md §The gate"},
    {"file": "skills/orchestrate/SKILL.md",
     "pattern": r"GIT_STATE", "min": 1,
     "reason": "`GIT_STATE` finding name named in §The gate's `SCOPE:` summary (REQ-HARN-HARNESSP6-001)",
     "fix": "keep the `GIT_STATE` mention in SKILL.md §The gate — its defining section is "
            "docs/spec/harness-write-scope.md §Git-State Observation; its producer lives in "
            "skills/orchestrate/references/write-scope.md"},
    # -- harness-p6 contract rows (REQ-LINT-HARNESSP6-003): the L2 gate token
    #    `CONVERGENCE:` gets the same producer/consumer pair that guards
    #    `COMMIT:` (skill-lint-v5.md §`REQUIRED` Row — `CONVERGENCE:`).
    {"file": "skills/orchestrate/references/loop-control.md",
     "pattern": r"CONVERGENCE:", "min": 1,
     "reason": "`CONVERGENCE:` L2 gate token producer — §5 order item 6c (REQ-LINT-HARNESSP6-003)",
     "fix": "keep the `CONVERGENCE:` line in loop-control.md §5 item 6c / §5b — its defining "
            "section is docs/spec/harness-loop-control.md §Convergence Signal; its consumer "
            "lives in skills/orchestrate/SKILL.md §The gate"},
    {"file": "skills/orchestrate/SKILL.md",
     "pattern": r"CONVERGENCE:", "min": 1,
     "reason": "`CONVERGENCE:` one-line summary in §The gate signal order (REQ-LINT-HARNESSP6-003)",
     "fix": "keep the `CONVERGENCE:` line in SKILL.md §The gate — its defining "
            "section is docs/spec/harness-loop-control.md §Convergence Signal; its producer "
            "lives in skills/orchestrate/references/loop-control.md"},
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
TEMPLATE_SOURCE = "skills/orchestrate/references/dispatch-templates.md"
TEMPLATE_DRIFT_FIX = (
    "edit skills/orchestrate/references/dispatch-templates.md (source of record) — "
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

# ---------------------------------------------------------------------------
# The retired-prefix rule (REQ-NAME-MARKETPLACE-009).
#
# The skills and tools dropped their `sdd-` prefix when this repository became
# the `sdd` plugin (docs/spec/skill-namespace-rename.md). This rule stops the
# retirement eroding as new text is written: a retired-prefix skill or tool name
# appearing in the LIVE rename scope is a finding.
#
# Two skips, evaluated in this order:
#   1. occurrences inside fenced code blocks and inside inline-backtick spans —
#      the same skip the drift sweep's orphan-id sweep applies, so a live
#      document may quote the retired form when describing the historical
#      corpus;
#   2. the short self-exemption path list below, carried IN THE RULE, naming the
#      four documents whose subject *is* this rule.
# There is no general allowlist and no per-occurrence suppression comment.
#
# Two scope boundaries sit beside the scope list, both for the same reason —
# a finding there would be unfixable by construction, not merely inconvenient:
#   * `tools/fixtures/`, whose bytes are part of what they test and which
#     REQ-PC-MARKETPLACE-005 freezes (Q-IMPL-MARKETPLACE-007);
#   * `docs/requirements/traceability.md`, which is DERIVED — regenerated from
#     the per-workstream files under `docs/ws/`, the corpus this rename
#     deliberately excludes, so sweeping it would only desynchronize it from its
#     own sources (Q-IMPL-MARKETPLACE-008).
# Neither is a per-occurrence allowlist and neither touches the self-exemption
# list, which stays at the four documents whose subject is the rule.
RETIRED_SKILLS = [
    "research", "requirements", "specs", "plan", "implement", "verify",
    "replan", "migrate", "orchestrate", "review",
]
RETIRED_TOOLS = ["gc", "skill-lint", "telemetry", "scope-check-selftest", "eval"]
RETIRED_RE = re.compile(
    r"\bsdd-(?:"
    + "|".join(sorted(RETIRED_SKILLS + RETIRED_TOOLS, key=len, reverse=True))
    + r")\b"
)
# The four documents whose subject is the rule itself.
RETIRED_SELF_EXEMPT = (
    "CONTRIBUTING.md",
    "docs/requirements/integration/naming.md",
    "tools/skill-lint.py",
    "docs/spec/skill-namespace-rename.md",
)
# The live rename scope — every live area of the corpus, enumerated. It is the
# set of areas that describe the system AS IT IS NOW, so it grows whenever the
# repository grows a new live area: `agents/` and the `.claude-plugin/` manifest
# directory did not exist when the scope was first written as "six areas", and
# `CONTRIBUTING.md`, `LICENSE` and `.pre-commit-config.yaml` arrived with the
# same cycle (Q-IMPL-MARKETPLACE-022). An area left out is not policed at all,
# which is the failure mode the enumeration exists to prevent.
RETIRED_SCOPE_DIRS = ("skills", "tools", "agents", ".claude-plugin",
                      "docs/spec", "docs/requirements")
RETIRED_SCOPE_FILES = ("CLAUDE.md", "README.md", "CONTRIBUTING.md",
                       "LICENSE", ".pre-commit-config.yaml")
# Which root each scope entry is bound to (two-root-linter.md §4). `suite` and
# `corpus` name one root; `both` is the DEDUPLICATED UNION over resolved
# absolute paths, so with equal roots the entry set is exactly today's.
# `.claude-plugin` must be union-bound because after the move it exists at both
# roots and a one-root binding silently drops whichever manifest the other
# holds; the five root files, because the move edits some of them and they may
# exist at either root. Every entry of RETIRED_SCOPE_DIRS + RETIRED_SCOPE_FILES
# has a binding (asserted in the self-test) — an unbound entry is unwalked.
RETIRED_SCOPE_BINDING = {
    "skills": "suite",
    "tools": "suite",
    "agents": "suite",
    "docs/spec": "corpus",
    "docs/requirements": "corpus",
    ".claude-plugin": "both",
    "CLAUDE.md": "both",
    "README.md": "both",
    "CONTRIBUTING.md": "both",
    "LICENSE": "both",
    ".pre-commit-config.yaml": "both",
}
RETIRED_SCOPE_EXCLUDE_DIRS = ("fixtures",)
RETIRED_SCOPE_EXCLUDE_FILES = ("docs/requirements/traceability.md",)
RETIRED_SUFFIXES = (".md", ".org", ".py", ".txt", ".yaml", ".yml", ".json", ".toml", ".sh")
RETIRED_FIX = ("drop the retired prefix (the plugin namespace supplies it), or — when the text "
               "describes the historical corpus — quote the name in a backtick span or a fence")

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
    "research", "requirements", "specs", "plan",
    "implement", "verify", "replan", "migrate", "orchestrate",
]

# The seven skills that carry the collapsed v4 ownership summary (audit P1).
V4_CONTRACT_SKILLS = [
    "research", "requirements", "specs", "plan",
    "implement", "verify", "replan",
]

# Description must state when NOT to use the skill (repo quality check).
NOT_USE_RE = re.compile(r"\b(Skip|Do NOT|Do not use|not for)\b", re.IGNORECASE)


DUPLICATE_SWEEP_FIX = ("rebuild the two-root sweep as a set union over resolved "
                       "absolute paths (two-root-linter.md §2) — never as list "
                       "concatenation over swept_roots()")


def default_suite_root() -> Path:
    """The script's own plugin root — the directory holding `tools/<this file>`.

    Pre-move that resolves to the repository root; after the suite moves it
    resolves to `plugins/sdd` (two-root-linter.md §2). It is deliberately NOT
    the corpus-root default: the corpus root defaults to the invocation cwd.
    """
    return Path(__file__).resolve().parent.parent


def duplicate_free_findings(paths: list[Path]) -> list[tuple[Path, str, str]]:
    """The duplicate-freeness construction guard (two-root-linter.md §6).

    A **pure function over a list of paths returning findings**: one
    `(path, msg, fix)` triple per path occurring more than once once resolved
    to an absolute path; the empty list means the swept list is a set. It
    cannot fire for a union built as §2 specifies — it pins that the union
    stays a set and is never rebuilt as list concatenation by a later edit.
    """
    counts: dict[Path, int] = {}
    order: list[Path] = []
    for p in paths:
        key = Path(p).resolve()
        if key not in counts:
            counts[key] = 0
            order.append(key)
        counts[key] += 1
    return [(key,
             f"swept list holds {key} {counts[key]} times — the two-root sweep "
             f"must be a set union, not a concatenation",
             DUPLICATE_SWEEP_FIX)
            for key in order if counts[key] > 1]


def forbidden_findings(swept: list[Path], rel: Callable[[Path], Path],
                       rules: list[dict] | None = None,
                       ) -> list[tuple[Path, Path, int, dict]]:
    """The counting path as a pure function from a swept list to findings
    (two-root-linter.md §7) — one `(file, rendered path, line, rule)` per
    violating line in the list it is given.

    It is NOT the deduplicator: given a path twice it emits its findings twice,
    which is what makes case C's count-once assertion invertible. Deduplication
    stays inside §2's union builder. `rel` renders a swept file against the
    root it was walked from; the rendered path is what the row's `files`
    substring filter and its `allow_files` exact allowlist match against, so a
    suite-root file under nested roots matches the same entries it matches
    under equal roots.
    """
    out: list[tuple[Path, Path, int, dict]] = []
    for f in swept:
        local = rel(f)
        local_s = local.as_posix()
        for rule in (FORBIDDEN if rules is None else rules):
            if rule["files"] and rule["files"] not in local_s:
                continue
            # Per-row file-granular allowlist: the whole file is skipped for
            # this row only; every other row still scans it.
            if local_s in rule.get("allow_files", ()):
                continue
            pat = re.compile(rule["pattern"])
            allows = [re.compile(a) for a in rule["allow"]]
            for no, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if pat.search(line) and not any(a.search(line) for a in allows):
                    out.append((f, local, no, rule))
    return out


class Linter:
    def __init__(self, corpus_root: Path, suite_root: Path | None = None,
                 suite_rules: bool = True):
        # The two roots are constructor parameters and the only root-resolution
        # mechanism (two-root-linter.md §2): no environment variable, no CLI
        # option. `corpus_root` carries the CLI positional's value and defaults
        # (in main()) to the invocation cwd, never to the script's location.
        self.corpus_root = corpus_root
        self.suite_root = default_suite_root() if suite_root is None else suite_root
        # Alias kept for the checks still bound to a single root; they re-bind
        # per entry / per side in a later chunk.
        self.root = corpus_root
        # `suite_rules=False` skips the repo-specific contract rows (REQUIRED,
        # VERSION_GATED_SKILLS, V4_CONTRACT_SKILLS) so self-test fixtures can
        # drive `run()` end to end without the real skill suite present.
        self.suite_rules = suite_rules
        # (severity, rendered text) — severity is "fail" or "warn".
        self.findings: list[tuple[str, str]] = []
        # The construction guard reports at most once per run (`walk()` is
        # called by many checks); no invocation mode can skip it.
        self._guard_done = False

    # -- helpers ------------------------------------------------------------

    def flag(self, path: Path, line_no: int | None, rule: str, msg: str, fix: str,
             severity: str = "fail", *, rel: Path | None = None) -> None:
        """Record a finding. `fix` is a required positional so no code path can
        emit a finding without remediation (a call without it is a TypeError).

        `rel` overrides the generic per-root rendering of `self.rel()` with a
        path the caller already rendered against the root **that entry or side
        is bound to** (two-root-linter.md §4, §5). The generic `rel()` covers
        the walk only, and raises on a file under a root outside `swept_roots()`
        — a disjoint suite root's file, say — so a per-entry-bound check must
        supply its own rendering or the binding is unimplementable.
        """
        assert severity in ("fail", "warn"), severity
        rel = self.rel(path) if rel is None else rel
        loc = f"{rel}:{line_no}" if line_no else str(rel)
        self.findings.append((severity, f"{loc}: [{rule}] {msg}\n    fix: {fix}"))

    # -- the two roots ------------------------------------------------------

    def suite_contained(self) -> bool:
        """True iff the suite root is contained in the corpus root (§2).

        Equality counts as containment; the complement is the **disjoint**
        geometry — the consumer shape, where the suite is an installed plugin
        cache outside the operator's repository.
        """
        corpus = Path(self.corpus_root).resolve()
        suite = Path(self.suite_root).resolve()
        return suite == corpus or suite.is_relative_to(corpus)

    def swept_roots(self) -> list[Path]:
        """The set of roots the generic walk covers (two-root-linter.md §2).

        `{corpus_root} | {suite_root if contained in corpus_root}` — a set
        union computed over **resolved absolute paths**, with equality counting
        as containment and therefore degenerating to today's single walk. The
        roots are returned as given (not resolved) in a stable order, corpus
        first, so rendering keeps the caller's spelling.
        """
        roots = [self.corpus_root]
        corpus = Path(self.corpus_root).resolve()
        suite = Path(self.suite_root).resolve()
        if suite != corpus and self.suite_contained():
            roots.append(self.suite_root)
        return roots

    def walk(self) -> list[Path]:
        """The deduplicated union of `<root>/skills/**/*.md` over swept_roots()."""
        collected: list[Path] = []
        for r in self.swept_roots():
            d = r / "skills"
            if d.is_dir():
                collected.extend(sorted(d.rglob("*.md")))
        seen: set[Path] = set()
        swept: list[Path] = []
        for f in collected:
            key = f.resolve()
            if key in seen:
                continue
            seen.add(key)
            swept.append(f)
        self._guard_duplicate_free(swept)
        return swept

    def _guard_duplicate_free(self, swept: list[Path]) -> None:
        """The union builder's only production call of the §6 guard.

        On failure the observable is a `fail`-severity finding in this run's own
        findings list naming the duplicated path — the `flag()` default, never a
        warning, an exception or a bare exit code.
        """
        if self._guard_done:
            return
        self._guard_done = True
        for _path, msg, fix in duplicate_free_findings(swept):
            self.flag(self.corpus_root, None, "sweep-duplicate", msg, fix)

    def rel(self, f: Path) -> Path:
        """Render `f` relative to the swept root it was walked from (§2).

        The deepest matching root wins, so a file under a nested suite root
        renders without the nesting segment. A relative path passes through; a
        path under no swept root raises `ValueError` exactly as the former
        single-root rendering did.
        """
        if not f.is_absolute():
            return f
        roots = self.swept_roots()
        best: Path | None = None
        for candidate_roots in (roots, [Path(r).resolve() for r in roots]):
            target = f if candidate_roots is roots else f.resolve()
            for r in candidate_roots:
                try:
                    cand = target.relative_to(r)
                except ValueError:
                    continue
                if best is None or len(cand.parts) < len(best.parts):
                    best = cand
            if best is not None:
                return best
        return f.relative_to(self.corpus_root)

    def skill_dir_of(self, f: Path) -> Path:
        """The `skills/<skill>/` directory a linted file belongs to.

        Bound to the root the file was WALKED FROM — the same rule `rel()`
        uses (two-root-linter.md §2, §4). `self.root / "skills"` alone names
        the corpus root's tree, which after the move does not exist, so every
        suite-root file routed through `resolve_backtick_path()` for a
        `references/…` span raised `ValueError`. §4 binds `skills` to the
        suite root; §3's "links keep resolving against the corpus root" governs
        where a link TARGET resolves, not where a swept file's skill directory
        is located (C3.10, added post-plan from the Chunk 2 verification).
        """
        for r in self.swept_roots():
            base = r / "skills"
            try:
                rel = Path(f).resolve().relative_to(Path(base).resolve())
            except ValueError:
                continue
            return base / rel.parts[0]
        # A file under no swept root: fall back to the corpus binding, which
        # raises exactly as the former single-root rendering did.
        rel = f.relative_to(self.corpus_root / "skills")
        return self.corpus_root / "skills" / rel.parts[0]

    def skill_files(self) -> list[Path]:
        """All lintable Markdown files under skills/ (SKILL.md, USAGE.md, references).

        Delegates to the two-root `walk()`; with equal roots that is exactly
        today's single sorted walk.
        """
        return self.walk()

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
        """Every skill dir has a SKILL.md; frontmatter well-formed; name matches dir.

        `skills` and `agents` bind to the **swept-root union** — the same
        `swept_roots()` set that `walk()`, `rel()` and `skill_dir_of()` use —
        never to a single root. `self.root` (the corpus root) named a `skills/`
        that does not exist there after the move, so the check degraded to a
        single `[structure] skills/ directory not found` finding and every
        per-skill frontmatter and naming rule silently stopped running (C6.11).
        Rebinding it to `self.suite_root` alone fixed that symptom but made
        frontmatter a silent third exception to REQ-PKG-PACKAGING-005 — which
        puts frontmatter on the **corpus** root with exactly two stated
        exceptions — and raised an uncaught `ValueError` out of `rel()` under
        the disjoint geometry, whose suite root is outside `swept_roots()`.
        The union is what -005 and §4 together support: nested and equal roots
        reach the suite's `skills/` exactly as the suite binding did, the
        corpus's own `skills/` is policed again, and a disjoint suite is not
        walked, so no finding can name a path `rel()` cannot render
        (C8.1, added post-plan from the implement-stage review).
        """
        roots = self.swept_roots()
        skills_dirs = [r / "skills" for r in roots if (r / "skills").is_dir()]
        if not skills_dirs:
            self.flag(self.corpus_root, None, "structure", "skills/ directory not found",
                      "lint a root that holds skills/, or one containing the suite "
                      "root that does — the corpus root is the CLI positional and "
                      "defaults to the invocation cwd")
            return
        seen_dirs: set[Path] = set()
        for skills_dir in skills_dirs:
            for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
                if d.resolve() in seen_dirs:
                    continue
                seen_dirs.add(d.resolve())
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
        # Union-bound for the same reason as `skills` above.
        seen_agents: set[Path] = set()
        for agents_dir in (r / "agents" for r in roots):
            if agents_dir.is_dir():
                for a in sorted(agents_dir.glob("*.md")):
                    if a.resolve() in seen_agents:
                        continue
                    seen_agents.add(a.resolve())
                    fm = self.frontmatter(a.read_text(encoding="utf-8"))
                    if fm is None:
                        self.flag(a, 1, "frontmatter", "agent file missing frontmatter",
                                  "start the agent file with a `---` block carrying name:")
                    elif not fm.get("name"):
                        self.flag(a, 1, "frontmatter", "agent frontmatter has no `name:`",
                                  "set name: to the agent file's basename")

    def check_forbidden(self) -> None:
        """The one production call site of the §7 counting function.

        The swept list it passes is exactly §2's union builder's output (via
        `skill_files()`), and the rendering it passes is the per-root `rel()` —
        so the row filter and the `allow_files` allowlist match against the
        root-correct local path (C3.11, added post-plan from the Chunk 2
        verification).
        """
        for f, local, no, rule in forbidden_findings(self.skill_files(), self.rel):
            self.flag(f, no, "forbidden",
                      f"`{rule['pattern']}` — {rule['reason']}",
                      rule['fix'], rule.get("severity", "fail"), rel=local)

    def check_required(self) -> None:
        """The suite-gated rows (§3): `REQUIRED`, `VERSION_GATED_SKILLS` and
        `V4_CONTRACT_SKILLS` resolve their path keys against the **suite root**.

        The rows name this suite's own files and were never portable style
        rules; in a consumer environment the suite root is the installed plugin
        cache, where those files exist, so the rows pass there. Findings render
        relative to the suite root — `self.rel()` covers the walk only and
        would raise on a disjoint suite root's file.
        """
        if not self.suite_rules:
            return
        for rule in REQUIRED:
            rel, pattern, minimum = rule["file"], rule["pattern"], rule["min"]
            severity = rule.get("severity", "fail")
            f = self.suite_root / rel
            if not f.is_file():
                self.flag(Path(rel), None, "required", "file missing entirely",
                          f"restore the file — {rule['reason']}", severity)
                continue
            n = len(re.findall(pattern, f.read_text(encoding="utf-8")))
            if n < minimum:
                self.flag(f, None, "required",
                          f"`{pattern}` found {n}x, need >= {minimum} — {rule['reason']}",
                          rule['fix'], severity, rel=Path(rel))
        for name in VERSION_GATED_SKILLS:
            rel = f"skills/{name}/SKILL.md"
            f = self.suite_root / rel
            if f.is_file() and "docs/.sdd-version" not in f.read_text(encoding="utf-8"):
                self.flag(f, None, "required", "never reads `docs/.sdd-version` "
                          "(every phase skill gates on the version marker)",
                          "add the version-gate paragraph that reads `docs/.sdd-version` on entry",
                          rel=Path(rel))
        for name in V4_CONTRACT_SKILLS:
            rel = f"skills/{name}/SKILL.md"
            f = self.suite_root / rel
            if f.is_file() and "common v4 contract" not in f.read_text(encoding="utf-8"):
                self.flag(f, None, "required",
                          "lost the collapsed v4 ownership summary (audit P1)",
                          "restore the `common v4 contract` ownership summary paragraph",
                          rel=Path(rel))

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
        F11 principle, scoped to the **ungated** set, with exactly two
        exceptions: (i) check_retired_prefix() — ungated but suite-bound;
        (ii) TEMPLATE_PAIRS's spec side — gated but corpus-bound); a present
        file that lost its anchored fence fails alone with the counterpart
        named (Q-IMPL-HARNESSP4-008).
        """
        if not self.suite_rules:
            return
        # Per-side binding (§5): the TEMPLATE_SOURCE side moves with the suite
        # and binds to the suite root; every row's `spec` key is a `docs/spec/…`
        # path that stays and binds to the corpus root.
        source = self.suite_root / TEMPLATE_SOURCE
        if not source.is_file():
            return  # the REQUIRED rows already report a missing source of record
        # newline="" keeps CR/LF bytes as written — the comparison is byte-for-byte.
        src_fences = self.fences(source.read_text(encoding="utf-8", newline=""))
        for pair in TEMPLATE_PAIRS:
            anchor = pair["anchor"]
            src = [(n, b) for n, b in src_fences if b.split("\n", 1)[0].startswith(anchor)]
            spec_path = self.corpus_root / pair["spec"]
            if not src:
                # The TEMPLATE_SOURCE side is suite-bound and runs in EVERY
                # geometry: §5 skips the SPEC side under disjoint roots, not
                # the row (C3 task 9, resolving C2.2's wider whole-row skip).
                self.flag(source, None, "template-drift",
                          f"no fence opens with `{anchor}` — the {pair['body']} source of record is gone "
                          f"while {pair['spec']} {pair['section']} still restates it", pair["fix"],
                          rel=Path(TEMPLATE_SOURCE))
                continue
            if not self.suite_contained():
                # Disjoint roots: the spec side is SKIPPED, not warned. Warning
                # (or failing) there names this suite's spec files inside a
                # consumer's tree — the F11 principle, ungated set only, with
                # the two exceptions check_retired_prefix (ungated but
                # suite-bound) and TEMPLATE_PAIRS's corpus-bound spec side.
                # Under containment the spec side is checked and an absent
                # spec keeps warning.
                continue
            if not spec_path.is_file():
                self.flag(spec_path, None, "template-drift",
                          f"restating spec for the {pair['body']} is absent — pair not checked",
                          pair["fix"], severity="warn")
                continue
            spec_fences = [(n, b) for n, b in self.fences(spec_path.read_text(encoding="utf-8", newline=""))
                           if b.split("\n", 1)[0].startswith(anchor)]
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
        `skills` binds to the **swept-root union**, as in `check_structure()`:
        a suite-root-only binding made size a silent exception to
        REQ-PKG-PACKAGING-005 (which puts size on the corpus root) and, under
        the disjoint geometry, measured the *live installed suite* instead of
        the corpus being linted — which is exactly how `gc.py`'s fixture shim
        (`gc.py` `lint_command()`, frozen by REQ-PKG-MARKETPLACE-007, passes a
        corpus root only) stopped seeing its own oversized fixture file and
        turned `gc.py --self-test` red. See Q-IMPL-PACKAGING-004
        (C8.1, added post-plan from the implement-stage review).
        """
        seen_size: set[Path] = set()
        for skills_dir in (r / "skills" for r in self.swept_roots()):
            if not skills_dir.is_dir():
                continue
            for sk in sorted(skills_dir.glob("*/SKILL.md")):
                if sk.resolve() in seen_size:
                    continue
                seen_size.add(sk.resolve())
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
        | `skills/<skill>/references/<file>`       | suite root      | fail     |
        | `agents/<name>.md`                       | suite root      | fail     |
        | `docs/spec/<file>.md`                    | corpus root     | warn     |

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
            # `skills/…` is suite-bound (§4's table), like `skill_dir_of()`.
            return path, self.suite_root, "fail"
        # A dispatch template cites each shipped agent by `subagent_type` name AND
        # by path; the name is checkable by nothing, so the path is what makes the
        # citation mechanically verifiable (REQ-AGENT-MARKETPLACE-005). Repo-rooted
        # and `fail`, like the skills/ form — both live in this repository.
        if re.match(r"agents/[^/]+\.md$", path):
            # `agents` is suite-bound (§4's table): the cited agent files ship
            # inside the plugin, so a corpus binding reports every one of them
            # unresolved once the roots differ (C6.11).
            return path, self.suite_root, "fail"
        if path.startswith("docs/spec/") and path.endswith(".md"):
            # `docs/spec` stays corpus-bound (§4's table).
            return path, self.corpus_root, "warn"
        return None

    def retired_scope_roots(self, entry: str) -> list[Path]:
        """The root(s) one retired-prefix scope entry is bound to (§4).

        `suite` / `corpus` name that root alone; `both` is the deduplicated
        union over resolved absolute paths, corpus first — so with equal roots
        a union-bound entry degenerates to one root and the entry set is
        exactly today's.
        """
        binding = RETIRED_SCOPE_BINDING[entry]
        if binding == "suite":
            return [self.suite_root]
        if binding == "corpus":
            return [self.corpus_root]
        roots = [self.corpus_root]
        if Path(self.suite_root).resolve() != Path(self.corpus_root).resolve():
            roots.append(self.suite_root)
        return roots

    def retired_scope_entries(self) -> list[tuple[Path, Path]]:
        """Every file in the live rename scope, paired with the root its scope
        entry is bound to (two-root-linter.md §4).

        The second element is what the file's finding renders against — a
        union-bound entry against whichever root supplied the file. The list is
        deduplicated on resolved absolute paths, so the union stays a set.
        """
        out: list[tuple[Path, Path]] = []
        seen: set[Path] = set()

        def add(f: Path, base: Path) -> None:
            key = f.resolve()
            if key in seen:
                return
            seen.add(key)
            out.append((f, base))

        for d in RETIRED_SCOPE_DIRS:
            for base in self.retired_scope_roots(d):
                area = base / d
                if not area.is_dir():
                    continue
                for f in sorted(area.rglob("*")):
                    if not f.is_file() or f.suffix not in RETIRED_SUFFIXES:
                        continue
                    rel = f.relative_to(base)
                    if any(part in (".git", ".worktrees") or part in RETIRED_SCOPE_EXCLUDE_DIRS
                           for part in rel.parts):
                        continue
                    if rel.as_posix() in RETIRED_SCOPE_EXCLUDE_FILES:
                        continue
                    add(f, base)
        for name in RETIRED_SCOPE_FILES:
            for base in self.retired_scope_roots(name):
                f = base / name
                if f.is_file():
                    add(f, base)
        return out

    def retired_scope_files(self) -> list[Path]:
        """Every file in the live rename scope the retired-prefix rule walks."""
        return [f for f, _base in self.retired_scope_entries()]

    def check_retired_prefix(self) -> None:
        """Flag retired-prefix skill/tool names in the live rename scope.

        Rendering is per entry (§4): each file is rendered against the root its
        scope entry is bound to, which is also what the self-exemption and the
        finding's location string are keyed on.
        """
        for f, base in self.retired_scope_entries():
            rel = f.relative_to(base).as_posix()
            if rel in RETIRED_SELF_EXEMPT:          # skip (2): the rule's own documents
                continue
            fenced = False
            for no, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if line.lstrip().startswith("```"):
                    fenced = not fenced
                    continue
                if fenced:                          # skip (1a): fenced code blocks
                    continue
                stripped = re.sub(r"`[^`]*`", "", line)   # skip (1b): inline-backtick spans
                m = RETIRED_RE.search(stripped)
                if m:
                    self.flag(f, no, "retired-prefix",
                              f"`{m.group(0)}` — the retired namespace prefix must not "
                              "appear bare in the live corpus (REQ-NAME-MARKETPLACE-009)",
                              RETIRED_FIX, rel=Path(rel))

    # -- driver -------------------------------------------------------------

    def run(self) -> int:
        self.check_structure()
        self.check_forbidden()
        self.check_retired_prefix()
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
    """Run the full driver on a fixture repo (suite-specific rows off) and capture stdout.

    The two roots are set EQUAL to the fixture root: a fixture exercising the
    single-tree semantics must not inherit the live plugin root as its suite
    root, which the per-entry bindings of two-root-linter.md §4 would otherwise
    make it walk. The geometry cases below construct their roots explicitly.
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = Linter(root, root, suite_rules=False).run()
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
        linter = Linter(root, root)
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
        clean = Linter(good_root, good_root)
        clean.check_structure()
        clean.check_forbidden()
        clean.check_ordinals()
        clean.check_links()
        check(not clean.findings,
              "clean fixture produced findings:\n" + "\n".join(t for _, t in clean.findings))

        # -- 3. flag() without fix is a TypeError (remediation is mandatory)
        try:
            Linter(root, root).flag(Path("x"), 1, "rule", "msg")  # type: ignore[call-arg]
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
            "Dispatch `agents/kept-agent.md`, never `agents/gone-agent.md`.\n"
            "Contract: `docs/spec/nowhere.md#section`.\n"
            "Globs like `references/*.md` are skipped.\n"
            "```\n`references/fenced-missing.md`\n```\n",
        )
        (d / "references").mkdir()
        (d / "references" / "present.md").write_text("# ok\n", encoding="utf-8")
        # The `agents/<name>.md` class resolves against the REPO ROOT, so the
        # resolvable half of the pair lives at the fixture root, not under the
        # skill dir (REQ-AGENT-MARKETPLACE-005).
        (ref_root / "agents").mkdir(parents=True, exist_ok=True)
        (ref_root / "agents" / "kept-agent.md").write_text(
            "---\nname: kept-agent\ndescription: Use when testing.\n---\n", encoding="utf-8")
        code, out = _run_capture(ref_root)
        check(code == 1, f"backtick fixture exited {code}:\n{out}")
        # One `fail` per unresolvable path the fixture cites, one per resolution
        # class. The expected count is DERIVED from this list, not hand-written,
        # so adding a class to the fixture forces its finding to appear.
        missing = ["references/missing.md",
                   "skills/ref-skill/references/absent.md",
                   "agents/gone-agent.md"]
        for m in missing:
            hits = [ln for ln in out.splitlines() if f"`{m}`" in ln]
            check(len(hits) == 1, f"backtick miss `{m}` not flagged exactly once:\n{out}")
            # `fail` severity is the absence of the WARN prefix the printer adds.
            check(hits and not hits[0].startswith("WARN "),
                  f"backtick miss `{m}` was not flagged at fail severity:\n{out}")
        check("WARN " in out and "`docs/spec/nowhere.md`" in out,
              f"docs/spec/ mention should warn:\n{out}")
        check("present.md" not in out, f"existing backtick path flagged:\n{out}")
        check("kept-agent" not in out, f"existing agents/ backtick path flagged:\n{out}")
        check("fenced-missing" not in out and "*.md" not in out,
              f"fenced or glob backtick path flagged:\n{out}")
        check(f"FAIL: {len(missing)} finding(s), 1 warning(s)" in out,
              f"backtick summary wrong:\n{out}")
        for sev, t in Linter(ref_root, ref_root, suite_rules=False).findings:
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
                    code = Linter(mut_root, mut_root).run()
                out = buf.getvalue()
                check(code == 1, f"stripping `{rule['pattern']}` from {rule['file']} did not fail:\n{out}")
                check(rule['fix'] in out,
                      f"fix string not printed for `{rule['pattern']}` in {rule['file']}:\n{out}")
            # every rule-table row carries a fix (the mutation loop above proves REQUIRED;
            # FORBIDDEN rows are asserted by shape)
            check(all(r.get('fix') for r in FORBIDDEN), "FORBIDDEN row without fix")
            # harness-p2 added four REQUIRED rows (RED_VERDICT producer/consumer,
            # REVIEW: CONTRADICTION, Material `affects`) — REQ-LINT-HARNESSP2-001.
            # harness-p6 replaces that `>=` bound with the exact total: this
            # cycle's three pairs (`PLAN:` ×2, `GIT_STATE` ×2, `CONVERGENCE:` ×2)
            # are all present, and the table counts rows, not files, so the rows
            # that share a target file are distinct rows
            # (skill-lint-v5.md §Self-Test Extension, REQ-LINT-HARNESSP6-003).
            check(len(REQUIRED) == 40, f"expected exactly 40 REQUIRED rows, found {len(REQUIRED)}")
            # d2 negative: a SKILL.md carrying only `RED_VERDICT: HELD` must NOT
            # satisfy the review-verdict consumer row (the `(?<!RED_)` lookbehind).
            d2 = next((r for r in REQUIRED
                       if r["file"] == "skills/orchestrate/SKILL.md" and "VERDICT" in r["pattern"]
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
            # harness-p6 adds the `PLAN:` and `GIT_STATE` pairs
            # (REQ-LINT-HARNESSP6-001). The mutation loop above already strips
            # each of the four rows from its own file and asserts the row's fix
            # is printed; these checks pin the pair shape so a later edit cannot
            # silently drop half a pair or re-point a fix string.
            plan_rows = [r for r in REQUIRED if r["pattern"] == r"PLAN: INCOMPLETE"]
            check(len(plan_rows) == 2, f"expected two `PLAN: INCOMPLETE` REQUIRED rows, found {len(plan_rows)}")
            check({r["file"] for r in plan_rows} == {
                      "skills/orchestrate/references/loop-control.md",
                      "skills/orchestrate/SKILL.md"},
                  "`PLAN: INCOMPLETE` pair must target loop-control.md (producer) and SKILL.md (consumer)")
            for r in plan_rows:
                check("harness-loop-control.md §Plan Completion Ownership" in r["fix"],
                      "`PLAN: INCOMPLETE` row fix must point at harness-loop-control.md §Plan Completion Ownership")
                check(re.search(r["pattern"], "pauses with `PLAN: INCOMPLETE (3 of 7 ticked)`") is not None,
                      f"`PLAN: INCOMPLETE` row pattern no longer matches the token: {r['pattern']}")
            # `GIT_STATE` is a finding NAME rendered inside the `SCOPE:` block,
            # not an own-line gate token — so its pattern carries no trailing
            # colon and no option-set alternation (Q-REQ-P6-A).
            git_rows = [r for r in REQUIRED if r["pattern"] == r"GIT_STATE"]
            check(len(git_rows) == 2, f"expected two `GIT_STATE` REQUIRED rows, found {len(git_rows)}")
            check({r["file"] for r in git_rows} == {
                      "skills/orchestrate/references/write-scope.md",
                      "skills/orchestrate/SKILL.md"},
                  "`GIT_STATE` pair must target write-scope.md (producer) and SKILL.md (consumer)")
            for r in git_rows:
                check("harness-write-scope.md §Git-State Observation" in r["fix"],
                      "`GIT_STATE` row fix must point at harness-write-scope.md §Git-State Observation")
                check(":" not in r["pattern"] and "|" not in r["pattern"],
                      f"`GIT_STATE` row pattern must carry no trailing colon and no alternation: {r['pattern']}")
            # `CONVERGENCE:` is an own-line gate token (item 6c), so unlike
            # `GIT_STATE` its pattern keeps the trailing colon
            # (REQ-LINT-HARNESSP6-003).
            conv_rows = [r for r in REQUIRED if r["pattern"] == r"CONVERGENCE:"]
            check(len(conv_rows) == 2, f"expected two `CONVERGENCE:` REQUIRED rows, found {len(conv_rows)}")
            check({r["file"] for r in conv_rows} == {
                      "skills/orchestrate/references/loop-control.md",
                      "skills/orchestrate/SKILL.md"},
                  "`CONVERGENCE:` pair must target loop-control.md (producer) and SKILL.md (consumer)")
            for r in conv_rows:
                check("harness-loop-control.md §Convergence Signal" in r["fix"],
                      "`CONVERGENCE:` row fix must point at harness-loop-control.md §Convergence Signal")
                check(re.search(r["pattern"], "CONVERGENCE: REQ-LINT-HARNESSP6-003 (review, red) — 2 layers")
                      is not None,
                      f"`CONVERGENCE:` row pattern no longer matches the token: {r['pattern']}")
            # -- 7c. [template-drift] (REQ-LINT-HARNESSP4-001): the four pair rows
            #       compare byte-identical on the shipped set (skills + docs/spec
            #       copied to a temp root); one character changed inside the RED
            #       TEAM `RETURN:` block of the temp dispatch-templates.md exits 1
            #       with a finding naming adversarial-verify.md and the fix, and
            #       fires no chunk-verifier row.
            check(len(TEMPLATE_PAIRS) == 4, f"expected the four TEMPLATE_PAIRS rows, found {len(TEMPLATE_PAIRS)}")
            check(all(r.get("fix") for r in TEMPLATE_PAIRS), "TEMPLATE_PAIRS row without fix")
            # `docs/spec/` is CORPUS-bound (§4's binding table) and deliberately
            # stayed at the corpus root when the suite moved to `plugins/sdd/`, so
            # it is not a sibling of the suite. Walk up from the suite root to the
            # nearest ancestor that holds it — that ancestor IS the corpus root,
            # and under the equal-roots geometry it is the suite's own parent, so
            # the pre-move behaviour is unchanged (C6.10).
            real_spec = next((anc / "docs" / "spec"
                              for anc in [real_skills.parent, *real_skills.parent.parents]
                              if (anc / "docs" / "spec").is_dir()), None)
            check(real_spec is not None,
                  "docs/spec/ not found at the corpus root above the real skill suite")
            if real_spec is not None:
                drift_root = root / "drift"
                shutil.copytree(real_skills, drift_root / "skills")
                shutil.copytree(real_spec, drift_root / "docs" / "spec")
                clean = Linter(drift_root, drift_root)
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
                        code = Linter(drift_root, drift_root).run()
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
            for required_allow in ("skills/orchestrate/SKILL.md",
                                   "skills/orchestrate/references/telemetry.md",
                                   "skills/orchestrate/references/write-scope.md"):
                check(required_allow in sdd_row["allow_files"], f"`\\.sdd/` allow_files lacks {required_allow}")
            sdd_root = root / "sddrow"
            fenced = "```\n.sdd/telemetry.jsonl\n```\n"
            _fixture_skill(sdd_root, "plan", fenced)            # non-allowlisted → must fail
            code, out = _run_capture(sdd_root)
            check(code == 1 and sdd_row["fix"] in out,
                  f"fenced .sdd/ mention in plan/SKILL.md did not fail with the row's fix:\n{out}")
            sdd_ok = root / "sddallow"
            for rel in sdd_row["allow_files"]:
                target = sdd_ok / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.name == "SKILL.md":
                    _fixture_skill(sdd_ok, target.parent.name, fenced)
                else:
                    target.write_text(fenced, encoding="utf-8")
            # every allowlisted path needs a well-formed SKILL.md beside it
            if not (sdd_ok / "skills" / "orchestrate" / "SKILL.md").is_file():
                _fixture_skill(sdd_ok, "orchestrate", "prose\n")
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
            af = Linter(af_root, af_root, suite_rules=False)
            af.check_forbidden()
        finally:
            FORBIDDEN = shipped                  # shipped list untouched
        af_text = "\n".join(t for _, t in af.findings)
        check("plain-skill/SKILL.md" in af_text and "SYNTHETIC-ALLOW-FILES-FIX" in af_text,
              f"allow_files row did not fire on the non-allowlisted fenced fixture:\n{af_text}")
        check("allowed.md" not in af_text,
              f"allow_files did not skip the allowlisted file:\n{af_text}")
        check(len(af.findings) == 1, f"expected exactly one allow_files finding:\n{af_text}")

        # -- 9. the retired-prefix rule (REQ-NAME-MARKETPLACE-009). The fixture is
        #       SYNTHESIZED into the temp root and discarded with it — never stored
        #       under tools/, whose live sweep would flag its deliberate bare
        #       occurrence (Q-IMPL-MARKETPLACE-002). Four occurrences of the
        #       retired form — bare, backticked, fenced, and inside a self-exempt
        #       file — and exactly one flag: the bare one.
        rp_root = root / "retired"
        (rp_root / "docs" / "spec").mkdir(parents=True)
        retired = RETIRED_SKILLS[0]                      # a retired-prefix skill name
        token = "sdd-" + retired
        (rp_root / "docs" / "spec" / "bare.md").write_text(
            f"The {token} skill is named in prose.\n", encoding="utf-8")
        (rp_root / "docs" / "spec" / "quoted.md").write_text(
            f"The historical corpus says `{token}` here.\n", encoding="utf-8")
        (rp_root / "docs" / "spec" / "fenced.md").write_text(
            f"Example:\n\n```\n{token}\n```\n", encoding="utf-8")
        # the self-exempt occurrence must sit in a walked scope area, or the skip
        # it exercises would be vacuous: the naming requirements file is both.
        (rp_root / "docs" / "requirements" / "integration").mkdir(parents=True)
        (rp_root / "docs" / "requirements" / "integration" / "naming.md").write_text(
            f"Pre-marketplace skills were named {token}.\n", encoding="utf-8")
        rp = Linter(rp_root, rp_root, suite_rules=False)
        rp.check_retired_prefix()
        rp_text = "\n".join(t for _, t in rp.findings)
        check(len(rp.findings) == 1,
              f"expected exactly one retired-prefix finding, got {len(rp.findings)}:\n{rp_text}")
        check("docs/spec/bare.md" in rp_text and "[retired-prefix]" in rp_text,
              f"the bare occurrence was not the flagged one:\n{rp_text}")
        for skipped in ("quoted.md", "fenced.md", "naming.md"):
            check(skipped not in rp_text, f"{skipped} must be skipped by the rule:\n{rp_text}")
        check(all(sev == "fail" for sev, _ in rp.findings), "retired-prefix must be fail severity")
        check(RETIRED_FIX in rp_text, f"retired-prefix finding without its fix:\n{rp_text}")
        # the self-exemption list stays at the four documents whose subject is the rule
        check(len(RETIRED_SELF_EXEMPT) == 4,
              f"expected four self-exempt paths, found {len(RETIRED_SELF_EXEMPT)}")
        # tools/fixtures/ is outside the walked scope (Q-IMPL-MARKETPLACE-007)
        (rp_root / "tools" / "fixtures").mkdir(parents=True)
        (rp_root / "tools" / "fixtures" / "frozen.md").write_text(
            f"{token}\n", encoding="utf-8")
        walked = {f.relative_to(rp_root).as_posix() for f in rp.retired_scope_files()}
        check("tools/fixtures/frozen.md" not in walked,
              "tools/fixtures/ must stay outside the retired-prefix walk (frozen fixture bytes)")
        (rp_root / "docs" / "requirements" / "traceability.md").write_text(
            f"{token}\n", encoding="utf-8")
        walked = {f.relative_to(rp_root).as_posix() for f in rp.retired_scope_files()}
        check("docs/requirements/traceability.md" not in walked,
              "the derived aggregate traceability must stay outside the retired-prefix walk")

        # -- 9b. the POLICED POPULATION, not merely the firing (R2 of the verify
        #        stage's red round, Q-IMPL-MARKETPLACE-023). Block 9 above proves
        #        the rule fires and skips correctly; it says nothing about WHICH
        #        areas it walks, so gutting RETIRED_SCOPE_DIRS to one directory
        #        still passed it. The expected population is pinned HERE, in the
        #        fixture, independently of the constants the rule reads — a list
        #        derived from those constants would shrink with them and the
        #        assertion would be vacuous again.
        policed_dirs = ("skills", "tools", "agents", ".claude-plugin",
                        "docs/spec", "docs/requirements")
        policed_files = ("CLAUDE.md", "README.md", "CONTRIBUTING.md",
                         "LICENSE", ".pre-commit-config.yaml")
        check(tuple(RETIRED_SCOPE_DIRS) == policed_dirs,
              f"retired-prefix scope dirs drifted from the policed population: "
              f"{tuple(RETIRED_SCOPE_DIRS)} != {policed_dirs}")
        check(tuple(RETIRED_SCOPE_FILES) == policed_files,
              f"retired-prefix scope files drifted from the policed population: "
              f"{tuple(RETIRED_SCOPE_FILES)} != {policed_files}")
        # Behavioural half: seed ONE bare occurrence in EVERY policed area and
        # require one finding per area. Deleting an area from the rule's scope
        # loses its finding and fails the suite.
        pop_root = root / "population"
        seeded = [f"{d}/seeded.md" for d in policed_dirs] + list(policed_files)
        for rel in seeded:
            f = pop_root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(f"The {token} name appears bare here.\n", encoding="utf-8")
        expected = {rel for rel in seeded if rel not in RETIRED_SELF_EXEMPT}
        pop = Linter(pop_root, pop_root, suite_rules=False)
        pop.check_retired_prefix()
        pop_text = "\n".join(t for _, t in pop.findings)
        for rel in sorted(expected):
            check(rel in pop_text,
                  f"policed area {rel} produced no retired-prefix finding — the area "
                  f"is seeded but unwalked:\n{pop_text}")
        check(len(pop.findings) == len(expected),
              f"expected one retired-prefix finding per policed area "
              f"({len(expected)}), got {len(pop.findings)}:\n{pop_text}")
        # and the self-exempt scope file is seeded yet silent, so the exemption
        # is exercised against a walked area rather than a vacuous one.
        for rel in sorted(set(seeded) - expected):
            check(rel not in pop_text,
                  f"self-exempt {rel} must stay silent although it is walked:\n{pop_text}")

        # -- 10. the two-root constructor interface (two-root-linter.md §2, §6,
        #        §Verification). Three named, checked-in cases.
        tr = root / "tworoot"
        tr_corpus = tr / "corpus"
        tr_suite = tr_corpus / "plugins" / "sdd"
        tr_far = tr / "elsewhere"
        tr_far.mkdir(parents=True, exist_ok=True)
        _fixture_skill(tr_corpus, "alpha", "Body. Skip for Y.\n")
        _fixture_skill(tr_suite, "beta", "Body. Skip for Y.\n")
        # A non-SKILL.md lintable file, so the swept-set comparison below is
        # sensitive to the walk's glob and not only to its roots.
        (tr_corpus / "skills" / "alpha" / "references").mkdir(parents=True, exist_ok=True)
        (tr_corpus / "skills" / "alpha" / "references" / "detail.md").write_text(
            "# Detail\n", encoding="utf-8")
        tr_alpha = tr_corpus / "skills" / "alpha" / "SKILL.md"
        tr_beta = tr_suite / "skills" / "beta" / "SKILL.md"

        def two_roots_construct_distinct_and_equal() -> None:
            """Construct with distinct and with equal roots, never via argparse."""
            nested = Linter(tr_corpus, tr_suite, suite_rules=False)
            check({p.resolve() for p in nested.swept_roots()}
                  == {tr_corpus.resolve(), tr_suite.resolve()},
                  "a contained suite root must join swept_roots()")
            equal = Linter(tr_corpus, tr_corpus, suite_rules=False)
            check([p.resolve() for p in equal.swept_roots()] == [tr_corpus.resolve()],
                  "equal roots must degenerate to today's single walk")
            disjoint = Linter(tr_corpus, tr_far, suite_rules=False)
            check([p.resolve() for p in disjoint.swept_roots()] == [tr_corpus.resolve()],
                  "a suite root outside the corpus root must not join the walk")
            check(Linter(tr_corpus).suite_root == default_suite_root(),
                  "the suite root must default to the script's own plugin root")
            # Per-root rendering: neither root's file raises, and the nested
            # suite file renders with no nesting segment.
            check(nested.rel(tr_alpha).as_posix() == "skills/alpha/SKILL.md",
                  f"corpus file mis-rendered: {nested.rel(tr_alpha)}")
            check(nested.rel(tr_beta).as_posix() == "skills/beta/SKILL.md",
                  f"suite file mis-rendered: {nested.rel(tr_beta)}")

        def equal_roots_sweep_set_unchanged() -> None:
            """With equal roots the swept set is the pre-change single-root set.

            The comparand is derived at run time — the walk this linter did
            before the two-root interface landed — and compared as a set, never
            against a pinned count.
            """
            def pre_change_sweep(r: Path) -> set[Path]:
                d = r / "skills"
                return {f.resolve() for f in sorted(d.rglob("*.md"))} if d.is_dir() else set()

            for r in (tr_corpus, default_suite_root()):
                lin = Linter(r, r, suite_rules=False)
                got = {f.resolve() for f in lin.walk()}
                check(got == pre_change_sweep(r),
                      f"equal-roots sweep of {r} differs from the pre-change set: "
                      f"{sorted(str(p) for p in got ^ pre_change_sweep(r))}")
                check(lin.findings == [],
                      f"equal-roots sweep of {r} must emit no finding: {lin.findings}")

        def sweep_is_duplicate_free() -> None:
            """The positive half of the §6 guard, plus its negative case."""
            # Equal roots are the geometry whose union would otherwise repeat
            # every path; the swept list holds each once and the guard is silent.
            dup = Linter(tr_corpus, tr_corpus, suite_rules=False)
            swept = dup.walk()
            check(len(swept) == len({p.resolve() for p in swept}),
                  f"swept list holds a path twice: {[str(p) for p in swept]}")
            check(dup.findings == [],
                  f"the guard must stay silent on a duplicate-free sweep: {dup.findings}")
            # Negative case: the pure guard called with a hand-built list
            # holding one path twice — the shape concatenation produces.
            fired = duplicate_free_findings([tr_alpha, tr_beta, tr_alpha])
            check(len(fired) == 1 and fired[0][0] == tr_alpha.resolve(),
                  f"the guard must name exactly the duplicated path: {fired}")
            obs = Linter(tr_corpus, tr_corpus, suite_rules=False)
            obs._guard_duplicate_free([tr_alpha, tr_alpha])
            check(len(obs.findings) == 1 and obs.findings[0][0] == "fail"
                  and str(tr_alpha.resolve()) in obs.findings[0][1],
                  f"the guard's observable must be one fail finding naming the "
                  f"duplicated path: {obs.findings}")
            # No mode skips it: the guard is called by the union builder, whose
            # only caller in the driver is skill_files().
            modes = Linter(tr_corpus, tr_corpus, suite_rules=False)
            modes.skill_files()
            check(modes._guard_done, "skill_files() must run the construction guard")
            # ...and the observable is REACHABLE in every mode, not merely run.
            # `--print-population` calls the union builder and then discarded
            # its findings, so the guard could fire there and be seen by
            # nobody. Drive a duplicate-yielding walk through that mode and
            # require the finding on stdout and a non-zero exit
            # (C8.3, added post-plan from the implement-stage review).
            orig_walk = Linter.walk

            def _dup_walk(self: Linter) -> list[Path]:
                self._guard_duplicate_free([tr_alpha, tr_alpha])
                return [tr_alpha, tr_alpha]

            Linter.walk = _dup_walk  # type: ignore[method-assign]
            try:
                pbuf = io.StringIO()
                with contextlib.redirect_stdout(pbuf):
                    prc = print_population(tr_corpus, tr_corpus)
                pout = pbuf.getvalue()
            finally:
                Linter.walk = orig_walk  # type: ignore[method-assign]
            check(prc != 0 and "[sweep-duplicate]" in pout
                  and str(tr_alpha.resolve()) in pout,
                  f"--print-population must surface the guard's finding and exit "
                  f"non-zero, got rc={prc}:\n{pout}")

        def retired_scope_binds_per_entry() -> None:
            """Per-entry binding and rendering (two-root-linter.md §4).

            Geometry: DISJOINT roots — the only one in which a mis-binding is
            observable at all, since under equality every entry resolves to the
            same tree. Each policed entry is seeded under the root it is bound
            to AND under the root it is not, so the case distinguishes "bound
            correctly" from "bound to both" and from "bound to the other one".
            """
            # Every scope entry carries a binding; an unbound entry is unwalked.
            check(set(RETIRED_SCOPE_BINDING) == set(RETIRED_SCOPE_DIRS) | set(RETIRED_SCOPE_FILES),
                  f"RETIRED_SCOPE_BINDING does not cover the policed population: "
                  f"{sorted(set(RETIRED_SCOPE_BINDING) ^ (set(RETIRED_SCOPE_DIRS) | set(RETIRED_SCOPE_FILES)))}")

            rs = root / "retiredscope"
            rs_corpus = rs / "corpus"
            rs_suite = rs / "suite"             # disjoint: NOT under rs_corpus

            def seed(base: Path, rel: str) -> None:
                f = base / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("body\n", encoding="utf-8")

            suite_bound = ("skills/s.md", "tools/t.md", "agents/a.md")
            corpus_bound = ("docs/spec/s.md", "docs/requirements/r.md")
            union_bound_suite = (".claude-plugin/plugin.json", "CLAUDE.md", "LICENSE")
            union_bound_corpus = (".claude-plugin/marketplace.json", "README.md",
                                  ".pre-commit-config.yaml")
            for rel in suite_bound + union_bound_suite:
                seed(rs_suite, rel)
            for rel in corpus_bound + union_bound_corpus:
                seed(rs_corpus, rel)
            # The discriminators: the same relative paths seeded under the WRONG
            # root. A binding that walked both roots for a one-root entry, or the
            # other root, picks these up.
            for rel in suite_bound:
                seed(rs_corpus, rel.replace(".md", "-wrong.md"))
            for rel in corpus_bound:
                seed(rs_suite, rel.replace(".md", "-wrong.md"))

            # No construction with two distinct roots raises ValueError, and
            # neither does the per-entry walk or the rendering it drives.
            lin = Linter(rs_corpus, rs_suite, suite_rules=False)
            try:
                entries = lin.retired_scope_entries()
                rendered = {f.relative_to(base).as_posix() for f, base in entries}
                lin.check_retired_prefix()
            except ValueError as exc:          # pragma: no cover - the regression
                check(False, f"two distinct roots raised ValueError: {exc}")
                return
            check(lin.findings == [],
                  f"the clean per-entry fixture must emit no finding: {lin.findings}")

            expected = set(suite_bound + corpus_bound + union_bound_suite + union_bound_corpus)
            check(rendered == expected,
                  f"per-entry binding/rendering drifted: missing "
                  f"{sorted(expected - rendered)}, unexpected {sorted(rendered - expected)}")
            # Each entry renders against the root it is BOUND to, not merely
            # against some root that happens to contain the file.
            by_rel = {f.relative_to(base).as_posix(): base for f, base in entries}
            for rel in suite_bound + union_bound_suite:
                check(by_rel.get(rel) == rs_suite,
                      f"{rel} must render against the suite root, got {by_rel.get(rel)}")
            for rel in corpus_bound + union_bound_corpus:
                check(by_rel.get(rel) == rs_corpus,
                      f"{rel} must render against the corpus root, got {by_rel.get(rel)}")
            # `.claude-plugin` is union-bound: BOTH manifests are members, and a
            # one-root binding drops exactly one of them.
            check({".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"} <= rendered,
                  f"the union-bound .claude-plugin entry dropped a manifest: {sorted(rendered)}")

            # Equal roots: the returned set is identical to the pre-change
            # single-root result, derived at run time rather than pinned.
            def pre_change_scope(r: Path) -> set[Path]:
                out: set[Path] = set()
                for d in RETIRED_SCOPE_DIRS:
                    base = r / d
                    if not base.is_dir():
                        continue
                    for f in sorted(base.rglob("*")):
                        if not f.is_file() or f.suffix not in RETIRED_SUFFIXES:
                            continue
                        rel = f.relative_to(r)
                        if any(part in (".git", ".worktrees") or part in RETIRED_SCOPE_EXCLUDE_DIRS
                               for part in rel.parts):
                            continue
                        if rel.as_posix() in RETIRED_SCOPE_EXCLUDE_FILES:
                            continue
                        out.add(f.resolve())
                for name in RETIRED_SCOPE_FILES:
                    f = r / name
                    if f.is_file():
                        out.add(f.resolve())
                return out

            # A fixture tree carrying BOTH skills/ and docs/ — the two halves the
            # per-entry table splits across roots — plus the live suite itself.
            eq = root / "retiredscope-equal"
            for rel in ("skills/s.md", "tools/t.md", "agents/a.md",
                        "docs/spec/s.md", "docs/requirements/r.md",
                        ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                        "CLAUDE.md", "README.md", "CONTRIBUTING.md", "LICENSE",
                        ".pre-commit-config.yaml", "tools/fixtures/frozen.md"):
                seed(eq, rel)
            for r in (eq, default_suite_root()):
                same = Linter(r, r, suite_rules=False)
                got = {f.resolve() for f in same.retired_scope_files()}
                check(got == pre_change_scope(r),
                      f"equal-roots retired scope of {r} differs from the pre-change set: "
                      f"{sorted(str(x) for x in got ^ pre_change_scope(r))}")
                check(len(same.retired_scope_files()) == len(got),
                      f"equal-roots retired scope of {r} holds a path twice")

        def retarget_seeds_an_ungated_finding() -> None:
            """The retarget check, with a seeded ungated violation (§3).

            A criterion asserting only "no gated findings" passes equally for a
            correct retarget and for a linter whose checks are all switched off.
            The seeded `[retired-prefix]` finding — ungated and corpus-bound —
            is what distinguishes the two, and it is asserted by path and tag.
            """
            rt = root / "retarget"
            (rt / "docs" / "spec").mkdir(parents=True, exist_ok=True)
            token = "sdd-" + RETIRED_SKILLS[0]
            (rt / "docs" / "spec" / "seeded-retired.md").write_text(
                f"The {token} skill is named bare in prose.\n", encoding="utf-8")
            # Corpus root: a scratch tree with NO skills/. Suite root: the live
            # plugin root, which has one — the disjoint consumer geometry.
            suite = default_suite_root()
            check(not (rt / "skills").exists(), "the retarget corpus root must have no skills/")
            check((suite / "skills").is_dir(), "the retarget suite root must have skills/")
            lin = Linter(rt, suite, suite_rules=True)
            check(not lin.suite_contained(), "the retarget geometry must be disjoint")
            with contextlib.redirect_stdout(io.StringIO()):
                lin.run()
            texts = [t for _, t in lin.findings]
            gated = [t for t in texts if "[required]" in t]
            check(not gated,
                  f"a suite-gated row fired against the corpus root — the retarget "
                  f"did not take:\n" + "\n".join(gated))
            seeded = [t for t in texts
                      if t.startswith("docs/spec/seeded-retired.md:") and "[retired-prefix]" in t]
            check(len(seeded) == 1,
                  f"expected exactly one [retired-prefix] finding at "
                  f"docs/spec/seeded-retired.md, got {len(seeded)}:\n" + "\n".join(texts))
            check(all(sev == "fail" for sev, t in lin.findings if t in seeded),
                  "the seeded ungated finding must keep fail severity")
            # The disjoint spec side of TEMPLATE_PAIRS is skipped, not warned.
            check(not any("[template-drift]" in t for t in texts),
                  f"the spec side must be skipped under disjoint roots:\n" + "\n".join(texts))

        # -- 11. the three fixture geometries and their negative cases
        #        (two-root-linter.md §6, §7, §Verification). Each fixture seeds a
        #        known number of `.md` files; a literal count is sound here and
        #        only here, a fixture not growing by contribution.
        def _loc(text: str) -> str:
            """The path part of a rendered finding — `<path>[:<line>]: [rule] …`."""
            return re.sub(r":\d+$", "", text.split(": [", 1)[0])

        # The seeded walk-class violation is the shipped row's own pattern, so
        # the seed cannot drift away from what the rule matches.
        SEED = next(r["pattern"] for r in FORBIDDEN if r["pattern"] == "Co-Authored-By")

        # Fixture A — nested (`suite_root = corpus_root/plugins/sdd`). TWO seeds,
        # one per root: one seed cannot discriminate per-root rendering from
        # suite-rooted rendering. Fixture A does NOT pin single-sweep — under
        # nesting the two walk terms are disjoint subtrees.
        fa = root / "fixtureA"
        fa_corpus = fa / "corpus"
        fa_suite = fa_corpus / "plugins" / "sdd"
        fa_corpus_skill = _fixture_skill(fa_corpus, "corpus-skill",
                                         f"Body. Skip for Y.\n{SEED}\n") / "SKILL.md"
        fa_suite_skill = _fixture_skill(fa_suite, "suite-skill",
                                        f"Body. Skip for Y.\n{SEED}\n") / "SKILL.md"

        # Fixture B — disjoint (the consumer shape): the suite root is a SIBLING
        # of the corpus root. The suite-root file carries BOTH a table-row
        # violation (a REQUIRED row's pattern short of its minimum) and a
        # walk-class violation, so "reported" and "correctly excluded" are
        # observed on one seeded path.
        fb = root / "fixtureB"
        fb_corpus = fb / "corpus"
        fb_suite = fb / "suite"
        fb_row = REQUIRED[0]
        fb_row_rel = fb_row["file"]
        fb_table_file = fb_suite / fb_row_rel
        fb_table_file.parent.mkdir(parents=True, exist_ok=True)
        fb_table_file.write_text(
            f"---\nname: {Path(fb_row_rel).parent.name}\ndescription: >\n"
            f"  Use for X. Skip for Y.\n---\n\nBody.\n{SEED}\n", encoding="utf-8")
        fb_corpus_skill = _fixture_skill(fb_corpus, "corpus-skill",
                                         f"Body. Skip for Y.\n{SEED}\n") / "SKILL.md"
        (fb_suite / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        (fb_suite / ".claude-plugin" / "plugin.json").write_text("{}\n", encoding="utf-8")
        (fb_corpus / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        (fb_corpus / ".claude-plugin" / "marketplace.json").write_text("{}\n", encoding="utf-8")

        def nested_roots_render_per_root() -> None:
            """Fixture A: both seeds reported, each rendered against its own root."""
            lin = Linter(fa_corpus, fa_suite, suite_rules=False)
            lin.check_forbidden()
            texts = [t for _, t in lin.findings]
            locs = sorted(_loc(t) for t in texts)
            check(locs == ["skills/corpus-skill/SKILL.md", "skills/suite-skill/SKILL.md"],
                  f"fixture A must report one seed per root, rendered per root: {locs}")
            check(not any("plugins/sdd" in t for t in texts),
                  f"a per-root rendering carries no nesting segment:\n" + "\n".join(texts))

        def disjoint_suite_walk_excluded() -> None:
            """Fixture B: the table row fires; the suite-root walk seed does not."""
            lin = Linter(fb_corpus, fb_suite, suite_rules=True)
            check(not lin.suite_contained(), "fixture B must be the disjoint geometry")
            with contextlib.redirect_stdout(io.StringIO()):
                lin.run()
            texts = [t for _, t in lin.findings]
            # (i) the table-row violation seeded under the suite root IS reported —
            #     the gated tables resolve `root / rel` and bypass the walk.
            table = [t for t in texts
                     if _loc(t) == fb_row_rel and "[required]" in t and fb_row["pattern"] in t]
            check(len(table) == 1,
                  f"the suite-root table-row violation must be reported once:\n" + "\n".join(texts))
            # (ii) the walk-class violation at that same seeded path is NOT reported,
            #      asserted as a named absent finding — never as exit-code silence —
            #      WHILE other findings are present.
            check(not any(_loc(t) == fb_row_rel and "[forbidden]" in t for t in texts),
                  f"the disjoint suite root must not join the walk:\n" + "\n".join(texts))
            check(any(_loc(t) == "skills/corpus-skill/SKILL.md" and "[forbidden]" in t
                      for t in texts),
                  f"the corpus-side seed must still fire (other findings present):\n"
                  + "\n".join(texts))
            check([f.resolve() for f in lin.walk()] == [fb_corpus_skill.resolve()],
                  f"the disjoint walk must hold the corpus seed alone: "
                  f"{[str(f) for f in lin.walk()]}")

        def manifest_pair_membership() -> None:
            """Both manifests are members; each one-root binding drops exactly one."""
            plugin = (fb_suite / ".claude-plugin" / "plugin.json").resolve()
            market = (fb_corpus / ".claude-plugin" / "marketplace.json").resolve()
            two = {f.resolve() for f in
                   Linter(fb_corpus, fb_suite, suite_rules=False).retired_scope_files()}
            check(plugin in two,
                  f"retired_scope_files() is missing <suite_root>/.claude-plugin/plugin.json "
                  f"({plugin})")
            check(market in two,
                  f"retired_scope_files() is missing <corpus_root>/.claude-plugin/"
                  f"marketplace.json ({market})")
            for label, r, dropped, kept in (("corpus-only", fb_corpus, plugin, market),
                                            ("suite-only", fb_suite, market, plugin)):
                one = {f.resolve() for f in
                       Linter(r, r, suite_rules=False).retired_scope_files()}
                check(dropped not in one and kept in one,
                      f"the {label} binding must drop exactly {dropped} and keep {kept}")

        def case_c_counts_once() -> None:
            """Case C — equal roots over fixture A's corpus tree: counted once.

            The only geometry in which both walk terms name the same subtree,
            hence the only one distinguishing a set union from a concatenation.
            """
            lin = Linter(fa_corpus, fa_corpus, suite_rules=False)
            found = forbidden_findings(lin.walk(), lin.rel)
            named = [x for x in found if x[1].as_posix() == "skills/corpus-skill/SKILL.md"]
            check(len(named) == 1,
                  f"case C must count its seeded violation exactly once, got {len(named)}")

        def case_c_negative_double_count() -> None:
            """Case C's OWN negative case (§7) — the §6 guard's discharges nothing here.

            The counting function is called DIRECTLY with a hand-built swept list
            holding the seeded path twice (the shape a concatenation over two equal
            roots produces); the count-once assertion must then fail, naming the path.
            """
            lin = Linter(fa_corpus, fa_corpus, suite_rules=False)
            doubled = forbidden_findings([fa_corpus_skill, fa_corpus_skill], lin.rel)
            named = [x for x in doubled if x[1].as_posix() == "skills/corpus-skill/SKILL.md"]
            count_once_holds = len(named) == 1
            check(named and not count_once_holds,
                  f"the count-once assertion must FAIL for skills/corpus-skill/SKILL.md on a "
                  f"hand-built list holding it twice, got {len(named)} finding(s)")

        def duplicate_guard_negative_case() -> None:
            """§6's checked-in negative case: the guard, called with a doubled list.

            It exercises the guard alone and cannot fail a count assertion — it
            does not discharge case C's negative case, nor is it discharged by it.
            """
            lin = Linter(fa_corpus, fa_corpus, suite_rules=False)
            lin._guard_duplicate_free([fa_corpus_skill, fa_suite_skill, fa_corpus_skill])
            check(len(lin.findings) == 1 and lin.findings[0][0] == "fail"
                  and str(fa_corpus_skill.resolve()) in lin.findings[0][1],
                  f"the guard must emit one fail finding naming the duplicated path: "
                  f"{lin.findings}")

        def fixture_counts_exact() -> None:
            """Each fixture asserts its own seeded `.md` count — exactly."""
            check(len(Linter(fa_corpus, fa_suite, suite_rules=False).walk()) == 2,
                  "fixture A (nested) must sweep exactly its 2 seeded .md files")
            check(len(Linter(fb_corpus, fb_suite, suite_rules=False).walk()) == 1,
                  "fixture B (disjoint) must sweep exactly its 1 corpus-side .md file")
            check(len(Linter(fa_corpus, fa_corpus, suite_rules=False).walk()) == 1,
                  "case C (equal roots) must sweep exactly its 1 seeded .md file")
            # Binding the corpus walk to a root holding no corpus fails the count
            # assertion — the zero-sweep detection §6 gives up live.
            nocorpus = root / "nocorpus"
            nocorpus.mkdir(exist_ok=True)
            mis = Linter(nocorpus, nocorpus, suite_rules=False).walk()
            check(len(mis) == 0 and len(mis) != 2,
                  f"a corpus-less root must sweep nothing and fail fixture A's count: {mis}")

        # The TEMPLATE_PAIRS fixtures (§5): a synthetic source of record under the
        # suite root, the restating specs under the corpus root. Anchors and spec
        # paths are read from the shipped table, never restated here.
        tp = root / "templatepairs"
        tp_corpus = tp / "corpus"
        tp_suite = tp_corpus / "plugins" / "sdd"     # nested
        tp_far = tp / "elsewhere"                    # disjoint
        tp_equal = tp / "equal"
        tp_drift = TEMPLATE_PAIRS[0]
        tp_absent_spec = TEMPLATE_PAIRS[-1]["spec"]
        tp_by_spec: dict[str, list[dict]] = {}
        for _pair in TEMPLATE_PAIRS:
            tp_by_spec.setdefault(_pair["spec"], []).append(_pair)

        def _tp_fence(pair: dict) -> str:
            tail = "drifted\n" if pair is tp_drift else "body\n"
            return "```\n" + pair["anchor"] + "\n" + tail + "```\n"

        def _tp_write_source(base: Path, skip: dict | None = None) -> None:
            f = base / TEMPLATE_SOURCE
            f.parent.mkdir(parents=True, exist_ok=True)
            # The source of record never carries the drifted tail — the drift is
            # seeded on the restating side.
            f.write_text("# dispatch templates\n\n" + "".join(
                "```\n" + q["anchor"] + "\nbody\n```\n"
                for q in TEMPLATE_PAIRS if q is not skip), encoding="utf-8")

        def _tp_write_specs(base: Path) -> None:
            for spec_rel, pairs in tp_by_spec.items():
                if spec_rel == tp_absent_spec:
                    continue                      # seeded ABSENT: the spec side warns
                f = base / spec_rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("# spec\n\n" + "".join(_tp_fence(q) for q in pairs),
                             encoding="utf-8")

        _tp_write_source(tp_suite)
        _tp_write_source(tp_far, skip=tp_drift)    # the disjoint source LOST a fence
        _tp_write_source(tp_equal)
        _tp_write_specs(tp_corpus)
        _tp_write_specs(tp_equal)

        def template_pairs_bind_per_side() -> None:
            """One case per geometry, plus the negative control (§5, §7)."""
            absent_rows = [q for q in TEMPLATE_PAIRS if q["spec"] == tp_absent_spec]

            def warns(lin: Linter) -> list[str]:
                return [t for sev, t in lin.findings
                        if sev == "warn" and "pair not checked" in t]

            # (a) nested — the TEMPLATE_SOURCE side binds to the suite root and its
            #     drift is reported; an absent spec under the corpus root STILL warns.
            nested = Linter(tp_corpus, tp_suite, suite_rules=True)
            nested.check_template_drift()
            nested_texts = [t for _, t in nested.findings]
            drift = [t for t in nested_texts
                     if _loc(t) == tp_drift["spec"] and "diverges from" in t]
            check(len(drift) == 1,
                  f"nested: the suite-root source must be compared against the corpus-root "
                  f"spec:\n" + "\n".join(nested_texts))
            check(len(warns(nested)) == len(absent_rows)
                  and all(_loc(t) == tp_absent_spec for t in warns(nested)),
                  f"nested: an absent spec must still warn, once per row:\n"
                  + "\n".join(nested_texts))

            # (b) disjoint — the SPEC SIDE is skipped, not warned: no finding of any
            #     severity is located at any row's spec path (a named absent finding
            #     per row, never exit-code silence), while the TEMPLATE_SOURCE-side
            #     finding is still present.
            dis = Linter(tp_corpus, tp_far, suite_rules=True)
            check(not dis.suite_contained(), "the disjoint template geometry must be disjoint")
            dis.check_template_drift()
            dis_texts = [t for _, t in dis.findings]
            for pair in TEMPLATE_PAIRS:
                check(not any(_loc(t) == pair["spec"] for t in dis_texts),
                      f"disjoint: {pair['spec']} must emit no template-drift finding of any "
                      f"severity:\n" + "\n".join(dis_texts))
            source_side = [t for t in dis_texts
                           if _loc(t) == TEMPLATE_SOURCE and "no fence opens with" in t]
            check(len(source_side) == 1,
                  f"disjoint: the TEMPLATE_SOURCE-side finding must still be present:\n"
                  + "\n".join(dis_texts))

            # (c) equal roots — both sides bind to the one root over the same content,
            #     and the rendered finding set is the nested one: the pre-change
            #     behaviour, compared as a set derived at run time.
            eq = Linter(tp_equal, tp_equal, suite_rules=True)
            eq.check_template_drift()
            check(set(eq.findings) == set(nested.findings),
                  f"equal roots must reproduce the per-side behaviour: "
                  f"{sorted(set(eq.findings) ^ set(nested.findings))}")

            # (d) the negative control (§Acceptance Criteria bullet 6): binding BOTH
            #     sides to the suite root makes all four rows emit the absent-spec
            #     warning — the self-test asserts that this does NOT happen, so a
            #     wholesale one-root binding fails loudly rather than passing quietly.
            wrong = Linter(tp_suite, tp_suite, suite_rules=True)
            wrong.check_template_drift()
            check(len(warns(wrong)) == len(TEMPLATE_PAIRS),
                  f"the negative control must reproduce the wholesale-one-root symptom, "
                  f"got {len(warns(wrong))} of {len(TEMPLATE_PAIRS)}")
            for label, lin in (("nested", nested), ("equal", eq), ("disjoint", dis)):
                check(len(warns(lin)) < len(TEMPLATE_PAIRS),
                      f"{label}: all {len(TEMPLATE_PAIRS)} rows degraded to the absent-spec "
                      f"warning — the spec side is bound to the wrong root")

        # -- 11b. the three cases added post-plan from the verification of an
        #         earlier chunk (C3.10, C3.11 from Chunk 2;
        #         `check_structure_binds_to_the_suite_root` = C6.11 from Chunk
        #         5). They are IN ADDITION to the fourteen cases §Verification
        #         and C7.6 count.
        sd = root / "skilldir"
        sd_corpus = sd / "corpus"
        sd_suite = sd_corpus / "plugins" / "sdd"
        sd_suite_skill = _fixture_skill(
            sd_suite, "suite-skill", "Body. Skip for Y. See `references/detail.md`.\n") / "SKILL.md"
        (sd_suite / "skills" / "suite-skill" / "references").mkdir(parents=True, exist_ok=True)
        (sd_suite / "skills" / "suite-skill" / "references" / "detail.md").write_text(
            "# detail\n", encoding="utf-8")
        _fixture_skill(sd_corpus, "corpus-skill", "Body. Skip for Y. See `references/gone.md`.\n")

        def skill_dir_of_binds_per_root() -> None:
            """C3.10: `skill_dir_of()` binds to the root its file was walked from.

            `self.root / "skills"` alone raised `ValueError` for every suite-root
            file carrying a `references/…` backtick span once the two roots differ.
            """
            lin = Linter(sd_corpus, sd_suite, suite_rules=False)
            check(lin.skill_dir_of(sd_suite_skill).resolve()
                  == (sd_suite / "skills" / "suite-skill").resolve(),
                  f"the suite-root file's skill dir must bind to the suite root: "
                  f"{lin.skill_dir_of(sd_suite_skill)}")
            try:
                lin.check_links()
            except ValueError as exc:               # pragma: no cover - the regression
                check(False, f"a nested suite-root file with a `references/…` span raised "
                             f"ValueError: {exc}")
                return
            texts = [t for _, t in lin.findings]
            check(not any(_loc(t) == "skills/suite-skill/SKILL.md" for t in texts),
                  f"the suite-root span resolves against its own skill dir:\n" + "\n".join(texts))
            check(any(_loc(t) == "skills/corpus-skill/SKILL.md" and "[path]" in t
                      for t in texts),
                  f"the corpus-root skill dir must still resolve its own spans:\n"
                  + "\n".join(texts))
            # Equal and disjoint geometries resolve too (a disjoint suite root's
            # files are not walked, so the corpus side is what is reachable there).
            for label, lin2 in (("equal", Linter(sd_corpus, sd_corpus, suite_rules=False)),
                                ("disjoint", Linter(sd_corpus, root / "nowhere",
                                                    suite_rules=False))):
                got = lin2.skill_dir_of(sd_corpus / "skills" / "corpus-skill" / "SKILL.md")
                check(got.resolve() == (sd_corpus / "skills" / "corpus-skill").resolve(),
                      f"{label}: corpus skill dir mis-bound to {got}")

        ac = root / "allowfiles"
        ac_corpus = ac / "corpus"
        ac_suite = ac_corpus / "plugins" / "sdd"
        AC_TOKEN = "SYNTHETIC-ROOT-CORRECT"
        _fixture_skill(ac_suite, "allowed-skill", f"Body. Skip for Y.\n{AC_TOKEN}\n")
        _fixture_skill(ac_suite, "flagged-skill", f"Body. Skip for Y.\n{AC_TOKEN}\n")

        def forbidden_allow_files_root_correct() -> None:
            """C3.11: `FORBIDDEN`'s row filter and allowlist match a root-correct path.

            A corpus-rooted local path renders a suite-root file as
            `plugins/sdd/skills/…`, so an `allow_files` entry such as
            `skills/orchestrate/SKILL.md` silently stops matching and that
            allowlist row is disabled with no diagnostic. The finding's RENDERING
            was already correct (`flag()`'s `self.rel()` default) — this is the
            matching path, not the rendering.
            """
            global FORBIDDEN
            synthetic = {"pattern": AC_TOKEN, "files": "skills/", "allow": [],
                         "allow_files": ["skills/allowed-skill/SKILL.md"],
                         "reason": "root-correct allow_files fixture",
                         "fix": "SYNTHETIC-ROOT-CORRECT-FIX"}
            shipped = FORBIDDEN
            FORBIDDEN = [synthetic]
            try:
                lin = Linter(ac_corpus, ac_suite, suite_rules=False)
                lin.check_forbidden()
            finally:
                FORBIDDEN = shipped
            texts = [t for _, t in lin.findings]
            check(not any(_loc(t) == "skills/allowed-skill/SKILL.md" for t in texts),
                  f"an allow_files entry must still match a suite-root file under nested "
                  f"roots:\n" + "\n".join(texts))
            check(len(texts) == 1 and _loc(texts[0]) == "skills/flagged-skill/SKILL.md",
                  f"the row must still fire on the non-allowlisted suite-root file:\n"
                  + "\n".join(texts))

        cs = root / "structure"
        cs_corpus = cs / "corpus"
        cs_suite = cs_corpus / "plugins" / "sdd"
        _fixture_skill(cs_suite, "good-skill", "Body. Skip for Y.\n")
        (cs_suite / "skills" / "mismatched").mkdir(parents=True, exist_ok=True)
        (cs_suite / "skills" / "mismatched" / "SKILL.md").write_text(
            "---\nname: not-the-dir\ndescription: >\n  Use for X. Skip for Y.\n---\n\n# x\n",
            encoding="utf-8")
        (cs_corpus / "docs").mkdir(parents=True, exist_ok=True)

        def check_structure_binds_to_the_suite_root() -> None:
            """C6.11: `check_structure()` walks `<suite_root>/skills`, not the corpus's.

            `self.root / "skills"` alone names the CORPUS root's tree, which after
            the move does not exist; the check then emitted one
            `[structure] skills/ directory not found` finding and returned, so
            every per-skill frontmatter and name-match rule stopped running with
            no diagnostic that they had. Added post-plan from the Chunk 5
            verification; §4's binding table puts `skills` on the suite root.
            """
            lin = Linter(cs_corpus, cs_suite, suite_rules=False)
            lin.check_structure()
            texts = [t for _, t in lin.findings]
            check(not any("skills/ directory not found" in t for t in texts),
                  "the nested suite's skills/ must be found at the suite root:\n"
                  + "\n".join(texts))
            check(any(_loc(t) == "skills/mismatched/SKILL.md" and "not-the-dir" in t
                      for t in texts),
                  "the per-skill rules must still run against the suite-root tree:\n"
                  + "\n".join(texts))
            check(not any(_loc(t) == "skills/good-skill/SKILL.md" for t in texts),
                  "the clean suite-root skill must not be flagged:\n" + "\n".join(texts))
            # The INVERSION, so the case cannot pass vacuously: bind the suite
            # root at the corpus root, which holds no `skills/` — exactly what
            # the corpus binding did post-move — and the single not-found
            # finding comes back and the per-skill findings disappear.
            inv = Linter(cs_corpus, cs_corpus, suite_rules=False)
            inv.check_structure()
            inv_texts = [t for _, t in inv.findings]
            check(len(inv_texts) == 1 and "skills/ directory not found" in inv_texts[0],
                  "inversion: a root with no skills/ must yield exactly the "
                  "not-found finding:\n" + "\n".join(inv_texts))

        def check_size_binds_to_the_swept_roots() -> None:
            """C8.2: `check_size()` measures the swept-root UNION, not one root.

            The invertible case the size check never had. `_run_capture()` sets
            both roots equal, so every pre-existing size fixture is
            geometry-blind: `self.root`, `self.suite_root` and the union are
            indistinguishable there, and a wrong binding stays green. The two
            halves below pin distinct roots, and each half fails under a
            different wrong binding.

            **Mutation that breaks it.** Rebinding the loop to
            `self.suite_root` alone drops `skills/big-corpus/SKILL.md` from the
            nested half AND makes the disjoint half report the suite's file
            instead of the corpus's — the exact defect that measured the live
            installed suite from inside `gc.py`'s fixture run and turned
            `gc.py --self-test` red. Rebinding it to `self.corpus_root` /
            `self.root` alone drops `skills/big-suite/SKILL.md` from the nested
            half (added post-plan from the implement-stage review).
            """
            over = SIZE_FAIL_LINES + 40
            # -- nested: an oversized SKILL.md at EACH root is measured.
            nz = root / "sizegeom" / "nested"
            nz_suite = nz / "plugins" / "sdd"
            _fixture_skill(nz, "big-corpus", "Body. Skip for Y.\n", lines=over)
            _fixture_skill(nz_suite, "big-suite", "Body. Skip for Y.\n", lines=over)
            lin = Linter(nz, nz_suite, suite_rules=False)
            lin.check_size()
            texts = [t for _, t in lin.findings if "[size]" in t]
            check(any(_loc(t) == "skills/big-corpus/SKILL.md" for t in texts),
                  "nested: the CORPUS root's oversized SKILL.md must be measured "
                  "(REQ-PKG-PACKAGING-005 puts size on the corpus root):\n"
                  + "\n".join(texts))
            check(any(_loc(t) == "skills/big-suite/SKILL.md" for t in texts),
                  "nested: the contained SUITE root's oversized SKILL.md must be "
                  "measured (§4's binding table):\n" + "\n".join(texts))
            # -- disjoint: the suite root is outside swept_roots(), so it is
            # neither measured nor renderable — the consumer geometry, and the
            # geometry `gc.py`'s frozen fixture shim constructs.
            dz_corpus = root / "sizegeom" / "dis-corpus"
            dz_suite = root / "sizegeom" / "dis-suite"
            _fixture_skill(dz_corpus, "big-corpus", "Body. Skip for Y.\n", lines=over)
            _fixture_skill(dz_suite, "big-suite", "Body. Skip for Y.\n", lines=over)
            dlin = Linter(dz_corpus, dz_suite, suite_rules=False)
            dlin.check_size()          # must not raise ValueError out of rel()
            dtexts = [t for _, t in dlin.findings if "[size]" in t]
            check(len(dtexts) == 1 and _loc(dtexts[0]) == "skills/big-corpus/SKILL.md",
                  "disjoint: exactly the CORPUS root's oversized file is measured; "
                  "a disjoint suite root is not swept:\n" + "\n".join(dtexts))

        def print_population_shape() -> None:
            """C4.3 — `--print-population`'s output asserted by SHAPE, not by value.

            The fourteenth checked-in case (two-root-linter.md §Verification).
            **No number is pinned here**: each table line must carry an integer
            that EQUALS the live table's length read at run time, so the case
            measures that the flag derives its counts rather than agreeing with
            a literal on both sides (§6). Inverting the shape — asserting a line
            the flag does not print — fails the self-test.
            """
            pp = root / "population"
            pp.mkdir(exist_ok=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = print_population(pp, pp)
            lines = buf.getvalue().splitlines()
            expected = population_tables()
            check(code == 0, f"--print-population must exit 0, got {code}")
            check(len(lines) == len(expected) + 1,
                  f"--print-population must print one line per rule table plus the "
                  f"corpus line ({len(expected) + 1}), got {len(lines)}: {lines}")
            for (label, n), line in zip(expected, lines):
                m = re.fullmatch(rf"{re.escape(label)}=([0-9]+)", line)
                check(m is not None,
                      f"the {label} line must read `{label}=<int>`, got {line!r}")
                if m:
                    check(int(m.group(1)) == n,
                          f"{label} must print its run-time row count, not a literal: "
                          f"printed {m.group(1)}, table holds {n}")
            # C8.4 — §6's population criterion, asserted rather than evaluated
            # once by hand. `population_tables()` is the same live table read
            # on both sides above, so that loop passes for ANY row count; these
            # four are the pinned comparands §6 states ("the one place in the
            # corpus where a row population is compared against a number"), and
            # they are the regression check on §3's retarget. A row dropped or
            # duplicated in any of the four now fails the self-test rather than
            # a one-off evaluation nobody re-runs
            # (added post-plan from the implement-stage review).
            pinned = {"REQUIRED": 40, "VERSION_GATED": 9, "V4_CONTRACT": 7,
                      "FORBIDDEN": 13}
            for label, want in pinned.items():
                check(f"{label}={want}" in lines,
                      f"§6 pins {label}={want}; --print-population printed "
                      f"{[l for l in lines if l.startswith(label + '=')]}")
            corpus_line = lines[-1] if lines else ""
            check(re.fullmatch(r"corpus: FILES_SWEPT=([0-9]+)  policed-areas=([0-9]+)",
                               corpus_line) is not None,
                  f"the corpus line must read "
                  f"`corpus: FILES_SWEPT=<int>  policed-areas=<int>`, got {corpus_line!r}")

        for _case in (two_roots_construct_distinct_and_equal,
                      equal_roots_sweep_set_unchanged,
                      sweep_is_duplicate_free,
                      retired_scope_binds_per_entry,
                      retarget_seeds_an_ungated_finding,
                      nested_roots_render_per_root,
                      disjoint_suite_walk_excluded,
                      manifest_pair_membership,
                      case_c_counts_once,
                      case_c_negative_double_count,
                      duplicate_guard_negative_case,
                      fixture_counts_exact,
                      template_pairs_bind_per_side,
                      print_population_shape,
                      skill_dir_of_binds_per_root,
                      forbidden_allow_files_root_correct,
                      check_structure_binds_to_the_suite_root,
                      check_size_binds_to_the_swept_roots):
            _case()

    if failures:
        print("SELF-TEST FAIL:\n- " + "\n- ".join(failures))
        return 1
    print("SELF-TEST OK: all rule classes fire; fix/warn/size/backtick/allow_files/"
          "retired-prefix fixtures pass")
    return 0


def population_tables() -> list[tuple[str, int]]:
    """The printed rule-table populations, derived from the tables at run time.

    Each row is `(label, len(<table>))` read from the live table object — no
    count is ever written into this function or into the flag, so a row
    dropped or duplicated by a later edit (two-root-linter.md §6's regression
    concern for §3's retarget) changes the OUTPUT instead of silently agreeing
    with a literal on both sides. The lengths are read at call time so a
    fixture that swaps a table in is reflected.
    """
    return [
        ("REQUIRED", len(REQUIRED)),
        ("VERSION_GATED", len(VERSION_GATED_SKILLS)),
        ("V4_CONTRACT", len(V4_CONTRACT_SKILLS)),
        ("FORBIDDEN", len(FORBIDDEN)),
        ("TEMPLATE_PAIRS", len(TEMPLATE_PAIRS)),
    ]


def print_population(corpus_root: Path, suite_root: Path) -> int:
    """`--print-population`: one line per rule table, plus the corpus line.

    The corpus line is **informational output only** and carries no pinned
    comparand (two-root-linter.md §6): a swept-file count from a live corpus
    is never asserted, because a literal fails on ordinary contribution and
    any re-derived comparand asserts the sweep against itself. Zero-sweep
    detection therefore lives in §7's fixture counts, not here. Exits 0.
    """
    for label, count in population_tables():
        print(f"{label}={count}")
    lin = Linter(corpus_root, suite_root)
    swept = lin.skill_files()
    policed = len(RETIRED_SCOPE_DIRS) + len(RETIRED_SCOPE_FILES)
    print(f"corpus: FILES_SWEPT={len(swept)}  policed-areas={policed}")
    # REQ-LINT-PACKAGING-005: the duplicate-freeness construction guard's
    # observable is a `fail`-severity finding in the run's own findings list
    # that NO invocation mode can skip. This mode calls the union builder
    # (`skill_files()`), which runs the guard — and then discarded its
    # findings, making this the one mode in which the guard was unobservable.
    # The findings are printed here and a `fail` exits non-zero; the flag's
    # "exits 0" (§6) still holds for every run in which nothing fired, which
    # is every run of a correctly constructed union. See Q-IMPL-PACKAGING-003.
    n_fail = 0
    for severity, text in lin.findings:
        print(("WARN " if severity == "warn" else "") + text)
        if severity == "fail":
            n_fail += 1
    return 1 if n_fail else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="skill-lint",
        description="Consistency linter for the SDD skill suite "
                    "(frontmatter, drift phrases, contract markers, ordinals, links, "
                    "backtick paths, SKILL.md size).",
    )
    ap.add_argument("root", nargs="?", default=None,
                    help="corpus root to lint (default: the invocation cwd); the "
                         "suite root is the plugin root holding this script")
    ap.add_argument("--self-test", action="store_true",
                    help="run built-in fixture tests instead of linting")
    ap.add_argument("--print-population", action="store_true",
                    help="print each rule table's run-time row count plus the "
                         "informational corpus line, then exit (no assertions)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    # The corpus root defaults to the invocation cwd, never to the script's
    # location: after the move the script's parent-of-parent names the suite,
    # and that default would silently stop sweeping the operator's corpus.
    root = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    if args.print_population:
        return print_population(root, default_suite_root())
    return Linter(root, default_suite_root()).run()


if __name__ == "__main__":
    sys.exit(main())
