"""Read-only, allowlisted projection of the existing source-run recorder.

This is an export projection, not a run-state, timing or logging authority.
Neither receipt locators nor recorder payloads cross the diagnostic boundary.
"""

from collections import deque
from datetime import UTC, datetime
import re
from typing import get_args

from core.process_interactions import StartReceipt
from core.process_validation import canonical_digest

from .support_diagnostics import (
    SourceDiagnosticEvent,
    SourceDiagnosticEventKind,
    SourceRunDiagnostic,
)
from .workflow_run_record import _read_run_record, read_workflow_run
from .workspace_path import WorkspacePath


_EVENT_KINDS = frozenset(get_args(SourceDiagnosticEventKind))
_STEP_ID = re.compile(r"^[a-z][a-z0-9_]{0,159}$")
_REASONS = frozenset(
    {
        "INTERACTION_NOT_DECLARED",
        "TASK_BLOCKED",
        "TASK_FAILED",
        "PROCESS_VALIDATION_REJECTED",
        "PROCESS_VALIDATION_NO_PROGRESS",
        "WORKFLOW_NOT_READY",
        "EXECUTION_FAILED",
        "DESIGN_CHECK_REJECTED",
        "WORKFLOW_OUTPUT_INVALID",
        "WORKFLOW_REFERENCE_CHANGED",
    }
)


def source_run_diagnostic(root: str, receipt: StartReceipt) -> SourceRunDiagnostic:
    """Verify through the recorder reader, then project one recorded revision."""
    process = receipt.process
    view = read_workflow_run(
        root, process.source_path, receipt.run_id, run_log_path=receipt.run_log_path
    )
    record = _read_run_record(WorkspacePath(root), view["path"], process.source_path)
    if (
        record.get("run_id") or (record.get("result") or {}).get("run_id")
    ) != receipt.run_id or record.get("source_digest") != process.source_digest:
        raise ValueError("The recorder and immutable receipt disagree")

    omitted = False

    def timestamp(value):
        nonlocal omitted
        if value is None:
            return None
        try:
            if not isinstance(value, str) or len(value) > 128:
                raise ValueError("Invalid recorded timestamp")
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if result.tzinfo is None:
                raise ValueError("An observation requires a timezone")
            return result.astimezone(UTC)
        except (ValueError, OverflowError):
            omitted = True
            return None

    events = deque(maxlen=100)
    starts = {}
    eligible = 0
    history = record.get("events", [])
    for sequence, event in enumerate(history, 1):
        kind = event.get("kind")
        if not isinstance(kind, str) or kind not in _EVENT_KINDS:
            continue
        eligible += 1
        step_id = event.get("task_id")
        if step_id == "" and kind in {"run_started", "run_resumed", "run_completed"}:
            # The recorder uses an empty task ID for whole-run observations.
            step_id = None
        if step_id is not None and (
            not isinstance(step_id, str) or not _STEP_ID.fullmatch(step_id)
        ):
            step_id = None
            omitted = True
        at = timestamp(event.get("at"))
        values = dict(sequence=sequence, kind=kind, step_id=step_id, at=at)
        if kind == "step_started" and step_id:
            starts[step_id] = (sequence, at)
        elif kind == "step_completed" and step_id:
            start = starts.pop(step_id, None)
            if start and start[1] and at:
                elapsed = int((at - start[1]).total_seconds() * 1000)
                if elapsed >= 0:
                    values.update(start_sequence=start[0], elapsed_ms=elapsed)
                else:
                    omitted = True
        elif kind in {"step_diagnostic", "validation_exhausted"}:
            code = event.get("code")
            if isinstance(code, str) and code in _REASONS:
                values["reason"] = code
            else:
                values["reason"] = (
                    "VALIDATION_EXHAUSTED"
                    if kind == "validation_exhausted"
                    else "SOURCE_STEP_DIAGNOSTIC"
                )
                omitted |= code is not None
        events.append(SourceDiagnosticEvent(**values))

    started_at = timestamp(record.get("started_at"))
    ended_at = timestamp(record.get("completed_at") or record.get("execution_ended_at"))
    return SourceRunDiagnostic(
        run_id=receipt.run_id,
        source_digest=f"sha256:{process.source_digest}",
        record_digest=f"sha256:{canonical_digest(record)}",
        # Preserve the recorded label, even if a later ownership probe differs.
        # The working view owns current state and recovery.
        recorded_status=record.get("status", "unknown"),
        started_at=started_at,
        ended_at=ended_at,
        event_count=len(history),
        events=tuple(events),
        events_truncated=eligible > len(events),
        metadata_omitted=omitted,
    )
