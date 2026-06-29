# SolidWorks Python COM Follow-Up

Catalog ID: `solidworks-mcp-python`

Source: https://github.com/andrewbartels1/SolidworksMCP-python

Validation status: `non_working` / `failed`

Validated source commit: `f0858a7b9cf8cb9a7838ddfaa91a706ef6439cab`

## Reproduction

Clean Intel Ubuntu container:

```bash
docker run --rm --platform linux/amd64 ubuntu:24.04 bash
apt-get update
apt-get install -y git curl ca-certificates python3 python3-venv python3-pip
git clone --depth 1 https://github.com/andrewbartels1/SolidworksMCP-python /tmp/solidworks-mcp-python
cd /tmp/solidworks-mcp-python
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e ".[test]"
python -m solidworks_mcp.server
```

Observed result:

```text
ModuleNotFoundError: No module named 'pydantic_ai.toolsets.fastmcp'
```

`solidworks-mcp --help` fails with the same import error because the console
entry point imports `solidworks_mcp.server`.

## Evidence

- `solidworks-mcp-python` version: 1.0.0
- `pydantic-ai` version resolved by the declared dependency range: 2.0.0
- `fastmcp` version: 3.4.2
- `mcp` version: 1.28.1
- Windows-only dependencies `pywin32`, `pywin32-ctypes`, and `comtypes` were
  correctly skipped on Linux due platform markers.
- Focused upstream tests failed during import before test execution reached MCP
  behavior.
- MCP `initialize`, `notifications/initialized`, and `tools/list` could not be
  called because server startup fails before stdio is available.

## Requested Upstream Fix

Either:

- Pin `pydantic-ai` to a version that still provides
  `pydantic_ai.toolsets.fastmcp.FastMCPToolset`, or
- Update `src/solidworks_mcp/server.py` to the current PydanticAI/FastMCP API.

After that fix lands, rerun the Ubuntu install/start check to confirm the server
can at least start in mock/development mode.

## Remaining Validation

Full CAD validation still requires:

- Windows 10/11
- Python from python.org
- SolidWorks installed and launched at least once
- Windows COM automation available

Once the Python dependency mismatch is fixed, validate on a Windows/SolidWorks
host with:

- `initialize`
- `notifications/initialized`
- `tools/list`
- one safe/status tool
- one backend-touching SolidWorks COM tool
