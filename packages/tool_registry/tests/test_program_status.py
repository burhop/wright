from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from tool_registry.program_status import (
    MAX_PROGRAM_STATUS_BYTES,
    ProgramStatusErrorCode,
    ProgramStatusReadError,
    ProgramStatusReader,
)


FULL_CONTRACT_ROOT = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "wright_engineering"
    / "static"
    / "program-status"
)


def canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def rehash(value: dict[str, object]) -> None:
    value["bundle_id"] = digest(
        {
            "source": value["source"],
            "dashboard": value["dashboard"],
            "supplement": value["supplement"],
        }
    )


def write_contracts(root: Path) -> None:
    dashboard_id = "https://wright.local/programs/epp/dashboard-v2.schema.json"
    dashboard_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": dashboard_id,
        "type": "object",
    }
    publisher = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "state",
            "mode",
            "observed_commit",
            "last_attempt_at",
            "last_success_at",
            "failure_code",
            "recovery",
        ],
        "properties": {
            "state": {"enum": ["active", "inactive", "failed", "unavailable"]},
            "mode": {"enum": ["committed_watch", "package_install", "manual"]},
            "observed_commit": {
                "oneOf": [
                    {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                    {"type": "null"},
                ]
            },
            "last_attempt_at": {"type": ["string", "null"]},
            "last_success_at": {"type": ["string", "null"]},
            "failure_code": {"type": ["string", "null"]},
            "recovery": {"type": ["string", "null"]},
        },
    }
    bundle_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "schema_version",
            "bundle_id",
            "generated_at",
            "source",
            "dashboard",
            "supplement",
        ],
        "properties": {
            "schema_version": {"const": "1.0.0"},
            "bundle_id": {"type": "string"},
            "generated_at": {"type": "string"},
            "source": {"type": "object"},
            "dashboard": {"$ref": dashboard_id},
            "supplement": {"type": "object"},
        },
        "$defs": {"publisher": publisher},
    }
    root.mkdir(parents=True)
    (root / "dashboard.schema.json").write_bytes(canonical(dashboard_schema))
    (root / "program-status-bundle.schema.json").write_bytes(canonical(bundle_schema))


def valid_bundle() -> dict[str, object]:
    dashboard = {"readiness": "unchanged", "benchmark": {"qualified": 0}}
    source = {
        "commit": "a" * 40,
        "dashboard_canonical_sha256": digest(dashboard),
        "snapshot_path": "docs/programs/engineering-process-platform/dashboard.json",
        "snapshot_raw_sha256": "b" * 64,
        "raw_identity_evidence": {
            "path": "docs/programs/engineering-process-platform/dashboard.json",
            "sha256": "b" * 64,
        },
    }
    supplement = {"work": {"tasks": 0}}
    value: dict[str, object] = {
        "schema_version": "1.0.0",
        "bundle_id": digest(
            {"source": source, "dashboard": dashboard, "supplement": supplement}
        ),
        "generated_at": "2026-08-29T02:02:46Z",
        "source": source,
        "dashboard": dashboard,
        "supplement": supplement,
    }
    return value


def roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    installed = tmp_path / "installed"
    packaged = tmp_path / "packaged"
    schemas = tmp_path / "schemas"
    installed.mkdir()
    packaged.mkdir()
    write_contracts(schemas)
    return installed, packaged, schemas


def test_reads_installed_valid_bundle_as_one_immutable_identity(tmp_path: Path) -> None:
    installed, packaged, schemas = roots(tmp_path)
    value = valid_bundle()
    (installed / "current.json").write_bytes(canonical(value))

    result = ProgramStatusReader(installed, packaged, schema_root=schemas).read_bundle()

    assert result.bundle_id == value["bundle_id"]
    assert result.source_kind == "installed"
    first = result.as_dict()
    first["dashboard"] = {}
    assert result.as_dict()["dashboard"] == value["dashboard"]


def test_fallback_is_used_only_when_installed_bundle_is_absent(tmp_path: Path) -> None:
    installed, packaged, schemas = roots(tmp_path)
    (packaged / "current.json").write_bytes(canonical(valid_bundle()))
    reader = ProgramStatusReader(installed, packaged, schema_root=schemas)

    assert reader.read_bundle().source_kind == "packaged_fallback"

    (installed / "current.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(ProgramStatusReadError) as raised:
        reader.read_bundle()
    assert raised.value.code is ProgramStatusErrorCode.INVALID


def test_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    installed, packaged, schemas = roots(tmp_path)
    value = valid_bundle()
    value["bundle_id"] = "0" * 64
    (installed / "current.json").write_bytes(canonical(value))

    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(installed, packaged, schema_root=schemas).read_bundle()

    assert raised.value.code is ProgramStatusErrorCode.IDENTITY_MISMATCH


def test_bounded_read_rejects_oversized_installed_data(tmp_path: Path) -> None:
    installed, packaged, schemas = roots(tmp_path)
    (installed / "current.json").write_bytes(b" " * (MAX_PROGRAM_STATUS_BYTES + 1))

    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(installed, packaged, schema_root=schemas).read_bundle()

    assert raised.value.code is ProgramStatusErrorCode.INVALID


def test_publisher_state_is_validated_separately(tmp_path: Path) -> None:
    installed, packaged, schemas = roots(tmp_path)
    state = {
        "state": "active",
        "mode": "manual",
        "observed_commit": "a" * 40,
        "last_attempt_at": "2026-08-29T02:02:46Z",
        "last_success_at": "2026-08-29T02:02:46Z",
        "failure_code": None,
        "recovery": None,
    }
    (installed / "publisher.json").write_bytes(canonical(state))

    result = ProgramStatusReader(
        installed, packaged, schema_root=schemas
    ).read_publisher()

    assert result.as_dict() == state


def test_full_contract_rejects_false_source_catalog_identity(tmp_path: Path) -> None:
    installed = tmp_path / "installed"
    installed.mkdir()
    value = json.loads((FULL_CONTRACT_ROOT / "current.json").read_bytes())
    value["source"]["source_catalog_sha256"] = "0" * 64
    rehash(value)
    (installed / "current.json").write_bytes(canonical(value))

    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(
            installed, FULL_CONTRACT_ROOT, schema_root=FULL_CONTRACT_ROOT
        ).read_bundle()

    assert raised.value.code is ProgramStatusErrorCode.IDENTITY_MISMATCH


def test_full_contract_rejects_self_hashed_false_task_arithmetic(
    tmp_path: Path,
) -> None:
    installed = tmp_path / "installed"
    installed.mkdir()
    value = json.loads((FULL_CONTRACT_ROOT / "current.json").read_bytes())
    value["supplement"]["work"]["tasks"]["remaining"] += 1
    rehash(value)
    (installed / "current.json").write_bytes(canonical(value))

    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(
            installed, FULL_CONTRACT_ROOT, schema_root=FULL_CONTRACT_ROOT
        ).read_bundle()

    assert raised.value.code is ProgramStatusErrorCode.INVALID


def test_full_contract_rejects_tampered_packaged_catalog(tmp_path: Path) -> None:
    installed = tmp_path / "installed"
    contracts = tmp_path / "contracts"
    installed.mkdir()
    shutil.copytree(FULL_CONTRACT_ROOT, contracts)
    (installed / "current.json").write_bytes(
        (FULL_CONTRACT_ROOT / "current.json").read_bytes()
    )
    catalog = contracts / "program-status-source-catalog.json"
    catalog.write_bytes(catalog.read_bytes() + b"\n")

    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(installed, contracts, schema_root=contracts).read_bundle()

    assert raised.value.code is ProgramStatusErrorCode.IDENTITY_MISMATCH
