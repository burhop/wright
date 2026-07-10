from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal


class DatabaseLifecycleError(RuntimeError):
    """Base error for state lifecycle operations."""

    exit_code = 7


class DatabaseCompatibilityError(DatabaseLifecycleError):
    exit_code = 3


class DatabaseIntegrityError(DatabaseLifecycleError):
    exit_code = 4


class DatabaseBusyError(DatabaseLifecycleError):
    exit_code = 5


class DatabaseFilesystemError(DatabaseLifecycleError):
    exit_code = 6


@dataclass(frozen=True)
class DatabaseStatus:
    database: str
    exists: bool
    integrity: Literal["ok", "corrupt", "locked", "unavailable"]
    foreign_keys_ok: bool
    current_version: int
    target_version: int
    pending: tuple[int, ...] = ()
    compatible: bool = True
    ready: bool = False
    message: str = ""
    operation: str = "status"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["pending"] = list(self.pending)
        return result


@dataclass(frozen=True)
class UpgradeResult:
    database: str
    starting_version: int
    ending_version: int
    applied: tuple[dict[str, Any], ...]
    ready: bool
    backup_manifest: str | None = None
    operation: str = "upgrade"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["applied"] = list(self.applied)
        return result


@dataclass(frozen=True)
class BackupResult:
    database: str
    backup_id: str
    snapshot_path: str
    manifest_path: str
    schema_version: int
    sha256: str
    size: int
    operation: str = "backup"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RestoreResult:
    database: str
    backup_id: str
    restored_version: int
    rollback_snapshot_path: str | None
    ready: bool
    operation: str = "restore"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BackupManifest:
    format_version: int
    backup_id: str
    created_at: str
    source_name: str
    database_file: str
    database_sha256: str
    database_size: int
    schema_version: int
    migration_checksums: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    integrity_check: str = "ok"
    foreign_key_check: str = "ok"
    product_version: str = "0.1.0"
    compatible_product_range: str = ">=0.1.0"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["migration_checksums"] = list(self.migration_checksums)
        return result

    @property
    def snapshot_name(self) -> str:
        return Path(self.database_file).name
