# API & Frontend Contracts: MCP Tool Registry

**Branch**: `003-mcp-tool-registry` | **Date**: 2026-06-02

## 1. Backend REST Endpoints

### List MCP Servers
- **Endpoint**: `GET /api/mcp/servers`
- **Response**: `200 OK`
  ```json
  {
    "servers": [
      {
        "server_id": "8fa8d10b-d249-43c2-bd72-6905580ea2df",
        "name": "CalculiX Runner",
        "type": "stdio",
        "command": ["uv", "run", "calculix-mcp"],
        "is_active": true,
        "status": "active",
        "category": "simulation",
        "created_at": 1780423000
      }
    ]
  }
  ```

### Register Custom MCP Server
- **Endpoint**: `POST /api/mcp/servers`
- **Request Body**:
  ```json
  {
    "name": "My Custom CLI Tool",
    "type": "stdio",
    "command": ["python", "scripts/tool.py"],
    "category": "utilities"
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "server_id": "97e68bc5-6cf9-42b7-84bc-d90df8f4955b",
    "name": "My Custom CLI Tool",
    "status": "inactive"
  }
  ```

### Toggle Server Activation (Start/Stop)
- **Endpoint**: `PATCH /api/mcp/servers/{server_id}`
- **Request Body**:
  ```json
  {
    "is_active": true
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "server_id": "8fa8d10b-d249-43c2-bd72-6905580ea2df",
    "is_active": true,
    "status": "active",
    "error_message": null
  }
  ```

### Delete Server Configuration
- **Endpoint**: `DELETE /api/mcp/servers/{server_id}`
- **Response**: `204 No Content`

### List Available Discovered Tools
- **Endpoint**: `GET /api/mcp/tools`
- **Response**: `200 OK`
  ```json
  {
    "tools": [
      {
        "name": "calculix_mesh_stiffness",
        "description": "Generate CalculiX mesh calculations",
        "input_schema": {
          "type": "object",
          "properties": {
            "mesh_size": { "type": "number" }
          },
          "required": ["mesh_size"]
        },
        "server_id": "8fa8d10b-d249-43c2-bd72-6905580ea2df",
        "is_enabled": true
      }
    ]
  }
  ```

---

## 2. WebMCP Browser Event Contract

WebMCP enables the backend Python agent to invoke client-side DOM reader tools in the user's browser. It works via custom window event dispatches:

### Request Event (Triggered by client socket coordinator)
- **Event Name**: `webmcp:request`
- **Payload (`detail`)**:
  ```json
  {
    "callId": "req-102",
    "method": "get_selected_part",
    "params": {}
  }
  ```

### Response Event (Triggered by target viewport component)
- **Event Name**: `webmcp:response`
- **Payload (`detail`)**:
  ```json
  {
    "callId": "req-102",
    "result": {
      "partId": "part-aba8973b-31a8",
      "dimensions": [12.0, 5.5, 2.3]
    }
  }
  ```

---

## 3. MCP-UI Progress Event Payload

To support live visual tool rendering in the transcript, tools emit structured progress messages to the chat coordinator:

- **JSON Payload Format**:
  ```json
  {
    "type": "progress",
    "data": {
      "percentage": 42.5,
      "message": "Generating structural mesh..."
    }
  }
  ```
