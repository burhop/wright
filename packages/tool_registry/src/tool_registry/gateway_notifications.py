from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator

from .gateway_models import GatewaySessionContext


class GatewayNotificationHub:
    def __init__(self) -> None:
        self._queues: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)

    async def subscribe(self, session: GatewaySessionContext) -> AsyncIterator[str]:
        queue: asyncio.Queue[str] = asyncio.Queue()
        self._queues[session.workspace_id].add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._queues[session.workspace_id].discard(queue)

    def publish(self, *, workspace_id: str, event: str) -> None:
        for queue in tuple(self._queues.get(workspace_id, ())):
            queue.put_nowait(event)

    def subscriber_count(self, workspace_id: str) -> int:
        return len(self._queues.get(workspace_id, ()))
