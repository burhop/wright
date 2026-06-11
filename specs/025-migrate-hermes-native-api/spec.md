# Feature Specification: Migrate to Hermes Native API

**Feature Branch**: `025-migrate-hermes-native-api`

**Created**: 2026-06-11

**Status**: Draft

**Input**: User description: "Migrate from the third-party hermes-webui community server to the official Hermes native API for all agent communication and MCP tool management. Today, our architecture has three layers of proxying: the React UI talks to our FastAPI backend, which proxies to a separate hermes-webui Python server process (cloned from github.com/nesquena/hermes-webui, running on port 8788), which then finally calls the hermes-agent core. This migration replaces that middle layer with the official Hermes API gateway (the `hermes gateway` command with API_SERVER_ENABLED=true, binding to port 8642 by default) which implements the OpenAI-compatible /v1 chat completions spec."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seamless Agent Chat After Migration (Priority: P1)

An engineer opens the Wright application, navigates to Agent Chat within a workspace, types a message in the composer, and receives a streamed response from the Hermes agent — exactly as they do today. The migration from the community backend to the official API is invisible to the end user: the same three-panel layout (sessions sidebar, chat transcript, workspace browser) works identically. Responses stream token-by-token, tool usage is surfaced in the transcript, and the agent operates within the correct workspace context.

**Why this priority**: The core user experience must be preserved. If live chat breaks, the entire application is non-functional. This is the "zero regression" gate that validates the migration end-to-end.

**Independent Test**: Can be fully tested by starting the Wright application with the new backend configuration, opening a workspace, sending a message in the chat composer, and verifying a meaningful streamed response appears in the transcript with tool call indicators when applicable.

**Acceptance Scenarios**:

1. **Given** the Wright app is running with the new native API backend, **When** the user types "Hello, what can you do?" and presses Send, **Then** a streamed response from the Hermes agent appears in the chat transcript within 30 seconds.
2. **Given** the agent uses a tool during a response (e.g., file read, CAD generation), **When** the tool is invoked, **Then** the UI displays a tool call indicator with the tool name and a progress bar, matching current behavior.
3. **Given** a workspace with enabled MCP tools (e.g., OpenSCAD), **When** the user asks the agent to perform a CAD task, **Then** the agent successfully invokes the workspace-scoped tools and produces the expected output.
4. **Given** the native API backend is not reachable, **When** the user sends a message, **Then** the system displays a clear error message indicating the agent is unavailable and does not crash.

---

### User Story 2 - Dynamic MCP Tool Management Without Service Interruption (Priority: P1)

An engineer is in an active workspace chat session and navigates to the workspace tool settings. They enable a new MCP server (e.g., FreeCAD Core) for their workspace. The tool becomes available to the agent within seconds — without the chat session being interrupted, without the agent backend restarting, and without any visible downtime. Similarly, disabling a tool immediately removes it from the agent's available capabilities.

**Why this priority**: Eliminating the disruptive process-restart cycle is the single largest architectural improvement in this migration. Today, toggling a tool kills the agent backend and requires a full restart, leaving the user unable to chat for several seconds. This must become a seamless, live operation.

**Independent Test**: Can be tested by opening a workspace, starting a chat session, enabling an MCP tool in the workspace settings, and immediately sending a message that uses that tool — all without observing any agent downtime or session interruption.

**Acceptance Scenarios**:

1. **Given** a user is in an active workspace chat session, **When** they enable an MCP tool in workspace settings, **Then** the tool becomes available to the agent within 5 seconds without disrupting the active session.
2. **Given** a user disables an MCP tool in workspace settings, **When** they send a subsequent message, **Then** the agent no longer has access to the disabled tool's capabilities.
3. **Given** the user toggles multiple tools rapidly (enable, disable, enable), **When** the system stabilizes, **Then** only the final set of enabled tools is active for the agent.

---

### User Story 3 - Workspace Session Isolation and History (Priority: P2)

When an engineer creates a new workspace, a new session is automatically generated. When returning to an existing workspace, their last session is restored. All session isolation rules continue to apply: only sessions belonging to the current workspace are visible and selectable. Session history (past messages) is retrievable and displays correctly.

**Why this priority**: Session management is fundamental to workspace productivity. While the migration changes the underlying agent backend, the user-facing session behavior must remain identical.

**Independent Test**: Can be tested by creating a workspace, chatting, leaving, returning, and verifying the session is restored with full message history intact.

**Acceptance Scenarios**:

1. **Given** a user creates a new workspace named "turbine-design", **When** the workspace is created, **Then** a new agent session is automatically started and bound to that workspace.
2. **Given** a workspace has three past sessions, **When** the user opens that workspace, **Then** the most recently updated session is loaded with its full chat history.
3. **Given** the user is inside workspace A, **When** they view the session list, **Then** only sessions belonging to workspace A are shown — no sessions from workspace B appear.

---

### User Story 4 - System Health Visibility (Priority: P3)

The status bar at the bottom of the Wright UI accurately reflects the connectivity state of the Hermes agent running on the new native API. When the agent backend goes offline, the status indicator changes from connected to disconnected within one polling cycle. The health indicator label and behavior remain consistent with the current experience.

**Why this priority**: Operational awareness is important but secondary to core functionality. The existing health polling infrastructure simply needs to point at the new backend.

**Independent Test**: Can be tested by starting the app with the native API running (expect green connected indicator), then stopping the backend (expect red disconnected indicator within one polling cycle).

**Acceptance Scenarios**:

1. **Given** the native Hermes API is running and healthy, **When** the user views the status bar, **Then** the "Hermes Agent" indicator shows a connected state.
2. **Given** the native Hermes API goes offline, **When** the status polls for connectivity, **Then** the indicator updates to disconnected within 15 seconds.

---

### User Story 5 - Simplified Container Deployment (Priority: P3)

A DevOps engineer builds and deploys the Wright Docker container. The container no longer includes the hermes-webui community server. Instead, it runs the official Hermes gateway as a supervised process. The container image is smaller, has fewer dependencies, and starts up faster. The engineer can verify the deployment by checking that both the Wright API and the Hermes gateway are running and healthy.

**Why this priority**: Operational simplification reduces maintenance burden and eliminates a third-party dependency from the critical path, but it does not directly affect the end-user experience.

**Independent Test**: Can be tested by building the Docker image, running the container, and verifying via `supervisorctl status` that the Wright API and Hermes gateway processes are both running.

**Acceptance Scenarios**:

1. **Given** a fresh Docker build, **When** the container starts, **Then** both the Wright API and the Hermes gateway process are running and reporting healthy.
2. **Given** the new container image, **When** compared to the previous image, **Then** the hermes-webui dependency (git clone, separate venv, requirements.txt) is no longer present.
3. **Given** the container is running, **When** the Wright API proxies a chat request to the gateway, **Then** the request completes successfully using the native API protocol.

---

### Edge Cases

- What happens when the native Hermes API is running but the LLM inference server behind it is offline? The system should report agent as connected but surface LLM errors gracefully in the chat transcript.
- How does the system handle the transition period during deployment — can old sessions created under hermes-webui be loaded by the new backend? Session data stored in Wright's SQLite should be unaffected, but Hermes-side session state may need migration.
- What happens if the native API does not support a feature that hermes-webui provided (e.g., a specific slash command format)? The system should degrade gracefully and log the unsupported feature.
- How does the system behave when the user switches active agents (e.g., from Hermes to OpenClaw) mid-session? The adapter pattern must continue to support hot-swapping.
- What happens if multiple workspaces are open in different browser tabs? The MCP tool isolation per workspace must remain correct even under concurrent use.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the hermes-webui community server with the official Hermes native API as the sole agent communication backend while preserving all existing user-facing functionality.
- **FR-002**: System MUST continue to stream agent responses token-by-token to the frontend, including tool call indicators, progress updates, and completion events.
- **FR-003**: System MUST support dynamic loading and unloading of MCP tools per workspace without restarting the agent backend process.
- **FR-004**: System MUST preserve workspace-scoped MCP tool bindings — tools enabled in workspace A must not be available in workspace B's sessions.
- **FR-005**: System MUST maintain session isolation per workspace — sessions created in one workspace must not be visible or selectable from another workspace.
- **FR-006**: System MUST automatically create a new agent session when a workspace is created, bound to that workspace's directory path.
- **FR-007**: System MUST restore the most recently active session when a user returns to an existing workspace.
- **FR-008**: System MUST propagate the workspace directory path to the agent backend during session creation and chat turns, ensuring the agent operates within the correct filesystem context.
- **FR-009**: System MUST maintain the adapter pattern for agent backends, allowing the Hermes implementation to be swapped for other agent engines without changing the frontend or API router layer.
- **FR-010**: System MUST report accurate health status for the native API backend via the status bar health indicators.
- **FR-011**: System MUST eliminate all references to hermes-webui from the production container image, including the git clone, separate virtual environment, and process supervision entry.
- **FR-012**: System MUST preserve the wright profile isolation — all agent operations must be scoped to the dedicated "wright" profile, not the user's personal Hermes profile.
- **FR-013**: System MUST log all agent interactions using structured JSON logging with trace IDs, consistent with the project's observability mandate.
- **FR-014**: System MUST limit frontend changes to the agent-service transport layer (`agent-service.ts`) only — no UI component, layout, or design changes. The transport layer is updated to use a unified POST-based streaming endpoint aligned with the OpenAI-compatible API used by both Hermes and OpenClaw. The FastAPI router is also updated to merge the two-step chat/start + chat/stream flow into a single `POST /chat` streaming endpoint.

### Key Entities

- **AgentSession**: A conversation thread between the user and an agent, identified by session ID, associated with a workspace path. Contains ordered messages with roles, content, and timestamps.
- **EngineeringWorkspace**: A project workspace with a unique ID, display name, local filesystem path, and a list of enabled MCP tool identifiers. Sessions are scoped to workspaces.
- **McpServer**: A registered Model Context Protocol server with an identifier, display name, activation state, and command configuration. Workspaces bind to specific MCP servers.
- **ServiceHealth**: A real-time connectivity record for the agent backend, containing connection state (connected/disconnected) and latency measurement.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can send a message and receive a complete agent response in under 30 seconds, matching or improving upon the current response time.
- **SC-002**: Agent responses appear incrementally (token-by-token) — the first token is visible within 3 seconds of the agent beginning to generate.
- **SC-003**: Enabling or disabling an MCP tool in a workspace takes effect within 5 seconds, without any visible agent downtime or session interruption.
- **SC-004**: 100% of existing workspace functionality (create, toggle tools, session isolation, session restore, workspace context propagation) continues to work after migration.
- **SC-005**: The production container image no longer includes the hermes-webui dependency, reducing the number of supervised processes from 2 to 2 (Wright API + Hermes gateway replaces Wright API + hermes-webui).
- **SC-006**: All existing integration tests (Playwright) and unit tests (pytest, Vitest) continue to pass after migration.
- **SC-007**: Health status indicators accurately reflect native API connectivity within one polling cycle (≤15 seconds).
- **SC-008**: The system handles agent unavailability gracefully — displaying an error state within 5 seconds without blocking the UI.

## Assumptions

- The official Hermes native API (via `hermes gateway` command) is available in a recent release of the `hermes-agent` package and can be installed via `uv tool install`.
- The native API implements an OpenAI-compatible `/v1/chat/completions` endpoint with streaming support, making it compatible with standard client libraries.
- The native Hermes gateway supports dynamic MCP server registration and deregistration without requiring process restarts — this is a key architectural assumption that must be validated during the planning/research phase.
- The wright profile isolation mechanism (`HERMES_HOME=~/.hermes/profiles/wright`) is supported by the native gateway, providing equivalent isolation to the `hermes_profile` cookie used by hermes-webui.
- The native API provides session management capabilities (create, list, delete sessions with workspace context) equivalent to what hermes-webui exposed via its custom REST endpoints.
- The React frontend transport layer (`agent-service.ts`) and the FastAPI router (`agent.py`) require minimal, targeted changes to adopt the unified POST-based streaming endpoint. UI components, layouts, and event handling logic remain unchanged — only the HTTP transport mechanism is updated.
- The wright-gateway MCP stdio bridge (`tool_registry/gateway.py`) continues to function as the intermediary between the Hermes gateway and Wright's tool registry — only the process that spawns it changes.
- Existing session data stored in Wright's SQLite database is unaffected by this migration. Hermes-side session state (if any) may need a one-time migration or can be treated as a clean start.
- The `hermes-webui` community server and its `ctl.sh` lifecycle scripts are fully removed from both the local development workflow and the Docker container after migration.
