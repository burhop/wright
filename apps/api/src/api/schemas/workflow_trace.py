"""Transport-only schemas for external workflow Trace evidence."""

from typing import Any, Dict

from pydantic import BaseModel, Field


class WorkflowTraceEvidenceIngestRequest(BaseModel):
    session_id: str
    evidence: Dict[str, Any]


class WorkflowTraceEvidencePageResponse(BaseModel):
    records: list[Dict[str, Any]] = Field(default_factory=list)
    next_after: str | None = None
