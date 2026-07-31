"""Most-restrictive Workspace Surface limits and fail-closed enforcement."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import dataclass, fields
from datetime import UTC, datetime, timedelta
from types import MappingProxyType
from typing import Any, Callable, Mapping

from ..config import SurfacePolicySettings


class SurfaceLimitError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        diagnostic: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.diagnostic = dict(diagnostic or {})


@dataclass(frozen=True, slots=True)
class EnforcementCapabilities:
    processes: bool = True
    cpu: bool = True
    memory: bool = True
    connections: bool = True


@dataclass(frozen=True, slots=True)
class LimitDemand:
    owned_apps: int
    processes: int
    cpu_cores: float
    memory_mib: int
    connections: int
    restart_attempts: int
    concurrent_starts: int = 0


class EffectiveSurfaceLimits:
    def __init__(
        self,
        values: Mapping[str, int | float],
        *,
        clock: Callable[[], datetime],
    ) -> None:
        self._values = MappingProxyType(dict(values))
        self.clock = clock
        self._request_windows: dict[str, deque[datetime]] = defaultdict(deque)
        self._message_windows: dict[str, deque[datetime]] = defaultdict(deque)
        self._stream_windows: dict[str, deque[tuple[datetime, int]]] = defaultdict(
            deque
        )
        self._log_windows: dict[str, deque[tuple[datetime, int]]] = defaultdict(deque)

    def __getattr__(self, name: str) -> int | float:
        try:
            return self._values[name]
        except KeyError as error:
            raise AttributeError(name) from error

    @staticmethod
    def _raise(code: str, message: str, **diagnostic: Any) -> None:
        raise SurfaceLimitError(code, message, diagnostic=diagnostic)

    def validate_http(
        self,
        headers: list[tuple[str, str]] | tuple[tuple[str, str], ...],
        *,
        encoded_bytes: int,
        decoded_bytes: int,
    ) -> None:
        if len(headers) > self.maximum_header_count:
            self._raise("SURFACE_LIMIT_HEADER_COUNT", "Surface header count limit exceeded")
        header_bytes = sum(
            len(name.encode("utf-8")) + len(value.encode("utf-8")) + 4
            for name, value in headers
        )
        if header_bytes > self.maximum_header_bytes:
            self._raise("SURFACE_LIMIT_HEADER_BYTES", "Surface header byte limit exceeded")
        if encoded_bytes < 0 or decoded_bytes < 0:
            self._raise("SURFACE_LIMIT_BODY_INVALID", "Surface body size is invalid")
        if encoded_bytes > self.maximum_request_body_bytes:
            self._raise("SURFACE_LIMIT_REQUEST_BODY", "Surface request body limit exceeded")
        if decoded_bytes > self.maximum_decoded_body_bytes:
            self._raise("SURFACE_LIMIT_DECODED_BODY", "Surface decoded body limit exceeded")
        ratio = decoded_bytes / max(1, encoded_bytes)
        if ratio > self.maximum_decompression_ratio:
            self._raise(
                "SURFACE_LIMIT_DECOMPRESSION",
                "Surface decompression ratio limit exceeded",
            )

    def validate_response(self, *, encoded_bytes: int, decoded_bytes: int) -> None:
        if encoded_bytes < 0 or decoded_bytes < 0:
            self._raise("SURFACE_LIMIT_BODY_INVALID", "Surface body size is invalid")
        if encoded_bytes > self.maximum_response_body_bytes:
            self._raise("SURFACE_LIMIT_RESPONSE_BODY", "Surface response body limit exceeded")
        if decoded_bytes > self.maximum_decoded_body_bytes:
            self._raise("SURFACE_LIMIT_DECODED_BODY", "Surface decoded body limit exceeded")
        if decoded_bytes / max(1, encoded_bytes) > self.maximum_decompression_ratio:
            self._raise(
                "SURFACE_LIMIT_DECOMPRESSION",
                "Surface decompression ratio limit exceeded",
            )

    def validate_frame(self, frame: bytes) -> None:
        if len(frame) > self.websocket_message_bytes:
            self._raise("SURFACE_LIMIT_MESSAGE_BYTES", "Surface message byte limit exceeded")

    @staticmethod
    def _json_depth(value: Any, depth: int = 0) -> int:
        if isinstance(value, dict):
            return max(
                (EffectiveSurfaceLimits._json_depth(item, depth + 1) for item in value.values()),
                default=depth + 1,
            )
        if isinstance(value, list):
            return max(
                (EffectiveSurfaceLimits._json_depth(item, depth + 1) for item in value),
                default=depth + 1,
            )
        return depth

    def validate_json(self, value: Any, *, maximum_depth: int = 32) -> None:
        try:
            encoded = json.dumps(value, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError) as error:
            raise SurfaceLimitError(
                "SURFACE_LIMIT_JSON_INVALID", "Surface JSON is invalid"
            ) from error
        if len(encoded) > self.websocket_message_bytes:
            self._raise("SURFACE_LIMIT_MESSAGE_BYTES", "Surface message byte limit exceeded")
        if self._json_depth(value) > maximum_depth:
            self._raise("SURFACE_LIMIT_JSON_DEPTH", "Surface JSON depth limit exceeded")

    def _admit_count(
        self,
        windows: dict[str, deque[datetime]],
        key: str,
        *,
        limit: int,
        label: str,
    ) -> None:
        now = self.clock()
        window = windows[key]
        cutoff = now - timedelta(minutes=1)
        while window and window[0] <= cutoff:
            window.popleft()
        if len(window) >= limit:
            self._raise(
                f"SURFACE_LIMIT_{label.upper()}_RATE",
                f"Surface {label} rate limit exceeded",
            )
        window.append(now)

    def admit_request(self, key: str) -> None:
        self._admit_count(
            self._request_windows,
            key,
            limit=min(
                int(self.requests_per_presentation_per_minute),
                int(self.request_burst),
            ),
            label="request",
        )

    def admit_message(self, key: str) -> None:
        self._admit_count(
            self._message_windows,
            key,
            limit=min(
                int(self.bridge_messages_per_minute),
                int(self.bridge_message_burst),
            ),
            label="message",
        )

    def admit_stream_bytes(self, key: str, amount: int) -> None:
        if amount < 0:
            self._raise("SURFACE_LIMIT_STREAM_INVALID", "Surface stream size is invalid")
        now = self.clock()
        window = self._stream_windows[key]
        cutoff = now - timedelta(seconds=1)
        while window and window[0][0] <= cutoff:
            window.popleft()
        if amount > self.stream_burst_bytes:
            self._raise("SURFACE_LIMIT_STREAM_BURST", "Surface stream burst limit exceeded")
        if sum(item[1] for item in window) + amount > self.stream_bytes_per_second:
            self._raise("SURFACE_LIMIT_STREAM_RATE", "Surface stream rate limit exceeded")
        window.append((now, amount))

    def admit_log_bytes(self, key: str, amount: int) -> None:
        if amount < 0:
            self._raise("SURFACE_LIMIT_LOG_INVALID", "Surface log size is invalid")
        if amount > self.captured_log_burst_bytes:
            self._raise("SURFACE_LIMIT_LOG_BURST", "Surface log burst limit exceeded")
        now = self.clock()
        window = self._log_windows[key]
        cutoff = now - timedelta(seconds=1)
        while window and window[0][0] <= cutoff:
            window.popleft()
        if sum(item[1] for item in window) + amount > self.captured_log_bytes_per_second:
            self._raise("SURFACE_LIMIT_LOG_RATE", "Surface log rate limit exceeded")
        window.append((now, amount))

    def validate_buffers(
        self, *, buffered_output_bytes: int, captured_log_bytes: int
    ) -> None:
        if buffered_output_bytes > self.maximum_buffered_output_bytes:
            self._raise("SURFACE_LIMIT_BUFFER", "Surface buffer limit exceeded")
        if captured_log_bytes > self.captured_log_bytes:
            self._raise("SURFACE_LIMIT_LOG", "Surface log limit exceeded")

    def validate_timing(
        self,
        *,
        first_byte_seconds: float,
        idle_seconds: float,
        lifetime_seconds: float,
    ) -> None:
        values = (
            (
                first_byte_seconds,
                self.first_byte_timeout_seconds,
                "SURFACE_LIMIT_FIRST_BYTE",
                "first-byte timeout",
            ),
            (
                idle_seconds,
                self.http_idle_timeout_seconds,
                "SURFACE_LIMIT_IDLE",
                "idle timeout",
            ),
            (
                lifetime_seconds,
                self.live_connection_lifetime_seconds,
                "SURFACE_LIMIT_LIFETIME",
                "connection lifetime",
            ),
        )
        for actual, limit, code, message in values:
            if actual > limit:
                self._raise(code, f"Surface {message} limit exceeded")

    def validate_runtime(
        self,
        demand: LimitDemand,
        *,
        enforcement: EnforcementCapabilities,
    ) -> None:
        unavailable = [
            resource
            for resource, required, available in (
                ("processes", demand.processes > 0, enforcement.processes),
                ("cpu", demand.cpu_cores > 0, enforcement.cpu),
                ("memory", demand.memory_mib > 0, enforcement.memory),
                ("connections", demand.connections > 0, enforcement.connections),
            )
            if required and not available
        ]
        if unavailable:
            self._raise(
                "SURFACE_LIMIT_ENFORCEMENT_UNAVAILABLE",
                "Surface resource enforcement is unavailable",
                resource=unavailable[0],
            )
        checks = (
            (demand.owned_apps, self.owned_apps_per_workspace, "OWNED_APPS"),
            (
                demand.concurrent_starts,
                self.concurrent_starts_per_workspace,
                "CONCURRENT_STARTS",
            ),
            (demand.processes, self.processes_per_owned_tree, "PROCESSES"),
            (demand.cpu_cores, self.cpu_cores_per_owned_app, "CPU"),
            (demand.memory_mib, self.memory_mib_per_owned_app, "MEMORY"),
            (demand.connections, self.connections_per_app, "CONNECTIONS"),
            (demand.restart_attempts, self.restart_attempts, "RESTARTS"),
        )
        for actual, limit, label in checks:
            if actual > limit:
                self._raise(
                    f"SURFACE_LIMIT_{label}",
                    f"Surface {label.lower().replace('_', ' ')} limit exceeded",
                )


class SurfaceLimitPolicy:
    def __init__(self, defaults: SurfacePolicySettings) -> None:
        self.defaults = defaults
        self._names = {field.name for field in fields(defaults)}

    def compose(
        self,
        *,
        declared: Mapping[str, int | float] | None = None,
        administrator: Mapping[str, int | float] | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> EffectiveSurfaceLimits:
        declared = dict(declared or {})
        administrator = dict(administrator or {})
        unknown = (set(declared) | set(administrator)) - self._names
        if unknown:
            raise SurfaceLimitError(
                "SURFACE_LIMIT_POLICY_INVALID",
                "Surface policy contains an unknown limit",
                diagnostic={"field": sorted(unknown)[0]},
            )
        values: dict[str, int | float] = {}
        for field in fields(self.defaults):
            candidates: list[int | float] = [getattr(self.defaults, field.name)]
            for overrides in (declared, administrator):
                if field.name in overrides:
                    value = overrides[field.name]
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                        raise SurfaceLimitError(
                            "SURFACE_LIMIT_POLICY_INVALID",
                            "Surface policy limits must be positive",
                            diagnostic={"field": field.name},
                        )
                    candidates.append(value)
            selected = min(candidates)
            default = getattr(self.defaults, field.name)
            values[field.name] = float(selected) if isinstance(default, float) else int(selected)
        return EffectiveSurfaceLimits(values, clock=clock)


__all__ = [
    "EffectiveSurfaceLimits",
    "EnforcementCapabilities",
    "LimitDemand",
    "SurfaceLimitError",
    "SurfaceLimitPolicy",
]
