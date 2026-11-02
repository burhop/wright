"""Failure-isolated incremental trace capture over the append-only run ledger."""

from __future__ import annotations

import hashlib
import json
import logging

from core.workflow_trace import TraceCaptureEvent
from data_vault import (
    WorkflowRunEventRecord,
    WorkflowRunRecord,
    WorkflowTraceRepository,
)

from .sources import adapt_rivet_run


logger = logging.getLogger(__name__)


class WorkflowTraceCapture:
    def __init__(self, repository: WorkflowTraceRepository) -> None:
        self.repository = repository

    def register_rivet_run(self, record: WorkflowRunRecord) -> None:
        """Capture identity without being allowed to change execution outcome."""
        try:
            self.repository.put_run(adapt_rivet_run(record))
        except Exception:
            logger.exception(
                "workflow trace run capture failed", extra={"run_id": record.run_id}
            )

    def append_rivet_event(self, event: WorkflowRunEventRecord) -> None:
        """Acknowledge one durable event; duplicate producer delivery is harmless."""
        try:
            payload = json.dumps(
                event.payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
            self.repository.append_event(
                TraceCaptureEvent(
                    event_id=f"rivet:{event.run_id}:{event.sequence}",
                    run_id=event.run_id,
                    sequence=event.sequence,
                    producer="rivet-runner",
                    producer_event_id=f"{event.run_id}:{event.sequence}",
                    occurred_at=event.occurred_at,
                    kind=event.kind.replace("_", "-"),
                    payload_digest=hashlib.sha256(payload).hexdigest(),
                    payload=event.payload,
                )
            )
        except Exception:
            logger.exception(
                "workflow trace event capture failed",
                extra={"run_id": event.run_id, "sequence": event.sequence},
            )
