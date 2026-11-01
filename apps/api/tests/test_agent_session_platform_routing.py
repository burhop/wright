from types import SimpleNamespace

import pytest

from agent_adapters.base import AgentChatMessage
from workspace_service.adapters.runtime import (
    associate_workspace_session,
    create_workspace,
)


@pytest.fixture
def mixed_sessions(client, mock_agent_engine, monkeypatch, tmp_path):
    from api.main import app
    from api.config import DATABASE_PATH
    from api.routers import agent

    old, new = "mixed-hermes-session", "mixed-codex-session"
    create_workspace(
        DATABASE_PATH,
        "mixed-workspace",
        old,
        str(tmp_path),
        workspace_name="Mixed sessions",
        agent_id="hermes",
    )
    associate_workspace_session(DATABASE_PATH, "mixed-workspace", new, agent_id="codex")
    calls = []

    async def history(session):
        calls.append(("hermes-history", session))
        return [AgentChatMessage("hermes-message", "assistant", "Hermes history", 1)]

    async def cancel(session):
        calls.append(("hermes-cancel", session))
        return True

    async def codex_history(session):
        calls.append(("codex-history", session))
        return [AgentChatMessage("codex-message", "assistant", "Codex history", 1)]

    async def models():
        return [{"model": "fixture", "displayName": "Fixture"}]

    mock_agent_engine.get_chat_history, mock_agent_engine.cancel_chat = history, cancel
    codex = SimpleNamespace(
        platform="codex",
        model="fixture",
        get_chat_history=codex_history,
        get_models=models,
    )
    monkeypatch.setattr(
        app.state,
        "agent_engines",
        {"hermes": mock_agent_engine, "codex": codex},
        raising=False,
    )
    app.state.agent_sync_manager.active_agent = "codex"
    monkeypatch.setattr(app.state, "agent_engine", codex)
    monkeypatch.setattr(
        agent,
        "_hermes_json_request",
        lambda *a, **kw: (_ for _ in ()).throw(
            AssertionError("No model call may fall back to Hermes")
        ),
    )
    yield SimpleNamespace(app=app, old=old, new=new, calls=calls)
    app.state.agent_sync_manager.active_agent = "hermes"


@pytest.mark.asyncio
async def test_path_and_query_operations_use_saved_platform_after_default_switch(
    client, mixed_sessions
):
    item = mixed_sessions
    response = await client.get(f"/api/agent/sessions/{item.old}/history")
    assert response.json()["messages"][0]["content"] == "Hermes history"
    assert (await client.post(f"/api/agent/chat/cancel?session_id={item.old}")).json()[
        "success"
    ]
    assert item.calls == [("hermes-history", item.old), ("hermes-cancel", item.old)]


@pytest.mark.asyncio
async def test_body_routing_preserves_codex_model_lock_when_default_is_hermes(
    client, mixed_sessions
):
    item = mixed_sessions
    item.app.state.agent_sync_manager.active_agent = "hermes"
    item.app.state.agent_engine = item.app.state.agent_engines["hermes"]
    response = await client.post(
        "/api/agent/model",
        json={"session_id": item.new, "provider": "other", "model": "other"},
    )
    assert response.status_code == 409
    assert "frozen" in response.json()["message"]
    response = await client.get(f"/api/agent/models?session_id={item.new}")
    assert response.json()["current_provider"] == "codex"
    assert not response.json()["selection_supported"]


@pytest.mark.asyncio
async def test_default_switch_reuses_engine_and_preserves_old_session_routes(
    client, mixed_sessions
):
    item = mixed_sessions
    original = item.app.state.agent_engines["codex"]
    assert (
        await client.post("/api/agent/active", json={"agent": "hermes"})
    ).status_code == 200
    response = await client.get(f"/api/agent/sessions/{item.new}/history")
    assert response.json()["messages"][0]["content"] == "Codex history"
    assert (
        await client.post("/api/agent/active", json={"agent": "codex"})
    ).status_code == 200
    assert item.app.state.agent_engine is original


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,body",
    [
        (
            "/api/workspace/workflows/example/runs",
            {"expected_revision": 1, "expected_digest": "a" * 64},
        ),
        (
            "/api/workspace/engineering-scenarios/example/runs",
            {
                "manifest_digest": "a" * 64,
                "workflow_revision": 1,
                "workflow_digest": "b" * 64,
                "binding_set_digest": "c" * 64,
            },
        ),
        (
            "/api/workspace/workflow-sources/run",
            {
                "path": "workflows/example.workflow.wflow",
                "expected_storage_digest": "a" * 64,
            },
        ),
    ],
)
async def test_codex_chat_session_cannot_start_a_workflow(
    client, mixed_sessions, path, body
):
    body = {"session_id": mixed_sessions.new, **body}
    response = await client.post(path, json=body)
    assert response.status_code == 409, response.text
    assert "Codex workflow execution is unavailable" in response.json()["message"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path,body",
    [
        (
            "/api/workspace/process-interfaces/runs",
            {
                "path": "workflows/example.workflow.wflow",
                "expected_storage_digest": "a" * 64,
                "expected_input_digest": "b" * 64,
                "input_snapshot_id": "inputs",
                "request_id": "codex-gated-start",
            },
        ),
        (
            "/api/native-processes/documents/example/runs",
            {"expected_token": "a" * 64, "request_id": "codex_gated_start"},
        ),
        (
            "/api/native-processes/example/runs",
            {"expected_token": "a" * 64, "request_id": "codex_gated_alias"},
        ),
    ],
)
async def test_codex_cannot_bypass_workflow_gate_through_native_start(
    client, mixed_sessions, path, body
):
    if "process-interfaces" in path:
        body = {"session_id": mixed_sessions.new, **body}
    response = await client.post(
        path, params={"session_id": mixed_sessions.new}, json=body
    )
    assert response.status_code == 409, response.text
    assert "Codex workflow execution is unavailable" in response.json()["message"]


@pytest.mark.asyncio
async def test_first_authoring_owner_uses_saved_hermes_session_under_codex_default(
    mixed_sessions, monkeypatch
):
    from starlette.requests import Request
    from api.routers import process_ui_authoring

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/workspace/process-interfaces/authoring-capabilities",
            "query_string": f"session_id={mixed_sessions.old}".encode(),
            "headers": [],
            "app": mixed_sessions.app,
        }
    )
    from agent_adapters.base import AgentInvocationCapabilities

    async def capabilities():
        return AgentInvocationCapabilities(
            adapter="hermes", available=False, reason="Fixture: no model is invoked"
        )

    monkeypatch.setattr(
        mixed_sessions.app.state.agent_engines["hermes"],
        "get_invocation_capabilities",
        capabilities,
        raising=False,
    )
    captured = []

    def configure(engine, toolchain):
        captured.append(engine)
        return SimpleNamespace(engine=engine)

    application = SimpleNamespace(configure_authoring=configure)
    service = SimpleNamespace(process_interfaces=application)
    monkeypatch.setattr(
        process_ui_authoring, "discover_build_toolchain", lambda: object()
    )
    owner = await process_ui_authoring.get_process_ui_authoring(request, service)
    assert owner.engine is mixed_sessions.app.state.agent_engines["hermes"]
    assert captured == [owner.engine]
