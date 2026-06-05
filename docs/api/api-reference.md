# API Reference

Wright exposes a FastAPI backend gateway to orchestrate agent requests, manage files, and execute local tools.

---

## Interactive Swagger Documentation

When running locally or via Docker, the interactive Swagger UI provides direct REST endpoint execution and schema details.

*   **Endpoint Route**: `http://localhost:8000/docs` (Local) or `http://localhost:8080/docs` (Docker)
*   **Alternate Redoc Interface**: `http://localhost:8000/redoc`

---

## Key Core Endpoint Groups

### 1. Workspaces
*   `GET /api/workspaces`: Lists available workspace directories.
*   `POST /api/workspaces`: Creates a new workspace and initializes a Git repository.
*   `GET /api/workspaces/{workspace_id}/files`: Returns tree nodes with git-porcelain indicators.

### 2. Agents & Sessions
*   `POST /api/sessions`: Creates an agent chat session.
*   `POST /api/sessions/{session_id}/chat`: Dispatches a message to the orchestrator (returns SSE token streams).
*   `GET /api/sessions/{session_id}/history`: Returns serialized chat history.

### 3. Tool registry
*   `GET /api/tools`: Lists all discovered and enabled MCP servers.
*   `POST /api/tools/install`: Registers a new stdio or sse MCP server in the SQLite state store.
*   `POST /api/tools/call`: Programmatically routes execution arguments to an active runner.
