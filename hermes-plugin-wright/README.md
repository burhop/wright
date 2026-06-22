# Hermes Wright Plugin

This is the official Wright integration plugin for Hermes Agent. It provides a browseable catalog of engineering MCP tools and commands to start and manage the Wright stack.

## Directory Structure

```text
hermes-plugin-wright/
├── plugin.yaml              # Plugin metadata manifest
├── __init__.py              # Registration entry point: register(ctx)
├── catalog.yaml             # Registry database containing ~30 engineering tools
├── catalog.py               # CatalogLoader implementation (search and filter APIs)
├── bridge.py                # Wright FastAPI server API client bridge
├── schemas.py               # Pydantic validation schemas (CatalogEntry, etc.)
├── pyproject.toml           # Packaging and dependencies
├── tests/
│   ├── conftest.py          # Test configuration
│   ├── test_catalog.py      # Unit tests for validation and search
│   └── test_bridge.py       # Unit tests for bridge API client
└── README.md                # This file
```

## Installation

### Manual Installation (Development)
To load this plugin manually in Hermes, copy the package directory into your local Hermes plugins folder:

```bash
cp -r hermes-plugin-wright/ ~/.hermes/plugins/wright
```

### PyPI Installation
Or install it in editable mode inside your Python environment:

```bash
pip install -e ./hermes-plugin-wright
```

## Catalog Usage

You can load and query the engineering tool catalog programmatically:

```python
from hermes_plugin_wright.catalog import CatalogLoader

# Load the catalog
loader = CatalogLoader()

# Query by domain taxonomy
cad_tools = loader.get_by_domain("cad")

# Search by keyword
results = loader.search("CalculiX")
```

## Bridge Client Usage

You can communicate with the Wright stack API server via the asynchronous bridge client:

```python
import asyncio
from hermes_plugin_wright.bridge import (
    detect_repo_dir,
    check_api_health,
    get_mcp_servers,
    get_workspaces,
)

async def main():
    # Auto-detect Wright repository path from local Hermes config
    repo_dir = detect_repo_dir()
    print(f"Detected repo path: {repo_dir}")

    # Check the API health
    health = await check_api_health()
    print(f"API Health: {health}")

    # Fetch registered MCP servers
    servers = await get_mcp_servers()
    print(f"MCP Servers: {servers}")

if __name__ == "__main__":
    asyncio.run(main())
```
