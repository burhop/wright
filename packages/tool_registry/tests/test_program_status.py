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


def test_full_contract_recomputes_canonical_test_checkpoint(tmp_path: Path) -> None:
    installed = tmp_path / "installed"
    installed.mkdir()
    value = json.loads((FULL_CONTRACT_ROOT / "current.json").read_bytes())
    test_ids = ["tests/a.py::test_x", "tests/a.py::test_y[param]"]
    counts = {"total": 2, "passed": 2, "failed": 0, "skipped": 0, "not_run": 0}
    reference = {
        "id": "test:unit-attempt-1:1",
        "path": "test-results/program-status/unit.json",
        "sha256": "9" * 64,
    }
    source = {
        "suite_id": "unit-suite",
        "population_id": "pkg",
        "run_id": "unit-attempt-1",
        "run_key": "dddb7540d46b1f8e83791141ac94b5f0bc38effee28f32baa36c6fc5be96ad5f",
        "attempt": 1,
        "observed_at": "2026-08-29T14:00:00Z",
        "terminal": True,
        "aggregate_role": "component",
        "category": "unit",
        "test_case_ids": test_ids,
        "test_case_set_sha256": "c4e6eafe639dc63fa01d5d2b41d04e105847a75f97c669fc3c0087c94376a1b7",
        "counts": counts,
        "evidence": [reference],
    }
    history = value["supplement"]["test_history"]
    history["availability"] = "available"
    history["unavailable_reason"] = None
    history["selection_attestation"]["selected_run_ids"] = ["unit-attempt-1"]
    history["checkpoints"] = [
        {
            "commit": "a" * 40,
            "observed_at": "2026-08-29T14:00:00Z",
            "counts": counts,
            "pass_rate": 1,
            "categories": {
                "unit": counts,
                "integration": None,
                "e2e": None,
                "benchmark": None,
            },
            "suite_sources": [source],
        }
    ]
    value["supplement"]["evidence_index"].append(
        {
            **reference,
            "label": "Unit run",
            "summary": "Canonical test fixture.",
            "freshness": "current",
            "recovery": None,
            "availability": "identity_only",
            "exact_url": None,
        }
    )
    rehash(value)
    (installed / "current.json").write_bytes(canonical(value))

    ProgramStatusReader(
        installed, FULL_CONTRACT_ROOT, schema_root=FULL_CONTRACT_ROOT
    ).read_bundle()

    source["test_case_set_sha256"] = "0" * 64
    rehash(value)
    (installed / "current.json").write_bytes(canonical(value))
    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(
            installed, FULL_CONTRACT_ROOT, schema_root=FULL_CONTRACT_ROOT
        ).read_bundle()
    assert raised.value.code is ProgramStatusErrorCode.INVALID


def test_full_contract_rejects_test_result_detail_outside_test_suite_source(
    tmp_path: Path,
) -> None:
    installed = tmp_path / "installed"
    installed.mkdir()
    value = json.loads((FULL_CONTRACT_ROOT / "current.json").read_bytes())
    value["supplement"]["evidence_index"].append(
        {
            "id": "orphan-test-result",
            "path": "test-results/program-status/orphan.json",
            "sha256": "8" * 64,
            "label": "Orphan test result",
            "summary": "Must be bound to one selected suite source.",
            "freshness": "current",
            "recovery": None,
            "availability": "identity_only",
            "exact_url": None,
        }
    )
    rehash(value)
    (installed / "current.json").write_bytes(canonical(value))

    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(
            installed, FULL_CONTRACT_ROOT, schema_root=FULL_CONTRACT_ROOT
        ).read_bundle()

    assert raised.value.code is ProgramStatusErrorCode.INVALID


def test_full_contract_rejects_test_result_path_on_non_test_reference(
    tmp_path: Path,
) -> None:
    installed = tmp_path / "installed"
    installed.mkdir()
    value = json.loads((FULL_CONTRACT_ROOT / "current.json").read_bytes())
    reference = value["supplement"]["work"]["current_next_action"]["evidence"][0]
    detail = next(
        item
        for item in value["supplement"]["evidence_index"]
        if item["id"] == reference["id"]
    )
    reference["path"] = "test-results/program-status/not-an-action-source.json"
    detail["path"] = reference["path"]
    rehash(value)
    (installed / "current.json").write_bytes(canonical(value))

    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(
            installed, FULL_CONTRACT_ROOT, schema_root=FULL_CONTRACT_ROOT
        ).read_bundle()

    assert raised.value.code is ProgramStatusErrorCode.INVALID


def test_full_contract_recomputes_nonempty_orthogonal_use_case_funnels(
    tmp_path: Path,
) -> None:
    installed = tmp_path / "installed"
    installed.mkdir()
    value = json.loads((FULL_CONTRACT_ROOT / "current.json").read_bytes())
    acceptance_ref = {
        "id": "use-case-acceptance",
        "path": "docs/programs/engineering-process-platform/gate-evidence.json",
        "sha256": "6" * 64,
    }
    verification_ref = {
        "id": "use-case-verification",
        "path": "docs/programs/engineering-process-platform/evidence/verification/EPP-F01-V9.json",
        "sha256": "7" * 64,
    }
    item = {
        "id": "EPP-UC-001",
        "title": "Inspect status",
        "customer_outcome": "A customer can inspect evidence-backed status.",
        "process_100_id": "EPP-PROC-001",
        "definition_evidence": [],
        "progress_evidence": [],
        "acceptance_evidence": [
            {
                "evidence_class": "customer_acceptance",
                "source_name": "gate_evidence",
                "subject_id": "ACC-001",
                "verdict": "passed",
                "acceptance_subject_id": None,
                "evidence_author": "customer-reviewer",
                "independent_verifier": None,
                "evidence": acceptance_ref,
            }
        ],
        "test_evidence": [],
        "independent_verification_evidence": [
            {
                "evidence_class": "independent_verification",
                "source_name": "verification_evidence",
                "subject_id": "VER-001",
                "verdict": "passed",
                "acceptance_subject_id": "ACC-001",
                "evidence_author": "implementation-agent",
                "independent_verifier": "independent-reviewer",
                "evidence": verification_ref,
            }
        ],
        "benchmark_qualification_evidence": [],
    }
    use_cases = value["supplement"]["use_cases"]
    use_cases["items"] = [item]
    use_cases["all"] = {
        "total": 1,
        "not_started": 0,
        "in_progress": 0,
        "implemented": 1,
        "independently_verified": 1,
        "remaining": 0,
    }
    use_cases["process_100"] = {
        "population_target": 100,
        "defined": 0,
        "in_progress": 0,
        "implemented": 1,
        "tested": 0,
        "independently_verified": 1,
        "benchmark_qualified": 0,
    }
    for reference, label in (
        (acceptance_ref, "Acceptance"),
        (verification_ref, "Independent verification"),
    ):
        value["supplement"]["evidence_index"].append(
            {
                **reference,
                "label": label,
                "summary": f"Exact {label.lower()} evidence.",
                "freshness": "current",
                "recovery": None,
                "availability": "identity_only",
                "exact_url": None,
            }
        )
    rehash(value)
    (installed / "current.json").write_bytes(canonical(value))

    ProgramStatusReader(
        installed, FULL_CONTRACT_ROOT, schema_root=FULL_CONTRACT_ROOT
    ).read_bundle()

    item["independent_verification_evidence"][0]["independent_verifier"] = (
        "implementation-agent"
    )
    rehash(value)
    (installed / "current.json").write_bytes(canonical(value))
    with pytest.raises(ProgramStatusReadError) as raised:
        ProgramStatusReader(
            installed, FULL_CONTRACT_ROOT, schema_root=FULL_CONTRACT_ROOT
        ).read_bundle()
    assert raised.value.code is ProgramStatusErrorCode.INVALID


def test_runtime_requires_reciprocal_correction_finding_verification_graph() -> None:
    value = json.loads((FULL_CONTRACT_ROOT / "current.json").read_bytes())
    reference = {
        "id": "correction-profile",
        "path": "docs/programs/engineering-process-platform/evidence/corrections/COR-001.json",
        "sha256": "5" * 64,
    }
    value["supplement"]["evidence_index"].append(
        {
            **reference,
            "label": "Correction profile",
            "summary": "Exact bounded correction profile.",
            "freshness": "current",
            "recovery": None,
            "availability": "identity_only",
            "exact_url": None,
        }
    )
    governance = value["supplement"]["governance"]
    governance["corrections"] = [
        {
            "profile_id": "COR-001",
            "path": reference["path"],
            "digest": reference["sha256"],
            "correction_class": "bounded_test_correction",
            "authority_status": "approved",
            "approval_id": "APR-001",
            "expected_claim_ids": ["FIND-001"],
            "verified_claim_ids": ["FIND-001"],
            "finding_ids": ["FIND-001"],
            "resolved_finding_ids": ["FIND-001"],
            "unresolved_finding_ids": [],
            "verification_ids": ["VER-001"],
            "verification_subject": "git:" + "a" * 40,
            "verified_at": "2026-08-29T13:00:00Z",
            "evidence": [reference],
        }
    ]
    governance["findings"] = [
        {
            "id": "FIND-001",
            "status": "resolved",
            "severity": "P0",
            "summary": "Bounded finding.",
            "blocking": False,
            "opened_at": None,
            "resolved_at": "2026-08-29T13:00:00Z",
            "correction_profile_id": "COR-001",
            "resolution_verification_id": "VER-001",
            "recovery": None,
            "evidence": [reference],
        }
    ]
    governance["verification"] = [
        {
            "id": "VER-001",
            "author": "author",
            "verifier": "independent-verifier",
            "independent": True,
            "subject": "git:" + "a" * 40,
            "verdict": "passed",
            "blocking": False,
            "finding_ids": ["FIND-001"],
            "correction_profile_ids": ["COR-001"],
            "verified_at": "2026-08-29T13:00:00Z",
            "evidence": [reference],
        }
    ]

    ProgramStatusReader._validate_relations(value)

    governance["corrections"][0]["verification_ids"] = []
    with pytest.raises(ValueError, match="correction claim relations"):
        ProgramStatusReader._validate_relations(value)
