"""Focused fixtures for canonical engineering workflow template tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


TEMPLATE_IDS = (
    "printed-replacement-part",
    "raspberry-pi-enclosure",
    "sheet-metal-supplier-handoff",
    "lightweight-equipment-bracket",
    "sensor-interface-pcb",
    "parametric-drill-jig",
    "robot-tracking-diagnosis",
    "heat-spreader-sizing",
    "sensor-fan-harness",
    "water-heater-sizing",
)


def template_resource_root() -> Path:
    return (
        Path(__file__).parents[1]
        / "src"
        / "workspace_service"
        / "engineering_workflow_templates"
    )


def load_catalog_document() -> dict[str, Any]:
    value = yaml.safe_load(
        (template_resource_root() / "catalog.yaml").read_text("utf-8")
    )
    assert isinstance(value, dict)
    return value


def assert_frozen_sdk_reasoning(plan):
    """Routing-only check on an existing engineering plan; no tool dispatch."""
    import asyncio
    import json
    from types import SimpleNamespace

    import pytest
    from agent_adapters.workflow_sdk import sdk_workflow_resolution
    from workspace_service.workflow_model_routing import freeze_workflow_model_routing
    from workspace_service.workflow_source_execution import WorkflowSourceExecutionError

    native = {
        "provider": "openai-codex",
        "model_reference": "gpt-6-astra",
        "api_mode": "codex_responses",
        "endpoint_digest": "a" * 64,
        "sdk_digest": "b" * 64,
        "reasoning_effort": "high",
    }

    async def capabilities():
        return {"available": True, "resolution": sdk_workflow_resolution(native)}

    service = SimpleNamespace(workflow_model_capabilities=capabilities)
    bound, context = asyncio.run(freeze_workflow_model_routing(service, plan, None))
    assert any(step.model_resolution for step in bound.steps)
    persisted = json.loads(json.dumps(context))
    resumed, _ = asyncio.run(
        freeze_workflow_model_routing(service, plan, None, persisted)
    )
    assert resumed == bound
    native["reasoning_effort"] = "low"
    with pytest.raises(WorkflowSourceExecutionError) as failure:
        asyncio.run(freeze_workflow_model_routing(service, plan, None, persisted))
    assert failure.value.code == "WORKFLOW_MODEL_CHANGED"
