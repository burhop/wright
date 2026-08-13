# Wright Rivet Runner Protocol v2

The runner reads exactly one bounded JSON object from stdin and emits bounded JSON Lines on stdout. Unknown security-relevant fields fail closed. Protocol v1 remains accepted only for graphs whose verified requirements exclude MCP.

## Request

```json
{
  "protocolVersion": 2,
  "runId": "run-uuid",
  "projectPath": "/absolute/workspace/path/.wright/workflows/example.rivet-project",
  "expectedDigest": "64-lowercase-hex",
  "graph": "Main",
  "inputs": {},
  "context": {},
  "capabilities": ["mcp"],
  "mcp": {
    "authorityId": "authority-uuid",
    "bridgeBaseUrl": "http://127.0.0.1:ephemeral-port/internal/rivet-mcp/v1",
    "token": "opaque-high-entropy-secret",
    "expiresAt": "2026-08-13T12:05:00Z",
    "bindingSetDigest": "64-lowercase-hex",
    "discoveryHandle": "wright-workspace",
    "bindings": [
      {
        "nodeId": "inspect-part",
        "handle": "wright:opaque-node-handle",
        "qualifiedToolName": "alpha__inspect",
        "bindingDigest": "64-lowercase-hex"
      }
    ]
  }
}
```

Rules:

- `mcp` is present only when `capabilities` contains `mcp` and the exact review is current.
- The runner validates origin, path, expiry shape, unique static node IDs/handles, namespaced tool names, and digests before loading the project.
- After project digest verification and project load, the runner validates the selected graph's MCP nodes against the binding set, rejects dynamic tool-name input, rejects any extra/missing MCP tool-call node, and creates an in-memory transformed project or provider lookup. It does not write the project.
- MCP prompt nodes and prompt retrieval are rejected because protocol v2 grants tools only.
- The token is never included in output, errors, URLs, project metadata, or child requests. The custom provider adds it as `Authorization: Bearer` only for exact-origin bridge calls.
- The network guard allows the exact AI origin (when present) and exact MCP bridge origin. It continues to deny graph `httpCall`, code, filesystem, dataset, or interactive capabilities unless independently granted; possession of an MCP bridge does not grant generic network access.

## Provider operations

The injected provider maps Rivet calls to the bridge:

- `discoverTools(serverConfig)` -> `POST /discover` with reserved discovery handle
- `callTool(serverConfig, toolName, args)` verifies `toolName` against the Wright-issued in-memory binding and then sends `POST /calls` with only the node handle, binding digest, request ID, and arguments; the tool namespace is not submitted as call authority
- prompt operations are denied in this loop unless separately specified and bound by a later protocol

Project-provided URL, command, args, env, headers, or authorization fields are never forwarded.

## Runner output

Existing event envelope remains:

```json
{"type":"progress","runId":"...","state":"running","phase":"mcp-child-progress","nodeId":"...","callId":"...","bindingDigest":"...","status":"running","title":"...","progress":0.5}
{"type":"result","runId":"...","state":"succeeded","outputs":{}}
```

Allowed MCP phases:

- `mcp-binding-validating`
- `mcp-approval-required`
- `mcp-child-starting`
- `mcp-child-progress`
- `mcp-child-result`
- `mcp-child-cancelling`
- `mcp-child-cancelled`
- `mcp-residue`

Every event is size-bounded and contains safe display fields only. The Python host assigns the durable sequence and revalidates run/node/call identities.

## Stable failures

- `RIVET_MCP_GRANT_REQUIRED`
- `RIVET_MCP_PROJECT_CONFIG_DENIED`
- `RIVET_MCP_DYNAMIC_TOOL_DENIED`
- `RIVET_MCP_BINDING_MISSING`
- `RIVET_MCP_BINDING_EXTRA`
- `RIVET_MCP_BINDING_MISMATCH`
- `RIVET_MCP_BRIDGE_DENIED`
- `RIVET_MCP_AUTHORITY_EXPIRED`
- `RIVET_MCP_AUTHORITY_REVOKED`
- `RIVET_MCP_POLICY_DENIED`
- `RIVET_MCP_APPROVAL_REQUIRED`
- `RIVET_MCP_RESULT_TOO_LARGE`
- `RIVET_MCP_CANCELLED`

Messages are safe to display and never echo a token, credential, endpoint query, environment value, or raw child error.

## Cancellation

SIGINT/SIGTERM aborts the processor and any active provider request. The Python owner separately revokes authority and cancels the gateway request; runner disconnect is not treated as proof that the child stopped.
