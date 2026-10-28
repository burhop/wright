"""Measure an analysis field against its exact submitted design and basis.

This proves the recorded input linkage and field value, not solver correctness,
material suitability or physical safety. Those require separate profile checks.
"""

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue
from .structural import _displacements, _stresses


class DesignResponseReader:
    identity = ReaderIdentity(
        id="design-response",
        version="1",
        config_digest=canonical_digest(
            {
                "version": 1,
                "operations": ["stress_maximum", "displacement_maximum"],
                "binding": "verified submitted design and explicit basis input digests",
            }
        ),
        method="independent_measurement",
        tool_identity="wright exact-design analysis field reader v1",
        formats=("step", "stp", "stl"),
    )

    def measure(self, snapshot, check, context):
        related = {item.subject.role: item for item in context.related_snapshots}
        field_role = check.parameters.get("field_role")
        basis_roles = check.parameters.get("basis_roles")
        operation = check.parameters.get("operation")
        expected_unit = {"stress_maximum": "MPa", "displacement_maximum": "mm"}.get(
            operation
        )
        if (
            expected_unit is None
            or check.unit != expected_unit
            or not isinstance(field_role, str)
            or not isinstance(basis_roles, list)
            or not basis_roles
            or any(not isinstance(role, str) for role in basis_roles)
            or len(set(basis_roles)) != len(basis_roles)
            or field_role in basis_roles
        ):
            raise ValidationIssue(
                "profile.design_response",
                "Declare the analysis field, distinct basis roles and supported units.",
                category="source_conflict",
            )
        field = related.get(field_role)
        if field is None or any(role not in related for role in basis_roles):
            raise ValidationIssue(
                "design_response.missing_evidence",
                "Bind the analysis field and every declared analysis-basis input.",
            )
        required = (snapshot, *(related[role] for role in basis_roles))
        if (
            field.subject.producer.run_id != snapshot.subject.producer.run_id
            or field.subject.producer.step_id == snapshot.subject.producer.step_id
            or field.subject.format != "csv"
            or any(
                item.subject.sha256 not in field.subject.input_digests
                for item in required
            )
        ):
            raise ValidationIssue(
                "design_response.input_mismatch",
                "The analysis field is not linked to this exact design and analysis basis. Recheck the analysis inputs.",
                category="source_conflict",
            )
        try:
            count, value = (
                _stresses(field)
                if operation == "stress_maximum"
                else _displacements(field)
            )
        except ValidationIssue as error:
            # Broken solver output is not an evidenced geometry defect.
            raise ValidationIssue(
                "design_response.invalid_analysis",
                "The analysis field cannot establish a design result. Correct its evidence before changing CAD.",
            ) from error
        context.checkpoint(entities=count)
        evidence = tuple(
            f"subject:{item.subject.id}@{item.subject.sha256}"
            for item in (*required, field)
        )
        return Measurement(
            id="m-"
            + canonical_digest(
                {
                    "subject": snapshot.subject,
                    "field": field.subject,
                    "basis": tuple(item.subject for item in required[1:]),
                    "check": check,
                    "reader": self.identity,
                }
            ),
            subject_id=snapshot.subject.id,
            subject_sha256=snapshot.subject.sha256,
            selector=check.selector,
            value=value,
            unit=expected_unit,
            frame=check.frame,
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=evidence,
        )
