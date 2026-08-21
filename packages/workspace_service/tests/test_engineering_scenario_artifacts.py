from __future__ import annotations

from copy import deepcopy

import pytest

from core.engineering_scenarios import EngineeringScenarioError
from workspace_service.engineering_scenario_artifacts import normalize_artifact
from workspace_service.engineering_scenario_catalog_service import fixture_documents


def test_all_packaged_fixture_artifacts_normalize_deterministically() -> None:
    for scenario_id in (
        "structural-bracket",
        "electronics-enclosure-cooling",
        "parametric-manufacturing",
    ):
        first = tuple(
            normalize_artifact(value)
            for value in fixture_documents(scenario_id, run_id="run-1")
        )
        second = tuple(
            normalize_artifact(value)
            for value in fixture_documents(scenario_id, run_id="run-1")
        )
        assert [item.content_digest for item in first] == [
            item.content_digest for item in second
        ]
        assert all(item.producer.run_id == "run-1" for item in first)


@pytest.mark.parametrize(
    "unsafe",
    [
        "<script>alert(1)</script>",
        "javascript:alert(1)",
        "../../escape",
        "file:///tmp/result",
    ],
)
def test_artifact_rejects_executable_markup_and_unsafe_paths(unsafe) -> None:
    value = deepcopy(fixture_documents("structural-bracket", run_id="run")[0])
    value["content"]["label"] = unsafe
    with pytest.raises(EngineeringScenarioError) as error:
        normalize_artifact(value)
    assert error.value.code == "artifact_executable_or_path_content"


def test_artifact_rejects_oversized_inline_content() -> None:
    value = deepcopy(fixture_documents("structural-bracket", run_id="run")[0])
    value["content"]["padding"] = "x" * (65 * 1024)
    with pytest.raises(EngineeringScenarioError) as error:
        normalize_artifact(value)
    assert error.value.code == "artifact_limit_exceeded"


def test_artifact_rejects_secret_like_content() -> None:
    value = deepcopy(fixture_documents("structural-bracket", run_id="run")[0])
    value["content"]["api_key"] = "secret"
    with pytest.raises(ValueError, match="secret-like"):
        normalize_artifact(value)


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda value: value["source_schema"].update(version="99.0"),
            "artifact_source_schema_unsupported",
        ),
        (
            lambda value: value.update(validation_state="unvalidated"),
            "artifact_validation_state_invalid",
        ),
        (
            lambda value: value.update(unexpected="field"),
            "artifact_field_unsupported",
        ),
        (
            lambda value: value.pop("content_digest"),
            "artifact_digest_invalid",
        ),
        (
            lambda value: value.update(content_digest="0" * 64),
            "artifact_digest_mismatch",
        ),
        (
            lambda value: value["content"].update(source="https://example.invalid/a"),
            "artifact_executable_or_path_content",
        ),
        (
            lambda value: value["content"].update(source="C:/private/result.step"),
            "artifact_executable_or_path_content",
        ),
    ],
)
def test_artifact_contract_and_source_versions_fail_closed(mutation, code) -> None:
    value = deepcopy(fixture_documents("structural-bracket", run_id="run")[0])
    mutation(value)
    with pytest.raises(EngineeringScenarioError) as error:
        normalize_artifact(value)
    assert error.value.code == code


def test_vault_reference_requires_exact_run_authorization() -> None:
    value = deepcopy(fixture_documents("structural-bracket", run_id="run")[0])
    value.pop("content")
    value["vault_reference"] = {
        "artifact_id": "vault-artifact-1",
        "media_type": "application/vnd.wright.mesh+json",
        "digest": "f" * 64,
    }
    value["content_digest"] = "f" * 64

    with pytest.raises(EngineeringScenarioError) as error:
        normalize_artifact(value)
    assert error.value.code == "artifact_vault_reference_unauthorized"

    normalized = normalize_artifact(value, authorized_vault_ids={"vault-artifact-1"})
    assert normalized.vault_reference["artifact_id"] == "vault-artifact-1"
