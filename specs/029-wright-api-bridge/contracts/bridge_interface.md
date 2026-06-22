# Interface Contracts: Wright API Bridge Client

This document defines the async methods exposed by the `bridge.py` module.

## Methods

### 1. detect_repo_dir
Locates the repository root directory on the host filesystem.
```python
def detect_repo_dir() -> Optional[str]:
    """
    Scans:
    1. ~/.hermes/profiles/wright/config.yaml
    2. ~/.hermes/config.yaml
    
    Parses 'wrightgateway' mcp_servers args list to locate '--project [path]'.
    Returns the absolute path, or None if not found.
    """
```

### 2. check_api_health
Queries FastAPI setup health check.
```python
async def check_api_health() -> dict:
    """
    Sends GET /api/health.
    Returns:
        {"success": True, "connected": True, "latencyMs": float}
        or
        {"success": False, "connected": False, "error": str}
    """
```

### 3. get_mcp_servers
Lists all registered servers from the database.
```python
async def get_mcp_servers() -> dict:
    """
    Sends GET /api/mcp/servers.
    Returns:
        {"success": True, "servers": list[dict]}
        or
        {"success": False, "error": str}
    """
```

### 4. register_mcp_server
Registers a tool from the catalog into the registry database.
```python
async def register_mcp_server(entry: CatalogEntry) -> dict:
    """
    Sends POST /api/mcp/servers with the serialized CatalogEntry fields
    mapped to the McpServerCreate schema.
    Returns:
        {"success": True, "server_id": str}
        or
        {"success": False, "error": str}
    """
```

### 5. get_workspaces
Lists active and recent workspace profiles.
```python
async def get_workspaces() -> dict:
    """
    Sends GET /api/workspace/list.
    Returns:
        {"success": True, "workspaces": list[dict]}
        or
        {"success": False, "error": str}
    """
```

### 6. get_credential_status
Checks credential configurations without retrieving values.
```python
async def get_credential_status(server_id: str) -> dict:
    """
    Sends GET /api/mcp/servers/{server_id}/credentials.
    Returns:
        {"success": True, "credentials": dict[str, bool]} # e.g. {"ONSHAPE_API_KEY": True}
        or
        {"success": False, "error": str}
    """
```
