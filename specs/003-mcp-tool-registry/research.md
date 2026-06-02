# Research: MCP & Tool Registry

**Branch**: `003-mcp-tool-registry` | **Date**: 2026-06-02

## Technical Decisions

### 1. Tool Configuration and State Persistence
- **Decision**: Persist MCP Server configurations and active tools in the local SQLite database.
- **Rationale**: Keeps database administration overhead zero. SQLite WAL mode provides reliable concurrent reads/writes for tool states. This satisfies the "zero-server database" mandate of the constitution.
- **Alternatives Considered**: File-based JSON configuration. Rejected because runtime edits (activating/deactivating tools, custom tool installations) require file locking which is prone to concurrency bugs in multi-process environments.

### 2. Spawning and Controlling Stdio MCP Servers
- **Decision**: Use Python's native `asyncio.create_subprocess_exec` to launch stdio CLI MCP servers, using non-blocking stdin/stdout readers.
- **Rationale**: Fits FastAPI's async loops natively and provides safe process isolation. Terminating processes can be done cleanly with SIGTERM/SIGKILL after a 60-second timeout.
- **Alternatives Considered**: Synchronous subprocess calls. Rejected because blocking the async thread pool would freeze the FastAPI web server.

### 3. Remote HTTP SSE Client Connections
- **Decision**: Use `httpx` and `httpx_sse` to handle connection handshakes and consume events from external HTTP SSE-based MCP endpoints.
- **Rationale**: Reuses the core monorepo client libraries already verified in the Hermes adapter, reducing dependency overhead.

### 4. WebMCP Frontend Viewport Hooking
- **Decision**: Implement a client-side WebMCP coordinator that listens to a custom DOM event channel (e.g. `webmcp:tool-call`).
- **Rationale**: Decouples the 3D viewport canvas or vault explorer from the chat component. Any component can register its state reader to this window channel, allowing the chat coordinator to query client state dynamically on behalf of the LLM agent.

### 5. MCP-UI Rich Renderers
- **Decision**: Define a standardized UI schema payload that tools can return. The frontend message component maps these payloads to visual patterns (e.g. progress bar, data grid, simulation run card).
- **Rationale**: Prevents hardcoding rendering logic in the chat component, keeping the UI extensible. The payload includes `{ renderType: 'progress' | 'metrics' | 'log-view', data: {...} }`.
