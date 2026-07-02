from pathlib import Path


def test_api_boot_uses_agent_registry_instead_of_direct_hermes_adapter_import():
    source = Path("apps/api/src/api/main.py").read_text(encoding="utf-8")

    assert "HermesAdapter" not in source
    assert "create_agent_engine" in source
