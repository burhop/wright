# Implementation Plan: Workspace Dashboard UX

**Branch**: `007-workspace-dashboard-ux` | **Date**: 2026-06-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-workspace-dashboard-ux/spec.md`

## Summary

Redesign the Wright console dashboard to display recent workspaces with "Create Workspace" and "View all workspaces" buttons, replace the standalone "Agent Chat" route with a workspace-scoped `/workspace/:id` route, add tool installation auto-detection, and implement generic agent context save/load API methods. The core change shifts the user mental model from "Agent Chat sessions" to "Workspaces" as the primary navigation unit.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 6.0, React 19 (frontend)

**Primary Dependencies**: React 19, react-router-dom v6, Vanilla CSS, FastAPI >=0.115, Pydantic v2, httpx

**Storage**: SQLite with WAL mode (`engineering_workspaces` table, `mcp_servers` table)

**Testing**: pytest (backend API), Vitest (frontend components), Playwright (E2E workspace navigation)

**Target Platform**: Linux local host (offline-first execution)

**Project Type**: Web application (modular monorepo)

**Performance Goals**: Workspace list loads <500ms. Workspace switch <2s. Tool installation detection <1s at startup.

**Constraints**: Offline-first. No background databases. Single-machine, single-user.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | FastAPI backend, zero business logic in routes | ✅ Pass | All workspace creation, listing, and context logic resides in `core/workspace.py` and `agent_adapters/`. Routes only dispatch. |
| 2 | Modular Monorepo with strict boundaries | ✅ Pass | API routes in `apps/api/`, core workspace logic in `packages/core/`, agent adapters in `packages/agent_adapters/`, React UI in `apps/web/`. |
| 3 | Offline-First Mandate | ✅ Pass | Workspace listing, creation, and tool detection are 100% local SQLite + filesystem operations. |
| 4 | Agent Abstraction (Adapter Pattern) | ✅ Pass | New `save_context`/`load_context` methods added to `BaseAgentEngine` abstract class. Hermes adapter implements no-op. |
| 5 | Zero-server databases | ✅ Pass | All data stored in existing SQLite database with WAL mode. |
| 6 | Local authentication | ✅ Pass | Inherits existing JWT session verification headers. |
| 7 | Template Method for tools | ✅ Pass | Tool installation detection added as a method on the existing tool registry pattern. |
| 8 | Atomic design (Tokens → Primitives → Components) | ✅ Pass | Dashboard components use existing CSS design tokens. New components follow the same pattern. |
| 9 | Tier 1/2/3 testing pyramid | ✅ Pass | Pytest for backend workspace/create endpoints, Vitest for dashboard component, Playwright for E2E workspace navigation. |
| 10 | OpenTelemetry tracing + structured JSON logging | ✅ Pass | Structured JSON logging via `logger` in all new backend functions. |
| 11 | Phase isolation + branch discipline | ✅ Pass | Working on `007-workspace-dashboard-ux` branch; plan before implementation. |

## Project Structure

### Documentation (this feature)

```text
specs/007-workspace-dashboard-ux/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model output
├── contracts/           # Phase 1 API contracts
│   └── workspace-api.md
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (repository root)

```text
packages/core/
└── src/core/
    └── workspace.py                    # [MODIFY] Add create_workspace_from_dashboard(), add workspace_name column support

packages/agent_adapters/
└── src/agent_adapters/
    ├── base.py                         # [MODIFY] Add save_context/load_context abstract methods
    └── hermes.py                       # [MODIFY] Implement save_context/load_context as no-ops

apps/api/
├── src/api/
│   ├── routers/
│   │   └── workspace.py               # [MODIFY] Add POST /create endpoint, add GET /workspace/:id endpoint
│   └── database/
│       └── migrate.py                  # [MODIFY] Add workspace_name column migration, add agent_contexts table
└── tests/
    └── test_workspace_api.py           # [MODIFY] Add tests for create, context save/load

apps/web/
├── src/
│   ├── App.tsx                         # [MODIFY] Replace /agent-chat with /workspace/:id route
│   ├── components/
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx       # [MODIFY] Replace dropdown with Create button, add View All button, fix workspace list
│   │   │   ├── AgentChatPage.tsx       # [DELETE] Remove standalone agent chat page
│   │   │   └── WorkspacePage.tsx       # [NEW] Workspace-scoped page that wraps WorkspacePanel with URL param
│   │   ├── chat/
│   │   │   └── WorkspacePanel.tsx      # [MODIFY] Accept workspaceId prop, scope context to workspace
│   │   └── common/
│   │       └── CreateWorkspaceModal.tsx # [NEW] Modal dialog for workspace creation form
│   ├── services/
│   │   ├── workspace-service.ts        # [MODIFY] Add createWorkspace(), getWorkspace() methods
│   │   └── agent-service.ts            # [MODIFY] Add saveContext(), loadContext() methods
│   └── store/
│       └── sessions.tsx                # [MODIFY] Scope localStorage key by workspaceId
└── tests/
    └── ui-integration/
        └── dashboard.spec.ts           # [MODIFY] Add tests for workspace list, create button, navigation
```

**Structure Decision**: Follows the existing modular monorepo layout. The key change is replacing `AgentChatPage` with `WorkspacePage` which extracts the workspace ID from the URL and passes it to `WorkspacePanel`. The `CreateWorkspaceModal` is a new reusable dialog component under `/common/`.

## Complexity Tracking

No constitution violations.

---

## Proposed Changes (by Component)

### 1. Core Workspace Logic (`packages/core`)

#### [MODIFY] [workspace.py](file:///home/burhop/repos/wright/packages/core/src/core/workspace.py)

- Add `create_workspace_from_dashboard(db_path, name, local_path)` function that:
  - Generates a `workspace_id` (UUID)
  - Generates a `session_id` (UUID) — every workspace needs one for the agent
  - Validates `local_path` exists on disk
  - Inserts into `engineering_workspaces` with the given name
  - Returns the full workspace dict
- Add `get_workspace_by_id(db_path, workspace_id)` function
- Add `save_agent_context(db_path, workspace_id, context_json)` and `load_agent_context(db_path, workspace_id)` functions that read/write from a new `agent_contexts` table

---

### 2. Agent Adapters (`packages/agent_adapters`)

#### [MODIFY] [base.py](file:///home/burhop/repos/wright/packages/agent_adapters/src/agent_adapters/base.py)

- Add two new abstract methods to `BaseAgentEngine`:
  - `async def save_context(self, session_id: str, workspace_id: str) -> bool`
  - `async def load_context(self, session_id: str, workspace_id: str) -> dict | None`

#### [MODIFY] [hermes.py](file:///home/burhop/repos/wright/packages/agent_adapters/src/agent_adapters/hermes.py)

- Implement `save_context` and `load_context` as no-ops (Hermes persists context server-side automatically)

---

### 3. API Layer (`apps/api`)

#### [MODIFY] [workspace.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/workspace.py)

- Add `POST /api/workspace/create` endpoint:
  - Request: `{ name: str, local_path: str }`
  - Response: `WorkspaceListEntry` (the created workspace)
  - Calls `create_workspace_from_dashboard()` from core
- Add `GET /api/workspace/{workspace_id}` endpoint:
  - Returns full workspace info for a given ID
- Add `POST /api/workspace/{workspace_id}/context/save` and `GET /api/workspace/{workspace_id}/context/load` endpoints

#### [MODIFY] [migrate.py](file:///home/burhop/repos/wright/apps/api/src/api/database/migrate.py)

- Add `workspace_name` column to `engineering_workspaces` table (TEXT, nullable, for display)
- Add `agent_contexts` table: `workspace_id TEXT PRIMARY KEY, context_data TEXT, updated_at INTEGER`
- Add startup tool detection: query `mcp_servers`, check if each tool's binary exists on `$PATH`, update `is_installed`

---

### 4. Frontend — Routing & Pages (`apps/web`)

#### [MODIFY] [App.tsx](file:///home/burhop/repos/wright/apps/web/src/App.tsx)

- Remove `AgentChatPage` import
- Add `WorkspacePage` import
- Replace `<Route path="/agent-chat" ...>` with `<Route path="/workspace/:workspaceId" ...>`
- Keep `/agent-chat` as a redirect to `/` for backward compatibility

#### [NEW] [WorkspacePage.tsx](file:///home/burhop/repos/wright/apps/web/src/components/pages/WorkspacePage.tsx)

- Extract `workspaceId` from URL params via `useParams()`
- Fetch workspace info from `GET /api/workspace/{workspaceId}`
- Pass `workspaceId` and `sessionId` to `WorkspacePanel` as props
- Show "Workspace not found" state if invalid ID

#### [DELETE] [AgentChatPage.tsx](file:///home/burhop/repos/wright/apps/web/src/components/pages/AgentChatPage.tsx)

- Remove this file entirely. Its functionality is replaced by `WorkspacePage.tsx`.

---

### 5. Frontend — Dashboard (`apps/web`)

#### [MODIFY] [DashboardPage.tsx](file:///home/burhop/repos/wright/apps/web/src/components/pages/DashboardPage.tsx)

- **Remove** the dropdown workspace selector (lines 125-228)
- **Add** a "Create Workspace" button prominently at the top of the workspace panel
- **Fix** the workspace list: ensure `recentWorkspaces` renders correctly when data exists
- **Update** workspace click handler: navigate to `/workspace/{workspace_id}` instead of `/agent-chat`
- **Add** "View all workspaces" button at the bottom of the recent list (navigates to a full list view or scrolls the list)
- **Remove** the "Hermes Agent" card from the feature grid (replaced by workspace-based navigation)
- **Keep** Tool Registry and File Vault cards

#### [NEW] [CreateWorkspaceModal.tsx](file:///home/burhop/repos/wright/apps/web/src/components/common/CreateWorkspaceModal.tsx)

- Modal dialog with:
  - Workspace name input (text)
  - Project directory path input (text)
  - "Create" and "Cancel" buttons
- On submit: calls `workspaceService.createWorkspace(name, path)`
- On success: navigates to `/workspace/{new_workspace_id}`
- Validates: name not empty, path not empty

---

### 6. Frontend — Services & State (`apps/web`)

#### [MODIFY] [workspace-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/workspace-service.ts)

- Add `createWorkspace(name: string, localPath: string): Promise<WorkspaceInfo>` method
- Add `getWorkspace(workspaceId: string): Promise<WorkspaceInfo>` method
- Add `workspace_name` field to `WorkspaceInfo` interface

#### [MODIFY] [agent-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/agent-service.ts)

- Add `saveContext(sessionId: string, workspaceId: string): Promise<void>` method
- Add `loadContext(sessionId: string, workspaceId: string): Promise<any>` method

#### [MODIFY] [sessions.tsx](file:///home/burhop/repos/wright/apps/web/src/store/sessions.tsx)

- Accept optional `workspaceId` prop in `ChatProvider`
- Namespace `localStorage` key as `wright-chat-{workspaceId}` when a workspace is scoped
- On workspace change, trigger context save for previous workspace and load for new one

---

### 7. Frontend — WorkspacePanel Update

#### [MODIFY] [WorkspacePanel.tsx](file:///home/burhop/repos/wright/apps/web/src/components/chat/WorkspacePanel.tsx)

- Accept optional `workspaceId` and `sessionId` props
- Use provided `sessionId` instead of reading from global chat state when props are available
- This scopes the workspace file tree, git operations, and chat to a specific workspace

---

## Verification Plan

### Automated Tests

1. **Backend**: `pytest apps/api/tests/test_workspace_api.py` — test `POST /create`, `GET /{id}`, context endpoints
2. **Frontend**: `npx vitest run` — test dashboard component renders workspace list, create modal, navigation
3. **E2E**: `npx playwright test tests/ui-integration/dashboard.spec.ts` — test full flow: dashboard → create workspace → workspace page loads

### Manual Verification

1. Open dashboard — verify recent workspaces display (not empty)
2. Click "Create Workspace" — verify modal opens, fill form, submit
3. Verify navigation to `/workspace/{id}` after creation
4. Verify workspace page loads with file tree and agent chat
5. Open a second browser tab with a different workspace URL — verify isolation
6. Navigate to Tool Registry — verify OpenSCAD shows as "Installed"
7. Verify `/agent-chat` redirects to dashboard
