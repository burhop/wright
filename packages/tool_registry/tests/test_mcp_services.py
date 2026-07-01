import sqlite3

import pytest

from tool_registry import EnvVarDefinition, McpServer, McpServerCreate, McpTool
from tool_registry.db import (
    get_server,
    insert_server,
    insert_tools,
    update_server as db_update_server,
)
from tool_registry import services


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "mcp-services.db"
    conn = sqlite3.connect(path)
    try:
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
        )
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
        )
        """)
        conn.commit()
    finally:
        conn.close()
    return str(path)


class FakeEngine:
    def __init__(self, db_path):
        self.db_path = db_path
        self.started: list[str] = []
        self.stopped: list[str] = []

    async def start_server(self, server_id: str):
        self.started.append(server_id)
        return db_update_server(
            self.db_path,
            server_id,
            {"is_active": True, "status": "active", "updated_at": 2000},
        )

    async def stop_server(self, server_id: str):
        self.stopped.append(server_id)
        return db_update_server(
            self.db_path,
            server_id,
            {"is_active": False, "status": "inactive", "updated_at": 3000},
        )


def _insert_server(db_path, **overrides):
    data = {
        "server_id": "calc-id-123",
        "name": "Calcul mesh",
        "type": "stdio",
        "command": ["uv", "run", "calc"],
        "is_active": False,
        "is_installed": False,
        "status": "inactive",
        "created_at": 1000,
        "updated_at": 1000,
    }
    data.update(overrides)
    server = McpServer(**data)
    insert_server(db_path, server)
    return server


def test_list_register_and_tool_services(db_path, tmp_path, monkeypatch):
    monkeypatch.setenv("WRIGHT_SECRETS_PATH", str(tmp_path / "secrets.json"))
    _insert_server(
        db_path,
        env_vars=[
            EnvVarDefinition(
                name="API_KEY", label="API key", required=True, secret=True
            )
        ],
    )
    services.save_server_credentials(db_path, "calc-id-123", {"API_KEY": "secret"})
    insert_tools(
        db_path,
        [
            McpTool(
                tool_id="calc-id-123:mesh_calc",
                server_id="calc-id-123",
                name="mesh_calc",
                description="Calculate mesh",
                input_schema={"type": "object"},
                is_enabled=True,
                created_at=1000,
            )
        ],
    )

    servers = services.list_registered_servers(db_path)
    assert servers[0].credentials_configured == {"API_KEY": True}

    created = services.register_server(
        db_path,
        McpServerCreate(name="Remote docs", type="sse", command="http://127/sse"),
        server_id="remote-docs",
        now=1234,
    )
    assert created.server_id == "remote-docs"
    assert get_server(db_path, "remote-docs").name == "Remote docs"

    tool = services.set_tool_enabled(db_path, "calc-id-123:mesh_calc", False)
    assert tool.is_enabled is False
    assert services.list_registered_tools(db_path)[0].is_enabled is False


@pytest.mark.asyncio
async def test_activation_install_and_uninstall_services(db_path):
    _insert_server(db_path)
    engine = FakeEngine(db_path)

    activated = await services.toggle_server_activation(engine, "calc-id-123", True)
    assert activated.is_active is True

    installed = await services.install_server(
        engine,
        "calc-id-123",
        session_id="session-1",
        is_server_enabled_for_session=lambda server: False,
    )

    assert installed.server.is_installed is True
    assert installed.server.is_active is False
    assert engine.started == ["calc-id-123", "calc-id-123"]
    assert engine.stopped == ["calc-id-123"]

    uninstalled = await services.uninstall_server(
        engine, "calc-id-123", session_id="session-1"
    )
    assert uninstalled.server.is_installed is False
    assert uninstalled.sync_session_id == "session-1"


@pytest.mark.asyncio
async def test_service_errors_are_domain_specific(db_path):
    _insert_server(db_path)

    with pytest.raises(services.McpConflictError, match="Calcul mesh"):
        services.register_server(
            db_path,
            McpServerCreate(
                name="Calcul mesh",
                type="stdio",
                command=["uv", "run", "other"],
            ),
        )

    with pytest.raises(services.McpNotFoundError, match="missing-tool"):
        services.set_tool_enabled(db_path, "missing-tool", False)

    _insert_server(
        db_path,
        server_id="blocked-id",
        name="Blocked CAD",
        installability_tier="blocked",
        install_blocked_reason="No usable source URL.",
    )

    with pytest.raises(services.McpInvalidOperationError, match="No usable source URL"):
        await services.install_server(FakeEngine(db_path), "blocked-id")


def test_credential_services(db_path, tmp_path, monkeypatch):
    monkeypatch.setenv("WRIGHT_SECRETS_PATH", str(tmp_path / "secrets.json"))
    _insert_server(
        db_path,
        env_vars=[
            EnvVarDefinition(name="ACCESS_KEY", label="Access key", secret=True),
            EnvVarDefinition(name="SECRET_KEY", label="Secret key", secret=True),
        ],
    )

    status = services.save_server_credentials(
        db_path,
        "calc-id-123",
        {"ACCESS_KEY": "access", "SECRET_KEY": "secret"},
    )

    assert status["configured"] == {"ACCESS_KEY": True, "SECRET_KEY": True}

    services.delete_server_credentials(db_path, "calc-id-123")
    status = services.get_credential_status(db_path, "calc-id-123")
    assert status["configured"] == {"ACCESS_KEY": False, "SECRET_KEY": False}


def test_validation_and_report_missing_services(db_path, tmp_path):
    _insert_server(db_path)
    db_update_server(
        db_path,
        "calc-id-123",
        {"host_software_required": ["DefinitelyMissingCadHost"]},
    )

    result = services.validate_registered_server(
        db_path, "calc-id-123", followup_dir=tmp_path / "followups"
    )
    assert result.status == "dependency_missing"
    assert result.missing_dependencies == ["DefinitelyMissingCadHost"]

    reported = services.report_missing_server(
        db_path,
        name="New Candidate MCP",
        source_url="https://example.com/new-candidate",
        notes="Needs verification",
        now=1234,
    )
    assert reported.server_id == "reported-new-candidate-mcp"
    assert reported.installability_tier == "blocked"


@pytest.mark.asyncio
async def test_version_check_and_update_services(db_path):
    _insert_server(db_path, is_installed=True, installed_version="1.2.3")

    version = await services.check_registered_server_version(db_path, "calc-id-123")
    assert version["latest"] == "1.4.0"
    assert version["update_available"] is True

    updated = await services.update_registered_server_version(db_path, "calc-id-123")
    assert updated == {
        "server_id": "calc-id-123",
        "installed_version": "1.4.0",
        "success": True,
        "error": None,
    }
    assert get_server(db_path, "calc-id-123").installed_version == "1.4.0"
