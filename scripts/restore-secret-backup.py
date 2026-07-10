"""Restore a Feature 043 plaintext backup for emergency image rollback."""

from __future__ import annotations

import argparse

from api.database.secret_migration import restore_plaintext_backup


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore a restricted Wright credential migration backup."
    )
    parser.add_argument("database")
    parser.add_argument("backup")
    args = parser.parse_args()
    restore_plaintext_backup(args.database, args.backup)
    print("Credential backup restored; values were not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
