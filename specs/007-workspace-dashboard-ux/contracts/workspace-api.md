# API Contract: Workspace Endpoints

**Branch**: `007-workspace-dashboard-ux` | **Date**: 2026-06-03

All endpoints are prefixed with `/api/workspace`.

## New Endpoints

### POST /api/workspace/create

Create a new workspace from the dashboard.

**Request**:
```json
{
  "name": "My Engineering Project",
  "local_path": "/home/user/projects/my-project"
}
```

**Response** (201 Created):
```json
{
  "workspace_id": "a1b2c3d4-...",
  "session_id": "e5f6g7h8-...",
  "workspace_name": "My Engineering Project",
  "local_path": "/home/user/projects/my-project",
  "git_remote_url": null,
  "git_username": null,
  "enabled_tools": null,
  "updated_at": 1748966400
}
```

**Errors**:
- `400 Bad Request` — missing name, missing/invalid path, path doesn't exist on disk
- `500 Internal Server Error` — database write failure

---

### GET /api/workspace/{workspace_id}

Fetch a single workspace by its ID.

**Response** (200 OK):
```json
{
  "workspace_id": "a1b2c3d4-...",
  "session_id": "e5f6g7h8-...",
  "workspace_name": "My Engineering Project",
  "local_path": "/home/user/projects/my-project",
  "git_remote_url": null,
  "git_username": null,
  "enabled_tools": ["openscad-geometry"],
  "updated_at": 1748966400
}
```

**Errors**:
- `404 Not Found` — workspace ID does not exist

---

### POST /api/workspace/{workspace_id}/context/save

Save agent conversation context for a workspace.

**Request**:
```json
{
  "context_data": { "messages": [...], "metadata": {...} }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "workspace_id": "a1b2c3d4-..."
}
```

---

### GET /api/workspace/{workspace_id}/context/load

Load agent conversation context for a workspace.

**Response** (200 OK):
```json
{
  "workspace_id": "a1b2c3d4-...",
  "context_data": { "messages": [...], "metadata": {...} },
  "updated_at": 1748966400
}
```

**Errors**:
- `404 Not Found` — no saved context for this workspace

---

## Modified Endpoints

### GET /api/workspace/recent

**Change**: Response now includes `workspace_name` field.

### GET /api/workspace/list

**Change**: Response now includes `workspace_name` field.

### POST /api/workspace/activate

**Change**: Also triggers context load for the activated workspace.

---

## Frontend Route Changes

| Old Route | New Route | Description |
|-----------|-----------|-------------|
| `/agent-chat` | `/workspace/:workspaceId` | Workspace-scoped IDE view |
| — | `/` (dashboard) | Shows "Create Workspace" button + recent list + "View all" button |
