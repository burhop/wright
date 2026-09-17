from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.testclient import TestClient
from tool_registry.program_status import ProgramStatusReader

from api.routers.program_status import router


ROOT = Path(__file__).resolve().parents[2]
PACKAGED = ROOT / "src" / "wright_engineering" / "static"


def _source_free_package(tmp_path: Path) -> Path:
    package = tmp_path / "installed-wheel" / "wright_engineering" / "static"
    shutil.copytree(PACKAGED / "program-status", package / "program-status")
    shutil.copytree(PACKAGED / "web", package / "web")
    assert not (tmp_path / ".git").exists()
    return package


def test_packaged_api_and_spa_work_without_checkout_git_or_network(
    tmp_path: Path, monkeypatch
) -> None:
    package = _source_free_package(tmp_path)
    monkeypatch.setenv("PATH", "")
    assert shutil.which("git") is None

    app = FastAPI()
    app.state.security_settings = SimpleNamespace(enforced=False)
    app.state.program_status_reader = ProgramStatusReader(
        tmp_path / "wright-data" / "program-status",
        package / "program-status",
    )
    app.include_router(router, prefix="/api/program-status")

    @app.get("/{_path:path}")
    def serve_spa(_path: str) -> FileResponse:
        return FileResponse(package / "web" / "index.html")

    client = TestClient(app)
    response = client.get("/api/program-status")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache, private"
    assert response.json()["source"]["commit"]

    unchanged = client.get(
        "/api/program-status", headers={"If-None-Match": response.headers["etag"]}
    )
    assert unchanged.status_code == 304
    assert unchanged.content == b""

    page = client.get("/program-status")
    assert page.status_code == 200
    assert '<div id="root"></div>' in page.text
    scripts = list((package / "web" / "assets").glob("index-*.js"))
    assert len(scripts) == 1
    assert b"program-status" in scripts[0].read_bytes()
