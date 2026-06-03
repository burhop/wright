# API Contracts: IDE UI Redesign

This document outlines the API route additions for saving file content and configuring workspace-specific MCP tools.

---

## 1. File Writing / Content Saving

### Update File Content
- **Endpoint**: `PUT /api/workspace/files/content`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)",
    "path": "string (workspace-relative path)",
    "content": "string (raw file content)"
  }
  ```
- **Response Schema (200 OK)**:
  ```json
  {
    "success": true
  }
  ```

---

## 2. Workspace Tools Configuration

### Get Enabled Workspace Tools
- **Endpoint**: `GET /api/workspace/tools`
- **Parameters**:
  - `session_id` (string, Query)
- **Response Schema (200 OK)**:
  ```json
  {
    "session_id": "string",
    "enabled_tools": ["string"]
  }
  ```

### Toggle Workspace Tool Status
- **Endpoint**: `POST /api/workspace/tools/toggle`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)",
    "server_id": "string (MCP server name/ID)",
    "is_enabled": "boolean"
  }
  ```
- **Response Schema (200 OK)**:
  ```json
  {
    "success": true,
    "session_id": "string",
    "server_id": "string",
    "is_enabled": "boolean"
  }
  ```
