# Implementation Plan: Wright Architecture Refactoring Phase 2

**Branch**: `codex/refactoring-phase-2-2026-07-01` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/038-refactoring-phase-2/spec.md`

**Note**: This plan follows the Phase 2 architecture document and implements the cohesive service/policy/telemetry slice plus the follow-up ownership pass requested after initial verification.

## Summary

Add a `workspace_service` package facade, strengthen provider-owned context materialization, move MCP catalog and safety ownership to `tool_registry`, add opt-in validation CLI/evidence writer seams, generate checked-in frontend contract types, clarify trace versus correlation identity, add a `data_vault` state-store seam, extract high-churn UI sections, and update docs. Hermes remains default and first-class, but generic workspace/API code no longer treats Hermes files as the architecture boundary.

## Technical Context

**Language/Version**: Python >=3.11; TypeScript 6.0 and React 19 for generated contract checks

**Primary Dependencies**: FastAPI, Pydantic, SQLite, structlog, OpenTelemetry API/SDK, pytest, React/Vite/Vitest

**Storage**: Local SQLite for current workspace/MCP state; local filesystem for workspaces, validation evidence, and checked-in generated contracts

**Testing**: `uv run pytest` for package/API tests; `npm run test --workspace=apps/web` when generated frontend files are touched; validation CLI mock executor tests only in default suite

**Target Platform**: Local Wright monorepo with offline-first default behavior

**Project Type**: Modular monorepo with FastAPI API, Python packages, Hermes plugin, MCP registry, and React frontend

**Performance Goals**: Preserve existing API response compatibility; avoid live agent, Docker, network, or MCP process startup during import and default tests

**Constraints**: Hermes remains default; OpenClaw remains a stub; API responses remain compatible; no MCP-specific host software is added to base Docker image; remote telemetry export is disabled by default

**Scale/Scope**: One Phase 2 implementation slice touching `packages/workspace_service`, `packages/agent_adapters`, `packages/tool_registry`, `packages/core`, selected API routes/services, generated frontend contracts, docs, and tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: New workspace lifecycle logic lives in `packages/workspace_service`; MCP policy and validation stay in `tool_registry`; provider context materialization stays in `agent_adapters`; API routes remain translators. (Pass)
- **Offline-First Mandate**: Default tests use fakes, mock validation, temp SQLite, and checked-in generated files. (Pass)
- **Container Strategy**: Docker validation is opt-in and does not add MCP-specific host software to the base image. (Pass)
- **Agent Abstraction**: Hermes is a provider implementation, not the generic context model. (Pass)
- **Engineering Tooling Protocol**: MCP safety and validation use registry-owned contracts and do not require GUI interaction. (Pass)
- **3-Tier Testing**: This slice adds package/API/contract tests. UI tests run if generated frontend contract files are touched. (Pass)
- **Observability**: This slice adds telemetry identity constants, redaction helpers, and tests for local-first/default-off behavior. (Pass)
- **Branch Discipline**: Work is on `codex/refactoring-phase-2-2026-07-01`. (Pass)
- **Manual Gating**: The user explicitly requested implementation after Spec Kit artifact generation; no breaking API response change is planned. (Pass)

## Project Structure

### Documentation (this feature)

```text
specs/038-refactoring-phase-2/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- agent-context-materialization.md
|   |-- frontend-contracts.md
|   |-- mcp-safety-policy.md
|   |-- telemetry-contract.md
|   |-- validation-cli.md
|   `-- workspace-service.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
apps/
|-- api/
|   |-- src/api/routers/workspace.py
|   |-- src/api/routers/gateway.py
|   |-- src/api/services/mcp_services.py
|   `-- tests/
`-- web/
    `-- src/types/generated/wright-contracts.ts

packages/
|-- agent_adapters/
|   |-- src/agent_adapters/context.py
|   `-- tests/
|-- core/
|   |-- src/core/telemetry.py
|   |-- src/core/redaction.py
|   `-- tests/
|-- tool_registry/
|   |-- src/tool_registry/safety.py
|   |-- src/tool_registry/validation_executor.py
|   |-- src/tool_registry/validation_writer.py
|   |-- src/tool_registry/validation_cli.py
|   `-- tests/
`-- workspace_service/
    |-- pyproject.toml
    |-- src/workspace_service/
    `-- tests/

scripts/
`-- generate-frontend-contracts.py

tests/
`-- test_import_boundaries.py
```

**Structure Decision**: Add one new package for workspace lifecycle ownership and keep all other changes inside existing package ownership boundaries.

### Completion Pass Additions

- `packages/tool_registry/src/tool_registry/engineering_catalog.py` owns the canonical engineering catalog seed data that API migrations import.
- `packages/data_vault/src/data_vault/state_store.py` owns shared SQLite connection defaults for migration-facing and service-facing storage paths.
- `DockerCleanContainerExecutor` launches an opt-in clean container and records direct stdio MCP probe evidence. It records `partial` evidence unless Wright gateway proxy probes are also present.
- `ToolCard` and `WorkspacePanel` shed repeated JSX into `WorkspaceEnablement` and `WorkspaceActivityBar`.

## Complexity Tracking

No constitution violations are planned. The new package is justified by the Phase 2 ownership decision and keeps API route churn incremental.

## Phase 0 Research

See [research.md](research.md).

Key decisions:

- Add `workspace_service` as a facade first, delegating to existing helpers where needed.
- Keep provider context materialization in `agent_adapters`.
- Enforce MCP safety through `tool_registry` policy decisions.
- Keep clean-container execution opt-in through a CLI/executor seam.
- Generate deterministic TypeScript contracts into the web app.
- Treat `X-Trace-Id` as `wright.correlation_id`, not OTel `trace_id`.

## Phase 1 Design

See [data-model.md](data-model.md) and [contracts/](contracts/).

Implementation order:

1. Boundary/package scaffolding and tests.
2. Telemetry constants/redaction helpers.
3. Agent context materializer contracts.
4. Workspace service facade and API route delegation.
5. MCP safety policy and lifecycle enforcement.
6. Validation CLI/evidence writing.
7. Frontend contract generation.
8. Docs and verification.

## Post-Design Constitution Re-Check

- **Modular Monorepo Boundaries**: Package responsibilities are explicit and import-boundary tests enforce `packages/*` cannot import `apps/api`. (Pass)
- **Offline-First Mandate**: Docker, network, credentials, hosted agents, package registries, and proprietary tools stay outside default tests. (Pass)
- **Agent Abstraction**: Hermes-specific context files move behind provider materializers. (Pass)
- **API Compatibility**: Routes touched by this phase return existing response models. (Pass)
- **Observability**: Trace/correlation/redaction contracts are defined before broader instrumentation. (Pass)

## Migration And Rollback

Migration is additive. `workspace_service` delegates to existing `core.workspace` behavior at first and can be bypassed if needed by restoring prior route calls. Hermes context materialization remains compatible through the Hermes materializer. MCP safety policy starts at package boundaries and surfaces typed errors through existing API error translation. Validation CLI mock and Docker seams can be disabled without affecting catalog metadata preflight. Generated TypeScript contracts are checked in and can be regenerated offline.
