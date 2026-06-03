# Research: Workspace Dashboard UX

**Branch**: `007-workspace-dashboard-ux` | **Date**: 2026-06-03

## Research Tasks & Findings

### R1: Why is the workspace list empty on the dashboard?

**Finding**: The `DashboardPage.tsx` calls `workspaceService.getRecentWorkspaces()` and `workspaceService.getAllWorkspaces()` which hit `/api/workspace/recent` and `/api/workspace/list`. These endpoints query the `engineering_workspaces` SQLite table. The table is only populated when a user navigates to the agent chat and creates a session (via `get_workspace_dir` → `create_workspace`). A fresh user who has never opened an agent chat session will see an empty workspace list because no rows exist in the table yet.

**Decision**: Add a "Create Workspace" flow that directly inserts a workspace record into `engineering_workspaces` without requiring an agent session first. The existing `create_workspace()` function in `core/workspace.py` already supports this — it just needs a frontend-facing endpoint and UI.

**Alternatives considered**:
- Auto-scan filesystem for project directories → too invasive, unclear which paths to scan
- Populate from Hermes sessions → couples workspace creation to a specific agent framework

---

### R2: Current routing structure and Agent Chat removal

**Finding**: `App.tsx` defines four routes: `/` (Dashboard), `/agent-chat` (AgentChatPage), `/tool-registry` (ToolRegistryPage), `/file-vault` (FileVaultPage). The `AgentChatPage` simply renders `<ChatLayout>` which renders `<WorkspacePanel>` — a large 53KB component that contains the full IDE-like workspace view (file tree, editor tabs, chat sidebar, activity bar). The current flow is: Dashboard → click "Hermes Agent" → navigate to `/agent-chat` → `WorkspacePanel` renders.

**Decision**: Replace `/agent-chat` with `/workspace/:id` route. The `WorkspacePanel` component continues to be the main workspace view, but it now receives a workspace ID from the URL. The "Hermes Agent" card on the dashboard is removed. When a user clicks a workspace from the dashboard's recent list, they navigate to `/workspace/<workspace_id>`.

**Alternatives considered**:
- Keep `/agent-chat` as an alias → creates confusion, user explicitly wants it removed
- Use query parameter `?workspace=id` → less clean URL, harder to bookmark

---

### R3: Multi-tab workspace isolation

**Finding**: The current `ChatProvider` (sessions store) is a React Context that uses `useState` and `localStorage` for persistence. The `activeSessionId` is shared across the entire app. If two browser tabs open the same URL, they both write to the same `localStorage` key `wright-chat-sessions`, causing conflicts.

**Decision**: When navigating to `/workspace/:id`, extract the workspace's `session_id` from the URL param and use it to scope the chat context. The `ChatProvider` can receive the workspace-scoped `sessionId` from the route, avoiding the global `activeSessionId` conflict. `localStorage` key should be namespaced per workspace: `wright-chat-{workspace_id}`.

**Alternatives considered**:
- Use `sessionStorage` (per-tab) → loses persistence across page reloads within same tab
- Use IndexedDB → over-engineering for this stage

---

### R4: Tool installation state tracking

**Finding**: The `mcp_servers` table has an `is_installed` column (INTEGER, 0/1). The `McpServer` Pydantic model has `is_installed: bool`. The `ToolCard.tsx` already renders different UI based on `server.is_installed` — showing "Install" button vs "✓ Installed" badge. The install/uninstall flow calls backend endpoints that toggle `is_installed` in the DB.

**Decision**: The tool installation tracking infrastructure already exists and is functional. The issue is likely with the initial seed data — e.g., OpenSCAD should have `is_installed = 1` by default if it's detected on the system. Add a startup check that verifies installed tools (e.g., checking if the binary exists on `$PATH`) and updates their `is_installed` flag accordingly.

**Alternatives considered**:
- Manual-only install tracking → user complained OpenSCAD shows as not installed
- System-wide binary scan → too broad, just check registered tools

---

### R5: Agent context save/load API design

**Finding**: The `BaseAgentEngine` abstract class has methods: `create_session`, `list_sessions`, `delete_session`, `start_chat`, `stream_response`, `get_session_workspace`. It does NOT have `save_context` or `load_context` methods. Hermes manages its own session context server-side — the session_id passed to Hermes preserves conversation history automatically. However, the Wright frontend stores messages in `localStorage` independently.

**Decision**: Add two new abstract methods to `BaseAgentEngine`: `save_context(session_id, workspace_id)` and `load_context(session_id, workspace_id)`. For Hermes, these will be no-ops (Hermes already persists server-side). The Wright frontend will save/load its local message cache keyed by workspace_id. For future agent frameworks, these methods will handle actual context serialization.

**Alternatives considered**:
- Pure frontend-only persistence → works for now but doesn't scale to agents that need explicit context management
- Database-stored context → adds complexity; better suited for v2

---

### R6: Workspace creation API

**Finding**: The backend has `create_workspace()` in `core/workspace.py` but no dedicated REST endpoint for creating a workspace from the dashboard. The current `get_workspace_dir()` dependency auto-creates workspaces as a side effect. Need a dedicated `POST /api/workspace/create` endpoint.

**Decision**: Create a new `POST /api/workspace/create` endpoint that accepts `{name, local_path}`, validates the path exists on disk, creates a workspace record, and returns the workspace info. This is separate from the session-based auto-creation flow.

**Alternatives considered**:
- Reuse `get_workspace_dir` → it requires a session_id, which doesn't exist yet during explicit creation
