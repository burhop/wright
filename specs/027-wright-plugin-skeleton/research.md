# Research: Hermes Wright Plugin Skeleton

## Decisions

### 1. Build System & Packaging
* **Decision**: Use `hatchling` as the build backend, configured via `pyproject.toml`.
* **Rationale**: Modern Python packaging standard. It is lightweight, supports PEP 621 metadata, and matches the distribution strategy outlined in Section 11.2 of [wright-hermes-plugin-plan.md](../../docs/wright-hermes-plugin-plan.md).
* **Alternatives Considered**: `setuptools` / `setup.py` (rejected as deprecated/legacy for new packages); `poetry` (rejected to keep dependencies and configuration standard and simple for a standalone plugin directory without lockfile overhead in the distribution package itself).

### 2. Entry Point Group
* **Decision**: Register the entry point under the `"hermes_agent.plugins"` namespace with name `"wright"` mapping to `hermes_plugin_wright:register`.
* **Rationale**: Aligns with the Hermes plugin discovery protocol, enabling Hermes to automatically load and register the plugin when the Python package is installed in the environment.
* **Alternatives Considered**: Direct filesystem path scanning (slower, harder to distribute via PyPI, but supported as a fallback copying option). Using standard entry points is the cleanest distribution path.

### 3. Structured Logging
* **Decision**: Use `structlog` to emit the `"Wright plugin loaded"` initialization message.
* **Rationale**: The Wright project constitution Section 7 mandates structured JSON logging and forbids traditional text logs. Using `structlog` ensures the plugin's logs are structured and compatible with the broader Wright appliance logging format.
* **Alternatives Considered**: Python's standard `logging` library (rejected due to constitutional mandate for structured JSON logging).

## Technical Unknowns & Mitigation
* No critical technical unknowns or `NEEDS CLARIFICATION` markers were present in the specification.
