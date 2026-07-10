import os
import tempfile
import pytest
import sqlite3
import asyncio
import json
from data_vault import upgrade_database
from fastapi.testclient import TestClient
from api.main import app
from tool_registry import McpEngine, McpServer
from tool_registry.db import insert_server
from api.security import SecuritySettings
from starlette.websockets import WebSocketDisconnect


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
    conn.commit()
    conn.close()
    upgrade_database(path)

    yield path

    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def client(test_db_path) -> TestClient:
    server = McpServer(
        server_id="webmcp-id-123",
        name="WebMCP Viewer",
        type="webmcp",
        command=None,
        is_active=True,
        status="active",
        created_at=1000,
        updated_at=1000,
    )
    insert_server(test_db_path, server)

    with TestClient(app) as c:
        engine = McpEngine(test_db_path)
        c.app.state.mcp_engine = engine
        yield c


class MockWebSocket:
    def __init__(self):
        self.sent_messages = []

    async def accept(self):
        pass

    async def send_text(self, text: str):
        self.sent_messages.append(text)


def test_webmcp_websocket_connection(client):
    with client.websocket_connect("/api/webmcp/ws"):
        # Check connection is active and we can close it
        pass


def test_webmcp_rejects_missing_token_and_bad_origin(client):
    previous = app.state.security_settings
    app.state.security_settings = SecuritySettings(
        "enforced", "websocket-token", ("http://localhost:5173",), "127.0.0.1"
    )
    try:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                "/api/webmcp/ws", headers={"origin": "https://evil.example"}
            ):
                pass
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                "/api/webmcp/ws", headers={"origin": "http://localhost:5173"}
            ):
                pass
        with client.websocket_connect(
            "/api/webmcp/ws",
            headers={
                "origin": "http://localhost:5173",
                "authorization": "Bearer websocket-token",
            },
        ):
            pass
    finally:
        app.state.security_settings = previous


@pytest.mark.asyncio
async def test_webmcp_tool_call_bridging(test_db_path):
    server = McpServer(
        server_id="webmcp-id-123",
        name="WebMCP Viewer",
        type="webmcp",
        command=None,
        is_active=True,
        status="active",
        created_at=1000,
        updated_at=1000,
    )
    insert_server(test_db_path, server)

    mcp_engine = McpEngine(test_db_path)
    mock_ws = MockWebSocket()
    await mcp_engine.register_webmcp_connection(mock_ws)

    # Run call_tool concurrently
    async def call_tool_task():
        return await mcp_engine.call_tool(
            "webmcp-id-123", "get_selected_part", {"mock_arg": "val"}
        )

    task = asyncio.create_task(call_tool_task())

    # Yield control to let call_tool register and send payload
    await asyncio.sleep(0.05)

    # Verify WebSocket sent the request
    assert len(mock_ws.sent_messages) == 1
    received_data = json.loads(mock_ws.sent_messages[0])
    assert received_data["method"] == "get_selected_part"
    assert received_data["params"] == {"mock_arg": "val"}
    call_id = received_data["id"]

    # Send response back to engine
    response_payload = {
        "jsonrpc": "2.0",
        "id": call_id,
        "result": {"part_id": "part-123"},
    }
    await mcp_engine.handle_webmcp_message(json.dumps(response_payload))

    # Await result
    result = await task
    assert result == {"part_id": "part-123"}
