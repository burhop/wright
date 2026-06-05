# Observability & Tracing

Engineering processes require high predictability. Wright rejects the "black box" design of typical AI applications, implementing a comprehensive end-to-end OpenTelemetry and structured logging architecture.

## Observability Architecture

*   **End-to-End Tracing**: Every user request generates a unique `trace_id`. The FastAPI middleware extracts/injects this identifier as the `X-Trace-Id` HTTP header. The trace propagates from the React frontend, through the router handlers, down to agent adapter prompts, tool executions, and SQLite database queries.
*   **Semantic Span Hierarchy**: Spans are published to a local **Jaeger** instance using standardized naming structures:
    *   `workspace.create`
    *   `agent.chat.start`
    *   `db.sqlite.query`
    *   `tool.openscad_generate`
    This allows developers and compliance auditors to inspect latency distributions and debug tool execution errors.
*   **Structured JSON Logging**: The entire Python codebase utilizes `structlog` to output standardized JSON lines, automatically binding the active trace context and parent span.
*   **Client-Side Log Persistence**: The React client records console and API errors locally using **IndexedDB** (`wright-logs` database). This provides an offline log buffer that can be queried by users or sent to support systems for diagnosing local runtime failures.

## OpenTelemetry Schema Mapping

All request and execution spans register key attribute metadata:

| Attribute | Description | Example Value |
| :--- | :--- | :--- |
| `wright.workspace_id` | Identifier of active workspace | `ws_proj_08` |
| `wright.session_id` | Active agent conversation session | `sess_4821` |
| `wright.tool_name` | Name of executing MCP tool | `openscad.generate_mesh` |
| `wright.agent_name` | Active reasoning agent profile | `openclaw` |
