# Contract: Gateway Engineering Model Capability Provider

## Purpose

Extend GatewayService with provider-neutral dynamic capabilities while keeping one workspace authority path. MCP catalog/lifecycle behavior remains unchanged; an engineering model provider is an additional source of typed tools, not an MCP server.

## Provider interface

```python
class GatewayCapabilityProvider(Protocol):
    def tools(self, session: GatewaySessionContext) -> Sequence[GatewayTool]: ...

    async def call(
        self,
        session: GatewaySessionContext,
        tool: GatewayTool,
        arguments: Mapping[str, Any],
        *,
        request_id: str,
        approval_context: Any,
        progress_callback: ProgressCallback | None,
    ) -> Mapping[str, Any]: ...

    async def cancel(self, session: GatewaySessionContext, request_id: str) -> None: ...

    async def close_session(self, session: GatewaySessionContext) -> None: ...

    async def shutdown(self) -> None: ...
```

GatewayService receives a sequence of providers. Provider identity and tool names must be unique. A collision fails composition/startup; it never uses last-writer-wins behavior.

## Model tool projection

- Name: `wright_model__<normalized-model-id>__<task-id>`.
- `server_id`: `wright-models` for gateway provenance only; it does not correspond to an MCP server row.
- Input/output schemas: exact package task contracts.
- Description: bounded purpose plus material limitations, not marketing text.
- Annotations: read-only/idempotent/destructive/open-world hints, approval gates, model/variant/installation/adapter identities, evidence state, and no runtime connection data.
- Required state: exact installation is ready, mandatory test evidence matches current artifact/adapter/environment policy, binding is enabled for the session workspace, and policy snapshot is current.

## Discovery

For every session, the provider resolves bindings using the immutable principal/workspace/session identity. Disabled, unhealthy, missing, stale, incompatible, or cross-workspace bindings are hidden and audited with a stable reason. Discovery performs no load and starts no adapter.

## Call path

1. GatewayService finds one unique tool across MCP catalog, management tools, and capability providers.
2. Existing GatewayPolicy evaluates list/call authorization and required approvals.
3. GatewayService validates arguments against the exact input schema and establishes request/cancellation/audit state.
4. The provider re-resolves the binding and installation to prevent time-of-check/time-of-use drift, acquires references/leases, and invokes the runtime supervisor.
5. The provider validates and bounds the result; GatewayService applies its normal model-boundary sanitation and terminal publication rules.
6. Evidence records request, binding, installation, adapter, task/schema, input/output digests, trace, timing, cancellation, and cleanup without raw secret data.

## Review and Rivet

Rivet capability discovery records the full namespaced tool, input/output schema digests, installation and binding digests, and policy snapshot in the reviewed workflow binding. A later installation, adapter, schema, workspace, or policy change makes the binding stale and requires re-preview/review. Rivet receives no adapter command, endpoint, content path, token, or process authority.

## Cancellation and shutdown

Gateway request cancellation calls provider cancellation and preserves the normal late-result boundary. Session close releases session leases and unloads handles not shared under policy. Gateway shutdown rejects new requests, cancels providers, then shuts providers down after MCP lifecycle shutdown ordering is safely coordinated. Cleanup residue is visible and cannot be reported as success.

## Compatibility

- Existing callers using no providers observe identical MCP/management discovery and call behavior.
- MCP namespace parsing remains unchanged.
- Provider errors map to existing gateway categories when possible and retain a bounded model-specific reason in metadata.
- Resource listing and MCP UI resources are not implicitly exposed by a model provider.
