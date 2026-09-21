---
status: Approved
last_updated: 2026-05-25
requires:
  - REQ-XSPEC-001
  - REQ-XSPEC-002
  - REQ-SKILL-013
---

# Cross-Spec Consistency

## Context

Specs are written one at a time and reviewed individually. When one spec
references a type defined in another spec, nothing validates that the
reference matches the definition. In the rubric M1 cycle, SPEC-RECON said
"match by `contract_id`" but SPEC-LOG's `PositionSnapshot` type didn't
include a `contract_id` field. Both specs were Approved. The inconsistency
wasn't caught until implementation, when it caused a chunk rework.

This spec defines a lightweight reading pass that `sdd-specs` performs after
all specs are written, catching cross-spec type reference mismatches before
they reach the plan.

## Design

### When the Pass Runs

The cross-spec reading pass runs in `sdd-specs` after all specs are written
and before the final coverage check (Step 5). Specifically:

```
Step 3: Write specs (one at a time, each reviewed)
Step 3b: Update traceability
Step 4: Review cycle (each spec individually)
    ↓
NEW: Cross-spec consistency pass
    ↓
Step 5: Coverage check
```

**Why after individual review**: Individual spec review validates internal
coherence. Cross-spec review validates external coherence — references
between specs. Running it after all specs are individually approved ensures
the pass operates on stable content.

**Why before coverage check**: The coverage check is the final gate before
declaring specs complete. Cross-spec issues should be resolved before that
gate.

### Identifying Cross-Spec References

A cross-spec type reference occurs when a spec mentions a type name that is
defined in a different spec. The reading pass identifies these by:

1. **Extract type definitions**: For each spec, scan markdown code blocks
   (fenced with `` ``` ``) for type definitions:
   - Class declarations: `class Foo` or `class Foo(Base)`
   - Enum declarations: `class Foo(Enum)` or `class Foo(StrEnum)`
   - Type alias patterns: `Foo: TypeAlias = Bar` or `Foo = NewType("Foo", Bar)`

2. **Build a type-to-spec map**: `{TypeName: spec-file.md}` across all
   specs. Flag duplicates (same type defined in multiple specs) as findings.

3. **Scan for references**: For each spec, search prose and code blocks for
   type names defined in other specs. A reference is any mention of the
   type name outside its defining spec.

**What counts as a reference**: The type name appearing in prose (e.g.,
"takes a `PositionSnapshot` as input") or in a code block (e.g., a field
typed as `PositionSnapshot`). Exact string matching on the type name is
sufficient — these are defined types with distinct CamelCase names, not
common words.

**What doesn't count**: References to requirement IDs (`REQ-AUTH-001`),
spec filenames (`see auth-flow.md`), or prose descriptions that happen to
match a type name in lowercase.

### Validation

For each cross-spec reference, the pass checks:

1. **Type exists**: The referenced type is actually defined (has a class
   body with fields) in the target spec. If the reference names a type
   that doesn't exist in any spec → finding.

2. **Expected fields present**: If the referencing spec mentions specific
   fields of the type (e.g., "the `contract_id` field of
   `PositionSnapshot`"), verify that the defining spec's type definition
   includes that field. Missing fields → finding.

3. **Field name consistency**: If both specs define the same conceptual
   field, verify the names match. For example, if spec A calls it
   `contract_id` and spec B calls it `instrument_id` but they refer to the
   same thing → finding.

### Findings

Each finding includes:
- The referencing spec and the specific reference location
- The target spec and the type definition
- What's missing or inconsistent

**Severity**: All findings are flagged to the operator. There is no
auto-fix. Cross-spec mismatches typically have multiple valid resolutions:
the referencing spec might be wrong, the defining spec might be incomplete,
or the types might need restructuring. Operator judgment is required.

**Presentation**: Findings are listed inline after the pass completes,
before the coverage check. The operator resolves each finding by editing
the relevant spec(s) and re-running the pass until clean.

### Scope Limitations

The reading pass is lightweight by design:

- **Type names only**: It validates that referenced types exist and have
  expected fields. It does not validate semantic meaning (e.g., whether
  `contract_id` in spec A means the same thing as `contract_id` in spec B).
- **Code blocks only**: Type definitions are extracted from fenced code
  blocks, not prose. If a spec describes a type only in prose without a
  code block definition, it won't be picked up.
- **No transitive checking**: If spec A references a type from spec B, and
  that type references a type from spec C, only the A→B reference is
  validated in spec A's context. The B→C reference is validated when
  processing spec B.

**Why these limits**: Full semantic analysis of spec prose is beyond what a
skill instruction can reliably accomplish. The grep-level type/field check
catches the most common failure mode (the rubric M1 `contract_id` case)
without requiring deep reading comprehension from the AI.

### Integration with specs

The cross-spec pass becomes a new sub-step in `sdd-specs`, inserted between
the review cycle (Step 4) and the coverage check (Step 5). The skill
instructions must:

1. Define when to run the pass (after all specs individually approved)
2. Describe how to extract type definitions from code blocks
3. Describe how to identify cross-spec references
4. Describe the validation checks
5. Specify that findings are flag-only with no auto-fix
6. Instruct the operator to resolve findings before proceeding to Step 5

## Verification

### Automated
- Verify `sdd-specs` SKILL.md contains the cross-spec consistency pass
- Verify the pass is positioned after individual review, before coverage
- Verify findings are described as flag-only (no auto-fix)

### Manual
- Write two specs where spec A references a type from spec B
- Omit a field from spec B's type definition that spec A expects
- Run `sdd-specs`; verify the pass flags the missing field
- Resolve the finding; verify the pass runs clean on re-check
- Write a spec with no cross-spec references; verify the pass completes
  with no findings

### Acceptance Criteria
- [ ] Reading pass identifies cross-spec type references (REQ-XSPEC-001)
- [ ] Pass runs after individual spec review, before coverage check (REQ-XSPEC-001)
- [ ] Reference validation checks type existence and field presence (REQ-XSPEC-002)
- [ ] Mismatches flagged to operator, no auto-fix (REQ-XSPEC-002)
- [ ] `sdd-specs` SKILL.md includes the cross-spec pass (REQ-SKILL-013)
