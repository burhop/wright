from __future__ import annotations

import asyncio
import importlib.metadata
import json
import os
import socket
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import pytest

from core.surfaces.live_app_manifest import (
    ManifestPlaceholders,
    parse_live_app_manifest,
)


pytestmark = pytest.mark.workspace_surfaces
LOCK = Path(__file__).with_name("framework-requirements.lock")
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PINNED = {
    "fastapi": "0.139.2",
    "panel": "1.9.3",
    "streamlit": "1.59.2",
    "gradio": "6.20.0",
    "dash": "4.4.1",
}
EXAMPLES = {
    "fastapi": REPOSITORY_ROOT
    / "examples"
    / "workspace-surfaces"
    / "fastapi_dashboard",
    "panel": REPOSITORY_ROOT / "examples" / "workspace-surfaces" / "panel_app",
    "streamlit": REPOSITORY_ROOT
    / "examples"
    / "workspace-surfaces"
    / "streamlit_app",
    "gradio": REPOSITORY_ROOT / "examples" / "workspace-surfaces" / "gradio_app",
    "dash": REPOSITORY_ROOT / "examples" / "workspace-surfaces" / "dash_app",
}


def _require_clean_container() -> None:
    if os.getenv("WRIGHT_FRAMEWORK_CONFORMANCE") != "1":
        pytest.skip(
            "set WRIGHT_FRAMEWORK_CONFORMANCE=1 in the disposable framework image"
        )


def _available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@dataclass(frozen=True)
class RunningTemplate:
    framework: str
    instance_id: str
    origin: str
    client: httpx.AsyncClient
    websocket: bool
    sse: bool


async def _wait_for_readiness(
    process: asyncio.subprocess.Process,
    client: httpx.AsyncClient,
    path: str,
) -> None:
    for _ in range(150):
        if process.returncode is not None:
            output = (await process.stdout.read()).decode(errors="replace")
            raise AssertionError(
                f"framework process exited before readiness ({process.returncode}):\n"
                f"{output[-4000:]}"
            )
        try:
            response = await client.get(path)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        await asyncio.sleep(0.1)
    raise AssertionError(f"framework readiness timed out at {path}")


async def _port_is_closed(port: int) -> bool:
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection("127.0.0.1", port),
            timeout=0.25,
        )
    except (OSError, TimeoutError):
        return True
    writer.close()
    await writer.wait_closed()
    return False


@asynccontextmanager
async def _running_template(framework: str, instance_id: str):
    example = EXAMPLES[framework]
    manifest_path = example / "wright-surface.json"
    assert manifest_path.is_file(), f"missing shipped {framework} template manifest"
    manifest = parse_live_app_manifest(
        json.loads(manifest_path.read_text(encoding="utf-8"))
    )
    port = _available_port()
    origin = f"http://127.0.0.1:{port}"
    command = manifest.resolve_command(
        ManifestPlaceholders(
            bind_host="127.0.0.1",
            port=port,
            public_origin=origin,
            base_path="/",
            instance_id=instance_id,
        ),
        secrets={},
    )
    working_directory = (example / command.cwd).resolve()
    assert working_directory.is_relative_to(example.resolve())
    environment = {
        **os.environ,
        **command.environment,
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "NO_PROXY": "127.0.0.1,localhost",
        "GRADIO_ANALYTICS_ENABLED": "False",
        "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
    }
    process = await asyncio.create_subprocess_exec(
        *command.argv,
        cwd=working_directory,
        env=environment,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    client = httpx.AsyncClient(base_url=origin, timeout=5.0, trust_env=False)
    try:
        await _wait_for_readiness(process, client, manifest.readiness.path)
        yield RunningTemplate(
            framework=framework,
            instance_id=instance_id,
            origin=origin,
            client=client,
            websocket=manifest.transports.websocket,
            sse=manifest.transports.sse,
        )
    finally:
        await client.aclose()
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except TimeoutError:
                process.kill()
                await process.wait()
        for _ in range(20):
            if await _port_is_closed(port):
                break
            await asyncio.sleep(0.05)
        assert await _port_is_closed(port), f"{framework} leaked listener {port}"


def _manifest(framework: str) -> dict:
    commands = {
        "fastapi": [
            "python",
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "${WRIGHT_BIND_HOST}",
            "--port",
            "${WRIGHT_PORT}",
            "--root-path",
            "${WRIGHT_BASE_PATH}",
            "--no-access-log",
        ],
        "panel": ["python", "run_panel.py"],
        "streamlit": [
            "streamlit",
            "run",
            "app.py",
            "--server.address",
            "${WRIGHT_BIND_HOST}",
            "--server.port",
            "${WRIGHT_PORT}",
            "--server.baseUrlPath",
            "${WRIGHT_BASE_PATH}",
            "--server.headless",
            "true",
            "--server.enableCORS",
            "true",
            "--server.enableXsrfProtection",
            "true",
            "--server.fileWatcherType",
            "none",
        ],
        "gradio": ["python", "app.py"],
        "dash": ["python", "app.py"],
    }
    return {
        "schemaVersion": 1,
        "id": f"wright.{framework}.conformance",
        "version": "1.0.0",
        "title": f"{framework.title()} conformance app",
        "ownershipPolicy": "wright-owned",
        "launch": {
            "mode": "command",
            "argv": commands[framework],
            "workingDirectory": ".",
            "environment": {},
            "framework": framework,
        },
        "readiness": {
            "path": "/health",
            "method": "GET",
            "expectedStatus": 200,
            "timeoutMs": 30000,
            "intervalMs": 100,
        },
        "health": {
            "path": "/health",
            "method": "GET",
            "expectedStatus": 200,
            "timeoutMs": 2000,
            "intervalMs": 1000,
        },
        "presentation": {
            "panel": True,
            "browser": True,
            "sharing": "isolated",
            "basePathMode": "root",
            "allowedFrameAncestors": [],
            "permissionsPolicy": [],
        },
        "transports": {
            "http": True,
            "websocket": framework in {"fastapi", "panel", "streamlit", "gradio"},
            "sse": framework == "fastapi",
        },
        "navigation": {
            "allowSameTargetRedirects": True,
            "externalLinks": "prompt-browser",
            "downloads": "deny",
        },
        "lifetime": {"policy": "workspace"},
        "capabilities": [],
        "limits": {},
        "redaction": {"environmentNames": [], "queryNames": []},
    }


def test_disposable_framework_lock_matches_reviewed_current_versions() -> None:
    pins = {
        name: version
        for line in LOCK.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
        for name, version in [line.split("==", 1)]
    }
    assert pins == PINNED


@pytest.mark.parametrize("framework", tuple(PINNED))
def test_framework_manifests_resolve_only_documented_runtime_authority(
    framework: str,
) -> None:
    manifest = parse_live_app_manifest(_manifest(framework))
    resolved = manifest.resolve_command(
        ManifestPlaceholders(
            bind_host="127.0.0.1",
            port=43123,
            public_origin="https://s-opaque.preview.example.test",
            base_path="/",
            instance_id="instance-one",
        ),
        secrets={},
    )
    assert resolved.shell is False
    assert resolved.environment == {
        "WRIGHT_BIND_HOST": "127.0.0.1",
        "WRIGHT_PORT": "43123",
        "WRIGHT_PUBLIC_ORIGIN": "https://s-opaque.preview.example.test",
        "WRIGHT_BASE_PATH": "/",
        "WRIGHT_INSTANCE_ID": "instance-one",
    }
    joined = " ".join(resolved.argv).lower()
    assert "0.0.0.0" not in joined
    assert "--show" not in joined
    assert "--reload" not in joined
    assert "*" not in joined
    assert "http://" not in joined and "https://" not in joined
    assert manifest.readiness.path == "/health"
    assert manifest.health is not None and manifest.health.path == "/health"


@pytest.mark.parametrize("framework", tuple(PINNED))
def test_clean_container_installed_framework_version_matches_lock(
    framework: str,
) -> None:
    _require_clean_container()
    assert importlib.metadata.version(framework) == PINNED[framework]


@pytest.mark.asyncio
@pytest.mark.parametrize("framework", tuple(PINNED))
async def test_clean_container_root_deep_asset_redirect_cookie_upload_health_offline(
    framework: str,
) -> None:
    _require_clean_container()
    async with _running_template(framework, f"{framework}-one") as app:
        root = await app.client.get("/")
        assert root.status_code == 200
        assert app.instance_id in root.text

        deep = await app.client.get("/deep/link")
        assert deep.status_code == 200
        assert app.instance_id in deep.text

        asset = await app.client.get("/assets/app.css")
        assert asset.status_code == 200
        assert "text/css" in asset.headers["content-type"]

        redirect = await app.client.get("/redirect", follow_redirects=False)
        assert redirect.status_code in {301, 302, 307, 308}
        destination = urljoin(app.origin, redirect.headers["location"])
        assert urlparse(destination).netloc == urlparse(app.origin).netloc
        followed = await app.client.get(destination)
        assert followed.status_code == 200

        cookie = await app.client.get("/cookie")
        assert cookie.status_code == 200
        assert "samesite=strict" in cookie.headers["set-cookie"].lower()
        cookie_check = await app.client.get("/cookie/check")
        assert cookie_check.json()["instanceId"] == app.instance_id

        upload = await app.client.post(
            "/upload",
            files={"file": ("small.txt", b"small upload", "text/plain")},
        )
        assert upload.status_code == 200
        assert upload.json()["bytes"] == len(b"small upload")
        oversized = await app.client.post(
            "/upload",
            files={"file": ("large.bin", b"x" * 1_048_577)},
        )
        assert oversized.status_code == 413

        health = await app.client.get("/health")
        assert health.status_code == 200
        assert health.json()["instanceId"] == app.instance_id

        offline_text = f"{root.text}\n{asset.text}".lower().replace(
            app.origin.lower(),
            "",
        )
        assert "https://" not in offline_text
        assert "http://" not in offline_text
        assert "//cdn." not in offline_text


@pytest.mark.asyncio
@pytest.mark.parametrize("framework", tuple(PINNED))
async def test_clean_container_websocket_and_sse_capabilities(framework: str) -> None:
    _require_clean_container()
    async with _running_template(framework, f"{framework}-transport") as app:
        if app.websocket:
            from websockets.asyncio.client import connect

            websocket_url = app.origin.replace("http://", "ws://") + "/ws"
            async with connect(websocket_url, origin=app.origin) as websocket:
                await websocket.send("workspace-surface")
                assert await websocket.recv() == (
                    f"{app.instance_id}:workspace-surface"
                )
        if app.sse:
            async with app.client.stream("GET", "/events") as response:
                assert response.status_code == 200
                iterator = response.aiter_lines()
                lines = [await anext(iterator) for _ in range(2)]
                assert "event: ready" in lines
                assert f"data: {app.instance_id}" in lines


@pytest.mark.asyncio
@pytest.mark.parametrize("framework", tuple(PINNED))
async def test_clean_container_two_instances_are_isolated_and_shutdown(
    framework: str,
) -> None:
    _require_clean_container()
    async with (
        _running_template(framework, f"{framework}-left") as left,
        _running_template(framework, f"{framework}-right") as right,
    ):
        assert left.origin != right.origin
        left_root, right_root = await asyncio.gather(
            left.client.get("/"),
            right.client.get("/"),
        )
        assert left.instance_id in left_root.text
        assert right.instance_id not in left_root.text
        assert right.instance_id in right_root.text
        assert left.instance_id not in right_root.text

        await left.client.get("/cookie")
        left_cookie, right_cookie = await asyncio.gather(
            left.client.get("/cookie/check"),
            right.client.get("/cookie/check"),
        )
        assert left_cookie.json()["instanceId"] == left.instance_id
        assert right_cookie.status_code in {401, 404}
