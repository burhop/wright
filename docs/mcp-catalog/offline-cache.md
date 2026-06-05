# Offline Caching Strategy

To facilitate complete offline operation in air-gapped or restricted-network environments, Wright implements a write-through offline caching system for both external Model Context Protocol queries and LLM contexts.

---

## 1. Local Package Caching

When running behind a firewall or offline:
*   **Apt Packages**: Pre-cached in `wright_varcache` volume during the initial container build.
*   **Python Dependencies**: Local packages can be installed using pre-downloaded wheels stored in a local directory cache or mirrored packages on the host.

---

## 2. Vector DB Metadata Caching

For RAG operations:
*   Engineering manuals, standards PDFs, and dataset vectors are pre-indexed and embedded into the local Vector DB.
*   Agents search the local in-process DB instead of executing remote cloud embedding lookups.

---

## 3. Tool Caching Actions

For third-party integrations (e.g., external REST MCP tools):
*   A write-through caching layer serializes tool request inputs and responses into a local SQLite table (`mcp_cache`).
*   Subsequent requests with identical arguments retrieve the response directly from the local cache, preventing remote network errors.
