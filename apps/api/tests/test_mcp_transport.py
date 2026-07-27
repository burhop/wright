from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from api.config import DATABASE_PATH
from api.main import app
from data_vault.secret_provider import FileSecretProvider
from data_vault.workspace_repository import WorkspaceRepository


def _binding(tmp_path):
    suffix = uuid.uuid4().hex
    workspace_id = f"workspace-{suffix}"
    session_id = f"session-{suffix}"
    workspace = tmp_path / workspace_id
    workspace.mkdir()
    WorkspaceRepository(
        DATABASE_PATH, secrets=FileSecretProvider(tmp_path / "secrets.json")
    ).create(workspace_id, session_id, str(workspace), workspace_name="MCP")
    return session_id, workspace_id


def test_streamable_http_requires_explicit_binding_and_initializes(tmp_path) -> None:
    session_id, workspace_id = _binding(tmp_path)
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "contract-test", "version": "1"},
        },
    }
    with TestClient(app, base_url="http://localhost") as client:
        missing = client.post("/mcp", json=initialize)
        assert missing.status_code == 400

        response = client.post(
            "/mcp",
            json=initialize,
            headers={
                "X-Wright-Session-Id": session_id,
                "X-Wright-Workspace-Id": workspace_id,
                "Accept": "application/json, text/event-stream",
            },
        )
        assert response.status_code == 200
        assert response.headers["mcp-session-id"]
        assert '"protocolVersion":"2025-11-25"' in response.text
        second = client.post(
            "/mcp",
            json=initialize,
            headers={
                "X-Wright-Session-Id": session_id,
                "X-Wright-Workspace-Id": workspace_id,
                "Accept": "application/json, text/event-stream",
            },
        )
        assert second.status_code == 200
        assert second.headers["mcp-session-id"] != response.headers["mcp-session-id"]


def test_streamable_http_rejects_foreign_workspace_and_large_body(tmp_path) -> None:
    session_id, workspace_id = _binding(tmp_path)
    with TestClient(app, base_url="http://localhost") as client:
        foreign = client.post(
            "/mcp",
            content="{}",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "X-Wright-Session-Id": session_id,
                "X-Wright-Workspace-Id": f"foreign-{workspace_id}",
            },
        )
        assert foreign.status_code == 400

        oversized = client.post(
            "/mcp",
            content=b"x" * 1_048_577,
            headers={
                "Content-Type": "application/json",
                "X-Wright-Session-Id": session_id,
                "X-Wright-Workspace-Id": workspace_id,
            },
        )
        assert oversized.status_code == 413


def test_streamable_http_session_id_cannot_cross_workspace_bindings(tmp_path) -> None:
    first_session, first_workspace = _binding(tmp_path)
    second_session, second_workspace = _binding(tmp_path)
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "isolation", "version": "1"},
        },
    }
    accept = {"Accept": "application/json, text/event-stream"}
    with TestClient(app, base_url="http://localhost") as client:
        first = client.post(
            "/mcp",
            json=initialize,
            headers={
                **accept,
                **{
                    "X-Wright-Session-Id": first_session,
                    "X-Wright-Workspace-Id": first_workspace,
                },
            },
        )
        second = client.post(
            "/mcp",
            json=initialize,
            headers={
                **accept,
                **{
                    "X-Wright-Session-Id": second_session,
                    "X-Wright-Workspace-Id": second_workspace,
                },
            },
        )
        assert first.status_code == second.status_code == 200
        crossed = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            headers={
                **accept,
                "X-Wright-Session-Id": second_session,
                "X-Wright-Workspace-Id": second_workspace,
                "Mcp-Session-Id": first.headers["mcp-session-id"],
                "Mcp-Protocol-Version": "2025-11-25",
            },
        )
        assert crossed.status_code == 404


def test_streamable_http_is_covered_by_control_plane_authentication(
    tmp_path, monkeypatch
) -> None:
    session_id, workspace_id = _binding(tmp_path)
    previous = app.state.security_settings
    monkeypatch.setenv("WRIGHT_AUTH_MODE", "enforced")
    monkeypatch.setenv("WRIGHT_API_TOKEN", "mcp-test-token")
    try:
        with TestClient(app, base_url="http://localhost") as client:
            headers = {
                "X-Wright-Session-Id": session_id,
                "X-Wright-Workspace-Id": workspace_id,
            }
            assert client.post("/mcp", json={}, headers=headers).status_code == 401
            denied = client.post(
                "/mcp",
                json={},
                headers={
                    **headers,
                    "Authorization": "Bearer mcp-test-token",
                    "Origin": "https://evil.example",
                },
            )
            assert denied.status_code == 403
    finally:
        app.state.security_settings = previous
