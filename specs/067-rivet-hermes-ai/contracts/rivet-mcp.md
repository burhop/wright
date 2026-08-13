# Contract: Wright Rivet Workflow MCP

Server identity: `rivet-workflows`. Through `wrightgateway`, tools are namespaced as `rivet-workflows__<tool>`.

The process receives its workspace, workspace ID, session ID, and database path from the trusted launch binding. No tool accepts those fields or arbitrary paths.

## `list_templates`

Input: `{}`

Output: bounded array of `{id,title,description,kind,requirements}` from the packaged reviewed catalog.

Annotations: read-only, idempotent.

## `list_workflows`

Input:

```json
{"limit": 50}
```

Output: bounded summaries containing `slug`, `workflowId`, `revision`, `digest`, `reviewState`, and last run state when available. No raw project content.

Annotations: read-only, idempotent.

## `inspect_workflow`

Input:

```json
{"slug":"safe-slug"}
```

Output: workflow identity plus the same graph/input/output/requirements summary as validation. Raw project text is excluded.

Annotations: read-only, idempotent.

## `create_workflow`

Input, template form:

```json
{"slug":"safe-slug","templateId":"basic-flow"}
```

Input, authored project form:

```json
{"slug":"safe-slug","project":"<bounded Rivet project text>"}
```

Exactly one source is required. Project content is parsed and validated before write. Existing slugs fail; update is not implicit. Output contains identity and validation summary.

Annotations: destructive/write, not idempotent. Enabling the Wright-managed
Rivet Workflows server for the bound workspace supplies only the scoped
`rivet-workflow-mutation` gateway grant; disabling it revokes the grant.

## `validate_workflow`

Input:

```json
{"slug":"safe-slug","expectedRevision":1,"expectedDigest":"<sha256>"}
```

Revision/digest may be omitted for discovery, but are required when the result will lead to execution. Output is `WorkflowValidationResult` from the data model.

Annotations: read-only, idempotent.

## `run_workflow`

Input:

```json
{
  "slug":"safe-slug",
  "expectedRevision":1,
  "expectedDigest":"<sha256>",
  "graph":"Main",
  "inputs":{},
  "context":{},
  "timeoutSeconds":120
}
```

Rules:

- Exact current revision/digest is mandatory.
- Durable review for that revision is mandatory.
- Graph, inputs, context, timeout, output, and progress are bounded.
- Capability requirements denied by current policy fail before spawn.
- MCP cancellation cancels the owned run and waits for process cleanup.

Progress notifications include only bounded `{runId,status,sequence,message,percent?}` data. Terminal output includes run/workflow identity, state, reason code, output summary, truncation flag, and timing. It never includes Hermes credentials, full transcripts, arbitrary logs, or paths outside the workspace.

Annotations: execution/destructive. The enabled-server grant is scoped to Rivet
workflow mutation, while the exact revision's durable review remains a separate
mandatory execution gate.

## Error model

Tool failures return MCP `isError: true` with a stable structured error code and concise redacted text. Expected codes include:

- `RIVET_WORKFLOW_NOT_FOUND`
- `RIVET_WORKFLOW_EXISTS`
- `RIVET_WORKFLOW_INVALID`
- `RIVET_WORKFLOW_REVISION_CONFLICT`
- `RIVET_WORKFLOW_REVIEW_REQUIRED`
- `RIVET_CAPABILITY_DENIED`
- `RIVET_RUNNER_UNAVAILABLE`
- `RIVET_RUN_TIMEOUT`
- `RIVET_RUN_CANCELLED`
- `RIVET_RUN_FAILED`
