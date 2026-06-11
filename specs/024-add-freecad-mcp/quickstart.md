# Quickstart: Verifying FreeCAD MCP Integration

This guide provides steps to manually verify the FreeCAD installation and tool functionality on the host (GB10) and inside the Docker container.

## 1. Verify Host Installation (GB10)

1. Verify that FreeCAD was successfully installed via Snap:
   ```bash
   /snap/bin/freecad.cmd --version
   ```
   *Expected Output*: Displays the FreeCAD version info (e.g. `FreeCAD 1.1.1` or similar).

2. Start the local Wright FastAPI server and frontend Vite development server:
   - Frontend: `http://localhost:5173`
   - Backend API: `http://127.0.0.1:8000`

3. Open the web interface at [http://localhost:5173/tool-registry](http://localhost:5173/tool-registry).
4. Locate the **FreeCAD Engineering** tool card.
5. Click **Install**.
6. Verify the card status changes to **Active** (green).
7. Expand the details to see the listed tools (e.g. `step_to_stl`, `create_shape`, etc.).

---

## 2. Verify Docker Container Environment

1. Start the container stack:
   ```bash
   docker-compose up --build -d
   ```

2. Exec into the running `wright_agent` container:
   ```bash
   docker exec -it wright_agent bash
   ```

3. Inside the container, verify that FreeCADCmd is installed and executable:
   ```bash
   freecadcmd --version
   ```
   *Expected Output*: FreeCAD command line version is printed successfully.
