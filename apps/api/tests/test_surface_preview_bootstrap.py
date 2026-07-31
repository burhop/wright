from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.surface_preview import get_presentation_tokens, router
from api.surface_host_dispatch import SurfaceHostDispatchMiddleware
from core.surfaces.models import (
    LiveAppOwnership,
    LiveAppSurfaceSource,
    SharingMode,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
)
from data_vault import SurfaceRepository, upgrade_database
from workspace_service.config import SurfacePreviewSettings
from workspace_service.surfaces.presentation_service import PresentationService
from workspace_service.surfaces.presentation_tokens import (
    PresentationTokenError,
    PresentationTokenService,
)
from workspace_service.surfaces.service import ActorRole, SurfaceActor


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)
PREVIEW = SurfacePreviewSettings(
    scheme="https",
    bind_host="127.0.0.1",
    domain="preview.example.test",
    public_port=443,
)


def _actor() -> SurfaceActor:
    return SurfaceActor(
        user_id="user-1",
        workspace_id="workspace-1",
        session_id="session-1",
        role=ActorRole.ENGINEER,
    )


def _ready_surface() -> SurfaceDescriptor:
    return SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("surface-app"),
        workspace_id="workspace-1",
        source=LiveAppSurfaceSource(
            manifest_id="app",
            manifest_version="1.0.0",
            manifest_hash="a" * 64,
            ownership=LiveAppOwnership.WRIGHT_OWNED,
            administrator_approved=True,
            sharing_mode=SharingMode.SHARED,
        ),
        title="App",
        lifecycle=SurfaceLifecycle.READY,
        instance={
            "instanceId": "instance-1",
            "generation": 2,
            "sharing": "shared",
        },
        presentations=(
            {"kind": "panel", "eligible": True},
            {"kind": "browser", "eligible": True},
        ),
        revision=SurfaceRevision(3),
        created_at=NOW,
        updated_at=NOW,
    )


def _services(tmp_path: Path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = SurfaceRepository(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', '/workspace/one', 1, 1)"""
        )
        connection.commit()
    repository.create(
        _ready_surface(),
        user_id="user-1",
        session_id="session-1",
        idempotency_key="declare-ready-app",
    )
    current = [NOW]
    presentations = PresentationService(
        database,
        preview=PREVIEW,
        clock=lambda: current[0],
        id_factory=lambda: "presentation-panel",
        token_factory=lambda: "A" * 43,
        token_ttl_seconds=60,
        presentation_ttl_seconds=8 * 60 * 60,
    )
    launch = presentations.open(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        kind="panel",
        idempotency_key="open-panel-request",
    ).launch
    tokens = PresentationTokenService(
        database,
        preview=PREVIEW,
        clock=lambda: current[0],
        cookie_factory=lambda: "C" * 43,
    )
    return current, presentations, tokens, launch


def _client(tokens: PresentationTokenService) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_presentation_tokens] = lambda: tokens
    return TestClient(app)


def test_fragment_bootstrap_document_never_receives_or_reflects_token(
    tmp_path: Path,
) -> None:
    _clock, _presentations, tokens, launch = _services(tmp_path)
    parsed = urlsplit(launch.absolute_bootstrap_url)
    client = _client(tokens)
    response = client.get("/__wright/bootstrap", headers={"Host": parsed.netloc})
    assert response.status_code == 200
    assert parsed.fragment not in response.text
    assert "location.hash" in response.text
    assert "history.replaceState" in response.text
    assert "method: 'POST'" in response.text
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["content-security-policy"]


def test_body_exchange_is_single_use_and_sets_only_a_host_cookie(
    tmp_path: Path,
) -> None:
    _clock, _presentations, tokens, launch = _services(tmp_path)
    parsed = urlsplit(launch.absolute_bootstrap_url)
    client = _client(tokens)
    wrong = client.post(
        "/__wright/bootstrap",
        headers={"Host": parsed.netloc},
        json={"token": "Z" * 43},
    )
    assert wrong.status_code == 401
    response = client.post(
        "/__wright/bootstrap",
        headers={"Host": parsed.netloc},
        json={"token": parsed.fragment},
    )
    assert response.status_code == 204
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("wright_surface=")
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Secure" in cookie
    assert "Path=/" in cookie
    assert "Domain=" not in cookie
    assert parsed.fragment not in cookie

    replay = client.post(
        "/__wright/bootstrap",
        headers={"Host": parsed.netloc},
        json={"token": parsed.fragment},
    )
    assert replay.status_code == 410


def test_bootstrap_ttl_host_audience_cookie_and_close_revocation(
    tmp_path: Path,
) -> None:
    clock, presentations, tokens, launch = _services(tmp_path)
    parsed = urlsplit(launch.absolute_bootstrap_url)
    with pytest.raises(PresentationTokenError) as wrong_host:
        tokens.exchange(
            host="s-wrong.preview.example.test",
            token=parsed.fragment,
        )
    assert wrong_host.value.code == "SURFACE_PREVIEW_NOT_FOUND"

    session = tokens.exchange(host=parsed.netloc, token=parsed.fragment)
    assert tokens.authorize(host=parsed.netloc, cookie=session.cookie_value).state == (
        "active"
    )
    with pytest.raises(PresentationTokenError) as wrong_cookie:
        tokens.authorize(host=parsed.netloc, cookie="D" * 43)
    assert wrong_cookie.value.code == "SURFACE_PREVIEW_UNAUTHORIZED"

    presentations.close(
        actor=_actor(),
        surface_id=SurfaceId("surface-app"),
        presentation_id=launch.presentation_id,
    )
    with pytest.raises(PresentationTokenError) as revoked:
        tokens.authorize(host=parsed.netloc, cookie=session.cookie_value)
    assert revoked.value.code == "SURFACE_PREVIEW_GONE"


def test_bootstrap_token_expires_before_the_presentation(tmp_path: Path) -> None:
    clock, _presentations, tokens, launch = _services(tmp_path)
    parsed = urlsplit(launch.absolute_bootstrap_url)
    clock[0] = NOW + timedelta(seconds=61)
    with pytest.raises(PresentationTokenError) as expired:
        tokens.exchange(host=parsed.netloc, token=parsed.fragment)
    assert expired.value.code == "SURFACE_PREVIEW_GONE"


def test_preview_dispatch_denies_control_routes_and_unbound_hosts(
    tmp_path: Path,
) -> None:
    _clock, _presentations, tokens, launch = _services(tmp_path)
    parsed = urlsplit(launch.absolute_bootstrap_url)
    preview_app = FastAPI()
    preview_app.include_router(router)
    preview_app.dependency_overrides[get_presentation_tokens] = lambda: tokens
    control_app = FastAPI()

    @control_app.get("/api/secret")
    def control_secret() -> dict[str, bool]:
        return {"secret": True}

    control_app.add_middleware(
        SurfaceHostDispatchMiddleware,
        preview_app=preview_app,
        preview_domain=PREVIEW.domain,
    )
    client = TestClient(control_app)
    assert client.get("/api/secret", headers={"Host": "wright.test"}).status_code == 200
    assert client.get("/api/secret", headers={"Host": parsed.netloc}).status_code == 404
    assert client.get("/mcp", headers={"Host": parsed.netloc}).status_code == 404
    assert (
        client.get(
            "/__wright/bootstrap",
            headers={"Host": "s-unbound.preview.example.test"},
        ).status_code
        == 404
    )


def test_reserved_mcp_sandbox_host_serves_only_bundled_proxy_assets(
    tmp_path: Path,
) -> None:
    sandbox = tmp_path / "surface-sandbox"
    sandbox.mkdir()
    (sandbox / "index.html").write_text("<h1>proxy</h1>", encoding="utf-8")
    (sandbox / "sandbox-proxy.js").write_text("void 0;", encoding="utf-8")
    preview_app = FastAPI()
    preview_app.state.surface_sandbox_domain = PREVIEW.domain
    preview_app.state.surface_sandbox_dist_dir = tmp_path
    preview_app.include_router(router)
    control_app = FastAPI()
    control_app.add_middleware(
        SurfaceHostDispatchMiddleware,
        preview_app=preview_app,
        preview_domain=PREVIEW.domain,
    )
    client = TestClient(control_app)
    host = f"mcp-sandbox.{PREVIEW.domain}"

    response = client.get("/surface-sandbox/index.html", headers={"Host": host})
    assert response.status_code == 200
    assert response.text == "<h1>proxy</h1>"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors http: https:" in response.headers["content-security-policy"]
    assert response.headers["permissions-policy"].startswith("camera=*")
    assert client.get("/api/secret", headers={"Host": host}).status_code == 404
    assert (
        client.get("/surface-sandbox/unknown.js", headers={"Host": host}).status_code
        == 404
    )
    assert (
        client.get(
            "/surface-sandbox/index.html",
            headers={"Host": f"evil.{PREVIEW.domain}"},
        ).status_code
        == 404
    )
