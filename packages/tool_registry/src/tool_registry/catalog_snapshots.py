from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .canonical_catalog import (
    CatalogValidationError,
    _validate_catalog_document,
    load_catalog_document,
)
from .capability_models import CatalogSnapshot
from .catalog_signing import canonical_json

BUNDLED_CHANNEL = "bundled"
BUNDLED_SEQUENCE = 1
BUNDLED_ISSUED_AT = datetime(2026, 8, 12, tzinfo=UTC)
BUNDLED_EXPIRES_AT = datetime(2100, 1, 1, tzinfo=UTC)
SNAPSHOT_RETENTION = 10


class CatalogSnapshotError(RuntimeError):
    pass


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _snapshot_from_row(row: sqlite3.Row) -> CatalogSnapshot:
    return CatalogSnapshot(
        snapshot_id=row["snapshot_id"],
        channel=row["channel"],
        sequence=row["sequence"],
        schema_version=row["schema_version"],
        issued_at=datetime.fromtimestamp(row["issued_at"], UTC),
        expires_at=datetime.fromtimestamp(row["expires_at"], UTC),
        payload_sha256=row["payload_sha256"],
        payload_json=json.loads(row["payload_json"]),
        envelope_json=json.loads(row["envelope_json"])
        if row["envelope_json"]
        else None,
        signer_key_id=row["signer_key_id"],
        signature=row["signature"],
        verification_state=row["verification_state"],
        verified_at=datetime.fromtimestamp(row["verified_at"], UTC)
        if row["verified_at"]
        else None,
        rejection_code=row["rejection_code"],
    )


def _insert_snapshot(connection: sqlite3.Connection, snapshot: CatalogSnapshot) -> None:
    connection.execute(
        """INSERT OR IGNORE INTO catalog_snapshots (
            snapshot_id, channel, sequence, schema_version, issued_at, expires_at,
            payload_sha256, payload_json, envelope_json, signer_key_id, signature,
            verification_state, verified_at, rejection_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            snapshot.snapshot_id,
            snapshot.channel,
            snapshot.sequence,
            snapshot.schema_version,
            int(snapshot.issued_at.timestamp()),
            int(snapshot.expires_at.timestamp()),
            snapshot.payload_sha256,
            canonical_json(snapshot.payload_json).decode("utf-8"),
            canonical_json(snapshot.envelope_json).decode("utf-8")
            if snapshot.envelope_json
            else None,
            snapshot.signer_key_id,
            snapshot.signature,
            snapshot.verification_state,
            int(snapshot.verified_at.timestamp()) if snapshot.verified_at else None,
            snapshot.rejection_code,
        ),
    )


def bundled_snapshot(payload: dict[str, Any] | None = None) -> CatalogSnapshot:
    document = _validate_catalog_document(payload or load_catalog_document())
    digest = hashlib.sha256(canonical_json(document)).hexdigest()
    return CatalogSnapshot(
        snapshot_id=f"bundled-{digest[:20]}",
        channel=BUNDLED_CHANNEL,
        sequence=BUNDLED_SEQUENCE,
        schema_version=1,
        issued_at=BUNDLED_ISSUED_AT,
        expires_at=BUNDLED_EXPIRES_AT,
        payload_sha256=digest,
        payload_json=document,
        envelope_json=None,
        signer_key_id=None,
        signature=None,
        verification_state="active",
        verified_at=BUNDLED_ISSUED_AT,
    )


def bootstrap_bundled_snapshot(
    database_path: str | Path,
    *,
    payload: dict[str, Any] | None = None,
    actor: str = "wright-bootstrap",
    trace_id: str = "catalog-bootstrap",
) -> CatalogSnapshot:
    snapshot = bundled_snapshot(payload)
    with _connect(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        _insert_snapshot(connection, snapshot)
        stored_row = connection.execute(
            "SELECT * FROM catalog_snapshots WHERE channel=? AND sequence=?",
            (BUNDLED_CHANNEL, BUNDLED_SEQUENCE),
        ).fetchone()
        if stored_row is None:
            raise CatalogSnapshotError("Bundled catalog snapshot was not persisted")
        stored_snapshot = _snapshot_from_row(stored_row)
        state = connection.execute(
            "SELECT active_snapshot_id FROM catalog_state WHERE state_id=1"
        ).fetchone()
        if state is None:
            connection.execute(
                """INSERT INTO catalog_state (
                    state_id, active_snapshot_id, previous_snapshot_id,
                    active_generation, updated_at, updated_by
                ) VALUES (1, ?, NULL, 1, ?, ?)""",
                (
                    stored_snapshot.snapshot_id,
                    int(BUNDLED_ISSUED_AT.timestamp()),
                    actor,
                ),
            )
            connection.execute(
                """INSERT OR IGNORE INTO catalog_activations (
                    activation_id, from_snapshot_id, to_snapshot_id, kind,
                    preview_digest, actor, trace_id, occurred_at, result, reason_code
                ) VALUES (?, NULL, ?, 'bootstrap', NULL, ?, ?, ?, 'succeeded', NULL)""",
                (
                    f"bootstrap-{stored_snapshot.snapshot_id}",
                    stored_snapshot.snapshot_id,
                    actor,
                    trace_id,
                    int(BUNDLED_ISSUED_AT.timestamp()),
                ),
            )
        return stored_snapshot


def known_catalog_server_ids(database_path: str | Path) -> set[str]:
    """Return identities seen in immutable catalog snapshots.

    This lets capability projection distinguish a catalog row left behind by a
    rollback from a user-created custom server without deleting either row.
    """
    with _connect(database_path) as connection:
        rows = connection.execute(
            "SELECT payload_json FROM catalog_snapshots"
        ).fetchall()
    identities: set[str] = set()
    for row in rows:
        try:
            document = json.loads(row["payload_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        for entry in document.get("servers", []):
            server_id = entry.get("server_id") or entry.get("id")
            if isinstance(server_id, str) and server_id:
                identities.add(server_id)
    return identities


def store_verified_snapshot(
    database_path: str | Path,
    snapshot: CatalogSnapshot,
    *,
    connection: sqlite3.Connection | None = None,
) -> CatalogSnapshot:
    owns_connection = connection is None
    connection = connection or _connect(database_path)
    try:
        _insert_snapshot(connection, snapshot)
        row = connection.execute(
            "SELECT * FROM catalog_snapshots WHERE snapshot_id=?",
            (snapshot.snapshot_id,),
        ).fetchone()
        if row is None:
            raise CatalogSnapshotError("Verified snapshot was not persisted")
        stored = _snapshot_from_row(row)
        if stored.payload_sha256 != snapshot.payload_sha256:
            raise CatalogSnapshotError("Stored snapshot identity conflict")
        if owns_connection:
            connection.commit()
        return stored
    finally:
        if owns_connection:
            connection.close()


def get_snapshot(
    database_path: str | Path,
    snapshot_id: str,
    *,
    connection: sqlite3.Connection | None = None,
) -> CatalogSnapshot | None:
    owns_connection = connection is None
    connection = connection or _connect(database_path)
    try:
        row = connection.execute(
            "SELECT * FROM catalog_snapshots WHERE snapshot_id=?", (snapshot_id,)
        ).fetchone()
        return _snapshot_from_row(row) if row else None
    finally:
        if owns_connection:
            connection.close()


def get_catalog_state(
    database_path: str | Path, *, connection: sqlite3.Connection | None = None
) -> dict[str, Any]:
    owns_connection = connection is None
    connection = connection or _connect(database_path)
    try:
        row = connection.execute(
            """SELECT s.*, active.sequence AS active_sequence,
                      active.channel AS active_channel
               FROM catalog_state s
               JOIN catalog_snapshots active
                 ON active.snapshot_id=s.active_snapshot_id
               WHERE s.state_id=1"""
        ).fetchone()
        if row is None:
            raise CatalogSnapshotError("Catalog state is not bootstrapped")
        bundled = connection.execute(
            """SELECT snapshot_id FROM catalog_snapshots
               WHERE channel='bundled' ORDER BY sequence ASC LIMIT 1"""
        ).fetchone()
        history = connection.execute(
            """SELECT activation_id, from_snapshot_id, to_snapshot_id, kind,
                      actor, trace_id, occurred_at, result, reason_code
               FROM catalog_activations ORDER BY occurred_at DESC, activation_id DESC
               LIMIT 20"""
        ).fetchall()
        return {
            "bundled_snapshot_id": bundled[0] if bundled else None,
            "active_snapshot_id": row["active_snapshot_id"],
            "previous_snapshot_id": row["previous_snapshot_id"],
            "active_sequence": row["active_sequence"],
            "active_channel": row["active_channel"],
            "active_generation": row["active_generation"],
            "updated_at": datetime.fromtimestamp(row["updated_at"], UTC).isoformat(),
            "updated_by": row["updated_by"],
            "history": [dict(item) for item in history],
            "diagnostic": None,
        }
    finally:
        if owns_connection:
            connection.close()


def load_active_catalog(
    database_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Load the active immutable payload or fail read-only to the packaged root."""
    try:
        state = get_catalog_state(database_path)
        snapshot = get_snapshot(database_path, state["active_snapshot_id"])
        if snapshot is None:
            raise CatalogSnapshotError("Active catalog snapshot is missing")
        actual_digest = hashlib.sha256(
            canonical_json(snapshot.payload_json)
        ).hexdigest()
        if actual_digest != snapshot.payload_sha256:
            raise CatalogSnapshotError("Active catalog snapshot digest is invalid")
        return _validate_catalog_document(snapshot.payload_json), None
    except (
        CatalogSnapshotError,
        CatalogValidationError,
        ValueError,
        json.JSONDecodeError,
    ):
        return load_catalog_document(), {
            "code": "catalog_recovery_bundled",
            "message": "The active catalog could not be read safely.",
            "recovery": "Wright is using the packaged recovery catalog.",
        }


def prune_snapshots(
    database_path: str | Path,
    *,
    retain: int = SNAPSHOT_RETENTION,
    connection: sqlite3.Connection | None = None,
) -> int:
    owns_connection = connection is None
    connection = connection or _connect(database_path)
    try:
        protected = connection.execute(
            """SELECT active_snapshot_id, previous_snapshot_id FROM catalog_state
               WHERE state_id=1"""
        ).fetchone()
        protected_ids = {item for item in protected or () if item}
        protected_ids.update(
            row[0]
            for row in connection.execute(
                "SELECT snapshot_id FROM catalog_snapshots WHERE channel='bundled'"
            )
        )
        candidates = connection.execute(
            """SELECT snapshot_id FROM catalog_snapshots
               ORDER BY verified_at DESC, issued_at DESC"""
        ).fetchall()
        keep = protected_ids.union(row[0] for row in candidates[:retain])
        removed = 0
        for (snapshot_id,) in candidates:
            if snapshot_id in keep:
                continue
            try:
                removed += connection.execute(
                    "DELETE FROM catalog_snapshots WHERE snapshot_id=?", (snapshot_id,)
                ).rowcount
            except sqlite3.IntegrityError:
                continue
        if owns_connection:
            connection.commit()
        return removed
    finally:
        if owns_connection:
            connection.close()
