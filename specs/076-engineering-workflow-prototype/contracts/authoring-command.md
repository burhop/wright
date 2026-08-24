# Contract: LLM Authoring Proposal

## Boundary

An LLM suggests bounded edits. It cannot mutate application state, emit canvas-library state, execute a workflow, call MCP tools, or approve its own proposal.

## Request

The authoring adapter receives:

- authoring instruction;
- current validated workflow and revision;
- selected blocks/phases, if any;
- compact tool-catalog descriptors only when tool binding is requested;
- the supported command schema and maximum command count.

Secrets, artifact bodies, unneeded evidence, and unrestricted workspace context are excluded.

## Response

```json
{
  "proposalVersion": "0.1",
  "proposalId": "proposal-123",
  "workflowId": "drill-bit-holder",
  "baseRevision": 4,
  "summary": "Add a reviewed analysis loop",
  "assumptions": [],
  "commands": []
}
```

Supported atomic commands:

- `addPhase`, `updatePhase`, `removePhase`, `reorderPhase`;
- `addBlock`, `updateBlock`, `moveBlock`, `removeBlock`;
- `addConnection`, `updateConnection`, `removeConnection`;
- `bindMcpTool`, `clearMcpBinding`, `mapMcpArgument`;
- `setLayoutHint`.

Each command includes a unique command ID, a discriminant, an explicit target, and command-specific values. Unknown commands or fields are rejected.

## Application protocol

1. Parse the response against a strict schema.
2. Confirm workflow ID and base revision.
3. Enforce command-count and payload-size limits.
4. Apply all commands through the manual-edit reducer to an immutable copy.
5. Validate the resulting complete workflow and binding policies.
6. Produce a semantic before/after diff and assumptions/warnings.
7. Require explicit user acceptance before committing the new revision.

Application is all-or-nothing. Rejection, stale revision, invalid command, dangling connection, unreviewed tool identity, or policy failure leaves the accepted workflow unchanged.

## Deterministic conformance set

At least 20 fixtures cover:

- valid single and multi-command edits;
- malformed JSON/shape and unknown commands;
- stale revisions and wrong workflow IDs;
- ID collisions and missing targets;
- dangling or incompatible connections;
- prohibited vendor state and prohibited execute/call intent;
- nonexistent or schema-mismatched MCP bindings;
- partial application attempts;
- maximum command/payload limits.

Target: at least 90% of valid fixture prompts yield a valid proposal on the first deterministic response, and 100% of invalid responses are rejected without mutation.
