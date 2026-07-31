from __future__ import annotations

import os
from dataclasses import asdict

import pytest

from workspace_service.config import (
    SurfaceFeatureFlags,
    SurfacePolicySettings,
    SurfacePreviewSettings,
)


pytestmark = pytest.mark.workspace_surfaces


def test_version_one_surface_policy_defaults_are_complete(monkeypatch) -> None:
    for name in tuple(os.environ):
        if name.startswith("WRIGHT_SURFACE_"):
            monkeypatch.delenv(name)
    settings = SurfacePolicySettings.from_env()
    assert asdict(settings) == {
        "owned_apps_per_workspace": 8,
        "concurrent_starts_per_workspace": 2,
        "processes_per_owned_tree": 32,
        "cpu_cores_per_owned_app": 2.0,
        "memory_mib_per_owned_app": 2048,
        "restart_attempts": 2,
        "restart_window_seconds": 300,
        "startup_timeout_seconds": 30,
        "graceful_shutdown_seconds": 5,
        "cleanup_reconciliation_seconds": 5,
        "ordinary_stop_timeout_seconds": 10,
        "maximum_header_count": 100,
        "maximum_header_bytes": 65_536,
        "maximum_request_body_bytes": 16_777_216,
        "maximum_response_body_bytes": 67_108_864,
        "maximum_decoded_body_bytes": 67_108_864,
        "maximum_decompression_ratio": 8,
        "maximum_buffered_output_bytes": 4_194_304,
        "connections_per_app": 128,
        "requests_per_presentation_per_minute": 300,
        "request_burst": 60,
        "stream_bytes_per_second": 8_388_608,
        "stream_burst_bytes": 16_777_216,
        "bridge_messages_per_minute": 60,
        "bridge_message_burst": 20,
        "websocket_message_bytes": 4_194_304,
        "websocket_messages_per_second": 100,
        "websocket_message_burst": 200,
        "first_byte_timeout_seconds": 30,
        "http_idle_timeout_seconds": 60,
        "stream_heartbeat_idle_seconds": 90,
        "live_connection_lifetime_seconds": 28_800,
        "captured_log_bytes": 10_485_760,
        "captured_log_bytes_per_second": 262_144,
        "captured_log_burst_bytes": 1_048_576,
        "display_representations": 12,
        "display_envelope_bytes": 16_777_216,
        "graph_points_per_series": 100_000,
        "retained_stateful_hosts_per_workspace": 6,
        "bootstrap_token_ttl_seconds": 60,
        "presentation_revocation_seconds": 2,
    }


def test_surface_rollout_flags_are_default_off(monkeypatch) -> None:
    for name in (
        "WRIGHT_SURFACES_ENABLED",
        "WRIGHT_SURFACES_DISPLAY_ENABLED",
        "WRIGHT_SURFACES_LIVE_APPS_ENABLED",
        "WRIGHT_SURFACES_MCP_APPS_ENABLED",
        "WRIGHT_SURFACES_WEBMCP_ENABLED",
    ):
        monkeypatch.delenv(name, raising=False)
    assert asdict(SurfaceFeatureFlags.from_env()) == {
        "model": False,
        "safe_display": False,
        "live_apps": False,
        "mcp_apps": False,
        "webmcp": False,
    }


def test_preview_and_policy_environment_values_are_validated(monkeypatch) -> None:
    monkeypatch.setenv("WRIGHT_SURFACE_PREVIEW_SCHEME", "https")
    monkeypatch.setenv("WRIGHT_SURFACE_PREVIEW_DOMAIN", "*.preview.example.test")
    monkeypatch.setenv("WRIGHT_SURFACE_BOOTSTRAP_TTL_SECONDS", "45")
    assert SurfacePreviewSettings.from_env().scheme == "https"
    assert SurfacePolicySettings.from_env().bootstrap_token_ttl_seconds == 45

    monkeypatch.setenv("WRIGHT_SURFACE_PREVIEW_DOMAIN", "https://unsafe.example")
    with pytest.raises(ValueError, match="hostname"):
        SurfacePreviewSettings.from_env()
    monkeypatch.setenv("WRIGHT_SURFACE_BOOTSTRAP_TTL_SECONDS", "0")
    with pytest.raises(ValueError, match="positive"):
        SurfacePolicySettings.from_env()
