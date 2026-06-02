# Implementation Plan: OpenSCAD MCP & 3D Visualization

**Branch**: `004-openscad-mcp` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-openscad-mcp/spec.md`

## Summary

Integrate the `quellant/openscad-mcp` server as a seeded stdio server to let agents generate 3D parametric CAD models. Add `three` to the React frontend (`apps/web`) to implement a WebGL 3D preview viewport inside the Workspace Panel. Enable workspace browsing and 3D file reading by exposing clean directory listing and file streaming endpoints in the FastAPI backend (`apps/api`).

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 6.0 (frontend)

**Primary Dependencies**: FastAPI >=0.115, Pydantic v2, three >=0.170.0 (frontend), @types/three (frontend dev)

**Storage**: Local SQLite database for seed MCP configurations. Structured local workspace directory vault for physical STL/SCAD files.

**Testing**: pytest (backend API), Vitest (frontend rendering), Playwright (E2E file selection)

**Target Platform**: Linux local machine (offline-first execution)

**Project Type**: Web application (monorepo)

**Performance Goals**: Headless render under 3 seconds. Three.js viewport loading under 300ms. Orbit animations >= 60 FPS.

**Constraints**: Air-gapped compatible (uses local `openscad` binary wrapped in `xvfb-run`). All tool runs traced with OpenTelemetry Jaeger.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | FastAPI backend, zero business logic in routes | ✅ Pass | Workspace listing and file reads isolated to `WorkspaceManager` class, routers call it directly. |
| 2 | Modular Monorepo with strict boundaries | ✅ Pass | Viewport in `apps/web/`, endpoints in `apps/api/`, files logic in `packages/core/` or `packages/data_vault/`. |
| 3 | Offline-first mandate | ✅ Pass | OpenSCAD runs locally using headless Xvfb virtual framebuffer. No cloud rendering. |
| 4 | Agent Abstraction (Adapter Pattern) | ✅ Pass | Uses generic MCP StdioRunner to interface with OpenSCAD tools without hardcoding. |
| 5 | Zero-server databases | ✅ Pass | Persisted in existing SQLite. No Postgres or extra containers added. |
| 6 | Local authentication | ⬜ N/A | Authentication not modified in scope of this feature. |
| 7 | Template Method for tools | ✅ Pass | Generic JSON-RPC calls are dispatched via BaseRunner. |
| 8 | Atomic design (Tokens → Primitives → Components) | ✅ Pass | 3D canvas viewport integrates into calm-console theme using theme token colors. |
| 9 | Tier 1/2/3 testing pyramid | ✅ Pass | Pytest API unit tests, Vitest canvas checks, Playwright UI select checks. |
| 10 | OpenTelemetry tracing + structured JSON logging | ✅ Pass | `trace_id` propagated to file indexing and subprocess runs. |
| 11 | Phase isolation + branch discipline | ✅ Pass | Branch `004-openscad-mcp` is active. Spec completed. |

## Project Structure

### Documentation (this feature)

```text
specs/004-openscad-mcp/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Headless Xvfb and Three.js decisions
├── data-model.md        # Seed configurations and workspace node models
├── quickstart.md        # Setup instructions
└── contracts/
    └── api-contracts.md # Endpoints contract details
```

### Source Code (repository root)

```text
packages/core/
└── src/core/
    └── workspace.py           # [NEW] WorkspaceManager listing and read logic

apps/api/
├── src/api/
│   ├── main.py                # Mount workspace router
│   ├── config.py              # [MODIFY] Self-configure default OPENSCAD_PATH env var
│   ├── database/
│   │   └── migrate.py         # [MODIFY] Seed OpenSCAD MCP server metadata
│   └── routers/
│       └── workspace.py       # [NEW] /api/workspace/files and /api/workspace/files/content
└── tests/
    └── test_workspace_api.py  # [NEW] Pytest for directory traversal protection and file streaming

apps/web/
├── package.json               # [MODIFY] Add three and @types/three dependencies
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   └── WorkspacePanel.tsx # [MODIFY] Add 3D tab/pane layout and file watch loop
│   │   └── common/
│   │       └── ThreeDViewer.tsx   # [NEW] Canvas component initializing Three.js & STLLoader
│   └── services/
│       └── workspace-service.ts   # [NEW] REST client for workspace directory and content fetch
└── tests/
    └── ThreeDViewer.spec.tsx  # [NEW] Vitest component checks for WebGL canvas mounting
```

**Structure Decision**: Exposes Workspace directory operations in a new `workspace.py` helper in `packages/core` to respect boundaries. Creates `/api/workspace/` routes in the API server by creating a new router module. Mounts Three.js canvas under `apps/web/src/components/common/ThreeDViewer.tsx`.

## Complexity Tracking

No constitution violations. Complexity is tracked cleanly under modular monorepo packages.
