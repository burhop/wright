"""Local, observational development history; never a release/approval authority.

SQLite transactions make concurrent collector and agent writes atomic. Event IDs
are idempotency keys. Timestamps describe observation time, not inferred effort.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FILENAME = "development-metrics.sqlite3"
STATES = (
    "queued",
    "working",
    "qa",
    "implemented",
    "verified",
    "integrated",
    "withdrawn",
    "manual_validation",
)
KINDS = ("snapshot", "task", "activity", "qa", "usage", "heartbeat")
LIMIT = 20000


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_event(event: dict[str, Any]) -> None:
    """Closed event vocabulary, bounded strings, explicit evidence for closure."""
    required = {"id", "at", "kind", "feature", "subject", "data"}
    if set(event) != required or event["kind"] not in KINDS:
        raise ValueError("Invalid metrics event fields or kind")
    for key in ("id", "at", "feature", "subject"):
        if not isinstance(event[key], str) or not 1 <= len(event[key]) <= 200:
            raise ValueError(f"Invalid {key}")
    when = datetime.fromisoformat(event["at"].replace("Z", "+00:00"))
    if when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("Observation time requires timezone")
    if when > datetime.now(timezone.utc):
        raise ValueError("Observation time cannot be in the future")
    data = event["data"]
    if not isinstance(data, dict) or len(json.dumps(event)) > 512000:
        raise ValueError("Invalid or oversized metrics data")
    fields = {
        "snapshot": {"tasks"},
        "task": {"task", "title", "state", "evidence"},
        "activity": {"task", "stage", "status", "summary"},
        "qa": {
            "suite",
            "environment",
            "passed",
            "failed",
            "skipped",
            "not_run",
            "evidence",
        },
        "usage": {"session", "task", "input_tokens", "output_tokens"},
        "heartbeat": {"status"},
    }
    optional = {"reason", "action", "owner"} if event["kind"] == "task" else set()
    if set(data) - optional != fields[event["kind"]]:
        raise ValueError("Invalid event data fields")
    if event["kind"] == "snapshot":
        if not isinstance(data["tasks"], list) or len(data["tasks"]) > 10000:
            raise ValueError("Invalid task population")
        ids = set()
        for task in data["tasks"]:
            if set(task) != {"task", "title", "checked"}:
                raise ValueError("Invalid task snapshot")
            if not isinstance(task["checked"], bool):
                raise ValueError("Invalid checkbox")
            if not isinstance(task["task"], str) or not re.fullmatch(
                r"T\d+", task["task"]
            ):
                raise ValueError("Invalid task ID")
            if not isinstance(task["title"], str) or len(task["title"]) > 1000:
                raise ValueError("Invalid task title")
            if task["task"] in ids:
                raise ValueError("Duplicate task ID")
            ids.add(task["task"])
    else:
        for key, value in data.items():
            if key == "not_run" and value is None:
                continue
            if key in {
                "passed",
                "failed",
                "skipped",
                "not_run",
                "input_tokens",
                "output_tokens",
            }:
                if type(value) is not int or not 0 <= value <= 10**12:
                    raise ValueError("Invalid count")
            elif not isinstance(value, str) or len(value) > 1000:
                raise ValueError("Invalid event text")
        if event["kind"] == "task":
            if data["state"] not in STATES:
                raise ValueError("Invalid task state")
            if (
                data["state"] in {"verified", "integrated"}
                and not data["evidence"].strip()
            ):
                raise ValueError("Verified/integrated requires evidence reference")
        if event["kind"] == "activity" and (
            data["stage"] not in {"implementation", "testing", "review", "integration"}
            or data["status"] not in {"started", "completed", "blocked", "failed"}
        ):
            raise ValueError("Invalid activity stage/status")
        if event["kind"] == "heartbeat" and data["status"] not in {
            "active",
            "stopped",
            "failed",
        }:
            raise ValueError("Invalid collector status")


class DevelopmentMetrics:
    def __init__(self, root: Path) -> None:
        self.path = root.resolve() / FILENAME

    def append(self, event: dict[str, Any]) -> bool:
        validate_event(event)
        event = {
            **event,
            "at": datetime.fromisoformat(event["at"].replace("Z", "+00:00"))
            .astimezone(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
        }
        payload = json.dumps(event, sort_keys=True, separators=(",", ":"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, "
                "id TEXT UNIQUE NOT NULL, at TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            existing = db.execute(
                "SELECT payload FROM events WHERE id=?", (event["id"],)
            ).fetchone()
            if existing:
                if existing[0] != payload:
                    raise ValueError("Event ID reused with different content")
                return False
            db.execute(
                "INSERT INTO events(id,at,payload) VALUES(?,?,?)",
                (event["id"], event["at"], payload),
            )
        return True

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": 1,
                "events": [],
                "truncated": False,
                "availability": "unavailable",
            }
        with sqlite3.connect(
            self.path.as_uri() + "?mode=ro", uri=True, timeout=2
        ) as db:
            cursor = db.execute(
                "SELECT payload FROM events ORDER BY at DESC,seq DESC LIMIT ?",
                (LIMIT + 1,),
            )
            rows: list[tuple[str]] = []
            size = 0
            truncated = False
            for row in cursor:
                size += len(row[0].encode("utf-8"))
                if len(rows) == LIMIT or size > 16 * 1024 * 1024:
                    truncated = True
                    break
                rows.append(row)
        events = [json.loads(row[0]) for row in reversed(rows)]
        return {
            "schema_version": 1,
            "events": events,
            "truncated": truncated,
            "availability": "available",
        }


def collect_tasks(
    repository: Path, sources: list[tuple[str, str]]
) -> list[dict[str, Any]]:
    """Snapshot explicit sources; checkbox means implemented, never QA verified."""
    result = []
    root = repository.resolve()
    for feature, relative in sources:
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Task source must be inside repository")
        tasks = [
            {
                "task": match[1],
                "title": match[2][:1000],
                "checked": match[0].lower() == "x",
            }
            for match in re.findall(
                r"^- \[([ xX])\] (T\d+)\b\s*(.*)$",
                path.read_text(encoding="utf-8"),
                re.MULTILINE,
            )
        ]
        result.append({"feature": feature, "tasks": tasks})
    return result
