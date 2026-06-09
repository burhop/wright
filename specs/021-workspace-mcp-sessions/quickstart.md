# Quickstart: Workspace MCP & Session Isolation

**Branch**: `021-workspace-mcp-sessions` | **Date**: 2026-06-09

This quickstart guide details how to verify the new workspace creation, session isolation, and cleanup features.

## Prerequisites
Ensure the local dev stack is running:
```bash
# Start backend and web interface via Docker Compose
docker compose up -d
```

---

## 1. Verify Named Workspace Creation
You can verify the named folder creation by sending a POST request to the workspace creation endpoint:

```bash
curl -X POST http://127.0.0.1:8000/api/workspace/create \
  -H "Content-Type: application/json" \
  -d '{"name": "test-propeller"}'
```

**Expected Results**:
1. Returns a `201 Created` status with the session details.
2. A new folder exists at `/home/agent/workspace/test-propeller` on the container or local dev disk.
3. Checking git status inside that directory reveals a initialized git repository:
   ```bash
   cd ~/workspace/test-propeller && git status
   ```

---

## 2. Verify Session Filtering
Create multiple sessions under different workspaces, then list sessions for a specific workspace to verify isolation:

```bash
# List sessions for the 'test-propeller' workspace
curl "http://127.0.0.1:8000/api/agent/sessions?workspace_id=<workspace-id-from-above>"
```

**Expected Results**:
* The returned list only contains session IDs created under the specified workspace.

---

## 3. Verify Workspace Cleanup Utility
Run the python cleanup script to wipe all test workspaces:

```bash
python scripts/cleanup-workspaces.py
```

**Expected Results**:
* All directories under the application's workspace directory are deleted.
* Database rows in the `engineering_workspaces`, `agent_contexts`, and `chat_messages` tables are successfully truncated.
