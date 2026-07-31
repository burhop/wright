"""Bind preview credentials to one immutable managed-runtime route."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from workspace_service.surfaces.live_app_manager import (
    LiveAppManagerError,
    LiveAppRoute,
)
from workspace_service.surfaces.presentation_tokens import (
    PresentationTokenError,
    PresentationTokenService,
)
from workspace_service.surfaces.target_policy import ResolvedTargetPin


class SurfaceRouteAuthorizationError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class LiveAppRouteManager(Protocol):
    def resolve_route(self, instance_id: str, *, generation: int) -> LiveAppRoute: ...

    def record_route_activity(self, instance_id: str) -> Any: ...


@dataclass(frozen=True, slots=True)
class AuthorizedSurfaceRoute:
    presentation_id: str
    presentation_origin: str
    principal_id: str
    workspace_id: str
    session_id: str
    surface_id: str
    source_id: str
    instance_id: str
    generation: int
    pin: ResolvedTargetPin
    http_declared: bool
    websocket_declared: bool
    sse_declared: bool
    limits: Any
    authority_valid: Callable[[], bool]
    target_valid: Callable[[], bool]
    activity: Callable[[], None]


class SurfaceRouteAuthority:
    def __init__(
        self,
        *,
        tokens: PresentationTokenService,
        manager_for_workspace: Callable[[str], LiveAppRouteManager],
    ) -> None:
        self._tokens = tokens
        self._manager_for_workspace = manager_for_workspace

    @staticmethod
    def _translate(
        error: PresentationTokenError | LiveAppManagerError,
    ) -> SurfaceRouteAuthorizationError:
        if isinstance(error, PresentationTokenError):
            return SurfaceRouteAuthorizationError(
                error.code, str(error), status_code=error.status_code
            )
        status = 410 if error.code == "SURFACE_STATE_STALE_GENERATION" else 503
        return SurfaceRouteAuthorizationError(
            error.code, str(error), status_code=status
        )

    def authorize(self, *, host: str, cookie: str) -> AuthorizedSurfaceRoute:
        try:
            presentation = self._tokens.authorize(host=host, cookie=cookie)
            manager = self._manager_for_workspace(presentation.workspace_id)
            route = manager.resolve_route(
                presentation.instance_id, generation=presentation.generation
            )
        except (PresentationTokenError, LiveAppManagerError) as error:
            raise self._translate(error) from error

        def authority_valid() -> bool:
            try:
                current = self._tokens.authorize(host=host, cookie=cookie)
            except PresentationTokenError:
                return False
            return (
                current.presentation_id == presentation.presentation_id
                and current.instance_id == presentation.instance_id
                and current.generation == presentation.generation
                and current.effective_origin == presentation.effective_origin
            )

        def target_valid() -> bool:
            try:
                current = manager.resolve_route(
                    presentation.instance_id, generation=presentation.generation
                )
            except LiveAppManagerError:
                return False
            return current.target == route.target

        policy = route.policy
        return AuthorizedSurfaceRoute(
            presentation_id=presentation.presentation_id,
            presentation_origin=presentation.effective_origin,
            principal_id=presentation.user_id,
            workspace_id=presentation.workspace_id,
            session_id=presentation.session_id,
            surface_id=presentation.surface_id,
            source_id=presentation.source_id,
            instance_id=presentation.instance_id,
            generation=presentation.generation,
            pin=route.target,
            http_declared=policy.http,
            websocket_declared=policy.websocket,
            sse_declared=policy.sse,
            limits=policy.limits,
            authority_valid=authority_valid,
            target_valid=target_valid,
            activity=lambda: manager.record_route_activity(presentation.instance_id),
        )


__all__ = [
    "AuthorizedSurfaceRoute",
    "LiveAppRouteManager",
    "SurfaceRouteAuthorizationError",
    "SurfaceRouteAuthority",
]
