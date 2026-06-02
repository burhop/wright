# Quickstart: MCP & Tool Registry

**Branch**: `003-mcp-tool-registry` | **Date**: 2026-06-02

## Setup

### 1. Database Migrations
Run the Python migration command to initialize the `mcp_servers` and `mcp_tools` tables inside the local SQLite database:

```bash
uv run python -m api.database.migrate
```

### 2. Launching the App
Select the compound VS Code run configuration: **"Wright App (API + Frontend - Standard Run)"** (F5) or run manually from the root:

```bash
# Start backend
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

# Start frontend (separate shell)
npm run dev --prefix apps/web
```

### 3. Adding a Custom MCP Server
Open your browser at `http://localhost:5173/tools` (or click "Tool Registry" in the sidebar). 
1. Click the **"+ Add Custom Tool"** button in the top right.
2. Select **"stdio subprocess"** as connection type.
3. Name it `Standards Checker`.
4. Provide the shell command to execute, e.g.: `uv run standards-mcp --check`.
5. Click **"Save"**. The backend will spawn it, perform dynamic schema discovery, and populate the tool list automatically.

---

## Running Verification Suites

Verify your implementation changes locally using the test pyramid tasks:

```bash
# 1. Run Vitest component tests (Verify Registry UI lists servers)
npm run test --prefix apps/web

# 2. Run Playwright integration tests (Verify Add Custom Tool form flow)
npx playwright test

# 3. Run pytest backend adapter tests (Verify stdio CLI subprocess lifecycle)
uv run pytest
```
