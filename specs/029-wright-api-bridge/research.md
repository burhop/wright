# Research: Wright API Bridge Client

## Decisions

### 1. HTTP Client Selection
* **Decision**: Use `httpx.AsyncClient` for all bridge requests.
* **Rationale**: `httpx` is a modern, fully async-capable HTTP client library for Python. It is already a dependency of the project (declared in `pyproject.toml`) and is the standard client library within the FastAPI ecosystem.
* **Alternatives Considered**: `requests` (rejected because it is synchronous, which would block the async Hermes event loop during long-running network calls); `aiohttp` (rejected to keep dependencies minimal, since `httpx` is already utilized in the workspace).

### 2. Error and Exception Boundary
* **Decision**: Catch all `httpx.HTTPError` exceptions (including connection, timeout, and response status errors) and return a structured dictionary containing `{"success": False, "error": "error message details"}`.
* **Rationale**: The bridge should fail gracefully. Unhandled connection exceptions would crash the host Hermes Agent plugin manager. Normalizing failures allows downstream command routers to output human-friendly diagnostic messages (e.g. "API offline").
* **Alternatives Considered**: Raising custom exceptions (rejected to keep the interface simple and easy for slash commands to display direct text prompts).

### 3. File Parser for Repo Detection
* **Decision**: Read `~/.hermes/profiles/wright/config.yaml` using `pyyaml` safe loading and search the argument list of `wrightgateway` for `--project`.
* **Rationale**: Simple, direct parser that avoids environment variable dependencies, automatically locating the correct repo path as seeded by the core `hermes_sync.py` synchronization service.
* **Alternatives Considered**: Regular expressions over the raw YAML string (rejected because structured parsing via PyYAML is safer and handles spacing changes natively).

## Technical Unknowns & Mitigation
* No critical technical unknowns are present. The route endpoints are verified in `apps/api` routers.
