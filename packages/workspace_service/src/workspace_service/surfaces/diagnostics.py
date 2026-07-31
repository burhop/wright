"""Bounded diagnostic history and authorized generated-artifact verification."""

from __future__ import annotations

from collections import defaultdict, deque
from threading import RLock
from typing import Any, Callable

from core.surfaces.models import GenerationProvenance
from core.surfaces.telemetry import SurfaceDiagnosticEvent


class SurfaceProvenanceAccessDenied(PermissionError):
    pass


class SurfaceDiagnosticHistory:
    def __init__(self, *, max_events_per_surface: int = 100) -> None:
        if max_events_per_surface < 1:
            raise ValueError("max_events_per_surface must be positive")
        self.maximum = max_events_per_surface
        self._events: dict[tuple[str, str], deque[SurfaceDiagnosticEvent]] = (
            defaultdict(lambda: deque(maxlen=self.maximum))
        )
        self._lock = RLock()

    def record(self, event: SurfaceDiagnosticEvent) -> None:
        if event.surface_id is None:
            raise ValueError("surface diagnostic history requires surface_id")
        with self._lock:
            self._events[(event.workspace_id, event.surface_id)].append(event)

    def list(
        self, *, workspace_id: str, surface_id: str
    ) -> list[SurfaceDiagnosticEvent]:
        with self._lock:
            return list(self._events.get((workspace_id, surface_id), ()))


def project_generation_provenance(
    provenance: GenerationProvenance,
    *,
    authorized: bool,
    script_loader: Callable[[str], str],
) -> dict[str, Any]:
    if not authorized:
        raise SurfaceProvenanceAccessDenied(
            "generated-artifact verification requires workspace authorization"
        )
    return {
        "mode": provenance.mode.value,
        "prompt": provenance.prompt,
        "no_prompt": provenance.no_prompt,
        "effective_constraints": dict(provenance.effective_constraints),
        "script": script_loader(provenance.script_vault_digest),
        "script_content_hash": provenance.script_content_hash,
        "script_revision": provenance.script_revision,
        "task_id": provenance.task_id,
        "execution_id": provenance.execution_id,
        "trace_id": provenance.trace_id,
        "created_at": provenance.created_at.isoformat(),
    }
