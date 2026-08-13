from __future__ import annotations

import re
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from core.redaction import redact_mapping, redact_text

from .mcp_validation import ValidationResult
from .validation_plan import ValidationPlan
from .capability_models import ValidationEvidence as CapabilityValidationEvidence

SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?(?:key|token)|secret|token|password|authorization)\b\s*[:=]\s*([^\s,;]+)"
)
VALIDATION_MAX_AGE = timedelta(hours=24)


class ValidationEvidenceError(RuntimeError):
    def __init__(self, code: str, message: str, *, http_status: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.status_code = http_status


def _connection(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def save_capability_validation_evidence(
    database_path: str | Path, evidence: CapabilityValidationEvidence
) -> CapabilityValidationEvidence:
    """Append evidence exactly once; validation history is never overwritten."""

    payload = evidence.model_dump_json()
    with _connection(database_path) as connection:
        try:
            connection.execute(
                """INSERT INTO mcp_validation_evidence (
                    evidence_id, capability_id, server_id, snapshot_id,
                    observation_id, state, schema_digest, evidence_json,
                    observed_at, trace_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evidence.evidence_id,
                    evidence.capability_id,
                    evidence.server_id,
                    evidence.snapshot_id,
                    evidence.observation_id,
                    evidence.state,
                    evidence.schema_digest,
                    payload,
                    int(evidence.observed_at.timestamp()),
                    evidence.trace_id,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise ValidationEvidenceError(
                "validation_evidence_conflict",
                "Validation evidence is append-only and this identity already exists.",
            ) from error
    return evidence


def _evidence_from_row(row: sqlite3.Row) -> CapabilityValidationEvidence:
    return CapabilityValidationEvidence.model_validate(json.loads(row["evidence_json"]))


def latest_capability_validation_evidence(
    database_path: str | Path, server_id: str
) -> CapabilityValidationEvidence | None:
    with _connection(database_path) as connection:
        row = connection.execute(
            """SELECT evidence_json FROM mcp_validation_evidence
               WHERE server_id=? ORDER BY observed_at DESC, evidence_id DESC LIMIT 1""",
            (server_id,),
        ).fetchone()
    return _evidence_from_row(row) if row else None


def validation_staleness_reasons(
    evidence: CapabilityValidationEvidence,
    *,
    snapshot_id: str,
    capability_digest: str,
    observation_id: str,
    server_revision: str,
    credential_binding_digest: str,
    schema_digest: str | None = None,
    now: datetime | None = None,
    maximum_age: timedelta = VALIDATION_MAX_AGE,
) -> list[str]:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    comparisons = (
        (evidence.snapshot_id, snapshot_id, "validation_snapshot_changed"),
        (
            evidence.capability_digest,
            capability_digest,
            "validation_capability_changed",
        ),
        (
            evidence.observation_id,
            observation_id,
            "validation_machine_observation_changed",
        ),
        (
            evidence.server_revision,
            server_revision,
            "validation_server_revision_changed",
        ),
        (
            evidence.credential_binding_digest,
            credential_binding_digest,
            "validation_credential_binding_changed",
        ),
    )
    reasons.extend(code for before, after, code in comparisons if before != after)
    if schema_digest is not None and evidence.schema_digest != schema_digest:
        reasons.append("validation_schema_changed")
    if current_time - evidence.observed_at > maximum_age:
        reasons.append("validation_evidence_expired")
    return reasons


def require_current_passed_validation(
    database_path: str | Path,
    server_id: str,
    **current: Any,
) -> CapabilityValidationEvidence:
    evidence = latest_capability_validation_evidence(database_path, server_id)
    if evidence is None:
        raise ValidationEvidenceError(
            "validation_required",
            "Run validation before enabling this capability for a workspace.",
        )
    if evidence.state != "passed":
        raise ValidationEvidenceError(
            "validation_not_passed",
            "Only current, fully passed protocol evidence permits workspace enablement.",
        )
    reasons = validation_staleness_reasons(evidence, **current)
    if reasons:
        raise ValidationEvidenceError(
            "validation_stale",
            "Validation is stale; run it again before workspace enablement.",
        )
    return evidence


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
