# Implementation Plan: Architecture Refactoring Audit Implementation

**Branch**: `codex/refactoring-audit-2026-07-01` | **Date**: 2026-07-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/037-refactoring-audit/spec.md`

**Note**: This plan follows the 2026-07-01 refactoring audit and intentionally avoids a big-bang rewrite. Each phase must be independently testable and suitable for a focused commit.

## Summary

Implement the high-priority architecture seams from the refactoring audit in six small phases: add an agent-neutral runtime registry, define shared Wright gateway contracts, extract MCP route business logic into service-layer code, unify catalog normalization boundaries, add a clean-container validation harness seam, and close constitution-required smoke coverage. Hermes remains the default and first-class working runtime, `hermes-plugin-wright` remains a first-class package, API response shapes remain backward compatible, and Docker/network validation stays opt-in.

## Technical Context

**Language/Version**: Python >=3.11 for backend/packages; TypeScript 6.0 and React 19 for frontend smoke coverage

**Primary Dependencies**: FastAPI, Pydantic, SQLite, structlog, pytest, httpx/respx, React, Vite, Vitest, Playwright

**Storage**: Existing local SQLite state and workspace files; catalog metadata in SQLite seed/plugin YAML; validation evidence and follow-up records under docs when produced

**Testing**: `uv run pytest` for targeted API/package tests; `npm run test --workspace=apps/web` or Playwright only when frontend files are touched; Docker/network validation opt-in only

**Target Platform**: Local Wright monorepo branch with offline-first default test behavior; clean-container MCP validation targets local Ubuntu/Linux containers when explicitly requested

**Project Type**: Modular monorepo with FastAPI backend, Python adapter/registry packages, Hermes plugin package, MCP tool registry package, React frontend, and system smoke tests

**Performance Goals**: Preserve API health and MCP list response latency within existing test expectations; avoid starting live agent or MCP processes during API import; keep fast targeted tests local and deterministic

**Constraints**: Preserve Hermes behavior; do not overfit abstractions to Hermes; do not delete `hermes-plugin-wright`; do not introduce breaking API responses; preserve offline-first behavior; do not add network-dependent tests to the default fast suite; do not add MCP-specific host software to the base Docker image; package-manager install/update flows do not need extra approval gates

**Scale/Scope**: Six implementation phases touching `packages/agent_adapters`, `apps/api`, `packages/tool_registry`, `hermes-plugin-wright`, selected `packages/core` gateway/workspace helpers, docs, and smoke tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Agent runtime contracts belong in `packages/agent_adapters`; MCP catalog/validation/service concepts move toward package/service-layer ownership; routes stay HTTP-focused. (Pass)
- **Offline-First Mandate**: Fast tests use mocks/fakes and do not require hosted agents, package registries, Docker, credentials, proprietary software, or network. Docker validation is documented as opt-in. (Pass)
- **Container Strategy**: Clean-container validation remains local and per-MCP; no MCP-specific host software is added to the base image solely for catalog validation. (Pass)
- **Agent Abstraction**: API boot must ask an agent-neutral registry/factory for the active engine instead of importing or instantiating Hermes directly. (Pass)
- **Engineering Tooling Protocol**: Wright gateway contracts use the same MCP protocol for Hermes and future OpenClaw integration. (Pass)
- **3-Tier Testing**: This feature adds package/API tests for changed contracts and system smoke coverage under `tests/e2e`. Existing UI integration coverage is left intact unless touched. (Pass)
- **Observability**: New package/service code should use existing structured logging patterns and preserve trace IDs through API routes. (Pass)
- **Branch Discipline**: Work is on `codex/refactoring-audit-2026-07-01`. (Pass)
- **Manual Gating**: This plan identifies no intentional breaking API changes. If implementation uncovers a breaking contract requirement, stop for explicit approval. (Pass)

## Project Structure

### Documentation (this feature)

```text
specs/037-refactoring-audit/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- risk-review.md
|-- contracts/
|   |-- agent-runtime-registry.md
|   |-- mcp-service-contract.md
|   |-- validation-evidence-contract.md
|   `-- wright-gateway-protocol.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
apps/api/
|-- src/api/main.py
|-- src/api/config.py
|-- src/api/routers/
|   |-- agent.py
|   |-- gateway.py
|   |-- mcp.py
|   `-- setup.py
|-- src/api/services/
`-- tests/

packages/
|-- agent_adapters/
|   |-- src/agent_adapters/
|   `-- tests/
|-- tool_registry/
|   |-- src/tool_registry/
|   `-- tests/
`-- core/
    `-- src/core/

hermes-plugin-wright/
|-- catalog.py
|-- schemas.py
|-- commands.py
`-- tests/

tests/
|-- e2e/
`-- ui-integration/
```

**Structure Decision**: Use existing packages and add focused service/contract modules inside current ownership boundaries. Do not create a new top-level package unless a later explicit decision shows the shared Wright gateway surface cannot fit cleanly in `agent_adapters` and `tool_registry`.

## Complexity Tracking

No constitution violations are planned. Complexity is controlled by phase gates, compatibility tests, and rollback paths per phase.

## Phase 0 Research

See [research.md](research.md).

Key decisions:

- `packages/agent_adapters` owns agent runtime registry/factory contracts and Wright gateway profile interfaces.
- `packages/tool_registry` owns shared MCP catalog schema/normalization and validation plan/evidence concepts.
- `apps/api` owns HTTP translation and dependency wiring only.
- `hermes-plugin-wright` remains first-class and consumes shared catalog/gateway concepts where practical without becoming a thin alias package.
- Validation evidence is structured first, with Markdown follow-up records retained for human-readable problem logs.

## Phase 1 Design

See [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md), and [risk-review.md](risk-review.md).

Implementation order:

1. Agent runtime registry and API boot selection.
2. Wright gateway contracts and Hermes compatibility seam.
3. MCP route service extraction.
4. MCP catalog normalization boundary.
5. Clean-container validation harness seam.
6. System smoke coverage.

## Migration and Rollback Note

Migration is additive and staged. The first runtime registry must default to Hermes and accept the existing Hermes configuration sources, so rollback for Phase 1 is limited to restoring direct API boot wiring if necessary. Gateway contract work keeps Hermes config and workspace behavior compatible while introducing shared contracts; rollback removes the new contract adapters and restores current Hermes sync service calls. MCP service extraction keeps route response models unchanged; rollback can replace service calls with the prior route-local logic for a single operation group. Catalog normalization initially runs in parity mode; rollback keeps existing API seed/plugin loaders. Validation harness work adds plan/evidence abstractions without making Docker validation mandatory; rollback disables the new runner seam while retaining metadata preflight. Smoke tests are additive and can be marked or skipped only if they expose an environment fixture issue, not to hide product regressions.

## Post-Design Constitution Re-Check

- **Modular Monorepo Boundaries**: Design assigns runtime, gateway, catalog, validation, API, and plugin responsibilities to existing package boundaries. (Pass)
- **Offline-First Mandate**: Fast tests use mocks/fakes; Docker/network validation is opt-in and documented. (Pass)
- **Container Strategy**: Clean-container validation remains per-MCP and does not add MCP-specific host software to the base image. (Pass)
- **Agent Abstraction**: Hermes is default provider through a registry, not a hardcoded API boot dependency. (Pass)
- **3-Tier Testing**: Tasks include unit/contract tests and a minimal system smoke suite. (Pass)
- **API Compatibility**: Contracts state existing response shapes must remain the compatibility baseline. (Pass)

