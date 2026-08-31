# Read-Only Process Definition API Contract

## Request

`GET /api/process-definitions/{process_id}` requires the existing engineer/admin read role when authentication is enforced, accepts `If-None-Match`, and supports only the bundled process in EPP-F02.

## Success

- `200 application/json`: validated definition, source kind, allowlisted logical `source_id`, source digest/availability, supported versions, and exact content identity.
- `ETag`: quoted SHA-256 of the canonical complete response envelope (excluding the ETag itself and request-specific trace header), so either a semantic-content or raw-source-identity change invalidates cache reuse; `Cache-Control: no-cache, private`; `X-Trace-Id`: existing trace.
- `304`: exact ETag match, no body.

## Closed failures

- `404 PROCESS_DEFINITION_UNAVAILABLE`, recovery `enable_or_reinstall`.
- `409 PROCESS_DEFINITION_IDENTITY_MISMATCH`, recovery `reinstall_exact_artifact`.
- `422 PROCESS_DEFINITION_INVALID`, recovery `replace_validated_definition`.
- `422 PROCESS_DEFINITION_UNSUPPORTED_VERSION`, recovery `install_compatible_wright`.
- `503 PROCESS_DEFINITION_READ_FAILED`, recovery `inspect_local_data_root`.

Errors include trace ID, code, recovery class, and supported versions where relevant; never raw content, absolute paths, credentials, or stack traces.

The only EPP-F02 `source_id` is `process-definitions/product-definition-v1.json`. Absolute paths, traversal, URI schemes, query/fragment text, and external URLs are rejected before response. The browser displays this logical identity and an internal detail view only; it never constructs a filesystem or external link.

No POST, PUT, PATCH, DELETE, execute, Apply, MCP, or LLM endpoint is included.
