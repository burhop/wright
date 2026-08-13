from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from model_registry import ModelCatalog, canonical_json


ROOT = Path(__file__).resolve().parents[2]
MODEL_PAYLOAD_SUFFIXES = {
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
SOURCE_OR_EXECUTABLE_SUFFIXES = {
    ".bat",
    ".cmd",
    ".dll",
    ".dylib",
    ".exe",
    ".js",
    ".msi",
    ".ps1",
    ".py",
    ".sh",
    ".so",
    ".whl",
}
SECRET = re.compile(
    r"(?i)(?:api[_-]?key|authorization|cookie|credential|password|secret|token)\s*[:=]"
)
RAW_PATH = re.compile(r"(?i)(?:[a-z]:\\|/home/|/users/|\\\\[^\\]+\\)")
ACTUATION = re.compile(
    r"(?i)(?:command|control|drive|extrude|heat|move|spin).{0,20}(?:axis|extruder|heater|machine|motor|plc|printer|robot|spindle)"
)


def _walk(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk(child)


def _approved_packages():
    return tuple(
        entry.package
        for entry in ModelCatalog.load_bundled().entries
        if entry.package is not None and entry.package.review_state == "approved"
    )


def test_git_distribution_contains_no_model_payload_bytes() -> None:
    tracked = (
        subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        .stdout.decode("utf-8")
        .split("\0")
    )
    payloads = [
        path
        for path in tracked
        if path and PurePosixPath(path).suffix.lower() in MODEL_PAYLOAD_SUFFIXES
    ]
    assert payloads == []
    assert not any(path.startswith(".local-run/") for path in tracked)


def test_approved_packages_declare_data_only_artifacts() -> None:
    packages = _approved_packages()
    assert {package.model_id for package in packages} >= {
        "wright-affine-test",
        "neuralfoil-medium",
    }
    for package in packages:
        for variant in package.variants:
            for artifact in variant.artifacts:
                suffix = PurePosixPath(artifact.path).suffix.lower()
                assert suffix not in SOURCE_OR_EXECUTABLE_SUFFIXES
                assert "training/" not in artifact.path.lower()
                assert "checkpoint" not in artifact.path.lower()
                assert artifact.role in {
                    "model_data",
                    "metadata",
                    "license",
                    "attribution",
                    "test_input",
                    "test_expected",
                }


def test_public_package_documents_exclude_secrets_paths_commands_and_actuation() -> (
    None
):
    forbidden_keys = {
        "command",
        "endpoint",
        "host_path",
        "process_handle",
        "runtime_command",
    }
    for package in _approved_packages():
        document = package.model_dump(mode="json", exclude_none=True)
        serialized = canonical_json(document)
        assert SECRET.search(serialized) is None
        assert RAW_PATH.search(serialized) is None
        assert ACTUATION.search(serialized) is None
        assert not forbidden_keys.intersection(key for key, _ in _walk(document))
        assert package.remote_code_policy == "forbidden"
        assert all(
            not ACTUATION.search(task.task_id + " " + task.description)
            for task in package.tasks
        )


def test_blocked_unsafe_candidates_never_gain_approved_package_payloads() -> None:
    catalog = ModelCatalog.load_bundled()
    pointnet = catalog.get("keras-io-pointnet")
    remote_code = catalog.get("blocked-remote-code-model")
    assert pointnet.package is None
    assert pointnet.document["readiness"] == "needs_review"
    assert remote_code.package is None
    assert remote_code.document["readiness"] == "blocked"
    assert any(
        blocker["category"] in {"unsafe_format", "remote_code_required"}
        for entry in (pointnet, remote_code)
        for blocker in entry.document["blockers"]
    )
