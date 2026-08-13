from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import sqlite3

import pytest
from data_vault import upgrade_database
from pydantic import ValidationError
from tool_registry.capability_models import ValidationEvidence
from tool_registry.validation_evidence import (
    ValidationEvidenceError,
    latest_capability_validation_evidence,
    list_capability_validation_evidence,
    require_current_passed_validation,
    save_capability_validation_evidence,
    validation_staleness_reasons,
)

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def _evidence(**changes) -> ValidationEvidence:
    data = {
        "evidence_id": "validation-one",
        "capability_id": "fixture-capability",
        "server_id": "fixture-server",
        "snapshot_id": "snapshot-one",
        "capability_digest": DIGEST_A,
        "observation_id": "observation-one",
        "platform_key": "linux_x64",
        "architecture": "x86_64",
        "server_revision": "1.0.0",
        "credential_binding_digest": DIGEST_B,
        "state": "passed",
        "protocol_steps": {
            "initialize": "passed",
            "notifications/initialized": "passed",
            "tools/list": "passed",
        },
        "schema_digest": DIGEST_C,
        "tool_count": 2,
        "read_only_probe": {
            "name": "health",
            "argument_digest": DIGEST_A,
            "result_digest": DIGEST_B,
            "status": "passed",
            "limitation": "Read-only fixture",
        },
        "observed_at": NOW,
        "trace_id": "trace-validation",
        "reason_codes": [],
        "missing_requirements": [],
    }
    data.update(changes)
    return ValidationEvidence.model_validate(data)


def _current(**changes):
    data = {
        "snapshot_id": "snapshot-one",
        "capability_digest": DIGEST_A,
        "observation_id": "observation-one",
        "server_revision": "1.0.0",
        "credential_binding_digest": DIGEST_B,
        "schema_digest": DIGEST_C,
        "now": NOW + timedelta(minutes=5),
    }
    data.update(changes)
    return data


def _seed_references(database) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO catalog_snapshots (
                snapshot_id, channel, sequence, schema_version, issued_at,
                expires_at, payload_sha256, payload_json, verification_state
            ) VALUES ('snapshot-one', 'test', 1, 1, 1, 2, ?, ?, 'active')""",
            (DIGEST_A, json.dumps({"servers": []})),
        )
        connection.execute(
            """INSERT INTO machine_compatibility_observations (
                observation_id, observed_at, expires_at, platform_key, os_name,
                os_version, architecture, distribution_mode, observation_json, digest
            ) VALUES ('observation-one', 1, 2, 'linux_x64', 'Linux', 'test',
                      'x86_64', 'test', '{}', ?)""",
            (DIGEST_B,),
        )
        connection.commit()


def test_required_transitions_reject_partial_pass_and_reasonless_failure() -> None:
    with pytest.raises(ValidationError, match="required protocol steps"):
        _evidence(protocol_steps={"initialize": "passed", "tools/list": "passed"})
    with pytest.raises(ValidationError, match="requires an explicit reason"):
        _evidence(state="failed", schema_digest=None, tool_count=None)

    partial = _evidence(
        state="partially_passed",
        protocol_steps={
            "initialize": "passed",
            "notifications/initialized": "passed",
            "tools/list": "failed",
        },
        schema_digest=None,
        tool_count=None,
        reason_codes=["validation_tools_list_failed"],
    )
    assert partial.state == "partially_passed"


def test_repository_is_append_only_and_returns_latest_redacted_record(tmp_path) -> None:
    database = tmp_path / "validation.db"
    upgrade_database(database)
    _seed_references(database)
    evidence = _evidence()

    save_capability_validation_evidence(database, evidence)
    assert (
        latest_capability_validation_evidence(database, evidence.server_id) == evidence
    )
    with pytest.raises(ValidationEvidenceError, match="append-only"):
        save_capability_validation_evidence(database, evidence)
    assert "secret" not in evidence.model_dump_json().lower()

    newer = _evidence(
        evidence_id="validation-two",
        observed_at=NOW + timedelta(minutes=1),
    )
    save_capability_validation_evidence(database, newer)
    assert list_capability_validation_evidence(database, evidence.server_id) == [
        newer,
        evidence,
    ]
    with pytest.raises(ValueError, match="between 1 and 100"):
        list_capability_validation_evidence(database, evidence.server_id, limit=0)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"snapshot_id": "snapshot-two"}, "validation_snapshot_changed"),
        ({"capability_digest": DIGEST_C}, "validation_capability_changed"),
        (
            {"observation_id": "observation-two"},
            "validation_machine_observation_changed",
        ),
        ({"server_revision": "2.0.0"}, "validation_server_revision_changed"),
        (
            {"credential_binding_digest": DIGEST_C},
            "validation_credential_binding_changed",
        ),
        ({"schema_digest": DIGEST_A}, "validation_schema_changed"),
        ({"now": NOW + timedelta(days=2)}, "validation_evidence_expired"),
    ],
)
def test_material_changes_and_age_make_evidence_stale(change, reason) -> None:
    assert reason in validation_staleness_reasons(_evidence(), **_current(**change))


def test_enablement_policy_requires_current_fully_passed_evidence(tmp_path) -> None:
    database = tmp_path / "enable.db"
    upgrade_database(database)
    _seed_references(database)
    with pytest.raises(ValidationEvidenceError) as missing:
        require_current_passed_validation(database, "fixture-server", **_current())
    assert missing.value.code == "validation_required"

    failed = _evidence(
        state="failed",
        schema_digest=None,
        tool_count=None,
        reason_codes=["validation_tools_list_failed"],
    )
    save_capability_validation_evidence(database, failed)
    with pytest.raises(ValidationEvidenceError) as not_passed:
        require_current_passed_validation(database, "fixture-server", **_current())
    assert not_passed.value.code == "validation_not_passed"
