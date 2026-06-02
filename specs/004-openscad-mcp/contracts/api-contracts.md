# API Contracts: Workspace File Management

This contract outlines the endpoints exposed by the FastAPI backend to allow the React frontend to browse and load files from the active workspace for Three.js rendering.

---

## 1. List Workspace Files

Browse the contents of the active workspace directory.

- **URL**: `/api/workspace/files`
- **Method**: `GET`
- **Query Parameters**:
  - `session_id` (String, Required): Active agent session ID to discover its bound workspace.
- **Headers**:
  - `Content-Type: application/json`

### Response (200 OK)
```json
{
  "workspace": {
    "name": "designs",
    "path": "/designs",
    "type": "directory",
    "size": null,
    "last_modified": 1780425558,
    "children": [
      {
        "name": "gearbox.stl",
        "path": "/designs/gearbox.stl",
        "type": "file",
        "size": 1048576,
        "last_modified": 1780425558,
        "children": null
      }
    ]
  }
}
```

---

## 2. Get File Content

Retrieve the raw content of a specific file in the active workspace. Used by the Three.js loader to fetch binary buffers (like STL files).

- **URL**: `/api/workspace/files/content`
- **Method**: `GET`
- **Query Parameters**:
  - `session_id` (String, Required): Session ID to identify the workspace sandbox.
  - `path` (String, Required): Workspace-relative path to the target file (e.g. `/designs/gearbox.stl`).
- **Headers**:
  - `Accept: application/octet-stream`

### Response (200 OK)
- **Content-Type**: `application/octet-stream` (or matching file type like `text/plain` for `.scad`)
- **Body**: Raw binary data or file stream.

### Error Responses
- **400 Bad Request**: Path contains invalid traversal characters (e.g., `..`).
- **404 Not Found**: File does not exist within the workspace sandbox directory.
