# Feature Specification: Workspace Dashboard UX

**Feature Branch**: `007-workspace-dashboard-ux`

**Created**: 2026-06-03

**Status**: Draft

**Input**: User description: "On the main page, existing workspaces are not being displayed. The list is empty. There should be a 'Create Workspace' button, not a dropdown at the top. At the bottom under the last workspace, there should be a button to 'View all workspaces'. For the tool registry, we need to keep track of what is installed and what is not. For example, OpenSCAD is already installed and it should show up like that. For the 'Agent Chat', we need to get rid of that concept and move more toward 'Workspaces'. We only want one workspace per web page. However, the user should be able to open multiple pages (maybe with a workspace ID?). We need to manage context with our agents. Hermes, I think, already does this so we need to map generic api (save/load context) to specific functionality for doing this in the agent frameworks."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Recent Workspaces on Dashboard (Priority: P1)

A user opens the Wright console and immediately sees their most recent workspaces listed on the main dashboard. The list shows the last 5 workspaces they opened, each with a recognizable name, path, and last-opened timestamp. If no workspaces exist yet, the user sees a clear empty state message encouraging them to create their first workspace.

**Why this priority**: The empty workspace list is the most visible bug reported — users land on the dashboard and see nothing, making the application appear broken. Fixing this restores the core first-impression experience.

**Independent Test**: Can be fully tested by opening the dashboard after creating at least one workspace. The workspace list should populate with accurate names and timestamps, delivering immediate orientation value.

**Acceptance Scenarios**:

1. **Given** the user has previously opened 3 workspaces, **When** they navigate to the dashboard, **Then** all 3 workspaces appear in the "Recent Workspaces" section ordered by most-recently-opened first.
2. **Given** the user has opened 8 workspaces, **When** they navigate to the dashboard, **Then** only the 5 most recent appear in the list, with a "View all workspaces" button visible below.
3. **Given** the user has never created a workspace, **When** they navigate to the dashboard, **Then** they see an empty state with a prompt to create their first workspace and a prominent "Create Workspace" button.

---

### User Story 2 - Create a New Workspace (Priority: P1)

A user wants to start a new engineering project. They click the "Create Workspace" button on the dashboard, provide a name and a project directory path, and a new workspace is initialized. After creation, the user is taken directly into that workspace.

**Why this priority**: Without the ability to create workspaces, no other feature is usable. This is the entry point for all user workflows.

**Independent Test**: Can be tested by clicking "Create Workspace", filling out the form, and verifying the workspace appears in the recent list and is ready for use.

**Acceptance Scenarios**:

1. **Given** the user is on the dashboard, **When** they click "Create Workspace", **Then** a creation form or dialog appears asking for workspace name and project directory.
2. **Given** the user has filled out the workspace creation form with valid details, **When** they submit, **Then** the workspace is created, stored in the local database, and the user is navigated into the new workspace view.
3. **Given** the user provides a duplicate workspace name, **When** they submit, **Then** the system shows a clear validation error without creating the workspace.

---

### User Story 3 - Tool Installation State Tracking (Priority: P2)

A user opens the Tool Registry and sees an accurate reflection of which tools are currently installed on their system and which are not. Tools that are already installed (e.g., OpenSCAD) display an "Installed" badge. Tools that are not installed show an "Install" button. Once installed, a tool can be enabled or disabled per workspace.

**Why this priority**: Tool state accuracy is essential for trust — if a tool is installed but shows as "not installed", users lose confidence in the system and may attempt redundant installations.

**Independent Test**: Can be tested by navigating to Tool Registry, verifying OpenSCAD shows as "Installed", and verifying an uninstalled tool shows an "Install" button.

**Acceptance Scenarios**:

1. **Given** OpenSCAD is installed on the system, **When** the user opens the Tool Registry, **Then** OpenSCAD shows an "Installed" badge and offers workspace-level enable/disable toggles.
2. **Given** a tool is not installed on the system, **When** the user views it in the Tool Registry, **Then** it shows an "Install" button instead of enable/disable controls.
3. **Given** a tool is installed and enabled for workspace A, **When** the user switches to workspace B, **Then** that tool's enabled state reflects workspace B's configuration (it may be disabled there).

---

### User Story 4 - One Workspace Per Page with Multi-Page Support (Priority: P2)

A user navigates to a workspace and the entire page is dedicated to that single workspace context. If they want to work on two projects simultaneously, they open a second browser tab/window with a different workspace URL (containing the workspace ID). Each tab operates independently with its own workspace context.

**Why this priority**: Removing the "Agent Chat" abstraction and moving to workspace-centric pages simplifies the mental model and allows parallel work across projects.

**Independent Test**: Can be tested by opening two browser tabs with different workspace IDs and verifying each loads its own workspace context independently.

**Acceptance Scenarios**:

1. **Given** the user clicks on a workspace from the dashboard, **When** the workspace loads, **Then** the URL contains the workspace ID and the page is fully dedicated to that workspace's context.
2. **Given** the user opens two browser tabs with different workspace IDs, **When** they interact with each tab, **Then** actions in one tab do not affect the other.
3. **Given** the user bookmarks a workspace URL, **When** they return to it later, **Then** the same workspace loads with its persisted state.

---

### User Story 5 - Agent Context Save/Load per Workspace (Priority: P3)

When a user switches away from a workspace or closes the page, the agent's conversation context is automatically saved. When they return to that workspace, the agent context is restored so they can continue where they left off. This behavior works generically across different agent frameworks (Hermes, OpenClaw, PI).

**Why this priority**: Context persistence turns workspaces from stateless sessions into meaningful ongoing projects, but it depends on the workspace and agent infrastructure being in place first.

**Independent Test**: Can be tested by having a conversation in a workspace, navigating away, returning, and verifying the conversation history is intact.

**Acceptance Scenarios**:

1. **Given** the user has an active conversation in workspace A, **When** they navigate away and then return to workspace A, **Then** the conversation history is fully restored.
2. **Given** the user switches from workspace A to workspace B, **When** the switch occurs, **Then** workspace A's context is saved and workspace B's context is loaded.
3. **Given** the system is using the Hermes agent framework, **When** context save/load is triggered, **Then** the generic API delegates to Hermes-specific context persistence methods.

---

### Edge Cases

- What happens when the user's workspace directory no longer exists on disk (e.g., it was deleted externally)?
  - The workspace should appear in the list with a warning indicator and an option to remove it.
- What happens when the user tries to open a workspace URL with an invalid workspace ID?
  - The system should redirect to the dashboard with a "Workspace not found" notification.
- What happens when agent context save fails (e.g., disk full)?
  - The system should warn the user that context may not be fully recoverable, and log the error for diagnostics.
- What happens when multiple browser tabs have the same workspace open?
  - The most recent tab's actions take precedence; a warning may be shown about concurrent editing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display the 5 most recently opened workspaces on the dashboard, ordered by last-opened timestamp.
- **FR-002**: System MUST provide a "Create Workspace" button on the dashboard that initiates workspace creation with name and directory inputs.
- **FR-003**: System MUST provide a "View all workspaces" button below the recent workspaces list that navigates to a full workspace listing.
- **FR-004**: System MUST track tool installation state independently from tool enablement state — a tool can be installed but not enabled in a given workspace.
- **FR-005**: System MUST accurately detect and display whether each tool is currently installed on the host system (e.g., checking if the binary exists or the MCP server is available).
- **FR-006**: System MUST allow enabling/disabling installed tools on a per-workspace basis, and the active tool set MUST change when the user switches workspaces.
- **FR-007**: System MUST route workspace pages using a workspace identifier in the URL (e.g., `/workspace/:id`).
- **FR-008**: System MUST support multiple browser tabs each operating independently on different workspaces.
- **FR-009**: System MUST save agent conversation context when the user leaves a workspace and restore it when they return.
- **FR-010**: System MUST provide a generic context save/load API that maps to agent-framework-specific implementations (Hermes, OpenClaw, PI).
- **FR-011**: System MUST remove the standalone "Agent Chat" page/concept and replace it with workspace-integrated agent interaction.

### Key Entities

- **Workspace**: A named engineering project context with a directory path, creation timestamp, last-opened timestamp, and associated tool configurations. Uniquely identified by an ID.
- **Tool**: An MCP-based server or external utility. Has an installation state (installed/not-installed) and per-workspace enablement state (enabled/disabled).
- **Agent Context**: The conversation history and state for an agent session within a workspace. Serializable for persistence and restorable across page loads.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users see their recent workspaces within 1 second of loading the dashboard — the list is never empty when workspaces exist.
- **SC-002**: Users can create a new workspace and begin working in it within 30 seconds of clicking "Create Workspace".
- **SC-003**: Tool installation status is accurately reflected for 100% of registered tools every time the Tool Registry is viewed.
- **SC-004**: Users can open the same workspace in a new browser tab via URL and have the correct context loaded 100% of the time.
- **SC-005**: Agent conversation context survives a full page reload or workspace switch with no data loss for conversations under 1000 messages.
- **SC-006**: Switching between workspaces updates the active tool set correctly within 2 seconds.

## Assumptions

- Users have stable local filesystem access for workspace directories.
- The existing SQLite database schema can be extended to support workspace-tool enablement mappings and agent context storage.
- Hermes agent framework already supports some form of session/context persistence that can be adapted to the generic save/load API.
- The "Agent Chat" removal does not delete existing chat history — it migrates or associates conversations with their respective workspaces.
- The application runs on a single machine; multi-user concurrent workspace access is out of scope for this feature.
- Mobile/tablet support is out of scope — the UI targets desktop browser viewports.
