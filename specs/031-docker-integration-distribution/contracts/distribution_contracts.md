# Contracts: Distribution & Packaging Boundaries

This document defines the packaging and integration contracts for `hermes-plugin-wright`.

---

## 1. PyPI / Python Packaging Entry Point

To ensure auto-discovery by Hermes Agent, the plugin package must declare an entry point in `pyproject.toml` conforming to standard Python PEP 517 metadata.

```toml
[project.entry-points."hermes_agent.plugins"]
wright = "hermes_plugin_wright:register"
```

Hermes Agent loads this using:
```python
import importlib.metadata

# Scans all active environment packages for the entry point group
eps = importlib.metadata.entry_points(group='hermes_agent.plugins')
wright_plugin = next((ep for ep in eps if ep.name == 'wright'), None)
register_hook = wright_plugin.load()
```

---

## 2. Docker Build Stage Contracts

During the Docker image build, the plugin files must be copied and installed as follows:

```dockerfile
# 1. Copy plugin files to a system-wide read-only directory
COPY hermes-plugin-wright/ /opt/hermes-plugins/wright/

# 2. Inject the package into the isolated hermes-agent virtual environment
RUN uv tool inject hermes-agent /opt/hermes-plugins/wright/
```

- **Target virtual environment**: `/opt/uv-tools/hermes-agent`
- **Output validation**: Running `hermes --help` or `python hermes-plugin-wright/verify_plugin.py` inside the container must execute without import errors.

---

## 3. Container Runtime Process Boundary

- **Indicator**: Existence of `/.dockerenv`.
- **Behavior Contract**:
  - When `is_in_docker() == True`:
    - API Healthy (`GET /api/health` returns 200): Return connection status successfully.
    - API Unhealthy: Do not launch any detached process. Immediately return:
      ```text
      ❌ Wright API is not running or unhealthy inside the container.
         Uvicorn lifecycle must be managed via supervisord.
      ```
