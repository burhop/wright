# Implementation Plan: MCP & Tool Registry

**Branch**: `003-mcp-tool-registry` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-mcp-tool-registry/spec.md`

## Summary

Integrate the Model Context Protocol (MCP) ecosystem into the Wright application. This will be accomplished by creating a backend tool registry database schema using SQLite, writing an adapter to spawn stdio CLI subprocesses and manage remote SSE endpoint configurations, exposing `/api/mcp/*` endpoints in the FastAPI server, building a visual "Tool Registry" page in the React frontend (supporting search, categories, and dynamic custom CLI/SSE registrations), and integrating WebMCP viewport-state listeners and MCP-UI progress cards inside the chat transcript.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 6.0 (frontend)

**Primary Dependencies**: FastAPI >=0.115, Pydantic v2, httpx (for SSE client streams), React 19, react-router-dom 7, Vite 8

**Storage**: Local SQLite database (WAL mode) for configuration metadata persistence.

**Testing**: pytest (backend), Vitest (frontend component), Playwright (E2E)

**Target Platform**: Linux local machine (offline-first execution)

**Project Type**: Web application (monorepo)

**Performance Goals**: Registry UI render <150ms. Stdio subprocess registration and schema lookup completed in <2 seconds. Visual progress status rendering updates within 100ms.

**Constraints**: Air-gapped compatible (local CLI wrappers). Subprocess execution isolation with 60-second timeouts. OpenTelemetry tracing and structured JSON logging.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | FastAPI backend, zero business logic in routes | ✅ Pass | Routes call `McpRegistry` and `McpEngine` classes, no business logic in router files. |
| 2 | Modular Monorepo with strict boundaries | ✅ Pass | Models and runners in `packages/tool_registry/`, endpoints in `apps/api/`, UI in `apps/web/`. |
| 3 | Offline-first mandate | ✅ Pass | Standard stdio CLI tools execute locally on host, remote SSE connections are optional with fallbacks. |
| 4 | Agent Abstraction (Adapter Pattern) | ✅ Pass | Dynamic schema registration allows hot-swappable tools without hardcoding agent adapters. |
| 5 | Zero-server databases | ✅ Pass | Persisted entirely in existing SQLite state DB. No external DB servers (Postgres/Qdrant) added. |
| 6 | Local authentication | ⬜ N/A | Authentication not modified in scope of this feature. |
| 7 | Template Method for tools | ✅ Pass | Custom tool executables are managed via standard schemas. |
| 8 | Atomic design (Tokens → Primitives → Components) | ✅ Pass | Directory card components follow calm-console color palette tokens. |
| 9 | Tier 1/2/3 testing pyramid | ✅ Pass | Pytest unit tests, Vitest UI cards rendering checks, and Playwright E2E tool add flows. |
| 10 | OpenTelemetry tracing + structured JSON logging | ✅ Pass | trace_id propagated down to subprocess shell invocations, structlog active. |
| 11 | Phase isolation + branch discipline | ✅ Pass | Branch `003-mcp-tool-registry` active, plan approved prior to implementation. |

## Project Structure

### Documentation (this feature)

```text
specs/003-mcp-tool-registry/
├── plan.md              # This file
├── research.md          # Technical decisions and rationales
├── data-model.md        # Database schema definitions
├── quickstart.md        # Developer setup instructions
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── contracts/
    └── api-contracts.md # Endpoints and event shape contracts
```

### Source Code (repository root)

```text
packages/tool_registry/
├── src/tool_registry/
│   ├── __init__.py            # Expose registry classes
│   ├── models.py              # Pydantic schemas for McpServer/McpTool
│   ├── db.py                  # SQLite query operations (WAL inserts, fetches)
│   ├── runners/
│   │   ├── base.py            # BaseRunner interface class
│   │   ├── stdio.py           # subprocess spawn runner with 60s timeout
│   │   └── sse.py             # HTTP SSE connection runner
│   └── manager.py             # McpEngine coordinating server state
└── tests/
    └── test_registry.py       # pytest tests for CLI subprocess spawn and schemas

apps/api/
├── src/api/
│   ├── main.py                # Mount MCP router
│   └── routers/
│       └── mcp.py             # [NEW] /api/mcp/servers and /api/mcp/tools endpoints

apps/web/
├── src/
│   ├── pages/
│   │   └── ToolRegistryPage.tsx # [MODIFY] Replace placeholder page with active Tool Registry UI
│   ├── components/
│   │   └── tools/
│   │       ├── AddToolModal.tsx # [NEW] Modal form for registering CLI/SSE custom servers
│   │       └── ToolCard.tsx     # [NEW] Display card component for a single MCP server
│   ├── services/
│   │   └── mcp-service.ts     # [NEW] REST API calls for server registration and activation
│   └── store/
│       └── tools.tsx          # [NEW] React store/context for tool listings
└── tests/
    ├── ToolRegistry.spec.tsx  # [NEW] Vitest component tests for filtering and status checks
    └── AddToolModal.spec.tsx  # [NEW] Vitest tests for the tool registration inputs

tests/ui-integration/
└── mcp-directory.spec.ts      # [NEW] Playwright integration test: register tool, check active status
```

**Structure Decision**: Exposes Tool Registry logic in a new `packages/tool_registry` python package to preserve strict monorepo boundaries. Exposes `/api/mcp/` routes in the API server by creating a new router module. Overwrites `apps/web/src/pages/ToolRegistryPage.tsx` placeholder with the visual directory grid.

## Complexity Tracking

No constitution violations. Complexity is tracked cleanly under modular monorepo packages.
