from __future__ import annotations

from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    fixture_documents,
)
from workspace_service.engineering_scenario_assertions import (
    EngineeringAssertionRegistry,
)
from workspace_service.engineering_scenario_artifacts import normalize_artifact


def test_chatter_scenario_fixture_has_two_mcps_one_model_and_safe_advisory() -> None:
    manifest = EngineeringScenarioCatalog().get("chatter-candidate-review")
    capabilities = manifest.document["capabilities"]
    assert sum(item["provider_kind"] == "mcp" for item in capabilities) >= 2
    assert (
        sum(item["provider_kind"] == "engineering_model" for item in capabilities) == 1
    )
    artifacts = {
        item.artifact_id: item
        for item in map(
            normalize_artifact,
            fixture_documents("chatter-candidate-review", run_id="system-proof"),
        )
    }
    results = EngineeringAssertionRegistry().evaluate_manifest(
        manifest.document["assertions"], artifacts
    )
    assert all(item.state.value == "pass" for item in results)
    advisory = artifacts["chatter-advisory"].content
    assert advisory["simulation_only"] is True
    assert advisory["machine_authority"] is False
    assert advisory["selected_candidate_id"] in {
        item["candidate_id"] for item in advisory["candidate_outcomes"]
    }
