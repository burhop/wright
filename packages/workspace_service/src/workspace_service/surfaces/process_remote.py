"""Container and remote runtime contracts with explicit preview reachability."""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlsplit, urlunsplit

from workspace_service.surfaces.process_supervisor import (
    PlatformProcessIdentity,
    ProcessLaunchRequest,
    ProcessStopResult,
)


def _validated_http_url(value: str, label: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
        or parts.query
    ):
        raise ValueError(f"{label} must be an absolute credential-free HTTP URL")
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", "")
    )


@dataclass(frozen=True, slots=True)
class RemotePreviewEndpoint:
    internal_origin: str
    public_origin: str | None
    browser_reachable: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "internal_origin",
            _validated_http_url(self.internal_origin, "internal_origin"),
        )
        if self.public_origin is not None:
            object.__setattr__(
                self,
                "public_origin",
                _validated_http_url(self.public_origin, "public_origin"),
            )
        if self.browser_reachable and self.public_origin is None:
            raise ValueError(
                "browser_reachable requires an adapter-vouched public_origin"
            )

    @property
    def browser_url(self) -> str | None:
        return self.public_origin if self.browser_reachable else None


@dataclass(frozen=True, slots=True)
class RemoteLaunchResult:
    runtime_reference: str
    containment_mode: str
    endpoint: RemotePreviewEndpoint

    def __post_init__(self) -> None:
        if not self.runtime_reference or not self.containment_mode:
            raise ValueError("remote launch identity must be non-empty")


class RemoteRuntimeHandle(Protocol):
    launch_result: RemoteLaunchResult

    def stdout(self) -> AsyncIterator[bytes]: ...

    def stderr(self) -> AsyncIterator[bytes]: ...

    async def wait(self) -> int: ...

    async def stop(self, *, deadline: datetime) -> ProcessStopResult: ...


class RemoteRuntimeProvider(Protocol):
    async def launch(self, request: ProcessLaunchRequest) -> RemoteRuntimeHandle: ...


class RemoteManagedProcess:
    def __init__(
        self,
        *,
        handle: RemoteRuntimeHandle,
        request: ProcessLaunchRequest,
        adapter_name: str,
    ) -> None:
        self._handle = handle
        self.endpoint = handle.launch_result.endpoint
        self._stop_result: ProcessStopResult | None = None
        command_digest = hashlib.sha256(
            json.dumps(request.argv, separators=(",", ":")).encode()
        ).hexdigest()
        self.identity = PlatformProcessIdentity(
            adapter=adapter_name,
            pid=None,
            creation_time=None,
            containment_id=handle.launch_result.runtime_reference,
            containment_mode=handle.launch_result.containment_mode,
            command_digest=command_digest,
        )

    def stdout(self) -> AsyncIterator[bytes]:
        return self._handle.stdout()

    def stderr(self) -> AsyncIterator[bytes]:
        return self._handle.stderr()

    async def wait(self) -> int:
        return await self._handle.wait()

    def owned_processes(self) -> tuple[tuple[int, float], ...]:
        return ()

    async def stop(self, *, deadline: datetime) -> ProcessStopResult:
        if self._stop_result is None:
            self._stop_result = await self._handle.stop(deadline=deadline)
        return self._stop_result


class RemoteProcessAdapter:
    def __init__(
        self, *, provider: RemoteRuntimeProvider, adapter_name: str = "remote"
    ) -> None:
        if not adapter_name:
            raise ValueError("remote adapter name must be non-empty")
        self._provider = provider
        self._adapter_name = adapter_name

    async def launch(self, request: ProcessLaunchRequest) -> RemoteManagedProcess:
        handle = await self._provider.launch(request)
        return RemoteManagedProcess(
            handle=handle, request=request, adapter_name=self._adapter_name
        )


__all__ = [
    "RemoteLaunchResult",
    "RemoteManagedProcess",
    "RemotePreviewEndpoint",
    "RemoteProcessAdapter",
    "RemoteRuntimeHandle",
    "RemoteRuntimeProvider",
]
