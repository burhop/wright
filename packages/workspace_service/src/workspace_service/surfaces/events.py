"""Bounded, ordered surface descriptor event publication."""

from __future__ import annotations

import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

from core.surfaces.models import SurfaceDescriptor


@dataclass(frozen=True, slots=True)
class SurfaceDescriptorEvent:
    event_id: str
    sequence: int
    event_type: str
    workspace_id: str
    user_id: str
    session_id: str
    surface_id: str
    revision: int
    descriptor: SurfaceDescriptor
    occurred_at: datetime


class SurfaceEventHistory:
    """Process-local event fanout buffer; durable delivery remains in the outbox."""

    def __init__(self, *, maximum_events_per_workspace: int = 512) -> None:
        if maximum_events_per_workspace < 1:
            raise ValueError("maximum event history must be positive")
        self.maximum = maximum_events_per_workspace
        self._events: dict[
            tuple[str, str, str], deque[SurfaceDescriptorEvent]
        ] = defaultdict(
            lambda: deque(maxlen=self.maximum)
        )
        self._sequences: dict[tuple[str, str, str], int] = defaultdict(int)
        self._lock = RLock()

    def publish(
        self,
        descriptor: SurfaceDescriptor,
        *,
        event_type: str,
        user_id: str,
        session_id: str,
    ) -> None:
        with self._lock:
            workspace_id = descriptor.workspace_id
            scope = (workspace_id, user_id, session_id)
            self._sequences[scope] += 1
            sequence = self._sequences[scope]
            self._events[scope].append(
                SurfaceDescriptorEvent(
                    event_id=str(uuid.uuid4()),
                    sequence=sequence,
                    event_type=event_type,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    session_id=session_id,
                    surface_id=str(descriptor.surface_id),
                    revision=int(descriptor.revision),
                    descriptor=descriptor,
                    occurred_at=datetime.now(UTC),
                )
            )

    def after(
        self,
        *,
        workspace_id: str,
        user_id: str,
        session_id: str,
        last_event_id: str | None = None,
    ) -> tuple[SurfaceDescriptorEvent, ...]:
        with self._lock:
            events = tuple(
                self._events.get((workspace_id, user_id, session_id), ())
            )
        if last_event_id is None:
            return events
        for index, event in enumerate(events):
            if event.event_id == last_event_id:
                return events[index + 1 :]
        return events
