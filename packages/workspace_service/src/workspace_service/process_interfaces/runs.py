"""Own local task lifetime; the existing recorder remains execution/state owner."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import PurePosixPath

from pydantic import TypeAdapter

from core.process_interactions import (
    NavigationTarget,
    StartReceipt,
    ProcessRunEvent,
    ProcessRunEventPage,
)
from core.process_validation import Digest, Identifier, canonical_digest
from core.tracing import traced
from data_vault.process_input_repository import ProcessRecordConflict

from ..workflow_run_preparation import (
    prepare_authorized_workflow_run,
    qualify_workflow_run_origin,
)
from ..workflow_run_record import (
    record_workflow_run,
    record_workflow_resume,
    read_workflow_run,
    _read_run_record,
)
from ..workflow_source_execution import (
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from ..workspace_path import WorkspacePath
from .errors import ProcessInterfaceError


@dataclass
class _OwnedRun:
    task: asyncio.Task | None = None
    emit: object = None
    cancel_request: dict | None = None
    local_cancel_supported: bool = False
    tool_runtime: object = None
    cancel_target: object = None
    checkpoint_id: str | None = None
    action_request: dict | None = None
    action_ready: asyncio.Event | None = None

    def cancellation_outcome(self):
        if self.cancel_request is None:
            return "interrupted"
        if self.cancel_target is not None and self.cancel_target.outcome not in {
            "completed",
            "failed",
            "cancelled",
        }:
            return "reconciliation_required"
        return "cancelled"


class ProcessRunSupervisor:
    def __init__(self, application, *, maximum_active=16):
        if type(maximum_active) is not int or not 1 <= maximum_active <= 64:
            raise ValueError("Run supervision requires a bounded active-task capacity")
        self.application = application
        self.maximum_active = maximum_active
        self._owned: dict[str, _OwnedRun] = {}
        self._allocation = asyncio.Lock()
        self._legacy_preparation = asyncio.Lock()
        self._commands = asyncio.Lock()
        self._cancellations: set[asyncio.Task] = set()
        self._closed = False

    def is_live(self, run_id):
        owned = self._owned.get(run_id)
        return bool(owned and owned.task and not owned.task.done())

    def _root(self, scope, process, operation="process.read"):
        scope.require(process, operation)
        record = self.application.workspace.repository.get_by_id(scope.workspace_id)
        if record is None:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This workspace is unavailable.",
                "Open the run's registered workspace.",
            )
        root = str(record["local_path"])
        self.application.workspace.ensure_workspace_path_safe(root)
        return root

    def _receipt(self, scope, process, run_id, operation="process.read"):
        scope.require_run(run_id)
        root = self._root(scope, process, operation)
        receipt = self.application.inputs.receipt_for_run(
            process.workspace_id, process.source_path, run_id
        )
        if (
            receipt is None
            or receipt.process.workspace_id != process.workspace_id
            or receipt.process.source_path != process.source_path
            or (
                (operation != "process.read" or scope.run_bound)
                and receipt.process != process
            )
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This run does not belong to the requested process.",
                "Attach its exact process and run reference.",
            )
        return root, receipt

    def _record(self, scope, process, run_id):
        root, receipt = self._receipt(scope, process, run_id)
        try:
            view = read_workflow_run(
                root, process.source_path, run_id, run_log_path=receipt.run_log_path
            )
            record = _read_run_record(
                WorkspacePath(root), view["path"], process.source_path
            )
        except (OSError, ValueError, KeyError) as error:
            raise ProcessInterfaceError(
                "OUTCOME_UNKNOWN",
                "The accepted run has no verifiable execution record.",
                "Reconcile the recorded start; do not submit it as a new request.",
            ) from error
        if record.get("source_digest") != receipt.process.source_digest:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The run record and start receipt disagree.",
                "Inspect their exact identities before continuing.",
            )
        return record, view

    @traced("process.interface.run.start")
    async def start(
        self,
        scope,
        process,
        input_snapshot_id,
        request_id,
        *,
        expected_input_digest,
        response_generator,
        gateway=None,
        session_id="",
        action_generator=None,
        integration_policy_digest=None,
    ):
        scope.require(process, "process.start")
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        expected_input_digest = TypeAdapter(Digest).validate_python(
            expected_input_digest
        )
        self._root(scope, process, "process.start")
        payload = canonical_digest(
            {
                "process": process,
                "input_snapshot_id": input_snapshot_id,
                "input_digest": expected_input_digest,
                "integration_policy_digest": integration_policy_digest,
            }
        )
        async with self._allocation:
            try:
                existing = self.application.inputs.start_receipt(
                    scope.principal_id, process, request_id
                )
            except KeyError:
                existing = None
            if existing is not None:
                if existing.process != process or existing.payload_digest != payload:
                    raise ProcessInterfaceError(
                        "REQUEST_CONFLICT",
                        "This start request already identifies different inputs.",
                        "Attach its recorded run or use a new request for the new preparation.",
                    )
                return existing
            if (
                self._closed
                or sum(self.is_live(run_id) for run_id in self._owned)
                >= self.maximum_active
            ):
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "The local run supervisor cannot accept another run.",
                    "Wait for capacity or reconnect to an active Wright runtime.",
                )
            resolved = await self.application.resolve_process(
                scope, process, operation="process.start"
            )
            frozen = self.application._input_snapshot(process, input_snapshot_id)
            if frozen.digest != expected_input_digest:
                raise ProcessInterfaceError(
                    "SUBJECT_STALE",
                    "The requested input identity changed.",
                    "Prepare the exact inputs before starting.",
                )

            def available_gateway():
                if gateway is None:
                    raise ProcessInterfaceError(
                        "CAPABILITY_UNAVAILABLE",
                        "The configured process tools are unavailable.",
                        "Connect the required providers before starting.",
                    )
                return gateway() if callable(gateway) else gateway

            try:
                prepared = await prepare_authorized_workflow_run(
                    service=self.application.workspace,
                    workspace_dir=resolved.workspace_dir,
                    workspace_id=process.workspace_id,
                    session_id=session_id,
                    source_path=process.source_path,
                    source_digest=process.source_digest,
                    input_snapshot=frozen,
                    gateway=available_gateway,
                    integration_policy_digest=integration_policy_digest,
                )
            except WorkflowSourceExecutionError as error:
                code = (
                    "SOURCE_CHANGED"
                    if error.code == "WORKFLOW_SOURCE_CONFLICT"
                    else "READINESS_UNSUPPORTED"
                    if error.code
                    in {
                        "WORKFLOW_SOURCE_INVALID",
                        "WORKFLOW_ACTION_INTENT_UPGRADE_REQUIRED",
                        "WORKFLOW_ACTION_INTENT_SCHEMA_UNSUPPORTED",
                        "WORKFLOW_ACTION_INTENT_INVALID",
                    }
                    else "CAPABILITY_UNAVAILABLE"
                )
                raise ProcessInterfaceError(
                    code,
                    str(error),
                    error.correction,
                    navigation=NavigationTarget(kind="block", block_id=error.block_id)
                    if error.block_id
                    else None,
                    details={"source_code": error.code},
                ) from error
            transferred = False
            try:
                slug = PurePosixPath(process.source_path).name.removesuffix(
                    ".workflow.wflow"
                )
                receipt = StartReceipt(
                    principal_id=scope.principal_id,
                    process=process,
                    request_id=request_id,
                    payload_digest=payload,
                    input_snapshot_id=frozen.snapshot_id,
                    input_digest=frozen.digest,
                    run_id=prepared.run_id,
                    run_log_path=f"runs/{slug}/{prepared.run_id}.json",
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                try:
                    receipt, won = self.application.inputs.reserve_start(
                        frozen, receipt
                    )
                except ProcessRecordConflict as error:
                    raise ProcessInterfaceError(
                        "REQUEST_CONFLICT",
                        "This start request already has another recorded outcome.",
                        "Attach the existing request instead of replaying work.",
                    ) from error
                if not won:
                    return receipt
                owned = _OwnedRun(
                    tool_runtime=prepared.runtime,
                    local_cancel_supported=not any(
                        step.tool_name
                        or step.agent_task
                        or step.external_action
                        or step.cad
                        or step.application
                        for step in prepared.plan.steps
                    ),
                )
                published = asyncio.Event()

                async def run():
                    async def execute(emit):
                        owned.emit = emit
                        published.set()
                        return await execute_prompt_workflow(
                            service=self.application.workspace,
                            workspace_dir=resolved.workspace_dir,
                            plan=prepared.plan,
                            input_values=prepared.values,
                            response_generator=response_generator,
                            tool_runtime=prepared.runtime,
                            action_generator=action_generator,
                            execution_context=prepared.execution_context,
                            on_event=emit,
                            run_id=receipt.run_id,
                        )

                    try:
                        from ..workflow_trace.canonical import (
                            project_prompt_workflow_trace,
                        )
                        from ..workflow_execution_continuation import input_identities

                        return await record_workflow_run(
                            service=self.application.workspace,
                            workspace_dir=resolved.workspace_dir,
                            workspace_id=process.workspace_id,
                            source_path=process.source_path,
                            source_digest=process.source_digest,
                            execute=execute,
                            execution_context=prepared.execution_context,
                            run_id=receipt.run_id,
                            run_log_path=receipt.run_log_path,
                            cancellation_status=owned.cancellation_outcome,
                            trace_definition=project_prompt_workflow_trace(
                                prepared.plan
                            ),
                            trace_inputs=input_identities(prepared.values),
                            required_step_ids=[step.id for step in prepared.plan.steps],
                        )
                    finally:
                        published.set()
                        if prepared.runtime is not None:
                            await prepared.runtime.close()

                owned.task = asyncio.create_task(
                    run(), name=f"wright-process:{receipt.run_id}"
                )
                self._owned[receipt.run_id] = owned

                def finished(task):
                    if self._owned.get(receipt.run_id) is owned:
                        self._owned.pop(receipt.run_id, None)
                    if not task.cancelled():
                        task.exception()  # Consume diagnostics; the recorder retains failure.

                owned.task.add_done_callback(finished)
                transferred = True
                # Wait only for the initial recorder publication, not model/tool
                # execution. The task is already retained, so losing this start
                # observer cannot interrupt execution or free its runtime.
                try:
                    async with asyncio.timeout(6):
                        await published.wait()
                except TimeoutError:
                    pass  # The durable accepted receipt still requires reconciliation.
                return receipt
            finally:
                if not transferred and prepared.runtime is not None:
                    await prepared.runtime.close()

    @traced("process.interface.run.respond")
    async def respond(
        self,
        scope,
        process,
        checkpoint_id,
        request_id,
        *,
        expected_subject_digest,
        value,
        response_generator,
        gateway=None,
        session_id="",
        action_generator=None,
        auto=False,
    ):
        """Accept a declared answer and own its same-run continuation task.

        Checkpoint/run are derived from the authenticated process scope. The
        ordinary actor is its principal; an explicit automatic test response
        derives its actor from the exact frozen integration enrollment.
        A retained answer is evidence, never permission to replay a claimed segment.
        """
        from .interactions import prepare_input_continuation

        scope.require(process, "process.respond")
        if type(auto) is not bool:
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "Automatic response must be a boolean.",
                "Use an explicit test response or the ordinary authenticated input path.",
            )
        checkpoint_id = TypeAdapter(Identifier).validate_python(checkpoint_id)
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        expected_subject_digest = TypeAdapter(Digest).validate_python(
            expected_subject_digest
        )
        async with self._allocation:
            checkpoint = self.application.human_inputs.repository.get(checkpoint_id)
            if checkpoint is None or (
                checkpoint.workspace_id != process.workspace_id
                or checkpoint.workflow_id != process.source_path
                or checkpoint.checkpoint_kind != "input"
            ):
                raise ProcessInterfaceError(
                    "SCOPE_DENIED",
                    "The declared input is not available in this process.",
                    "Attach this process's exact run and checkpoint.",
                )
            root, receipt = self._receipt(
                scope, process, checkpoint.run_id, "process.respond"
            )
            checkpoint = self.application.human_inputs.get(
                checkpoint_id,
                workspace_id=process.workspace_id,
                run_id=receipt.run_id,
            )
            if checkpoint.subject_digest != expected_subject_digest:
                raise ProcessInterfaceError(
                    "SUBJECT_STALE",
                    "This answer belongs to an earlier input subject.",
                    "Refresh the run and answer its current declared input.",
                )
            record, view = await asyncio.to_thread(
                self._record, scope, process, receipt.run_id
            )
            actor = scope.principal_id
            reason = "Response to declared process input"
            if auto:
                from ..workflow_integration_policy import WorkflowIntegrationPolicyError

                context = checkpoint.continuation.get("execution_context", {}) or {}
                policies = getattr(
                    self.application.workspace, "workflow_integration_policies", None
                )
                if policies is None or not context.get("integration_policy_digest"):
                    raise ProcessInterfaceError(
                        "SCOPE_DENIED",
                        "This run has no enrolled automatic-input authority.",
                        "Use an authenticated response or enroll an exact isolated test process.",
                    )
                try:
                    authority = policies.authorize_input_response(
                        context["integration_policy_digest"],
                        workspace_id=process.workspace_id,
                        checkpoint=checkpoint,
                        expected_subject_digest=expected_subject_digest,
                    )
                except WorkflowIntegrationPolicyError as error:
                    raise ProcessInterfaceError(
                        "SCOPE_DENIED",
                        "Automatic input is not authorized for this exact test subject.",
                        "Inspect the local test enrollment and the current declared input.",
                    ) from error
                actor, reason = authority["actor"], authority["reason"]
            prior = None
            if checkpoint.continuation.get("response_id") is not None:
                checkpoint, prior, _ = self.application.human_inputs.respond(
                    checkpoint_id,
                    workspace_id=process.workspace_id,
                    run_id=receipt.run_id,
                    expected_subject_digest=expected_subject_digest,
                    value=value,
                    actor=actor,
                    reason=reason,
                    request_id=request_id,
                    integration_test=actor.startswith("integration_test:"),
                )
                claim = record.get("resume_segments", {}).get(checkpoint_id)
                owned = self._owned.get(receipt.run_id)
                if claim and claim.get("subject_digest") != checkpoint.subject_digest:
                    raise ProcessInterfaceError(
                        "SUBJECT_STALE",
                        "The saved continuation claim belongs to another input subject.",
                        "Inspect this run's exact response and continuation evidence.",
                    )
                if claim and claim.get("state") == "completed":
                    return prior
                if (
                    self.is_live(receipt.run_id)
                    and owned.checkpoint_id == checkpoint_id
                ):
                    return prior
                if claim:
                    raise ProcessInterfaceError(
                        "OUTCOME_UNKNOWN",
                        "This input continuation already began and cannot be replayed.",
                        "Inspect the saved run and reconcile unfinished work.",
                    )
            reference = (record.get("result") or {}).get("input_checkpoint") or {}
            if (
                view["status"] != "waiting_human"
                or reference.get("checkpoint_id") != checkpoint_id
            ):
                raise ProcessInterfaceError(
                    "ACTION_NOT_PERMITTED",
                    "This run is not waiting for that input.",
                    "Inspect its current checkpoint and recorded outcome.",
                )
            if self.is_live(receipt.run_id):
                raise ProcessInterfaceError(
                    "ACTION_NOT_PERMITTED",
                    "The run is already executing another segment.",
                    "Follow the current run; do not submit another continuation.",
                )
            if (
                self._closed
                or sum(self.is_live(key) for key in self._owned) >= self.maximum_active
            ):
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "The local runtime cannot continue this run yet.",
                    "Wait for runtime capacity and retry this exact response request.",
                )
            resolved = await self.application.resolve_process(
                scope, process, operation="process.respond"
            )

            def available_gateway():
                if gateway is None:
                    raise ProcessInterfaceError(
                        "CAPABILITY_UNAVAILABLE",
                        "The configured process tools are unavailable.",
                        "Reconnect the required providers before continuing.",
                    )
                return gateway() if callable(gateway) else gateway

            prepared = await prepare_input_continuation(
                self.application,
                resolved,
                checkpoint,
                gateway=available_gateway,
                session_id=session_id,
            )
            transferred = False
            try:
                if self._closed:
                    raise ProcessInterfaceError(
                        "CAPABILITY_UNAVAILABLE",
                        "The runtime is shutting down.",
                        "Reconnect and retry this exact response request.",
                    )
                checkpoint, answer, _ = self.application.human_inputs.respond(
                    checkpoint_id,
                    workspace_id=process.workspace_id,
                    run_id=receipt.run_id,
                    expected_subject_digest=expected_subject_digest,
                    value=value,
                    actor=actor,
                    reason=reason,
                    request_id=request_id,
                    integration_test=actor.startswith("integration_test:"),
                )
                if checkpoint.state == "pending":
                    checkpoint = self.application.human_inputs.consume(
                        checkpoint_id,
                        workspace_id=process.workspace_id,
                        run_id=receipt.run_id,
                        response_id=answer.response_id,
                    )
                owned = _OwnedRun(
                    checkpoint_id=checkpoint_id,
                    tool_runtime=prepared.runtime,
                    local_cancel_supported=not any(
                        step.tool_name
                        or step.agent_task
                        or step.external_action
                        or step.cad
                        or step.application
                        for step in prepared.plan.steps[
                            checkpoint.continuation["next_step_index"] :
                        ]
                    ),
                )

                async def run():
                    async def execute(emit):
                        owned.emit = emit
                        return await execute_prompt_workflow(
                            service=self.application.workspace,
                            workspace_dir=root,
                            plan=prepared.plan,
                            input_values=prepared.values,
                            response_generator=response_generator,
                            tool_runtime=prepared.runtime,
                            action_generator=action_generator,
                            execution_context=prepared.execution_context,
                            on_event=emit,
                            run_id=receipt.run_id,
                            continuation=checkpoint.continuation,
                            completed_checkpoint=asdict(checkpoint),
                        )

                    try:
                        return await record_workflow_resume(
                            service=self.application.workspace,
                            workspace_dir=root,
                            workspace_id=process.workspace_id,
                            checkpoint=checkpoint,
                            execute=execute,
                            cancellation_status=owned.cancellation_outcome,
                        )
                    finally:
                        if prepared.runtime is not None:
                            await prepared.runtime.close()

                # No await between durable response consumption and task ownership.
                owned.task = asyncio.create_task(
                    run(), name=f"wright-process:{receipt.run_id}:{checkpoint_id}"
                )
                self._owned[receipt.run_id] = owned
                transferred = True

                def finished(task):
                    if self._owned.get(receipt.run_id) is owned:
                        self._owned.pop(receipt.run_id, None)
                    if not task.cancelled():
                        task.exception()

                owned.task.add_done_callback(finished)
                return answer
            finally:
                if not transferred and prepared.runtime is not None:
                    await prepared.runtime.close()

    @traced("process.interface.run.action")
    async def request_action(
        self,
        scope,
        process,
        action_id,
        request_id,
        *,
        expected_subject_digest,
        response_generator,
        gateway=None,
        session_id="",
        action_generator=None,
    ):
        """Own an exact approval continuation; observation never owns dispatch.

        The canonical approval lease, consume store, gateway and recorder retain
        authority. This adapter allocates their task and returns its durable request
        identity; it does not execute a graph or infer an external outcome.
        """
        from ..workflow_approval_execution import (
            inspect_workflow_approval,
            resume_workflow_approval,
        )
        from ..workflow_external_actions import WorkflowExternalActionError
        from .decisions import decision_error

        scope.require(process, "process.action")
        scope.require(process, "process.read")
        action_id = TypeAdapter(Identifier).validate_python(action_id)
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        expected_subject_digest = TypeAdapter(Digest).validate_python(
            expected_subject_digest
        )
        if not action_id.startswith("continue-") or len(action_id) <= len("continue-"):
            raise ProcessInterfaceError(
                "ACTION_NOT_PERMITTED",
                "This action has no declared continuation.",
                "Choose the exact permitted action in this process's current run.",
            )
        checkpoint_id = action_id[len("continue-") :]
        intent = {
            "request_id": request_id,
            "principal_id": scope.principal_id,
            "subject_digest": expected_subject_digest,
            "action_id": action_id,
        }
        try:
            async with self._allocation:
                await self.application.resolve_process(
                    scope, process, operation="process.action"
                )
                checkpoint = (
                    self.application.workspace.workflow_external_actions.lookup(
                        checkpoint_id
                    )
                )
                if (
                    checkpoint.workspace_id != process.workspace_id
                    or checkpoint.workflow_id != process.source_path
                    or checkpoint.checkpoint_kind != "approval"
                    or checkpoint.subject.get("definition_digest")
                    != process.source_digest
                ):
                    raise ProcessInterfaceError(
                        "SCOPE_DENIED",
                        "This action does not belong to this exact process.",
                        "Open its registered process and recorded checkpoint.",
                    )
                if checkpoint.subject_digest != expected_subject_digest:
                    raise ProcessInterfaceError(
                        "SUBJECT_STALE",
                        "The reviewed action subject changed.",
                        "Refresh the exact checkpoint and its recorded evidence.",
                    )
                root, receipt = self._receipt(
                    scope, process, checkpoint.run_id, "process.action"
                )
                record, view = await asyncio.to_thread(
                    self._record, scope, process, receipt.run_id
                )
                reference = view.get("approval") or {}
                if (
                    reference.get("checkpoint_id") != checkpoint_id
                    or reference.get("subject_digest") != expected_subject_digest
                ):
                    raise ProcessInterfaceError(
                        "SCOPE_DENIED",
                        "This is not the recorded run's exact action.",
                        "Open its current saved checkpoint before continuing.",
                    )
                owned = self._owned.get(receipt.run_id)
                if self.is_live(receipt.run_id):
                    if (
                        owned.checkpoint_id != checkpoint_id
                        or owned.action_request != intent
                    ):
                        raise ProcessInterfaceError(
                            "REQUEST_CONFLICT",
                            "This run already owns another continuation request.",
                            "Follow that request and its actual recorded outcome.",
                        )
                else:
                    claim = record.get("resume_segments", {}).get(checkpoint_id)
                    if checkpoint.state == "consumed":
                        prior = checkpoint.external_action or {}
                        if (
                            prior.get("action_id") != request_id
                            or prior.get("principal_id") != scope.principal_id
                        ):
                            raise ProcessInterfaceError(
                                "REQUEST_CONFLICT",
                                "A different action request already consumed this checkpoint.",
                                "Inspect the original request; it cannot be submitted as another identity.",
                            )
                        if (
                            claim
                            and claim.get("subject_digest") != expected_subject_digest
                        ):
                            raise ProcessInterfaceError(
                                "SUBJECT_STALE",
                                "The continuation claim belongs to another subject.",
                                "Inspect this run's exact action and continuation evidence.",
                            )
                        if claim and claim.get("state") == "completed":
                            return await self.application.get_snapshot(
                                scope,
                                process,
                                run_id=receipt.run_id,
                                gateway=gateway,
                                session_id=session_id,
                            )
                        if (
                            claim
                            or prior.get("outcome") != "dispatched"
                            or (
                                checkpoint.action_kind == "mcp-operation"
                                and not prior.get("evidence", {}).get(
                                    "delivery_completed"
                                )
                            )
                        ):
                            raise ProcessInterfaceError(
                                "OUTCOME_UNKNOWN",
                                "This consumed action cannot be replayed.",
                                "Reconcile its submission and unfinished continuation before another action.",
                            )
                    else:
                        inspection = await inspect_workflow_approval(
                            service=self.application.workspace,
                            workspace_id=process.workspace_id,
                            workspace_dir=root,
                            checkpoint=checkpoint,
                            subject_digest=expected_subject_digest,
                            gateway=gateway,
                            session_id=session_id,
                        )
                        if not inspection.can_resume:
                            raise ProcessInterfaceError(
                                "ACTION_NOT_PERMITTED",
                                "This action is not approved and ready to continue.",
                                inspection.resume_correction
                                or "Complete its declared review and inspect the current evidence.",
                            )
                    if (
                        self._closed
                        or sum(self.is_live(key) for key in self._owned)
                        >= self.maximum_active
                    ):
                        raise ProcessInterfaceError(
                            "CAPABILITY_UNAVAILABLE",
                            "The runtime cannot continue this action yet.",
                            "Wait for capacity, then reconcile this same request.",
                        )
                    owned = _OwnedRun(
                        checkpoint_id=checkpoint_id,
                        action_request=intent,
                        action_ready=asyncio.Event(),
                    )

                    def runtime_ready(runtime, emit, local_cancel_supported):
                        owned.tool_runtime = runtime
                        owned.emit = emit
                        owned.local_cancel_supported = local_cancel_supported

                    def authorized(current):
                        action = current.external_action or {}
                        if (
                            action.get("action_id") != request_id
                            or action.get("principal_id") != scope.principal_id
                        ):
                            raise ValueError(
                                "The consumed action does not match its supervised request"
                            )
                        owned.action_ready.set()

                    async def run():
                        return await resume_workflow_approval(
                            service=self.application.workspace,
                            workspace_id=process.workspace_id,
                            workspace_dir=root,
                            checkpoint=checkpoint,
                            subject_digest=expected_subject_digest,
                            request_id=request_id,
                            principal_id=scope.principal_id,
                            gateway=gateway,
                            session_id=session_id,
                            response_generator=response_generator,
                            action_generator=action_generator,
                            on_runtime=runtime_ready,
                            on_authorized=authorized,
                            cancellation_status=owned.cancellation_outcome,
                        )

                    # The task is registered before the first scheduling point.
                    owned.task = asyncio.create_task(
                        run(),
                        name=f"wright-process-action:{receipt.run_id}:{checkpoint_id}",
                    )
                    self._owned[receipt.run_id] = owned

                    def finished(task):
                        if self._owned.get(receipt.run_id) is owned:
                            self._owned.pop(receipt.run_id, None)
                        if not task.cancelled():
                            task.exception()

                    owned.task.add_done_callback(finished)
            waiter = asyncio.create_task(owned.action_ready.wait())
            try:
                await asyncio.wait(
                    (owned.task, waiter), timeout=6, return_when=asyncio.FIRST_COMPLETED
                )
                if not owned.action_ready.is_set():
                    if owned.task.done():
                        await asyncio.shield(owned.task)
                    raise ProcessInterfaceError(
                        "OUTCOME_UNKNOWN",
                        "The action request is still awaiting durable confirmation.",
                        "Reconcile this same request; do not submit a new action identity.",
                    )
            finally:
                waiter.cancel()
            return await self.application.get_snapshot(
                scope,
                process,
                run_id=receipt.run_id,
                gateway=gateway,
                session_id=session_id,
            )
        except (WorkflowExternalActionError, WorkflowSourceExecutionError) as error:
            raise decision_error(error) from error

    @traced("process.interface.run.legacy.start")
    async def start_legacy(self, scope, process, request_id, **execution):
        """Freeze source defaults once; delegate the legacy transport to start.

        The separate preparation lock makes concurrent legacy requests share
        their first snapshot identity. Native starts already carry a frozen ID.
        No executor, source edit or runtime ownership exists in the adapter.
        """
        scope.require(process, "process.start")
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        async with self._legacy_preparation:
            try:
                previous = self.application.inputs.start_receipt(
                    scope.principal_id, process, request_id
                )
            except KeyError:
                previous = None
            if previous is not None:
                frozen = self.application._input_snapshot(
                    previous.process, previous.input_snapshot_id
                )
            else:
                root = self._root(scope, process, "process.start")
                await qualify_workflow_run_origin(
                    service=self.application.workspace,
                    workspace_dir=root,
                    workspace_id=process.workspace_id,
                    source_path=process.source_path,
                    source_digest=process.source_digest,
                    integration_policy_digest=execution.get(
                        "integration_policy_digest"
                    ),
                )
                prepared = await self.application.set_inputs(
                    scope,
                    process,
                    gateway=execution.get("gateway"),
                    session_id=execution.get("session_id", ""),
                )
                frozen = prepared.snapshot
            return await self.start(
                scope,
                process,
                frozen.snapshot_id,
                request_id,
                expected_input_digest=frozen.digest,
                **execution,
            )

    @traced("process.interface.run.legacy.resume")
    async def resume_legacy_approval(
        self,
        scope,
        process,
        checkpoint,
        request_id,
        *,
        expected_subject_digest,
        response_generator,
        gateway=None,
        session_id="",
        action_generator=None,
    ):
        """Keep the compatibility response while supervising its continuation.

        Canonical approval/consume and resume records still decide authority and
        cached segment results, including historical runs without start receipts.
        Disconnecting this observer cannot interrupt the registered execution.
        """
        from ..workflow_approval_execution import resume_workflow_approval

        scope.require(process, "process.action")
        scope.require_run(checkpoint.run_id)
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        expected_subject_digest = TypeAdapter(Digest).validate_python(
            expected_subject_digest
        )
        root = self._root(scope, process, "process.action")
        if (
            checkpoint.workspace_id != process.workspace_id
            or checkpoint.workflow_id != process.source_path
            or checkpoint.checkpoint_kind != "approval"
            or checkpoint.subject.get("definition_digest") != process.source_digest
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This continuation belongs to another process.",
                "Open the exact saved process and its checkpoint.",
            )
        if checkpoint.subject_digest != expected_subject_digest:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The reviewed continuation subject changed.",
                "Refresh its exact checkpoint before continuing.",
            )
        intent = {
            "request_id": request_id,
            "principal_id": scope.principal_id,
            "subject_digest": expected_subject_digest,
            "action_id": f"continue-{checkpoint.checkpoint_id}",
        }
        async with self._allocation:
            owned = self._owned.get(checkpoint.run_id)
            if self.is_live(checkpoint.run_id):
                if (
                    owned.checkpoint_id != checkpoint.checkpoint_id
                    or owned.action_request != intent
                ):
                    raise ProcessInterfaceError(
                        "REQUEST_CONFLICT",
                        "This run already owns another continuation request.",
                        "Follow the original request and its recorded outcome.",
                    )
            else:
                if (
                    self._closed
                    or sum(self.is_live(key) for key in self._owned)
                    >= self.maximum_active
                ):
                    raise ProcessInterfaceError(
                        "CAPABILITY_UNAVAILABLE",
                        "The runtime cannot continue this action yet.",
                        "Wait for capacity, then reconcile this same request.",
                    )
                current = self.application.workspace.workflow_external_actions.lookup(
                    checkpoint.checkpoint_id
                )
                if current.state == "consumed":
                    prior = current.external_action or {}
                    if prior.get("action_id") != request_id or prior.get(
                        "principal_id"
                    ) not in {None, scope.principal_id}:
                        raise ProcessInterfaceError(
                            "REQUEST_CONFLICT",
                            "A different request already consumed this checkpoint.",
                            "Inspect the original request; do not submit another identity.",
                        )
                owned = _OwnedRun(
                    checkpoint_id=checkpoint.checkpoint_id,
                    action_request=intent,
                    action_ready=asyncio.Event(),
                )

                def runtime_ready(runtime, emit, local_cancel_supported):
                    owned.tool_runtime = runtime
                    owned.emit = emit
                    owned.local_cancel_supported = local_cancel_supported

                def authorized(current):
                    owned.action_ready.set()

                async def execute():
                    return await resume_workflow_approval(
                        service=self.application.workspace,
                        workspace_id=process.workspace_id,
                        workspace_dir=root,
                        checkpoint=current,
                        subject_digest=expected_subject_digest,
                        request_id=request_id,
                        principal_id=scope.principal_id,
                        gateway=gateway,
                        session_id=session_id,
                        response_generator=response_generator,
                        action_generator=action_generator,
                        on_runtime=runtime_ready,
                        on_authorized=authorized,
                        cancellation_status=owned.cancellation_outcome,
                    )

                owned.task = asyncio.create_task(
                    execute(),
                    name=f"wright-process-action:{checkpoint.run_id}:{checkpoint.checkpoint_id}",
                )
                self._owned[checkpoint.run_id] = owned

                def finished(task):
                    if self._owned.get(checkpoint.run_id) is owned:
                        self._owned.pop(checkpoint.run_id, None)
                    if not task.cancelled():
                        task.exception()

                owned.task.add_done_callback(finished)
        return await asyncio.shield(owned.task)

    @traced("process.interface.run.events")
    async def events(self, scope, process, run_id, *, cursor=None, limit=256):
        """Read bounded progress from the recorder; subscription starts no work.

        The cursor binds this actor, exact process/run and consumed history.
        It remains valid when new events append, but fails on altered history.
        Results, tool arguments, prompts and credentials are read through their
        owning authorized services, never broadcast as progress events.
        """
        page = await self._event_page(
            scope, process, run_id, cursor=cursor, limit=limit
        )
        return ProcessRunEventPage.model_validate(page).model_dump(
            mode="json", exclude_none=True
        )

    async def legacy_events(self, scope, process, run_id, *, cursor=None):
        """Compatibility progress payloads for the authorized source-run view."""
        return await self._event_page(
            scope, process, run_id, cursor=cursor, limit=256, legacy=True
        )

    async def _event_page(self, scope, process, run_id, *, cursor, limit, legacy=False):
        if type(limit) is not int or not 1 <= limit <= 256:
            raise ValueError("Event pages require a limit between 1 and 256")
        record, view = await asyncio.to_thread(self._record, scope, process, run_id)
        history = record.get("events", [])

        def identity(offset):
            return canonical_digest(
                {
                    "principal": scope.principal_id,
                    "process": process,
                    "run_id": run_id,
                    "history": history[:offset],
                }
            )

        offset = 0
        if cursor is not None:
            try:
                version, number, anchor = cursor.split(".")
                offset = int(number)
                if (
                    version != "pe1"
                    or number != str(offset)
                    or not 0 <= offset <= len(history)
                    or anchor != identity(offset)
                ):
                    raise ValueError("Unverifiable history cursor")
            except (AttributeError, ValueError):
                raise ProcessInterfaceError(
                    "SUBJECT_STALE",
                    "This progress cursor no longer matches the run.",
                    "Read its current snapshot and attach without the old cursor.",
                ) from None
        projected = []
        size = 0
        for index, event in enumerate(history[offset : offset + limit], offset + 1):
            item = {"sequence": index}
            for key in (
                "kind",
                "at",
                "task_id",
                "task_title",
                "step_id",
                "execution_kind",
            ):
                value = event.get(key)
                if isinstance(value, str):
                    item[key] = value[:256]
            if legacy:
                candidate = dict(event)
                if (
                    len(json.dumps(candidate, ensure_ascii=False).encode("utf-8"))
                    <= 60_000
                ):
                    item = candidate
                else:
                    item.update(
                        details_truncated=True,
                        event_details_ref={
                            "run_id": run_id,
                            "run_log_path": view["path"],
                            "sequence": index,
                        },
                    )
            if not legacy:
                # The page contract includes defaulted null fields in its size
                # check. Budget that validated shape, not the smaller sparse
                # projection, so long histories paginate before the limit.
                item = ProcessRunEvent.model_validate(item).model_dump(mode="json")
            size += len(json.dumps(item, ensure_ascii=False).encode("utf-8"))
            if size > 60_000:
                break
            projected.append(item)
        offset += len(projected)
        from .projection import _STATES

        return {
            "run_id": run_id,
            "state": _STATES.get(view["status"], "reconciliation_required"),
            "events": projected,
            "cursor": f"pe1.{offset}.{identity(offset)}",
            "has_more": offset < len(history),
            "following": self.is_live(run_id),
        }

    @traced("process.interface.run.wait")
    async def wait(self, scope, process, run_id):
        self._receipt(scope, process, run_id)
        owned = self._owned.get(run_id)
        if owned is not None:
            try:
                await asyncio.shield(owned.task)
            except asyncio.CancelledError:
                if asyncio.current_task().cancelling():
                    raise  # Only this observer was cancelled.
            except Exception:
                pass  # The canonical failure record is the returned authority.
        record, view = await asyncio.to_thread(self._record, scope, process, run_id)
        return {
            **(record.get("result") or {}),
            "run_id": run_id,
            "status": view["status"],
            "run_log_path": view["path"],
            **(
                {
                    "error": record["error"],
                    "code": record.get("code", "EXECUTION_FAILED"),
                    "correction": record.get("correction")
                    or "Open this recorded run's details before starting another attempt.",
                }
                if record.get("error")
                else {}
            ),
        }

    @traced("process.interface.run.cancel")
    async def cancel(self, scope, process, run_id, request_id):
        self._receipt(scope, process, run_id, "process.cancel")
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        if len(self._cancellations) >= 64:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "The cancellation service is at capacity.",
                "Attach to the current run and wait for the pending requests.",
            )
        task = asyncio.create_task(
            self._cancel(scope, process, run_id, request_id),
            name=f"wright-process-cancel:{run_id}:{request_id}",
        )
        self._cancellations.add(task)

        def finished(completed):
            self._cancellations.discard(completed)
            if not completed.cancelled():
                completed.exception()

        task.add_done_callback(finished)
        return await asyncio.shield(task)

    def cancellation_capability(self, run_id):
        """Presentation hint only; cancel rechecks the exact active provider binding."""
        owned = self._owned.get(run_id)
        if not owned or owned.task is None or owned.task.done():
            return (
                False,
                "This runtime has no active execution to cancel. Inspect the recorded outcome.",
            )
        if owned.emit is None:
            return (
                False,
                "Execution is preparing. Cancellation is unavailable until its active operation is identified.",
            )
        if owned.cancel_request:
            return (
                False,
                "Cancellation was requested. Follow the identified operation's actual outcome.",
            )
        if owned.local_cancel_supported:
            return True, ""
        from ..workflow_async_operations import operation_cancellation

        if operation_cancellation(owned.tool_runtime) is not None:
            return True, ""
        return (
            False,
            "The active provider operation has no currently qualified cancellation capability.",
        )

    async def _cancel(self, scope, process, run_id, request_id):
        self._receipt(scope, process, run_id, "process.cancel")
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        async with self._commands:
            record, _ = await asyncio.to_thread(self._record, scope, process, run_id)
            previous = next(
                (
                    event
                    for event in record.get("events", [])
                    if event.get("kind") == "cancellation_requested"
                    and event.get("request_id") == request_id
                    and event.get("principal_id") == scope.principal_id
                ),
                None,
            )
            if previous:
                return {
                    "request_id": request_id,
                    "run_id": run_id,
                    "state": "cancellation_requested",
                }
            owned = self._owned.get(run_id)
            if not owned or owned.task is None or owned.task.done():
                raise ProcessInterfaceError(
                    "ACTION_NOT_PERMITTED",
                    "This runtime has no active execution to cancel.",
                    "Inspect the actual run outcome; an unknown owner needs reconciliation.",
                )
            if owned.emit is None:
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "Execution is preparing; its cancellation capability is not established yet.",
                    "Follow the same run until its active operation and permitted actions are available.",
                )
            target = None
            if not owned.local_cancel_supported:
                from ..workflow_async_operations import operation_cancellation

                target = operation_cancellation(owned.tool_runtime, reserve=True)
                if target is None:
                    raise ProcessInterfaceError(
                        "CAPABILITY_UNAVAILABLE",
                        "This operation has no currently qualified cancellation capability.",
                        "Inspect its provider operation and reconcile its actual outcome; local task cancellation cannot establish an external outcome.",
                    )
            result = {
                "request_id": request_id,
                "run_id": run_id,
                "state": "cancellation_requested",
            }
            try:
                await owned.emit(
                    {
                        "kind": "cancellation_requested",
                        "at": datetime.now(timezone.utc).isoformat(),
                        "request_id": request_id,
                        "principal_id": scope.principal_id,
                        "run_id": run_id,
                        **(
                            {
                                "operation_id": target.operation_id,
                                "task_id": target.step_id,
                                "provider_binding": target.provider_binding,
                            }
                            if target
                            else {}
                        ),
                    }
                )
            except BaseException as error:
                if target:
                    target.publication_unknown()
                if not isinstance(error, Exception):
                    raise
                raise ProcessInterfaceError(
                    "OUTCOME_UNKNOWN",
                    "Wright could not confirm publication of this cancellation request.",
                    "Attach the exact run and reconcile its recorded request and provider outcome before another action.",
                ) from error
            owned.cancel_request = result
            owned.cancel_target = target
            if target:
                target.activate()
            else:
                owned.task.cancel()
            return result

    async def close(self):
        self._closed = True
        pending_commands = set()
        if self._cancellations:
            _, pending_commands = await asyncio.wait(
                tuple(self._cancellations), timeout=6
            )
        tasks = tuple(
            owned.task
            for owned in self._owned.values()
            if owned.task and not owned.task.done()
        )
        for task in tasks:
            if not task.cancelling():
                task.cancel()
        if tasks:
            _, pending = await asyncio.wait(tasks, timeout=6)
            if pending or pending_commands:
                raise ProcessInterfaceError(
                    "OUTCOME_UNKNOWN",
                    "A run did not finish runtime shutdown within its deadline.",
                    "Retain its identity and reconcile its actual operation outcome.",
                )
        elif pending_commands:
            raise ProcessInterfaceError(
                "OUTCOME_UNKNOWN",
                "Cancellation did not finish before runtime shutdown.",
                "Reconcile the retained command and run identities.",
            )
