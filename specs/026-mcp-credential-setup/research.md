# Research: MCP Credential & Secret Setup

**Feature**: 026-mcp-credential-setup | **Date**: 2026-06-12

## Research Tasks

### 1. Jarvis OnShape MCP Integration Requirements

**Decision**: Use `uv run --with jarvis-onshape-mcp onshape-mcp` as the stdio command.

**Rationale**: The OnShape MCP is a Python package published on PyPI (via `uv`). It uses stdio transport and requires two environment variables: `ONSHAPE_API_KEY` (access key) and `ONSHAPE_API_SECRET` (secret key). The `uv run --with` pattern is consistent with how other MCP servers in the Wright catalog are installed (e.g., OpenSCAD uses `uv run --with git+...`). This avoids cloning the repository locally.

**Alternatives considered**:
- **Git clone + local install**: Too heavyweight for a catalog entry. Requires managing a local clone and venv.
- **`uvx onshape-mcp`**: Would work but `uv run --with` is more explicit about the package name vs. entry point.

### 2. Secure Local Secret Storage Approach

**Decision**: Use a JSON file at `~/.config/wright/mcp-secrets.json` with `0600` permissions and `fcntl.flock` advisory locking.

**Rationale**: 
- **File-based storage** is the simplest approach that satisfies the offline-first mandate (Constitution §1) and zero-server-databases requirement (Constitution §3).
- **`~/.config/wright/`** follows the XDG Base Directory specification for user configuration on Linux, which is the target platform.
- **`0600` permissions** (owner read/write only) prevent other system users from reading secrets.
- **`fcntl.flock`** provides POSIX advisory locking to prevent concurrent write corruption from multiple API workers.

**Alternatives considered**:
- **OS Keychain (keyring library)**: Would provide stronger encryption-at-rest, but adds a new dependency (`keyring`), requires D-Bus on Linux (not always available in containers), and violates the zero-external-dependency constraint. The Docker container use case makes this impractical.
- **Encrypted file (Fernet/AES)**: Adds complexity. The encryption key itself needs to be stored somewhere, creating a turtles-all-the-way-down problem. File permissions are sufficient for a single-user local appliance.
- **SQLite column with encryption**: Violates the spec requirement that secrets never appear in the database.
- **Environment variables only**: Not practical for multiple MCP servers with different credentials. Users would need to manage env vars manually.

### 3. Env Var Metadata Schema Design

**Decision**: Store `env_vars` as a JSON array of `EnvVarDefinition` objects in the `mcp_servers.env_vars` column.

**Rationale**: The existing `env_vars: dict[str, str]` field conflates metadata (variable name, whether it's required) with values (the actual secret). The new structured format separates these concerns:
- **Database stores metadata only**: `[{"name": "API_KEY", "label": "API Key", "required": true, "secret": true}]`
- **Secrets file stores values only**: `{"server-id": {"API_KEY": "actual-value"}}`
- **At runtime**, the engine merges metadata + values when starting a server.

**Backward compatibility**: The deserialization layer (`_row_to_server()`) will detect whether `env_vars` is a dict (old format) or list (new format) and handle both. Old-format entries without explicit metadata will be treated as non-required, non-secret environment variables.

**Alternatives considered**:
- **Separate `env_var_definitions` column**: Adds schema complexity without benefit. The existing `env_vars` column can hold the evolved format.
- **Separate `env_var_definitions` table**: Violates YAGNI. The data is small and tied 1:1 to servers.

### 4. API Credential Flow

**Decision**: Three new endpoints under `/api/mcp/servers/{server_id}/credentials`.

**Rationale**: Keeps credential management RESTful and scoped to individual servers. The `PUT` verb for save (idempotent upsert) is more appropriate than `POST` since saving credentials for the same server should overwrite, not create duplicates.

**Flow**:
1. UI calls `GET /servers/{server_id}/credentials` → gets env var definitions + configured flags
2. User fills in values in the UI
3. UI calls `PUT /servers/{server_id}/credentials` with `{ credentials: { "KEY": "value" } }`
4. Backend writes to `~/.config/wright/mcp-secrets.json`
5. Backend returns updated configured flags (never values)
6. User clicks Install → backend reads secrets from file and passes to `StdioRunner`

### 5. Frontend Credential UI Pattern

**Decision**: Add a collapsible credential configuration panel within the existing `ToolCard` component.

**Rationale**: 
- Keeps the UI change minimal — no new pages or modals needed.
- Follows the existing collapsible pattern used for "Show connection details" and "Configure Workspaces."
- The credential form appears below the server description and above the workspace enablement section.
- Input fields use `type="password"` for secret variables and `type="text"` for non-secret ones.

**Alternatives considered**:
- **Modal dialog**: More disruptive to the user flow. The collapsible panel is consistent with the existing UI patterns.
- **Separate settings page**: Over-engineered for what is a per-server configuration.
- **First-run wizard**: Would be needed if we supported many credential types, but for now the inline panel is sufficient.
