from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pytest


def _module():
    root = Path(__file__).resolve().parents[2]
    path = root / "scripts" / "qualification" / "qualify-chatter-model.py"
    spec = importlib.util.spec_from_file_location("qualify_chatter_model", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _arguments(tmp_path, *, acknowledgement="I-UNDERSTAND-NO-REDISTRIBUTION"):
    source = tmp_path / "source"
    data_vault = tmp_path / "data-vault"
    dataset = tmp_path / "dataset.parquet"
    evidence = tmp_path / "evidence.json"
    environment_lock = tmp_path / "uv.lock"
    source.mkdir(exist_ok=True)
    (data_vault / "src" / "pipeline").mkdir(parents=True, exist_ok=True)
    (data_vault / "src" / "pipeline" / "ml_pipeline.py").write_text(
        "CHATTER_PROCESS_FEATURES = ()\n", encoding="utf-8"
    )
    dataset.write_bytes(b"fixture")
    evidence.write_text("{}", encoding="utf-8")
    environment_lock.write_text("version = 1\n", encoding="utf-8")
    return argparse.Namespace(
        source=source,
        data_vault_source=data_vault,
        dataset=dataset,
        reference_evidence=evidence,
        environment_lock=environment_lock,
        output=tmp_path / "qualified-output",
        acknowledge_internal_only=acknowledgement,
    )


def test_qualification_requires_exact_internal_only_acknowledgement(tmp_path) -> None:
    module = _module()
    arguments = _arguments(tmp_path, acknowledgement="yes")
    with pytest.raises(module.QualificationError, match="acknowledgement"):
        module.preflight(arguments, tmp_path / "repository")


def test_qualification_output_must_stay_outside_repository(tmp_path) -> None:
    module = _module()
    repository = tmp_path / "repository"
    repository.mkdir()
    arguments = _arguments(tmp_path)
    arguments.output = repository / "private-serving-output"
    with pytest.raises(module.QualificationError, match="outside"):
        module.preflight(arguments, repository)


def test_qualification_rejects_changed_source_before_dataset_use(
    tmp_path, monkeypatch
) -> None:
    module = _module()
    arguments = _arguments(tmp_path)
    monkeypatch.setattr(module, "_git", lambda *_values: "changed-revision")
    with pytest.raises(module.QualificationError, match="revision changed"):
        module.preflight(arguments, tmp_path / "repository")


def test_qualification_source_contains_no_unsafe_training_artifact_loader() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (
        root / "scripts" / "qualification" / "qualify-chatter-model.py"
    ).read_text(encoding="utf-8")
    assert "joblib.load" not in source.lower()
    assert "pickle.load" not in source.lower()
    assert "allow_pickle=True" not in source
