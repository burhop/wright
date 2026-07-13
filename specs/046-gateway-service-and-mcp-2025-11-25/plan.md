# Implementation Plan: Gateway Service and MCP 2025-11-25

**Branch**: `codex/046-gateway-service-and-mcp-2025-11-25` | **Date**: 2026-07-11 | **Spec**: [spec.md](spec.md)

## Summary

Replace Wright's hand-written, process-global REST/SSE gateway with one provider-neutral `GatewayService` in `tool_registry`. Bind every STDIO process or authenticated HTTP session immutably to an explicit workspace, delegate child-server lifecycle to a generation-safe coordinator, load a single packaged schema-validated catalog, and project authorized tools/resources through the official stable MCP Python SDK using protocol 2025-11-25 semantics. Keep the legacy REST/SSE routes behind an explicit one-release switch and make them delegate to the same service.

## Technical Context

**Language/Version**: Python 3.11–3.13; JSON/YAML/TOML/Markdown contracts

**Primary Dependencies**: Official `mcp>=1.27.2,<2` stable SDK, FastAPI/Starlette, Pydantic, existing httpx, structlog, `core`, `data_vault`, `workspace_service`, and `tool_registry`

**Storage**: Feature 044 SQLite schema plus packaged catalog resource; additive audit/session state only if repository evidence proves persistence is required

**Testing**: pytest async/unit/contract/integration tests, official SDK in-memory/STDIO/Streamable HTTP clients, protocol fixtures, Codex CLI 0.144.1 Windows smoke, package-resource builds, full dev merge gate

**Target Platform**: Windows and Linux local development; air-gapped amd64 Linux OCI appliance; exact Codex evidence limited to Windows in this feature

**Performance Goals**: 100 concurrent messages remain decodable; 100 two-session trials show zero leakage; operations have configurable timeouts and bounded maximums; shutdown completes within 10 seconds in tests

**Constraints**: Explicit immutable workspace identity; server policy authoritative; no recent/global fallback; no Hermes dependency; loopback-safe HTTP; serialized STDIO writes; no MCP host software in base image; legacy gateway one-release opt-in only

**Scale/Scope**: Existing engineering catalog (~30 entries), all enabled child MCP tools, multiple concurrent host sessions, lifecycle generations per configured server, three task-oriented management groups, catalog/workspace/artifact resources

## Constitution Check

- **Modular boundaries**: Pass. Protocol and lifecycle behavior live in `tool_registry`; API is a transport/composition adapter; workspace/data access use existing ports.
- **Offline-first**: Pass. STDIO and loopback HTTP work without cloud services.
- **Container policy**: Pass with roadmap precedence over the stale thick-base wording; no host applications are added.
- **Agent abstraction**: Pass. Codex and Hermes independently consume the same provider-neutral service.
- **SQLite/local files**: Pass. No server database is introduced.
- **Security/identity**: Pass. Feature 042 auth and explicit workspace binding are mandatory; client annotations never authorize calls.
- **Engineering protocol**: Pass. Official MCP SDK replaces hand-written framing.
- **Testing**: Pass. Direct protocol, isolation, lifecycle, package, API, and real Codex evidence are required.
- **Observability**: Pass. Redacted structured audit records and correlation are preserved; exporter wiring remains Feature 051.
- **Branch/manual gate**: Pass. Work is isolated and `check-dev-merge.sh` remains authoritative.

## Project Structure

```text
packages/tool_registry/src/tool_registry/
├── gateway_service.py            # provider-neutral discovery/call/resource use cases
├── gateway_models.py             # session/request/result value models
├── gateway_policy.py             # server-authoritative projection/authorization
├── lifecycle.py                  # per-server locks, generations, reconciliation/shutdown
├── mcp_server.py                 # SDK server construction and handlers
├── mcp_stdio.py                  # explicit-workspace STDIO entry point
├── catalog/
│   ├── engineering-catalog.yaml  # single packaged source
│   └── schema.json               # validation contract
├── catalog_loader.py             # packaged resource validation/aliases
└── gateway.py                    # temporary legacy entry delegating to SDK service

apps/api/src/api/
├── composition.py                # singleton service/coordinator construction
├── routers/mcp_transport.py      # authenticated /mcp mount/translation
└── routers/gateway.py            # one-release legacy adapter

packages/tool_registry/tests/
├── test_gateway_service.py
├── test_gateway_isolation.py
├── test_lifecycle_coordinator.py
├── test_mcp_stdio.py
├── test_mcp_http.py
├── test_gateway_policy.py
└── test_catalog_resource.py

tests/e2e/
└── test_codex_mcp_compatibility.py
```

## Implementation Sequence

1. Add official SDK dependency and protocol/client characterization tests around current behavior.
2. Introduce immutable gateway session/request/result models and repository/adapter ports.
3. Build a lifecycle coordinator; move start/stop/reconcile/shutdown behind per-server locks and generations; retain `McpEngine` as a delegate.
4. Consolidate the Python/YAML catalogs into one packaged resource with schema, provenance, aliases, and fail-closed validation evidence.
5. Implement `GatewayService` discovery/call/resource/policy/audit operations using explicit session context only.
6. Construct the official SDK server with protocol handlers, structured results, annotations, resources, notifications, cancellation, and stable errors.
7. Add serialized STDIO entry point with required workspace/process identity and bounded shutdown.
8. Mount authenticated Streamable HTTP `/mcp` through API composition with Origin, principal, session, protocol, and rate/size policy.
9. Convert existing REST/SSE gateway routes to a feature-flagged delegate and remove global active/recent workspace behavior.
10. Validate concurrency, late generations, reconnect, cancellation, package resources, clean shutdown, Codex CLI, docs, and full dev gate.

## Migration and Rollback

- **Upgrade**: Existing workspace/session/tool rows remain compatible. Catalog aliases map legacy IDs. No recent/global gateway selection is migrated into authorization; callers must supply explicit identity.
- **Host configuration**: Existing merge-only writers remain atomic and preserve unrelated configuration. Feature 048 owns Codex installer changes.
- **Compatibility**: `WRIGHT_LEGACY_GATEWAY=1` enables REST/SSE compatibility for one release; it delegates to `GatewayService` and still requires explicit session binding.
- **Failure**: Invalid catalog resources or unavailable required adapters fail composition/readiness closed. Child server failures are generation-scoped and redacted.
- **Rollback**: Stop the process and return to Feature 045. Existing SQLite/workspace state remains readable. Re-enable the prior image rather than partially restoring global gateway functions.
- **Removal**: Delete the compatibility routes/flag in the next approved removal feature after caller and telemetry evidence shows no use.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/gateway-service-contract.md](contracts/gateway-service-contract.md), [contracts/mcp-transport-contract.md](contracts/mcp-transport-contract.md), [contracts/catalog-contract.md](contracts/catalog-contract.md), and [quickstart.md](quickstart.md).

## Constitution Check — Post-Design

All gates remain passing. The design makes transport identity explicit, keeps API routes translation-only, uses a stable SDK rather than proprietary framing, preserves offline operation and state compatibility, and confines aspirational release/plugin/Hermes work to later features.

## Complexity Tracking

The one-release legacy gateway adapter is the only intentional temporary seam. It is justified by existing API/host callers, is feature-flagged, delegates to the same service, and has an explicit removal condition.
