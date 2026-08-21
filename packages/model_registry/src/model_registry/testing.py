"""Deterministic, declarative test-vector evaluation and bounded evidence."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from jsonschema import ValidationError, validate  # type: ignore[import-untyped]

from .models import (
    ExpectedPredicate,
    ModelPackage,
    ModelTestVector,
    ModelVariant,
    canonical_digest,
)


class EvidenceFailure(RuntimeError):
    def __init__(self, category: str, message: str) -> None:
        super().__init__(message)
        self.category = category


@dataclass(frozen=True, slots=True)
class ModelValidationEvidence:
    state: str
    material_digest: str
    observation_digest: str
    material: Mapping[str, Any]
    observation: Mapping[str, Any]

    def projection(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "state": self.state,
            "material_digest": self.material_digest,
            "observation_digest": self.observation_digest,
            "material": dict(self.material),
            "observation": dict(self.observation),
        }


def _finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite(item) for item in value)
    return True


def _numeric_compare(
    actual: Any,
    expected: Any,
    *,
    absolute: float | None = None,
    relative: float | None = None,
) -> bool:
    if isinstance(expected, Mapping):
        return (
            isinstance(actual, Mapping)
            and set(actual) == set(expected)
            and all(
                _numeric_compare(
                    actual[key], expected[key], absolute=absolute, relative=relative
                )
                for key in expected
            )
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(
                _numeric_compare(a, e, absolute=absolute, relative=relative)
                for a, e in zip(actual, expected, strict=True)
            )
        )
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        if not isinstance(actual, (int, float)) or isinstance(actual, bool):
            return False
        difference = abs(float(actual) - float(expected))
        if absolute is not None:
            return difference <= absolute
        if relative is not None:
            return difference <= relative * max(abs(float(expected)), 1e-15)
    return actual == expected


def _single_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, Mapping) and len(value) == 1:
        return _single_number(next(iter(value.values())))
    return None


def _predicate_passes(predicate: ExpectedPredicate, output: Mapping[str, Any]) -> bool:
    if predicate.kind in {"exact", "category"}:
        return _numeric_compare(output, predicate.value)
    if predicate.kind == "absolute_tolerance":
        return _numeric_compare(
            output, predicate.value, absolute=predicate.absolute_tolerance
        )
    if predicate.kind == "relative_tolerance":
        return _numeric_compare(
            output, predicate.value, relative=predicate.relative_tolerance
        )
    if predicate.kind == "range":
        actual = _single_number(output)
        return (
            actual is not None
            and predicate.minimum is not None
            and predicate.maximum is not None
            and predicate.minimum <= actual <= predicate.maximum
        )
    return False


def _task(package: ModelPackage, task_id: str):
    for task in package.tasks:
        if task.task_id == task_id:
            return task
    raise EvidenceFailure("test_task_changed", "Test task is unavailable")


def validate_mandatory_vectors(
    package: ModelPackage, variant: ModelVariant
) -> tuple[ModelTestVector, ...]:
    mandatory = tuple(vector for vector in variant.test_vectors if vector.mandatory)
    if not mandatory:
        raise EvidenceFailure(
            "test_vector_invalid", "Mandatory test evidence is missing"
        )
    declared = {item.limitation_id for item in package.limitations}
    exercised = {
        limitation
        for vector in mandatory
        for limitation in vector.limitations_exercised
    }
    if exercised != declared:
        raise EvidenceFailure(
            "test_limitation_changed",
            "Mandatory vectors do not cover the declared limitations",
        )
    for vector in mandatory:
        task = _task(package, vector.task_id)
        if vector.input_schema_sha256 != canonical_digest(task.input_schema) or (
            vector.output_schema_sha256 != canonical_digest(task.output_schema)
        ):
            raise EvidenceFailure(
                "test_schema_changed", "Test vector schema identity changed"
            )
        if dict(vector.units) != dict(task.units):
            raise EvidenceFailure("test_units_changed", "Test vector units changed")
        if vector.coordinate_convention != task.coordinate_convention:
            raise EvidenceFailure(
                "test_coordinates_changed", "Test coordinate convention changed"
            )
        if (
            isinstance(vector.deterministic_seed, int) and vector.deterministic_seed < 0
        ) or (
            isinstance(vector.deterministic_seed, str)
            and not 1 <= len(vector.deterministic_seed) <= 128
        ):
            raise EvidenceFailure(
                "test_vector_invalid", "Deterministic seed is invalid"
            )
    return mandatory


def evaluate_test_vector(
    *,
    package: ModelPackage,
    variant: ModelVariant,
    vector: ModelTestVector,
    output: Mapping[str, Any],
    installation_id: str,
    installation_digest: str,
    artifact_set_digest: str,
    adapter_id: str,
    adapter_version: str,
    adapter_contract_version: str,
    environment_policy_digest: str,
    timing_ms: int,
    resources: Mapping[str, Any],
    trace_id: str,
) -> ModelValidationEvidence:
    validate_mandatory_vectors(package, variant)
    task = _task(package, vector.task_id)
    declared = {item.limitation_id for item in package.limitations}
    if not set(vector.limitations_exercised) <= declared:
        raise EvidenceFailure(
            "test_limitation_changed", "Test limitation identity changed"
        )
    if vector.input_schema_sha256 != canonical_digest(task.input_schema) or (
        vector.output_schema_sha256 != canonical_digest(task.output_schema)
    ):
        raise EvidenceFailure("test_schema_changed", "Test schema identity changed")
    if dict(vector.units) != dict(task.units):
        raise EvidenceFailure("test_units_changed", "Test vector units changed")
    if vector.coordinate_convention != task.coordinate_convention:
        raise EvidenceFailure(
            "test_coordinates_changed", "Test coordinate convention changed"
        )
    if (
        isinstance(vector.deterministic_seed, int) and vector.deterministic_seed < 0
    ) or (
        isinstance(vector.deterministic_seed, str)
        and not 1 <= len(vector.deterministic_seed) <= 128
    ):
        raise EvidenceFailure("test_vector_invalid", "Deterministic seed is invalid")
    if not _finite(output):
        raise EvidenceFailure(
            "non_finite_output", "Test output contains non-finite values"
        )
    try:
        validate(instance=vector.input, schema=task.input_schema)
        validate(instance=dict(output), schema=task.output_schema)
    except ValidationError as error:
        raise EvidenceFailure(
            "output_invalid", "Test input or output is invalid"
        ) from error
    encoded_output = json.dumps(
        dict(output), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(encoded_output) > vector.limits.max_output_bytes:
        raise EvidenceFailure("size_exceeded", "Test output exceeds its byte limit")
    if timing_ms < 0 or timing_ms > vector.limits.inference_timeout_ms:
        raise EvidenceFailure("runtime_timeout", "Test inference exceeded its deadline")
    if not _finite(resources):
        raise EvidenceFailure("output_invalid", "Resource observation is invalid")
    if not _predicate_passes(vector.expected, dict(output)):
        raise EvidenceFailure("test_failed", "Mandatory test predicate failed")

    material = {
        "schema_version": "1.0",
        "installation_id": installation_id,
        "installation_digest": installation_digest,
        "model_id": package.model_id,
        "package_revision": package.package_revision,
        "variant_id": variant.variant_id,
        "manifest_digest": package.digest,
        "artifact_set_digest": artifact_set_digest,
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
        "adapter_contract_version": adapter_contract_version,
        "environment_policy_digest": environment_policy_digest,
        "vector_id": vector.vector_id,
        "vector_version": vector.version,
        "task_id": vector.task_id,
        "deterministic_seed": vector.deterministic_seed,
        "input_schema_digest": vector.input_schema_sha256,
        "output_schema_digest": vector.output_schema_sha256,
        "input_digest": canonical_digest(vector.input),
        "output_digest": canonical_digest(dict(output)),
        "predicate": vector.expected.model_dump(mode="json", exclude_none=True),
        "limits": vector.limits.model_dump(mode="json"),
        "units": dict(vector.units),
        "coordinate_convention": vector.coordinate_convention,
        "limitations_exercised": list(vector.limitations_exercised),
        "result": "passed",
    }
    material_digest = canonical_digest(material)
    observation = {
        "material_digest": material_digest,
        "timing_ms": timing_ms,
        "resources": dict(resources),
        "trace_id": trace_id,
    }
    observation_digest = canonical_digest(observation)
    return ModelValidationEvidence(
        "passed",
        material_digest,
        observation_digest,
        material,
        observation,
    )


__all__ = [
    "EvidenceFailure",
    "ModelValidationEvidence",
    "evaluate_test_vector",
    "validate_mandatory_vectors",
]
