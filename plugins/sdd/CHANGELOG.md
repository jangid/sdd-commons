# Changelog

This file ships with the `sdd` plugin (it lives under `plugins/sdd/`, the
plugin's source root, so a consumer's install delivers it). All notable
changes to the plugin are listed here. Versions follow semver as read from
`plugins/sdd/.claude-plugin/plugin.json`.

## 0.2.0 — 2026-09-22 (pipeline-observability)

Changes a consumer repository will notice when it updates:

- **Two new `fail`-severity drift-sweep rules** in `plugins/sdd/tools/gc.py`:
  `self-matching-grep` (a counting `grep` whose quoted pattern matches its own
  line while the file is among its operands) and `qimpl-malformed` (under
  marker `4`, a bare `Q-IMPL-NNN` reference with no bare definition). Neither
  is auto-fixable. A corpus with pre-existing instances fails its commit gate
  until they are repaired — by fencing the criterion, excluding the file by
  path, or giving the reference its workstream segment. This repository needed
  forty such repairs in its own requirements.
- **Two new `warn`-severity rules**, folded per file: `literal-anchor` (a
  `file.md:line` citation on an unfenced line of a spec or requirement) and
  `dead-path-citation` (an inline-code path that resolves neither at the
  corpus root nor under `plugins/sdd/`). They never change the exit status.
- **`telemetry.py append`**: the orchestrator writes gate records through a
  validating subcommand; `TELEMETRY: rec <n>` renders only on its exit 0.
  `migrate` gains the `flat-cg` shape for schema-less records.
- **Review routing**: `APPROVE_WITH_FIXES` is fix-then-proceed with no
  re-review unless the operator opts in; the fix-loop cap counts consecutive
  consumed `REJECT`s; a manual intervention is followed by a `post-manual`
  review; a read-only leaf that mutates git state has its verdict voided.
- **One review report grammar** for both producers (`skills/review/SKILL.md`
  and `agents/reviewer.md`), with three disjoint verdict predicates; the gate
  consumes a report whose tiers disagree with its token as malformed.
- `skill-lint.py`: fifteen `REQUIRED` rows and one `FORBIDDEN` row pin the
  above; the rule-table population is asserted by a three-way equality
  (`--print-population` == code tables == `docs/spec/two-root-linter.md` §6).
- The `.claude/` directory is excluded from the hygiene hooks in
  `.pre-commit-config.yaml`.

## 0.1.0 — 2026-09-21

Initial marketplace release (see `docs/ws/marketplace/`).
