# Data Model: Workspace Dashboard UX

**Branch**: `007-workspace-dashboard-ux` | **Date**: 2026-06-03

## Entities

### 1. Workspace (existing: `engineering_workspaces` table — modified)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `workspace_id` | TEXT | PRIMARY KEY | UUID, unique identifier |
| `session_id` | TEXT | NOT NULL, UNIQUE | Agent session identifier |
| `workspace_name` | TEXT | nullable | Human-readable display name (NEW) |
| `local_path` | TEXT | NOT NULL | Absolute filesystem path to workspace directory |
| `git_remote_url` | TEXT | nullable | Git remote URL for syncing |
| `git_username` | TEXT | nullable | Git username |
| `git_token` | TEXT | nullable | Git access token (encrypted at rest) |
| `enabled_tools` | TEXT | nullable | JSON array of enabled tool server_ids |
| `created_at` | INTEGER | NOT NULL | Unix timestamp |
| `updated_at` | INTEGER | NOT NULL | Unix timestamp, updated on access |

**Changes**: Added `workspace_name` column (TEXT, nullable). Existing workspaces without a name will derive one from the `local_path` basename at display time.

**State transitions**:
- Created → Active (on navigate to workspace page)
- Active → Inactive (on navigate away)
- Any → Deleted (on explicit user deletion)

### 2. Agent Context (NEW: `agent_contexts` table)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `workspace_id` | TEXT | PRIMARY KEY, FK → engineering_workspaces | Links context to workspace |
| `context_data` | TEXT | nullable | JSON-serialized agent conversation context |
| `updated_at` | INTEGER | NOT NULL | Unix timestamp of last save |

**Purpose**: Stores the agent's conversation context per workspace, enabling context restoration when switching between workspaces.

**Note**: For the Hermes adapter, this table serves as a frontend-only cache. Hermes manages its own server-side context. For future agents that don't persist context server-side, this table will be the primary store.

### 3. MCP Server (existing: `mcp_servers` table — unchanged schema)

| Field | Type | Key | Description |
|-------|------|-----|-------------|
| `server_id` | TEXT | PK | UUID |
| `name` | TEXT | | Display name |
| `type` | TEXT | | "stdio" / "sse" / "webmcp" |
| `command` | TEXT | | Command or URL |
| `is_active` | INTEGER | | 0/1 global toggle |
| `is_installed` | INTEGER | | 0/1 installation state |
| `status` | TEXT | | "active" / "inactive" / "error" |
| `error_message` | TEXT | | Last error |
| `category` | TEXT | | "cad" / "simulation" / etc. |
| `created_at` | INTEGER | | Unix timestamp |
| `updated_at` | INTEGER | | Unix timestamp |

**Behavior change**: At API startup, a migration step checks each registered tool's binary against `$PATH` or process list and updates `is_installed` accordingly.

## Entity Relationships

```mermaid
erDiagram
    WORKSPACE ||--o| AGENT_CONTEXT : "has"
    WORKSPACE ||--o{ MCP_SERVER : "enables (via enabled_tools JSON)"
    
    WORKSPACE {
        text workspace_id PK
        text session_id UK
        text workspace_name
        text local_path
        text enabled_tools
        int created_at
        int updated_at
    }
    
    AGENT_CONTEXT {
        text workspace_id PK_FK
        text context_data
        int updated_at
    }
    
    MCP_SERVER {
        text server_id PK
        text name
        text type
        int is_installed
        int is_active
    }
```

## Validation Rules

1. `workspace_name` max length: 100 characters
2. `local_path` must be an absolute path (`/` prefix)
3. `local_path` must exist on disk at creation time
4. `workspace_id` and `session_id` are auto-generated UUIDs
5. `context_data` max size: 10MB (practical limit for SQLite TEXT)
6. Duplicate `workspace_name` values are allowed (not a unique constraint)
7. Duplicate `local_path` values are allowed (same directory can have multiple workspace configs)
