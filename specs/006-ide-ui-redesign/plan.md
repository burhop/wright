# Implementation Plan: IDE UI Redesign

**Branch**: `005-engineering-workspace` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-ide-ui-redesign/spec.md`

## Summary

Redesign the wright console UI to resemble a multi-pane IDE layout similar to VS Code. Introduce a vertical Activity Bar on the far-left, a collapsible Left Sidebar (Workspace Explorer / Tools Marketplace), a central Tabbed Editor View supporting multi-type file previews (STL, Images, Syntax-highlighted Code with auto-save updates), and a collapsible Right Sidebar for the Hermes Agent chat console. Implement session-specific tools customization enabling/disabling MCP servers per workspace.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 6.0, React 19 (frontend)

**Primary Dependencies**: React 19, Lucide Icons (or standard emojis for console icons), Vanilla CSS, FastAPI >=0.115, Three.js, Pydantic v2

**Storage**: SQLite with WAL mode for session-specific tools configuration updates.

**Testing**: pytest (backend API), Vitest (frontend components), Playwright (E2E panel collapses, tab switches)

**Target Platform**: Linux local host (offline-first execution)

**Project Type**: Web application (modular monorepo)

**Performance Goals**: Sidebar switches <50ms. Tab changes <100ms. 3D renderings <200ms. Database toggles <100ms.

**Constraints**: Bounded to standard Git checkout. Local storage databases only (no background databases like PG).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | FastAPI backend, zero business logic in routes | ✅ Pass | All workspace files and tools toggling code resides inside `WorkspaceManager` class in `packages/core/src/core/workspace.py`. |
| 2 | Modular Monorepo with strict boundaries | ✅ Pass | API routes in `apps/api/`, files logic in `packages/core/`, React layout panels in `apps/web/src/`. |
| 3 | Offline-First Mandate | ✅ Pass | Layout rendering, 3D viewport calculations, and tool states are 100% local. |
| 4 | Agent Abstraction (Adapter Pattern) | ✅ Pass | Right-hand agent sidebar is hot-swappable and leverages the `BaseAgentEngine` framework. |
| 5 | Zero-server databases | ✅ Pass | Config updates saved to existing SQLite `engineering_workspaces` table. |
| 6 | Local authentication | ✅ Pass | Inherits standard JWT session verification headers. |
| 7 | Template Method for tools | ✅ Pass | The Tools Marketplace manages servers inheriting from `BaseTool`. |
| 8 | Atomic design (Tokens → Primitives → Components) | ✅ Pass | IDE sidebar and editor tab elements styled using index.css console tokens. |
| 9 | Tier 1/2/3 testing pyramid | ✅ Pass | Pytest API updates, Vitest components test tabs, Playwright tests verify tripartite panel layouts. |
| 10 | OpenTelemetry tracing + structured JSON logging | ✅ Pass | Every UI action (tab switches, tool toggles, file saves) traces telemetry spans. |
| 11 | Phase isolation + branch discipline | ✅ Pass | Working on feature specification and plan before tasks execution. |

## Project Structure

### Documentation (this feature)

```text
specs/006-ide-ui-redesign/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── checklists/
    └── requirements.md # Quality validation checklist
```

### Source Code (repository root)

```text
packages/core/
└── src/core/
    └── workspace.py           # [MODIFY] Add tools list management and save file content logic

apps/api/
├── src/api/
│   └── routers/
│       └── workspace.py       # [MODIFY] Add GET/POST /workspace/config (tools list) and PUT /workspace/files/content (file save)
└── tests/
    └── test_workspace_api.py  # [MODIFY] Write tests verifying tool toggling and PUT file saves

apps/web/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   └── WorkspacePanel.tsx # [MODIFY] Restructure layout to act as Activity Bar + Sidebar drawer + Agent console
│   │   ├── common/
│   │   │   ├── FileEditor.tsx     # [NEW] View/Edit text files with syntax highlighting
│   │   │   ├── EditorTabs.tsx     # [NEW] Render tab list header and dispatch active tab file viewers
│   │   │   └── ToolsMarketplace.tsx # [NEW] Render MCP tools list with session toggle actions
│   └── services/
│       └── workspace-service.ts   # [MODIFY] Add api methods for tool config and file saving
```

**Structure Decision**: Exposes layout operations inside `WorkspacePanel.tsx` using Vanilla CSS. Modularizes file-type views (`FileEditor.tsx`, `EditorTabs.tsx`, `ToolsMarketplace.tsx`) under `/common/` to prevent workspace drawer clutter. Exposes API endpoints under `apps/api/src/api/routers/workspace.py`.
