---
last_updated: 2026-09-17
---

# Research Index

| ID | Topic | Date | Status | Summary |
|----|-------|------|--------|---------|
| RS-001 | SDD artifact structure | 2026-04-27 | Complete | Plan bloat, research traceability, and requirements splitting — v2 structure designed |
| RS-002 | SDD skill improvements | 2026-05-25 | Complete | Chunk-close review checklist, Q-IMPL protocol, per-milestone plans, drift detection — six workflow gaps identified from rubric M1 |
| RS-003 | v3 migration path | 2026-05-25 | Complete | One migration-required change (plan vocabulary), lightweight v2→v3 procedure, v1→v3 via sequential composition |
| RS-004 | sdd-review skill design | 2026-05-25 | Complete | External review catches critical issues at phase boundaries; ~7 requirements for a formal skill covering phase detection, report format, trigger classification, and session isolation |
| RS-005 | sdd-orchestrate feasibility | 2026-06-04 | Complete | Subagent skill-invocation and dispatch-time review isolation both proven with live dispatches; no new resume marker needed, fan out along independent plan chunks, package as one skill — greenlight for requirements |
| RS-006 | Subagent nesting & worktrees | 2026-06-04 | Complete | Nested dispatch blocked (subagents have no dispatch tool); subagent worktree create/commit and sequential merge with abort-redo fallback all proven — evidence selects orchestrator-owned fan-out (one level deep), not nested |
| RS-007 | Multi-workstream SDD | 2026-07-21 | Complete | Plain table append conflicts under concurrency (proven) — use sorted-into-distinct-regions or per-ws-owned rows/files; milestone staleness generalizes to ws-scope for plan/implement/replan, new branches for verify/specs; v3→v4 migrate is copy-verify-flip-cleanup with .sdd-version flipped last; ws-prefixed IDs break 4 ID-generators + 1 review convention string, nothing else |
| RS-008 | Harness hardening | 2026-09-17 | Complete | Loop-control state needs no new artifact (per-session fix count, replan count derived from plan-history, checkpoint in the plan's blocked-task note); chunk-close verifier is a second executor of sdd-implement Step 4, never sdd-review; structured RETURN block + fixed-shape repair packet; lint can check all marker contracts via REQUIRED rows, needs 3 small code changes (size warn, backtick refs, remediation); write-scope check = porcelain delta + committed delta + ancestry — all 12 in-scope ideas research-complete |
