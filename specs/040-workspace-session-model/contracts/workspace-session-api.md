# Contract: Workspace Session APIs

## GET /api/workspace/by-id/{workspace_id}

Returns the stable workspace record.

**Response additions/clarifications**:

- `workspace_id`: Stable workspace id.
- `session_id`: Default or last active session id for compatibility.
- `enabled_tools`: Workspace-level enabled MCP tool list.

## GET /api/workspace/by-id/{workspace_id}/sessions

Returns non-archived chat sessions associated with the workspace.

**Response**:

```json
{
  "workspace_id": "workspace-123",
  "sessions": [
    {
      "session_id": "api_session_1",
      "title": "Onshape Session 1",
      "created_at": 1783030000,
      "updated_at": 1783030500,
      "message_count": 4
    }
  ]
}
```

**Rules**:

- Must not include sessions from other workspaces.
- Should reconcile known local associations with agent backend sessions where possible.

## POST /api/workspace/by-id/{workspace_id}/sessions

Creates a new chat session associated with the workspace.

**Response**:

```json
{
  "workspace_id": "workspace-123",
  "session_id": "api_session_2",
  "title": "Onshape Session 2",
  "created_at": 1783031000
}
```

**Rules**:

- Must add a session association without replacing existing workspace sessions.
- May update the workspace default session pointer.

## POST /api/workspace/by-id/{workspace_id}/session/select

Selects a default/current session for the workspace.

**Request**:

```json
{
  "session_id": "api_session_2"
}
```

**Response**:

```json
{
  "success": true,
  "workspace_id": "workspace-123",
  "session_id": "api_session_2"
}
```

**Rules**:

- Must reject session ids that belong to a different workspace.
- Must not change workspace enabled tools.
- Must not reset workspace file/viewer state.

## GET /api/workspace/by-id/{workspace_id}/tools

Returns workspace-level enabled MCP tools.

**Response**:

```json
{
  "workspace_id": "workspace-123",
  "enabled_tools": ["Jarvis OnShape MCP"]
}
```

## POST /api/workspace/by-id/{workspace_id}/tools/toggle

Updates workspace-level MCP enablement.

**Request**:

```json
{
  "server_id": "jarvisonshapemcp",
  "is_enabled": true
}
```

**Response**:

```json
{
  "success": true,
  "workspace_id": "workspace-123",
  "server_id": "jarvisonshapemcp",
  "is_enabled": true
}
```

## GET /api/workspace/by-id/{workspace_id}/mcp-status

Returns status for MCPs required by this workspace.

**Response**:

```json
{
  "workspace_id": "workspace-123",
  "status": "ok",
  "message": "MCP configuration is active and healthy.",
  "running_mcps": [
    {
      "name": "Jarvis OnShape MCP",
      "status": "active",
      "error_message": null
    }
  ]
}
```

**Rules**:

- Must evaluate only tools enabled for the workspace.
- Must not report globally installed but disabled tools as workspace failures.
- Must name required MCPs that cannot start or are unavailable.

## Compatibility

Existing session-based endpoints may remain during migration, but new UI flows should prefer workspace-id endpoints for workspace state and MCP status.
