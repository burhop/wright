# Quickstart: Wright API Bridge Client

This guide explains how to import the bridge client and invoke endpoints.

## Example Invocations

```python
import asyncio
from hermes_plugin_wright.bridge import (
    check_api_health,
    get_mcp_servers,
    get_workspaces
)

async def test_bridge():
    # 1. Health check
    health = await check_api_health()
    print("Health Status:", health)
    
    # 2. Fetch servers
    if health.get("connected"):
        servers = await get_mcp_servers()
        print("MCP Servers:", servers)
        
        # 3. Fetch workspaces
        workspaces = await get_workspaces()
        print("Workspaces:", workspaces)

if __name__ == "__main__":
    asyncio.run(test_bridge())
```

## Mock Testing
To run mock integration tests:

```bash
pytest hermes-plugin-wright/tests/test_bridge.py
```
