# Technical Decisions & Research: OpenSCAD MCP & 3D Visualization

## 1. OpenSCAD Headless Execution on Linux

### The Problem
On headless Linux environments (such as Docker containers or server VMs), running the `openscad` command directly to compile or render models fails with the following errors:
```text
Unable to open a connection to the X server.
DISPLAY=
Can't create OpenGL OffscreenView. Code: -1.
Segmentation fault (core dumped)
```
This occurs because OpenSCAD's rendering engine relies on OpenGL and requires an active display server context (X11) to perform even offscreen calculations.

### The Solution
We use `xvfb-run` (X Virtual Framebuffer) to execute OpenSCAD inside a virtual display environment.
We tested this on the host and confirmed that wrapping the command succeeds instantly:
```bash
xvfb-run /usr/bin/openscad -o output.png input.scad
```
To enable the generic `quellant/openscad-mcp` server (which executes the binary configured in the `OPENSCAD_PATH` env var) to work in this environment without modifying its source code, we implement a wrapper script at `scripts/openscad-headless.sh`:
```bash
#!/bin/bash
exec xvfb-run /usr/bin/openscad "$@"
```
By setting `OPENSCAD_PATH` to this wrapper script, all subprocess execution calls made by the MCP server are redirected to run headlessly.

---

## 2. Three.js Integration Strategy for React

### Alternatives Considered
1. **React Three Fiber (R3F)**:
   - *Pros*: Declarative React component wrapping of Three.js scenes.
   - *Cons*: High dependency footprint. React 19 compatibility is currently complex and often requires experimental packages or beta releases.
2. **Vanilla Three.js**:
   - *Pros*: Extremely lightweight, zero React-version lock-in, direct control over WebGL rendering context. Matches the Constitution §6 (Atomic design and simplicity).
   - *Cons*: Imperative DOM manipulation within a React `useEffect` hook.

### Decision
We will use **Vanilla Three.js** by adding `three` and `@types/three` directly as dependencies in `apps/web/package.json`.
We will build a simple `ThreeDViewer.tsx` component that mounts a canvas `<canvas ref={canvasRef} />` and initializes the WebGLRenderer, Scene, PerspectiveCamera, OrbitControls, and lights inside a React `useEffect` cleanup hook. This guarantees stability under React 19.

---

## 3. Workspace File Access & Visualization

### The Problem
The frontend needs to load the raw binary contents of the generated STL meshes from the active workspace to pass them to Three.js's `STLLoader`. The existing backend has no endpoints to read files or directory structures from the active workspace.

### The Solution
We will add two lightweight endpoints to the FastAPI backend:
1. `GET /api/workspace/files`: Lists files recursively under the active workspace directory, returning names, paths, sizes, and last modified times.
2. `GET /api/workspace/files/content`: Serves the raw binary file contents.

To prevent directory traversal attacks, the backend will strictly sanitize the input path and verify it is located inside the configured active workspace directory.

---

## 4. Live Viewport Auto-Refresh

### The Problem
When the agent updates a 3D model, the file in the workspace changes. We need the Three.js viewport to automatically reload the updated mesh.

### The Solution
The frontend will run a file watch loop on the active selected file path. When a file is loaded in the viewport, the frontend stores its last-modified timestamp. A simple polling function calls the file metadata endpoint `/api/workspace/files` every 2 seconds. If the last-modified timestamp of the open file changes, the viewer triggers an asynchronous reload of the STL mesh buffer. This approach is highly robust and avoids complex WebSocket/SSE broadcast setups.
