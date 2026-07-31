from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType

import pytest
from jsonschema import Draft202012Validator

from core.surfaces.live_app_manifest import (
    ManifestError,
    ManifestPlaceholders,
    parse_live_app_manifest,
)


pytestmark = pytest.mark.workspace_surfaces

_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA = json.loads(
    (
        _ROOT
        / "packages/core/src/core/surfaces/schemas/v1/live-app-manifest.schema.json"
    ).read_text(encoding="utf-8")
)


def _manifest(**changes):
    value = {
        "schemaVersion": 1,
        "id": "fastapi-dashboard",
        "version": "1.2.3",
        "title": "FastAPI dashboard",
        "ownershipPolicy": "wright-owned",
        "launch": {
            "mode": "command",
            "argv": [
                "python",
                "-m",
                "dashboard",
                "--host",
                "${WRIGHT_BIND_HOST}",
                "--port",
                "${WRIGHT_PORT}",
            ],
            "workingDirectory": ".",
            "environment": {
                "PUBLIC_ORIGIN": "${WRIGHT_PUBLIC_ORIGIN}",
                "API_TOKEN": {"secretRef": "workspace/dashboard-token"},
            },
            "framework": "fastapi",
        },
        "readiness": {
            "path": "/health",
            "method": "GET",
            "expectedStatus": 200,
            "timeoutMs": 10_000,
            "intervalMs": 100,
        },
        "presentation": {
            "panel": True,
            "browser": True,
            "sharing": "shared",
        },
        "transports": {"http": True, "websocket": True, "sse": True},
        "capabilities": [],
    }
    value.update(changes)
    return value


def test_manifest_is_immutable_and_supplies_every_version_one_default() -> None:
    manifest = parse_live_app_manifest(_manifest())

    assert manifest.schema_version == 1
    assert manifest.lifetime.policy == "workspace"
    assert manifest.presentation.base_path_mode == "injected-prefix"
    assert manifest.navigation.allow_same_target_redirects is True
    assert manifest.navigation.external_links == "prompt-browser"
    assert manifest.navigation.downloads == "deny"
    assert manifest.readiness.method == "GET"
    assert manifest.limits.as_policy_mapping() == {
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
        "maximum_request_body_bytes": 16 * 1024 * 1024,
        "maximum_response_body_bytes": 64 * 1024 * 1024,
        "maximum_decoded_body_bytes": 64 * 1024 * 1024,
        "maximum_decompression_ratio": 8,
        "maximum_buffered_output_bytes": 4 * 1024 * 1024,
        "connections_per_app": 128,
        "requests_per_presentation_per_minute": 300,
        "request_burst": 60,
        "stream_bytes_per_second": 8 * 1024 * 1024,
        "stream_burst_bytes": 16 * 1024 * 1024,
        "websocket_message_bytes": 4 * 1024 * 1024,
        "websocket_messages_per_second": 100,
        "websocket_message_burst": 200,
        "first_byte_timeout_seconds": 30,
        "http_idle_timeout_seconds": 60,
        "stream_heartbeat_idle_seconds": 90,
        "live_connection_lifetime_seconds": 8 * 60 * 60,
        "captured_log_bytes": 10 * 1024 * 1024,
        "captured_log_bytes_per_second": 256 * 1024,
        "captured_log_burst_bytes": 1024 * 1024,
    }
    with pytest.raises((TypeError, AttributeError)):
        manifest.title = "changed"  # type: ignore[misc]
    assert isinstance(manifest.launch.environment, MappingProxyType)


def test_command_launch_interpolates_only_documented_values_and_secret_refs() -> None:
    manifest = parse_live_app_manifest(_manifest())
    launch = manifest.resolve_command(
        ManifestPlaceholders(
            bind_host="127.0.0.1",
            port=43123,
            public_origin="http://s-one.localhost:8000",
            base_path="/",
            instance_id="instance-one",
        ),
        secrets={"workspace/dashboard-token": "secret-value"},
    )

    assert launch.argv[-4:] == ("--host", "127.0.0.1", "--port", "43123")
    assert launch.cwd == "."
    assert launch.environment["PUBLIC_ORIGIN"] == "http://s-one.localhost:8000"
    assert launch.environment["API_TOKEN"] == "secret-value"
    assert launch.secret_environment_names == frozenset({"API_TOKEN"})
    assert launch.shell is False

    bad = _manifest()
    bad["launch"] = {**bad["launch"], "argv": ["${HOME}"]}
    with pytest.raises(ManifestError, match="placeholder"):
        parse_live_app_manifest(bad).resolve_command(
            ManifestPlaceholders(
                bind_host="127.0.0.1",
                port=43123,
                public_origin="http://s-one.localhost:8000",
                base_path="/",
                instance_id="instance-one",
            ),
            secrets={},
        )


@pytest.mark.parametrize(
    ("launch", "ownership"),
    [
        ({"mode": "command", "argv": ["python"], "workingDirectory": "."}, "approved-attach"),
        ({"mode": "attach", "url": "http://127.0.0.1:9000"}, "wright-owned"),
    ],
)
def test_launch_mode_and_ownership_are_consistent(launch, ownership) -> None:
    with pytest.raises(ManifestError, match="ownership"):
        parse_live_app_manifest(
            _manifest(launch=launch, ownershipPolicy=ownership)
        )


def test_attach_requires_explicit_approval_and_is_never_treated_as_owned() -> None:
    manifest = parse_live_app_manifest(
        _manifest(
            ownershipPolicy="approved-attach",
            launch={
                "mode": "attach",
                "url": "http://127.0.0.1:9000",
                "ownershipProof": "operator-approved",
            },
        )
    )
    assert manifest.requires_attach_approval is True
    with pytest.raises(ManifestError, match="approval"):
        manifest.resolve_attach(administrator_approved=False)
    assert manifest.resolve_attach(administrator_approved=True).url == (
        "http://127.0.0.1:9000/"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"launch": {"mode": "command", "argv": "python app.py", "workingDirectory": "."}},
        {"presentation": {"panel": False, "browser": False, "sharing": "shared"}},
        {"lifetime": {"policy": "lease"}},
        {"lifetime": {"policy": "idle"}},
        {"lifetime": {"policy": "workspace", "idleSeconds": 60}},
        {"transports": {"http": False, "websocket": True, "sse": False}},
        {"readiness": {"path": "health", "expectedStatus": 200, "timeoutMs": 1000}},
        {"limits": {"maxProcesses": 0}},
    ],
)
def test_invalid_manifest_shapes_fail_closed(changes) -> None:
    with pytest.raises(ManifestError):
        parse_live_app_manifest(_manifest(**changes))


def test_declared_limits_can_only_narrow_effective_policy() -> None:
    manifest = parse_live_app_manifest(
        _manifest(
            limits={
                "startupTimeoutMs": 45_000,
                "maxMemoryMiB": 512,
                "maxRequestBytes": 4096,
                "maxDecodedBodyBytes": 8192,
                "maxDecompressionRatio": 4,
                "requestBurst": 12,
                "maxStreamBytesPerSecond": 2048,
                "streamBurstBytes": 4096,
                "streamHeartbeatIdleMs": 5_000,
            }
        )
    )
    policy = manifest.limits.as_policy_mapping()
    assert policy["startup_timeout_seconds"] == 30
    assert policy["memory_mib_per_owned_app"] == 512
    assert policy["maximum_request_body_bytes"] == 4096
    assert policy["maximum_decoded_body_bytes"] == 8192
    assert policy["maximum_decompression_ratio"] == 4
    assert policy["request_burst"] == 12
    assert policy["stream_bytes_per_second"] == 2048
    assert policy["stream_burst_bytes"] == 4096
    assert policy["stream_heartbeat_idle_seconds"] == 5


def test_schema_and_runtime_cover_every_documented_limit() -> None:
    limits = {
        "startupTimeoutMs": 1_000,
        "shutdownTimeoutMs": 1_000,
        "gracefulShutdownMs": 1_000,
        "cleanupReconciliationMs": 1_000,
        "maxRestarts": 1,
        "restartWindowMs": 1_000,
        "maxProcesses": 4,
        "maxCpuCores": 1,
        "maxMemoryMiB": 256,
        "maxConnections": 32,
        "maxHeaderCount": 10,
        "maxHeaderBytes": 8_192,
        "maxRequestBytes": 2_048,
        "maxResponseBytes": 4_096,
        "maxDecodedBodyBytes": 4_096,
        "maxDecompressionRatio": 2,
        "maxBufferedOutputBytes": 4_096,
        "maxRequestRatePerMinute": 60,
        "requestBurst": 10,
        "maxWebSocketMessageBytes": 1_024,
        "maxMessageRatePerSecond": 10,
        "webSocketMessageBurst": 20,
        "maxStreamBytesPerSecond": 1_024,
        "streamBurstBytes": 1_024,
        "firstByteTimeoutMs": 1_000,
        "httpIdleTimeoutMs": 1_000,
        "streamHeartbeatIdleMs": 1_000,
        "maxConnectionLifetimeMs": 1_000,
        "maxLogBytes": 4_096,
        "maxLogBytesPerSecond": 1_024,
        "logBurstBytes": 1_024,
    }
    document = _manifest(limits=limits)

    Draft202012Validator(_SCHEMA).validate(document)
    assert parse_live_app_manifest(document).limits.as_policy_mapping() == {
        "owned_apps_per_workspace": 8,
        "concurrent_starts_per_workspace": 2,
        "processes_per_owned_tree": 4,
        "cpu_cores_per_owned_app": 1.0,
        "memory_mib_per_owned_app": 256,
        "restart_attempts": 1,
        "restart_window_seconds": 1,
        "startup_timeout_seconds": 1,
        "graceful_shutdown_seconds": 1,
        "cleanup_reconciliation_seconds": 1,
        "ordinary_stop_timeout_seconds": 1,
        "maximum_header_count": 10,
        "maximum_header_bytes": 8_192,
        "maximum_request_body_bytes": 2_048,
        "maximum_response_body_bytes": 4_096,
        "maximum_decoded_body_bytes": 4_096,
        "maximum_decompression_ratio": 2,
        "maximum_buffered_output_bytes": 4_096,
        "connections_per_app": 32,
        "requests_per_presentation_per_minute": 60,
        "request_burst": 10,
        "stream_bytes_per_second": 1_024,
        "stream_burst_bytes": 1_024,
        "websocket_message_bytes": 1_024,
        "websocket_messages_per_second": 10,
        "websocket_message_burst": 20,
        "first_byte_timeout_seconds": 1,
        "http_idle_timeout_seconds": 1,
        "stream_heartbeat_idle_seconds": 1,
        "live_connection_lifetime_seconds": 1,
        "captured_log_bytes": 4_096,
        "captured_log_bytes_per_second": 1_024,
        "captured_log_burst_bytes": 1_024,
    }


def test_idle_lifetime_has_an_exact_activity_definition() -> None:
    manifest = parse_live_app_manifest(
        _manifest(lifetime={"policy": "idle", "idleSeconds": 90})
    )
    assert manifest.lifetime.idle_seconds == 90
    assert manifest.lifetime.activity_events == frozenset(
        {"application-request", "presentation-open", "presentation-traffic"}
    )
