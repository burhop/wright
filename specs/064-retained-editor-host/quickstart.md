# Quickstart

1. Install the verified pinned editor artifact and enable `WRIGHT_RIVET_EDITOR_ENABLED`.
2. Open **Rivet editor** from the Workflows panel.
3. Confirm the isolated workspace tab and manual import/export disclosure.
4. Use the browser picker to import/export a project; confirm no workspace workflow file changes.
5. Disable the feature and confirm the tab cannot start while ordinary Wright operation continues.
## Local verification record

The retained-host slice was verified on 2026-08-03 with:

- `uv run python -m pytest packages/workspace_service/tests/test_workflow_editor.py packages/workspace_service/tests/test_rivet_editor_host.py packages/workspace_service/tests/surfaces/test_live_app_manager.py apps/api/tests/test_surfaces_api_contract.py apps/api/tests/test_rivet_workflow_feature_flag.py -q` — 31 passed, 1 skipped (Windows symbolic-link privilege unavailable), 1 upstream TestClient deprecation warning.
- `npm test -- --run tests/RivetWorkflowsPanel.spec.tsx` — 2 passed.
- `npm run build` — passed; the existing Vite large-chunk advisory remains.
- `uv run ruff check` for changed Python sources and tests, plus `git diff --check` — passed.

The tests cover checksum and manifest confinement, workspace-local manifest creation, isolated sharing with no capabilities, repeated retained declaration, disabled/unavailable rejection before process resolution, browser-only disclosure, bounded `/health` and SPA hosting, and distinct workspace manifests. Disabling the feature rejects both the editor endpoint and a direct generic-surface declaration; existing workspace workflow files are not changed.
