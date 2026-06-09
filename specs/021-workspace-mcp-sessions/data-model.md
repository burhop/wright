# Data Model: Workspace MCP & Session Isolation

**Branch**: `021-workspace-mcp-sessions` | **Date**: 2026-06-09

## Relational Schema (SQLite)

We will utilize the existing SQLite database schema but clarify the usage of columns to support multi-session isolation.

### 1. `engineering_workspaces`
Stores the metadata for each workspace directory and tracks the active session pointer.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `workspace_id` | TEXT | PRIMARY KEY | Unique UUID generated on creation. |
| `workspace_name` | TEXT | NOT NULL | User-provided display name (e.g., "Gearbox Design"). |
| `local_path` | TEXT | NOT NULL UNIQUE | Absolute disk path to the directory (e.g., `/home/agent/workspace/gearbox-design`). |
| `session_id` | TEXT | NOT NULL | Pointer to the active or last used session ID for this workspace. |
| `git_remote_url` | TEXT | NULLABLE | Remote git repository URL. |
| `git_username` | TEXT | NULLABLE | Git provider username. |
| `git_token` | TEXT | NULLABLE | Encrypted/masked token for git push/pull. |
| `enabled_tools` | TEXT | NULLABLE | JSON array of active MCP server IDs (e.g. `["openscad-mcp-server"]`). |
| `created_at` | INTEGER | NOT NULL | Epoch timestamp (seconds). |
| `updated_at` | INTEGER | NOT NULL | Epoch timestamp (seconds). |

---

### 2. `chat_messages`
Stores message logs for chat history.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | TEXT | PRIMARY KEY | Unique message ID. |
| `session_id` | TEXT | NOT NULL | Associated session ID. |
| `role` | TEXT | NOT NULL | Either `'user'` or `'assistant'`. |
| `content` | TEXT | NOT NULL | Message text content. |
| `timestamp` | INTEGER | NOT NULL | Time the message was sent (epoch ms). |
| `trace_id` | TEXT | NULLABLE | OpenTelemetry trace identifier. |
| `created_at` | INTEGER | NOT NULL | Epoch timestamp. |

---

## Workspace Directory Sanitization Rules

To construct the directory path, the workspace name is passed through a sanitization function:
1. Convert all characters to lowercase.
2. Replace non-alphanumeric characters (excluding hyphens/underscores) with hyphens.
3. Replace consecutive hyphens with a single hyphen.
4. Strip leading and trailing hyphens.

Example:
* Input name: `Propeller v3: (Final Run!)`
* Sanitized: `propeller-v3-final-run`
* Output local path: `/home/agent/workspace/propeller-v3-final-run`
