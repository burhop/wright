"""Shared deterministic dependency doubles for engineering-model tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

from model_registry.policy import HostObservation


@dataclass(slots=True)
class FrozenClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        if delta.total_seconds() < 0:
            raise ValueError("Clock cannot move backwards")
        self.current += delta


@dataclass(slots=True)
class FakeHostObserver:
    observation: HostObservation
    calls: int = 0

    @classmethod
    def reference(cls) -> "FakeHostObserver":
        return cls(HostObservation.reference())

    def observe(self) -> HostObservation:
        self.calls += 1
        return self.observation


@dataclass(slots=True)
class _Reservation:
    owner: "FakeDiskReservation"
    operation_id: str
    bytes: int
    released: bool = False

    def release(self) -> None:
        if self.released:
            return
        self.owner._release(self.operation_id, self.bytes)
        self.released = True


@dataclass(slots=True)
class FakeDiskReservation:
    capacity_bytes: int
    reservations: dict[str, int] = field(default_factory=dict)

    @property
    def available_bytes(self) -> int:
        return self.capacity_bytes - sum(self.reservations.values())

    def reserve(self, operation_id: str, bytes: int) -> _Reservation:
        if bytes < 0 or operation_id in self.reservations:
            raise ValueError("Disk reservation is invalid")
        if bytes > self.available_bytes:
            raise ValueError("Insufficient fake disk capacity")
        self.reservations[operation_id] = bytes
        return _Reservation(self, operation_id, bytes)

    def _release(self, operation_id: str, bytes: int) -> None:
        if self.reservations.get(operation_id) == bytes:
            self.reservations.pop(operation_id)


class FakeSecretReferences:
    def __init__(self, values: Mapping[str, str] | None = None) -> None:
        self._values = dict(values or {})

    def contains(self, reference_id: str) -> bool:
        return reference_id in self._values

    def resolve_for_source(self, reference_id: str) -> str:
        try:
            return self._values[reference_id]
        except KeyError as error:
            raise KeyError("Secret reference is unavailable") from error

    def __repr__(self) -> str:
        return f"FakeSecretReferences(reference_ids={sorted(self._values)!r})"


class FakeTransport:
    def __init__(self, responses: Sequence[Mapping[str, Any]] = ()) -> None:
        self._responses = [dict(item) for item in responses]
        self._requests: list[dict[str, Any]] = []
        self._cancelled: list[str] = []

    @property
    def requests(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._requests)

    @property
    def cancelled(self) -> tuple[str, ...]:
        return tuple(self._cancelled)

    def request(self, message: Mapping[str, Any]) -> dict[str, Any]:
        self._requests.append(dict(message))
        if not self._responses:
            raise RuntimeError("No fake transport response is queued")
        return self._responses.pop(0)

    def cancel(self, request_id: str) -> None:
        self._cancelled.append(request_id)


__all__ = [
    "FakeDiskReservation",
    "FakeHostObserver",
    "FakeSecretReferences",
    "FakeTransport",
    "FrozenClock",
]
