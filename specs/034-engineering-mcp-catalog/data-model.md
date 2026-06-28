# Data Model: Engineering MCP Catalog

## MCP Catalog Entry

Represents a known engineering MCP server, docs MCP, wrapper candidate, capability alias, UI/web standard, watchlist item, or excluded candidate.

Fields:

- `server_id`: Stable canonical identifier.
- `display_name`: User-facing name.
- `aliases`: Alternate names from prior catalogs or research.
- `verification_state`: One of `verified_mcp`, `verified_docs_mcp`, `community_mcp`, `user_reported_url_needed`, `verified_api_wrapper_candidate`, `capability_alias`, `ui_or_web_standard`, `watchlist`, `excluded`.
- `installability_tier`: One of `tested`, `might_work`, `blocked`, `non_working`.
- `source_url`: Primary evidence URL when known.
- `host_reference_urls`: Supporting host/vendor documentation URLs.
- `domains`: Engineering areas such as CAD, code CAD, FEA, CAM, BIM, PLM, robotics, IoT, documentation.
- `description`: Short user-facing summary.
- `deployment_mode`: One of `local-only`, `local-bridge`, `local-plus-network`, `cloud-saas`, `remote-mcp`, `docs-only`, `unknown`.
- `transport`: One or more of `stdio`, `sse`, `streamable-http`, `webmcp`, `websocket`, `rest-bridge`, `custom-rpc`, `unknown`.
- `platform_support`: Platform support records for all required platform keys.
- `host_software_required`: Required host applications, drivers, CAD tools, hardware controllers, or runtimes.
- `requires_gui`: Whether a GUI session is required.
- `headless_ok`: One of `yes`, `likely`, `unknown`, `no`.
- `credentials_required`: Credential definitions or environment variable names.
- `install_methods`: Install/probe methods.
- `example_mcp_config`: Optional MCP client configuration.
- `health_check`: Expected validation action or blocked reason.
- `risk_level`: One of `read-only`, `low`, `medium`, `high`, `safety-critical`.
- `default_enabled`: Whether the entry may be enabled by default.
- `approval_gates`: Safety approvals required before write/code/cloud/machine actions.
- `follow_up_url`: Optional local or GitHub follow-up record for non-working entries.

Validation rules:

- Every entry must have all required platform keys.
- `tested` entries must have validation evidence and cannot lack source/install evidence.
- `user_reported_url_needed` entries cannot be auto-installable.
- `high` and `safety-critical` entries must default disabled.
- `capability_alias` and `ui_or_web_standard` entries must not be counted as verified installable MCP servers.

## Platform Support Record

Represents compatibility for a specific OS/architecture.

Fields:

- `status`: One of `yes`, `likely`, `host-dependent`, `unknown`, `no`.
- `tested`: Boolean indicating whether the current implementation has tested this platform.
- `notes`: Human-readable evidence or limitation.

## Install Method

Represents a supported automated or manual install/probe approach.

Fields:

- `type`: One of `uvx`, `uv`, `npm`, `npx`, `docker`, `host_app_addon`, `remote_mcp`, `manual`, `blocked`.
- `command`: Executable name or connector type.
- `args`: Command arguments.
- `env`: Required environment indirections.
- `automation_allowed`: Whether validation may run this method automatically.
- `notes`: Install or limitation notes.

Validation rules:

- Blocked and URL-needed entries have no automation-allowed install methods.
- Commands must be represented as structured arrays where possible.

## Validation Result

Represents the result of probing one catalog entry in one environment.

Fields:

- `server_id`: Catalog entry identity.
- `environment`: Platform and runner environment label.
- `status`: One of `passed`, `dependency_missing`, `blocked`, `failed`, `skipped`, `not_tested`.
- `installability_tier`: Derived tier after validation.
- `message`: User-facing summary.
- `diagnostics`: Detailed but secret-redacted output.
- `missing_dependencies`: Required host software, credentials, license, GUI, or hardware not present.
- `tested_at`: Timestamp.
- `follow_up_url`: Link to follow-up record when applicable.

State transitions:

- URL-needed entries: `not_tested` -> `blocked`.
- Verified/community entries: `not_tested` -> `passed`, `dependency_missing`, or `failed`.
- Failed entries: `failed` -> `non_working` and follow-up required.
- Dependency-missing entries: `dependency_missing` -> `might_work` unless the missing dependency makes the platform unsupported.

## Safety Policy

Represents default restrictions for risky entries.

Fields:

- `risk_level`: Read-only through safety-critical.
- `default_enabled`: Boolean.
- `approval_gates`: Approval names required before unsafe actions.
- `read_only_default`: Boolean.
- `simulation_default`: Boolean for machine-control entries.
- `security_notes`: User-facing risk notes.

Validation rules:

- Safety-critical entries require disabled defaults and machine-control approval.
- Code execution entries require execute-code approval.
- Cloud upload entries require cloud-upload and secrets approvals where credentials are needed.

## Follow-Up Record

Represents durable investigation work for a non-working entry.

Fields:

- `server_id`: Catalog entry identity.
- `title`: Triage title.
- `source_url`: Evidence source.
- `observed_status`: Validation status that triggered the record.
- `environment`: Reproduction environment.
- `failure_summary`: Short failure reason.
- `reproduction_steps`: Commands or actions used.
- `expected_behavior`: What should work.
- `next_action`: Suggested fix or verification step.
- `record_path`: Local path.
- `github_url`: Optional PR or issue URL.

Validation rules:

- One active follow-up record per `server_id` and failure signature.
- Records must not contain secret values.

## Missing MCP Report

Represents a user-submitted MCP candidate before verification.

Fields:

- `submitted_name`
- `suggested_source_url`
- `reported_capabilities`
- `reported_platforms`
- `notes`
- `normalized_server_id`
- `created_at`

Validation rules:

- Reports with incomplete evidence become `user_reported_url_needed`.
- Duplicate aliases are merged into existing entries.
