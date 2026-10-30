"""Versioned installed setup assets, shared with the existing example preparer.

Build mappings ship canonical authored files; no repository or test dataset is
required by an installed handle setup. The source-tree branch is developer-only.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
PACKAGE_PREFIX = "packages/workspace_service/src/workspace_service/"
HANDLE_PREFIX = "tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle/"


def source_resource(reference: str, *, repository: Path | None = None) -> Path:
    """Resolve retained provenance names to installed, independently shipped data."""
    if ".." in reference.replace("\\", "/").split("/") or Path(reference).is_absolute():
        raise ValueError("Invalid recipe resource path")
    if reference.startswith(PACKAGE_PREFIX):
        target = PACKAGE / reference.removeprefix(PACKAGE_PREFIX)
    elif reference.startswith(HANDLE_PREFIX):
        target = (
            PACKAGE
            / "engineering_workflow_templates/inputs/replacement-drawer-handle"
            / reference.removeprefix(HANDLE_PREFIX)
        )
    elif repository is not None:
        target = repository / reference  # Existing repository-only wheel examples.
    else:
        raise ValueError("Unsupported installed recipe resource")
    return target


def recipe_root() -> Path:
    installed = PACKAGE / "engineering_workflow_templates/setup_resources"
    if (installed / "definition.py").is_file():
        return installed
    checkout = PACKAGE.parents[3]
    if not (checkout / "pyproject.toml").is_file():
        raise ValueError(
            "The packaged handle setup recipe is unavailable; reinstall a complete distribution"
        )
    return checkout / "examples/process-interfaces"


def load_preparer():
    path = recipe_root() / "printed-replacement-part/prepare.py"
    spec = importlib.util.spec_from_file_location(
        "wright_packaged_handle_preparer", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract() -> dict:
    return json.loads(
        (
            recipe_root()
            / "printed-replacement-part/handle-geometry/setup-contract.json"
        ).read_bytes()
    )


def inventory() -> list[dict]:
    mapping = json.loads((PACKAGE / "handle_setup_resources.json").read_bytes())
    records = []
    for item in mapping["files"]:
        path = recipe_root() / item["target"]
        raw = path.read_bytes()
        records.append(
            {
                "resource": item["target"],
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
                "license": item["license"],
            }
        )
    for relative in (
        "handle_setup.py",
        "handle_setup_resources.py",
        "handle_setup_resources.json",
        "engineering_workflow_templates/templates/printed-replacement-part.workflow.wflow",
        "process_validation/profiles/coverage.json",
        "process_validation/profiles/printed-replacement-part-02.json",
        "process_validation/readers/three_mf_geometry.py",
        "process_interfaces/representations.py",
    ):
        raw = (PACKAGE / relative).read_bytes()
        records.append(
            {
                "resource": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
                "license": "MIT",
            }
        )
    inputs = PACKAGE / "engineering_workflow_templates/inputs/replacement-drawer-handle"
    rights = json.loads((inputs / "rights.json").read_bytes())
    for name, expected in rights["files"].items():
        raw = (inputs / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected:
            raise ValueError("Packaged starter input differs from its rights inventory")
        records.append(
            {
                "resource": "inputs/" + name,
                "sha256": digest,
                "size_bytes": len(raw),
                "license": rights["license"],
            }
        )
    return records


def recipe_identity() -> dict:
    value = contract()
    data = json.dumps(inventory(), sort_keys=True, separators=(",", ":")).encode()
    return {
        "id": value["id"],
        "version": value["version"],
        "digest": hashlib.sha256(data).hexdigest(),
    }
