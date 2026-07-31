from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from api.surface_host_dispatch import SurfaceHostDispatchMiddleware
from workspace_service.surfaces.process_remote import RemotePreviewEndpoint


pytestmark = pytest.mark.workspace_surfaces


def test_single_public_port_dispatches_opaque_preview_hosts_without_control_fallback() -> None:
    preview = FastAPI()

    @preview.get("/{path:path}")
    async def preview_route(path: str, request: Request) -> JSONResponse:
        if path.split("/", 1)[0] in {"api", "mcp"}:
            raise HTTPException(status_code=404)
        return JSONResponse(
            {
                "plane": "preview",
                "host": request.headers["host"],
                "path": f"/{path}",
            }
        )

    control = FastAPI()

    @control.get("/api/control")
    async def control_route() -> dict[str, str]:
        return {"plane": "control"}

    control.add_middleware(
        SurfaceHostDispatchMiddleware,
        preview_app=preview,
        preview_domain="preview.example.test",
    )
    client = TestClient(control, base_url="http://wright.example.test:8000")

    assert client.get("/api/control").json() == {"plane": "control"}
    preview_response = client.get(
        "/dashboard/deep?series=load",
        headers={"Host": "s-opaque-7.preview.example.test:8000"},
    )
    assert preview_response.status_code == 200
    assert preview_response.json() == {
        "plane": "preview",
        "host": "s-opaque-7.preview.example.test:8000",
        "path": "/dashboard/deep",
    }
    assert (
        client.get(
            "/api/control",
            headers={"Host": "s-opaque-7.preview.example.test:8000"},
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/dashboard/deep",
            headers={"Host": "unbound.other.example.test:8000"},
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    ("endpoint", "expected"),
    [
        (
            RemotePreviewEndpoint(
                internal_origin="http://app:8000",
                public_origin=None,
                browser_reachable=False,
            ),
            None,
        ),
        (
            RemotePreviewEndpoint(
                internal_origin="http://app:8000",
                public_origin="https://s-opaque.preview.example.test",
                browser_reachable=True,
            ),
            "https://s-opaque.preview.example.test",
        ),
    ],
)
def test_remote_adapter_never_guesses_browser_reachability(endpoint, expected) -> None:
    assert endpoint.browser_url == expected
    if expected is None:
        assert endpoint.internal_origin == "http://app:8000"
        assert endpoint.internal_origin != endpoint.browser_url


def test_remote_adapter_requires_vouched_public_origin_for_browser_reachability() -> None:
    with pytest.raises(ValueError, match="vouched public_origin"):
        RemotePreviewEndpoint(
            internal_origin="http://app:8000",
            public_origin=None,
            browser_reachable=True,
        )
    with pytest.raises(ValueError, match="credential-free"):
        RemotePreviewEndpoint(
            internal_origin="http://user:secret@app:8000",
            public_origin=None,
            browser_reachable=False,
        )


def test_remote_projection_contains_no_runtime_authority_or_internal_origin() -> None:
    endpoint = RemotePreviewEndpoint(
        internal_origin="http://app:8000",
        public_origin="https://s-opaque.preview.example.test",
        browser_reachable=True,
    )
    projection = {
        "absoluteBootstrapUrl": (
            f"{endpoint.browser_url}/__wright/bootstrap#one-use-fragment"
        ),
        "expiresAt": datetime(2026, 7, 30, 12, 1, tzinfo=UTC).isoformat(),
    }
    assert endpoint.internal_origin not in str(projection)
    assert "app:8000" not in str(projection)
