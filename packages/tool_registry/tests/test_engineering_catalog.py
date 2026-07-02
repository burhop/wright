from tool_registry.catalog_models import REQUIRED_PLATFORM_KEYS
from tool_registry.engineering_catalog import ENGINEERING_CATALOG
from tool_registry.mcp_catalog import tier_sort_key


def test_engineering_catalog_is_package_owned_and_normalized():
    assert len(ENGINEERING_CATALOG) >= 40

    seen_ids = set()
    for entry in ENGINEERING_CATALOG:
        assert entry["server_id"] not in seen_ids
        seen_ids.add(entry["server_id"])
        assert entry["verification_state"]
        assert entry["installability_tier"]
        assert entry["risk_level"]
        assert set(REQUIRED_PLATFORM_KEYS).issubset(entry["platform_support"])
        assert isinstance(entry["host_software_required"], list)
        assert isinstance(entry["credentials_required"], list)
        assert isinstance(entry["approval_gates"], list)
        assert isinstance(entry["validation_result"], dict)

    assert "openscad-mcp-server" in seen_ids
    assert "autodesk-product-help-mcp" in seen_ids
    assert ENGINEERING_CATALOG == sorted(ENGINEERING_CATALOG, key=tier_sort_key)
