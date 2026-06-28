# Investigate MCP Server: autodesk-fusion-mcp-python

## Server ID

autodesk-fusion-mcp-python

## Source URL

https://github.com/sockcymbal/autodesk-fusion-mcp-python

## Verification State

community_mcp

## Current Installability Tier

non_working

## Environment

ubuntu-linux-x64-container

## Observed Failure

Clean Intel Ubuntu validation cloned commit `a3398ac5c76baa252240f301167a4cba2fe6f5b8`.

The repository installed with:

```bash
python3 -m venv /tmp/fusion-python-venv
. /tmp/fusion-python-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

There are no upstream tests. The seeded command `python main.py` is stale because the repository has no `main.py`; the MCP script is `fusion_mcp.py`.

Without APS variables, startup fails before MCP initialization:

```text
KeyError: 'APS_CLIENT_ID'
```

With dummy `APS_CLIENT_ID`, `APS_CLIENT_SECRET`, and `FUSION_ACTIVITY_ID`, MCP initialized as serverInfo `fusion` version `1.28.1` and listed one tool: `generate_cube`.

Calling `generate_cube` failed before any APS request:

```text
'BasicAuth' object has no attribute 'auth_header'
```

The traceback points to:

```python
headers = httpx.BasicAuth(CLIENT_ID, CLIENT_SECRET).auth_header
```

## Reproduction Commands

```bash
git clone https://github.com/sockcymbal/autodesk-fusion-mcp-python
cd autodesk-fusion-mcp-python
python3 -m venv /tmp/fusion-python-venv
. /tmp/fusion-python-venv/bin/activate
pip install -r requirements.txt
APS_CLIENT_ID=dummy APS_CLIENT_SECRET=dummy FUSION_ACTIVITY_ID=dummy.activity+prod python fusion_mcp.py
```

MCP call:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "generate_cube",
    "arguments": {"edge_mm": 20}
  }
}
```

## Expected Behavior

With dummy APS credentials, `generate_cube` should at least reach Autodesk APS authentication and return a clear 401/auth diagnostic. With valid credentials and a registered activity, it should submit a Fusion Design Automation work item or return a clear activity/configuration diagnostic.

## Missing Context Or Dependencies

- Valid `APS_CLIENT_ID`
- Valid `APS_CLIENT_SECRET`
- Registered `FUSION_ACTIVITY_ID`
- Fusion 360 / LiveCube only for the separate local add-in workflow

The current failure occurs before those dependencies can be fully tested.

## Suggested Next Action

Update `get_oauth_token()` to use a valid Basic Auth header path for current `httpx`, for example by constructing the header manually with base64 encoding or by using an `httpx.AsyncClient(auth=(CLIENT_ID, CLIENT_SECRET))` request shape. Also consider delaying required env-var reads until startup/tool call so the MCP can initialize and return a clean missing-credential diagnostic.

## GitHub PR/Issue URL

TBD
