# Validation Contract

## Request

Validation may run for one server or the current catalog:

```json
{
  "server_id": "blender_mcp_ahujasid",
  "environment": "ubuntu-linux-x64-container",
  "mode": "dry_run"
}
```

## Response

```json
{
  "server_id": "blender_mcp_ahujasid",
  "environment": "ubuntu-linux-x64-container",
  "status": "dependency_missing",
  "installability_tier": "might_work",
  "message": "Package probe is available, but Blender host software is not installed.",
  "missing_dependencies": ["Blender"],
  "diagnostics": "secret-redacted validation summary",
  "follow_up_url": null
}
```

## Status Rules

- `passed`: Install/probe and MCP smoke check succeeded.
- `dependency_missing`: Package or command path is plausible, but host software, credentials, license, GUI, or hardware is unavailable.
- `blocked`: Entry lacks verified URL/install data or is intentionally not auto-installable.
- `failed`: Probe ran and failed for reasons not explained by declared dependencies.
- `skipped`: Entry is out of scope for the current validation mode.
- `not_tested`: No validation has run.

## Safety Rules

- Validation must not supply real secrets.
- Machine-control entries run only in simulation/read-only classification during this sprint.
- High-risk entries may run help/version checks but must not perform writes, cloud uploads, code execution inside host apps, or machine actions.
