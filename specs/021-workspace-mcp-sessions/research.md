# Research: Workspace MCP & Session Isolation

**Branch**: `021-workspace-mcp-sessions` | **Date**: 2026-06-09

## Decision 1: Workspace Path Sanitization & Collision Handling

**Decision**: 
The backend will sanitize the user-provided workspace display name to construct a safe directory name (lowercase, alphanumeric, and hyphens only). If a directory with the sanitized folder name already exists under the default parent workspace directory, or a record with that name exists in SQLite, the backend will return an HTTP 400 Bad Request with a clear validation message.

**Rationale**:
* **Aesthetics & Readability**: Human-readable directory names (e.g., `/home/agent/workspace/gearbox-design`) are vastly superior to anonymous UUIDs for developers inspecting the workspace.
* **Predictable Path Mapping**: Allows clean mapping without relying on random UUID directories.
* **Collision Avoidance**: Preventing overwrite of existing project directories protects user data from unintended merges or directory clutter.

**Alternatives considered**:
* *UUID-only paths (previous behavior)*: Rejected because the user wants human-readable paths under the workspace directory.
* *Auto-suffixing indices (e.g. `name-1`)*: Rejected per user selection of Option A (Block and request unique name).

---

## Decision 2: Multi-Session to Workspace Mapping Strategy

**Decision**:
We will keep `session_id` in the `engineering_workspaces` table to represent the **last active/most recently used session** of that workspace. However, to retrieve all sessions belonging to a specific workspace, we will query the agent engine's sessions list and filter them by the workspace's `local_path`.

We will also update `GET /api/agent/sessions` to support an optional `workspace_id` query parameter. When provided, the backend will look up the workspace's `local_path` in SQLite and only return the sessions from the agent engine that are set to that path.

**Rationale**:
* **Direct Alignment with Agent Store**: The underlying agent runner (`hermes-webui`) already stores a `workspace` absolute path string for each session. By filtering the list at the API layer, we keep the agent store and SQLite database perfectly synchronized without creating duplicate session tracking tables.
* **UI Cleanliness**: In the workspace panel, the session switcher dropdown will only display sessions belonging to the active workspace.

**Alternatives considered**:
* *Workspace Sessions Join Table*: Rejected as redundant since the agent backend already has a source-of-truth mapping between session IDs and workspace directories.

---

## Decision 3: Session Switching and Restoration Flow

**Decision**:
1. When a user opens a workspace, the frontend calls `/api/workspace/activate`.
2. The backend resolves the workspace. If it has a recorded `session_id` in SQLite, it checks if that session still exists in the agent backend.
3. If it exists, it activates that session. If it does not exist (or has been deleted), the backend looks for any other session associated with that workspace path. If none exists, it creates a new session.
4. When the user switches sessions within the workspace, the frontend calls a new endpoint `POST /api/workspace/by-id/{workspace_id}/session` to update the active `session_id` for that workspace in SQLite.

**Rationale**:
* **Resilience**: If a session was deleted on the Hermes backend, Wright will gracefully recover by creating a new session or selecting another existing one rather than crashing or showing an empty state.
* **UX Continuity**: Keeps the user's focus on their last context.

---

## Decision 4: Propagation of Workspace Context to LLM Agents

**Decision**:
During agent execution (`POST /api/chat/start` and `/api/chat/stream`), the Wright API will ensure the session's workspace path is synchronized with the agent adapter. The `BaseAgentEngine` concrete implementation (`HermesAdapter`) will pass the workspace path down to `hermes-webui` during session creation and chat initialization.

---

## Decision 5: Dev/Test Cleanup Routine

**Decision**:
We will create a python script `scripts/cleanup-workspaces.py` (and expose it via a shell task or NPM script `npm run clean-workspaces`) that will:
1. Delete all workspace directories under the default workspace parent folder (`/home/agent/workspace/*` or `~/workspace/*`), excluding hidden configurations or specific project files.
2. Truncate/delete all rows from the `engineering_workspaces`, `agent_contexts`, and `chat_messages` tables in the SQLite database.

**Rationale**:
Directly addresses the user rule: "All existing workspaces should be removed" to purge previous test debris and start with a clean state.

---

## Decision 6: Workspace MCP Instructions Injection via .hermes.md

**Decision**:
Instead of passing compiled workspace MCP instructions dynamically inside the chat history database (via `engine.create_session(instructions=...)`), Wright will write them directly to a `.hermes.md` file in the root of the workspace directory. Sessions are created as empty sessions.

The MCP instructions block is written under designated markers:
```markdown
<!-- WRIGHT MCP INSTRUCTIONS START -->
...
<!-- WRIGHT MCP INSTRUCTIONS END -->
```
If `.hermes.md` already exists, Wright will preserve any user-written rules outside of these markers.

**Rationale**:
* **Schema Compliance**: Passing system messages inside the database session history results in the LLM receiving multiple system messages on the wire when the agent prepends its own persona. Strict providers (like Claude and DeepSeek) return a `400 BadRequestError` stating system messages must be at the beginning of the request. Consolidation via `.hermes.md` completely bypasses this issue.
* **Zero Hermes Modifications**: Leverages Hermes's native project context loaders (`.hermes.md` has highest priority and is automatically loaded and merged into the single system prompt Context tier on every turn).
* **Git Version Controlled**: The workspace instructions and user custom rules are saved directly in the project directory, enabling versioning and easy inspection by developers.

