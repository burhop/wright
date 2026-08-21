from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import tomllib

import model_registry


SCHEMA_NAMES = (
    "model-package.schema.json",
    "model-test-vector.schema.json",
    "model-install-plan.schema.json",
    "model-operation.schema.json",
)
CHATTER_SCHEMA_NAMES = (
    "chatter-candidate-batch.schema.json",
    "chatter-result-batch.schema.json",
    "chatter-serving-metadata.schema.json",
    "conversion-parity-evidence.schema.json",
)


def test_public_schemas_are_package_resources() -> None:
    root = model_registry.schema_root()
    assert root == files("model_registry.schemas")
    assert {item.name for item in root.iterdir()} >= set(
        SCHEMA_NAMES + CHATTER_SCHEMA_NAMES
    )


def test_packaged_schemas_match_feature_contracts() -> None:
    repository = Path(__file__).resolve().parents[3]
    source = repository / "specs" / "071-local-engineering-model-library" / "contracts"
    packaged = model_registry.schema_root()
    for name in SCHEMA_NAMES:
        assert packaged.joinpath(name).read_bytes() == (source / name).read_bytes()


def test_packaged_chatter_schemas_match_feature_contracts() -> None:
    repository = Path(__file__).resolve().parents[3]
    source = repository / "specs" / "072-chatter-rivet-scenarios" / "contracts"
    packaged = model_registry.schema_root()
    for name in CHATTER_SCHEMA_NAMES:
        assert packaged.joinpath(name).read_bytes() == (source / name).read_bytes()


def test_package_has_no_model_runtime_or_hub_dependency() -> None:
    package = Path(__file__).resolve().parents[1]
    project = tomllib.loads((package / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    dependencies = "\n".join(project["dependencies"]).lower()
    for forbidden in (
        "tensorflow",
        "torch",
        "cuda",
        "onnxruntime",
        "huggingface_hub",
        "transformers",
    ):
        assert forbidden not in dependencies
