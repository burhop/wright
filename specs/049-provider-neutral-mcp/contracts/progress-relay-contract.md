# Progress Relay Contract

## Child Request

When an outer MCP `tools/call` contains `_meta.progressToken`:

1. Wright generates a unique opaque child token scoped to the active child request.
2. Wright includes the child token in the child `tools/call` request metadata.
3. The STDIO reader recognizes `notifications/progress` without treating it as a response.
4. Updates are associated only with the matching active child token.

When the outer caller does not request progress, Wright does not require the child to emit it and adds no progress callback work.

## Validation and Forwarding

- `progressToken` must match the active child token.
- `progress` must be numeric, finite, and monotonic.
- `total`, when supplied, must be numeric, finite, and positive.
- `message`, when supplied, is converted to a bounded plain string.
- Unknown tokens, malformed updates, decreasing values, and updates after terminal completion are ignored and safely logged without payload disclosure.
- Valid updates are forwarded with the outer caller's original token through the official SDK session.

## Chat Projection

Agent adapters normalize received tool progress into generic fields:

```json
{
  "server": "optional-server-id",
  "tool": "qualified-or-advertised-name",
  "title": "advertised title or generic fallback",
  "progress": 1,
  "total": 4,
  "message": "server-authored message or generic fallback",
  "elapsedSeconds": 2.5,
  "correlationId": "optional request identity",
  "status": "running"
}
```

Wright-generated heartbeat events are explicitly marked `heartbeat: true` and never claim provider-specific state.

## Terminal Behavior

- Success, failure, cancellation, and timeout close the projection exactly once.
- The child callback is removed in `finally` regardless of outcome.
- No progress notification is forwarded after the child response or terminal error.
- Cancellation continues through the existing request/task lifecycle and cannot affect another session's token.
