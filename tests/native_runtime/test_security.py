from __future__ import annotations

from wright_engineering.runtime.diagnostics import bounded_details, redact
from wright_engineering.runtime.logging import LifecycleLogger


def test_redaction_masks_nested_secrets_and_sensitive_assignments() -> None:
    payload = {
        "token": "top-secret",
        "nested": {"API_KEY": "abc", "safe": "value"},
        "message": "PASSWORD=hunter2 request failed",
    }
    cleaned = redact(payload)
    rendered = repr(cleaned)
    assert "top-secret" not in rendered
    assert "hunter2" not in rendered
    assert "abc" not in rendered
    assert "value" in rendered


def test_diagnostic_details_are_allowlisted_and_bounded() -> None:
    details = bounded_details(
        {
            "state": "healthy",
            "ui_url": "http://127.0.0.1:8000",
            "stdout": "x" * 100_000,
            "environment": {"SECRET": "bad"},
        },
        allowed={"state", "ui_url", "stdout"},
        max_value_length=128,
    )
    assert "environment" not in details
    assert len(details["stdout"]) <= 128


def test_structured_lifecycle_log_has_operation_id_and_no_secret(tmp_path) -> None:
    path = tmp_path / "lifecycle.jsonl"
    LifecycleLogger(path).emit(
        "operation",
        operation_id="op-123",
        token="test-secret-value",
        summary="PASSWORD=hunter2 failed",
    )
    content = path.read_text(encoding="utf-8")
    assert '"operation_id": "op-123"' in content
    assert "test-secret-value" not in content
    assert "hunter2" not in content
