# Gateway service

Wright exposes one provider-neutral `GatewayService`. Codex, the API transport,
and optional agent integrations consume the same service; Hermes is not a bridge
or authorization authority.

## Identity and policy

Every process or HTTP transport is bound before MCP initialization to an explicit
principal, workspace session, and workspace ID. The repository verifies the exact
session/workspace association and the resulting immutable context supplies the
only workspace path used for child tools and resources. Recent activity and the
legacy `active_gateway_session_id` setting are never read for authorization.

Discovery projects only installed, enabled, workspace-authorized tools. Every
call repeats server-side policy evaluation, validates its input and structured
output, applies a bounded timeout, and appends a redacted audit record. MCP safety
annotations and client approval prompts are descriptive hints; they cannot grant
Wright approval.

## Protocol and lifecycle

The official stable Python MCP SDK owns protocol negotiation and framing for
STDIO and Streamable HTTP. Wright targets protocol `2025-11-25` and implements
tools/list, tools/call, resources/list, resources/read, cancellation, stable error
results, and workspace-scoped tool/resource list-change notifications.

Child MCP runners are owned by a generation-safe lifecycle coordinator. Per-server
locks prevent duplicate starts, late results cannot replace a newer generation,
and startup reconciliation plus bounded shutdown are awaited by the API lifespan.

The packaged YAML catalog and JSON Schema are the authored source. API and plugin
projections consume that resource, including canonical identity, aliases,
provenance, conservative safety metadata, platform status, and dated validation
evidence. Wheel and sdist tests verify both resources are present.

## Compatibility boundary

`WRIGHT_LEGACY_GATEWAY=1` temporarily enables `/api/gateway` and the
`tool_registry.gateway` launcher for one release. Both require explicit identity
and delegate to the same service/official SDK entry point. The flag defaults off;
removal is permitted after Feature 049 migrates the optional Hermes integration
and telemetry shows no remaining callers.
