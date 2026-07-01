from tool_registry.mcp_validation import ValidationResult
from tool_registry.validation_evidence import (
    ValidationEvidence,
    ValidationStepEvidence,
    evidence_from_preflight,
    redact_secret_values,
)
from tool_registry.validation_plan import ValidationPlan, ValidationProbeStep


def test_redacts_secret_like_assignments_and_explicit_values():
    text = "API_TOKEN=abc123 password: hunter2 plain abc123"

    redacted = redact_secret_values(text, ["abc123"])

    assert "abc123" not in redacted
    assert "hunter2" not in redacted
    assert "API_TOKEN=[REDACTED]" in redacted
    assert "password=[REDACTED]" in redacted


def test_validation_evidence_redacted_dump_scrubs_steps():
    evidence = ValidationEvidence(
        server_id="server",
        environment="local",
        status="failed",
        diagnostics="token=abc123",
        steps=[
            ValidationStepEvidence(
                name="initialize",
                status="failed",
                output="secret=abc123",
                error="authorization: bearer-token",
            )
        ],
    )

    data = evidence.redacted_model_dump(["abc123", "bearer-token"])

    assert "abc123" not in str(data)
    assert "bearer-token" not in str(data)
    assert data["steps"][0]["output"] == "secret=[REDACTED]"


def test_preflight_evidence_preserves_classification_without_execution():
    plan = ValidationPlan(
        server_id="server",
        environment="ubuntu-linux-x64-container",
        preflight={"status": "blocked"},
        protocol_probes=[ValidationProbeStep(name="initialize", method="initialize")],
    )
    result = ValidationResult(
        server_id="server",
        environment="ubuntu-linux-x64-container",
        status="blocked",
        installability_tier="blocked",
        message="URL missing",
        diagnostics="URL missing",
    )

    evidence = evidence_from_preflight(plan, result)

    assert evidence.status == "blocked"
    assert evidence.steps[0].name == "metadata_preflight"
    assert evidence.diagnostics == "URL missing"
