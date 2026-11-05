"""Use the existing runtime selection; never install or select another harness."""

from types import SimpleNamespace

import pytest

from wright_engineering import desktop_launcher
from wright_engineering.manager_profiles import build_manager_profile, codex_mcp_config
from wright_engineering.runtime.models import RuntimeStatus


def test_desktop_profile_has_no_workspace_or_secret_and_preserves_direct_profile(
    tmp_path,
):
    config = codex_mcp_config(desktop=True, wright_home=tmp_path)
    assert config["args"] == ["mcp", "desktop", "--api-url", "http://127.0.0.1:8000"]
    assert config["env"]["WRIGHT_HOME"] == str(tmp_path)
    assert "TOKEN" not in repr(config)
    with pytest.raises(ValueError, match="explicit_workspace_selection"):
        codex_mcp_config(desktop=True, wright_home=tmp_path, workspace="elsewhere")
    with pytest.raises(ValueError, match="codex_stdio"):
        codex_mcp_config(desktop=True, transport="streamable-http")
    with pytest.raises(ValueError, match="codex_stdio"):
        build_manager_profile("hermes", desktop=True)


def test_manager_delegates_to_selected_private_runtime_without_shell(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("WRIGHT_HOME", str(tmp_path))
    layout = desktop_launcher.NativeLayout.discover()
    layout.ensure()
    layout.manifest.touch()
    environment = layout.runtimes / "qualified"
    python = desktop_launcher.RuntimeInstaller.environment_python(environment)
    python.parent.mkdir(parents=True)
    python.touch()
    runtime = SimpleNamespace(
        status=RuntimeStatus.ACTIVE, environment_path=str(environment)
    )
    monkeypatch.setattr(
        desktop_launcher.ManifestStore,
        "load",
        lambda *a, **kw: SimpleNamespace(
            active_runtime_id="qualified", runtimes={"qualified": runtime}
        ),
    )
    calls = []
    monkeypatch.setattr(
        desktop_launcher.subprocess, "call", lambda args: calls.append(args) or 7
    )
    assert desktop_launcher.serve_desktop("http://127.0.0.1:12345") == 7
    assert calls == [
        [
            str(python),
            "-I",
            "-m",
            "api.desktop.entrypoint",
            "--api-url",
            "http://127.0.0.1:12345",
            "--token-file",
            str(layout.control_plane_token),
        ]
    ]
    runtime.status = RuntimeStatus.STAGED
    assert desktop_launcher.serve_desktop("http://127.0.0.1:12345") == 1
    assert len(calls) == 1
    runtime.status = RuntimeStatus.ACTIVE
    runtime.environment_path = str(tmp_path.parent)
    with pytest.raises(ValueError):
        desktop_launcher.serve_desktop("http://127.0.0.1:12345")
    assert len(calls) == 1
