"""Lowest-consumer capability ports for Workspace Surface application services."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Protocol

from core.surfaces.models import SurfaceDescriptor, SurfaceId, SurfaceRevision


class SurfaceRepositoryPort(Protocol):
    def create(
        self,
        descriptor: SurfaceDescriptor,
        *,
        user_id: str,
        session_id: str,
        idempotency_key: str | None = None,
    ) -> SurfaceDescriptor: ...

    def get(
        self,
        surface_id: SurfaceId,
        *,
        workspace_id: str,
        user_id: str,
        session_id: str,
    ) -> SurfaceDescriptor | None: ...

    def get_by_idempotency(
        self,
        *,
        workspace_id: str,
        user_id: str,
        session_id: str,
        idempotency_key: str,
    ) -> SurfaceDescriptor | None: ...

    def list(
        self, *, workspace_id: str, user_id: str, session_id: str
    ) -> Sequence[SurfaceDescriptor]: ...

    def compare_and_set(
        self,
        descriptor: SurfaceDescriptor,
        *,
        expected_revision: SurfaceRevision,
        user_id: str,
        session_id: str,
    ) -> SurfaceDescriptor: ...


class SurfaceVaultPort(Protocol):
    def put(self, *, workspace_id: str, payload: bytes) -> str: ...

    def get(self, *, workspace_id: str, digest: str) -> bytes: ...


class SurfaceClock(Protocol):
    def __call__(self) -> datetime: ...


class SurfaceIdFactory(Protocol):
    def __call__(self) -> str: ...


class SurfaceTokenIssuer(Protocol):
    def issue(
        self,
        *,
        audience: str,
        subject: str,
        workspace_id: str,
        expires_at: datetime,
        claims: Mapping[str, str],
    ) -> str: ...

    def revoke(self, token_id: str) -> None: ...


class SurfaceProcessSupervisor(Protocol):
    async def start(
        self,
        *,
        workspace_id: str,
        argv: Sequence[str],
        cwd: str,
        environment: Mapping[str, str],
        limits: Mapping[str, Any],
        idempotency_key: str,
    ) -> Mapping[str, Any]: ...

    async def stop(
        self, *, runtime_id: str, generation: int, deadline: datetime
    ) -> Mapping[str, Any]: ...


class SurfaceNetworkPort(Protocol):
    async def resolve_and_pin(
        self,
        *,
        workspace_id: str,
        instance_id: str,
        generation: int,
        declaration: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...


class SurfaceEventPublisherPort(Protocol):
    def publish(
        self,
        descriptor: SurfaceDescriptor,
        *,
        event_type: str,
        user_id: str,
        session_id: str,
    ) -> None: ...


class McpUiPort(Protocol):
    async def read_resource(
        self,
        *,
        gateway_session_id: str,
        server_connection_id: str,
        resource_uri: str,
    ) -> Mapping[str, Any]: ...

    async def invoke_visible_tool(
        self,
        *,
        gateway_session_id: str,
        server_connection_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
    ) -> Mapping[str, Any]: ...
