"""Export the public validator contracts from their authoritative core models."""

import json
from pathlib import Path

from core.process_validation import (
    Assessment,
    AssessmentReference,
    FindingPage,
    RepairFeedback,
    ReviewDecision,
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
    ):
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"urn:wright:process-validation:1:{model.__name__}"
        (target / f"{model.__name__}.schema.json").write_text(
            json.dumps(schema, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    export(
        Path(__file__).resolve().parents[1]
        / "specs/082-output-content-validation/contracts/schemas"
    )
