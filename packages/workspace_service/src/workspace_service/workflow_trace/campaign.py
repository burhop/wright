"""Projection for retained feature-081 engineering campaign run records."""

from __future__ import annotations

import hashlib
import mimetypes
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any


_PRIMARY_RESULT_LIMIT = 12
_CUSTOM_MEDIA_TYPES = {
    ".3mf": "model/3mf",
    ".frd": "application/vnd.calculix.frd",
    ".gcode": "text/x-gcode",
    ".inp": "application/vnd.calculix.input",
    ".step": "model/step",
    ".stl": "model/stl",
    ".stp": "model/step",
    ".vtu": "application/vnd.vtk",
}


def is_campaign_run(record: Mapping[str, Any]) -> bool:
    return (
        record.get("schema_version") == 1
        and isinstance(record.get("scenario_id"), str)
        and isinstance(record.get("attempt_id"), str)
        and isinstance(record.get("produced_files"), list)
        and isinstance(record.get("step_events"), list)
    )


def _seconds(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _label(task_id: str, scenario_id: str | None = None) -> str:
    value = re.sub(r"_t[a-f0-9]{24}$", "", task_id)
    if scenario_id:
        suffix = scenario_id.replace("-", "_")
        value = re.sub(rf"_{re.escape(suffix)}_attempt_\d+$", "", value)
    value = re.sub(r"_[a-z0-9-]+_attempt_\d+$", "", value)
    value = re.sub(r"_+", " ", value).strip()
    label = value[:1].upper() + value[1:] if value else "Recorded step"
    for source, replacement in (
        (r"\bAgentcad\b", "AgentCAD"),
        (r"\bCad\b", "CAD"),
        (r"\bCfd\b", "CFD"),
        (r"\bPcb\b", "PCB"),
    ):
        label = re.sub(source, replacement, label, flags=re.I)
    return label


def _safe_relative(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        return None
    return str(path)


def _media_type(path: str) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    return _CUSTOM_MEDIA_TYPES.get(
        suffix, mimetypes.guess_type(path)[0] or "application/octet-stream"
    )


def _artifact_result(
    value: Mapping[str, Any], *, run_path: str, index: int, directory: str = "artifacts"
) -> dict[str, Any]:
    relative = _safe_relative(value.get("path"))
    workspace_path = (
        str(PurePosixPath(run_path).parent / directory / relative) if relative else ""
    )
    artifact_id = str(
        value.get("artifact_id")
        or f"campaign-artifact:{hashlib.sha256(str(value).encode()).hexdigest()[:24]}"
    )
    name = relative or f"Recorded artifact {index}"
    digest = str(value.get("sha256") or "")
    size = value.get("size_bytes")
    size = int(size) if isinstance(size, int) and size >= 0 else 0
    media_type = _media_type(name)
    artifact = {
        "artifact_id": artifact_id,
        "media_type": media_type,
        "sha256": digest if len(digest) == 64 else None,
        "bytes": size,
        "label": PurePosixPath(name).name,
        "workspace_path": workspace_path,
        "role": str(value.get("artifact_role") or "output"),
    }
    return {
        "result_id": f"campaign:{artifact_id}",
        "name": name,
        "origin": "campaign_output",
        "kind": "artifact",
        "data_type": media_type,
        "evidence_state": "available" if workspace_path else "unavailable",
        "value": workspace_path or None,
        "preview": PurePosixPath(name).name,
        "complete": bool(workspace_path and len(digest) == 64),
        "truncation_reason": None if workspace_path else "unsafe_or_missing_path",
        "original_bytes": size,
        "retained_bytes": size,
        "digest": digest
        if len(digest) == 64
        else hashlib.sha256(name.encode()).hexdigest(),
        "redaction_count": 0,
        "artifact": artifact,
    }


def _primary_priority(result: Mapping[str, Any], index: int) -> tuple[int, int]:
    name = str(result.get("name") or "").lower()
    suffix = PurePosixPath(name).suffix
    if any(token in name for token in ("report", "summary", "decision", "comparison")):
        return (0, index)
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        return (1, index)
    if suffix in {".step", ".stp", ".stl", ".3mf", ".pdf", ".zip", ".md"}:
        return (2, index)
    return (3, index)


def _primary_category(result: Mapping[str, Any]) -> str:
    name = str(result.get("name") or "").lower()
    suffix = PurePosixPath(name).suffix
    if any(token in name for token in ("report", "summary", "decision", "comparison")):
        return "report"
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
        return "image"
    if suffix in {".step", ".stp", ".stl", ".3mf"}:
        return "model"
    if suffix in {".zip", ".gcode", ".kicad_pro", ".blend"}:
        return "package"
    if suffix in {".csv", ".json", ".vtu", ".vtk", ".frd", ".inp"}:
        return "data"
    return "other"


def _primary_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[tuple[int, dict[str, Any]]] = []
    selected_indexes: set[int] = set()
    for category in ("report", "image", "model", "package", "data", "other"):
        match = next(
            (
                (index, result)
                for index, result in enumerate(results)
                if index not in selected_indexes
                and _primary_category(result) == category
            ),
            None,
        )
        if match is not None:
            selected.append(match)
            selected_indexes.add(match[0])
    remaining = sorted(
        (
            (index, result)
            for index, result in enumerate(results)
            if index not in selected_indexes
        ),
        key=lambda item: _primary_priority(item[1], item[0]),
    )
    selected.extend(remaining[: _PRIMARY_RESULT_LIMIT - len(selected)])
    return [result for _index, result in selected]


def _build_steps(
    record: Mapping[str, Any],
    produced: list[Mapping[str, Any]],
    results: list[dict[str, Any]],
    scenario_id: str,
) -> list[dict[str, Any]]:
    raw_events = [
        event for event in record.get("step_events", ()) if isinstance(event, Mapping)
    ]
    occurrences: list[dict[str, Any]] = []
    by_task: dict[str, list[dict[str, Any]]] = {}
    for event_index, event in enumerate(raw_events, start=1):
        task_id = event.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        kind = event.get("kind")
        matching = by_task.setdefault(task_id, [])
        if kind == "step_started":
            occurrence = {
                "task_id": task_id,
                "sequence": event_index,
                "attempt": len(matching) + 1,
                "started_at": event.get("at"),
                "completed_at": None,
            }
            matching.append(occurrence)
            occurrences.append(occurrence)
        elif kind == "step_completed":
            occurrence = next(
                (item for item in reversed(matching) if item["completed_at"] is None),
                None,
            )
            if occurrence is None:
                occurrence = {
                    "task_id": task_id,
                    "sequence": event_index,
                    "attempt": len(matching) + 1,
                    "started_at": None,
                    "completed_at": None,
                }
                matching.append(occurrence)
                occurrences.append(occurrence)
            occurrence["completed_at"] = event.get("at")

    outputs_by_task: dict[str, list[dict[str, Any]]] = {}
    for raw, result in zip(produced, results, strict=True):
        if isinstance(raw.get("task_id"), str):
            outputs_by_task.setdefault(str(raw["task_id"]), []).append(result)

    run_status = str(record.get("status") or "unknown")
    steps = []
    for occurrence in sorted(occurrences, key=lambda item: item["sequence"]):
        task_id = occurrence["task_id"]
        outputs = outputs_by_task.get(task_id, [])
        started = _seconds(occurrence["started_at"])
        completed = _seconds(occurrence["completed_at"])
        if occurrence["completed_at"] is not None:
            state = "succeeded"
        elif run_status == "failed":
            state = "failed"
        elif run_status in {"cancelled", "blocked"}:
            state = run_status
        else:
            state = "interrupted"
        step_id = f"campaign:{task_id}:attempt:{occurrence['attempt']}"
        steps.append(
            {
                "step_id": step_id,
                "sequence": occurrence["sequence"],
                "attempt": occurrence["attempt"],
                "node_id": task_id,
                "node_type": "recorded_campaign_step",
                "label": _label(task_id, scenario_id),
                "kind": "campaign_step",
                "qualified_tool_name": None,
                "request_id": None,
                "trace_id": None,
                "state": state,
                "started_at": occurrence["started_at"],
                "completed_at": occurrence["completed_at"],
                "duration_ms": (
                    max(0, round((completed - started) * 1000))
                    if started is not None and completed is not None
                    else None
                ),
                "reason_code": record.get("error_code") if state == "failed" else None,
                "inputs": [],
                "outputs": outputs,
                "input_state": "not-retained",
                "output_state": "available" if outputs else "not-retained",
                "result": outputs[0] if outputs else None,
                "artifacts": [item["artifact"] for item in outputs],
                "redaction_count": 0,
                "complete": occurrence["completed_at"] is not None,
            }
        )
    return steps


def build_campaign_trace(
    record: Mapping[str, Any], *, workspace_id: str, session_id: str, path: str
) -> dict[str, Any]:
    """Project one immutable campaign record without inventing uncaptured facts."""
    if not is_campaign_run(record):
        raise ValueError("campaign run record is invalid")
    scenario_id = str(record["scenario_id"])
    attempt_id = str(record["attempt_id"])
    run_id = str(record.get("run_id") or "")
    if not run_id:
        raise ValueError("campaign run identity is unavailable")

    produced = [
        value
        for value in record.get("produced_files", ())
        if isinstance(value, Mapping)
    ]
    results = [
        _artifact_result(value, run_path=path, index=index)
        for index, value in enumerate(produced, start=1)
    ]
    steps = _build_steps(record, produced, results, scenario_id)
    final_outputs = _primary_results(results)
    run_inputs = []
    input_pack = record.get("trace_input_pack") or {}
    if input_pack.get("dataset_digest") == record.get("dataset_digest"):
        for index, value in enumerate(input_pack.get("files", []), start=1):
            if value.get("sha256") != input_pack.get("input_hashes", {}).get(
                value.get("path")
            ):
                continue
            item = _artifact_result(
                value,
                run_path=path,
                index=index,
                directory=f"inputs/{PurePosixPath(path).stem}",
            )
            item["origin"] = "campaign_input_pack"
            item["value"] = value.get("reference")
            item["artifact"]["role"] = "input"
            run_inputs.append(item)

    supplements = []
    for index, value in enumerate(
        record.get("trace_review_supplements") or [], start=1
    ):
        if not isinstance(value, Mapping) or value.get("artifact_role") not in {
            "input_reconstruction",
            "source_document",
            "review_visualization",
        }:
            continue
        item = _artifact_result(
            value,
            run_path=path,
            index=index,
            directory=f"review-sources/{PurePosixPath(path).stem}",
        )
        item.update(
            {
                key: value.get(key)
                for key in (
                    "provenance",
                    "source_artifact_ids",
                    "node_id",
                    "software",
                    "title",
                    "caption",
                    "engineering_summary",
                    "visualization_parameters",
                )
            }
        )
        item["origin"] = "review_supplement"
        item["value"] = value.get("reference")
        supplements.append(item)

    required = [
        value
        for value in record.get("required_step_ids", ())
        if isinstance(value, str) and value
    ]
    observed = [step["node_id"] for step in steps]
    node_ids = list(dict.fromkeys([*required, *observed]))
    execution_order = list(dict.fromkeys(observed))
    graph = {
        "graph_id": f"campaign:{scenario_id}:{attempt_id}",
        "name": scenario_id.replace("-", " ").title(),
        "nodes": [
            {
                "node_id": task_id,
                "node_type": "recorded_campaign_step",
                "label": _label(task_id, scenario_id),
                "order": index,
                "x": ((index - 1) % 4) * 250,
                "y": ((index - 1) // 4) * 140,
                "width": 220,
                "prompt": None,
                "configuration": {},
            }
            for index, task_id in enumerate(node_ids, start=1)
        ],
        "connections": [
            {
                "connection_id": f"campaign-order:{index}:{source}:{target}",
                "source_node_id": source,
                "target_node_id": target,
                "label": "Next recorded activity",
                "basis": "recorded_execution_order",
                "traversals": [],
            }
            for index, (source, target) in enumerate(
                zip(execution_order, execution_order[1:], strict=False), start=1
            )
        ],
    }

    raw_status = str(record.get("status") or "unknown")
    state = "succeeded" if raw_status == "completed" else raw_status
    if state == "outcome_unknown":
        state = "interrupted"
    started_at = record.get("started_at")
    completed_at = record.get("finished_at")
    started, completed = _seconds(started_at), _seconds(completed_at)
    duration_ms = (
        max(0, round((completed - started) * 1000))
        if started is not None and completed is not None
        else None
    )
    complete_steps = sum(step["state"] == "succeeded" for step in steps)
    events = [
        {"sequence": index, **dict(event)}
        for index, event in enumerate(record.get("step_events", ()), start=1)
        if isinstance(event, Mapping)
    ]
    error = record.get("error")
    diagnostic = None
    if state != "succeeded":
        failed = next((step for step in reversed(steps) if not step["complete"]), None)
        diagnostic = {
            "code": str(record.get("error_code") or raw_status),
            "summary": str(
                error or f"The campaign run stopped with status {raw_status}."
            ),
            "recovery_action": "Inspect the retained steps and artifacts before deciding whether to run again.",
            "failed_step_id": failed["step_id"] if failed else None,
            "failed_node_id": failed["node_id"] if failed else None,
            "failed_node_label": failed["label"] if failed else None,
            "qualified_tool_name": None,
            "trace_id": None,
            "full_rerun_available": raw_status in {"failed", "cancelled"},
            "partial_retry_available": False,
            "residue_possible": raw_status in {"outcome_unknown", "interrupted"},
        }
    reasons = [
        "full_execution_context_not_retained"
        if run_inputs
        else "input_files_not_indexed_by_campaign_record",
        "executed_connections_not_retained",
        "executed_prompts_not_retained",
    ]
    if len(results) > _PRIMARY_RESULT_LIMIT:
        reasons.append("additional_outputs_available_in_process_steps")
    outputs_complete = bool(record.get("all_required_steps_succeeded")) and all(
        result["complete"] for result in results
    )
    definition_digest = str(record.get("definition_digest") or "")
    if len(definition_digest) != 64:
        definition_digest = "0" * 64
    return {
        "schema_version": 1,
        "run": {
            "run_id": run_id,
            "workspace_id": workspace_id,
            "session_id": session_id,
            "workflow_id": scenario_id,
            "revision": 1,
            "digest": definition_digest,
            "graph": graph["name"],
            "generation": max(1, int(re.sub(r"\D", "", attempt_id) or "1")),
            "state": state,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_ms": duration_ms,
            "reason_code": str(record.get("error_code"))
            if record.get("error_code")
            else None,
            "trace_id": None,
            "latest_sequence": len(events),
            "has_outputs": bool(results),
            "has_diagnostic": diagnostic is not None,
            "output_truncated": False,
            "output_redaction_count": 0,
        },
        "progress": {
            "phase": raw_status,
            "current_step_id": next(
                (step["step_id"] for step in reversed(steps) if not step["complete"]),
                None,
            ),
            "completed_steps": complete_steps,
            "total_steps": len(node_ids),
            "last_sequence": len(events),
            "updated_at": completed_at or started_at,
        },
        "events": events,
        "run_inputs": run_inputs,
        "review_supplements": supplements,
        "inputs_state": "available" if run_inputs else "not-retained",
        "graph": graph,
        "evidence_records": [],
        "steps": steps,
        "final_outputs": final_outputs,
        "diagnostic": diagnostic,
        "completeness": {
            "inputs_complete": False,
            "outputs_complete": outputs_complete,
            "steps_complete": set(required).issubset(
                {
                    value
                    for value in record.get("completed_step_ids", ())
                    if isinstance(value, str)
                }
            ),
            "events_complete": True,
            "evidence_available": bool(
                record.get("runtime_evidence") or record.get("approval_evidence")
            ),
            "reasons": reasons,
        },
    }


__all__ = ["build_campaign_trace", "is_campaign_run"]
