from importlib.resources import files

import pytest

from tool_registry.canonical_catalog import (
    CatalogValidationError,
    _validate_evidence,
    _validate_identity,
    catalog_aliases,
    load_catalog_document,
    load_catalog_document_from_text,
)
from tool_registry.catalog_platforms import filter_catalog_entries
from tool_registry.catalog_models import CatalogEntry
from tool_registry.engineering_catalog import ENGINEERING_CATALOG


def test_canonical_catalog_resource_is_schema_valid_and_exact() -> None:
    document = load_catalog_document()
    assert document["format_version"] == 1
    assert len(document["servers"]) == 70
    assert len(ENGINEERING_CATALOG) == 70
    assert files("tool_registry.catalog").joinpath("schema.json").is_file()
    assert files("tool_registry.catalog").joinpath("engineering-catalog.yaml").is_file()


def test_catalog_rejects_duplicate_canonical_or_alias_identity() -> None:
    with pytest.raises(CatalogValidationError, match="shared"):
        from tool_registry.catalog_models import CatalogEntry

        _validate_identity(
            [
                CatalogEntry.model_validate(
                    {
                        "id": "one",
                        "name": "One",
                        "vendor": "Test",
                        "description": "One",
                        "domains": ["cad"],
                        "transport": "stdio",
                        "command": "one",
                        "locality": "local",
                        "weight": "light",
                        "aliases": ["legacy"],
                    }
                ),
                CatalogEntry.model_validate(
                    {
                        "id": "two",
                        "name": "Two",
                        "vendor": "Test",
                        "description": "Two",
                        "domains": ["cad"],
                        "transport": "stdio",
                        "command": "two",
                        "locality": "local",
                        "weight": "light",
                        "aliases": ["legacy"],
                    }
                ),
            ]
        )
    assert isinstance(catalog_aliases(), dict)


def test_catalog_passed_validation_requires_environment_evidence() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="passed validation requires"):
        from tool_registry.catalog_models import CatalogEntry

        _validate_evidence(
            [
                CatalogEntry.model_validate(
                    {
                        "id": "unsafe-claim",
                        "name": "Unsafe",
                        "vendor": "Test",
                        "description": "Unsafe",
                        "domains": ["cad"],
                        "transport": "stdio",
                        "command": "unsafe",
                        "locality": "local",
                        "weight": "light",
                        "validation_result": {"status": "passed", "message": "claimed"},
                    }
                )
            ]
        )


def test_catalog_high_risk_entries_are_not_default_enabled() -> None:
    for entry in ENGINEERING_CATALOG:
        if entry["risk_level"] in {"medium", "high", "safety-critical"}:
            assert entry["default_enabled"] is False, entry["server_id"]


def test_researched_entries_carry_source_and_runtime_metadata() -> None:
    document = load_catalog_document()
    entries = {
        entry["id"]: CatalogEntry.model_validate(entry) for entry in document["servers"]
    }

    matlab = entries["matlab-mcp-server"]
    assert matlab.maturity == "official"
    assert matlab.auth_model == "license-server"
    assert matlab.repository_url == "https://github.com/matlab/matlab-mcp-server"
    assert matlab.runtime_requirements.docker == "no"
    assert matlab.source_records[0].primary is True

    fusion_data = entries["autodesk-fusion-data-mcp"]
    assert fusion_data.auth_model == "oauth"
    assert fusion_data.locality == "remote"
    assert fusion_data.runtime_requirements.docker == "yes"

    rhino = entries["rhino-mcp-easehee"]
    assert rhino.runtime_requirements.docker == "yes"
    assert "STEP, IGES, STL, OBJ, IFC, and gbXML workflows" in rhino.capability_summary

    rescale = entries["rescale-mcp-hosted"]
    assert rescale.maturity == "official"
    assert rescale.transport == "sse"
    assert rescale.auth_model == "api-key"
    assert rescale.runtime_requirements.docker == "yes"

    pyfluent = entries["ansys-fluent-mcp"]
    assert pyfluent.vendor == "Ansys"
    assert pyfluent.maturity == "official"
    assert pyfluent.runtime_requirements.docker == "partial"

    backflip = entries["backflip-ai-watchlist"]
    assert backflip.verification_state == "watchlist"
    assert backflip.installability_tier == "blocked"
    assert (
        "No verified public MCP server as of the latest sweep"
        in backflip.capability_summary
    )

    omniverse_kit = entries["nvidia-omniverse-kit-mcp"]
    assert omniverse_kit.maturity == "official"
    assert omniverse_kit.runtime_requirements.docker == "yes"
    assert "NVIDIA_API_KEY" in {env.name for env in omniverse_kit.env_vars}


def test_platform_filter_selects_gb10_candidates_without_desktop_hosts() -> None:
    entries = [
        CatalogEntry.model_validate(entry)
        for entry in load_catalog_document()["servers"]
    ]

    strict = {
        entry.id
        for entry in filter_catalog_entries(entries, "gb10", require_docker=True)
    }
    candidates = {
        entry.id
        for entry in filter_catalog_entries(
            entries, "gb10", mode="candidate", require_docker=True
        )
    }

    assert "autodesk-product-help-mcp" in strict
    assert "autodesk-fusion-desktop-mcp" not in candidates
    assert "matlab-mcp-server" not in candidates
    assert "autodesk-fusion-data-mcp" in candidates
    assert "brep-mcp" in candidates


def test_remote_catalog_text_uses_same_validation_contract() -> None:
    document = load_catalog_document_from_text(
        """
servers:
- id: remote-ok
  name: Remote OK
  vendor: Test
  description: Remote catalog entry
  domains: [cad]
  transport: stdio
  command: remote-ok
  source_url: https://example.test/remote-ok
  repository_url: https://example.test/remote-ok
  auth_model: none
  install_method: source
  maturity: community
  capability_summary: [probe]
  source_records:
  - url: https://example.test/remote-ok
    kind: repository
    primary: true
    observed_at: '2026-08-12'
  runtime_requirements:
    docker: 'yes'
  locality: local
  weight: light
format_version: 1
"""
    )

    assert document["servers"][0]["id"] == "remote-ok"
    assert document["servers"][0]["runtime_requirements"]["docker"] == "yes"
