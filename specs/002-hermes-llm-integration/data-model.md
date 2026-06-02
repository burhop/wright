# Data Model: Hermes & LLM Integration

**Branch**: `002-hermes-llm-integration` | **Date**: 2026-06-02

## Entity Diagram

```mermaid
erDiagram
    HermesProfile ||--o{ AgentSession : "owns"
    AgentSession ||--o{ AgentMessage : "contains"
    AgentSession ||--o| StreamContext : "has active"
    ServiceHealth }o--|| HermesProfile : "monitors"

    HermesProfile {
        string name PK "e.g. 'wright'"
        string hermesHome "~/.hermes/profiles/wright/"
        string webuiBaseUrl "http://127.0.0.1:8788"
        int webuiPort "8788"
        string llmBaseUrl "inherited from default"
        string llmModel "inherited from default"
        boolean isActive
    }

    AgentSession {
        string sessionId PK "UUID from Hermes"
        string hermesSessionId "mapped to Hermes WebUI session"
        string title
        int createdAt "epoch ms"
        int updatedAt "epoch ms"
        boolean isActive
        string profileName FK "HermesProfile.name"
    }

    AgentMessage {
        string id PK "local UUID"
        string sessionId FK
        string role "user | assistant"
        string content
        int timestamp "epoch ms"
        string traceId "OpenTelemetry trace"
        int tokenCount "nullable, assistant only"
        float latencyMs "nullable, assistant only"
    }

    StreamContext {
        string streamId PK "from Hermes /api/chat/start"
        string sessionId FK
        string status "streaming | done | error | cancelled"
        int startedAt "epoch ms"
        int endedAt "nullable, epoch ms"
    }

    ServiceHealth {
        string serviceId PK "wright-api | hermes-agent | inference"
        string name "display name"
        string endpoint "health check URL"
        string state "connected | disconnected | unknown"
        int lastChecked "epoch ms"
        float latencyMs "last check latency"
    }
```

## Entity Details

### HermesProfile

Represents a dedicated Hermes agent profile for the Wright application. Created once during setup. Configuration is cloned from the default profile.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| name | string | setup script | Always "wright" for this feature |
| hermesHome | string | `hermes profile show wright` | Full path to profile HERMES_HOME |
| webuiBaseUrl | string | Wright API config | URL of the dedicated WebUI instance |
| webuiPort | int | Wright API config | Dedicated port (8788) |
| llmBaseUrl | string | cloned config.yaml | Inherited from default profile |
| llmModel | string | cloned config.yaml | Inherited from default profile |
| isActive | boolean | runtime check | Whether WebUI process is running |

### AgentSession

A conversation thread. Maps 1:1 to a Hermes WebUI session. Created via `POST /api/session/new` on the Hermes WebUI.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| sessionId | string | Wright internal ID | Used by frontend store |
| hermesSessionId | string | Hermes WebUI API | Used for backend proxy calls |
| title | string | Auto-generated or user-set | Updated on first message |
| createdAt | int | epoch ms | Set at creation |
| updatedAt | int | epoch ms | Updated on each message |
| isActive | boolean | runtime state | Whether session is currently streaming |
| profileName | string | FK → HermesProfile | Always "wright" |

### AgentMessage

A single message in a session. User messages are local; assistant messages are populated from SSE stream events.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| id | string | local UUID | Generated client-side |
| sessionId | string | FK → AgentSession | Parent session |
| role | string | "user" or "assistant" | Determines rendering |
| content | string | user input or SSE tokens | Streamed for assistant |
| timestamp | int | epoch ms | When message was created/completed |
| traceId | string | OpenTelemetry | Nullable, set by Wright API |
| tokenCount | int | SSE metadata | Nullable, assistant messages only |
| latencyMs | float | measured | Nullable, time to first token |

### StreamContext

Tracks an active SSE stream between the Wright API and Hermes WebUI. Transient — exists only during an active chat turn.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| streamId | string | Hermes `/api/chat/start` response | Used to connect to SSE |
| sessionId | string | FK → AgentSession | Owning session |
| status | string | runtime state | streaming → done/error/cancelled |
| startedAt | int | epoch ms | When stream was initiated |
| endedAt | int | epoch ms | Nullable, when stream completed |

### ServiceHealth

Real-time connectivity status for monitored backend services. Already exists in the frontend store from feature 001.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| serviceId | string | hardcoded | wright-api, hermes-agent, inference |
| name | string | display label | Human-readable |
| endpoint | string | Wright API health route | Backend proxy endpoint |
| state | string | health check result | connected/disconnected/unknown |
| lastChecked | int | epoch ms | Timestamp of last poll |
| latencyMs | float | measured | Round-trip time of health check |

## State Transitions

### StreamContext Lifecycle

```mermaid
stateDiagram-v2
    [*] --> streaming: POST /api/chat/start returns stream_id
    streaming --> done: SSE stream_end event
    streaming --> error: SSE error event or connection failure
    streaming --> cancelled: User cancels or POST /api/chat/cancel
    done --> [*]
    error --> [*]
    cancelled --> [*]
```

### ServiceHealth States

```mermaid
stateDiagram-v2
    [*] --> unknown: App starts
    unknown --> connected: Health check succeeds
    unknown --> disconnected: Health check fails or times out
    connected --> disconnected: Health check fails
    disconnected --> connected: Health check succeeds
```
