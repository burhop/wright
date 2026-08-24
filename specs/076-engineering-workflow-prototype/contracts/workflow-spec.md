# Contract: Wright Engineering Workflow Specification

## Boundary

This contract defines the canonical prototype workflow exchanged between domain logic, UI components, canvas adapters, fixtures, and LLM proposal validation. It is not Rivet state and is not an MCP execution plan.

## Version and compatibility

- Every document has `schemaVersion`, `workflowId`, and integer `revision`.
- Readers reject unknown major versions and return structured path/code/message errors.
- Additive optional fields may be accepted within a prototype minor version.
- Vendor-native node, edge, socket, engine, or serialization objects are prohibited.
- Layout hints may be separated from semantic content, but both must be validated when present.

## Required document shape

```json
{
  "schemaVersion": "0.1",
  "workflowId": "drill-bit-holder",
  "revision": 1,
  "title": "Design and source a sheet-metal drill-bit holder",
  "purpose": "Produce a verified, quotable design package",
  "phases": [],
  "blocks": [],
  "connections": [],
  "metadata": {}
}
```

Normative entity definitions and invariants are in `../data-model.md`.

## Validation result

Validation returns one of:

```ts
type ParseResult =
  | { ok: true; value: Workflow }
  | {
      ok: false;
      errors: Array<{ path: string; code: string; message: string }>;
    };
```

Validation must cover referential integrity, unique IDs/order, port direction and multiplicity, connection compatibility, feedback semantics, role/config compatibility, finite layout values, and exact MCP binding completeness.

## Projection rule

A canvas adapter receives a frozen/readonly workflow and returns a disposable projection. Candidate IDs may exist only inside the adapter. All interactions are translated to Wright commands before they leave the adapter.

## Reference fixture

Every candidate renders the same fixture containing:

- configurable phases Define, Verify, and Manufacture;
- image and context inputs;
- a reviewable design specification artifact;
- an MCP-bound model-creation action and review gate;
- a generic export artifact;
- an MCP-bound analysis action with test instructions and a feedback connection;
- fabrication package/quote request, approval, and notification blocks.

The fixture may label example artifacts STEP, DXF, drawing, or analysis report. These are data values and media types, not special runtime classes.

## Acceptance examples

- Renaming Verify to Validate changes only the phase label and semantic diff.
- Moving a block between phases changes `phaseId` and optionally position; it does not change role or MCP binding.
- Binding a tool requires an exact catalog identity/schema. Typing “CAD tool” does not constitute a valid binding.
- A feedback edge is visually distinct and explicitly has `semantics: "feedback"`.
