from __future__ import annotations

import copy

import pytest
from model_registry.chatter_runtime import load_forest, predict_batch
from model_registry.generated import (
    chatter_fixture_artifacts,
    generated_chatter_package,
)
from model_registry.runtime import (
    RuntimeSupervisor,
    built_in_runtime_registry,
    current_runtime_platform,
)


def _runtime(tmp_path):
    package = generated_chatter_package()
    for name, value in chatter_fixture_artifacts(package).items():
        target = tmp_path.joinpath(*name.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    metadata, arrays = load_forest(tmp_path)
    vector = package.variants[0].test_vectors[0]
    return metadata, arrays, vector


def test_threshold_equality_near_threshold_and_failed_invariant_are_ineligible(
    tmp_path,
) -> None:
    metadata, arrays, vector = _runtime(tmp_path)
    batch = copy.deepcopy(vector.input)
    arrays["leaf_class_fraction"][[1, 4]] = 0.5
    batch["candidates"][0]["engineering_invariants"][0]["state"] = "fail"
    result = predict_batch(
        batch, metadata, arrays, vector.expected.value["model_evidence"]
    )
    row = result["results"][0]
    assert row["predicted_state"] == "chatter"
    assert row["applicability"] == "near_threshold"
    assert row["review_required"] is True
    assert row["eligible_for_preference"] is False
    assert "engineering_invariant_failed" in row["warnings"]


def test_population_drift_is_reported_without_becoming_probability(tmp_path) -> None:
    metadata, arrays, vector = _runtime(tmp_path)
    batch = copy.deepcopy(vector.input)
    batch["candidates"][0]["values"][0] = 2e9
    result = predict_batch(
        batch, metadata, arrays, vector.expected.value["model_evidence"]
    )
    row = result["results"][0]
    assert row["applicability"] == "out_of_population"
    assert row["calibration_status"] == "uncalibrated_model_score"
    assert "probability" not in " ".join(row["warnings"])


@pytest.mark.asyncio
async def test_generated_chatter_runs_through_supervised_adapter_lifecycle(
    tmp_path,
) -> None:
    package = generated_chatter_package()
    artifacts = chatter_fixture_artifacts(package)
    paths = {}
    for name, value in artifacts.items():
        target = tmp_path.joinpath("source", *name.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
        paths[name] = target
    platform, architecture = current_runtime_platform()
    supervisor = RuntimeSupervisor(
        built_in_runtime_registry(), scratch_root=tmp_path / "runtime"
    )
    session = await supervisor.start_session(
        adapter_id="wright-chatter-forest-numpy",
        installation_id="installation-generated-chatter",
        artifacts=paths,
        model_format="wright-chatter-forest-npz-1.0",
        task_id="screen_chatter_candidates",
        platform=platform,
        architecture=architecture,
        execution_provider="cpu",
    )
    try:
        verified = await session.verify()
        handle = await session.load()
        vector = package.variants[0].test_vectors[0]
        result = await session.infer(
            handle,
            vector.input,
            schema_digest=vector.input_schema_sha256,
            model_evidence=vector.expected.value["model_evidence"],
            timeout=3,
            maximum_output_bytes=1024 * 1024,
        )
        assert verified["artifact_set_digest"] == session.artifact_set_digest
        assert result["output"] == vector.expected.value
        await session.unload(handle)
    finally:
        assert await session.shutdown() == "clean"
    assert supervisor.active_process_count == 0
