# Provider observations and qualified cancellation — T016

**Date:** 2026-09-30. **Branch:** `codex/083-process-working-interfaces`.
**Host:** Windows / repository virtual environment / Python 3.13.5.

## Ownership and behavior

The existing `wright/operation` monitor supplies compact recorded observations.
This is explicitly configured provider metadata, not an assumption that all MCP
servers implement job or MCP Tasks semantics. The same canonical executor,
recorder, gateway, preparation and process-interface projection are reused.

The optional profile fields are `progress_field`, `remaining_seconds_field`,
`metrics_fields` (at most 16 named scalar selectors), `freshness_seconds`
(0.05–300 seconds, default 30) and `cancel_confirm_seconds` (0–10 seconds,
default 1). Progress means percent and remaining time means seconds; the provider
configuration must declare suitable fields. No values are inferred from elapsed
time, AI prose, completed graph nodes or a provider's generic success flag.
Absent or invalid metrics stay null/unavailable. No fabricated 100% or zero ETA.

Status/result tool definitions and authority are qualified before submission.
Operation metadata is copied and companion tool identities/schema digests are
pinned before the gateway call. A changed binding is not adopted after submission.
When returned, an explicit status operation ID must equal the submitted ID.
Missing submission identity is an unknown outcome; it never triggers resubmission.

Each saved observation retains operation/step/provider binding, submission schema
digest, source attribution, actual observation time, freshness deadline, nullable
metrics and limitations. The compact recorder fold retains the latest event per
identity, at most 256 operations and the existing 64 KiB read bound. Truncated or
unverifiable operation history is explicit and requires reconciliation. Raw
arguments/provider results remain in the canonical run log.

The projection preserves historical observation times on reopen. Expired active
observations require reconciliation and do not show current percent/ETA. Confirmed
terminal facts remain historical facts. A locally ended run with an active or
unknown provider outcome remains reconciliation-required. Provider `input_required`
does not create a human form; that needs the later declared-input mechanism.

## Explicit cancellation

Native cancel uses the same backend-owned command path. For provider work it
reserves exactly one live qualified monitor, persists the actor/request/run and
exact operation identity, then wakes the monitor. Closing an observer cannot
abandon that command. Companion schema/current approval checks apply again before
the configured cancel invocation. Missing cancellation authority is unavailable,
not an opportunistic runtime approval question.

The reservation prevents following work from advancing while publication is
pending. Unknown publication blocks the run with an actionable unknown-outcome
reason and sends no remote cancellation. A successful request returns a request
receipt; it does not assert the provider stopped. The monitor reads actual status
within the finite confirmation budget. It retains completed, failed, cancelled
or unconfirmed outcomes distinctly, and does not resubmit the original operation.
The source run may be locally cancelled while the provider is observed completed;
both facts remain visible. Unconfirmed cancellation records reconciliation-required.

Local monitor interruption has no provider mutation authority. Runtime shutdown
records uncertain/interrupted observations rather than sending a remote cancel
because a Python observer was cancelled. Configured timeout cancellation still
uses its qualified capability and the finite confirmation policy.

The projection includes a cancellation action with an exact run/source/input
subject and an actionable unavailable reason. It is a presentation hint; the
actual command rechecks active scope/binding/authority.

## Evidence and limitations

The new metric, wrong-job, interruption and cancellation outcome checks were
observed failing before implementation (10 failures). They passed after the
monitor changes. Later fixture errors included a missing action title, missing
tool-input binding/required start parameters, an incorrect error-reason accessor
and a temporary exception/finally ordering error. Those were corrected; none is
represented as an engineering-provider defect or a successful live proof.

Canonical cancellation checks prepare accepted source and immutable inputs, use
the actual recorder/files/SQLite receipts and invoke a controlled nonphysical
provider. They exercise completed, failed, cancelled and still-working outcomes
with connected and disconnected request observers. Every case checks one submit,
one permitted cancel, durable request publication before the cancel, immediate
wakeup from a 30-second poll interval, duplicate receipt recovery and no following
output publication. The ambiguous-publication case checks zero remote cancels.

Read/reopen tests inspect actual saved logs through process services without
provider polling or mutation. These are controlled provider/model fixtures,
not actual engineering results, default-model UI creation, served UI completion,
physical cancellation or native/Docker distribution proof.

Before the final two cases, the affected regression group passed **253 tests,
one existing skip**, 57.45 seconds. The subsequent run passed 254 tests with one
fixture assertion failure; that accessor was corrected and the full group rerun.
Final result: **255 passed, one existing skip**, 59.67 seconds. The same test
handle was observed through terminal completion. Two existing
Starlette/httpx/AnyIO deprecation warnings remain.

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_async_operations.py packages/workspace_service/tests/test_process_operation_cancel.py packages/workspace_service/tests/test_process_operation_observations.py packages/workspace_service/tests/test_workflow_execution_snapshot.py packages/workspace_service/tests/test_process_interaction_projection.py packages/workspace_service/tests/test_process_interaction_owners.py packages/workspace_service/tests/test_workflow_mcp_execution.py packages/workspace_service/tests/test_workflow_application_task.py packages/workspace_service/tests/test_workflow_application_exports.py packages/workspace_service/tests/test_process_run_supervisor.py packages/workspace_service/tests/test_process_recorded_run_read.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_approval_execution.py apps/api/tests/test_process_interface_run_lifecycle.py apps/api/tests/test_process_interfaces_api.py apps/api/tests/test_workflow_execution_snapshot_api.py apps/api/tests/test_workflow_run_inspection_api.py apps/api/tests/test_workflow_stream_cancellation.py apps/api/tests/test_security.py apps/api/tests/test_main_security.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/provider-observations-final-3
```

Ruff `check --no-cache` passes for the owned source/tests. Original router/startup
prototype patches and the three protected campaign hashes are preserved. No
vendor protocol, new executor, physical dispatch, campaign decision, push or
publication occurred. The public client/common UI and later declared interactions,
approved generic operation dispatch, actual model/live engineering/browser and
installed distribution proofs remain required by T017–T057.
