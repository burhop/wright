from __future__ import annotations

import pytest

from tool_registry.canonical_catalog import (
    CatalogValidationError,
    catalog_aliases,
    load_canonical_entries,
    load_catalog_document_from_text,
)
from tool_registry.catalog_evidence import validate_catalog_evidence
from tool_registry.catalog_models import CatalogEntry, conservative_evidence_class


def _entry(**updates) -> CatalogEntry:
    values = {
        "id": "example",
        "name": "Example",
        "vendor": "Example vendor",
        "description": "Example capability",
        "domains": ["cad"],
        "transport": "stdio",
        "command": ["example"],
        "locality": "local",
        "weight": "light",
    }
    values.update(updates)
    return CatalogEntry.model_validate(values)


def test_legacy_mapping_never_infers_official_status() -> None:
    assert (
        conservative_evidence_class(
            _entry(verification_state="verified_mcp", maturity="official")
        )
        == "verified_community"
    )
    assert (
        conservative_evidence_class(
            _entry(verification_state="verified_api_wrapper_candidate")
        )
        == "api_wrapper_candidate"
    )
    assert (
        conservative_evidence_class(_entry(verification_state="watchlist"))
        == "user_reported_source_needed"
    )


def test_official_claim_requires_primary_authoritative_vendor_source() -> None:
    entry = _entry(
        maturity="official",
        evidence_class="official_preview",
        default_enabled=False,
        source_records=[
            {
                "url": "https://directory.example/mcp",
                "kind": "directory",
                "primary": True,
                "authority": "directory",
            }
        ],
    )
    with pytest.raises(ValueError, match="vendor or publisher"):
        validate_catalog_evidence(entry)

    entry.source_records[0] = entry.source_records[0].model_copy(
        update={"kind": "vendor_docs", "authority": "vendor"}
    )
    validate_catalog_evidence(entry)


def test_schema_validation_rejects_unsupported_official_claim() -> None:
    with pytest.raises(CatalogValidationError, match="vendor or publisher"):
        load_catalog_document_from_text(
            """
format_version: 1
servers:
- id: unsupported-official
  name: Unsupported Official
  vendor: Example
  description: Unsupported claim
  domains: [cad]
  transport: stdio
  command: example
  locality: local
  weight: light
  maturity: official
  evidence_class: official_production
  source_records:
  - url: https://example.test/community
    kind: repository
    authority: community
"""
        )


def test_onshape_official_preview_is_distinct_and_vendor_grounded() -> None:
    entries = {entry.id: entry for entry in load_canonical_entries()}
    official = entries["onshape-labs-featurescript-mcp"]

    assert official.evidence_class == "official_preview"
    assert official.transport == "streamable_http"
    assert official.command == "https://fs-mcp.labs.onshape.app/mcp"
    assert official.default_enabled is False
    assert official.validation_result.status == "not_tested"
    assert official.auth_model == "unknown"
    assert any(
        source.primary and source.authority == "vendor" and source.kind == "vendor_docs"
        for source in official.source_records
    )
    assert "jarvis-onshape-mcp" in entries
    assert "onshape-mcp-hedless" in entries
    assert catalog_aliases()["onshape-featurescript-mcp-official"] == (
        "onshape-labs-featurescript-mcp"
    )
