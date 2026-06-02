# Developer Quickstart: OpenSCAD & Three.js Viewport

This guide covers local environment setup for testing the OpenSCAD MCP integration and the Three.js 3D viewport canvas.

---

## 1. System Prerequisites

The OpenSCAD MCP server executes headlessly on Linux using a virtual frame buffer. Install the dependencies on your development host:

```bash
# Install OpenSCAD and Xvfb for headless rendering
sudo apt-get update && sudo apt-get install -y openscad xvfb
```

---

## 2. Frontend Dependencies

Add `three` and `@types/three` dependencies in the `apps/web` package:

```bash
# In wright workspace root, run:
npm install --workspace=web three
npm install --save-dev --workspace=web @types/three
```

---

## 3. Seed Database & Start Services

1. Run migrations to seed the new `OpenSCAD` MCP server configuration:
   ```bash
   uv run apps/api/src/api/database/migrate.py
   ```
2. Start the FastAPI backend:
   ```bash
   uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
   ```
3. Start the React dev server:
   ```bash
   npm run dev
   ```

---

## 4. Testing the 3D Viewer

1. Open the wright application in the browser (`http://localhost:5173`).
2. Navigate to the **Tool Registry** page and click **Activate** on the **OpenSCAD Geometry** server card. (The backend will spawn the `quellant/openscad-mcp` subprocess and discover its tools: `render_preview`, `validate_scad`, etc.).
3. Start a new Chat Session. Ask the agent:
   > "Create an STL cylinder with radius 5 and height 20 named cylinder.stl"
4. The agent will execute the `export_model` tool which creates the `cylinder.stl` file in your workspace directory.
5. In the **Workspace Browser** pane, click `cylinder.stl`. The **3D Preview** viewport will automatically load the STL mesh and render it in WebGL. Drag the cursor to rotate and scroll to zoom.
