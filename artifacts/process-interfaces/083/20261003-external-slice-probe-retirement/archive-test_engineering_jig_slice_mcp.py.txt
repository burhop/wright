from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(monkeypatch: pytest.MonkeyPatch, workspace: Path):
    monkeypatch.setenv("WRIGHT_JIG_WORKSPACE", str(workspace))
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "engineering_jig_slice_mcp_test", ROOT / "scripts/engineering_jig_slice_mcp.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _stage(workspace: Path, source: str, output: str) -> tuple[str, str]:
    inputs = workspace / "campaign/jig/attempt-001/inputs"
    inputs.mkdir(parents=True)
    operation_source = inputs / "engineering_dataset_slice.py"
    operation_source.write_bytes((ROOT / "scripts/engineering_dataset_slice.py").read_bytes())
    config = inputs / "slice-operation.json"
    config.write_text(
        json.dumps(
            {"workspace_root": str(workspace), "source": source, "output_root": output}
        ),
        encoding="utf-8",
    )
    return (
        config.relative_to(workspace).as_posix(),
        operation_source.relative_to(workspace).as_posix(),
    )


def test_accepts_only_same_attempt_jig_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load(monkeypatch, tmp_path)
    source = "campaign/jig/attempt-001/artifacts/jig.stl"
    output = "campaign/jig/attempt-001/artifacts/additive-manufacturing"
    (tmp_path / source).parent.mkdir(parents=True)
    (tmp_path / source).write_bytes(b"solid jig\n" + b"0" * 100)
    config, operation_source = _stage(tmp_path, source, output)
    assert module._configuration(config, operation_source).name == "slice-operation.json"


@pytest.mark.parametrize(
    ("source", "output"),
    [
        ("campaign/jig/attempt-002/artifacts/jig.stl", "campaign/jig/attempt-001/artifacts/additive-manufacturing"),
        ("campaign/jig/attempt-001/artifacts/repaired_mesh.stl", "campaign/jig/attempt-001/artifacts/additive-manufacturing"),
        ("campaign/jig/attempt-001/artifacts/jig.stl", "campaign/jig/attempt-001/artifacts"),
    ],
)
def test_rejects_cross_attempt_or_wrong_roles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str, output: str
) -> None:
    module = _load(monkeypatch, tmp_path)
    config, operation_source = _stage(tmp_path, source, output)
    with pytest.raises(ValueError):
        module._configuration(config, operation_source)
