# Feature Specification: Workspace MCP & Session Isolation

**Feature Branch**: `021-workspace-mcp-sessions`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "We need to improve and update the workspace functionality.  A user creates a workspace with a name.  A new workspace folder with that name should be created under the application's workspace directory.  A new session should be created at that time so the user can start chatting. Once in the workspace, the user can select one or more installed MCP servers to be used as tools for sessions started in the workspace.  Once the MCPs are added, the current session is updated so the MCP servers can now be called (the LLM is aware of the tools). Likewise, the user can remove MCP Servers from the workspace. IF a workspace already exists, the last session should be activiated when the uses opens that workspace.  All previous sessions should be stored in the workspace and the user should be able to double click on them to start them up in the workspace. WHen is a workspace, only the sessions that go with that workspace should be selectable.  THe user should not be able to be in one workspace but have a session from another workspace. When in a workspace, this context should be known to the agent system (Hermes, OpenClaw, Pi) so that it is able to work with the files there. We also need to clean out the old workspaces that were created as part of testing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Named Workspace & Auto-Start Chatting (Priority: P1)

When a user creates an engineering workspace, they want it organized under a clean, recognizable folder name rather than an auto-generated UUID. They also want a session automatically started so they can begin collaborating with their engineering agent immediately.

**Why this priority**: Core user onboarding flow. Without this, users cannot create project workspaces with human-readable directories or start chat sessions.

**Independent Test**: Can be tested by filling out the workspace creation modal on the dashboard, confirming that the directory was created under the application's workspace path, and validating that the user is immediately redirected to a fresh chat screen.

**Acceptance Scenarios**:

1. **Given** the user is on the Dashboard Page, **When** they click "Create Workspace", type a name "gearbox-design", and click "Submit", **Then** a directory `~/workspace/gearbox-design` is created, a new session is generated, and the user is redirected to the workspace page.
2. **Given** a user input name with special characters (e.g. "Turbine V2: High Speed"), **When** the workspace is created, **Then** the folder name is safely sanitized (e.g. `turbine-v2-high-speed`), while the display name remains as typed.

---

### User Story 2 - Toggle MCP Tools Inside Active Workspace Session (Priority: P1)

Once inside a workspace, the user wants to enable or disable specific installed MCP servers (such as OpenSCAD Geometry, FreeCAD Core, or CalculiX Simulation). The LLM agent should immediately gain or lose access to these tools during the active session.

**Why this priority**: Crucial for agent execution. The agent needs appropriate tools to perform CAD and FEA tasks within the workspace.

**Independent Test**: Can be tested by opening the Tools Marketplace tab in the workspace sidebar, checking the box to enable an installed MCP server, and verifying that the agent is immediately aware of and utilizes that MCP server's tools in subsequent prompts.

**Acceptance Scenarios**:

1. **Given** the user is in a workspace with the "OpenSCAD Geometry" server disabled, **When** they toggle it "Enabled" in the UI, **Then** the active agent engine is reconfigured to bind the OpenSCAD tools, and subsequent messages can call those tools.
2. **Given** an MCP server is enabled in the workspace, **When** the user toggles it "Disabled" in the UI, **Then** the active agent engine immediately unbinds the tools.

---

### User Story 3 - Existing Workspace Last-Session Restore & Session List (Priority: P2)

When returning to an existing workspace, the user wants to pick up right where they left off by restoring the last active session. They also want a clear list of all other sessions that belong to this workspace so they can double-click and switch to them.

**Why this priority**: Essential for productivity and history management.

**Independent Test**: Can be tested by opening a workspace, chatting, returning to the dashboard, and then re-opening that workspace to confirm the last session is restored.

**Acceptance Scenarios**:

1. **Given** a workspace has three past sessions, **When** the user clicks on the workspace card from the dashboard, **Then** the last active session is loaded and displayed.
2. **Given** the user is inside a workspace, **When** they look at the session selector, **Then** only the sessions belonging to this workspace are listed.
3. **Given** the user double-clicks on a past session in the workspace sidebar list, **When** it loads, **Then** that session's chat history is restored.

---

### User Story 4 - Workspace Context Propagation to LLM Agents (Priority: P1)

When a user interacts with the agent, the agent must be fully aware of the workspace directory path so it can read files (such as `.scad` or `.step` models) and write generated files directly to that workspace.

**Why this priority**: Core architectural constraint. Without workspace path context, the agent will write/read from incorrect directories.

**Independent Test**: Prompting the agent to "List the files in the workspace" or "Save this CAD design" and verifying that it inspects or writes to the correct physical workspace directory path on the container's disk.

**Acceptance Scenarios**:

1. **Given** the active agent is Hermes, **When** a chat session is started, **Then** the workspace path is sent as part of the session initialization or chat payload so the agent uses it as its root path for all filesystem tools.

---

### User Story 5 - Automated Clean Up of Test Workspaces (Priority: P2)

To keep the application's workspace directory clean, the system should identify and purge old, orphan workspaces created during testing or those containing UUIDs with no user activity.

**Why this priority**: Prevents disk clutter and system decay in development and test environments.

**Independent Test**: Running the cleanup command/logic and confirming that empty/uuid-named test workspaces are deleted from the disk and the database.

**Acceptance Scenarios**:

1. **Given** several UUID-named folders from old test runs exist in `~/workspace`, **When** the cleanup routine is executed, **Then** these folders are deleted and their records are removed from SQLite.

### Edge Cases

- **Workspace Folder Collisions**: The system MUST block creation and request a unique name if a workspace folder or database record with that name already exists.
- **Empty Workspaces/Sessions**: Handling cases where the user creates a workspace but never sends a message, leaving an empty session.
- **Missing Disk Folder**: If the workspace record exists in SQLite but the folder was deleted from disk, the system must recreate the folder and initialize a Git repository instead of crashing.
- **Agent Switch During Session**: When the user switches the active agent (e.g. from Hermes to Qwen) in the middle of a workspace session, the workspace path context and enabled MCP tools must be correctly sync'd to the new agent.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST sanitize the user-provided workspace name to construct a safe directory name (lowercase, alphanumeric, and hyphens only) under the parent workspace directory.
- **FR-002**: When creating a workspace, the system MUST automatically create a new agent session associated with that workspace's path.
- **FR-003**: The system MUST store session-workspace associations in the local SQLite database.
- **FR-004**: When retrieving sessions, the system MUST filter and return only those sessions associated with the active workspace.
- **FR-005**: The system MUST prevent a user from selecting or accessing a session belonging to workspace A while they are viewing workspace B.
- **FR-006**: Opening a workspace MUST automatically load the session that was last active (most recently updated) in that workspace.
- **FR-007**: The system MUST expose a list of all sessions associated with the current workspace in the UI, enabling the user to switch between them.
- **FR-008**: Toggling MCP servers in the workspace UI MUST update the workspace's enabled tools list in SQLite and immediately reload the active agent's tool definitions for that session.
- **FR-009**: The system MUST propagate the workspace directory path to the active agent adapter (Hermes, OpenClaw, PI) during session initialization and chat turns.
- **FR-010**: The system MUST provide a cleanup utility to delete all existing workspaces and their database records to clean the system state.

### Key Entities

- **EngineeringWorkspace**:
  - `workspace_id` (UUID)
  - `workspace_name` (display name, e.g., "Turbine V2")
  - `local_path` (absolute disk path, e.g., `/home/agent/workspace/turbine-v2`)
  - `enabled_tools` (JSON list of enabled MCP server IDs)
  - `git_remote_url` (optional remote)
  - `created_at` (epoch timestamp)
  - `updated_at` (epoch timestamp)
- **AgentSession**:
  - `session_id` (agent-side UUID)
  - `workspace_id` (foreign key pointing to EngineeringWorkspace)
  - `title` (session title)
  - `created_at` (timestamp)
  - `updated_at` (timestamp)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of newly created workspaces have their folder named after the sanitized workspace name instead of a UUID.
- **SC-002**: When switching workspaces, the list of selectable sessions updates in under 200ms and excludes all sessions from other workspaces.
- **SC-003**: Enabling/disabling an MCP tool in the UI updates the agent's active tool schema within 1.5 seconds.
- **SC-004**: The workspace cleanup utility successfully reclaims disk space by purging 100% of untracked test directories.

## Assumptions

- Workspaces are stored under a configurable root directory (defaulting to `/home/agent/workspace` or `~/workspace`).
- Hermes and other agent adapters expose APIs that accept a workspace directory path to set context.
- Sessions are registered with both the local SQLite database and the agent's internal backend (e.g. Hermes WebUI).
- UI elements (session selector, list) use Playwright tests for integration testing.
