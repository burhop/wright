from __future__ import annotations

import json

from model_registry.chatter_runtime import load_forest, predict_batch
from model_registry.generated import (
    chatter_fixture_artifacts,
    generated_chatter_package,
)

from fixture_factory import generate_chatter_fixture


def _write(root, artifacts):
    for name, value in artifacts.items():
        path = root.joinpath(*name.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)


def test_generated_fixture_is_repeatable_and_matches_mandatory_vector(tmp_path) -> None:
    package = generated_chatter_package()
    first = chatter_fixture_artifacts(package)
    second = chatter_fixture_artifacts(package)
    assert first == second
    _write(tmp_path, first)
    metadata, arrays = load_forest(tmp_path)
    vector = package.variants[0].test_vectors[0]
    evidence = vector.expected.value["model_evidence"]
    result = predict_batch(vector.input, metadata, arrays, evidence)
    assert result == vector.expected.value
    assert json.loads(first["evidence/conversion-parity.json"])["status"] == "passed"


def test_generated_fixture_factory_writes_only_to_caller_owned_state(tmp_path) -> None:
    fixture = generate_chatter_fixture(tmp_path / "generated-chatter")
    assert fixture.package == generated_chatter_package()
    assert fixture.archive_path.is_file()
    assert fixture.manifest_path.is_file()
    assert not (
        tmp_path.parent / "wright-chatter-generated-test-r1.wright-model.zip"
    ).exists()
