# Pure process projection — T008 and partial T009

Date: 2026-09-30. Branch: `codex/083-process-working-interfaces`.
Environment: Windows, Python 3.13.5, pytest 9.0.3; current editable packages.

Tests were introduced before the module existed and the first run failed with
the expected missing `process_interfaces.projection` import. The implemented
pure fold now passes **24 tests in 0.82 seconds**:

```powershell
.venv/Scripts/python.exe -m pytest `
  packages/workspace_service/tests/test_process_interaction_projection.py `
  -q -p no:cacheprovider --tb=short `
  --basetemp=.local-run/process-interfaces-083/pytest/projection-green-2
```

Ruff check and format pass for the projection and tests.

## Checked scope

- Preparation versus run identity, explicit waiting/cancellation/unknown states,
  original historical source references, restricted capabilities and exact result
  producer/port/path/hash linkage.
- Retention of owner-supplied missing-measurement/review reasons; unknown external
  outcomes cannot enable repeat submission. The fold only narrows owner permission.
- Actual `ProcessValidationService` structured-reader assessments and superseding
  currentness, preserving full-subject digest and exact result/hash matching.
  A pass does not override a pending approval or unavailable capability.
- Nullable telemetry/freshness, declared checkpoint/schema and exact navigation.
- An attached run cannot inherit another preparation's values. Legacy records
  without new snapshot metadata expose unknown identity rather than a guessed one.
- Only supported hashed file representations receive preview capabilities.
  Native/value results retain exact canonical navigation; specialized readers and
  toolpath/analysis views remain T044 work.

## Pending composition and acceptance

`ProjectionFacts` and `RecordedRun` are internal application data, not public
request schemas or a new persisted run table. Existing owners must supply live
facts and reconcile leases/checkpoints/options/currentness before projection.
T009 is still pending for that complete composition; source/run/checkpoint/API
integration and paging are not established by the pure tests. Overlarge pages
currently return an explicit unsupported reason rather than silently dropping
evidence. No served browser, model authoring, engineering-tool chain, external
effect or human acceptance is claimed.

## Combined regressions

The following combined command completed with **187 passed, 1 skipped in 17.16
seconds** (the host cannot create the existing symlink fixture):

```powershell
.venv/Scripts/python.exe -m pytest `
  packages/core/tests/test_process_interface_contracts.py `
  packages/core/tests/test_process_validation.py `
  packages/data_vault/tests/test_process_interface_migrations.py `
  packages/data_vault/tests/test_migrations.py `
  packages/data_vault/tests/test_workflow_continuation_repository.py `
  packages/data_vault/tests/test_process_validation_repository.py `
  packages/workspace_service/tests/test_process_interface_service_boundaries.py `
  packages/workspace_service/tests/test_process_interaction_projection.py `
  packages/workspace_service/tests/test_workspace_service.py `
  packages/workspace_service/tests/test_workflow_execution_snapshot.py `
  packages/workspace_service/tests/test_workflow_execution_continuation.py `
  -q -p no:cacheprovider --tb=short `
  --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/regressions-1
```
