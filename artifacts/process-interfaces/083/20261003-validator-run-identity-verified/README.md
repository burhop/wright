# Source validator identity across durable runs

The actual second isolated Heat run produced 17 CAD/solver outputs, then its
validator failed with `Idempotency key was used for different input`. The adapter
used only the step/revision invocation and `revision:0` key in one workspace;
the second request contained different run-specific output identities.

Two focused regressions reproduce that exact conflict before the fix. The
existing adapter now derives its bounded idempotency key from durable run ID,
step and revision. Storage retains its exact-request conflict and retry rules.
Historical attempts and source/UI bindings are not rewritten.

Six affected suites pass 128 cases with no skips, including passing and measured
failure second-run scenarios, and identical retries returning each original
assessment/attempt. Rework, exact result identity, validation security and run
paths remain covered. Ruff passes both owning files. Exact XML and protected
preservation checks are included; this is controlled regression evidence.

The live Heat API remains loaded from a4cfc474. This record does not prove a
successful actual repeat gate on the corrected backend. Preserve its failed run
and all first/second output bytes. Reconcile terminal work and owned services
before a cold load; use a fresh isolated run without replaying consumed actions.

## Reproduce

Use a fresh pytest temporary/cache directory from the repo:

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_process_validation.py packages/workspace_service/tests/test_workflow_process_validation_rework.py packages/workspace_service/tests/test_validation_result_identity.py packages/workspace_service/tests/test_process_validation.py packages/workspace_service/tests/test_process_validation_security.py packages/workspace_service/tests/test_workflow_run_paths.py -q
.venv/Scripts/python.exe -m ruff check packages/workspace_service/src/workspace_service/process_validation/process.py packages/workspace_service/tests/test_workflow_process_validation.py
```

No tool dispatch, review decision or engineering release occurred in these tests.
All remaining Feature 083 tasks retain their full scope.
