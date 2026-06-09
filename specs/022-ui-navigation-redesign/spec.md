# Feature Specification: UI Navigation and Dashboard Redesign

**Feature Branch**: `022-ui-navigation-redesign`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "We need to make the UI more intuitive and easier to use. On the left hand panel, we should have the following items: Dashboard, Tool Registry, Settings, Logs, and Settings. We need both a new Settings page and a Logs page that lets us view the application logs. For the logs, we should provide additional UI for filtering, getting messages just for certain workspaces, and a right hand click that allows us to send the selection to the agent (hermes) for help with debugging. THe Dashboard itselve should be made more attractive and useful. THe engineering Workspaces Box should be 1/2 the width. We should have a new box with status information from the agent (hermes) on tasks that are running, connection status, any recent system errors. We do not need the Tool Registry box or File Vault boxes in the Dashboard. I think we need a new 'news' box. in the Dashboard talking about new versions, new MCP servers. IT shoudl give links that start a new browser page (E.g. burhop.substack.com, github.com/burhop/wright, INdustry blogs, etc.) THese boxes should be condensed with much less white space as compared to the current UI. At full size, we should easily see 4 panels (boxes) in the Dashboard. The workspace UI left row of buttons needs to change. At the top, add a 'Back' button to take us back the dashboard. NExt should be the folder button we have now. 3rd button is an MCP Tool selector. It should show a list of the installed MCP tools (right now that would just be the OpenSCAD but will be 5 to 20 MCPs later. The MCP display should be similar to the MCP Library display, but likely smaller to we can get at least 5 MCP tools there. 4th button should be an improved Git panel that allows greater functionality (new branches, merging, pull) For large files, we may need to indicate that theya re not being managed because they are too big. THis is likely to be common with engineering documentation. 5th button should be Workspace settings. We need something akin to a workspace prompt that any sessions inlcude in thier context. We also wnat to set any special setting unique to the workspace but not already addressed by the git and MCP. 6th button should be documentation and tutorials. All these buttons for the workspace only change the content of the left panel. Tooltips or other help should be given to help the user navigate the UI."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Modernized & Condensed Dashboard Layout (Priority: P1)

As an engineer, I want a high-density, informational dashboard at startup so that I can see my active workspaces, current agent task status, and system/industry updates at a glance.

**Why this priority**: Highly critical as the landing page of the application, replacing the current low-density, two-column layout with a four-panel control hub.

**Independent Test**: Can be verified by running the web application, confirming the new 4-box layout with condensed borders/padding and verifying that clicking links in the News box opens them in a separate browser tab.

**Acceptance Scenarios**:

1. **Given** the user navigates to the root URL `/`, **When** the page renders, **Then** they see a grid containing four distinct panels:
   - *Engineering Workspaces* (taking up 1/2 of the dashboard grid width).
   - *Agent Status* (displaying Hermes agent connection status, running task trees, and recent system errors).
   - *News & Resources* (displaying software updates, active MCP server releases, and external links).
   - *System Activity & Telemetry* (displaying database metrics, session history, and recent logs count).
2. **Given** the user views the dashboard on a standard full-size screen, **When** they look at the layout, **Then** all 4 panels are visible without scrolling, utilizing condensed padding and margins.
3. **Given** the News panel is rendered, **When** the user clicks on links like `burhop.substack.com` or `github.com/burhop/wright`, **Then** the link opens in a new browser tab/window without navigating away from the Wright dashboard.

---

### User Story 2 - Global Sidebar Re-organization & Application Logs (Priority: P1)

As an engineer, I want the main left-hand sidebar to direct me to the Dashboard, Tool Registry, Logs, and Global Settings, and I want to easily view backend and agent logs.

**Why this priority**: Essential navigation reform to support debugging and simplify path access.

**Independent Test**: Verify that the main left sidebar features the correct icons and routes, and that navigating to `/logs` displays active system logs.

**Acceptance Scenarios**:

1. **Given** the user is on the main application route, **When** they look at the left sidebar, **Then** they see exactly four navigation links: Dashboard, Tool Registry, Logs, and Settings.
2. **Given** the user clicks on "Logs", **When** the Logs page loads, **Then** they see a list of application logs with controls to:
   - Filter by log level (INFO, WARNING, ERROR).
   - Filter logs by specific workspace tags.
   - Search for keywords within the logs.

---

### User Story 3 - Debugging Logs with Hermes (Priority: P2)

As an engineer troubleshooting a failed tool run or model generation, I want to select relevant log entries and send them to the agent for debugging help.

**Why this priority**: Bridges the observability of the system with the autonomous capabilities of the agent.

**Independent Test**: Select a range of log lines on the Logs page, open the right-click menu, select "Send to Hermes for Debugging", and verify the agent receives the logs in its prompt context.

**Acceptance Scenarios**:

1. **Given** the user is on the Logs page, **When** they highlight a range of log lines and right-click, **Then** a context menu appears with the option "Send Selection to Hermes for Help".
2. **Given** the user selects the right-click action, **When** the action completes, **Then** the system contextually passes the log lines to the agent in a floating debugger drawer/panel that slides open on the right side of the Logs page, allowing the user to chat with Hermes without leaving the logs page.

---

### User Story 4 - Workspace Inner Activity Sidebar (Priority: P1)

As an engineer working inside a workspace, I want an activity row of buttons that changes only the left sidebar panel content, letting me switch between file trees, Git panels, workspace options, and tool documentation.

**Why this priority**: Critical user interface control for workspace-specific tasks without disrupting the main editor canvas or active 3D view.

**Independent Test**: Navigate to a workspace, click the sidebar activity buttons, and verify that only the sidebar changes and no full-page reloads occur.

**Acceptance Scenarios**:

1. **Given** the user is inside a workspace view, **When** they look at the activity bar row, **Then** they see six buttons in this order:
   - Button 1: **Back** (arrow/exit icon) which takes the user back to the Dashboard.
   - Button 2: **Explorer** (folder icon) showing the workspace file tree.
   - Button 3: **MCP Tool Selector** (compact grid/list icon) showing installed MCP tools.
   - Button 4: **Version Control** (git icon) showing an improved Git panel.
   - Button 5: **Workspace Settings** (sliders/gear icon) showing workspace settings.
   - Button 6: **Docs & Tutorials** (book/help icon) showing learning resources.
2. **Given** the user clicks any of the workspace buttons (2 through 6), **When** the panel changes, **Then** only the content of the left-hand panel transitions, and the editor tab area and 3D viewer remain unchanged.
3. **Given** the user hovers over any of the activity row buttons, **When** the cursor rests on the button, **Then** a helpful tooltip appears describing its destination.

---

### User Story 5 - Workspace settings & Prompt Context (Priority: P2)

As an engineer, I want to define a workspace-specific prompt that is injected into all agent sessions within that workspace, and configure other settings.

**Why this priority**: Allows domain-specific tuning of Hermes agents per workspace.

**Independent Test**: Edit the workspace prompt in Workspace Settings, save it, and verify that subsequent agent sessions have the prompt included in their context.

**Acceptance Scenarios**:

1. **Given** the user is on the Workspace Settings panel, **When** they edit the "Workspace Prompt Context" text area and save, **Then** the settings are saved.
2. **Given** a saved Workspace Prompt, **When** the user starts a session or interacts with Hermes, **Then** the prompt is injected into the agent's active system prompt.

---

### User Story 6 - Compact MCP Tool Selector (Priority: P2)

As an engineer, I want to see a compact display of installed MCP tools in my workspace so I can review what tools are currently enabled for the agent.

**Why this priority**: Keeps the user informed of active tool availability.

**Independent Test**: Click the MCP Tool selector button, confirm that a list/grid of installed MCP tools appears and displays at least 5 tools compactly.

**Acceptance Scenarios**:

1. **Given** the user clicks the MCP Tool Selector button in the workspace sidebar, **When** the panel renders, **Then** it shows a compact list of installed MCP tools (such as OpenSCAD).
2. **Given** the workspace contains multiple installed MCP tools, **When** the panel displays, **Then** at least 5 tools are visible without needing to scroll the sidebar.

---

### User Story 7 - Advanced Git Panel with Large File Detection (Priority: P2)

As an engineer handling large 3D models and engineering documentation, I want a Git panel that supports branch creation, merging, pulling, and warns me if files exceed size limits.

**Why this priority**: Essential to prevent git repository bloat from large binary CAD/STL files.

**Independent Test**: View the Git panel in a workspace with a file larger than the configured limit, and verify it displays a size warning indicator.

**Acceptance Scenarios**:

1. **Given** the user is on the Git panel, **When** they view changed files, **Then** any file exceeding the size threshold displays a warning badge indicating that it is too large and is not being managed.
2. **Given** the user clicks on the Git panel controls, **When** they choose to create branches, merge, or pull, **Then** the system executes the corresponding operation and displays status logs.

---

## Edge Cases

- **Agent Disconnection**: If the backend is disconnected from Hermes, the *Agent Status* panel on the dashboard must display a clear "Disconnected" warning state with a reconnection helper link.
- **Large Log Volume**: If the backend has logged 100,000+ entries, the Logs page must virtualize the log list or paginate to prevent browser memory crashes, and apply client-side and server-side filtering limits.
- **Git Large File Threshold**: If a file is exactly at the boundary of the size threshold (which defaults to 10MB but can be customized in the Workspace Settings panel), the Git warning badge must trigger consistently.
- **No MCP Tools Configured**: If a workspace has 0 active MCP tools, the MCP Tool Selector panel must show a helpful empty-state message directing the user to the Tool Registry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: **Main Sidebar Layout**: The application's global navigation sidebar MUST be updated to contain four items: Dashboard, Tool Registry, Logs, and Settings.
- **FR-002**: **Logs Page**: A new Logs page (route `/logs`) MUST be created to display backend structured JSON application logs.
- **FR-003**: **Log Filtering**: The Logs page MUST provide controls to filter logs by Log Level (INFO, WARNING, ERROR), search query, and Workspace association.
- **FR-004**: **Logs Agent Debug Integration**: The Logs page MUST allow users to select text in the log list and right-click to trigger a "Send to Hermes" debug request, which opens a floating debugger drawer on the right side of the Logs page populated with the selected log context.
- **FR-005**: **Global Settings Page**: A new Global Settings page (route `/settings`) MUST be created to handle system-wide preferences (including LLM providers, themes, and API keys), separating these from workspace-specific options (such as workspace prompt context and Git credentials).
- **FR-006**: **Dashboard Grid**: The Dashboard page MUST be restructured into a high-density grid layout displaying at least 4 boxes (Engineering Workspaces, Agent Status, News, and System Activity) with condensed padding and margins.
- **FR-007**: **Dashboard - Workspaces Box**: The Engineering Workspaces box MUST occupy exactly half of the width of the dashboard grid.
- **FR-008**: **Dashboard - Agent Status Box**: A new Agent Status box MUST show the active LLM agent connection status, running task queues, and any recent system errors.
- **FR-009**: **Dashboard - News Box**: A new News box MUST be added containing wright updates and links to external resources (e.g. `burhop.substack.com`, `github.com/burhop/wright`), opening in new browser tabs.
- **FR-010**: **Workspace Activity Sidebar Buttons**: The workspace view activity bar MUST be updated to feature six vertical buttons: Back (Dashboard), Explorer, MCP Tool Selector, Version Control, Workspace Settings, and Docs/Tutorials.
- **FR-011**: **Workspace Sidebar Panels**: Clicking a workspace activity button MUST only toggle the contents of the left sidebar, preserving the editor and 3D preview canvases.
- **FR-012**: **Workspace Settings - Prompt Injection**: The Workspace Settings panel MUST provide a text field allowing users to define custom instructions/prompt that are automatically included in Hermes agent context.
- **FR-013**: **Workspace - MCP Tool Selector**: A compact selector list MUST show installed MCP tools in the sidebar, displaying at least 5 tools compactly.
- **FR-014**: **Workspace - Git Panel**: The workspace Git panel MUST support branch creation, merge, and pull operations.
- **FR-015**: **Workspace - Git Large File Detection**: The Git panel MUST identify files that exceed the git file size limit and display a warning indicating they are not managed.
- **FR-016**: **Test IDs**: All new interactive UI elements MUST include a `data-testid` attribute (e.g., `data-testid="nav-logs"`, `data-testid="dashboard-agent-status"`, etc.) in compliance with Constitution §6.

### Key Entities

- **LogEntry**: Represents a single structured log line from the backend, featuring attributes like timestamp, severity level, message, workspace_id, and trace_id.
- **AgentStatus**: Represents the current status of the agent adapter, including connection state, active tasks, and active task progress metrics.
- **WorkspaceSettings**: Represents configuration parameters unique to the workspace, containing the workspace prompt text, custom settings override dictionary, and Git exclusions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: **UI Density**: The spacing on the dashboard is reduced such that all four core boxes are fully visible on a standard 1080p viewport without vertical scrolling.
- **SC-002**: **Logs Responsiveness**: The Logs page load time is under 1.5 seconds for repositories containing up to 10,000 log entries.
- **SC-003**: **Workspace Activity Transition**: Switching between workspace sidebar tabs (Explorer, Git, Settings, etc.) is instantaneous (less than 50ms) and has zero impact on the state of open editor tabs or the 3D model viewer.
- **SC-004**: **Task Completion Rate**: 100% of user clicks on news links successfully launch external pages in separate tabs, keeping the primary Wright tab open.

## Assumptions

- The backend system logs are exposed via a queryable service or SQLite database table that the frontend can fetch.
- Global Settings are stored locally in the server configuration database (`state.db`) rather than in individual workspaces.
- Git tools (Git executable) are available in the running environment to execute pull, merge, and branch operations.
- Large file threshold defaults to 10MB unless overridden in Workspace Settings.
