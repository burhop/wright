from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from api.routers.surfaces import get_surface_service, router
from data_vault import (
    GenerationProvenanceRepository,
    SurfaceRepository,
    upgrade_database,
)
from workspace_service.surfaces.service import SurfaceService


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _database(tmp_path: Path) -> Path:
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.executemany(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, 1, 1)""",
            [
                ("workspace-1", "session-1", "/workspace/one"),
                ("workspace-2", "session-2", "/workspace/two"),
            ],
        )
        connection.commit()
    return database


def _client(database: Path) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def actor(request: Request, call_next):
        request.state.principal_id = request.headers.get("X-Test-User", "user-1")
        request.state.principal_role = request.headers.get("X-Test-Role", "engineer")
        return await call_next(request)

    app.include_router(router, prefix="/api/workspace")
    service = SurfaceService(repository=SurfaceRepository(database))
    app.dependency_overrides[get_surface_service] = lambda: service
    return TestClient(app)


def _headers(**overrides) -> dict[str, str]:
    values = {
        "X-Wright-Workspace-ID": "workspace-1",
        "X-Wright-Session-ID": "session-1",
        "Idempotency-Key": "surface-scope-0001",
        "X-Test-User": "user-1",
        "X-Test-Role": "engineer",
    }
    values.update(overrides)
    return values


def test_surface_api_never_crosses_user_workspace_or_session_scope(
    tmp_path: Path,
) -> None:
    client = _client(_database(tmp_path))
    created = client.post(
        "/api/workspace/surfaces",
        headers=_headers(),
        json={
            "schemaVersion": 1,
            "kind": "external_url",
            "url": "https://docs.example.test/guide",
            "approval": "explicit_view_only_instance",
        },
    )
    assert created.status_code == 201
    surface_id = created.json()["surfaceId"]
    assert (
        client.get(
            f"/api/workspace/surfaces/{surface_id}", headers=_headers()
        ).status_code
        == 200
    )
    for hostile_headers in (
        _headers(**{"X-Test-User": "user-2"}),
        _headers(**{"X-Wright-Session-ID": "other-session"}),
        _headers(
            **{
                "X-Wright-Workspace-ID": "workspace-2",
                "X-Wright-Session-ID": "session-2",
            }
        ),
    ):
        response = client.get(
            f"/api/workspace/surfaces/{surface_id}", headers=hostile_headers
        )
        assert response.status_code == 404
        assert "docs.example.test" not in response.text


def test_engineer_cannot_approve_attach_but_administrator_can(tmp_path: Path) -> None:
    client = _client(_database(tmp_path))
    body = {
        "schemaVersion": 1,
        "kind": "live_app",
        "manifest": {
            "id": "attached-app",
            "title": "Attached app",
            "version": "1.0.0",
            "launch": {"mode": "attach", "url": "https://app.example.test"},
        },
    }
    denied = client.post("/api/workspace/surfaces", headers=_headers(), json=body)
    assert denied.status_code == 403
    allowed = client.post(
        "/api/workspace/surfaces",
        headers=_headers(
            **{
                "X-Test-Role": "admin",
                "Idempotency-Key": "surface-scope-admin-0001",
            }
        ),
        json=body,
    )
    assert allowed.status_code == 201


def test_generated_provenance_repository_requires_exact_workspace_user(
    tmp_path: Path,
) -> None:
    database = _database(tmp_path)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO workspace_surfaces (
                surface_id, workspace_id, user_id, session_id, schema_version,
                source_kind, source_id, source_version, source_json, title,
                lifecycle, presentations_json, capabilities_json, revision,
                created_at, updated_at
            ) VALUES ('display-1', 'workspace-1', 'user-1', 'session-1', 1,
                'display', 'task:chart', '1', '{}', 'Chart', 'ready', '[]', '[]',
                1, ?, ?)""",
            (NOW.isoformat(), NOW.isoformat()),
        )
        connection.execute(
            """INSERT INTO surface_display_artifacts (
                artifact_id, surface_id, workspace_id, display_id, revision,
                producer_execution_id, producer_task_id, representations_json,
                durability, current, idempotency_key, created_at
            ) VALUES ('artifact-1', 'display-1', 'workspace-1', 'chart', 1,
                'execution-1', 'task-1', '[]', 'durable', 1, 'artifact-request-1', ?)""",
            (NOW.isoformat(),),
        )
        connection.execute(
            """INSERT INTO surface_generation_provenance (
                artifact_id, workspace_id, mode, no_prompt,
                constraints_vault_digest, script_vault_digest,
                script_content_hash, script_revision, task_id, execution_id,
                trace_id, created_at
            ) VALUES ('artifact-1', 'workspace-1', 'direct_execution', 1,
                'sha256:constraints', 'sha256:script', ?, 1, 'task-1',
                'execution-1', '0123456789abcdef', ?)""",
            ("a" * 64, NOW.isoformat()),
        )
        connection.commit()
    repository = GenerationProvenanceRepository(database)
    assert (
        repository.get(
            artifact_id="artifact-1", workspace_id="workspace-1", user_id="user-1"
        )
        is not None
    )
    assert (
        repository.get(
            artifact_id="artifact-1", workspace_id="workspace-1", user_id="user-2"
        )
        is None
    )
    assert (
        repository.get(
            artifact_id="artifact-1", workspace_id="workspace-2", user_id="user-1"
        )
        is None
    )
