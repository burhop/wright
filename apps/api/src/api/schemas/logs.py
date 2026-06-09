from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    logger: str
    workspace_id: Optional[str] = None
    trace_id: str
    span_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class LogsListResponse(BaseModel):
    logs: List[LogEntry]
    total: int
