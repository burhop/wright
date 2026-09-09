"""Read the evidence-backed engineering MCP portfolio status artifact."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from importlib.resources import files
from typing import Any


STATUS_RESOURCE = "engineering-status.json"
MAX_STATUS_BYTES = 4 * 1024 * 1024


class EngineeringStatusError(ValueError):
    """The bundled portfolio status artifact is missing or invalid."""


def _load_status_bytes() -> bytes:
    resource = files("tool_registry.catalog").joinpath(STATUS_RESOURCE)
    value = resource.read_bytes()
    if len(value) > MAX_STATUS_BYTES:
        raise EngineeringStatusError("Engineering MCP status exceeds its size limit")
    return value


def _validate_status(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise EngineeringStatusError("Unsupported engineering MCP status format")
    records = value.get("records")
    counts = value.get("counts")
    evidence = value.get("evidence_payloads")
    if not isinstance(records, list) or not isinstance(counts, dict):
        raise EngineeringStatusError("Engineering MCP status is incomplete")
    if sum(
        int(counts.get(key, 0)) for key in ("curated", "follow_up", "removed")
    ) != len(records):
        raise EngineeringStatusError(
            "Engineering MCP disposition counts do not match records"
        )
    identities = [
        record.get("server_id") for record in records if isinstance(record, dict)
    ]
    if len(identities) != len(records) or len(set(identities)) != len(identities):
        raise EngineeringStatusError(
            "Engineering MCP status contains duplicate records"
        )
    if not isinstance(evidence, dict):
        raise EngineeringStatusError("Engineering MCP evidence payloads are missing")
    for evidence_id, payload in evidence.items():
        if not isinstance(evidence_id, str) or not isinstance(payload, dict):
            raise EngineeringStatusError("Engineering MCP evidence index is malformed")
        content = payload.get("content")
        digest = payload.get("sha256")
        if not isinstance(content, str) or not isinstance(digest, str):
            raise EngineeringStatusError(
                "Engineering MCP evidence payload is malformed"
            )
        if hashlib.sha256(content.encode("utf-8")).hexdigest() != digest:
            raise EngineeringStatusError("Engineering MCP evidence digest mismatch")
        try:
            json.loads(content)
        except json.JSONDecodeError as error:
            raise EngineeringStatusError(
                "Engineering MCP evidence is not JSON"
            ) from error
    return value


def load_engineering_status(*, include_evidence: bool = False) -> dict[str, Any]:
    """Load and verify the bundled status; omit bulky evidence from list responses."""
    try:
        value = json.loads(_load_status_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise EngineeringStatusError("Engineering MCP status is unavailable") from error
    result = deepcopy(_validate_status(value))
    if not include_evidence:
        result.pop("evidence_payloads", None)
    return result


def load_engineering_status_evidence(evidence_id: str) -> tuple[str, str]:
    if not evidence_id or len(evidence_id) > 160:
        raise EngineeringStatusError("Unknown engineering MCP evidence")
    status = load_engineering_status(include_evidence=True)
    payload = status["evidence_payloads"].get(evidence_id)
    if payload is None:
        raise EngineeringStatusError("Unknown engineering MCP evidence")
    return payload["content"], payload["sha256"]
