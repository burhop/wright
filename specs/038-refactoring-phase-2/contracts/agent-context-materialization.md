# Contract: Agent Context Materialization

## Provider Contract

```text
AgentContextMaterializer.provider_id -> str
AgentContextMaterializer.support_level -> supported | experimental | stub | unavailable
AgentContextMaterializer.materialize(request) -> ContextMaterializationResult
```

## Materialization Request

Fields:

- `db_path`
- `workspace_path`
- `workspace_id`
- `session_id`
- `correlation_id`

## Materialization Result

Fields:

- `provider_id`
- `support_level`
- `files_written`
- `warnings`
- `error_code`

## Provider Rules

- Hermes provider may write `.hermes.md`.
- Hermes config paths under `~/.hermes` remain inside Hermes gateway/profile code.
- OpenClaw stub writes no Hermes files and returns a successful stub result.
- Future providers must implement this contract without changing workspace routes.
