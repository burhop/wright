from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import structlog

from .canonical_catalog import _validate_catalog_document
from .catalog_reconcile import reconcile_engineering_catalog_document
from .catalog_signing import (
    CatalogTrustRoot,
    CatalogVerificationError,
    canonical_json,
    verify_catalog_envelope,
)
from .catalog_snapshots import (
    bootstrap_bundled_snapshot,
    get_catalog_state,
    get_snapshot,
    prune_snapshots,
    store_verified_snapshot,
)

logger = structlog.get_logger(__name__)
PREVIEW_TTL = timedelta(minutes=30)


class CatalogUpdateError(RuntimeError):
    def __init__(
        self, code: str, message: str, recovery: str, *, status_code: int = 409
    ) -> None:
        self.code = code
        self.recovery = recovery
        self.status_code = status_code
        super().__init__(message)


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _identity_map(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["id"]: entry for entry in document["servers"]}


def catalog_diff(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    old = _identity_map(_validate_catalog_document(before))
    new = _identity_map(_validate_catalog_document(after))
    added = [
        {
            "id": identity,
            "after": new[identity],
            "provenance": new[identity].get("source_records", []),
        }
        for identity in sorted(new.keys() - old.keys())
    ]
    removed = [
        {
            "id": identity,
            "before": old[identity],
            "provenance": old[identity].get("source_records", []),
        }
        for identity in sorted(old.keys() - new.keys())
    ]
    changed: list[dict[str, Any]] = []
    for identity in sorted(old.keys() & new.keys()):
        fields = []
        for field in sorted(set(old[identity]) | set(new[identity])):
            before_value = old[identity].get(field)
            after_value = new[identity].get(field)
            if before_value == after_value:
                continue
            fields.append(
                {
                    "field": field,
                    "before": before_value,
                    "after": after_value,
                    "provenance": new[identity].get("source_records", []),
                }
            )
        if fields:
            changed.append({"id": identity, "fields": fields})
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "total_before": len(old),
            "total_after": len(new),
        },
    }


def _risk_summary(diff: dict[str, Any]) -> dict[str, Any]:
    changed_records = [item["after"] for item in diff["added"]]
    for item in diff["changed"]:
        fields = {change["field"]: change["after"] for change in item["fields"]}
        changed_records.append(fields)
    return {
        "new_executable_entries": sum(
            1 for record in changed_records if record.get("transport") == "stdio"
        ),
        "new_remote_entries": sum(
            1
            for record in changed_records
            if record.get("transport") in {"streamable_http", "sse", "webmcp"}
        ),
        "high_or_safety_critical": sum(
            1
            for record in changed_records
            if record.get("risk_level") in {"high", "safety-critical"}
        ),
        "note": "Catalog activation changes metadata only; it cannot install or enable.",
    }


def _preview_material(
    *,
    active_snapshot_id: str,
    candidate_snapshot_id: str,
    diff: dict[str, Any],
    actor: str,
    created_at: datetime,
    expires_at: datetime,
) -> dict[str, Any]:
    return {
        "active_snapshot_id": active_snapshot_id,
        "candidate_snapshot_id": candidate_snapshot_id,
        "diff": diff,
        "actor": actor,
        "created_at": created_at.isoformat(),
        "expires_at": expires_at.isoformat(),
    }


def _preview_response(row: sqlite3.Row, snapshot=None) -> dict[str, Any]:
    diff = json.loads(row["diff_json"])
    return {
        "preview_id": row["preview_id"],
        "active_snapshot_id": row["active_snapshot_id"],
        "candidate_snapshot_id": row["candidate_snapshot_id"],
        "candidate": {
            "channel": snapshot.channel,
            "sequence": snapshot.sequence,
            "schema_version": snapshot.schema_version,
            "payload_sha256": snapshot.payload_sha256,
            "signer_key_id": snapshot.signer_key_id,
            "expires_at": snapshot.expires_at.isoformat(),
        }
        if snapshot
        else None,
        "diff": diff,
        "risk_summary": _risk_summary(diff),
        "actor": row["actor"],
        "created_at": datetime.fromtimestamp(row["created_at"], UTC).isoformat(),
        "expires_at": datetime.fromtimestamp(row["expires_at"], UTC).isoformat(),
        "state": row["state"],
        "preview_digest": row["preview_digest"],
    }


def preview_catalog_update(
    database_path: str | Path,
    envelope: dict[str, Any] | bytes,
    *,
    trust_root: CatalogTrustRoot,
    actor: str,
    now: datetime,
    trace_id: str,
) -> dict[str, Any]:
    bootstrap_bundled_snapshot(database_path)
    state = get_catalog_state(database_path)
    logger.info(
        "catalog_update_verify_started",
        trace_id=trace_id,
        channel=trust_root.channel,
        active_sequence=state["active_sequence"],
    )
    try:
        snapshot = verify_catalog_envelope(
            envelope,
            trust_root=trust_root,
            now=now,
            minimum_sequence=state["active_sequence"],
        )
    except CatalogVerificationError as error:
        logger.warning(
            "catalog_update_verify_rejected",
            trace_id=trace_id,
            code=error.code,
            channel=trust_root.channel,
        )
        raise CatalogUpdateError(
            error.code, str(error), error.recovery, status_code=422
        ) from error

    active = get_snapshot(database_path, state["active_snapshot_id"])
    if active is None:
        raise CatalogUpdateError(
            "catalog_active_missing",
            "The active catalog snapshot is unavailable.",
            "Use the bundled recovery catalog before previewing an update.",
        )
    diff = catalog_diff(active.payload_json, snapshot.payload_json)
    created_at = now.astimezone(UTC)
    expires_at = min(snapshot.expires_at, created_at + PREVIEW_TTL)
    material = _preview_material(
        active_snapshot_id=active.snapshot_id,
        candidate_snapshot_id=snapshot.snapshot_id,
        diff=diff,
        actor=actor,
        created_at=created_at,
        expires_at=expires_at,
    )
    preview_digest = hashlib.sha256(canonical_json(material)).hexdigest()
    preview_id = f"preview-{preview_digest[:24]}"

    with _connect(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        store_verified_snapshot(database_path, snapshot, connection=connection)
        connection.execute(
            """UPDATE catalog_update_previews SET state='superseded'
               WHERE state='open' AND actor=?""",
            (actor,),
        )
        connection.execute(
            """INSERT OR REPLACE INTO catalog_update_previews (
                preview_id, active_snapshot_id, candidate_snapshot_id, diff_json,
                preview_digest, actor, created_at, expires_at, state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')""",
            (
                preview_id,
                active.snapshot_id,
                snapshot.snapshot_id,
                canonical_json(diff).decode("utf-8"),
                preview_digest,
                actor,
                int(created_at.timestamp()),
                int(expires_at.timestamp()),
            ),
        )
        row = connection.execute(
            "SELECT * FROM catalog_update_previews WHERE preview_id=?", (preview_id,)
        ).fetchone()
    logger.info(
        "catalog_update_preview_created",
        trace_id=trace_id,
        preview_id=preview_id,
        candidate_snapshot_id=snapshot.snapshot_id,
        added=diff["summary"]["added"],
        removed=diff["summary"]["removed"],
        changed=diff["summary"]["changed"],
    )
    return _preview_response(row, snapshot)


def _user_state_digest(
    connection: sqlite3.Connection, *, server_ids: set[str] | None = None
) -> tuple[str, dict[str, int]]:
    server_rows = [
        list(row)
        for row in connection.execute(
            """SELECT server_id, is_installed, is_active, status, error_message,
                      installed_version FROM mcp_servers ORDER BY server_id"""
        )
    ]
    if server_ids is not None:
        server_rows = [row for row in server_rows if row[0] in server_ids]
    workspace_rows = [
        list(row)
        for row in connection.execute(
            """SELECT workspace_id, enabled_tools FROM engineering_workspaces
               ORDER BY workspace_id"""
        )
    ]
    digest = hashlib.sha256(
        canonical_json({"servers": server_rows, "workspaces": workspace_rows})
    ).hexdigest()
    counts = {
        "registered": len(server_rows),
        "installed": sum(int(row[1]) for row in server_rows),
        "active": sum(int(row[2]) for row in server_rows),
        "workspaces": len(workspace_rows),
    }
    return digest, counts


def _load_preview(connection: sqlite3.Connection, preview_id: str) -> sqlite3.Row:
    row = connection.execute(
        "SELECT * FROM catalog_update_previews WHERE preview_id=?", (preview_id,)
    ).fetchone()
    if row is None:
        raise CatalogUpdateError(
            "catalog_preview_not_found",
            "Catalog update preview was not found.",
            "Create and review a new preview.",
            status_code=404,
        )
    return row


def activate_catalog_update(
    database_path: str | Path,
    preview_id: str,
    preview_digest: str,
    *,
    actor: str,
    now: datetime,
    trace_id: str,
    fault: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    now = now.astimezone(UTC)
    logger.info(
        "catalog_update_activation_started",
        trace_id=trace_id,
        preview_id=preview_id,
    )
    with _connect(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        preview = _load_preview(connection, preview_id)
        if preview["state"] != "open":
            raise CatalogUpdateError(
                "catalog_preview_stale",
                "Catalog update preview is no longer open.",
                "Create and review a new preview.",
            )
        if preview["actor"] != actor:
            raise CatalogUpdateError(
                "catalog_preview_actor_mismatch",
                "Catalog update preview belongs to a different administrator.",
                "Create a new preview as the current administrator.",
                status_code=403,
            )
        if preview["preview_digest"] != preview_digest:
            raise CatalogUpdateError(
                "catalog_preview_digest_mismatch",
                "Catalog update preview digest does not match the reviewed preview.",
                "Create and review a new preview.",
            )
        if preview["expires_at"] <= int(now.timestamp()):
            connection.execute(
                "UPDATE catalog_update_previews SET state='expired' WHERE preview_id=?",
                (preview_id,),
            )
            raise CatalogUpdateError(
                "catalog_preview_expired",
                "Catalog update preview has expired.",
                "Create and review a new preview.",
            )
        state = connection.execute(
            "SELECT * FROM catalog_state WHERE state_id=1"
        ).fetchone()
        if (
            state is None
            or state["active_snapshot_id"] != preview["active_snapshot_id"]
        ):
            raise CatalogUpdateError(
                "catalog_preview_stale",
                "The active catalog changed after this preview was created.",
                "Create and review a new preview.",
            )
        candidate = get_snapshot(
            database_path, preview["candidate_snapshot_id"], connection=connection
        )
        if candidate is None or candidate.verification_state != "verified":
            raise CatalogUpdateError(
                "catalog_candidate_unavailable",
                "The verified catalog candidate is unavailable.",
                "Create and review a new preview.",
            )
        expected = hashlib.sha256(canonical_json(candidate.payload_json)).hexdigest()
        if expected != candidate.payload_sha256:
            raise CatalogUpdateError(
                "catalog_candidate_corrupt",
                "The verified catalog candidate failed its digest check.",
                "Keep the current catalog and create a new preview.",
            )

        existing_server_ids = {
            row[0] for row in connection.execute("SELECT server_id FROM mcp_servers")
        }
        before_digest, before_counts = _user_state_digest(
            connection, server_ids=existing_server_ids
        )
        reconciled = reconcile_engineering_catalog_document(
            str(database_path), candidate.payload_json, connection=connection
        )
        if fault:
            fault("after_reconcile")
        after_digest, after_counts = _user_state_digest(
            connection, server_ids=existing_server_ids
        )
        if before_digest != after_digest:
            raise CatalogUpdateError(
                "catalog_user_state_changed",
                "Catalog activation attempted to change user-owned state.",
                "Keep the current catalog and report this integrity failure.",
            )

        current_id = state["active_snapshot_id"]
        connection.execute(
            "UPDATE catalog_snapshots SET verification_state='previous' WHERE snapshot_id=?",
            (current_id,),
        )
        connection.execute(
            "UPDATE catalog_snapshots SET verification_state='active' WHERE snapshot_id=?",
            (candidate.snapshot_id,),
        )
        connection.execute(
            """UPDATE catalog_state SET active_snapshot_id=?, previous_snapshot_id=?,
                      active_generation=active_generation+1, updated_at=?, updated_by=?
               WHERE state_id=1""",
            (candidate.snapshot_id, current_id, int(now.timestamp()), actor),
        )
        connection.execute(
            "UPDATE catalog_update_previews SET state='activated' WHERE preview_id=?",
            (preview_id,),
        )
        activation_id = f"activate-{preview_digest[:20]}"
        connection.execute(
            """INSERT INTO catalog_activations (
                activation_id, from_snapshot_id, to_snapshot_id, kind,
                preview_digest, actor, trace_id, occurred_at, result, reason_code
            ) VALUES (?, ?, ?, 'activate', ?, ?, ?, ?, 'succeeded', NULL)""",
            (
                activation_id,
                current_id,
                candidate.snapshot_id,
                preview_digest,
                actor,
                trace_id,
                int(now.timestamp()),
            ),
        )
        if fault:
            fault("before_commit")
        result_state = get_catalog_state(database_path, connection=connection)
    prune_snapshots(database_path)
    logger.info(
        "catalog_update_activation_succeeded",
        trace_id=trace_id,
        preview_id=preview_id,
        active_snapshot_id=candidate.snapshot_id,
        reconciled=reconciled,
    )
    return {
        "state": result_state,
        "reconciled": reconciled,
        "preserved_user_state": before_counts == after_counts,
        "preserved_counts": after_counts,
    }


def rollback_catalog(
    database_path: str | Path,
    *,
    expected_active_snapshot_id: str,
    expected_previous_snapshot_id: str,
    actor: str,
    now: datetime,
    trace_id: str,
    fault: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    now = now.astimezone(UTC)
    logger.info("catalog_rollback_started", trace_id=trace_id)
    with _connect(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        state = connection.execute(
            "SELECT * FROM catalog_state WHERE state_id=1"
        ).fetchone()
        if (
            state is None
            or state["active_snapshot_id"] != expected_active_snapshot_id
            or state["previous_snapshot_id"] != expected_previous_snapshot_id
        ):
            raise CatalogUpdateError(
                "catalog_rollback_stale",
                "Catalog state changed before rollback.",
                "Refresh the catalog state and review rollback again.",
            )
        target = get_snapshot(
            database_path, expected_previous_snapshot_id, connection=connection
        )
        if target is None:
            raise CatalogUpdateError(
                "catalog_rollback_unavailable",
                "The previous catalog snapshot is unavailable.",
                "Use the packaged recovery catalog.",
            )
        digest = hashlib.sha256(canonical_json(target.payload_json)).hexdigest()
        if digest != target.payload_sha256:
            raise CatalogUpdateError(
                "catalog_rollback_corrupt",
                "The previous catalog snapshot failed its digest check.",
                "Use the packaged recovery catalog.",
            )
        existing_server_ids = {
            row[0] for row in connection.execute("SELECT server_id FROM mcp_servers")
        }
        before_digest, before_counts = _user_state_digest(
            connection, server_ids=existing_server_ids
        )
        reconciled = reconcile_engineering_catalog_document(
            str(database_path), target.payload_json, connection=connection
        )
        after_digest, after_counts = _user_state_digest(
            connection, server_ids=existing_server_ids
        )
        if before_digest != after_digest:
            raise CatalogUpdateError(
                "catalog_user_state_changed",
                "Catalog rollback attempted to change user-owned state.",
                "Keep the current catalog and report this integrity failure.",
            )
        if fault:
            fault("after_reconcile")
        connection.execute(
            "UPDATE catalog_snapshots SET verification_state='previous' WHERE snapshot_id=?",
            (expected_active_snapshot_id,),
        )
        connection.execute(
            "UPDATE catalog_snapshots SET verification_state='active' WHERE snapshot_id=?",
            (target.snapshot_id,),
        )
        connection.execute(
            """UPDATE catalog_state SET active_snapshot_id=?, previous_snapshot_id=?,
                      active_generation=active_generation+1, updated_at=?, updated_by=?
               WHERE state_id=1""",
            (
                target.snapshot_id,
                expected_active_snapshot_id,
                int(now.timestamp()),
                actor,
            ),
        )
        activation_id = hashlib.sha256(
            canonical_json(
                {
                    "kind": "rollback",
                    "from": expected_active_snapshot_id,
                    "to": target.snapshot_id,
                    "actor": actor,
                    "at": now.isoformat(),
                }
            )
        ).hexdigest()[:20]
        connection.execute(
            """INSERT INTO catalog_activations (
                activation_id, from_snapshot_id, to_snapshot_id, kind,
                preview_digest, actor, trace_id, occurred_at, result, reason_code
            ) VALUES (?, ?, ?, 'rollback', NULL, ?, ?, ?, 'succeeded', NULL)""",
            (
                f"rollback-{activation_id}",
                expected_active_snapshot_id,
                target.snapshot_id,
                actor,
                trace_id,
                int(now.timestamp()),
            ),
        )
        if fault:
            fault("before_commit")
        result_state = get_catalog_state(database_path, connection=connection)
    logger.info(
        "catalog_rollback_succeeded",
        trace_id=trace_id,
        active_snapshot_id=target.snapshot_id,
    )
    return {
        "state": result_state,
        "reconciled": reconciled,
        "preserved_user_state": before_counts == after_counts,
        "preserved_counts": after_counts,
    }


def recover_catalog_to_bundled(
    database_path: str | Path,
    *,
    actor: str,
    now: datetime,
    trace_id: str,
    reason_code: str,
) -> dict[str, Any]:
    bundled = bootstrap_bundled_snapshot(database_path)
    with _connect(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        state = connection.execute(
            "SELECT * FROM catalog_state WHERE state_id=1"
        ).fetchone()
        current_id = state["active_snapshot_id"]
        reconcile_engineering_catalog_document(
            str(database_path), bundled.payload_json, connection=connection
        )
        connection.execute(
            "UPDATE catalog_snapshots SET verification_state='previous' WHERE snapshot_id=?",
            (current_id,),
        )
        connection.execute(
            "UPDATE catalog_snapshots SET verification_state='active' WHERE snapshot_id=?",
            (bundled.snapshot_id,),
        )
        connection.execute(
            """UPDATE catalog_state SET active_snapshot_id=?, previous_snapshot_id=?,
                      active_generation=active_generation+1, updated_at=?, updated_by=?
               WHERE state_id=1""",
            (bundled.snapshot_id, current_id, int(now.timestamp()), actor),
        )
        activation_id = hashlib.sha256(
            f"{current_id}:{bundled.snapshot_id}:{now.isoformat()}".encode()
        ).hexdigest()[:20]
        connection.execute(
            """INSERT INTO catalog_activations (
                activation_id, from_snapshot_id, to_snapshot_id, kind,
                preview_digest, actor, trace_id, occurred_at, result, reason_code
            ) VALUES (?, ?, ?, 'recovery', NULL, ?, ?, ?, 'recovered', ?)""",
            (
                f"recovery-{activation_id}",
                current_id,
                bundled.snapshot_id,
                actor,
                trace_id,
                int(now.timestamp()),
                reason_code,
            ),
        )
        result = get_catalog_state(database_path, connection=connection)
    logger.warning(
        "catalog_recovery_succeeded",
        trace_id=trace_id,
        reason_code=reason_code,
        active_snapshot_id=bundled.snapshot_id,
    )
    return result
