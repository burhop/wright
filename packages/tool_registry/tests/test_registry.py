import os
import sys
import uuid
import time
import pytest
from data_vault import upgrade_database
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
from tool_registry.models import EnvVarDefinition


@pytest.fixture
def temp_db_path(tmp_path) -> str:
    db_file = tmp_path / "test_state.db"
    db_path = str(db_file)
    upgrade_database(db_path)
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
        updated_at=456,
        env_vars={"KEY": "VAL"},
    )
    assert server.name == "Test CLI"
    assert server.command == ["uv", "run", "cli"]
    assert server.is_active is True
    assert server.env_vars == {"KEY": "VAL"}

    tool = McpTool(
        tool_id="test-id:tool",
        server_id="test-id",
        name="tool",
        description="test desc",
        input_schema={"type": "object"},
        is_enabled=True,
        created_at=123,
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
        updated_at=int(time.time()),
        env_vars={"MY_ENV_VAR": "my_val"},
    )
    insert_server(temp_db_path, server)

    # Get Server
    fetched = get_server(temp_db_path, server_id)
    assert fetched is not None
    assert fetched.name == "Test SQLite Server"
    assert fetched.command == ["python", "test.py"]
    assert fetched.is_active is False
    assert fetched.env_vars == {"MY_ENV_VAR": "my_val"}

    # Get Servers list
    servers = get_servers(temp_db_path)
    assert len(servers) == 1

    # Update Server
    updated = update_server(
        temp_db_path,
        server_id,
        {"is_active": True, "status": "active", "env_vars": {"NEW_VAR": "new_val"}},
    )
    assert updated.is_active is True
    assert updated.status == "active"
    assert updated.env_vars == {"NEW_VAR": "new_val"}

    # Delete Server
    assert delete_server(temp_db_path, server_id) is True
    assert get_server(temp_db_path, server_id) is None


def test_database_persists_catalog_metadata(temp_db_path):
    server = McpServer(
        server_id="metadata-server",
        name="Metadata Server",
        type="stdio",
        command=["uvx", "metadata-server"],
        is_active=False,
        status="inactive",
        created_at=1,
        updated_at=1,
        verification_state="verified_mcp",
        installability_tier="tested",
        risk_level="medium",
        deployment_mode="local-only",
        platform_support={
            "linux_x64": {
                "status": "yes",
                "tested": True,
                "notes": "validated in unit test",
            }
        },
        host_software_required=["OpenSCAD"],
        credentials_required=["TOKEN"],
        default_enabled=False,
        approval_gates=["workspace_write_approval"],
        validation_result={
            "status": "passed",
            "message": "Validated",
            "missing_dependencies": [],
        },
        follow_up_url="docs/mcp-catalog/followups/metadata-server.md",
    )
    insert_server(temp_db_path, server)

    fetched = get_server(temp_db_path, "metadata-server")
    assert fetched.verification_state == "verified_mcp"
    assert fetched.installability_tier == "tested"
    assert fetched.platform_support["linux_x64"].status == "yes"
    assert fetched.host_software_required == ["OpenSCAD"]
    assert fetched.credentials_required == ["TOKEN"]
    assert fetched.default_enabled is False
    assert fetched.validation_result.status == "passed"


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
    assert 'Called test_tool with: {"val": "hello"}' in res["content"][0]["text"]

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
        updated_at=int(time.time()),
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
        "required": ["val"],
    }

    # Call tool through Engine
    res = await engine.call_tool(server_id, "test_tool", {"val": "engine_test"})
    assert "content" in res
    assert 'Called test_tool with: {"val": "engine_test"}' in res["content"][0]["text"]

    # Stop Server
    stopped_server = await engine.stop_server(server_id)
    assert stopped_server.is_active is False
    assert stopped_server.status == "inactive"

    # Verify tools cleared from DB
    tools_after = get_tools(temp_db_path, server_id)
    assert len(tools_after) == 0

    await engine.shutdown()


@pytest.mark.asyncio
async def test_mcp_engine_blocks_start_when_credentials_missing(
    temp_db_path, tmp_path, monkeypatch
):
    monkeypatch.setenv("WRIGHT_SECRETS_PATH", str(tmp_path / "secrets.json"))
    server = McpServer(
        server_id="credentialed-engine",
        name="Credentialed Engine",
        type="stdio",
        command=[sys.executable, "-c", "print('unused')"],
        is_active=False,
        status="inactive",
        created_at=int(time.time()),
        updated_at=int(time.time()),
        env_vars=[
            EnvVarDefinition(
                name="API_TOKEN",
                label="API token",
                required=True,
                secret=True,
            )
        ],
    )
    insert_server(temp_db_path, server)
    engine = McpEngine(temp_db_path)

    with pytest.raises(RuntimeError, match="missing required credentials"):
        await engine.start_server("credentialed-engine")
