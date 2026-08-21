from __future__ import annotations

import os
from pathlib import Path

import pytest

from wright_engineering.runtime.diagnostics import bounded_details, redact
from wright_engineering.runtime.auth import (
    ControlPlaneTokenError,
    ensure_control_plane_token,
    read_control_plane_token,
)
from wright_engineering.runtime.layout import NativeLayout
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


def test_redaction_uses_the_program_path_authority_and_collection_limits() -> None:
    cleaned = redact(
        {
            "safe": ["value"] * 150,
            "message": (
                "Bearer reusable-token C:\\Users\\engineer\\private.step "
                "http://127.0.0.1:8123/control"
            ),
            "artifact_body": "private geometry",
            "model_features": [0.1, 0.2],
        }
    )
    rendered = repr(cleaned)
    assert len(cleaned["safe"]) == 100
    assert "reusable-token" not in rendered
    assert "engineer" not in rendered
    assert "8123" not in rendered
    assert "private geometry" not in rendered
    assert "0.1" not in rendered


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


def test_managed_control_plane_token_is_stable_contained_and_private(
    tmp_path: Path,
) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")

    first = ensure_control_plane_token(layout)
    second = ensure_control_plane_token(layout)

    assert first == second
    assert len(first) == 64
    assert read_control_plane_token(layout) == first
    assert layout.control_plane_token.parent == layout.data
    assert layout.control_plane_token.read_text(encoding="utf-8") == first
    if os.name != "nt":
        assert layout.control_plane_token.stat().st_mode & 0o077 == 0


def test_managed_control_plane_token_rejects_symlink(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    layout.ensure()
    outside = tmp_path / "outside-token"
    outside.write_text("a" * 64, encoding="utf-8")
    try:
        layout.control_plane_token.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this host")

    with pytest.raises(ControlPlaneTokenError, match="symlink"):
        ensure_control_plane_token(layout)
