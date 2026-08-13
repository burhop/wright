from __future__ import annotations

import pytest

from model_registry.catalog import ModelCatalog
from model_registry.models import ExpectedPredicate, canonical_digest
from model_registry.testing import (
    EvidenceFailure,
    evaluate_test_vector,
    validate_mandatory_vectors,
)


def fixture():
    package = ModelCatalog.load_bundled().get("wright-affine-test").package
    assert package is not None
    variant = package.variants[0]
    vector = variant.test_vectors[0]
    return package, variant, vector


def evaluate(*, output=None, vector=None, timing_ms=1, trace_id="trace-one"):
    package, variant, default_vector = fixture()
    return evaluate_test_vector(
        package=package,
        variant=variant,
        vector=vector or default_vector,
        output=output if output is not None else {"y": 5.0},
        installation_id="installation-affine",
        installation_digest="a" * 64,
        artifact_set_digest="b" * 64,
        adapter_id="wright-deterministic",
        adapter_version="1.0.0",
        adapter_contract_version="1.0",
        environment_policy_digest="c" * 64,
        timing_ms=timing_ms,
        resources={"peak_ram_bytes": 1024},
        trace_id=trace_id,
    )


def test_vector_identity_seed_schema_units_coordinates_and_limitations_are_bound() -> (
    None
):
    package, variant, vector = fixture()
    validate_mandatory_vectors(package, variant)
    evidence = evaluate()

    assert evidence.state == "passed"
    assert evidence.material["deterministic_seed"] == 0
    assert evidence.material["input_schema_digest"] == canonical_digest(
        package.tasks[0].input_schema
    )
    assert evidence.material["output_schema_digest"] == canonical_digest(
        package.tasks[0].output_schema
    )
    assert evidence.material["units"] == {"x": "1", "y": "1"}
    assert evidence.material["limitations_exercised"] == ["test-only"]
    assert evidence.material_digest != evidence.observation_digest


@pytest.mark.parametrize(
    ("predicate", "output"),
    [
        (ExpectedPredicate(kind="exact", value={"y": 5.0}), {"y": 5.0}),
        (
            ExpectedPredicate(
                kind="absolute_tolerance", value={"y": 5.0}, absolute_tolerance=0.01
            ),
            {"y": 5.005},
        ),
        (
            ExpectedPredicate(
                kind="relative_tolerance", value={"y": 5.0}, relative_tolerance=0.01
            ),
            {"y": 5.04},
        ),
        (ExpectedPredicate(kind="range", minimum=4.0, maximum=6.0), {"y": 5.0}),
        (ExpectedPredicate(kind="category", value={"y": 5.0}), {"y": 5.0}),
    ],
)
def test_declarative_predicate_kinds_pass_without_executable_assertions(
    predicate, output
) -> None:
    _, _, vector = fixture()
    evidence = evaluate(
        vector=vector.model_copy(update={"expected": predicate}), output=output
    )
    assert evidence.state == "passed"


@pytest.mark.parametrize(
    ("change", "category"),
    [
        ({"input_schema_sha256": "0" * 64}, "test_schema_changed"),
        ({"output_schema_sha256": "0" * 64}, "test_schema_changed"),
        ({"units": {"x": "mm"}}, "test_units_changed"),
        ({"coordinate_convention": "right-handed"}, "test_coordinates_changed"),
        ({"limitations_exercised": ("missing",)}, "test_limitation_changed"),
        ({"deterministic_seed": -1}, "test_vector_invalid"),
    ],
)
def test_changed_vector_material_fails_closed(change, category) -> None:
    _, _, vector = fixture()
    if change.get("deterministic_seed") == -1:
        with pytest.raises(EvidenceFailure) as caught:
            evaluate(vector=vector.model_copy(update=change))
        assert caught.value.category == category
        return
    with pytest.raises(EvidenceFailure) as caught:
        evaluate(vector=vector.model_copy(update=change))
    assert caught.value.category == category


@pytest.mark.parametrize(
    ("output", "category"),
    [
        ({"y": 9.0}, "test_failed"),
        ({"y": float("nan")}, "non_finite_output"),
        ({"wrong": 5.0}, "output_invalid"),
    ],
)
def test_invalid_or_failed_outputs_are_not_pass_evidence(output, category) -> None:
    with pytest.raises(EvidenceFailure) as caught:
        evaluate(output=output)
    assert caught.value.category == category


def test_timing_and_observation_change_only_observation_digest() -> None:
    first = evaluate(timing_ms=1, trace_id="trace-one")
    second = evaluate(timing_ms=2, trace_id="trace-two")
    assert first.material_digest == second.material_digest
    assert first.observation_digest != second.observation_digest


def test_vector_time_and_output_limits_fail_closed() -> None:
    _, _, vector = fixture()
    with pytest.raises(EvidenceFailure) as caught:
        evaluate(timing_ms=vector.limits.inference_timeout_ms + 1)
    assert caught.value.category == "runtime_timeout"
    with pytest.raises(EvidenceFailure) as caught:
        evaluate(output={"y": 5.0, "padding": "x" * 5000})
    assert caught.value.category in {"output_invalid", "size_exceeded"}


def test_mandatory_vectors_must_cover_declared_limitations() -> None:
    package, variant, vector = fixture()
    extra = package.limitations[0].model_copy(
        update={"limitation_id": "extra-limit", "description": "Extra limitation"}
    )
    changed = package.model_copy(update={"limitations": (*package.limitations, extra)})
    with pytest.raises(EvidenceFailure) as caught:
        validate_mandatory_vectors(changed, variant)
    assert caught.value.category == "test_limitation_changed"
