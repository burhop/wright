# Feature Specification: Wright Slash Commands

**Feature Branch**: `030-wright-slash-commands`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Create /wright launcher, catalog, status slash commands"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Server Lifecycle Management (Priority: P1)

Users want to start and stop the Wright application stack directly from their chat environment without having to manually run command-line scripts or build web assets in their terminal.

**Why this priority**: Starting the local API gateway and web UI is the core prerequisite for using the plugin. It represents the primary lifecycle MVP.

**Independent Test**:
- User types `/wright start` in a stopped state. The system builds the stale frontend assets, starts the backend service in the background, verifies connectivity, and opens the user's browser automatically.
- User types `/wright stop` in a running state. The background processes are terminated gracefully.

**Acceptance Scenarios**:

1. **Given** the Wright stack is not running, **When** the user runs `/wright start`, **Then** the application performs asset verification, builds if necessary, starts the background services, opens the browser, and prints a success notification.
2. **Given** the Wright stack is already running, **When** the user runs `/wright start`, **Then** the system detects it is already healthy and opens the browser without starting a new server session.
3. **Given** the Wright stack is running, **When** the user runs `/wright stop`, **Then** the system terminates the processes gracefully and cleans up the active process trackers.

---

### User Story 2 - Navigation & Diagnostics (Priority: P1)

Users need to quickly access the web application interface and inspect the setup to troubleshoot directory permissions, missing configuration profiles, or unavailable dependencies.

**Why this priority**: Speeds up diagnostics and troubleshooting when local files or credentials are misconfigured.

**Independent Test**:
- User runs `/wright open` to immediately navigate to the web UI.
- User runs `/wright doctor` to see a checklist of environment health items.

**Acceptance Scenarios**:

1. **Given** the Wright stack is not running, **When** the user runs `/wright open`, **Then** they receive a warning message pointing them to use `/wright start`.
2. **Given** the user is unsure about their setup, **When** they run `/wright doctor`, **Then** they see a detailed checklist report showing repository detection, API health, build status, SQLite DB presence, credential keys state, and active MCP servers.

---

### User Story 3 - Catalog Exploration & Search (Priority: P2)

Users want to browse, search, and inspect the registry of engineering tools from within the Hermes interface before installing them.

**Why this priority**: Helps users discover tools matching their engineering disciplines (CAD, FEA, CFD, etc.) directly in the conversation flow.

**Independent Test**:
- User runs `/wright catalog` to view the list of available tools.
- User runs `/wright catalog search openfoam` to filter the catalog.
- User runs `/wright info prusaslicer` to inspect structural attributes and dependencies.

**Acceptance Scenarios**:

1. **Given** a user wants to view CAD tools, **When** they run `/wright catalog cad`, **Then** they see a structured table displaying ID, Name, Locality, and Weight for tools matching that domain.
2. **Given** a user searches for tools, **When** they run `/wright catalog search <query>`, **Then** they receive a list of matches based on name, description, or tags.
3. **Given** a user wants tool details, **When** they run `/wright info <id>`, **Then** they see descriptions, commands, transport methods, required credentials, and system dependencies.

---

### User Story 4 - Tool Installation (Priority: P2)

Users need to install cataloged engineering MCP servers into the Wright gateway from the chat session.

**Why this priority**: Enables rapid workspace configuration by deploying tools into the active server registry.

**Independent Test**:
- User runs `/wright install calculix` to register the CalculiX MCP server and receives success confirmation.

**Acceptance Scenarios**:

1. **Given** a valid catalog tool ID, **When** the user runs `/wright install <id>`, **Then** the client registers the server with the Wright gateway and displays a success confirmation.
2. **Given** an invalid tool ID, **When** the user runs `/wright install <id>`, **Then** they receive a descriptive error message.

---

### User Story 5 - Connection & Integration Status (Priority: P2)

Users want to check the status of the current workspace, active tools, and missing credentials from the chat interface.

**Why this priority**: Provides a quick dashboard view of active tools and pending actions.

**Independent Test**:
- User runs `/wright status` and receives a dashboard status overview.

**Acceptance Scenarios**:

1. **Given** the Wright server is running, **When** the user runs `/wright status`, **Then** they see the active workspace name/path and a list of enabled tools with active/inactive/needs credentials status indicators.

---

### Edge Cases

- **Build Failure**: If asset compilation (`npm run build`) fails, the launcher must abort startup and print the build output log to help the user resolve the issue.
- **Port Conflict**: If port 8000 is already in use by a non-Wright process, `/wright start` must fail gracefully instead of hangs or background crashes.
- **Missing or Locked PID**: If a stale PID file exists but the process is dead, `/wright stop` must clean up the stale PID file and report that the process was not active.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a command launcher router namespace `/wright`.
- **FR-002**: System MUST support launching the application stack (`/wright start`) by compiling missing or stale frontend assets and starting background processes.
- **FR-003**: System MUST support stopping background processes (`/wright stop`) via signal propagation and process ID tracking.
- **FR-004**: System MUST check backend connection health before launching the user interface (`/wright open`).
- **FR-005**: System MUST provide diagnostics (`/wright doctor`) validating repository existence, database state, permissions of secrets files, and configured credentials.
- **FR-006**: System MUST query active workspace path, API connectivity, and tool statuses via the `/wright status` command.
- **FR-007**: System MUST list catalog items (`/wright catalog [domain]`), filterable by taxonomy, in a clean visual layout.
- **FR-008**: System MUST perform keyword searches (`/wright catalog search <query>`) across catalog attributes.
- **FR-009**: System MUST display detail pages (`/wright info <id>`) exposing requirements, command lines, and dependencies of a catalog item.
- **FR-010**: System MUST trigger tool registrations (`/wright install <id>`) targeting the backend gateway endpoints.
- **FR-011**: System MUST display a categorized list of help subcommands when no arguments or unknown commands are supplied.

### Key Entities

- **Process Tracker (PID)**: Represents the running state identifier of the background service. It maps to the target system process.
- **Diagnostics Check**: Represents a set of system validation checks (permissions, paths, db status).
- **Subcommand Context**: Holds active arguments and dispatches command requests to the client bridge.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can start the entire stack via `/wright start` in under 15 seconds if frontend assets are already built.
- **SC-002**: All diagnostics checks run and render within 2 seconds.
- **SC-003**: Users can search and filter 30+ catalog entries with instant responses (latency under 100ms).
- **SC-004**: System successfully isolates credential values during the doctor/status commands (0 instances of raw secrets leaked in logs or text outputs).

## Assumptions

- **A-001**: The system has standard unix shell capabilities (e.g. `npm`, `python`/`uvicorn`, and `kill` signals).
- **A-002**: Local environment has Node.js and npm installed for frontend asset compilation.
- **A-003**: The user's operating system has a configured default web browser accessible via Python's standard `webbrowser` library.
- **A-004**: All processes run with permissions appropriate to modify files under the target repository path and read the configuration directories.
