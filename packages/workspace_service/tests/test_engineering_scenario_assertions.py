from __future__ import annotations

from copy import deepcopy

import pytest

from core.engineering_scenarios import AssertionState, EngineeringScenarioError
from workspace_service.engineering_scenario_artifacts import (
    artifact_content_digest,
    normalize_artifact,
)
from workspace_service.engineering_scenario_assertions import (
    EngineeringAssertionRegistry,
)
from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    fixture_documents,
)


def _refresh_digest(value) -> None:
    value["content_digest"] = artifact_content_digest(value["content"])


@pytest.mark.parametrize(
    "scenario_id",
    [
        "structural-bracket",
        "electronics-enclosure-cooling",
        "parametric-manufacturing",
    ],
)
def test_packaged_scenario_assertions_pass(scenario_id) -> None:
    catalog = EngineeringScenarioCatalog()
    manifest = catalog.get(scenario_id).document
    artifacts = {
        artifact.artifact_id: artifact
        for artifact in (
            normalize_artifact(value)
            for value in fixture_documents(scenario_id, run_id="run-1")
        )
    }

    results = EngineeringAssertionRegistry().evaluate_manifest(
        manifest["assertions"], artifacts
    )

    assert results
    assert all(result.state == AssertionState.PASS for result in results)


def test_unit_mismatch_is_attributed_to_numeric_assertion() -> None:
    values = list(fixture_documents("structural-bracket", run_id="run-1"))
    values[1]["units"]["mass"] = "mm"
    artifacts = {
        artifact.artifact_id: artifact
        for artifact in (normalize_artifact(value) for value in values)
    }
    definition = (
        EngineeringScenarioCatalog().get("structural-bracket").document["assertions"][1]
    )

    result = EngineeringAssertionRegistry().evaluate(definition, artifacts)

    assert result.state == AssertionState.ERROR
    assert result.reason_code == "unit_dimension_mismatch"
    assert result.producer["node_id"] == "node-python"


def test_non_converged_solver_fails_even_when_completed() -> None:
    values = list(fixture_documents("structural-bracket", run_id="run-1"))
    values[2]["content"]["converged"] = False
    _refresh_digest(values[2])
    artifacts = {
        artifact.artifact_id: artifact
        for artifact in (normalize_artifact(value) for value in values)
    }
    definition = next(
        value
        for value in EngineeringScenarioCatalog()
        .get("structural-bracket")
        .document["assertions"]
        if value["assertion_id"] == "fea-converged"
    )

    result = EngineeringAssertionRegistry().evaluate(definition, artifacts)

    assert result.state == AssertionState.FAIL
    assert result.reason_code == "solver_not_converged"
    assert result.producer["node_id"] == "node-fea"


def test_cam_actuation_is_rejected() -> None:
    values = list(fixture_documents("parametric-manufacturing", run_id="run-1"))
    values[-1]["content"]["program"] += "\nM3 S1000\nG1 X1"
    _refresh_digest(values[-1])
    artifacts = {
        artifact.artifact_id: artifact
        for artifact in (normalize_artifact(value) for value in values)
    }
    definition = (
        EngineeringScenarioCatalog()
        .get("parametric-manufacturing")
        .document["assertions"][-1]
    )

    result = EngineeringAssertionRegistry().evaluate(definition, artifacts)

    assert result.state == AssertionState.FAIL
    assert result.reason_code == "cam_actuation_forbidden"


def test_plugin_registry_rejects_duplicate_and_unknown_versions() -> None:
    registry = EngineeringAssertionRegistry()
    with pytest.raises(EngineeringScenarioError) as duplicate:
        registry.register("numeric", "1.0", lambda rule, artifacts: (True, {}, "ok"))
    assert duplicate.value.code == "scenario_plugin_conflict"

    definition = deepcopy(
        EngineeringScenarioCatalog().get("structural-bracket").document["assertions"][0]
    )
    definition["plugin_version"] = "2.0"
    with pytest.raises(EngineeringScenarioError) as unknown:
        registry.evaluate(definition, {})
    assert unknown.value.code == "scenario_plugin_unsupported"


def test_monotonic_relational_and_table_rules_are_versioned_extensions() -> None:
    values = list(fixture_documents("structural-bracket", run_id="run-1"))
    values[1]["content"]["samples"] = [1, 2, 2, 4]
    values[1]["units"]["samples"] = "mm"
    values[1]["content"]["rows"] = [
        {"station": 0, "stress": 10.0},
        {"station": 1, "stress": 11.5},
    ]
    _refresh_digest(values[1])
    artifacts = {
        artifact.artifact_id: artifact
        for artifact in (normalize_artifact(value) for value in values)
    }
    registry = EngineeringAssertionRegistry()

    monotonic = registry.evaluate(
        {
            "assertion_id": "samples-monotonic",
            "plugin": "numeric",
            "plugin_version": "1.0",
            "artifact_ids": ["bracket-mass"],
            "rule": {
                "kind": "monotonic",
                "path": "samples",
                "direction": "nondecreasing",
                "unit": "m",
            },
        },
        artifacts,
    )
    relational = registry.evaluate(
        {
            "assertion_id": "volumes-match",
            "plugin": "numeric",
            "plugin_version": "1.0",
            "artifact_ids": ["bracket-mass", "bracket-geometry"],
            "rule": {
                "kind": "relational",
                "path": "volume",
                "right_path": "volume",
                "operator": "==",
                "unit": "mm3",
            },
        },
        artifacts,
    )
    table = registry.evaluate(
        {
            "assertion_id": "stress-table",
            "plugin": "table",
            "plugin_version": "1.0",
            "artifact_ids": ["bracket-mass"],
            "rule": {
                "path": "rows",
                "columns": ["station", "stress"],
                "finite_columns": ["station", "stress"],
                "minimum_rows": 2,
                "maximum_rows": 10,
            },
        },
        artifacts,
    )

    assert monotonic.state == AssertionState.PASS
    assert monotonic.observed["values"] == ["0.001", "0.002", "0.002", "0.004"]
    assert relational.state == AssertionState.PASS
    assert table.state == AssertionState.PASS


def test_solver_conservation_and_geometry_declaration_fail_closed() -> None:
    values = list(fixture_documents("structural-bracket", run_id="run-1"))
    values[2]["content"].update(input_energy=100.0, output_energy=99.9)
    _refresh_digest(values[2])
    geometry_without_frame = deepcopy(values[0])
    geometry_without_frame.pop("coordinate_system")
    artifacts = {
        artifact.artifact_id: artifact
        for artifact in (normalize_artifact(value) for value in values)
    }
    registry = EngineeringAssertionRegistry()
    conservation = registry.evaluate(
        {
            "assertion_id": "energy-conservation",
            "plugin": "fea",
            "plugin_version": "1.0",
            "artifact_ids": ["bracket-fea"],
            "rule": {
                "kind": "conservation",
                "input_path": "input_energy",
                "output_path": "output_energy",
                "absolute_tolerance": 0.2,
            },
        },
        artifacts,
    )
    invalid_geometry = normalize_artifact(geometry_without_frame)
    geometry = registry.evaluate(
        EngineeringScenarioCatalog()
        .get("structural-bracket")
        .document["assertions"][0],
        {"bracket-geometry": invalid_geometry},
    )

    assert conservation.state == AssertionState.PASS
    assert geometry.state == AssertionState.FAIL
    assert geometry.observed["coordinate_and_units_declared"] is False


def test_mass_property_relationship_rejects_uncorrelated_lineage() -> None:
    values = list(fixture_documents("structural-bracket", run_id="run-1"))
    values[1]["upstream_digests"] = ["0" * 64]
    artifacts = {
        artifact.artifact_id: artifact
        for artifact in (normalize_artifact(value) for value in values)
    }
    definition = next(
        value
        for value in EngineeringScenarioCatalog()
        .get("structural-bracket")
        .document["assertions"]
        if value["assertion_id"] == "mass-properties"
    )

    result = EngineeringAssertionRegistry().evaluate(definition, artifacts)

    assert result.state == AssertionState.FAIL
    assert result.reason_code == "mass_properties_invalid"
    assert result.observed["density"] == "2.7E+3"
    assert result.observed["input_correlated"] is False
