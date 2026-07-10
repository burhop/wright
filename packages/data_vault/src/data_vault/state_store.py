from __future__ import annotations

import os
import sqlite3
from pathlib import Path


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def connect_state_db(
    db_path: str | os.PathLike[str],
    *,
    ensure_parent: bool = False,
    wal: bool = True,
    read_only: bool = False,
    timeout: float = 5.0,
) -> sqlite3.Connection:
    """Open Wright local state SQLite with shared connection defaults."""
    path = Path(db_path)
    if ensure_parent and path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)

    target = f"file:{path.resolve()}?mode=ro" if read_only else str(path)
    conn = sqlite3.connect(
        target,
        factory=ClosingConnection,
        uri=read_only,
        timeout=timeout,
        isolation_level=None,
    )
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout = {max(0, int(timeout * 1000))};")
    conn.execute("PRAGMA foreign_keys = ON;")
    if wal and not read_only:
        conn.execute("PRAGMA journal_mode=WAL;")
    return conn
