"""Bounded, rate-limited, redacted live-application runtime logs."""

from __future__ import annotations

import re
import threading
import time
from collections import deque
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class RuntimeLogEntry:
    sequence: int
    stream: str
    message: str
    captured_at: datetime
    byte_count: int


@dataclass(frozen=True, slots=True)
class RuntimeLogWrite:
    sequence: int
    dropped: bool


@dataclass(frozen=True, slots=True)
class RuntimeLogTail:
    entries: tuple[RuntimeLogEntry, ...]
    rotated: bool
    dropped_bytes: int
    next_sequence: int


class RuntimeLogBuffer:
    """A byte-bounded ring with a token bucket before log persistence."""

    def __init__(
        self,
        *,
        maximum_bytes: int,
        bytes_per_second: int,
        burst_bytes: int,
        secret_values: Iterable[str] = (),
        environment_names: Iterable[str] = (),
        query_names: Iterable[str] = (),
        clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        if minimum := min(maximum_bytes, bytes_per_second, burst_bytes):
            if minimum < 1:
                raise ValueError("runtime log bounds must be positive")
        else:
            raise ValueError("runtime log bounds must be positive")
        self.maximum_bytes = maximum_bytes
        self.bytes_per_second = bytes_per_second
        self.burst_bytes = burst_bytes
        self._secrets = tuple(
            sorted({value for value in secret_values if value}, key=len, reverse=True)
        )
        self._environment_names = tuple(sorted(set(environment_names)))
        self._query_names = tuple(sorted(set(query_names)))
        self._clock = clock or (lambda: datetime.now(UTC))
        self._monotonic = monotonic or time.monotonic
        self._entries: deque[RuntimeLogEntry] = deque()
        self._retained_bytes = 0
        self._dropped_bytes = 0
        self._next_sequence = 1
        self._tokens = float(burst_bytes)
        self._last_refill = self._monotonic()
        self._drop_marker_active = False
        self._lock = threading.RLock()

    @property
    def retained_bytes(self) -> int:
        with self._lock:
            return self._retained_bytes

    @property
    def dropped_bytes(self) -> int:
        with self._lock:
            return self._dropped_bytes

    def _redact(self, message: str) -> str:
        result = message
        for name in self._environment_names:
            result = re.sub(
                rf"(?i)(?<![A-Z0-9_])({re.escape(name)})\s*=\s*([^\s&]+)",
                r"\1=[REDACTED]",
                result,
            )
        for name in self._query_names:
            result = re.sub(
                rf"(?i)([?&]{re.escape(name)}=)[^&#\s]*",
                r"\1[REDACTED]",
                result,
            )
        for secret in self._secrets:
            result = result.replace(secret, "[REDACTED]")
        return result

    def _append(self, *, stream: str, message: str, byte_count: int) -> RuntimeLogEntry:
        entry = RuntimeLogEntry(
            sequence=self._next_sequence,
            stream=stream,
            message=message,
            captured_at=self._clock(),
            byte_count=min(byte_count, self.maximum_bytes),
        )
        self._next_sequence += 1
        self._entries.append(entry)
        self._retained_bytes += entry.byte_count
        while self._entries and self._retained_bytes > self.maximum_bytes:
            removed = self._entries.popleft()
            self._retained_bytes -= removed.byte_count
        return entry

    def _refill(self) -> None:
        current = self._monotonic()
        elapsed = max(0.0, current - self._last_refill)
        self._tokens = min(
            float(self.burst_bytes), self._tokens + elapsed * self.bytes_per_second
        )
        self._last_refill = current

    def write(self, stream: str, payload: bytes) -> RuntimeLogWrite:
        if stream not in {"stdout", "stderr", "system"}:
            raise ValueError("runtime log stream must be stdout, stderr, or system")
        if not isinstance(payload, bytes):
            raise TypeError("runtime log payload must be bytes")
        with self._lock:
            self._refill()
            byte_count = len(payload)
            if byte_count > self._tokens:
                self._dropped_bytes += byte_count
                if not self._drop_marker_active:
                    marker = self._append(
                        stream="system",
                        message="Runtime log rate limit exceeded; output was dropped.",
                        byte_count=64,
                    )
                    self._drop_marker_active = True
                    sequence = marker.sequence
                else:
                    sequence = self._next_sequence - 1
                return RuntimeLogWrite(sequence=sequence, dropped=True)
            self._tokens -= byte_count
            self._drop_marker_active = False
            decoded = payload.decode("utf-8", errors="replace").rstrip("\r\n")
            entry = self._append(
                stream=stream,
                message=self._redact(decoded),
                byte_count=byte_count,
            )
            return RuntimeLogWrite(sequence=entry.sequence, dropped=False)

    def tail(self, *, after_sequence: int = 0, limit: int = 200) -> RuntimeLogTail:
        if after_sequence < 0 or not 1 <= limit <= 1000:
            raise ValueError("runtime log tail bounds are invalid")
        with self._lock:
            oldest = self._entries[0].sequence if self._entries else self._next_sequence
            selected = [
                entry for entry in self._entries if entry.sequence > after_sequence
            ][-limit:]
            return RuntimeLogTail(
                entries=tuple(selected),
                rotated=after_sequence > 0 and after_sequence < oldest,
                dropped_bytes=self._dropped_bytes,
                next_sequence=self._next_sequence,
            )

    def diagnostic_projection(self) -> dict[str, object]:
        with self._lock:
            preview = "\n".join(entry.message for entry in list(self._entries)[-20:])
            return {
                "preview": preview[-4096:],
                "retained_bytes": self._retained_bytes,
                "dropped_bytes": self._dropped_bytes,
                "oldest_sequence": (
                    self._entries[0].sequence if self._entries else self._next_sequence
                ),
                "next_sequence": self._next_sequence,
            }


__all__ = [
    "RuntimeLogBuffer",
    "RuntimeLogEntry",
    "RuntimeLogTail",
    "RuntimeLogWrite",
]
