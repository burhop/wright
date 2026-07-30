# Workspace Surfaces Migration and Rollout

## Compatibility Goals

- Existing code, text, Markdown, image, PDF, STL/3D, notebook and other registered viewers keep their provider IDs, document behavior, commands and stable test IDs wherever practical.
- `/api/workspace/files/content` keeps its current editor-oriented contract; static/active preview uses dedicated surface resource routes.
- Existing saved workspace layouts load without data loss. File paths become `kind: file` surface sources; unsupported/stale fields are ignored safely.
- Existing MCP tools/results without UI metadata behave unchanged. UI capability is additive and explicitly negotiated.
- Existing clients may continue using the old viewer store during a bounded compatibility window; no live app or MCP authority is exposed through that path.

## Feature Flags

| Flag | Initial state | Scope | Rollback behavior |
|---|---|---|---|
| `workspace_surfaces_model` | internal/test | server + web | Revert to legacy file tabs; new rows retained but ignored |
| `python_display_surfaces` | internal/test then opt-in | workspace | Existing artifacts remain in vault; ingestion disabled cleanly |
| `managed_live_apps` | opt-in/admin policy | deployment/workspace | Revoke presentations and stop owned runtimes before disable |
| `mcp_apps_host` | opt-in then default | deployment | Stop advertising extension; fallback content remains |
| `webmcp_surface_adapter` | experimental opt-in | deployment/workspace | Unregister/cancel adapter tools; managed page still displays |
| `surface_focus_layout` | opt-in then default | user | Migrate back to ordinary layout without changing surfaces |

Feature flags never bypass schema validation, authentication, target policy, isolation or cleanup.

## Data Migration

1. Add forward-compatible surface, instance, runtime, presentation, preference, display revision, grant, MCP binding and diagnostic indexes/tables using the repository's migration mechanism.
2. Append the next contiguous, checksummed data-vault migration (currently expected to be migration 6); never modify an applied migration. Add layout schema version `2`. On first read, transform every valid legacy tab path into a file `SurfaceDescriptor` compatibility record and preserve active-tab/order/width intent.
3. Do not persist or migrate legacy iframe runtime state, window references, global WebMCP handlers, PIDs, ports or tokens.
4. Keep legacy layout data until the version-2 record has been written and read successfully; record migration outcome without path/content leakage.
5. The data-vault framework intentionally rejects a database with a future schema version, so binary rollback requires stopping Wright and restoring the automatic pre-upgrade backup using the documented database restore procedure. It is not safe to claim an old binary can ignore the new schema. New vault payloads created after that backup remain subject to the explicit recovery/retention procedure.

## API and Contract Versioning

- New surface APIs live under `/api/workspace/surfaces` and carry schema version 1.
- Preview paths are a distinct data plane and never accept an upstream URL.
- Unknown major contract versions return an actionable compatibility error; additive fields are ignored by older same-major clients.
- MCP gateway accepts deprecated incoming `ui/resourceUri` metadata but emits canonical nested metadata only. Deprecation telemetry contains server/version only, not content.
- The legacy global WebMCP window relay is disabled for privileged operations, can be exposed for one compatibility release only behind an explicit unsafe-compatibility flag, and logs a deprecation event. New examples use the scoped SDK exclusively.
- The Python helper includes its display contract version in every request and emits a clear upgrade error when incompatible.

## Frontend Migration

1. Introduce `services/surfaces` types/registry and `store/surfaces` without changing existing provider implementations.
2. Add a `FileSurfaceAdapter` that projects a file source into the current `ViewerProvider`/document contract. Registry fallback continues to use current extension/MIME/predicate rules.
3. Render new and adapted sources through `SurfaceDeck`; retain stateful hosts and allow legacy static hosts to recreate using stored view state.
4. Move tab identity from normalized path to stable surface/instance IDs. Keep path as file-source data only.
5. Extract accessible tabs, toolbar, diagnostics/approval dialogs, retained deck and focus layout from `WorkspacePanel` in small behavior-preserving changes.
6. Replace pointer-only separators and non-semantic tab divs with tested primitives; add a narrow-width chat/surface switcher instead of hiding the surface.
7. Extend browser/Electron host adapters with validated absolute endpoint and external-open methods before exposing browser presentation.
8. Remove the generic iframe watchdog for surfaces; use declared protocol health or runtime health. Preserve legacy provider behavior until migrated.

## Backend Migration

1. Add domain models, repositories and use cases in `workspace_service`; API routes delegate only.
2. Add display ingestion/storage before any active web runtime, proving durable safe output independently.
3. Add generic managed-app lifecycle and capability-bound preview router behind admin policy; leave the fixed legacy Onshape proxy untouched until a separate migration is approved.
4. Extend `tool_registry` to preserve server-scoped UI metadata/resources and app visibility. Validate non-UI tool behavior with existing suites.
5. Add MCP host and WebMCP adapter only after message/origin/capability contracts pass hostile tests.
6. Package `src/wright`, renderer assets, sandbox proxy assets and schemas in native and Docker artifacts; smoke test installed distributions without a repository checkout.

## Rollout Stages

1. **Contract/fixture stage**: schemas, hostile/reference fixtures, data migration, file adapter and tests; no user-visible live app launch.
2. **Internal display preview**: safe MIME/text/image/table/Plotly and novice helper; collect performance/accessibility evidence.
3. **Managed app opt-in**: FastAPI fixture first, then BREP integration and optional framework adapters; native/Docker cleanup and transport soak required.
4. **MCP Apps opt-in**: capability advertised only to conformance-tested servers; fallback content remains primary on failure.
5. **Focus layout default**: after accessibility, narrow viewport and retained-state tests pass.
6. **Default-on surfaces**: after security review, cross-platform release matrix, package smoke and requirement audit; WebMCP native path remains experimental even if the scoped adapter is default.

## Rollback and Recovery

- Disabling display ingestion leaves accepted artifacts readable through safe fallback/download until normal retention cleanup.
- Disabling managed apps first rejects new starts, revokes all preview credentials/bridges/grants, stops Wright-owned trees to the cleanup bound, and records unresolved leaks; only then hides controls.
- A client rollback can ignore new live tabs and show a compatibility notice. It must not open a persisted preview URL/token.
- A server rollback first uses the current-version recovery command/runbook to reject new starts, invalidate preview/bootstrap authority and reconcile owned runtimes, then stops Wright, restores the pre-upgrade database backup and starts the reviewed prior binary. If the upgraded server cannot start, the recovery command runs from the upgraded distribution before backup restore; the prior binary is never started against the future schema.
- Migration and rollback procedures must be exercised on copies of representative SQLite/vault data and packaged native/Docker installations.

## Removal Criteria

Legacy viewer storage/orchestration can be removed only after two consecutive production releases show:

- all registered providers operate through `FileSurfaceAdapter`;
- no supported client reads layout version 1;
- existing viewer/editor regression suite and telemetry show no compatibility issue;
- rollback tooling no longer needs the legacy store.

The global WebMCP relay can be removed after one documented compatibility release and verification that all shipped examples/integrations use the scoped SDK. The fixed Onshape proxy is not automatically removed by this feature; its replacement requires its own tested migration because changing it could affect existing users.
