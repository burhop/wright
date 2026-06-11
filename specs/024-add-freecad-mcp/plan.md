# Implementation Plan: FreeCAD MCP Server Integration

**Branch**: `024-add-freecad-mcp` | **Date**: 2026-06-09 | **Spec**: [specs/024-add-freecad-mcp/spec.md](spec.md)

**Input**: Feature specification from `/specs/024-add-freecad-mcp/spec.md`

## Summary

Integrate the `freecad-mcp` server as an installable option in the Engineering Tool Registry. Install the FreeCAD kernel natively on the GB10 host using Snap, and bundle the FreeCAD headless engine inside the Docker container by extracting the official `aarch64` AppImage.

## Technical Context

**Language/Version**: React 19 (TypeScript) / Python 3.13 (FastAPI backend)

**Primary Dependencies**: `freecad` snap package, `FreeCAD_1.0.0-conda-Linux-aarch64-py311.AppImage`, `freecad-mcp` PyPI server package

**Storage**: SQLite (`state.db`) using `mcp_servers` and `mcp_tools` tables

**Testing**: pytest (FastAPI routers), Playwright (UI integration/E2E check)

**Target Platform**: Dell GB10 host (arm64/aarch64, Ubuntu 24.04), Docker container (Ubuntu 26.04)

**Project Type**: Modular Monorepo Web Application

**Performance Goals**: `freecad_status` checks <500ms, mesh conversion <5s

**Constraints**: Offline-first execution, no FUSE/nested snapd inside Docker (mitigated by AppImage extraction), structured JSON logging via `structlog`.

**Scale/Scope**: 46+ FreeCAD tools dynamically resolved and registered via FastMCP gateway.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **FastAPI strict typing**: YES. All router integrations leverage native Pydantic models.
- **Offline-First Mandate**: YES. Once FreeCAD is installed, execution of CAD commands is entirely local on the GB10 host and within the Docker container.
- **Relational Data in SQLite (WAL)**: YES. Server registration and tool discovery results are persisted in the local SQLite database.
- **Component Test IDs**: YES. Tool registry page cards use standard `data-testid` attributes.
- **Structured JSON Logging**: YES. Logs for server start/stop and tool execution utilize the structured `structlog` system.

## Project Structure

### Documentation (this feature)

```text
specs/024-add-freecad-mcp/
├── plan.md              # This file
├── spec.md              # Specification file
├── research.md          # Research findings
├── data-model.md        # DB schemas and seeded attributes
├── quickstart.md        # Manual verification guide
└── checklists/
    └── requirements.md  # Spec quality validation checklist
```

### Source Code

```text
apps/api/src/api/
└── database/
    └── migrate.py              # [MODIFY] Seed the FreeCAD catalog entry

docker/
└── Dockerfile                  # [MODIFY] Download and extract FreeCAD AppImage, configure PATH
```

**Structure Decision**: Monorepo Web Application layout. The database migrations seed the catalog, and the Dockerfile bundles the headless FreeCAD client.

## Complexity Tracking

*No complexity violations present. No exceptions required.*
