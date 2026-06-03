# Research Notes: IDE UI Redesign

This document details the research findings, design decisions, and technology selections for implementing the VS Code-like IDE UI redesign.

---

## 1. UI Layout & Collapsible Panels

### Decision
Implement a three-column CSS Grid layout for the main layout:
- Column 1: Far-left Activity Bar (fixed width: `48px`).
- Column 2: Collapsible Sidebar (resizable width, default `260px`).
- Column 3: Central main area (flexible width `1fr`), which houses:
  - Central Tabbed Editor/Viewer Panel.
  - Collapsible bottom drawer for terminals/logs (optional placeholder).
- Column 4: Collapsible Agent Sidebar on the far right (fixed width `320px`).

Toggling panels is handled dynamically using React component states (`isSidebarCollapsed`, `isAgentCollapsed`) which add CSS classes or inline styles (e.g. toggling `display: none` or altering the grid template columns).

### Rationale
CSS Grid allows defining a responsive layout structure where columns can easily collapse to `0px` or expand, keeping boundaries clean. Toggling states in React avoids heavy DOM manipulation and allows smooth transition animations.

### Alternatives Considered
- **Nested Flexbox Panels**: Rejected because managing resizable vertical columns with nested flex containers requires complicated math and flex basis changes, which often result in rendering layout shifts on dynamic panel toggles.

---

## 2. Extensible File Viewer & Editor Tab Dispatcher

### Decision
Introduce a `FileTabDispatcher` component inside the central editor panel that resolves the active file extension to a specialized rendering component:
- **STL Viewer**: Rendered inside the existing `ThreeDViewer` component using Three.js and `STLLoader`.
- **Image Viewer**: Rendered natively via standard HTML `<img>` tag with support for zoom/pan.
- **Code Viewer/Editor**: Rendered in a text editor with syntax highlighting (using `Prism` or a lightweight `react-syntax-highlighter` wrapper). The editor will support direct modifications, committing edits via a debounced or auto-save on blur endpoint `PUT /api/workspace/files/content`.
- **Unsupported File Types**: Displayed in a read-only text viewer or a placeholder screen prompting file download.

### Rationale
This dispatcher provides a modular tab architecture. If we need to support new files (e.g. FreeCAD `.fcstd` or simulation result tables) in the future, we simply create a new tab renderer component and register it in the dispatcher's extension mapping registry.

### Alternatives Considered
- **Single Monolithic Viewport Component**: Rejected because coupling 3D rendering, native image buffers, and plain text code logic into one component creates a massive, unmaintainable file with excessive re-renders.

---

## 3. Session-Specific Tools Configuration (Workspace Tools)

### Decision
Associate MCP tools/servers with individual session workspaces by adding an `enabled_tools` column (type `TEXT`, storing a JSON list of enabled server names/IDs) directly to the SQLite `engineering_workspaces` table schema:
- When a workspace is initialized, `enabled_tools` defaults to all registered servers (e.g., `["CalculiX Simulation", "OpenSCAD Geometry"]`).
- In the "Tools Marketplace" sidebar tab, toggling a tool sends a POST request to update the JSON list in SQLite for the active `session_id`.
- The agent router and subprocess execution layers filter available servers based on this session list.

### Rationale
Storing the enabled tools as a JSON list in a text column inside `engineering_workspaces` is lightweight, does not require a new table join, and keeps SQLite schema migrations extremely simple. It provides the required session-specific tool containment.

### Alternatives Considered
- **Separate `workspace_tools` Junction Table**: Rejected as over-engineered for the current MVP. Toggling status is simple boolean mapping, so storing a stringified JSON array in a text field is highly performant and easy to query.
