from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field
from core.redaction import redact_mapping, redact_text

from .mcp_validation import ValidationResult
from .validation_plan import ValidationPlan

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?(?:key|token)|secret|token|password|authorization)\b\s*[:=]\s*([^\s,;]+)"
)


class ValidationStepEvidence(BaseModel):
    name: str
    status: str
    output: str = ""
    error: str | None = None
    duration_ms: int | None = None


class ValidationEvidence(BaseModel):
    server_id: str
    catalog_version: str = "unknown"
    validation_started_at: str | None = None
    validation_finished_at: str | None = None
    environment: str
    container_image: str | None = None
    install_steps: list[str] = Field(default_factory=list)
    protocol_probes: list[ValidationStepEvidence] = Field(default_factory=list)
    safe_backend_probe: ValidationStepEvidence | None = None
    gateway_proxy_probe: list[ValidationStepEvidence] = Field(default_factory=list)
    credential_requirements: list[str] = Field(default_factory=list)
    network_requirements: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None
    status: str
    steps: list[ValidationStepEvidence] = Field(default_factory=list)
    diagnostics: str = ""
    missing_dependencies: list[str] = Field(default_factory=list)
    follow_up_url: str | None = None
    follow_up_required: bool = False
    redactions: list[str] = Field(default_factory=list)

    def redacted_model_dump(self, secrets: list[str] | None = None) -> dict[str, Any]:
        data = self.model_dump()
        data = redact_mapping(data)
        data["diagnostics"] = redact_secret_values(data["diagnostics"], secrets)
        for section in ("steps", "protocol_probes", "gateway_proxy_probe"):
            for step in data.get(section, []):
                step["output"] = redact_secret_values(step.get("output", ""), secrets)
                if step.get("error"):
                    step["error"] = redact_secret_values(step["error"], secrets)
        if data.get("safe_backend_probe"):
            data["safe_backend_probe"]["output"] = redact_secret_values(
                data["safe_backend_probe"].get("output", ""), secrets
            )
            if data["safe_backend_probe"].get("error"):
                data["safe_backend_probe"]["error"] = redact_secret_values(
                    data["safe_backend_probe"]["error"], secrets
                )
        for index, step in enumerate(data.get("install_steps", [])):
            data["install_steps"][index] = redact_secret_values(step, secrets)
        return data


def redact_secret_values(text: str, secrets: list[str] | None = None) -> str:
    redacted = redact_text(text, secrets)
    for secret in secrets or []:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return SECRET_ASSIGNMENT_RE.sub(r"\1=[REDACTED]", redacted)


def evidence_from_preflight(
    plan: ValidationPlan, result: ValidationResult
) -> ValidationEvidence:
    return ValidationEvidence(
        server_id=plan.server_id,
        container_image=("ubuntu-x64" if plan.requires_docker else "local-mock"),
        install_steps=plan.install_steps,
        credential_requirements=[],
        network_requirements={"requires_network": plan.requires_network},
        result=result.status,
        environment=plan.environment,
        status=result.status,
        steps=[
            ValidationStepEvidence(
                name="metadata_preflight",
                status=result.status,
                output=result.message,
            )
        ],
        diagnostics=result.diagnostics or result.message,
        missing_dependencies=result.missing_dependencies,
        follow_up_url=result.follow_up_url,
    )
