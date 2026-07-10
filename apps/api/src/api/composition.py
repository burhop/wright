from __future__ import annotations

from functools import lru_cache

from workspace_service import WorkspaceService, build_workspace_service

from api.config import DATABASE_PATH
from api.notifications import GatewayWorkspaceNotifier


@lru_cache(maxsize=1)
def workspace_service() -> WorkspaceService:
    return build_workspace_service(DATABASE_PATH, notifier=GatewayWorkspaceNotifier())


async def close_application_services() -> None:
    if workspace_service.cache_info().currsize:
        await workspace_service().close()
        workspace_service.cache_clear()
