# Wright API

The API package is Wright's composition root and transport layer. It constructs
workspace, data-vault, tool-registry, and agent adapters once during the
fail-closed lifespan; routes translate authenticated requests and do not select
infrastructure.

Feature 046 mounts the official MCP SDK Streamable HTTP transport at `/mcp` and
provides `python -m api.gateway_stdio` for explicitly bound local STDIO clients.
See [gateway architecture](../../docs/architecture/gateway-service.md) and the
[operations guide](../../docs/operations/mcp-gateway.md).
