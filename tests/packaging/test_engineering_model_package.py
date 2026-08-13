from __future__ import annotations

import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
PAYLOAD_SUFFIXES = {
    ".h5",
    ".joblib",
    ".keras",
    ".onnx",
    ".npz",
    ".pb",
    ".pickle",
    ".pkl",
    ".pt",
    ".pth",
    ".safetensors",
}
REQUIRED_RUNTIME_RESOURCES = {
    "model_registry/affine_runtime.py",
    "model_registry/neuralfoil_runtime.py",
    "model_registry/catalog/catalog.yaml",
    "model_registry/catalog/generated-affine-package.json",
    "model_registry/catalog/neuralfoil-medium-package.json",
    "model_registry/schemas/model-package.schema.json",
    "model_registry/schemas/model-install-plan.schema.json",
    "model_registry/schemas/model-operation.schema.json",
    "model_registry/schemas/model-test-vector.schema.json",
}


def test_wheel_and_sdist_ship_model_contracts_without_model_payloads(tmp_path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--sdist",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    sdist = next(tmp_path.glob("*.tar.gz"))
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
        metadata_name = next(
            name for name in wheel_names if name.endswith(".dist-info/METADATA")
        )
        metadata = archive.read(metadata_name).decode("utf-8")
    with tarfile.open(sdist, "r:gz") as archive:
        sdist_names = {PurePosixPath(name) for name in archive.getnames()}

    assert REQUIRED_RUNTIME_RESOURCES <= wheel_names
    assert "Provides-Extra: engineering-models" in metadata
    assert "numpy" in metadata and "extra == 'engineering-models'" in metadata
    assert not any(
        PurePosixPath(name).suffix.lower() in PAYLOAD_SUFFIXES for name in wheel_names
    )
    assert not any(path.suffix.lower() in PAYLOAD_SUFFIXES for path in sdist_names)
    assert not any(".local-run" in path.parts for path in sdist_names)
    assert any(path.name == "neuralfoil-medium-package.json" for path in sdist_names)
    assert (ROOT / "docs/models/local-engineering-models.md").is_file()
    assert (
        ROOT / "docs/model-evidence/external-model-validation-2026-08-13.md"
    ).is_file()

    model_project = tomllib.loads(
        (ROOT / "packages/model_registry/pyproject.toml").read_text(encoding="utf-8")
    )
    assert model_project["project"]["optional-dependencies"]["neuralfoil"] == [
        "numpy>=1.26,<3"
    ]
