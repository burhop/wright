"""Trace projection for durable workspace-owned workflow run records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from .campaign import build_campaign_trace, is_campaign_run


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()
    ).hexdigest()


def _result(value: Mapping[str, Any], *, origin: str = "final_output") -> dict:
    representations = value.get("representations")
    representations = representations if isinstance(representations, list) else []
    primary = next(
        (
            item
            for item in representations
            if isinstance(item, Mapping) and item.get("location")
        ),
        {},
    )
    name = str(value.get("name") or value.get("id") or "Recorded result")
    kind = str(value.get("kind") or "structured")
    location = str(primary.get("location") or "")
    format_name = str(primary.get("format") or kind)
    is_file = primary.get("kind") == "workspace_file"
    artifact = (
        {
            "artifact_id": str(value.get("id") or _digest(value)[:24]),
            "media_type": format_name,
            "sha256": primary.get("sha256"),
            "bytes": primary.get("size_bytes") or 0,
            "label": name,
            "workspace_path": location,
        }
        if is_file
        else None
    )
    return {
        "result_id": f"canonical:{value.get('id') or _digest(value)[:24]}",
        "name": name,
        "origin": origin,
        "kind": "artifact" if is_file else ("link" if location else kind),
        "data_type": format_name,
        "evidence_state": "available" if representations else "not-retained",
        "value": location or None,
        "preview": location or f"Recorded {kind} result",
        "complete": True,
        "truncation_reason": None,
        "original_bytes": int(primary.get("size_bytes") or 0),
        "retained_bytes": int(primary.get("size_bytes") or 0),
        "digest": str(primary.get("sha256") or _digest(value)),
        "redaction_count": 0,
        "artifact": artifact,
    }


def _value_result(name: str, value: Any, *, origin: str) -> dict:
    return {
        "result_id": f"canonical:{origin}:{_digest([name, value])[:24]}",
        "name": name,
        "origin": origin,
        "kind": "text" if isinstance(value, str) else "structured",
        "data_type": "text/plain" if isinstance(value, str) else "application/json",
        "evidence_state": "available",
        "value": value,
        "preview": str(value)[:240],
        "complete": True,
        "truncation_reason": None,
        "original_bytes": len(str(value).encode()),
        "retained_bytes": len(str(value).encode()),
        "digest": _digest(value),
        "redaction_count": 0,
        "artifact": None,
    }


def project_prompt_workflow_trace(plan: Any) -> dict:
    """Freeze the authored process facts needed to review a future run."""
    steps = tuple(plan.steps)
    task_ids = {step.id for step in steps}
    connections = []
    seen: set[tuple[str, str, str]] = set()
    for target in steps:
        for target_port, source_ref in target.references:
            source = str(source_ref).split(".", 1)[0]
            identity = (source, target.id, target_port)
            if source not in task_ids or identity in seen:
                continue
            seen.add(identity)
            connections.append(
                {
                    "connection_id": f"{source}:{target.id}:{target_port}",
                    "source_node_id": source,
                    "target_node_id": target.id,
                    "source_port": str(source_ref).split(".", 1)[-1],
                    "target_port": target_port,
                    "label": target_port.replace("_", " "),
                }
            )
    return {
        "graph_id": "canonical",
        "name": plan.title,
        "nodes": [
            {
                "node_id": step.id,
                "node_type": (
                    "mcp_task" if step.agent_task else "mcp" if step.tool_name else "ai"
                ),
                "label": step.title,
                "order": index + 1,
                "x": (index % 4) * 250,
                "y": (index // 4) * 140,
                "width": 220,
                "prompt": step.prompt or None,
                "configuration": {
                    "output_format": step.output_format,
                    "output_path": step.output_path or None,
                    "tool": step.tool_name or None,
                    "server": step.server_id or None,
                    "max_revisions": step.max_revisions,
                },
            }
            for index, step in enumerate(steps)
        ],
        "connections": connections,
    }


def _seconds(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return (
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            .astimezone(UTC)
            .timestamp()
        )
    except ValueError:
        return None


def build_canonical_trace(
    record: Mapping[str, Any], *, workspace_id: str, session_id: str, path: str
) -> dict:
    if is_campaign_run(record):
        return build_campaign_trace(
            record,
            workspace_id=workspace_id,
            session_id=session_id,
            path=path,
        )
    result = record.get("result") if isinstance(record.get("result"), Mapping) else {}
    raw_results = result.get("results")
    if not isinstance(raw_results, list):
        partial = record.get("partial_results")
        raw_results = list(partial.values()) if isinstance(partial, Mapping) else []
    final_outputs = [_result(item) for item in raw_results if isinstance(item, Mapping)]
    attempts = result.get("revision_attempts")
    attempts = attempts if isinstance(attempts, list) else []
    completed = result.get("steps")
    completed = completed if isinstance(completed, list) else []
    ordered = [*attempts, *completed]
    per_node: dict[str, int] = {}
    steps = []
    for sequence, item in enumerate(ordered, start=1):
        if not isinstance(item, Mapping):
            continue
        node_id = str(item.get("task_id") or f"recorded-{sequence}")
        attempt = per_node.get(node_id, 0) + 1
        per_node[node_id] = attempt
        response = item.get("response")
        output = (
            [_value_result("Recorded response", response, origin="step_output")]
            if response is not None
            else []
        )
        steps.append(
            {
                "step_id": f"canonical:{node_id}:attempt:{attempt}",
                "sequence": sequence,
                "attempt": attempt,
                "node_id": node_id,
                "node_type": item.get("execution_kind"),
                "label": str(item.get("task_title") or node_id),
                "kind": "canonical_step",
                "qualified_tool_name": item.get("tool"),
                "request_id": None,
                "trace_id": None,
                "state": "superseded" if item in attempts else "succeeded",
                "started_at": None,
                "completed_at": None,
                "duration_ms": None,
                "reason_code": None,
                "inputs": [],
                "outputs": output,
                "input_state": "not-retained",
                "output_state": "available" if output else "not-retained",
                "result": output[0] if output else None,
                "artifacts": [],
                "redaction_count": 0,
                "complete": True,
            }
        )
    status = str(record.get("status") or "unknown")
    state = "succeeded" if status in {"completed", "pending_review"} else status
    run_id = str(result.get("run_id") or record.get("run_id") or _digest(path)[:24])
    started, ended = (
        _seconds(record.get("started_at")),
        _seconds(record.get("completed_at")),
    )
    duration_ms = (
        max(0, round((ended - started) * 1000))
        if started is not None and ended is not None
        else None
    )
    raw_inputs = record.get("trace_inputs")
    run_inputs = [
        _value_result(str(name), value, origin="run_input")
        for name, value in (
            raw_inputs.items() if isinstance(raw_inputs, Mapping) else ()
        )
    ]
    graph = record.get("trace_definition")
    graph = dict(graph) if isinstance(graph, Mapping) else None
    if graph is not None:
        graph["nodes"] = [dict(item) for item in graph.get("nodes") or ()]
        graph["connections"] = [dict(item) for item in graph.get("connections") or ()]
        for connection in graph["connections"]:
            source_steps = [
                step
                for step in steps
                if step["node_id"] == connection.get("source_node_id")
            ]
            target_steps = [
                step
                for step in steps
                if step["node_id"] == connection.get("target_node_id")
            ]
            traversals = []
            for target_step in target_steps:
                source_step = next(
                    (
                        step
                        for step in reversed(source_steps)
                        if step["sequence"] < target_step["sequence"]
                    ),
                    None,
                )
                if source_step is None:
                    continue
                traversals.append(
                    {
                        "traversal_id": (
                            f"canonical:{connection.get('connection_id')}:"
                            f"{target_step['attempt']}"
                        ),
                        "sequence": target_step["sequence"],
                        "source_step_id": source_step["step_id"],
                        "target_step_id": target_step["step_id"],
                        "source_attempt": source_step["attempt"],
                        "target_attempt": target_step["attempt"],
                    }
                )
            connection["traversals"] = traversals
    error = str(record.get("error") or "")
    diagnostic = None
    if state not in {"succeeded", "running"} or error:
        diagnostic = {
            "code": str(record.get("code") or status),
            "summary": error or f"The workflow stopped with status {status}.",
            "recovery_action": "Inspect the retained steps and artifacts before deciding whether to run again.",
            "failed_step_id": steps[-1]["step_id"] if steps else None,
            "failed_node_id": steps[-1]["node_id"] if steps else None,
            "failed_node_label": steps[-1]["label"] if steps else None,
            "qualified_tool_name": None,
            "trace_id": None,
            "full_rerun_available": status in {"failed", "cancelled", "interrupted"},
            "partial_retry_available": False,
            "residue_possible": status in {"interrupted", "unknown"},
        }
    reasons = []
    if graph is None:
        reasons.append("executed_graph_not_retained")
    if not run_inputs:
        reasons.append("input_identities_not_retained")
    return {
        "schema_version": 1,
        "run": {
            "run_id": run_id,
            "workspace_id": workspace_id,
            "session_id": session_id,
            "workflow_id": str(record.get("workflow_path") or path),
            "revision": 1,
            "digest": str(record.get("source_digest") or "0" * 64),
            "graph": str((graph or {}).get("name") or "canonical"),
            "generation": 1,
            "state": state,
            "started_at": record.get("started_at"),
            "completed_at": record.get("completed_at"),
            "duration_ms": duration_ms,
            "reason_code": str(record.get("code")) if record.get("code") else None,
            "trace_id": None,
            "latest_sequence": len(record.get("events") or ()),
            "has_outputs": bool(final_outputs),
            "has_diagnostic": diagnostic is not None,
            "output_truncated": False,
            "output_redaction_count": 0,
        },
        "progress": {
            "phase": status,
            "current_step_id": None,
            "completed_steps": len(completed),
            "total_steps": len(steps),
            "last_sequence": len(record.get("events") or ()),
            "updated_at": record.get("completed_at") or record.get("started_at"),
        },
        "events": [],
        "run_inputs": run_inputs,
        "inputs_state": "available" if run_inputs else "not-retained",
        "graph": graph,
        "evidence_records": [],
        "steps": steps,
        "final_outputs": final_outputs,
        "diagnostic": diagnostic,
        "completeness": {
            "inputs_complete": bool(run_inputs),
            "outputs_complete": True,
            "steps_complete": True,
            "events_complete": True,
            "evidence_available": bool(record.get("verification")),
            "reasons": reasons,
        },
    }


def canonical_artifact_paths(inspection: Mapping[str, Any]) -> Sequence[dict]:
    artifacts: dict[str, dict] = {}
    results = list(inspection.get("final_outputs") or ())
    results.extend(inspection.get("run_inputs") or ())
    results.extend(inspection.get("review_supplements") or ())
    for step in inspection.get("steps") or ():
        if isinstance(step, Mapping):
            results.extend(step.get("outputs") or ())
            results.extend(step.get("inputs") or ())
    for item in results:
        if not isinstance(item, Mapping) or not isinstance(item.get("artifact"), Mapping):
            continue
        artifact = dict(item["artifact"])
        artifact_id = artifact.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id:
            artifacts.setdefault(artifact_id, artifact)
    return list(artifacts.values())


__all__ = [
    "build_canonical_trace",
    "canonical_artifact_paths",
    "project_prompt_workflow_trace",
]
