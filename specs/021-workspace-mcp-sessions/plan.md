# Implementation Plan: Workspace MCP & Session Isolation

**Branch**: `021-workspace-mcp-sessions` | **Date**: 2026-06-09 | **Spec**: [spec.md](file:///home/burhop/repos/wright/specs/021-workspace-mcp-sessions/spec.md)

**Input**: Feature specification from `/specs/021-workspace-mcp-sessions/spec.md`

## Summary
Improve the workspace creation and management flow by allowing users to create human-readable, named workspace directories on disk rather than UUIDs. Establish session isolation: sessions are associated with their workspace directory path and only sessions belonging to the active workspace are selectable in the UI. Provide an automated cleanup utility to purge test workspaces.

---

## Technical Context

**Language/Version**: Python 3.13, TypeScript, Node.js 22

**Primary Dependencies**: FastAPI, Pydantic v2, SQLite, React, React Router

**Storage**: SQLite WAL mode (DATABASE_PATH), local filesystem (directories created under `~/workspace/`)

**Testing**: pytest (backend unit/integration tests), Playwright (tests under `tests/ui-integration/`)

**Target Platform**: Dockerized Linux container (Ubuntu 26.04 base)

**Project Type**: Monorepo Web Application

**Performance Goals**: Workspace loading and session filtering under 200ms.

**Constraints**: Air-gapped/offline-first compatibility (all path creation, git init, and tool synchronization must run locally).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: Verified. API endpoints in `/apps/api/` will handle routing and delegates immediately to `/packages/core/` and `/packages/agent_adapters/`.
- **Offline-First Mandate**: Verified. The workspace creation, directory creation, git initialization, and tool toggle functions are entirely local.
- **Zero-Server Databases**: Verified. All tracking is done via SQLite database and the file system.
- **Agent Abstraction (Adapter Pattern)**: Verified. Changes to workspace and session management utilize `BaseAgentEngine` abstract methods through dependency injection.
- **UI Testing Requirement**: Verified. All interactive elements (e.g. workspace creation, session switching) must have `data-testid` attributes.

---

## Project Structure

### Documentation (this feature)

```text
specs/021-workspace-mcp-sessions/
├── plan.md              # This file
├── research.md          # Design decisions and rationales
├── data-model.md        # Database schema details and path sanitization rules
├── quickstart.md        # Verification commands and scripts
└── contracts/
    └── api-contracts.md # API endpoints request/response schemas
```

### Source Code (repository root)

```text
apps/api/
├── src/api/
│   ├── routers/
│   │   ├── agent.py      # Session list & creation endpoints
│   │   └── workspace.py  # Workspace CRUD endpoints
│   └── schemas/
│       └── workspace.py  # Pydantic schemas for workspaces
└── tests/
    └── test_workspace_mcp.py  # New backend unit tests

apps/web/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   └── WorkspacePanel.tsx  # Session list render and toggle
│   │   └── common/
│   │       └── CreateWorkspaceModal.tsx # Workspace create form
│   └── services/
│       ├── agent-service.ts
│       └── workspace-service.ts

packages/core/
├── src/core/
│   └── workspace.py  # DB and file-system helpers

scripts/
└── cleanup-workspaces.py  # New python cleanup script
```

**Structure Decision**: Monorepo project structure where changes span both the FastAPI API and the React Web UI.

---

## Proposed Code Changes

### [FastAPI Backend API]

#### [MODIFY] [workspace.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/workspace.py)
* Update `create_workspace_endpoint`:
  1. Generate sanitized path from name under parent workspace folder (`~/workspace/<sanitized-name>`).
  2. Query database/disk for existing workspace. If folder path or DB record exists, raise HTTPException `400 Bad Request`.
  3. Run `os.makedirs` and instantiate `WorkspaceManager(local_path)` to initialize git.
  4. Create agent session via engine.
  5. Save to database using `create_workspace_from_dashboard`.
* Update `/files` root folder name resolution to display workspace display name.

#### [MODIFY] [agent.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/agent.py)
* Update `list_agent_sessions` to accept `workspace_id: Optional[str] = None`.
* If `workspace_id` is supplied, lookup `local_path` for that workspace in SQLite, then filter the list of sessions returned by `engine.list_sessions()` to only include sessions whose `workspace` path matches `local_path`.

#### [MODIFY] [workspace.py](file:///home/burhop/repos/wright/apps/api/src/api/schemas/workspace.py)
* Update `WorkspaceCreateRequest` to make `local_path` optional since it is now derived and created backend-side.

---

### [React Frontend App]

#### [MODIFY] [agent-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/agent-service.ts)
* Update `listSessions` method to accept an optional `workspaceId` and append it as a query parameter `workspace_id` in the API call.

#### [MODIFY] [sessions.tsx](file:///home/burhop/repos/wright/apps/web/src/store/sessions.tsx)
* Update `hydrateSessions` or the state structure so that the session list is refreshed/filtered based on the active `workspaceId`.

#### [MODIFY] [WorkspacePanel.tsx](file:///home/web/src/components/chat/WorkspacePanel.tsx)
* Ensure that the session selector dropdown only displays sessions matching the current workspace's filtered list.
* Update double-click behavior or switcher actions to call `POST /api/workspace/by-id/{workspaceId}/session` to save the active session mapping on the backend.

---

### [Database & CLI]

#### [NEW] [cleanup-workspaces.py](file:///home/burhop/repos/wright/scripts/cleanup-workspaces.py)
* Script to wipe all directory folders inside the application workspace path and delete all entries in `engineering_workspaces`, `agent_contexts`, and `chat_messages` tables.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No constitution check violations.*

