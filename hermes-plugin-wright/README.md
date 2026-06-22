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

### Docker Appliance Installation
The plugin is baked into the official Wright appliance Docker image. To build and run the appliance:

```bash
# Build the Docker image
docker build -t wright-appliance:latest -f docker/Dockerfile .

# Start the appliance container
docker run -d -p 8000:8000 --name wright-app wright-appliance:latest
```

## Quick Start Guide

Once the plugin is loaded in Hermes, run the following slash commands:

1. **Start the stack**:
   ```bash
   /wright start
   ```
   *(Locally builds web assets and starts uvicorn; inside Docker, verifies supervisord uvicorn service health).*

2. **Browse catalog of tools**:
   ```bash
   /wright catalog cad
   ```
   *(Lists CAD tools like FreeCAD and OpenSCAD).*

3. **Install an MCP tool**:
   ```bash
   /wright install openscad-mcp
   ```
   *(Registers the tool in the active Wright workspace).*

## Slash Commands

Once loaded in Hermes, the plugin exposes the `/wright` slash command group:

| Command | Arguments | Description |
|:---|:---|:---|
| `/wright start` | | Builds frontend web assets, starts the FastAPI server, and opens the UI in your browser |
| `/wright stop` | | Gracefully shuts down the FastAPI server via SIGTERM signaling |
| `/wright open` | | Opens the Wright UI in your default browser (requires running stack) |
| `/wright doctor` | | Performs a diagnostic environment health check |
| `/wright status` | | Shows connection status, active workspace, and status of configured MCP tools |
| `/wright catalog` | `[domain]` | Lists available engineering tools filterable by domain tag (e.g. `cad`, `fea`) |
| `/wright catalog search` | `<query>` | Performs a keyword search across catalog attributes |
| `/wright info` | `<id>` | Displays requirements, commands, credentials, and dependencies of a catalog item |
| `/wright install` | `<id>` | Installs/registers a cataloged engineering MCP server in the Wright gateway |

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

## References

For full details, designs, and distribution strategies, check the [Wright Hermes Plugin Plan](file:///home/burhop/repos/wright/docs/wright-hermes-plugin-plan.md).
