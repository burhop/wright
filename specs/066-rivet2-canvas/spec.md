# Feature Specification: Modern Rivet Canvas Editor

**Feature Branch**: `066-rivet2-canvas`

**Created**: 2026-08-05

**Status**: Implemented

**Input**: User description: "Remove the old Rivet integration, replace it with valerypopoff/rivet2.0, and display only the modern graph editing area inside Wright."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Edit on a Focused Graph Canvas (Priority: P1)

An engineer opens a Rivet workflow in Wright and sees the modern graph canvas as part of the Wright workspace, without a second application's project bar, navigation sidebar, execution toolbar, status bar, settings, help, or auxiliary tools competing with Wright's controls.

**Why this priority**: The focused modern canvas is the requested user experience and the primary reason for replacing the legacy editor.

**Independent Test**: Open a workspace workflow and verify that graph nodes can be selected, moved, connected, added, edited, and removed while only graph-authoring surfaces are visible inside the editor region.

**Acceptance Scenarios**:

1. **Given** a workspace with an existing Rivet workflow, **When** the engineer opens it in Wright, **Then** the workflow graph appears in the retained workspace surface without Rivet-owned application chrome.
2. **Given** the graph canvas is open, **When** the engineer edits nodes and connections, **Then** the canvas responds with the modern interaction and visual design while preserving all controls required to author the graph.
3. **Given** the editor needs a contextual surface to edit a selected node, **When** the engineer invokes that surface, **Then** the relevant graph-authoring overlay is available without revealing unrelated application areas.

---

### User Story 2 - Keep Wright as the Workflow Authority (Priority: P2)

An engineer creates, opens, saves, lints, and runs Rivet workflows using Wright's workspace controls while the embedded canvas reflects the selected workspace document and returns current edits for revision-aware saving.

**Why this priority**: A modern canvas is useful only if Wright remains authoritative for workflow identity, persistence, policy, and execution.

**Independent Test**: Create a workflow, edit it on the canvas, save it, close and reopen it, then lint and run it from Wright; verify the saved graph and selected workspace workflow remain consistent throughout.

**Acceptance Scenarios**:

1. **Given** a workspace workflow, **When** Wright opens or replaces the active document, **Then** the canvas shows that exact workflow without a browser file dialog or duplicate project catalog.
2. **Given** unsaved canvas edits, **When** the engineer uses Wright's save control, **Then** the current project is stored as a new workspace revision and the success or conflict result is visible in Wright.
3. **Given** a saved workflow, **When** the engineer uses Wright's lint or run control, **Then** Wright evaluates the workspace-authoritative revision rather than editor-private state.
4. **Given** multiple workspace workflows, **When** the engineer switches the selected workflow, **Then** the canvas transitions to the selected document without leaking another workspace's project state.

---

### User Story 3 - Use the Modern Editor Reliably Offline (Priority: P3)

An engineer can use the replacement editor in supported native and containerized Wright installations without a runtime download, public content dependency, or fallback to the retired editor.

**Why this priority**: Wright's offline and packaged distribution promises must remain true after the editor replacement.

**Independent Test**: Start Wright with network access denied on each supported packaging path, open a Rivet workflow, and complete a canvas edit and save without any request for editor code or assets.

**Acceptance Scenarios**:

1. **Given** a supported offline installation, **When** the engineer opens the Rivet editor, **Then** all required editor code and visual assets load locally.
2. **Given** the replacement editor is disabled or unavailable, **When** the engineer requests it, **Then** Wright reports a bounded availability error and does not start the retired editor.
3. **Given** two Wright workspaces, **When** each opens the editor, **Then** editor state and workflow content remain isolated by workspace.

---

### User Story 4 - Start a Workflow from a Template (Priority: P1)

An engineer opens the template chooser from the focused Wright workflow toolbar, reviews a small curated set of packaged Rivet 2 projects, and creates a fresh workspace workflow from one selection without leaving the canvas.

**Why this priority**: A useful modern canvas needs an immediate path from an empty project to a working graph, especially for the upcoming MCP client workflow.

**Independent Test**: Open the template chooser, instantiate the same template twice, and verify that both workflows appear under distinct filenames with independent project, graph, node, and connection identities.

**Acceptance Scenarios**:

1. **Given** the Rivet canvas is open, **When** the engineer invokes the template action, **Then** Wright shows the reviewed templates with descriptions and configuration requirements.
2. **Given** a selected template, **When** the engineer creates it, **Then** Wright stores a new workspace-authoritative workflow and opens it on the canvas.
3. **Given** the same template is selected more than once, **When** the workflows are created, **Then** each receives a collision-safe filename and fresh Rivet project, graph, node, and connection identities.
4. **Given** the workflow is open in a Wright tab, **When** the canvas toolbar is displayed, **Then** the filename appears only in the tab and the toolbar omits duplicate filenames, workflow switching, and routine status prose.

### Edge Cases

- The selected workflow is deleted, renamed, or replaced while its canvas is open.
- A workflow contains data accepted by the legacy editor but rejected or normalized by the modern editor.
- The editor reports a save after the workspace revision changed elsewhere.
- The retained surface is hidden, reopened, refreshed, or stopped while it contains unsaved edits.
- A graph has no nodes, a very large node count, missing optional plugins, or an unknown node type.
- A user invokes a keyboard shortcut whose legacy meaning belonged to hidden editor chrome.
- The replacement artifact is missing, has the wrong checksum, or attempts to load a remote asset.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST replace the retired Rivet editor with the approved Rivet 2 editor and MUST NOT fall back to the retired editor.
- **FR-002**: The embedded editor region MUST display the graph canvas and graph-authoring contextual surfaces only.
- **FR-003**: The embedded region MUST hide Rivet-owned project tabs, file menu, project navigation, execution controls, status bar, settings, help, prompt design, test tooling, chat viewer, data studio, and web-app design surfaces.
- **FR-004**: Hiding unrelated surfaces MUST NOT prevent users from adding, selecting, moving, connecting, configuring, duplicating, or deleting graph nodes.
- **FR-005**: Wright MUST remain authoritative for workflow creation, selection, persistence, revision conflicts, linting, and execution.
- **FR-006**: Opening a workflow MUST place the selected workspace project directly on the canvas without requiring a browser file picker, import dialog, or editor-private project selection.
- **FR-007**: Saving from Wright MUST capture the complete current canvas project and preserve the existing workspace revision and conflict rules.
- **FR-008**: Switching workflows or workspaces MUST replace or isolate editor state so content cannot cross workflow or workspace boundaries.
- **FR-009**: Wright MUST provide clear loading, ready, saving, error, disabled, and unavailable states for the canvas surface.
- **FR-010**: Interactive Wright controls surrounding the canvas MUST retain stable accessibility names and test identifiers.
- **FR-011**: The replacement editor and its required assets MUST be available without runtime network access.
- **FR-012**: Wright MUST verify the identity and integrity of the packaged replacement editor before launching it.
- **FR-013**: The replacement MUST work through Wright's supported retained-surface lifecycle, including open, hide, reopen, stop, and workspace isolation behavior.
- **FR-014**: The shipped product MUST not contain or reference the retired Rivet editor artifact as an executable fallback.
- **FR-015**: Upgrade failures caused by incompatible workflow data MUST be reported without overwriting the workspace-authoritative project.
- **FR-016**: Wright MUST ship a reviewed workflow template catalog and project resources inside the workspace-service package for offline use.
- **FR-017**: Template instantiation MUST create fresh project, graph, node, and connection identities before workspace persistence.
- **FR-018**: The template chooser MUST describe configuration requirements such as a model provider, MCP server configuration, or interactive user input before creation.
- **FR-019**: The Wright tab MUST use the workflow filename, or a stable default filename before one is assigned, as its document label.
- **FR-020**: The focused workflow toolbar MUST omit a duplicate filename, workflow selector, open-workflow action, and routine success/status prose while retaining accessible status announcements.

### Key Entities

- **Workspace Workflow**: The authored Rivet project selected in a Wright workspace, including its stable identity, serialized graph, datasets, and revision.
- **Canvas Session**: The isolated retained editing state for one workspace surface, including the active workflow, readiness state, and unsaved canvas content.
- **Canvas Visibility Policy**: The allowlist of graph-authoring surfaces that may appear inside Wright and the unrelated Rivet application surfaces that must remain absent.
- **Editor Artifact**: The locally packaged Rivet 2 editor input whose version, origin, entrypoint, and integrity are verified before use.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In automated UI inspection, 100% of the disallowed Rivet application surfaces listed in FR-003 are absent while all required graph-authoring interactions in FR-004 remain usable.
- **SC-002**: The create, open, edit, save, close, reopen, lint, and run acceptance journey completes successfully for 100% of supported workspace test fixtures.
- **SC-003**: A saved canvas edit survives close and reopen with no graph-content loss in all supported native and containerized acceptance environments.
- **SC-004**: Editor startup and a complete edit/save journey produce zero runtime requests for remotely hosted editor code, fonts, scripts, styles, or images.
- **SC-005**: Cross-workspace isolation tests observe zero workflow or editor-state leakage across 100 consecutive open/switch/close cycles.
- **SC-006**: The canvas becomes ready for interaction within 5 seconds on the standard packaged-installation test environment.
- **SC-007**: Packaged artifact inspection finds zero executable references to the retired Rivet editor.
- **SC-008**: Every packaged template loads as a valid version 4 project, and 100 repeated instantiations produce no shared project, graph, or node IDs.
- **SC-009**: Component inspection finds exactly one visible workflow filename in the active editor area: the Wright tab label.

## Assumptions

- "Graphics area" means the graph canvas plus contextual menus, node editors, dialogs, and overlays strictly required for graph authoring.
- Wright's existing workspace toolbar remains the only visible place for workflow creation, selection, save, lint, run, and open-in-browser actions.
- The editor continues to run in an isolated retained surface rather than sharing Wright's application runtime or styling scope.
- Existing Wright workflow files and revision semantics remain authoritative; the replacement does not introduce a second durable project store.
- This feature replaces the editor experience only. Changes to workflow publication, approval policy, or the production runner are outside scope unless compatibility requires a bounded format update.
- Rivet 2 is pinned to an exact reviewed source revision and packaged for offline use before the feature is enabled.
