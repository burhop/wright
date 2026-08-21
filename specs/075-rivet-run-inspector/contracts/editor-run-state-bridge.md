# Contract: Rivet Editor Run-State Bridge

The direct surface and embedded Rivet editor continue to communicate only through the existing exact-origin `postMessage` bridge. No output values, credentials, authority tokens, or MCP arguments cross this bridge.

## Protocol version

The editor advertises:

```json
{ "type": "wright-rivet:ready", "protocolVersion": 3 }
```

The parent accepts version 2 for project open/save compatibility. Run-state and node-focus messages require version 3; if unavailable, the Run Inspector remains functional and explains that canvas highlighting is unavailable.

## Set node execution states

Parent request:

```json
{
  "type": "wright-rivet:set-run-state",
  "requestId": "request-123",
  "runId": "run-123",
  "states": [
    { "nodeId": "node-a", "state": "succeeded" },
    { "nodeId": "node-b", "state": "failed" }
  ],
  "focusNodeId": "node-b"
}
```

Editor response:

```json
{
  "type": "wright-rivet:run-state-set",
  "requestId": "request-123",
  "runId": "run-123",
  "missingNodeIds": []
}
```

Validation rules:

- `requestId`, `runId`, and each `nodeId` are non-empty bounded strings.
- At most 512 node states are accepted per request.
- State is one of `queued`, `running`, `succeeded`, `failed`, `cancelled`, `not_run`, or `unknown`.
- The editor applies text/icon/accessibility metadata in addition to color.
- `focusNodeId`, when present and found, selects the node and brings it into the visible viewport without modifying the project.
- Missing historical nodes are reported in `missingNodeIds`; no similar node is substituted.
- A second run ID replaces the prior run overlay atomically.

## Clear node execution states

Parent request:

```json
{
  "type": "wright-rivet:clear-run-state",
  "requestId": "request-124",
  "runId": "run-123"
}
```

Editor response:

```json
{
  "type": "wright-rivet:run-state-cleared",
  "requestId": "request-124",
  "runId": "run-123"
}
```

The overlay clears when a new workflow project opens, the selected run changes, or the parent explicitly clears it. It is presentation state and never changes serialized workflow bytes.

## Security and failure behavior

- Continue requiring `event.source === window.parent` and the exact configured parent origin.
- Continue correlating every response by request ID.
- Reject malformed messages with `wright-rivet:error` and a stable non-secret code.
- Do not use DOM selectors or synthetic user events to implement focus.
- Implement the host method at Wright's maintained Rivet source-patch layer, then rebuild and verify the pinned editor manifest and wrapper hashes.

