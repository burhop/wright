"""One read-only validator shared by direct callers and canonical process gates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

import structlog

from core.process_validation import (
    Assessment,
    CheckResult,
    Correction,
    Finding,
    ValidationProfile,
    ValidationRequest,
    canonical_json,
    summarize,
)
from core.tracing import traced
from data_vault.process_validation_repository import AttemptRecord

from .evaluation import compare
from .readers.base import ReaderContext, ReaderRegistry, ValidationIssue
from .readers.structured import StructuredReader

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class EvaluationOutcome:
    attempt: AttemptRecord
    assessment: Assessment | None
    is_current: bool

    @property
    def release_eligible(self):
        return bool(
            self.is_current
            and self.assessment
            and self.assessment.summary.release_eligible
        )


def _finding(profile, check, issue, subject=None, measurement=None, *, evidence=()):
    sources = tuple(
        dict.fromkeys(
            source
            for requirement in profile.baseline.requirements
            if requirement.id in check.requirement_ids
            for source in requirement.sources
        )
    )
    observed = measurement.value if measurement else None
    expected = check.constraint
    target = (
        f"Set {check.selector or 'the output'} to {expected.target:g} {check.unit}, within {expected.tolerance:g} {check.unit}."
        if expected.operator == "within"
        else f"Satisfy {', '.join(check.requirement_ids)} at {check.selector or 'the output root'}: {expected.model_dump(exclude_none=True)}."
    )
    if issue.action != "revise_output":
        target = str(issue)
    return Finding(
        id="f-" + uuid4().hex,
        code=issue.code,
        check_id=check.id,
        requirement_ids=check.requirement_ids,
        state=issue.state,
        category=issue.category,
        subject_id=subject.id if subject else None,
        owner=subject.producer if subject else None,
        selector=check.selector,
        expected=expected,
        observed=observed,
        unit=check.unit,
        frame=check.frame,
        observed_unit=measurement.unit if measurement else None,
        observed_frame=measurement.frame if measurement else None,
        evidence_refs=measurement.evidence_refs if measurement else evidence,
        source_refs=sources,
        summary=str(issue),
        explanation=(
            f"Observed {str(observed)[:1024]}. {target}" if measurement else str(issue)
        ),
        correction=Correction(
            action=issue.action,
            target_step_id=subject.producer.step_id
            if subject and issue.action == "revise_output"
            else None,
            target=target,
            recheck_ids=tuple(c.id for c in profile.checks),
        ),
    )


class ProcessValidationService:
    def __init__(self, repository, resolver, *, registry=None):
        self.repository, self.resolver = repository, resolver
        if registry is None:
            registry = ReaderRegistry()
            registry.register(StructuredReader())
        self.registry = registry

    def _outcome(self, attempt):
        current = self.repository.current(
            attempt.request.workspace_id, attempt.stream_key
        )
        assessment_id = (
            current.assessment_id
            if current and current.id == attempt.id
            else attempt.assessment_id
        )
        assessment = (
            self.repository.assessment(attempt.request.workspace_id, assessment_id)
            if assessment_id
            else None
        )
        is_current = bool(current and current.id == attempt.id)
        if is_current and attempt.request.run_id:
            is_current = bool(self.resolver.verify_binding) and all(
                self.resolver.verify_binding(subject)
                for subject in attempt.request.subjects
            )
        return EvaluationOutcome(attempt, assessment, is_current)

    @traced("workspace.process_validation.evaluate")
    def evaluate(
        self, request: ValidationRequest, profile: ValidationProfile, *, cancelled=None
    ) -> EvaluationOutcome:
        # Detach caller-owned mutable JSON containers and revalidate model copies.
        request = ValidationRequest.model_validate_json(request.model_dump_json())
        profile = ValidationProfile.model_validate_json(profile.model_dump_json())
        if request.workspace_id != self.resolver.workspace_id:
            raise PermissionError(
                "Validation request is outside the authorized workspace"
            )
        if (
            request.profile_ref != profile.reference()
            or request.baseline_ref != profile.baseline.reference()
        ):
            raise ValueError("Request does not match the pinned profile and baseline")
        attempt, created = self.repository.create(request)
        if not created:
            return self._outcome(attempt)
        attempt = self.repository.start(request.workspace_id, attempt.id)
        context = ReaderContext.create(request.budget, request.trace_id, cancelled)
        try:
            assessment = self._evaluate(attempt, profile, context)
            attempt = self.repository.finalize(assessment)
        except Exception:
            # Unexpected persistence/contracts faults remain visible as a newer
            # terminal error; a former pass cannot become current again.
            self.repository.stop(
                request.workspace_id,
                attempt.id,
                "error",
                "Validation could not persist a complete assessment.",
            )
            raise
        logger.info(
            "process_validation_completed",
            trace_id=request.trace_id,
            workspace_id=request.workspace_id,
            attempt_id=attempt.id,
            assessment_id=assessment.id,
            release_eligible=assessment.summary.release_eligible,
        )
        return self._outcome(attempt)

    def _evaluate(self, attempt, profile, context):
        request = attempt.request
        subjects = {subject.role: subject for subject in request.subjects}
        snapshots, snapshot_errors = {}, {}
        measurements, results, findings = [], [], []
        total_bytes = 0
        measurement_bytes = 0
        for check in profile.checks:
            subject, measurement = subjects.get(check.subject_role), None
            evidence = ()
            try:
                context.checkpoint()
                if check.applicability_reason:
                    results.append(
                        CheckResult(
                            check_id=check.id,
                            requirement_ids=check.requirement_ids,
                            state="not_applicable",
                            applicability_reason=check.applicability_reason,
                        )
                    )
                    continue
                if profile.baseline.unresolved_decisions:
                    raise ValidationIssue(
                        "baseline.unresolved",
                        "Resolve the declared requirement decisions before acceptance.",
                        category="source_conflict",
                    )
                if check.constraint.operator == "review":
                    raise ValidationIssue(
                        "review.required",
                        "An authenticated human review is required for this requirement.",
                        category="review_required",
                        action="request_review",
                    )
                if subject is None:
                    raise ValidationIssue(
                        "subject.role_missing",
                        f"Bind the required output role '{check.subject_role}'.",
                    )
                if subject.kind not in profile.supported_kinds:
                    raise ValidationIssue(
                        "subject.kind",
                        "Profile does not support this output representation.",
                        category="capability_unavailable",
                        action="restore_capability",
                    )
                if subject.id in snapshot_errors:
                    raise snapshot_errors[subject.id]
                if subject.id not in snapshots:
                    try:
                        snapshot = self.resolver.snapshot(request, subject, context)
                        total_bytes += len(snapshot.content)
                        if total_bytes > request.budget.max_bytes:
                            raise ValidationIssue(
                                "subject.total_byte_limit",
                                "Combined inputs exceed the invocation byte budget.",
                                category="capability_unavailable",
                                action="restore_capability",
                            )
                        snapshots[subject.id] = snapshot
                    except ValidationIssue as exc:
                        snapshot_errors[subject.id] = exc
                        raise
                snapshot = snapshots[subject.id]
                evidence = (f"subject:{subject.id}@{subject.sha256}#{check.selector}",)
                measurement = self.registry.measure(snapshot, check, context)
                measurement_bytes += len(canonical_json(measurement).encode("utf-8"))
                if measurement_bytes > min(
                    4 * 1024 * 1024, request.budget.memory_limit_mb * 1024 * 1024 // 8
                ):
                    measurement = None
                    raise ValidationIssue(
                        "reader.measurement_budget",
                        "Measurements exceed the invocation result budget; select smaller regions.",
                        category="capability_unavailable",
                        action="restore_capability",
                    )
                measurements.append(measurement)
                state = compare(check, measurement, subject)
                if state != "pass":
                    raise ValidationIssue(
                        "requirement.out_of_bounds"
                        if state == "fail"
                        else "measurement.uncertain",
                        "Observed output does not meet the requirement."
                        if state == "fail"
                        else "Measurement uncertainty overlaps the acceptance boundary.",
                        state=state,
                        category="output_defect"
                        if state == "fail"
                        else "missing_evidence",
                        action="revise_output" if state == "fail" else "supply_input",
                    )
                results.append(
                    CheckResult(
                        check_id=check.id,
                        requirement_ids=check.requirement_ids,
                        state="pass",
                        measurement_ids=(measurement.id,),
                        evidence_refs=measurement.evidence_refs,
                    )
                )
                continue
            except ValidationIssue as error:
                issue = error
            except Exception as error:
                logger.error(
                    "process_validation_reader_error",
                    trace_id=request.trace_id,
                    check_id=check.id,
                    error_type=type(error).__name__,
                )
                issue = ValidationIssue(
                    "validator.unexpected_error",
                    "The validator could not complete this check; inspect its trace and retry validation.",
                    state="error",
                    category="validator_error",
                    action="retry_validation",
                )
            finding = _finding(
                profile, check, issue, subject, measurement, evidence=evidence
            )
            findings.append(finding)
            results.append(
                CheckResult(
                    check_id=check.id,
                    requirement_ids=check.requirement_ids,
                    state=issue.state,
                    measurement_ids=(measurement.id,) if measurement else (),
                    evidence_refs=measurement.evidence_refs
                    if measurement
                    else evidence,
                    finding_ids=(finding.id,),
                )
            )
        subject_current = True
        for snapshot in snapshots.values():
            try:
                self.resolver.assert_unchanged(request, snapshot, context)
            except ValidationIssue as issue:
                subject_current = False
                check = next(
                    c for c in profile.checks if c.subject_role == snapshot.subject.role
                )
                # Invocation-level readiness diagnostic preserves measured checks
                # against their snapshot; it cannot erase a known design defect.
                findings.append(_finding(profile, check, issue, snapshot.subject))
        return Assessment(
            id="assessment-" + uuid4().hex,
            attempt_id=attempt.id,
            request=request,
            profile=profile,
            created_at=datetime.now(timezone.utc).isoformat(),
            measurements=tuple(measurements),
            checks=tuple(results),
            findings=tuple(findings),
            subject_current=subject_current,
            summary=summarize(profile, tuple(results), subject_current=subject_current),
        )
