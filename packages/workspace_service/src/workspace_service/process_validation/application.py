"""Workspace-bound composition shared by process execution, CLI and transports."""

from core.process_validation import ValidationRequest, canonical_digest
from data_vault.process_validation_repository import ProcessValidationRepository

from .configuration import ProfileLocation
from .profiles import load_profile
from .service import ProcessValidationService
from .subjects import SubjectResolver


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
        report = self.service.get_result(assessment_id)
        return report.assessment, report.currentness.is_current

    def get_result(self, assessment_id):
        return self.service.get_result(assessment_id)

    def list_findings(self, assessment_id, *, cursor=0, limit=20):
        return self.service.list_findings(assessment_id, cursor=cursor, limit=limit)

    def export_result(self, assessment_id, format):
        return self.service.export_result(assessment_id, format)

    def record_review(self, assessment_id, **kwargs):
        return self.service.record_review(assessment_id, **kwargs)


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
