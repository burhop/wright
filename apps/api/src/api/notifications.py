from __future__ import annotations

import asyncio
from typing import Any

import structlog

logger = structlog.get_logger(__name__)
gateway_event_queues: set[asyncio.Queue[Any]] = set()


def notify_gateway_tool_change() -> None:
    logger.info(
        "notifying_gateways_of_tool_change", active_queues=len(gateway_event_queues)
    )
    for queue in list(gateway_event_queues):
        try:
            queue.put_nowait("list_changed")
        except Exception as error:
            logger.warning("failed_to_queue_gateway_event", error=str(error))


class GatewayWorkspaceNotifier:
    def publish(
        self,
        event: str,
        *,
        workspace_id: str | None = None,
        session_id: str | None = None,
    ) -> None:
        logger.info(
            "workspace_change_notification",
            change_type=event,
            workspace_id=workspace_id,
            session_id=session_id,
        )
        notify_gateway_tool_change()
