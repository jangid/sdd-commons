---
status: Approved
last_updated: 2026-09-22
workstream: pipeline-observability
requires:
  - REQ-AGENT-MARKETPLACE-002
  - REQ-AGENT-PIPELINEOBSERVABILITY-001
  - REQ-ARB-HARNESSP2-002
  - REQ-ARB-HARNESSP3-001
  - REQ-ARB-PIPELINEOBSERVABILITY-001
  - REQ-CHKC-004
  - REQ-DOCS-PIPELINEOBSERVABILITY-001
  - REQ-GC-HARNESSP2-002
  - REQ-GC-HARNESSP2-003
  - REQ-GC-HARNESSP6-003
  - REQ-GC-PIPELINEOBSERVABILITY-001
  - REQ-GC-PIPELINEOBSERVABILITY-002
  - REQ-GC-PIPELINEOBSERVABILITY-003
  - REQ-GC-PIPELINEOBSERVABILITY-004
  - REQ-HARN-001
  - REQ-HARN-013
  - REQ-HARN-HARNESSP6-001
  - REQ-HARN-PIPELINEOBSERVABILITY-001
  - REQ-HARN-PIPELINEOBSERVABILITY-002
  - REQ-HARN-PIPELINEOBSERVABILITY-003
  - REQ-HARN-PIPELINEOBSERVABILITY-004
  - REQ-HARN-PIPELINEOBSERVABILITY-005
  - REQ-HARN-PIPELINEOBSERVABILITY-006
  - REQ-LINT-PIPELINEOBSERVABILITY-001
  - REQ-LINT-PACKAGING-007
  - REQ-PC-PIPELINEOBSERVABILITY-001
  - REQ-PKG-PIPELINEOBSERVABILITY-001
  - REQ-REQ-PIPELINEOBSERVABILITY-001
  - REQ-REV-002
  - REQ-REV-PIPELINEOBSERVABILITY-001
  - REQ-TELEM-HARNESSP2-004
  - REQ-TELEM-HARNESSP3-001
  - REQ-TELEM-HARNESSP4-005
  - REQ-TELEM-HARNESSP5-008
  - REQ-TELEM-PIPELINEOBSERVABILITY-001
  - REQ-TELEM-PIPELINEOBSERVABILITY-002
  - REQ-TELEM-PIPELINEOBSERVABILITY-003
---

# Pipeline Observability — the harness verifying itself (delta map)

## Context

The consumer-geometry cycle rendered every gate green while the harness
silently reduced its own claims: `TELEMETRY: rec 39` with no readable record,
`FIX_LOOP_MAX` exhausted four times on verdicts that should have closed their
stages, read-only leaves that stashed and edited, four manual interventions no
review ever saw (`docs/ws/pipeline-observability/kickoff.md` §The observation;
RS-PIPELINEOBSERVABILITY-001). The requirements stage bound the eleven gaps as
twenty-one new requirements and sixteen in-place amendments to existing
requirements — the amendments in eight domains (AGENT, ARB, CHKC, GC, HARN,
LINT, REV, TELEM; the LINT one, REQ-LINT-PACKAGING-007, joined at requirements
27.4 from the specs closing review, Q-REQ-PO-AL), the new requirements in six
of those eight (AGENT 1, ARB 1, GC 4, HARN 6, REV 1, TELEM 3 — sixteen) plus
four domains that gain only one new id each (PC, PKG, DOCS, REQ) and LINT's
one new id beside its amendment — twenty-one in all; per-domain counts by
`grep -c "^| REQ-<DOMAIN>-PIPELINEOBSERVABILITY-"` over
`docs/ws/pipeline-observability/traceability.md`, re-run 2026-09-22) — and
sixteen existing spec files touched in all (Q-REQ-PO-N: no new prefix). This spec is the **map** of where each of
those thirty-seven requirements is designed — every one is designed in the
**section of record** of the existing spec that owns its contract, edited in
place under a `[Updated: 2026-09-22]` marker, with that spec's dated
`## Pipeline-Observability Amendment` section as the record of *why*
(REQ-REQ-PIPELINEOBSERVABILITY-001 (b); re-derived against requirements 27.2
on 2026-09-22 and mirrored to 27.3, Q-REQ-PO-AK, the same day) — and the record of the decisions the specs stage took
(`Q-SPEC-PO-*`). It holds no contract of its own: reverting any binding below
is caught by the owning spec's acceptance criteria, not by this file.

Two rules the requirements gate handed this stage govern every amendment:
**no line-number or commit-sha comparand** — each mechanical criterion is
dereferenced to a durable key (a skill-lint `REQUIRED`/`FORBIDDEN` row, a
`--self-test` case name, a `--lint` assertion id, a gc rule name, a section
heading) — and **the V3 routing is specified as in force**, not re-proposed.

## Design

### Where each requirement is designed

The `requires:` list in this file's frontmatter is a **back-reference** for
the coverage check, not an ownership claim: the owning spec's `requires:` is
authoritative for every id below, and every `Spec` cell of
`docs/ws/pipeline-observability/traceability.md` names the owning spec's
section of record, never an amendment section and never this map —
`grep -c '^|.*pipeline-observability\.md' docs/ws/pipeline-observability/traceability.md`
reads 0 (scoped to table rows: the file's header prose names this map once,
so the unanchored form reads 1).

| Requirement | Owning spec and section of record (the `Spec` cell) | Record of why |
|---|---|---|
| REQ-TELEM-PIPELINEOBSERVABILITY-001; REQ-TELEM-HARNESSP2-004 (amended) | `telemetry.md` §Writer | §Pipeline-Observability Amendment — `append` validates before it writes |
| REQ-TELEM-HARNESSP3-001 (amended) | `telemetry.md` §Positive Gate Line `TELEMETRY: rec <n>` | same |
| REQ-TELEM-PIPELINEOBSERVABILITY-002; REQ-TELEM-HARNESSP4-005 (amended) | `telemetry-reader.md` §In-Place Migration of the 8 p3 Records | §Pipeline-Observability Amendment — `flat-cg` |
| REQ-TELEM-PIPELINEOBSERVABILITY-003; REQ-TELEM-HARNESSP5-008 (amended) | `telemetry-reader.md` §Schema Lint | same — four cross-field assertions ((d) over the four non-`legal` cells, Q-REQ-PO-AK), `POST_MANUAL` / `manual_intervention` / `malformed` |
| REQ-HARN-PIPELINEOBSERVABILITY-001, -003; REQ-HARN-001 (amended) | `harness-loop-control.md` §Fix-Loop Cap | §Pipeline-Observability Amendment — routing in force, `reject_run`, the `post-manual` review and its footprint |
| REQ-HARN-PIPELINEOBSERVABILITY-002 | `harness-loop-control.md` §Gate Signal Order | same — row 6d, `GROWTH:` |
| REQ-HARN-PIPELINEOBSERVABILITY-006 | `harness-loop-control.md` §Budget Slot | same — derived test-run budget |
| REQ-HARN-PIPELINEOBSERVABILITY-004; REQ-HARN-HARNESSP6-001 (amended) | `harness-write-scope.md` §Git-State Observation | §Pipeline-Observability Amendment — the void rule and its per-gate `REDO_MAX`-valued bound |
| REQ-HARN-PIPELINEOBSERVABILITY-005; REQ-HARN-013 (amended) | `harness-return-contract.md` §VERDICT Token | §Pipeline-Observability Amendment — tier-section parsing: `blocking_items` and `material_items`, placeholder normalisation, six pauses (two missing-section, four conflict) exhaustive over the 4×3 case table, fixtures F1–F9 (Q-REQ-PO-AE, -AF, -AJ, -AK) |
| REQ-REV-PIPELINEOBSERVABILITY-001; REQ-REV-002 (amended) | `review.md` §Report Format | §Pipeline-Observability Amendment — the report grammar and the three disjoint verdict predicates, (3) cross-referencing the consumer's case table (Q-REQ-PO-Z, -AK, Q-SPEC-PO-I) |
| REQ-ARB-PIPELINEOBSERVABILITY-001; REQ-ARB-HARNESSP2-002 (amended) | `arbitrated-handoff.md` §Contradiction Classes (the `W_N` schema line of §Retained Per-Round State edited in place) | §Pipeline-Observability Amendment — `new[N]` |
| REQ-ARB-HARNESSP3-001 (amended) | `arbitrated-handoff.md` §`W_N` Includes Regeneration Writes | same |
| REQ-AGENT-PIPELINEOBSERVABILITY-001; REQ-AGENT-MARKETPLACE-002 (amended) | `harness-agents.md` §The frontmatter contract | §Pipeline-Observability Amendment — the git-state sentence; `reviewer.md` carries the grammar by reference |
| REQ-GC-PIPELINEOBSERVABILITY-001, -002, -004; REQ-GC-HARNESSP2-002 (amended) | `drift-sweep.md` §Sweep Table | §Pipeline-Observability Amendment — rows 16–18, source-line discipline, command-line and token grammars (Q-REQ-PO-AB, -W) |
| REQ-GC-PIPELINEOBSERVABILITY-003; REQ-GC-HARNESSP2-003 (amended) | `drift-sweep.md` §Q-IMPL Counting Rule | same — `qimpl-malformed` |
| REQ-GC-HARNESSP6-003 (amended) | `drift-sweep.md` §Shared-Spec Staleness | same — traced stale-chain `warn` |
| REQ-LINT-PIPELINEOBSERVABILITY-001 | `skill-lint-v5.md` §`FORBIDDEN` Row — `literal-anchor` (the fifteen rows: §`REQUIRED` Rows — Pipeline-Observability; the totals they land: §Self-Test Extension) | §Pipeline-Observability Amendment |
| REQ-LINT-PACKAGING-007 (amended) | `two-root-linter.md` §6. Counts: asserted, or only printed | §Pipeline-Observability Amendment — the dated numbers (`42 / 9 / 7 / 14` current, `57` / `15` after the rows) and the three-way equality that replaces the frozen pin (Q-REQ-PO-AL, Q-SPEC-PO-U) |
| REQ-CHKC-004 (amended) | `chunk-close-review.md` §Checklist (Check 3) | §Pipeline-Observability Amendment — the derived module set |
| REQ-PC-PIPELINEOBSERVABILITY-001 | `pre-commit.md` §Design (the excluded-paths table of record) | §Pipeline-Observability Amendment — `.claude/` excluded |
| REQ-PKG-PIPELINEOBSERVABILITY-001 | `marketplace-packaging.md` §The manifest pair | §Pipeline-Observability Amendment — the version bump (minimal; the split is out of scope) |
| REQ-DOCS-PIPELINEOBSERVABILITY-001 | `project-docs.md` §`CLAUDE.md` | §Pipeline-Observability Amendment — `CLAUDE.md` bindings |
| REQ-REQ-PIPELINEOBSERVABILITY-001 | `requirements-artifacts.md` §Amendment Landing | §Pipeline-Observability Amendment — the five clauses (Q-SPEC-PO-M) |

`orchestration.md` §Gate Protocol / §v5 Harness Hardening and
`harness-commit-fidelity.md` are **not amended by this stage**: the first
points at `harness-loop-control.md` §Gate Signal Order rather than restating
the order, and the second's `COMMIT:` comparand is reused unchanged by the
`post-manual` rule. "Not amended by this stage" is not "unchanged on this
branch": `orchestration.md`'s loop-back row was changed by the routing fix
landed at the research gate (the V3 routing this stage specifies as in force),
so that file is in the branch diff without carrying a
`## Pipeline-Observability Amendment` section or an `[Updated: 2026-09-22]`
marker, and the count criteria below exclude it by construction. `harness-chunk-verifier.md` is likewise **not amended and not re-dated**
(`last_updated: 2026-09-19`): it inherits the Check 3 declared-convention
clause by reference — its §Positioning has the verifier re-run Check 3 as
`chunk-close-review.md` defines it — and row p12 pins the verifier body
directly, so no sentence of that spec changes; gc's `stale-chain` line on it is
the untraced shared-spec `info` class, unrouted by design until a plan traces
it (`drift-sweep.md` §Sweep Table).

Nine criteria of the amendments are decided at the verify stage by
construction and each needs a **verify-typed plan task** of its own: the live
`summarize --workstream consumer-geometry` record count after migration
(`telemetry-reader.md`); the gates that ran under the fix-then-proceed routing,
the manual-intervention list with the `post-manual` round that followed each,
and the conditional `GROWTH:` quotation (`harness-loop-control.md`, three
criteria); the real-chunk Check 3 `pass` under a declared convention
(`chunk-close-review.md`); the installed cache's version after `/plugin
update` (`marketplace-packaging.md`); and the three **gate-rendering
walkthroughs** — the `reject_run` verdict sequences
(`harness-loop-control.md`), the chunk-0 void sequence
(`harness-write-scope.md`) and the tier fixture bodies
(`harness-return-contract.md`) — whose transcripts are recorded in this
cycle's `docs/ws/pipeline-observability/verification.md` under the section
headed `Gate-rendering walkthroughs`, the comparand each of those three
criteria names (Q-SPEC-PO-L).

### Cross-spec consistency statement (XSPEC, operator rule 1)

Each amendment names the existing sections it touches and the sections it
leaves consistent. The cross-references that carry shared vocabulary between
amendments, checked pairwise at this stage:

| Referencing amendment | Referenced contract | Agreement |
|---|---|---|
| `telemetry-reader.md` assertions (a)–(d) | `harness-write-scope.md` void rule; `harness-loop-control.md` `reject_run` and `post-manual`; `harness-return-contract.md` tier count | each assertion's fields (`scope.token`, `gate.fix_iteration`, `gate.decision = manual_intervention`, `dispatch.reason = POST_MANUAL`, `verdict.findings.C`, `gate.decision = malformed`) are named identically on both sides |
| `harness-write-scope.md` bound | `harness-loop-control.md` §Redo Cap per Chunk | `REDO_MAX` is reused as a **value**; the counter `voided_redispatch_count[<gate>]` is distinct from `chunk_redo_count[<chunk header>]` |
| `harness-loop-control.md` row 6d | `skills/orchestrate/references/loop-control.md` §5 item 6d; `CLAUDE.md` §Gate vocabulary (`project-docs.md`) | `GROWTH:` sits after `CONVERGENCE:` (6c) and before `TELEMETRY:` (7) in all three |
| `harness-return-contract.md` §VERDICT Token counts | `review.md` §Report Format grammar (label lines, extent, placeholder set) and `agents/reviewer.md` (the same grammar by reference) | the consumer names no label form of its own; both producers are bound to one list (Q-SPEC-PO-N); the consumer's three `legal` cells are the producer's three predicates of (3), so the six pauses are exhaustive over the grammar (Q-REQ-PO-AK) |
| `arbitrated-handoff.md` `new[N]` | `skills/orchestrate/references/loop-control.md` §2a schema block | the `W_N` line carries the same three terms on both sides |
| `harness-agents.md` sentence | `skill-lint-v5.md` rows p1–p3 | pattern `git stash`, one row per body |
| `harness-loop-control.md` `post-manual` footprint | `telemetry-reader.md` assertion (c); `telemetry.md` §Record Schema | `POST_MANUAL`, `manual_intervention`, `gate.fix_iteration` equal to the preceding gate record — named identically on both sides (Q-SPEC-PO-O) |
| `chunk-close-review.md` derived module set | `skill-lint-v5.md` rows p11–p12 | pattern `script path in a command` on both executors (Q-SPEC-PO-R) |
| `harness-write-scope.md` void sentence and bound | `skill-lint-v5.md` rows p6–p8 | row p6's pattern (`voids its verdict`) is disjoint from row p8's bound line (`voided re-dispatch` + `REDO_MAX`), so deleting the §1b void sentence alone fails the linter; row p7 pins the §8 consumer half |
| `drift-sweep.md` `qimpl-malformed` | REQ-GC-HARNESSP3-001 convention (§Convention: Do Not Quote…) | membership by definition set, not by shape — the declined scoping is not reopened |
| `chunk-close-review.md` clause | `harness-chunk-verifier.md` §Positioning | the verifier re-runs Check 3 by reference; rows p11/p12 pin both executors |
| `requirements-artifacts.md` §Amendment Landing (c) | `ws-traceability.md` §Per-Workstream File Shape | the `(amended)` marker adds a meaning to a row the workstream already owns; row ownership is unchanged |

The Step 4b type-map extraction reports **no extractable type definitions**
for every amended spec (Q-SPEC-PO-G); the table above is the pass that stands
in for it and found no field-name mismatch.

### Q-SPEC resolutions (pipeline-observability)

- **Q-SPEC-PO-A** (amend in place or new spec, per requirement): **amend in
  place, every one.** Each of the thirty-seven requirements (the row count of
  `docs/ws/pipeline-observability/traceability.md` —
  `grep -c '^| REQ-' docs/ws/pipeline-observability/traceability.md` reads 37
  on 2026-09-22, Q-SPEC-PO-V) amends or extends a
  contract an existing spec already owns — the section of record is edited in
  place (Q-SPEC-PO-M supersedes the earlier "dated amendment section at the
  end of that spec" as the carrier) and the amendment section records why.
  This file is the only new spec and holds no contract.
- **Q-SPEC-PO-B** (home of REQ-HARN-PIPELINEOBSERVABILITY-004): **`harness-write-scope.md`**,
  because the void is a consequence of a write-scope finding and the
  requirement asks that spec to walk the chunk-0 sequence; the bound's
  comparand lives in `skills/orchestrate/references/loop-control.md` §1b as the requirements gate
  placed it (Q-REQ-PO-Q), and `harness-loop-control.md` cross-references it
  rather than restating it.
- **Q-SPEC-PO-C** (where the lost-record note lives): inside the OPTIONAL
  `migration` marker as `lost: {<kind>: int}`, admitted only beside `from:
  flat-cg`. A new top-level key would change the `v: 2` key set and make every
  live record `key-missing`; a note outside the record would be unreadable by
  `summarize`.
- **Q-SPEC-PO-D** (tier-section opener form): the count rule matches a
  Markdown heading **or** the bold label form the `review` skill's own template
  uses, both spellings (`Blocking`, `Critical`). The requirement's regex is the
  heading form; a heading-only matcher would never fire on the shipped
  template's shape, which is a silent non-check of the class the rule exists
  for. The requirement's fixtures are unchanged and one bold-label fixture is
  added.
- **Q-SPEC-PO-E** (the `literal-anchor` drift phrase and fences): the
  `FORBIDDEN` scan is raw-line and fence-inclusive today; the row carries a
  per-row visible-lines flag so a fenced anchor raises nothing, as the
  requirement's acceptance demands, and no other row changes behaviour.
- **Q-SPEC-PO-F** (`GROWTH:` line counting): `A`/`D` are `git diff --numstat`
  additions/deletions over the deliverable path between the two rounds' shas,
  fenced lines included — the line is a size, not a comparand, so the visible
  filter is neither needed nor applied.
- **Q-SPEC-PO-G** (Step 4b evidence): **the prose cross-reference table of
  §Cross-spec consistency statement is this stage's XSPEC evidence, in place
  of the type-map extraction.** No amendment carries a typed code block, so
  the extraction reports "no extractable type definitions" for every amended
  spec; recording that alone would read as a clean pass while checking
  nothing, so the shared field names are checked pairwise in prose instead.
- **Q-SPEC-PO-H** (`dead-path-citation` token shape): the token additionally
  holds **no whitespace**. The requirement's token definition would otherwise
  match every backticked command whose last argument is a path (`grep -c
  convention plugins/sdd/agents/chunk-verifier.md`), a class the research's
  path-only measurement never counted; a cited path has no spaces. Tightening,
  not widening — no finding the requirement intends is lost. The authority for
  the text is REQ-GC-PIPELINEOBSERVABILITY-004 **as amended** on 2026-09-22
  (Q-REQ-PO-W): its token definition carries the clause "and no whitespace"
  after its excluded-character list and its acceptance names the fifth and
  sixth fixture cases (a backticked command ending in a path raises nothing;
  the same path cited alone while absent raises one folded warn).
  `drift-sweep.md`'s amendment designs to that requirement text; the
  traceability row is **not** marked `(amended)` — the marker means the
  workstream does not own the id (Q-SPEC-PO-K).
- **Q-SPEC-PO-I** (verdict definitions vs. the tier-count rule): the count
  rule of `harness-return-contract.md` (blocking items > 0 and token ≠
  `REJECT` → `REVIEW: MALFORMED`) made `skills/review/SKILL.md` §Verdict
  definitions' `Approve with fixes` line ("Critical findings exist but are
  bounded. Fix them, then proceed without re-review") unreachable, and the
  skill's instruction is why three reviews of this cycle carried Critical
  findings under `APPROVE_WITH_FIXES`. **The skill text is the side that
  moves**: `Approve with fixes` is re-specified as "No blocking finding;
  Material and minor findings only. Fix them, then proceed without
  re-review." and `Reject` as "Any blocking (Critical) finding. …", matching
  `agents/reviewer.md`'s existing "REJECT — a blocking finding makes the
  artifact unsound"; the reviewer body's `APPROVE_WITH_FIXES` paragraph moves
  the same way. Pinned by skill-lint row p13 (`skill-lint-v5.md`); the
  producer-side acceptance is in `review.md`, the agent-body half in
  `harness-agents.md`. The authority for both text changes is the requirement
  text as amended on 2026-09-22 (Q-REQ-PO-V): REQ-REV-002 requires the
  re-specified §Verdict definitions, and REQ-AGENT-PIPELINEOBSERVABILITY-001 —
  the requirement that governs what the three agent bodies say, where
  REQ-AGENT-MARKETPLACE-002 governs only the frontmatter — requires
  `reviewer.md`'s `APPROVE_WITH_FIXES` paragraph. The count rule itself is
  unchanged. **Wording superseded by the second amendment** (Q-REQ-PO-X): the
  first re-specification left `Approve` and `Approve with fixes` sharing the
  predicate "no blocking finding", so REQ-REV-002 (second note) now fixes all
  three as mutually disjoint predicates over the tier counts — `Approve` =
  "No findings above minor; nothing to apply before the next stage." (0
  critical, 0 material); `Approve with fixes` = "No blocking finding; at least
  one Material finding — fix them, then proceed without re-review." (0
  critical, ≥ 1 material); `Reject` = "Any blocking (Critical) finding. …"
  (≥ 1 critical) — row p13's pattern is `at least one Material finding`, and
  `reviewer.md`'s three paragraphs carry the same three predicates
  (REQ-AGENT-PIPELINEOBSERVABILITY-001 as amended, second note). The side that
  moves is unchanged.
- **Q-SPEC-PO-J** — never allocated: the letter was skipped when the first
  specs pass renumbered this list, no committed or working-tree text ever
  carried it (`git log -S'Q-SPEC-PO-J' -- docs/` is empty), and it is kept as
  a recorded gap rather than renumbering K–R, which the owning specs cite.
- **Q-SPEC-PO-K** (the `(amended)` marker on a new-and-amended own id): the
  marker in `docs/ws/pipeline-observability/traceability.md` and in an
  amendment heading means **"this workstream does not own the id"** — it
  marks the sixteen pre-existing requirements amended in place (fifteen at
  27.3; REQ-LINT-PACKAGING-007 joined at 27.4), never one of the twenty-one ids
  this workstream minted
  (`grep -h '^### REQ-[A-Z]*-PIPELINEOBSERVABILITY-' docs/requirements/*/*.md | wc -l`
  reads 21 on 2026-09-22), however many times that id's text was amended at
  the origin. REQ-GC-PIPELINEOBSERVABILITY-004 and
  REQ-AGENT-PIPELINEOBSERVABILITY-001 are therefore unmarked in the
  traceability file and in the `harness-agents.md` and `drift-sweep.md`
  amendment headings, and the header's "sixteen" stays true. Why: the regenerated aggregate uses the marker to tell
  an amendment row from the owning workstream's row, and an own id has no
  other owner to defer to.
- **Q-SPEC-PO-L** (where a gate-rendering walkthrough is recorded): the three
  criteria that rest on a walkthrough (`harness-loop-control.md` verdict
  sequences, `harness-write-scope.md` chunk-0 sequence,
  `harness-return-contract.md` tier fixtures) name **this cycle's
  `docs/ws/pipeline-observability/verification.md`, section `Gate-rendering
  walkthroughs`**, as the artifact holding the transcript, so each has a
  decidable comparand; they are verify-by-construction criteria whose
  comparand is that transcript (§Where each requirement is designed names the
  three; no count of them is asserted here, Q-SPEC-PO-V). Why not a fixture file: the walkthrough
  is the orchestrator rendering its own gate, which no shipped tool executes.

- **Q-SPEC-PO-M** (where a moved contract lives, and where an amendment's
  acceptance criteria live): **the section of record carries the contract
  under a `[Updated: 2026-09-22]` marker; the spec's own Acceptance Criteria
  section carries the criteria under a dated sub-heading; the
  `## Pipeline-Observability Amendment` section carries only the trigger, the
  list of sections of record, and the why.** Moved text keeps no `###`
  heading of its own (a bold lead-in instead), so the `sed`-range criteria
  that address a section by its heading are not split. REQ-REQ-PIPELINEOBSERVABILITY-001
  owner: `requirements-artifacts.md` (the spec of the corpus's structure), as
  a new §Amendment Landing; `ws-traceability.md` is cross-referenced, not
  amended, because row ownership (REQ-WS-008) is unchanged. Supersedes
  Q-SPEC-PO-A's "a dated amendment section at the end of that spec" as the
  carrier.
- **Q-SPEC-PO-N** (the consumer reads the grammar, not a matcher of its own):
  the tier-section parsing rule of `harness-return-contract.md` §VERDICT
  Token takes the label form, the gloss, the extent and the token line's
  free position from `review.md` §Report Format
  (REQ-REV-PIPELINEOBSERVABILITY-001) and states only the two counts, the
  placeholder normalisation and the pauses (three at 27.2, six at 27.3 —
  see the extension below). **Supersedes Q-SPEC-PO-D**
  (the heading-or-bold-label dual form and both spellings): no tier is ever a
  markdown heading and `Blocking` is retired, so the dual matcher would match
  a shape the grammar forbids. The M-side (`material_items`) is
  consumer-checked (Q-REQ-PO-AJ). Cross-field assertion (d) gains the
  `C = 0 / M ≥ 1 / APPROVE` clause; the `gate.decision` member is `malformed`.
  **Extended at requirements 27.3** (Q-REQ-PO-AK, specs review round 5 M3
  routed to its origin): the pauses are six — the two missing-section pauses
  and four conflict conditions, the last two `0 material under
  APPROVE_WITH_FIXES` and `0 blocking under REJECT` — proven exhaustive by
  the 4×3 case table whose three `legal` cells are (3)'s predicates; fixtures
  F8 and F9 and two further witness greps mirror it; `accept prose manually`
  consumes the verdict the table's row implies; assertion (d) fails on all
  four non-`legal` cell classes. The specs mirror the requirement and add no
  rule of their own.
- **Q-SPEC-PO-O** (`post-manual` footprint and case): the enum member is
  **`POST_MANUAL`** (upper case, beside `REVIEW` in `dispatch.reason`, outside
  the fix-only subset); the gate record's `gate.fix_iteration` **equals** the
  preceding same-stage gate record's value (not a literal 0 — the earlier
  wording of this stage), which is what assertion (c)'s second clause reads;
  `[reason-review]` is untouched. At a per-chunk gate the review carries
  `dispatch.chunk = N`, leaves `gate.redo_count` untouched and does not re-run
  the verifier.
- **Q-SPEC-PO-P** (the voided-re-dispatch bound is per gate at the `REDO_MAX`
  value): `voided_redispatch_count[<gate>]` is counted per gate, capped at the
  integer `REDO_MAX` names in `harness-loop-control.md` §Redo Cap per Chunk —
  the constant's only definition; no requirement establishes it — and never
  shown in `Redo: N of REDO_MAX` (Q-REQ-PO-AI). The first specs pass's
  miscitation of the checkpoint requirement as the cap's is corrected in the
  moved text.
- **Q-SPEC-PO-Q** (no piped grep is a witness of itself): every acceptance
  bullet of this delta that quoted a `sed … | grep -c` form as the witness of
  the `self-matching-grep` rule is rewritten to read the table row it names —
  the piped form is out of scope by Q-REQ-PO-AB, so it could witness nothing.
- **Q-SPEC-PO-R** (the derived module set of Check 3): the set is the script
  paths of commands `CLAUDE.md` quotes or the commit gate's `entry:` values,
  decided by the one command in `chunk-close-review.md` §Checklist; the
  skill-lint rows p11/p12 pin the phrase `script path in a command`, replacing
  `self-test convention` (the earlier pattern pinned a sentence the amended
  requirement withdrew).
- **Q-SPEC-PO-U** (the row-population comparand is derived, and
  `two-root-linter.md` is the sixteenth amended spec): the specs closing
  review's C2 found §6's frozen pin (`42 / 9 / 7 / 14`) failing on the very
  rows this delta lands; its origin was fixed at requirements 27.4
  (Q-REQ-PO-AL) and the spec mirrors it — §6 states its numbers under a dated
  marker as current-at-date (`57` / `15` after the rows), moved by any
  row-adding cycle, and the acceptance is the three-way equality
  (`--print-population` == code tables == §6), failing in a temp copy when any
  one side moves alone. `skill-lint-v5.md` §Self-Test Extension states the
  delta's totals as arithmetic and defers to §6 for the comparand, so the
  harness-p6 "six" stays as history and every hit of `grep -n 'grows by
  exactly' docs/spec/skill-lint-v5.md` reads fifteen (2 hit(s) on
  2026-09-22, every one `fifteen`; one read `fourteen` until the verify-stage
  red round R1 traced the p15 drift to its origin) — one consistent statement. The default taken
  without an operator: the self-test's `pinned = {…}` dict becomes a read of
  §6's numbers rather than a second literal — the alternative, keeping the
  dict and adding §6 as a fourth surface, is exactly the chase the amendment
  removes. `two-root-linter.md` therefore gains its own
  `## Pipeline-Observability Amendment` section and joins the map: every
  "fifteen" count in this file moves to sixteen (amended requirements, amended
  specs), thirty-six rows to thirty-seven, and the derived counts below were
  re-run on 2026-09-22 on the tree carrying the 27.4 row, each by the command
  the criterion names: the criterion-1 parse printed `37 rows, 0 mismatches`;
  the `§Pipeline-Observability Amendment` cell grep printed 0; the
  `## Pipeline-Observability Amendment` heading count printed 16 and the
  `Updated: 2026-09-22` count printed 16 with the map excluded (17
  unexcluded); the added-line anchor grep printed 0 over 17 changed spec
  files; and the back-reference sweep (§Verification → Automated) printed 75.
- **Q-SPEC-PO-V** (every count in this file is derived or commanded): a
  number in this file is one of three kinds and nothing else — **derived**
  from a rule stated beside it (the sweep total, the per-domain sums), or
  **commanded** by a read-only command written next to it whose output on
  2026-09-22 is the number given (the row count 37, the minted count 21, the
  heading counts 16, the parse `37 rows, 0 mismatches`), or a **dated
  historical value** labelled with its tree or requirements version (§Reference
  values recorded, never pinned; the `15` of criterion 1's pre-re-derivation
  tree; the 27.2/27.3 pause counts; §6's pins in `two-root-linter.md`). Why:
  the closing review's Critical was arithmetic that a fix had written by hand
  after the 37th row joined — `72 rather than 36` for a sweep that reads 75
  over 37 — and a stated number cannot be told from a stale one, while a
  command's output can be re-run by the reader. No number in this file is
  asserted without one of the three markers; a count that moves with the
  corpus is written as its command, never as its value alone.
- **Q-SPEC-PO-W** (frozen counts in `requirements-artifacts.md` replaced by
  derived forms after the 27.4 row landed): the pipeline-observability block
  of that spec's §Acceptance Criteria had frozen `36` rows, `9 = 9` files and
  `thirty-six` in prose, written before REQ-LINT-PACKAGING-007 joined the
  workstream's traceability at requirements 27.4 (plan review round 1 M5).
  Each bullet now states its command — the row population is
  `grep -c '^| REQ-' docs/ws/<id>/traceability.md`, the `(amended)` count
  `grep -c '^| REQ-.* (amended)' …`, the file-set equality the two derivation
  commands of REQ-REQ-PIPELINEOBSERVABILITY-001 (d) compared by `diff` — with
  the measured value (37, 16, 10 = 10 on 2026-09-22) labelled as a dated
  observation, never as the criterion's comparand. Why: the same rule as
  Q-SPEC-PO-V applied to the one spec it had not reached — a stated count
  cannot be told from a stale one, and this one went stale within the cycle.
- **Q-SPEC-PO-X** (criterion 2's comparand is derived, not a frozen date):
  the plan's closing review (round 1, C1) found criterion 2 pinning
  `last_updated: 2026-09-22` and two whole-corpus `wc -l` counts as its
  comparand while three plan chunks edit members of the amended set during
  implement — `two-root-linter.md` §6, the repaired self-matching lines, the
  carried notes — each bumping `last_updated` past the pin. Criterion 2 now
  derives its spec set from the traceability `Spec` cells by command, checks
  (a) `Approved`, (b) the amendment heading, (c) a dated marker in a section
  of record (the per-file check of `requirements-artifacts.md` §Amendment
  Landing (b), carried by reference), and (d) `last_updated` on or after the
  latest marker, printing `<N> specs, 0 failures`; the old counts stay as
  dated observations beside their commands. Implement-stage edits bump
  `last_updated` and add no new dated marker unless they land a new contract.
  Why (d) is `>=` and not `==`: an edit that only bumps the date must keep the
  criterion true, and an edit that lands a new contract adds a newer marker
  the bump must still cover — the same rule as Q-SPEC-PO-V and -W applied to
  the last frozen comparand in this file.

### Reference values recorded, never pinned

36 migrated / 17 lost consumer-geometry records; 77 packaging records; 69
`literal-anchor` findings in 7 files; 4 self-matching greps; 30 bare / 94
prefixed `Q-IMPL` definitions — all measured on 2026-09-22 and all derived at
run time by the criteria that mention them. The Q3 replay round counts are
criteria nowhere (Q-REQ-PO-M).

## Verification

### Automated

Every mechanical criterion lives in the owning spec's own Acceptance Criteria
section under the date 2026-09-22; this file adds none. The corpus-level checks that decide this stage are:

- `python3 plugins/sdd/tools/skill-lint.py` exits 0 (the two landed rows and
  the landed `FORBIDDEN` phrase present).
- `python3 plugins/sdd/tools/gc.py --report` exits `OK` (no `xlink-dead`,
  `id-missing` or `spec-approval` finding on the amended set).
- A requirement→spec coverage sweep that counts `requires:` back-references
  over `docs/spec/*.md` for this map's ids has a **derived** total, not a
  stated one: at least 2 per id (its owning spec plus this map's frontmatter),
  3 for any id two owning specs share — so a total above the row count is the
  double count, not a coverage defect, and the coverage question is decided by
  the criterion-1 parse below (owning spec ≠ this map), not by the sweep. The
  command that computes it, run from the repo root, parses each spec's
  frontmatter (the text between its first two `---` lines) and counts every
  whole-word occurrence of each id listed in this map's `requires:`:

  ```python
  import re,glob
  fm=lambda t:t.split('---',2)[1]
  ids=re.findall(r'^\s*-\s+(REQ-\S+)',fm(open('docs/spec/pipeline-observability.md').read()),re.M)
  n={i:sum(len(re.findall(r'\b'+re.escape(i)+r'\b',fm(open(f).read()))) for f in glob.glob('docs/spec/*.md')) for i in ids}
  print(len(ids),'ids',sum(n.values()),'refs',{i:c for i,c in n.items() if c!=2})
  ```

  Its output on 2026-09-22 is
  `37 ids 75 refs {'REQ-LINT-PIPELINEOBSERVABILITY-001': 3}` — 2 × 37 plus
  the one id two owning specs share (`skill-lint-v5.md` and
  `two-root-linter.md` both require it, Q-SPEC-PO-U), which is the derivation
  above with the corpus's numbers put in (Q-SPEC-PO-V).

### Acceptance Criteria

- [ ] Every row of `docs/ws/pipeline-observability/traceability.md` has a
  non-empty `Spec` cell naming a section of record of a spec other than this
  map whose `requires:` lists that row's id —
  `grep -c '| [a-z0-9-]*\.md §Pipeline-Observability Amendment |' docs/ws/pipeline-observability/traceability.md`
  reads 0 over all thirty-seven rows, amended and new alike (15 on the
  pre-re-derivation tree of 2026-09-22 (round 4); 0 on the current tree,
  measured with the command above; REQ-REQ-PIPELINEOBSERVABILITY-001 (b)) — and the load-bearing half is decided by one parse of the two files,
  run from the repo root, whose expected output is `37 rows, 0 mismatches`
  (measured exactly that on 2026-09-22, after the REQ-LINT-PACKAGING-007 row
  joined at 27.4):

  ```python
  import re
  rows=[m.groups() for m in re.finditer(r'^\| (REQ-\S+)[^|]*\| ([a-z0-9-]+\.md) §(.+?) \|', open('docs/ws/pipeline-observability/traceability.md').read(), re.M)]
  bad=[]
  for rid,f,sec in rows:
      t=open('docs/spec/'+f).read(); fm=t.split('---')[1]
      ok=any(h.startswith(sec) for h in re.findall(r'^#{2,3} (.+)$',t,re.M)) and rid in fm and f!='pipeline-observability.md'
      if not ok: bad.append((rid,f,sec))
  print(f'{len(rows)} rows, {len(bad)} mismatches', bad or '')
  ```

  A `Spec` cell matches a heading by **prefix** (`## `/`### ` text begins with
  the cell's section text) because headings of record carry a trailing
  requirement list — `### VERDICT Token (REQ-HARN-013)` — that the cell omits.
- [ ] Every spec named in a `Spec` cell of
  `docs/ws/pipeline-observability/traceability.md` — the set is **derived**
  by command, never stated as a list:
  `awk -F'|' '/^\| REQ-/{print $3}' docs/ws/pipeline-observability/traceability.md | sed 's/ §.*//' | tr -d ' ' | sort -u`
  (16 files on 2026-09-22, `two-root-linter.md` the sixteenth, Q-SPEC-PO-U) —
  satisfies four checks: (a) `status: Approved`; (b) a
  `## Pipeline-Observability Amendment` heading exists; (c) at least one dated
  marker `[Updated: YYYY-MM-DD]` (or `**Amended YYYY-MM-DD**`) exists in a
  section of record; (d) the frontmatter `last_updated` is **on or after** the
  latest such marker's date. Decided by one parse, run from the repo root,
  whose expected output is `<N> specs, 0 failures` with `<N>` the size of the
  derived set (measured `16 specs, 0 failures` on 2026-09-22):

  ```python
  import re
  specs=sorted({m.group(1) for m in re.finditer(r'^\| REQ-[^|]*\| ([a-z0-9-]+\.md) §', open('docs/ws/pipeline-observability/traceability.md').read(), re.M)})
  bad=[]
  for f in specs:
      t=open('docs/spec/'+f).read(); fm=t.split('---')[1]
      lu=re.search(r'^last_updated:\s*(\S+)',fm,re.M)
      dates=[a or b for a,b in re.findall(r'\[Updated: (\d{4}-\d{2}-\d{2})\]|\*\*Amended (\d{4}-\d{2}-\d{2})\*\*',t)]
      ok=(re.search(r'^status:\s*Approved',fm,re.M) and re.search(r'^## Pipeline-Observability Amendment',t,re.M)
          and dates and lu and lu.group(1)>=max(dates))
      if not ok: bad.append(f)
  print(f'{len(specs)} specs, {len(bad)} failures', bad or '')
  ```

  Check (c) is the per-file dated-marker check of `requirements-artifacts.md`
  §Amendment Landing (b), carried here by reference so one verify task runs
  both with this loop. No date is the comparand: implement-stage edits to
  these specs **bump `last_updated`** and add **no new dated marker** unless
  they land a new contract, and (d) stays true under every such bump — the
  frozen `last_updated: 2026-09-22` the earlier form pinned was the
  snapshot-comparand class this cycle exists to close (Q-SPEC-PO-X). The two
  whole-corpus counts are dated observations beside their commands, never the
  criterion: `grep -l '^## Pipeline-Observability Amendment' docs/spec/*.md | wc -l`
  read 16 on 2026-09-22 (this map file has no such heading) and
  `find docs/spec -type f ! -path docs/spec/pipeline-observability.md -exec grep -l 'Updated: 2026-09-22' {} + | wc -l`
  read 16 on the same day — the map is excluded by path, the form Q-REQ-PO-AN
  fixes, because its own prose quotes the marker (the unexcluded count read
  17, one being this file).
- [ ] No amendment section and no moved section-of-record text cites a `.md`
  line-number anchor as a comparand — the amendments **added** none, decided
  from the diff rather than from three checkouts:
  `git diff $(git merge-base HEAD main) -- docs/spec | grep '^+[^+]' | cut -c2- | awk '/^\`\`\`/{f=!f;next} !f' | grep -cE '[a-z0-9_-]+\.md:[0-9]+'`
  reads 0 (added lines only, fenced added lines dropped; measured 0 on
  2026-09-22 over 17 changed files, re-run after `two-root-linter.md` joined
  the amended set — it was already in the branch diff from the research-gate
  routing landing, so the file count did not move). The standing floor is earlier cycles'
  text (69 `literal-anchor` findings in 7 files on 2026-09-22, a reference
  value, never a pin) and is the landed rule's business, not this
  criterion's.
- [ ] The sha half of the same rule: no visible line of the sixteen
  `## Pipeline-Observability Amendment` sections (each read from its heading
  to the end of its file through the fence filter) nor of the text marked
  `[Updated: 2026-09-22]` in their sections of record holds a 7-to-40-hex-digit
  token matching `\b[0-9a-f]{7,40}\b`, except inside a `git show
  <sha_N>:<file>` / `<sha>` placeholder form — a per-section scan, so this
  file's own criterion line is outside its scope. The scan, written out
  (Chunk 4 task 6 (ii); both loops read 0 on 2026-09-22, a measurement, not
  a pin) — the amendment sections, heading to end of file:

  ```bash
  for f in $(grep -l '^## Pipeline-Observability Amendment' docs/spec/*.md); do
    sed -n '/^## Pipeline-Observability Amendment/,$p' "$f" \
      | awk '/^```/{f=!f;next} !f' \
      | sed -E 's/git show <sha_N>:<file>//g; s/<sha>//g' \
      | grep -nE '\b[0-9a-f]{7,40}\b' | sed "s|^|$f amendment line |"
  done | wc -l    # reads 0
  ```

  and the marked text of the sections of record — every blank-line-delimited
  paragraph carrying the marker, so the older prose of the same section stays
  outside the scan:

  ```bash
  for f in $(grep -lF '[Updated: 2026-09-22]' docs/spec/*.md); do
    awk 'BEGIN{RS=""; ORS="\n\n"} /^```/{next} index($0, "[Updated: 2026-09-22]")' "$f" \
      | awk '/^```/{f=!f;next} !f' \
      | sed -E 's/git show <sha_N>:<file>//g; s/<sha>//g' \
      | grep -nE '\b[0-9a-f]{7,40}\b' | sed "s|^|$f marked paragraph line |"
  done | wc -l    # reads 0
  ```

## Open Questions

- **`PreToolUse` hook enforcement of read-only leaves** — OPEN, a plan-time
  spike (one live dispatch with a logging hook decides whether hook input
  carries the subagent type; RS-PIPELINEOBSERVABILITY-001 §Q2, Q-REQ-PO-O).
  Not a spec contract; the git-state sentence and the void rule are the
  contract until it is decided.
- The unquoted-pattern form of `self-matching-grep`, `docs/ws/**` /
  `docs/research/**` as lint scope, and a folded `info` per research spike stay
  out (requirements §Open Questions; default no).
