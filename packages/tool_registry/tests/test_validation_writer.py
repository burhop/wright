import json

from tool_registry.validation_evidence import (
    ValidationEvidence,
    ValidationStepEvidence,
)
from tool_registry.validation_writer import write_validation_evidence


def test_validation_writer_emits_redacted_json_and_markdown(tmp_path):
    evidence = ValidationEvidence(
        server_id="secret-server",
        environment="unit-test",
        container_image="local-mock",
        install_steps=["uvx server --token abc123"],
        status="failed",
        result="failed",
        diagnostics="API_TOKEN=abc123",
        steps=[
            ValidationStepEvidence(
                name="tools/list",
                status="failed",
                output="password=hunter2",
            )
        ],
        follow_up_required=True,
        redactions=["credentials", "commands"],
    )

    json_path, markdown_path = write_validation_evidence(
        evidence, tmp_path, secrets=["abc123", "hunter2"]
    )

    data = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    combined = json.dumps(data) + markdown

    assert "abc123" not in combined
    assert "hunter2" not in combined
    assert data["follow_up_required"] is True
    assert "MCP Validation Evidence" in markdown
