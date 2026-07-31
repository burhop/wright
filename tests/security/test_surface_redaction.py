from __future__ import annotations

import json

import pytest

from core.redaction import REDACTED, redact_text
from core.surfaces.telemetry import redact_surface_attributes


pytestmark = pytest.mark.workspace_surfaces


def test_surface_attributes_remove_every_sensitive_boundary_value() -> None:
    secret = "test-secret-value"
    attributes = redact_surface_attributes(
        {
            "authorization": f"Bearer {secret}",
            "cookie": f"wright_surface={secret}",
            "secret_env": {"BREP_TOKEN": secret},
            "query": f"?access_token={secret}",
            "target_pin": {"numeric_address": "127.0.0.1", "port": 8000},
            "user_content": f"private drawing {secret}",
            "upstream_logs": f"Cookie: app_session={secret}",
            "source_id": "brep",
            "manifest_hash": "a" * 64,
        }
    )
    serialized = json.dumps(attributes)
    assert secret not in serialized
    assert "127.0.0.1" not in serialized
    for key in (
        "authorization",
        "cookie",
        "secret_env",
        "query",
        "target_pin",
        "user_content",
        "upstream_logs",
    ):
        assert attributes[key] == REDACTED
    assert attributes["source_id"] == "brep"
    assert attributes["manifest_hash"] == "a" * 64


def test_diagnostic_text_redacts_bearer_cookie_and_secret_query_values() -> None:
    value = redact_text(
        "Bearer bearer-value Cookie: wright_surface=cookie-value "
        "url=https://example.test/?token=query-value"
    )
    assert "bearer-value" not in value
    assert "cookie-value" not in value
    assert "query-value" not in value
