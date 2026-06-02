# Research: Hermes & LLM Integration

**Branch**: `002-hermes-llm-integration` | **Date**: 2026-06-02

## Decision 1: Hermes Profile Isolation Strategy

**Decision**: Use `hermes profile create wright --clone` to create an isolated profile sharing the same Python/venv install but with its own HERMES_HOME under `~/.hermes/profiles/wright/`.

**Rationale**: The Reddit thread (r/hermesagent) and the local `hermes profile create --help` confirm that each profile gets its own isolated HERMES_HOME directory. The `--clone` flag copies `config.yaml`, `.env`, and `SOUL.md` from the active profile, meaning the "wright" profile automatically inherits the LLM provider/base_url configuration. Sessions, skills, and state.db are independent.

**Alternatives considered**:
- **Shared profile with tagged sessions**: Would contaminate the user's personal Hermes sessions. Rejected per constitution mandate for isolation.
- **Separate Hermes installation**: Wasteful — profiles share the same venv and agent code. Only the data directory differs.
- **Docker-based isolation**: Out of scope for this phase per spec constraints.

## Decision 2: Wright API ↔ Hermes WebUI Communication Protocol

**Decision**: The Wright FastAPI backend will act as an HTTP proxy to the Hermes WebUI API. Chat requests go through `POST /api/chat/start` (returns `stream_id`) followed by `GET /api/chat/stream?stream_id=<id>` (SSE stream).

**Rationale**: Direct inspection of the hermes-webui `routes.py` reveals this two-phase protocol:
1. `POST /api/chat/start` — accepts `{session_id, message, profile?, model?}` → returns `{stream_id, session_id}`
2. `GET /api/chat/stream?stream_id=<id>` — returns SSE events: `token`, `tool`, `stream_end`, `error`, `cancel`
3. `POST /api/session/new` — creates a new session → returns `{session_id}`
4. `GET /api/sessions` — lists all sessions → returns session array

This is a well-defined, stable internal API.

**Alternatives considered**:
- **WebSocket proxy**: Hermes WebUI uses SSE, not WebSocket. Adding a WebSocket layer would require protocol translation with no benefit.
- **Direct frontend → Hermes**: Violates constitution requirement that all traffic routes through the Wright API for adapter abstraction and traceability.
- **Import Hermes Python modules**: Tight coupling, version fragility, and violates constitution's adapter pattern mandate.

## Decision 3: SSE Forwarding Strategy (Backend → Frontend)

**Decision**: Use FastAPI's `StreamingResponse` with `media_type="text/event-stream"` to forward the Hermes SSE stream. The backend opens an `httpx` async streaming connection to the Hermes WebUI and re-emits each SSE event to the frontend, adding Wright-specific metadata (trace_id, timestamps).

**Rationale**: This approach:
- Preserves token-by-token streaming (first token visible within seconds)
- Allows the Wright API to inject OpenTelemetry spans and structured logs per constitution mandate
- Keeps the frontend Hermes-agnostic — it only speaks to the Wright API
- Uses httpx (already available via uvicorn's `[standard]` extras) for async HTTP

**Alternatives considered**:
- **Buffered proxy (collect full response, then send)**: Destroys streaming UX. Rejected.
- **Server-Sent Events directly from Wright API (no Hermes)**: Would require implementing the entire agent runtime. Completely out of scope.

## Decision 4: Agent Adapter Pattern Implementation

**Decision**: Implement a `BaseAgentEngine` abstract class in `packages/agent_adapters/` with a concrete `HermesAdapter` subclass. The Wright API routes call only the abstract interface, never Hermes directly.

**Rationale**: Constitution §2 mandates: "LLM agents MUST NOT be hardcoded into the API. They MUST be integrated via an Adapter Pattern (BaseAgentEngine) to allow hot-swapping." The `agent_adapters` package already exists with this docstring.

**Alternatives considered**:
- **Direct HTTP calls in route handlers**: Violates constitution. Rejected.
- **Plugin/registry pattern**: Overkill for v1 with a single adapter. Can be added later without breaking the adapter interface.

## Decision 5: Hermes WebUI Startup for Wright Profile

**Decision**: The Wright setup script will start a dedicated Hermes WebUI instance for the "wright" profile on port 8788 (default Hermes WebUI is 8787). The Wright API `config.py` will store this base URL.

**Rationale**: The Hermes WebUI is a per-profile server. The existing default profile's WebUI runs on port 8787. A second instance for the "wright" profile needs its own port. The `ctl.sh` script in hermes-webui supports `--port` and `HERMES_HOME` environment variables for multi-instance operation.

**Alternatives considered**:
- **Share the default WebUI**: The default WebUI serves the default profile. Profile switching via cookies would contaminate the user's session state. Rejected.
- **Use Hermes CLI directly**: The CLI is synchronous and doesn't provide SSE streaming. Rejected.

## Decision 6: Frontend Agent Service Refactoring

**Decision**: Replace `StubAgentService` with `HermesAgentService` that calls the Wright API (`/api/agent/chat/start`, `/api/agent/chat/stream`) using `fetch` + `EventSource`. The `AgentEvent` type interface remains unchanged.

**Rationale**: The existing `StubAgentService` already defines the correct `AgentEvent` type union (`token`, `tool`, `done`, `error`) and the `AsyncIterable<AgentEvent>` streaming interface. The real service implementation swaps the fake delay loop for real SSE consumption. No store or component changes needed.

**Alternatives considered**:
- **Rewrite the store/reducer**: Unnecessary — the store already handles `AgentEvent` correctly.
- **Use a WebSocket library**: The Wright API will emit SSE, which the browser's `EventSource` API handles natively. No extra dependency needed.

## Decision 7: Health Check Implementation

**Decision**: Replace the stub health endpoints in the Wright API with real connectivity checks:
- `/api/agent/health` → `GET http://127.0.0.1:8788/api/health` (wright profile WebUI)
- `/api/inference/health` → `GET http://<vllm_host>:8000/health` (LLM inference server)

**Rationale**: The frontend health polling infrastructure already exists and polls these endpoints every 15 seconds. Only the backend stubs need to make real HTTP requests.

**Alternatives considered**:
- **Frontend direct health checks**: CORS issues and violates the proxy architecture. Rejected.
