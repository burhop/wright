"""Canonical approval decisions and durable, same-run continuation dispatch.

Only the fixed local review and enrolled integration handoff operations execute
here. Other external transports need their own authorized dispatcher; no tool or
network destination is inferred from a user-authored checkpoint.
"""

from dataclasses import asdict
import asyncio
import hashlib
import json

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
    prepare_prompt_workflow,
    execute_prompt_workflow,
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
        state.get("schema_version") != 2
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
        plan, inputs = await prepare_prompt_workflow(
            service=service,
            workspace_dir=workspace_dir,
            path=checkpoint.workflow_id,
            expected_digest=checkpoint.subject["definition_digest"],
            tool_runtime=get_runtime,
        )
        state = checkpoint.continuation
        cursor = state.get("next_step_index")
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
                for key in ("binding", "destination", "settings", "action")
            )
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
    gateway=None,
    session_id="",
):
    if decision not in {"approved", "changes_requested"}:
        raise WorkflowExternalActionError(
            "approval_decision_invalid", "Unknown approval decision"
        )
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
            actor = "local_workspace_user"
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
            )
            if current.state != decided.state:
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
            if current.state == "consumed":
                if (current.external_action or {}).get("outcome") != "dispatched":
                    raise _error(
                        "WORKFLOW_CONTINUATION_OUTCOME_UNKNOWN",
                        "The consumed action has no confirmed completed outcome.",
                        "Reconcile its existing evidence; do not dispatch it again.",
                    )
            else:
                if kind == "test_handoff":
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
                    evidence = await _dispatch(
                        service=service,
                        workspace_dir=workspace_dir,
                        checkpoint=current,
                        kind=kind,
                        context=context,
                    )
                except BaseException as error:
                    current = service.workflow_external_actions.reconcile(
                        current.checkpoint_id,
                        workspace_id=workspace_id,
                        run_id=current.run_id,
                        expected_subject_digest=current.subject_digest,
                        outcome="outcome_unknown",
                        evidence={
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
