from pathlib import Path

import pytest

from tool_registry.catalog_loader import (
    catalog_entry_to_mcp_seed,
    load_catalog_entries,
    normalize_mcp_seed_entry,
)
from tool_registry.catalog_models import REQUIRED_PLATFORM_KEYS

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalized_seed_entry_fills_shared_defaults():
    entry = normalize_mcp_seed_entry(
        {
            "server_id": "sample",
            "name": "Sample",
            "type": "stdio",
            "command": ["uvx", "sample"],
            "category": "cad",
        }
    )

    assert set(REQUIRED_PLATFORM_KEYS).issubset(entry["platform_support"])
    assert entry["validation_result"]["status"] == "not_tested"
    assert entry["installability_tier"] == "might_work"
    assert entry["default_enabled"] is True


def test_high_risk_seed_entry_defaults_disabled():
    entry = normalize_mcp_seed_entry(
        {
            "server_id": "risky",
            "name": "Risky",
            "type": "stdio",
            "command": ["python", "server.py"],
            "category": "cad",
        },
        {"risk_level": "high"},
    )

    assert entry["risk_level"] == "high"
    assert entry["default_enabled"] is False


def test_load_catalog_entries_normalizes_and_converts_to_seed(tmp_path):
    catalog_file = FIXTURES / "catalog_normalization.yaml"

    entry = load_catalog_entries(catalog_file)[0]

    assert entry.platform_support["linux_x64"].status == "yes"
    assert set(REQUIRED_PLATFORM_KEYS).issubset(entry.platform_support)
    assert entry.default_enabled is False

    seed = catalog_entry_to_mcp_seed(entry)
    assert seed["server_id"] == "risky"
    assert seed["type"] == "stdio"
    assert seed["category"] == "cad"
    assert seed["default_enabled"] is False
    assert seed["platform_support"]["linux_x64"]["tested"] is True


def test_duplicate_catalog_ids_are_rejected(tmp_path):
    catalog_file = tmp_path / "catalog.yaml"
    catalog_file.write_text(
        """
servers:
  - id: duplicate
    name: First
    vendor: Test
    description: Test
    domains: [cad]
    transport: stdio
    command: test
    locality: local
    weight: light
  - id: duplicate
    name: Second
    vendor: Test
    description: Test
    domains: [fea]
    transport: stdio
    command: test
    locality: local
    weight: light
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate catalog entry ID"):
        load_catalog_entries(catalog_file)


def test_invalid_catalog_entries_are_rejected(tmp_path):
    catalog_file = tmp_path / "catalog.yaml"
    catalog_file.write_text(
        """
servers:
  - id: invalid
    name: Invalid
    vendor: Test
    description: Test
    domains: [cad]
    transport: magic
    command: test
    locality: local
    weight: light
""",
        encoding="utf-8",
    )

    with pytest.raises(Exception):
        load_catalog_entries(catalog_file)
