from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from model_registry.chatter_contracts import (
    ChatterContractError,
    validate_candidate_batch,
)
from model_registry.generated import (
    chatter_fixture_artifacts,
    generated_chatter_package,
)


ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = re.compile(
    r"(?i)(?:api[_-]?key|authorization|credential|password|private[_-]?key|process_handle|runtime_endpoint|g[-_ ]?code|spindle command)"
)


def test_public_chatter_contracts_exclude_commands_credentials_and_authority() -> None:
    package = generated_chatter_package()
    material = package.model_dump(mode="json", exclude_none=True)
    material["artifacts"] = sorted(chatter_fixture_artifacts(package))
    assert FORBIDDEN.search(json.dumps(material, sort_keys=True)) is None
    assert package.remote_code_policy == "forbidden"
    assert package.license.redistribution == "prohibited"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("feature_order", ["unreviewed"] * 37),
        ("units", ["probability"] * 37),
    ],
)
def test_changed_schema_or_units_fail_before_runtime(field, value) -> None:
    package = generated_chatter_package()
    artifacts = chatter_fixture_artifacts(package)
    metadata = json.loads(artifacts["model/serving-metadata.json"])
    batch = dict(package.variants[0].test_vectors[0].input)
    batch[field] = value
    with pytest.raises(ChatterContractError):
        validate_candidate_batch(batch, metadata)


def test_scenario_artifacts_forbid_machine_authority_and_private_paths() -> None:
    fixture = (
        ROOT
        / "packages/workspace_service/src/workspace_service/engineering_scenario_catalog/fixtures/chatter-candidate-review.json"
    ).read_text(encoding="utf-8")
    assert 'machine_authority":false' in fixture.replace(" ", "").lower()
    assert re.search(r"(?i)(?:[a-z]:\\|/home/|/users/|\\\\)", fixture) is None
    assert FORBIDDEN.search(fixture) is None
