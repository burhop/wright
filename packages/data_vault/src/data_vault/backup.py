from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import tempfile
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence
from collections.abc import Callable

from .lifecycle_lock import lifecycle_lock
from .migrations import (
    MIGRATIONS,
    PRODUCT_VERSION,
    Migration,
    database_status,
    ledger_entries,
)
from .models import (
    BackupManifest,
    BackupResult,
    DatabaseCompatibilityError,
    DatabaseBusyError,
    DatabaseFilesystemError,
    DatabaseIntegrityError,
    RestoreResult,
)
from .state_store import connect_state_db

MANIFEST_FORMAT_VERSION = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _restrict(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError as exc:
        raise DatabaseFilesystemError("Unable to restrict database backup") from exc


def _sync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _verify_database(path: Path) -> None:
    try:
        with connect_state_db(path, read_only=True, wal=False) as connection:
            quick = connection.execute("PRAGMA quick_check").fetchone()
            foreign = connection.execute("PRAGMA foreign_key_check").fetchone()
    except sqlite3.DatabaseError as exc:
        raise DatabaseIntegrityError("Backup database cannot be inspected") from exc
    if not quick or str(quick[0]).lower() != "ok" or foreign is not None:
        raise DatabaseIntegrityError("Backup database integrity check failed")


def _prepare_for_replacement(path: Path) -> None:
    try:
        connection = sqlite3.connect(path, timeout=5.0)
        try:
            connection.execute("PRAGMA busy_timeout = 5000")
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            connection.execute("PRAGMA journal_mode=DELETE").fetchone()
        finally:
            connection.close()
    except sqlite3.DatabaseError as exc:
        raise DatabaseBusyError("Database must be stopped before restore") from exc


def _write_manifest(path: Path, manifest: BackupManifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as handle:
            json.dump(manifest.to_dict(), handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        _restrict(temporary)
        os.replace(temporary, path)
        _restrict(path)
        _sync_directory(path.parent)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def create_backup(
    database_path: str | os.PathLike[str],
    *,
    output_dir: str | os.PathLike[str] | None = None,
    acquire_lock: bool = True,
    migrations: Sequence[Migration] = MIGRATIONS,
) -> BackupResult:
    source = Path(database_path)
    if not source.exists():
        raise DatabaseFilesystemError("Database does not exist")
    destination_dir = Path(output_dir or source.parent / "backups")
    try:
        destination_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DatabaseFilesystemError("Unable to create backup directory") from exc
    context = lifecycle_lock(source) if acquire_lock else nullcontext()
    with context:
        status = database_status(source, migrations)
        backup_id = (
            datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
        )
        snapshot = destination_dir / f"{source.stem}-{backup_id}.db"
        manifest_path = snapshot.with_suffix(".manifest.json")
        temporary = destination_dir / f".{snapshot.name}.{secrets.token_hex(4)}.tmp"
        try:
            with connect_state_db(source, read_only=True, wal=False) as source_conn:
                destination = sqlite3.connect(temporary)
                try:
                    source_conn.backup(destination)
                    destination.commit()
                finally:
                    destination.close()
            _restrict(temporary)
            _verify_database(temporary)
            digest = _sha256(temporary)
            size = temporary.stat().st_size
            os.replace(temporary, snapshot)
            _restrict(snapshot)
            with connect_state_db(snapshot, read_only=True, wal=False) as connection:
                checksums = tuple(
                    {"version": int(row["version"]), "checksum": row["checksum"]}
                    for row in ledger_entries(connection)
                )
            manifest = BackupManifest(
                format_version=MANIFEST_FORMAT_VERSION,
                backup_id=backup_id,
                created_at=datetime.now(UTC).isoformat(),
                source_name=source.name,
                database_file=snapshot.name,
                database_sha256=digest,
                database_size=size,
                schema_version=status.current_version,
                migration_checksums=checksums,
                product_version=PRODUCT_VERSION,
            )
            _write_manifest(manifest_path, manifest)
            _sync_directory(destination_dir)
            return BackupResult(
                database=source.name,
                backup_id=backup_id,
                snapshot_path=str(snapshot),
                manifest_path=str(manifest_path),
                schema_version=status.current_version,
                sha256=digest,
                size=size,
            )
        except (DatabaseIntegrityError, DatabaseCompatibilityError):
            raise
        except OSError as exc:
            raise DatabaseFilesystemError("Database backup failed") from exc
        finally:
            if temporary.exists():
                temporary.unlink()


def load_manifest(
    manifest_path: str | os.PathLike[str],
    *,
    migrations: Sequence[Migration] = MIGRATIONS,
) -> tuple[BackupManifest, Path]:
    path = Path(manifest_path)
    try:
        payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        payload["migration_checksums"] = tuple(payload.get("migration_checksums", []))
        manifest = BackupManifest(**payload)
    except (OSError, ValueError, TypeError) as exc:
        raise DatabaseCompatibilityError("Backup manifest is invalid") from exc
    if manifest.format_version != MANIFEST_FORMAT_VERSION:
        raise DatabaseCompatibilityError("Backup manifest format is unsupported")
    if manifest.compatible_product_range != ">=0.1.0":
        raise DatabaseCompatibilityError("Backup product compatibility is unsupported")
    if Path(manifest.database_file).name != manifest.database_file:
        raise DatabaseCompatibilityError("Backup manifest database path is unsafe")
    if not 0 <= manifest.schema_version <= len(migrations):
        raise DatabaseCompatibilityError("Backup schema version is unsupported")
    expected = [
        {"version": migration.version, "checksum": migration.checksum}
        for migration in migrations[: manifest.schema_version]
    ]
    if list(manifest.migration_checksums) != expected:
        raise DatabaseCompatibilityError("Backup migration checksums do not match")
    snapshot = path.parent / manifest.database_file
    if snapshot.is_symlink() or snapshot.resolve().parent != path.parent.resolve():
        raise DatabaseCompatibilityError("Backup snapshot path is unsafe")
    if not snapshot.is_file():
        raise DatabaseCompatibilityError("Backup snapshot is missing")
    if snapshot.stat().st_size != manifest.database_size:
        raise DatabaseCompatibilityError("Backup snapshot size does not match")
    if _sha256(snapshot) != manifest.database_sha256:
        raise DatabaseCompatibilityError("Backup snapshot digest does not match")
    _verify_database(snapshot)
    status = database_status(snapshot, migrations)
    if status.current_version != manifest.schema_version:
        raise DatabaseCompatibilityError("Backup schema version does not match")
    return manifest, snapshot


def restore_backup(
    database_path: str | os.PathLike[str],
    manifest_path: str | os.PathLike[str],
    *,
    migrations: Sequence[Migration] = MIGRATIONS,
    failure_hook: Callable[[str], None] | None = None,
) -> RestoreResult:
    target = Path(database_path)
    manifest, snapshot = load_manifest(manifest_path, migrations=migrations)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DatabaseFilesystemError("Unable to create restore directory") from exc
    with lifecycle_lock(target):
        candidate = target.parent / f".{target.name}.restore-{secrets.token_hex(6)}.tmp"
        rollback_path: str | None = None
        rollback_snapshot: Path | None = None
        try:
            shutil.copyfile(snapshot, candidate)
            _restrict(candidate)
            if (
                candidate.stat().st_size != manifest.database_size
                or _sha256(candidate) != manifest.database_sha256
            ):
                raise DatabaseCompatibilityError(
                    "Restore candidate no longer matches its manifest"
                )
            _verify_database(candidate)
            if target.exists():
                try:
                    rollback = create_backup(
                        target,
                        output_dir=target.parent / "backups",
                        acquire_lock=False,
                        migrations=migrations,
                    )
                    rollback_path = rollback.snapshot_path
                    rollback_snapshot = Path(rollback.snapshot_path)
                    _prepare_for_replacement(target)
                except DatabaseIntegrityError:
                    rollback_dir = target.parent / "backups"
                    rollback_dir.mkdir(parents=True, exist_ok=True)
                    rollback_snapshot = rollback_dir / (
                        f"{target.stem}-displaced-corrupt-{secrets.token_hex(6)}.db"
                    )
                    shutil.copyfile(target, rollback_snapshot)
                    _restrict(rollback_snapshot)
                    rollback_path = str(rollback_snapshot)
            if failure_hook:
                failure_hook("before_activation")
            for suffix in ("-wal", "-shm"):
                sidecar = Path(f"{target}{suffix}")
                if sidecar.exists():
                    sidecar.unlink()
            os.replace(candidate, target)
            _restrict(target)
            _sync_directory(target.parent)
            if failure_hook:
                failure_hook("after_activation")
            status = database_status(target, migrations)
            if status.current_version != manifest.schema_version:
                raise DatabaseIntegrityError("Restored database version is invalid")
            return RestoreResult(
                database=target.name,
                backup_id=manifest.backup_id,
                restored_version=manifest.schema_version,
                rollback_snapshot_path=rollback_path,
                ready=status.ready,
            )
        except OSError as exc:
            if rollback_snapshot and rollback_snapshot.exists():
                shutil.copyfile(rollback_snapshot, target)
                _restrict(target)
            raise DatabaseFilesystemError("Database restore failed") from exc
        except Exception:
            if rollback_snapshot and rollback_snapshot.exists():
                shutil.copyfile(rollback_snapshot, target)
                _restrict(target)
            raise
        finally:
            if candidate.exists():
                candidate.unlink()
