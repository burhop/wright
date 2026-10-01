"""Pure presentation of owner facts; never executes or approves a process."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

from pydantic import ValidationError

from core.process_interactions import (
    Action,
    ArtifactRef,
    AssessmentRef,
    InputDefinition,
    InputSnapshot,
    InteractionContext,
    InteractionSnapshot,
    NavigationTarget,
    Observation,
    OutputRef,
    PendingInteraction,
    ProcessRef,
    Readiness,
    Reason,
    Timestamp,
)
from core.process_validation import ValidationReport, canonical_digest
from core.redaction import redact_text

from ..workflow_results import EngineeringResult
from .errors import ProcessInterfaceError
from .service import ProcessScope

_STATES = {
    "running": "running",
    "completed": "completed",
    "failed": "failed",
    "pending_review": "waiting_human",
    "awaiting_approval": "waiting_human",
    "waiting_human": "waiting_human",
    "continuation_ready": "waiting_human",
    "changes_requested": "waiting_human",
    "awaiting_external_outcome": "waiting_external",
    "waiting_external": "waiting_external",
    "external_action_not_dispatched": "failed",
    "external_action_outcome_unknown": "reconciliation_required",
    "interrupted": "reconciliation_required",
    "unknown": "reconciliation_required",
    "reconciliation_required": "reconciliation_required",
    "cancellation_requested": "cancellation_requested",
    "cancelled": "cancelled",
}
_OPERATIONS = {
    "start": "process.start",
    "respond": "process.respond",
    "review": "process.review",
    "action": "process.action",
    "cancel": "process.cancel",
    "read": "process.read",
    "attach": "process.read",
    "navigate": "process.navigate",
}
# Preview support is deliberately limited to implemented generic viewers. A
# format name alone cannot establish a toolpath/parser/native-app capability.
_VIEWERS = {
    "stl": "stl",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "webp": "image",
}

_OPERATION_STATES = {
    "submitted": "waiting_external",
    "working": "running",
    "completed": "completed",
    "results_collected": "completed",
    "failed": "failed",
    "cancelled": "cancelled",
    "cancellation_requested": "cancellation_requested",
    "input_required": "reconciliation_required",
    "cancellation_unconfirmed": "reconciliation_required",
    "cancellation_unavailable": "reconciliation_required",
    "monitor_interrupted": "reconciliation_required",
    "status_unavailable": "reconciliation_required",
    "reconciliation_required": "reconciliation_required",
}


def project_operation_observations(execution, generated_at):
    """Read compact recorder facts; never poll, mutate or infer engineering metrics."""
    observations = []
    unavailable = bool(execution.get("operations_truncated"))
    for item in execution.get("operations", ()):
        try:
            if not isinstance(item, dict) or not all(
                isinstance(item.get(key), str)
                and item[key].strip()
                and len(item[key]) <= 160
                for key in ("provider_binding", "operation_id", "task_id")
            ):
                raise ValueError()
            limits = tuple(item.get("limitations", ()))
            source = item.get("observation_source")
            qualified = (
                source
                in {"provider_status", "submission_receipt", "local_request", "unknown"}
                and isinstance(item.get("provider_schema_digest"), str)
                and len(item["provider_schema_digest"]) == 64
                and all(c in "0123456789abcdef" for c in item["provider_schema_digest"])
            )
            if not qualified or not item.get("observed_at"):
                raise ValueError()
            for metric in ("progress_percent", "estimated_remaining_seconds"):
                value = item.get(metric)
                if value is not None and (
                    type(value) not in (int, float) or not math.isfinite(value)
                ):
                    raise ValueError()
            observation = Observation(
                observation_id="operation-"
                + canonical_digest(
                    [item["provider_binding"], item["task_id"], item["operation_id"]]
                ),
                provider_binding=item["provider_binding"],
                operation_id=item["operation_id"],
                state=_OPERATION_STATES.get(
                    item.get("state"), "reconciliation_required"
                ),
                observed_at=item["observed_at"],
                stale_after=item.get("stale_after"),
                activity=redact_text(item["message"])[:8192]
                if item.get("message")
                else None,
                progress_percent=item.get("progress_percent"),
                estimated_remaining_seconds=item.get("estimated_remaining_seconds"),
                metrics={
                    **item.get("metrics", {}),
                    "step_id": item["task_id"],
                    "provider_schema_digest": item["provider_schema_digest"],
                    "observation_source": source,
                },
                limitations=limits,
            )
            # A read now is not a new provider observation. Preserve the saved
            # timestamp; require reconciliation when active facts have expired.
            stamp = datetime.fromisoformat(
                observation.observed_at.replace("Z", "+00:00")
            )
            now = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            deadline = (
                datetime.fromisoformat(observation.stale_after.replace("Z", "+00:00"))
                if observation.stale_after
                else None
            )
            if (
                stamp.tzinfo is None
                or now.tzinfo is None
                or stamp > now
                or deadline
                and (deadline.tzinfo is None or deadline <= stamp)
            ):
                raise ValueError()
            if observation.state not in {"completed", "failed", "cancelled"} and (
                deadline is None or now >= deadline
            ):
                observation = observation.model_copy(
                    update={
                        "state": "reconciliation_required",
                        "progress_percent": None,
                        "estimated_remaining_seconds": None,
                        "limitations": (
                            *observation.limitations,
                            "The provider observation is stale; reconcile the identified operation before another action.",
                        ),
                    }
                )
            observations.append(observation)
        except (ValidationError, ValueError, TypeError, KeyError, OverflowError):
            unavailable = True
    if unavailable:
        observations.append(
            Observation(
                observation_id="unverified-provider-history",
                provider_binding="unqualified-provider",
                state="reconciliation_required",
                observed_at=generated_at,
                limitations=(
                    "Some operation identities or observations could not be verified within the read bound. Inspect the canonical run log before another action.",
                ),
            )
        )
    return tuple(observations)


@dataclass(frozen=True, slots=True)
class RecordedRun:
    """Read facts after the existing run owner has reconciled its lease/outcome."""

    process: ProcessRef
    run_id: str
    status: str
    cursor: int
    observed_at: Timestamp
    results: tuple[EngineeringResult, ...] = ()
    input_snapshot: InputSnapshot | None = None
    results_truncated: bool = False


@dataclass(frozen=True, slots=True)
class ProjectionFacts:
    """Internal service composition, not a browser request or retained run table."""

    process: ProcessRef
    generated_at: Timestamp
    input_snapshot: InputSnapshot | None = None
    inputs: tuple[InputDefinition, ...] = ()
    readiness: Readiness | None = None
    run: RecordedRun | None = None
    reports: tuple[ValidationReport, ...] = ()
    interactions: tuple[PendingInteraction, ...] = ()
    actions: tuple[Action, ...] = ()
    observations: tuple[Observation, ...] = ()
    diagnostics: tuple[Reason, ...] = ()


def _assessments(
    result: EngineeringResult, reports: tuple[ValidationReport, ...]
) -> tuple[AssessmentRef, ...]:
    references = []
    for report in reports:
        assessment = report.assessment
        for subject in assessment.request.subjects:
            owner = subject.producer
            if (
                subject.result_id != result.id
                or owner.run_id != result.provenance.run_id
                or owner.step_id != result.provenance.task_id
                or owner.output_port != result.provenance.output_port
                or subject.sha256 not in {rep.sha256 for rep in result.representations}
            ):
                continue
            counts = assessment.summary.counts
            outcome = next(
                (
                    state
                    for state in ("fail", "error", "blocked", "inconclusive")
                    if counts.get(state, 0)
                ),
                None,
            )
            if outcome is None:
                outcome = (
                    "inconclusive"
                    if not assessment.summary.evaluation_complete
                    else "pass"
                    if counts.get("pass", 0)
                    else "not_applicable"
                )
            currentness = "current" if report.currentness.is_current else "stale"
            if subject.id not in report.currentness.selected_subject_ids:
                currentness = "unresolved"
            references.append(
                AssessmentRef(
                    assessment_id=assessment.id,
                    subject_digest=canonical_digest(subject),
                    outcome=outcome,
                    currentness=currentness,
                )
            )
    return tuple(references)


def project_output(
    result: EngineeringResult, reports: tuple[ValidationReport, ...] = ()
) -> OutputRef:
    references = []
    viewers = []
    for rep in result.representations:
        if rep.kind != "workspace_file" or not rep.sha256:
            continue
        # Exact paths and hashes from the result owner, never filenames guessed
        # from logs or model prose. Native/value forms retain canonical result
        # navigation until their own supported representation reader is used.
        references.append(
            ArtifactRef(
                artifact_ref=rep.location, sha256=rep.sha256, result_id=result.id
            )
        )
        viewer = _VIEWERS.get(rep.format.lower())
        if viewer and viewer not in viewers:
            viewers.append(viewer)
    return OutputRef(
        result_id=result.id,
        step_id=result.provenance.task_id,
        port_id=result.provenance.output_port,
        role=result.artifact_role,
        title=redact_text(result.name),
        representations=tuple(references),
        assessments=_assessments(result, reports),
        supported_viewers=tuple(viewers),
    )


def _disabled(action: Action, reason: Reason) -> Action:
    return Action.model_validate(
        {**action.model_dump(), "enabled": False, "reasons": [reason, *action.reasons]}
    )


def project_interactions(
    facts: ProjectionFacts, scope: ProcessScope, *, page: str | None = None
) -> InteractionSnapshot:
    scope.require(facts.process, "process.read")
    if facts.input_snapshot and facts.input_snapshot.process != facts.process:
        raise ProcessInterfaceError(
            "SUBJECT_STALE",
            "The prepared inputs belong to another process revision.",
            "Prepare inputs for the current accepted process.",
        )
    run = facts.run
    snapshot = run.input_snapshot if run else facts.input_snapshot
    pinned_process = run.process if run else facts.process
    if snapshot and snapshot.process != pinned_process:
        raise ProcessInterfaceError(
            "SUBJECT_STALE",
            "The recorded inputs belong to another process revision.",
            "Inspect the run's exact input snapshot.",
        )
    if run and (
        run.process.workspace_id != facts.process.workspace_id
        or run.process.source_path != facts.process.source_path
    ):
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "The run belongs to another process.",
            "Attach a run from this process's workspace.",
        )
    if run and any(result.provenance.run_id != run.run_id for result in run.results):
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "A result belongs to another run.",
            "Reload the exact run's recorded results.",
        )
    if any(
        report.assessment.request.workspace_id != facts.process.workspace_id
        for report in facts.reports
    ):
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "An assessment belongs to another workspace.",
            "Reload this workspace's exact result assessments.",
        )
    if run and run.status not in _STATES:
        raise ProcessInterfaceError(
            "READINESS_UNSUPPORTED",
            "This run's recorded state is unsupported.",
            "Inspect its canonical run details before taking another action.",
        )
    state = (
        _STATES[run.status]
        if run
        else "ready"
        if facts.readiness and facts.readiness.state == "ready"
        else "preparing"
    )
    provider_observations = [
        o
        for o in facts.observations
        if o.observation_id.startswith(("operation-", "unverified-provider-"))
    ]
    if run and any(
        o.state == "reconciliation_required"
        or run.status in {"failed", "cancelled", "completed"}
        and o.state not in {"completed", "failed", "cancelled"}
        for o in provider_observations
    ):
        state = "reconciliation_required"
    elif (
        run
        and state == "running"
        and any(o.state == "cancellation_requested" for o in provider_observations)
    ):
        state = "cancellation_requested"
    elif (
        run
        and state == "running"
        and any(o.state == "waiting_external" for o in provider_observations)
    ):
        state = "waiting_external"
    outputs = tuple(
        project_output(result, facts.reports) for result in (run.results if run else ())
    )
    actions = []
    for action in facts.actions:
        if not action.enabled:
            actions.append(action)
            continue
        reason = None
        if _OPERATIONS[action.operation] not in scope.capabilities:
            reason = Reason(
                code="SCOPE_DENIED",
                message="This interface cannot perform that operation.",
                correction="Use an authorized Wright process view.",
            )
        elif (
            run
            and run.process != facts.process
            and action.operation not in {"read", "navigate", "attach"}
        ):
            reason = Reason(
                code="SOURCE_CHANGED",
                message="The accepted process has changed since this run started.",
                correction="Inspect the original run and prepare the current process before another action.",
            )
        elif state == "reconciliation_required" and action.operation in {
            "start",
            "respond",
            "review",
            "action",
        }:
            reason = Reason(
                code="OUTCOME_UNKNOWN",
                message="The previous operation's outcome has not been confirmed.",
                correction="Reconcile the recorded operation before submitting another action.",
            )
        actions.append(_disabled(action, reason) if reason else action)
    navigation = [NavigationTarget(kind="process")]
    if run:
        navigation.append(NavigationTarget(kind="run", run_id=run.run_id))
    for output in outputs:
        navigation.append(
            NavigationTarget(
                kind="result", run_id=run.run_id, result_id=output.result_id
            )
        )
        for assessment in output.assessments:
            navigation.append(
                NavigationTarget(
                    kind="assessment",
                    assessment_id=assessment.assessment_id,
                    result_id=output.result_id,
                    run_id=run.run_id,
                )
            )
        for representation in output.representations:
            navigation.append(
                NavigationTarget(
                    kind="evidence",
                    artifact_ref=representation.artifact_ref,
                    result_id=output.result_id,
                    run_id=run.run_id,
                )
            )
    for interaction in facts.interactions:
        navigation.append(
            NavigationTarget(
                kind="block",
                block_id=interaction.step_id,
                run_id=run.run_id if run else None,
            )
        )
    for diagnostic in facts.diagnostics:
        if diagnostic.navigation and diagnostic.navigation not in navigation:
            navigation.append(diagnostic.navigation)
    readiness = facts.readiness
    if readiness and (
        readiness.process != pinned_process
        or readiness.input_digest != (snapshot.digest if snapshot else None)
    ):
        readiness = None
    # An attached run's values are its retained snapshot, never another current
    # preparation. Legacy records without snapshots remain explicitly unknown.
    bindings = {item.input_id: item for item in snapshot.bindings} if snapshot else {}
    inputs = (
        tuple(
            InputDefinition.model_validate(
                {**item.model_dump(), "current_value": bindings.get(item.input_id)}
            )
            for item in facts.inputs
        )
        if pinned_process == facts.process
        else ()
    )
    context = InteractionContext(
        process=pinned_process,
        run_id=run.run_id if run else None,
        input_snapshot_id=snapshot.snapshot_id if snapshot else None,
        input_digest=snapshot.digest if snapshot else None,
        cursor=run.cursor if run else 0,
        generated_at=facts.generated_at,
    )
    collections = {
        "inputs": inputs,
        "outputs": outputs,
        "interactions": facts.interactions,
        "actions": tuple(actions),
        "observations": facts.observations,
        "diagnostics": facts.diagnostics,
        "navigation": tuple(navigation),
    }
    # A page cursor is a read reference, never a grant. Bind it to actual facts
    # and the authorized principal. Reading at a later time alone cannot expire
    # it, but changed results/permissions/recorded events require a fresh page.
    digest = canonical_digest(
        {
            "principal": scope.principal_id,
            "accepted_process": facts.process,
            "context": context.model_dump(exclude={"generated_at"}),
            "state": state,
            "readiness": readiness,
            "collections": {
                **collections,
                "observations": tuple(
                    item.model_dump(exclude={"observed_at", "stale_after"})
                    for item in facts.observations
                ),
            },
        }
    )
    largest = max((len(items) for items in collections.values()), default=0)
    offset = 0
    if page is not None:
        try:
            if not isinstance(page, str) or len(page) > 100:
                raise ValueError("Invalid page")
            version, expected, start = page.split(":")
            if (
                version != "p1"
                or expected != digest
                or not start.isascii()
                or not start.isdecimal()
            ):
                raise ValueError("Changed page")
            offset = int(start)
            if offset <= 0 or offset % 256 or offset >= largest:
                raise ValueError("Outside page")
        except ValueError as error:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "This process page no longer matches its recorded context.",
                "Reload the first interaction page and follow its current page references.",
            ) from error
    next_page = f"p1:{digest}:{offset + 256}" if offset + 256 < largest else None
    return InteractionSnapshot(
        context=context,
        state=state,
        readiness=readiness,
        next_page=next_page,
        **{name: items[offset : offset + 256] for name, items in collections.items()},
    )
