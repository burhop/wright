# Quickstart: Initial UI Foundation

**Feature**: 001-initial-ui | **Date**: 2026-06-02

## Prerequisites

- Node.js 22+ (with npm)
- Git
- A modern browser (Chrome, Firefox, or Edge)

## Getting Started

```bash
# 1. Switch to the feature branch
git checkout 001-initial-ui

# 2. Navigate to the web app
cd apps/web

# 3. Install dependencies
npm install

# 4. Start the development server
npm run dev
```

The app will be available at `http://localhost:5173`.

## What You'll See

1. **Dashboard** — The landing page with an overview panel, navigation sidebar, and status indicators.
2. **Agent Chat** — Navigate via the sidebar. A three-panel layout appears: sessions sidebar (left), chat area (center), workspace browser (right).
3. **Status Bar** — In the header. Shows connectivity dots for Wright API, Hermes Agent, and LLM inference (all will show "disconnected" without a backend).

## Running Tests

### Tier 1 — Component Tests (Vitest)

```bash
cd apps/web
npm run test
```

### Tier 2 — UI Integration Tests (Playwright)

```bash
# From the repo root
npx playwright install --with-deps chromium
npx playwright test --project=ui-integration
```

## Key Files

| File | Purpose |
|------|---------|
| `apps/web/src/main.tsx` | Entry point — initializes logging and telemetry |
| `apps/web/src/tokens/design-tokens.css` | Hermes calm-console design tokens |
| `apps/web/src/components/chat/ChatLayout.tsx` | Three-panel Hermes-style chat |
| `apps/web/src/services/logger.ts` | Structured JSON logging |
| `apps/web/src/services/telemetry.ts` | OpenTelemetry trace initialization |
| `tests/ui-integration/` | Playwright integration tests |

## Observability

- **Structured logs**: Open the browser console. All log entries are structured JSON objects with `timestamp`, `level`, `message`, `component`, and optional `traceId`.
- **Trace IDs**: Traces appear in the status bar. Each navigation or chat send action generates a trace ID visible in the UI and console.
- **No backend required**: The UI works fully offline with stub data and placeholder states.

## Next Steps

After verifying the UI renders correctly:
- `/speckit-tasks` — Generate the task list for implementation
- `/speckit-implement` — Execute the implementation
