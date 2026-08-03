# Retained Rivet Editor Host Evidence

**Branch**: `064-retained-editor-host`
**Base**: `9c0c19b`
**Date**: 2026-08-03

## Requirements traceability

| Requirement | Evidence |
|---|---|
| FR-001 / SC-001 | `test_manual_surface_manifest_is_verified_and_collision_safe`, `test_editor_host_serves_health_and_spa_routes_from_supplied_root`, and the workspace-panel component test verify the pinned, isolated surface declaration and local host. |
| FR-002 | `RivetWorkflowsPanel.spec.tsx` checks the visible manual browser import/export disclosure and absence of a workspace-save control. |
| FR-003 | Generated manifest has empty capabilities, no injected environment, and the UI only submits the server-owned manifest. |
| FR-004 / SC-003 | Disabled generic and editor-specific declarations reject before service/process resolution; missing host assets provision nothing. |
| FR-005 | `WorkspaceManifestStore` accepts the generated manifest without changing workflow persistence; workspace confinement and symlink rejection are covered. |
| SC-002 | `test_isolated_surface_reuses_its_retained_instance_for_the_same_declaration` proves a repeated declaration key produces one retained instance. |

## Verification

- Focused Python suite: 31 passed, 1 skipped because symbolic-link creation was unavailable on this Windows host, and 1 third-party TestClient deprecation warning.
- Focused web component suite: 2 passed.
- Web production build and changed-file Ruff checks passed.
- `git diff --check` passed.

## Rollback and limitations

`WRIGHT_RIVET_EDITOR_ENABLED` defaults off. When disabled, both the editor route and a direct generic-surface declaration are rejected; application shutdown owns the lifecycle stop path. This manual mode intentionally has no Wright workspace file, gateway, secret, or execution bridge. Full workspace-authoritative editor save/load remains in the previously merged adapter/persistence slice.
