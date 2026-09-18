# RS-HARNESSP4-001 — Evidence appendix

Working material for [`findings.md`](findings.md): probe transcripts and a
fixture cross-check, committed for citability. Observations here are evidence;
nothing here is a contract.

## §A — Probe 1 (Q1): `COMMIT:` comparands in a scratch repository

Run 2026-09-18 with `bash $TMPDIR/rs-p4-probe.sh` against a fresh `git init`
repository under `$TMPDIR/rs-p4-probe/repo`. Nothing in this repository's
working tree or history was touched. Inline `-c user.email/-c user.name`
identity, as `fan-out.md` §2 prescribes for leaves. Verbatim output:

```
=== SEQUENTIAL: leaf writes 3 paths, orchestrator git-adds only 2 (the V14 Chunk 7 case)
observed - committed (INCOMPLETE):
docs/plan.md
committed - observed (inverse error):
porcelain after commit (leftover dirty path):
 M docs/plan.md

=== SEQUENTIAL inverse: orchestrator commits a path no leaf wrote
committed - observed:
stray.txt

=== FAN-OUT A: leaf makes 2 commits on its branch, orchestrator merges (fast-forward)
leaf committed delta (base..tip):
a.txt b.txt
git show --name-only --format= HEAD after FF merge (only the LAST leaf commit):
b.txt
git diff --name-only PRE HEAD after FF merge:
a.txt b.txt

=== FAN-OUT B: true merge commit (integration branch advanced meanwhile)
leaf committed delta (base..tip):
a.txt c.txt
git show --name-only --format= HEAD on the MERGE commit: []
git diff --name-only PRE HEAD: [a.txt c.txt ]
git diff --name-only merge-base(PRE,TIP) TIP (== leaf committed delta): [a.txt c.txt ]

=== FAN-OUT C: conflict -> abort -> redo-by-re-derivation; the redo leaf omits a path the aborted leaf had
merge exit != 0 -> git merge --abort
redo committed delta vs main: [b.txt ]  (first attempt had: a.txt b.txt)
diff PRE HEAD after redo merge: [b.txt ]

=== timing: git diff --name-only over two shas
real    0m0.007s
```

Reading: `git show --name-only --format= HEAD` (V14's proposed comparand)
under-reports on a fast-forward (last leaf commit only) and is empty on a merge
commit; `git diff --name-only <PRE> <HEAD>` equals the leaf's committed delta in
both merge shapes. A clean merge never dropped a path; the only drop
(case C) came from an aborted attempt whose redo — a new dispatch — legitimately
had a different set.

Supporting history read (this repository, read-only):
`git log --oneline 77e84fe..b0b69be | wc -l` = 20 commits for the 8-chunk p3
implement stage — 8 `feat(...)` chunk commits, 8 `docs(traceability):
regenerate aggregate after Chunk N`, plus `fb2afda` (plan), `16e240b` (the V14
fix-up) and `b0b69be` (docs). The regeneration commits are the reason a
`git show HEAD` taken after bookkeeping would name only the aggregate.

## §B — Fixture cross-check (Q2): implied vs recorded dispatches

Read-only pass over `tools/fixtures/telemetry-harness-p3-2026-09-18.jsonl`
(20 records) on 2026-09-18. Output of the inspection script:

```
kinds {'pipeline': 15, 'review': 2, 'red': 2, 'gate': 1}
implement records 9 with chunk_verdict non-null 8
redo values on implement records (seq, redo, reason, gate.redo_count):
  (6, None, None, 0) (7, 1, 'VERIFIER_FAIL', 1) (8, None, None, 0) (9, None, None, 0)
  (10, 1, 'VERIFIER_FAIL', 1) (11, None, None, 0) (12, None, None, 0) (13, 1, 'REVIEW', 1)
  (14, None, None, None)
review_verdict non-null on non-review records:
  (1, pipeline, APPROVE_WITH_FIXES) (2, pipeline, APPROVE_WITH_FIXES) (3, pipeline, APPROVE_WITH_FIXES)
  (4, pipeline, APPROVE_WITH_FIXES) (5, pipeline, APPROVE_WITH_FIXES) (20, gate, APPROVE_WITH_FIXES)
red_verdict non-null on non-red: (20, gate)
loop-back-to-fix / fix_iteration>=1:
  (1, pipeline, loop-back-to-fix, 1) (2, pipeline, proceed, 1) (3, pipeline, proceed, 1)
  (4, pipeline, proceed, 1) (5, pipeline, proceed, 1) (14, review, proceed, 1)
  (17, review, None, 1) (18, pipeline, None, 1) (19, red, None, 1) (20, gate, proceed, 1)
git heads (seq, head_before, head_after):
  (1, 8bdc9b8, None) (2, 8bdc9b8, None) (3, 41b9eaa, 57af095) (4, 3e96101, 77e84fe) (5, None, 'HEAD')
  (6..14, None, None)
  (15..19, b0b69be0c5be814b9d138acdcabec45dbba6359a, same)  (20, b0b69be0c5be…, e1f5985654…)
stages (seq, stage, kind, decision):
  1 research pipeline loop-back-to-fix | 2 research pipeline proceed | 3 requirements pipeline proceed
  4 specs pipeline proceed | 5 plan pipeline proceed | 6-13 implement pipeline proceed
  14 implement review proceed | 15 verify pipeline None | 16 verify red None | 17 verify review None
  18 verify pipeline None | 19 verify red None | 20 verify gate proceed
sha-domain violations: (5, head_after, 'HEAD'); undeclared key git.commit_n on seq 15-20
```

Derived counts used in findings Q2:

| Kind | Implied by fields (formula output) | Recorded | Missing (per stage) |
|---|---|---|---|
| verifier | Σ (1 + redo) over 8 chunk records with `chunk_verdict` = 8 + 3 = 11 | 0 | 11 |
| implement pipeline | Σ (1 + redo) over 8 implement pipeline records = 11 | 8 | 3 |
| review | 6 carrying records (seq 1, 2, 3, 4, 5, 20) | 2 (seq 14 implement, seq 17 verify) | 5 — research×2, requirements, specs, plan; seq 20 covered by seq 17 |
| fix | 1 via `gate.decision: loop-back-to-fix` (seq 1 → seq 2) + 1 via `reason: red_break` (seq 18) = 2 | 0 (both typed `pipeline`) | 0 (2 mis-typed — present as records of another kind, a `--lint` finding, not a missing append) |
| red | 1 carrying record (seq 20) | 2 (seq 16, 19) | 0 |

`expected` = highest seq 20 + Σ missing (11 + 3 + 5 + 0) = 39 dispatches vs 20
records. Recomputed 2026-09-18 after review round 1 (C1: the distinct
`(stage, fix_iteration)` review count gave 4, not the 5 the prose claimed; the
per-carrying-record count is 6, of which 5 are unmatched by any review record).

Domain / key-set violations: `kind: gate` (P3); `head_after: "HEAD"`; null
heads on all implement records; 40-char shas vs "short sha"; undeclared
`git.commit_n`.
