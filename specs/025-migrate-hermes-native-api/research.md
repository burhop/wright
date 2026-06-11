# Research: Migrate to Hermes Native API

**Feature**: 025-migrate-hermes-native-api | **Date**: 2026-06-11

## R1: Official Hermes API Server Capabilities

**Decision**: Use the official Hermes gateway API server (`hermes gateway` with `API_SERVER_ENABLED=true`) running on port 8642 as the replacement for hermes-webui on port 8788.

**Rationale**: The official API server is a first-class component of `hermes-agent`, maintained by Nous Research. It exposes both an OpenAI-compatible `/v1/chat/completions` endpoint and a REST session management API under `/api/sessions/*`. This eliminates the need for the community `hermes-webui` intermediary entirely.

**Key Findings**:
- **Configuration**: Enabled via `API_SERVER_ENABLED=true` and `API_SERVER_KEY=<secret>` in `~/.hermes/.env` (or `hermes config set`)
- **Default Port**: 8642, configurable via `API_SERVER_PORT`
- **Authentication**: Bearer token via `Authorization: Bearer <API_SERVER_KEY>` header on all requests
- **Not a proxy**: The API server is a full agent runtime — it spawns agent processes on the host with full tool access
- **Current pinned version**: Our Dockerfile uses `hermes-agent==0.15.2`. The gateway API server is available in v0.15+

**Alternatives Considered**:
- Keep hermes-webui: Rejected — adds unnecessary proxy layer, requires separate venv, has custom non-standard API
- Direct OpenAI SDK from React frontend: Rejected — violates constitution's API routing rules and loses trace ID injection

---

## R2: Session Management API

**Decision**: Use the native `/api/sessions` REST endpoints for session CRUD, replacing hermes-webui's custom `/api/session/new`, `/api/sessions`, and `/api/session/delete` endpoints.

**Rationale**: The native API provides equivalent session management with a cleaner REST interface and built-in authentication.

**Key Findings**:

| Operation | hermes-webui (current) | Native API (new) |
|-----------|----------------------|------------------|
| Create session | `POST /api/session/new` | `POST /api/sessions` |
| List sessions | `GET /api/sessions?all_profiles=0` | `GET /api/sessions` |
| Get session | `GET /api/session?session_id=X&messages=1` | `GET /api/sessions/{id}` |
| Delete session | `POST /api/session/delete` | `DELETE /api/sessions/{id}` |
| Get history | `GET /api/session?session_id=X&messages=1` | `GET /api/sessions/{id}/messages` |

**Workspace Context**: The native API does not have a dedicated `workspace` field in `POST /api/sessions`. Workspace association will continue to be managed by Wright's SQLite database (as it is today), with the workspace path injected into the system prompt or session metadata. This is functionally equivalent to the current approach where hermes-webui stores a `workspace` string per session.

**Alternatives Considered**:
- Custom session tracking in Wright only: Rejected — would lose Hermes-side session persistence and history

---

## R3: Streaming Response Format

**Decision**: Use the OpenAI-compatible `/v1/chat/completions` streaming endpoint with `stream: true`, consuming both standard `chat.completion.chunk` events and the custom `hermes.tool.progress` SSE events.

**Rationale**: The streaming format maps cleanly to our existing `AgentStreamEvent` types, requiring only a translation layer in the adapter.

**Key Findings**:

### Event Mapping

| Native API Event | Wright AgentStreamEvent | Notes |
|-----------------|------------------------|-------|
| `chat.completion.chunk` (delta.content) | `token` | Text tokens streamed to UI |
| `chat.completion.chunk` (delta.tool_calls) | `tool` | Tool invocation with name + accumulated args |
| `hermes.tool.progress` | `progress` | Custom SSE event: `{tool, emoji, label, toolCallId, status}` |
| Stream end (`[DONE]`) | `stream_end` | Standard OpenAI stream termination |
| Error / connection failure | `error` | Map to error message |

### Implementation Approach
- Use the `openai` Python SDK with `base_url` pointing to `http://127.0.0.1:8642/v1`
- Set `api_key` to the configured `API_SERVER_KEY`
- Use `client.chat.completions.create(stream=True)` for streaming
- Parse `hermes.tool.progress` events via raw SSE handling (the OpenAI SDK passes through custom events)
- Accumulate `delta.tool_calls[].function.arguments` chunks into complete JSON before yielding tool events

**Alternatives Considered**:
- Raw `httpx` SSE client (current approach): Viable but more code than using the OpenAI SDK
- `httpx-sse` library: Current adapter already uses this; could keep it but gains no standardization benefit

---

## R4: MCP Dynamic Tool Management

**Decision**: Use the Hermes gateway's config file watching mechanism for MCP tool changes. When Wright updates `config.yaml`, the gateway automatically detects changes and refreshes MCP connections — no process restart needed.

**Rationale**: The hermes gateway watches `~/.hermes/profiles/wright/config.yaml` for changes. When the `mcp_servers` block is updated, it re-establishes MCP connections automatically. This eliminates the `fuser -k -n tcp 8788` + `ctl.sh stop/start` restart cycle.

**Key Findings**:
- The gateway attempts auto-reload of MCP configs on file change
- Known limitation: some edge cases may require `hermes gateway restart` for clean state
- Our architecture mitigates this because we use a single `wrightgateway` MCP server that itself proxies to individual tools via the wright-gateway stdio bridge. The gateway only sees one MCP server that never changes — tool changes are handled inside our gateway bridge via the `notifications/tools/list_changed` JSONRPC notification
- The existing `gateway.py` stdio bridge already supports `listChanged: true` capability and sends `notifications/tools/list_changed` when tools change — this is the correct MCP protocol mechanism for dynamic tool updates

**Simplified MCP Architecture**:
```
Wright UI → toggle tool → API → SQLite update → SSE notify gateway.py
                                                        ↓
                                            gateway.py sends JSONRPC
                                            notifications/tools/list_changed
                                                        ↓
                                            Hermes gateway re-fetches
                                            tools/list from gateway.py
```

This means:
1. `hermes_sync.py` restart logic is **completely eliminated**
2. `agent_sync.py` restart logic is **completely eliminated**  
3. `config.yaml` is written once at startup (static `wrightgateway` entry) and never needs updating
4. Tool changes flow through the existing `gateway.py` → JSONRPC notification path

**Alternatives Considered**:
- Write individual MCP server entries to config.yaml per tool: Rejected — our gateway bridge pattern is cleaner and avoids config file churn
- Use experimental `mcp-add`/`mcp-remove` runtime commands: Rejected — not stable enough and would require agent-side changes

---

## R5: Profile Isolation

**Decision**: Use `HERMES_HOME=~/.hermes/profiles/wright` environment variable when starting the gateway, combined with the `--profile wright` CLI flag. This replaces the `hermes_profile=wright` cookie used by hermes-webui.

**Rationale**: The native Hermes gateway supports profiles as a first-class concept. Each profile has its own `HERMES_HOME` directory containing isolated config, sessions, .env, and state. Running `hermes -p wright gateway start` starts a gateway bound to the wright profile.

**Key Findings**:
- Profiles reside in `~/.hermes/profiles/<name>/`
- Each profile has its own `config.yaml`, `.env`, sessions, skills
- Gateway can be started per-profile: `hermes -p wright gateway start`
- Multiple gateways can run concurrently on different ports
- Profile creation: `hermes profile create wright --clone` (already done in our setup)
- Authentication is per-profile via `API_SERVER_KEY` in the profile's `.env`

**Alternatives Considered**:
- Single shared profile with session-level filtering: Rejected — violates isolation principle and risks cross-contamination
