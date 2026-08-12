# COMSOL Multiphysics MCP by Suzy-Sa Follow-Up

Catalog ID: `comsol-multiphysics-mcp-suzysa`

Source: https://github.com/Suzy-Sa/COMSOL-Multiphysics-MCP

Validation status: package tests passed, MCP startup failed in GB10 local
preflight

Validated source commit: `3735fb3276ec6ad44163a55763dad45932367ffe`

## Reproduction

GB10 Linux ARM64 host:

```bash
git clone --depth 1 https://github.com/Suzy-Sa/COMSOL-Multiphysics-MCP /tmp/comsol-mcp-suzysa
cd /tmp/comsol-mcp-suzysa
uv run pytest -q
uv run python -m comsol_agent_mcp.server
```

Observed test result:

```text
76 passed
```

Observed MCP startup result:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

## Evidence

- The package can install on GB10/Linux ARM64.
- The upstream tests pass, but they do not import the MCP entrypoint.
- The server imports `from mcp.server.fastmcp import FastMCP`, which is not
  available in the resolved MCP SDK version.
- MCP `initialize`, `notifications/initialized`, and `tools/list` could not be
  called because startup exits before stdio is available.

## Requested Upstream Fix

Either:

- Pin `mcp` to a version that still provides `mcp.server.fastmcp`, or
- Migrate `src/comsol_agent_mcp/server.py` to the current FastMCP package/API.

## Remaining Validation

After stdio startup is fixed, rerun:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `backend_status` or equivalent safe no-license status call

Licensed COMSOL/mph validation should wait until the MCP entrypoint starts
cleanly.
