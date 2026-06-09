# Feature Specification: Pluggable Viewer Panel API

**Feature Branch**: `023-viewer-panel-api`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "Implement the viewer spec found in docs/viewer-spec.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Custom Viewer Registration & Discovery (Priority: P1)

Developers can register custom viewer providers mapped to specific file extensions, MIME types, glob patterns, or custom predicates. The registry resolves the best available provider or defaults to plain text/iframe fallbacks.

**Why this priority**: Core foundation of the pluggable architecture; necessary for any file rendering or editing.

**Independent Test**: Register a mock viewer provider for `.step` files and verify the system resolves it.

**Acceptance Scenarios**:
1. **Given** a registered custom viewer for `.step` files, **When** the registry is queried for a file with extension `.step`, **Then** the custom viewer provider is returned as the default choice.
2. **Given** no custom viewer is registered for a specific extension, **When** matching a text file, **Then** the registry falls back to the generic Plain Text viewer.

---

### User Story 2 - Viewer Tab Opening & Lifecycle Management (Priority: P1)

Users open a workspace file, which resolves and mounts its specialized UI (e.g. 3D WebGL canvas, code editor) into a unified center panel tab. The tab's lifecycle (creation, visibility updates, and disposal) is managed by the system, ensuring resource cleanup and support for reference-counted sharing across multiple views of the same document.

**Why this priority**: Main workflow for viewing and editing workspace assets.

**Independent Test**: Open a text document and verify that the tab mounts, updates visible states on switch, and disposes document resources upon closure.

**Acceptance Scenarios**:
1. **Given** a selected file, **When** opened, **Then** a PanelHost container is created and the viewer mounts its UI into the panel's DOM container.
2. **Given** a document opened in multiple tabs, **When** one tab is closed, **Then** the panel is disposed but the document is preserved until the last remaining tab is closed.

---

### User Story 3 - Persistence & Transaction History (Dirty Tracking / Undo-Redo) (Priority: P2)

Users edit files, see a dirty indicator, save changes, and perform undo/redo operations in custom viewers, with changes pushed to a document-level transaction history.

**Why this priority**: Critical for editing and modifying workspace designs and code safely.

**Independent Test**: Edit a file in a custom code editor, verify the dirty indicator is shown, trigger undo to revert, and save the document.

**Acceptance Scenarios**:
1. **Given** an unsaved edit in a viewer, **When** applied, **Then** the document and its tab show a dirty indicator.
2. **Given** a modified document with an undo history, **When** triggering a global undo command, **Then** the editor reverts the change and clears the dirty state if all edits are undone.

---

### User Story 4 - Unresponsive Panel Watchdog & Resource Isolation (Priority: P2)

Administrators and users can monitor panel heartbeats, isolate heavy computations to prevent browser freezes, and reload or kill unresponsive viewer panels.

**Why this priority**: Required for system stability and robustness against buggy third-party viewer scripts.

**Independent Test**: Simulate a hung panel and verify the reload/close prompt appears.

**Acceptance Scenarios**:
1. **Given** an active viewer tab, **When** it ceases to reply to heartbeat pings within the timeout threshold, **Then** the host renders an warning overlay offering to reload or close the tab.
2. **Given** a disposed viewer panel, **When** closed, **Then** WebGL contexts, event listeners, and background web workers are terminated.

---

### User Story 5 - Developer Tools & Inspector Overlay (Priority: P3)

Developers can inspect a viewer panel's registration metadata, capabilities, last errors, and open browser DevTools focused on the sandboxed iframe/container.

**Why this priority**: Simplifies development and diagnostics of custom viewer plugins.

**Independent Test**: Open the developer tools context menu on a panel and check the inspector overlay.

**Acceptance Scenarios**:
1. **Given** a viewer tab active, **When** selecting developer tools, **Then** the diagnostic overlay displays its URI, provider ID, capabilities, and last logs.

### Edge Cases

- **File size exceeds threshold**: When opening a massive file (e.g. >100MB STEP file), how does the system handle it? The viewer must load data progressively in web workers and show a loading percentage indicator without locking the UI.
- **Concurrent edits**: What happens if the file is updated on the filesystem by another process while the editor has unsaved changes? The system must prompt the user to compare, merge, or overwrite changes.
- **Renderer crash**: If the WebGL context is lost (GPU crash), the system must catch the event and offer a one-click reload button.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support registering custom viewer contributions with selector rules matching file extensions, MIME types, or glob patterns.
- **FR-002**: The system MUST resolve the default viewer for any selected file descriptor, falling back to a plain text viewer or sandboxed iframe viewer.
- **FR-003**: The PanelHost MUST provide an isolated DOM container and asynchronous messaging channel (postMessage / onDidReceiveMessage) for each opened tab.
- **FR-004**: The system MUST support dirty tracking per document, exposing change events and updating visual tab indicators.
- **FR-005**: Viewers MUST be able to push edit transactions onto a document-level undo/redo stack.
- **FR-006**: Viewers rendering untrusted HTML or third-party web content MUST prefersIsolation and run inside a sandboxed `<iframe>` with strict Content Security Policies (CSP).
- **FR-007**: The system MUST run heavy file parsing or WebGL geometry processing in background Web Workers.
- **FR-008**: The PanelHost MUST monitor viewer heartbeats and display a reloading/closing warning overlay if a panel becomes unresponsive.
- **FR-009**: The system MUST support a diagnostic overlay displaying viewer metadata, capabilities, and errors.

### Key Entities *(include if feature involves data)*

- **FileDescriptor**: Represents the resource metadata. Contains:
  - `id`: unique identifier
  - `uri`: file URI
  - `name`: display filename
  - `extension`: file extension
  - `mimeType`: MIME content type
  - `size`: optional byte size
  - `metadata`: optional key-value dictionary
- **ViewerDocument**: Represents the memory model for the content. Exposes:
  - `uri`: canonical URI
  - `type`: logical document type
  - `isDirty()`: boolean indicating unsaved changes
  - `markClean()`: resets dirty status
  - `dispose()`: clears memory
- **PanelHost**: Represents the active layout container (tab). Exposes:
  - `id`: unique tab identifier
  - `title`: display tab title
  - `container`: DOM mount point
  - `active`/`visible`: view state indicators
  - `postMessage(msg)`: post message to viewer
  - `onDidReceiveMessage`: event stream of messages from viewer
- **ViewerProvider**: Handles document loading, view rendering, and persistence. Defines:
  - `openDocument(file)`: returns `ViewerDocument`
  - `resolveViewer(doc, panel, mode)`: mounts and connects UI
  - `save(doc)` / `revert(doc)`: file persistence controls
  - `backup(doc)`: creates temporary auto-save backup
- **ViewerRegistry**: Catalog of all registered `ViewerContribution` entries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Custom viewer registration and resolution takes less than 5ms for any file descriptor.
- **SC-002**: Tab switching and rendering of static views (text, markdown preview) completes in under 50ms.
- **SC-003**: Heartbeat monitor detects an unresponsive or crashed main thread within 5 seconds and renders the reload overlay.
- **SC-004**: Closing a tab releases all associated GPU resources, event listeners, and web worker references within 100ms.

## Assumptions

- **Local Execution**: The application runs in a web environment with modern browser capabilities (WebGL, Web Workers, IndexedDB).
- **File System API**: The backend handles file read/write operations and updates the file system, exposing standardized REST/WebSocket APIs for save and backup commands.
- **Browser Sandbox**: Iframes are sufficient to isolate untrusted web pages when configured with appropriate `sandbox` attributes and CSP headers.
