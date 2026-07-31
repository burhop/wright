# User Story 1 test-first evidence

Recorded 2026-07-30 on branch `053-workspace-surfaces` before User Story 1
implementation.

## Python SDK, contract, API, service, and e2e

```text
uv run pytest tests/sdk/test_wright_graphs.py
  tests/sdk/test_wright_display_adapters.py
  tests/contract/workspace_surfaces/test_display_envelope.py
  apps/api/tests/test_surface_display_api.py
  packages/workspace_service/tests/surfaces/test_display_service.py
  tests/e2e/workspace-surfaces/test_python_display.py
  tests/packaging/test_workspace_surface_examples.py -q

6 collection errors:
- wright.models missing
- wright.adapters missing
- workspace_service.surfaces.display_service missing
- api.routers.surface_displays missing
```

The separate clean-wheel example smoke reached the installed artifact and failed
because `wright.client` was not yet packaged.

## Frontend renderers

```text
npx vitest run
  src/services/surfaces/renderers/safe-renderers.spec.tsx
  src/services/surfaces/renderers/plotly-renderer.spec.tsx

2 suites failed during import because safe-renderers.tsx and
plotly-renderer.tsx did not exist.
```

## Mocked browser journey

```text
npx playwright test
  tests/ui-integration/workspace-surfaces/python-display.spec.ts
  --project=chromium --grep "shows, updates" --workers=1

1 failed: surface-tab-surface-loads was not found.
```

All new Python test sources passed Ruff, and both renderer test sources passed
ESLint before the red runs. These failures therefore identify missing User Story
1 behavior rather than malformed test code.
