from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

import pytest
from jsonschema import Draft202012Validator


pytestmark = pytest.mark.workspace_surfaces
ROOT = Path(__file__).resolve().parents[3]
FIXTURE = (
    ROOT / "tests" / "fixtures" / "workspace_surfaces" / "shareable_app"
)


def test_shareable_app_fixture_matches_the_public_manifest_contract() -> None:
    fixture = FIXTURE / "manifest.surface.json"
    schema = (
        ROOT
        / "packages"
        / "core"
        / "src"
        / "core"
        / "surfaces"
        / "schemas"
        / "v1"
        / "live-app-manifest.schema.json"
    )
    manifest = json.loads(fixture.read_text(encoding="utf-8"))
    Draft202012Validator(
        json.loads(schema.read_text(encoding="utf-8"))
    ).validate(manifest)
    assert manifest["presentation"] == {
        "panel": True,
        "browser": True,
        "sharing": "shared",
        "basePathMode": "root",
        "permissionsPolicy": [],
    }
    assert "${WRIGHT_BIND_HOST}" in manifest["launch"]["argv"]
    assert "${WRIGHT_PORT}" in manifest["launch"]["argv"]


def test_shareable_app_fixture_exposes_one_observable_shared_state() -> None:
    spec = importlib.util.spec_from_file_location(
        "wright_shareable_app_fixture", FIXTURE / "app.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with module.State.lock:
        module.State.value = 0
    server = module.ThreadingHTTPServer(("127.0.0.1", 0), module.Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{origin}/api/state", timeout=2) as response:
            assert json.load(response) == {"value": 0}
        request = Request(f"{origin}/api/state", data=b"", method="POST")
        with urlopen(request, timeout=2) as response:
            assert json.load(response) == {"value": 1}
        with urlopen(f"{origin}/api/state", timeout=2) as response:
            assert json.load(response) == {"value": 1}
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
