from api.config import DATABASE_PATH
from tool_registry.db import get_servers


def test_seeded_engineering_catalog_metadata_loads_through_models():
    servers = get_servers(DATABASE_PATH)

    assert len(servers) >= 40
    assert all(server.platform_support for server in servers)


def test_fresh_engineering_catalog_seed_does_not_preinstall_mcps(tmp_path, monkeypatch):
    from api.database import migrate

    db_path = tmp_path / "fresh-seed.db"
    monkeypatch.setattr(migrate, "DATABASE_PATH", str(db_path))

    migrate.run_migrations()
    servers = get_servers(str(db_path))

    assert servers
    assert all(not server.is_installed for server in servers)
    assert all(not server.is_active for server in servers)


def test_migration_clears_failed_catalog_installs_including_openscad(tmp_path, monkeypatch):
    import sqlite3
    from api.database import migrate

    db_path = tmp_path / "cleanup-seed.db"
    monkeypatch.setattr(migrate, "DATABASE_PATH", str(db_path))

    migrate.run_migrations()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE mcp_servers
            SET is_installed = 1, is_active = 1, status = 'error',
                error_message = 'missing command'
            WHERE server_id = 'openscad-mcp-server'
            """
        )
        conn.commit()

    migrate.run_migrations()
    openscad = next(
        server for server in get_servers(str(db_path))
        if server.server_id == "openscad-mcp-server"
    )

    assert openscad.is_installed is False
    assert openscad.is_active is False
    assert openscad.status == "inactive"
    assert openscad.error_message is None


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
