from __future__ import annotations

import time
from typing import Any, Protocol

from .validation_evidence import ValidationEvidence, ValidationStepEvidence
from .validation_plan import ValidationPlan, ValidationProbeStep


class LightweightProbeClient(Protocol):
    async def initialize(self) -> dict[str, Any]: ...

    async def initialized(self) -> None: ...

    async def list_tools(self) -> list[dict[str, Any]]: ...

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


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
