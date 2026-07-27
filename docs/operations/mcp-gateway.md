# MCP gateway operations

## STDIO

Start the full-repository composition root with an existing workspace/session
association:

```powershell
uv run python -m api.gateway_stdio `
  --session-id <session-id> `
  --workspace-id <workspace-id> `
  --principal-id codex:local
```

The same values may be supplied as `WRIGHT_MCP_SESSION_ID`,
`WRIGHT_MCP_WORKSPACE_ID`, and `WRIGHT_MCP_PRINCIPAL_ID`. Missing or mismatched
identity fails before initialization. Diagnostics use stderr; stdout is reserved
for SDK-owned MCP frames. EOF cancels owned calls and closes the session.

## Streamable HTTP

The stateful endpoint is `POST|GET|DELETE /mcp`. Use the configured Wright bearer
token and send these headers on every request:

```text
Authorization: Bearer <WRIGHT_API_TOKEN>
X-Wright-Session-Id: <session-id>
X-Wright-Workspace-Id: <workspace-id>
```

The existing configured Origin policy applies. The SDK-issued `Mcp-Session-Id`
and negotiated `Mcp-Protocol-Version` are required for subsequent stateful
requests. A transport session ID presented with another binding receives 404.

Defaults are loopback binding, 1 MiB request bodies, 16 concurrent transport
requests, 120 requests/minute per local principal, a 30-second operation timeout,
a 120-second maximum, and a 30-minute session idle timeout. Override with
`WRIGHT_MCP_MAX_BODY_BYTES`, `WRIGHT_MCP_MAX_CONCURRENCY`,
`WRIGHT_MCP_REQUESTS_PER_MINUTE`, `WRIGHT_MCP_TIMEOUT`,
`WRIGHT_MCP_MAX_TIMEOUT`, and `WRIGHT_MCP_SESSION_IDLE_TIMEOUT`.

Client disconnect does not imply protocol cancellation. Send
`notifications/cancelled` with the owned request ID. Shutdown stops accepting new
calls, cancels owned requests, closes transport sessions, and then stops child
runners.

## Failure and rollback

Invalid catalog, database migration, security configuration, or required adapter
construction prevents readiness. Tool/provider failures return stable redacted
results and remain in the append-only gateway audit table.

Rollback the complete Feature 046 commit/image and restart. SQLite workspace and
audit rows are additive and remain readable; no reverse migration is needed.
Temporarily enabling `WRIGHT_LEGACY_GATEWAY=1` is a caller migration aid, not a
rollback for explicit identity or server-side authorization.
