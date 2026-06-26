"""
Tests for MCP credential store and credential management API endpoints.

Covers:
  T006: secrets module unit tests (write, read, delete, has_credentials, file permissions)
  T007: credential API endpoint tests (GET, PUT, DELETE /credentials)
  T013: security validation tests (secrets never in API responses)
  T016: OnShape MCP catalog entry verification
"""

import json
import os
import stat
import sqlite3
import tempfile

import pytest
from fastapi.testclient import TestClient
from api.main import app
from tool_registry import McpEngine


# ── T006: Credential Store Module Tests ──────────────────────────────────────


class TestSecretsModule:
    """Unit tests for tool_registry.secrets module."""

    @pytest.fixture(autouse=True)
    def setup_temp_secrets(self, tmp_path, monkeypatch):
        """Use a temp directory for secrets to avoid touching real user config."""
        self.secrets_path = str(tmp_path / "test-mcp-secrets.json")
        monkeypatch.setenv("WRIGHT_SECRETS_PATH", self.secrets_path)

    def test_write_and_read_secrets(self):
        from tool_registry.secrets import write_secrets, read_secrets

        write_secrets("test-server", {"API_KEY": "test-key-123", "API_SECRET": "test-secret-456"})
        result = read_secrets("test-server")
        assert result == {"API_KEY": "test-key-123", "API_SECRET": "test-secret-456"}

    def test_read_nonexistent_server(self):
        from tool_registry.secrets import read_secrets

        result = read_secrets("nonexistent-server")
        assert result == {}

    def test_read_missing_file(self):
        from tool_registry.secrets import read_secrets

        result = read_secrets("any-server")
        assert result == {}

    def test_delete_secrets(self):
        from tool_registry.secrets import write_secrets, read_secrets, delete_secrets

        write_secrets("test-server", {"API_KEY": "value"})
        assert read_secrets("test-server") == {"API_KEY": "value"}

        delete_secrets("test-server")
        assert read_secrets("test-server") == {}

    def test_delete_nonexistent_server(self):
        from tool_registry.secrets import delete_secrets

        # Should not raise
        delete_secrets("nonexistent-server")

    def test_has_credentials_all_present(self):
        from tool_registry.secrets import write_secrets, has_credentials

        write_secrets("test-server", {"KEY_A": "val_a", "KEY_B": "val_b"})
        result = has_credentials("test-server", ["KEY_A", "KEY_B"])
        assert result == {"KEY_A": True, "KEY_B": True}

    def test_has_credentials_partial(self):
        from tool_registry.secrets import write_secrets, has_credentials

        write_secrets("test-server", {"KEY_A": "val_a"})
        result = has_credentials("test-server", ["KEY_A", "KEY_B"])
        assert result == {"KEY_A": True, "KEY_B": False}

    def test_has_credentials_none_present(self):
        from tool_registry.secrets import has_credentials

        result = has_credentials("test-server", ["KEY_A", "KEY_B"])
        assert result == {"KEY_A": False, "KEY_B": False}

    def test_has_credentials_no_required_vars(self):
        from tool_registry.secrets import has_credentials

        result = has_credentials("test-server", None)
        assert result == {}

    def test_file_permissions_0600(self):
        from tool_registry.secrets import write_secrets

        write_secrets("test-server", {"KEY": "value"})
        if os.name == "nt":
            assert os.path.exists(self.secrets_path)
            assert os.access(self.secrets_path, os.R_OK | os.W_OK)
            return

        mode = oct(stat.S_IMODE(os.stat(self.secrets_path).st_mode))
        assert mode == "0o600", f"Expected 0o600, got {mode}"

    def test_overwrite_existing_server(self):
        from tool_registry.secrets import write_secrets, read_secrets

        write_secrets("test-server", {"KEY": "old_value"})
        write_secrets("test-server", {"KEY": "new_value"})
        result = read_secrets("test-server")
        assert result == {"KEY": "new_value"}

    def test_multiple_servers_isolated(self):
        from tool_registry.secrets import write_secrets, read_secrets

        write_secrets("server-a", {"KEY_A": "val_a"})
        write_secrets("server-b", {"KEY_B": "val_b"})
        assert read_secrets("server-a") == {"KEY_A": "val_a"}
        assert read_secrets("server-b") == {"KEY_B": "val_b"}

    def test_empty_credential_value_treated_as_not_configured(self):
        from tool_registry.secrets import write_secrets, has_credentials

        write_secrets("test-server", {"KEY": ""})
        result = has_credentials("test-server", ["KEY"])
        assert result == {"KEY": False}  # empty string = not configured


# ── Shared fixture for API tests with McpEngine ──────────────────────────────


@pytest.fixture
def cred_test_db_path():
    """Create a temporary database with schema and seed the OnShape MCP entry."""
    fd, path = tempfile.mkstemp(suffix="-cred-test.db")
    os.close(fd)

    conn = sqlite3.connect(path)
    conn.execute("""
    CREATE TABLE mcp_servers (
        server_id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL CHECK(type IN ('stdio', 'sse', 'webmcp')),
        command TEXT,
        is_active INTEGER NOT NULL DEFAULT 0,
        is_installed INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'inactive',
        error_message TEXT,
        category TEXT NOT NULL DEFAULT 'utilities',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        image_url TEXT,
        description TEXT,
        source_url TEXT,
        installed_version TEXT,
        env_vars TEXT,
        instructions TEXT
    );
    """)
    conn.execute("""
    CREATE TABLE mcp_tools (
        tool_id TEXT PRIMARY KEY,
        server_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        input_schema TEXT NOT NULL,
        is_enabled INTEGER NOT NULL DEFAULT 1,
        created_at INTEGER NOT NULL,
        FOREIGN KEY (server_id) REFERENCES mcp_servers(server_id) ON DELETE CASCADE
    );
    """)
    # Seed the OnShape MCP entry with env_var definitions
    env_vars = json.dumps([
        {"name": "ONSHAPE_ACCESS_KEY", "label": "Access Key", "description": "Onshape API access key from dev-portal.onshape.com", "required": True, "secret": False},
        {"name": "ONSHAPE_SECRET_KEY", "label": "Secret Key", "description": "Onshape API secret key (shown once at creation)", "required": True, "secret": True},
    ])
    conn.execute("""
    INSERT INTO mcp_servers (server_id, name, type, command, is_active, is_installed,
        status, category, created_at, updated_at, image_url, description, source_url, env_vars)
    VALUES (?, ?, ?, ?, 0, 0, 'inactive', ?, 1000, 1000, ?, ?, ?, ?)
    """, (
        "jarvis-onshape-mcp",
        "Jarvis OnShape MCP",
        "stdio",
        json.dumps(["uv", "run", "--with", "jarvis-onshape-mcp", "onshape-mcp"]),
        "cad",
        "https://avatars.githubusercontent.com/u/6536550?s=64",
        "AI copilot for Onshape CAD.",
        "https://github.com/ReshefElisha/jarvis-onshape-mcp",
        env_vars,
    ))
    conn.commit()
    conn.close()

    yield path

    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def cred_client(cred_test_db_path, tmp_path, monkeypatch):
    """TestClient with McpEngine set up and temp secrets path."""
    secrets_path = str(tmp_path / "api-test-secrets.json")
    monkeypatch.setenv("WRIGHT_SECRETS_PATH", secrets_path)

    with TestClient(app) as c:
        engine = McpEngine(cred_test_db_path)
        c.app.state.mcp_engine = engine
        yield c


# ── T007: Credential API Endpoint Tests ──────────────────────────────────────


class TestCredentialAPIEndpoints:
    """Tests for credential management REST API endpoints."""

    def test_get_credential_status_for_server_with_env_vars(self, cred_client):
        """GET /credentials returns env var definitions and configured status."""
        response = cred_client.get("/api/mcp/servers/jarvis-onshape-mcp/credentials")
        assert response.status_code == 200
        data = response.json()
        assert data["server_id"] == "jarvis-onshape-mcp"
        assert len(data["env_vars"]) == 2
        names = [v["name"] for v in data["env_vars"]]
        assert "ONSHAPE_ACCESS_KEY" in names
        assert "ONSHAPE_SECRET_KEY" in names
        assert data["configured"]["ONSHAPE_ACCESS_KEY"] is False
        assert data["configured"]["ONSHAPE_SECRET_KEY"] is False

    def test_save_and_get_credentials(self, cred_client):
        """PUT /credentials saves values; GET shows them as configured."""
        save_response = cred_client.put(
            "/api/mcp/servers/jarvis-onshape-mcp/credentials",
            json={"credentials": {
                "ONSHAPE_ACCESS_KEY": "test-access-key",
                "ONSHAPE_SECRET_KEY": "test-secret-key",
            }},
        )
        assert save_response.status_code == 200
        save_data = save_response.json()
        assert save_data["configured"]["ONSHAPE_ACCESS_KEY"] is True
        assert save_data["configured"]["ONSHAPE_SECRET_KEY"] is True

        get_response = cred_client.get("/api/mcp/servers/jarvis-onshape-mcp/credentials")
        get_data = get_response.json()
        assert get_data["configured"]["ONSHAPE_ACCESS_KEY"] is True
        assert get_data["configured"]["ONSHAPE_SECRET_KEY"] is True

    def test_delete_credentials(self, cred_client):
        """DELETE /credentials removes saved values."""
        cred_client.put(
            "/api/mcp/servers/jarvis-onshape-mcp/credentials",
            json={"credentials": {"ONSHAPE_ACCESS_KEY": "key", "ONSHAPE_SECRET_KEY": "secret"}},
        )

        del_response = cred_client.delete("/api/mcp/servers/jarvis-onshape-mcp/credentials")
        assert del_response.status_code == 204

        get_response = cred_client.get("/api/mcp/servers/jarvis-onshape-mcp/credentials")
        get_data = get_response.json()
        assert get_data["configured"]["ONSHAPE_ACCESS_KEY"] is False
        assert get_data["configured"]["ONSHAPE_SECRET_KEY"] is False

    def test_get_credentials_for_nonexistent_server(self, cred_client):
        """GET /credentials for non-existent server returns 404."""
        response = cred_client.get("/api/mcp/servers/nonexistent-server-id/credentials")
        assert response.status_code == 404

    def test_save_credentials_for_nonexistent_server(self, cred_client):
        """PUT /credentials for non-existent server returns 404."""
        response = cred_client.put(
            "/api/mcp/servers/nonexistent-server-id/credentials",
            json={"credentials": {"KEY": "value"}},
        )
        assert response.status_code == 404


# ── T013: Security Validation Tests ──────────────────────────────────────────


class TestCredentialSecurity:
    """Verify secrets never leak into API responses."""

    def test_list_servers_never_returns_credential_values(self, cred_client):
        """GET /servers response must not contain actual credential values."""
        cred_client.put(
            "/api/mcp/servers/jarvis-onshape-mcp/credentials",
            json={"credentials": {
                "ONSHAPE_ACCESS_KEY": "SUPER_SECRET_KEY_12345",
                "ONSHAPE_SECRET_KEY": "ULTRA_SECRET_VALUE_67890",
            }},
        )

        response = cred_client.get("/api/mcp/servers")
        assert response.status_code == 200
        body = response.text
        assert "SUPER_SECRET_KEY_12345" not in body
        assert "ULTRA_SECRET_VALUE_67890" not in body

    def test_list_servers_includes_credentials_configured_flags(self, cred_client):
        """GET /servers includes credentials_configured booleans."""
        cred_client.put(
            "/api/mcp/servers/jarvis-onshape-mcp/credentials",
            json={"credentials": {
                "ONSHAPE_ACCESS_KEY": "key-value",
                "ONSHAPE_SECRET_KEY": "secret-value",
            }},
        )

        response = cred_client.get("/api/mcp/servers")
        data = response.json()
        onshape = next(
            (s for s in data["servers"] if s["server_id"] == "jarvis-onshape-mcp"),
            None,
        )
        assert onshape is not None
        assert onshape["credentials_configured"]["ONSHAPE_ACCESS_KEY"] is True
        assert onshape["credentials_configured"]["ONSHAPE_SECRET_KEY"] is True

        # Verify the response text doesn't contain the actual values
        assert "key-value" not in response.text
        assert "secret-value" not in response.text

    def test_install_blocked_without_credentials(self, cred_client):
        """POST /install returns 400 when required credentials are missing."""
        cred_client.delete("/api/mcp/servers/jarvis-onshape-mcp/credentials")

        response = cred_client.post("/api/mcp/servers/jarvis-onshape-mcp/install")
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", data.get("message", ""))
        assert "requires credentials" in detail.lower()


# ── T016: OnShape MCP Catalog Entry Tests ────────────────────────────────────


class TestOnShapeCatalogEntry:
    """Verify the Jarvis OnShape MCP is properly seeded in the catalog."""

    def test_onshape_mcp_exists_in_catalog(self, cred_client):
        """The OnShape MCP should exist in the servers list."""
        response = cred_client.get("/api/mcp/servers")
        assert response.status_code == 200
        data = response.json()
        onshape = next(
            (s for s in data["servers"] if s["server_id"] == "jarvis-onshape-mcp"),
            None,
        )
        assert onshape is not None, "Jarvis OnShape MCP not found in catalog"

    def test_onshape_mcp_correct_metadata(self, cred_client):
        """OnShape MCP has correct server_id, name, type, category."""
        response = cred_client.get("/api/mcp/servers")
        data = response.json()
        onshape = next(
            s for s in data["servers"] if s["server_id"] == "jarvis-onshape-mcp"
        )
        assert onshape["name"] == "Jarvis OnShape MCP"
        assert onshape["type"] == "stdio"
        assert onshape["category"] == "cad"

    def test_onshape_mcp_has_env_var_definitions(self, cred_client):
        """OnShape MCP has correct env_var definitions."""
        response = cred_client.get("/api/mcp/servers/jarvis-onshape-mcp/credentials")
        assert response.status_code == 200
        data = response.json()
        assert len(data["env_vars"]) == 2

        key_def = next(v for v in data["env_vars"] if v["name"] == "ONSHAPE_ACCESS_KEY")
        assert key_def["label"] == "Access Key"
        assert key_def["required"] is True
        assert key_def["secret"] is False

        secret_def = next(v for v in data["env_vars"] if v["name"] == "ONSHAPE_SECRET_KEY")
        assert secret_def["label"] == "Secret Key"
        assert secret_def["required"] is True
        assert secret_def["secret"] is True


class TestWorkspaceDefaultTools:
    """Verify that get_workspace_enabled_tools filters default tools correctly."""

    def test_default_tools_filtering(self, cred_test_db_path):
        """Default tools list should omit installed servers with missing credentials or error status."""
        from core.workspace import get_workspace_enabled_tools
        from tool_registry.db import insert_server
        from tool_registry.models import McpServer, EnvVarDefinition
        import json
        import uuid

        db_path = cred_test_db_path
        session_id = str(uuid.uuid4())

        # Seed mock servers:
        # 1. Stdio server, installed, no credentials -> should be enabled
        insert_server(db_path, McpServer(
            server_id="server-ok",
            name="Server OK",
            type="stdio",
            is_active=False,
            is_installed=True,
            status="inactive",
            created_at=0,
            updated_at=0,
        ))

        # 2. Stdio server, installed, requires credentials (missing) -> should be filtered out
        insert_server(db_path, McpServer(
            server_id="server-missing-creds",
            name="Server Missing Creds",
            type="stdio",
            is_active=False,
            is_installed=True,
            status="inactive",
            created_at=0,
            updated_at=0,
            env_vars=[
                EnvVarDefinition(name="API_SECRET", label="Secret", required=True, secret=True)
            ]
        ))

        # 3. SSE server, installed, has error status -> should be filtered out
        insert_server(db_path, McpServer(
            server_id="server-error",
            name="Server Error",
            type="sse",
            is_active=False,
            is_installed=True,
            status="error",
            error_message="Timeout",
            created_at=0,
            updated_at=0,
        ))

        # Create engineering_workspaces table and insert workspace row
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("""
        CREATE TABLE engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            local_path TEXT NOT NULL,
            git_remote_url TEXT,
            git_username TEXT,
            git_token TEXT,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            workspace_name TEXT
        );
        """)
        conn.execute(
            """
            INSERT INTO engineering_workspaces (
                workspace_id, session_id, local_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("ws-test", session_id, "/tmp/ws-test", 0, 0),
        )
        conn.commit()
        conn.close()

        # Get default enabled tools
        enabled = get_workspace_enabled_tools(db_path, session_id)
        assert "Server OK" in enabled
        assert "Server Missing Creds" not in enabled
        assert "Server Error" not in enabled

