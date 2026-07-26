# Implementation Plan: Provider-Neutral MCP Integration

**Branch**: `049-provider-neutral-mcp` | **Date**: 2026-07-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/049-provider-neutral-mcp/spec.md`

## Summary

Replace Wright's Solid Edge-specific prompt, tool filtering, workspace environment injection, and progress labels with provider-neutral contracts. Trusted MCP launch configuration gains exact workspace placeholders for literal argument arrays and non-secret environment templates; discovered tools retain their advertised metadata; standard child MCP progress is relayed through the Wright gateway; and agent/UI progress is normalized without recognizing provider or tool names. Preserve the current external server contract through ordinary configuration data, then prove identity independence with two synthetic servers and keep live Solid Edge validation optional and Windows-only.

## Technical Context

**Language/Version**: Python 3.11-3.14 for API/packages/tests; TypeScript 5 and React 19 for the existing web progress projection

**Primary Dependencies**: FastAPI/Starlette, Pydantic, official `mcp>=1.27.2,<2` SDK, asyncio/anyio, jsonschema, structlog, OpenTelemetry, SQLite, React, Vitest, Playwright

**Storage**: Existing SQLite `mcp_servers` and `mcp_tools` tables receive additive columns for trusted launch environment templates and complete advertised tool metadata; no destructive migration

**Testing**: pytest unit/contract/integration tests with synthetic STDIO servers, Vitest component/service tests, existing Hermes plugin tests, optional Windows live Solid Edge smoke, and `scripts/check-dev-merge.sh`

**Target Platform**: Offline-first Windows 11 and Linux x64 Wright hosts; optional Solid Edge compatibility remains Windows host-only

**Project Type**: Modular Python monorepo with FastAPI transport adapters, provider-neutral MCP packages, pluggable agent adapters, and React UI

**Performance Goals**: Relay requested child progress within 250 ms of receipt; preserve configured MCP call timeouts; add no subprocess or network round trip to calls without progress

**Constraints**: No provider-name/tool-name branching in Wright runtime; no shell evaluation of workspace values; untrusted server metadata cannot grant access; stdout remains protocol-only; no Solid Edge installation or SolidEdgeMCP checkout in required CI; preserve Hermes rebinding and multiple sessions

**Scale/Scope**: One generic launch-template grammar, all local STDIO MCP servers, complete stored metadata for discovered tools, one progress relay per active tool call, and existing active/recent chat replay buffers

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **Modular boundaries**: Pass. Launch rendering and child progress live in `tool_registry`; generic agent progress normalization lives in `agent_adapters`; API routes translate streams only.
- **Offline-first**: Pass. Runtime behavior uses local configuration, local subprocesses, SQLite, and existing workspace bindings.
- **Container strategy**: Pass under the repository's current roadmap and MCP clean-container process. Proprietary host software remains outside Wright images and required CI.
- **Agent abstraction**: Pass. No Hermes-only or provider-only rule enters the generic tool contracts; Hermes remains one adapter consuming the same progress projection.
- **Embedded state and file vault**: Pass. Additive SQLite columns preserve local state; approved workspace paths remain the artifact boundary.
- **Security and identity**: Pass. Only trusted configuration may use the exact workspace placeholder. Server annotations remain descriptive and approvals remain Wright-controlled.
- **Engineering protocol**: Pass. Subprocesses use literal argument arrays and official MCP JSON-RPC progress. Agents do not control GUI dialogs through Wright.
- **Testing pyramid**: Pass. Synthetic contract tests cover core behavior; UI tests cover progress rendering; live proprietary-host validation is optional.
- **Observability**: Pass. Correlation, timeout, lifecycle, and redaction fields remain structured. Progress payloads exclude arguments and secrets.
- **Phase isolation and branch discipline**: Pass. The operator explicitly requested the complete specify/plan/tasks/analyze/implement sequence on a dedicated feature branch.

## Project Structure

### Documentation (this feature)

```text
specs/049-provider-neutral-mcp/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- launch-binding-contract.md
|   |-- tool-metadata-contract.md
|   `-- progress-relay-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/data_vault/src/data_vault/
`-- migrations.py                 # additive launch/tool metadata columns

packages/tool_registry/src/tool_registry/
|-- models.py                     # launch config and complete tool metadata
|-- catalog_models.py             # trusted catalog launch environment
|-- catalog_loader.py             # catalog-to-state projection
|-- catalog_reconcile.py          # additive reconciliation
|-- db.py                         # serialization of new fields
|-- launch_templates.py           # exact workspace placeholder renderer
|-- lifecycle_adapters.py         # generic runner construction
|-- lifecycle.py                  # progress callback propagation
|-- manager.py                    # generic call callback propagation
|-- gateway_models.py             # trusted approvals separate from annotations
|-- gateway_policy.py             # provider-neutral policy only
|-- gateway_adapters.py           # preserve advertised metadata
|-- gateway_ports.py              # progress callback port
|-- gateway_service.py            # request-correlated progress relay
|-- mcp_server.py                 # outer SDK progress notification
`-- runners/
    |-- base.py                    # generic progress callback contract
    `-- stdio.py                   # child progress-token/notification handling

packages/agent_adapters/src/agent_adapters/
|-- hermes.py                     # remove provider-specific system guidance
`-- progress.py                   # generic progress projection and state

apps/api/src/api/routers/
`-- agent.py                      # thin use of generic progress projection

apps/web/src/services/
`-- agent-service.ts              # consume generic progress fields

packages/tool_registry/tests/
|-- test_launch_templates.py
|-- test_lifecycle_adapters.py
|-- test_gateway_policy.py
|-- test_gateway_service.py
|-- test_mcp_stdio.py
`-- test_mcp_transport.py

packages/agent_adapters/tests/
`-- test_progress.py

apps/api/tests/
`-- test_agent_stream_progress.py

apps/web/tests/
`-- ChatTranscript.spec.tsx
```

**Structure Decision**: Extend the provider-neutral GatewayService and lifecycle seams created by Feature 046. Store trusted launch configuration and complete discovered metadata in the existing registry state, relay standard progress through the official SDK at the outer boundary, and keep API/UI code unaware of providers.

## Implementation Sequence

1. Add failing contracts for exact workspace placeholder rendering, unknown-placeholder rejection, literal argument handling, unchanged unbound servers, and two differently named servers.
2. Add additive state fields for non-secret launch environment templates and advertised tool title/output schema/annotations; update catalog normalization, reconciliation, and serialization.
3. Replace `_workspace_scoped_environment` with one provider-neutral launch renderer and migrate the existing integration through configuration data/documentation rather than runtime detection.
4. Preserve full tool metadata during discovery and separate untrusted advertised annotations from trusted Wright approval requirements.
5. Remove the provider-specific gateway allowlist and Hermes system guidance.
6. Add a child-call progress callback contract, include a unique child progress token, consume standard progress notifications, and relay them through the outer SDK request token.
7. Move progress normalization/state into `agent_adapters`, remove CAD labels from the API route, and keep UI parsing/rendering generic.
8. Run synthetic identity-independence, rebinding, concurrency, cancellation, timeout, and replay tests; perform optional live Windows compatibility only when the matching external server contract is available.
9. Update operator migration/rollback guidance and the provider-specific removal inventory, then run the authoritative dev merge gate.

## Migration and Rollback

- **Database**: Add nullable/defaulted columns only. Older rows deserialize to empty launch templates and empty optional tool metadata.
- **Existing servers**: Commands and environments without `{workspace.path}` are byte-for-byte equivalent after parsing. A trusted administrator adds the exact placeholder to a command-array element or `launch_env` value when a server needs the active workspace.
- **Current SolidEdgeMCP**: Until its neutral command-line contract lands, an ordinary server record may set `CADMCP_SOLID_EDGE_ALLOWED_ROOTS: "{workspace.path}"` in launch configuration. The identifier is data, not Wright runtime logic.
- **Tool discovery**: Refresh replaces cached tool rows with the server's current title, schemas, and annotations. Missing optional metadata remains valid.
- **Progress**: Servers that ignore progress tokens behave as before. Servers that emit malformed/decreasing/late progress are clamped or ignored and cannot keep a request open.
- **Rollback**: Revert code and documentation as one unit. Additive database columns remain harmless. Restore the prior server record/environment if the external server has not adopted its neutral configuration.
- **Validation boundary**: A live Windows smoke is compatibility evidence only; catalog validation status still follows `docs/mcp-catalog/mcp-server-testing-process.md`.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/launch-binding-contract.md](contracts/launch-binding-contract.md), [contracts/tool-metadata-contract.md](contracts/tool-metadata-contract.md), [contracts/progress-relay-contract.md](contracts/progress-relay-contract.md), and [quickstart.md](quickstart.md).

## Constitution Check - Post-Design

All gates remain passing. The design uses additive embedded state, exact trusted placeholders, subprocess argument arrays, official MCP progress, package-owned policy/projection, and synthetic cross-platform tests. Proprietary host software and provider semantics stay outside Wright core and required CI.

## Complexity Tracking

No constitution violations require justification.
