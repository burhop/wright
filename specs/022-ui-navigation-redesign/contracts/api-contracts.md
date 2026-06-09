# API Contracts: UI Navigation and Dashboard Redesign

This document details the HTTP REST API contracts for logs and settings.

## 1. Application Logs API

### `GET /api/logs`
Retrieve a paginated and filtered list of structured application logs.

**Query Parameters:**
- `workspace_id`: String (Optional) - Filter logs by a specific workspace ID.
- `level`: String (Optional) - Filter logs by severity level (`info`, `warning`, `error`).
- `search`: String (Optional) - Keyword search within log messages.
- `limit`: Integer (Optional, default: 100) - Maximum number of logs to return.
- `offset`: Integer (Optional, default: 0) - Number of logs to skip.

**Response (200 OK):**
```json
{
  "logs": [
    {
      "timestamp": "2026-06-09T11:47:33Z",
      "level": "info",
      "message": "Workspace loaded and activated",
      "logger": "api.routers.workspace",
      "workspace_id": "abc-123-xyz",
      "trace_id": "8f39bda012fc994bb0010c71a31d2e95",
      "span_id": "9ac18e0018f972b5",
      "extra": {
        "workspaceId": "abc-123-xyz",
        "path": "/home/burhop/repos/wright"
      }
    }
  ],
  "total": 1254
}
```

---

## 2. Workspace Config API (Modified)

### `GET /api/workspace/{workspace_id}/config`
Fetch the workspace configuration options.

**Response (200 OK):**
```json
{
  "workspace_id": "abc-123-xyz",
  "git_remote_url": "https://github.com/burhop/wright",
  "git_username": "burhop",
  "has_token": true,
  "workspace_path": "/home/burhop/repos/wright",
  "workspace_prompt": "Always place models in ./models and renderings in ./renders.",
  "git_large_file_threshold": 10485760
}
```

### `POST /api/workspace/config`
Update workspace settings.

**Request Body:**
```json
{
  "session_id": "session-9f82d-11e2",
  "git_remote_url": "https://github.com/burhop/wright",
  "git_username": "burhop",
  "git_token": "ghp_securetoken...",
  "workspace_prompt": "Always place models in ./models and renderings in ./renders.",
  "git_large_file_threshold": 10485760
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "workspace_id": "abc-123-xyz"
}
```

---

## 3. Global Settings API

### `GET /api/settings`
Fetch global application preferences.

**Response (200 OK):**
```json
{
  "llm_provider": "hermes",
  "theme": "dark",
  "api_keys": {
    "openai": "sk-proj-••••••••",
    "anthropic": "sk-ant-••••••••"
  }
}
```

### `POST /api/settings`
Save global application preferences.

**Request Body:**
```json
{
  "llm_provider": "hermes",
  "theme": "dark",
  "api_keys": {
    "openai": "sk-proj-...",
    "anthropic": "sk-ant-..."
  }
}
```

**Response (200 OK):**
```json
{
  "success": true
}
```
