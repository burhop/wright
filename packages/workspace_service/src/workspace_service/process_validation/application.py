"""Workspace-bound composition shared by process execution, CLI and transports."""

from core.process_validation import ValidationRequest, canonical_digest
from data_vault.process_validation_repository import ProcessValidationRepository

from .configuration import ProfileLocation
from .profiles import load_profile
from .service import ProcessValidationService
from .subjects import SubjectResolver
from .readers.base import ReaderContext, ValidationIssue


class ValidationApplication:
    def __init__(
        self,
        db_path,
        workspace_id,
        workspace_root,
        *,
        registry=None,
        provider_readback=None,
    ):
        self.workspace_id = workspace_id
        self.workspace_root = workspace_root
        self.repository = ProcessValidationRepository(db_path)
        self.service = ProcessValidationService(
            self.repository,
            SubjectResolver(
                workspace_id,
                workspace_root,
                verify_binding=lambda subject: self.repository.output_is_current(
                    workspace_id, subject
                ),
                provider_readback=provider_readback,
            ),
            registry=registry,
        )

    def evaluate(
        self, request: ValidationRequest, location: ProfileLocation, *, cancelled=None
    ):
        if request.workspace_id != self.workspace_id:
            raise PermissionError("Validation request is outside this workspace")
        profile = load_profile(
            location.name,
            expected=location.reference,
            workspace_root=self.workspace_root
            if location.source == "workspace"
            else None,
        )
        return self.service.evaluate(request, profile, cancelled=cancelled)

    def read(self, assessment_id):
        assessment = self.repository.assessment(self.workspace_id, assessment_id)
        attempt = self.repository.get(self.workspace_id, assessment.attempt_id)
        current = self.repository.current(self.workspace_id, attempt.stream_key)
        is_current = bool(
            current
            and current.id == attempt.id
            and current.assessment_id == assessment.id
        )
        if assessment.request.run_id:
            is_current = is_current and all(
                self.repository.output_is_current(self.workspace_id, subject)
                for subject in assessment.request.subjects
            )
        if is_current:
            context = ReaderContext.create(
                assessment.request.budget, assessment.request.trace_id
            )
            try:
                for subject in assessment.request.subjects:
                    self.service.resolver.snapshot(assessment.request, subject, context)
            except (ValidationIssue, OSError):
                is_current = False
        return assessment, is_current


def assessment_reference(assessment, is_current):
    return {
        "schema_version": "wright.process-validation/1",
        "assessment_id": assessment.id,
        "assessment_digest": canonical_digest(assessment),
        "attempt_id": assessment.attempt_id,
        "workspace_id": assessment.request.workspace_id,
        "is_current": is_current,
        "release_eligible": bool(is_current and assessment.summary.release_eligible),
        "summary": assessment.summary.model_dump(mode="json"),
        "finding_count": len(assessment.findings),
    }
