from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote

import pytest
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from api.main import _resolve_spa_asset, proxy_onshape, proxy_onshape_path


class _FailingAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, *args, **kwargs):
        raise RuntimeError("sentinel C:\\private\\onshape-token.txt")


def _request(
    trace_id: str = "trace-main-123", path: str = "/api/proxy/onshape"
) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": b"",
            "headers": [],
            "state": {"trace_id": trace_id},
            "app": SimpleNamespace(state=SimpleNamespace()),
        }
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("path", [None, "documents/example"])
async def test_onshape_proxy_failure_is_generic_and_trace_bearing(monkeypatch, path):
    monkeypatch.setattr("api.main.httpx.AsyncClient", _FailingAsyncClient)
    request = _request()

    if path is None:
        response = await proxy_onshape(request)
    else:
        response = await proxy_onshape_path(path, request)

    body = response.body.decode()
    assert response.status_code == 502
    assert response.headers["x-trace-id"] == "trace-main-123"
    assert "Failed to connect to Onshape." in body
    assert "trace-main-123" in body
    assert "sentinel" not in body
    assert "onshape-token" not in body


@pytest.mark.asyncio
async def test_spa_asset_resolver_accepts_regular_file_inside_root(tmp_path):
    dist = tmp_path / "dist"
    asset = dist / "assets" / "app.js"
    asset.parent.mkdir(parents=True)
    asset.write_text("console.log('ok')", encoding="utf-8")

    response = await _resolve_spa_asset(
        StaticFiles(directory=dist),
        "assets/app.js",
        _request(path="/assets/app.js"),
    )

    assert response is not None
    assert Path(response.path).resolve() == asset.resolve()


@pytest.mark.parametrize(
    "requested_path",
    [
        "../outside.txt",
        "%2e%2e%2foutside.txt",
    ],
)
@pytest.mark.asyncio
async def test_spa_asset_resolver_rejects_plain_and_encoded_traversal(
    tmp_path, requested_path
):
    dist = tmp_path / "dist"
    dist.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    decoded = unquote(requested_path)
    assert (
        await _resolve_spa_asset(
            StaticFiles(directory=dist), decoded, _request(path=f"/{decoded}")
        )
        is None
    )


@pytest.mark.asyncio
async def test_spa_asset_resolver_rejects_absolute_and_sibling_prefix_paths(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    sibling = tmp_path / "dist-evil"
    sibling.mkdir()
    secret = sibling / "secret.txt"
    secret.write_text("secret", encoding="utf-8")

    static_files = StaticFiles(directory=dist)
    assert (
        await _resolve_spa_asset(
            static_files, str(secret.resolve()), _request(path="/absolute")
        )
        is None
    )
    assert (
        await _resolve_spa_asset(
            static_files,
            "../dist-evil/secret.txt",
            _request(path="/../dist-evil/secret.txt"),
        )
        is None
    )


@pytest.mark.asyncio
async def test_spa_asset_resolver_rejects_symlink_to_outside_root(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = dist / "linked.txt"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Host does not permit symlink creation: {exc}")

    assert (
        await _resolve_spa_asset(
            StaticFiles(directory=dist),
            "linked.txt",
            _request(path="/linked.txt"),
        )
        is None
    )
