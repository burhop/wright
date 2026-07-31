"""Immutable version-1 managed live-application manifest values."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit


class ManifestError(ValueError):
    """A fail-closed live-app declaration error with a stable code."""

    def __init__(self, message: str, *, code: str = "SURFACE_MANIFEST_INVALID") -> None:
        super().__init__(message)
        self.code = code


_ID = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
_ENVIRONMENT = re.compile(r"^[A-Z_][A-Z0-9_]{0,127}$")
_PLACEHOLDER = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")
_DOCUMENTED_PLACEHOLDERS = frozenset(
    {
        "WRIGHT_BIND_HOST",
        "WRIGHT_PORT",
        "WRIGHT_PUBLIC_ORIGIN",
        "WRIGHT_BASE_PATH",
        "WRIGHT_INSTANCE_ID",
    }
)
_CAPABILITIES = frozenset(
    {
        "wright.hostContext.read",
        "wright.userMessage.send",
        "wright.tool.call",
        "wright.resource.read",
        "wright.file.pick",
        "wright.file.read",
        "wright.file.write",
        "wright.download",
        "wright.clipboard.read",
        "wright.clipboard.write",
        "wright.webmcp.register",
    }
)


def _record(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be an object")
    return dict(value)


def _exact(value: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise ManifestError(f"{label}.{unexpected[0]} is not allowed")


def _string(value: Any, label: str, *, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} must be a non-empty string")
    normalized = value.strip()
    if len(normalized) > maximum or "\0" in normalized:
        raise ManifestError(f"{label} is invalid")
    return normalized


def _integer(
    value: Any,
    label: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
        or value > maximum
    ):
        raise ManifestError(f"{label} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True, slots=True)
class SecretReference:
    secret_ref: str


EnvironmentValue = str | SecretReference


@dataclass(frozen=True, slots=True)
class Probe:
    path: str
    method: str
    expected_status: int
    timeout_ms: int
    interval_ms: int


@dataclass(frozen=True, slots=True)
class CommandLaunch:
    argv: tuple[str, ...]
    working_directory: str
    environment: Mapping[str, EnvironmentValue]
    framework: str
    mode: str = "command"


@dataclass(frozen=True, slots=True)
class AttachLaunch:
    url: str
    ownership_proof: str | None
    mode: str = "attach"


@dataclass(frozen=True, slots=True)
class Presentation:
    panel: bool
    browser: bool
    sharing: str
    base_path_mode: str
    allowed_frame_ancestors: tuple[str, ...]
    permissions_policy: frozenset[str]


@dataclass(frozen=True, slots=True)
class Transports:
    http: bool
    websocket: bool
    sse: bool


@dataclass(frozen=True, slots=True)
class Navigation:
    allow_same_target_redirects: bool = True
    external_links: str = "prompt-browser"
    downloads: str = "deny"


@dataclass(frozen=True, slots=True)
class Lifetime:
    policy: str = "workspace"
    lease_seconds: int | None = None
    idle_seconds: int | None = None
    activity_events: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"application-request", "presentation-open", "presentation-traffic"}
        )
    )


_DEFAULT_POLICY: dict[str, int | float] = {
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
    "maximum_header_bytes": 64 * 1024,
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

# manifest key -> policy key, conversion divisor, schema minimum, hard maximum
_LIMIT_FIELDS: dict[str, tuple[str, int, int | float, int | float]] = {
    "startupTimeoutMs": ("startup_timeout_seconds", 1000, 100, 300_000),
    "shutdownTimeoutMs": ("ordinary_stop_timeout_seconds", 1000, 100, 60_000),
    "gracefulShutdownMs": ("graceful_shutdown_seconds", 1000, 100, 30_000),
    "cleanupReconciliationMs": ("cleanup_reconciliation_seconds", 1000, 100, 30_000),
    "maxRestarts": ("restart_attempts", 1, 0, 20),
    "restartWindowMs": ("restart_window_seconds", 1000, 1000, 3_600_000),
    "maxProcesses": ("processes_per_owned_tree", 1, 1, 256),
    "maxCpuCores": ("cpu_cores_per_owned_app", 1, 0.1, 64),
    "maxMemoryMiB": ("memory_mib_per_owned_app", 1, 16, 65_536),
    "maxConnections": ("connections_per_app", 1, 1, 10_000),
    "maxHeaderCount": ("maximum_header_count", 1, 1, 200),
    "maxHeaderBytes": ("maximum_header_bytes", 1, 1024, 1_048_576),
    "maxRequestBytes": ("maximum_request_body_bytes", 1, 1024, 1_073_741_824),
    "maxResponseBytes": ("maximum_response_body_bytes", 1, 1024, 1_073_741_824),
    "maxDecodedBodyBytes": ("maximum_decoded_body_bytes", 1, 1024, 1_073_741_824),
    "maxDecompressionRatio": ("maximum_decompression_ratio", 1, 1, 64),
    "maxBufferedOutputBytes": ("maximum_buffered_output_bytes", 1, 4096, 1_073_741_824),
    "maxRequestRatePerMinute": ("requests_per_presentation_per_minute", 1, 1, 100_000),
    "requestBurst": ("request_burst", 1, 1, 100_000),
    "maxWebSocketMessageBytes": ("websocket_message_bytes", 1, 1024, 67_108_864),
    "maxMessageRatePerSecond": ("websocket_messages_per_second", 1, 1, 100_000),
    "webSocketMessageBurst": ("websocket_message_burst", 1, 1, 100_000),
    "maxStreamBytesPerSecond": ("stream_bytes_per_second", 1, 1024, 1_073_741_824),
    "streamBurstBytes": ("stream_burst_bytes", 1, 1024, 1_073_741_824),
    "firstByteTimeoutMs": ("first_byte_timeout_seconds", 1000, 100, 300_000),
    "httpIdleTimeoutMs": ("http_idle_timeout_seconds", 1000, 100, 3_600_000),
    "streamHeartbeatIdleMs": ("stream_heartbeat_idle_seconds", 1000, 100, 3_600_000),
    "maxConnectionLifetimeMs": (
        "live_connection_lifetime_seconds",
        1000,
        1000,
        86_400_000,
    ),
    "maxLogBytes": ("captured_log_bytes", 1, 4096, 1_073_741_824),
    "maxLogBytesPerSecond": ("captured_log_bytes_per_second", 1, 1024, 67_108_864),
    "logBurstBytes": ("captured_log_burst_bytes", 1, 1024, 67_108_864),
}


@dataclass(frozen=True, slots=True)
class LiveAppLimits:
    _values: Mapping[str, int | float]

    def as_policy_mapping(self) -> dict[str, int | float]:
        return dict(self._values)


@dataclass(frozen=True, slots=True)
class ManifestPlaceholders:
    bind_host: str
    port: int
    public_origin: str
    base_path: str
    instance_id: str

    def values(self) -> dict[str, str]:
        if self.bind_host not in {"127.0.0.1", "::1"}:
            raise ManifestError("WRIGHT_BIND_HOST must be numeric loopback")
        if self.port < 1 or self.port > 65_535:
            raise ManifestError("WRIGHT_PORT is invalid")
        if not self.base_path.startswith("/"):
            raise ManifestError("WRIGHT_BASE_PATH is invalid")
        return {
            "WRIGHT_BIND_HOST": self.bind_host,
            "WRIGHT_PORT": str(self.port),
            "WRIGHT_PUBLIC_ORIGIN": self.public_origin.rstrip("/"),
            "WRIGHT_BASE_PATH": self.base_path,
            "WRIGHT_INSTANCE_ID": self.instance_id,
        }


@dataclass(frozen=True, slots=True)
class ResolvedCommand:
    argv: tuple[str, ...]
    cwd: str
    environment: Mapping[str, str]
    secret_environment_names: frozenset[str]
    shell: bool = False


@dataclass(frozen=True, slots=True)
class ResolvedAttach:
    url: str


@dataclass(frozen=True, slots=True)
class LiveAppManifest:
    schema_version: int
    manifest_id: str
    version: str
    title: str
    description: str | None
    ownership_policy: str
    launch: CommandLaunch | AttachLaunch
    readiness: Probe
    health: Probe | None
    presentation: Presentation
    transports: Transports
    navigation: Navigation
    lifetime: Lifetime
    capabilities: frozenset[str]
    limits: LiveAppLimits
    redaction_environment_names: frozenset[str]
    redaction_query_names: frozenset[str]
    documentation: str | None
    canonical_hash: str

    @property
    def requires_attach_approval(self) -> bool:
        return isinstance(self.launch, AttachLaunch)

    def resolve_command(
        self,
        placeholders: ManifestPlaceholders,
        *,
        secrets: Mapping[str, str],
    ) -> ResolvedCommand:
        if not isinstance(self.launch, CommandLaunch):
            raise ManifestError("manifest launch is not a command")
        values = placeholders.values()

        def interpolate(value: str) -> str:
            unknown = set(_PLACEHOLDER.findall(value)) - _DOCUMENTED_PLACEHOLDERS
            if unknown:
                raise ManifestError(
                    f"unsupported placeholder: {sorted(unknown)[0]}",
                    code="SURFACE_MANIFEST_PLACEHOLDER_INVALID",
                )
            return _PLACEHOLDER.sub(lambda item: values[item.group(1)], value)

        # Resolve every non-secret field first so malformed declarations fail
        # deterministically and cannot be masked by secret-store availability.
        argv = tuple(interpolate(value) for value in self.launch.argv)
        cwd = interpolate(self.launch.working_directory)
        literal_environment = {
            name: interpolate(value)
            for name, value in self.launch.environment.items()
            if isinstance(value, str)
        }
        environment: dict[str, str] = {}
        secret_names: set[str] = set()
        for name, value in self.launch.environment.items():
            if isinstance(value, SecretReference):
                if value.secret_ref not in secrets:
                    raise ManifestError(
                        f"secret reference is unavailable: {value.secret_ref}",
                        code="SURFACE_MANIFEST_SECRET_UNAVAILABLE",
                    )
                environment[name] = secrets[value.secret_ref]
                secret_names.add(name)
            else:
                environment[name] = literal_environment[name]
        environment.update(values)
        return ResolvedCommand(
            argv=argv,
            cwd=cwd,
            environment=MappingProxyType(environment),
            secret_environment_names=frozenset(secret_names),
        )

    def resolve_attach(self, *, administrator_approved: bool) -> ResolvedAttach:
        if not isinstance(self.launch, AttachLaunch):
            raise ManifestError("manifest launch is not approved attach")
        if not administrator_approved:
            raise ManifestError(
                "attach requires explicit administrator approval",
                code="SURFACE_ATTACH_APPROVAL_REQUIRED",
            )
        parts = urlsplit(self.launch.url)
        normalized = urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                parts.path or "/",
                parts.query,
                "",
            )
        )
        return ResolvedAttach(url=normalized)


def _parse_probe(value: Any, label: str) -> Probe:
    record = _record(value, label)
    _exact(
        record,
        {"path", "method", "expectedStatus", "timeoutMs", "intervalMs"},
        label,
    )
    path = _string(record.get("path"), f"{label}.path", maximum=2048)
    if not path.startswith("/") or path.startswith("//"):
        raise ManifestError(f"{label}.path must be an absolute target path")
    method = record.get("method", "GET")
    if method not in {"GET", "HEAD"}:
        raise ManifestError(f"{label}.method is invalid")
    return Probe(
        path=path,
        method=method,
        expected_status=_integer(
            record.get("expectedStatus"),
            f"{label}.expectedStatus",
            minimum=100,
            maximum=599,
        ),
        timeout_ms=_integer(
            record.get("timeoutMs"), f"{label}.timeoutMs", minimum=100, maximum=300_000
        ),
        interval_ms=_integer(
            record.get("intervalMs", 250),
            f"{label}.intervalMs",
            minimum=50,
            maximum=60_000,
        ),
    )


def _parse_launch(value: Any) -> CommandLaunch | AttachLaunch:
    record = _record(value, "launch")
    mode = record.get("mode")
    if mode == "command":
        _exact(
            record,
            {"mode", "argv", "workingDirectory", "environment", "framework"},
            "launch",
        )
        argv_value = record.get("argv")
        if not isinstance(argv_value, list) or not 1 <= len(argv_value) <= 128:
            raise ManifestError(
                "launch.argv must be a non-empty argument array; shell strings are forbidden"
            )
        argv = tuple(_string(item, "launch.argv item") for item in argv_value)
        environment_record = _record(
            record.get("environment", {}), "launch.environment"
        )
        if len(environment_record) > 128:
            raise ManifestError("launch.environment contains too many values")
        environment: dict[str, EnvironmentValue] = {}
        for name, item in environment_record.items():
            if not _ENVIRONMENT.fullmatch(name):
                raise ManifestError("launch.environment name is invalid")
            if isinstance(item, str):
                if len(item) > 8192 or "\0" in item:
                    raise ManifestError("launch.environment value is invalid")
                environment[name] = item
            else:
                secret = _record(item, f"launch.environment.{name}")
                _exact(secret, {"secretRef"}, f"launch.environment.{name}")
                environment[name] = SecretReference(
                    _string(secret.get("secretRef"), "secretRef", maximum=256)
                )
        framework = record.get("framework", "generic")
        if framework not in {
            "generic",
            "fastapi",
            "panel",
            "streamlit",
            "gradio",
            "dash",
        }:
            raise ManifestError("launch.framework is invalid")
        return CommandLaunch(
            argv=argv,
            working_directory=_string(
                record.get("workingDirectory"), "launch.workingDirectory"
            ),
            environment=MappingProxyType(environment),
            framework=framework,
        )
    if mode == "attach":
        _exact(record, {"mode", "url", "ownershipProof"}, "launch")
        url = _string(record.get("url"), "launch.url")
        parts = urlsplit(url)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or parts.fragment
        ):
            raise ManifestError(
                "launch.url must be an absolute HTTP URL without credentials or fragment"
            )
        proof = record.get("ownershipProof")
        if proof is not None and proof not in {
            "shared-secret",
            "health-nonce",
            "process-attestation",
            "operator-approved",
        }:
            raise ManifestError("launch.ownershipProof is invalid")
        return AttachLaunch(url=url, ownership_proof=proof)
    raise ManifestError("launch.mode must be command or attach")


def _parse_limits(value: Any) -> LiveAppLimits:
    declared = _record(value, "limits") if value is not None else {}
    _exact(declared, set(_LIMIT_FIELDS), "limits")
    effective = dict(_DEFAULT_POLICY)
    for manifest_name, raw in declared.items():
        policy_name, divisor, minimum, maximum = _LIMIT_FIELDS[manifest_name]
        if manifest_name == "maxCpuCores":
            if (
                isinstance(raw, bool)
                or not isinstance(raw, (int, float))
                or not minimum <= raw <= maximum
            ):
                raise ManifestError(f"limits.{manifest_name} is invalid")
            converted: int | float = float(raw)
        else:
            validated = _integer(
                raw,
                f"limits.{manifest_name}",
                minimum=int(minimum),
                maximum=int(maximum),
            )
            converted = validated / divisor if divisor != 1 else validated
            if divisor != 1:
                converted = max(0.1, converted)
        effective[policy_name] = min(effective[policy_name], converted)
    return LiveAppLimits(MappingProxyType(effective))


def parse_live_app_manifest(value: Mapping[str, Any]) -> LiveAppManifest:
    record = _record(value, "manifest")
    _exact(
        record,
        {
            "$schema",
            "schemaVersion",
            "id",
            "version",
            "title",
            "description",
            "ownershipPolicy",
            "launch",
            "readiness",
            "health",
            "presentation",
            "transports",
            "navigation",
            "lifetime",
            "capabilities",
            "limits",
            "redaction",
            "documentation",
        },
        "manifest",
    )
    if record.get("schemaVersion") != 1:
        raise ManifestError("schemaVersion must be 1")
    manifest_id = _string(record.get("id"), "id", maximum=128)
    if len(manifest_id) < 3 or not _ID.fullmatch(manifest_id):
        raise ManifestError("id is invalid")
    version = _string(record.get("version"), "version", maximum=64)
    if not _VERSION.fullmatch(version):
        raise ManifestError("version is invalid")
    ownership = record.get("ownershipPolicy")
    launch = _parse_launch(record.get("launch"))
    expected_ownership = (
        "wright-owned" if isinstance(launch, CommandLaunch) else "approved-attach"
    )
    if ownership != expected_ownership:
        raise ManifestError("launch mode and ownership policy are inconsistent")

    presentation_record = _record(record.get("presentation"), "presentation")
    _exact(
        presentation_record,
        {
            "panel",
            "browser",
            "sharing",
            "basePathMode",
            "allowedFrameAncestors",
            "permissionsPolicy",
        },
        "presentation",
    )
    panel = presentation_record.get("panel")
    browser = presentation_record.get("browser")
    if (
        not isinstance(panel, bool)
        or not isinstance(browser, bool)
        or not (panel or browser)
    ):
        raise ManifestError("presentation must enable panel or browser")
    sharing = presentation_record.get("sharing")
    if sharing not in {"shared", "isolated"}:
        raise ManifestError("presentation.sharing is invalid")
    base_path_mode = presentation_record.get("basePathMode", "injected-prefix")
    if base_path_mode not in {"root", "injected-prefix"}:
        raise ManifestError("presentation.basePathMode is invalid")
    ancestors = presentation_record.get("allowedFrameAncestors", [])
    if not isinstance(ancestors, list) or len(ancestors) > 16:
        raise ManifestError("presentation.allowedFrameAncestors is invalid")
    permissions = presentation_record.get("permissionsPolicy", [])
    allowed_permissions = {
        "clipboard-read",
        "clipboard-write",
        "camera",
        "microphone",
        "geolocation",
        "fullscreen",
        "downloads",
        "notifications",
    }
    if (
        not isinstance(permissions, list)
        or len(permissions) != len(set(permissions))
        or not set(permissions) <= allowed_permissions
    ):
        raise ManifestError("presentation.permissionsPolicy is invalid")

    transports_record = _record(record.get("transports"), "transports")
    _exact(transports_record, {"http", "websocket", "sse"}, "transports")
    if set(transports_record) != {"http", "websocket", "sse"} or not all(
        isinstance(transports_record[name], bool) for name in transports_record
    ):
        raise ManifestError("transports must define HTTP, WebSocket, and SSE booleans")
    if (
        transports_record["websocket"] or transports_record["sse"]
    ) and not transports_record["http"]:
        raise ManifestError("WebSocket and SSE transports require HTTP")

    navigation_record = _record(record.get("navigation", {}), "navigation")
    _exact(
        navigation_record,
        {"allowSameTargetRedirects", "externalLinks", "downloads"},
        "navigation",
    )
    allow_redirects = navigation_record.get("allowSameTargetRedirects", True)
    external_links = navigation_record.get("externalLinks", "prompt-browser")
    downloads = navigation_record.get("downloads", "deny")
    if (
        not isinstance(allow_redirects, bool)
        or external_links not in {"deny", "prompt-browser"}
        or downloads not in {"deny", "prompt"}
    ):
        raise ManifestError("navigation is invalid")

    lifetime_record = _record(
        record.get("lifetime", {"policy": "workspace"}), "lifetime"
    )
    _exact(lifetime_record, {"policy", "leaseSeconds", "idleSeconds"}, "lifetime")
    lifetime_policy = lifetime_record.get("policy")
    if lifetime_policy not in {"presentation", "workspace", "lease", "idle", "manual"}:
        raise ManifestError("lifetime.policy is invalid")
    lease = lifetime_record.get("leaseSeconds")
    idle = lifetime_record.get("idleSeconds")
    if lifetime_policy == "lease":
        lease = _integer(lease, "lifetime.leaseSeconds", minimum=30, maximum=86_400)
    elif lease is not None:
        raise ManifestError("leaseSeconds is only valid for lease lifetime")
    if lifetime_policy == "idle":
        idle = _integer(idle, "lifetime.idleSeconds", minimum=30, maximum=86_400)
    elif idle is not None:
        raise ManifestError("idleSeconds is only valid for idle lifetime")

    capabilities = record.get("capabilities")
    if (
        not isinstance(capabilities, list)
        or len(capabilities) > 64
        or len(capabilities) != len(set(capabilities))
        or not set(capabilities) <= _CAPABILITIES
    ):
        raise ManifestError("capabilities are invalid")
    redaction = _record(record.get("redaction", {}), "redaction")
    _exact(redaction, {"environmentNames", "queryNames"}, "redaction")
    environment_names = redaction.get("environmentNames", [])
    query_names = redaction.get("queryNames", [])
    if (
        not isinstance(environment_names, list)
        or not isinstance(query_names, list)
        or len(environment_names) > 128
        or len(query_names) > 128
        or len(environment_names) != len(set(environment_names))
        or len(query_names) != len(set(query_names))
        or any(
            not isinstance(item, str) or not item or len(item) > 128
            for item in (*environment_names, *query_names)
        )
    ):
        raise ManifestError("redaction values must be arrays")
    canonical = json.dumps(
        record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return LiveAppManifest(
        schema_version=1,
        manifest_id=manifest_id,
        version=version,
        title=_string(record.get("title"), "title", maximum=256),
        description=(
            _string(record["description"], "description", maximum=4096)
            if "description" in record
            else None
        ),
        ownership_policy=ownership,
        launch=launch,
        readiness=_parse_probe(record.get("readiness"), "readiness"),
        health=_parse_probe(record["health"], "health") if "health" in record else None,
        presentation=Presentation(
            panel=panel,
            browser=browser,
            sharing=sharing,
            base_path_mode=base_path_mode,
            allowed_frame_ancestors=tuple(
                _string(item, "allowedFrameAncestors item", maximum=2048)
                for item in ancestors
            ),
            permissions_policy=frozenset(permissions),
        ),
        transports=Transports(**transports_record),
        navigation=Navigation(allow_redirects, external_links, downloads),
        lifetime=Lifetime(lifetime_policy, lease, idle),
        capabilities=frozenset(capabilities),
        limits=_parse_limits(record.get("limits")),
        redaction_environment_names=frozenset(environment_names),
        redaction_query_names=frozenset(query_names),
        documentation=(
            _string(record["documentation"], "documentation", maximum=2048)
            if "documentation" in record
            else None
        ),
        canonical_hash=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )


__all__ = [
    "AttachLaunch",
    "CommandLaunch",
    "LiveAppLimits",
    "LiveAppManifest",
    "ManifestError",
    "ManifestPlaceholders",
    "Probe",
    "ResolvedAttach",
    "ResolvedCommand",
    "parse_live_app_manifest",
]
