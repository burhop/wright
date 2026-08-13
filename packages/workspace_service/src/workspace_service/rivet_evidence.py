"""Bounded redaction and artifact projection for Rivet run evidence."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from urllib.parse import unquote

from core.rivet_mcp import ArtifactReference, canonical_digest
from tool_registry.gateway_models import GatewayToolResult


_SECRET = re.compile(
    r"(?i)(token|secret|password|passwd|api[_-]?key|authorization|credential)"
)
_URL_SECRET = re.compile(r"(?i)([?&](?:token|access_token|api_key|key)=)[^&\s]+")


class RivetEvidenceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def redact_value(value: Any, *, maximum_text: int = 4096) -> tuple[Any, int]:
    redactions = 0

    def visit(item: Any) -> Any:
        nonlocal redactions
        if isinstance(item, Mapping):
            result: dict[str, Any] = {}
            for key, child in item.items():
                name = str(key)
                if _SECRET.search(name):
                    result[name] = "[redacted]"
                    redactions += 1
                else:
                    result[name] = visit(child)
            return result
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            return [visit(child) for child in item]
        if isinstance(item, str):
            sanitized, count = _URL_SECRET.subn(r"\1[redacted]", item)
            redactions += count
            if len(sanitized) > maximum_text:
                return sanitized[:maximum_text] + "…[truncated]"
            return sanitized
        return item

    return visit(value), redactions


def safe_argument_summary(
    arguments: Mapping[str, Any], *, maximum_bytes: int = 4096
) -> tuple[dict[str, Any], int, bool]:
    safe, redactions = redact_value(arguments)
    encoded = json.dumps(safe, sort_keys=True, default=str).encode("utf-8")
    if len(encoded) <= maximum_bytes:
        return dict(safe), redactions, False
    return (
        {
            "summary": "Arguments exceeded the evidence limit",
            "argument_digest": canonical_digest(arguments),
            "bytes": len(encoded),
        },
        redactions,
        True,
    )


def authorized_artifacts(
    result: GatewayToolResult, *, workspace_id: str
) -> tuple[ArtifactReference, ...]:
    prefix = f"wright://artifact/{workspace_id}/"
    artifacts: list[ArtifactReference] = []
    for item in result.content:
        if item.get("type") != "resource_link":
            continue
        uri = str(item.get("uri") or "")
        if not uri.startswith(prefix):
            raise RivetEvidenceError(
                "RIVET_MCP_ARTIFACT_DENIED",
                "Child artifact reference is not authorized for this workspace",
            )
        locator = unquote(uri.removeprefix(prefix))
        if (
            not locator
            or "\\" in locator
            or "\x00" in locator
            or any(part in {"", ".", ".."} for part in locator.split("/"))
        ):
            raise RivetEvidenceError(
                "RIVET_MCP_ARTIFACT_DENIED",
                "Child artifact reference is not authorized for this workspace",
            )
        digest = item.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise RivetEvidenceError(
                "RIVET_MCP_ARTIFACT_DENIED",
                "Child artifact reference has no verified digest",
            )
        artifacts.append(
            ArtifactReference(
                artifact_id=locator,
                media_type=str(item.get("mimeType") or "application/octet-stream"),
                sha256=digest,
                bytes=max(0, int(item.get("bytes") or 0)),
                label=str(item.get("name") or item.get("title") or locator)[:255],
            )
        )
    return tuple(artifacts)


def sanitize_gateway_result(
    result: GatewayToolResult, *, workspace_id: str
) -> tuple[GatewayToolResult, tuple[ArtifactReference, ...], int]:
    artifacts = authorized_artifacts(result, workspace_id=workspace_id)
    content, content_redactions = redact_value(result.content)
    structured, structured_redactions = redact_value(result.structured_content)
    meta, meta_redactions = redact_value(result.meta)
    return (
        GatewayToolResult(
            content=tuple(content),
            structured_content=(
                dict(structured) if isinstance(structured, Mapping) else None
            ),
            meta=dict(meta) if isinstance(meta, Mapping) else {},
            is_error=result.is_error,
            error_code=result.error_code,
        ),
        artifacts,
        content_redactions + structured_redactions + meta_redactions,
    )


_COMPARISONS = (
    ("workflow_digest", "workflow_changed", "review_current_workflow"),
    ("review_digest", "review_changed", "review_current_workflow"),
    ("binding_set_digest", "binding_set_changed", "review_current_bindings"),
    (
        "policy_snapshot_digest",
        "policy_snapshot_changed",
        "review_current_policy",
    ),
    ("runner_sha256", "runner_artifact_changed", "verify_current_runner"),
)


def compare_run_manifest(
    manifest: Mapping[str, Any], current: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare only pinned, non-secret identities and return stable recovery advice."""

    workflow = manifest.get("workflow")
    runtime = manifest.get("runtime")
    recorded = {
        "workflow_digest": (
            workflow.get("digest") if isinstance(workflow, Mapping) else None
        ),
        "review_digest": manifest.get("review_digest"),
        "binding_set_digest": manifest.get("binding_set_digest"),
        "policy_snapshot_digest": manifest.get("policy_snapshot_digest"),
        "runner_sha256": (
            runtime.get("runner_sha256") if isinstance(runtime, Mapping) else None
        ),
    }
    differences: list[dict[str, str]] = []
    for key, code, recovery in _COMPARISONS:
        if key not in current:
            continue
        expected = str(recorded.get(key) or "unavailable")[:512]
        actual = str(current.get(key) or "unavailable")[:512]
        if expected != actual:
            differences.append(
                {
                    "code": code,
                    "recorded": expected,
                    "current": actual,
                    "recovery_action": recovery,
                }
            )
    for code in tuple(dict.fromkeys(current.get("stale_reasons") or ())):
        value = str(code)[:128]
        if any(item["code"] == value for item in differences):
            continue
        differences.append(
            {
                "code": value,
                "recorded": "reviewed",
                "current": "changed",
                "recovery_action": "review_current_bindings",
            }
        )
    return {
        "reproducible": not differences,
        "differences": differences[:100],
        "summary": (
            "Recorded identities match the current reviewed configuration."
            if not differences
            else "A new review is required before reproducing this run."
        ),
    }


def _timestamp(value: Any, fallback: datetime) -> tuple[float, str]:
    if isinstance(value, (int, float)):
        instant = datetime.fromtimestamp(float(value), tz=UTC)
        return float(value), instant.isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        try:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return instant.timestamp(), instant.astimezone(UTC).isoformat().replace(
                "+00:00", "Z"
            )
        except ValueError:
            pass
    return fallback.timestamp(), fallback.isoformat().replace("+00:00", "Z")


def _safe_child_call(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value.get(key)
        for key in (
            "call_id",
            "request_id",
            "node_id",
            "binding_digest",
            "qualified_tool_name",
            "server_revision",
            "schema_digest",
            "validation_evidence_id",
            "argument_digest",
            "trace_id",
            "state",
            "child_received",
            "started_at",
            "completed_at",
            "reason_code",
            "artifacts",
            "redaction_count",
        )
    }


def _safe_approval(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value.get(key)
        for key in (
            "approval_id",
            "run_id",
            "node_id",
            "binding_digest",
            "server_id",
            "qualified_tool_name",
            "request_id",
            "argument_digest",
            "argument_summary",
            "required_gates",
            "state",
            "created_at",
            "expires_at",
            "decided_by",
            "decision_reason",
            "decided_at",
            "consumed_at",
        )
    }


def build_run_evidence(
    *,
    manifest: Mapping[str, Any],
    child_calls: Sequence[Mapping[str, Any]],
    approvals: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    current: Mapping[str, Any],
    maximum_records: int = 1000,
) -> dict[str, Any]:
    """Build one bounded restart-safe evidence export with complete correlations."""

    limit = max(1, min(maximum_records, 1000))
    safe_manifest, manifest_redactions = redact_value(dict(manifest))
    safe_calls, call_redactions = redact_value(
        [_safe_child_call(item) for item in child_calls[:limit]]
    )
    safe_approvals, approval_redactions = redact_value(
        [_safe_approval(item) for item in approvals[:limit]]
    )
    _, started_text = _timestamp(manifest.get("started_at"), datetime.now(UTC))
    started = datetime.fromisoformat(started_text.replace("Z", "+00:00"))
    timeline: list[tuple[float, int, dict[str, Any]]] = []

    for index, binding in enumerate(manifest.get("bindings") or ()):
        if isinstance(binding, Mapping):
            timeline.append(
                (
                    started.timestamp(),
                    index,
                    {
                        "kind": "binding",
                        "occurred_at": started_text,
                        "node_id": binding.get("node_id"),
                        "qualified_tool_name": binding.get("qualified_tool_name"),
                        "binding_digest": binding.get("binding_digest"),
                        "state": "reviewed",
                    },
                )
            )
    for event in events[:limit]:
        when, text = _timestamp(event.get("occurred_at"), started)
        payload, _ = redact_value(dict(event.get("payload") or {}))
        timeline.append(
            (
                when,
                int(event.get("sequence") or 0) + 10_000,
                {
                    "kind": str(event.get("kind") or "run-event")[:128],
                    "occurred_at": text,
                    "sequence": int(event.get("sequence") or 0),
                    "phase": payload.get("phase"),
                    "node_id": payload.get("nodeId") or payload.get("node_id"),
                    "request_id": payload.get("requestId") or payload.get("request_id"),
                    "state": payload.get("status"),
                    "reason_code": payload.get("code"),
                },
            )
        )
    for index, approval in enumerate(safe_approvals):
        when, text = _timestamp(approval.get("created_at"), started)
        timeline.append(
            (
                when,
                index + 20_000,
                {
                    "kind": "approval",
                    "occurred_at": text,
                    "node_id": approval.get("node_id"),
                    "request_id": approval.get("request_id"),
                    "qualified_tool_name": approval.get("qualified_tool_name"),
                    "state": approval.get("state"),
                    "approval_id": approval.get("approval_id"),
                },
            )
        )
    for index, call in enumerate(safe_calls):
        when, text = _timestamp(call.get("started_at"), started)
        timeline.append(
            (
                when,
                index + 30_000,
                {
                    "kind": "child-call",
                    "occurred_at": text,
                    "node_id": call.get("node_id"),
                    "request_id": call.get("request_id"),
                    "qualified_tool_name": call.get("qualified_tool_name"),
                    "trace_id": call.get("trace_id"),
                    "state": call.get("state"),
                    "reason_code": call.get("reason_code"),
                    "child_received": call.get("child_received"),
                    "call_id": call.get("call_id"),
                },
            )
        )
    timeline.sort(key=lambda item: (item[0], item[1]))
    timeline_truncated = len(timeline) > limit
    call_requests = {
        str(item.get("request_id"))
        for item in safe_calls
        if item.get("child_received") is True
    }
    denied_before_child = sum(
        1
        for item in safe_approvals
        if str(item.get("state")) in {"denied", "expired", "cancelled"}
        and str(item.get("request_id")) not in call_requests
    )
    recorded_call_ids = {
        str(item.get("call_id")) for item in safe_calls if item.get("call_id")
    }
    recorded_approval_ids = {
        str(item.get("approval_id"))
        for item in safe_approvals
        if item.get("approval_id")
    }
    referenced_call_ids = {str(item) for item in manifest.get("child_call_ids") or ()}
    referenced_approval_ids = {str(item) for item in manifest.get("approval_ids") or ()}
    missing_call_ids = sorted(referenced_call_ids - recorded_call_ids)
    missing_approval_ids = sorted(referenced_approval_ids - recorded_approval_ids)
    evidence = {
        "schema_version": 1,
        "run_id": manifest.get("run_id"),
        "manifest": safe_manifest,
        "bindings": list(manifest.get("bindings") or ())[:100],
        "child_calls": safe_calls,
        "approvals": safe_approvals,
        "artifacts": list(manifest.get("artifacts") or ())[:limit],
        "timeline": [item[2] for item in timeline[:limit]],
        "reproducibility": compare_run_manifest(manifest, current),
        "accounting": {
            "binding_count": len(manifest.get("bindings") or ()),
            "child_call_count": len(child_calls),
            "approval_count": len(approvals),
            "artifact_count": len(manifest.get("artifacts") or ()),
            "denied_before_child_count": denied_before_child,
            "referenced_child_calls_accounted": not missing_call_ids,
            "referenced_approvals_accounted": not missing_approval_ids,
            "complete": not missing_call_ids and not missing_approval_ids,
            "redaction_count": int(manifest.get("redaction_count") or 0)
            + manifest_redactions
            + call_redactions
            + approval_redactions,
            "truncated": bool(
                timeline_truncated
                or len(child_calls) > limit
                or len(approvals) > limit
                or len(events) > limit
                or manifest.get("event_truncated")
                or manifest.get("output_truncated")
            ),
        },
    }
    normalized = json.loads(json.dumps(evidence, sort_keys=True, default=str))
    if len(json.dumps(normalized, sort_keys=True).encode("utf-8")) > 2 * 1024 * 1024:
        raise RivetEvidenceError(
            "RIVET_MCP_EVIDENCE_TOO_LARGE",
            "Run evidence exceeds the export limit",
        )
    return normalized


__all__ = [
    "RivetEvidenceError",
    "authorized_artifacts",
    "build_run_evidence",
    "compare_run_manifest",
    "redact_value",
    "safe_argument_summary",
    "sanitize_gateway_result",
]
