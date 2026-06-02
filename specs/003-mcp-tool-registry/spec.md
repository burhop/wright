# Feature Specification: MCP & Tool Registry

**Feature Branch**: `003-mcp-tool-registry`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "We want to be set up to use MCP, webMCP, MCP-UI, run CLIs, and eventually start A2A. We can then either use existing MCPs or create our own for specialized applications. We can also develop python applications that call the MCP APIs directly. We need a list with different MCPs for engineering and design applications."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Tool Registry Directory (Priority: P1)

The user browses, searches, and filters a list of engineering and design tools (MCP servers) available in the Wright application, similar to a plugin store. They can view tool cards containing names, descriptions, categories (e.g. CAD, Simulation, Standards, Productivity), capabilities, and install/enable them.

**Why this priority**: Core MVP requirement. Allows users to discover and activate the specific engineering capabilities (like CAD exporters or CalculiX runners) they need for their workflows.

**Independent Test**: Can be fully tested by navigating to the "Tool Registry" tab, typing a query in the search bar, clicking "Install" on a mock CAD exporter tool, and verifying the tool status changes to active.

**Acceptance Scenarios**:
1. **Given** the user is on the Tool Registry page, **When** they type "CAD" in the search box, **Then** only tools tagged with "CAD" are displayed.
2. **Given** a tool is marked as inactive, **When** the user clicks "Install", **Then** the button updates to "Active" and the tool becomes available to the LLM agent.

---

### User Story 2 - Register Custom MCP Servers & CLIs (Priority: P2)

An engineer wants to expose a proprietary CLI tool (e.g. a topology optimization script) or a local web-based server to the agent. They use the UI to configure and register a new local CLI wrapper or SSE (Server-Sent Events) endpoint.

**Why this priority**: Crucial for developers and advanced users to extend Wright's capabilities without modifying the core monorepo code.

**Independent Test**: Can be tested by filling out the "Add Custom Tool" form with a mock bash command (e.g. `echo '{"success": true}'`), verifying it successfully registers, and inspecting the tool's schemas in the database.

**Acceptance Scenarios**:
1. **Given** the "Add Custom Tool" form, **When** the user provides a command string and save it, **Then** the backend parses the command, executes its JSON schema discovery, and lists it under custom tools.
2. **Given** an invalid command or inaccessible SSE URL, **When** the user tries to save it, **Then** the system displays a connection validation error and refuses to save.

---

### User Story 3 - Rich UI Renderers for Tool Progress (MCP-UI) (Priority: P2)

When an agent invokes a complex or long-running engineering calculation (like a finite element mesh generator or standard checkers), the UI renders an interactive visual component (such as a progress bar, step logs, or chart) inside the Chat Transcript instead of raw text.

**Why this priority**: Bridges conversational interfaces with rich engineering readouts. Provides high-transparency diagnostics in line with the project constitution.

**Independent Test**: Initiate a chat session, type a command that triggers a progress-yielding tool, and assert that the transcript renders a visual card with live progress state changes.

**Acceptance Scenarios**:
1. **Given** a running simulation tool, **When** the tool updates its step percentage, **Then** the chat transcript displays a live, animating progress bar.
2. **Given** a completed tool execution, **When** the tool outputs visual metadata (like bounding box vectors), **Then** the chat displays an interactive results card.

---

### User Story 4 - WebMCP Browser Context Sharing (Priority: P3)

The agent needs to understand the active state of the client-side CAD Viewer or workspace window. The client browser uses WebMCP to register active viewport metrics (e.g., camera zoom level, selected component IDs) as tools callable by the LLM agent.

**Why this priority**: Enables close human-agent collaboration on 3D mechanical designs without screen-scraping.

**Independent Test**: Run a local task where the agent asks "What is currently selected?", and verify that the agent issues a call to `get_selected_part()` which returns the exact client-state ID.

**Acceptance Scenarios**:
1. **Given** a part is selected in the workspace panel, **When** the agent queries selection context, **Then** the client-side WebMCP hook intercepts the call and returns the part UUID from browser state.

---

### Edge Cases

- **Execution Timeout**: If a registered CLI wrapper hangs during execution, the system must terminate the process after a configured timeout (e.g., 60 seconds) and return a clean execution error trace to the LLM agent.
- **Port Conflict**: When starting multiple local standard MCP servers, the system must assign dynamic non-conflicting local ports or run via stdio streams to isolate execution.
- **Offline SSE Endpoints**: If a registered remote HTTP SSE endpoint becomes unreachable, the status bar and tool details must instantly display a disconnected state and route to local cached mocks if available.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The frontend MUST implement an interactive Tool Registry dashboard showing categorizable cards for standard and custom MCP servers.
- **FR-002**: The frontend MUST support rendering custom interactive visual components (MCP-UI blocks) inside message bubbles based on tool execution event payloads.
- **FR-003**: The backend API MUST manage MCP server registrations and tool state in the local SQLite WAL database.
- **FR-004**: The system MUST support executing stdio-based MCP servers using local CLI subprocess spawning.
- **FR-005**: The system MUST support connecting to HTTP SSE-based remote MCP endpoints.
- **FR-006**: The system MUST support WebMCP hooks executing client-side functions in the browser window context.
- **FR-007**: Every tool execution request MUST propagate the active `trace_id` and create OpenTelemetry spans for process runtime tracing.

### Key Entities

- **McpServer**: Represents a registered tool provider.
  - `serverId` (UUID): Primary key.
  - `name` (String): Display name.
  - `type` (Enum): `stdio` | `sse` | `webmcp`.
  - `source` (String): Command string for `stdio` or HTTP URL for `sse`.
  - `status` (Enum): `active` | `inactive` | `error`.
  - `category` (String): Grouping tag.
- **McpTool**: Represents individual functions exposed by an MCP Server.
  - `toolId` (String): Unique identifier.
  - `serverId` (UUID): Foreign key to McpServer.
  - `name` (String): Function call name.
  - `description` (Text): Parameter explanations.
  - `inputSchema` (JSON): Argument validation schema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can load and search the Tool Registry directory page in under 150ms.
- **SC-002**: The backend validates and mounts a newly registered stdio CLI MCP server configuration within 2 seconds of registration.
- **SC-003**: Dynamic progress updates (MCP-UI events) are rendered in the transcript within 100ms of arrival at the SSE client endpoint.
- **SC-004**: System recovers from a crashed stdio subprocess, terminating parent hooks and reporting failure cleanly, in under 1 second.

## Assumptions

- Stdio CLI binaries run under the host system user permissions.
- Complex visual panels rendered inside the chat are packaged as reusable client components.
- The default set of featured engineering MCP servers (e.g. CAD, FEA checkers) are loaded via seed scripts during setup.
