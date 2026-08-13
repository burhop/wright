from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
PRIVATE_SUFFIXES = {
    ".joblib",
    ".pickle",
    ".pkl",
    ".npz",
    ".wright-model.zip",
}


def _tracked() -> tuple[str, ...]:
    raw = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True
    ).stdout.decode("utf-8")
    return tuple(item for item in raw.split("\0") if item)


def test_git_and_container_inputs_exclude_private_chatter_payloads() -> None:
    tracked = _tracked()
    offending = []
    for name in tracked:
        path = PurePosixPath(name.lower())
        if path.name.endswith(".wright-model.zip") or path.suffix in PRIVATE_SUFFIXES:
            offending.append(name)
    assert offending == []
    assert not any(
        part in {".local-run", ".chatter-qualification"}
        for name in tracked
        for part in PurePosixPath(name).parts
    )


def test_distribution_metadata_contains_contracts_but_no_payload_signature() -> None:
    package_root = ROOT / "packages/model_registry/src/model_registry"
    assert (package_root / "chatter_contracts.py").is_file()
    assert (package_root / "chatter_runtime.py").is_file()
    assert (package_root / "catalog/generated-chatter-package.json").is_file()
    for dockerfile in ROOT.glob("docker/**/Dockerfile*"):
        text = dockerfile.read_text(encoding="utf-8", errors="ignore").lower()
        assert ".wright-model.zip" not in text
        assert "dataset2" not in text
