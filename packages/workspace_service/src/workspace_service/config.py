"""Environment-backed Workspace Surfaces feature and safety settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, fields


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _env_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _env_float(name: str, default: float) -> float:
    value = float(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True, slots=True)
class SurfaceFeatureFlags:
    """Independent default-off rollout controls for each surface class."""

    model: bool = False
    safe_display: bool = False
    live_apps: bool = False
    mcp_apps: bool = False
    webmcp: bool = False

    @classmethod
    def from_env(cls) -> "SurfaceFeatureFlags":
        return cls(
            model=_env_bool("WRIGHT_SURFACES_ENABLED", False),
            safe_display=_env_bool("WRIGHT_SURFACES_DISPLAY_ENABLED", False),
            live_apps=_env_bool("WRIGHT_SURFACES_LIVE_APPS_ENABLED", False),
            mcp_apps=_env_bool("WRIGHT_SURFACES_MCP_APPS_ENABLED", False),
            webmcp=_env_bool("WRIGHT_SURFACES_WEBMCP_ENABLED", False),
        )


@dataclass(frozen=True, slots=True)
class SurfacePreviewSettings:
    """Opaque isolated-origin routing configuration."""

    scheme: str = "http"
    bind_host: str = "127.0.0.1"
    domain: str = "localhost"
    public_port: int = 8000

    @classmethod
    def from_env(cls) -> "SurfacePreviewSettings":
        scheme = os.getenv("WRIGHT_SURFACE_PREVIEW_SCHEME", "http").strip().lower()
        if scheme not in {"http", "https"}:
            raise ValueError("WRIGHT_SURFACE_PREVIEW_SCHEME must be http or https")
        domain = os.getenv("WRIGHT_SURFACE_PREVIEW_DOMAIN", "localhost").strip()
        if not domain or "://" in domain or "/" in domain:
            raise ValueError("WRIGHT_SURFACE_PREVIEW_DOMAIN must be a hostname")
        return cls(
            scheme=scheme,
            bind_host=os.getenv(
                "WRIGHT_SURFACE_PREVIEW_BIND_HOST", "127.0.0.1"
            ).strip(),
            domain=domain,
            public_port=_env_int("WRIGHT_SURFACE_PREVIEW_PORT", 8000),
        )


@dataclass(frozen=True, slots=True)
class SurfacePolicySettings:
    """Version-1 safe defaults from ``policy-defaults.md``.

    Values are fallback policy, never an unlimited state. Later policy
    composition chooses the most restrictive hard, administrator, declaration,
    and version-default value.
    """

    owned_apps_per_workspace: int = 8
    concurrent_starts_per_workspace: int = 2
    processes_per_owned_tree: int = 32
    cpu_cores_per_owned_app: float = 2.0
    memory_mib_per_owned_app: int = 2048
    restart_attempts: int = 2
    restart_window_seconds: int = 300
    startup_timeout_seconds: int = 30
    graceful_shutdown_seconds: int = 5
    cleanup_reconciliation_seconds: int = 5
    ordinary_stop_timeout_seconds: int = 10
    maximum_header_count: int = 100
    maximum_header_bytes: int = 64 * 1024
    maximum_request_body_bytes: int = 16 * 1024 * 1024
    maximum_response_body_bytes: int = 64 * 1024 * 1024
    maximum_decoded_body_bytes: int = 64 * 1024 * 1024
    maximum_decompression_ratio: int = 8
    maximum_buffered_output_bytes: int = 4 * 1024 * 1024
    connections_per_app: int = 128
    requests_per_presentation_per_minute: int = 300
    request_burst: int = 60
    stream_bytes_per_second: int = 8 * 1024 * 1024
    stream_burst_bytes: int = 16 * 1024 * 1024
    bridge_messages_per_minute: int = 60
    bridge_message_burst: int = 20
    websocket_message_bytes: int = 4 * 1024 * 1024
    websocket_messages_per_second: int = 100
    websocket_message_burst: int = 200
    first_byte_timeout_seconds: int = 30
    http_idle_timeout_seconds: int = 60
    stream_heartbeat_idle_seconds: int = 90
    live_connection_lifetime_seconds: int = 8 * 60 * 60
    captured_log_bytes: int = 10 * 1024 * 1024
    captured_log_bytes_per_second: int = 256 * 1024
    captured_log_burst_bytes: int = 1024 * 1024
    display_representations: int = 12
    display_envelope_bytes: int = 16 * 1024 * 1024
    graph_points_per_series: int = 100_000
    retained_stateful_hosts_per_workspace: int = 6
    bootstrap_token_ttl_seconds: int = 60
    presentation_revocation_seconds: int = 2

    @classmethod
    def from_env(cls) -> "SurfacePolicySettings":
        integer_values = {
            "owned_apps_per_workspace": ("WRIGHT_SURFACE_MAX_APPS", 8),
            "concurrent_starts_per_workspace": ("WRIGHT_SURFACE_MAX_STARTS", 2),
            "processes_per_owned_tree": ("WRIGHT_SURFACE_MAX_PROCESSES", 32),
            "memory_mib_per_owned_app": ("WRIGHT_SURFACE_MEMORY_MIB", 2048),
            "restart_attempts": ("WRIGHT_SURFACE_RESTART_ATTEMPTS", 2),
            "restart_window_seconds": ("WRIGHT_SURFACE_RESTART_WINDOW_SECONDS", 300),
            "startup_timeout_seconds": ("WRIGHT_SURFACE_STARTUP_TIMEOUT_SECONDS", 30),
            "graceful_shutdown_seconds": ("WRIGHT_SURFACE_GRACEFUL_STOP_SECONDS", 5),
            "cleanup_reconciliation_seconds": ("WRIGHT_SURFACE_CLEANUP_SECONDS", 5),
            "ordinary_stop_timeout_seconds": (
                "WRIGHT_SURFACE_STOP_TIMEOUT_SECONDS",
                10,
            ),
            "maximum_header_count": ("WRIGHT_SURFACE_MAX_HEADER_COUNT", 100),
            "maximum_header_bytes": ("WRIGHT_SURFACE_MAX_HEADER_BYTES", 65536),
            "maximum_request_body_bytes": (
                "WRIGHT_SURFACE_MAX_REQUEST_BYTES",
                16777216,
            ),
            "maximum_response_body_bytes": (
                "WRIGHT_SURFACE_MAX_RESPONSE_BYTES",
                67108864,
            ),
            "maximum_decoded_body_bytes": (
                "WRIGHT_SURFACE_MAX_DECODED_BYTES",
                67108864,
            ),
            "maximum_decompression_ratio": (
                "WRIGHT_SURFACE_MAX_DECOMPRESSION_RATIO",
                8,
            ),
            "maximum_buffered_output_bytes": (
                "WRIGHT_SURFACE_MAX_BUFFERED_BYTES",
                4194304,
            ),
            "connections_per_app": ("WRIGHT_SURFACE_MAX_CONNECTIONS", 128),
            "requests_per_presentation_per_minute": (
                "WRIGHT_SURFACE_REQUESTS_PER_MINUTE",
                300,
            ),
            "request_burst": ("WRIGHT_SURFACE_REQUEST_BURST", 60),
            "stream_bytes_per_second": (
                "WRIGHT_SURFACE_STREAM_BYTES_PER_SECOND",
                8388608,
            ),
            "stream_burst_bytes": ("WRIGHT_SURFACE_STREAM_BURST_BYTES", 16777216),
            "bridge_messages_per_minute": (
                "WRIGHT_SURFACE_BRIDGE_MESSAGES_PER_MINUTE",
                60,
            ),
            "bridge_message_burst": ("WRIGHT_SURFACE_BRIDGE_MESSAGE_BURST", 20),
            "websocket_message_bytes": ("WRIGHT_SURFACE_WS_MESSAGE_BYTES", 4194304),
            "websocket_messages_per_second": (
                "WRIGHT_SURFACE_WS_MESSAGES_PER_SECOND",
                100,
            ),
            "websocket_message_burst": ("WRIGHT_SURFACE_WS_MESSAGE_BURST", 200),
            "first_byte_timeout_seconds": ("WRIGHT_SURFACE_FIRST_BYTE_SECONDS", 30),
            "http_idle_timeout_seconds": ("WRIGHT_SURFACE_HTTP_IDLE_SECONDS", 60),
            "stream_heartbeat_idle_seconds": ("WRIGHT_SURFACE_STREAM_IDLE_SECONDS", 90),
            "live_connection_lifetime_seconds": (
                "WRIGHT_SURFACE_CONNECTION_LIFETIME_SECONDS",
                28800,
            ),
            "captured_log_bytes": ("WRIGHT_SURFACE_CAPTURED_LOG_BYTES", 10485760),
            "captured_log_bytes_per_second": (
                "WRIGHT_SURFACE_LOG_BYTES_PER_SECOND",
                262144,
            ),
            "captured_log_burst_bytes": ("WRIGHT_SURFACE_LOG_BURST_BYTES", 1048576),
            "display_representations": ("WRIGHT_SURFACE_DISPLAY_REPRESENTATIONS", 12),
            "display_envelope_bytes": (
                "WRIGHT_SURFACE_DISPLAY_ENVELOPE_BYTES",
                16777216,
            ),
            "graph_points_per_series": (
                "WRIGHT_SURFACE_GRAPH_POINTS_PER_SERIES",
                100000,
            ),
            "retained_stateful_hosts_per_workspace": (
                "WRIGHT_SURFACE_RETAINED_HOSTS",
                6,
            ),
            "bootstrap_token_ttl_seconds": ("WRIGHT_SURFACE_BOOTSTRAP_TTL_SECONDS", 60),
            "presentation_revocation_seconds": ("WRIGHT_SURFACE_REVOCATION_SECONDS", 2),
        }
        values = {
            name: _env_int(env, default)
            for name, (env, default) in integer_values.items()
        }
        values["cpu_cores_per_owned_app"] = _env_float("WRIGHT_SURFACE_CPU_CORES", 2.0)
        settings = cls(**values)
        if {item.name for item in fields(cls)} != set(values):
            raise RuntimeError("surface policy environment mapping is incomplete")
        return settings


@dataclass(frozen=True, slots=True)
class WorkspaceSurfaceSettings:
    flags: SurfaceFeatureFlags
    preview: SurfacePreviewSettings
    policy: SurfacePolicySettings

    @classmethod
    def from_env(cls) -> "WorkspaceSurfaceSettings":
        return cls(
            flags=SurfaceFeatureFlags.from_env(),
            preview=SurfacePreviewSettings.from_env(),
            policy=SurfacePolicySettings.from_env(),
        )
