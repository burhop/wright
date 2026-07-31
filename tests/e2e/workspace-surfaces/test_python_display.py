from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
import sqlite3

from fastapi import FastAPI
from fastapi.testclient import TestClient

import wright
from api.routers.surface_displays import (
    get_display_service,
    get_display_token_service,
    router,
)
from data_vault import SurfaceVault, upgrade_database
from workspace_service.surfaces.display_service import (
    DisplayExecutionContext,
    DisplayService,
)
from workspace_service.surfaces.display_tokens import (
    DisplayExecutionClaims,
    DisplayExecutionTokenService,
)
from wright.client import DisplayClient, use_display_client


NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _stack(tmp_path: Path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '/workspace/one', 1, 1)"""
        )
        connection.commit()
    vault_root = tmp_path / "vault"
    service = DisplayService(database, vault=SurfaceVault(vault_root), clock=lambda: NOW)
    tokens = DisplayExecutionTokenService(secret=b"test-secret" * 4, clock=lambda: NOW)
    claims = DisplayExecutionClaims(
            audience="wright-display-ingest-v1",
            user_id="user-1",
            workspace_id="workspace-1",
            session_id="session-1",
            task_id="task-1",
            execution_id="execution-1",
            expires_at=NOW + timedelta(minutes=5),
            prompt="Graph the measured load.",
            effective_constraints={"offline": True},
            script="import wright\nwright.line(...)\n",
            script_revision=1,
            trace_id="a" * 32,
    )
    token = tokens.issue(claims)
    app = FastAPI()
    app.include_router(router, prefix="/api/workspace")
    app.dependency_overrides[get_display_service] = lambda: service
    app.dependency_overrides[get_display_token_service] = lambda: tokens
    api = TestClient(app)

    def transport(method, url, headers, payload):
        response = api.request(method, url, headers=headers, json=payload)
        body = response.json() if response.content else None
        return response.status_code, body

    client = DisplayClient(
        endpoint="/api/workspace/surfaces/displays",
        token=token,
        workspace_id="workspace-1",
        transport=transport,
    )
    context = DisplayExecutionContext(
        user_id=claims.user_id,
        workspace_id=claims.workspace_id,
        session_id=claims.session_id,
        task_id=claims.task_id,
        execution_id=claims.execution_id,
        prompt=claims.prompt,
        no_prompt=False,
        effective_constraints=claims.effective_constraints,
        script=claims.script,
        script_revision=claims.script_revision,
        trace_id=claims.trace_id,
    )
    return database, vault_root, service, api, client, context


def test_beginner_graph_update_history_error_and_durability_after_exit(
    tmp_path: Path,
) -> None:
    database, vault_root, service, api, client, context = _stack(tmp_path)
    with use_display_client(client):
        first = wright.line(
            x=[0, 1, 2],
            y=[10, 12, 15],
            title="Measured load",
            x_label="Time (s)",
            y_label="Load (N)",
            description="Load rises from 10 N to 15 N.",
            display_id="loads",
        )
        second = wright.line(
            x=[0, 1, 2],
            y=[10, 13, 18],
            title="Measured load",
            x_label="Time (s)",
            y_label="Load (N)",
            description="Updated load rises from 10 N to 18 N.",
            display_id="loads",
        )

    assert first.surface_id == second.surface_id
    assert (first.revision, second.revision) == (1, 2)
    assert [
        item.revision
        for item in service.history(display_id="loads", context=context)
    ] == [1, 2]

    headers = {
        "Authorization": f"Bearer {client.token}",
        "X-Wright-Workspace-ID": "workspace-1",
    }
    projection = api.get(
        f"/api/workspace/surfaces/{second.surface_id}/display", headers=headers
    )
    assert projection.status_code == 200
    assert projection.json()["revision"] == 2
    assert projection.json()["representations"][0]["mediaType"] == (
        "application/vnd.plotly.v1+json"
    )
    history = api.get(
        f"/api/workspace/surfaces/{second.surface_id}/history", headers=headers
    )
    assert history.status_code == 200
    assert [item["revision"] for item in history.json()["items"]] == [1, 2]
    verification = api.get(
        f"/api/workspace/surfaces/{second.surface_id}/verification", headers=headers
    )
    assert verification.status_code == 200
    assert verification.json()["prompt"] == "Graph the measured load."
    assert verification.json()["script_revision"] == 1

    missing = api.get(
        "/api/workspace/surfaces/display-does-not-exist/history", headers=headers
    )
    assert missing.status_code == 404

    recovered = DisplayService(
        database, vault=SurfaceVault(vault_root), clock=lambda: NOW
    )
    assert recovered.history(display_id="loads", context=context)[-1].current


def test_delete_endpoint_requires_retention_disclosure(tmp_path: Path) -> None:
    _database, _vault, _service, api, client, _context = _stack(tmp_path)
    with use_display_client(client):
        handle = wright.bar(
            x=["A", "B"],
            y=[2, 3],
            title="Counts",
            x_label="Category",
            y_label="Count",
            description="Category B has the larger count.",
            display_id="counts",
        )
    headers = {
        "Authorization": f"Bearer {client.token}",
        "X-Wright-Workspace-ID": "workspace-1",
    }
    denied = api.delete(
        f"/api/workspace/surfaces/{handle.surface_id}/display",
        headers=headers,
        params={"retentionDisclosureConfirmed": "false"},
    )
    assert denied.status_code == 409
    deleted = api.delete(
        f"/api/workspace/surfaces/{handle.surface_id}/display",
        headers=headers,
        params={"retentionDisclosureConfirmed": "true"},
    )
    assert deleted.status_code == 200
    assert deleted.json() == {
        "deleted": True,
        "recoverable": False,
        "retentionStatus": "payload_cleanup_scheduled",
    }
