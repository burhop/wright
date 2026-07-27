"""One-release compatibility entrypoint for the data-vault migration service."""

from __future__ import annotations

from api.config import DATABASE_PATH
from data_vault import UpgradeResult, upgrade_database


def run_migrations(database_path: str | None = None) -> UpgradeResult:
    return upgrade_database(database_path or DATABASE_PATH)


if __name__ == "__main__":
    result = run_migrations()
    print(
        f"Database ready at schema {result.ending_version}; "
        f"applied {len(result.applied)} migration(s)."
    )
