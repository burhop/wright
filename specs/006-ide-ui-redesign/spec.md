# Feature Specification: IDE UI Redesign

**Feature Branch**: `006-ide-ui-redesign`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "We need to redesign the UI to be more like VS CODE (see image). On the far left should be a set of icons that up the left side panel. The default should be the workspace panel. A second pane should be "Tools" but is basically like the Extensions: Market place (second picture) . The middle should be any file that we have opened from the workspace. If it is STL, it should be 3D graphics. For images, it should show the image, for python, it should show the python file colored as in visual studio. We will add viewers for other file types. The right should be our agent (hermes, OpenClaw, or Pi). Only Hermes is implemented now. Each workspace will have a set of tools that go with it (this is different that VS CODE as extensions work across workspaces."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Panel Activity Bar Layout (Priority: P1)

The user wants a layout styled like Visual Studio Code that maximizes screen space and makes navigation intuitive:
- A vertical **Activity Bar** on the far-left showing icons for "Workspace" and "Tools".
- A collapsible/resizable **Sidebar** representing the active view (Workspace File Tree by default).
- A central **Tabbed Editor View** where files from the explorer are loaded.
- A collapsible **Agent Drawer** on the right side housing the Hermes console.

**Why this priority**: Highly critical layout prerequisite. All subsequent file views and tools panes anchor onto this tripartite layout.

**Independent Test**: Click Activity Bar icons to toggle panels; drag sidebar borders to resize; collapse the Agent panel on the right.

**Acceptance Scenarios**:
1. **Given** the application has loaded, **When** the user clicks the "Tools" icon in the far-left Activity Bar, **Then** the sidebar changes from the Workspace Explorer to the Tools Marketplace view.
2. **Given** the sidebar is open, **When** the user clicks the active Activity Bar icon again, **Then** the sidebar collapses to maximize the central editor view.

---

### User Story 2 - Extensible File Tab Viewers (Priority: P1)

The user wants to open workspace files inside a central tabbed editor area rather than viewing them in restricted side overlays. The viewer must identify file types and load:
- STL files in an interactive 3D graphics viewer.
- Image files (PNG, JPG, SVG) in a native visual previewer.
- Code files (Python `.py`, OpenSCAD `.scad`, JSON, Markdown `.md`) in a syntax-highlighted editor with code-coloring and editing support.
- Unsupported file types in a plain text editor or binary file info panel.

**Why this priority**: Essential to verify physical STL output files and code side-by-side with the agent, facilitating quick iteration.

**Independent Test**: Double-click `/designs/bracket.stl` and `model.scad` in the Workspace Explorer; verify they open in separate side-by-side editor tabs.

**Acceptance Scenarios**:
1. **Given** the user is viewing the Workspace Explorer, **When** the user double-clicks an STL file, **Then** a new tab opens in the central editor showing the 3D orbit controls and model.
2. **Given** multiple tabs are open, **When** the user edits a Python file tab, **Then** the code changes are auto-saved to the local workspace on disk.

---

### User Story 3 - Workspace-Specific Tools Marketplace (Priority: P2)

The user wants to configure which MCP tools and servers are active *specifically for the current session/workspace*, rather than applying tools globally. The "Tools" panel inside the sidebar acts as a marketplace:
- Lists all registered MCP servers and their current status (Active/Inactive) in this workspace.
- Allows enabling/disabling tools for the active workspace.
- Allows editing connection configurations and settings per tool for this session.

**Why this priority**: Empowers users to limit agent context and control costs by enabling only relevant tools per engineering session.

**Independent Test**: Open the Tools marketplace sidebar, toggle off "CalculiX Simulation", verify that Hermes no longer has access to CalculiX tools for that session.

**Acceptance Scenarios**:
1. **Given** the user is on the Tools Marketplace sidebar, **When** the user clicks "Disable" on a tool card, **Then** the tool's access is restricted specifically for this workspace, and database mappings update.

---

### Edge Cases

- **Large Files**: If a file larger than 10MB (e.g. dense STL model or raw simulation output log) is opened, show a size warning and ask for confirmation before loading the tab to prevent browser freeze.
- **External Modifications**: If the active agent or external processes modify a file currently open in a tab, reload the buffer dynamically or prompt the user with a "File modified on disk" reload banner.
- **Agent Drawer Collapse**: Ensure that when the Agent drawer is collapsed, Hermes continues running background tasks and alerts the user of completion via badges on the Activity Bar/Agent tab.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render a vertical Activity Bar on the far-left of the main layout containing Workspace and Tools navigation primitives.
- **FR-002**: System MUST render a collapsible Sidebar panel displaying either the Workspace File Browser or the Tools Marketplace based on the Activity Bar selection.
- **FR-003**: System MUST render a tabbed central Editor Panel displaying multiple opened files simultaneously.
- **FR-004**: System MUST support file type dispatching in the Editor Panel:
  - STL files MUST open in an interactive 3D graphics viewport.
  - Standard images MUST open in a native image preview tab.
  - Python (`.py`), OpenSCAD (`.scad`), JSON, and Markdown (`.md`) MUST open in a syntax-highlighted code editor.
- **FR-005**: System MUST associate MCP tools/servers with workspaces, persisting activation status in the local database storage per `session_id`.
- **FR-006**: System MUST automatically prompt users to reload or hot-reload file contents when modified on disk by the agent runner.
- **FR-007**: System MUST render a collapsible right-hand drawer containing the active agent console (Hermes).

### Key Entities *(include if feature involves data)*

- **EditorTab**: Represents an open file tab in the central area. Attributes: `path` (workspace relative), `name`, `type` (file extension), `is_dirty` (has unsaved edits), `last_modified` (timestamp).
- **WorkspaceToolMapping**: Represents session-specific tool configs. Attributes: `session_id`, `server_id`, `is_enabled` (boolean override), `custom_config` (JSON string).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clicking Activity Bar icons toggles or switches Sidebar panes in under 50ms.
- **SC-002**: Switching between opened editor tabs completes in under 100ms.
- **SC-003**: The 3D graphics viewer loads and renders STL files up to 5MB in under 200ms.
- **SC-004**: Disabling or enabling a tool in the Tools marketplace updates session configurations in the local database in under 100ms.

## Assumptions

- **Single Active Workspace**: The UI assumes one active workspace is visible at a time (locked to the current chat session).
- **Syntax Highlighting**: A lightweight in-browser code formatter/syntax highlighter (such as Prism or Monaco) will be used to render file tabs.
- **Agent Extensibility**: While Hermes is the only active agent implemented, the UI layout leaves placeholding tabs/settings for future adapters (OpenClaw, Pi).
