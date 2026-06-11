# Data Model: Migrate to Hermes Native API

**Feature**: 025-migrate-hermes-native-api | **Date**: 2026-06-11

## Overview

This migration does **not** change Wright's SQLite schema. All existing tables (`engineering_workspaces`, `mcp_servers`, `mcp_tools`, `system_settings`) remain unchanged. The changes are limited to how the `HermesAdapter` communicates with the agent backend, how MCP configuration is synchronized, and a redesign of the `BaseAgentEngine` / router interface to align with the OpenAI-compatible streaming model shared by both Hermes and OpenClaw.

## Entities Unchanged

### engineering_workspaces
No schema changes. Session-to-workspace binding continues to use `session_id` column.

### mcp_servers / mcp_tools
No schema changes. The tool registry and workspace-level enablement continue to work through SQLite.

### system_settings
No schema changes. The `active_agent` key continues to control which adapter is active.

## Configuration Changes

### Hermes Profile Environment (NEW)

**Location**: `~/.hermes/profiles/wright/.env`

| Key | Value | Notes |
|-----|-------|-------|
| `API_SERVER_ENABLED` | `true` | Enables the native API server |
| `API_SERVER_KEY` | `<generated-secret>` | Bearer token for API auth |
| `API_SERVER_PORT` | `8642` | Default port (configurable) |

### Wright API Config Constants (MODIFIED)

**File**: `apps/api/src/api/config.py`

| Constant | Old Value | New Value |
|----------|-----------|-----------|
| `HERMES_WEBUI_PORT` | `8788` | Renamed to `HERMES_API_PORT`, default `8642` |
| `HERMES_WEBUI_BASE_URL` | `http://127.0.0.1:8788` | Renamed to `HERMES_API_BASE_URL`, default `http://127.0.0.1:8642` |
| `HERMES_API_KEY` | N/A (NEW) | Loaded from env `HERMES_API_KEY` |

### Hermes Profile Config (SIMPLIFIED)

**Location**: `~/.hermes/profiles/wright/config.yaml`

Written once at startup. No longer needs to be rewritten on every MCP tool change:

```yaml
mcp_servers:
  wrightgateway:
    command: uv
    args:
      - run
      - --project
      - /home/burhop/repos/wright
      - python
      - -m
      - tool_registry.gateway
```

---

## Agent API Redesign: Hermes + OpenClaw Common Interface

### Why the current interface doesn't fit

The current `BaseAgentEngine` interface was designed around hermes-webui's **two-step** protocol:

1. `POST /api/chat/start` → returns `stream_id`
2. `GET /api/chat/stream?stream_id=X` → returns SSE events

Both the **Hermes native API** and **OpenClaw** use the **OpenAI-compatible** pattern instead:

1. `POST /v1/chat/completions` with `stream: true` → **returns SSE events inline, in the same response**

There is no `stream_id`. The response IS the stream. This is how every modern LLM API works.

The current split (`start_chat()` → `stream_response(stream_id)`) forces adapters to invent a fake `stream_id`, store the async iterator in a dict, and retrieve it later — an unnecessary stateful dance that adds complexity and creates race conditions.

### Cross-Agent API Comparison

| Capability | Hermes Native API | OpenClaw |
|-----------|------------------|----------|
| **Chat endpoint** | `POST /v1/chat/completions` | `POST /v1/chat/completions` |
| **Streaming** | `stream: true` → SSE inline | `stream: true` → SSE inline |
| **Auth** | `Authorization: Bearer <key>` | `Authorization: Bearer <key>` |
| **Session create** | `POST /api/sessions` | Auto-created via `x-openclaw-session-key` header |
| **Session list** | `GET /api/sessions` | `openclaw sessions` CLI / `sessions_list` tool |
| **Session delete** | `DELETE /api/sessions/{id}` | `/new` command or file deletion |
| **Chat history** | `GET /api/sessions/{id}/messages` | Stored in `.jsonl` transcript files |
| **Tool events** | `hermes.tool.progress` custom SSE event | `tool_calls` in `delta` (standard OpenAI) |
| **Session ID in chat** | `session_id` in request body or header | `x-openclaw-session-key` header |
| **MCP support** | Native `config.yaml` → auto-reload | Gateway-managed tool/skill system |
| **Default port** | `8642` | `18789` |

### Key Observation

Both agents speak the same core language: **OpenAI `/v1/chat/completions` with streaming**. The differences are in session management and tool progress events — not in the chat protocol itself.

### Redesigned BaseAgentEngine Interface

```python
class BaseAgentEngine(ABC):
    """Abstract base for all agent adapters (Constitution §2)."""

    @abstractmethod
    async def check_health(self) -> dict:
        """Return {"state": "connected"|"disconnected", "latencyMs": float}."""

    @abstractmethod
    async def create_session(
        self, workspace: str | None = None, instructions: str | None = None
    ) -> AgentSessionInfo:
        """Create a new agent session."""

    @abstractmethod
    async def list_sessions(self) -> list[AgentSessionInfo]:
        """List all sessions for this adapter's profile."""

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if deleted."""

    @abstractmethod
    async def stream_chat(
        self, request: AgentChatRequest
    ) -> AsyncIterator[AgentStreamEvent]:
        """Send a message and stream back the agent's response.

        This is a unified operation: it sends the user message to the
        agent backend and yields SSE events as they arrive. There is
        no separate start/stream handoff.

        Adapters map their backend's streaming format to AgentStreamEvent:
        - "token": text content delta
        - "tool": tool invocation (name, args, call_id)
        - "progress": tool execution progress (tool name, status, label)
        - "stream_end": response complete
        - "error": error occurred
        """

    @abstractmethod
    async def get_session_workspace(self, session_id: str) -> str | None:
        """Retrieve the workspace path for a given session ID."""

    @abstractmethod
    async def save_context(self, session_id: str, workspace_id: str) -> bool:
        """Save agent context for a workspace."""

    @abstractmethod
    async def load_context(self, session_id: str, workspace_id: str) -> dict | None:
        """Load agent context for a workspace."""

    @abstractmethod
    async def get_chat_history(self, session_id: str) -> list[AgentChatMessage]:
        """Retrieve the full chat message history for a session."""

    @abstractmethod
    async def get_commands(self) -> list[AgentCommand]:
        """Retrieve the available slash commands from the agent engine."""

    async def cancel_chat(self, session_id: str) -> bool:
        """Cancel an active response stream. Returns True if accepted."""
        return False
```

### What Changed

| Old Interface | New Interface | Why |
|--------------|--------------|-----|
| `start_chat(request) → AgentChatStartResponse` | **REMOVED** | Two-step protocol was hermes-webui specific |
| `stream_response(stream_id) → AsyncIterator` | **REMOVED** | Stream ID concept doesn't exist in OpenAI API |
| N/A | `stream_chat(request) → AsyncIterator` | **NEW** — unified send+stream, matches OpenAI protocol used by both Hermes and OpenClaw |
| `cancel_chat(session_id, stream_id)` | `cancel_chat(session_id)` | Removed `stream_id` param — cancel by session, not by stream |

### Removed Dataclass

```python
# DELETED — no longer needed
@dataclass
class AgentChatStartResponse:
    stream_id: str
    session_id: str
```

### Redesigned FastAPI Router

The `agent.py` router also simplifies. Instead of two endpoints (`POST /chat/start` + `GET /chat/stream`), we merge into a single streaming endpoint:

#### Old Router (TWO endpoints)

```
POST /api/agent/chat/start    → returns {stream_id, session_id, trace_id}
GET  /api/agent/chat/stream   → SSE stream keyed by stream_id
```

#### New Router (ONE endpoint)

```
POST /api/agent/chat           → SSE stream (direct response)
POST /api/agent/chat/cancel    → cancel active stream
```

```python
@router.post("/chat")
@traced("agent.chat")
async def chat(
    body: ChatRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
):
    """Unified chat endpoint: send message and stream response."""
    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id, session_id=body.session_id)
    log.info("chat_requested")

    # Sync workspace tools before chat turn
    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        try:
            sync_manager.sync_workspace_tools(body.session_id)
        except Exception as e:
            log.warn("Failed to sync workspace tools", error=str(e))

    chat_request = AgentChatRequest(
        session_id=body.session_id,
        message=body.message,
        trace_id=trace_id,
        attachments=body.attachments,
    )

    async def sse_generator() -> AsyncIterator[str]:
        try:
            async for event in engine.stream_chat(chat_request):
                yield f"event: {event.type}\ndata: {json.dumps(event.data)}\n\n"
        except Exception as exc:
            log.exception("chat_stream_failed", error=str(exc))
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Trace-Id": trace_id,
        },
    )
```

### Frontend Impact

The `agent-service.ts` currently does:

```typescript
// OLD — two-step
const { stream_id } = await fetch("/api/agent/chat/start", { method: "POST", ... }).json();
const eventSource = new EventSource(`/api/agent/chat/stream?stream_id=${stream_id}`);
```

It becomes:

```typescript
// NEW — single POST, read stream from response body
const response = await fetch("/api/agent/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ session_id, message, attachments }),
});
// Use ReadableStream or EventSource wrapper to consume SSE from response body
const reader = response.body.getReader();
// ... parse SSE events from the ReadableStream
```

> **Note**: `EventSource` only supports GET requests. Since we're switching to POST, the frontend will use `fetch()` with `response.body` as a ReadableStream and parse SSE events manually (or use a lightweight library like `@microsoft/fetch-event-source`). This is a standard pattern used by ChatGPT, Claude, and every modern AI frontend.

### How Adapters Implement stream_chat()

#### HermesAdapter.stream_chat()

```python
async def stream_chat(self, request: AgentChatRequest) -> AsyncIterator[AgentStreamEvent]:
    """Stream chat via Hermes native OpenAI-compatible API."""
    messages = await self._build_messages(request)

    async with httpx.AsyncClient() as client:
        async with aconnect_sse(
            client, "POST",
            f"{self.base_url}/v1/chat/completions",
            json={"model": "hermes", "messages": messages, "stream": True},
            headers={"Authorization": f"Bearer {self.api_key}"},
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event == "hermes.tool.progress":
                    data = json.loads(sse.data)
                    yield AgentStreamEvent(type="progress", data=data)
                elif sse.data == "[DONE]":
                    yield AgentStreamEvent(type="stream_end", data={})
                else:
                    chunk = json.loads(sse.data)
                    delta = chunk["choices"][0]["delta"]
                    if delta.get("content"):
                        yield AgentStreamEvent(type="token", data={"text": delta["content"]})
                    if delta.get("tool_calls"):
                        yield AgentStreamEvent(type="tool", data={"tool_calls": delta["tool_calls"]})
```

#### OpenClawAdapter.stream_chat()

```python
async def stream_chat(self, request: AgentChatRequest) -> AsyncIterator[AgentStreamEvent]:
    """Stream chat via OpenClaw OpenAI-compatible API."""
    messages = await self._build_messages(request)

    async with httpx.AsyncClient() as client:
        async with aconnect_sse(
            client, "POST",
            f"{self.base_url}/v1/chat/completions",
            json={"model": "openclaw", "messages": messages, "stream": True},
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "x-openclaw-session-key": f"agent:wright:{request.session_id}",
            },
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.data == "[DONE]":
                    yield AgentStreamEvent(type="stream_end", data={})
                else:
                    chunk = json.loads(sse.data)
                    delta = chunk["choices"][0]["delta"]
                    if delta.get("content"):
                        yield AgentStreamEvent(type="token", data={"text": delta["content"]})
                    if delta.get("tool_calls"):
                        yield AgentStreamEvent(type="tool", data={"tool_calls": delta["tool_calls"]})
```

The two implementations are nearly identical because **both backends speak the same protocol**.

---

## Session Management Abstraction

Session CRUD differs more between backends than chat streaming does. Here's how each adapter handles it:

| Operation | HermesAdapter | OpenClawAdapter |
|-----------|--------------|-----------------|
| **create_session** | `POST /api/sessions` → session_id | Auto-created via `x-openclaw-session-key` on first chat; Wright generates the session_id locally |
| **list_sessions** | `GET /api/sessions` → filter by workspace | Query Wright's SQLite directly (OpenClaw sessions are file-based, Wright is the source of truth) |
| **delete_session** | `DELETE /api/sessions/{id}` | Remove session files from `~/.openclaw/agents/wright/sessions/` |
| **get_chat_history** | `GET /api/sessions/{id}/messages` | Parse `.jsonl` transcript files from disk |

The `BaseAgentEngine` interface handles this naturally — each adapter implements the same abstract methods using its backend's specific mechanism.

---

## Files Deleted

| File | Reason |
|------|--------|
| `hermes_sync.py` restart logic | Gateway handles MCP reload automatically |
| hermes-webui Dockerfile block | No longer cloning community server |
| hermes-webui supervisord entry | Replaced with hermes gateway process |
| `setup-wright-profile.sh` ctl.sh calls | Replaced with `hermes -p wright gateway start` |

## Files Changed for API Redesign

| File | Change |
|------|--------|
| `packages/agent_adapters/src/agent_adapters/base.py` | Replace `start_chat()` + `stream_response()` with `stream_chat()`. Remove `AgentChatStartResponse`. |
| `apps/api/src/api/routers/agent.py` | Merge `POST /chat/start` + `GET /chat/stream` into single `POST /chat`. Remove `ChatStartResponse` schema. |
| `apps/web/src/services/agent-service.ts` | Switch from `EventSource` (GET) to `fetch` + `ReadableStream` (POST). Remove `stream_id` concept. |
