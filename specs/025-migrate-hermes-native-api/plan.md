# Implementation Plan: Migrate to Hermes Native API

**Branch**: `025-migrate-hermes-native-api` | **Date**: 2026-06-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/025-migrate-hermes-native-api/spec.md`

## Summary

Replace the third-party `hermes-webui` community server with the official Hermes native API gateway for all agent communication and MCP tool management. The migration eliminates a full proxy layer, removes process-restart-based MCP synchronization, and redesigns the `BaseAgentEngine` interface to align with the OpenAI-compatible streaming model shared by both Hermes and OpenClaw. The FastAPI router and React frontend are updated to use a unified single-POST streaming endpoint.

## Technical Context

**Language/Version**: Python 3.13 (FastAPI backend), React 19 (TypeScript frontend)

**Primary Dependencies**: `hermes-agent>=0.15.2` (pinned), `httpx` + `httpx-sse` (retained — used for all API calls including streaming via `aconnect_sse`)

**Storage**: SQLite (`state.db`) — no schema changes

**Testing**: pytest (adapter unit tests), Playwright (UI integration tests), Vitest (component tests)

**Target Platform**: Dell GB10 host (arm64/aarch64, Ubuntu 24.04), Docker container (Ubuntu 26.04)

**Project Type**: Modular Monorepo Web Application

**Performance Goals**: Chat first-token latency <3s, MCP tool toggle <5s without service interruption

**Constraints**: Offline-first execution, adapter pattern (Constitution §2), structured JSON logging (Constitution §7)

**Scale/Scope**: ~12 files modified/deleted, ~2 files created, 1 dependency added. Frontend `agent-service.ts` updated to use unified POST streaming.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **FastAPI strict typing (§1)**: YES. Router schemas updated (remove `ChatStartResponse`, add unified `ChatRequest`). All types remain Pydantic/dataclass.
- **Agent Abstraction / Adapter Pattern (§2)**: YES. The `BaseAgentEngine` abstract interface is **redesigned** to unify `start_chat()` + `stream_response()` into `stream_chat()`. The adapter pattern itself is preserved — only the method signatures change. All concrete adapters (Hermes, and future OpenClaw/PI/Qwen) must implement the new `stream_chat()` method.
- **Offline-First Mandate (§1)**: YES. The Hermes gateway runs locally. No external cloud dependency introduced.
- **Zero-Server Databases (§3)**: YES. SQLite remains the sole database. No new database servers introduced.
- **Modular Monorepo boundaries (§1)**: YES. Changes span `packages/agent_adapters`, `apps/api`, `apps/web/src/services/agent-service.ts`, and `docker/`.
- **Structured JSON Logging (§7)**: YES. All new adapter code uses `structlog` for logging.
- **Agent Traceability (§7)**: YES. Trace IDs continue to flow through the adapter via `AgentChatRequest.trace_id`. The unified `POST /chat` endpoint returns `X-Trace-Id` in the response header.
- **Test IDs (§6)**: N/A. No UI component markup changes — only the `agent-service.ts` transport layer is updated (EventSource → fetch+ReadableStream).

## Project Structure

### Documentation (this feature)

```text
specs/025-migrate-hermes-native-api/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research findings
├── data-model.md        # Configuration and API contract changes
├── quickstart.md        # Manual verification guide
└── checklists/
    └── requirements.md  # Spec quality validation checklist
```

### Source Code

```text
packages/agent_adapters/src/agent_adapters/
├── base.py                     # [MODIFY] Redesign: merge start_chat+stream_response → stream_chat
└── hermes.py                   # [MODIFY] Rewrite to use native API with stream_chat

apps/api/src/api/
├── config.py                   # [MODIFY] Rename constants, add API key
├── main.py                     # [MODIFY] Update config imports
├── services/
│   └── hermes_sync.py          # [MODIFY] Gut restart logic, keep static config write
└── routers/
    └── agent.py                # [MODIFY] Merge /chat/start + /chat/stream → POST /chat

packages/core/src/core/
└── agent_sync.py               # [MODIFY] Remove restart logic from _sync_to_hermes

apps/web/src/services/
└── agent-service.ts            # [MODIFY] Switch from EventSource to fetch+ReadableStream

docker/
├── Dockerfile                  # [MODIFY] Remove hermes-webui, add gateway config
└── supervisord.conf            # [MODIFY] Replace hermes-webui with hermes-gateway

scripts/
└── setup-wright-profile.sh     # [MODIFY] Use `hermes -p wright gateway start`

apps/api/tests/
└── test_hermes_adapter.py      # [MODIFY] Update tests for new API contract
```

**Structure Decision**: Monorepo Web Application layout. Changes span the adapter layer, API router, frontend service, and infrastructure. No new packages or directories introduced.

## Proposed Changes

### Component 0: BaseAgentEngine Interface Redesign

#### [MODIFY] [base.py](file:///home/burhop/repos/wright/packages/agent_adapters/src/agent_adapters/base.py)

Redesign the abstract interface to align with the OpenAI-compatible streaming model used by both Hermes and OpenClaw:

- **Replace** `start_chat(request) → AgentChatStartResponse` and `stream_response(stream_id) → AsyncIterator` with unified `stream_chat(request) → AsyncIterator[AgentStreamEvent]`
- **Remove** `AgentChatStartResponse` dataclass (the `stream_id` concept no longer exists)
- **Update** `cancel_chat(session_id, stream_id)` → `cancel_chat(session_id)` (remove stream_id param)
- **Keep** all other methods unchanged: `check_health`, `create_session`, `list_sessions`, `delete_session`, `get_session_workspace`, `save_context`, `load_context`, `get_chat_history`, `get_commands`

See [data-model.md](data-model.md) for the complete redesigned interface and rationale.

---

### Component 1: HermesAdapter Rewrite

#### [MODIFY] [hermes.py](file:///home/burhop/repos/wright/packages/agent_adapters/src/agent_adapters/hermes.py)

The core adapter rewrite. Replace all hermes-webui REST/SSE calls with native API calls:

- **`__init__`**: Accept `base_url` and `api_key`. Keep `httpx.AsyncClient` for health checks and session management REST calls.
- **`check_health()`**: Change from `GET /health` to `GET /health` (same pattern, new base URL). Add `Authorization: Bearer` header.
- **`create_session()`**: Change from `POST /api/session/new` to `POST /api/sessions`. Add auth header. Map response fields.
- **`list_sessions()`**: Change from `GET /api/sessions?all_profiles=0` to `GET /api/sessions`. Add auth header. Remove profile cookie.
- **`delete_session()`**: Change from `POST /api/session/delete` to `DELETE /api/sessions/{id}`. Add auth header.
- **`stream_chat()`**: NEW unified method. `POST /v1/chat/completions` with `stream: true`. Map `delta.content` → `token` events, `delta.tool_calls` → `tool` events, `hermes.tool.progress` → `progress` events, `[DONE]` → `stream_end`.
- **`get_chat_history()`**: Change from `GET /api/session?session_id=X&messages=1` to `GET /api/sessions/{id}/messages`. Map response.
- **`cancel_chat()`**: Abort the active HTTP connection for the session.
- **Remove**: `hermes_profile=wright` cookie. Replace with `Authorization: Bearer` header.
- **Remove**: `start_chat()` and `stream_response()` — replaced by `stream_chat()`.

---

### Component 2: Configuration Updates

#### [MODIFY] [config.py](file:///home/burhop/repos/wright/apps/api/src/api/config.py)

- Rename `HERMES_WEBUI_PORT` → `HERMES_API_PORT` (default `8642`)
- Rename `HERMES_WEBUI_BASE_URL` → `HERMES_API_BASE_URL` (default `http://127.0.0.1:8642`)
- Add `HERMES_API_KEY = os.getenv("HERMES_API_KEY", "wright-dev-key")` — the default is for local development only; production deployments MUST set the `HERMES_API_KEY` environment variable to a strong, unique secret

#### [MODIFY] [main.py](file:///home/burhop/repos/wright/apps/api/src/api/main.py)

- Update import from `HERMES_WEBUI_BASE_URL` to `HERMES_API_BASE_URL`
- Pass `HERMES_API_KEY` as second argument to `HermesAdapter(HERMES_API_BASE_URL, HERMES_API_KEY)`

---

### Component 2.5: Router Redesign

#### [MODIFY] [agent.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/agent.py)

Merge the two-endpoint chat flow into a single streaming POST endpoint:

- **Remove**: `POST /chat/start` endpoint and `ChatStartResponse` schema
- **Remove**: `GET /chat/stream` endpoint
- **Add**: `POST /chat` — unified endpoint that calls `engine.stream_chat(request)` and returns a `StreamingResponse` with SSE events. The `X-Trace-Id` header is included in the response for observability.
- **Update**: `POST /chat/cancel` — simplify to accept only `session_id` (remove `stream_id` query param)
- **Update**: Error messages to be agent-agnostic (replace "Hermes agent" with "Agent" in error details)
- **Keep**: All session management endpoints unchanged (`/sessions/new`, `/sessions`, `/sessions/{id}`, `/sessions/{id}/history`)
- **Keep**: `/commands`, `/active` endpoints unchanged

---

### Component 2.6: Frontend Update

#### [MODIFY] [agent-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/agent-service.ts)

Switch from the two-step EventSource pattern to POST-based streaming:

- **Replace**: `fetch("/api/agent/chat/start")` + `new EventSource("/api/agent/chat/stream?stream_id=X")` with single `fetch("/api/agent/chat", { method: "POST", ... })` + `ReadableStream` SSE parsing
- **Remove**: `stream_id` concept entirely. Remove `stream_start` event yield.
- **Add**: SSE line parser for the `response.body` ReadableStream (parse `event:` and `data:` lines)
- **Update**: `cancelStream()` — call `POST /api/agent/chat/cancel` with only `session_id`
- **Update**: Error messages to be agent-agnostic (replace "Hermes" references)
- **Keep**: All event handler logic (`token`, `tool`, `progress`, `stream_end`, `error`) unchanged — same event names, same data shapes

> **Note**: The `EventSource` API only supports GET requests. Since the new endpoint uses POST, we switch to `fetch()` + manual SSE parsing from the response body. This is the standard pattern used by ChatGPT, Claude, and every modern AI chat frontend. A lightweight alternative is `@microsoft/fetch-event-source`.

---

### Component 3: MCP Sync Simplification

#### [MODIFY] [hermes_sync.py](file:///home/burhop/repos/wright/apps/api/src/api/services/hermes_sync.py)

- **Keep**: `_write_static_hermes_config()` — still needed to ensure the `wrightgateway` MCP server entry exists in `config.yaml` at startup
- **Remove**: `restart_hermes_background()` function entirely (lines 162-212)
- **Simplify**: `sync_mcp_server_to_hermes()` — write config if needed, then call `notify_gateway_tool_change()` (no restart fallback)
- **Simplify**: `sync_workspace_tools_to_hermes()` — write config + gitignore + hermes.md, then call `notify_gateway_tool_change()` (no restart fallback)

#### [MODIFY] [agent_sync.py](file:///home/burhop/repos/wright/packages/core/src/core/agent_sync.py)

- **Remove**: Lines 161-202 — the `fuser -k`, `ctl.sh stop/start`, and health-check polling loop in `_sync_to_hermes()`
- **Replace with**: After writing config, call `notify_gateway_tool_change()` via the API gateway SSE notification path. If config changed, log a message that the gateway will auto-reload.

---

### Component 4: Docker & Infrastructure

#### [MODIFY] [Dockerfile](file:///home/burhop/repos/wright/docker/Dockerfile)

- **Remove**: Lines 87-97 — the entire hermes-webui git clone, venv creation, and requirements.txt installation block
- **Add**: Write `API_SERVER_ENABLED=true`, `API_SERVER_KEY`, and `API_SERVER_PORT=8642` to the wright profile `.env` during build
- **Keep**: `hermes-agent==0.15.2` installation via `uv tool install` (line 84)

#### [MODIFY] [supervisord.conf](file:///home/burhop/repos/wright/docker/supervisord.conf)

- **Replace** `[program:hermes-webui]` (lines 29-42) with:
  ```ini
  [program:hermes-gateway]
  command=/usr/local/bin/hermes -p wright gateway
  environment=HERMES_HOME="/home/agent/.hermes/profiles/wright"
  autostart=true
  autorestart=true
  startsecs=5
  stopwaitsecs=10
  stdout_logfile=/var/log/supervisor/hermes-gateway-stdout.log
  stderr_logfile=/var/log/supervisor/hermes-gateway-stderr.log
  stdout_logfile_maxbytes=10MB
  stderr_logfile_maxbytes=10MB
  ```

---

### Component 5: Local Development Setup

#### [MODIFY] [setup-wright-profile.sh](file:///home/burhop/repos/wright/scripts/setup-wright-profile.sh)

- Replace `ctl.sh start 8788` with `hermes -p wright gateway start`
- Replace health check URL from `http://127.0.0.1:8788/health` to `http://127.0.0.1:8642/health`
- Add API server configuration step: enable `API_SERVER_ENABLED` and set `API_SERVER_KEY`

---

### Component 6: Test Updates

#### [MODIFY] [test_hermes_adapter.py](file:///home/burhop/repos/wright/apps/api/tests/test_hermes_adapter.py)

- Update all `HermesAdapter("http://127.0.0.1:8788")` instantiations to `HermesAdapter("http://127.0.0.1:8642", "test-key")`
- Update mocked endpoints to match native API paths (`/api/sessions` instead of `/api/session/new`, etc.)
- Add test for `hermes.tool.progress` event parsing
- Add test for OpenAI streaming format parsing

## Verification Plan

### Automated Tests

```bash
# Unit tests for the rewritten adapter
uv run pytest apps/api/tests/test_hermes_adapter.py -v

# Full test suite regression check
uv run pytest apps/api/tests/ -v

# Frontend component tests
npm test --workspace=apps/web

# UI integration tests (requires running backend)
npx playwright test tests/ui-integration/
```

### Manual Verification

Follow the [quickstart.md](quickstart.md) verification checklist:

1. Start the Hermes gateway for the wright profile
2. Start the Wright API
3. Verify health endpoints report connected
4. Create a workspace and send a chat message
5. Verify streamed response with tool indicators
6. Toggle an MCP tool and verify it takes effect without restart
7. Build the Docker image and verify supervised processes

## Complexity Tracking

*No complexity violations present. No exceptions required.*
