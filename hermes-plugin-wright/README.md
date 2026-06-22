# Hermes Wright Plugin

This is the official Wright integration plugin for Hermes Agent. It provides a browseable catalog of engineering MCP tools and commands to start and manage the Wright stack.

## Directory Structure

```text
hermes-plugin-wright/
├── plugin.yaml              # Plugin metadata manifest
├── __init__.py              # Registration entry point: register(ctx)
├── pyproject.toml           # Packaging and dependencies
├── tests/
│   └── conftest.py          # Test configuration
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
