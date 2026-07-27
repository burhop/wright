# Database Migration and Recovery

Wright owns its SQLite schema through numbered, checksummed migrations in the
data-vault package. Application startup upgrades supported state before any
agent, MCP engine, or workspace runtime is constructed. Integrity failure,
foreign-key inconsistency, changed migration history, an unknown newer schema,
or an interrupted migration prevents startup.

## Supported source states

- A new database or empty database file.
- The complete unversioned state shipped immediately before Feature 044.
- Historical partial shapes tolerated by that release, including missing MCP
  metadata columns, workspace metadata columns, session associations, message
  state, and settings tables.
- Any database with a contiguous migration ledger whose identifiers and
  checksums match the installed release.

Unknown future versions, ledger gaps, edited checksums, and corrupt databases
are never upgraded in place. Preserve them and restore a verified backup or use
the newer Wright release that owns the schema.

## Inspect state without mutation

Stop the Wright appliance before maintenance, then run:

```bash
uv run --package wright-data-vault wright-db --json status \
  --database /path/to/wright.db
```

Status reports only the database filename, integrity, current and target
versions, pending migration identifiers, compatibility, readiness, and a
redacted summary. It does not create a database or expose rows.

## Create a backup

```bash
uv run --package wright-data-vault wright-db backup \
  --database /path/to/wright.db \
  --output-dir /secure/wright-backups
```

The command uses SQLite's online snapshot mechanism rather than copying a live
WAL file. It publishes an owner-restricted `.db` snapshot and adjacent
`.manifest.json` only after database integrity, foreign keys, size, digest,
schema version, and migration checksums are verified. Store both files
together. The manifest contains no database rows or credentials.

Backups are operator-managed. Retain at least the last verified pre-upgrade
pair until the new release has passed application and workspace smoke tests.
Move older pairs to offline storage or delete them according to local policy;
never delete the only known-good pre-upgrade pair during an upgrade.

## Upgrade explicitly

```bash
uv run --package wright-data-vault wright-db --json upgrade \
  --database /path/to/wright.db \
  --backup-dir /secure/wright-backups
```

An existing database with pending migrations receives a verified pre-upgrade
backup before mutation. Each migration and its ledger entry share one
transaction. A failure rolls that migration back and leaves the last completed
version durable. Repeating upgrade on current state is safe and applies no
changes.

Normal Wright startup invokes the same upgrade service through a one-release
compatibility wrapper. Catalog reconciliation happens afterward in a separate
transaction; direct `wright-db upgrade` never seeds or resets MCP catalog rows.

## Restore and rollback

Stop Wright and ensure no process has the database open:

```bash
uv run --package wright-data-vault wright-db restore \
  --database /path/to/wright.db \
  --manifest /secure/wright-backups/wright-BACKUP.manifest.json
```

Restore confines the snapshot name to the manifest directory and validates the
manifest format, digest, size, supported schema, exact migration checksums,
integrity, and foreign keys before activation. It then preserves the displaced
database in the local backup directory, checkpoints the active WAL, and
atomically activates the candidate. A corrupt active database is preserved as
a restricted raw evidence copy before replacement.

Downgrade is restore-only:

1. Stop the newer Wright release.
2. Restore the verified backup created before its upgrade.
3. Start the older release and run its status and application smoke checks.

Do not edit the migration ledger, run reverse SQL manually, copy a live
database/WAL pair, or start an older release against a newer schema.

## Failure handling

The command exits nonzero for incompatible state (`3`), corruption (`4`), a
busy lifecycle (`5`), filesystem/permission failure (`6`), or migration/restore
failure (`7`). Usage errors exit `2`. With `--json`, stdout/stderr remains
machine-readable and contains no row values.

- **Busy**: stop the API/appliance and retry. Do not remove the stable lock
  file; the operating-system lock, not file presence, determines ownership.
- **Permission failure**: make the database parent and selected backup
  directory writable only to the Wright operator, then retry.
- **Checksum/future version**: use the matching newer release or restore a
  compatible backup. Never stamp the ledger.
- **Corruption/foreign-key failure**: preserve the database and sidecars, then
  restore a verified snapshot. Keep the displaced evidence until recovery is
  confirmed.
- **Interrupted upgrade**: inspect status, confirm the last completed version,
  and retry with the same release. The interrupted migration was rolled back.

Feature 043 credential migration backups are separate restricted recovery
artifacts. Do not merge them into state manifests or paste either artifact into
logs, issues, or support messages.

## Recovery performance evidence

Maintainers can reproduce the one-gigabyte local target without retaining test
data:

```bash
uv run --package wright-data-vault python scripts/benchmark-database-recovery.py \
  --size-mib 1024 --limit-seconds 300
```

The script creates a temporary migrated database, snapshots and restores it,
prints timings and byte size as JSON, and removes all generated databases on
exit. Record the platform and result in the implementation ledger; this is a
local storage benchmark, not a claim about every filesystem or host.
