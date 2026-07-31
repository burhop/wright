# User Story 2 test-first evidence

Recorded 2026-07-30 on branch `053-workspace-surfaces` before User Story 2
implementation.

## Presentation service and API

```text
uv run pytest
  packages/workspace_service/tests/surfaces/test_presentation_service.py
  apps/api/tests/test_surface_presentations_api.py -q

2 collection errors:
- workspace_service.surfaces.presentation_service was missing
- api.routers.surface_presentations was missing
```

The failures occurred before route or service implementation and therefore
proved that the tests did not pass through an existing presentation path.

## Browser and desktop host boundaries

```text
npx vitest run src/services/host-adapter/browser-adapter.spec.ts

3 failed, 6 passed:
- issued absolute preview URL validation was absent
- guarded external open was absent
- approved direct-URL handling was absent
```

```text
node --test hermes-wright-panel/tests/surface-host-adapter.spec.cjs

The Electron assertions were authored before the implementation, but a
separate failing runner output was not retained before the first green run.
That is an evidence gap, not a passing red-state claim; the final story record
will preserve this limitation.
```

## Surface controls

```text
npx vitest run src/components/surfaces/SurfaceToolbar.spec.tsx

1 suite failed during import because SurfaceToolbar.tsx did not exist.
```

The component, restoration, presenter/deck, and mocked browser journeys were
then added without weakening these expectations. The final combined green run
is intentionally pending because the local command-approval quota became
unavailable after the partial implementation runs; no unverified task is
marked complete and no User Story 2 implementation commit has been created.
