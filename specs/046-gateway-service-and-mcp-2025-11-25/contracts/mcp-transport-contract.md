# MCP Transport Contract

## STDIO

- One process receives one explicit workspace binding before initialization.
- Input/output use the official SDK transport; diagnostics never use stdout.
- All responses and notifications pass through one serialized writer.
- EOF begins bounded close: cancel owned requests, close session, stop transport.

## Streamable HTTP `/mcp`

- Protected by existing Wright authentication and configured Origin policy.
- Session identity is bound to authenticated principal and immutable workspace.
- Subsequent requests carry the negotiated protocol header and valid transport session identifier when stateful mode is used.
- Disconnect is not cancellation; explicit MCP cancellation owns that semantic.
- Request body, concurrency, and rate limits fail with stable HTTP/protocol errors.
- Loopback is the default bind; remote insecure configuration remains refused.

## Capabilities

Advertise only implemented tools/resources list-change, logging/progress, and other capabilities. Do not advertise experimental tasks or unsupported prompts/sampling.

## Compatibility

Legacy `/api/gateway/tools`, `/call`, and `/events` exist only when the compatibility switch is enabled and delegate to a bound session on the same service.
