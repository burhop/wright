# Rivet Workspace MCP Gateway API

All public endpoints use existing Wright authentication, role, session, and workspace resolution. Route handlers contain no binding/policy/lifecycle logic. The internal runner bridge is loopback-only, bearer-authorized by a memory-only run capability, has no CORS permission, and is not a user API.

## Public authoring and review

### `GET /api/workspace/workflows/{slug}/mcp-capabilities`

Query: `session_id`, `graph`, optional `after`, `limit` (bounded).

Returns the exact workflow identity, selected graph, extracted MCP requirements/nodes, discovery snapshot digest, and current workspace-enabled namespaced tool projections. Does not start a child solely for authoring.

### `POST /api/workspace/workflows/{slug}/mcp-bindings/preview`

Request contains `session_id`, expected workflow revision/digest, graph, and proposed `{node_id, qualified_tool_name}` selections. It cannot contain server configuration or credential material.

Returns canonical binding previews, ambiguity/blocking reasons, binding-set digest, expiry, and safe policy/risk/schema facts. Preview has no execution authority.

### `POST /api/workspace/workflows/{slug}/review`

Extends the existing review request with expected workflow digest, graph, and binding-set digest for MCP graphs. On approval, Wright rebuilds/compares every binding and stores a v2 review digest atomically. A stale preview returns `409` with a reason-coded diff.

### `POST /api/workspace/workflows/{slug}/runs`

Extends the current start request with expected review digest and binding-set digest. The service verifies current review and bindings, creates the run/manifest, mints authority, and starts protocol v2. Neither token nor internal bridge address appears in the public response.

## Public exact-call approval

### `GET /api/workspace/workflows/runs/{run_id}/approvals`

Query: `session_id`. Returns pending/decided exact-call approvals with node, namespaced tool, safe argument summary/digest, required gates, effect/risk information, expiry, and current state.

### `POST /api/workspace/workflows/runs/{run_id}/approvals/{approval_id}`

Request: `session_id`, `decision` (`approved` or `denied`), expected `approval_digest`, optional bounded reason.

The authenticated service verifies workspace/run/node/tool/argument/gate/expiry identities. Approval is one-shot and cannot be supplied by the runner.

## Public run inspection/cancellation

Existing run/status/history/cancel endpoints retain their paths. Responses add safe manifest identity, current node/call/approval, residue, artifact references, and recovery reasons. Cancel is idempotent by run generation.

## Internal loopback bridge

Every request uses:

- exact internal path and method;
- `Authorization: Bearer <opaque run token>`;
- `Content-Type: application/json`;
- body/request/event/output limits;
- authority/run/request/node identities in the body;
- no workspace, server URL/command, environment, headers, credentials, or arbitrary tool namespace from the runner.

### `POST /internal/rivet-mcp/v1/discover`

Request: authority ID, run ID, discovery handle, request ID, optional bounded cursor.

Response: only the authority's reviewed binding-set tool projections. This operation revalidates authority/review/grants and cannot expand authority from newly enabled tools.

### `POST /internal/rivet-mcp/v1/calls`

Request: authority ID, run ID, node handle, binding digest, request ID, and arguments. It contains no server or tool namespace.

Response is bounded NDJSON:

```json
{"type":"progress","callId":"...","phase":"child-starting","status":"running"}
{"type":"progress","callId":"...","phase":"child-progress","status":"running","progress":0.5}
{"type":"approval_required","callId":"...","approvalId":"...","approvalDigest":"..."}
{"type":"result","callId":"...","content":[],"structuredContent":{},"isError":false,"artifacts":[]}
```

The server resolves the node handle to the authoritative server/tool binding, validates arguments/schema/policy, and invokes `GatewayService.call_tool` with `client_approval_hint=false`.

### `POST /internal/rivet-mcp/v1/calls/{request_id}/cancel`

Internal diagnostic/idempotent cancel. Normal public cancellation goes through the run service, which revokes authority and directly cancels active gateway requests even if the runner is unreachable.

## Error envelope

Public APIs use Wright's established typed error response. Internal bridge failures use one terminal NDJSON result with stable code, safe message, run/node/call correlation, retryability, and optional recovery action. Authentication failures reveal no claim comparison detail.

Representative public reason codes:

- `RIVET_BINDING_REQUIRED`, `RIVET_BINDING_AMBIGUOUS`, `RIVET_BINDING_STALE`
- `RIVET_REVIEW_STALE`, `RIVET_WORKSPACE_GRANT_CHANGED`
- `RIVET_SERVER_REVISION_CHANGED`, `RIVET_TOOL_SCHEMA_CHANGED`, `RIVET_VALIDATION_STALE`
- `RIVET_CALL_APPROVAL_REQUIRED`, `RIVET_CALL_APPROVAL_CHANGED`, `RIVET_CALL_APPROVAL_EXPIRED`
- `RIVET_RUN_AUTHORITY_REVOKED`, `RIVET_CHILD_CANCELLATION_UNCONFIRMED`

## Redaction and limits

- No raw token, credential, authorization/header value, child environment, command, endpoint query, unrestricted path, or full secret-like argument is returned or logged.
- Schemas, arguments, content, structured results, progress, and error text are bounded using the runner/gateway limits.
- Artifact responses contain only Wright-authorized gateway resource or contained-vault identities/digests and separately authorized download routes. Raw child paths, arbitrary URIs, and unvalidated artifact claims are rejected.
