from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import ANY

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.surface_presentations import get_presentation_service, router
from api.routers.surfaces import get_surface_actor
from core.surfaces.models import SurfaceId
from workspace_service.surfaces.presentation_service import (
    PresentationLaunch,
    PresentationOpenResult,
    PresentationPreferenceDecision,
    PresentationUnavailable,
)
from workspace_service.surfaces.service import ActorRole, SurfaceActor


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


class FakePresentationService:
    def __init__(self) -> None:
        self.calls = []
        self.created = True
        self.error: Exception | None = None

    def open(self, **kwargs):
        self.calls.append(("open", kwargs))
        if self.error:
            raise self.error
        return PresentationOpenResult(
            launch=PresentationLaunch(
                presentation_id="presentation-1",
                instance_id="instance-1",
                generation=2,
                kind=kwargs["kind"],
                absolute_bootstrap_url=(
                    "https://s-presentation-1.preview.test/__wright/bootstrap#token-value"
                ),
                expires_at=NOW + timedelta(seconds=60),
            ),
            created=self.created,
        )

    def close(self, **kwargs):
        self.calls.append(("close", kwargs))
        if self.error:
            raise self.error

    def resolve_preference(self, **kwargs):
        self.calls.append(("resolve_preference", kwargs))
        if self.error:
            raise self.error
        return PresentationPreferenceDecision(
            kind="browser",
            remembered=False,
            reason="No remembered choice is available.",
        )

    def set_preference(self, **kwargs):
        self.calls.append(("set_preference", kwargs))
        if self.error:
            raise self.error
        return PresentationPreferenceDecision(
            kind=kwargs["kind"],
            remembered=True,
            reason="Remembered choice is current and eligible.",
        )


def _actor(**changes) -> SurfaceActor:
    values = dict(
        user_id="user-1",
        workspace_id="workspace-1",
        session_id="session-1",
        role=ActorRole.ENGINEER,
    )
    values.update(changes)
    return SurfaceActor(**values)


def _client(actor: SurfaceActor | None = None):
    app = FastAPI()
    service = FakePresentationService()
    app.include_router(router, prefix="/api/workspace")
    app.dependency_overrides[get_presentation_service] = lambda: service
    if actor is not None:
        app.dependency_overrides[get_surface_actor] = lambda: actor
    return TestClient(app), service


def _headers(**changes) -> dict[str, str]:
    values = {
        "X-Wright-Workspace-ID": "workspace-1",
        "X-Wright-Session-ID": "session-1",
        "Idempotency-Key": "presentation-request-0001",
    }
    values.update(changes)
    return values


def test_create_returns_only_absolute_bootstrap_projection_and_is_idempotent() -> None:
    client, service = _client(_actor())
    response = client.post(
        "/api/workspace/surfaces/surface-app/presentations",
        headers=_headers(),
        json={"kind": "panel", "rememberPreference": True},
    )
    assert response.status_code == 201
    assert response.json() == {
        "presentationId": "presentation-1",
        "instanceId": "instance-1",
        "generation": 2,
        "kind": "panel",
        "absoluteBootstrapUrl": (
            "https://s-presentation-1.preview.test/__wright/bootstrap#token-value"
        ),
        "expiresAt": "2026-07-30T12:01:00Z",
    }
    assert "target" not in response.text.lower()
    assert service.calls[0][1]["surface_id"] == SurfaceId("surface-app")

    service.created = False
    replay = client.post(
        "/api/workspace/surfaces/surface-app/presentations",
        headers=_headers(),
        json={"kind": "panel"},
    )
    assert replay.status_code == 200


def test_create_validates_kind_scope_and_isolated_acknowledgement() -> None:
    client, service = _client(_actor())
    invalid = client.post(
        "/api/workspace/surfaces/surface-app/presentations",
        headers=_headers(),
        json={"kind": "popup"},
    )
    assert invalid.status_code == 422
    service.error = PresentationUnavailable("Presentation unavailable")
    denied = client.post(
        "/api/workspace/surfaces/surface-app/presentations",
        headers=_headers(),
        json={"kind": "panel", "isolatedAcknowledged": True},
    )
    assert denied.status_code == 409

    unauthenticated, _ = _client()
    unauthorized = unauthenticated.post(
        "/api/workspace/surfaces/surface-app/presentations",
        headers=_headers(),
        json={"kind": "panel"},
    )
    assert unauthorized.status_code in {401, 403}


def test_close_is_scoped_and_returns_no_content() -> None:
    client, service = _client(_actor())
    response = client.delete(
        "/api/workspace/surfaces/surface-app/presentations/presentation-1",
        headers={
            "X-Wright-Workspace-ID": "workspace-1",
            "X-Wright-Session-ID": "session-1",
        },
    )
    assert response.status_code == 204
    assert response.content == b""
    assert service.calls == [
        (
            "close",
            {
                "actor": ANY,
                "surface_id": SurfaceId("surface-app"),
                "presentation_id": "presentation-1",
            },
        )
    ]


def test_browser_create_and_preference_routes_project_no_authority() -> None:
    client, service = _client(_actor())
    launch = client.post(
        "/api/workspace/surfaces/surface-app/presentations",
        headers=_headers(),
        json={"kind": "browser"},
    )
    assert launch.status_code == 201
    assert launch.json()["kind"] == "browser"

    current = client.get(
        "/api/workspace/surfaces/surface-app/presentation-preference",
        headers={
            "X-Wright-Workspace-ID": "workspace-1",
            "X-Wright-Session-ID": "session-1",
        },
    )
    assert current.status_code == 200
    assert current.json() == {
        "kind": "browser",
        "remembered": False,
        "reason": "No remembered choice is available.",
    }

    stored = client.put(
        "/api/workspace/surfaces/surface-app/presentation-preference",
        headers={
            "X-Wright-Workspace-ID": "workspace-1",
            "X-Wright-Session-ID": "session-1",
        },
        json={"kind": "panel"},
    )
    assert stored.status_code == 200
    assert stored.json()["remembered"] is True
    assert service.calls[-1][1] == {
        "actor": ANY,
        "surface_id": SurfaceId("surface-app"),
        "kind": "panel",
    }
