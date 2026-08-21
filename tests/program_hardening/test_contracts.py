from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


CONTRACTS = Path(__file__).parents[2] / "specs" / "073-program-hardening" / "contracts"


def _load(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


def _registry() -> Registry:
    registry = Registry()
    for path in CONTRACTS.glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(
            document["$id"], Resource.from_contents(document)
        )
        registry = registry.with_resource(path.name, Resource.from_contents(document))
    return registry


def test_all_contracts_are_valid_draft_2020_12_schemas() -> None:
    for path in CONTRACTS.glob("*.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_supporting_compatibility_evidence_requires_complete_passed_lifecycle() -> None:
    schema = _load("compatibility-evidence.schema.json")
    base = {
        "schema_version": "1.0",
        "evidence_id": "evidence-1",
        "runtime_version": "0.1.9",
        "artifact_digest": f"sha256:{'a' * 64}",
        "platform": "windows",
        "architecture": "x86_64",
        "manager_profile": "native-hermes",
        "storage_profile": "native",
        "data_schema_before": 14,
        "data_schema_after": 16,
        "source_isolation": "clean-candidate",
        "forbidden_executable_audit": "passed",
        "evidence_level": "host",
        "status": "passed",
        "supporting": True,
    }
    checks = [
        {"name": name, "status": "passed", "reason": "CHECK_PASSED"}
        for name in (
            "install",
            "start",
            "status",
            "doctor",
            "use",
            "stop",
            "upgrade",
            "persist",
            "rollback",
            "uninstall",
            "offline",
        )
    ]
    validator = Draft202012Validator(schema)
    validator.validate({**base, "checks": checks})

    failures = list(validator.iter_errors({**base, "checks": checks[:-1]}))
    assert failures


def test_support_snapshot_contract_resolves_state_inventory_reference() -> None:
    schema = _load("support-diagnostic-snapshot.schema.json")
    validator = Draft202012Validator(schema, registry=_registry())
    snapshot = {
        "schema_version": "1.0",
        "snapshot_id": "snapshot_12345678",
        "created_at": "2026-08-13T12:00:00Z",
        "expires_at": "2026-08-13T12:05:00Z",
        "workspace_id": "workspace-1",
        "principal_digest": f"sha256:{'b' * 64}",
        "scope": {"session_id": "session-1"},
        "summary": {
            "status": "healthy",
            "reason": "READY",
            "next_action": "RUN_PREFLIGHT",
        },
        "providers": [],
        "state_inventory": {
            "schema_version": "1.0",
            "data_schema": 16,
            "catalog_snapshot": {
                "channel": "stable",
                "sequence": 1,
                "digest": f"sha256:{'c' * 64}",
                "state": "active",
            },
            "counts": {},
            "digests": {},
            "storage": [],
        },
        "failures": [],
        "categories": [
            {
                "name": "program-state",
                "disposition": "included",
                "item_count": 1,
                "reason": "INCLUDED",
            }
        ],
        "snapshot_digest": f"sha256:{'d' * 64}",
    }
    validator.validate(snapshot)
