from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.surfaces.telemetry import (
    SurfaceDiagnosticEvent,
    SurfaceSeverity,
    TraceCorrelation,
    redact_surface_attributes,
)


pytestmark = pytest.mark.workspace_surfaces


def test_surface_attributes_are_recursively_redacted_without_mutating_input() -> None:
    original = {
        "surface_id": "surface-1",
        "token": "super-secret",
        "authorization": "Bearer abc.def.ghi",
        "target_url": "https://user:pass@example.test/path?token=secret",
        "nested": {
            "password": "p4ss",
            "safe": "token=hidden",
            "prompt": "private user prompt",
            "effective_constraints": {"proprietary": True},
            "script": "print('private')",
        },
    }
    safe = redact_surface_attributes(original)
    rendered = repr(safe).lower()
    for secret in (
        "super-secret",
        "abc.def.ghi",
        "user:pass",
        "token=secret",
        "p4ss",
        "private user prompt",
        "proprietary",
        "print('private')",
    ):
        assert secret.lower() not in rendered
    assert safe["surface_id"] == "surface-1"
    assert original["token"] == "super-secret"


def test_diagnostic_event_requires_stable_code_and_complete_trace_context() -> None:
    event = SurfaceDiagnosticEvent(
        timestamp=datetime(2026, 7, 30, 12, 0, tzinfo=UTC),
        severity=SurfaceSeverity.WARNING,
        code="SURFACE_STATE_STALE_REVISION",
        message="The surface changed; refresh before retrying.",
        correlation=TraceCorrelation(
            correlation_id="correlation-1",
            trace_id="0" * 32,
            span_id="1" * 16,
        ),
        retryable=True,
        workspace_id="workspace-1",
        surface_id="surface-1",
        attributes={"expected_revision": 1, "current_revision": 2},
    )
    assert event.code == "SURFACE_STATE_STALE_REVISION"
    assert event.attributes == {"expected_revision": 1, "current_revision": 2}
    with pytest.raises(ValueError, match="SURFACE_"):
        SurfaceDiagnosticEvent(
            timestamp=event.timestamp,
            severity=event.severity,
            code="stale_revision",
            message=event.message,
            correlation=event.correlation,
            retryable=True,
            workspace_id="workspace-1",
            surface_id="surface-1",
        )


def test_diagnostic_event_never_serializes_forbidden_content() -> None:
    event = SurfaceDiagnosticEvent(
        timestamp=datetime(2026, 7, 30, 12, 0, tzinfo=UTC),
        severity=SurfaceSeverity.ERROR,
        code="SURFACE_RUNTIME_START_FAILED",
        message="Application startup failed.",
        correlation=TraceCorrelation(
            correlation_id="correlation-1",
            trace_id="0" * 32,
            span_id="1" * 16,
        ),
        retryable=True,
        workspace_id="workspace-1",
        surface_id="surface-1",
        attributes={
            "prompt": "secret design prompt",
            "effective_constraints": {"customer": "private"},
            "script_content": "open('secret.step')",
            "api_key": "key-1",
        },
    )
    rendered = repr(event.as_dict()).lower()
    assert "secret design prompt" not in rendered
    assert "customer" not in rendered
    assert "secret.step" not in rendered
    assert "key-1" not in rendered
