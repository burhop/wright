"""Export the public validator contracts from their authoritative core models."""

import json
from pathlib import Path

from core.process_validation import (
    Assessment,
    AssessmentReference,
    FindingPage,
    RepairFeedback,
    ReviewDecision,
    ValidationReport,
    ValidationProfile,
    ValidationRequest,
)


def export(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for model in (
        ValidationRequest,
        ValidationProfile,
        Assessment,
        AssessmentReference,
        FindingPage,
        RepairFeedback,
        ReviewDecision,
        ValidationReport,
    ):
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"urn:wright:process-validation:1:{model.__name__}"
        (target / f"{model.__name__}.schema.json").write_text(
            json.dumps(schema, indent=2) + "\n", encoding="utf-8"
        )


def export_authoring_profiles(target: Path) -> None:
    """Build frontend choices from the same packaged profiles used at runtime."""
    from importlib.resources import files
    from workspace_service.process_validation.profiles import load_profile

    choices = []
    for resource in sorted(
        files("workspace_service.process_validation").joinpath("profiles").iterdir(),
        key=lambda p: p.name,
    ):
        if resource.suffix != ".json" or resource.name == "coverage.json":
            continue
        profile = load_profile(resource.stem)
        choices.append(
            {
                "name": resource.stem,
                "title": profile.id.replace("-", " ").title(),
                "profile_ref": profile.reference().model_dump(),
                "baseline_ref": profile.baseline.reference().model_dump(),
                "roles": sorted({check.subject_role for check in profile.checks}),
                "limitations": list(profile.limitations),
                "excluded_scope": list(profile.excluded_scope),
            }
        )
    target.write_text(json.dumps(choices, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    export(
        Path(__file__).resolve().parents[1]
        / "specs/082-output-content-validation/contracts/schemas"
    )
    export_authoring_profiles(
        Path(__file__).resolve().parents[1]
        / "apps/web/src/prototypes/workflow-recovery/validation-profiles.json"
    )
