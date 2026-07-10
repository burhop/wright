from api.config import DATABASE_PATH
from tool_registry.db import get_servers


def test_seeded_engineering_catalog_metadata_loads_through_models():
    servers = get_servers(DATABASE_PATH)

    assert len(servers) >= 40
    assert all(server.platform_support for server in servers)


def test_api_seed_helper_uses_shared_catalog_normalization():
    from tool_registry.catalog_models import CatalogEntry, REQUIRED_PLATFORM_KEYS
    from tool_registry.catalog_loader import catalog_entry_to_mcp_seed

    entry = CatalogEntry(
        id="shared-sample",
        name="Shared Sample",
        vendor="Wright",
        description="Sample",
        domains=["cad"],
        transport="stdio",
        command=["uvx", "shared-sample"],
        locality="local",
        weight="light",
        risk_level="medium",
    )

    seed = catalog_entry_to_mcp_seed(entry)

    assert seed["server_id"] == "shared-sample"
    assert seed["type"] == "stdio"
    assert seed["category"] == "cad"
    assert seed["default_enabled"] is False
    assert set(REQUIRED_PLATFORM_KEYS).issubset(seed["platform_support"])


def test_api_migration_contains_no_catalog_behavior():
    import inspect

    from api.database import migrate

    source = inspect.getsource(migrate)
    assert "ENGINEERING_CATALOG" not in source
    assert "mcp_servers" not in source


def test_fresh_engineering_catalog_seed_does_not_preinstall_mcps(tmp_path, monkeypatch):
    from api.database import migrate

    db_path = tmp_path / "fresh-seed.db"
    monkeypatch.setattr(migrate, "DATABASE_PATH", str(db_path))

    migrate.run_migrations()
    from tool_registry.catalog_reconcile import reconcile_engineering_catalog

    reconcile_engineering_catalog(str(db_path))
    servers = get_servers(str(db_path))

    assert servers
    assert all(not server.is_installed for server in servers)
    assert all(not server.is_active for server in servers)


def test_autodesk_product_help_seed_uses_official_remote_mcp_endpoint(
    tmp_path, monkeypatch
):
    from api.database import migrate

    db_path = tmp_path / "autodesk-product-help-seed.db"
    monkeypatch.setattr(migrate, "DATABASE_PATH", str(db_path))

    migrate.run_migrations()
    from tool_registry.catalog_reconcile import reconcile_engineering_catalog

    reconcile_engineering_catalog(str(db_path))
    autodesk_help = next(
        server
        for server in get_servers(str(db_path))
        if server.server_id == "autodesk-product-help-mcp"
    )

    assert (
        autodesk_help.command
        == "https://developer.api.autodesk.com/knowledge/public/v1/mcp"
    )
    assert (
        autodesk_help.source_url
        == "https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_KnowledgeMcp_autodesk_product_help_mcp_server_html"
    )
    assert autodesk_help.verification_state == "verified_docs_mcp"
    assert autodesk_help.installability_tier == "tested"
    assert autodesk_help.install_blocked_reason is None
    assert autodesk_help.validation_result.status == "passed"
    assert "get_available_products" in autodesk_help.validation_result.message


def test_migration_clears_failed_catalog_installs_including_openscad(
    tmp_path, monkeypatch
):
    import sqlite3
    from api.database import migrate

    db_path = tmp_path / "cleanup-seed.db"
    monkeypatch.setattr(migrate, "DATABASE_PATH", str(db_path))

    migrate.run_migrations()
    from tool_registry.catalog_reconcile import reconcile_engineering_catalog

    reconcile_engineering_catalog(str(db_path))
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

    reconcile_engineering_catalog(str(db_path))
    openscad = next(
        server
        for server in get_servers(str(db_path))
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
