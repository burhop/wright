"""Structured, bounded, secret-safe native lifecycle event logging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .diagnostics import redact
from .models import utc_now


class LifecycleLogger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def emit(self, event: str, *, operation_id: str, **fields: Any) -> None:
        payload = redact(
            {
                "timestamp": utc_now(),
                "event": event,
                "operation_id": operation_id,
                **fields,
            },
            max_string_length=2048,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")
