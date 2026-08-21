from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from fakes import (
    FakeDiskReservation,
    FakeHostObserver,
    FakeSecretReferences,
    FakeTransport,
    FrozenClock,
)


def test_frozen_clock_and_host_observer_are_explicit_and_repeatable() -> None:
    start = datetime(2026, 8, 13, tzinfo=UTC)
    clock = FrozenClock(start)
    observer = FakeHostObserver.reference()

    assert clock.now() == start
    clock.advance(timedelta(seconds=3))
    assert clock.now() == start + timedelta(seconds=3)
    assert observer.observe().platform == "windows"
    assert observer.calls == 1


def test_disk_reservations_are_bounded_releasable_and_fail_closed() -> None:
    disk = FakeDiskReservation(capacity_bytes=10)
    first = disk.reserve("operation-1", 7)
    assert disk.available_bytes == 3
    with pytest.raises(ValueError, match="disk"):
        disk.reserve("operation-2", 4)
    first.release()
    assert disk.available_bytes == 10
    first.release()
    assert disk.available_bytes == 10


def test_secret_references_and_transport_never_expose_secret_values() -> None:
    secrets = FakeSecretReferences({"hf-read": "synthetic-private-value"})
    transport = FakeTransport([{"state": "ok"}])

    assert secrets.contains("hf-read")
    assert secrets.resolve_for_source("hf-read") == "synthetic-private-value"
    assert "synthetic-private-value" not in repr(secrets)
    assert transport.request({"kind": "health"}) == {"state": "ok"}
    assert transport.requests == ({"kind": "health"},)
    transport.cancel("request-1")
    assert transport.cancelled == ("request-1",)
