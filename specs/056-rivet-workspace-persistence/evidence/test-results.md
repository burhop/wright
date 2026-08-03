# Test Results

Environment: Windows x64, Python managed by `uv`, 2026-08-03.

- `uv run pytest packages/workspace_service/tests/test_workflow_persistence.py packages/data_vault/tests/test_workflow_repository.py apps/api/tests/test_rivet_workflow_feature_flag.py -q`: 12 passed.
- `uv run ruff check` on changed API, workspace-service, data-vault, and test sources: passed.
- `uv run mypy` on new persistence and index modules: passed.
- `uv run pytest packages/data_vault/tests/test_migrations.py packages/data_vault/tests/test_surface_migration.py packages/data_vault/tests/test_workspace_repository.py packages/data_vault/tests/test_workflow_repository.py -q`: 16 passed.
- `uv run pytest packages/workspace_service/tests -q`: 181 passed, 5 skipped.
- `uv run pytest packages/data_vault/tests -q`: 60 passed, 1 skipped.
- `uv run pytest apps/api/tests/test_workspace_api.py -q`: 45 passed.

Focused coverage includes workspace isolation, unsafe slugs, recoverable delete, index projection/rebuild, default-off feature behavior, revision conflicts, and 100 stale-save trials.

The additive `workspace_workflow_metadata` migration is ledgered as schema version 10 and existing migration tests were updated to avoid hard-coding the prior schema ceiling.
