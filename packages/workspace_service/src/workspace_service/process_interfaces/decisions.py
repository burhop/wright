"""Scoped review decisions over the existing approval and artifact owners.

The browser selects an exact subject and a declared decision. Run identity and
actor come from the registered process and authenticated invocation scope. A
decision records evidence; external dispatch remains a separate operation.
"""

from __future__ import annotations

from pydantic import TypeAdapter

from core.process_validation import Digest, Identifier
from core.tracing import traced

from ..workflow_approval_execution import decide_workflow_approval
from ..workflow_external_actions import WorkflowExternalActionError
from ..workflow_source_execution import WorkflowSourceExecutionError
from .errors import ProcessInterfaceError


def decision_error(error):
    code = getattr(error, "code", "")
    return ProcessInterfaceError(
        "SOURCE_CHANGED"
        if code == "WORKFLOW_SOURCE_CONFLICT"
        else "OUTCOME_UNKNOWN"
        if "OUTCOME_UNKNOWN" in code.upper()
        else "SUBJECT_STALE"
        if "STALE" in code.upper() or "EXPIRED" in code.upper()
        else "REQUEST_CONFLICT"
        if "CONFLICT" in code.upper()
        else "RESPONSE_INVALID"
        if "INVALID" in code.upper()
        else "CAPABILITY_UNAVAILABLE",
        str(error),
        getattr(error, "correction", None)
        or "Refresh this run and inspect its exact checkpoint and recorded decision.",
    )


class ProcessReviewDecisions:
    def __init__(self, application):
        self.application = application

    @traced("process.interface.review.decide")
    async def decide(
        self,
        scope,
        process,
        checkpoint_id,
        request_id,
        *,
        expected_subject_digest,
        decision,
        reason="",
        gateway=None,
        session_id="",
    ):
        scope.require(process, "process.review")
        scope.require(process, "process.read")
        checkpoint_id = TypeAdapter(Identifier).validate_python(checkpoint_id)
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        expected_subject_digest = TypeAdapter(Digest).validate_python(
            expected_subject_digest
        )
        if (
            decision not in {"approved", "changes_requested"}
            or not isinstance(reason, str)
            or len(reason) > 2000
            or (decision == "changes_requested" and not reason.strip())
        ):
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "Choose an available review decision and explain requested changes.",
                "Review the current evidence and provide a reason of at most 2,000 characters.",
            )
        reason = reason.strip()
        resolved = await self.application.resolve_process(
            scope, process, operation="process.review"
        )
        workspace = self.application.workspace
        try:
            checkpoint = workspace.workflow_external_actions.lookup(checkpoint_id)
        except WorkflowExternalActionError as error:
            if error.code != "approval_not_found":
                raise decision_error(error) from error
            checkpoint = None
        try:
            if checkpoint is not None:
                if (
                    checkpoint.workspace_id != process.workspace_id
                    or checkpoint.workflow_id != process.source_path
                    or checkpoint.checkpoint_kind != "approval"
                    or checkpoint.subject.get("definition_digest")
                    != process.source_digest
                ):
                    raise self._scope_error()
                run_id = checkpoint.run_id
                self.application.runs._receipt(scope, process, run_id, "process.review")
                _, view = self.application.runs._record(scope, process, run_id)
                reference = view.get("approval") or {}
                if (
                    reference.get("checkpoint_id") != checkpoint_id
                    or reference.get("subject_digest") != expected_subject_digest
                ):
                    raise self._scope_error()
                await decide_workflow_approval(
                    service=workspace,
                    workspace_id=process.workspace_id,
                    workspace_dir=resolved.workspace_dir,
                    checkpoint=checkpoint,
                    subject_digest=expected_subject_digest,
                    decision=decision,
                    reason=reason,
                    actor=scope.principal_id,
                    request_id=request_id,
                    gateway=gateway,
                    session_id=session_id,
                )
            else:
                reviews = getattr(workspace, "workflow_artifact_reviews", None)
                if reviews is None:
                    raise ProcessInterfaceError(
                        "CAPABILITY_UNAVAILABLE",
                        "This checkpoint has no available review owner.",
                        "Open its exact saved run and reconnect its review service.",
                    )
                review = await reviews.get(
                    process.workspace_id, checkpoint_id, resolved.workspace_dir
                )
                if (
                    review["workflow_path"] != process.source_path
                    or review["source_digest"] != process.source_digest
                ):
                    raise self._scope_error()
                run_id = review["run_id"]
                self.application.runs._receipt(scope, process, run_id, "process.review")
                _, view = self.application.runs._record(scope, process, run_id)
                reference = view.get("review") or {}
                if (
                    reference.get("review_id") != checkpoint_id
                    or reference.get("package_digest") != expected_subject_digest
                ):
                    raise self._scope_error()
                decided = await reviews.decide(
                    workspace_id=process.workspace_id,
                    workspace_dir=resolved.workspace_dir,
                    review_id=checkpoint_id,
                    expected_package_digest=expected_subject_digest,
                    decision=decision,
                    reason=reason,
                    actor=scope.principal_id,
                    request_id=request_id,
                )
                from ..workflow_run_record import (
                    record_workflow_artifact_review_decision,
                )

                try:
                    await record_workflow_artifact_review_decision(
                        service=workspace,
                        workspace_dir=resolved.workspace_dir,
                        workspace_id=process.workspace_id,
                        review=decided,
                    )
                except (OSError, ValueError) as error:
                    raise ProcessInterfaceError(
                        "OUTCOME_UNKNOWN",
                        "The review decision was saved but its run update could not be confirmed.",
                        "Reconcile this same review request; do not prepare another decision or rerun work.",
                    ) from error
        except (WorkflowExternalActionError, WorkflowSourceExecutionError) as error:
            raise decision_error(error) from error
        except KeyError as error:
            raise self._scope_error() from error
        except OSError as error:
            raise ProcessInterfaceError(
                "OUTCOME_UNKNOWN",
                "Wright could not confirm the review update.",
                "Reconcile this same review request and inspect its recorded decision before another action.",
            ) from error
        return await self.application.get_snapshot(
            scope, process, run_id=run_id, gateway=gateway, session_id=session_id
        )

    @staticmethod
    def _scope_error():
        return ProcessInterfaceError(
            "SCOPE_DENIED",
            "This checkpoint is not the declared review of this exact process run.",
            "Open this process's saved run and review its current checkpoint.",
        )
