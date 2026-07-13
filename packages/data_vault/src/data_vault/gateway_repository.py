from __future__ import annotations

import json
import time
import uuid
from collections.abc import Mapping
from typing import Any

from core.redaction import redact_mapping  # type: ignore[import-untyped]

from .state_store import connect_state_db


class GatewayBindingError(RuntimeError):
    """Raised when gateway identity does not map to one explicit workspace."""


class GatewayRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def resolve_binding(
        self,
        *,
        session_id: str,
        principal_id: str,
        workspace_id: str,
    ) -> dict[str, Any]:
        values = {
            "session_id": session_id.strip(),
            "principal_id": principal_id.strip(),
            "workspace_id": workspace_id.strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise GatewayBindingError(
                f"Explicit gateway binding requires {', '.join(missing)}"
            )
        with connect_state_db(self.db_path) as connection:
            row = connection.execute(
                """SELECT ew.workspace_id, ew.local_path, was.session_id
                FROM workspace_agent_sessions was
                JOIN engineering_workspaces ew ON ew.workspace_id = was.workspace_id
                WHERE was.session_id = ? AND was.workspace_id = ?
                  AND was.is_archived = 0""",
                (values["session_id"], values["workspace_id"]),
            ).fetchone()
        if row is None:
            raise GatewayBindingError(
                "Gateway session is not bound to the requested workspace"
            )
        return {
            "session_id": values["session_id"],
            "principal_id": values["principal_id"],
            "workspace_id": row["workspace_id"],
            "workspace_path": row["local_path"],
        }

    def enabled_server_ids(self, workspace_id: str) -> set[str] | None:
        with connect_state_db(self.db_path) as connection:
            row = connection.execute(
                "SELECT enabled_tools FROM engineering_workspaces WHERE workspace_id = ?",
                (workspace_id,),
            ).fetchone()
        if row is None or row["enabled_tools"] is None:
            return None
        try:
            value = json.loads(row["enabled_tools"])
        except (TypeError, json.JSONDecodeError):
            return None
        return {str(item) for item in value} if isinstance(value, list) else None

    def record_audit(self, event: Mapping[str, Any]) -> str:
        required = (
            "correlation_id",
            "session_id",
            "principal_id",
            "workspace_id",
            "operation",
            "reason_code",
            "outcome",
        )
        missing = [name for name in required if not str(event.get(name) or "").strip()]
        if missing:
            raise ValueError(f"Gateway audit event requires {', '.join(missing)}")
        event_id = str(event.get("event_id") or uuid.uuid4())
        metadata = event.get("metadata")
        safe_metadata = (
            redact_mapping(metadata) if isinstance(metadata, Mapping) else {}
        )
        with connect_state_db(self.db_path) as connection:
            connection.execute(
                """INSERT INTO gateway_audit_events (
                    event_id, occurred_at, correlation_id, request_id, session_id,
                    principal_id, workspace_id, operation, server_id, target_name,
                    allowed, reason_code, outcome, duration_ms, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_id,
                    int(event.get("occurred_at") or time.time_ns()),
                    str(event["correlation_id"]),
                    _optional(event.get("request_id")),
                    str(event["session_id"]),
                    str(event["principal_id"]),
                    str(event["workspace_id"]),
                    str(event["operation"]),
                    _optional(event.get("server_id")),
                    _optional(event.get("target_name")),
                    int(bool(event.get("allowed"))),
                    str(event["reason_code"]),
                    str(event["outcome"]),
                    max(0, int(event.get("duration_ms") or 0)),
                    json.dumps(safe_metadata, sort_keys=True),
                ),
            )
        return event_id

    def list_audit(self, session_id: str) -> list[dict[str, Any]]:
        with connect_state_db(self.db_path) as connection:
            rows = connection.execute(
                """SELECT * FROM gateway_audit_events
                WHERE session_id = ? ORDER BY occurred_at, rowid""",
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]


def _optional(value: Any) -> str | None:
    return str(value) if value is not None else None
