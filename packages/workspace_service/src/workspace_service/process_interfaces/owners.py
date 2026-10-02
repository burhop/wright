"""Compose read facts from existing run, validation and decision authorities."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from pydantic import ValidationError

from core.process_interactions import (
    PAGE_ITEMS,
    Action,
    ArtifactRef,
    NavigationTarget,
    Observation,
    PendingInteraction,
    ReviewDecision,
    ApprovedActionReceipt,
    ProcessRef,
    Reason,
)
from core.redaction import redact_text
from core.process_validation import canonical_digest

from ..process_validation.application import ValidationApplication
from ..workflow_approval_execution import inspect_workflow_approval
from ..workflow_execution_continuation import restore_result
from ..workflow_external_actions import WorkflowExternalActionError
from ..workflow_run_record import WorkflowRunReadError, read_workflow_run
from ..workflow_source_execution import WorkflowSourceExecutionError, _parse
from .errors import ProcessInterfaceError
from .projection import (
    ProjectionFacts,
    RecordedRun,
    _STATES,
    project_operation_observations,
)


def _blocked(code, message, correction):
    return Reason(
        code=code,
        message=redact_text(message)[:8192],
        correction=redact_text(correction)[:8192],
    )


async def _human_input(app, resolved, view, *, gateway, session_id):
    """Present the retained declaration; qualify permission without releasing it."""
    from .interactions import input_subject, prepare_input_continuation

    reference = view.get("input_checkpoint")
    if not reference:
        return (), ()
    checkpoint = app.human_inputs.get(
        reference.get("checkpoint_id"),
        workspace_id=resolved.process.workspace_id,
        run_id=view["run_id"],
    )
    if (
        checkpoint.workflow_id != resolved.process.source_path
        or checkpoint.subject_digest != reference.get("subject_digest")
        or checkpoint.subject.get("definition_digest") != view["source_digest"]
    ):
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "The declared input belongs to another process revision or run.",
            "Open the exact saved run and its declared checkpoint.",
        )
    declaration = input_subject(checkpoint.subject).declaration
    evidence = tuple(
        ArtifactRef(artifact_ref=path, sha256=digest)
        for path, digest in sorted(
            {
                (item["path"], item["sha256"])
                for item in checkpoint.continuation["artifact_files"]
            }
        )
    )
    if len(evidence) > PAGE_ITEMS:
        raise ProcessInterfaceError(
            "READINESS_UNSUPPORTED",
            "This input checkpoint exceeds the bounded evidence composition size.",
            "Inspect every artifact in the canonical run and reduce the declared checkpoint's evidence scope.",
        )
    reason = None
    enabled = (
        view["status"] == "waiting_human"
        and checkpoint.state == "pending"
        and checkpoint.continuation.get("response_id") is None
        and not app.runs.is_live(view["run_id"])
    )
    if checkpoint.state == "pending":

        def available_gateway():
            if gateway is None:
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "The configured process tools are unavailable.",
                    "Reconnect the required providers before continuing.",
                )
            return gateway() if callable(gateway) else gateway

        try:
            prepared = await prepare_input_continuation(
                app,
                resolved,
                checkpoint,
                gateway=available_gateway,
                session_id=session_id,
            )
            if prepared.runtime is not None:
                await prepared.runtime.close()
        except ProcessInterfaceError as error:
            reason = error.reason
            enabled = False
    state = (
        "stale"
        if checkpoint.state in {"expired", "stale"}
        or reason
        and reason.code in {"SUBJECT_STALE", "SOURCE_CHANGED"}
        else "consumed"
        if checkpoint.state == "consumed"
        else "cancelled"
        if checkpoint.state == "cancelled"
        else "responded"
        if checkpoint.continuation.get("response_id") is not None
        else "waiting"
    )
    interaction = PendingInteraction(
        checkpoint_id=checkpoint.checkpoint_id,
        step_id=checkpoint.step_id,
        kind="input",
        subject_digest=checkpoint.subject_digest,
        instructions=redact_text(declaration.instructions),
        response_schema=declaration.response_schema,
        evidence=evidence,
        state=state,
    )
    action = Action(
        action_id=f"respond-{checkpoint.checkpoint_id}",
        operation="respond",
        title="Submit response",
        subject_digest=checkpoint.subject_digest,
        checkpoint_id=checkpoint.checkpoint_id,
        enabled=enabled,
        reasons=()
        if enabled
        else (
            reason
            or _blocked(
                "ACTION_NOT_PERMITTED",
                "This run is not waiting for a new response to this input.",
                "Follow the recorded run; reconcile a saved response instead of submitting another answer.",
            ),
        ),
    )
    return (interaction,), (action,)


def _action_receipt(checkpoint):
    action = checkpoint.external_action
    if not action:
        return None
    evidence = action.get("evidence") or {}
    outcome = action.get("outcome")
    submission = (
        "unknown"
        if outcome == "outcome_unknown"
        else "rejected"
        if evidence.get("submission") == "rejected"
        or (outcome == "not_dispatched" and action.get("reconciled_at"))
        else "accepted"
        if outcome == "dispatched"
        else "authorized"
    )
    return ApprovedActionReceipt(
        request_id=action["action_id"],
        principal_id=action.get("principal_id"),
        submission=submission,
        delivery_completed=bool(evidence.get("delivery_completed"))
        if checkpoint.action_kind == "mcp-operation"
        else outcome == "dispatched",
        observed_outcome=evidence.get("observed_outcome"),
        provider_reference=evidence.get("provider_reference"),
        cancellation_requested=bool(evidence.get("cancellation_requested")),
        cancellation_outcome=evidence.get("cancellation_outcome"),
    )


async def _approval(app, resolved, view, *, gateway, session_id):
    reference = view.get("approval")
    if (
        not reference
        or not reference.get("checkpoint_id")
        or not reference.get("subject_digest")
    ):
        return (), ()
    try:
        checkpoint = app.workspace.workflow_external_actions.get(
            reference["checkpoint_id"],
            workspace_id=resolved.process.workspace_id,
            run_id=view["run_id"],
        )
    except WorkflowExternalActionError as error:
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "The exact run checkpoint could not be verified.",
            "Inspect this run's canonical checkpoint reference.",
            details={"checkpoint_error": error.code},
        ) from error
    if (
        checkpoint.workflow_id != resolved.process.source_path
        or checkpoint.subject.get("definition_digest") != view["source_digest"]
    ):
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "The checkpoint belongs to another process revision.",
            "Open the exact recorded process and checkpoint.",
        )
    reason = None
    can_decide = can_resume = False
    try:
        inspection = await inspect_workflow_approval(
            service=app.workspace,
            workspace_id=resolved.process.workspace_id,
            workspace_dir=resolved.workspace_dir,
            checkpoint=checkpoint,
            subject_digest=reference["subject_digest"],
            gateway=gateway,
            session_id=session_id,
        )
        checkpoint = inspection.checkpoint
        can_decide, can_resume = inspection.can_decide, inspection.can_resume
        if app.runs.is_live(view["run_id"]):
            can_decide = can_resume = False
            reason = _blocked(
                "ACTION_NOT_PERMITTED",
                "This run is already executing a segment.",
                "Follow the saved run and its current action receipt.",
            )
        if inspection.resume_error_code:
            reason = _blocked(
                "CAPABILITY_UNAVAILABLE",
                "This action has no available authorized dispatcher.",
                inspection.resume_correction,
            )
    except (WorkflowExternalActionError, WorkflowSourceExecutionError) as error:
        reason = _blocked(
            "SOURCE_CHANGED"
            if error.code == "WORKFLOW_SOURCE_CONFLICT"
            else "SUBJECT_STALE"
            if "STALE" in error.code.upper() or "POLICY" in error.code.upper()
            else "CAPABILITY_UNAVAILABLE",
            str(error),
            getattr(
                error, "correction", "Inspect the exact checkpoint before continuing."
            ),
        )
    state = (
        "stale"
        if reason
        and reason.code in {"SUBJECT_STALE", "SOURCE_CHANGED"}
        or checkpoint.state in {"stale", "expired"}
        else "waiting"
        if checkpoint.state in {"pending", "approved"}
        else "consumed"
        if checkpoint.state == "consumed"
        else "responded"
    )
    interaction = PendingInteraction(
        checkpoint_id=checkpoint.checkpoint_id,
        step_id=checkpoint.step_id,
        kind="action",
        subject_digest=checkpoint.subject_digest,
        instructions="Review the exact process action and its evidence before continuing.",
        decisions=("approved", "changes_requested"),
        state=state,
        action_receipt=_action_receipt(checkpoint),
        decision=ReviewDecision(
            decision=(checkpoint.continuation.get("decision_receipt") or {}).get(
                "decision",
                "changes_requested"
                if checkpoint.state == "changes_requested"
                else "approved",
            ),
            actor=checkpoint.actor,
            reason=redact_text(checkpoint.reason or "")[:2000],
            request_id=(checkpoint.continuation.get("decision_receipt") or {}).get(
                "request_id"
            ),
            integration_test=checkpoint.actor.startswith("integration_test:"),
        )
        if checkpoint.actor is not None
        else None,
    )
    review_reason = reason or _blocked(
        "ACTION_NOT_PERMITTED",
        "This checkpoint is not awaiting a review decision.",
        "Inspect its recorded decision or prepare a new exact subject.",
    )
    resume_reason = reason or _blocked(
        "ACTION_NOT_PERMITTED",
        "This checkpoint is not ready to continue.",
        "Complete its required review; an already consumed action cannot be submitted again.",
    )
    actions = (
        Action(
            action_id=f"review-{checkpoint.checkpoint_id}",
            operation="review",
            title="Review action",
            enabled=can_decide,
            subject_digest=checkpoint.subject_digest,
            checkpoint_id=checkpoint.checkpoint_id,
            reasons=() if can_decide else (review_reason,),
        ),
        Action(
            action_id=f"continue-{checkpoint.checkpoint_id}",
            operation="action",
            title="Continue process",
            enabled=can_resume,
            subject_digest=checkpoint.subject_digest,
            checkpoint_id=checkpoint.checkpoint_id,
            reasons=() if can_resume else (resume_reason,),
        ),
    )
    return (interaction,), actions


async def _review(app, resolved, view):
    reference = view.get("review")
    if (
        not reference
        or not reference.get("review_id")
        or not reference.get("package_digest")
    ):
        return (), ()
    try:
        review = await app.workspace.workflow_artifact_reviews.get(
            resolved.process.workspace_id,
            reference["review_id"],
            resolved.workspace_dir,
        )
    except KeyError as error:
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "The exact run review could not be verified.",
            "Inspect this run's canonical review reference.",
        ) from error
    if (
        review["run_id"] != view["run_id"]
        or review["workflow_path"] != resolved.process.source_path
        or review["source_digest"] != view["source_digest"]
    ):
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "The review belongs to another process run.",
            "Open this run's exact review package.",
        )
    current = (
        review.get("evidence_status") == "current"
        and review["package_digest"] == reference["package_digest"]
    )
    enabled = current and review["state"] == "pending"
    evidence = tuple(
        ArtifactRef(artifact_ref=item["output_path"], sha256=item["sha256"])
        for item in review["artifacts"]
    )
    interaction = PendingInteraction(
        checkpoint_id=review["review_id"],
        step_id=review["task_id"],
        kind="review",
        subject_digest=review["package_digest"],
        instructions=redact_text(review["instructions"])[:8192],
        decisions=("approved", "changes_requested"),
        evidence=evidence,
        state="stale" if not current else "waiting" if enabled else "responded",
        decision=ReviewDecision(
            decision=review["state"],
            actor=review["actor"],
            reason=redact_text(review.get("reason") or "")[:2000],
            request_id=review.get("request_id"),
            integration_test=review["actor"].startswith("integration_test:"),
        )
        if review.get("actor") is not None
        and review["state"] in {"approved", "changes_requested"}
        else None,
    )
    reason = _blocked(
        "SUBJECT_STALE" if not current else "ACTION_NOT_PERMITTED",
        "The review evidence changed or is unavailable."
        if not current
        else "This review already has a decision.",
        "Create a new exact review package; inspect the recorded evidence and decision.",
    )
    action = Action(
        action_id=f"review-{review['review_id']}",
        operation="review",
        title="Review outputs",
        enabled=enabled,
        subject_digest=review["package_digest"],
        checkpoint_id=review["review_id"],
        reasons=() if enabled else (reason,),
    )
    return (interaction,), (action,)


def _reports(app, resolved, run_id):
    validation = ValidationApplication(
        app.db_path, resolved.process.workspace_id, resolved.workspace_dir
    )
    identities = validation.repository.assessment_ids_for_run(
        resolved.process.workspace_id, run_id
    )
    if identities and validation.repository.assessment_ids_for_run(
        resolved.process.workspace_id,
        run_id,
        cursor=identities[-1][0],
        limit=1,
    ):
        raise ProcessInterfaceError(
            "READINESS_UNSUPPORTED",
            "This run exceeds the bounded assessment composition size.",
            "Use the canonical paged validation results to inspect every retained assessment.",
        )
    return tuple(
        validation.get_result(assessment_id) for _, assessment_id in identities
    )


async def recorded_run_facts(app, resolved, run_id, *, gateway=None, session_id=""):
    """Read one authorized run; mutations still belong to canonical use cases."""
    generated_at = datetime.now(timezone.utc).isoformat()
    receipt = await asyncio.to_thread(
        app.inputs.receipt_for_run,
        resolved.process.workspace_id,
        resolved.process.source_path,
        run_id,
    )
    try:
        view = await asyncio.to_thread(
            read_workflow_run,
            resolved.workspace_dir,
            resolved.process.source_path,
            run_id,
            **(
                {"run_log_path": receipt.run_log_path}
                if receipt and receipt.run_log_path
                else {}
            ),
        )
        process = ProcessRef(
            workspace_id=resolved.process.workspace_id,
            source_path=resolved.process.source_path,
            source_digest=view["source_digest"],
        )
        results = tuple(restore_result(item) for item in view["results"])
    except (
        WorkflowRunReadError,
        ValidationError,
        ValueError,
        TypeError,
        KeyError,
    ) as error:
        raise ProcessInterfaceError(
            "CAPABILITY_UNAVAILABLE",
            "Wright could not verify this recorded run.",
            "Open its canonical run log and check the exact process and run identity.",
            details={"record_error": getattr(error, "code", "invalid")},
        ) from error
    inputs = None
    if receipt:
        inputs = await asyncio.to_thread(
            app.inputs.get_snapshot, process.workspace_id, receipt.input_snapshot_id
        )
        if (
            receipt.process != process
            or inputs.process != process
            or receipt.input_digest != inputs.digest
        ):
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The retained inputs do not match this run's process revision.",
                "Inspect the exact run's source and input receipt.",
            )
    approval, action_permissions = await _approval(
        app, resolved, view, gateway=gateway, session_id=session_id
    )
    human_input, response_permissions = await _human_input(
        app, resolved, view, gateway=gateway, session_id=session_id
    )
    review, review_permissions = await _review(app, resolved, view)
    reports = await asyncio.to_thread(_reports, app, resolved, run_id)
    execution = view["execution"]
    progress = execution.get("last_progress") or {}
    diagnostics = ()
    if view.get("error"):
        step_id = (
            progress.get("task_id")
            if progress.get("kind") != "step_completed"
            else None
        )
        # A reason is a read projection, never a new checkpoint or permission.
        # Only navigate to a step belonging to this exact accepted definition.
        if not isinstance(step_id, str) or step_id not in {
            block["id"]
            for block in _parse(resolved.document.source)
            if block["kind"] == "task"
        }:
            step_id = None
        diagnostics = (
            Reason(
                code=view.get("code") or "EXECUTION_FAILED",
                message=redact_text(view["error"])[:8192],
                correction=redact_text(
                    view.get("correction")
                    or "Inspect the recorded run and completed operations before starting another attempt."
                )[:8192],
                step_id=step_id,
                navigation=NavigationTarget(
                    kind="block", block_id=step_id, run_id=run_id
                )
                if step_id
                else NavigationTarget(kind="run", run_id=run_id),
                technical_details_ref=view["path"],
            ),
        )
    observations = (
        Observation(
            observation_id="source-run",
            provider_binding="wright-source-run",
            operation_id=run_id,
            state=_STATES[view["status"]],
            observed_at=generated_at,
            activity=redact_text(progress["message"])[:8192]
            if progress.get("message")
            else None,
            metrics={
                "recorded_events": execution["event_count"],
                "completed_steps": len(execution["completed_task_ids"]),
            },
            limitations=(
                "Some recorded result metadata exceeded the read bound; use the canonical run log.",
            )
            if execution["truncated"]
            else (),
        ),
    )
    cancel_enabled, cancel_message = app.runs.cancellation_capability(run_id)
    cancel_action = Action(
        action_id="cancel-run",
        title="Cancel this run",
        operation="cancel",
        subject_digest=canonical_digest(
            {
                "process": process,
                "run_id": run_id,
                "input_digest": inputs.digest if inputs else None,
            }
        ),
        enabled=cancel_enabled,
        reasons=()
        if cancel_enabled
        else (
            _blocked(
                "CAPABILITY_UNAVAILABLE",
                cancel_message,
                "Inspect the exact run and provider observations; a local request cannot establish a remote outcome.",
            ),
        ),
    )
    return ProjectionFacts(
        process=resolved.process,
        generated_at=generated_at,
        run=RecordedRun(
            process=process,
            run_id=run_id,
            status=view["status"],
            cursor=execution["event_count"],
            observed_at=generated_at,
            results=results,
            input_snapshot=inputs,
            results_truncated=bool(execution["truncated"]),
        ),
        reports=reports,
        interactions=approval + review + human_input,
        actions=action_permissions
        + review_permissions
        + response_permissions
        + (cancel_action,),
        observations=observations
        + project_operation_observations(execution, generated_at),
        diagnostics=diagnostics,
    )
