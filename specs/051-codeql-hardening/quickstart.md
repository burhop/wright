# Quickstart: Validate CodeQL Security Hardening

Run from the repository root on `051-codeql-hardening`.

## Focused Python Security Regressions

```bash
uv run python -m pytest -q \
  packages/agent_adapters/tests/test_health_probe_security.py \
  packages/data_vault/tests/test_file_vault.py \
  packages/workspace_service/tests/test_workspace_service.py \
  packages/tool_registry/tests/test_version_check.py \
  apps/api/tests/test_setup_api.py \
  apps/api/tests/test_vault_security.py \
  apps/api/tests/test_agent_security.py \
  apps/api/tests/test_agent_stream_progress.py \
  apps/api/tests/test_main_security.py
```

All DNS and HTTP edge cases are mocked; the focused suite must not contact the internet.

## Focused Frontend Regressions

```bash
npm run test --workspace=apps/web -- \
  src/services/viewer-panel/__tests__/registry.test.ts \
  src/services/viewer-panel/__tests__/providers.test.ts
```

## Required Merge Gates

```bash
scripts/check-dev-merge.sh
scripts/check-prod-merge.sh
```

The dev gate must pass before feature-to-dev merge. The production gate runs on final updated dev only as a readiness check; do not merge main.

## GitHub Verification

1. Confirm every pull-request workflow passes, including CodeQL.
2. Merge only into `dev` after the local dev gate and PR checks are green.
3. Fast-forward local `dev` and wait for every workflow on the final dev commit.
4. Verify production findings #3, #4, #5, #7, #8, #10, #12, #24, #25, #27, #28, and #29 have no open dev instance.
5. Verify #2 is dismissed as `used in tests`; verify #13 is fixed, or dismissed as `false positive` only with the required evidence.
6. Explicitly distinguish any still-visible main instance from the fixed dev result.
