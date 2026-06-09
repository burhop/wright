import structlog
from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional

from core.workspace import read_application_logs
from api.schemas.logs import LogsListResponse
from core.tracing import traced

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("", response_model=LogsListResponse)
@traced("logs.get")
async def get_logs(
    workspace_id: Optional[str] = Query(None, description="Filter logs by workspace ID"),
    level: Optional[str] = Query(None, description="Filter logs by level (info, warning, error)"),
    search: Optional[str] = Query(None, description="Keyword search within log events"),
    limit: int = Query(100, ge=1, le=1000, description="Max logs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Retrieve structured application logs filtered by workspace, level, and keywords."""
    try:
        result = read_application_logs(
            workspace_id=workspace_id,
            level=level,
            search=search,
            limit=limit,
            offset=offset,
        )
        return LogsListResponse(
            logs=result["logs"],
            total=result["total"]
        )
    except Exception as e:
        logger.exception("fetch_logs_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch application logs: {e}"
        )
