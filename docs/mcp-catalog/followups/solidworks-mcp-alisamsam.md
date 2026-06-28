# SolidWorks MCP by alisamsam Follow-Up

Catalog ID: `solidworks-mcp-alisamsam`

Source: https://github.com/alisamsam/solidworks-mcp

Validation status: `non_working` / `failed`

Validated source commit: `ee8f42a1a919af5e0fa8d1dcd24270c9983ce027`

## Reproduction

Clean Intel Ubuntu container:

```bash
docker run --rm --platform linux/amd64 ubuntu:24.04 bash
apt-get update
apt-get install -y git curl ca-certificates python3 python3-venv python3-pip
git clone --depth 1 https://github.com/alisamsam/solidworks-mcp /tmp/solidworks-mcp-alisamsam
cd /tmp/solidworks-mcp-alisamsam
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Observed install result:

```text
ERROR: Could not find a version that satisfies the requirement asyncio-compat>=0.1.0
ERROR: No matching distribution found for asyncio-compat>=0.1.0
```

After installing only available runtime dependencies:

```bash
pip install mcp python-dotenv
python solidworks_mcp_server.py
```

Observed runtime result:

```text
ModuleNotFoundError: No module named 'win32com'
```

## Evidence

- `pip index versions asyncio-compat` returned no matching distribution.
- `pip index versions pywin32` returned no matching distribution on Linux.
- No upstream tests were present in the checkout.
- MCP `initialize`, `notifications/initialized`, and `tools/list` could not be
  called because the server cannot start.

## Requested Upstream Fix

- Remove or replace `asyncio-compat>=0.1.0` unless a real published package is
  intended.
- Mark `pywin32` as Windows-only, for example with a platform marker.
- Delay `win32com` imports until Windows/SolidWorks tools are invoked, or return
  a clear startup diagnostic on unsupported platforms.

## Remaining Validation

After dependencies are fixed, validate on a Windows/SolidWorks host with:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `get_solidworks_info`
- `connect_solidworks`
- one safe document or metadata operation
