# Contract: Workspace Service

## Package Boundary

`packages/workspace_service` owns workspace lifecycle orchestration touched by Phase 2.

Allowed dependencies:

- `core`
- `agent_adapters`
- `tool_registry`
- `data_vault` when storage helpers are needed

Forbidden dependencies:

- `apps/api`
- provider-specific filesystem paths outside adapter materializers

## Public Operations

```text
create_workspace(request) -> WorkspaceRecord
activate_workspace(request) -> WorkspaceActivation
update_workspace_config(request) -> WorkspaceConfig
list_workspace_tools(session_id) -> WorkspaceToolState
set_workspace_tool_enabled(session_id, server_id, enabled) -> WorkspaceToolState
execute_workspace_file(session_id, path, policy) -> FileExecutionResult
refresh_agent_context(workspace_id | path, agent_id) -> ContextRefreshResult
```

## Error Contract

Package errors are typed and expose safe `code` and `message` values:

- `workspace.not_found`
- `workspace.conflict`
- `workspace.invalid_request`
- `workspace.execution_failed`
- `workspace.context_failed`

API routes translate these errors to HTTP status codes and preserve response shapes.

## Compatibility Rules

- Existing route response fields remain unchanged.
- Workspace creation may continue using a local fallback session when the active agent is unavailable.
- Generic workspace service code must not call `write_workspace_hermes_md` directly.
- Hermes materialization is allowed only through a Hermes adapter materializer.
