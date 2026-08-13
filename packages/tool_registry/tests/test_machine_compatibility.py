from __future__ import annotations

from datetime import UTC, datetime

from tool_registry.catalog_models import CatalogEntry
from tool_registry.compatibility import evaluate_compatibility, observe_machine


NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)


def _observe(*, available: set[str] | None = None, network_policy: str = "allowed"):
    available = available or set()
    return observe_machine(
        clock=lambda: NOW,
        which=lambda name: f"/safe/{name}" if name in available else None,
        version_reader=lambda path: f"{path} 1.0",
        system_reader=lambda: "Linux",
        version_system_reader=lambda: "test-kernel",
        architecture_reader=lambda: "x86_64",
        network_policy=network_policy,
    )


def _entry(**updates) -> CatalogEntry:
    values = {
        "id": "example",
        "name": "Example",
        "vendor": "Example",
        "description": "Example",
        "domains": ["cad"],
        "transport": "stdio",
        "command": ["example"],
        "locality": "local",
        "weight": "light",
        "platform_support": {
            "linux_x64": {"status": "yes", "tested": True, "notes": "fixture"}
        },
    }
    values.update(updates)
    return CatalogEntry.model_validate(values)


def test_observation_is_stable_read_only_and_allowlisted() -> None:
    first = observe_machine(
        clock=lambda: NOW,
        which=lambda name: f"/safe/{name}",
        version_reader=lambda path: "1.0",
        system_reader=lambda: "Linux",
        version_system_reader=lambda: "test-kernel",
        architecture_reader=lambda: "aarch64",
        required_executables=["openscad", "../unsafe", "openscad"],
        host_detectors={"Solid Edge": lambda: {"available": True, "version": "2026"}},
    )
    second = first.model_copy()

    assert first == second
    assert first.platform_key == "linux_arm64"
    assert len(first.digest) == 64
    assert "executable:openscad" in first.host_observations
    assert "executable:../unsafe" not in first.host_observations
    assert first.host_observations["Solid Edge"]["available"] is True


def test_compatibility_reports_compatible_incompatible_uncertain_and_blocked() -> None:
    compatible = evaluate_compatibility(_entry(), _observe())
    assert compatible.status == "compatible"
    assert compatible.reasons == []

    missing_node = evaluate_compatibility(
        _entry(dependencies={"node": ["example-package"]}),
        _observe(),
    )
    assert missing_node.status == "incompatible"
    assert {reason.code for reason in missing_node.reasons} >= {
        "runtime_node_missing",
        "package_manager_npm_missing",
    }

    uncertain = evaluate_compatibility(
        _entry(
            locality="remote",
            platform_support={"linux_x64": {"status": "likely", "tested": False}},
        ),
        _observe(network_policy="unknown"),
    )
    assert uncertain.status == "uncertain"
    assert {reason.code for reason in uncertain.reasons} == {
        "network_access_unconfirmed",
        "platform_support_unverified",
    }

    blocked = evaluate_compatibility(
        _entry(
            installability_tier="blocked",
            install_blocked_reason="No public MCP server.",
        ),
        _observe(),
    )
    assert blocked.status == "blocked"
    assert blocked.reasons[0].recovery
