# Quickstart: Quality, Testing & Observability Refactor

## Prerequisites

- Running Wright API: `cd apps/api && PYTHONPATH=src uv run uvicorn api.main:app --host 0.0.0.0 --port 8000`
- Running Wright Web: `cd apps/web && npm run dev`
- Jaeger running: `docker-compose up -d jaeger` (for trace visualization)

## Running Tests

### Backend API Tests (Tier 2)
```bash
cd apps/api
PYTHONPATH=src uv run pytest tests/ -v --tb=short
```

### Frontend Component Tests (Tier 1)
```bash
cd apps/web
npx vitest run
```

### Playwright UI Integration Tests (Tier 2)
```bash
# From repo root, with both API and web servers running
npx playwright test tests/ui-integration/
```

### System E2E Tests (Tier 3)
```bash
# Requires live API and web servers
npx playwright test tests/e2e/
```

### Full Suite
```bash
# Backend
cd apps/api && PYTHONPATH=src uv run pytest tests/ -v

# Frontend components
cd apps/web && npx vitest run

# UI integration
npx playwright test tests/ui-integration/

# E2E
npx playwright test tests/e2e/
```

## Verifying Traces

1. Open Jaeger UI: `http://localhost:16686`
2. Select service: `wright.api`
3. Search for traces — you should see spans like `workspace.create`, `agent.chat.start`, `db.sqlite.query`

## Verifying Frontend Log Persistence

1. Open browser DevTools → Application → IndexedDB → `wright-logs` → `entries`
2. Perform any action in the UI
3. Verify log entries appear with `timestamp`, `level`, `message`, `component`, `traceId`
