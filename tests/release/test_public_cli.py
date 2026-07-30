import json
from importlib.metadata import version
from types import SimpleNamespace

import pytest

from wright_engineering import __version__
from wright_engineering.appliance import ApplianceError
from wright_engineering.cli import main


def test_version_and_doctor_are_dependency_safe(capsys) -> None:
    assert __version__ == version("wright-engineering")
    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "python" in output
    assert "api-token" in output


def test_config_dry_run_masks_token(monkeypatch, capsys) -> None:
    monkeypatch.setenv("WRIGHT_API_TOKEN", "never-print-this")
    assert main(["config", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "never-print-this" not in output
    assert json.loads(output)["token_status"] == "set"


def test_mcp_cli_forwards_explicit_workspace_identity(monkeypatch, tmp_path) -> None:
    captured = {}

    def fake_serve_stdio(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr("wright_engineering.cli.serve_stdio", fake_serve_stdio)
    assert (
        main(
            [
                "mcp",
                "serve",
                "--stdio",
                "--workspace",
                str(tmp_path),
                "--workspace-id",
                "workspace-123",
            ]
        )
        == 0
    )
    assert captured["workspace"] == tmp_path
    assert captured["workspace_id"] == "workspace-123"


def test_no_command_reports_both_supported_distribution_paths(capsys) -> None:
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "Hermes Git plugin" in output
    assert "Codex uses direct MCP" in output
    assert "burhop/wright" in output
    assert "ghcr.io/burhop/wright" in output


def test_strict_doctor_fails_a_required_diagnostic(monkeypatch, capsys) -> None:
    diagnostics = [
        SimpleNamespace(ok=False, name="python", detail="unsupported"),
        SimpleNamespace(ok=False, name="api-token", detail="optional"),
    ]
    monkeypatch.setattr("wright_engineering.cli.run_diagnostics", lambda: diagnostics)
    assert main(["doctor", "--strict"]) == 1
    assert "WARN python: unsupported" in capsys.readouterr().out


def test_appliance_status_cli_reports_success_and_bounded_failure(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(
        "wright_engineering.cli.appliance_status", lambda _url: {"status": "ok"}
    )
    assert main(["appliance", "status"]) == 0
    assert json.loads(capsys.readouterr().out) == {"status": "ok"}

    def unavailable(_url):
        raise ApplianceError("appliance status unavailable: TimeoutError")

    monkeypatch.setattr("wright_engineering.cli.appliance_status", unavailable)
    assert main(["appliance", "status"]) == 1
    assert "TimeoutError" in capsys.readouterr().out


class _LifecycleResult:
    def __init__(self, *, ok: bool, command: str) -> None:
        self.ok = ok
        self.command = command

    def to_dict(self):
        return {"ok": self.ok, "command": self.command}


class _FakeLifecycle:
    def status(self):
        return _LifecycleResult(ok=True, command="status")

    def update(self, version):
        assert version == "0.1.9"
        return _LifecycleResult(ok=False, command="update")


@pytest.mark.parametrize(
    ("arguments", "expected_code", "expected_command"),
    [
        (["native", "status"], 0, "status"),
        (["native", "update", "0.1.9"], 1, "update"),
    ],
)
def test_native_cli_dispatches_no_argument_and_versioned_commands(
    monkeypatch, capsys, arguments, expected_code, expected_command
) -> None:
    monkeypatch.setattr(
        "wright_engineering.runtime.lifecycle.NativeLifecycle.default",
        lambda: _FakeLifecycle(),
    )
    assert main(arguments) == expected_code
    assert json.loads(capsys.readouterr().out)["command"] == expected_command


def test_native_cli_rejects_missing_handler(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "wright_engineering.runtime.lifecycle.NativeLifecycle.default",
        lambda: object(),
    )
    assert main(["native", "start"]) == 2
    assert "not implemented" in capsys.readouterr().out


def test_runtime_cli_forwards_contained_server_arguments(monkeypatch, tmp_path) -> None:
    captured = {}

    def fake_serve(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("wright_engineering.runtime.server.serve", fake_serve)
    assert (
        main(
            [
                "runtime",
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
                "--data-root",
                str(tmp_path),
            ]
        )
        == 0
    )
    assert captured == {"host": "127.0.0.1", "port": 8765, "data_root": tmp_path}
