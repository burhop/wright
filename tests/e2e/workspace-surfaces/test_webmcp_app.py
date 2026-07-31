from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from jsonschema import Draft202012Validator

ROOT = Path(__file__).parents[3]
EXAMPLE = ROOT / "examples" / "workspace-surfaces" / "webmcp_app"


def _available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _read(url: str) -> str:
    with urlopen(url, timeout=1) as response:  # noqa: S310 - fixed loopback fixture
        return response.read().decode()


def test_reference_webmcp_app_manifest_health_and_cleanup() -> None:
    schema = json.loads(
        (
            ROOT
            / "packages/core/src/core/surfaces/schemas/v1/live-app-manifest.schema.json"
        ).read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (EXAMPLE / "webmcp.surface.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(manifest)
    assert manifest["capabilities"] == ["wright.webmcp.register"]
    assert manifest["presentation"] == {
        "panel": True,
        "browser": True,
        "sharing": "shared",
    }

    port = _available_port()
    process = subprocess.Popen(  # noqa: S603 - fixed interpreter and repository fixture
        [sys.executable, str(EXAMPLE / "server.py"), "--port", str(port)],
        cwd=EXAMPLE,
    )
    try:
        deadline = time.monotonic() + 5
        while True:
            try:
                assert json.loads(_read(f"http://127.0.0.1:{port}/health")) == {
                    "status": "ready"
                }
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)

        page = _read(f"http://127.0.0.1:{port}/")
        sdk = _read(f"http://127.0.0.1:{port}/wright-surface-sdk.js")
        app = _read(f"http://127.0.0.1:{port}/app.js")
        assert "Scoped WebMCP graph" in page
        assert 'new URL("/__wright/webmcp"' in sdk
        assert 'addEventListener("pagehide"' in sdk
        assert "document.modelContext?.registerTool" in app
        assert "document.modelContext =" not in app
    finally:
        process.terminate()
        process.wait(timeout=5)

    assert process.returncode is not None
