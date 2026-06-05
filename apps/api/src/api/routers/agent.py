import json
import secrets
from typing import Optional, List, AsyncIterator
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import structlog
from opentelemetry import trace
from core.tracing import traced

from agent_adapters import (
    BaseAgentEngine,
    AgentChatRequest,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


# ── Dependency injection helper ──────────────────────────────────────────────
def get_agent_engine(request: Request) -> BaseAgentEngine:
    """Extract BaseAgentEngine from app state."""
    engine = getattr(request.app.state, "agent_engine", None)
    if not engine:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent engine not initialized in app state",
        )
    return engine


def get_current_trace_id() -> str:
    """Retrieve trace_id from OpenTelemetry active span or generate ephemeral fallback."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return f"{span.get_span_context().trace_id:032x}"
    return secrets.token_hex(16)


# ── Pydantic Request/Response Schemas ─────────────────────────────────────────
class ActiveAgentResponse(BaseModel):
    agent: str


class SetActiveAgentRequest(BaseModel):
    agent: str


class NewSessionRequest(BaseModel):
    workspace: Optional[str] = None


class NewSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: int


class SessionInfoModel(BaseModel):
    session_id: str
    title: str
    created_at: int
    updated_at: int
    message_count: int


class SessionsListResponse(BaseModel):
    sessions: List[SessionInfoModel]


class DeleteSessionResponse(BaseModel):
    ok: bool


class ChatStartRequest(BaseModel):
    session_id: str
    message: str


class ChatStartResponse(BaseModel):
    stream_id: str
    session_id: str
    trace_id: str


class ChatHistoryMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: int
    trace_id: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatHistoryMessage]


# ── Route Handlers ───────────────────────────────────────────────────────────
@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
@traced("agent.session.history")
async def get_session_history(
    session_id: str, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    """Retrieve chat history for a session from the agent backend.

    Each agent adapter (Hermes, OpenClaw, etc.) is responsible for
    persisting and returning its own chat history.
    """
    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id, session_id=session_id)
    log.info("chat_history_requested")

    try:
        messages = await engine.get_chat_history(session_id)
        log.info("chat_history_success", message_count=len(messages))
        return ChatHistoryResponse(
            session_id=session_id,
            messages=[
                ChatHistoryMessage(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    timestamp=m.timestamp,
                    trace_id=m.trace_id,
                )
                for m in messages
            ],
        )
    except Exception as exc:
        log.exception("chat_history_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to retrieve chat history: {str(exc)}",
        )


@router.post("/sessions/new", response_model=NewSessionResponse)
@traced("agent.session.create")
async def create_new_session(
    body: NewSessionRequest, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    import os
    import uuid
    from core import WorkspaceManager
    from core.workspace import create_workspace
    from api.config import DATABASE_PATH

    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id, workspace=body.workspace)
    log.info("create_session_requested")

    try:
        workspace_path = body.workspace
        if not workspace_path:
            # Generate a unique workspace directory name
            workspace_uuid = str(uuid.uuid4())
            home_dir = os.environ.get("HOME", "/home/agent")
            workspace_path = os.path.join(home_dir, "workspace", workspace_uuid)

        os.makedirs(workspace_path, exist_ok=True)
        # Instantiate WorkspaceManager to automatically run git init
        WorkspaceManager(workspace_path)

        session_info = await engine.create_session(workspace_path)
        log.info("create_session_success", session_id=session_info.session_id)

        # Save mapping to local SQLite (reusing existing workspace if the path matches)
        import sqlite3

        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM engineering_workspaces WHERE local_path = ?",
                (workspace_path,),
            )
            existing = cursor.fetchone()
        finally:
            conn.close()

        if existing:
            import time

            conn = sqlite3.connect(DATABASE_PATH)
            try:
                conn.execute(
                    "UPDATE engineering_workspaces SET session_id = ?, updated_at = ? WHERE workspace_id = ?",
                    (
                        session_info.session_id,
                        int(time.time()),
                        existing["workspace_id"],
                    ),
                )
                conn.commit()
            finally:
                conn.close()
            log.info(
                "create_session_updated_existing_workspace",
                workspace_id=existing["workspace_id"],
                session_id=session_info.session_id,
            )
        else:
            create_workspace(
                DATABASE_PATH,
                str(uuid.uuid4()),
                session_info.session_id,
                workspace_path,
                workspace_name=os.path.basename(workspace_path),
            )

        return NewSessionResponse(
            session_id=session_info.session_id,
            title=session_info.title,
            created_at=session_info.created_at,
        )
    except Exception as exc:
        log.exception("create_session_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hermes agent failed to create session: {str(exc)}",
        )


@router.get("/sessions", response_model=SessionsListResponse)
@traced("agent.session.list")
async def list_agent_sessions(engine: BaseAgentEngine = Depends(get_agent_engine)):
    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id)
    log.info("list_sessions_requested")

    try:
        sessions = await engine.list_sessions()
        log.info("list_sessions_success", count=len(sessions))
        return SessionsListResponse(
            sessions=[
                SessionInfoModel(
                    session_id=s.session_id,
                    title=s.title,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    message_count=s.message_count,
                )
                for s in sessions
            ]
        )
    except Exception as exc:
        log.exception("list_sessions_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hermes agent failed to list sessions: {str(exc)}",
        )


@router.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
@traced("agent.session.delete")
async def delete_agent_session(
    session_id: str, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id, session_id=session_id)
    log.info("delete_session_requested")

    try:
        ok = await engine.delete_session(session_id)
        log.info("delete_session_result", success=ok)
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or delete failed",
            )
        return DeleteSessionResponse(ok=ok)
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("delete_session_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hermes agent failed to delete session: {str(exc)}",
        )


@router.post("/chat/start", response_model=ChatStartResponse)
@traced("agent.chat.start")
async def start_chat_turn(
    body: ChatStartRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
):
    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id, session_id=body.session_id)
    log.info("chat_start_requested")

    try:
        sync_manager = getattr(request.app.state, "agent_sync_manager", None)
        if sync_manager:
            try:
                sync_manager.sync_workspace_tools(body.session_id)
            except Exception as e:
                log.warn(
                    "Failed to sync workspace tools to active agent before chat turn",
                    error=str(e),
                )

        chat_request = AgentChatRequest(
            session_id=body.session_id,
            message=body.message,
            trace_id=trace_id,
        )
        chat_response = await engine.start_chat(chat_request)
        log.info("chat_start_success", stream_id=chat_response.stream_id)
        return ChatStartResponse(
            stream_id=chat_response.stream_id,
            session_id=chat_response.session_id,
            trace_id=trace_id,
        )
    except Exception as exc:
        log.exception("chat_start_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Hermes agent unavailable: {str(exc)}",
        )


@router.get("/chat/stream")
@traced("agent.chat.stream")
async def chat_response_stream(
    stream_id: str, engine: BaseAgentEngine = Depends(get_agent_engine)
):
    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id, stream_id=stream_id)
    log.info("chat_stream_connected")

    async def sse_generator() -> AsyncIterator[str]:
        try:
            async for event in engine.stream_response(stream_id):
                log.info("chat_stream_yield_event", type=event.type)
                yield f"event: {event.type}\ndata: {json.dumps(event.data)}\n\n"
        except Exception as exc:
            log.exception("chat_stream_yield_failed", error=str(exc))
            # Yield error event and exit
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/active", response_model=ActiveAgentResponse)
@traced("agent.active.get")
async def get_active_agent_endpoint(request: Request):
    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    agent_name = sync_manager.active_agent if sync_manager else "hermes"
    return ActiveAgentResponse(agent=agent_name)


@router.post("/active", response_model=ActiveAgentResponse)
@traced("agent.active.set")
async def set_active_agent_endpoint(
    body: SetActiveAgentRequest, request: Request, session_id: Optional[str] = None
):
    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        sync_manager.active_agent = body.agent
        if session_id:
            # Sync tools immediately for the active workspace session
            try:
                sync_manager.sync_workspace_tools(session_id)
            except Exception as e:
                logger.error("Failed to sync tools on agent switch: %s", e)
        return ActiveAgentResponse(agent=sync_manager.active_agent)
    return ActiveAgentResponse(agent="hermes")
