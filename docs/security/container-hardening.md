# Container Hardening and Volume Migration

The default Wright appliance runs as `agent` without sudo, drops all Linux
capabilities, enables `no-new-privileges`, and uses a read-only root filesystem.
Writable tmpfs mounts are limited to `/tmp` and the agent cache.
`WRIGHT_API_TOKEN` is required and unique; the internal Hermes key is generated
per start unless explicitly supplied.

Only these named volumes persist: `wright_data`, `wright_workspaces`,
`wright_config`, `wright_hermes`, and `wright_logs`. System directories such as
`/etc`, `/opt`, `/usr/local`, `/var/lib`, and the entire `/home` tree are never
persisted by the default deployment.

## Upgrade from pre-043 volumes

1. Stop the old appliance and back up every old `wright_*` volume.
2. Start the old image with `docker-compose.legacy.yml` only long enough to
   export Wright database, workspace, configuration, Hermes, and log data.
3. Start the new image with the default Compose file and a unique token.
4. Import only documented Wright-owned data into the new narrow volumes.
5. Run health, workspace, credential-status, Git, and MCP checks.
6. Quarantine old volumes until verified, then remove them per retention policy.

The legacy file is migration-only for one release. It disables the new
read-only/privilege restrictions to mount old layouts and must not be used for
normal operation.

## Rollback

Stop the new appliance, retain its narrow volumes, and restart the previous
image with the backed-up legacy volumes. Never attach new and old writable
layouts to two running containers simultaneously.
