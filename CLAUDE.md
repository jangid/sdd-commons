# Tools, Skills & Agents

A curated collection of reusable tools, skills, and agents for AI-assisted workflows.

## Repository Structure

```
tools/    — Standalone utilities and helper scripts
skills/   — Composable skill definitions (Claude Code SKILL.md format)
agents/   — Agent configurations and prompt templates
```

## Conventions

### Skills (`skills/`)

Each skill lives in its own directory with a `SKILL.md` file:

```
skills/<skill-name>/SKILL.md
```

- **Frontmatter** is required: `name`, `description` (YAML `---` block)
- `name` must match the directory name
- `description` is a concise sentence used for skill discovery — be specific about when to use vs. when to skip
- Body defines the skill's instructions, process, and rules
- Skills describe workflows, not implementation code
- Keep each SKILL.md cohesive; move bulky detail to a `references/` file (loaded on demand) rather than growing the body — size is a soft signal, not a hard limit

### Agents (`agents/`)

Each agent is a single Markdown file:

```
agents/<agent-name>.md
```

- **Frontmatter** fields: `name`, `description`, `tools`, `model`, `color`, `emoji`, `vibe`
- `tools` lists the Claude Code tools the agent may use (e.g., `Read, Bash, Grep, Glob`)
- `model` specifies the preferred model tier (`opus`, `sonnet`, `haiku`)
- Body defines the agent's identity, phases, checklists, and report templates
- Agents are adversarial or specialized personas — they should be opinionated and thorough

### Tools (`tools/`)

Standalone scripts or utilities. Use the appropriate language for the task. Each tool should:

- Be self-contained (minimal dependencies)
- Include a usage comment or `--help` flag
- Follow the code style conventions from the user's global CLAUDE.md

## Adding New Content

### New Skill

1. Create `skills/<name>/SKILL.md` with frontmatter and body
2. Test the skill by invoking it in a Claude Code session
3. Commit with: `feat(skills): add <name>`

### New Agent

1. Create `agents/<name>.md` with frontmatter and body
2. Verify the agent can be loaded as a subagent type
3. Commit with: `feat(agents): add <name>`

### New Tool

1. Create the script in `tools/`
2. Ensure it runs standalone
3. Commit with: `feat(tools): add <name>`

## Quality Checks

- All Markdown files should be well-formed (no broken frontmatter)
- Skill and agent names use kebab-case
- No orphaned files — every skill directory has a SKILL.md, every agent file has frontmatter
- Descriptions must be actionable: state when to use AND when not to use
- Prose describing **another** repository's artifacts (a toy clone, an evidence
  record, a pilot log) must not quote that repository's `Q-IMPL` id tokens
  verbatim — paraphrase them or wrap them in a fenced code block, which
  `tools/sdd-gc.py`'s `qimpl-undefined` sweep already skips (the rule itself is
  unchanged; there is no allowlist)
- Run `tools/sdd-skill-lint.py` after editing any skill — it enforces the checks
  above plus cross-skill contract markers and known drift phrases (exit 0 = clean)

## Spec-Driven Development (SDD)

A cyclic, phase-based workflow for building software with AI assistance. Each phase produces artifacts on disk that serve as state markers — any new session can detect the current phase and resume.

### Phases (9 skills)

```
┌─ RESEARCH ──→ REQUIREMENTS ──→ SPECS ──→ PLAN ──→ IMPLEMENT ──→ VERIFY ─┐
│      ↑              ↑            ↑         ↑          │           │      │
│      └──────────────┴────────────┴─────────┴── REPLAN ←───────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
                              ↕ REVIEW (cross-cutting, out-of-session)
```

1. `sdd-research` — time-boxed exploration to reduce uncertainty (`docs/research/RS-NNN-{topic}/`)
2. `sdd-requirements` — elicit and document requirements (`docs/requirements/`)
3. `sdd-specs` — translate requirements into design specs (`docs/spec/`)
4. `sdd-plan` — break specs into ordered, typed tasks (implement/spike/verify)
5. `sdd-implement` — execute the plan with TDD inner loop and stuck detection
6. `sdd-verify` — holistic validation: quality gates + acceptance criteria + UX
7. `sdd-replan` — structured replanning when assumptions break
8. `sdd-migrate` — one-time migration between artifact structure versions
9. `sdd-review` — structured external review in a separate session at phase boundaries (cross-cutting, not sequential)

### Driver (`sdd-orchestrate`)

`sdd-orchestrate` is a **driver**, not a tenth phase skill. It runs the nine
skills above as a single-operator loop — DISCUSS → KICKOFF → LOOP → DONE — where
each pipeline stage and each `sdd-review` run as **separate, context-isolated
subagents** and the operator gates after every stage (proceed │ loop-back-to-fix
│ stop). It introduces one new artifact, `docs/handoff/kickoff.md`; reviews stay
ephemeral. v1 is research-entry and sequential (no mid-pipeline entry, no
parallel fan-out). Under marker `4` it opens with a **workstream picker**
(select-or-create a workstream, every new one entering at research) and its
implement-stage fan-out branches from the workstream branch — see
[Multi-Workstream Layout (v4)](#multi-workstream-layout-v4). Use it to run a whole
SDD cycle end-to-end with built-in external review; invoke an individual `sdd-*`
skill directly for a single phase.

**Gate vocabulary (v5 harness hardening).** Every dispatched leaf ends with a
structured `RETURN:` block (`status: COMPLETE | PARTIAL | BLOCKED |
BUDGET_EXHAUSTED`, `budget_consumed` against the dispatched `Budget:`). At the
implement stage each chunk is dispatched separately and closes at a **per-chunk
gate** (`proceed │ fix │ stop`) showing, in order, `RETURN.status`, the
write-scope check `SCOPE: CLEAN | VIOLATION`, and the fresh read-only chunk
verifier's `CHUNK_VERDICT: PASS | FAIL`, with `Redo: N of REDO_MAX`. After all
chunks (and after every non-implement stage) the **stage gate**
(`proceed │ loop-back-to-fix │ stop`) shows the review's own-line `VERDICT:`
token and, when a loop is active, `iteration N of FIX_LOOP_MAX` or the derived
replan re-entry count against `REPLAN_MAX`. All three caps default to 3
(`FIX_LOOP_MAX`, `REPLAN_MAX`, `REDO_MAX`). After `proceed` the orchestrator's own
commit is checked against the leaf's observed writes and closes the same gate
with `COMMIT: COMPLETE (N paths) | INCOMPLETE (…)` — `INCOMPLETE` pauses with
`amend │ accept (note) │ stop` before any next dispatch (harness-p4;
`skills/sdd-orchestrate/references/write-scope.md` §7a). The no-new-artifact
invariant holds:
counters are session-scoped or derived, reviews stay ephemeral, and the only
durable trace is the bounded circuit-break checkpoint in the plan's existing
blocked-task note.

**Cycle signals (v5 part 2 — harness-p2).** After every gate the driver appends
one record — counts, enums, shas, timestamps, never finding text — to
`.sdd/telemetry.jsonl` (gitignored, orchestrator-only, never read by phase
detection; default on, opt-out at KICKOFF; `TELEMETRY: rec <n> | WRITE FAILED | OFF |
.gitignore updated` are its only gate lines — four members, `rec <n>` the
positive one; post-cycle reader `python3
tools/telemetry.py summarize`). At the verify stage the operator may opt in
to a **red team** (`red team: off | on`, default off): one read-only leaf attacks
the weakest acceptance criteria and ends with `RED_VERDICT: BROKEN | HELD`;
`sdd-verify` then writes `status: pending-red` and `proceed` is withheld until
every `BROKEN` `Rn` is fixed (`RED_BREAK` packet) or accepted (recorded under
§Issues Found → Minor), after which the gate flips `pending-red → pass`. Inside a
fix loop a later review round that raises new ground, or regresses without it,
pauses the stage gate as `REVIEW: CONTRADICTION (round N vs round N+1, class
b|c)` with `accept round N+1 (fix) | accept round N (proceed, note) | third
opinion (re-dispatch review) | stop`. `python3 tools/gc.py --report` sweeps
the docs corpus at entry (one informational `GC:` line) and at DONE (findings
routed `--fix <rule>` │ `record | ignore` │ note; `record` appends to
`verification.md` `## Next Steps`); gc never runs between stages, never blocks a
gate and never touches a plan task.

**Harness hardening, part 3 (harness-p3).** The write-scope observation is a
**content** decision: a path already dirty when the snapshot was taken and
re-touched by a leaf is observed (`git hash-object` per path in the ambiguous
set), so paths cancel only when their content hash is unchanged too. Every
dispatch template pins its leaf's `RETURN:` block verbatim, and a
`BUDGET_EXHAUSTED` return pauses the gate with `budget_consumed` rather than
reading as progress. Arbitration counts a **regenerated** artifact as written by
the fix loop, so a finding in a wholesale-regenerated file is not a class (b)
`REVIEW: CONTRADICTION`, while a file the loop left alone still pauses. The
`TELEMETRY:` family gains its positive member — `TELEMETRY: rec <n>`, `<n>`
counting successful appends this session — so a gate that claims telemetry is on
now shows that the append happened. A completion signal (`verification.md`
`status: pass`, or a fully-checked plan) counts for **this** cycle only when its
frontmatter `research_id:` string-equals the kickoff's; a mismatch or an absent
field reads as a previous cycle's artifact. At the verify gate a red round
N >= 2 renders one derived `RED: Rn new-ground | regression` line per `BROKEN`
`Rn`, from a re-run of the previous round's `reproduce:` command, and the
`Verified` column reads `pending-red` until the `pending-red → pass` flip at
DONE. The canonical gate signal order lives in
`skills/sdd-orchestrate/references/loop-control.md` §5; `SKILL.md` §The gate is
its non-divergent summary.

### Phase Detection

Every skill checks `docs/.sdd-version` on entry. If missing, it suggests running `sdd-migrate`. `docs/.sdd-version` is the **sole layout gate**: marker `3` (or earlier) selects the flat single-operator layout; marker `4` selects the multi-workstream layout where phase detection is a **function of `(repo, workstream)`** — every skill takes a `workstream` argument (default `default`) and roots execution artifacts at `docs/ws/<id>/` (see [Multi-Workstream Layout (v4)](#multi-workstream-layout-v4)). Both markers are supported; this repo migrated to marker `4` on 2026-09-17 (solo work runs in the implicit `default` workstream).

Skills then detect the current phase by checking which artifacts exist **and whether they are stale**. Execution-artifact paths depend on the marker — under marker `3` they are the flat paths below; under marker `4` the same artifacts live at `docs/ws/<id>/` (the shared corpus — `research/`, `requirements/`, `spec/` — stays at top level under both markers):

| Artifact (marker `3` flat / marker `4` per-ws) | Phase complete |
|----------|---------------|
| `docs/research/RS-*/findings.md` (status: Complete) — shared | Research done |
| `docs/requirements/index.md` (status: Approved) — shared | Requirements done |
| `docs/spec/*.md` (all status: Approved) — shared | Specs done |
| `docs/plan.md` → `docs/ws/<id>/plan.md` (exists, tasks incomplete) | Planning done, implementing |
| `docs/plan.md` → `docs/ws/<id>/plan.md` (`status: complete`, all tasks done, **`research_id` matches the kickoff's — when a kickoff with one exists**) | Implementation done |
| `docs/verification.md` → `docs/ws/<id>/verification.md` (status: pass, **`research_id` matches the kickoff's — when a kickoff with one exists**) | Verified, ready to ship |
| `docs/verification.md` → `docs/ws/<id>/verification.md` (status: fail) | Needs replan |

Under marker `4`, phase is resolved **per workstream** — two workstreams in the same repo can sit at different phases simultaneously. A skill under marker `3` never reads `docs/ws/`; a skill under marker `4` never reads flat `docs/plan.md` / `docs/verification.md`.

**Cycle identity.** The two **completion-signal** rows above carry a second condition: the artifact's frontmatter `research_id:` must equal the kickoff's (`docs/ws/<id>/kickoff.md` under marker `4`, `docs/handoff/kickoff.md` under marker `3`), compared by **exact string equality** on the trimmed value. Three exhaustive cases: (1) **mismatch** → a previous cycle's artifact, the stage has not been reached in this cycle; (2) **field absent** while the kickoff has one (legacy — existing files are never back-filled) → read as a mismatch, the safe direction; (3) **no usable discriminator** (no kickoff, **or** a kickoff carrying no `research_id`) → the comparison is **skipped entirely** and the `status:`-only rule applies unchanged, so a repo that never ran the orchestrator still reads its `status: pass` report as verified. `sdd-plan` and `sdd-verify` write the stamp, copied verbatim from the kickoff; the shared corpus (`docs/requirements/**`, `docs/spec/**`) is never stamped, because `status: Approved` there is product-wide, not per-cycle. See `docs/spec/cycle-identity.md`.

#### Staleness Detection

Downstream artifacts become stale when their upstream inputs are updated. Each skill compares `last_updated` dates across the dependency chain, using `docs/requirements/index.md` as the single staleness reference for requirements:

```
research/index.md → requirements/index.md → specs → plan → implementation → verification
```

If a downstream artifact's `last_updated` is older than its upstream input, it is **stale** and needs updating — not skipping to. For example, if `requirements/index.md` was updated today but `docs/spec/*.md` and `docs/plan.md` are from last week, `sdd-specs` will update the specs rather than redirecting to `sdd-implement`. Early-phase skills (research, requirements) are always valid entry points — they note existing downstream artifacts but don't block on them.

Under marker `4`, staleness is **workstream-scoped**: the plan path is `docs/ws/<id>/plan.md` and the scope is computed **live** from that workstream's plan (walk each task's `traces to` spec → the spec's `requires:` requirement IDs → those requirements' category-file dates). A shared spec or requirement that **no task in `<id>`'s plan traces** does not make that workstream stale — a change in one workstream's traced inputs never falsely flags another. Requirements-corpus staleness (research → requirements) stays shared and workstream-independent. No staleness path reads any traceability file. See `ws-staleness.md`.

#### Plan Archival

When `sdd-plan` rewrites a plan or `sdd-replan` makes significant changes, the previous plan is archived to `docs/plan-history/{date}-{reason}.md` (under marker `4`: `docs/ws/<id>/plan-history/{date}-{reason}.md` — archival is scoped to the active workstream and never touches another workstream's history). The active plan stays lean — completed milestones are summarized to one line each. Changelogs and removed tasks live only in archive files.

### Multi-Workstream Layout (v4)

v4 lets a team run several SDD cycles concurrently in one repo — **one branch/issue per workstream** — without artifact collisions, false staleness, ID races, or cross-workstream phase confusion, while keeping requirements/specs/research/traceability a single shared corpus and keeping solo use ceremony-free. `docs/.sdd-version` = `4` is the sole gate that flips every skill to this layout; marker `3` (flat) remains fully supported and is what this repo uses today.

**Layout — execution artifacts move, the shared corpus stays.** Under marker `4`:

```
docs/
  .sdd-version          # "4"
  research/             # SHARED corpus (top level, used as-is)
  requirements/         # SHARED corpus — index.md, category files, aggregated traceability.md
  spec/                 # SHARED corpus
  ws/
    <id>/               # one directory per workstream (issue/branch key; solo → "default")
      kickoff.md        # OWNED
      plan.md           # OWNED
      plan-history/     # OWNED
      verification.md   # OWNED
      traceability.md   # OWNED — this workstream's rows only
```

A workstream **owns only** its `kickoff.md`, `plan.md`, `plan-history/`, `verification.md`, and per-ws `traceability.md`. Requirements, specs, research, and the aggregated `docs/requirements/traceability.md` are **shared** — new work only ADDs IDs/files to them; no skill ever creates `docs/ws/<id>/requirements/` or `docs/ws/<id>/spec/`. The shared aggregate traceability is **regenerated** (never hand-merged) from the per-ws files. Solo use runs in an implicit `default` workstream — never name a workstream, and all execution artifacts land under `docs/ws/default/`.

**Workstream lifecycle.** `sdd-orchestrate` opens with a **workstream picker**: it enumerates `docs/ws/<id>/`, shows each workstream's id + description (from its `kickoff.md`) + detected phase, and lets the operator select an existing workstream or create a new one (a `default`-only repo degenerates to a picker of one — no ceremony). Every **new** workstream begins at **research** and seeds `docs/ws/<id>/kickoff.md`, then runs the normal per-workstream research → requirements → specs → plan → implement → verify pipeline. Done-vs-new-cycle is resolved **per workstream** (a workstream whose `verification.md` is `status: pass` offers "start a new cycle in this workstream"; a genuinely new idea mints a new workstream id). Research may **early-exit** when the shared corpus already covers the workstream's needs (recorded as an explicit "covered by shared corpus" finding).

**Approval** is a bare per-scope `status` flag — owned `plan.md`/`verification.md` carry their own status; shared `requirements/*` / `spec/*` carry one product-wide status. No approver identity or quorum.

**Workstream-prefixed IDs.** Under marker `4`, downstream IDs carry a `<WS>` segment before the counter, with a **per-workstream counter** (per `domain+workstream` for requirements): `RS-<WS>-NNN`, `REQ-<DOMAIN>-<WS>-NNN`, `Q-IMPL-<WS>-NNN` (e.g. `RS-ISSUE42-001`, `REQ-AUTH-ISSUE42-001`, `Q-IMPL-ISSUE42-003`). `NNN` is parsed after the `<WS>` token, so two workstreams allocate `RS-ISSUE42-001` / `RS-ISSUE57-001` with no coordination and no collision. Legacy bare v2/v3 ids remain valid and are treated as the `default` workstream (not remapped). Specs stay filename-based (shared). Shared-table writes are merge-safe (ID-sorted insertion / per-ws-owned rows) — never raw EOF append; same-domain concurrent requirement additions are an accepted human PR conflict, not auto-unioned. See `ws-ids.md`.

**Git integration — branch per workstream → PR to `main`.** Each workstream corresponds to its own git branch; isolation comes from git + path scoping, not naming discipline. The workstream branch is the integration unit — a completed workstream merges via **PR to `main`**; concurrent open PRs are supported; `main` is a shared trunk, not a working surface. Orchestrate's implement-stage fan-out branches worktrees from the **workstream branch** (HEAD) and merges back into it, leaving `main` untouched until the PR. `sdd-verify`'s regression base is the workstream branch point — `merge-base(<id>, main)` — so a workstream's verification is unaffected by unrelated workstreams merged to `main` meanwhile. See `ws-integration.md`.

**Migration.** `sdd-migrate` handles the one-time **v3 → v4** flip via copy-verify-flip-cleanup: copy (not move) the flat execution artifacts into `docs/ws/default/`, verify byte-identity, write `.sdd-version` = `4` **last**, then delete the flat originals. The shared corpus is left in place; interrupting before the flip leaves a working v3 repo, after the flip a working v4 repo (both re-runnable idempotently). See `ws-migration.md`. Full v4 contracts: `docs/spec/ws-layout.md`, `ws-ids.md`, `ws-traceability.md`, `ws-staleness.md`, `ws-integration.md`, `ws-migration.md`, `ws-orchestration.md`.

### Key Differences from Linear Waterfall

- **Research phase**: explore before committing (time-boxed spikes)
- **Typed tasks**: implement (code), spike (research), verify (validation)
- **Stuck detection**: if implementation hits a wall, trigger replan instead of spinning
- **Replan triggers**: defined upfront in the plan — conditions that invalidate the approach
- **Holistic verification**: goes beyond "tests pass" to user-perspective validation
- **External review**: `sdd-review` runs in a separate session at phase boundaries to catch coherence gaps and scope omissions that in-session layers miss
- **Four verification layers**: chunk-close (mechanical, per-chunk), XSPEC (structural, during specs), verify (holistic, end-of-project), review (semantic, out-of-session)
- **Cyclic**: replan can route back to any earlier phase based on severity

### When to Use

Use SDD for non-trivial features (multi-file, multi-day, architectural impact). Skip for bug fixes, small tweaks, and well-understood changes.
