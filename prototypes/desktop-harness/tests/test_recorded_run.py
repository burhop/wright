"""Exact recorder observation stays available after accepted source changes."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI
from data_vault import WorkspaceRepository, upgrade_database
from workspace_service.workflow_results import (
    EngineeringResult,
    Provenance,
    Representation,
)


@pytest.fixture
def history(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_backend import DesktopBackend

    root = tmp_path / "workspaces" / "alpha"
    (root / "workflows").mkdir(parents=True)
    (root / "runs" / "history").mkdir(parents=True)
    path = "workflows/history.workflow.wflow"
    prior = "accepted revision one"
    digest = hashlib.sha256(prior.encode()).hexdigest()
    (root / path).write_text("accepted revision two")
    result = EngineeringResult(
        "answer",
        "file",
        "Recorded result",
        (
            Representation(
                "workspace_file",
                "answer.txt",
                sha256=hashlib.sha256(b"exact").hexdigest(),
                size_bytes=5,
            ),
        ),
        Provenance("historic", "task", "result"),
    ).to_dict()
    record = {
        "run_id": "historic",
        "workflow_path": path,
        "source_digest": digest,
        "status": "completed",
        "started_at": "2026-10-17T00:00:00Z",
        "events": [],
        "result": {"run_id": "historic", "results": [result]},
    }
    recorded = root / "runs/history/proof.json"
    recorded.write_text(json.dumps(record))
    database = str(tmp_path / "state.db")
    upgrade_database(database)
    repository = WorkspaceRepository(database, secrets=Mock())
    repository.create("alpha", "desktop-alpha", str(root), workspace_name="Alpha")
    repository.associate_session(
        "alpha", "desktop-alpha", agent_id="openai-desktop-harness"
    )
    owner = SimpleNamespace(db_path=database, repository=repository)
    backend = DesktopBackend(owner, tmp_path, 5207)
    app = FastAPI()
    app.include_router(backend.router())
    return app, root, path, digest, recorded, record


@pytest.mark.asyncio
async def test_real_recorder_reads_older_source_without_mutation_or_action_grants(
    history,
):
    app, root, path, digest, recorded, _ = history
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    body = {
        "workspace_id": "alpha",
        "session_id": "desktop-alpha",
        "path": path,
        "run_id": "historic",
        "source_digest": digest,
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        value = await client.post("/api/desktop/run-records/read", json=body)
        assert value.status_code == 200, value.text
        record = value.json()["record"]
        assert record["run_id"] == "historic" and record["source_digest"] == digest
        assert record["source_matches_current"] is False
        assert record["results"][0]["representations"][0]["size_bytes"] == 5
        assert record["approval"] is None and record["review"] is None
        assert {p: p.read_bytes() for p in before} == before
        for patch, status in [
            ({"session_id": "foreign"}, 403),
            ({"workspace_id": "foreign"}, 403),
            ({"source_digest": "f" * 64}, 409),
            ({"run_id": "missing"}, 409),
            ({"path": "../escape"}, 409),
            ({"resume": True}, 422),
        ]:
            denied = await client.post(
                "/api/desktop/run-records/read", json={**body, **patch}
            )
            assert denied.status_code == status, denied.text
        assert {p: p.read_bytes() for p in before} == before


@pytest.mark.asyncio
async def test_run_metadata_is_redacted_and_malformed_result_fails_closed(history):
    app, _, path, digest, recorded, record = history
    body = {
        "workspace_id": "alpha",
        "session_id": "desktop-alpha",
        "path": path,
        "run_id": "historic",
        "source_digest": digest,
    }
    record["error"] = "token=synthetic-private"
    recorded.write_text(json.dumps(record))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        value = await client.post("/api/desktop/run-records/read", json=body)
        assert value.status_code == 200 and "synthetic-private" not in value.text
        record["result"]["results"][0]["schema_version"] = 2
        recorded.write_text(json.dumps(record))
        assert (
            await client.post("/api/desktop/run-records/read", json=body)
        ).status_code == 409
        record["result"]["results"][0]["schema_version"] = 1
        record["result"]["results"][0]["provenance"]["run_id"] = "foreign"
        recorded.write_text(json.dumps(record))
        assert (
            await client.post("/api/desktop/run-records/read", json=body)
        ).status_code == 409


@pytest.mark.asyncio
async def test_read_port_is_app_only_readonly_and_closed(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from mcp_bridge import server

    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"record": {}})
    )
    bridge = server(client)
    tool = next(
        t for t in await bridge.list_tools() if t.name == "wright_recorded_run_read"
    )
    assert tool.meta["ui"]["visibility"] == ["app"] and tool.annotations.readOnlyHint
    request = {
        "workspace_id": "alpha",
        "session_id": "desktop-alpha",
        "path": "workflows/history.workflow.wflow",
        "run_id": "historic",
        "source_digest": "a" * 64,
    }
    await bridge.call_tool(tool.name, {"request": request})
    client.call.assert_awaited_once_with(
        "POST", "/api/desktop/run-records/read", json=request
    )
    client.call.reset_mock()
    with pytest.raises(Exception):
        await bridge.call_tool(tool.name, {"request": {**request, "approve": True}})
    client.call.assert_not_awaited()
    client.scope.side_effect = RuntimeError("scope denied")
    with pytest.raises(Exception, match="scope denied"):
        await bridge.call_tool(tool.name, {"request": request})
    client.call.assert_not_awaited()
