# Feature Specification: OpenSCAD MCP & 3D Visualization

**Feature Branch**: `004-openscad-mcp`

**Created**: 2026-06-02

**Status**: Draft

**Input**: User description: "Implement the quellant/openscad-mcp MCP. Our overall plan is to support MCP servers listed in the document that follows. So continue to support these tools in a generic way. We would like to be able to visualize the 3D geometry that is created. so that should be created too (adding Three.js to the proeject). We want this work to serve as a example or template for future MCPs we add to this project. Review the openscad-mcp and consider the best way to support the functionality. Verify we can install openscad on the GB10."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register and Execute OpenSCAD MCP Server (Priority: P1)

An engineer registers the `quellant/openscad-mcp` server using the Tool Registry. Once active, the LLM agent can call the OpenSCAD tools (such as `render_preview` and `export_model`) to compile parametric scripts and render high-fidelity PNG previews or export physical model files.

**Why this priority**: Foundational functionality. Validates that stdio-based MCP servers wrapping local CLI tools can run successfully on the host environment and interact with the LLM agent.

**Independent Test**: Can be tested by registering the OpenSCAD server with the command `uv run --with git+https://github.com/quellant/openscad-mcp.git openscad-mcp`, checking that its schema-defined tools are discovered, sending a chat prompt to render a simple parametric box, and verifying the agent successfully calls the tool and receives a base64 image back.

**Acceptance Scenarios**:
1. **Given** the OpenSCAD MCP server is active in the Tool Registry, **When** the agent calls `render_preview` with a script containing `cube([10, 20, 30]);`, **Then** the server executes the local `openscad` binary and returns a Base64-encoded PNG image representing the 3D model.
2. **Given** a finished design in the chat session, **When** the agent calls `export_model` with the format `stl` and a path, **Then** the local OpenSCAD engine compiles the file and saves the resulting `.stl` mesh file into the active workspace directory.

---

### User Story 2 - Interactive 3D Model Viewport (Priority: P1)

An engineer wants to interactively inspect the 3D geometry of the models they are designing. When they click a `.stl` (or other supported 3D geometry) file in the Workspace Panel, the UI displays an interactive 3D WebGL Canvas rendering the mesh using Three.js, allowing the user to rotate, zoom, and pan the model.

**Why this priority**: Core requirement for visual feedback. Translates mathematical coordinate code into visual engineering structures that can be audited for collision or scale.

**Independent Test**: Can be tested by selecting a `.stl` model in the File Tree browser, asserting that the Workspace Panel displays the 3D canvas viewport, loading the STL mesh, and verifying that mouse drag interactions successfully rotate the viewport camera.

**Acceptance Scenarios**:
1. **Given** a `.stl` file exists in the active workspace file tree, **When** the user clicks the file, **Then** the Workspace Panel opens a "3D Preview" pane rendering the 3D geometry on a Three.js Canvas.
2. **Given** the 3D Preview pane is open, **When** the user drags their cursor or scrolls their mouse wheel on the canvas, **Then** the camera rotates, pans, or zooms around the object accordingly.

---

### User Story 3 - Real-Time Canvas Auto-Refresh (Priority: P2)

As the LLM agent compiles new iterations of the 3D model during the chat conversation, the interactive 3D viewer dynamically reloads and updates the rendering to show the latest changes without requiring manual user page refreshes.

**Why this priority**: Seamless agent-human design loops. Ensures the user sees the instantaneous outcome of agent modifications.

**Independent Test**: Can be tested by keeping the 3D Preview pane open on a file, programmatically overwriting the file on disk (simulating an agent tool call), and asserting that the Three.js scene triggers a reload and renders the new geometry shape.

**Acceptance Scenarios**:
1. **Given** the 3D Preview pane is currently rendering a specific STL file, **When** the agent saves a modified version of that STL file, **Then** the frontend detects the change and automatically updates the Three.js viewport to display the new geometry.

---

### Edge Cases

- **Missing OpenSCAD Binary**: If the local `openscad` executable is missing or not configured on the host machine, the MCP server registry should return a clean configuration error rather than hanging or crashing the entire wright API.
- **Malformed SCAD Code**: If the agent submits invalid syntax to the OpenSCAD renderer, the tool must return the exact compiler error stream (stdout/stderr diagnostics) to the agent so it can self-correct.
- **Large STL Files**: When loading very large CAD assemblies (e.g. >20MB STL files), the Three.js viewer must show a loading spinner and load the geometry asynchronously to prevent freezing the browser thread.
- **Headless X11/FrameBuffer constraints**: On Linux servers without an active X11 display, OpenSCAD requires a virtual framebuffer (e.g. `xvfb-run`) for headless PNG rendering. The system configuration must support prepending render execution wrapper commands.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support configuring and running the `quellant/openscad-mcp` stdio-based server locally.
- **FR-002**: The backend MUST expose a configuration variable (e.g. `OPENSCAD_PATH`) to define the local OpenSCAD binary executable location.
- **FR-003**: The backend MUST support executing the local OpenSCAD binary headlessly for rendering PNG base64 previews.
- **FR-004**: The frontend MUST include `three` and associated loader packages (such as `STLLoader`) in its dependencies.
- **FR-005**: The Workspace Panel in the frontend MUST support tabbed or split views to display both the File Tree and a "3D Preview" pane.
- **FR-006**: The 3D Preview component MUST render `.stl` files on a WebGL Canvas using Three.js.
- **FR-007**: The 3D Preview component MUST support orbit controls (rotate, zoom, pan) with mouse/touch interactions.
- **FR-008**: The frontend MUST implement file-change listeners to dynamically reload the rendered mesh in the 3D Canvas when the active file is modified.
- **FR-009**: All tool executions and rendering calls MUST propagate the `trace_id` for OpenTelemetry span monitoring.

### Key Entities

- **McpServer (Extended)**: Configured with stdio execution details to spawn `openscad-mcp`.
- **GeometryArtifact**: Represents a 3D geometry file (e.g., `.stl`, `.scad`) created in the workspace.
  - `path` (String): Unique absolute path in the vault.
  - `fileType` (String): `stl` | `scad`.
  - `size` (Integer): Size in bytes.
  - `lastModified` (Timestamp): Timestamp used for change-detection and cache-busting.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The local OpenSCAD MCP server must register and return its tool schema in under 2 seconds.
- **SC-002**: Headless rendering of a simple 3D shape (e.g. cube or sphere) must complete and return the Base64 image to the agent in under 3 seconds.
- **SC-003**: The Three.js WebGL canvas must initialize and render a standard 1MB STL file in the browser in under 300ms from selection.
- **SC-004**: Interactive orbit movements (rotate/zoom) must run smoothly at a minimum of 60 FPS on standard modern desktop web browsers.

## Assumptions

- The host environment running the backend has a functional OpenSCAD installation.
- Headless rendering on headless Linux systems will use `xvfb-run` or similar wrappers if a physical display server is absent.
- The default viewer focuses on `.stl` mesh rendering; rendering `.scad` files directly in WebGL is out of scope (they will be rendered headlessly by the OpenSCAD binary and output to the agent as PNGs, or compiled to STLs for Three.js display).
