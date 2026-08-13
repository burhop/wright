from __future__ import annotations

import pytest

from core.engineering_scenarios import EngineeringScenarioError
from workspace_service.engineering_scenario_service import (
    ScenarioEnvironmentAuthorization,
    classify_scenario_environment,
    selected_tier2_adapter_plan,
)


def _document(*, tier="tier1", **environment):
    return {
        "tier": tier,
        "environment": {
            "network": False,
            "credentials": False,
            "proprietary_application": False,
            "gpu": False,
            "hardware": False,
            "large_download": False,
            "platforms": ["linux-amd64"],
            **environment,
        },
        "safety": {"physical_actuation": False},
    }


def _codes(blockers):
    return {value.code for value in blockers}


def test_tier1_rejects_external_requirements_and_physical_actuation() -> None:
    document = _document(
        network=True,
        credentials=True,
        proprietary_application=True,
        gpu=True,
        hardware=True,
        large_download=True,
    )
    document["safety"]["physical_actuation"] = True

    blockers = classify_scenario_environment(document, platform_tag="linux-amd64")

    assert _codes(blockers) == {
        "scenario_tier_invalid",
        "scenario_physical_actuation_forbidden",
    }


def test_tier2_fails_closed_before_network_prompt_or_host_mutation() -> None:
    blockers = classify_scenario_environment(
        _document(
            tier="tier2",
            network=True,
            credentials=True,
            license_prompt=True,
            host_mutation=True,
            interactive_prompt=True,
        ),
        platform_tag="linux-amd64",
    )

    assert {
        "scenario_tier_opt_in_required",
        "scenario_network_authorization_required",
        "scenario_credentials_authorization_required",
        "scenario_license_review_required",
        "scenario_host_mutation_forbidden",
        "scenario_interactive_prompt_forbidden",
        "scenario_disposable_environment_required",
    } <= _codes(blockers)


def test_candidate_and_watchlist_catalog_states_are_not_runnable() -> None:
    authorization = ScenarioEnvironmentAuthorization(
        allow_tier2=True,
        network=True,
        disposable=True,
    )
    for catalog_state in (
        "api_wrapper_candidate",
        "watchlist",
        "no_public_mcp",
        "unconfirmed",
    ):
        blockers = classify_scenario_environment(
            _document(tier="tier2", network=True, catalog_state=catalog_state),
            platform_tag="linux-amd64",
            authorization=authorization,
        )
        assert "scenario_catalog_entry_unconfirmed" in _codes(blockers)


def test_selected_pyfluent_adapter_is_partial_and_evidence_only() -> None:
    plan = selected_tier2_adapter_plan(
        "ansys-fluent-mcp",
        platform_target="gb10-linux-arm64",
        authorization=ScenarioEnvironmentAuthorization(
            allow_tier2=True,
            network=True,
            disposable=True,
        ),
    )

    assert plan.state == "partial"
    assert plan.safe_tool == "session_status"
    assert plan.discovery_digest is None
    assert plan.gateway_digest is None
    assert plan.cleanup_state == "not_started"
    assert "gateway proxy evidence" in plan.pending_evidence
    assert plan.evidence_resources


def test_elements_adapter_requires_license_metadata_review() -> None:
    baseline = ScenarioEnvironmentAuthorization(
        allow_tier2=True,
        network=True,
        disposable=True,
    )
    blocked = selected_tier2_adapter_plan(
        "nvidia-elements-mcp",
        platform_target="gb10-linux-arm64",
        authorization=baseline,
    )
    reviewed = selected_tier2_adapter_plan(
        "nvidia-elements-mcp",
        platform_target="gb10-linux-arm64",
        authorization=ScenarioEnvironmentAuthorization(
            allow_tier2=True,
            network=True,
            disposable=True,
            license_reviewed=True,
        ),
    )

    assert blocked.state == "blocked"
    assert "scenario_license_review_required" in _codes(blocked.blockers)
    assert reviewed.state == "partial"
    assert reviewed.install_command_digest != reviewed.catalog_digest


def test_unknown_or_unsupported_adapter_is_rejected_without_execution() -> None:
    with pytest.raises(EngineeringScenarioError) as error:
        selected_tier2_adapter_plan(
            "simscale-api-wrapper",
            platform_target="linux-amd64",
        )
    assert error.value.code == "scenario_tier2_adapter_unknown"

    plan = selected_tier2_adapter_plan(
        "ansys-fluent-mcp",
        platform_target="not-a-platform",
        authorization=ScenarioEnvironmentAuthorization(
            allow_tier2=True,
            network=True,
            disposable=True,
        ),
    )
    assert plan.state == "blocked"
    assert "scenario_catalog_platform_incompatible" in _codes(plan.blockers)
