# Conformance Kernel Contract

The kernel is pure, deterministic, renderer-neutral, and side-effect free. It is the only path from text or commands to a workflow candidate.

## Operations

```text
parse(text, syntaxVersion)
  -> { ok: true, ir, sourceMap, formattingEnvelope }
  |  { ok: false, diagnostics }

format(ir, syntaxVersion, formattingPolicy)
  -> { text, sourceMap }

validate(ir)
  -> { valid, diagnostics }

apply(ir, commandBatch, currentRevision)
  -> { ok: true, candidate, semanticDiff }
  |  { ok: false, diagnostics }

semanticDiff(before, after)
  -> stable-ID-aware added/removed/changed facts

project(ir, layout, optionalRunProjection)
  -> renderer-neutral canvas projection
```

## Parse and formatting rules

- A parse succeeds only for one complete supported document version.
- Duplicate identities/keys, malformed Unicode, unsupported numeric values, unknown required fields, and trailing unparsed input fail closed.
- Diagnostics include stable code, severity, semantic IDs when known, source span, explanation, and correction.
- The recovery DSL canonical formatter preserves leading standalone comments and semantic IDs but normalizes indentation/order. JSON has no comments. The evaluated YAML parser preserves semantic content but not arbitrary comments or formatting; this limitation must remain visible.
- Source maps bind semantic IDs and significant fields to current formatted spans. A diagnostic retains semantic identity even when a later format changes the span.

## Apply rules

- `commandBatch.base_revision` must equal the current accepted revision.
- Commands are a closed discriminated union and are applied in order to a clone.
- One unsupported, invalid, or stale command rejects the entire batch.
- Validation runs after all commands; no intermediate candidate is accepted.
- `apply` never assigns a new accepted revision or writes storage.
- Manual graph/form, parsed text diff, and AI proposal use the same operation.

## Required invariants

1. `parse(format(ir)).ir` is semantically equal to `ir`.
2. Text edit → parse → project preserves every semantic fact.
3. Graph commands → format → parse preserves every semantic fact.
4. Invalid text returns diagnostics and does not provide a replacement IR.
5. Invalid/stale graph or AI commands preserve the exact last-valid object and revision.
6. Layout-only changes do not change canonical definition bytes or semantic digest.
7. Run projection changes do not change definition or layout bytes.
8. The same base and command batch produce the same candidate and diff.
9. A command accepted once is stale when replayed against the advanced revision.
10. Renderer replacement changes no kernel result.

## Equality

Semantic equality compares canonical definition bytes after excluding digest fields. Array order is semantic where explicitly ordered (phases, command sequence) and canonicalized by stable ID where order is not semantic.

## Error stability

Codes are contract values. Explanations may improve without changing the code. Recovery concept codes use the prefix `WFR-`; production promotion must version any incompatible code change.

