from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_fixture_or_skipped_evidence_cannot_claim_platform_support() -> None:
    path = (
        Path(__file__).parents[2]
        / "specs"
        / "073-program-hardening"
        / "contracts"
        / "compatibility-evidence.schema.json"
    )
    validator = Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))
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
    base = {
        "schema_version": "1.0",
        "evidence_id": "evidence-1",
        "runtime_version": "0.1.9",
        "artifact_digest": f"sha256:{'a' * 64}",
        "platform": "linux",
        "architecture": "arm64",
        "manager_profile": "docker-mcp",
        "storage_profile": "docker-mcp",
        "data_schema_before": 16,
        "data_schema_after": 16,
        "checks": checks,
        "status": "passed",
        "supporting": True,
        "source_isolation": "clean-candidate",
        "forbidden_executable_audit": "passed",
    }

    assert list(validator.iter_errors({**base, "evidence_level": "fixture"}))
    assert list(
        validator.iter_errors(
            {
                **base,
                "evidence_level": "host",
                "status": "skipped",
            }
        )
    )
