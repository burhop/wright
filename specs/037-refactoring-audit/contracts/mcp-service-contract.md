# Contract: MCP Service Layer

## Purpose

MCP HTTP routes delegate business logic to service-layer code while preserving public API response shapes.

## Operations

Initial service groups:

- Catalog listing and credential configured flags.
- Server registration and report-missing.
- Install, uninstall, activation, delete.
- Validation classification, follow-up writing, and persistence.
- Credential status, save, and delete.
- Version check and update.

## Response Compatibility

The following route response models remain the compatibility baseline:

- `ServersListResponse`
- `RegisterServerResponse`
- `ServerToggleResponse`
- `ServerInstallResponse`
- `ValidateServerResponse`
- `ToolsListResponse`
- `ToolToggleResponse`
- `CredentialStatusResponse`

## Error Compatibility

Routes continue translating domain errors to existing HTTP statuses:

- Missing server or tool: 404.
- Duplicate server name: 400.
- Blocked or non-working install: 400.
- Network-type version check/update mismatch: 400.
- Unexpected service failure: 500 unless an existing route uses another status.

## Required Tests

- Direct service tests for each moved operation group.
- Existing API route tests continue to pass unchanged or with fixture-only updates.
- Tests prove install/update flows do not add extra approval gates beyond catalog safety restrictions.

