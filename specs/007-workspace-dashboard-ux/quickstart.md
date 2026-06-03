# Quickstart: Workspace Dashboard UX

**Branch**: `007-workspace-dashboard-ux` | **Date**: 2026-06-03

## Prerequisites

- Python 3.13+ with `uv` package manager
- Node.js 22+ with `npm`
- SQLite 3.x (built-in)
- Wright monorepo cloned at `/home/burhop/repos/wright`

## Development Setup

### 1. Start the backend

```bash
cd apps/api
PYTHONPATH=src uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 2. Start the frontend

```bash
cd apps/web
npm run dev -- --host 0.0.0.0
```

### 3. Run database migrations (if schema changes)

```bash
cd apps/api
PYTHONPATH=src uv run python -m api.database.migrate
```

## Key File Locations

| Purpose | Path |
|---------|------|
| Dashboard page | `apps/web/src/components/pages/DashboardPage.tsx` |
| Workspace page (NEW) | `apps/web/src/components/pages/WorkspacePage.tsx` |
| Create modal (NEW) | `apps/web/src/components/common/CreateWorkspaceModal.tsx` |
| Workspace service | `apps/web/src/services/workspace-service.ts` |
| Router config | `apps/web/src/App.tsx` |
| API workspace router | `apps/api/src/api/routers/workspace.py` |
| Core workspace logic | `packages/core/src/core/workspace.py` |
| Agent base class | `packages/agent_adapters/src/agent_adapters/base.py` |
| DB migrations | `apps/api/src/api/database/migrate.py` |

## Testing

```bash
# Backend tests
cd apps/api && PYTHONPATH=src uv run pytest tests/test_workspace_api.py -v

# Frontend tests
cd apps/web && npx vitest run

# E2E tests
npx playwright test tests/ui-integration/dashboard.spec.ts
```

## Verification Checklist

1. Open `http://localhost:5173` — dashboard shows recent workspaces
2. Click "Create Workspace" — modal opens
3. Fill name + path, submit — navigates to `/workspace/{id}`
4. Workspace page loads with file tree + agent chat
5. Tool Registry shows OpenSCAD as "Installed"
6. `/agent-chat` URL redirects to dashboard
