# Workspace Surfaces Foundation Red-Phase Evidence

Date: 2026-07-30

Scope: Phase 2 test tasks T011-T019 before implementation tasks T020-T034.

## Result

The foundational contract tests were written, linted, and executed before the
corresponding production modules. Failures match the missing implementation
boundaries; existing file-viewer/API behavior and the package fitness rules
remain green.

| Contract group | Command | Expected result observed |
|---|---|---|
| Core model, repository, service, API, telemetry, diagnostics | `uv run pytest` over the new Phase 2 Python files plus boundary tests | RED during collection: missing `core.surfaces.models`, `core.surfaces.telemetry`, `data_vault.surface_repository`, `workspace_service.surfaces.service`, and `api.routers.surfaces` |
| Migration 6 | `uv run pytest packages/data_vault/tests/test_surface_migration.py -q` | RED: runtime migration list is `[1,2,3,4,5]`, upgrade remains at 5, and no migration-6 backup is produced; future-schema guard already passes |
| Frontend contract/store/file adapter | `npx vitest run src/services/surfaces/surface-contract.spec.ts src/store/surfaces.spec.tsx src/services/surfaces/file-surface-adapter.spec.ts` | RED: all three planned production modules are unresolved |
| Installed wheel | `uv run pytest tests/packaging/test_wright_surface_package.py -q` | RED: clean installed `wright` import has no `CONTRACT_VERSION`; packaged schema asset test already passes |
| Legacy file API and package boundaries | `uv run pytest apps/api/tests/test_workspace_file_content_compat.py tests/test_import_boundaries.py -q` | GREEN: 17 tests pass, proving the red suite does not redefine existing file content behavior or loosen dependency direction |
| Test quality | Ruff format/check, Prettier check/write, web ESLint | GREEN |

No test was skipped, weakened, or rewritten to manufacture a passing result.
Implementation proceeds against these contracts.
