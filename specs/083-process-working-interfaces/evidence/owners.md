# Recorded run and owner composition — T009 increment

Date: 2026-09-30. Branch: `codex/083-process-working-interfaces`.
This is service/recorder evidence, not served UI or live engineering acceptance.

## Implemented

- Exact read-only run attachment in the existing recorder, including the run ID
  persisted before the first engineering result. History and attachment use the
  same local lease probe. A foreign/unreadable owner stays unknown; reading does
  not acquire execution ownership, mutate a run log or replay work.
- Legacy result identities remain readable. Duplicate/mismatched identities,
  unsafe paths, oversized records and bounded-history exhaustion are explicit.
  The optional server-retained log locator still checks source/run identity.
  New supervisor starts will need to supply a retained/derivable locator (T014);
  the service currently uses the bounded legacy fallback.
- Run attachment recovers only its exact immutable input receipt. Receipt state
  never replaces recorded run state, and a changed accepted source does not
  replace the run's original source reference.
- Approval inspection reuses the canonical application's subject/preparation
  checks and dispatcher qualification. It never decides, consumes or dispatches
  the action. Actual mutations still recheck under their canonical lease.
- Terminal review projection rechecks actual source/input/output bytes through
  the existing review owner. Stale evidence disables review; a pointer to another
  run is rejected. Review permission remains separate from action continuation.
- Existing 082 assessments are queried by exact scoped run/producer identity,
  then read through `ValidationApplication.get_result` to recompute currentness.
  Actual structured assessments/supersession are covered by service tests.
- Pure projection now returns bounded collection pages. A page reference binds
  source, frozen inputs, run/event cursor, exact result/evidence/action facts and
  principal. Read time alone can change; changed facts require a fresh first page.
  Navigation targets remain exact. Pages do not grant permission.

The composition does not infer completion from a review decision, elapsed time,
submission receipt or producer claim. Progress percentage/time stay null when
the recorder has no such measured observation. Canonical terminal review and
external checkpoint owners retain their existing lifecycle semantics.

## Checks

New tests were run red before their missing reader/query/inspection/composition/
paging operations were added. Approval fixture assertions initially assumed no
preceding generation; corrected assertions compare with the fixture's actual
pre-inspection call list. A consumed-action fixture initially used the wrong
generator argument; it now uses the canonical resume signature. Neither change
weakens the no-replay/no-decision assertions.

Focused checks: 42 recorder/snapshot tests; 33 receipt/validation/storage tests;
20 inspection/canonical approval tests; 34 paging/pure projection tests; 8 owner
composition tests. These overlap the combined run below.

Combined regression command (repository root, existing Python 3.13 environment):

```powershell
.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_interface_contracts.py packages/core/tests/test_process_validation.py packages/data_vault/tests/test_process_interface_migrations.py packages/data_vault/tests/test_process_run_identity_queries.py packages/data_vault/tests/test_migrations.py packages/data_vault/tests/test_workflow_continuation_repository.py packages/data_vault/tests/test_process_validation_repository.py packages/workspace_service/tests/test_process_interface_service_boundaries.py packages/workspace_service/tests/test_process_interaction_projection.py packages/workspace_service/tests/test_process_interaction_pages.py packages/workspace_service/tests/test_process_interaction_owners.py packages/workspace_service/tests/test_process_recorded_run_read.py packages/workspace_service/tests/test_process_approval_inspection.py packages/workspace_service/tests/test_workspace_service.py packages/workspace_service/tests/test_workflow_execution_snapshot.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_artifact_review.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/owner-regressions-1
```

Result: **272 passed, 1 existing host symlink skip in 32.88 seconds**. The same
process handle was polled to completion; no restart was inferred from a timeout.
Ruff passes for every changed/new implementation and test module.

## Remaining

T009 remains unchecked until preparation/source-input/readiness composition is
connected to the shared input implementation. The current application method
requires an explicit attached run. Thin authenticated routes (T010), input
preflight/overlays (T011/T012), supervisor/cancel/event attachment (T013/T014), v3
declared responses and MCP actions are still pending. More than 256 retained
assessments currently produces an explicit composition-size reason; their
canonical paged reads remain available, not silently omitted.

There is no served workspace/browser, actual UI-authoring model, live MCP or
installed distribution proof in this increment. The private fixture decisions
are regression data, not engineering acceptance or live proof enrollment.
Protected campaign/prototype files remain outside this work.
