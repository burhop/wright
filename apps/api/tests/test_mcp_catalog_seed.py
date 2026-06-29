from api.config import DATABASE_PATH
from tool_registry.db import get_servers


def test_seeded_engineering_catalog_metadata_loads_through_models():
    servers = get_servers(DATABASE_PATH)

    assert len(servers) >= 40
    assert all(server.platform_support for server in servers)


def test_kicad_seed_preserves_partial_result_as_user_facing_notes():
    servers = get_servers(DATABASE_PATH)
    kicad = next(
        server for server in servers if server.server_id == "kicad-mcp-lamaalrajih"
    )

    linux = kicad.platform_support["linux_x64"]
    assert linux.status == "no"
    assert linux.tested is True
    assert "project discovery worked" in linux.notes
    assert "11 of 16 tools" in linux.notes
    assert "ctx" in linux.notes
    assert kicad.validation_result.status == "failed"
    assert "run_drc_check" in kicad.validation_result.message
