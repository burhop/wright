"""Small side-effect-neutral protocol vocabulary used across owned packages."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class Clock(Protocol):
    def now_epoch_seconds(self) -> int: ...


class AuditSink(Protocol):
    def record(self, event: str, fields: Mapping[str, Any]) -> None: ...


class Redactor(Protocol):
    def text(self, value: str) -> str: ...

    def command(self, value: list[str]) -> list[str]: ...


class CancelSignal(Protocol):
    def cancelled(self) -> bool: ...


Work = Callable[[], T]
