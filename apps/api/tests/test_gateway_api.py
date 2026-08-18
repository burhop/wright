from __future__ import annotations

import uuid
import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.config import DATABASE_PATH
from api.main import app
from data_vault.secret_provider import FileSecretProvider
from data_vault import GatewayRepository
from data_vault.workspace_repository import WorkspaceRepository
from tool_registry import McpServer, McpTool
from tool_registry.db import insert_server, insert_tools
from tool_registry.gateway_models import GatewayError, GatewayErrorCode


@pytest.fixture
def legacy_client(monkeypatch):
    monkeypatch.setenv("WRIGHT_LEGACY_GATEWAY", "1")
    with TestClient(app, base_url="http://localhost") as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup_gateway_test_rows():
    yield
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "DELETE FROM gateway_audit_events WHERE workspace_id LIKE 'workspace-%'"
        )
        connection.execute("DELETE FROM mcp_tools WHERE server_id LIKE 'calc-%'")
        connection.execute("DELETE FROM mcp_servers WHERE server_id LIKE 'calc-%'")
        connection.execute(
            "DELETE FROM workspace_agent_sessions WHERE workspace_id LIKE 'workspace-%'"
        )
        connection.execute(
            "DELETE FROM engineering_workspaces WHERE workspace_id LIKE 'workspace-%'"
        )


def _seed(tmp_path):
    suffix = uuid.uuid4().hex
    server_id = f"calc-{suffix}"
    workspace_id = f"workspace-{suffix}"
    session_id = f"session-{suffix}"
    workspace = tmp_path / workspace_id
    workspace.mkdir()
    insert_server(
        DATABASE_PATH,
        McpServer(
            server_id=server_id,
            name=f"Calculation {suffix}",
            type="stdio",
            command=["uv", "run", "calc"],
            is_active=False,
            is_installed=True,
            status="inactive",
            risk_level="high",
            approval_gates=["workspace_write_approval"],
            created_at=1000,
            updated_at=1000,
        ),
    )
    insert_tools(
        DATABASE_PATH,
        [
            McpTool(
                tool_id=f"{server_id}:mesh_calc",
                server_id=server_id,
                name="mesh_calc",
                description="Calculate mesh",
                input_schema={"type": "object"},
                is_enabled=True,
                created_at=1000,
            )
        ],
    )
    WorkspaceRepository(
        DATABASE_PATH, secrets=FileSecretProvider(tmp_path / "secrets.json")
    ).create(
        workspace_id,
        session_id,
        str(workspace),
        workspace_name="Gateway",
    )
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            "UPDATE engineering_workspaces SET enabled_tools = ? WHERE workspace_id = ?",
            (f'["{server_id}"]', workspace_id),
        )
    return server_id, session_id, workspace_id, str(workspace)


def _headers(session_id, workspace_id):
    return {
        "X-Wright-Session-Id": session_id,
        "X-Wright-Workspace-Id": workspace_id,
    }


def test_legacy_gateway_is_disabled_by_default(sync_client) -> None:
    response = sync_client.get("/api/gateway/tools")
    assert response.status_code == 404


def test_legacy_gateway_requires_and_uses_explicit_binding(
    legacy_client, tmp_path
) -> None:
    server_id, session_id, workspace_id, _ = _seed(tmp_path)
    assert legacy_client.get("/api/gateway/tools").status_code == 400

    response = legacy_client.get(
        "/api/gateway/tools", headers=_headers(session_id, workspace_id)
    )
    assert response.status_code == 200
    names = [item["name"] for item in response.json()["tools"]]
    assert f"{server_id}__mesh_calc" in names

    foreign = legacy_client.get(
        "/api/gateway/tools", headers=_headers(session_id, "foreign")
    )
    assert foreign.status_code in {400, 409}


def test_legacy_call_delegates_to_gateway_service(
    legacy_client, tmp_path, monkeypatch
) -> None:
    server_id, session_id, workspace_id, workspace_path = _seed(tmp_path)
    captured = {}

    async def start(server, workspace_dir=None, *, approval_context=None):
        captured["start"] = (server, workspace_dir, approval_context)

    async def call(server, tool, arguments, *, approval_context=None):
        captured["call"] = (server, tool, arguments, approval_context)
        return {"ok": True}

    monkeypatch.setattr(app.state.mcp_engine, "start_server", start)
    monkeypatch.setattr(app.state.mcp_engine, "call_tool", call)
    response = legacy_client.post(
        "/api/gateway/call",
        headers=_headers(session_id, workspace_id),
        json={"name": f"{server_id}__mesh_calc", "arguments": {}},
    )
    assert response.status_code == 200
    assert response.json()["structuredContent"] == {"ok": True}
    assert captured["start"][1] == workspace_path
    assert captured["call"][3].workspace_id == workspace_id
    assert captured["call"][3].workspace_approvals == {"workspace_write_approval"}


def test_legacy_call_does_not_expose_gateway_exception_details(
    legacy_client, tmp_path, monkeypatch
) -> None:
    server_id, session_id, workspace_id, _ = _seed(tmp_path)
    sensitive_detail = r"Traceback: secret-token at D:\private\server.py:42"

    async def fail_call(*args, **kwargs):
        raise GatewayError(GatewayErrorCode.INTERNAL, sensitive_detail)

    monkeypatch.setattr(app.state.gateway_service, "call_tool", fail_call)
    response = legacy_client.post(
        "/api/gateway/call",
        headers=_headers(session_id, workspace_id),
        json={"name": f"{server_id}__mesh_calc", "arguments": {}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["isError"] is True
    assert body["structuredContent"] == {"error": "internal"}
    assert body["content"][0]["text"] == "Gateway request failed (internal)."
    assert sensitive_detail not in response.text


def test_mcp_router_uses_generic_wright_gateway_sync():
    from api.services import mcp_services

    assert (
        mcp_services.sync_mcp_server_to_wright_gateway.__module__
        == "api.services.wright_gateway_sync"
    )


def test_rivet_management_writes_use_only_the_scoped_rivet_grant() -> None:
    from api.composition import _rivet_gateway_tools
    from tool_registry.wright_managed_servers import RIVET_WORKFLOW_MUTATION_APPROVAL

    specs = {spec.name: spec for spec, _handler in _rivet_gateway_tools()}
    mutation_names = {
        "wright__rivet_add_node",
        "wright__rivet_edit_node",
        "wright__rivet_delete_node",
        "wright__rivet_connect_ports",
        "wright__rivet_disconnect_ports",
        "wright__rivet_save_revision",
        "wright__rivet_run_workflow",
    }
    for name in mutation_names:
        assert specs[name].required_approvals == frozenset(
            {RIVET_WORKFLOW_MUTATION_APPROVAL}
        )
    assert specs["wright__rivet_inspect_graph"].required_approvals == frozenset()
    assert specs["wright__rivet_lint"].required_approvals == frozenset()


def test_gateway_diagnostics_summarize_persisted_timings(sync_client, tmp_path) -> None:
    server_id, session_id, workspace_id, _ = _seed(tmp_path)
    GatewayRepository(DATABASE_PATH).record_audit(
        {
            "correlation_id": "diagnostic-correlation",
            "request_id": "diagnostic-request",
            "session_id": session_id,
            "principal_id": "local-admin",
            "workspace_id": workspace_id,
            "operation": "tool.call",
            "server_id": server_id,
            "target_name": "mesh_calc",
            "allowed": True,
            "reason_code": "allowed",
            "outcome": "succeeded",
            "duration_ms": 1250,
            "metadata": {"response_bytes": 4096},
        }
    )

    response = sync_client.get(
        "/api/gateway/diagnostics", params={"session_id": session_id}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["completed_calls"] == 1
    assert body["summary"]["maximum_duration_ms"] == 1250
    assert body["slowest"][0]["metadata"]["response_bytes"] == 4096
