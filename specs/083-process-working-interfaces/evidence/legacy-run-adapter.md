# Legacy run adapter — T015

**Date:** 2026-09-30. **Branch:** `codex/083-process-working-interfaces`.
**Environment:** Windows, repository virtual environment, Python 3.13.5.

## Implemented behavior

`POST /api/workspace/workflow-sources/run` delegates JSON and NDJSON requests to
the existing `ProcessRunSupervisor`. The request observes the backend-owned task;
disconnecting does not cancel execution or close its runtime. Native start,
status, event attachment and explicit cancellation retain the same owner and
recorder. No parallel executor or scheduler was added.

An optional request ID identifies a legacy start. The first request freezes source
defaults into the existing immutable input snapshot. Concurrent/retried requests
with that ID recover the original snapshot/receipt and do not execute again.
Changed source/policy identity conflicts. Old callers without an ID get a new ID.
The response carries `X-Wright-Run-Id` for exact attachment.

Shared source-origin/template/integration checks run before input freezing and are
rechecked by actual preparation. Existing diagnostic codes, model-unavailable
status, review checkpoints, approval continuations and AI format instructions
are retained. A failed request retried with the same identity reads its recorded
failure; it does not call the model again. Engineer/admin authorization applies
before workspace lookup. Server-derived scope and current origin/auth rules remain.

Legacy events preserve compatible fields when bounded. An oversized event instead
provides metadata with an exact run/log/sequence reference. Native metadata never
exposes legacy raw prompts/results. UTF-8 serialization keeps event-page byte
bounds meaningful for non-ASCII content. The legacy final result retains its
existing schema; it is not represented as the new bounded public client contract.

The actual-file cancellation tests distinguish observer disconnect, an explicit
user request and the outcome saved by the recorder. A timed-out final checkpoint
remains interrupted/uncertain after its lease ends; it is not labelled completed
or proven cancelled. Remote provider cancellation is still T016 work.

## Verification

Real ASGI observer disconnects, SQLite receipts, saved run records, actual file
workers and an isolated stdio MCP fixture were exercised. Models and engineering
provider payloads in these checks are controlled fixtures. This does not establish
actual default-model generation, live engineering acceptance, served UI completion,
physical effects or installed distribution readiness.

The first compatibility run found two ordering regressions: template readiness
returned an input error instead of the existing conflict, and a wrong integration
grant encountered a file error first. Factoring the existing origin/grant preflight
restored both original checks. The corrected group passed 16 tests. The actual
disconnect/review/stdio MCP group passed 17 tests; supervisor/event-bound checks
passed 34 tests before the final additional viewer case. These are overlapping
groups, not additive totals.

After the reported chat-stream disconnect, the previous terminal handle was no
longer available. Its final result is deliberately not inferred. The following
separate verification was observed through terminal completion:

```powershell
.venv/Scripts/python.exe -m pytest apps/api/tests/test_process_interface_run_lifecycle.py apps/api/tests/test_process_interfaces_api.py apps/api/tests/test_workflow_sources_api.py apps/api/tests/test_engineering_workflow_template_api.py apps/api/tests/test_workflow_artifact_reviews_api.py apps/api/tests/test_workflow_integration_run_api.py apps/api/tests/test_workflow_multicheckpoint_durable_mcp.py apps/api/tests/test_workflow_stream_cancellation.py apps/api/tests/test_workflow_run_inspection_api.py apps/api/tests/test_workflow_execution_snapshot_api.py apps/api/tests/test_workflow_approval_resume_api.py apps/api/tests/test_security.py apps/api/tests/test_main_security.py packages/workspace_service/tests/test_process_run_supervisor.py packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_artifact_review.py packages/workspace_service/tests/test_process_interaction_owners.py packages/workspace_service/tests/test_process_recorded_run_read.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/legacy-stream-recovery-final
```

**209 passed, one existing skip**, 42.16 seconds. Two existing Starlette/httpx/AnyIO
deprecation warnings remain. The same test handle was observed to complete.

```powershell
.venv/Scripts/python.exe -m ruff check --no-cache apps/api/src/api/routers/workspace.py apps/api/src/api/routers/process_interfaces.py apps/api/src/api/schemas/workspace.py apps/api/tests/process_interface_fixtures.py apps/api/tests/test_process_interface_run_lifecycle.py apps/api/tests/test_workflow_sources_api.py apps/api/tests/test_engineering_workflow_template_api.py apps/api/tests/test_workflow_artifact_reviews_api.py apps/api/tests/test_workflow_integration_run_api.py apps/api/tests/test_workflow_multicheckpoint_durable_mcp.py apps/api/tests/test_workflow_stream_cancellation.py packages/workspace_service/src/workspace_service/process_interfaces/runs.py packages/workspace_service/src/workspace_service/workflow_run_preparation.py packages/workspace_service/src/workspace_service/workflow_run_record.py packages/workspace_service/tests/test_process_run_supervisor.py
```

**All checks passed.** New fixture bindings explicitly expose real process-interface
services to existing API fakes; production code has no permissive fake fallback.

## Ownership and remaining work

Only the owned legacy-router patch is staged; its pre-existing two-line prototype
cancel guard is retained outside the increment. The original nine-line startup
patch is also retained. Three protected campaign hashes are unchanged. The approved
083 feature-pointer activation is checked against current HEAD separately from
the original 082 baseline.

T001–T015 are checked. T016–T057 and their real proof requirements remain pending.
No push, merge, publication, campaign approval or physical dispatch occurred.
