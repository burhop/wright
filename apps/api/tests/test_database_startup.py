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
        "reconcile_engineering_catalog",
        lambda path: events.append("catalog"),
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
        def __init__(self, *args):
            events.append("mcp")

        async def shutdown(self):
            events.append("shutdown")

        async def sync_active_servers(self):
            events.append("reconcile")

    monkeypatch.setattr(main, "McpEngine", FakeMcpEngine)
    isolated_app = SimpleNamespace(state=SimpleNamespace())

    async with main.lifespan(isolated_app):
        events.append("serving")

    assert events == [
        "migration",
        "secret",
        "catalog",
        "agent",
        "sync",
        "mcp",
        "reconcile",
        "serving",
        "shutdown",
    ]
