from importlib.resources import files

import pytest

from tool_registry.canonical_catalog import (
    CatalogValidationError,
    _validate_evidence,
    _validate_identity,
    catalog_aliases,
    load_catalog_document,
)
from tool_registry.engineering_catalog import ENGINEERING_CATALOG


def test_canonical_catalog_resource_is_schema_valid_and_exact() -> None:
    document = load_catalog_document()
    assert document["format_version"] == 1
    assert len(document["servers"]) == 42
    assert len(ENGINEERING_CATALOG) == 42
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
