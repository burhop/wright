# Feature Specification: Hermes & LLM Integration

**Feature Branch**: `002-hermes-llm-integration`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "Connect to Hermes and our LLM. Create a new Hermes profile specific to this application. Enable live chat via the existing Agent Chat session UI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Live Agent Chat via Wright UI (Priority: P1)

An engineer opens the Wright application, navigates to the Agent Chat page, types a message in the composer, and receives a streamed response from the Hermes agent running under the dedicated "wright" profile. The response appears incrementally in the chat transcript — the same way the Hermes WebUI displays responses.

**Why this priority**: This is the core deliverable. The user explicitly stated: "if we can run our app and talk to Hermes via the chat session, we are good." Without this, the feature has zero value.

**Independent Test**: Can be fully tested by starting both the Wright API and frontend, sending a message in the chat composer, and verifying a meaningful streamed response appears in the transcript within the configured timeout.

**Acceptance Scenarios**:

1. **Given** the Wright app is running and the "wright" Hermes profile is available, **When** the user types "Hello, what can you do?" and presses Send, **Then** a streamed response from the Hermes agent appears in the chat transcript within 30 seconds.
2. **Given** the Wright app is running and the Hermes gateway is not reachable, **When** the user sends a message, **Then** the system displays a clear error message indicating the agent is unavailable and does not crash.
3. **Given** an active chat session with prior messages, **When** the user sends a follow-up question, **Then** the agent receives conversation history and responds in context.

---

### User Story 2 - Dedicated Wright Hermes Profile (Priority: P2)

A developer runs a setup command that creates an isolated Hermes profile named "wright" on the local machine, sharing the existing Hermes installation and Python environment but with its own configuration, sessions, and skills directories. This prevents Wright agent sessions from interfering with the user's personal Hermes agent.

**Why this priority**: Profile isolation is essential for multi-agent coexistence, but it is a one-time setup step that unblocks Story 1. The agent chat itself is useless without it, but the profile creation is a prerequisite rather than the end-user experience.

**Independent Test**: Can be fully tested by running the profile creation script and verifying `hermes profile list` shows "wright" as a separate profile with its own HERMES_HOME directory.

**Acceptance Scenarios**:

1. **Given** Hermes is installed and the "default" profile is running, **When** the developer runs the Wright setup script, **Then** a "wright" profile is created with its own isolated HERMES_HOME directory under `~/.hermes/profiles/wright/`.
2. **Given** the "wright" profile already exists, **When** the developer runs setup again, **Then** the existing profile is preserved and setup succeeds without errors.
3. **Given** the "wright" profile is created, **When** the developer inspects it, **Then** it uses the same LLM provider and base URL as the default profile but has independent sessions and skills directories.

---

### User Story 3 - Backend Proxy to Hermes API (Priority: P2)

The Wright FastAPI backend exposes proxy endpoints that forward chat requests to the Hermes WebUI API running on the "wright" profile. The frontend never communicates directly with Hermes — all traffic routes through the Wright API, which handles profile selection, health checking, and error wrapping.

**Why this priority**: The proxy layer is an architectural requirement from the constitution (API routes route to isolated packages). It enables the frontend to remain Hermes-agnostic and supports future agent hot-swapping via the Adapter Pattern.

**Independent Test**: Can be fully tested by calling the Wright API chat endpoint with `curl` and verifying it returns a streamed response from the Hermes agent.

**Acceptance Scenarios**:

1. **Given** the Wright API is running and the Hermes "wright" profile WebUI is accessible, **When** a POST request is sent to the Wright chat endpoint with a user message, **Then** the API returns a streamed response from the Hermes agent.
2. **Given** the Hermes WebUI is not running, **When** the Wright API health endpoint is called, **Then** it reports the Hermes agent service as "disconnected."

---

### User Story 4 - Health Status Reflects Live Hermes Connectivity (Priority: P3)

The status bar at the bottom of the Wright UI reflects the real connectivity state of the Hermes agent and the LLM inference endpoint. When the Hermes gateway or LLM goes offline, the status dot changes from green to red, giving the engineer immediate visibility without attempting a chat message.

**Why this priority**: Useful for operational awareness but not blocking for the core chat functionality. The existing health polling infrastructure from the Initial UI Foundation already supports this — this story wires it to real endpoints instead of stubs.

**Independent Test**: Can be tested by starting the app with the Hermes gateway running (expect green dot), then stopping the gateway (expect red dot within one polling cycle).

**Acceptance Scenarios**:

1. **Given** the Wright app is running and Hermes is healthy, **When** the user looks at the status bar, **Then** the "Hermes Agent" indicator shows a green connected dot.
2. **Given** the Wright app is running and the LLM inference server is down, **When** the user looks at the status bar, **Then** the "LLM Inference" indicator shows a red disconnected dot.

---

### Edge Cases

- What happens when the Hermes profile exists but its gateway service is not running?
- How does the system handle extremely long agent responses (e.g., multi-page code generation)?
- What happens if the LLM inference server returns an error mid-stream?
- How does the system behave when the user sends a new message while a previous response is still streaming?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create and manage a dedicated Hermes profile named "wright" that is isolated from the user's default Hermes profile.
- **FR-002**: System MUST provide a setup command or script that idempotently creates the "wright" profile, cloning LLM configuration from the default profile.
- **FR-003**: System MUST expose a backend chat proxy endpoint that accepts a user message and session identifier, forwards the request to the Hermes WebUI API under the "wright" profile, and streams the response back.
- **FR-004**: System MUST stream agent responses token-by-token to the frontend using Server-Sent Events (SSE) so users see incremental output.
- **FR-005**: System MUST maintain conversation context across messages within a session by forwarding session identifiers to the Hermes API.
- **FR-006**: System MUST report the real-time health status of the Hermes agent and LLM inference endpoint to the frontend status bar.
- **FR-007**: System MUST gracefully handle Hermes unavailability by displaying a user-friendly error message without crashing or hanging.
- **FR-008**: System MUST follow the constitution's Agent Abstraction rule: Hermes integration MUST be implemented via an adapter pattern so the agent backend can be swapped without changing frontend code.
- **FR-009**: System MUST log all chat interactions using structured JSON logging with trace IDs as required by the constitution's observability mandate.
- **FR-010**: System MUST support the offline-first mandate: when the agent is unavailable, previously loaded sessions and the UI remain functional.

### Key Entities

- **HermesProfile**: An isolated Hermes configuration containing its own HERMES_HOME, config.yaml, sessions, skills, and gateway state. Identified by profile name.
- **AgentSession**: A conversation thread between the user and the Hermes agent. Contains an ordered list of messages. Identified by session ID. Mapped to a Hermes WebUI session.
- **AgentMessage**: A single user or assistant message within a session. Contains role, content, timestamp, and optional metadata (token count, latency).
- **ServiceHealth**: A real-time connectivity record for a backend service (Hermes gateway, LLM inference). Contains service ID, state (connected/disconnected/degraded), and last-checked timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can send a message and receive a complete agent response in under 30 seconds from message submission (excluding LLM inference time beyond application control).
- **SC-002**: Agent responses appear incrementally (token-by-token streaming) — the first token is visible within 3 seconds of the agent beginning to generate.
- **SC-003**: The "wright" Hermes profile runs independently from the default profile — creating, using, or deleting it does not affect the user's existing Hermes sessions or configuration.
- **SC-004**: When the agent backend is unavailable, the system displays an error state within 5 seconds and does not block the UI.
- **SC-005**: Health status indicators accurately reflect real connectivity within one polling cycle (≤15 seconds).
- **SC-006**: All existing unit tests (6 Vitest) and integration tests (3 Playwright) continue to pass after integration.
- **SC-007**: The live chat interaction (send message → receive response) can be demonstrated end-to-end in a running Wright instance.

## Assumptions

- Hermes v0.15+ is installed on the local machine with a running gateway service and a working LLM inference endpoint.
- The existing Hermes WebUI API (hermes-webui) provides the `/api/chat/start`, `/api/chat/stream`, and `/api/sessions` endpoints needed for integration.
- The LLM inference server (vLLM) is accessible at the URL configured in the default Hermes profile's `config.yaml`.
- The "wright" profile can share the same Python virtual environment and Hermes agent installation as the default profile — only the data directory (HERMES_HOME) needs to be isolated.
- WebSocket or SSE streaming is supported by the deployment environment (no intermediate proxies that buffer streams).
- The Wright WebUI frontend (port 5173) and Wright API (port 8000) run on the same machine as the Hermes installation.
