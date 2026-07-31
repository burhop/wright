"""Race-resistant loopback endpoint reservation and ownership proof."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Protocol

import psutil


class EndpointError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ListenerIdentity:
    address: str
    port: int
    pid: int
    creation_time: float


@dataclass(frozen=True, slots=True)
class RuntimeIdentity:
    instance_id: str
    generation: int
    pid: int
    creation_time: float
    descendants: tuple[tuple[int, float], ...] = ()

    @property
    def owned_processes(self) -> frozenset[tuple[int, float]]:
        return frozenset(((self.pid, self.creation_time), *self.descendants))


@dataclass(frozen=True, slots=True)
class EndpointOwnershipProof:
    instance_id: str
    generation: int
    listener: ListenerIdentity


class ListenerInspector(Protocol):
    def find_listener(self, *, address: str, port: int) -> ListenerIdentity | None: ...


class PsutilListenerInspector:
    """Resolve a numeric listener to an exact PID creation-time identity."""

    def find_listener(self, *, address: str, port: int) -> ListenerIdentity | None:
        normalized = ipaddress.ip_address(address).compressed
        try:
            connections = psutil.net_connections(kind="tcp")
        except psutil.Error as error:
            raise EndpointError(
                "SURFACE_LISTENER_INSPECTION_FAILED",
                "Could not inspect host listeners for endpoint ownership",
            ) from error
        matches = []
        for item in connections:
            if item.status != psutil.CONN_LISTEN or not item.laddr or item.pid is None:
                continue
            try:
                item_address = ipaddress.ip_address(item.laddr.ip).compressed
            except ValueError:
                continue
            if item_address == normalized and item.laddr.port == port:
                matches.append(item)
        if len(matches) != 1:
            return None
        item = matches[0]
        try:
            created = psutil.Process(item.pid).create_time()
        except psutil.Error:
            return None
        return ListenerIdentity(normalized, port, item.pid, created)


class EndpointReservation:
    """An exclusive socket reservation bound to one runtime generation."""

    def __init__(
        self,
        *,
        instance_id: str,
        generation: int,
        address: str,
        port: int,
        inherit_listener: bool,
        held_socket: socket.socket,
    ) -> None:
        self.instance_id = instance_id
        self.generation = generation
        self.address = address
        self.port = port
        self.inherit_listener = inherit_listener
        self._socket: socket.socket | None = held_socket
        self.released_for_spawn = False

    @property
    def listener_handle(self) -> int | None:
        if not self.inherit_listener or self._socket is None:
            return None
        return self._socket.fileno()

    def release_immediately_before_spawn(self) -> None:
        if self.inherit_listener:
            raise EndpointError(
                "SURFACE_ENDPOINT_INHERITED",
                "An inherited listener stays owned through child startup",
            )
        if self.released_for_spawn:
            raise EndpointError(
                "SURFACE_ENDPOINT_ALREADY_RELEASED",
                "Endpoint reservation was already released for spawn",
            )
        if self._socket is None:
            raise EndpointError(
                "SURFACE_ENDPOINT_CLOSED", "Endpoint reservation is already closed"
            )
        self._socket.close()
        self._socket = None
        self.released_for_spawn = True

    def prove_listener_ownership(
        self,
        *,
        runtime: RuntimeIdentity,
        inspector: ListenerInspector,
    ) -> EndpointOwnershipProof:
        if (
            runtime.instance_id != self.instance_id
            or runtime.generation != self.generation
        ):
            raise EndpointError(
                "SURFACE_TARGET_OWNERSHIP_MISMATCH",
                "Runtime generation does not own the reserved endpoint",
            )
        listener = inspector.find_listener(address=self.address, port=self.port)
        if (
            listener is None
            or listener.address != self.address
            or listener.port != self.port
            or (listener.pid, listener.creation_time) not in runtime.owned_processes
        ):
            raise EndpointError(
                "SURFACE_TARGET_OWNERSHIP_MISMATCH",
                "Listener identity does not belong to the expected process tree",
            )
        return EndpointOwnershipProof(
            instance_id=self.instance_id,
            generation=self.generation,
            listener=listener,
        )

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def __enter__(self) -> "EndpointReservation":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


class LoopbackEndpointAllocator:
    """Create exclusive IPv4/IPv6 loopback reservations on ephemeral ports."""

    def __init__(self, *, address: str = "127.0.0.1", backlog: int = 128) -> None:
        try:
            normalized = ipaddress.ip_address(address)
        except ValueError as error:
            raise EndpointError(
                "SURFACE_ENDPOINT_ADDRESS_DENIED", "Endpoint address must be loopback"
            ) from error
        if not normalized.is_loopback:
            raise EndpointError(
                "SURFACE_ENDPOINT_ADDRESS_DENIED", "Endpoint address must be loopback"
            )
        if backlog < 1:
            raise ValueError("endpoint listener backlog must be positive")
        self.address = normalized.compressed
        self.backlog = backlog

    def reserve(
        self,
        *,
        instance_id: str,
        generation: int,
        inherit_listener: bool,
    ) -> EndpointReservation:
        if not instance_id or generation < 1:
            raise EndpointError(
                "SURFACE_ENDPOINT_IDENTITY_INVALID",
                "Endpoint reservation requires an instance and positive generation",
            )
        family = socket.AF_INET6 if ":" in self.address else socket.AF_INET
        held = socket.socket(family, socket.SOCK_STREAM)
        try:
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                held.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            held.set_inheritable(inherit_listener)
            held.bind((self.address, 0))
            if inherit_listener:
                held.listen(self.backlog)
            bound = held.getsockname()
            return EndpointReservation(
                instance_id=instance_id,
                generation=generation,
                address=self.address,
                port=int(bound[1]),
                inherit_listener=inherit_listener,
                held_socket=held,
            )
        except BaseException:
            held.close()
            raise


__all__ = [
    "EndpointError",
    "EndpointOwnershipProof",
    "EndpointReservation",
    "ListenerIdentity",
    "ListenerInspector",
    "LoopbackEndpointAllocator",
    "PsutilListenerInspector",
    "RuntimeIdentity",
]
