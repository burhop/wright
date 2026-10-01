# Backend-owned source runs — T013/T014 and native T015 transport

**Date:** 30 September 2026. **Branch:** `codex/083-process-working-interfaces`.
**Scope:** Controlled service/API fixtures; actual recorder, file publication,
SQLite receipts, lease reads, executor and ASGI middleware/streaming behavior.
No live model, engineering MCP, served browser or distribution proof is claimed.

## Implemented ownership

`ProcessRunSupervisor` retains at most 16 local run tasks (configured bound
1–64). It qualifies through `prepare_authorized_workflow_run`, persists the
immutable input/start identity before dispatch, and calls the existing
`execute_prompt_workflow` inside `record_workflow_run`. It adds no graph runner.
The canonical recorder/lease remains status authority. New receipts retain an
exact confined run-log locator; older receipts default to no locator and remain
readable. Indexed publication never executes against a reused run-log identity.

A start normally acknowledges after the initial record is published, before
model work completes. Its six-second publication wait is bounded; if publication
does not finish, the durable accepted receipt remains and later reads must
reconcile. Cancellation of the start observer leaves the allocated task/runtime
owned by the supervisor. Reusing an actor/process/request identity with the same
payload returns the existing receipt; conflicting inputs/policy are rejected.
Unknown/missing outcomes are never automatically executed again.

Recorded progress uses a bounded, actor/process/run/history-bound cursor. Appended
events preserve the cursor; modified history or another actor/run rejects it.
Pages contain at most 256 events and less than 64 KiB of metadata. Prompts,
responses, tool arguments and EngineeringResult payloads are not broadcast.
Results retain their owning authorized read services. Reads do not run work.

Local cancellation is currently supported for plain AI/file processes. Tool,
agent, CAD, application or external-action steps explicitly require qualified
provider cancellation/reconciliation (T016). A cancellation request is recorded
before local task cancellation; the receipt confirms a request, not its outcome.
The cancellation command itself survives observer disconnect. Repeated commands
return the durable request without recancelling a finishing task. Runtime shutdown
is recorded as interrupted rather than user cancellation; worker cleanup still
runs if supervisor shutdown reports an error. Waiting/terminal records are read
without resuming their checkpoints. Existing v2 approval authority is unchanged.

## Native routes now available

Under the existing authenticated `/api/workspace/process-interfaces` mount:

- `POST /runs`: exact prepared input/source/request identity, 202 StartReceipt.
- `GET /runs/{run_id}`: common InteractionSnapshot over existing run/result owners.
- `GET /runs/{run_id}/events`: bounded SSE history replay/follow; query cursor or
  Last-Event-ID; observer disconnect never cancels the run.
- `POST /runs/{run_id}/cancel`: explicit local supported request and actual recorder
  outcome. Server derives actor/workspace/capabilities; injection is rejected.

Responses remain no-store and use current authentication/origin/engineer-admin
gates. Progress/cancellation contracts are in the generated shared v1 fixtures.
Current-source references can read exact prior run history in the supervisor;
cancel requests still pin the original run source. Current-source snapshot
projection retains the original inputs and invalidates mismatched mutations.

## Observed verification

Tests were observed failing before event attachment/storage-cleanup/error mapping
implementation (four failures); before native run routes (four 405 failures);
before cancellation observer ownership (one timeout); and before immediate start
attachment (one missing-log failure). Each failure was corrected and rerun.

Focused final command:

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_process_run_supervisor.py apps/api/tests/test_process_interface_run_lifecycle.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/source-history-scope
```

**26 passed**, 6.32 seconds. This includes an actual ASGI SSE disconnect on the
real mounted app, lost start observer during initial file publication, cancellation
observer loss after persistence, duplicate/concurrent starts, exact input mismatch,
bounded capacity, retained earlier output, changed event history, reopened API,
missing run log, explicit cancel replay and ordered shutdown even on error.
Two existing Starlette/httpx/AnyIO deprecation warnings remain.

Broader affected regression command before the final two additional service cases:

```powershell
.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_interface_contracts.py packages/data_vault/tests/test_process_interface_migrations.py packages/data_vault/tests/test_process_run_identity_queries.py packages/workspace_service/tests/test_process_run_supervisor.py packages/workspace_service/tests/test_process_interaction_owners.py packages/workspace_service/tests/test_process_recorded_run_read.py packages/workspace_service/tests/test_workflow_execution_snapshot.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_artifact_review.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_process_input_readiness.py apps/api/tests/test_process_interface_run_lifecycle.py apps/api/tests/test_process_interfaces_api.py apps/api/tests/test_workflow_sources_api.py apps/api/tests/test_workflow_integration_run_api.py apps/api/tests/test_workflow_stream_cancellation.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/run-supervisor-full-regressions-3
```

**256 passed**, 32.28 seconds; same live handle polled to completion. The legacy
disconnect test still tests its existing request-owned behavior; passing it does
not prove the required migration is complete. Ruff passes on owned Python files.

Final rerun, including all final service cases and existing authentication/origin
regressions:

```powershell
.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_interface_contracts.py packages/data_vault/tests/test_process_interface_migrations.py packages/data_vault/tests/test_process_run_identity_queries.py packages/workspace_service/tests/test_process_run_supervisor.py packages/workspace_service/tests/test_process_interaction_owners.py packages/workspace_service/tests/test_process_recorded_run_read.py packages/workspace_service/tests/test_workflow_execution_snapshot.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_artifact_review.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_process_input_readiness.py apps/api/tests/test_process_interface_run_lifecycle.py apps/api/tests/test_process_interfaces_api.py apps/api/tests/test_workflow_sources_api.py apps/api/tests/test_workflow_integration_run_api.py apps/api/tests/test_workflow_stream_cancellation.py apps/api/tests/test_security.py apps/api/tests/test_main_security.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/run-supervisor-final-regressions-4
```

**272 passed, one existing skip**, 33.19 seconds. All handles completed; none is
left as an assumed live wait. Twelve original runtime/prototype file hashes,
three protected review/binding hashes and the exact original main.py prototype
patch match the saved baselines. No prototype file is included in this increment.

## Remaining

The T015 statement at this checkpoint is superseded by the
[legacy adapter evidence](legacy-run-adapter.md): both source-start formats now
delegate to the same backend supervisor. T016 provider-aware observations and
cancellation remain pending. The client/kit/common UI, declared interactions,
actual Wright model authoring, live digital engineering proofs, vendor migration,
served editor journey and installed distribution checks are still required.
