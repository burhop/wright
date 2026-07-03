# Feature Specification: Workspace Session Model

**Feature Branch**: `040-workspace-session-model`

**Created**: 2026-07-02

**Status**: Draft

**Input**: User description: "Fix Wright workspace/session identity model so each workspace owns zero to many Hermes chat sessions, MCP enablement is workspace-scoped, switching sessions only changes chat, and workspace-required MCP servers are active when chatting."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Continue Sessions Within A Workspace (Priority: P1)

An engineer opens a Wright workspace and sees only the chat sessions that belong to that workspace. They can create a new session, return later, select any previous session for that same workspace, and continue the conversation without losing the workspace's files, tabs, viewer state, settings, or enabled tool configuration.

**Why this priority**: Session identity is core product state. If sessions are overwritten, lost, or mixed across workspaces, users cannot trust Wright for ongoing engineering work.

**Independent Test**: Create two sessions in one workspace, reload Wright, reopen the workspace, and verify both sessions are available while the workspace file/viewer state remains stable when switching between them.

**Acceptance Scenarios**:

1. **Given** a workspace with no chat sessions, **When** the user starts a new chat session, **Then** the workspace contains one selectable session and the workspace identity remains unchanged.
2. **Given** a workspace with two existing chat sessions, **When** the user switches between those sessions, **Then** only the chat transcript changes and the file tree, open viewer/editor tabs, workspace settings, and enabled tools do not reset.
3. **Given** two different workspaces each with their own sessions, **When** the user opens one workspace, **Then** the session selector lists only sessions for that workspace.

---

### User Story 2 - Keep MCP Tools Workspace-Scoped (Priority: P1)

An engineer enables MCP tools for a workspace and expects every chat session in that workspace to inherit those tools. The MCP status indicator reflects whether the workspace-required tools are available, not whether unrelated tools from another workspace or stale session are inactive.

**Why this priority**: MCP tools are part of the engineering workspace configuration. A wrong or stale MCP state can make the agent fail tool calls or mislead the user during testing.

**Independent Test**: Enable Onshape MCP for one workspace and different tools for another workspace, then verify each workspace reports only its own required MCP status across all sessions.

**Acceptance Scenarios**:

1. **Given** a workspace with Onshape MCP enabled, **When** any session in that workspace is selected, **Then** the MCP status checks the workspace's Onshape MCP requirement.
2. **Given** another workspace with different enabled tools, **When** the user opens the Onshape workspace, **Then** the MCP indicator does not report unrelated tools from the other workspace.
3. **Given** a workspace-required MCP cannot be started, **When** the user begins or resumes chat, **Then** Wright shows a clear user-facing error naming the affected MCP and does not label the issue as merely inactive without explanation.

---

### User Story 3 - Recover Existing Installations Safely (Priority: P2)

An existing Wright installation that previously stored one session directly on each workspace is upgraded without losing workspaces, saved chats, enabled tools, or active workspace behavior.

**Why this priority**: Users already have local state created by earlier Wright builds. The fix must migrate that state safely so testing can continue on the current machine and future installs.

**Independent Test**: Start from a database containing the previous one-session-per-workspace format, run the upgraded Wright application, and verify the existing workspace session appears as that workspace's first session with enabled tools preserved.

**Acceptance Scenarios**:

1. **Given** an existing workspace with a stored session and enabled tools, **When** Wright starts after upgrade, **Then** that session is associated with the workspace and the enabled tool list is preserved.
2. **Given** historical chat messages for a migrated session, **When** the user opens that session, **Then** the transcript is available in the same workspace.
3. **Given** a workspace whose last active session no longer exists in the agent backend, **When** the workspace is opened, **Then** Wright keeps the workspace available and guides the user to create or select a valid session without corrupting workspace state.

---

### User Story 4 - Preserve Workspace Context During Session Actions (Priority: P2)

An engineer can create, select, delete, and reload sessions without accidentally changing the active workspace, active MCP tool set, or visible workspace layout.

**Why this priority**: These are frequent testing actions. They must be predictable so user testing can isolate real agent/tool problems from UI state bugs.

**Independent Test**: In one workspace, open files and a viewer tab, create a new session, switch back to the old session, delete a session, and reload the page; verify the workspace layout remains tied to the workspace and only the chat list/transcript changes.

**Acceptance Scenarios**:

1. **Given** a workspace with an open file tab, **When** the user creates a new chat session, **Then** the open tab remains visible.
2. **Given** a workspace with a selected chat session, **When** the user deletes another session in the same workspace, **Then** the workspace remains open and only the session selector updates.
3. **Given** a workspace page is refreshed, **When** Wright restores state, **Then** it restores the same workspace and the most recent valid session for that workspace.

### Edge Cases

- A workspace may have zero sessions before the first chat.
- A workspace may have many sessions with duplicate or empty titles; Wright must still identify them clearly enough for selection.
- A session may be missing from the agent backend but still referenced by local state.
- Enabled MCP tools may include aliases or renamed tool entries; status must resolve them to the workspace requirement.
- A tool may be installed but intentionally disabled for the workspace; it must not appear as an error for that workspace.
- Multiple workspaces may be open or recently used during one Wright process; state must not bleed between them.
- The gateway may expose tools for only one active workspace at a time; switching the active workspace must update the gateway's workspace context.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST model a workspace as owning zero or more chat sessions.
- **FR-002**: Wright MUST preserve a stable workspace identity independent of the currently selected chat session.
- **FR-003**: Wright MUST list only the sessions associated with the currently opened workspace in that workspace's session selector.
- **FR-004**: Wright MUST create new chat sessions as additional sessions within the workspace rather than replacing the workspace's prior session.
- **FR-005**: Wright MUST allow the user to select any valid session associated with the workspace without changing workspace files, layout, settings, enabled tools, or workspace identity.
- **FR-006**: Wright MUST persist enough session metadata for sessions to remain discoverable after restart or reload.
- **FR-007**: Wright MUST migrate existing one-session workspace records into the new multi-session workspace model without losing the existing session association.
- **FR-008**: Wright MUST store MCP tool enablement as workspace configuration shared by all sessions in that workspace.
- **FR-009**: Wright MUST report MCP status using the workspace's enabled tool configuration, not a different workspace's session or unrelated installed tools.
- **FR-010**: Wright MUST attempt to make workspace-enabled MCP tools available when a workspace is opened or when chat begins in that workspace.
- **FR-011**: Wright MUST show a clear user-facing error when a workspace-required MCP cannot be made available, including the affected MCP name and actionable status.
- **FR-012**: Wright MUST avoid warning about tools that are installed globally but not enabled for the current workspace.
- **FR-013**: Wright MUST keep workspace layout persistence scoped to the workspace rather than the selected chat session.
- **FR-014**: Wright MUST keep chat transcript loading scoped to the selected session.
- **FR-015**: Wright MUST recover gracefully when a remembered session is missing, archived, or unavailable.
- **FR-016**: Wright MUST maintain compatibility with existing dashboard and workspace navigation flows.

### Key Entities

- **Workspace**: A named engineering project area with a stable identity, local file location, settings, enabled tool configuration, and zero or more chat sessions.
- **Chat Session**: A conversation context associated with exactly one workspace, with a title, timestamps, availability state, and message history.
- **Workspace Tool Configuration**: The set of MCP tools enabled for a workspace and inherited by all chat sessions in that workspace.
- **Workspace MCP Status**: The current availability and error state of the MCP tools required by a workspace.
- **Active Workspace Context**: The workspace currently exposed to the agent gateway for tool discovery and calls.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In manual testing, a workspace can create and retain at least three separate chat sessions across page reload and Wright restart.
- **SC-002**: Switching between sessions in the same workspace changes the chat transcript without changing the visible file tree, open tabs, viewer state, enabled tools, or workspace URL.
- **SC-003**: The session selector never displays sessions from another workspace during tests with at least two workspaces.
- **SC-004**: MCP status for a workspace with Onshape enabled reports only workspace-required MCPs and never reports unrelated tools from another workspace.
- **SC-005**: Existing local state with one stored session per workspace upgrades without losing the workspace, its stored session, or enabled tools.
- **SC-006**: When a workspace-required MCP cannot be made available, the user sees a named error within one chat attempt or workspace activation.
- **SC-007**: Automated backend and frontend regression tests cover multi-session workspace association, workspace-scoped MCP status, and session switching without workspace reset.

## Assumptions

- Hermes remains the active agent provider for this feature; other agent providers can reuse the same workspace/session association model later.
- Chat sessions belong to one workspace at a time and are not shared across workspaces.
- Workspace MCP enablement is a workspace setting, not a per-session setting.
- Existing databases may contain only the previous one-session workspace field and must be migrated in place.
- Global MCP installation state remains separate from per-workspace MCP enablement.
