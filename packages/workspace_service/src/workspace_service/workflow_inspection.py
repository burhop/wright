"""Authoritative, refresh-safe projection of one persisted Rivet workflow run."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from data_vault import WorkflowRunRecord

from .rivet_evidence import project_result_value, redact_value


_TERMINAL = {"cancelled", "succeeded", "failed"}
_DIAGNOSTICS: dict[str, tuple[str, str]] = {
    "RIVET_MCP_BRIDGE_DENIED": (
        "Wright stopped this MCP call before it reached the selected server.",
        "Refresh the workflow's tool connections and run the saved revision again.",
    ),
    "RIVET_MCP_CALL_CANCELLED": (
        "The MCP call ended before the selected server returned a result.",
        "Run the saved revision again. If it repeats, inspect the technical identifiers.",
    ),
    "RIVET_MCP_GENERATION_REPLACED": (
        "The MCP server was explicitly restarted while this step was running.",
        "Wait for the server to become active, then run the saved revision again.",
    ),
    "RIVET_MCP_TRANSPORT_CANCELLED": (
        "The remote MCP connection ended while this step was running.",
        "Reconnect the MCP server and run the saved revision again.",
    ),
    "RIVET_MCP_RESIDUE_POSSIBLE": (
        "Cancellation could not confirm that the engineering operation stopped cleanly.",
        "Inspect the target engineering application before running the workflow again.",
    ),
    "RIVET_MCP_PANEL_UNAVAILABLE": (
        "The engineering application panel was unavailable for this step.",
        "Reopen the application panel, inspect its state, and run the saved revision again.",
    ),
    "RIVET_MCP_HOST_BRIDGE_UNAVAILABLE": (
        "Wright could not reach the engineering application's host bridge.",
        "Inspect or restart the engineering application, then run the saved revision again.",
    ),
    "timeout": (
        "The workflow did not finish before its configured deadline.",
        "Check the failed step and run again with an appropriate timeout.",
    ),
    "cancelled": (
        "The workflow was cancelled.",
        "Run the saved revision again when you are ready.",
    ),
}


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        instant = value.astimezone(UTC)
    elif isinstance(value, (int, float)):
        instant = datetime.fromtimestamp(float(value), tz=UTC)
    elif isinstance(value, str):
        try:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
                UTC
            )
        except ValueError:
            return None
    else:
        return None
    return instant.isoformat().replace("+00:00", "Z")


def _epoch(value: Any) -> float | None:
    normalized = _iso(value)
    if normalized is None:
        return None
    return datetime.fromisoformat(normalized.replace("Z", "+00:00")).timestamp()


def _duration_ms(started: Any, completed: Any) -> int | None:
    first, last = _epoch(started), _epoch(completed)
    if first is None or last is None:
        return None
    return max(0, round((last - first) * 1000))


def _event_document(event: Any) -> dict[str, Any]:
    payload, _ = redact_value(dict(getattr(event, "payload", {}) or {}))
    return {
        "sequence": int(getattr(event, "sequence", 0)),
        "kind": str(getattr(event, "kind", "event")),
        "occurred_at": _iso(getattr(event, "occurred_at", None)),
        "payload": payload,
    }


def _step_document(value: Mapping[str, Any], sequence: int) -> dict[str, Any]:
    qualified = str(value.get("qualified_tool_name") or "MCP tool call")
    result = value.get("result")
    if not isinstance(result, Mapping):
        result = None
    artifacts = [
        dict(item) for item in value.get("artifacts") or () if isinstance(item, Mapping)
    ]
    return {
        "step_id": str(value.get("call_id") or f"step-{sequence}"),
        "sequence": sequence,
        "node_id": str(value.get("node_id")) if value.get("node_id") else None,
        "label": str(
            value.get("label") or qualified.replace("__", " · ").replace("_", " ")
        ),
        "kind": "mcp_call",
        "qualified_tool_name": qualified,
        "request_id": str(value.get("request_id")) if value.get("request_id") else None,
        "trace_id": str(value.get("trace_id")) if value.get("trace_id") else None,
        "state": str(value.get("state") or "unknown"),
        "started_at": _iso(value.get("started_at")),
        "completed_at": _iso(value.get("completed_at")),
        "duration_ms": _duration_ms(value.get("started_at"), value.get("completed_at")),
        "reason_code": str(value.get("reason_code"))
        if value.get("reason_code")
        else None,
        "result": dict(result) if result is not None else None,
        "artifacts": artifacts,
        "redaction_count": max(0, int(value.get("redaction_count") or 0)),
        "complete": value.get("result_complete") is not False,
    }


def _final_outputs(record: WorkflowRunRecord) -> list[dict[str, Any]]:
    summary = record.output_summary or {}
    current = summary.get("results")
    if isinstance(current, list):
        return [dict(item) for item in current if isinstance(item, Mapping)]
    outputs = summary.get("outputs")
    if not isinstance(outputs, Mapping):
        return []
    return [
        project_result_value(
            value, name=str(name), origin="final_output", maximum_bytes=64 * 1024
        )
        for name, value in sorted(outputs.items(), key=lambda item: str(item[0]))
    ]


def build_run_summary(
    record: WorkflowRunRecord, *, latest_sequence: int
) -> dict[str, Any]:
    started_at = _iso(record.started_at)
    completed_at = _iso(record.completed_at)
    duration = _duration_ms(record.started_at, record.completed_at)
    if duration is None and isinstance(record.output_summary, Mapping):
        raw_duration = record.output_summary.get("durationMs")
        duration = int(raw_duration) if isinstance(raw_duration, (int, float)) else None
    outputs = _final_outputs(record)
    return {
        "run_id": record.run_id,
        "workspace_id": record.workspace_id,
        "session_id": record.session_id,
        "workflow_id": record.workflow_id,
        "revision": record.revision,
        "digest": record.digest,
        "graph": record.graph,
        "generation": record.generation,
        "state": record.state,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": duration,
        "reason_code": record.reason_code,
        "trace_id": record.trace_id,
        "latest_sequence": latest_sequence,
        "has_outputs": bool(outputs),
        "has_diagnostic": bool(record.reason_code),
        "output_truncated": record.output_truncated,
        "output_redaction_count": sum(
            max(0, int(item.get("redaction_count") or 0)) for item in outputs
        ),
    }


def build_workflow_inspection(
    *,
    record: WorkflowRunRecord,
    events: Sequence[Any],
    incremental_events: Sequence[Any],
    child_calls: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    ordered_events = sorted(events, key=lambda item: int(getattr(item, "sequence", 0)))
    latest_sequence = (
        int(getattr(ordered_events[-1], "sequence", 0)) if ordered_events else 0
    )
    steps = [
        _step_document(item, sequence)
        for sequence, item in enumerate(
            sorted(
                child_calls,
                key=lambda item: (
                    _epoch(item.get("started_at")) or 0,
                    str(item.get("call_id") or ""),
                ),
            ),
            start=1,
        )
    ]
    outputs = _final_outputs(record)
    failed_step = next(
        (step for step in reversed(steps) if step["state"] == "failed"), None
    )
    reason = record.reason_code or (failed_step or {}).get("reason_code")
    diagnostic = None
    if reason:
        summary, recovery = _DIAGNOSTICS.get(
            str(reason),
            (
                "The workflow stopped before every step completed.",
                "Inspect the failed step and run the saved revision again.",
            ),
        )
        residue = str(reason) == "RIVET_MCP_RESIDUE_POSSIBLE" or bool(
            (manifest or {}).get("residue_possible")
        )
        diagnostic = {
            "code": str(reason),
            "summary": summary,
            "recovery_action": recovery,
            "failed_step_id": (failed_step or {}).get("step_id"),
            "failed_node_id": (failed_step or {}).get("node_id"),
            "qualified_tool_name": (failed_step or {}).get("qualified_tool_name"),
            "trace_id": (failed_step or {}).get("trace_id") or record.trace_id,
            "full_rerun_available": record.state in _TERMINAL,
            "partial_retry_available": False,
            "residue_possible": residue,
        }
    latest_event = ordered_events[-1] if ordered_events else None
    latest_payload = dict(getattr(latest_event, "payload", {}) or {})
    terminal_steps = sum(step["state"] in _TERMINAL for step in steps)
    reasons: list[str] = []
    if record.output_truncated or any(
        not item.get("complete", True) for item in outputs
    ):
        reasons.append("outputs_truncated")
    if any(not step["complete"] for step in steps):
        reasons.append("step_results_truncated")
    if bool((manifest or {}).get("event_truncated")):
        reasons.append("events_truncated")
    return {
        "schema_version": 1,
        "run": build_run_summary(record, latest_sequence=latest_sequence),
        "progress": {
            "phase": str(
                latest_payload.get("phase")
                or getattr(latest_event, "kind", record.state)
            ),
            "current_step_id": next(
                (
                    step["step_id"]
                    for step in reversed(steps)
                    if step["state"] not in _TERMINAL
                ),
                None,
            ),
            "completed_steps": terminal_steps,
            "total_steps": len(steps),
            "last_sequence": latest_sequence,
            "updated_at": _iso(getattr(latest_event, "occurred_at", None))
            or _iso(record.completed_at)
            or _iso(record.started_at),
        },
        "events": [_event_document(item) for item in incremental_events],
        "steps": steps,
        "final_outputs": outputs,
        "diagnostic": diagnostic,
        "completeness": {
            "outputs_complete": "outputs_truncated" not in reasons,
            "steps_complete": "step_results_truncated" not in reasons,
            "events_complete": "events_truncated" not in reasons,
            "evidence_available": manifest is not None or bool(child_calls),
            "reasons": reasons,
        },
    }


__all__ = ["build_run_summary", "build_workflow_inspection"]
