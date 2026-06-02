# API & Service Contracts: Hermes & LLM Integration

**Branch**: `002-hermes-llm-integration` | **Date**: 2026-06-02

## 1. Wright API → Frontend Contracts

### 1.1 Agent Chat Start

```
POST /api/agent/chat/start
Content-Type: application/json

Request:
{
  "session_id": string,    // Wright session ID
  "message": string        // User message text
}

Response 200:
{
  "stream_id": string,     // SSE stream identifier
  "session_id": string,    // Confirmed session ID
  "trace_id": string       // OpenTelemetry trace ID
}

Response 400: { "error": string }
Response 502: { "error": "Hermes agent unavailable" }
```

### 1.2 Agent Chat Stream (SSE)

```
GET /api/agent/chat/stream?stream_id=<id>
Accept: text/event-stream

SSE Events:

event: token
data: {"text": "partial response text"}

event: tool
data: {"name": "tool_name", "preview": "description of tool action"}

event: stream_end
data: {"session_id": "...", "message_id": "...", "token_count": 42}

event: error
data: {"message": "error description"}

: heartbeat  (every 5s during idle)
```

### 1.3 Session Management

```
POST /api/agent/sessions/new
Content-Type: application/json

Request:
{
  "workspace": string?     // Optional workspace path
}

Response 200:
{
  "session_id": string,
  "title": string,
  "created_at": int        // epoch ms
}
```

```
GET /api/agent/sessions
Response 200:
{
  "sessions": [
    {
      "session_id": string,
      "title": string,
      "created_at": int,
      "updated_at": int,
      "message_count": int
    }
  ]
}
```

```
DELETE /api/agent/sessions/<session_id>
Response 200: { "ok": true }
Response 404: { "error": "Session not found" }
```

### 1.4 Health Endpoints

```
GET /api/agent/health
Response 200: { "state": "connected"|"disconnected", "latencyMs": float }

GET /api/inference/health
Response 200: { "state": "connected"|"disconnected", "latencyMs": float }
```

## 2. Wright API → Hermes WebUI Contracts (Internal)

These are the Hermes WebUI API endpoints consumed by the Wright backend proxy.

### 2.1 Session New

```
POST http://127.0.0.1:8788/api/session/new
Content-Type: application/json
Cookie: hermes_session=<auth_cookie>

Request: { "workspace": string? }
Response: { "session_id": string, ... }
```

### 2.2 Chat Start

```
POST http://127.0.0.1:8788/api/chat/start
Content-Type: application/json
Cookie: hermes_session=<auth_cookie>

Request:
{
  "session_id": string,
  "message": string,
  "profile": "wright"
}

Response: { "stream_id": string, "session_id": string, ... }
```

### 2.3 Chat Stream

```
GET http://127.0.0.1:8788/api/chat/stream?stream_id=<id>
Accept: text/event-stream
Cookie: hermes_session=<auth_cookie>

SSE Events: token, tool_use, tool_result, stream_end, error, cancel
Heartbeat: ": heartbeat\n\n" every 5s
```

### 2.4 Sessions List

```
GET http://127.0.0.1:8788/api/sessions
Cookie: hermes_session=<auth_cookie>

Response: [ { session_id, title, updated_at, ... }, ... ]
```

### 2.5 Health

```
GET http://127.0.0.1:8788/api/health
Response: { "ok": true, "version": "...", ... }
```

## 3. Agent Adapter Interface (Python)

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass

@dataclass
class AgentStreamEvent:
    """A single event from an agent response stream."""
    type: str          # "token" | "tool" | "stream_end" | "error"
    data: dict         # Event-specific payload

@dataclass
class AgentChatRequest:
    """Request to send a message to an agent."""
    session_id: str
    message: str
    trace_id: str | None = None

@dataclass
class AgentChatStartResponse:
    """Response from starting a chat turn."""
    stream_id: str
    session_id: str

@dataclass
class AgentSessionInfo:
    """Summary of an agent session."""
    session_id: str
    title: str
    created_at: int
    updated_at: int
    message_count: int

class BaseAgentEngine(ABC):
    """Abstract base for all agent adapters (Constitution §2)."""

    @abstractmethod
    async def check_health(self) -> dict:
        """Return {"state": "connected"|"disconnected", "latencyMs": float}"""
        ...

    @abstractmethod
    async def create_session(self, workspace: str | None = None) -> AgentSessionInfo:
        """Create a new agent session."""
        ...

    @abstractmethod
    async def list_sessions(self) -> list[AgentSessionInfo]:
        """List all sessions for this adapter's profile."""
        ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if deleted."""
        ...

    @abstractmethod
    async def start_chat(self, request: AgentChatRequest) -> AgentChatStartResponse:
        """Initiate a chat turn. Returns stream_id for SSE consumption."""
        ...

    @abstractmethod
    async def stream_response(self, stream_id: str) -> AsyncIterator[AgentStreamEvent]:
        """Yield SSE events from the agent's response stream."""
        ...
```

## 4. Frontend Service Interface (TypeScript)

```typescript
// Unchanged from feature 001 — same AgentEvent type union
export type AgentEvent =
  | { type: 'token'; text: string }
  | { type: 'tool'; name: string; preview: string }
  | { type: 'done'; session: ChatSession }
  | { type: 'error'; message: string };

export interface AgentService {
  checkHealth(): Promise<ServiceHealthResult>;
  createSession(workspace?: string): Promise<ChatSession>;
  listSessions(): Promise<ChatSessionCompact[]>;
  loadSession(sessionId: string): Promise<ChatSession>;
  deleteSession(sessionId: string): Promise<void>;
  sendMessage(sessionId: string, message: string): AsyncIterable<AgentEvent>;
}
```

## 5. Design Tokens (Unchanged)

All existing Hermes calm-console design tokens from feature 001 remain unchanged. No new tokens are required for this feature.
