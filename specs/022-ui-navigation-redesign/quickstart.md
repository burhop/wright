# Quickstart: UI Navigation and Dashboard Redesign

This document outlines how to use and verify the new navigation, logs, and settings interfaces in Wright.

## 1. Navigating the New Main Interface

1. Start the backend and frontend dev servers using `npm run dev` and `uv run uvicorn api.main:app`.
2. Open your browser and navigate to `http://localhost:5173/`.
3. You will land on the redesigned **Dashboard**, featuring four high-density boxes:
   - **Engineering Workspaces** (half width, listing recent workspaces).
   - **Agent Status** (monitoring Hermes tasks, active errors, and socket state).
   - **News & Resources** (releasing version news and substack/github links opening in new tabs).
   - **System Activity & Telemetry** (tracking database operations).
4. Use the global left-hand sidebar to switch to:
   - `/` (Dashboard)
   - `/tool-registry` (Tool Registry)
   - `/logs` (Logs Viewer)
   - `/settings` (Global Settings)

## 2. Using the Log Viewer and Hermes Debugger

1. Navigate to `/logs` from the main sidebar.
2. Filter logs using the filters at the top:
   - Select a workspace from the dropdown list to isolate logs from that workspace.
   - Select a log level (`info`, `warning`, `error`).
   - Type in the search box to search for specific logs.
3. To debug a specific log entry:
   - Highlight the relevant log rows.
   - Right-click and choose **Send Selection to Hermes for Help**.
   - A drawer will slide open on the right hand side containing the log context and a chat input where you can ask Hermes for debugging assistance.

## 3. Workspace Settings & MCP Tool Selection

1. Enter a workspace from the Dashboard.
2. In the workspace view, use the new left vertical row of buttons:
   - **Back Button** (Top): Returns you to the Dashboard.
   - **Explorer Button**: Opens the standard file browser tree.
   - **MCP Tools Button**: Displays a compact list of active workspace MCP tools (e.g. OpenSCAD).
   - **Git Panel Button**: Allows branch switching/creation, merging, pulling, and highlights ignored large files (>10MB).
   - **Workspace Settings Button**: Opens settings to edit the Workspace Prompt Context.
   - **Docs & Tutorials Button**: Opens learning documentation.
