from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tool_registry.capability_views import (
    CapabilityCursorError,
    CapabilityFilters,
    build_capability_views,
    find_capability,
    paginate_capabilities,
)
from tool_registry.catalog_models import CatalogEntry
from tool_registry.compatibility import observe_machine
from tool_registry.models import McpServer


def _observation():
    return observe_machine(
        clock=lambda: datetime(2026, 8, 12, tzinfo=UTC),
        which=lambda name: None,
        version_reader=lambda path: None,
        system_reader=lambda: "Linux",
        version_system_reader=lambda: "test",
        architecture_reader=lambda: "x86_64",
        network_policy="allowed",
    )


def _entry() -> CatalogEntry:
    return CatalogEntry.model_validate(
        {
            "id": "canonical-cad",
            "name": "Canonical CAD",
            "vendor": "Vendor",
            "description": "Design brackets",
            "domains": ["cad"],
            "tags": ["bracket"],
            "aliases": ["legacy-cad"],
            "transport": "stdio",
            "command": ["cad-mcp"],
            "locality": "local",
            "weight": "light",
            "platform_support": {"linux_x64": {"status": "yes", "tested": True}},
            "source_records": [
                {"url": "https://vendor.example/cad", "notes": "Bracket tools"}
            ],
        }
    )


def _server(server_id: str, name: str = "Canonical CAD") -> McpServer:
    return McpServer(
        server_id=server_id,
        name=name,
        type="stdio",
        command=["cad-mcp"],
        is_active=False,
        is_installed=True,
        status="inactive",
        created_at=1,
        updated_at=1,
        installed_version="1.2.3",
        credentials_configured={"TOKEN": True},
    )


def test_projection_merges_alias_user_state_and_retains_custom_rows() -> None:
    entries = [_entry()]
    servers = [_server("legacy-cad"), _server("custom-mcp", "My private custom MCP")]
    views = build_capability_views(
        entries,
        servers,
        _observation(),
        workspace_membership={
            "legacy-cad": [{"workspace_id": "ws-1", "label": "Bracket project"}]
        },
    )

    catalog = find_capability(views, "legacy-cad")
    assert catalog is not None
    assert catalog.canonical_id == "canonical-cad"
    assert catalog.user_state.installed is True
    assert catalog.user_state.explicit_disabled is True
    assert catalog.user_state.credentials_configured == {"TOKEN": True}
    assert catalog.user_state.enabled_workspaces[0]["workspace_id"] == "ws-1"
    assert "token-value" not in catalog.model_dump_json().lower()

    custom = find_capability(views, "custom-mcp")
    assert custom is not None
    assert custom.custom is True
    assert custom.evidence_class == "user_reported_source_needed"


def test_projection_downgrades_legacy_pass_without_current_evidence() -> None:
    server = _server("legacy-passed", "Legacy passed MCP")
    server.validation_result.status = "passed"
    server.validation_result.message = "Legacy startup check passed"

    view = find_capability(
        build_capability_views([], [server], _observation()), "legacy-passed"
    )

    assert view is not None
    assert view.validation_result["status"] == "not_tested"
    assert view.validation_result["evidence_status"] == "unverified"
    assert "no current Wright validation evidence" in view.validation_result["message"]
    assert server.validation_result.status == "passed"


def test_projection_search_filters_and_cursor_are_stable() -> None:
    entries = [_entry()]
    views = build_capability_views(entries, [], _observation())
    page = paginate_capabilities(
        entries,
        views,
        filters=CapabilityFilters(search="bracket", domains=frozenset({"cad"})),
        limit=1,
    )
    assert page.total == 1
    assert page.capabilities[0].capability_id == "canonical-cad"
    assert page.capabilities[0].lifecycle_stage == "user_reported_url_needed"
    assert page.capabilities[0].maturity == "community"
    assert page.capabilities[0].field_provenance["compatibility"] == (
        "current_machine_observation"
    )
    assert "supported_platforms" in page.capabilities[0].requirements
    assert page.capabilities[0].validation_history[0]["status"] == "not_tested"
    assert page.snapshot.offline is True

    all_dimensions = paginate_capabilities(
        entries,
        views,
        filters=CapabilityFilters(
            platforms=frozenset({_observation().platform_key}),
            lifecycle_stages=frozenset({"user_reported_url_needed"}),
            maturities=frozenset({"community"}),
            evidence_classes=frozenset({"user_reported_source_needed"}),
            compatibility=frozenset({"compatible"}),
            risks=frozenset({"low"}),
            localities=frozenset({"local"}),
            validation=frozenset({"not_tested"}),
            installed=False,
        ),
    )
    assert all_dimensions.total == 1

    views[0].local_validation = {"state": "partially_passed"}
    local_validation = paginate_capabilities(
        entries,
        views,
        filters=CapabilityFilters(validation=frozenset({"partially_passed"})),
    )
    assert local_validation.total == 1

    empty = paginate_capabilities(
        entries,
        views,
        filters=CapabilityFilters(search="does-not-exist"),
    )
    assert empty.total == 0

    with pytest.raises(CapabilityCursorError):
        paginate_capabilities(entries, views, cursor="not-a-cursor!")
