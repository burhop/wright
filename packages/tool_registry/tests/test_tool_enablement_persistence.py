"""An operator's tool deny survives discovery, stop and API-owner replacement."""

import pytest

from data_vault import upgrade_database
from tool_registry import McpServer
from tool_registry.db import get_tools, insert_server
from tool_registry.lifecycle_adapters import DatabaseLifecycleAdapter
from tool_registry.services import set_tool_enabled


@pytest.mark.asyncio
async def test_tool_deny_survives_stop_and_new_discovery_owner(tmp_path):
    database = str(tmp_path / "state.db")
    upgrade_database(database)
    for identity in ("alpha", "different-provider"):
        insert_server(
            database,
            McpServer(
                server_id=identity,
                name=identity,
                type="stdio",
                command=["unused"],
                is_active=False,
                status="inactive",
                created_at=1,
                updated_at=1,
            ),
        )
    description = [{"name": "inspect", "inputSchema": {"type": "object"}}]
    adapter = DatabaseLifecycleAdapter(database)
    for identity in ("alpha", "different-provider"):
        await adapter.publish_tools(identity, description, 1)
    set_tool_enabled(database, "alpha:inspect", False)
    await adapter.publish_tools("alpha", (), 2)
    assert get_tools(database, "alpha") == []  # Stop still removes callable contracts.
    adapter = DatabaseLifecycleAdapter(database)
    await adapter.publish_tools("alpha", description, 3)
    assert get_tools(database, "alpha")[0].is_enabled is False
    assert get_tools(database, "different-provider")[0].is_enabled is True
    set_tool_enabled(database, "alpha:inspect", True)
    await adapter.publish_tools("alpha", (), 4)
    await DatabaseLifecycleAdapter(database).publish_tools("alpha", description, 5)
    assert get_tools(database, "alpha")[0].is_enabled is True
