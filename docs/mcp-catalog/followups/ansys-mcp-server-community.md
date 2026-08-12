# Ansys MCP Server Community Follow-Up

Catalog ID: `ansys-mcp-server-community`

Source: https://pypi.org/project/ansys-mcp-server/

Validation status: `non_working` / startup failed in GB10 local preflight

## Reproduction

GB10 Linux ARM64 host:

```bash
uvx --from ansys-mcp-server ansys-mcp-server --help
uvx --python 3.12 --from ansys-mcp-server ansys-mcp-server --help
```

Observed result on Python 3.13 and Python 3.12:

```text
ImportError: cannot import name 'InitializationCapabilities' from 'mcp.server.models'
```

## Evidence

- Package dependencies installed successfully.
- The console script imports `ansys_mcp_server.server`.
- Import fails before `initialize`, `notifications/initialized`, or
  `tools/list` can run.
- The failure repeated with Python 3.12, so it is not only a Python 3.13
  compatibility issue.

## Requested Upstream Fix

Either:

- Pin the Python MCP SDK to a version that still exports
  `mcp.server.models.InitializationCapabilities`, or
- Update the server implementation to the current MCP SDK API.

## Remaining Validation

After startup is fixed, rerun:

- `initialize`
- `notifications/initialized`
- `tools/list`
- a safe status/no-op tool without a licensed solver

Full backend validation still requires whichever licensed Ansys products the
selected tool path uses.
