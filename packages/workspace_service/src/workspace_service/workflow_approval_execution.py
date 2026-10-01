"""Canonical approval decisions and durable, same-run continuation dispatch.

Fixed local review, enrolled test handoff and qualified approved MCP operations
reuse one-shot consumption. No transport is inferred from a tool name or prose.
"""

from dataclasses import asdict, dataclass
import asyncio
import hashlib
import json

from data_vault.workflow_continuation_repository import WorkflowContinuationCheckpoint

from .workflow_execution_continuation import input_identities
from .workflow_external_actions import (
    WorkflowExternalActionError,
    approval_subject_digest,
)
from .workflow_integration_policy import (
    LOCAL_REVIEW_BINDING,
    LOCAL_REVIEW_DESTINATION,
    TEST_HANDOFF_BINDING,
)
from .workflow_mcp_execution import WorkflowMcpRuntime
from .workflow_resource_lease import ApplicationLease
from .workflow_run_record import (
    record_workflow_approval_transition,
    record_workflow_resume,
)
from .workflow_source_execution import (
    WorkflowSourceExecutionError,
    prepare_prompt_workflow,
    execute_prompt_workflow,
    _resolved_approval_settings,
    _error,
)
from .workspace_path import WorkspacePath


def _lease(workspace_id, checkpoint):
    return ApplicationLease(
        f"workflow-approval-execution:{workspace_id}:{checkpoint.run_id}"
    )


def _current(service, checkpoint, workspace_id, subject_digest):
    current = service.workflow_external_actions.get(
        checkpoint.checkpoint_id,
        workspace_id=workspace_id,
        run_id=checkpoint.run_id,
    )
    if (
        current.subject_digest != subject_digest
        or approval_subject_digest(current.subject) != subject_digest
    ):
        raise WorkflowExternalActionError(
            "approval_stale", "The approval subject changed"
        )
    state = current.continuation
    if (
        type(state.get("schema_version")) is not int
        or state["schema_version"] not in {2, 3}
        or (
            state["schema_version"] == 3
            and (
                state.get("checkpoint_kind") != "approval"
                or state.get("response_id") is not None
                or state.get("response_digest") is not None
            )
        )
        or state.get("workflow_path") != current.workflow_id
        or state.get("run_id") != current.run_id
    ):
        raise _error(
            "WORKFLOW_CONTINUATION_STALE",
            "The checkpoint has no matching canonical continuation.",
            "Inspect the persisted run before continuing.",
        )
    return current


async def _prepare(
    *, service, workspace_id, workspace_dir, checkpoint, gateway, session_id
):
    runtime = None

    def get_runtime():
        nonlocal runtime
        if runtime is None:
            if gateway is None:
                raise _error(
                    "WORKFLOW_TOOL_UNAVAILABLE",
                    "Workflow tools are unavailable.",
                    "Connect the enrolled MCP servers before continuing.",
                )
            runtime = WorkflowMcpRuntime(
                gateway, workspace_id=workspace_id, session_id=session_id
            )
            context = checkpoint.continuation.get("execution_context") or {}
            if context.get("integration_policy_digest"):
                grant = service.workflow_integration_policies.get(
                    context["integration_policy_digest"]
                )
                runtime.restrict_to(grant["allowed_tools"])
        return runtime

    try:
        state = checkpoint.continuation
        overlay = {}
        if state.get("schema_version") == 3:
            try:
                frozen = service.process_interfaces.inputs.get_snapshot(
                    workspace_id, state["input_snapshot_id"]
                )
                if frozen.digest != state.get("input_digest") or (
                    frozen.process.source_path != checkpoint.workflow_id
                    or frozen.process.source_digest
                    != checkpoint.subject["definition_digest"]
                ):
                    raise ValueError("The frozen approval inputs changed")
                overlay = {"workspace_id": workspace_id, "input_snapshot": frozen}
            except (AttributeError, KeyError, ValueError, TypeError) as error:
                raise _error(
                    "WORKFLOW_CONTINUATION_STALE",
                    "The approval has no matching frozen input snapshot.",
                    "Inspect the saved run inputs before continuing.",
                ) from error
        plan, inputs = await prepare_prompt_workflow(
            service=service,
            workspace_dir=workspace_dir,
            path=checkpoint.workflow_id,
            expected_digest=checkpoint.subject["definition_digest"],
            tool_runtime=get_runtime,
            **overlay,
        )
        state = checkpoint.continuation
        cursor = state.get("next_step_index")
        settings = None
        if type(cursor) is int and 0 <= cursor < len(plan.steps):
            settings = await _resolved_approval_settings(
                pending_action=plan.steps[cursor],
                plan=plan,
                workspace_dir=workspace_dir,
                service=service,
                continuation=state,
            )
        if (
            type(cursor) is not int
            or not 0 <= cursor < len(plan.steps)
            or plan.steps[cursor].id != checkpoint.step_id
            or not plan.steps[cursor].external_action
            or state.get("input_identities") != input_identities(inputs)
            or sorted(input_identities(inputs).values())
            != checkpoint.subject.get("input_digests")
            or any(
                checkpoint.subject.get(key) != plan.steps[cursor].external_action[key]
                for key in ("binding", "destination", "action")
            )
            or checkpoint.subject.get("settings") != settings
        ):
            raise WorkflowExternalActionError(
                "approval_stale", "The canonical inputs or approval action changed"
            )
        for key in ("input_files", "artifact_files"):
            for item in state.get(key, []):
                # Path confinement is supplied by the same workspace file API
                # used during preparation and execution.
                try:
                    WorkspacePath(workspace_dir).resolve(item["path"], must_exist=True)
                    identity = await service.files.hash_reference(
                        workspace_dir, item["path"]
                    )
                except (OSError, ValueError) as error:
                    raise WorkflowExternalActionError(
                        "approval_stale", "A reviewed input or artifact is unavailable"
                    ) from error
                if identity != item["sha256"]:
                    raise WorkflowExternalActionError(
                        "approval_stale", "A reviewed input or artifact changed"
                    )
        context = state.get("execution_context")
        if context:
            policy_digest = context.get("integration_policy_digest")
            if not policy_digest:
                raise _error(
                    "WORKFLOW_INTEGRATION_POLICY_INVALID",
                    "The execution context has no enrolled policy.",
                    "Re-enroll this exact integration run.",
                )
            grant = service.workflow_integration_policies.get(policy_digest)
            if grant["allowed_tools"] and runtime is None:
                get_runtime()
            current_context = await service.workflow_integration_policies.authorize(
                policy_digest,
                workspace_id=workspace_id,
                workspace_dir=workspace_dir,
                source_path=checkpoint.workflow_id,
                source_digest=plan.definition_digest,
                plan=plan,
                tool_runtime=runtime,
                files=service.files,
            )
            if current_context != context:
                raise _error(
                    "WORKFLOW_INTEGRATION_POLICY_INVALID",
                    "The immutable run policy context changed.",
                    "Inspect enrollment before continuing this run.",
                )
            if runtime is not None:
                from .workflow_integration_document_write import (
                    bind_integration_document_writes,
                )

                bind_integration_document_writes(
                    service=service,
                    runtime=runtime,
                    context=context,
                    plan=plan,
                    workspace_dir=workspace_dir,
                    workspace_id=workspace_id,
                    run_id=checkpoint.run_id,
                )
        return plan, inputs, runtime, context
    except BaseException:
        if runtime is not None:
            await runtime.close()
        raise


@dataclass(frozen=True)
class WorkflowApprovalInspection:
    checkpoint: WorkflowContinuationCheckpoint
    can_decide: bool
    can_resume: bool
    resume_error_code: str | None = None
    resume_correction: str | None = None


async def inspect_workflow_approval(
    *,
    service,
    workspace_id,
    workspace_dir,
    checkpoint,
    subject_digest,
    gateway=None,
    session_id="",
):
    """Read permission using the same currentness/preparation as real mutations.

    This never acquires dispatch authority, records a decision, consumes a
    checkpoint or dispatches its external operation. Mutations rerun these checks
    under their canonical lease; an inspection result is not a reusable grant.
    """
    current = _current(service, checkpoint, workspace_id, subject_digest)
    if current.state not in {"pending", "approved"}:
        return WorkflowApprovalInspection(current, False, False)
    _, _, runtime, context = await _prepare(
        service=service,
        workspace_id=workspace_id,
        workspace_dir=workspace_dir,
        checkpoint=current,
        gateway=gateway,
        session_id=session_id,
    )
    try:
        if current.state == "pending":
            return WorkflowApprovalInspection(current, True, False)
        try:
            _dispatch_kind(current, context)
        except WorkflowSourceExecutionError as error:
            return WorkflowApprovalInspection(
                current, False, False, error.code, error.correction
            )
        return WorkflowApprovalInspection(current, False, True)
    finally:
        if runtime is not None:
            await runtime.close()


async def decide_workflow_approval(
    *,
    service,
    workspace_id,
    workspace_dir,
    checkpoint,
    subject_digest,
    decision,
    reason="",
    auto=False,
    actor="local_workspace_user",
    request_id=None,
    gateway=None,
    session_id="",
):
    if (
        decision not in {"approved", "changes_requested"}
        or not isinstance(reason, str)
        or len(reason) > 2000
        or (decision == "changes_requested" and not reason.strip())
    ):
        raise WorkflowExternalActionError(
            "approval_decision_invalid", "Unknown approval decision"
        )
    from core.process_validation import Identifier
    from pydantic import TypeAdapter

    TypeAdapter(Identifier).validate_python(actor)
    if request_id is not None:
        TypeAdapter(Identifier).validate_python(request_id)
    reason = reason.strip()
    async with _lease(workspace_id, checkpoint):
        current = _current(service, checkpoint, workspace_id, subject_digest)
        _, _, runtime, context = await _prepare(
            service=service,
            workspace_id=workspace_id,
            workspace_dir=workspace_dir,
            checkpoint=current,
            gateway=gateway,
            session_id=session_id,
        )
        try:
            if auto:
                if decision != "approved" or not context:
                    raise _error(
                        "WORKFLOW_INTEGRATION_POLICY_INVALID",
                        "Automatic review requires enrolled test authority.",
                        "Use a manual decision or enroll an exact automatic test policy.",
                    )
                authority = service.workflow_integration_policies.authorize_decision(
                    context["integration_policy_digest"],
                    workspace_id=workspace_id,
                    checkpoint=current,
                    expected_subject_digest=subject_digest,
                )
                actor, reason = authority["actor"], authority["reason"]
            decided = service.workflow_external_actions.decide(
                current.checkpoint_id,
                workspace_id=workspace_id,
                expected_subject_digest=subject_digest,
                actor=actor,
                approved=decision == "approved",
                reason=reason,
                request_id=request_id,
            )
            if current.state != decided.state or (
                request_id is not None
                and decided.state in {"approved", "changes_requested"}
            ):
                await record_workflow_approval_transition(
                    service=service,
                    workspace_dir=workspace_dir,
                    checkpoint=decided,
                    kind="approval_decided",
                )
            return decided
        finally:
            if runtime is not None:
                await runtime.close()


def _dispatch_kind(checkpoint, context):
    subject = checkpoint.subject
    if (
        checkpoint.action_kind == "local_review"
        and subject["binding"] == LOCAL_REVIEW_BINDING
        and subject["destination"] == LOCAL_REVIEW_DESTINATION
        and subject["action"] == {"kind": "local_review", "mode": "review_only"}
    ):
        return "local_review"
    if context and subject["binding"] == TEST_HANDOFF_BINDING:
        # authorize() has checked the exact enrolled test URI and confined
        # receipt path against every canonical action immediately before this.
        return "test_handoff"
    if checkpoint.action_kind == "mcp-operation":
        return "mcp-operation"
    raise _error(
        "WORKFLOW_EXTERNAL_DISPATCH_UNSUPPORTED",
        "This canonical external action has no supported authorized dispatcher.",
        "Configure an enrolled integration test destination or the required live transport adapter.",
    )


async def _dispatch(*, service, workspace_dir, checkpoint, kind, context):
    if kind == "local_review":
        return {
            "operation": "local_review",
            "effect": "review_only",
            "run_id": checkpoint.run_id,
        }
    subject = checkpoint.subject
    relative = subject["settings"]["receipt_path"]
    receipt = {
        "schema_version": 1,
        "integration_test": True,
        "simulated_handoff": True,
        "run_id": checkpoint.run_id,
        "step_id": checkpoint.step_id,
        "checkpoint_id": checkpoint.checkpoint_id,
        "subject_digest": checkpoint.subject_digest,
        "action_id": checkpoint.external_action["action_id"],
        "campaign_id": context["campaign_id"],
        "dataset_id": context["dataset_id"],
        "integration_policy_digest": context["integration_policy_digest"],
        "destination": subject["destination"],
        "action_kind": checkpoint.action_kind,
        "artifact_digests": subject["artifact_digests"],
        "network_dispatch": False,
    }
    text = json.dumps(receipt, ensure_ascii=False, indent=2)
    actual = await service.files.write_generated(
        workspace_dir, relative, text, "indexed"
    )
    if actual != relative:
        raise _error(
            "WORKFLOW_RECEIPT_COLLISION",
            "The enrolled receipt path was occupied during dispatch.",
            "Inspect the preserved receipt and reconcile the operation; it cannot be replayed.",
        )
    raw = text.encode("utf-8")
    if await service.files.read_reference(workspace_dir, actual) != raw:
        raise _error(
            "WORKFLOW_RECEIPT_CHANGED",
            "The generated test receipt did not retain its exact bytes.",
            "Inspect receipt storage and reconcile the existing action.",
        )
    return {
        "operation": "test_handoff",
        "integration_test": True,
        "simulated_handoff": True,
        "produced_files": [
            {
                "output_path": actual,
                "output_bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "output_format": "json",
                "output_port": "receipt",
            }
        ],
    }


async def _save_operation_receipt(*, service, workspace_dir, checkpoint, evidence):
    """Publish a confined actual receipt using existing indexed artifact storage."""
    relative = checkpoint.subject["settings"]["receipt_path"]
    WorkspacePath(workspace_dir).resolve(relative)
    receipt = {
        "schema_version": 1,
        "checkpoint_id": checkpoint.checkpoint_id,
        "subject_digest": checkpoint.subject_digest,
        "run_id": checkpoint.run_id,
        "action_id": checkpoint.external_action["action_id"],
        **{
            key: value for key, value in evidence.items() if key != "delivery_completed"
        },
    }
    text = json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False)
    actual = await service.files.write_generated(
        workspace_dir, relative, text, "indexed"
    )
    if actual != relative:
        raise _error(
            "WORKFLOW_RECEIPT_COLLISION",
            "The operation receipt path was occupied.",
            "Reconcile the existing operation; it cannot be replayed.",
        )
    raw = text.encode("utf-8")
    if await service.files.read_reference(workspace_dir, actual) != raw:
        raise _error(
            "WORKFLOW_RECEIPT_CHANGED",
            "The operation receipt did not retain its bytes.",
            "Inspect the stored receipt before continuing.",
        )
    return {
        **evidence,
        "produced_files": [
            {
                "output_path": actual,
                "output_bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "output_format": "json",
                "output_port": "receipt",
            }
        ],
    }


def _operation_dispatch_check(checkpoint, workspace_dir, runtime=None, step=None):
    """Use Gateway's existing final dispatch hook for exact file/tool freshness."""
    from .workflow_mcp_execution import schema_digest

    def check(tool):
        if runtime is not None:
            from .workflow_mcp_operations import qualify_operation

            qualify_operation(
                runtime,
                step,
                integration=bool(checkpoint.continuation.get("execution_context")),
            )
        binding = checkpoint.subject["binding"]
        if (tool.server_id, tool.name, schema_digest(tool)) != (
            binding["server"],
            binding["tool"],
            binding["schema"],
        ):
            raise _error(
                "WORKFLOW_CONTINUATION_STALE",
                "The approved provider changed before dispatch.",
                "Reconcile this action before preparing another submission.",
            )
        files = [
            {
                "path": checkpoint.workflow_id,
                "sha256": checkpoint.subject["definition_digest"],
            },
            *checkpoint.continuation.get("input_files", []),
            *checkpoint.continuation.get("artifact_files", []),
        ]
        paths = WorkspacePath(workspace_dir)
        try:
            for item in files:
                target = paths.resolve(item["path"], must_exist=True)
                with target.open("rb") as stream:
                    current = hashlib.file_digest(stream, "sha256").hexdigest()
                if current != item["sha256"]:
                    raise ValueError("Identity mismatch")
        except (OSError, ValueError) as error:
            raise _error(
                "WORKFLOW_CONTINUATION_STALE",
                "An approved file changed before dispatch.",
                "Inspect the exact saved action; it has not been replayed.",
            ) from error

    return check


async def resume_workflow_approval(
    *,
    service,
    workspace_id,
    workspace_dir,
    checkpoint,
    subject_digest,
    request_id,
    gateway=None,
    session_id="",
    response_generator,
    action_generator=None,
    on_event=None,
):
    async with _lease(workspace_id, checkpoint):
        current = _current(service, checkpoint, workspace_id, subject_digest)
        plan, inputs, runtime, context = await _prepare(
            service=service,
            workspace_id=workspace_id,
            workspace_dir=workspace_dir,
            checkpoint=current,
            gateway=gateway,
            session_id=session_id,
        )
        try:
            kind = _dispatch_kind(current, context)
            operation = None
            if kind == "mcp-operation":
                from .workflow_mcp_operations import qualify_operation

                operation = qualify_operation(
                    runtime,
                    plan.steps[current.continuation["next_step_index"]],
                    integration=bool(context),
                )
            if current.state == "consumed":
                prior = current.external_action or {}
                if prior.get("outcome") != "dispatched" or (
                    kind == "mcp-operation"
                    and not prior.get("evidence", {}).get("delivery_completed")
                ):
                    raise _error(
                        "WORKFLOW_CONTINUATION_OUTCOME_UNKNOWN",
                        "The consumed action has no confirmed completed outcome.",
                        "Reconcile its existing evidence; do not dispatch it again.",
                    )
            else:
                if kind == "test_handoff" or (
                    kind == "mcp-operation"
                    and current.subject["settings"].get("receipt_path")
                ):
                    receipt = WorkspacePath(workspace_dir).resolve(
                        current.subject["settings"]["receipt_path"]
                    )
                    if receipt.exists():
                        raise _error(
                            "WORKFLOW_RECEIPT_COLLISION",
                            "The enrolled receipt path already exists.",
                            "Use a fresh isolated attempt instead of overwriting existing output.",
                        )
                current = service.workflow_external_actions.consume_for_dispatch(
                    current.checkpoint_id,
                    workspace_id=workspace_id,
                    current_subject=current.subject,
                    action_id=request_id,
                )
                try:
                    await record_workflow_approval_transition(
                        service=service,
                        workspace_dir=workspace_dir,
                        checkpoint=current,
                        kind="external_action_authorized",
                    )
                    if kind == "mcp-operation":
                        from .workflow_mcp_operations import submit_operation

                        invocation, profile, monitor_profile, monitor_bindings = (
                            operation
                        )
                        submitted, evidence = await submit_operation(
                            runtime,
                            invocation,
                            plan.steps[current.continuation["next_step_index"]],
                            current.subject["settings"],
                            profile,
                            integration=bool(context),
                            before_dispatch=_operation_dispatch_check(
                                current,
                                workspace_dir,
                                runtime,
                                plan.steps[current.continuation["next_step_index"]],
                            ),
                        )
                    else:
                        evidence = await _dispatch(
                            service=service,
                            workspace_dir=workspace_dir,
                            checkpoint=current,
                            kind=kind,
                            context=context,
                        )
                except BaseException as error:
                    from .workflow_mcp_operations import OperationRejected

                    rejected = isinstance(error, OperationRejected)
                    current = service.workflow_external_actions.reconcile(
                        current.checkpoint_id,
                        workspace_id=workspace_id,
                        run_id=current.run_id,
                        expected_subject_digest=current.subject_digest,
                        outcome="not_dispatched" if rejected else "outcome_unknown",
                        evidence=error.evidence
                        if rejected
                        else {
                            "dispatch_error_type": type(error).__name__,
                            "replay_permitted": False,
                        },
                    )
                    await asyncio.shield(
                        record_workflow_approval_transition(
                            service=service,
                            workspace_dir=workspace_dir,
                            checkpoint=current,
                            kind="external_action_reconciled",
                        )
                    )
                    if rejected:
                        raise _error(
                            "WORKFLOW_MCP_OPERATION_REJECTED",
                            "The provider rejected the reviewed submission.",
                            "Inspect its recorded rejection and correct the configuration before preparing a new action.",
                        ) from error
                    if kind == "mcp-operation" and not isinstance(
                        error, asyncio.CancelledError
                    ):
                        raise _error(
                            "WORKFLOW_CONTINUATION_OUTCOME_UNKNOWN",
                            "The provider submission could not be confirmed.",
                            "Reconcile the existing action before another submission; it has not been replayed.",
                        ) from error
                    raise
                current = service.workflow_external_actions.reconcile(
                    current.checkpoint_id,
                    workspace_id=workspace_id,
                    run_id=current.run_id,
                    expected_subject_digest=current.subject_digest,
                    outcome="dispatched",
                    evidence=evidence,
                )
                await record_workflow_approval_transition(
                    service=service,
                    workspace_dir=workspace_dir,
                    checkpoint=current,
                    kind="external_action_reconciled",
                )
                if kind == "mcp-operation":
                    # Persist acceptance before observation. A monitor failure
                    # cannot erase the receipt or authorize another submission.
                    last_observation = {}
                    cancellation_requested = False

                    async def operation_event(event_kind, **data):
                        nonlocal last_observation, cancellation_requested
                        if event_kind != "operation_progress":
                            raise ValueError("Unexpected approved operation event")
                        last_observation = data
                        cancellation_requested |= (
                            data.get("state") == "cancellation_requested"
                        )
                        await record_workflow_approval_transition(
                            service=service,
                            workspace_dir=workspace_dir,
                            checkpoint=current,
                            kind=event_kind,
                            operation_event=data,
                        )
                        if on_event:
                            await on_event({"kind": event_kind, **data})

                    try:
                        if monitor_profile is not None:
                            from .workflow_async_operations import monitor_operation

                            await monitor_operation(
                                runtime,
                                invocation,
                                submitted,
                                monitor_profile,
                                operation_event,
                                pinned_tools=monitor_bindings,
                            )
                            evidence = {**evidence, "observed_outcome": "completed"}
                        if current.subject["settings"].get("receipt_path"):
                            evidence = await _save_operation_receipt(
                                service=service,
                                workspace_dir=workspace_dir,
                                checkpoint=current,
                                evidence=evidence,
                            )
                        evidence = {**evidence, "delivery_completed": True}
                    except BaseException as error:
                        actual = {
                            "APPLICATION_FAILED": "failed",
                            "APPLICATION_CANCELLED": "cancelled",
                            "APPLICATION_INPUT_REQUIRED": "input_required",
                        }.get(getattr(error, "code", None), "unknown")
                        if last_observation.get(
                            "observation_source"
                        ) == "provider_status" and last_observation.get("state") in {
                            "completed",
                            "failed",
                            "cancelled",
                        }:
                            actual = last_observation["state"]
                        evidence = {
                            **evidence,
                            "delivery_completed": False,
                            "observation_error_type": type(error).__name__,
                            "observed_outcome": actual,
                            "cancellation_requested": cancellation_requested,
                            "cancellation_outcome": actual
                            if cancellation_requested
                            else None,
                        }
                        current = service.workflow_external_actions.reconcile(
                            current.checkpoint_id,
                            workspace_id=workspace_id,
                            run_id=current.run_id,
                            expected_subject_digest=current.subject_digest,
                            outcome="dispatched",
                            evidence=evidence,
                        )
                        await asyncio.shield(
                            record_workflow_approval_transition(
                                service=service,
                                workspace_dir=workspace_dir,
                                checkpoint=current,
                                kind="external_action_reconciled",
                            )
                        )
                        raise
                    current = service.workflow_external_actions.reconcile(
                        current.checkpoint_id,
                        workspace_id=workspace_id,
                        run_id=current.run_id,
                        expected_subject_digest=current.subject_digest,
                        outcome="dispatched",
                        evidence=evidence,
                    )
                    await record_workflow_approval_transition(
                        service=service,
                        workspace_dir=workspace_dir,
                        checkpoint=current,
                        kind="external_action_reconciled",
                    )

            async def execute(emit):
                return await execute_prompt_workflow(
                    service=service,
                    workspace_dir=workspace_dir,
                    plan=plan,
                    input_values=inputs,
                    response_generator=response_generator,
                    action_generator=action_generator,
                    tool_runtime=runtime,
                    on_event=emit,
                    continuation=current.continuation,
                    completed_checkpoint=asdict(current),
                    execution_context=context,
                    run_id=current.run_id,
                )

            result = await record_workflow_resume(
                service=service,
                workspace_dir=workspace_dir,
                workspace_id=workspace_id,
                checkpoint=current,
                execute=execute,
                on_event=on_event,
            )
            return current, result
        finally:
            if runtime is not None:
                await runtime.close()
