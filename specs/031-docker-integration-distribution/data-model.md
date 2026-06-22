# Data Model: Docker Integration & Distribution Packaging

This document describes the entities, configurations, and environment mappings utilized for distributing and packaging the `hermes-plugin-wright` plugin.

---

## 1. Container Configuration Metadata

These variables represent the execution state and configurations loaded in the Docker container during the build stage.

### Docker Env Indicator
- **Source**: `/.dockerenv` file path.
- **Data Type**: Boolean (file exists check).
- **Purpose**: Restricts the launcher from starting manual background subprocesses.

### Supervisord Processes
The container runs two primary processes managed via supervisor:
1. `wright-api`: Runs the FastAPI backend on port 8000.
2. `hermes-gateway`: Runs the Hermes gateway listener on port 8642.

---

## 2. Packaging Manifest Mappings

The plugin package structure is declared inside `pyproject.toml` and `plugin.yaml`:

### Entry Point Schema
- **Group**: `hermes_agent.plugins`
- **Name**: `wright`
- **Hook Value**: `hermes_plugin_wright:register`

### Manifest Schema (`plugin.yaml`)
- **name**: `wright`
- **version**: `1.0.0`
- **min_hermes_version**: `0.15.2`
- **capabilities**:
  - `commands`: Enables registration of `/wright` namespace.
