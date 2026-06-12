# Implementation Plan: MCP Credential & Secret Setup

**Branch**: `026-mcp-credential-setup` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/026-mcp-credential-setup/spec.md`

## Summary

Add credential configuration support to the MCP Tool Registry so that MCP servers requiring authentication (API keys, secrets, tokens) can be set up through the Wright UI. Secret values are stored in a local user config file (`~/.config/wright/mcp-secrets.json`) outside the repository — never in the database, API responses, or version control. The Jarvis OnShape MCP is added to the engineering catalog as the reference implementation and validation case.

## Technical Context

**Language/Version**: Python 3.13 (FastAPI backend), React 19 (TypeScript frontend)

**Primary Dependencies**: `tool_registry` package (existing), `fastapi`, `pydantic`, `structlog`; no new external dependencies needed

**Storage**: SQLite (`state.db`) — `mcp_servers.env_vars` column evolves to store variable definitions (metadata only, not secret values). New file: `~/.config/wright/mcp-secrets.json` for secret values.

**Testing**: pytest (backend unit tests), Vitest (frontend component tests), Playwright (UI integration tests)

**Target Platform**: Dell GB10 host (arm64/aarch64, Ubuntu 24.04), Docker container

**Project Type**: Modular Monorepo Web Application

**Performance Goals**: Credential save/load < 100ms, no impact on MCP server start latency

**Constraints**: Offline-first, adapter pattern (Constitution §2), structured JSON logging (Constitution §7), secrets never in repo or API responses

**Scale/Scope**: ~10 files modified, ~2 files created, 0 new dependencies

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **FastAPI strict typing (§1)**: YES. New API endpoints use Pydantic models. All credential request/response schemas are strictly typed.
- **Agent Abstraction / Adapter Pattern (§2)**: YES. No changes to `BaseAgentEngine`. The credential system operates at the MCP server registry level, below the agent abstraction.
- **Offline-First Mandate (§1)**: YES. Secrets stored locally in `~/.config/wright/mcp-secrets.json`. No external cloud dependency.
- **Zero-Server Databases (§3)**: YES. SQLite remains sole DB. Secrets use a local JSON file (not a database server).
- **Modular Monorepo boundaries (§1)**: YES. Changes span `packages/tool_registry`, `apps/api`, and `apps/web`. Each package boundary is respected.
- **Structured JSON Logging (§7)**: YES. All new code uses `structlog`. Secret values are never logged.
- **Security / Local Auth (§4)**: YES. Secrets stored with `0600` file permissions. Never transmitted via API responses.
- **Test IDs (§6)**: YES. New UI components include `data-testid` attributes.

## Project Structure

### Documentation (this feature)

```text
specs/026-mcp-credential-setup/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research findings
├── data-model.md        # Credential store schema & API contracts
├── quickstart.md        # Manual verification guide
└── checklists/
    └── requirements.md  # Spec quality validation checklist
```

### Source Code

```text
packages/tool_registry/src/tool_registry/
├── models.py                   # [MODIFY] Evolve env_vars to structured EnvVarDefinition list
├── secrets.py                  # [NEW] Credential store: read/write/delete from ~/.config/wright/mcp-secrets.json
├── manager.py                  # [MODIFY] Merge secrets from credential store at server start
└── db.py                       # [MODIFY] Update env_vars serialization for structured metadata

apps/api/src/api/
├── routers/
│   └── mcp.py                  # [MODIFY] Add credential endpoints, mask secrets in responses
├── database/
│   └── migrate.py              # [MODIFY] Add Jarvis OnShape MCP to catalog with env_var definitions

apps/web/src/
├── services/
│   └── mcp-service.ts          # [MODIFY] Add credential API methods, update McpServer interface
├── components/tools/
│   └── ToolCard.tsx             # [MODIFY] Add credential configuration panel
└── store/
    └── tools.tsx                # [MODIFY] Add credential actions

apps/api/tests/
├── test_mcp_credentials.py     # [NEW] Unit tests for credential store and API endpoints
```

**Structure Decision**: Monorepo Web Application layout. The new `secrets.py` module is added to `packages/tool_registry` to keep credential management within the tool registry boundary. The credential store is a file-system utility, not a database concern.

---

## Proposed Changes

### Component 0: Credential Store Module

#### [NEW] [secrets.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/secrets.py)

New module providing secure local credential storage:

- **`SECRETS_PATH`**: `~/.config/wright/mcp-secrets.json` (configurable via `WRIGHT_SECRETS_PATH` env var for testing)
- **`read_secrets(server_id: str) -> dict[str, str]`**: Read credentials for a specific server from the secrets file. Returns empty dict if file doesn't exist or server has no saved credentials.
- **`write_secrets(server_id: str, credentials: dict[str, str]) -> None`**: Write/update credentials for a server. Creates parent directory and file if needed. Sets file permissions to `0o600`. Uses file-level advisory locking (`fcntl.flock`) to prevent concurrent write corruption.
- **`delete_secrets(server_id: str) -> None`**: Remove a server's credentials from the secrets file.
- **`has_credentials(server_id: str, required_vars: list[str]) -> bool`**: Check if all required env vars for a server are configured.
- All operations log via `structlog` — secret values are never logged.

---

### Component 1: Model Evolution

#### [MODIFY] [models.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/models.py)

Evolve the `env_vars` field from `dict[str, str]` to a structured metadata schema:

- **Add** `EnvVarDefinition` Pydantic model:
  ```python
  class EnvVarDefinition(BaseModel):
      name: str           # Variable name (e.g., "ONSHAPE_API_KEY")
      label: str          # Human-readable label (e.g., "Access Key")
      description: str = ""  # Help text
      required: bool = True
      secret: bool = False   # If True, value should be masked in UI
  ```
- **Change** `McpServer.env_vars` type from `Optional[dict[str, str]]` to `Optional[list[EnvVarDefinition]]`
- **Change** `McpServerCreate.env_vars` type similarly
- **Add** `credentials_configured: Optional[dict[str, bool]]` field to `McpServer` — populated dynamically by the API to indicate which env vars have saved values (never includes actual values)

#### [MODIFY] [db.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/db.py)

- **Update** `_row_to_server()` to deserialize `env_vars` JSON as `list[EnvVarDefinition]` (with backward compatibility for old `dict[str, str]` format)
- **Update** `insert_server()` and `update_server()` to serialize `list[EnvVarDefinition]` as JSON

---

### Component 2: Engine Integration

#### [MODIFY] [manager.py](file:///home/burhop/repos/wright/packages/tool_registry/src/tool_registry/manager.py)

Update `start_server()` to merge credentials from the secrets store:

- **Before creating `StdioRunner`**: Call `secrets.read_secrets(server_id)` to load saved credentials
- **Merge** saved credentials into the `env_vars` dict that is passed to `StdioRunner(command, env=env_vars)`
- **Validation**: If the server has required env var definitions and any required credentials are missing, raise a descriptive `ValueError` ("Server 'X' requires credentials: ONSHAPE_API_KEY, ONSHAPE_API_SECRET. Configure them via the UI before activating.")
- **Keep** existing env_vars behavior for non-credential variables (e.g., `FREECAD_PATH`)

---

### Component 3: API Endpoints

#### [MODIFY] [mcp.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/mcp.py)

Add credential management endpoints and sanitize existing responses:

- **Add** `GET /servers/{server_id}/credentials` — Returns the server's env var definitions and which ones are configured (boolean flags, never values). Response model: `CredentialStatusResponse`.
- **Add** `PUT /servers/{server_id}/credentials` — Accepts credential values and saves them to the secrets store. Request model: `SaveCredentialsRequest { credentials: dict[str, str] }`. Response: `CredentialStatusResponse`.
- **Add** `DELETE /servers/{server_id}/credentials` — Removes all saved credentials for a server.
- **Update** `list_servers()` — Add `credentials_configured` field to each server response, indicating which env vars have saved values (call `secrets.has_credentials()` for each server with env_var definitions).
- **Update** `delete_server_endpoint()` — Also call `secrets.delete_secrets(server_id)` to clean up credentials when a server is removed.
- **Update** `install_server_endpoint()` — Before starting the server, validate that all required credentials are configured. Return HTTP 400 with descriptive error if not.

---

### Component 4: Catalog Update

#### [MODIFY] [migrate.py](file:///home/burhop/repos/wright/apps/api/src/api/database/migrate.py)

Add the Jarvis OnShape MCP to the engineering catalog:

- **Add** new catalog entry:
  ```python
  {
      "server_id": "jarvis-onshape-mcp",
      "name": "Jarvis OnShape MCP",
      "type": "stdio",
      "command": json.dumps(["uv", "run", "--with", "jarvis-onshape-mcp", "onshape-mcp"]),
      "category": "cad",
      "image_url": "https://avatars.githubusercontent.com/u/6536550?s=64",
      "description": "AI copilot for Onshape CAD. 60+ tools: parametric sketches, extrudes, fillets, assemblies, Variable Studios, FeatureScript, and multi-view rendering with vision feedback.",
      "source_url": "https://github.com/ReshefElisha/jarvis-onshape-mcp",
      "env_vars": json.dumps([
          {"name": "ONSHAPE_API_KEY", "label": "Access Key", "description": "Onshape API access key from dev-portal.onshape.com", "required": True, "secret": False},
          {"name": "ONSHAPE_API_SECRET", "label": "Secret Key", "description": "Onshape API secret key (shown once at creation)", "required": True, "secret": True}
      ]),
  }
  ```
- **Update** the catalog seed loop to include `env_vars` in `INSERT OR IGNORE` and `UPDATE` statements

---

### Component 5: Frontend Updates

#### [MODIFY] [mcp-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/mcp-service.ts)

- **Add** `EnvVarDefinition` interface matching the backend model
- **Update** `McpServer` interface to include `env_vars?: EnvVarDefinition[]` and `credentials_configured?: Record<string, boolean>`
- **Add** `getCredentialStatus(serverId: string): Promise<CredentialStatusResponse>`
- **Add** `saveCredentials(serverId: string, credentials: Record<string, string>): Promise<CredentialStatusResponse>`
- **Add** `deleteCredentials(serverId: string): Promise<void>`

#### [MODIFY] [ToolCard.tsx](file:///home/burhop/repos/wright/apps/web/src/components/tools/ToolCard.tsx)

Add a credential configuration panel:

- **Add** "Configure Credentials" button — visible when server has `env_vars` definitions
- **Add** collapsible credential form panel with:
  - Labeled input field for each env var definition
  - Password-type inputs for variables marked as `secret: true`
  - "Required" indicator for required variables
  - "Save Credentials" button that calls `saveCredentials()`
  - "Clear Credentials" button
  - Status indicators showing which variables are configured (green check / red X)
- **Add** "Requires Configuration" badge on server card when required credentials are not configured
- **Block** install button when required credentials are missing, showing a tooltip: "Configure credentials before installing"
- All new elements include `data-testid` attributes

#### [MODIFY] [tools.tsx](file:///home/burhop/repos/wright/apps/web/src/store/tools.tsx)

- **Add** `saveCredentials` and `getCredentialStatus` actions
- **Update** `fetchServersAndTools` to include credential status in server state

---

### Component 6: Tests

#### [NEW] [test_mcp_credentials.py](file:///home/burhop/repos/wright/apps/api/tests/test_mcp_credentials.py)

- **Test** secrets module: write, read, delete, file permissions, missing file handling
- **Test** credential API endpoints: save, get status, delete, masked responses
- **Test** install blocking: server with required credentials not configured → HTTP 400
- **Test** server deletion cascades to credential cleanup
- **Test** McpEngine merges credentials from secrets store at server start
- **Test** OnShape MCP catalog entry exists with correct env_var definitions

---

## Verification Plan

### Automated Tests

```bash
# Unit tests for credential store and API
uv run pytest apps/api/tests/test_mcp_credentials.py -v

# Existing MCP API tests (regression)
uv run pytest apps/api/tests/test_mcp_api.py -v

# Full test suite
uv run pytest apps/api/tests/ -v

# Frontend component tests
npm test --workspace=apps/web
```

### Manual Verification

1. Run database migration to seed the OnShape MCP catalog entry
2. Open the Tool Registry UI
3. Find "Jarvis OnShape MCP" in the catalog
4. Click "Configure Credentials" → verify input fields appear for Access Key and Secret Key
5. Enter credentials and save → verify green checkmarks appear
6. Install the server → verify it starts and tools are discovered
7. Verify `~/.config/wright/mcp-secrets.json` contains the credentials with `0600` permissions
8. Verify `GET /api/mcp/servers` does NOT return credential values
9. Delete the server → verify credentials are removed from the secrets file

## Complexity Tracking

*No complexity violations present. No exceptions required.*
