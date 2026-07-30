"""Native activation preflight around Wright's durable data-vault migrations."""

from __future__ import annotations

from pathlib import Path


class MigrationPreflightError(RuntimeError):
    pass


class NativeMigrationManager:
    @staticmethod
    def database_path(data_root: Path) -> Path:
        return data_root / "wright.db"

    def current_schema(self, data_root: Path) -> int:
        from data_vault import database_status

        return database_status(self.database_path(data_root)).current_version

    def prepare_activation(
        self,
        *,
        data_root: Path,
        data_schema_min: int,
        data_schema_max: int,
        operation_id: str,
    ) -> str | None:
        from data_vault import upgrade_database
        from data_vault.migrations import require_schema_compatible

        database = self.database_path(data_root)
        before = self.current_schema(data_root)
        if before > data_schema_max:
            raise MigrationPreflightError("data_schema_newer_than_candidate")
        result = upgrade_database(database, backup_dir=data_root / "backups")
        require_schema_compatible(
            result.ending_version,
            minimum=data_schema_min,
            maximum=data_schema_max,
        )
        return result.backup_manifest
