# API Contracts: Workspace MCP & Session Isolation

**Branch**: `021-workspace-mcp-sessions` | **Date**: 2026-06-09

## 1. Create Workspace
Create a new engineering workspace directory and start an initial chat session.

* **Endpoint**: `POST /api/workspace/create`
* **Content-Type**: `application/json`

### Request Body
```json
{
  "name": "gearbox-design"
}
```

### Response (201 Created)
```json
{
  "workspace_id": "ws-uuid-12345",
  "session_id": "sess-uuid-67890",
  "workspace_name": "gearbox-design",
  "local_path": "/home/agent/workspace/gearbox-design",
  "git_remote_url": null,
  "git_username": null,
  "enabled_tools": [],
  "updated_at": 1717900000
}
```

### Error Response (400 Bad Request)
Returned if a workspace name contains invalid characters or a folder with the sanitized name already exists on disk or in SQLite.
```json
{
  "detail": "Workspace directory already exists: /home/agent/workspace/gearbox-design"
}
```

---

## 2. List Agent Sessions (Filtered)
List sessions from the active agent runner, optionally filtered to a single workspace.

* **Endpoint**: `GET /api/agent/sessions`
* **Query Parameters**:
  * `workspace_id`: (optional string) UUID of the workspace to filter by.

### Response (200 OK)
```json
{
  "sessions": [
    {
      "session_id": "sess-uuid-67890",
      "title": "Gearbox Design Session 1",
      "created_at": 1717900000,
      "updated_at": 1717900000,
      "message_count": 0
    }
  ]
}
```

---

## 3. Update Active Session
Updates the database pointer for the currently active session in a workspace.

* **Endpoint**: `POST /api/workspace/by-id/{workspace_id}/session`
* **Content-Type**: `application/json`

### Request Body
```json
{
  "session_id": "sess-uuid-abcde"
}
```

### Response (200 OK)
```json
{
  "success": true
}
```
