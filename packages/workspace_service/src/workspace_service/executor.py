"""Owned bounded executor for synchronous workspace infrastructure work."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import TypeVar

from .errors import WorkspaceTimeoutError

T = TypeVar("T")


class BoundedExecutor:
    def __init__(self, *, max_workers: int = 4) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="wright-workspace"
        )
        self._capacity = asyncio.Semaphore(max_workers)
        self._closed = False

    async def run(
        self, operation: str, work: Callable[[], T], *, timeout_seconds: float
    ) -> T:
        if self._closed:
            raise RuntimeError("workspace executor is closed")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        try:
            async with asyncio.timeout(timeout_seconds):
                async with self._capacity:
                    loop = asyncio.get_running_loop()
                    return await loop.run_in_executor(self._pool, partial(work))
        except TimeoutError as exc:
            raise WorkspaceTimeoutError(
                f"{operation} exceeded its deadline", operation=operation
            ) from exc

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._pool.shutdown(wait=True, cancel_futures=True)
