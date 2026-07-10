"""Wright data vault storage helpers."""

from .backup import create_backup, restore_backup
from .migrations import MIGRATIONS, database_status, upgrade_database
from .models import (
    BackupResult,
    DatabaseLifecycleError,
    DatabaseStatus,
    RestoreResult,
    UpgradeResult,
)
from .state_store import ClosingConnection, connect_state_db
from .workspace_repository import WorkspaceRepository
from .secret_provider import (
    CompositeSecretProvider,
    EnvironmentSecretProvider,
    FileSecretProvider,
    MountedSecretProvider,
    create_default_secret_provider,
    install_default_secret_provider,
)

__all__ = [
    "MIGRATIONS",
    "BackupResult",
    "ClosingConnection",
    "DatabaseLifecycleError",
    "DatabaseStatus",
    "RestoreResult",
    "UpgradeResult",
    "WorkspaceRepository",
    "CompositeSecretProvider",
    "EnvironmentSecretProvider",
    "FileSecretProvider",
    "MountedSecretProvider",
    "create_default_secret_provider",
    "install_default_secret_provider",
    "connect_state_db",
    "create_backup",
    "database_status",
    "restore_backup",
    "upgrade_database",
]
