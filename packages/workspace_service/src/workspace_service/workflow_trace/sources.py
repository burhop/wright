"""Explicit adapters from authoritative workflow run records into Trace."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from core.workflow_trace import TraceRunRecord
from data_vault import WorkflowRunRecord


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _outcome(status: str, *, ended_at: int | None) -> str:
    normalized = status.strip().lower().replace("-", "_")
    if normalized in {"succeeded", "success", "completed", "complete"}:
        return "completed"
    if normalized in {"failed", "error"}:
        return "failed"
    if normalized in {"blocked", "needs_input", "waiting_for_approval"}:
        return "blocked"
    if normalized in {"cancelled", "canceled"}:
        return "cancelled"
    if normalized in {"running", "queued", "cancelling", "interrupted"}:
        return "interrupted" if ended_at is None else "checkpoint"
    return "checkpoint"


def adapt_rivet_run(record: WorkflowRunRecord) -> TraceRunRecord:
    source = {
        "run_id": record.run_id,
        "workspace_id": record.workspace_id,
        "session_id": record.session_id,
        "workflow_id": record.workflow_id,
        "revision": record.revision,
        "digest": record.digest,
        "graph": record.graph,
        "state": record.state,
        "generation": record.generation,
        "started_at": record.started_at,
        "completed_at": record.completed_at,
        "reason_code": record.reason_code,
        "output_summary": record.output_summary,
        "output_truncated": record.output_truncated,
        "trace_id": record.trace_id,
    }
    return TraceRunRecord(
        workspace_id=record.workspace_id,
        run_id=record.run_id,
        source_kind="rivet",
        source_record_ref=f"rivet-run:{record.run_id}",
        source_record_digest=_digest(source),
        workflow_id=record.workflow_id,
        definition_digest=record.digest,
        original_status=record.state,
        outcome=_outcome(record.state, ended_at=record.completed_at),
        capture_state="complete"
        if record.state in {"succeeded", "failed", "cancelled"}
        else "partial",
        started_at=record.started_at,
        ended_at=record.completed_at,
    )


def adapt_source_run(
    source: Mapping[str, Any], *, workspace_id: str, source_ref: str
) -> TraceRunRecord:
    result = source.get("result") if isinstance(source.get("result"), Mapping) else {}
    run_id = str(result.get("run_id") or source.get("run_id") or "")
    workflow_id = str(
        source.get("workflow_id") or source.get("workflow") or source.get("slug") or ""
    )
    status = str(
        source.get("state")
        or source.get("status")
        or result.get("status")
        or "checkpoint"
    )
    started = source.get("started_at")
    ended = source.get("completed_at") or source.get("ended_at")
    definition_digest = source.get("definition_digest") or source.get("workflow_digest")
    if not run_id or not workflow_id:
        raise ValueError("source run identity is unavailable")
    if definition_digest is not None and (
        not isinstance(definition_digest, str) or len(definition_digest) != 64
    ):
        definition_digest = None
    return TraceRunRecord(
        workspace_id=workspace_id,
        run_id=run_id,
        source_kind="source-json",
        source_record_ref=source_ref,
        source_record_digest=_digest(source),
        workflow_id=workflow_id,
        definition_digest=definition_digest,
        definition_ref=(
            str(source["definition_ref"]) if source.get("definition_ref") else None
        ),
        layout_ref=(str(source["layout_ref"]) if source.get("layout_ref") else None),
        original_status=status,
        outcome=_outcome(status, ended_at=ended if isinstance(ended, int) else None),
        capture_state="complete"
        if source.get("capture_complete") is True
        else "legacy",
        started_at=started if isinstance(started, int) else None,
        ended_at=ended if isinstance(ended, int) else None,
    )
