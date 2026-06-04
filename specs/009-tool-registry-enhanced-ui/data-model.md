# Data Model: Enhanced Tool Registry UI

**Feature**: `009-tool-registry-enhanced-ui`
**Date**: 2026-06-04

---

## Entity: McpServer (Extended)

Represents a registered MCP server entry in the catalog. Persisted in `mcp_servers` SQLite table.

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_id` | string (UUID) | Yes | Primary key |
| `name` | string | Yes | Display name of the server |
| `type` | enum: `stdio` \| `sse` \| `webmcp` | Yes | Transport/deployment type. `stdio` = Local, `sse`/`webmcp` = Network |
| `command` | string \| string[] | Conditional | CLI command for `stdio`; connection URL for `sse` |
| `is_active` | boolean | Yes | Whether the server subprocess/connection is currently running |
| `is_installed` | boolean | Yes | Whether the server has been installed/connected |
| `status` | enum: `active` \| `inactive` \| `error` | Yes | Current runtime status |
| `error_message` | string \| null | No | Last error message if status is `error` |
| `category` | string | Yes | Functional category (e.g., `simulation`, `cad`, `utilities`) |
| `created_at` | integer (Unix timestamp) | Yes | Row creation time |
| `updated_at` | integer (Unix timestamp) | Yes | Last update time |
| `image_url` | string \| null | **NEW** | Direct URL to the server logo/avatar image |
| `description` | string \| null | **NEW** | Human-readable description of the server and what installing it means |
| `source_url` | string \| null | **NEW** | Origin URL (GitHub repo, npm page). Used to derive `image_url` as fallback |
| `installed_version` | string \| null | **NEW** | Version string of the installed package (e.g., `"1.2.3"`) |

### Deployment Type Classification

| `type` value | Deployment Category | UI Label | Actions |
|--------------|--------------------|-----------|---------| 
| `stdio` | Local | ⬡ Local (amber badge) | Install / Check for Updates / Update / Uninstall |
| `sse` | Network | ⚡ Network (cyan badge) | Connect / Disconnect |
| `webmcp` | Network | ⚡ Network (cyan badge) | Connect / Disconnect |

### State Transitions

```
Not Installed → [Install/Connect] → Installed (inactive) → [Start] → Active
Active → [Stop] → Installed (inactive)
Installed (inactive) → [Uninstall/Disconnect] → Not Installed
Installed → [Check for Updates] → Update Available → [Update] → Installed (new version)
```

### Validation Rules

- `name`: non-empty, max 100 chars, unique per DB
- `type`: must be one of `stdio`, `sse`, `webmcp`
- `image_url`: must be a valid URL if provided (validated on frontend with try/catch URL constructor)
- `source_url`: must be a valid URL if provided
- `installed_version`: semver string (e.g., `"1.2.3"`) or `null`
- `description`: max 500 chars

---

## Entity: VersionCheckResult (Runtime, not persisted)

Returned by `GET /api/mcp/servers/{id}/version-check`. Not stored in DB (version checks are always on-demand).

| Field | Type | Description |
|-------|------|-------------|
| `server_id` | string | ID of the checked server |
| `installed` | string \| null | Currently installed version |
| `latest` | string \| null | Latest available version |
| `update_available` | boolean | `true` if `latest > installed` |
| `error` | string \| null | Error message if check failed (e.g., `"unsupported_package_manager"`, `"timeout"`) |

---

## SQLite Schema Migration

**Migration is idempotent** — each `ALTER TABLE` is wrapped in `try/except OperationalError` to handle the case where the column already exists.

```sql
ALTER TABLE mcp_servers ADD COLUMN image_url TEXT DEFAULT NULL;
ALTER TABLE mcp_servers ADD COLUMN description TEXT DEFAULT NULL;
ALTER TABLE mcp_servers ADD COLUMN source_url TEXT DEFAULT NULL;
ALTER TABLE mcp_servers ADD COLUMN installed_version TEXT DEFAULT NULL;
```

Applied via the `ensure_migrations()` function called from `_get_conn()` or at app startup.

---

## Seeded Server Enrichment

The existing CalculiX Simulation and OpenSCAD Geometry seeded entries (written during DB initialization) will be updated to include `image_url`, `description`, and `source_url` values. This is a one-time data migration handled in the seed logic.
