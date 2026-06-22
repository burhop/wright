# Research: Engineering Tool Catalog

## Decisions

### 1. Catalog File Format & Location
* **Decision**: YAML format at `hermes-plugin-wright/catalog.yaml`.
* **Rationale**: YAML is highly human-readable, making it easy for developers to add or update tool entries without JSON's syntax constraints.
* **Alternatives Considered**: JSON (rejected due to lack of comments and strict syntax), SQLite database (rejected because a static catalog file is simpler to manage in version control and distribute with the plugin).

### 2. Search Implementation
* **Decision**: In-memory keyword search across fields (`name`, `description`, `tags`) using basic Python string operations.
* **Rationale**: The catalog contains a small number (~30) of entries, so advanced search libraries (like Whoosh or SQLite FTS) are unnecessary overhead. Case-insensitive substring matching is extremely fast and has zero deployment dependencies.
* **Alternatives Considered**: Regular expressions (rejected to keep code simple and fast).

### 3. Pydantic Alignment
* **Decision**: Import Pydantic directly to construct `schemas.py` models, matching the existing structure of `tool_registry.models.EnvVarDefinition` exactly.
* **Rationale**: Enables seamless direct insertion into the main Wright SQLite backend database when the tool is installed.

## Technical Unknowns & Mitigation
* No critical technical unknowns are present. The domain taxonomy and schema mappings are pre-defined.
