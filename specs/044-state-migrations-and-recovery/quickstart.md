# Quickstart: State Migrations and Recovery

1. Inspect without mutation: `uv run --package wright-data-vault wright-db --json status --database /path/to/wright.db`.
2. Create and validate a snapshot: `uv run --package wright-data-vault wright-db backup --database /path/to/wright.db --output-dir /path/to/backups`.
3. Upgrade explicitly: `uv run --package wright-data-vault wright-db upgrade --database /path/to/wright.db --backup-dir /path/to/backups`.
4. Repeat status and upgrade; verify current version, no pending changes, and an empty applied list.
5. Restore a verified pre-upgrade snapshot: `uv run --package wright-data-vault wright-db restore --database /path/to/wright.db --manifest /path/to/backups/BACKUP.manifest.json`.
6. Attempt restore from a modified snapshot/manifest and verify refusal leaves the active database digest unchanged.
7. Run application startup against fresh, current, partial legacy, corrupt, future-version, and interrupted fixtures. Only fresh/current/supported legacy state may become ready.
8. Verify catalog rows reconcile after migration but are not modified by direct `wright-db upgrade`.
9. Run focused data-vault/API suites, leak scan, distribution dry run, and `scripts/check-dev-merge.sh`.

Rollback is snapshot-based: stop Wright, use `wright-db restore` with the verified pre-upgrade manifest, then run the older release's status/startup checks. Never copy a live WAL database or edit the migration ledger manually.
