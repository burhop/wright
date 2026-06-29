from tool_registry.mcp_followups import redact_secrets, write_followup_record
from tool_registry.mcp_validation import ValidationResult


def test_redacts_secret_like_values():
    assert "abc123" not in redact_secrets("api_key=abc123")
    assert "<redacted>" in redact_secrets("token: abc123")


def test_write_followup_record_deduplicates(tmp_path):
    result = ValidationResult(
        server_id="broken-server",
        environment="ubuntu-linux-x64-container",
        status="failed",
        installability_tier="non_working",
        message="Failed",
        diagnostics="token=abc123 failed",
    )

    first = write_followup_record(
        tmp_path, result, "https://example.com", "community_mcp"
    )
    second = write_followup_record(
        tmp_path, result, "https://example.com", "community_mcp"
    )

    assert first == second
    content = (tmp_path / "broken-server.md").read_text(encoding="utf-8")
    assert "abc123" not in content
    assert "broken-server" in content
