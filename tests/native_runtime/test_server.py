from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from wright_engineering.runtime import server
from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.server import (
    ServerBootstrapError,
    packaged_static_path,
    prepare_runtime_environment,
    runtime_identity_payload,
    native_ui_url,
)


ROOT = Path(__file__).resolve().parents[2]


def test_packaged_server_bootstrap_uses_stable_data_and_prebuilt_ui(
    tmp_path: Path, monkeypatch
) -> None:
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<html>Wright</html>", encoding="utf-8")
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")

    environment: dict[str, str] = {}
    values = prepare_runtime_environment(
        layout, static_path=static, environment=environment
    )

    assert values["DATABASE_PATH"] == str(layout.data / "wright.db")
    assert values["FRONTEND_DIST_DIR"] == str(static.resolve())
    assert values["WRIGHT_RIVET_WORKFLOWS_ENABLED"] == "1"
    assert values["WRIGHT_RIVET_RUNNER_ENABLED"] == "1"
    assert values["WRIGHT_RIVET_EDITOR_ENABLED"] == "1"
    assert values["WRIGHT_RIVET_AI_ENABLED"] == "1"
    assert values["WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED"] == "1"
    assert values["WRIGHT_SURFACES_ENABLED"] == "1"
    assert values["WRIGHT_SURFACES_LIVE_APPS_ENABLED"] == "1"
    assert values["WRIGHT_SURFACE_PREVIEW_DOMAIN"] == "wright.localhost"
    assert values["WRIGHT_SURFACE_PREVIEW_PORT"] == "8000"
    assert values["WRIGHT_ALLOWED_ORIGINS"] == ",".join(
        (
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://wright.localhost:8000",
        )
    )
    assert values["WRIGHT_WORKSPACE_ROOT"] == str(layout.workspaces)
    assert values["WRIGHT_WORKSPACES_DIR"] == str(layout.workspaces)
    assert environment == values
    assert layout.workspaces.is_dir()


def test_native_loopback_ui_and_rivet_preview_share_a_browser_site() -> None:
    ui_url = native_ui_url("127.0.0.1", 8765)

    assert ui_url == "http://wright.localhost:8765/"
    assert "s-presentation.wright.localhost".endswith(
        "." + ui_url.split("//", 1)[1].split(":", 1)[0]
    )


def test_windows_workstation_startup_enables_rivet_without_eager_launch() -> None:
    startup_script = (ROOT / "scripts" / "windows" / "start-wright.ps1").read_text(
        encoding="utf-8"
    )
    for feature_flag in (
        "WRIGHT_RIVET_WORKFLOWS_ENABLED",
        "WRIGHT_RIVET_EDITOR_ENABLED",
        "WRIGHT_RIVET_AI_ENABLED",
        "WRIGHT_RIVET_RUNNER_ENABLED",
        "WRIGHT_RIVET_REAL_EXECUTION_ENABLED",
        "WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED",
        "WRIGHT_SURFACES_ENABLED",
        "WRIGHT_SURFACES_LIVE_APPS_ENABLED",
    ):
        assert f'$env:{feature_flag} = "1"' in startup_script

    api_start = startup_script.index('Start-HiddenProcess -Name "wright-api"')
    for feature_flag in (
        "WRIGHT_RIVET_EDITOR_ENABLED",
        "WRIGHT_SURFACES_ENABLED",
        "WRIGHT_SURFACES_LIVE_APPS_ENABLED",
    ):
        assert startup_script.index(f"$env:{feature_flag}") < api_start


def test_runtime_identity_contains_hash_not_raw_challenge(monkeypatch) -> None:
    monkeypatch.setenv("WRIGHT_RUNTIME_CHALLENGE", "unlogged-secret")
    monkeypatch.setenv("WRIGHT_RUNTIME_ID", "runtime-1")
    monkeypatch.setenv("WRIGHT_RUNTIME_INSTANCE_ID", "instance-1")
    payload = runtime_identity_payload()
    assert payload["challenge_hash"] == hashlib.sha256(b"unlogged-secret").hexdigest()
    assert "unlogged-secret" not in json.dumps(payload)


def test_packaged_static_path_exists_and_missing_asset_fails(
    monkeypatch, tmp_path: Path
) -> None:
    assert (packaged_static_path() / "index.html").is_file()
    monkeypatch.setattr(server, "files", lambda _package: tmp_path)
    with pytest.raises(ServerBootstrapError, match="packaged_ui_missing"):
        packaged_static_path()


def test_prepare_and_identity_fail_closed_on_missing_inputs(
    monkeypatch, tmp_path: Path
) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    with pytest.raises(ServerBootstrapError, match="packaged_ui_missing"):
        prepare_runtime_environment(
            layout, static_path=tmp_path / "missing", environment={}
        )
    monkeypatch.delenv("WRIGHT_RUNTIME_CHALLENGE", raising=False)
    with pytest.raises(ServerBootstrapError, match="runtime_challenge_missing"):
        runtime_identity_payload()


def test_serve_enforces_data_containment_and_starts_uvicorn(
    monkeypatch, tmp_path: Path
) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text("<html>Wright</html>", encoding="utf-8")

    with pytest.raises(ServerBootstrapError, match="data_root_outside_layout"):
        server.serve(
            host="127.0.0.1",
            port=8765,
            data_root=tmp_path / "other",
            static_path=static,
        )

    calls = []
    monkeypatch.setattr(
        "uvicorn.run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    environment: dict[str, str] = {}
    monkeypatch.setattr(server.os, "environ", environment)
    server.serve(host="127.0.0.1", port=8765, data_root=layout.data, static_path=static)
    assert calls == [
        (
            ("api.main:app",),
            {"host": "127.0.0.1", "port": 8765, "log_config": None},
        )
    ]
    assert environment["WRIGHT_NATIVE_RUNTIME"] == "1"


def test_canonical_catalog_is_packaged_with_runtime_modules() -> None:
    assert (
        ROOT
        / "packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml"
    ).is_file()
    assert (
        ROOT / "packages/tool_registry/src/tool_registry/catalog/schema.json"
    ).is_file()
