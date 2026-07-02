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
) -> sqlite3.Connection:
    """Open Wright local state SQLite with shared connection defaults."""
    path = Path(db_path)
    if ensure_parent and path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    if wal:
        conn.execute("PRAGMA journal_mode=WAL;")
    return conn
