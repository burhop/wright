# Wright Data Vault

`wright-data-vault` owns Wright's embedded SQLite connection policy, numbered
schema migrations, migration ledger, integrity checks, consistent backups, and
verified restore activation. Application packages may use repositories after
readiness, but they must not create or alter schema.

The internal operator command is available in the workspace as:

```bash
uv run --package wright-data-vault wright-db --json status --database /path/to/wright.db
```

See [Database Recovery](../../docs/operations/database-recovery.md) for backup,
upgrade, restore, failure, and rollback procedures. This internal package is
not an independently supported public distribution.
