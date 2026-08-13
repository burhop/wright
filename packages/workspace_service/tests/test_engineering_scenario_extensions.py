from __future__ import annotations

import copy

import pytest

from core.engineering_scenarios import AssertionState, EngineeringScenarioError
from workspace_service.engineering_scenario_assertions import (
    EngineeringAssertionRegistry,
)
from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
    fixture_documents,
    validate_manifest,
)
from workspace_service.engineering_scenario_artifacts import (
    EngineeringArtifactNormalizerRegistry,
    artifact_content_digest,
    normalize_artifact,
)


def test_custom_versioned_assertion_plugin_runs_without_runner_changes() -> None:
    artifact = normalize_artifact(
        fixture_documents("structural-bracket", run_id="run")[0]
    )
    registry = EngineeringAssertionRegistry()
    registry.register(
        "test_only",
        "1.0",
        lambda rule, artifacts: (
            len(artifacts) == int(rule["count"]),
            {"count": len(artifacts)},
            "test_count_matches",
        ),
    )

    result = registry.evaluate(
        {
            "assertion_id": "extension-count",
            "plugin": "test_only",
            "plugin_version": "1.0",
            "artifact_ids": [artifact.artifact_id],
            "rule": {"count": 1},
            "guidance": "Inspect the extension fixture.",
        },
        {artifact.artifact_id: artifact},
    )

    assert result.state == AssertionState.PASS
    assert result.reason_code == "test_count_matches"


def test_custom_versioned_artifact_normalizer_runs_without_runner_changes() -> None:
    registry = EngineeringArtifactNormalizerRegistry(include_defaults=False)
    visited = []
    registry.register(
        "custom-summary",
        "wright-test-summary",
        "1.0",
        lambda raw: visited.append(raw["artifact_id"]),
    )
    content = {"value": 42}
    artifact = normalize_artifact(
        {
            "schema_version": "1.0",
            "artifact_id": "custom-artifact",
            "domain": "python",
            "kind": "custom-summary",
            "source_schema": {
                "name": "wright-test-summary",
                "version": "1.0",
                "media_type": "application/vnd.wright.test+json",
            },
            "producer": {
                "run_id": "run",
                "node_id": "node-python",
                "call_id": "call",
                "capability": "python__custom",
            },
            "upstream_digests": [],
            "content": content,
            "content_digest": artifact_content_digest(content),
            "validation_state": "valid",
        },
        registry=registry,
    )
    assert artifact.content == content
    assert visited == ["custom-artifact"]

    with pytest.raises(EngineeringScenarioError) as duplicate:
        registry.register("custom-summary", "wright-test-summary", "1.0")
    assert duplicate.value.code == "scenario_normalizer_conflict"


def test_duplicate_and_unknown_plugin_versions_fail_closed() -> None:
    registry = EngineeringAssertionRegistry()
    with pytest.raises(EngineeringScenarioError) as duplicate:
        registry.register("numeric", "1.0", lambda _rule, _artifacts: (True, {}, "ok"))
    assert duplicate.value.code == "scenario_plugin_conflict"

    artifact = normalize_artifact(
        fixture_documents("structural-bracket", run_id="run")[0]
    )
    with pytest.raises(EngineeringScenarioError) as unsupported:
        registry.evaluate(
            {
                "assertion_id": "future-version",
                "plugin": "numeric",
                "plugin_version": "2.0",
                "artifact_ids": [artifact.artifact_id],
                "rule": {"kind": "presence"},
            },
            {artifact.artifact_id: artifact},
        )
    assert unsupported.value.code == "scenario_plugin_unsupported"


def test_third_party_and_unsafe_extension_variants_are_rejected() -> None:
    document = copy.deepcopy(
        EngineeringScenarioCatalog().get("structural-bracket").document
    )
    document["provenance"] = {
        "owner": "External project",
        "fixture_origin": "third-party",
        "license": "MIT",
    }
    with pytest.raises(EngineeringScenarioError) as provenance:
        validate_manifest(document)
    assert provenance.value.code == "scenario_provenance_incomplete"

    document = copy.deepcopy(
        EngineeringScenarioCatalog().get("structural-bracket").document
    )
    document["capabilities"][0]["command"] = ["unreviewed-server"]
    with pytest.raises(EngineeringScenarioError) as connection:
        validate_manifest(document)
    assert connection.value.code in {
        "scenario_manifest_invalid",
        "scenario_connection_material_forbidden",
    }
