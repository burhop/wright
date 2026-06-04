# API Contract: MCP Version Check & Update Endpoints

**Feature**: `009-tool-registry-enhanced-ui`
**Base path**: `/api/mcp`

---

## GET `/api/mcp/servers/{server_id}/version-check`

Check if an installed local MCP server has a newer version available.

### Request

```
GET /api/mcp/servers/{server_id}/version-check
```

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `server_id` | path | string (UUID) | Yes | ID of the server to check |

### Responses

#### 200 OK — Check completed

```json
{
  "server_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "installed": "1.2.3",
  "latest": "1.4.0",
  "update_available": true,
  "error": null
}
```

```json
{
  "server_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "installed": "1.4.0",
  "latest": "1.4.0",
  "update_available": false,
  "error": null
}
```

```json
{
  "server_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "installed": null,
  "latest": null,
  "update_available": false,
  "error": "unsupported_package_manager"
}
```

#### 400 Bad Request — Not applicable (server is `sse` or `webmcp` type)

```json
{ "detail": "Version check not applicable for network-type servers." }
```

#### 404 Not Found — Server does not exist

```json
{ "detail": "MCP Server '{server_id}' not found." }
```

#### 500 Internal Server Error

```json
{ "detail": "Version check failed: {error_message}" }
```

---

## POST `/api/mcp/servers/{server_id}/update`

Update an installed local MCP server to the latest available version.

### Request

```
POST /api/mcp/servers/{server_id}/update
```

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| `server_id` | path | string (UUID) | Yes | ID of the server to update |

No request body.

### Responses

#### 200 OK — Update completed

```json
{
  "server_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "installed_version": "1.4.0",
  "success": true,
  "error": null
}
```

#### 400 Bad Request — Not applicable for network servers

```json
{ "detail": "Update not applicable for network-type servers." }
```

#### 404 Not Found

```json
{ "detail": "MCP Server '{server_id}' not found." }
```

#### 500 Internal Server Error

```json
{ "detail": "Update failed: {error_message}" }
```

---

## Existing Endpoints — Extended Fields

### GET `/api/mcp/servers` — Response (extended)

The `McpServer` object in the `servers` array now includes:

```json
{
  "server_id": "...",
  "name": "CalculiX Simulation",
  "type": "stdio",
  "command": ["uvx", "calculix-mcp"],
  "is_active": false,
  "is_installed": true,
  "status": "inactive",
  "error_message": null,
  "category": "simulation",
  "created_at": 1717430400,
  "updated_at": 1717430400,
  "image_url": "https://github.com/CalculiX.png?size=64",
  "description": "Finite element analysis solver. Installing this server sets up the CalculiX MCP bridge via uvx.",
  "source_url": "https://github.com/calculix/calculix-mcp",
  "installed_version": "2.21.0"
}
```

### POST `/api/mcp/servers` — Request (extended)

```json
{
  "name": "My Custom Tool",
  "type": "stdio",
  "command": ["python", "scripts/my_tool.py"],
  "category": "utilities",
  "image_url": "https://example.com/logo.png",
  "description": "Runs mesh analysis scripts. No additional software needed beyond Python.",
  "source_url": "https://github.com/myorg/my-tool"
}
```

All new fields are optional. Existing callers are unaffected.
