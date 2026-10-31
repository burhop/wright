"""One read-only validator shared by direct callers and canonical process gates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import uuid4

import structlog

from core.process_validation import (
    Assessment,
    AssessmentCurrentness,
    AssessmentReference,
    CheckResult,
    Correction,
    Finding,
    FindingPage,
    ReviewDecision,
    ValidationProfile,
    ValidationRequest,
    canonical_digest,
    canonical_json,
    summarize,
)
from core.tracing import traced
from data_vault.process_validation_repository import AttemptRecord

from .evaluation import compare
from .readers.base import ReaderContext, ReaderRegistry, ValidationIssue
from .readers.cfd import CfdEvidenceReader
from .readers.geometry import StepSeatGeometryReader
from .readers.harness import HarnessReader
from .readers.kicad import KiCadReader
from .readers.printing import PrintingArtifactReader
from .readers.sheet_metal import SheetMetalEvidenceReader
from .readers.structured import StructuredReader
from .readers.json_container import JsonContainerReader
from .readers.step_box import StepBoundingBoxReader
from .readers.structural import StructuralEvidenceReader
from .readers.thermal import ThermalFieldReader
from .readers.tracking import TrackingTimelineReader
from .readers.water_heater import WaterHeaterTimelineReader
from .reporting import build_report, export_report

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
        f"Required at {check.selector or 'the output'}: {expected.target:g} {check.unit}, within {expected.tolerance:g} {check.unit}."
        if expected.operator == "within"
        else f"Required by {', '.join(check.requirement_ids)} at {check.selector or 'the output root'}: {expected.model_dump(exclude_none=True)}."
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
            f"Observed {str(observed)[:1024]}{(' ' + measurement.unit) if measurement.unit else ''}. {target}"
            if measurement
            else str(issue)
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


def default_reader_registry() -> ReaderRegistry:
    """The same installed readers for workflow preparation and evaluation."""
    registry = ReaderRegistry()
    registry.register(StructuredReader())
    registry.register(JsonContainerReader())
    registry.register(CfdEvidenceReader())
    registry.register(StepSeatGeometryReader())
    registry.register(HarnessReader())
    registry.register(KiCadReader())
    registry.register(PrintingArtifactReader())
    registry.register(SheetMetalEvidenceReader())
    registry.register(StepBoundingBoxReader())
    registry.register(StructuralEvidenceReader())
    registry.register(ThermalFieldReader())
    registry.register(TrackingTimelineReader())
    registry.register(WaterHeaterTimelineReader())
    return registry


class ProcessValidationService:
    def __init__(self, repository, resolver, *, registry=None):
        self.repository, self.resolver = repository, resolver
        self.registry = default_reader_registry() if registry is None else registry

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

    def currentness(self, assessment: Assessment) -> AssessmentCurrentness:
        workspace_id = assessment.request.workspace_id
        attempt = self.repository.get(workspace_id, assessment.attempt_id)
        latest = self.repository.current(workspace_id, attempt.stream_key)
        stale_reason = None
        if latest is None or latest.id != attempt.id:
            stale_reason = "newer_validation_attempt"
        elif latest.assessment_id != assessment.id:
            stale_reason = "superseded_by_review"
        elif not assessment.subject_current:
            stale_reason = "subject_changed_during_validation"
        elif assessment.request.run_id and not all(
            self.repository.output_is_current(workspace_id, subject)
            for subject in assessment.request.subjects
        ):
            stale_reason = "subject_revision_changed"
        elif assessment.request.subjects:
            context = ReaderContext.create(
                assessment.request.budget, assessment.request.trace_id
            )
            try:
                for subject in assessment.request.subjects:
                    self.resolver.snapshot(assessment.request, subject, context)
            except (ValidationIssue, OSError):
                stale_reason = "subject_unavailable"
        return AssessmentCurrentness(
            as_of=datetime.now(timezone.utc).isoformat(),
            selected_assessment_id=assessment.id,
            selected_attempt_id=assessment.attempt_id,
            selected_subject_ids=tuple(
                subject.id for subject in assessment.request.subjects
            ),
            latest_attempt_id=latest.id if latest else attempt.id,
            latest_assessment_id=latest.assessment_id if latest else None,
            superseded_by=self.repository.assessment_successors(
                workspace_id, assessment.id
            ),
            is_current=stale_reason is None,
            stale_reason=stale_reason,
        )

    @traced("workspace.process_validation.get_result")
    def get_result(self, assessment_id: str):
        assessment = self.repository.assessment(
            self.resolver.workspace_id, assessment_id
        )
        return build_report(assessment, self.currentness(assessment))

    @traced("workspace.process_validation.list_findings")
    def list_findings(
        self, assessment_id: str, *, cursor: int = 0, limit: int = 20
    ) -> FindingPage:
        if not 0 <= cursor or not 1 <= limit <= 20:
            raise ValueError("Finding page requires cursor >= 0 and limit 1..20")
        report = self.get_result(assessment_id)
        items = []
        for finding in report.assessment.findings[cursor : cursor + limit]:
            candidate = finding.model_dump(mode="json")
            if len(canonical_json([*items, candidate]).encode("utf-8")) > 64 * 1024:
                if not items:
                    raise ValueError(
                        "Finding exceeds inline capacity; use the authorized JSON export"
                    )
                break
            items.append(candidate)
        end = cursor + len(items)
        return FindingPage(
            **self.reference(report.assessment, report.currentness).model_dump(),
            findings=tuple(items),
            next_cursor=end if end < len(report.assessment.findings) else None,
        )

    @staticmethod
    def reference(
        assessment: Assessment, currentness: AssessmentCurrentness
    ) -> AssessmentReference:
        return AssessmentReference(
            assessment_id=assessment.id,
            assessment_digest=canonical_digest(assessment),
            attempt_id=assessment.attempt_id,
            workspace_id=assessment.request.workspace_id,
            is_current=currentness.is_current,
            release_eligible=bool(
                currentness.is_current and assessment.summary.release_eligible
            ),
            summary=assessment.summary,
            finding_count=len(assessment.findings),
        )

    @traced("workspace.process_validation.export")
    def export_result(self, assessment_id: str, format: str):
        return export_report(self.get_result(assessment_id), format)

    @traced("workspace.process_validation.review")
    def record_review(
        self,
        assessment_id: str,
        *,
        requirement_id: str,
        actor_id: str,
        authority_ref: str,
        decision: str,
        rationale: str,
        evidence_refs: tuple[str, ...],
    ) -> Assessment:
        original = self.repository.assessment(self.resolver.workspace_id, assessment_id)
        if not self.currentness(original).is_current:
            raise ValueError("Review requires the current validation assessment")
        review = ReviewDecision(
            id="review-" + uuid4().hex,
            workspace_id=self.resolver.workspace_id,
            assessment_id=original.id,
            assessment_digest=canonical_digest(original),
            requirement_id=requirement_id,
            actor_id=actor_id,
            actor_type="authenticated_human",
            authority_ref=authority_ref,
            decision=decision,
            rationale=rationale,
            evidence_refs=evidence_refs,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        requirements = {
            item.id: item for item in original.profile.baseline.requirements
        }
        requirement = requirements.get(requirement_id)
        if requirement is None or not requirement.review_required:
            raise ValueError("Requirement does not accept human review")
        definitions = {item.id: item for item in original.profile.checks}
        subjects = {item.role: item for item in original.request.subjects}
        eligible = {
            item.id
            for item in original.profile.checks
            if item.constraint.operator == "review"
            and requirement_id in item.requirement_ids
        }
        if not eligible:
            raise ValueError("Requirement has no pending review check")
        checks, findings = (
            [],
            [item for item in original.findings if item.check_id not in eligible],
        )
        for check in original.checks:
            if check.check_id not in eligible:
                checks.append(check)
                continue
            definition = definitions[check.check_id]
            evidence = tuple(dict.fromkeys((review.id, *review.evidence_refs)))
            finding_ids = ()
            if review.decision == "changes_requested":
                subject = subjects.get(definition.subject_role)
                finding = Finding(
                    id="f-" + uuid4().hex,
                    code="review.changes_requested",
                    check_id=definition.id,
                    requirement_ids=definition.requirement_ids,
                    state="fail",
                    category="review_required",
                    subject_id=subject.id if subject else None,
                    owner=subject.producer if subject else None,
                    selector=definition.selector,
                    expected=definition.constraint,
                    unit=definition.unit,
                    frame=definition.frame,
                    evidence_refs=evidence,
                    source_refs=requirement.sources,
                    summary="Authenticated review requested changes.",
                    explanation=review.rationale,
                    correction=Correction(
                        action="request_review",
                        target="Address the authenticated review rationale and submit a new output for validation.",
                        recheck_ids=tuple(item.id for item in original.profile.checks),
                    ),
                )
                findings.append(finding)
                finding_ids = (finding.id,)
            checks.append(
                CheckResult(
                    check_id=check.check_id,
                    requirement_ids=check.requirement_ids,
                    state="pass" if review.decision == "approved" else "fail",
                    evidence_refs=evidence,
                    finding_ids=finding_ids,
                )
            )
        revised = Assessment(
            **{
                **original.model_dump(),
                "id": "assessment-" + uuid4().hex,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "checks": tuple(checks),
                "findings": tuple(findings),
                "review_ids": (*original.review_ids, review.id),
                "supersedes": original.id,
                "summary": summarize(
                    original.profile,
                    tuple(checks),
                    subject_current=original.subject_current,
                ),
            }
        )
        self.repository.append_review(review, revised)
        return revised

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

        def resolve(subject):
            nonlocal total_bytes
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
            return snapshots[subject.id]

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
                snapshot = resolve(subject)
                related_roles = check.parameters.get("related_roles", [])
                if not isinstance(related_roles, list) or any(
                    not isinstance(role, str) for role in related_roles
                ):
                    raise ValidationIssue(
                        "profile.related_roles",
                        "Related roles must be a list of bound subject-role names.",
                        category="source_conflict",
                    )
                related = []
                for role in related_roles:
                    related_subject = subjects.get(role)
                    if related_subject is None:
                        raise ValidationIssue(
                            "subject.related_role_missing",
                            f"Bind the required related output role '{role}'.",
                        )
                    related.append(resolve(related_subject))
                evidence = (f"subject:{subject.id}@{subject.sha256}#{check.selector}",)
                measurement = self.registry.measure(
                    snapshot,
                    check,
                    replace(context, related_snapshots=tuple(related)),
                )
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
