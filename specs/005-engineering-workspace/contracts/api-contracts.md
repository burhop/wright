# API Contracts: Engineering Workspace

This document defines the HTTP API routes and request/response contracts for the Engineering Workspace and Git Integration.

## 1. Workspace Operations

### Create File/Folder
- **Endpoint**: `POST /api/workspace/files`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)",
    "path": "string (workspace-relative path)",
    "type": "string ('file' | 'directory')"
  }
  ```
- **Response Schema (201 Created)**:
  ```json
  {
    "name": "string",
    "path": "string",
    "type": "string",
    "size": null,
    "last_modified": 1780420000,
    "git_status": "U"
  }
  ```

### Delete File/Folder
- **Endpoint**: `DELETE /api/workspace/files`
- **Parameters**:
  - `session_id` (string, Query)
  - `path` (string, Query)
- **Response Schema (204 No Content)**: Empty

### Move/Rename File
- **Endpoint**: `PUT /api/workspace/files/move`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)",
    "source_path": "string (workspace-relative source path)",
    "destination_path": "string (workspace-relative destination path)"
  }
  ```
- **Response Schema (200 OK)**:
  ```json
  {
    "success": true,
    "source_path": "string",
    "destination_path": "string"
  }
  ```

---

## 2. Git Version Control

### Get Workspace Git Status
- **Endpoint**: `GET /api/workspace/git/status`
- **Parameters**:
  - `session_id` (string, Query)
- **Response Schema (200 OK)**:
  ```json
  {
    "branch_name": "string",
    "is_clean": false,
    "changes": [
      {
        "path": "string",
        "git_status": "string ('M' | 'U' | 'A' | 'D')",
        "staged": false
      }
    ]
  }
  ```

### View File Git Diff
- **Endpoint**: `GET /api/workspace/git/diff`
- **Parameters**:
  - `session_id` (string, Query)
  - `path` (string, Query)
- **Response Schema (200 OK)**:
  ```json
  {
    "path": "string",
    "diff": "string (unified diff format)"
  }
  ```

### Revert File to HEAD
- **Endpoint**: `POST /api/workspace/git/revert`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)",
    "path": "string (workspace-relative path)"
  }
  ```
- **Response Schema (200 OK)**:
  ```json
  {
    "success": true,
    "path": "string"
  }
  ```

### Create Git Commit
- **Endpoint**: `POST /api/workspace/git/commit`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)",
    "message": "string"
  }
  ```
- **Response Schema (200 OK)**:
  ```json
  {
    "success": true,
    "commit_hash": "string",
    "message": "string",
    "timestamp": 1780420000
  }
  ```

### Get Git Commit History
- **Endpoint**: `GET /api/workspace/git/history`
- **Parameters**:
  - `session_id` (string, Query)
  - `limit` (int, Query, default=50)
- **Response Schema (200 OK)**:
  ```json
  {
    "commits": [
      {
        "commit_hash": "string",
        "message": "string",
        "author": "string",
        "timestamp": 1780420000
      }
    ]
  }
  ```

---

## 3. Remote Synchronization & Settings

### Get Workspace Remote Configuration
- **Endpoint**: `GET /api/workspace/config`
- **Parameters**:
  - `session_id` (string, Query)
- **Response Schema (200 OK)**:
  ```json
  {
    "workspace_id": "string (UUID)",
    "git_remote_url": "string | null",
    "git_username": "string | null",
    "has_token": false
  }
  ```

### Update Workspace Remote Configuration
- **Endpoint**: `POST /api/workspace/config`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)",
    "git_remote_url": "string | null",
    "git_username": "string | null",
    "git_token": "string | null"
  }
  ```
- **Response Schema (200 OK)**:
  ```json
  {
    "success": true,
    "workspace_id": "string (UUID)"
  }
  ```

### Push Commits to Remote
- **Endpoint**: `POST /api/workspace/git/push`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)"
  }
  ```
- **Response Schema (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Push completed successfully"
  }
  ```

### Pull Commits from Remote
- **Endpoint**: `POST /api/workspace/git/pull`
- **Request Schema**:
  ```json
  {
    "session_id": "string (UUID)"
  }
  ```
- **Response Schema (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Pull completed successfully"
  }
  ```
- **Error Schema (409 Conflict)**:
  ```json
  {
    "error": "MergeConflict",
    "message": "Pull resulted in merge conflicts",
    "conflicted_files": ["string"]
  }
  ```
