# Implementation Plan: Pluggable Viewer Panel API

**Branch**: `023-viewer-panel-api` | **Date**: 2026-06-09 | **Spec**: [specs/023-viewer-panel-api/spec.md](spec.md)

**Input**: Feature specification from `/specs/023-viewer-panel-api/spec.md`

## Summary

Implement the pluggable viewer panel API framework supporting registry resolution matching, center editor tabs, and viewer lifecycles (opening, dirty state, undo/redo transactions, watchdog monitoring, and developer inspection). Connect initial adapters for Monaco/CodeMirror code editor, WebGL 3D graphics, PDF.js, and sandboxed iframes.

## Technical Context

**Language/Version**: React 19 (TypeScript) / Python 3.11 (FastAPI backend)

**Primary Dependencies**: React 19, react-router-dom, Three.js (3D graphics rendering), Monaco Editor / CodeMirror (code editing), PDF.js (document previewing)

**Storage**: SQLite (`state.db`) backend storage for file descriptors and saved state indices

**Testing**: Playwright (UI integration/E2E), Vitest (React store & component unit tests), pytest (FastAPI routers)

**Target Platform**: Linux server/local execution (offline-capable)

**Project Type**: Modular Monorepo Web Application

**Performance Goals**: Rendering/resolving views <50ms; watchdog detection within 5s; teardown & cleanup under 100ms

**Constraints**: Compliant with Virtual Mechanical Engineer Constitution (zero-server SQLite database, offline-first execution, strict design tokens, and mandatory `data-testid` attributes)

**Scale/Scope**: 5 viewer types (3D, Python/text, PDF, Markdown, IFrame) resolved dynamically via `ViewerRegistry`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **FastAPI strict typing**: YES. All new endpoints will use native Pydantic data schemas.
- **Offline-First Mandate**: YES. All viewer scripts (Three.js, Monaco, PDF.js) are bundled locally.
- **Relational Data in SQLite (WAL)**: YES. All database storage utilizes local SQLite.
- **Component Test IDs**: YES. Every new tab and container features unique `data-testid` attributes.
- **Structured JSON Logging**: YES. Logging output routes through backend `structlog`.

## Project Structure

### Documentation (this feature)

```text
specs/023-viewer-panel-api/
├── plan.md              # This file
├── research.md          # Research findings and decisions
├── data-model.md        # Entities definition
├── quickstart.md        # Validation guide
├── contracts/
│   └── api-contracts.md # Interface and message contracts
└── tasks.md             # Implementation tasks
```

### Source Code

```text
apps/api/src/api/
├── routers/
│   └── workspace.py            # File save/revert/backup endpoints
└── schemas/
    └── workspace.py            # Pydantic schemas for file content and metadata

apps/web/src/
├── components/
│   └── chat/
│       ├── WorkspacePanel.tsx  # Central panel mounting logic
│       ├── EditorTabs.tsx      # Tab buttons and active view manager
│       └── ThreeDViewer.tsx    # Three.js 3D WebGL viewer component
├── services/
│   ├── viewer-panel/
│   │   ├── registry.ts         # ViewerRegistry and registration
│   │   ├── panel-host.ts       # PanelHost implementation and messages proxy
│   │   └── providers/          # Initial viewer adapters (3D, Code, PDF, IFrame)
│   │       ├── code-provider.ts
│   │       ├── threed-provider.ts
│   │       ├── pdf-provider.ts
│   │       └── iframe-provider.ts
│   └── workspace-service.ts    # Fetch and save payload callers
```

**Structure Decision**: Monorepo Web Application layout (Option 2 aligned). All API code lives in `apps/api` and frontend SPA code lives in `apps/web`.

## Complexity Tracking

*No complexity violations present. No exceptions required.*
