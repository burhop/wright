from __future__ import annotations

import json

from wright_engineering.cli import main


def test_model_catalog_validation_is_static_and_reports_bounded_json(
    monkeypatch, tmp_path, capsys
) -> None:
    package = tmp_path / "package.json"
    package.write_text((tmp_path.parent / "missing").as_posix(), encoding="utf-8")
    monkeypatch.setattr(
        "subprocess.Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("validation started a process")
        ),
    )
    assert main(["models", "validate-catalog", str(package)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["passed"] is False
    assert result["findings"][0]["category"] == "manifest_invalid"
    assert "traceback" not in result


def test_model_adapter_validation_never_starts_the_declared_command(
    monkeypatch, tmp_path, capsys
) -> None:
    descriptor = tmp_path / "adapter.json"
    descriptor.write_text(
        json.dumps(
            {
                "adapter_id": "test-adapter",
                "adapter_version": "1.0.0",
                "contract_version": "1.0",
                "command": ["never-run"],
                "formats": ["onnx"],
                "tasks": ["predict"],
                "platforms": ["windows"],
                "architectures": ["x86_64"],
                "execution_providers": ["cpu"],
                "maximum_control_bytes": 65536,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "subprocess.Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("validation started a process")
        ),
    )
    assert main(["models", "validate-adapter", str(descriptor)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["passed"] is True
    assert result["identity"] == "test-adapter@1.0.0"
    assert "command" not in result
