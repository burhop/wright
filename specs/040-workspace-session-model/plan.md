# Implementation Plan: Workspace Session Model

**Branch**: `040-workspace-session-model` | **Date**: 2026-07-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/040-workspace-session-model/spec.md`

## Summary

Wright currently treats `engineering_workspaces.session_id` as the workspace identity for many operations, which collapses the user's intended model of one workspace owning many chat sessions. The implementation introduces an explicit workspace-to-agent-session association, migrates existing one-session workspace data into that association, changes workspace MCP/tool APIs to resolve through workspace identity, and adjusts frontend state so switching chat sessions updates only the transcript.

## Technical Context

**Language/Version**: Python 3.13 backend packages and FastAPI API; TypeScript 6.0 / React 19 frontend.

**Primary Dependencies**: FastAPI, Pydantic, SQLite/WAL, workspace_service package, core workspace package, tool_registry package, React, Vite, Vitest, pytest.

**Storage**: Local SQLite state database. Existing `engineering_workspaces` table remains for compatibility; new association state records zero to many agent sessions per workspace.

**Testing**: pytest for backend/database/API behavior; Vitest and React Testing Library for frontend session switching behavior.

**Target Platform**: Local Wright web app running against the local Wright FastAPI backend and Hermes gateway.

**Project Type**: Modular monorepo web application with backend API, shared Python packages, and frontend app.

**Performance Goals**: Workspace load and session switching should remain interactive; session listing should complete within the current backend list-session latency envelope and avoid extra full workspace reloads on chat-only selection.

**Constraints**: Must preserve existing local data, must remain offline-first, must avoid hardcoding Hermes-specific assumptions beyond the existing agent adapter boundary, and must not require a database server.

**Scale/Scope**: Local single-user installations with multiple workspaces and multiple sessions per workspace; target at least dozens of sessions per workspace without UI state bleed.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Pass. Data helpers remain in `packages/core`, workflow logic in `packages/workspace_service`, API routing in `apps/api`, and UI state in `apps/web`.
- **Offline-First Mandate**: Pass. Uses local SQLite and local agent/MCP processes only.
- **Agent Abstraction**: Pass. The model stores generic agent session associations and uses existing `BaseAgentEngine` APIs.
- **Zero-Server Databases**: Pass. SQLite remains the only relational store.
- **Component Layers**: Pass. UI changes are scoped to existing workspace/chat components and service layer.
- **Structured Logging / Traceability**: Pass. New backend flows will use existing route/service logging and traced route/service entry points where present.
- **Branch Discipline**: Pass. Work is on `040-workspace-session-model`, not `main`.

## Project Structure

### Documentation (this feature)

```text
specs/040-workspace-session-model/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── workspace-session-api.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/api/
├── src/api/database/migrate.py
├── src/api/routers/agent.py
├── src/api/routers/workspace.py
└── tests/test_workspace_api.py

packages/core/src/core/workspace.py
packages/workspace_service/src/workspace_service/
├── models.py
└── service.py

apps/web/
├── src/components/chat/MessageComposer.tsx
├── src/components/chat/WorkspacePanel.tsx
├── src/components/pages/WorkspacePage.tsx
├── src/services/workspace-service.ts
├── src/services/agent-service.ts
├── src/store/sessions.tsx
└── tests/WorkspacePanelSessions.spec.tsx
```

**Structure Decision**: Use the existing modular monorepo boundaries. The core package owns SQLite persistence helpers, workspace_service owns workspace/session orchestration, API routers expose thin endpoints, and the React app consumes workspace-scoped APIs.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design & Contracts

See [data-model.md](data-model.md), [contracts/workspace-session-api.md](contracts/workspace-session-api.md), and [quickstart.md](quickstart.md).

## Constitution Check - Post-Design

- **Modular Monorepo Boundaries**: Pass. The design keeps data, orchestration, API, and UI responsibilities separated.
- **Offline-First Mandate**: Pass. Migration and session association are local-only.
- **Agent Abstraction**: Pass. Session association stores `agent_id` and does not assume the agent implementation owns workspace configuration.
- **Zero-Server Databases**: Pass. SQLite migration only.
- **UI Component Layers**: Pass. Existing components are adjusted; no new design system is introduced.
- **Testing Pyramid**: Pass. Backend persistence/API tests plus frontend component tests cover the regression.

## Complexity Tracking

No constitution violations identified.
