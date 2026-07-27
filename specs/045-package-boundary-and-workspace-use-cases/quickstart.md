# Quickstart: Package Boundaries and Workspace Use Cases

## Architecture fitness

```bash
uv run pytest -q tests/test_import_boundaries.py
```

The check covers production source imports, dynamic import forms, manifest validity, graph cycles, and package metadata parity.

## Direct application tests

```bash
uv run pytest -q packages/workspace_service/tests
```

These tests construct workspace operations with temporary or recording adapters and do not require an API server, real agent runtime, or network.

## Route compatibility

```bash
uv run pytest -q apps/api/tests/test_workspace_api.py apps/api/tests/test_gateway_api.py
```

## Full feature verification

```bash
uv run ruff check apps/api packages tests/test_import_boundaries.py
uv run ruff format --check apps/api packages tests/test_import_boundaries.py
uv run pytest -q
scripts/check-dev-merge.sh
```

On Windows, invoke the final gate with Git Bash:

```powershell
& 'D:\Program Files\Git\bin\bash.exe' scripts/check-dev-merge.sh
```

## Upgrade and rollback

No schema or workspace conversion occurs. Take the normal state backup before deployment, stop the process, deploy the new version, and exercise workspace CRUD/file/Git/session smoke checks. To roll back, stop the new process and restart the prior image or commit; restore the backup only if ordinary state rollback is required.
