"""Authoritative, refresh-safe projection of one persisted Rivet workflow run."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from data_vault import WorkflowRunRecord

from .rivet_evidence import (
    normalize_rivet_output_value,
    project_result_value,
    redact_value,
)


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


def _bounded_text(value: Any, *, maximum: int = 255) -> str | None:
    if not isinstance(value, (str, int, float)):
        return None
    text = str(value).strip()
    return text[:maximum] if text else None


def _uuid_like(value: str | None) -> bool:
    if not value:
        return False
    try:
        UUID(value)
    except ValueError:
        return False
    return True


def _primary_label(value: Any, *, node_id: str | None = None) -> str | None:
    label = _bounded_text(value)
    if label is None or label == node_id or _uuid_like(label):
        return None
    return label


def _tool_action_label(value: Any) -> str:
    qualified = _bounded_text(value, maximum=512)
    if qualified is None:
        return "MCP tool call"
    action = qualified.rsplit("__", 1)[-1].rsplit(".", 1)[-1]
    label = _primary_label(action.replace("_", " ").replace("-", " "))
    return label or "MCP tool call"


def _event_payload(event: Any) -> tuple[dict[str, Any], int]:
    safe, redactions = redact_value(dict(getattr(event, "payload", {}) or {}))
    return (dict(safe) if isinstance(safe, Mapping) else {}), redactions


def _event_document(event: Any) -> dict[str, Any]:
    payload, _ = _event_payload(event)
    return {
        "sequence": int(getattr(event, "sequence", 0)),
        "kind": str(getattr(event, "kind", "event")),
        "occurred_at": _iso(getattr(event, "occurred_at", None)),
        "payload": payload,
    }


def _retained_results(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    results: list[dict[str, Any]] = []
    for item in value[:64]:
        if not isinstance(item, Mapping):
            continue
        retained = dict(item)
        retained.setdefault("data_type", str(retained.get("kind") or "unknown"))
        retained.setdefault(
            "evidence_state",
            "available" if retained.get("complete") is not False else "truncated",
        )
        results.append(retained)
    return results


def _inspection_context(
    events: Sequence[Any], record: WorkflowRunRecord
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]], str]:
    for event in events:
        if str(getattr(event, "kind", "")) != "inspection-context":
            continue
        payload, _ = _event_payload(event)
        if (
            int(payload.get("revision") or 0) != record.revision
            or str(payload.get("digest") or "") != record.digest
        ):
            continue
        run_inputs = _retained_results(payload.get("runInputs"))
        nodes = [
            {
                "node_id": _bounded_text(item.get("node_id"), maximum=128),
                "node_type": _bounded_text(item.get("node_type"), maximum=64),
                "label": _primary_label(
                    item.get("label"),
                    node_id=_bounded_text(item.get("node_id"), maximum=128),
                ),
                "order": max(1, int(item.get("order") or index)),
            }
            for index, item in enumerate(payload.get("graphNodes") or (), start=1)
            if isinstance(item, Mapping)
        ][:100]
        return (
            run_inputs,
            str(payload.get("inputsState") or "unavailable"),
            nodes,
            str(payload.get("inventoryState") or "unavailable"),
        )
    return [], "not-retained", [], "not-retained"


def _step_document(value: Mapping[str, Any], sequence: int) -> dict[str, Any]:
    node_id = _bounded_text(value.get("node_id"), maximum=256)
    node_type = _bounded_text(value.get("node_type"), maximum=128)
    qualified = _bounded_text(value.get("qualified_tool_name"), maximum=512)
    explicit_label = (
        _primary_label(value.get("label"), node_id=node_id)
        or _primary_label(value.get("tool_title"), node_id=node_id)
        or _primary_label(value.get("action"), node_id=node_id)
    )
    label = explicit_label or _tool_action_label(qualified)
    result = value.get("result")
    if not isinstance(result, Mapping):
        result = None
    artifacts = [
        dict(item) for item in value.get("artifacts") or () if isinstance(item, Mapping)
    ]
    return {
        "step_id": str(value.get("call_id") or f"step-{sequence}"),
        "sequence": sequence,
        "node_id": node_id,
        "node_type": node_type,
        "label": label,
        "_label_rank": 2,
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
        "inputs": [],
        "outputs": [dict(result)] if result is not None else [],
        "input_state": "not-retained",
        "output_state": (
            str(result.get("evidence_state") or "available")
            if result is not None
            else "unavailable"
        ),
        "result": dict(result) if result is not None else None,
        "artifacts": artifacts,
        "redaction_count": max(0, int(value.get("redaction_count") or 0)),
        "complete": value.get("result_complete") is not False,
    }


def _lifecycle_steps(
    events: Sequence[Any], inventory: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    steps_by_node: dict[tuple[str, ...], dict[str, Any]] = {}
    for item in inventory:
        node_id = _bounded_text(item.get("node_id"), maximum=128)
        node_type = _bounded_text(item.get("node_type"), maximum=64)
        node_title = _primary_label(item.get("label"), node_id=node_id)
        key = (
            ("node", node_id)
            if node_id is not None
            else ("inventoried", node_type or "", node_title or "")
        )
        order = max(1, int(item.get("order") or len(steps_by_node) + 1))
        steps_by_node[key] = {
            "step_id": f"node:{node_id}" if node_id else f"inventory:{order}",
            "sequence": order,
            "node_id": node_id,
            "node_type": node_type,
            "label": node_title or node_type or "Workflow box",
            "_label_rank": 3 if node_title else (1 if node_type else 0),
            "_order": 1_000_000 + order,
            "_has_lifecycle": False,
            "kind": "node",
            "qualified_tool_name": None,
            "request_id": None,
            "trace_id": None,
            "state": "not-run",
            "started_at": None,
            "completed_at": None,
            "duration_ms": None,
            "reason_code": None,
            "inputs": [],
            "outputs": [],
            "input_state": "not-run",
            "output_state": "not-run",
            "result": None,
            "artifacts": [],
            "redaction_count": 0,
            "complete": True,
        }
    for event in events:
        payload, redactions = _event_payload(event)
        phase = _bounded_text(payload.get("phase"), maximum=64)
        if phase not in {
            "node-start",
            "node-finish",
            "node-error",
            "node-excluded",
        }:
            continue
        event_sequence = int(getattr(event, "sequence", 0))
        node_id = _bounded_text(
            payload.get("nodeId") or payload.get("node_id"), maximum=256
        )
        node_type = _bounded_text(
            payload.get("nodeType") or payload.get("node_type"), maximum=128
        )
        node_title = _primary_label(
            payload.get("nodeTitle") or payload.get("node_title"), node_id=node_id
        )
        key = (
            ("node", node_id)
            if node_id is not None
            else ("observed", node_type or "", node_title or "")
        )
        step = steps_by_node.get(key)
        if step is None:
            label = node_title or node_type or "Workflow node"
            step = {
                "step_id": f"node:{node_id}"
                if node_id
                else f"node-event:{event_sequence}",
                "sequence": event_sequence,
                "node_id": node_id,
                "node_type": node_type,
                "label": label,
                "_label_rank": 3 if node_title else (1 if node_type else 0),
                "_order": event_sequence,
                "_has_lifecycle": True,
                "kind": "node",
                "qualified_tool_name": None,
                "request_id": None,
                "trace_id": None,
                "state": "unknown",
                "started_at": None,
                "completed_at": None,
                "duration_ms": None,
                "reason_code": None,
                "inputs": [],
                "outputs": [],
                "input_state": "unavailable",
                "output_state": "unavailable",
                "result": None,
                "artifacts": [],
                "redaction_count": 0,
                "complete": True,
            }
            steps_by_node[key] = step
        if node_title and step["_label_rank"] < 3:
            step["label"] = node_title
            step["_label_rank"] = 3
        elif node_type and step["_label_rank"] < 1:
            step["label"] = node_type
            step["_label_rank"] = 1
        if step["node_type"] is None:
            step["node_type"] = node_type
        step["_has_lifecycle"] = True
        step["_order"] = min(step["_order"], event_sequence)
        step["redaction_count"] += redactions
        occurred_at = _iso(getattr(event, "occurred_at", None))
        if phase == "node-start":
            step["started_at"] = step["started_at"] or occurred_at
            step["state"] = "running"
            step["inputs"] = _retained_results(payload.get("inputValues"))
            step["input_state"] = str(
                payload.get("inputState")
                or ("available" if step["inputs"] else "unavailable")
            )
        elif phase == "node-excluded":
            step["state"] = "not-run"
            step["completed_at"] = occurred_at or step["completed_at"]
            step["reason_code"] = _bounded_text(
                payload.get("exclusionReason"), maximum=255
            )
            step["inputs"] = _retained_results(payload.get("inputValues"))
            step["outputs"] = _retained_results(payload.get("outputValues"))
            step["input_state"] = str(payload.get("inputState") or "not-run")
            step["output_state"] = str(payload.get("outputState") or "not-run")
        else:
            step["completed_at"] = occurred_at or step["completed_at"]
            if phase == "node-error":
                step["state"] = "failed"
                step["output_state"] = str(payload.get("outputState") or "no-value")
                step["reason_code"] = _bounded_text(
                    payload.get("errorCode")
                    or payload.get("error_code")
                    or payload.get("code"),
                    maximum=128,
                )
            elif step["state"] != "failed":
                step["state"] = "succeeded"
                step["outputs"] = _retained_results(payload.get("outputValues"))
                step["output_state"] = str(
                    payload.get("outputState")
                    or ("available" if step["outputs"] else "unavailable")
                )
        trace_id = _bounded_text(
            payload.get("traceId") or payload.get("trace_id"), maximum=256
        )
        step["trace_id"] = trace_id or step["trace_id"]
        retained_duration = payload.get("durationMs")
        step["duration_ms"] = (
            max(0, round(float(retained_duration)))
            if isinstance(retained_duration, (int, float))
            else _duration_ms(step["started_at"], step["completed_at"])
        )
    for step in steps_by_node.values():
        if not step["_has_lifecycle"]:
            continue
        step["complete"] = step["input_state"] not in {
            "truncated",
            "unavailable",
        } and step["output_state"] not in {"truncated", "unavailable"}
    return list(steps_by_node.values())


def _first_time(*values: Any) -> str | None:
    candidates = [
        (epoch, _iso(value)) for value in values if (epoch := _epoch(value)) is not None
    ]
    return min(candidates, default=(0, None), key=lambda item: item[0])[1]


def _last_time(*values: Any) -> str | None:
    candidates = [
        (epoch, _iso(value)) for value in values if (epoch := _epoch(value)) is not None
    ]
    return max(candidates, default=(0, None), key=lambda item: item[0])[1]


def _merge_child_step(step: dict[str, Any], child: dict[str, Any]) -> None:
    child_is_first = not step.get("_child_seen")
    child_failed = child["state"] == "failed"
    if child["_label_rank"] > step["_label_rank"]:
        step["label"] = child["label"]
        step["_label_rank"] = child["_label_rank"]
    step["kind"] = "mcp_call"
    if child_is_first or child_failed:
        step["step_id"] = child["step_id"]
        step["qualified_tool_name"] = child["qualified_tool_name"]
        step["request_id"] = child["request_id"]
        step["trace_id"] = child["trace_id"] or step["trace_id"]
        if child["result"] is not None:
            step["result"] = child["result"]
            step["outputs"] = child["outputs"]
            step["output_state"] = child["output_state"]
    if child_failed:
        step["state"] = "failed"
        step["reason_code"] = child["reason_code"] or step["reason_code"]
    elif not step.get("_has_lifecycle"):
        if child["state"] not in _TERMINAL:
            step["state"] = child["state"]
        elif step["state"] not in {"failed", "cancelled"}:
            step["state"] = child["state"]
        step["reason_code"] = step["reason_code"] or child["reason_code"]
    step["started_at"] = _first_time(step["started_at"], child["started_at"])
    step["completed_at"] = _last_time(step["completed_at"], child["completed_at"])
    step["duration_ms"] = _duration_ms(step["started_at"], step["completed_at"])
    step["artifacts"].extend(child["artifacts"])
    step["redaction_count"] += child["redaction_count"]
    step["complete"] = step["complete"] and child["complete"]
    step["_order"] = min(step["_order"], child["_order"])
    step["_child_seen"] = True


def _merged_steps(
    events: Sequence[Any],
    child_calls: Sequence[Mapping[str, Any]],
    inventory: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    steps = _lifecycle_steps(events, inventory)
    by_node = {
        step["node_id"]: step for step in steps if step.get("node_id") is not None
    }
    ordered_calls = sorted(
        child_calls,
        key=lambda item: (
            _epoch(item.get("started_at")) or 0,
            str(item.get("call_id") or ""),
        ),
    )
    for index, item in enumerate(ordered_calls, start=1):
        child = _step_document(item, index)
        child["_order"] = 1_000_000 + index
        child["_has_lifecycle"] = False
        node_id = child.get("node_id")
        step = by_node.get(node_id) if node_id is not None else None
        if step is None:
            step = child
            steps.append(step)
            if node_id is not None:
                by_node[node_id] = step
        else:
            _merge_child_step(step, child)

    def ordering(step: Mapping[str, Any]) -> tuple[float, int]:
        observed_at = _epoch(step.get("started_at") or step.get("completed_at"))
        return (
            observed_at if observed_at is not None else float("inf"),
            int(step["_order"]),
        )

    steps.sort(key=ordering)
    for sequence, step in enumerate(steps, start=1):
        step["sequence"] = sequence
        for private in ("_label_rank", "_order", "_has_lifecycle", "_child_seen"):
            step.pop(private, None)
    return steps


def _final_outputs(record: WorkflowRunRecord) -> list[dict[str, Any]]:
    summary = record.output_summary or {}
    current = summary.get("results")
    if isinstance(current, list):
        outputs: list[dict[str, Any]] = []
        for item in current:
            if not isinstance(item, Mapping):
                continue
            stored = dict(item)
            stored.setdefault("data_type", str(stored.get("kind") or "unknown"))
            stored.setdefault(
                "evidence_state",
                "available" if stored.get("complete") is not False else "truncated",
            )
            value = stored.get("value")
            normalized = normalize_rivet_output_value(value)
            if normalized is value or stored.get("complete") is False:
                outputs.append(stored)
                continue
            projected = project_result_value(
                normalized,
                name=str(stored.get("name") or "result"),
                origin=str(stored.get("origin") or "final_output"),
                maximum_bytes=64 * 1024,
                artifact=(
                    stored.get("artifact")
                    if isinstance(stored.get("artifact"), Mapping)
                    else None
                ),
            )
            projected["result_id"] = str(
                stored.get("result_id") or projected["result_id"]
            )
            projected["redaction_count"] = max(
                projected["redaction_count"],
                max(0, int(stored.get("redaction_count") or 0)),
            )
            outputs.append(projected)
        return outputs
    outputs = summary.get("outputs")
    if not isinstance(outputs, Mapping):
        return []
    return [
        project_result_value(
            value,
            name=str(name),
            origin="final_output",
            maximum_bytes=64 * 1024,
        )
        for name, value in sorted(outputs.items(), key=lambda item: str(item[0]))
    ]


def _artifact_outputs(manifest: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in (manifest or {}).get("artifacts") or ():
        if not isinstance(item, Mapping):
            continue
        artifact_id = _bounded_text(item.get("artifact_id"), maximum=512)
        digest = _bounded_text(item.get("sha256"), maximum=64)
        media_type = _bounded_text(item.get("media_type"), maximum=255)
        if not artifact_id or not digest or len(digest) != 64 or not media_type:
            continue
        label = _bounded_text(item.get("label"), maximum=255) or artifact_id
        artifact = {
            "artifact_id": artifact_id,
            "media_type": media_type,
            "sha256": digest,
            "bytes": max(0, int(item.get("bytes") or 0)),
            "label": label,
        }
        result = project_result_value(
            {
                "media_type": media_type,
                "bytes": artifact["bytes"],
                "sha256": digest,
            },
            name=label,
            origin="artifact",
            artifact=artifact,
            data_type="artifact-reference",
        )
        result["result_id"] = f"artifact:{artifact_id}"
        results.append(result)
    return results


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
        "has_diagnostic": bool(record.reason_code)
        or record.state in {"failed", "cancelled"},
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
    run_inputs, inputs_state, inventory, inventory_state = _inspection_context(
        ordered_events, record
    )
    steps = _merged_steps(ordered_events, child_calls, inventory)
    artifacts = _artifact_outputs(manifest)
    artifact_ids = {
        str((item.get("artifact") or {}).get("artifact_id"))
        for item in artifacts
        if isinstance(item.get("artifact"), Mapping)
    }
    outputs = artifacts + [
        item
        for item in _final_outputs(record)
        if not (
            isinstance(item.get("artifact"), Mapping)
            and str(item["artifact"].get("artifact_id")) in artifact_ids
        )
    ]
    failed_step = next(
        (step for step in reversed(steps) if step["state"] == "failed"), None
    )
    reason = (
        record.reason_code
        or (failed_step or {}).get("reason_code")
        or ("RIVET_RUN_FAILED" if record.state == "failed" else None)
        or ("cancelled" if record.state == "cancelled" else None)
    )
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
            "failed_node_label": (failed_step or {}).get("label"),
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
        reasons.append("outputs_incomplete")
    if any(not step["complete"] for step in steps):
        reasons.append("step_results_incomplete")
    if inputs_state not in {"available", "redacted", "no-value"}:
        reasons.append(f"inputs_{inputs_state}")
    if inventory_state not in {"available"}:
        reasons.append(f"inventory_{inventory_state}")
    events_truncated = bool((manifest or {}).get("event_truncated"))
    if events_truncated:
        reasons.append("events_truncated")
    return {
        "schema_version": 1,
        "run": {
            **build_run_summary(record, latest_sequence=latest_sequence),
            "has_outputs": bool(outputs),
            "has_diagnostic": diagnostic is not None,
        },
        "progress": {
            "phase": str(
                latest_payload.get("phase")
                or getattr(latest_event, "kind", record.state)
            ),
            "current_step_id": next(
                (
                    step["step_id"]
                    for step in reversed(steps)
                    if step["state"] in {"queued", "running", "cancelling"}
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
        "run_inputs": run_inputs,
        "inputs_state": inputs_state,
        "steps": steps,
        "final_outputs": outputs,
        "diagnostic": diagnostic,
        "completeness": {
            "inputs_complete": not any(item.startswith("inputs_") for item in reasons),
            "outputs_complete": "outputs_incomplete" not in reasons,
            "steps_complete": not (
                {
                    "step_results_incomplete",
                    "events_truncated",
                    "inventory_truncated",
                }
                & set(reasons)
            ),
            "events_complete": "events_truncated" not in reasons,
            "evidence_available": manifest is not None
            or bool(child_calls)
            or bool(steps),
            "reasons": reasons,
        },
    }


__all__ = ["build_run_summary", "build_workflow_inspection"]
