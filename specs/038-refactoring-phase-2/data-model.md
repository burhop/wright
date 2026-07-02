# Data Model: Wright Architecture Refactoring Phase 2

## Workspace Service Request

Represents a package-level workspace operation request.

Fields:

- `db_path`: local SQLite database path
- `session_id`: current or requested agent session ID
- `workspace_id`: optional workspace identifier
- `workspace_name`: human-readable workspace name for create flows
- `local_path`: absolute workspace path when known
- `agent_id`: optional provider ID, defaulting through the agent registry
- `policy`: operation-specific policy such as file execution timeout

Validation:

- Workspace names must be non-empty after sanitization.
- Generated paths must remain under the configured Wright workspace parent unless the user supplied an absolute local path.
- File execution paths must resolve inside the workspace and must be Python files for the current compatibility path.

## Workspace Activation

Represents the result of activating a workspace.

Fields:

- `success`: boolean
- `session_id`: active session after fallback or provider verification
- `workspace_path`: absolute path
- `workspace_id`: optional workspace ID
- `agent_id`: provider ID
- `context`: `ContextMaterializationResult`

State transitions:

- `requested` -> `session_verified`
- `session_verified` -> `context_materialized`
- `context_materialized` -> `gateway_synced`
- Any state -> `failed` with typed error

## Agent Context Materializer

Provider-owned context writer.

Fields:

- `provider_id`
- `support_level`: `supported`, `experimental`, `stub`, or `unavailable`
- `context_filename`: optional provider-owned file name

Operations:

- `materialize(db_path, workspace_path, context) -> ContextMaterializationResult`

Validation:

- A materializer may intentionally write no files.
- Hermes materializer is the only generic provider allowed to write `.hermes.md`.

## Context Materialization Result

Safe metadata about provider context refresh.

Fields:

- `provider_id`
- `support_level`
- `files_written`
- `warnings`
- `error_code`

Redaction:

- Must not contain raw generated prompt content, credentials, or full environment maps.

## MCP Policy Decision

Result from `tool_registry` safety evaluation.

Fields:

- `allowed`
- `operation`: `install`, `start`, or `call`
- `reason`
- `required_approvals`
- `missing_credentials`
- `network_required`
- `blocked_by_catalog`
- `diagnostics`

Validation:

- Blocked and non-working entries are always denied for install/start/call in this phase.
- Missing credentials deny start/call.
- High-risk and safety-critical entries with approval gates deny install/start/call unless matching local approvals exist.

## Approval Context

Local approvals available to safety policy.

Fields:

- `machine_approvals`
- `workspace_approvals`
- `workspace_id`

Validation:

- Install checks global machine approvals.
- Start/call checks workspace approvals and machine approvals.

## Validation Evidence

Canonical validation record.

Required fields:

- `server_id`
- `catalog_version`
- `validation_started_at`
- `validation_finished_at`
- `environment`
- `container_image`
- `install_steps`
- `protocol_probes`
- `safe_backend_probe`
- `gateway_proxy_probe`
- `credential_requirements`
- `network_requirements`
- `result`
- `diagnostics`
- `follow_up_required`
- `redactions`

Compatibility fields:

- `status`
- `steps`
- `missing_dependencies`
- `follow_up_url`

Redaction:

- Commands, environment values, credentials, tool arguments, subprocess output, diagnostics, and validation evidence summaries must be redacted before persistence or logs.

## Generated Contract Bundle

Checked-in TypeScript domain contract file.

Fields:

- `generated_at_policy`: static comment describing deterministic generation
- `source_models`: list of package/backend schemas represented
- `typescript_interfaces`: generated interfaces and literal unions

Validation:

- Regeneration must be deterministic and offline.
- Contract freshness tests compare generated output to checked-in files.
