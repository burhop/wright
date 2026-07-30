from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "specs" / "053-workspace-surfaces" / "contracts"
PACKAGED = ROOT / "packages" / "core" / "src" / "core" / "surfaces" / "schemas"


def test_versioned_contract_package_is_byte_for_byte_in_sync() -> None:
    manifest = json.loads((PACKAGED / "contract-set.json").read_text(encoding="utf-8"))
    assert manifest["contractVersion"] == 1
    assert manifest["source"] == "specs/053-workspace-surfaces/contracts"

    packaged_names = {
        path.name for path in (PACKAGED / "v1").iterdir() if path.is_file()
    }
    assert packaged_names == set(manifest["files"])
    for name, expected_hash in manifest["files"].items():
        source_bytes = (SOURCE / name).read_bytes()
        packaged_bytes = (PACKAGED / "v1" / name).read_bytes()
        assert packaged_bytes == source_bytes, name
        assert hashlib.sha256(packaged_bytes).hexdigest() == expected_hash, name


def test_json_contracts_are_valid_json_and_openapi_is_versioned() -> None:
    for path in sorted((PACKAGED / "v1").glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(document, dict)
    openapi = (PACKAGED / "v1" / "workspace-surfaces.openapi.yaml").read_text(
        encoding="utf-8"
    )
    assert openapi.startswith("openapi: 3.")
