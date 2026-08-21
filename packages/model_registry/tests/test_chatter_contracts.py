from __future__ import annotations

import json
from pathlib import Path

import pytest

from model_registry.chatter_contracts import (
    FEATURE_ORDER,
    FEATURE_UNITS,
    ChatterContractError,
    validate_candidate_batch,
    validate_serving_metadata,
)
from model_registry.generated import (
    chatter_fixture_artifacts,
    generated_chatter_package,
)


def _documents():
    package = generated_chatter_package()
    artifacts = chatter_fixture_artifacts(package)
    metadata = json.loads(artifacts["model/serving-metadata.json"])
    batch = package.variants[0].test_vectors[0].input
    return metadata, batch


def test_generated_contract_has_exact_feature_order_units_and_digest() -> None:
    metadata, batch = _documents()
    validated = validate_serving_metadata(metadata)
    assert tuple(item["name"] for item in validated["input_contract"]) == FEATURE_ORDER
    assert tuple(item["unit"] for item in validated["input_contract"]) == FEATURE_UNITS
    assert (
        validate_candidate_batch(batch, metadata)["candidates"][0]["candidate_id"]
        == "generated-stable"
    )


@pytest.mark.parametrize("field", ["feature_order", "units"])
def test_candidate_contract_rejects_changed_order_or_units(field: str) -> None:
    metadata, batch = _documents()
    changed = dict(batch)
    changed[field] = list(reversed(batch[field]))
    with pytest.raises(ChatterContractError, match="invalid|changed"):
        validate_candidate_batch(changed, metadata)


def test_candidate_contract_rejects_duplicates_nonfinite_and_wrong_origin() -> None:
    metadata, batch = _documents()
    duplicate = json.loads(json.dumps(batch))
    duplicate["candidates"].append(duplicate["candidates"][0])
    with pytest.raises(ChatterContractError, match="duplicated"):
        validate_candidate_batch(duplicate, metadata)

    wrong_origin = json.loads(json.dumps(batch))
    wrong_origin["candidates"][0]["origins"][0] = "measured"
    metadata["input_contract"][0]["allowed_origins"] = ["simulated"]
    material = dict(metadata)
    material.pop("metadata_digest")
    from model_registry.models import canonical_digest

    metadata["metadata_digest"] = canonical_digest(material)
    with pytest.raises(ChatterContractError, match="origin"):
        validate_candidate_batch(wrong_origin, metadata)

    nonfinite = json.loads(json.dumps(batch))
    nonfinite["candidates"][0]["values"][0] = float("nan")
    with pytest.raises(ChatterContractError, match="finite"):
        validate_candidate_batch(nonfinite, _documents()[0])


def test_reviewed_contract_fixtures_remain_valid_and_fail_closed() -> None:
    root = Path(__file__).with_name("fixtures") / "chatter"
    metadata, _ = _documents()
    valid = json.loads(
        (root / "valid-candidate-batch.json").read_text(encoding="utf-8")
    )
    assert (
        validate_candidate_batch(valid, metadata)["candidates"][0]["candidate_id"]
        == "fixture-stable"
    )
    invalid = json.loads(
        (root / "invalid-candidate-batch.json").read_text(encoding="utf-8")
    )
    with pytest.raises(ChatterContractError):
        validate_candidate_batch(invalid, metadata)
