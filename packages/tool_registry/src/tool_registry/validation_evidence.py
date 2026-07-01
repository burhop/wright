from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from .mcp_validation import ValidationResult
from .validation_plan import ValidationPlan

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password|authorization)\b\s*[:=]\s*([^\s,;]+)"
)


class ValidationStepEvidence(BaseModel):
    name: str
    status: str
    output: str = ""
    error: str | None = None
    duration_ms: int | None = None


class ValidationEvidence(BaseModel):
    server_id: str
    environment: str
    status: str
    steps: list[ValidationStepEvidence] = Field(default_factory=list)
    diagnostics: str = ""
    missing_dependencies: list[str] = Field(default_factory=list)
    follow_up_url: str | None = None

    def redacted_model_dump(self, secrets: list[str] | None = None) -> dict[str, Any]:
        data = self.model_dump()
        data["diagnostics"] = redact_secret_values(data["diagnostics"], secrets)
        for step in data["steps"]:
            step["output"] = redact_secret_values(step.get("output", ""), secrets)
            if step.get("error"):
                step["error"] = redact_secret_values(step["error"], secrets)
        return data


def redact_secret_values(text: str, secrets: list[str] | None = None) -> str:
    redacted = text
    for secret in secrets or []:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return SECRET_ASSIGNMENT_RE.sub(r"\1=[REDACTED]", redacted)


def evidence_from_preflight(
    plan: ValidationPlan, result: ValidationResult
) -> ValidationEvidence:
    return ValidationEvidence(
        server_id=plan.server_id,
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
