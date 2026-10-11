import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import FastAPI
import httpx
import pytest

from core.desktop_reasoning import DesktopReasoningRequest


@pytest.fixture
def leased(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_backend import DesktopBackend

    root = tmp_path / "workspaces/private"
    root.mkdir(parents=True)
    service = SimpleNamespace(
        db_path=str(tmp_path / "wright.sqlite"),
        repository=SimpleNamespace(
            get_by_session=Mock(
                return_value={"workspace_id": "workspace", "local_path": str(root)}
            ),
            list_sessions=Mock(
                return_value=[
                    {"session_id": "session", "agent_id": "openai-desktop-harness"}
                ]
            ),
        ),
        create_workspace=AsyncMock(),
    )
    backend = DesktopBackend(service, tmp_path, 5207)
    now = [100.0]
    backend._now = lambda: now[0]
    app = FastAPI()
    app.include_router(backend.router())
    client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    )
    body = {"client_id": "client-1", "binding": backend.binding.model_dump(mode="json")}
    return backend, service, now, client, body


@pytest.mark.asyncio
async def test_heartbeat_renews_but_expired_client_cannot_resurrect(leased):
    backend, _, now, client, body = leased
    async with client:
        response = await client.post("/api/desktop/connect", json=body)
        assert response.status_code == 200
        assert response.json()["connection_lease_seconds"] == 30
        now[0] = 125
        assert (
            await client.post("/api/desktop/heartbeat", json=body)
        ).status_code == 200
        now[0] = 154
        assert (await client.get("/api/desktop/connection")).json()["connected"] is True
        now[0] = 155
        assert (await client.get("/api/desktop/connection")).json()[
            "connected"
        ] is False
        assert (
            await client.post("/api/desktop/heartbeat", json=body)
        ).status_code == 409
        assert not backend.connected
        changed = {**body, "binding": {**body["binding"], "connection_id": "different"}}
        assert (
            await client.post("/api/desktop/connect", json=changed)
        ).status_code == 409
        assert (await client.post("/api/desktop/connect", json=body)).status_code == 200
        assert backend.connected


@pytest.mark.asyncio
async def test_expiry_blocks_mutation_and_preserves_pending_evidence(leased):
    backend, service, now, client, body = leased
    task = DesktopReasoningRequest(
        request_id="lease-request",
        workspace_id="workspace",
        session_id="session",
        run_id="lease-run",
        ordinal=1,
        created_at=datetime.now(timezone.utc).isoformat(),
        kind="response",
        output_format="text",
        binding=backend.binding,
        instruction_set_digest="a" * 64,
        payload={"messages": [], "tools": [], "tool_choice": "none"},
    )
    backend.repository.put_request(task)
    async with client:
        await client.post("/api/desktop/connect", json=body)
        now[0] = 130
        assert (await backend.capabilities())["available"] is False
        assert (
            await client.post(
                "/api/desktop/workspaces", json={"name": "Must not be created"}
            )
        ).status_code == 503
        service.create_workspace.assert_not_awaited()
        response = {
            "request_id": task.request_id,
            "request_digest": task.digest,
            "binding_digest": task.binding.digest,
            "response_id": "late-answer",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "reply": "Never consumed",
        }
        assert (
            await client.post(
                "/api/desktop/reasoning/respond",
                json={
                    "workspace_id": "workspace",
                    "session_id": "session",
                    "response": response,
                },
            )
        ).status_code == 503
        pending = await client.get(
            "/api/desktop/reasoning",
            params={"workspace_id": "workspace", "session_id": "session"},
        )
        assert pending.status_code == 200
        assert pending.json()[0]["request_digest"] == task.digest
        assert backend.repository.pending("workspace", "session") == [task]


@pytest.mark.asyncio
async def test_disconnect_of_one_client_keeps_another_live_lease(leased):
    backend, _, now, client, body = leased
    async with client:
        await client.post("/api/desktop/connect", json=body)
        other = {**body, "client_id": "client-2"}
        now[0] = 110
        await client.post("/api/desktop/connect", json=other)
        now[0] = 131
        assert backend.connected
        assert (await client.post("/api/desktop/disconnect", json=body)).json()[
            "connected"
        ] is True
        assert (await client.post("/api/desktop/disconnect", json=other)).json()[
            "connected"
        ] is False


@pytest.mark.asyncio
async def test_failed_heartbeat_terminates_lifecycle_without_retry(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    import mcp_bridge

    async def immediate(_):
        await asyncio.sleep(0)

    monkeypatch.setattr(mcp_bridge.anyio, "sleep", immediate)
    paths = []

    async def call(method, path, **options):
        paths.append(path)
        if path.endswith("heartbeat"):
            raise RuntimeError("Controlled heartbeat loss")
        return {"connection_lease_seconds": 30, "heartbeat_interval_seconds": 5}

    client = SimpleNamespace(
        client_id="one", binding={}, call=call, http=SimpleNamespace(aclose=AsyncMock())
    )
    with pytest.raises(ExceptionGroup, match="TaskGroup"):
        async with mcp_bridge.connection_lifespan(client):
            await asyncio.Event().wait()
    assert paths == [
        "/api/desktop/connect",
        "/api/desktop/heartbeat",
        "/api/desktop/disconnect",
    ]
    client.http.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_lease_descriptor_is_explicit_and_closes_client(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    import mcp_bridge

    client = SimpleNamespace(
        client_id="one",
        binding={},
        call=AsyncMock(return_value={}),
        http=SimpleNamespace(aclose=AsyncMock()),
    )
    with pytest.raises(ValueError, match="invalid connection lease"):
        async with mcp_bridge.connection_lifespan(client):
            pytest.fail("Missing descriptor must not enable the lifecycle")
    assert [call.args[1] for call in client.call.call_args_list] == [
        "/api/desktop/connect",
        "/api/desktop/disconnect",
    ]
    client.http.aclose.assert_awaited_once()
