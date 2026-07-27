# Gateway Service Contract

Every operation receives an immutable session context. No operation accepts an omitted workspace or consults recent/global activity.

## Operations

- `open_session(binding) -> GatewaySessionContext`
- `initialize(session, client/version/capabilities) -> server capabilities/instructions`
- `list_tools(session, cursor?) -> tools/next cursor`
- `call_tool(session, request_id, name, arguments, timeout?) -> structured result`
- `list_resources(session, cursor?) -> resources/next cursor`
- `read_resource(session, uri) -> contents`
- `cancel(session, request_id, reason?)`
- `subscribe_changes(session, sink)` / `close_session(session)`
- `shutdown()`

## Stable failures

- invalid/missing identity or workspace binding
- unsupported protocol or lifecycle order
- unknown/disabled/foreign tool or resource
- invalid input/output schema
- policy denied or approval prerequisite missing
- child unavailable, timeout, cancellation, or internal redacted failure

Policy denial is a successful protocol-level tool result with `isError` and structured error data where required by MCP; malformed protocol requests use JSON-RPC errors.
