# Contract: Generic MCP Binding and Invocation

## Principle

Wright has one generic MCP binding and invocation path. The prototype must not dispatch by engineering discipline, file format, vendor, or friendly label.

## Catalog dependency

The adapter consumes the existing workspace-scoped catalog representation and normalizes only the fields needed by the workflow editor:

```ts
type CatalogTool = {
  serverId: string;
  toolName: string;
  qualifiedToolName?: string;
  serverRevision?: string;
  title?: string;
  description?: string;
  inputSchema: JsonSchema;
  inputSchemaDigest: string;
  approvalPolicy?: ApprovalPolicyReference;
};
```

Final field mapping must be derived from the existing Wright API and recorded in the checkpoint evidence; this prototype contract does not authorize a parallel catalog endpoint.

## Binding

A valid binding identifies one exact visible catalog tool and the reviewed schema/revision, plus explicit input/output mappings. Friendly aliases are display-only.

Before invocation, the adapter must:

1. re-resolve the exact tool in the current workspace catalog;
2. compare server/tool/revision/schema identity;
3. resolve mapped values from validated literals and upstream ports;
4. validate arguments against the current input schema;
5. present any existing approval requirement;
6. invoke only through Wright's existing governed gateway.

A missing tool or changed schema yields `review-required`. It is never silently rebound by name similarity.

## Normalized result

```ts
type McpStepResult = {
  status:
    | "pending-approval"
    | "running"
    | "succeeded"
    | "failed"
    | "cancelled"
    | "review-required";
  content?: unknown;
  artifacts: ArtifactReference[];
  evidence: EvidenceReference[];
  error?: { code: string; message: string; retryable?: boolean };
};
```

Gateway responses remain the source of truth for approvals, audit identity, evidence, and artifacts. The prototype does not infer successful engineering outcomes from transport success.

## Conformance fixtures

At minimum, test three structurally different tools through identical adapter code:

- a tool with scalar/string inputs and a text result;
- a tool with nested/object or array inputs and an artifact result;
- a tool requiring approval or returning a structured error.

The reference story may assign engineering labels to these fixtures. Test assertions must confirm zero tool-name, domain, CAD, FEA, supplier, or file-format branches in the adapter.
