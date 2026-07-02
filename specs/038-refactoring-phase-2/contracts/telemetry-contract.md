# Contract: Telemetry And Redaction

## Identity

- OpenTelemetry owns `trace_id`.
- OpenTelemetry owns `span_id`.
- Wright owns `wright.correlation_id`.
- `X-Trace-Id` carries `wright.correlation_id` for API clients and UI support flows.

## Required Span/Event Names

- `workspace.create`
- `workspace.activate`
- `workspace.config.update`
- `workspace.file.execute`
- `agent.runtime.select`
- `agent.context.materialize`
- `mcp.catalog.seed_refresh`
- `mcp.server.install`
- `mcp.server.start`
- `mcp.server.stop`
- `mcp.tool.call`
- `mcp.safety.evaluate`
- `mcp.validation.plan`
- `mcp.validation.run`
- `mcp.validation.evidence.write`

## Required Fields When Available

- `wright.correlation_id`
- `wright.workspace_id`
- `wright.session_id`
- `wright.agent_id`
- `wright.provider_id`
- `wright.server_id`
- `wright.tool_name`
- `wright.validation_id`
- `wright.catalog_version`
- `wright.policy_decision`
- `duration_ms`
- `error_code`

## Forbidden Without Redaction

- Raw credential values
- Full environment maps
- Unredacted command lines
- Full raw tool arguments
- Full subprocess stdout/stderr
- Full validation evidence payloads before redaction

## Remote Export

Remote telemetry export is disabled by default. Any remote exporter requires explicit operator configuration.
