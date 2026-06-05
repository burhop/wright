# Data Model & Configuration Schemas: Docker Distribution Polish

This document defines the configuration schemas, OCI image labels mapping, and docker-compose configurations.

---

## 1. OCI Image Labels Specification

These labels will be declared in the production `Dockerfile` under the organizational metadata spec:

| Label Name | Build Arg | Source / Value |
| :--- | :--- | :--- |
| `org.opencontainers.image.title` | None | `"Wright"` |
| `org.opencontainers.image.description` | None | `"Local-first AI mechanical engineer — CAD generation, FEA, and manufacturing automation powered by multi-agent LLMs"` |
| `org.opencontainers.image.url` | None | `"https://github.com/burhop/wright"` |
| `org.opencontainers.image.source` | None | `"https://github.com/burhop/wright"` |
| `org.opencontainers.image.documentation` | None | `"https://burhop.github.io/wright/"` |
| `org.opencontainers.image.vendor` | None | `"burhop"` |
| `org.opencontainers.image.licenses` | None | `"MIT"` |
| `org.opencontainers.image.version` | `VERSION` | Build-time injected version string (e.g. `0.1.0`) |
| `org.opencontainers.image.revision` | `REVISION` | Build-time injected git commit SHA |
| `org.opencontainers.image.created` | `CREATED` | Build-time injected ISO 8601 timestamp |

---

## 2. Docker Compose Variant Profiles

The project will support two Docker Compose layout profiles:

### 1. Production Layout (`docker-compose.yml`)
*   **Service Core**: `agent` (contains API gateway, mounted volumes, and ports mapping)
*   **Observability Stack**: `jaeger` (jaegertracing/all-in-one container for OpenTelemetry traces)
*   **Ports**: Remaps `8080` (external host) to `8000` (internal API container).

### 2. Minimal Layout (`docker-compose.minimal.yml`)
*   **Service Core**: `agent` (same core application container and volumes)
*   **Observability Stack**: None (Jaeger service is omitted; OTEL tracing variables point to null/local trace logs instead of external collector)
*   **Ports**: Remaps `8080` (external host) to `8000` (internal API container).
