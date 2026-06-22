# Feature Specification: Wright API Bridge Client

**Feature Branch**: `029-wright-api-bridge`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "/speckit-plan specify Create the Wright API bridge client for hermes-plugin-wright that communicates with the Wright FastAPI server at http://127.0.0.1:8000. The bridge lives in hermes-plugin-wright/bridge.py. It must: (1) Auto-detect the Wright repo directory by reading the Hermes config.yaml wrightgateway entry — look in ~/.hermes/profiles/wright/config.yaml and ~/.hermes/config.yaml for mcp_servers.wrightgateway.args, find the --project flag value. (2) Provide an async health check via GET /api/health. (3) Provide async methods to: get server list (GET /api/mcp/servers), install a catalog entry (POST /api/mcp/servers with name, type, command, category, image_url, description, source_url, env_vars from the catalog entry schema), get workspace info (GET /api/workspace/list), and check credential status (GET /api/mcp/servers/{id}/credentials). (4) Use httpx.AsyncClient with a 30-second timeout. (5) Never log or expose credential values — only check configured/not-configured status. (6) Handle connection errors gracefully — return structured error results, never raise unhandled exceptions. (7) Export constants WRIGHT_API_BASE = "http://127.0.0.1:8000" and WRIGHT_UI_URL = "http://localhost:8000". The bridge does NOT manage MCP servers directly — it delegates everything to the Wright FastAPI API which already handles McpEngine lifecycle, credential storage, and gateway SSE notifications. Write unit tests with httpx mocking. Reference: docs/wright-hermes-plugin-plan.md sections 7 (Gateway Bridge) and 9.2 (Repo Path Detection)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify API Health Status (Priority: P1)

An operator or user wants to verify if the Wright backend service is alive and accessible. They run a health check query. The bridge client dispatches a request to the `/api/health` endpoint on localhost:8000. If the server is up, it returns a healthy status containing latency metrics. If the server is offline or unreachable, the client handles the network exception gracefully, returning a structured disconnected status report instead of throwing unhandled crashes.

**Why this priority**: Connection verification is the prerequisite for all interactive tool registry and workspace management tasks.

**Independent Test**: Can be tested by shutting down or starting the FastAPI server and checking the returned connection health dictionary.

**Acceptance Scenarios**:

1. **Given** the Wright API server is running on localhost:8000, **When** check_health is called, **Then** it returns `{"connected": True, "latencyMs": ...}`.
2. **Given** the Wright API server is stopped, **When** check_health is called, **Then** it returns `{"connected": False, "error": "..."}` without crashing the client process.

---

### User Story 2 - Register a Tool Registry Catalog Entry (Priority: P1)

A user wants to add an engineering tool from the catalog to their active Wright environment. The system dispatches the tool's YAML registry metadata directly to the backend via `POST /api/mcp/servers`. The bridge translates Pydantic schemas, maps them to the expected `McpServerCreate` parameters, and sends the request. The backend registers the tool, and the bridge client receives the registration confirmation response.

**Why this priority**: Essential to bridging the static catalog data with the active SQLite database registry backend.

**Independent Test**: Can be tested by calling the install function with a mock `CatalogEntry` and verifying the target JSON payload matches the required `McpServerCreate` structure.

**Acceptance Scenarios**:

1. **Given** a valid `CatalogEntry` input, **When** register_tool is called, **Then** the client sends a `POST` request to `/api/mcp/servers` containing normalized name, type, command, category, and env_vars mappings.
2. **Given** a server error (e.g. unique constraint violation), **When** registering the tool, **Then** the client returns an error response with the API error message.

---

### User Story 3 - Repository Path Auto-Detection (Priority: P2)

The plugin starts up and needs to locate where the Wright codebase is located on the host filesystem (e.g. to build the frontend or locate config files). Rather than forcing manual environment variable definitions, the bridge client opens the local Hermes profile configuration files (first checking `~/.hermes/profiles/wright/config.yaml` then falling back to `~/.hermes/config.yaml`), searches for the `wrightgateway` MCP arguments, extracts the `--project` path parameter, and exposes this directory.

**Why this priority**: Critical for seamless, zero-config startup and operation of uvicorn and npm tasks.

**Independent Test**: Can be tested by mock writing a config file containing a `--project /path/to/repo` argument and verifying the detector returns `/path/to/repo`.

**Acceptance Scenarios**:

1. **Given** a valid Hermes config file containing a `--project` argument, **When** detect_repo_dir is called, **Then** it returns the correct absolute path.
2. **Given** no configs exist or have no `--project` argument, **When** detect_repo_dir is called, **Then** it returns `None`.

---

### Edge Cases

- **Credential Exposure**: What happens if check_credential_status receives secret values from the API? -> The bridge MUST never receive or log actual credential values. The API endpoints only return boolean configurations indicating configured/not-configured state.
- **Backend Timeouts**: What happens if the API backend hangs? -> The HTTP client enforces a strict 30-second timeout. If exceeded, a connection timeout error is returned gracefully.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The bridge code MUST reside in `hermes-plugin-wright/bridge.py`.
- **FR-002**: The bridge MUST export the constants `WRIGHT_API_BASE = "http://127.0.0.1:8000"` and `WRIGHT_UI_URL = "http://localhost:8000"`.
- **FR-003**: The bridge client MUST use `httpx.AsyncClient` with a timeout threshold of 30.0 seconds.
- **FR-004**: The bridge client MUST implement `detect_repo_dir()` to read `~/.hermes/profiles/wright/config.yaml` (with fallback to `~/.hermes/config.yaml`) and locate the `--project` argument value.
- **FR-005**: The client MUST provide `check_api_health()` calling `GET /api/health`.
- **FR-006**: The client MUST provide `get_mcp_servers()` calling `GET /api/mcp/servers`.
- **FR-007**: The client MUST provide `register_mcp_server(entry: CatalogEntry)` calling `POST /api/mcp/servers`.
- **FR-008**: The client MUST provide `get_workspaces()` calling `GET /api/workspace/list`.
- **FR-009**: The client MUST provide `get_credential_status(server_id: str)` calling `GET /api/mcp/servers/{server_id}/credentials`.
- **FR-010**: All HTTP methods MUST catch connection exceptions (e.g. `ConnectError`, `TimeoutException`) and return a structured dictionary containing `"success": False` and `"error"` instead of letting exceptions escape.
- **FR-011**: The client MUST NOT log, print, or expose any secret environment variables.
- **FR-012**: The package MUST include unit tests utilizing mock HTTP client handlers (e.g., `respx` or mock `httpx` routing).

### Key Entities

- **Bridge Client**: The asynchronous client engine managing network requests to the local FastAPI stack.
- **Repo Directory Detector**: The filesystem reader locating the project root from active Hermes configurations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Auto-detecting the repo path executes in under 2 milliseconds when the configuration file exists.
- **SC-002**: All network timeouts are correctly capped at 30 seconds, preventing infinite client hangs.
- **SC-003**: Zero raw HTTP exceptions are thrown to caller; 100% of network failures return normalized error dictionaries.

## Assumptions

- The local FastAPI server listens on port 8000.
- The Hermes profile path is relative to the user's home directory (`~`).
- The API responses conform to the standard schemas defined in the Wright monorepo.
