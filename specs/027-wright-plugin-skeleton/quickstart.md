# Quickstart: Hermes Wright Plugin Skeleton

This guide helps you set up, install, and run a basic verification of the `hermes-plugin-wright` skeleton.

## Prerequisites

* Python >= 3.11
* `pip` and `virtualenv` (or standard `venv`)

## Installation

To install the plugin in editable mode for local development:

```bash
# From the wright repository root
pip install -e ./hermes-plugin-wright
```

Alternatively, to build the source and wheel distribution:

```bash
# Build the package
python -m build ./hermes-plugin-wright
```

## Verification

Since this is a skeleton implementation, verification checks that the plugin is discoverable and logs correctly when registered.

### 1. Verification Script
You can run a quick mock verification in python:

```python
import importlib.metadata
import structlog

# Check entry point registration
entry_points = importlib.metadata.entry_points(group='hermes_agent.plugins')
wright_plugin = next((ep for ep in entry_points if ep.name == 'wright'), None)

assert wright_plugin is not None, "Wright plugin entry point not registered!"
print("✅ Entry point discoverable")

# Load and invoke entry point
register_func = wright_plugin.load()
register_func(None)  # Invokes registration and triggers structlog output
```

### Expected Output
When run, the script should output:
```json
{"event": "Wright plugin loaded", "level": "info", "logger": "hermes_plugin_wright"}
```
*(Exact output format depends on your `structlog` configuration)*
