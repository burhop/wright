from __future__ import annotations

from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    fixture_documents,
    workflow_text,
)
from workspace_service.engineering_scenario_artifacts import normalize_artifact
from workspace_service.engineering_scenario_assertions import (
    EngineeringAssertionRegistry,
)
from workspace_service.rivet_validation import extract_rivet_mcp_requirements


def test_every_packaged_example_has_exact_nodes_artifacts_and_fixture_provenance() -> (
    None
):
    catalog = EngineeringScenarioCatalog()
    expected_domains = {
        "structural-bracket": {"cad", "python", "fea"},
        "electronics-enclosure-cooling": {"ecad", "cad", "cfd", "python"},
        "parametric-manufacturing": {
            "grasshopper",
            "cad",
            "additive",
            "slicing",
            "cam",
        },
    }

    for entry in catalog.list():
        manifest = catalog.get(entry.scenario_id)
        requirements = extract_rivet_mcp_requirements(workflow_text(manifest))
        fixtures = fixture_documents(entry.scenario_id, run_id="fixture-run")
        assert set(entry.domains) == expected_domains[entry.scenario_id]
        assert len(requirements.nodes) == len(manifest.document["capabilities"])
        assert {item["artifact_id"] for item in fixtures} == {
            item["artifact_id"] for item in manifest.document["artifacts"]
        }
        assert manifest.document["provenance"] == {
            "owner": "Wright Project",
            "fixture_origin": "wright-generated",
            "license": "MIT",
        }


def test_repeated_runs_keep_material_artifact_digests_and_outcomes_identical() -> None:
    catalog = EngineeringScenarioCatalog()
    for entry in catalog.list():
        manifest = catalog.get(entry.scenario_id)
        runs = []
        for run_id in ("first-run", "second-run"):
            artifacts = {
                artifact.artifact_id: artifact
                for artifact in (
                    normalize_artifact(value)
                    for value in fixture_documents(entry.scenario_id, run_id=run_id)
                )
            }
            assertions = EngineeringAssertionRegistry().evaluate_manifest(
                manifest.document["assertions"], artifacts
            )
            runs.append(
                (
                    {key: value.content_digest for key, value in artifacts.items()},
                    [(value.assertion_id, value.state) for value in assertions],
                )
            )
        assert runs[0] == runs[1]


def test_fixture_lineage_references_actual_upstream_content_digests() -> None:
    expected_parent = {
        "structural-bracket": {
            "bracket-mass": "bracket-geometry",
            "bracket-fea": "bracket-geometry",
        },
        "electronics-enclosure-cooling": {
            "enclosure-geometry": "board-envelope",
            "thermal-result": "enclosure-geometry",
            "thermal-margin": "thermal-result",
        },
        "parametric-manufacturing": {
            "parametric-geometry": "parameter-tree",
            "additive-package": "parametric-geometry",
            "slice-summary": "additive-package",
            "cam-program": "slice-summary",
        },
    }
    for scenario_id, parents in expected_parent.items():
        artifacts = {
            artifact.artifact_id: artifact
            for artifact in (
                normalize_artifact(value)
                for value in fixture_documents(scenario_id, run_id="lineage-run")
            )
        }
        for child_id, parent_id in parents.items():
            assert artifacts[child_id].upstream_digests == (
                artifacts[parent_id].content_digest,
            )
