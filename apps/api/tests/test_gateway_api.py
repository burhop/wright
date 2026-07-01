import pytest
import sqlite3
import asyncio
from fastapi.testclient import TestClient
from api.main import app
from tool_registry import McpServer, McpTool
from tool_registry.db import insert_server, insert_tools


@pytest.fixture
def test_client():
    """Fixture that enters TestClient context manager to trigger lifespan startup."""
    with TestClient(app) as c:
        yield c
    db_path = app.state.mcp_engine.db_path
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "DELETE FROM mcp_tools WHERE server_id IN (?, ?, ?)",
            ("calc-id-123", "gateway-active-server", "gateway-newer-server"),
        )
        conn.execute(
            "DELETE FROM mcp_servers WHERE server_id IN (?, ?, ?)",
            ("calc-id-123", "gateway-active-server", "gateway-newer-server"),
        )
        conn.execute(
            "DELETE FROM engineering_workspaces WHERE workspace_id IN (?, ?, ?)",
            ("ws-123", "gateway-active-ws", "gateway-newer-ws"),
        )
        conn.execute(
            "DELETE FROM system_settings WHERE key = 'active_gateway_session_id'"
        )
        conn.commit()
    finally:
        conn.close()


def test_gateway_tools_endpoint(test_client):
    # Pre-seed a default server
    db_path = app.state.mcp_engine.db_path

    server = McpServer(
        server_id="calc-id-123",
        name="Calcul mesh",
        type="stdio",
        command=["uv", "run", "calc"],
        is_active=True,
        is_installed=True,
        status="active",
        created_at=1000,
        updated_at=1000,
    )
    insert_server(db_path, server)

    # Pre-seed a tool
    tool = McpTool(
        tool_id="calc-id-123:mesh_calc",
        server_id="calc-id-123",
        name="mesh_calc",
        description="Calculate mesh",
        input_schema={"type": "object"},
        is_enabled=True,
        created_at=1000,
    )
    insert_tools(db_path, [tool])

    # Pre-seed active workspace in database
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO engineering_workspaces (
            workspace_id, workspace_name, local_path, session_id, enabled_tools, created_at, updated_at
        ) VALUES ('ws-123', 'Test Workspace', '/tmp/ws', 'session-123', '["Calcul mesh"]', 1000, 2000)
        """
    )
    conn.commit()
    conn.close()

    # Query gateway tools
    response = test_client.get("/api/gateway/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "calculmesh__mesh_calc"
    assert data["tools"][0]["description"] == "Calculate mesh"


def test_mcp_router_uses_generic_wright_gateway_sync():
    from api.routers import mcp

    assert "sync_mcp_server_to_hermes" not in vars(mcp)
    assert (
        mcp.sync_mcp_server_to_wright_gateway.__module__
        == "api.services.wright_gateway_sync"
    )


def test_gateway_tools_prefers_pinned_active_session(test_client):
    db_path = app.state.mcp_engine.db_path
    active_server_id = "gateway-active-server"
    newer_server_id = "gateway-newer-server"

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "DELETE FROM mcp_tools WHERE server_id IN (?, ?)",
            (active_server_id, newer_server_id),
        )
        conn.execute(
            "DELETE FROM mcp_servers WHERE server_id IN (?, ?)",
            (active_server_id, newer_server_id),
        )
        conn.execute(
            "DELETE FROM engineering_workspaces WHERE session_id IN (?, ?)",
            ("gateway-active-session", "gateway-newer-session"),
        )
        conn.execute(
            "DELETE FROM system_settings WHERE key = 'active_gateway_session_id'"
        )
        conn.commit()
    finally:
        conn.close()

    insert_server(
        db_path,
        McpServer(
            server_id=active_server_id,
            name="Active CAD",
            type="stdio",
            command=["uv", "run", "active-cad"],
            is_active=True,
            is_installed=True,
            status="active",
            created_at=1000,
            updated_at=1000,
        ),
    )
    insert_server(
        db_path,
        McpServer(
            server_id=newer_server_id,
            name="Newer CAD",
            type="stdio",
            command=["uv", "run", "newer-cad"],
            is_active=True,
            is_installed=True,
            status="active",
            created_at=1000,
            updated_at=1000,
        ),
    )
    insert_tools(
        db_path,
        [
            McpTool(
                tool_id=f"{active_server_id}:active_tool",
                server_id=active_server_id,
                name="active_tool",
                description="Active session tool",
                input_schema={"type": "object"},
                is_enabled=True,
                created_at=1000,
            ),
            McpTool(
                tool_id=f"{newer_server_id}:newer_tool",
                server_id=newer_server_id,
                name="newer_tool",
                description="Newer workspace tool",
                input_schema={"type": "object"},
                is_enabled=True,
                created_at=1000,
            ),
        ],
    )

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO engineering_workspaces (
                workspace_id, workspace_name, local_path, session_id, enabled_tools, created_at, updated_at
            ) VALUES
                ('gateway-active-ws', 'Active Workspace', '/tmp/active-ws', 'gateway-active-session', '["Active CAD"]', 1000, 2000),
                ('gateway-newer-ws', 'Newer Workspace', '/tmp/newer-ws', 'gateway-newer-session', '["Newer CAD"]', 1000, 3000)
            """
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO system_settings (key, value)
            VALUES ('active_gateway_session_id', 'gateway-active-session')
            """
        )
        conn.commit()
    finally:
        conn.close()

    response = test_client.get("/api/gateway/tools")

    assert response.status_code == 200
    tool_names = [tool["name"] for tool in response.json()["tools"]]
    assert "activecad__active_tool" in tool_names
    assert "newercad__newer_tool" not in tool_names


def test_gateway_call_endpoint(test_client):
    # Pre-seed default server and tool first
    db_path = app.state.mcp_engine.db_path

    server = McpServer(
        server_id="calc-id-123",
        name="Calcul mesh",
        type="stdio",
        command=["uv", "run", "calc"],
        is_active=True,
        is_installed=True,
        status="active",
        created_at=1000,
        updated_at=1000,
    )
    insert_server(db_path, server)

    tool = McpTool(
        tool_id="calc-id-123:mesh_calc",
        server_id="calc-id-123",
        name="mesh_calc",
        description="Calculate mesh",
        input_schema={"type": "object"},
        is_enabled=True,
        created_at=1000,
    )
    insert_tools(db_path, [tool])

    # Test calling a tool via the gateway mock runner
    payload = {"name": "calculmesh__mesh_calc", "arguments": {"test": "val"}}
    response = test_client.post("/api/gateway/call", json=payload)
    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.asyncio
async def test_gateway_events_generator():
    from api.routers.gateway import event_generator

    queue = asyncio.Queue()
    gen = event_generator(queue)

    # First yield should be the connection event
    first_event = await gen.__anext__()
    assert first_event == "data: connected\n\n"

    # Put an event in the queue and get it
    await queue.put("list_changed")
    second_event = await gen.__anext__()
    assert second_event == "data: list_changed\n\n"
