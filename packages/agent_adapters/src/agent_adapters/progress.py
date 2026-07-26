from __future__ import annotations

import math
from typing import Any, Mapping

TERMINAL_STATUSES = frozenset(
    {"completed", "succeeded", "failed", "cancelled", "timed_out", "timeout"}
)


class GenericProgressProjector:
    """Normalize backend tool progress without provider or tool-name policy."""

    def __init__(self) -> None:
        self._last_progress: dict[str, float] = {}
        self._terminal: set[str] = set()
        self.current_title = "Working on request"

    def start(self, *, elapsed_seconds: float = 0.0) -> dict[str, Any]:
        self.current_title = "Planning request"
        return {
            "status": "running",
            "title": "Planning request",
            "message": "Planning the requested work and preparing available tools.",
            "elapsedSeconds": _elapsed(elapsed_seconds),
        }

    def heartbeat(self, *, elapsed_seconds: float) -> dict[str, Any]:
        return {
            "status": "running",
            "title": self.current_title,
            "message": f"{self.current_title}. Still working.",
            "elapsedSeconds": _elapsed(elapsed_seconds),
            "heartbeat": True,
        }

    def project(
        self, data: Mapping[str, Any], *, elapsed_seconds: float
    ) -> dict[str, Any] | None:
        server = _optional_text(data.get("server") or data.get("server_id"))
        tool = _optional_text(
            data.get("tool") or data.get("tool_name") or data.get("name")
        )
        correlation_id = _optional_text(
            data.get("correlationId")
            or data.get("correlation_id")
            or data.get("requestId")
            or data.get("request_id")
        )
        key = correlation_id or (
            f"{server or ''}:{tool or ''}" if server or tool else "agent"
        )
        status = _status(data.get("status") or data.get("state"))
        if key in self._terminal:
            if status != "running":
                return None
            self._terminal.remove(key)
            self._last_progress.pop(key, None)

        title = _optional_text(data.get("title") or data.get("label"))
        if title is None:
            title = tool or "Tool activity"
        message = _optional_text(
            data.get("message") or data.get("detail") or data.get("description")
        )
        if message is None:
            message = (
                f"{title} completed."
                if status in TERMINAL_STATUSES
                else f"Running {title}."
            )

        result: dict[str, Any] = {
            "status": status,
            "title": title,
            "message": message,
            "elapsedSeconds": _elapsed(elapsed_seconds),
        }
        if server is not None:
            result["server"] = server
        if tool is not None:
            result["tool"] = tool
        if correlation_id is not None:
            result["correlationId"] = correlation_id
        if data.get("heartbeat") is True:
            result["heartbeat"] = True

        progress = _number(data.get("progress"))
        previous = self._last_progress.get(key)
        if progress is not None:
            progress = max(progress, previous) if previous is not None else progress
            self._last_progress[key] = progress
            result["progress"] = progress
        total = _number(data.get("total"))
        if total is not None and total > 0:
            result["total"] = total

        if status in TERMINAL_STATUSES:
            self._terminal.add(key)
            self.current_title = "Working on request"
        elif status == "running":
            self.current_title = title
        return result


def _status(value: Any) -> str:
    normalized = str(value or "running").strip().lower().replace("-", "_")
    aliases = {"complete": "completed", "success": "succeeded", "canceled": "cancelled"}
    return aliases.get(normalized, normalized or "running")


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:512] if text else None


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _elapsed(value: float) -> float:
    return round(max(0.0, value), 1)
