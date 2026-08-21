from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.config import SurfacePolicySettings
from workspace_service.surfaces.limits import (
    EnforcementCapabilities,
    LimitDemand,
    SurfaceLimitError,
    SurfaceLimitPolicy,
)


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def test_declared_and_administrator_limits_can_only_narrow_defaults() -> None:
    policy = SurfaceLimitPolicy(SurfacePolicySettings())
    effective = policy.compose(
        declared={"maximum_request_body_bytes": 1024, "cpu_cores_per_owned_app": 1.5},
        administrator={"maximum_request_body_bytes": 512, "memory_mib_per_owned_app": 512},
    )
    assert effective.maximum_request_body_bytes == 512
    assert effective.cpu_cores_per_owned_app == 1.5
    assert effective.memory_mib_per_owned_app == 512
    with pytest.raises(SurfaceLimitError, match="unknown"):
        policy.compose(declared={"unlimited_memory": 1})
    with pytest.raises(SurfaceLimitError, match="positive"):
        policy.compose(administrator={"maximum_header_count": 0})


def test_http_json_and_decompression_limits_fail_closed() -> None:
    effective = SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator={
            "maximum_header_count": 2,
            "maximum_header_bytes": 32,
            "maximum_request_body_bytes": 16,
            "maximum_decoded_body_bytes": 24,
            "maximum_decompression_ratio": 2,
            "websocket_message_bytes": 64,
        }
    )
    effective.validate_http([("a", "1"), ("b", "2")], encoded_bytes=8, decoded_bytes=16)
    with pytest.raises(SurfaceLimitError) as headers:
        effective.validate_http(
            [("a", "1"), ("b", "2"), ("c", "3")],
            encoded_bytes=1,
            decoded_bytes=1,
        )
    assert headers.value.code == "SURFACE_LIMIT_HEADER_COUNT"
    with pytest.raises(SurfaceLimitError) as body:
        effective.validate_http([], encoded_bytes=13, decoded_bytes=25)
    assert body.value.code == "SURFACE_LIMIT_DECODED_BODY"
    with pytest.raises(SurfaceLimitError) as depth:
        effective.validate_json({"a": {"b": {"c": True}}}, maximum_depth=2)
    assert depth.value.code == "SURFACE_LIMIT_JSON_DEPTH"


def test_each_http_response_frame_and_decompression_bound_has_a_stable_code() -> None:
    effective = SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator={
            "maximum_header_count": 2,
            "maximum_header_bytes": 12,
            "maximum_request_body_bytes": 8,
            "maximum_response_body_bytes": 10,
            "maximum_decoded_body_bytes": 20,
            "maximum_decompression_ratio": 2,
            "websocket_message_bytes": 16,
        }
    )
    cases = [
        (
            lambda: effective.validate_http(
                [("long-name", "long-value")], encoded_bytes=1, decoded_bytes=1
            ),
            "SURFACE_LIMIT_HEADER_BYTES",
        ),
        (
            lambda: effective.validate_http([], encoded_bytes=9, decoded_bytes=9),
            "SURFACE_LIMIT_REQUEST_BODY",
        ),
        (
            lambda: effective.validate_http([], encoded_bytes=8, decoded_bytes=17),
            "SURFACE_LIMIT_DECOMPRESSION",
        ),
        (
            lambda: effective.validate_response(encoded_bytes=11, decoded_bytes=11),
            "SURFACE_LIMIT_RESPONSE_BODY",
        ),
        (
            lambda: effective.validate_response(encoded_bytes=10, decoded_bytes=21),
            "SURFACE_LIMIT_DECODED_BODY",
        ),
        (
            lambda: effective.validate_frame(b"x" * 17),
            "SURFACE_LIMIT_MESSAGE_BYTES",
        ),
    ]
    for operation, expected in cases:
        with pytest.raises(SurfaceLimitError) as failure:
            operation()
        assert failure.value.code == expected


def test_rate_stream_buffer_log_and_time_limits_are_independent() -> None:
    clock = [NOW]
    effective = SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator={
            "requests_per_presentation_per_minute": 2,
            "bridge_messages_per_minute": 2,
            "stream_bytes_per_second": 10,
            "stream_burst_bytes": 10,
            "maximum_buffered_output_bytes": 16,
            "captured_log_bytes": 20,
            "captured_log_bytes_per_second": 8,
            "captured_log_burst_bytes": 8,
            "first_byte_timeout_seconds": 3,
            "http_idle_timeout_seconds": 4,
            "live_connection_lifetime_seconds": 5,
        },
        clock=lambda: clock[0],
    )
    effective.admit_request("presentation")
    effective.admit_request("presentation")
    with pytest.raises(SurfaceLimitError, match="request rate"):
        effective.admit_request("presentation")
    effective.admit_message("presentation")
    effective.admit_message("presentation")
    with pytest.raises(SurfaceLimitError, match="message rate"):
        effective.admit_message("presentation")
    effective.admit_stream_bytes("presentation", 10)
    with pytest.raises(SurfaceLimitError, match="stream rate"):
        effective.admit_stream_bytes("presentation", 1)
    effective.admit_log_bytes("runtime", 8)
    with pytest.raises(SurfaceLimitError, match="log rate"):
        effective.admit_log_bytes("runtime", 1)
    with pytest.raises(SurfaceLimitError, match="buffer"):
        effective.validate_buffers(buffered_output_bytes=17, captured_log_bytes=1)
    with pytest.raises(SurfaceLimitError, match="log"):
        effective.validate_buffers(buffered_output_bytes=1, captured_log_bytes=21)
    for values in ((4, 0, 0), (0, 5, 0), (0, 0, 6)):
        with pytest.raises(SurfaceLimitError):
            effective.validate_timing(
                first_byte_seconds=values[0],
                idle_seconds=values[1],
                lifetime_seconds=values[2],
            )
    clock[0] += timedelta(minutes=1, seconds=1)
    effective.admit_request("presentation")


def test_stream_rate_uses_burst_capacity_and_refills_at_sustained_rate() -> None:
    clock = [NOW]
    effective = SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator={
            "stream_bytes_per_second": 10,
            "stream_burst_bytes": 20,
        },
        clock=lambda: clock[0],
    )

    effective.admit_stream_bytes("presentation", 20)
    with pytest.raises(SurfaceLimitError, match="stream rate"):
        effective.admit_stream_bytes("presentation", 1)

    clock[0] += timedelta(seconds=0.5)
    effective.admit_stream_bytes("presentation", 5)
    with pytest.raises(SurfaceLimitError, match="stream rate"):
        effective.admit_stream_bytes("presentation", 1)


def test_runtime_demands_and_degraded_enforcement_are_denied_with_code() -> None:
    effective = SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator={
            "owned_apps_per_workspace": 1,
            "processes_per_owned_tree": 2,
            "cpu_cores_per_owned_app": 1,
            "memory_mib_per_owned_app": 256,
            "connections_per_app": 4,
            "restart_attempts": 1,
            "concurrent_starts_per_workspace": 1,
        }
    )
    effective.validate_runtime(
        LimitDemand(
            owned_apps=1,
            processes=2,
            cpu_cores=1,
            memory_mib=256,
            connections=4,
            restart_attempts=1,
        ),
        enforcement=EnforcementCapabilities(),
    )
    with pytest.raises(SurfaceLimitError) as exceeded:
        effective.validate_runtime(
            LimitDemand(2, 2, 1, 256, 4, 1),
            enforcement=EnforcementCapabilities(),
        )
    assert exceeded.value.code == "SURFACE_LIMIT_OWNED_APPS"
    with pytest.raises(SurfaceLimitError) as degraded:
        effective.validate_runtime(
            LimitDemand(1, 2, 1, 256, 4, 1),
            enforcement=EnforcementCapabilities(memory=False),
        )
    assert degraded.value.code == "SURFACE_LIMIT_ENFORCEMENT_UNAVAILABLE"
    assert degraded.value.diagnostic["resource"] == "memory"


def test_every_runtime_resource_and_restart_bound_has_a_stable_code() -> None:
    effective = SurfaceLimitPolicy(SurfacePolicySettings()).compose(
        administrator={
            "owned_apps_per_workspace": 1,
            "concurrent_starts_per_workspace": 1,
            "processes_per_owned_tree": 2,
            "cpu_cores_per_owned_app": 1,
            "memory_mib_per_owned_app": 256,
            "connections_per_app": 4,
            "restart_attempts": 1,
        }
    )
    allowed = LimitDemand(1, 2, 1, 256, 4, 1, concurrent_starts=1)
    for changed, expected in (
        ({"owned_apps": 2}, "SURFACE_LIMIT_OWNED_APPS"),
        ({"concurrent_starts": 2}, "SURFACE_LIMIT_CONCURRENT_STARTS"),
        ({"processes": 3}, "SURFACE_LIMIT_PROCESSES"),
        ({"cpu_cores": 2}, "SURFACE_LIMIT_CPU"),
        ({"memory_mib": 257}, "SURFACE_LIMIT_MEMORY"),
        ({"connections": 5}, "SURFACE_LIMIT_CONNECTIONS"),
        ({"restart_attempts": 2}, "SURFACE_LIMIT_RESTARTS"),
    ):
        with pytest.raises(SurfaceLimitError) as failure:
            effective.validate_runtime(
                replace(allowed, **changed),
                enforcement=EnforcementCapabilities(),
            )
        assert failure.value.code == expected
