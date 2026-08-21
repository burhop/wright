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


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (
            lambda value: value.update(schema_version="2.0"),
            "artifact_version_unsupported",
        ),
        (
            lambda value: value["content"].update(label="../../../private"),
            "artifact_executable_or_path_content",
        ),
        (
            lambda value: value["content"].update(label="<script>run()</script>"),
            "artifact_executable_or_path_content",
        ),
        (
            lambda value: value["content"].update(padding="x" * (65 * 1024)),
            "artifact_limit_exceeded",
        ),
    ],
)
def test_untrusted_artifact_failure_matrix_is_stable(mutation, expected_code) -> None:
    value = deepcopy(fixture_documents("structural-bracket", run_id="run")[0])
    mutation(value)
    with pytest.raises(EngineeringScenarioError) as error:
        normalize_artifact(value)
    assert error.value.code == expected_code


def test_numeric_and_solver_failures_preserve_exact_producer_and_recovery() -> None:
    catalog = EngineeringScenarioCatalog()
    values = list(fixture_documents("structural-bracket", run_id="run"))
    values[1]["units"]["mass"] = "mm"
    values[2]["content"]["converged"] = False
    values[2]["content_digest"] = artifact_content_digest(values[2]["content"])
    artifacts = {
        artifact.artifact_id: artifact
        for artifact in (normalize_artifact(value) for value in values)
    }
    definitions = catalog.get("structural-bracket").document["assertions"]
    registry = EngineeringAssertionRegistry()

    unit_result = registry.evaluate(definitions[1], artifacts)
    convergence_result = registry.evaluate(
        next(
            value for value in definitions if value["assertion_id"] == "fea-converged"
        ),
        artifacts,
    )

    assert unit_result.state == AssertionState.ERROR
    assert unit_result.reason_code == "unit_dimension_mismatch"
    assert unit_result.producer == {
        "node_id": "node-python",
        "capability": "python__mass_properties",
        "call_id": "structural-python",
    }
    assert unit_result.recovery == "Inspect density, volume, and unit conversion."
    assert convergence_result.state == AssertionState.FAIL
    assert convergence_result.reason_code == "solver_not_converged"
    assert convergence_result.producer["node_id"] == "node-fea"
    assert convergence_result.producer["capability"] == "fea__solve_static"


def test_secret_like_and_non_finite_values_never_become_report_evidence() -> None:
    secret = deepcopy(fixture_documents("structural-bracket", run_id="run")[0])
    secret["content"]["access_token"] = "synthetic-secret-value"
    with pytest.raises(ValueError, match="secret-like"):
        normalize_artifact(secret)

    values = list(fixture_documents("structural-bracket", run_id="run"))
    values[1]["content"]["mass"] = float("nan")
    with pytest.raises(EngineeringScenarioError) as error:
        normalize_artifact(values[1])
    assert error.value.code == "artifact_non_finite_value"
