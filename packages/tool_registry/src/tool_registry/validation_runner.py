from __future__ import annotations

import time
import hashlib
import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from .capability_models import (
    MachineCompatibilityObservation,
    ValidationEvidence as CapabilityValidationEvidence,
)
from .catalog_signing import canonical_json
from .validation_evidence import save_capability_validation_evidence
from .validation_evidence import ValidationEvidence, ValidationStepEvidence
from .validation_plan import ValidationPlan, ValidationProbeStep


class LightweightProbeClient(Protocol):
    async def initialize(self) -> dict[str, Any]: ...

    async def initialized(self) -> None: ...

    async def list_tools(self) -> list[dict[str, Any]]: ...

    async def call_tool(
        self, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]: ...


class ValidationCancelled(RuntimeError):
    pass


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _cancelled(cancel_requested: Callable[[], bool] | None) -> None:
    if cancel_requested and cancel_requested():
        raise ValidationCancelled("Validation was cancelled before the next probe.")


async def run_capability_validation(
    database_path: str | Path,
    *,
    capability_id: str,
    server_id: str,
    snapshot_id: str,
    capability_document: Mapping[str, Any],
    observation: MachineCompatibilityObservation,
    server_revision: str,
    credential_status: Mapping[str, bool],
    client: LightweightProbeClient | None,
    gateway_client: LightweightProbeClient | None = None,
    read_only_probe: Mapping[str, Any] | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    trace_id: str | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> CapabilityValidationEvidence:
    """Run the bounded MCP protocol sequence and persist only digests/booleans."""

    observed_at = clock()
    capability_digest = _digest(dict(capability_document))
    credential_digest = _digest(
        {str(key): bool(value) for key, value in sorted(credential_status.items())}
    )
    steps = {
        "initialize": "pending",
        "notifications/initialized": "pending",
        "tools/list": "pending",
    }
    reasons: list[str] = []
    missing: list[str] = []
    schema_digest: str | None = None
    tool_count: int | None = None
    probe_evidence: dict[str, Any] | None = None

    if client is None:
        steps = {name: "skipped" for name in steps}
        reasons.append("validation_client_unavailable")
        missing.append("configured_validation_client")
        state = "blocked"
    else:
        state = "passed"
        try:
            _cancelled(cancel_requested)
            await client.initialize()
            steps["initialize"] = "passed"
            _cancelled(cancel_requested)
            await client.initialized()
            steps["notifications/initialized"] = "passed"
            _cancelled(cancel_requested)
            tools = await client.list_tools()
            if not isinstance(tools, list):
                raise TypeError("tools/list did not return a list")
            normalized_tools = [
                {
                    "name": str(tool.get("name", "")),
                    "input_schema": tool.get(
                        "inputSchema", tool.get("input_schema", {})
                    ),
                    "output_schema": tool.get(
                        "outputSchema", tool.get("output_schema")
                    ),
                }
                for tool in tools
                if isinstance(tool, Mapping)
            ]
            schema_digest = _digest(normalized_tools)
            tool_count = len(normalized_tools)
            steps["tools/list"] = "passed"
            if read_only_probe:
                _cancelled(cancel_requested)
                probe_name = str(read_only_probe["name"])
                arguments = dict(read_only_probe.get("arguments", {}))
                result = await client.call_tool(probe_name, arguments)
                probe_evidence = {
                    "name": probe_name,
                    "argument_digest": _digest(arguments),
                    "result_digest": _digest(result),
                    "status": "passed",
                    "limitation": str(
                        read_only_probe.get(
                            "limitation",
                            "The probe confirms only this bounded read-only request.",
                        )
                    ),
                }
            if gateway_client is not None:
                _cancelled(cancel_requested)
                gateway_tools = await gateway_client.list_tools()
                if not isinstance(gateway_tools, list):
                    raise TypeError("gateway tools/list did not return a list")
                reasons.append("gateway_proxy_validated")
        except ValidationCancelled:
            state = "blocked"
            reasons.append("validation_cancelled")
            for name, status in steps.items():
                if status == "pending":
                    steps[name] = "skipped"
        except Exception as error:
            state = "failed"
            reasons.append(
                f"validation_{next((name for name, value in steps.items() if value == 'pending'), 'probe')}_failed".replace(
                    "/", "_"
                )
            )
            for name, status in steps.items():
                if status == "pending":
                    steps[name] = (
                        "failed"
                        if not any(value == "failed" for value in steps.values())
                        else "skipped"
                    )
            missing.append(type(error).__name__)

    evidence = CapabilityValidationEvidence(
        evidence_id=f"validation-{uuid.uuid4().hex}",
        capability_id=capability_id,
        server_id=server_id,
        snapshot_id=snapshot_id,
        capability_digest=capability_digest,
        observation_id=observation.observation_id,
        platform_key=observation.platform_key,
        architecture=observation.architecture,
        server_revision=server_revision,
        credential_binding_digest=credential_digest,
        state=state,
        protocol_steps=steps,
        schema_digest=schema_digest,
        tool_count=tool_count,
        read_only_probe=probe_evidence,
        observed_at=observed_at,
        trace_id=trace_id,
        reason_codes=reasons,
        missing_requirements=missing,
    )
    return save_capability_validation_evidence(database_path, evidence)


async def run_lightweight_validation(
    plan: ValidationPlan,
    client: LightweightProbeClient,
    *,
    gateway_client: LightweightProbeClient | None = None,
) -> ValidationEvidence:
    steps: list[ValidationStepEvidence] = []
    status = "passed"

    for probe in plan.protocol_probes:
        step = await _run_probe(client, probe)
        steps.append(step)
        if step.status != "passed" and probe.required:
            status = "failed"
            break

    if status == "passed" and plan.safe_backend_probe:
        step = await _run_probe(client, plan.safe_backend_probe)
        steps.append(step)
        if step.status != "passed" and plan.safe_backend_probe.required:
            status = "failed"

    if status == "passed" and gateway_client:
        for probe in plan.gateway_probe:
            step = await _run_probe(gateway_client, probe)
            steps.append(step)
            if step.status != "passed" and probe.required:
                status = "failed"
                break

    diagnostics = "\n".join(
        step.output or step.error or f"{step.name}: {step.status}" for step in steps
    )
    return ValidationEvidence(
        server_id=plan.server_id,
        environment=plan.environment,
        status=status,
        steps=steps,
        diagnostics=diagnostics,
    )


async def _run_probe(
    client: LightweightProbeClient, probe: ValidationProbeStep
) -> ValidationStepEvidence:
    started = time.perf_counter()
    try:
        if probe.method == "initialize":
            output = await client.initialize()
        elif probe.method == "notifications/initialized":
            await client.initialized()
            output = {"ok": True}
        elif probe.method == "tools/list":
            output = await client.list_tools()
        elif probe.method == "tools/call":
            output = await client.call_tool(
                probe.arguments["name"],
                probe.arguments.get("arguments", {}),
            )
        else:
            raise ValueError(f"Unsupported validation probe method: {probe.method}")

        return ValidationStepEvidence(
            name=probe.name,
            status="passed",
            output=str(output),
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
    except Exception as e:
        return ValidationStepEvidence(
            name=probe.name,
            status="failed",
            error=str(e),
            duration_ms=int((time.perf_counter() - started) * 1000),
        )
