"""Application composition for independently replaceable chat platforms."""

from agent_adapters.registry import (
    create_agent_engine as create_provider_engine,
    default_agent_registry,
)
from workspace_service.codex_platform import create_codex_chat_engine


def create_agent_engine(agent_name=None, *, db_path=None, registry=None):
    selected = (registry or default_agent_registry()).resolve_provider(agent_name)
    if selected.name == "codex":
        if not db_path:
            raise ValueError("Codex chat requires a durable Wright database")
        return create_codex_chat_engine(db_path)
    return create_provider_engine(selected.name, db_path=db_path, registry=registry)


async def require_workflow_platform(request):
    """Gate new native starts; existing runs retain their independent owner."""
    if getattr(request.app.state, "agent_engine", None) is None:
        return
    from api.routers.agent import get_agent_engine
    from fastapi import HTTPException

    selected = await get_agent_engine(request)
    if getattr(selected, "platform", None) == "codex":
        raise HTTPException(
            409,
            detail="Codex workflow execution is unavailable in the experimental chat pilot",
        )
