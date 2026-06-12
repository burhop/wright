# Quickstart: MCP Credential & Secret Setup

**Feature**: 026-mcp-credential-setup | **Date**: 2026-06-12

## Prerequisites

- Wright API running locally (`uv run python -m api`)
- Wright Web UI running (`npm run dev --workspace=apps/web`)
- Database migrated (`uv run python -m api.database.migrate`)

## Verification Steps

### 1. Verify OnShape MCP Catalog Entry

```bash
# Check the database for the Jarvis OnShape MCP entry
sqlite3 apps/api/state.db "SELECT server_id, name, env_vars FROM mcp_servers WHERE server_id = 'jarvis-onshape-mcp';"
```

Expected: Entry exists with `env_vars` containing ONSHAPE_API_KEY and ONSHAPE_API_SECRET definitions.

### 2. Verify Credential API Endpoints

```bash
# Get credential status (should show unconfigured initially)
curl -s http://127.0.0.1:8000/api/mcp/servers/jarvis-onshape-mcp/credentials | python3 -m json.tool

# Save credentials
curl -s -X PUT http://127.0.0.1:8000/api/mcp/servers/jarvis-onshape-mcp/credentials \
  -H "Content-Type: application/json" \
  -d '{"credentials": {"ONSHAPE_API_KEY": "test-key", "ONSHAPE_API_SECRET": "test-secret"}}' | python3 -m json.tool

# Verify configured status
curl -s http://127.0.0.1:8000/api/mcp/servers/jarvis-onshape-mcp/credentials | python3 -m json.tool

# Verify secrets NOT in API response
curl -s http://127.0.0.1:8000/api/mcp/servers | python3 -m json.tool | grep -i "test-secret"
# Expected: no output (secrets are never in API responses)
```

### 3. Verify Secrets File

```bash
# Check file exists and has correct permissions
ls -la ~/.config/wright/mcp-secrets.json
# Expected: -rw------- (0600)

# Check contents (should contain the saved credentials)
cat ~/.config/wright/mcp-secrets.json
```

### 4. Verify UI Credential Panel

1. Open http://localhost:5173 → navigate to Tool Registry
2. Find "Jarvis OnShape MCP" card
3. Verify "Configure Credentials" button is visible
4. Click it → verify input fields for "Access Key" and "Secret Key" appear
5. Secret Key field should use password masking
6. Enter values and click "Save Credentials"
7. Verify green checkmarks appear for configured variables
8. Verify "Install" button is now enabled

### 5. Verify OnShape MCP Start (requires real credentials)

1. Configure real OnShape credentials via the UI
2. Click "Install" on the OnShape MCP card
3. Verify server starts and shows "active" status
4. Verify tools are discovered (should show 60+ OnShape tools)

### 6. Verify Server Deletion Cleanup

```bash
# Delete the server and verify credentials are removed
curl -s -X DELETE http://127.0.0.1:8000/api/mcp/servers/jarvis-onshape-mcp
cat ~/.config/wright/mcp-secrets.json
# Expected: no entry for "jarvis-onshape-mcp"
```

## Running Tests

```bash
# Credential-specific tests
uv run pytest apps/api/tests/test_mcp_credentials.py -v

# Full regression suite
uv run pytest apps/api/tests/ -v
```
