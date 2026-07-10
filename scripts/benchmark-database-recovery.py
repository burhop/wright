#!/usr/bin/env python3
"""Measure local Wright database backup/restore against the recovery target."""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
import time
from contextlib import closing
from pathlib import Path

from data_vault import create_backup, restore_backup, upgrade_database


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size-mib", type=int, default=1024)
    parser.add_argument("--limit-seconds", type=float, default=300.0)
    parser.add_argument("--work-dir", type=Path)
    args = parser.parse_args()
    if args.size_mib < 1:
        parser.error("--size-mib must be positive")

    with tempfile.TemporaryDirectory(dir=args.work_dir) as directory:
        root = Path(directory)
        database = root / "benchmark.db"
        upgrade_database(database)
        with closing(sqlite3.connect(database)) as connection:
            connection.execute("CREATE TABLE benchmark_payload (payload BLOB NOT NULL)")
            remaining = args.size_mib
            while remaining:
                chunk_mib = min(64, remaining)
                connection.execute(
                    "INSERT INTO benchmark_payload VALUES (zeroblob(?))",
                    (chunk_mib * 1024 * 1024,),
                )
                remaining -= chunk_mib
            connection.commit()

        started = time.perf_counter()
        backup = create_backup(database, output_dir=root / "backups")
        backup_seconds = time.perf_counter() - started

        started = time.perf_counter()
        restored = restore_backup(database, backup.manifest_path)
        restore_seconds = time.perf_counter() - started
        total_seconds = backup_seconds + restore_seconds
        result = {
            "requested_mib": args.size_mib,
            "database_bytes": database.stat().st_size,
            "backup_seconds": round(backup_seconds, 3),
            "restore_seconds": round(restore_seconds, 3),
            "total_seconds": round(total_seconds, 3),
            "limit_seconds": args.limit_seconds,
            "ready": restored.ready,
            "passed": restored.ready and total_seconds <= args.limit_seconds,
        }
        print(json.dumps(result, sort_keys=True))
        return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
