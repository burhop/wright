from __future__ import annotations

import socket

import pytest

from workspace_service.surfaces.endpoints import (
    EndpointError,
    ListenerIdentity,
    LoopbackEndpointAllocator,
    RuntimeIdentity,
)


pytestmark = pytest.mark.workspace_surfaces


class FakeInspector:
    def __init__(self, listener: ListenerIdentity | None) -> None:
        self.listener = listener

    def find_listener(self, *, address: str, port: int) -> ListenerIdentity | None:
        return self.listener


def test_reservation_holds_unique_numeric_loopback_port_until_spawn() -> None:
    allocator = LoopbackEndpointAllocator()
    reservation = allocator.reserve(
        instance_id="instance-1", generation=3, inherit_listener=False
    )
    other = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        assert reservation.address == "127.0.0.1"
        assert reservation.port > 0
        assert reservation.generation == 3
        with pytest.raises(OSError):
            other.bind((reservation.address, reservation.port))

        reservation.release_immediately_before_spawn()
        assert reservation.released_for_spawn is True
        other.bind((reservation.address, reservation.port))
        with pytest.raises(EndpointError, match="already released"):
            reservation.release_immediately_before_spawn()
    finally:
        reservation.close()
        other.close()


def test_inherited_listener_remains_continuously_owned() -> None:
    reservation = LoopbackEndpointAllocator().reserve(
        instance_id="instance-2", generation=1, inherit_listener=True
    )
    try:
        assert reservation.listener_handle is not None
        assert reservation.released_for_spawn is False
        with pytest.raises(EndpointError, match="inherited"):
            reservation.release_immediately_before_spawn()
    finally:
        reservation.close()


def test_listener_ownership_requires_exact_pid_creation_identity_and_generation() -> (
    None
):
    reservation = LoopbackEndpointAllocator().reserve(
        instance_id="instance-3", generation=7, inherit_listener=True
    )
    try:
        runtime = RuntimeIdentity(
            instance_id="instance-3",
            generation=7,
            pid=100,
            creation_time=10.0,
            descendants=((101, 11.0),),
        )
        listener = ListenerIdentity(
            address=reservation.address,
            port=reservation.port,
            pid=101,
            creation_time=11.0,
        )
        proof = reservation.prove_listener_ownership(
            runtime=runtime, inspector=FakeInspector(listener)
        )
        assert proof.listener == listener
        assert proof.instance_id == "instance-3"
        assert proof.generation == 7

        reused = ListenerIdentity(
            address=reservation.address,
            port=reservation.port,
            pid=101,
            creation_time=99.0,
        )
        with pytest.raises(EndpointError) as raised:
            reservation.prove_listener_ownership(
                runtime=runtime, inspector=FakeInspector(reused)
            )
        assert raised.value.code == "SURFACE_TARGET_OWNERSHIP_MISMATCH"
    finally:
        reservation.close()


def test_wrong_generation_or_missing_listener_fails_without_fallback() -> None:
    reservation = LoopbackEndpointAllocator().reserve(
        instance_id="instance-4", generation=2, inherit_listener=True
    )
    try:
        wrong_generation = RuntimeIdentity(
            instance_id="instance-4",
            generation=1,
            pid=100,
            creation_time=10.0,
        )
        with pytest.raises(EndpointError) as raised:
            reservation.prove_listener_ownership(
                runtime=wrong_generation, inspector=FakeInspector(None)
            )
        assert raised.value.code == "SURFACE_TARGET_OWNERSHIP_MISMATCH"
    finally:
        reservation.close()


def test_allocator_rejects_non_loopback_bind_address() -> None:
    with pytest.raises(EndpointError, match="loopback"):
        LoopbackEndpointAllocator(address="0.0.0.0")
