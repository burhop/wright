# User Story 3 green evidence

Recorded 2026-07-30 on Windows, branch `053-workspace-surfaces`.

## Outcome

The hostile security story now has production boundaries for exact grants,
messages, preview credentials and hosts, target pinning, proxy headers/cookies
and redirects, iframe policy, bridge origin/window/generation validation,
revocation, resource limits, direct-only external URLs, file containment, and
surface-specific redaction. All services are present in the production surface
composition graph.

BREP-class JavaScript applications retain scripts, forms, same-origin behavior
within their own opaque origin, WebSocket connectivity, workers, blobs, and
inline styles. Popup, download, top-navigation, clipboard, device, and other
authority remains declaration-, policy-, and grant-controlled.

## Python security and compatibility gate

```text
uv run pytest [16 focused US3, presentation, migration, composition, and telemetry files] -q

78 passed, 1 pre-existing Starlette/httpx deprecation warning
```

The affected Python source and test directories also pass Ruff:

```text
uv run ruff check packages/core/src/core packages/data_vault/src/data_vault \
  packages/data_vault/tests packages/workspace_service/src/workspace_service \
  packages/workspace_service/tests/surfaces apps/api/src/api apps/api/tests \
  tests/security

All checks passed!
```

## Web and browser gate

```text
npm run test -- \
  src/services/surfaces/bridge/surface-bridge.spec.ts \
  src/components/surfaces/CapabilityDialog.spec.tsx \
  src/components/surfaces/ExternalUrlSurface.spec.tsx \
  src/services/surfaces/presenters/live-app-presenter.spec.ts

4 files passed; 11 tests passed

npm run lint
passed

npm run build
passed (existing Vite >500 kB chunk advisory only)
```

The real Chromium mocked-host journey ran against the production iframe
presenter and the hostile fixture:

```text
npx playwright test \
  tests/ui-integration/workspace-surfaces/hostile-surface.spec.ts \
  --project=chromium

2 passed
```

It verified distinct-origin parent/storage/cookie isolation, preview `/api`
denial, popup/device/download/top-navigation restrictions, ignored wildcard
messages, stable redacted audit expectations, and no top-level navigation.

## Migration and audit

Migration 8 is forward-only and leaves migrations 1-7 immutable. It separates
the one-time bootstrap expiry from the bounded presentation-session expiry and
stores only presentation-cookie digests. Upgrade-from-5, upgrade-from-6,
future-schema rejection, legacy-authority revocation, and fresh schema tests are
included in the 78-test gate.

`git diff --check` passed; only line-ending conversion notices were emitted.
