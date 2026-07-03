# Data Model: Workspace Session Model

## Workspace

Represents a stable engineering workspace.

**Fields**:

- `workspace_id`: Stable workspace identifier.
- `workspace_name`: User-visible name.
- `local_path`: Local filesystem path.
- `enabled_tools`: Workspace-level list of enabled MCP tool names or ids.
- `updated_at`: Last workspace-level update time.
- `last_active_session_id`: Compatibility/current-session pointer used for default selection only.

**Relationships**:

- Has zero to many Workspace Agent Sessions.
- Has one Workspace Tool Configuration.
- May be the Active Workspace Context exposed to the gateway.

**Validation Rules**:

- Workspace identity must not change when chat sessions are created, selected, deleted, or refreshed.
- `last_active_session_id`, if set, must refer to a session associated with the workspace or be ignored during recovery.

## Workspace Agent Session

Associates an agent chat session with one workspace.

**Fields**:

- `workspace_id`: Owning workspace.
- `session_id`: Agent/Hermes session id.
- `agent_id`: Agent provider id, defaulting to Hermes for current flows.
- `title`: User-visible session title, if known.
- `created_at`: Creation timestamp.
- `updated_at`: Last known update timestamp.
- `is_archived`: Whether the session is hidden from normal selection.

**Relationships**:

- Belongs to exactly one Workspace.
- Has zero to many Chat Messages by `session_id`.

**Validation Rules**:

- A `session_id` may be associated with only one workspace.
- A workspace may have multiple non-archived sessions.
- Missing agent-backend sessions are tolerated during list/recovery but must not corrupt workspace state.

## Workspace Tool Configuration

Defines which MCP servers a workspace expects.

**Fields**:

- `workspace_id`: Owning workspace.
- `enabled_tools`: List of enabled MCP server names or ids.

**Relationships**:

- Shared by all Workspace Agent Sessions in the workspace.
- Used by Workspace MCP Status.

**Validation Rules**:

- Installed but disabled tools are not required for the workspace.
- Enabled aliases and server ids should resolve to the same workspace requirement where possible.

## Workspace MCP Status

Represents current availability of workspace-required tools.

**Fields**:

- `workspace_id`: Workspace being evaluated.
- `status`: `ok`, `warning`, `mismatch`, or `error`.
- `message`: User-facing summary.
- `required_mcps`: Required server status entries for enabled workspace tools.

**State Transitions**:

- `ok`: All workspace-required MCPs are available or no tools are enabled.
- `warning`: A recoverable or pending availability condition exists.
- `mismatch`: Gateway/configuration does not match the active workspace context.
- `error`: A required MCP failed to start or has a known error.

## Active Workspace Context

Tracks which workspace the gateway should expose to Hermes.

**Fields**:

- `workspace_id`: Active workspace.
- `session_id`: Current/default session for the active workspace.

**Validation Rules**:

- Switching the active workspace updates gateway context.
- Switching chat sessions inside the same workspace may update default session, but must not change workspace tool enablement.
