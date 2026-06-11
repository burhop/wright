import pytest
import sqlite3
import json
import asyncio
from fastapi.testclient import TestClient
from api.main import app
from api.config import DATABASE_PATH
from tool_registry import McpServer, McpTool
from tool_registry.db import insert_server, insert_tools

@pytest.fixture
def test_client():
    """Fixture that enters TestClient context manager to trigger lifespan startup."""
    with TestClient(app) as c:
        yield c

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
    payload = {
        "name": "calculmesh__mesh_calc",
        "arguments": {"test": "val"}
    }
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
