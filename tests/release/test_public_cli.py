import json
from importlib.metadata import version

from wright_engineering import __version__
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
