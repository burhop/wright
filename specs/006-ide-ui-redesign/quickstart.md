# Developer Quickstart: IDE UI Redesign

This guide helps developers get started building and testing the IDE layout redesign.

---

## 1. Running the Local Environment

Ensure both backend and frontend are running:
```bash
# Terminal 1: Backend
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Web frontend
npm run dev --workspace=web -- --force
```

---

## 2. Running API Integration Tests

To execute tests asserting that file saves and tools list configurations update successfully:
```bash
uv run pytest apps/api/tests/test_workspace_api.py -v
```

---

## 3. Manual Verification Scenarios

### Layout Collapse Check
1. Start the web console in your browser.
2. Click the active icon in the far-left Activity Bar to collapse the Left Sidebar.
3. Collapse the Right Agent Panel by clicking its toggle header.
4. Verify the central file area stretches to occupy the full remaining viewport width.

### Editor Tab Switch Check
1. Open a STL file (`/designs/bracket.stl`) and a python file (`/app.py`).
2. Verify both open in separate tabs.
3. Click the tabs to switch views, verifying the 3D model orbit rendering persists without complete reloads.
4. Click the close `✕` button on a tab, and check that it closes properly.

### Tools Configuration Toggle
1. Click the "Tools" marketplace icon on the far-left Activity Bar.
2. Toggle a tool's activation status checkbox.
3. Verify the change triggers a sqlite configuration save to the backend.
