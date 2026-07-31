from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from data_vault import (
    GenerationProvenanceRepository,
    SurfaceDiagnosticRepository,
    SurfaceGrantRepository,
    SurfacePreferenceRepository,
    SurfaceRepository,
    SurfaceRuntimeRepository,
    SurfaceVault,
)

from .ports import WorkspaceNotifier
from .service import WorkspaceService
from .surfaces.diagnostics import SurfaceDiagnosticHistory
from .surfaces.events import SurfaceEventHistory
from .surfaces.service import SurfaceService


def build_workspace_service(
    db_path: str, *, notifier: WorkspaceNotifier | None = None
) -> WorkspaceService:
    """Construct the production local workspace application graph explicitly."""
    return WorkspaceService(db_path, notifier=notifier)


@dataclass(slots=True)
class SurfaceApplication:
    """Owned foundational surface graph with explicit readiness/shutdown state."""

    service: SurfaceService
    repository: SurfaceRepository
    provenance_repository: GenerationProvenanceRepository
    preference_repository: SurfacePreferenceRepository
    grant_repository: SurfaceGrantRepository
    runtime_repository: SurfaceRuntimeRepository
    diagnostic_repository: SurfaceDiagnosticRepository
    vault: SurfaceVault
    events: SurfaceEventHistory
    diagnostics: SurfaceDiagnosticHistory
    accepting_commands: bool = False

    async def reconcile_startup(self) -> None:
        # Runtime/presentation reconciliation is filled by the managed-runtime
        # phase. Until then this gate deliberately exposes no recovered authority.
        self.accepting_commands = True

    async def close(self) -> None:
        # Reject commands before later phases revoke presentation/runtime
        # authority and flush their durable outbox work.
        self.accepting_commands = False


def build_surface_application(
    db_path: str, *, vault_root: str | Path | None = None
) -> SurfaceApplication:
    repository = SurfaceRepository(db_path)
    provenance_repository = GenerationProvenanceRepository(db_path)
    preference_repository = SurfacePreferenceRepository(db_path)
    grant_repository = SurfaceGrantRepository(db_path)
    runtime_repository = SurfaceRuntimeRepository(db_path)
    diagnostic_repository = SurfaceDiagnosticRepository(db_path)
    vault = SurfaceVault(vault_root or Path(db_path).with_suffix(".surfaces"))
    events = SurfaceEventHistory()
    diagnostics = SurfaceDiagnosticHistory()
    return SurfaceApplication(
        service=SurfaceService(repository=repository, events=events),
        repository=repository,
        provenance_repository=provenance_repository,
        preference_repository=preference_repository,
        grant_repository=grant_repository,
        runtime_repository=runtime_repository,
        diagnostic_repository=diagnostic_repository,
        vault=vault,
        events=events,
        diagnostics=diagnostics,
    )
