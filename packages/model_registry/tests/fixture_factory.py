"""Deterministic no-weight engineering-model fixtures for lifecycle tests."""

from __future__ import annotations

import hashlib
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from model_registry import ModelPackage, canonical_digest, canonical_json


def _encoded(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class GeneratedModelFixture:
    root: Path
    archive_path: Path
    manifest_path: Path
    package: ModelPackage
    artifacts: dict[str, bytes]
    manifest_digest: str
    artifact_set_digest: str


def generate_affine_fixture(
    root: Path,
    *,
    revision: int = 1,
    scale: float = 2.0,
    offset: float = 1.0,
) -> GeneratedModelFixture:
    """Generate one deterministic affine package beneath a caller-owned temp root."""

    target = Path(root)
    if target.parent == target:
        raise ValueError("Fixture root cannot be a filesystem root")
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("Fixture root must be empty")
    target.mkdir(parents=True, exist_ok=True)

    input_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["x"],
        "properties": {"x": {"type": "number"}},
    }
    output_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["y"],
        "properties": {"y": {"type": "number"}},
    }
    test_input = {"x": 2.0}
    test_expected = {"y": scale * test_input["x"] + offset}
    artifacts = {
        "LICENSE": b"MIT License\n\nCopyright Wright Project contributors.\n",
        "model/coefficients.json": _encoded({"offset": offset, "scale": scale}),
        "tests/predict-two-input.json": _encoded(test_input),
        "tests/predict-two-expected.json": _encoded(test_expected),
    }
    declarations = [
        {
            "path": path,
            "role": (
                "license"
                if path == "LICENSE"
                else "model_data"
                if path.startswith("model/")
                else "test_input"
                if path.endswith("input.json")
                else "test_expected"
            ),
            "media_type": "text/plain"
            if path == "LICENSE"
            else "application/vnd.wright.affine+json"
            if path.startswith("model/")
            else "application/json",
            "size": len(value),
            "sha256": _sha256(value),
            "source_uri": f"wright://generated/affine-test/{path}",
            "redistributable": True,
        }
        for path, value in sorted(artifacts.items())
    ]
    total_bytes = sum(len(value) for value in artifacts.values())
    package = ModelPackage.model_validate(
        {
            "schema_version": "1.0",
            "model_id": "wright-affine-test",
            "package_revision": revision,
            "display_name": "Wright Affine Test Model",
            "description": "Generated deterministic fixture for safe lifecycle tests.",
            "publisher": {
                "name": "Wright Project",
                "source_uri": "https://github.com/burhop/wright",
            },
            "source": {
                "kind": "wright",
                "uri": "wright://generated/affine-test",
                "immutable_revision": f"fixture-revision-{revision}",
                "access": "public",
                "allowed_hosts": [],
            },
            "tasks": [
                {
                    "task_id": "predict",
                    "description": "Apply a deterministic affine transform.",
                    "input_schema": input_schema,
                    "output_schema": output_schema,
                    "units": {"x": "1", "y": "1"},
                }
            ],
            "license": {
                "expression": "MIT",
                "evidence": [
                    {
                        "kind": "artifact",
                        "location": "LICENSE",
                        "sha256": _sha256(artifacts["LICENSE"]),
                    }
                ],
                "attribution": "Copyright Wright Project contributors.",
                "redistribution": "allowed",
                "acceptance_required": False,
            },
            "limitations": [
                {
                    "limitation_id": "test-only",
                    "description": "Not a production engineering prediction model.",
                    "severity": "critical",
                }
            ],
            "remote_code_policy": "forbidden",
            "review_state": "approved",
            "variants": [
                {
                    "variant_id": "json-cpu-f64",
                    "format": "wright-affine-json",
                    "precision": "float64",
                    "platforms": [
                        "linux/x86_64",
                        "linux/aarch64",
                        "windows/x86_64",
                        "macos/aarch64",
                    ],
                    "accelerator": "cpu",
                    "runtime": {
                        "adapter_id": "wright-deterministic",
                        "contract_version": "1.0",
                        "version_specifier": "==1.0.0",
                    },
                    "resources": {
                        "download_bytes": total_bytes,
                        "installed_bytes": total_bytes,
                        "ram_bytes": 1_048_576,
                        "vram_bytes": 0,
                        "load_timeout_ms": 1_000,
                        "inference_timeout_ms": 1_000,
                        "max_output_bytes": 4_096,
                    },
                    "artifacts": declarations,
                    "test_vectors": [
                        {
                            "schema_version": "1.0",
                            "vector_id": "predict-two",
                            "version": 1,
                            "task_id": "predict",
                            "input_schema_sha256": canonical_digest(input_schema),
                            "output_schema_sha256": canonical_digest(output_schema),
                            "deterministic_seed": 0,
                            "units": {"x": "1", "y": "1"},
                            "input": test_input,
                            "expected": {"kind": "exact", "value": test_expected},
                            "limitations_exercised": ["test-only"],
                            "limits": {
                                "load_timeout_ms": 1_000,
                                "inference_timeout_ms": 1_000,
                                "max_output_bytes": 4_096,
                            },
                            "mandatory": True,
                        }
                    ],
                }
            ],
        }
    )
    manifest_bytes = _encoded(package.model_dump(mode="json", exclude_none=True))
    manifest_path = target / "engineering-model-package.json"
    manifest_path.write_bytes(manifest_bytes)
    for relative_path, value in artifacts.items():
        destination = target / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(value)

    archive_path = target / f"wright-affine-test-r{revision}.wright-model.zip"
    archive_entries = {
        **artifacts,
        "engineering-model-package.json": manifest_bytes,
    }
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for relative_path, value in sorted(archive_entries.items()):
            info = zipfile.ZipInfo(relative_path, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, value)

    artifact_set_digest = canonical_digest(
        [
            {"path": path, "sha256": _sha256(value), "size": len(value)}
            for path, value in sorted(artifacts.items())
        ]
    )
    return GeneratedModelFixture(
        root=target,
        archive_path=archive_path,
        manifest_path=manifest_path,
        package=package,
        artifacts=artifacts,
        manifest_digest=package.digest,
        artifact_set_digest=artifact_set_digest,
    )


__all__ = ["GeneratedModelFixture", "generate_affine_fixture"]
