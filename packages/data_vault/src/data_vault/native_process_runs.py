"""Immutable native snapshots and atomic run/step/event transitions."""

from __future__ import annotations

import base64
import re
import sqlite3
import uuid
from typing import Any

from core.canonical_json import canonical_json_bytes, strict_json_loads
from core.native_process import topological_order
from core.native_runtime_json import runtime_json_bytes, runtime_json_loads
from core.tracing import traced

from .native_process_repository import (
    NativeProcessRepository,
    NativeRepositoryError,
    decode_envelope,
    fingerprint,
    utc_now,
)
from .state_store import connect_state_db

TERMINAL_STATES = frozenset(
    {"succeeded", "failed", "cancelled", "timed_out", "interrupted"}
)
MAX_VALUE_BYTES = 1024 * 1024


def _decode(raw: bytes | None):
    return (
        runtime_json_loads(raw, max_bytes=MAX_VALUE_BYTES) if raw is not None else None
    )


def _encode(value: Any) -> bytes:
    try:
        return runtime_json_bytes(value, max_bytes=MAX_VALUE_BYTES)
    except (ValueError, UnicodeError) as error:
        raise NativeRepositoryError(
            "NATIVE_LIMIT", "Recorded native values must be valid bounded JSON."
        ) from error


class NativeRunRepository(NativeProcessRepository):
    @staticmethod
    def _run_fingerprint(
        workspace_id: str,
        process_id: str,
        *,
        session_id: str,
        expected_token: str,
        request_id: str,
        bindings: dict[str, Any],
        timeout_seconds: int,
        derived_from_run_id: str | None,
        actor: str,
        trace_id: str,
    ) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", request_id):
            raise NativeRepositoryError(
                "NATIVE_INVALID", "Request identity is invalid."
            )
        if not re.fullmatch(r"[0-9a-f]{64}", expected_token):
            raise NativeRepositoryError("NATIVE_INVALID", "Expected token is invalid.")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 300:
            raise NativeRepositoryError(
                "NATIVE_INVALID", "Run deadline must be between 1 and 300 seconds."
            )
        return fingerprint(
            {
                "operation": "run",
                "workspace_id": workspace_id,
                "process_id": process_id,
                "expected_token": expected_token,
                "bindings": bindings,
                "timeout_seconds": timeout_seconds,
                "derived_from_run_id": derived_from_run_id,
                "session_id": session_id,
                "actor": actor,
            }
        )

    def replay_run(
        self, workspace_id: str, process_id: str, **request
    ) -> dict[str, Any] | None:
        """Look up exact submission before current-definition preflight.

        create_run repeats this lookup inside its write transaction. A service
        may safely return the original submission after later saves or startup.
        """
        digest = self._run_fingerprint(workspace_id, process_id, **request)
        with connect_state_db(self.db_path, read_only=True) as connection:
            return self._replay(connection, workspace_id, request["request_id"], digest)

    def indexed_artifact_keys(self, workspace_id: str) -> frozenset[str]:
        with connect_state_db(self.db_path, read_only=True) as connection:
            return frozenset(
                row[0]
                for row in connection.execute(
                    "SELECT storage_key FROM native_process_artifacts WHERE workspace_id=?",
                    (workspace_id,),
                )
            )

    def artifact_scopes(self) -> list[dict[str, str]]:
        with connect_state_db(self.db_path, read_only=True) as connection:
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT DISTINCT workspace_id,session_id FROM native_process_runs ORDER BY workspace_id,session_id"
                )
            ]

    def record_cleanup_residue(
        self, workspace_id: str, run_id: str, artifact_id: str
    ) -> None:
        """Retain a safe diagnostic if bounded cleanup cannot remove a leaf."""
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._row(connection, workspace_id, run_id)
            self._event(
                connection,
                row,
                "artifact.cleanup_residue",
                {
                    "artifact_id": artifact_id,
                    "message": "An unindexed generated artifact could not be removed; owner startup reconciliation will retry.",
                },
                utc_now(),
            )

    @staticmethod
    def _row(connection: sqlite3.Connection, workspace_id: str, run_id: str):
        row = connection.execute(
            "SELECT * FROM native_process_runs WHERE workspace_id=? AND run_id=?",
            (workspace_id, run_id),
        ).fetchone()
        if row is None:
            raise NativeRepositoryError(
                "NATIVE_NOT_FOUND", "Native run was not found in this workspace."
            )
        return row

    @staticmethod
    def _summary(row) -> dict[str, Any]:
        fields = (
            "run_id",
            "process_id",
            "state",
            "semantic_digest",
            "created_at",
            "started_at",
            "completed_at",
            "derived_from_run_id",
            "trace_id",
        )
        return {**{key: row[key] for key in fields}, "reason": _decode(row["reason"])}

    @staticmethod
    def _event(connection, row, kind: str, payload: dict[str, Any], timestamp: str):
        raw = _encode(payload)
        if len(raw) > 64 * 1024:
            raise NativeRepositoryError("NATIVE_LIMIT", "Run event exceeds 64 KiB.")
        sequence = connection.execute(
            "SELECT COALESCE(MAX(sequence),0)+1 FROM native_process_events WHERE workspace_id=? AND run_id=?",
            (row["workspace_id"], row["run_id"]),
        ).fetchone()[0]
        connection.execute(
            """INSERT INTO native_process_events
            (workspace_id,run_id,sequence,occurred_at,kind,payload,trace_id) VALUES (?,?,?,?,?,?,?)""",
            (
                row["workspace_id"],
                row["run_id"],
                sequence,
                timestamp,
                kind,
                raw,
                row["trace_id"],
            ),
        )

    @traced("native.run.create")
    def create_run(
        self,
        workspace_id: str,
        process_id: str,
        *,
        session_id: str,
        expected_token: str,
        request_id: str,
        bindings: dict[str, Any],
        timeout_seconds: int,
        derived_from_run_id: str | None,
        actor: str,
        trace_id: str,
    ) -> dict[str, Any]:
        digest = self._run_fingerprint(
            workspace_id,
            process_id,
            session_id=session_id,
            expected_token=expected_token,
            request_id=request_id,
            bindings=bindings,
            timeout_seconds=timeout_seconds,
            derived_from_run_id=derived_from_run_id,
            actor=actor,
            trace_id=trace_id,
        )
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            replay = self._replay(connection, workspace_id, request_id, digest)
            if replay is not None:
                return replay
            saved = connection.execute(
                "SELECT envelope,token FROM native_process_documents WHERE workspace_id=? AND process_id=?",
                (workspace_id, process_id),
            ).fetchone()
            if saved is None:
                raise NativeRepositoryError(
                    "NATIVE_NOT_FOUND",
                    "Native process was not found in this workspace.",
                )
            if saved["token"] != expected_token:
                raise NativeRepositoryError(
                    "NATIVE_CONFLICT",
                    "The saved process changed before run submission.",
                )
            if derived_from_run_id is not None:
                previous = self._row(connection, workspace_id, derived_from_run_id)
                if previous["process_id"] != process_id:
                    raise NativeRepositoryError(
                        "NATIVE_INVALID",
                        "The prior run belongs to a different process.",
                    )
            envelope = decode_envelope(saved["envelope"])
            snapshot = {
                key: envelope[key]
                for key in ("definition", "revision", "token", "semantic_digest")
            }
            run_id, timestamp = str(uuid.uuid4()), utc_now()
            connection.execute(
                """INSERT INTO native_process_runs
                (workspace_id,run_id,process_id,session_id,snapshot,bindings,semantic_digest,derived_from_run_id,
                 actor,trace_id,state,created_at,timeout_seconds) VALUES (?,?,?,?,?,?,?,?,?,?,'queued',?,?)""",
                (
                    workspace_id,
                    run_id,
                    process_id,
                    session_id,
                    canonical_json_bytes(snapshot),
                    _encode(bindings),
                    envelope["semantic_digest"],
                    derived_from_run_id,
                    actor,
                    trace_id,
                    timestamp,
                    timeout_seconds,
                ),
            )
            steps = {step["id"]: step for step in snapshot["definition"]["steps"]}
            connection.executemany(
                """INSERT INTO native_process_steps
                (workspace_id,run_id,step_id,ordinal,operation,state) VALUES (?,?,?,?,?,'pending')""",
                [
                    (
                        workspace_id,
                        run_id,
                        identity,
                        ordinal,
                        steps[identity]["operation"],
                    )
                    for ordinal, identity in enumerate(
                        topological_order(snapshot["definition"])
                    )
                ],
            )
            result = {
                "run_id": run_id,
                "state": "queued",
                "semantic_digest": envelope["semantic_digest"],
            }
            row = self._row(connection, workspace_id, run_id)
            self._event(connection, row, "run.queued", result, timestamp)
            self._remember(
                connection,
                workspace_id,
                request_id,
                digest,
                canonical_json_bytes(result),
                timestamp,
                trace_id,
            )
        return result

    @traced("native.run.inspect")
    def inspect(self, workspace_id: str, run_id: str) -> dict[str, Any]:
        with connect_state_db(self.db_path, read_only=True) as connection:
            connection.execute("BEGIN")
            row = self._row(connection, workspace_id, run_id)
            steps = []
            for step in connection.execute(
                "SELECT * FROM native_process_steps WHERE workspace_id=? AND run_id=? ORDER BY ordinal",
                (workspace_id, run_id),
            ):
                steps.append(
                    {
                        **{
                            key: step[key]
                            for key in (
                                "step_id",
                                "operation",
                                "state",
                                "started_at",
                                "completed_at",
                            )
                        },
                        **{
                            key: _decode(step[key])
                            for key in ("inputs", "outputs", "reason")
                        },
                    }
                )
            artifacts = [
                {
                    **{
                        key: item[key]
                        for key in (
                            "artifact_id",
                            "step_id",
                            "port_id",
                            "filename",
                            "content_digest",
                            "size",
                            "media_type",
                        )
                    },
                    "provenance": _decode(item["provenance"]),
                }
                for item in connection.execute(
                    "SELECT * FROM native_process_artifacts WHERE workspace_id=? AND run_id=? ORDER BY created_at,artifact_id",
                    (workspace_id, run_id),
                )
            ]
            last_sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence),0) FROM native_process_events WHERE workspace_id=? AND run_id=?",
                (workspace_id, run_id),
            ).fetchone()[0]
            return {
                **self._summary(row),
                "snapshot": decode_envelope(row["snapshot"]),
                "bindings": _decode(row["bindings"]),
                "actor": row["actor"],
                "timeout_seconds": row["timeout_seconds"],
                "steps": steps,
                "artifacts": artifacts,
                "last_sequence": last_sequence,
            }

    def summary(self, workspace_id: str, run_id: str) -> dict[str, Any]:
        with connect_state_db(self.db_path, read_only=True) as connection:
            return self._summary(self._row(connection, workspace_id, run_id))

    @traced("native.run.start")
    def start(self, workspace_id: str, run_id: str) -> bool:
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._row(connection, workspace_id, run_id)
            if row["state"] != "queued":
                return False
            timestamp = utc_now()
            connection.execute(
                "UPDATE native_process_runs SET state='running',started_at=? WHERE workspace_id=? AND run_id=? AND state='queued'",
                (timestamp, workspace_id, run_id),
            )
            self._event(connection, row, "run.started", {}, timestamp)
        return True

    @staticmethod
    def _values_budget(connection, workspace_id: str, run_id: str, added: int):
        size = connection.execute(
            "SELECT COALESCE(SUM(COALESCE(length(inputs),0)+COALESCE(length(outputs),0)),0) FROM native_process_steps WHERE workspace_id=? AND run_id=?",
            (workspace_id, run_id),
        ).fetchone()[0]
        if size + added > MAX_VALUE_BYTES:
            raise NativeRepositoryError(
                "NATIVE_LIMIT", "Run recorded values exceed 1 MiB."
            )

    @traced("native.step.start")
    def start_step(
        self, workspace_id: str, run_id: str, step_id: str, inputs: dict[str, Any]
    ) -> bool:
        encoded = _encode(inputs)
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._row(connection, workspace_id, run_id)
            if row["state"] != "running":
                return False
            self._values_budget(connection, workspace_id, run_id, len(encoded))
            timestamp = utc_now()
            changed = connection.execute(
                """UPDATE native_process_steps SET state='running',started_at=?,inputs=?
                WHERE workspace_id=? AND run_id=? AND step_id=? AND state='pending'""",
                (timestamp, encoded, workspace_id, run_id, step_id),
            ).rowcount
            if changed:
                self._event(
                    connection, row, "step.started", {"step_id": step_id}, timestamp
                )
            return changed == 1

    @traced("native.step.complete")
    def complete_step(
        self,
        workspace_id: str,
        run_id: str,
        step_id: str,
        outputs: dict[str, Any],
        *,
        artifacts: tuple[dict[str, Any], ...] = (),
    ) -> bool:
        encoded = _encode(outputs)
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._row(connection, workspace_id, run_id)
            step = connection.execute(
                "SELECT state FROM native_process_steps WHERE workspace_id=? AND run_id=? AND step_id=?",
                (workspace_id, run_id, step_id),
            ).fetchone()
            if row["state"] != "running" or step is None or step["state"] != "running":
                return False
            self._values_budget(connection, workspace_id, run_id, len(encoded))
            timestamp = utc_now()
            for artifact in artifacts:
                connection.execute(
                    """INSERT INTO native_process_artifacts
                    (workspace_id,run_id,artifact_id,step_id,port_id,filename,storage_key,content_digest,size,media_type,provenance,created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        workspace_id,
                        run_id,
                        artifact["artifact_id"],
                        step_id,
                        artifact["port_id"],
                        artifact["filename"],
                        artifact["storage_key"],
                        artifact["content_digest"],
                        artifact["size"],
                        artifact["media_type"],
                        _encode(artifact["provenance"]),
                        timestamp,
                    ),
                )
                self._event(
                    connection,
                    row,
                    "artifact.indexed",
                    {
                        "step_id": step_id,
                        "artifact_id": artifact["artifact_id"],
                        "content_digest": artifact["content_digest"],
                    },
                    timestamp,
                )
            connection.execute(
                "UPDATE native_process_steps SET state='succeeded',completed_at=?,outputs=? WHERE workspace_id=? AND run_id=? AND step_id=? AND state='running'",
                (timestamp, encoded, workspace_id, run_id, step_id),
            )
            self._event(
                connection, row, "step.succeeded", {"step_id": step_id}, timestamp
            )
        return True

    @traced("native.run.finish")
    def finish(
        self,
        workspace_id: str,
        run_id: str,
        state: str,
        *,
        reason: dict[str, Any] | None = None,
        failed_step_id: str | None = None,
    ) -> dict[str, Any]:
        if state not in TERMINAL_STATES:
            raise NativeRepositoryError(
                "NATIVE_INVALID", "Requested run terminal state is invalid."
            )
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = self._row(connection, workspace_id, run_id)
            if row["state"] in TERMINAL_STATES:
                return self._summary(row)
            remaining = connection.execute(
                "SELECT step_id,state FROM native_process_steps WHERE workspace_id=? AND run_id=? AND state!='succeeded'",
                (workspace_id, run_id),
            ).fetchall()
            if state == "succeeded" and (row["state"] != "running" or remaining):
                raise NativeRepositoryError(
                    "NATIVE_CONFLICT", "Run cannot succeed before every step succeeds."
                )
            timestamp = utc_now()
            dependents = set()
            if failed_step_id:
                definition = decode_envelope(row["snapshot"])["definition"]
                owners = {port["id"]: port["step_id"] for port in definition["ports"]}
                frontier = {failed_step_id}
                while frontier:
                    targets = {
                        owners[edge["target_port_id"]]
                        for edge in definition["connections"]
                        if owners[edge["source_port_id"]] in frontier
                    }
                    frontier = targets - dependents
                    dependents.update(targets)
            for step in remaining:
                identity = step["step_id"]
                disposition = (
                    "failed"
                    if identity == failed_step_id
                    else "blocked"
                    if identity in dependents
                    else "cancelled"
                )
                step_reason = reason
                if disposition in {"blocked", "cancelled"} and failed_step_id:
                    step_reason = {
                        "code": "DEPENDENCY_FAILED"
                        if disposition == "blocked"
                        else "run_stopped_after_failure",
                        "message": "A preceding process step failed.",
                        "recovery": "Correct the failure and create a linked run.",
                        "step_id": failed_step_id,
                        "port_id": None,
                    }
                connection.execute(
                    "UPDATE native_process_steps SET state=?,completed_at=?,reason=? WHERE workspace_id=? AND run_id=? AND step_id=?",
                    (
                        disposition,
                        timestamp,
                        _encode(step_reason) if step_reason else None,
                        workspace_id,
                        run_id,
                        identity,
                    ),
                )
                self._event(
                    connection,
                    row,
                    "step." + disposition,
                    {"step_id": identity, "reason": step_reason},
                    timestamp,
                )
            connection.execute(
                "UPDATE native_process_runs SET state=?,completed_at=?,reason=? WHERE workspace_id=? AND run_id=? AND state IN ('queued','running')",
                (
                    state,
                    timestamp,
                    _encode(reason) if reason else None,
                    workspace_id,
                    run_id,
                ),
            )
            self._event(connection, row, "run." + state, {"reason": reason}, timestamp)
            return self._summary(self._row(connection, workspace_id, run_id))

    def interrupt_abandoned(self) -> int:
        """Only the OS-lock-owning coordinator may call this at startup."""
        with connect_state_db(self.db_path, read_only=True) as connection:
            rows = connection.execute(
                "SELECT workspace_id,run_id FROM native_process_runs WHERE state IN ('queued','running')"
            ).fetchall()
        for row in rows:
            self.finish(
                row["workspace_id"],
                row["run_id"],
                "interrupted",
                reason={
                    "code": "OWNER_INTERRUPTED",
                    "message": "The runtime owner stopped before completion.",
                    "recovery": "Inspect retained evidence and create a linked run.",
                    "step_id": None,
                    "port_id": None,
                },
            )
        return len(rows)

    def events(
        self,
        workspace_id: str,
        run_id: str,
        *,
        after_sequence: int = 0,
        limit: int = 200,
    ) -> dict[str, Any]:
        if (
            type(after_sequence) is not int
            or after_sequence < 0
            or type(limit) is not int
            or not 1 <= limit <= 200
        ):
            raise NativeRepositoryError(
                "NATIVE_INVALID", "Event cursor or page size is invalid."
            )
        with connect_state_db(self.db_path, read_only=True) as connection:
            self._row(connection, workspace_id, run_id)
            rows = connection.execute(
                "SELECT * FROM native_process_events WHERE workspace_id=? AND run_id=? AND sequence>? ORDER BY sequence LIMIT ?",
                (workspace_id, run_id, after_sequence, limit),
            ).fetchall()
        events = [
            {
                "sequence": row["sequence"],
                "occurred_at": row["occurred_at"],
                "kind": row["kind"],
                "payload": _decode(row["payload"]),
                "trace_id": row["trace_id"],
            }
            for row in rows
        ]
        return {
            "events": events,
            "next_sequence": events[-1]["sequence"] if events else after_sequence,
        }

    def history(
        self,
        workspace_id: str,
        process_id: str,
        *,
        limit: int = 25,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise NativeRepositoryError("NATIVE_INVALID", "Run page size is invalid.")
        self.get(workspace_id, process_id)
        timestamp, identity = "9999", ""
        if cursor:
            try:
                position = strict_json_loads(
                    base64.b64decode(cursor, altchars=b"-_", validate=True),
                    max_bytes=256,
                )
                timestamp, identity = position["created_at"], position["run_id"]
                if not isinstance(timestamp, str) or not isinstance(identity, str):
                    raise ValueError("Invalid cursor")
            except (ValueError, KeyError, TypeError) as error:
                raise NativeRepositoryError(
                    "NATIVE_INVALID", "Run cursor is invalid."
                ) from error
        with connect_state_db(self.db_path, read_only=True) as connection:
            rows = connection.execute(
                """SELECT * FROM native_process_runs WHERE workspace_id=? AND process_id=?
                AND (created_at<? OR (created_at=? AND run_id>?)) ORDER BY created_at DESC,run_id LIMIT ?""",
                (workspace_id, process_id, timestamp, timestamp, identity, limit + 1),
            ).fetchall()
        summaries = [self._summary(row) for row in rows[:limit]]
        next_cursor = (
            base64.urlsafe_b64encode(
                canonical_json_bytes(
                    {key: summaries[-1][key] for key in ("created_at", "run_id")}
                )
            ).decode("ascii")
            if len(rows) > limit
            else None
        )
        return {"runs": summaries, "next_cursor": next_cursor}

    def artifact(
        self, workspace_id: str, run_id: str, artifact_id: str
    ) -> dict[str, Any]:
        with connect_state_db(self.db_path, read_only=True) as connection:
            row = connection.execute(
                "SELECT * FROM native_process_artifacts WHERE workspace_id=? AND run_id=? AND artifact_id=?",
                (workspace_id, run_id, artifact_id),
            ).fetchone()
        if row is None:
            raise NativeRepositoryError(
                "NATIVE_NOT_FOUND", "Indexed artifact was not found in this run."
            )
        return {**dict(row), "provenance": _decode(row["provenance"])}
