# Database Lifecycle Contract

## Command grammar

```text
wright-db [--json] status  --database PATH
wright-db [--json] backup  --database PATH [--output-dir DIR]
wright-db [--json] upgrade --database PATH [--backup-dir DIR]
wright-db [--json] restore --database PATH --manifest MANIFEST
```

`status` is read-only. Mutating commands serialize through the lifecycle lock. Human output contains paths, versions, migration identifiers, integrity state, and recovery guidance only. JSON output uses the result objects below and never includes database rows or credentials.

## Stable exit behavior

- `0`: requested operation completed and resulting state is verified
- `2`: usage or unsupported input
- `3`: incompatible version, checksum drift, or invalid manifest
- `4`: integrity/corruption failure
- `5`: lifecycle lock or SQLite busy timeout
- `6`: filesystem/permission failure
- `7`: migration or restore execution failure

## Status result

```json
{
  "operation": "status",
  "database": "wright.db",
  "exists": true,
  "integrity": "ok",
  "foreign_keys_ok": true,
  "current_version": 4,
  "target_version": 4,
  "pending": [],
  "compatible": true,
  "ready": true,
  "message": "Database is ready"
}
```

## Backup result

Returns operation, database basename, backup ID, snapshot path, manifest path, schema version, digest, integrity status, and success. It returns no row counts by sensitive category and no row values.

## Upgrade result

Returns operation, pre-upgrade backup manifest, starting/ending versions, applied migration versions/names, final integrity, and readiness. If no migration is pending, `applied` is empty and the operation remains successful and idempotent.

## Restore result

Returns operation, activated manifest/backup ID, restored version, displaced-state recovery manifest/path, final integrity, and readiness. Before activation failure returns no displaced state because the current database is unchanged.

## API startup compatibility

`api.database.migrate.run_migrations(database_path=None)` delegates to the data-vault upgrade service. It raises a lifecycle exception on any failure; callers MUST NOT catch and continue. After successful schema readiness, the API composition root invokes catalog reconciliation as a separate operation. The wrapper is retained for one release and emits no schema SQL itself.

## Manifest compatibility

Restore accepts only known manifest format versions and schema versions supported by installed migration definitions. Snapshot filename resolution is confined to the manifest directory. Digest, size, recorded checksums, integrity, and foreign-key checks must all pass before activation.
