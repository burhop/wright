"""Validate optional portable presentation data."""

import json
import math
import re

_LAYOUT_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,159}$")
WORKFLOW_LAYOUT_MAX_BYTES = 256 * 1024


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def validate_source_layout(value: object) -> dict[str, object]:
    """Bound presentation data without parsing or taking authority over source.

    Canonical block membership is validated by the caller's command layer;
    this storage boundary validates only the closed layout shape and limits.
    """

    def invalid() -> None:
        raise ValueError("Workflow layout has an invalid shape or value")

    def number(item: object, minimum: float, maximum: float) -> bool:
        return (
            not isinstance(item, bool)
            and isinstance(item, (int, float))
            and minimum <= item <= maximum
            and math.isfinite(item)
        )

    if not isinstance(value, dict) or set(value) != {
        "documentKind",
        "schemaVersion",
        "workflowId",
        "semanticRevision",
        "layoutRevision",
        "positions",
        "viewport",
    }:
        invalid()
    if (
        value["documentKind"] != "workflow-layout"
        or value["schemaVersion"] != "1.0.0-recovery.1"
        or not isinstance(value["workflowId"], str)
        or not _LAYOUT_ID.fullmatch(value["workflowId"])
        or _positive_int(value["semanticRevision"]) is None
        or _positive_int(value["layoutRevision"]) is None
    ):
        invalid()
    positions = value["positions"]
    if not isinstance(positions, dict) or len(positions) > 4000:
        invalid()
    for identity, point in positions.items():
        if (
            not isinstance(identity, str)
            or not _LAYOUT_ID.fullmatch(identity)
            or not isinstance(point, dict)
            or set(point) != {"x", "y"}
            or not all(
                number(point[key], -10_000_000, 10_000_000) for key in ("x", "y")
            )
        ):
            invalid()
    viewport = value["viewport"]
    if (
        not isinstance(viewport, dict)
        or set(viewport) != {"x", "y", "zoom"}
        or not all(number(viewport[key], -10_000_000, 10_000_000) for key in ("x", "y"))
        or not number(viewport["zoom"], 0.000001, 64)
    ):
        invalid()
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > WORKFLOW_LAYOUT_MAX_BYTES:
        invalid()
    return json.loads(encoded)
