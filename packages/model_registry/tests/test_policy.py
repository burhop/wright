from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_registry.models import ModelPackage
from model_registry.policy import (
    HostObservation,
    ModelPolicy,
    PolicyState,
    validate_artifact_path,
)


def package_document() -> dict[str, object]:
    path = Path(__file__).parent / "fixtures" / "contracts" / "valid-model-package.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "path",
    (
        "../model.onnx",
        "/model.onnx",
        "C:/model.onnx",
        "model\\weights.onnx",
        "model//weights.onnx",
        "model/./weights.onnx",
        "model/weights.py",
        "model/weights.PTH",
        "model/weights.dll",
        "model/archive.zip",
    ),
)
def test_unsafe_artifact_paths_and_formats_are_rejected(path: str) -> None:
    with pytest.raises(ValueError):
        validate_artifact_path(path)


def test_normalized_relative_data_path_is_accepted() -> None:
    assert validate_artifact_path("model/weights.safetensors") == (
        "model/weights.safetensors"
    )


def test_policy_approves_generated_fixture_on_compatible_host() -> None:
    package = ModelPackage.model_validate(package_document())
    result = ModelPolicy().evaluate(
        package,
        variant_id="json-cpu-f64",
        host=HostObservation(
            platform="windows",
            architecture="x86_64",
            available_disk_bytes=1_000_000_000,
            available_ram_bytes=1_000_000_000,
            accelerators=frozenset({"cpu"}),
            runtime_adapters={"wright-deterministic": "1.0.0"},
        ),
    )
    assert result.state is PolicyState.COMPATIBLE
    assert result.blockers == ()


@pytest.mark.parametrize(
    ("change", "category"),
    (
        ("platform", "incompatible_platform"),
        ("architecture", "incompatible_platform"),
        ("disk", "insufficient_disk"),
        ("ram", "insufficient_resources"),
        ("accelerator", "insufficient_resources"),
        ("runtime", "runtime_missing"),
    ),
)
def test_policy_reports_exact_compatibility_blockers(
    change: str, category: str
) -> None:
    values = {
        "platform": "windows",
        "architecture": "x86_64",
        "available_disk_bytes": 1_000_000_000,
        "available_ram_bytes": 1_000_000_000,
        "accelerators": frozenset({"cpu"}),
        "runtime_adapters": {"wright-deterministic": "1.0.0"},
    }
    if change == "platform":
        values["platform"] = "solaris"
    elif change == "architecture":
        values["architecture"] = "sparc"
    elif change == "disk":
        values["available_disk_bytes"] = 1
    elif change == "ram":
        values["available_ram_bytes"] = 1
    elif change == "accelerator":
        values["accelerators"] = frozenset()
    else:
        values["runtime_adapters"] = {}
    result = ModelPolicy().evaluate(
        ModelPackage.model_validate(package_document()),
        variant_id="json-cpu-f64",
        host=HostObservation(**values),
    )
    assert result.state is PolicyState.BLOCKED
    assert category in {blocker.category for blocker in result.blockers}


def test_policy_blocks_unsafe_format_and_physical_actuation_task() -> None:
    unsafe = package_document()
    unsafe["variants"][0]["format"] = "pytorch-pickle"
    unsafe["variants"][0]["artifacts"][0]["path"] = "model/weights.pth"
    unsafe_result = ModelPolicy().evaluate(
        ModelPackage.model_validate(unsafe),
        variant_id="json-cpu-f64",
        host=HostObservation.reference(),
    )
    assert "unsafe_format" in {item.category for item in unsafe_result.blockers}

    actuation = package_document()
    actuation["tasks"][0]["task_id"] = "start-spindle"
    actuation["variants"][0]["test_vectors"][0]["task_id"] = "start-spindle"
    actuation_result = ModelPolicy().evaluate(
        ModelPackage.model_validate(actuation),
        variant_id="json-cpu-f64",
        host=HostObservation.reference(),
    )
    assert "physical_actuation_forbidden" in {
        item.category for item in actuation_result.blockers
    }


def test_external_source_and_license_actions_fail_closed() -> None:
    document = package_document()
    document["source"].update(
        kind="hugging_face",
        uri="http://example.invalid/model",
        access="gated",
        allowed_hosts=["example.invalid"],
    )
    document["license"]["acceptance_required"] = True
    document["review_state"] = "needs_review"
    package = ModelPackage.model_validate(document)
    result = ModelPolicy().evaluate(
        package, variant_id="json-cpu-f64", host=HostObservation.reference()
    )
    categories = {item.category for item in result.blockers}
    assert {"source_insecure", "source_gated", "license_action_required"} <= categories
