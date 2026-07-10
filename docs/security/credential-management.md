# Credential Management, Migration, and Recovery

Wright keeps API, Git, MCP, and integration credentials behind one local
provider boundary. Normal API reads return configuration booleans, never stored
values. Git credentials use a short-lived askpass helper and do not enter
remote URLs or process arguments. MCP diagnostics are redacted before logging.

## Provider precedence

1. `WRIGHT_SECRET_<NAMESPACE>_<OWNER>_<NAME>` environment variables.
2. Files with the same encoded name under `WRIGHT_SECRETS_DIR`.
3. The owner-only atomic fallback at `WRIGHT_SECRETS_PATH`.

Environment and mounted-file providers are read-only. Administrative writes go
to the fallback. A separate lock file protects cross-process transactions;
updates use a restricted temporary sibling, flush/fsync, and atomic replace.

## Upgrade from plaintext state

At API startup, Wright detects legacy `system_settings.api_keys` and workspace
`git_token` values. Before importing anything it writes an owner-only backup at
`<database>.secrets-backup.json` (override with
`WRIGHT_SECRET_MIGRATION_BACKUP`). Values are imported and read back before a
SQLite transaction removes plaintext. Failure aborts startup and leaves the
source plus backup available for recovery.

Treat the backup as sensitive. Move it to encrypted offline storage or remove
it after the new provider and application operations have been verified.

## Rotation and removal

Set a new value through the authenticated settings or MCP credential operation.
Omitted and blank placeholder fields preserve existing values. Explicit removal
uses the named removal operation. Rotate an upstream credential first when it
may have leaked, then replace Wright's value.

## Rollback

Stop Wright and protect copies of the current database and credential store.
Invoke `restore_plaintext_backup(database_path, backup_path)` from
`api.database.secret_migration` in the recovery environment. This restores the
legacy database fields without printing values. Rollback weakens storage and is
only for returning to the previous image long enough to recover.

The repository helper is:

```bash
uv run python scripts/restore-secret-backup.py <state.db> <backup.json>
```
