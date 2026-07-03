import asyncio
import json
import re
import secrets
from typing import Optional, List, AsyncIterator
from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import structlog
from opentelemetry import trace
from core.tracing import traced

from agent_adapters import (
    BaseAgentEngine,
    AgentChatRequest,
    UnsupportedAgentRuntimeError,
    create_agent_engine,
    default_agent_registry,
)
from workspace_service import WorkspaceService
from core.workspace import (
    get_workspace_by_session,
    get_workspace_enabled_tools,
    update_workspace_agent_session_title,
    update_workspace_session,
)
from tool_registry import ApprovalContext
from tool_registry.db import get_servers

logger = structlog.get_logger(__name__)
router = APIRouter()


class ChatStreamJob:
    def __init__(self, session_id: str, request: AgentChatRequest, engine: BaseAgentEngine):
        self.session_id = session_id
        self.request = request
        self.engine = engine
        self.events: list[tuple[str, dict]] = []
        self.done = False
        self.cancelled = False
        self._condition = asyncio.Condition()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done() and not self.done

    async def _append(self, event_type: str, data: dict) -> None:
        async with self._condition:
            self.events.append((event_type, data))
            self._condition.notify_all()

    async def _finish(self) -> None:
        async with self._condition:
            self.done = True
            self._condition.notify_all()

    async def _run(self) -> None:
        saw_stream_end = False
        try:
            async for event in self.engine.stream_chat(self.request):
                if self.cancelled:
                    break
                saw_stream_end = saw_stream_end or event.type == "stream_end"
                await self._append(event.type, event.data)
        except asyncio.CancelledError:
            self.cancelled = True
            await self._append("error", {"message": "Stream cancelled by user."})
        except Exception as exc:
            await self._append("error", {"message": str(exc)})
        finally:
            if not self.cancelled and not saw_stream_end:
                await self._append("stream_end", {})
            await self._finish()

    async def stream_from(self, index: int = 0) -> AsyncIterator[tuple[str, dict]]:
        cursor = max(0, index)
        while True:
            async with self._condition:
                while cursor >= len(self.events) and not self.done:
                    await self._condition.wait()
                if cursor < len(self.events):
                    event = self.events[cursor]
                    cursor += 1
                elif self.done:
                    break
                else:
                    continue
            yield event

    async def cancel(self) -> bool:
        self.cancelled = True
        if self._task and not self._task.done():
            self._task.cancel()
        try:
            await self.engine.cancel_chat(self.session_id)
        except Exception:
            pass
        async with self._condition:
            self._condition.notify_all()
        return True


class ChatStreamRegistry:
    def __init__(self):
        self._jobs: dict[str, ChatStreamJob] = {}
        self._lock = asyncio.Lock()

    async def start(self, request: AgentChatRequest, engine: BaseAgentEngine) -> ChatStreamJob:
        async with self._lock:
            existing = self._jobs.get(request.session_id)
            if existing and existing.is_running:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A chat turn is already running for this session.",
                )
            job = ChatStreamJob(request.session_id, request, engine)
            self._jobs[request.session_id] = job
            job.start()
            return job

    async def get(self, session_id: str) -> ChatStreamJob | None:
        async with self._lock:
            return self._jobs.get(session_id)

    async def cancel(self, session_id: str, engine: BaseAgentEngine) -> bool:
        async with self._lock:
            job = self._jobs.get(session_id)
        if job:
            return await job.cancel()
        return await engine.cancel_chat(session_id)


def get_chat_stream_registry(request: Request) -> ChatStreamRegistry:
    registry = getattr(request.app.state, "chat_stream_registry", None)
    if registry is None:
        registry = ChatStreamRegistry()
        request.app.state.chat_stream_registry = registry
    return registry


#  Dependency injection helper
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


async def ensure_workspace_mcp_servers_active(
    request: Request, session_id: str
) -> None:
    """Start enabled workspace MCP servers before a chat turn begins."""

    mcp_engine = getattr(request.app.state, "mcp_engine", None)
    if not mcp_engine:
        return

    from api.config import DATABASE_PATH

    workspace = get_workspace_by_session(DATABASE_PATH, session_id)
    if not workspace:
        return

    enabled_tools = get_workspace_enabled_tools(DATABASE_PATH, session_id)
    enabled_servers = []
    for server in get_servers(DATABASE_PATH):
        if not server.is_installed:
            continue
        is_enabled = True
        if enabled_tools is not None:
            is_enabled = (server.name in enabled_tools) or (
                server.server_id in enabled_tools
            )
        if is_enabled:
            enabled_servers.append(server)

    workspace_dir = workspace["local_path"]
    failed: list[str] = []
    for server in enabled_servers:
        try:
            runner = getattr(mcp_engine, "_active_runners", {}).get(server.server_id)
            if runner and runner.is_running() and server.status == "active":
                continue
            await mcp_engine.start_server(
                server.server_id,
                workspace_dir=workspace_dir,
                approval_context=ApprovalContext(
                    workspace_id=workspace["workspace_id"],
                    workspace_approvals=set(server.approval_gates or []),
                ),
            )
        except Exception as exc:
            logger.exception(
                "workspace_mcp_preflight_start_failed",
                server=server.name,
                session_id=session_id,
                error=str(exc),
            )
            failed.append(f"{server.name}: {exc}")

    if failed:
        detail = "Failed to start workspace MCP server(s): " + "; ".join(failed)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )


#  Pydantic Request/Response Schemas
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


class ChatRequest(BaseModel):
    session_id: str
    message: str
    attachments: Optional[List[str]] = None


def title_from_slash_command(message: str) -> str | None:
    match = re.match(r"^\s*/title\s+(.+)\s*$", message or "", re.IGNORECASE)
    if not match:
        return None
    title = match.group(1).strip().strip('"\'“”')
    return title or None


class ChatHistoryMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: int
    trace_id: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatHistoryMessage]


class CommandModel(BaseModel):
    name: str
    description: str
    prefix: str


class CommandsResponse(BaseModel):
    commands: List[CommandModel]


#  Route Handlers


@router.get("/commands", response_model=CommandsResponse)
@traced("agent.get_commands")
async def get_commands(engine: BaseAgentEngine = Depends(get_agent_engine)):
    try:
        agent_cmds = await engine.get_commands()
    except Exception as e:
        logger.error("Failed to get commands from engine", error=str(e))
        agent_cmds = []

    # Map engine slash commands
    commands = [
        CommandModel(name=c.name, description=c.description, prefix="/")
        for c in agent_cmds
    ]

    wright_command = CommandModel(
        name="wright",
        description="Wright engineering platform: start, stop, open UI, doctor, catalog, info, install, and status",
        prefix="/",
    )
    if not any(c.prefix == "/" and c.name == "wright" for c in commands):
        commands.insert(0, wright_command)

    # Static @ mentions for the IDE's WebUI
    webui_mentions = [
        CommandModel(
            name="file", description="Mention a file in the workspace", prefix="@"
        ),
        CommandModel(name="task", description="Mention a background task", prefix="@"),
        CommandModel(
            name="conversation", description="Mention a past conversation", prefix="@"
        ),
        CommandModel(
            name="agent", description="Mention another agent profile", prefix="@"
        ),
    ]

    commands.extend(webui_mentions)
    return CommandsResponse(commands=commands)


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
    body: NewSessionRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
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

        workspace_id = existing["workspace_id"] if existing else str(uuid.uuid4())
        if existing:
            update_workspace_session(
                DATABASE_PATH, existing["workspace_id"], session_info.session_id
            )
            log.info(
                "create_session_associated_with_existing_workspace",
                workspace_id=workspace_id,
                session_id=session_info.session_id,
            )
        else:
            create_workspace(
                DATABASE_PATH,
                workspace_id,
                session_info.session_id,
                workspace_path,
                workspace_name=os.path.basename(workspace_path),
            )

        sync_manager = getattr(request.app.state, "agent_sync_manager", None)
        agent_id = getattr(sync_manager, "active_agent", "hermes")
        WorkspaceService(DATABASE_PATH).refresh_agent_context_for_path(
            workspace_path,
            agent_id=agent_id,
            workspace_id=workspace_id,
            session_id=session_info.session_id,
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
            detail=f"Agent failed to create session: {str(exc)}",
        )


@router.get("/sessions", response_model=SessionsListResponse)
@traced("agent.session.list")
async def list_agent_sessions(
    workspace_id: Optional[str] = None,
    engine: BaseAgentEngine = Depends(get_agent_engine),
):
    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id, workspace_id=workspace_id)
    log.info("list_sessions_requested")

    try:
        sessions = await engine.list_sessions()
        if workspace_id:
            from api.config import DATABASE_PATH
            from core.workspace import associate_workspace_session, get_workspace_by_id

            workspace = get_workspace_by_id(DATABASE_PATH, workspace_id)
            if workspace:
                local_path = workspace["local_path"]
                sessions = [s for s in sessions if s.workspace == local_path]
                for session in sessions:
                    associate_workspace_session(
                        DATABASE_PATH,
                        workspace_id,
                        session.session_id,
                        title=session.title,
                        created_at=session.created_at,
                        updated_at=session.updated_at,
                    )
            else:
                sessions = []
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
            detail=f"Agent failed to list sessions: {str(exc)}",
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
            detail=f"Agent failed to delete session: {str(exc)}",
        )


@router.post("/chat")
@traced("agent.chat")
async def chat(
    body: ChatRequest,
    request: Request,
    engine: BaseAgentEngine = Depends(get_agent_engine),
):
    """Unified chat endpoint: send message and stream response."""
    trace_id = get_current_trace_id()
    log = logger.bind(trace_id=trace_id, session_id=body.session_id)
    log.info("chat_requested")

    # Sync and activate workspace tools before chat turn. Chat should not begin
    # until the MCP servers assigned to this workspace are available.
    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        try:
            sync_manager.sync_workspace_tools(body.session_id)
        except Exception as e:
            log.warn("Failed to sync workspace tools", error=str(e))

    await ensure_workspace_mcp_servers_active(request, body.session_id)

    requested_title = title_from_slash_command(body.message)
    if requested_title:
        from api.config import DATABASE_PATH

        updated = update_workspace_agent_session_title(
            DATABASE_PATH, body.session_id, requested_title
        )
        log.info("workspace_session_title_updated", updated=updated)

    chat_request = AgentChatRequest(
        session_id=body.session_id,
        message=body.message,
        trace_id=trace_id,
        attachments=body.attachments,
    )
    registry = get_chat_stream_registry(request)
    job = await registry.start(chat_request, engine)

    async def sse_generator() -> AsyncIterator[str]:
        yield f"event: stream_start\ndata: {json.dumps({'stream_id': trace_id, 'session_id': body.session_id})}\n\n"
        try:
            async for event_type, event_data in job.stream_from(0):
                log.info("chat_stream_yield_event", type=event_type)
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
        except Exception as exc:
            log.exception("chat_stream_attach_failed", error=str(exc))
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Trace-Id": trace_id,
        },
    )


@router.get("/active", response_model=ActiveAgentResponse)
@traced("agent.active.get")
async def get_active_agent_endpoint(request: Request):
    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    registry = default_agent_registry()
    agent_name = sync_manager.active_agent if sync_manager else None
    try:
        provider = registry.resolve_provider(agent_name)
    except UnsupportedAgentRuntimeError:
        provider = registry.default_provider()
    return ActiveAgentResponse(agent=provider.name)


@router.post("/active", response_model=ActiveAgentResponse)
@traced("agent.active.set")
async def set_active_agent_endpoint(
    body: SetActiveAgentRequest, request: Request, session_id: Optional[str] = None
):
    registry = default_agent_registry()
    try:
        provider = registry.resolve_provider(body.agent)
    except UnsupportedAgentRuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    from api.config import DATABASE_PATH

    request.app.state.agent_engine = create_agent_engine(
        provider.name, db_path=DATABASE_PATH, registry=registry
    )
    sync_manager = getattr(request.app.state, "agent_sync_manager", None)
    if sync_manager:
        sync_manager.active_agent = provider.name
        if session_id:
            # Sync tools immediately for the active workspace session
            try:
                sync_manager.sync_workspace_tools(session_id)
            except Exception as e:
                logger.error("Failed to sync tools on agent switch: %s", e)
        return ActiveAgentResponse(agent=sync_manager.active_agent)
    return ActiveAgentResponse(agent=provider.name)


@router.get("/chat/stream")
@traced("agent.chat.stream.attach")
async def attach_chat_stream(
    request: Request,
    session_id: str = Query(...),
    after: int = Query(0, ge=0),
):
    """Attach or reattach to a running or recently completed chat stream."""
    registry = get_chat_stream_registry(request)
    job = await registry.get(session_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stream is available for this session.",
        )

    async def sse_generator() -> AsyncIterator[str]:
        async for event_type, event_data in job.stream_from(after):
            yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/chat/cancel")
@traced("agent.chat.cancel")
async def cancel_chat_turn(
    request: Request,
    session_id: str = Query(...),
    engine: BaseAgentEngine = Depends(get_agent_engine),
):
    """Cancel a running chat turn stream."""
    try:
        registry = get_chat_stream_registry(request)
        ok = await registry.cancel(session_id, engine)
        return {"success": ok}
    except Exception as exc:
        logger.exception("chat_cancel_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to cancel chat turn: {str(exc)}",
        )
