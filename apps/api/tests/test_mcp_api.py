import os
import tempfile
import pytest
import sqlite3
from fastapi.testclient import TestClient
from api.main import app
from tool_registry import McpEngine, McpServer, McpTool
from tool_registry.db import insert_server, insert_tools

@pytest.fixture
def test_db_path() -> str:
    # Use a temporary file for the SQLite DB
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    conn = sqlite3.connect(path)
    conn.execute("""
    CREATE TABLE mcp_servers (
        server_id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL CHECK(type IN ('stdio', 'sse', 'webmcp')),
        command TEXT,
        is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0, 1)),
        is_installed INTEGER NOT NULL DEFAULT 0 CHECK(is_installed IN (0, 1)),
        status TEXT NOT NULL DEFAULT 'inactive' CHECK(status IN ('active', 'inactive', 'error')),
        error_message TEXT,
        category TEXT NOT NULL DEFAULT 'utilities',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
    );
    """)
    conn.execute("""
    CREATE TABLE mcp_tools (
        tool_id TEXT PRIMARY KEY,
        server_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        input_schema TEXT NOT NULL,
        is_enabled INTEGER NOT NULL DEFAULT 1 CHECK(is_enabled IN (0, 1)),
        created_at INTEGER NOT NULL,
        FOREIGN KEY (server_id) REFERENCES mcp_servers(server_id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()
    
    yield path
    
    if os.path.exists(path):
        os.unlink(path)

@pytest.fixture
def client(test_db_path) -> TestClient:
    # Pre-seed a default server
    server = McpServer(
        server_id="calc-id-123",
        name="Calcul mesh",
        type="stdio",
        command=["uv", "run", "calc"],
        is_active=False,
        status="inactive",
        created_at=1000,
        updated_at=1000
    )
    insert_server(test_db_path, server)
    
    # Pre-seed a tool
    tool = McpTool(
        tool_id="calc-id-123:mesh_calc",
        server_id="calc-id-123",
        name="mesh_calc",
        description="Calculate mesh",
        input_schema={"type": "object"},
        is_enabled=True,
        created_at=1000
    )
    insert_tools(test_db_path, [tool])

    with TestClient(app) as c:
        engine = McpEngine(test_db_path)
        c.app.state.mcp_engine = engine
        yield c

def test_list_servers(client):
    response = client.get("/api/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert len(data["servers"]) == 1
    assert data["servers"][0]["server_id"] == "calc-id-123"
    assert data["servers"][0]["name"] == "Calcul mesh"

def test_register_server(client):
    payload = {
        "name": "Custom SSE Link",
        "type": "sse",
        "command": "http://127.0.0.1:9000/sse",
        "category": "simulation"
    }
    response = client.post("/api/mcp/servers", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "server_id" in data
    assert data["name"] == "Custom SSE Link"
    assert data["status"] == "inactive"
    
    # Verify it was added to database
    servers_res = client.get("/api/mcp/servers")
    servers = servers_res.json()["servers"]
    assert len(servers) == 2
    assert any(s["name"] == "Custom SSE Link" for s in servers)

def test_register_duplicate_server_fails(client):
    payload = {
        "name": "Calcul mesh",
        "type": "stdio",
        "command": ["python", "foo.py"],
        "category": "utilities"
    }
    response = client.post("/api/mcp/servers", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_toggle_server_not_found(client):
    response = client.patch("/api/mcp/servers/nonexistent-id", json={"is_active": True})
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_delete_server(client):
    response = client.delete("/api/mcp/servers/calc-id-123")
    assert response.status_code == 204
    
    # Verify it was deleted
    servers_res = client.get("/api/mcp/servers")
    servers = servers_res.json()["servers"]
    assert len(servers) == 0

def test_list_tools(client):
    response = client.get("/api/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "mesh_calc"
    assert data["tools"][0]["is_enabled"] is True

def test_toggle_tool_enabled(client):
    response = client.patch("/api/mcp/tools/calc-id-123:mesh_calc", json={"is_enabled": False})
    assert response.status_code == 200
    assert response.json()["is_enabled"] is False

    # Check database status
    tools_res = client.get("/api/mcp/tools")
    tools = tools_res.json()["tools"]
    assert tools[0]["is_enabled"] is False
