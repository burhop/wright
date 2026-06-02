import os
import sys
import uuid
import time
import pytest
import sqlite3
from tool_registry.models import McpServer, McpTool
from tool_registry.db import (
    get_servers,
    get_server,
    insert_server,
    update_server,
    delete_server,
    get_tools,
)
from tool_registry.runners.stdio import StdioRunner
from tool_registry.manager import McpEngine

@pytest.fixture
def temp_db_path(tmp_path) -> str:
    db_file = tmp_path / "test_state.db"
    db_path = str(db_file)
    conn = sqlite3.connect(db_path)
    conn.execute("""
    CREATE TABLE mcp_servers (
        server_id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL CHECK(type IN ('stdio', 'sse', 'webmcp')),
        command TEXT,
        is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0, 1)),
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
    return db_path

def test_pydantic_models():
    server = McpServer(
        server_id="test-id",
        name="Test CLI",
        type="stdio",
        command=["uv", "run", "cli"],
        is_active=True,
        status="active",
        category="simulation",
        created_at=123,
        updated_at=456
    )
    assert server.name == "Test CLI"
    assert server.command == ["uv", "run", "cli"]
    assert server.is_active is True

    tool = McpTool(
        tool_id="test-id:tool",
        server_id="test-id",
        name="tool",
        description="test desc",
        input_schema={"type": "object"},
        is_enabled=True,
        created_at=123
    )
    assert tool.name == "tool"
    assert tool.input_schema == {"type": "object"}

def test_database_crud(temp_db_path):
    # Insert Server
    server_id = str(uuid.uuid4())
    server = McpServer(
        server_id=server_id,
        name="Test SQLite Server",
        type="stdio",
        command=["python", "test.py"],
        is_active=False,
        status="inactive",
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    insert_server(temp_db_path, server)

    # Get Server
    fetched = get_server(temp_db_path, server_id)
    assert fetched is not None
    assert fetched.name == "Test SQLite Server"
    assert fetched.command == ["python", "test.py"]
    assert fetched.is_active is False

    # Get Servers list
    servers = get_servers(temp_db_path)
    assert len(servers) == 1

    # Update Server
    updated = update_server(temp_db_path, server_id, {"is_active": True, "status": "active"})
    assert updated.is_active is True
    assert updated.status == "active"

    # Delete Server
    assert delete_server(temp_db_path, server_id) is True
    assert get_server(temp_db_path, server_id) is None

@pytest.mark.asyncio
async def test_stdio_runner_mock():
    mock_server_path = os.path.join(os.path.dirname(__file__), "mock_server.py")
    cmd = [sys.executable, mock_server_path]
    runner = StdioRunner(cmd)

    await runner.start()
    assert runner.is_running() is True

    # List Tools
    tools = await runner.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"

    # Call Tool
    res = await runner.call_tool("test_tool", {"val": "hello"})
    assert "content" in res
    assert "Called test_tool with: {\"val\": \"hello\"}" in res["content"][0]["text"]

    await runner.stop()
    assert runner.is_running() is False

@pytest.mark.asyncio
async def test_mcp_engine(temp_db_path):
    mock_server_path = os.path.join(os.path.dirname(__file__), "mock_server.py")
    server_id = str(uuid.uuid4())
    server = McpServer(
        server_id=server_id,
        name="Mock MCP Server Engine Test",
        type="stdio",
        command=[sys.executable, mock_server_path],
        is_active=False,
        status="inactive",
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    insert_server(temp_db_path, server)

    engine = McpEngine(temp_db_path)

    # Start Server through Engine
    updated_server = await engine.start_server(server_id)
    assert updated_server.is_active is True
    assert updated_server.status == "active"

    # Verify tools registered in DB
    tools = get_tools(temp_db_path, server_id)
    assert len(tools) == 1
    assert tools[0].name == "test_tool"
    assert tools[0].input_schema == {
        "type": "object",
        "properties": {"val": {"type": "string"}},
        "required": ["val"]
    }

    # Call tool through Engine
    res = await engine.call_tool(server_id, "test_tool", {"val": "engine_test"})
    assert "content" in res
    assert "Called test_tool with: {\"val\": \"engine_test\"}" in res["content"][0]["text"]

    # Stop Server
    stopped_server = await engine.stop_server(server_id)
    assert stopped_server.is_active is False
    assert stopped_server.status == "inactive"

    # Verify tools cleared from DB
    tools_after = get_tools(temp_db_path, server_id)
    assert len(tools_after) == 0

    await engine.shutdown()
