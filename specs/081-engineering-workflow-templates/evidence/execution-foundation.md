# Execution Foundation Evidence

Feature 081 adds an additive data-vault migration for durable workflow continuation checkpoints and compare-and-swap state transitions. Checkpoints survive service reconstruction, decisions cover the canonical subject digest, and two concurrent consumers cannot both obtain dispatch authority.

The initial external action kinds are `printer_transfer`, `supplier_upload_preview`, and `cart_quote_handoff`. Canonical source execution now pauses before these steps, stores `awaiting_approval` in the same indexed run log, and retains completed step/result identities in the continuation. Resume consumes one exact approval and records `not_dispatched`; it does not call a device or supplier. Reconciliation can record `dispatched`, `not_dispatched`, or `outcome_unknown`. Identical decision/resume retries are idempotent, while changed or already-consumed subjects fail. Unsupported purchase actions and credential-bearing approval subjects fail before authority is created.

Commands and results:

```powershell
uv run pytest packages/data_vault/tests/test_migrations.py packages/data_vault/tests/test_migration_failures.py apps/api/tests/test_engineering_workflow_template_api.py packages/data_vault/tests/test_workflow_continuation_repository.py packages/workspace_service/tests/test_workflow_approval_resume.py -q
```

Result after using a workspace-local pytest temporary directory: `40 passed` with one existing Starlette test-client deprecation warning.

```powershell
uv run pytest apps/api/tests/test_workflow_approval_resume_api.py apps/api/tests/test_engineering_workflow_template_api.py packages/workspace_service/tests/test_workflow_approval_resume.py packages/data_vault/tests/test_workflow_continuation_repository.py -q
```

Result: `10 passed`. The API suite covers pending detail, exact approval, one-shot resume, unknown-outcome reconciliation, wrong-run isolation, stale digest rejection, and replay rejection.

```powershell
uv run pytest packages/workspace_service/tests/test_workflow_demo_capture.py packages/workspace_service/tests/test_engineering_template_promotion.py packages/workspace_service/tests/test_engineering_workflow_templates.py packages/workspace_service/tests/test_engineering_workflow_template_instances.py packages/workspace_service/tests/test_workflow_external_action_execution.py packages/workspace_service/tests/test_workflow_approval_resume.py packages/workspace_service/tests/test_workflow_engineering_assertions.py packages/workspace_service/tests/test_workflow_results.py packages/data_vault/tests/test_workflow_continuation_repository.py packages/data_vault/tests/test_migrations.py -q
```

Result: `58 passed`. This covers durable run-log pause/projection, exact-subject compilation, one-shot authority, artifact roles and lineage fields, strict readiness promotion, instance-specific supplied fixtures, and local capture rejection/creation. The matching API slice passed `7` tests, including server-side source/artifact digest recomputation on resume. The final dialog/source/run/approval/capture client and component slice passed `100` tests across four files.

```powershell
$env:HERMES_API_BASE_URL='http://127.0.0.1:8642'
uv run pytest tests/e2e/test_engineering_workflow_template_tracing.py -q
```

Result: `1 passed` with one existing Starlette test-client deprecation warning. It asserts stable span names for template list/detail/readiness/instantiate, run, approval get/decide/resume, external-action reconciliation, engineering assertions, and local capture.

The generic engineering assertion suites cover actual mesh dimensions/topology/build volume, slice compatibility, manufacturer reference identity, CAD/CFD domain identity, solver fields/convergence/balance/sensitivity, sheet-metal revision bounds, export identity, supplier quote fields, and the no-order boundary. These are reusable validators; they are not evidence that the currently unqualified vendor integrations ran.
