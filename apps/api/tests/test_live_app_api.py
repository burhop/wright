from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.live_apps import get_live_app_service, router
from api.routers.surfaces import get_surface_actor
from workspace_service.surfaces.health import ProbeResult
from workspace_service.surfaces.live_app_manager import (
    LiveAppFailure,
    LiveAppInstance,
)
from workspace_service.surfaces.live_app_service import LiveAppControlError
from workspace_service.surfaces.runtime_logs import RuntimeLogEntry, RuntimeLogTail
from workspace_service.surfaces.service import ActorRole, SurfaceActor


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _actor() -> SurfaceActor:
    return SurfaceActor(
        user_id="user-1",
        workspace_id="workspace-1",
        session_id="session-1",
        role=ActorRole.ENGINEER,
    )


def _instance(
    *, state: str = "ready", generation: int = 2, failed: bool = False
) -> LiveAppInstance:
    return LiveAppInstance(
        instance_id="instance-1",
        workspace_id="workspace-1",
        surface_id="surface-app",
        manifest_id="demo.app",
        manifest_hash="a" * 64,
        generation=generation,
        revision=5,
        state=state,
        sharing="shared",
        ownership="launched",
        platform="windows_job",
        runtime_id="internal-runtime-id",
        lifetime_policy="workspace",
        lease_expires_at=None,
        idle_seconds=None,
        last_activity_at=NOW,
        started_at=NOW,
        ready_at=NOW,
        ended_at=NOW if state in {"failed", "stopped"} else None,
        last_health=ProbeResult(
            ok=not failed,
            attempts=2,
            elapsed_seconds=0.02,
            failure_kind="application-status" if failed else None,
            diagnostic_code="SURFACE_READINESS_STATUS_MISMATCH" if failed else None,
            message="Application probe failed"
            if failed
            else "Application probe succeeded",
            observed_status=503 if failed else 200,
        ),
        failure=(
            LiveAppFailure("SURFACE_PROCESS_EXITED", "Application exited", True)
            if failed
            else None
        ),
    )


class FakeLiveAppService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []
        self.result = _instance()
        self.error: Exception | None = None

    async def _call(self, operation: str, **kwargs):
        self.calls.append((operation, kwargs))
        if self.error:
            raise self.error
        return self.result

    async def start(self, **kwargs):
        return await self._call("start", **kwargs)

    async def retry(self, **kwargs):
        return await self._call("retry", **kwargs)

    async def restart(self, **kwargs):
        return await self._call("restart", **kwargs)

    async def stop(self, **kwargs):
        return await self._call("stop", **kwargs)

    async def inspect(self, **kwargs):
        return await self._call("inspect", **kwargs)

    async def health(self, **kwargs):
        return await self._call("health", **kwargs)

    async def logs(self, **kwargs):
        self.calls.append(("logs", kwargs))
        if self.error:
            raise self.error
        return RuntimeLogTail(
            entries=(
                RuntimeLogEntry(
                    sequence=4,
                    stream="stdout",
                    message="dashboard ready",
                    captured_at=NOW,
                    byte_count=15,
                ),
            ),
            rotated=False,
            dropped_bytes=3,
            next_sequence=5,
        )


def _client(*, authenticated: bool = True) -> tuple[TestClient, FakeLiveAppService]:
    app = FastAPI()
    service = FakeLiveAppService()
    app.include_router(router, prefix="/api/workspace")
    app.dependency_overrides[get_live_app_service] = lambda: service
    if authenticated:
        app.dependency_overrides[get_surface_actor] = _actor
    return TestClient(app), service


def _headers() -> dict[str, str]:
    return {
        "X-Wright-Workspace-ID": "workspace-1",
        "X-Wright-Session-ID": "session-1",
        "Idempotency-Key": "managed-app-operation-0001",
    }


@pytest.mark.parametrize("operation", ["start", "retry", "restart", "stop"])
def test_lifecycle_routes_are_authenticated_idempotent_and_thin(operation: str) -> None:
    client, service = _client()
    if operation == "stop":
        service.result = _instance(state="stopped")
    response = client.post(
        f"/api/workspace/surfaces/surface-app/{operation}", headers=_headers()
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["surfaceId"] == "surface-app"
    assert payload["instanceId"] == "instance-1"
    assert payload["generation"] == 2
    assert "internal-runtime-id" not in response.text
    assert service.calls == [
        (
            operation,
            {
                "actor": service.calls[0][1]["actor"],
                "surface_id": service.calls[0][1]["surface_id"],
                "idempotency_key": "managed-app-operation-0001",
            },
        )
    ]
    assert str(service.calls[0][1]["surface_id"]) == "surface-app"


def test_inspect_health_and_redacted_bounded_log_routes() -> None:
    client, service = _client()
    status = client.get(
        "/api/workspace/surfaces/surface-app/live-app", headers=_headers()
    )
    assert status.status_code == 200
    assert {item["operation"] for item in status.json()["actions"]} == {
        "restart",
        "stop",
    }

    health = client.get(
        "/api/workspace/surfaces/surface-app/live-app/health", headers=_headers()
    )
    assert health.status_code == 200
    assert health.json() == {
        "instanceId": "instance-1",
        "generation": 2,
        "state": "ready",
        "ok": True,
        "diagnosticCode": None,
        "message": "Application probe succeeded",
        "observedStatus": 200,
        "attempts": 2,
    }

    logs = client.get(
        "/api/workspace/surfaces/surface-app/live-app/logs?afterSequence=3&limit=10",
        headers=_headers(),
    )
    assert logs.status_code == 200
    assert logs.json()["entries"][0]["message"] == "dashboard ready"
    assert logs.json()["droppedBytes"] == 3
    assert service.calls[-1][1]["after_sequence"] == 3
    assert service.calls[-1][1]["limit"] == 10


def test_invalid_state_returns_stable_safe_problem_and_no_runtime_details() -> None:
    client, service = _client()
    service.error = LiveAppControlError(
        "SURFACE_LIFECYCLE_CONFLICT",
        "Restart is not available from starting",
        retryable=False,
    )
    response = client.post(
        "/api/workspace/surfaces/surface-app/restart", headers=_headers()
    )
    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "SURFACE_LIFECYCLE_CONFLICT",
        "message": "Restart is not available from starting",
        "retryable": False,
    }
    assert "runtime_id" not in response.text


def test_compensation_failure_returns_safe_correlation_reference() -> None:
    client, service = _client()
    service.error = LiveAppControlError(
        "SURFACE_DESCRIPTOR_COMMIT_FAILED",
        "Managed runtime was safely contained. Reference abcdef0123456789.",
        retryable=True,
        correlation_id="abcdef0123456789",
    )

    response = client.post(
        "/api/workspace/surfaces/surface-app/start", headers=_headers()
    )

    assert response.status_code == 409
    assert response.json()["detail"] == {
        "code": "SURFACE_DESCRIPTOR_COMMIT_FAILED",
        "message": "Managed runtime was safely contained. Reference abcdef0123456789.",
        "retryable": True,
        "correlationId": "abcdef0123456789",
    }
    assert "runtime_id" not in response.text


def test_lifecycle_routes_require_engineer_or_administrator_authority() -> None:
    client, service = _client(authenticated=False)
    response = client.post(
        "/api/workspace/surfaces/surface-app/start", headers=_headers()
    )
    assert response.status_code == 403
    assert service.calls == []


def test_operation_requires_bounded_idempotency_key() -> None:
    client, service = _client()
    response = client.post(
        "/api/workspace/surfaces/surface-app/start",
        headers={**_headers(), "Idempotency-Key": "short"},
    )
    assert response.status_code == 422
    assert service.calls == []
