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
