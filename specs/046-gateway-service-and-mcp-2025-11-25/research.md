# Research: Gateway Service and MCP 2025-11-25

## Official stable Python SDK

**Decision**: Depend on `mcp>=1.27.2,<2` and use its server/session transports; the 2026-07-11 lock resolution selected stable `mcp 1.28.1`.

**Rationale**: On 2026-07-11 the official repository identifies v1 as stable and v2 as prerelease; the package index resolution selected v1.28.1. The prior Wright gateway had no SDK dependency and hand-wrote protocol 2024-11-05.

**Alternatives considered**: Hand-written JSON-RPC was rejected for negotiation/cancellation/transport risk. MCP v2 alpha was rejected because compatibility claims require stable dependencies.

## Protocol version

**Decision**: Implement and test MCP 2025-11-25 semantics as the approved compatibility target while allowing SDK negotiation rather than hard-coded response literals.

**Rationale**: The official lifecycle requires initialize/initialized ordering, version negotiation, capability declarations, timeouts, and the `MCP-Protocol-Version` HTTP header. Cancellation and Streamable HTTP rules are explicit for 2025-11-25.

**Alternatives considered**: Keeping 2024-11-05 contradicts the roadmap. Claiming a newer protocol without a verified host/SDK matrix was rejected.

## Codex compatibility

**Decision**: Record exact local evidence for Codex CLI 0.144.1 on Windows only.

**Rationale**: `codex --version` reports `codex-cli 0.144.1`. The official Codex manual integrity fetch failed because the response omitted its required checksum header, so no claims are derived from that snapshot; official OpenAI pages and executable local behavior are used.

**Alternatives considered**: Broad ChatGPT desktop/macOS/IDE claims are deferred to Feature 048/host-matrix work.

## Session identity

**Decision**: Create immutable `GatewaySessionContext` at connection/process creation and require it on every service operation.

**Rationale**: Current routes call `get_gateway_workspace`, backed by process-global active state, and `McpEngine` falls back to the most recently updated workspace. Both violate authorization isolation.

**Alternatives considered**: Context variables alone were rejected because reconnect and cancellation require durable session-key lookup. Recent-workspace compatibility was rejected as unsafe.

## Lifecycle ownership

**Decision**: Add a coordinator with a lock and monotonically increasing generation per server; only the current generation may publish status/tools.

**Rationale**: Current `McpEngine` directly mutates a runner dictionary and database across unsynchronized start/stop/reconcile paths, allowing late results and duplicate processes.

**Alternatives considered**: A single global lock needlessly serializes unrelated servers. Keeping route access to `_active_runners` was rejected.

## Catalog ownership

**Decision**: Package one schema-validated YAML catalog resource in `tool_registry`, with generated projections only where necessary.

**Rationale**: `engineering_catalog.py`, plugin YAML, and fixtures currently duplicate catalog truth. A packaged resource enables exact parity and artifact tests.

**Alternatives considered**: Python literals remain difficult to consume outside Python. Runtime merging of divergent sources hides conflicts and was rejected.

## HTTP security

**Decision**: Reuse Feature 042 authentication and origin policy, bind SDK transport sessions to authenticated principals, require explicit workspace/session selection, and default to loopback.

**Rationale**: Official SDK v1.27.2 includes authenticated-principal transport-session binding fixes. The official transport specification requires protocol headers and distinguishes disconnect from cancellation.

**Alternatives considered**: Anonymous loopback and Origin-agnostic requests were rejected due to browser/DNS-rebinding threats. Full remote OAuth authorization-server work is deferred.

## Experimental tasks

**Decision**: Do not claim MCP durable-task support. Implement cancellable requests and Wright task-oriented management tools.

**Rationale**: Tasks are an experimental 2025-11-25 utility with distinct state/cancellation semantics, and the approved feature does not require persistence of protocol tasks.

**Alternatives considered**: Partial task support would create false compatibility claims.

## Primary evidence

- OpenAI Codex developer documentation and executable `codex-cli 0.144.1`, verified 2026-07-11 on Windows.
- MCP 2025-11-25 lifecycle, transports, and cancellation pages, verified 2026-07-11.
- Official `modelcontextprotocol/python-sdk` README/releases plus resolved package metadata, v1.28.1 stable and v2 prerelease, verified 2026-07-11.
