# Data Model: MCP Credential & Secret Setup

**Feature**: 026-mcp-credential-setup | **Date**: 2026-06-12

## Entity Changes

### EnvVarDefinition (New)

Metadata about an environment variable required by an MCP server.

| Field       | Type   | Required | Description                                      |
| ----------- | ------ | -------- | ------------------------------------------------ |
| name        | string | yes      | Environment variable name (e.g., `ONSHAPE_API_KEY`) |
| label       | string | yes      | Human-readable label (e.g., "Access Key")        |
| description | string | no       | Help text for the user                           |
| required    | bool   | yes      | Whether this variable must be configured to start the server |
| secret      | bool   | yes      | Whether the value should be masked in UI (password field) |

### McpServer (Modified)

| Field                    | Type                          | Change     | Description                                  |
| ------------------------ | ----------------------------- | ---------- | -------------------------------------------- |
| env_vars                 | `list[EnvVarDefinition]`      | **evolved** | Was `dict[str, str]`. Now stores variable metadata, not values. |
| credentials_configured   | `dict[str, bool]`             | **added**   | Dynamic field (not stored). Indicates which env vars have saved values. |

### Credential Store (New — File-based)

**Location**: `~/.config/wright/mcp-secrets.json`
**Permissions**: `0600` (owner read/write only)

```json
{
  "jarvis-onshape-mcp": {
    "ONSHAPE_API_KEY": "onshape-access-key-placeholder",
    "ONSHAPE_API_SECRET": "onshape-secret-key-placeholder"
  },
  "another-server-id": {
    "API_TOKEN": "tok_..."
  }
}
```

## Database Schema Changes

### mcp_servers.env_vars Column (Evolved Encoding)

**Before** (old format — backward compatible):
```json
{"FREECAD_PATH": "/usr/local/bin/freecadcmd"}
```

**After** (new format):
```json
[
  {"name": "ONSHAPE_API_KEY", "label": "Access Key", "description": "...", "required": true, "secret": false},
  {"name": "ONSHAPE_API_SECRET", "label": "Secret Key", "description": "...", "required": true, "secret": true}
]
```

The deserialization layer detects the format:
- If JSON parses to a `list` → new `EnvVarDefinition` format
- If JSON parses to a `dict` → old format (treated as non-required, non-secret variables)

## API Contracts

### GET /api/mcp/servers/{server_id}/credentials

**Response** `200 OK`:
```json
{
  "server_id": "jarvis-onshape-mcp",
  "env_vars": [
    {"name": "ONSHAPE_API_KEY", "label": "Access Key", "description": "...", "required": true, "secret": false},
    {"name": "ONSHAPE_API_SECRET", "label": "Secret Key", "description": "...", "required": true, "secret": true}
  ],
  "configured": {
    "ONSHAPE_API_KEY": true,
    "ONSHAPE_API_SECRET": true
  }
}
```

### PUT /api/mcp/servers/{server_id}/credentials

**Request**:
```json
{
  "credentials": {
    "ONSHAPE_API_KEY": "onshape-access-key-placeholder",
    "ONSHAPE_API_SECRET": "onshape-secret-key-placeholder"
  }
}
```

**Response** `200 OK`:
```json
{
  "server_id": "jarvis-onshape-mcp",
  "env_vars": [...],
  "configured": {
    "ONSHAPE_API_KEY": true,
    "ONSHAPE_API_SECRET": true
  }
}
```

### DELETE /api/mcp/servers/{server_id}/credentials

**Response** `204 No Content`

### GET /api/mcp/servers (Modified — Existing)

Each server in the `servers` list now includes:
```json
{
  "server_id": "jarvis-onshape-mcp",
  "name": "Jarvis OnShape MCP",
  "env_vars": [
    {"name": "ONSHAPE_API_KEY", "label": "Access Key", "required": true, "secret": false},
    {"name": "ONSHAPE_API_SECRET", "label": "Secret Key", "required": true, "secret": true}
  ],
  "credentials_configured": {
    "ONSHAPE_API_KEY": true,
    "ONSHAPE_API_SECRET": false
  },
  ...
}
```

**SECURITY**: The `credentials` values themselves (the actual secret strings) are NEVER included in any API response.

## State Transitions

```
Server Registered (env_vars defined)
    │
    ▼
Credentials Not Configured ──► [UI: "Configure Credentials"]
    │
    ▼  (PUT /credentials)
Credentials Configured ──► [UI: green checks, Install button enabled]
    │
    ▼  (POST /install)
Server Installed & Active ──► credentials merged from secrets file → StdioRunner
    │
    ▼  (DELETE /servers/{id})
Server Deleted ──► credentials removed from secrets file
```
