# Data Model: IDE UI Redesign

This document details the data structures and schemas required for the IDE UI redesign and workspace-specific tool mappings.

---

## 1. Database Schema

### Table: `engineering_workspaces` (Modified)
Add a column `enabled_tools` to persist which MCP servers/tools are enabled specifically for a workspace:
- **`enabled_tools`**: `TEXT` (nullable). Stores a JSON array of server names/IDs, e.g. `["CalculiX Simulation", "OpenSCAD Geometry"]`. If NULL, defaults to enabling all registered servers.

```sql
ALTER TABLE engineering_workspaces ADD COLUMN enabled_tools TEXT;
```

---

## 2. React UI State Models

### Entity: `EditorTab`
Represents a file tab opened in the central panel.
```typescript
export interface EditorTab {
  path: string;           // Workspace-relative path to the file (e.g. "/designs/gearbox.stl")
  name: string;           // Filename (e.g. "gearbox.stl")
  type: 'stl' | 'image' | 'code' | 'text'; // File categorization type
  isDirty: boolean;       // True if there are unsaved text edits
  last_modified: number;  // Epoch timestamp when file was opened/last modified
}
```

### Entity: `WorkspaceLayoutState`
Represents the structural visibility states of panels in the tripartite IDE.
```typescript
export interface WorkspaceLayoutState {
  activeSidebarTab: 'explorer' | 'tools'; // Active pane inside Left Sidebar
  isSidebarCollapsed: boolean;            // True if Left Sidebar is collapsed
  isAgentCollapsed: boolean;              // True if Right Agent Sidebar is collapsed
  openTabs: EditorTab[];                  // List of open file tabs
  activeTabPath: string | null;           // Path of the currently focused file tab
}
```
