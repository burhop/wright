# Implementation Plan: Engineering MCP Catalog

**Branch**: `034-engineering-mcp-catalog` | **Date**: 2026-06-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/034-engineering-mcp-catalog/spec.md`

## Summary

Implement the engineering MCP research handoff as a statused, testable catalog that preserves uncertain entries while making installability, platform support, dependency limits, safety defaults, and follow-up work explicit. The implementation will extend the existing Wright plugin catalog, `tool_registry` models/API, and current `ToolRegistryPage`/`ToolCard` UI instead of introducing a separate plugin-manager layout. The first executable validation target is one Ubuntu-based Docker environment; host-dependent MCPs may pass validation with a clear dependency-missing diagnostic.

## Technical Context

**Language/Version**: Python >=3.11 for `packages/tool_registry`, `apps/api`, and `hermes-plugin-wright`; TypeScript 6.0 for `apps/web`

**Primary Dependencies**: Pydantic, FastAPI, SQLite, structlog, pytest, React 19, Vite 8, Vitest 4, Playwright, Docker Compose

**Storage**: Existing local SQLite MCP registry for runtime servers; YAML seed catalog in `hermes-plugin-wright/catalog.yaml`; generated local follow-up records under `docs/mcp-catalog/followups/`

**Testing**: `uv run pytest`, targeted Python package tests, `npm run test --workspace=apps/web`, `npm run build --workspace=apps/web`, Playwright UI integration where useful, Docker smoke validation for the Ubuntu target

**Target Platform**: First-class validation in a single Ubuntu x64 Docker container; schema records Windows 11 x64, Linux x64, Linux ARM64, macOS x64, and macOS ARM64

**Project Type**: Modular monorepo with FastAPI backend, Python registry/plugin packages, React frontend, and Docker appliance scripts

**Performance Goals**: Catalog load and sort remain interactive for 100+ entries; validation can classify the seeded catalog without hanging on blocked or host-dependent entries; UI cards do not shift layout when metadata is expanded

**Constraints**: Preserve offline-first behavior; do not require cloud credentials, paid CAD software, GUI apps, or hardware to pass the initial container validation; do not auto-enable high-risk or safety-critical MCPs; do not weaken existing tests

**Scale/Scope**: Seed and normalize the current engineering MCP catalog entries, add installability/status fields, implement validation classification and follow-up generation, and update current UI cards/page to display the new metadata

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Backend/API remains in `apps/api`, reusable registry logic in `packages/tool_registry`, plugin catalog logic in `hermes-plugin-wright`, UI in `apps/web`. (Pass)
- **Offline-First Mandate**: Core catalog browsing, classification, and follow-up record generation run locally. Cloud MCP entries are represented but not required for validation without credentials. (Pass)
- **Container Strategy**: First validation target is the existing Ubuntu-based Docker appliance; host software gaps are classified explicitly. (Pass)
- **Engineering Tooling Protocol**: MCP install/validation is command-driven and does not require GUI automation for the agent. GUI/CAD host dependencies are detected or reported as unavailable. (Pass)
- **UI Component Layers**: Existing page/card components are extended using existing design tokens and stable `data-testid` attributes. (Pass)
- **3-Tier Testing**: Python model/service tests, React component tests, API tests, UI integration tests, and Docker smoke validation are planned. (Pass)
- **Observability**: Validation and API operations keep structured logging/tracing conventions already present in the API. (Pass)
- **Branch Discipline**: Work is on `034-engineering-mcp-catalog`. (Pass)
- **Manual Gating**: User explicitly requested the full specify-plan-tasks-implement sprint in this turn. (Pass)

## Project Structure

### Documentation (this feature)

```text
specs/034-engineering-mcp-catalog/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- catalog-contract.md
|   |-- validation-contract.md
|   |-- followup-contract.md
|   `-- ui-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
hermes-plugin-wright/
|-- catalog.yaml
|-- catalog.py
|-- schemas.py
`-- tests/test_catalog.py

packages/tool_registry/
|-- src/tool_registry/models.py
|-- src/tool_registry/db.py
|-- src/tool_registry/manager.py
|-- src/tool_registry/mcp_catalog.py
|-- src/tool_registry/mcp_validation.py
|-- src/tool_registry/mcp_followups.py
`-- tests/

apps/api/
|-- src/api/routers/mcp.py
`-- tests/test_mcp_api.py

apps/web/
|-- src/services/mcp-service.ts
|-- src/store/tools.tsx
|-- src/components/pages/ToolRegistryPage.tsx
|-- src/components/tools/ToolCard.tsx
|-- tests/ToolRegistry.spec.tsx
`-- src/test/ToolRegistryLayout.spec.tsx

docs/mcp-catalog/
|-- engineering_mcp_research_handoff.md
`-- followups/

tests/ui-integration/tool-registry.spec.ts
docker-compose.test.yml
```

**Structure Decision**: Extend the current catalog and registry surfaces. The handoff's conceptual loader/verifier/installer/runtime/safety/UI layers map to existing modules rather than becoming a new top-level subsystem.

## Complexity Tracking

No constitution violations detected.

## Phase 0 Research

See [research.md](research.md).

## Phase 1 Design

See [data-model.md](data-model.md), [contracts/](contracts/), and [quickstart.md](quickstart.md).

## Post-Design Constitution Re-Check

- **Modular Monorepo Boundaries**: Design places catalog parsing in plugin/registry packages, API exposure in `apps/api`, and display-only UI concerns in `apps/web`. (Pass)
- **Offline-First Mandate**: Broken/cloud/host-dependent entries remain visible with local metadata and do not require network access to classify as blocked. (Pass)
- **3-Tier Testing**: Tasks will require unit, API, component, UI integration, and Docker smoke tests before implementation completion. (Pass)
- **Safety**: High-risk and safety-critical servers default disabled and blocked from blind install. (Pass)
