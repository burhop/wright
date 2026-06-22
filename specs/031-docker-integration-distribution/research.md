# Research Findings: Docker Integration & Distribution Packaging

This document outlines the research and architectural decisions for integrating the `hermes-plugin-wright` package inside Docker and local Python environments.

---

## 1. Container Integration & Packaging

### Topic: Injecting the plugin into the Hermes Agent isolated tool environment.

- **Decision**: 
  Add the following lines to `docker/Dockerfile` right after the `uv tool install hermes-agent==0.15.2` instruction:
  ```dockerfile
  # ── Copy and inject Wright Hermes plugin ───────────────────
  COPY --chown=agent:agent hermes-plugin-wright/ /opt/hermes-plugins/wright/
  RUN uv tool inject hermes-agent /opt/hermes-plugins/wright/
  ```
- **Rationale**: 
  Because `hermes-agent` is installed as a CLI tool using `uv tool install`, it runs in an isolated virtual environment under `/opt/uv-tools/hermes-agent`. Doing a global `pip install` or `uv pip install --system` makes the plugin package visible to system Python but not to the `hermes` CLI execution context. Running `uv tool inject` ensures the plugin and its dependencies are loaded into the specific virtual environment managed by `uv tool`.
- **Alternatives Considered**: 
  - **Mounting skill directories manually**: Creating a symlink from `/opt/hermes-plugins/wright` to `~/.hermes/plugins/wright`. While this works, it does not install library dependencies (like `respx`, `httpx` etc.) automatically if they are missing in the tool environment, whereas `uv tool inject` does.

---

## 2. Headless/Docker Launcher Behavior

### Topic: Preventing manual uvicorn process spawning inside Docker containers.

- **Decision**: 
  Implement `is_in_docker()` by verifying the presence of `/.dockerenv` or container-specific variables.
  Inside `/wright start` in `commands.py`:
  ```python
  def is_in_docker() -> bool:
      return os.path.exists('/.dockerenv')
  ```
  If `is_in_docker()` is True:
  - If the API health check succeeds, open the UI URL and report success.
  - If the API is unhealthy/stopped, immediately abort and return a supervisor warning:
    `❌ Wright API is not running or unhealthy inside the container.`
    `   Uvicorn lifecycle must be managed via supervisord.`
- **Rationale**: 
  Inside the Docker appliance container, supervisord is the single source of truth for process lifecycles. If the API is down, starting uvicorn via `subprocess.Popen` in `/wright start` would create a rogue process not tracked by supervisord, causing resource leaks and port conflicts.
- **Alternatives Considered**: 
  - Attempting to call `supervisorctl restart wright-api`. Rejected because this requires root/supervisor group permissions that the `agent` user may not have, and could lead to privilege escalation issues.

---

## 3. Context & Sync Boundary

### Topic: Preventing duplicate configuration and metadata writes.

- **Decision**: 
  The plugin's `register(ctx)` registers `/wright` commands and loads the catalog loader. It does not attempt to modify `config.yaml` or write `.hermes.md` files. All data syncing and instruction generation remain delegated to `api.services.hermes_sync` (`hermes_sync.py`), which executes on core API lifecycles.
- **Rationale**: 
  Keeps the plugin lightweight and avoids write collisions, race conditions, or file locks when multiple agent sessions are opened.
