"""Conditional input cannot expand its fixed response fields or trust model prose."""

import pytest

from core.workflow_input_conditions import (
    ConditionalInputEvaluation,
    HumanInputCondition,
    validate_requirements_resolution,
)


SCHEMA = {
    "type": "object",
    "properties": {
        "material": {"type": "string", "enum": ["steel", "aluminum"]},
        "width_mm": {"type": "number", "minimum": 10, "maximum": 100},
    },
    "required": ["material", "width_mm"],
    "additionalProperties": False,
}
CONDITION = HumanInputCondition(
    kind="unresolved_fields",
    source="analysis.requirements",
    fields=("material", "width_mm"),
)


def test_known_values_are_validated_but_wait_keeps_the_complete_answer_schema():
    before = repr(SCHEMA)
    result = validate_requirements_resolution(
        CONDITION,
        SCHEMA,
        {
            "version": "wright.requirements-resolution/1",
            "unresolved_fields": ["material"],
            "resolved_values": {"width_mm": 50},
        },
    )
    assert result.unresolved_fields == ("material",)
    assert result.resolved_values == {"width_mm": 50}
    assert repr(SCHEMA) == before and SCHEMA["required"] == ["material", "width_mm"]


@pytest.mark.parametrize(
    "values",
    [
        {"width_mm": 9},
        {"width_mm": "50"},
        {"width_mm": float("nan")},
        {},
        {"width_mm": 50, "material": "steel"},
    ],
)
def test_partial_resolution_must_supply_valid_known_values_without_overlapping_unresolved(
    values,
):
    with pytest.raises(ValueError):
        validate_requirements_resolution(
            CONDITION,
            SCHEMA,
            {
                "version": "wright.requirements-resolution/1",
                "unresolved_fields": ["material"],
                "resolved_values": values,
            },
        )


@pytest.mark.parametrize(
    "values",
    [
        {"width_mm": 50},
        {"width_mm": 50, "material": "plastic"},
        {"width_mm": 50, "material": "steel", "new_requirement": True},
    ],
)
def test_skip_requires_the_whole_original_response_schema(values):
    with pytest.raises(ValueError):
        validate_requirements_resolution(
            CONDITION,
            SCHEMA,
            {
                "version": "wright.requirements-resolution/1",
                "unresolved_fields": [],
                "resolved_values": values,
            },
        )


def test_evaluation_cannot_claim_skip_for_unresolved_fields():
    with pytest.raises(ValueError, match="decision"):
        ConditionalInputEvaluation(
            version="wright.input-condition-evaluation/1",
            source="analysis.requirements",
            source_digest="a" * 64,
            decision="skip",
            unresolved_fields=("material",),
            resolved_values={"width_mm": 50},
        )
