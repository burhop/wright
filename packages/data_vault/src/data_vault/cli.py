from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .backup import create_backup, restore_backup
from .migrations import database_status, upgrade_database
from .models import (
    BackupResult,
    DatabaseLifecycleError,
    DatabaseStatus,
    RestoreResult,
    UpgradeResult,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wright-db")
    parser.add_argument("--json", action="store_true", dest="as_json")
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser("status")
    status.add_argument("--database", required=True)

    backup = commands.add_parser("backup")
    backup.add_argument("--database", required=True)
    backup.add_argument("--output-dir")

    upgrade = commands.add_parser("upgrade")
    upgrade.add_argument("--database", required=True)
    upgrade.add_argument("--backup-dir")

    restore = commands.add_parser("restore")
    restore.add_argument("--database", required=True)
    restore.add_argument("--manifest", required=True)
    return parser


def _human(result: dict[str, Any]) -> str:
    fields = [f"operation: {result['operation']}"]
    for key in (
        "database",
        "ready",
        "current_version",
        "target_version",
        "ending_version",
        "schema_version",
        "manifest_path",
        "snapshot_path",
        "rollback_snapshot_path",
        "message",
        "error",
    ):
        if key in result and result[key] is not None:
            fields.append(f"{key}: {result[key]}")
    return "\n".join(fields)


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result: DatabaseStatus | BackupResult | UpgradeResult | RestoreResult
        if args.command == "status":
            result = database_status(args.database)
        elif args.command == "backup":
            result = create_backup(args.database, output_dir=args.output_dir)
        elif args.command == "upgrade":
            result = upgrade_database(args.database, backup_dir=args.backup_dir)
        else:
            result = restore_backup(args.database, args.manifest)
        payload = result.to_dict()
        print(json.dumps(payload, sort_keys=True) if args.as_json else _human(payload))
        return 0
    except DatabaseLifecycleError as exc:
        payload = {
            "operation": args.command,
            "database": Path(args.database).name,
            "success": False,
            "error": str(exc),
        }
        print(
            json.dumps(payload, sort_keys=True) if args.as_json else _human(payload),
            file=sys.stderr,
        )
        return exc.exit_code


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
