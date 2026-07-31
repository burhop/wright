from __future__ import annotations

from datetime import UTC, datetime

import pytest

from workspace_service.surfaces.runtime_logs import RuntimeLogBuffer


pytestmark = pytest.mark.workspace_surfaces


class Clock:
    def __init__(self) -> None:
        self.monotonic = 100.0

    def now(self) -> datetime:
        return datetime(2026, 7, 30, tzinfo=UTC)


def test_redacts_secret_values_environment_and_query_fields() -> None:
    clock = Clock()
    logs = RuntimeLogBuffer(
        maximum_bytes=4096,
        bytes_per_second=4096,
        burst_bytes=4096,
        secret_values=("super-secret",),
        environment_names=("API_TOKEN",),
        query_names=("access_token",),
        clock=clock.now,
        monotonic=lambda: clock.monotonic,
    )

    logs.write(
        "stdout",
        b"API_TOKEN=super-secret GET /data?access_token=super-secret&safe=yes\n",
    )

    entry = logs.tail().entries[0]
    assert entry.message == "API_TOKEN=[REDACTED] GET /data?access_token=[REDACTED]&safe=yes"
    assert "super-secret" not in logs.diagnostic_projection()["preview"]


def test_byte_ring_rotates_old_entries_and_reports_gap() -> None:
    clock = Clock()
    logs = RuntimeLogBuffer(
        maximum_bytes=24,
        bytes_per_second=1024,
        burst_bytes=1024,
        clock=clock.now,
        monotonic=lambda: clock.monotonic,
    )
    first = logs.write("stdout", b"first-entry\n")
    logs.write("stderr", b"second-entry\n")
    logs.write("stdout", b"third-entry\n")

    result = logs.tail(after_sequence=first.sequence)
    assert result.rotated is True
    assert [entry.message for entry in result.entries] == ["third-entry"]
    assert logs.retained_bytes <= 24


def test_rate_limit_drops_excess_and_emits_bounded_diagnostic() -> None:
    clock = Clock()
    logs = RuntimeLogBuffer(
        maximum_bytes=4096,
        bytes_per_second=10,
        burst_bytes=10,
        clock=clock.now,
        monotonic=lambda: clock.monotonic,
    )

    logs.write("stdout", b"1234567890")
    dropped = logs.write("stdout", b"too-fast")
    assert dropped.dropped is True
    assert logs.dropped_bytes == len(b"too-fast")
    assert "rate limit" in logs.tail().entries[-1].message

    clock.monotonic += 1.0
    accepted = logs.write("stdout", b"recovered")
    assert accepted.dropped is False


def test_tail_is_bounded_and_rejects_invalid_stream() -> None:
    clock = Clock()
    logs = RuntimeLogBuffer(
        maximum_bytes=4096,
        bytes_per_second=4096,
        burst_bytes=4096,
        clock=clock.now,
        monotonic=lambda: clock.monotonic,
    )
    for value in range(5):
        logs.write("stdout", f"line-{value}".encode())
    assert len(logs.tail(limit=2).entries) == 2
    with pytest.raises(ValueError, match="stream"):
        logs.write("audit", b"no")
