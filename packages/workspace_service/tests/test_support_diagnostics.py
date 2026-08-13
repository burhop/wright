from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.support_diagnostics import (
    MAX_COLLECTION_ITEMS,
    MAX_EXPORT_BYTES,
    MAX_SAFE_STRING_LENGTH,
    DiagnosticPolicyError,
    canonical_snapshot_bytes,
    digest_value,
    sanitize_untrusted,
)


@pytest.mark.parametrize(
    "value",
    [
        {"token": "token-secret"},
        {"api_key": "api-secret"},
        {"Authorization": "Bearer bearer-secret"},
        {"password": "password-secret"},
        {"environment": {"SAFE": "env-secret"}},
        {"command": "python proprietary.py --token command-secret"},
        {"arguments": ["--secret", "argument-secret"]},
        {"prompt": "private engineering prompt"},
        {"request_body": {"geometry": "private-body"}},
        {"model_features": [1.0, 2.0]},
        {"artifact_body": "private-step-body"},
        {"filename": "customer-part.step"},
        {"path": r"C:\Customers\Secret\part.step"},
        {"endpoint": "http://127.0.0.1:43123/private"},
        {"authority": "reusable-authority"},
        {"cookie": "session-cookie"},
        {"database_row": {"payload": "private-row"}},
        {"process_environment": "PRIVATE=secret"},
        {"tool_result": "private result"},
        {"raw_log": "api_key=log-secret"},
    ],
)
def test_adversarial_private_values_are_irreversibly_redacted(value: object) -> None:
    rendered = repr(sanitize_untrusted(value))
    for forbidden in (
        "token-secret",
        "api-secret",
        "bearer-secret",
        "password-secret",
        "env-secret",
        "command-secret",
        "argument-secret",
        "private engineering prompt",
        "private-body",
        "customer-part.step",
        "Customers",
        "43123",
        "reusable-authority",
        "session-cookie",
        "private-row",
        "private result",
        "log-secret",
    ):
        assert forbidden not in rendered


def test_sanitizer_caps_strings_and_collections() -> None:
    sanitized = sanitize_untrusted(
        {
            "safe_code": "A" * (MAX_SAFE_STRING_LENGTH + 50),
            "safe_items": list(range(MAX_COLLECTION_ITEMS + 50)),
        },
        allowed_keys={"safe_code", "safe_items"},
    )
    assert len(sanitized["safe_code"]) == MAX_SAFE_STRING_LENGTH
    assert len(sanitized["safe_items"]) == MAX_COLLECTION_ITEMS


def test_canonical_snapshot_bytes_are_stable_and_bounded() -> None:
    now = datetime(2026, 8, 13, 12, tzinfo=UTC)
    snapshot = {
        "schema_version": "1.0",
        "snapshot_id": "snapshot_12345678",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        "workspace_id": "workspace-1",
        "principal_digest": digest_value("principal-1"),
        "scope": {},
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
                "digest": digest_value("catalog"),
                "state": "active",
            },
            "counts": {},
            "digests": {},
            "storage": [],
        },
        "failures": [],
        "categories": [],
    }
    assert canonical_snapshot_bytes(snapshot) == canonical_snapshot_bytes(snapshot)
    assert len(canonical_snapshot_bytes(snapshot)) < MAX_EXPORT_BYTES

    with pytest.raises(DiagnosticPolicyError, match="DIAGNOSTIC_EXPORT_TOO_LARGE"):
        canonical_snapshot_bytes({"safe": "x" * (MAX_EXPORT_BYTES + 1)})
