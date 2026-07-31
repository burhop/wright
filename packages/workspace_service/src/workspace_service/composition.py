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
from .surfaces.browser_policy import BrowserPolicyProjector
from .surfaces.display_service import DisplayService
from .surfaces.display_tokens import DisplayExecutionTokenService
from .surfaces.events import SurfaceEventHistory
from .surfaces.external_urls import ExternalUrlApprovalService
from .surfaces.grants import CapabilityGrantService
from .surfaces.limits import EffectiveSurfaceLimits, SurfaceLimitPolicy
from .surfaces.live_app_runtime import LiveAppRuntimeRegistry
from .surfaces.live_app_service import LiveAppControlService
from .surfaces.messages import SurfaceMessageRouter
from .surfaces.presentation_service import PresentationService
from .surfaces.presentation_tokens import PresentationTokenService
from .surfaces.revocation import RevocationCoordinator
from .surfaces.service import SurfaceService
from .surfaces.target_policy import TargetPolicy
from .config import WorkspaceSurfaceSettings


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
    display_service: DisplayService
    display_tokens: DisplayExecutionTokenService
    presentation_service: PresentationService
    presentation_tokens: PresentationTokenService
    revocation: RevocationCoordinator
    grant_service: CapabilityGrantService
    message_router: SurfaceMessageRouter
    target_policy: TargetPolicy
    browser_policy: BrowserPolicyProjector
    limits: EffectiveSurfaceLimits
    external_urls: ExternalUrlApprovalService
    vault: SurfaceVault
    events: SurfaceEventHistory
    diagnostics: SurfaceDiagnosticHistory
    runtime_registry: LiveAppRuntimeRegistry
    live_apps: LiveAppControlService
    accepting_commands: bool = False

    async def reconcile_startup(self) -> None:
        await self.runtime_registry.reconcile_startup()
        self.accepting_commands = True

    async def begin_shutdown(self) -> None:
        self.accepting_commands = False
        await self.runtime_registry.begin_shutdown()

    async def close(self) -> None:
        await self.begin_shutdown()
        await self.runtime_registry.shutdown()


def build_surface_application(
    db_path: str,
    *,
    vault_root: str | Path | None = None,
    settings: WorkspaceSurfaceSettings | None = None,
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
    display_service = DisplayService(db_path, vault=vault, events=events)
    display_tokens = DisplayExecutionTokenService(
        secret=DisplayExecutionTokenService.generate_secret()
    )
    effective_settings = settings or WorkspaceSurfaceSettings.from_env()
    presentation_service = PresentationService(
        db_path,
        preview=effective_settings.preview,
        token_ttl_seconds=effective_settings.policy.bootstrap_token_ttl_seconds,
        presentation_ttl_seconds=(
            effective_settings.policy.live_connection_lifetime_seconds
        ),
    )
    presentation_tokens = PresentationTokenService(
        db_path, preview=effective_settings.preview
    )
    revocation = RevocationCoordinator(db_path)
    grant_service = CapabilityGrantService(db_path)
    limits = SurfaceLimitPolicy(effective_settings.policy).compose()
    message_router = SurfaceMessageRouter(
        maximum_message_bytes=effective_settings.policy.websocket_message_bytes,
        maximum_messages_per_minute=(
            effective_settings.policy.bridge_messages_per_minute
        ),
    )
    runtime_registry = LiveAppRuntimeRegistry(
        db_path,
        settings=effective_settings,
        revocation=revocation,
    )
    surface_service = SurfaceService(repository=repository, events=events)
    return SurfaceApplication(
        service=surface_service,
        repository=repository,
        provenance_repository=provenance_repository,
        preference_repository=preference_repository,
        grant_repository=grant_repository,
        runtime_repository=runtime_repository,
        diagnostic_repository=diagnostic_repository,
        display_service=display_service,
        display_tokens=display_tokens,
        presentation_service=presentation_service,
        presentation_tokens=presentation_tokens,
        revocation=revocation,
        grant_service=grant_service,
        message_router=message_router,
        target_policy=TargetPolicy(),
        browser_policy=BrowserPolicyProjector(),
        limits=limits,
        external_urls=ExternalUrlApprovalService(),
        vault=vault,
        events=events,
        diagnostics=diagnostics,
        runtime_registry=runtime_registry,
        live_apps=LiveAppControlService(
            surfaces=surface_service,
            manager_for_workspace=runtime_registry.manager_for,
        ),
    )
