# Data Model: Architecture Refactoring Audit Implementation

## AgentRuntimeProvider

- **Purpose**: Describes one selectable agent runtime implementation.
- **Fields**: `name`, `display_name`, `description`, `is_default`, `supported`, `health_capabilities`, `gateway_profile`, `factory`.
- **Validation Rules**: `name` is lowercase and unique. Exactly one provider is default. Unsupported providers may be listed only if they cannot be instantiated accidentally.

## AgentEngineRegistry

- **Purpose**: Resolves provider metadata, validates active runtime names, and creates engine instances.
- **Fields**: `providers`, `default_provider_name`.
- **Relationships**: Creates `BaseAgentEngine` instances from `AgentRuntimeProvider` factories.
- **State Transitions**: `unconfigured -> default_provider`; `configured_supported -> provider`; `configured_unsupported -> typed error`.

## AgentRuntimeSettings

- **Purpose**: Captures active runtime selection and provider-specific configuration source.
- **Fields**: `active_agent`, `source`, `llm_api_url`, `provider_settings`.
- **Validation Rules**: Runtime names must be recognized by the registry before becoming active.

## WrightGatewayProfile

- **Purpose**: Describes how a runtime consumes Wright gateway capabilities.
- **Fields**: `profile_name`, `server_name`, `protocol`, `command`, `args`, `workspace_context_writer`, `supports_tool_list_changed`.
- **Validation Rules**: Generic contract uses "Wright gateway"; Hermes-specific command details are confined to the Hermes provider/profile.

## WrightGatewaySyncAdapter

- **Purpose**: Applies gateway configuration and workspace context for a provider.
- **Fields**: `provider_name`, `profile`, `sync_static_config`, `sync_workspace_context`, `notify_tool_change`.
- **Relationships**: May call existing Hermes config writers through a Hermes adapter while future providers implement the same interface.

## WorkspaceContextWriter

- **Purpose**: Writes agent-facing workspace context files without making `.hermes.md` the generic extension point.
- **Fields**: `target_filename`, `format_version`, `write_context`.
- **Validation Rules**: Shared contracts do not require Hermes filenames. Hermes compatibility may continue writing `.hermes.md`.

## McpServiceOperation

- **Purpose**: Represents a business operation moved out of an HTTP route.
- **Fields**: `operation_name`, `request_data`, `result_data`, `domain_errors`.
- **Relationships**: Wraps `McpEngine`, `tool_registry.db`, `tool_registry.secrets`, `mcp_validation`, and gateway sync adapters.
- **Validation Rules**: Service results map to existing route response models without changing successful response shapes.

## CatalogRecord

- **Purpose**: Shared normalized MCP catalog record.
- **Fields**: `id`, `name`, `vendor`, `description`, `domains`, `transport`, `command`, `installability_tier`, `risk_level`, `platform_support`, `host_software_required`, `credentials_required`, `validation_result`, `follow_up_url`, `install_blocked_reason`.
- **Relationships**: Converts to API `McpServer` records and Hermes plugin catalog entries.
- **Validation Rules**: Required platform keys are filled with defaults; duplicate IDs are rejected; installability ordering is shared.

## CatalogNormalizationResult

- **Purpose**: Captures normalized catalog entries plus warnings.
- **Fields**: `records`, `warnings`, `source_name`, `source_path`.
- **Validation Rules**: Warnings must not hide invalid duplicate IDs or invalid transport values.

## ValidationPlan

- **Purpose**: Ordered validation intent for one MCP server.
- **Fields**: `server_id`, `environment`, `preflight`, `install_steps`, `protocol_probes`, `safe_backend_probe`, `gateway_probe`, `requires_docker`, `requires_network`, `requires_credentials`.
- **Validation Rules**: Docker, network, credential, proprietary, and hardware-bound steps are opt-in flags, not fast-suite defaults.

## ValidationEvidence

- **Purpose**: Recorded result of validation plan execution.
- **Fields**: `server_id`, `environment`, `started_at`, `completed_at`, `status`, `steps`, `diagnostics`, `missing_dependencies`, `follow_up_url`.
- **Validation Rules**: Secret-like values are redacted. Evidence status cannot mark an MCP as fully tested unless protocol probes and a safe backend-touching probe succeed or are explicitly blocked with documented reason.

## SystemSmokeScenario

- **Purpose**: Minimal end-to-end verification path required by the constitution.
- **Fields**: `name`, `fixtures`, `requests`, `assertions`, `offline_safe`.
- **Validation Rules**: Default smoke scenarios must not require Docker, network, hosted agents, credentials, or proprietary software.

