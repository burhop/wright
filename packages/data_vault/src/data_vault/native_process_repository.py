"""Workspace-scoped native persistence with explicit SQLite write transactions."""

from __future__ import annotations

import base64
import hashlib
import re
import sqlite3
from datetime import UTC, datetime
from typing import Any

from core.canonical_json import canonical_json_bytes, strict_json_loads
from core.logging import get_logger
from core.native_process import NativeDocument, validate_presentation
from core.native_tracing import traced_native

from .state_store import connect_state_db

logger = get_logger(__name__)
MAX_ENVELOPE_BYTES = 1100 * 1024


class NativeRepositoryError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def decode_envelope(raw: bytes) -> dict[str, Any]:
    return strict_json_loads(raw, max_bytes=MAX_ENVELOPE_BYTES)


class NativeProcessRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @staticmethod
    def _replay(
        connection: sqlite3.Connection, workspace_id: str, request_id: str, digest: str
    ) -> dict[str, Any] | None:
        row = connection.execute(
            "SELECT fingerprint,result FROM native_process_requests WHERE workspace_id=? AND request_id=?",
            (workspace_id, request_id),
        ).fetchone()
        if row is None:
            return None
        if row["fingerprint"] != digest:
            raise NativeRepositoryError(
                "NATIVE_REQUEST_REUSED",
                "Request identity was already used with different content.",
            )
        return decode_envelope(row["result"])

    @staticmethod
    def _remember(
        connection: sqlite3.Connection,
        workspace_id: str,
        request_id: str,
        digest: str,
        result: bytes,
        timestamp: str,
        trace_id: str,
    ) -> None:
        connection.execute(
            """INSERT INTO native_process_requests
            (workspace_id,request_id,fingerprint,result,created_at,trace_id)
            VALUES (?,?,?,?,?,?)""",
            (workspace_id, request_id, digest, result, timestamp, trace_id),
        )

    @traced_native("native.document.save")
    def save(
        self,
        workspace_id: str,
        document: NativeDocument,
        presentation: object,
        *,
        request_id: str,
        expected_token: str | None,
        trace_id: str,
    ) -> dict[str, Any]:
        """None token means create; updates compare-and-swap the full envelope.

        The idempotency result and prior/current envelope commit together. An
        exact retry returns its original result even if another save followed.
        """
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id):
            raise NativeRepositoryError(
                "NATIVE_INVALID", "Request identity is invalid."
            )
        if expected_token is not None and not re.fullmatch(
            r"[0-9a-f]{64}", expected_token
        ):
            raise NativeRepositoryError("NATIVE_INVALID", "Expected token is invalid.")
        positions = validate_presentation(document, presentation)
        semantics = document.as_dict()
        digest = fingerprint(
            {
                "operation": "create" if expected_token is None else "update",
                "workspace_id": workspace_id,
                "process_id": document.process_id,
                "expected_token": expected_token,
                "definition": semantics,
                "presentation": positions,
            }
        )
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            replay = self._replay(connection, workspace_id, request_id, digest)
            if replay is not None:
                return replay
            current = connection.execute(
                "SELECT revision,token,envelope FROM native_process_documents WHERE workspace_id=? AND process_id=?",
                (workspace_id, document.process_id),
            ).fetchone()
            if current is None and expected_token is not None:
                raise NativeRepositoryError(
                    "NATIVE_NOT_FOUND",
                    "Native process was not found in this workspace.",
                )
            if current is not None and (
                expected_token is None or expected_token != current["token"]
            ):
                raise NativeRepositoryError(
                    "NATIVE_CONFLICT",
                    "The saved process has changed; reopen it before saving.",
                )
            timestamp = utc_now()
            revision = current["revision"] + 1 if current else 1
            envelope = {
                "definition": semantics,
                "presentation": positions,
                "revision": revision,
                "semantic_digest": document.semantic_digest,
                "updated_at": timestamp,
            }
            envelope["token"] = fingerprint({"workspace_id": workspace_id, **envelope})
            encoded = canonical_json_bytes(envelope)
            if len(encoded) > MAX_ENVELOPE_BYTES:
                raise NativeRepositoryError(
                    "NATIVE_LIMIT", "Saved envelope exceeds its size limit."
                )
            if current is None:
                connection.execute(
                    """INSERT INTO native_process_documents
                    (workspace_id,process_id,revision,token,semantic_digest,title,envelope,updated_at,trace_id)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        workspace_id,
                        document.process_id,
                        revision,
                        envelope["token"],
                        document.semantic_digest,
                        semantics["title"],
                        encoded,
                        timestamp,
                        trace_id,
                    ),
                )
            else:
                cursor = connection.execute(
                    """UPDATE native_process_documents SET revision=?,token=?,semantic_digest=?,title=?,
                    previous_envelope=envelope,envelope=?,updated_at=?,trace_id=?
                    WHERE workspace_id=? AND process_id=? AND token=?""",
                    (
                        revision,
                        envelope["token"],
                        document.semantic_digest,
                        semantics["title"],
                        encoded,
                        timestamp,
                        trace_id,
                        workspace_id,
                        document.process_id,
                        expected_token,
                    ),
                )
                if cursor.rowcount != 1:
                    raise NativeRepositoryError(
                        "NATIVE_CONFLICT", "The saved process has changed."
                    )
            self._remember(
                connection,
                workspace_id,
                request_id,
                digest,
                encoded,
                timestamp,
                trace_id,
            )
        logger.info(
            "native_process_saved",
            workspace_id=workspace_id,
            process_id=document.process_id,
            revision=revision,
            semantic_digest=document.semantic_digest,
            trace_id=trace_id,
        )
        return envelope

    @traced_native("native.document.read")
    def get(
        self, workspace_id: str, process_id: str, *, previous: bool = False
    ) -> dict[str, Any]:
        column = "previous_envelope" if previous else "envelope"
        with connect_state_db(self.db_path, read_only=True) as connection:
            row = connection.execute(
                f"SELECT {column} FROM native_process_documents WHERE workspace_id=? AND process_id=?",
                (workspace_id, process_id),
            ).fetchone()
        if row is None or row[0] is None:
            raise NativeRepositoryError(
                "NATIVE_NOT_FOUND", "Native process was not found in this workspace."
            )
        return decode_envelope(row[0])

    @traced_native("native.document.list")
    def list(
        self, workspace_id: str, *, limit: int = 25, cursor: str | None = None
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise NativeRepositoryError(
                "NATIVE_INVALID", "Page size must be between 1 and 100."
            )
        after = ""
        if cursor:
            try:
                after = base64.b64decode(
                    cursor.encode("ascii"), altchars=b"-_", validate=True
                ).decode("ascii")
                if not re.fullmatch(r"[a-z][a-z0-9-]{2,79}", after):
                    raise ValueError("Invalid cursor")
            except (ValueError, UnicodeError) as exc:
                raise NativeRepositoryError(
                    "NATIVE_INVALID", "Page cursor is invalid."
                ) from exc
        with connect_state_db(self.db_path, read_only=True) as connection:
            rows = connection.execute(
                """SELECT process_id AS id,title,revision,token,updated_at FROM native_process_documents
                WHERE workspace_id=? AND process_id>? ORDER BY process_id LIMIT ?""",
                (workspace_id, after, limit + 1),
            ).fetchall()
        page = [dict(row) for row in rows[:limit]]
        next_cursor = (
            base64.urlsafe_b64encode(page[-1]["id"].encode("ascii")).decode("ascii")
            if len(rows) > limit
            else None
        )
        return {"documents": page, "next_cursor": next_cursor}
