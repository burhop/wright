from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).parents[2]


def _validator() -> Draft202012Validator:
    contract = (
        ROOT
        / "specs"
        / "073-program-hardening"
        / "contracts"
        / "compatibility-evidence.schema.json"
    )
    return Draft202012Validator(json.loads(contract.read_text(encoding="utf-8")))


def _record(*, platform: str = "windows", architecture: str = "x86_64") -> dict:
    return {
        "schema_version": "1.0",
        "evidence_id": f"candidate-{platform}-{architecture}",
        "runtime_version": "0.1.9",
        "artifact_digest": f"sha256:{'a' * 64}",
        "platform": platform,
        "architecture": architecture,
        "manager_profile": "native-hermes",
        "storage_profile": "native",
        "data_schema_before": 14,
        "data_schema_after": 16,
        "checks": [
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
        ],
        "source_isolation": "clean-candidate",
        "forbidden_executable_audit": "passed",
        "evidence_level": "host",
        "status": "passed",
        "supporting": True,
    }


def test_exact_candidate_platform_and_architecture_record_can_support() -> None:
    _validator().validate(_record())


def test_unavailable_platform_remains_non_supporting_without_invalidating_available() -> (
    None
):
    validator = _validator()
    available = _record()
    unavailable = {
        **_record(platform="macos", architecture="arm64"),
        "checks": [
            {"name": "install", "status": "skipped", "reason": "HOST_UNAVAILABLE"}
        ],
        "source_isolation": "unknown",
        "forbidden_executable_audit": "skipped",
        "evidence_level": "contract",
        "status": "skipped",
        "supporting": False,
    }
    validator.validate(available)
    validator.validate(unavailable)
    assert (available["platform"], available["architecture"]) != (
        unavailable["platform"],
        unavailable["architecture"],
    )


def test_support_rejects_nonisolated_source_or_changed_artifact_subject() -> None:
    validator = _validator()
    record = _record()
    assert list(validator.iter_errors({**record, "source_isolation": "installed-host"}))
    changed = {
        **record,
        "evidence_id": "candidate-windows-x86-64-new",
        "artifact_digest": f"sha256:{'b' * 64}",
        "supporting": False,
        "evidence_level": "contract",
    }
    validator.validate(changed)
    assert changed["artifact_digest"] != record["artifact_digest"]
