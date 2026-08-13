import pytest

from tool_registry.gateway_models import GatewayToolResult
from workspace_service.rivet_evidence import (
    RivetEvidenceError,
    safe_argument_summary,
    sanitize_gateway_result,
)


def test_evidence_redacts_secret_keys_and_url_values():
    summary, redactions, truncated = safe_argument_summary(
        {"api_key": "secret", "url": "https://example.test/?token=value"}
    )
    assert summary == {
        "api_key": "[redacted]",
        "url": "https://example.test/?token=[redacted]",
    }
    assert redactions == 2
    assert not truncated


def test_gateway_result_accepts_only_workspace_artifact_resources():
    accepted = GatewayToolResult(
        content=(
            {
                "type": "resource_link",
                "uri": "wright://artifact/workspace/result.step",
                "name": "result.step",
                "mimeType": "model/step",
                "sha256": "a" * 64,
                "bytes": 12,
            },
        )
    )
    _, artifacts, _ = sanitize_gateway_result(accepted, workspace_id="workspace")
    assert artifacts[0].artifact_id == "result.step"

    hostile = GatewayToolResult(
        content=(
            {
                "type": "resource_link",
                "uri": "file:///etc/passwd",
                "sha256": "a" * 64,
            },
        )
    )
    with pytest.raises(RivetEvidenceError, match="not authorized"):
        sanitize_gateway_result(hostile, workspace_id="workspace")
