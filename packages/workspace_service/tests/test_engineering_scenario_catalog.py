from __future__ import annotations

from copy import deepcopy

import pytest

from core.engineering_scenarios import EngineeringScenarioError
from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    validate_manifest,
)


def test_catalog_contains_model_enabled_and_multi_domain_tier1_scenarios() -> None:
    catalog = EngineeringScenarioCatalog()
    entries = catalog.list()

    assert [entry.scenario_id for entry in entries] == [
        "chatter-candidate-review",
        "electronics-enclosure-cooling",
        "parametric-manufacturing",
        "structural-bracket",
    ]
    assert all(entry.tier == "tier1" for entry in entries)
    assert set().union(*(set(entry.domains) for entry in entries)) == {
        "cad",
        "ecad",
        "fea",
        "cfd",
        "python",
        "cam",
        "grasshopper",
        "additive",
        "slicing",
    }
    for entry in entries:
        assert len(catalog.get(entry.scenario_id).document["capabilities"]) >= 2


def test_model_enabled_manifest_requires_independent_mcp_and_model_providers() -> None:
    document = deepcopy(
        EngineeringScenarioCatalog().get("chatter-candidate-review").document
    )
    document["capabilities"] = [
        value
        for value in document["capabilities"]
        if value["provider_kind"] != "engineering_model"
    ]
    with pytest.raises(EngineeringScenarioError) as error:
        validate_manifest(document)
    assert error.value.code == "scenario_provider_composition_invalid"


def test_catalog_digests_are_stable() -> None:
    first = EngineeringScenarioCatalog()
    second = EngineeringScenarioCatalog()
    assert [(item.scenario_id, item.manifest_digest) for item in first.list()] == [
        (item.scenario_id, item.manifest_digest) for item in second.list()
    ]


def test_tier1_rejects_external_dependency() -> None:
    document = deepcopy(EngineeringScenarioCatalog().get("structural-bracket").document)
    document["environment"]["network"] = True
    with pytest.raises(EngineeringScenarioError) as error:
        validate_manifest(document)
    assert error.value.code == "scenario_tier_invalid"


def test_manifest_rejects_child_connection_material() -> None:
    document = deepcopy(EngineeringScenarioCatalog().get("structural-bracket").document)
    document["inputs"]["server_url"] = "http://127.0.0.1:9999"
    with pytest.raises(EngineeringScenarioError) as error:
        validate_manifest(document)
    assert error.value.code == "scenario_connection_material_forbidden"


def test_manifest_rejects_unknown_assertion_artifact() -> None:
    document = deepcopy(EngineeringScenarioCatalog().get("structural-bracket").document)
    document["assertions"][0]["artifact_ids"] = ["missing"]
    with pytest.raises(EngineeringScenarioError) as error:
        validate_manifest(document)
    assert error.value.code == "scenario_manifest_invalid"
