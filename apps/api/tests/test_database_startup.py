from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_lifespan_fails_before_runtime_construction_on_migration_error(
    monkeypatch,
):
    from api import main
    from api.database import migrate

    constructed: list[str] = []

    def fail_migration():
        raise RuntimeError("seeded database row must not be logged")

    monkeypatch.setattr(migrate, "run_migrations", fail_migration)
    monkeypatch.setattr(
        main,
        "create_agent_engine",
        lambda **kwargs: constructed.append("agent"),
    )
    monkeypatch.setattr(
        main,
        "AgentSyncManager",
        lambda *args: constructed.append("sync"),
    )
    monkeypatch.setattr(
        main,
        "McpEngine",
        lambda *args: constructed.append("mcp"),
    )
    isolated_app = SimpleNamespace(state=SimpleNamespace())

    with pytest.raises(RuntimeError, match="seeded database row"):
        async with main.lifespan(isolated_app):
            pass

    assert constructed == []


@pytest.mark.asyncio
async def test_lifespan_orders_migration_secret_catalog_before_runtimes(monkeypatch):
    from api import main
    from api.database import migrate, secret_migration
    from tool_registry import catalog_reconcile

    events: list[str] = []

    monkeypatch.setattr(migrate, "run_migrations", lambda: events.append("migration"))
    monkeypatch.setattr(
        secret_migration,
        "migrate_plaintext_secrets",
        lambda path: events.append("secret"),
    )
    monkeypatch.setattr(
        catalog_reconcile,
        "reconcile_active_engineering_catalog",
        lambda path: events.append("catalog") or (0, None),
    )
    monkeypatch.setattr(
        catalog_reconcile,
        "reconcile_wright_managed_servers",
        lambda path: events.append("wright-managed"),
    )
    monkeypatch.setattr(
        main,
        "create_agent_engine",
        lambda **kwargs: events.append("agent") or object(),
    )
    monkeypatch.setattr(
        main,
        "AgentSyncManager",
        lambda *args: events.append("sync") or object(),
    )

    class FakeMcpEngine:
        def __init__(self, *args, **kwargs):
            events.append("mcp")
            assert kwargs["operation_timeout"] == 30.0

        async def shutdown(self):
            events.append("shutdown")

        async def sync_active_servers(self):
            events.append("reconcile")

    monkeypatch.setattr(main, "McpEngine", FakeMcpEngine)

    class FakeNative:
        async def startup(self):
            events.append("native-startup")

        async def close(self):
            events.append("native-close")

    def native_service(db_path, gateway, workspace):
        assert gateway.lifecycle is not None
        events.append("native-build")
        return FakeNative()

    monkeypatch.setattr(main, "build_native_process_service", native_service)
    isolated_app = SimpleNamespace(state=SimpleNamespace())

    async with main.lifespan(isolated_app):
        events.append("serving")

    assert events == [
        "migration",
        "secret",
        "catalog",
        "wright-managed",
        "agent",
        "sync",
        "mcp",
        "reconcile",
        "native-build",
        "native-startup",
        "serving",
        "native-close",
        "shutdown",
    ]
