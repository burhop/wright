"""Deterministic comparison of independently obtained, typed observations."""

from decimal import Decimal

from pydantic import ValidationError

from core.engineering_scenarios import (
    ArtifactProducer,
    AssertionState,
    EngineeringScenarioError,
    NormalizedArtifact,
    convert_unit,
)
from core.process_validation import canonical_digest
from core.image_coordinates import ImageCoordinateFrame

from ..engineering_scenario_assertions import EngineeringAssertionRegistry
from .readers.base import ValidationIssue


def _same_json(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _same_json(left[k], right[k]) for k in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _same_json(a, b) for a, b in zip(left, right)
        )
    return left == right


def compare(check, measurement, subject):
    value, rule = measurement.value, check.constraint
    if check.unit == "px":
        try:
            image_frame = ImageCoordinateFrame.model_validate(
                check.parameters.get("image_frame")
            )
        except ValidationError as exc:
            raise ValidationIssue(
                "profile.image_frame",
                "Pixel checks require an exact image coordinate frame.",
                state="inconclusive",
                category="source_conflict",
            ) from exc
        if check.frame != image_frame.identifier() or rule.operator not in {
            "within",
            "range",
        }:
            raise ValidationIssue(
                "profile.image_frame",
                "Pixel checks require a matching frame identity and numeric constraint.",
                state="inconclusive",
                category="source_conflict",
            )
    if check.frame and measurement.frame != check.frame:
        raise ValidationIssue(
            "measurement.frame",
            "Observed and required datum frames differ; provide an established transform.",
            state="inconclusive",
            category="source_conflict",
        )
    if rule.operator == "exists":
        return "pass"
    if rule.operator == "equals":
        return "pass" if _same_json(value, rule.expected) else "fail"
    if rule.operator == "type":
        matched = {
            "object": isinstance(value, dict),
            "array": isinstance(value, list),
            "string": isinstance(value, str),
            "number": type(value) in {int, float},
            "boolean": isinstance(value, bool),
            "null": value is None,
        }
        return "pass" if matched[rule.expected] else "fail"
    if rule.operator == "review":
        raise ValidationIssue(
            "review.required",
            "An authenticated human decision is required.",
            category="review_required",
            action="request_review",
        )
    if type(value) not in {int, float}:
        return "fail"
    if not measurement.unit:
        raise ValidationIssue(
            "measurement.unit",
            "Numeric observation has no declared unit.",
            state="inconclusive",
            category="missing_evidence",
        )
    try:
        low = convert_unit(
            Decimal(str(value)) - Decimal(str(measurement.uncertainty)),
            measurement.unit,
            check.unit,
        )
        high = convert_unit(
            Decimal(str(value)) + Decimal(str(measurement.uncertainty)),
            measurement.unit,
            check.unit,
        )
        center = convert_unit(value, measurement.unit, check.unit)
    except EngineeringScenarioError as exc:
        raise ValidationIssue(
            "measurement.unit",
            "Observed unit cannot be converted to the required measurement dimension.",
            state="inconclusive",
            category="source_conflict",
        ) from exc
    if rule.operator == "within":
        minimum = Decimal(str(rule.target)) - Decimal(str(rule.tolerance))
        maximum = Decimal(str(rule.target)) + Decimal(str(rule.tolerance))
    else:
        minimum = Decimal(str(rule.minimum)) if rule.minimum is not None else None
        maximum = Decimal(str(rule.maximum)) if rule.maximum is not None else None
    inside = (
        minimum is None or (low >= minimum if rule.inclusive else low > minimum)
    ) and (maximum is None or (high <= maximum if rule.inclusive else high < maximum))
    outside = (
        minimum is not None and (high < minimum if rule.inclusive else high <= minimum)
    ) or (maximum is not None and (low > maximum if rule.inclusive else low >= maximum))
    if measurement.uncertainty or not rule.inclusive:
        return "pass" if inside else "fail" if outside else "inconclusive"
    # Adapt the existing versioned numeric predicate only after real readback.
    # Its ERROR state remains an evaluator error, never a design failure.
    numeric_rule = {"kind": "range", "path": "value", "unit": check.unit}
    if minimum is not None:
        numeric_rule["minimum"] = str(minimum)
    if maximum is not None:
        numeric_rule["maximum"] = str(maximum)
    content = {"value": str(center)}
    artifact = NormalizedArtifact(
        artifact_id=measurement.id,
        domain="process-validation",
        kind="measurement",
        source_schema={"name": "wright-process-measurement", "version": "1"},
        producer=ArtifactProducer(
            subject.producer.run_id,
            subject.producer.step_id,
            measurement.id,
            measurement.reader.id,
        ),
        upstream_digests=(subject.sha256,),
        content_digest=canonical_digest(content),
        validation_state="valid",
        content=content,
        units={"value": check.unit},
    )
    result = EngineeringAssertionRegistry().evaluate(
        {
            "assertion_id": check.id,
            "plugin": "numeric",
            "plugin_version": "1.0",
            "artifact_ids": [artifact.artifact_id],
            "rule": numeric_rule,
        },
        {artifact.artifact_id: artifact},
    )
    if result.state not in {AssertionState.PASS, AssertionState.FAIL}:
        raise ValidationIssue(
            "validator.numeric",
            "Numeric comparison could not be evaluated.",
            state="error",
            category="validator_error",
            action="retry_validation",
        )
    return result.state.value
