# Foundation evidence — T005–T007

Date: 2026-09-30. Branch: `codex/083-process-working-interfaces`.
Parent: `679447bb3ad62b670b49b27a278ff14406647809`.

## Implemented scope

- Pure core strict/frozen shapes for accepted source, input snapshots, exact
  start receipts/responses, interactions/readiness/actions/observations/navigation,
  saved UI source/assets/bindings/build provenance and coding role/jobs.
- Generated installed `core/process_schemas/contracts-v1.json`, checked against
  the Python contracts; schema references have bounded local acyclic expansion.
- Data-vault migration 22 only. Existing migration checksums/ledger rows and v2
  checkpoint payload remain unchanged during the old-database upgrade test.
- Immutable SQLite records/triggers for snapshots/receipts/responses/revisions;
  workspace/process/principal keys, conflict detection, concurrent uniqueness,
  active-revision compare-and-swap, scoped rollback and monotonic job transitions.
- Workspace-service entry composes repositories lazily on the existing database,
  reuses the existing accepted-source service and rejects unauthorized scope or
  changed source. Closed capabilities, administrative bounds and safe diagnostics.

These are preparation/presentation metadata, not another executor, scheduler,
validator or run lifecycle database. Actual start/response continuation,
projection/API/frontend/live-provider integration remain pending tasks.

## Tests and commands

Python: existing `.venv/Scripts/python.exe`, Python 3.13.5, pytest 9.0.3. Ruff uses
`--no-cache` because the preexisting cache directory is not writable in this host.

Contract, storage and service boundary tests were written and executed red before
their owning modules were introduced (missing-module collection errors).

The foundation regression command is:

```powershell
.venv/Scripts/python.exe -m pytest `
  packages/core/tests/test_process_interface_contracts.py `
  packages/core/tests/test_process_validation.py `
  packages/data_vault/tests/test_process_interface_migrations.py `
  packages/data_vault/tests/test_migrations.py `
  packages/data_vault/tests/test_workflow_continuation_repository.py `
  packages/data_vault/tests/test_process_validation_repository.py `
  -q -p no:cacheprovider --tb=short `
  --basetemp=.local-run/process-interfaces-083/pytest/foundation-3
```

The workspace service regression command is:

```powershell
.venv/Scripts/python.exe -m pytest `
  packages/workspace_service/tests/test_process_interface_service_boundaries.py `
  packages/workspace_service/tests/test_workspace_service.py `
  -q -p no:cacheprovider --tb=short `
  --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/service-2
```

Result: **29 passed, 1 skipped** (Windows cannot create the symlink fixture).
The earlier inside-checkout temp root produced 14 protected-path rejections;
moving tests outside Wright's application root preserved the guard and passed.
The contract oversized-string case initially produced an oversized node ID;
explicit parameter IDs corrected the fixture issue without weakening the bound.

Ruff check/format covers new core/storage/service modules and their new tests.
Final foundation result: **104 passed in 5.22 seconds**. All fourteen retained
runtime/prototype and protected campaign/binding hashes match the pre-implementation
baseline. Feature context activation is the intentional recorded exception.
The initial unstaged `git diff --check` passed. The first staged check also
included new planning Markdown and reported its intentional hard-break spaces;
these were corrected in the subsequent document cleanup. No code check failed.

## Limits of evidence

SQLite races and older checkpoints are fixtures. There has been no model
generation, engineering MCP execution, physical action, live UI/browser acceptance
or installed-distribution verification in this increment. No campaign checkpoint,
counter, engineering threshold or human decision has been changed.
