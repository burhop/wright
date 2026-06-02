# Data Model & Schema: OpenSCAD MCP & 3D Visualization

## 1. Database Seeding

We do not modify the existing SQLite database schemas for `mcp_servers` or `mcp_tools` defined in `specs/003-mcp-tool-registry/data-model.md`.
Instead, we add a seed block to `apps/api/src/api/database/migrate.py` to pre-register the OpenSCAD MCP server:

```sql
INSERT INTO mcp_servers (server_id, name, type, command, is_active, status, category, created_at, updated_at)
VALUES (
    'openscad-mcp-server',
    'OpenSCAD Geometry',
    'stdio',
    '["uv", "run", "--with", "git+https://github.com/quellant/openscad-mcp.git", "openscad-mcp"]',
    0,
    'inactive',
    'cad',
    strftime('%s','now'),
    strftime('%s','now')
);
```

---

## 2. API Workspace Models

We define the data shapes returned by the new workspace file endpoints in `apps/api`. These structures are used by Pydantic for API contract serialization.

### WorkspaceNode
Represents a node in the hierarchical file browser tree.
- `name` (String): File or directory basename.
- `path` (String): Project-relative path.
- `type` (Enum): `file` | `directory`.
- `size` (Optional[Integer]): Size in bytes (null for directories).
- `last_modified` (Optional[Integer]): Last modified unix timestamp.
- `children` (Optional[List[WorkspaceNode]]): Child nodes (null for files).

### FileMetadataResponse
Represents metadata returned when checking for updates.
- `path` (String): Project-relative path.
- `size` (Integer): Size in bytes.
- `last_modified` (Integer): Last modified unix timestamp.
